from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _abrir_checkin(data="2024-05-01", travado=False):
    client.put(
        "/config",
        json={"estrelas_visiveis": True, "checkin_data_aberta": data, "checkin_travado": travado},
    )


def _fechar_checkin():
    client.put(
        "/config", json={"estrelas_visiveis": True, "checkin_data_aberta": "", "checkin_travado": False}
    )


def test_confirma_presenca_quando_checkin_esta_aberto():
    _abrir_checkin("2024-05-01")

    resposta = client.post(
        "/checkins", json={"jogador_id": "p1", "jogador_nome": "Ana", "estrelas": 4, "sexo": "F"}
    )

    assert resposta.status_code == 200
    criado = resposta.json()
    assert criado["data"] == "2024-05-01"
    assert criado["jogador_id"] == "p1"


def test_nao_confirma_presenca_com_checkin_fechado():
    _fechar_checkin()

    resposta = client.post("/checkins", json={"jogador_id": "p1"})

    assert resposta.status_code == 409


def test_nao_confirma_presenca_com_checkin_travado():
    _abrir_checkin("2024-05-02", travado=True)

    resposta = client.post("/checkins", json={"jogador_id": "p1"})

    assert resposta.status_code == 409


def test_nao_permite_confirmar_o_mesmo_jogador_duas_vezes_no_mesmo_dia():
    _abrir_checkin("2024-05-03")
    client.post("/checkins", json={"jogador_id": "dup1"})

    resposta = client.post("/checkins", json={"jogador_id": "dup1"})

    assert resposta.status_code == 409


def test_lista_checkins():
    _abrir_checkin("2024-05-04")
    client.post("/checkins", json={"jogador_id": "listado"})

    lista = client.get("/checkins").json()

    assert any(c["jogador_id"] == "listado" for c in lista)


def test_remove_checkin_desmarcando_presenca():
    _abrir_checkin("2024-05-05")
    criado = client.post("/checkins", json={"jogador_id": "removivel"}).json()

    resposta = client.delete(f"/checkins/{criado['id']}")

    assert resposta.status_code == 200
    assert not any(c["id"] == criado["id"] for c in client.get("/checkins").json())


def test_nao_remove_checkin_quando_travado():
    _abrir_checkin("2024-05-06")
    criado = client.post("/checkins", json={"jogador_id": "protegido"}).json()
    _abrir_checkin("2024-05-06", travado=True)

    resposta = client.delete(f"/checkins/{criado['id']}")

    assert resposta.status_code == 409
