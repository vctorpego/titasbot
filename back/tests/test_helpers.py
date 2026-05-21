from app.application.helpers import summarize_sources
from app.infrastructure.retrieval import RetrievedChunk


def test_summarize_sources_uses_file_name_and_page() -> None:
    chunks = [
        RetrievedChunk(
            content="conteudo",
            source=r"C:\Projetos\titasbot\back\base\tabelas - livro titas.pdf",
            page=24,
            doc_kind="table",
            vector_score=0.0,
            lexical_score=0.0,
            final_score=0.0,
        ),
        RetrievedChunk(
            content="conteudo repetido",
            source=r"C:\Projetos\titasbot\back\base\tabelas - livro titas.pdf",
            page=24,
            doc_kind="table",
            vector_score=0.0,
            lexical_score=0.0,
            final_score=0.0,
        ),
    ]

    assert summarize_sources(chunks) == ["tabelas - livro titas.pdf (pagina 25)"]
