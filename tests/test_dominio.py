"""Testes das entidades: encapsulamento, validações, abstração e polimorfismo."""

from datetime import timedelta
from decimal import Decimal

import pytest

from happy_green.dominio import (
    Categoria,
    Competencia,
    ContaFinanceira,
    Despesa,
    Lancamento,
    Receita,
    TipoLancamento,
    criar_lancamento,
    hoje,
)
from happy_green.excecoes import CategoriaIncompativelError, DadosInvalidosError, ValorInvalidoError


@pytest.fixture
def conta():
    return ContaFinanceira("Conta Corrente", "0")


@pytest.fixture
def salario():
    return Categoria("Salário", TipoLancamento.RECEITA)


@pytest.fixture
def alimentacao():
    return Categoria("Alimentação", "despesa")


# ----------------------------------------------------------- abstração
def test_lancamento_e_abstrato(conta, salario):
    with pytest.raises(TypeError):
        Lancamento("x", "10", hoje(), conta, salario)


# ------------------------------------------------ herança e polimorfismo
def test_receita_aumenta_e_despesa_diminui(conta, salario, alimentacao):
    receita = Receita("Salário", "1.500,00", hoje(), conta, salario)
    despesa = Despesa("Mercado", "300,00", hoje(), conta, alimentacao)
    assert isinstance(receita, Lancamento) and isinstance(despesa, Lancamento)
    assert receita.calcular_impacto_no_saldo() == Decimal("1500.00")
    assert despesa.calcular_impacto_no_saldo() == Decimal("-300.00")
    # O valor guardado é sempre positivo; o sinal vem do comportamento.
    assert despesa.valor == Decimal("300.00")


def test_saldo_calculado_polimorficamente(conta, salario, alimentacao):
    outra = ContaFinanceira("Carteira", "50")
    lancamentos = [
        Receita("Salário", "1500", hoje(), conta, salario),
        Despesa("Mercado", "300", hoje(), conta, alimentacao),
        Despesa("Lanche", "20", hoje(), outra, alimentacao),  # outra conta: não entra
    ]
    assert conta.calcular_saldo(lancamentos) == Decimal("1200.00")
    assert outra.calcular_saldo(lancamentos) == Decimal("30.00")


def test_fabrica_reconstroi_a_subclasse_certa(conta, salario, alimentacao):
    receita = criar_lancamento("receita", descricao="A", valor="1", data=hoje(), conta=conta, categoria=salario)
    despesa = criar_lancamento(TipoLancamento.DESPESA, descricao="B", valor="1", data=hoje(), conta=conta,
                               categoria=alimentacao)
    assert type(receita) is Receita
    assert type(despesa) is Despesa


# -------------------------------------------------------- validações
@pytest.mark.parametrize("valor", ["0", "-10", "0,00"])
def test_valor_deve_ser_estritamente_positivo(conta, alimentacao, valor):
    with pytest.raises(ValorInvalidoError):
        Despesa("Mercado", valor, hoje(), conta, alimentacao)


def test_categoria_incompativel(conta, salario, alimentacao):
    with pytest.raises(CategoriaIncompativelError):
        Despesa("Mercado", "10", hoje(), conta, salario)
    with pytest.raises(CategoriaIncompativelError):
        Receita("Salário", "10", hoje(), conta, alimentacao)


@pytest.mark.parametrize("descricao", ["", "   ", None, "x" * 121])
def test_descricao_obrigatoria_e_limitada(conta, alimentacao, descricao):
    with pytest.raises(DadosInvalidosError):
        Despesa(descricao, "10", hoje(), conta, alimentacao)


def test_data_no_futuro_ou_invalida(conta, alimentacao):
    with pytest.raises(DadosInvalidosError, match="futuro"):
        Despesa("Mercado", "10", hoje() + timedelta(days=1), conta, alimentacao)
    with pytest.raises(DadosInvalidosError):
        Despesa("Mercado", "10", "2026-01-01", conta, alimentacao)


def test_edicao_atomica_nao_altera_nada_se_invalida(conta, alimentacao, salario):
    despesa = Despesa("Mercado", "300", hoje(), conta, alimentacao)
    with pytest.raises(CategoriaIncompativelError):
        despesa.editar(descricao="Outro", valor="999", data=hoje(), conta=conta, categoria=salario)
    assert despesa.descricao == "Mercado"
    assert despesa.valor == Decimal("300.00")


def test_edicao_valida(conta, alimentacao):
    despesa = Despesa("Ônibus", "120", hoje(), conta, alimentacao)
    despesa.editar(descricao="Ônibus e metrô", valor="150,00", data=hoje(), conta=conta, categoria=alimentacao)
    assert despesa.valor == Decimal("150.00")
    assert despesa.descricao == "Ônibus e metrô"


# ------------------------------------------------------ encapsulamento
def test_nome_da_conta_validado_e_normalizado():
    conta = ContaFinanceira("  Conta   Corrente ", "10")
    assert conta.nome == "Conta Corrente"
    with pytest.raises(DadosInvalidosError):
        conta.nome = ""
    # Não existe atributo de saldo atual: ele é sempre calculado (sem dado redundante).
    assert not hasattr(conta, "saldo_atual")


def test_saldo_inicial_pode_ser_negativo_mas_nao_float():
    assert ContaFinanceira("Especial", "-100").saldo_inicial == Decimal("-100.00")
    with pytest.raises(ValorInvalidoError):
        ContaFinanceira("Especial", 10.5)


def test_valor_do_lancamento_nao_tem_setter(conta, alimentacao):
    despesa = Despesa("Mercado", "10", hoje(), conta, alimentacao)
    with pytest.raises(AttributeError):
        despesa.valor = Decimal("1")  # type: ignore[misc]


def test_id_atribuido_uma_unica_vez():
    conta = ContaFinanceira("Conta", "0")
    conta.atribuir_id(7)
    conta.atribuir_id(7)  # repetir o mesmo id é permitido
    with pytest.raises(DadosInvalidosError):
        conta.atribuir_id(8)


def test_mesma_entidade_por_id():
    a = ContaFinanceira("Conta", "0", id=1)
    b = ContaFinanceira("Conta (outra leitura)", "0", id=1)
    assert a.mesma_entidade(b)
    assert not a.mesma_entidade(ContaFinanceira("Conta", "0", id=2))
    assert not a.mesma_entidade(Categoria("Conta", "despesa", id=1))  # família diferente


def test_tipo_invalido_de_categoria():
    with pytest.raises(DadosInvalidosError):
        Categoria("Teste", "investimento")


# -------------------------------------------------------- competência
def test_competencia():
    competencia = Competencia(2026, 2)
    assert str(competencia) == "02/2026"
    assert competencia.ultimo_dia.day == 28
    assert competencia.anterior() == Competencia(2026, 1)
    assert Competencia(2026, 12).proxima() == Competencia(2027, 1)
    with pytest.raises(DadosInvalidosError):
        Competencia(2026, 13)
