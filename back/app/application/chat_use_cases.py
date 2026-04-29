from __future__ import annotations

from app.application.chat_service import TitasBotService
from app.core.models import ChatResult


def ask_question(
    service: TitasBotService,
    question: str,
    previous_question: str | None = None,
    previous_answer: str | None = None,
) -> ChatResult:
    return service.ask(question=question, previous_question=previous_question, previous_answer=previous_answer)


def review_answer(
    service: TitasBotService,
    question: str,
    previous_answer: str,
    feedback: str,
    previous_question: str | None = None,
) -> ChatResult:
    return service.review_last_answer(
        question=question,
        previous_answer=previous_answer,
        feedback=feedback,
        previous_question=previous_question,
    )
