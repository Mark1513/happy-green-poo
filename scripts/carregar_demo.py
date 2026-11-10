"""Carrega os dados fictícios de demonstração (sql/003_dados_demonstracao.sql).

Uso (na raiz do projeto, com .streamlit/secrets.toml preenchido):

    python scripts/carregar_demo.py

É seguro rodar mais de uma vez: se a base já tiver dados, nada é alterado.
A aplicação NUNCA executa esta carga sozinha.
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import psycopg  # noqa: E402

from happy_green.config import ler_configuracao_arquivo  # noqa: E402


def main() -> None:
    config = ler_configuracao_arquivo(str(RAIZ / ".streamlit" / "secrets.toml"), secao="banco")
    script = (RAIZ / "sql" / "003_dados_demonstracao.sql").read_text(encoding="utf-8")
    script = script.replace("SET search_path TO happy_green;", "")  # o schema vem da configuração
    with psycopg.connect(**config.parametros_conexao()) as conexao:
        conexao.add_notice_handler(lambda aviso: print("Banco:", aviso.message_primary))
        conexao.execute(psycopg.sql.SQL("SET search_path TO {}").format(psycopg.sql.Identifier(config.schema)))
        conexao.execute(script)
    print(f"Pronto (schema {config.schema}).")


if __name__ == "__main__":
    main()
