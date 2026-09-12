import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.checkin import Checkin
from app.routers.config import ORGANIZACAO_PADRAO, get_or_create_config
from app.schemas.checkin import CheckinEntrada, CheckinSaida

router = APIRouter(prefix="/checkins", tags=["checkins"])


@router.get("", response_model=list[CheckinSaida])
def listar_checkins(db: Session = Depends(get_db)):
    return db.query(Checkin).all()


@router.post("", response_model=CheckinSaida)
def confirmar_presenca(dados: CheckinEntrada, db: Session = Depends(get_db)):
    config = get_or_create_config(db)
    if not config.checkin_data_aberta:
        raise HTTPException(status_code=409, detail="O check-in está fechado no momento.")
    if config.checkin_travado:
        raise HTTPException(
            status_code=409,
            detail="O check-in está travado pelo admin — não é possível incluir novos nomes.",
        )
    ja_confirmado = (
        db.query(Checkin)
        .filter(Checkin.data == config.checkin_data_aberta, Checkin.jogador_id == dados.jogador_id)
        .first()
    )
    if ja_confirmado:
        raise HTTPException(status_code=409, detail="Esse jogador já confirmou presença hoje.")

    checkin = Checkin(
        id=str(uuid.uuid4()),
        organizacao_id=ORGANIZACAO_PADRAO,
        data=config.checkin_data_aberta,
        jogador_id=dados.jogador_id,
        jogador_nome=dados.jogador_nome,
        estrelas=dados.estrelas,
        sexo=dados.sexo,
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return checkin


@router.delete("/{checkin_id}")
def desmarcar_presenca(checkin_id: str, db: Session = Depends(get_db)):
    config = get_or_create_config(db)
    if config.checkin_travado:
        raise HTTPException(
            status_code=409,
            detail="O check-in está travado pelo admin — não é possível remover confirmações.",
        )
    checkin = db.query(Checkin).filter(Checkin.id == checkin_id).first()
    if not checkin:
        raise HTTPException(status_code=404, detail="Check-in não encontrado.")
    db.delete(checkin)
    db.commit()
    return {"status": "ok"}
