"""
Orquestrador bicameral — enriquece dados com informacoes da Camara e do Senado.

Coordena as chamadas aos clientes de ambas as casas legislativas
e classifica a origem dos dados (Camara, Senado, ambas ou nao encontrado).
"""

import logging
import time
from typing import Any, Dict

import pandas as pd

from src.clientes.camara import ClienteCamara
from src.clientes.senado import ClienteSenado

logger = logging.getLogger(__name__)


class EnriquecedorBicameral:
    """
    Enriquece um DataFrame de proposicoes com dados da Camara e do Senado.

    Args:
        cliente_camara: Instancia do cliente da Camara dos Deputados.
        cliente_senado: Instancia do cliente do Senado Federal.
        intervalo_entre_requisicoes: Segundos de pausa entre chamadas para
            suavizar a carga nas APIs.
    """

    def __init__(
        self,
        cliente_camara: ClienteCamara,
        cliente_senado: ClienteSenado,
        intervalo_entre_requisicoes: float = 0.05,
    ):
        self.camara = cliente_camara
        self.senado = cliente_senado
        self.intervalo = intervalo_entre_requisicoes

    def enriquecer_referencia(
        self, sigla: Any, numero: Any, ano: Any
    ) -> Dict[str, Any]:
        """
        Busca dados de uma unica proposicao em ambas as casas.

        Returns:
            Dicionario com campos de ambas as casas e a coluna 'Origem Dados'
            indicando onde a proposicao foi encontrada.
        """
        dados_camara = self.camara.buscar(sigla, numero, ano)
        time.sleep(self.intervalo)
        dados_senado = self.senado.buscar(sigla, numero, ano)

        if dados_camara and dados_senado:
            origem = "Câmara + Senado"
        elif dados_camara:
            origem = "Câmara"
        elif dados_senado:
            origem = "Senado"
        else:
            origem = "Não encontrado"

        resultado = {
            "sigla": sigla,
            "numero": numero,
            "ano": ano,
            "Origem Dados": origem,
        }
        resultado.update(dados_camara)
        resultado.update(dados_senado)
        return resultado

    def enriquecer_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enriquece um DataFrame inteiro, processando cada combinacao unica
        de sigla/numero/ano.

        Args:
            df: DataFrame com colunas 'sigla', 'numero' e 'ano'.

        Returns:
            DataFrame com os dados enriquecidos de ambas as casas legislativas.

        Raises:
            KeyError: Se as colunas obrigatorias nao existirem no DataFrame.
        """
        colunas_necessarias = ["sigla", "numero", "ano"]
        colunas_faltantes = [c for c in colunas_necessarias if c not in df.columns]
        if colunas_faltantes:
            raise KeyError(
                f"Colunas obrigatorias ausentes no DataFrame: {colunas_faltantes}"
            )

        referencias = (
            df[colunas_necessarias]
            .dropna(subset=colunas_necessarias)
            .drop_duplicates()
            .copy()
        )

        total = len(referencias)
        logger.info("Enriquecendo %d referencias unicas...", total)

        resultados = []
        for indice, linha in enumerate(referencias.itertuples(), start=1):
            if indice % 10 == 0 or indice == total:
                logger.info("Progresso: %d/%d", indice, total)
            resultados.append(
                self.enriquecer_referencia(linha.sigla, linha.numero, linha.ano)
            )

        logger.info("Enriquecimento concluido: %d referencias processadas.", total)
        return pd.DataFrame(resultados)
