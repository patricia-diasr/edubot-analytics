# Deploy da API no Render

A API está publicada no [Render](https://render.com), no plano gratuito, como um **Web
Service** criado pelo painel. Este documento registra a configuração usada, para que o
serviço possa ser recriado e auditado.

**URL pública:** https://edubot-analytics.onrender.com (documentação em [/docs](https://edubot-analytics.onrender.com/docs))

## Configuração do serviço

| Campo no painel | Valor | Por quê |
| --- | --- | --- |
| Source | `patricia-diasr/edubot-analytics` | Acesso do Render ao GitHub limitado a este repositório |
| Branch | `tp3-infra-sec` (passa a ser `main` após a integração do TP3) | |
| Language | Python 3 | Versão fixada em `api/.python-version` (3.12, a mesma do GitHub Actions) |
| Region | Virginia (US East) | Região gratuita mais próxima do Brasil |
| Root Directory | `api` | O código da API fica nessa pasta |
| Build Command | `pip install -r requirements.txt` | Instala as dependências fixadas e auditadas pelo pip-audit |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT --no-server-header` | `--no-server-header` mantém a correção do ZAP do TP2 (não revela o servidor) |
| Instance Type | Free | 512 MB, dorme após 15 min sem uso |
| Health Check Path | `/health` | O Render usa essa rota para saber se a API está no ar |
| Auto-Deploy | After CI Checks Pass | Uma versão nova só é publicada se os testes e o pip-audit do GitHub Actions passarem |

## Variáveis de ambiente

| Variável | Valor | Observação |
| --- | --- | --- |
| `SECRET_KEY` | gerada aleatoriamente | Chave de assinatura do JWT. Nunca aparece no código nem no repositório. A API não inicia sem ela |
| `CLIENT_IP_HEADER` | `cf-connecting-ip` | A API fica atrás da Cloudflare e dos balanceadores do Render. O IP real do cliente vem nesse header, escrito pela Cloudflare (ver `api/app/core/rate_limit.py` e a seção abaixo) |
| `SEED_PASSWORD_ALUNO1` | definida no painel | Senha do usuário de teste `aluno.teste` |
| `SEED_PASSWORD_ALUNO2` | definida no painel | Senha do usuário de teste `aluno.teste2` |
| `SEED_PASSWORD_ALUNO3` | definida no painel | Senha do usuário de teste `aluno.teste3` |

As senhas dos usuários de teste são entregues à dupla adversária no plano de escopo do
pentest, e não ficam registradas no repositório.

## Limitações conhecidas do plano gratuito

- **Hibernação:** depois de 15 minutos sem acesso, o serviço "dorme" e o primeiro acesso
  seguinte leva cerca de 50 segundos.
- **Banco efêmero:** o SQLite fica no disco do serviço, que é apagado a cada novo deploy
  ou reinício. Os usuários e solicitações de teste são recriados automaticamente na
  inicialização, o que também desfaz qualquer alteração feita durante o pentest.
- **Rate limit em memória:** o contador também zera quando o serviço reinicia. Como há
  uma única instância, o limite continua valendo enquanto ela está no ar.

## Rate limit atrás do proxy (achado da verificação pós-deploy)

Na primeira versão publicada, o rate limit usava `TRUSTED_PROXY_HOPS=1` (último valor do
`X-Forwarded-For`). O teste contra a URL pública mostrou que **7 tentativas de login
seguidas não geravam 429**. Os logs revelaram o motivo: o último valor do
`X-Forwarded-For` é o IP interno do balanceador do Render (`10.x.x.x`), e não o do
cliente. Como há dois balanceadores, todos os usuários dividiam apenas dois contadores:

- o limite efetivo subia para ~10 tentativas por minuto;
- um atacante podia esgotar o contador de propósito e bloquear o login de todos os
  usuários (negação de serviço).

**Correção:** o IP do cliente passou a ser lido do header `cf-connecting-ip`, que a
Cloudflare (camada na frente do Render) preenche com o IP de quem abriu a conexão,
sobrescrevendo qualquer valor enviado pelo cliente. O `X-Forwarded-For` enviado pelo
cliente continua sendo ignorado. As tentativas de login que falham registram em log os
headers de IP recebidos, para investigação.
