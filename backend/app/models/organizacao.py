"""Organização = um "grupo"/tenant (ex: Vôlei de Terça, Vôlei Meme). Guarda a
identidade visual que hoje vivia solta no Config — Config passa a ter só
configurações operacionais (check-in, prazos de ausência)."""

import uuid

from sqlalchemy import Column, String

from app.database import Base


class Organizacao(Base):
    __tablename__ = "organizacoes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    slug = Column(String, nullable=False, unique=True)
    nome = Column(String, nullable=False)
    subtitulo = Column(String, default="")
    logo_url = Column(String, default="")
    cor_primaria = Column(String, default="")
    cor_secundaria = Column(String, default="")
    link_rede_social = Column(String, default="")
    plano = Column(String, default="gratuito")
