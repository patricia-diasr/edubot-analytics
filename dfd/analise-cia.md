# Análise CIA - EduBot Analytics (TP1)

Análise aplicada aos componentes identificados no DFD (`dfd/dfd.md`): os três processos da API e o armazenamento de credenciais.

## 1. GET /health - Health Check

- **Confidencialidade -> baixa.** A resposta é fixa (`{"status": "ok"}`) e não expõe nenhum dado de negócio, credencial ou detalhe interno da aplicação. Por isso a rota é pública, sem exigir JWT.
- **Integridade -> baixa.** Não há estado para adulterar, é uma checagem de disponibilidade, não uma operação sobre dados.
- **Disponibilidade -> alta.** É o componente que sistemas de monitoramento e orquestração usam para saber se a API está de pé. Precisa responder rápido e sem dependências (não consulta o User Store nem valida nada), justamente para não cair junto se outra parte do sistema falhar.

## 2. POST /auth/token - Auth Service

- **Confidencialidade -> alta.** Recebe `username`/`password` em texto no corpo da requisição (form OAuth2) e nunca deve devolvê-los de volta nem logá-los. A senha nunca é armazenada em texto puro, `fake_db.py` guarda apenas o hash gerado com `bcrypt` (via `passlib`). A `SECRET_KEY` usada para assinar o JWT (`python-jose`, algoritmo HS256) também é confidencial, se vazar, qualquer pessoa consegue forjar tokens válidos para qualquer usuário.
- **Integridade -> alta.** O JWT emitido precisa ser inviolável, a assinatura HS256 garante que qualquer alteração no payload (por exemplo, trocar o `sub` para se passar por outro aluno) invalida o token na hora da verificação. Só deve gerar token para credenciais que batam com o hash armazenado.
- **Disponibilidade -> alta.** Se esse endpoint cair, ninguém consegue obter um token novo e todo o sistema fica inacessível para autenticação, mesmo que `/predict` esteja no ar.

## 3. POST /predict - Predict Service

- **Confidencialidade -> alta.** O corpo da requisição (`mensagem`) pode conter dados pessoais/acadêmicos do aluno (motivo do pedido, disciplina, RA, etc.). Isso se conecta diretamente com o desafio de segurança do domínio, ou seja, evitar que um aluno acesse ou infira dados de registros de outro aluno através das respostas do agente.
- **Integridade -> alta.** A rota depende de `get_current_user`, que não só valida a assinatura do JWT como também confere no User Store que o usuário do token (`sub`) ainda existe, isso impede que um token de um usuário removido continue sendo aceito. No futuro, quando o agente real existir, integridade também vai envolver garantir que o aluno não consiga manipular o agente para alterar notas ou dados (ex: via prompt injection).
- **Disponibilidade -> média.** É a funcionalidade de maior valor do sistema, mas sua indisponibilidade é menos crítica que a do `/auth/token`: sem login ninguém entra no sistema; sem `/predict`, o aluno pelo menos ainda recebe respostas de outras rotas.

## 4. User Store - `fake_db.py`

- **Confidencialidade -> altíssima.** Guarda os hashes de senha de todos os usuários. Mesmo hasheada, uma senha exposta permite ataques de força bruta offline. Hoje o armazenamento é em memória (não persiste em disco, reduzindo a superfície de exposição), mas também não há nenhum controle de acesso real, qualquer parte do processo Python pode ler a estrutura diretamente, sem isolamento.
- **Integridade -> alta.** Se um invasor conseguisse escrever nessa estrutura (por exemplo, através de alguma injeção não tratada em uma versão futura), poderia criar usuários fraudulentos ou substituir hashes existentes, comprometendo toda a autenticação.
- **Disponibilidade -> baixa (risco conhecido).** Por ser em memória, os dados de usuário são perdidos a cada reinício da API. Isso é aceitável e documentado como placeholder para o TP1, mas é um risco real de continuidade que precisa ser resolvido com persistência de verdade (banco de dados) nas próximas entregas.

## Resumo

| Componente | Confidencialidade | Integridade | Disponibilidade |
| ------------------------------ | :---: | :---: | :---: |
| GET /health | Baixa | Baixa | Alta |
| POST /auth/token | Alta | Alta | Alta |
| POST /predict | Alta | Alta | Média |
| User Store (fake_db.py) | Altíssima | Alta | Baixa (risco conhecido) |

**Observação:** a disponibilidade baixa do User Store e a ausência de rate limiting em `/auth/token` (que abriria espaço para força bruta de senha) são riscos já identificados nesta entrega, mas o escopo de mitigação, como rate limiting e validação de headers, está previsto para os próximos TP's.
