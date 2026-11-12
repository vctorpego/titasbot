from __future__ import annotations

import os
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

os.environ.setdefault("DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE", "45")
os.environ.setdefault("DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE", "120")
os.environ.setdefault("DEEPEVAL_TASK_GATHER_BUFFER_SECONDS_OVERRIDE", "10")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

CASES_PATH = PROJECT_ROOT / "tests" / "evals" / "model_eval_cases.json"
ANNOTATIONS_PATH = PROJECT_ROOT / "tests" / "evals" / "rag_stage_eval_cases.json"
OUTPUT_DIR = PROJECT_ROOT / "avaliacao_rag_4_metricas"


def _import_deepeval() -> Any:
    try:
        from deepeval.metrics import FaithfulnessMetric, GEval
        from deepeval.test_case import LLMTestCase, SingleTurnParams
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "DeepEval nao esta instalado. Rode `pip install -r requirements.txt` "
            "e `pip install -r requirements-eval.txt` antes desta avaliacao."
        ) from exc
    return {
        "FaithfulnessMetric": FaithfulnessMetric,
        "GEval": GEval,
        "LLMTestCase": LLMTestCase,
        "SingleTurnParams": SingleTurnParams,
    }


def _build_eval_model() -> Any:
    eval_model = os.getenv("DEEPEVAL_EVAL_MODEL", "gpt-5-nano")
    provider = (os.getenv("DEEPEVAL_EVAL_PROVIDER") or "openai").strip().lower()
    if provider in {"openai", ""}:
        return eval_model

    from deepeval.models import AnthropicModel, DeepSeekModel, GeminiModel

    if provider in {"google_genai", "google", "gemini"}:
        return GeminiModel(model=eval_model, api_key=os.getenv("GOOGLE_API_KEY"))
    if provider == "anthropic":
        return AnthropicModel(model=eval_model, api_key=os.getenv("ANTHROPIC_API_KEY"))
    if provider == "deepseek":
        return DeepSeekModel(model=eval_model, api_key=os.getenv("DEEPSEEK_API_KEY"))
    raise ValueError(f"DEEPEVAL_EVAL_PROVIDER desconhecido: {provider!r}")


def measure_generation_metrics(case: Any, answer: str, retrieval_context: list[str]) -> tuple[Any, Any]:
    from app.evaluation.rag_stage_scorer import GenerationMetricScore

    deepeval = _import_deepeval()
    eval_model = _build_eval_model()
    test_case = deepeval["LLMTestCase"](
        input=case.question,
        actual_output=answer,
        expected_output=case.expected_output,
        retrieval_context=retrieval_context,
    )
    correctness = deepeval["GEval"](
        name="Answer Correctness",
        criteria=(
            "Determine se a resposta real esta correta em relacao a resposta esperada. "
            "Aceite variacoes de redacao, mas penalize fatos ausentes, anos errados, "
            "classificacoes erradas, listas incompletas ou invencao de informacoes."
        ),
        evaluation_params=[
            deepeval["SingleTurnParams"].INPUT,
            deepeval["SingleTurnParams"].ACTUAL_OUTPUT,
            deepeval["SingleTurnParams"].EXPECTED_OUTPUT,
        ],
        threshold=case.correctness_threshold,
        model=eval_model,
        async_mode=False,
    )
    faithfulness = deepeval["FaithfulnessMetric"](
        threshold=case.faithfulness_threshold,
        model=eval_model,
        truths_extraction_limit=int(os.getenv("RAG_STAGE_TRUTHS_LIMIT", "8")),
        include_reason=os.getenv("DEEPEVAL_INCLUDE_REASON", "0") == "1",
        async_mode=False,
    )
    return (
        _measure_metric(correctness, case.correctness_threshold, test_case=test_case),
        _measure_metric(faithfulness, case.faithfulness_threshold, test_case=test_case),
    )


def _measure_metric(metric: Any, threshold: float, test_case: Any | None = None) -> Any:
    from app.evaluation.rag_stage_scorer import GenerationMetricScore

    try:
        if test_case is None:
            raise RuntimeError("test_case ausente.")
        measured = metric.measure(test_case)
        score = _to_float(getattr(metric, "score", measured))
        passed = getattr(metric, "success", None)
        if passed is None and hasattr(metric, "is_successful"):
            passed = metric.is_successful()
        if passed is None and score is not None:
            passed = score >= threshold
        return GenerationMetricScore(
            name=str(getattr(metric, "name", metric.__class__.__name__)),
            score=score,
            threshold=threshold,
            passed=bool(passed) if passed is not None else None,
            reason=str(getattr(metric, "reason", "") or ""),
            error="",
        )
    except Exception as exc:
        return GenerationMetricScore(
            name=str(getattr(metric, "name", metric.__class__.__name__)),
            score=None,
            threshold=threshold,
            passed=False,
            reason="",
            error=str(exc),
        )


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def run() -> list[Any]:
    from app.application.chat_service import TitasBotService
    from app.evaluation.rag_stage_scorer import (
        GenerationMetricScore,
        RagStageResult,
        classify_diagnosis,
        load_stage_cases,
        score_retrieval,
        write_outputs,
    )
    from app.infrastructure.env import load_project_env
    from app.infrastructure.net_env import clear_broken_local_proxy
    from app.infrastructure.settings import get_settings

    clear_broken_local_proxy()
    load_project_env()

    model = os.getenv("EVAL_DEEPSEEK_MODEL", "deepseek-chat")
    settings = replace(get_settings(), chat_model=model, chat_provider="deepseek")
    bot = TitasBotService(settings)
    if not bot.has_documents():
        raise RuntimeError("Base vetorial vazia. Rode criar_db.py antes da avaliacao RAG.")

    cases = load_stage_cases(ANNOTATIONS_PATH, CASES_PATH)
    print(f"Avaliando {len(cases)} caso(s) com {model}.")

    results: list[RagStageResult] = []
    try:
        for case in cases:
            print(f"[{case.number:02d}] {case.id}", flush=True)
            try:
                chat_result = bot.ask(question=case.question)
                top_chunks = chat_result.chunks[:5]
                retrieval = score_retrieval(case, top_chunks)
                retrieval_context = [chunk.content[: int(os.getenv("RAG_STAGE_CONTEXT_CHARS", "1200"))] for chunk in top_chunks]
                correctness, faithfulness = measure_generation_metrics(
                    case,
                    chat_result.answer,
                    retrieval_context,
                )
                diagnosis = classify_diagnosis(retrieval, correctness, faithfulness)
                result = RagStageResult(
                    case_id=case.id,
                    number=case.number,
                    category=case.category,
                    question=case.question,
                    expected_output=case.expected_output,
                    answer=chat_result.answer,
                    retrieval_query=chat_result.retrieval_query,
                    retrieval=retrieval,
                    correctness=correctness,
                    faithfulness=faithfulness,
                    diagnosis=diagnosis,
                    error="",
                )
            except Exception as exc:
                empty_metric = GenerationMetricScore("Answer Correctness", None, case.correctness_threshold, False, "", str(exc))
                empty_faithfulness = GenerationMetricScore("Faithfulness", None, case.faithfulness_threshold, False, "", str(exc))
                retrieval = score_retrieval(case, [])
                result = RagStageResult(
                    case_id=case.id,
                    number=case.number,
                    category=case.category,
                    question=case.question,
                    expected_output=case.expected_output,
                    answer="",
                    retrieval_query="",
                    retrieval=retrieval,
                    correctness=empty_metric,
                    faithfulness=empty_faithfulness,
                    diagnosis="both_error",
                    error=str(exc),
                )
            results.append(result)
            print(
                "  -> "
                f"Hit@5={result.retrieval.hit_at_5:.0f} "
                f"Precision@5={result.retrieval.precision_at_5:.2f} "
                f"Correctness={_fmt_score(result.correctness.score)} "
                f"Faithfulness={_fmt_score(result.faithfulness.score)} "
                f"{result.diagnosis}",
                flush=True,
            )
    finally:
        if results:
            write_outputs(OUTPUT_DIR, results)
            print(f"Relatorios salvos em: {OUTPUT_DIR}", flush=True)
    return results


def _fmt_score(score: float | None) -> str:
    return "" if score is None else f"{score:.2f}"


def main() -> None:
    run()


if __name__ == "__main__":
    main()
