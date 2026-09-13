# DFD - EduBot Analytics

## Elementos do diagrama

- **Entidade externa:** Aluno / Cliente - usuário não confiável que interage com a API via HTTP.
- **Processos:** quatro rotas da API (`/health`, `/auth/token`, `/predict` e `/solicitacoes/{id}`).
- **Armazenamento de dados:** banco de dados SQLite via SQLModel, com duas tabelas, `User` (credenciais) e `Solicitacao`.
- **Trust boundaries:**
  1. Entre o Aluno (rede pública / Internet) e o servidor da API -> todo dado que cruza essa fronteira é tratado como não confiável até ser validado (ex: token JWT, corpo da requisição).
  2. Entre a lógica da aplicação (processos) e o banco de dados -> separa o código que atende requisições do componente que guarda dados persistentes.

## Diagrama

```mermaid
flowchart TD
    Aluno(["Aluno / Cliente<br/>navegador, app, Postman"])
    
    subgraph Legenda["Legenda"]
      L1["<b>Trust Boundary 1:</b> Internet - Servidor da API<br/><b>Trust Boundary 2:</b> Aplicação - Banco de dados"]
    end
    
    Aluno ~~~ Legenda

    subgraph B1["Trust Boundary 1"]
      subgraph API["Processo: API FastAPI - EduBot Analytics"]
        Health["GET /health<br/>Health Check<br/>rota publica"]
        Auth["POST /auth/token<br/>Auth Service<br/>emite JWT<br/>rate limit: 5/min por IP"]
        Predict["POST /predict<br/>Predict Service<br/>protegida - cria Solicitacao"]
        Solicitacoes["GET /solicitacoes/id<br/>Solicitacoes Service<br/>protegida - verifica ownership"]
      end
    end

    subgraph B2["Trust Boundary 2"]
      DB[("Banco de dados<br/>SQLite via SQLModel<br/>tabelas: User, Solicitacao")]
    end

    Aluno -- "1: GET /health" --> Health
    Health -- "2: 200 OK" --> Aluno

    Aluno -- "3: POST /auth/token<br/>username + password" --> Auth
    Auth -- "4: consulta User e hash" --> DB
    DB -- "5: hash armazenado" --> Auth
    Auth -- "6: 200 OK access_token<br/>ou 401 credenciais invalidas<br/>ou 429 rate limit excedido" --> Aluno

    Aluno -- "7: POST /predict<br/>Authorization Bearer JWT + mensagem" --> Predict
    Predict -- "8: valida JWT e consulta User" --> DB
    DB -- "9: usuario existe ou nao" --> Predict
    Predict -- "10: grava nova Solicitacao" --> DB
    Predict -- "11: 200 OK Solicitacao criada id/categoria/urgencia<br/>ou 401" --> Aluno

    Aluno -- "12: GET /solicitacoes/id<br/>Authorization Bearer JWT" --> Solicitacoes
    Solicitacoes -- "13: valida JWT e consulta Solicitacao por id" --> DB
    DB -- "14: Solicitacao encontrada ou nao, e de quem" --> Solicitacoes
    Solicitacoes -- "15: 200 OK se for do proprio usuario<br/>ou 404 se nao existe OU nao e do usuario<br/>ou 401 sem token" --> Aluno
```

## Entradas e saídas

**Entradas da API:**

- Credenciais (`username`, `password`) em `POST /auth/token`
- Token JWT no header `Authorization: Bearer <token>` em `POST /predict` e `GET /solicitacoes/{id}`
- Corpo da requisição (`mensagem`) em `POST /predict`
- ID da solicitação (parâmetro de rota) em `GET /solicitacoes/{id}`

**Saídas da API:**

- Status de disponibilidade em `GET /health`
- Token de acesso (JWT) em `POST /auth/token`, ou erro 401 (credenciais inválidas) ou 429 (rate limit excedido)
- Solicitação criada (id, categoria, urgência) em `POST /predict`, ou erro 401 sem token válido
- Dados da solicitação em `GET /solicitacoes/{id}` (se pertencer ao usuário autenticado), ou erro 404 (ID inexistente ou pertencente a outro usuário) ou 401 sem token
