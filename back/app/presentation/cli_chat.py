from __future__ import annotations

from app.application.chat_service import TitasBotService
from app.application.chat_use_cases import ask_question, review_answer
from app.infrastructure.settings import Settings
from app.infrastructure.text_utils import normalize_text


def print_debug_chunks(chunks) -> None:
    print("\n[DEBUG] Top chunks recuperados:")
    for i, chunk in enumerate(chunks, start=1):
        snippet = chunk.content.replace("\n", " ")[:140]
        print(
            f"- [{i}] score_final={chunk.final_score:.3f} "
            f"(vec={chunk.vector_score:.3f}, lex={chunk.lexical_score:.3f}) "
            f"| {chunk.source_label}"
        )
        print(f"  trecho: {snippet}...")


def is_error_feedback(text: str) -> bool:
    t = normalize_text(text)
    feedback_terms = (
        "errou",
        "errado",
        "errado novamente",
        "continua errado",
        "continua errando",
        "quase isso",
        "nao era isso",
        "não era isso",
        "ta errado",
        "esta errado",
        "voce errou",
        "nao e isso",
        "nao foi isso",
    )
    return any(term in t for term in feedback_terms)


def is_confirmation_feedback(text: str) -> bool:
    t = normalize_text(text)
    terms = (
        "tem certeza",
        "certeza",
        "confirma",
        "confirmar",
    )
    return any(term in t for term in terms)


def is_equivalence_feedback(text: str) -> bool:
    t = normalize_text(text)
    patterns = (
        "mesma coisa",
        "e a mesma",
        "sao iguais",
        "são iguais",
        "e igual",
        "é igual",
        "equivalente",
        "sinonimo",
        "sinônimo",
    )
    return any(p in t for p in patterns)


def run_chat(settings: Settings) -> None:
    bot = TitasBotService(settings)
    debug_mode = False
    last_question = None
    last_answer = None
    previous_question = None

    if not bot.has_documents():
        print("A base vetorial esta vazia. Rode 'criar_db.py' primeiro.")
        return

    print("TitasBot pronto. Comandos: /debug on, /debug off, sair")
    while True:
        question = input("Pergunta: ").strip()
        if not question:
            continue

        if question.lower() in {"sair", "exit", "quit"}:
            break
        if question.lower() == "/debug on":
            debug_mode = True
            print("Modo debug ativado.")
            continue
        if question.lower() == "/debug off":
            debug_mode = False
            print("Modo debug desativado.")
            continue

        if is_error_feedback(question) or is_confirmation_feedback(question) or is_equivalence_feedback(question):
            if not last_question or not last_answer:
                print("\nResposta:")
                print("Posso revisar, mas preciso de uma pergunta anterior para corrigir.")
                print()
                continue
            result = review_answer(
                service=bot,
                question=last_question,
                previous_answer=last_answer,
                feedback=question,
                previous_question=previous_question,
            )
            print("\nResposta:")
            print(result.answer)
            last_answer = result.answer
            if debug_mode and result.chunks:
                print(f"[DEBUG] Consulta de recuperacao: {result.retrieval_query}")
                print_debug_chunks(result.chunks)
            print()
            continue

        result = ask_question(
            service=bot,
            question=question,
            previous_question=previous_question,
            previous_answer=last_answer,
        )
        print("\nResposta:")
        print(result.answer)
        previous_question = question
        last_question = question
        last_answer = result.answer

        if debug_mode and result.chunks:
            print(f"[DEBUG] Consulta de recuperacao: {result.retrieval_query}")
            print_debug_chunks(result.chunks)

        print()
