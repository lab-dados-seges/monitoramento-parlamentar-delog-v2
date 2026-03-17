import os
from typing import List, Dict
import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Monitoramento de Projetos de Lei - CGNOR/DELOG",
    layout="wide",
)

col_esq, col_dir = st.columns([5, 1.5])

with col_esq:
    st.title("Monitoramento de Projetos de Lei - CGNOR/DELOG/SEGES/MGI")
    st.caption(
        '''
        Este aplicativo permite consultar proposições legislativas previamente cadastradas pela Coordenação-Geral de Normas
        para obter informações de interesse e acompanhar a tramitação no Congresso Nacional.

        Fonte de dados: CGNOR - Dados Internos | API Câmara | API Senado
               
        '''
    )

with col_dir:
    st.image("image/logo_verde_mgi.png")








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
    "camara_situacao_ultima_tramitacao",
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
    "camara_situacao_ultima_tramitacao": "(Câmara) Situação da Última Tramitação",
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
    "camara_situacao_ultima_tramitacao",
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

    pinned_cols = [
        "Projeto de LEI",
        "Projeto de Lei - Regex",
        "Processo",
        "Origem Dados"
        
    ]
    for col in pinned_cols:
        if col in df.columns:
            config[col] = st.column_config.Column(
                DISPLAY_LABELS.get(col, col),
                pinned=True,
            )

    return config


def first_non_empty(row: pd.Series, cols: List[str]) -> str:
    for col in cols:
        if col in row.index:
            val = row[col]
            if pd.notna(val) and str(val).strip():
                return str(val)
    return ""


def render_kv(df_row: pd.Series, columns: List[str], title_map: Dict[str, str] | None = None):
    cols_ok = [c for c in columns if c in df_row.index]
    if not cols_ok:
        st.info("Nenhum dado disponível nesta seção.")
        return

    for col in cols_ok:
        label = title_map.get(col, col) if title_map else col
        value = df_row[col]

        if pd.isna(value) or str(value).strip() == "":
            value = "Não identificado"

        if col in LINK_COLUMNS and isinstance(value, str) and value.startswith("http"):
            st.markdown(f"**{label}:** [Abrir link]({value})")
        elif value == "Não identificado":
            st.markdown(
                f"""
                **{label}:**
                <span style="
                    display:inline-block;
                    padding: 2px 8px;
                    border-radius: 8px;
                    background-color: #F3F4F6;
                    color: #6B7280;
                    font-size: 0.92em;
                    font-style: italic;
                ">
                    Não identificado
                </span>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(f"**{label}:** {value}")


def limpar_filtros():
    st.session_state["filtro_busca_projeto"] = ""
    st.session_state["filtro_busca_ementa"] = ""
    st.session_state["filtro_busca_propositor"] = ""
    st.session_state["filtro_origem"] = []
    st.session_state["filtro_sigla"] = []


def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filtros")
    st.sidebar.button("🧹 Limpar filtros", on_click=limpar_filtros, use_container_width=True)

    busca_projeto = st.sidebar.text_input(
        "Buscar por número / identificação do PL",
        key="filtro_busca_projeto",
    )
    busca_ementa = st.sidebar.text_input(
        "Buscar por palavra-chave na ementa",
        key="filtro_busca_ementa",
    )
    busca_propositor = st.sidebar.text_input(
        "Buscar pelo autor da Proposta",
        key="filtro_busca_propositor",
    )

    origem_options = []
    if COLUNA_ORIGEM in df.columns:
        origem_options = sorted(
            [x for x in df[COLUNA_ORIGEM].dropna().astype(str).unique() if x.strip()]
        )

    origem_selecionada = st.sidebar.multiselect(
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

    siglas_selecionadas = st.sidebar.multiselect(
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
    resumo = df[cols_ok].copy()
    return resumo


def render_metrics(df: pd.DataFrame):
    total = len(df)

    camara = 0
    senado = 0
    bicameral = 0

    if COLUNA_ORIGEM in df.columns:
        origem = df[COLUNA_ORIGEM].fillna("").astype(str)
        camara = (origem == "Câmara").sum()
        senado = (origem == "Senado").sum()
        bicameral = (origem == "Câmara + Senado").sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Projetos de Lei monitorados", total)
    c2.metric("Câmara", camara)
    c3.metric("Senado", senado)
    c4.metric("Câmara + Senado", bicameral)


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
# LEITURA DO ARQUIVO
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

st.divider()
render_metrics(df_filtrado)





# ============================================================
# SELEÇÃO DE REGISTRO
# ============================================================

st.subheader("Detalhamento do PL")

df_selecao = df_filtrado.copy().reset_index(drop=False).rename(columns={"index": "_row_id"})
df_selecao["_label"] = df_selecao.apply(build_selector_label, axis=1)

selected_label = st.selectbox(
    "Selecione um proposta para detalhar",
    options=df_selecao["_label"].tolist(),
)

registro = df_selecao.loc[df_selecao["_label"] == selected_label].iloc[0]


# ============================================================
# ABAS DE DETALHE
# ============================================================

tab_resumo, tab_camara, tab_senado, tab_interno = st.tabs(
    ["Resumo", "Câmara", "Senado", "CGNOR - Controle Interno"]
)

with tab_resumo:
    st.markdown("### Dados gerais")
    render_kv(
        registro,
        COLUNAS_RESUMO_DETALHE,
        title_map=DISPLAY_LABELS,
    )

    st.markdown("### Ementas")
    if "camara_ementa" in registro.index and pd.notna(registro["camara_ementa"]) and str(registro["camara_ementa"]).strip():
        st.markdown(f"**Ementa Câmara:** {registro['camara_ementa']}")

    if "senado_ementa" in registro.index and pd.notna(registro["senado_ementa"]) and str(registro["senado_ementa"]).strip():
        st.markdown(f"**Ementa Senado:** {registro['senado_ementa']}")

    st.markdown("### Situação atual")
    render_kv(
        registro,
        [
            "camara_data_ultima_tramitacao",
            "camara_orgao_ultima_tramitacao",
            "camara_situacao_ultima_tramitacao",
            "senado_data_ultima_tramitacao",
            "senado_orgao_ultima_tramitacao",
            "senado_situacao_ultima_tramitacao",
        ],
        title_map=DISPLAY_LABELS
    )

with tab_camara:
    st.markdown("### Dados da Câmara dos Deputados")
    render_kv(registro, COLUNAS_CAMARA, title_map=DISPLAY_LABELS)

with tab_senado:
    st.markdown("### Dados do Senado Federal")
    render_kv(registro, COLUNAS_SENADO, title_map=DISPLAY_LABELS)

with tab_interno:
    st.markdown("### Dados do Controle Interno CGNOR")
    render_kv(registro, COLUNAS_CONTROLE_INTERNO)



# ============================================================
# TABELA RESUMIDA
# ============================================================


st.divider()
st.subheader("Base das proposições Monitoradas")
st.caption("Abaixo a tabela com todos os campos disponíveis (Dados CGNOR + API Camara + API Senado). Ao parar o mouse sobre a tabela, o icone com olho será apresentado. E é possível selecionar as colunas a serem visualizadas")

if df_filtrado.empty:
    st.warning("Nenhum registro encontrado com os filtros aplicados.")
    st.stop()

df_resumo = build_summary_table(df_filtrado)

column_config_resumo = make_link_column_config(df_resumo)



st.dataframe(
    df_resumo,
    use_container_width=True,
    hide_index=True,
    column_config=column_config_resumo,
)

st.markdown(
    """
    <style>
    .download-button-container {
        position: fixed;
        bottom: 30px;
        right: 40px;
        z-index: 1000;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="download-button-container">', unsafe_allow_html=True)

st.download_button(
    label="⬇️ Download em csv",
    data=df_filtrado.to_csv(index=False).encode("utf-8-sig"),
    file_name="planilha_completa_pl.csv",
    mime="text/csv",
)

st.markdown("</div>", unsafe_allow_html=True)


# Rodapé
st.markdown("""
<hr style="height:1px;border:none;color:#ccc;background-color:#ccc;" />
<p style="text-align: center; font-size: 0.9em;">
Desenvolvido pelo <b>Núcleo de Inteligência de Dados</b> - <b>CDATA/CGINF/SEGES/MGI</b>.
</p>
""", unsafe_allow_html=True)
