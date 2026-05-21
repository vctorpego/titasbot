from __future__ import annotations

import re
from pathlib import Path

from app.domain.intents import is_full_student_list_request
from app.infrastructure.retrieval import RetrievedChunk
from app.infrastructure.text_utils import normalize_text


def _target_team(question: str) -> str | None:
    q = normalize_text(question)
    aliases = {
        "futebol 2d": ("futebol 2d", "2d"),
        "cospace": ("cospace",),
        "drone": ("drone",),
        "osorin": ("osorin",),
        "pratica": ("pratica",),
        "sek": ("sek",),
        "teorica": ("teorica",),
        "adm": ("adm", "administrativa"),
    }
    for team, terms in aliases.items():
        if any(term in q for term in terms):
            return team
    return None


def _target_year(question: str) -> str | None:
    match = re.search(r"\b(?:19|20)\d{2}\b", question)
    return match.group(0) if match else None


def _load_neighbor_page_text(chunks: list[RetrievedChunk]) -> str:
    texts: list[str] = []
    by_source: dict[str, set[int]] = {}
    for chunk in chunks:
        if chunk.doc_kind != "table" or chunk.page is None:
            continue
        by_source.setdefault(chunk.source, set()).add(chunk.page)

    for source, pages in by_source.items():
        source_path = Path(source)
        if not source_path.exists():
            continue
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(source_path), strict=False)
        except Exception:
            continue

        wanted_pages: set[int] = set()
        for page in pages:
            for neighbor in range(max(0, page - 1), min(len(reader.pages), page + 3)):
                wanted_pages.add(neighbor)

        for page in sorted(wanted_pages):
            try:
                text = reader.pages[page].extract_text() or ""
            except Exception:
                text = ""
            if text.strip():
                texts.append(text)

    return "\n".join(texts)


def _target_sections(text: str, team: str, year: str) -> list[str]:
    sections: list[str] = []
    current: list[str] = []
    in_section = False

    for line in text.splitlines():
        line_norm = normalize_text(line)
        is_integrantes_heading = "integrantes da equipe" in line_norm and year in line_norm
        is_target_heading = is_integrantes_heading and team in line_norm

        if is_target_heading:
            if current:
                sections.append("\n".join(current))
            current = [line]
            in_section = True
            continue

        if not in_section:
            continue

        starts_other_section = (
            "tabela de integrantes da equipe" in line_norm
            and (team not in line_norm or year not in line_norm)
        )
        starts_other_table = "tabela de podios" in line_norm or "tabela de orientadores" in line_norm
        if starts_other_section or starts_other_table:
            if current:
                sections.append("\n".join(current))
            current = []
            in_section = False
            continue

        current.append(line)
        if "fonte:" in line_norm:
            sections.append("\n".join(current))
            current = []
            in_section = False

    if current:
        sections.append("\n".join(current))

    return sections


def _clean_name(candidate: str) -> str:
    candidate = re.sub(r"\s{2,}", " ", candidate).strip(" -\t")
    candidate = re.sub(r"\s+(Graduação|Graduacao|Ensino Médio|Ensino Medio)$", "", candidate).strip()
    return candidate


def extract_student_names_from_chunks(chunks: list[RetrievedChunk], question: str, max_chunks: int) -> list[str]:
    table_chunks = [c for c in chunks if c.doc_kind == "table"] or chunks
    table_chunks = table_chunks[:max_chunks]
    target_team = _target_team(question)
    target_year = _target_year(question)
    texts = [c.content for c in table_chunks]

    if target_team and target_year:
        page_text = _load_neighbor_page_text(table_chunks)
        if page_text:
            texts.insert(0, page_text)
        section_texts: list[str] = []
        for text in texts:
            section_texts.extend(_target_sections(text, target_team, target_year))
        if section_texts:
            texts = section_texts

    blocked_line_terms = (
        "tabela",
        "fonte",
        "temporada",
        "alunos nivel",
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

    name_pattern = (
        r"\b[A-ZÁÂÃÉÊÍÓÔÕÚÇ][a-záâãéêíóôõúç]+"
        r"(?:\s+(?:d[aeo]s?|e|[A-ZÁÂÃÉÊÍÓÔÕÚÇ][a-záâãéêíóôõúç]+)){1,8}\b"
    )
    names: list[str] = []
    seen = set()

    for text in texts:
        for raw_line in text.splitlines():
            line = re.sub(r"^\s*[\-\*\d\.\)\(]+\s*", "", raw_line).strip()
            if len(line) < 4:
                continue
            line_norm = normalize_text(line)
            if any(t in line_norm for t in blocked_line_terms):
                continue
            if any(t in line_norm for t in ("patrocin", "empresa", "orientador")):
                continue

            for match in re.findall(name_pattern, line):
                m = _clean_name(match)
                if len(m.split()) < 2 or len(m.split()) > 8:
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
