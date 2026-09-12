"""Usuário da plataforma. Quem autentica de fato é o Clerk (ainda não
integrado) — esta tabela só guarda o PAPEL de cada e-mail: superadmin (vê
tudo), admin (gerencia 1 organização) ou jogador (futuro: conta vinculada a
um cadastro de Jogador já existente). `clerk_user_id` fica nulo até a
integração real acontecer."""

import uuid

from sqlalchemy import Boolean, Column, ForeignKey, String

from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, nullable=False, unique=True)
    tipo = Column(String, nullable=False, default="admin")  # "superadmin" | "admin" | "jogador"
    organizacao_id = Column(String, ForeignKey("organizacoes.id"), nullable=True)
    clerk_user_id = Column(String, nullable=True, unique=True)
    ativo = Column(Boolean, default=True)
