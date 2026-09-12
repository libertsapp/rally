"""Porta em Python do algoritmo de sorteio de times (draftBalanced e cia.),
originalmente em JavaScript em legado-referencia/volei-dashboard.html.

Módulo puro: não depende de banco nem de FastAPI. Recebe e devolve apenas
JogadorSorteio e estruturas simples (listas, dicts).
"""

from __future__ import annotations

import random
import re
from datetime import datetime
from typing import Iterable, Optional

from app.sorteio.modelos import JogadorSorteio


def peso_de(jogador: JogadorSorteio) -> float:
    return jogador.estrelas if jogador and jogador.estrelas > 0 else 3


def soma_time(time: list[JogadorSorteio]) -> float:
    return sum(peso_de(p) for p in time)


def peso_altura(jogador: JogadorSorteio) -> int:
    if not jogador or not jogador.porte:
        return 1
    if jogador.porte == "G":
        return 2
    if jogador.porte == "P":
        return 0
    return 1  # M


def troca_viola_grupo(
    grupos_map: Optional[dict[str, int]],
    time_destino: list[JogadorSorteio],
    jogador_que_entra: JogadorSorteio,
    jogador_que_sai: JogadorSorteio,
) -> bool:
    if grupos_map is None:
        return False
    meu_grupo = grupos_map.get(jogador_que_entra.id)
    if meu_grupo is None:
        return False
    return any(
        q.id != jogador_que_sai.id and grupos_map.get(q.id) == meu_grupo
        for q in time_destino
    )


def _to_timestamp(iso: str) -> float:
    if isinstance(iso, str):
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", iso)
        if m:
            ano, mes, dia = (int(x) for x in m.groups())
            return datetime(ano, mes, dia).timestamp()
    try:
        return datetime.fromisoformat(str(iso)).timestamp()
    except ValueError:
        return 0


def draft_balanced(
    players: list[JogadorSorteio],
    num_times: int,
    grupos_para_este_sorteio: Optional[list[list[JogadorSorteio]]] = None,
    recent_counts: Optional[dict[frozenset[str], int]] = None,
) -> list[list[JogadorSorteio]]:
    """Porta de draftBalanced: monta os times respeitando cota de mulheres, teto
    de cabeças de chave (5 estrelas), equilíbrio de nota e de altura, e
    anti-repetição de duplas — e, se vier de "grupos por nível"
    (`grupos_para_este_sorteio`), garante que ninguém do mesmo grupo caia no
    mesmo time."""
    embaralhados = players[:]
    random.shuffle(embaralhados)
    ordenados = sorted(embaralhados, key=peso_de, reverse=True)
    total = len(ordenados)

    base, resto = divmod(total, num_times)
    com_vaga_extra = set(random.sample(range(num_times), resto))
    tamanho_alvo = [base + (1 if i in com_vaga_extra else 0) for i in range(num_times)]

    total_mulheres = sum(1 for p in ordenados if p.sexo == "F")
    fem_base, fem_resto = divmod(total_mulheres, num_times)
    fem_com_extra = set(random.sample(range(num_times), fem_resto))
    female_alvo = [fem_base + (1 if i in fem_com_extra else 0) for i in range(num_times)]

    total_cinco_estrelas = sum(1 for p in ordenados if p.estrelas == 5)
    teto_cinco_estrelas = (
        0 if total_cinco_estrelas == 0 else max(1, -(-total_cinco_estrelas // num_times))
    )

    teams: list[list[JogadorSorteio]] = [[] for _ in range(num_times)]
    mulheres_por_time = [0] * num_times
    cinco_por_time = [0] * num_times

    idx = random.randrange(num_times)
    direcao = random.choice([1, -1])

    def proxima_vaga() -> int:
        nonlocal idx, direcao
        escolhida = idx
        idx += direcao
        if idx >= num_times:
            idx = num_times - 1
            direcao = -1
        elif idx < 0:
            idx = 0
            direcao = 1
        return escolhida

    def cabe(time: int, p: JogadorSorteio, respeitar_cinco: bool, respeitar_mulher: bool) -> bool:
        if len(teams[time]) >= tamanho_alvo[time]:
            return False
        if respeitar_mulher and p.sexo == "F" and mulheres_por_time[time] >= female_alvo[time]:
            return False
        if respeitar_cinco and p.estrelas == 5 and cinco_por_time[time] >= teto_cinco_estrelas:
            return False
        return True

    def colocar(time: int, p: JogadorSorteio) -> None:
        teams[time].append(p)
        if p.sexo == "F":
            mulheres_por_time[time] += 1
        if p.estrelas == 5:
            cinco_por_time[time] += 1

    def distribuir(lista: list[JogadorSorteio], respeitar_cinco: bool) -> None:
        for p in lista:
            vaga = None
            for _ in range(num_times):
                candidata = proxima_vaga()
                if cabe(candidata, p, respeitar_cinco, True):
                    vaga = candidata
                    break
            if vaga is None:
                for _ in range(num_times):
                    candidata = proxima_vaga()
                    if cabe(candidata, p, False, True):
                        vaga = candidata
                        break
            if vaga is None:
                candidatos_menores = [
                    i
                    for i in range(num_times)
                    if len(teams[i]) < tamanho_alvo[i]
                    and (p.sexo != "F" or mulheres_por_time[i] < female_alvo[i])
                ]
                if candidatos_menores:
                    vaga = candidatos_menores[0]
                else:
                    vaga = min(range(num_times), key=lambda i: len(teams[i]))
            colocar(vaga, p)

    grupos_map: Optional[dict[str, int]] = None
    if grupos_para_este_sorteio:
        id_para_grupo: dict[str, int] = {}
        for gi, grupo in enumerate(grupos_para_este_sorteio):
            for p in grupo:
                id_para_grupo[p.id] = gi
        grupos_clonados: list[list[JogadorSorteio]] = [[] for _ in grupos_para_este_sorteio]
        for p in ordenados:
            gi = id_para_grupo.get(p.id)
            if gi is not None:
                grupos_clonados[gi].append(p)
        grupos_map = {}
        for gi, grupo in enumerate(grupos_clonados):
            for p in grupo:
                grupos_map[p.id] = gi

        for grupo in grupos_clonados:
            jogadores_do_grupo = grupo[:]
            random.shuffle(jogadores_do_grupo)
            times_usados_nesse_grupo: set[int] = set()
            for p in jogadores_do_grupo:
                candidatos = [i for i in range(num_times) if i not in times_usados_nesse_grupo]
                random.shuffle(candidatos)
                vaga = next((i for i in candidatos if cabe(i, p, True, True)), None)
                if vaga is None:
                    vaga = next((i for i in candidatos if cabe(i, p, False, True)), None)
                if vaga is None:
                    # afrouxa por último o tamanho-alvo do time (equilibrar_times ajusta
                    # isso depois) — mas NUNCA escolhe um time fora de `candidatos`, ou
                    # seja, nunca repete grupo. Como `candidatos` sempre tem pelo menos
                    # 1 time (grupo nunca é maior que num_times), sempre há vaga aqui.
                    vaga = min(candidatos, key=lambda i: len(teams[i]))
                colocar(vaga, p)
                times_usados_nesse_grupo.add(vaga)
    else:
        mulheres = [p for p in ordenados if p.sexo == "F"]
        homens = [p for p in ordenados if p.sexo != "F"]
        distribuir(mulheres, True)
        distribuir(homens, True)

    equilibrar_times(teams, num_times, teto_cinco_estrelas, grupos_map)
    reforcar_time_com_mais_mulheres(teams, teto_cinco_estrelas, grupos_map)
    equilibrar_altura(teams, num_times, teto_cinco_estrelas, grupos_map)
    evitar_duplas_repetidas(
        teams, num_times, teto_cinco_estrelas, grupos_map, recent_counts or {}
    )

    random.shuffle(teams)
    return teams


def equilibrar_times(
    teams: list[list[JogadorSorteio]],
    num_times: int,
    teto_cinco_estrelas: int,
    grupos_map: Optional[dict[str, int]],
) -> None:
    """Troca jogadores entre o time mais forte e o mais fraco (mesmo sexo) pra
    reduzir a diferença de soma de notas. Muda `teams` in place."""
    for _ in range(40):
        max_t, min_t = 0, 0
        for i in range(1, num_times):
            if soma_time(teams[i]) > soma_time(teams[max_t]):
                max_t = i
            if soma_time(teams[i]) < soma_time(teams[min_t]):
                min_t = i
        diff_atual = soma_time(teams[max_t]) - soma_time(teams[min_t])
        if max_t == min_t or diff_atual <= 1:
            break

        melhor_troca = None
        melhor_diff = diff_atual
        for ia, pa in enumerate(teams[max_t]):
            for ib, pb in enumerate(teams[min_t]):
                if pa.sexo != pb.sexo:
                    continue
                if troca_viola_grupo(
                    grupos_map, teams[min_t], pa, pb
                ) or troca_viola_grupo(grupos_map, teams[max_t], pb, pa):
                    continue
                pa_cinco, pb_cinco = pa.estrelas == 5, pb.estrelas == 5
                if pa_cinco != pb_cinco:
                    cinco_max = (
                        sum(1 for p in teams[max_t] if p.estrelas == 5)
                        - (1 if pa_cinco else 0)
                        + (1 if pb_cinco else 0)
                    )
                    cinco_min = (
                        sum(1 for p in teams[min_t] if p.estrelas == 5)
                        - (1 if pb_cinco else 0)
                        + (1 if pa_cinco else 0)
                    )
                    if cinco_max > teto_cinco_estrelas or cinco_min > teto_cinco_estrelas:
                        continue
                nova_soma_max = soma_time(teams[max_t]) - peso_de(pa) + peso_de(pb)
                nova_soma_min = soma_time(teams[min_t]) - peso_de(pb) + peso_de(pa)
                novo_diff = abs(nova_soma_max - nova_soma_min)
                if novo_diff < melhor_diff:
                    melhor_diff = novo_diff
                    melhor_troca = (ia, ib)
        if melhor_troca is None:
            break
        ia, ib = melhor_troca
        teams[max_t][ia], teams[min_t][ib] = teams[min_t][ib], teams[max_t][ia]


def reforcar_time_com_mais_mulheres(
    teams: list[list[JogadorSorteio]],
    teto_cinco_estrelas: int,
    grupos_map: Optional[dict[str, int]],
) -> None:
    """Quando a cota de mulheres não pôde ficar 100% igual entre os times, o(s)
    time(s) com MAIS mulheres deve(m) ficar com a maior soma de notas — mesmo que
    isso deixe os outros times um pouco menos parelhos entre si. Muda `teams`
    in place."""
    fem_counts = [sum(1 for p in t if p.sexo == "F") for t in teams]
    max_fem, min_fem = max(fem_counts), min(fem_counts)
    if max_fem == min_fem:
        return

    for team_forte, time in enumerate(teams):
        if fem_counts[team_forte] != max_fem:
            continue
        for _ in range(30):
            somas = [soma_time(t) for t in teams]
            max_soma = max(somas)
            if somas[team_forte] >= max_soma:
                break
            doador = somas.index(max_soma)
            if doador == team_forte:
                break

            melhor_troca = None
            melhor_ganho = 0
            for i_fraco, p_fraco in enumerate(teams[team_forte]):
                for i_forte, p_forte in enumerate(teams[doador]):
                    if p_fraco.sexo != p_forte.sexo:
                        continue
                    if troca_viola_grupo(
                        grupos_map, teams[team_forte], p_forte, p_fraco
                    ) or troca_viola_grupo(grupos_map, teams[doador], p_fraco, p_forte):
                        continue
                    cinco_forte = (
                        sum(1 for p in teams[team_forte] if p.estrelas == 5)
                        - (1 if p_fraco.estrelas == 5 else 0)
                        + (1 if p_forte.estrelas == 5 else 0)
                    )
                    cinco_doador = (
                        sum(1 for p in teams[doador] if p.estrelas == 5)
                        - (1 if p_forte.estrelas == 5 else 0)
                        + (1 if p_fraco.estrelas == 5 else 0)
                    )
                    if cinco_forte > teto_cinco_estrelas or cinco_doador > teto_cinco_estrelas:
                        continue
                    ganho = peso_de(p_forte) - peso_de(p_fraco)
                    if ganho > melhor_ganho:
                        melhor_ganho = ganho
                        melhor_troca = (i_fraco, i_forte)
            if melhor_troca is None:
                break
            i_fraco, i_forte = melhor_troca
            teams[team_forte][i_fraco], teams[doador][i_forte] = (
                teams[doador][i_forte],
                teams[team_forte][i_fraco],
            )


def equilibrar_altura(
    teams: list[list[JogadorSorteio]],
    num_times: int,
    teto_cinco_estrelas: int,
    grupos_map: Optional[dict[str, int]],
) -> None:
    """Ajuste fino de altura, DEPOIS do equilíbrio de notas — só troca jogador se
    isso não piorar o equilíbrio de notas já alcançado em mais de 1 ponto. Muda
    `teams` in place."""
    for _ in range(20):
        melhor = None
        melhor_ganho = 0
        for ta in range(num_times):
            for tb in range(ta + 1, num_times):
                altura_ta = sum(peso_altura(p) for p in teams[ta])
                altura_tb = sum(peso_altura(p) for p in teams[tb])
                gap_antes = abs(altura_ta - altura_tb)
                diff_notas_antes = abs(soma_time(teams[ta]) - soma_time(teams[tb]))
                for ia, pa in enumerate(teams[ta]):
                    for ib, pb in enumerate(teams[tb]):
                        if pa.sexo != pb.sexo:
                            continue
                        if troca_viola_grupo(
                            grupos_map, teams[tb], pa, pb
                        ) or troca_viola_grupo(grupos_map, teams[ta], pb, pa):
                            continue
                        pa_cinco, pb_cinco = pa.estrelas == 5, pb.estrelas == 5
                        if pa_cinco != pb_cinco:
                            cinco_a = (
                                sum(1 for p in teams[ta] if p.estrelas == 5)
                                - (1 if pa_cinco else 0)
                                + (1 if pb_cinco else 0)
                            )
                            cinco_b = (
                                sum(1 for p in teams[tb] if p.estrelas == 5)
                                - (1 if pb_cinco else 0)
                                + (1 if pa_cinco else 0)
                            )
                            if cinco_a > teto_cinco_estrelas or cinco_b > teto_cinco_estrelas:
                                continue
                        nova_altura_ta = altura_ta - peso_altura(pa) + peso_altura(pb)
                        nova_altura_tb = altura_tb - peso_altura(pb) + peso_altura(pa)
                        ganho = gap_antes - abs(nova_altura_ta - nova_altura_tb)
                        if ganho <= 0:
                            continue
                        novo_ta = teams[ta][:]
                        novo_ta[ia] = pb
                        novo_tb = teams[tb][:]
                        novo_tb[ib] = pa
                        diff_notas_depois = abs(soma_time(novo_ta) - soma_time(novo_tb))
                        if diff_notas_depois > diff_notas_antes + 1:
                            continue
                        if ganho > melhor_ganho:
                            melhor_ganho = ganho
                            melhor = (ta, tb, ia, ib)
        if melhor is None:
            break
        ta, tb, ia, ib = melhor
        teams[ta][ia], teams[tb][ib] = teams[tb][ib], teams[ta][ia]


def evitar_duplas_repetidas(
    teams: list[list[JogadorSorteio]],
    num_times: int,
    teto_cinco_estrelas: int,
    grupos_map: Optional[dict[str, int]],
    recent_counts: dict[frozenset[str], int],
) -> None:
    """Tenta separar duplas que já jogaram muito juntas recentemente, trocando
    jogadores entre times — só troca se isso não piorar o equilíbrio de notas em
    mais de 1 ponto. `recent_counts` vem de `contar_duplas_recentes`. Muda `teams`
    in place."""
    if not recent_counts:
        return

    def penalidade_time(time: list[JogadorSorteio]) -> int:
        p = 0
        for i in range(len(time)):
            for j in range(i + 1, len(time)):
                p += recent_counts.get(frozenset({time[i].id, time[j].id}), 0)
        return p

    for _ in range(20):
        melhor = None
        melhor_ganho = 0
        for ta in range(num_times):
            for tb in range(ta + 1, num_times):
                pen_antes = penalidade_time(teams[ta]) + penalidade_time(teams[tb])
                diff_antes = abs(soma_time(teams[ta]) - soma_time(teams[tb]))
                for ia, pa in enumerate(teams[ta]):
                    for ib, pb in enumerate(teams[tb]):
                        if pa.sexo != pb.sexo:
                            continue
                        if troca_viola_grupo(
                            grupos_map, teams[tb], pa, pb
                        ) or troca_viola_grupo(grupos_map, teams[ta], pb, pa):
                            continue
                        pa_cinco, pb_cinco = pa.estrelas == 5, pb.estrelas == 5
                        if pa_cinco != pb_cinco:
                            cinco_a = (
                                sum(1 for p in teams[ta] if p.estrelas == 5)
                                - (1 if pa_cinco else 0)
                                + (1 if pb_cinco else 0)
                            )
                            cinco_b = (
                                sum(1 for p in teams[tb] if p.estrelas == 5)
                                - (1 if pb_cinco else 0)
                                + (1 if pa_cinco else 0)
                            )
                            if cinco_a > teto_cinco_estrelas or cinco_b > teto_cinco_estrelas:
                                continue
                        novo_ta = teams[ta][:]
                        novo_ta[ia] = pb
                        novo_tb = teams[tb][:]
                        novo_tb[ib] = pa
                        ganho = pen_antes - (
                            penalidade_time(novo_ta) + penalidade_time(novo_tb)
                        )
                        diff_depois = abs(soma_time(novo_ta) - soma_time(novo_tb))
                        if ganho > melhor_ganho and diff_depois <= diff_antes + 1:
                            melhor_ganho = ganho
                            melhor = (ta, tb, ia, ib)
        if melhor is None:
            break
        ta, tb, ia, ib = melhor
        teams[ta][ia], teams[tb][ib] = teams[tb][ib], teams[ta][ia]


def contar_duplas_recentes(
    rounds: Iterable[dict], limite_qtd_rodadas: int
) -> dict[frozenset[str], int]:
    recentes = sorted(rounds, key=lambda r: _to_timestamp(r["data"]), reverse=True)[
        :limite_qtd_rodadas
    ]
    counts: dict[frozenset[str], int] = {}
    for r in recentes:
        for time in r["times"]:
            ids = [i for i in time.get("playerIds", []) if i]
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    chave = frozenset({ids[i], ids[j]})
                    counts[chave] = counts.get(chave, 0) + 1
    return counts
