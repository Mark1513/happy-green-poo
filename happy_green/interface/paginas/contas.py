"""Página Contas: cadastro, edição, listagem e exclusão de contas."""

import streamlit as st

from happy_green.dominio.dinheiro import formatar_brl, formatar_para_edicao
from happy_green.interface import componentes, contexto


def pagina() -> None:
    st.title("Contas")
    componentes.mostrar_mensagem_pendente()
    servicos = contexto.obter_servicos()
    contas = componentes.carregar(servicos.contas.listar_com_saldo)

    if contas:
        componentes.tabela(
            [
                {"Conta": c.nome, "Saldo inicial": formatar_brl(c.saldo_inicial), "Saldo atual": formatar_brl(s)}
                for c, s in contas
            ]
        )
        st.caption("O saldo atual é calculado: saldo inicial + receitas - despesas da conta.")
    else:
        st.info("Nenhuma conta cadastrada ainda. Use o formulário abaixo.", icon=":material/info:")

    aba_nova, aba_editar = st.tabs(["Nova conta", "Editar ou excluir"])

    with aba_nova:
        with st.form("form_nova_conta", clear_on_submit=True):
            nome = st.text_input("Nome da conta", max_chars=60, placeholder="Ex.: Conta Corrente")
            saldo = st.text_input("Saldo inicial (R$)", value="0,00", help=componentes.ajuda_valor())
            if st.form_submit_button("Cadastrar conta", type="primary", icon=":material/add:"):
                componentes.executar(
                    lambda: servicos.contas.criar(nome, saldo), f"Conta '{nome.strip()}' cadastrada."
                )

    with aba_editar:
        if not contas:
            st.caption("Cadastre uma conta para poder editá-la.")
            return
        por_id = {c.id: c for c, _ in contas}
        conta_id = st.selectbox("Conta", list(por_id), format_func=lambda i: por_id[i].nome, key="conta_editar")
        conta = por_id[conta_id]
        with st.form(f"form_editar_conta_{conta.id}"):
            novo_nome = st.text_input("Nome da conta", value=conta.nome, max_chars=60)
            novo_saldo = st.text_input(
                "Saldo inicial (R$)", value=formatar_para_edicao(conta.saldo_inicial), help=componentes.ajuda_valor()
            )
            if st.form_submit_button("Salvar alterações", type="primary", icon=":material/save:"):
                componentes.executar(
                    lambda: servicos.contas.editar(conta.id, novo_nome, novo_saldo), "Conta atualizada."
                )
        if st.button("Excluir conta", icon=":material/delete:", key=f"excluir_conta_{conta.id}"):
            componentes.confirmar_exclusao(
                f"Excluir a conta **{conta.nome}**? Só é possível excluir contas sem lançamentos.",
                lambda: servicos.contas.excluir(conta.id),
                f"Conta '{conta.nome}' excluída.",
            )
