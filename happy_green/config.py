"""Configuração: leitura dos segredos e criação do pool de conexões.

Os segredos vêm de ``st.secrets`` (arquivo local ``.streamlit/secrets.toml``
ou painel de Secrets do Streamlit Community Cloud). Nada aqui grava ou exibe
a senha: ``ConfiguracaoBanco`` a omite do ``repr`` e dos logs.
"""

import logging
import re
from collections.abc import Mapping
from dataclasses import dataclass, field

from psycopg import sql
from psycopg_pool import ConnectionPool

from happy_green.excecoes import ErroInfraestrutura

log = logging.getLogger("happy_green.config")

_NOME_SCHEMA = re.compile(r"[a-z_][a-z0-9_]{0,62}")


@dataclass(frozen=True)
class ConfiguracaoBanco:
    host: str
    porta: int
    banco: str
    usuario: str
    senha: str = field(repr=False)  # nunca aparece em mensagens ou logs
    schema: str = "happy_green"
    sslmode: str = "require"  # exige conexão criptografada

    CAMPOS_OBRIGATORIOS = ("host", "port", "dbname", "user", "password")

    @classmethod
    def de_mapeamento(cls, dados: Mapping) -> "ConfiguracaoBanco":
        faltando = [campo for campo in cls.CAMPOS_OBRIGATORIOS if not dados.get(campo)]
        if faltando:
            raise ErroInfraestrutura(
                "Configuração do banco incompleta. Campos ausentes nos Secrets: " + ", ".join(faltando)
            )
        schema = str(dados.get("schema", "happy_green"))
        if not _NOME_SCHEMA.fullmatch(schema):
            raise ErroInfraestrutura("Nome de schema inválido na configuração.")
        sslmode = str(dados.get("sslmode", "require"))
        if sslmode not in ("require", "verify-ca", "verify-full"):
            raise ErroInfraestrutura("Use sslmode require, verify-ca ou verify-full (conexão criptografada).")
        return cls(
            host=str(dados["host"]),
            porta=int(dados["port"]),
            banco=str(dados["dbname"]),
            usuario=str(dados["user"]),
            senha=str(dados["password"]),
            schema=schema,
            sslmode=sslmode,
        )

    def parametros_conexao(self) -> dict:
        return {
            "host": self.host,
            "port": self.porta,
            "dbname": self.banco,
            "user": self.usuario,
            "password": self.senha,
            "sslmode": self.sslmode,
            "connect_timeout": 10,
            "application_name": "happy-green",
        }


def criar_pool(config: ConfiguracaoBanco, tamanho_maximo: int = 4) -> ConnectionPool:
    """Cria um pool de conexões compartilhado pelas sessões do Streamlit.

    - Cada conexão é emprestada a uma operação e devolvida ao fim dela, então
      vários visitantes podem usar a aplicação ao mesmo tempo.
    - ``check`` testa a conexão antes de entregá-la (o pooler pode fechar
      conexões ociosas).
    - ``configure`` define o schema da aplicação em cada nova conexão.
    """

    def configurar(conexao) -> None:
        conexao.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(config.schema)))
        conexao.commit()

    log.info("Criando pool de conexões (host=%s, schema=%s)", config.host, config.schema)
    return ConnectionPool(
        kwargs=config.parametros_conexao(),
        min_size=1,
        max_size=tamanho_maximo,
        timeout=20,
        max_idle=300,
        configure=configurar,
        check=ConnectionPool.check_connection,
        name="happy-green",
        open=True,
    )


def ler_configuracao_streamlit(secao: str = "banco") -> ConfiguracaoBanco:
    """Lê a seção ``[banco]`` de ``st.secrets``."""
    import streamlit as st  # importado aqui para o resto do pacote não depender do Streamlit

    try:
        dados = st.secrets[secao]
    except (KeyError, FileNotFoundError) as erro:
        raise ErroInfraestrutura(
            f"Seção [{secao}] não encontrada nos Secrets. Veja .streamlit/secrets.example.toml."
        ) from erro
    return ConfiguracaoBanco.de_mapeamento(dados)


def ler_configuracao_arquivo(caminho: str = ".streamlit/secrets.toml", secao: str = "banco") -> ConfiguracaoBanco:
    """Lê os mesmos segredos sem Streamlit (scripts e testes de integração)."""
    import tomllib

    try:
        with open(caminho, "rb") as arquivo:
            dados = tomllib.load(arquivo)
    except FileNotFoundError as erro:
        raise ErroInfraestrutura(f"Arquivo {caminho} não encontrado.") from erro
    if secao not in dados:
        raise ErroInfraestrutura(f"Seção [{secao}] não encontrada em {caminho}.")
    return ConfiguracaoBanco.de_mapeamento(dados[secao])
