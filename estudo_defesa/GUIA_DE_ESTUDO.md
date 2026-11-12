# Guia de Estudo — Defesa do TCC

**Avaliação do Impacto da Geração Aumentada por Recuperação em Modelos de Linguagem**
Victor Lopes Pego · Victor Cordeiro de Sousa · Orientador: Jaimel de Oliveira Lima · Ifes Campus Colatina · Bacharelado em Sistemas de Informação

> Documento vivo: vamos ajustando conforme você estuda. A **fonte principal é o artigo do TCC** (`ART_TCC.pdf`, MNR 2026). Além dele, o guia usa os slides e o código do repositório (incluindo os resultados em `back/avaliacao_metricas/`). O artigo diagnóstico do TitãsBot ficou fora do TCC e saiu deste guia. Marcas: **[DO CÓDIGO]** para o que o código revela e o artigo não diz; **[CÁLCULO COMPLEMENTAR]** para números calculados só para a defesa; **[PONTO SENSÍVEL]** para o que a banca pode explorar, com resposta pronta no `ROTEIRO_DEFESA.md`. A seção 2.3 separa o que está no artigo do que vem só do código. **Para os testes e as métricas em profundidade (como cada uma calcula, com exemplos reais, e como se comporta em cada modelo), use o `TESTES_E_METRICAS.md`.**

---

## Sumário

1. [O trabalho em 1 minuto](#1-o-trabalho-em-1-minuto)
2. [O artigo do TCC, seção por seção](#2-o-artigo-do-tcc-seção-por-seção)
3. [Contexto: Titãs da Robótica e memória institucional](#3-contexto-titãs-da-robótica-e-memória-institucional)
4. [Fundamentação teórica](#4-fundamentação-teórica)
5. [O sistema TitãsBot por dentro (código)](#5-o-sistema-titãsbot-por-dentro-código)
6. [Desenho experimental (seção 4 do artigo)](#6-desenho-experimental-seção-4-do-artigo)
7. [As métricas, uma por uma](#7-as-métricas-uma-por-uma)
8. [Meta-avaliação: como se mede uma métrica](#8-meta-avaliação-como-se-mede-uma-métrica)
9. [Resultados com todos os números](#9-resultados-com-todos-os-números)
10. [Tabelas e figuras do artigo (e as que não estão nos slides)](#10-tabelas-e-figuras-do-artigo-e-as-que-não-estão-nos-slides)
11. [Exemplos reais para citar na defesa](#11-exemplos-reais-para-citar-na-defesa)
12. [Leitura crítica: limitações e pontos sensíveis](#12-leitura-crítica-limitações-e-pontos-sensíveis)
13. [Glossário rápido](#13-glossário-rápido)
14. [Referências e o que cada uma sustenta](#14-referências-e-o-que-cada-uma-sustenta)
15. [Cola de números (revisar no dia)](#15-cola-de-números-revisar-no-dia)
16. [A parte do Victor Pego](#16-a-parte-do-victor-pego-para-você-saber-não-para-apresentar)

---

## 1. O trabalho em 1 minuto

**Versão falada (decore a ideia, não as palavras):**

> LLMs escrevem bem, mas não conhecem o que é local: a história do Titãs da Robótica não está nos dados de treino deles. Quando não sabem, eles podem inventar com confiança, e isso é alucinação. O RAG resolve parte disso buscando trechos de documentos da equipe e entregando ao modelo antes de ele responder. Nós construímos o TitãsBot com RAG e testamos 40 perguntas em 3 modelos (Claude Haiku 4.5, DeepSeek Chat e GPT-5 mini), com e sem RAG, o que deu 240 respostas. Sem RAG, o acerto foi de 5,8%. Com RAG, foi de 51,7%. O ganho depende do tipo de pergunta: listas curtas melhoram muito, listas longas continuam difíceis. E depende de o recuperador achar a evidência: quando ela está entre os 5 primeiros trechos, o acerto vai a 60–70%; quando não está, cai para cerca de 10%. Por fim, comparamos 15 métricas automáticas para ver qual distingue resposta certa de errada. A G-Eval (baseada em LLM) e a METEOR (lexical, gratuita) empataram no topo, com AUC de 0,968 e 0,966. Métricas como Answer Relevancy ficaram no nível do acaso, porque medem outra coisa.

**As 5 frases que resumem tudo:**
1. O conhecimento paramétrico dos LLMs não cobre domínios locais; o RAG traz evidência externa no momento da inferência.
2. O RAG elevou o acerto de 5,8% para 51,7%, e o efeito do RAG foi muito maior que a diferença entre modelos.
3. O ganho não é uniforme: com RAG, listas curtas chegam a 72,5% e listas longas ficam em 27,3%, porque sofrem com omissões.
4. A recuperação é condição necessária, mas não suficiente: com evidência no top-5, o acerto fica entre 60% e 70%; sem ela, entre 9% e 10%.
5. Métricas não são intercambiáveis: lexicais simples empatam com G-Eval em separar certo de errado. Relevância e fidelidade não medem correção factual, e o limiar escolhido muda tudo.

---

## 2. O artigo do TCC, seção por seção

### 2.1 Identidade

- **Título:** *Avaliação do impacto da geração aumentada por recuperação em modelos de linguagem integrados a um chatbot especializado no domínio do Titãs da Robótica*.
- **Autores:** Victor Lopes Pego, Victor Cordeiro de Sousa, Jaimel de Oliveira Lima. Anais da MNR 2026, categoria Artigo Superior / Multimídia. São 10 páginas e 18 referências.
- **Vídeo:** a seção 7 traz o vídeo de apresentação (https://youtu.be/ZZMSgk9U9S0) e o QR code da Figura 10. Assista uma vez: a banca pode ter visto.
- **Relação com o que você já estudou:** é o artigo do RAG da primeira versão deste guia, com o mesmo texto, as mesmas tabelas, as mesmas figuras e os mesmos números. A única mudança é que a seção 4.2 ganhou três citações: **Fawcett (2006)** para AUC e ROC, **Brodersen et al. (2010)** para a acurácia balanceada e **McNemar (1947)** para o teste pareado.

### 2.2 Mapa: seção do artigo → slide → onde estudar

| Seção do artigo | O que diz | Slide | Guia |
|---|---|---|---|
| Resumo | Desenho (40 perguntas, 3 modelos, com e sem RAG, 240 respostas); 5,8% → 51,7%; listas curtas são as melhores com RAG; G-Eval tem a maior AUC; METEOR tem a maior BA estratificada em validação cruzada | 1 e 4 | 1 |
| 1. Introdução | LLM fluente não é LLM correto; o acervo dos Titãs está fragmentado; o RAG traz novas incertezas; avaliar também é um problema; as três questões (i), (ii) e (iii); objetivo; contribuição dupla (efeito do RAG + crítica dos instrumentos de medida) | 2 a 4 (Pego) | 3 e 4 |
| 2. Fundamentação | 2.1 IA, PLN e Transformer · 2.2 LLMs em domínios especializados (conhecimento paramétrico, alucinação) · 2.3 RAG ("não elimina alucinações") · 2.4 recuperação semântica, BM25 e chunking · 2.5 métricas lexicais, semânticas e por LLM | 2 e 5 | 4 e 7 |
| 3. O trabalho proposto | Ingestão com metadados; OpenAIEmbeddings; Chroma; busca híbrida vetorial + BM25 com cobertura de termos, números e intenção; contexto numerado; templates por tipo de consulta; auditoria; troca do gerador sem refazer a recuperação | 5 (Pego) | 5 |
| 4.1 Procedimento | 40 perguntas em 4 estratos (5/7/17/11); 3 modelos; 2 condições; fatos-chave; cortes de 100%, 75% e 80%; limitação: não penaliza fato extra | **6 (você)** | 6 |
| 4.2 Métricas e critérios | 15 métricas em três famílias; AUC (Fawcett); limiar por acurácia balanceada (Brodersen); validação leave-one-model-out; matrizes de confusão; McNemar exato (1947); análise agregada e por tipologia | **6 e 11** | 7 e 8 |
| 5.1 Efeito do RAG | 69 corretas e 171 incorretas; Tabela 1; Figura 1; Figura 2 (cobertura) | **7 e 8** | 9.1 e 9.2 |
| 5.2 Tipologia | Figuras 3 e 4; Tabela 2 (Hit@5) | **9 e 10** | 9.3 e 9.4 |
| 5.3 Comparação das métricas | Figura 5 (limiar); Tabela 3; Figura 6 (custo); Figura 7 (ranking); Figura 8 (ROC) | **11** | 8, 9.5 e 10 |
| 5.4 Capacidade discriminativa | Tabela 5 e Figura 9; o falso positivo é o erro mais grave; nenhuma métrica é árbitro universal; revisão humana nos casos de maior impacto; parágrafo-síntese | **12 e 13** | 9.6 |
| 6. Conclusões | O RAG muda substancialmente o desempenho; o ganho não é uniforme; métricas simples discriminam bem; as de LLM não dão vantagem uniforme; relevância e fidelidade não são correção; limitações em uma frase; continuidade | 14 (Pego) | 12 |
| 7. Vídeo | Link e QR code (Figura 10) | — | — |

### 2.3 O que está no artigo × o que vem só do código

A banca leu o artigo. **Na apresentação, os números do artigo são a base.** O que vem do código serve para responder com segurança. Quando usar, diga "nos dados do experimento" ou "no código".

| Informação | Está no artigo? | Onde estudar |
|---|---|---|
| Corpus de 3 PDFs, 289 páginas e 1.026 chunks; chunks de 900 caracteres com 180 de sobreposição | Não | 5 |
| Pesos da busca híbrida (0,50 / 0,30 / 0,15 / 0,05) | Não. O artigo só diz que entram cobertura de termos, números e intenção | 5.3 |
| O LLM gerador participa da recuperação (expansão de consulta e seleção de evidências) | Não. O artigo diz só que "um subconjunto de evidências é selecionado" | 5.4; Roteiro A5 |
| Modelo que avaliou nas métricas de LLM (`gpt-5-nano`, via DeepEval) | Não | 7; Roteiro C2 |
| Tamanho do subconjunto anotado para o Hit@5 (20 perguntas) | Não. O artigo diz "subconjunto com evidências anotadas" | 9.4 |
| Como funciona o limiar estratificado | Só o nome da coluna ("BA estrat.") | 8; Roteiro B7 e B9 |
| Regras fixas (q02, q39, q40) e a pista "Asimov" no prompt sem RAG | Não | 5.4 e 12; Roteiro A4 e A14 |
| Intervalos de confiança, bootstrap da AUC, McNemar entre modelos | Não. São cálculos complementares | 9 |
| Latência por modelo e a demo com `gpt-5-nano` | Não | Seção 16.5 (D8 e D12) |

### 2.4 Detalhes de forma que a banca pode notar

1. **A "Tabela 4" não existe.** No fim da seção 5.3, o texto diz que a AUC de 0,520 "permanece na Tabela 4", mas as tabelas são 1, 2, 3 e 5. A AUC está na Tabela 3. (Roteiro G1)
2. **0,968 ou 0,967?** O texto e a Tabela 3 dão AUC de 0,968 para a G-Eval; a legenda da Figura 8 dá 0,967. **[DO CÓDIGO]** O valor exato é 0,96745: com três casas, é 0,967. O 0,968 veio de arredondar duas vezes (0,96745 → 0,9675 → 0,968). O mesmo acontece com a `ref_projeto` (0,92050, que aparece como 0,920). Nada muda: G-Eval e METEOR (0,96568) continuam empatadas. (Roteiro G2)
3. **Cabeçalho "MNR 2019"** em algumas páginas, sobra do modelo do evento. (Roteiro G3)
4. **Decimal:** os gráficos usam ponto ("0.966") e o texto usa vírgula.
5. **A Figura 4 soma com e sem RAG.** No agregado dos 6 sistemas, o fato curto lidera (38,1%). Só com RAG, quem lidera é a lista curta (72,5%), como diz o Resumo. (Seção 9.3; Roteiro G4)
6. **As conclusões citam as limitações em uma frase só.** As outras estão espalhadas pelas seções 4.1, 5.2 e 5.3 (seção 12). (Roteiro G5)

---

## 3. Contexto: Titãs da Robótica e memória institucional

### 3.1 A equipe (fatos que podem aparecer na banca)

Fonte: gabarito oficial e o artigo diagnóstico do TitãsBot, que ficou fora do TCC. O artigo do TCC descreve o domínio em um parágrafo da Introdução. Isto é contexto para a parte do Pego e para a demo.

- **Origem:** entre 2009 e 2012, estudos no campus identificaram evasão ligada à dificuldade em programação. Em **2013** nasceu o projeto *Revitalização do Pavilhão de Informática Através de Jogos Educacionais*, coordenado pelo prof. **Renan Osório Rios**, com Arduino, Raspberry Pi e LEGO Mindstorms.
- **Idealização:** em **2014**, **Renato Lopes de Oliveira**, então estudante de Sistemas de Informação, propôs a equipe.
- **Institucionalização:** o projeto *Robótica educacional para o aprendizado de programação* foi submetido ao **CNPq em 2014**, e as atividades começaram em **2015**.
- **Nome:** primeiro **Asimov** (homenagem a Isaac Asimov), depois **Titãs da Robótica**, por **questões legais de registro de marca**.
- **Primeira competição:** **2015, na LARC**.
- **Modalidades:** SEK, Futebol 2D, CoSpace, Humanoide, Prática e Teórica (OBR). Subgrupos ao longo do tempo incluem ADM, Challenge, Drone, Lego Sumô, OBI, Osorin, Pesquisa e Seguidor de Linha.
- **Destaques:** OBR com títulos estaduais na prática e **1º lugar nacional em 2023**; RoboCup **2019 (12º, Soccer)**, **2024 (5º, Rescue, Eindhoven)** e **2025** (segundo o gabarito: SuperTeam 1º lugar no Mundial).
- **Escala:** **191 estudantes** ao longo da história (152 do sexo masculino e 39 do feminino), segundo o gabarito.
- **Extensão e social:** LETER (2019), Caderno Digital, *Introdução à Lógica por meio da Robótica*, Espaços do Saber; na pandemia, suportes de face shield por impressão 3D (mais de 5 mil por dia) e laringoscópios de baixo custo (cerca de R$ 60, contra mais de R$ 10 mil dos comerciais); app IFeira Colatina; **primeira equipe só de alunas em 2023**; robô **OSORIN** (ROS, SLAM, YOLO, RTAB-Map, A*).

### 3.2 O problema real que o TitãsBot ataca

- **Acervo de 10+ anos fragmentado:** livro, artigos, tabelas, registros de competições e projetos.
- **Alta rotatividade:** estudantes ficam poucos anos. O conhecimento tácito vai embora com eles.
- **Silos informacionais:** sem acesso rápido à memória da equipe, há retrabalho e erros repetidos.

### 3.3 Conceitos de memória institucional (apoio aos slides 2 e 3; não estão no artigo do TCC)

- **Walsh & Ungson (1991):** memória organizacional é informação da história da organização que pode ser **armazenada e depois recuperada**. A palavra-chave é *recuperada*: guardar não basta.
- **Nonaka & Takeuchi (1995):** conhecimento **tácito** (experiência, difícil de formalizar) e **explícito** (registrado). A continuidade depende de externalizar o tácito e torná-lo acessível.
- **Sistema conversacional orientado a conhecimento × orientado a conversa:** no TitãsBot, o critério principal não é a fluência, é a resposta estar **sustentada por evidência**. Por isso, dizer "não encontrei informação suficiente" é um comportamento **desejável** quando falta evidência.
- **Frase de efeito:** "O LLM não substitui a memória institucional; ele faz a mediação entre o usuário e os registros que a constituem."

---

## 4. Fundamentação teórica

> Autores citados nesta seção que não estão nas 18 referências do artigo (por exemplo, Russell & Norvig) estão na seção 14.2. Não diga que o trabalho os cita.

### 4.1 IA, PLN e Transformer

- **IA:** métodos computacionais para tarefas de percepção, inferência, aprendizagem, decisão e interação (Russell & Norvig).
- **PLN:** representação e processamento computacional da linguagem humana (classificação, tradução, recuperação de informação, pergunta e resposta, geração).
- **Transformer (Vaswani et al., 2017, *Attention Is All You Need*):** troca a recorrência (RNN/LSTM) por **self-attention**. Cada token "olha" para todos os outros e pondera a relevância de cada um, o que permite paralelizar o treino e capturar dependências longas. É a base de todos os LLMs atuais.
  - *Se perguntarem como funciona a atenção:* cada token gera três vetores, Query, Key e Value. O peso de atenção entre dois tokens é o produto escalar Query·Key, normalizado por softmax, e a saída é a média ponderada dos Values. A fórmula é Attention(Q,K,V) = softmax(QKᵀ/√d)·V.

### 4.2 LLMs e conhecimento paramétrico

- Um **modelo de linguagem** estima a probabilidade da próxima unidade (token) dado o contexto. Um LLM gerativo produz texto token a token.
- **Escala (Brown et al., 2020, GPT-3):** modelos grandes fazem tarefas novas só com instruções e exemplos no prompt (*few-shot* ou *in-context learning*), sem treino específico.
- **Conhecimento paramétrico:** o que o modelo "sabe" fica distribuído nos pesos. Isso traz três problemas: (1) não dá para atualizar seletivamente sem retreinar; (2) não dá para rastrear a fonte de uma afirmação; (3) fatos locais e raros quase não aparecem no treino.
- **Fluência ≠ veracidade:** essa é a tese que atravessa o trabalho.

### 4.3 Alucinação (Ji et al., 2023)

- **Definição:** texto fluente e plausível, mas sem suporte na fonte ou contraditório com os fatos.
- **Tipos clássicos:** *intrínseca* (contradiz a fonte fornecida) e *extrínseca* (acrescenta algo que não dá para verificar pela fonte).
- **No TitãsBot:** sem RAG, os modelos ou admitem não saber, ou inventam (por exemplo, sugerem competições como FIRST/FLL que a equipe não disputa). Com RAG, a alucinação diminui, mas não some, porque o modelo ainda pode errar ao usar o contexto.

### 4.4 RAG — Retrieval-Augmented Generation (Lewis et al., 2020)

- **Ideia:** combinar uma **memória paramétrica** (o LLM) com uma **memória não paramétrica** (documentos indexados e recuperáveis).
- **Pipeline:** (1) **recuperação**: a pergunta vira consulta e o sistema busca os trechos mais relevantes; (2) **contextualização**: os trechos entram no prompt; (3) **geração**: o LLM responde condicionado ao contexto.
- **Vantagens:** conhecimento atualizável (basta reindexar), especialização por domínio sem treinar o modelo, rastreabilidade das fontes.
- **O RAG não elimina a alucinação:** o recuperador pode trazer trechos errados ou incompletos, e o gerador pode interpretar mal, omitir ou misturar com o que já "sabia".
- **Gao et al. (2023/2024, survey):** organiza o RAG em *Naive*, *Advanced* e *Modular*, com estratégias antes da recuperação (reescrita e expansão de consulta), durante (busca híbrida) e depois (reranking, compressão de contexto). O TitãsBot é um **RAG avançado**: tem expansão de consulta, busca híbrida, seleção de evidências por LLM e auditoria da resposta.
- **Liu et al. (2024, *Lost in the Middle*):** LLMs usam pior a informação que fica no meio de contextos longos. Mais contexto não significa mais uso efetivo.
- **Asai et al. (2023, Self-RAG):** o modelo decide quando recuperar e critica a própria resposta. O TitãsBot tem uma ideia parecida na etapa de **auditoria**.
- **Es et al. (2023, RAGAS):** avaliação de RAG em dimensões como fidelidade ao contexto e relevância. As métricas Faithfulness e Answer Relevancy do DeepEval seguem essa linha.

### 4.5 Recuperação: vetorial, lexical e híbrida

**Embeddings:** convertem texto em vetor (no TitãsBot, `text-embedding-3-small` da OpenAI). Textos de significado próximo ficam próximos no espaço.
- **Similaridade por cosseno:** cos(u, v) = (u·v) / (‖u‖·‖v‖). Vale 1 para a mesma direção e perto de 0 para textos sem relação.
- **Sentence-BERT (Reimers & Gurevych, 2019):** gera embeddings de frase comparáveis, o que viabiliza busca semântica eficiente.
- **MiniLM (Wang et al., 2020):** destila um Transformer grande num modelo pequeno e rápido. É usado aqui **na avaliação** (métrica cosseno), não na recuperação.
- **DPR (Karpukhin et al., 2020):** mostrou que a recuperação densa (vetorial) supera a lexical em QA de domínio aberto.

**BM25 (Robertson & Zaragoza, 2009):** ranking lexical probabilístico.
- Fórmula, por termo da consulta: IDF(q) · [tf · (k1 + 1)] / [tf + k1 · (1 − b + b · |D| / avgdl)]
  - **tf:** quantas vezes o termo aparece no trecho. **IDF:** termos raros pesam mais. **|D|/avgdl:** normaliza pelo tamanho do trecho.
  - **[DO CÓDIGO]** k1 = 1,5 e b = 0,75 (valores clássicos); IDF = ln(1 + (N − df + 0,5) / (df + 0,5)). Implementação própria em `back/app/infrastructure/retrieval.py`.
- **Por que híbrido?** O vetorial entende paráfrase ("quando surgiu a equipe" ≈ "ano de criação"), mas é fraco para **nomes próprios, siglas, anos e colocações**, que são exatamente o conteúdo do acervo dos Titãs. O BM25 cobre isso.

**Chunking:** documentos grandes são quebrados em pedaços. Pedaços grandes demais trazem ruído; pequenos demais quebram o fato (o nome fica num chunk e a colocação no outro). **[DO CÓDIGO]** O TitãsBot usa 900 caracteres com sobreposição de 180 (`RecursiveCharacterTextSplitter`). A sobreposição evita perder uma frase cortada na fronteira.

### 4.6 Avaliação de geração de texto: três famílias

| Família | Ideia | Exemplos | Ponto fraco |
|---|---|---|---|
| **Lexical** | Sobreposição de palavras ou caracteres com a referência | Exact Match, Token F1, BLEU, ROUGE-1/2/L, METEOR, chrF | Penaliza paráfrase correta |
| **Semântica** | Proximidade de significado via embeddings | BERTScore, cosseno MiniLM | Texto "parecido" pode errar nome ou data |
| **Baseada em LLM** | Um LLM julga segundo critérios | G-Eval, Answer Relevancy, Faithfulness, Hallucination | Custo, lentidão, não determinismo, dependência do prompt e do modelo avaliador |

Essas propriedades **não são intercambiáveis**: uma resposta pode ser relevante, semanticamente parecida e fiel ao contexto e, mesmo assim, errar uma data. Essa é a frase central da pergunta de pesquisa III.

---

## 5. O sistema TitãsBot por dentro (código)

### 5.1 Stack e arquitetura em camadas

- **Backend:** Python, LangChain 1.x, ChromaDB (banco vetorial), OpenAI embeddings, servidor HTTP próprio (`ThreadingHTTPServer`, rotas `/health` e `/chat`).
- **Frontend:** React 19, Vite, TypeScript, Tailwind, react-markdown.
- **Deploy:** Docker multi-stage no **Google Cloud Run** (`https://titasbot-uxzg5xqawa-uc.a.run.app`). **[DO CÓDIGO]** A versão publicada usa **gpt-5-nano** como gerador (barato), que **não é** um dos três modelos avaliados (`deploy/deploy_cloud_run.ps1`). No teste de 08/11, a primeira chamada levou cerca de 30 s só para acordar o servidor, e as respostas levaram de 10 a 50 s (roteiro da demo no `ROTEIRO_DEFESA.md`, seção 3).
- **Camadas** (`back/ARQUITETURA.md`):
  - `presentation/`: CLI e HTTP
  - `application/`: orquestração RAG (`chat_service.py`), prompts, auditoria
  - `domain/`: intenções e regras (tipo de pergunta, pedidos conversacionais)
  - `infrastructure/`: configuração, ingestão, Chroma, recuperação híbrida, fábrica de LLMs
  - `core/`: modelos compartilhados
- **Multi-provedor** (`llm_factory.py`): a mesma interface `invoke()` funciona para OpenAI, Anthropic, DeepSeek e Gemini. **É isso que permite trocar só o gerador e manter o resto do pipeline**, a base do experimento com três modelos.

### 5.2 Ingestão (preparação da base)

**[DO CÓDIGO]** (`back/app/infrastructure/ingestion.py`, `settings.py`)
- **Fontes:** 3 PDFs em `back/base/`: o **livro de 10 anos** da equipe (cerca de 246 páginas), o **artigo MNR 2025** (8 páginas) e o **Tabelas.pdf** (35 páginas).
- Cada página vira texto (pypdf) com metadados: arquivo, página e `doc_kind` (`table` se o nome do arquivo contém "tabela", "lista", etc.; senão `context`).
- **Resultado [CÁLCULO COMPLEMENTAR]:** 289 páginas com texto → **1.026 chunks** (894 do livro, 72 das tabelas, 60 do artigo), com média de 769 caracteres.
- Os chunks são embutidos com `text-embedding-3-small` e salvos no Chroma (coleção `titas_docs`).

### 5.3 Recuperação híbrida

**[DO CÓDIGO]** (`HybridRetriever.retrieve`, em `retrieval.py`)
1. **Busca vetorial:** top **k = 12** por relevância no Chroma.
2. **BM25:** top **36** (12 × 3).
3. **Fusão:** une os candidatos e normaliza o BM25 pelo máximo.
4. **Nota final de cada chunk:**

```
final = 0,50·vetorial + 0,30·BM25 + 0,15·cobertura + 0,05·número
        + bônus de intenção + ajuste de ano
```

- **cobertura:** fração dos tokens da pergunta presentes no chunk.
- **número:** 1 se um número da pergunta (por exemplo, um ano) aparece no chunk.
- **ajuste de ano:** +0,22 se o ano da pergunta aparece; −0,18 se o chunk tem outros números mas não o ano pedido.
- **bônus de intenção:** perguntas de lista, competição ou estudantes favorecem chunks de **tabela** (+0,08 a +0,16); perguntas de história favorecem `context` (+0,06).

5. Filtra por nota mínima (0,08), mantém **até 8 chunks** e, em perguntas de lista, garante chunks de tabela no topo.

> **Por que esses pesos?** Foram ajustados empiricamente durante o desenvolvimento, para um corpus cheio de nomes, anos e colocações. **[PONTO SENSÍVEL]** Não houve um estudo de ablação formal dos pesos, e isso é um trabalho futuro legítimo.

### 5.4 Orquestração de uma pergunta: `TitasBotService.ask()`

**[DO CÓDIGO]** (`back/app/application/chat_service.py`). Essa é a ordem real dos passos e vale saber de cor:

1. **Atalhos de regra:** perguntas sabidamente sem resposta na base, mensagens sociais ("oi", "obrigado") e pedidos conversacionais ("resuma", "em tópicos") são respondidos sem recuperação.
2. **Consulta de recuperação:** `precision_query_boost` reforça termos. Em perguntas de lista, acrescenta pistas como "usar arquivo de listagens/tabelas". Em perguntas de continuidade, o LLM decide se usa o histórico (`CONTEXT_DECISION_PROMPT`).
3. **Expansão de consulta (usa o LLM gerador):** gera até 3 variações curtas da consulta (`QUERY_EXPANSION_PROMPT`), roda a busca híbrida para cada uma e une os resultados. Não é aplicada quando a pergunta já tem ano e é direta.
4. **Filtro de relevância para a equipe:** descarta trechos de outras equipes ou projetos.
5. **Atalhos determinísticos:**
   - pergunta sobre o **primeiro nome da equipe** → se algum chunk contém "Asimov", responde "O primeiro nome da equipe foi Asimov." (`_known_team_alias_answer`);
   - **lista de estudantes** → extração determinística de nomes das tabelas (`student_list.py`).
6. **Seleção de evidências (usa o LLM gerador):** com mais de 5 chunks, o LLM escolhe de 3 a 8 IDs (`EVIDENCE_SELECTION_PROMPT`). Em perguntas de lista, prioriza tabelas.
7. **Contexto numerado:** `[1] arquivo (página N)\n texto`, separado por `---`.
8. **Geração com prompt por tipo:** lista de estudantes, participação, projetos, lista, fato ou geral (`prompts.py`). Todos dizem "não invente" e mandam responder exatamente *"Não encontrei informação suficiente na base para responder com segurança."* quando faltam dados.
9. **Fallback extrativo:** se o LLM disse "insuficiente" mas há evidência mínima, o sistema extrai frases relevantes dos chunks.
10. **Auditoria:** o LLM revisa a resposta contra o contexto e devolve `STATUS: OK/FIX`, `USED_IDS` e `ANSWER`. Pode manter, corrigir ou trocar pela mensagem de insuficiência.
11. **Reenfoque**, se a resposta não atinge o alvo da pergunta (`STRICT_REFOCUS_PROMPT`).
12. **Auditoria de escopo da equipe** (`TEAM_SCOPE_AUDIT_PROMPT`).
13. **Canonicalização de listas:** deduplicação textual e depois semântica (LLM).
14. **Fontes:** acrescenta "Fontes usadas" com arquivo e página.

**Consequências que você precisa saber explicar:**
- Uma pergunta pode disparar de **4 a 7 chamadas ao LLM** (expansão, seleção, geração, auditoria, escopo, canonicalização). Isso tem impacto em custo e latência.
- **[PONTO SENSÍVEL]** Como a expansão e a seleção usam o **mesmo LLM que gera**, o contexto final **não é idêntico entre os modelos**. O índice, os embeddings, o algoritmo e os pesos são idênticos, mas o "sistema" avaliado é *modelo + pipeline*. Isso explica por que o Hit@5 varia entre 45% e 50% entre os modelos.
- **[PONTO SENSÍVEL]** Nas perguntas q02 (nome Asimov) e q39 (lista de 191 estudantes), a resposta com RAG vem de **regra**, não do LLM. Nelas, os três modelos têm comportamento praticamente igual com RAG.
- **[PONTO SENSÍVEL]** Na **q40** (valor total captado em patrocínio), nem há recuperação. O passo 1 (`is_known_absent_detail_question`, em `back/app/domain/intents.py`) tem uma lista de frases de perguntas sabidamente sem resposta, e ela inclui literalmente "valor total captado". O sistema devolve a mensagem de insuficiência na hora, sem busca e sem LLM. **As 3 respostas com RAG da q40 vieram dessa regra**, e é por isso que não têm trechos (daí a Faithfulness com n = 117). Na demo publicada, essa pergunta responde em 0,3 s; não a use na apresentação.
- A temperatura é configurada como 0, mas alguns modelos (família GPT-5) não aceitam temperatura. O wrapper então chama sem ela, e a geração não é totalmente determinística.

### 5.5 Arquitetura do slide 5 × arquitetura real

O slide mostra **Ingestão → Busca híbrida → Contexto → Geração**, e está correto como visão de alto nível. Se a banca pedir mais detalhe, acrescente: "entre a busca e a geração há expansão de consulta e seleção de evidências, e depois da geração há uma auditoria da resposta contra o contexto, que pode corrigir a resposta ou declarar insuficiência".

---

## 6. Desenho experimental (seção 4 do artigo)

### 6.1 Natureza da pesquisa

Aplicada e **experimental**: usa um sistema implementado para observar, sob condições controladas, o efeito de uma variável (presença ou ausência de RAG) e de outra (modelo) sobre um desfecho (correção da resposta). É um **desenho fatorial 3 × 2 com medidas repetidas** (as mesmas 40 perguntas passam por todas as 6 combinações).

### 6.2 As 40 perguntas

- **Origem:** gabarito oficial ("Conjunto de Perguntas e Respostas — TitãsBot", entregue pelo orientador), em `back/tests/evals/model_eval_cases.json`.
- **Categorias temáticas** (8): história, resultados, orientadores, métricas históricas, projetos, tecnologia, institucional, financeiro.
- **Estratos por tipo de resposta** (`metric_eval_annotations.json`):

| Estrato | Nº | Perguntas | Cobertura mínima para "correta" |
|---|---|---|---|
| **Fato curto** | 7 | 2, 3, 5, 7, 30, 33, 40 | **100%** |
| **Descritiva** | 5 | 1, 4, 6, 35, 36 | **75%** |
| **Lista curta** (≤ 8 itens) | 17 | classificações de 2015, 2016, 2018 e 2020–2024; orientadores de 2015–2018, 2020, 2022, 2024 e 2025; campeonatos (q32) | **80%** |
| **Lista longa** (> 8 itens) | 11 | classificações de 2017, 2019 e 2025; orientadores de 2019, 2021 e 2023; subgrupos (q31); projetos (q34); patrocinadores (q37); 20 orientadores (q38); **191 estudantes (q39)** | **80%** |

- **Por que estratos por tipo, e não pelas 8 categorias?** Algumas categorias têm 1 ou 2 perguntas (estatística instável), e o comportamento das métricas muda com o formato: métricas lexicais penalizam respostas curtas parafraseadas e favorecem listas copiadas.
- **Importante:** a classificação **não é uma escala de dificuldade**. Ela distingue quantidade e organização da informação exigida.

### 6.3 Modelos e condições

- **Modelos:** `gpt-5-mini` (OpenAI), `claude-haiku-4-5-20251001` (Anthropic), `deepseek-chat` (DeepSeek).
  - **Por que esses?** São da **faixa intermediária** de cada empresa, nem os mais fortes nem os mais fracos, o que deixa a comparação justa e realista em custo para uma instituição pública. São três fornecedores diferentes, incluindo um chinês.
- **Sem RAG:** o modelo recebe só a pergunta e um prompt de sistema.
  - **[DO CÓDIGO]** O prompt é: *"Você é o TitasBot, assistente sobre a equipe Titãs da Robótica (IFES Campus Colatina; a equipe já se chamou Asimov). Responda em português, de forma objetiva e fiel ao que você sabe. Se não tiver a informação, diga isso."*
  - **[PONTO SENSÍVEL]** Esse prompt **revela** "Asimov" e "Ifes Campus Colatina". Isso explica por que os três modelos acertaram sem RAG a **q01** ("Quem são os Titãs?") e a **q02** ("primeiro nome"). Dos 7 acertos sem RAG, 6 vêm daí. O sétimo é do DeepSeek na q40, uma pergunta cuja resposta certa é "não há informação". **Efeito:** a linha de base sem RAG ficou levemente inflada, ou seja, **o ganho do RAG está, se algo, subestimado** (é uma estimativa conservadora).
- **Com RAG:** a pergunta percorre o pipeline completo do TitãsBot (`bot.ask()`).
- **Total:** 40 × 3 × 2 = **240 respostas**.

### 6.4 Pipeline de avaliação em 3 etapas (com cache)

**[DO CÓDIGO]** Cada etapa grava arquivo e retoma de onde parou, para não pagar chamadas de API repetidas:
1. `scripts/generate_answers.py` → `respostas.jsonl` (respostas, consulta usada e os 8 chunks selecionados). Uma falha de API vira erro registrado, **não** uma resposta vazia rotulada como incorreta.
2. `scripts/score_answers.py` → `scores.jsonl` (métricas tradicionais, recuperação e DeepEval com 8 workers em paralelo).
3. `scripts/analyze_metrics.py` → `analise_metricas.json`, CSVs e relatório HTML (`comparacao_metricas.html`).

### 6.5 A "verdade": cobertura de fatos-chave → rótulo binário

**[DO CÓDIGO]** (`back/app/evaluation/ground_truth.py`)

1. Cada resposta do gabarito foi **decomposta em fatos-chave** revisados manualmente (nomes, datas, colocações, itens de lista).
2. Três tipos de fato:
   - **`terms`:** termos ou regex que precisam aparecer (por exemplo, "Asimov", "2014", "CNPq"). Aceita alternativas.
   - **`name`:** nome de pessoa. Basta **primeiro nome + um sobrenome identificador** (tolera nomes do meio omitidos e variações como Luis/Luiz e Alan/Allan).
   - **`placement`:** "Modalidade: Nº lugar — COMPETIÇÃO (Nível)". **Modalidade, colocação e competição precisam aparecer no mesmo trecho** (mesma linha, ou linha mais os 2 cabeçalhos acima). Aceita sinônimos ("1º lugar", "primeiro lugar", "campeão"; "OBR" = "Olimpíada Brasileira de Robótica").
3. **Cobertura** = fatos encontrados ÷ total de fatos.
4. **Rótulo** = 1 (correta) se cobertura ≥ mínimo do estrato (100/75/80/80%); senão 0.
5. **Testes automatizados:** cada gabarito precisa cobrir 100% dos próprios fatos; o rótulo é orientado como 1 = correta; outros anos não contam como acerto; nomes toleram o nome do meio omitido; uma colocação exige o mesmo trecho.

**Por que essa verdade e não um LLM-juiz?** Por orientação do orientador, nenhuma etapa usa um LLM para *inventar* o rótulo de verdade. Isso evitaria circularidade (usar LLM para avaliar métricas de LLM). A cobertura é **reprodutível, auditável e barata**.

**Limitação assumida no artigo:** a cobertura mede **presença** dos fatos esperados, mas **não penaliza um fato extra inventado**. Por isso o rótulo é tratado como "referência operacional", não como verdade absoluta.

### 6.6 Métricas aplicadas

- **11 tradicionais (determinísticas, rodam localmente):** Exact Match, Token F1, BLEU-4, chrF, ROUGE-1, ROUGE-2, ROUGE-L, METEOR, cosseno MiniLM, BERTScore F1, `ref_projeto`.
- **4 DeepEval (usam LLM):** G-Eval Correctness, Answer Relevancy, Faithfulness (só com RAG) e 1 − Hallucination.
  - **LLM de apoio:** `gpt-5-nano` (OpenAI). **Não é um juiz separado**: ele só executa os passos internos das métricas do DeepEval (extrair afirmações, pontuar critérios).
- **Recuperação (diagnóstico, fora do ranking):** Hit@5 e Precision@5 nas 20 perguntas com evidências anotadas (`rag_stage_eval_cases.json`).

---

## 7. As métricas, uma por uma

Para cada métrica: o que mede, a intuição, a fórmula essencial, a armadilha e como ela se saiu aqui. Os resultados completos estão na seção 9.

> Exemplo usado: referência = *"O primeiro nome da equipe era Asimov."*; resposta = *"A equipe se chamava Asimov no início."*

### 7.1 Lexicais

**Exact Match (EM).** Vale 1 se resposta e referência são idênticas depois de normalizar (minúsculas, sem acento e sem pontuação); senão 0. No exemplo, dá 0. Respostas de LLM quase nunca são idênticas ao gabarito. **AUC 0,594**: só acerta respostas copiadas literalmente. É binária, então não serve como régua contínua.

**Token F1 (estilo SQuAD).** Conta os tokens em comum.
- Precisão = comuns ÷ tokens da resposta; Revocação = comuns ÷ tokens da referência; F1 = 2PR / (P + R).
- No exemplo (7 tokens em cada texto), os comuns são {equipe, asimov}: P = 2/7, R = 2/7, F1 ≈ 0,29. A resposta está certa e a nota fica baixa, o que ilustra como métricas lexicais penalizam paráfrase.
- **AUC 0,946.**

**BLEU-4 (Papineni et al., 2002).** Nasceu na tradução automática.
- É a média geométrica das **precisões** de n-gramas (n = 1 a 4) vezes uma **penalidade por brevidade**. Usa suavização (`method1`) para não zerar quando não há 4-gramas em comum.
- **Armadilha:** é orientado à precisão e fica muito baixo em textos longos e livres (por isso o limiar ótimo é 0,10).
- **AUC 0,951.**

**ROUGE-1, ROUGE-2 e ROUGE-L (Lin, 2004).** Nasceu na sumarização.
- ROUGE-N mede a sobreposição de n-gramas (unigramas ou bigramas). ROUGE-L usa a **maior subsequência comum** (LCS), que respeita a ordem sem exigir contiguidade. Aqui se usa o F-measure.
- **AUC:** ROUGE-1 0,943; ROUGE-2 0,945; ROUGE-L 0,952.

**chrF (Popović, 2015).** F-score de **n-gramas de caractere** (até 6).
- **Vantagem no português:** tolera flexão ("competição" e "competições" compartilham muitos n-gramas de caractere).
- **[DO CÓDIGO]** A implementação do nltk usa β = 3, ou seja, a **revocação pesa 3 vezes mais** que a precisão.
- **AUC 0,963** (3ª melhor).

**METEOR (Banerjee & Lavie, 2005).**
- Alinha unigramas entre resposta e referência por correspondência exata, por radical (*stem*) e por sinônimos (WordNet). Calcula um **F-mean com peso maior na revocação** e aplica uma **penalidade de fragmentação**: quanto mais "pedaços" desconexos no alinhamento, maior a penalidade (a métrica recompensa manter a ordem).
- Fórmula (nltk): Fmean = P·R / (α·P + (1 − α)·R), com α = 0,9; Penalidade = 0,5·(chunks/matches)³; Score = Fmean·(1 − Penalidade).
- **[PONTO SENSÍVEL]** O WordNet e o *stemmer* são **do inglês**. Em português, o METEOR funciona quase como um F-mean de palavras exatas com penalidade de ordem. **Mesmo assim, foi a melhor métrica em acurácia balanceada estratificada.**
- **Por que o METEOR funcionou tão bem aqui?** Porque "estar correta" neste domínio é, essencialmente, **conter os nomes, anos e colocações da referência**. Isso é **revocação**, e o METEOR é orientado à revocação. A penalidade de fragmentação também recompensa listas na mesma ordem das tabelas.
- **AUC 0,966**; BA estratificada (CV) **0,891**, a maior.

### 7.2 Semânticas

**Cosseno MiniLM.** Converte resposta e referência em vetores de frase (`paraphrase-multilingual-MiniLM-L12-v2`) e calcula o cosseno.
- **[DO CÓDIGO]** Corrigiu um defeito importante: o modelo corta em 128 tokens, e o gabarito da lista de 191 estudantes tem 1.164 tokens (cerca de 89% do texto seria ignorado). A solução foi processar em blocos de até 128 tokens e fazer a média ponderada pelo tamanho (`reference_scorer.py`, `_embed_long_text`).
- **Armadilha:** "Asimov" e "Titãs" podem ficar próximos no espaço vetorial, então ele tolera erros factuais.
- **AUC 0,903**, a pior das semânticas.

**BERTScore F1 (Zhang et al., 2020).** Embeddings **contextuais por token** (`bert-base-multilingual-cased`). Cada token de um texto é casado com o mais parecido do outro (cosseno), o que dá P, R e F1.
- **[DO CÓDIGO]** Rodou **sem *rescale with baseline***, então os valores ficam comprimidos entre cerca de 0,55 e 0,93 (até respostas erradas têm ~0,60). Por isso o limiar ótimo é alto (0,70).
- **AUC 0,944.**

**`ref_projeto`.** É a fórmula do **projeto de referência** indicado pelo orientador (Visualizador-do-avaliador): **0,8 × cosseno MiniLM + 0,2 × SequenceMatcher** (difflib, similaridade de caracteres). Foi incluída para comparação direta com esse projeto.
- **[PONTO SENSÍVEL]** Os pesos 80/20 vêm da justificativa conceitual do projeto de referência, não de uma calibração empírica.
- **AUC 0,920.**

### 7.3 Baseadas em LLM (DeepEval, com `gpt-5-nano` de apoio)

**G-Eval Correctness (Liu et al., 2023).**
- **Como funciona:** (1) a partir de um **critério** em linguagem natural, o LLM gera os **passos de avaliação** (cadeia de raciocínio); (2) recebe pergunta, resposta e resposta esperada e dá uma nota.
- No artigo original, a nota é **ponderada pelas probabilidades dos tokens** (logprobs). **[DO CÓDIGO / VERIFICADO]** Com `gpt-5-nano`, que não fornece logprobs ao DeepEval, a nota é um **inteiro de 0 a 10 dividido por 10**. Por isso os valores observados são só 0,0; 0,1; …; 1,0.
- **Critério usado [DO CÓDIGO]:** "Determine se a resposta real está correta em relação à resposta esperada. Aceite variações de redação, mas penalize fatos ausentes, anos errados, classificações erradas ou invenção de informações. Não penalize detalhes adicionais quando forem compatíveis com a resposta esperada e não mudarem o sentido principal."
- **Entradas:** input, actual_output e expected_output (**usa o gabarito**).
- **Não determinismo:** repetindo 3 vezes em 36 respostas, o desvio-padrão médio foi de 0,056, e a amplitude máxima chegou a 0,4 (a mesma resposta recebeu notas com 0,4 de diferença).
- **AUC 0,968** (a maior), sem diferença significativa para o METEOR (seção 9.6).

**Answer Relevancy.**
- **Como funciona:** o LLM extrai as **afirmações** da resposta e classifica cada uma como relevante ou não para a **pergunta**. Score = relevantes ÷ total.
- **Não usa o gabarito.** Ela mede se a resposta fala do assunto da pergunta, não se está certa.
- **[VERIFICADO no código do DeepEval 4.0.2]** Se não houver afirmações (por exemplo, "Não encontrei informação"), o score é **1,0**.
- **Consequência:** respostas sem RAG (95% erradas) tiveram relevância média de **0,97**; com RAG, ~0,80–0,94. No nível de sistema, ela ordena os sistemas **ao contrário** da verdade (Kendall τ = −0,79).
- **AUC 0,520**, igual ao acaso.

**Faithfulness.**
- **Como funciona:** extrai as **afirmações** da resposta e as **verdades** do contexto recuperado (até 8), e verifica se cada afirmação **não contradiz** o contexto. Score = fiéis ÷ total.
- Só se aplica **com RAG** (precisa de `retrieval_context`). **[DO CÓDIGO]** Foram **117 respostas**: as 3 respostas com RAG da q40 não tinham chunks, porque foram respondidas por regra (seção 5.4), e foram puladas. O contexto entregue à métrica são os 5 primeiros chunks, cada um cortado em 1.200 caracteres.
- **Armadilha:** uma resposta **fiel a um contexto incompleto** recebe nota alta e está errada; uma recusa recebe 1,0.
- **AUC 0,557.**

**Hallucination (usada invertida: `hallucination_inv` = 1 − Hallucination).**
- **[VERIFICADO no DeepEval 4.0.2]** Hallucination = contextos **contraditos pela resposta** ÷ total de contextos (quanto menor, melhor). O código inverte para "maior = melhor", como as demais.
- O "contexto" usado foi o **próprio gabarito** (um único documento). **Com um só contexto, a nota é binária** (0 ou 1): "a resposta contradiz o gabarito ou não?". Isso foi confirmado nos dados: 159 respostas com 1,0, 79 com 0,0 e só 2 valores intermediários.
- **Armadilha:** mede **contradição, não omissão**. Uma resposta que omite 80% dos itens mas não contradiz nada recebe 1,0.
- **AUC 0,658.**

### 7.4 Métricas de recuperação

**[DO CÓDIGO]** (`rag_stage_scorer.py`)
- Para cada uma das 20 perguntas anotadas, há uma lista de **termos de evidência** (ex.: q07 → "2015" e "LARC"), um mínimo de termos para um chunk ser **relevante** e outro para ser **suficiente**.
- **Hit@5:** vale 1 se **algum** dos 5 primeiros chunks é **suficiente**.
- **Precision@5:** número de chunks **relevantes** ÷ 5 (o denominador é fixo, mesmo que venham menos chunks).
- Uma pergunta pode ter Hit@5 = 1 com Precision@5 baixa (basta um chunk bom).

---

## 8. Meta-avaliação: como se mede uma métrica

A pergunta III é: **quão bem cada métrica separa respostas corretas de incorretas?** Para responder, cada métrica é tratada como um **classificador**: *score ≥ limiar ⇒ "correta"*.

### 8.1 Matriz de confusão (classe positiva = "correta")

| | Prevista correta | Prevista incorreta |
|---|---|---|
| **Realmente correta** | **VP** (aprovou certa) | **FN** (rejeitou certa: penaliza paráfrase) |
| **Realmente incorreta** | **FP** (aprovou errada: o erro perigoso) | **VN** (rejeitou errada) |

- **Sensibilidade** (revocação da classe correta) = VP / (VP + FN): das respostas certas, quantas a métrica aprova?
- **Especificidade** = VN / (VN + FP): das erradas, quantas ela barra?
- **Por que o FP pesa mais num chatbot institucional?** Porque dá aparência de validade a uma informação errada sobre pessoas, datas e premiações.

### 8.2 Acurácia × acurácia balanceada

- Há 69 corretas (28,75%) e 171 incorretas (71,25%): **as classes são desbalanceadas**.
- Um "classificador" que diz sempre "incorreta" teria **71,25% de acurácia** sem saber nada.
- **Acurácia balanceada** = (sensibilidade + especificidade) / 2 (Brodersen et al., 2010). O classificador "sempre incorreta" fica com 50%, que é o nível do acaso.
- **Exemplo:** METEOR com VN = 161, FP = 10, FN = 15, VP = 54 → especificidade 161/171 = 94,2%; sensibilidade 54/69 = 78,3%; **BA = 86,2%**.

### 8.3 AUC-ROC (Fawcett, 2006)

- A **curva ROC** traça sensibilidade × (1 − especificidade) para **todos os limiares** possíveis. A **AUC** é a área sob ela.
- **Interpretação que você deve saber falar:** *"A AUC é a probabilidade de uma resposta correta, sorteada ao acaso, receber nota maior que uma incorreta sorteada ao acaso."* 0,5 é acaso; 1,0 é separação perfeita.
- **[DO CÓDIGO]** É calculada pelo método de **Mann–Whitney**: compara todos os 69 × 171 = 11.799 pares (correta, incorreta) e conta 1 se a correta tem nota maior e 0,5 em caso de empate. Uma AUC de 0,966 significa que ~96,6% dos pares ficam na ordem certa.
- **A AUC independe do limiar.** Ela mede a **capacidade de ordenar**, não a qualidade de uma decisão concreta.

### 8.4 Limiar global, varredura e limiar estratificado

- **Varredura:** limiares de 0,00 a 1,00 em passos de 0,05. Para cada um, calculam-se a matriz e a BA, e escolhe-se o que maximiza a BA (em empate, o mais próximo de 0,5).
- **Global:** um limiar para todas as respostas (ex.: METEOR 0,35).
- **Estratificado:** um limiar por tipo de resposta. Ex.: METEOR com descritiva 0,35, fato curto 0,35, lista curta 0,55 e lista longa 0,60.
  - **Por que listas precisam de limiar maior?** Uma lista copiada da tabela tem muita sobreposição de palavras **mesmo incompleta**. Para exigir completude, a régua sobe.
  - Estratos com menos de 6 respostas ou com uma só classe usam o limiar global.

### 8.5 Validação cruzada *leave-one-model-out* (LOMO)

- **Problema:** escolher o limiar e medir o desempenho **nos mesmos dados** é otimista (sobreajuste do limiar), principalmente no estratificado, que tem 4 limiares.
- **Solução:** calibrar os limiares com as respostas de **2 modelos** (160 respostas) e aplicá-los ao **3º** (80 respostas, nunca vistas na calibração). Repete-se 3 vezes, trocando o modelo de fora, e juntam-se as 240 previsões numa matriz única.
- **O que isso testa:** se a regra de decisão **generaliza para um gerador novo**, que é o cenário real (amanhã o TitãsBot pode trocar de modelo).
- **Efeito observado:** a G-Eval cai de 0,913 (BA global dentro da amostra) para 0,872 (CV global); o METEOR, de 0,900 para 0,862. **No artigo** (seção 5.3, comentário da Figura 5), a frase é "cai para 0,875 na validação cruzada", que é a versão estratificada. Se perguntarem, os dois números estão certos: 0,872 com limiar global, 0,875 com limiar por tipo.
- **[PONTO SENSÍVEL]** As mesmas perguntas aparecem na calibração e no teste (só o modelo muda). A validação testa generalização entre geradores, **não entre perguntas novas**.

### 8.6 Correlações e ranking de sistemas

- **Spearman e Kendall** entre o score e a cobertura (contínua): se a métrica acompanha a completude factual. Todas as boas ficaram entre 0,74 e 0,84.
- **Ranking de sistemas (Kendall τ):** a métrica ordena os 6 sistemas na mesma ordem da taxa real de acerto? METEOR τ = 0,93, o melhor; a maioria das outras 0,645; Answer Relevancy **−0,79** (inverte).

### 8.7 Teste de McNemar (McNemar, 1947)

- **Para quê:** comparar duas condições (sem e com RAG) **nas mesmas perguntas**, ou seja, dados binários **pareados**.
- **Ideia:** as perguntas que ficaram iguais (certa→certa, errada→errada) **não informam nada** sobre a diferença. Só os **pares discordantes** importam: ganhos (errada→certa) e perdas (certa→errada).
- **Versão exata (binomial):** sob a hipótese nula de que o RAG não muda nada, ganho e perda são igualmente prováveis (p = 0,5).
  - **Cálculo à mão, Claude:** 20 ganhos e 0 perdas → p = 2 × 0,5²⁰ = **1,91 × 10⁻⁶**.
  - **DeepSeek:** 18 ganhos e 1 perda → p = 2 × (1 + 19) / 2¹⁹ = **7,63 × 10⁻⁵**.
  - **GPT-5 mini:** 18 ganhos e 0 perdas → p = 2 × 0,5¹⁸ = **7,63 × 10⁻⁶**.
- **[DO CÓDIGO]** O teste não está nos scripts do repositório; foi calculado à parte. Os valores conferem exatamente com o cálculo acima.
- **Postura do artigo:** priorizar a **magnitude** (pontos percentuais e número de perguntas que mudaram) sobre o valor-p.

---

## 9. Resultados com todos os números

### 9.1 RQ1 — Efeito do RAG por modelo

| Modelo | Sem RAG | Com RAG | Dif. (p.p.) | Ganhos | Perdas | p (McNemar exato) |
|---|---|---|---|---|---|---|
| Claude Haiku 4.5 | 5,0% (2/40) | **55,0%** (22/40) | +50,0 | 20 | 0 | 1,91e−06 |
| DeepSeek Chat | 7,5% (3/40) | 50,0% (20/40) | +42,5 | 18 | 1 | 7,63e−05 |
| GPT-5 mini | 5,0% (2/40) | 50,0% (20/40) | +45,0 | 18 | 0 | 7,63e−06 |
| **Total** | **5,8%** (7/120) | **51,7%** (62/120) | +45,8 | 56 | 1 | ~8e−16 **[CÁLCULO COMPLEMENTAR]** |

- **Leitura:** a diferença entre as condições (≈ 45 p.p.) é muito maior que a diferença entre modelos (≈ 5 p.p.).
- **A única perda** é do DeepSeek na q01: sem RAG, a resposta genérica cobria 100% dos fatos; com RAG, trouxe detalhes do contexto (CNPq, nome Asimov) e omitiu "estudantes e orientadores" e "competições" (cobertura de 50%, abaixo dos 75%).
- **Razões relativas** ("10 vezes mais") **devem ser evitadas**: partem de uma base minúscula e exageram a impressão. O artigo usa ganhos absolutos.

**[CÁLCULO COMPLEMENTAR] Intervalos de confiança de 95% (Wilson):**
- Sem RAG: 5,8% [2,9% – 11,6%]. Com RAG: 51,7% [42,8% – 60,4%]. Os intervalos não se sobrepõem.
- Por modelo com RAG: Claude 55,0% [39,8% – 69,3%]; DeepSeek e GPT 50,0% [35,2% – 64,8%]. **Os intervalos se sobrepõem bastante.**
- **McNemar entre modelos, ambos com RAG:** Claude × DeepSeek p = 0,69; Claude × GPT p = 0,73; DeepSeek × GPT p = 1,00. **Não há diferença estatisticamente significativa entre os modelos.** O "Claude liderou com 55%" deve ser dito como **tendência**, não como superioridade.
- Das 40 perguntas com RAG: em 16 os três modelos acertam, em 13 os três erram e em 11 eles divergem.

### 9.2 Cobertura factual (slide 8, Figura 2)

| Modelo | Cobertura média sem RAG | Com RAG |
|---|---|---|
| Claude Haiku 4.5 | 0,058 | 0,629 |
| DeepSeek Chat | 0,099 | 0,629 |
| GPT-5 mini | 0,097 | 0,644 |

- **Leitura:** as respostas com RAG passaram a conter cerca de 63–64% dos fatos esperados, contra 6–10% sem RAG. Isso complementa o rótulo binário: houve **ganho de completude**.
- **Ressalva (está no slide):** a cobertura não impede que a resposta também tenha um fato falso.

### 9.3 RQ2 — Efeito da tipologia (slide 9, Figuras 3 e 4)

**Taxa de acerto por estrato (heatmap):**

| Sistema | Descritiva (5) | Fato curto (7) | Lista curta (17) | Lista longa (11) |
|---|---|---|---|---|
| Claude, sem RAG | 0,20 | 0,14 | 0,00 | 0,00 |
| Claude, com RAG | 0,60 | 0,57 | **0,76** | 0,18 |
| DeepSeek, sem RAG | 0,20 | 0,29 | 0,00 | 0,00 |
| DeepSeek, com RAG | 0,00 | 0,57 | **0,82** | 0,18 |
| GPT-5 mini, sem RAG | 0,20 | 0,14 | 0,00 | 0,00 |
| GPT-5 mini, com RAG | 0,20 | 0,57 | 0,59 | **0,45** |

**Agregado por estrato (as 6 condições juntas, que é o que a Figura 4 mostra):** fato curto **38,1%** (16/42); lista curta **36,3%** (37/102); descritiva **23,3%** (7/30); lista longa **13,6%** (9/66).

**Só com RAG [CÁLCULO COMPLEMENTAR]:** lista curta **72,5%** (37/51); fato curto **57,1%** (12/21); lista longa **27,3%** (9/33); descritiva **26,7%** (4/15). Sem RAG: fato curto 19,0%, descritiva 20,0% e as duas listas 0%.

**[PONTO SENSÍVEL]** A Figura 4 mistura as duas condições. Nela o fato curto lidera, porque teve acertos sem RAG (a pista do prompt). Com RAG, quem lidera é a lista curta, e é isso que o Resumo afirma. Se a banca perguntar se os 13,6% das listas longas são com RAG: não, são o agregado; com RAG, são 27,3%.

**Como interpretar (frases para a defesa):**
- **Listas curtas:** 0% sem RAG em todos os modelos; 59–82% com RAG. É **onde o RAG mais transforma**, porque são tabelas de resultados e orientadores que a recuperação acha bem.
- **Listas longas:** também partem de 0%, mas com RAG ficam entre 18% e 45%. **Todo o acerto desse estrato vem do RAG**, então o RAG ajuda, mas não basta para completar listas extensas. Os itens ficam espalhados por vários chunks, e os 8 chunks do contexto não cobrem 20, 17 ou 191 itens. O GPT-5 mini foi melhor aqui (45,5%).
- **Fato curto:** os três convergem em 57,1% com RAG (4 de 7).
- **Descritiva:** variável, mas cada célula tem só 5 perguntas, então **exige cautela**. O RAG quase não mudou o agregado (de 3 para 4 acertos em 15). O DeepSeek com RAG zerou (0 de 5); sem RAG, acertou a q01 por causa da pista no prompt. As descritivas pedem síntese de cerca de 4 fatos com corte de 75%, e faltar um fato reprova.
- **Não foi aplicado teste inferencial entre estratos.** As diferenças são **tendências** do conjunto.

**As 13 perguntas que os três modelos erraram mesmo com RAG** (bom saber se pedirem exemplos de falha):
- **Nenhum fato encontrado ou recusa:** q18 (classificações de 2025), q30 ("quantos estudantes": a resposta é 191, com 152 do sexo masculino e 39 do feminino), q37 (patrocinadores).
- **Listas incompletas:** q31 (subgrupos), q32 (campeonatos), q34 (projetos), q39 (191 estudantes: cobertura de só 9%), q21 e q27 (orientadores de 2017 e 2023, ~56% de cobertura).
- **Fatos ou descrições parciais:** q07 (primeira competição: acertam o ano ou a competição, não os dois), q33 (anos da RoboCup: falta 2025), q35 (tecnologias), q36 (como participar).

**[CÁLCULO COMPLEMENTAR]** **A informação existe na base** (o livro cita patrocinadores e 2025, e a tabela tem SuperTeam e 2025). Então essas falhas são de **recuperação ou geração**, não de ausência no corpus.

### 9.4 Recuperação como fator crítico (slide 10, Tabela 2 do artigo)

| Modelo | Hit@5 | Precision@5 | Acerto quando Hit = 1 | Acerto quando Hit = 0 |
|---|---|---|---|---|
| Claude Haiku 4.5 | 45,0% | 29,0% | **66,7%** | 9,1% |
| DeepSeek Chat | 50,0% | 34,0% | **70,0%** | 10,0% |
| GPT-5 mini | 50,0% | 35,0% | **60,0%** | 10,0% |

- **Leitura 1:** com a evidência no top-5, o acerto fica entre 60% e 70%; sem ela, cai para 9–10%. **A recuperação é condição necessária.**
- **Leitura 2:** mesmo **com** evidência, de 30% a 40% erram. **Não é suficiente**, porque há falhas na seleção, na combinação ou na geração.
- **Leitura 3:** Hit@5 de 45–50% e P@5 de 29–35% mostram **margem de melhoria no recuperador** (justifica os trabalhos futuros: reranking e chunking).
- **Cautela:** só cobre as 20 perguntas anotadas.

### 9.5 RQ3 — Comparação das métricas (slides 11 e 12, Tabela 3 do artigo)

Ordenação do artigo pela AUC. "BA" significa acurácia balanceada; "CV" é a validação cruzada leave-one-model-out.

| Métrica | Família | AUC | BA global (CV) | BA estratificada (CV) | Limiar global | Tempo/aval. (s) | Custo total (US$) |
|---|---|---|---|---|---|---|---|
| **G-Eval Correctness** | LLM | **0,968** | 0,872 | 0,875 | 0,40 | 23,7 | 0,43 |
| **METEOR** | lexical | **0,966** | 0,862 | **0,891** | 0,35 | 0,010 | 0 |
| chrF | lexical | 0,963 | 0,872 | 0,875 | 0,50 | 0,002 | 0 |
| ROUGE-L | lexical | 0,952 | 0,875 | 0,885 | 0,25 | ~0 | 0 |
| BLEU | lexical | 0,951 | 0,859 | 0,837 | 0,10 | 0,008 | 0 |
| Token F1 | lexical | 0,946 | 0,846 | 0,871 | 0,45 | ~0 | 0 |
| ROUGE-2 | lexical | 0,945 | **0,882** | 0,858 | 0,20 | ~0 | 0 |
| BERTScore F1 | semântica | 0,944 | 0,880 | 0,870 | 0,70 | 0,125 | 0 |
| ROUGE-1 | lexical | 0,943 | 0,833 | 0,889 | 0,45 | ~0 | 0 |
| ref_projeto | referência | 0,920 | 0,814 | 0,849 | 0,55 | 0,114 | 0 |
| Cosseno MiniLM | semântica | 0,903 | 0,824 | 0,863 | 0,65 | 0,114 | 0 |
| 1 − Hallucination | LLM | 0,658 | 0,663 | 0,663 | 0,50 | 19,9 | 0,36 |
| Exact Match | lexical | 0,594 | 0,594 | 0,594 | 0,50 | ~0 | 0 |
| Faithfulness* | LLM | 0,557 | 0,586 | 0,578 | 0,70 | 63,2 | 0,58 |
| Answer Relevancy | LLM | 0,520 | 0,496 | 0,502 | 0,95 | 30,4 | 0,52 |

\* Faithfulness com n = 117 (só respostas com RAG e com chunks). As demais têm n = 240.

**Pontos que você precisa dominar:**
1. **No topo há um empate técnico:** G-Eval 0,968 × METEOR 0,966 × chrF 0,963. **[CÁLCULO COMPLEMENTAR]** No bootstrap por pergunta (2.000 reamostragens), a diferença G-Eval − METEOR tem IC95% de **[−0,024; +0,034]**. O intervalo **contém o zero**, então a diferença não é significativa.
2. **AUC maior não significa melhor decisão:** na BA estratificada (CV), METEOR 0,891 > ROUGE-1 0,889 > ROUGE-L 0,885 > G-Eval 0,875.
3. **[PONTO SENSÍVEL]** Na BA **global** (CV), quem lidera é **ROUGE-2 (0,882)** e **BERTScore (0,880)**; o METEOR fica com 0,862. O slide diz que o METEOR tem a "melhor acurácia balanceada cruzada", o que é verdade **na versão estratificada**, que era o critério principal definido no método. Diferenças de 1 a 2 p.p. estão dentro do ruído com n = 240.
4. **H2 (limiar estratificado melhora?)** se confirma só em parte. Melhorou METEOR (0,862 → 0,891), ROUGE-1 (0,833 → 0,889), Token F1, cosseno, ref_projeto, ROUGE-L, chrF e G-Eval. Piorou ROUGE-2 (0,882 → 0,858), BERTScore (0,880 → 0,870) e BLEU (0,859 → 0,837).
5. **Por que as métricas lexicais vão tão bem aqui:** o corpus é cheio de **nomes, datas, modalidades e colocações**, e a presença ou ausência desses termos **é** a informação factual. **Isso é próprio deste domínio e não deve ser generalizado** para tarefas com mais liberdade de paráfrase.
6. **Faithfulness, Answer Relevancy e Hallucination ficaram perto do acaso, e isso não quer dizer que sejam inúteis.** Elas medem **outra coisa** (fidelidade ao contexto, pertinência e contradição), não correção em relação ao gabarito.
7. **Sensibilidade ao limiar** (Figura 5 do artigo): METEOR tem o melhor ponto perto de 0,35 (BA ~0,90 dentro da amostra); ROUGE-L, perto de 0,25; BERTScore, perto de 0,70; G-Eval, entre 0,35 e 0,40. Answer Relevancy fica em ~0,52 com qualquer limiar, então o problema dela não é o limiar.

### 9.6 Matrizes de confusão (slide 12)

As matrizes do slide são da **CV leave-one-model-out com limiar global**.

| Métrica | VN | FP | FN | VP | Especificidade | Sensibilidade | BA |
|---|---|---|---|---|---|---|---|
| METEOR | 161 | 10 | 15 | 54 | **94,2%** | 78,3% | 86,2% |
| G-Eval | 157 | 14 | 12 | 57 | 91,8% | **82,6%** | 87,2% |
| Answer Relevancy | 16 | **155** | 7 | 62 | 9,4% | 89,9% | 49,6% |

- **METEOR é mais conservador:** menos FP (10), mais FN (15). Penaliza paráfrases corretas.
- **G-Eval é mais sensível:** menos FN (12), mais FP (14).
- **Nenhuma é superior em absoluto.** A escolha depende do custo atribuído a cada tipo de erro.
- **Answer Relevancy aprova quase tudo:** 155 respostas erradas aprovadas. A sensibilidade alta (89,9%) **engana** quando vista sozinha.
- **[PONTO SENSÍVEL]** Se perguntarem por que o slide 11 diz que o METEOR tem BA de 0,891 e a matriz dá 86,2%: são versões diferentes. 0,891 é com **limiar estratificado**; a matriz do slide é com **limiar global**. A matriz estratificada do METEOR seria VN 156, FP 15, FN 9, VP 60.

### 9.7 Aspectos práticos de adoção das métricas (não é uma avaliação sociotécnica completa)

**[DO CÓDIGO]**, com dados de `analise_metricas.json`. Não estão todas no artigo, mas o orientador pediu essa discussão.
- **Custo e tempo:** as tradicionais levam ~0,03 s por resposta e custam US$ 0; as LLM levam ~34 s por resposta em média e custaram **US$ 1,88** no total. Em tempo, as LLM são mais de 1.000 vezes mais lentas.
- **Estabilidade (3 repetições em 36 respostas):** as tradicionais têm desvio de 0 (determinísticas). G-Eval 0,056 (amplitude máxima 0,4); Answer Relevancy 0,051 (máx. 1,0); Faithfulness 0,048 (máx. 0,86); **Hallucination 0,183 (máx. 1,0)**: a mesma resposta virou de 0 para 1.
- **Respostas sobre pessoas reais:** 78 respostas envolvem nomes, 50 delas incorretas. Taxa de aprovação indevida, com o limiar global dentro da amostra: **G-Eval 2% (1/50)**; METEOR, ROUGE e BERTScore ~10–12%; cosseno e ref_projeto 16%; Hallucination 48%; Faithfulness 82% (9/11); Answer Relevancy 86%.
  - **Nuance a favor da G-Eval:** em respostas sobre pessoas, ela foi a mais segura. É um bom contraponto para não parecer que "o lexical ganhou em tudo".
- **Viés do avaliador:** o `gpt-5-nano` é da mesma família do `gpt-5-mini` avaliado. **Os dados não mostram favorecimento:** a média da G-Eval com RAG foi Claude 0,500, GPT 0,510 e DeepSeek 0,532.
- **Privacidade:** nomes de estudantes foram enviados a APIs externas durante a avaliação com LLM. As métricas tradicionais rodam localmente.
- **Reprodutibilidade e transparência:** fórmula determinística × LLM opaco, versionado pelo fornecedor e que muda com o tempo.

---

## 10. Tabelas e figuras do artigo (e as que não estão nos slides)

| Item | O que mostra | Números | Slide |
|---|---|---|---|
| Tabela 1 | Acerto por modelo e condição, ganhos e perdas pareados, McNemar | 5,0→55,0 / 7,5→50,0 / 5,0→50,0; 20/0, 18/1, 18/0; p = 1,91e-06, 7,63e-05 e 7,63e-06 | 7 (a fala cobre o McNemar) |
| Figura 1 | Barras sem e com RAG por modelo | idem | 7 |
| Figura 2 | Cobertura média de fatos-chave | Claude 5,8→62,9; DeepSeek 9,9→62,9; GPT-5 mini 9,7→64,4 | 8 |
| Figura 3 | Heatmap sistema × tipologia | seção 9.3 | 9 |
| Figura 4 | Agregado por tipologia, **com e sem RAG juntos** | 23,3 / 38,1 / 36,3 / 13,6 | 9 |
| Tabela 2 | Hit@5, Precision@5, acerto com Hit = 1 e com Hit = 0 | 45/29/66,7/9,1 · 50/34/70/10 · 50/35/60/10 | 10 |
| Figura 5 | Acurácia balanceada × limiar, nos dados completos | METEOR ≈ 0,90 em 0,35; ROUGE-L em 0,25; BERTScore em 0,70; G-Eval ≈ 0,91 em 0,35–0,40 (cai para 0,875 na validação cruzada); Answer Relevancy ≈ 0,5 em qualquer limiar | **não está nos slides** |
| Tabela 3 | As 15 métricas: AUC, BA global (CV), BA estratificada (CV), limiar, segundos por avaliação e custo | seção 15 | **o slide 11 só mostra 3 métricas** |
| Figura 6 | AUC × tempo por avaliação (escala log) | lexicais entre 0,0001 e 0,01 s; LLM entre 20 e 63 s | **não está nos slides** |
| Figura 7 | Ranking por AUC, colorido por família | | 11 |
| Figura 8 | Curvas ROC de METEOR, ROUGE-L, BERTScore, G-Eval e chrF | todas longe da diagonal; G-Eval aparece com 0,967 | **não está nos slides** |
| Tabela 5 | Matrizes resumidas | METEOR 161/10/15/54 · G-Eval 157/14/12/57 · Relevancy 16/155/7/62 | 12 |
| Figura 9 | Matrizes normalizadas pela classe real | | 12 |
| Figura 10 | QR code do vídeo | youtu.be/ZZMSgk9U9S0 | — |

### Como explicar o que não está nos slides

- **Figura 5 (limiar):** "Cada curva mostra a acurácia balanceada de uma métrica conforme o ponto de corte muda. Ela mostra duas coisas: cada métrica tem seu limiar ideal (METEOR em 0,35, BERTScore em 0,70), e escolher mal o limiar derruba o desempenho. A Answer Relevancy fica perto de 0,5 em qualquer limiar, então o problema dela não é calibração; é que ela não separa certo de errado."
- **Tabela 3 (as colunas):** "AUC" é a capacidade de ordenar. "BA global (CV)" é a acurácia balanceada com um único limiar, validada deixando um modelo de fora. "BA estrat. (CV)" é o mesmo com um limiar por tipo de resposta. "Limiar" é o corte global escolhido com todos os dados. "s/aval." são os segundos por resposta avaliada. "Custo US$" é o custo total das 240 avaliações (as quatro de LLM somam US$ 1,88).
- **Figura 6 (custo):** "O eixo do tempo está em escala logarítmica. As lexicais ficam no alto e à esquerda: AUC alta, em milissegundos. As de LLM ficam à direita, com dezenas de segundos; só a G-Eval está no alto. As outras três de LLM ficam embaixo, perto do acaso."
- **Figura 8 (ROC):** "Para cada limiar possível, a curva marca a taxa de verdadeiros positivos contra a de falsos positivos. Quanto mais perto do canto superior esquerdo, melhor. A área sob a curva é a AUC, e a diagonal tracejada é o acaso. As cinco curvas quase se sobrepõem: famílias diferentes ordenam as respostas de forma parecida."

**Se alguém mencionar o artigo diagnóstico do TitãsBot**, que ficou fora do TCC, uma frase basta: "Foi um estudo anterior, com 20 perguntas e só o DeepSeek, que separou falhas de recuperação e de geração. A ideia entrou no TCC como a Tabela 2."

---

## 11. Exemplos reais para citar na defesa

Tirados de `back/avaliacao_metricas/analise_metricas.json`. Exemplos concretos convencem a banca mais que números soltos.

1. **Answer Relevancy aprova resposta inútil (q12, GPT-5 mini, sem RAG).** Pergunta: classificações de 2019. Resposta: o modelo **pergunta de volta** em qual competição o usuário está interessado, sugere FIRST/FLL (competições que a equipe não disputa) e indica onde procurar. Notas: **Answer Relevancy = 1,0**, G-Eval = 0,0, METEOR = 0,03. Mostra que relevância ≠ correção.
2. **Fiel, mas incompleta (q33, GPT-5 mini, com RAG).** Esperado: 2019, 2024 e 2025. Resposta: "2019 e 2024". Cobertura de 67% (fato curto exige 100%), então **incorreta**. Faithfulness = 1,0; G-Eval = 0,6 (aprovaria com o limiar 0,40, um FP); METEOR = 0,12 (rejeita). É o caso típico de fidelidade sem correção.
3. **G-Eval rejeita resposta correta por formato (q28, Claude, com RAG).** Os 8 orientadores de 2024 estavam todos corretos, mas em tabela e com uma linha duplicada (Eduardo Max em duas linhas). **G-Eval = 0,3** (falso negativo, "discrepância estrutural"); METEOR = 0,94. O LLM-avaliador também tem idiossincrasias.
4. **Resposta curta e correta penalizada por todas as métricas de referência (q05, DeepSeek, com RAG).** "Renato Lopes de Oliveira idealizou a criação da equipe." Está correta (o fato-chave é o nome), mas G-Eval = 0,2 e METEOR = 0,20, porque o gabarito é mais longo (cita o curso e o campus). É uma armadilha de métricas baseadas em referência.
5. **Caso de fronteira na verdade (q08, GPT e Claude, com RAG).** Esperado: "SEK: 1º lugar — TRUFES; SEK: 3º lugar — LARC". Resposta: "1º lugar — TRUFES; 3º lugar — LARC", **sem dizer a modalidade (SEK)**. A verdade marca incorreta (a modalidade é exigida no fato `placement`); METEOR 0,81 e G-Eval 0,8 aprovam. É defensável dos dois lados: falta informação (qual modalidade?), mas a essência está lá.
6. **Pergunta de abstenção (q40).** O gabarito diz que a base não contém a informação. O DeepSeek sem RAG disse "não sei" e foi rotulado **correto**. O Claude sem RAG também disse que não tinha a informação, mas o casamento de padrão não reconheceu a frase e o rotulou **incorreto**, enquanto a G-Eval deu 0,9. **[PONTO SENSÍVEL]** É um exemplo honesto de que a verdade automática tem erros residuais (ver seção 12).
7. **O RAG declarando insuficiência (q18 e q37).** Com RAG, vários modelos responderam "Não encontrei informação suficiente na base…". Pelo desenho do sistema, isso é preferível a inventar, mas conta como incorreto contra o gabarito. Falha de recuperação: a informação existe no corpus.

---

## 12. Leitura crítica: limitações e pontos sensíveis

Saber isso é o que diferencia uma defesa boa de uma ótima. A banca **vai** procurar fragilidades, e reconhecer cada uma com serenidade mostra maturidade científica. As respostas prontas estão em `ROTEIRO_DEFESA.md`, seção 5.

**Limitações declaradas no artigo (e onde estão):**
1. A cobertura de fatos mede presença e não penaliza um fato extra inventado (4.1).
2. As descritivas têm só 5 perguntas por célula (5.2).
3. Não houve teste inferencial entre estratos (5.2).
4. A análise de Hit@5 cobre só o subconjunto anotado (5.2).
5. O bom desempenho das lexicais é próprio deste corpus e não se generaliza para tarefas com mais paráfrase (5.3).
6. Os resultados ficam condicionados ao recorte experimental e ao domínio (6, a única limitação citada nas Conclusões).

O artigo não fala explicitamente do tamanho da amostra (40 perguntas). Vale você dizer isso por iniciativa própria, como na fala do slide 13.

**Pontos que o artigo não discute, mas o código revela [PONTO SENSÍVEL]:**
1. **O prompt sem RAG cita "Asimov" e "Ifes Campus Colatina"**, o que gerou os acertos das q01 e q02 sem RAG. O efeito do RAG fica subestimado (conservador).
2. **A verdade é automática:** casamento de padrões sobre fatos curados por humanos. **Nenhum rótulo foi revisado manualmente na rodada final** (`rotulos_revisados_por_humano: 0`). Há erros residuais conhecidos (q40 do Claude e do GPT sem RAG).
3. **A verdade tem natureza lexical** (presença de termos), e isso pode **favorecer as métricas lexicais**. Mitigação: a G-Eval (semântica, por LLM) chega à mesma AUC, o que sugere que a separação reflete conteúdo e não só forma.
4. **A recuperação não é idêntica entre os modelos:** a expansão de consulta e a seleção de evidências usam o LLM gerador.
5. **Atalhos determinísticos** (q02 Asimov, q39 lista de estudantes e q40 patrocínio) tornam algumas respostas independentes do modelo. Na q40, a resposta com RAG vem de uma regra que nem faz busca.
6. **A G-Eval com `gpt-5-nano`** dá notas inteiras de 0 a 10, sem ponderação por probabilidade, e não é determinística.
7. **O LLM de apoio é da família GPT**, a mesma de um dos avaliados. Não houve favorecimento observado.
8. **A validação leave-one-model-out** testa troca de gerador, não perguntas novas. São só 3 dobras.
9. **Faithfulness com n = 117** não é diretamente comparável às outras (n = 240).
10. **Hallucination com contexto único** vira binária e mede contradição, não omissão.
11. **METEOR com WordNet em inglês:** em português, os sinônimos e os radicais não funcionam.
12. **Os pesos da busca híbrida** (0,50/0,30/0,15/0,05) foram ajustados empiricamente, sem ablação formal.
13. **A temperatura 0 não vale para todos os modelos** (a família GPT-5 ignora), então a geração não é 100% determinística.
14. **A demo publicada usa `gpt-5-nano`**, que não é um dos três modelos avaliados.
15. **O pipeline foi ajustado com o gabarito à vista.** A regra da q40 contém a frase da própria pergunta, e outras regras (Asimov, lista de estudantes, prompts de participação e de projetos) atendem perguntas do gabarito. Então os 51,7% são uma estimativa **otimista** para perguntas novas. O efeito do RAG resiste: sem q01, q02 e q40, vai de **0% (0/111) para 48,6% (54/111)**. A meta-avaliação das métricas não é afetada, porque compara métricas e rótulos sobre as mesmas respostas, seja qual for a origem delas. Resposta pronta: Roteiro, A14.
16. **A Figura 4 mistura com e sem RAG** (seção 9.3). Quem lê rápido pode achar que os 13,6% das listas longas são com RAG.
17. **Detalhes de forma no artigo:** a Tabela 4 citada não existe, a AUC da G-Eval aparece como 0,968 e 0,967, e há o cabeçalho "MNR 2019" (seção 2.4).
18. **A q07 tem divergência entre o gabarito e o livro.** O gabarito diz que a primeira competição foi a LARC; o livro (seção "A primeira competição", p. 61) diz II TRUFES, junho de 2015. O Claude com RAG seguiu o livro e foi marcado incorreto. Afeta 1 resposta de 240. Resposta pronta: Roteiro, A15.

**Trabalhos futuros coerentes (e já citados nos slides e artigos):**
- Melhorar o recuperador: **reranking** (por exemplo, um cross-encoder), **chunking** orientado à estrutura (uma linha de tabela por chunk), recuperação iterativa, *k* adaptativo por tipo de pergunta (listas longas pedem mais chunks).
- Extração estruturada para listas longas, por exemplo consultando a tabela como dado estruturado em vez de texto.
- Ampliar o gabarito e fazer **rotulagem humana dupla** com medida de concordância (kappa de Cohen).
- Comparar mais modelos e avaliadores (G-Eval com outro LLM de apoio, passos de avaliação fixos e rubrica).
- Ablação dos componentes do pipeline (sem expansão, sem auditoria, só vetorial × híbrido).

---

## 13. Glossário rápido

| Termo | Definição curta |
|---|---|
| **LLM** | Modelo de linguagem de grande escala, baseado em Transformer, que gera texto token a token |
| **Token** | Unidade de texto do modelo (pedaço de palavra) |
| **Conhecimento paramétrico** | O que o modelo "sabe", guardado nos pesos |
| **Memória não paramétrica** | Documentos externos, consultados na inferência (o RAG) |
| **Alucinação** | Texto fluente sem suporte factual |
| **RAG** | Recuperar trechos relevantes e gerar a resposta condicionada a eles |
| **Embedding** | Vetor que representa o significado de um texto |
| **Similaridade por cosseno** | Ângulo entre vetores; 1 = mesma direção |
| **BM25** | Ranking lexical por frequência do termo, raridade e tamanho do documento |
| **Busca híbrida** | Combinação de vetorial e lexical |
| **Chunk / chunking** | Pedaço de documento e o processo de dividir |
| **Chroma** | Banco de dados vetorial usado no TitãsBot |
| **Top-k** | Os k trechos mais bem pontuados |
| **Hit@5** | Ao menos um chunk suficiente entre os 5 primeiros |
| **Precision@5** | Fração de chunks relevantes entre os 5 primeiros |
| **Fato-chave** | Unidade mínima de informação do gabarito (nome, data, colocação) |
| **Cobertura** | Fatos encontrados ÷ total de fatos |
| **Rótulo binário** | Correta (1) ou incorreta (0), conforme a cobertura mínima |
| **Estrato** | Tipo de resposta: fato curto, descritiva, lista curta, lista longa |
| **Limiar (threshold)** | Ponto de corte: score ≥ limiar ⇒ "correta" |
| **VP/FP/FN/VN** | Verdadeiro/falso positivo/negativo (positivo = correta) |
| **Sensibilidade** | VP/(VP+FN): quanto das corretas é aprovado |
| **Especificidade** | VN/(VN+FP): quanto das incorretas é barrado |
| **Acurácia balanceada** | Média de sensibilidade e especificidade; robusta a desbalanceamento |
| **AUC-ROC** | Probabilidade de a métrica dar nota maior a uma correta do que a uma incorreta |
| **Leave-one-model-out** | Calibrar com 2 modelos e testar no 3º |
| **McNemar** | Teste para dados binários pareados; usa só os pares que mudaram |
| **Spearman / Kendall** | Correlação de postos (ordem), não de valores |
| **G-Eval** | Avaliação por LLM com critérios e passos gerados por cadeia de raciocínio |
| **DeepEval** | Biblioteca Python de métricas de avaliação de LLM |
| **LLM-as-a-judge** | Usar um LLM para avaliar saídas de outro LLM |

---

## 14. Referências e o que cada uma sustenta

**Regra para a arguição:** só diga "citamos" para as referências de 14.1, que são as 18 do artigo. As de 14.2 são leitura de apoio; ao usá-las, diga "a literatura mostra" ou "um trabalho conhecido é…".

### 14.1 As 18 referências do artigo do TCC

| Referência | Para que você cita |
|---|---|
| Vaswani et al. (2017), *Attention Is All You Need* | Transformer e self-attention, a base dos LLMs |
| Brown et al. (2020), *Language Models are Few-Shot Learners* | Escala e aprendizado no contexto (GPT-3) |
| Ji et al. (2023), *Survey of Hallucination in NLG* | Definição e tipos de alucinação |
| Lewis et al. (2020), *Retrieval-Augmented Generation…* | Proposta original do RAG: memória paramétrica + não paramétrica |
| Gao et al. (2023/2024), *RAG for LLMs: A Survey* | Taxonomia (naive/advanced/modular) e desafios do RAG |
| Reimers & Gurevych (2019), *Sentence-BERT* | Embeddings de frase para busca semântica |
| Wang et al. (2020), *MiniLM* | Modelo compacto usado na métrica de cosseno |
| Karpukhin et al. (2020), *DPR* | Recuperação densa em QA |
| Robertson & Zaragoza (2009), *BM25 and Beyond* | Recuperação lexical probabilística |
| Papineni et al. (2002), BLEU · Lin (2004), ROUGE · Banerjee & Lavie (2005), METEOR · Popović (2015), chrF | Métricas lexicais |
| Zhang et al. (2020), BERTScore | Métrica semântica por token |
| Liu, Y. et al. (2023), G-Eval | Avaliação por LLM com cadeia de raciocínio |
| Fawcett (2006), *An introduction to ROC analysis* | AUC/ROC |
| Brodersen et al. (2010), *The balanced accuracy…* | Acurácia balanceada |
| McNemar (1947) | Teste para proporções pareadas |

### 14.2 Leituras de apoio (não estão no artigo)

| Referência | Para que você cita |
|---|---|
| Liu, N. et al. (2024), *Lost in the Middle* | Mais contexto não é mais uso efetivo |
| Asai et al. (2023), *Self-RAG* | Recuperação com autocrítica (relaciona com a auditoria) |
| Es et al. (2023), *RAGAS* | Avaliação de RAG por fidelidade e relevância |
| Mikolov et al. (2013) | Origem das representações vetoriais de palavras (word2vec) |
| Johnson, Douze & Jégou (2021), *Billion-scale similarity search* (FAISS) | Busca vetorial eficiente |
| Walsh & Ungson (1991), *Organizational Memory* | Memória organizacional = armazenar + recuperar |
| Nonaka & Takeuchi (1995) | Conhecimento tácito × explícito |
| Russell & Norvig (2022) | Definição de IA |
| Pego, Massarioli & Rios (2025) | *10 anos de Titãs da Robótica* (MNR 2025), a história da equipe |
| Voorhees (2003), TREC QA Track · Lin & Demner-Fushman (2006) | Avaliação por *nuggets* (fatos atômicos), a mesma lógica da cobertura de fatos-chave |
| Pradeep et al. (2024), TREC 2024 RAG Track (AutoNuggetizer) | Avaliação de RAG por *nuggets* |
| Min et al. (2023), *FActScore* | Fatos atômicos, mas medindo precisão (o que é sustentado) |

---

## 15. Cola de números (revisar no dia)

```
DESENHO
  40 perguntas = 5 descritivas + 7 fato curto + 17 lista curta + 11 lista longa
  3 modelos × 2 condições = 6 sistemas → 240 respostas
  Corte de cobertura: fato curto 100% · descritiva 75% · listas 80%
  69 corretas (28,75%) · 171 incorretas (71,25%) → desbalanceado → AUC + BA
  Corpus: 3 PDFs · 289 páginas · 1.026 chunks · 900 car. / sobreposição 180
  Busca: vetorial k=12 + BM25 top 36 → até 8 chunks no contexto
  Nota: 0,50 vet + 0,30 BM25 + 0,15 cobertura + 0,05 número + bônus
  DeepEval com gpt-5-nano

RQ1 — RAG
  Total:    5,8% → 51,7%   (7/120 → 62/120)
  Claude:   5,0% → 55,0%   +50,0 p.p.   20 ganhos / 0 perdas   p = 1,9e-6
  DeepSeek: 7,5% → 50,0%   +42,5 p.p.   18 / 1                 p = 7,6e-5
  GPT-5m:   5,0% → 50,0%   +45,0 p.p.   18 / 0                 p = 7,6e-6
  Cobertura: 0,058–0,099 → 0,629–0,644
  Entre modelos com RAG: sem diferença significativa (p ≥ 0,69)
  Sem q01, q02 (prompt) e q40 (regra): 0% → 48,6%   (0/111 → 54/111)

RQ2 — TIPOLOGIA (agregado)
  Fato curto 38,1% · Lista curta 36,3% · Descritiva 23,3% · Lista longa 13,6%
  Lista curta com RAG: 76,5 / 82,4 / 58,8   (C / D / G)
  Lista longa com RAG: 18,2 / 18,2 / 45,5
  Fato curto com RAG: 57,1 nos três

RECUPERAÇÃO (20 perguntas anotadas)
  Hit@5 45–50% · P@5 29–35%
  Acerto com Hit=1: 60–70% · com Hit=0: 9–10%

RQ3 — MÉTRICAS
  AUC: G-Eval 0,968 · METEOR 0,966 · chrF 0,963 · ROUGE-L 0,952 · BERTScore 0,944
       Cosseno 0,903 · Halluc 0,658 · EM 0,594 · Faith 0,557 · Relevancy 0,520
  BA estratificada CV: METEOR 0,891 (maior) · ROUGE-1 0,889 · ROUGE-L 0,885 · G-Eval 0,875
  G-Eval − METEOR (AUC): IC95 [−0,024; +0,034] → empate
  Matrizes (CV, limiar global):
    METEOR   VN161 FP10  FN15 VP54  → esp 94,2% · sens 78,3%
    G-Eval   VN157 FP14  FN12 VP57  → esp 91,8% · sens 82,6%
    Relev.   VN16  FP155 FN7  VP62  → esp  9,4% · sens 89,9%
  Custo LLM: ~34 s/resposta, US$ 1,88 total · tradicionais: ~0,03 s, US$ 0
  Pessoas (50 incorretas): aprovação indevida G-Eval 2% · METEOR 12% · Relev. 86%

TIPOLOGIA SÓ COM RAG
  Lista curta 72,5% · Fato curto 57,1% · Lista longa 27,3% · Descritiva 26,7%
  (a Figura 4 e o "agregado" acima somam com e sem RAG)

TABELA 3 (resto)            AUC    BA glob  BA estr  limiar  s/aval   US$
  BLEU                      0,951  0,859    0,837    0,10    0,008    0
  ROUGE-2                   0,945  0,882    0,858    0,20    0        0
  BERTScore                 0,944  0,880    0,870    0,70    0,125    0
  Token F1                  0,946  0,846    0,871    0,45    0        0
  ref_projeto               0,920  0,814    0,849    0,55    0,114    0
  G-Eval                    0,968  0,872    0,875    0,40    23,7     0,43
  Hallucination (inv.)      0,658  0,663    0,663    0,50    19,9     0,36
  Faithfulness (n=117)      0,557  0,586    0,578    0,70    63,2     0,58
  Answer Relevancy          0,520  0,496    0,502    0,95    30,4     0,52

DETALHES DE FORMA DO ARTIGO
  "Tabela 4" citada não existe (é a Tabela 3) · G-Eval 0,968 no texto, 0,967 na Fig. 8 (exato 0,96745)
  Cabeçalho "MNR 2019" em algumas páginas · Vídeo: youtu.be/ZZMSgk9U9S0
```

---

## 16. A parte do Victor Pego (para você saber, não para apresentar)

> O roteiro de defesa tem só a sua parte. Esta seção reúne o que o Pego apresenta e responde, para você entender o todo e não ser pego de surpresa se a banca dirigir a você uma pergunta sobre isso.

### 16.1 Estrutura completa da apresentação (20 minutos)

| # | Slide | Quem | Tempo | Acumulado |
|---|---|---|---|---|
| 1 | Capa | Pego | 0:30 | 0:30 |
| 2 | LLMs e domínios especializados | Pego | 1:15 | 1:45 |
| 3 | O domínio do Titãs da Robótica | Pego | 1:15 | 3:00 |
| 4 | As três questões centrais (+ objetivo, falado) | Pego | 1:00 | 4:00 |
| 5 | RAG no TitãsBot | Pego | 1:40 | 5:40 |
| — | *Passagem de vez* | | 0:10 | 5:50 |
| 6 a 13 | Testes e resultados | **Victor Cordeiro** | 10:10 | 16:00 |
| — | *Passagem de vez* | | 0:10 | 16:10 |
| 14 | Conclusão e trabalhos futuros | Pego | 0:50 | 17:00 |
| — | Demonstração ao vivo | Pego narra, Victor Cordeiro no teclado | 2:30 | 19:30 |
| 14 | Frase de fechamento e agradecimento | Pego | 0:15 | 19:45 |
| — | Folga | | 0:15 | 20:00 |

### 16.2 Slides 1 a 5: o que ele diz

- **Slide 2:** LLMs têm fluência, mas o conhecimento é limitado ao treino (paramétrico, desatualizado) e eles alucinam. Os dados dos Titãs estão fragmentados e ausentes dos corpora gerais.
- **Slide 3:** acervo de mais de 10 anos, alta rotatividade (perda de conhecimento tácito, Nonaka & Takeuchi) e silos informacionais (retrabalho).
- **Slide 4:** a pergunta geral e as questões I (efeito do RAG), II (efeito da tipologia) e III (as métricas distinguem certo de errado?). Como o slide não mostra os objetivos, o Pego diz em uma frase: *"O objetivo geral foi avaliar o efeito do RAG nas respostas de três LLMs sobre a história dos Titãs e verificar se métricas automáticas conseguem distinguir respostas corretas de incorretas."*
- **Slide 5:** ingestão (3 PDFs → 1.026 chunks → embeddings → Chroma) → busca híbrida (semântica + BM25) → contexto (trechos numerados no prompt) → geração. A frase-chave do slide: "Fornece evidências, mas não elimina alucinações". Detalhes no Guia, seção 5.

**Passagem de vez (fala do Pego, sugestão):**
> "…então o RAG fornece evidência, mas não garante a resposta correta. A pergunta é: quanto ele ajuda de fato, e como medir isso? Para mostrar como testamos, passo para o Victor Cordeiro."

### 16.3 Slide 14: conclusões

**Fala do Pego (sugestão):**
> "Concluindo. O RAG foi decisivo: levou o acerto de 5,8% para 51,7% e a cobertura factual de menos de 10% para cerca de 63%. Mas ele não resolve tudo: listas longas e falhas de recuperação ainda limitam o sistema. As métricas não são absolutas. Famílias muito diferentes separam bem respostas certas de erradas, mas a qualidade da decisão depende do limiar e do tipo de erro que se aceita, e relevância não é correção. Como próximos passos, queremos melhorar o motor de busca com reranking e um chunking que respeite a estrutura das tabelas, melhorar a extração de listas longas e ampliar o gabarito com rotulagem humana independente. [aponte para o QR] E agora vamos mostrar o TitãsBot funcionando."

**Frase de fechamento (o Pego diz depois da demo, de volta ao slide 14, seguida de "Obrigado, ficamos à disposição da banca"):**
> "O TitãsBot mostra que é possível tornar consultável a memória de uma equipe com mais de dez anos de história, desde que se meça com cuidado onde ele acerta e onde ainda erra."

### 16.4 Narração da demo

**Fala do Pego (sugestão):**
> "Este é o TitãsBot publicado no Google Cloud Run. Por custo, a versão pública usa o gpt-5-nano, que não é um dos três modelos do experimento, mas o pipeline é o mesmo.
>
> [você digita a pergunta 1] Vamos perguntar quem foram os orientadores da equipe em 2024. [enquanto carrega] Enquanto ele responde, o que acontece por trás: o sistema gera variações da pergunta, faz a busca híbrida nos 1.026 trechos, o modelo escolhe as evidências, gera a resposta, e uma auditoria confere a resposta contra os trechos antes de mostrar. São de quatro a sete chamadas ao modelo, por isso leva alguns segundos.
>
> [resposta aparece] São os oito orientadores do gabarito. E aqui embaixo estão as fontes, com arquivo e página: dá para conferir cada informação.
>
> [você digita a pergunta 2] Agora uma pergunta cuja resposta não está no acervo: o custo da viagem para a RoboCup de 2024. [resposta] Ele diz que não encontrou informação suficiente, em vez de inventar um valor. Num sistema de memória institucional, saber dizer que não sabe é o comportamento certo."

[volta ao slide 14] Frase de fechamento e "Obrigado, ficamos à disposição da banca."

**Durante a espera:** a pergunta 1 leva cerca de 45 segundos, e a narração acima preenche uns 25. Se demorar mais, o Pego pode mostrar o que está na tela (o campo de pergunta, onde as fontes vão aparecer). Não preencha com piadas sobre a demora.

**Durante a espera:** a pergunta 1 leva cerca de 45 segundos, e a narração acima preenche uns 25. Se demorar mais, ele pode mostrar o que está na tela (o campo de pergunta, onde as fontes vão aparecer).

### 16.5 Perguntas de sistema que são dele

As perguntas D5 (listas longas) e D6 (regras fixas) ficaram no seu roteiro, porque mexem com os resultados. As demais estão aqui.

**D1 ★ Explique o pipeline do TitãsBot.**
> Na **preparação**, 3 PDFs (o livro de 10 anos da equipe, um artigo e um documento de tabelas) viram 1.026 trechos de cerca de 900 caracteres, transformados em vetores e guardados no Chroma. Na **pergunta**, o sistema monta a consulta, gera variações dela com o LLM, faz a busca híbrida (vetorial mais BM25), filtra trechos de outras equipes, o LLM escolhe os trechos mais úteis, o modelo gera a resposta com um prompt específico para o tipo de pergunta, uma auditoria confere a resposta contra os trechos e o sistema acrescenta as fontes.

**D2 ★ Por que busca híbrida? E por que esses pesos?**
> A busca vetorial entende paráfrase, mas é fraca para nomes próprios, siglas, anos e colocações, que são justamente o que mais aparece no acervo. O BM25 garante a correspondência exata. A nota final combina 50% vetorial, 30% BM25, 15% cobertura de termos e 5% acerto de números, mais bônus por tipo de pergunta (por exemplo, priorizar tabelas em listas). Os pesos foram ajustados empiricamente durante o desenvolvimento; uma ablação formal é trabalho futuro.

**D3 Por que trechos de 900 caracteres com 180 de sobreposição?**
> É um equilíbrio: trechos grandes trazem ruído, e trechos pequenos quebram o fato (o nome num, a colocação no outro). A sobreposição de 20% evita perder uma frase cortada na fronteira. Para tabelas, um chunking que respeite as linhas da tabela é uma melhoria clara.

**D4 Qual embedding e qual banco vetorial? Por que o Chroma?**
> `text-embedding-3-small`, da OpenAI, e o ChromaDB. O Chroma é leve, roda embutido na aplicação, persiste em disco e integra com o LangChain, o que basta para um acervo de cerca de mil trechos. Para bilhões de vetores, faria sentido algo como o FAISS (Johnson et al.).

**D7 A auditoria não é outro LLM avaliando? Não mistura com a avaliação?**
> A auditoria é parte do **sistema**, não da avaliação. O próprio gerador revisa a resposta contra os trechos antes de entregá-la e pode corrigir ou declarar insuficiência, numa ideia parecida com o Self-RAG. A **avaliação** é externa e compara com o gabarito.

**D8 Quanto custa e quanto demora uma pergunta?**
> Uma pergunta com RAG dispara de 4 a 7 chamadas ao LLM (expansão, seleção, geração, auditoria, escopo, organização de listas). No experimento, a mediana com RAG foi de cerca de 9 s no Claude, 6 s no DeepSeek e 38 s no GPT-5 mini, que é um modelo de raciocínio. Sem RAG, de 1 a 7 s. A demo publicada usa o `gpt-5-nano`, pelo custo.

**D9 Como o sistema evita inventar quando não há informação?**
> Todos os prompts mandam usar só o contexto e, na falta de dados, responder exatamente "Não encontrei informação suficiente na base para responder com segurança". A auditoria pode trocar uma resposta sem suporte por essa mensagem, e há filtros de escopo da equipe. Num sistema orientado a conhecimento, reconhecer a falta de evidência é o comportamento correto.

**D10 E a privacidade dos dados dos estudantes?**
> O acervo já é institucional e foi publicado (livro, artigo). Ainda assim, as perguntas e os trechos passam por APIs de terceiros. Na avaliação, as métricas com LLM também enviam nomes ao provedor, enquanto as tradicionais rodam localmente. Isso entrou na discussão dos aspectos práticos de adoção das métricas. Para dados sensíveis, um modelo local seria o caminho.

**D11 ★ Por que RAG e não fine-tuning (treinar o modelo com os dados da equipe)?**
> O fine-tuning é caro, precisa ser refeito a cada atualização, não dá rastreabilidade da fonte e o modelo continua podendo alucinar. Com RAG, basta reindexar para atualizar, cada resposta cita arquivo e página, e trocar de modelo não exige retreinar nada. É a vantagem apontada por Lewis et al. (2020).

**D12 ★ Por que a demonstração demora tanto para responder?**
> A versão publicada usa o `gpt-5-nano`, que é um modelo de raciocínio, e cada pergunta faz de quatro a sete chamadas ao modelo: expansão da consulta, seleção de evidências, geração e auditoria. No teste de 08/11, as respostas levaram de 10 a 50 segundos. Dá para reduzir: tirar etapas que uma ablação mostrar dispensáveis, usar um modelo sem raciocínio ou mostrar a resposta enquanto é gerada (*streaming*). No experimento, o Claude Haiku levou cerca de 9 s e o DeepSeek cerca de 6 s.

**D13 A demo usa um modelo que vocês não avaliaram?**
> Sim. A versão pública usa o `gpt-5-nano` por custo. As conclusões do estudo valem para os três modelos avaliados. Como o gerador é só uma configuração (`llm_factory.py`), trocar o modelo da demo por um dos avaliados não exige mudar o pipeline.
