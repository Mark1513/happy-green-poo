"""Orçamento mensal por categoria de despesa."""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from happy_green.dominio.categorias import Categoria, TipoLancamento
from happy_green.dominio.dinheiro import ZERO, converter_valor, formatar_brl, percentual
from happy_green.dominio.entidade import Entidade
from happy_green.dominio.lancamentos import Lancamento
from happy_green.dominio.tempo import Competencia
from happy_green.excecoes import CategoriaIncompativelError, DadosInvalidosError, ValorInvalidoError


@dataclass(frozen=True)
class SituacaoOrcamento:
    """Fotografia do consumo de um orçamento (objeto de valor, imutável)."""

    limite: Decimal
    consumido: Decimal

    @property
    def disponivel(self) -> Decimal:
        return self.limite - self.consumido

    @property
    def percentual_consumido(self) -> Decimal:
        return percentual(self.consumido, self.limite)

    @property
    def ultrapassado(self) -> bool:
        return self.consumido > self.limite

    @property
    def excedente(self) -> Decimal:
        return max(self.consumido - self.limite, ZERO)

    @property
    def mensagem(self) -> str:
        if self.ultrapassado:
            return f"Limite ultrapassado em {formatar_brl(self.excedente)}."
        return f"Disponível: {formatar_brl(self.disponivel)}."


class OrcamentoMensal(Entidade):
    """Limite de gasto de uma categoria de despesa em uma competência (mês/ano).

    Associação: referencia uma Categoria que existe independentemente dele.
    Composição: contém uma Competencia, objeto de valor que só faz sentido
    como parte do orçamento (não tem identidade nem tabela própria).
    """

    def __init__(
        self,
        categoria: Categoria,
        competencia: Competencia,
        limite: str | int | Decimal,
        id: int | None = None,
    ) -> None:
        super().__init__(id)
        if not isinstance(categoria, Categoria):
            raise DadosInvalidosError("Selecione uma categoria válida.")
        if not categoria.aceita(TipoLancamento.DESPESA):
            raise CategoriaIncompativelError("Orçamentos só podem ser definidos para categorias de despesa.")
        if not isinstance(competencia, Competencia):
            raise DadosInvalidosError("Informe o mês do orçamento.")
        self._categoria = categoria
        self._competencia = competencia
        self.limite = limite

    @property
    def categoria(self) -> Categoria:
        return self._categoria

    @property
    def competencia(self) -> Competencia:
        return self._competencia

    @property
    def limite(self) -> Decimal:
        return self._limite

    @limite.setter
    def limite(self, valor: str | int | Decimal) -> None:
        limite = converter_valor(valor)
        if limite <= 0:
            raise ValorInvalidoError("O limite do orçamento deve ser maior que zero.")
        self._limite = limite

    def calcular_consumo(self, lancamentos: Iterable[Lancamento]) -> Decimal:
        """Soma o que foi gasto na categoria dentro da competência.

        Usa o método polimórfico: o impacto de uma despesa é negativo, então
        o consumo é o impacto com o sinal invertido.
        """
        return sum(
            (
                -lancamento.calcular_impacto_no_saldo()
                for lancamento in lancamentos
                if lancamento.categoria.mesma_entidade(self._categoria) and lancamento.ocorreu_em(self._competencia)
            ),
            ZERO,
        )

    def calcular_situacao(self, lancamentos: Iterable[Lancamento]) -> SituacaoOrcamento:
        return SituacaoOrcamento(limite=self._limite, consumido=self.calcular_consumo(lancamentos))

    def __repr__(self) -> str:
        return (
            f"OrcamentoMensal(id={self.id!r}, categoria={self._categoria.nome!r}, "
            f"competencia='{self._competencia}', limite={self._limite!r})"
        )
