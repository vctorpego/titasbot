from __future__ import annotations

from langchain_chroma.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

from app.infrastructure.settings import Settings


def build_embeddings(settings: Settings) -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        request_timeout=settings.embedding_request_timeout_s,
        max_retries=settings.embedding_max_retries,
    )


def get_vectorstore(settings: Settings) -> Chroma:
    primary_path = settings.chroma_db_path
    fallback_path = settings.project_dir / ".runtime_chroma_db"
    primary_path.mkdir(parents=True, exist_ok=True)
    embeddings = build_embeddings(settings)
    try:
        return Chroma(
            persist_directory=str(primary_path),
            collection_name=settings.collection_name,
            embedding_function=embeddings,
        )
    except Exception:
        fallback_path.mkdir(parents=True, exist_ok=True)
        return Chroma(
            persist_directory=str(fallback_path),
            collection_name=settings.collection_name,
            embedding_function=embeddings,
        )


def reset_collection(settings: Settings) -> Chroma:
    vectorstore = get_vectorstore(settings)
    try:
        vectorstore.delete_collection()
    except Exception:
        # Se a colecao ainda nao existe, segue o fluxo.
        pass
    return get_vectorstore(settings)
