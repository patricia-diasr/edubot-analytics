"""
Rate limiting (OWASP API4: Unrestricted Resource Consumption): limita tentativas de
login (força bruta) e o uso do /predict
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from starlette.requests import Request
from app.core.config import settings
from app.core.rate_limit import get_client_ip
from tests.conftest import create_user

LIMITE_LOGIN = 5
LIMITE_PREDICT = 20


def _login(client: TestClient, senha: str, headers: dict | None = None):
    return client.post(
        "/auth/token",
        data={"username": "aluno1", "password": senha},
        headers=headers or {},
    )


def test_login_retorna_429_apos_exceder_o_limite(client: TestClient, session: Session):
    """A 6ª tentativa no mesmo minuto é bloqueada com 429"""

    create_user(session, "aluno1", "senha-do-aluno-1")

    status_tentativas = [
        _login(client, "errada").status_code for _ in range(LIMITE_LOGIN)
    ]
    bloqueada = _login(client, "errada")

    assert status_tentativas == [401] * LIMITE_LOGIN
    assert bloqueada.status_code == 429


def test_resposta_429_informa_quando_tentar_de_novo(
    client: TestClient, session: Session
):
    """O 429 segue o formato dos outros erros e traz o header Retry-After"""

    create_user(session, "aluno1", "senha-do-aluno-1")
    for _ in range(LIMITE_LOGIN):
        _login(client, "errada")

    bloqueada = _login(client, "errada")

    assert bloqueada.status_code == 429
    assert "detail" in bloqueada.json()
    assert 1 <= int(bloqueada.headers["retry-after"]) <= 60


def test_login_bloqueado_mesmo_com_a_senha_certa(client: TestClient, session: Session):
    """
    Depois do bloqueio nem a senha certa passa, senão o atacante continuaria testando
    senhas e só olharia quais respostas não são 429
    """

    create_user(session, "aluno1", "senha-do-aluno-1")
    for _ in range(LIMITE_LOGIN):
        _login(client, "errada")

    assert _login(client, "senha-do-aluno-1").status_code == 429


def test_trocar_x_forwarded_for_nao_burla_o_limite(
    client: TestClient, session: Session
):
    """Sem proxy configurado, o header X-Forwarded-For enviado pelo cliente é ignorado"""

    create_user(session, "aluno1", "senha-do-aluno-1")

    respostas = [
        _login(client, "errada", {"X-Forwarded-For": f"10.0.0.{i}"}).status_code
        for i in range(LIMITE_LOGIN + 1)
    ]

    assert respostas[-1] == 429


def test_predict_retorna_429_apos_exceder_o_limite(
    client: TestClient, headers_aluno1: dict
):
    respostas = [
        client.post(
            "/predict", json={"mensagem": "teste"}, headers=headers_aluno1
        ).status_code
        for _ in range(LIMITE_PREDICT + 1)
    ]

    assert respostas[:LIMITE_PREDICT] == [200] * LIMITE_PREDICT
    assert respostas[-1] == 429


def _request(
    ip_conexao: str,
    x_forwarded_for: str | None = None,
    cf_connecting_ip: str | None = None,
) -> Request:
    headers = []
    if x_forwarded_for is not None:
        headers.append((b"x-forwarded-for", x_forwarded_for.encode()))
    if cf_connecting_ip is not None:
        headers.append((b"cf-connecting-ip", cf_connecting_ip.encode()))
    return Request({"type": "http", "client": (ip_conexao, 12345), "headers": headers})


@pytest.mark.parametrize(
    "hops, x_forwarded_for, esperado",
    [
        # Sem proxy: sempre o IP da conexão, o header é ignorado
        (0, "1.1.1.1", "9.9.9.9"),
        # 1 proxy: o último valor foi escrito pelo proxy, os anteriores pelo cliente
        (1, "6.6.6.6, 203.0.113.7", "203.0.113.7"),
        # 2 proxies (ex: CDN + balanceador): o penúltimo valor é o cliente
        (2, "6.6.6.6, 203.0.113.7, 10.0.0.1", "203.0.113.7"),
        # Header ausente ou menor que o esperado: volta para o IP da conexão
        (1, None, "9.9.9.9"),
        (2, "203.0.113.7", "9.9.9.9"),
    ],
)
def test_ip_do_cliente_atras_de_proxy(
    monkeypatch, hops: int, x_forwarded_for: str | None, esperado: str
):
    monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", hops)

    assert get_client_ip(_request("9.9.9.9", x_forwarded_for)) == esperado


def test_ip_do_cliente_pelo_header_do_proxy(monkeypatch):
    """
    No Render, o IP real vem no cf-connecting-ip (escrito pela Cloudflare). O
    X-Forwarded-For enviado pelo cliente é ignorado
    """

    monkeypatch.setattr(settings, "CLIENT_IP_HEADER", "cf-connecting-ip")
    monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", 1)

    requisicao = _request("10.26.25.107", "1.2.3.4, 10.0.0.1", "187.180.167.89")

    assert get_client_ip(requisicao) == "187.180.167.89"


def test_sem_o_header_do_proxy_usa_a_regra_de_hops(monkeypatch):
    monkeypatch.setattr(settings, "CLIENT_IP_HEADER", "cf-connecting-ip")
    monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", 1)

    assert get_client_ip(_request("9.9.9.9", "6.6.6.6, 203.0.113.7")) == "203.0.113.7"


def test_limite_vale_por_cliente_atras_do_proxy(
    client: TestClient, session: Session, monkeypatch
):
    """
    Atrás do proxy, cada cliente tem o próprio contador: o bloqueio de um atacante não
    impede o login de outro aluno (evita negação de serviço no login)
    """

    monkeypatch.setattr(settings, "CLIENT_IP_HEADER", "cf-connecting-ip")
    create_user(session, "aluno1", "senha-do-aluno-1")

    atacante = {"cf-connecting-ip": "203.0.113.66"}
    for _ in range(LIMITE_LOGIN):
        _login(client, "errada", atacante)

    assert _login(client, "errada", atacante).status_code == 429
    outro_aluno = _login(
        client, "senha-do-aluno-1", {"cf-connecting-ip": "198.51.100.7"}
    )
    assert outro_aluno.status_code == 200
