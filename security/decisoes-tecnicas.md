# Decisões Técnicas - TP2 (Infra/Sec)

Registro das decisões de design tomadas na implementação dos controles de segurança da API neste TP2, com a justificativa de cada uma.

## Persistência: SQLite via SQLModel

Substituiu o armazenamento em memória do TP1 (`fake_db.py`). SQLite foi escolhido por não exigir nenhum setup de servidor de banco separado, um único arquivo (`edubot.db`) já é suficiente para o escopo do projeto. Não seria adequado para produção com múltiplas réplicas, mas atende bem a uma API rodando localmente para fins acadêmicos. O SQLModel garante queries parametrizadas por padrão, atendendo ao controle OWASP correspondente.

## Novo recurso: `Solicitação`

A API do TP1 não tinha nenhuma rota que retornasse um recurso por ID, só `/predict`, sem estado. Para implementar e testar verificação de ownership (BOLA) de forma real, foi criado o recurso `Solicitação`, em que cada chamada a `POST /predict` agora persiste um registro vinculado ao usuário autenticado, recuperável via `GET /solicitacoes/{id}`.

## Ownership (BOLA): 404 em vez de 403

Quando um aluno tenta acessar a solicitação de outro, a API responde **404**, não 403. Um 403 confirmaria que aquele ID existe e pertence a alguém, o que seria um vazamento de informação que permitiria enumerar IDs válidos observando a diferença entre 403 e 404. Do ponto de vista de quem chama a API, "não existe" e "não é seu" são indistinguíveis.

## Content Security Policy

**Escopo da exceção - só `/docs` e `/redoc`:** inicialmente o `/openapi.json` também estava na lista de exceção da CSP, mas isso era desnecessário, já que só as páginas HTML de documentação (Swagger/Redoc) carregam JS de CDNs externos. O `/openapi.json` é um arquivo JSON estático, que não executa nada, e portanto não precisava da exceção, e o scan do ZAP confirmou isso.

**Diretivas explícitas (`frame-ancestors`, `base-uri`, `form-action`):** essas diretivas não são cobertas pelo fallback de `default-src`, diferente da maioria das diretivas de fetch (script-src, img-src, etc.), elas ficam sem nenhuma restrição a menos que sejam declaradas explicitamente. Identificado pelo scan do ZAP (finding Médio, corrigido).

## CORS: allowlist de desenvolvimento local

Não existe um frontend real integrado ao projeto ainda, então a allowlist (`CORS_ORIGINS`) aponta para portas comuns de dev local (`localhost:3000`). `allow_methods` e `allow_headers` ficaram restritos ao que a API realmente usa (`GET`/`POST`, `Authorization`/`Content-Type`), em vez de `"*"`.

## Rate limiting: 5 requisições por minuto em `/auth/token`

Esse número busca um equilíbrio, é generoso o suficiente para um aluno real errar a senha algumas vezes por engano, mas reduz drasticamente a velocidade de um ataque de força bruta,de milhares de tentativas por minuto para 5. A contagem é por IP, então um IP bloqueado não afeta outros usuários logando ao mesmo tempo.

**Limitação conhecida:** a contagem é em memória, então reseta se a API reiniciar e não é compartilhada entre múltiplas instâncias rodando em paralelo, aceitável para este projeto, mas seria um problema em produção com múltiplos workers.

## Header "Server": removido via flag do Uvicorn, não por middleware

Uma tentativa inicial de remover o header `Server: uvicorn` dentro do middleware da aplicação não funcionou: o Uvicorn reinsere esse header na camada de transporte, depois que a aplicação já respondeu, nenhum middleware ASGI consegue impedir isso. A correção efetiva foi subir o servidor com a flag nativa.

## Testes: reset do rate limiter entre testes

Como o `TestClient` do pytest sempre simula o mesmo IP, logins de testes diferentes se acumulariam na mesma contagem do rate limiter, podendo derrubar um teste por um motivo desconectado do que ele verifica. Resolvido com uma fixture `autouse` que zera o limiter antes de cada teste.
