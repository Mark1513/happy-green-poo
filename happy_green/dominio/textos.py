"""Validação de textos obrigatórios, compartilhada pelas entidades."""

from happy_green.excecoes import DadosInvalidosError


def validar_texto(valor: object, campo: str, tamanho_maximo: int) -> str:
    """Remove espaços das pontas e exige um texto não vazio e não muito longo."""
    if not isinstance(valor, str) or not valor.strip():
        raise DadosInvalidosError(f"O campo {campo} é obrigatório.")
    texto = " ".join(valor.split())  # também reduz espaços repetidos no meio
    if len(texto) > tamanho_maximo:
        raise DadosInvalidosError(f"O campo {campo} aceita no máximo {tamanho_maximo} caracteres.")
    return texto
