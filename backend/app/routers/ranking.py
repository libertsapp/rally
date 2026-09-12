from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.jogador import Jogador
from app.models.organizacao import Organizacao
from app.models.rodada import Rodada
from app.schemas.ranking import RankingLinha
from app.tenant import get_organizacao_atual
from app.utils import ano_de as _ano_de

router = APIRouter(prefix="/ranking", tags=["ranking"])


@router.get("", response_model=list[RankingLinha])
def obter_ranking(
    ano: int,
    db: Session = Depends(get_db),
    organizacao: Organizacao = Depends(get_organizacao_atual),
):
    stats = {
        p.id: {
            "id": p.id,
            "nome": p.nome,
            "apelido": p.apelido or "",
            "jogos": 0,
            "titulos": 0,
            "vitorias_partidas": 0,
            "datas_campeao": [],
        }
        for p in db.query(Jogador).filter(Jogador.organizacao_id == organizacao.id).all()
    }

    rodadas = (
        db.query(Rodada)
        .options(joinedload(Rodada.times))
        .filter(Rodada.rascunho.is_(False), Rodada.organizacao_id == organizacao.id)
        .all()
    )
    for r in rodadas:
        if _ano_de(r.data) != str(ano):
            continue
        vencedor_idx = r.vencedor
        for t in r.times:
            eh_vencedor = t.time_index == vencedor_idx
            for pid in t.player_ids:
                if pid not in stats:
                    continue  # convidado avulso, sem cadastro de Jogador — não entra no ranking
                stats[pid]["jogos"] += 1
                if eh_vencedor:
                    stats[pid]["titulos"] += 1
                    stats[pid]["datas_campeao"].append(r.data)
                stats[pid]["vitorias_partidas"] += t.vitorias or 0

    resultado = [s for s in stats.values() if s["jogos"] > 0]
    for s in resultado:
        s["pct"] = round((s["titulos"] / s["jogos"]) * 100)
    resultado.sort(key=lambda s: (-s["titulos"], -s["vitorias_partidas"], -s["pct"]))
    return resultado
