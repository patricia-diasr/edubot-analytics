# Auditoria final de segurança da API (TP3)

Este documento consolida a auditoria de segurança da API do EduBot Analytics feita no TP3,
antes de ela ser entregue como alvo do pentest (TP4). Ele reúne:

1. os achados da revisão de código e do teste na URL pública, com severidade e correção;
2. o checklist de controles, organizado pelo OWASP API Security Top 10 (2023);
3. o resultado do scan final do OWASP ZAP;
4. os riscos aceitos e a evidência de que a API está pronta para o pentest.

**API auditada:** https://edubot-analytics.onrender.com (versão 0.3.0)
**Código:** branch `tp3-infra-sec`

## 1. Achados da auditoria do TP3

A revisão do código entregue no TP2, a auditoria de dependências (`pip-audit`) e o teste
da API publicada encontraram os problemas abaixo. A severidade segue o CVSS 3.1, a mesma
escala que será usada no relatório de pentest do TP4.

| ID | Achado | Como foi encontrado | CVSS 3.1 | Status |
| --- | --- | --- | --- | --- |
| A1 | Chave de assinatura do JWT com valor padrão no código público. Sem `.env`, a API usava essa chave, e qualquer pessoa podia forjar um token válido para qualquer aluno | Revisão de código. Teste: token forjado com a chave padrão recebia 200 | 7.4 Alto `AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N` | ✅ Corrigido |
| A2 | 35 vulnerabilidades conhecidas em 4 dependências (`python-jose`, `starlette`, `python-multipart`, `ecdsa`), incluindo negação de serviço no envio de formulários (usado pelo `/auth/token`) | `pip-audit` | 7.5 Alto `AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H` | ✅ Corrigido |
| A3 | Rate limit ineficaz atrás do proxy do Render. O IP usado era o do balanceador interno (`10.x.x.x`), então todos os usuários dividiam dois contadores: o limite real dobrava e um atacante podia bloquear o login de todos | Teste na URL pública: 7 logins errados sem 429. Confirmado pelos logs | 7.5 Alto `AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H` | ✅ Corrigido |
| A4 | Senhas dos usuários de teste (`senha123`) escritas no código público. Na API online, dariam acesso direto às contas | Revisão de código | 6.5 Médio `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:N` | ✅ Corrigido |
| A5 | `/predict` sem limite de requisições, o que permite uso abusivo (e custo, quando o agente chamar um LLM no TP4) | Revisão de código | 4.3 Médio `AV:N/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:L` | ✅ Corrigido |
| A6 | Enumeração de usuários pelo tempo de resposta do login: usuário inexistente respondia na hora, usuário existente demorava (bcrypt) | Revisão de código. Teste de tempo | 3.7 Baixo `AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N` | ✅ Corrigido |
| A7 | O erro 422 repetia na resposta o valor enviado pelo cliente (campo `input`) | Teste manual | Informativo | ✅ Corrigido |
| A8 | Mensagem composta só de espaços era aceita no `/predict` | Teste manual | Informativo | ✅ Corrigido |

### Como cada achado foi corrigido

- **A1:** `SECRET_KEY` passou a ser obrigatória, com no mínimo 32 caracteres, e os
  valores de exemplo publicados são recusados. A API não inicia sem uma chave válida, e a
  chave não aparece em logs de erro (`hide_input_in_errors`). No Render, a chave foi gerada
  aleatoriamente e fica só nas variáveis de ambiente. O JWT também ficou mais rígido:
  algoritmo fixo (recusa `alg: none`) e claims `exp` e `sub` obrigatórias.
  _Testes:_ `test_autenticacao.py`.
- **A2:** dependências atualizadas, `python-jose` trocado por `PyJWT` e `passlib`
  (abandonado) trocado por `bcrypt`. `pip-audit` passou de 35 para 0 vulnerabilidades e
  agora roda no GitHub Actions a cada push.
  _Evidência:_ `security/evidencias/pip-audit-antes-tp2.txt` e `pip-audit-depois-tp3.txt`,
  prints 04 e 02.
- **A3:** o IP do cliente passou a ser lido do header `cf-connecting-ip`, escrito pela
  Cloudflare (camada na frente do Render). Testado online: 5 tentativas com
  `X-Forwarded-For` falso geraram 401, e a 6ª gerou **429**. Tentar forjar o próprio
  `CF-Connecting-IP` é barrado pela Cloudflare (403). Os logs registram o IP real.
  _Evidência:_ `security/deploy-render.md`, `test_rate_limit.py`, print 12.
- **A4:** senhas dos usuários de teste movidas para variáveis de ambiente
  (`SEED_PASSWORD_ALUNO1..3`). No Render, foram geradas aleatoriamente.
- **A5:** limite de 20 requisições por minuto por IP no `/predict`.
- **A6:** quando o usuário não existe, a API faz uma verificação bcrypt equivalente, e o
  tempo de resposta fica igual nos dois casos.
- **A7:** handler próprio para o 422, que devolve só tipo, local e mensagem do erro.
- **A8:** espaços nas pontas são removidos antes da validação de tamanho mínimo.

## 2. Checklist de controles (OWASP API Security Top 10 2023)

| # | Risco OWASP | Controle na API | Status | Evidência |
| --- | --- | --- | --- | --- |
| API1 | Broken Object Level Authorization (BOLA) | `GET /solicitacoes/{id}` só devolve recursos do aluno do token. "Não existe" e "não é seu" têm a mesma resposta (404). O dono da solicitação vem do token, nunca do corpo | ✅ Resolvido | `test_bola.py` (5 testes); prints 06 e 07 (CI bloqueia o merge se a verificação for removida) |
| API2 | Broken Authentication | JWT HS256 com chave forte obrigatória, algoritmo fixo, `exp` e `sub` obrigatórios, validade de 30 min. Senhas com bcrypt. Mesma resposta para senha errada e usuário inexistente, com tempo igual. Rate limit no login | ✅ Resolvido | `test_autenticacao.py` (12 testes); achados A1, A4 e A6 |
| API3 | Broken Object Property Level Authorization | Entrada com `extra="forbid"` (campo extra → 422). A saída usa `response_model`, que não expõe `usuario_id` nem dados internos | ✅ Resolvido | `test_validacao_entrada.py`; `test_predict_ignora_tentativa_de_definir_outro_dono` |
| API4 | Unrestricted Resource Consumption | Login: 5/min por IP. `/predict`: 20/min por IP. Mensagem com até 2000 caracteres. 429 com `Retry-After` | ✅ Resolvido | `test_rate_limit.py` (13 testes); achados A3 e A5; print 12 |
| API5 | Broken Function Level Authorization | A API só tem funções de aluno. Não existem rotas administrativas nem de alteração de notas | ✅ Não aplicável (sem funções privilegiadas) | `test_documentacao.py` garante que só existem as 4 rotas documentadas |
| API6 | Unrestricted Access to Sensitive Business Flows | O único fluxo de negócio (`/predict`) exige autenticação e tem limite por IP | ✅ Resolvido | `test_rate_limit.py` |
| API7 | Server Side Request Forgery | A API não faz requisições para URLs informadas pelo usuário | ✅ Não aplicável | Revisão de código |
| API8 | Security Misconfiguration | HTTPS com redirecionamento e HSTS. Headers X-Frame-Options, X-Content-Type-Options, CSP e `Cache-Control: no-store` em todas as respostas, inclusive de erro. `/docs` com CSP própria, versão fixa e SRI. CORS com allowlist. Sem header `Server: uvicorn`. 422 sem eco do valor enviado | ✅ Resolvido | `test_headers_cors.py` (13 testes); print 12; scan ZAP (seção 3) |
| API9 | Improper Inventory Management | Uma única versão publicada, totalmente documentada no `/docs` com todos os códigos de resposta | ✅ Resolvido | `test_documentacao.py`; prints 09 a 11 |
| API10 | Unsafe Consumption of APIs | A API ainda não consome APIs externas. Passa a ser relevante no TP4, quando o agente chamar um LLM | ⏳ Reavaliar no TP4 | Plano de segurança do agente |

### Controles complementares

| Controle | Status | Evidência |
| --- | --- | --- |
| SQL injection: SQLModel com queries parametrizadas, sem SQL montado na mão | ✅ Resolvido | `test_injecao_sql_*` e `test_id_nao_numerico_e_rejeitado` |
| Dependências sem vulnerabilidades conhecidas, verificadas a cada push | ✅ Resolvido | Job `pip-audit` no GitHub Actions; print 04 |
| Segredos fora do código: `SECRET_KEY` e senhas de teste só em variáveis de ambiente, `.env` no `.gitignore` | ✅ Resolvido | `api/.env.example`; `security/deploy-render.md` |
| Logs de segurança: login com falha registra usuário, IP e headers de IP, nunca a senha | ✅ Resolvido | `api/app/routers/auth.py`; logs do Render |
| CI/CD: testes e auditoria de dependências a cada push. Merge na `main` bloqueado se falharem. Deploy só depois do CI aprovar | ✅ Resolvido | `.github/workflows/security-tests.yml`; prints 01 a 08 |

## 3. Scan final com OWASP ZAP

Scan passivo com OWASP ZAP 2.17.0 contra a URL pública, com tráfego autenticado gerado pelo
Swagger UI. Detalhes de cada finding em [`zap-findings-tp3.md`](zap-findings-tp3.md).

| Finding | Risco | Status |
| --- | --- | --- |
| Content Security Policy (CSP) Header Not Set (`/docs`) | Médio | ✅ Corrigido: CSP própria no `/docs`, sem `'unsafe-inline'` |
| Sub Resource Integrity Attribute Missing (`/docs`) | Médio | ✅ Corrigido: Swagger UI com versão fixa e SRI; `/redoc` removido |
| Cross-Domain JavaScript Source File Inclusion (`/docs`) | Baixo | ⚠️ Aceito: coberto pelo SRI e pela versão fixa |
| Re-examine Cache-control Directives | Informativo | ✅ Corrigido: `Cache-Control: no-store` em todas as respostas |
| Server Leaks via "Server" (`cloudflare`) | Informativo | ⚠️ Aceito: header da plataforma, sem versão |
| Modern Web Application, Session Management, Authentication Request | Informativo | Sem ação (não são falhas) |

- Relatório inicial: [`zap-report-tp3-inicial.html`](zap-report-tp3-inicial.html)
- Relatório de verificação: _a preencher após o segundo scan_ (`zap-report-tp3-verificacao.html`)

## 4. Riscos aceitos

| Risco | Por que foi aceito | Mitigação existente |
| --- | --- | --- |
| Rate limit por IP, sem bloqueio por conta: um ataque distribuído (muitos IPs) contra um mesmo usuário não é barrado | Bloquear a conta permitiria que qualquer pessoa travasse o login de um aluno de propósito | Senhas de teste fortes e aleatórias. Tentativas registradas em log |
| Contador do rate limit em memória: zera quando o serviço reinicia | Há uma única instância. Um armazenamento compartilhado (Redis) não é necessário nesse escopo | Reinícios são raros e não podem ser provocados pelo cliente |
| Token JWT não pode ser revogado antes de expirar (não há logout no servidor) | A API não guarda sessão. Lista de revogação adicionaria estado e complexidade | Validade curta (30 min). Token de usuário removido é recusado |
| `/docs` carrega o Swagger UI de outro domínio (`cdn.jsdelivr.net`), finding Baixo do ZAP | Evita versionar ~1,5 MB de arquivos de terceiros no repositório | Versão fixa, SRI e CSP própria no `/docs`: um arquivo alterado na CDN não é executado |
| Banco SQLite efêmero no plano gratuito do Render | Adequado ao escopo acadêmico. Os dados de teste são recriados a cada reinício | Facilita restaurar o estado depois do pentest |
| Headers de infraestrutura (`server: cloudflare`, `x-render-origin-server: Render`) | Adicionados pela plataforma, fora do controle da aplicação. Não revelam versão de software | O header do servidor da aplicação (`uvicorn`) foi removido |

## 5. Prontidão para o pentest

| Requisito | Status | Evidência |
| --- | --- | --- |
| API rodando sem erros em URL pública com HTTPS | ✅ | https://edubot-analytics.onrender.com/health, print 09 |
| Autenticação funcionando | ✅ | Print 10 (login pelo Authorize do Swagger) |
| Dados de teste disponíveis: 3 alunos, cada um com solicitações próprias, para testes de BOLA | ✅ | `api/app/db/seed.py`. As credenciais são entregues à dupla adversária no plano de escopo |
| Documentação OpenAPI acessível | ✅ | https://edubot-analytics.onrender.com/docs, prints 09 a 11 |
| Suíte de testes de segurança passando | ✅ | `pytest tests/ -v`: 67 testes. `security/evidencias/pytest-tp3.txt` |
| Nenhum finding Médio ou Alto pendente | _a confirmar com o scan ZAP_ | Seção 3 |

**Observação para a dupla adversária:** no plano gratuito, a API "dorme" após 15 minutos
sem uso. O primeiro acesso depois disso leva cerca de 50 segundos.
