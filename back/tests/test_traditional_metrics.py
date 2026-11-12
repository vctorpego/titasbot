from difflib import SequenceMatcher

import pytest

from app.evaluation import traditional_metrics as tm
from app.evaluation.llm_metrics import applicable_llm_metrics, eval_llm_config


def test_exact_match_ignores_case_accents_and_punctuation():
    assert tm.exact_match("O nome era Asimov.", "o nome era asimov") == 1.0
    assert tm.exact_match("Asimov", "Titãs") == 0.0


def test_token_f1():
    assert tm.token_f1("a b c d", "a b c d") == 1.0
    assert tm.token_f1("a b c d", "x y") == 0.0
    assert tm.token_f1("a b c d", "a b") == pytest.approx(2 * 1.0 * 0.5 / 1.5)


def test_bleu_and_chrf_are_bounded_and_ordered():
    ref = "A equipe competiu pela primeira vez em 2015 na LARC."
    assert tm.bleu(ref, ref) == pytest.approx(1.0)
    assert tm.chrf(ref, ref) == pytest.approx(1.0)
    close = "A equipe competiu pela primeira vez na LARC em 2015."
    far = "Não sei responder."
    assert tm.bleu(ref, close) > tm.bleu(ref, far)
    assert tm.chrf(ref, close) > tm.chrf(ref, far)
    assert tm.bleu(ref, "") == 0.0


def test_rouge_keeps_portuguese_words():
    scores = tm.rouge("informação não disponível", "informação não disponível")
    assert scores == {"rouge1": 1.0, "rouge2": 1.0, "rougeL": 1.0}


def test_reference_project_formula(monkeypatch):
    expected, answer = "Asimov", "asimov!"
    lex = SequenceMatcher(None, expected.lower(), answer.lower()).ratio()
    assert tm.reference_project_score(expected, answer, cosine=0.5) == pytest.approx(0.8 * 0.5 + 0.2 * lex)


def test_score_traditional_without_semantic_returns_all_lexical(monkeypatch):
    monkeypatch.setattr(tm, "meteor", lambda e, a: None)
    results = tm.score_traditional("a b c", "a b c", include_semantic=False)
    assert set(results) == {"exact_match", "token_f1", "bleu", "chrf", "rouge1", "rouge2", "rougeL", "meteor"}
    assert results["meteor"][0] is None
    assert results["token_f1"][0] == 1.0


def test_every_traditional_metric_is_registered():
    results_names = {"exact_match", "token_f1", "bleu", "chrf", "rouge1", "rouge2", "rougeL", "meteor",
                     "cosine_minilm", "bertscore_f1", "ref_projeto"}
    assert set(tm.TRADITIONAL_METRICS) == results_names


def test_deepeval_llm_defaults_to_gpt(monkeypatch):
    monkeypatch.delenv("DEEPEVAL_EVAL_PROVIDER", raising=False)
    monkeypatch.delenv("DEEPEVAL_EVAL_MODEL", raising=False)
    assert eval_llm_config() == ("openai", "gpt-5-nano")


def test_faithfulness_only_with_rag():
    assert "faithfulness" in applicable_llm_metrics("rag")
    assert "faithfulness" not in applicable_llm_metrics("no_rag")
