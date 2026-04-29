from __future__ import annotations

import re

from app.domain.intents import is_full_student_list_request
from app.infrastructure.retrieval import RetrievedChunk
from app.infrastructure.text_utils import normalize_text


def extract_student_names_from_chunks(chunks: list[RetrievedChunk], question: str, max_chunks: int) -> list[str]:
    table_chunks = [c for c in chunks if c.doc_kind == "table"] or chunks
    table_chunks = table_chunks[:max_chunks]

    blocked_line_terms = (
        "professor",
        "professora",
        "orientador",
        "orientadora",
        "patrocinador",
        "patrocinadores",
        "empresa",
        "empresas",
        "parceiro",
        "parceiros",
        "fornecedor",
        "fornecedores",
        "tecnico",
        "tecnica",
        "coordenador",
        "coordenadora",
    )
    blocked_name_terms = (
        "ifes",
        "campus",
        "robotica",
        "obr",
        "cbr",
        "robocup",
        "larc",
        "nasa",
        "governo",
        "secretaria",
        "universidade",
        "fabrica",
        "laboratorio",
        "digital",
        "informatica",
        "sistemas",
        "industria",
        "metalurgica",
        "cursos",
        "media",
        "fulltech",
        "seek",
        "siad",
        "frisa",
        "matriz",
        "moveedu",
    )

    name_pattern = r"\b[A-ZÁÂÃÉÊÍÓÔÕÚÇ][a-záâãéêíóôõúç]+(?:\s+[A-ZÁÂÃÉÊÍÓÔÕÚÇ][a-záâãéêíóôõúç]+){1,5}\b"
    names: list[str] = []
    seen = set()

    for chunk in table_chunks:
        for raw_line in chunk.content.splitlines():
            line = re.sub(r"^\s*[\-\*\d\.\)\(]+\s*", "", raw_line).strip()
            if len(line) < 4:
                continue
            line_norm = normalize_text(line)
            if any(t in line_norm for t in blocked_line_terms):
                continue
            if any(t in line_norm for t in ("patrocin", "empresa", "orientador")):
                continue

            for match in re.findall(name_pattern, line):
                m = re.sub(r"\s{2,}", " ", match).strip(" -\t")
                if len(m.split()) < 2 or len(m.split()) > 6:
                    continue
                if re.search(r"\d", m):
                    continue
                m_norm = normalize_text(m)
                if any(t in m_norm for t in blocked_name_terms):
                    continue
                if m_norm in {"equipe administrativa", "equipe pratica", "equipe teorica"}:
                    continue
                if m_norm in seen:
                    continue
                seen.add(m_norm)
                names.append(m)

    if not names:
        return []

    if is_full_student_list_request(question):
        names = sorted(names, key=normalize_text)

    return names
