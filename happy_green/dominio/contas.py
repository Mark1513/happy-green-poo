"""Conta financeira (conta corrente, carteira, poupança...)."""

from collections.abc import Iterable
from decimal import Decimal
from typing import TYPE_CHECKING

from happy_green.dominio.dinheiro import ZERO, converter_valor
from happy_green.dominio.entidade import Entidade
from happy_green.dominio.textos import validar_texto

if TYPE_CHECKING:  # evita importação circular; usado só nas anotações
    from happy_green.dominio.lancamentos import Lancamento


class ContaFinanceira(Entidade):
    """Conta com saldo inicial. O saldo atual NÃO é armazenado: é calculado.

    Guardar o saldo atual no banco criaria um dado redundante que poderia
    divergir dos lançamentos. Por isso ele sempre é derivado do saldo inicial
    mais o impacto de cada lançamento.
    """

    TAMANHO_MAXIMO_NOME = 60

    def __init__(self, nome: str, saldo_inicial: str | int | Decimal = ZERO, id: int | None = None) -> None:
        super().__init__(id)
        self.nome = nome
        self.saldo_inicial = saldo_inicial

    @property
    def nome(self) -> str:
        return self._nome

    @nome.setter
    def nome(self, valor: str) -> None:
        self._nome = validar_texto(valor, "nome da conta", self.TAMANHO_MAXIMO_NOME)

    @property
    def saldo_inicial(self) -> Decimal:
        return self._saldo_inicial

    @saldo_inicial.setter
    def saldo_inicial(self, valor: str | int | Decimal) -> None:
        # Pode ser negativo (ex.: conta que já começou no cheque especial).
        self._saldo_inicial = converter_valor(valor)

    def calcular_saldo(self, lancamentos: Iterable["Lancamento"]) -> Decimal:
        """Saldo acumulado = saldo inicial + impacto de cada lançamento desta conta.

        Polimorfismo: não perguntamos se o lançamento é receita ou despesa;
        cada objeto sabe calcular o próprio impacto.
        """
        impacto = sum(
            (lancamento.calcular_impacto_no_saldo() for lancamento in lancamentos if lancamento.pertence_a(self)),
            ZERO,
        )
        return self._saldo_inicial + impacto

    def __str__(self) -> str:
        return self._nome

    def __repr__(self) -> str:
        return f"ContaFinanceira(id={self.id!r}, nome={self._nome!r}, saldo_inicial={self._saldo_inicial!r})"
