import os
from typing import List, Dict
import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Monitoramento de Proposições - CGNOR/DELOG",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Aplicativo de monitoramento parlamentar - Núcleo de Inteligência de Dados"
    }
)

# CSS global para melhor experiência visual
st.markdown("""
<style>
/* Cards de métricas */
[data-testid="metric-container"] {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px 16px;
}

/* Expander com fonte levemente mais destacada */
[data-testid="stExpander"] summary p {
    font-weight: 600;
}

/* Botão de download e limpar filtros */
[data-testid="stSidebar"] .stButton > button {
    border-radius: 8px;
}

/* Rodapé */
.rodape {
    text-align: center;
    font-size: 0.85em;
    color: #94a3b8;
    padding: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# Header
with st.container():
    col_esq, col_dir = st.columns([5, 1.5])
    with col_esq:
        st.title("Monitoramento de Proposições  CGNOR/DELOG/SEGES/MGI")
        st.caption(
            "Consulta e acompanhamento de proposições legislativas acompanhadas pela Coordenação-Geral de Normas - CGNOR -  "
            "tramitação na Câmara dos Deputados e no Senado Federal. \n"

            "**Atualização:** Diária · **Fonte:** Dados Internos CGNOR | API Câmara | API Senado"
        )
    with col_dir:
        st.image("image/logo_verde_mgi.png")

st.divider()


# ============================================================
# CONFIGURAÇÕES GERAIS
# ============================================================

BASE_PATH = "data"
ARQUIVO_DADOS = "df_final_bicameral.csv"

COLUNA_CHAVE_EXIBICAO = "Projeto de LEI"
COLUNA_REGEX = "Projeto de Lei - Regex"
COLUNA_ORIGEM = "Origem Dados"

LINK_COLUMNS = [
    "camara_link_inteiro_teor_parecer",
    "camara_link_inteiro_teor_pl",
    "camara_link_ficha_tramitacao",
    "camara_emendas",
    "camara_substitutivos",
    "senado_link_inteiro_teor_parecer",
    "senado_link_inteiro_teor_pl",
    "senado_link_ficha_tramitacao",
    "senado_emendas",
    "senado_substitutivos",
]

COLUNAS_DATA = [
    "camara_data_ultima_tramitacao",
    "camara_data_parecer_aprovado",
    "camara_data_proposta_pl",
    "senado_data_ultima_tramitacao",
    "senado_data_parecer_aprovado",
    "senado_data_proposta_pl",
    "1º Encaminhamento - Data",
    "2º Encaminhamento - Data",
    "3º Encaminhamento - Data",
    "Envio para a Delog - Data",
    "Envio ao Gabinete da Seges - Data",
    "Assinaturas - Data",
]

COLUNAS_NUMERICAS_SEM_DECIMAL = [
    "numero",
    "ano",
    "Validação pelo gabinete da Seges - Quantidade de dias úteis",
    "camara_id_proposicao",
    "senado_id_processo",
    "senado_codigo_materia",
]

COLUNAS_RESUMO_DETALHE = [
    "Projeto de Lei - Regex",
    "Origem Dados",
    "camara_projeto",
    "senado_projeto",
    "camara_data_proposta_pl",
    "senado_data_proposta_pl",
    "camara_propositor_pl",
    "senado_propositor_pl",
]

COLUNAS_CAMARA = [
    "camara_id_proposicao",
    "camara_projeto",
    "camara_ementa",
    "camara_data_proposta_pl",
    "camara_propositor_pl",
    "camara_partido",
    "camara_estado",
    "camara_data_ultima_tramitacao",
    "camara_orgao_ultima_tramitacao",
    "camara_descricao_tramitacao",
    "camara_situacao_ultima_tramitacao",
    "camara_despacho_ultima_tramitacao",
    "camara_data_parecer_aprovado",
    "camara_orgao_parecer",
    "camara_despacho_parecer",
    "camara_link_inteiro_teor_parecer",
    "camara_link_inteiro_teor_pl",
    "camara_link_ficha_tramitacao",
    "camara_emendas",
    "camara_substitutivos",
]

COLUNAS_SENADO = [
    "senado_id_processo",
    "senado_codigo_materia",
    "senado_projeto",
    "senado_ementa",
    "senado_data_proposta_pl",
    "senado_propositor_pl",
    "senado_partido",
    "senado_estado",
    "senado_data_ultima_tramitacao",
    "senado_orgao_ultima_tramitacao",
    "senado_situacao_ultima_tramitacao",
    "senado_data_parecer_aprovado",
    "senado_orgao_parecer",
    "senado_link_inteiro_teor_parecer",
    "senado_link_inteiro_teor_pl",
    "senado_link_ficha_tramitacao",
    "senado_emendas",
    "senado_substitutivos",
]

COLUNAS_CONTROLE_INTERNO = [
    "Nº",
    "Processo",
    "Descrição",
    "Encaminhamento prévio - Teams/E-mail",
    "1º Encaminhamento - Rementente",
    "1º Encaminhamento - Despacho /Ofício",
    "1º Encaminhamento - Data",
    "1º Encaminhamento - Prazo p/ Resposta",
    "2º Encaminhamento - Remetente",
    "2º Encaminhamento - Despacho",
    "2º Encaminhamento - Data",
    "2º Encaminhamento - Prazo p/ Resposta",
    "3º Encaminhamento - Remetente",
    "3º Encaminhamento - Despacho",
    "3º Encaminhamento - Data",
    "3º Encaminhamento - Prazo p/ Resposta",
    "Período de elaboração da Análise - Quantidade de dias úteis",
    "Envio para a Delog - Data",
    "Envio ao Gabinete da Seges - Data",
    "Validação pelo gabinete da Seges - Quantidade de dias úteis",
    "Assinaturas - Data",
    "Manifestação da Seges - Nota técnica",
    "Andamento do PL - Data/Detalhamento",
    "Observações andamento - Parecer",
]

DISPLAY_LABELS = {
    "Projeto de Lei - Regex": "Identificação",
    "camara_id_proposicao": "(Câmara) ID da Proposição",
    "camara_projeto": "(Câmara) Projeto",
    "camara_ementa": "(Câmara) Ementa",
    "camara_data_proposta_pl": "(Câmara) Data da Proposta",
    "camara_propositor_pl": "(Câmara) Propositor",
    "camara_partido": "(Câmara) Partido",
    "camara_estado": "(Câmara) Estado",
    "camara_data_ultima_tramitacao": "(Câmara) Data da Última Tramitação",
    "camara_orgao_ultima_tramitacao": "(Câmara) Órgão da Última Tramitação",
    "camara_descricao_tramitacao": "(Câmara) Descrição da Tramitação",
    "camara_situacao_ultima_tramitacao": "(Câmara) Situação da Última Tramitação",
    "camara_despacho_ultima_tramitacao": "(Câmara) Despacho da Última Tramitação",
    "camara_data_parecer_aprovado": "(Câmara) Data do Parecer Aprovado",
    "camara_orgao_parecer": "(Câmara) Órgão do Parecer",
    "camara_despacho_parecer": "(Câmara) Despacho do Parecer",
    "camara_link_inteiro_teor_parecer": "(Câmara) Link do Inteiro Teor do Parecer",
    "camara_link_inteiro_teor_pl": "(Câmara) Link do Inteiro Teor do PL",
    "camara_link_ficha_tramitacao": "(Câmara) Link da Ficha de Tramitação",
    "camara_emendas": "(Câmara) Emendas",
    "camara_substitutivos": "(Câmara) Substitutivos",

    "senado_id_processo": "(Senado) ID do Processo",
    "senado_codigo_materia": "(Senado) Código da Matéria",
    "senado_projeto": "(Senado) Projeto",
    "senado_ementa": "(Senado) Ementa",
    "senado_data_proposta_pl": "(Senado) Data da Proposta",
    "senado_propositor_pl": "(Senado) Propositor",
    "senado_partido": "(Senado) Partido",
    "senado_estado": "(Senado) Estado",
    "senado_data_ultima_tramitacao": "(Senado) Data da Última Tramitação",
    "senado_orgao_ultima_tramitacao": "(Senado) Órgão da Última Tramitação",
    "senado_situacao_ultima_tramitacao": "(Senado) Situação da Última Tramitação",
    "senado_data_parecer_aprovado": "(Senado) Data do Parecer Aprovado",
    "senado_orgao_parecer": "(Senado) Órgão do Parecer",
    "senado_link_inteiro_teor_parecer": "(Senado) Link do Inteiro Teor do Parecer",
    "senado_link_inteiro_teor_pl": "(Senado) Link do Inteiro Teor do PL",
    "senado_link_ficha_tramitacao": "(Senado) Link da Ficha de Tramitação",
    "senado_emendas": "(Senado) Emendas",
    "senado_substitutivos": "(Senado) Substitutivos",
}

# Labels sem prefixo de casa legislativa — usados dentro das abas específicas
def _strip_prefix(label_map: Dict[str, str], prefix: str) -> Dict[str, str]:
    return {k: v.replace(prefix, "").strip() for k, v in label_map.items()}

DISPLAY_LABELS_CAMARA = _strip_prefix(DISPLAY_LABELS, "(Câmara)")
DISPLAY_LABELS_SENADO = _strip_prefix(DISPLAY_LABELS, "(Senado)")

COLUNAS_RESULTADOS = [
    "Origem Dados",
    "Projeto de LEI",
    "Projeto de Lei - Regex",
    "camara_ementa",
    "camara_data_proposta_pl",
    "camara_propositor_pl",
    "camara_partido",
    "camara_estado",
    "camara_data_ultima_tramitacao",
    "camara_orgao_ultima_tramitacao",
    "camara_descricao_tramitacao",
    "camara_situacao_ultima_tramitacao",
    "camara_despacho_ultima_tramitacao",
    "camara_data_parecer_aprovado",
    "camara_orgao_parecer",
    "camara_despacho_parecer",
    "camara_link_inteiro_teor_parecer",
    "camara_link_inteiro_teor_pl",
    "camara_link_ficha_tramitacao",
    "camara_emendas",
    "camara_substitutivos",
    "senado_ementa",
    "senado_data_proposta_pl",
    "senado_propositor_pl",
    "senado_partido",
    "senado_estado",
    "senado_data_ultima_tramitacao",
    "senado_orgao_ultima_tramitacao",
    "senado_situacao_ultima_tramitacao",
    "senado_data_parecer_aprovado",
    "senado_orgao_parecer",
    "senado_link_inteiro_teor_parecer",
    "senado_link_inteiro_teor_pl",
    "senado_link_ficha_tramitacao",
    "senado_emendas",
    "senado_substitutivos",
    "Nº",
    "Processo",
    "Descrição",
    "Encaminhamento prévio - Teams/E-mail",
    "1º Encaminhamento - Rementente",
    "1º Encaminhamento - Despacho /Ofício",
    "1º Encaminhamento - Data",
    "1º Encaminhamento - Prazo p/ Resposta",
    "2º Encaminhamento - Remetente",
    "2º Encaminhamento - Despacho",
    "2º Encaminhamento - Data",
    "2º Encaminhamento - Prazo p/ Resposta",
    "3º Encaminhamento - Remetente",
    "3º Encaminhamento - Despacho",
    "3º Encaminhamento - Data",
    "3º Encaminhamento - Prazo p/ Resposta",
    "Período de elaboração da Análise - Quantidade de dias úteis",
    "Envio para a Delog - Data",
    "Envio ao Gabinete da Seges - Data",
    "Validação pelo gabinete da Seges - Quantidade de dias úteis",
    "Assinaturas - Data",
    "Manifestação da Seges - Nota técnica",
    "Andamento do PL - Data/Detalhamento",
    "Observações andamento - Parecer",
]


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def formatar_datas_para_exibicao(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in COLUNAS_DATA:
        if col in df.columns:
            serie = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
            df[col] = serie.dt.strftime("%d/%m/%Y")
            df[col] = df[col].fillna("")
    return df


def formatar_numeros_sem_decimal(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in COLUNAS_NUMERICAS_SEM_DECIMAL:
        if col in df.columns:
            serie = pd.to_numeric(df[col], errors="coerce")
            df[col] = serie.apply(lambda x: "" if pd.isna(x) else str(int(x)))
    return df


def normalizar_campos_para_exibicao(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = formatar_datas_para_exibicao(df)
    df = formatar_numeros_sem_decimal(df)
    return df


@st.cache_data(ttl=60 * 15, show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
    df = normalizar_campos_para_exibicao(df)
    if COLUNA_ORIGEM in df.columns:
        df[COLUNA_ORIGEM] = df[COLUNA_ORIGEM].fillna("Não encontrado").astype(str)
        df[COLUNA_ORIGEM] = df[COLUNA_ORIGEM].apply(lambda x: "Não encontrado" if str(x).strip() == "" else x)
    return df


def available_cols(df: pd.DataFrame, cols: List[str]) -> List[str]:
    return [c for c in cols if c in df.columns]


def normalize_text_series(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def make_link_column_config(df: pd.DataFrame) -> Dict[str, st.column_config.Column]:
    config = {}
    for col in df.columns:
        label_exibicao = DISPLAY_LABELS.get(col, col)
        if col in LINK_COLUMNS:
            config[col] = st.column_config.LinkColumn(
                label=label_exibicao,
                display_text="Abrir link",
                help=f"Abrir {label_exibicao}",
            )
        else:
            config[col] = st.column_config.Column(label_exibicao)

    pinned_cols = ["Projeto de LEI", "Projeto de Lei - Regex", "Processo", "Origem Dados"]
    for col in pinned_cols:
        if col in df.columns:
            config[col] = st.column_config.Column(DISPLAY_LABELS.get(col, col), pinned=True)
    return config


def first_non_empty(row: pd.Series, cols: List[str]) -> str:
    for col in cols:
        if col in row.index:
            val = row[col]
            if pd.notna(val) and str(val).strip():
                return str(val)
    return ""


def _render_kv_field(label: str, value, col: str):
    """Renderiza um único campo chave-valor com formatação consistente."""
    if col in LINK_COLUMNS and isinstance(value, str) and value.startswith("http"):
        st.markdown(f"**{label}:** [Abrir link]({value})")
    elif value == "Não identificado":
        st.markdown(
            f'**{label}:** <span style="'
            'display:inline-block;padding:2px 8px;border-radius:6px;'
            'background-color:#F3F4F6;color:#9CA3AF;font-size:0.9em;font-style:italic;">'
            'Não identificado</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"**{label}:** {value}")


def render_kv(df_row: pd.Series, columns: List[str], title_map: Dict[str, str] | None = None):
    cols_ok = [c for c in columns if c in df_row.index]
    if not cols_ok:
        st.info("Nenhum dado disponível nesta seção.")
        return

    has_any_data = any(pd.notna(df_row[col]) and str(df_row[col]).strip() for col in cols_ok)
    if not has_any_data:
        st.info("Nenhum dado disponível nesta seção.")
        return

    for col in cols_ok:
        label = title_map.get(col, col) if title_map else col
        value = df_row[col]
        if pd.isna(value) or str(value).strip() == "":
            value = "Não identificado"
        _render_kv_field(label, value, col)


def render_kv_two_columns(
    df_row: pd.Series,
    camara_cols: List[str],
    senado_cols: List[str],
    title_map: Dict[str, str] | None = None,
    camara_title_map: Dict[str, str] | None = None,
    senado_title_map: Dict[str, str] | None = None,
):
    """Renderiza dados em duas colunas lado a lado (Câmara e Senado)."""
    camara_cols_ok = [c for c in camara_cols if c in df_row.index]
    senado_cols_ok = [c for c in senado_cols if c in df_row.index]

    if not camara_cols_ok and not senado_cols_ok:
        st.info("Nenhum dado disponível nesta seção.")
        return

    c_map = camara_title_map or title_map
    s_map = senado_title_map or title_map

    col_esq, col_dir = st.columns(2)

    with col_esq:
        if camara_cols_ok:
            st.markdown(":blue[**Câmara dos Deputados**]")
            has_data = any(pd.notna(df_row[c]) and str(df_row[c]).strip() for c in camara_cols_ok)
            if not has_data:
                st.markdown(
                    "<span style='color:#9CA3AF;font-style:italic;'>Sem dados disponíveis</span>",
                    unsafe_allow_html=True,
                )
            else:
                for col in camara_cols_ok:
                    label = c_map.get(col, col) if c_map else col
                    value = df_row[col]
                    if pd.isna(value) or str(value).strip() == "":
                        value = "Não identificado"
                    _render_kv_field(label, value, col)

    with col_dir:
        if senado_cols_ok:
            st.markdown(":green[**Senado Federal**]")
            has_data = any(pd.notna(df_row[c]) and str(df_row[c]).strip() for c in senado_cols_ok)
            if not has_data:
                st.markdown(
                    "<span style='color:#9CA3AF;font-style:italic;'>Sem dados disponíveis</span>",
                    unsafe_allow_html=True,
                )
            else:
                for col in senado_cols_ok:
                    label = s_map.get(col, col) if s_map else col
                    value = df_row[col]
                    if pd.isna(value) or str(value).strip() == "":
                        value = "Não identificado"
                    _render_kv_field(label, value, col)


def limpar_filtros():
    st.session_state["filtro_busca_projeto"] = ""
    st.session_state["filtro_busca_ementa"] = ""
    st.session_state["filtro_busca_propositor"] = ""
    st.session_state["filtro_origem"] = []
    st.session_state["filtro_sigla"] = []


def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("🔍 Filtros de Pesquisa")
    st.sidebar.button("🧹 Limpar filtros", on_click=limpar_filtros, use_container_width=True)

    with st.sidebar.expander("📝 Busca por Texto", expanded=True):
        busca_projeto = st.text_input(
            "Número / identificação do PL",
            placeholder="Ex: PL 1234/2024",
            key="filtro_busca_projeto",
        )
        busca_ementa = st.text_input(
            "Palavra-chave na ementa",
            placeholder="Ex: servidor público",
            key="filtro_busca_ementa",
        )
        busca_propositor = st.text_input(
            "Autor da proposta",
            placeholder="Ex: João Silva",
            key="filtro_busca_propositor",
        )

    with st.sidebar.expander("📊 Filtros Categóricos"):
        origem_options = []
        if COLUNA_ORIGEM in df.columns:
            origem_options = sorted(
                [x for x in df[COLUNA_ORIGEM].dropna().astype(str).unique() if x.strip()]
            )

        origem_selecionada = st.multiselect(
            "Origem dos dados",
            options=origem_options,
            default=[],
            key="filtro_origem",
        )

        siglas_options = []
        if "sigla" in df.columns:
            siglas_options = sorted(
                [str(x) for x in df["sigla"].dropna().unique() if str(x).strip()]
            )

        siglas_selecionadas = st.multiselect(
            "Sigla",
            options=siglas_options,
            default=[],
            key="filtro_sigla",
        )

    df_view = df.copy()

    if busca_projeto:
        texto = busca_projeto.strip()
        cols_busca_projeto = available_cols(
            df_view,
            [
                "Projeto de LEI",
                "Projeto de Lei - Regex",
                "camara_projeto",
                "senado_projeto",
                "numero",
                "Processo",
            ],
        )
        if cols_busca_projeto:
            mask = pd.Series(False, index=df_view.index)
            for c in cols_busca_projeto:
                mask |= normalize_text_series(df_view[c]).str.contains(texto, case=False, na=False)
            df_view = df_view.loc[mask]

    if busca_ementa:
        texto = busca_ementa.strip()
        cols_ementa = available_cols(df_view, ["camara_ementa", "senado_ementa", "Descrição"])
        if cols_ementa:
            mask = pd.Series(False, index=df_view.index)
            for c in cols_ementa:
                mask |= normalize_text_series(df_view[c]).str.contains(texto, case=False, na=False)
            df_view = df_view.loc[mask]

    if busca_propositor:
        texto = busca_propositor.strip()
        cols_prop = available_cols(df_view, ["camara_propositor_pl", "senado_propositor_pl"])
        if cols_prop:
            mask = pd.Series(False, index=df_view.index)
            for c in cols_prop:
                mask |= normalize_text_series(df_view[c]).str.contains(texto, case=False, na=False)
            df_view = df_view.loc[mask]

    if origem_selecionada and COLUNA_ORIGEM in df_view.columns:
        df_view = df_view[df_view[COLUNA_ORIGEM].astype(str).isin(origem_selecionada)]

    if siglas_selecionadas and "sigla" in df_view.columns:
        df_view = df_view[df_view["sigla"].astype(str).isin(siglas_selecionadas)]

    return df_view


def build_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    cols_ok = available_cols(df, COLUNAS_RESULTADOS)
    return df[cols_ok].copy()


def render_metrics(df: pd.DataFrame):
    total = len(df)
    camara = senado = bicameral = nao_encontrado = 0

    if COLUNA_ORIGEM in df.columns:
        origem = df[COLUNA_ORIGEM].fillna("").astype(str)
        camara = (origem == "Câmara").sum()
        senado = (origem == "Senado").sum()
        bicameral = (origem == "Câmara + Senado").sum()
        nao_encontrado = (origem == "Não encontrado").sum()

    st.markdown("### Proposições Monitoradas")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total", f"{total:,}")
    with col2:
        st.metric("Câmara", f"{camara:,}")
    with col3:
        st.metric("Senado", f"{senado:,}")
    with col4:
        st.metric("Bicameral", f"{bicameral:,}")
    with col5:
        st.metric("Não encontrado", f"{nao_encontrado:,}")


def build_selector_label(row: pd.Series) -> str:
    projeto = row.get("Projeto de LEI", "")
    regex = row.get("Projeto de Lei - Regex", "")
    origem = row.get("Origem Dados", "")

    projeto = str(projeto).strip() if pd.notna(projeto) else ""
    regex = str(regex).strip() if pd.notna(regex) else ""
    origem = str(origem).strip() if pd.notna(origem) else ""

    partes = [p for p in [projeto, regex, origem] if p]
    return " | ".join(partes) if partes else "Registro"


# ============================================================
# CARREGAMENTO DOS DADOS
# ============================================================

try:
    caminho_arquivo = os.path.join(BASE_PATH, ARQUIVO_DADOS)
    df = load_data(caminho_arquivo)
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
    st.stop()


# ============================================================
# FILTROS
# ============================================================

df_filtrado = filter_dataframe(df)


# ============================================================
# ÚLTIMAS ATUALIZAÇÕES
# ============================================================

if not df.empty:
    colunas_data_tramitacao = ["camara_data_ultima_tramitacao", "senado_data_ultima_tramitacao"]
    colunas_disponiveis = [col for col in colunas_data_tramitacao if col in df.columns]

    if colunas_disponiveis:
        df_atualizacoes = df.copy()
        for col in colunas_disponiveis:
            df_atualizacoes[col] = pd.to_datetime(df_atualizacoes[col], format="%d/%m/%Y", errors="coerce")

        df_atualizacoes["_data_mais_recente"] = df_atualizacoes[colunas_disponiveis].max(axis=1)
        df_atualizacoes = (
            df_atualizacoes.dropna(subset=["_data_mais_recente"])
            .sort_values("_data_mais_recente", ascending=False)
            .head(10)
        )

        if not df_atualizacoes.empty:
            with st.expander("🔔 Últimas Atualizações", expanded=False):
                st.caption("Proposições com tramitações mais recentes:")
                for _, row in df_atualizacoes.iterrows():
                    pl = row.get("Projeto de Lei - Regex", "N/A")
                    origem = row.get("Origem Dados", "")

                    dt_camara = pd.to_datetime(
                        row.get("camara_data_ultima_tramitacao"), format="%d/%m/%Y", errors="coerce"
                    )
                    dt_senado = pd.to_datetime(
                        row.get("senado_data_ultima_tramitacao"), format="%d/%m/%Y", errors="coerce"
                    )

                    partes = []
                    if pd.notna(dt_camara):
                        partes.append(f"Câmara: **{pd.Timestamp(dt_camara).strftime('%d/%m/%Y')}**")
                    if pd.notna(dt_senado):
                        partes.append(f"Senado: **{pd.Timestamp(dt_senado).strftime('%d/%m/%Y')}**")

                    data_text = " · ".join(partes) if partes else "_sem data_"
                    st.markdown(f"**{pl}** ({origem}) — {data_text}")

st.divider()
render_metrics(df_filtrado)


# ============================================================
# SELEÇÃO DE REGISTRO
# ============================================================

if df_filtrado.empty:
    st.warning("Nenhum resultado encontrado com os filtros aplicados.", icon="⚠️")
    st.info("Verifique os termos de busca, tente filtros menos específicos ou use **Limpar filtros** na barra lateral.")
    st.stop()

st.subheader("Detalhamento da Proposição")

df_selecao = df_filtrado.copy().reset_index(drop=False).rename(columns={"index": "_row_id"})
df_selecao["_label"] = df_selecao.apply(build_selector_label, axis=1)

selected_label = st.selectbox(
    "Selecione uma proposição",
    options=df_selecao["_label"].tolist(),
    help="Escolha uma proposição da lista para ver todos os dados detalhados",
)

registro = df_selecao.loc[df_selecao["_label"] == selected_label].iloc[0]


# ============================================================
# ABAS DE DETALHE
# ============================================================

tab_resumo, tab_camara, tab_senado, tab_interno = st.tabs(
    ["Resumo", "Câmara", "Senado", "Controle Interno"]
)

with tab_resumo:
    st.markdown("#### Ementas")
    if "camara_ementa" in registro.index and pd.notna(registro["camara_ementa"]) and str(registro["camara_ementa"]).strip():
        st.markdown(f"**Câmara:** {registro['camara_ementa']}")
    if "senado_ementa" in registro.index and pd.notna(registro["senado_ementa"]) and str(registro["senado_ementa"]).strip():
        st.markdown(f"**Senado:** {registro['senado_ementa']}")

    st.markdown("#### Dados Gerais")
    camara_cols_resumo = [
        "camara_data_proposta_pl",
        "camara_propositor_pl",
    ]
    senado_cols_resumo = [
        "senado_data_proposta_pl",
        "senado_propositor_pl",
    ]
    render_kv_two_columns(
        registro,
        camara_cols_resumo,
        senado_cols_resumo,
        camara_title_map=DISPLAY_LABELS_CAMARA,
        senado_title_map=DISPLAY_LABELS_SENADO,
    )

    st.markdown("####  Situação Atual")
    camara_cols_situacao = [
        "camara_data_ultima_tramitacao",
        "camara_orgao_ultima_tramitacao",
        "camara_descricao_tramitacao",
        "camara_situacao_ultima_tramitacao",
        "camara_despacho_ultima_tramitacao",
    ]
    senado_cols_situacao = [
        "senado_data_ultima_tramitacao",
        "senado_orgao_ultima_tramitacao",
        "senado_situacao_ultima_tramitacao",
    ]
    render_kv_two_columns(
        registro,
        camara_cols_situacao,
        senado_cols_situacao,
        camara_title_map=DISPLAY_LABELS_CAMARA,
        senado_title_map=DISPLAY_LABELS_SENADO,
    )

with tab_camara:
    camara_left = [
        "camara_id_proposicao",
        "camara_projeto",
        "camara_ementa",
        "camara_data_proposta_pl",
        "camara_propositor_pl",
        "camara_partido",
        "camara_estado",
    ]
    camara_right = [
        "camara_data_ultima_tramitacao",
        "camara_orgao_ultima_tramitacao",
        "camara_descricao_tramitacao",
        "camara_situacao_ultima_tramitacao",
        "camara_despacho_ultima_tramitacao",
        "camara_data_parecer_aprovado",
        "camara_orgao_parecer",
        "camara_despacho_parecer",
        "camara_link_inteiro_teor_parecer",
        "camara_link_inteiro_teor_pl",
        "camara_link_ficha_tramitacao",
        "camara_emendas",
        "camara_substitutivos",
    ]
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(":blue[**Identificação e Autoria**]")
        render_kv(registro, camara_left, title_map=DISPLAY_LABELS_CAMARA)
    with col2:
        st.markdown(":blue[**Tramitação e Parecer**]")
        render_kv(registro, camara_right, title_map=DISPLAY_LABELS_CAMARA)

with tab_senado:
    senado_left = [
        "senado_id_processo",
        "senado_codigo_materia",
        "senado_projeto",
        "senado_ementa",
        "senado_data_proposta_pl",
        "senado_propositor_pl",
        "senado_partido",
        "senado_estado",
    ]
    senado_right = [
        "senado_data_ultima_tramitacao",
        "senado_orgao_ultima_tramitacao",
        "senado_situacao_ultima_tramitacao",
        "senado_data_parecer_aprovado",
        "senado_orgao_parecer",
        "senado_link_inteiro_teor_parecer",
        "senado_link_inteiro_teor_pl",
        "senado_link_ficha_tramitacao",
        "senado_emendas",
        "senado_substitutivos",
    ]
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(":green[**Identificação e Autoria**]")
        render_kv(registro, senado_left, title_map=DISPLAY_LABELS_SENADO)
    with col2:
        st.markdown(":green[**Tramitação e Parecer**]")
        render_kv(registro, senado_right, title_map=DISPLAY_LABELS_SENADO)

with tab_interno:
    controle_left = COLUNAS_CONTROLE_INTERNO[: len(COLUNAS_CONTROLE_INTERNO) // 2]
    controle_right = COLUNAS_CONTROLE_INTERNO[len(COLUNAS_CONTROLE_INTERNO) // 2 :]
    col1, col2 = st.columns(2)
    with col1:
        render_kv(registro, controle_left, title_map=DISPLAY_LABELS)
    with col2:
        render_kv(registro, controle_right, title_map=DISPLAY_LABELS)


# ============================================================
# DOWNLOAD DOS DADOS
# ============================================================

st.divider()
st.markdown("### Download dos Dados")

st.download_button(
    label="⬇️ Baixar Planilha (CSV)",
    data=df.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"dados_proposicoes_{pd.Timestamp.now().strftime('%d-%m-%Y')}.csv",
    mime="text/csv",
    help="Download da planilha completa com todos os dados em formato CSV",
)
st.caption("O arquivo CSV contém todos os campos disponíveis."
)

# Rodapé
st.markdown("""
<hr style="height:1px;border:none;color:#e2e8f0;background-color:#e2e8f0;margin-top:2rem;" />
<div class="rodape">
    Desenvolvido pelo <b>Núcleo de Inteligência de Dados</b> · <b>CDATA/CGINF/SEGES/MGI</b>
</div>
""", unsafe_allow_html=True)
