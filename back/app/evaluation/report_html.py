from __future__ import annotations

"""Paginas HTML do visualizador de avaliacao (autossuficientes, sem CDN).

- write_comparacao_html: compara os modelos (com RAG vs sem RAG), com o melhor
  threshold por celula e a tabela completa de metricas de classificacao.
- write_como_funciona_html: explica as duas metodologias e as condicoes.

Inspirado no projeto de referencia (comparacao_metricas_avaliadores.html /
como_funciona.html), reproduzindo a estrutura sem depender dos arquivos originais.
"""

import html
from pathlib import Path
from typing import Any, Sequence

_STYLE = """
  :root { color-scheme: light; }
  body { font-family: Arial, Helvetica, sans-serif; margin: 0; background: #f6f7fb; color: #111827; }
  main { max-width: 1180px; margin: 0 auto; padding: 32px 20px; }
  h1 { margin: 0 0 8px; }
  h2 { margin: 28px 0 10px; }
  p.lead { color: #4b5563; margin-top: 0; }
  nav { margin: 8px 0 20px; }
  nav a { margin-right: 16px; color: #2563eb; text-decoration: none; }
  .table-wrap { overflow-x: auto; background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 12px; }
  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  th, td { padding: 9px 12px; border-bottom: 1px solid #e5e7eb; text-align: left; white-space: nowrap; }
  th { background: #f9fafb; position: sticky; top: 0; }
  tbody tr:hover { background: #f3f4f6; }
  .muted { color: #6b7280; }
  .note { background: #fff7ed; border: 1px solid #fed7aa; border-radius: 8px; padding: 12px 16px; color: #9a3412; }
  .tag { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 12px; background: #eef2ff; color: #3730a3; }
"""


def _fmt(value: Any) -> str:
    if isinstance(value, bool):
        return "sim" if value else "nao"
    if isinstance(value, float):
        return f"{value:.4f}"
    if value is None:
        return ""
    return str(value)


def _table(
    rows: Sequence[dict[str, Any]],
    columns: Sequence[str],
    headers: Sequence[str],
    empty_note: str = "Sem dados.",
) -> str:
    if not rows:
        return f'<p class="muted">{html.escape(empty_note)}</p>'
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{html.escape(_fmt(row.get(col)))}</td>" for col in columns)
        body_rows.append(f"<tr>{cells}</tr>")
    body = "\n".join(body_rows)
    return (
        '<div class="table-wrap"><table><thead><tr>'
        + head
        + "</tr></thead><tbody>"
        + body
        + "</tbody></table></div>"
    )


def _page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <style>{_STYLE}</style>
</head>
<body>
  <main>{body}</main>
</body>
</html>
"""


def write_comparacao_html(
    path: Path,
    summary: Sequence[dict[str, Any]],
    reference_threshold_rows: Sequence[dict[str, Any]],
) -> None:
    """Pagina de comparacao dos modelos (com RAG vs sem RAG)."""
    summary_tbl = _table(
        summary,
        ["model", "condition", "total_evaluated", "passed", "pass_rate", "avg_score", "avg_ref_score"],
        ["Modelo", "Condicao", "Avaliados", "Aprovados (DeepEval)", "Taxa aprovacao", "Score medio (DeepEval)", "Score medio (ref.)"],
        empty_note="Sem resumo (nenhum caso avaliado).",
    )

    reference_tbl = _table(
        reference_threshold_rows,
        ["model", "condition", "threshold", "total_evaluated", "passed", "pass_rate", "avg_score"],
        ["Modelo", "Condicao", "Threshold", "Avaliados", "Aprovados", "Taxa aprovacao", "Score medio"],
        empty_note="Sem metricas de referencia (sentence-transformers indisponivel).",
    )

    body = f"""
    <h1>Comparacao de metricas - TitasBot</h1>
    <p class="lead">Comparacao dos modelos por provedor, nas condicoes <span class="tag">com RAG</span>
    e <span class="tag">sem RAG</span>, sempre contra o gabarito das perguntas de teste.</p>
    <nav><a href="avaliacao_modelos.html">Respostas detalhadas</a><a href="como_funciona.html">Como funciona</a></nav>

    <h2>Resumo por modelo e condicao (DeepEval)</h2>
    {summary_tbl}

    <h2>Taxa de aprovacao por threshold (avaliador de referencia)</h2>
    <p class="muted">Score de similaridade semantica+lexical vs. gabarito (sem LLM). Para cada
    threshold, mostra quantas respostas tem score &ge; threshold.</p>
    {reference_tbl}
    """
    path.write_text(_page("Comparacao de metricas - TitasBot", body), encoding="utf-8")


def write_como_funciona_html(path: Path) -> None:
    """Pagina explicativa das metodologias de avaliacao."""
    body = """
    <h1>Como funciona a avaliacao</h1>
    <p class="lead">Cada modelo responde as mesmas perguntas do conjunto de teste, em duas condicoes,
    e as respostas sao pontuadas por duas metodologias em paralelo.</p>
    <nav><a href="avaliacao_modelos.html">Respostas detalhadas</a><a href="comparacao_metricas.html">Comparacao de metricas</a></nav>

    <h2>Modelos comparados</h2>
    <p>Provedores diferentes (hoje: OpenAI, Anthropic/Claude e DeepSeek). Os embeddings e a
    recuperacao (RAG) sao os mesmos para todos (OpenAI), de modo que apenas o modelo gerador
    muda &mdash; comparacao justa.</p>

    <h2>Condicoes: com RAG vs sem RAG</h2>
    <ul>
      <li><strong>Com RAG:</strong> o modelo responde usando o contexto recuperado da base de conhecimento
      (livro/artigos da equipe Titas da Robotica).</li>
      <li><strong>Sem RAG:</strong> o modelo responde apenas com o proprio conhecimento, sem contexto &mdash;
      util para medir o quanto o RAG contribui.</li>
    </ul>

    <h2>Metodologia 1 - DeepEval (juiz LLM)</h2>
    <p>Metricas assistidas por LLM: <strong>Correctness</strong> (fidelidade a resposta esperada),
    <strong>Answer Relevancy</strong>, <strong>Faithfulness</strong> (fidelidade ao contexto
    recuperado -- so roda com RAG) e <strong>Hallucination</strong> (alucinacao). Cada metrica
    produz um score em [0,1] e um veredito de aprovacao dado um limiar.</p>

    <h2>Fidelidade vs. Alucinacao -- nao sao a mesma coisa</h2>
    <ul>
      <li><strong>Faithfulness (fidelidade ao contexto):</strong> compara a resposta com o que foi
      de fato <em>recuperado</em> pelo RAG. So roda na condicao com RAG (sem RAG nao ha contexto
      recuperado para comparar).</li>
      <li><strong>Hallucination (alucinacao):</strong> compara a resposta com o <em>gabarito</em>
      (resposta esperada), nas duas condicoes (com e sem RAG) -- por isso e sempre calculada,
      mesmo sem RAG. Atencao: o veredito e invertido em relacao as outras metricas
      (<code>score &le; limiar</code> = aprovado; quanto menor, melhor).</li>
    </ul>

    <h2>Metodologia 2 - Similaridade (projeto de referencia)</h2>
    <p>Compara a resposta com o gabarito por:</p>
    <ul>
      <li><strong>Semantica (80%)</strong>: cosseno entre embeddings do modelo multilingue
      <code>paraphrase-multilingual-MiniLM-L12-v2</code>.</li>
      <li><strong>Lexica (20%)</strong>: ROUGE-L (F-measure) sobre as palavras do texto.</li>
    </ul>
    <p><code>score_final = 0.8 &times; semantica + 0.2 &times; lexica</code></p>
    <p>Nao usa LLM nenhum: e um calculo puramente determinístico contra o gabarito. E reportado
    como nota media (0 a 1) e como taxa de aprovacao em varios thresholds fixos
    (<code>score_final &ge; threshold</code>) &mdash; sem comparar contra nenhum rotulo de verdade
    externo, so contagem direta.</p>

    <p class="note">Observacao: as duas metodologias comparam a resposta direto com o gabarito das
    perguntas de teste. Nenhuma delas usa um LLM para gerar um rotulo de correto/incorreto por fora
    do gabarito.</p>
    """
    path.write_text(_page("Como funciona a avaliacao - TitasBot", body), encoding="utf-8")
