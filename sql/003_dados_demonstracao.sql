-- =====================================================================
-- Happy Green - 003: carga de dados FICTÍCIOS para a demonstração
--
-- Procedimento explícito: rode quando quiser povoar uma base vazia.
--   Opção A: python scripts/carregar_demo.py
--   Opção B: Supabase > SQL Editor > cole este arquivo > Run.
--
-- Sem duplicações: se já existir qualquer conta ou categoria, NADA é feito.
-- Tudo roda em um único bloco (transação): ou carrega tudo, ou nada.
-- As datas são relativas ao mês atual (horário de Brasília), para que o
-- painel tenha dados no dia da apresentação. Nenhuma data fica no futuro.
-- =====================================================================

SET search_path TO happy_green;

DO $$
DECLARE
    hoje       date := (now() AT TIME ZONE 'America/Sao_Paulo')::date;
    mes        date := date_trunc('month', (now() AT TIME ZONE 'America/Sao_Paulo'))::date;
    anterior   date := (date_trunc('month', (now() AT TIME ZONE 'America/Sao_Paulo')) - interval '1 month')::date;
    c_corrente bigint; c_carteira bigint; c_poupanca bigint;
    k_salario  bigint; k_freela bigint; k_rendimento bigint;
    k_alimentacao bigint; k_transporte bigint; k_moradia bigint;
    k_lazer bigint; k_saude bigint; k_educacao bigint;
BEGIN
    IF EXISTS (SELECT 1 FROM contas) OR EXISTS (SELECT 1 FROM categorias) THEN
        RAISE NOTICE 'A base já possui dados: carga de demonstração ignorada (nada foi alterado).';
        RETURN;
    END IF;

    INSERT INTO contas (nome, saldo_inicial) VALUES ('Conta Corrente', 2500.00) RETURNING id INTO c_corrente;
    INSERT INTO contas (nome, saldo_inicial) VALUES ('Carteira', 150.00)      RETURNING id INTO c_carteira;
    INSERT INTO contas (nome, saldo_inicial) VALUES ('Poupança', 5000.00)     RETURNING id INTO c_poupanca;

    INSERT INTO categorias (nome, tipo) VALUES ('Salário', 'receita')     RETURNING id INTO k_salario;
    INSERT INTO categorias (nome, tipo) VALUES ('Freelance', 'receita')   RETURNING id INTO k_freela;
    INSERT INTO categorias (nome, tipo) VALUES ('Rendimentos', 'receita') RETURNING id INTO k_rendimento;
    INSERT INTO categorias (nome, tipo) VALUES ('Alimentação', 'despesa') RETURNING id INTO k_alimentacao;
    INSERT INTO categorias (nome, tipo) VALUES ('Transporte', 'despesa')  RETURNING id INTO k_transporte;
    INSERT INTO categorias (nome, tipo) VALUES ('Moradia', 'despesa')     RETURNING id INTO k_moradia;
    INSERT INTO categorias (nome, tipo) VALUES ('Lazer', 'despesa')       RETURNING id INTO k_lazer;
    INSERT INTO categorias (nome, tipo) VALUES ('Saúde', 'despesa')       RETURNING id INTO k_saude;
    INSERT INTO categorias (nome, tipo) VALUES ('Educação', 'despesa')    RETURNING id INTO k_educacao;

    -- Mês anterior (completo)
    INSERT INTO lancamentos (tipo, descricao, valor, data, conta_id, categoria_id) VALUES
        ('receita', 'Salário (fictício)',         4200.00, anterior + 4,  c_corrente, k_salario),
        ('receita', 'Projeto de site (fictício)',  800.00, anterior + 17, c_corrente, k_freela),
        ('receita', 'Rendimento da poupança',       32.50, anterior + 27, c_poupanca, k_rendimento),
        ('despesa', 'Aluguel',                    1300.00, anterior + 9,  c_corrente, k_moradia),
        ('despesa', 'Conta de energia',            145.90, anterior + 11, c_corrente, k_moradia),
        ('despesa', 'Supermercado',                512.37, anterior + 6,  c_corrente, k_alimentacao),
        ('despesa', 'Feira',                        86.40, anterior + 13, c_carteira, k_alimentacao),
        ('despesa', 'Restaurante',                 142.00, anterior + 20, c_corrente, k_alimentacao),
        ('despesa', 'Cartão de transporte',        180.00, anterior + 2,  c_corrente, k_transporte),
        ('despesa', 'Cinema',                       64.00, anterior + 15, c_carteira, k_lazer),
        ('despesa', 'Farmácia',                     73.25, anterior + 18, c_corrente, k_saude),
        ('despesa', 'Curso online',                 99.90, anterior + 7,  c_corrente, k_educacao);

    -- Mês atual (até hoje)
    INSERT INTO lancamentos (tipo, descricao, valor, data, conta_id, categoria_id) VALUES
        ('receita', 'Salário (fictício)',         4200.00, LEAST(mes + 4,  hoje), c_corrente, k_salario),
        ('receita', 'Revisão de texto (fictício)', 350.00, LEAST(mes + 12, hoje), c_corrente, k_freela),
        ('despesa', 'Aluguel',                    1300.00, LEAST(mes + 9,  hoje), c_corrente, k_moradia),
        ('despesa', 'Supermercado',                468.90, LEAST(mes + 5,  hoje), c_corrente, k_alimentacao),
        ('despesa', 'Padaria',                      38.60, LEAST(mes + 8,  hoje), c_carteira, k_alimentacao),
        ('despesa', 'Aplicativo de transporte',     57.80, LEAST(mes + 6,  hoje), c_corrente, k_transporte),
        ('despesa', 'Cartão de transporte',        180.00, LEAST(mes + 2,  hoje), c_corrente, k_transporte),
        ('despesa', 'Show',                        180.00, LEAST(mes + 7,  hoje), c_corrente, k_lazer),
        ('despesa', 'Consulta',                    150.00, LEAST(mes + 3,  hoje), c_corrente, k_saude);

    -- Orçamentos (Lazer do mês atual propositalmente ultrapassado)
    INSERT INTO orcamentos (categoria_id, competencia, limite) VALUES
        (k_alimentacao, anterior, 800.00),
        (k_lazer,       anterior, 150.00),
        (k_alimentacao, mes,      800.00),
        (k_transporte,  mes,      300.00),
        (k_lazer,       mes,      150.00),
        (k_moradia,     mes,     1600.00);

    RAISE NOTICE 'Carga de demonstração concluída.';
END
$$;
