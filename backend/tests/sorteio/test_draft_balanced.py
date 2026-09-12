from app.sorteio.modelos import JogadorSorteio
from app.sorteio.draft import draft_balanced
from app.sorteio.grupos import montar_grupos


def jogador(id, estrelas=3, sexo="M", porte=""):
    return JogadorSorteio(id=id, nome=f"J{id}", estrelas=estrelas, sexo=sexo, porte=porte)


def test_draft_balanced_distribui_todo_mundo_em_times_do_tamanho_certo():
    jogadores = [jogador(str(i)) for i in range(12)]

    teams = draft_balanced(jogadores, num_times=4)

    assert len(teams) == 4
    assert all(len(t) == 3 for t in teams)
    todos_ids = [p.id for t in teams for p in t]
    assert sorted(todos_ids) == sorted(p.id for p in jogadores)


def test_draft_balanced_distribui_tamanhos_o_mais_parelho_possivel_com_resto():
    jogadores = [jogador(str(i)) for i in range(13)]  # 13 em 4 times = 4/3/3/3

    teams = draft_balanced(jogadores, num_times=4)

    tamanhos = sorted((len(t) for t in teams), reverse=True)
    assert tamanhos == [4, 3, 3, 3]


def test_draft_balanced_respeita_cota_exata_de_mulheres_por_time():
    # 8 mulheres em 4 times = exatamente 2 por time
    jogadores = [jogador(f"f{i}", sexo="F") for i in range(8)] + [
        jogador(f"m{i}", sexo="M") for i in range(8)
    ]

    teams = draft_balanced(jogadores, num_times=4)

    for t in teams:
        assert sum(1 for p in t if p.sexo == "F") == 2


def test_draft_balanced_respeita_teto_de_cabecas_de_chave():
    # 8 jogadores de 5 estrelas em 4 times -> teto = max(1, ceil(8/4)) = 2 por time
    jogadores = [jogador(f"top{i}", estrelas=5) for i in range(8)] + [
        jogador(f"m{i}", estrelas=2) for i in range(8)
    ]

    teams = draft_balanced(jogadores, num_times=4)

    for t in teams:
        assert sum(1 for p in t if p.estrelas == 5) <= 2


def test_draft_balanced_nunca_deixa_dois_do_mesmo_grupo_no_mesmo_time():
    jogadores = [jogador(str(i), estrelas=(i % 5) + 1, sexo="F" if i % 3 == 0 else "M") for i in range(20)]
    grupos = montar_grupos(jogadores, num_times=4)

    teams = draft_balanced(jogadores, num_times=4, grupos_para_este_sorteio=grupos)

    id_para_grupo = {}
    for gi, grupo in enumerate(grupos):
        for p in grupo:
            id_para_grupo[p.id] = gi

    for time in teams:
        grupos_no_time = [id_para_grupo[p.id] for p in time]
        assert len(grupos_no_time) == len(set(grupos_no_time))
