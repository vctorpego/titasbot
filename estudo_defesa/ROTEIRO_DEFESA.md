# Roteiro de Defesa — Minha parte: testes e resultados (Victor Cordeiro)

> Só a sua parte: os slides 6 a 13, o seu papel na demo e as perguntas da banca que são suas. O que o Victor Pego apresenta e responde está no `GUIA_DE_ESTUDO.md`, seção 16. A teoria e os números estão no Guia. **Os testes e as métricas em profundidade estão no `TESTES_E_METRICAS.md`; os cálculos passo a passo, o laboratório de métricas e a simulação de banca, no `ESTUDO_DETALHADO.md`.**

---

## 0. Sua parte em resumo

- **Defesa:** segunda-feira, **16/11/2026**, presencial, **20 minutos** no total, com a demo dentro.
- **Você:** slides **6 a 13** (testes e resultados), cerca de **10 minutos**. Você entra por volta de 5:50 e sai por volta de 16:00.
- **Deixa para entrar:** o Pego fecha o slide 5 e passa a palavra para você (seção 3, "Sua entrada").
- **Deixa para sair:** a sua frase de passagem no fim do slide 13.
- **Na demo:** você digita as perguntas e o Pego narra. Você só fala se a resposta errar ou se a banca perguntar (seção 3, "Slide 14 e demonstração").
- **Na arguição:** você responde o que é experimento, verdade, estatística, métricas e resultados (seção 5).
- **Slides:** provavelmente não serão mais editados, então os ajustes viraram instruções de fala (seção 4).
- **Texto do TCC:** o artigo `ART_TCC.pdf`.
- [ ] **Pendente:** confirmar com o orientador se a demo conta dentro dos 20 minutos.

---

## 1. O que as melhores defesas fazem (síntese das referências)

Pesquisei guias de universidades (Carleton, McGill, Texas A&M, Penn State) e materiais brasileiros sobre defesa de TCC. Os pontos que se repetem, já aplicados ao seu caso:

1. **A banca é a plateia, e a apresentação é o ponto de partida das perguntas.** Tudo o que você mostra pode virar pergunta. Por isso, não mostre nada que você não saiba explicar (por exemplo, cada barra da Figura 7).
2. **Uma ideia por slide, com o título dizendo a conclusão** (abordagem *assertion-evidence* de Michael Alley, Penn State). Em vez de "Matrizes de Confusão", use algo como "Métricas com AUC parecida erram de jeitos diferentes". Estudos de Alley indicam que a plateia entende e lembra mais com esse formato. A seção 3 traz um título sugerido para cada slide seu.
3. **Conte uma história:** problema → lacuna → o que fizemos → o que encontramos → o que isso significa → o que falta. Seus slides já seguem esse arco; as transições faladas é que costuram tudo.
4. **Números com significado.** Não é só "51,7%", é "de 1 resposta certa em cada 17 para 1 em cada 2". Evite razões relativas ("9 vezes mais"), que o próprio artigo desaconselha por partirem de uma base minúscula.
5. **Antecipe as fragilidades e fale delas antes da banca.** Mencionar as limitações por iniciativa própria mostra maturidade e desarma a pergunta. As perguntas mais comuns em TCC são sobre a justificativa metodológica, as limitações, a relação entre objetivos e resultados e a continuidade da pesquisa.
6. **Na arguição:** ouça a pergunta inteira, peça para reformular se não entender, responda de forma curta e direta e mostre evidência (slide, número, exemplo). Se não souber, diga com honestidade ("Não trabalhamos com esse aspecto neste estudo, mas…").
7. **Ensaie em voz alta, cronometrado, várias vezes**, de preferência para alguém que não conhece o trabalho e, pelo menos uma vez, com o orientador.
8. **Em apresentação em dupla:** combinem as passagens de vez (*handoffs*). Quem sai faz uma recapitulação de uma frase e anuncia quem entra e o assunto. Quem não está falando mantém postura atenta, porque a banca olha para os dois.
9. **Plano B técnico:** PDF dos slides num pendrive e na nuvem, vídeo da demo e uma cópia impressa dos slides e do artigo para consultar durante a arguição.

Fontes ao final (seção 8).

---

## 2. Seu tempo: slides 6 a 13 (cerca de 10 minutos)

Antes de você, o Pego apresenta os slides 1 a 5 (até cerca de 5:40). Depois, ele faz o slide 14 e a demo. A estrutura completa está no Guia, seção 16.1.

| Slide | Tema | Tempo | Relógio ao terminar |
|---|---|---|---|
| — | Sua entrada, depois da deixa do Pego | 0:10 | 5:50 |
| 6 | Metodologia experimental | 1:40 | 7:30 |
| 7 | Impacto do RAG | 1:25 | 8:55 |
| 8 | Cobertura factual | 0:40 | 9:35 |
| 9 | Tipologia das consultas | 1:25 | 11:00 |
| 10 | Recuperação (Hit@5) | 1:05 | 12:05 |
| 11 | Comparação das métricas | 1:45 | 13:50 |
| 12 | Matrizes de confusão | 1:05 | 14:55 |
| 13 | Lições aprendidas + limitações (faladas) | 1:05 | 16:00 |
| — | Sua passagem de volta ao Pego | 0:10 | 16:10 |

**Use a última coluna como relógio no ensaio.** Se, ao terminar o slide 9, já tiver passado de 11:30, aplique os cortes.

As suas falas somam cerca de 1.230 palavras. Num ritmo calmo, de cerca de 130 palavras por minuto, são 9 minutos e meio de fala, mais os segundos de apontar e respirar. Cabe, mas sem folga. Por isso:

- **Cronometre no ensaio.** Se passar de 10:30, aplique os cortes ✂ abaixo, nesta ordem, até caber.
- **Não acelere para caber.** Com nervosismo, todo mundo fala mais rápido. É melhor cortar uma frase do que correr.
- **Se a demo ficar fora dos 20 minutos** (pendência da seção 0), use as falas completas, sem cortes.

**✂ Cortes de segurança (cerca de 1 minuto no total):**
1. **Slide 6:** tire os exemplos ("Por exemplo, uma pergunta de fato curto é… orientadores que já passaram pela equipe."). −10 s
2. **Slide 7:** troque os números de cada modelo por "e isso vale para os três modelos, que ficaram entre 50% e 55%". −10 s
3. **Slide 9:** tire os exemplos entre vírgulas ("como os orientadores de um ano…" e "como os 20 orientadores…"). −8 s
4. **Slide 10:** tire a frase "O padrão se repete nos três modelos." −4 s
5. **Slide 11:** no primeiro parágrafo, diga só "Comparamos 15 métricas automáticas, de três famílias: lexicais, semânticas e baseadas em LLM". −12 s
6. **Slide 8:** use a versão curta: "Com RAG, a cobertura de fatos foi de 6% a 10% para cerca de 63%. A ressalva: cobertura mede presença e não penaliza invenção." −15 s

---

## 3. Sua fala slide a slide

> **Como usar:** leia em voz alta até a ideia ficar natural, e depois **pare de ler**. Decore a **mensagem** de cada slide (a frase em negrito) e os **números**. As palavras exatas podem variar. Os colchetes indicam gestos ou para onde apontar.

### Sua entrada

**Deixa:** o Pego fecha o slide 5 com algo como "…quanto ele ajuda de fato, e como medir isso? Para mostrar como testamos, passo para o Victor Cordeiro." Combinem a frase exata no ensaio.

**Sua primeira frase (sem repetir o que ele disse):**
> "Obrigado. Para responder a essas três questões, montamos um experimento controlado."

**Enquanto ele apresenta os slides 1 a 5:** fique de frente para a banca, com postura atenta. Combinem quem passa os slides. O resumo do que ele diz está no Guia, seção 16.2, caso a banca dirija a você uma pergunta sobre essa parte.

---

### Slide 6 — Metodologia experimental

**Título sugerido:** *Testamos 40 perguntas em 3 modelos, com e sem RAG: 240 respostas*
**Mensagem:** o desenho é controlado e pareado, e a verdade vem do gabarito, não de outro LLM.

**Fala (~2 min):**
> "Partimos de **40 perguntas** do gabarito oficial da equipe, elaborado a partir do acervo. Organizamos essas perguntas em **quatro tipos**, conforme a estrutura da resposta esperada: descritivas, de fato curto, de lista curta, com até oito itens, e de lista longa. Por exemplo, uma pergunta de fato curto é 'qual era o primeiro nome da equipe?'; uma lista longa é 'liste todos os orientadores que já passaram pela equipe'.
>
> [aponte para "3 Modelos"] Cada pergunta foi enviada a **três modelos de porte intermediário**, de fornecedores diferentes: Claude Haiku 4.5, DeepSeek Chat e GPT-5 mini. E em **duas condições**: sem RAG, só com a pergunta, e com RAG, passando pelo pipeline completo do TitãsBot. São 40 vezes 3 vezes 2: [aponte para o 240] **240 respostas**.
>
> [aponte para "Critério de avaliação"] E como decidimos se uma resposta estava certa? Não usamos outro modelo de linguagem como juiz. Decompusemos cada resposta do gabarito em **fatos-chave**: nomes, anos, colocações. Depois medimos qual fração desses fatos aparece na resposta. Uma resposta de fato curto precisa conter 100% dos fatos; uma descritiva, 75%; listas, 80%. Assim cada resposta recebe um rótulo de **correta ou incorreta**, que é a nossa referência para todas as análises."

⏱ **Versão curta:** "40 perguntas do gabarito, em 4 tipos, 3 modelos intermediários e duas condições, com e sem RAG: 240 respostas. A verdade é a cobertura de fatos-chave do gabarito, com corte de 100%, 75% ou 80% conforme o tipo, e isso vira um rótulo binário."

**Transição:** "E o primeiro resultado já é bastante claro."

---

### Slide 7 — O impacto do RAG no desempenho

**Título sugerido:** *Com RAG, o acerto foi de 5,8% para 51,7%*
**Mensagem:** o efeito do RAG é grande, consistente nos três modelos e muito maior que a diferença entre eles.

**Fala (~1:40):**
> "Isso responde à primeira questão. [aponte para as barras grandes] **Sem RAG, os modelos acertaram 5,8%** das perguntas, 7 de 120. **Com RAG, 51,7%**, 62 de 120. Saímos de uma resposta certa a cada 17 para uma a cada duas.
>
> [aponte para o gráfico] E isso vale para os três: o Claude foi de 5% para 55%; o DeepSeek e o GPT-5 mini, de 5% a 7,5% para 50%. Reparem que a distância entre as barras azul e laranja é muito maior que a distância entre os modelos: **neste domínio, ter acesso à evidência pesou muito mais do que a escolha do modelo**.
>
> Como as mesmas perguntas foram usadas nas duas condições, comparamos pergunta a pergunta. No Claude, 20 perguntas passaram de erradas para certas e nenhuma fez o caminho contrário; no DeepSeek, 18 contra 1; no GPT, 18 contra 0. O teste de McNemar, próprio para esse tipo de comparação pareada, deu **p menor que 0,001** nos três.
>
> Um cuidado: a liderança do Claude, com 55%, é uma **tendência**. Com 40 perguntas, os 5 pontos de diferença entre os modelos não são estatisticamente significativos."

⏱ **Versão curta:** "Sem RAG, 5,8%; com RAG, 51,7%. Vale para os três modelos, de 20 a 18 perguntas viraram de errada para certa, quase sem perdas, com McNemar p < 0,001. A diferença entre modelos é pequena e não significativa."

**Transição:** "Mas acertar ou errar é binário. E a quantidade de informação correta?"

---

### Slide 8 — Efeito do RAG na cobertura factual

**Título sugerido:** *As respostas com RAG passaram a conter cerca de 63% dos fatos esperados*
**Mensagem:** houve ganho de completude, com a ressalva de que cobertura não detecta invenção.

**Fala (~50 s):**
> "Olhamos também a **cobertura média de fatos-chave**, que capta respostas parcialmente certas. Sem RAG, as respostas traziam entre 6% e 10% dos fatos do gabarito; com RAG, cerca de **63% a 64%**. Então, além de acertar mais, as respostas ficaram muito mais completas.
>
> [aponte para a caixa vermelha] Mas a ressalva é importante: a cobertura mede **presença**. Uma resposta pode conter todos os fatos esperados e, junto, um fato inventado, e a cobertura não penaliza isso. Por isso a lemos junto com as outras métricas."

**Transição:** "Esse ganho é igual para qualquer tipo de pergunta? Essa é a segunda questão."

---

### Slide 9 — Influência da tipologia das consultas

**Título sugerido:** *O ganho não é uniforme: listas curtas melhoram muito, listas longas seguem difíceis*
**Mensagem:** a estrutura da resposta muda o efeito do RAG, e listas longas sofrem com omissões.

**Fala (~1:40):**
> "[aponte para o heatmap] Cada linha é um sistema, modelo e condição, e cada coluna é um tipo de pergunta. Quanto mais escuro, maior o acerto.
>
> Nas **listas curtas**, como os orientadores de um ano ou as classificações de uma temporada, **nenhum modelo acertou sem RAG**, e com RAG chegaram a 59% a 82%. É onde o RAG mais transforma, porque são informações de tabela que o recuperador encontra bem.
>
> Nas **listas longas**, como os 20 orientadores ou os 191 estudantes, também partimos de zero, mas com RAG ficamos entre 18% e 45%. [aponte para o gráfico de barras] Nesse gráfico, que soma as condições com e sem RAG, fatos e listas curtas ficaram em 36% a 38%, e as listas longas em **13,6%**.
>
> Isso não quer dizer que o RAG não ajude nas listas longas: **todo acerto ali veio do RAG**. Mas ele não basta. Os itens estão espalhados por muitos trechos, o contexto não comporta todos, e a resposta fica incompleta.
>
> Como não aplicamos teste estatístico entre os tipos, e as descritivas têm só 5 perguntas, tratamos essas diferenças como **tendências**."

⏱ **Versão curta:** "Listas curtas: de 0% para até 82% com RAG. Listas longas: de 0% para no máximo 45%, 13,6% no agregado. O RAG ajuda, mas listas extensas ficam incompletas. É uma tendência, sem teste entre estratos."

**Transição:** "Para entender por que ainda sobram erros, olhamos a recuperação."

---

### Slide 10 — A recuperação como fator crítico (Hit@5)

**Título sugerido:** *Com a evidência no top-5, o acerto vai a 60–70%; sem ela, cai para 9–10%*
**Mensagem:** a recuperação é necessária, mas não suficiente.

**Fala (~1:20):**
> "Em 20 perguntas, anotamos quais evidências eram necessárias para respondê-las. O **Hit@5** indica se pelo menos um dos cinco primeiros trechos recuperados contém evidência suficiente.
>
> [aponte para o verde] Quando contém, o acerto fica entre **60% e 70%**. [aponte para o vermelho] Quando não contém, despenca para **9% a 10%**. O padrão se repete nos três modelos.
>
> Isso mostra duas coisas. A recuperação é **condição necessária**: sem a evidência, quase ninguém acerta. Mas não é **suficiente**: mesmo com a evidência, 30% a 40% das respostas ainda erram, por falha na seleção ou no uso do contexto pelo modelo.
>
> E o Hit@5 ficou entre 45% e 50%, ou seja, há espaço claro para melhorar o recuperador."

**Transição:** "Até aqui, tudo dependeu de saber se cada resposta estava certa. Isso nos leva à terceira questão: dá para medir isso automaticamente?"

---

### Slide 11 — Avaliação automática: comparação

**Título sugerido:** *G-Eval e METEOR empatam no topo; Answer Relevancy fica no nível do acaso*
**Mensagem:** famílias muito diferentes separam bem; métricas que medem outra coisa, não.

**Fala (~2 min):**
> "Essa é a contribuição metodológica do trabalho. Comparamos **15 métricas automáticas**: lexicais, como BLEU, ROUGE e METEOR, que medem sobreposição de palavras; semânticas, como o BERTScore, que medem proximidade de significado; e métricas que usam um modelo de linguagem para avaliar, do DeepEval.
>
> Tratamos cada métrica como um classificador de certo ou errado e medimos a **AUC**: a probabilidade de a métrica dar nota maior a uma resposta correta do que a uma incorreta. 0,5 é o mesmo que chutar; 1 é separação perfeita.
>
> [aponte para o topo da Figura 7] O topo é praticamente um **empate**: a **G-Eval**, baseada em LLM, com **0,968**, e o **METEOR**, uma métrica lexical de 2005, gratuita e determinística, com **0,966**. A diferença não é estatisticamente significativa.
>
> Quando escolhemos o ponto de corte e validamos num modelo que ficou de fora da calibração, o METEOR, com um limiar para cada tipo de resposta, teve a maior **acurácia balanceada**: 0,891, contra 0,875 da G-Eval.
>
> [aponte para a base do gráfico] Na base, Answer Relevancy e Faithfulness ficam perto de 0,5. **Não porque sejam inúteis, mas porque medem outra coisa**: se a resposta fala do assunto e se é fiel ao trecho recuperado. Uma resposta pode ser relevante e fiel e, mesmo assim, errar uma data."

⏱ **Versão curta:** "15 métricas tratadas como classificadores. A AUC é a chance de dar nota maior à resposta certa. G-Eval com 0,968 e METEOR com 0,966 empatam no topo. Em acurácia balanceada validada, o METEOR estratificado lidera com 0,891. Relevância e fidelidade ficam perto de 0,5 porque medem outra coisa."

**Se alguém notar que a Figura 8 do artigo mostra 0,967 para a G-Eval:** G2 da seção 5.

**Transição:** "Mas a AUC não diz que tipo de erro cada métrica comete."

---

### Slide 12 — Matrizes de confusão

**Título sugerido:** *Métricas com AUC parecida erram de jeitos diferentes*
**Mensagem:** a escolha da métrica depende de qual erro é mais caro, e no TitãsBot o caro é aprovar uma resposta errada.

**Fala (~1:20):**
> "[aponte para o METEOR] O METEOR é o mais **conservador**: especificidade de **94%**, apenas 10 respostas erradas aprovadas. Em troca, rejeita mais respostas certas, 15, porque penaliza quem diz a mesma coisa com outras palavras.
>
> [aponte para a G-Eval] A G-Eval é mais **sensível**: reconhece **82,6%** das corretas, mas aprova 14 erradas. Não há uma vencedora absoluta; depende do peso de cada erro. Num chatbot institucional, aprovar uma resposta errada sobre pessoas ou premiações é o erro mais grave.
>
> [aponte para a Answer Relevancy] E a Answer Relevancy mostra o perigo de olhar um número só: sensibilidade de 90% parece ótima, mas ela aprovou **155 das 171 respostas erradas**. Ela aprova quase tudo."

**Transição:** "Juntando tudo, ficam três lições."

---

### Slide 13 — Lições aprendidas

**Título sugerido:** *Evidência transforma, o gargalo é duplo, e custo maior não garantiu avaliação melhor*

**Fala (~50 s):**
> "**Primeira:** o acesso à evidência transforma o desempenho num domínio restrito. **Segunda:** o gargalo é duplo. A resposta falha quando a recuperação não traz a evidência ou quando o modelo não a usa bem. **Terceira:** custo e benefício. As métricas com LLM levaram em média 34 segundos por resposta, custam dinheiro e variam entre execuções. As lexicais rodam em milissegundos, de graça, sempre com o mesmo resultado, e neste domínio, cheio de nomes e datas, **empataram** com a melhor métrica de LLM. Isso não torna a G-Eval dispensável: nas respostas sobre pessoas, foi a que menos aprovou erros. Mas mostra que **custo maior, sozinho, não garantiu uma avaliação melhor**."

**Limitações, antes de passar a vez (~25 s; o slide não tem, então a fala cobre):**
> "Antes de passar a palavra, quatro limitações que delimitam esses resultados. São 40 perguntas de um único domínio. A verdade é automática, por fatos-chave, e não penaliza um fato a mais inventado. Parte da recuperação usa o próprio LLM, então o contexto varia um pouco entre os modelos. E as diferenças entre modelos e entre tipos de pergunta são tendências, sem significância estatística."

**Passagem de vez (sua fala):**
> "Com isso, passo de volta ao Victor Pego, que fecha com as conclusões e mostra o TitãsBot funcionando."

**Se a banca apontar a palavra "superaram" no slide:** seção 4, item 4.

---

### Slide 14 e demonstração: o seu papel

O Pego apresenta o slide 14 e narra a demo (as falas dele estão no Guia, seções 16.3 e 16.4). O seu papel:

1. **Durante o slide 14:** deixe o navegador aberto na demo, em outra janela, para a troca ser rápida. Fique pronto para complementar se a banca perguntar das métricas ou dos números.
2. **Na demo, você digita e ele narra.** Endereço: https://titasbot-uxzg5xqawa-uc.a.run.app. Digite as perguntas 1 e 2, nesta ordem, quando ele der a deixa ("Vamos perguntar…").

**Testes de 08/11 na versão publicada** (gerador `gpt-5-nano`):

| # | Pergunta (digite exatamente assim) | Resposta obtida | Tempo | Uso |
|---|---|---|---|---|
| 1 | Quem foram os orientadores da equipe em 2024? | Os 8 orientadores do gabarito, com fontes do livro | 46 s | **Principal** |
| 2 | Qual foi o custo da viagem da equipe para a RoboCup de 2024? | "Não encontrei informação suficiente na base para responder com segurança." | 11 s | **Principal** |
| 3 | Quem idealizou a criação da equipe? | Renato Lopes de Oliveira, com fonte (livro, p. 56) | 40 s | Reserva, se sobrar tempo |
| 4 | Em quais anos a equipe participou do Mundial RoboCup? | "2019, 2024", sem 2025 | 23 s | Só se a banca pedir para ver um erro |

As respostas podem variar, porque o modelo não é determinístico. Teste de novo na véspera e no dia.

3. **Você só fala se algo der errado ou se a banca perguntar.**

**Se a banca quiser fazer uma pergunta própria:** aceite. Se o bot acertar, ótimo. Se errar, é a sua deixa para ligar aos resultados: "Esse é exatamente o tipo de falha que medimos. Com a evidência certa entre os cinco primeiros trechos, o acerto fica entre 60% e 70%; sem ela, cai para cerca de 10%." Se for uma lista longa: "É o tipo mais difícil: mesmo com RAG, o acerto ficou em 27%."

**Se a pergunta 4 (RoboCup) aparecer:** a resposta "2019 e 2024" é fiel ao que foi recuperado, mas incompleta, porque faltou 2025. É o caso típico de fidelidade alta com correção baixa, por falha de recuperação (C4 da seção 5).

4. **O que não digitar:**

- **"Qual é o valor total captado em patrocínio…"** (pergunta 40 do gabarito). Ela responde em 0,3 s porque está fixa no código, sem busca e sem LLM (`is_known_absent_detail_question`, em `back/app/domain/intents.py`). Se a banca notar a velocidade e perguntar, a resposta expõe a regra. Use a pergunta 2 acima, que passa pelo pipeline inteiro.
- **"Qual era o primeiro nome da equipe?"** Tem atalho no código (`_known_team_alias_answer`) e é a pergunta que vazou no prompt sem RAG.
- **Listas longas** ("liste todos os estudantes", "liste todos os subgrupos"): falham, como os resultados mostram. Só use se a intenção for mostrar a limitação.

**Preparação técnica (combinem quem faz cada item):**
- **Vídeo de reserva:** grave a demo completa (perguntas 1 e 2) até sexta, 13/11, e deixe o arquivo no notebook e no pendrive, para não depender da internet. No Windows, Win+Alt+R grava a janela ativa pela Xbox Game Bar; o Clipchamp também serve.
- **Servidor frio:** o Cloud Run desliga o servidor quando ninguém usa. Em 08/11, a primeira chamada levou 30 s só para acordá-lo. Uns 5 minutos antes de começar, mande a pergunta 3 na demo para acordar o servidor e conferir que a API responde.
- **Opcional, para o dia:** deixar uma instância sempre ligada com `gcloud run services update titasbot --region us-central1 --min-instances 1` e depois voltar com `--min-instances 0`. Isso tem custo enquanto estiver ligado.
- **Créditos da OpenAI:** em setembro os créditos acabaram, e isso derruba o bot. Confira o saldo no painel da OpenAI na véspera.
- **Internet:** não confie no Wi-Fi da sala. Leve o celular com roteamento (hotspot) já testado no notebook.
- **Se nada funcionar:** "A conexão não está colaborando; gravamos esta mesma demonstração no dia 13." E rode o vídeo. Não gaste mais de 20 segundos tentando consertar.

---

## 4. Ajustes nos slides → o que fazer na fala

Como os slides provavelmente não mudam mais, cada problema virou uma instrução de fala. Se ainda der para editar, faça só os itens 1 e 4, que são os que a banca mais nota.

| # | Problema no slide | O que fazer |
|---|---|---|
| 1 | **Numeração das seções repetida:** depois de "04 \| ARQUITETURA" vêm "03 \| DESENHO EXPERIMENTAL" e "04 \| RESULTADOS GERAIS" | Nada na fala; não chame atenção para isso. Se alguém notar: "Erro de numeração nosso, obrigado." |
| 2 | **Não há slide de limitações** | Você fala as quatro limitações no fim do slide 13 (texto na seção 3). |
| 3 | **Não há objetivos** | É a parte do Pego: ele diz o objetivo no slide 4. Se a banca perguntar a você: "O objetivo geral foi avaliar o efeito do RAG nas respostas de três LLMs sobre a história dos Titãs e verificar se métricas automáticas conseguem distinguir respostas corretas de incorretas." |
| 4 | **O slide 13 diz que "métricas lexicais tradicionais superaram avaliadores neurais no controle factual"**, mas na AUC foi empate | Na fala, diga "**empataram**". Se a banca apontar a palavra: "No controle de falsos positivos, o METEOR foi de fato melhor: aprovou 10 respostas erradas, contra 14 da G-Eval, uma especificidade de 94% contra 92%. Na capacidade geral de separar certo de errado, empataram, com AUC de 0,966 contra 0,968. E nas respostas sobre pessoas, a G-Eval foi a mais segura." |
| 5 | **O slide 11 diz "melhor acurácia balanceada cruzada" para o METEOR**, o que só vale com um limiar por tipo de resposta | A fala já diz "com um limiar para cada tipo de resposta". Se perguntarem, use B7 e B8 da seção 5. |
| 6 | **O slide 11 usa ponto decimal** ("0.968"), e o resto usa vírgula | Fale com vírgula, normalmente: "zero vírgula nove seis oito". |
| 7 | **No slide 12, o "94,2%" quebra em duas linhas** | Aponte e diga "94%". |
| 8 | **O slide 8 tem o texto "[ Inserir Figura 2 ]" escondido atrás da figura** | Não aparece na projeção. Nada a fazer. |
| 9 | **Os títulos são temas, não conclusões** (por exemplo, "Matrizes de Confusão") | A **primeira frase** de cada slide é a conclusão: é a "Mensagem" em negrito na seção 3. Na prática, você fala o título que o slide não tem. |
| 10 | **O slide 7 não mostra o teste estatístico** | Já está na fala: "McNemar, p menor que 0,001 nos três". |

---

## 5. Banco de perguntas da banca (as suas)

> Só estão aqui as perguntas que são suas. As de contexto, sistema, custo, privacidade e demo, que o Pego responde, estão no Guia, seção 16.5. Leia-as uma vez para saber o básico.

> Cada item tem uma **resposta curta** (20 a 40 segundos, falada) e, quando útil, um **se insistirem**. Os números estão na seção 15 do Guia. ★ marca as perguntas mais prováveis ou mais perigosas, que você deve treinar primeiro.

### A. Desenho e metodologia

**A1 ★ Por que só 40 perguntas? É suficiente?**
> É o gabarito oficial completo, elaborado por quem conhece o acervo. Como cada pergunta passa pelas 6 condições, temos 240 observações pareadas. Para o efeito do RAG, que é grande, é suficiente: os intervalos de confiança nem se tocam (sem RAG, entre 2,9% e 11,6%; com RAG, entre 42,8% e 60,4%). Para diferenças pequenas, entre modelos ou entre tipos de pergunta, não é. Por isso essas diferenças são apresentadas como tendência.

**A2 ★ Por que esses três modelos? Por que não os mais fortes?**
> O objetivo era medir o efeito do RAG, não achar o melhor modelo. Escolhemos a faixa intermediária de cada fornecedor por dois motivos: comparar modelos equivalentes entre si e ter um custo realista para uma instituição pública. São três empresas diferentes. Um modelo maior provavelmente melhoraria pouco sem RAG, porque o limite ali é de **conhecimento**, não de capacidade: dificilmente ele viu no treino as classificações da equipe em 2019.

**A3 Comparar com o sem RAG não é óbvio? Claro que sem RAG vai mal.**
> A direção era esperada; a magnitude, não. E a magnitude é o que interessa: ela mostra quanto do desempenho vem da evidência e quanto do modelo. Além disso, o sem RAG é a linha de base que permite atribuir o ganho ao RAG, e não ao prompt ou ao modelo. O resultado também tem uma parte que não é óbvia: o RAG não elimina os erros. Mesmo com ele, quase metade das respostas falha.

**A4 ★ Por que os modelos acertaram algumas perguntas sem RAG (q01 e q02)?**
> O prompt da condição sem RAG identificava a equipe (nome, Ifes Campus Colatina e o nome antigo Asimov), para que o modelo soubesse de que equipe se tratava. "Titãs" sozinho seria ambíguo. O efeito colateral é que as perguntas 1 ("quem são os Titãs?") e 2 ("primeiro nome") ficaram respondíveis pelo próprio prompt: 6 dos 7 acertos sem RAG vêm delas. Isso **infla** a linha de base, então o ganho do RAG que reportamos é **conservador**. Excluindo essas duas perguntas, o sem RAG cai para 0,9% (1 de 114) e o com RAG fica em 50%. Se tirarmos também a pergunta 40, que com RAG é respondida por uma regra fixa (A14), o sem RAG vai a 0% (0 de 111) e o com RAG fica em 48,6%.
> *Se insistirem:* "Num próximo experimento, o ideal é uma identificação neutra da equipe no prompt, sem conteúdo que responda perguntas do gabarito."

**A5 ★ A recuperação foi idêntica para os três modelos? Por que o Hit@5 varia?**
> O índice, os embeddings, o algoritmo de busca e os pesos são idênticos. Mas o pipeline do TitãsBot usa o próprio LLM em duas etapas da recuperação: gerar variações da consulta e selecionar os trechos mais úteis. Então o contexto final varia um pouco entre os modelos, e por isso o Hit@5 foi 45% no Claude e 50% nos outros. Avaliamos o sistema como ele funciona de verdade, modelo mais pipeline. Um experimento com recuperação congelada, com os mesmos trechos para todos, isolaria só o gerador; fica como trabalho futuro.

**A6 Por que estratificar por tipo de resposta e não pelas categorias temáticas?**
> Duas razões. Algumas das 8 categorias têm 1 ou 2 perguntas, o que não sustenta análise. E o comportamento das métricas muda com o **formato**: métricas lexicais penalizam respostas curtas parafraseadas e favorecem listas copiadas. O tipo de resposta é o que realmente muda a avaliação.

**A7 ★ Os cortes de 100%, 75% e 80% não são arbitrários?**
> Foram definidos *a priori*, conforme a exigência de cada formato. Um fato curto tem de 1 a 3 fatos e faltar um muda a resposta, então exige 100%. Uma descritiva tem por volta de 4 fatos e admite uma omissão, daí 75%. Listas toleram até 20% de omissão: é exigente sem pedir perfeição numa lista de 191 nomes. Não foram otimizados nos dados. E reportamos também a cobertura contínua: as boas métricas têm correlação de Spearman de ~0,83 com ela, o que mostra que a conclusão não depende do corte exato.

**A8 ★ Como os fatos-chave foram construídos? Quem validou?**
> Cada resposta do gabarito oficial foi decomposta manualmente em fatos-chave, como nomes, datas e colocações, e revisada. Há três tipos de fato: termos, que aceitam alternativas; nomes, em que basta o primeiro nome e um sobrenome; e colocações, que exigem modalidade, posição e competição no mesmo trecho. Há testes automatizados: por exemplo, cada gabarito tem de cobrir 100% dos próprios fatos, e uma colocação de outro ano não conta como acerto.

**A9 ★ Os rótulos de correto e incorreto foram conferidos por humanos?**
> Os **fatos-chave** foram curados por humanos; a **aplicação** às 240 respostas é automática e determinística, o que dá reprodutibilidade. O sistema permite corrigir rótulos manualmente, mas na rodada final nenhum foi alterado. Conhecemos erros residuais. Por exemplo, na pergunta sobre o valor do patrocínio, cuja resposta certa é dizer que não há informação, uma resposta que dizia isso com outra redação não foi reconhecida. São poucos casos e entram como ruído para todas as métricas. O próximo passo é uma rotulagem humana independente, com dois anotadores e medida de concordância (kappa).

**A10 ★★ A verdade é baseada em presença de termos. Isso não favorece as métricas lexicais?**
> É uma pergunta pertinente, e reconhecemos o risco. Três pontos. Primeiro, a verdade não compara n-gramas com o texto inteiro do gabarito: ela verifica a presença de **fatos específicos**, com tolerância a variações (sinônimos de colocação, nomes sem o nome do meio, siglas). Ou seja, ela verifica conteúdo, não estilo. Segundo, a G-Eval, que é semântica e não conta palavras, chegou à **mesma AUC** (0,968), o que indica que a separação reflete o conteúdo das respostas. Terceiro, neste domínio, estar correto **é**, em grande parte, conter os nomes, anos e colocações certos. Mesmo assim, por isso afirmamos que o resultado não se generaliza para tarefas com mais paráfrase, e a rotulagem humana é o próximo passo.

**A11 E se a resposta tiver todos os fatos e mais um inventado?**
> Ela seria marcada como correta, porque a cobertura mede presença e não penaliza o excesso. É uma limitação declarada no artigo. Por isso o rótulo é tratado como referência operacional, e as métricas de alucinação e de fidelidade estão no estudo justamente para olhar essa outra dimensão.

**A12 ★ Por que não usar um LLM como juiz para definir a verdade? Ou avaliação humana?**
> Usar um LLM para definir a verdade e depois avaliar métricas de LLM contra ela seria circular, e foi orientação do orientador evitar isso. A avaliação humana completa, de 240 respostas, algumas com 191 nomes, é cara e também subjetiva. A cobertura de fatos-chave é o meio-termo: o critério é humano (os fatos foram curados), a aplicação é automática e o processo é auditável.

**A13 As respostas são reprodutíveis?**
> Cada resposta foi gerada uma vez e armazenada em arquivo, e toda a avaliação roda sobre esse arquivo congelado. Então as métricas tradicionais são 100% reprodutíveis sobre as mesmas respostas. Regerar as respostas pode mudar algumas, porque a temperatura 0 não vale para todos os modelos (a família GPT-5 não aceita esse parâmetro) e o pipeline tem etapas com LLM. As métricas com LLM variam mesmo sobre a mesma resposta: medimos isso repetindo 3 vezes, e a G-Eval teve desvio médio de 0,056, com variação de até 0,4 na mesma resposta.

**A14 ★★ O sistema foi ajustado olhando para o gabarito? Isso não infla os 51,7%?**
> Em parte, sim, e é melhor dizer isso com clareza. O gabarito é o conjunto oficial de perguntas da equipe, e o sistema tem regras para perguntas recorrentes. O exemplo mais direto é a pergunta 40, sobre o valor total do patrocínio: o código reconhece essa frase e responde que não há informação, sem busca e sem LLM. Por isso, os 51,7% são uma estimativa **otimista** para perguntas novas. Mas isso não muda as duas conclusões principais. O efeito do RAG continua enorme: sem as perguntas 1, 2 e 40, vai de 0% para 48,6%. E a avaliação das métricas não depende de como as respostas foram produzidas, porque as métricas são comparadas com os rótulos das mesmas 240 respostas.
> *Se insistirem:* "O próximo passo é um teste cego: perguntas novas, escritas por quem não desenvolveu o sistema."
> **[CONFIRME COM O PEGO]** como as regras foram criadas durante o desenvolvimento, para responder com segurança se a banca perguntar.

**A15 ★ A pergunta 7 diz que a primeira competição foi a LARC. Não foi o TRUFES?**
> Boa observação. O livro da equipe, na seção "A primeira competição", registra o II TRUFES, em junho de 2015, e o gabarito oficial diz LARC. Usamos o gabarito sem alterá-lo. A resposta do Claude com RAG seguiu o livro e foi marcada incorreta: é um erro da referência, não do sistema. Afeta 1 resposta de 240 e não muda nenhuma conclusão, mas mostra por que o próximo passo é uma rotulagem humana independente.

### B. Estatística

**B1 ★★ O que é a AUC? Explique de forma simples.**
> Pegue uma resposta correta e uma incorreta ao acaso. A AUC é a probabilidade de a métrica dar nota maior para a correta. Com 0,5, ela não distingue nada; com 1, separa perfeitamente. O METEOR tem 0,966: em 96,6% desses pares ele coloca a correta na frente. A AUC olha todos os limiares possíveis de uma vez, ou seja, mede a capacidade de **ordenar**, não uma decisão concreta.

**B2 ★ Por que acurácia balanceada e não acurácia?**
> Porque as classes são desbalanceadas: 71% das respostas são incorretas. Uma métrica que reprovasse tudo teria 71% de acurácia sem saber nada. A acurácia balanceada é a média entre o acerto nas corretas (sensibilidade) e nas incorretas (especificidade). Nesse caso extremo, daria 50%, que é o acaso.

**B3 ★★ O que é a validação *leave-one-model-out* e por que usá-la?**
> Escolher o limiar e medir o desempenho nos mesmos dados é otimista, porque o limiar se ajusta aos dados. Então calibramos o limiar com as respostas de dois modelos e aplicamos no terceiro, que a calibração nunca viu, e repetimos trocando o modelo de fora. Isso testa se a régua funciona para um gerador novo, que é o cenário real: amanhã o TitãsBot pode trocar de modelo. O efeito aparece nos números: a G-Eval vai de 0,913 dentro da amostra para 0,872 validada com limiar global, ou 0,875 com limiar por tipo, que é o número citado no artigo (seção 5.3).
> *Se insistirem nas limitações:* "São só 3 dobras, e as perguntas se repetem entre treino e teste. A validação testa a troca de modelo, não perguntas novas."

**B4 ★ Por que o teste de McNemar? Como se calcula?**
> Porque os dados são binários e **pareados**: a mesma pergunta, com e sem RAG. As perguntas que não mudaram não informam nada; só contam as que mudaram. Se o RAG não fizesse diferença, mudar para certa ou para errada teria a mesma chance, 50%. No Claude, foram 20 mudanças, todas para certa: a chance disso por acaso é 2 × 0,5²⁰, cerca de 2 em um milhão. Usamos a versão exata, binomial, porque as contagens são pequenas.

**B5 ★ Os resultados são estatisticamente significativos?**
> O efeito do RAG, sim, com folga: p < 0,001 em cada modelo, e os intervalos de confiança não se sobrepõem. A diferença **entre modelos** com RAG, não: os testes pareados dão p de 0,69 a 1,0. Por isso falamos em tendência quando dizemos que o Claude liderou.

**B6 ★ A diferença entre G-Eval (0,968) e METEOR (0,966) é significativa?**
> Não. Fizemos um bootstrap reamostrando as perguntas, e o intervalo de 95% da diferença vai de −0,024 a +0,034, ou seja, contém o zero. Na prática é um empate, e por isso o slide diz "empate".

**B7 ★ Por que o METEOR aparece com 0,891 no slide 11 e com 86,2% na matriz do slide 12?**
> São duas versões da mesma validação. 0,891 é com um limiar diferente para cada tipo de resposta (estratificado). A matriz do slide usa um limiar único (global), que dá 86,2%. A matriz estratificada do METEOR seria de 156 VN, 15 FP, 9 FN e 60 VP.

**B8 Na tabela, o ROUGE-2 tem acurácia balanceada global maior que o METEOR. Por que o METEOR é o "melhor"?**
> O critério principal, definido no método, era a acurácia balanceada **estratificada** validada, em que o METEOR lidera (0,891). Na versão global, ROUGE-2 (0,882), BERTScore (0,880) e G-Eval (0,872) ficam à frente do METEOR (0,862). Mas as diferenças de 1 a 2 pontos entre as melhores estão dentro do ruído para 240 respostas. A conclusão robusta não é "o METEOR é o melhor"; é que **várias métricas simples empatam com a melhor métrica de LLM**.

**B9 O limiar estratificado ajudou?**
> Em parte. Melhorou a maioria das métricas validadas (o METEOR foi de 0,862 para 0,891; o ROUGE-1, de 0,833 para 0,889), mas piorou algumas (ROUGE-2, BERTScore, BLEU). Ajuda quando a métrica se comporta de forma bem diferente entre listas e respostas curtas; com poucos dados por estrato, também pode sobreajustar.

**B10 Por que a Faithfulness tem outro *n*?**
> Ela só se aplica com RAG, porque precisa dos trechos recuperados. Foram 117 respostas: as 3 respostas com RAG da pergunta 40 não tinham trechos, porque essa pergunta é respondida por uma regra antes da busca (A14). Por isso a AUC dela não é diretamente comparável às outras, que têm 240.

### C. Métricas

**C1 ★★ Por que o METEOR funcionou tão bem, se o dicionário de sinônimos dele é em inglês?**
> Em português, os sinônimos e radicais do WordNet praticamente não funcionam, e o METEOR vira uma comparação de palavras exatas, com **peso maior na revocação** e uma penalidade quando a ordem se fragmenta. E é exatamente isso que importa aqui: estar correto, neste domínio, é **cobrir** os nomes, anos e colocações da referência (revocação), e listas corretas tendem a seguir a ordem das tabelas. Ou seja, o METEOR mede algo muito próximo do que define uma resposta certa neste corpus. O chrF, que também prioriza revocação e lida melhor com a flexão do português, ficou logo atrás.

**C2 ★ Como funciona a G-Eval? Qual LLM?**
> Damos um critério em linguagem natural: penalizar fatos ausentes, anos errados e invenções, e aceitar paráfrases. O LLM gera passos de avaliação e dá uma nota de 0 a 10, comparando a resposta com a esperada. O LLM de apoio foi o `gpt-5-nano`. Como esse modelo não expõe as probabilidades dos tokens, a nota é inteira (0; 0,1; …; 1), sem a ponderação do artigo original. E ela não é determinística: repetindo a mesma avaliação, a nota variou em média 0,056.

**C3 ★★ Por que a Answer Relevancy foi tão mal?**
> Porque ela não usa o gabarito. Ela só verifica se as frases da resposta tratam do assunto da pergunta. Uma resposta errada, mas sobre o assunto, ganha nota máxima, e uma recusa como "não encontrei informação" também ganha 1,0, porque não tem nenhuma frase irrelevante. Exemplo real: sem RAG, o GPT-5 mini respondeu às classificações de 2019 com uma pergunta de volta e sugestões de onde procurar, e levou relevância 1,0. Respostas sem RAG, 95% erradas, tiveram relevância média de 0,97. No nível dos sistemas, ela ordenou ao contrário da verdade.

**C4 ★ Uma resposta pode ser fiel e estar errada?**
> Pode, e o artigo diz isso na seção 5.3: uma resposta pode ser relevante e fiel ao contexto recuperado e ainda conter um nome, uma data ou um resultado incorreto. Fidelidade é "não contradiz o que foi recuperado"; correção é "contém o que o gabarito pede". Exemplo real: na pergunta sobre os anos da RoboCup, os trechos recuperados só tinham 2019 e 2024, e a resposta trouxe exatamente isso. Foi fiel ao contexto, com Faithfulness 1,0, mas incompleta, porque faltou 2025. A falha veio da recuperação, não da geração.

**C5 Por que a métrica de alucinação ficou com AUC tão baixa?**
> Usamos o gabarito como contexto, e com um único contexto ela vira uma pergunta de sim ou não: "a resposta contradiz o gabarito?". Ela não detecta **omissão**. Uma resposta com 2 de 10 itens, sem contradizer nada, ganha nota máxima. Além disso, foi a mais instável: a mesma resposta chegou a mudar de 0 para 1 entre execuções.

**C6 ★ Afinal, qual métrica vocês recomendam para o TitãsBot?**
> Uma combinação. Para monitoramento contínuo e barato: METEOR ou chrF com limiar por tipo de resposta, como filtro (determinístico, gratuito, alta especificidade). Para auditoria por amostragem, sobretudo em respostas sobre pessoas: G-Eval, que aprovou apenas 1 de 50 respostas erradas sobre pessoas. E revisão humana nos casos de maior impacto. Nenhuma métrica deve ser árbitro único.

**C7 ★ O avaliador ser um GPT não favorece o GPT-5 mini?**
> É um risco conhecido, o viés de autopreferência. Verificamos nos dados: com RAG, a média da G-Eval foi 0,500 no Claude, 0,510 no GPT e 0,532 no DeepSeek. O GPT não ficou à frente. Mesmo assim, uma replicação com outro LLM de apoio é trabalho futuro.

**C8 O que é a métrica `ref_projeto`?**
> É a fórmula do projeto de referência indicado pelo orientador: 0,8 × similaridade semântica (cosseno MiniLM) + 0,2 × similaridade de caracteres. Incluímos para comparar diretamente com esse projeto. Ela ficou no meio do ranking (AUC 0,920), abaixo das lexicais. Os pesos 80/20 vêm da justificativa conceitual do projeto original, não de calibração.

**C9 Por que o BERTScore precisa de limiar 0,70?**
> Rodamos sem o reescalonamento pela linha de base, então até textos sem relação ficam por volta de 0,55 a 0,60. A faixa útil fica comprimida no alto, e o corte ótimo ficou em 0,70.

### D. Sistema (só o que cai nos resultados)

**D5 ★ Por que as listas longas falham? Como resolver?**
> Os itens ficam espalhados em muitos trechos, e o contexto leva no máximo 8. Uma lista de 20 orientadores ou 191 estudantes não cabe nem é recuperada inteira. Soluções: aumentar o número de trechos conforme o tipo de pergunta, fazer chunking por linha de tabela, usar recuperação iterativa e, principalmente, consultar as tabelas como dado estruturado, em vez de texto.

**D6 ★ O sistema tem regras fixas no código?**
> Sim, algumas regras de domínio para casos recorrentes. Por exemplo, a pergunta sobre o primeiro nome da equipe tem um atalho que responde "Asimov" **se** um trecho recuperado contiver esse nome, e a lista de estudantes é extraída das tabelas de forma determinística. A evidência continua vindo da recuperação. Há também uma regra para dados que sabemos que não estão no acervo, como o valor total captado em patrocínio (pergunta 40): o sistema responde direto que não encontrou a informação, sem busca. Nas três respostas com RAG da pergunta 40, foi essa regra que respondeu. Para o experimento, isso significa que nessas perguntas a resposta com RAG praticamente não depende do modelo, o que é bom saber ao comparar modelos (e ver A14).

### E. Resultados, contribuição e futuro

**E1 ★★ Qual é a contribuição do trabalho?**
> Duas, articuladas. Primeiro, medir, de forma pareada e com três modelos, o efeito real do RAG num domínio institucional pequeno e especializado, mostrando onde ele ajuda (listas curtas, fatos) e onde não basta (listas longas, falhas de recuperação). Segundo, avaliar criticamente os próprios **instrumentos de medida**: métricas simples e gratuitas empatam com a melhor métrica de LLM, e métricas populares de RAG, como relevância e fidelidade, não medem correção. Além disso, há o artefato: o TitãsBot está funcionando e publicado.

**E2 ★ Os resultados se generalizam?**
> O efeito do RAG em domínios locais deve se generalizar: é o mesmo argumento de Lewis et al., e o tamanho do efeito é grande. Já a boa performance das métricas lexicais é **própria deste domínio**, cheio de entidades. Em tarefas com mais paráfrase, como respostas explicativas longas, a vantagem relativa das métricas semânticas e de LLM tende a crescer.

**E3 ★ O que vocês fariam diferente?**
> Três coisas: um prompt sem RAG neutro, sem pistas que respondam perguntas do gabarito; uma rotulagem humana dupla em paralelo à automática; e uma condição com recuperação congelada, para isolar o gerador. Também anotaríamos as evidências das 40 perguntas, não só de 20.

**E4 Quais trabalhos futuros concretos?**
> Reranking com cross-encoder; chunking por estrutura das tabelas; número de trechos adaptativo por tipo de pergunta; extração estruturada para listas longas; ablação dos componentes do pipeline; ampliar o gabarito; e replicar a meta-avaliação com outros LLMs de apoio e com passos de avaliação fixos na G-Eval.

**E5 ★ A Figura 4 diz que as listas longas têm 13,6%. Isso é com RAG?**
> Não. A Figura 4 soma as seis configurações, com e sem RAG. Só com RAG, as listas longas ficam em 27,3% e as listas curtas em 72,5%, que é o melhor estrato com recuperação, como diz o Resumo. No agregado, o fato curto aparece na frente (38,1%) porque teve alguns acertos sem RAG.

**E6 ★ Por que o DeepSeek com RAG zerou nas descritivas (Figura 3)?**
> São só 5 perguntas por célula, então um ou dois casos mudam muito a taxa, e o próprio artigo pede cautela. As descritivas pedem uma síntese de cerca de 4 fatos, com corte de 75%: faltar um fato reprova. Exemplo: em "Quem são os Titãs?", o DeepSeek com RAG trouxe detalhes do contexto, como o nome Asimov e a chamada do CNPq, mas omitiu dois dos quatro fatos esperados. Sem RAG, ele tinha acertado essa pergunta por causa da identificação da equipe no prompt (A4).

**E7 ★ Vocês concluem que o RAG mitiga alucinações. Mediram alucinação diretamente?**
> De forma indireta. Sem RAG, os modelos ou recusavam ou inventavam detalhes; por exemplo, um deles sugeriu competições que a equipe nunca disputou. Com RAG, a cobertura de fatos foi de ~8% para ~63%, e a métrica de não contradição com o gabarito subiu em média de 0,58 para 0,75. Mas é justo dizer que não fizemos uma contagem manual de alucinações. A formulação mais precisa é: **o RAG reduz omissões e aumenta as respostas sustentadas por evidência**.

**E8 Por que o DeepSeek piorou numa pergunta com RAG?**
> Foi a pergunta 1, "Quem são os Titãs?". Sem RAG, a resposta genérica citava estudantes, orientadores e competições. Com RAG, trouxe detalhes do contexto (o nome Asimov, a chamada do CNPq) e omitiu dois dos quatro fatos esperados. Ficou com 50% de cobertura, abaixo do corte de 75%. Mais informação recuperada não garante cobrir o que a pergunta pede.

### F. Perguntas conceituais rápidas (respostas de uma frase)

- **O que é um LLM?** Um modelo Transformer treinado em muito texto para prever o próximo token, capaz de gerar linguagem.
- **O que é um embedding?** Um vetor numérico que representa o significado de um texto, no qual textos parecidos ficam próximos.
- **O que é alucinação?** Uma resposta fluente e plausível, mas sem suporte factual.
- **O que é RAG em uma frase?** Buscar trechos relevantes num acervo e entregá-los ao modelo para que ele responda com base neles.
- **O que é self-attention?** O mecanismo em que cada token pondera a importância de todos os outros para construir sua representação.
- **O que é BM25?** Um ranking por palavras-chave que valoriza termos raros e normaliza pelo tamanho do documento.
- **Precisão × revocação?** Precisão: do que aprovei, quanto estava certo. Revocação: do que estava certo, quanto aprovei.
- **O que é um falso positivo aqui?** A métrica aprovar uma resposta errada, o erro mais perigoso num chatbot institucional.

### G. Perguntas sobre o texto do artigo

**G1 O artigo cita a Tabela 4, mas ela não existe.**
> Erro de numeração nosso: a referência é à Tabela 3, que tem a AUC de 0,520 da Answer Relevancy. As tabelas são 1, 2, 3 e 5.

**G2 ★ A Tabela 3 dá 0,968 para a G-Eval, e a Figura 8 dá 0,967. Qual é o certo?**
> O valor exato é 0,96745. Com três casas, é 0,967, como na figura. O 0,968 veio de arredondar duas vezes. Não muda a conclusão: a METEOR tem 0,966, e a diferença não é significativa.

**G3 O cabeçalho de algumas páginas diz "MNR 2019".**
> É uma sobra do modelo do evento; o artigo é da MNR 2026.

**G4 ★ Qual LLM avaliou nas métricas de LLM? O artigo não diz.**
> O `gpt-5-nano`, pelo DeepEval. É uma informação que faltou no texto. Ver C2 e C7.

**G5 ★ As conclusões quase não falam de limitações.**
> As limitações estão distribuídas no texto: a cobertura não penaliza fato extra (4.1), as descritivas têm só 5 perguntas, não houve teste entre estratos e o Hit@5 cobre só o subconjunto anotado (5.2), e o bom desempenho das lexicais é próprio deste corpus (5.3). Eu acrescentaria duas: o tamanho da amostra, de 40 perguntas, e a verdade automática sem rotulagem humana independente.

**G6 Quantas perguntas tinham evidências anotadas? O artigo diz só "subconjunto".**
> Vinte das quarenta.

**G7 ★ O que a Figura 5 mostra? E a Figura 6? E a 8?**
> Use as explicações do Guia, seção 10. Em uma frase cada. A Figura 5 mostra que o limiar muda a acurácia balanceada e que cada métrica tem seu ponto ideal. A Figura 6 mostra que as lexicais têm AUC alta em milissegundos, enquanto as de LLM levam dezenas de segundos. A Figura 8 mostra as curvas ROC longe da diagonal do acaso: famílias diferentes ordenam as respostas de forma parecida.

**G8 Por que o artigo não traz intervalos de confiança?**
> O artigo priorizou a magnitude das diferenças e as transições pareadas, e diz isso na seção 4.2: o valor de p não foi usado isoladamente. Calculamos os intervalos depois. Sem RAG, de 2,9% a 11,6%; com RAG, de 42,8% a 60,4%. Eles nem se tocam.

**G9 O que é a "métrica de referência específica do projeto" da seção 4.2?**
> É a `ref_projeto`, 0,8 × cosseno MiniLM + 0,2 × similaridade de caracteres. É a fórmula de um projeto anterior indicado pelo orientador, replicada para comparação; não fomos nós que criamos. Ficou com AUC de 0,920. Ver C8.

---

## 6. Técnica de resposta na arguição

**Estrutura em 4 tempos (cerca de 30 segundos):**
1. **Acolher:** "Boa pergunta." Ou reformule: "Se entendi bem, a pergunta é se…" Isso ganha 3 segundos para pensar e confirma o que foi perguntado.
2. **Responder primeiro, explicar depois:** a primeira frase é a resposta ("Sim, em parte" / "Não, porque…").
3. **Evidência:** um número, um exemplo ou um slide ("No slide 10, quando a evidência estava no top-5…").
4. **Fechar:** ligue a resposta a uma limitação ou a um trabalho futuro, se couber, e pare de falar.

**Frases-ponte úteis:**
- "Isso aparece nos dados de forma clara: …"
- "Reconhecemos essa limitação, e ela tem um efeito específico: …"
- "Essa é uma decisão de projeto; o motivo foi…"
- "Não trabalhamos com esse aspecto neste estudo, mas a forma como abordaríamos é…"
- "Se a banca permitir, o Victor Pego complementa a parte do sistema." (passar a vez quando a pergunta é da parte do outro)

**O que não fazer:**
- Não discutir com a banca. Se discordar, argumente com dados e com calma.
- Não inventar um número. É melhor "não tenho esse valor de cabeça, mas a ordem de grandeza é…" ou "está na Tabela 3 do artigo".
- Não responder uma pergunta diferente da que foi feita.
- Não fazer uma resposta longa demais. Se a banca quiser mais, ela pede.
- Não interromper o colega. Combine um sinal para "posso complementar?".

**Dupla:** você responde as seções A, B, C, D (D5 e D6), E e G desta lista, além de qualquer erro que aparecer na demo. Perguntas de contexto, Titãs, fundamentos, sistema, custo, privacidade e demo são do Pego. As respostas dele estão no Guia, seção 16.5, para você saber o básico e complementar se ele pedir. Combinem um sinal discreto para "posso complementar?", como um leve aceno. Quem responde olha para quem perguntou, não para o colega.

---

## 7. Plano de estudo: de 08/11 a 16/11

> A lógica é **entender → lembrar → explicar → ser questionado**. Use **recordação ativa** (feche o material e tente explicar) e a **técnica de Feynman** (explique como para alguém leigo). Reler sem testar a memória rende pouco. Cada dia tem de 2 a 3 horas. Se o dia apertar, faça só os itens marcados com ★.

### Domingo, 08/11 — Hoje (~1 h)
- [ ] ★ Guia, seções 1 a 3: a história do trabalho.
- [ ] ★ Contar o trabalho em 1 minuto, em voz alta, sem olhar.

### Segunda, 09/11 — Desenho e resultados
- [ ] ★ `TESTES_E_METRICAS.md`, Partes 1 e 2 e testes T1 a T4. Explicar, sem olhar, como uma resposta vira "certa" ou "errada" com os Exemplos A e B.
- [ ] Guia, seções 6 e 9: desenho experimental e todos os números.
- [ ] ★ Cola de números (Guia, seção 15): ler, fechar e escrever de memória o bloco RQ1.
- [ ] ★ Ler o artigo do TCC (`ART_TCC.pdf`) do começo ao fim, com o Guia, seção 2, ao lado.
- [ ] Assistir ao vídeo do artigo (youtu.be/ZZMSgk9U9S0).

### Terça, 10/11 — Métricas
- [ ] ★ `TESTES_E_METRICAS.md`, Parte 4: as 15 métricas. Calcular à mão o Token F1, o ROUGE-2 e a METEOR do Exemplo A.
- [ ] ★ Responder em voz alta C1 a C9 (seção 5 deste roteiro).
- [ ] Ensaio 1: sua parte inteira, **lendo** as falas, cronometrada. Anote o tempo de cada slide.

### Quarta, 11/11 — Meta-avaliação e estatística
- [ ] ★ `TESTES_E_METRICAS.md`, testes T5 e T6 e Parte 5 (comportamento por modelo e por tipo). Guia, seção 8, como apoio.
- [ ] ★ `ESTUDO_DETALHADO.md`, seções 2 a 4: como cada número foi calculado, como comparar métricas diferentes e o laboratório.
- [ ] ★ Explicar sem olhar: AUC (a frase do sorteio), acurácia balanceada (o exemplo do "sempre incorreta"), leave-one-model-out e McNemar (o cálculo do Claude).
- [ ] Calcular à mão a especificidade, a sensibilidade e a BA do METEOR a partir da matriz.
- [ ] ★ Responder em voz alta B1 a B10.
- [ ] Ensaio 2: sua parte **sem ler**. Grave em vídeo e assista.

### Quinta, 12/11 — Fundamentos, sistema e figuras do artigo
- [ ] ★ `TESTES_E_METRICAS.md`, Partes 6 e 7 e o autoteste da Parte 8. Meta: 27 de 30.
- [ ] Guia, seção 4: explicar "o que é RAG" e "por que busca híbrida" como para um leigo.
- [ ] Guia, seção 5, com o código aberto: desenhar de memória o pipeline de 14 passos.
- [ ] ★ Guia, seções 2.3, 2.4 e 10: o que vem só do código, os detalhes de forma e as figuras que não estão nos slides (5, 6 e 8). Responder G1 a G9, E5 e E6.
- [ ] ★ Com o Pego: rodar a demo inteira (seção 3) e combinar quem digita e quem fala. Conferir para onde aponta o QR do slide 14 (vídeo do artigo ou demo).

### Sexta, 13/11 — Pontos sensíveis e ensaio em dupla
- [ ] ★ Guia, seção 12, e as perguntas ★★ da seção 5 (A10, A14, B1, B3, C1, C3, E1).
- [ ] ★ **Gravar o vídeo de reserva da demo.**
- [ ] ★ Ensaio 3: apresentação completa em dupla, com passagens de vez, demo e cronômetro. Meta: entre 19 e 20 minutos.

### Sábado, 14/11 — Simulação de banca
- [ ] ★ Ensaio 4: com o orientador ou colegas no papel de banca. Peça perguntas difíceis.
- [ ] ★ Simulação de arguição: alguém sorteia 15 perguntas da seção 5 e você responde em até 40 segundos cada. Marque as que travaram.
- [ ] Revisar as perguntas que travaram.
- [ ] Autoteste do `TESTES_E_METRICAS.md` (Parte 8) em ordem sorteada. Meta: 30 de 30.
- [ ] ★ Simulação de banca do `ESTUDO_DETALHADO.md` (seção 6), com as réplicas, em voz alta.

### Domingo, 15/11 — Véspera (leve)
- [ ] Um único ensaio completo, sem parar para corrigir.
- [ ] Revisar a cola de números e as perguntas ★★.
- [ ] Testar a demo (perguntas 1 e 2) e conferir os créditos da OpenAI.
- [ ] Separar o material do checklist abaixo e imprimir o que for impresso.
- [ ] Parar de estudar no começo da noite e dormir cedo. O sono consolida o que você estudou; virar a noite piora a lembrança no dia seguinte.

### Segunda, 16/11 — Dia da defesa
- [ ] 20 minutos de revisão da cola de números, e só.
- [ ] Seguir o checklist abaixo.

**Texto do TCC:** o `ART_TCC.pdf` é a referência. Se aparecer uma monografia separada, me mande que eu cruzo com o Guia.

### Checklist do dia (presencial)

**Separar na véspera:**
- [ ] Notebook carregado, com o carregador.
- [ ] Adaptador para o projetor da sala (HDMI ou outro). Pergunte antes ao orientador qual é a conexão.
- [ ] Passador de slides com pilha nova, se tiver.
- [ ] PDF dos slides no notebook, num pendrive e na nuvem.
- [ ] Vídeo da demo no notebook e no pendrive.
- [ ] Celular carregado, com o roteamento (hotspot) já testado no notebook.
- [ ] Impressos para consultar na arguição: cola de números (Guia, seção 15), as matrizes do slide 12, a tabela de AUC e BA e o artigo do TCC impresso, com as tabelas marcadas.
- [ ] Caneta e papel para anotar as perguntas da banca.
- [ ] Água.

**Na sala, 30 minutos antes:**
- [ ] Testar o projetor e o passador. Abrir o PDF em tela cheia e passar todos os slides uma vez, conferindo se as figuras e o QR aparecem.
- [ ] Testar a internet e abrir a demo numa aba. Uns 5 minutos antes, mandar a pergunta 3 para acordar o servidor.
- [ ] Celular no silencioso.
- [ ] Combinar com o Pego o sinal de "posso complementar?" e onde cada um fica.

**Durante:**
- [ ] Fale para a banca, não para a tela. Olhe a tela só para apontar.
- [ ] Quando o Pego estiver falando, fique de frente para a banca e atento: a banca olha os dois.
- [ ] Anote cada pergunta antes de responder. Isso evita esquecer partes de perguntas longas.
- [ ] Respire. A banca quer ver o que vocês aprenderam, não reprovar.

---

## 8. Fontes consultadas sobre apresentação e defesa

- [Five tips for presenting and defending your PhD thesis — Universidade Católica Portuguesa](https://fd.porto.ucp.pt/en/node/27226)
- [Ph.D. Defense — Procedure and Advice — Carleton University (Physics)](https://physics.carleton.ca/node/233)
- [Hints for PhD defenses — McGill University](https://mcgill.ca/caps/files/caps/acw2012_hintsforphddefenses.pdf)
- [Dissertation Defense — Texas A&M Writing Center](https://writingcenter.tamu.edu/guides/resources/dissertation-defense.html)
- [Thesis defense: how to ace this crucial step — Researcher.Life](https://researcher.life/blog/article/thesis-defense-how-to-ace-this-crucial-step/)
- [Tips for a Thesis Defense Presentation — TalTech (Medium)](https://medium.com/taltech-blog/tips-for-a-thesis-defense-presentation-a4990e244c9a)
- [Como se preparar para a defesa do TCC — Na Prática](https://napratica.org.br/noticias/como-se-preparar-para-a-defesa-do-tcc)
- [Perguntas mais comuns da banca — Doutora Nathalia](https://doutoranathalia.com.br/blog/perguntas-mais-comuns-da-banca/)
- [Perguntas da Banca de TCC: as mais frequentes — Tesify](https://tesify.pt/perguntas-banca-tcc-mais-frequentes-como-responder-2026/)
- [Scientific Presentations / Assertion-Evidence — Michael Alley, Penn State](https://writing.engr.psu.edu/research.html)
- [Rethinking Slide Design: The Assertion-Evidence Approach — Penn State Huck Institutes](https://www.huck.psu.edu/event/rethinking-slide-design-in-scientific-presentation-the-assertion-evidence-approach-1)
- [Power Point Slide Design — iBiology (Michael Alley)](https://www.ibiology.org/professional-development/power-point-slide-design/)
- [Team Presentation Theory: The Five Formats — UT Arlington](https://www.uta.edu/academics/schools-colleges/business/news-and-events/releases/2024/08/21/five-formats)
- [3 keys to transition speakers in group presentations — Brainzooming](https://www.brainzooming.com/blog/3-keys-to-transition-speakers-in-group-presentations)
- Documentação do DeepEval (como cada métrica calcula): [G-Eval](https://deepeval.com/docs/metrics-llm-evals) · [Answer Relevancy](https://deepeval.com/docs/metrics-answer-relevancy) · [Faithfulness](https://deepeval.com/docs/metrics-faithfulness) · [Hallucination](https://deepeval.com/docs/metrics-hallucination)
