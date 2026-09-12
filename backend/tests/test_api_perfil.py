from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _criar_jogador(nome):
    return client.post("/jogadores", json={"nome": nome}).json()["id"]


def _criar_rodada(data, times, rascunho=False, vencedor=0):
    return client.post(
        "/rodadas", json={"data": data, "rascunho": rascunho, "vencedor": vencedor, "times": times}
    ).json()


def test_perfil_conta_jogos_titulos_e_vitorias():
    ana = _criar_jogador("AnaPerfil")
    bia = _criar_jogador("BiaPerfil")
    _criar_rodada(
        "2024-07-01",
        [
            {"nome": "Time 1", "player_ids": [ana], "vitorias": 2},
            {"nome": "Time 2", "player_ids": [bia], "vitorias": 0},
        ],
        vencedor=0,
    )
    _criar_rodada(
        "2024-07-08",
        [
            {"nome": "Time 1", "player_ids": [ana], "vitorias": 1},
            {"nome": "Time 2", "player_ids": [bia], "vitorias": 1},
        ],
        vencedor=1,
    )

    perfil = client.get(f"/jogadores/{ana}/perfil").json()

    assert perfil["jogos"] == 2
    assert perfil["titulos"] == 1
    assert perfil["vitorias_partidas"] == 3
    assert perfil["pct"] == 50
    assert perfil["rounds"][0]["data"] == "2024-07-08"  # mais recente primeiro


def test_perfil_de_jogador_inexistente_retorna_404():
    resposta = client.get("/jogadores/nao-existe/perfil")
    assert resposta.status_code == 404


def test_perfil_lista_parceiros_mais_frequentes():
    ana = _criar_jogador("AnaParceiros")
    bia = _criar_jogador("BiaParceiros")
    caio = _criar_jogador("CaioParceiros")
    _criar_rodada("2024-08-01", [{"nome": "Time 1", "player_ids": [ana, bia], "vitorias": 0}], vencedor=-1)
    _criar_rodada("2024-08-08", [{"nome": "Time 1", "player_ids": [ana, bia], "vitorias": 0}], vencedor=-1)
    _criar_rodada("2024-08-15", [{"nome": "Time 1", "player_ids": [ana, caio], "vitorias": 0}], vencedor=-1)

    perfil = client.get(f"/jogadores/{ana}/perfil").json()

    parceiros_por_id = {p["id"]: p["count"] for p in perfil["parceiros"]}
    assert parceiros_por_id[bia] == 2
    assert parceiros_por_id[caio] == 1
    assert list(parceiros_por_id.keys())[0] == bia  # mais frequente primeiro


def test_perfil_calcula_serie_de_aproveitamento_em_ordem_cronologica():
    ana = _criar_jogador("AnaSerie")
    _criar_rodada("2024-09-01", [{"nome": "Time 1", "player_ids": [ana], "vitorias": 0}], vencedor=0)
    _criar_rodada("2024-09-08", [{"nome": "Time 1", "player_ids": [ana], "vitorias": 0}], vencedor=-1)

    perfil = client.get(f"/jogadores/{ana}/perfil").json()

    serie = perfil["aproveitamento_series"]
    assert serie[0]["data"] == "2024-09-01"
    assert serie[-1]["data"] == "2024-09-08"
