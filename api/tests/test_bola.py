"""
Autorização por objeto (OWASP API1: BOLA): um aluno só enxerga as próprias solicitações,
mesmo conhecendo ou adivinhando o ID de outra
"""

from fastapi.testclient import TestClient


def _criar_solicitacao(client: TestClient, headers: dict, texto: str) -> int:
    resposta = client.post("/predict", json={"mensagem": texto}, headers=headers)
    assert resposta.status_code == 200
    return resposta.json()["id"]


def test_aluno_acessa_a_propria_solicitacao(client: TestClient, headers_aluno1: dict):
    solicitacao_id = _criar_solicitacao(client, headers_aluno1, "Trancar Cálculo II")

    resposta = client.get(f"/solicitacoes/{solicitacao_id}", headers=headers_aluno1)

    assert resposta.status_code == 200
    assert resposta.json()["mensagem"] == "Trancar Cálculo II"


def test_acesso_a_solicitacao_de_outro_usuario_retorna_404(
    client: TestClient, headers_aluno1: dict, headers_aluno2: dict
):
    """Um aluno não pode acessar a solicitação de outro aluno"""

    solicitacao_id = _criar_solicitacao(client, headers_aluno1, "Trancar Cálculo II")

    resposta = client.get(f"/solicitacoes/{solicitacao_id}", headers=headers_aluno2)

    assert resposta.status_code == 404
    assert "Cálculo" not in resposta.text


def test_solicitacao_de_outro_e_inexistente_tem_a_mesma_resposta(
    client: TestClient, headers_aluno1: dict, headers_aluno2: dict
):
    """
    "Não é sua" e "não existe" precisam ser indistinguíveis, senão o atacante
    descobre quais IDs existem
    """

    solicitacao_id = _criar_solicitacao(client, headers_aluno1, "Revisão de nota")

    de_outro = client.get(f"/solicitacoes/{solicitacao_id}", headers=headers_aluno2)
    inexistente = client.get("/solicitacoes/999999", headers=headers_aluno2)

    assert de_outro.status_code == inexistente.status_code == 404
    assert de_outro.json() == inexistente.json()


def test_enumeracao_de_ids_nao_vaza_solicitacoes(
    client: TestClient, headers_aluno1: dict, headers_aluno2: dict
):
    """Percorrer vários IDs em sequência só devolve o que é do próprio aluno"""

    ids_aluno1 = {
        _criar_solicitacao(client, headers_aluno1, f"Pedido {i} do aluno 1")
        for i in range(3)
    }
    id_aluno2 = _criar_solicitacao(client, headers_aluno2, "Pedido do aluno 2")

    visiveis = {
        i
        for i in range(1, 10)
        if client.get(f"/solicitacoes/{i}", headers=headers_aluno2).status_code == 200
    }

    assert visiveis == {id_aluno2}
    assert not visiveis & ids_aluno1


def test_predict_ignora_tentativa_de_definir_outro_dono(
    client: TestClient, headers_aluno1: dict
):
    """O dono da solicitação vem do token, nunca do corpo da requisição"""

    resposta = client.post(
        "/predict",
        json={"mensagem": "teste", "usuario_id": 2},
        headers=headers_aluno1,
    )

    assert resposta.status_code == 422
