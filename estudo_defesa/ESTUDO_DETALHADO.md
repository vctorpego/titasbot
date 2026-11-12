# Estudo detalhado — como chegamos aos resultados e simulação de banca

> Complemento do `TESTES_E_METRICAS.md`. Lá está **o que** cada teste e cada métrica mostram; aqui está **como** cada número foi calculado, **como** se comparam métricas que medem coisas diferentes e um **laboratório** com respostas controladas. No fim, há uma **simulação de banca e do orientador**, com réplicas e tréplicas. Todos os cálculos foram refeitos nos dados do projeto em 10/11/2026.

---

## 1. Do zero ao número: o caminho de uma resposta

Para entender o estudo inteiro, siga **uma** resposta do começo ao fim. Vamos usar o Exemplo A: q07, GPT-5 mini, com RAG.

### Passo 1 — A pergunta entra no sistema
"Em que ano a equipe participou da primeira competição?" passa pelo pipeline do TitãsBot. Ele expande a consulta, faz a busca híbrida, o modelo escolhe os trechos, gera a resposta e a audita.

### Passo 2 — O que foi recuperado (teste T4)
Para a q07, os termos de evidência anotados são **"2015" e "LARC"**. Um trecho é "relevante" se tem pelo menos 1 desses termos e "suficiente" se tem os 2.
- Nos 5 primeiros trechos do GPT, 2 eram relevantes (Precision@5 = 2/5 = 0,40), mas **nenhum era suficiente**: **Hit@5 = 0**.
- O trecho principal era a página 61 do livro, que fala da estreia em 2015, no TRUFES.

### Passo 3 — A resposta gerada
"A equipe participou da primeira competição em 2015."

### Passo 4 — A régua (verdade)
- Fatos-chave da q07: {2015} e {LARC}. A resposta tem 2015 e não tem LARC: cobertura = 1/2 = **50%**.
- Fato curto exige 100%. Rótulo = **0 (incorreta)**.
- Coerente com o T4: sem a evidência no top-5, a resposta saiu incompleta.

### Passo 5 — As 15 notas
METEOR 0,455 · G-Eval 0,5 · ROUGE-L 0,556 · Token F1 0,556 · BLEU 0,068 · chrF 0,501 · Cosseno 0,766 · BERTScore 0,843 · ref_projeto 0,749 · Answer Relevancy 1,0 · Faithfulness 1,0 · Hallucination (inv.) 1,0 · Exact Match 0.

### Passo 6 — A decisão de cada métrica
Cada métrica compara a sua nota com o seu limiar. A METEOR (limiar 0,35) e a G-Eval (limiar 0,40) **aprovam** essa resposta: é um **falso positivo** de cada uma. O BLEU (limiar 0,10) reprova, por acaso do jeito como ele pune respostas curtas.

### Passo 7 — Como essa resposta entra nos resultados
- **No T1:** é 1 das 58 respostas incorretas com RAG.
- **Na AUC:** ela é uma das 171 incorretas. Entra em 69 pares (contra cada resposta correta) e "perde" para toda correta com nota maior que a dela.
- **Na matriz:** soma 1 no FP da METEOR e 1 no FP da G-Eval.

> **Frase para guardar:** cada resposta gera um rótulo (pela régua) e 15 notas (pelas métricas). Todo o estudo das métricas é comparar as 15 notas com esse rótulo, nas 240 respostas.

---

## 2. Como cada número foi calculado

### 2.1 Taxa de acerto e diferença (T1)
- Taxa = corretas ÷ 40 por sistema. No total com RAG: 62/120 = 51,7%. Sem RAG: 7/120 = 5,8%.
- **Diferença absoluta** em pontos percentuais: 51,7 − 5,8 = +45,8 p.p.
- **Por que não "9 vezes mais"?** Porque a razão parte de uma base minúscula (5,8%) e exagera o efeito. O artigo usa a diferença absoluta.

### 2.2 McNemar exato (T1)

Para cada modelo, monta-se uma tabela 2 × 2 com as mesmas 40 perguntas:

| | Com RAG certa | Com RAG errada |
|---|---|---|
| **Sem RAG certa** | não mudou | **perda (c)** |
| **Sem RAG errada** | **ganho (b)** | não mudou |

Só importam as perguntas que **mudaram** (b + c). Se o RAG não fizesse diferença, cada mudança teria 50% de chance de ser ganho ou perda, como uma moeda.

- **Claude:** b = 20, c = 0 → p = 2 × 0,5²⁰ = **1,91 × 10⁻⁶**
- **DeepSeek:** b = 18, c = 1 → p = 2 × (1 + 19) ÷ 2¹⁹ = 40 ÷ 524.288 = **7,63 × 10⁻⁵**
- **GPT-5 mini:** b = 18, c = 0 → p = 2 × 0,5¹⁸ = **7,63 × 10⁻⁶**
- **[CÁLCULO COMPLEMENTAR] Juntando os três:** 56 ganhos e 1 perda → p ≈ 8 × 10⁻¹⁶

O "2 ×" vem do teste **bicaudal**: ele considera tanto um excesso de ganhos quanto um excesso de perdas. A versão **exata** (binomial) foi usada porque as contagens são pequenas; a versão qui-quadrado é uma aproximação para contagens grandes.

### 2.3 Intervalo de confiança de Wilson [CÁLCULO COMPLEMENTAR]

Para uma proporção p = k/n, com z = 1,96 (95%):

```
centro    = (p + z²/2n) ÷ (1 + z²/n)
meia-largura = z · √( p(1−p)/n + z²/4n² ) ÷ (1 + z²/n)
```

- **Com RAG (62/120):** p = 0,517 → centro 0,516, meia-largura 0,088 → **[42,8%; 60,4%]**
- **Sem RAG (7/120):** **[2,9%; 11,6%]**

**Por que Wilson e não "p ± 1,96 × erro"?** Porque a fórmula simples falha com proporções perto de 0, e 5,8% está perto de 0: o intervalo poderia até ficar negativo. O de Wilson é o recomendado para isso.

### 2.4 Cobertura média (T2)
Média, por sistema, da cobertura de cada resposta (de 0 a 1). Ela não tem corte: capta acertos parciais. Exemplo: a resposta A tem cobertura 0,5 e soma 0,5 na média, embora seja "incorreta" no rótulo.

### 2.5 Hit@5 e acerto condicional (T4)

Contagens nas 20 perguntas anotadas:

| Modelo | Respostas com Hit = 1 | Corretas entre elas | Respostas com Hit = 0 | Corretas entre elas |
|---|---|---|---|---|
| Claude | 9 | 6 (66,7%) | 11 | 1 (9,1%) |
| DeepSeek | 10 | 7 (70%) | 10 | 1 (10%) |
| GPT-5 mini | 10 | 6 (60%) | 10 | 1 (10%) |

**Por que top-5?** São os trechos mais bem posicionados entre os até 8 do contexto. É uma medida padrão de recuperação e fácil de explicar.

### 2.6 AUC (T5): o cálculo por pares

**Exemplo de brinquedo:** 3 respostas certas com notas 0,9, 0,6 e 0,4; 3 erradas com 0,5, 0,3 e 0,1. São 3 × 3 = 9 pares (certa, errada):
- 0,9 vence as 3 erradas → 3
- 0,6 vence as 3 → 3
- 0,4 vence 0,3 e 0,1, mas perde para 0,5 → 2

AUC = 8/9 = **0,889**. Empate vale meio ponto.

**No estudo:** são 69 × 171 = **11.799 pares**.
- METEOR: AUC 0,9657 → vence cerca de **11.394** pares.
- G-Eval: AUC 0,9675 → cerca de **11.415** pares, contando os empates como meio.
- A diferença é de uns 20 pares em quase 12 mil. Por isso é **empate**.

**Ligação com o teste de Mann-Whitney:** essa contagem é exatamente a estatística U de Mann-Whitney dividida pelo número de pares. É assim que o código calcula (`roc_auc` em `meta_evaluation.py`).

### 2.7 A escolha do limiar: a varredura (T5)

O código testa 21 cortes (0,00 a 1,00, de 0,05 em 0,05) e fica com o de **maior acurácia balanceada**. Varredura da METEOR nas 240 respostas:

| Limiar | VP | FP | VN | FN | Sensibilidade | Especificidade | BA |
|---|---|---|---|---|---|---|---|
| 0,20 | 67 | 47 | 124 | 2 | 0,971 | 0,725 | 0,848 |
| 0,25 | 64 | 32 | 139 | 5 | 0,928 | 0,813 | 0,870 |
| 0,30 | 63 | 23 | 148 | 6 | 0,913 | 0,865 | 0,889 |
| **0,35** | **62** | **17** | **154** | **7** | **0,899** | **0,901** | **0,900** |
| 0,40 | 58 | 10 | 161 | 11 | 0,841 | 0,942 | 0,891 |
| 0,50 | 55 | 8 | 163 | 14 | 0,797 | 0,953 | 0,875 |
| 0,60 | 52 | 3 | 168 | 17 | 0,754 | 0,982 | 0,868 |
| 0,70 | 46 | 3 | 168 | 23 | 0,667 | 0,982 | 0,825 |

**Como ler:** subir o limiar troca falsos positivos por falsos negativos. Em 0,35, sensibilidade e especificidade se equilibram em 0,90. Quem quiser um avaliador mais rigoroso, que quase não aprove resposta errada, pode subir para 0,55: são só 4 FP, ao custo de 16 FN.

**Detalhe da G-Eval:** como a nota é inteira (0; 0,1; 0,2; …), os limiares 0,35 e 0,40 dão o mesmo resultado (BA 0,913). No empate, o código escolhe o mais perto de 0,5, que é 0,40.

### 2.8 Validação leave-one-model-out, dobra por dobra (T5 e T6)

Calibra-se o limiar com as 160 respostas de dois modelos e aplica-se nas 80 do terceiro.

**METEOR, limiar global:**

| Modelo deixado de fora | Limiar aprendido nos outros dois | VP | FP | VN | FN | BA na dobra |
|---|---|---|---|---|---|---|
| Claude | 0,55 | 17 | 1 | 55 | 7 | 0,845 |
| DeepSeek | 0,35 | 20 | 5 | 52 | 3 | 0,891 |
| GPT-5 mini | 0,40 | 17 | 4 | 54 | 5 | 0,852 |
| **Soma (matriz do slide 12)** | | **54** | **10** | **161** | **15** | **0,862** |

**G-Eval, limiar global:** 0,50 (Claude fora), 0,40 e 0,40. Soma: VP 57, FP 14, VN 157, FN 12 → BA 0,872.

**Por que a BA validada é menor que a de dentro da amostra (0,900)?** Porque o limiar **muda** conforme os dados de calibração: na METEOR, foi de 0,35 a 0,55. Quando o limiar aprendido em dois modelos não serve tão bem ao terceiro, a decisão piora. Isso mede o que acontece na vida real: calibrar hoje e usar amanhã com outro modelo.

**Com limiar por tipo (estratificado),** a METEOR deixando o Claude de fora sobe de 0,845 para 0,935. Na soma das três dobras: VP 60, FP 15, VN 156, FN 9 → **BA 0,891**.

### 2.9 Acurácia balanceada a partir da matriz

```
BA = (sensibilidade + especificidade) ÷ 2
METEOR: (54/69 + 161/171) ÷ 2 = (0,783 + 0,942) ÷ 2 = 0,862
G-Eval: (57/69 + 157/171) ÷ 2 = (0,826 + 0,918) ÷ 2 = 0,872
Relevancy: (62/69 + 16/171) ÷ 2 = (0,899 + 0,094) ÷ 2 = 0,496
```

**O exemplo do "reprovar tudo":** VP = 0 e VN = 171 → acurácia 171/240 = 71%, mas BA = (0 + 1) ÷ 2 = 50%. A BA desmascara o classificador que não sabe nada.

### 2.10 Bootstrap da diferença de AUC [CÁLCULO COMPLEMENTAR]

1. Sorteia 40 perguntas **com reposição** entre as 40 (algumas repetem, outras ficam de fora), levando as 6 respostas de cada pergunta sorteada.
2. Recalcula a AUC da G-Eval e da METEOR nessa amostra e guarda a diferença.
3. Repete muitas vezes e pega o intervalo entre os percentis 2,5% e 97,5%.

Resultado: **[−0,024; +0,034]**. Como o zero está dentro, a diferença não é significativa.

**Por que reamostrar perguntas e não respostas?** Porque as 6 respostas de uma mesma pergunta não são independentes: uma pergunta difícil é difícil para todos. Reamostrar perguntas respeita isso.

### 2.11 Spearman com a cobertura e Kendall entre sistemas
- **Spearman:** correlação de postos entre a nota da métrica e a cobertura contínua de cada resposta. Mostra se a métrica acompanha **o quanto** a resposta está completa, não só certo × errado. METEOR 0,83, G-Eval 0,84, ROUGE-L 0,84; Answer Relevancy −0,03 (nenhuma relação).
- **Kendall entre sistemas:** ordena os 6 sistemas pela nota média e pela taxa real e mede a concordância. METEOR 0,93 (acerta a ordem); Answer Relevancy −0,79 (ordem invertida).

---

## 3. Como comparar métricas que avaliam de formas diferentes

Esta é a pergunta metodológica mais importante da sua parte. Domine este capítulo.

### 3.1 O problema
As 15 métricas são diferentes em quase tudo:

| Diferença | Exemplos |
|---|---|
| **Escala** | BLEU fica quase sempre entre 0 e 0,4; BERTScore entre 0,55 e 1; G-Eval anda de 0,1 em 0,1; Hallucination só dá 0 ou 1 |
| **Unidade que comparam** | palavras, sequências de palavras, caracteres, vetores de frase, vetores de palavra, julgamento de um LLM |
| **Referência que usam** | gabarito (a maioria), só a pergunta (Answer Relevancy), os trechos recuperados (Faithfulness) |
| **O que querem medir** | parecença de texto, de sentido, correção, relevância, fidelidade, contradição |

Comparar "0,46 da METEOR" com "0,5 da G-Eval" diretamente não faz sentido: são réguas diferentes.

### 3.2 A solução: cinco decisões de desenho

1. **Mesma tarefa para todas:** decidir se a resposta está **correta ou incorreta**. É a tarefa de que o mantenedor do TitãsBot precisa.
2. **Mesma referência, independente das métricas:** o rótulo vem dos fatos-chave curados por humanos. Nenhuma métrica participa da construção da verdade. É por isso que não usamos um LLM como juiz para criar a verdade: seria circular.
3. **Mesmas 240 respostas para todas:** a comparação é pareada. Diferenças entre métricas não podem vir de respostas diferentes.
4. **Medidas que não dependem da escala:**
   - a **AUC** só olha a **ordem** das notas, não o valor (seção 3.3);
   - cada métrica ganha o **seu próprio limiar**, escolhido do mesmo jeito para todas.
5. **Mesma validação para todas:** limiar aprendido em dois modelos e testado no terceiro.

E mais quatro eixos práticos, medidos igualmente para todas: **tempo, custo, estabilidade** entre execuções e **erros sobre pessoas**.

### 3.3 Por que a AUC permite comparar escalas diferentes
A AUC só pergunta "a certa ficou na frente da errada?". Qualquer transformação que preserve a ordem (multiplicar, elevar ao quadrado, somar uma constante) não muda a AUC.

**Exemplo:** se o BERTScore (que vive entre 0,6 e 0,9) e o BLEU (que vive entre 0 e 0,4) ordenassem as 240 respostas exatamente na mesma sequência, os dois teriam **a mesma AUC**, apesar das escalas totalmente diferentes. Por isso a AUC é a moeda comum do estudo.

### 3.4 Por que cada métrica tem o seu limiar
Usar 0,5 para todas seria injusto: o BLEU quase nunca chega a 0,5 (reprovaria tudo), e o BERTScore quase sempre passa de 0,5 (aprovaria tudo). Cada métrica recebe o corte que **ela** precisa para decidir melhor, escolhido pelo mesmo critério (maior BA) e validado do mesmo jeito.

### 3.5 É justo comparar Answer Relevancy e Faithfulness com correção?
É justo **perguntar** se elas servem para detectar correção, porque em ferramentas de RAG elas costumam ser apresentadas como "qualidade da resposta". A resposta do estudo é: **não servem para isso**. Não é que sejam ruins; elas medem outra coisa, e o artigo diz isso explicitamente.

O uso certo delas:
- **Faithfulness:** detectar se o gerador inventou algo **contra** os trechos;
- **Answer Relevancy:** detectar respostas fora do assunto.

São complementos, não substitutos de uma métrica de correção.

### 3.6 Como cada métrica "enxerga" uma resposta

| Métrica | Compara | Usa | Pesa mais | Ordem importa? | Vê paráfrase? | Vê fato trocado? | Vê omissão? | Determinística? |
|---|---|---|---|---|---|---|---|---|
| Exact Match | texto inteiro | gabarito | igualdade | sim | não | sim | sim | sim |
| Token F1 | palavras | gabarito | equilíbrio P/R | não | pouco | pouco | sim | sim |
| BLEU-4 | sequências de 1–4 palavras | gabarito | precisão | sim | não | pouco | pela brevidade | sim |
| ROUGE-1/2/L | palavras, pares, subsequência | gabarito | F | 2 e L: sim | pouco | pouco | sim | sim |
| METEOR | palavras alinhadas | gabarito | **revocação** | sim (fragmentação) | pouco | pouco | **sim** | sim |
| chrF | sequências de caracteres | gabarito | **revocação** | não | um pouco (flexão) | pouco | sim | sim |
| Cosseno MiniLM | vetor da frase | gabarito | sentido geral | pouco | **sim** | **não** | pouco | sim |
| BERTScore | vetor de cada palavra | gabarito | sentido por palavra | pouco | **sim** | **não** | pouco | sim |
| ref_projeto | 80% cosseno + 20% caracteres | gabarito | sentido geral | pouco | sim | não | pouco | sim |
| G-Eval | julgamento do LLM | pergunta + gabarito | critério escrito | — | **sim** | **sim** | parcial | **não** |
| Answer Relevancy | afirmações × pergunta | só a pergunta | assunto | — | — | **não** | **não** | não |
| Faithfulness | afirmações × trechos | trechos | não contradizer o contexto | — | — | só contra os trechos | **não** | não |
| Hallucination | resposta × gabarito | gabarito | contradição | — | — | **sim** | **não** | não |

As colunas "vê fato trocado" e "vê omissão" vêm do laboratório da seção 4.

### 3.7 O que significa "uma métrica é melhor que outra" neste estudo
Significa: **neste domínio e com esta régua**, ela ordena e decide melhor quais respostas estão certas, validada num modelo que ela não viu. **Não** significa que ela seja melhor em qualquer tarefa. O artigo diz isso na seção 5.3.

---

## 4. Laboratório: oito respostas controladas para a mesma pergunta

Para ver **como cada métrica reage** a cada tipo de erro, rodamos o código do projeto em oito variações de resposta à q07. Gabarito: *"A equipe competiu pela primeira vez em 2015 na LARC."*

**[CÁLCULO COMPLEMENTAR]** Feito em 10/11/2026. As tradicionais são determinísticas. As de LLM (G-Eval, Hallucination e Answer Relevancy, com `gpt-5-nano`) foram rodadas **uma vez**, e numa nova execução podem variar um pouco. A Faithfulness não entra porque precisa de trechos recuperados.

| Variante | Rótulo da régua | Token F1 | BLEU | ROUGE-L | METEOR | chrF | Cosseno | BERTScore | G-Eval | Halluc. (inv.) | Relevancy |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Idêntica ao gabarito | ✓ correta | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 | 1,0 | 1 | 1,0 |
| Paráfrase: "A estreia da equipe em competições foi na LARC, no ano de 2015." | ✓ correta | 0,52 | 0,04 | 0,43 | 0,41 | 0,39 | 0,96 | 0,83 | 1,0 | 1 | 1,0 |
| Curta: "2015, na LARC." | ✓ correta | 0,46 | 0,05 | 0,46 | 0,32 | 0,20 | 0,72 | 0,73 | 0,5 | 1 | 0,5 |
| Fato extra inventado: "… em 2015 na LARC, onde ficou em 1º lugar." | ✓ correta | 0,80 | 0,63 | 0,80 | 0,94 | 0,96 | 0,93 | 0,93 | 1,0 | 1 | 0,5 |
| Falta um fato: "… pela primeira vez em 2015." | ✗ incorreta | 0,89 | 0,78 | 0,89 | 0,82 | 0,86 | 0,80 | 0,93 | 0,6 | 1 | 1,0 |
| Ano trocado: "… em 2016 na LARC." | ✗ incorreta | 0,90 | 0,71 | 0,90 | 0,90 | 0,91 | 0,85 | 1,00 | 0,2 | 0 | 1,0 |
| Competição trocada: "… em 2015 na OBR." | ✗ incorreta | 0,90 | 0,88 | 0,90 | 0,90 | 0,90 | 0,67 | 0,97 | 0,4 | 0 | 1,0 |
| Recusa: "Não encontrei informação suficiente…" | ✗ incorreta | 0,10 | 0,02 | 0,10 | 0,05 | 0,14 | 0,00 | 0,66 | 0,2 | 1 | 0,0 |

### O que o laboratório ensina

1. **As tradicionais não percebem a troca de um fato.** "Ano trocado", "competição trocada" e "falta um fato" mudam uma palavra e levam de 0,80 a 1,00. Ganham nota **maior** que a paráfrase correta (0,40–0,50). O BERTScore dá 1,00 para o ano trocado.
2. **Então por que a AUC delas foi tão alta no estudo?** Porque, nas 240 respostas reais, os erros quase nunca são uma troca sutil de uma palavra. São **recusas, listas incompletas e respostas longas e genéricas**, muito diferentes do gabarito. As tradicionais separam bem esse tipo de erro. **A AUC alta reflete o perfil de erro deste conjunto.** Num sistema que errasse trocando datas sutilmente, elas iriam muito pior. É mais um motivo para não generalizar o resultado das lexicais.
3. **O cosseno vê o sentido, não o detalhe.** Dá 0,96 à paráfrase (ótimo), mas 0,85 ao ano trocado. Só a troca de competição o fez cair (0,67).
4. **A G-Eval é a única que acerta quase tudo:** 1,0 para a paráfrase, 0,2 para o ano trocado. Mas:
   - deu **0,6 à resposta com um fato faltando** (aprovaria com o limiar 0,40);
   - deu **0,4 à competição trocada**, exatamente no limiar (aprovaria);
   - deu **1,0 ao fato extra inventado**: o critério mandava não penalizar detalhes compatíveis, e "1º lugar" parecia compatível.
5. **A Hallucination pega contradição, e só ela.** Zerou o ano e a competição trocados, mas deu 1 à omissão, ao fato inventado extra e à recusa.
6. **A Answer Relevancy mede assunto.** Deu 1,0 a todas as erradas que falam de "primeira competição em ano X". Nesta execução, deu 0 à recusa; no estudo, recusas muitas vezes ganharam nota alta, o que mostra a variação entre execuções.
7. **A régua também tem ponto cego:** a resposta com fato extra inventado é "correta" para ela, porque tem todos os fatos-chave. É a limitação declarada no artigo, seção 4.1.

> **Frase para a banca:** "Num teste controlado, as métricas lexicais deram nota quase máxima a uma resposta com o ano trocado. Elas funcionaram bem no nosso estudo porque os erros reais eram principalmente omissões e recusas, não trocas sutis. Por isso afirmamos que o resultado é próprio deste domínio e deste perfil de erro."

---

## 5. Decisões de desenho e por que foram tomadas

| Decisão | Alternativa | Por que escolhemos assim |
|---|---|---|
| Comparação pareada (mesmas perguntas nas 6 condições) | Grupos diferentes de perguntas | Controla a dificuldade da pergunta; permite o McNemar |
| McNemar **exato** | Qui-quadrado de McNemar | Contagens pequenas (até 20 mudanças) |
| Diferença absoluta (p.p.) | Razão ("9 vezes") | A razão exagera quando a base é pequena |
| Wilson para os intervalos | Intervalo normal (Wald) | Wald falha perto de 0% |
| Verdade por fatos-chave | LLM como juiz ou avaliação humana completa | Juiz LLM seria circular; humano completo é caro e subjetivo |
| Cortes 100/75/80% definidos antes | Cortes otimizados nos dados | Evita ajustar a régua ao resultado |
| Tipos pela estrutura da resposta | As 8 categorias temáticas | Algumas categorias têm 1–2 perguntas; o formato é o que muda as métricas |
| AUC como medida principal de separação | Acurácia | Independe de limiar e de escala |
| Acurácia balanceada para escolher o limiar | Acurácia ou F1 | 71% das respostas são incorretas |
| Varredura de 0 a 1, de 0,05 em 0,05 | Busca contínua | Simples, transparente e igual para todas |
| Empate de limiar → mais perto de 0,5 | Menor ou maior limiar | Regra neutra, definida antes |
| Limiar por tipo só com ≥ 6 respostas e as duas classes | Sempre por tipo | Evita limiar sem base |
| Leave-one-model-out | k-fold por pergunta | Simula trocar o gerador, que é o cenário real |
| Bootstrap por pergunta | Por resposta | Respostas da mesma pergunta não são independentes |
| Hit@5 com termos de evidência | MRR, nDCG | Simples, binário, ligado direto ao acerto |
| Respostas geradas uma vez e congeladas | Gerar de novo a cada análise | Reprodutibilidade das métricas |

---

## 6. Simulação de banca e do orientador

> **Como treinar:** leia a pergunta, feche o texto, responda em voz alta em até 40 segundos e só depois compare. As réplicas simulam o avaliador insistindo. "Evite" mostra respostas que pioram a situação. Os números de referência estão nas seções acima e no `TESTES_E_METRICAS.md`.

### 6.1 Avaliador de estatística e metodologia

**P1. "Vocês afirmam que o RAG melhorou o acerto. Como sabem que não foi sorte?"**
> Porque o desenho é pareado: as mesmas 40 perguntas com e sem RAG, em cada modelo. Pelo McNemar exato, que só olha as perguntas que mudaram, o Claude teve 20 mudanças para certa e nenhuma para errada; por acaso, isso teria chance de cerca de 2 em um milhão. Os três modelos deram p menor que 0,001, e os intervalos de confiança das duas condições nem se tocam: de 2,9% a 11,6% sem RAG e de 42,8% a 60,4% com RAG.
>
> *Réplica:* "E por que não um teste t ou qui-quadrado comum?"
> *Tréplica:* "O t é para médias de variáveis contínuas, e aqui o dado é binário. O qui-quadrado comum supõe grupos independentes, mas os nossos são pareados. O McNemar é o teste para proporções pareadas, e usamos a versão exata porque as contagens são pequenas."
>
> *Evite:* "Foi muito significativo." Dê os números e o raciocínio.

**P2. "Quarenta perguntas não é pouco?"**
> Para o efeito do RAG, não: ele é grande, e os intervalos não se sobrepõem. Para diferenças pequenas, sim, e por isso tratamos a diferença entre modelos e entre tipos de pergunta como tendência. Também são 240 respostas pareadas, e cada métrica foi avaliada em 11.799 pares de resposta certa contra errada.
>
> *Réplica:* "Mas a AUC calculada nesses pares não está inflada, já que as respostas de uma mesma pergunta se repetem?"
> *Tréplica:* "Por isso a incerteza da diferença entre G-Eval e METEOR foi estimada com bootstrap reamostrando perguntas, não respostas. O intervalo deu de −0,024 a +0,034, ou seja, empate."

**P3. "A acurácia balanceada validada da METEOR é 0,862 no slide 12 e 0,891 no slide 11. Qual vale?"**
> As duas. 0,862 usa um limiar único para todas as perguntas; 0,891 usa um limiar por tipo de resposta. A matriz do slide 12 é a do limiar único. O critério principal do método era a versão por tipo, e nela a METEOR lidera.

**P4. "Explique por que a validação dá um número menor que o ajuste nos dados todos."**
> Porque o limiar ajustado nos mesmos dados em que é medido se encaixa neles. Na validação, o limiar é aprendido em dois modelos e testado no terceiro. Na METEOR, o limiar aprendido variou de 0,35 a 0,55 conforme o modelo deixado de fora, e o desempenho caiu de 0,900 para 0,862. A versão validada é a estimativa honesta do que acontece ao trocar de modelo.
>
> *Réplica:* "Três dobras não é pouco?"
> *Tréplica:* "É, e reconhecemos. Ela testa a troca de gerador, não perguntas novas, porque as mesmas perguntas aparecem no treino e no teste. Com mais modelos, teríamos mais dobras."

**P5. "Por que vocês escolheram o limiar pela acurácia balanceada e não pelo F1?"**
> Porque o F1 olha só a classe positiva e é afetado pelo desbalanceamento. A acurácia balanceada pesa igualmente acertar as certas e as erradas. Com 71% de respostas erradas, isso evita premiar uma métrica que aprova pouco ou reprova tudo.

**P6. "Vocês testaram 15 métricas. Não deveriam corrigir para comparações múltiplas?"**
> Não fizemos teste de hipótese entre todas as métricas. A comparação é descritiva, por AUC e acurácia balanceada validada. O único teste formal entre métricas foi o bootstrap entre as duas primeiras, que deu empate. Se fizéssemos testes entre todos os pares, sim, seria preciso corrigir, por exemplo com Bonferroni ou Holm. Não afirmamos que a METEOR é significativamente melhor que nenhuma das outras do topo.

**P7. "A cobertura de fatos não é contínua? Por que transformar em binário?"**
> Porque a pergunta prática é "esta resposta pode ser entregue ou não?". Mas não descartamos a versão contínua: reportamos a cobertura média (Figura 2) e a correlação das métricas com ela. As melhores têm Spearman de cerca de 0,83, o que mostra que a conclusão não depende do corte exato.

**P8. "Os cortes de 100%, 75% e 80% não favorecem algum resultado?"**
> Foram definidos antes de olhar as métricas, pela natureza de cada formato, e não foram otimizados. Faltar o único fato de uma pergunta de fato curto torna a resposta errada; numa lista de 191 nomes, exigir 100% seria irreal. E, como a correlação com a cobertura contínua é alta, mudar o corte um pouco não muda o ranking das métricas.

### 6.2 Avaliador de IA e PLN

**P9. "Como uma métrica de 2005, que conta palavras, empata com um LLM?"**
> Porque, neste domínio, estar certo é conter os nomes, anos e colocações do gabarito, e a METEOR pesa justamente a revocação, ou seja, quanto do gabarito aparece na resposta. Além disso, os erros reais do nosso conjunto são principalmente omissões e recusas, que ficam muito longe do gabarito.
>
> *Réplica:* "Então a METEOR detectaria uma data trocada?"
> *Tréplica:* "Não. No nosso teste controlado, uma resposta com o ano trocado levou 0,90 na METEOR, e a G-Eval deu 0,2. As lexicais funcionaram aqui por causa do perfil de erro deste conjunto. Por isso não generalizamos: em tarefas com erros sutis ou muita paráfrase, a avaliação por LLM tende a ser necessária."
>
> *Evite:* "A METEOR é melhor que a G-Eval." Não é o que os dados dizem.

**P10. "O WordNet da METEOR é em inglês. Ela não fica quebrada em português?"**
> Fica sem os sinônimos e os radicais, e vira uma comparação de palavras exatas com peso na revocação e penalidade por fragmentação. Isso, por coincidência, é o que interessa aqui. Uma adaptação para português, com sinônimos e radicais da língua, é um trabalho futuro possível. O chrF, que lida melhor com a flexão do português, ficou logo atrás.

**P11. "Por que vocês não usaram o BERTScore com o reescalonamento pela linha de base?"**
> Usamos a configuração padrão, sem ele. Isso comprime a escala: até textos sem relação ficam perto de 0,6, e o limiar ótimo ficou em 0,70. Para a AUC, isso não faz diferença, porque o reescalonamento é linear e não muda a ordem das notas. Só muda o valor do limiar.

**P12. "A G-Eval original usa as probabilidades dos tokens. Vocês usaram?"**
> Não. O `gpt-5-nano` não fornece essas probabilidades, então a nota é inteira, de 0 a 10. A consequência é uma escala mais grossa: na varredura, os limiares 0,35 e 0,40 dão o mesmo resultado. Mesmo assim, ela teve a maior AUC.
>
> *Réplica:* "E por que um modelo tão pequeno como avaliador?"
> *Tréplica:* "Custo e consistência com as fases anteriores do projeto. As quatro métricas de LLM custaram US$ 1,88 nas 240 respostas. Um avaliador maior provavelmente melhoraria a G-Eval, e isso é um trabalho futuro. Mas, pelo nosso resultado, o ganho teria de pagar um custo que as lexicais não têm."

**P13. "O avaliador é um GPT e um dos modelos avaliados é um GPT. Isso não enviesa?"**
> É um risco conhecido, e verificamos. A AUC da G-Eval foi a menor justamente no GPT-5 mini (0,958, contra 0,972 e 0,977), e a nota média dela no GPT com RAG (0,51) ficou entre a do Claude e a do DeepSeek. Não houve sinal de autopreferência. Uma replicação com um avaliador de outra empresa reforçaria isso.

**P14. "Por que a Faithfulness, tão usada em RAG, deu resultado de acaso?"**
> Porque ela mede se a resposta respeita os trechos recuperados, e o modelo quase sempre respeita: a média foi 0,89 nos três. O erro típico aqui é a omissão. Na pergunta da RoboCup, os trechos só tinham 2019 e 2024, e a resposta trouxe exatamente isso: fiel ao contexto, com nota 1,0, mas faltou 2025. A Faithfulness diz se o gerador foi fiel, não se a resposta está completa.

**P15. "A Answer Relevancy ordenou os sistemas ao contrário. Como isso é possível?"**
> Ela não usa o gabarito: só pergunta se cada frase da resposta trata do assunto da pergunta. Respostas sem RAG, como "não tenho essa informação, procure o site da equipe", são 100% sobre o assunto. Por isso os sistemas sem RAG, que erram 95%, tiveram relevância média de 0,96 a 0,99, maior que os com RAG.

**P16. "Vocês não deveriam ter usado o RAGAS?"**
> O RAGAS e o DeepEval implementam famílias de métricas parecidas, como fidelidade e relevância, e o nosso resultado sobre elas vale para as duas: medem outra coisa que não a correção. Escolhemos o DeepEval pela integração com o projeto e por ter a G-Eval. Replicar com o RAGAS é um trabalho futuro coerente.

**P17. "O que é exatamente a métrica `ref_projeto`? Vocês a criaram?"**
> Não. É a pontuação do projeto de referência indicado pelo orientador: 0,8 de cosseno MiniLM mais 0,2 da semelhança de caracteres de Ratcliff-Obershelp, o `SequenceMatcher` do Python. Incluímos como linha de base. Ela quase coincide com o cosseno (correlação de 0,987) e, mesmo com o melhor peso possível, ficaria em cerca de 0,93, abaixo da METEOR.

### 6.3 Avaliador de sistemas e engenharia

**P18. "Os 51,7% são o acerto que o usuário vai ter?"**
> Não exatamente. O sistema tem regras ajustadas a perguntas recorrentes do gabarito; a mais clara é a pergunta 40, que é respondida por uma regra fixa. Então 51,7% é otimista para perguntas novas. Mas o efeito do RAG se mantém sem as perguntas afetadas: de 0% para 48,6%. O próximo passo é um teste cego, com perguntas escritas por quem não desenvolveu o sistema.

**P19. "A recuperação é igual para os três modelos?"**
> O índice, os vetores e os pesos são iguais. Mas duas etapas da busca usam o próprio modelo gerador: a expansão da consulta e a escolha dos trechos. Por isso o Hit@5 deu 45% no Claude e 50% nos outros. Avaliamos o sistema como ele funciona. Uma condição com os mesmos trechos para todos isolaria só o gerador; é trabalho futuro.

**P20. "Se a recuperação acerta só metade das vezes, onde está o gargalo?"**
> Nos dois lados. Sem a evidência no top-5, o acerto cai para cerca de 10%, então a recuperação é necessária. Com a evidência, ainda há 30–40% de erros, então a geração também falha: escolhe mal os trechos ou omite itens. Na q07, por exemplo, os trechos tinham "2015", mas nenhum tinha "2015" e "LARC" juntos, e a resposta saiu incompleta.

**P21. "Qual métrica vocês colocariam em produção para monitorar o TitãsBot?"**
> Uma combinação. A METEOR ou o chrF, com limiar por tipo, como filtro diário: grátis, instantânea e com especificidade acima de 90%. A G-Eval por amostragem, sobretudo nas respostas sobre pessoas, em que ela aprovou indevidamente só 2% das erradas. E revisão humana nos casos de maior impacto. O limiar teria de ser recalibrado se o perfil de perguntas mudar.

**P22. "As métricas de LLM variam entre execuções. Quanto?"**
> Repetimos três vezes 36 respostas. Na G-Eval, a nota variou em média 0,056, mas chegou a variar 0,4 na mesma resposta, o que pode mudar a decisão. A Hallucination foi a pior: a mesma resposta foi de 0 a 1. As tradicionais não variam.

### 6.4 Orientador (conhece o projeto por dentro)

**P23. "Por que vocês não usaram o LLM como juiz para definir a verdade, como fizemos no começo?"**
> Porque depois íamos avaliar métricas de LLM contra uma verdade criada por um LLM, e isso seria circular: a métrica parecida com o juiz sairia favorecida. Com os fatos-chave, o critério é humano e a aplicação é automática e auditável.

**P24. "O que vocês aprenderam com o projeto de referência?"**
> Duas coisas. A ideia de tratar a nota como um classificador e varrer os limiares, que ampliamos com o limiar por tipo e a validação deixando um modelo de fora. E que a fórmula dele, apoiada no cosseno, não enxerga fatos: ficou com AUC de 0,920, abaixo das lexicais que verificam a presença dos termos do gabarito.

**P25. "E a questão sociotécnica que eu pedi?"**
> Primeiro, um cuidado: não fizemos uma avaliação sociotécnica completa, porque o sistema não foi implantado nem avaliado com usuários; organização e pessoas ficaram fora. O que medimos foram aspectos práticos de adoção das métricas, quatro coisas além da separação. **Custo:** US$ 1,88 nas métricas de LLM contra zero. **Tempo:** 34 segundos por resposta contra milissegundos. **Estabilidade:** as de LLM mudam entre execuções. **Impacto sobre pessoas:** nas 50 respostas erradas sobre alunos e orientadores, a G-Eval aprovou 1, a METEOR 6 e a Answer Relevancy 43. Em um chatbot institucional, aprovar uma informação errada sobre uma pessoa é o erro mais grave.

**P26. "A pergunta 7 está certa no gabarito?"**
> O gabarito diz LARC, mas o livro, na seção "A primeira competição", diz II TRUFES, em junho de 2015. Mantivemos o gabarito sem alterar. A resposta do Claude com RAG seguiu o livro e foi marcada errada: é um erro da referência, que afeta 1 resposta de 240. Vale corrigir o gabarito numa próxima versão.

**P27. "Se tivessem mais um mês, o que fariam?"**
> Três coisas, na ordem. Uma rotulagem humana independente, com dois anotadores e medida de concordância. Um conjunto de perguntas novas, cego para o sistema. E uma condição com a recuperação fixa para todos os modelos, para separar o efeito do gerador do da busca.

### 6.5 Perguntas-armadilha

**P28. "Então a G-Eval não vale o custo?"**
> Não foi isso que concluímos. Ela empatou na separação geral, mas foi a melhor em fatos curtos e descrições, a mais segura com pessoas e a única que pegou o ano trocado no teste controlado. O que concluímos é que custo maior, sozinho, não garantiu uma avaliação melhor neste domínio.

**P29. "Se as lexicais não pegam uma data trocada, o resultado de vocês não vale nada?"**
> Vale para o que foi medido: o desempenho delas no perfil real de erros do TitãsBot, que são omissões e recusas. O teste controlado mostra o limite. Por isso recomendamos combinar a lexical com a G-Eval por amostragem, e não usar a lexical sozinha.

**P30. "Por que o Claude é o melhor modelo?"**
> Não afirmamos isso. Ele teve 55% contra 50% dos outros, mas a diferença não é significativa (p ≥ 0,69). O resultado é que o RAG pesou muito mais que a escolha do modelo.

**P31. "O RAG elimina alucinações, certo?"**
> Não. O próprio artigo diz que o RAG não deve ser tratado como mecanismo que elimina alucinações. O que vimos é que ele reduz omissões e aumenta as respostas sustentadas por evidência. Não fizemos uma contagem manual de alucinações.

**P32. "A AUC de 0,968 quer dizer que a G-Eval acerta 96,8% das vezes?"**
> Não. Quer dizer que, num par sorteado com uma resposta certa e uma errada, ela dá nota maior à certa 96,8% das vezes. A taxa de decisões certas depende do limiar; validada, a acurácia balanceada dela foi 0,872.

**P33. "Por que a Figura 8 mostra 0,967 e o texto 0,968?"**
> O valor exato é 0,96745. Com três casas, é 0,967; o 0,968 veio de arredondar duas vezes. Não muda nada: continua empatada com a METEOR, que tem 0,966.

### 6.6 Perguntas da conversa com o orientador (10/11)

**P34 ★★. "Na Figura 5, um limiar de 0,1 ou 0,2 não está aprovando resposta que não tem similaridade nenhuma com o gabarito?"**
> O limiar está na escala de cada métrica, não em porcentagem de acerto. Quem define se a resposta está certa é a régua de fatos-chave. Uma paráfrase correta tira 0,04 no BLEU, e uma resposta com o ano trocado tira 0,90 na METEOR; então "abaixo de 0,5" não é "menos da metade correta". Testamos a restrição: com limiar mínimo de 0,5, o topo não muda (G-Eval 0,881, METEOR 0,867, chrF 0,872 validadas); só caem as métricas de escala comprimida, como o BLEU.
>
> *Réplica:* "Mas a AUC não está somando essa região de limiares que ninguém usaria?"
> *Tréplica:* "Está, e por isso calculamos a AUC parcial, só na zona com até 10% de falsos positivos (McClish, 1989). Nessa zona, chrF (0,888), METEOR (0,885) e G-Eval (0,883) continuam empatados. A conclusão se mantém onde a decisão importa."

**P35. "Por que as Figuras 5 e 8 mostram só algumas métricas?"**
> Para legibilidade. Na Figura 5, escolhemos representantes das três famílias e um contraste: METEOR e ROUGE-L (lexicais com melhores limiares diferentes), BERTScore (melhor semântica), G-Eval (melhor de LLM) e Answer Relevancy (a pior). Na Figura 8, as quatro de maior AUC mais a melhor semântica. As curvas das 15 métricas estão no material complementar.

**P36. "Dá para comparar essas métricas todas, se elas medem coisas diferentes?"**
> Só no eixo de correspondência com o gabarito existem métricas das três famílias (lexicais, semânticas e a G-Eval). Hallucination, Faithfulness e Answer Relevancy são de LLM e medem outros eixos: contradição, fidelidade ao contexto e relevância. Elas entram na comparação para responder se servem como detectores de correção; a resposta é não, porque o objetivo delas é outro.

### 6.7 Rodada relâmpago (resposta em uma frase)

1. Quantas respostas certas? → 69 de 240.
2. Corte do fato curto? → 100%.
3. Ganhos e perdas do DeepSeek? → 18 e 1.
4. O que é Hit@5? → Pelo menos um dos 5 primeiros trechos tem evidência suficiente.
5. Acerto com e sem a evidência? → 60–70% contra 9–10%.
6. Maior AUC? → G-Eval, 0,968.
7. Maior BA validada por tipo? → METEOR, 0,891.
8. Limiar da METEOR? → 0,35 global; 0,55 e 0,60 nas listas.
9. Especificidade da METEOR? → 94,2%.
10. Erradas aprovadas pela Answer Relevancy? → 155 de 171.
11. Por que a Hallucination só dá 0 ou 1? → Um único contexto, o gabarito.
12. Quanto custaram as métricas de LLM? → US$ 1,88 no total.
13. Quem avaliou nas métricas de LLM? → `gpt-5-nano`.
14. Quantas perguntas anotadas para o Hit@5? → 20.
15. Lista longa com RAG? → 27,3%.
16. O que é a ref_projeto? → 0,8 cosseno + 0,2 caracteres, do projeto de referência.
17. Pares na AUC? → 69 × 171 = 11.799.
18. Intervalo do RAG? → 42,8% a 60,4%.
19. Por que bootstrap por pergunta? → Respostas da mesma pergunta não são independentes.
20. Por que a BA validada é menor? → O limiar aprendido em dois modelos não serve tão bem ao terceiro.

---

## 7. Checklist de domínio

Marque quando conseguir fazer **sem olhar**:

- [ ] Seguir o Exemplo A do começo ao fim (seção 1).
- [ ] Calcular o McNemar dos três modelos (2.2).
- [ ] Explicar por que Wilson e não Wald (2.3).
- [ ] Calcular a AUC do exemplo de brinquedo e dizer quantos pares há no estudo (2.6).
- [ ] Ler a tabela da varredura e justificar o 0,35 da METEOR (2.7).
- [ ] Explicar por que a BA validada cai, com os limiares das dobras (2.8).
- [ ] Calcular a BA da METEOR, da G-Eval e da Relevancy pela matriz (2.9).
- [ ] Explicar as cinco decisões que permitem comparar métricas diferentes (3.2).
- [ ] Explicar por que a AUC não depende da escala (3.3).
- [ ] Contar o que o laboratório mostrou sobre o ano trocado (seção 4).
- [ ] Responder P1, P9, P18, P28 e P34 com as réplicas.
