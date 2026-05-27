"""
Aplicativo Streamlit — Monitoramento de Proposicoes CGNOR/DELOG.

Ponto de entrada: configura a pagina e despacha a navegacao
entre as paginas disponiveis (Detalhamento e Tabela de Proposicoes).

Execute com:
    streamlit run app.py
"""

import sys
from pathlib import Path

# Garante que a raiz do projeto esta no sys.path para resolver 'from src...'
_RAIZ_PROJETO = str(Path(__file__).resolve().parent)
if _RAIZ_PROJETO not in sys.path:
    sys.path.insert(0, _RAIZ_PROJETO)

import streamlit as st

from src.interface import configurar_pagina


configurar_pagina(titulo="Monitoramento de Proposicoes - CGNOR/DELOG")

paginas = [
    st.Page(
        "pages/detalhamento.py",
        title="Detalhamento",
        icon="📄",
        default=True,
    ),
    st.Page(
        "pages/tabela_proposicoes.py",
        title="Tabela de Proposições",
        icon="📋",
    ),
]

st.navigation(paginas).run()
