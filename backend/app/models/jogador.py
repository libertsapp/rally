import uuid

from sqlalchemy import Column, Float, String

from app.database import Base


class Jogador(Base):
    __tablename__ = "jogadores"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organizacao_id = Column(String, nullable=False, default="dev")  # fixo até multi-tenant de verdade
    nome = Column(String, nullable=False)
    apelido = Column(String, default="")
    foto = Column(String, default="")
    estrelas = Column(Float, default=0)
    sexo = Column(String, default="")
    porte = Column(String, default="")  # "P" | "M" | "G" | ""
