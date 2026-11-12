from pathlib import Path

import pytest

from app.evaluation.ground_truth import (
    LABEL_CORRECT,
    LABEL_INCORRECT,
    KeyFact,
    fact_matched,
    key_fact_coverage,
    load_label_overrides,
    load_metric_cases,
    placement_groups,
    truth_label,
)

EVALS = Path(__file__).resolve().parent / "evals"


@pytest.fixture(scope="module")
def cases():
    loaded = load_metric_cases(EVALS / "metric_eval_annotations.json", EVALS / "model_eval_cases.json")
    return {case.number: case for case in loaded}


def test_labels_orientation_is_one_for_correct():
    # O projeto de referencia invertia os rotulos (0 = verdadeiro). Aqui 1 = correta.
    assert LABEL_CORRECT == 1 and LABEL_INCORRECT == 0
    assert truth_label(1.0, 1.0) == LABEL_CORRECT
    assert truth_label(0.5, 0.8) == LABEL_INCORRECT
    assert truth_label(0.8, 0.8) == LABEL_CORRECT


def test_every_official_case_is_annotated(cases):
    assert sorted(cases) == list(range(1, 41))


def test_gabarito_covers_all_of_its_own_facts(cases):
    for case in cases.values():
        result = key_fact_coverage(case.expected_output, case.key_facts)
        assert result.coverage == 1.0, (case.id, result.missing)


def test_other_years_do_not_count_as_correct(cases):
    wrong = key_fact_coverage(cases[12].expected_output, cases[10].key_facts)
    assert truth_label(wrong.coverage, cases[10].min_coverage) == LABEL_INCORRECT


def test_free_form_list_with_headers_is_matched(cases):
    answer = (
        "Em 2017 a equipe conquistou:\n\n**LARC (Latin American Robotics Competition):**\n"
        "- CoSpace: 1º lugar\n- Futebol 2D: campeã\n- Humanoide: 1º lugar\n- SEK: 4º lugar\n\n"
        "**IRONCUP:**\n- Futebol 2D: 1º lugar\n- Seguidor de Linha: 8º lugar\n\n"
        "TRUFES: SEK 2º e 3º lugar\nOBR: Prática 8º lugar (regional) e medalha de bronze na teórica."
    )
    assert key_fact_coverage(answer, cases[10].key_facts).coverage == 1.0


def test_names_tolerate_missing_middle_names(cases):
    answer = "Foram Jean Glazar, Giovany Frossard, Julio Vendramini, Diego Mafioletti, Igor Pulini, Renan Rios e Luiz Reinoso."
    assert key_fact_coverage(answer, cases[21].key_facts).coverage == 1.0
    assert key_fact_coverage("Foram Igor Pulini e Renan Rios.", cases[21].key_facts).coverage < 0.5


def test_short_fact_and_refusal(cases):
    assert key_fact_coverage("O primeiro nome foi ASIMOV.", cases[2].key_facts).coverage == 1.0
    assert key_fact_coverage("Sempre foi Titãs.", cases[2].key_facts).coverage == 0.0
    assert key_fact_coverage("Não encontrei essa informação nos documentos.", cases[40].key_facts).coverage == 1.0
    assert key_fact_coverage("Foram captados 50 mil reais.", cases[40].key_facts).coverage == 0.0


def test_placement_requires_same_segment():
    fact = KeyFact(text="SEK: 1° lugar — TRUFES (Regional)", kind="placement",
                   groups=placement_groups("SEK: 1° lugar — TRUFES (Regional)"), scope="line")
    assert fact_matched("SEK: primeiro lugar no TRUFES", fact)
    assert not fact_matched("SEK: 3º lugar no TRUFES\nCoSpace: 1º lugar na LARC", fact)


def test_label_overrides(tmp_path):
    path = tmp_path / "rotulos_revisados.csv"
    path.write_text("answer_key;label\na|rag|q01;1\nb|rag|q02;incorreta\nc|rag|q03;\n", encoding="utf-8-sig")
    assert load_label_overrides(path) == {"a|rag|q01": 1, "b|rag|q02": 0}
    assert load_label_overrides(tmp_path / "nao_existe.csv") == {}
