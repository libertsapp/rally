from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _criar_jogadores(n, sexo="M", estrelas=3):
    ids = []
    for i in range(n):
        resp = client.post("/jogadores", json={"nome": f"J{i}", "sexo": sexo, "estrelas": estrelas})
        ids.append(resp.json()["id"])
    return ids


def test_sortear_times_distribui_todo_mundo():
    ids = _criar_jogadores(12)

    resposta = client.post("/sorteio/times", json={"jogador_ids": ids, "num_times": 4})

    assert resposta.status_code == 200
    times = resposta.json()
    assert len(times) == 4
    todos = [i for time in times for i in time]
    assert sorted(todos) == sorted(ids)


def test_sortear_times_com_id_desconhecido_retorna_404():
    resposta = client.post("/sorteio/times", json={"jogador_ids": ["nao-existe"], "num_times": 2})
    assert resposta.status_code == 404


def test_montar_grupos_devolve_grupos_do_tamanho_do_time():
    ids = _criar_jogadores(8)

    resposta = client.post("/sorteio/grupos", json={"jogador_ids": ids, "num_times": 4})

    assert resposta.status_code == 200
    grupos = resposta.json()
    assert all(len(g) == 4 for g in grupos)


def test_sortear_times_com_grupos_nunca_repete_grupo_no_mesmo_time():
    ids = _criar_jogadores(16)
    grupos = client.post("/sorteio/grupos", json={"jogador_ids": ids, "num_times": 4}).json()

    resposta = client.post(
        "/sorteio/times", json={"jogador_ids": ids, "num_times": 4, "grupos": grupos}
    )

    times = resposta.json()
    id_para_grupo = {i: gi for gi, grupo in enumerate(grupos) for i in grupo}
    for time in times:
        grupos_no_time = [id_para_grupo[i] for i in time]
        assert len(grupos_no_time) == len(set(grupos_no_time))
