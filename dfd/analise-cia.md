# Análise CIA - EduBot Analytics

Análise aplicada aos componentes identificados no DFD (`dfd/dfd.md`): os quatro processos da API e o banco de dados.

## 1. GET /health - Health Check

- **Confidencialidade -> baixa.** A resposta é fixa (`{"status": "ok"}`) e não expõe nenhum dado de negócio, credencial ou detalhe interno da aplicação. Por isso a rota é pública, sem exigir JWT.
- **Integridade -> baixa.** Não há estado para adulterar, é uma checagem de disponibilidade, não uma operação sobre dados.
- **Disponibilidade -> alta.** É o componente que sistemas de monitoramento e orquestração usam para saber se a API está de pé. Precisa responder rápido e sem dependências (não consulta o banco nem valida nada), justamente para não cair junto se outra parte do sistema falhar.

## 2. POST /auth/token - Auth Service

- **Confidencialidade -> alta.** Recebe `username`/`password` em texto no corpo da requisição (form OAuth2) e nunca deve devolvê-los de volta nem logá-los. A senha nunca é armazenada em texto puro, o banco guarda apenas o hash gerado com `bcrypt` (via `passlib`). A `SECRET_KEY` usada para assinar o JWT (`python-jose`, algoritmo HS256) também é confidencial, se vazar, qualquer pessoa consegue forjar tokens válidos para qualquer usuário.
- **Integridade -> alta.** O JWT emitido precisa ser inviolável, a assinatura HS256 garante que qualquer alteração no payload (por exemplo, trocar o `sub` para se passar por outro aluno) invalida o token na hora da verificação. Só deve gerar token para credenciais que batam com o hash armazenado.
- **Disponibilidade -> alta.** Se esse endpoint cair, ninguém consegue obter um token novo e todo o sistema fica inacessível para autenticação, mesmo que `/predict` esteja no ar. É protegido por rate limiting (5 requisições/minuto por IP) contra força bruta.

## 3. POST /predict - Predict Service

- **Confidencialidade -> alta.** O corpo da requisição (`mensagem`) pode conter dados pessoais/acadêmicos do aluno (motivo do pedido, disciplina, RA, etc.). Isso se conecta diretamente com o desafio de segurança do domínio, ou seja, evitar que um aluno acesse ou infira dados de registros de outro aluno através das respostas do agente. A mensagem é persistida como uma `Solicitacao` vinculada ao usuário, o que reforça a importância de nunca expor esse dado a outro usuário.
- **Integridade -> alta.** A rota depende de `get_current_user`, que não só valida a assinatura do JWT como também confere no banco que o usuário do token (`sub`) ainda existe, isso impede que um token de um usuário removido continue sendo aceito. No futuro, quando o agente real existir, integridade também vai envolver garantir que o aluno não consiga manipular o agente para alterar notas ou dados (ex: via prompt injection).
- **Disponibilidade -> média.** É a funcionalidade de maior valor do sistema, mas sua indisponibilidade é menos crítica que a do `/auth/token`: sem login ninguém entra no sistema; sem `/predict`, o aluno pelo menos ainda recebe respostas de outras rotas.

## 4. GET /solicitacoes/{id} - Solicitacoes Service

- **Confidencialidade -> alta.** Retorna o conteúdo de uma solicitação (mensagem, categoria, urgência). Sem controle de acesso, seria trivial um aluno ler solicitações de outro só trocando o ID na URL.
- **Integridade -> alta.** Implementa verificação de ownership (BOLA): compara `usuario_id` da solicitação com o usuário do token. Retorna **404** tanto para ID inexistente quanto para solicitação de outro usuário, pra não confirmar a quem tenta acessar que aquele ID existe.
- **Disponibilidade -> média.** Mesma lógica do `/predict`: importante, mas não tão crítico quanto o `/auth/token`.

## 5. Banco de dados - SQLite via SQLModel

- **Confidencialidade -> altíssima.** Guarda os hashes de senha de todos os usuários (tabela `User`) e o conteúdo das solicitações de todos os alunos (tabela `Solicitacao`), ambos dados sensíveis. Mesmo hasheada, uma senha exposta permite ataques de força bruta offline.
- **Integridade -> alta.** Se um invasor conseguisse escrever nessa estrutura, poderia criar usuários fraudulentos, substituir hashes ou adulterar solicitações de outros alunos. O uso do SQLModel com queries parametrizadas (sem SQL raw) mitiga injeção de SQL como vetor de ataque.
- **Disponibilidade -> média (melhorou em relação ao TP1).** A migração para SQLite resolveu o risco de perda de dados a cada reinício (que era o problema do TP1). Ainda é um único arquivo, sem backup ou redundância, aceitável para o escopo do projeto, mas seria um problema real em produção.

## Resumo

| Componente | Confidencialidade | Integridade | Disponibilidade |
| ------------------------------ | :---: | :---: | :---: |
| GET /health | Baixa | Baixa | Alta |
| POST /auth/token | Alta | Alta | Alta |
| POST /predict | Alta | Alta | Média |
| GET /solicitacoes/{id} | Alta | Alta | Média |
| Banco de dados (SQLite via SQLModel) | Altíssima | Alta | Média |

**Observação:** os riscos identificados no TP1, disponibilidade do armazenamento de usuários e ausência de rate limiting em `/auth/token`, foram resolvidos no TP2. A persistência migrou para SQLite via SQLModel, e o rate limiting (5 requisições/minuto por IP) foi implementado em `/auth/token`. Detalhes das decisões técnicas e do scan de segurança (OWASP ZAP) estão documentados em `security/decisoes-tecnicas.md` e `security/zap-findings.md`.
