# Documentação Técnica - Chatbot dos Titãs da Robótica

## 1. Visão Geral do Sistema

O **Chatbot dos Titãs da Robótica** é uma aplicação de perguntas e respostas projetada para consultar, de forma confiável, a base documental da equipe Titãs da Robótica (IFES Campus Colatina). O sistema foi desenvolvido para responder perguntas em linguagem natural sobre história da equipe, projetos, competições, resultados, integrantes e informações institucionais presentes nos documentos oficiais do projeto.

O problema central que a aplicação resolve é o seguinte: a base de conhecimento da equipe está distribuída em documentos longos (livro, artigo e PDFs com tabelas), o que dificulta localizar fatos específicos de maneira rápida e precisa. Em vez de exigir leitura manual de centenas de páginas, o chatbot realiza recuperação semântica e lexical dos trechos relevantes e entrega uma resposta objetiva com indicação de fontes.

A abordagem adotada é **RAG (Retrieval-Augmented Generation)**, que significa, no contexto deste projeto, combinar:
- **Retrieval (recuperação)**: buscar no acervo os trechos mais relevantes para a pergunta;
- **Generation (geração)**: usar um modelo de linguagem para montar a resposta com base nesses trechos.

O sistema é alimentado por documentos da pasta `base/`, incluindo:
- livro da equipe (`Titãs da Robótica - LIVRO.pdf`), com contexto histórico e institucional;
- PDF de tabelas (`tabelas - livro titas.pdf`), com dados mais estruturados (resultados, listagens, etc.);
- artigo adicional (`MNR2025-ART Titãs.pdf`).

Assim, o chatbot foi construído para manter **fidelidade ao conteúdo documental**, reduzindo respostas inventadas (hallucinations) e melhorando a precisão em consultas factuais.

---

## 2. Visão Geral da Arquitetura

### 2.1 Modelo arquitetural adotado

O backend segue uma arquitetura em camadas com separação explícita de responsabilidades:
- `presentation`
- `application`
- `domain`
- `infrastructure`
- `core`

Além disso, o projeto possui:
- `scripts` (entrypoints de execução)
- `tests` (testes automatizados)

### 2.2 Por que essa arquitetura foi escolhida

A escolha prioriza quatro objetivos:
1. **Simplicidade operacional**: o sistema é executável com poucos comandos e estrutura direta;
2. **Modularidade**: cada camada possui função clara, reduzindo acoplamento;
3. **Evolução incremental**: novas regras podem ser adicionadas sem reescrever o sistema inteiro;
4. **Legibilidade acadêmica**: facilita explicar, em TCC, onde cada decisão técnica está implementada.

### 2.3 Adequação ao TCC

Para um trabalho acadêmico aplicado, esta arquitetura é adequada porque:
- torna visível a relação entre teoria (RAG, engenharia de prompts, recuperação híbrida) e implementação;
- permite justificar decisões por camada (ex.: regra de negócio no `domain`, integração externa no `infrastructure`);
- organiza o código para banca e manutenção futura por outros estudantes.

### 2.4 Por que abordagens mais complexas não foram adotadas

Não foram adotados frameworks arquiteturais mais pesados (por exemplo, microserviços, event sourcing, CQRS completo) porque o escopo atual não exige distribuição entre múltiplos serviços independentes. Tais abordagens aumentariam complexidade operacional (deploy, observabilidade, contratos interserviços) sem ganho proporcional no estágio atual do projeto.

---

## 3. Explicação Detalhada de Cada Camada

## 3.1 Camada `presentation`

### Responsabilidade
Receber entradas externas (CLI e HTTP), validar o mínimo necessário, chamar casos de uso e devolver respostas ao usuário.

### O que deve ficar nela
- Interface de terminal;
- Endpoints HTTP;
- Controle de sessão de conversa em nível de interface.

### O que não deve ficar nela
- Regras de negócio de recuperação;
- Regras semânticas de pergunta;
- Implementação de indexação/vetorização.

### Relação com outras camadas
`presentation` chama `application` (casos de uso), mas não conhece detalhes internos de recuperação ou parsing.

### Importância da separação
Evita que API/CLI acumulem lógica de IA e garante que a mesma regra possa ser reutilizada em múltiplas interfaces.

## 3.2 Camada `application`

### Responsabilidade
Orquestrar o fluxo completo de resposta do chatbot: montagem de consulta, recuperação, seleção de evidência, geração, auditoria e formatação final.

### O que deve ficar nela
- Serviço principal do chatbot (`chat_service`);
- Casos de uso (`chat_use_cases`);
- Prompts e helpers de fluxo de resposta;
- Lógica de especialização de respostas (ex.: listagem de estudantes).

### O que não deve ficar nela
- Operações de leitura direta de PDF;
- Operação física do banco vetorial;
- Regras puras de domínio desacopladas do fluxo.

### Relação com outras camadas
Consome `domain` (intenções/regras), `infrastructure` (retrieval, vectorstore, config), `core` (modelos comuns) e é invocada por `presentation`.

### Importância da separação
Centraliza a orquestração do caso de uso e evita lógica duplicada entre CLI e API.

## 3.3 Camada `domain`

### Responsabilidade
Conter regras de negócio puras e decisões semânticas independentes de tecnologia externa.

### O que deve ficar nela
- Constantes do domínio (mensagens canônicas, limites lógicos);
- Detecção de intenções da pergunta (`is_list_question`, `is_projects_question`, etc.).

### O que não deve ficar nela
- Chamada a modelo de linguagem;
- Chamada a banco vetorial;
- Operação de rede/IO.

### Relação com outras camadas
`application` utiliza `domain` para decidir comportamento; `domain` não depende de `presentation`.

### Importância da separação
Permite evolução das regras sem impacto em integrações externas.

## 3.4 Camada `infrastructure`

### Responsabilidade
Implementar integrações concretas com bibliotecas e recursos externos.

### O que deve ficar nela
- Configuração via ambiente (`settings`);
- Ingestão de PDFs e chunking (`ingestion`);
- Vetor store e embeddings (`vectorstore`);
- Recuperação híbrida (`retrieval`);
- Utilidades de normalização/tokenização (`text_utils`).

### O que não deve ficar nela
- Regras de diálogo orientadas ao usuário;
- Decisões de alto nível do caso de uso.

### Relação com outras camadas
`application` depende de `infrastructure`; `presentation` não deveria usar diretamente operações de baixo nível.

### Importância da separação
Isola dependências de terceiros (OpenAI, Chroma, pypdf), facilitando substituição futura de componentes.

## 3.5 Camada `core`

### Responsabilidade
Definir elementos transversais e contratos de dados compartilhados entre camadas.

### O que deve ficar nela
- Modelos básicos de transporte interno (ex.: `ChatResult`).

### O que não deve ficar nela
- Regras específicas de ingestão ou prompts;
- Código de interface.

### Relação com outras camadas
Serve como ponto comum de tipagem/contrato para `application` e demais módulos.

### Importância da separação
Garante consistência de estruturas compartilhadas e reduz dependências cíclicas.

## 3.6 Diretório `tests`

Armazena testes automatizados. Atualmente há teste de detecção de intenção (`test_intents.py`), importante para validar regressão em regras de pergunta.

## 3.7 Diretório `scripts`

Agrupa entrypoints executáveis do projeto (`build_vector_db`, `run_chat_cli`, `run_http_server`, `evaluate_chatbot`).

Finalidade: separar execução operacional da lógica de negócio.

---

## 4. Fluxos Principais do Sistema

## 4.1 Fluxo de ingestão de documentos

### Entrada
- PDFs em `base/`;
- Configurações de chunking, batch e caminhos via `.env`.

### Processamento
1. `scripts/build_vector_db.py` chama `infrastructure.ingestion.build_vector_db`.
2. `load_documents` lê páginas dos PDFs com `pypdf`.
3. Cada página vira `Document` com metadados (`source`, `page`, `doc_kind`).
4. `split_documents` divide conteúdo em chunks (`RecursiveCharacterTextSplitter`).
5. `vectorstore.add_documents` gera embeddings e persiste no Chroma.
6. Em falhas transitórias, o processo usa retry por lote.

### Saída
- Coleção vetorial persistida no diretório configurado do Chroma.

### Motivo da implementação
Chunking + metadados por página permitem rastreabilidade de fonte e recuperação mais precisa.

## 4.2 Fluxo da pergunta do usuário

### Entrada
- Pergunta via CLI (`presentation/cli_chat.py`) ou API (`presentation/http_server.py`).

### Processamento
1. Interface chama caso de uso em `application/chat_use_cases.py`.
2. Caso de uso delega para `TitasBotService.ask`.
3. Serviço determina intenção e estratégia de recuperação.

### Saída
- Resposta textual com bloco `Fontes usadas`.

### Motivo da implementação
Mesmo núcleo de negócio atende dois canais (CLI e HTTP), evitando divergência de comportamento.

## 4.3 Fluxo de recuperação via RAG

### Entrada
- Pergunta normalizada e, quando aplicável, contexto anterior.

### Processamento
1. Construção de `retrieval_query` com reforços semânticos.
2. Recuperação híbrida em `infrastructure/retrieval.py`:
- similaridade vetorial (embeddings);
- score lexical BM25;
- reranqueamento com sinais de intenção (lista, competição, contexto).
3. Seleção de chunks de evidência.

### Saída
- Conjunto de trechos candidatos com score e metadados de origem.

### Motivo da implementação
A recuperação híbrida combina robustez semântica com precisão em termos exatos (nomes, anos, classificações).

## 4.4 Fluxo de montagem de prompt

### Entrada
- Pergunta + contexto textual montado dos chunks + histórico (quando necessário).

### Processamento
- O serviço escolhe template em `application/prompts.py` conforme intenção:
- factual;
- listagem;
- participação;
- projetos;
- revisão de resposta;
- auditoria final.

### Saída
- Prompt estruturado para o modelo de linguagem.

### Motivo da implementação
Prompts especializados reduzem ambiguidade e melhoram controle de qualidade da resposta.

## 4.5 Fluxo de geração da resposta final

### Entrada
- Prompt + contexto recuperado.

### Processamento
1. LLM gera resposta candidata.
2. `helpers.py` limpa texto e audita aderência ao contexto.
3. Se necessário, aplica fallback extrativo.
4. Normaliza referências de fontes usadas.

### Saída
- Resposta final com texto + referências numeradas.

### Motivo da implementação
A etapa de auditoria/fallback reduz respostas vagas e aumenta consistência factual.

---

## 5. Explicação Arquivo por Arquivo

## 5.1 Raiz (`back/`)

- `main.py`: entrypoint mínimo da execução CLI.
- `criar_db.py`: entrypoint mínimo para indexação.
- `web_server.py`: entrypoint mínimo do servidor HTTP.
- `README.md`: visão rápida de estrutura e execução.
- `ARQUITETURA.md`: visão arquitetural resumida.

Esses arquivos ficam na raiz para facilitar operação por comando direto.

Exemplo de execução a partir da raiz do repositório:

```powershell
cd c:\Users\victo\OneDrive\Documents\ProjetosVSCD\chatbot
& c:/python314/python.exe back/criar_db.py
& c:/python314/python.exe back/main.py
& c:/python314/python.exe back/web_server.py
```

## 5.2 `app/presentation`

- `cli_chat.py`
  - Implementa chat em terminal, comandos de debug e tratamento de feedback de correção.
  - Não contém lógica de recuperação de baixo nível.

- `http_server.py`
  - Implementa servidor HTTP (`/health`, `/chat`), CORS e sessão por `session_id`.
  - Encaminha para casos de uso da camada `application`.

## 5.3 `app/application`

- `chat_service.py`
  - Núcleo orquestrador do chatbot.
  - Coordena query expansion, retrieval, seleção de evidências, geração, auditoria e pós-processamento.

- `chat_use_cases.py`
  - Expõe operações do caso de uso (`ask_question`, `review_answer`).
  - Mantém `presentation` desacoplada do detalhe interno do serviço.

- `prompts.py`
  - Centraliza templates de prompt por tarefa.
  - Garante consistência de instruções ao modelo.

- `helpers.py`
  - Funções de apoio da orquestração (limpeza, parsing de IDs, normalização de fontes, validação da resposta).

- `student_list.py`
  - Estratégia especializada para extração de nomes de estudantes em listagens.
  - Existe para evitar mistura de entidades (alunos x patrocinadores x orientadores).

## 5.4 `app/domain`

- `constants.py`
  - Mensagens padrão e limites usados pela lógica do domínio.

- `intents.py`
  - Regras para detectar tipo de pergunta e intenção semântica.

## 5.5 `app/infrastructure`

- `settings.py`
  - Define `Settings` e leitura de variáveis de ambiente.

- `ingestion.py`
  - Leitura de PDFs, classificação de tipo de documento, chunking e indexação em lotes.

- `vectorstore.py`
  - Criação/uso do Chroma e embeddings OpenAI.

- `retrieval.py`
  - Implementa recuperação híbrida (vetorial + BM25) e reranqueamento.

- `text_utils.py`
  - Normalização textual, tokenização e utilidades linguísticas básicas.

## 5.6 `app/core`

- `models.py`
  - Modelo `ChatResult` usado como contrato de retorno no fluxo de perguntas.

## 5.7 `scripts`

- `run_chat_cli.py`: executa modo terminal.
- `build_vector_db.py`: executa indexação da base.
- `run_http_server.py`: executa API HTTP.
- `evaluate_chatbot.py`: rotina de avaliação automatizada.

## 5.8 `tests`

- `test_intents.py`: valida regras de intenção de perguntas.

---

## 6. Regras, Decisões e Padrões Adotados

Principais decisões arquiteturais:
- separar entrada (`presentation`) da orquestração (`application`);
- isolar integrações externas em `infrastructure`;
- manter regras semânticas em `domain`;
- manter contrato compartilhado em `core`.

Convenções adotadas:
- prompts centralizados em módulo dedicado da camada de aplicação;
- funções auxiliares de parsing/auditoria separadas de lógica de endpoint;
- entrypoints finos em `scripts` para reduzir duplicação.

O que foi evitado:
- lógica de negócio em endpoints;
- acoplamento direto da interface com componentes de infraestrutura;
- abstrações excessivas para o escopo atual.

Simplificações por escopo:
- uso de servidor HTTP nativo simples em vez de framework web mais pesado;
- foco em uma base documental principal e um fluxo de RAG monolítico (não distribuído).

---

## 7. Justificativas Técnicas

- **Recuperação híbrida**: aumenta acurácia em perguntas com nomes e anos.
- **Prompts especializados**: melhora consistência da resposta por tipo de pergunta.
- **Fallback extrativo**: reduz respostas vazias quando há evidência parcial.
- **Módulo específico para listagem de alunos**: evita erro recorrente de entidade misturada.

Problemas evitados por essa organização:
- regressões em cascata por arquivo monolítico;
- duplicação de lógica entre CLI e API;
- dependências cíclicas entre módulos.

Benefício acadêmico:
- facilita mapear decisão arquitetural -> arquivo -> comportamento observável no sistema.

---

## 8. Integração com Modelo de Linguagem e RAG

### 8.1 Como documentos viram base de conhecimento

Os PDFs são convertidos em chunks textuais e indexados com embeddings em Chroma. Cada chunk carrega metadados de origem (arquivo e página), permitindo rastrear evidência.

### 8.2 Como ocorre a recuperação

Para cada pergunta, o sistema combina busca vetorial e BM25 lexical, consolidando e reranqueando candidatos por score final.

### 8.3 Como o prompt é montado

A aplicação concatena os chunks selecionados em contexto estruturado e aplica o template de prompt apropriado ao tipo de pergunta.

### 8.4 Como o modelo recebe contexto

O LLM recebe pergunta + contexto + regras explícitas de fidelidade (não inventar, usar somente contexto, indicar insuficiência quando necessário).

### 8.5 Como a resposta final é construída

A resposta candidata passa por auditoria e normalização. Ao final, retorna com referências de fontes (`Fontes usadas`).

### 8.6 Limitações e cuidados

- Se a evidência estiver ausente ou ambígua, o sistema pode retornar insuficiência;
- qualidade depende da qualidade textual dos PDFs;
- OCR/extração de páginas complexas pode gerar ruído;
- atualização da base exige reindexação.

---

## 9. Escalabilidade e Evolução Futura

A arquitetura atual suporta evolução incremental sem quebra estrutural:

- **Novos documentos**: adicionar arquivos em `base/` e reindexar.
- **Troca de modelo LLM**: ajustar `OPENAI_CHAT_MODEL` no `.env`.
- **Troca de mecanismo vetorial**: encapsulada em `infrastructure/vectorstore.py`.
- **Novos endpoints**: adicionar em `presentation/http_server.py` preservando casos de uso.
- **Melhoria de recuperação**: evoluir `infrastructure/retrieval.py` sem alterar interfaces de apresentação.
- **Novas funcionalidades**: incluir novos casos de uso em `application` e novas regras em `domain`.

Essa organização favorece crescimento com baixo acoplamento e menor risco de regressão.

---

## 10. Conclusão da Arquitetura

A arquitetura do Chatbot dos Titãs da Robótica foi desenhada para equilibrar precisão técnica, clareza estrutural e viabilidade de evolução. O sistema combina RAG, recuperação híbrida e prompts especializados para responder com fidelidade documental.

A separação em `presentation`, `application`, `domain`, `infrastructure` e `core` garante responsabilidade clara por módulo, facilita manutenção e fortalece a explicação acadêmica do projeto. Para o escopo do TCC, a solução entrega organização suficiente para qualidade de engenharia sem adicionar complexidade desnecessária.

Como resultado, o projeto permanece funcional, escalável e didaticamente defendável: cada parte do sistema tem propósito explícito, justificativa técnica e caminho de evolução definido.
