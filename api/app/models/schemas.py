from datetime import datetime
from typing import Optional
from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(SQLModel):
    username: Optional[str] = None


class SolicitacaoCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")
    mensagem: str = Field(min_length=1, max_length=2000)


class SolicitacaoRead(SQLModel):
    id: int
    mensagem: str
    categoria: str
    urgencia: str
    status: str
    criado_em: datetime
