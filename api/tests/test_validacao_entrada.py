"""
Validação de entrada (OWASP API3/API8): o corpo das requisições precisa seguir
exatamente o schema, sem campos extras, vazios ou fora do tamanho permitido
"""

import pytest
from fastapi.testclient import TestClient


def test_campo_extra_no_body_e_rejeitado(client: TestClient, headers_aluno1: dict):
    """Campo não esperado no corpo da requisição deve ser rejeitado"""

    resposta = client.post(
        "/predict",
        json={"mensagem": "teste", "campo_extra": "não deveria existir"},
        headers=headers_aluno1,
    )
    assert resposta.status_code == 422


@pytest.mark.parametrize(
    "corpo",
    [
        {},
        {"mensagem": ""},
        {"mensagem": "     "},
        {"mensagem": "x" * 2001},
        {"mensagem": 123},
        {"mensagem": None},
        {"mensagem": ["lista", "de", "textos"]},
    ],
    ids=[
        "sem_mensagem",
        "vazia",
        "so_espacos",
        "maior_que_2000",
        "numero",
        "nulo",
        "lista",
    ],
)
def test_mensagem_invalida_e_rejeitada(
    client: TestClient, headers_aluno1: dict, corpo: dict
):
    resposta = client.post("/predict", json=corpo, headers=headers_aluno1)
    assert resposta.status_code == 422


def test_mensagem_no_limite_de_2000_caracteres_e_aceita(
    client: TestClient, headers_aluno1: dict
):
    resposta = client.post(
        "/predict", json={"mensagem": "x" * 2000}, headers=headers_aluno1
    )
    assert resposta.status_code == 200


def test_body_que_nao_e_json_e_rejeitado(client: TestClient, headers_aluno1: dict):
    resposta = client.post(
        "/predict",
        content="mensagem=teste",
        headers={**headers_aluno1, "Content-Type": "text/plain"},
    )
    assert resposta.status_code == 422


def test_erro_422_nao_ecoa_o_valor_enviado(client: TestClient, headers_aluno1: dict):
    """A resposta de erro não repete o conteúdo enviado pelo cliente"""

    resposta = client.post(
        "/predict",
        json={"mensagem": "teste", "campo": "<script>alert(1)</script>"},
        headers=headers_aluno1,
    )

    assert resposta.status_code == 422
    assert "<script>" not in resposta.text
    assert "input" not in resposta.json()["detail"][0]


@pytest.mark.parametrize("solicitacao_id", ["abc", "1 OR 1=1", "1;DROP TABLE user"])
def test_id_nao_numerico_e_rejeitado(
    client: TestClient, headers_aluno1: dict, solicitacao_id: str
):
    """IDs com texto ou tentativa de SQL injection nem chegam ao banco"""

    resposta = client.get(f"/solicitacoes/{solicitacao_id}", headers=headers_aluno1)
    assert resposta.status_code == 422


def test_injecao_sql_na_mensagem_e_salva_como_texto(
    client: TestClient, headers_aluno1: dict
):
    """Com queries parametrizadas, SQL no texto é tratado como texto comum"""

    payload = "'; DROP TABLE solicitacao; --"
    criada = client.post(
        "/predict", json={"mensagem": payload}, headers=headers_aluno1
    ).json()

    lida = client.get(f"/solicitacoes/{criada['id']}", headers=headers_aluno1)

    assert lida.status_code == 200
    assert lida.json()["mensagem"] == payload


def test_injecao_sql_no_login_nao_autentica(client: TestClient, headers_aluno1: dict):
    resposta = client.post(
        "/auth/token", data={"username": "aluno1' OR '1'='1", "password": "x"}
    )
    assert resposta.status_code == 401
