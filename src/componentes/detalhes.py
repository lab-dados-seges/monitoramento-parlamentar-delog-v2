"""
Componentes de detalhamento — renderiza campos chave-valor e abas de detalhe.
"""

from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

from src.configuracao import (
    COLUNAS_CONTROLE_INTERNO,
    COLUNAS_LINK,
    ROTULOS_CAMARA,
    ROTULOS_EXIBICAO,
    ROTULOS_SENADO,
)


# ============================================================
# RENDERIZACAO DE CAMPOS CHAVE-VALOR
# ============================================================


def _renderizar_campo(rotulo: str, valor, coluna: str):
    """Renderiza um unico campo chave-valor com formatacao consistente."""
    if coluna in COLUNAS_LINK and isinstance(valor, str) and valor.startswith("http"):
        st.markdown(f"**{rotulo}:** [Abrir link]({valor})")
    elif valor == "Não identificado":
        st.markdown(
            f'**{rotulo}:** <span style="'
            'display:inline-block;padding:2px 8px;border-radius:6px;'
            'background-color:#F3F4F6;color:#9CA3AF;font-size:0.9em;font-style:italic;">'
            'Não identificado</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"**{rotulo}:** {valor}")


def _renderizar_lista_campos(
    registro: pd.Series,
    colunas: List[str],
    mapa_rotulos: Optional[Dict[str, str]] = None,
):
    """
    Renderiza uma lista de campos chave-valor a partir de um registro.

    Exibe 'Nenhum dado disponivel' se nenhuma coluna tiver valor preenchido.
    """
    colunas_ok = [c for c in colunas if c in registro.index]
    if not colunas_ok:
        st.info("Nenhum dado disponível nesta seção.")
        return

    tem_dados = any(
        pd.notna(registro[col]) and str(registro[col]).strip()
        for col in colunas_ok
    )
    if not tem_dados:
        st.info("Nenhum dado disponível nesta seção.")
        return

    for coluna in colunas_ok:
        rotulo = mapa_rotulos.get(coluna, coluna) if mapa_rotulos else coluna
        valor = registro[coluna]
        if pd.isna(valor) or str(valor).strip() == "":
            valor = "Não identificado"
        _renderizar_campo(rotulo, valor, coluna)


def _renderizar_duas_colunas(
    registro: pd.Series,
    colunas_esquerda: List[str],
    colunas_direita: List[str],
    rotulos_esquerda: Optional[Dict[str, str]] = None,
    rotulos_direita: Optional[Dict[str, str]] = None,
    titulo_esquerda: str = ":blue[**Câmara dos Deputados**]",
    titulo_direita: str = ":green[**Senado Federal**]",
):
    """Renderiza dados em duas colunas lado a lado (ex: Camara e Senado)."""
    colunas_esq_ok = [c for c in colunas_esquerda if c in registro.index]
    colunas_dir_ok = [c for c in colunas_direita if c in registro.index]

    if not colunas_esq_ok and not colunas_dir_ok:
        st.info("Nenhum dado disponível nesta seção.")
        return

    col_esq, col_dir = st.columns(2)

    for container, colunas_ok, mapa, titulo in [
        (col_esq, colunas_esq_ok, rotulos_esquerda, titulo_esquerda),
        (col_dir, colunas_dir_ok, rotulos_direita, titulo_direita),
    ]:
        with container:
            if not colunas_ok:
                continue
            st.markdown(titulo)
            _renderizar_lista_campos(registro, colunas_ok, mapa)


# ============================================================
# ABAS DE DETALHE
# ============================================================


def renderizar_aba_resumo(registro: pd.Series):
    """Aba Resumo — ementas, dados gerais e situacao atual."""
    st.markdown("#### Ementas")
    for coluna, casa in [("camara_ementa", "Câmara"), ("senado_ementa", "Senado")]:
        if coluna in registro.index and pd.notna(registro[coluna]) and str(registro[coluna]).strip():
            st.markdown(f"**{casa}:** {registro[coluna]}")

    st.markdown("#### Dados Gerais")
    _renderizar_duas_colunas(
        registro,
        colunas_esquerda=["camara_data_proposta_pl", "camara_propositor_pl"],
        colunas_direita=["senado_data_proposta_pl", "senado_propositor_pl"],
        rotulos_esquerda=ROTULOS_CAMARA,
        rotulos_direita=ROTULOS_SENADO,
    )

    st.markdown("#### Situação Atual")
    _renderizar_duas_colunas(
        registro,
        colunas_esquerda=[
            "camara_regime",
            "camara_data_ultima_tramitacao",
            "camara_orgao_ultima_tramitacao",
            "camara_descricao_tramitacao",
            "camara_situacao_ultima_tramitacao",
            "camara_despacho_ultima_tramitacao",
        ],
        colunas_direita=[
            "senado_data_ultima_tramitacao",
            "senado_orgao_ultima_tramitacao",
            "senado_situacao_ultima_tramitacao",
        ],
        rotulos_esquerda=ROTULOS_CAMARA,
        rotulos_direita=ROTULOS_SENADO,
    )


def _renderizar_aba_casa(
    registro: pd.Series,
    colunas_identificacao: List[str],
    colunas_tramitacao: List[str],
    mapa_rotulos: Dict[str, str],
    cor: str,
):
    """Renderiza uma aba de casa legislativa (Camara ou Senado) em duas colunas."""
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f":{cor}[**Identificação e Autoria**]")
        _renderizar_lista_campos(registro, colunas_identificacao, mapa_rotulos)
    with col2:
        st.markdown(f":{cor}[**Tramitação e Parecer**]")
        _renderizar_lista_campos(registro, colunas_tramitacao, mapa_rotulos)


def renderizar_aba_camara(registro: pd.Series):
    """Aba Camara — identificacao, autoria, tramitacao e parecer."""
    _renderizar_aba_casa(
        registro,
        colunas_identificacao=[
            "camara_id_proposicao", "camara_projeto", "camara_ementa",
            "camara_data_proposta_pl", "camara_propositor_pl",
            "camara_partido", "camara_estado",
        ],
        colunas_tramitacao=[
            "camara_regime","camara_data_ultima_tramitacao", "camara_orgao_ultima_tramitacao",
            "camara_descricao_tramitacao", "camara_situacao_ultima_tramitacao",
            "camara_despacho_ultima_tramitacao", "camara_data_parecer_aprovado",
            "camara_orgao_parecer", "camara_despacho_parecer",
            "camara_link_inteiro_teor_parecer", "camara_link_inteiro_teor_pl",
            "camara_link_ficha_tramitacao", "camara_emendas", "camara_substitutivos",
        ],
        mapa_rotulos=ROTULOS_CAMARA,
        cor="blue",
    )


def renderizar_aba_senado(registro: pd.Series):
    """Aba Senado — identificacao, autoria, tramitacao e parecer."""
    _renderizar_aba_casa(
        registro,
        colunas_identificacao=[
            "senado_id_processo", "senado_codigo_materia", "senado_projeto",
            "senado_ementa", "senado_data_proposta_pl", "senado_propositor_pl",
            "senado_partido", "senado_estado",
        ],
        colunas_tramitacao=[
            "senado_data_ultima_tramitacao", "senado_orgao_ultima_tramitacao",
            "senado_situacao_ultima_tramitacao", "senado_data_parecer_aprovado",
            "senado_orgao_parecer", "senado_link_inteiro_teor_parecer",
            "senado_link_inteiro_teor_pl", "senado_link_ficha_tramitacao",
            "senado_emendas", "senado_substitutivos",
        ],
        mapa_rotulos=ROTULOS_SENADO,
        cor="green",
    )


def renderizar_aba_controle_interno(registro: pd.Series):
    """Aba Controle Interno — dados do SEI e encaminhamentos."""
    campos_sei = [
        "Integração SEI - Processo",
        "Integração SEI - Anotação do Bloco Interno",
    ]
    outros = [
        c for c in COLUNAS_CONTROLE_INTERNO if c not in ["Nº", "Processo"] + campos_sei
    ]
    metade = len(outros) // 2

    col1, col2 = st.columns(2)
    with col1:
        _renderizar_lista_campos(registro, ["Nº", "Processo"], ROTULOS_EXIBICAO)

        # Campos SEI com badge "Em desenvolvimento"
        for campo in campos_sei:
            if campo in registro.index and pd.notna(registro[campo]) and str(registro[campo]).strip():
                st.markdown(f"**{campo}:** {registro[campo]}")
            else:
                st.markdown(
                    f'**{campo}:** <span style="display:inline-block;padding:2px 8px;'
                    f'border-radius:6px;background-color:#EFF6FF;color:#3B82F6;'
                    f'font-size:0.85em;font-weight:500;">Em desenvolvimento</span>',
                    unsafe_allow_html=True,
                )

        _renderizar_lista_campos(registro, outros[:metade], ROTULOS_EXIBICAO)
    with col2:
        _renderizar_lista_campos(registro, outros[metade:], ROTULOS_EXIBICAO)
