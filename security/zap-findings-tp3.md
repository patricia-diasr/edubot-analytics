# Relatório de Findings - OWASP ZAP (TP3)

Fiz um scan passivo com o OWASP ZAP 2.17.0 contra a API publicada em
`https://edubot-analytics.onrender.com`, como parte da auditoria final antes do pentest.
Para gerar tráfego, usei o navegador do ZAP (Manual Explore) e o Swagger UI em `/docs`:
health check, login, `/predict` com e sem token, campo extra, consulta da própria
solicitação e de uma solicitação de outro aluno. O scan foi só passivo (o ZAP observa o
tráfego sem atacar). O ataque ativo fica para o pentest da dupla adversária no TP4.

O relatório foi filtrado para incluir só o site da API, deixando de fora os domínios de
terceiros que o navegador acessou (CDN, Google).

Relatório inicial exportado em: [`zap-report-tp3-inicial.html`](zap-report-tp3-inicial.html)

| Risco | Quantidade de tipos de alerta |
| --- | :---: |
| Alto | 0 |
| Médio | 2 |
| Baixo | 1 |
| Informativo | 5 |

## Findings (severidade Medium)

### Content Security Policy (CSP) Header Not Set (em /docs)

- **Severidade:** Médio
- **O que foi detectado:** a página `/docs` (Swagger UI) não tinha o header Content-Security-Policy.
- **Por que é um problema:** sem CSP, se um atacante conseguir injetar um script na página, o navegador o executa sem restrição. A página `/docs` tinha ficado de fora da CSP restrita de propósito no TP2, porque carrega o Swagger UI de uma CDN e não funcionaria com `default-src 'none'`. A exceção resolvia o funcionamento, mas deixava a página sem nenhuma proteção.
- **Status:** ✅ Corrigido
- **O que fiz:** a página `/docs` passou a ser servida pela própria API (`api/app/routers/docs.py`), com uma CSP própria e restrita: `default-src 'none'`, scripts e estilos só da CDN `cdn.jsdelivr.net`, o script de inicialização liberado apenas pelo seu hash (`sha256-...`), chamadas só para a própria API (`connect-src 'self'`), e `frame-ancestors`, `base-uri` e `form-action` em `'none'`. A CSP **não usa `'unsafe-inline'`** nem para scripts nem para estilos. Testei no navegador: o Swagger funciona (login, chamadas, janela Authorize) sem nenhuma violação de CSP.

### Sub Resource Integrity Attribute Missing (em /docs)

- **Severidade:** Médio
- **O que foi detectado:** os arquivos do Swagger UI (`swagger-ui-bundle.js` e `swagger-ui.css`) eram carregados da CDN sem o atributo `integrity`, e com versão flutuante (`swagger-ui-dist@5`).
- **Por que é um problema:** se a CDN fosse comprometida, ou se uma versão nova maliciosa fosse publicada, o navegador executaria o código alterado na página da API, com acesso ao token do usuário logado no Swagger. Com a versão flutuante, a página podia passar a carregar outro código sem nenhuma mudança no repositório.
- **Status:** ✅ Corrigido
- **O que fiz:** fixei a versão (`swagger-ui-dist@5.33.0`, publicada há mais de duas semanas no momento da escolha) e adicionei o atributo `integrity` com o hash SHA-384 de cada arquivo, mais `crossorigin="anonymous"`. Conferi os hashes calculando-os sobre os arquivos baixados e comparando com os publicados pela jsDelivr. Se o arquivo da CDN for alterado, o navegador se recusa a usá-lo. Também removi a página `/redoc`, que não era necessária e carregava scripts e fontes de outros três domínios (`cdn.redoc.ly` e Google Fonts).

## Findings de baixa severidade / informativos

### Cross-Domain JavaScript Source File Inclusion

- **Severidade:** Baixo
- **O que foi detectado:** a página `/docs` carrega um script de outro domínio (`cdn.jsdelivr.net`).
- **Status:** ⚠️ Risco aceito
- **Por que mantive assim:** o Swagger UI precisa do seu JavaScript, e a alternativa seria versionar cerca de 1,5 MB de arquivos de terceiros no repositório. O risco que esse alerta descreve (o script de outro domínio ser alterado) está coberto pelo SRI e pela versão fixa: um arquivo alterado não é executado. O script só roda na página de documentação, e não nas respostas da API.

### Re-examine Cache-control Directives

- **Severidade:** Informativo
- **O que foi detectado:** as respostas não tinham o header `Cache-Control`.
- **Status:** ✅ Corrigido
- **O que fiz:** todas as respostas passaram a enviar `Cache-Control: no-store`. As respostas da API podem conter o token de acesso (`/auth/token`) e dados dos alunos, que não devem ficar guardados no cache do navegador nem de proxies.

### Server Leaks its Webserver Application via "Server" HTTP Response Header Field

- **Severidade:** Informativo
- **O que foi detectado:** as respostas trazem `Server: cloudflare`.
- **Status:** ⚠️ Risco aceito
- **Por que mantive assim:** o header é adicionado pela Cloudflare, na frente do Render, fora do controle da aplicação. Ele não revela versão de software. O header da aplicação (`Server: uvicorn`), corrigido no TP2, continua removido.

### Modern Web Application, Session Management Response Identified e Solicitação de autenticação identificada

- **Severidade:** Informativo
- **Status:** Sem ação necessária
- **Por quê:** não são falhas. O ZAP apenas registrou que a página `/docs` é uma aplicação JavaScript e reconheceu o fluxo de login (requisição de autenticação e token na resposta).

## Verificação da correção (segundo scan)

_A preencher após o scan de verificação contra a versão corrigida
(`zap-report-tp3-verificacao.html`)._
