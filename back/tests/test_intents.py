import pytest

from app.domain.intents import conversational_intent, is_full_student_list_request, is_student_list_question


@pytest.mark.parametrize(
    "question,expected",
    [
        ("liste todos os alunos da equipe", True),
        ("quais estudantes participaram em 2019?", True),
        ("liste todos os patrocinadores", False),
        ("quais orientadores atuaram em 2024?", False),
    ],
)
def test_is_student_list_question(question: str, expected: bool) -> None:
    assert is_student_list_question(question) is expected


@pytest.mark.parametrize(
    "question,expected",
    [
        ("quero a lista geral completa de alunos", True),
        ("mostre todos os alunos", True),
        ("quais alunos da equipe de futebol 2d em 2021?", False),
    ],
)
def test_is_full_student_list_request(question: str, expected: bool) -> None:
    assert is_full_student_list_request(question) is expected


@pytest.mark.parametrize(
    "message,expected_intent",
    [
        ("bom dia", "greeting"),
        ("obrigado", "thanks"),
        ("valeu pela ajuda", "thanks"),
        ("qual foi a classificação em 2025?", "none"),
        ("liste os alunos da equipe sek em 2017", "none"),
    ],
)
def test_conversational_intent(message: str, expected_intent: str) -> None:
    assert conversational_intent(message) == expected_intent
