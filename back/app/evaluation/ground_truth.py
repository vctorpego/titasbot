from __future__ import annotations

"""Verdade derivada do gabarito: cobertura de fatos-chave.

Para comparar metricas (tradicionais x LLM) cada metrica e tratada como um
classificador de "resposta correta / incorreta". A "verdade" contra a qual elas
sao medidas vem do gabarito oficial, decomposto em FATOS-CHAVE curados
(`tests/evals/metric_eval_annotations.json`, revisado por humano):

    cobertura = fatos do gabarito encontrados na resposta / total de fatos
    rotulo    = 1 (correta) se cobertura >= minimo do tipo de resposta, senao 0

ATENCAO a orientacao dos rotulos: 1 = CORRETA, 0 = INCORRETA (o projeto de
referencia invertia isso; ha teste unitario garantindo a orientacao aqui).

Tipos de fato (campo `kind` na anotacao):
- "terms":     `all` = lista de grupos; cada grupo e uma lista de alternativas e
               pelo menos uma alternativa de CADA grupo precisa aparecer.
               Alternativa comecando com "re:" e regex sobre o texto normalizado.
- "name":      nome de pessoa; casa primeiro nome + um sobrenome (tolerante a
               nomes do meio omitidos).
- "placement": linha de resultado "Modalidade: 1° lugar — COMPETICAO (Nivel)";
               modalidade, colocacao e competicao precisam estar no mesmo trecho.

`scope`: "answer" procura na resposta inteira; "line" exige que todos os grupos
estejam no mesmo trecho (linha + cabecalhos acima dela).
"""

import csv
import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Sequence

from app.infrastructure.text_utils import normalize_text

LABEL_CORRECT = 1
LABEL_INCORRECT = 0

ANSWER_TYPES = ("fato_curto", "descritiva", "lista_curta", "lista_longa")

# Cobertura minima para a resposta ser considerada correta, por tipo.
DEFAULT_MIN_COVERAGE: dict[str, float] = {
    "fato_curto": 1.0,
    "descritiva": 0.75,
    "lista_curta": 0.8,
    "lista_longa": 0.8,
}

_NAME_PARTICLES = {"de", "da", "do", "das", "dos", "e"}
# Segundo nome muito comum como nome composto: nao serve para identificar a pessoa.
_COMMON_GIVEN_NAMES = {
    "pedro", "clara", "luiza", "luisa", "henrique", "eduardo", "guilherme", "lucas",
    "vitor", "victor", "paulo", "gabriel", "fernando", "carlos", "cesar", "antonio",
    "felipe", "gustavo", "maria", "luis", "luiz", "ricardo", "raquel", "talia",
    "alberto", "tadeu", "regina", "vitor", "hugo", "andre", "jose", "joao",
}
_GIVEN_NAME_VARIANTS = {"luis": "lui[sz]", "luiz": "lui[sz]", "alan": "all?an", "allan": "all?an"}
_SURNAME_VARIANTS = {"vendramin": "vendramini?", "vendramini": "vendramini?"}

_ORDINAL_WORDS = {1: "primeir[oa]", 2: "segund[oa]", 3: "terceir[oa]", 4: "quart[oa]", 5: "quint[oa]"}

_MODALITY_ALIASES = {
    "futebol 2d": r"futebol\s*2d|futebol|soccer\s*2d|2d",
    "robocup soccer": r"soccer|futebol",
    "cospace": r"co\s*space",
    "superteam": r"super\s*team",
    "robocup rescue": r"rescue",
    "rescue line": r"rescue",
    "pratica": r"pratica",
    "teorica": r"teorica",
}
_COMPETITION_ALIASES = {
    "ironcup": r"iron\s*cup",
    "larc": r"larc|latin\s+american",
    "robocup": r"robo\s*cup|mundial",
    "obr": r"obr|olimpiada\s+brasileira\s+de\s+robotica",
    "cbr": r"cbr|competicao\s+brasileira\s+de\s+robotica",
    "trufes": r"trufes|torneio\s+de\s+robotica\s+da\s+ufes",
}
_LEVEL_ALIASES = {
    "regional": r"regional|estadual",
    "nacional": r"nacional",
    "internacional": r"internacional",
    "mundial": r"mundial",
}


@dataclass(frozen=True)
class KeyFact:
    text: str
    kind: str = "terms"
    groups: tuple[tuple[str, ...], ...] = ()
    scope: str = "answer"
    with_level: bool = False


@dataclass(frozen=True)
class MetricEvalCase:
    id: str
    number: int
    category: str
    question: str
    expected_output: str
    answer_type: str
    key_facts: tuple[KeyFact, ...]
    min_coverage: float


@dataclass(frozen=True)
class CoverageResult:
    coverage: float
    found: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Carregamento
# ---------------------------------------------------------------------------


def load_metric_cases(annotations_path: Path, official_cases_path: Path) -> list[MetricEvalCase]:
    annotations = json.loads(annotations_path.read_text(encoding="utf-8"))
    official = json.loads(official_cases_path.read_text(encoding="utf-8"))
    if not isinstance(annotations, list) or not isinstance(official, list):
        raise ValueError("Anotacoes e casos oficiais devem ser listas JSON.")

    official_by_id = {str(case.get("id")): case for case in official}
    cases: list[MetricEvalCase] = []
    for idx, raw in enumerate(annotations, start=1):
        case_id = str(raw.get("id", "")).strip()
        source = official_by_id.get(case_id)
        if source is None:
            raise ValueError(f"Anotacao #{idx}: caso oficial nao encontrado: {case_id}")
        answer_type = str(raw.get("answer_type", "")).strip()
        if answer_type not in ANSWER_TYPES:
            raise ValueError(f"Anotacao {case_id}: answer_type invalido {answer_type!r}")
        facts = tuple(_parse_fact(case_id, fact) for fact in raw.get("key_facts", []))
        if not facts:
            raise ValueError(f"Anotacao {case_id}: key_facts vazio.")
        min_coverage = float(raw.get("min_coverage", DEFAULT_MIN_COVERAGE[answer_type]))
        cases.append(
            MetricEvalCase(
                id=case_id,
                number=int(source["number"]),
                category=str(source["category"]),
                question=str(source["question"]).strip(),
                expected_output=str(source["expected_output"]).strip(),
                answer_type=answer_type,
                key_facts=facts,
                min_coverage=min_coverage,
            )
        )
    return sorted(cases, key=lambda case: case.number)


def _parse_fact(case_id: str, raw: Any) -> KeyFact:
    if isinstance(raw, str):
        raw = {"text": raw, "kind": "terms", "all": [[raw]]}
    if not isinstance(raw, dict) or not str(raw.get("text", "")).strip():
        raise ValueError(f"Anotacao {case_id}: fato-chave invalido: {raw!r}")
    kind = str(raw.get("kind", "terms"))
    text = str(raw["text"]).strip()
    if kind == "terms":
        groups = tuple(tuple(str(alt) for alt in group) for group in raw.get("all", []))
        if not groups or any(not group for group in groups):
            raise ValueError(f"Anotacao {case_id}: fato {text!r} sem grupos de termos.")
        return KeyFact(text=text, kind=kind, groups=groups, scope=str(raw.get("scope", "answer")))
    if kind == "name":
        return KeyFact(text=text, kind=kind, groups=(("re:" + name_pattern(text),),), scope="answer")
    if kind == "placement":
        with_level = bool(raw.get("with_level", False))
        return KeyFact(
            text=text,
            kind=kind,
            groups=placement_groups(text, with_level=with_level),
            scope="line",
            with_level=with_level,
        )
    raise ValueError(f"Anotacao {case_id}: kind desconhecido {kind!r}")


# ---------------------------------------------------------------------------
# Normalizacao e construcao de padroes
# ---------------------------------------------------------------------------


def normalize_for_match(text: str) -> str:
    """Minusculas, sem acentos, sem marcadores de ordinal e pontuacao -> espacos."""
    text = (text or "").replace("º", " ").replace("°", " ").replace("ª", " ")
    text = normalize_text(text)
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def name_pattern(name: str) -> str:
    """Regex: primeiro nome, ate 4 palavras quaisquer, e um sobrenome identificador."""
    tokens = [tok for tok in normalize_for_match(name).split() if tok not in _NAME_PARTICLES]
    if len(tokens) < 2:
        return rf"\b{re.escape(tokens[0])}\b" if tokens else r"(?!)"
    first = _GIVEN_NAME_VARIANTS.get(tokens[0], re.escape(tokens[0]))
    surnames = tokens[2:] if len(tokens) >= 3 else tokens[1:]
    if len(tokens) >= 3 and tokens[1] not in _COMMON_GIVEN_NAMES:
        surnames = [tokens[1], *surnames]
    alternatives = "|".join(_SURNAME_VARIANTS.get(s, re.escape(s)) for s in surnames)
    return rf"\b{first}\b(?:\s+\w+){{0,4}}?\s+(?:{alternatives})\b"


def ordinal_pattern(position: int) -> str:
    """Regex para "N° lugar" (aceita "1 e 2 lugar", "1o lugar", "primeiro lugar")."""
    parts = [rf"(?<![\d]){position}o?\s+(?:(?:e\s+)?\d+o?\s+)*(?:lugar|colocad[oa]|colocacao)"]
    if position in _ORDINAL_WORDS:
        parts.append(rf"\b{_ORDINAL_WORDS[position]}\s+(?:lugar|colocad[oa])")
    if position == 1:
        parts.append(r"\bcampe(?:ao|a|oes|as)\b")
    return "|".join(parts)


_PLACEMENT_RE = re.compile(
    r"^(?P<mod>[^:]+):\s*(?P<res>.+?)\s*[—–-]\s*(?P<comp>[^()]+?)\s*(?:\((?P<level>[^)]+)\))?\s*$"
)


def placement_groups(text: str, with_level: bool = False) -> tuple[tuple[str, ...], ...]:
    match = _PLACEMENT_RE.match(text.strip())
    if not match:
        raise ValueError(f"Linha de resultado fora do formato esperado: {text!r}")
    modality = normalize_for_match(match.group("mod"))
    result = normalize_for_match(match.group("res"))
    competition = normalize_for_match(match.group("comp"))
    level = normalize_for_match(match.group("level") or "")

    groups: list[tuple[str, ...]] = [
        ("re:" + _MODALITY_ALIASES.get(modality, re.escape(modality).replace(r"\ ", r"\s*")),),
        ("re:" + _result_pattern(result),),
        ("re:" + _COMPETITION_ALIASES.get(competition, re.escape(competition)),),
    ]
    if with_level and level:
        groups.append(("re:" + _LEVEL_ALIASES.get(level, re.escape(level)),))
    return tuple(groups)


def _result_pattern(result: str) -> str:
    ordinal = re.match(r"^(\d+)\s+lugar$", result)
    if ordinal:
        return ordinal_pattern(int(ordinal.group(1)))
    for medal in ("bronze", "prata", "ouro"):
        if medal in result:
            return medal
    if "honra" in result:
        return r"honra|mencao\s+honrosa"
    return re.escape(result)


@lru_cache(maxsize=4096)
def _compile(alternative: str) -> re.Pattern[str]:
    if alternative.startswith("re:"):
        return re.compile(alternative[3:])
    phrase = normalize_for_match(alternative)
    return re.compile(rf"(?<!\w){re.escape(phrase)}(?!\w)")


# ---------------------------------------------------------------------------
# Casamento e cobertura
# ---------------------------------------------------------------------------


def _is_header(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return (
        stripped.endswith(":")
        or stripped.startswith("#")
        or bool(re.fullmatch(r"\*\*[^*]+\*\*:?", stripped))
    )


def answer_segments(answer: str) -> list[str]:
    """Trechos normalizados: cada linha concatenada aos ate 2 cabecalhos acima dela.

    Assim "LARC 2017:\\n- CoSpace: 1° lugar" ainda casa a competicao com o item.
    """
    segments: list[str] = []
    headers: list[str] = []
    for raw_line in re.split(r"[\n;]+", answer or ""):
        line = raw_line.strip()
        if not line:
            continue
        if _is_header(line):
            headers = (headers + [line])[-2:]
        segments.append(normalize_for_match(" ".join([*headers, line])))
    return segments


def fact_matched(answer: str, fact: KeyFact) -> bool:
    if fact.scope == "line":
        segments = answer_segments(answer)
    else:
        segments = [normalize_for_match(answer)]
    for segment in segments:
        if all(any(_compile(alt).search(segment) for alt in group) for group in fact.groups):
            return True
    return False


def key_fact_coverage(answer: str, facts: Sequence[KeyFact]) -> CoverageResult:
    if not facts:
        return CoverageResult(coverage=0.0)
    found: list[str] = []
    missing: list[str] = []
    for fact in facts:
        (found if fact_matched(answer, fact) else missing).append(fact.text)
    return CoverageResult(coverage=round(len(found) / len(facts), 6), found=found, missing=missing)


def truth_label(coverage: float, min_coverage: float) -> int:
    """1 = CORRETA (cobertura suficiente), 0 = INCORRETA."""
    return LABEL_CORRECT if coverage >= min_coverage - 1e-9 else LABEL_INCORRECT


def load_label_overrides(path: Path) -> dict[str, int]:
    """Le `rotulos_revisados.csv` (answer_key;label) com rotulos revisados por humano.

    label aceita 1/0, correta/incorreta. Linhas vazias ou invalidas sao ignoradas.
    """
    if not path.exists():
        return {}
    overrides: dict[str, int] = {}
    with path.open(encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp, delimiter=";")
        for row in reader:
            key = (row.get("answer_key") or "").strip()
            label = (row.get("label") or "").strip().lower()
            if not key:
                continue
            if label in {"1", "correta", "correto", "true", "sim"}:
                overrides[key] = LABEL_CORRECT
            elif label in {"0", "incorreta", "incorreto", "false", "nao", "não"}:
                overrides[key] = LABEL_INCORRECT
    return overrides
