# Relatório de execução — Sessão dupla R1-b1 (ParEGO) → R1-e7 (EDN-ARMOEA)

> **O que é este documento.** A narrativa COMPLETA do processo desta sessão (2026-07-17), para a
> torre de controle: cada etapa executada, cada comando de validação rodado e seu resultado,
> os 3 incidentes encontrados (com diagnóstico e resolução), e o estado final. Complementa (não
> substitui) os handoffs técnicos `handoff/R1-b1.md` e `handoff/R1-e7.md` — aqui está o COMO;
> lá está o QUÊ. Precedente: `[c217-fix-log]`.

**Veredito curto:** os 2 cartões fecharam **VERDES e committados** (6 commits, working tree
limpo). Gate objetivo exit 0 nos 6 runs (2 algs × 3 problemas), regressão total verde (17 gates
Python + stub MATLAB 7/0 + preflight), fidelidade instrumentada e entregue para a validação
MANUAL do autor (D97 — não julgada por mim). 3 incidentes reais encontrados e resolvidos, sendo
2 achados estruturais que a torre deve reter (§5 e §7).

---

## 1. Verificação de ambiente (D81 — ANTES de qualquer código)

| Checagem | Comando | Resultado |
|---|---|---|
| Ponte MATLAB↔Python | `matlab -batch "pyenv; double(py.numpy.array([1,2,3]).sum())"` | pyenv 3.11 → `~/ponte_teste/bin/python`; **soma = 6** ✓ |
| Statistics Toolbox (dacefit/normcdf do b1) | `ver('stats')` + `license('test','Statistics_Toolbox')` | **Statistics and ML Toolbox 25.1, licença 1** ✓ |
| Gate Python (env-main) | `PY -c "import pyarrow, numpy"` | Python 3.11.9, pyarrow 25.0.0, numpy 2.4.6 ✓ |
| DoEs da validação | `ls data/doe/{MMF1,ZDT1,DTLZ2}` | Artefatos + sidecars presentes p/ todas as sementes ✓ |
| Estado do git | `git status` | Limpo (exceto `data/doe/DTLZ2_d15/` untracked pré-existente — não tocado) |

## 2. PASSO 0 — contexto lido (na ordem prescrita, e somente ele)

`HANDOFF_MESTRE.md` (§10/§11 — armadilha nº1 do §11.1 anotada) → `handoff/R1-c217.md` (template
`run_c217` + receita N.0) → `handoff/R1-b3.md`/`R1-b4.md` (padrão sessão-dupla) →
`claude_code_context/CLAUDE.md` → linha R1-b1 do `cards/INDEX.md` → `00_contrato_rodada1.md`
(N.0/N.2/N.3/L.0/S.1–S.3) → `alg_b1_parego.md` INTEIRO → `01_regras_globais.md` (D53–D100) →
`03_contrato_export.md` (§17 completo — caso MONO-OUTPUT da ③). O `alg_e7_ednarmoea.md` foi
lido SOMENTE no PASSO 0 da FASE 2, como mandado. Nenhum outro `alg_*.md` foi aberto.
Complemento de implementação (código, não contexto): `src/experiment.m`, `FEBudget.m`,
`RunBuffer.m`, `hook_output.m`, `b3_instrument.m` (template), `accept.py`, `preflight.py`,
`anchors.json`, e os fontes stock de ParEGO/EDN-ARMOEA.

## 3. FASE 1 — R1-b1 (ParEGO)

### 3.1 Plano (apresentado antes de codar; sem ambiguidade material ⇒ segui direto)
P1 DoE :29–:30 juntas (D94) · P2 guard L8 escopado · P4 NaN-guard (semântica: idioma L4 do
c141, `den(den==0)=eps` — resultado numericamente INVARIANTE à escolha do denominador, pois o
numerador é 0 nas colunas degeneradas; por isso não parei p/ perguntar) · instrumentação
só-leitura · `run_b1` cópia do `run_b3` · ③ mono-output D47/C3.

### 3.2 Implementação (o que mudou, por arquivo)
- `ParEGO.m` — P1 (:29–:30 → `Population = Problem.Evaluation(Problem.data.X0);`); P4 (:39,
  `den==0→eps` + flag); tic/toc+contadores no dacefit (:58); `[PopDec,gainfo]=EvolALG(...)`;
  **sync D89** pós-:61; chamada `b1_instrument`.
- `EvolALG.m` — P2 (:25 `sqrt(max(mse,0))` + contador mse<0); 2º output `info` (pop final
  scorada + y/s/EI + Gbest + e0_trace + contadores). Decisões INTACTAS (torneio bugado :16
  mantido — CÓDIGO K.3). **Armadilha §11.1 respeitada:** edição POR ARQUIVO; provado por
  `grep -rn "sqrt(mse)"` (2 ocorrências no repo: ParEGO/EvolALG.m:25 patchada,
  **EGO/EvolEI.m:23 intocada**) + `git diff --name-only -- algorithms/` no fim.
- `src/b1_instrument.m` (novo) — ③ = pop final do GA por iteração de BO (DEF-C2 §17.4),
  mu_0/sigma_0 escalar (writer preenche mu_1..=NULL), C3 `transf_params={λ,min,max,gbest}`;
  jsonl `b1_gen` (S.7); timing §17.6; eventos mse_neg/nan_guard/dedup_treino/ei_nan.
- `src/experiment.m` — `case 'b1' → run_b1` ('N',100 → λ 100/91; sem 'parameter').
- `anchors.json` — `b1-doe-D94` concretizada com literais (p/ veto); `b1-mse-guard-L8` já literal.

### 3.3 INCIDENTE 1 — write_surrogate O(n²) (o achado de infra da sessão)
**Sintoma:** MMF1 e DTLZ2 verdes; no ZDT1 o Solve fechou em ~27 min mas o processo ficou
**3h30+ a 100% CPU sem produzir o parquet da ③** (nenhum `.tmp` criado → travado ANTES do
`parquetwrite`). **Diagnóstico (evidência, não palpite):** `/usr/bin/sample` do processo →
100% do tempo útil em `libmwstring_core/matrix/string` ⇒ os builders **`arrayfun` por coluna
de STRING** do `write_surrogate` (infra R1-00): acumulação de string array é **O(n²)**. A ③
do b1/ZDT1 tem **757.316 linhas** (pop final do GA ≈ 2×|arquivo| ≈ 1.860/iter × 600 iters) —
~3,4× o recorde anterior (b3, 221k) ⇒ ~12× o custo ⇒ horas. **Morderia a bateria inteira.**
**Resolução:** kill do processo; reescrita da montagem das colunas em **UMA passada O(n)
prealocada** (mesmos NaN/missing/tipos/ordem/branch int32-double do rsi). **Prova de
equivalência:** os parquets do MMF1 do writer antigo foram guardados; re-run do MMF1 com o
novo → pyarrow: **①②③ com schema E conteúdo IDÊNTICOS**; timing difere SÓ em `tempo_*`
(relógio de runs distintos; `geracao`/`n_acumulado` idênticos = determinismo do run re-provado).
**Pós-fix:** stub `accept_r1_00` re-rodado → PASS 7/0; ZDT1 re-rodado → **1.719 s TOTAL**
(Solve+export). Exceção controlada ao "não altere a infra" — sinalizada p/ veto.

### 3.4 Validação b1 (comandos × resultados)
| Comando | Resultado |
|---|---|
| `checkcode` nos 4 arquivos editados | só avisos de estilo (idioma da infra); 0 erro |
| `experiment('b1','MMF1',0)` | ok · FE **61** · CP-init ✓ · cache_hits=2 (probe+1 dup real) · 16 s |
| `experiment('b1','DTLZ2',0)` | ok · FE **371** · CP-init ✓ · λ=91 NBI · 689 s |
| `experiment('b1','ZDT1',0)` (pós-fix) | ok · FE **929** · CP-init ✓ · cache_hits=3 (probe+2 dups → **sync D89 exercitado**) · 1.719 s |
| `accept.py R1-b1 …` ×3 | **exit 0 ×3** |
| Auditoria pyarrow (script ad-hoc) | ① 61/371/929 (init+opt exatos); ③ 3.320/120k/757k linhas, **mu_0/sigma_0 100% preenchidos, mu_1../sigma_1.. 100% NULL** (mono-output D47); C3 completo; rsi double+NaN (fallback R1-00); timing com `n_acumulado` saturando no cap top-(11D−1+25) |
| Workflow adversarial (3 lentes: fidelidade-stock, numérica-edge, fiação-schema) | **0 achados sobreviventes** (3 agentes, 91 tool-calls, 13 min) |
| `git diff --name-only -- algorithms/` | SÓ os 2 arquivos do ParEGO; **EvolEI.m intocado** |

### 3.5 Commits b1
`021e5f0` (patches ParEGO) · `dfcb2b7` (run_b1 + b1_instrument + fix infra + âncora) ·
`9ade475` (handoff + cartão ✅).

## 4. FASE 2 — R1-e7 (EDN-ARMOEA)

### 4.1 Leitura e plano
`alg_e7_ednarmoea.md` INTEIRO + fontes stock (EDNARMOEA.m, Dropout/* — Estimate/trainmodel/
trainNet/updatemodel/testNet/dropout/iniA, IndividualSelect, SelectTrainData, UpdateRefPoint).
**Descoberta de leitura que fecha a C3:** a "translação pelo ideal" REAL do built-in está no
`SelectTrainData` (subtrai `min(A.objs)` do y a partir do 1º retreino; ciclo 1 treina cru); o
`Estimate` só reverte o mapminmax ⇒ μ/σ saem no espaço TRANSLADADO ⇒ o `ymin` por ciclo é o
parâmetro de des-transformação (por isso o "logar min(A.objs)" do cartão é load-bearing).
Plano ≤15 linhas apresentado; segui direto.

### 4.2 Implementação
- `EDNARMOEA.m:31–:32` — P1 DoE juntas (D94). Instrumentação: tic/toc dos 2 treinos; snaps da
  pop selecionada de cada geração interna (19/ciclo); `ymin_vig`/`espaco_vig` (C3); sync D89;
  **guarda (c) do D60** (`stall_ciclos` — ciclos consecutivos com 0 FE, SÓ LOGA); chamada
  `e7_instrument`. `flag=RatioOld-Ratio<delta` INTACTO (RatioVelho/RatioNew são cópias).
- `Dropout/trainmodel.m:6` — **dropout [0.2,0.5]→[0.1,0.1]** (fidelidade D30→ARTIGO).
- `Dropout/Estimate.m:26` — guard `sqrt(max(var,0))` + 3º output `nneg`.
- FICOU stock: decay/run/batch hardcodes, Ke=3, δ=0.05, init N(0,1/fan_in), SGD 8e4/8e3, T=100,
  SEM dedup de infill (comportamento; duplicata = cache-hit 0 FE + slot perdido, logado).
- `src/e7_instrument.m` (novo) — ③ por objetivo no espaço do MODELO + C3 translação; jsonl
  `e7_gen` (Ratio/flag/ramo/motivo, dup_infill, stall_ciclos, **rss_mb — RAM D86 via `ps`**);
  timing com linha extra do treino inicial (8e4) no 1º ciclo.
- `src/experiment.m` — `case 'e7' → run_e7`; `anchors.json` — `e7-doe-D94` concretizada.

### 4.3 INCIDENTE 2 — sombra de path do DRLOS-EMCMO (achado estrutural; reter p/ TODOS os cartões)
**Sintoma:** 1º run falhou em segundos: "Too many output arguments" no `Estimate`. **Causa:** o
built-in **DRLOS-EMCMO** (fora do estudo) vendoriza um `Dropout/` **byte-idêntico** ao do
EDN-ARMOEA; `D<E` no genpath ⇒ as cópias do DRLOS vêm ANTES no path e **sombreiam**
Estimate/trainmodel/trainNet/testNet/updatemodel/dropout/iniA/MgaussRandom (as chamadas saem
de `EDNARMOEA.m`, que NÃO é same-folder do `Dropout/` — a regra same-folder NÃO cobre
subpastas). **Implicação grave:** sem o meu 3º output no Estimate (que quebrou rápido, por
sorte), os patches sancionados (dropout 0,1 e guard) **NUNCA rodariam, em silêncio** — o run
ficaria verde no gate com o σ ERRADO. **Resolução:** `ensure_paths_e7` = prepend de
`genpath(EDN-ARMOEA/)` + **asserts `which`** dos 8 nomes (padrão do `ensure_paths_c141`/S.8).
**Regra nova p/ a torre:** todo built-in com SUBPASTA própria exige checagem de sombra.

### 4.4 INCIDENTE 3 — CRLF no patch do trainmodel (pego pela verificação adversarial)
O workflow adversarial do e7 (3 lentes) devolveu **1 achado real (minor)**: meu patch do
dropout via Python em modo texto normalizou CRLF→LF no arquivo inteiro (diff de 55 linhas em
vez de 1 — quebrava a auditabilidade byte-exata do patch). **Resolução:** restaurei o stock e
re-apliquei em modo binário preservando CRLF → diff final = 1 linha trocada + 3 de comentário.
As outras 2 lentes: 0 achados.

### 4.5 Validação e7 (comandos × resultados)
| Comando | Resultado |
|---|---|
| `experiment('e7','MMF1',0)` | ok · FE **61** · CP-init ✓ · 302 s · **corte D61 provado**: 40 infills ∤ Ke=3 → 14º lote cortado no meio pelo hard-stop (guard `hard_stop` no jsonl) |
| `experiment('e7','DTLZ2',0)` | ok · FE **371** · CP-init ✓ · 80 ciclos EXATOS (240/3) · 1.691 s |
| `experiment('e7','ZDT1',0)` | ok · FE **929** · CP-init ✓ · 200 ciclos EXATOS · **4.343 s (novo pior-caso wall da R1)** |
| `accept.py R1-e7 …` ×3 | **exit 0 ×3** |
| Auditoria pyarrow | ③ 24,7k/152k/380k linhas; **mu_j/sigma_j preenchidos p/ TODOS os M**; espaços `{cru, transformado}` (C3 ✓); timing = ciclos+1 (linha extra do treino inicial ✓); `n_acumulado` constante = 11D−1 (cap SelectTrainData ✓); ramos convergência/incerteza = 8/5, 69/11, 152/48; guards dup_infill/std_neg/saldo_congelado armados, **0 disparos** na semente 0; **RSS máx 0,9/1,8/3,25 GB** (D86 medido) |

### 4.6 Commits e7
`8bd66b8` (patches EDN-ARMOEA) · `b8e9635` (run_e7 + e7_instrument + precedência de path +
âncora) · `a9675cd` (handoff + cartão ✅).

## 5. Regressão TOTAL final (rodada após TUDO — prova de não-quebra cruzada)

```
accept.py F0-01 F0-02 F0-03 F0-04 ................................ exit 0 ×4
accept.py R1-c217 {MMF1,ZDT1,DTLZ2} .............................. exit 0 ×3
accept.py R1-c141 MMF1 ........................................... exit 0
accept.py R1-b3  {MMF1,ZDT1,DTLZ2} ............................... exit 0 ×3
accept.py R1-b4  {MMF1,ZDT1,DTLZ2} ............................... exit 0 ×3
accept.py R1-b1  {MMF1,ZDT1,DTLZ2} ............................... exit 0 ×3
accept.py R1-e7  {MMF1,ZDT1,DTLZ2} ............................... exit 0 ×3
accept_r1_00.m (stub MATLAB, re-exercita o writer NOVO) .......... PASS 7/0
preflight.py (b1-mse-guard-L8, b1-doe-D94, e7-doe-D94 = APLICADO) . exit 0
```
(Nota de método: o stub R1-00 foi rodado 2× — logo após o fix de infra da §3.3 e de novo aqui.)

## 6. Números-guia consolidados p/ o dossiê de fidelidade em lote (D97 — GUIA, não gate)

| Alg | Problema | FE | IGD_raw | \|ND\| | Observações de mecanismo (fonte: .jsonl) |
|---|---|---|---|---|---|
| b1 | MMF1 | 61 | — (IGDX pós-hoc D99) | 18 | dedup_treino ×2; cache 2 |
| b1 | DTLZ2 | 371 | 1,2558e-1 (das-dennis 5050→esfera) | 73 | dedup_treino ×95; n_treino satura 151/156 |
| b1 | ZDT1 | 929 | 3,3486e-2 (front analítico 10k) | 42 | dedup_treino ×490; 2 dups reais de infill; guards mse_neg/nan_guard/ei_nan: 0 disparos |
| e7 | MMF1 | 61 | — | 10 | ramos conv/incert 8/5; hard_stop no 14º lote |
| e7 | DTLZ2 | 371 | 2,1942e-1 | 88 | ramos 69/11 (âncora J é d=20: 0,647) |
| e7 | ZDT1 | 929 | 4,5967e-1 | 23 | ramos 152/48; dup_infill/stall: 0; RSS 3,25 GB |

**Custo (p/ o piloto §22.5):** b1/ZDT1 ≈ 29 min (~14 h/core p/ 30 sementes); **e7/ZDT1 ≈ 72
min (~36 h/core) — novo pior-caso da R1** (1,68M passos SGD, B6.4: medidos, nunca reduzidos);
**RAM e7 3,25 GB/run** ⇒ 8 workers ≈ 26 GB agregados — dimensionar antes das 30 sementes.

## 7. Sinalizações para o VETO do autor (consolidadas)

1. Âncoras `b1-doe-D94` e `e7-doe-D94` concretizadas com literais (precedente c141/b3).
2. **Fix de infra `write_surrogate` O(n²)→O(n)** (§3.3) — única edição transversal;
   equivalência provada, mas é o writer de TODOS os MATLAB.
3. P4 do b1 = idioma L4 (`den==0→eps`; resultado invariante).
4. ③ do b1: pop FINAL do GA por iteração (leitura DEF-C2 §17.4, precedência sobre o
   "best/ger" do I.1); C3 `{λ,min,max,gbest}`.
5. ③ do e7: UMA linha por candidato em espaço do MODELO + `transf_params={ymin}` (cru=μ+ymin —
   leitura D47 da DEF-C3; NÃO materializei linhas duplicadas por espaço); carimbo
   `geracao=ciclo` (precedente b3).
6. Precedência de path do e7 (prepend+asserts — muda a ordem de resolução do processo; c141
   tem o mesmo padrão).

## 8. O que esta sessão NÃO fez (limites honestos, por desenho)

- **Não julguei fidelidade** (D97) — instrumentei e deixei os números prontos; o veredito é do
  autor, em lote, no fim da onda MATLAB.
- **Não rodei a bateria** — só semente 0 dos 3 problemas do gate (o escopo do cartão).
- **Não instalei pins nem toquei envs**; não editei bundles/SPEC; não fiz o doc-sync D6 (janela
  agora livre). Não toquei c238/pisos/e74/e103 nem o `alg_*.md` de nenhum outro algoritmo.
- Guardas do e7 (`dup_infill`/`saldo_congelado`/`std_neg`) e do b1 (`mse_neg`/`nan_guard`/
  `ei_nan`) estão ARMADAS mas não dispararam na semente 0 — vigiar na bateria.

## 9. Estado final do repositório

Branch `experiment/definitive_algorythms`, working tree limpo. Commits da sessão (ordem):
`021e5f0` → `dfcb2b7` → `9ade475` (`[R1-b1]`) → `8bd66b8` → `b8e9635` → `a9675cd` (`[R1-e7]`).
Arquivos tocados: 2 do ParEGO + 3 do EDN-ARMOEA (sob `algorithms/`, rastreados pela raiz);
`src/experiment.m` (+run_b1/run_e7/fix writer), `src/b1_instrument.m` e `src/e7_instrument.m`
(novos); `anchors.json` (2 âncoras concretizadas); `cards/INDEX.md` (b1/e7 ✅);
`handoff/R1-b1.md`, `handoff/R1-e7.md` e este relatório. Outputs em
`data/experiments/main/{b1,e7}/` (gitignored — regeneráveis pelos comandos dos handoffs §5).
