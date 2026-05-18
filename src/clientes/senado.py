"""
Cliente para a API de Dados Abertos do Senado Federal.

Documentacao da API: https://legis.senado.leg.br/dadosabertos/docs
"""

import logging
from typing import Any, Dict, Optional

import pandas as pd

from src.clientes.base import ClienteBaseApi
from src.configuracao import URL_API_SENADO

logger = logging.getLogger(__name__)


class ClienteSenado(ClienteBaseApi):
    """
    Busca informacoes de materias legislativas na API do Senado Federal.

    Retorna dados como ementa, autoria, tramitacao e links
    para cada proposicao identificada por sigla/numero/ano.
    """

    def __init__(self):
        super().__init__(
            url_base=URL_API_SENADO,
            timeout_padrao=20,
            max_tentativas=6,
        )
        self._cache_ids: Dict[tuple, Optional[str]] = {}
        self._cache_detalhes: Dict[str, Dict[str, Any]] = {}

    def _get(self, caminho: str, params: Optional[dict] = None) -> Dict[str, Any]:
        """Requisicao GET padrao para a API do Senado."""
        return self._requisitar_json(
            f"{self.url_base}/{caminho.lstrip('/')}",
            params=params or {},
        )

    @staticmethod
    def _limpar_id_numerico(valor: Any) -> Optional[str]:
        """Converte um valor para string de ID limpo (sem '.0')."""
        if valor is None:
            return None
        texto = str(valor).strip()
        if texto.endswith(".0"):
            texto = texto[:-2]
        return texto or None

    @staticmethod
    def _concatenar_sigla_nome(sigla: Any, nome: Any) -> str:
        """Junta sigla e nome de um orgao, tratando valores nulos."""
        sigla = str(sigla).strip() if sigla is not None and not pd.isna(sigla) else ""
        nome = str(nome).strip() if nome is not None and not pd.isna(nome) else ""

        if sigla and nome:
            return f"{sigla} - {nome}"
        return sigla or nome

    def obter_id_processo(self, sigla: str, numero: Any, ano: Any) -> Optional[str]:
        """
        Busca o ID do processo no Senado a partir de sigla/numero/ano.

        Resultados sao cacheados para evitar requisicoes repetidas.
        """
        ref = self._normalizar_referencia(sigla, numero, ano)
        if not ref:
            return None

        sigla, numero, ano = ref
        chave = (sigla, numero, ano)

        if chave in self._cache_ids:
            return self._cache_ids[chave]

        try:
            resposta = self._get(
                "processo.json",
                params={"sigla": sigla, "numero": numero, "ano": ano, "v": "1"},
            )
            pid = self._limpar_id_numerico(
                self._buscar_chave_profunda(resposta, "id")
            )
            self._cache_ids[chave] = pid
            return pid

        except Exception:
            logger.exception(
                "Erro ao buscar ID do processo %s %s/%s no Senado",
                sigla, numero, ano,
            )
            self._cache_ids[chave] = None
            return None

    def _extrair_orgao(self, item: dict, autuacao: dict) -> str:
        """
        Identifica o orgao responsavel usando fallback hierarquico:
        1. Colegiado do item
        2. Ente administrativo do item
        3. Ente de controle atual da autuacao
        """
        fontes = [
            item.get("colegiado") or {},
            item.get("enteAdministrativo") or {},
            {
                "sigla": autuacao.get("siglaEnteControleAtual"),
                "nome": autuacao.get("nomeEnteControleAtual"),
            },
        ]
        for fonte in fontes:
            orgao = self._concatenar_sigla_nome(fonte.get("sigla"), fonte.get("nome"))
            if orgao:
                return orgao
        return ""

    def _buscar_mais_recente(
        self,
        itens: list,
        campo_data: str,
        campo_descricao: str,
        autuacao: dict,
    ) -> tuple[str, str, str]:
        """Encontra o item mais recente em uma lista, extraindo data, orgao e descricao."""
        if not isinstance(itens, list) or not itens:
            return "", "", ""

        melhor = None
        melhor_data = None

        for item in itens:
            data = self._parse_data_iso(item.get(campo_data))
            if data and (melhor_data is None or data > melhor_data):
                melhor_data = data
                melhor = item

        if not melhor or not melhor_data:
            return "", "", ""

        return (
            melhor_data.strftime("%d/%m/%Y"),
            self._extrair_orgao(melhor, autuacao),
            (melhor.get(campo_descricao) or melhor.get("sigla") or "").strip(),
        )

    def _extrair_ultimo_movimento(self, json_processo: Dict[str, Any]) -> tuple[str, str, str]:
        """
        Extrai data, orgao e situacao do ultimo movimento do processo.

        Tenta primeiro os informes legislativos; se vazio, tenta situacoes.
        """
        autuacoes = json_processo.get("autuacoes") or []
        primeira_autuacao = (
            autuacoes[0] if isinstance(autuacoes, list) and autuacoes else {}
        )

        for campo_lista, campo_data in [
            ("informesLegislativos", "data"),
            ("situacoes", "inicio"),
        ]:
            itens = primeira_autuacao.get(campo_lista) or []
            resultado = self._buscar_mais_recente(itens, campo_data, "descricao", primeira_autuacao)
            if resultado[0]:
                return resultado

        return "", "", ""

    def buscar(self, sigla: str, numero: Any, ano: Any) -> Dict[str, Any]:
        """
        Busca dados completos de uma materia no Senado.

        Args:
            sigla: Tipo da proposicao (PL, PLC, PDL, MPV, etc.).
            numero: Numero da proposicao.
            ano: Ano da proposicao.

        Returns:
            Dicionario com todos os campos prefixados com 'senado_',
            ou dicionario vazio se nao encontrada.
        """
        pid = self.obter_id_processo(sigla, numero, ano)
        if not pid:
            return {}

        if pid in self._cache_detalhes:
            return self._cache_detalhes[pid]

        try:
            json_processo = self._get(f"processo/{pid}.json", params={"v": "1"})

            codigo_materia = self._limpar_id_numerico(
                self._buscar_chave_profunda(json_processo, "codigoMateria")
            ) or ""

            link_ficha = (
                f"https://www25.senado.leg.br/web/atividade/materias/-/materia/{codigo_materia}"
                if codigo_materia
                else ""
            )

            documento = json_processo.get("documento") or {}
            autoria = documento.get("autoria") or []

            nomes = [
                a.get("autor")
                for a in autoria
                if isinstance(a, dict) and a.get("autor")
            ]
            primeiro_autor = (
                autoria[0]
                if isinstance(autoria, list) and autoria and isinstance(autoria[0], dict)
                else {}
            )

            data_ult, orgao_ult, situacao_ult = self._extrair_ultimo_movimento(json_processo)

            url_documento = (documento.get("url") or "").strip()
            link_inteiro_teor = ""
            if url_documento:
                link_inteiro_teor = (
                    url_documento
                    if "disposition=" in url_documento
                    else f"{url_documento}&disposition=inline"
                )

            ementa = ""
            conteudo = json_processo.get("conteudo") or {}
            if isinstance(conteudo, dict):
                ementa = (conteudo.get("ementa") or "").strip()
            if not ementa:
                ementa = str(self._buscar_chave_profunda(json_processo, "ementa") or "").strip()

            # Usa sigla/numero/ano ja normalizados pelo obter_id_processo
            ref = self._normalizar_referencia(sigla, numero, ano)
            s, n, a = ref if ref else (str(sigla).upper(), str(numero), str(ano))

            resultado = {
                "senado_id_processo": pid,
                "senado_codigo_materia": codigo_materia,
                "senado_projeto": f"{s} {n}/{a}",
                "senado_ementa": ementa,
                "senado_data_ultima_tramitacao": data_ult,
                "senado_orgao_ultima_tramitacao": orgao_ult,
                "senado_situacao_ultima_tramitacao": situacao_ult,
                "senado_data_parecer_aprovado": "",
                "senado_orgao_parecer": "",
                "senado_link_inteiro_teor_parecer": "",
                "senado_link_inteiro_teor_pl": link_inteiro_teor,
                "senado_link_ficha_tramitacao": link_ficha,
                "senado_data_proposta_pl": self._formatar_data(documento.get("dataApresentacao")),
                "senado_propositor_pl": self._formatar_propositor(nomes),
                "senado_partido": (primeiro_autor.get("siglaPartido") or "").strip(),
                "senado_estado": (primeiro_autor.get("uf") or "").strip(),
                "senado_emendas": link_ficha,
                "senado_substitutivos": link_ficha,
            }

            self._cache_detalhes[pid] = resultado
            return resultado

        except Exception:
            logger.exception("Erro ao buscar detalhes do processo %s no Senado", pid)
            self._cache_detalhes[pid] = {}
            return {}
