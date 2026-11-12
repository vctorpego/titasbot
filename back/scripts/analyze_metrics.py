"""Etapa 3 do estudo de metricas: meta-avaliacao + relatorio.

Uso (em back/):
    .\\venv\\Scripts\\python.exe scripts\\analyze_metrics.py

Nao chama nenhuma API: le respostas.jsonl + scores.jsonl (+ rotulos_revisados.csv,
se existir) e gera em avaliacao_metricas/:
    analise_metricas.json, ranking_metricas.csv, metricas_por_threshold.csv,
    respostas_avaliadas.csv, comparacao_metricas.html, como_funciona.html

Env: META_CRITERION=balanced_accuracy | f1_correta | accuracy | f1_macro
     DEEPEVAL_EVAL_PROVIDER / DEEPEVAL_EVAL_MODEL (qual LLM de apoio do DeepEval analisar)
"""

from __future__ import annotations

import csv
import json
import os
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.evaluation import study_io  # noqa: E402
from app.evaluation.ground_truth import (  # noqa: E402
    ANSWER_TYPES,
    key_fact_coverage,
    load_label_overrides,
    truth_label,
)
from app.evaluation.llm_metrics import LLM_METRICS, eval_llm_config  # noqa: E402
from app.evaluation.meta_evaluation import (  # noqa: E402
    EvalRow,
    evaluate_metric,
    per_stratum_sweeps,
    rank_metrics,
    stability,
)
from app.evaluation.traditional_metrics import TRADITIONAL_METRICS  # noqa: E402

RETRIEVAL_METRICS = ("retrieval_hit_at_5", "retrieval_precision_at_5")


def _metric_info(name: str) -> dict[str, str]:
    info = TRADITIONAL_METRICS.get(name) or LLM_METRICS.get(name)
    if info is None:
        return {"family": "recuperacao", "kind": "recuperacao", "description": name}
    return {"family": info.family, "kind": info.kind, "description": info.description}


def build_dataset(eval_llm_label: str) -> dict[str, Any]:
    cases = {case.id: case for case in study_io.load_cases()}
    selected = {case.id for case in study_io.filter_cases(list(cases.values()))}
    answers = [
        a for a in study_io.latest_answers().values()
        if not a.get("error") and a["case_id"] in cases and a["case_id"] in selected
    ]
    overrides = load_label_overrides(study_io.OVERRIDES_PATH)

    # score principal por (resposta, metrica) + repeticoes das metricas DeepEval
    main_scores: dict[tuple[str, str], dict[str, Any]] = {}
    repeated: dict[str, dict[str, dict[int, float]]] = defaultdict(lambda: defaultdict(dict))
    cost_time: dict[str, dict[str, list[float]]] = defaultdict(lambda: {"seconds": [], "cost": []})
    for record in study_io.read_jsonl(study_io.SCORES_PATH):
        if record.get("family") == "llm" and record.get("eval_llm") != eval_llm_label:
            continue
        metric = record["metric"]
        key = record["answer_key"]
        if record.get("seconds") is not None:
            cost_time[metric]["seconds"].append(float(record["seconds"]))
        if record.get("cost") is not None:
            cost_time[metric]["cost"].append(float(record["cost"]))
        if record.get("score") is None:
            continue
        run = int(record.get("run", 0))
        if record.get("family") == "llm":
            repeated[metric][key][run] = float(record["score"])
        current = main_scores.get((key, metric))
        if current is None or run <= current["run"]:
            main_scores[(key, metric)] = {"run": run, "score": float(record["score"]), "reason": record.get("reason", "")}

    rows: list[EvalRow] = []
    answer_views: list[dict[str, Any]] = []
    for answer in sorted(answers, key=lambda a: (a["model_label"], a["condition"], a["number"])):
        case = cases[answer["case_id"]]
        coverage = key_fact_coverage(answer["answer"], case.key_facts)
        auto_label = truth_label(coverage.coverage, case.min_coverage)
        label = overrides.get(answer["answer_key"], auto_label)
        metric_names = sorted({m for (k, m) in main_scores if k == answer["answer_key"]})
        scores = {m: main_scores[(answer["answer_key"], m)]["score"] for m in metric_names}
        model_name = f"{answer['model_label']} ({answer['model']})"
        rows.append(
            EvalRow(
                answer_key=answer["answer_key"],
                model=model_name,
                condition=answer["condition"],
                case_id=case.id,
                stratum=case.answer_type,
                truth=label,
                coverage=coverage.coverage,
                scores={m: v for m, v in scores.items() if m not in RETRIEVAL_METRICS},
            )
        )
        answer_views.append(
            {
                "answer_key": answer["answer_key"],
                "model": model_name,
                "condition": answer["condition"],
                "case_id": case.id,
                "number": case.number,
                "category": case.category,
                "stratum": case.answer_type,
                "question": case.question,
                "expected": case.expected_output,
                "answer": answer["answer"],
                "coverage": coverage.coverage,
                "min_coverage": case.min_coverage,
                "found": coverage.found,
                "missing": coverage.missing,
                "truth": label,
                "truth_auto": auto_label,
                "truth_source": "revisado" if answer["answer_key"] in overrides else "fatos-chave",
                "scores": scores,
                "reasons": {
                    m: main_scores[(answer["answer_key"], m)]["reason"]
                    for m in metric_names
                    if main_scores[(answer["answer_key"], m)]["reason"]
                },
                "has_people_facts": any(f.kind == "name" for f in case.key_facts),
                "seconds_generation": answer.get("seconds"),
            }
        )

    repeated_lists = {
        metric: {key: [runs[r] for r in sorted(runs)] for key, runs in per_key.items()}
        for metric, per_key in repeated.items()
    }
    return {"rows": rows, "answers": answer_views, "repeated": repeated_lists, "cost_time": cost_time}


def analyze(dataset: dict[str, Any], criterion: str, eval_llm_label: str) -> dict[str, Any]:
    rows: list[EvalRow] = dataset["rows"]
    metric_names = sorted({m for r in rows for m in r.scores})
    summaries = []
    sweeps: dict[str, Any] = {}
    for metric in metric_names:
        summary = evaluate_metric(rows, metric, criterion)
        info = _metric_info(metric)
        times = dataset["cost_time"].get(metric, {"seconds": [], "cost": []})
        summary.update(info)
        summary["segundos_medios"] = statistics.fmean(times["seconds"]) if times["seconds"] else None
        summary["custo_total_usd"] = sum(times["cost"]) if times["cost"] else (0.0 if info["family"] == "tradicional" else None)
        summary["estabilidade"] = (
            stability(dataset["repeated"].get(metric, {})) if info["family"] == "llm" else {"desvio_padrao_medio": 0.0}
        )
        summaries.append(summary)
        sweeps[metric] = per_stratum_sweeps(rows, metric)

    ranking = rank_metrics(summaries, criterion)
    systems = _system_summary(rows, dataset["answers"])
    return {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "criterio": criterion,
        "llm_deepeval": eval_llm_label,
        "estratos": list(ANSWER_TYPES),
        "total_respostas": len(rows),
        "total_corretas": sum(r.truth for r in rows),
        "distribuicao_estratos": {
            s: {"respostas": sum(1 for r in rows if r.stratum == s), "corretas": sum(r.truth for r in rows if r.stratum == s)}
            for s in ANSWER_TYPES
        },
        "ranking": ranking,
        "sweeps": sweeps,
        "sistemas": systems,
        "recuperacao": _retrieval_summary(dataset["answers"]),
        "socio_tecnico": _socio_technical(ranking, dataset["answers"]),
        "answers": dataset["answers"],
    }


def _system_summary(rows: list[EvalRow], answers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_system: dict[str, list[EvalRow]] = defaultdict(list)
    for row in rows:
        by_system[row.system].append(row)
    metric_names = sorted({m for r in rows for m in r.scores})
    out = []
    for system, subset in sorted(by_system.items()):
        entry: dict[str, Any] = {
            "system": system,
            "respostas": len(subset),
            "taxa_correta_verdade": statistics.fmean(r.truth for r in subset),
            "cobertura_media": statistics.fmean(r.coverage for r in subset),
            "scores_medios": {},
        }
        for metric in metric_names:
            values = [r.scores[metric] for r in subset if r.scores.get(metric) is not None]
            entry["scores_medios"][metric] = statistics.fmean(values) if values else None
        out.append(entry)
    return out


def _retrieval_summary(answers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for answer in answers:
        if "retrieval_hit_at_5" in answer["scores"]:
            by_model[answer["model"]].append(answer)
    out = []
    for model, subset in sorted(by_model.items()):
        hits = [a for a in subset if a["scores"]["retrieval_hit_at_5"] >= 1]
        misses = [a for a in subset if a["scores"]["retrieval_hit_at_5"] < 1]
        out.append(
            {
                "model": model,
                "respostas_anotadas": len(subset),
                "hit_at_5": statistics.fmean(a["scores"]["retrieval_hit_at_5"] for a in subset),
                "precision_at_5": statistics.fmean(a["scores"]["retrieval_precision_at_5"] for a in subset),
                "taxa_correta_com_hit": statistics.fmean(a["truth"] for a in hits) if hits else None,
                "taxa_correta_sem_hit": statistics.fmean(a["truth"] for a in misses) if misses else None,
            }
        )
    return out


def _socio_technical(ranking: list[dict[str, Any]], answers: list[dict[str, Any]]) -> dict[str, Any]:
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for summary in ranking:
        by_family[summary["family"]].append(summary)

    def family_stats(items: list[dict[str, Any]]) -> dict[str, Any]:
        seconds = [s["segundos_medios"] for s in items if s["segundos_medios"] is not None]
        costs = [s["custo_total_usd"] for s in items if s["custo_total_usd"] is not None]
        stds = [s["estabilidade"].get("desvio_padrao_medio") for s in items if s["estabilidade"].get("desvio_padrao_medio") is not None]
        best = items[0] if items else None
        return {
            "metricas": len(items),
            "melhor_metrica": best["metric"] if best else None,
            "segundos_medios_por_resposta": statistics.fmean(seconds) if seconds else None,
            "custo_total_usd": sum(costs) if costs else None,
            "desvio_padrao_medio_entre_execucoes": statistics.fmean(stds) if stds else None,
        }

    people = [a for a in answers if a["has_people_facts"]]
    false_positive_people = []
    for summary in ranking:
        metric = summary["metric"]
        threshold = summary["threshold_global"]
        candidates = [a for a in people if a["scores"].get(metric) is not None and a["truth"] == 0]
        accepted = [a for a in candidates if a["scores"][metric] >= threshold]
        false_positive_people.append(
            {
                "metric": metric,
                "family": summary["family"],
                "respostas_incorretas_sobre_pessoas": len(candidates),
                "aprovadas_indevidamente": len(accepted),
                "taxa": (len(accepted) / len(candidates)) if candidates else None,
            }
        )

    rag_effect = defaultdict(dict)
    for answer in answers:
        rag_effect[answer["model"]].setdefault(answer["condition"], []).append(answer["truth"])
    return {
        "por_familia": {family: family_stats(items) for family, items in by_family.items()},
        "respostas_sobre_pessoas": len(people),
        "respostas_sobre_pessoas_incorretas": sum(1 for a in people if a["truth"] == 0),
        "aprovacao_indevida_sobre_pessoas": false_positive_people,
        "efeito_rag_na_verdade": {
            model: {cond: statistics.fmean(v) for cond, v in conds.items()} for model, conds in rag_effect.items()
        },
        "rotulos_revisados_por_humano": sum(1 for a in answers if a["truth_source"] == "revisado"),
        "rotulos_alterados_pela_revisao": sum(1 for a in answers if a["truth"] != a["truth_auto"]),
    }


# ---------------------------------------------------------------------------
# Escrita
# ---------------------------------------------------------------------------


def _br(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4f}".replace(".", ",")
    return str(value)


def write_csvs(output_dir: Path, analysis: dict[str, Any]) -> None:
    with (output_dir / "ranking_metricas.csv").open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.writer(fp, delimiter=";")
        writer.writerow([
            "posicao", "metrica", "familia", "tipo", "n", "auc", "spearman_cobertura",
            "bal_acc_global_cv", "bal_acc_estratificado_cv", "f1_correta_global_cv", "f1_correta_estratificado_cv",
            "threshold_global", "thresholds_por_estrato", "kendall_tau_sistemas",
            "segundos_medios", "custo_total_usd", "desvio_padrao_execucoes",
        ])
        for s in analysis["ranking"]:
            cv = s["validacao_cruzada"]
            writer.writerow([
                s["posicao"], s["metric"], s["family"], s["kind"], s["n"], _br(s["auc"]),
                _br(s["correlacao_cobertura"]["spearman"]),
                _br((cv["global"] or {}).get("balanced_accuracy")),
                _br((cv["stratified"] or {}).get("balanced_accuracy")),
                _br((cv["global"] or {}).get("f1_correta")),
                _br((cv["stratified"] or {}).get("f1_correta")),
                _br(s["threshold_global"]),
                " ".join(f"{k}={v:.2f}" for k, v in s["thresholds_por_estrato"].items()),
                _br(s["ranking_sistemas"]["kendall_tau"]),
                _br(s["segundos_medios"]), _br(s["custo_total_usd"]),
                _br(s["estabilidade"].get("desvio_padrao_medio")),
            ])

    columns = [
        "threshold", "n", "accuracy", "balanced_accuracy", "precision_correta", "recall_correta", "f1_correta",
        "precision_incorreta", "recall_incorreta", "f1_incorreta",
    ]
    with (output_dir / "metricas_por_threshold.csv").open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.writer(fp, delimiter=";")
        writer.writerow(["metrica", "estrato", *columns])
        for metric, per_stratum in analysis["sweeps"].items():
            for stratum, rows in per_stratum.items():
                for row in rows:
                    writer.writerow([metric, stratum, *[_br(float(row[c]) if c != "n" else row[c]) for c in columns]])

    metrics = [s["metric"] for s in analysis["ranking"]] + list(RETRIEVAL_METRICS)
    with (output_dir / "respostas_avaliadas.csv").open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.writer(fp, delimiter=";")
        writer.writerow([
            "answer_key", "modelo", "condicao", "numero", "estrato", "cobertura", "rotulo_verdade",
            "origem_rotulo", *metrics, "fatos_faltantes", "pergunta", "gabarito", "resposta",
        ])
        for a in analysis["answers"]:
            writer.writerow([
                a["answer_key"], a["model"], a["condition"], a["number"], a["stratum"], _br(a["coverage"]),
                a["truth"], a["truth_source"], *[_br(a["scores"].get(m)) for m in metrics],
                " | ".join(a["missing"]), a["question"], a["expected"], a["answer"],
            ])

    template = output_dir / "rotulos_revisados_modelo.csv"
    with template.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.writer(fp, delimiter=";")
        writer.writerow(["answer_key", "label", "rotulo_automatico", "cobertura", "pergunta"])
        for a in analysis["answers"]:
            writer.writerow([a["answer_key"], "", a["truth_auto"], _br(a["coverage"]), a["question"]])


def main() -> None:
    from app.evaluation.metric_comparison_report import write_html_reports
    from app.infrastructure.env import load_project_env

    load_project_env()
    criterion = os.getenv("META_CRITERION", "balanced_accuracy")
    provider, model = eval_llm_config()
    eval_llm_label = f"{provider}:{model}"

    dataset = build_dataset(eval_llm_label)
    if not dataset["rows"]:
        raise SystemExit("Sem respostas pontuadas. Rode generate_answers.py e score_answers.py antes.")
    analysis = analyze(dataset, criterion, eval_llm_label)

    output_dir = study_io.OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "analise_metricas.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_csvs(output_dir, analysis)
    write_html_reports(output_dir, analysis)

    print(f"Respostas analisadas: {analysis['total_respostas']} (corretas pela verdade: {analysis['total_corretas']})")
    print("Ranking das metricas (validacao cruzada, " + criterion + "):")
    for s in analysis["ranking"]:
        cv = s["validacao_cruzada"]
        strat = (cv["stratified"] or {}).get(criterion)
        glob = (cv["global"] or {}).get(criterion)
        auc = s["auc"]
        print(
            f"  {s['posicao']:>2}. {s['metric']:<20} [{s['family']}] "
            f"AUC={auc if auc is None else round(auc, 3)} global={glob and round(glob, 3)} estratificado={strat and round(strat, 3)}"
        )
    print(f"\nRelatorio: {output_dir / 'comparacao_metricas.html'}")


if __name__ == "__main__":
    main()
