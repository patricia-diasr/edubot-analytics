import hashlib
import json
from pathlib import Path

import pandas as pd
import requests

DATASET = "liteofspace/unb-chatbot-dpo"
API_URL = "https://datasets-server.huggingface.co/rows"
BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / "data" / "cache"
MANIFEST_PATH = BASE_DIR / "data" / "amostra_academica_rotulada.csv"
SAMPLE_SIZE = 300

CATEGORY_TERMS = {
    "ACESSO": ("senha", "login", "acesso", "portal", "sigaa"),
    "FINANCEIRO": ("boleto", "pagamento", "mensalidade", "taxa", "auxílio", "bolsa"),
    "CADASTRO": ("cadastro", "dados", "nome social", "documento", "histórico"),
    "FEEDBACK": ("reclama", "revisão de nota", "recurso", "denúncia", "ouvidoria"),
    "SUPORTE": ("contato", "secretaria", "erro", "problema", "atendimento"),
}

HIGH_URGENCY_TERMS = (
    "hoje",
    "último dia",
    "prazo termina",
    "prazo encerra",
    "não consigo acessar",
    "bloqueado",
)
MEDIUM_URGENCY_TERMS = (
    "prazo",
    "matrícula",
    "trancamento",
    "formatura",
    "estágio",
    "recurso",
)


def fetch_split(split: str, total: int) -> list[dict]:
    rows = []
    for offset in range(0, total, 100):
        response = requests.get(
            API_URL,
            params={
                "dataset": DATASET,
                "config": "default",
                "split": split,
                "offset": offset,
                "length": min(100, total - offset),
            },
            timeout=60,
        )
        response.raise_for_status()
        rows.extend(item["row"] for item in response.json()["rows"])
    return rows


def user_message(messages: list[dict]) -> str:
    for message in messages:
        if message.get("role") == "user":
            return message.get("content", "").strip()
    return ""


def draft_category(text: str) -> str:
    normalized = text.casefold()
    for category, terms in CATEGORY_TERMS.items():
        if any(term in normalized for term in terms):
            return category
    return "ACADEMICO"


def draft_urgency(text: str) -> str:
    normalized = text.casefold()
    if any(term in normalized for term in HIGH_URGENCY_TERMS):
        return "alta"
    if any(term in normalized for term in MEDIUM_URGENCY_TERMS):
        return "media"
    return "indeterminada"


def main() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    records = []

    for split, total in (("train", 991), ("validation", 114)):
        for row in fetch_split(split, total):
            text = user_message(row["chosen"])
            if not text:
                continue
            records.append(
                {
                    "item_hash": row["item_hash"],
                    "split_origem": split,
                    "texto": text,
                    "categoria_rascunho": draft_category(text),
                    "urgencia_rascunho": draft_urgency(text),
                }
            )

    source = (
        pd.DataFrame(records)
        .drop_duplicates(subset=["texto"])
        .assign(
            texto_sha256=lambda frame: frame["texto"].map(
                lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest()
            )
        )
    )

    sample = (
        source.sample(n=min(SAMPLE_SIZE, len(source)), random_state=42)
        .sort_values(["categoria_rascunho", "item_hash"])
        .reset_index(drop=True)
    )
    sample.insert(0, "amostra_id", range(1, len(sample) + 1))
    sample["categoria_revisada"] = ""
    sample["urgencia_revisada"] = ""
    sample["status_revisao"] = "pendente"

    cache_path = CACHE_DIR / "amostra_academica_com_texto.csv"
    sample.to_csv(cache_path, index=False)

    manifest_columns = [
        "amostra_id",
        "item_hash",
        "split_origem",
        "texto_sha256",
        "categoria_rascunho",
        "urgencia_rascunho",
        "categoria_revisada",
        "urgencia_revisada",
        "status_revisao",
    ]
    sample[manifest_columns].to_csv(MANIFEST_PATH, index=False)

    metadata = {
        "dataset": DATASET,
        "dataset_revision": "f2b61707c7fe5a24083257c6696f50a7b9d231e3",
        "sample_size": len(sample),
        "random_state": 42,
        "license_declared": False,
        "redistributed_text": False,
    }
    (CACHE_DIR / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Amostra local: {cache_path}")
    print(f"Manifesto versionável: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
