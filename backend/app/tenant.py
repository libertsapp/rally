"""Resolução de tenant por request.

Ordem de prioridade:
1. Usuário autenticado (Clerk) com organização própria — sempre vence,
   nunca pode ser sobrescrito por header (senão um admin logado poderia se
   passar por outra organização só mandando um header diferente).
2. Header `X-Organizacao-Id` — usado por quem não tem organização própria
   ainda (superadmin navegando entre organizações, ou dev/teste sem Clerk).
3. Organização "dev" — mesmo comportamento de sempre, backward compatible.
"""

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.clerk_auth import get_usuario_atual
from app.database import get_db
from app.models.organizacao import Organizacao
from app.models.usuario import Usuario
from app.org_bootstrap import get_or_create_organizacao_padrao


def get_organizacao_atual(
    x_organizacao_id: str | None = Header(default=None),
    usuario: Usuario | None = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
) -> Organizacao:
    if usuario and usuario.organizacao_id:
        organizacao = db.query(Organizacao).filter(Organizacao.id == usuario.organizacao_id).first()
        if organizacao:
            return organizacao

    if x_organizacao_id:
        organizacao = db.query(Organizacao).filter(Organizacao.id == x_organizacao_id).first()
        if not organizacao:
            raise HTTPException(status_code=404, detail="Organização não encontrada.")
        return organizacao

    return get_or_create_organizacao_padrao(db)
