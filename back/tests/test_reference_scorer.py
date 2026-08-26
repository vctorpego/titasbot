from __future__ import annotations

import pytest

from app.evaluation import reference_scorer


def test_lexical_score_identical_and_case_insensitive():
    assert reference_scorer.lexical_score("Asimov", "asimov") == pytest.approx(1.0)
    assert reference_scorer.lexical_score("", "") == pytest.approx(1.0)


def test_lexical_score_partial():
    # ROUGE-L compara palavras inteiras (nao caracteres): "gato" e "rato" sao
    # tokens distintos, sem sobreposicao -> F-measure 0.
    assert reference_scorer.lexical_score("gato", "rato") == pytest.approx(0.0)
    # Frases de 6 palavras cada, com 4 em comum e na mesma ordem relativa
    # ("a equipe ... o torneio ..."): LCS = 4, F-measure = 2*4/(6+6) = 2/3.
    assert reference_scorer.lexical_score(
        "a equipe venceu o torneio regional", "a equipe perdeu o torneio nacional"
    ) == pytest.approx(2 / 3)


def test_lexical_score_ignores_dash_style():
    expected = "SEK: 1° lugar — TRUFES (Regional)"
    actual_hyphen = "SEK: 1° lugar - TRUFES (Regional)"
    actual_en_dash = "SEK: 1° lugar – TRUFES (Regional)"
    assert reference_scorer.lexical_score(expected, actual_hyphen) == pytest.approx(1.0)
    assert reference_scorer.lexical_score(expected, actual_en_dash) == pytest.approx(1.0)


def test_final_score_combines_weights(monkeypatch):
    monkeypatch.setenv("REF_SEMANTIC_WEIGHT", "0.8")
    monkeypatch.setenv("REF_LEXICAL_WEIGHT", "0.2")
    monkeypatch.setattr(reference_scorer, "semantic_score", lambda a, b: 1.0)

    result = reference_scorer.final_score("gato", "rato")
    assert result["semantic"] == pytest.approx(1.0)
    assert result["lexical"] == pytest.approx(0.0)
    # 0.8*1.0 + 0.2*0.0 = 0.8
    assert result["final"] == pytest.approx(0.8)


def test_final_score_is_clamped(monkeypatch):
    monkeypatch.setenv("REF_SEMANTIC_WEIGHT", "1.0")
    monkeypatch.setenv("REF_LEXICAL_WEIGHT", "1.0")
    monkeypatch.setattr(reference_scorer, "semantic_score", lambda a, b: 1.0)
    # 1.0*1.0 + 1.0*1.0 = 2.0 -> clamp em 1.0
    result = reference_scorer.final_score("abc", "abc")
    assert result["final"] == pytest.approx(1.0)


def test_reference_scoring_available_returns_bool():
    assert isinstance(reference_scorer.reference_scoring_available(), bool)


@pytest.mark.skipif(
    not reference_scorer.reference_scoring_available(),
    reason="sentence-transformers nao instalado",
)
def test_semantic_score_considers_text_beyond_token_limit():
    """Conteudo depois do limite de 128 tokens do modelo deve influenciar o score.

    Antes da correcao por blocos, o MiniLM truncava em 128 tokens: dois textos
    com o mesmo inicio longo e finais completamente diferentes recebiam score
    1.0 (identicos), porque a parte divergente era descartada.
    """
    prefixo = " ".join(f"item numero {i} da lista de resultados" for i in range(120))
    base = f"{prefixo} o campeao foi a equipe Asimov"
    igual = f"{prefixo} o campeao foi a equipe Asimov"
    diferente = f"{prefixo} a equipe foi desclassificada e nao houve premiacao"

    assert reference_scorer.semantic_score(base, igual) == pytest.approx(1.0, abs=1e-4)
    assert reference_scorer.semantic_score(base, diferente) < 0.999
