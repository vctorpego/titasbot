# Metodologia de avaliação — TitãsBot

Referência completa do processo de avaliação comparativa de modelos de linguagem:
o que é medido, como é calculado, por que foi escolhido assim e onde estão os
limites do que os resultados sustentam.

> Versão navegável (mesma informação, com diagramas e índice):
> https://claude.ai/code/artifact/c5b37fcf-d9b5-410b-8a99-fc5766f13536

---

## 1. Visão geral do pipeline

Cada pergunta percorre o mesmo caminho para os três modelos comparados. O ponto
essencial: existem **duas avaliações independentes** rodando em paralelo sobre a
mesma resposta, e as duas comparam sempre com o gabarito das perguntas de teste
(documento oficial do orientador) — nenhuma delas depende de um LLM para gerar um
rótulo de verdade à parte.

```
Perguntas com gabarito (documento oficial do orientador)
        │
        ▼
Cada modelo (GPT-5 · Claude Sonnet 5 · DeepSeek V4 Pro)
responde em 2 condições: com RAG e sem RAG
        │
        ├──► A) DeepEval — 4 métricas, avaliadas por um LLM, contra o gabarito
        └──► B) Score de referência — semântica + léxica, contra o gabarito
                    │
                    ▼
Agregação: taxa de aprovação DeepEval (indicador principal de qualidade) ·
nota média e taxa de aprovação por threshold do score de referência
```

---

## 2. A base de conhecimento e o RAG

RAG (*Retrieval-Augmented Generation*) = buscar trechos relevantes numa base antes
de responder e entregá-los ao modelo junto com a pergunta. É o que permite ao
chatbot responder sobre a equipe sem ter sido treinado nela.

### Da fonte aos blocos

A base são PDFs em `back/base/` (livro de 10 anos da equipe, um artigo, um
documento de tabelas). Cada página vira texto e é quebrada em blocos de **900
caracteres com 180 de sobreposição** — a sobreposição garante que uma frase
cortada na fronteira continue recuperável pelo bloco seguinte.

Cada bloco é convertido em vetor por `text-embedding-3-small` (OpenAI) e
armazenado no ChromaDB. PDFs cujo nome indica tabelas recebem `doc_kind="table"`,
usado depois para priorizar tabelas em perguntas sobre competições.

### Recuperação híbrida

Dois mecanismos complementares: **vetorial** (encontra significado próximo, mesmo
com palavras diferentes) e **BM25** (encontra termos exatos — crucial para nomes,
siglas e anos, onde a busca vetorial é fraca). Combinados em:

```
nota = 0,50 × vetorial + 0,30 × BM25 + 0,15 × cobertura + 0,05 × números
       + ajustes de intenção
```

### Por que testar sem RAG

A condição **sem RAG** faz a mesma pergunta ao mesmo modelo, sem contexto. É a
*linha de base*: mede quanto o modelo sabe por conta própria. Como a equipe é um
assunto local e específico, espera-se desempenho muito baixo — e a diferença entre
as duas condições é exatamente a contribuição do RAG.

**Validade da comparação:** a base, os embeddings e a recuperação são idênticos
para os três modelos. Só o modelo que redige muda. Sem isso não seria possível
atribuir a diferença ao modelo.

---

## 3. As 4 métricas do DeepEval

Cada métrica usa um modelo avaliador para julgar a resposta sob um critério,
produzindo nota em `[0,1]` e veredito contra um limiar fixo.

| Métrica | Limiar | Compara com | Pergunta que responde |
|---|---|---|---|
| Correção | 0,55 | gabarito | Os fatos do gabarito estão presentes, sem invenção? |
| Relevância | 0,60 | a pergunta | Cada afirmação trata do que foi perguntado? |
| Fidelidade | 0,70 | trecho recuperado | Inventou algo fora do contexto? *(só com RAG)* |
| Alucinação | 0,50 | gabarito | A resposta contradiz o fato correto? |

### Fidelidade vs. Alucinação — não são redundantes

Recebem entradas diferentes. Fidelidade usa `retrieval_context` (os trechos que o
RAG entregou) e por isso só roda com RAG. Alucinação usa `context`, preenchido
aqui com o próprio gabarito, e roda nas duas condições.

- **Fidelidade**: "inventou além do que leu?"
- **Alucinação**: "contradisse a verdade?"

Uma resposta pode ser fiel ao trecho recuperado e ainda assim errada, se o trecho
recuperado for o errado.

### ⚠ A Alucinação tem veredito invertido

Nas outras três, `nota ≥ limiar` = aprovado. Na Alucinação é o contrário:
`nota ≤ limiar` = aprovado — a nota mede *quanta* alucinação existe, então quanto
menor, melhor. Ler com a convenção das outras inverte a conclusão.

### O efeito do "E lógico"

"Aprovado" exige que **todas** as métricas aplicáveis passem juntas. Como são
critérios independentes, as taxas se multiplicam: quatro métricas individualmente
razoáveis (70%, 60%, 55%, 47%) produzem taxa combinada perto de **11%**. Taxa de
aprovação baixa não significa que os modelos erram quase tudo — é consequência
aritmética de exigir unanimidade entre quatro juízes imperfeitos.

---

## 4. O score de referência

Metodologia herdada do projeto de referência indicado pelo orientador.

### Os dois critérios

**Similaridade semântica** — mede se a resposta *quer dizer* o mesmo que o
gabarito. Cada texto vira um vetor pelo modelo multilíngue
`paraphrase-multilingual-MiniLM-L12-v2`; a nota é o cosseno entre eles. Reconhece
paráfrase.

**Similaridade léxica** — mede se a resposta *usa as mesmas palavras*. Calculada
por **ROUGE-L** (F-measure): a maior subsequência comum de palavras entre gabarito
e resposta, medida padrão na literatura de NLP para sobreposição lexical. Existe
porque em algumas perguntas os termos exatos são essenciais (nomes, siglas,
colocações). Diferenças de pontuação/tipografia (parênteses, travessão vs. hífen)
não penalizam, porque não viram token.

```
score_final = 0,8 × semântica + 0,2 × léxica
```

### Exemplo com números reais

GPT-4o-mini, "classificações da temporada de 2017", com RAG — reproduziu os 10
itens do gabarito, mudando pontuação (removeu os parênteses de "(Regional)" /
"(Internacional)") e trocando pequenos detalhes de fraseado. *(Exemplo de uma
rodada anterior, com o conjunto de modelos usado até 26/08/2026 — GPT-4o-mini,
Claude Haiku 4.5, DeepSeek V4 Flash; o ponto ilustrado pelo cálculo continua
valendo com os modelos atuais.)*

```
semântica = 0,9469   ← significado praticamente idêntico
léxica    = 1,0000   ← mesmas palavras; a mudança de pontuação não penaliza no ROUGE-L
score_final = 0,8 × 0,9469 + 0,2 × 1,0000 = 0,9575
```

Aqui os dois critérios concordam porque a resposta manteve as mesmas palavras;
quando um modelo parafraseia mais (troca termos por sinônimos, muda a ordem),
a léxica cai mais que a semântica — é esse o cenário em que os dois **discordam**,
e por isso os dois são reportados juntos em vez de só um.

### ⚠ Defeito corrigido: truncamento em 128 tokens

O modelo semântico aceita no máximo **128 tokens** e descartava silenciosamente o
excedente. Cinco dos 40 gabaritos ultrapassam esse limite — o da lista de 191
estudantes tem **1.164 tokens**, ou seja, **~89% do texto era ignorado**.

Efeito medido: uma resposta contendo apenas os 20 primeiros nomes recebia score
semântico **1,0000** (nota máxima por acertar 11% do conteúdo). Após a correção
(processamento em blocos de ≤128 tokens, vetores combinados por média ponderada
pelo tamanho do bloco), a mesma resposta recebe **0,7992**.

Implementado em `back/app/evaluation/reference_scorer.py` (`_embed_long_text`).
Textos curtos seguem por caminho de bloco único — resultado numericamente
idêntico ao anterior, sem regressão.

### ⚠ Limitação: a origem dos pesos 80/20

Vieram do documento de metodologia do projeto de referência, que os justifica
*conceitualmente*: a semântica pesa mais porque "uma resposta pode estar correta
mesmo sem repetir exatamente os mesmos termos". **Não há, nesse documento, nenhum
experimento comparando 80/20 contra outras proporções.**

Formulação honesta para a defesa: os pesos foram **adotados por consistência com a
metodologia de referência**, não escolhidos por otimização empírica sobre este
conjunto de perguntas.

---

## 5. Threshold e taxa de aprovação (avaliador de referência)

O score de referência é contínuo. Para virar uma leitura de aprovação, aplica-se
um corte:

```
score_final ≥ threshold  →  "aprovada"
score_final <  threshold  →  "reprovada"
```

Score `0,65` é "aprovada" sob threshold `0,60` e "reprovada" sob `0,70`. Em vez de
fixar um único valor arbitrário, o código varre thresholds de `0,00` a `1,00` em
passos de `0,05` e reporta, para cada um, quantas respostas (por modelo e
condição) ficam acima do corte — uma contagem direta contra o gabarito, sem
comparar com nenhum rótulo de verdade externo.

Isso é deliberadamente mais simples do que a versão anterior deste projeto (que
calculava Precisão/Recall/F1 comparando o score contra um rótulo gerado por um LLM
juiz): por orientação do orientador, nenhuma metodologia deste projeto usa um LLM
para inventar um rótulo de correto/incorreto — só o gabarito, comparado
diretamente pelas duas metodologias (seções 3 e 4).

---

## 6. Limitações conhecidas

### Da metodologia de referência

- **Os pesos 80/20 não foram calibrados** neste projeto nem no de referência
  (seção 4). Um teste de sensibilidade — variar os pesos sobre os dados já
  calculados, sem custo de API — resolveria.
- ~~`SequenceMatcher` é ferramenta de *diff* de arquivos, caractere a caractere,
  não um padrão da área para sobreposição léxica~~ — **corrigido**: a métrica
  lexical passou a ser ROUGE-L (F-measure sobre palavras), o padrão de fato usado
  na literatura de NLP para isso. Como efeito colateral, a normalização manual de
  travessão vs. hífen deixou de ser necessária (pontuação não vira token no
  ROUGE-L, então já é ignorada naturalmente).
- **Similaridade não é a métrica ideal para perguntas factuais de lista**, que são
  a maioria deste conjunto. Nem semântica nem léxica respondem ao que importa: dos
  N itens, quantos foram listados corretamente e quantos foram inventados. Uma
  métrica em nível de item seria o complemento adequado.

### Da execução

- **Erros de rede contam como reprovação.** Quando uma chamada de métrica expira, o
  resultado é registrado como falha, sem distinguir "não deu para medir" de
  "medido e reprovado". As métricas do DeepEval não têm nova tentativa automática.
- **Amostra pequena.** Com dezenas de perguntas por célula, diferença de poucos
  pontos percentuais entre modelos está dentro da variação esperada e não sustenta
  afirmação de superioridade.
- **Rodadas reduzidas não substituem a completa.** O subconjunto estratificado
  (`EVAL_CASE_IDS`) serve para iterar rápido sobre a metodologia; os números finais
  do trabalho devem sair do conjunto completo.

---

## Onde está cada coisa no código

| Arquivo | Papel |
|---|---|
| `back/scripts/evaluate_models.py` | Orquestra a matriz, monta as métricas, agrega |
| `back/app/evaluation/reference_scorer.py` | Semântica + léxica + `score_final` |
| `back/app/evaluation/report_html.py` | Geração das páginas de resultado |
| `back/tests/evals/model_eval_cases.json` | As perguntas e gabaritos oficiais |
| `back/avaliacao_modelos/` | Saídas de cada rodada (CSV, JSON, HTML) |
