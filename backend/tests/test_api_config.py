from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_get_config_cria_configuracao_padrao_na_primeira_vez():
    resposta = client.get("/config")

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["estrelas_visiveis"] is True
    assert dados["checkin_data_aberta"] == ""
    assert dados["checkin_travado"] is False
    assert dados["contador_acessos"] == 0


def test_put_config_abre_checkin_pra_uma_data():
    resposta = client.put(
        "/config",
        json={"estrelas_visiveis": True, "checkin_data_aberta": "2024-05-01", "checkin_travado": False},
    )

    assert resposta.status_code == 200
    assert resposta.json()["checkin_data_aberta"] == "2024-05-01"


def test_put_config_nunca_deixa_o_cliente_sobrescrever_o_contador_de_acessos():
    client.post("/config/acesso")
    client.post("/config/acesso")

    client.put(
        "/config", json={"estrelas_visiveis": True, "checkin_data_aberta": "", "checkin_travado": False}
    )

    assert client.get("/config").json()["contador_acessos"] == 2


def test_put_config_salva_identidade_visual_do_grupo():
    resposta = client.put(
        "/config",
        json={
            "estrelas_visiveis": True,
            "checkin_data_aberta": "",
            "checkin_travado": False,
            "nome_grupo": "Vôlei de Terça",
            "subtitulo": "Toda terça, 19h",
            "cor_primaria": "#0a2f5c",
            "cor_secundaria": "#d4af37",
        },
    )

    dados = resposta.json()
    assert dados["nome_grupo"] == "Vôlei de Terça"
    assert dados["cor_primaria"] == "#0a2f5c"


def test_post_acesso_incrementa_contador():
    antes = client.get("/config").json()["contador_acessos"]

    resposta = client.post("/config/acesso")

    assert resposta.json()["contador_acessos"] == antes + 1
