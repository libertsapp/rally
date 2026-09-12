"""Configuração de banco compartilhada por todos os modelos.

Troca DATABASE_URL pra apontar pro Postgres (Vercel Postgres / Neon /
Supabase) quando for pra produção — o resto do código não muda, porque
usamos SQLAlchemy (ele conversa com os dois bancos igual).
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./volei.db")

# provedores de Postgres (Neon, Supabase, Vercel Postgres...) costumam dar a
# URL como "postgres://" ou "postgresql://" puro, que o SQLAlchemy tentaria
# abrir com psycopg2 — mas instalamos psycopg (v3). Força o driver certo.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
