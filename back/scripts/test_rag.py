from __future__ import annotations

from app.application.chat_service import TitasBotService
from app.infrastructure.env import load_project_env
from app.infrastructure.net_env import clear_broken_local_proxy
from app.infrastructure.settings import get_settings


def main() -> None:
    clear_broken_local_proxy()
    load_project_env()
    settings = get_settings()
    bot = TitasBotService(settings)

    if not bot.has_documents():
        raise RuntimeError("Base vetorial vazia. Rode criar_db.py primeiro.")

    question = "Qual foi a classificacao da equipe na temporada de 2024?"
    result = bot.ask(question=question)

    print(f"Pergunta: {question}")
    print(f"Consulta de recuperacao: {result.retrieval_query}")
    print("\nResposta:")
    print(result.answer)
    print("\nFontes recuperadas:")
    for idx, chunk in enumerate(result.chunks, start=1):
        print(f"- [{idx}] {chunk.source_label} | score={chunk.final_score:.3f}")


if __name__ == "__main__":
    main()
