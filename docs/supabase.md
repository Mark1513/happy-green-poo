# Configuração do Supabase (PostgreSQL)

## Visão geral

| Item | Escolha | Motivo |
|---|---|---|
| Conexão | **Session pooler** (Supavisor), porta 5432 | O Streamlit Community Cloud só tem IPv4. A conexão direta do Supabase é IPv6 no plano gratuito; o pooler é IPv4 em todos os planos. O modo sessão mantém o `SET search_path` e aceita prepared statements. |
| Criptografia | `sslmode=require` | O driver recusa conectar sem TLS. (`verify-full` com o certificado raiz do Supabase é uma melhoria possível.) |
| Schema | `happy_green` | Não está na lista de schemas da Data API (Settings > API > Exposed schemas), então não é acessível pela API REST pública. Os papéis `anon` e `authenticated` não têm permissão nele. |
| Usuário | `happy_green_app` | Menor privilégio: só SELECT/INSERT/UPDATE/DELETE nas tabelas do Happy Green. Não usa o usuário `postgres`. |
| Testes | schema `happy_green_teste` | Dados de teste separados da demonstração. |

## Passo a passo (projeto novo)

1. Crie um projeto em <https://supabase.com/dashboard> (plano Free) e guarde a senha do banco.
2. **SQL Editor** > cole `sql/001_estrutura.sql` > **Run**.
   Para os testes de integração, rode de novo trocando `happy_green` por `happy_green_teste` nas duas primeiras linhas.
3. **SQL Editor** > cole `sql/002_usuario_aplicacao.sql`, troque `TROQUE_POR_UMA_SENHA_FORTE` por uma senha longa (só letras e números evita problemas de codificação) > **Run**. Não salve a senha no arquivo.
4. Clique em **Connect** (topo do painel) > **Session pooler** e copie o **host** (formato `aws-N-REGIAO.pooler.supabase.com`; o número N não pode ser deduzido, copie do painel).
5. Copie `.streamlit/secrets.example.toml` para `.streamlit/secrets.toml` e preencha:
   - `host`: o host copiado; `port = 5432`; `dbname = "postgres"`;
   - `user = "happy_green_app.<ref-do-projeto>"` (no pooler o usuário leva o ref do projeto);
   - `password`: a senha do passo 3.
6. Carga de demonstração (opcional, uma vez): `python scripts/carregar_demo.py`
   (ou cole `sql/003_dados_demonstracao.sql` no SQL Editor). Se a base já tiver dados, nada é alterado.

## Neste projeto (o que foi feito de fato)

- Projeto Supabase: "Mark1513's Project", região `us-east-1`, Postgres 17.
- Migrações aplicadas: `happy_green_001_estrutura` (schemas `happy_green` e `happy_green_teste`) e `happy_green_002_usuario_aplicacao`.
- Host do Session pooler que respondeu: `aws-0-us-east-1.pooler.supabase.com` (o `aws-1` recusou com "tenant/user not found").
- Consultor de segurança do Supabase (Advisors > Security): **nenhum alerta** após as migrações.
- Carga de demonstração: 3 contas, 9 categorias, 21 lançamentos e 6 orçamentos; a segunda execução foi ignorada (sem duplicar).

## Limitações do plano gratuito

- O projeto é **pausado após 7 dias com pouca atividade** (o Supabase avisa por e-mail antes). Os dados são preservados e o projeto pode ser restaurado no painel. **Antes da apresentação**, abra o app ou o painel do Supabase nos dias anteriores.
- 500 MB de banco, CPU compartilhada. Suficiente para a demonstração.
- Fonte: [Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing) e [Pricing](https://supabase.com/pricing).

## Atualizar a estrutura no futuro

Crie um novo arquivo numerado (ex.: `sql/004_...sql`) com `ALTER TABLE ...`, versione no Git e aplique no SQL Editor. Nunca edite um script já aplicado para mudar a estrutura existente.
