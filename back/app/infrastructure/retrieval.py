from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import md5
from math import log
from typing import Dict, List, Tuple

from langchain_chroma.vectorstores import Chroma

from app.infrastructure.settings import Settings
from app.infrastructure.text_utils import extract_terms, tokenize


@dataclass
class RetrievedChunk:
    content: str
    source: str
    page: int | None
    doc_kind: str
    vector_score: float
    lexical_score: float
    final_score: float

    @property
    def source_label(self) -> str:
        if self.page is None:
            return self.source
        return f"{self.source} (pagina {self.page + 1})"


@dataclass
class _SparseDoc:
    content: str
    source: str
    page: int | None
    doc_kind: str
    tf: Counter
    length: int


def _doc_key(content: str, source: str, page: int | None) -> str:
    payload = f"{source}|{page}|{content[:400]}".encode("utf-8", errors="ignore")
    return md5(payload).hexdigest()


class HybridRetriever:
    """Retriever hibrido: similaridade vetorial + BM25 para termos exatos."""

    def __init__(self, vectorstore: Chroma, settings: Settings) -> None:
        self.vectorstore = vectorstore
        self.settings = settings
        self._sparse_docs: List[_SparseDoc] = []
        self._df: Dict[str, int] = {}
        self._avg_doc_len: float = 1.0
        self._index_ready = False

    def _build_sparse_index(self) -> None:
        if self._index_ready:
            return

        raw = self.vectorstore._collection.get(include=["documents", "metadatas"])
        documents = raw.get("documents") or []
        metadatas = raw.get("metadatas") or [{} for _ in documents]

        sparse_docs: List[_SparseDoc] = []
        df_counter: Dict[str, int] = {}
        total_len = 0

        for content, meta in zip(documents, metadatas):
            text = (content or "").strip()
            if not text:
                continue
            terms = extract_terms(text)
            tf = Counter(terms)
            doc_len = sum(tf.values()) or 1
            total_len += doc_len

            source = meta.get("source", "arquivo_desconhecido")
            page_raw = meta.get("page")
            page = page_raw if isinstance(page_raw, int) else None
            doc_kind = meta.get("doc_kind", "context")

            sparse_docs.append(
                _SparseDoc(
                    content=text,
                    source=source,
                    page=page,
                    doc_kind=doc_kind,
                    tf=tf,
                    length=doc_len,
                )
            )

            for term in tf:
                df_counter[term] = df_counter.get(term, 0) + 1

        self._sparse_docs = sparse_docs
        self._df = df_counter
        self._avg_doc_len = (total_len / len(sparse_docs)) if sparse_docs else 1.0
        self._index_ready = True

    def _bm25_hits(self, question: str, top_k: int) -> List[Tuple[_SparseDoc, float]]:
        self._build_sparse_index()
        q_terms = list(tokenize(question))
        if not q_terms or not self._sparse_docs:
            return []

        n_docs = len(self._sparse_docs)
        k1 = 1.5
        b = 0.75

        scored: List[Tuple[_SparseDoc, float]] = []
        for doc in self._sparse_docs:
            score = 0.0
            for term in q_terms:
                tf = doc.tf.get(term, 0)
                if tf == 0:
                    continue
                df = self._df.get(term, 0)
                idf = log(1 + (n_docs - df + 0.5) / (df + 0.5))
                denom = tf + k1 * (1 - b + b * (doc.length / self._avg_doc_len))
                score += idf * ((tf * (k1 + 1)) / denom)
            if score > 0:
                scored.append((doc, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def retrieve(self, question: str) -> List[RetrievedChunk]:
        try:
            vector_hits = self.vectorstore.similarity_search_with_relevance_scores(
                question, k=self.settings.similarity_k
            )
        except Exception:
            # Keep retrieval operational when embedding API/network is unavailable.
            vector_hits = []
        bm25_hits = self._bm25_hits(question, top_k=self.settings.similarity_k * 3)

        q_tokens = tokenize(question)
        q_numeric_tokens = {t for t in q_tokens if t.isdigit()}
        question_norm = question.lower()
        list_intent = any(k in question_norm for k in ["lista", "listar", "quais", "todos os", "nomes"])
        student_list_intent = list_intent and any(k in question_norm for k in ["aluno", "alunos", "estudante", "estudantes", "integrante", "integrantes"])
        competition_intent = any(k in question_norm for k in ["compet", "podio", "colocacao", "classificacao", "torneio"])
        context_intent = any(k in question_norm for k in ["historia", "contexto", "trajetoria", "criacao"])
        merged = {}

        for doc, vec_score in vector_hits:
            content = (doc.page_content or "").strip()
            if not content:
                continue
            source = doc.metadata.get("source", "arquivo_desconhecido")
            page_raw = doc.metadata.get("page")
            page = page_raw if isinstance(page_raw, int) else None
            key = _doc_key(content, source, page)
            entry = merged.setdefault(
                key,
                {
                    "content": content,
                    "source": source,
                    "page": page,
                    "doc_kind": doc.metadata.get("doc_kind", "context"),
                    "vector_score": 0.0,
                    "bm25_raw": 0.0,
                },
            )
            entry["vector_score"] = max(entry["vector_score"], float(vec_score))

        for sparse_doc, bm25_score in bm25_hits:
            key = _doc_key(sparse_doc.content, sparse_doc.source, sparse_doc.page)
            entry = merged.setdefault(
                key,
                {
                    "content": sparse_doc.content,
                    "source": sparse_doc.source,
                    "page": sparse_doc.page,
                    "doc_kind": sparse_doc.doc_kind,
                    "vector_score": 0.0,
                    "bm25_raw": 0.0,
                },
            )
            entry["bm25_raw"] = max(entry["bm25_raw"], bm25_score)

        if not merged:
            return []

        max_bm25 = max(v["bm25_raw"] for v in merged.values()) or 1.0
        ranked: List[RetrievedChunk] = []
        for entry in merged.values():
            content_tokens = tokenize(entry["content"][:1500])
            vector_score = max(0.0, min(1.0, entry["vector_score"]))
            bm25_score = entry["bm25_raw"] / max_bm25

            coverage = (len(q_tokens & content_tokens) / len(q_tokens)) if q_tokens else 0.0
            numeric_hit = 1.0 if (q_numeric_tokens and (q_numeric_tokens & content_tokens)) else 0.0
            doc_kind = str(entry.get("doc_kind", "context"))

            intent_boost = 0.0
            if list_intent and doc_kind == "table":
                intent_boost += 0.12
            if student_list_intent and doc_kind == "table":
                intent_boost += 0.16
            if student_list_intent and any(k in entry["content"].lower() for k in ["aluno", "alunos", "estudante", "integrante", "cadastro", "equipe administrativa"]):
                intent_boost += 0.12
            if competition_intent and doc_kind == "table":
                intent_boost += 0.08
            if context_intent and doc_kind == "context":
                intent_boost += 0.06

            lexical_score = 0.7 * bm25_score + 0.3 * coverage
            final_score = (
                0.50 * vector_score
                + 0.30 * bm25_score
                + 0.15 * coverage
                + 0.05 * numeric_hit
                + intent_boost
            )

            ranked.append(
                RetrievedChunk(
                    content=entry["content"],
                    source=entry["source"],
                    page=entry["page"],
                    doc_kind=doc_kind,
                    vector_score=vector_score,
                    lexical_score=lexical_score,
                    final_score=final_score,
                )
            )

        ranked.sort(key=lambda x: x.final_score, reverse=True)
        selected = [d for d in ranked if d.final_score >= self.settings.min_final_score]
        if len(selected) < self.settings.min_chunks:
            selected = ranked[: self.settings.max_chunks_for_context]
        else:
            selected = selected[: self.settings.max_chunks_for_context]

        # Em perguntas de lista, garante pelo menos evidencias de tabela quando existirem.
        if list_intent:
            table_chunks = [d for d in ranked if d.doc_kind == "table"]
            if table_chunks:
                merged = []
                seen = set()
                head_n = 5 if student_list_intent else 3
                for d in table_chunks[:head_n] + selected:
                    key = _doc_key(d.content, d.source, d.page)
                    if key in seen:
                        continue
                    seen.add(key)
                    merged.append(d)
                selected = merged[: self.settings.max_chunks_for_context]

        return selected
