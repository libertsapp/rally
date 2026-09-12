"""Resolução de tenant por request.

Sem autenticação de verdade ainda (Clerk não integrado), então não há como
saber com certeza "de qual organização é esse usuário" a partir de uma
sessão. Por ora, o cliente pode informar explicitamente via header
`X-Organizacao-Id` (o admin de um grupo específico faria isso); sem o
header, cai na organização "dev" — o mesmo comportamento de sempre, então
nada quebra pra quem já estava usando a API assim.

Quando o Clerk entrar, esta função passa a resolver a organização a partir
do usuário autenticado (via app.models.usuario.Usuario), não mais de um
header que qualquer um pode forjar.
"""

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.organizacao import Organizacao
from app.routers.organizacoes import get_or_create_organizacao_padrao


def get_organizacao_atual(
    x_organizacao_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Organizacao:
    if x_organizacao_id:
        organizacao = db.query(Organizacao).filter(Organizacao.id == x_organizacao_id).first()
        if not organizacao:
            raise HTTPException(status_code=404, detail="Organização não encontrada.")
        return organizacao
    return get_or_create_organizacao_padrao(db)
