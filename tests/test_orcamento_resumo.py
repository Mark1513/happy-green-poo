"""Testes de orçamento mensal e resumo mensal."""

from datetime import date
from decimal import Decimal

import pytest

from happy_green.dominio import (
    Categoria,
    Competencia,
    ContaFinanceira,
    Despesa,
    OrcamentoMensal,
    Receita,
    ResumoMensal,
    TipoLancamento,
)
from happy_green.excecoes import CategoriaIncompativelError, ValorInvalidoError

OUTUBRO = Competencia(2026, 10)
DIA = date(2026, 10, 15)


@pytest.fixture
def dados():
    conta = ContaFinanceira("Conta", "1000", id=1)
    salario = Categoria("Salário", "receita", id=1)
    alimentacao = Categoria("Alimentação", "despesa", id=2)
    transporte = Categoria("Transporte", "despesa", id=3)
    lancamentos = [
        Receita("Salário", "1500", DIA, conta, salario, id=1),
        Despesa("Mercado", "300", DIA, conta, alimentacao, id=2),
        Despesa("Ônibus", "120", DIA, conta, transporte, id=3),
        Despesa("Mercado de setembro", "999", date(2026, 9, 30), conta, alimentacao, id=4),
    ]
    return conta, salario, alimentacao, transporte, lancamentos


def test_orcamento_so_para_despesa(dados):
    _, salario, *_ = dados
    with pytest.raises(CategoriaIncompativelError):
        OrcamentoMensal(salario, OUTUBRO, "100")


def test_limite_positivo(dados):
    _, _, alimentacao, *_ = dados
    with pytest.raises(ValorInvalidoError):
        OrcamentoMensal(alimentacao, OUTUBRO, "0")


def test_orcamento_ultrapassado_considera_so_o_mes(dados):
    _, _, alimentacao, _, lancamentos = dados
    situacao = OrcamentoMensal(alimentacao, OUTUBRO, "250").calcular_situacao(lancamentos)
    assert situacao.consumido == Decimal("300.00")  # setembro não entra
    assert situacao.ultrapassado
    assert situacao.excedente == Decimal("50.00")
    assert situacao.percentual_consumido == Decimal("120.0")
    assert "ultrapassado" in situacao.mensagem


def test_orcamento_dentro_do_limite(dados):
    _, _, _, transporte, lancamentos = dados
    situacao = OrcamentoMensal(transporte, OUTUBRO, "200").calcular_situacao(lancamentos)
    assert not situacao.ultrapassado
    assert situacao.disponivel == Decimal("80.00")


def test_orcamento_reconhece_categoria_lida_em_outra_consulta(dados):
    _, _, _, _, lancamentos = dados
    mesma_categoria_relida = Categoria("Alimentação", "despesa", id=2)
    orcamento = OrcamentoMensal(mesma_categoria_relida, OUTUBRO, "250")
    assert orcamento.calcular_consumo(lancamentos) == Decimal("300.00")


def test_resumo_mensal_diferencia_resultado_de_saldo(dados):
    conta, _, alimentacao, _, lancamentos = dados
    resumo = ResumoMensal(OUTUBRO, lancamentos, [OrcamentoMensal(alimentacao, OUTUBRO, "250")])
    assert resumo.total_receitas == Decimal("1500.00")
    assert resumo.total_despesas == Decimal("420.00")
    assert resumo.resultado == Decimal("1080.00")
    # Saldo acumulado inclui saldo inicial (1000) e o lançamento de setembro (-999).
    assert conta.calcular_saldo(lancamentos) == Decimal("1081.00")


def test_resumo_por_categoria(dados):
    _, _, alimentacao, _, lancamentos = dados
    resumo = ResumoMensal(OUTUBRO, lancamentos, [OrcamentoMensal(alimentacao, OUTUBRO, "250")])
    despesas = resumo.itens_do_tipo(TipoLancamento.DESPESA)
    assert [(i.categoria.nome, i.total) for i in despesas] == [
        ("Alimentação", Decimal("300.00")),
        ("Transporte", Decimal("120.00")),
    ]
    assert despesas[0].participacao == Decimal("71.4")
    assert despesas[0].situacao_orcamento.ultrapassado


def test_categoria_com_orcamento_e_sem_gasto_aparece_com_zero(dados):
    *_, lancamentos = dados
    lazer = Categoria("Lazer", "despesa", id=9)
    resumo = ResumoMensal(OUTUBRO, lancamentos, [OrcamentoMensal(lazer, OUTUBRO, "100")])
    item = next(i for i in resumo.itens if i.categoria.nome == "Lazer")
    assert item.total == Decimal("0.00")
    assert not item.situacao_orcamento.ultrapassado


def test_totais_de_qualquer_colecao(dados):
    from happy_green.dominio import Totais

    *_, lancamentos = dados
    totais = Totais.calcular(lancamentos)
    assert (totais.receitas, totais.despesas, totais.resultado) == (
        Decimal("1500.00"), Decimal("1419.00"), Decimal("81.00"),
    )


def test_resumo_vazio():
    resumo = ResumoMensal(OUTUBRO, [])
    assert resumo.resultado == Decimal("0.00")
    assert resumo.itens == ()
