from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.application.chat_service import TitasBotService
from app.infrastructure.env import load_project_env
from app.infrastructure.net_env import clear_broken_local_proxy
from app.infrastructure.settings import get_settings
from app.infrastructure.text_utils import normalize_text


@dataclass
class CaseResult:
    idx: int
    question: str
    passed: bool
    score: float
    details: list[str]
    answer: str


def _load_cases(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Arquivo de casos deve conter uma lista JSON.")
    return data


def _check_case(answer: str, case: dict[str, Any]) -> tuple[bool, float, list[str]]:
    details: list[str] = []
    body = answer.split("Fontes usadas:")[0].strip()
    ans = normalize_text(body)
    max_points = 0.0
    points = 0.0

    contains_all = [normalize_text(x) for x in case.get("contains_all", [])]
    contains_any = [normalize_text(x) for x in case.get("contains_any", [])]
    not_contains = [normalize_text(x) for x in case.get("not_contains", [])]

    for token in contains_all:
        max_points += 1.0
        if token in ans:
            points += 1.0
            details.append(f"OK contains_all: {token}")
        else:
            details.append(f"FALHOU contains_all: {token}")

    if contains_any:
        max_points += 1.0
        if any(repr(token) and re.search(rf"\b{re.escape(token)}\b", ans) for token in contains_any):
            points += 1.0
            details.append("OK contains_any")
        else:
            details.append("FALHOU contains_any")

    for token in not_contains:
        max_points += 1.0
        if token not in ans:
            points += 1.0
            details.append(f"OK not_contains: {token}")
        else:
            details.append(f"FALHOU not_contains: {token}")

    if max_points == 0:
        return True, 1.0, ["Sem regras para avaliar."]

    score = points / max_points
    min_score = float(case.get("min_score", 1.0))
    passed = score >= min_score
    return passed, score, details


def main() -> None:
    clear_broken_local_proxy()
    load_project_env()
    settings = get_settings()
    bot = TitasBotService(settings)

    cases_path = Path("avaliacao_casos.json")
    if not cases_path.exists():
        raise FileNotFoundError("Arquivo 'avaliacao_casos.json' nao encontrado.")

    cases = _load_cases(cases_path)
    if not bot.has_documents():
        raise RuntimeError("Base vetorial vazia. Rode criar_db.py antes.")

    previous_question: str | None = None
    previous_answer: str | None = None

    results: list[CaseResult] = []
    for idx, case in enumerate(cases, start=1):
        question = str(case["question"]).strip()
        if not question:
            continue

        keep_context = bool(case.get("keep_context", True))
        result = bot.ask(
            question=question,
            previous_question=previous_question if keep_context else None,
            previous_answer=previous_answer if keep_context else None,
        )

        passed, score, details = _check_case(result.answer, case)
        results.append(
            CaseResult(
                idx=idx,
                question=question,
                passed=passed,
                score=score,
                details=details,
                answer=result.answer,
            )
        )

        previous_question = question
        previous_answer = result.answer

    total = len(results)
    approved = sum(1 for r in results if r.passed)
    avg_score = (sum(r.score for r in results) / total) if total else 0.0

    print(f"Casos: {total}")
    print(f"Aprovados: {approved}/{total}")
    print(f"Score medio: {avg_score:.2%}")
    print()

    for r in results:
        status = "OK" if r.passed else "ERRO"
        print(f"[{status}] #{r.idx} - {r.question}")
        print(f"Score: {r.score:.2%}")
        for d in r.details:
            print(f"  - {d}")
        print(f"Resposta: {r.answer[:280].replace(chr(10), ' ')}")
        print()

    report = {
        "total": total,
        "approved": approved,
        "avg_score": avg_score,
        "results": [
            {
                "idx": r.idx,
                "question": r.question,
                "passed": r.passed,
                "score": r.score,
                "details": r.details,
                "answer": r.answer,
            }
            for r in results
        ],
    }
    Path("avaliacao_relatorio.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Relatorio salvo em: avaliacao_relatorio.json")


if __name__ == "__main__":
    main()
