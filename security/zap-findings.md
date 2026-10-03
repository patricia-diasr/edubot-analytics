# Relatório de Findings - OWASP ZAP

Fiz um scan passivo com o OWASP ZAP 2.17.0 contra a API rodando localmente em `http://127.0.0.1:8000`. Para gerar tráfego autenticado, usei o navegador embutido do ZAP e o Swagger UI em `/docs`.

Relatório inicial exportado em: [`zap-report-inicial.html`](zap-report-inicial.html)

## Findings (severidade Medium)

### CSP: Failure to Define Directive with No Fallback

- **Severidade:** Médio
- **O que foi detectado:** a Content-Security-Policy configurada (`default-src 'none'`) não definia explicitamente `frame-ancestors`, `base-uri` e `form-action`.
- **Por que é um problema:** essas três diretivas não usam o fallback de `default-src`. Então, mesmo com uma política bem restritiva, elas ficam sem uma regra própria se não forem declaradas.
- **Status:** ✅ Corrigido
- **O que fiz:** expandi a CSP para `default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'`.

### Content Security Policy (CSP) Header Not Set (em /openapi.json)

- **Severidade:** Médio
- **O que foi detectado:** a rota `/openapi.json` não retornava o header Content-Security-Policy.
- **Por que aconteceu:** eu tinha colocado essa rota na lista de exceções, mas ela não precisava estar lá. `/openapi.json` retorna JSON e não carrega scripts externos, diferente de `/docs` e `/redoc`, que são páginas HTML.
- **Status:** ✅ Corrigido
- **O que fiz:** removi `/openapi.json` da exceção. Agora só `/docs` e `/redoc` ficam de fora da CSP padrão.

## Findings de baixa severidade / informativos

### Server Leaks its Webserver Application via "Server" HTTP Response Header Field

- **Severidade:** Informativo
- **O que foi detectado:** as respostas incluíam `Server: uvicorn`, o que revela a tecnologia usada no servidor.
- **Status:** ✅ Corrigido
- **O que fiz:** tentei primeiro remover o header pelo middleware, mas o Uvicorn adiciona esse valor depois que a aplicação já respondeu. A correção foi iniciar o servidor com `--no-server-header`.

### Strict-Transport-Security Header on Plain HTTP Response

- **Severidade:** Informativo
- **O que foi detectado:** o header HSTS aparece mesmo nas respostas servidas por HTTP puro, sem TLS.
- **Status:** ⚠️ Risco aceito
- **Por que mantive assim:** o HSTS só tem efeito real em HTTPS. Navegadores ignoram esse header quando ele chega por uma conexão HTTP, então no ambiente local ele fica inerte. Como implementar HSTS era um requisito da tarefa 3, mantive o header. Quando a API estiver atrás de HTTPS/TLS, ele passa a funcionar normalmente.

## Verificação da correção (segundo scan)

Depois das correções, rodei um segundo scan para conferir se os findings tinham sumido. O relatório completo ficou em [`zap-report-verificacao.html`](zap-report-verificacao.html), e o scan original está em [`zap-report-inicial.html`](zap-report-inicial.html).

| Finding | Status no scan original | Status no scan de verificação |
| --- | --- | --- |
| CSP: Failure to Define Directive with No Fallback | Médio | Ausente - correção confirmada |
| CSP Header Not Set (`/openapi.json`) | Médio | Ausente - correção confirmada |
| Server Leaks via header "Server" | Informativo | Ausente - correção confirmada |
| Strict-Transport-Security em HTTP puro | Informativo | Presente - esperado (risco aceito, não uma correção pendente) |

**Observação:** o scan de verificação também mostrou dois alertas informativos a mais: *Solicitação de autenticação identificada* e *Session Management Response Identified*. Eles foram gerados pelo Authentication Helper do ZAP ao reconhecer o padrão de login da API. Não são falhas de segurança apontadas para correção e não faziam parte dos findings originais desta entrega.
