# Backend — API da plataforma de vôlei

FastAPI + SQLAlchemy. SQLite em dev local, Postgres em produção (mesma base de
código — só troca a `DATABASE_URL`).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Copie `.env.example` para `.env` se for usar Postgres (em dev local, SQLite
funciona sem configurar nada).

## Rodar

```bash
alembic upgrade head           # aplica as migrations (cria as tabelas)
uvicorn main:app --reload
```

Depois abra http://127.0.0.1:8000/docs — o FastAPI gera uma tela de teste
automática pra cada endpoint.

## Testes

```bash
pytest tests/ -v
```

Os testes de API usam um banco SQLite temporário próprio (criado via
`Base.metadata.create_all`, sem depender do Alembic — banco de teste é
descartável a cada execução). O módulo `app/sorteio/` tem sua própria suíte
isolada, incluindo simulações que provam a garantia de "nunca 2 jogadores do
mesmo grupo no mesmo time".

## Mudando o schema (models)

1. Edite o(s) model(s) em `app/models/`.
2. Gere a migration: `alembic revision --autogenerate -m "descrição curta"`.
3. Confira o arquivo gerado em `alembic/versions/` — o autogenerate é um
   rascunho, não confie cegamente nele.
4. Aplique: `alembic upgrade head`.

Nunca edite uma tabela só apagando o `volei.db` local — isso funciona sozinho
em dev, mas quebra em produção (dado real não pode ser apagado). A partir de
agora, toda mudança de schema é uma migration.

## Estrutura

```
app/
  database.py       # engine, Session, Base — lê DATABASE_URL do ambiente
  models/           # tabelas (SQLAlchemy)
  schemas/          # formato de entrada/saída da API (Pydantic)
  routers/          # os endpoints, um arquivo por área
  sorteio/          # algoritmo de sorteio — módulo puro, sem banco nem API
alembic/            # migrations
tests/              # pytest — um arquivo por área + tests/sorteio/
main.py             # só monta o app e inclui os routers
```

## Multi-tenant

Toda tabela já nasce com `organizacao_id` (hoje fixo em `"dev"` — ainda não
existe autenticação nem conceito de organização de verdade). Isso é
propositalmente adiantado: quando a Fase 2 (superadmin, múltiplos grupos)
começar, não vai ser preciso migrar dado nenhum, só passar a filtrar de
verdade por esse campo.
