from __future__ import annotations

"""Relatorio HTML do estudo comparativo de metricas (autossuficiente, sem CDN).

- comparacao_metricas.html: ranking, thresholds (global x estratificado),
  sistemas, recuperacao, socio-tecnico e explorador resposta a resposta
  (com revisao de rotulo exportavel para rotulos_revisados.csv).
- como_funciona.html: metodologia em linguagem simples.
"""

import html
import json
from pathlib import Path
from typing import Any

from app.evaluation.report_html import _STYLE as _BASE_STYLE

_STYLE = _BASE_STYLE + """
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin: 12px 0; }
  .card { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px 16px; }
  .card strong { display: block; font-size: 22px; margin-bottom: 4px; }
  .card span { color: #4b5563; font-size: 13px; }
  .fam-tradicional { background: #ecfdf5; color: #065f46; }
  .fam-llm { background: #eff6ff; color: #1e40af; }
  .ok { background: #dcfce7 !important; }
  .bad { background: #fee2e2 !important; }
  td.num { text-align: right; font-variant-numeric: tabular-nums; }
  .filters { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin: 10px 0; }
  .filters label { font-size: 13px; color: #374151; }
  select, button { font: inherit; padding: 4px 8px; }
  details { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px 12px; margin: 8px 0; }
  summary { cursor: pointer; font-weight: bold; }
  .answer-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px 16px; margin: 10px 0; }
  .answer-card pre { white-space: pre-wrap; font-family: inherit; margin: 4px 0; max-height: 260px; overflow: auto; background: #f9fafb; padding: 8px; border-radius: 6px; }
  .cols { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 10px; }
  .chips span { display: inline-block; margin: 2px; padding: 2px 8px; border-radius: 999px; font-size: 12px; }
  .bar { height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; min-width: 80px; }
  .bar i { display: block; height: 100%; background: #2563eb; }
  ul.tight li { margin: 4px 0; }
"""

_NAV = """<nav><a href="#ranking">Ranking</a><a href="#familias">Tradicional x LLM</a>
<a href="#thresholds">Thresholds</a><a href="#sistemas">Modelos</a><a href="#recuperacao">Recuperação</a>
<a href="#socio">Sócio-técnico</a><a href="#respostas">Respostas</a><a href="como_funciona.html">Como funciona</a></nav>"""


def _f(value: Any, digits: int = 3) -> str:
    if value is None:
        return "—"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{float(value):.{digits}f}"
    return html.escape(str(value))


def _pct(value: Any) -> str:
    return "—" if value is None else f"{float(value) * 100:.1f}%"


def _page(title: str, body: str) -> str:
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{html.escape(title)}</title><style>{_STYLE}</style></head><body><main>{body}</main></body></html>"
    )


def _ranking_table(analysis: dict[str, Any]) -> str:
    crit = analysis["criterio"]
    head = (
        "<tr><th>#</th><th>Métrica</th><th>Família</th><th>AUC</th><th>Spearman (cobertura)</th>"
        f"<th>{crit} global (CV)</th><th>{crit} estratificado (CV)</th><th>Ganho estratificação</th>"
        "<th>Threshold global</th><th>Thresholds por estrato</th><th>τ ranking modelos</th>"
        "<th>s/avaliação</th><th>Custo US$</th><th>Desvio entre execuções</th></tr>"
    )
    body = []
    for s in analysis["ranking"]:
        cv = s["validacao_cruzada"]
        glob = (cv.get("global") or {}).get(crit)
        strat = (cv.get("stratified") or {}).get(crit)
        gain = None if glob is None or strat is None else strat - glob
        gain_cls = "" if gain is None else ("ok" if gain > 0.005 else "bad" if gain < -0.005 else "")
        thresholds = ", ".join(f"{k}: {v:.2f}" for k, v in s["thresholds_por_estrato"].items())
        body.append(
            f"<tr><td>{s['posicao']}</td><td title='{html.escape(s['description'])}'><b>{html.escape(s['metric'])}</b></td>"
            f"<td><span class='tag fam-{s['family']}'>{s['family']}</span></td>"
            f"<td class='num'>{_f(s['auc'])}</td><td class='num'>{_f(s['correlacao_cobertura']['spearman'])}</td>"
            f"<td class='num'>{_f(glob)}</td><td class='num'>{_f(strat)}</td>"
            f"<td class='num {gain_cls}'>{'—' if gain is None else f'{gain:+.3f}'}</td>"
            f"<td class='num'>{_f(s['threshold_global'], 2)}</td><td>{html.escape(thresholds)}</td>"
            f"<td class='num'>{_f(s['ranking_sistemas']['kendall_tau'])}</td>"
            f"<td class='num'>{_f(s['segundos_medios'])}</td><td class='num'>{_f(s['custo_total_usd'], 4)}</td>"
            f"<td class='num'>{_f(s['estabilidade'].get('desvio_padrao_medio'))}</td></tr>"
        )
    scheme = analysis["ranking"][0]["validacao_cruzada"]["scheme"] if analysis["ranking"] else ""
    return (
        f"<p class='muted'>Ordenado pelo melhor {crit} fora da amostra ({html.escape(scheme)}), depois AUC. "
        "AUC 0,5 = acaso; 1,0 = separa perfeitamente respostas corretas de incorretas.</p>"
        f"<div class='table-wrap'><table><thead>{head}</thead><tbody>{''.join(body)}</tbody></table></div>"
    )


def _families(analysis: dict[str, Any]) -> str:
    fams = analysis["socio_tecnico"]["por_familia"]
    ranking = {s["metric"]: s for s in analysis["ranking"]}
    crit = analysis["criterio"]
    cards = []
    for family, label in (("tradicional", "Melhor métrica tradicional"), ("llm", "Melhor métrica com LLM")):
        stats = fams.get(family)
        if not stats or not stats["melhor_metrica"]:
            cards.append(f"<article class='card'><strong>—</strong><span>{label}: sem dados</span></article>")
            continue
        best = ranking[stats["melhor_metrica"]]
        cv = best["validacao_cruzada"]
        value = max(v for v in ((cv.get("global") or {}).get(crit), (cv.get("stratified") or {}).get(crit), -1) if v is not None)
        cards.append(
            f"<article class='card'><strong>{html.escape(best['metric'])}</strong>"
            f"<span>{label}<br>AUC {_f(best['auc'])} · {crit} (CV) {_f(value)}<br>"
            f"{_f(stats['segundos_medios_por_resposta'])} s/métrica · custo US$ {_f(stats['custo_total_usd'], 4)}</span></article>"
        )
    winner = analysis["ranking"][0] if analysis["ranking"] else None
    verdict = ""
    if winner:
        verdict = (
            f"<p class='note'>Neste experimento a métrica que mais concordou com o gabarito foi "
            f"<b>{html.escape(winner['metric'])}</b> (família <b>{winner['family']}</b>). "
            "Leia junto com custo, estabilidade e as discordâncias no explorador antes de concluir.</p>"
        )
    return f"<div class='cards'>{''.join(cards)}</div>{verdict}"


def _threshold_section(analysis: dict[str, Any]) -> str:
    cols = ["threshold", "n", "accuracy", "balanced_accuracy", "precision_correta", "recall_correta",
            "f1_correta", "precision_incorreta", "recall_incorreta", "f1_incorreta"]
    blocks = []
    crit = analysis["criterio"]
    for s in analysis["ranking"]:
        metric = s["metric"]
        inner = []
        for stratum, rows in analysis["sweeps"][metric].items():
            if not rows or rows[0]["n"] == 0:
                continue
            best = max(float(r[crit]) for r in rows)
            head = "".join(f"<th>{c}</th>" for c in cols)
            body = "".join(
                "<tr" + (" class='ok'" if float(r[crit]) == best else "") + ">"
                + "".join(f"<td class='num'>{_f(r[c], 2 if c == 'threshold' else 3) if c != 'n' else r[c]}</td>" for c in cols)
                + "</tr>"
                for r in rows
            )
            auc = s["auc"] if stratum == "global" else s["auc_por_estrato"].get(stratum)
            inner.append(
                f"<h4>{html.escape(stratum)} <span class='muted'>(AUC {_f(auc)})</span></h4>"
                f"<div class='table-wrap'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"
            )
        blocks.append(f"<details><summary>{html.escape(metric)} <span class='tag fam-{s['family']}'>{s['family']}</span></summary>{''.join(inner)}</details>")
    dist = analysis["distribuicao_estratos"]
    dist_rows = "".join(
        f"<tr><td>{k}</td><td class='num'>{v['respostas']}</td><td class='num'>{v['corretas']}</td></tr>" for k, v in dist.items()
    )
    return (
        "<p>Mesma leitura do projeto de referência (tabela por threshold), mas feita <b>para todas as respostas (global)</b> "
        "e <b>separadamente por tipo de resposta</b>. Linha verde = melhor threshold pelo critério.</p>"
        f"<div class='table-wrap'><table><thead><tr><th>Estrato</th><th>Respostas</th><th>Corretas (verdade)</th></tr></thead><tbody>{dist_rows}</tbody></table></div>"
        + "".join(blocks)
    )


def _systems_section(analysis: dict[str, Any]) -> str:
    metrics = [s["metric"] for s in analysis["ranking"]]
    head = "<tr><th>Sistema</th><th>Respostas</th><th>Corretas (verdade)</th><th>Cobertura média</th>" + "".join(
        f"<th>{html.escape(m)}</th>" for m in metrics
    ) + "</tr>"
    body = "".join(
        f"<tr><td><b>{html.escape(s['system'])}</b></td><td class='num'>{s['respostas']}</td>"
        f"<td class='num'>{_pct(s['taxa_correta_verdade'])}</td><td class='num'>{_f(s['cobertura_media'])}</td>"
        + "".join(f"<td class='num'>{_f(s['scores_medios'].get(m))}</td>" for m in metrics)
        + "</tr>"
        for s in analysis["sistemas"]
    )
    return (
        "<p>Comparação dos modelos medianos com e sem RAG. A coluna <i>Corretas (verdade)</i> vem do gabarito; "
        "as demais mostram a nota média que cada métrica deu. Uma boa métrica ordena os sistemas como a verdade (τ no ranking).</p>"
        f"<div class='table-wrap'><table><thead>{head}</thead><tbody>{body}</tbody></table></div>"
    )


def _retrieval_section(analysis: dict[str, Any]) -> str:
    rows = analysis["recuperacao"]
    if not rows:
        return "<p class='muted'>Sem respostas RAG com anotação de evidências.</p>"
    body = "".join(
        f"<tr><td>{html.escape(r['model'])}</td><td class='num'>{r['respostas_anotadas']}</td>"
        f"<td class='num'>{_pct(r['hit_at_5'])}</td><td class='num'>{_pct(r['precision_at_5'])}</td>"
        f"<td class='num'>{_pct(r['taxa_correta_com_hit'])}</td><td class='num'>{_pct(r['taxa_correta_sem_hit'])}</td></tr>"
        for r in rows
    )
    return (
        "<p>Métricas tradicionais de recuperação (Hit@5 e Precision@5) nas 20 perguntas com evidências anotadas. "
        "Não entram no ranking (avaliam a busca, não a resposta), mas mostram se o erro vem da recuperação ou da geração.</p>"
        "<div class='table-wrap'><table><thead><tr><th>Modelo</th><th>Respostas</th><th>Hit@5</th><th>Precision@5</th>"
        "<th>Corretas quando Hit=1</th><th>Corretas quando Hit=0</th></tr></thead>"
        f"<tbody>{body}</tbody></table></div>"
    )


def _socio_section(analysis: dict[str, Any]) -> str:
    st = analysis["socio_tecnico"]
    fam = st["por_familia"]
    trad = fam.get("tradicional", {})
    llm = fam.get("llm", {})
    people_rows = "".join(
        f"<tr><td>{html.escape(p['metric'])}</td><td><span class='tag fam-{p['family']}'>{p['family']}</span></td>"
        f"<td class='num'>{p['respostas_incorretas_sobre_pessoas']}</td><td class='num'>{p['aprovadas_indevidamente']}</td>"
        f"<td class='num'>{_pct(p['taxa'])}</td></tr>"
        for p in st["aprovacao_indevida_sobre_pessoas"]
    )
    rag_rows = "".join(
        f"<tr><td>{html.escape(model)}</td><td class='num'>{_pct(c.get('rag'))}</td><td class='num'>{_pct(c.get('no_rag'))}</td></tr>"
        for model, c in st["efeito_rag_na_verdade"].items()
    )
    return f"""
<p>O TitãsBot não é só um artefato técnico: responde, em nome de uma equipe de uma instituição pública,
sobre <b>pessoas reais</b> (alunos e orientadores) e sobre a história e os resultados da equipe.
A escolha da métrica de avaliação também tem consequências sociais e organizacionais. Os números abaixo são medidos neste experimento.</p>
<div class="cards">
  <article class="card"><strong>{_f(trad.get('segundos_medios_por_resposta'))} s × {_f(llm.get('segundos_medios_por_resposta'))} s</strong>
    <span>Tempo médio por avaliação: tradicional × LLM</span></article>
  <article class="card"><strong>US$ {_f(trad.get('custo_total_usd'), 2)} × US$ {_f(llm.get('custo_total_usd'), 4)}</strong>
    <span>Custo total de avaliação: tradicional × LLM (dependência de API paga)</span></article>
  <article class="card"><strong>{_f(llm.get('desvio_padrao_medio_entre_execucoes'))}</strong>
    <span>Desvio médio da nota DeepEval ao repetir a mesma avaliação (tradicionais: 0, determinísticas)</span></article>
  <article class="card"><strong>{st['respostas_sobre_pessoas_incorretas']} / {st['respostas_sobre_pessoas']}</strong>
    <span>Respostas sobre pessoas (listas de nomes) incorretas pela verdade</span></article>
</div>
<h3>Aprovação indevida de respostas erradas sobre pessoas</h3>
<p class="muted">Respostas incorretas que citam alunos/orientadores e que a métrica aprovaria no seu threshold global. Um nome omitido ou trocado afeta o reconhecimento de alguém.</p>
<div class="table-wrap"><table><thead><tr><th>Métrica</th><th>Família</th><th>Incorretas sobre pessoas</th><th>Aprovadas indevidamente</th><th>Taxa</th></tr></thead><tbody>{people_rows}</tbody></table></div>
<h3>Efeito do RAG (taxa de respostas corretas pela verdade)</h3>
<div class="table-wrap"><table><thead><tr><th>Modelo</th><th>Com RAG</th><th>Sem RAG</th></tr></thead><tbody>{rag_rows}</tbody></table></div>
<h3>Dimensões para a discussão no TCC</h3>
<ul class="tight">
  <li><b>Papel humano na verdade:</b> o gabarito foi escrito pela equipe/orientador e decomposto em fatos-chave revisados por humano;
      {st['rotulos_revisados_por_humano']} rótulo(s) revisado(s) manualmente, {st['rotulos_alterados_pela_revisao']} alterado(s) pela revisão.</li>
  <li><b>Reprodutibilidade e transparência:</b> métricas tradicionais são fórmulas auditáveis e determinísticas; as métricas DeepEval dependem de um LLM opaco, mudam com a versão do modelo e variam entre execuções.</li>
  <li><b>Custo e acesso:</b> avaliar com LLM exige chaves pagas e conexão externa, uma barreira para instituições públicas e estudantes; as tradicionais rodam localmente.</li>
  <li><b>Viés do avaliador:</b> o LLM de apoio do DeepEval ({html.escape(analysis['llm_deepeval'])}) é da mesma família de um dos modelos avaliados (GPT) e pode favorecê-lo; LLMs também tendem a preferir respostas longas e fluentes.</li>
  <li><b>Língua e domínio:</b> métricas lexicais penalizam paráfrases em português e listas em outra ordem; embeddings multilíngues e juízes lidam melhor, mas podem aprovar respostas fluentes com fatos errados.</li>
  <li><b>Privacidade:</b> avaliar com LLM envia perguntas, respostas e nomes de alunos a provedores externos.</li>
  <li><b>Thresholds estratificados:</b> um único threshold trata igual “qual o primeiro nome?” e “liste 191 estudantes”; o contexto da pergunta muda o que é aceitável.</li>
</ul>"""


def _explorer(analysis: dict[str, Any]) -> str:
    calib = {
        s["metric"]: {"global": s["threshold_global"], "estratos": s["thresholds_por_estrato"], "family": s["family"]}
        for s in analysis["ranking"]
    }
    payload = json.dumps({"answers": analysis["answers"], "calib": calib}, ensure_ascii=False).replace("</", "<\\/")
    return """
<p>Cada cartão mostra pergunta, gabarito, resposta e fatos-chave encontrados/faltantes. Nas métricas,
<span class="tag ok">verde</span> = o veredito da métrica concorda com a verdade e <span class="tag bad">vermelho</span> = discorda.
Se discordar da verdade automática, marque o rótulo revisado e baixe <code>rotulos_revisados.csv</code>
(salve em <code>back/avaliacao_metricas/</code> e rode <code>analyze_metrics.py</code> de novo).</p>
<div class="filters">
  <label>Modelo <select id="fModel"></select></label>
  <label>Condição <select id="fCond"></select></label>
  <label>Estrato <select id="fStratum"></select></label>
  <label>Threshold <select id="fMode"><option value="estratos">estratificado</option><option value="global">global</option></select></label>
  <label>Mostrar <select id="fShow"><option value="all">todas</option><option value="disagree">com discordância</option><option value="wrong">verdade = incorreta</option></select></label>
  <button id="btnCsv" type="button">Baixar rotulos_revisados.csv</button>
  <span id="count" class="muted"></span>
</div>
<div id="list"></div>
<script id="data" type="application/json">""" + payload + """</script>
<script>
(function(){
  const data = JSON.parse(document.getElementById('data').textContent);
  const reviewed = {};
  const $ = id => document.getElementById(id);
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function fill(sel, values){ sel.innerHTML = '<option value="">todos</option>' + values.map(v => `<option>${esc(v)}</option>`).join(''); }
  const uniq = k => [...new Set(data.answers.map(a => a[k]))].sort();
  fill($('fModel'), uniq('model')); fill($('fCond'), uniq('condition')); fill($('fStratum'), uniq('stratum'));
  function verdict(a, m){
    const c = data.calib[m]; const s = a.scores[m];
    if (!c || s === undefined || s === null) return null;
    const t = $('fMode').value === 'global' ? c.global : (c.estratos[a.stratum] ?? c.global);
    return {score: s, t: t, pred: s >= t - 1e-12 ? 1 : 0};
  }
  function render(){
    const fm = $('fModel').value, fc = $('fCond').value, fs = $('fStratum').value, show = $('fShow').value;
    const metrics = Object.keys(data.calib);
    let html = '', n = 0;
    for (const a of data.answers){
      if ((fm && a.model !== fm) || (fc && a.condition !== fc) || (fs && a.stratum !== fs)) continue;
      const truth = reviewed[a.answer_key] ?? a.truth;
      const vs = metrics.map(m => [m, verdict(a, m)]).filter(x => x[1]);
      const disagree = vs.some(([, v]) => v.pred !== truth);
      if (show === 'disagree' && !disagree) continue;
      if (show === 'wrong' && truth !== 0) continue;
      n++;
      const chips = vs.map(([m, v]) => `<span class="${v.pred === truth ? 'ok' : 'bad'}" title="threshold ${v.t.toFixed(2)}">${esc(m)} ${v.score.toFixed(2)}</span>`).join('');
      const sel = `<select data-key="${esc(a.answer_key)}"><option value="">(automático: ${a.truth_auto ? 'correta' : 'incorreta'})</option><option value="1" ${reviewed[a.answer_key]===1?'selected':''}>correta</option><option value="0" ${reviewed[a.answer_key]===0?'selected':''}>incorreta</option></select>`;
      html += `<article class="answer-card">
        <h3>#${a.number} · ${esc(a.model)} · ${esc(a.condition)} · <span class="tag">${esc(a.stratum)}</span></h3>
        <p><b>${esc(a.question)}</b></p>
        <p>Verdade: <span class="tag ${truth ? 'ok' : 'bad'}">${truth ? 'correta' : 'incorreta'}</span>
           cobertura ${(a.coverage*100).toFixed(0)}% (mínimo ${(a.min_coverage*100).toFixed(0)}%) · origem ${esc(a.truth_source)} · revisar: ${sel}</p>
        <div class="chips">${chips}</div>
        <div class="cols">
          <div><b>Gabarito</b><pre>${esc(a.expected)}</pre></div>
          <div><b>Resposta</b><pre>${esc(a.answer)}</pre></div>
          <div><b>Fatos faltantes (${a.missing.length})</b><pre>${esc(a.missing.join('\\n')) || '—'}</pre>
               <details><summary>Encontrados (${a.found.length})</summary><pre>${esc(a.found.join('\\n'))}</pre></details></div>
        </div>
        ${Object.keys(a.reasons||{}).length ? `<details><summary>Justificativas do DeepEval</summary><pre>${esc(Object.entries(a.reasons).map(([k,v]) => k + ': ' + v).join('\\n\\n'))}</pre></details>` : ''}
      </article>`;
    }
    $('list').innerHTML = html; $('count').textContent = n + ' resposta(s)';
  }
  document.addEventListener('change', e => {
    if (e.target.dataset && e.target.dataset.key){
      const v = e.target.value; if (v === '') delete reviewed[e.target.dataset.key]; else reviewed[e.target.dataset.key] = Number(v);
      render(); return;
    }
    if (e.target.tagName === 'SELECT') render();
  });
  $('btnCsv').addEventListener('click', () => {
    const lines = ['answer_key;label'].concat(Object.entries(reviewed).map(([k, v]) => k + ';' + v));
    const blob = new Blob(['\\ufeff' + lines.join('\\n')], {type: 'text/csv;charset=utf-8'});
    const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = 'rotulos_revisados.csv'; link.click();
  });
  render();
})();
</script>"""


def write_html_reports(output_dir: Path, analysis: dict[str, Any]) -> None:
    body = f"""
<h1>Métricas tradicionais × métricas com LLM</h1>
<p class="lead">TitãsBot · {analysis['total_respostas']} respostas avaliadas ({analysis['total_corretas']} corretas pela verdade do gabarito) ·
LLM do DeepEval: {html.escape(analysis['llm_deepeval'])} · critério: {html.escape(analysis['criterio'])} · gerado em {html.escape(analysis['gerado_em'])}</p>
{_NAV}
<h2 id="ranking">1. Qual métrica concorda mais com o gabarito?</h2>
{_ranking_table(analysis)}
<h2 id="familias">2. Tradicional × LLM</h2>
{_families(analysis)}
<h2 id="thresholds">3. Thresholds: global × estratificado por tipo de resposta</h2>
{_threshold_section(analysis)}
<h2 id="sistemas">4. Modelos com e sem RAG</h2>
{_systems_section(analysis)}
<h2 id="recuperacao">5. Recuperação</h2>
{_retrieval_section(analysis)}
<h2 id="socio">6. Características sócio-técnicas</h2>
{_socio_section(analysis)}
<h2 id="respostas">7. Explorador de respostas</h2>
{_explorer(analysis)}
"""
    (output_dir / "comparacao_metricas.html").write_text(_page("Comparação de métricas — TitãsBot", body), encoding="utf-8")
    (output_dir / "como_funciona.html").write_text(_page("Como funciona — estudo de métricas", _HOW_IT_WORKS), encoding="utf-8")


_HOW_IT_WORKS = """
<h1>Como funciona o estudo de métricas</h1>
<nav><a href="comparacao_metricas.html">← Voltar ao relatório</a></nav>
<h2>Pergunta de pesquisa</h2>
<p>As métricas tradicionais de NLP (BLEU, ROUGE, similaridade de embeddings…) já foram superadas por métricas que usam um LLM para avaliar (DeepEval)
para avaliar um chatbot RAG? Qual avalia melhor as respostas do TitãsBot?</p>
<h2>1. Respostas</h2>
<p>40 perguntas do gabarito oficial respondidas por três modelos medianos equivalentes (GPT-5 mini, Claude Haiku 4.5, DeepSeek Chat), cada um
<b>com RAG</b> (base de documentos da equipe) e <b>sem RAG</b> (só o conhecimento do modelo): até 240 respostas.</p>
<h2>2. Verdade (a partir do gabarito)</h2>
<p>Cada resposta do gabarito foi decomposta em <b>fatos-chave</b> (um nome, um ano, uma linha "Modalidade: colocação — competição"),
revisados por humano. A <b>cobertura</b> é a fração desses fatos presente na resposta. A resposta é <b>correta</b> (rótulo 1) se a cobertura
atingir o mínimo do seu tipo: fato curto 100%, descritiva 75%, listas 80%. Rótulos podem ser corrigidos manualmente no explorador.</p>
<h2>3. Métricas avaliadas</h2>
<ul class="tight">
  <li><b>Tradicionais lexicais:</b> Exact Match, F1 de tokens, BLEU, chrF, ROUGE-1/2/L, METEOR.</li>
  <li><b>Tradicionais semânticas:</b> cosseno de embeddings MiniLM, BERTScore.</li>
  <li><b>Projeto de referência:</b> 0,8 × cosseno + 0,2 × SequenceMatcher (Visualizador-do-avaliador).</li>
  <li><b>Com LLM (DeepEval, apoiado por GPT):</b> GEval Correctness, Answer Relevancy, Faithfulness (só RAG) e Hallucination (invertida).</li>
</ul>
<h2>4. Como decidimos qual métrica é melhor</h2>
<p>Cada métrica vira um classificador: <i>score ≥ threshold ⇒ correta</i>. Comparamos o veredito com a verdade:</p>
<ul class="tight">
  <li><b>AUC</b>: sem threshold, mede se a métrica dá notas maiores às respostas corretas.</li>
  <li><b>Threshold global</b>: igual ao projeto de referência, testando 0,00 a 1,00 e medindo acurácia, precisão, recall e F1.</li>
  <li><b>Threshold estratificado</b>: um threshold por tipo de resposta (fato curto, descritiva, lista curta, lista longa).</li>
  <li><b>Validação cruzada</b>: o threshold é escolhido com as respostas de dois modelos e testado no terceiro, para não "decorar" os dados.</li>
  <li><b>Ranking dos modelos</b>, <b>custo</b>, <b>tempo</b> e <b>estabilidade</b> (repetir a avaliação dá a mesma nota?).</li>
</ul>
<h2>Limitações</h2>
<ul class="tight">
  <li>A verdade por fatos-chave mede presença de fatos, não penaliza fatos extras inventados; por isso existe a revisão humana.</li>
  <li>O LLM de apoio das métricas DeepEval (GPT) é da mesma família de um dos modelos avaliados.</li>
  <li>METEOR usa sinônimos do inglês (WordNet); em português funciona praticamente como sobreposição de palavras.</li>
</ul>
"""
