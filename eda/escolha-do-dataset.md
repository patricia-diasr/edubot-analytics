# Documento de escolha do dataset — TP1

**Projeto:** EduBot Analytics — Suporte Acadêmico Universitário  
**Disciplina:** Projeto de Bloco: Análise e Segurança de Agentes de IA  
**Professor:** Ricardo Pires Mesquita  
**Responsável por esta etapa:** Maitê Mota Belo de Souza Silva (Aluno A — Dados/IA)

---

## 1. Identificação

| Campo | Valor |
|---|---|
| **Nome** | Bitext — Customer Service Tagged Training Dataset for LLM-based Virtual Assistants |
| **Autor** | Bitext Innovations, 2024 |
| **Fonte (Hugging Face)** | https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset |
| **Fonte (GitHub)** | https://github.com/bitext/customer-support-llm-chatbot-training-dataset |
| **Licença** | Community Data License Agreement — Sharing, Version 1.0 (CDLA-Sharing-1.0) |
| **Arquivo no repositório** | `eda/data/Bitext_Sample_Customer_Support_Training_Dataset_27K_responses-v11.csv` |
| **Cópia da licença** | `eda/data/LICENSE-CDLA-Sharing-1.0.txt` |
| **Volume** | 26.872 registros × 5 colunas (19,2 MB) |
| **Idioma** | Inglês |

### Sobre a licença

A CDLA-Sharing-1.0 permite usar, modificar e redistribuir os dados, desde que:

1. a gente credite a Bitext Innovations como fonte;
2. qualquer versão modificada seja compartilhada sob a mesma licença.

Isso está coberto neste repositório: a atribuição está aqui e no cabeçalho do notebook, e a licença completa acompanha o arquivo de dados. O `edubot_dataset_tratado.csv` herda a mesma licença por ser derivado do original.

---

## 2. Estrutura das colunas

| Coluna | Tipo | Descrição |
|---|---|---|
| `flags` | texto | Letras que marcam propriedades do texto (coloquial, typo, ofensa, negação, abreviação...). 394 combinações distintas. |
| `instruction` | texto | **Coluna de texto exigida pelo TP.** A mensagem do usuário. De 1 a 16 palavras. |
| `category` | categórico | **Coluna de categoria exigida pelo TP.** Rótulo de alto nível. 11 valores. |
| `intent` | categórico | Intenção específica. 27 valores, ~1.000 amostras cada no bruto. |
| `response` | texto | Resposta modelo do assistente. Não usei no TP1. |

O enunciado pede pelo menos 500 amostras com colunas de texto e categoria — aqui são 26.872, com folga.

---

## 3. Alternativas que descartei

| Alternativa | Por que não |
|---|---|
| **Gerar dataset sintético com LLM** | O professor pediu explicitamente em aula (12/08) pra não fazer isso: dados sintéticos vêm equilibrados demais, sem ruído e sem casos incompletos — ou seja, sem a parte de engenharia de dados. |
| **Chatbots universitários do Kaggle** (`intents.json`) | Pouco volume (80–200 frases), abaixo do mínimo de 500, e sem tags linguísticas. |
| **Feedback/avaliação de estudantes** | Rótulo de sentimento sobre disciplina, não de intenção de atendimento. Não serve pra roteamento. |
| **Logs de chatbot universitário (Zenodo)** | Promissores, mas sem rótulo de intenção padronizado — exigiria anotação manual, inviável no prazo do TP1. Ficam como opção pro TP2. |

---

## 4. Por que escolhi a Bitext

**Volume e estrutura.** 26.872 registros, com texto livre e rótulo em duas camadas (categoria → intenção). Não precisei adaptar a estrutura.

**Dá pra mapear pro domínio acadêmico.** A própria Bitext diz que selecionou estas intenções a partir de 20 datasets verticais, incluindo Educação. Cancelar pedido, consultar cobrança, recuperar senha, reclamar — são os mesmos tipos de pedido que aparecem numa secretaria acadêmica, só muda a palavra usada. O remapeamento detalhado está na seção 4 do notebook (23 intenções mapeadas, 4 descartadas).

**Tags de ruído linguístico.** A coluna `flags` marca typo, coloquialismo, abreviação e ofensa. Isso permitiu medir que quase metade das mensagens legítimas já chega com grafia irregular (H3 do notebook) — dado relevante pro desenho das defesas de segurança.

**Licença permissiva.** CDLA-Sharing-1.0, com o texto completo no repositório.

---

## 5. Ressalvas (pra não esquecer depois)

Detalhes na seção 8.2 do notebook.

1. **Dataset sintético** — intenções quase uniformes (~1.000 cada), o que não reflete a sazonalidade real de uma secretaria (rematrícula concentra tudo em matrícula e nota).
2. **Inglês** — conforme orientação em aula, treino fica em inglês; tradução pro aluno fica na camada de resposta (TP2+).
3. **Adaptação de rótulo, não de texto** — as frases continuam falando de "order" e "invoice"; termos como *dispensa de disciplina* não aparecem. No TP2 quero combinar com logs universitários em português.
4. **Sem rótulo de urgência** — tentei um proxy pela tag de hostilidade (H2) e não funcionou. Preciso de dataset de emoção ou anotação manual no TP2.

---

## 6. Plano pro TP2

Conforme a ideia de combinar datasets discutida em aula:

| Finalidade | O que buscar |
|---|---|
| Rótulo de urgência | Dataset de emoção/urgência em mensagens de suporte |
| Vocabulário acadêmico | Logs de chatbot universitário (Zenodo / Hugging Face) |
| Segurança | Dataset de prompt injection / jailbreak |

---

## 7. Atribuição

> Bitext Innovations (2024). *Bitext — Customer Service Tagged Training Dataset for LLM-based Virtual Assistants.* Disponível em Hugging Face e GitHub. Licenciado sob Community Data License Agreement — Sharing, Version 1.0 (CDLA-Sharing-1.0).

---

## 8. Uso de IA neste trabalho

Conforme a política de Sinal Verde do enunciado:

- Usei o **Claude (Anthropic)** na triagem de datasets candidatos, pra montar o notebook e revisar este documento.
- Escolha do dataset, mapeamento, limpeza e hipóteses foram decisões minhas.
- Os números citados aqui e no notebook vêm da execução do código sobre `eda/data/`; dá pra reproduzir rodando `eda_edubot_tp1.ipynb`.
