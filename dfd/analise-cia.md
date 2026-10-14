# Análise CIA - EduBot Analytics

Análise aplicada aos componentes identificados no DFD versão 3 (`dfd/dfd.md`): os processos
da API, os armazenamentos de dados, a borda da plataforma onde a API está publicada e a
cadeia de entrega. Os componentes 6 a 10 foram incluídos no TP3, com a publicação da API no
Render. Os componentes 1 a 5 foram revisados para refletir as mudanças do TP3.

## 1. GET /health - Health Check

- **Confidencialidade -> baixa.** A resposta é fixa (`{"status": "ok"}`) e não expõe nenhum dado de negócio, credencial ou detalhe interno da aplicação. Por isso a rota é pública, sem exigir JWT.
- **Integridade -> baixa.** Não há estado para adulterar, é uma checagem de disponibilidade, não uma operação sobre dados.
- **Disponibilidade -> alta.** É o componente que o Render usa como health check para saber se a API está de pé. Precisa responder rápido e sem dependências (não consulta o banco nem valida nada), justamente para não cair junto se outra parte do sistema falhar.

## 2. POST /auth/token - Auth Service

- **Confidencialidade -> alta.** Recebe `username`/`password` no corpo da requisição (form OAuth2), sempre por HTTPS, e nunca os devolve nem os registra em log (o log de login com falha guarda só o usuário e o IP). A senha nunca é armazenada em texto puro: o banco guarda apenas o hash gerado com `bcrypt`. A `SECRET_KEY` usada para assinar o JWT (`PyJWT`, algoritmo HS256) também é confidencial: se vazar, qualquer pessoa consegue forjar tokens válidos para qualquer usuário. Por isso, a partir do TP3, ela é obrigatória, tem no mínimo 32 caracteres, é gerada pelo Render e nunca aparece no código. A resposta para senha errada e para usuário inexistente é a mesma, com o mesmo tempo, para não revelar quais usuários existem.
- **Integridade -> alta.** O JWT emitido precisa ser inviolável: a assinatura HS256 garante que qualquer alteração no payload (por exemplo, trocar o `sub` para se passar por outro aluno) invalida o token na verificação. O algoritmo é fixo (tokens com `alg: none` são recusados) e as claims `exp` e `sub` são obrigatórias. Só gera token para credenciais que batam com o hash armazenado.
- **Disponibilidade -> alta.** Se esse endpoint cair, ninguém consegue obter um token novo e todo o sistema fica inacessível, mesmo que `/predict` esteja no ar. É protegido por rate limiting (5 requisições por minuto por IP real do cliente) contra força bruta. No TP3, o rate limit foi corrigido para usar o IP real atrás do proxy do Render: antes, todos os usuários dividiam o mesmo contador e um atacante podia bloquear o login de todos.

## 3. POST /predict - Predict Service

- **Confidencialidade -> alta.** O corpo da requisição (`mensagem`) pode conter dados pessoais/acadêmicos do aluno (motivo do pedido, disciplina, RA, etc.). Isso se conecta diretamente com o desafio de segurança do domínio, ou seja, evitar que um aluno acesse ou infira dados de registros de outro aluno através das respostas do agente. A mensagem é persistida como uma `Solicitacao` vinculada ao usuário do token, o que reforça a importância de nunca expor esse dado a outro usuário. Erros de validação (422) não repetem o conteúdo enviado.
- **Integridade -> alta.** A rota depende de `get_current_user`, que não só valida a assinatura do JWT como também confere no banco que o usuário do token (`sub`) ainda existe, o que impede que um token de um usuário removido continue sendo aceito. O dono da solicitação vem sempre do token: o corpo aceita apenas `mensagem` (`extra="forbid"`). No futuro, quando o agente real existir, integridade também vai envolver garantir que o aluno não consiga manipular o agente para alterar notas ou dados (ex: via prompt injection), ver `dfd/threat-model-stride.md`.
- **Disponibilidade -> média.** É a funcionalidade de maior valor do sistema, mas sua indisponibilidade é menos crítica que a do `/auth/token`. Tem limite de 20 requisições por minuto por IP e mensagens de até 2000 caracteres, para evitar uso abusivo, que vai ficar mais caro quando o agente chamar um modelo de linguagem.

## 4. GET /solicitacoes/{id} - Solicitacoes Service

- **Confidencialidade -> alta.** Retorna o conteúdo de uma solicitação (mensagem, categoria, urgência). Sem controle de acesso, seria trivial um aluno ler solicitações de outro só trocando o ID na URL.
- **Integridade -> alta.** Implementa verificação de ownership (BOLA): compara `usuario_id` da solicitação com o usuário do token. Retorna **404** tanto para ID inexistente quanto para solicitação de outro usuário, para não confirmar a quem tenta acessar que aquele ID existe. Um teste automatizado no CI falha (e bloqueia o merge) se essa verificação for removida.
- **Disponibilidade -> média.** Mesma lógica do `/predict`: importante, mas não tão crítico quanto o `/auth/token`.

## 5. Banco de dados - SQLite via SQLModel

- **Confidencialidade -> altíssima.** Guarda os hashes de senha de todos os usuários (tabela `User`) e o conteúdo das solicitações de todos os alunos (tabela `Solicitacao`), ambos dados sensíveis. Mesmo hasheada, uma senha exposta permite ataques de força bruta offline. O arquivo fica no disco do serviço no Render e não é exposto por nenhuma rota.
- **Integridade -> alta.** Se um invasor conseguisse escrever nessa estrutura, poderia criar usuários fraudulentos, substituir hashes ou adulterar solicitações de outros alunos. O uso do SQLModel com queries parametrizadas (sem SQL raw) mitiga injeção de SQL, e há testes automatizados de SQL injection no login, na mensagem e no ID da rota.
- **Disponibilidade -> baixa (mudou no TP3).** No plano gratuito do Render, o disco é apagado a cada novo deploy ou reinício, então os dados não são permanentes. Para o escopo do projeto isso é aceito: os usuários e solicitações de teste são recriados automaticamente na inicialização, o que inclusive restaura o estado original depois do pentest. Em produção real, seria necessário um banco gerenciado com backup.

## 6. Borda da plataforma - Cloudflare + balanceador do Render (novo no TP3)

- **Confidencialidade -> alta.** É onde termina o HTTPS: garante que credenciais, tokens e mensagens não trafeguem em texto aberto pela Internet. Requisições HTTP são redirecionadas para HTTPS, e o header HSTS faz o navegador usar sempre HTTPS (risco aceito no TP2, resolvido no TP3).
- **Integridade -> alta.** A aplicação confia no header `cf-connecting-ip`, escrito pela Cloudflare, para identificar o IP do cliente no rate limit. Esse header não pode ser falsificado: a Cloudflare bloqueia (403) requisições que tentam enviá-lo. Já o `X-Forwarded-For`, que o cliente pode escrever, é ignorado.
- **Disponibilidade -> média.** É gerenciada pelo Render, fora do controle da dupla. No plano gratuito, o serviço "dorme" após 15 minutos sem uso e o primeiro acesso leva cerca de 50 segundos.

## 7. GET /docs e /openapi.json - Documentação (novo no TP3)

- **Confidencialidade -> baixa.** Documenta publicamente as rotas, os schemas e os controles de segurança. Isso é intencional: a API vai ser alvo de pentest, e a segurança não depende de esconder as rotas. A documentação não contém segredos nem dados de usuários.
- **Integridade -> média.** Uma documentação errada levaria a usos incorretos da API. Um teste automatizado garante que todas as rotas continuam documentadas com todas as respostas possíveis. A página `/docs` carrega o Swagger UI de uma CDN com versão fixa e SRI: se o arquivo for adulterado na CDN, o navegador não o executa. Ela também tem uma CSP própria, sem `'unsafe-inline'` (correção de dois findings Médios do ZAP no TP3).
- **Disponibilidade -> baixa.** Útil para quem consome a API, mas não afeta o funcionamento das demais rotas.

## 8. Variáveis de ambiente do Render - segredos (novo no TP3)

- **Confidencialidade -> altíssima.** Guardam a `SECRET_KEY` do JWT e as senhas dos usuários de teste. Quem tiver a chave consegue se passar por qualquer aluno. Por isso ficam só no painel do Render (acesso restrito à conta da dupla), nunca no código, no repositório ou em logs (a chave não aparece nem em mensagens de erro de configuração).
- **Integridade -> alta.** Trocar a chave invalida todos os tokens emitidos. Trocar as senhas altera o acesso às contas de teste. Só a dona da conta no Render pode alterar.
- **Disponibilidade -> alta.** Sem a `SECRET_KEY`, a API se recusa a iniciar, de propósito: é preferível ficar fora do ar a rodar com uma chave insegura.

## 9. Logs do Render - eventos de segurança (novo no TP3)

- **Confidencialidade -> média.** Registram tentativas de login que falharam, com usuário e IP. Nunca registram senhas nem tokens. O acesso é restrito ao painel do Render.
- **Integridade -> média.** Servem como evidência de tentativas de ataque (por exemplo, força bruta ou falsificação de IP). Foram eles que permitiram diagnosticar a falha do rate limit atrás do proxy.
- **Disponibilidade -> baixa.** A API funciona normalmente sem eles. No plano gratuito, o histórico de logs é limitado.

## 10. Cadeia de entrega - GitHub, GitHub Actions e deploy (novo no TP3)

- **Confidencialidade -> média.** O repositório é público, então nada sensível pode estar nele: segredos ficam só no Render, e o `.env` está no `.gitignore`. O workflow do GitHub Actions não usa nenhum segredo real (a chave dos testes é gerada a cada execução).
- **Integridade -> altíssima.** É o caminho pelo qual um código malicioso ou com falha chegaria à produção. Por isso: a `main` só recebe código por pull request com os testes de segurança e o `pip-audit` aprovados (ruleset), o workflow roda com permissão somente de leitura, e o Render só publica uma versão depois que o CI aprova.
- **Disponibilidade -> média.** Se o GitHub ou o Render estiverem fora do ar, não há deploy novo, mas a versão publicada continua funcionando.

## Resumo

| Componente | Confidencialidade | Integridade | Disponibilidade |
| ------------------------------ | :---: | :---: | :---: |
| GET /health | Baixa | Baixa | Alta |
| POST /auth/token | Alta | Alta | Alta |
| POST /predict | Alta | Alta | Média |
| GET /solicitacoes/{id} | Alta | Alta | Média |
| Banco de dados (SQLite via SQLModel) | Altíssima | Alta | Baixa |
| Borda (Cloudflare + Render) | Alta | Alta | Média |
| Documentação (/docs, /openapi.json) | Baixa | Média | Baixa |
| Variáveis de ambiente (segredos) | Altíssima | Alta | Alta |
| Logs de segurança | Média | Média | Baixa |
| Cadeia de entrega (CI/CD) | Média | Altíssima | Média |

**Evolução entre os TPs:**

- **TP1 → TP2:** os riscos de disponibilidade do armazenamento de usuários (memória) e a ausência de rate limiting em `/auth/token` foram resolvidos com SQLite e com o limite de 5 requisições por minuto por IP.
- **TP2 → TP3:** a chave do JWT deixou de ter valor padrão no código, as dependências vulneráveis foram substituídas, o rate limit passou a funcionar atrás do proxy e foi estendido ao `/predict`, e o HSTS passou a ter efeito com HTTPS. A disponibilidade do banco caiu para "baixa" porque o disco do plano gratuito do Render é efêmero, um risco aceito e documentado. Detalhes em `security/auditoria-final-tp3.md` e `security/deploy-render.md`.
