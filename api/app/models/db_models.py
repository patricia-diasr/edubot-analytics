from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: Optional[str] = None


class Solicitacao(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    mensagem: str
    categoria: str = Field(default="placeholder")
    urgencia: str = Field(default="placeholder")
    status: str = Field(default="not_implemented")
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    usuario_id: int = Field(foreign_key="user.id", index=True)
