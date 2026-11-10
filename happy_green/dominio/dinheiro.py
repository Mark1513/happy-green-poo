"""Regras monetárias do Happy Green.

Política adotada:
- Moeda: Real brasileiro (BRL).
- Escala: 2 casas decimais (centavos). No banco: ``NUMERIC(14, 2)``.
- Precisão: até 12 dígitos inteiros (máximo 999.999.999.999,99).
- Entrada: valores digitados com mais de 2 casas são RECUSADOS (não são
  arredondados em silêncio).
- Arredondamento: ``ROUND_HALF_UP`` ("meio para cima", o usual no comércio),
  aplicado só a valores calculados, como percentuais de orçamento.
- ``Decimal`` nunca é criado a partir de ``float``: ``float`` é binário e não
  representa exatamente valores como 0,10.
"""

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from happy_green.excecoes import ValorInvalidoError

MOEDA = "BRL"
CASAS_DECIMAIS = 2
QUANTUM = Decimal("0.01")
ARREDONDAMENTO = ROUND_HALF_UP
VALOR_MAXIMO = Decimal("999999999999.99")
ZERO = Decimal("0.00")

_NUMERO_NORMALIZADO = re.compile(r"-?\d+(\.\d+)?")


def converter_valor(valor: str | int | Decimal) -> Decimal:
    """Converte a entrada do usuário em ``Decimal`` com 2 casas.

    Aceita ``"1.500,00"``, ``"1500,5"``, ``"1500.50"``, ``"R$ 10"``, ``int`` e
    ``Decimal``. Recusa ``float`` para preservar a precisão desde a entrada.
    """
    if isinstance(valor, (bool, float)):
        raise ValorInvalidoError(
            "Valores monetários não podem ser float; informe o valor como texto ou Decimal."
        )
    if isinstance(valor, Decimal):
        numero = valor
    elif isinstance(valor, int):
        numero = Decimal(valor)
    elif isinstance(valor, str):
        numero = _ler_texto(valor)
    else:
        raise ValorInvalidoError("Tipo de valor não suportado.")

    if not numero.is_finite():
        raise ValorInvalidoError("Informe um número válido.")
    if numero != numero.quantize(QUANTUM):
        raise ValorInvalidoError("Use no máximo 2 casas decimais (centavos).")
    if abs(numero) > VALOR_MAXIMO:
        raise ValorInvalidoError("Valor acima do máximo permitido (999.999.999.999,99).")
    return numero.quantize(QUANTUM)


def _ler_texto(texto: str) -> Decimal:
    """Interpreta o formato brasileiro, com ou sem separador de milhar."""
    limpo = texto.strip().replace("R$", "").replace(" ", "").replace(" ", "")
    if not limpo:
        raise ValorInvalidoError("Informe um valor.")

    if "," in limpo:
        # Formato brasileiro: vírgula decimal e ponto como milhar ("1.500,00").
        if limpo.count(",") > 1:
            raise ValorInvalidoError(f"Valor inválido: '{texto}'. Exemplo: 1.500,00")
        inteiro, fracao = limpo.split(",")
        limpo = f"{inteiro.replace('.', '')}.{fracao}"
    elif limpo.count(".") > 1 or ("." in limpo and len(limpo.split(".")[1]) == 3):
        # "1.500" ou "1.500.000": pontos são separadores de milhar.
        limpo = limpo.replace(".", "")

    if not _NUMERO_NORMALIZADO.fullmatch(limpo):
        raise ValorInvalidoError(f"Valor inválido: '{texto}'. Exemplo: 1.500,00")
    try:
        return Decimal(limpo)
    except InvalidOperation as erro:  # pragma: no cover - a regex já protege
        raise ValorInvalidoError(f"Valor inválido: '{texto}'.") from erro


def arredondar(valor: Decimal, quantum: Decimal = QUANTUM) -> Decimal:
    """Aplica a política de arredondamento a um valor calculado."""
    return valor.quantize(quantum, rounding=ARREDONDAMENTO)


def percentual(parte: Decimal, total: Decimal) -> Decimal:
    """Percentual com 1 casa decimal (ex.: 120.0). Total zero resulta em 0."""
    if total == 0:
        return Decimal("0.0")
    return arredondar(parte * 100 / total, Decimal("0.1"))


def formatar_brl(valor: Decimal) -> str:
    """Formata no padrão brasileiro: ``Decimal('-1500.5')`` -> ``'-R$ 1.500,50'``."""
    quantizado = arredondar(valor)
    sinal = "-" if quantizado < 0 else ""
    inteiro, centavos = f"{abs(quantizado):.2f}".split(".")
    inteiro_com_milhar = f"{int(inteiro):,}".replace(",", ".")
    return f"{sinal}R$ {inteiro_com_milhar},{centavos}"


def formatar_para_edicao(valor: Decimal) -> str:
    """Formato usado para preencher campos de edição: ``'1500,50'``."""
    return f"{arredondar(valor):.2f}".replace(".", ",")
