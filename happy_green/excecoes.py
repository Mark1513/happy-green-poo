"""Exceções do Happy Green.

A hierarquia permite que a interface trate todos os erros esperados com um
único ``except ErroHappyGreen`` e mostre a mensagem ao usuário, enquanto
detalhes técnicos ficam apenas nos registros (logs).
"""


class ErroHappyGreen(Exception):
    """Base de todos os erros previstos pela aplicação."""

    def __init__(self, mensagem: str) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem


# ---------------------------------------------------------------- domínio
class ErroDominio(ErroHappyGreen):
    """Uma regra de negócio foi violada."""


class DadosInvalidosError(ErroDominio):
    """Campo obrigatório ausente, texto grande demais, data inválida etc."""


class ValorInvalidoError(DadosInvalidosError):
    """Valor monetário inválido (formato, casas decimais, sinal ou tamanho)."""


class CategoriaIncompativelError(ErroDominio):
    """Categoria de receita usada em despesa (ou vice-versa)."""


class RegistroNaoEncontradoError(ErroDominio):
    """O registro procurado não existe (pode ter sido excluído por outro visitante)."""


class RegistroDuplicadoError(ErroDominio):
    """Violação de unicidade (ex.: dois orçamentos para a mesma categoria e mês)."""


class ExclusaoNaoPermitidaError(ErroDominio):
    """A exclusão deixaria referências inválidas (ex.: conta com lançamentos)."""


# ---------------------------------------------------------- infraestrutura
class ErroInfraestrutura(ErroHappyGreen):
    """Falha técnica (banco indisponível, tempo esgotado, configuração ausente)."""
