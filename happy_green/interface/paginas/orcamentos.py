"""Página Orçamentos: limite mensal por categoria de despesa e acompanhamento."""

import streamlit as st

from happy_green.dominio import TipoLancamento
from happy_green.dominio.dinheiro import formatar_brl, formatar_para_edicao
from happy_green.interface import componentes, contexto


def pagina() -> None:
    st.title("Orçamentos")
    componentes.mostrar_mensagem_pendente()
    servicos = contexto.obter_servicos()
    competencia = componentes.seletor_competencia("orcamentos", permitir_futuro=True)
    acompanhamento = componentes.carregar(lambda: servicos.orcamentos.acompanhar(competencia))
    categorias_despesa = componentes.carregar(lambda: servicos.categorias.listar(TipoLancamento.DESPESA))

    if acompanhamento:
        for orcamento, situacao in acompanhamento:
            with st.container(border=True):
                st.markdown(f"**{orcamento.categoria.nome}**")
                c1, c2, c3 = st.columns(3)
                c1.metric("Limite", formatar_brl(situacao.limite))
                c2.metric("Gasto", formatar_brl(situacao.consumido))
                c3.metric("Disponível", formatar_brl(situacao.disponivel))
                # A barra vai até 100%; acima disso o aviso explica o excedente.
                st.progress(
                    min(int(situacao.percentual_consumido), 100),
                    text=f"{situacao.percentual_consumido}% do limite".replace(".", ","),
                )
                if situacao.ultrapassado:
                    st.error(componentes.md(f"Atenção: {situacao.mensagem}"), icon=":material/warning:")
    else:
        st.info(f"Nenhum orçamento definido para {competencia}.", icon=":material/info:")

    aba_definir, aba_editar = st.tabs(["Definir orçamento", "Alterar ou excluir"])

    with aba_definir:
        if not categorias_despesa:
            st.warning("Cadastre uma categoria de despesa antes.", icon=":material/warning:")
        else:
            por_id = {c.id: c for c in categorias_despesa}
            with st.form("form_novo_orcamento", clear_on_submit=True):
                st.caption(f"Mês do orçamento: **{competencia}** (escolha acima).")
                categoria_id = st.selectbox("Categoria de despesa", list(por_id), format_func=lambda i: por_id[i].nome)
                limite = st.text_input("Limite mensal (R$)", placeholder="0,00", help=componentes.ajuda_valor())
                if st.form_submit_button("Definir orçamento", type="primary", icon=":material/add:"):
                    componentes.executar(
                        lambda: servicos.orcamentos.definir(categoria_id, competencia, limite),
                        f"Orçamento de '{por_id[categoria_id].nome}' definido para {competencia}.",
                    )

    with aba_editar:
        if not acompanhamento:
            st.caption("Não há orçamentos neste mês para alterar.")
            return
        por_id = {o.id: o for o, _ in acompanhamento}
        orcamento_id = st.selectbox(
            "Orçamento", list(por_id), format_func=lambda i: por_id[i].categoria.nome, key="orcamento_editar"
        )
        orcamento = por_id[orcamento_id]
        with st.form(f"form_editar_orcamento_{orcamento.id}"):
            novo_limite = st.text_input(
                "Novo limite (R$)", value=formatar_para_edicao(orcamento.limite), help=componentes.ajuda_valor()
            )
            if st.form_submit_button("Salvar limite", type="primary", icon=":material/save:"):
                componentes.executar(
                    lambda: servicos.orcamentos.alterar_limite(orcamento.id, novo_limite), "Limite atualizado."
                )
        if st.button("Excluir orçamento", icon=":material/delete:", key=f"excluir_orcamento_{orcamento.id}"):
            componentes.confirmar_exclusao(
                f"Excluir o orçamento de **{orcamento.categoria.nome}** em {orcamento.competencia}?",
                lambda: servicos.orcamentos.excluir(orcamento.id),
                "Orçamento excluído.",
            )
