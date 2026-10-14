"""
Textos e respostas de erro reaproveitados na documentação OpenAPI (/docs)
"""

from app.core.config import settings
from app.models.schemas import ErroSimples, ErroValidacao

_UNIDADES = {"second": "segundo", "minute": "minuto", "hour": "hora", "day": "dia"}


def limite_legivel(limite: str) -> str:
    """Converte o formato do slowapi ("5/minute") para texto ("5 por minuto")"""

    quantidade, _, unidade = limite.partition("/")
    return f"{quantidade} por {_UNIDADES.get(unidade, unidade)}"


DESCRICAO_API = f"""
API do **EduBot Analytics**, agente de suporte acadêmico universitário que recebe pedidos
de alunos (matrícula, trancamento, consulta de notas) e, a partir do TP4, vai classificar
a categoria e a urgência de cada pedido.

## Como autenticar

1. Clique em **Authorize** (cadeado) e informe usuário e senha. O Swagger chama
   `POST /auth/token` e guarda o JWT.
2. As rotas protegidas passam a enviar o header `Authorization: Bearer <token>`.
3. O token vale **{settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutos**. Depois disso, faça
   login novamente.

## Controles de segurança

| Controle | Comportamento |
| --- | --- |
| Autenticação JWT (HS256) | Rotas protegidas retornam **401** sem token, com token inválido, expirado ou de usuário inexistente |
| Ownership (BOLA) | Um aluno só acessa as próprias solicitações. Recurso de outro aluno retorna **404**, igual a um ID inexistente |
| Validação de entrada | Campos extras, tipos errados e tamanhos fora do limite retornam **422**, sem repetir o valor enviado |
| Rate limiting | Login: **{limite_legivel(settings.RATE_LIMIT_LOGIN)}** por IP. `/predict`: **{limite_legivel(settings.RATE_LIMIT_PREDICT)}** por IP. Acima disso, **429** |
| Headers HTTP | HSTS, X-Frame-Options, X-Content-Type-Options e Content-Security-Policy em todas as respostas |

Código-fonte e documentação de segurança:
[github.com/patricia-diasr/edubot-analytics](https://github.com/patricia-diasr/edubot-analytics)
"""

TAGS = [
    {
        "name": "health",
        "description": "Verificação de disponibilidade, sem autenticação",
    },
    {"name": "auth", "description": "Login e emissão do token JWT"},
    {
        "name": "predict",
        "description": "Envio de pedidos do aluno para classificação (protegida)",
    },
    {
        "name": "solicitacoes",
        "description": "Consulta das solicitações do próprio aluno (protegida)",
    },
]

RESPOSTA_401 = {
    401: {
        "model": ErroSimples,
        "description": "Token ausente, inválido, expirado ou de usuário inexistente",
        "content": {
            "application/json": {
                "example": {"detail": "Não foi possível validar as credenciais"}
            }
        },
    }
}

RESPOSTA_422 = {
    422: {
        "model": ErroValidacao,
        "description": "Entrada fora do schema (campo extra, tipo errado, tamanho "
        "inválido). O valor enviado não é repetido na resposta",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "type": "extra_forbidden",
                            "loc": ["body", "campo_extra"],
                            "msg": "Extra inputs are not permitted",
                        }
                    ]
                }
            }
        },
    }
}


def resposta_429(limite: str) -> dict:
    return {
        429: {
            "model": ErroSimples,
            "description": f"Limite de requisições excedido ({limite_legivel(limite)} por IP). "
            "O header `Retry-After` indica quantos segundos esperar",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Muitas requisições. Tente novamente em instantes."
                    }
                }
            },
        }
    }
