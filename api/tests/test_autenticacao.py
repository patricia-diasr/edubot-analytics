"""
Autenticação (OWASP API2: Broken Authentication): só tokens válidos, assinados com a
chave da API e dentro da validade, dão acesso às rotas protegidas
"""

from datetime import timedelta
import jwt
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.core.config import settings
from app.core.security import create_access_token
from tests.conftest import auth_headers, create_user

MENSAGEM = {"mensagem": "Quero consultar minhas notas"}


def test_health_e_publico(client: TestClient):
    """/health responde sem token (usado por monitoramento)"""

    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_predict_sem_token_retorna_401(client: TestClient):
    """Acesso a rota protegida sem token deve ser rejeitado com 401"""

    resposta = client.post("/predict", json=MENSAGEM)
    assert resposta.status_code == 401


def test_solicitacoes_sem_token_retorna_401(client: TestClient):
    resposta = client.get("/solicitacoes/1")
    assert resposta.status_code == 401


def test_token_malformado_retorna_401(client: TestClient):
    resposta = client.post(
        "/predict", json=MENSAGEM, headers=auth_headers("isso.nao.e-um-jwt")
    )
    assert resposta.status_code == 401


def test_token_assinado_com_outra_chave_retorna_401(
    client: TestClient, session: Session
):
    """Token forjado: mesmo usuário e formato, mas assinado com uma chave diferente"""

    create_user(session, "aluno1", "senha-do-aluno-1")
    forjado = jwt.encode(
        {"sub": "aluno1"}, "chave-do-atacante-com-mais-de-32-caracteres", "HS256"
    )

    resposta = client.post("/predict", json=MENSAGEM, headers=auth_headers(forjado))
    assert resposta.status_code == 401


def test_token_com_algoritmo_none_retorna_401(client: TestClient, session: Session):
    """Token sem assinatura ("alg": "none"), ataque clássico contra JWT"""

    create_user(session, "aluno1", "senha-do-aluno-1")
    sem_assinatura = jwt.encode({"sub": "aluno1"}, None, algorithm="none")

    resposta = client.post(
        "/predict", json=MENSAGEM, headers=auth_headers(sem_assinatura)
    )
    assert resposta.status_code == 401


def test_token_expirado_retorna_401(client: TestClient, session: Session):
    create_user(session, "aluno1", "senha-do-aluno-1")
    expirado = create_access_token({"sub": "aluno1"}, timedelta(minutes=-1))

    resposta = client.post("/predict", json=MENSAGEM, headers=auth_headers(expirado))
    assert resposta.status_code == 401


def test_token_sem_expiracao_retorna_401(client: TestClient, session: Session):
    """Um token sem "exp" valeria para sempre, então é recusado"""

    create_user(session, "aluno1", "senha-do-aluno-1")
    sem_exp = jwt.encode({"sub": "aluno1"}, settings.SECRET_KEY, settings.ALGORITHM)

    resposta = client.post("/predict", json=MENSAGEM, headers=auth_headers(sem_exp))
    assert resposta.status_code == 401


def test_token_de_usuario_inexistente_retorna_401(client: TestClient):
    """Token válido, mas de um usuário que não existe (ou foi removido)"""

    token = create_access_token({"sub": "usuario.removido"})

    resposta = client.post("/predict", json=MENSAGEM, headers=auth_headers(token))
    assert resposta.status_code == 401


def test_senha_errada_e_usuario_inexistente_tem_a_mesma_resposta(
    client: TestClient, session: Session
):
    """A resposta não pode revelar se o usuário existe (enumeração de usuários)"""

    create_user(session, "aluno1", "senha-do-aluno-1")

    senha_errada = client.post(
        "/auth/token", data={"username": "aluno1", "password": "errada"}
    )
    usuario_inexistente = client.post(
        "/auth/token", data={"username": "ninguem", "password": "errada"}
    )

    assert senha_errada.status_code == usuario_inexistente.status_code == 401
    assert senha_errada.json() == usuario_inexistente.json()


def test_login_valido_retorna_token_bearer(client: TestClient, session: Session):
    create_user(session, "aluno1", "senha-do-aluno-1")

    resposta = client.post(
        "/auth/token", data={"username": "aluno1", "password": "senha-do-aluno-1"}
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["token_type"] == "bearer"
    assert (
        jwt.decode(
            corpo["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )["sub"]
        == "aluno1"
    )


def test_fluxo_valido_login_e_predict(client: TestClient, headers_aluno1: dict):
    """Sanity check: o fluxo legítimo continua funcionando com todos os controles ativos"""

    resposta = client.post("/predict", json=MENSAGEM, headers=headers_aluno1)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["mensagem"] == MENSAGEM["mensagem"]
    assert corpo["categoria"] == "placeholder"
    assert "id" in corpo
