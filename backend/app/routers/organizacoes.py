"""Gestão de organizações (tenants) e seus admins.

Criar/listar organizações e convidar admin são coisas de superadmin.
Atualizar a identidade de uma organização também pode ser feito pelo admin
DAQUELA organização (ele cuida da própria marca, não das outras). Ler a
identidade de uma organização (`/atual`, `/{id}`) continua público — é só a
marca do grupo, sem dado sensível, e o frontend precisa disso sem estar
logado pra montar a tela.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.clerk_auth import get_usuario_atual
from app.database import get_db
from app.models.config import Config
from app.models.organizacao import Organizacao
from app.models.usuario import Usuario
from app.org_bootstrap import get_or_create_organizacao_padrao
from app.schemas.organizacao import OrganizacaoAtualizar, OrganizacaoEntrada, OrganizacaoSaida
from app.schemas.usuario import ConvidarAdminEntrada, UsuarioSaida
from app.tenant import get_organizacao_atual

router = APIRouter(prefix="/organizacoes", tags=["organizacoes"])


def _exigir_superadmin(usuario: Usuario | None = Depends(get_usuario_atual)) -> Usuario:
    if not usuario or usuario.tipo != "superadmin":
        raise HTTPException(status_code=403, detail="Só o superadmin pode fazer isso.")
    return usuario


@router.get("", response_model=list[OrganizacaoSaida])
def listar_organizacoes(db: Session = Depends(get_db), _: Usuario = Depends(_exigir_superadmin)):
    return db.query(Organizacao).all()


@router.post("", response_model=OrganizacaoSaida)
def criar_organizacao(
    dados: OrganizacaoEntrada, db: Session = Depends(get_db), _: Usuario = Depends(_exigir_superadmin)
):
    if db.query(Organizacao).filter(Organizacao.slug == dados.slug).first():
        raise HTTPException(status_code=409, detail="Já existe uma organização com esse slug.")
    organizacao = Organizacao(**dados.model_dump())
    db.add(organizacao)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe uma organização com esse slug.")
    db.refresh(organizacao)
    # toda organização já nasce com sua linha de configuração operacional
    db.add(Config(organizacao_id=organizacao.id))
    db.commit()
    return organizacao


@router.get("/atual", response_model=OrganizacaoSaida)
def obter_organizacao_atual(organizacao: Organizacao = Depends(get_organizacao_atual)):
    """Organização "corrente": a do usuário autenticado, ou a apontada pelo
    header X-Organizacao-Id (usado pelo seletor de organização do
    superadmin), ou a "dev" de bootstrap — ver app/tenant.py."""
    return organizacao


@router.get("/{organizacao_id}", response_model=OrganizacaoSaida)
def obter_organizacao(organizacao_id: str, db: Session = Depends(get_db)):
    organizacao = db.query(Organizacao).filter(Organizacao.id == organizacao_id).first()
    if not organizacao:
        raise HTTPException(status_code=404, detail="Organização não encontrada.")
    return organizacao


@router.put("/{organizacao_id}", response_model=OrganizacaoSaida)
def atualizar_organizacao(
    organizacao_id: str,
    dados: OrganizacaoAtualizar,
    db: Session = Depends(get_db),
    usuario: Usuario | None = Depends(get_usuario_atual),
):
    pode_editar = usuario and (
        usuario.tipo == "superadmin" or (usuario.tipo == "admin" and usuario.organizacao_id == organizacao_id)
    )
    if not pode_editar:
        raise HTTPException(status_code=403, detail="Você não administra essa organização.")
    organizacao = db.query(Organizacao).filter(Organizacao.id == organizacao_id).first()
    if not organizacao:
        raise HTTPException(status_code=404, detail="Organização não encontrada.")
    for campo, valor in dados.model_dump().items():
        setattr(organizacao, campo, valor)
    db.commit()
    db.refresh(organizacao)
    return organizacao


@router.post("/{organizacao_id}/admins", response_model=UsuarioSaida)
def convidar_admin(
    organizacao_id: str,
    dados: ConvidarAdminEntrada,
    db: Session = Depends(get_db),
    _: Usuario = Depends(_exigir_superadmin),
):
    organizacao = db.query(Organizacao).filter(Organizacao.id == organizacao_id).first()
    if not organizacao:
        raise HTTPException(status_code=404, detail="Organização não encontrada.")

    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if usuario:
        usuario.tipo = "admin"
        usuario.organizacao_id = organizacao_id
        usuario.ativo = True
    else:
        usuario = Usuario(email=dados.email, tipo="admin", organizacao_id=organizacao_id)
        db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.get("/{organizacao_id}/admins", response_model=list[UsuarioSaida])
def listar_admins(
    organizacao_id: str, db: Session = Depends(get_db), _: Usuario = Depends(_exigir_superadmin)
):
    return (
        db.query(Usuario)
        .filter(Usuario.organizacao_id == organizacao_id, Usuario.tipo == "admin")
        .all()
    )
