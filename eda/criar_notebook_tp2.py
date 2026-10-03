from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parent
NOTEBOOK_PATH = ROOT / "eda_edubot_tp2.ipynb"


def markdown(text: str):
    return nbf.v4.new_markdown_cell(text.strip())


def code(text: str):
    return nbf.v4.new_code_cell(text.strip())


cells = [
    markdown("""
# EduBot Analytics: EDA do TP2

Este notebook continua o TP1. O objetivo é testar formalmente a H1, acrescentar
visualizações multivariadas e verificar a distância entre o Bitext e uma amostra
de perguntas acadêmicas em português.

A amostra acadêmica vem de `liteofspace/unb-chatbot-dpo`. Como a fonte não declara
licença, os textos são baixados pelo script `preparar_amostra_academica.py` e ficam
somente no cache local. Os rótulos atuais são uma triagem para revisão humana e
não são usados como verdade de campo.
"""),
    code("""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import mannwhitneyu

BASE_DIR = Path.cwd()
if BASE_DIR.name != "eda":
    BASE_DIR = BASE_DIR / "eda"

FIGURES_DIR = BASE_DIR / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

bitext = pd.read_csv(BASE_DIR / "data" / "edubot_dataset_tratado.csv")
academic = pd.read_csv(BASE_DIR / "data" / "cache" / "amostra_academica_com_texto.csv")

sns.set_theme(style="whitegrid")
print(f"Bitext tratado: {bitext.shape[0]:,} linhas")
print(f"Amostra acadêmica: {academic.shape[0]:,} linhas")
"""),
    markdown("""
## 1. Comparação de domínio

O TP1 adaptou os rótulos, mas preservou frases de e-commerce em inglês. Aqui a
comparação usa termos simples e não pretende substituir uma avaliação semântica.
Ela apenas mede de forma reproduzível a diferença que o professor apontou.
"""),
    code("""
academic_terms = (
    "matrícula", "disciplina", "curso", "nota", "estágio", "semestre",
    "currículo", "formatura", "trancamento", "universidade"
)
commerce_terms = (
    "order", "invoice", "shipping", "delivery", "refund", "payment", "purchase"
)

def term_rate(series, terms):
    pattern = "|".join(terms)
    return series.str.casefold().str.contains(pattern, regex=True).mean() * 100

comparison = pd.DataFrame(
    [
        {
            "corpus": "Bitext tratado",
            "n": len(bitext),
            "media_caracteres": bitext["instruction"].str.len().mean(),
            "media_palavras": bitext["instruction"].str.split().str.len().mean(),
            "termos_academicos_pct": term_rate(bitext["instruction"], academic_terms),
            "termos_comercio_pct": term_rate(bitext["instruction"], commerce_terms),
        },
        {
            "corpus": "Amostra acadêmica",
            "n": len(academic),
            "media_caracteres": academic["texto"].str.len().mean(),
            "media_palavras": academic["texto"].str.split().str.len().mean(),
            "termos_academicos_pct": term_rate(academic["texto"], academic_terms),
            "termos_comercio_pct": term_rate(academic["texto"], commerce_terms),
        },
    ]
).round(2)
comparison
"""),
    markdown("""
## 2. Heatmap de correlação

Foi usada correlação de Spearman porque os comprimentos são discretos e as flags
são binárias. A matriz ajuda a identificar atributos redundantes. Correlação não
indica que uma tag causa outra.
"""),
    code("""
flag_columns = [
    "tem_ofensa", "tem_typo", "tem_coloquial", "tem_polidez",
    "tem_negacao", "modo_keyword", "tem_abreviacao"
]
correlation_columns = ["n_chars", "n_palavras", *flag_columns]
corr = bitext[correlation_columns].corr(method="spearman")

plt.figure(figsize=(10, 7))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="vlag", center=0, vmin=-1, vmax=1)
plt.title("Correlação de Spearman entre comprimento e flags linguísticas")
plt.xlabel("Atributos")
plt.ylabel("Atributos")
plt.tight_layout()
plt.savefig(FIGURES_DIR / "fig7_heatmap_correlacao.png", dpi=150)
plt.show()
"""),
    markdown("""
## 3. Scatter plots

O primeiro gráfico mostra a relação esperada entre caracteres e palavras. O
segundo verifica se mensagens mais longas acumulam mais marcas de ruído.
"""),
    code("""
plot_sample = bitext.sample(n=min(2500, len(bitext)), random_state=42)

plt.figure(figsize=(10, 6))
sns.scatterplot(
    data=plot_sample,
    x="n_palavras",
    y="n_chars",
    hue="categoria_edubot",
    alpha=0.45,
    s=28,
)
plt.title("Comprimento das mensagens por categoria")
plt.xlabel("Número de palavras")
plt.ylabel("Número de caracteres")
plt.legend(title="Categoria", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
plt.savefig(FIGURES_DIR / "fig8_scatter_comprimento.png", dpi=150)
plt.show()

bitext["n_ruidos"] = bitext[
    ["tem_typo", "tem_coloquial", "tem_abreviacao", "tem_ofensa"]
].sum(axis=1)
noise_sample = bitext.sample(n=min(2500, len(bitext)), random_state=42).copy()
noise_sample["n_ruidos_jitter"] = (
    noise_sample["n_ruidos"] + np.random.default_rng(42).normal(0, 0.06, len(noise_sample))
)

plt.figure(figsize=(9, 5))
sns.scatterplot(
    data=noise_sample,
    x="n_palavras",
    y="n_ruidos_jitter",
    alpha=0.35,
    s=25,
)
plt.title("Comprimento e quantidade de marcas de ruído")
plt.xlabel("Número de palavras")
plt.ylabel("Marcas de ruído por mensagem")
plt.yticks(range(5))
plt.tight_layout()
plt.savefig(FIGURES_DIR / "fig9_scatter_ruido.png", dpi=150)
plt.show()
"""),
    markdown("""
## 4. Teste formal da H1

**H1 do TP1:** pedidos que exigem justificativa ou consulta de processo tendem a
ser mais longos que pedidos diretos.

Os grupos foram definidos antes do teste. Como `n_palavras` é discreto, limitado
a 16 no Bitext e não tem distribuição normal, foi escolhido o teste
Mann-Whitney bicaudal.

- H0: os dois grupos têm a mesma distribuição de comprimento;
- H1: as distribuições são diferentes.
"""),
    code("""
direct_intents = {
    "acesso_recuperar_senha",
    "cadastro_atualizar_dados",
    "financeiro_emitir_boleto",
    "matricula_solicitar",
    "disciplina_inscrever",
}
process_intents = {
    "financeiro_politica_reembolso",
    "financeiro_acompanhar_reembolso",
    "solicitacao_consultar_status",
    "matricula_problema",
    "trancamento_consultar_regra",
}

direct = bitext.loc[bitext["intent_edubot"].isin(direct_intents), "n_palavras"]
process = bitext.loc[bitext["intent_edubot"].isin(process_intents), "n_palavras"]
statistic, p_value = mannwhitneyu(process, direct, alternative="two-sided")

def cliffs_delta(first, second):
    first = np.asarray(first)
    second = np.asarray(second)
    greater = sum((value > second).sum() for value in first)
    smaller = sum((value < second).sum() for value in first)
    return (greater - smaller) / (len(first) * len(second))

delta = cliffs_delta(process, direct)
test_result = pd.DataFrame(
    {
        "grupo": ["Processo/justificativa", "Pedido direto"],
        "n": [len(process), len(direct)],
        "media_palavras": [process.mean(), direct.mean()],
        "mediana_palavras": [process.median(), direct.median()],
    }
).round(2)

display(test_result)
print(f"U = {statistic:,.0f}")
print(f"p-valor = {p_value:.3e}")
print(f"Cliff's delta = {delta:.3f}")
"""),
    markdown("""
### Interpretação

Um p-valor abaixo de 0,05 rejeita H0 para esta amostra. O tamanho de efeito de
Cliff deve ser lido junto com a diferença de medianas: uma diferença
estatisticamente detectável em mais de 20 mil registros pode continuar pequena
na prática.

O resultado vale para o Bitext e para os grupos definidos acima. Ele não prova
que mensagens reais de estudantes seguem o mesmo padrão. A amostra acadêmica
será usada para testar essa generalização depois da revisão dos rótulos.
"""),
    markdown("""
## 5. Urgência

O `urgencia_proxy` do TP1 não será usado como alvo. Ele mede polidez ou
hostilidade, enquanto a nova rubrica considera prazo e impacto acadêmico.
Como a revisão humana da amostra ainda é necessária, este notebook apenas
apresenta a distribuição dos rótulos de triagem.
"""),
    code("""
urgency_summary = (
    academic["urgencia_rascunho"]
    .value_counts()
    .rename_axis("urgencia")
    .reset_index(name="n")
)
urgency_summary["pct"] = (urgency_summary["n"] / len(academic) * 100).round(1)
urgency_summary
"""),
    markdown("""
## 6. Conclusões

1. O corpus acadêmico corrige o vocabulário de domínio, mas ainda exige revisão
   humana e não substitui logs reais.
2. O heatmap deixa clara a redundância esperada entre caracteres e palavras.
3. O Mann-Whitney transforma a H1 em uma hipótese testável e reporta também o
   tamanho do efeito.
4. A urgência continua separada de hostilidade. O próximo modelo só deve usar
   rótulos revisados segundo prazo e impacto.
"""),
]

notebook = nbf.v4.new_notebook(
    cells=cells,
    metadata={
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3"},
    },
)
nbf.write(notebook, NOTEBOOK_PATH)
print(f"Notebook criado em {NOTEBOOK_PATH}")
