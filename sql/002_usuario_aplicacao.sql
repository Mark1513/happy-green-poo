-- =====================================================================
-- Happy Green - 002: usuário do banco usado pela aplicação
--
-- Princípio do menor privilégio: a aplicação NÃO usa o usuário "postgres".
-- O usuário happy_green_app só lê e grava dados nas tabelas do Happy Green;
-- ele não consegue apagar tabelas nem acessar outros schemas.
--
-- Como aplicar (SQL Editor do Supabase), uma única vez:
--   1. Troque TROQUE_POR_UMA_SENHA_FORTE por uma senha longa e aleatória.
--   2. Execute. 3. NÃO salve a senha real neste arquivo nem no Git.
--   4. Coloque a senha em .streamlit/secrets.toml e nos Secrets da hospedagem.
-- Para trocar a senha depois: ALTER ROLE happy_green_app PASSWORD '...';
-- =====================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'happy_green_app') THEN
        CREATE ROLE happy_green_app LOGIN PASSWORD 'TROQUE_POR_UMA_SENHA_FORTE' CONNECTION LIMIT 20;
    END IF;
END
$$;

-- Dados da demonstração
GRANT USAGE ON SCHEMA happy_green TO happy_green_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA happy_green TO happy_green_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA happy_green TO happy_green_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA happy_green
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO happy_green_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA happy_green
    GRANT USAGE, SELECT ON SEQUENCES TO happy_green_app;

-- Dados de TESTES de integração (schema separado; TRUNCATE permitido só aqui).
-- Rode somente depois de criar o schema happy_green_teste com o 001.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'happy_green_teste') THEN
        GRANT USAGE ON SCHEMA happy_green_teste TO happy_green_app;
        GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA happy_green_teste TO happy_green_app;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA happy_green_teste TO happy_green_app;
    END IF;
END
$$;

-- Garante que os papéis públicos da Data API não acessam o schema.
REVOKE ALL ON SCHEMA happy_green FROM anon, authenticated;
REVOKE ALL ON ALL TABLES IN SCHEMA happy_green FROM anon, authenticated;
