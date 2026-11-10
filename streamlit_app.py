"""Happy Green: ponto de entrada da aplicação Streamlit.

Este arquivo só cuida da inicialização (configuração da página, registros de
log, identidade visual) e da navegação. As regras ficam em ``happy_green``.

Executar localmente:  streamlit run streamlit_app.py
"""

import logging

import streamlit as st

from happy_green.interface import componentes
from happy_green.interface.paginas import categorias, contas, lancamentos, orcamentos, painel, resumo

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

st.set_page_config(page_title="Happy Green", page_icon="assets/icone.svg", layout="wide")
st.logo("assets/logo.svg", icon_image="assets/icone.svg")

navegacao = st.navigation(
    [
        st.Page(painel.pagina, title="Painel", icon=":material/dashboard:", default=True),
        st.Page(contas.pagina, title="Contas", icon=":material/account_balance_wallet:", url_path="contas"),
        st.Page(categorias.pagina, title="Categorias", icon=":material/sell:", url_path="categorias"),
        st.Page(lancamentos.pagina, title="Lançamentos", icon=":material/receipt_long:", url_path="lancamentos"),
        st.Page(orcamentos.pagina, title="Orçamentos", icon=":material/savings:", url_path="orcamentos"),
        st.Page(resumo.pagina, title="Resumo mensal", icon=":material/bar_chart:", url_path="resumo"),
    ]
)

componentes.aviso_demonstracao()
navegacao.run()

st.sidebar.caption("Happy Green · projeto acadêmico de Programação Orientada a Objetos")
