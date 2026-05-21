from __future__ import annotations

from app.infrastructure.env import load_project_env
from app.infrastructure.ingestion import IndexingInterrupted, build_vector_db
from app.infrastructure.net_env import clear_broken_local_proxy
from app.infrastructure.settings import get_settings


def main() -> None:
    clear_broken_local_proxy()
    load_project_env()
    settings = get_settings()

    print(f"Base PDF: {settings.base_dir}")
    print(f"PDF de tabelas (detector): {', '.join(settings.table_pdf_keywords)}")
    print(f"Max paginas por PDF: {settings.max_pdf_pages}")
    print(f"Lote de ingestao: {settings.ingest_batch_size} | Retries: {settings.ingest_retry_attempts}")
    print(f"Banco vetorial: {settings.chroma_db_path}")
    print(f"Colecao: {settings.collection_name}")

    try:
        documents_count, chunks_count = build_vector_db(settings)
    except IndexingInterrupted as interrupted:
        print(
            "Indexacao interrompida pelo usuario "
            f"({interrupted.processed_chunks}/{interrupted.total_chunks} chunks processados)."
        )
        return
    except Exception as exc:
        print(f"Erro ao criar banco vetorial: {exc}")
        print("Verifique internet, OPENAI_API_KEY e permissoes da pasta do banco.")
        raise

    print(f"Documentos carregados: {documents_count}")
    print(f"Chunks gerados: {chunks_count}")
    print("Banco vetorial criado com sucesso.")


if __name__ == "__main__":
    main()
