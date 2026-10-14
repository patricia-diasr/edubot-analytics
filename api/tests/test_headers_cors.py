"""
Headers de segurança e CORS (OWASP API8: Security Misconfiguration): presentes em
todas as respostas, inclusive nas de erro
"""

import base64
import hashlib
import re
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.core.config import settings
from app.routers.docs import SWAGGER_UI_VERSION
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


def test_respostas_nao_sao_guardadas_em_cache(client: TestClient):
    """Tokens e dados de alunos não podem ficar em cache no navegador ou em proxies"""

    assert client.get("/health").headers["cache-control"] == "no-store"
    resposta = client.post("/auth/token", data={"username": "x", "password": "y"})
    assert resposta.headers["cache-control"] == "no-store"


def test_docs_tem_csp_propria_sem_unsafe_inline(client: TestClient):
    """
    /docs carrega o Swagger UI da CDN, então tem uma CSP própria: libera só a CDN e o
    script de inicialização da página (pelo hash), nunca qualquer script inline
    """

    resposta = client.get("/docs")
    csp = resposta.headers["content-security-policy"]

    assert resposta.status_code == 200
    assert "default-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "unsafe-inline" not in csp
    assert "unsafe-eval" not in csp
    assert resposta.headers["x-frame-options"] == "DENY"


def test_script_inline_do_docs_bate_com_o_hash_da_csp(client: TestClient):
    """Se o script de inicialização mudar sem atualizar a CSP, o Swagger para de carregar"""

    resposta = client.get("/docs")
    script = re.search(r"<script>(.*?)</script>", resposta.text, re.S).group(1)
    hash_script = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()

    assert f"'sha256-{hash_script}'" in resposta.headers["content-security-policy"]


def test_docs_carrega_swagger_com_versao_fixa_e_sri(client: TestClient):
    """
    Os arquivos da CDN têm versão fixa e integrity (SRI): se forem alterados na CDN, o
    navegador se recusa a usá-los (findings Médios do ZAP no TP3)
    """

    html = client.get("/docs").text
    externos = re.findall(r"<(?:script|link)[^>]+(?:src|href)=\"https://[^>]+>", html)

    assert len(externos) == 2
    for tag in externos:
        assert f"swagger-ui-dist@{SWAGGER_UI_VERSION}/" in tag
        assert 'integrity="sha384-' in tag
        assert 'crossorigin="anonymous"' in tag


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
