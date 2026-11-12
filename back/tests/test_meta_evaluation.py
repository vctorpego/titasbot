import pytest

from app.evaluation.meta_evaluation import (
    EvalRow,
    best_threshold_row,
    calibrate,
    classification_metrics,
    cross_validated_evaluation,
    evaluate_metric,
    rank_metrics,
    roc_auc,
    stability,
    system_ranking_agreement,
    threshold_sweep,
)


def _row(i, truth, score, stratum="fato_curto", model="m1", condition="rag", metric="x"):
    return EvalRow(
        answer_key=f"{model}|{condition}|q{i}",
        model=model,
        condition=condition,
        case_id=f"q{i}",
        stratum=stratum,
        truth=truth,
        coverage=float(truth),
        scores={metric: score},
    )


def test_classification_metrics_uses_correct_as_positive_class():
    m = classification_metrics([1, 1, 0, 0], [0.9, 0.2, 0.8, 0.1], 0.5)
    assert (m["tp"], m["fn"], m["fp"], m["tn"]) == (1, 1, 1, 1)
    assert m["precision_correta"] == 0.5 and m["recall_correta"] == 0.5
    assert m["accuracy"] == 0.5 and m["balanced_accuracy"] == 0.5


def test_threshold_is_inclusive():
    assert classification_metrics([1], [0.5], 0.5)["tp"] == 1


def test_auc_perfect_inverted_and_random():
    assert roc_auc([1, 1, 0, 0], [0.9, 0.8, 0.2, 0.1]) == 1.0
    assert roc_auc([1, 1, 0, 0], [0.1, 0.2, 0.8, 0.9]) == 0.0
    assert roc_auc([1, 0], [0.5, 0.5]) == 0.5
    assert roc_auc([1, 1], [0.5, 0.4]) is None


def test_best_threshold_prefers_criterion_then_closest_to_half():
    rows = threshold_sweep([1, 1, 0, 0], [0.9, 0.8, 0.2, 0.1])
    best = best_threshold_row(rows, "balanced_accuracy")
    assert best["balanced_accuracy"] == 1.0
    assert best["threshold"] == 0.5


def test_stratified_thresholds_adapt_to_each_stratum():
    rows = []
    # fato curto: corretas ~0.9, incorretas ~0.6  -> threshold alto
    for i in range(8):
        rows.append(_row(i, 1, 0.9, "fato_curto"))
        rows.append(_row(100 + i, 0, 0.6, "fato_curto"))
    # lista longa: corretas ~0.4, incorretas ~0.1 -> threshold baixo
    for i in range(8):
        rows.append(_row(200 + i, 1, 0.4, "lista_longa"))
        rows.append(_row(300 + i, 0, 0.1, "lista_longa"))
    calibration = calibrate(rows, "x")
    assert calibration["by_stratum"]["fato_curto"] > 0.6
    assert calibration["by_stratum"]["lista_longa"] <= 0.4
    summary = evaluate_metric(rows, "x")
    assert summary["in_sample"]["stratified"]["balanced_accuracy"] == 1.0
    assert summary["in_sample"]["global"]["balanced_accuracy"] < 1.0


def test_cross_validation_leave_one_model_out():
    rows = []
    for model in ("m1", "m2", "m3"):
        for i in range(6):
            rows.append(_row(i, 1, 0.8, model=model))
            rows.append(_row(50 + i, 0, 0.3, model=model))
    cv = cross_validated_evaluation(rows, "x")
    assert cv["scheme"] == "leave-one-model-out"
    assert cv["global"]["n"] == len(rows)
    assert cv["global"]["balanced_accuracy"] == 1.0


def test_cross_validation_falls_back_to_question_folds():
    rows = [_row(i, i % 2, 0.9 if i % 2 else 0.1) for i in range(20)]
    cv = cross_validated_evaluation(rows, "x")
    assert cv["scheme"].endswith("por pergunta")
    assert cv["stratified"]["accuracy"] == 1.0


def test_rows_without_score_are_ignored():
    rows = [_row(1, 1, 0.9), _row(2, 0, 0.1), EvalRow("k", "m1", "rag", "q9", "fato_curto", 1, 1.0, {"x": None})]
    assert evaluate_metric(rows, "x")["n"] == 2


def test_system_ranking_agreement():
    rows = []
    for system_idx, (model, rate) in enumerate((("a", 0.2), ("b", 0.5), ("c", 0.9))):
        for i in range(10):
            truth = 1 if i < rate * 10 else 0
            rows.append(_row(i, truth, rate, model=model))
    result = system_ranking_agreement(rows, "x")
    assert result["kendall_tau"] == pytest.approx(1.0)


def test_stability_and_ranking():
    assert stability({"a": [0.5, 0.5], "b": [0.2, 0.6]})["amplitude_maxima"] == pytest.approx(0.4)
    good = {"metric": "good", "auc": 0.9, "validacao_cruzada": {"global": {"balanced_accuracy": 0.9}, "stratified": {"balanced_accuracy": 0.95}}}
    bad = {"metric": "bad", "auc": 0.6, "validacao_cruzada": {"global": {"balanced_accuracy": 0.6}, "stratified": None}}
    ranked = rank_metrics([bad, good])
    assert [r["metric"] for r in ranked] == ["good", "bad"]
    assert ranked[0]["posicao"] == 1
