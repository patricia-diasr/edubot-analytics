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
    # extra="forbid" rejeita campos não declarados (422) e str_strip_whitespace remove
    # espaços das pontas antes da validação, então mensagem só com espaços é recusada
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    mensagem: str = Field(min_length=1, max_length=2000)


class SolicitacaoRead(SQLModel):
    id: int
    mensagem: str
    categoria: str
    urgencia: str
    status: str
    criado_em: datetime
