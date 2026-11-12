# Metodologia — estudo comparativo de métricas (tradicionais × LLM)

> Substitui, como foco dos testes do TCC, a avaliação comparativa de modelos descrita em
> `metodologia.md` (mantida como histórico das fases anteriores).

## 1. Pergunta de pesquisa

As métricas tradicionais de avaliação de texto já foram superadas por métricas atuais que usam um
LLM para avaliar (DeepEval)? Qual método avalia melhor as respostas de um chatbot RAG institucional (TitãsBot)?

Hipóteses a discutir:
- **H1:** métricas com LLM separam melhor respostas corretas de incorretas (AUC maior).
- **H2:** thresholds estratificados por tipo de resposta melhoram a concordância com a verdade.
- **H3:** o ganho das métricas com LLM tem custo sócio-técnico (dinheiro, reprodutibilidade, transparência, privacidade).

## 2. Desenho experimental

```
40 perguntas (gabarito oficial)
  × 3 modelos medianos equivalentes: gpt-5-mini · claude-haiku-4-5 · deepseek-chat
  × 2 condições: com RAG · sem RAG
  = até 240 respostas
        │
        ├── verdade: fatos-chave do gabarito → cobertura → rótulo (1 correta / 0 incorreta)
        ├── 11 métricas tradicionais (determinísticas, locais)
        └── 4 métricas DeepEval (LLM de apoio: GPT, gpt-5-nano)
                │
                ▼
      meta-avaliação: cada métrica vs a verdade
```

Os modelos são da faixa intermediária de cada empresa (nem os mais fortes, nem os mais fracos)
para que a comparação entre eles seja justa; os embeddings e a recuperação são os mesmos para todos.

## 3. Verdade a partir do gabarito

O gabarito (`tests/evals/model_eval_cases.json`) foi decomposto em **fatos-chave** em
`tests/evals/metric_eval_annotations.json`:

| Tipo de fato | Exemplo | Como casa |
|---|---|---|
| `terms` | "Asimov", "2014", "CNPq" | termos (ou regex) presentes na resposta |
| `name` | "Julio César Goldner Vendramini" | primeiro nome + um sobrenome (tolera nomes do meio omitidos) |
| `placement` | "SEK: 1° lugar — TRUFES (Regional)" | modalidade, colocação e competição no mesmo trecho (linha + cabeçalhos) |

- **Cobertura** = fatos encontrados / total de fatos.
- **Rótulo** = 1 (correta) se cobertura ≥ mínimo do tipo de resposta; senão 0.
- Sanidade: cada gabarito cobre 100% dos próprios fatos (teste automatizado).
- **Revisão humana**: rótulos podem ser corrigidos no explorador do relatório (`rotulos_revisados.csv`).

### Estratos (tipo de resposta)

| Estrato | Perguntas | Cobertura mínima |
|---|---|---|
| `fato_curto` | 2, 3, 5, 7, 30, 33, 40 | 100% |
| `descritiva` | 1, 4, 6, 35, 36 | 75% |
| `lista_curta` (≤ 8 itens) | 17 perguntas de resultados/orientadores/campeonatos | 80% |
| `lista_longa` (> 8 itens) | 11 perguntas (inclui 191 estudantes, 20 orientadores, 17 projetos) | 80% |

A estratificação por tipo foi preferida às 8 categorias temáticas porque algumas categorias têm
1–2 perguntas, e porque o comportamento das métricas muda com o formato: métricas lexicais
penalizam respostas curtas parafraseadas e favorecem listas longas copiadas.

## 4. Métricas comparadas

**Tradicionais:** Exact Match, F1 de tokens, BLEU-4, chrF, ROUGE-1/2/L, METEOR, cosseno MiniLM,
BERTScore e `ref_projeto` = 0,8 · cosseno + 0,2 · SequenceMatcher (fórmula literal do projeto de
referência Visualizador-do-avaliador).

**Com LLM (DeepEval):** GEval Correctness, Answer Relevancy, Faithfulness (só RAG) e
1 − Hallucination (contexto = gabarito). Essas métricas precisam de um LLM para executar seus
passos internos (extrair afirmações, pontuar critérios); usamos o GPT (`gpt-5-nano`) como esse
LLM de apoio. Não há um "juiz" explícito separado.

**Recuperação (diagnóstico, fora do ranking):** Hit@5 e Precision@5 nas 20 perguntas com evidências anotadas.

## 5. Meta-avaliação

Cada métrica vira um classificador: `score ≥ threshold ⇒ correta`.

1. **AUC** (independente de threshold) e correlação de Spearman/Kendall com a cobertura.
2. **Threshold global** — varredura 0,00…1,00 (passo 0,05): acurácia, acurácia balanceada,
   precisão/recall/F1 das classes *correta* e *incorreta* (mesma tabela do projeto de referência).
3. **Threshold estratificado** — a mesma varredura dentro de cada estrato; cada estrato recebe o seu
   threshold (estratos com < 6 respostas ou uma só classe usam o global).
4. **Validação cruzada leave-one-model-out** — thresholds calibrados nas respostas de 2 modelos e
   aplicados no 3º. É o número usado no ranking, pois evita que o threshold estratificado se ajuste
   demais aos dados.
5. **Ranking de sistemas** — Kendall τ entre a nota média da métrica e a taxa de acerto real dos 6 sistemas.
6. **Custo, tempo e estabilidade** — repetição das métricas DeepEval 3× em 6 perguntas (desvio-padrão da nota).

Critério padrão: acurácia balanceada (robusta ao desbalanceamento entre corretas e incorretas).

## 6. Características sócio-técnicas analisadas

- Respostas sobre **pessoas reais** (listas de alunos/orientadores): taxa de aprovação indevida por métrica.
- **Custo e acesso**: métricas com LLM exigem APIs pagas; tradicionais rodam localmente.
- **Reprodutibilidade/transparência**: fórmula determinística × métrica apoiada em LLM opaco e variável.
- **Viés do avaliador**: o LLM de apoio (GPT) é da mesma família de um dos modelos avaliados
  (gpt-5-mini) e pode favorecê-lo; LLMs também tendem a preferir respostas longas/fluentes.
- **Língua e domínio**: paráfrases em português, ordem de listas, nomes próprios.
- **Privacidade**: nomes de estudantes enviados a provedores externos durante a avaliação.
- **Papel humano**: autoria do gabarito, curadoria dos fatos-chave e revisão de rótulos.

## 7. Limitações

- A cobertura de fatos mede presença, não penaliza fatos extras inventados (mitigado pela revisão humana
  e pelas métricas de alucinação).
- METEOR usa WordNet em inglês; em português se aproxima de sobreposição de palavras.
- 40 perguntas × 6 sistemas é uma amostra pequena; reportar intervalos e evitar generalizações fortes.
