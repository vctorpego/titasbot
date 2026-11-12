from __future__ import annotations

"""Metricas de avaliacao em duas etapas para RAG.

Recuperacao:
- Hit@5: pelo menos um dos 5 primeiros chunks contem evidencia suficiente.
- Precision@5: proporcao dos 5 primeiros chunks julgados relevantes.

Geracao:
- os scores de Answer Correctness e Faithfulness sao calculados no script com
  DeepEval; este modulo mantem a estrutura, classificacao e escrita visual.
"""

import csv
import html
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

from app.infrastructure.retrieval import RetrievedChunk
from app.infrastructure.text_utils import normalize_text


DEFAULT_TOP_K = 5


@dataclass(frozen=True)
class RagStageEvalCase:
    id: str
    number: int
    category: str
    question: str
    expected_output: str
    evidence_terms: list[str]
    min_terms_for_relevant_chunk: int
    min_terms_for_sufficient_chunk: int
    correctness_threshold: float = 0.55
    faithfulness_threshold: float = 0.70


@dataclass(frozen=True)
class RetrievedChunkEval:
    rank: int
    source: str
    page: int | None
    vector_score: float
    lexical_score: float
    final_score: float
    matched_terms: list[str]
    relevant: bool
    sufficient: bool
    content_preview: str


@dataclass(frozen=True)
class RetrievalStageScore:
    hit_at_5: float
    precision_at_5: float
    relevant_chunks: int
    sufficient_chunks: int
    top_k: int
    chunks: list[RetrievedChunkEval]


@dataclass(frozen=True)
class GenerationMetricScore:
    name: str
    score: float | None
    threshold: float
    passed: bool | None
    reason: str = ""
    error: str = ""


@dataclass(frozen=True)
class RagStageResult:
    case_id: str
    number: int
    category: str
    question: str
    expected_output: str
    answer: str
    retrieval_query: str
    retrieval: RetrievalStageScore
    correctness: GenerationMetricScore
    faithfulness: GenerationMetricScore
    diagnosis: str
    error: str = ""


def load_stage_cases(annotations_path: Path, official_cases_path: Path) -> list[RagStageEvalCase]:
    annotations = json.loads(annotations_path.read_text(encoding="utf-8"))
    official = json.loads(official_cases_path.read_text(encoding="utf-8"))
    if not isinstance(annotations, list):
        raise ValueError("rag_stage_eval_cases.json deve conter uma lista.")
    if not isinstance(official, list):
        raise ValueError("model_eval_cases.json deve conter uma lista.")

    official_by_id = {str(case.get("id")): case for case in official}
    cases: list[RagStageEvalCase] = []
    for idx, raw in enumerate(annotations, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"Anotacao #{idx} deve ser um objeto.")
        case_id = str(raw.get("id", "")).strip()
        source = official_by_id.get(case_id)
        if source is None:
            raise ValueError(f"Anotacao #{idx}: caso oficial nao encontrado: {case_id}")
        if not source.get("scored"):
            raise ValueError(f"Anotacao #{idx}: caso oficial nao e pontuavel: {case_id}")

        evidence_terms = [str(term).strip() for term in raw.get("evidence_terms", []) if str(term).strip()]
        if not evidence_terms:
            raise ValueError(f"Anotacao #{idx}: evidence_terms vazio.")

        cases.append(
            RagStageEvalCase(
                id=case_id,
                number=int(source["number"]),
                category=str(source["category"]),
                question=str(source["question"]).strip(),
                expected_output=str(source["expected_output"]).strip(),
                evidence_terms=evidence_terms,
                min_terms_for_relevant_chunk=max(1, int(raw.get("min_terms_for_relevant_chunk", 1))),
                min_terms_for_sufficient_chunk=max(1, int(raw.get("min_terms_for_sufficient_chunk", 1))),
                correctness_threshold=float(raw.get("correctness_threshold", 0.55)),
                faithfulness_threshold=float(raw.get("faithfulness_threshold", 0.70)),
            )
        )
    return cases


def score_retrieval(
    case: RagStageEvalCase,
    chunks: Sequence[RetrievedChunk],
    top_k: int = DEFAULT_TOP_K,
) -> RetrievalStageScore:
    top_chunks = list(chunks[:top_k])
    evaluated = [_evaluate_chunk(case, chunk, rank=idx) for idx, chunk in enumerate(top_chunks, start=1)]
    relevant = sum(1 for chunk in evaluated if chunk.relevant)
    sufficient = sum(1 for chunk in evaluated if chunk.sufficient)
    return RetrievalStageScore(
        hit_at_5=1.0 if sufficient else 0.0,
        precision_at_5=relevant / top_k,
        relevant_chunks=relevant,
        sufficient_chunks=sufficient,
        top_k=top_k,
        chunks=evaluated,
    )


def classify_diagnosis(
    retrieval: RetrievalStageScore,
    correctness: GenerationMetricScore,
    faithfulness: GenerationMetricScore,
) -> str:
    retrieval_ok = retrieval.hit_at_5 >= 1.0
    generation_ok = correctness.passed is True and faithfulness.passed is True
    if retrieval_ok and generation_ok:
        return "ok"
    if not retrieval_ok and generation_ok:
        return "retrieval_error"
    if retrieval_ok and not generation_ok:
        return "generation_error"
    return "both_error"


def summarize_results(results: Sequence[RagStageResult]) -> dict[str, Any]:
    total = len(results)
    correctness_scores = [r.correctness.score for r in results if r.correctness.score is not None]
    faithfulness_scores = [r.faithfulness.score for r in results if r.faithfulness.score is not None]
    return {
        "total_cases": total,
        "avg_hit_at_5": _avg([r.retrieval.hit_at_5 for r in results]),
        "avg_precision_at_5": _avg([r.retrieval.precision_at_5 for r in results]),
        "avg_answer_correctness": _avg(correctness_scores),
        "avg_faithfulness": _avg(faithfulness_scores),
        "retrieval_pass_rate": _avg([1.0 if r.retrieval.hit_at_5 >= 1 else 0.0 for r in results]),
        "correctness_pass_rate": _avg([1.0 if r.correctness.passed is True else 0.0 for r in results]),
        "faithfulness_pass_rate": _avg([1.0 if r.faithfulness.passed is True else 0.0 for r in results]),
        "diagnosis_counts": {
            "ok": sum(1 for r in results if r.diagnosis == "ok"),
            "retrieval_error": sum(1 for r in results if r.diagnosis == "retrieval_error"),
            "generation_error": sum(1 for r in results if r.diagnosis == "generation_error"),
            "both_error": sum(1 for r in results if r.diagnosis == "both_error"),
        },
    }


def summarize_by_category(results: Sequence[RagStageResult]) -> list[dict[str, Any]]:
    categories: list[str] = []
    for result in results:
        if result.category not in categories:
            categories.append(result.category)

    rows = []
    for category in categories:
        selected = [result for result in results if result.category == category]
        rows.append(
            {
                "category": category,
                "cases": len(selected),
                "hit_at_5": _avg([r.retrieval.hit_at_5 for r in selected]),
                "precision_at_5": _avg([r.retrieval.precision_at_5 for r in selected]),
                "answer_correctness": _avg([r.correctness.score for r in selected if r.correctness.score is not None]),
                "faithfulness": _avg([r.faithfulness.score for r in selected if r.faithfulness.score is not None]),
                "ok": sum(1 for r in selected if r.diagnosis == "ok"),
                "retrieval_error": sum(1 for r in selected if r.diagnosis == "retrieval_error"),
                "generation_error": sum(1 for r in selected if r.diagnosis == "generation_error"),
                "both_error": sum(1 for r in selected if r.diagnosis == "both_error"),
            }
        )
    return rows


def write_outputs(output_dir: Path, results: Sequence[RagStageResult]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_results(results)
    by_category = summarize_by_category(results)
    payload = {
        "summary": summary,
        "by_category": by_category,
        "results": [asdict(result) for result in results],
    }
    (output_dir / "rag_4_metricas.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_csv(output_dir / "rag_4_metricas.csv", results)
    write_html(output_dir / "rag_4_metricas.html", results, summary, by_category)


def write_html(
    path: Path,
    results: Sequence[RagStageResult],
    summary: dict[str, Any] | None = None,
    by_category: Sequence[dict[str, Any]] | None = None,
) -> None:
    summary = summary or summarize_results(results)
    by_category = by_category or summarize_by_category(results)
    cards = "".join(
        _card(label, _fmt_percent(summary.get(key)), note)
        for label, key, note in [
            ("Hit@5", "avg_hit_at_5", "recuperacao"),
            ("Precision@5", "avg_precision_at_5", "recuperacao"),
            ("Answer Correctness", "avg_answer_correctness", "geracao"),
            ("Faithfulness", "avg_faithfulness", "geracao"),
        ]
    )
    methodology = _methodology_section()
    category_rows = "".join(
        f"""
        <tr>
          <td>{html.escape(str(row["category"]))}</td>
          <td>{row["cases"]}</td>
          <td>{_fmt_percent(row["hit_at_5"])}</td>
          <td>{_fmt_percent(row["precision_at_5"])}</td>
          <td>{_fmt_percent(row["answer_correctness"])}</td>
          <td>{_fmt_percent(row["faithfulness"])}</td>
          <td>{row["ok"]}</td>
          <td>{row["retrieval_error"]}</td>
          <td>{row["generation_error"]}</td>
          <td>{row["both_error"]}</td>
        </tr>
        """
        for row in by_category
    )
    case_panels = "".join(_case_panel(result) for result in results)
    page = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Avaliacao RAG - 4 metricas</title>
  <style>
    :root {{ color-scheme: light; }}
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: #f5f7fb; color: #111827; }}
    main {{ max-width: 1220px; margin: 0 auto; padding: 32px 20px; }}
    h1 {{ margin: 0 0 8px; }}
    h2 {{ margin: 28px 0 12px; }}
    .lead, .muted {{ color: #4b5563; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; margin: 22px 0 24px; }}
    .card {{ background: #fff; border: 1px solid #d9e2ec; border-radius: 8px; padding: 16px; }}
    .card strong {{ display: block; font-size: 30px; color: #0f766e; margin-bottom: 5px; }}
    .card span {{ color: #4b5563; font-size: 13px; }}
    .table-wrap {{ overflow-x: auto; background: #fff; border: 1px solid #d9e2ec; border-radius: 8px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ padding: 9px 11px; border-bottom: 1px solid #e5e7eb; text-align: left; white-space: nowrap; }}
    th {{ background: #f9fafb; }}
    .methodology {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; margin: 22px 0 26px; }}
    .method {{ background: #fff; border: 1px solid #d9e2ec; border-radius: 8px; padding: 16px; }}
    .method h3 {{ margin: 0 0 8px; font-size: 16px; }}
    .method p {{ margin: 7px 0; color: #374151; line-height: 1.45; }}
    .formula {{ display: block; margin-top: 8px; padding: 8px 10px; border-radius: 6px; background: #f3f4f6; color: #111827; font-family: Consolas, monospace; font-size: 13px; white-space: normal; }}
    .cases {{ display: grid; gap: 14px; }}
    .case {{ background: #fff; border: 1px solid #d9e2ec; border-radius: 8px; padding: 16px; }}
    .case h3 {{ margin: 0 0 7px; font-size: 17px; }}
    .case .meta {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }}
    .tag {{ display: inline-flex; padding: 3px 8px; border-radius: 6px; background: #eef2ff; color: #312e81; font-size: 12px; font-weight: 700; }}
    .tag.ok {{ background: #ecfdf5; color: #065f46; }}
    .tag.warn {{ background: #fff7ed; color: #9a3412; }}
    .tag.bad {{ background: #fef2f2; color: #991b1b; }}
    .columns {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1.1fr); gap: 14px; margin-top: 12px; }}
    .answer, .expected, .chunks {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; background: #f9fafb; }}
    .answer p, .expected p {{ white-space: pre-wrap; }}
    .chunk {{ margin: 0 0 10px; padding-bottom: 10px; border-bottom: 1px solid #e5e7eb; }}
    .chunk:last-child {{ margin-bottom: 0; padding-bottom: 0; border-bottom: 0; }}
    .chunk strong {{ display: block; margin-bottom: 4px; }}
    .chunk p {{ margin: 5px 0; white-space: pre-wrap; }}
    @media (max-width: 980px) {{ .columns {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <h1>Avaliacao RAG - 4 metricas</h1>
    <p class="lead">DeepSeek com RAG avaliado em duas etapas: recuperacao dos trechos e geracao da resposta.</p>
    <section class="cards">{cards}</section>
    <h2>Como o teste e calculado</h2>
    {methodology}
    <h2>Resumo por categoria</h2>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Categoria</th><th>Casos</th><th>Hit@5</th><th>Precision@5</th><th>Correctness</th><th>Faithfulness</th><th>OK</th><th>Recuperacao</th><th>Geracao</th><th>Ambas</th></tr></thead>
        <tbody>{category_rows}</tbody>
      </table>
    </div>
    <h2>Casos avaliados</h2>
    <section class="cases">{case_panels}</section>
  </main>
</body>
</html>
"""
    path.write_text(page, encoding="utf-8")


def _methodology_section() -> str:
    blocks = [
        (
            "Fluxo do teste",
            "Cada pergunta do gabarito e enviada ao TitasBot usando DeepSeek com RAG. O sistema salva a resposta final e os cinco primeiros trechos recuperados, mantendo fonte, pagina e score interno do recuperador.",
            "Entrada: pergunta oficial + gabarito + evidencias anotadas",
        ),
        (
            "Hit@5",
            "Verifica se pelo menos um dos cinco primeiros trechos contem evidencia suficiente para responder a pergunta. A suficiencia e definida pelas evidencias anotadas em rag_stage_eval_cases.json.",
            "Hit@5 = 1 se existe chunk suficiente no top 5; senao 0",
        ),
        (
            "Precision@5",
            "Mede quantos dos cinco primeiros trechos recuperados sao relevantes. Um trecho e relevante quando contem a quantidade minima de termos de evidencia configurada para aquele caso.",
            "Precision@5 = chunks relevantes no top 5 / 5",
        ),
        (
            "Answer Correctness",
            "Avalia a resposta final contra a resposta do gabarito usando DeepEval. O criterio penaliza fatos ausentes, anos errados, listas incompletas, classificacoes erradas e informacoes inventadas.",
            "Aprovado quando score >= threshold do caso (padrao 0.55)",
        ),
        (
            "Faithfulness",
            "Avalia se a resposta final foi fiel ao contexto recuperado. A pergunta aqui nao e se o gabarito foi coberto, mas se a resposta contradiz ou inventa algo alem dos trechos fornecidos.",
            "Aprovado quando score >= threshold do caso (padrao 0.70)",
        ),
        (
            "Diagnostico",
            "Combina as etapas para apontar onde ocorreu o problema: recuperacao, geracao, ambas, ou nenhum erro. Isso separa casos em que o contexto veio ruim de casos em que o contexto estava bom mas a resposta falhou.",
            "ok | retrieval_error | generation_error | both_error",
        ),
    ]
    return '<section class="methodology">' + "".join(
        f"""
        <article class="method">
          <h3>{html.escape(title)}</h3>
          <p>{html.escape(description)}</p>
          <code class="formula">{html.escape(formula)}</code>
        </article>
        """
        for title, description, formula in blocks
    ) + "</section>"


def _evaluate_chunk(case: RagStageEvalCase, chunk: RetrievedChunk, rank: int) -> RetrievedChunkEval:
    matched_terms = [term for term in case.evidence_terms if _contains_phrase(chunk.content, term)]
    relevant = len(matched_terms) >= case.min_terms_for_relevant_chunk
    sufficient = len(matched_terms) >= case.min_terms_for_sufficient_chunk
    return RetrievedChunkEval(
        rank=rank,
        source=chunk.source,
        page=chunk.page,
        vector_score=round(float(chunk.vector_score), 6),
        lexical_score=round(float(chunk.lexical_score), 6),
        final_score=round(float(chunk.final_score), 6),
        matched_terms=matched_terms,
        relevant=relevant,
        sufficient=sufficient,
        content_preview=_preview(chunk.content),
    )


def _contains_phrase(text: str, phrase: str) -> bool:
    return _norm_phrase(phrase) in _norm_phrase(text)


def _norm_phrase(text: str) -> str:
    text = (text or "").replace("º", "").replace("°", "")
    text = normalize_text(text or "")
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _preview(text: str, limit: int = 520) -> str:
    clean = re.sub(r"\s+", " ", text or "").strip()
    return clean[: limit - 3] + "..." if len(clean) > limit else clean


def _avg(values: Sequence[float]) -> float | None:
    clean = [float(value) for value in values if value is not None]
    return round(sum(clean) / len(clean), 6) if clean else None


def _write_csv(path: Path, results: Sequence[RagStageResult]) -> None:
    fieldnames = [
        "case_id",
        "number",
        "category",
        "hit_at_5",
        "precision_at_5",
        "answer_correctness",
        "faithfulness",
        "diagnosis",
        "question",
        "expected_output",
        "answer",
        "retrieval_query",
        "chunks",
        "error",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "case_id": result.case_id,
                    "number": result.number,
                    "category": result.category,
                    "hit_at_5": _fmt_number(result.retrieval.hit_at_5),
                    "precision_at_5": _fmt_number(result.retrieval.precision_at_5),
                    "answer_correctness": _fmt_number(result.correctness.score),
                    "faithfulness": _fmt_number(result.faithfulness.score),
                    "diagnosis": result.diagnosis,
                    "question": result.question,
                    "expected_output": result.expected_output,
                    "answer": result.answer,
                    "retrieval_query": result.retrieval_query,
                    "chunks": json.dumps([asdict(chunk) for chunk in result.retrieval.chunks], ensure_ascii=False),
                    "error": result.error or result.correctness.error or result.faithfulness.error,
                }
            )


def _case_panel(result: RagStageResult) -> str:
    diagnosis_class = {
        "ok": "ok",
        "retrieval_error": "bad",
        "generation_error": "warn",
        "both_error": "bad",
    }.get(result.diagnosis, "warn")
    chunks = "".join(_chunk_block(chunk) for chunk in result.retrieval.chunks)
    return f"""
    <article class="case">
      <h3>#{result.number} {html.escape(result.category)} - {html.escape(result.case_id)}</h3>
      <p>{html.escape(result.question)}</p>
      <div class="meta">
        <span class="tag {diagnosis_class}">{html.escape(result.diagnosis)}</span>
        <span class="tag">Hit@5: {_fmt_percent(result.retrieval.hit_at_5)}</span>
        <span class="tag">Precision@5: {_fmt_percent(result.retrieval.precision_at_5)}</span>
        <span class="tag">Correctness: {_fmt_percent(result.correctness.score)}</span>
        <span class="tag">Faithfulness: {_fmt_percent(result.faithfulness.score)}</span>
      </div>
      <div class="columns">
        <div class="answer">
          <strong>Resposta gerada</strong>
          <p>{html.escape(result.answer)}</p>
        </div>
        <div class="expected">
          <strong>Resposta do gabarito</strong>
          <p>{html.escape(result.expected_output)}</p>
        </div>
        <div class="chunks">
          <strong>Top 5 trechos recuperados</strong>
          {chunks or '<p class="muted">Nenhum trecho recuperado.</p>'}
        </div>
      </div>
    </article>
    """


def _chunk_block(chunk: RetrievedChunkEval) -> str:
    label = chunk.source if chunk.page is None else f"{chunk.source} (pagina {chunk.page + 1})"
    status = "suficiente" if chunk.sufficient else "relevante" if chunk.relevant else "baixo sinal"
    cls = "ok" if chunk.sufficient else "warn" if chunk.relevant else "bad"
    terms = ", ".join(chunk.matched_terms) if chunk.matched_terms else "nenhum termo anotado"
    return f"""
    <div class="chunk">
      <strong>#{chunk.rank} {html.escape(label)} | score {chunk.final_score:.3f}</strong>
      <span class="tag {cls}">{status}</span>
      <p><em>Termos:</em> {html.escape(terms)}</p>
      <p>{html.escape(chunk.content_preview)}</p>
    </div>
    """


def _card(label: str, value: str, note: str) -> str:
    return f'<article class="card"><strong>{html.escape(value)}</strong><span>{html.escape(label)} - {html.escape(note)}</span></article>'


def _fmt_percent(value: Any) -> str:
    if value is None:
        return ""
    return f"{float(value) * 100:.1f}%"


def _fmt_number(value: float | None) -> str:
    return "" if value is None else f"{value:.4f}"
