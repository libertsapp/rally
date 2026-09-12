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


class _EmailAddressFake:
    def __init__(self, id, email_address):
        self.id = id
        self.email_address = email_address


class _UserFake:
    def __init__(self, email):
        self.primary_email_address_id = "email_1"
        self.email_addresses = [_EmailAddressFake("email_1", email)]


class _UsersApiFake:
    def __init__(self, email):
        self._email = email

    def get(self, *, user_id):
        return _UserFake(self._email)


class _RequestStateFake:
    is_signed_in = True
    payload = {"sub": "user_abc123"}  # sem "email" — igual ao token de sessão padrão do Clerk


class _ClerkSdkFake:
    def __init__(self, email):
        self.users = _UsersApiFake(email)

    def authenticate_request(self, request, options):
        return _RequestStateFake()


def test_busca_email_na_api_do_clerk_quando_o_token_nao_traz_email(monkeypatch, db):
    """Reproduz o bug real: o token de sessão padrão do Clerk não inclui
    "email" nas claims — sem esse fallback, todo login válido virava
    visitante anônimo pro backend."""
    import app.clerk_auth as clerk_auth

    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_qualquercoisa")
    monkeypatch.setattr(clerk_auth, "_get_clerk_sdk", lambda: _ClerkSdkFake("pessoa@exemplo.com"))
    request = _fake_request({"authorization": "Bearer token-de-sessao-valido"})

    usuario = get_usuario_atual(request, db)

    assert usuario is not None
    assert usuario.email == "pessoa@exemplo.com"
    assert usuario.clerk_user_id == "user_abc123"
