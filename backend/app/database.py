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
