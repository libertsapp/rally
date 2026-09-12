"""Regressão de um caso real encontrado pela suíte de 200 simulações: quando os
times têm tamanhos-alvo desiguais e um grupo do tamanho de um time inteiro é
processado depois que times menores já encheram, o fallback de "segurança
extrema" do algoritmo original (JS) podia repetir grupo mesmo quando existia uma
alternativa sem violação. Ver conversa/registro da sessão para a reprodução."""

import random

from app.sorteio.modelos import JogadorSorteio
from app.sorteio.draft import draft_balanced
from app.sorteio.grupos import montar_grupos


def _elenco_do_seed_18():
    random.seed(18)
    tamanho = random.randint(8, 30)
    jogadores = []
    for i in range(tamanho):
        estrelas = random.choice([1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
        sexo = random.choice(["F", "M", "M"])
        porte = random.choice(["P", "M", "G", ""])
        jogadores.append(
            JogadorSorteio(id=f"p{i}", nome=f"J{i}", estrelas=estrelas, sexo=sexo, porte=porte)
        )
    num_times = random.choice([2, 3, 4])
    return jogadores, num_times


def test_grupo_cheio_processado_por_ultimo_nao_repete_grupo_no_mesmo_time():
    jogadores, num_times = _elenco_do_seed_18()
    grupos = montar_grupos(jogadores, num_times)

    teams = draft_balanced(jogadores, num_times, grupos_para_este_sorteio=grupos)

    id_para_grupo = {p.id: gi for gi, grupo in enumerate(grupos) for p in grupo}
    for time in teams:
        grupos_no_time = [id_para_grupo[p.id] for p in time]
        assert len(grupos_no_time) == len(set(grupos_no_time)), (
            f"time com 2+ jogadores do mesmo grupo: {[(p.id, id_para_grupo[p.id]) for p in time]}"
        )
