from app.sorteio.modelos import JogadorSorteio
from app.sorteio.draft import equilibrar_times, soma_time


def jogador(id, estrelas, sexo="M"):
    return JogadorSorteio(id=id, nome=f"J{id}", estrelas=estrelas, sexo=sexo)


def test_equilibrar_times_reduz_diferenca_de_soma_entre_times():
    time_forte = [jogador("1", 5), jogador("2", 5)]
    time_fraco = [jogador("3", 1), jogador("4", 1)]
    teams = [time_forte, time_fraco]

    equilibrar_times(teams, num_times=2, teto_cinco_estrelas=2, grupos_map=None)

    assert abs(soma_time(teams[0]) - soma_time(teams[1])) <= 1


def test_equilibrar_times_nao_troca_jogadores_de_sexos_diferentes():
    time_forte = [jogador("1", 5, sexo="F"), jogador("2", 5, sexo="M")]
    time_fraco = [jogador("3", 1, sexo="F"), jogador("4", 1, sexo="M")]
    teams = [time_forte, time_fraco]

    equilibrar_times(teams, num_times=2, teto_cinco_estrelas=2, grupos_map=None)

    # cada time continua com exatamente 1 mulher e 1 homem
    for time in teams:
        assert sum(1 for p in time if p.sexo == "F") == 1
        assert sum(1 for p in time if p.sexo == "M") == 1


def test_equilibrar_times_nao_move_ninguem_entre_times_do_mesmo_grupo():
    # "1" e "3" são do mesmo grupo (0) — trocar "1" (time 0) por "3" (time 1)
    # deixaria os dois no mesmo time, então essa troca deve ser bloqueada
    time_a = [jogador("1", 5)]
    time_b = [jogador("3", 1)]
    teams = [time_a, time_b]
    grupos_map = {"1": 0, "3": 0}

    equilibrar_times(teams, num_times=2, teto_cinco_estrelas=2, grupos_map=grupos_map)

    # nada mudou: única troca possível violaria o grupo
    assert teams[0][0].id == "1"
    assert teams[1][0].id == "3"
