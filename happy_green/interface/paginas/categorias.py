"""Página Categorias: cadastro, edição e exclusão de categorias de receita e despesa."""

import streamlit as st

from happy_green.dominio import TipoLancamento
from happy_green.interface import componentes, contexto

TIPOS = [TipoLancamento.RECEITA, TipoLancamento.DESPESA]


def pagina() -> None:
    st.title("Categorias")
    componentes.mostrar_mensagem_pendente()
    servicos = contexto.obter_servicos()
    categorias = componentes.carregar(servicos.categorias.listar)

    if categorias:
        receitas, despesas = st.columns(2)
        for coluna, tipo in ((receitas, TipoLancamento.RECEITA), (despesas, TipoLancamento.DESPESA)):
            with coluna:
                st.subheader(f"{tipo.rotulo}s")
                nomes = [{"Categoria": c.nome} for c in categorias if c.tipo is tipo]
                if nomes:
                    componentes.tabela(nomes)
                else:
                    st.caption(f"Nenhuma categoria de {tipo.value}.")
    else:
        st.info("Nenhuma categoria cadastrada ainda. Use o formulário abaixo.", icon=":material/info:")

    aba_nova, aba_editar = st.tabs(["Nova categoria", "Editar ou excluir"])

    with aba_nova:
        with st.form("form_nova_categoria", clear_on_submit=True):
            nome = st.text_input("Nome da categoria", max_chars=60, placeholder="Ex.: Alimentação")
            tipo = st.radio("Tipo", TIPOS, index=1, format_func=lambda t: t.rotulo, horizontal=True)
            if st.form_submit_button("Cadastrar categoria", type="primary", icon=":material/add:"):
                componentes.executar(
                    lambda: servicos.categorias.criar(nome, tipo), f"Categoria '{nome.strip()}' cadastrada."
                )

    with aba_editar:
        if not categorias:
            st.caption("Cadastre uma categoria para poder editá-la.")
            return
        por_id = {c.id: c for c in categorias}
        categoria_id = st.selectbox(
            "Categoria",
            list(por_id),
            format_func=lambda i: f"{por_id[i].nome} ({por_id[i].tipo.value})",
            key="categoria_editar",
        )
        categoria = por_id[categoria_id]
        with st.form(f"form_editar_categoria_{categoria.id}"):
            novo_nome = st.text_input("Nome da categoria", value=categoria.nome, max_chars=60)
            novo_tipo = st.radio(
                "Tipo",
                TIPOS,
                index=TIPOS.index(categoria.tipo),
                format_func=lambda t: t.rotulo,
                horizontal=True,
                help="O tipo só pode mudar se a categoria ainda não tiver lançamentos nem orçamentos.",
            )
            if st.form_submit_button("Salvar alterações", type="primary", icon=":material/save:"):
                componentes.executar(
                    lambda: servicos.categorias.editar(categoria.id, novo_nome, novo_tipo), "Categoria atualizada."
                )
        if st.button("Excluir categoria", icon=":material/delete:", key=f"excluir_categoria_{categoria.id}"):
            componentes.confirmar_exclusao(
                f"Excluir a categoria **{categoria.nome}**? Só é possível excluir categorias sem uso.",
                lambda: servicos.categorias.excluir(categoria.id),
                f"Categoria '{categoria.nome}' excluída.",
            )
