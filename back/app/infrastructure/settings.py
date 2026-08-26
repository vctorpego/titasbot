from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    project_dir: Path
    base_dir: Path
    table_pdf_keywords: tuple[str, ...]
    chroma_db_path: Path
    collection_name: str
    embedding_model: str
    embedding_request_timeout_s: float
    embedding_max_retries: int
    chat_model: str
    chat_temperature: float
    chunk_size: int
    chunk_overlap: int
    similarity_k: int
    max_chunks_for_context: int
    min_vector_score: float
    min_final_score: float
    min_chunks: int
    max_pdf_pages: int
    ingest_batch_size: int
    ingest_retry_attempts: int
    chat_provider: str = ""


def get_settings() -> Settings:
    # settings.py -> infrastructure -> app -> back
    project_dir = Path(__file__).resolve().parents[2]
    base_dir_env = os.getenv("BASE_DIR")
    default_base_dir = project_dir / "base"
    base_dir = Path(base_dir_env) if base_dir_env else default_base_dir
    if not base_dir.exists():
        base_dir = default_base_dir

    local_base = os.getenv("CHROMA_BASE_DIR") or os.getenv("TEMP") or os.getenv("LOCALAPPDATA") or os.path.expanduser("~")
    chroma_db_env = os.getenv("CHROMA_DB_PATH")
    chroma_db_path = Path(chroma_db_env) if chroma_db_env else Path(local_base) / "chatbot_chroma_db"
    keywords_raw = os.getenv("TABLE_PDF_KEYWORDS", "tabela,tabelas,podio,podios,lista,cadastro")
    table_pdf_keywords = tuple(k.strip().lower() for k in keywords_raw.split(",") if k.strip())

    return Settings(
        project_dir=project_dir,
        base_dir=base_dir,
        table_pdf_keywords=table_pdf_keywords,
        chroma_db_path=chroma_db_path,
        collection_name=os.getenv("CHROMA_COLLECTION", "titas_docs"),
        embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        embedding_request_timeout_s=float(os.getenv("EMBEDDING_REQUEST_TIMEOUT_S", "45")),
        embedding_max_retries=int(os.getenv("EMBEDDING_MAX_RETRIES", "2")),
        chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-5"),
        chat_temperature=float(os.getenv("CHAT_TEMPERATURE", "0")),
        chat_provider=os.getenv("CHAT_PROVIDER", ""),
        chunk_size=int(os.getenv("CHUNK_SIZE", "900")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "180")),
        similarity_k=int(os.getenv("SIMILARITY_K", "12")),
        max_chunks_for_context=int(os.getenv("MAX_CONTEXT_CHUNKS", "8")),
        min_vector_score=float(os.getenv("MIN_VECTOR_SCORE", "0.12")),
        min_final_score=float(os.getenv("MIN_FINAL_SCORE", "0.08")),
        min_chunks=int(os.getenv("MIN_CHUNKS", "2")),
        max_pdf_pages=int(os.getenv("MAX_PDF_PAGES", "600")),
        ingest_batch_size=int(os.getenv("INGEST_BATCH_SIZE", "64")),
        ingest_retry_attempts=int(os.getenv("INGEST_RETRY_ATTEMPTS", "3")),
    )
