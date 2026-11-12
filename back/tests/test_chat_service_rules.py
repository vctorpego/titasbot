from app.application.chat_service import TitasBotService
from app.infrastructure.retrieval import RetrievedChunk


def _chunk(content: str) -> RetrievedChunk:
    return RetrievedChunk(
        content=content,
        source="base.pdf",
        page=0,
        doc_kind="context",
        vector_score=0.9,
        lexical_score=0.9,
        final_score=0.9,
    )


def test_known_team_alias_uses_retrieved_evidence() -> None:
    result = TitasBotService._known_team_alias_answer(
        "Qual era o primeiro nome da equipe Titãs da Robótica?",
        [_chunk("A equipe começou como Equipe Asimov antes de se tornar Titãs da Robótica.")],
    )

    assert result is not None
    assert "Asimov" in result.answer
    assert result.chunks


def test_known_team_alias_ignores_unrelated_questions() -> None:
    result = TitasBotService._known_team_alias_answer(
        "Quais competições a equipe participou em 2025?",
        [_chunk("A equipe começou como Equipe Asimov antes de se tornar Titãs da Robótica.")],
    )

    assert result is None
