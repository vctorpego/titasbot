from __future__ import annotations

import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.models import ChatResult
from app.infrastructure.settings import Settings
from app.domain.constants import INSUFFICIENT_MSG, STUDENT_LIST_MAX_CHUNKS, STUDENT_LIST_SOURCE_IDS
from app.domain.intents import (
    conversational_intent,
    is_fact_question,
    is_list_question,
    is_participation_question,
    is_projects_question,
    is_social_message,
    is_student_list_question,
    needs_previous_context,
    precision_query_boost,
    should_expand_query,
)
from app.application.helpers import (
    AuditResult,
    answer_targets_question,
    build_context,
    build_history,
    chunk_key,
    clean_answer,
    dedupe_keep_order,
    filter_team_relevant_chunks,
    has_min_evidence,
    normalize_sources,
    parse_ids,
    split_sentences,
)
from app.application.prompts import (
    ANSWER_AUDIT_PROMPT,
    CONTEXT_DECISION_PROMPT,
    EVIDENCE_SELECTION_PROMPT,
    FACT_PROMPT,
    GEN_PROMPT,
    LIST_PROMPT,
    LIST_CANONICALIZATION_PROMPT,
    PARTICIPATION_PROMPT,
    PROJECTS_PROMPT,
    QUERY_EXPANSION_PROMPT,
    REVIEW_PROMPT,
    STRICT_REFOCUS_PROMPT,
    STUDENT_LIST_PROMPT,
    TEAM_SCOPE_AUDIT_PROMPT,
)
from app.application.student_list import extract_student_names_from_chunks
from app.infrastructure.retrieval import HybridRetriever, RetrievedChunk
from app.infrastructure.text_utils import extract_terms, normalize_text
from app.infrastructure.vectorstore import get_vectorstore

class TitasBotService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.vectorstore = get_vectorstore(settings)
        self.retriever = HybridRetriever(self.vectorstore, settings)
        self.model = ChatOpenAI(model=settings.chat_model, temperature=settings.chat_temperature)

        self.gen_prompt = ChatPromptTemplate.from_template(GEN_PROMPT)
        self.fact_prompt = ChatPromptTemplate.from_template(FACT_PROMPT)
        self.list_prompt = ChatPromptTemplate.from_template(LIST_PROMPT)
        self.list_canonicalization_prompt = ChatPromptTemplate.from_template(LIST_CANONICALIZATION_PROMPT)
        self.student_list_prompt = ChatPromptTemplate.from_template(STUDENT_LIST_PROMPT)
        self.participation_prompt = ChatPromptTemplate.from_template(PARTICIPATION_PROMPT)
        self.projects_prompt = ChatPromptTemplate.from_template(PROJECTS_PROMPT)
        self.strict_refocus_prompt = ChatPromptTemplate.from_template(STRICT_REFOCUS_PROMPT)
        self.review_prompt = ChatPromptTemplate.from_template(REVIEW_PROMPT)
        self.evidence_selection_prompt = ChatPromptTemplate.from_template(EVIDENCE_SELECTION_PROMPT)
        self.answer_audit_prompt = ChatPromptTemplate.from_template(ANSWER_AUDIT_PROMPT)
        self.query_expansion_prompt = ChatPromptTemplate.from_template(QUERY_EXPANSION_PROMPT)
        self.context_decision_prompt = ChatPromptTemplate.from_template(CONTEXT_DECISION_PROMPT)
        self.team_scope_audit_prompt = ChatPromptTemplate.from_template(TEAM_SCOPE_AUDIT_PROMPT)

    def has_documents(self) -> bool:
        try:
            return self.vectorstore._collection.count() > 0
        except Exception:
            return False

    def _build_retrieval_query(
        self,
        question: str,
        previous_question: str | None,
        previous_answer: str | None = None,
    ) -> str:
        base = precision_query_boost(question)
        if is_list_question(question):
            base = f"{base} (usar arquivo de listagens/tabelas; cadastro; nomes)"
        q_norm = normalize_text(question)
        prev_norm = normalize_text(previous_question or "")
        prev_years = re.findall(r"\b(?:19|20)\d{2}\b", previous_question or "")

        if q_norm.startswith("e depois") and ("primeiro nome" in prev_norm or "nome da equipe" in prev_norm):
            return "qual foi o nome adotado depois de Asimov pela equipe Titas da Robotica"

        if "classificacao" in q_norm and "nessa competicao" in q_norm and prev_years:
            return f"{base} (competicao do ano {prev_years[0]}; colocacao; lugar)"

        if not previous_question or not needs_previous_context(question):
            return base

        model_followup = False
        prev_short = ""
        if previous_answer:
            prev_short = re.sub(r"\s+", " ", previous_answer.split("Fontes usadas:")[0]).strip()[:220]

        try:
            msg = self.context_decision_prompt.invoke(
                {
                    "previous_question": previous_question,
                    "previous_answer": prev_short,
                    "question": question,
                }
            )
            decision = self._invoke_text(msg).upper()
            model_followup = decision.startswith("USE_PREVIOUS")
        except Exception:
            model_followup = False

        if not model_followup and len(normalize_text(question).split()) > 5:
            return base

        if prev_short:
            return f"{base} (sobre: {previous_question}; contexto anterior: {prev_short})"
        return f"{base} (sobre: {previous_question})"

    def _enforce_team_scope(self, question: str, answer: str, context: str) -> str:
        if not answer or normalize_text(answer) == normalize_text(INSUFFICIENT_MSG):
            return answer

        msg = self.team_scope_audit_prompt.invoke(
            {
                "question": question,
                "context": context,
                "answer": answer,
                "insufficient": INSUFFICIENT_MSG,
            }
        )
        reviewed = clean_answer(self._invoke_text(msg))
        return reviewed or answer

    def _invoke_text(self, message) -> str:
        try:
            return self.model.invoke(message).content.strip()
        except Exception:
            return ""

    def _expand_queries(self, question: str) -> list[str]:
        try:
            msg = self.query_expansion_prompt.invoke({"question": question})
            raw = self._invoke_text(msg)
            lines = [re.sub(r"^[\-\d\.\)\s]+", "", ln).strip() for ln in raw.splitlines()]
            queries: list[str] = []
            for q in lines:
                if q and q not in queries:
                    queries.append(q)
            return queries[:3] if queries else [question]
        except Exception:
            return [question]

    def _retrieve_with_expansion(self, question: str, retrieval_query: str) -> list[RetrievedChunk]:
        queries = [retrieval_query]
        if not is_student_list_question(question) and should_expand_query(question):
            for q in self._expand_queries(retrieval_query):
                if q not in queries:
                    queries.append(q)

        merged = {}
        for q in queries:
            try:
                hits = self.retriever.retrieve(q)
            except Exception:
                hits = []
            for h in hits:
                key = chunk_key(h)
                prev = merged.get(key)
                if prev is None or h.final_score > prev.final_score:
                    merged[key] = h

        ranked = sorted(merged.values(), key=lambda x: x.final_score, reverse=True)
        if is_student_list_question(question):
            table_first = [c for c in ranked if c.doc_kind == "table"]
            return (table_first or ranked)[:STUDENT_LIST_MAX_CHUNKS]
        return ranked[: max(self.settings.max_chunks_for_context * 2, 12)]

    def _select_evidence_chunks(self, question: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if is_student_list_question(question):
            table_chunks = [c for c in chunks if c.doc_kind == "table"]
            base = table_chunks or chunks
            return base[: min(30, len(base))]

        if is_list_question(question):
            table_chunks = [c for c in chunks if c.doc_kind == "table"]
            if table_chunks:
                table_chunks.sort(key=lambda x: x.final_score, reverse=True)
                return table_chunks[: self.settings.max_chunks_for_context]

        if len(chunks) <= 5:
            return chunks

        seed = chunks[:6]
        full_context = build_context(chunks)
        try:
            sel_msg = self.evidence_selection_prompt.invoke({"question": question, "context": full_context})
            raw = self._invoke_text(sel_msg)
            ids = parse_ids(raw, len(chunks))
        except Exception:
            ids = []

        selected = [chunks[i - 1] for i in ids[:8]] if ids else []
        if not selected:
            selected = seed

        seen = {chunk_key(c) for c in selected}
        for c in seed:
            key = chunk_key(c)
            if key not in seen:
                selected.append(c)
                seen.add(key)

        selected.sort(key=lambda x: x.final_score, reverse=True)
        return selected[: self.settings.max_chunks_for_context]

    def _extractive_fallback_answer(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        query_hint: str = "",
    ) -> str:
        q_terms = set(extract_terms(question))
        focus_years = set(re.findall(r"\b(?:19|20)\d{2}\b", f"{question} {query_hint}"))
        q_norm = normalize_text(question)
        rank_intent = any(k in q_norm for k in ("classific", "coloc", "lugar", "podio", "cada uma"))
        project_intent = is_projects_question(question)
        participation_intent = is_participation_question(question)
        student_list_intent = is_student_list_question(question)
        candidates: list[tuple[float, str]] = []

        for c in chunks[:6]:
            for sentence in split_sentences(c.content):
                s = sentence.strip()
                if len(s) < 24:
                    continue
                s_norm = normalize_text(s)
                s_terms = set(extract_terms(s))
                if not s_terms:
                    continue
                overlap = len(q_terms & s_terms) / max(1, len(q_terms)) if q_terms else 0.0
                sentence_years = set(re.findall(r"\b(?:19|20)\d{2}\b", s))
                year_bonus = 0.0
                if focus_years and sentence_years & focus_years:
                    year_bonus += 0.35
                elif sentence_years:
                    year_bonus += 0.12

                rank_bonus = 0.0
                if rank_intent and re.search(r"\b\d{1,2}\s*(?:º|°)\s*lugar\b|\bmedalha\b|\bcoloc", normalize_text(s)):
                    rank_bonus += 0.35

                project_penalty = 0.0
                if project_intent:
                    competition_like = any(
                        k in s_norm
                        for k in ("competicao", "obr", "cbr", "robocup", "larc", "podio", "classificacao", "lugar")
                    )
                    project_like = any(k in s_norm for k in ("projeto", "extens", "pesquisa", "ensino", "acao", "iniciativa"))
                    if competition_like and not project_like:
                        project_penalty -= 0.35

                participation_bonus = 0.0
                if participation_intent:
                    if any(k in s_norm for k in ("processo seletivo", "inscricao", "selecao", "edital", "participar")):
                        participation_bonus += 0.25
                    if any(k in s_norm for k in ("qualquer curso", "todos os cursos", "estudantes do ifes")):
                        participation_bonus += 0.35
                    if any(k in s_norm for k in ("informatica para internet", "sistemas de informacao")) and "qualquer curso" not in s_norm:
                        participation_bonus -= 0.20

                student_bonus = 0.0
                if student_list_intent:
                    has_name_shape = bool(re.search(r"\b[A-ZÁÂÃÉÊÍÓÔÕÚÇ][a-záâãéêíóôõúç]+(?:\s+[A-ZÁÂÃÉÊÍÓÔÕÚÇ][a-záâãéêíóôõúç]+){1,4}\b", s))
                    if has_name_shape:
                        student_bonus += 0.35
                    if any(k in s_norm for k in ("aluno", "alunos", "estudante", "integrante", "equipe administrativa")):
                        student_bonus += 0.20
                    if any(k in s_norm for k in ("competicao", "podio", "classificacao", "lugar", "modalidade")):
                        student_bonus -= 0.35

                score = overlap + year_bonus + rank_bonus + project_penalty + participation_bonus + student_bonus + (0.15 * c.final_score)
                if score >= 0.15:
                    candidates.append((score, s))

        if not candidates:
            return INSUFFICIENT_MSG

        candidates.sort(key=lambda x: x[0], reverse=True)
        picked = dedupe_keep_order([s for _, s in candidates[:8]])
        if not picked:
            return INSUFFICIENT_MSG

        if student_list_intent:
            names: list[str] = []
            seen = set()
            pattern = r"\b[A-ZÁÂÃÉÊÍÓÔÕÚÇ][a-záâãéêíóôõúç]+(?:\s+[A-ZÁÂÃÉÊÍÓÔÕÚÇ][a-záâãéêíóôõúç]+){1,4}\b"
            for s in picked[:12]:
                for m in re.findall(pattern, s):
                    key = normalize_text(m)
                    if key not in seen and len(m.split()) >= 2:
                        seen.add(key)
                        names.append(m.strip())
            if names:
                return "\n".join(f"- {n}" for n in names[:40])
            return INSUFFICIENT_MSG

        if is_list_question(question) or rank_intent or project_intent:
            bullets = [f"- {s}" for s in picked[:6]]
            return "\n".join(bullets)

        if any(k in normalize_text(question) for k in ("ano", "data", "quando", "foi em", "em que ano", "qual ano")):
            year_lines = [s for s in picked if re.search(r"\b(?:19|20)\d{2}\b", s)]
            if year_lines:
                return year_lines[0]

        return " ".join(picked[:2])

    def _audit_answer(self, question: str, answer: str, context: str, limit_ids: int) -> AuditResult:
        try:
            msg = self.answer_audit_prompt.invoke(
                {
                    "question": question,
                    "context": context,
                    "answer": answer,
                    "insufficient": INSUFFICIENT_MSG,
                }
            )
            raw = self._invoke_text(msg)
        except Exception:
            return AuditResult(status="FIX", answer=clean_answer(answer), used_ids=[])

        status_match = re.search(r"STATUS:\s*(OK|FIX)", raw, flags=re.IGNORECASE)
        status = status_match.group(1).upper() if status_match else "FIX"
        ids = parse_ids(raw, limit_ids)
        answer_match = re.search(r"ANSWER:\s*(.*)$", raw, flags=re.IGNORECASE | re.DOTALL)
        fixed_answer = answer_match.group(1).strip() if answer_match else clean_answer(answer)
        fixed_answer = clean_answer(fixed_answer)
        return AuditResult(status=status, answer=fixed_answer, used_ids=ids)

    def _generate_candidate(
        self,
        question: str,
        context: str,
        previous_question: str | None,
        previous_answer: str | None,
    ) -> str:
        if is_student_list_question(question):
            msg = self.student_list_prompt.invoke(
                {"question": question, "context": context, "insufficient": INSUFFICIENT_MSG}
            )
            ans = self._invoke_text(msg)
            return ans or INSUFFICIENT_MSG

        if is_participation_question(question):
            msg = self.participation_prompt.invoke(
                {"question": question, "context": context, "insufficient": INSUFFICIENT_MSG}
            )
            ans = self._invoke_text(msg)
            return ans or INSUFFICIENT_MSG

        if is_projects_question(question):
            msg = self.projects_prompt.invoke(
                {"question": question, "context": context, "insufficient": INSUFFICIENT_MSG}
            )
            ans = self._invoke_text(msg)
            return ans or INSUFFICIENT_MSG

        if is_list_question(question):
            msg = self.list_prompt.invoke(
                {"question": question, "context": context, "insufficient": INSUFFICIENT_MSG}
            )
            ans = self._invoke_text(msg)
            return ans or INSUFFICIENT_MSG

        if is_fact_question(question):
            msg = self.fact_prompt.invoke(
                {"question": question, "context": context, "insufficient": INSUFFICIENT_MSG}
            )
            ans = self._invoke_text(msg)
            return ans or INSUFFICIENT_MSG

        history = build_history(previous_question, previous_answer)
        msg = self.gen_prompt.invoke(
            {
                "question": question,
                "context": context,
                "history": history,
                "insufficient": INSUFFICIENT_MSG,
            }
        )
        ans = self._invoke_text(msg)
        return ans or INSUFFICIENT_MSG

    def _refocus_answer(self, question: str, context: str) -> str:
        msg = self.strict_refocus_prompt.invoke(
            {"question": question, "context": context, "insufficient": INSUFFICIENT_MSG}
        )
        return clean_answer(self._invoke_text(msg))

    @staticmethod
    def _social_response(question: str, previous_answer: str | None = None) -> str:
        q = normalize_text(question)
        if "bom dia" in q:
            return "Bom dia! Pode mandar sua pergunta sobre os Titãs da Robótica."
        if "boa tarde" in q:
            return "Boa tarde! Estou pronto para te ajudar com as informações da equipe."
        if "boa noite" in q:
            return "Boa noite! Pode perguntar que eu te ajudo com a base dos Titãs da Robótica."
        if any(k in q for k in ("obrigad", "valeu")):
            return "De nada! Se quiser, posso aprofundar qualquer ponto ou trazer a resposta em formato de lista."
        if any(k in q for k in ("tchau", "falou")):
            return "Até mais! Quando quiser, é só voltar com outra pergunta sobre os Titãs da Robótica."
        if any(k in q for k in ("oi", "ola", "olá")):
            return "Oi! Pode mandar sua pergunta sobre a equipe Titãs da Robótica."
        if any(k in q for k in ("entendi", "que legal", "legal", "bacana", "massa", "top", "show")):
            if previous_answer:
                return "Que bom! Se quiser, eu também posso detalhar isso por ano, categoria ou participantes."
            return "Que bom! Pode mandar a próxima pergunta e eu continuo te ajudando."
        return "Perfeito. Se quiser, posso continuar e aprofundar o próximo ponto."

    def _conversational_response(
        self,
        question: str,
        previous_question: str | None,
        previous_answer: str | None,
    ) -> str | None:
        intent = conversational_intent(question)
        if intent == "none":
            return None
        if intent in {"greeting", "thanks", "bye", "ack", "confirm_short"}:
            return self._social_response(question, previous_answer)
        if intent == "reset_context":
            return "Perfeito, vamos começar um novo assunto. Pode mandar sua próxima pergunta."
        if intent == "continue":
            if not previous_answer:
                return "Claro. Me diga sobre qual ponto você quer que eu continue."
            return "Perfeito. Posso aprofundar por: contexto geral, resultados por ano, ou participantes. Me diga qual."
        if intent in {"summarize", "reformat", "shorter", "detailed"}:
            if not previous_answer:
                return "Consigo fazer isso, mas preciso de uma resposta anterior para transformar."
            base = previous_answer.split("Fontes usadas:")[0].strip()
            if intent == "summarize" or intent == "shorter":
                msg = (
                    "Reescreva de forma mais curta e objetiva em até 3 bullets, sem inventar fatos:\n\n"
                    f"{base}"
                )
            elif intent == "reformat":
                msg = (
                    "Reescreva em bullets claros (um ponto por linha), sem inventar fatos:\n\n"
                    f"{base}"
                )
            else:
                msg = (
                    "Reescreva com mais detalhes e melhor explicação, sem inventar fatos:\n\n"
                    f"{base}"
                )
            transformed = self._invoke_text(msg).strip()
            return clean_answer(transformed) if transformed else base
        return None

    @staticmethod
    def _extract_list_items(answer: str) -> list[str]:
        lines = [ln.strip() for ln in answer.splitlines() if ln.strip()]
        items: list[str] = []
        for ln in lines:
            raw = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", ln).strip()
            if raw:
                items.append(raw)
        if not items and "," in answer:
            items = [p.strip() for p in answer.split(",") if p.strip()]
        return items

    def _postprocess_list_equivalences(self, question: str, answer: str, context: str) -> str:
        if not is_list_question(question):
            return answer
        if normalize_text(answer) == normalize_text(INSUFFICIENT_MSG):
            return answer

        items = self._extract_list_items(answer)
        if not items:
            return answer

        # Primeira deduplicacao textual simples.
        unique_items = dedupe_keep_order(items)
        if len(unique_items) <= 1:
            return "\n".join(f"- {it}" for it in unique_items) if unique_items else answer

        # Segunda deduplicacao semantica (LLM), valida para qualquer tipo de listagem.
        items_text = "\n".join(f"- {it}" for it in unique_items)
        try:
            msg = self.list_canonicalization_prompt.invoke(
                {
                    "question": question,
                    "context": context,
                    "items": items_text,
                    "insufficient": INSUFFICIENT_MSG,
                }
            )
            normalized = clean_answer(self._invoke_text(msg))
        except Exception:
            normalized = ""

        if not normalized or normalize_text(normalized) == normalize_text(INSUFFICIENT_MSG):
            return "\n".join(f"- {it}" for it in unique_items)

        normalized_items = self._extract_list_items(normalized)
        normalized_items = dedupe_keep_order(normalized_items)
        if not normalized_items:
            return "\n".join(f"- {it}" for it in unique_items)
        return "\n".join(f"- {it}" for it in normalized_items)

    def ask(
        self,
        question: str,
        previous_question: str | None = None,
        previous_answer: str | None = None,
    ) -> ChatResult:
        conversational = self._conversational_response(question, previous_question, previous_answer)
        if conversational is not None:
            return ChatResult(
                answer=conversational,
                chunks=[],
                retrieval_query="conversational_intent",
            )

        if is_social_message(question):
            social = self._social_response(question, previous_answer)
            return ChatResult(answer=social, chunks=[], retrieval_query="social_message")

        retrieval_query = self._build_retrieval_query(question, previous_question, previous_answer)
        chunks = self._retrieve_with_expansion(question, retrieval_query)
        chunks = filter_team_relevant_chunks(
            question=question,
            chunks=chunks,
            max_chunks_for_context=self.settings.max_chunks_for_context,
            min_chunks=self.settings.min_chunks,
            student_list_max_chunks=STUDENT_LIST_MAX_CHUNKS,
        )
        if not chunks:
            return ChatResult("Nao foi possivel encontrar informacoes relevantes na base.", [], retrieval_query)

        if is_student_list_question(question):
            names = extract_student_names_from_chunks(chunks, question, STUDENT_LIST_MAX_CHUNKS)
            if names:
                lines = "\n".join(f"- {n}" for n in names)
                source_chunks = chunks[:STUDENT_LIST_SOURCE_IDS]
                used_ids = list(range(1, min(STUDENT_LIST_SOURCE_IDS, len(source_chunks)) + 1))
                answer = normalize_sources(lines, source_chunks, used_ids=used_ids)
                return ChatResult(answer=answer, chunks=source_chunks, retrieval_query=retrieval_query)

        selected_chunks = self._select_evidence_chunks(question, chunks)
        context = build_context(selected_chunks)

        candidate = self._generate_candidate(
            question, context, previous_question, previous_answer
        )
        candidate = clean_answer(candidate)
        if candidate == INSUFFICIENT_MSG and has_min_evidence(selected_chunks):
            candidate = self._extractive_fallback_answer(question, selected_chunks, query_hint=retrieval_query)

        audit = self._audit_answer(
            question=question,
            answer=candidate,
            context=context,
            limit_ids=len(selected_chunks),
        )

        answer = audit.answer if audit.status in {"OK", "FIX"} else candidate
        if answer == INSUFFICIENT_MSG and has_min_evidence(selected_chunks):
            answer = self._extractive_fallback_answer(question, selected_chunks, query_hint=retrieval_query)
        if not answer_targets_question(question, answer):
            answer = self._refocus_answer(question, context)
            if answer == INSUFFICIENT_MSG and has_min_evidence(selected_chunks):
                answer = self._extractive_fallback_answer(question, selected_chunks, query_hint=retrieval_query)
        answer = self._enforce_team_scope(question, answer, context)
        answer = self._postprocess_list_equivalences(question, answer, context)
        answer = normalize_sources(answer, selected_chunks, used_ids=audit.used_ids)
        return ChatResult(answer=answer, chunks=selected_chunks, retrieval_query=retrieval_query)

    def review_last_answer(
        self,
        question: str,
        previous_answer: str,
        feedback: str,
        previous_question: str | None = None,
    ) -> ChatResult:
        retrieval_query = self._build_retrieval_query(question, previous_question, previous_answer)
        chunks = self._retrieve_with_expansion(question, retrieval_query)
        chunks = filter_team_relevant_chunks(
            question=question,
            chunks=chunks,
            max_chunks_for_context=self.settings.max_chunks_for_context,
            min_chunks=self.settings.min_chunks,
            student_list_max_chunks=STUDENT_LIST_MAX_CHUNKS,
        )
        if not chunks:
            return ChatResult("Nao consegui validar a resposta anterior com os dados da base.", [], retrieval_query)

        selected_chunks = self._select_evidence_chunks(question, chunks)
        context = build_context(selected_chunks)
        msg = self.review_prompt.invoke(
            {
                "question": question,
                "previous_answer": previous_answer,
                "feedback": feedback,
                "context": context,
                "insufficient": INSUFFICIENT_MSG,
            }
        )
        revised = self._invoke_text(msg)
        revised = clean_answer(revised)
        if revised == INSUFFICIENT_MSG and has_min_evidence(selected_chunks):
            revised = self._extractive_fallback_answer(question, selected_chunks, query_hint=retrieval_query)

        audit = self._audit_answer(
            question=question,
            answer=revised,
            context=context,
            limit_ids=len(selected_chunks),
        )
        answer = audit.answer if audit.status in {"OK", "FIX"} else revised
        if answer == INSUFFICIENT_MSG and has_min_evidence(selected_chunks):
            answer = self._extractive_fallback_answer(question, selected_chunks, query_hint=retrieval_query)
        if not answer_targets_question(question, answer):
            answer = self._refocus_answer(question, context)
            if answer == INSUFFICIENT_MSG and has_min_evidence(selected_chunks):
                answer = self._extractive_fallback_answer(question, selected_chunks, query_hint=retrieval_query)
        answer = self._enforce_team_scope(question, answer, context)
        answer = self._postprocess_list_equivalences(question, answer, context)
        answer = normalize_sources(answer, selected_chunks, used_ids=audit.used_ids)
        return ChatResult(answer=answer, chunks=selected_chunks, retrieval_query=retrieval_query)
