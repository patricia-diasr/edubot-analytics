"""
Página /docs (Swagger UI) servida pela própria API, no lugar da página padrão do FastAPI.

A página padrão carrega o Swagger UI de uma CDN com versão flutuante (@5), sem verificação
de integridade e sem Content-Security-Policy. O scan do ZAP no TP3 apontou isso como dois
findings Médios. Aqui a versão é fixa, os arquivos da CDN têm SRI (o navegador recusa o
arquivo se ele for alterado) e a página tem uma CSP própria, que libera só a CDN e o script
de inicialização desta página
"""

import base64
import hashlib
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.core.config import settings

router = APIRouter(include_in_schema=False)

# Versão publicada há mais de 2 semanas no momento da escolha, para reduzir o risco de
# usar uma versão recém-comprometida. Os hashes SRI foram conferidos com os publicados
# pela jsDelivr. Ao trocar a versão, os dois hashes precisam ser recalculados:
#   curl -s <url> | openssl dgst -sha384 -binary | openssl base64 -A
SWAGGER_UI_VERSION = "5.33.0"
_CDN = f"https://cdn.jsdelivr.net/npm/swagger-ui-dist@{SWAGGER_UI_VERSION}"
_SRI_JS = "sha384-YDALVcy8kj8yltLBVi1vBiBAUqdxvus673gM8XKwiy6aDUJFXivF/KCufekjYbVf"
_SRI_CSS = "sha384-Ov4/wv3j2bmct8cDc5X4ngJZohVPzEmc6uDPH8WeljUxO5vtoykvMEfbu9Vh6RaW"

_SCRIPT_INICIALIZACAO = (
    "SwaggerUIBundle({"
    'url: "/openapi.json", '
    'dom_id: "#swagger-ui", '
    'layout: "BaseLayout", '
    "deepLinking: true, "
    "presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset]"
    "});"
)
# O script de inicialização fica no próprio HTML. Em vez de liberar qualquer script
# inline ('unsafe-inline'), a CSP libera só este, pelo hash do seu conteúdo. Os estilos
# também não precisam de 'unsafe-inline': o Swagger UI aplica estilos dinâmicos pelo
# CSSOM, que a CSP não bloqueia (testado sem nenhuma violação no navegador)
_HASH_SCRIPT = base64.b64encode(
    hashlib.sha256(_SCRIPT_INICIALIZACAO.encode("utf-8")).digest()
).decode("ascii")

CSP_DOCS = "; ".join(
    [
        "default-src 'none'",
        f"script-src https://cdn.jsdelivr.net 'sha256-{_HASH_SCRIPT}'",
        "style-src https://cdn.jsdelivr.net",
        "img-src 'self' data:",
        "connect-src 'self'",
        "frame-ancestors 'none'",
        "base-uri 'none'",
        "form-action 'none'",
    ]
)

_HTML = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{settings.APP_NAME} - Swagger UI</title>
<link rel="stylesheet" href="{_CDN}/swagger-ui.css" integrity="{_SRI_CSS}" crossorigin="anonymous">
</head>
<body>
<div id="swagger-ui"></div>
<script src="{_CDN}/swagger-ui-bundle.js" integrity="{_SRI_JS}" crossorigin="anonymous"></script>
<script>{_SCRIPT_INICIALIZACAO}</script>
</body>
</html>
"""


@router.get("/docs")
def swagger_ui() -> HTMLResponse:
    return HTMLResponse(_HTML, headers={"Content-Security-Policy": CSP_DOCS})
