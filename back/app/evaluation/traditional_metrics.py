from __future__ import annotations

"""Metricas TRADICIONAIS (sem LLM), todas comparando resposta x gabarito.

Todas devolvem um score em [0, 1] (maior = mais parecido com o gabarito), para
poderem ser tratadas como classificadores com o mesmo sweep de thresholds.

Lexicais (sobreposicao de palavras/caracteres):
- exact_match:  1 se resposta e gabarito sao iguais apos normalizacao.
- token_f1:     F1 de tokens (estilo SQuAD).
- bleu:         BLEU-4 com suavizacao (nltk).
- chrf:         chrF, n-gramas de caractere (nltk) -- robusto a flexao do portugues.
- rouge1/rouge2/rougeL: F-measure (rouge-score, tokenizador Unicode).
- meteor:       METEOR (nltk; precisa do corpus wordnet -- sinonimos sao do
                ingles, entao em portugues ele funciona quase como F-mean com ordem).

Semanticas (embeddings):
- cosine_minilm: cosseno MiniLM multilingue (mesmo modelo do projeto de referencia).
- bertscore_f1:  BERTScore F1 com modelo multilingue (opcional: pacote bert-score).

Replica do projeto de referencia:
- ref_projeto:   0.8 * cosseno + 0.2 * difflib.SequenceMatcher (exatamente a
                 formula do Visualizador-do-avaliador), para comparacao direta.
"""

import logging
import os
import re
import time
from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any, Callable

from app.infrastructure.text_utils import normalize_text

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class MetricInfo:
    name: str
    family: str  # "tradicional" | "llm"
    kind: str  # "lexica" | "semantica" | "referencia" | "juiz"
    description: str


TRADITIONAL_METRICS: dict[str, MetricInfo] = {
    info.name: info
    for info in [
        MetricInfo("exact_match", "tradicional", "lexica", "Igualdade exata apos normalizacao"),
        MetricInfo("token_f1", "tradicional", "lexica", "F1 de tokens (SQuAD)"),
        MetricInfo("bleu", "tradicional", "lexica", "BLEU-4 suavizado"),
        MetricInfo("chrf", "tradicional", "lexica", "chrF (n-gramas de caractere)"),
        MetricInfo("rouge1", "tradicional", "lexica", "ROUGE-1 F"),
        MetricInfo("rouge2", "tradicional", "lexica", "ROUGE-2 F"),
        MetricInfo("rougeL", "tradicional", "lexica", "ROUGE-L F"),
        MetricInfo("meteor", "tradicional", "lexica", "METEOR (nltk)"),
        MetricInfo("cosine_minilm", "tradicional", "semantica", "Cosseno MiniLM multilingue"),
        MetricInfo("bertscore_f1", "tradicional", "semantica", "BERTScore F1 multilingue"),
        MetricInfo("ref_projeto", "tradicional", "referencia", "0.8 cosseno + 0.2 SequenceMatcher (projeto de referencia)"),
    ]
}

SEMANTIC_METRICS = {"cosine_minilm", "bertscore_f1", "ref_projeto"}


def _tokens(text: str) -> list[str]:
    return re.findall(r"\w+", normalize_text(text or ""))


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def exact_match(expected: str, answer: str) -> float:
    return 1.0 if _tokens(expected) == _tokens(answer) else 0.0


def token_f1(expected: str, answer: str) -> float:
    exp, ans = _tokens(expected), _tokens(answer)
    if not exp and not ans:
        return 1.0
    common = sum((Counter(exp) & Counter(ans)).values())
    if common == 0:
        return 0.0
    precision = common / len(ans)
    recall = common / len(exp)
    return 2 * precision * recall / (precision + recall)


def bleu(expected: str, answer: str) -> float:
    from nltk.translate.bleu_score import SmoothingFunction, sentence_bleu

    exp, ans = _tokens(expected), _tokens(answer)
    if not exp or not ans:
        return 0.0
    return _clamp(sentence_bleu([exp], ans, smoothing_function=SmoothingFunction().method1))


def chrf(expected: str, answer: str) -> float:
    from nltk.translate.chrf_score import sentence_chrf

    exp = " ".join(_tokens(expected))
    ans = " ".join(_tokens(answer))
    if not exp or not ans:
        return 0.0
    return _clamp(sentence_chrf(exp, ans))


@lru_cache(maxsize=1)
def _rouge_scorer() -> Any:
    from rouge_score import rouge_scorer

    from app.evaluation.reference_scorer import _WordTokenizer

    return rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=False, tokenizer=_WordTokenizer())


def rouge(expected: str, answer: str) -> dict[str, float]:
    scores = _rouge_scorer().score(expected or "", answer or "")
    return {name: float(scores[name].fmeasure) for name in ("rouge1", "rouge2", "rougeL")}


@lru_cache(maxsize=1)
def meteor_available() -> bool:
    try:
        from nltk.corpus import wordnet

        wordnet.ensure_loaded()
        return True
    except Exception:
        log.warning("METEOR indisponivel: rode `python -m nltk.downloader wordnet omw-1.4`.")
        return False


def meteor(expected: str, answer: str) -> float | None:
    if not meteor_available():
        return None
    from nltk.translate.meteor_score import meteor_score

    exp, ans = _tokens(expected), _tokens(answer)
    if not exp or not ans:
        return 0.0
    return _clamp(meteor_score([exp], ans))


def cosine_minilm(expected: str, answer: str) -> float:
    from app.evaluation.reference_scorer import semantic_score

    return _clamp(semantic_score(expected, answer))


def reference_project_score(expected: str, answer: str, cosine: float | None = None) -> float:
    """Formula literal do projeto de referencia: 0.8 cosseno + 0.2 SequenceMatcher."""
    sem = cosine_minilm(expected, answer) if cosine is None else cosine
    lex = SequenceMatcher(None, (expected or "").lower(), (answer or "").lower()).ratio()
    return _clamp(0.8 * sem + 0.2 * lex)


def bertscore_available() -> bool:
    import importlib.util

    return importlib.util.find_spec("bert_score") is not None


@lru_cache(maxsize=1)
def _bertscorer() -> Any:
    from bert_score import BERTScorer

    model_type = os.getenv("BERTSCORE_MODEL", "bert-base-multilingual-cased")
    return BERTScorer(model_type=model_type, lang="pt", rescale_with_baseline=False)


def bertscore_f1(expected: str, answer: str) -> float | None:
    if not bertscore_available():
        return None
    if not (expected or "").strip() or not (answer or "").strip():
        return 0.0
    _, _, f1 = _bertscorer().score([answer], [expected])
    return _clamp(f1.item())


def score_traditional(
    expected: str,
    answer: str,
    include_semantic: bool = True,
) -> dict[str, tuple[float | None, float]]:
    """Calcula todas as metricas tradicionais: {nome: (score, segundos)}."""
    results: dict[str, tuple[float | None, float]] = {}

    def timed(name: str, fn: Callable[[], float | None]) -> float | None:
        start = time.perf_counter()
        try:
            value = fn()
        except Exception as exc:  # uma metrica quebrada nao derruba as demais
            log.warning("metrica %s falhou: %s", name, exc)
            value = None
        results[name] = (None if value is None else round(float(value), 6), round(time.perf_counter() - start, 4))
        return value

    timed("exact_match", lambda: exact_match(expected, answer))
    timed("token_f1", lambda: token_f1(expected, answer))
    timed("bleu", lambda: bleu(expected, answer))
    timed("chrf", lambda: chrf(expected, answer))

    start = time.perf_counter()
    try:
        rouge_scores: dict[str, float | None] = dict(rouge(expected, answer))
    except Exception as exc:
        log.warning("ROUGE falhou: %s", exc)
        rouge_scores = {"rouge1": None, "rouge2": None, "rougeL": None}
    elapsed = round((time.perf_counter() - start) / 3, 4)
    for name, value in rouge_scores.items():
        results[name] = (None if value is None else round(value, 6), elapsed)

    timed("meteor", lambda: meteor(expected, answer))

    if include_semantic:
        cosine = timed("cosine_minilm", lambda: cosine_minilm(expected, answer))
        timed("bertscore_f1", lambda: bertscore_f1(expected, answer))
        start = time.perf_counter()
        try:
            ref = reference_project_score(expected, answer, cosine=cosine)
        except Exception as exc:
            log.warning("ref_projeto falhou: %s", exc)
            ref = None
        cosine_seconds = results["cosine_minilm"][1]
        results["ref_projeto"] = (
            None if ref is None else round(ref, 6),
            round(time.perf_counter() - start + cosine_seconds, 4),
        )
    return results
