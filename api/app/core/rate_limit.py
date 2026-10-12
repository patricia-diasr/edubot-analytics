from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request
from app.core.config import settings


def get_client_ip(request: Request) -> str:
    """
    Descobre o IP real do cliente para o rate limiting.

    Sem proxy (TRUSTED_PROXY_HOPS=0), usa o IP da conexão.
    Atrás de N proxies confiáveis, cada proxy acrescenta ao final do X-Forwarded-For o IP
    de quem se conectou a ele. Por isso o IP real é o N-ésimo valor contando do fim.
    Os valores mais à esquerda podem ter sido escritos pelo próprio cliente e não são
    usados, senão bastaria trocar o header a cada tentativa para escapar do limite
    """

    hops = settings.TRUSTED_PROXY_HOPS
    if hops <= 0:
        return get_remote_address(request)

    forwarded_for = request.headers.get("x-forwarded-for", "")
    ips = [ip.strip() for ip in forwarded_for.split(",") if ip.strip()]
    if len(ips) < hops:
        return get_remote_address(request)
    return ips[-hops]


limiter = Limiter(key_func=get_client_ip)
