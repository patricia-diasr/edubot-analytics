import os

# A configuração é lida quando o app é importado, então as variáveis de teste precisam
# existir antes dos imports abaixo. Chave gerada só para os testes, não é usada em
# nenhum ambiente real
os.environ.setdefault(
    "SECRET_KEY", "chave-exclusiva-dos-testes-automatizados-0123456789"
)
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from app.core.database import get_session
from app.core.hashing import get_password_hash
from app.core.rate_limit import limiter
from app.main import app
from app.models.db_models import User


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """
    Zera o contador do rate limiter antes de cada teste
    """

    limiter.reset()
    yield


@pytest.fixture(name="session")
def session_fixture():
    """
    Banco SQLite em memória, criado do zero a cada teste
    """

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    TestClient com a dependency get_session substituída pela sessão de teste
    """

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)

    yield client
    app.dependency_overrides.clear()


def create_user(session: Session, username: str, password: str) -> User:
    user = User(username=username, hashed_password=get_password_hash(password))
    session.add(user)
    session.commit()
    session.refresh(user)

    return user


def get_token(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/auth/token", data={"username": username, "password": password}
    )

    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(name="headers_aluno1")
def headers_aluno1_fixture(client: TestClient, session: Session) -> dict:
    """Cria o aluno1, faz login e devolve o header Authorization pronto"""

    create_user(session, "aluno1", "senha-do-aluno-1")
    return auth_headers(get_token(client, "aluno1", "senha-do-aluno-1"))


@pytest.fixture(name="headers_aluno2")
def headers_aluno2_fixture(client: TestClient, session: Session) -> dict:
    """Cria o aluno2, faz login e devolve o header Authorization pronto"""

    create_user(session, "aluno2", "senha-do-aluno-2")
    return auth_headers(get_token(client, "aluno2", "senha-do-aluno-2"))
