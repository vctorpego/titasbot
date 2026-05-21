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
