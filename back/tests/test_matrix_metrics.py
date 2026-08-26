from __future__ import annotations

import pytest

from scripts.evaluate_models import ModelCaseResult, aggregate_by_model


def _res(
    model: str,
    condition: str,
    *,
    ref_final: float | None,
    score: float | None = 0.7,
    passed: bool | None = True,
    scored: bool = True,
    skipped: bool = False,
) -> ModelCaseResult:
    return ModelCaseResult(
        model=model,
        case_id="c",
        number=1,
        category="historia",
        question="q?",
        expected_output="e",
        answer="a",
        scored=scored,
        skipped=skipped,
        skip_reason="",
        passed=passed,
        score=score,
        metrics=[],
        retrieval_query="",
        sources=[],
        error="",
        condition=condition,
        provider="p",
        ref_semantic=ref_final,
        ref_lexical=ref_final,
        ref_final=ref_final,
    )


def test_aggregate_splits_by_condition():
    results = [
        _res("m", "rag", ref_final=0.9),
        _res("m", "no_rag", ref_final=0.2),
    ]
    summary = aggregate_by_model(results)
    assert {row["condition"] for row in summary} == {"rag", "no_rag"}
    assert all(row["model"] == "m" for row in summary)


def test_aggregate_computes_avg_ref_score():
    results = [
        _res("m", "rag", ref_final=0.9),
        _res("m", "rag", ref_final=0.7),
        _res("m", "rag", ref_final=None, score=None, passed=None, scored=False, skipped=True),
    ]
    summary = aggregate_by_model(results)
    row = next(r for r in summary if r["condition"] == "rag")
    assert row["avg_ref_score"] == pytest.approx(0.8)
    assert row["total_evaluated"] == 2
