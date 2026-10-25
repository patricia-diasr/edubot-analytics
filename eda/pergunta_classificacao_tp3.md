# Pergunta de classificação do TP3

## Definição da tarefa

A pergunta que queremos responder no T2 é:

> Dado o texto de uma mensagem de atendimento, qual é a intenção do usuário?

A entrada será o texto livre da coluna `instruction`. A saída será uma das 23
classes da coluna `intent_edubot`. É uma tarefa de classificação multiclasse
supervisionada, porque cada exemplo do dataset já tem uma intenção associada.

O objetivo é usar a intenção para encaminhar a solicitação ou escolher o próximo
passo do atendimento. A classificação de urgência continua sendo uma tarefa
separada. O Bitext não tem um rótulo de urgência confiável.

## Classes e distribuição

O dataset tratado tem 21.006 mensagens. As classes ficaram relativamente
equilibradas, mas `disciplina_trancar` tem apenas 493 exemplos e merece atenção
na avaliação.

| Intenção | O que representa | Mensagens | Percentual |
| --- | --- | ---: | ---: |
| `acesso_recuperar_senha` | Recuperar senha ou acesso | 995 | 4,74% |
| `cadastro_atualizar_dados` | Atualizar dados cadastrais | 777 | 3,70% |
| `cadastro_cancelar_vinculo` | Cancelar um vínculo | 918 | 4,37% |
| `cadastro_trocar_vinculo` | Trocar um vínculo existente | 862 | 4,10% |
| `disciplina_alterar` | Alterar uma disciplina | 870 | 4,14% |
| `disciplina_inscrever` | Fazer inscrição em disciplina | 998 | 4,75% |
| `disciplina_trancar` | Trancar uma disciplina | 493 | 2,35% |
| `feedback_avaliacao` | Enviar uma avaliação | 997 | 4,75% |
| `feedback_reclamacao` | Registrar uma reclamação | 1.000 | 4,76% |
| `financeiro_acompanhar_reembolso` | Acompanhar um reembolso | 707 | 3,37% |
| `financeiro_consultar_boleto` | Consultar um boleto | 921 | 4,38% |
| `financeiro_emitir_boleto` | Emitir um boleto | 909 | 4,33% |
| `financeiro_formas_pagamento` | Consultar formas de pagamento | 999 | 4,76% |
| `financeiro_politica_reembolso` | Consultar regras de reembolso | 997 | 4,75% |
| `financeiro_problema_pagamento` | Relatar problema de pagamento | 999 | 4,76% |
| `financeiro_solicitar_reembolso` | Pedir um reembolso | 918 | 4,37% |
| `matricula_problema` | Relatar problema de matrícula | 999 | 4,76% |
| `matricula_solicitar` | Solicitar matrícula | 892 | 4,25% |
| `solicitacao_consultar_status` | Consultar andamento de uma solicitação | 807 | 3,84% |
| `suporte_atendente_humano` | Pedir atendimento humano | 999 | 4,76% |
| `suporte_comunicados` | Consultar comunicados | 999 | 4,76% |
| `suporte_contato_secretaria` | Pedir contato da secretaria | 1.000 | 4,76% |
| `trancamento_consultar_regra` | Consultar regras de trancamento | 950 | 4,52% |

A distribuição também está em
`figures/fig12_distribuicao_intencoes_tp3.png`.

## Ambiguidades esperadas

Algumas classes são próximas. Uma mensagem sobre reembolso pode pedir a
política, iniciar a solicitação ou apenas acompanhar o andamento. Também pode
haver confusão entre problema de matrícula, inscrição em disciplina e alteração
de disciplina. O modelo vai precisar aprender o contexto, não só palavras
isoladas.

Existe ainda uma limitação maior. Os rótulos foram adaptados para o EduBot, mas
os textos do Bitext continuam em inglês e falam de e-commerce. Por isso, uma boa
métrica nesse dataset não prova que o modelo funcionará com alunos escrevendo
em português.

## Por que regressão linear não resolve

As intenções são categorias nominais. Não existe uma ordem em que
`acesso_recuperar_senha` valha menos ou mais que `matricula_solicitar`. Se cada
classe recebesse um número, a regressão trataria a distância entre esses números
como algo real e poderia devolver valores contínuos sem significado, como 3,7.

A regressão do notebook do TP3 prevê `n_chars` e serve para estudar R², RMSE e
resíduos. Para prever intenção, precisamos de um classificador supervisionado
que escolha entre as 23 classes e possa ser avaliado por classe.

## Critério de sucesso no T2

O primeiro baseline será avaliado com Macro-F1, precision, recall e matriz de
confusão. A Macro-F1 terá destaque porque dá o mesmo peso a cada intenção,
inclusive à classe com menos exemplos. Também vamos comparar o resultado com um
baseline simples que sempre prevê a classe mais frequente.
