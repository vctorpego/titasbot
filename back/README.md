# chatbot-rag

Estrutura atual do backend:

```text
chatbot-rag/
├── app/
│   ├── presentation/
│   ├── application/
│   ├── domain/
│   ├── infrastructure/
│   └── core/
├── tests/
├── scripts/
└── README.md
```

## Execucao

```powershell
cd C:\Projetos\titasbot\back

# CLI
.\venv\Scripts\python.exe main.py

# Indexacao
.\venv\Scripts\python.exe criar_db.py

# API HTTP
.\venv\Scripts\python.exe web_server.py
```

Os arquivos `main.py`, `criar_db.py` e `web_server.py` sao entrypoints finos que delegam para `scripts/`.

## Testes

Testes rapidos e deterministicos:

```powershell
.\venv\Scripts\python.exe -m pytest tests -q
```

Evals manuais com DeepEval:

```powershell
# Baseline padrao: 13 casos curados, GEval em modo rapido.
.\venv\Scripts\deepeval.exe test run tests/evals/test_rag_quality.py --display failing -- --tb=short

# Bateria completa: 46 casos, ainda diagnostica.
$env:DEEPEVAL_CASE_SET="all"; .\venv\Scripts\deepeval.exe test run tests/evals/test_rag_quality.py --display failing -- --tb=short

# Mais rigor/custo: adiciona AnswerRelevancy e, em casos selecionados, Faithfulness/contextuais.
$env:DEEPEVAL_CASE_SET="all"; $env:DEEPEVAL_METRIC_SET="full"; .\venv\Scripts\deepeval.exe test run tests/evals/test_rag_quality.py --display failing -- --tb=short
```

Os evals usam `OPENAI_API_KEY` e exigem a base vetorial ja criada.

## Estudo comparativo de metricas: tradicionais x LLM (atual)

Objetivo do TCC: descobrir **qual metodo avalia melhor** as respostas do chatbot -- metricas
tradicionais (BLEU, chrF, ROUGE, METEOR, F1, cosseno, BERTScore e a formula do projeto de
referencia) ou metricas do DeepEval que usam LLM (GEval Correctness, Answer Relevancy,
Faithfulness e Hallucination). Metodologia completa em `docs/metodologia_metricas.md`.

- **Modelos medianos** (com e sem RAG): `gpt-5-mini`, `claude-haiku-4-5-20251001`, `deepseek-chat`.
- **Verdade**: gabarito oficial decomposto em fatos-chave (`tests/evals/metric_eval_annotations.json`);
  resposta correta se cobrir o minimo de fatos do seu tipo (fato curto 100%, descritiva 75%, listas 80%).
- **Meta-avaliacao**: cada metrica vira classificador; AUC, varredura de thresholds **global** e
  **estratificada por tipo de resposta**, validacao cruzada leave-one-model-out, ranking de modelos,
  custo, tempo e estabilidade das metricas DeepEval.
- **LLM de apoio do DeepEval**: GPT (`DEEPEVAL_EVAL_PROVIDER` / `DEEPEVAL_EVAL_MODEL`, padrao `gpt-5-nano`).

```powershell
pip install -r requirements-eval.txt
.\venv\Scripts\python.exe -m nltk.downloader wordnet omw-1.4   # para o METEOR (opcional)

# 1) respostas (pago; retomavel)  -- smoke test: $env:EVAL_CASE_LIMIT="3"; $env:EVAL_MODELS="deepseek"
.\venv\Scripts\python.exe scripts\generate_answers.py
# 2) metricas; primeiro veja quantas avaliacoes DeepEval faltam
$env:EVAL_DRY_RUN="1"; .\venv\Scripts\python.exe scripts\score_answers.py; Remove-Item Env:EVAL_DRY_RUN
.\venv\Scripts\python.exe scripts\score_answers.py
# 3) analise (sem API) -> avaliacao_metricas/comparacao_metricas.html
.\venv\Scripts\python.exe scripts\analyze_metrics.py
```

Revisao humana: no explorador do HTML, marque rotulos que discordar da verdade automatica, baixe
`rotulos_revisados.csv`, salve em `avaliacao_metricas/` e rode so a etapa 3 de novo.

As secoes abaixo (`evaluate_models.py` e `evaluate_rag_four_metrics.py`) sao as rodadas anteriores
do projeto, mantidas como historico.

## Avaliacao comparativa de modelos (multi-provedor)

Compara **3 provedores** (OpenAI, Anthropic/Claude e DeepSeek), cada um em **duas condicoes**
(com RAG e sem RAG), pontuando cada resposta por **duas metodologias em paralelo**.
(Google/Gemini foi removido da comparacao por decisao do usuario; `llm_factory.py` ainda suporta
`google_genai` de forma generica, mas nenhum `ModelSpec` o usa hoje.)

- **DeepEval**: Correctness, AnswerRelevancy, Faithfulness (fidelidade ao contexto
  recuperado -- so roda com RAG) e Hallucination (alucinacao -- compara com o gabarito, roda
  sempre, com ou sem RAG; veredito invertido: `score &lt;= limiar` = aprovado). Todas usam o
  avaliador do DeepEval (`DEEPEVAL_EVAL_MODEL`) comparando direto com o gabarito.
- **Referencia** (metodologia do orientador): similaridade semantica (embeddings MiniLM) 80% +
  lexica (ROUGE-L) 20% -> `score_final`, comparado direto com o gabarito. Sem LLM. Reportado
  como nota media e taxa de aprovacao por threshold fixo (sem Precisao/Recall/F1 -- essas
  exigiriam um rotulo de verdade independente, que este projeto nao usa).

Os embeddings/recuperacao continuam em OpenAI para todos os modelos (comparacao justa: so o modelo
gerador muda). O conjunto de teste sao as perguntas de `tests/evals/model_eval_cases.json`.

### Preparacao

```powershell
cd C:\Faculdade\TCC\titasbot\back
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
pip install -r requirements-eval.txt   # provedores extras + sentence-transformers
```

Configure as chaves em `back\.env` (veja `.env.example`): `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` e
`DEEPSEEK_API_KEY`. **DeepSeek exige saldo pre-pago** em `platform.deepseek.com` (sem tier
gratuito) -- mesma friccao da Anthropic. `OPENAI_API_KEY` tambem alimenta o avaliador do DeepEval
(`gpt-5-nano`, ver abaixo). `GOOGLE_API_KEY` (opcional) so e necessaria se voce reativar o Gemini
como avaliador do DeepEval com faturamento pago -- ver nota abaixo sobre o tier gratuito. Depois
construa a base vetorial:

```powershell
.\venv\Scripts\python.exe criar_db.py
```

### Execucao

```powershell
.\venv\Scripts\python.exe scripts\evaluate_models.py
```

Saidas em `avaliacao_modelos/`:

- `respostas_por_modelo.csv` (respostas + scores das duas metodologias)
- `resumo_modelos.csv`, `metricas_por_threshold.csv` (metodologia DeepEval)
- `metricas_referencia_por_threshold.csv` (taxa de aprovacao do avaliador de referencia)
- `avaliacao_modelos.json`
- `avaliacao_modelos.html`, `comparacao_metricas.html`, `como_funciona.html` (visualizador)

## Avaliacao RAG em 4 metricas

Executa uma rodada menor e mais explicavel, focada somente no DeepSeek e em 20
perguntas oficiais do gabarito. A avaliacao separa o RAG em duas etapas:

- **Recuperacao**: `Hit@5` e `Precision@5`, usando evidencias anotadas em
  `tests/evals/rag_stage_eval_cases.json`.
- **Geracao**: `Answer Correctness` e `Faithfulness`, medidas pelo DeepEval
  contra o gabarito e o contexto recuperado.

```powershell
$env:EVAL_DEEPSEEK_MODEL="deepseek-chat"
$env:DEEPEVAL_EVAL_MODEL="gpt-5-nano"
$env:DEEPEVAL_EVAL_PROVIDER="openai"
.\venv\Scripts\python.exe scripts\evaluate_rag_four_metrics.py
```

Saidas em `avaliacao_rag_4_metricas/`:

- `rag_4_metricas.json`
- `rag_4_metricas.csv`
- `rag_4_metricas.html`

### Configuracoes (env)

```powershell
# Modelos por provedor (CONFIRME os IDs atuais do provedor antes da rodada avaliada):
$env:EVAL_OPENAI_MODEL="gpt-5"
$env:EVAL_ANTHROPIC_MODEL="claude-sonnet-5"
$env:EVAL_DEEPSEEK_MODEL="deepseek-v4-pro"

# Rodar so uma condicao (mais rapido/barato): "rag", "no_rag" ou "rag,no_rag"
$env:EVAL_CONDITIONS="rag"

# Avaliador das metricas DeepEval: um modelo diferente dos 3 comparados, para
# reduzir autoavaliacao. Gemini (independencia total de provedor) foi tentado
# primeiro, mas o tier gratuito (15 requisicoes/minuto) e impraticavel para o
# volume desta avaliacao. gpt-5-nano (OpenAI) e mais barato que os 3 modelos
# comparados ($0,05/$0,40 por milhao de tokens) e usa uma chave ja configurada.
$env:DEEPEVAL_EVAL_MODEL="gpt-5-nano"
$env:DEEPEVAL_EVAL_PROVIDER="openai"
$env:MODEL_EVAL_METRIC_SET="full"      # fast, standard ou full (default agora "full")
$env:MODEL_EVAL_CONTEXT_CHARS="1200"
```

> `DEEPEVAL_EVAL_PROVIDER` aceita `openai` (default, retrocompativel -- passa a string do
> modelo direto para o DeepEval), `google_genai`, `anthropic` ou `deepseek` (via wrappers
> nativos `deepeval.models.GeminiModel`/`AnthropicModel`/`DeepSeekModel`) -- util se quiser
> reativar o Gemini com faturamento pago (sem o limite de 15 req/min do tier gratuito).

> A matriz completa (3 modelos x 2 condicoes x 40 perguntas oficiais, tier `full`) dispara
> aproximadamente **1.014 chamadas de LLM** (respostas + Correctness/AnswerRelevancy/Faithfulness/
> Hallucination), em 3 contas. Estimativa: **US$ 0,35-0,55** e **30-50 minutos** (execucao
> sequencial) -- ambas aproximadas, sem a chamada extra do juiz que a versao anterior desta
> avaliacao fazia por caso. Rode primeiro um smoke test barato antes da rodada cheia:
> ```powershell
> $env:EVAL_CASE_LIMIT="3"; $env:EVAL_CONDITIONS="rag"; $env:MODEL_EVAL_METRIC_SET="fast"
> .\venv\Scripts\python.exe scripts\evaluate_models.py
> ```
> Sem `sentence-transformers`, a metodologia de referencia e pulada (so DeepEval roda).
