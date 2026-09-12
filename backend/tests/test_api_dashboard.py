from datetime import date, timedelta

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _criar_jogador(nome, estrelas=3, sexo="M"):
    return client.post("/jogadores", json={"nome": nome, "estrelas": estrelas, "sexo": sexo}).json()["id"]


def _criar_rodada(data, times, rascunho=False, vencedor=0):
    return client.post(
        "/rodadas",
        json={"data": data, "rascunho": rascunho, "vencedor": vencedor, "times": times},
    ).json()


def _dias_atras(n):
    return (date.today() - timedelta(days=n)).isoformat()


def test_resumo_conta_dias_jogados_e_campeao_da_semana():
    ana = _criar_jogador("AnaResumo")
    bia = _criar_jogador("BiaResumo")
    ano_atual = str(date.today().year)
    hoje = date.today().isoformat()

    _criar_rodada(
        hoje,
        [
            {"nome": "Time 1", "player_ids": [ana], "vitorias": 2},
            {"nome": "Time 2", "player_ids": [bia], "vitorias": 0},
        ],
        vencedor=0,
    )

    resumo = client.get("/dashboard/resumo").json()

    assert resumo["ano"] == ano_atual
    assert resumo["dias_jogados_no_ano"] >= 1
    assert resumo["campeao_semana"]["time_nome"] == "Time 1"
    assert ana in resumo["campeao_semana"]["player_ids"]


def test_mais_vezes_na_foto_ordena_por_quantidade():
    campeao = _criar_jogador("CampeaoFoto")
    perdedor = _criar_jogador("PerdedorFoto")
    ano = "2024"
    for i in range(3):
        _criar_rodada(
            f"2024-02-0{i+1}",
            [
                {"nome": "Time 1", "player_ids": [campeao], "vitorias": 1},
                {"nome": "Time 2", "player_ids": [perdedor], "vitorias": 0},
            ],
            vencedor=0,
        )

    lista = client.get("/dashboard/mais-vezes-na-foto", params={"ano": ano}).json()
    por_id = {d["id"]: d for d in lista}

    assert por_id[campeao]["vezes"] == 3
    assert perdedor not in por_id  # nunca foi campeão, não aparece (vezes>0 só)


def test_duplas_mais_sorteadas_conta_pares_no_mesmo_time():
    a = _criar_jogador("DuplaA")
    b = _criar_jogador("DuplaB")
    _criar_rodada("2024-03-01", [{"nome": "Time 1", "player_ids": [a, b], "vitorias": 0}], vencedor=-1)
    _criar_rodada("2024-03-08", [{"nome": "Time 1", "player_ids": [a, b], "vitorias": 0}], vencedor=-1)

    lista = client.get("/dashboard/duplas-mais-sorteadas", params={"ano": "2024"}).json()

    dupla = next(d for d in lista if {d["id1"], d["id2"]} == {a, b})
    assert dupla["count"] == 2


def test_panelas_calcula_diferenca_de_media_entre_times():
    forte1 = _criar_jogador("Forte1", estrelas=5)
    forte2 = _criar_jogador("Forte2", estrelas=5)
    fraco1 = _criar_jogador("Fraco1", estrelas=1)
    fraco2 = _criar_jogador("Fraco2", estrelas=1)
    _criar_rodada(
        "2024-04-01",
        [
            {"nome": "Panela", "player_ids": [forte1, forte2], "vitorias": 0},
            {"nome": "Zebra", "player_ids": [fraco1, fraco2], "vitorias": 0},
        ],
        vencedor=-1,
    )

    lista = client.get("/dashboard/panelas", params={"ano": "2024"}).json()

    panela = next(p for p in lista if p["time_nome"] == "Panela")
    assert panela["diff"] == 4  # média 5 contra média 1


def test_ausentes_classifica_rip_e_aposentado_pelos_dias_sem_jogar():
    ausente_rip = _criar_jogador("AusenteRip")
    ausente_aposentado = _criar_jogador("AusenteAposentado")
    ativo = _criar_jogador("Ativo")

    _criar_rodada(_dias_atras(70), [{"nome": "Time 1", "player_ids": [ausente_rip], "vitorias": 0}], vencedor=-1)
    _criar_rodada(
        _dias_atras(150), [{"nome": "Time 1", "player_ids": [ausente_aposentado], "vitorias": 0}], vencedor=-1
    )
    _criar_rodada(_dias_atras(1), [{"nome": "Time 1", "player_ids": [ativo], "vitorias": 0}], vencedor=-1)

    lista = client.get("/dashboard/ausentes").json()
    por_id = {a["id"]: a for a in lista}

    assert por_id[ausente_rip]["status"] == "rip"
    assert por_id[ausente_aposentado]["status"] == "aposentado"
    assert ativo not in por_id
