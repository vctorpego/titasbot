from __future__ import annotations

"""Metricas "novas" do DeepEval, que usam um LLM internamente para calcular o score.

- geval_correctness:  DeepEval GEval (criterio de correcao vs gabarito).
- answer_relevancy:   DeepEval AnswerRelevancyMetric (a resposta responde a pergunta?).
- faithfulness:       DeepEval FaithfulnessMetric (fiel aos trechos recuperados; so RAG).
- hallucination_inv:  1 - DeepEval HallucinationMetric (context = gabarito), invertida
                      para "maior = melhor" como as demais.

O LLM de apoio e o GPT configurado em DEEPEVAL_EVAL_PROVIDER / DEEPEVAL_EVAL_MODEL
(padrao openai / gpt-5-nano), o mesmo ja usado nas fases anteriores do projeto. Ele
nao e usado como juiz explicito: so executa os passos internos das metricas do
DeepEval. Limitacao a discutir: e da mesma familia de um dos modelos avaliados
(gpt-5-mini), o que pode favorece-lo.

Diferente de scripts/evaluate_models.py (mantido como historico), aqui cada
metrica e medida isoladamente e sem threshold: o threshold e escolhido depois,
na meta-avaliacao (app/evaluation/meta_evaluation.py).
"""

import os
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from app.evaluation.traditional_metrics import MetricInfo

os.environ.setdefault("DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE", "60")
os.environ.setdefault("DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE", "180")

LLM_METRICS: dict[str, MetricInfo] = {
    info.name: info
    for info in [
        MetricInfo("geval_correctness", "llm", "deepeval", "DeepEval GEval Correctness"),
        MetricInfo("answer_relevancy", "llm", "deepeval", "DeepEval Answer Relevancy"),
        MetricInfo("faithfulness", "llm", "deepeval", "DeepEval Faithfulness (so RAG)"),
        MetricInfo("hallucination_inv", "llm", "deepeval", "1 - DeepEval Hallucination (contexto = gabarito)"),
    ]
}

CORRECTNESS_CRITERIA = (
    "Determine se a resposta real esta correta em relacao a resposta esperada. "
    "Aceite variacoes de redacao, mas penalize fatos ausentes, anos errados, "
    "classificacoes erradas ou invencao de informacoes. Nao penalize detalhes "
    "adicionais quando forem compativeis com a resposta esperada e nao mudarem "
    "o sentido principal."
)


@dataclass(frozen=True)
class LLMMetricScore:
    name: str
    score: float | None
    seconds: float
    cost: float | None = None
    reason: str = ""
    error: str = ""


def eval_llm_config() -> tuple[str, str]:
    """LLM de apoio do DeepEval (GPT por padrao)."""
    provider = (os.getenv("DEEPEVAL_EVAL_PROVIDER") or "openai").strip().lower()
    model = os.getenv("DEEPEVAL_EVAL_MODEL") or "gpt-5-nano"
    return provider, model


@lru_cache(maxsize=4)
def build_deepeval_model(provider: str, model: str) -> Any:
    if provider in {"openai", ""}:
        return model  # string crua: caminho nativo OpenAI do DeepEval
    from deepeval.models import AnthropicModel, DeepSeekModel, GeminiModel

    if provider in {"google_genai", "google", "gemini"}:
        return GeminiModel(model=model, api_key=os.getenv("GOOGLE_API_KEY"), temperature=0)
    if provider == "anthropic":
        return AnthropicModel(model=model, api_key=os.getenv("ANTHROPIC_API_KEY"))
    if provider == "deepseek":
        return DeepSeekModel(model=model, api_key=os.getenv("DEEPSEEK_API_KEY"))
    raise ValueError(f"DEEPEVAL_EVAL_PROVIDER desconhecido: {provider!r}")


def _throttle() -> None:
    interval = float(os.getenv("EVAL_LLM_MIN_INTERVAL_S", "0") or 0)
    if interval > 0:
        time.sleep(interval)


def applicable_llm_metrics(condition: str) -> list[str]:
    names = ["geval_correctness", "answer_relevancy", "hallucination_inv"]
    if condition == "rag":
        names.insert(2, "faithfulness")
    return names


def _build_deepeval_metric(name: str, llm: Any) -> Any:
    from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, GEval, HallucinationMetric
    from deepeval.test_case import SingleTurnParams

    if name == "geval_correctness":
        return GEval(
            name="Correctness",
            criteria=CORRECTNESS_CRITERIA,
            evaluation_params=[
                SingleTurnParams.INPUT,
                SingleTurnParams.ACTUAL_OUTPUT,
                SingleTurnParams.EXPECTED_OUTPUT,
            ],
            model=llm,
            async_mode=False,
        )
    if name == "answer_relevancy":
        return AnswerRelevancyMetric(model=llm, include_reason=True, async_mode=False)
    if name == "faithfulness":
        return FaithfulnessMetric(
            model=llm,
            truths_extraction_limit=int(os.getenv("MODEL_EVAL_TRUTHS_LIMIT", "8")),
            include_reason=True,
            async_mode=False,
        )
    if name == "hallucination_inv":
        return HallucinationMetric(model=llm, include_reason=True, async_mode=False)
    raise ValueError(name)


def _is_rate_limit(error: str) -> bool:
    return any(token in error for token in ("429", "RESOURCE_EXHAUSTED", "rate limit", "Rate limit"))


def measure_llm_metric(
    name: str,
    question: str,
    expected: str,
    answer: str,
    retrieval_context: list[str],
) -> LLMMetricScore:
    """Mede uma metrica; erros de limite de requisicoes (429) sao repetidos com espera."""
    retries = int(os.getenv("EVAL_LLM_RETRIES", "3"))
    wait_s = float(os.getenv("EVAL_LLM_RETRY_WAIT_S", "30"))
    result = _measure_once(name, question, expected, answer, retrieval_context)
    for attempt in range(1, retries + 1):
        if not result.error or not _is_rate_limit(result.error):
            break
        time.sleep(wait_s * attempt)
        result = _measure_once(name, question, expected, answer, retrieval_context)
    return result


def _measure_once(
    name: str,
    question: str,
    expected: str,
    answer: str,
    retrieval_context: list[str],
) -> LLMMetricScore:
    provider, model = eval_llm_config()
    start = time.perf_counter()
    try:
        _throttle()
        from deepeval.test_case import LLMTestCase

        metric = _build_deepeval_metric(name, build_deepeval_model(provider, model))
        test_case = LLMTestCase(
            input=question,
            actual_output=answer or "(resposta vazia)",
            expected_output=expected,
            retrieval_context=retrieval_context or None,
            context=[expected],
        )
        metric.measure(test_case)
        raw = getattr(metric, "score", None)
        score = None if raw is None else float(raw)
        if name == "hallucination_inv" and score is not None:
            score = 1.0 - score
        cost = getattr(metric, "evaluation_cost", None)
        return LLMMetricScore(
            name,
            None if score is None else round(max(0.0, min(1.0, score)), 6),
            round(time.perf_counter() - start, 3),
            cost=None if cost is None else float(cost),
            reason=str(getattr(metric, "reason", "") or "")[:600],
        )
    except Exception as exc:
        return LLMMetricScore(name, None, round(time.perf_counter() - start, 3), error=str(exc)[:600])
