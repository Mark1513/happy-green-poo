"""Tipos de lançamento e categorias."""

from enum import Enum

from happy_green.dominio.entidade import Entidade
from happy_green.dominio.textos import validar_texto
from happy_green.excecoes import DadosInvalidosError


class TipoLancamento(Enum):
    """Natureza de um lançamento ou de uma categoria."""

    RECEITA = "receita"
    DESPESA = "despesa"

    @property
    def rotulo(self) -> str:
        return self.value.capitalize()

    @classmethod
    def converter(cls, valor: "TipoLancamento | str") -> "TipoLancamento":
        try:
            return valor if isinstance(valor, cls) else cls(str(valor).strip().lower())
        except ValueError as erro:
            raise DadosInvalidosError("Tipo inválido: use receita ou despesa.") from erro


class Categoria(Entidade):
    """Classifica lançamentos (ex.: Salário é receita; Alimentação é despesa)."""

    TAMANHO_MAXIMO_NOME = 60

    def __init__(self, nome: str, tipo: TipoLancamento | str, id: int | None = None) -> None:
        super().__init__(id)
        self.nome = nome  # passa pelo setter, que valida
        self._tipo = TipoLancamento.converter(tipo)

    @property
    def nome(self) -> str:
        return self._nome

    @nome.setter
    def nome(self, valor: str) -> None:
        self._nome = validar_texto(valor, "nome da categoria", self.TAMANHO_MAXIMO_NOME)

    @property
    def tipo(self) -> TipoLancamento:
        return self._tipo

    def alterar_tipo(self, novo_tipo: TipoLancamento | str) -> None:
        """Muda o tipo. O serviço só permite isso quando a categoria não está em uso."""
        self._tipo = TipoLancamento.converter(novo_tipo)

    def aceita(self, tipo: TipoLancamento) -> bool:
        """Uma categoria só aceita lançamentos do mesmo tipo."""
        return self._tipo is tipo

    def __str__(self) -> str:
        return self._nome

    def __repr__(self) -> str:
        return f"Categoria(id={self.id!r}, nome={self._nome!r}, tipo={self._tipo.value!r})"
