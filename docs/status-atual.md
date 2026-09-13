# Status atual — Rally (plataforma de vôlei)

> Leia isto pra continuar o projeto sem precisar ler o histórico da conversa.
> Última atualização: 2026-09-13.

## O que é

Migração dos dashboards **Vôlei de Terça** e **Vôlei Meme Brasil**
(HTML/JS + Google Apps Script + Sheets) pra uma plataforma multi-tenant
(Python/FastAPI + Postgres + Vercel). Visão completa em
`docs/plataforma-volei-plano-estrategico.md` e
`docs/inventario-nucleo-vs-configuravel.md`.

## URLs e acessos

- **Produção**: https://rally-eight-blush.vercel.app (frontend + API sob `/api/*`)
- **Repo**: https://github.com/libertsapp/rally (branch `master`, deploy automático a cada push)
- **Vercel**: projeto `vilela5/rally`
- **Banco**: Postgres via Neon (integração da Vercel) — string de conexão em `DATABASE_URL` (env var da Vercel + `backend/.env` local, gitignored)
- **Auth**: Clerk (chaves em `CLERK_PUBLISHABLE_KEY`/`CLERK_SECRET_KEY`, mesmo esquema)
- **Superadmin**: `kingnabucodonosor@gmail.com` (único usuário com papel `superadmin` no banco — precisa logar com esse e-mail exato pra ver "Mais → Organizações")

## Organizações reais já importadas em produção

| Organização | slug | id |
|---|---|---|
| dev (bootstrap/teste) | `dev` | `dev` |
| Vôlei de Terça | `volei-de-terca` | `e2760ab2-4301-4d7e-9dfc-d81b98a3fb91` |
| Vôlei Meme Brasil | `volei-meme` | `3b18f20d-431f-401e-b6cf-c17818f27a39` |

Pra ver os dados de uma organização sem logar como superadmin: mandar o
header `X-Organizacao-Id: <id>` em qualquer chamada à API.

## Estrutura do repositório

```
backend/
  app/
    database.py       # engine, Session, Base — lê DATABASE_URL do ambiente
    models/            # Organizacao, Usuario, Jogador, Rodada, RodadaTime, Checkin, Config
    schemas/           # Pydantic (entrada/saída da API)
    routers/           # 1 arquivo por área (jogadores, rodadas, sorteio, checkins,
                        #   config, ranking, dashboard, gamificacao, organizacoes, usuarios)
    sorteio/            # algoritmo de sorteio — módulo PURO, sem banco nem API
    clerk_auth.py      # verificação de sessão Clerk (get_usuario_atual)
    tenant.py          # resolução de organização por request (get_organizacao_atual)
    org_bootstrap.py   # organização "dev" de fallback (evita import circular)
  alembic/             # migrations — schema do banco é controlado por aqui, não por create_all
  tests/               # pytest, 109 testes
  main.py              # só monta o app e inclui os routers
api/index.py           # entrypoint da função serverless da Vercel (Starlette: /api→FastAPI, resto→estático)
frontend/
  index.html, style.css, app.js   # vanilla JS, sem build, consome a API
vercel.json             # não existe mais — roteamento é feito dentro de api/index.py
requirements.txt        # (raiz) usado pelo build da Vercel — espelha backend/requirements.txt
```

## O que está PRONTO (testado e em produção)

- **Fase 1 completa**: Jogadores, Rodadas, Check-in, Sorteio (algoritmo portado do JS legado,
  isolado em `app/sorteio/`, garantia de "nunca 2 do mesmo grupo no mesmo time" validada em
  milhares de simulações), Ranking, Dashboard, Perfil, Gamificação (badges), Hall da Fama, Histórico.
- **Fase 2 completa**: modelo `Organizacao`/`Usuario` real, isolamento de dados por organização
  em TODOS os routers (testado em `test_multi_tenant_isolamento.py`), autenticação Clerk de
  verdade (token verificado via SDK oficial, não confia em header sem sessão válida), CORS
  restrito, seletor de organização no frontend (Mais → Organizações, só superadmin).
- **Infra**: Alembic (migrations versionadas, schema nunca mais editado via `create_all` em
  produção), deploy automático (push → build → produção via GitHub↔Vercel), Postgres real (Neon).
- **Dados reais migrados**: Vôlei de Terça (44 jogadores, 33 rodadas) e Vôlei Meme Brasil
  (53 jogadores, 7 rodadas) importados da planilha Google Sheets original, preservando os IDs.

## O que FALTA

- UI de "reivindicar perfil" (jogador comum vincula conta a um cadastro já existente).
- PWA de verdade (ícones, service worker) — hoje só tem manifest básico.
- Placar ao vivo é 100% client-side (sem persistência) — decisão consciente, não é bug.

## Padrões e armadilhas importantes (releia antes de mexer)

1. **Nunca conte `player_ids` de uma Rodada sem filtrar convidados avulsos.**
   `player_ids` pode conter `"convidado:NOME#hash"` (gente que jogou sem cadastro de Jogador).
   Já apareceram 2 bugs reais por esquecer esse filtro (`/badges` e `/dashboard/resumo`) — sempre
   que iterar `player_ids` pra estatística de jogador cadastrado, filtrar por
   `pid in {ids reais de Jogador}` primeiro.
2. **Frontend: toda tela que faz fetch assíncrono usa o sistema de `token`/`tokenValido()`**
   em `app.js` (protege contra condição de corrida quando o usuário navega antes do fetch
   terminar). Qualquer novo renderizador assíncrono precisa seguir esse padrão — ver
   `renderInicio`/`renderHistoricoSub` como exemplo.
3. **Schema do banco só muda via Alembic.** Editar um model sem gerar migration
   (`alembic revision --autogenerate -m "..."`) quebra produção. Testes usam `create_all`
   direto (banco descartável), isso é esperado e correto.
4. **`DATABASE_URL` de provedor externo** (Neon/Supabase/etc) vem como `postgres://` — o projeto
   usa `psycopg` v3, então `app/database.py` reescreve pra `postgresql+psycopg://` automaticamente.
5. **Resolução de organização** (`app/tenant.py`): usuário autenticado com organização própria
   sempre vence; senão usa o header `X-Organizacao-Id`; senão cai na organização "dev". Um
   admin logado NUNCA pode ser sobrescrito por header (só superadmin/anônimo usa o header).
6. **Terminal Windows pode exibir UTF-8 errado** (mojibake) sem o dado estar corrompido de
   verdade — sempre confirmar corrupção de dado real via Python (`bytes.decode('utf-8')`),
   nunca só pelo que aparece no terminal.

## Como rodar localmente

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head          # cria o schema (sqlite local por padrão)
uvicorn main:app --reload     # API em http://127.0.0.1:8000/docs

cd ../frontend
python -m http.server 5500    # frontend em http://127.0.0.1:5500 (aponta pro backend acima)
```

Pra rodar contra o Postgres de produção (com cuidado — é dado real):
```bash
DATABASE_URL=$(grep -E "^DATABASE_URL=" .env.local | head -1 | cut -d= -f2- | tr -d '"') \
  python -m uvicorn main:app --host 127.0.0.1 --port 8000
```
(`.env.local` na raiz do repo, gitignored, criado pela integração Neon/Vercel)

## Deploy manual (só se o deploy automático falhar)

```bash
npx vercel deploy --prod --yes
```

## Testes

```bash
cd backend && pytest tests/ -v     # 109 testes, todos devem passar
```
