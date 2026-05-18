"""
Aplicativo Streamlit — Monitoramento de Proposicoes CGNOR/DELOG.

Execute com:
    streamlit run app.py
"""

import os
import sys
from pathlib import Path

# Garante que a raiz do projeto esta no sys.path para resolver 'from src...'
_RAIZ_PROJETO = str(Path(__file__).resolve().parent)
if _RAIZ_PROJETO not in sys.path:
    sys.path.insert(0, _RAIZ_PROJETO)

import pandas as pd
import streamlit as st

from src.componentes.atualizacoes import renderizar_ultimas_atualizacoes
from src.componentes.detalhes import (
    renderizar_aba_camara,
    renderizar_aba_controle_interno,
    renderizar_aba_resumo,
    renderizar_aba_senado,
)
from src.componentes.filtros import renderizar_filtros
from src.componentes.metricas import renderizar_metricas
from src.configuracao import (
    ARQUIVO_CSV_FINAL,
    CACHE_TTL_SEGUNDOS,
    CAMINHO_DADOS,
    COLUNAS_DATA,
    COLUNAS_LINK,
    COLUNAS_NUMERICAS_INTEIRAS,
    COLUNA_ORIGEM,
    ROTULOS_EXIBICAO,
)


# ============================================================
# CONFIGURACAO DA PAGINA
# ============================================================

st.set_page_config(
    page_title="Monitoramento de Proposicoes - CGNOR/DELOG",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Aplicativo de monitoramento parlamentar - Nucleo de Inteligencia de Dados"
    },
)

st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

# Header
with st.container():
    col_esq, col_dir = st.columns([5, 1.5])
    with col_esq:
        st.title("Monitoramento de Proposições  CGNOR/DELOG/SEGES/MGI")
        st.caption(
            "Consulta e acompanhamento de proposições legislativas acompanhadas "
            "pela Coordenação-Geral de Normas - CGNOR -  "
            "tramitação na Câmara dos Deputados e no Senado Federal. \n"
            "**Atualização:** Diária · **Fonte:** Dados Internos CGNOR | API Câmara | API Senado"
        )
    with col_dir:
        st.image("image/logo_verde_mgi.png")

st.divider()


# ============================================================
# FUNCOES DE CARREGAMENTO E FORMATACAO
# ============================================================


@st.cache_data(ttl=CACHE_TTL_SEGUNDOS, show_spinner=False)
def carregar_dados(caminho: str) -> pd.DataFrame:
    """Carrega e formata o CSV de dados processados."""
    df = pd.read_csv(caminho, encoding="utf-8-sig")
    df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]

    # Formata datas para dd/mm/aaaa
    for coluna in COLUNAS_DATA:
        if coluna in df.columns:
            serie = pd.to_datetime(df[coluna], errors="coerce", format="%d/%m/%Y")
            df[coluna] = serie.dt.strftime("%d/%m/%Y").fillna("")

    # Remove casas decimais de colunas inteiras
    for coluna in COLUNAS_NUMERICAS_INTEIRAS:
        if coluna in df.columns:
            serie = pd.to_numeric(df[coluna], errors="coerce")
            df[coluna] = serie.apply(lambda x: "" if pd.isna(x) else str(int(x)))

    # Preenche origem ausente
    if COLUNA_ORIGEM in df.columns:
        df[COLUNA_ORIGEM] = (
            df[COLUNA_ORIGEM]
            .fillna("Não encontrado")
            .astype(str)
            .replace(r"^\s*$", "Não encontrado", regex=True)
        )

    return df


def _construir_rotulo_seletor(linha: pd.Series) -> str:
    """Monta o rotulo de exibicao para o selectbox de proposicoes."""
    projeto = str(linha.get("Projeto de LEI", "")).strip() if pd.notna(linha.get("Projeto de LEI")) else ""
    regex = str(linha.get("Projeto de Lei - Regex", "")).strip() if pd.notna(linha.get("Projeto de Lei - Regex")) else ""
    origem = str(linha.get("Origem Dados", "")).strip() if pd.notna(linha.get("Origem Dados")) else ""

    partes = [p for p in [projeto, regex, origem] if p]
    return " | ".join(partes) if partes else "Registro"


def _configurar_colunas_tabela(df: pd.DataFrame) -> dict:
    """Monta a configuracao de colunas para o st.dataframe (links clicaveis, labels, etc.)."""
    config = {}
    for coluna in df.columns:
        rotulo = ROTULOS_EXIBICAO.get(coluna, coluna)
        if coluna in COLUNAS_LINK:
            config[coluna] = st.column_config.LinkColumn(
                label=rotulo,
                display_text="Abrir link",
                help=f"Abrir {rotulo}",
            )
        else:
            config[coluna] = st.column_config.Column(rotulo)

    colunas_fixas = ["Projeto de LEI", "Projeto de Lei - Regex", "Processo", "Origem Dados"]
    for coluna in colunas_fixas:
        if coluna in df.columns:
            config[coluna] = st.column_config.Column(
                ROTULOS_EXIBICAO.get(coluna, coluna), pinned=True
            )
    return config


# ============================================================
# CARREGAMENTO DOS DADOS
# ============================================================

try:
    caminho_arquivo = os.path.join(CAMINHO_DADOS, ARQUIVO_CSV_FINAL)
    df = carregar_dados(caminho_arquivo)
except FileNotFoundError:
    st.error(
        f"Arquivo de dados não encontrado: `{CAMINHO_DADOS}/{ARQUIVO_CSV_FINAL}`. "
        "Execute o pipeline de atualização primeiro."
    )
    st.stop()
except pd.errors.ParserError as erro:
    st.error(f"Erro ao interpretar o arquivo CSV: {erro}")
    st.stop()
except Exception as erro:
    st.error(f"Erro inesperado ao carregar os dados: {erro}")
    st.stop()


# ============================================================
# FILTROS
# ============================================================

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

df_selecao = df_filtrado.copy().reset_index(drop=False).rename(columns={"index": "_row_id"})
df_selecao["_label"] = df_selecao.apply(_construir_rotulo_seletor, axis=1)

rotulo_selecionado = st.selectbox(
    "Selecione uma proposição",
    options=df_selecao["_label"].tolist(),
    help="Escolha uma proposição da lista para ver todos os dados detalhados",
)

registro = df_selecao.loc[df_selecao["_label"] == rotulo_selecionado].iloc[0]

tab_resumo, tab_camara, tab_senado, tab_interno = st.tabs(
    ["Resumo", "Câmara", "Senado", "Controle Interno"]
)

with tab_resumo:
    renderizar_aba_resumo(registro)

with tab_camara:
    renderizar_aba_camara(registro)

with tab_senado:
    renderizar_aba_senado(registro)

with tab_interno:
    renderizar_aba_controle_interno(registro)


# ============================================================
# DOWNLOAD DOS DADOS
# ============================================================

st.divider()
st.markdown("### Download dos Dados")

st.download_button(
    label="Baixar Planilha (CSV)",
    data=df.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"dados_proposicoes_{pd.Timestamp.now().strftime('%d-%m-%Y')}.csv",
    mime="text/csv",
    help="Download da planilha completa com todos os dados em formato CSV",
)
st.caption("O arquivo CSV contém todos os campos disponíveis.")

# Rodape
st.markdown(
    """
<hr style="height:1px;border:none;color:#e2e8f0;background-color:#e2e8f0;margin-top:2rem;" />
<div class="rodape">
    Desenvolvido pelo <b>Núcleo de Inteligência de Dados</b> · <b>CDATA/CGINF/SEGES/MGI</b>
</div>
""",
    unsafe_allow_html=True,
)
