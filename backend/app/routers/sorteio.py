from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.jogador import Jogador
from app.models.organizacao import Organizacao
from app.models.rodada import Rodada
from app.schemas.sorteio import MontarGruposEntrada, SortearTimesEntrada
from app.sorteio.draft import contar_duplas_recentes, draft_balanced
from app.sorteio.grupos import montar_grupos
from app.sorteio.modelos import JogadorSorteio
from app.tenant import get_organizacao_atual

router = APIRouter(prefix="/sorteio", tags=["sorteio"])


def _buscar_jogadores(db: Session, jogador_ids: list[str], organizacao_id: str) -> list[Jogador]:
    jogadores = (
        db.query(Jogador)
        .filter(Jogador.id.in_(jogador_ids), Jogador.organizacao_id == organizacao_id)
        .all()
    )
    encontrados = {p.id for p in jogadores}
    faltando = [i for i in jogador_ids if i not in encontrados]
    if faltando:
        raise HTTPException(status_code=404, detail=f"Jogadores não encontrados: {faltando}")
    return jogadores


def _para_sorteio(p: Jogador) -> JogadorSorteio:
    return JogadorSorteio(id=p.id, nome=p.nome, estrelas=p.estrelas or 0, sexo=p.sexo or "", porte=p.porte or "")


def _recent_counts(db: Session, organizacao_id: str, limite: int) -> dict[frozenset[str], int]:
    rounds = (
        db.query(Rodada)
        .filter(Rodada.rascunho.is_(False), Rodada.organizacao_id == organizacao_id)
        .order_by(Rodada.data.desc())
        .limit(limite)
        .all()
    )
    rounds_dict = [
        {"data": r.data, "times": [{"playerIds": t.player_ids} for t in r.times]} for r in rounds
    ]
    return contar_duplas_recentes(rounds_dict, limite)


@router.post("/grupos", response_model=list[list[str]])
def montar_grupos_route(
    dados: MontarGruposEntrada,
    db: Session = Depends(get_db),
    organizacao: Organizacao = Depends(get_organizacao_atual),
):
    """Modo manual: monta grupos por nível. Devolve os IDs de cada grupo,
    já na ordem cascata (mais forte pro mais fraco, mulheres nos últimos)."""
    jogadores = _buscar_jogadores(db, dados.jogador_ids, organizacao.id)
    por_id = {p.id: p for p in jogadores}
    grupos = montar_grupos([_para_sorteio(por_id[i]) for i in dados.jogador_ids], dados.num_times)
    return [[p.id for p in grupo] for grupo in grupos]


@router.post("/times", response_model=list[list[str]])
def sortear_times_route(
    dados: SortearTimesEntrada,
    db: Session = Depends(get_db),
    organizacao: Organizacao = Depends(get_organizacao_atual),
):
    """Monta os times sorteados. Se `grupos` vier preenchido (IDs por grupo,
    do modo híbrido "grupos + automático"), garante que ninguém do mesmo grupo
    cai no mesmo time. Devolve os IDs de cada time (ordem de exibição sorteada)."""
    jogadores = _buscar_jogadores(db, dados.jogador_ids, organizacao.id)
    por_id = {p.id: p for p in jogadores}
    pool = [_para_sorteio(por_id[i]) for i in dados.jogador_ids]

    grupos_para_sorteio = None
    if dados.grupos:
        pool_por_id = {p.id: p for p in pool}
        grupos_para_sorteio = [[pool_por_id[i] for i in grupo] for grupo in dados.grupos]

    recent_counts = (
        _recent_counts(db, organizacao.id, dados.limite_rodadas_recentes)
        if dados.considerar_historico
        else {}
    )

    times = draft_balanced(
        pool,
        dados.num_times,
        grupos_para_este_sorteio=grupos_para_sorteio,
        recent_counts=recent_counts,
    )
    return [[p.id for p in time] for time in times]
