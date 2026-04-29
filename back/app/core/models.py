from __future__ import annotations

from dataclasses import dataclass

from app.infrastructure.retrieval import RetrievedChunk


@dataclass
class ChatResult:
    answer: str
    chunks: list[RetrievedChunk]
    retrieval_query: str

