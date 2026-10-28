import os

# Configuración de pruebas: base en memoria y sin credenciales de IA. La variable
# vacía tiene prioridad sobre cualquier .env local, así las pruebas nunca llaman a la API.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from backend.app.ai import assistant  # noqa: E402
from backend.app.config import Settings, get_settings  # noqa: E402
from backend.app.database import Base, get_db  # noqa: E402
from backend.app.main import app  # noqa: E402


@pytest.fixture
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def test_settings():
    return Settings(_env_file=None, database_url="sqlite:///:memory:", anthropic_api_key=None)


@pytest.fixture
def client(db_session, test_settings, monkeypatch):
    def _override():
        yield db_session

    # Las pruebas nunca deben depender de credenciales presentes en la máquina.
    monkeypatch.setattr(assistant, "is_configured", lambda settings: False)
    app.dependency_overrides[get_db] = _override
    app.dependency_overrides[get_settings] = lambda: test_settings
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
