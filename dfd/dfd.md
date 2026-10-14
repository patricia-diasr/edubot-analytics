# DFD - EduBot Analytics

**Versão 3 (TP3).** O diagrama foi atualizado para refletir a API publicada no Render: a
borda da plataforma (Cloudflare + balanceador do Render), os segredos em variáveis de
ambiente, os logs de segurança, a documentação OpenAPI e a cadeia de entrega (GitHub,
GitHub Actions e deploy). O histórico das versões está no fim do documento.

O DFD foi dividido em dois diagramas, escritos em Mermaid neste arquivo. As imagens PNG
(`dfd-v3-requisicao.png` e `dfd-v3-cicd.png`) são geradas a partir deles com
`python dfd/gerar_imagens.py`. A imagem da versão anterior está em `historico/`.

- **Diagrama 1, fluxo de uma requisição:** o caminho dos dados quando um aluno usa a API.
- **Diagrama 2, cadeia de entrega:** o caminho do código até a API publicada.

## Elementos do diagrama

- **Entidades externas:**
  - **Aluno / Cliente:** usuário não confiável que acessa a API pela Internet (navegador, Swagger, Postman).
  - **Desenvolvedoras:** a dupla, que envia código ao repositório.
- **Processos:**
  - **Borda da plataforma (Cloudflare + balanceador do Render):** termina o HTTPS, redireciona HTTP para HTTPS e escreve o header `cf-connecting-ip` com o IP real do cliente.
  - **Middlewares da API:** headers de segurança, CORS e rate limit por IP real.
  - **Rotas da API:** `GET /health`, `GET /docs` (e `/openapi.json`), `POST /auth/token`, `POST /predict` e `GET /solicitacoes/{id}`.
  - **GitHub Actions:** roda os testes de segurança e o `pip-audit`.
  - **Render (build e deploy):** publica uma versão nova só depois que o CI aprova.
- **Armazenamentos de dados:**
  - **Banco SQLite** (via SQLModel), com as tabelas `User` (credenciais) e `Solicitacao`.
  - **Variáveis de ambiente do Render:** `SECRET_KEY` (gerada pelo Render) e senhas dos usuários de teste.
  - **Logs do Render:** tentativas de login que falharam (usuário, IP e headers de IP, nunca a senha).
  - **Repositório GitHub:** código-fonte, protegido pelo ruleset da `main`.

## Trust boundaries

1. **Internet → borda da plataforma:** tudo que vem do cliente é não confiável, inclusive
   headers como `X-Forwarded-For`, que o cliente pode escrever. A partir daqui o tráfego é
   HTTPS.
2. **Borda → aplicação:** a aplicação confia **somente** no header `cf-connecting-ip`, que
   a Cloudflare sobrescreve (tentar enviá-lo do cliente é bloqueado com 403). Corpo, token
   e parâmetros continuam não confiáveis até serem validados pela API.
3. **Aplicação → dados:** separa o código que atende requisições dos dados persistentes e
   dos segredos. Só a aplicação acessa o banco, as variáveis de ambiente e os logs.
4. **Cadeia de entrega (CI/CD):** separa quem escreve código do que vai para produção. O
   código só chega à `main` por pull request com os checks aprovados, e só é publicado
   depois do CI.

## Diagrama 1: fluxo de uma requisição

![DFD v3 - fluxo de uma requisição](dfd-v3-requisicao.png)

<details>
<summary>Código Mermaid do diagrama</summary>

```mermaid
flowchart TB
    Aluno(["Aluno / Cliente<br/>navegador, Swagger, Postman"])

    subgraph TB1["Trust Boundary 1: Internet → borda da plataforma"]
      Edge["Cloudflare + balanceador do Render<br/>HTTPS (TLS), redireciona HTTP para HTTPS<br/>escreve cf-connecting-ip"]
    end

    subgraph TB2["Trust Boundary 2: borda → aplicação"]
      subgraph API["Processo: API FastAPI (Render, plano gratuito)"]
        MW["Middlewares<br/>headers de segurança, CORS<br/>rate limit por IP real"]
        Health["GET /health<br/>pública"]
        Docs["GET /docs, /openapi.json<br/>pública, documentação"]
        Auth["POST /auth/token<br/>emite JWT, 5 por minuto"]
        Predict["POST /predict<br/>exige JWT, 20 por minuto"]
        Solic["GET /solicitacoes/id<br/>exige JWT, verifica ownership"]
      end
    end

    subgraph TB3["Trust Boundary 3: aplicação → dados"]
      DB[("Banco SQLite<br/>User, Solicitacao")]
      Env[("Variáveis de ambiente<br/>SECRET_KEY, SEED_PASSWORD_*")]
      Logs[("Logs do Render<br/>login_falhou: usuário e IP")]
    end

    Aluno -- "1: requisição HTTPS<br/>credenciais, JWT, mensagem, id" --> Edge
    Edge -- "2: requisição + cf-connecting-ip" --> MW
    MW -- "3" --> Health
    MW -- "3" --> Docs
    MW -- "3" --> Auth
    MW -- "3" --> Predict
    MW -- "3" --> Solic
    Auth -- "5: consulta User e hash bcrypt" --> DB
    Auth -- "6: registra login com falha" --> Logs
    Predict -- "7: grava Solicitacao do aluno do token" --> DB
    Solic -- "8: lê Solicitacao e o dono" --> DB
    Predict ~~~ Env
    Env -. "4: chave do JWT e senhas de teste<br/>lidas na inicialização" .-> MW
    MW -- "9: resposta + headers de segurança<br/>200, 401, 404, 422 ou 429" --> Edge
    Edge -- "10: resposta HTTPS" --> Aluno
```

</details>

## Diagrama 2: cadeia de entrega (CI/CD)

![DFD v3 - cadeia de entrega](dfd-v3-cicd.png)

<details>
<summary>Código Mermaid do diagrama</summary>

```mermaid
flowchart LR
    Dev(["Desenvolvedoras<br/>Patricia e Maitê"])

    subgraph TB4["Trust Boundary 4: cadeia de entrega"]
      Repo[("Repositório GitHub<br/>ruleset: main só por PR<br/>com checks aprovados")]
      GHA["GitHub Actions<br/>pytest + pip-audit<br/>permissão somente leitura"]
      Deploy["Render: build e deploy<br/>só após o CI aprovar"]
      Segredos[("Variáveis de ambiente do Render<br/>SECRET_KEY gerada, senhas de teste")]
    end

    Prod["API em produção<br/>edubot-analytics.onrender.com"]

    Dev -- "1: push e pull request" --> Repo
    Repo -- "2: dispara o workflow" --> GHA
    GHA -- "3: resultado dos checks<br/>falha bloqueia o merge" --> Repo
    Repo -- "4: código com checks aprovados" --> Deploy
    Segredos -. "5: injetados no ambiente" .-> Deploy
    Deploy -- "6: publica a nova versão" --> Prod
```

</details>

## Entradas e saídas

**Entradas da API:**

- Credenciais (`username`, `password`) em `POST /auth/token`
- Token JWT no header `Authorization: Bearer <token>` em `POST /predict` e `GET /solicitacoes/{id}`
- Corpo da requisição (`mensagem`, até 2000 caracteres, sem campos extras) em `POST /predict`
- ID da solicitação (parâmetro de rota, inteiro maior ou igual a 1) em `GET /solicitacoes/{id}`
- Header `cf-connecting-ip`, escrito pela Cloudflare, usado pelo rate limit
- Variáveis de ambiente (`SECRET_KEY`, `SEED_PASSWORD_*`), lidas na inicialização

**Saídas da API:**

- Status de disponibilidade em `GET /health`
- Especificação OpenAPI em `/openapi.json` e página de documentação em `/docs`
- Token de acesso (JWT) em `POST /auth/token`, ou 401 (credenciais inválidas), 422 (formulário inválido) ou 429 (limite excedido, com `Retry-After`)
- Solicitação criada (id, categoria, urgência) em `POST /predict`, ou 401, 422 ou 429
- Dados da solicitação em `GET /solicitacoes/{id}`, se pertencer ao aluno autenticado, ou 404 (inexistente ou de outro aluno), 401 ou 422
- Headers de segurança (HSTS, X-Frame-Options, X-Content-Type-Options, CSP) em todas as respostas
- Registros de login com falha nos logs do Render

## Histórico de versões

| Versão | TP | O que mudou |
| --- | --- | --- |
| 1 | TP1 | Três rotas (`/health`, `/auth/token`, `/predict`) e credenciais em memória (`fake_db.py`). Duas trust boundaries |
| 2 | TP2 | Persistência em SQLite via SQLModel, rota `GET /solicitacoes/{id}` com ownership e rate limit no login |
| 3 | TP3 | API publicada no Render: borda Cloudflare/Render com HTTPS, segredos em variáveis de ambiente, logs de segurança, documentação OpenAPI, rate limit no `/predict`, cadeia de entrega (GitHub Actions + deploy condicionado ao CI). Quatro trust boundaries |
