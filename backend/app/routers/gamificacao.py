from datetime import date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.jogador import Jogador
from app.routers.config import get_or_create_config
from app.routers.dashboard import peso_de_jogador, rodadas_oficiais
from app.schemas.gamificacao import Badges, HallPeriodo, HallVencedor
from app.utils import ano_de

router = APIRouter(tags=["gamificacao"])


def _panela_entries(db: Session, ano: str) -> list[dict]:
    jogadores = {p.id: p for p in db.query(Jogador).all()}
    entradas = []
    for r in rodadas_oficiais(db):
        if ano_de(r.data) != ano:
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
            entradas.append({"player_ids": t.player_ids, "diff": medias[t.time_index] - media_outros})
    return entradas


def _top_duos(db: Session, ano: str) -> list[tuple[str, str, int]]:
    counts: dict[frozenset[str], int] = {}
    for r in rodadas_oficiais(db):
        if ano_de(r.data) != ano:
            continue
        for t in r.times:
            ids = [i for i in t.player_ids if i]
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    chave = frozenset({ids[i], ids[j]})
                    counts[chave] = counts.get(chave, 0) + 1
    duos = [(*sorted(k), c) for k, c in counts.items()]
    duos.sort(key=lambda d: d[2], reverse=True)
    return duos


def _ultima_participacao(db: Session) -> dict[str, str]:
    ultima: dict[str, str] = {}
    for r in rodadas_oficiais(db):
        for t in r.times:
            for pid in t.player_ids:
                if pid not in ultima or r.data > ultima[pid]:
                    ultima[pid] = r.data
    return ultima


@router.get("/badges", response_model=Badges)
def badges(db: Session = Depends(get_db)):
    config = get_or_create_config(db)
    jogadores = {p.id: p for p in db.query(Jogador).all()}
    ano_atual = str(date.today().year)

    # TOP1: quem mais saiu na foto de campeão no ano corrente
    vezes: dict[str, int] = {}
    for r in rodadas_oficiais(db):
        if ano_de(r.data) != ano_atual:
            continue
        for t in r.times:
            if t.time_index != r.vencedor:
                continue
            for pid in t.player_ids:
                if pid in jogadores:
                    vezes[pid] = vezes.get(pid, 0) + 1
    max_foto = max(vezes.values()) if vezes else 0
    top1 = [pid for pid, v in vezes.items() if v == max_foto] if max_foto > 0 else []

    # PANELEIRO / CARREGADOR DE MOCHILA no ano corrente
    entradas = _panela_entries(db, ano_atual)
    paneleiro_counts: dict[str, int] = {}
    for e in entradas:
        if e["diff"] <= 0:
            continue
        for pid in e["player_ids"]:
            paneleiro_counts[pid] = paneleiro_counts.get(pid, 0) + 1
    paneleiro = [pid for pid, _ in sorted(paneleiro_counts.items(), key=lambda kv: kv[1], reverse=True)[:3]]

    mochila_counts: dict[str, int] = {}
    for e in entradas:
        if e["diff"] >= 0:
            continue
        for pid in e["player_ids"]:
            jogador = jogadores.get(pid)
            if not jogador or (jogador.estrelas or 0) <= 3:
                continue
            mochila_counts[pid] = mochila_counts.get(pid, 0) + 1
    mochila = [pid for pid, _ in sorted(mochila_counts.items(), key=lambda kv: kv[1], reverse=True)[:3]]

    # GRUDENTO: dupla #1 do ano corrente
    duos = _top_duos(db, ano_atual)
    grudento = [duos[0][0], duos[0][1]] if duos else []

    # RIP / APOSENTADO: olham o histórico completo
    hoje = date.today()
    rip, aposentado = [], []
    for pid, data_str in _ultima_participacao(db).items():
        try:
            dias = (hoje - datetime.strptime(data_str, "%Y-%m-%d").date()).days
        except ValueError:
            continue
        if dias > config.dias_para_aposentado:
            aposentado.append(pid)
        elif dias > config.dias_para_rip:
            rip.append(pid)

    cabeca_de_chave = [p.id for p in jogadores.values() if p.estrelas == 5]

    return Badges(
        top1=top1,
        paneleiro=paneleiro,
        mochila=mochila,
        grudento=grudento,
        rip=rip,
        aposentado=aposentado,
        cabeca_de_chave=cabeca_de_chave,
    )


@router.get("/hall-da-fama", response_model=list[HallPeriodo])
def hall_da_fama(modo: str = "anual", db: Session = Depends(get_db)):
    jogadores = {p.id: p for p in db.query(Jogador).all()}
    por_periodo: dict[str, dict[str, int]] = {}
    for r in rodadas_oficiais(db):
        if r.vencedor == -1:
            continue
        time = next((t for t in r.times if t.time_index == r.vencedor), None)
        if not time:
            continue
        periodo = ano_de(r.data) if modo == "anual" else r.data[:7]
        if not periodo:
            continue
        por_periodo.setdefault(periodo, {})
        for pid in time.player_ids:
            por_periodo[periodo][pid] = por_periodo[periodo].get(pid, 0) + 1

    resultado = []
    for periodo in sorted(por_periodo.keys(), reverse=True):
        contagens = por_periodo[periodo]
        maximo = max(contagens.values())
        vencedores = [
            HallVencedor(
                id=pid,
                nome=jogadores[pid].nome if pid in jogadores else "(removido)",
                apelido=(jogadores[pid].apelido or "") if pid in jogadores else "",
                count=c,
            )
            for pid, c in contagens.items()
            if c == maximo
        ]
        resultado.append(HallPeriodo(periodo=periodo, vencedores=vencedores))
    return resultado
