from __future__ import annotations

"""Avaliador de referencia (metodologia do orientador / projeto de referencia).

    score_final = w_sem * similaridade_semantica + w_lex * similaridade_lexical
      - semantica: cosseno entre embeddings do modelo multilingue MiniLM
      - lexica:    ROUGE-L (F-measure) sobre as palavras do texto

Pesos padrao: 0.8 semantica / 0.2 lexica (iguais ao projeto de referencia; podem
ser ajustados por REF_SEMANTIC_WEIGHT / REF_LEXICAL_WEIGHT).

A dependencia `sentence-transformers` e pesada (puxa torch/transformers) e o
modelo (~470 MB) e baixado no primeiro uso. Por isso o carregamento e preguicoso
e existe `reference_scoring_available()` para o harness degradar com elegancia
quando as libs nao estiverem instaladas.
"""

import os
import re
from functools import lru_cache
from typing import Any

_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class _WordTokenizer:
    """Tokenizador Unicode-aware para o ROUGE-L.

    O tokenizador padrao do pacote `rouge_score` so reconhece `[a-z0-9]`,
    quebrando palavras acentuadas em portugues (ex.: "não" vira os
    tokens "n" e "o", "informação" vira "informa" e "o"). Aqui usamos
    `\\w+` (Unicode por padrao no Python 3), que preserva letras acentuadas
    como parte da palavra.
    """

    def tokenize(self, text: str) -> list[str]:
        return re.findall(r"\w+", (text or "").lower())


def reference_scoring_available() -> bool:
    """True se as dependencias do avaliador de referencia estiverem instaladas."""
    try:
        import importlib.util

        return (
            importlib.util.find_spec("sentence_transformers") is not None
            and importlib.util.find_spec("rouge_score") is not None
        )
    except Exception:
        return False


@lru_cache(maxsize=1)
def _get_model() -> Any:
    import logging

    try:
        from transformers import logging as hf_logging

        hf_logging.set_verbosity_error()
    except Exception:
        pass
    logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(_MODEL_NAME)


def _embed_long_text(text: str) -> Any:
    """Embedding de um texto de qualquer tamanho, sem perder conteudo.

    O MiniLM usado aqui tem `max_seq_length` de apenas 128 tokens: textos mais
    longos eram TRUNCADOS silenciosamente (ex.: o gabarito com os 191 estudantes
    tem ~1.164 tokens -- ~89% era descartado antes do cosseno). Aqui o texto e
    dividido em blocos de ate `max_seq_length` tokens; cada bloco e codificado e
    os vetores sao combinados por media ponderada pelo tamanho do bloco,
    devolvendo UM vetor por texto -- mesmo formato do calculo original.

    Textos curtos (a maioria) caem no caminho de bloco unico e o resultado e
    numericamente identico ao anterior.
    """
    import torch

    model = _get_model()
    tokenizer = model.tokenizer
    # add_special_tokens=False: os tokens especiais sao reinseridos pelo encode()
    # de cada bloco; conta-los aqui reduziria o tamanho util do bloco.
    token_ids = tokenizer.encode(text or "", add_special_tokens=False)
    limit = max(1, int(model.max_seq_length) - 2)  # -2 reserva [CLS] e [SEP]

    if len(token_ids) <= limit:
        return model.encode(text or "", convert_to_tensor=True, normalize_embeddings=True)

    blocks = [token_ids[i : i + limit] for i in range(0, len(token_ids), limit)]
    texts = [tokenizer.decode(b, skip_special_tokens=True) for b in blocks]
    embeddings = model.encode(texts, convert_to_tensor=True, normalize_embeddings=True)
    weights = torch.tensor(
        [float(len(b)) for b in blocks], dtype=embeddings.dtype, device=embeddings.device
    )
    pooled = (embeddings * weights.unsqueeze(1)).sum(dim=0) / weights.sum()
    return pooled / pooled.norm()


def semantic_score(expected: str, actual: str) -> float:
    """Similaridade semantica (cosseno) entre gabarito e resposta.

    Textos longos sao processados em blocos (ver `_embed_long_text`) para nao
    perder conteudo no limite de 128 tokens do modelo.
    """
    from sentence_transformers import util

    expected_embedding = _embed_long_text(expected or "")
    actual_embedding = _embed_long_text(actual or "")
    return float(util.cos_sim(expected_embedding, actual_embedding).item())


@lru_cache(maxsize=1)
def _get_rouge_scorer() -> Any:
    from rouge_score import rouge_scorer

    return rouge_scorer.RougeScorer(["rougeL"], use_stemmer=False, tokenizer=_WordTokenizer())


def lexical_score(expected: str, actual: str) -> float:
    """Similaridade lexical via ROUGE-L (F-measure), puro e deterministico.

    ROUGE-L mede a maior subsequencia comum (LCS) de PALAVRAS entre o gabarito
    e a resposta -- e o padrao usado na literatura de NLP para sobreposicao
    lexical (substitui o difflib.SequenceMatcher usado antes, que operava em
    nivel de caractere e nao e uma metrica reconhecida na area para isso).

    Diferencas de estilo tipografico (travessao "—" vs hifen "-", por exemplo)
    ja sao absorvidas pela tokenizacao por palavra -- pontuacao nao vira token,
    entao nao precisa de normalizacao especial como no metodo anterior.
    """
    exp = (expected or "").strip()
    act = (actual or "").strip()
    if not exp and not act:
        return 1.0
    scores = _get_rouge_scorer().score(exp, act)
    return float(scores["rougeL"].fmeasure)


def _weights() -> tuple[float, float]:
    w_sem = float(os.getenv("REF_SEMANTIC_WEIGHT", "0.8"))
    w_lex = float(os.getenv("REF_LEXICAL_WEIGHT", "0.2"))
    return w_sem, w_lex


def final_score(expected: str, actual: str) -> dict[str, float]:
    """Retorna {'semantic','lexical','final'}; 'final' combinado e clampado em [0,1]."""
    w_sem, w_lex = _weights()
    sem = semantic_score(expected, actual)
    lex = lexical_score(expected, actual)
    final = max(0.0, min(1.0, w_sem * sem + w_lex * lex))
    return {
        "semantic": round(sem, 6),
        "lexical": round(lex, 6),
        "final": round(final, 6),
    }
