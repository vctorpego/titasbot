from __future__ import annotations

import csv
import html
import json
import os
import sys
from dataclasses import asdict, dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import Any

os.environ.setdefault("DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE", "45")
os.environ.setdefault("DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE", "120")
os.environ.setdefault("DEEPEVAL_TASK_GATHER_BUFFER_SECONDS_OVERRIDE", "10")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@dataclass(frozen=True)
class ModelSpec:
    """Um modelo a comparar, com seu provedor explicito."""

    label: str
    model: str
    provider: str


def _build_model_specs() -> list[ModelSpec]:
    """Le EVAL_OPENAI_MODEL/EVAL_GOOGLE_MODEL do ambiente atual.

    Chamada de novo dentro de run_matrix() (apos load_project_env()), assim
    configuracao feita so em back/.env tambem funciona -- nao apenas variaveis
    ja exportadas no shell antes de iniciar o processo.
    """
    return [
        ModelSpec("openai", os.getenv("EVAL_OPENAI_MODEL", "gpt-5"), "openai"),
        ModelSpec("anthropic", os.getenv("EVAL_ANTHROPIC_MODEL", "claude-sonnet-5"), "anthropic"),
        ModelSpec("deepseek", os.getenv("EVAL_DEEPSEEK_MODEL", "deepseek-v4-pro"), "deepseek"),
    ]


def _build_conditions() -> list[str]:
    """Le EVAL_CONDITIONS do ambiente atual (ver docstring de _build_model_specs)."""
    return [c.strip() for c in os.getenv("EVAL_CONDITIONS", "rag,no_rag").split(",") if c.strip()]


# Os provedores comparados (hoje: OpenAI + Anthropic + DeepSeek) e as condicoes
# do experimento (com/sem RAG). ATENCAO: confirme os IDs atuais antes da rodada
# avaliada. Google/Gemini foi removido da comparacao por decisao do usuario
# (llm_factory.py ainda suporta google_genai de forma generica, mas nenhum
# ModelSpec o usa aqui). DeepSeek e Anthropic exigem saldo/pagamento cadastrado
# nas respectivas plataformas (DEEPSEEK_API_KEY / ANTHROPIC_API_KEY no .env).
# Valores calculados na importacao do modulo (uteis para introspeccao/testes);
# run_matrix() os recalcula apos carregar back/.env para refletir o .env real.
MODEL_SPECS = _build_model_specs()
CONDITIONS = _build_conditions()

# Thresholds do sweep do DeepEval (compatibilidade com o relatorio original).
THRESHOLDS = [0.5, 0.6, 0.7, 0.8, 0.9]

# Sweep denso para a taxa de aprovacao do avaliador de referencia (score >= threshold,
# sem rotulo de verdade -- so contagem direta contra o gabarito).
REFERENCE_THRESHOLDS = [round(0.05 * i, 2) for i in range(21)]

CASES_PATH = PROJECT_ROOT / "tests" / "evals" / "model_eval_cases.json"
OUTPUT_DIR = PROJECT_ROOT / "avaliacao_modelos"

# Prompt do modo "sem RAG": o LLM responde sem contexto recuperado.
NO_RAG_SYSTEM = (
    "Voce e o TitasBot, assistente sobre a equipe Titas da Robotica "
    "(IFES Campus Colatina; a equipe ja se chamou Asimov). Responda em portugues, "
    "de forma objetiva e fiel ao que voce sabe. Se nao tiver a informacao, diga isso."
)


@dataclass(frozen=True)
class ModelEvalCase:
    id: str
    number: int
    category: str
    question: str
    expected_output: str
    scored: bool
    skip_reason: str = ""
    correctness_threshold: float = 0.55
    answer_relevancy_threshold: float = 0.6
    faithfulness_threshold: float = 0.7
    hallucination_threshold: float = 0.5


@dataclass(frozen=True)
class MetricResult:
    name: str
    score: float | None
    threshold: float | None
    passed: bool | None
    reason: str
    error: str


@dataclass(frozen=True)
class ModelCaseResult:
    model: str
    case_id: str
    number: int
    category: str
    question: str
    expected_output: str
    answer: str
    scored: bool
    skipped: bool
    skip_reason: str
    passed: bool | None
    score: float | None
    metrics: list[MetricResult]
    retrieval_query: str
    sources: list[str]
    error: str
    # --- campos da matriz multi-provedor / duas metodologias ---
    condition: str = "rag"
    provider: str = ""
    ref_semantic: float | None = None
    ref_lexical: float | None = None
    ref_final: float | None = None


def load_cases(path: Path = CASES_PATH) -> list[ModelEvalCase]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("model_eval_cases.json deve conter uma lista de casos.")

    cases: list[ModelEvalCase] = []
    required = {"id", "number", "category", "question", "expected_output", "scored", "skip_reason"}
    for idx, raw in enumerate(data, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"Caso #{idx} deve ser um objeto JSON.")
        missing = sorted(required - set(raw))
        if missing:
            raise ValueError(f"Caso #{idx} sem campos obrigatorios: {', '.join(missing)}")

        scored = bool(raw["scored"])
        expected_output = str(raw.get("expected_output", "")).strip()
        if scored and not expected_output:
            raise ValueError(f"Caso {raw['id']} esta marcado como scored=true sem expected_output.")

        cases.append(
            ModelEvalCase(
                id=str(raw["id"]),
                number=int(raw["number"]),
                category=str(raw["category"]),
                question=str(raw["question"]).strip(),
                expected_output=expected_output,
                scored=scored,
                skip_reason=str(raw.get("skip_reason", "")).strip(),
                correctness_threshold=float(raw.get("correctness_threshold", 0.55)),
                answer_relevancy_threshold=float(raw.get("answer_relevancy_threshold", 0.6)),
                faithfulness_threshold=float(raw.get("faithfulness_threshold", 0.7)),
                hallucination_threshold=float(raw.get("hallucination_threshold", 0.5)),
            )
        )
    return cases


@dataclass(frozen=True)
class _DeepEvalImports:
    GEval: Any
    AnswerRelevancyMetric: Any
    FaithfulnessMetric: Any
    HallucinationMetric: Any
    LLMTestCase: Any
    SingleTurnParams: Any


def _import_deepeval() -> _DeepEvalImports:
    try:
        from deepeval.metrics import (
            AnswerRelevancyMetric,
            FaithfulnessMetric,
            GEval,
            HallucinationMetric,
        )
        from deepeval.test_case import LLMTestCase, SingleTurnParams
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "DeepEval nao esta instalado neste ambiente. Rode `pip install -r requirements.txt` "
            "no ambiente do projeto antes de executar scripts/evaluate_models.py."
        ) from exc
    return _DeepEvalImports(
        GEval=GEval,
        AnswerRelevancyMetric=AnswerRelevancyMetric,
        FaithfulnessMetric=FaithfulnessMetric,
        HallucinationMetric=HallucinationMetric,
        LLMTestCase=LLMTestCase,
        SingleTurnParams=SingleTurnParams,
    )


@lru_cache(maxsize=1)
def _build_eval_model() -> Any:
    """Modelo usado pelo DeepEval para avaliar as 4 metricas.

    DEEPEVAL_EVAL_PROVIDER=openai (padrao, retrocompativel): devolve a string
    crua do modelo -- o DeepEval resolve isso internamente assumindo OpenAI,
    igual ao comportamento original. Outros provedores usam os wrappers
    nativos do deepeval.models (evita autoavaliacao: o juiz/avaliador nao
    deveria ser um dos modelos comparados).
    """
    eval_model = os.getenv("DEEPEVAL_EVAL_MODEL", "gpt-4o-mini")
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


def build_metrics(case: ModelEvalCase, has_retrieval_context: bool) -> list[Any]:
    deepeval = _import_deepeval()
    eval_model = _build_eval_model()
    # Default "full": o usuario pediu fidelidade e alucinacao como parte do
    # teste, entao o comportamento de fabrica ja inclui as duas (rebaixe para
    # "fast"/"standard" via env para um smoke test mais barato).
    metric_set = os.getenv("MODEL_EVAL_METRIC_SET", "full").lower()
    include_reason = os.getenv("DEEPEVAL_INCLUDE_REASON", "0") == "1"

    metrics: list[Any] = [
        deepeval.GEval(
            name="Correctness",
            criteria=(
                "Determine se a resposta real esta correta em relacao a resposta esperada. "
                "Aceite variacoes de redacao, mas penalize fatos ausentes, anos errados, "
                "classificacoes erradas ou invencao de informacoes. Nao penalize detalhes "
                "adicionais quando forem compativeis com a resposta esperada e nao mudarem "
                "o sentido principal."
            ),
            evaluation_params=[
                deepeval.SingleTurnParams.INPUT,
                deepeval.SingleTurnParams.ACTUAL_OUTPUT,
                deepeval.SingleTurnParams.EXPECTED_OUTPUT,
            ],
            threshold=case.correctness_threshold,
            model=eval_model,
            async_mode=False,
        )
    ]

    if metric_set in {"standard", "full"}:
        metrics.append(
            deepeval.AnswerRelevancyMetric(
                threshold=case.answer_relevancy_threshold,
                model=eval_model,
                include_reason=include_reason,
                async_mode=False,
            )
        )

    if metric_set == "full" and has_retrieval_context:
        metrics.append(
            deepeval.FaithfulnessMetric(
                threshold=case.faithfulness_threshold,
                model=eval_model,
                truths_extraction_limit=int(os.getenv("MODEL_EVAL_TRUTHS_LIMIT", "8")),
                include_reason=include_reason,
                async_mode=False,
            )
        )

    # Incondicional (fora do sistema de tiers): nao depende de retrieval_context
    # (usa expected_output como "context" -- ver make_test_case), e foi pedida
    # explicitamente junto com fidelidade. Assim mesmo um smoke test em "fast"
    # ja exercita/reporta a metrica de alucinacao.
    metrics.append(
        deepeval.HallucinationMetric(
            threshold=case.hallucination_threshold,
            model=eval_model,
            include_reason=include_reason,
            async_mode=False,
        )
    )

    return metrics


def make_test_case(case: ModelEvalCase, answer: str, retrieval_context: list[str]) -> Any:
    deepeval = _import_deepeval()
    return deepeval.LLMTestCase(
        input=case.question,
        actual_output=answer,
        expected_output=case.expected_output,
        retrieval_context=retrieval_context,
        # HallucinationMetric usa `context` (nao `retrieval_context`): uma
        # referencia curada, nao o que foi de fato recuperado pelo RAG. Usar o
        # gabarito aqui faz "alucinacao" significar consistentemente "contradiz
        # a resposta esperada" nas duas condicoes (com/sem RAG); "fidelidade"
        # (Faithfulness, so roda com RAG) continua significando "contradiz o
        # que foi de fato recuperado" -- os dois ficam com sentidos distintos.
        context=[case.expected_output],
    )


def measure_metrics(metrics: list[Any], test_case: Any) -> list[MetricResult]:
    results: list[MetricResult] = []
    for metric in metrics:
        name = str(getattr(metric, "name", metric.__class__.__name__))
        threshold = _to_float(getattr(metric, "threshold", None))
        try:
            measured = metric.measure(test_case)
            score = _to_float(getattr(metric, "score", measured))
            passed = getattr(metric, "success", None)
            if passed is None and hasattr(metric, "is_successful"):
                passed = metric.is_successful()
            if passed is None and score is not None and threshold is not None:
                passed = score >= threshold
            reason = str(getattr(metric, "reason", "") or "")
            results.append(
                MetricResult(
                    name=name,
                    score=score,
                    threshold=threshold,
                    passed=bool(passed) if passed is not None else None,
                    reason=reason,
                    error="",
                )
            )
        except Exception as exc:
            results.append(
                MetricResult(
                    name=name,
                    score=None,
                    threshold=threshold,
                    passed=False,
                    reason="",
                    error=str(exc),
                )
            )
    return results


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def primary_score(metrics: list[MetricResult]) -> float | None:
    for metric in metrics:
        if metric.name.lower() == "correctness" and metric.score is not None:
            return metric.score
    scores = [metric.score for metric in metrics if metric.score is not None]
    return (sum(scores) / len(scores)) if scores else None


def result_passed(metrics: list[MetricResult]) -> bool | None:
    if not metrics:
        return None
    return all(metric.passed is True and not metric.error for metric in metrics)


def answer_without_rag(model_client: Any, question: str) -> str:
    """Responde sem RAG: chama o LLM diretamente, sem contexto recuperado."""
    from langchain_core.prompts import ChatPromptTemplate

    from app.infrastructure.llm_factory import to_text

    message = ChatPromptTemplate.from_messages(
        [("system", NO_RAG_SYSTEM), ("human", "{question}")]
    ).invoke({"question": question})
    try:
        return to_text(model_client.invoke(message)).strip()
    except Exception:
        return ""


def skipped_result(
    model: str,
    case: ModelEvalCase,
    condition: str = "rag",
    provider: str = "",
) -> ModelCaseResult:
    return ModelCaseResult(
        model=model,
        case_id=case.id,
        number=case.number,
        category=case.category,
        question=case.question,
        expected_output=case.expected_output,
        answer="",
        scored=False,
        skipped=True,
        skip_reason=case.skip_reason or "Caso sem gabarito.",
        passed=None,
        score=None,
        metrics=[],
        retrieval_query="",
        sources=[],
        error="",
        condition=condition,
        provider=provider,
    )


def evaluate_case(
    spec: ModelSpec,
    condition: str,
    bot: Any,
    case: ModelEvalCase,
    max_context_chars: int,
    reference_available: bool,
) -> ModelCaseResult:
    if not case.scored:
        return skipped_result(spec.model, case, condition=condition, provider=spec.provider)

    try:
        from app.application.helpers import summarize_sources

        if condition == "no_rag":
            answer = answer_without_rag(bot.model, case.question)
            retrieval_query = "no_rag"
            sources: list[str] = []
            retrieval_context: list[str] = []
        else:
            chat_result = bot.ask(question=case.question)
            answer = chat_result.answer
            retrieval_query = chat_result.retrieval_query
            sources = summarize_sources(chat_result.chunks)
            retrieval_context = [chunk.content[:max_context_chars] for chunk in chat_result.chunks[:6]]

        # Metodologia 1: DeepEval (GEval/Relevancy/Faithfulness/Hallucination),
        # sempre comparando com o gabarito (expected_output) -- ver build_metrics().
        metrics = build_metrics(case, has_retrieval_context=bool(retrieval_context))
        test_case = make_test_case(case, answer, retrieval_context)
        metric_results = measure_metrics(metrics, test_case)

        # Metodologia 2: avaliador de referencia (semantica + lexica).
        # Isolado em try/except proprio: uma falha aqui (ex.: 1o download do
        # modelo MiniLM sem rede disponivel) nao pode descartar o score do
        # DeepEval acima, que ja foi calculado com sucesso.
        ref_semantic = ref_lexical = ref_final = None
        if reference_available:
            try:
                from app.evaluation.reference_scorer import final_score

                ref = final_score(case.expected_output, answer)
                ref_semantic, ref_lexical, ref_final = ref["semantic"], ref["lexical"], ref["final"]
            except Exception as exc:
                print(f"    [aviso] avaliador de referencia falhou em {case.id}: {exc}")

        return ModelCaseResult(
            model=spec.model,
            case_id=case.id,
            number=case.number,
            category=case.category,
            question=case.question,
            expected_output=case.expected_output,
            answer=answer,
            scored=True,
            skipped=False,
            skip_reason="",
            passed=result_passed(metric_results),
            score=primary_score(metric_results),
            metrics=metric_results,
            retrieval_query=retrieval_query,
            sources=sources,
            error="",
            condition=condition,
            provider=spec.provider,
            ref_semantic=ref_semantic,
            ref_lexical=ref_lexical,
            ref_final=ref_final,
        )
    except Exception as exc:
        return ModelCaseResult(
            model=spec.model,
            case_id=case.id,
            number=case.number,
            category=case.category,
            question=case.question,
            expected_output=case.expected_output,
            answer="",
            scored=True,
            skipped=False,
            skip_reason="",
            passed=False,
            score=None,
            metrics=[],
            retrieval_query="",
            sources=[],
            error=str(exc),
            condition=condition,
            provider=spec.provider,
        )


def _distinct_groups(results: list[ModelCaseResult]) -> list[tuple[str, str]]:
    """Pares (modelo, condicao) na ordem de primeira aparicao."""
    groups: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for result in results:
        key = (result.model, result.condition)
        if key not in seen:
            seen.add(key)
            groups.append(key)
    return groups


def aggregate_by_model(results: list[ModelCaseResult]) -> list[dict[str, Any]]:
    """Resumo por (modelo, condicao). Ignora casos pulados nas medias."""
    summary: list[dict[str, Any]] = []
    for model, condition in _distinct_groups(results):
        model_results = [r for r in results if r.model == model and r.condition == condition]
        evaluated = [r for r in model_results if r.scored and not r.skipped]
        scored_with_score = [r for r in evaluated if r.score is not None]
        passed = sum(1 for r in evaluated if r.passed is True)
        failed = sum(1 for r in evaluated if r.passed is False)
        avg_score = (
            sum(r.score for r in scored_with_score if r.score is not None) / len(scored_with_score)
            if scored_with_score
            else None
        )
        # Taxa de aprovacao do DeepEval Correctness = INDICADOR PRINCIPAL de
        # qualidade do modelo (compara direto com o gabarito). avg_ref_score e
        # a nota media da metodologia de referencia (semantica+lexical, sem
        # LLM), reportada em paralelo como um segundo angulo sobre o gabarito.
        scored_with_ref = [r for r in evaluated if r.ref_final is not None]
        avg_ref_score = (
            sum(r.ref_final for r in scored_with_ref if r.ref_final is not None) / len(scored_with_ref)
            if scored_with_ref
            else None
        )
        summary.append(
            {
                "model": model,
                "condition": condition,
                "total_cases": len(model_results),
                "total_scored": sum(1 for r in model_results if r.scored),
                "total_skipped": sum(1 for r in model_results if r.skipped),
                "total_evaluated": len(evaluated),
                "passed": passed,
                "failed": failed,
                "avg_score": avg_score,
                "pass_rate": (passed / len(evaluated)) if evaluated else None,
                "avg_ref_score": avg_ref_score,
            }
        )
    return summary


def metrics_by_threshold(
    results: list[ModelCaseResult],
    thresholds: list[float] = THRESHOLDS,
) -> list[dict[str, Any]]:
    """Sweep do score DeepEval por (modelo, condicao)."""
    rows: list[dict[str, Any]] = []
    for model, condition in _distinct_groups(results):
        evaluated = [
            r
            for r in results
            if r.model == model
            and r.condition == condition
            and r.scored
            and not r.skipped
            and r.score is not None
        ]
        avg_score = (
            sum(r.score for r in evaluated if r.score is not None) / len(evaluated) if evaluated else None
        )
        for threshold in thresholds:
            passed = sum(1 for r in evaluated if r.score is not None and r.score >= threshold)
            rows.append(
                {
                    "model": model,
                    "condition": condition,
                    "threshold": threshold,
                    "total_evaluated": len(evaluated),
                    "passed": passed,
                    "failed": len(evaluated) - passed,
                    "pass_rate": (passed / len(evaluated)) if evaluated else None,
                    "avg_score": avg_score,
                }
            )
    return rows


def reference_metrics_by_threshold(
    results: list[ModelCaseResult],
    thresholds: list[float] | None = None,
) -> list[dict[str, Any]]:
    """Sweep do score de referencia (semantica+lexical) por (modelo, condicao).

    Espelha metrics_by_threshold(), mas para r.ref_final em vez de r.score.
    Nao exige rotulo de verdade nenhum: so conta quantas respostas tem
    ref_final >= threshold, comparando direto com o gabarito.
    """
    if thresholds is None:
        thresholds = REFERENCE_THRESHOLDS
    rows: list[dict[str, Any]] = []
    for model, condition in _distinct_groups(results):
        evaluated = [
            r
            for r in results
            if r.model == model
            and r.condition == condition
            and r.scored
            and not r.skipped
            and r.ref_final is not None
        ]
        avg_score = (
            sum(r.ref_final for r in evaluated if r.ref_final is not None) / len(evaluated)
            if evaluated
            else None
        )
        for threshold in thresholds:
            passed = sum(1 for r in evaluated if r.ref_final is not None and r.ref_final >= threshold)
            rows.append(
                {
                    "model": model,
                    "condition": condition,
                    "threshold": threshold,
                    "total_evaluated": len(evaluated),
                    "passed": passed,
                    "failed": len(evaluated) - passed,
                    "pass_rate": (passed / len(evaluated)) if evaluated else None,
                    "avg_score": avg_score,
                }
            )
    return rows


def write_reports(
    output_dir: Path,
    results: list[ModelCaseResult],
    summary: list[dict[str, Any]],
    threshold_rows: list[dict[str, Any]],
    *,
    reference_threshold_rows: list[dict[str, Any]] | None = None,
    model_specs: list[ModelSpec] | None = None,
    conditions: list[str] | None = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_results_csv(output_dir / "respostas_por_modelo.csv", results)
    _write_dict_csv(output_dir / "resumo_modelos.csv", summary)
    _write_dict_csv(output_dir / "metricas_por_threshold.csv", threshold_rows)
    if reference_threshold_rows:
        _write_dict_csv(output_dir / "metricas_referencia_por_threshold.csv", reference_threshold_rows)
    _write_json_report(
        output_dir / "avaliacao_modelos.json",
        results,
        summary,
        threshold_rows,
        reference_threshold_rows=reference_threshold_rows,
        model_specs=model_specs,
        conditions=conditions,
    )
    _write_html_report(output_dir / "avaliacao_modelos.html", results, summary)

    # Paginas extras (visualizador nos moldes do projeto de referencia).
    try:
        from app.evaluation.report_html import write_como_funciona_html, write_comparacao_html

        write_comparacao_html(
            output_dir / "comparacao_metricas.html",
            summary,
            reference_threshold_rows or [],
        )
        write_como_funciona_html(output_dir / "como_funciona.html")
    except Exception as exc:  # nao falhar a rodada por causa das paginas extras
        print(f"[aviso] paginas extras nao geradas: {exc}")


def _write_results_csv(path: Path, results: list[ModelCaseResult]) -> None:
    fieldnames = [
        "model",
        "provider",
        "condition",
        "case_id",
        "number",
        "category",
        "scored",
        "skipped",
        "passed",
        "score",
        "ref_semantic",
        "ref_lexical",
        "ref_final",
        "metrics",
        "question",
        "expected_output",
        "answer",
        "error",
        "sources",
        "retrieval_query",
        "skip_reason",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "model": result.model,
                    "provider": result.provider,
                    "condition": result.condition,
                    "case_id": result.case_id,
                    "number": result.number,
                    "category": result.category,
                    "scored": result.scored,
                    "skipped": result.skipped,
                    "passed": result.passed,
                    "score": _format_optional_float(result.score),
                    "ref_semantic": _format_optional_float(result.ref_semantic),
                    "ref_lexical": _format_optional_float(result.ref_lexical),
                    "ref_final": _format_optional_float(result.ref_final),
                    "metrics": json.dumps([asdict(metric) for metric in result.metrics], ensure_ascii=False),
                    "question": result.question,
                    "expected_output": result.expected_output,
                    "answer": result.answer,
                    "error": result.error,
                    "sources": " | ".join(result.sources),
                    "retrieval_query": result.retrieval_query,
                    "skip_reason": result.skip_reason,
                }
            )


def _write_dict_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as fp:
        if not fieldnames:
            fp.write("")
            return
        writer = csv.DictWriter(fp, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _format_value(value) for key, value in row.items()})


def _write_json_report(
    path: Path,
    results: list[ModelCaseResult],
    summary: list[dict[str, Any]],
    threshold_rows: list[dict[str, Any]],
    *,
    reference_threshold_rows: list[dict[str, Any]] | None = None,
    model_specs: list[ModelSpec] | None = None,
    conditions: list[str] | None = None,
) -> None:
    payload = {
        "models": [spec.model for spec in model_specs] if model_specs else sorted({r.model for r in results}),
        "model_specs": [asdict(spec) for spec in model_specs] if model_specs else [],
        "conditions": conditions if conditions is not None else sorted({r.condition for r in results}),
        "metric_set": os.getenv("MODEL_EVAL_METRIC_SET", "full").lower(),
        "eval_model": os.getenv("DEEPEVAL_EVAL_MODEL", "gpt-4o-mini"),
        "eval_provider": os.getenv("DEEPEVAL_EVAL_PROVIDER", "openai"),
        "summary": summary,
        "threshold_metrics": threshold_rows,
        "reference_threshold_metrics": reference_threshold_rows or [],
        "results": [
            {
                **asdict(result),
                "metrics": [asdict(metric) for metric in result.metrics],
            }
            for result in results
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_html_report(path: Path, results: list[ModelCaseResult], summary: list[dict[str, Any]]) -> None:
    summary_cards = "\n".join(
        f"""
        <article class="card">
          <h2>{html.escape(str(row["model"]))}</h2>
          <p class="cond">Condicao: <strong>{html.escape(str(row.get("condition", "")))}</strong></p>
          <p><strong>Avaliados:</strong> {row["total_evaluated"]}</p>
          <p><strong>Aprovados:</strong> {row["passed"]}/{row["total_evaluated"]}</p>
          <p><strong>Score medio:</strong> {html.escape(_format_optional_float(row["avg_score"]))}</p>
          <p><strong>Skipped:</strong> {row["total_skipped"]}</p>
        </article>
        """
        for row in summary
    )

    result_rows = "\n".join(
        f"""
        <tr>
          <td>{html.escape(result.model)}</td>
          <td>{html.escape(result.condition)}</td>
          <td>{result.number}</td>
          <td>{html.escape(result.category)}</td>
          <td>{html.escape(result.question)}</td>
          <td>{html.escape(_status_label(result))}</td>
          <td>{html.escape(_format_optional_float(result.score))}</td>
          <td>{html.escape(_format_optional_float(result.ref_final))}</td>
          <td>{html.escape(result.answer[:500])}</td>
          <td>{html.escape(result.error or result.skip_reason)}</td>
        </tr>
        """
        for result in results
    )

    page = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Avaliacao de modelos - TitasBot</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f6f7fb; color: #111827; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 32px 20px; }}
    h1 {{ margin: 0 0 16px; }}
    nav a {{ margin-right: 16px; }}
    .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-bottom: 24px; }}
    .card {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; }}
    .card .cond {{ color: #6b7280; margin-top: 0; }}
    .table-wrap {{ overflow-x: auto; background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid #e5e7eb; text-align: left; vertical-align: top; }}
    th {{ background: #f9fafb; }}
    td:nth-child(9) {{ min-width: 320px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <main>
    <h1>Avaliacao de modelos - TitasBot</h1>
    <nav><a href="comparacao_metricas.html">Comparacao de metricas</a><a href="como_funciona.html">Como funciona</a></nav>
    <section class="summary">{summary_cards}</section>
    <section class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Modelo</th>
            <th>Cond.</th>
            <th>#</th>
            <th>Categoria</th>
            <th>Pergunta</th>
            <th>Status</th>
            <th>Score (DeepEval)</th>
            <th>Score (ref.)</th>
            <th>Resposta</th>
            <th>Obs.</th>
          </tr>
        </thead>
        <tbody>{result_rows}</tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""
    path.write_text(page, encoding="utf-8")


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    if value is None:
        return ""
    return str(value)


def _format_optional_float(value: float | None) -> str:
    return "" if value is None else f"{value:.4f}"


def _status_label(result: ModelCaseResult) -> str:
    if result.skipped:
        return "skipped"
    if result.error:
        return "erro"
    if result.passed is True:
        return "aprovado"
    if result.passed is False:
        return "falhou"
    return "sem avaliacao"


def run_matrix() -> list[ModelCaseResult]:
    from app.application.chat_service import TitasBotService
    from app.infrastructure.env import load_project_env
    from app.infrastructure.net_env import clear_broken_local_proxy
    from app.infrastructure.settings import get_settings

    clear_broken_local_proxy()
    load_project_env()
    # Recalculados apos load_project_env(): assim EVAL_* configurado so em
    # back/.env (nao so no shell) tambem e respeitado (ver _build_model_specs).
    model_specs = _build_model_specs()
    conditions = _build_conditions()
    settings = get_settings()
    cases = load_cases()
    # EVAL_CASE_IDS tem prioridade sobre EVAL_CASE_LIMIT: permite um subconjunto
    # ESTRATIFICADO (uma amostra de cada categoria) em vez dos N primeiros, que
    # cairiam todos na mesma categoria. Casa por prefixo do id ("q10" casa
    # "q10_quais_foram_classificacoes_equipe_temporada").
    case_ids_raw = os.getenv("EVAL_CASE_IDS")
    case_limit_raw = os.getenv("EVAL_CASE_LIMIT")
    if case_ids_raw:
        wanted = [p.strip() for p in case_ids_raw.split(",") if p.strip()]
        cases = [c for c in cases if c.scored and any(c.id.startswith(p) for p in wanted)]
        encontrados = {p for p in wanted for c in cases if c.id.startswith(p)}
        faltando = sorted(set(wanted) - encontrados)
        if faltando:
            raise ValueError(f"EVAL_CASE_IDS: nenhum caso casa com {faltando}")
        print(f"[aviso] EVAL_CASE_IDS: subconjunto com {len(cases)} caso(s) com gabarito.")
    elif case_limit_raw:
        limit = int(case_limit_raw)
        cases = [c for c in cases if c.scored][:limit]
        print(f"[aviso] EVAL_CASE_LIMIT={limit}: smoke test com {len(cases)} caso(s) com gabarito.")
    max_context_chars = int(os.getenv("MODEL_EVAL_CONTEXT_CHARS", "1200"))
    _import_deepeval()

    from app.evaluation.reference_scorer import reference_scoring_available

    reference_available = reference_scoring_available()
    if not reference_available:
        print(
            "[aviso] sentence-transformers indisponivel: a metodologia de referencia "
            "sera pulada (ref_* = None)."
        )

    print(f"Modelos: {[s.model for s in model_specs]}")
    print(f"Condicoes: {conditions}")

    results: list[ModelCaseResult] = []
    try:
        for spec in model_specs:
            print(f"\n== Avaliando: {spec.label} ({spec.model} / {spec.provider}) ==")
            model_settings = replace(settings, chat_model=spec.model, chat_provider=spec.provider)
            bot = TitasBotService(model_settings)
            if "rag" in conditions and not bot.has_documents():
                raise RuntimeError("Base vetorial vazia. Rode criar_db.py antes da avaliacao com RAG.")

            for condition in conditions:
                print(f"  -- condicao: {condition} --")
                for case in cases:
                    if not case.scored:
                        results.append(skipped_result(spec.model, case, condition=condition, provider=spec.provider))
                        continue

                    print(f"  [{spec.label}/{condition}] #{case.number} {case.id}")
                    result = evaluate_case(
                        spec, condition, bot, case, max_context_chars, reference_available
                    )
                    results.append(result)
                    status = _status_label(result)
                    score = _format_optional_float(result.score)
                    extra = ""
                    if result.ref_final is not None:
                        extra += f" | ref={_format_optional_float(result.ref_final)}"
                    print(f"    -> {status}" + (f" | score={score}" if score else "") + extra)
    finally:
        # Sempre grava o que foi coletado ate aqui, mesmo que o loop acima
        # tenha sido interrompido por uma excecao (ex.: chave de API invalida
        # no 2o/3o provedor, depois que o 1o ja rodou por completo). A
        # excecao original, se houver, continua propagando apos o finally.
        if results:
            summary = aggregate_by_model(results)
            threshold_rows = metrics_by_threshold(results)
            reference_threshold_rows = reference_metrics_by_threshold(results)
            write_reports(
                OUTPUT_DIR,
                results,
                summary,
                threshold_rows,
                reference_threshold_rows=reference_threshold_rows,
                model_specs=model_specs,
                conditions=conditions,
            )
            print(f"\nRelatorios salvos em: {OUTPUT_DIR}")
        else:
            print("\nNenhum resultado coletado; relatorios nao foram gerados.")

    return results


def run() -> list[ModelCaseResult]:
    """Alias retrocompativel."""
    return run_matrix()


def main() -> None:
    run_matrix()


if __name__ == "__main__":
    main()
