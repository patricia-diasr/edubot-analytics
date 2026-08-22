# DFD - EduBot Analytics

## Elementos do diagrama

- **Entidade externa:** Aluno / Cliente - usuário não confiável que interage com a API via HTTP.
- **Processos:** os três endpoints da API (`/health`, `/auth/token`, `/predict`).
- **Armazenamento de dados:** base de usuários (atualmente em memória, `fake_db.py`), que guarda o hash das senhas.
- **Trust boundaries:**
  1. Entre o Aluno (rede pública / Internet) e o servidor da API -> todo dado que cruza essa fronteira é tratado como não confiável até ser validado (ex: token JWT, corpo da requisição).
  2. Entre a lógica da aplicação (processos) e o armazenamento de credenciais -> separa o código que atende requisições do componente que guarda segredos.

## Diagrama

```mermaid
flowchart TD
    Aluno(["Aluno / Cliente<br/>navegador, app, Postman"])
    
    subgraph Legenda["Legenda"]
      L1["<b>Trust Boundary 1:</b> Internet - Servidor da API<br/><b>Trust Boundary 2:</b> Aplicação - Armazenamento de credenciais"]
    end
    
    Aluno ~~~ Legenda

    subgraph B1["Trust Boundary 1"]
      subgraph API["Processo: API FastAPI - EduBot Analytics"]
        Health["GET /health<br/>Health Check<br/>rota publica"]
        Auth["POST /auth/token<br/>Auth Service<br/>emite JWT"]
        Predict["POST /predict<br/>Predict Service<br/>protegida - placeholder"]
      end
    end

    subgraph B2["Trust Boundary 2"]
      UserStore[("User store<br/>fake_db.py<br/>senha com hash bcrypt")]
    end

    Aluno -- "1: GET /health" --> Health
    Health -- "2: 200 OK" --> Aluno

    Aluno -- "3: POST /auth/token<br/>username + password" --> Auth
    Auth -- "4: consulta usuario e hash" --> UserStore
    UserStore -- "5: hash armazenado" --> Auth
    Auth -- "6: 200 OK access_token<br/>ou 401 credenciais invalidas" --> Aluno

    Aluno -- "7: POST /predict<br/>Authorization Bearer JWT + mensagem" --> Predict
    Predict -- "8: valida JWT e consulta usuario" --> UserStore
    UserStore -- "9: usuario existe ou nao" --> Predict
    Predict -- "10: 401 token invalido ou usuario inexistente<br/>ou 200 OK categoria/urgencia" --> Aluno
```

## Entradas e saídas

**Entradas da API:**

- Credenciais (`username`, `password`) em `POST /auth/token`
- Token JWT no header `Authorization: Bearer <token>` em `POST /predict`
- Corpo da requisição (`mensagem`) em `POST /predict`

**Saídas da API:**

- Status de disponibilidade em `GET /health`
- Token de acesso (JWT) em `POST /auth/token`, ou erro 401 se credenciais inválidas
- Classificação de categoria/urgência (hoje placeholder) em `POST /predict`, ou erro 401 sem token válido
