from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def rodada_exemplo(data="2024-05-01", rascunho=False, vencedor=0):
    return {
        "data": data,
        "rascunho": rascunho,
        "vencedor": vencedor,
        "times": [
            {"nome": "Time 1", "player_ids": ["1", "2"], "vitorias": 2},
            {"nome": "Time 2", "player_ids": ["3", "4"], "vitorias": 1},
        ],
    }


def test_cria_rodada_e_calcula_vencedor_a_partir_do_indice():
    resposta = client.post("/rodadas", json=rodada_exemplo(vencedor=1))

    assert resposta.status_code == 200
    criada = resposta.json()
    assert criada["vencedor"] == 1
    assert len(criada["times"]) == 2
    assert criada["times"][0]["player_ids"] == ["1", "2"]


def test_cria_rodada_sem_vencedor_retorna_menos_um():
    resposta = client.post("/rodadas", json=rodada_exemplo(vencedor=-1))
    assert resposta.json()["vencedor"] == -1


def test_lista_rodadas():
    client.post("/rodadas", json=rodada_exemplo())
    lista = client.get("/rodadas").json()
    assert len(lista) >= 1


def test_atualiza_rodada_substitui_times():
    criada = client.post("/rodadas", json=rodada_exemplo()).json()

    nova = rodada_exemplo(data="2024-05-08", vencedor=0)
    resposta = client.put(f"/rodadas/{criada['id']}", json=nova)

    assert resposta.status_code == 200
    assert resposta.json()["data"] == "2024-05-08"


def test_remove_rodada():
    criada = client.post("/rodadas", json=rodada_exemplo()).json()

    resposta = client.delete(f"/rodadas/{criada['id']}")

    assert resposta.status_code == 200
    ids = [r["id"] for r in client.get("/rodadas").json()]
    assert criada["id"] not in ids
