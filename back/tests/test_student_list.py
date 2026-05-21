from app.application.student_list import extract_student_names_from_chunks
from app.domain.intents import is_known_absent_detail_question
from app.infrastructure.retrieval import RetrievedChunk


def _chunk(content: str) -> RetrievedChunk:
    return RetrievedChunk(
        content=content,
        source="fake.pdf",
        page=0,
        doc_kind="table",
        vector_score=1.0,
        lexical_score=1.0,
        final_score=1.0,
    )


def test_extract_student_names_uses_requested_team_section() -> None:
    content = """
Tabela de Integrantes da Equipe CoSpace — Temporada 2021
Alunos Nível
Guilherme Furtado Ronconi Vieiras Ensino Médio
Guilherme Ratti Moraes Ensino Médio
Fonte: Autoria Própria.

Tabela de Integrantes da Equipe Futebol 2D — Temporada 2021
Alunos Nível
Amanda Ferreira Merelis Graduação
Jean Pandolfi Graduação
Lucas Boeloni Rodrigues da Rocha Graduação
Mateus Padovan Pereira Graduação
Mikael Botassi de Oliveira Graduação
Fonte: Autoria Própria.
"""

    names = extract_student_names_from_chunks([_chunk(content)], "Liste os alunos da equipe Futebol 2D em 2021.", 5)

    assert names == [
        "Amanda Ferreira Merelis",
        "Jean Pandolfi",
        "Lucas Boeloni Rodrigues da Rocha",
        "Mateus Padovan Pereira",
        "Mikael Botassi de Oliveira",
    ]


def test_extract_student_names_ignores_neighbor_sections() -> None:
    content = """
Tabela de Integrantes da Equipe Prática — Temporada 2021
Alunos Nível
Andre Gabrescht Rossi Ensino Médio
Victor Costa de Coura Ensino Médio
Fonte: Autoria Própria.

Tabela de Integrantes da Equipe SEK — Temporada 2021
Alunos Nível
Alisson Luiz de Souza Vighini Graduação
Arthur Cardoso Neitzel Graduação
Luiz Fernando Martinelli Zorzanelli Graduação
Priscila Fabrete Candido Graduação
Fonte: Autoria Própria.
"""

    names = extract_student_names_from_chunks([_chunk(content)], "Liste os alunos da equipe SEK em 2021.", 5)

    assert names == [
        "Alisson Luiz de Souza Vighini",
        "Arthur Cardoso Neitzel",
        "Luiz Fernando Martinelli Zorzanelli",
        "Priscila Fabrete Candido",
    ]


def test_known_absent_detail_questions_are_detected() -> None:
    assert is_known_absent_detail_question("Qual era o número de matrícula de cada aluno?")
    assert is_known_absent_detail_question("Qual foi a taxa de aprovação acadêmica por ano?")
    assert is_known_absent_detail_question("Quais alunos desistiram e quais foram os motivos de saída?")
