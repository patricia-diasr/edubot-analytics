from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_DOCS_HTML_PATHS = ("/docs", "/redoc")


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

        if not request.url.path.startswith(_DOCS_HTML_PATHS):
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; frame-ancestors 'none'; "
                "base-uri 'none'; form-action 'none'"
            )

        return response
