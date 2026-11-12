from __future__ import annotations

"""Meta-avaliacao: quao bem cada METRICA concorda com a verdade do gabarito.

Cada metrica produz um score em [0, 1] por resposta. Tratando-a como
classificador ("score >= threshold => correta") medimos, contra o rotulo de
verdade (1 = correta, 0 = incorreta, ver ground_truth.py):

1. Independente de threshold
   - ROC-AUC: probabilidade de a metrica dar nota maior a uma resposta correta
     do que a uma incorreta (0.5 = acaso, 1.0 = separacao perfeita).
   - Spearman / Kendall entre o score e a cobertura de fatos-chave.
2. Threshold GLOBAL (como no projeto de referencia): varredura 0.00..1.00.
3. Threshold ESTRATIFICADO: um threshold por tipo de resposta
   (fato_curto, descritiva, lista_curta, lista_longa).
4. Validacao cruzada (fora da amostra): thresholds calibrados em parte dos dados
   e aplicados no restante -- leave-one-model-out quando ha >= 2 modelos, senao
   k-fold por pergunta. Evita que o threshold estratificado "decore" os dados.
5. Concordancia de ranking: a metrica ordena os sistemas (modelo x condicao) na
   mesma ordem que a verdade? (Kendall tau)
"""

import math
import statistics
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from app.evaluation.ground_truth import LABEL_CORRECT, LABEL_INCORRECT

THRESHOLDS = [round(0.05 * i, 2) for i in range(21)]
CRITERIA = ("balanced_accuracy", "f1_correta", "accuracy", "f1_macro")
MIN_STRATUM_ROWS = 6


@dataclass(frozen=True)
class EvalRow:
    answer_key: str
    model: str
    condition: str
    case_id: str
    stratum: str
    truth: int
    coverage: float
    scores: dict[str, float | None] = field(default_factory=dict)

    @property
    def system(self) -> str:
        return f"{self.model} | {self.condition}"


# ---------------------------------------------------------------------------
# Classificacao em um threshold
# ---------------------------------------------------------------------------


def classification_metrics(truth: Sequence[int], scores: Sequence[float], threshold: float) -> dict[str, float | int]:
    tp = fp = tn = fn = 0
    for label, score in zip(truth, scores):
        predicted_correct = score >= threshold - 1e-12
        if label == LABEL_CORRECT:
            tp += predicted_correct
            fn += not predicted_correct
        else:
            fp += predicted_correct
            tn += not predicted_correct
    n = tp + fp + tn + fn
    precision_c = _safe_div(tp, tp + fp)
    recall_c = _safe_div(tp, tp + fn)
    precision_i = _safe_div(tn, tn + fn)
    recall_i = _safe_div(tn, tn + fp)
    f1_c = _f1(precision_c, recall_c)
    f1_i = _f1(precision_i, recall_i)
    has_both = (tp + fn) > 0 and (tn + fp) > 0
    return {
        "threshold": threshold,
        "n": n,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "accuracy": _safe_div(tp + tn, n),
        "balanced_accuracy": (recall_c + recall_i) / 2 if has_both else _safe_div(tp + tn, n),
        "precision_correta": precision_c,
        "recall_correta": recall_c,
        "f1_correta": f1_c,
        "precision_incorreta": precision_i,
        "recall_incorreta": recall_i,
        "f1_incorreta": f1_i,
        "f1_macro": (f1_c + f1_i) / 2,
    }


def threshold_sweep(
    truth: Sequence[int],
    scores: Sequence[float],
    thresholds: Sequence[float] = THRESHOLDS,
) -> list[dict[str, float | int]]:
    return [classification_metrics(truth, scores, t) for t in thresholds]


def best_threshold_row(rows: Sequence[dict[str, Any]], criterion: str = "balanced_accuracy") -> dict[str, Any]:
    """Melhor linha pelo criterio; empate -> threshold mais proximo de 0.5."""
    if criterion not in CRITERIA:
        raise ValueError(f"criterio desconhecido: {criterion}")
    return max(rows, key=lambda row: (round(float(row[criterion]), 9), -abs(float(row["threshold"]) - 0.5)))


# ---------------------------------------------------------------------------
# Metricas independentes de threshold
# ---------------------------------------------------------------------------


def roc_auc(truth: Sequence[int], scores: Sequence[float]) -> float | None:
    """AUC via Mann-Whitney (empates contam 0.5). None se so ha uma classe."""
    positives = [s for t, s in zip(truth, scores) if t == LABEL_CORRECT]
    negatives = [s for t, s in zip(truth, scores) if t == LABEL_INCORRECT]
    if not positives or not negatives:
        return None
    wins = 0.0
    for p in positives:
        for q in negatives:
            wins += 1.0 if p > q else 0.5 if p == q else 0.0
    return wins / (len(positives) * len(negatives))


def correlations(scores: Sequence[float], reference: Sequence[float]) -> dict[str, float | None]:
    if len(scores) < 3 or len(set(scores)) < 2 or len(set(reference)) < 2:
        return {"spearman": None, "spearman_p": None, "kendall": None, "kendall_p": None}
    from scipy.stats import kendalltau, spearmanr

    sp = spearmanr(scores, reference)
    kd = kendalltau(scores, reference)
    return {
        "spearman": _finite(sp.statistic),
        "spearman_p": _finite(sp.pvalue),
        "kendall": _finite(kd.statistic),
        "kendall_p": _finite(kd.pvalue),
    }


# ---------------------------------------------------------------------------
# Thresholds global x estratificado
# ---------------------------------------------------------------------------


def rows_with_metric(rows: Sequence[EvalRow], metric: str) -> list[EvalRow]:
    return [row for row in rows if row.scores.get(metric) is not None]


def calibrate(rows: Sequence[EvalRow], metric: str, criterion: str = "balanced_accuracy") -> dict[str, Any]:
    """Threshold global e um threshold por estrato (fallback: global)."""
    usable = rows_with_metric(rows, metric)
    if not usable:
        return {"global": 0.5, "by_stratum": {}}
    global_row = best_threshold_row(
        threshold_sweep([r.truth for r in usable], [float(r.scores[metric]) for r in usable]), criterion
    )
    by_stratum: dict[str, float] = {}
    for stratum in sorted({r.stratum for r in usable}):
        subset = [r for r in usable if r.stratum == stratum]
        labels = {r.truth for r in subset}
        if len(subset) < MIN_STRATUM_ROWS or len(labels) < 2:
            by_stratum[stratum] = float(global_row["threshold"])
            continue
        best = best_threshold_row(
            threshold_sweep([r.truth for r in subset], [float(r.scores[metric]) for r in subset]), criterion
        )
        by_stratum[stratum] = float(best["threshold"])
    return {"global": float(global_row["threshold"]), "by_stratum": by_stratum}


def predict(row: EvalRow, metric: str, calibration: dict[str, Any], stratified: bool) -> int:
    threshold = calibration["global"]
    if stratified:
        threshold = calibration["by_stratum"].get(row.stratum, threshold)
    return LABEL_CORRECT if float(row.scores[metric]) >= threshold - 1e-12 else LABEL_INCORRECT


def _metrics_from_predictions(truth: Sequence[int], predicted: Sequence[int]) -> dict[str, float | int]:
    # Reaproveita classification_metrics tratando a predicao binaria como score.
    return classification_metrics(truth, [float(p) for p in predicted], 0.5)


def in_sample_evaluation(rows: Sequence[EvalRow], metric: str, criterion: str) -> dict[str, Any]:
    usable = rows_with_metric(rows, metric)
    calibration = calibrate(usable, metric, criterion)
    truth = [r.truth for r in usable]
    return {
        "calibration": calibration,
        "global": _metrics_from_predictions(truth, [predict(r, metric, calibration, False) for r in usable]),
        "stratified": _metrics_from_predictions(truth, [predict(r, metric, calibration, True) for r in usable]),
    }


def cross_validated_evaluation(
    rows: Sequence[EvalRow],
    metric: str,
    criterion: str = "balanced_accuracy",
    folds: int = 5,
) -> dict[str, Any]:
    usable = rows_with_metric(rows, metric)
    models = sorted({r.model for r in usable})
    if len(models) >= 2:
        scheme = "leave-one-model-out"
        group_of: Callable[[EvalRow], str] = lambda r: r.model
    else:
        scheme = f"{folds}-fold por pergunta"
        case_ids = sorted({r.case_id for r in usable})
        fold_of_case = {case_id: str(i % folds) for i, case_id in enumerate(case_ids)}
        group_of = lambda r: fold_of_case[r.case_id]

    truth: list[int] = []
    pred_global: list[int] = []
    pred_strat: list[int] = []
    for group in sorted({group_of(r) for r in usable}):
        train = [r for r in usable if group_of(r) != group]
        test = [r for r in usable if group_of(r) == group]
        if not train or not test:
            continue
        calibration = calibrate(train, metric, criterion)
        for row in test:
            truth.append(row.truth)
            pred_global.append(predict(row, metric, calibration, False))
            pred_strat.append(predict(row, metric, calibration, True))
    if not truth:
        return {"scheme": scheme, "global": None, "stratified": None}
    return {
        "scheme": scheme,
        "global": _metrics_from_predictions(truth, pred_global),
        "stratified": _metrics_from_predictions(truth, pred_strat),
    }


def per_stratum_sweeps(rows: Sequence[EvalRow], metric: str) -> dict[str, list[dict[str, Any]]]:
    usable = rows_with_metric(rows, metric)
    sweeps = {"global": threshold_sweep([r.truth for r in usable], [float(r.scores[metric]) for r in usable])}
    for stratum in sorted({r.stratum for r in usable}):
        subset = [r for r in usable if r.stratum == stratum]
        sweeps[stratum] = threshold_sweep([r.truth for r in subset], [float(r.scores[metric]) for r in subset])
    return sweeps


# ---------------------------------------------------------------------------
# Sistemas, estabilidade e resumo
# ---------------------------------------------------------------------------


def system_ranking_agreement(rows: Sequence[EvalRow], metric: str) -> dict[str, Any]:
    usable = rows_with_metric(rows, metric)
    systems = sorted({r.system for r in usable})
    truth_means = []
    score_means = []
    for system in systems:
        subset = [r for r in usable if r.system == system]
        truth_means.append(statistics.fmean(r.truth for r in subset))
        score_means.append(statistics.fmean(float(r.scores[metric]) for r in subset))
    tau = None
    if len(systems) >= 3 and len(set(truth_means)) > 1 and len(set(score_means)) > 1:
        from scipy.stats import kendalltau

        tau = _finite(kendalltau(score_means, truth_means).statistic)
    return {
        "kendall_tau": tau,
        "systems": [
            {"system": s, "taxa_correta_verdade": t, "score_medio": m}
            for s, t, m in zip(systems, truth_means, score_means)
        ],
    }


def stability(repeated_scores: dict[str, list[float]]) -> dict[str, float | None]:
    """Desvio-padrao medio entre execucoes repetidas da mesma avaliacao."""
    stds = [statistics.pstdev(values) for values in repeated_scores.values() if len(values) >= 2]
    ranges = [max(values) - min(values) for values in repeated_scores.values() if len(values) >= 2]
    return {
        "respostas_repetidas": len(stds),
        "desvio_padrao_medio": statistics.fmean(stds) if stds else None,
        "amplitude_media": statistics.fmean(ranges) if ranges else None,
        "amplitude_maxima": max(ranges) if ranges else None,
    }


def evaluate_metric(rows: Sequence[EvalRow], metric: str, criterion: str = "balanced_accuracy") -> dict[str, Any]:
    usable = rows_with_metric(rows, metric)
    truth = [r.truth for r in usable]
    scores = [float(r.scores[metric]) for r in usable]
    in_sample = in_sample_evaluation(usable, metric, criterion)
    cv = cross_validated_evaluation(usable, metric, criterion)
    auc_by_stratum = {
        stratum: roc_auc([r.truth for r in usable if r.stratum == stratum],
                         [float(r.scores[metric]) for r in usable if r.stratum == stratum])
        for stratum in sorted({r.stratum for r in usable})
    }
    return {
        "metric": metric,
        "n": len(usable),
        "positivos": sum(truth),
        "auc": roc_auc(truth, scores),
        "auc_por_estrato": auc_by_stratum,
        "correlacao_cobertura": correlations(scores, [r.coverage for r in usable]),
        "threshold_global": in_sample["calibration"]["global"],
        "thresholds_por_estrato": in_sample["calibration"]["by_stratum"],
        "in_sample": {"global": in_sample["global"], "stratified": in_sample["stratified"]},
        "validacao_cruzada": cv,
        "ranking_sistemas": system_ranking_agreement(usable, metric),
    }


def rank_metrics(summaries: Sequence[dict[str, Any]], criterion: str = "balanced_accuracy") -> list[dict[str, Any]]:
    """Ordena metricas pelo desempenho fora da amostra (estratificado), depois AUC."""

    def key(summary: dict[str, Any]) -> tuple[float, float]:
        cv = summary.get("validacao_cruzada") or {}
        strat = (cv.get("stratified") or {}).get(criterion)
        glob = (cv.get("global") or {}).get(criterion)
        best_cv = max(v for v in (strat, glob, -1.0) if v is not None)
        return (best_cv, summary.get("auc") if summary.get("auc") is not None else -1.0)

    ranked = sorted(summaries, key=key, reverse=True)
    return [{**summary, "posicao": idx} for idx, summary in enumerate(ranked, start=1)]


def _safe_div(num: float, den: float) -> float:
    return num / den if den else 0.0


def _f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0


def _finite(value: Any) -> float | None:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None
