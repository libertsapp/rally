"""Espelha a planilha "Rodadas" do Apps Script legado (roundId | data |
timeIndex | timeNome | jogadores | vitorias | vencedor | rascunho), só que
normalizado em duas tabelas em vez de uma linha por time por rodada."""

import uuid

from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Rodada(Base):
    __tablename__ = "rodadas"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organizacao_id = Column(String, nullable=False, default="dev")
    data = Column(String, nullable=False)  # "yyyy-mm-dd"
    rascunho = Column(Boolean, default=False)

    times = relationship(
        "RodadaTime", back_populates="rodada", cascade="all, delete-orphan", order_by="RodadaTime.time_index"
    )

    @property
    def vencedor(self) -> int:
        for t in self.times:
            if t.vencedor:
                return t.time_index
        return -1


class RodadaTime(Base):
    __tablename__ = "rodada_times"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rodada_id = Column(String, ForeignKey("rodadas.id"), nullable=False)
    time_index = Column(Integer, nullable=False)
    nome = Column(String, default="")
    player_ids = Column(JSON, default=list)
    vitorias = Column(Integer, default=0)
    vencedor = Column(Boolean, default=False)

    rodada = relationship("Rodada", back_populates="times")
