"""
Documentação OpenAPI (/docs): todas as rotas documentadas com descrição, schemas de
entrada e saída e todas as respostas de erro possíveis
"""

import pytest
from fastapi.testclient import TestClient

ROTAS_ESPERADAS = {
    ("get", "/health"): {"200"},
    ("post", "/auth/token"): {"200", "401", "422", "429"},
    ("post", "/predict"): {"200", "401", "422", "429"},
    ("get", "/solicitacoes/{solicitacao_id}"): {"200", "401", "404", "422"},
}


@pytest.fixture(name="spec")
def spec_fixture(client: TestClient) -> dict:
    resposta = client.get("/openapi.json")
    assert resposta.status_code == 200
    return resposta.json()


def test_todas_as_rotas_estao_documentadas(spec: dict):
    documentadas = {
        (metodo, rota) for rota, ops in spec["paths"].items() for metodo in ops
    }
    assert documentadas == set(ROTAS_ESPERADAS)


@pytest.mark.parametrize("metodo, rota", list(ROTAS_ESPERADAS))
def test_rota_documenta_todas_as_respostas(spec: dict, metodo: str, rota: str):
    operacao = spec["paths"][rota][metodo]

    assert operacao.get("summary"), "rota sem resumo"
    assert operacao.get("description"), "rota sem descrição"
    assert set(operacao["responses"]) == ROTAS_ESPERADAS[(metodo, rota)]

    for codigo, resposta in operacao["responses"].items():
        assert resposta.get("description"), f"resposta {codigo} sem descrição"
        assert (
            "schema" in resposta["content"]["application/json"]
        ), f"resposta {codigo} sem schema"


def test_rotas_protegidas_exigem_autenticacao_na_spec(spec: dict):
    protegidas = [
        spec["paths"]["/predict"]["post"],
        spec["paths"]["/solicitacoes/{solicitacao_id}"]["get"],
    ]
    for operacao in protegidas:
        assert operacao["security"] == [{"OAuth2PasswordBearer": []}]

    esquema = spec["components"]["securitySchemes"]["OAuth2PasswordBearer"]
    assert esquema["flows"]["password"]["tokenUrl"] == "auth/token"


def test_schema_de_entrada_documenta_limites_e_proibe_campos_extras(spec: dict):
    schema = spec["components"]["schemas"]["SolicitacaoCreate"]

    assert schema["additionalProperties"] is False
    assert schema["properties"]["mensagem"]["minLength"] == 1
    assert schema["properties"]["mensagem"]["maxLength"] == 2000


def test_docs_acessivel_e_redoc_removido(client: TestClient):
    """O /redoc foi removido no TP3 para reduzir a superfície (scripts de 3 domínios)"""

    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 404
