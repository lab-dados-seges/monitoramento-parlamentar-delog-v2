"""
Cliente HTTP base com retry e backoff exponencial.

Todas as classes de integracao com APIs externas herdam deste cliente.
"""

import logging
import random
import time
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)


class ClienteBaseApi:
    """
    Cliente HTTP generico com retry automatico e backoff exponencial.

    Args:
        url_base: URL raiz da API (ex: 'https://api.exemplo.com/v2').
        timeout_padrao: Tempo limite em segundos para cada requisicao.
        max_tentativas: Numero maximo de tentativas antes de desistir.
        user_agent: Identificacao do cliente nas requisicoes.
    """

    CODIGOS_HTTP_RETENTAVEIS = (429, 500, 502, 503, 504)

    def __init__(
        self,
        url_base: str,
        timeout_padrao: int = 20,
        max_tentativas: int = 5,
        user_agent: str = "NID-DELOG-Monitor/1.0",
    ):
        self.url_base = url_base.rstrip("/")
        self.timeout_padrao = timeout_padrao
        self.max_tentativas = max_tentativas
        self.sessao = requests.Session()
        self.user_agent = user_agent

    def _requisitar_json(
        self,
        url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Faz uma requisicao GET e retorna o JSON da resposta.

        Implementa retry com backoff exponencial para erros transientes
        (timeout, erro de conexao, HTTP 429/5xx).

        Raises:
            requests.HTTPError: Quando todas as tentativas falham.
        """
        params = dict(params or {})
        headers_final = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }
        if headers:
            headers_final.update(headers)

        ultima_excecao = None
        timeout = timeout or self.timeout_padrao

        for tentativa in range(1, self.max_tentativas + 1):
            try:
                resposta = self.sessao.get(
                    url,
                    params=params,
                    headers=headers_final,
                    timeout=timeout,
                )

                if resposta.status_code in self.CODIGOS_HTTP_RETENTAVEIS:
                    raise requests.HTTPError(
                        f"HTTP {resposta.status_code}",
                        response=resposta,
                    )

                resposta.raise_for_status()
                return resposta.json()

            except (
                requests.Timeout,
                requests.ConnectionError,
                requests.HTTPError,
                ValueError,
            ) as erro:
                ultima_excecao = erro
                logger.warning(
                    "Tentativa %d/%d falhou para %s: %s",
                    tentativa,
                    self.max_tentativas,
                    url,
                    erro,
                )
                if tentativa == self.max_tentativas:
                    break

                tempo_espera = (2 ** (tentativa - 1)) * 0.5 + random.uniform(0, 0.4)
                time.sleep(tempo_espera)

        logger.error("Todas as %d tentativas falharam para %s", self.max_tentativas, url)
        raise ultima_excecao

    @staticmethod
    def _normalizar_referencia(
        sigla: Any, numero: Any, ano: Any
    ) -> Optional[tuple[str, str, str]]:
        """
        Valida e normaliza sigla/numero/ano de uma proposicao.

        Returns:
            Tupla (sigla, numero, ano) normalizada, ou None se invalida.
        """
        if pd.isna(sigla) or pd.isna(numero) or pd.isna(ano):
            return None
        return (
            str(sigla).strip().upper(),
            str(int(numero)),
            str(int(ano)),
        )

    @staticmethod
    def _parse_data_iso(valor: Any) -> Optional[datetime]:
        """Interpreta datas em formatos ISO variados. Retorna None se invalido."""
        if not valor or pd.isna(valor):
            return None
        texto = str(valor).strip().replace("T", " ").replace("Z", "")
        if "." in texto:
            texto = texto.split(".")[0]
        for formato in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(texto, formato)
            except ValueError:
                continue
        return None

    @staticmethod
    def _formatar_data(iso: Any) -> str:
        """Converte data ISO 8601 para o formato brasileiro dd/mm/aaaa."""
        dt = ClienteBaseApi._parse_data_iso(iso)
        if dt:
            return dt.strftime("%d/%m/%Y")
        return str(iso) if iso and not pd.isna(iso) else ""

    @staticmethod
    def _formatar_propositor(nomes: list[str], limite: int = 5) -> str:
        """Formata lista de nomes de autores em texto unico com truncamento."""
        if not nomes:
            return ""
        texto = "; ".join(nomes[:limite])
        if len(nomes) > limite:
            texto += f" (+{len(nomes) - limite})"
        return texto

    @staticmethod
    def _buscar_chave_profunda(obj: Any, chave: str):
        """
        Busca recursiva por uma chave em dicionarios/listas aninhados.

        Retorna o primeiro valor encontrado ou None.
        """
        if isinstance(obj, dict):
            if chave in obj:
                return obj[chave]
            for valor in obj.values():
                encontrado = ClienteBaseApi._buscar_chave_profunda(valor, chave)
                if encontrado is not None:
                    return encontrado
        elif isinstance(obj, list):
            for item in obj:
                encontrado = ClienteBaseApi._buscar_chave_profunda(item, chave)
                if encontrado is not None:
                    return encontrado
        return None
