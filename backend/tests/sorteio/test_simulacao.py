"""Suíte de simulação: reproduz a garantia validada com 200 simulações na versão
JS original — sorteios repetidos, com composições de elenco variadas, nunca devem
violar as invariantes centrais do algoritmo (sobretudo: ninguém do mesmo grupo cai
no mesmo time)."""

import random

from app.sorteio.modelos import JogadorSorteio
from app.sorteio.draft import draft_balanced, peso_de
from app.sorteio.grupos import montar_grupos

NUM_SIMULACOES = 200


def elenco_aleatorio(rng: random.Random) -> list[JogadorSorteio]:
    tamanho = rng.randint(8, 30)
    jogadores = []
    for i in range(tamanho):
        estrelas = rng.choice([1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
        sexo = rng.choice(["F", "M", "M"])  # mais homens que mulheres, como no uso real
        porte = rng.choice(["P", "M", "G", ""])
        jogadores.append(
            JogadorSorteio(id=f"p{i}", nome=f"J{i}", estrelas=estrelas, sexo=sexo, porte=porte)
        )
    return jogadores


def test_200_simulacoes_com_grupos_nunca_deixam_dois_do_mesmo_grupo_no_mesmo_time():
    rng = random.Random(42)
    for _ in range(NUM_SIMULACOES):
        jogadores = elenco_aleatorio(rng)
        num_times = rng.choice([2, 3, 4])
        if len(jogadores) < num_times * 2:
            continue  # elenco pequeno demais pra esse número de times, pula essa rodada

        grupos = montar_grupos(jogadores, num_times)
        teams = draft_balanced(jogadores, num_times, grupos_para_este_sorteio=grupos)

        id_para_grupo = {p.id: gi for gi, grupo in enumerate(grupos) for p in grupo}
        for time in teams:
            grupos_no_time = [id_para_grupo[p.id] for p in time]
            assert len(grupos_no_time) == len(set(grupos_no_time)), (
                f"time com 2+ jogadores do mesmo grupo: {[p.id for p in time]}"
            )


def test_200_simulacoes_sem_grupos_respeitam_tamanho_cota_e_teto():
    rng = random.Random(7)
    for _ in range(NUM_SIMULACOES):
        jogadores = elenco_aleatorio(rng)
        num_times = rng.choice([2, 3, 4])
        if len(jogadores) < num_times:
            continue

        teams = draft_balanced(jogadores, num_times)

        # ninguém sumiu nem duplicou
        todos_ids = [p.id for t in teams for p in t]
        assert sorted(todos_ids) == sorted(p.id for p in jogadores)

        # tamanhos de time nunca diferem em mais de 1
        tamanhos = [len(t) for t in teams]
        assert max(tamanhos) - min(tamanhos) <= 1

        # cota de mulheres nunca difere em mais de 1 entre times
        fem_counts = [sum(1 for p in t if p.sexo == "F") for t in teams]
        assert max(fem_counts) - min(fem_counts) <= 1

        # teto de cabeças de chave nunca é violado
        total_cinco = sum(1 for p in jogadores if p.estrelas == 5)
        if total_cinco:
            teto = max(1, -(-total_cinco // num_times))
            for t in teams:
                assert sum(1 for p in t if p.estrelas == 5) <= teto
