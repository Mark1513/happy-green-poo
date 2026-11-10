"""Página Painel: visão geral do mês e saldo acumulado."""

import streamlit as st

from happy_green.dominio import TipoLancamento
from happy_green.dominio.dinheiro import formatar_brl
from happy_green.interface import componentes, contexto


def pagina() -> None:
    st.title("Painel")
    componentes.mostrar_mensagem_pendente()
    competencia = componentes.seletor_competencia("painel")
    painel = componentes.carregar(lambda: contexto.obter_servicos().relatorios.painel(competencia))

    if not painel.saldos_por_conta:
        st.info("Nenhuma conta cadastrada ainda. Comece pela página **Contas**.", icon=":material/info:")
        return

    resumo = painel.resumo
    # Grade 2 x 2: os valores cabem inteiros no computador e no celular.
    linha_1, linha_2 = st.columns(2), st.columns(2)
    linha_1[0].metric(
        "Saldo total atual",
        formatar_brl(painel.saldo_total),
        help="Saldo ACUMULADO: saldos iniciais + todos os lançamentos até hoje, em todas as contas.",
        border=True,
    )
    linha_1[1].metric(
        "Resultado do mês",
        formatar_brl(resumo.resultado),
        help="Receitas do mês menos despesas do mês. Não inclui saldos iniciais nem outros meses.",
        border=True,
    )
    linha_2[0].metric("Receitas do mês", formatar_brl(resumo.total_receitas), border=True)
    linha_2[1].metric("Despesas do mês", formatar_brl(resumo.total_despesas), border=True)
    st.caption(
        "**Saldo acumulado** considera todo o histórico de cada conta. "
        f"**Resultado mensal** considera apenas {competencia.rotulo_extenso}."
    )

    for orcamento, situacao in painel.orcamentos_ultrapassados:
        st.warning(
            componentes.md(
                f"Orçamento de **{orcamento.categoria.nome}** ultrapassado: gasto de "
                f"{formatar_brl(situacao.consumido)} para um limite de {formatar_brl(situacao.limite)} "
                f"({formatar_brl(situacao.excedente)} acima)."
            ),
            icon=":material/warning:",
        )

    esquerda, direita = st.columns(2)
    with esquerda:
        st.subheader("Saldos por conta")
        componentes.tabela(
            [{"Conta": conta.nome, "Saldo atual": formatar_brl(saldo)} for conta, saldo in painel.saldos_por_conta]
        )
    with direita:
        st.subheader("Despesas por categoria")
        despesas = [(i.categoria.nome, i.total) for i in resumo.itens_do_tipo(TipoLancamento.DESPESA) if i.total > 0]
        if despesas:
            componentes.grafico_por_categoria(despesas)
        else:
            st.caption("Nenhuma despesa neste mês.")

    st.subheader("Últimos lançamentos do mês")
    if painel.ultimos_lancamentos:
        componentes.tabela(componentes.linhas_de_lancamentos(list(painel.ultimos_lancamentos)))
    else:
        st.caption("Nenhum lançamento neste mês.")
