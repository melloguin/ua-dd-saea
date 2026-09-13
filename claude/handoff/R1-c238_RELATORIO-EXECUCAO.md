# R1-c238 — RELATÓRIO DE EXECUÇÃO da sessão (narrativa do processo, p/ a torre)

> **O que é.** A narrativa comando-a-comando de COMO o cartão R1-c238 foi executado
> (2026-07-17 20:00 → 2026-07-18 03:45, Mac), complementar ao `handoff/R1-c238.md`
> (que é o repasse técnico do RESULTADO). Público: a instância-torre que gerou as
> instruções. Formato-precedente: `R1-b1-e7_RELATORIO-EXECUCAO.md`.

---

## 0. Ambiente (D81 — verificado ANTES de qualquer código)

```
matlab -batch "pe=pyenv; double(py.numpy.array([1,2,3]).sum()); ver"
→ pyenv 3.11 InProcess = ~/ponte_teste/bin/python · ponte sum=6 ✓
→ toolboxes: Deep Learning | MATLAB | Optimization | PCT | Statistics
  (Optimization = fmincon sqp do GP_Train ✓; Statistics = normcdf/lhsdesign ✓)
PY -c "import pyarrow, numpy" → pyarrow 25.0.0, numpy 2.4.6 ✓ (env-main)
```
Nenhum bloqueio; sessão liberada.

## 1. PASSO 0 — contexto lido (na ordem prescrita, e SOMENTE ele)

1. `HANDOFF_MESTRE.md` (§10/§11) · `handoff/R1-c217.md` (receita N.0/D61/D89) ·
   `handoff/R1-b1.md` + `R1-e7.md` (writer O(n), padrão ensure_paths, lição sombra).
2. `claude_code_context/CLAUDE.md` inteiro.
3. Linha R1-c238 do `cards/INDEX.md`.
4. `10_rodada1_matlab/00_contrato_rodada1.md` (N.0) + `alg_c238_eim.md` INTEIRO;
   o bundle cita o N.5 → li a **seção N.5 da SPEC por grep** (linha 2169: os 8 pontos).
5. `00_fundacao/01_regras_globais.md` + `03_contrato_export.md` (§17 + S.7).
6. Código REAL do c238 (`MultiObjective_EIM.m`, `GP_Train.m`, `GP_Predict.m`,
   `Infill_EIM.m`, `Optimizer_GA.m`, `Paretoset.m`) + infra existente
   (`run_b1`/`run_e7`/`ensure_paths_*`, `FEBudget.m`, `RunBuffer.m`, `hook_output.m`,
   `b1_instrument.m` como molde, `accept.py`, `preflight.py`, `anchors.json`,
   `repos.lock`, `params.json`). Conferências prévias que pouparam erro:
   - `GP_Predict.m:22` JÁ é `sqrt(max(mse,0))` stock (guard s<0 não precisou de patch).
   - `params.json.por_config.c238` = ARD θ 1×D / θ0=1 / [1e-3,1e3] / GA 10D×200 —
     bate com o call-site do script (θ vetorial) → GP_Train chamado com vetores.
   - preflight anchor-check é `expect_before in txt` PRIMEIRO → o comentário-marcador
     do patch NÃO pode conter o literal `Hypervolume(`.
   - line endings do c238 = LF (a armadilha CRLF do e7 não se aplica).

## 2. PASSO 1 — plano (mostrado antes de codar; segui direto, D81 armado)

(a) embrulho classdef N.5 com DoE do artefato + FEBudget/ponte; (b) âncora
`c238-hypervolume-rm` concretizada com comentário-marcador (⚠ veto); (c) varredura de
sombra: chamadas do c238 ÚNICAS, mas sombra REVERSA achada (§3); (d) `run_c238` +
`c238_instrument` + validação MMF1/ZDT1/DTLZ2 + regressão total. Sem ambiguidade de
SPEC em nenhum ponto → nenhuma parada D81 foi necessária na sessão inteira.

## 3. Varredura de sombra de path (obrigatória — resultado integral)

`find algorithms -name '<basename>'` p/ cada arquivo chamado/patchado:

| basename | ocorrências | veredito |
|---|---|---|
| GP_Train.m / GP_Predict.m / Infill_EIM.m / Optimizer_GA.m / Paretoset.m / MultiObjective_EIM.m | **1** (só c238_EIM) | sem sombra p/ DENTRO ✔ |
| EIM.m | 0 (novo — nome livre na árvore) | ✔ |
| **UniformPoint.m** | **3**: c238_EIM + PlatEMO 4.15 + CLMEA 4.1 | ⚠ **SOMBRA REVERSA** |
| **DTLZ2.m** | **3**: c238_EIM + PlatEMO + CLMEA | ⚠ idem |
| Hypervolume.mexw64 | 1 (c238) | morto pelo patch |

A sombra reversa: `ensure_paths_c238` E o próprio `ALGORITHM.Solve:81`
(`addpath(fileparts(which(class(obj))))`) PREPENDAM `c238_EIM/` e nunca removem →
um run posterior de b1/b3/e7/pisos no MESMO processo resolveria `UniformPoint`
(chamado DIRETO pelos adapters run_b1:577/run_e7:1062) p/ a cópia simplificada do
Zhan — corrupção silenciosa. **Fix:** `onCleanup(@() rmpath_quiet(c238dir))` no
run_c238 (sai do path em QUALQUER saída). Durante o run do c238 nada consome
UniformPoint/DTLZ2 → precedência temporária inócua. Asserts `which` dos 6 nomes
ficam de rede p/ sombras futuras.

## 4. Implementação (ordem real dos patches/commits)

1. **`MultiObjective_EIM.m:40/:64`** — âncora: 2 linhas `Hypervolume(` → comentário-
   marcador (sem o literal, §1). Verificado: `grep "Hypervolume(" → exit 1`, marcador ×2.
2. **`Infill_EIM.m`** — assinatura `[y,u,s,n_nan]` + guard `EIM(isnan(EIM))=0` pós-:15.
3. **`Optimizer_GA.m`** — assinatura `[best_x,best_y,pop_vari,pop_fitness]`.
4. **`EIM.m`** (novo) — classdef N.5; pontos-chave além do óbvio:
   - front ND via `Paretoset(sample_y)` sobre o y **CRU** (script :37/:61; min-max é
     monótono → mesmo ND);
   - dedup `unique(...,'rows','stable')` SÓ p/ o conjunto de TREINO (guard chol);
     min/max/front saem da amostra CHEIA (invariantes a duplicata — fidelidade);
   - `criterion = Algorithm.ParameterSet('Euclidean')` (var real, L.9);
   - sync D89 pós-init E pós-infill; stall counter (D60-c, só loga);
   - instrumentação = 1 chamada extra `Infill_EIM(ga_pop,...)` pós-GA (0 FE) +
     `min_dist` do infill (telemetria B10.7).
5. **`run_c238` + `ensure_paths_c238` + `rmpath_quiet`** em `src/experiment.m`
   (corpo = cópia b1/e7) + `case 'c238'`.
6. **`src/c238_instrument.m`** (molde b1_instrument): ③ pop final do GA (mu/sigma POR
   OBJETIVO no espaço min-max; transf_params={min,range}; rsi nullable), jsonl
   `c238_gen` (S.7 completo), timing §17.6, eventos guard.
7. **anchors.json** concretizada + `preflight.py` → `c238-hypervolume-rm APLICADO`, exit 0.

## 5. Validação — CADA comando rodado e seu resultado

**Runs MATLAB completos (semente 0):**
```
experiment('c238','MMF1',0,'main','data')  → status=ok, wall 8 s,  FE=61,  cp_ok=1, cache_hits=1
experiment('c238','DTLZ2',0,'main','data') → status=ok, wall 686 s, FE=371, cp_ok=1, cache_hits=1
experiment('c238','ZDT1',0,'main','data')  → footer ok, FE=929, cp_init=true, cache_hits=1,
                                             wall 14.128 s (header→footer; ~3h55)
```
**Gate objetivo (env-main):**
```
PY scripts/accept.py R1-c238 --alg c238 --problema MMF1  --semente 0 → exit 0 (VERDE)
PY scripts/accept.py R1-c238 --alg c238 --problema DTLZ2 --semente 0 → exit 0 (VERDE)
PY scripts/accept.py R1-c238 --alg c238 --problema ZDT1  --semente 0 → exit 0 (VERDE)
  (cada um: 4 saídas ✓ · FE=31D−1 derivado das colunas da ① ✓ · CP-init hash=sidecar ✓)
```
**Regressão total:**
```
PY scripts/accept.py F0-0{1,2,3,4}                    → exit 0 ×4
accept_r1_00('MMF1',0,'data') [MATLAB, stub re-RODADO] → PASS=7 FAIL=0
PY scripts/accept.py R1-{c217,c141,b3,b4,b1,e7} × {MMF1,ZDT1,DTLZ2} → exit 0 ×18
python3 scripts/preflight.py                           → exit 0 (APLICADO ×9, STOCK resto)
```
**Auditoria pyarrow (env-main; igualdades EXATAS, não aproximadas):**
| run | ① | ② (=Σ|pop| fechado) | ③ (=iters×10D) | timing n_acum | guards |
|---|---|---|---|---|---|
| MMF1 | 61 (21+40) | 1.681 = (21+61)·41/2 | 800 = 40×20 | 21→60 | cache_hit ×1 |
| DTLZ2 | 371 (131+240) | 60.491 = (131+371)·241/2 | 28.800 = 240×120; mu_2 100% (M=3) | 131→370 | cache_hit ×1 |
| ZDT1 | 929 (329+600) | 378.029 = (329+929)·601/2 | 180.000 = 600×300 | 329→928 | cache_hit ×1 |

Schema ③ conferido coluna-a-coluna (§17.2/C1/C3): `pred_tipo=valor`,
`modelo=OK-Forrester`, `espaco=transformado`, `transf=minmax`,
`transf_params={min,range}` (len=M), `real_solution_id` double+NaN (fallback R1-00),
`geracao` int32. Manifestos `status=ok` nos 3.

**Números-guia (D97):** ZDT1 IGD_raw **4,9908e-2** |ND|=27 (front analítico 10k) ·
DTLZ2 **2,3032e-1** |ND|=57 (das-dennis 5151→esfera) · MMF1 |ND|=16 (IGDX pós-hoc D99).
Guards de mecanismo **0 disparos em 880 iterações** (n_range0=0, n_eim_nan=0, sem dup).

## 6. Verificação adversarial (workflow 19 agentes: 3 lentes → dedup → 2 refutadores/achado)

- **fidelidade-stock: 0 achados** (o embrulho não altera decisão nenhuma; patches são
  só-leitura; dedup=identidade sem duplicata; NaN-guard inerte sem NaN).
- **Sobreviventes (3, todos MINOR):**
  1. `Infill_EIM.m:25` — **crash latente STOCK** (|front ND|=1 → y escalar →
     `Optimizer_GA:17` estoura). CONFIRMADO empiricamente pelos 2 refutadores
     (linha byte-idêntica ao stock). **Não consertei** (não sancionado; análogo ao
     crash latente do b3) — documentado no handoff §8.5a; se disparar = falha honesta.
  2. `EIM.m` — objetivo-constante: `max(range,eps)` evita o NaN mas a coluna vira 0
     exato → `sigma2=0` → `lnL=+Inf` → **fmincon aborta** ANTES do instrument → o
     evento guard_range se perderia. **Fix de instrumentação aplicado:** guard_range
     emitido NA DETECÇÃO (via `logger` no `Problem.data`); o abort do fmincon segue
     sendo falha honesta (consertá-lo = decisão de fidelidade do autor).
  3. `run_c238` pós-Solve — fid do jsonl sem fclose se o EXPORT falhar. **Padrão
     herdado idêntico aos 6 runners anteriores** → não mudei unilateralmente;
     nota de infra no handoff §8.5c.
- **Refutados (exemplos):** "fprintf órfão no script" (comportamento exatamente o
  sancionado pela âncora; script nunca roda); "banda (0,eps) sem log" (semântica
  literal do guard sancionado); "watchdog D60-b não existe" (é citação da SPEC, rede
  da BATERIA, não deste cartão).
- **Pós-fix:** provei que a realocação do guard é NO-OP p/ os runs já feitos
  (`n_range0=0` em 40/40, 240/240 e 600/600 linhas c238_gen) e **re-rodei MMF1**
  com o código final → VERDE (10 s). DTLZ2/ZDT1 não re-rodados: outputs provadamente
  idênticos (o código movido nunca executou) — economia consciente de ~4h.

## 7. Incidentes operacionais (3 — nenhum tocou resultado)

1. **cwd do shell NÃO persiste entre comandos** → o 1º lançamento do ZDT1 e um gate
   morreram no arranque (`Unrecognized function 'experiment'` / arquivo não achado).
   Fix: `cd` ABSOLUTO dentro de cada comando; run relançado limpo do zero.
2. **`matlab -batch ... | tail -N` em background TRAVA no fim**: o MATLAB saiu, mas os
   helpers `MathWorksServiceHost` herdam o write-end do pipe → o `tail` nunca vê EOF
   (ficou 4h28 pendurado com o run já íntegro). Diagnóstico por pstree/lsof; task
   encerrada; **nada perdido** (término monitorado pelo footer do `.jsonl`, a fonte
   da verdade). Lição p/ os próximos cartões MATLAB: redirecionar p/ ARQUIVO.
3. **`handoff/R2-c262.md` untracked apareceu** durante a sessão (sessão paralela R2,
   conforme o plano de paralelismo do autor) — **intocado**, fora dos meus commits.

## 8. Custo medido (p/ o piloto de timing D84/§22.5)

ZDT1 (D=30): **14.128 s** (~3h55) — **novo pior-caso de wall da R1** (antes: e7
4.343 s). Decomposição: loop 163 min (fit mediana 11 s/iter, max 31 s — fmincon
20D=600 avaliações da verossimilhança com chol n×n POR objetivo; busca mediana
5,6 s/iter, max 15,2 s — 60.000 GP_Predict batched/iter); ~70 min de overhead
(Population/③/hook/instrument). Extrapolação: **30 sementes ZDT1 ≈ 118 h/core**;
DTLZ2 686 s → ~5,7 h/30 sementes; MMF1 desprezível. Recomendação p/ o M8: c238
nos problemas D=22–30 é candidato a worker dedicado de longa duração.

## 9. Entregas e estado final

- **Commits (lista explícita, nenhum blob):** `f65a17c` (EIM.m novo + 3 patches
  c238_EIM) · `82f4d47` (run_c238 + c238_instrument + anchors.json + repos.lock
  re-hashado via `preflight --write`, precedente c141) · `8ea7478` (handoff +
  cartão ✅ no INDEX). Branch `experiment/definitive_algorythms`.
- **Sinalizações p/ VETO do autor** (handoff §8.2): âncora concretizada · ③
  minmax/D47 (precedente e7) · `'N',100` inerte (N.5-2) · rmpath via onCleanup.
- **M3 (R1): 7 de 9** — c217, c141, b3, b4, b1, e7, **c238** ✅; faltam pisos, e74
  (N.0-4.1, árvore 4.1, worker dedicado), e103 (N.3, worker dedicado).
- Fidelidade: **não julgada** (D97) — instrumentação completa entregue p/ a
  validação manual em lote do autor (D97, fim da onda).
