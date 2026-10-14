# Decisões Técnicas (Infra/Sec)

Aqui estão as principais decisões que tomei na parte de segurança e infraestrutura da API, junto com o motivo de cada uma. As decisões estão separadas por TP. Quando uma decisão do TP2 foi revista no TP3, isso está indicado.

# TP2

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

_Revisto no TP3: a forma de identificar o IP mudou com o deploy, ver abaixo._

Escolhi o limite de 5 tentativas por minuto porque ainda permite que um usuário erre a senha algumas vezes sem ser bloqueado logo de cara, mas reduz bastante a velocidade de uma tentativa de força bruta. Em vez de milhares de tentativas por minuto, o mesmo IP fica limitado a 5.

A contagem é feita por IP, então o bloqueio de um endereço não impede outros usuários de tentarem login ao mesmo tempo.

**Limitação conhecida:** esse contador fica em memória. Se a API reiniciar, ele zera, e também não é compartilhado entre várias instâncias rodando em paralelo. Para este projeto isso é aceitável, mas em produção com vários workers precisaria de outra solução.

## Header "Server": removido via flag do Uvicorn, não por middleware

Primeiro tentei remover o header `Server: uvicorn` dentro do middleware da aplicação, mas não funcionou. O Uvicorn adiciona esse header na camada de transporte, depois que a aplicação já montou a resposta. Por isso, o middleware ASGI não consegue impedir que ele apareça.

A solução que realmente funcionou foi iniciar o servidor usando a flag nativa do Uvicorn.

## Testes: reset do rate limiter entre testes

O `TestClient` do pytest sempre simula o mesmo IP. Sem um reset, tentativas de login feitas em testes diferentes iam se acumulando no mesmo contador e poderiam fazer um teste falhar por um motivo que não tinha relação com o que ele estava validando.

Para evitar isso, usei uma fixture `autouse` que zera o rate limiter antes de cada teste.

# TP3

## Chave do JWT obrigatória, sem valor padrão

No TP2, o `config.py` tinha um valor padrão para a `SECRET_KEY`. Se o `.env` não existisse, a API subia usando uma chave que estava escrita no código público, e qualquer pessoa conseguia criar um token válido para qualquer aluno. Testei isso na prática: um token forjado com essa chave era aceito.

Agora a chave não tem valor padrão. A API se recusa a iniciar se ela não estiver definida, se tiver menos de 32 caracteres ou se for um dos valores de exemplo que já apareceram no repositório. Prefiro que a API não suba a que ela suba insegura. No Render, a chave foi gerada aleatoriamente e só existe nas variáveis de ambiente.

## Troca de bibliotecas: PyJWT e bcrypt

O `pip-audit` encontrou 35 vulnerabilidades conhecidas nas dependências do TP2. A biblioteca do JWT (`python-jose`) tinha falhas próprias e trazia o pacote `ecdsa`, também vulnerável. Troquei pelo `PyJWT`, que é o recomendado hoje pela documentação do FastAPI.

O `passlib` não recebe atualizações há anos e era o motivo de o projeto precisar fixar uma versão antiga do `bcrypt`. Passei a usar o `bcrypt` diretamente, o que tirou uma dependência e permitiu usar a versão atual.

## Mesmo tempo de resposta no login

Quando o usuário não existia, a API respondia na hora. Quando existia, demorava, porque precisava conferir a senha com bcrypt. Medindo o tempo, dava para descobrir quais usuários existem. Agora, para usuário inexistente, a API faz uma verificação bcrypt "de mentira", e os dois casos demoram o mesmo tempo.

## Rate limit atrás de proxy: `cf-connecting-ip`

No Render, a API não recebe a conexão direto do usuário. Na frente dela existem a Cloudflare e os balanceadores do Render. Por isso, o "IP de quem conectou" é sempre o de um desses intermediários.

Primeiro configurei a API para ler o último valor do `X-Forwarded-For`. Os testes locais passavam, mas o teste contra a URL pública mostrou que 7 logins errados seguidos não geravam 429. Os logs mostraram que esse valor era o IP interno do balanceador do Render (`10.x.x.x`). Como existem dois balanceadores, todos os usuários dividiam dois contadores. Isso tinha dois efeitos ruins: o limite real dobrava, e um atacante podia errar a senha de propósito para bloquear o login de todo mundo.

A correção foi ler o IP do header `cf-connecting-ip`, que a Cloudflare preenche com o IP de quem abriu a conexão. Escolhi esse header porque ele não pode ser falsificado: testei enviá-lo do meu lado, e a Cloudflare bloqueou a requisição com 403. Já o `X-Forwarded-For` o cliente consegue escrever, então ele é ignorado. O nome do header é configurável (`CLIENT_IP_HEADER`), para a API continuar funcionando localmente, sem proxy.

Essa foi a decisão mais importante do TP3: mostrou que testar só localmente não basta, porque o ambiente real muda o comportamento dos controles.

## Rate limit também no `/predict`

Coloquei 20 requisições por minuto por IP no `/predict`. É bem acima do que um aluno digitando usaria, mas impede que alguém automatize milhares de chamadas. Isso vai ser mais importante no TP4, quando cada chamada acionar um modelo de linguagem, que tem custo.

## 422 sem repetir o que foi enviado

O tratamento padrão de erro de validação do FastAPI devolve, no campo `input`, o valor que o cliente mandou. Isso reflete dados de volta na resposta, o que é uma porta para ataques de reflexão e pode expor dados em logs de terceiros. Escrevi um tratamento próprio que devolve só o tipo, o local e a mensagem do erro.

## Senhas de teste fora do código

No TP2, as senhas dos usuários de teste (`senha123`) estavam no `seed.py`. Com a API online, isso daria acesso direto às contas. Agora elas vêm de variáveis de ambiente, e um usuário sem senha definida simplesmente não é criado. Também criei um terceiro aluno e solicitações de exemplo para cada um, para a dupla adversária ter o que testar no pentest de BOLA.

## GitHub Actions + ruleset + deploy condicionado

Os testes de segurança e o `pip-audit` rodam a cada push. Sozinho, o CI só avisa; o que impede o merge é o ruleset da `main`, que exige pull request com os dois checks aprovados. No Render, o auto-deploy está configurado para só publicar depois que o CI aprova. Assim, uma regressão de segurança é barrada em três pontos: no PR, na `main` e no deploy. Validei isso com um PR de demonstração que removia a verificação de ownership: os testes de BOLA falharam e o merge ficou bloqueado.

O workflow roda com permissão somente de leitura e não usa nenhum segredo real. A chave dos testes é gerada a cada execução.

## Documentação OpenAPI pública

Mantive `/docs`, `/redoc` e `/openapi.json` públicos. A API vai ser alvo de pentest, e a segurança não pode depender de esconder as rotas. Uma documentação completa também ajuda a dupla adversária a testar o que realmente importa. Um teste garante que toda rota continue documentada com todas as respostas possíveis.

## Python 3.12 no CI e no Render

Fixei a mesma versão do Python no GitHub Actions e no Render (`api/.python-version`), para que o que foi testado seja exatamente o que roda online. Sem isso, o Render usaria a 3.14 por padrão.

