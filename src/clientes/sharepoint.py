"""
Cliente para acesso ao SharePoint via Microsoft Graph.

Autenticacao OAuth2 client-credentials (app registration no Azure AD).
Credenciais lidas das variaveis de ambiente AZURE_CLIENT_ID,
AZURE_CLIENT_SECRET e AZURE_TENANT_ID. O carregamento de .env e
responsabilidade do chamador (CI define via secrets; dev local via dotenv).
"""

import logging
import os
import time
from typing import Optional

import msal
import requests

from src.configuracao import (
    ARQUIVO_PLANILHA,
    CAMINHO_DADOS,
    SHAREPOINT_HOST,
    SHAREPOINT_PASTA_PLANILHA,
    SHAREPOINT_SITE,
)

logger = logging.getLogger(__name__)

_GRAPH_BASE = "https://graph.microsoft.com/v1.0"
_GRAPH_SCOPE = ["https://graph.microsoft.com/.default"]


def _ler_env(nome: str) -> str:
    valor = os.environ.get(nome)
    if not valor:
        raise RuntimeError(
            f"Variavel de ambiente {nome} nao definida. "
            "Configure-a no .env (dev local) ou nos secrets do CI."
        )
    return valor


class ClienteSharePoint:
    """
    Cliente para listar e baixar arquivos de uma biblioteca de SharePoint
    via Microsoft Graph.

    Args:
        host: dominio do tenant SharePoint (ex.: 'colaboragov.sharepoint.com').
        site: nome do site dentro do tenant (ex.: 'CGNOR-SEGES').
        client_id, client_secret, tenant_id: credenciais do app no Azure AD.
            Se nao informados, lidos das variaveis de ambiente AZURE_*.
    """

    def __init__(
        self,
        host: str = SHAREPOINT_HOST,
        site: str = SHAREPOINT_SITE,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant_id: Optional[str] = None,
        timeout_padrao: int = 30,
    ):
        self.host = host
        self.site = site
        self.timeout_padrao = timeout_padrao

        self._client_id = client_id or _ler_env("AZURE_CLIENT_ID")
        client_secret = client_secret or _ler_env("AZURE_CLIENT_SECRET")
        self._tenant_id = tenant_id or _ler_env("AZURE_TENANT_ID")

        self._app = msal.ConfidentialClientApplication(
            client_id=self._client_id,
            client_credential=client_secret,
            authority=f"https://login.microsoftonline.com/{self._tenant_id}",
        )

        self._token: Optional[str] = None
        self._token_expira_em: float = 0.0
        self._site_id: Optional[str] = None
        self._drive_id: Optional[str] = None

    def _obter_token(self) -> str:
        """Retorna um token de aplicacao valido, com cache em memoria."""
        if self._token and time.time() < self._token_expira_em - 60:
            return self._token

        resultado = self._app.acquire_token_for_client(scopes=_GRAPH_SCOPE)
        if "access_token" not in resultado:
            raise RuntimeError(
                f"Falha ao obter token: {resultado.get('error_description', 'desconhecido')}"
            )
        self._token = resultado["access_token"]
        self._token_expira_em = time.time() + int(resultado.get("expires_in", 3600))
        return self._token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._obter_token()}",
            "Accept": "application/json",
        }

    def _resolver_site_e_drive(self) -> tuple[str, str]:
        """Descobre site_id e drive_id (biblioteca 'Documents'), com cache."""
        if self._site_id and self._drive_id:
            return self._site_id, self._drive_id

        r = requests.get(
            f"{_GRAPH_BASE}/sites/{self.host}:/sites/{self.site}",
            headers=self._headers(),
            timeout=self.timeout_padrao,
        )
        r.raise_for_status()
        site_id = r.json()["id"]

        r = requests.get(
            f"{_GRAPH_BASE}/sites/{site_id}/drives",
            headers=self._headers(),
            timeout=self.timeout_padrao,
        )
        r.raise_for_status()
        drives = r.json().get("value", [])
        try:
            drive_id = next(d["id"] for d in drives if d["name"] == "Documents")
        except StopIteration:
            raise RuntimeError(
                f"Biblioteca 'Documents' nao encontrada no site {self.site!r}"
            )

        self._site_id, self._drive_id = site_id, drive_id
        return site_id, drive_id

    def listar_arquivos(self, pasta: str) -> list[dict]:
        """Retorna a lista de itens imediatos em uma pasta."""
        site_id, drive_id = self._resolver_site_e_drive()
        r = requests.get(
            f"{_GRAPH_BASE}/sites/{site_id}/drives/{drive_id}/root:/{pasta}:/children",
            headers=self._headers(),
            timeout=self.timeout_padrao,
        )
        r.raise_for_status()
        return r.json().get("value", [])

    def baixar_arquivo(
        self,
        nome_arquivo: str,
        pasta: str,
        destino: str,
    ) -> str:
        """
        Baixa um arquivo do SharePoint para a pasta local. Sobrescreve se ja existir.

        Returns:
            Caminho local do arquivo baixado.
        """
        site_id, drive_id = self._resolver_site_e_drive()
        r = requests.get(
            f"{_GRAPH_BASE}/sites/{site_id}/drives/{drive_id}"
            f"/root:/{pasta}/{nome_arquivo}:/content",
            headers=self._headers(),
            allow_redirects=True,
            timeout=self.timeout_padrao * 2,
        )
        r.raise_for_status()

        os.makedirs(destino, exist_ok=True)
        caminho_local = os.path.join(destino, nome_arquivo)
        with open(caminho_local, "wb") as f:
            f.write(r.content)

        logger.info(
            "Arquivo baixado do SharePoint: %s (%d bytes)",
            caminho_local,
            len(r.content),
        )
        return caminho_local


def baixar_planilha_cgnor(destino: str = CAMINHO_DADOS) -> str:
    """
    Baixa a planilha oficial da CGNOR do SharePoint para a pasta de dados local.

    Sobrescreve a versao local se ja existir. Usa as configuracoes
    SHAREPOINT_* e ARQUIVO_PLANILHA do `configuracao.py`.

    Returns:
        Caminho absoluto do arquivo baixado.
    """
    cliente = ClienteSharePoint()
    return cliente.baixar_arquivo(
        nome_arquivo=ARQUIVO_PLANILHA,
        pasta=SHAREPOINT_PASTA_PLANILHA,
        destino=destino,
    )


if __name__ == "__main__":
    # Permite invocar via `python -m src.clientes.sharepoint`.
    # Em dev local, carrega .env. Em CI, env vars dos secrets ja estao no ambiente
    # e load_dotenv nao sobrescreve por padrao, entao e seguro nos dois cenarios.
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    print(baixar_planilha_cgnor())
