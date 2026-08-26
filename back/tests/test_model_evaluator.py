from __future__ import annotations

import json

import pytest

from scripts.evaluate_models import (
    MetricResult,
    ModelCaseResult,
    ModelEvalCase,
    aggregate_by_model,
    load_cases,
    make_test_case,
    metrics_by_threshold,
    skipped_result,
    write_reports,
)


def _result(
    model: str,
    case_id: str,
    score: float | None,
    passed: bool | None,
    *,
    scored: bool = True,
    skipped: bool = False,
) -> ModelCaseResult:
    metrics = []
    if score is not None:
        metrics.append(MetricResult("Correctness", score, 0.55, passed, "", ""))

    return ModelCaseResult(
        model=model,
        case_id=case_id,
        number=1,
        category="historia",
        question="Pergunta?",
        expected_output="Resposta esperada.",
        answer="Resposta real.",
        scored=scored,
        skipped=skipped,
        skip_reason="Sem gabarito." if skipped else "",
        passed=passed,
        score=score,
        metrics=metrics,
        retrieval_query="consulta",
        sources=["fonte.pdf (pagina 1)"],
        error="",
    )


def test_load_cases_validates_and_preserves_skipped(tmp_path):
    path = tmp_path / "cases.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "ok",
                    "number": 1,
                    "category": "historia",
                    "question": "Qual era o primeiro nome?",
                    "expected_output": "Asimov.",
                    "scored": True,
                    "skip_reason": "",
                },
                {
                    "id": "skip",
                    "number": 2,
                    "category": "historia",
                    "question": "Pergunta sem gabarito?",
                    "expected_output": "",
                    "scored": False,
                    "skip_reason": "Sem resposta-gabarito explicita no DOCX.",
                },
            ]
        ),
        encoding="utf-8",
    )

    cases = load_cases(path)

    assert len(cases) == 2
    assert cases[0].scored is True
    assert cases[1].scored is False
    assert cases[1].skip_reason == "Sem resposta-gabarito explicita no DOCX."


def test_load_cases_rejects_scored_case_without_expected_output(tmp_path):
    path = tmp_path / "cases.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "bad",
                    "number": 1,
                    "category": "historia",
                    "question": "Pergunta?",
                    "expected_output": "",
                    "scored": True,
                    "skip_reason": "",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="expected_output"):
        load_cases(path)


def test_skipped_result_does_not_count_as_evaluated():
    skipped_case = ModelEvalCase(
        id="c1",
        number=1,
        category="historia",
        question="Pergunta sem gabarito?",
        expected_output="",
        scored=False,
        skip_reason="Sem resposta-gabarito.",
    )

    result = skipped_result("gpt-4o-mini", skipped_case)

    assert result.skipped is True
    assert result.scored is False
    assert result.score is None
    assert result.passed is None


def test_aggregate_by_model_ignores_skipped_in_scores():
    results = [
        _result("model-a", "a", 0.8, True),
        _result("model-a", "b", 0.4, False),
        _result("model-a", "c", None, None, scored=False, skipped=True),
        _result("model-b", "a", 0.9, True),
    ]

    summary = aggregate_by_model(results)

    model_a = next(row for row in summary if row["model"] == "model-a")
    assert model_a["total_cases"] == 3
    assert model_a["total_evaluated"] == 2
    assert model_a["total_skipped"] == 1
    assert model_a["passed"] == 1
    assert model_a["failed"] == 1
    assert model_a["avg_score"] == pytest.approx(0.6)
    assert model_a["pass_rate"] == pytest.approx(0.5)


def test_metrics_by_threshold_uses_primary_score():
    results = [
        _result("model-a", "a", 0.8, True),
        _result("model-a", "b", 0.6, True),
        _result("model-a", "c", None, None, scored=False, skipped=True),
    ]

    rows = metrics_by_threshold(results, thresholds=[0.5, 0.7])

    low = next(row for row in rows if row["threshold"] == 0.5)
    high = next(row for row in rows if row["threshold"] == 0.7)
    assert low["passed"] == 2
    assert low["failed"] == 0
    assert high["passed"] == 1
    assert high["failed"] == 1


def test_write_reports_creates_csv_json_and_html(tmp_path):
    results = [
        _result("model-a", "a", 0.8, True),
        _result("model-a", "b", None, None, scored=False, skipped=True),
    ]
    summary = aggregate_by_model(results)
    threshold_rows = metrics_by_threshold(results, thresholds=[0.5])

    write_reports(tmp_path, results, summary, threshold_rows)

    assert (tmp_path / "respostas_por_modelo.csv").exists()
    assert (tmp_path / "resumo_modelos.csv").exists()
    assert (tmp_path / "metricas_por_threshold.csv").exists()
    assert (tmp_path / "avaliacao_modelos.html").exists()

    payload = json.loads((tmp_path / "avaliacao_modelos.json").read_text(encoding="utf-8"))
    assert payload["summary"][0]["model"] == "model-a"
    assert payload["results"][0]["score"] == 0.8


def test_load_cases_hallucination_threshold_default_and_override(tmp_path):
    path = tmp_path / "cases.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "default",
                    "number": 1,
                    "category": "historia",
                    "question": "Pergunta?",
                    "expected_output": "Resposta.",
                    "scored": True,
                    "skip_reason": "",
                },
                {
                    "id": "override",
                    "number": 2,
                    "category": "historia",
                    "question": "Outra pergunta?",
                    "expected_output": "Outra resposta.",
                    "scored": True,
                    "skip_reason": "",
                    "hallucination_threshold": 0.2,
                },
            ]
        ),
        encoding="utf-8",
    )

    cases = load_cases(path)

    assert cases[0].hallucination_threshold == pytest.approx(0.5)
    assert cases[1].hallucination_threshold == pytest.approx(0.2)


def test_make_test_case_populates_context_with_expected_output():
    case = ModelEvalCase(
        id="c1",
        number=1,
        category="historia",
        question="Qual era o primeiro nome da equipe?",
        expected_output="Asimov.",
        scored=True,
    )

    # Sem RAG: retrieval_context vazio, mas context (usado pelo HallucinationMetric)
    # ainda deve ser preenchido com o gabarito.
    test_case_no_rag = make_test_case(case, "A equipe se chamava Asimov.", [])
    assert test_case_no_rag.context == ["Asimov."]
    assert test_case_no_rag.retrieval_context == []

    # Com RAG: retrieval_context populado (usado pelo Faithfulness) e context
    # continua sendo o gabarito (usado pelo Hallucination) -- os dois campos
    # tem sentidos distintos e nao devem se confundir.
    test_case_rag = make_test_case(case, "A equipe se chamava Asimov.", ["trecho recuperado"])
    assert test_case_rag.context == ["Asimov."]
    assert test_case_rag.retrieval_context == ["trecho recuperado"]
