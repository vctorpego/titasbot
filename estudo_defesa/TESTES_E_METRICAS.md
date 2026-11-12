# Testes e Métricas — o que você precisa ter na cabeça

> Material focado só nos testes: como cada teste foi feito, como cada métrica calcula, o que deu, por que deu e o que se pode concluir. Os números conferem com o artigo do TCC (`ART_TCC.pdf`) e com os resultados em `back/avaliacao_metricas/`. **[DO CÓDIGO]** marca o que vem do código e não está no artigo; **[CÁLCULO COMPLEMENTAR]** marca o que foi calculado para a defesa. A Parte 9 traz o plano para estudar este material. Os cálculos passo a passo, a comparação entre métricas, o laboratório com respostas controladas e a simulação de banca estão no `ESTUDO_DETALHADO.md`.

---

## Parte 1 — O experimento em uma página

**Em uma frase:** fizemos 40 perguntas a 3 modelos, com e sem RAG (240 respostas), decidimos qual resposta estava certa comparando com os fatos-chave do gabarito, e depois testamos se 15 métricas automáticas conseguem reproduzir essa decisão.

**Os seis testes:**

| # | Teste | Pergunta que responde | Questão do artigo | Resultado em uma linha | Slide |
|---|---|---|---|---|---|
| T1 | Efeito do RAG na corretude | O RAG aumenta o acerto? | (i) | 5,8% → 51,7%, nos três modelos | 7 |
| T2 | Cobertura factual | As respostas ficam mais completas? | (i) | cerca de 8% → cerca de 63% dos fatos | 8 |
| T3 | Tipologia | O ganho é igual para todo tipo de pergunta? | (ii) | Lista curta 72,5% com RAG; lista longa 27,3% | 9 |
| T4 | Recuperação (Hit@5) | Por que ainda há erro com RAG? | apoio a (i) e (ii) | Com evidência no top-5: 60–70%; sem: 9–10% | 10 |
| T5 | Comparação das 15 métricas | Qual métrica separa certo de errado? | (iii) | G-Eval 0,968 e METEOR 0,966 empatam; Relevancy 0,520 | 11 |
| T6 | Matrizes de confusão | Que tipo de erro cada métrica comete? | (iii) | METEOR conservadora, G-Eval sensível, Relevancy aprova tudo | 12 |

**Análises de apoio:** custo e tempo das métricas, estabilidade entre execuções, respostas sobre pessoas e ordenação dos sistemas.

**Os números que amarram tudo:**

```
240 respostas = 40 perguntas × 3 modelos × 2 condições
69 corretas (28,75%) × 171 incorretas (71,25%)   → classes desbalanceadas → AUC e acurácia balanceada
Sem RAG 5,8% (7/120) → com RAG 51,7% (62/120)
Evidência no top-5: 60–70% de acerto · sem ela: 9–10%
AUC: G-Eval 0,968 · METEOR 0,966 (empate) · Answer Relevancy 0,520 (acaso)
Acurácia balanceada estratificada validada: METEOR 0,891 (maior) · G-Eval 0,875
```

---

## Parte 2 — A linha de montagem: como cada resposta virou um número

### 2.1 As perguntas

- **40 perguntas** do gabarito oficial da equipe, em **4 tipos**, definidos pela estrutura da resposta esperada:

| Tipo | Quantas | Exemplo | Corte de cobertura |
|---|---|---|---|
| Fato curto | 7 | "Em que ano a equipe participou da primeira competição?" | 100% |
| Descritiva | 5 | "Quem são os Titãs da Robótica?" | 75% |
| Lista curta (até 8 itens) | 17 | "Quem foram os orientadores da equipe em 2024?" | 80% |
| Lista longa | 11 | "Liste todos os estudantes que já passaram pela equipe" | 80% |

### 2.2 Gerar as 240 respostas

**[DO CÓDIGO]** `back/scripts/generate_answers.py`.

- **Sem RAG:** a pergunta vai direto ao modelo, com um prompt de sistema que identifica a equipe. **[PONTO SENSÍVEL]** Esse prompt cita "Ifes Campus Colatina" e o nome antigo "Asimov", o que deixou as q01 e q02 respondíveis sem RAG (Roteiro A4).
- **Com RAG:** a pergunta passa pelo `TitasBotService.ask()` completo: expansão da consulta, busca híbrida, seleção de evidências, geração com prompt por tipo, auditoria e fontes. **[PONTO SENSÍVEL]** A expansão e a seleção usam o próprio modelo gerador, então o contexto final varia um pouco entre os modelos (Roteiro A5).
- **Cada resposta foi gerada uma única vez** e guardada em `respostas.jsonl`, junto com os trechos usados. Toda a avaliação roda sobre esse arquivo congelado.

### 2.3 A régua: fatos-chave → cobertura → rótulo

**[DO CÓDIGO]** `back/app/evaluation/ground_truth.py` e `back/tests/evals/metric_eval_annotations.json`.

1. Cada resposta do gabarito foi decomposta em **fatos-chave** curados por humanos. Há três tipos:
   - **termos:** grupos de alternativas, e pelo menos uma de cada grupo precisa aparecer (por exemplo, "2015");
   - **nome:** basta o primeiro nome e um sobrenome, tolerando nomes do meio omitidos;
   - **colocação:** modalidade, posição e competição precisam aparecer no mesmo trecho da resposta.
2. **Cobertura** = fatos encontrados ÷ total de fatos.
3. **Rótulo:** a resposta é **correta (1)** se a cobertura atinge o corte do tipo; senão, **incorreta (0)**.

**Dois exemplos reais que vamos usar no material inteiro:**

| | Exemplo A — q07, GPT-5 mini, com RAG | Exemplo B — q05, DeepSeek, com RAG |
|---|---|---|
| Pergunta | Em que ano a equipe participou da primeira competição? | Quem idealizou a criação da equipe? |
| Gabarito | "A equipe competiu pela primeira vez em 2015 na LARC." | "A equipe de robótica foi idealizada por Renato Lopes de Oliveira, enquanto cursava a graduação em Sistemas de Informação no Ifes Campus Colatina." |
| Resposta | "A equipe participou da primeira competição em 2015." | "Renato Lopes de Oliveira idealizou a criação da equipe." |
| Fatos-chave | {2015} e {LARC} | {Renato Lopes de Oliveira} |
| Cobertura | 1 de 2 = 50% (faltou LARC) | 1 de 1 = 100% |
| Corte (fato curto) | 100% | 100% |
| **Rótulo** | **Incorreta** | **Correta** |

Guarde isto: **a régua só exige os fatos-chave**. A resposta B é curta, mas está certa; a resposta A parece o gabarito, mas está incompleta.

**Resultado da régua:** 69 respostas corretas e 171 incorretas.

**Erros conhecidos da régua [PONTO SENSÍVEL]:**
- **Nenhum rótulo foi revisado à mão** na rodada final.
- **q40, sem RAG:** o Claude e o GPT disseram que não tinham a informação, que é a resposta certa, mas com uma redação que o casamento de padrões não reconheceu. Ficaram como incorretas.
- **q07, gabarito × livro:** o gabarito diz que a primeira competição foi a LARC em 2015. O livro da equipe, na seção "A primeira competição" (p. 61), diz que foi o II TRUFES, em junho de 2015. O Claude com RAG respondeu TRUFES, seguindo o livro, e foi marcado incorreto. Afeta 1 resposta de 240 (Roteiro A15).

### 2.4 Pontuar: 15 métricas em cada resposta

**[DO CÓDIGO]** `back/scripts/score_answers.py`.

**O que cada métrica recebe:**

| Métrica | Pergunta | Resposta | Gabarito | Trechos recuperados |
|---|---|---|---|---|
| As 11 tradicionais (EM, Token F1, BLEU, ROUGE-1/2/L, METEOR, chrF, cosseno, BERTScore, ref_projeto) | | ✓ | ✓ | |
| G-Eval Correctness | ✓ | ✓ | ✓ | |
| Answer Relevancy | ✓ | ✓ | | |
| Faithfulness | | ✓ | | ✓ (5 primeiros, até 1.200 caracteres cada) |
| Hallucination | | ✓ | ✓ (como contexto) | |

- **Faithfulness** só existe com RAG e com trechos: são **117 respostas**. As 3 que faltam são da q40, respondida por uma regra sem busca.
- As 4 métricas de LLM usam o **`gpt-5-nano`** pelo DeepEval. O artigo não diz isso (Roteiro G4).
- **Estabilidade:** as métricas de LLM foram repetidas 3 vezes em 6 perguntas (q02, q07, q09, q21, q35, q36), nos 6 sistemas: 36 respostas repetidas (18 na Faithfulness).

### 2.5 Analisar: como se avalia uma métrica

**[DO CÓDIGO]** `back/app/evaluation/meta_evaluation.py`. Cada métrica é tratada como um **classificador**: "nota ≥ limiar → correta".

1. **AUC**, sem limiar: para todos os pares (uma resposta correta, uma incorreta), conta quantas vezes a correta recebeu nota maior. Empate conta meio. AUC = vitórias ÷ (69 × 171).
2. **Varredura de limiares:** testa os cortes 0,00; 0,05; …; 1,00 e calcula, para cada um, sensibilidade, especificidade e **acurácia balanceada** (BA = média das duas). Fica o corte de maior BA; no empate, o mais perto de 0,5.
3. **Limiar estratificado:** o mesmo, mas um corte para cada tipo de pergunta. Só vale se o tipo tem pelo menos 6 respostas e as duas classes; senão, usa o global.
4. **Validação leave-one-model-out:** calibra o limiar com as respostas de 2 modelos e aplica no 3º, três vezes. As 240 decisões resultantes geram a **BA validada (CV)** e as matrizes de confusão.
5. **Extras:** correlação de Spearman entre a nota e a cobertura; τ de Kendall entre a nota média de cada sistema e a taxa real de acerto.

**Como as métricas foram ranqueadas:** pela maior BA validada (global ou estratificada) e, no empate, pela AUC.

---

## Parte 3 — Os seis testes, um por um

### T1 — Efeito do RAG na corretude (slide 7, Tabela 1 e Figura 1)

**Pergunta:** fornecer contexto por RAG muda o acerto dos modelos?

**Como foi feito:** as mesmas 40 perguntas, em cada modelo, sem e com RAG. Compara-se a taxa de acerto e, pergunta a pergunta, quantas passaram de errada para certa (ganho) e de certa para errada (perda). O teste de McNemar exato verifica se ganhos e perdas são equilibrados, como seriam se o RAG não fizesse diferença.

**Resultado:**

| Modelo | Sem RAG | Com RAG | Diferença | Ganhos | Perdas | McNemar p |
|---|---|---|---|---|---|---|
| Claude Haiku 4.5 | 5,0% (2/40) | 55,0% (22/40) | +50,0 p.p. | 20 | 0 | 1,91e-06 |
| DeepSeek Chat | 7,5% (3/40) | 50,0% (20/40) | +42,5 p.p. | 18 | 1 | 7,63e-05 |
| GPT-5 mini | 5,0% (2/40) | 50,0% (20/40) | +45,0 p.p. | 18 | 0 | 7,63e-06 |
| **Total** | **5,8% (7/120)** | **51,7% (62/120)** | **+45,8 p.p.** | 56 | 1 | |

**[CÁLCULO COMPLEMENTAR]** Intervalos de 95% (Wilson): sem RAG, de 2,9% a 11,6%; com RAG, de 42,8% a 60,4%. Entre os modelos com RAG, os testes pareados dão p entre 0,69 e 1,0, sem diferença.

**Como se calcula o McNemar (Claude):** só contam as 20 perguntas que mudaram. Se o RAG não importasse, cada mudança teria 50% de chance de ir para cada lado. A chance de as 20 irem todas para "certa" é 2 × 0,5²⁰ ≈ 1,9 em um milhão.

**Por que deu isso:** as perguntas são sobre fatos locais (nomes, anos, colocações) que quase certamente não estão nos dados de treino dos modelos. Sem RAG, o modelo ou recusa ou inventa. Dos 7 acertos sem RAG, 6 vêm da pista do prompt (q01 e q02) e 1 é o DeepSeek dizendo "não sei" na q40, que é a resposta certa.

**Conclusão:**
- **Pode afirmar:** o RAG aumentou muito o acerto, nos três modelos, e o efeito do RAG foi muito maior que a diferença entre os modelos.
- **Não pode afirmar:** que o Claude é melhor (5 pontos com 40 perguntas não é significativo) nem que 51,7% vale para perguntas novas (o sistema tem regras ajustadas ao gabarito, Roteiro A14). Sem q01, q02 e q40, o efeito continua: de 0% para 48,6%.

**Em 30 segundos:** "Sem RAG, os modelos acertaram 5,8%; com RAG, 51,7%. Vale para os três, de 18 a 20 perguntas passaram de erradas para certas com no máximo uma perda, e o McNemar deu p menor que 0,001 em cada modelo. A diferença entre os modelos é pequena e não significativa: ter a evidência pesou mais que escolher o modelo."

**Perguntas prováveis:** A1, A3, A4, A14, B4, B5 (Roteiro).

### T2 — Cobertura factual (slide 8, Figura 2)

**Pergunta:** além de acertar mais, as respostas passaram a conter mais fatos do gabarito?

**Como foi feito:** média da cobertura de fatos-chave (de 0 a 1) por sistema. É uma medida contínua, que capta respostas parcialmente certas.

**Resultado:** Claude 5,8% → 62,9%; DeepSeek 9,9% → 62,9%; GPT-5 mini 9,7% → 64,4%.

**Por que deu isso:** sem RAG, as respostas são recusas ou textos genéricos, com quase nenhum fato. Com RAG, as listas de orientadores e classificações vêm das tabelas recuperadas.

**Conclusão:** houve ganho de completude, não só de acerto. **Limite:** a cobertura mede presença. Uma resposta com todos os fatos e mais um inventado tem cobertura 100%.

**Em 30 segundos:** "A cobertura média de fatos foi de 6% a 10% para cerca de 63%. Então as respostas ficaram muito mais completas. Mas cobertura mede presença: ela não penaliza um fato a mais inventado, por isso a lemos junto com as outras métricas."

**Perguntas prováveis:** A11, E7.

### T3 — Tipologia (slide 9, Figuras 3 e 4)

**Pergunta:** o efeito do RAG muda conforme o tipo de pergunta?

**Como foi feito:** taxa de acerto por sistema × tipo (Figura 3, heatmap) e agregada por tipo (Figura 4).

**Resultado:**

| Sistema | Descritiva (5) | Fato curto (7) | Lista curta (17) | Lista longa (11) |
|---|---|---|---|---|
| Claude sem / com RAG | 20% / 60% | 14% / 57% | 0% / **76%** | 0% / 18% |
| DeepSeek sem / com RAG | 20% / **0%** | 29% / 57% | 0% / **82%** | 0% / 18% |
| GPT-5 mini sem / com RAG | 20% / 20% | 14% / 57% | 0% / 59% | 0% / **45%** |

| Tipo | Figura 4 (com e sem RAG juntos) | Só com RAG [CÁLCULO COMPLEMENTAR] |
|---|---|---|
| Lista curta | 36,3% | **72,5%** |
| Fato curto | 38,1% | 57,1% |
| Lista longa | 13,6% | 27,3% |
| Descritiva | 23,3% | 26,7% |

**Por que deu isso:**
- **Listas curtas:** a resposta está numa tabela, num ou dois trechos, que a busca híbrida encontra bem (os pesos e o bônus priorizam tabelas em perguntas de lista).
- **Listas longas:** os itens estão espalhados por muitos trechos, e o contexto leva no máximo 8. Não cabem 20 orientadores, muito menos 191 estudantes. Todo acerto nesse tipo veio do RAG, mas ele não basta.
- **Fato curto:** exige 100% de cobertura. Os modelos costumam acertar metade, como o ano sem a competição na q07.
- **Descritiva:** pede síntese de cerca de 4 fatos com corte de 75%; faltar um reprova. São só 5 perguntas, então cada uma vale 20 pontos percentuais.

**Conclusão:** o ganho não é uniforme; a estrutura da resposta importa. **Limite:** não houve teste estatístico entre os tipos, e a descritiva tem só 5 perguntas, então são **tendências**.

**Em 30 segundos:** "O ganho depende do tipo. Nas listas curtas, ninguém acertava sem RAG, e com RAG chegou a 59–82%. Nas listas longas, também partimos de zero, mas com RAG ficamos em 18–45%, porque os itens estão espalhados e não cabem no contexto. São tendências: não fizemos teste entre os tipos."

**Perguntas prováveis:** A6, D5, E5, E6.

### T4 — Recuperação (slide 10, Tabela 2)

**Pergunta:** os erros que sobram com RAG vêm da busca ou da geração?

**Como foi feito:** em **20 perguntas** (o artigo diz só "subconjunto"), anotamos os termos de evidência que um trecho precisa conter **[DO CÓDIGO]** (`rag_stage_eval_cases.json`). Nos 5 primeiros trechos do contexto que cada modelo recebeu:
- um trecho é **suficiente** se contém o mínimo de termos para sustentar a resposta; **Hit@5 = 1** se pelo menos um dos 5 é suficiente;
- um trecho é **relevante** se contém o mínimo de termos de relevância; **Precision@5** = relevantes ÷ 5.

Depois, compara-se o acerto das respostas com Hit = 1 e com Hit = 0.

**Resultado:**

| Modelo | Hit@5 | Precision@5 | Acerto com Hit = 1 | Acerto com Hit = 0 |
|---|---|---|---|---|
| Claude | 45% (9/20) | 29% | 66,7% (6/9) | 9,1% (1/11) |
| DeepSeek | 50% (10/20) | 34% | 70% (7/10) | 10% (1/10) |
| GPT-5 mini | 50% (10/20) | 35% | 60% (6/10) | 10% (1/10) |

**Por que deu isso:** sem a evidência, o modelo não tem de onde tirar o fato. Com a evidência, ainda erra 30–40% das vezes, porque a seleção descarta o trecho certo, a resposta junta trechos de forma incompleta ou a geração omite itens. O Hit@5 varia entre os modelos porque o próprio modelo participa da busca.

**Conclusão:** a recuperação é **necessária, mas não suficiente**, e há espaço claro para melhorar o recuperador (Hit@5 de 45–50%). **Limite:** vale para o subconjunto anotado.

**Em 30 segundos:** "Quando a evidência certa está entre os cinco primeiros trechos, o acerto fica entre 60% e 70%; quando não está, cai para cerca de 10%. A recuperação é necessária. Mas, mesmo com ela, 30–40% erram, então também não é suficiente."

**Perguntas prováveis:** A5, D5.

### T5 — Comparação das 15 métricas (slide 11, Tabela 3, Figuras 5 a 8)

**Pergunta:** qual métrica automática reproduz melhor a decisão "certa ou errada" da régua?

**Como foi feito:** Parte 2.5. Para cada métrica: AUC, limiar global e estratificado, validação deixando um modelo de fora, tempo e custo.

**Resultado (Tabela 3 do artigo):**

| Métrica | Família | AUC | BA global (CV) | BA estrat. (CV) | Limiar | s/resposta | US$ total |
|---|---|---|---|---|---|---|---|
| G-Eval | LLM | **0,968** | 0,872 | 0,875 | 0,40 | 23,7 | 0,43 |
| METEOR | lexical | **0,966** | 0,862 | **0,891** | 0,35 | 0,010 | 0 |
| chrF | lexical | 0,963 | 0,872 | 0,875 | 0,50 | 0,002 | 0 |
| ROUGE-L | lexical | 0,952 | 0,875 | 0,885 | 0,25 | 0,000 | 0 |
| BLEU | lexical | 0,951 | 0,859 | 0,837 | 0,10 | 0,008 | 0 |
| Token F1 | lexical | 0,946 | 0,846 | 0,871 | 0,45 | 0,000 | 0 |
| ROUGE-2 | lexical | 0,945 | **0,882** | 0,858 | 0,20 | 0,000 | 0 |
| BERTScore | semântica | 0,944 | 0,880 | 0,870 | 0,70 | 0,125 | 0 |
| ROUGE-1 | lexical | 0,943 | 0,833 | 0,889 | 0,45 | 0,000 | 0 |
| ref_projeto | referência | 0,920 | 0,814 | 0,849 | 0,55 | 0,114 | 0 |
| Cosseno MiniLM | semântica | 0,903 | 0,824 | 0,863 | 0,65 | 0,114 | 0 |
| Hallucination (inv.) | LLM | 0,658 | 0,663 | 0,663 | 0,50 | 19,9 | 0,36 |
| Exact Match | lexical | 0,594 | 0,594 | 0,594 | 0,50 | 0,000 | 0 |
| Faithfulness (n=117) | LLM | 0,557 | 0,586 | 0,578 | 0,70 | 63,2 | 0,58 |
| Answer Relevancy | LLM | 0,520 | 0,496 | 0,502 | 0,95 | 30,4 | 0,52 |

**[CÁLCULO COMPLEMENTAR]** Bootstrap por pergunta da diferença de AUC entre G-Eval e METEOR: de −0,024 a +0,034. Contém o zero, então é empate.

**Por que deu isso:** Parte 6, as seis causas.

**Conclusão:**
- Famílias muito diferentes chegam ao topo: uma de LLM (G-Eval) e várias lexicais gratuitas (METEOR, chrF, ROUGE).
- A maior AUC não garante a melhor decisão: a G-Eval cai de 0,913 (dentro da amostra) para 0,872 validada.
- Relevância e fidelidade ficam no acaso porque medem outra coisa.
- **Limite:** o resultado das lexicais é próprio deste domínio, cheio de nomes e anos.

**Em 30 segundos:** "Tratamos cada métrica como um classificador. A AUC é a chance de ela dar nota maior à resposta certa. G-Eval, com 0,968, e METEOR, com 0,966, empatam no topo. Com o limiar validado num modelo que ficou de fora, a METEOR com limiar por tipo lidera, com 0,891. Answer Relevancy e Faithfulness ficam perto de 0,5 porque medem relevância e fidelidade, não correção."

**Perguntas prováveis:** B1, B2, B3, B6, B7, B8, B9, C1, C3, C6, G2, G7.

### T6 — Matrizes de confusão (slide 12, Tabela 5 e Figura 9)

**Pergunta:** quando a métrica erra, que tipo de erro ela comete?

**Como foi feito:** as 240 decisões da validação leave-one-model-out, com o **limiar global**. VN = incorreta reprovada; FP = incorreta aprovada; FN = correta reprovada; VP = correta aprovada.

**Resultado:**

| Métrica | VN | FP | FN | VP | Especificidade | Sensibilidade |
|---|---|---|---|---|---|---|
| METEOR | 161 | 10 | 15 | 54 | 94,2% (161/171) | 78,3% (54/69) |
| G-Eval | 157 | 14 | 12 | 57 | 91,8% | 82,6% |
| Answer Relevancy | 16 | 155 | 7 | 62 | 9,4% | 89,9% |

Com o limiar por tipo, a METEOR fica em 156 / 15 / 9 / 60 (BA 0,891).

**Respostas sobre pessoas [CÁLCULO COMPLEMENTAR do relatório]:** são 78 respostas, 50 delas incorretas. A G-Eval aprovou indevidamente 1 (2%); a METEOR, 6 (12%); a Answer Relevancy, 43 (86%).

**Por que deu isso:**
- A METEOR exige sobreposição de palavras: reprova paráfrases e respostas curtas (FN, como o Exemplo B) e aprova pouca coisa errada.
- A G-Eval aceita paráfrase (menos FN), mas às vezes dá meia nota a resposta incompleta (FP, como o Exemplo A).
- A Answer Relevancy aprova quase tudo, porque quase toda resposta fala do assunto da pergunta.

**Conclusão:** métricas com AUC parecida erram de jeitos diferentes; a escolha depende de qual erro custa mais. Num chatbot institucional, o FP (aprovar informação errada) é o mais grave. Por isso nenhuma métrica deve ser árbitro único.

**Em 30 segundos:** "A METEOR é a mais conservadora: aprova só 10 erradas, mas reprova 15 certas. A G-Eval é mais sensível: reconhece 83% das certas, mas aprova 14 erradas. A Answer Relevancy parece ótima pela sensibilidade, mas aprovou 155 das 171 erradas."

**Perguntas prováveis:** B2, B7, C3, C6.

---

## Parte 4 — As 15 métricas, uma por uma

### 4.0 Os dois exemplos em todas as métricas

Lembre: o **A está incorreto** (faltou LARC) e o **B está correto** (tem o nome).

| Métrica | Exemplo A (incorreto) | Decisão com o limiar global | Exemplo B (correto) | Decisão com o limiar global |
|---|---|---|---|---|
| Exact Match | 0 | reprova ✓ | 0 | reprova ✗ |
| Token F1 | 0,56 | aprova (≥ 0,45) ✗ | 0,38 | reprova ✗ |
| BLEU | 0,07 | reprova (< 0,10) ✓ | 0,07 | reprova ✗ |
| ROUGE-1 | 0,56 | aprova ✗ | 0,38 | reprova ✗ |
| ROUGE-2 | 0,25 | aprova (≥ 0,20) ✗ | 0,20 | aprova ✓ |
| ROUGE-L | 0,56 | aprova ✗ | 0,31 | aprova (≥ 0,25) ✓ |
| METEOR | 0,46 | aprova (≥ 0,35) ✗ | 0,20 | reprova ✗ |
| chrF | 0,50 | aprova (≥ 0,50) ✗ | 0,28 | reprova ✗ |
| Cosseno MiniLM | 0,77 | aprova ✗ | 0,63 | reprova (< 0,65) ✗ |
| BERTScore | 0,84 | aprova ✗ | 0,77 | aprova ✓ |
| ref_projeto | 0,75 | aprova ✗ | 0,58 | aprova (≥ 0,55) ✓ |
| G-Eval | 0,50 | aprova (≥ 0,40) ✗ | 0,20 | reprova ✗ |
| Answer Relevancy | 1,00 | aprova ✗ | 1,00 | aprova ✓ |
| Faithfulness | 1,00 | aprova ✗ | 1,00 | aprova ✓ |
| Hallucination (inv.) | 1,00 | aprova ✗ | 1,00 | aprova ✓ |

**A lição dos dois exemplos:** das métricas que dão notas diferentes aos dois, todas menos o BLEU dão nota **maior à resposta errada (A) do que à certa (B)**. O motivo é que todas comparam com o **texto inteiro** do gabarito, e a régua só exige os **fatos-chave**. A resposta A copia a frase do gabarito e omite um fato; a B tem o fato, mas pouco texto em comum. São casos difíceis, de fato curto, e é por isso que o fato curto tem a menor AUC em quase todas as métricas (Parte 5.4). Nas 240 respostas, porém, a maioria dos pares é fácil, e as boas métricas acertam a ordem em mais de 95% deles.

### 4.1 Métricas lexicais (sobreposição de palavras ou caracteres)

**Preparação comum [DO CÓDIGO]:** o texto é posto em minúsculas, os acentos são removidos e as palavras são separadas por `\w+`. O ROUGE é exceção: mantém os acentos.

#### Exact Match (EM)
- **O que mede:** a resposta é idêntica ao gabarito, palavra por palavra?
- **Como calcula:** 1 se as listas de palavras normalizadas são iguais; senão, 0.
- **Resultado:** AUC 0,594; especificidade 100% e sensibilidade 18,8%. Só acertou 13 respostas, todas listas de classificações copiadas literalmente da tabela (q08 a q16, com RAG).
- **Por que:** respostas de LLM quase nunca repetem o gabarito palavra por palavra.
- **Frase:** "O Exact Match serve de piso: mostra que exigir igualdade literal não funciona para respostas geradas."

#### Token F1
- **O que mede:** quantas palavras a resposta e o gabarito têm em comum, equilibrando precisão e revocação (estilo SQuAD).
- **Como calcula:** P = palavras em comum ÷ palavras da resposta; R = palavras em comum ÷ palavras do gabarito; F1 = 2PR ÷ (P + R).
- **Exemplo A, calculado:** gabarito com 10 palavras (a, equipe, competiu, pela, primeira, vez, em, 2015, na, larc); resposta com 8 (a, equipe, participou, da, primeira, competicao, em, 2015). Em comum: a, equipe, primeira, em, 2015 = 5. P = 5/8 = 0,625; R = 5/10 = 0,5; F1 = 2 × 0,625 × 0,5 ÷ 1,125 = **0,556**, igual ao valor nos dados.
- **Resultado:** AUC 0,946; BA estratificada validada 0,871; AUC na descritiva só 0,677.
- **Por que:** ignora a ordem e trata todas as palavras igualmente, inclusive "a", "da" e "em".
- **Frase:** "Conta palavras em comum; funciona bem para listas e mal para descrições."

#### BLEU-4
- **O que mede:** precisão de sequências de 1 a 4 palavras da resposta que aparecem no gabarito, com penalidade se a resposta for curta. Veio da tradução automática.
- **Como calcula:** média geométrica das precisões de 1, 2, 3 e 4 palavras × penalidade de brevidade. Com suavização (`method1` do NLTK): quando uma precisão é zero, usa 0,1 no numerador.
- **Exemplo A, calculado:** p1 = 5/8; p2 = 2/7 ("a equipe", "em 2015"); p3 = 0 → 0,1/6; p4 = 0 → 0,1/5. Média geométrica = (0,625 × 0,286 × 0,0167 × 0,02)^¼ ≈ 0,088. Brevidade: 8 palavras contra 10 → e^(1 − 10/8) ≈ 0,779. BLEU ≈ 0,088 × 0,779 = **0,068**, igual aos dados.
- **Resultado:** AUC 0,951, mas limiar baixíssimo (0,10); BA estratificada validada 0,837.
- **Por que:** em respostas curtas quase não há sequência de 4 palavras em comum, então as notas ficam espremidas perto de zero.
- **Frase:** "Ordena bem, mas a escala fica comprimida perto de zero; é difícil escolher o corte."

#### ROUGE-1, ROUGE-2 e ROUGE-L
- **O que medem:** sobreposição entre resposta e gabarito, vinda da avaliação de resumos. ROUGE-1 conta palavras; ROUGE-2, pares de palavras seguidas; ROUGE-L, a maior subsequência comum (palavras na mesma ordem, não necessariamente juntas). Usamos a medida F.
- **Exemplo A:** ROUGE-1 = 0,556, como o Token F1. ROUGE-2: o gabarito tem 9 pares e a resposta 7; em comum, "a equipe" e "em 2015" → P = 2/7, R = 2/9, F = **0,25**. ROUGE-L: a maior sequência comum é "a equipe … primeira … em 2015" = 5 palavras → **0,556**.
- **Resultado:** AUC 0,943 / 0,945 / 0,952. O ROUGE-2 tem a maior BA global validada (0,882); o ROUGE-1 sobe de 0,833 para 0,889 com limiar por tipo.
- **Por que:** listas copiadas da tabela têm muita sobreposição, e respostas sem RAG quase nenhuma. Na descritiva, ROUGE-1 e Token F1 são fracos (0,68).
- **Frase:** "Sobreposição de palavras; muito boa aqui, porque estar certo é conter os nomes e os anos."

#### METEOR (a melhor BA validada)
- **O que mede:** alinhamento de palavras entre resposta e gabarito, com **peso maior na revocação** e penalidade quando as palavras alinhadas ficam picadas em vários pedaços.
- **Como calcula:**
  1. Alinha as palavras iguais (em inglês, também radicais e sinônimos do WordNet; em português, isso praticamente não funciona, então sobra a igualdade exata).
  2. P = alinhadas ÷ palavras da resposta; R = alinhadas ÷ palavras do gabarito.
  3. Fmédia = P·R ÷ (0,9·P + 0,1·R), que favorece a revocação.
  4. Penalidade = 0,5 × (pedaços ÷ alinhadas)³.
  5. METEOR = Fmédia × (1 − penalidade).
- **Exemplo A, calculado:** 5 palavras alinhadas, P = 0,625, R = 0,5. Fmédia = 0,3125 ÷ 0,6125 = 0,510. Pedaços: "a equipe", "primeira", "em 2015" = 3. Penalidade = 0,5 × (3/5)³ = 0,108. METEOR = 0,510 × 0,892 = **0,455**, igual aos dados. Como o limiar é 0,35, a METEOR **aprovou** essa resposta incorreta (um FP).
- **Resultado:** AUC 0,966; BA validada 0,862 (global) e **0,891** (por tipo, a maior); especificidade 94,2%. AUC por tipo: 0,99 a 1,00 nas listas, 0,91 na descritiva e 0,84 no fato curto.
- **Limiar por tipo:** 0,35 em descritivas e fatos; 0,55 em listas curtas; 0,60 em listas longas.
- **Por que funcionou:** estar correto, neste domínio, é **cobrir** os nomes, anos e colocações do gabarito, e a METEOR é a métrica clássica que mais pesa a revocação. Listas certas também seguem a ordem das tabelas, e a penalidade de fragmentação recompensa isso. O limiar maior nas listas existe porque uma lista incompleta ainda copia muito texto da tabela.
- **Frase:** "Em português, a METEOR vira uma comparação de palavras com peso na revocação, e cobrir os fatos é exatamente o que define uma resposta certa aqui."

#### chrF
- **O que mede:** sobreposição de **sequências de caracteres** (de 1 a 6), com F-beta de β = 3, ou seja, a revocação pesa bem mais que a precisão.
- **Por que é interessante:** caracteres lidam melhor com a flexão do português ("competiu" e "competição" compartilham "compet").
- **Resultado:** AUC 0,963 (3ª); especificidade validada 94,7%, a maior entre as boas; BA estratificada 0,875.
- **Frase:** "Parecida com a METEOR, também prioriza revocação, e mais robusta à flexão das palavras."

### 4.2 Métricas semânticas (significado por vetores)

#### Cosseno MiniLM
- **O que mede:** a proximidade de significado entre resposta e gabarito.
- **Como calcula:** cada texto vira um vetor (`paraphrase-multilingual-MiniLM-L12-v2`), e a nota é o cosseno entre os vetores. **[DO CÓDIGO]** Textos longos são divididos em blocos de até 126 tokens, e os vetores são combinados por média ponderada, para não cortar o gabarito de 191 estudantes.
- **Resultado:** AUC 0,903 (11ª); dentro só do RAG, cai para 0,784. Notas médias sem RAG em torno de 0,40.
- **Por que:** "a equipe competiu em 2015" e "a equipe competiu em 2016" têm quase o mesmo significado para o vetor; um ano trocado quase não muda o cosseno.
- **Frase:** "Mede o assunto e o sentido geral, não detalhes como um ano ou um nome."

#### BERTScore
- **O que mede:** proximidade de significado palavra a palavra, com vetores contextuais.
- **Como calcula:** cada palavra (token) da resposta é casada com a palavra mais parecida do gabarito, e vice-versa, usando `bert-base-multilingual-cased`; daí sai a F1. **[DO CÓDIGO]** Sem o reescalonamento pela linha de base.
- **Resultado:** AUC 0,944; BA global validada 0,880 (2ª). Limiar 0,70; as médias vão de cerca de 0,60 sem RAG a 0,76 com RAG.
- **Por que o limiar é 0,70:** sem o reescalonamento, até textos sem relação ficam por volta de 0,55 a 0,60, então a faixa útil fica espremida no alto.
- **Frase:** "Semântica por palavra; boa aqui, mas com a escala comprimida, porque não aplicamos a linha de base."

#### ref_projeto
- **O que mede:** a fórmula do projeto de referência indicado pelo orientador (não foi criada por nós).
- **Como calcula:** 0,8 × cosseno MiniLM + 0,2 × `SequenceMatcher` (proporção de caracteres em blocos comuns).
- **Resultado:** AUC 0,920; BA validada 0,814 / 0,849.
- **Por que:** herda a fraqueza do cosseno, que tem 80% do peso.
- **Frase:** "Replicamos a fórmula do projeto anterior para comparar; ela ficou no meio do ranking."

### 4.3 Métricas baseadas em LLM (DeepEval, com `gpt-5-nano`)

#### G-Eval Correctness (a maior AUC)
- **O que mede:** se a resposta está correta em relação à esperada, segundo um critério escrito por nós.
- **Como calcula:**
  1. Recebe o critério: "aceite variações de redação, mas penalize fatos ausentes, anos errados, classificações erradas ou invenção de informações; não penalize detalhes adicionais compatíveis".
  2. O LLM gera passos de avaliação a partir do critério (cadeia de raciocínio).
  3. O LLM lê a pergunta, a resposta e o gabarito e dá uma nota de 0 a 10, que vira 0 a 1.
  4. **[DO CÓDIGO]** O `gpt-5-nano` não fornece as probabilidades dos tokens, então a nota é inteira (0; 0,1; …; 1), sem a média ponderada do artigo original.
- **Resultado:** AUC 0,968 (0,96745); BA validada 0,872 / 0,875; especificidade 91,8% e sensibilidade 82,6%; nas respostas sobre pessoas, aprovou indevidamente só 2%. Leva 23,7 s por resposta (US$ 0,43 no total). Repetindo a avaliação, a nota variou em média 0,056, e até 0,4 na mesma resposta.
- **Por que funcionou:** entende paráfrase e compara fatos. Por isso é a mais uniforme entre os tipos (AUC de 0,93 no fato curto e na descritiva, contra 0,84 e 0,91 da METEOR).
- **Onde falha:** dá meia nota a resposta incompleta (Exemplo A: 0,5) e penaliza resposta curta e certa quando o gabarito tem detalhes extras (Exemplo B: 0,2). Também já marcou como errada uma lista correta só por estar em tabela com uma linha duplicada (q28 do Claude: nota 0,3).
- **Frase:** "É a métrica que mais se parece com um avaliador humano, mas custa, demora e não dá a mesma nota duas vezes."

#### Answer Relevancy (no nível do acaso)
- **O que mede:** se a resposta trata do assunto da pergunta. **Não usa o gabarito.**
- **Como calcula:** o LLM quebra a resposta em afirmações, julga cada uma como relevante ou não para a pergunta, e a nota = afirmações não irrelevantes ÷ total. **[DO CÓDIGO]** No DeepEval, "não sei" conta como relevante, e uma resposta sem afirmações vale 1.
- **Resultado:** AUC 0,520; BA validada 0,496; aprovou 155 das 171 erradas. A ordem dos sistemas sai **invertida** (τ = −0,79): sem RAG, a média foi 0,96 a 0,99; com RAG, 0,80 a 0,94.
- **Por que:** uma recusa ("não tenho essa informação") ou uma resposta errada sobre o assunto são 100% relevantes. Exemplo real (q12, GPT-5 mini sem RAG): devolveu uma pergunta e sugeriu competições que a equipe nunca disputou, e levou nota 1,0.
- **Frase:** "Relevância não é correção: uma resposta pode ser totalmente sobre o assunto e totalmente errada."

#### Faithfulness (no nível do acaso)
- **O que mede:** se a resposta é fiel aos **trechos recuperados**, ou seja, se não os contradiz. Só existe com RAG.
- **Como calcula:** o LLM extrai até 8 verdades dos trechos e as afirmações da resposta; julga cada afirmação (contradiz as verdades: sim, não ou não sei). Nota = afirmações não contraditórias ÷ total.
- **Resultado:** AUC 0,557 (n = 117); média de 0,89 nos três modelos, sem diferença (τ = 0); especificidade 19%. A mais cara: 63 s por resposta.
- **Por que:** o modelo, com RAG, quase sempre fica fiel ao que recebeu. O erro típico é **omissão**, não contradição: na q33, os trechos só tinham 2019 e 2024, a resposta trouxe exatamente isso e levou 1,0, mas faltou 2025.
- **Frase:** "Fidelidade mede se a resposta respeita o contexto; se o contexto veio incompleto, a resposta pode ser fiel e errada."

#### Hallucination, invertida (fraca)
- **O que mede:** se a resposta **contradiz** o contexto dado. Usamos o gabarito como contexto e invertemos a nota (1 − alucinação), para que maior seja melhor.
- **Como calcula:** para cada contexto, o LLM diz se a resposta concorda com ele. Alucinação = contextos contraditos ÷ total. **Com um único contexto, a nota só pode ser 0 ou 1.**
- **Resultado:** AUC 0,658; especificidade 42,7%; a mais instável (desvio médio de 0,18, e a mesma resposta mudou de 0 para 1).
- **Por que:** não enxerga **omissão**. Uma resposta com 2 de 10 itens, sem contradizer nada, leva 1. Ela pega contradições: o DeepSeek sem RAG disse que a primeira competição foi em 2014 e levou 0.
- **Frase:** "Detecta contradição, não falta de informação, e no nosso caso o erro mais comum é a falta."

---

## Parte 5 — Como cada métrica se comporta em cada modelo e tipo de pergunta

**[CÁLCULO COMPLEMENTAR]** Calculado sobre `respostas_avaliadas.csv` e `analise_metricas.json`. Não está no artigo.

### 5.1 AUC por modelo (com e sem RAG juntos)

| Métrica | Claude | DeepSeek | GPT-5 mini |
|---|---|---|---|
| G-Eval | 0,972 | 0,977 | 0,958 |
| METEOR | 0,972 | 0,962 | 0,962 |
| chrF | 0,968 | 0,960 | 0,956 |
| ROUGE-L | 0,953 | 0,966 | 0,937 |
| BLEU | 0,950 | 0,962 | 0,943 |
| Token F1 | 0,945 | 0,963 | 0,928 |
| ROUGE-2 | 0,942 | 0,952 | 0,940 |
| BERTScore | 0,934 | 0,966 | 0,927 |
| ROUGE-1 | 0,940 | 0,960 | 0,925 |
| ref_projeto | 0,904 | 0,936 | 0,916 |
| Cosseno | 0,890 | 0,917 | 0,907 |
| Hallucination | 0,633 | 0,601 | 0,738 |
| Exact Match | 0,562 | 0,609 | 0,614 |
| Faithfulness | 0,585 | 0,537 | 0,550 |
| Answer Relevancy | 0,584 | 0,457 | 0,519 |

**O que concluir:**
- **A ordem das métricas é a mesma nos três modelos.** As boas são boas para qualquer gerador, o que reforça a validação leave-one-model-out.
- **A G-Eval não favoreceu o GPT:** a AUC dela é a **menor** justamente no GPT-5 mini (0,958). Junto com as médias (0,50 Claude, 0,51 GPT, 0,53 DeepSeek), não há sinal de autopreferência (Roteiro C7).
- A METEOR é a mais estável entre os modelos (0,962 a 0,972).

### 5.2 Nota média por sistema × acerto real

| Métrica | Claude s/c RAG | DeepSeek s/c RAG | GPT s/c RAG | τ de Kendall |
|---|---|---|---|---|
| **Acerto real** | **5% / 55%** | **7,5% / 50%** | **5% / 50%** | — |
| METEOR | 0,11 / 0,52 | 0,11 / 0,52 | 0,11 / 0,48 | **0,93** |
| G-Eval | 0,19 / 0,50 | 0,22 / 0,53 | 0,21 / 0,51 | 0,65 |
| chrF | 0,29 / 0,57 | 0,28 / 0,56 | 0,31 / 0,53 | 0,65 |
| ROUGE-L | 0,08 / 0,48 | 0,10 / 0,52 | 0,08 / 0,50 | 0,65 |
| BERTScore | 0,61 / 0,75 | 0,62 / 0,77 | 0,60 / 0,76 | 0,65 |
| Cosseno | 0,39 / 0,67 | 0,40 / 0,69 | 0,43 / 0,70 | 0,50 |
| Hallucination (inv.) | 0,68 / 0,74 | 0,65 / 0,80 | 0,43 / 0,70 | 0,65 |
| Faithfulness | — / 0,89 | — / 0,89 | — / 0,89 | 0,00 |
| Answer Relevancy | 0,97 / 0,86 | 0,96 / 0,80 | 0,99 / 0,94 | **−0,79** |

**O que concluir:**
- **Quase todas enxergam o efeito do RAG:** a nota média sobe muito do "sem" para o "com".
- **A METEOR é a única que acerta a ordem completa** (τ = 0,93). A maioria fica em 0,65 porque coloca o DeepSeek com RAG à frente do Claude com RAG, quando na verdade o Claude acertou mais (55% contra 50%).
- **O BERTScore enxerga o RAG, mas comprimido:** de 0,60 para 0,76, por causa da falta de reescalonamento.
- **A Faithfulness não distingue os modelos:** 0,89 nos três.
- **A Answer Relevancy inverte:** dá nota maior aos sistemas sem RAG, que erram 95%, porque recusas e respostas genéricas são "relevantes".

### 5.3 A métrica está só detectando "tem RAG ou não"? (AUC só com RAG)

Como quase todas as respostas sem RAG estão erradas, alguém pode suspeitar que a AUC alta só separa "com RAG" de "sem RAG". Dentro das 120 respostas com RAG (62 certas e 58 erradas):

| METEOR | G-Eval | chrF | BLEU | ROUGE-L | Token F1 | ROUGE-2 | ROUGE-1 | BERTScore | ref_projeto | Cosseno | Hallucination | EM | Relevancy | Faithfulness |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0,940 | 0,935 | 0,933 | 0,903 | 0,901 | 0,895 | 0,892 | 0,887 | 0,862 | 0,813 | 0,784 | 0,636 | 0,605 | 0,575 | 0,557 |

**O que concluir:** as melhores continuam acima de 0,93 só entre as respostas com RAG, então **separam certo de errado, não só a condição**. METEOR e G-Eval seguem empatadas no topo. As semânticas caem mais (o cosseno vai a 0,78), porque, com RAG, certas e erradas falam do mesmo assunto.

### 5.4 AUC por tipo de pergunta

| Métrica | Descritiva | Fato curto | Lista curta | Lista longa |
|---|---|---|---|---|
| G-Eval | **0,932** | **0,925** | 0,984 | 0,987 |
| METEOR | 0,913 | 0,839 | 0,989 | 1,000 |
| chrF | 0,876 | 0,839 | 0,989 | 1,000 |
| ROUGE-L | 0,832 | 0,856 | 0,976 | 1,000 |
| BLEU | 0,820 | 0,901 | 0,973 | 0,986 |
| BERTScore | 0,739 | 0,880 | 0,958 | 0,971 |
| ROUGE-1 | 0,683 | 0,868 | 0,977 | 0,998 |
| Token F1 | 0,677 | 0,882 | 0,979 | 1,000 |
| Cosseno | 0,851 | 0,825 | 0,945 | 0,910 |
| Answer Relevancy | 0,540 | 0,597 | 0,464 | 0,596 |

**O que concluir:**
- **Nas listas, quase todas separam perfeitamente** (0,97 a 1,00): uma lista certa copia muito mais itens do gabarito que uma errada.
- **No fato curto e na descritiva, as lexicais caem**, e a G-Eval é a melhor. É onde a paráfrase e a concisão mais pesam (Exemplos A e B).
- **Isso explica o empate geral:** a G-Eval ganha nos tipos com poucas respostas certas (descritiva e fato curto), e as lexicais empatam ou ganham nas listas, que são a maioria das perguntas (28 de 40).
- **Cuidado:** a descritiva tem só 7 respostas certas e a lista longa só 9, então essas AUCs são instáveis.

### 5.5 Limiar escolhido por tipo de pergunta

| Métrica | Global | Descritiva | Fato curto | Lista curta | Lista longa |
|---|---|---|---|---|---|
| METEOR | 0,35 | 0,35 | 0,35 | 0,55 | 0,60 |
| G-Eval | 0,40 | 0,40 | 0,65 | 0,40 | 0,40 |
| ROUGE-L | 0,25 | 0,30 | 0,25 | 0,45 | 0,70 |
| Token F1 | 0,45 | 0,45 | 0,25 | 0,65 | 0,65 |
| BERTScore | 0,70 | 0,75 | 0,70 | 0,75 | 0,70 |
| BLEU | 0,10 | 0,05 | 0,05 | 0,10 | 0,20 |

**O que concluir:**
- **Nas lexicais, o limiar das listas é maior:** listas incompletas ainda copiam muito texto da tabela, então é preciso exigir mais para aprovar.
- **No fato curto, as lexicais pedem menos** (0,25 no ROUGE-L e no Token F1), porque uma resposta curta e certa tem pouca sobreposição com um gabarito mais longo.
- **A G-Eval pede mais no fato curto** (0,65): ela tende a dar meia nota a respostas que acertam metade, como o Exemplo A.
- É por isso que o limiar por tipo ajuda as métricas cuja escala depende do tamanho da resposta (METEOR de 0,862 para 0,891; ROUGE-1 de 0,833 para 0,889), mas pode piorar outras (ROUGE-2, BLEU, BERTScore), porque, com poucos dados por tipo, o limiar sobreajusta.

---

## Parte 6 — Por que os resultados deram o que deram (as seis causas)

1. **O domínio é feito de entidades.** Responder certo, aqui, é conter os nomes, anos e colocações certos. Métricas que contam palavras do gabarito, com peso na revocação, capturam isso diretamente. Por isso as lexicais simples empataram com a G-Eval. O próprio artigo avisa que isso não se generaliza para tarefas com mais paráfrase.
2. **A régua é de fatos, e isso pode favorecer as lexicais.** A régua procura fatos específicos no texto. Isso é parecido com o que as lexicais fazem, então há risco de viés. Três coisas mitigam: a G-Eval, que não conta palavras, chegou à mesma AUC; só entre as respostas com RAG as lexicais continuam acima de 0,93; e a correlação das melhores com a cobertura é parecida (Spearman de 0,83 a 0,84 em METEOR, G-Eval e ROUGE-L). Roteiro A10.
3. **Algumas métricas medem outra coisa.** Answer Relevancy mede assunto; Faithfulness mede fidelidade ao contexto; Hallucination mede contradição. Nenhuma mede se o fato pedido está lá, e o erro dominante aqui é **omissão**. Por isso ficam perto do acaso, e não porque sejam inúteis.
4. **O limiar muda tudo.** A AUC mede só a ordenação. Para decidir, é preciso um corte, e o corte ajustado nos mesmos dados é otimista: a G-Eval vai de 0,913 a 0,872, e a METEOR de 0,900 a 0,862, quando validadas num modelo de fora.
5. **As classes são desbalanceadas** (71% incorretas). Uma métrica que reprovasse tudo teria 71% de acurácia sem saber nada. Por isso a acurácia balanceada, que nesse caso daria 50%.
6. **As métricas de LLM trazem custo e variação.** São de 20 a 63 segundos e alguns centavos por resposta, e a nota muda entre execuções. As tradicionais rodam em milissegundos, de graça e sempre iguais.

---

## Parte 7 — O que você pode concluir e o que não pode

| Pode afirmar | Não pode afirmar |
|---|---|
| O RAG aumentou muito o acerto (5,8% → 51,7%), nos três modelos (p < 0,001 em cada) | Que um modelo é melhor que outro (diferenças não significativas) |
| O efeito do RAG foi muito maior que a diferença entre os modelos | Que 51,7% é o acerto esperado para perguntas novas (há regras ajustadas ao gabarito) |
| O ganho depende do tipo: listas curtas transformam, listas longas continuam difíceis | Que as diferenças entre tipos são significativas (não houve teste; células pequenas) |
| A recuperação é necessária e não suficiente (60–70% × 9–10%) | Que todo erro é de recuperação (30–40% erram mesmo com a evidência) |
| Lexicais simples empataram com a G-Eval em separar certo de errado, a custo zero | Que lexicais são melhores em geral (é próprio deste domínio) |
| Relevância e fidelidade não medem correção | Que relevância e fidelidade são inúteis (medem outra coisa) |
| Métricas com AUC parecida erram de jeitos diferentes; o limiar e o tipo de erro importam | Que existe uma métrica vencedora absoluta |
| O RAG reduziu omissões e aumentou respostas sustentadas por evidência | Que o RAG eliminou alucinações (não houve contagem manual de alucinações) |

---

## Parte 8 — Autoteste

Responda em voz alta e só depois confira. Se errar, volte à parte indicada.

1. Quantas respostas, quantas certas, quantas erradas? → 240; 69; 171 (Parte 1)
2. Qual é o corte de cobertura do fato curto? E da descritiva e das listas? → 100%; 75%; 80% (2.1)
3. Por que a resposta "A equipe participou da primeira competição em 2015" é incorreta? → faltou LARC; 50% < 100% (2.3)
4. Quais métricas recebem os trechos recuperados? → só a Faithfulness (2.4)
5. O que é a AUC, em uma frase? → a chance de a métrica dar nota maior à resposta certa num par certa/errada (2.5)
6. Por que acurácia balanceada? → 71% das respostas são erradas; reprovar tudo daria 71% de acurácia (Parte 6)
7. Como funciona a validação leave-one-model-out? → calibra em 2 modelos e testa no 3º, três vezes (2.5)
8. Quantos ganhos e perdas teve o DeepSeek com RAG? → 18 e 1 (T1)
9. Como se calcula o McNemar do Claude? → 20 mudanças, todas para certa: 2 × 0,5²⁰ (T1)
10. Os 13,6% das listas longas são com RAG? → não; com RAG, 27,3% (T3)
11. Hit@5 e acerto com e sem hit? → 45–50%; 60–70% × 9–10% (T4)
12. Qual métrica tem a maior AUC? E a maior BA estratificada validada? → G-Eval 0,968; METEOR 0,891 (T5)
13. A diferença G-Eval × METEOR é significativa? → não; IC do bootstrap de −0,024 a +0,034 (T5)
14. Matriz da METEOR? → 161 / 10 / 15 / 54; especificidade 94,2% (T6)
15. Quantas erradas a Answer Relevancy aprovou? → 155 de 171 (T6)
16. Calcule o Token F1 do Exemplo A. → 5/8 e 5/10 → 0,556 (4.1)
17. Por que a METEOR funciona em português sem sinônimos? → vira comparação exata com peso na revocação, e cobrir os fatos é o que define o acerto (4.1)
18. Por que o BERTScore precisa de limiar 0,70? → sem a linha de base, até textos sem relação dão 0,55–0,60 (4.2)
19. Por que o cosseno não vê um ano errado? → 2015 e 2016 têm quase o mesmo significado no vetor (4.2)
20. Que modelo roda as métricas de LLM? Por que a nota da G-Eval é inteira? → `gpt-5-nano`; ele não fornece as probabilidades dos tokens (4.3)
21. Por que a Answer Relevancy inverte a ordem dos sistemas? → recusas e respostas genéricas são 100% relevantes (4.3 e 5.2)
22. Por que a Faithfulness dá 0,89 para todo mundo? → o modelo fica fiel ao que recebeu; o erro é omissão (4.3)
23. Por que a Hallucination só dá 0 ou 1? → um único contexto, o gabarito (4.3)
24. A G-Eval favoreceu o GPT? → não; a AUC dela é menor no GPT (0,958) (5.1)
25. A métrica só detecta se teve RAG? → não; só com RAG, METEOR 0,940 e G-Eval 0,935 (5.3)
26. Em que tipo a G-Eval ganha das lexicais? → fato curto e descritiva (5.4)
27. Por que o limiar das listas é maior nas lexicais? → listas incompletas ainda copiam muito texto (5.5)
28. Por que as lexicais empataram com a G-Eval? → domínio de entidades, régua de fatos, revocação (Parte 6)
29. O que não se pode concluir sobre os modelos? → que um é melhor (Parte 7)
30. Que erro da régua você conhece? → q40 sem RAG e q07 gabarito × livro; nenhum rótulo revisado à mão (2.3)

---

## Parte 9 — Plano para dominar este material

Encaixado no cronograma do `ROTEIRO_DEFESA.md`, seção 7. Cada sessão tem de 1h30 a 2h.

| Quando | O que estudar | Como saber que aprendeu |
|---|---|---|
| **Segunda, 09/11** | Partes 1 e 2 (o experimento e a linha de montagem) + T1 a T4 | Explicar, sem olhar, como uma resposta vira "certa" ou "errada" usando os Exemplos A e B. Dar os números de T1 a T4 |
| **Terça, 10/11** | Parte 4 (as 15 métricas) | Calcular à mão o Token F1, o ROUGE-2 e a METEOR do Exemplo A. Explicar cada métrica em uma frase |
| **Quarta, 11/11** | T5, T6 e Parte 5 (comportamento por modelo e tipo) | Explicar por que G-Eval e METEOR empatam, olhando só a tabela 5.4. Responder 5.1 a 5.3 sem olhar |
| **Quinta, 12/11** | Partes 6 e 7 + autoteste completo | Acertar pelo menos 27 das 30 perguntas da Parte 8 |
| **Sábado, 14/11** | Autoteste de novo, sorteando a ordem | 30 de 30, em voz alta |

**Técnica:** feche o material e explique em voz alta como se fosse para alguém de outro curso. Onde travar, é o ponto a rever.
