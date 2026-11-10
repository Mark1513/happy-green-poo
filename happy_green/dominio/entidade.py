"""Classe base das entidades (objetos com identidade própria)."""

from happy_green.excecoes import DadosInvalidosError


class Entidade:
    """Superclasse de conta, categoria, lançamento e orçamento.

    Centraliza a regra do identificador: ele é atribuído pelo banco uma única
    vez e, depois disso, não pode ser trocado (invariante protegida).
    """

    def __init__(self, id: int | None = None) -> None:
        self._id: int | None = None
        if id is not None:
            self.atribuir_id(id)

    @property
    def id(self) -> int | None:
        return self._id

    def atribuir_id(self, id: int) -> None:
        if isinstance(id, bool) or not isinstance(id, int) or id <= 0:
            raise DadosInvalidosError("Identificador inválido.")
        if self._id is not None and self._id != id:
            raise DadosInvalidosError("O identificador de um registro não pode ser alterado.")
        self._id = id

    def mesma_entidade(self, outra: "Entidade") -> bool:
        """Compara identidades: pelo id quando existe, senão pelo próprio objeto.

        Objetos lidos do banco em consultas diferentes são instâncias distintas,
        mas representam o mesmo registro se tiverem o mesmo id.
        """
        if not isinstance(outra, Entidade):
            return False
        if self._id is not None and outra.id is not None:
            return self._id == outra.id and self._familia() is outra._familia()
        return self is outra

    def chave(self) -> tuple:
        """Chave usada para agrupar entidades em dicionários."""
        return ("id", self._id) if self._id is not None else ("objeto", id(self))

    def _familia(self) -> type:
        """Primeira classe abaixo de Entidade (Receita e Despesa são da família Lancamento)."""
        for classe in type(self).__mro__:
            if Entidade in classe.__bases__:
                return classe
        return type(self)  # pragma: no cover
