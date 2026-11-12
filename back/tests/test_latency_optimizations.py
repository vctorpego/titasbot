"""Otimizacoes de tempo de resposta (2026-11-11).

Cobre as quatro mudancas que tiraram a mediana de ~57 s para ~15 s sem
perder qualidade: reasoning_effort por etapa, auditoria que nao reescreve a
resposta aprovada, e o atalho de tabelas restrito ao que as tabelas contem.
"""
from types import SimpleNamespace

import pytest
from langchain_core.prompts import ChatPromptTemplate

from app.application.chat_service import TitasBotService
from app.application.helpers import is_unchanged_marker
from app.application.prompts import ANSWER_AUDIT_PROMPT
from app.domain.intents import is_list_question, is_table_topic_question
from app.infrastructure import llm_factory


# --------------------------------------------------------------- auditoria

def test_unchanged_marker_accepts_equals_and_variants() -> None:
    for text in ["=", " = ", '"="', "Igual", "(mantida)", ""]:
        assert is_unchanged_marker(text), text
    assert not is_unchanged_marker("Os Titãs da Robótica são a equipe do Ifes.")


def _bot_with_audit_reply(reply: str) -> TitasBotService:
    bot = TitasBotService.__new__(TitasBotService)
    bot.settings = SimpleNamespace(log_stage_timings=False)
    bot.answer_audit_prompt = ChatPromptTemplate.from_template(ANSWER_AUDIT_PROMPT)
    bot._invoke_text = lambda *_a, **_k: reply
    return bot


def test_approved_audit_keeps_candidate_without_rewriting() -> None:
    bot = _bot_with_audit_reply("STATUS: OK\nUSED_IDS: 1,2\nANSWER: =")
    result = bot._audit_answer("Pergunta?", "Resposta candidata original.", "contexto", limit_ids=4)
    assert result.status == "OK"
    assert result.answer == "Resposta candidata original."
    assert result.used_ids == [1, 2]


def test_fix_audit_uses_corrected_answer() -> None:
    bot = _bot_with_audit_reply("STATUS: FIX\nUSED_IDS: 3\nANSWER: Resposta corrigida.")
    result = bot._audit_answer("Pergunta?", "Resposta errada.", "contexto", limit_ids=4)
    assert result.status == "FIX"
    assert result.answer == "Resposta corrigida."


# ------------------------------------------------------- atalho de tabelas

def test_table_shortcut_only_for_what_tables_contain() -> None:
    # "quais" faz a pergunta ser de lista, mas tecnologias e projetos nao
    # estao nas tabelas -- restringir o contexto a elas dava "nao encontrei".
    assert is_list_question("Quais tecnologias utilizam?")
    assert not is_table_topic_question("Quais tecnologias utilizam?")
    assert not is_table_topic_question("Quais projetos vocês já fizeram?")
    assert not is_table_topic_question("Liste todos os patrocinadores da equipe")
    # O que as tabelas contem continua usando o atalho.
    assert is_table_topic_question("Quais foram as classificações da equipe na temporada de 2017?")
    assert is_table_topic_question("Quem foram os orientadores da equipe em 2018?")
    assert is_table_topic_question("Liste todos os subgrupos que já existiram na equipe")


# ------------------------------------------------- fallback extrativo

def _ctx_chunk(content: str):
    from app.infrastructure.retrieval import RetrievedChunk

    return RetrievedChunk(
        content=content, source="livro.pdf", page=0, doc_kind="context",
        vector_score=0.8, lexical_score=0.8, final_score=0.8,
    )


def test_extractive_fallback_ignores_sentences_only_about_the_team() -> None:
    # Antes, "equipe Titas da Robotica" bastava para a frase pontuar, e a
    # pergunta sobre patrocinadores devolvia fragmentos aleatorios do livro.
    bot = TitasBotService.__new__(TitasBotService)
    chunks = [
        _ctx_chunk(
            "A constituição da equipe Titãs da Robótica buscou estabelecer o desenvolvimento integral. "
            "A Figura 30 apresenta a equipe Asimov em 2015 com os primeiros uniformes da equipe."
        )
    ]
    answer = bot._extractive_fallback_answer(
        "Liste todos os patrocinadores da equipe Titãs da Robótica em ordem alfabética.", chunks
    )
    assert "encontrei" in answer.lower()


def test_extractive_fallback_still_works_when_question_is_only_about_the_team() -> None:
    # Sem termo especifico ("Quem sao os Titas da Robotica?"), o fallback usa
    # todos os termos, como antes -- frases sobre a equipe sao a resposta.
    bot = TitasBotService.__new__(TitasBotService)
    chunks = [_ctx_chunk("Os Titãs da Robótica são a equipe de robótica do Ifes Campus Colatina, criada em 2015.")]
    answer = bot._extractive_fallback_answer("Quem são os Titãs da Robótica?", chunks)
    assert "encontrei" not in answer.lower()
    assert "Titãs" in answer


def test_extractive_fallback_keeps_sentences_on_topic() -> None:
    bot = TitasBotService.__new__(TitasBotService)
    chunks = [_ctx_chunk("Os patrocinadores da equipe ao longo dos anos incluíram empresas de tecnologia da região.")]
    answer = bot._extractive_fallback_answer("Liste todos os patrocinadores da equipe Titãs da Robótica.", chunks)
    assert "patrocinadores" in answer


# ------------------------------------------------------ reasoning_effort

def test_reasoning_effort_only_for_openai_reasoning_models() -> None:
    assert llm_factory.supports_reasoning_effort("gpt-5-mini", "openai")
    assert llm_factory.supports_reasoning_effort("gpt-5-nano", "openai")
    assert llm_factory.supports_reasoning_effort("o3", "openai")
    assert not llm_factory.supports_reasoning_effort("gpt-4.1-mini", "openai")
    assert not llm_factory.supports_reasoning_effort("claude-haiku-4-5", "anthropic")
    assert not llm_factory.supports_reasoning_effort("deepseek-chat", "deepseek")


class _FakeClient:
    def __init__(self, params: dict, rejected: set[str]) -> None:
        self.params = params
        self.rejected = rejected

    def invoke(self, *_args, **_kwargs) -> str:
        for name in sorted(self.rejected):
            if name in self.params:
                raise ValueError(f"Unsupported parameter: '{name}' is not supported with this model.")
        return "ok"


def _record_builds(monkeypatch, rejected: set[str]) -> list[set[str]]:
    built: list[set[str]] = []

    def fake_init(model, model_provider, **kwargs):
        built.append(set(kwargs) & {"temperature", "reasoning_effort"})
        return _FakeClient(kwargs, rejected)

    monkeypatch.setattr(llm_factory, "init_chat_model", fake_init)
    return built


def test_fallback_drops_only_the_rejected_parameter(monkeypatch) -> None:
    # GPT-5 recusa temperature=0; reasoning_effort precisa sobreviver a isso.
    built = _record_builds(monkeypatch, rejected={"temperature"})
    model = llm_factory.build_chat_model("gpt-5-mini", temperature=0, reasoning_effort="low")
    assert model.invoke("oi") == "ok"
    assert built == [{"temperature", "reasoning_effort"}, {"reasoning_effort"}]


def test_fallback_drops_reasoning_effort_when_rejected(monkeypatch) -> None:
    built = _record_builds(monkeypatch, rejected={"temperature", "reasoning_effort"})
    model = llm_factory.build_chat_model("gpt-5-mini", temperature=0, reasoning_effort="minimal")
    assert model.invoke("oi") == "ok"
    assert built[-1] == set()


def test_reasoning_effort_not_sent_to_other_providers(monkeypatch) -> None:
    built = _record_builds(monkeypatch, rejected=set())
    llm_factory.build_chat_model("deepseek-chat", temperature=0, reasoning_effort="low")
    assert built == [{"temperature"}]


def test_unrelated_errors_still_propagate(monkeypatch) -> None:
    class _Boom:
        def invoke(self, *_a, **_k):
            raise RuntimeError("rate limit exceeded")

    monkeypatch.setattr(llm_factory, "init_chat_model", lambda *_a, **_k: _Boom())
    model = llm_factory.build_chat_model("gpt-5-mini", reasoning_effort="low")
    with pytest.raises(RuntimeError):
        model.invoke("oi")
