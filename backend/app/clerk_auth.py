"""Verificação de sessão via Clerk.

`get_usuario_atual` devolve o Usuario correspondente ao token de sessão do
Clerk mandado no header Authorization (Bearer), ou None se não houver sessão
válida (visitante anônimo). Quem exige login faz a checagem de papel em cima
disso — ver `_exigir_superadmin` em app/routers/organizacoes.py para o
padrão (uma função nomeada, não uma fábrica, pra dar pra sobrescrever nos
testes via app.dependency_overrides).

Primeiro acesso de um e-mail novo que faz login vira um Usuario com papel
"jogador" por padrão — vira admin só através de /organizacoes/{id}/admins,
feito por um superadmin.
"""

import os

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario

_clerk_sdk = None


def _get_clerk_sdk():
    global _clerk_sdk
    if _clerk_sdk is None:
        from clerk_backend_api import Clerk

        _clerk_sdk = Clerk(bearer_auth=os.environ.get("CLERK_SECRET_KEY", ""))
    return _clerk_sdk


def get_usuario_atual(request: Request, db: Session = Depends(get_db)) -> Usuario | None:
    if not os.environ.get("CLERK_SECRET_KEY"):
        return None

    from clerk_backend_api.security.types import AuthenticateRequestOptions

    try:
        request_state = _get_clerk_sdk().authenticate_request(request, AuthenticateRequestOptions())
    except Exception:
        return None
    if not request_state.is_signed_in:
        return None

    payload = request_state.payload or {}
    email = payload.get("email")
    clerk_user_id = payload.get("sub")
    if not email:
        return None

    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        usuario = Usuario(email=email, tipo="jogador", clerk_user_id=clerk_user_id)
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
    elif clerk_user_id and usuario.clerk_user_id != clerk_user_id:
        usuario.clerk_user_id = clerk_user_id
        db.commit()
    return usuario
