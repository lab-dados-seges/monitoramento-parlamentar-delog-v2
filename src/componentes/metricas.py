"""
Componente de metricas — exibe contadores de proposicoes por origem.
"""

import pandas as pd
import streamlit as st

from src.configuracao import COLUNA_ORIGEM


def renderizar_metricas(df: pd.DataFrame):
    """Exibe as metricas (cards) com totais por origem dos dados."""
    total = len(df)
    camara = senado = bicameral = nao_encontrado = 0

    if COLUNA_ORIGEM in df.columns:
        origem = df[COLUNA_ORIGEM].fillna("").astype(str)
        camara = (origem == "Câmara").sum()
        senado = (origem == "Senado").sum()
        bicameral = (origem == "Câmara + Senado").sum()
        nao_encontrado = (origem == "Não encontrado").sum()

    st.markdown("## Proposições Monitoradas")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total", f"{total:,}")
    with col2:
        st.metric("Câmara", f"{camara:,}")
    with col3:
        st.metric("Senado", f"{senado:,}")
    with col4:
        st.metric("Câmara e Senado", f"{bicameral:,}")
    with col5:
        st.metric("Não encontrado", f"{nao_encontrado:,}")
