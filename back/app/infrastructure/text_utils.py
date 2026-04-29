from __future__ import annotations

import re
import unicodedata
from typing import Iterable, List, Set


STOPWORDS_PT = {
    "a",
    "o",
    "as",
    "os",
    "de",
    "do",
    "da",
    "dos",
    "das",
    "e",
    "em",
    "no",
    "na",
    "nos",
    "nas",
    "um",
    "uma",
    "uns",
    "umas",
    "que",
    "para",
    "por",
    "com",
    "como",
    "qual",
    "quais",
    "quando",
    "onde",
    "sobre",
    "se",
    "ser",
    "sao",
    "foi",
    "mais",
}


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower().strip()


def extract_terms(text: str) -> List[str]:
    clean = normalize_text(text)
    tokens = re.findall(r"[a-z0-9]{2,}", clean)
    return [t for t in tokens if t not in STOPWORDS_PT]


def tokenize(text: str) -> Set[str]:
    return set(extract_terms(text))


def jaccard_score(a: Iterable[str], b: Iterable[str]) -> float:
    a_set = set(a)
    b_set = set(b)
    if not a_set or not b_set:
        return 0.0
    inter = len(a_set & b_set)
    union = len(a_set | b_set)
    return inter / union if union else 0.0
