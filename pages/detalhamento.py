"""
Pagina de Detalhamento — visao tradicional registro a registro.

Mostra metricas, ultimas atualizacoes e abas de detalhe (Resumo,
Camara, Senado, Controle Interno e Calor Legislativo) para a
proposicao selecionada.
"""

import sys
from pathlib import Path

# Permite imports 'from src...' quando o arquivo e executado como pagina
_RAIZ_PROJETO = str(Path(__file__).resolve().parent.parent)
if _RAIZ_PROJETO not in sys.path:
    sys.path.insert(0, _RAIZ_PROJETO)

import pandas as pd
import streamlit as st

from src.componentes.atualizacoes import renderizar_ultimas_atualizacoes
from src.componentes.detalhes import (
    renderizar_aba_calor_legislativo,
    renderizar_aba_camara,
    renderizar_aba_controle_interno,
    renderizar_aba_resumo,
    renderizar_aba_senado,
)
from src.componentes.filtros import renderizar_filtros
from src.componentes.metricas import renderizar_metricas
from src.interface import obter_dataframe, renderizar_header, renderizar_rodape


renderizar_header()

df = obter_dataframe()
df_filtrado = renderizar_filtros(df)


# ============================================================
# METRICAS E ATUALIZACOES
# ============================================================

renderizar_metricas(df_filtrado)

st.divider()
renderizar_ultimas_atualizacoes(df)


# ============================================================
# SELECAO DE REGISTRO E ABAS DE DETALHE
# ============================================================

if df_filtrado.empty:
    st.warning("Nenhum resultado encontrado com os filtros aplicados.", icon="⚠️")
    st.info(
        "Verifique os termos de busca, tente filtros menos específicos "
        "ou use **Limpar filtros** na barra lateral."
    )
    st.stop()

st.subheader("Detalhamento da Proposição")


def _construir_rotulo_seletor(linha: pd.Series) -> str:
    """Monta o rotulo de exibicao para o selectbox de proposicoes."""
    projeto = (
        str(linha.get("Projeto de LEI", "")).strip()
        if pd.notna(linha.get("Projeto de LEI"))
        else ""
    )
    regex = (
        str(linha.get("Projeto de Lei - Regex", "")).strip()
        if pd.notna(linha.get("Projeto de Lei - Regex"))
        else ""
    )
    origem = (
        str(linha.get("Origem Dados", "")).strip()
        if pd.notna(linha.get("Origem Dados"))
        else ""
    )
    partes = [p for p in [projeto, regex, origem] if p]
    return " | ".join(partes) if partes else "Registro"


df_selecao = (
    df_filtrado.copy().reset_index(drop=False).rename(columns={"index": "_row_id"})
)
df_selecao["_label"] = df_selecao.apply(_construir_rotulo_seletor, axis=1)

rotulo_selecionado = st.selectbox(
    "Selecione uma proposição",
    options=df_selecao["_label"].tolist(),
    help="Escolha uma proposição da lista para ver todos os dados detalhados",
)

registro = df_selecao.loc[df_selecao["_label"] == rotulo_selecionado].iloc[0]

tab_resumo, tab_camara, tab_senado, tab_interno, tab_calor = st.tabs(
    ["Resumo", "Câmara", "Senado", "Controle Interno", "Calor Legislativo"]
)

with tab_resumo:
    renderizar_aba_resumo(registro)

with tab_camara:
    renderizar_aba_camara(registro)

with tab_senado:
    renderizar_aba_senado(registro)

with tab_interno:
    renderizar_aba_controle_interno(registro)

with tab_calor:
    renderizar_aba_calor_legislativo(registro)


# ============================================================
# DOWNLOAD DOS DADOS
# ============================================================

st.divider()
st.markdown("### Download dos Dados")

st.download_button(
    label="Baixar Planilha (CSV)",
    data=df.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"dados_proposicoes_{pd.Timestamp.now(tz='America/Sao_Paulo').strftime('%d-%m-%Y')}.csv",
    mime="text/csv",
    help="Download da planilha completa com todos os dados em formato CSV",
)
st.caption("O arquivo CSV contém todos os campos disponíveis.")

renderizar_rodape()
