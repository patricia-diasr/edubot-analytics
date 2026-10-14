from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field

# Schemas de entrada e saída da API. São modelos Pydantic puros (não viram tabelas),
# as tabelas do banco ficam em db_models.py


class HealthResponse(BaseModel):
    status: str = Field(
        description="Sempre `ok` quando a API está no ar", examples=["ok"]
    )


class Token(BaseModel):
    access_token: str = Field(
        description="JWT assinado com HS256, válido por 30 minutos. Enviar no header "
        "`Authorization: Bearer <token>`",
        examples=[
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbHVuby50ZXN0ZSJ9.x"
        ],
    )
    token_type: str = Field(default="bearer", examples=["bearer"])


class TokenData(BaseModel):
    username: Optional[str] = None


class SolicitacaoCreate(BaseModel):
    # extra="forbid" rejeita campos não declarados (422) e str_strip_whitespace remove
    # espaços das pontas antes da validação, então mensagem só com espaços é recusada
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {"mensagem": "Preciso trancar Cálculo II, o prazo termina amanhã"}
            ]
        },
    )
    mensagem: str = Field(
        min_length=1,
        max_length=2000,
        description="Texto do pedido do aluno. Espaços nas pontas são removidos, e "
        "mensagens vazias ou só com espaços são recusadas",
    )


class SolicitacaoRead(BaseModel):
    # Permite montar a resposta direto a partir do objeto do banco (Solicitacao)
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Identificador da solicitação", examples=[1])
    mensagem: str = Field(
        description="Texto enviado pelo aluno",
        examples=["Preciso trancar Cálculo II, o prazo termina amanhã"],
    )
    categoria: str = Field(
        description="Categoria do pedido (burocrático ou pedagógico). Retorna "
        "`placeholder` até o modelo de classificação ser integrado (TP4)",
        examples=["placeholder"],
    )
    urgencia: str = Field(
        description="Urgência do pedido. Retorna `placeholder` até o modelo de "
        "classificação ser integrado (TP4)",
        examples=["placeholder"],
    )
    status: str = Field(
        description="Situação do processamento da solicitação",
        examples=["not_implemented"],
    )
    criado_em: datetime = Field(description="Data e hora de criação, em UTC")


# Schemas das respostas de erro, usados só na documentação OpenAPI (/docs)


class ErroSimples(BaseModel):
    detail: str = Field(description="Descrição do erro")


class ItemErroValidacao(BaseModel):
    type: str = Field(description="Tipo do erro", examples=["extra_forbidden"])
    loc: List[Union[str, int]] = Field(
        description="Onde está o erro (ex: body, campo)", examples=[["body", "campo"]]
    )
    msg: str = Field(
        description="Mensagem de erro", examples=["Extra inputs are not permitted"]
    )


class ErroValidacao(BaseModel):
    detail: List[ItemErroValidacao]
