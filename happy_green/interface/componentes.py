"""Componentes reutilizáveis da interface (mensagens, tabelas, diálogos, seletores)."""

import logging
from collections.abc import Callable
from datetime import date
from decimal import Decimal

import streamlit as st

from happy_green.dominio import Competencia, Lancamento, hoje
from happy_green.dominio.dinheiro import formatar_brl
from happy_green.excecoes import ErroHappyGreen

log = logging.getLogger("happy_green.interface")

_CHAVE_MENSAGEM = "_mensagem_de_sucesso"
MESES = ("Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro")


def md(texto: str) -> str:
    """Escapa o cifrão: no Markdown do Streamlit, texto entre dois "$" vira fórmula."""
    return texto.replace("$", "\\$")


def aviso_demonstracao() -> None:
    st.info(
        "**Demonstração acadêmica.** Os dados são fictícios e **compartilhados entre todos os "
        "visitantes**: qualquer pessoa pode alterá-los ou excluí-los. Não registre informações reais.",
        icon=":material/science:",
    )


def mostrar_mensagem_pendente() -> None:
    """Exibe a mensagem de sucesso guardada antes do último ``st.rerun()``."""
    mensagem = st.session_state.pop(_CHAVE_MENSAGEM, None)
    if mensagem:
        st.success(md(mensagem), icon=":material/check_circle:")


def executar(acao: Callable[[], object], mensagem_sucesso: str) -> None:
    """Executa uma gravação e recarrega a página para mostrar os dados atualizados.

    Erros previstos aparecem como mensagem amigável; detalhes técnicos vão
    apenas para o log do servidor.
    """
    try:
        acao()
    except ErroHappyGreen as erro:
        st.error(md(erro.mensagem), icon=":material/error:")
        return
    except Exception:  # noqa: BLE001 - qualquer falha inesperada é registrada no log
        log.exception("Erro inesperado ao executar uma ação")
        st.error("Ocorreu um erro inesperado. Tente novamente.", icon=":material/error:")
        return
    st.session_state[_CHAVE_MENSAGEM] = mensagem_sucesso
    st.rerun()  # fora do try: o rerun do Streamlit funciona lançando uma exceção interna


def carregar(funcao: Callable[[], object]):
    """Executa uma leitura; se falhar, mostra a mensagem e interrompe a página."""
    try:
        return funcao()
    except ErroHappyGreen as erro:
        st.error(md(erro.mensagem), icon=":material/cloud_off:")
    except Exception:  # noqa: BLE001
        log.exception("Erro inesperado ao carregar dados")
        st.error("Não foi possível carregar os dados agora. Tente novamente.", icon=":material/cloud_off:")
    st.stop()


@st.dialog("Confirmar exclusão")
def confirmar_exclusao(descricao: str, acao: Callable[[], object], mensagem_sucesso: str) -> None:
    st.markdown(md(descricao))
    st.warning("Esta ação não pode ser desfeita.", icon=":material/warning:")
    coluna_excluir, coluna_cancelar = st.columns(2)
    if coluna_excluir.button("Sim, excluir", type="primary", icon=":material/delete:", width="stretch"):
        executar(acao, mensagem_sucesso)
    if coluna_cancelar.button("Cancelar", width="stretch"):
        st.rerun()


def seletor_competencia(chave: str, permitir_futuro: bool = False) -> Competencia:
    """Escolha de mês e ano. Padrão: mês atual (horário de Brasília)."""
    atual = Competencia.atual()
    anos = list(range(atual.ano - 4, atual.ano + (2 if permitir_futuro else 1)))
    coluna_mes, coluna_ano = st.columns(2)
    mes = coluna_mes.selectbox(
        "Mês", range(1, 13), index=atual.mes - 1, format_func=lambda m: MESES[m - 1], key=f"{chave}_mes"
    )
    ano = coluna_ano.selectbox("Ano", anos, index=anos.index(atual.ano), key=f"{chave}_ano")
    return Competencia(ano, mes)


def tabela(linhas: list[dict], altura: int | None = None) -> None:
    if altura:
        st.dataframe(linhas, hide_index=True, width="stretch", height=altura)
    else:
        st.dataframe(linhas, hide_index=True, width="stretch")


def linhas_de_lancamentos(lancamentos: list[Lancamento]) -> list[dict]:
    """Converte lançamentos em linhas de tabela. O sinal vem do método polimórfico."""
    return [
        {
            "Data": l.data.strftime("%d/%m/%Y"),
            "Tipo": l.tipo.rotulo,
            "Descrição": l.descricao,
            "Categoria": l.categoria.nome,
            "Conta": l.conta.nome,
            "Valor": formatar_brl(l.calcular_impacto_no_saldo()),
        }
        for l in lancamentos
    ]


def grafico_por_categoria(itens: list[tuple[str, Decimal]], rotulo_valor: str = "Total (R$)") -> None:
    """Gráfico de barras com dados reais. Decimal vira float SÓ para desenhar."""
    dados = {"Categoria": [nome for nome, _ in itens], rotulo_valor: [float(valor) for _, valor in itens]}
    st.bar_chart(dados, x="Categoria", y=rotulo_valor, horizontal=True, color="#1B6E3C")


def campo_data(rotulo: str, valor: date, chave: str) -> date:
    return st.date_input(
        rotulo, value=valor, min_value=date(2000, 1, 1), max_value=hoje(), format="DD/MM/YYYY", key=chave
    )


def ajuda_valor() -> str:
    return "Use vírgula para os centavos. Exemplos: 1500 · 1.500,00 · 89,90"
