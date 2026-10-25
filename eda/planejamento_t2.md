# Planejamento técnico do T2

## Objetivo

No T2, o EduBot vai receber uma mensagem e prever uma das 23 intenções
documentadas em `pergunta_classificacao_tp3.md`.

O primeiro objetivo não é buscar o modelo mais complexo. É criar um baseline
simples, reproduzível e fácil de analisar. Depois disso, podemos comparar outro
modelo usando exatamente a mesma separação dos dados.

## Modelo candidato

O baseline será uma **regressão logística multiclasse**. Apesar do nome, esse é
um modelo de classificação. Ele funciona bem com matrizes esparsas de texto,
treina rápido e permite inspecionar quais termos tiveram mais peso em cada
classe.

O segundo candidato será o **SVM linear**, usando `LinearSVC`. Ele costuma ter
bom resultado em classificação de texto e será comparado com o baseline pela
Macro-F1. A escolha final será feita pelas métricas e pela análise dos erros, não
apenas pela acurácia.

## Features de texto

O texto será transformado com TF-IDF. A configuração inicial será:

- palavras em unigramas e bigramas;
- conversão para minúsculas;
- `min_df=2` para retirar termos que aparecem uma única vez;
- `sublinear_tf=True` para reduzir o peso de repetições;
- limite de features ajustado apenas se o consumo de memória exigir.

O `TfidfVectorizer` e o classificador ficarão no mesmo `Pipeline` do
scikit-learn. O pipeline será ajustado apenas no conjunto de treino. Isso evita
que o vocabulário ou o IDF do teste vazem para o treinamento.

## Separação e avaliação

Os dados serão divididos de forma estratificada em treino, validação e teste.
Uma proposta inicial é 70% para treino, 15% para validação e 15% para teste, com
`random_state` fixo.

As métricas planejadas são:

- Macro-F1 como métrica principal;
- precision e recall por classe;
- acurácia como visão geral;
- matriz de confusão;
- comparação com o baseline da classe mais frequente.

Antes da divisão, vamos procurar textos idênticos ou quase idênticos. O Bitext é
sintético e tem variações de templates, então uma divisão aleatória pode gerar
um resultado otimista se mensagens muito parecidas aparecerem nos dois lados.

## Integração futura com a API

O treinamento será feito fora da API. O pipeline escolhido será salvo com sua
versão e carregado uma vez na inicialização do FastAPI. Ele não será treinado a
cada chamada.

O contrato planejado para `POST /predict` é:

- entrada: texto validado, não vazio e dentro do limite de tamanho;
- saída: intenção prevista, versão do modelo e, quando o modelo permitir, score
  de confiança;
- autenticação e rate limiting continuam ativos;
- logs não devem guardar o texto completo nem dados pessoais;
- entradas inválidas devem continuar retornando erro estruturado.

## Limitações que precisam acompanhar o modelo

O Bitext é sintético, em inglês e voltado a e-commerce. Os rótulos foram
adaptados, mas as frases não viraram mensagens acadêmicas. O baseline vai ajudar
a validar o pipeline técnico, mas não deve ser apresentado como pronto para uso
com alunos reais.

A amostra acadêmica em português ainda é pequena e os rótulos precisam de
revisão humana. Ela pode ser usada para uma avaliação de domínio depois dessa
revisão, sem misturar seus textos não licenciados ao repositório.

## Equipe adversária e API alvo

| Item | Situação no TP3 |
| --- | --- |
| Colega ou equipe adversária | A definir pelo professor após a entrega |
| URL ou IP da API alvo | A definir pelo professor após a entrega |
| Confirmação de acesso | Será registrada assim que o pareamento for informado |

Esses campos ficam em aberto por orientação do professor. Na aula de 07/10/2026,
ele explicou que determinaria quem ataca quem depois de receber as entregas. Nas
aulas de 14/10/2026 e 21/10/2026, confirmou que faria o pareamento entre equipes
com entregas equivalentes para não prejudicar nenhum grupo.

Depois da definição, vamos registrar o nome da equipe, a URL ou IP, os endpoints
permitidos, as credenciais de teste, o período e a confirmação explícita de
acesso antes de iniciar qualquer teste.
