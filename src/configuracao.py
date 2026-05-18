"""
Configuracoes centrais do projeto de Monitoramento Parlamentar.

Fonte unica de verdade para colunas, labels, URLs e parametros
usados tanto pelo pipeline de ETL quanto pelo app Streamlit.
"""

import os

# ============================================================
# CAMINHOS E ARQUIVOS
# ============================================================

CAMINHO_DADOS = os.environ.get("CAMINHO_DADOS", "data")
ARQUIVO_PLANILHA = "Levantamento de prazos para análise de PLs.xlsx"
ARQUIVO_CSV_FINAL = "df_final_bicameral.csv"

# ============================================================
# URLs DAS APIS
# ============================================================

URL_API_CAMARA = os.environ.get(
    "URL_API_CAMARA",
    "https://dadosabertos.camara.leg.br/api/v2",
)
URL_API_SENADO = os.environ.get(
    "URL_API_SENADO",
    "https://legis.senado.leg.br/dadosabertos",
)

# ============================================================
# SHAREPOINT (origem da planilha CGNOR)
# ============================================================

SHAREPOINT_HOST = "colaboragov.sharepoint.com"
SHAREPOINT_SITE = "CGNOR-SEGES"
SHAREPOINT_PASTA_PLANILHA = "Robô Projetos de Lei"

# ============================================================
# CACHE DO STREAMLIT
# ============================================================

CACHE_TTL_SEGUNDOS = int(os.environ.get("CACHE_TTL_SEGUNDOS", 60 * 15))

# ============================================================
# COLUNAS — IDENTIFICACAO
# ============================================================

COLUNA_CHAVE_EXIBICAO = "Projeto de LEI"
COLUNA_REGEX = "Projeto de Lei - Regex"
COLUNA_ORIGEM = "Origem Dados"

# ============================================================
# MAPA DE CAMPOS — sufixo → rotulo amigavel (define uma vez)
# ============================================================

_CAMPOS_API = {
    "id_proposicao": "ID da Proposição",
    "id_processo": "ID do Processo",
    "codigo_materia": "Código da Matéria",
    "projeto": "Projeto",
    "ementa": "Ementa",
    "data_proposta_pl": "Data da Proposta",
    "propositor_pl": "Propositor",
    "partido": "Partido",
    "estado": "Estado",
    "data_ultima_tramitacao": "Data da Última Tramitação",
    "orgao_ultima_tramitacao": "Órgão da Última Tramitação",
    "descricao_tramitacao": "Descrição da Última Tramitação",
    "situacao_ultima_tramitacao": "Situação da Última Tramitação",
    "despacho_ultima_tramitacao": "Despacho da Última Tramitação",
    "data_parecer_aprovado": "Data do Parecer Aprovado",
    "orgao_parecer": "Órgão do Parecer",
    "despacho_parecer": "Despacho do Parecer",
    "link_inteiro_teor_parecer": "Link do Inteiro Teor do Parecer",
    "link_inteiro_teor_pl": "Link do Inteiro Teor do PL",
    "link_ficha_tramitacao": "Link da Ficha de Tramitação",
    "emendas": "Emendas",
    "substitutivos": "Substitutivos",
}

# Sufixos que sao links clicaveis
_SUFIXOS_LINK = {
    "link_inteiro_teor_parecer", "link_inteiro_teor_pl", "link_ficha_tramitacao",
    "emendas", "substitutivos",
}

# ============================================================
# COLUNAS — AGRUPAMENTOS POR SECAO DA UI
# ============================================================

_SUFIXOS_CAMARA = [
    "id_proposicao", "projeto", "ementa", "data_proposta_pl", "propositor_pl",
    "partido", "estado", "data_ultima_tramitacao", "orgao_ultima_tramitacao",
    "descricao_tramitacao", "situacao_ultima_tramitacao", "despacho_ultima_tramitacao",
    "data_parecer_aprovado", "orgao_parecer", "despacho_parecer",
    "link_inteiro_teor_parecer", "link_inteiro_teor_pl", "link_ficha_tramitacao",
    "emendas", "substitutivos",
]
_SUFIXOS_SENADO = [
    "id_processo", "codigo_materia", "projeto", "ementa", "data_proposta_pl",
    "propositor_pl", "partido", "estado", "data_ultima_tramitacao",
    "orgao_ultima_tramitacao", "situacao_ultima_tramitacao", "data_parecer_aprovado",
    "orgao_parecer", "link_inteiro_teor_parecer", "link_inteiro_teor_pl",
    "link_ficha_tramitacao", "emendas", "substitutivos",
]

COLUNAS_CAMARA = [f"camara_{s}" for s in _SUFIXOS_CAMARA]
COLUNAS_SENADO = [f"senado_{s}" for s in _SUFIXOS_SENADO]

# ---- Derivados automaticamente ----
COLUNAS_LINK = [f"{p}_{s}" for p in ("camara", "senado") for s in _SUFIXOS_LINK]

COLUNAS_DATA = [
    f"{p}_{s}"
    for p in ("camara", "senado")
    for s in ("data_ultima_tramitacao", "data_parecer_aprovado", "data_proposta_pl")
] + [
    "1º Encaminhamento - Data", "2º Encaminhamento - Data", "3º Encaminhamento - Data",
    "Envio para a Delog - Data", "Envio ao Gabinete da Seges - Data", "Assinaturas - Data",
]

COLUNAS_DATA_PIPELINE = COLUNAS_DATA + [
    "1º Encaminhamento - Prazo p/ Resposta",
    "2º Encaminhamento - Prazo p/ Resposta",
    "3º Encaminhamento - Prazo p/ Resposta",
]

COLUNAS_NUMERICAS_INTEIRAS = [
    "numero", "ano", "Validação pelo gabinete da Seges - Quantidade de dias úteis",
    "camara_id_proposicao", "senado_id_processo", "senado_codigo_materia",
]

# Colunas reservadas para integracao SEI futura - injetadas vazias pelo pipeline
# enquanto a planilha de origem nao as fornecer.
COLUNAS_PLACEHOLDER_SEI = [
    "Integração SEI - Processo",
    "Integração SEI - Anotação do Bloco Interno",
]

COLUNAS_CONTROLE_INTERNO = [
    "Nº", "Processo",
    "Integração SEI - Processo", "Integração SEI - Anotação do Bloco Interno",
    "Descrição", "Encaminhamento prévio - Teams/E-mail",
    "1º Encaminhamento - Remetente", "1º Encaminhamento - Despacho /Ofício",
    "1º Encaminhamento - Data", "1º Encaminhamento - Prazo p/ Resposta",
    "2º Encaminhamento - Remetente", "2º Encaminhamento - Despacho",
    "2º Encaminhamento - Data", "2º Encaminhamento - Prazo p/ Resposta",
    "3º Encaminhamento - Remetente", "3º Encaminhamento - Despacho",
    "3º Encaminhamento - Data", "3º Encaminhamento - Prazo p/ Resposta",
    "Período de elaboração da Análise - Quantidade de dias úteis",
    "Envio para a Delog - Data", "Envio ao Gabinete da Seges - Data",
    "Validação pelo gabinete da Seges - Quantidade de dias úteis",
    "Assinaturas - Data", "Manifestação da Seges - Nota técnica",
    "Andamento do PL - Data/Detalhamento", "Observações andamento - Parecer",
]

# ============================================================
# COLUNAS — TABELA DE RESULTADOS (visao geral com todas)
# ============================================================

COLUNAS_RESULTADOS = [
    "Origem Dados", "Projeto de LEI", "Projeto de Lei - Regex",
    *[c for c in COLUNAS_CAMARA if c != "camara_id_proposicao"],
    *[c for c in COLUNAS_SENADO if c not in ("senado_id_processo", "senado_codigo_materia")],
    *COLUNAS_CONTROLE_INTERNO,
]

# ============================================================
# COLUNAS — ORDENACAO DO PIPELINE (CSV final)
# ============================================================

COLUNAS_ORDENACAO_PIPELINE = [
    "Projeto de LEI", "Projeto de Lei - Regex",
    "sigla", "numero", "ano", "Origem Dados",
    *COLUNAS_CAMARA,
    *[c for c in COLUNAS_SENADO if c not in COLUNAS_CAMARA],
]

# ============================================================
# LABELS — GERADOS AUTOMATICAMENTE DO MAPA DE CAMPOS
# ============================================================

ROTULOS_EXIBICAO: dict[str, str] = {"Projeto de Lei - Regex": "Identificação"}
for _sufixo, _rotulo in _CAMPOS_API.items():
    ROTULOS_EXIBICAO[f"camara_{_sufixo}"] = f"(Câmara) {_rotulo}"
    ROTULOS_EXIBICAO[f"senado_{_sufixo}"] = f"(Senado) {_rotulo}"

ROTULOS_CAMARA = {k: v.replace("(Câmara)", "").strip() for k, v in ROTULOS_EXIBICAO.items()}
ROTULOS_SENADO = {k: v.replace("(Senado)", "").strip() for k, v in ROTULOS_EXIBICAO.items()}
