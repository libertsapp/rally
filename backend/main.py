"""Backend da plataforma — FastAPI + SQLite (local) / Postgres (produção).

Como rodar:
    alembic upgrade head   # aplica as migrations (cria/atualiza as tabelas)
    uvicorn main:app --reload

Depois é só abrir http://127.0.0.1:8000/docs no navegador — o FastAPI gera
uma tela de testes automática pra cada endpoint, sem precisar escrever nada.

O schema do banco é controlado pelo Alembic (pasta alembic/), não mais por
Base.metadata.create_all — qualquer mudança de modelo precisa de uma migration
nova (`alembic revision --autogenerate -m "..."`). Os testes continuam usando
create_all direto (ver tests/conftest.py), o que é o normal: banco de teste é
descartável, não precisa de migration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    checkins,
    config,
    dashboard,
    gamificacao,
    jogadores,
    organizacoes,
    ranking,
    rodadas,
    sorteio,
)

app = FastAPI(title="Vôlei — API")

# CORS liberado geral por enquanto (é dev local) — quando for pra produção,
# troca allow_origins=["*"] pela lista real de domínios do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jogadores.router)
app.include_router(rodadas.router)
app.include_router(sorteio.router)
app.include_router(config.router)
app.include_router(checkins.router)
app.include_router(ranking.router)
app.include_router(dashboard.router)
app.include_router(gamificacao.router)
app.include_router(organizacoes.router)


@app.get("/")
def raiz():
    return {"status": "ok", "mensagem": "API do Vôlei rodando 🏐"}
