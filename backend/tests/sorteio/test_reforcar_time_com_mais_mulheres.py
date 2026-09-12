from app.sorteio.modelos import JogadorSorteio
from app.sorteio.draft import reforcar_time_com_mais_mulheres, soma_time


def jogador(id, estrelas, sexo="M"):
    return JogadorSorteio(id=id, nome=f"J{id}", estrelas=estrelas, sexo=sexo)


def test_nao_faz_nada_quando_todos_os_times_tem_o_mesmo_numero_de_mulheres():
    time_a = [jogador("1", 5, sexo="F")]
    time_b = [jogador("2", 1, sexo="F")]
    teams = [time_a, time_b]

    reforcar_time_com_mais_mulheres(teams, teto_cinco_estrelas=2, grupos_map=None)

    assert teams[0][0].id == "1"
    assert teams[1][0].id == "2"


def test_time_com_mais_mulheres_fica_com_a_maior_soma_de_notas():
    # time_a tem 2 mulheres (mais que time_b, que tem 0) — time_a deve terminar
    # com soma de notas >= time_b, mesmo que isso troque um homem fraco por um forte
    time_a = [jogador("f1", 5, sexo="F"), jogador("f2", 5, sexo="F"), jogador("fraco", 1, sexo="M")]
    time_b = [jogador("forte", 5, sexo="M"), jogador("m1", 1, sexo="M"), jogador("m2", 1, sexo="M")]
    teams = [time_a, time_b]

    reforcar_time_com_mais_mulheres(teams, teto_cinco_estrelas=3, grupos_map=None)

    assert soma_time(teams[0]) >= soma_time(teams[1])
    # a troca só pode ter sido entre homens (mesmo sexo) — mulheres continuam intactas
    assert sum(1 for p in teams[0] if p.sexo == "F") == 2
