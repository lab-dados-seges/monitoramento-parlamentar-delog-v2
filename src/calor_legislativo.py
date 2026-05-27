"""
Calculo do Calor Legislativo (Cl) — score de prioridade para proposicoes.

Formula:
                A * (1 + Ne/100) * S * R
    Cl = -----------------------------------
              ln(T_base + e)

Onde:
    A       : Atividade — numero de eventos de tramitacao nos ultimos 30 dias
              (se A == 0, usa-se 0.5).
    Ne      : Numero de emendas registradas na proposicao.
    S       : Multiplicador de substitutivo (1.5 se o ultimo parecer mencionar
              "substitutivo" ou "texto com alteracoes"; 1.0 caso contrario).
    R       : Multiplicador de rito (2.0 urgencia, 1.5 prioridade, 1.0 outros).
    T_base  : Dias decorridos desde a ultima mudanca de descricaoSituacao.

A classificacao final usa tres faixas:
    < 0.8        : Baixo Impacto
    0.8 a 2.0    : Alerta Amarelo
    > 2.0        : Alto Impacto
"""

import logging
import math
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTES DE CLASSIFICACAO
# ============================================================

NIVEL_BAIXO_IMPACTO = "Baixo Impacto"
NIVEL_ALERTA_AMARELO = "Alerta Amarelo"
NIVEL_ALTO_IMPACTO = "Alto Impacto"
NIVEL_INDEFINIDO = "Indefinido"

LIMITE_ALERTA = 0.8
LIMITE_ALTO = 2.0

NIVEIS_ORDENADOS = [
    NIVEL_BAIXO_IMPACTO,
    NIVEL_ALERTA_AMARELO,
    NIVEL_ALTO_IMPACTO,
    NIVEL_INDEFINIDO,
]

# Cores hexadecimais para badges no Streamlit (cor "forte" do texto/icone)
CORES_NIVEL: Dict[str, str] = {
    NIVEL_BAIXO_IMPACTO: "#16A34A",   # verde
    NIVEL_ALERTA_AMARELO: "#F59E0B",  # amarelo/laranja
    NIVEL_ALTO_IMPACTO: "#DC2626",    # vermelho
    NIVEL_INDEFINIDO: "#9CA3AF",      # cinza
}

# Fundos pastel correspondentes (estilo "chip" suave)
CORES_NIVEL_FUNDO: Dict[str, str] = {
    NIVEL_BAIXO_IMPACTO: "#ECFDF5",   # verde claro
    NIVEL_ALERTA_AMARELO: "#FEF3C7",  # amarelo claro
    NIVEL_ALTO_IMPACTO: "#FEE2E2",    # vermelho claro
    NIVEL_INDEFINIDO: "#F3F4F6",      # cinza claro
}

# Icones (emoji) para uso em rotulos textuais
ICONES_NIVEL: Dict[str, str] = {
    NIVEL_BAIXO_IMPACTO: "🟢",
    NIVEL_ALERTA_AMARELO: "🟡",
    NIVEL_ALTO_IMPACTO: "🔴",
    NIVEL_INDEFINIDO: "⚪",
}


# ============================================================
# ESTRUTURA DE RESULTADO
# ============================================================


@dataclass
class ResultadoCalor:
    """Componentes do calculo de calor legislativo para uma proposicao."""

    A: float
    Ne: int
    S: float
    R: float
    T_base: int
    score_cl: Optional[float]
    nivel_calor: str

    def como_dict_camara(self) -> Dict[str, Any]:
        """Converte para dicionario com prefixo 'camara_calor_*'."""
        d = asdict(self)
        return {f"camara_calor_{chave}": valor for chave, valor in d.items()}


# ============================================================
# CALCULOS AUXILIARES
# ============================================================


def calcular_multiplicador_rito(regime: Optional[str]) -> float:
    """
    Mapeia o regime de tramitacao para o multiplicador R.

    - Contem "urgencia" (case-insensitive)  -> 2.0
    - Contem "prioridade" (case-insensitive) -> 1.5
    - Qualquer outro caso                    -> 1.0
    """
    if not regime:
        return 1.0

    texto = str(regime).strip().lower()
    if not texto:
        return 1.0

    # Tolerancia para variacoes com/sem acento
    if "urgencia" in texto or "urgência" in texto:
        return 2.0
    if "prioridade" in texto:
        return 1.5
    return 1.0


def classificar_nivel(score: Optional[float]) -> str:
    """Classifica o score de calor em uma faixa nominal."""
    if score is None or (isinstance(score, float) and math.isnan(score)):
        return NIVEL_INDEFINIDO
    if score < LIMITE_ALERTA:
        return NIVEL_BAIXO_IMPACTO
    if score <= LIMITE_ALTO:
        return NIVEL_ALERTA_AMARELO
    return NIVEL_ALTO_IMPACTO


def calcular_score(
    a: float,
    ne: int,
    s: float,
    r: float,
    t_base: int,
) -> Optional[float]:
    """
    Aplica a formula Cl = A * (1 + Ne/100) * S * R / ln(T_base + e).

    Returns:
        Score como float arredondado em 4 casas, ou None em caso de erro.
    """
    try:
        denominador = math.log(max(t_base, 0) + math.e)
        if denominador <= 0:
            return None
        numerador = a * (1.0 + (ne / 100.0)) * s * r
        return round(numerador / denominador, 4)
    except (ValueError, ZeroDivisionError, TypeError) as erro:
        logger.warning("Falha ao calcular score Cl: %s", erro)
        return None


# ============================================================
# FUNCAO PRINCIPAL
# ============================================================


def calcular_calor(
    atividade: Optional[int],
    emendas: Optional[int],
    s_substitutivo: Optional[float],
    regime: Optional[str],
    t_base: Optional[int],
) -> ResultadoCalor:
    """
    Calcula o resultado completo de Calor Legislativo a partir dos componentes.

    Aplica os valores defaults previstos na especificacao quando algum
    componente vier ausente:
      - A = 0.5  quando atividade for 0, None ou negativa
      - Ne = 0   quando ausente
      - S = 1.0  quando ausente
      - R = 1.0  quando regime ausente
      - T_base = 0 quando ausente (tratado como recente)

    Args:
        atividade: Numero de eventos nos ultimos 30 dias.
        emendas: Numero de emendas registradas.
        s_substitutivo: Multiplicador S (1.0 ou 1.5) ja resolvido pelo cliente.
        regime: String do regime de tramitacao (usada para calcular R).
        t_base: Dias desde a ultima mudanca de descricaoSituacao.

    Returns:
        Instancia de ResultadoCalor com todos os componentes e nivel.
    """
    a_norm = float(atividade) if (atividade is not None and atividade > 0) else 0.5
    ne_norm = int(emendas) if (emendas is not None and emendas >= 0) else 0
    s_norm = float(s_substitutivo) if s_substitutivo else 1.0
    r_norm = calcular_multiplicador_rito(regime)
    t_norm = int(t_base) if (t_base is not None and t_base >= 0) else 0

    score = calcular_score(a_norm, ne_norm, s_norm, r_norm, t_norm)
    nivel = classificar_nivel(score)

    return ResultadoCalor(
        A=a_norm,
        Ne=ne_norm,
        S=s_norm,
        R=r_norm,
        T_base=t_norm,
        score_cl=score,
        nivel_calor=nivel,
    )
