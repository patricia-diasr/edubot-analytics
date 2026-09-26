# Relatório de Findings - OWASP ZAP

Scan passivo executado com OWASP ZAP 2.17.0 contra a API rodando localmente (`http://127.0.0.1:8000`), com tráfego autenticado real gerado através do navegador embutido do ZAP e do Swagger UI (`/docs`).

Relatório completo exportado em: [`zap-report.html`](zap-report.html)

## Findings (severidade Medium)

### CSP: Failure to Define Directive with No Fallback

- **Severidade:** Médio
- **O que foi detectado:** a Content-Security-Policy configurada (`default-src 'none'`) não define explicitamente as diretivas `frame-ancestors`, `base-uri` e `form-action`.
- **Por que é um problema:** ao contrário da maioria das diretivas de CSP, essas três **não seguem o fallback de `default-src`**, ficam sem nenhuma restrição a menos que sejam declaradas explicitamente, mesmo com uma política restritiva definida.
- **Status:** ✅ Corrigido
- **Justificativa:** a CSP foi expandida para `default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'`, fechando a lacuna.

### Content Security Policy (CSP) Header Not Set (em /openapi.json)

- **Severidade:** Médio
- **O que foi detectado:** a rota `/openapi.json` não retornava o header Content-Security-Policy.
- **Por que é um problema:** essa exclusão foi um erro de escopo, não uma necessidade real, `/openapi.json` é um arquivo JSON estático, que não carrega scripts de CDN (diferente de `/docs` e `/redoc`, que são páginas HTML e precisam da exceção).
- **Status:** ✅ Corrigido
- **Justificativa:** removido `/openapi.json` da lista de exceção da CSP, agora só `/docs` e `/redoc` ficam de fora.

## Findings de baixa severidade / informativos

### Server Leaks its Webserver Application via "Server" HTTP Response Header Field

- **Severidade:** Informativo
- **O que foi detectado:** toda resposta incluía `Server: uvicorn`, revelando a stack de aplicação usada.
- **Status:** ✅ Corrigido
- **Justificativa:** o header não pode ser removido via middleware da aplicação (o Uvicorn o adiciona na camada de transporte, depois da resposta da aplicação). A correção foi subir o servidor com a flag nativa `--no-server-header`.

### Strict-Transport-Security Header on Plain HTTP Response

- **Severidade:** Informativo
- **O que foi detectado:** o header HSTS está presente mesmo em respostas servidas por HTTP puro (sem TLS).
- **Status:** ⚠️ Risco aceito
- **Justificativa:** HSTS só tem efeito prático sobre HTTPS, navegadores ignoram esse header quando recebido por conexão não criptografada, então ele fica inerte no ambiente de desenvolvimento local. Isso é esperado: implementar HSTS é um requisito explícito da tarefa 3, e o header passa a funcionar normalmente assim que a API for implantada atrás de HTTPS/TLS.

## Verificação da correção (segundo scan)

Após aplicar as correções acima, um segundo scan foi executado para confirmar a remediação. O relatório completo está em [`zap-report-verificacao.html`](zap-report-verificacao.html), e pode ser comparado com o scan original em [`zap-report-inicial.html`](zap-report-inicial.html)).

| Finding | Status no scan original | Status no scan de verificação |
| --- | --- | --- |
| CSP: Failure to Define Directive with No Fallback | Médio | Ausente - correção confirmada |
| CSP Header Not Set (`/openapi.json`) | Médio | Ausente - correção confirmada |
| Server Leaks via header "Server" | Informativo | Ausente - correção confirmada |
| Strict-Transport-Security em HTTP puro | Informativo | Presente - esperado (risco aceito, não uma correção pendente) |

**Observação:** o scan de verificação também identificou dois alertas informativos adicionais (*Solicitação de autenticação identificada* e *Session Management Response Identified*), gerados pelo add-on de Authentication Helper do ZAP ao reconhecer o padrão de login da API. Não são achados de segurança, o próprio ZAP classifica o primeiro deles como informativo sem necessidade de correção, e não fazem parte do escopo original de findings desta entrega.
