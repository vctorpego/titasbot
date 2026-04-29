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
cd c:\Users\victo\OneDrive\Documents\ProjetosVSCD\chatbot

# CLI
& c:/python314/python.exe back/main.py

# Indexacao
& c:/python314/python.exe back/criar_db.py

# API HTTP
& c:/python314/python.exe back/web_server.py
```

Os arquivos `main.py`, `criar_db.py` e `web_server.py` sao entrypoints finos que delegam para `scripts/`.
