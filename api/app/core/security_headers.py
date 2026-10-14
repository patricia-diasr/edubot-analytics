from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

CSP_PADRAO = (
    "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adiciona headers HTTP de segurança a todas as respostas da API, seguindo as recomendações do OWASP Secure Headers Project
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains"
        )
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Respostas podem ter tokens e dados de alunos, então nenhuma cópia deve ficar
        # guardada em cache no navegador ou em proxies (finding informativo do ZAP no TP3)
        response.headers["Cache-Control"] = "no-store"

        # A CSP restrita vale para todas as respostas. A única que define a própria CSP é
        # a página /docs (app/routers/docs.py), que precisa carregar o Swagger UI da CDN
        if "content-security-policy" not in response.headers:
            response.headers["Content-Security-Policy"] = CSP_PADRAO

        return response
