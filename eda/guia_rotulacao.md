# Guia de rotulação da amostra acadêmica

## Objetivo

A amostra complementa o Bitext com perguntas em português e ligadas ao cotidiano universitário. Ela não substitui o dataset do TP1. Serve para medir a distância entre os dois domínios e preparar uma base mais adequada para as próximas etapas.

## Fonte

As perguntas vêm do dataset [liteofspace/unb-chatbot-dpo](https://huggingface.co/datasets/liteofspace/unb-chatbot-dpo), revisão `f2b6170`, com 1.105 pares nos splits de treino e validação.

O dataset não declara licença. Por isso, o repositório não redistribui o texto das perguntas. O script `preparar_amostra_academica.py` baixa os dados da fonte e cria:

- um cache local com os textos, ignorado pelo Git;
- um manifesto versionável com identificadores, hashes e rótulos.

O corpus tem perguntas ligadas a fontes institucionais da UnB, mas inclui variações geradas. Ele é mais próximo do domínio acadêmico que o Bitext, porém não deve ser descrito como log real de atendimento.

## Categorias

- `ACADEMICO`: matrícula, trancamento, disciplinas, notas, estágio, currículo e formatura;
- `FINANCEIRO`: bolsas, auxílios, taxas e pagamentos;
- `ACESSO`: senha, login, portal e sistemas acadêmicos;
- `CADASTRO`: dados pessoais, documentos, histórico e vínculo;
- `SUPORTE`: contato, erro técnico ou encaminhamento para atendimento;
- `FEEDBACK`: reclamação, recurso, revisão ou denúncia.

Quando mais de uma categoria aparecer, vale o assunto que determina a providência principal.

## Urgência

A urgência deve considerar prazo e impacto acadêmico, não o tom da mensagem.

- `alta`: há prazo imediato explícito, bloqueio de acesso em momento crítico ou risco concreto de perda acadêmica;
- `media`: o pedido envolve prazo ou processo sensível, mas o texto não indica vencimento imediato;
- `baixa`: dúvida informativa sem prazo ou prejuízo próximo;
- `indeterminada`: faltam dados para avaliar prazo e impacto.

Na dúvida entre `baixa` e `indeterminada`, use `indeterminada`. Não se deve inventar contexto.

## Processo de revisão

1. Execute `python preparar_amostra_academica.py`.
2. Abra `data/cache/amostra_academica_com_texto.csv`.
3. Confira `categoria_rascunho` e `urgencia_rascunho`.
4. Preencha `categoria_revisada`, `urgencia_revisada` e altere `status_revisao` para `revisado`.
5. Copie apenas as colunas sem texto para `data/amostra_academica_rotulada.csv`.

Os rótulos iniciais são uma triagem automática e não são considerados rótulos humanos. Até a revisão terminar, análises que os utilizem devem ser chamadas de exploratórias.

## Uso de IA

O Cursor foi usado para preparar o script, propor a primeira triagem e revisar a documentação. A decisão final sobre cada rótulo cabe à autora do trabalho.
