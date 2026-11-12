from __future__ import annotations

"""Configuracao e I/O compartilhados pelo estudo comparativo de metricas.

Etapas (cada uma com cache em arquivo, para nao repetir chamadas pagas):
  1. scripts/generate_answers.py -> avaliacao_metricas/respostas.jsonl
  2. scripts/score_answers.py    -> avaliacao_metricas/scores.jsonl
  3. scripts/analyze_metrics.py  -> avaliacao_metricas/*.csv, *.json, *.html
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

from app.evaluation.ground_truth import MetricEvalCase, load_metric_cases

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVALS_DIR = PROJECT_ROOT / "tests" / "evals"
OFFICIAL_CASES_PATH = EVALS_DIR / "model_eval_cases.json"
ANNOTATIONS_PATH = EVALS_DIR / "metric_eval_annotations.json"
RAG_STAGE_ANNOTATIONS_PATH = EVALS_DIR / "rag_stage_eval_cases.json"

OUTPUT_DIR = Path(os.getenv("METRIC_STUDY_OUTPUT_DIR") or PROJECT_ROOT / "avaliacao_metricas")
ANSWERS_PATH = OUTPUT_DIR / "respostas.jsonl"
SCORES_PATH = OUTPUT_DIR / "scores.jsonl"
OVERRIDES_PATH = OUTPUT_DIR / "rotulos_revisados.csv"


@dataclass(frozen=True)
class ModelSpec:
    label: str
    model: str
    provider: str


def model_specs() -> list[ModelSpec]:
    """Modelos medianos e equivalentes de cada empresa (sobrescreva por env)."""
    specs = [
        ModelSpec("openai", os.getenv("EVAL_OPENAI_MODEL", "gpt-5-mini"), "openai"),
        ModelSpec("anthropic", os.getenv("EVAL_ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"), "anthropic"),
        ModelSpec("deepseek", os.getenv("EVAL_DEEPSEEK_MODEL", "deepseek-chat"), "deepseek"),
    ]
    wanted = {p.strip() for p in os.getenv("EVAL_MODELS", "").split(",") if p.strip()}
    return [s for s in specs if not wanted or s.label in wanted]


def conditions() -> list[str]:
    return [c.strip() for c in os.getenv("EVAL_CONDITIONS", "rag,no_rag").split(",") if c.strip()]


def answer_key(model_label: str, condition: str, case_id: str) -> str:
    return f"{model_label}|{condition}|{case_id}"


def load_cases() -> list[MetricEvalCase]:
    return load_metric_cases(ANNOTATIONS_PATH, OFFICIAL_CASES_PATH)


def filter_cases(cases: Sequence[MetricEvalCase]) -> list[MetricEvalCase]:
    """EVAL_CASE_IDS (prefixos, ex.: "q02,q10") tem prioridade sobre EVAL_CASE_LIMIT."""
    ids_raw = os.getenv("EVAL_CASE_IDS")
    limit_raw = os.getenv("EVAL_CASE_LIMIT")
    if ids_raw:
        wanted = [p.strip() for p in ids_raw.split(",") if p.strip()]
        selected = [c for c in cases if any(c.id.startswith(p) for p in wanted)]
        missing = [p for p in wanted if not any(c.id.startswith(p) for c in selected)]
        if missing:
            raise ValueError(f"EVAL_CASE_IDS: nenhum caso casa com {missing}")
        return selected
    if limit_raw:
        return list(cases)[: int(limit_raw)]
    return list(cases)


def read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if not path.exists():
        return
    with path.open(encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if line:
                yield json.loads(line)


def append_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        for record in records:
            fp.write(json.dumps(record, ensure_ascii=False) + "\n")
            fp.flush()


def latest_answers(path: Path = ANSWERS_PATH) -> dict[str, dict[str, Any]]:
    """Ultima geracao de cada answer_key (o arquivo e append-only)."""
    latest: dict[str, dict[str, Any]] = {}
    for record in read_jsonl(path):
        latest[record["answer_key"]] = record
    return latest
