"""Testes da política monetária (Decimal, formato brasileiro e arredondamento)."""

from decimal import Decimal

import pytest

from happy_green.dominio.dinheiro import (
    arredondar,
    converter_valor,
    formatar_brl,
    formatar_para_edicao,
    percentual,
)
from happy_green.excecoes import ValorInvalidoError


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("1.500,00", Decimal("1500.00")),
        ("1500,5", Decimal("1500.50")),
        ("1500.50", Decimal("1500.50")),
        ("1.500", Decimal("1500.00")),
        ("1.234.567,89", Decimal("1234567.89")),
        ("R$ 10", Decimal("10.00")),
        ("  0,10 ", Decimal("0.10")),
        ("-250,00", Decimal("-250.00")),
        (300, Decimal("300.00")),
        (Decimal("12.3"), Decimal("12.30")),
    ],
)
def test_converte_entradas_validas(entrada, esperado):
    assert converter_valor(entrada) == esperado


def test_resultado_sempre_tem_duas_casas():
    assert converter_valor("7").as_tuple().exponent == -2


@pytest.mark.parametrize("entrada", ["", "abc", "1,2,3", "10,999", "1e5", "--1", Decimal("NaN")])
def test_recusa_entradas_invalidas(entrada):
    with pytest.raises(ValorInvalidoError):
        converter_valor(entrada)


def test_recusa_float_para_preservar_precisao():
    with pytest.raises(ValorInvalidoError, match="float"):
        converter_valor(0.1)


def test_recusa_valor_acima_do_maximo():
    with pytest.raises(ValorInvalidoError):
        converter_valor("1.000.000.000.000,00")


def test_arredondamento_meio_para_cima():
    assert arredondar(Decimal("2.345")) == Decimal("2.35")
    assert arredondar(Decimal("2.344")) == Decimal("2.34")


def test_percentual_com_uma_casa():
    assert percentual(Decimal("300"), Decimal("250")) == Decimal("120.0")
    assert percentual(Decimal("1"), Decimal("3")) == Decimal("33.3")
    assert percentual(Decimal("5"), Decimal("0")) == Decimal("0.0")


@pytest.mark.parametrize(
    ("valor", "texto"),
    [
        (Decimal("1500"), "R$ 1.500,00"),
        (Decimal("-1080.5"), "-R$ 1.080,50"),
        (Decimal("0"), "R$ 0,00"),
        (Decimal("1234567.89"), "R$ 1.234.567,89"),
    ],
)
def test_formatacao_brl(valor, texto):
    assert formatar_brl(valor) == texto


def test_formatacao_para_edicao_volta_a_ser_lida():
    texto = formatar_para_edicao(Decimal("1500.5"))
    assert texto == "1500,50"
    assert converter_valor(texto) == Decimal("1500.50")
