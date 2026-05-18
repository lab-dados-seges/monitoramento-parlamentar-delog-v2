"""
Pipeline de ETL — carrega planilha CGNOR, enriquece com APIs e exporta CSV.

Pode ser executado como script (python -m src.pipeline) ou importado
pelo notebook para execucao interativa.
"""

import logging
import os
import sys
from pathlib import Path

# Garante que a raiz do projeto esta no sys.path
_RAIZ_PROJETO = str(Path(__file__).resolve().parent.parent)
if _RAIZ_PROJETO not in sys.path:
    sys.path.insert(0, _RAIZ_PROJETO)

import pandas as pd

from src.analisador_legislativo import AnalisadorReferenciaLegislativa
from src.clientes.camara import ClienteCamara
from src.clientes.senado import ClienteSenado
from src.configuracao import (
    ARQUIVO_CSV_FINAL,
    ARQUIVO_PLANILHA,
    CAMINHO_DADOS,
    COLUNAS_DATA_PIPELINE,
    COLUNAS_NUMERICAS_INTEIRAS,
    COLUNAS_ORDENACAO_PIPELINE,
    COLUNAS_PLACEHOLDER_SEI,
)
from src.enriquecedor import EnriquecedorBicameral

logger = logging.getLogger(__name__)


def carregar_planilha(caminho: str) -> pd.DataFrame:
    """
    Carrega a planilha Excel da CGNOR e faz o tratamento inicial.

    - Promove a primeira linha a cabecalho
    - Normaliza nomes de colunas (remove espacos)
    - Remove duplicatas
    """
    logger.info("Carregando planilha: %s", caminho)
    df = pd.read_excel(caminho)

    # Promove primeira linha a cabecalho
    df.columns = df.iloc[0]
    df = df.iloc[1:].reset_index(drop=True)

    # Normaliza nomes das colunas
    df.columns = df.columns.str.strip()

    # Remove duplicatas
    tamanho_antes = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    removidos = tamanho_antes - len(df)
    if removidos:
        logger.info("Removidas %d linhas duplicadas.", removidos)

    # Injeta colunas placeholder ausentes (ex.: integracao SEI ainda nao implementada)
    for coluna in COLUNAS_PLACEHOLDER_SEI:
        if coluna not in df.columns:
            df[coluna] = pd.NA

    logger.info("Planilha carregada: %d linhas.", len(df))
    return df


def extrair_referencias(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica o analisador legislativo e adiciona colunas sigla/numero/ano/regex."""
    logger.info("Extraindo referencias legislativas...")

    resultados = df["Projeto de LEI"].apply(
        AnalisadorReferenciaLegislativa.extrair_referencia
    )
    df_parsed = pd.DataFrame(list(resultados))

    df = df.copy()
    df["sigla"] = df_parsed["sigla"]
    df["numero"] = pd.to_numeric(df_parsed["numero"], errors="coerce").astype("Int64")
    df["ano"] = pd.to_numeric(df_parsed["ano"], errors="coerce").astype("Int64")
    df["Projeto de Lei - Regex"] = df_parsed["proposicao_normalizada"]

    validos = df["sigla"].notna().sum()
    logger.info(
        "Referencias extraidas: %d/%d com sigla identificada.", validos, len(df)
    )
    return df


def enriquecer_com_apis(df: pd.DataFrame) -> pd.DataFrame:
    """Busca dados nas APIs da Camara e Senado e faz merge com o DataFrame."""
    logger.info("Iniciando enriquecimento bicameral...")

    cliente_camara = ClienteCamara()
    cliente_senado = ClienteSenado()
    enriquecedor = EnriquecedorBicameral(cliente_camara, cliente_senado)

    df_enriquecido = enriquecedor.enriquecer_dataframe(df)

    df_final = pd.merge(
        df,
        df_enriquecido,
        on=["sigla", "numero", "ano"],
        how="left",
    )

    logger.info("Merge concluido: %d linhas no resultado final.", len(df_final))
    return df_final


def normalizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza o DataFrame final:
    - Remove colunas duplicadas
    - Ordena colunas conforme schema definido
    - Padroniza datas para dd/mm/aaaa
    - Converte colunas numericas para inteiro
    """
    logger.info("Normalizando colunas...")

    df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]

    if df.columns.duplicated().any():
        duplicadas = list(df.columns[df.columns.duplicated()])
        logger.warning("Colunas duplicadas removidas: %s", duplicadas)
        df = df.loc[:, ~df.columns.duplicated()]

    # Ordena colunas: primeiro as principais, depois o restante
    colunas_ok = [c for c in COLUNAS_ORDENACAO_PIPELINE if c in df.columns]
    colunas_restantes = [c for c in df.columns if c not in colunas_ok]
    df = df[colunas_ok + colunas_restantes]

    # Padroniza datas
    for coluna in COLUNAS_DATA_PIPELINE:
        if coluna in df.columns:
            df[coluna] = (
                pd.to_datetime(df[coluna], errors="coerce", format="mixed", dayfirst=True)
                .dt.strftime("%d/%m/%Y")
                .fillna("")
            )

    # Converte numericas para inteiro
    for coluna in COLUNAS_NUMERICAS_INTEIRAS:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce").astype("Int64")

    return df


def executar_pipeline() -> pd.DataFrame:
    """
    Executa o pipeline completo de ETL:
    1. (Opcional) Baixa planilha do SharePoint quando BAIXAR_DO_SHAREPOINT=1
    2. Carrega planilha Excel
    3. Extrai referencias legislativas
    4. Enriquece com APIs da Camara e Senado
    5. Normaliza e ordena colunas
    6. Exporta para CSV

    Returns:
        DataFrame final processado.
    """
    if os.environ.get("BAIXAR_DO_SHAREPOINT") == "1":
        # Import tardio: msal so e necessario quando a flag esta ativa.
        from src.clientes.sharepoint import baixar_planilha_cgnor

        logger.info("Baixando planilha do SharePoint (BAIXAR_DO_SHAREPOINT=1)...")
        baixar_planilha_cgnor()

    caminho_planilha = os.path.join(CAMINHO_DADOS, ARQUIVO_PLANILHA)
    caminho_csv = os.path.join(CAMINHO_DADOS, ARQUIVO_CSV_FINAL)

    df = carregar_planilha(caminho_planilha)
    df = extrair_referencias(df)
    df = enriquecer_com_apis(df)
    df = normalizar_colunas(df)

    df.to_csv(caminho_csv, index=False, encoding="utf-8-sig")
    logger.info("CSV exportado com sucesso: %s (%d linhas)", caminho_csv, len(df))

    return df


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    executar_pipeline()
