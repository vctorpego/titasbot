from __future__ import annotations

import re

from app.infrastructure.text_utils import normalize_text


def needs_previous_context(question: str) -> bool:
    q = normalize_text(question)
    explicit = (
        "isso",
        "essa",
        "esse",
        "dessas",
        "desses",
        "nesse ano",
        "naquele ano",
        "cada uma",
        "essas equipes",
        "geral",
        "tem certeza",
        "e o da",
        "e o de",
        "e depois",
        "e depois disso",
        "e quanto",
    )
    return any(t in q for t in explicit) or len(q.split()) <= 5


def precision_query_boost(question: str) -> str:
    q = normalize_text(question)
    hints: list[str] = []
    if any(k in q for k in ("criad", "fund", "origem", "inicio", "comec")):
        hints.extend(["criacao", "fundacao", "inicio oficial"])
    if any(k in q for k in ("compet", "classific", "coloc", "podio", "torneio")):
        hints.extend(["competicao", "classificacao", "resultado"])
    if any(k in q for k in ("orientador", "professor", "aluno", "integrante")):
        hints.extend(["nomes", "lista", "integrantes"])
    if any(k in q for k in ("participar", "entrar", "ingressar", "fazer parte")):
        hints.extend(["ingresso", "processo seletivo", "estudantes do ifes", "elegibilidade"])
    if any(k in q for k in ("projeto", "projetos")):
        hints.extend(["ensino", "pesquisa", "extensao", "acoes", "iniciativas"])
    if any(k in q for k in ("competicao", "competicoes", "obr", "cbr", "robocup", "larc")):
        hints.extend(["competicao", "modalidade", "classificacao"])
    if any(k in q for k in ("voces", "vocês", "equipe", "titas", "titãs", "asimov")):
        hints.extend(["Titãs da Robótica", "Asimov", "IFES Campus Colatina"])
    if not hints:
        return question
    return f"{question} ({', '.join(hints)})"


def is_participation_question(question: str) -> bool:
    q = normalize_text(question)
    return any(k in q for k in ("como participar", "como entrar", "como ingressar", "fazer parte", "entrar na equipe"))


def is_projects_question(question: str) -> bool:
    q = normalize_text(question)
    return "projeto" in q and not any(k in q for k in ("competicao", "competi", "podio", "classificacao"))


def is_student_list_question(question: str) -> bool:
    q = normalize_text(question)
    list_intent = any(k in q for k in ("liste", "listar", "lista", "todos os", "todas as", "quais"))
    student_intent = any(k in q for k in ("alunos", "aluno", "estudantes", "estudante", "integrantes"))
    return list_intent and student_intent


def is_full_student_list_request(question: str) -> bool:
    q = normalize_text(question)
    return any(k in q for k in ("todos", "toda", "geral", "completa", "completo", "todo mundo"))


def question_is_about_team(question: str) -> bool:
    q = normalize_text(question)
    team_signals = (
        "voces",
        "vocês",
        "equipe",
        "titas",
        "titãs",
        "asimov",
        "ifes",
        "projetos voces",
        "projetos vocês",
    )
    return any(s in q for s in team_signals)


def is_year_sensitive_question(question: str) -> bool:
    q = normalize_text(question)
    hints = ("ano", "data", "quando", "foi em", "em que ano", "qual ano")
    return any(h in q for h in hints)


def is_fact_question(question: str) -> bool:
    q = normalize_text(question)
    return any(
        h in q
        for h in (
            "qual",
            "quando",
            "ano",
            "nome",
            "classificacao",
            "colocacao",
            "resultado",
            "quem",
            "quantos",
            "quantidade",
        )
    )


def is_list_question(question: str) -> bool:
    q = normalize_text(question)
    return any(h in q for h in ("lista", "listar", "quais", "nomes", "todos os", "todos as"))


def should_expand_query(question: str) -> bool:
    q = normalize_text(question)
    has_year = bool(re.search(r"\b(?:19|20)\d{2}\b", q))
    is_direct = any(k in q for k in ("qual", "quem", "quando", "em que ano", "lista", "listar", "nomes"))
    return not (has_year and is_direct)


def is_social_message(question: str) -> bool:
    q = normalize_text(question).strip()
    if not q:
        return False
    social_terms = (
        "que legal",
        "legal",
        "bacana",
        "massa",
        "top",
        "show",
        "entendi",
        "ok",
        "blz",
        "beleza",
        "obrigado",
        "obrigada",
        "valeu",
        "perfeito",
        "ótimo",
        "otimo",
        "bom",
        "boa",
        "certo",
        "aha",
        "aham",
        "olá",
        "ola",
        "oi",
        "bom dia",
        "boa tarde",
        "boa noite",
        "tchau",
        "falou",
    )
    if q in social_terms:
        return True
    return any(
        q.startswith(prefix)
        for prefix in (
            "bom dia",
            "boa tarde",
            "boa noite",
            "que legal",
            "obrigad",
            "valeu",
            "entendi",
            "beleza",
            "perfeito",
            "legal",
            "bacana",
        )
    )


def conversational_intent(question: str) -> str:
    q = normalize_text(question).strip()
    if not q:
        return "none"

    if any(k in q for k in ("bom dia", "boa tarde", "boa noite", "oi", "ola", "olá")):
        return "greeting"
    if any(k in q for k in ("obrigad", "valeu")):
        return "thanks"
    if any(k in q for k in ("tchau", "falou")):
        return "bye"
    if any(k in q for k in ("que legal", "legal", "bacana", "massa", "top", "show", "entendi")):
        return "ack"
    if q in {"sim", "nao", "não", "ok", "perfeito", "certo", "blz", "beleza"}:
        return "confirm_short"
    if any(k in q for k in ("continue", "pode seguir", "segue", "continue nisso", "aprofunde")):
        return "continue"
    if any(k in q for k in ("resuma", "resume", "resumir", "resumo")):
        return "summarize"
    if any(k in q for k in ("em topicos", "em tópicos", "em lista", "em tabela")):
        return "reformat"
    if any(k in q for k in ("mais curto", "mais resumido", "objetivo")):
        return "shorter"
    if any(k in q for k in ("mais detalhado", "detalhe mais", "aprofunda mais")):
        return "detailed"
    if any(k in q for k in ("novo assunto", "mudar assunto", "limpar contexto", "zera contexto")):
        return "reset_context"
    return "none"
