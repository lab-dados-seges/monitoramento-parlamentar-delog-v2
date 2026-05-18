"""
Analisador de referencias legislativas.

Extrai e normaliza referencias como 'PL n 4603/2023' para o padrao 'PL 4603/2023',
a partir de textos livres da planilha CGNOR.
"""

import re
from typing import Any, Dict

import pandas as pd


class AnalisadorReferenciaLegislativa:
    """
    Extrai e normaliza referencias legislativas para o padrao:
    SIGLA NUMERO/ANO

    Exemplos:
        - 'PL n. 4603/2023'                    -> 'PL 4603/2023'
        - 'Projeto de Lei n. 3.117, de 2024'   -> 'PL 3117/2024'
        - 'PDL n. 4/2024'                      -> 'PDL 4/2024'
        - 'Medida Provisoria n. 1.221/2024'    -> 'MPV 1221/2024'
    """

    # Mapa de padroes textuais para siglas normalizadas.
    # A ordem importa: padroes mais especificos vem primeiro para evitar
    # que "Projeto de Lei" capture antes de "Projeto de Lei Complementar".
    MAPA_SIGLAS = [
        (r"\bPROJETO DE LEI COMPLEMENTAR\b", "PLC"),
        (r"\bPROJETO DE DECRETO LEGISLATIVO\b", "PDL"),
        (r"\bPROJETO DE LEI\b", "PL"),
        (r"\bPLEI\b", "PL"),
        (r"\bMEDIDA PROVISORIA\b", "MPV"),
        (r"\bMEDIDA PROVISÓRIA\b", "MPV"),
        (r"\bPLN\b", "PLN"),
        (r"\bPLC\b", "PLC"),
        (r"\bPDL\b", "PDL"),
        (r"\bPL\b", "PL"),
        (r"\bMPV\b", "MPV"),
        (r"\bMP\b", "MPV"),
    ]

    # Regex para extrair numero e ano de formatos variados:
    #   '4603/2023', '3.117, de 2024', '1221 de 2024'
    _REGEX_NUMERO_ANO = re.compile(
        r"(\d{1,3}(?:\.\d{3})*|\d+)\s*(?:/|,\s*DE\s+|,\s*| DE\s+)(\d{4})"
    )

    @classmethod
    def extrair_referencia(cls, texto: Any) -> Dict[str, Any]:
        """
        Analisa um texto livre e extrai sigla, numero, ano e forma normalizada.

        Args:
            texto: Texto contendo a referencia legislativa (ex: 'PL n. 4603/2023').

        Returns:
            Dicionario com chaves: sigla, numero, ano, proposicao_normalizada.
            Valores ausentes sao representados como pd.NA.
        """
        resultado_vazio = {
            "sigla": pd.NA,
            "numero": pd.NA,
            "ano": pd.NA,
            "proposicao_normalizada": pd.NA,
        }

        if pd.isna(texto):
            return resultado_vazio

        texto_limpo = str(texto).strip().upper()

        # Remove marcadores textuais que atrapalham o parsing
        for caractere in ("Nº", "N°", "NO", "º", "°"):
            texto_limpo = texto_limpo.replace(caractere, " ")
        texto_limpo = re.sub(r"\s+", " ", texto_limpo).strip()

        # Identifica a sigla
        sigla_encontrada = pd.NA
        for padrao, sigla in cls.MAPA_SIGLAS:
            if re.search(padrao, texto_limpo):
                sigla_encontrada = sigla
                break

        # Extrai numero e ano
        match = cls._REGEX_NUMERO_ANO.search(texto_limpo)
        if not match:
            return {**resultado_vazio, "sigla": sigla_encontrada}

        numero_bruto = match.group(1)
        ano = int(match.group(2))
        numero = int(numero_bruto.replace(".", ""))

        if pd.isna(sigla_encontrada):
            return {
                "sigla": pd.NA,
                "numero": numero,
                "ano": ano,
                "proposicao_normalizada": pd.NA,
            }

        return {
            "sigla": sigla_encontrada,
            "numero": numero,
            "ano": ano,
            "proposicao_normalizada": f"{sigla_encontrada} {numero}/{ano}",
        }
