from typing import Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    """Resposta do endpoint de login"""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Dados extraídos de dentro do JWT decodificado"""

    username: Optional[str] = None


class UserInDB(BaseModel):
    """Representação do usuário armazenado"""

    username: str
    hashed_password: str
    full_name: Optional[str] = None


class PredictRequest(BaseModel):
    """
    Corpo da requisição para /predict. Representa a mensagem enviada por um aluno ao EduBot Analytics
    """

    mensagem: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        json_schema_extra={
            "example": "Preciso trancar a disciplina de Cálculo II, como faço?"
        },
    )


class PredictResponse(BaseModel):
    """
    Resposta de /predict
    """

    categoria: str = Field(default="placeholder")
    urgencia: str = Field(default="placeholder")
    status: str = Field(default="not_implemented")
