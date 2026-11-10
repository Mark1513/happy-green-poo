"""Contratos (classes abstratas) dos repositórios e o filtro de lançamentos.

Os serviços dependem destes contratos, e não do PostgreSQL. Assim:
- a aplicação usa ``repositorios.postgres`` (persistência real);
- os testes de serviço usam implementações em memória (``tests/fakes.py``).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from happy_green.dominio import (
    Categoria,
    Competencia,
    ContaFinanceira,
    Lancamento,
    OrcamentoMensal,
    TipoLancamento,
)
from happy_green.excecoes import DadosInvalidosError


@dataclass(frozen=True)
class FiltroLancamentos:
    """Critérios de consulta de lançamentos. ``None`` significa "todos"."""

    data_inicio: date | None = None
    data_fim: date | None = None
    conta_id: int | None = None
    categoria_id: int | None = None
    tipo: TipoLancamento | None = None

    def __post_init__(self) -> None:
        if self.data_inicio and self.data_fim and self.data_inicio > self.data_fim:
            raise DadosInvalidosError("A data inicial não pode ser posterior à data final.")

    def aceita(self, lancamento: Lancamento) -> bool:
        """Versão em Python do filtro (usada pelos repositórios em memória)."""
        return (
            (self.data_inicio is None or lancamento.data >= self.data_inicio)
            and (self.data_fim is None or lancamento.data <= self.data_fim)
            and (self.conta_id is None or lancamento.conta.id == self.conta_id)
            and (self.categoria_id is None or lancamento.categoria.id == self.categoria_id)
            and (self.tipo is None or lancamento.tipo is self.tipo)
        )


class RepositorioContas(ABC):
    @abstractmethod
    def listar(self) -> list[ContaFinanceira]: ...

    @abstractmethod
    def obter(self, id: int) -> ContaFinanceira:
        """Retorna a conta ou lança RegistroNaoEncontradoError."""

    @abstractmethod
    def adicionar(self, conta: ContaFinanceira) -> ContaFinanceira: ...

    @abstractmethod
    def atualizar(self, conta: ContaFinanceira) -> None: ...

    @abstractmethod
    def remover(self, id: int) -> None: ...


class RepositorioCategorias(ABC):
    @abstractmethod
    def listar(self, tipo: TipoLancamento | None = None) -> list[Categoria]: ...

    @abstractmethod
    def obter(self, id: int) -> Categoria: ...

    @abstractmethod
    def adicionar(self, categoria: Categoria) -> Categoria: ...

    @abstractmethod
    def atualizar(self, categoria: Categoria) -> None: ...

    @abstractmethod
    def remover(self, id: int) -> None: ...

    @abstractmethod
    def em_uso(self, id: int) -> bool:
        """True se houver lançamentos ou orçamentos usando a categoria."""


class RepositorioLancamentos(ABC):
    @abstractmethod
    def listar(self, filtro: FiltroLancamentos | None = None) -> list[Lancamento]: ...

    @abstractmethod
    def obter(self, id: int) -> Lancamento: ...

    @abstractmethod
    def adicionar(self, lancamento: Lancamento, chave_envio: UUID | None = None) -> Lancamento:
        """Grava o lançamento. Se a mesma ``chave_envio`` já foi gravada
        (formulário reenviado), devolve o lançamento existente sem duplicar."""

    @abstractmethod
    def atualizar(self, lancamento: Lancamento) -> None: ...

    @abstractmethod
    def remover(self, id: int) -> None: ...

    @abstractmethod
    def existe_para_conta(self, conta_id: int) -> bool: ...


class RepositorioOrcamentos(ABC):
    @abstractmethod
    def listar(self, competencia: Competencia | None = None) -> list[OrcamentoMensal]: ...

    @abstractmethod
    def obter(self, id: int) -> OrcamentoMensal: ...

    @abstractmethod
    def adicionar(self, orcamento: OrcamentoMensal) -> OrcamentoMensal: ...

    @abstractmethod
    def atualizar(self, orcamento: OrcamentoMensal) -> None: ...

    @abstractmethod
    def remover(self, id: int) -> None: ...

    @abstractmethod
    def existe(self, categoria_id: int, competencia: Competencia) -> bool: ...
