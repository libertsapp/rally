from app.sorteio.modelos import JogadorSorteio
from app.sorteio.draft import equilibrar_altura, soma_time, peso_altura


def jogador(id, estrelas=3, sexo="M", porte=""):
    return JogadorSorteio(id=id, nome=f"J{id}", estrelas=estrelas, sexo=sexo, porte=porte)


def soma_altura(time):
    return sum(peso_altura(p) for p in time)


def test_equilibrar_altura_reduz_gap_de_altura_sem_piorar_muito_a_nota():
    # time_a: 2 grandes (G=2 cada) | time_b: 2 pequenos (P=0 cada) — mesma soma de
    # notas (estrelas iguais), então dá pra equilibrar altura livremente
    time_a = [jogador("1", estrelas=3, porte="G"), jogador("2", estrelas=3, porte="G")]
    time_b = [jogador("3", estrelas=3, porte="P"), jogador("4", estrelas=3, porte="P")]
    teams = [time_a, time_b]

    equilibrar_altura(teams, num_times=2, teto_cinco_estrelas=2, grupos_map=None)

    assert abs(soma_altura(teams[0]) - soma_altura(teams[1])) < 4  # gap inicial era 4


def test_equilibrar_altura_nao_troca_sexos_diferentes():
    time_a = [jogador("1", sexo="F", porte="G"), jogador("2", sexo="M", porte="G")]
    time_b = [jogador("3", sexo="F", porte="P"), jogador("4", sexo="M", porte="P")]
    teams = [time_a, time_b]

    equilibrar_altura(teams, num_times=2, teto_cinco_estrelas=2, grupos_map=None)

    for time in teams:
        assert sum(1 for p in time if p.sexo == "F") == 1


def test_equilibrar_altura_nao_piora_diferenca_de_notas_em_mais_de_um_ponto():
    # time_a já tem soma de nota MUITO maior; trocar pra equilibrar altura não pode
    # aumentar ainda mais essa diferença de nota
    time_a = [jogador("1", estrelas=5, porte="G")]
    time_b = [jogador("2", estrelas=1, porte="P")]
    teams = [time_a, time_b]
    diff_notas_antes = abs(soma_time(teams[0]) - soma_time(teams[1]))

    equilibrar_altura(teams, num_times=2, teto_cinco_estrelas=2, grupos_map=None)

    diff_notas_depois = abs(soma_time(teams[0]) - soma_time(teams[1]))
    assert diff_notas_depois <= diff_notas_antes + 1
