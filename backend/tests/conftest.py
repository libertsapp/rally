import os
import tempfile
from contextlib import contextmanager

import pytest

_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"
# testes rodam sem Clerk de verdade — sem chave, get_usuario_atual sempre
# devolve None (visitante anônimo), sem nenhuma chamada de rede
os.environ["CLERK_SECRET_KEY"] = ""

from app.database import Base, engine, SessionLocal  # noqa: E402
from app.clerk_auth import get_usuario_atual  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402
from main import app  # noqa: E402


@contextmanager
def as_usuario(tipo="superadmin", organizacao_id=None, email="teste@exemplo.com"):
    """Simula um login Clerk nos testes, sem precisar de rede nem de sessão
    de verdade — sobrescreve get_usuario_atual enquanto o bloco `with` roda."""
    fake = Usuario(id="fixture-usuario", email=email, tipo=tipo, organizacao_id=organizacao_id, ativo=True)
    app.dependency_overrides[get_usuario_atual] = lambda: fake
    try:
        yield fake
    finally:
        app.dependency_overrides.pop(get_usuario_atual, None)


@pytest.fixture(autouse=True)
def banco_limpo():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def pytest_sessionfinish(session, exitstatus):
    engine.dispose()
    try:
        os.remove(_db_path)
    except OSError:
        pass
