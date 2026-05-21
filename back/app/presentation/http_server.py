from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from uuid import uuid4

from app.application.helpers import summarize_sources
from app.application.chat_use_cases import ask_question, review_answer
from app.application.chat_service import TitasBotService
from app.infrastructure.env import load_project_env
from app.infrastructure.settings import get_settings
from app.presentation.cli_chat import is_confirmation_feedback, is_equivalence_feedback, is_error_feedback


HOST = "127.0.0.1"
PORT = 8000


@dataclass
class SessionState:
    previous_question: str | None = None
    last_question: str | None = None
    last_answer: str | None = None


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    handler.end_headers()
    handler.wfile.write(body)


def _get_or_create_session(
    sessions: dict[str, SessionState],
    sessions_lock: threading.Lock,
    session_id: str | None,
) -> tuple[str, SessionState]:
    sid = session_id.strip() if isinstance(session_id, str) and session_id.strip() else str(uuid4())
    with sessions_lock:
        state = sessions.get(sid)
        if state is None:
            state = SessionState()
            sessions[sid] = state
    return sid, state


class ChatHandler(BaseHTTPRequestHandler):
    bot: TitasBotService | None = None
    sessions: dict[str, SessionState] = {}
    sessions_lock = threading.Lock()

    def log_message(self, fmt: str, *args) -> None:
        return

    def _bot(self) -> TitasBotService:
        if self.bot is None:
            raise RuntimeError("Servidor nao inicializado.")
        return self.bot

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/health":
            _json_response(self, 200, {"ok": True, "documents_ready": self._bot().has_documents()})
            return

        if self.path == "/":
            html = (
                "<!doctype html><html><head><meta charset='utf-8'><title>TitasBot</title></head>"
                "<body style='font-family:Arial;padding:24px'>"
                "<h2>TitasBot Web</h2>"
                "<p>Endpoint de saude: <code>/health</code></p>"
                "<p>Endpoint de chat: <code>POST /chat</code></p>"
                "<pre>{\"question\":\"qual foi o primeiro nome da equipe?\",\"session_id\":\"opcional\"}</pre>"
                "</body></html>"
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return

        _json_response(self, 404, {"error": "Not found"})

    def do_POST(self) -> None:
        if self.path != "/chat":
            _json_response(self, 404, {"error": "Not found"})
            return

        bot = self._bot()
        if not bot.has_documents():
            _json_response(self, 400, {"error": "Base vetorial vazia. Rode criar_db.py primeiro."})
            return

        try:
            raw_len = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(raw_len).decode("utf-8")
            payload = json.loads(body) if body else {}
        except Exception:
            _json_response(self, 400, {"error": "JSON invalido."})
            return

        question = str(payload.get("question", "")).strip()
        if not question:
            _json_response(self, 400, {"error": "Campo 'question' e obrigatorio."})
            return

        session_id, state = _get_or_create_session(
            self.sessions,
            self.sessions_lock,
            payload.get("session_id"),
        )

        if is_error_feedback(question) or is_confirmation_feedback(question) or is_equivalence_feedback(question):
            if not state.last_question or not state.last_answer:
                _json_response(
                    self,
                    200,
                    {
                        "session_id": session_id,
                        "answer": "Posso revisar, mas preciso de uma pergunta anterior para corrigir.",
                        "sources": [],
                    },
                )
                return
            result = review_answer(
                service=bot,
                question=state.last_question,
                previous_answer=state.last_answer,
                feedback=question,
                previous_question=state.previous_question,
            )
            state.last_answer = result.answer
            _json_response(
                self,
                200,
                {
                    "session_id": session_id,
                    "answer": result.answer,
                    "retrieval_query": result.retrieval_query,
                    "sources": summarize_sources(result.chunks),
                },
            )
            return

        result = ask_question(
            service=bot,
            question=question,
            previous_question=state.previous_question,
            previous_answer=state.last_answer,
        )
        state.previous_question = question
        state.last_question = question
        state.last_answer = result.answer
        _json_response(
            self,
            200,
            {
                "session_id": session_id,
                "answer": result.answer,
                "retrieval_query": result.retrieval_query,
                "sources": summarize_sources(result.chunks),
            },
        )


def main() -> None:
    load_project_env()
    settings = get_settings()
    ChatHandler.bot = TitasBotService(settings)
    ChatHandler.sessions = {}
    ChatHandler.sessions_lock = threading.Lock()
    server = ThreadingHTTPServer((HOST, PORT), ChatHandler)
    print(f"TitasBot Web ativo em http://{HOST}:{PORT}")
    print("Health: GET /health")
    print("Chat:   POST /chat")
    server.serve_forever()
