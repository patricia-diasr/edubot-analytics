# Decisões Técnicas - TP2 (Infra/Sec)

Aqui estão as principais decisões que tomei na parte de segurança e infraestrutura da API, junto com o motivo de cada uma.

## Persistência: SQLite via SQLModel

No TP1, os dados ficavam só em memória no `fake_db.py`. Neste TP, troquei isso por SQLite porque ele funciona bem para um projeto local e não precisa de um servidor de banco separado. Um único arquivo (`edubot.db`) já resolve o que eu precisava aqui.

Não seria uma boa escolha para uma aplicação em produção com várias réplicas, mas para este projeto acadêmico atende bem. Também usei SQLModel, que trabalha com queries parametrizadas por padrão e ajuda a cobrir o controle correspondente da OWASP.

## Novo recurso: `Solicitação`

No TP1, a API só tinha o `/predict` e não guardava estado. Não existia uma rota para buscar um recurso por ID. Para conseguir implementar e testar ownership/BOLA de verdade, criei o recurso `Solicitação`.

Agora, cada chamada a `POST /predict` salva um registro ligado ao usuário autenticado, e esse registro pode ser buscado em `GET /solicitacoes/{id}`.

## Ownership (BOLA): 404 em vez de 403

Quando um aluno tenta acessar a solicitação de outra pessoa, escolhi retornar **404** em vez de 403. Se a API respondesse 403, ela estaria confirmando que aquele ID existe, só não pertence ao usuário atual. Isso já seria uma informação que poderia ajudar alguém a enumerar IDs válidos.

Com 404, para quem está chamando a API, “não existe” e “não é seu” acabam tendo a mesma resposta.

## Content Security Policy

**Exceção só para `/docs` e `/redoc`:** no começo, eu também tinha colocado `/openapi.json` na lista de exceções da CSP. Depois percebi que não precisava. Quem carrega JavaScript de CDN são as páginas HTML do Swagger e do Redoc. O `/openapi.json` é só JSON e não executa nada. O scan do ZAP confirmou que dava para tirar essa exceção.

**Diretivas explícitas (`frame-ancestors`, `base-uri`, `form-action`):** essas diretivas não herdam o `default-src` da mesma forma que várias diretivas de fetch. Então, se não forem declaradas, ficam sem uma restrição específica. O ZAP apontou isso como finding Médio, e eu corrigi adicionando as três de forma explícita.

## CORS: allowlist de desenvolvimento local

Ainda não existe um frontend real integrado ao projeto. Por isso, a allowlist (`CORS_ORIGINS`) ficou voltada para portas comuns de desenvolvimento local, como `localhost:3000`.

Também evitei deixar métodos e headers como `"*"`. `allow_methods` e `allow_headers` ficaram só com o que a API usa hoje: `GET`/`POST` e `Authorization`/`Content-Type`.

## Rate limiting: 5 requisições por minuto em `/auth/token`

Escolhi o limite de 5 tentativas por minuto porque ainda permite que um usuário erre a senha algumas vezes sem ser bloqueado logo de cara, mas reduz bastante a velocidade de uma tentativa de força bruta. Em vez de milhares de tentativas por minuto, o mesmo IP fica limitado a 5.

A contagem é feita por IP, então o bloqueio de um endereço não impede outros usuários de tentarem login ao mesmo tempo.

**Limitação conhecida:** esse contador fica em memória. Se a API reiniciar, ele zera, e também não é compartilhado entre várias instâncias rodando em paralelo. Para este projeto isso é aceitável, mas em produção com vários workers precisaria de outra solução.

## Header "Server": removido via flag do Uvicorn, não por middleware

Primeiro tentei remover o header `Server: uvicorn` dentro do middleware da aplicação, mas não funcionou. O Uvicorn adiciona esse header na camada de transporte, depois que a aplicação já montou a resposta. Por isso, o middleware ASGI não consegue impedir que ele apareça.

A solução que realmente funcionou foi iniciar o servidor usando a flag nativa do Uvicorn.

## Testes: reset do rate limiter entre testes

O `TestClient` do pytest sempre simula o mesmo IP. Sem um reset, tentativas de login feitas em testes diferentes iam se acumulando no mesmo contador e poderiam fazer um teste falhar por um motivo que não tinha relação com o que ele estava validando.

Para evitar isso, usei uma fixture `autouse` que zera o rate limiter antes de cada teste.
