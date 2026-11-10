"""Monta os serviços usados pelas páginas.

O pool de conexões é criado uma única vez por processo (``st.cache_resource``)
e compartilhado por todas as sessões. Os dados NÃO são guardados em cache:
como a demonstração é compartilhada, cada página lê o estado atual do banco,
e o que um visitante grava aparece para os demais na próxima interação.
"""

import streamlit as st

from happy_green.config import criar_pool, ler_configuracao_streamlit
from happy_green.repositorios.postgres import montar_repositorios_postgres
from happy_green.servicos import Servicos, montar_servicos


@st.cache_resource(show_spinner="Conectando ao banco de dados...")
def _obter_pool():
    return criar_pool(ler_configuracao_streamlit("banco"))


def obter_servicos() -> Servicos:
    return montar_servicos(*montar_repositorios_postgres(_obter_pool()))
