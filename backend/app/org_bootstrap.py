"""Organização padrão ("dev") usada como fallback enquanto um usuário não
tem organização própria (visitante anônimo, superadmin sem org selecionada,
ou dev/teste sem Clerk). Vive num módulo à parte pra `app.tenant` e
`app.routers.organizacoes` poderem compartilhar sem import circular."""

from sqlalchemy.orm import Session

from app.models.config import Config
from app.models.organizacao import Organizacao

SLUG_ORGANIZACAO_PADRAO = "dev"


def get_or_create_organizacao_padrao(db: Session) -> Organizacao:
    organizacao = db.query(Organizacao).filter(Organizacao.slug == SLUG_ORGANIZACAO_PADRAO).first()
    if not organizacao:
        organizacao = Organizacao(slug=SLUG_ORGANIZACAO_PADRAO, nome="Organização de desenvolvimento")
        db.add(organizacao)
        db.commit()
        db.refresh(organizacao)
        db.add(Config(organizacao_id=organizacao.id))
        db.commit()
    return organizacao
