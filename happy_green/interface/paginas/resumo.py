"""Página Resumo mensal: totais por categoria."""

import streamlit as st

from happy_green.dominio import TipoLancamento
from happy_green.dominio.dinheiro import formatar_brl
from happy_green.interface import componentes, contexto


def _situacao(item) -> str:
    if item.situacao_orcamento is None:
        return "—"
    return ("Ultrapassado" if item.situacao_orcamento.ultrapassado else "Dentro do limite") + (
        f" ({formatar_brl(item.situacao_orcamento.limite)})"
    )


def pagina() -> None:
    st.title("Resumo mensal")
    componentes.mostrar_mensagem_pendente()
    competencia = componentes.seletor_competencia("resumo")
    resumo = componentes.carregar(lambda: contexto.obter_servicos().relatorios.resumo_mensal(competencia))

    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", formatar_brl(resumo.total_receitas), border=True)
    c2.metric("Despesas", formatar_brl(resumo.total_despesas), border=True)
    c3.metric("Resultado do mês", formatar_brl(resumo.resultado), border=True)
    st.caption(f"{resumo.quantidade_lancamentos} lançamento(s) em {competencia.rotulo_extenso}.")

    if not resumo.itens:
        st.info(f"Nenhum lançamento ou orçamento em {competencia}.", icon=":material/info:")
        return

    for tipo in (TipoLancamento.RECEITA, TipoLancamento.DESPESA):
        itens = resumo.itens_do_tipo(tipo)
        st.subheader(f"{tipo.rotulo}s por categoria")
        if not itens:
            st.caption(f"Nenhuma {tipo.value} neste mês.")
            continue
        linhas = [
            {
                "Categoria": item.categoria.nome,
                "Lançamentos": item.quantidade,
                "Total": formatar_brl(item.total),
                "% do total": f"{item.participacao}%".replace(".", ","),
            }
            for item in itens
        ]
        if tipo is TipoLancamento.DESPESA:
            for linha, item in zip(linhas, itens):
                linha["Orçamento"] = _situacao(item)
        componentes.tabela(linhas)
        if tipo is TipoLancamento.DESPESA and any(item.total > 0 for item in itens):
            componentes.grafico_por_categoria([(i.categoria.nome, i.total) for i in itens if i.total > 0])
