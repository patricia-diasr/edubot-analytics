from typing import Optional
from app.core.hashing import get_password_hash
from app.models.schemas import UserInDB

_FAKE_USERS_DB = {
    "aluno.teste": UserInDB(
        username="aluno.teste",
        full_name="Aluno de Teste",
        hashed_password=get_password_hash("senha123"),
    )
}


def get_user(username: str) -> Optional[UserInDB]:
    return _FAKE_USERS_DB.get(username)
