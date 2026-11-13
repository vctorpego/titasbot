# Otimização do tempo de resposta — noite de 11/11/2026

Trabalho feito enquanto você dormia: medir onde o tempo ia, descobrir por que
as respostas estavam grandes, corrigir e validar. Tudo commitado na `main` e
publicado em <https://titasbot.duckdns.org>.

## Resumo

| | Antes | Depois |
|---|---|---|
| Tempo mediano (bancada, 12 perguntas) | **56,8 s** | **~15–18 s** |
| Pior caso (bancada) | 103,7 s | ~26 s |
| **Produção, as mesmas 12 perguntas** (2 rodadas) | perguntas abertas em 81–96 s | **mediana 16–18 s, máx. 25 s** |
| "O que são os Titãs da Robótica?" | 68 s, 1.812 caracteres | 13 s, ~580 caracteres |
| Atalhos da tela inicial falhando com "não encontrei" | aleatório (seu print) | 0 de 12 execuções |
| "Liste os patrocinadores" | 0 de 14 sempre | 14 de 14 em parte das execuções |
| Palavras sem acento nas respostas | — | 0 em todas as rodadas |

A arquitetura do pipeline **não mudou**: as mesmas etapas, na mesma ordem.
Mudou o esforço de raciocínio de cada etapa, a redação dos prompts e dois
defeitos de lógica.

## Como medi

Montei uma bancada que roda o pipeline real (`TitasBotService.ask`) com um
índice vetorial idêntico ao de produção (mesmos 3 PDFs, 289 documentos, 1.026
trechos) e registra, por pergunta, o tempo total, a resposta e — por etapa de
LLM — o tempo e o tamanho da saída. Assim dava para ver **onde** o tempo ia e
**onde** a resposta crescia.

Perguntas: os 4 atalhos da tela inicial (o que mais vai aparecer numa demo) e
8 do `model_eval_cases.json`, que têm resposta de referência — para checar
acerto, não só tempo.

Testei 8 configurações. As respostas foram conferidas item a item contra a
referência (quantos orientadores, colocações e patrocinadores a resposta
acerta), porque resposta curta e rápida que perde informação não serve.

## Por que estava lento

Cada pergunta passa por até 7 chamadas de LLM **em sequência**. Com o
gpt-5-mini no raciocínio padrão (baseline):

| Etapa | Tempo médio | O que faz |
|---|---|---|
| canonicalização de lista | 15,0 s | junta itens duplicados |
| geração | 13,0 s | escreve a resposta |
| auditoria | 10,9 s | confere a resposta contra o contexto |
| expansão da consulta | 10,7 s | gera 3 variações da pergunta |
| escopo | 9,2 s | remove fatos de outras equipes |
| seleção de evidências | 8,9 s | escolhe IDs de trechos |

Os modelos GPT-5 são **modelos de raciocínio**: antes de responder, gastam
tokens "pensando". Isso faz sentido na geração, mas não para escolher IDs de
trechos ou juntar itens repetidos — e era aí que ia quase metade do tempo.

**Seu próprio estudo já mostrava isso.** Com o mesmo pipeline, em setembro:
gpt-5-mini levou mediana de **37,7 s** por resposta, Claude Haiku 4.5 **9,1 s**
e DeepSeek **5,6 s**. A diferença não é o modelo ser "mais lento" — é ele
raciocinar em todas as etapas. Pode ser um bom ponto de discussão na defesa.

Por isso trocar gpt-5-mini por gpt-5-nano **não mudava nada** no tempo (testei:
~82 s nos dois) — os dois raciocinam do mesmo jeito.

## Por que as respostas estavam grandes

Você estava certo, e há quatro causas — **nenhuma delas é a correção de
acentos** que fiz ontem. Conferi: as respostas do seu estudo de setembro, nas
perguntas abertas, já vinham longas e com os mesmos vícios.

1. **O prompt pedia.** O `GEN_PROMPT` mandava responder de forma
   "conversacional e **didática**", sem limite de tamanho. O modelo
   interpretava como "explique tudo": parágrafos, listas de fatos e títulos
   como "Resumo objetivo:" e "Fatos sobre a equipe:".
2. **A auditoria reescrevia tudo.** O formato pedia `ANSWER: <resposta>`
   sempre, então o auditor repetia o texto inteiro mesmo aprovando sem mudar
   nada. Numa resposta de 2.400 caracteres, foram 26 s só para copiar.
3. **A regra interna sobre Asimov vazava.** O prompt de escopo dizia "É
   OBRIGATÓRIO considerar os dados e pódios da Asimov como válidos e
   pertencentes aos Titãs", e o modelo escrevia isso **na resposta**. Já
   acontecia no estudo — a resposta de participação de setembro começa com
   "Observação histórica: … dados e resultados da Asimov são considerados
   pertencentes aos Titãs".
4. **Resposta longa custa três vezes.** Geração, auditoria e escopo emitem a
   resposta inteira. Resposta grande deixava as três etapas lentas.

Uma observação sobre a comparação: a mediana do estudo (185 caracteres) é
puxada pelas perguntas factuais curtas ("Qual o primeiro nome?" → "Asimov").
Nas perguntas abertas, que são as dos atalhos da tela, o estudo também
gerava respostas longas.

## O que mudei

**1. Esforço de raciocínio por etapa** (`CHAT_REASONING_EFFORT=low`,
`CHAT_FAST_REASONING_EFFORT=minimal`)

| Etapa | Antes | Agora |
|---|---|---|
| decisão de contexto, seleção de evidências, escopo, canonicalização | padrão | `minimal` |
| expansão da consulta, geração, auditoria, refoco | padrão | `low` |

A expansão de consulta começou em `minimal`, mas numa execução ela gerou
consultas que tiraram do contexto as tabelas certas e a pergunta de
classificações de 2017 caiu para 0 de 9 itens. Como ela decide o que a busca
encontra, voltei para `low` (+2 s, sem nenhuma falha total).

**2. Auditoria aprova sem reescrever.** Com `STATUS: OK` o auditor escreve só
`ANSWER: =` e a resposta original é mantida. 8 de cada 11 auditorias aprovam,
então a etapa caiu de ~11 s para ~7 s.

**3. Prompts concisos.** "Responda em no máximo 3 ou 4 frases curtas, ou numa
lista curta", "não use títulos como Resumo ou Fatos", "não repita estas
instruções". O critério sobre Asimov virou "critério interno (não mencione na
resposta)".

**4. Bug: atalhos da tela inicial falhando ao acaso.** Era o que aparece no seu
print. Em perguntas com "quais", se **um único** trecho do PDF de tabelas
aparecesse na busca, o contexto virava **só tabelas** — que têm colocações e
orientadores, nada de tecnologias. Resultado: "não encontrei" ou não,
conforme a busca daquele momento. Agora o atalho só vale para o que as tabelas
contêm (colocações, orientadores, estudantes, subgrupos).

**5. Bug: lixo nas respostas de lista.** Quando o modelo dizia "não encontrei",
um fallback recortava frases dos trechos. Ele pontuava a frase pela
sobreposição de palavras com a pergunta — e "equipe", "Titãs", "Robótica"
estão em quase todo trecho. Para "Liste os patrocinadores", **qualquer** frase
sobre a equipe passava, e a resposta saía como 20 linhas de fragmentos do
livro. Agora só contam os termos específicos da pergunta.

**6. Participação.** A resposta restringia a dois cursos, contra a referência
("qualquer estudante, independentemente do curso"). A base só diz de quais
cursos vieram integrantes — o modelo transformava isso em requisito. O prompt
agora explicita que isso não é restrição e pede os critérios de seleção e
permanência (perfil, interesse, disponibilidade, rendimento escolar).

## Qualidade: o que verifiquei

Itens da referência que cada resposta acerta, várias execuções:

| Pergunta | Baseline (56,8 s) | Final |
|---|---|---|
| Classificações em 2017 (9 itens) | 7 | 6, 9, 7 |
| Orientadores em 2018 (8 itens) | 7 | 8, 8, 8 |
| Patrocinadores (14 itens) | 0 | 0, 14, 0 |

Atalhos da tela inicial, 3 execuções cada: **0 falhas em 12**, entre 12 e 22 s.

**Em produção** (site real, duas rodadas depois do deploy): classificações
7/9 e **9/9**, orientadores 7/8 nas duas, patrocinadores 0/14 e **14/14**.
Nenhuma palavra sem acento, nenhum título "Resumo"/"Fatos" e nenhum
vazamento da regra sobre Asimov. A lista de
tecnologias trouxe LEGO EV3, Spike Prime, Arduino, Raspberry Pi e impressão
3D, como a referência.

**Conversa com seguimento** (testada no site, na mesma sessão):

| Turno | Resposta | Tempo |
|---|---|---|
| "Quem foram os orientadores em 2018?" | os 8 orientadores | 17 s |
| "E em 2019?" | entendeu o seguimento: os 9 de 2019 | 18 s |
| "Qual era o primeiro nome da equipe?" | Asimov | 5 s |
| "Por que mudou?" | entendeu: registro de marca | 13 s |
| "Oi, tudo bem?" | saudação | 0,1 s |

30 testes unitários passam (12 novos em `tests/test_latency_optimizations.py`),
e o CI roda todos antes de publicar.

## Limitações que continuam (não mexi)

Todas já existiam no baseline **e** no seu estudo de setembro:

- **RoboCup 2025.** "Em quais anos participou do Mundial?" responde 2019 e
  2024, sem 2025 (referência tem os três).
- **Ano de criação.** Responde "2015"; a referência explica que foi proposta
  em 2014 e começou em 2015.
- **Quem idealizou.** Às vezes aponta "conflito" entre Renato Lopes de
  Oliveira e Renan Osório Rios — a base cita os dois em papéis diferentes.
- **Projetos.** Lista 2 ou 3; a referência tem bem mais.
- **Participação.** Melhorou ("em regra, estudantes do Ifes"), mas ainda dá
  foco aos cursos técnicos e de SI e às vezes omite o rendimento escolar. A
  causa: **os PDFs não dizem "qualquer estudante, independentemente do
  curso"** — a sua referência vai além do que está na base. A correção certa
  é acrescentar esse texto à base de conhecimento, não forçar pelo prompt
  (seria o modelo afirmar algo sem evidência).
- **Patrocinadores.** Acerta os 14 só quando a busca traz o trecho da lista.
- **Variação entre execuções.** Os modelos GPT-5 **não aceitam
  `temperature=0`** — o código descarta o parâmetro e o modelo roda com
  temperatura padrão. A mesma pergunta pode sair diferente a cada vez. Isso
  vale também para as respostas do seu estudo.

## Para o dia da defesa

- **Endereço: <https://titasbot.duckdns.org>.** Se ele não abrir (o DuckDNS
  é um serviço gratuito de terceiros), use a reserva
  <https://vps73870.publiccloud.com.br> — é o mesmo servidor.
- **Não faça push na `main` durante a apresentação.** Cada deploy recria o
  container e o site fica ~15 s fora do ar (vi dois erros 502 durante um
  deploy). Mudanças só em `.md` ou em `estudo_defesa/` não disparam mais
  deploy.
- Faça uma pergunta qualquer alguns minutos antes de começar: confirma que
  está tudo no ar.
- Os atalhos da tela inicial levam ~13–23 s. Perguntas factuais diretas
  ("primeiro nome da equipe") respondem em ~4 s, e saudações na hora.

## Impacto no TCC

- As etapas do pipeline descritas no texto continuam as mesmas.
- **Os scripts de avaliação não mudaram de comportamento**: com as duas
  variáveis de raciocínio vazias (padrão fora do Docker), tudo roda como antes.
  Os resultados do estudo continuam reproduzíveis.
- Mas a **produção** agora roda com outra configuração que a do estudo. Se a
  banca perguntar se a demo é idêntica ao que foi avaliado: as etapas e o
  modelo são os mesmos; o esforço de raciocínio por etapa e a redação dos
  prompts foram ajustados depois, para a demonstração.

## Como desfazer

Só a parte de tempo (mantendo os prompts novos), no servidor:

```bash
ssh -i ~/.ssh/titasbot_vps root@vps73870.publiccloud.com.br
cd /opt/titasbot
sed -i 's/^CHAT_REASONING_EFFORT=.*/CHAT_REASONING_EFFORT=/; s/^CHAT_FAST_REASONING_EFFORT=.*/CHAT_FAST_REASONING_EFFORT=/' .env
docker compose up -d
```

Tudo (voltar para a versão de antes desta noite), no servidor:

```bash
cd /opt/titasbot
sed -i 's|^TITASBOT_IMAGE=.*|TITASBOT_IMAGE=ghcr.io/vctorpego/titasbot:db543587090b5d9c97f0cda3d4fab5c365175bcd|' .env
docker compose pull && docker compose up -d
```

Para voltar a acompanhar a `main` depois, devolva `TITASBOT_IMAGE` para
`ghcr.io/vctorpego/titasbot:latest`.
