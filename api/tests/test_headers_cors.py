"""
Headers de segurança e CORS (OWASP API8: Security Misconfiguration): presentes em
todas as respostas, inclusive nas de erro
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.core.config import settings
from tests.conftest import create_user

HEADERS_ESPERADOS = {
    "strict-transport-security": "max-age=63072000; includeSubDomains",
    "x-frame-options": "DENY",
    "x-content-type-options": "nosniff",
    "content-security-policy": (
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
    ),
}


def _conferir_headers(resposta):
    for nome, valor in HEADERS_ESPERADOS.items():
        assert resposta.headers.get(nome) == valor, f"header {nome} ausente ou errado"


@pytest.mark.parametrize(
    "metodo, rota, status_esperado",
    [
        ("get", "/health", 200),
        ("get", "/openapi.json", 200),
        ("post", "/predict", 401),
        ("get", "/solicitacoes/1", 401),
        ("get", "/rota-que-nao-existe", 404),
    ],
)
def test_headers_de_seguranca_presentes(
    client: TestClient, metodo: str, rota: str, status_esperado: int
):
    resposta = getattr(client, metodo)(rota)

    assert resposta.status_code == status_esperado
    _conferir_headers(resposta)


def test_headers_presentes_na_resposta_429(client: TestClient, session: Session):
    create_user(session, "aluno1", "senha-do-aluno-1")
    for _ in range(6):
        resposta = client.post(
            "/auth/token", data={"username": "aluno1", "password": "errada"}
        )

    assert resposta.status_code == 429
    _conferir_headers(resposta)


def test_docs_continua_acessivel(client: TestClient):
    """
    /docs carrega o Swagger UI de uma CDN, por isso fica fora da CSP restrita
    (decisão documentada em security/decisoes-tecnicas.md)
    """

    resposta = client.get("/docs")

    assert resposta.status_code == 200
    assert "swagger" in resposta.text.lower()
    assert resposta.headers["x-frame-options"] == "DENY"


def test_cors_permite_origem_da_allowlist(client: TestClient):
    origem = settings.CORS_ORIGINS[0]

    resposta = client.get("/health", headers={"Origin": origem})

    assert resposta.headers.get("access-control-allow-origin") == origem


def test_cors_bloqueia_origem_fora_da_allowlist(client: TestClient):
    resposta = client.get("/health", headers={"Origin": "https://site-malicioso.com"})

    assert "access-control-allow-origin" not in resposta.headers


def test_cors_preflight_recusa_metodo_nao_permitido(client: TestClient):
    resposta = client.options(
        "/predict",
        headers={
            "Origin": settings.CORS_ORIGINS[0],
            "Access-Control-Request-Method": "DELETE",
        },
    )

    assert resposta.status_code == 400
