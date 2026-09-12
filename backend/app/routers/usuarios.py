from fastapi import APIRouter, Depends, HTTPException

from app.clerk_auth import get_usuario_atual
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioSaida

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("/eu", response_model=UsuarioSaida)
def eu(usuario: Usuario | None = Depends(get_usuario_atual)):
    if not usuario:
        raise HTTPException(status_code=401, detail="Não autenticado.")
    return usuario
