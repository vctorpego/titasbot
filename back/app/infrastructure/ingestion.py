from __future__ import annotations

from pathlib import Path
import sys
import time
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

if __package__ is None or __package__ == "":
    # Permite executar este arquivo diretamente: `python app/ingestion.py`
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.infrastructure.settings import Settings
from app.infrastructure.text_utils import normalize_text
from app.infrastructure.vectorstore import reset_collection


class IndexingInterrupted(Exception):
    def __init__(self, processed_chunks: int, total_chunks: int, documents_count: int) -> None:
        self.processed_chunks = processed_chunks
        self.total_chunks = total_chunks
        self.documents_count = documents_count
        super().__init__("Indexacao interrompida pelo usuario")


def _detect_doc_kind(file_name: str, settings: Settings) -> str:
    lowered = normalize_text(file_name)
    return "table" if any(k in lowered for k in settings.table_pdf_keywords) else "context"


def load_documents(settings: Settings) -> List[Document]:
    pdf_paths = sorted(Path(settings.base_dir).glob("*.pdf"))
    docs: List[Document] = []

    for pdf_path in pdf_paths:
        doc_kind = _detect_doc_kind(pdf_path.name, settings)

        try:
            reader = PdfReader(str(pdf_path), strict=False)
        except Exception:
            continue

        for page_idx, page in enumerate(reader.pages[: settings.max_pdf_pages]):
            try:
                text = page.extract_text() or ""
            except KeyboardInterrupt:
                print(
                    f"[AVISO] Extracao interrompida na pagina {page_idx + 1} de {pdf_path.name}. "
                    "Pagina ignorada e ingestao continua."
                )
                continue
            except Exception:
                continue

            text = text.strip()
            if not text:
                continue

            docs.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": str(pdf_path),
                        "source_name": pdf_path.name,
                        "page": page_idx,
                        "doc_type": "pdf_page",
                        "doc_kind": doc_kind,
                    },
                )
            )

    return docs


def split_documents(documents: List[Document], settings: Settings) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
        add_start_index=True,
    )
    return splitter.split_documents(documents)


def build_vector_db(settings: Settings) -> tuple[int, int]:
    documents = load_documents(settings)
    chunks = split_documents(documents, settings)

    vectorstore = reset_collection(settings)
    total = len(chunks)
    batch_size = max(1, settings.ingest_batch_size)
    retries = max(1, settings.ingest_retry_attempts)

    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch = chunks[start:end]

        last_error: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                vectorstore.add_documents(batch)
                print(f"Upsert: {end}/{total} chunks")
                last_error = None
                break
            except KeyboardInterrupt:
                print(
                    f"[AVISO] Indexacao interrompida em {end}/{total} chunks. "
                    "Encerrando de forma segura."
                )
                raise IndexingInterrupted(
                    processed_chunks=end,
                    total_chunks=total,
                    documents_count=len(documents),
                )
            except Exception as exc:
                last_error = exc
                if attempt < retries:
                    wait_s = 1.2 * attempt
                    print(
                        f"[AVISO] Falha no lote {start}-{end} (tentativa {attempt}/{retries}): {exc}. "
                        f"Repetindo em {wait_s:.1f}s..."
                    )
                    time.sleep(wait_s)
                else:
                    break

        if last_error is not None:
            raise last_error

    return len(documents), len(chunks)
