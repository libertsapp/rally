from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _criar_jogador(nome):
    return client.post("/jogadores", json={"nome": nome}).json()["id"]


def _criar_rodada(data, times, rascunho=False, vencedor=0):
    return client.post(
        "/rodadas",
        json={"data": data, "rascunho": rascunho, "vencedor": vencedor, "times": times},
    ).json()


def test_ranking_conta_jogos_titulos_e_vitorias_de_partida():
    ana = _criar_jogador("Ana")
    bia = _criar_jogador("Bia")

    # rodada 1: Ana campeã (time 0), 2 vitórias de partida
    _criar_rodada(
        "2024-03-01",
        [
            {"nome": "Time 1", "player_ids": [ana], "vitorias": 2},
            {"nome": "Time 2", "player_ids": [bia], "vitorias": 1},
        ],
        vencedor=0,
    )
    # rodada 2: Bia campeã (time 1)
    _criar_rodada(
        "2024-03-08",
        [
            {"nome": "Time 1", "player_ids": [ana], "vitorias": 0},
            {"nome": "Time 2", "player_ids": [bia], "vitorias": 2},
        ],
        vencedor=1,
    )

    ranking = client.get("/ranking", params={"ano": 2024}).json()

    por_id = {r["id"]: r for r in ranking}
    assert por_id[ana]["jogos"] == 2
    assert por_id[ana]["titulos"] == 1
    assert por_id[ana]["vitorias_partidas"] == 2
    assert por_id[ana]["pct"] == 50

    assert por_id[bia]["jogos"] == 2
    assert por_id[bia]["titulos"] == 1
    assert por_id[bia]["vitorias_partidas"] == 3


def test_ranking_ignora_rodadas_de_outro_ano():
    ana = _criar_jogador("AnaOutroAno")
    _criar_rodada("2023-01-01", [{"nome": "Time 1", "player_ids": [ana], "vitorias": 1}], vencedor=0)

    ranking = client.get("/ranking", params={"ano": 2024}).json()

    assert not any(r["id"] == ana for r in ranking)


def test_ranking_ignora_rascunho():
    ana = _criar_jogador("AnaRascunho")
    _criar_rodada(
        "2024-04-01",
        [{"nome": "Time 1", "player_ids": [ana], "vitorias": 1}],
        rascunho=True,
        vencedor=0,
    )

    ranking = client.get("/ranking", params={"ano": 2024}).json()

    assert not any(r["id"] == ana for r in ranking)


def test_ranking_ordena_por_titulos_depois_vitorias_depois_pct():
    a = _criar_jogador("A")
    b = _criar_jogador("B")
    # A: 1 jogo, 1 título (100%) | B: 1 jogo, 0 títulos
    _criar_rodada(
        "2024-05-01",
        [
            {"nome": "Time 1", "player_ids": [a], "vitorias": 0},
            {"nome": "Time 2", "player_ids": [b], "vitorias": 0},
        ],
        vencedor=0,
    )

    ranking = client.get("/ranking", params={"ano": 2024}).json()
    ids_em_ordem = [r["id"] for r in ranking if r["id"] in (a, b)]

    assert ids_em_ordem == [a, b]


def test_ranking_ignora_convidado_sem_cadastro_de_jogador():
    ana = _criar_jogador("AnaComConvidado")
    _criar_rodada(
        "2024-06-01",
        [{"nome": "Time 1", "player_ids": [ana, "convidado-avulso-id"], "vitorias": 1}],
        vencedor=0,
    )

    ranking = client.get("/ranking", params={"ano": 2024}).json()

    assert not any(r["id"] == "convidado-avulso-id" for r in ranking)
