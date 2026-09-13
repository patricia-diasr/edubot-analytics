from sqlmodel import Session, select
from app.core.database import engine
from app.core.hashing import get_password_hash
from app.models.db_models import User

_SEED_USERS = [
    {"username": "aluno.teste", "password": "senha123", "full_name": "Aluno de Teste"},
    {
        "username": "aluno.teste2",
        "password": "senha456",
        "full_name": "Segundo Aluno de Teste",
    },
]


def seed_users() -> None:
    with Session(engine) as session:
        for data in _SEED_USERS:

            existing = session.exec(
                select(User).where(User.username == data["username"])
            ).first()

            if existing:
                continue

            user = User(
                username=data["username"],
                full_name=data["full_name"],
                hashed_password=get_password_hash(data["password"]),
            )

            session.add(user)

        session.commit()
