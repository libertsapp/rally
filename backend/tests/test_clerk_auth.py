"""Testa o módulo de verificação do Clerk de verdade (sem override de
dependência) — usa a chave secreta real do projeto, então bate na rede do
Clerk pra validar a assinatura. Prova que token forjado nunca autentica."""

from starlette.requests import Request

from app.clerk_auth import get_usuario_atual


def _fake_request(headers: dict) -> Request:
    scope = {
        "type": "http",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
    }
    return Request(scope)


def test_sem_chave_configurada_nao_autentica(monkeypatch, db):
    monkeypatch.setenv("CLERK_SECRET_KEY", "")
    request = _fake_request({"authorization": "Bearer qualquer-coisa"})

    assert get_usuario_atual(request, db) is None


def test_sem_header_de_autorizacao_nao_autentica(monkeypatch, db):
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_qZLghSZpKpQmVoLxfNJH35sKZHhM2HiBgvxnqLHhPZ")
    request = _fake_request({})

    assert get_usuario_atual(request, db) is None


def test_token_forjado_nunca_autentica(monkeypatch, db):
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_qZLghSZpKpQmVoLxfNJH35sKZHhM2HiBgvxnqLHhPZ")
    request = _fake_request({"authorization": "Bearer isso-nao-e-um-jwt-de-verdade"})

    assert get_usuario_atual(request, db) is None
