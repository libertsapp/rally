from datetime import date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.jogador import Jogador
from app.models.organizacao import Organizacao
from app.models.rodada import Rodada
from app.routers.config import get_or_create_config
from app.schemas.dashboard import AusenteLinha, CampeaoSemana, DuplaLinha, FotoLinha, PanelaLinha, ResumoDashboard
from app.tenant import get_organizacao_atual
from app.utils import ano_de

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def rodadas_oficiais(db: Session, organizacao_id: str) -> list[Rodada]:
    return (
        db.query(Rodada)
        .options(joinedload(Rodada.times))
        .filter(Rodada.rascunho.is_(False), Rodada.organizacao_id == organizacao_id)
        .all()
    )


def peso_de_jogador(jogadores_por_id: dict[str, Jogador], pid: str) -> float:
    p = jogadores_por_id.get(pid)
    return p.estrelas if p and p.estrelas and p.estrelas > 0 else 3


@router.get("/resumo", response_model=ResumoDashboard)
def resumo(db: Session = Depends(get_db), organizacao: Organizacao = Depends(get_organizacao_atual)):
    config = get_or_create_config(db, organizacao.id)
    rodadas = rodadas_oficiais(db, organizacao.id)
    total_jogadores_query = db.query(Jogador).filter(Jogador.organizacao_id == organizacao.id)

    if not rodadas:
        return ResumoDashboard(
            ano=str(date.today().year),
            dias_jogados_no_ano=0,
            jogadores_ativos=total_jogadores_query.count(),
            desaparecidos=0,
            campeao_semana=None,
        )

    ultima = max(rodadas, key=lambda r: r.data)
    ano_atual = ano_de(ultima.data)
    dias_jogados = sum(1 for r in rodadas if ano_de(r.data) == ano_atual)

    ultima_participacao: dict[str, str] = {}
    for r in rodadas:
        for t in r.times:
            for pid in t.player_ids:
                if pid not in ultima_participacao or r.data > ultima_participacao[pid]:
                    ultima_participacao[pid] = r.data

    hoje = date.today()
    desaparecidos = 0
    for data_str in ultima_participacao.values():
        try:
            dias = (hoje - datetime.strptime(data_str, "%Y-%m-%d").date()).days
        except ValueError:
            continue
        if dias > config.dias_para_rip:
            desaparecidos += 1

    total_jogadores = total_jogadores_query.count()

    campeao = None
    vencedor_idx = ultima.vencedor
    if vencedor_idx != -1:
        time_vencedor = next((t for t in ultima.times if t.time_index == vencedor_idx), None)
        if time_vencedor:
            campeao = CampeaoSemana(
                data=ultima.data, time_nome=time_vencedor.nome, player_ids=time_vencedor.player_ids
            )

    return ResumoDashboard(
        ano=ano_atual,
        dias_jogados_no_ano=dias_jogados,
        jogadores_ativos=total_jogadores - desaparecidos,
        desaparecidos=desaparecidos,
        campeao_semana=campeao,
    )


@router.get("/mais-vezes-na-foto", response_model=list[FotoLinha])
def mais_vezes_na_foto(
    ano: str | None = None,
    db: Session = Depends(get_db),
    organizacao: Organizacao = Depends(get_organizacao_atual),
):
    jogadores = {p.id: p for p in db.query(Jogador).filter(Jogador.organizacao_id == organizacao.id).all()}
    vezes: dict[str, int] = {pid: 0 for pid in jogadores}
    ultima_conquista: dict[str, str] = {}

    for r in rodadas_oficiais(db, organizacao.id):
        if ano and ano_de(r.data) != ano:
            continue
        for t in r.times:
            if t.time_index != r.vencedor:
                continue
            for pid in t.player_ids:
                if pid not in vezes:
                    continue
                vezes[pid] += 1
                if pid not in ultima_conquista or r.data > ultima_conquista[pid]:
                    ultima_conquista[pid] = r.data

    linhas = [
        FotoLinha(id=pid, nome=jogadores[pid].nome, apelido=jogadores[pid].apelido or "", vezes=v)
        for pid, v in vezes.items()
        if v > 0
    ]
    # mais vezes primeiro; empate desfeito por quem foi campeão mais recentemente
    linhas.sort(key=lambda linha: (linha.vezes, ultima_conquista.get(linha.id, "")), reverse=True)
    return linhas[:10]


@router.get("/duplas-mais-sorteadas", response_model=list[DuplaLinha])
def duplas_mais_sorteadas(
    ano: str | None = None,
    db: Session = Depends(get_db),
    organizacao: Organizacao = Depends(get_organizacao_atual),
):
    counts: dict[frozenset[str], int] = {}
    for r in rodadas_oficiais(db, organizacao.id):
        if ano and ano_de(r.data) != ano:
            continue
        for t in r.times:
            ids = [i for i in t.player_ids if i]
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    chave = frozenset({ids[i], ids[j]})
                    counts[chave] = counts.get(chave, 0) + 1

    linhas = [DuplaLinha(id1=sorted(k)[0], id2=sorted(k)[1], count=c) for k, c in counts.items()]
    linhas.sort(key=lambda linha: linha.count, reverse=True)
    return linhas[:10]


@router.get("/panelas", response_model=list[PanelaLinha])
def panelas(
    ano: str | None = None,
    db: Session = Depends(get_db),
    organizacao: Organizacao = Depends(get_organizacao_atual),
):
    jogadores = {p.id: p for p in db.query(Jogador).filter(Jogador.organizacao_id == organizacao.id).all()}
    resultados = []
    for r in rodadas_oficiais(db, organizacao.id):
        if ano and ano_de(r.data) != ano:
            continue
        times = [t for t in r.times if t.player_ids]
        if len(times) < 2:
            continue
        medias = {
            t.time_index: sum(peso_de_jogador(jogadores, pid) for pid in t.player_ids) / len(t.player_ids)
            for t in times
        }
        for t in times:
            outros = [medias[i] for i in medias if i != t.time_index]
            media_outros = sum(outros) / len(outros)
            media_time = medias[t.time_index]
            resultados.append(
                PanelaLinha(
                    data=r.data,
                    time_nome=t.nome,
                    player_ids=t.player_ids,
                    media_time=media_time,
                    media_outros=media_outros,
                    diff=media_time - media_outros,
                )
            )
    resultados.sort(key=lambda p: p.diff, reverse=True)
    return resultados[:3]


@router.get("/ausentes", response_model=list[AusenteLinha])
def ausentes(db: Session = Depends(get_db), organizacao: Organizacao = Depends(get_organizacao_atual)):
    config = get_or_create_config(db, organizacao.id)
    jogadores = {p.id: p for p in db.query(Jogador).filter(Jogador.organizacao_id == organizacao.id).all()}

    ultima_participacao: dict[str, str] = {}
    for r in rodadas_oficiais(db, organizacao.id):
        for t in r.times:
            for pid in t.player_ids:
                if pid not in ultima_participacao or r.data > ultima_participacao[pid]:
                    ultima_participacao[pid] = r.data

    hoje = date.today()
    linhas = []
    for pid, data_str in ultima_participacao.items():
        jogador = jogadores.get(pid)
        if not jogador:
            continue
        try:
            dias = (hoje - datetime.strptime(data_str, "%Y-%m-%d").date()).days
        except ValueError:
            continue
        if dias > config.dias_para_aposentado:
            status = "aposentado"
        elif dias > config.dias_para_rip:
            status = "rip"
        else:
            continue
        linhas.append(
            AusenteLinha(
                id=pid, nome=jogador.nome, apelido=jogador.apelido or "", dias_sem_jogar=dias, status=status
            )
        )
    linhas.sort(key=lambda linha: linha.dias_sem_jogar, reverse=True)
    return linhas
