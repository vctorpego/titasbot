from __future__ import annotations

import json

import pytest

from app.evaluation.rag_stage_scorer import (
    GenerationMetricScore,
    RagStageEvalCase,
    RagStageResult,
    classify_diagnosis,
    load_stage_cases,
    score_retrieval,
    write_outputs,
)
from app.infrastructure.retrieval import RetrievedChunk


def test_score_retrieval_calculates_hit_and_precision_at_5():
    case = _case(
        evidence_terms=["Asimov", "2015", "LARC"],
        min_terms_for_relevant_chunk=1,
        min_terms_for_sufficient_chunk=2,
    )
    chunks = [
        _chunk("A equipe Asimov participou da LARC em 2015."),
        _chunk("Texto sobre outra equipe."),
        _chunk("Asimov aparece em outro trecho."),
    ]

    result = score_retrieval(case, chunks)

    assert result.hit_at_5 == pytest.approx(1.0)
    assert result.precision_at_5 == pytest.approx(0.4)
    assert result.relevant_chunks == 2
    assert result.sufficient_chunks == 1
    assert result.chunks[0].matched_terms == ["Asimov", "2015", "LARC"]


def test_score_retrieval_uses_fixed_denominator_even_with_fewer_chunks():
    case = _case(evidence_terms=["Renato Lopes"], min_terms_for_relevant_chunk=1)

    result = score_retrieval(case, [_chunk("Renato Lopes de Oliveira idealizou a equipe.")])

    assert result.hit_at_5 == pytest.approx(1.0)
    assert result.precision_at_5 == pytest.approx(0.2)


def test_classify_diagnosis_separates_retrieval_and_generation_failures():
    ok_retrieval = score_retrieval(_case(evidence_terms=["Asimov"]), [_chunk("Asimov")])
    bad_retrieval = score_retrieval(_case(evidence_terms=["Asimov"]), [_chunk("Outro texto")])
    ok_metric = GenerationMetricScore("m", 0.9, 0.55, True)
    bad_metric = GenerationMetricScore("m", 0.2, 0.55, False)

    assert classify_diagnosis(ok_retrieval, ok_metric, ok_metric) == "ok"
    assert classify_diagnosis(bad_retrieval, ok_metric, ok_metric) == "retrieval_error"
    assert classify_diagnosis(ok_retrieval, bad_metric, ok_metric) == "generation_error"
    assert classify_diagnosis(bad_retrieval, bad_metric, ok_metric) == "both_error"


def test_load_stage_cases_joins_annotations_with_official_cases(tmp_path):
    official_path = tmp_path / "model_eval_cases.json"
    annotations_path = tmp_path / "rag_stage_eval_cases.json"
    official_path.write_text(
        json.dumps(
            [
                {
                    "id": "q1",
                    "number": 1,
                    "category": "historia",
                    "question": "Qual era o primeiro nome?",
                    "expected_output": "Asimov.",
                    "scored": True,
                    "skip_reason": "",
                }
            ]
        ),
        encoding="utf-8",
    )
    annotations_path.write_text(
        json.dumps(
            [
                {
                    "id": "q1",
                    "evidence_terms": ["Asimov"],
                    "min_terms_for_relevant_chunk": 1,
                    "min_terms_for_sufficient_chunk": 1,
                }
            ]
        ),
        encoding="utf-8",
    )

    cases = load_stage_cases(annotations_path, official_path)

    assert len(cases) == 1
    assert cases[0].id == "q1"
    assert cases[0].question == "Qual era o primeiro nome?"
    assert cases[0].evidence_terms == ["Asimov"]


def test_write_outputs_creates_json_csv_and_html(tmp_path):
    case = _case(evidence_terms=["Asimov"])
    retrieval = score_retrieval(case, [_chunk("O primeiro nome foi Asimov.")])
    result = RagStageResult(
        case_id=case.id,
        number=case.number,
        category=case.category,
        question=case.question,
        expected_output=case.expected_output,
        answer="O primeiro nome foi Asimov.",
        retrieval_query="primeiro nome Asimov",
        retrieval=retrieval,
        correctness=GenerationMetricScore("Answer Correctness", 0.9, 0.55, True),
        faithfulness=GenerationMetricScore("Faithfulness", 0.8, 0.7, True),
        diagnosis="ok",
    )

    write_outputs(tmp_path, [result])

    assert (tmp_path / "rag_4_metricas.json").exists()
    assert (tmp_path / "rag_4_metricas.csv").exists()
    assert (tmp_path / "rag_4_metricas.html").exists()
    payload = json.loads((tmp_path / "rag_4_metricas.json").read_text(encoding="utf-8"))
    html = (tmp_path / "rag_4_metricas.html").read_text(encoding="utf-8")
    assert payload["summary"]["total_cases"] == 1
    assert "Avaliacao RAG - 4 metricas" in html
    assert "Como o teste e calculado" in html
    assert "Hit@5 = 1 se existe chunk suficiente no top 5" in html
    assert "Resposta do gabarito" in html
    assert "Resposta." in html


def _case(
    *,
    evidence_terms: list[str],
    min_terms_for_relevant_chunk: int = 1,
    min_terms_for_sufficient_chunk: int = 1,
) -> RagStageEvalCase:
    return RagStageEvalCase(
        id="q1",
        number=1,
        category="historia",
        question="Pergunta?",
        expected_output="Resposta.",
        evidence_terms=evidence_terms,
        min_terms_for_relevant_chunk=min_terms_for_relevant_chunk,
        min_terms_for_sufficient_chunk=min_terms_for_sufficient_chunk,
    )


def _chunk(content: str) -> RetrievedChunk:
    return RetrievedChunk(
        content=content,
        source="fonte.pdf",
        page=0,
        doc_kind="context",
        vector_score=0.8,
        lexical_score=0.7,
        final_score=0.75,
    )
