from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE", "45")
os.environ.setdefault("DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE", "120")
os.environ.setdefault("DEEPEVAL_TASK_GATHER_BUFFER_SECONDS_OVERRIDE", "10")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from deepeval import assert_test
from deepeval.metrics import (
    AnswerRelevancyMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    FaithfulnessMetric,
    GEval,
)
from deepeval.test_case import LLMTestCase, SingleTurnParams

from app.application.chat_service import TitasBotService
from app.domain.constants import INSUFFICIENT_MSG
from app.infrastructure.env import load_project_env
from app.infrastructure.net_env import clear_broken_local_proxy
from app.infrastructure.settings import get_settings
from app.infrastructure.text_utils import normalize_text


CASES_PATH = Path(__file__).with_name("rag_eval_cases.json")
BASELINE_CASE_IDS = {
    "origem_primeiro_nome",
    "origem_ano_criacao",
    "origem_idealizador",
    "resultado_2023",
    "resultado_2025",
    "projeto_escudos_faciais",
    "projeto_osorin",
    "alunos_futebol_2d_2021",
    "alunos_sek_2021",
    "alunos_cospace_2021",
    "fora_escopo_2026",
    "fora_escopo_telefone",
    "fora_escopo_valor_patrocinio",
}

FULL_METRIC_CASE_IDS = {
    "origem_primeiro_nome",
    "origem_ano_criacao",
    "resultado_2023",
    "resultado_2025",
    "projeto_escudos_faciais",
    "alunos_sek_2021",
}
FAST_METRIC_CASE_IDS = FULL_METRIC_CASE_IDS


def _load_cases() -> list[dict[str, Any]]:
    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("rag_eval_cases.json deve conter uma lista de casos.")

    case_ids = os.getenv("DEEPEVAL_CASE_IDS")
    if case_ids:
        wanted = {case_id.strip() for case_id in case_ids.split(",") if case_id.strip()}
        selected = [case for case in data if case["id"] in wanted]
    else:
        case_set = os.getenv("DEEPEVAL_CASE_SET", "baseline").lower()
        if case_set in {"all", "full"}:
            selected = data
        elif case_set in {"expanded", "diagnostic"}:
            selected = [case for case in data if case["id"] not in BASELINE_CASE_IDS]
        else:
            selected = [case for case in data if case["id"] in BASELINE_CASE_IDS]

    if not selected:
        raise ValueError("Nenhum caso selecionado para os evals DeepEval.")
    return selected


@pytest.fixture(scope="module")
def bot() -> TitasBotService:
    clear_broken_local_proxy()
    load_project_env()

    if not os.getenv("OPENAI_API_KEY"):
        pytest.fail("OPENAI_API_KEY ausente. Configure .env antes de rodar os evals DeepEval.")

    service = TitasBotService(get_settings())
    if not service.has_documents():
        pytest.fail("Base vetorial vazia. Rode criar_db.py antes dos evals DeepEval.")
    return service


def _assert_text_rules(answer: str, case: dict[str, Any]) -> None:
    answer_norm = normalize_text(answer)
    insufficient_norm = normalize_text(INSUFFICIENT_MSG)

    if case.get("expect_insufficient"):
        assert insufficient_norm in answer_norm
    else:
        assert insufficient_norm not in answer_norm

    for token in case.get("must_contain", []):
        assert normalize_text(str(token)) in answer_norm

    for token in case.get("must_not_contain", []):
        assert normalize_text(str(token)) not in answer_norm


def _metrics_for_case(case: dict[str, Any], has_retrieval_context: bool) -> list[Any]:
    eval_model = os.getenv("DEEPEVAL_EVAL_MODEL", "gpt-4o-mini")
    metric_set = os.getenv("DEEPEVAL_METRIC_SET", "fast").lower()
    include_reason = os.getenv("DEEPEVAL_INCLUDE_REASON", "0") == "1"
    correctness_threshold = float(case.get("correctness_threshold", 0.55))

    if case.get("expect_insufficient"):
        return []
    if metric_set == "fast" and case["id"] not in FAST_METRIC_CASE_IDS:
        return []

    metrics: list[Any] = [
        GEval(
            name="Correctness",
            criteria=(
                "Determine se a resposta real esta correta em relacao a resposta esperada. "
                "Aceite variacoes de redacao, mas penalize fatos ausentes, anos errados, "
                "classificacoes erradas ou invencao de informacoes. Nao penalize detalhes "
                "adicionais quando forem compativeis com a resposta esperada e nao mudarem "
                "o sentido principal."
            ),
            evaluation_params=[
                SingleTurnParams.INPUT,
                SingleTurnParams.ACTUAL_OUTPUT,
                SingleTurnParams.EXPECTED_OUTPUT,
            ],
            threshold=correctness_threshold,
            model=eval_model,
            async_mode=False,
        ),
    ]

    if metric_set in {"standard", "full"}:
        metrics.append(
            AnswerRelevancyMetric(
                threshold=float(case.get("answer_relevancy_threshold", 0.6)),
                model=eval_model,
                include_reason=include_reason,
                async_mode=False,
            )
        )

    if metric_set == "full" and has_retrieval_context and case["id"] in FULL_METRIC_CASE_IDS:
        metrics.append(
            FaithfulnessMetric(
                threshold=float(case.get("faithfulness_threshold", 0.7)),
                model=eval_model,
                truths_extraction_limit=int(case.get("truths_extraction_limit", 8)),
                include_reason=include_reason,
                async_mode=False,
            )
        )

    if (
        metric_set == "full"
        and case.get("critical_retrieval")
        and has_retrieval_context
        and case["id"] in FULL_METRIC_CASE_IDS
    ):
        metrics.extend(
            [
                ContextualPrecisionMetric(
                    threshold=float(case.get("contextual_precision_threshold", 0.55)),
                    model=eval_model,
                    include_reason=include_reason,
                    async_mode=False,
                ),
                ContextualRecallMetric(
                    threshold=float(case.get("contextual_recall_threshold", 0.55)),
                    model=eval_model,
                    include_reason=include_reason,
                    async_mode=False,
                ),
            ]
        )

    return metrics


@pytest.mark.parametrize("case", _load_cases(), ids=lambda case: case["id"])
def test_rag_quality_case(bot: TitasBotService, case: dict[str, Any]) -> None:
    result = bot.ask(question=str(case["input"]))
    max_context_chars = int(os.getenv("DEEPEVAL_CONTEXT_CHARS", "1200"))
    retrieval_context = [chunk.content[:max_context_chars] for chunk in result.chunks[:6]]

    _assert_text_rules(result.answer, case)
    metrics = _metrics_for_case(case, has_retrieval_context=bool(retrieval_context))
    if not metrics:
        return

    test_case = LLMTestCase(
        input=str(case["input"]),
        actual_output=result.answer,
        expected_output=str(case["expected_output"]),
        retrieval_context=retrieval_context,
    )
    assert_test(test_case, metrics, run_async=False)
