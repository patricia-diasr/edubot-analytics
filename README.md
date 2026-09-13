# EduBot Analytics - Suporte Acadêmico Universitário

## Sobre o projeto

Este repositório contém o desenvolvimento do projeto **EduBot Analytics**, uma gente de IA para suporte acadêmico universitário, atendendo pedidos de matrícula, trancamento de disciplinas e consulta de notas desenvolvido como parte da disciplina **Projeto de Bloco: Análise e Segurança de Agentes de IA**.

O projeto é construído ao longo do bloco em cinco entregas parciais, evoluindo desde a exploração de dados e o setup de uma API segura até a implementação de um agente de IA funcional e um pentest cruzado entre duplas. Este repositório reúne o progresso até o TP2: EDA do dataset, API com autenticação JWT e persistência real, controles OWASP Top 10 auditados via OWASP ZAP, e modelagem de ameaças (DFD + análise CIA).

## Disciplina e equipe

| **Disciplina** | Projeto de Bloco: Análise e Segurança de Agentes de IA |
| --- | --- |
| **Professor(a)** | Ricardo Pires Mesquita |
| **Aluno A - Dados/IA** | Maitê Mota Belo de Souza Silva |
| **Aluno B - Infra/Sec** | Patricia Dias Rodrigues |

## Estrutura do repositório

```
├── api/        # API FastAPI (Infra/Sec), autenticação JWT, rotas base
├── eda/        # Notebook de EDA e dataset (Dados/IA)
│ ├── eda_edubot_tp1.ipynb    # Notebook principal da EDA
│ ├── escolha-do-dataset.md   # Fonte, licença e justificativa do dataset
│ ├── requirements.txt
│ ├── data/                   # Dataset bruto, licença e dataset tratado
│ └── figures/                # Figuras exportadas pelo notebook
├── dfd/        # Diagrama de fluxo de dados (DFD) e análise CIA
├── security/   # Scan OWASP ZAP, findings e decisões técnicas (TP2)
└── README.md   # Este arquivo
```

## API (Infra/Sec)

### O que foi implementado

- Estrutura modular em `api/app/`: `routers/` (rotas), `models/` (schemas Pydantic e tabelas SQLModel), `core/` (configuração, segurança, persistência), `db/` (seed de usuários de teste).
- Autenticação **JWT** com `OAuth2PasswordBearer` (`python-jose` para o token, `passlib`/`bcrypt` para hashing de senha).
- **Persistência real com SQLModel + SQLite**, substituindo o armazenamento em memória do TP1.
- **Controles OWASP Top 10:**
  - `extra='forbid'` em todos os modelos de entrada (rejeita campos inesperados no corpo da requisição).
  - Queries parametrizadas via SQLModel (sem SQL raw).
  - Verificação de **ownership (BOLA)** em `GET /solicitacoes/{id}`, retorna 404 tanto para ID inexistente quanto para recurso de outro usuário.
  - Headers de segurança (HSTS, X-Frame-Options, X-Content-Type-Options, Content-Security-Policy) via middleware.
  - CORS com allowlist explícita de origens.
  - Rate limiting (5/minuto) em `POST /auth/token`, contra força bruta.
- 4 rotas:
  - `GET /health` - pública.
  - `POST /auth/token` - login, retorna JWT (rate limitado).
  - `POST /predict` - protegida, persiste uma `Solicitação` vinculada ao usuário autenticado.
  - `GET /solicitacoes/{id}` - protegida, com verificação de ownership.

### Estrutura do código

```
api/
├── app/
│   ├── main.py                     # cria o app, registra middlewares e rotas
│   ├── core/
│   │   ├── config.py                # settings (variáveis de ambiente)
│   │   ├── hashing.py               # hashing de senha (bcrypt)
│   │   ├── security.py              # JWT, autenticação, dependency de auth
│   │   ├── security_headers.py      # middleware de headers HTTP
│   │   ├── database.py              # engine e sessão do SQLModel
│   │   └── rate_limit.py            # limiter compartilhado (slowapi)
│   ├── models/
│   │   ├── schemas.py                # schemas de entrada/saída (Pydantic)
│   │   └── db_models.py              # tabelas SQLModel (User, Solicitacao)
│   ├── routers/
│   │   ├── health.py
│   │   ├── auth.py
│   │   ├── predict.py
│   │   └── solicitacoes.py
│   └── db/
│       └── seed.py                   # usuários de teste
├── tests/
│   ├── conftest.py                   # fixtures (sessão de teste, client)
│   └── test_security.py              # 4 casos de segurança
├── requirements.txt
├── requirements-dev.txt              # black, pytest, httpx
├── pyproject.toml                    # configuração do Black
└── .env.example
```

### Como instalar (Windows / PowerShell)

```powershell
cd api

# 1. Criar e ativar o ambiente virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Instalar as dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 3. Criar o arquivo de variáveis de ambiente
Copy-Item .env.example .env
# edite o .env e defina uma SECRET_KEY própria
```

### Como rodar

```powershell
uvicorn app.main:app --reload --no-server-header
```

A API sobe em `http://127.0.0.1:8000`. Documentação Swagger em `http://127.0.0.1:8000/docs`.

### Como rodar os testes

```powershell
python -m pytest tests/ -v
```

4 testes cobrindo: acesso sem token, acesso a recurso de outro usuário (BOLA), campo extra no corpo da requisição, e um fluxo válido completo.

### Testando as rotas manualmente

```powershell
# 1. Health check (sem autenticação) - esperado: 200
curl.exe http://127.0.0.1:8000/health

# 2. Login (usuário de teste: aluno.teste / senha123)
curl.exe -X POST http://127.0.0.1:8000/auth/token -d "username=aluno.teste password=senha123"

# 3. Predict com token - cria e retorna uma Solicitação com id
$TOKEN = "cole_aqui_o_access_token_recebido"
curl.exe -X POST http://127.0.0.1:8000/predict -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"mensagem": "Preciso trancar uma disciplina"}'

# 4. Consultar a solicitação pelo id retornado acima
curl.exe http://127.0.0.1:8000/solicitacoes/1 -H "Authorization: Bearer $TOKEN"
```

Também é possível testar pela interface do Swagger em `/docs`, usando o botão **Authorize** após obter o token em `/auth/token`.

### Formatação automática

O projeto usa [Black](https://black.readthedocs.io/) para formatação automática do código Python, com indentação de 4 espaços.

```powershell
python -m black app/
```

### Observações importantes

- A base de usuários em `app/db/seed.py` cria usuários de teste fixos (`aluno.teste` / `senha123`) apenas para validar os fluxos de autenticação e ownership.
- `SECRET_KEY` no `.env.example` é só um placeholder de desenvolvimento, nunca deve ser usada como está, nem versionada.

## DFD e Análise CIA

O diagrama de fluxo de dados (DFD) modela as interações entre o Aluno/Cliente, os três endpoints da API (`GET /health`, `POST /auth/token`, `POST /predict`) e o armazenamento de credenciais (`fake_db.py`), identificando duas trust boundaries, entre o Aluno e o servidor da API, e entre a aplicação e o armazenamento de credenciais.

- **[`dfd/dfd.md`](dfd/dfd.md)** -> diagrama em Mermaid, com a lista de entradas, saídas e trust boundaries identificados.
- **`dfd/dfd.png`** -> imagem exportada do diagrama, gerada a partir do `dfd.md`.
- **[`dfd/analise-cia.md`](dfd/analise-cia.md)** -> análise da tríade CIA (confidencialidade, integridade, disponibilidade) aplicada aos 4 componentes do diagrama.

![DFD do EduBot Analytics](dfd/dfd.png)

Resumo da análise CIA (detalhamento completo em `dfd/analise-cia.md`):

| Componente | Confidencialidade | Integridade | Disponibilidade |
| --- | :---: | :---: | :---: |
| `GET /health` | Baixa | Baixa | Alta |
| `POST /auth/token` | Alta | Alta | Alta |
| `POST /predict` | Alta | Alta | Média |
| `GET /solicitacoes/{id}` | Alta | Alta | Média |
| Banco de dados | Altíssima | Alta | Média |

## EDA (Análise Exploratória de Dados)

Usamos o dataset **Bitext - Customer Service Tagged Training Dataset** (Bitext Innovations, 2024, licença CDLA-Sharing-1.0): 26.872 registros em inglês, com texto livre (`instruction`) e rótulo em duas camadas (`category` → `intent`). A justificativa completa, licença e alternativas descartadas estão em `[eda/escolha-do-dataset.md](eda/escolha-do-dataset.md)`.

A análise está no notebook `[eda/eda_edubot_tp1.ipynb](eda/eda_edubot_tp1.ipynb)`. Em resumo:

- **Saída:** 26.872 → **21.006 registros × 17 colunas** (78,2% retidos), em `eda/data/edubot_dataset_tratado.csv`
- **Limpeza:** removi duplicatas do par (`instruction`, `intent`) (−2.237), descartei 4 intenções logísticas sem equivalente acadêmico (−3.629) e remapeei as 23 restantes para o vocabulário do EduBot
- **Categorias finais:** FINANCEIRO (30,7%), ACADEMICO (28,6%), SUPORTE (14,3%), CADASTRO (12,2%), FEEDBACK (9,5%), ACESSO (4,7%)
- **Figuras:** 6 gráficos em `[eda/figures/](eda/figures/)`



### Hipóteses (detalhes na seção 7 do notebook)


| Hipótese                                              | Resultado  | O que isso muda                                                                      |
| ----------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------ |
| H1 — pedidos com justificativa são mais longos        | Parcial    | `n_palavras` pode ser feature auxiliar, mas o sinal principal continua sendo o texto |
| H2 — hostilidade indica o tipo de pedido              | Refutada   | `urgencia_proxy` não serve; no TP2 precisamos de rótulo de urgência de verdade       |
| H3 — ~49% das mensagens têm typo, gíria ou abreviação | Confirmada | Filtro por palavra-chave não segura; defesa precisa ser semântica                    |
| H4 — ~17% dos pedidos são de cadastro ou acesso       | Confirmada | Reforça a necessidade de checar dono do recurso (IDOR) no TP2                        |




### Limitações

Dataset sintético, em inglês, com vocabulário de e-commerce (adaptamos os rótulos, não as frases). Sem rótulo de urgência utilizável. As hipóteses ainda são observacionais — teste estatístico fica pro TP2.

### Como rodar

```powershell
cd eda
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
jupyter notebook eda_edubot_tp1.ipynb
```

O notebook roda de ponta a ponta com os dados já em `eda/data/`.

---



## Uso de IA neste trabalho

Conforme a política de Sinal Verde do enunciado:

- Usei o **Claude** na triagem de datasets, pra montar a estrutura do notebook e revisar texto.
- Escolha do dataset, mapeamento de domínio, limpeza e hipóteses foram decisões minhas - revisei tudo antes de entregar.
- Os números citados aqui e no notebook vêm da execução do código sobre `eda/data/`; dá pra reproduzir rodando o notebook.
- Usei o **Claude** como ferramenta auxiliar na escrita do código da API, no entendimento do funcionamento dos componentes e na identificação e correção de bugs.
- As decisões de implementação, a revisão do código e a validação das soluções foram realizadas por mim.
