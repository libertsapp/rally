from fastapi.testclient import TestClient

from main import app
from tests.conftest import as_usuario

client = TestClient(app)


def _criar_org(slug="terca", nome="Vôlei de Terça"):
    with as_usuario("superadmin"):
        return client.post(
            "/organizacoes", json={"slug": slug, "nome": nome, "cor_primaria": "#f4b942"}
        ).json()


def test_cria_organizacao():
    with as_usuario("superadmin"):
        resposta = client.post(
            "/organizacoes", json={"slug": "meme", "nome": "Vôlei Meme Brasil", "cor_primaria": "#39ff9e"}
        )
    assert resposta.status_code == 200
    criada = resposta.json()
    assert criada["slug"] == "meme"
    assert criada["nome"] == "Vôlei Meme Brasil"
    assert criada["id"]


def test_visitante_anonimo_nao_pode_criar_organizacao():
    resposta = client.post("/organizacoes", json={"slug": "invasor", "nome": "X"})
    assert resposta.status_code == 403


def test_admin_comum_nao_pode_criar_organizacao():
    with as_usuario("admin", organizacao_id="qualquer"):
        resposta = client.post("/organizacoes", json={"slug": "invasor2", "nome": "X"})
    assert resposta.status_code == 403


def test_visitante_anonimo_nao_pode_listar_organizacoes():
    assert client.get("/organizacoes").status_code == 403


def test_nao_permite_slug_duplicado():
    _criar_org(slug="duplicado")
    with as_usuario("superadmin"):
        resposta = client.post("/organizacoes", json={"slug": "duplicado", "nome": "Outro nome"})
    assert resposta.status_code == 409


def test_lista_organizacoes():
    _criar_org(slug="listada")
    with as_usuario("superadmin"):
        lista = client.get("/organizacoes").json()
    assert any(o["slug"] == "listada" for o in lista)


def test_busca_organizacao_por_id():
    criada = _criar_org(slug="buscada")
    resposta = client.get(f"/organizacoes/{criada['id']}")
    assert resposta.status_code == 200
    assert resposta.json()["slug"] == "buscada"


def test_organizacao_atual_bootstrap_automatico():
    resposta = client.get("/organizacoes/atual")
    assert resposta.status_code == 200
    assert resposta.json()["slug"] == "dev"

    # chamar de novo não duplica a organização padrão
    de_novo = client.get("/organizacoes/atual").json()
    assert de_novo["id"] == resposta.json()["id"]


def test_organizacao_atual_respeita_header_x_organizacao_id():
    criada = _criar_org(slug="via-header")

    resposta = client.get("/organizacoes/atual", headers={"X-Organizacao-Id": criada["id"]})

    assert resposta.status_code == 200
    assert resposta.json()["slug"] == "via-header"


def test_organizacao_inexistente_retorna_404():
    assert client.get("/organizacoes/nao-existe").status_code == 404


def test_atualiza_identidade_da_organizacao():
    criada = _criar_org(slug="atualizavel")
    with as_usuario("superadmin"):
        resposta = client.put(
            f"/organizacoes/{criada['id']}",
            json={"nome": "Nome Novo", "cor_primaria": "#000000"},
        )
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Nome Novo"
    assert resposta.json()["cor_primaria"] == "#000000"


def test_admin_da_propria_organizacao_pode_atualizar_identidade():
    criada = _criar_org(slug="admin-edita-a-propria")
    with as_usuario("admin", organizacao_id=criada["id"]):
        resposta = client.put(f"/organizacoes/{criada['id']}", json={"nome": "Editado pelo admin"})
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Editado pelo admin"


def test_admin_de_outra_organizacao_nao_pode_atualizar():
    criada = _criar_org(slug="protegida")
    with as_usuario("admin", organizacao_id="outra-organizacao"):
        resposta = client.put(f"/organizacoes/{criada['id']}", json={"nome": "Invadido"})
    assert resposta.status_code == 403


def test_convida_admin_para_organizacao():
    criada = _criar_org(slug="com-admin")
    with as_usuario("superadmin"):
        resposta = client.post(f"/organizacoes/{criada['id']}/admins", json={"email": "admin@exemplo.com"})
    assert resposta.status_code == 200
    admin = resposta.json()
    assert admin["email"] == "admin@exemplo.com"
    assert admin["tipo"] == "admin"
    assert admin["organizacao_id"] == criada["id"]


def test_convidar_admin_ja_existente_move_para_nova_organizacao():
    org1 = _criar_org(slug="org-origem")
    org2 = _criar_org(slug="org-destino")
    with as_usuario("superadmin"):
        client.post(f"/organizacoes/{org1['id']}/admins", json={"email": "movel@exemplo.com"})
        resposta = client.post(f"/organizacoes/{org2['id']}/admins", json={"email": "movel@exemplo.com"})

    assert resposta.status_code == 200
    assert resposta.json()["organizacao_id"] == org2["id"]


def test_lista_admins_da_organizacao():
    criada = _criar_org(slug="lista-admins")
    with as_usuario("superadmin"):
        client.post(f"/organizacoes/{criada['id']}/admins", json={"email": "a@exemplo.com"})
        client.post(f"/organizacoes/{criada['id']}/admins", json={"email": "b@exemplo.com"})
        lista = client.get(f"/organizacoes/{criada['id']}/admins").json()

    emails = {a["email"] for a in lista}
    assert emails == {"a@exemplo.com", "b@exemplo.com"}
