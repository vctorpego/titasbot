from __future__ import annotations

import re
from dataclasses import dataclass
from hashlib import md5
from pathlib import PurePosixPath
from typing import Iterable

from app.domain.constants import INSUFFICIENT_MSG, TEAM_ANCHORS
from app.domain.intents import (
    is_participation_question,
    is_projects_question,
    is_student_list_question,
    is_year_sensitive_question,
    question_is_about_team,
)
from app.infrastructure.retrieval import RetrievedChunk
from app.infrastructure.text_utils import normalize_text


@dataclass
class AuditResult:
    status: str
    answer: str
    used_ids: list[int]


def build_context(chunks: list[RetrievedChunk]) -> str:
    blocks = [f"[{i}] {c.source_label}\n{c.content}" for i, c in enumerate(chunks, start=1)]
    return "\n\n---\n\n".join(blocks)


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[\.\!\?\n])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def build_history(previous_question: str | None, previous_answer: str | None) -> str:
    if not previous_question or not previous_answer:
        return "Sem histórico relevante."
    short_answer = re.sub(r"\s+", " ", previous_answer.split("Fontes usadas:")[0]).strip()[:280]
    return f"Pergunta anterior: {previous_question}\nResumo da resposta anterior: {short_answer}"


def chunk_key(chunk: RetrievedChunk) -> str:
    payload = f"{chunk.source}|{chunk.page}|{chunk.content[:400]}".encode("utf-8", errors="ignore")
    return md5(payload).hexdigest()


def parse_ids(text: str, limit: int) -> list[int]:
    ids: list[int] = []
    for n in re.findall(r"\b\d+\b", text):
        i = int(n)
        if 1 <= i <= limit and i not in ids:
            ids.append(i)
    return ids


def clean_answer(answer: str) -> str:
    clean = re.sub(r"\n?Fontes usadas:.*$", "", answer, flags=re.IGNORECASE | re.DOTALL).strip()
    return clean or INSUFFICIENT_MSG


_UNCHANGED_MARKERS = {"", "=", "(=)", "igual", "(igual)", "mantida", "(mantida)", "ok"}


def is_unchanged_marker(text: str) -> bool:
    """O auditor sinaliza "mantenha a resposta como esta" com "="."""
    return normalize_text(text or "").strip(" .\"'`") in _UNCHANGED_MARKERS


def is_insufficient(text: str) -> bool:
    """Compara com INSUFFICIENT_MSG ignorando acentuacao/caixa.

    O modelo pode devolver a mensagem padrao com ou sem acentos; a comparacao
    precisa reconhecer as duas formas para que os fallbacks continuem valendo.
    """
    return normalize_text(text or "") == normalize_text(INSUFFICIENT_MSG)


def has_min_evidence(chunks: list[RetrievedChunk]) -> bool:
    if not chunks:
        return False
    return any(c.final_score >= 0.16 for c in chunks[:6])


def dedupe_keep_order(items: list[str]) -> list[str]:
    seen = set()
    out: list[str] = []
    for item in items:
        k = normalize_text(item)
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(item)
    return out


def chunk_mentions_team(chunk: RetrievedChunk) -> bool:
    text = normalize_text(chunk.content)
    return any(a in text for a in TEAM_ANCHORS)


def filter_team_relevant_chunks(
    question: str,
    chunks: list[RetrievedChunk],
    max_chunks_for_context: int,
    min_chunks: int,
    student_list_max_chunks: int,
) -> list[RetrievedChunk]:
    if not chunks or not question_is_about_team(question):
        return chunks

    strong = [c for c in chunks if chunk_mentions_team(c)]
    if len(strong) >= min_chunks:
        strong.sort(key=lambda x: x.final_score, reverse=True)
        cap = student_list_max_chunks if is_student_list_question(question) else max(max_chunks_for_context * 2, 12)
        return strong[:cap]
    return chunks


def normalize_sources(answer: str, chunks: list[RetrievedChunk], used_ids: list[int] | None = None) -> str:
    clean = re.sub(r"\n?Fontes usadas:.*$", "", answer, flags=re.IGNORECASE | re.DOTALL).strip()
    if not clean:
        clean = INSUFFICIENT_MSG
    return clean


def source_file_name(source: str) -> str:
    """Nome do arquivo, venha o caminho do Windows ou do Linux.

    O indice vetorial guarda o caminho absoluto de onde foi gerado. Um
    indice criado no Windows e lido dentro do container Linux nao seria
    cortado por Path().name, que ali nao reconhece a barra invertida como
    separador: a fonte apareceria como o caminho inteiro.
    """
    cleaned = source.replace("\\", "/").rstrip("/")
    return PurePosixPath(cleaned).name or source


def summarize_sources(chunks: list[RetrievedChunk]) -> list[str]:
    sources: list[str] = []
    seen = set()
    for chunk in chunks:
        source_name = source_file_name(chunk.source)
        label = source_name
        if chunk.page is not None:
            label = f"{source_name} (página {chunk.page + 1})"
        key = normalize_text(label)
        if key in seen:
            continue
        seen.add(key)
        sources.append(label)
    return sources


def answer_targets_question(question: str, answer: str) -> bool:
    ans = normalize_text(answer)
    if INSUFFICIENT_MSG in ans:
        return True
    q = normalize_text(question)
    if is_student_list_question(question):
        return ("- " in answer and answer.count("\n") >= 2) or (answer.count(",") >= 4)
    if is_participation_question(question):
        return any(k in ans for k in ("particip", "selec", "inscri", "estudante", "ingress"))
    if is_projects_question(question):
        competition_only = any(k in ans for k in ("obr", "cbr", "robocup", "larc", "podio", "classifica")) and "projeto" not in ans
        return not competition_only
    if is_year_sensitive_question(question):
        return bool(re.search(r"\b(?:19|20)\d{2}\b", answer))
    if "qual foi o primeiro nome" in q or ("primeiro nome" in q):
        return any(k in ans for k in ("asimov", "titas"))
    if any(k in q for k in ("quem", "quais", "liste", "listar", "nomes")):
        return ("- " in answer) or (answer.count(",") >= 2) or ("\n1." in answer)
    return True
