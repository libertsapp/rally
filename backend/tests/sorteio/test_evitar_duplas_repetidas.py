from app.sorteio.modelos import JogadorSorteio
from app.sorteio.draft import evitar_duplas_repetidas, soma_time


def jogador(id, estrelas=3, sexo="M"):
    return JogadorSorteio(id=id, nome=f"J{id}", estrelas=estrelas, sexo=sexo)


def test_nao_faz_nada_sem_historico_recente():
    time_a = [jogador("1"), jogador("2")]
    time_b = [jogador("3"), jogador("4")]
    teams = [time_a, time_b]

    evitar_duplas_repetidas(
        teams, num_times=2, teto_cinco_estrelas=2, grupos_map=None, recent_counts={}
    )

    assert teams[0][0].id == "1" and teams[0][1].id == "2"


def test_separa_dupla_que_jogou_muito_junta_recentemente():
    # "1" e "2" jogaram juntos 5 vezes recentemente e caíram no mesmo time de novo —
    # a função deve trocar um deles pra outro time, se isso não piorar muito a nota
    time_a = [jogador("1", estrelas=3), jogador("2", estrelas=3)]
    time_b = [jogador("3", estrelas=3), jogador("4", estrelas=3)]
    teams = [time_a, time_b]
    recent_counts = {frozenset({"1", "2"}): 5}

    evitar_duplas_repetidas(
        teams,
        num_times=2,
        teto_cinco_estrelas=2,
        grupos_map=None,
        recent_counts=recent_counts,
    )

    ids_time_a = {p.id for p in teams[0]}
    assert not {"1", "2"}.issubset(ids_time_a)


def test_nao_piora_diferenca_de_notas_em_mais_de_um_ponto():
    time_a = [jogador("1", estrelas=5), jogador("2", estrelas=5)]
    time_b = [jogador("3", estrelas=1), jogador("4", estrelas=1)]
    teams = [time_a, time_b]
    diff_antes = abs(soma_time(teams[0]) - soma_time(teams[1]))
    recent_counts = {frozenset({"1", "2"}): 5}

    evitar_duplas_repetidas(
        teams,
        num_times=2,
        teto_cinco_estrelas=2,
        grupos_map=None,
        recent_counts=recent_counts,
    )

    diff_depois = abs(soma_time(teams[0]) - soma_time(teams[1]))
    assert diff_depois <= diff_antes + 1
