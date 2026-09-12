from fastapi.testclient import TestClient

from main import app
from tests.conftest import as_usuario

client = TestClient(app)


def test_visitante_anonimo_recebe_401():
    assert client.get("/usuarios/eu").status_code == 401


def test_usuario_logado_ve_o_proprio_papel():
    with as_usuario("admin", organizacao_id="org-x", email="admin@teste.com"):
        resposta = client.get("/usuarios/eu")

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["email"] == "admin@teste.com"
    assert dados["tipo"] == "admin"
    assert dados["organizacao_id"] == "org-x"
