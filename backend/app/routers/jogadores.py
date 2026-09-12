from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.jogador import Jogador
from app.models.organizacao import Organizacao
from app.routers.dashboard import rodadas_oficiais
from app.schemas.jogador import JogadorEntrada, JogadorSaida
from app.schemas.perfil import ParceiroFrequente, PerfilSaida, PontoAproveitamento, RodadaDoPerfil
from app.tenant import get_organizacao_atual

router = APIRouter(prefix="/jogadores", tags=["jogadores"])


@router.get("", response_model=list[JogadorSaida])
def listar_jogadores(db: Session = Depends(get_db), organizacao: Organizacao = Depends(get_organizacao_atual)):
    return db.query(Jogador).filter(Jogador.organizacao_id == organizacao.id).all()


@router.post("", response_model=JogadorSaida)
def criar_jogador(
    dados: JogadorEntrada,
    db: Session = Depends(get_db),
    organizacao: Organizacao = Depends(get_organizacao_atual),
):
    novo = Jogador(**dados.model_dump(), organizacao_id=organizacao.id)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.put("/{jogador_id}", response_model=JogadorSaida)
def atualizar_jogador(
    jogador_id: str,
    dados: JogadorEntrada,
    db: Session = Depends(get_db),
    organizacao: Organizacao = Depends(get_organizacao_atual),
):
    jogador = (
        db.query(Jogador)
        .filter(Jogador.id == jogador_id, Jogador.organizacao_id == organizacao.id)
        .first()
    )
    if not jogador:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    for campo, valor in dados.model_dump().items():
        setattr(jogador, campo, valor)
    db.commit()
    db.refresh(jogador)
    return jogador


@router.delete("/{jogador_id}")
def remover_jogador(
    jogador_id: str,
    db: Session = Depends(get_db),
    organizacao: Organizacao = Depends(get_organizacao_atual),
):
    jogador = (
        db.query(Jogador)
        .filter(Jogador.id == jogador_id, Jogador.organizacao_id == organizacao.id)
        .first()
    )
    if not jogador:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    db.delete(jogador)
    db.commit()
    return {"status": "ok"}


@router.get("/{jogador_id}/perfil", response_model=PerfilSaida)
def perfil_do_jogador(
    jogador_id: str,
    db: Session = Depends(get_db),
    organizacao: Organizacao = Depends(get_organizacao_atual),
):
    jogador = (
        db.query(Jogador)
        .filter(Jogador.id == jogador_id, Jogador.organizacao_id == organizacao.id)
        .first()
    )
    if not jogador:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")

    jogos = titulos = vitorias_partidas = vezes_na_foto = 0
    rounds: list[RodadaDoPerfil] = []
    parceiros_counts: dict[str, int] = {}

    for r in rodadas_oficiais(db, organizacao.id):
        for t in r.times:
            if jogador_id not in t.player_ids:
                continue
            jogos += 1
            is_winner = t.time_index == r.vencedor
            if is_winner:
                titulos += 1
                vezes_na_foto += 1
            vitorias_partidas += t.vitorias or 0
            rounds.append(
                RodadaDoPerfil(data=r.data, time_nome=t.nome, is_winner=is_winner, vitorias=t.vitorias or 0)
            )
            for pid in t.player_ids:
                if pid and pid != jogador_id:
                    parceiros_counts[pid] = parceiros_counts.get(pid, 0) + 1

    rounds.sort(key=lambda x: x.data, reverse=True)
    pct = round((titulos / jogos) * 100) if jogos > 0 else 0

    cronologico = list(reversed(rounds))
    janela = 5
    serie = []
    for i in range(len(cronologico)):
        recorte = cronologico[max(0, i - janela + 1) : i + 1]
        vitorias = sum(1 for x in recorte if x.is_winner)
        serie.append(PontoAproveitamento(data=cronologico[i].data, pct=round((vitorias / len(recorte)) * 100)))

    jogadores_por_id = {
        p.id: p for p in db.query(Jogador).filter(Jogador.organizacao_id == organizacao.id).all()
    }
    parceiros = [
        ParceiroFrequente(id=pid, nome=jogadores_por_id[pid].nome, apelido=jogadores_por_id[pid].apelido or "", count=c)
        for pid, c in sorted(parceiros_counts.items(), key=lambda kv: kv[1], reverse=True)
        if pid in jogadores_por_id
    ][:3]

    return PerfilSaida(
        jogos=jogos,
        titulos=titulos,
        vitorias_partidas=vitorias_partidas,
        vezes_na_foto=vezes_na_foto,
        pct=pct,
        rounds=rounds,
        aproveitamento_series=serie,
        parceiros=parceiros,
    )
