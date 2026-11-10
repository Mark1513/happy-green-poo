# Evidências (resultados observados)

Este arquivo registra apenas o que foi **executado e observado**. Resultados
esperados ficam no roteiro e nos testes; aqui só entram saídas reais.

## 1. Testes automatizados — 10/11/2026

| Execução | Resultado observado | Arquivo com a saída completa |
|---|---|---|
| `pytest -v` (domínio, serviços, interface; sem banco) | **93 passed**, 6 deselected em 6,56 s | [`evidencias/testes_unitarios_e_interface.txt`](evidencias/testes_unitarios_e_interface.txt) |
| `pytest -m integracao -v` (Supabase, schema `happy_green_teste`) | **6 passed** em 59,80 s | [`evidencias/testes_integracao_supabase.txt`](evidencias/testes_integracao_supabase.txt) |

Ambiente: Windows 11, Python 3.12.10, streamlit 1.66.1, psycopg 3.3.6, psycopg-pool 3.3.3, pytest 9.2.0.

O cenário do enunciado roda em dois testes:
- `tests/test_servicos.py::test_cenario_do_enunciado` (repositórios em memória);
- `tests/test_integracao_postgres.py::test_cenario_completo_com_persistencia_e_reinicio`
  (PostgreSQL real: 1.080,00 → aviso de orçamento → 1.050,00 → 1.350,00, e depois
  fecha todas as conexões, cria um pool novo e confere que os dados e os tipos
  `Receita`/`Despesa` continuam lá).

## 2. Banco de dados (Supabase)

| Verificação | Resultado observado |
|---|---|
| Conexão pelo Session pooler `aws-0-us-east-1.pooler.supabase.com:5432` com o usuário `happy_green_app` | Conectou; `current_user = happy_green_app`, PostgreSQL 17.11 |
| Conexão criptografada | `pgconn.ssl_in_use = True` (teste `test_conexao_criptografada`) |
| Consultor de segurança do Supabase após as migrações | Nenhum alerta |
| Carga de demonstração, 1ª execução | "Carga de demonstração concluída." → 3 contas, 9 categorias, 21 lançamentos, 6 orçamentos |
| Carga de demonstração, 2ª execução | "A base já possui dados: carga de demonstração ignorada" (sem duplicar) |

## 3. Execução local no navegador (antes da publicação)

`streamlit run streamlit_app.py` com o banco real:

- Painel em 10/11/2026: saldo total **R$ 12.253,38**, receitas do mês R$ 4.550,00, despesas do mês R$ 2.375,30, resultado R$ 2.174,70. Conferido à mão com os dados de `sql/003` (saldos iniciais 7.650,00 + mês anterior 5.032,50 − 2.603,82 + mês atual 4.550,00 − 2.375,30).
- Aviso de orçamento: "Orçamento de Lazer ultrapassado: gasto de R$ 180,00 para um limite de R$ 150,00 (R$ 30,00 acima)."
- Orçamentos: Alimentação 63,4%, Lazer 120,0% com aviso, Moradia 81,3%, Transporte 79,3%.
- Problemas encontrados e corrigidos nesta verificação: o "R$" virava fórmula no Markdown (corrigido escapando o cifrão) e os 4 indicadores ficavam cortados em telas médias (trocados por uma grade 2 × 2).
- Capturas: [computador](evidencias/local_painel_computador.jpg), [celular 1](evidencias/local_painel_celular_1.jpg), [celular 2](evidencias/local_painel_celular_2.jpg) (viewport 375 × 812).
  Nas capturas do celular, a Carteira aparece com −R$ 39,00; depois disso o saldo inicial dela foi ajustado de 150,00 para 300,00 nos dados fictícios.

## 4. Verificação pela URL pública

_Pendente: preenchido após o deploy no Streamlit Community Cloud._
