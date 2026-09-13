from fastapi.testclient import TestClient
from sqlmodel import Session
from tests.conftest import create_user, get_token


def test_predict_sem_token_retorna_401(client: TestClient):
    """(Acesso a rota protegida sem token deve ser rejeitado com 401"""
    response = client.post("/predict", json={"mensagem": "teste"})
    assert response.status_code == 401


def test_acesso_a_solicitacao_de_outro_usuario_retorna_404(
    client: TestClient, session: Session
):
    """Um aluno não pode acessar a solicitação de outro aluno"""

    create_user(session, "aluno1", "senha123")
    create_user(session, "aluno2", "senha456")

    token_aluno1 = get_token(client, "aluno1", "senha123")
    token_aluno2 = get_token(client, "aluno2", "senha456")

    criar = client.post(
        "/predict",
        json={"mensagem": "Preciso trancar Calculo II"},
        headers={"Authorization": f"Bearer {token_aluno1}"},
    )
    
    assert criar.status_code == 200
    solicitacao_id = criar.json()["id"]

    resposta = client.get(
        f"/solicitacoes/{solicitacao_id}",
        headers={"Authorization": f"Bearer {token_aluno2}"},
    )
    assert resposta.status_code == 404


def test_campo_extra_no_body_e_rejeitado(client: TestClient, session: Session):
    """Campo não esperado no corpo da requisição deve ser rejeitado"""

    create_user(session, "aluno1", "senha123")
    token = get_token(client, "aluno1", "senha123")

    resposta = client.post(
        "/predict",
        json={"mensagem": "teste", "campo_extra": "não deveria existir"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resposta.status_code == 422


def test_fluxo_valido_login_e_predict(client: TestClient, session: Session):
    """Sanity check: o fluxo legítimo continua funcionando com todos os controles ativos"""

    create_user(session, "aluno1", "senha123")
    token = get_token(client, "aluno1", "senha123")

    resposta = client.post(
        "/predict",
        json={"mensagem": "Quero consultar minhas notas"},
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert resposta.status_code == 200
    corpo = resposta.json()
    
    assert corpo["categoria"] == "placeholder"
    assert "id" in corpo
