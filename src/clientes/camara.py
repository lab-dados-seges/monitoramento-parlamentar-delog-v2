"""
Cliente para a API de Dados Abertos da Camara dos Deputados.

Documentacao da API: https://dadosabertos.camara.leg.br/swagger/api.html
"""

import logging
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from src.clientes.base import ClienteBaseApi
from src.configuracao import URL_API_CAMARA

logger = logging.getLogger(__name__)


# Tipos de proposicao consideradas "emendas" para o calculo de Ne
SIGLAS_EMENDA = {
    "EMC", "EMP", "EMS", "EMR", "EML", "EMO", "EMD",
    "EMA", "EMRP", "EMC-A", "EMPV",
}

# Palavras-chave (lowercase) que indicam substitutivo no parecer do relator
PALAVRAS_SUBSTITUTIVO = ("substitutivo", "texto com alterações", "texto com alteracoes")


class ClienteCamara(ClienteBaseApi):
    """
    Busca informacoes de proposicoes na API da Camara dos Deputados.

    Retorna dados como ementa, autoria, tramitacao, pareceres e links
    para cada proposicao identificada por sigla/numero/ano.
    """

    def __init__(self):
        super().__init__(
            url_base=URL_API_CAMARA,
            timeout_padrao=15,
            max_tentativas=5,
        )
        self._cache_deputados: Dict[int, dict] = {}

    @staticmethod
    def _extrair_id_deputado(uri: str) -> Optional[int]:
        """Extrai o ID numerico de um deputado a partir da URI da API."""
        if not isinstance(uri, str):
            return None
        match = re.search(r"/deputados/(\d+)", uri)
        return int(match.group(1)) if match else None

    def _get(self, caminho: str, params: Optional[dict] = None) -> Dict[str, Any]:
        """Requisicao GET com formato JSON padrao da API da Camara."""
        params = dict(params or {})
        params.setdefault("formato", "json")
        return self._requisitar_json(
            f"{self.url_base}/{caminho.lstrip('/')}",
            params=params,
        )

    def _resolver_partido_uf(self, id_deputado: Optional[int]) -> tuple[str, str]:
        """Busca partido e UF de um deputado pelo ID, com cache."""
        if not id_deputado:
            return "", ""

        if id_deputado in self._cache_deputados:
            dados_dep = self._cache_deputados[id_deputado]
        else:
            dados_dep = self._get(f"deputados/{id_deputado}").get("dados", {}) or {}
            self._cache_deputados[id_deputado] = dados_dep

        ultimo_status = dados_dep.get("ultimoStatus", {}) or {}
        return (
            (ultimo_status.get("siglaPartido") or "").strip(),
            (ultimo_status.get("siglaUf") or "").strip(),
        )

    def _extrair_autoria(self, id_proposicao: int) -> tuple[str, str, str]:
        """
        Extrai propositor, partido e estado a partir dos autores da proposicao.

        Returns:
            Tupla (propositor, partido, estado).
        """
        autores = self._get(f"proposicoes/{id_proposicao}/autores").get("dados", []) or []
        autores = sorted(
            autores,
            key=lambda a: (
                a.get("ordemAssinatura") is None,
                a.get("ordemAssinatura", 10**9),
            ),
        )

        nomes = []
        partido = ""
        estado = ""
        id_deputado = None

        for autor in autores:
            nome = (autor.get("nome") or autor.get("nomeAutor") or "").strip()
            if nome:
                nomes.append(nome)
            if not partido:
                partido = (autor.get("siglaPartido") or "").strip()
            if not estado:
                estado = (autor.get("siglaUf") or "").strip()
            if id_deputado is None:
                id_deputado = self._extrair_id_deputado(autor.get("uri") or "")

        # Fallback: busca partido/UF pelo endpoint do deputado
        if id_deputado and (not partido or not estado):
            partido_dep, estado_dep = self._resolver_partido_uf(id_deputado)
            partido = partido or partido_dep
            estado = estado or estado_dep

        if id_deputado is None and nomes:
            partido = partido or "N/A"
            estado = estado or "N/A"

        return self._formatar_propositor(nomes), partido, estado

    def _extrair_parecer(self, id_proposicao: int) -> tuple[str, str, str, str]:
        """
        Busca o parecer mais recente nas tramitacoes da proposicao.

        Returns:
            Tupla (data, orgao, despacho, link).
        """
        tramitacoes = (
            self._get(f"proposicoes/{id_proposicao}/tramitacoes").get("dados", []) or []
        )

        candidatos = []
        for tramitacao in tramitacoes:
            codigo = str(tramitacao.get("codTipoTramitacao", ""))
            texto = (
                f"{tramitacao.get('descricaoTramitacao', '')} "
                f"{tramitacao.get('despacho', '')}"
            ).lower()
            if codigo == "322" or "parecer" in texto:
                candidatos.append(tramitacao)

        if not candidatos:
            return "", "", "", ""

        def _parse_datetime(item):
            try:
                return datetime.fromisoformat(
                    str(item.get("dataHora", "")).replace("Z", "")
                )
            except (ValueError, TypeError):
                return datetime.min

        candidatos.sort(key=_parse_datetime, reverse=True)
        mais_recente = candidatos[0]

        data = self._formatar_data(mais_recente.get("dataHora"))
        orgao = (mais_recente.get("siglaOrgao") or "").strip()
        despacho = (
            mais_recente.get("despacho") or mais_recente.get("descricaoTramitacao") or ""
        ).strip()

        link = (mais_recente.get("url") or "").strip()
        if not link:
            for doc in mais_recente.get("documentos") or []:
                link = (
                    doc.get("url")
                    or doc.get("urlInteiroTeor")
                    or doc.get("uri")
                    or ""
                )
                if link:
                    break

        return data, orgao, despacho, link

    # ============================================================
    # COLETA DE METRICAS PARA CALOR LEGISLATIVO
    # ============================================================

    def _contar_tramitacoes_recentes(
        self, tramitacoes: List[dict], dias: int = 30
    ) -> int:
        """
        Conta itens de tramitacao cujo dataHora esta dentro dos ultimos N dias.

        Retorna 0 quando nenhum item se enquadra (a normalizacao para 0.5
        ocorre no modulo de calculo, nao aqui).
        """
        if not tramitacoes:
            return 0

        limite = datetime.combine(date.today(), datetime.min.time()) - timedelta(days=dias)
        contador = 0
        for item in tramitacoes:
            dt = self._parse_data_iso(item.get("dataHora"))
            if dt and dt >= limite:
                contador += 1
        return contador

    def _calcular_t_base(self, tramitacoes: List[dict]) -> int:
        """
        Retorna o numero de dias desde a ultima mudanca de descricaoSituacao.

        Identifica o status atual (item com maior 'sequencia') e percorre a
        lista de tras para frente buscando o primeiro item com descricaoSituacao
        diferente. Se nao houver mudanca anterior, usa o primeiro evento
        registrado.
        """
        if not tramitacoes:
            return 0

        # Ordena por 'sequencia' (fallback: dataHora). Maior sequencia = mais recente.
        def _chave_ordenacao(item: dict):
            seq = item.get("sequencia")
            try:
                return (0, int(seq)) if seq is not None else (1, 0)
            except (TypeError, ValueError):
                return (1, 0)

        ordenadas = sorted(tramitacoes, key=_chave_ordenacao)
        atual = ordenadas[-1]
        situacao_atual = (atual.get("descricaoSituacao") or "").strip()

        data_mudanca: Optional[datetime] = None
        # Percorre de tras para frente, ignorando o ultimo (o proprio atual)
        for item in reversed(ordenadas[:-1]):
            situacao_item = (item.get("descricaoSituacao") or "").strip()
            if situacao_item and situacao_item != situacao_atual:
                data_mudanca = self._parse_data_iso(item.get("dataHora"))
                if data_mudanca:
                    break

        # Fallback: data do primeiro evento da tramitacao
        if data_mudanca is None:
            data_mudanca = self._parse_data_iso(ordenadas[0].get("dataHora"))

        if data_mudanca is None:
            return 0

        delta = date.today() - data_mudanca.date()
        return max(delta.days, 0)

    def _coletar_emendas_e_substitutivo(
        self, id_proposicao: int
    ) -> tuple[int, float]:
        """
        Le /proposicoes/{id}/relacionadas e calcula Ne e S.

        Returns:
            Tupla (numero_emendas, multiplicador_substitutivo).
        """
        try:
            relacionadas = (
                self._get(f"proposicoes/{id_proposicao}/relacionadas").get("dados", [])
                or []
            )
        except Exception:
            logger.warning(
                "Falha ao buscar relacionadas da proposicao %s para calor legislativo",
                id_proposicao,
            )
            return 0, 1.0

        # Ne: contagem por sigla de emenda
        numero_emendas = sum(
            1
            for item in relacionadas
            if (item.get("siglaTipo") or "").strip().upper() in SIGLAS_EMENDA
        )

        # S: parecer (PRL) mais recente com palavra-chave de substitutivo
        pareceres = [
            item
            for item in relacionadas
            if (item.get("siglaTipo") or "").strip().upper() == "PRL"
        ]

        if not pareceres:
            return numero_emendas, 1.0

        def _data_apresentacao(item: dict) -> datetime:
            dt = self._parse_data_iso(item.get("dataApresentacao"))
            return dt or datetime.min

        pareceres.sort(key=_data_apresentacao, reverse=True)
        ementa_recente = (pareceres[0].get("ementa") or "").lower()

        s_mult = 1.5 if any(p in ementa_recente for p in PALAVRAS_SUBSTITUTIVO) else 1.0
        return numero_emendas, s_mult

    def coletar_metricas_calor(
        self, id_proposicao: int, regime: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Coleta os componentes brutos (A, Ne, S, R, T_base) usados no calculo
        do Calor Legislativo.

        Reutiliza a sessao HTTP do cliente; trata falhas de API retornando
        defaults (0/1.0) para nao quebrar o pipeline.

        Args:
            id_proposicao: ID da proposicao na API da Camara.
            regime: Regime de tramitacao ja conhecido (para evitar nova chamada).

        Returns:
            Dicionario com as chaves 'A', 'Ne', 'S', 'R_regime', 'T_base'
            onde 'R_regime' contem o texto bruto do regime (o calculo do
            multiplicador R fica a cargo do modulo de calor_legislativo).
        """
        # Tramitacoes (A e T_base compartilham a mesma chamada)
        try:
            tramitacoes = (
                self._get(f"proposicoes/{id_proposicao}/tramitacoes").get("dados", [])
                or []
            )
        except Exception:
            logger.warning(
                "Falha ao buscar tramitacoes da proposicao %s para calor legislativo",
                id_proposicao,
            )
            tramitacoes = []

        atividade = self._contar_tramitacoes_recentes(tramitacoes, dias=30)
        t_base = self._calcular_t_base(tramitacoes)
        emendas, s_mult = self._coletar_emendas_e_substitutivo(id_proposicao)

        return {
            "A": atividade,
            "Ne": emendas,
            "S": s_mult,
            "R_regime": (regime or "").strip(),
            "T_base": t_base,
        }

    def buscar(self, sigla: str, numero: Any, ano: Any) -> Dict[str, Any]:
        """
        Busca dados completos de uma proposicao na Camara.

        Args:
            sigla: Tipo da proposicao (PL, PLC, PDL, MPV, etc.).
            numero: Numero da proposicao.
            ano: Ano da proposicao.

        Returns:
            Dicionario com todos os campos prefixados com 'camara_',
            ou dicionario vazio se nao encontrada.
        """
        ref = self._normalizar_referencia(sigla, numero, ano)
        if not ref:
            return {}

        sigla, numero, ano = ref

        try:
            busca = self._get(
                "proposicoes",
                params={"siglaTipo": sigla, "numero": numero, "ano": ano},
            )
            dados = busca.get("dados", []) or []
            if not dados:
                return {}

            proposicao = dados[0]
            id_prop = proposicao.get("id")
            if not id_prop:
                return {}

            detalhe = self._get(f"proposicoes/{id_prop}").get("dados", {}) or {}
            status = detalhe.get("statusProposicao", {}) or {}

            propositor, partido, estado = self._extrair_autoria(id_prop)
            parecer_data, parecer_orgao, parecer_despacho, parecer_link = (
                self._extrair_parecer(id_prop)
            )

            link_ficha = (
                f"https://www.camara.leg.br/proposicoesWeb/"
                f"fichadetramitacao?idProposicao={id_prop}"
            )
            link_inteiro_teor_pl = (detalhe.get("urlInteiroTeor") or "").strip()
            emendas = (
                f"https://www.camara.leg.br/proposicoesWeb/"
                f"prop_emendas?idProposicao={id_prop}&subst=0"
            )
            substitutivos = (
                f"https://www.camara.leg.br/proposicoesWeb/"
                f"prop_pareceres_substitutivos_votos?idProposicao={id_prop}"
            )

            regime_str = (status.get("regime") or "").strip()

            # Coleta componentes do Calor Legislativo (A, Ne, S, R, T_base)
            from src.calor_legislativo import calcular_calor

            metricas = self.coletar_metricas_calor(id_prop, regime=regime_str)
            resultado_calor = calcular_calor(
                atividade=metricas["A"],
                emendas=metricas["Ne"],
                s_substitutivo=metricas["S"],
                regime=metricas["R_regime"],
                t_base=metricas["T_base"],
            )

            dados_proposicao = {
                "camara_id_proposicao": str(id_prop),
                "camara_projeto": f"{sigla} {numero}/{ano}",
                "camara_ementa": (proposicao.get("ementa") or "").strip(),
                "camara_data_ultima_tramitacao": self._formatar_data(status.get("dataHora")),
                "camara_orgao_ultima_tramitacao": (status.get("siglaOrgao") or "").strip(),
                "camara_descricao_tramitacao": (
                    status.get("descricaoTramitacao") or ""
                ).strip(),
                "camara_regime": regime_str,
                "camara_situacao_ultima_tramitacao": (
                    status.get("descricaoSituacao") or ""
                ).strip(),
                "camara_despacho_ultima_tramitacao": (status.get("despacho") or "").strip(),
                "camara_data_parecer_aprovado": parecer_data,
                "camara_orgao_parecer": parecer_orgao,
                "camara_despacho_parecer": parecer_despacho,
                "camara_link_inteiro_teor_parecer": parecer_link,
                "camara_link_inteiro_teor_pl": link_inteiro_teor_pl,
                "camara_link_ficha_tramitacao": link_ficha,
                "camara_data_proposta_pl": self._formatar_data(detalhe.get("dataApresentacao")),
                "camara_propositor_pl": propositor,
                "camara_partido": partido,
                "camara_estado": estado,
                "camara_emendas": emendas,
                "camara_substitutivos": substitutivos,
            }
            dados_proposicao.update(resultado_calor.como_dict_camara())
            return dados_proposicao

        except Exception:
            logger.exception("Erro ao buscar %s %s/%s na Camara", sigla, numero, ano)
            return {}
