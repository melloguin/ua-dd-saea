# HANDOFF — validação de fidelidade da campanha T11

**De:** torre de validação de fidelidade (instância F5/T11) · **Para:** torre central de implementação
**Data:** 2026-07-31 · **Status:** análise fechada · **Doutrina:** D97 — analiso e recomendo; o veredito é do AUTOR

---

## 0. Leia nesta ordem (30 min para entender tudo)

| # | arquivo | tempo | por quê |
|---|---|---|---|
| 1 | `f5/t11/RELATORIO_FINAL_T11.md` | 15 min | **começa aqui.** O consolidado inteiro: veredito, tabela comparativa, regressões, ganhos, bloqueadores, decisões |
| 2 | `f5/t11/dados/bloqueios.json` | 5 min | os 22 bloqueadores + 18 decisões do autor, machine-readable |
| 3 | `f5/t11/dados/regressoes.json` | 5 min | as 14 regressões e os 8 ganhos, cada um com a medição que fiz |
| 4 | `f5/t11/relatorios_config/{seu_config}.md` | 5 min | só o(s) config(s) que você for mexer — 40–76 KB cada |

Se você só tem 3 minutos: **§1, §2 e §7 do `RELATORIO_FINAL_T11.md`.** É o veredito, o problema
da régua e os 8 bloqueadores.

---

## 1. O que foi feito, em um parágrafo

Validei os 24 configs contra os papers e contra a rodada-42, medindo o efeito da campanha T11 e
comparando com a análise F5 anterior. Rodaram **24 agentes independentes** (1 por config, 5,8 M
tokens), depois **11 agentes** que tentaram **refutar** os 24 vereditos e varreram as
transversais, depois medições diretas minhas sobre os 11 smokes Python e a célula do teto do c154.
Nada foi copiado do handoff da T11: a instrução do autor foi *"desconfie dos números, re-meça o
que for usar"*, e ela foi cumprida — inclusive contra os meus próprios números da F5.

---

## 2. O veredito

**ACEITAR os 24.** Zero bugs de mecanismo. A T11 **não tocou uma linha de algoritmo**, e isso é
medido, não alegado: **9/9 pares `g6_com`×`g6_sem`** com a camada ① de **sha256 idêntico**.

**Mas leia isto antes de comemorar:** a campanha melhorou o que o pipeline **decide** e piorou o
que ele **declara**. Saldo líquido **+0,075** na média (não os +0,158 que a leitura ingênua dá).

| | melhorou | manteve | piorou |
|---|:--:|:--:|:--:|
| base recomendada (híbrida) | 10 | 11 | **3** — `c217`, `moead`, `moead_media` |

---

## 3. 🚨 Três coisas que você precisa saber antes de tocar em qualquer código

### 3.1 A régua de comparação estava trincada

`f5/scores_f53.csv` é **pré-adversarial** e nunca foi atualizado — a própria sentença
`f5/adversarial/moead_media-C9b.md:76` escreve *"`scores_f53.csv` a atualizar"*, e isso não
aconteceu. O `RELATORIO_FINAL_F5.md:129` tem a matriz **D1** revista, **mas ela é recomendação
dentro de uma decisão aberta**, não nota homologada.

**Efeito prático:** comparar a T11 contra o CSV credita a ela **5 achados que a F5.4 já havia
resolvido sem uma linha de código**. Foi exatamente o erro que **8 dos 24 agentes** cometeram —
dupla contagem. Se você for reportar ganho da T11, use a base híbrida do §2 do relatório final.

### 3.2 A assinatura de defeito da campanha: campo verde, dado sentinela

Um campo nasce para fechar uma lacuna que a auditoria nomeou, **entra verde, e vem vazio**. A
lacuna continua aberta e agora está **camuflada** — que é pior do que estar aberta e visível.

| config | campo | o que medi |
|---|---|---|
| c217 | `pmid_ids` | **426/426 = −1**, ids distintos = `[-1]` |
| b5r / b5m | `flag_vetores_degenerados` | presente em **1.144/1.144**, não-nulo em **0/1.144** |
| c217 | `y_treino_dist` | `(0,0,n)` em **42/42** — conta alvo ternário sobre vetor que só tem `{1,2}` |
| c217 | `params.operadores` | declara Balde C 20/20 onde a SPEC §567 diz *"não se aplica"* |
| 5 offline Python | `timing/tempo_aval_real_s` | era **0,0 exato em 200/200** na s42; agora mede ingestão do dataset |
| c122 | sonda estratificada | **10.500/10.500** linhas com `e(z)` em `mu_0` e `pred_score` NULL |

### 3.3 A causa-raiz: **os gates testam texto, não comportamento**

É o achado mais acionável do relatório inteiro, e explica por que tudo acima atravessou uma
campanha de instrumentação com **6 portões verdes**:

- `tests/test_g7_instrumentacao.py:118-127` → `assertNotIn("tempo_aval_real_s=0.0", src)` sobre o
  **fonte** de 5 arquivos. Nunca roda um offline.
- `tests/test_a2_c122.py:220-260` → `inspect.getsource` + `assertIn`. Afere o texto da função,
  nunca a linha emitida.
- `tests/test_a9_regra_rotulo_c217.py` → testa a aritmética do índice e a presença da string,
  nunca o **valor**.

**A regra que eu recomendo adotar, e é a mais barata do relatório:** *todo gate novo precisa de um
controle negativo — um teste que REPROVA na versão de hoje e passa depois do fix.* Dois configs já
fizeram certo e servem de modelo: `c149` (`gate_3x1` com 29 OK / 1 RUIM) e `sobol_batch` (G-7 RUIM
na s42 × OK no pós).

---

## 4. O que fazer antes do disparo das 30 sementes

**8 bloqueadores. Soma do trabalho de código: ~10 linhas.** O resto é decisão e texto.

| id | o quê | config | custo |
|---|---|---|---|
| BL-01 | `pmid_ids`: fatia `1:D` numa matriz de largura D+1 | c217 | **1 linha** + controle negativo |
| BL-02 | `flag_vetores_degenerados` é código morto (`src/b5_prob.py:118` lê o objeto errado) | b5m, b5r, moead_media | **1 token** + ~3 linhas |
| BL-05 | `y_treino_dist` degenerado | c217 | 1–3 linhas |
| BL-06 | sob `teto_wall` o finalProbe não roda | c154, c262 | **1 linha** (~0,08 s) |
| BL-07 | **piso de ruído O-18 desatualizado × 3 máquinas** | todas as 695×30 | **0 CPU** — só decisão |
| BL-08 | pinar `scipy` junto do `torch` na `envs.json` | sobol_batch | **1 linha** |
| BL-09 | `jsonl_line` sem `fflush` por linha | b1 + MATLAB | **1 linha** |
| BL-10 | contradição documental viva sobre N=20 (DI-32/A2 × DI-39) | 4 pisos | decisão |

**O mais grave não é de código: BL-07.** O piso declarado (HV ≤1,55%) não cobre a divergência
cross-máquina medida — `c238/MMF1` dá **ΔHV −9,69%, 6,3× o piso**. A campanha vai rodar em 3
máquinas. Se isso não for resolvido antes, todo contraste entre configs que rodarem em máquinas
diferentes fica sem régua.

**E BL-10 é o de maior risco de descarte:** se o SUB-varN rodar depois do M8 e eleger N≠20, as 25
células de **cada** piso vão para o lixo.

---

## 5. Mapa completo dos artefatos

### 5.1 O que a T11 produziu de análise (novo, 2026-07-31)

| artefato | endereço | conteúdo |
|---|---|---|
| **Consolidado** | `f5/t11/RELATORIO_FINAL_T11.md` | 24 KB · 11 seções · veredito, tabela, regressões, bloqueadores, decisões |
| **24 relatórios de config** | `f5/t11/relatorios_config/*.md` | **1,35 MB** · 40–76 KB cada · 20–34 aspectos narrados por config |
| **Validação do teto** | `f5/t11/VALIDACAO_TETO_c154.md` | 8 KB · medição completa do rito DI-43/44 |
| Seções de score verbatim | `f5/t11/_secoes_score.md` | 48 KB · a §7 de cada um dos 24, para conferência rápida |
| Baseline resolvida | `f5/t11/dados/baseline.json` | 24 × (CSV, pós-adversarial, estado, citação com arquivo:linha) |
| Vereditos verificados | `f5/t11/dados/veredictos.json` | 24 × (alegado, corrigido, sustenta, evidência re-medida) |
| Classe (3) | `f5/t11/dados/classe3.json` | 21 achados, 9 transversais, dedupados |
| Instrumentação | `f5/t11/dados/instrumentacao.json` | placar I-1..I-8 |
| Bloqueadores + decisões | `f5/t11/dados/bloqueios.json` | 22 bloqueadores + 18 decisões do autor |
| Regressões + ganhos | `f5/t11/dados/regressoes.json` | 14 regressões, 8 ganhos, todos com medição |
| **Baterias executáveis** | `f5/t11/baterias/{config}/` | **24 pastas** · scripts `.py` + CSVs/JSONs de saída de cada agente. **É aqui que está a reprodução** |

### 5.2 O que a F5 produziu antes (contexto, 2026-07-2x)

| artefato | endereço | conteúdo |
|---|---|---|
| Relatório final F5 | `f5/RELATORIO_FINAL_F5.md` | 204 KB · matriz 24×7, 16 decisões, **a matriz D1 do §2.2** |
| Plano da rodada perfeita | `f5/PLANO_RODADA_PERFEITA.md` | 64 KB · 17 bloqueadores com file:line e custo |
| Protocolo de análise | `f5/PROTOCOLO_ANALISE_FIDELIDADE.md` | 12 KB · **a metodologia** (bateria U1-U12, 4 módulos de família) |
| 24 relatórios F5 | `f5/relatorios_config/*.md` | a análise anterior, para comparar |
| 14 sentenças adversariais | `f5/adversarial/*.md` | as refutações da F5.4 — **inclui as que moveram score** |
| Scores F5.3 | `f5/scores_f53.csv` | ⚠ **pré-adversarial, desatualizado** |
| Laudo de instrumentação | `handoff/F5-LAUDO-INSTRUMENTACAO.md` | as 8 recomendações I-1..I-8 que a T11 implementou |

### 5.3 Os dados

| corpus | endereço | papel |
|---|---|---|
| **rodada-42** | `resultados_experimentos/{alg}/{problema}/42/` | **o corpus de fidelidade** — 666 células oficiais, 7 camadas cada |
| rodada-42 (bruto) | `ua-dd-saea/data/experiments/` | 744 células — inclui semente 0, `_baseline_pre_retrofit`, stubs. **Filtre** |
| evidência T11 | `evidencia_T11/` | 72 MB · 11 smokes Python, 15 MATLAB, 9 pares g6, 1 teto |

---

## 6. Tutorial — como entender esta análise

### 6.1 O modelo mental em 5 linhas

1. **Cada config é julgado contra o paper dele**, não contra os outros.
2. Cada **aspecto** do algoritmo cai em **3 classes**: (1) conforme ao paper · (2) desvio
   **sancionado** (com decisão citada) · (3) **inexplicado** 🎯 — e a classe (3) é o que puxa a
   nota para baixo. Existe ainda **T** = teto de verificabilidade (fora do denominador).
3. O **score 0–10** sai da régua do `handoff/F5-FRAMEWORK-v2.md` §F5.3b: 10 = tudo (1)/(2) com
   cada (2) ancorado, contrato perfeito, saúde limpa; 9 = com (3) menores já investigados.
4. **D97: o veredito é do autor.** Eu produzo evidência e recomendo. Nada aqui é sentença.
5. **D29 é a bússola** de para onde vai a correção quando código e paper divergem: 🔴 bug→paper ·
   🔵 versão→paper se toca o surrogate · 🟠 impl→código · 🟣 errata→código · 🟢 extensão nossa,
   declarada.

### 6.2 Onde a evidência mora: as 7 camadas

Todo experimento grava 7 camadas. Saber qual olhar é metade do trabalho:

| camada | arquivo | o que responde |
|---|---|---|
| ① | `__real.parquet` | toda avaliação real da função-objetivo — **a verdade** |
| ② | `__pop.parquet` | a população selecionada por geração |
| ③ | `__surrogate.parquet` | toda predição do modelo — **busca + SONDA** |
| ④ | `__timing.parquet` | tempos por geração (fit, busca, sonda) |
| ⑤ | `.manifest.json` | a certidão: `params`, `sigma_dict`, hashes, `campanha_id` |
| ⑥ | `.jsonl` | **o filme das decisões** — 1 evento por geração |
| ⑦ | `__final.parquet` | só nos 5 offline: o endpoint oficial |

**A SONDA é a régua comum:** 2.000 pontos Sobol fixos que **todo** surrogate prediz, a custo zero
de FE. É o que permite comparar modelos incomensuráveis. O join é **posicional**. A
`sonda_estratificada` (~500 pontos perto do arquivo) **nunca** se mistura com ela — CONTRATO
regra 12.

### 6.3 Como ler um relatório de config

Todos têm a mesma espinha:

- **§1 Ficha do mecanismo** — o que o paper manda, o que o código faz, e as divergências já
  sancionadas com a decisão citada
- **§2 Tabela de aspectos** — a matriz. Cada linha é um aspecto com classe, verificabilidade,
  Δ vs F5 e o número medido. **É o coração do documento.**
- **§3–6** — as baterias: identidades fechadas, query-joia da família, saúde, contrato
- **§7 SCORE, recomendação e VEREDITO** — a conclusão, com a **causa nomeada** do movimento
- **§8** — os classe (3) que vão à verificação adversarial
- **§9** — as armadilhas: o que faria um analista futuro concluir errado

**A "query-joia"** é a identidade central de cada família — a pergunta que, se fechar, prova que o
mecanismo é o do paper. Ex.: identidade fechada do EI (b1), recomputo do maximin (e81), argmax da
aquisição (c262), estado ⇔ desigualdade (c217/e7).

### 6.4 Como reproduzir qualquer número deste relatório

Todo número tem script. Vá em `f5/t11/baterias/{config}/`, escolha o `.py`, rode com:

```bash
/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python f5/t11/baterias/c217/b6_causa_raiz_pmid.py
```

Os CSVs/JSONs ao lado são as saídas já materializadas — dá para conferir sem rodar nada.

### 6.5 ⚠ As 3 regras que você não pode violar ao auditar

1. **NUNCA invoque `experiments.py` sobre uma célula existente, nem para no-op.** O
   `AuditLogger` faz append cego (`src/audit_log.py:55`) e o `is_run_done` pula a célula — o
   resultado é o ⑥ contaminado sem que nada mais mude. **Isso já aconteceu comigo**, num agente
   meu, em `batch/e81/ZDT4`: 10 pares header/footer vazios anexados. Auditei as 666, restaurei
   bit-exato e congelei em modo 444.
2. **Um smoke não prova fidelidade.** Prova encanamento. O §5 do `evidencia_T11/HANDOFF-SMOKES.md`
   diz certo: *"um algoritmo pode estar profundamente errado e passar nos 6 portões"*. O corpus de
   fidelidade é a rodada-42.
3. **Recomputar dominância sobre a ① ou a ⑦ é lossy** (float32) — CONTRATO regra 11.

---

## 7. O que fica pendente e é do AUTOR

**18 decisões**, todas em `f5/t11/dados/bloqueios.json`. As 5 que travam o disparo:

1. **D1 — qual matriz de score homologar?** (a) o CSV como está · (b) a lista revista pós-F5.4 ·
   (c) reabrir config a config. **Recomendo (b)** — 4 das 5 revisões são refutações provadas.
   ⚠ Atenção: a escolha **inverte o veredito do `e103`** e muda `b4`, `c149`, `b5r`.
2. **DA-01 — piso de ruído O-18 × 3 máquinas.** Ver BL-07. Decidir **antes** do disparo.
3. **DA-02 — N=20 definitivo ou SUB-varN é pré-requisito?** Contradição documental viva.
4. **DA-03 — `tempo_aval_real_s` no offline:** manter medindo ingestão (renomeando), voltar a
   NULL, ou separar em dois campos.
5. **DA-11 — as 25 células da s42 do `e74` descrevem um algoritmo diferente** do que rodará no M8
   (o DI-45 veio depois). Recomendo caveat duro: **não agregar** com runs pós-fix. Único config.

**E uma que abri hoje:** o teto de 6 h **nunca** fecha `c154/DTLZ2` — a projeção pede ~13,4 h.
Três saídas: (a) aceitar curva parcial e comparar por FE-comum *(recomendo)* · (b) elevar o teto
para ~14 h nas células BoTorch · (c) declarar como limitação metodológica. (b) multiplica o custo
das 3 máquinas por ~2,3 justamente nas células mais caras.

---

## 8. Resumo executivo para colar no topo de qualquer conversa

> A validação de fidelidade da T11 está fechada. **24/24 ACEITAR, zero bugs de mecanismo** — a
> campanha não tocou uma linha de algoritmo (9/9 pares g6 com ① de sha256 idêntico). O saldo é
> **+0,075** na média, menor do que parece: a régua da F5 estava desatualizada e 8 dos 24 agentes
> fizeram dupla contagem. **3 configs pioraram** (`c217` −0,5, `moead` −1,0, `moead_media` −0,2),
> nenhum por mecanismo — todos por instrumentação que a própria T11 escreveu, com a mesma
> assinatura: **campo verde, dado sentinela**. A causa-raiz é estrutural: **os gates testam texto,
> não comportamento**. Antes do disparo das 30 sementes há **8 bloqueadores somando ~10 linhas de
> código**, mais **18 decisões do autor** — sendo as duas mais graves não de código: o **piso de
> ruído O-18 não cobre a divergência entre as 3 máquinas** (6,3× o piso declarado) e a
> **contradição viva sobre N=20**, que pode descartar 25 células de cada piso.
> Tudo em `f5/t11/RELATORIO_FINAL_T11.md`.
