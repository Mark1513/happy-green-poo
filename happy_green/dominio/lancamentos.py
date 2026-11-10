"""Lançamentos financeiros: abstração, herança e polimorfismo."""

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from happy_green.dominio.categorias import Categoria, TipoLancamento
from happy_green.dominio.contas import ContaFinanceira
from happy_green.dominio.dinheiro import converter_valor, formatar_brl
from happy_green.dominio.entidade import Entidade
from happy_green.dominio.tempo import Competencia, validar_data
from happy_green.dominio.textos import validar_texto
from happy_green.excecoes import CategoriaIncompativelError, DadosInvalidosError, ValorInvalidoError


class Lancamento(Entidade, ABC):
    """Classe abstrata: não existe "lançamento genérico", só Receita ou Despesa.

    O valor é sempre estritamente positivo. Quem decide se ele aumenta ou
    diminui o saldo é o método polimórfico ``calcular_impacto_no_saldo()``.
    """

    TAMANHO_MAXIMO_DESCRICAO = 120

    def __init__(
        self,
        descricao: str,
        valor: str | int | Decimal,
        data: date,
        conta: ContaFinanceira,
        categoria: Categoria,
        id: int | None = None,
    ) -> None:
        super().__init__(id)
        self._validar_e_atribuir(descricao, valor, data, conta, categoria)

    # ------------------------------------------------------ contrato abstrato
    @property
    @abstractmethod
    def tipo(self) -> TipoLancamento:
        """Tipo do lançamento; usado para validar a categoria."""

    @abstractmethod
    def calcular_impacto_no_saldo(self) -> Decimal:
        """Quanto este lançamento soma (+) ou subtrai (-) do saldo da conta."""

    # ------------------------------------------------- leitura (encapsulada)
    @property
    def descricao(self) -> str:
        return self._descricao

    @property
    def valor(self) -> Decimal:
        return self._valor

    @property
    def data(self) -> date:
        return self._data

    @property
    def conta(self) -> ContaFinanceira:
        return self._conta

    @property
    def categoria(self) -> Categoria:
        return self._categoria

    # ---------------------------------------------------------- comportamento
    def editar(
        self,
        *,
        descricao: str,
        valor: str | int | Decimal,
        data: date,
        conta: ContaFinanceira,
        categoria: Categoria,
    ) -> None:
        """Altera os dados de forma atômica: ou tudo é válido e muda, ou nada muda."""
        self._validar_e_atribuir(descricao, valor, data, conta, categoria)

    def pertence_a(self, conta: ContaFinanceira) -> bool:
        return self._conta.mesma_entidade(conta)

    def ocorreu_em(self, competencia: Competencia) -> bool:
        return competencia.contem(self._data)

    def _validar_e_atribuir(self, descricao, valor, data, conta, categoria) -> None:
        # 1) Valida tudo em variáveis locais...
        descricao_valida = validar_texto(descricao, "descrição", self.TAMANHO_MAXIMO_DESCRICAO)
        valor_valido = converter_valor(valor)
        if valor_valido <= 0:
            raise ValorInvalidoError("O valor deve ser maior que zero.")
        data_valida = validar_data(data)
        if not isinstance(conta, ContaFinanceira):
            raise DadosInvalidosError("Selecione uma conta válida.")
        if not isinstance(categoria, Categoria):
            raise DadosInvalidosError("Selecione uma categoria válida.")
        if not categoria.aceita(self.tipo):
            raise CategoriaIncompativelError(
                f"A categoria '{categoria.nome}' é de {categoria.tipo.value} "
                f"e não pode ser usada em uma {self.tipo.value}."
            )
        # 2) ...e só então altera o objeto, preservando as invariantes.
        self._descricao = descricao_valida
        self._valor = valor_valido
        self._data = data_valida
        self._conta = conta
        self._categoria = categoria

    def __str__(self) -> str:
        return f"{self._data:%d/%m/%Y} {self.tipo.rotulo}: {self._descricao} ({formatar_brl(self._valor)})"

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id!r}, descricao={self._descricao!r}, valor={self._valor!r})"


class Receita(Lancamento):
    """Entrada de dinheiro: aumenta o saldo."""

    @property
    def tipo(self) -> TipoLancamento:
        return TipoLancamento.RECEITA

    def calcular_impacto_no_saldo(self) -> Decimal:  # sobrescrita
        return self.valor


class Despesa(Lancamento):
    """Saída de dinheiro: diminui o saldo."""

    @property
    def tipo(self) -> TipoLancamento:
        return TipoLancamento.DESPESA

    def calcular_impacto_no_saldo(self) -> Decimal:  # sobrescrita
        return -self.valor


# Fábrica: escolhe a subclasse por um dicionário (sem cadeia de if/elif).
CLASSES_DE_LANCAMENTO: dict[TipoLancamento, type[Lancamento]] = {
    TipoLancamento.RECEITA: Receita,
    TipoLancamento.DESPESA: Despesa,
}


def criar_lancamento(tipo: TipoLancamento | str, **dados) -> Lancamento:
    """Cria (ou reconstrói, a partir do banco) a subclasse correta de Lancamento."""
    classe = CLASSES_DE_LANCAMENTO[TipoLancamento.converter(tipo)]
    return classe(**dados)
