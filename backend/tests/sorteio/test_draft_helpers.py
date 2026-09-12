from app.sorteio.modelos import JogadorSorteio
from app.sorteio.draft import (
    peso_de,
    soma_time,
    troca_viola_grupo,
    peso_altura,
    contar_duplas_recentes,
)


def jogador(id, estrelas=3, sexo="", porte=""):
    return JogadorSorteio(id=id, nome=f"J{id}", estrelas=estrelas, sexo=sexo, porte=porte)


def test_peso_de_usa_estrelas_quando_maior_que_zero():
    assert peso_de(jogador("1", estrelas=4)) == 4


def test_peso_de_usa_tres_como_peso_neutro_quando_sem_estrelas():
    assert peso_de(jogador("1", estrelas=0)) == 3


def test_soma_time_soma_peso_de_cada_jogador():
    time = [jogador("1", estrelas=5), jogador("2", estrelas=0), jogador("3", estrelas=2)]
    # pesos: 5 + 3 (neutro) + 2 = 10
    assert soma_time(time) == 10


def test_peso_altura_porte_grande_pesa_dois():
    assert peso_altura(jogador("1", porte="G")) == 2


def test_peso_altura_porte_pequeno_pesa_zero():
    assert peso_altura(jogador("1", porte="P")) == 0


def test_peso_altura_porte_medio_ou_vazio_pesa_um():
    assert peso_altura(jogador("1", porte="M")) == 1
    assert peso_altura(jogador("1", porte="")) == 1


def test_troca_viola_grupo_falso_quando_nao_ha_mapa_de_grupos():
    time_destino = [jogador("2")]
    assert troca_viola_grupo(None, time_destino, jogador("1"), jogador("2")) is False


def test_troca_viola_grupo_verdadeiro_quando_alguem_do_mesmo_grupo_ja_esta_no_time():
    grupos_map = {"1": 0, "2": 0, "3": 1, "5": 1}
    time_destino = [jogador("2"), jogador("3")]
    # jogador "1" é do grupo 0, e "2" (também grupo 0) já está no time destino;
    # quem está saindo do time destino é "5", então "2" continua contando
    assert troca_viola_grupo(grupos_map, time_destino, jogador("1"), jogador("5")) is True


def test_troca_viola_grupo_ignora_o_proprio_jogador_que_esta_saindo():
    grupos_map = {"1": 0, "2": 0}
    time_destino = [jogador("2")]
    # "2" é quem está SAINDO do time destino, então não conta contra "1" entrar
    assert troca_viola_grupo(grupos_map, time_destino, jogador("1"), jogador("2")) is False


def test_contar_duplas_recentes_conta_pares_das_rodadas_mais_recentes():
    rounds = [
        {
            "data": "2024-01-01",
            "times": [{"playerIds": ["1", "2", "3"]}],
        },
        {
            "data": "2024-01-08",
            "times": [{"playerIds": ["1", "2"]}],
        },
    ]
    counts = contar_duplas_recentes(rounds, limite_qtd_rodadas=5)
    assert counts[frozenset({"1", "2"})] == 2
    assert counts[frozenset({"1", "3"})] == 1


def test_contar_duplas_recentes_respeita_limite_de_rodadas_mais_recentes():
    rounds = [
        {"data": "2024-01-01", "times": [{"playerIds": ["1", "2"]}]},
        {"data": "2024-01-08", "times": [{"playerIds": ["3", "4"]}]},
    ]
    counts = contar_duplas_recentes(rounds, limite_qtd_rodadas=1)
    assert frozenset({"1", "2"}) not in counts
    assert counts[frozenset({"3", "4"})] == 1
