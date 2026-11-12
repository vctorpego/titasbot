"""Etapa 1 do estudo de metricas: gera as respostas dos modelos (com e sem RAG).

Uso (em back/):
    .\\venv\\Scripts\\python.exe scripts\\generate_answers.py

Retomavel: respostas ja geradas sem erro sao puladas (EVAL_REGENERATE=1 refaz tudo).
Filtros: EVAL_MODELS=openai,anthropic,deepseek  EVAL_CONDITIONS=rag,no_rag
         EVAL_CASE_IDS=q02,q10  ou  EVAL_CASE_LIMIT=3
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluate_models import NO_RAG_SYSTEM  # noqa: E402

STORED_CHUNKS = 8


def answer_without_rag(model_client, question: str) -> str:
    """Como em evaluate_models.answer_without_rag, mas propaga erros de API
    (uma falha de rede nao pode virar "resposta vazia" e ser rotulada incorreta)."""
    from langchain_core.prompts import ChatPromptTemplate

    from app.infrastructure.llm_factory import to_text

    message = ChatPromptTemplate.from_messages(
        [("system", NO_RAG_SYSTEM), ("human", "{question}")]
    ).invoke({"question": question})
    return to_text(model_client.invoke(message)).strip()


def main() -> None:
    from app.application.chat_service import TitasBotService
    from app.evaluation import study_io
    from app.infrastructure.env import load_project_env
    from app.infrastructure.net_env import clear_broken_local_proxy
    from app.infrastructure.settings import get_settings

    clear_broken_local_proxy()
    load_project_env()

    specs = study_io.model_specs()
    conds = study_io.conditions()
    cases = study_io.filter_cases(study_io.load_cases())
    regenerate = os.getenv("EVAL_REGENERATE") == "1"
    existing = {} if regenerate else study_io.latest_answers()

    total = len(specs) * len(conds) * len(cases)
    print(f"Modelos: {[s.model for s in specs]} | condicoes: {conds} | casos: {len(cases)} | total: {total}")
    settings = get_settings()
    done = 0
    max_consecutive_errors = int(os.getenv("EVAL_MAX_CONSECUTIVE_ERRORS", "5"))
    consecutive_errors = 0
    for spec in specs:
        bot = TitasBotService(replace(settings, chat_model=spec.model, chat_provider=spec.provider))
        if "rag" in conds and not bot.has_documents():
            raise RuntimeError("Base vetorial vazia. Rode criar_db.py antes de gerar respostas com RAG.")
        for condition in conds:
            for case in cases:
                done += 1
                key = study_io.answer_key(spec.label, condition, case.id)
                previous = existing.get(key)
                if previous and not previous.get("error"):
                    continue
                print(f"[{done}/{total}] {key}")
                start = time.perf_counter()
                record = {
                    "answer_key": key,
                    "model_label": spec.label,
                    "model": spec.model,
                    "provider": spec.provider,
                    "condition": condition,
                    "case_id": case.id,
                    "number": case.number,
                    "answer": "",
                    "retrieval_query": "",
                    "chunks": [],
                    "seconds": None,
                    "error": "",
                    "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                }
                try:
                    if condition == "no_rag":
                        record["answer"] = answer_without_rag(bot.model, case.question)
                        record["retrieval_query"] = "no_rag"
                    else:
                        result = bot.ask(question=case.question)
                        record["answer"] = result.answer
                        record["retrieval_query"] = result.retrieval_query
                        record["chunks"] = [asdict(chunk) for chunk in result.chunks[:STORED_CHUNKS]]
                except Exception as exc:
                    record["error"] = f"{type(exc).__name__}: {exc}"[:800]
                    print(f"    erro: {record['error']}")
                record["seconds"] = round(time.perf_counter() - start, 3)
                study_io.append_jsonl(study_io.ANSWERS_PATH, [record])
                consecutive_errors = consecutive_errors + 1 if record["error"] else 0
                if consecutive_errors >= max_consecutive_errors:
                    raise SystemExit(
                        f"\n{consecutive_errors} erros seguidos. Verifique credito/limite das APIs "
                        "(o RAG tambem usa embeddings da OpenAI) e rode de novo; o que ja foi gerado fica em cache."
                    )

    print(f"\nRespostas em: {study_io.ANSWERS_PATH}")


if __name__ == "__main__":
    main()
