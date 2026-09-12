from datetime import date, timedelta

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _criar_jogador(nome, estrelas=3, sexo="M"):
    return client.post("/jogadores", json={"nome": nome, "estrelas": estrelas, "sexo": sexo}).json()["id"]


def _criar_rodada(data, times, rascunho=False, vencedor=0):
    return client.post(
        "/rodadas", json={"data": data, "rascunho": rascunho, "vencedor": vencedor, "times": times}
    ).json()


def _dias_atras(n):
    return (date.today() - timedelta(days=n)).isoformat()


def test_badges_cabeca_de_chave_e_nota_maxima_sem_depender_de_rodada():
    campeao = _criar_jogador("CabecaDeChave", estrelas=5)

    badges = client.get("/badges").json()

    assert campeao in badges["cabeca_de_chave"]


def test_badges_top1_e_quem_mais_saiu_campeao_no_ano_corrente():
    ano = str(date.today().year)
    top = _criar_jogador("Top1Badge")
    outro = _criar_jogador("OutroBadge")
    _criar_rodada(
        f"{ano}-02-01",
        [{"nome": "Time 1", "player_ids": [top], "vitorias": 0}, {"nome": "Time 2", "player_ids": [outro], "vitorias": 0}],
        vencedor=0,
    )

    badges = client.get("/badges").json()

    assert top in badges["top1"]
    assert outro not in badges["top1"]


def test_badges_rip_e_aposentado_pelos_dias_sem_jogar():
    rip = _criar_jogador("RipBadge")
    aposentado = _criar_jogador("AposentadoBadge")
    _criar_rodada(_dias_atras(70), [{"nome": "Time 1", "player_ids": [rip], "vitorias": 0}], vencedor=-1)
    _criar_rodada(
        _dias_atras(150), [{"nome": "Time 1", "player_ids": [aposentado], "vitorias": 0}], vencedor=-1
    )

    badges = client.get("/badges").json()

    assert rip in badges["rip"]
    assert aposentado in badges["aposentado"]
    assert aposentado not in badges["rip"]


def test_badges_grudento_e_a_dupla_mais_sorteada_no_ano_corrente():
    ano = str(date.today().year)
    a = _criar_jogador("GrudentoA")
    b = _criar_jogador("GrudentoB")
    _criar_rodada(f"{ano}-03-01", [{"nome": "Time 1", "player_ids": [a, b], "vitorias": 0}], vencedor=-1)
    _criar_rodada(f"{ano}-03-08", [{"nome": "Time 1", "player_ids": [a, b], "vitorias": 0}], vencedor=-1)

    badges = client.get("/badges").json()

    assert a in badges["grudento"]
    assert b in badges["grudento"]


def test_hall_da_fama_agrupa_campeoes_por_ano():
    ano = str(date.today().year)
    campeao = _criar_jogador("HallCampeao")
    _criar_rodada(f"{ano}-01-15", [{"nome": "Time 1", "player_ids": [campeao], "vitorias": 0}], vencedor=0)

    hall = client.get("/hall-da-fama", params={"modo": "anual"}).json()

    periodo = next(p for p in hall if p["periodo"] == ano)
    ids_vencedores = [v["id"] for v in periodo["vencedores"]]
    assert campeao in ids_vencedores


def test_hall_da_fama_agrupa_campeoes_por_mes():
    ano = str(date.today().year)
    campeao = _criar_jogador("HallCampeaoMes")
    _criar_rodada(f"{ano}-06-01", [{"nome": "Time 1", "player_ids": [campeao], "vitorias": 0}], vencedor=0)

    hall = client.get("/hall-da-fama", params={"modo": "mensal"}).json()

    periodo = next(p for p in hall if p["periodo"] == f"{ano}-06")
    ids_vencedores = [v["id"] for v in periodo["vencedores"]]
    assert campeao in ids_vencedores
