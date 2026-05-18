"""
Componentes de filtragem — sidebar com busca por texto e filtros categoricos.
"""

from typing import List

import pandas as pd
import streamlit as st

from src.configuracao import COLUNA_ORIGEM


def _colunas_disponiveis(df: pd.DataFrame, colunas: List[str]) -> List[str]:
    """Retorna apenas as colunas que existem no DataFrame."""
    return [c for c in colunas if c in df.columns]


def _normalizar_texto(serie: pd.Series) -> pd.Series:
    """Preenche nulos e converte para string limpa."""
    return serie.fillna("").astype(str).str.strip()


def limpar_filtros():
    """Reseta todos os filtros para o estado inicial."""
    st.session_state["filtro_busca_projeto"] = ""
    st.session_state["filtro_busca_ementa"] = ""
    st.session_state["filtro_busca_propositor"] = ""
    st.session_state["filtro_origem"] = []
    st.session_state["filtro_sigla"] = []


def renderizar_filtros(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renderiza a sidebar de filtros e retorna o DataFrame filtrado.

    Filtros disponiveis:
    - Busca por numero/identificacao do PL
    - Busca por palavra-chave na ementa
    - Busca por autor da proposta
    - Filtro por origem dos dados
    - Filtro por sigla
    """
    st.sidebar.header("Filtros de Pesquisa")

    with st.sidebar.expander("Busca por Texto", expanded=True):
        busca_projeto = st.text_input(
            "Numero / identificacao do PL",
            placeholder="Ex: PL 1234/2024",
            key="filtro_busca_projeto",
        )
        busca_ementa = st.text_input(
            "Palavra-chave na ementa",
            placeholder="Ex: servidor publico",
            key="filtro_busca_ementa",
        )
        busca_propositor = st.text_input(
            "Autor da proposta",
            placeholder="Ex: Joao Silva",
            key="filtro_busca_propositor",
        )

    with st.sidebar.expander("Filtros Categoricos"):
        opcoes_origem = []
        if COLUNA_ORIGEM in df.columns:
            opcoes_origem = sorted(
                x for x in df[COLUNA_ORIGEM].dropna().astype(str).unique() if x.strip()
            )

        origem_selecionada = st.multiselect(
            "Origem dos dados",
            options=opcoes_origem,
            key="filtro_origem",
        )

        opcoes_sigla = []
        if "sigla" in df.columns:
            opcoes_sigla = sorted(
                str(x) for x in df["sigla"].dropna().unique() if str(x).strip()
            )

        siglas_selecionadas = st.multiselect(
            "Sigla",
            options=opcoes_sigla,
            key="filtro_sigla",
        )

    st.sidebar.button(
        "Limpar filtros",
        on_click=limpar_filtros,
        use_container_width=True,
    )

    # Aplica filtros
    df_filtrado = df.copy()

    # Buscas textuais — cada tupla: (valor digitado, colunas onde buscar)
    buscas_texto = [
        (busca_projeto, [
            "Projeto de LEI", "Projeto de Lei - Regex",
            "camara_projeto", "senado_projeto", "numero", "Processo",
        ]),
        (busca_ementa, ["camara_ementa", "senado_ementa", "Descrição"]),
        (busca_propositor, ["camara_propositor_pl", "senado_propositor_pl"]),
    ]
    for termo, colunas_alvo in buscas_texto:
        if not termo:
            continue
        colunas = _colunas_disponiveis(df_filtrado, colunas_alvo)
        if colunas:
            mascara = pd.Series(False, index=df_filtrado.index)
            for coluna in colunas:
                mascara |= _normalizar_texto(df_filtrado[coluna]).str.contains(
                    termo.strip(), case=False, na=False
                )
            df_filtrado = df_filtrado.loc[mascara]

    # Filtros categóricos
    if origem_selecionada and COLUNA_ORIGEM in df_filtrado.columns:
        df_filtrado = df_filtrado[
            df_filtrado[COLUNA_ORIGEM].astype(str).isin(origem_selecionada)
        ]

    if siglas_selecionadas and "sigla" in df_filtrado.columns:
        df_filtrado = df_filtrado[
            df_filtrado["sigla"].astype(str).isin(siglas_selecionadas)
        ]

    return df_filtrado
