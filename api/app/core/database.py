from typing import Generator
from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = "sqlite:///./edubot.db"

engine = create_engine(
    DATABASE_URL, echo=False, connect_args={"check_same_thread": False}
)


def create_db_and_tables() -> None:
    """Cria as tabelas no banco a partir dos modelos SQLModel, se ainda não existirem"""

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependency do FastAPI, abre uma sessão por requisição e garante o fechamento"""

    with Session(engine) as session:
        yield session
