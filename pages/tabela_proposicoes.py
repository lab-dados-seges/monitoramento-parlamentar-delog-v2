"""
Pagina de Tabela de Proposicoes.

Apresenta as proposicoes em formato tabular com colunas selecionadas,
links clicaveis para a ficha de tramitacao e destaque visual para o
nivel de Calor Legislativo.
"""

import sys
from pathlib import Path

# Permite imports 'from src...' quando o arquivo e executado como pagina
_RAIZ_PROJETO = str(Path(__file__).resolve().parent.parent)
if _RAIZ_PROJETO not in sys.path:
    sys.path.insert(0, _RAIZ_PROJETO)

import pandas as pd
import streamlit as st

from src.calor_legislativo import (
    CORES_NIVEL,
    CORES_NIVEL_FUNDO,
    ICONES_NIVEL,
    NIVEL_INDEFINIDO,
)
from src.componentes.filtros import renderizar_filtros
from src.configuracao import (
    COLUNA_NIVEL_CALOR_CAMARA,
    COLUNA_SCORE_CALOR_CAMARA,
)
from src.interface import obter_dataframe, renderizar_header, renderizar_rodape


# ============================================================
# COLUNAS EXIBIDAS
# ============================================================

# (coluna_origem, rotulo, tipo) — tipo controla o column_config do dataframe
_COLUNAS_TABELA = [
    ("Projeto de Lei - Regex", "PL", "texto"),
    ("_calor_display", "Calor Legislativo", "calor"),
    ("Origem Dados", "Origem", "texto"),
    ("camara_ementa", "Ementa (Câmara)", "ementa"),
    ("senado_ementa", "Ementa (Senado)", "ementa"),
    ("camara_data_ultima_tramitacao", "Última Tramitação (Câmara)", "data"),
    ("camara_situacao_ultima_tramitacao", "Situação (Câmara)", "texto"),
    ("camara_regime", "Regime", "texto"),
    ("senado_data_ultima_tramitacao", "Última Tramitação (Senado)", "data"),
    ("senado_situacao_ultima_tramitacao", "Situação (Senado)", "texto"),
    ("camara_link_ficha_tramitacao", "Ficha (Câmara)", "link"),
    ("senado_link_ficha_tramitacao", "Ficha (Senado)", "link"),
]


def _construir_coluna_calor(df: pd.DataFrame) -> pd.Series:
    """Constroi a coluna de exibicao do calor: icone + nivel + score."""
    if COLUNA_NIVEL_CALOR_CAMARA not in df.columns:
        return pd.Series([""] * len(df), index=df.index)

    niveis = df[COLUNA_NIVEL_CALOR_CAMARA].fillna("").astype(str).str.strip()
    scores = pd.to_numeric(
        df.get(COLUNA_SCORE_CALOR_CAMARA, pd.Series(index=df.index)),
        errors="coerce",
    )

    def _formatar(nivel: str, score) -> str:
        if not nivel:
            return ""
        icone = ICONES_NIVEL.get(nivel, ICONES_NIVEL[NIVEL_INDEFINIDO])
        if pd.notna(score):
            return f"{icone} {nivel} · {float(score):.2f}"
        return f"{icone} {nivel}"

    return pd.Series(
        [_formatar(n, s) for n, s in zip(niveis, scores)], index=df.index
    )


def _estilizar_calor(valor: str) -> str:
    """Retorna estilo CSS para a celula de calor conforme o nivel."""
    if not isinstance(valor, str) or not valor:
        return ""
    for nivel, cor_texto in CORES_NIVEL.items():
        if nivel in valor:
            cor_fundo = CORES_NIVEL_FUNDO[nivel]
            return (
                f"background-color: {cor_fundo}; color: {cor_texto}; "
                "font-weight: 600;"
            )
    return ""


def _truncar(texto, limite: int = 140) -> str:
    """Trunca strings longas mantendo legibilidade na tabela."""
    if pd.isna(texto):
        return ""
    s = str(texto).strip()
    return s if len(s) <= limite else s[: limite - 1].rstrip() + "…"


def _montar_column_config(colunas_visiveis):
    """Monta o dicionario de column_config para o st.dataframe."""
    config = {}
    for coluna, rotulo, tipo in colunas_visiveis:
        if tipo == "link":
            config[coluna] = st.column_config.LinkColumn(
                label=rotulo,
                display_text="Abrir",
                help=f"Abrir {rotulo}",
                width="small",
            )
        elif tipo == "ementa":
            config[coluna] = st.column_config.TextColumn(
                rotulo, width="large", help="Texto completo no detalhamento."
            )
        elif tipo == "calor":
            config[coluna] = st.column_config.TextColumn(
                rotulo, width="medium", help="Score Cl e nível de calor (Câmara)."
            )
        elif tipo == "data":
            config[coluna] = st.column_config.TextColumn(rotulo, width="small")
        else:
            config[coluna] = st.column_config.TextColumn(rotulo)
    # Coluna fixada
    if "Projeto de Lei - Regex" in config:
        config["Projeto de Lei - Regex"] = st.column_config.TextColumn(
            "PL", pinned=True, width="small"
        )
    return config


# ============================================================
# PAGINA
# ============================================================

renderizar_header()

df = obter_dataframe()
df_filtrado = renderizar_filtros(df)

st.subheader("Tabela de Proposições")

if df_filtrado.empty:
    st.warning("Nenhum resultado encontrado com os filtros aplicados.", icon="⚠️")
    st.info(
        "Verifique os termos de busca, tente filtros menos específicos "
        "ou use **Limpar filtros** na barra lateral."
    )
    st.stop()

# Monta o dataframe de exibicao
df_tabela = df_filtrado.copy()
df_tabela["_calor_display"] = _construir_coluna_calor(df_tabela)

# Trunca ementas para a tabela ficar legivel
for col in ("camara_ementa", "senado_ementa"):
    if col in df_tabela.columns:
        df_tabela[col] = df_tabela[col].apply(_truncar)

colunas_visiveis = [
    (col, rot, tipo)
    for (col, rot, tipo) in _COLUNAS_TABELA
    if col in df_tabela.columns
]
nomes_colunas = [c for c, _, _ in colunas_visiveis]

styler = df_tabela[nomes_colunas].style.map(
    _estilizar_calor, subset=["_calor_display"]
) if "_calor_display" in nomes_colunas else df_tabela[nomes_colunas].style

st.caption(
    f"Exibindo **{len(df_tabela)}** proposições. "
    "Use os filtros na barra lateral para refinar a lista."
)

st.dataframe(
    styler,
    use_container_width=True,
    hide_index=True,
    column_config=_montar_column_config(colunas_visiveis),
    height=620,
)

# Download da visao filtrada
st.divider()
st.download_button(
    label="Baixar visão filtrada (CSV)",
    data=df_filtrado.to_csv(index=False).encode("utf-8-sig"),
    file_name=(
        f"dados_proposicoes_filtrado_"
        f"{pd.Timestamp.now(tz='America/Sao_Paulo').strftime('%d-%m-%Y')}.csv"
    ),
    mime="text/csv",
    help="Download do CSV com todas as colunas, considerando os filtros aplicados.",
)

renderizar_rodape()
