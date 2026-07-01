"""
Helpers compartilhados entre as paginas do app Streamlit.

Centraliza:
  - Configuracao da pagina (set_page_config + CSS) e cabecalho/rodape
  - Carregamento e formatacao do CSV (com cache)
"""

import os
from typing import Optional

import pandas as pd
import streamlit as st

from src.configuracao import (
    ARQUIVO_CSV_FINAL,
    CACHE_TTL_SEGUNDOS,
    CAMINHO_DADOS,
    COLUNAS_DATA,
    COLUNAS_NUMERICAS_INTEIRAS,
    COLUNA_ORIGEM,
)


# ============================================================
# CSS GLOBAL DA APLICACAO
# ============================================================

_CSS_GLOBAL = """
<style>
/* Cards de metricas */
[data-testid="metric-container"] {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px 16px;
}
[data-testid="stExpander"] summary p {
    font-weight: 600;
}
[data-testid="stSidebar"] .stButton > button {
    border-radius: 8px;
}
.rodape {
    text-align: center;
    font-size: 0.85em;
    color: #94a3b8;
    padding: 0.5rem 0;
}
</style>
"""


def configurar_pagina(titulo: str) -> None:
    """
    Aplica set_page_config padronizado e injeta CSS global.

    Deve ser chamado UMA VEZ no script principal (app.py), antes de
    st.navigation(...).run(). As paginas individuais nao devem chamar
    novamente set_page_config.

    Args:
        titulo: Titulo exibido na aba do navegador.
    """
    st.set_page_config(
        page_title=titulo,
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "About": (
                "Aplicativo de monitoramento parlamentar - "
                "Nucleo de Inteligencia de Dados"
            )
        },
    )
    st.markdown(_CSS_GLOBAL, unsafe_allow_html=True)


def renderizar_header() -> None:
    """Renderiza o cabecalho com titulo, descricao e logo. Usado por cada pagina."""
    with st.container():
        col_esq, col_dir = st.columns([5, 1.5])
        with col_esq:
            st.title("Monitoramento de Proposições  CGNOR/DELOG/SEGES/MGI")
            st.caption(
                "Consulta e acompanhamento de proposições legislativas "
                "monitoradas pela Coordenação-Geral de Normas - CGNOR  \n"                
                "**Atualização:** Diária · **Fonte:** Dados Internos CGNOR | "
                "API Câmara | API Senado"
            )
        with col_dir:
            st.caption("Ministério da Gestão e Inovação em Serviços Públicos - MGI")
            #st.image("image/logo_verde_mgi.png")
    st.divider()


def renderizar_rodape() -> None:
    """Rodape padrao usado nas paginas."""
    st.markdown(
        """
<hr style="height:1px;border:none;color:#e2e8f0;background-color:#e2e8f0;
margin-top:2rem;" />
<div class="rodape">
    Desenvolvido pelo <b>Núcleo de Inteligência de Dados</b> ·
    <b>CDATA/CGINF/SEGES/MGI</b>
</div>
""",
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=CACHE_TTL_SEGUNDOS, show_spinner=False)
def carregar_dados(caminho: str) -> pd.DataFrame:
    """Carrega e formata o CSV de dados processados (com cache)."""
    df = pd.read_csv(caminho, encoding="utf-8-sig")
    df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]

    for coluna in COLUNAS_DATA:
        if coluna in df.columns:
            serie = pd.to_datetime(df[coluna], errors="coerce", format="%d/%m/%Y")
            df[coluna] = serie.dt.strftime("%d/%m/%Y").fillna("")

    for coluna in COLUNAS_NUMERICAS_INTEIRAS:
        if coluna in df.columns:
            serie = pd.to_numeric(df[coluna], errors="coerce")
            df[coluna] = serie.apply(lambda x: "" if pd.isna(x) else str(int(x)))

    if COLUNA_ORIGEM in df.columns:
        df[COLUNA_ORIGEM] = (
            df[COLUNA_ORIGEM]
            .fillna("Não encontrado")
            .astype(str)
            .replace(r"^\s*$", "Não encontrado", regex=True)
        )

    return df


def obter_dataframe(caminho: Optional[str] = None) -> pd.DataFrame:
    """
    Wrapper que carrega o CSV principal com tratamento de erros.

    Em caso de falha, exibe um st.error e interrompe a execucao da pagina.
    """
    caminho_arquivo = caminho or os.path.join(CAMINHO_DADOS, ARQUIVO_CSV_FINAL)
    try:
        return carregar_dados(caminho_arquivo)
    except FileNotFoundError:
        st.error(
            f"Arquivo de dados não encontrado: `{caminho_arquivo}`. "
            "Execute o pipeline de atualização primeiro."
        )
        st.stop()
    except pd.errors.ParserError as erro:
        st.error(f"Erro ao interpretar o arquivo CSV: {erro}")
        st.stop()
    except Exception as erro:
        st.error(f"Erro inesperado ao carregar os dados: {erro}")
        st.stop()
