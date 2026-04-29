# TitasBot - Arquitetura em Camadas

## Camadas
- `app/presentation/`: interfaces de entrada (CLI e HTTP)
- `app/application/`: casos de uso, orquestracao e componentes de resposta (prompts/helpers)
- `app/domain/`: regras de negocio e intencoes
- `app/infrastructure/`: integracoes externas (config, ingestao, vectorstore, retrieval)
- `app/core/`: modelos/contratos centrais

## Estrutura principal
- `main.py`: entrypoint CLI
- `criar_db.py`: entrypoint de ingestao/indexacao
- `web_server.py`: entrypoint HTTP

### Presentation
- `app/presentation/cli_chat.py`: chat de terminal e debug
- `app/presentation/http_server.py`: servidor HTTP (`/health`, `/chat`)

### Application
- `app/application/chat_service.py`: orquestrador RAG
- `app/application/chat_use_cases.py`: casos de uso (`ask_question`, `review_answer`)
- `app/application/prompts.py`: prompts de geracao/auditoria
- `app/application/helpers.py`: parsing/auditoria/normalizacao
- `app/application/student_list.py`: extracao deterministica de lista de alunos

### Domain
- `app/domain/constants.py`: constantes do dominio
- `app/domain/intents.py`: deteccao de intencoes e regras de decisao

### Infrastructure
- `app/infrastructure/settings.py`: configuracao via `.env`
- `app/infrastructure/ingestion.py`: leitura PDF + chunking + indexacao
- `app/infrastructure/vectorstore.py`: Chroma + embeddings
- `app/infrastructure/retrieval.py`: recuperacao hibrida (vetorial + BM25)
- `app/infrastructure/text_utils.py`: normalizacao/tokenizacao utilitaria

### Core
- `app/core/models.py`: modelos compartilhados (ex.: `ChatResult`)

## Fluxo
1. `criar_db.py` indexa os PDFs em `base/`.
2. `main.py` (CLI) ou `web_server.py` (HTTP) recebe pergunta.
3. Application consulta retrieval, seleciona evidencias e gera resposta.
4. Application audita/normaliza a resposta e devolve com fontes.

## Comandos
```powershell
cd c:\Users\victo\OneDrive\Documents\ProjetosVSCD\chatbot
& c:/python314/python.exe back/criar_db.py
& c:/python314/python.exe back/main.py
& c:/python314/python.exe back/web_server.py
```
