"""
Componente de ultimas atualizacoes — lista as proposicoes com tramitacoes mais recentes.
"""

import pandas as pd
import streamlit as st


def _aplicar_filtro_pl(pl: str):
    """Popula o filtro de busca por PL na sidebar; Streamlit re-renderiza em seguida."""
    st.session_state["filtro_busca_projeto"] = pl


def renderizar_ultimas_atualizacoes(df: pd.DataFrame):
    """
    Exibe um expander com as 10 proposicoes que tiveram tramitacao mais recente.

    Usa as colunas de data de ultima tramitacao ja formatadas (dd/mm/aaaa)
    e as converte temporariamente para ordenacao.
    """
    if df.empty:
        return

    colunas_data_tramitacao = [
        "camara_data_ultima_tramitacao",
        "senado_data_ultima_tramitacao",
    ]
    colunas_disponiveis = [c for c in colunas_data_tramitacao if c in df.columns]
    if not colunas_disponiveis:
        return

    df_temp = df.copy()
    for coluna in colunas_disponiveis:
        df_temp[f"_dt_{coluna}"] = pd.to_datetime(
            df_temp[coluna], format="%d/%m/%Y", errors="coerce"
        )

    colunas_dt = [f"_dt_{c}" for c in colunas_disponiveis]
    df_temp["_data_mais_recente"] = df_temp[colunas_dt].max(axis=1)

    df_recentes = (
        df_temp.dropna(subset=["_data_mais_recente"])
        .sort_values("_data_mais_recente", ascending=False)
        .head(10)
    )

    if df_recentes.empty:
        return

    with st.expander("🔔Últimas Atualizacoes", expanded=False):
        # CSS escopado: aperta espacamento vertical entre as linhas do expander
        # e tira padding/altura minima dos botoes tertiary pra ficarem inline.
        st.markdown(
            """
            <style>
            div[data-testid="stExpander"] div[data-testid="stHorizontalBlock"] {
                margin-bottom: -0.5rem;
            }
            div[data-testid="stExpander"] .stButton > button {
                padding: 0 0.25rem;
                min-height: 0;
                line-height: 1.6;
                text-align: left !important;
                justify-content: flex-start !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Proposicoes com tramitacoes mais recentes — clique no PL para filtrar:")
        for idx, linha in df_recentes.iterrows():
            pl_raw = linha.get("Projeto de Lei - Regex")
            pl = str(pl_raw).strip() if pd.notna(pl_raw) else ""
            origem = linha.get("Origem Dados", "")

            partes = []
            if pd.notna(linha.get(f"_dt_{colunas_disponiveis[0]}", None)):
                data_fmt = linha[colunas_disponiveis[0]]
                partes.append(f"Câmara: **{data_fmt}**")
            if len(colunas_disponiveis) > 1 and pd.notna(
                linha.get(f"_dt_{colunas_disponiveis[1]}", None)
            ):
                data_fmt = linha[colunas_disponiveis[1]]
                partes.append(f"Senado: **{data_fmt}**")

            texto_data = " · ".join(partes) if partes else "_sem data_"

            col_pl, col_info = st.columns([2, 5], vertical_alignment="center")
            with col_pl:
                if pl:
                    st.button(
                        pl,
                        key=f"atualiz_pl_{idx}",
                        on_click=_aplicar_filtro_pl,
                        args=(pl,),
                        type="tertiary",
                    )
                else:
                    st.markdown("**N/A**")
            with col_info:
                st.markdown(f"({origem}) — {texto_data}")
