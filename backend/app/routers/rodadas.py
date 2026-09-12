from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.rodada import Rodada, RodadaTime
from app.schemas.rodada import RodadaEntrada, RodadaSaida

router = APIRouter(prefix="/rodadas", tags=["rodadas"])


def _query_base(db: Session):
    return db.query(Rodada).options(joinedload(Rodada.times))


@router.get("", response_model=list[RodadaSaida])
def listar_rodadas(db: Session = Depends(get_db)):
    return _query_base(db).all()


@router.post("", response_model=RodadaSaida)
def criar_rodada(dados: RodadaEntrada, db: Session = Depends(get_db)):
    rodada = Rodada(data=dados.data, rascunho=dados.rascunho)
    for idx, time in enumerate(dados.times):
        rodada.times.append(
            RodadaTime(
                time_index=idx,
                nome=time.nome,
                player_ids=time.player_ids,
                vitorias=time.vitorias,
                vencedor=(idx == dados.vencedor),
            )
        )
    db.add(rodada)
    db.commit()
    db.refresh(rodada)
    return rodada


@router.put("/{rodada_id}", response_model=RodadaSaida)
def atualizar_rodada(rodada_id: str, dados: RodadaEntrada, db: Session = Depends(get_db)):
    rodada = _query_base(db).filter(Rodada.id == rodada_id).first()
    if not rodada:
        raise HTTPException(status_code=404, detail="Rodada não encontrada")
    rodada.data = dados.data
    rodada.rascunho = dados.rascunho
    rodada.times = [
        RodadaTime(
            time_index=idx,
            nome=time.nome,
            player_ids=time.player_ids,
            vitorias=time.vitorias,
            vencedor=(idx == dados.vencedor),
        )
        for idx, time in enumerate(dados.times)
    ]
    db.commit()
    db.refresh(rodada)
    return rodada


@router.delete("/{rodada_id}")
def remover_rodada(rodada_id: str, db: Session = Depends(get_db)):
    rodada = db.query(Rodada).filter(Rodada.id == rodada_id).first()
    if not rodada:
        raise HTTPException(status_code=404, detail="Rodada não encontrada")
    db.delete(rodada)
    db.commit()
    return {"status": "ok"}
