"""Prova que dados de uma organização nunca vazam pra outra — a garantia
mais crítica da Fase 2. Sem autenticação de verdade ainda, o isolamento é
resolvido pelo header X-Organizacao-Id (ver app/tenant.py)."""

from fastapi.testclient import TestClient

from main import app
from tests.conftest import as_usuario

client = TestClient(app)


def _criar_org(slug):
    with as_usuario("superadmin"):
        return client.post("/organizacoes", json={"slug": slug, "nome": f"Org {slug}"}).json()


def _headers(org):
    return {"X-Organizacao-Id": org["id"]}


def test_jogador_de_uma_org_nao_aparece_na_listagem_de_outra():
    org_a = _criar_org("tenant-a")
    org_b = _criar_org("tenant-b")

    client.post("/jogadores", json={"nome": "Só da A"}, headers=_headers(org_a))

    lista_a = client.get("/jogadores", headers=_headers(org_a)).json()
    lista_b = client.get("/jogadores", headers=_headers(org_b)).json()

    assert any(p["nome"] == "Só da A" for p in lista_a)
    assert not any(p["nome"] == "Só da A" for p in lista_b)


def test_nao_atualiza_jogador_de_outra_organizacao():
    org_a = _criar_org("tenant-c")
    org_b = _criar_org("tenant-d")
    jogador = client.post("/jogadores", json={"nome": "Da C"}, headers=_headers(org_a)).json()

    resposta = client.put(
        f"/jogadores/{jogador['id']}", json={"nome": "Sequestrado"}, headers=_headers(org_b)
    )

    assert resposta.status_code == 404


def test_sorteio_nao_enxerga_jogador_de_outra_organizacao():
    org_a = _criar_org("tenant-e")
    org_b = _criar_org("tenant-f")
    jogador_b = client.post("/jogadores", json={"nome": "Da F"}, headers=_headers(org_b)).json()

    resposta = client.post(
        "/sorteio/times",
        json={"jogador_ids": [jogador_b["id"]], "num_times": 2},
        headers=_headers(org_a),
    )

    assert resposta.status_code == 404


def test_ranking_e_dashboard_isolados_por_organizacao():
    org_a = _criar_org("tenant-g")
    org_b = _criar_org("tenant-h")
    j_a = client.post("/jogadores", json={"nome": "Jogador G"}, headers=_headers(org_a)).json()

    client.post(
        "/rodadas",
        json={
            "data": "2024-10-01",
            "rascunho": False,
            "vencedor": 0,
            "times": [{"nome": "Time 1", "player_ids": [j_a["id"]], "vitorias": 1}],
        },
        headers=_headers(org_a),
    )

    ranking_a = client.get("/ranking", params={"ano": 2024}, headers=_headers(org_a)).json()
    ranking_b = client.get("/ranking", params={"ano": 2024}, headers=_headers(org_b)).json()
    resumo_b = client.get("/dashboard/resumo", headers=_headers(org_b)).json()

    assert any(r["id"] == j_a["id"] for r in ranking_a)
    assert not any(r["id"] == j_a["id"] for r in ranking_b)
    assert resumo_b["dias_jogados_no_ano"] == 0


def test_checkin_e_config_isolados_por_organizacao():
    org_a = _criar_org("tenant-i")
    org_b = _criar_org("tenant-j")

    client.put(
        "/config",
        json={"estrelas_visiveis": True, "checkin_data_aberta": "2024-11-01", "checkin_travado": False},
        headers=_headers(org_a),
    )

    config_a = client.get("/config", headers=_headers(org_a)).json()
    config_b = client.get("/config", headers=_headers(org_b)).json()

    assert config_a["checkin_data_aberta"] == "2024-11-01"
    assert config_b["checkin_data_aberta"] == ""


def test_header_com_organizacao_inexistente_retorna_404():
    resposta = client.get("/jogadores", headers={"X-Organizacao-Id": "nao-existe"})
    assert resposta.status_code == 404


def test_sem_header_cai_na_organizacao_padrao_dev():
    org_dev = client.get("/organizacoes/atual").json()
    assert org_dev["slug"] == "dev"
    # sem header, request cai na mesma organização "dev"
    lista = client.get("/jogadores").json()
    lista_explicita = client.get("/jogadores", headers=_headers(org_dev)).json()
    assert lista == lista_explicita
