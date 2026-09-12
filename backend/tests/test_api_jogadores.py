from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_cria_e_lista_jogador():
    resposta = client.post("/jogadores", json={"nome": "Ana", "estrelas": 4, "sexo": "F"})
    assert resposta.status_code == 200
    criado = resposta.json()
    assert criado["nome"] == "Ana"
    assert criado["id"]

    lista = client.get("/jogadores").json()
    assert any(p["id"] == criado["id"] for p in lista)


def test_atualiza_jogador():
    criado = client.post("/jogadores", json={"nome": "Bia", "estrelas": 3}).json()

    resposta = client.put(f"/jogadores/{criado['id']}", json={"nome": "Bia Silva", "estrelas": 5})

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Bia Silva"
    assert resposta.json()["estrelas"] == 5


def test_atualizar_jogador_inexistente_retorna_404():
    resposta = client.put("/jogadores/nao-existe", json={"nome": "X"})
    assert resposta.status_code == 404


def test_remove_jogador():
    criado = client.post("/jogadores", json={"nome": "Caio"}).json()

    resposta = client.delete(f"/jogadores/{criado['id']}")

    assert resposta.status_code == 200
    lista = client.get("/jogadores").json()
    assert not any(p["id"] == criado["id"] for p in lista)
