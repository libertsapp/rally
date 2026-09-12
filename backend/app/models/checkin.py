"""Espelha a aba "Checkins" do Apps Script legado. `jogador_nome`/`estrelas`/
`sexo` ficam denormalizados (e não como FK) de propósito: é o que permite
confirmar presença de CONVIDADOS avulsos, que não têm cadastro em Jogador."""

import uuid

from sqlalchemy import Column, Float, String

from app.database import Base


class Checkin(Base):
    __tablename__ = "checkins"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organizacao_id = Column(String, nullable=False, default="dev")
    data = Column(String, nullable=False)  # "yyyy-mm-dd"
    jogador_id = Column(String, nullable=False)
    jogador_nome = Column(String, default="")
    estrelas = Column(Float, default=0)
    sexo = Column(String, default="")
