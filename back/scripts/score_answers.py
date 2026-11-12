"""Etapa 2 do estudo de metricas: aplica as metricas tradicionais e as de LLM.

Uso (em back/):
    .\\venv\\Scripts\\python.exe scripts\\score_answers.py

Env:
    SCORE_GROUPS=traditional,retrieval,llm   grupos a calcular (padrao: todos)
    EVAL_DRY_RUN=1                           so conta quantas avaliacoes faltam
    EVAL_STABILITY_RUNS=3                    repeticoes das metricas DeepEval no subconjunto de estabilidade
    EVAL_STABILITY_CASE_IDS=q02,q07,...      perguntas repetidas para medir estabilidade
    DEEPEVAL_EVAL_PROVIDER / DEEPEVAL_EVAL_MODEL   LLM de apoio do DeepEval (padrao openai / gpt-5-nano)
    EVAL_LLM_MIN_INTERVAL_S=4                pausa entre chamadas (limite de requisicoes)
    EVAL_LLM_WORKERS=8                       chamadas DeepEval em paralelo (cada uma faz varias
                                              sub-chamadas internas ao LLM de apoio, sequenciais e
                                              lentas -- ~20-30s cada -- entao paralelizar entre
                                              respostas diferentes reduz bastante o tempo total)

Cache: scores.jsonl e append-only; pares (resposta, metrica, execucao, LLM de apoio) ja
calculados com sucesso sao pulados.
"""

from __future__ import annotations

import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_STABILITY_CASES = "q02,q07,q09,q21,q35,q36"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> None:
    from app.evaluation import study_io
    from app.evaluation.llm_metrics import applicable_llm_metrics, eval_llm_config, measure_llm_metric
    from app.evaluation.traditional_metrics import TRADITIONAL_METRICS, score_traditional
    from app.infrastructure.env import load_project_env
    from app.infrastructure.net_env import clear_broken_local_proxy

    clear_broken_local_proxy()
    load_project_env()

    groups = {g.strip() for g in os.getenv("SCORE_GROUPS", "traditional,retrieval,llm").split(",") if g.strip()}
    dry_run = os.getenv("EVAL_DRY_RUN") == "1"
    stability_runs = max(1, int(os.getenv("EVAL_STABILITY_RUNS", "3")))
    stability_prefixes = [
        p.strip() for p in os.getenv("EVAL_STABILITY_CASE_IDS", DEFAULT_STABILITY_CASES).split(",") if p.strip()
    ]
    context_chars = int(os.getenv("MODEL_EVAL_CONTEXT_CHARS", "1200"))
    llm_provider, llm_model = eval_llm_config()
    eval_llm_label = f"{llm_provider}:{llm_model}"

    cases = {case.id: case for case in study_io.load_cases()}
    selected_ids = {case.id for case in study_io.filter_cases(list(cases.values()))}
    answers = [
        a for a in study_io.latest_answers().values()
        if not a.get("error") and a["case_id"] in selected_ids
    ]
    if not answers:
        raise SystemExit("Nenhuma resposta valida. Rode scripts/generate_answers.py antes.")

    # Metrica tradicional "indisponivel" (ex.: METEOR sem wordnet) conta como feita,
    # para nao recalcular tudo a cada execucao; SCORE_RETRY_UNAVAILABLE=1 tenta de novo.
    retry_unavailable = os.getenv("SCORE_RETRY_UNAVAILABLE") == "1"
    done = {
        (s["answer_key"], s["metric"], int(s.get("run", 0)), s.get("eval_llm", ""))
        for s in study_io.read_jsonl(study_io.SCORES_PATH)
        if s.get("score") is not None or (s.get("error") == "indisponivel" and not retry_unavailable)
    }

    def pending(answer_key: str, metric: str, run: int = 0, eval_llm: str = "") -> bool:
        return (answer_key, metric, run, eval_llm) not in done

    # --- tradicionais -------------------------------------------------------
    if "traditional" in groups:
        todo = [a for a in answers if any(pending(a["answer_key"], m) for m in TRADITIONAL_METRICS)]
        print(f"Tradicionais: {len(todo)} resposta(s) pendente(s).")
        if not dry_run:
            for idx, answer in enumerate(todo, start=1):
                case = cases[answer["case_id"]]
                print(f"  [trad {idx}/{len(todo)}] {answer['answer_key']}")
                results = score_traditional(case.expected_output, answer["answer"])
                study_io.append_jsonl(
                    study_io.SCORES_PATH,
                    [
                        {
                            "answer_key": answer["answer_key"],
                            "metric": name,
                            "family": "tradicional",
                            "run": 0,
                            "eval_llm": "",
                            "score": score,
                            "seconds": seconds,
                            "cost": 0.0,
                            "reason": "",
                            "error": "" if score is not None else "indisponivel",
                            "scored_at": _now(),
                        }
                        for name, (score, seconds) in results.items()
                        if pending(answer["answer_key"], name)
                    ],
                )

    # --- recuperacao (so RAG, perguntas com anotacao de evidencias) ----------
    if "retrieval" in groups:
        from app.evaluation.rag_stage_scorer import load_stage_cases, score_retrieval
        from app.infrastructure.retrieval import RetrievedChunk

        stage_cases = {
            c.id: c for c in load_stage_cases(study_io.RAG_STAGE_ANNOTATIONS_PATH, study_io.OFFICIAL_CASES_PATH)
        }
        records = []
        for answer in answers:
            stage_case = stage_cases.get(answer["case_id"])
            if answer["condition"] != "rag" or stage_case is None:
                continue
            if not pending(answer["answer_key"], "retrieval_hit_at_5"):
                continue
            chunks = [RetrievedChunk(**chunk) for chunk in answer.get("chunks", [])]
            retrieval = score_retrieval(stage_case, chunks)
            for name, value in (
                ("retrieval_hit_at_5", retrieval.hit_at_5),
                ("retrieval_precision_at_5", retrieval.precision_at_5),
            ):
                records.append(
                    {
                        "answer_key": answer["answer_key"], "metric": name, "family": "recuperacao",
                        "run": 0, "eval_llm": "", "score": value, "seconds": 0.0, "cost": 0.0,
                        "reason": "", "error": "", "scored_at": _now(),
                    }
                )
        print(f"Recuperacao: {len(records) // 2} resposta(s) RAG anotada(s) pontuada(s).")
        if records and not dry_run:
            study_io.append_jsonl(study_io.SCORES_PATH, records)

    # --- metricas DeepEval (usam LLM) --------------------------------------------------------
    if "llm" in groups:
        jobs = []
        for answer in answers:
            runs = stability_runs if any(answer["case_id"].startswith(p) for p in stability_prefixes) else 1
            for metric in applicable_llm_metrics(answer["condition"]):
                # Faithfulness exige retrieval_context nao-vazio; quando o RAG nao recupera
                # nenhum chunk (ex.: o bot corretamente responde "nao encontrei informacao"),
                # a metrica simplesmente nao se aplica -- pular em vez de falhar.
                if metric == "faithfulness" and not answer.get("chunks"):
                    continue
                for run in range(runs):
                    if pending(answer["answer_key"], metric, run, eval_llm_label):
                        jobs.append((answer, metric, run))
        print(f"DeepEval ({eval_llm_label}): {len(jobs)} avaliacao(oes) pendente(s).")
        if not dry_run and jobs:
            # Cada chamada DeepEval faz varias sub-chamadas sequenciais ao LLM de apoio (~20-30s
            # no total) -- paralelizamos ENTRE respostas (nao dentro de uma mesma chamada) para
            # nao esperar isso 1092 vezes em serie. write_lock protege o append_jsonl (uma linha
            # por vez) e abort_event para cedo o pool se o credito/chave estiver invalido, sem
            # deixar centenas de erros identicos se acumularem.
            max_consecutive_errors = int(os.getenv("EVAL_MAX_CONSECUTIVE_ERRORS", "5"))
            workers = max(1, int(os.getenv("EVAL_LLM_WORKERS", "8")))
            write_lock = threading.Lock()
            abort_event = threading.Event()
            state = {"consecutive_errors": 0, "done": 0}

            def run_job(answer: dict, metric: str, run: int):
                case = cases[answer["case_id"]]
                context = [c["content"][:context_chars] for c in answer.get("chunks", [])[:5]]
                result = measure_llm_metric(metric, case.question, case.expected_output, answer["answer"], context)
                return answer, metric, run, result

            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {executor.submit(run_job, answer, metric, run): (answer, metric, run) for answer, metric, run in jobs}
                for future in as_completed(futures):
                    answer, metric, run = futures[future]
                    try:
                        answer, metric, run, result = future.result()
                    except Exception as exc:  # falha na propria thread (nao no measure_llm_metric)
                        from app.evaluation.llm_metrics import LLMMetricScore

                        result = LLMMetricScore(metric, None, 0.0, error=str(exc)[:600])

                    with write_lock:
                        state["done"] += 1
                        status = f"{result.score:.3f}" if result.score is not None else f"erro: {result.error[:120]}"
                        print(f"  [llm {state['done']}/{len(jobs)}] {answer['answer_key']} {metric} run={run} -> {status}")
                        study_io.append_jsonl(
                            study_io.SCORES_PATH,
                            [
                                {
                                    "answer_key": answer["answer_key"],
                                    "metric": metric,
                                    "family": "llm",
                                    "run": run,
                                    "eval_llm": eval_llm_label,
                                    "score": result.score,
                                    "seconds": result.seconds,
                                    "cost": result.cost,
                                    "reason": result.reason,
                                    "error": result.error,
                                    "scored_at": _now(),
                                }
                            ],
                        )
                        state["consecutive_errors"] = state["consecutive_errors"] + 1 if result.error else 0
                        if state["consecutive_errors"] >= max_consecutive_errors and not abort_event.is_set():
                            abort_event.set()
                            print(
                                f"\n{state['consecutive_errors']} erros seguidos no DeepEval ({eval_llm_label}); "
                                "cancelando o restante da fila (o que ja foi calculado fica em cache)."
                            )
                            for pending_future in futures:
                                pending_future.cancel()

            if abort_event.is_set():
                raise SystemExit(
                    f"Abortado por erros seguidos no DeepEval ({eval_llm_label}). Verifique credito/limite "
                    "da API do provedor e rode de novo (o cache retoma de onde parou)."
                )

    print(f"\nScores em: {study_io.SCORES_PATH}")


if __name__ == "__main__":
    main()
