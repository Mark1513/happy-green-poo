-- =====================================================================
-- Happy Green - 001: estrutura do banco (PostgreSQL / Supabase)
--
-- Como aplicar: Supabase > SQL Editor > cole este arquivo > Run.
-- O script é idempotente (IF NOT EXISTS): rodar de novo não apaga dados.
--
-- As tabelas ficam no schema "happy_green", que NÃO está na lista de
-- schemas expostos pela Data API do Supabase (Settings > API). O acesso é
-- feito somente pelo servidor Python, com um usuário próprio (ver 002).
--
-- Para o banco de TESTES de integração, rode este mesmo arquivo trocando
-- "happy_green" por "happy_green_teste" nas duas linhas abaixo.
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS happy_green;
SET search_path TO happy_green;

-- Contas financeiras. O saldo atual NÃO é guardado: é calculado a partir
-- do saldo inicial e dos lançamentos (evita dado redundante).
CREATE TABLE IF NOT EXISTS contas (
    id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome          varchar(60)    NOT NULL,
    saldo_inicial numeric(14, 2) NOT NULL DEFAULT 0,
    criado_em     timestamptz    NOT NULL DEFAULT now(),
    CONSTRAINT contas_nome_preenchido CHECK (btrim(nome) <> '')
);
CREATE UNIQUE INDEX IF NOT EXISTS contas_nome_unico ON contas (lower(nome));

-- Categorias de receita ou de despesa.
CREATE TABLE IF NOT EXISTS categorias (
    id        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome      varchar(60) NOT NULL,
    tipo      varchar(7)  NOT NULL,
    criado_em timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT categorias_nome_preenchido CHECK (btrim(nome) <> ''),
    CONSTRAINT categorias_tipo_valido CHECK (tipo IN ('receita', 'despesa')),
    -- Permite que lançamentos e orçamentos referenciem (id, tipo) e o banco
    -- garanta que a categoria é compatível com o tipo do lançamento.
    CONSTRAINT categorias_id_tipo_unico UNIQUE (id, tipo)
);
CREATE UNIQUE INDEX IF NOT EXISTS categorias_nome_tipo_unico ON categorias (lower(nome), tipo);

-- Receitas e despesas. "valor" é sempre positivo; o sinal é dado pelo tipo.
CREATE TABLE IF NOT EXISTS lancamentos (
    id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tipo         varchar(7)     NOT NULL,
    descricao    varchar(120)   NOT NULL,
    valor        numeric(14, 2) NOT NULL,
    data         date           NOT NULL,
    conta_id     bigint         NOT NULL,
    categoria_id bigint         NOT NULL,
    chave_envio  uuid,                      -- evita duplicação por reenvio de formulário
    criado_em    timestamptz    NOT NULL DEFAULT now(),
    CONSTRAINT lancamentos_tipo_valido CHECK (tipo IN ('receita', 'despesa')),
    CONSTRAINT lancamentos_descricao_preenchida CHECK (btrim(descricao) <> ''),
    CONSTRAINT lancamentos_valor_positivo CHECK (valor > 0),
    CONSTRAINT lancamentos_data_valida CHECK (data >= DATE '2000-01-01'),
    CONSTRAINT lancamentos_chave_envio_unica UNIQUE (chave_envio),
    CONSTRAINT lancamentos_conta_fk FOREIGN KEY (conta_id)
        REFERENCES contas (id) ON DELETE RESTRICT,
    CONSTRAINT lancamentos_categoria_fk FOREIGN KEY (categoria_id, tipo)
        REFERENCES categorias (id, tipo) ON DELETE RESTRICT ON UPDATE RESTRICT
);
CREATE INDEX IF NOT EXISTS lancamentos_data_idx ON lancamentos (data);
CREATE INDEX IF NOT EXISTS lancamentos_conta_idx ON lancamentos (conta_id);
CREATE INDEX IF NOT EXISTS lancamentos_categoria_idx ON lancamentos (categoria_id);

-- Orçamento mensal: um por categoria de DESPESA e mês.
CREATE TABLE IF NOT EXISTS orcamentos (
    id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    categoria_id   bigint         NOT NULL,
    tipo_categoria varchar(7)     NOT NULL DEFAULT 'despesa',
    competencia    date           NOT NULL,  -- sempre o dia 1 do mês
    limite         numeric(14, 2) NOT NULL,
    criado_em      timestamptz    NOT NULL DEFAULT now(),
    CONSTRAINT orcamentos_somente_despesa CHECK (tipo_categoria = 'despesa'),
    CONSTRAINT orcamentos_competencia_primeiro_dia CHECK (extract(day FROM competencia) = 1),
    CONSTRAINT orcamentos_limite_positivo CHECK (limite > 0),
    CONSTRAINT orcamentos_categoria_competencia_unico UNIQUE (categoria_id, competencia),
    CONSTRAINT orcamentos_categoria_fk FOREIGN KEY (categoria_id, tipo_categoria)
        REFERENCES categorias (id, tipo) ON DELETE RESTRICT ON UPDATE RESTRICT
);
