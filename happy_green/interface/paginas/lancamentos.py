"""Página Lançamentos: registro, consulta com filtros, edição e exclusão."""

from datetime import date
from uuid import uuid4

import streamlit as st

from happy_green.dominio import Competencia, TipoLancamento, Totais, hoje
from happy_green.dominio.dinheiro import formatar_brl, formatar_para_edicao
from happy_green.interface import componentes, contexto
from happy_green.repositorios import FiltroLancamentos

TIPOS = [TipoLancamento.RECEITA, TipoLancamento.DESPESA]
_CHAVE_ENVIO = "chave_envio_novo_lancamento"


def pagina() -> None:
    st.title("Lançamentos")
    componentes.mostrar_mensagem_pendente()
    servicos = contexto.obter_servicos()
    contas = componentes.carregar(servicos.contas.listar)
    categorias = componentes.carregar(servicos.categorias.listar)

    if not contas or not categorias:
        st.info(
            "Para registrar lançamentos, cadastre antes pelo menos uma **conta** e uma **categoria**.",
            icon=":material/info:",
        )
        return

    conta_por_id = {c.id: c for c in contas}
    categoria_por_id = {c.id: c for c in categorias}

    # ------------------------------------------------------------ filtros
    with st.container(border=True):
        st.markdown("**Filtros**")
        atual = Competencia.atual()
        col_periodo, col_tipo = st.columns([2, 1])
        periodo = col_periodo.date_input(
            "Período",
            value=(atual.primeiro_dia, hoje()),
            min_value=date(2000, 1, 1),
            max_value=hoje(),
            format="DD/MM/YYYY",
            key="filtro_periodo",
        )
        tipo = col_tipo.selectbox(
            "Tipo", [None, *TIPOS], format_func=lambda t: "Todos" if t is None else t.rotulo, key="filtro_tipo"
        )
        col_conta, col_categoria = st.columns(2)
        conta_id = col_conta.selectbox(
            "Conta", [None, *conta_por_id], format_func=lambda i: "Todas" if i is None else conta_por_id[i].nome,
            key="filtro_conta",
        )
        categoria_id = col_categoria.selectbox(
            "Categoria",
            [None, *categoria_por_id],
            format_func=lambda i: "Todas" if i is None else f"{categoria_por_id[i].nome} ({categoria_por_id[i].tipo.value})",
            key="filtro_categoria",
        )

    inicio, fim = (periodo[0], periodo[-1]) if periodo else (None, None)
    filtro = componentes.carregar(
        lambda: FiltroLancamentos(data_inicio=inicio, data_fim=fim, conta_id=conta_id, categoria_id=categoria_id,
                                  tipo=tipo)
    )
    lancamentos = componentes.carregar(lambda: servicos.lancamentos.consultar(filtro))

    totais = Totais.calcular(lancamentos)
    # Linha de texto (e não 3 indicadores lado a lado): cabe inteira em qualquer largura.
    with st.container(border=True):
        st.markdown(
            componentes.md(
                f"**{len(lancamentos)} lançamento(s) no filtro** · "
                f"Receitas: **{formatar_brl(totais.receitas)}** · "
                f"Despesas: **{formatar_brl(totais.despesas)}** · "
                f"Resultado: **{formatar_brl(totais.resultado)}**"
            )
        )

    if lancamentos:
        componentes.tabela(componentes.linhas_de_lancamentos(lancamentos), altura=min(420, 38 + 35 * len(lancamentos)))
    else:
        st.info("Nenhum lançamento encontrado para os filtros escolhidos.", icon=":material/search_off:")

    aba_novo, aba_editar = st.tabs(["Novo lançamento", "Editar ou excluir"])

    # ----------------------------------------------------------- registro
    with aba_novo:
        tipo_novo = st.radio("Tipo do lançamento", TIPOS, index=1, format_func=lambda t: t.rotulo,
                             horizontal=True, key="novo_tipo")
        categorias_do_tipo = [c for c in categorias if c.tipo is tipo_novo]
        if not categorias_do_tipo:
            st.warning(f"Cadastre uma categoria de {tipo_novo.value} antes.", icon=":material/warning:")
        else:
            # Chave única por formulário: se o mesmo envio chegar duas vezes
            # (clique duplo, reexecução), o banco grava apenas um lançamento.
            st.session_state.setdefault(_CHAVE_ENVIO, uuid4())
            with st.form("form_novo_lancamento", clear_on_submit=True):
                descricao = st.text_input("Descrição", max_chars=120, placeholder="Ex.: Supermercado")
                valor = st.text_input("Valor (R$)", placeholder="0,00", help=componentes.ajuda_valor())
                data = componentes.campo_data("Data", hoje(), "novo_data")
                col_a, col_b = st.columns(2)
                conta_nova = col_a.selectbox("Conta", list(conta_por_id), format_func=lambda i: conta_por_id[i].nome)
                categoria_nova = col_b.selectbox(
                    "Categoria", [c.id for c in categorias_do_tipo], format_func=lambda i: categoria_por_id[i].nome
                )
                if st.form_submit_button(f"Registrar {tipo_novo.value}", type="primary", icon=":material/add:"):

                    def registrar() -> None:
                        servicos.lancamentos.registrar(
                            tipo_novo, descricao, valor, data, conta_nova, categoria_nova,
                            chave_envio=st.session_state[_CHAVE_ENVIO],
                        )
                        st.session_state[_CHAVE_ENVIO] = uuid4()  # próximo formulário, nova chave

                    componentes.executar(registrar, f"{tipo_novo.rotulo} '{descricao.strip()}' registrada.")

    # ------------------------------------------------- edição e exclusão
    with aba_editar:
        if not lancamentos:
            st.caption("Ajuste os filtros para encontrar o lançamento que deseja editar.")
            return
        por_id = {l.id: l for l in lancamentos}
        lancamento_id = st.selectbox(
            "Lançamento (dentre os filtrados)",
            list(por_id),
            format_func=lambda i: f"{por_id[i].data:%d/%m/%Y} · {por_id[i].descricao} · "
                                  f"{formatar_brl(por_id[i].calcular_impacto_no_saldo())}",
            key="lancamento_editar",
        )
        lancamento = por_id[lancamento_id]
        compativeis = [c for c in categorias if c.aceita(lancamento.tipo)]
        st.caption(f"Tipo: **{lancamento.tipo.rotulo}** (para trocar o tipo, exclua e registre novamente).")
        with st.form(f"form_editar_lancamento_{lancamento.id}"):
            descricao = st.text_input("Descrição", value=lancamento.descricao, max_chars=120)
            valor = st.text_input("Valor (R$)", value=formatar_para_edicao(lancamento.valor),
                                  help=componentes.ajuda_valor())
            data = componentes.campo_data("Data", lancamento.data, f"editar_data_{lancamento.id}")
            col_a, col_b = st.columns(2)
            ids_contas = list(conta_por_id)
            conta_edit = col_a.selectbox(
                "Conta", ids_contas, index=ids_contas.index(lancamento.conta.id),
                format_func=lambda i: conta_por_id[i].nome,
            )
            ids_categorias = [c.id for c in compativeis]
            categoria_edit = col_b.selectbox(
                "Categoria", ids_categorias, index=ids_categorias.index(lancamento.categoria.id),
                format_func=lambda i: categoria_por_id[i].nome,
            )
            if st.form_submit_button("Salvar alterações", type="primary", icon=":material/save:"):
                componentes.executar(
                    lambda: servicos.lancamentos.editar(
                        lancamento.id, descricao, valor, data, conta_edit, categoria_edit
                    ),
                    "Lançamento atualizado. Saldos, resumos e orçamentos já consideram a alteração.",
                )
        if st.button("Excluir lançamento", icon=":material/delete:", key=f"excluir_lancamento_{lancamento.id}"):
            componentes.confirmar_exclusao(
                f"Excluir **{lancamento.descricao}** ({formatar_brl(lancamento.valor)}, "
                f"{lancamento.data:%d/%m/%Y})?",
                lambda: servicos.lancamentos.excluir(lancamento.id),
                "Lançamento excluído. Saldos, resumos e orçamentos foram atualizados.",
            )
