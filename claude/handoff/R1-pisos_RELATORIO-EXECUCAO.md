# R1-pisos — RELATÓRIO DE EXECUÇÃO da sessão (narrativa do processo, p/ a torre)

> Companion do `handoff/R1-pisos.md` (que documenta o **resultado**). Este documenta o **processo**:
> o que foi rodado, em que ordem, o que deu errado no caminho e como foi resolvido. Data: **2026-07-18**.
> Commits da sessão: `7170fb7` (docs N=20) · `906343c` (adapter) · `349aabb` (handoff).

---

## 0. Ambiente (D81 — verificado ANTES de qualquer código)

Rodado via script em arquivo (`scratchpad/gate_env.m`), MATLAB `-batch`, saída redirecionada p/ arquivo
(nunca pipe — lição das sessões anteriores sobre o `MathWorksServiceHost`).

```
MATLAB    = 25.1.0.2973910 (R2025a) Update 1
PYENV_VER = 3.11
PYEXEC    = /Users/gmello/ponte_teste/bin/python
EXECMODE  = InProcess
BRIDGE_SUM = 6                      ← double(py.numpy.array([1,2,3]).sum())  ✅ GATE VERDE
```

Confirmado no mesmo gate que as 4 classes de piso e os utilitários resolvem para a árvore 4.15:
`NSGAII`, `NSGAIII`, `MOEAD`, `SMSEMOA`, `NDSort`, `CrowdingDistance`, `UserProblem`, `OperatorGA`.

**Descoberta antecipada no gate (mudou o desenho):** `UniformPoint(20, M)` devolve
**M=2 → 20** mas **M=3 → 15** (o lattice das-dennis arredonda p/ BAIXO: H=4→15 ≤ 20; H=5→21 > 20).
Ou seja, NSGA-III e MOEA/D rodam com **N efetivo 15** em M=3. Tratado pelo precedente §6.3 (registrar o
N efetivo no manifesto), não como erro.

---

## 1. PASSO 0 — contexto lido (na ordem prescrita, e SOMENTE ele)

`HANDOFF_MESTRE.md` (§10/§11) → `handoff/R1-c217.md` → `handoff/R1-c238.md` → `claude_code_context/CLAUDE.md`
→ a linha `R1-pisos` de `cards/INDEX.md` (só leitura) → `10_rodada1_matlab/00_contrato_rodada1.md` (N.0)
→ **`10_rodada1_matlab/alg_pisos_online.md` INTEIRO** → `00_fundacao/01_regras_globais.md` +
`03_contrato_export.md`. Greps pontuais na SPEC só para §22.6/D65/§6.3/§6.4. **Nenhum `alg_*.md` de
outro algoritmo foi aberto.**

Leitura adicional de código, dentro da faixa: `src/experiment.m` (dispatch + `run_b3`/`run_c238` como
molde + os writers), `src/hook_output.m`, `src/FEBudget.m`, `algorithms/_PlatEMO/.../{NSGAII,NSGAIII,MOEAD,SMSEMOA}.m`,
`ALGORITHM.m` (`NotTerminated`), `UserProblem.m` (`Initialization`), `PROBLEM.m`, `scripts/accept.py`,
`claude_code_context/gen_bundles.py`, `artifacts/params.json`.

---

## 2. O BLOQUEIO D81 — e por que a sessão parou antes de codar

`alg_pisos_online.md` prescreve "N por config", mas o N estava em **conflito triplo dentro da SPEC**:

| Fonte | Valor | Precedência |
|---|---|---|
| §6.3 (tabela D20) | `100` | corpo |
| §3.2 / §6.4 / `params.json` | `~20–25` "calibrado no piloto" | corpo / artefato |
| **D65** (Anexo D) | `{10,20,30,50}` por varredura, **"supersede o '100' e o '~20'"** | **Anexo D — vence** |

E a varredura da D65 é o **`SUB-varN`**, que em `cards/INDEX.md:54` está **depende-de `R1-pisos`** →
circularidade estrutural. **Nenhum N estava cravado, e o cartão não podia inventar um** (D81).

**Evidência que levei ao autor** (calculada, não opinada): com `31D−1 = 11D−1 [DoE] + 20D [infills]`, as
gerações são `20D ÷ N`, logo

| N | MMF1 (D=2) | DTLZ2 (D=12) | ZDT1 (D=30) |
|---|---|---|---|
| 20 | 2 ger. | 12 | 30 |
| 100 | **infactível** (pop 100 > DoE de 21 pts; 40 infills < 1 geração) | 2,4 | 6 |

**Primeira pergunta foi mal formulada** — o autor respondeu *"com essa descrição eu não entendi nada"*.
Reformulei do zero (explicando o que é o N, por que é o único botão do piso, por que importa para a
régua, e a tabela de gerações). **Lição p/ a torre: em pergunta de decisão, explicar o MECANISMO antes
das opções — não abrir com os IDs de decisão (D65/§6.3), que são taquigrafia minha, não do autor.**

**Decisão do autor: `N = 20`** + instrução extra: *"crave essa decisão em todas as documentações […]
regularize esse ponto em todos os documentos. justifique o porque escolhemos 20"*.

⚠ **Conflito de faixa, resolvido a favor da instrução explícita:** SPEC/bundles/`params.json` estavam
marcados **PROIBIDO** no prompt da sessão. Executei por ordem direta do autor, com duas salvaguardas:
(1) bundles **nunca** à mão — regenerados por `gen_bundles.py`; (2) commit isolado e reversível.

---

## 3. PASSO 1 — plano (mostrado antes de codar) e o que mudou nele

Plano de 10 linhas apresentado antes de qualquer edição. **Nada nele mudou durante a execução** — as
três peças novas previstas (semeadura §3.2/D88, sync D89 local, ③/timing vazias) foram implementadas
como planejadas. O único ajuste foi de detalhe: o `N efetivo = 15` em M=3, já antecipado no gate (§0).

---

## 4. Regularização documental (commit `7170fb7`)

**Protocolo seguido, na ordem:**

1. **`gen_bundles.py` rodado ANTES de qualquer edição** → `git status` **VAZIO**. Isso provou duas
   coisas: (a) os bundles estavam em sincronia com a SPEC; (b) a regeneração é fiel e byte-idêntica,
   logo **sem risco para a sessão c262 paralela** (que lê `20_rodada2_botorch/`).
2. **5 edições na SPEC** (a fonte única): §3.2 (justificativa integral em 4 pontos), §6.3 (linha dos
   pisos separada da dos SA-MOEA), §6.4 (tabela de Balde B), checklist §22.2, e a linha **D65** do
   Anexo D (adendo registrando o valor provisório em vigor + a circularidade).
3. **`gen_bundles.py` de novo** → churn **exclusivamente** nos 3 bundles de pisos:
   `00_fundacao/01_regras_globais.md` (2 linhas), `10_rodada1_matlab/alg_pisos_online.md` (15),
   `40_subestudos/varredura_N_pisos.md` (11). **`20_rodada2_botorch/` intacto.** ✅
4. **`artifacts/params.json`** — `pisos_online.N` cravado + chave nova `N_nota_supersede`. JSON validado.
5. **`preflight.py` → exit 0** (`pré-voo OK ✓`, 1 deferimento intencional pré-existente).

---

## 5. Implementação (commit `906343c`) — `src/experiment.m`, +313 linhas

**Um único runner para os 4 pisos.** `piso_spec(alg)` isola a única diferença real (classe + `parameter`).
Peças novas, e o *porquê* de cada uma:

| Peça | Por que existe |
|---|---|
| **Semeadura §3.2/D88** | O piso é MOEA puro: não tem arquivo de surrogate para absorver as `11D−1`. Ordem: (1) pré-avalia o DoE INTEIRO pelo `bud` na ordem do artefato → fase `init`, CP-init fecha; (2) `NDSort`+`CrowdingDistance`; (3) `initFcn` devolve os N melhores → o Solve os re-avalia como **cache-hit (0 FE)**. É a única ordem que fecha CP-init **e** orçamento ao mesmo tempo. |
| **`piso_hook` (sync D89)** | Duplo motivo. (a) comum: o `obj.FE` nativo soma cache-hits e correria à frente do saldo (achado do c217). (b) **específico do piso**: `ALGORITHM.Solve` **zera `pro.FE` (`:80`)**, mas o DoE foi gasto **fora** do Solve. Posição validada no código: `ALGORITHM.m:126` chama o `outputFcn` **antes** da checagem `:127`. Mora num wrapper **local** → `src/hook_output.m` (infra transversal) **intocado**. |
| **③/timing vazias + guard** | Bundle: "tabela ③ vazia; série §17.6 vazia". Saem com 0 linhas mas **schema completo**. O invariante é **assertado** (`guard piso_com_surrogate`), não presumido. **Nenhum `pisos_instrument.m`** — não há semântica de surrogate. |
| **`ensure_paths_piso`** | Assert de precedência: a classe + `UniformPoint`/`NDSort`/`CrowdingDistance`/`OperatorGA` **têm** de resolver para `_PlatEMO/`. É a rede contra a sombra reversa do c238 (§7). |

**Patches no PlatEMO: ZERO.** `anchors.json` e `repos.lock` não tocados. Único parâmetro fixado:
`MOEAD 'parameter',{1}` (type=1 PBI **explícito**, S.2#19, ainda que coincida com o default).

---

## 6. Validação — CADA comando rodado e seu resultado

### 6.1 Runs (12) — `experiment(alg, prob, 0, 'main', 'data')`

Ordem serial, um piso validado antes do próximo: `nsga2/MMF1` → gate → os outros 3 em MMF1 → os 8
restantes. **Todos `status=ok`, FE exato, `cp_ok=1`.**

| Piso | MMF1 (61) | DTLZ2 (371) | ZDT1 (929) |
|---|---|---|---|
| nsga2 | 61 · 3 ger · 21 hits · 4,1 s | 371 · 13 ger · 28 hits · 3,4 s | 929 · 31 ger · 32 hits · 0,8 s |
| nsga3 | 61 · 3 ger · 23 hits · 3,0 s | 371 · 19 ger · 28 hits · 0,7 s (**Nef=15**) | 929 · 31 ger · 40 hits · 0,6 s |
| moead | 61 · 3 ger · 23 hits · 0,5 s | 371 · 17 ger · 25 hits · 0,6 s (**Nef=15**) | 929 · 39 ger · **182 hits** · 0,8 s |
| smsemoa | 61 · 3 ger · 23 hits · 0,5 s | 371 · 13 ger · 21 hits · 1,3 s | 929 · 31 ger · 21 hits · 0,6 s |

**Custo: trivial** (< 5 s por run) — os pisos não treinam GP. Para o piloto D84: os 4 pisos × 25
problemas × 30 sementes é ruído perto do c238 (ZDT1 ≈ 3h55/run).

**O `cache-hits ≥ 21` é a prova empírica do desenho:** 1 (probe) + 20 (a população selecionada, que
**bate no cache** ⇒ 0 FE). O excedente são offspring duplicados — e o **`182` do MOEA/D/ZDT1** é a prova
de que o **sync D89 funciona**: sem ele o `obj.FE` teria corrido 182 à frente e o run fecharia em ~747.

### 6.2 Gates (12) — `accept.py R1-pisos --alg … --problema … --semente 0`

```
VERDE nsga2/{MMF1,DTLZ2,ZDT1}   VERDE nsga3/{MMF1,DTLZ2,ZDT1}
VERDE moead/{MMF1,DTLZ2,ZDT1}   VERDE smsemoa/{MMF1,DTLZ2,ZDT1}
=== 12 GATES: 12 verdes / 0 vermelhos ===
```
Cada um checa: 4 saídas + jsonl · FE = 31D−1 · CP-init bit-a-bit.

### 6.3 Auditoria pyarrow dos 12 (`scratchpad/audit_pisos.py`, escrita nesta sessão)

Verifica, por run: ① com `31D−1` linhas, `fase=init` == `11D−1` **e nas primeiras posições**,
`fase=opt` == `20D`, `solution_id` int32 único e ordenado, `x*`/`f*` float32; ② int32 e
`Σ|pop| == num_rows` e **todo id da ② existe na ①** (join íntegro); ③ **0 linhas com schema §17.2
completo**; timing **0 linhas com schema §17.6**; manifesto `status=ok` e `N_nominal=20`; `.jsonl` com footer.

```
run                   ①       ②   ger    ③  tim  Nef  cache
nsga2/MMF1           61      60     3    0    0   20     21
nsga2/DTLZ2         371     260    13    0    0   20     28
nsga2/ZDT1          929     620    31    0    0   20     32
nsga3/MMF1           61      60     3    0    0   20     23
nsga3/DTLZ2         371     285    19    0    0   15     28
nsga3/ZDT1          929     620    31    0    0   20     40
moead/MMF1           61      60     3    0    0   20     23
moead/DTLZ2         371     255    17    0    0   15     25
moead/ZDT1          929     780    39    0    0   20    182
smsemoa/MMF1         61      60     3    0    0   20     23
smsemoa/DTLZ2       371     260    13    0    0   20     21
smsemoa/ZDT1        929     620    31    0    0   20     21

✅ AUDITORIA OK — 12 runs, schema §17.2 conforme, ③/timing vazias
```
② bate exatamente com `n_ger × N_efetivo` (ex.: nsga3/DTLZ2 = 19×15 = 285; moead/ZDT1 = 39×20 = 780).

### 6.4 Regressão

**MATLAB re-executado de verdade** (não só os gates Python), ×MMF1, todos `status=ok fe=61 cp=1`:
`stub`, `c217`, `c141`, `b1`, `b3`, `b4`, `e7`, `c238`.

**Gates Python:** `F0-01-harness`, `F0-02-doe`, `F0-03-export`, `F0-04-metrica`, `R1-00-harness`,
`R1-c217`, `R1-c141`, `R1-b1`, `R1-b3`, `R1-b4`, `R1-e7`, `R1-c238` → **12/12 VERDES**.
`preflight.py` → **exit 0**.
Suíte: `python -m unittest discover -s tests` → **`Ran 82 tests … OK (skipped=1)`**.

> Nota: `pytest` **não existe** no env-main; a suíte roda por `unittest`. Registrado p/ as próximas sessões.
> Não rodei gates do c262 (sessão ativa), conforme instruído — a suíte inclui `test_c262.py`, que é
> execução read-only de teste, não gate, e passou junto.

### 6.5 IGD_raw p/ o dossiê (`scratchpad/igd_pisos.py`)

Mesma convenção dos handoffs c217/c238 (DTLZ2: das-dennis H=100→5151 pts projetados à esfera; ZDT1:
front analítico 10k). Números na §5 do `handoff/R1-pisos.md`. **Guia, não gate (D97).**

---

## 7. Varredura de sombra de path — resultado integral

- **`NSGAII.m` / `NSGAIII.m` / `MOEAD.m` / `SMSEMOA.m`: ÚNICOS** ✔
- **`EnvironmentalSelection.m`: 156 cópias** — idioma do PlatEMO (uma por algoritmo); a **regra
  same-folder** resolve (`Solve:81` prepende a pasta do próprio algoritmo). ✔
- **`Reduce.m`: 2** (SMS-EMOA + NNDREA-MO) — same-folder. ✔
- **`NDSort`/`CrowdingDistance`: 3 · `UniformPoint`: 3 · `OperatorGA`/`OperatorGAhalf`: 2 ·
  `TournamentSelection`: 4** — extras em `e74_CLMEA/` (4.1, worker dedicado — D95) e `c238_EIM/`.

**O achado que importa:** a **sombra REVERSA do c238 atinge este cartão em cheio**. O handoff do c238 já
previa "um run posterior de b1/b3/e7/**pisos** no mesmo processo resolveria `UniformPoint` p/ a cópia do
Zhan" — e **NSGA-III e MOEA/D chamam `UniformPoint`**. Pior: o `run_piso` chama
`NDSort`/`CrowdingDistance` **direto do adapter** (na semeadura), fora de pasta de algoritmo, logo pela
ordem **global** do path. **Coberto por dois lados:** o `onCleanup(rmpath)` do `run_c238` **e** o assert
de precedência do `ensure_paths_piso` (se o cleanup falhar, o piso falha honestamente).

---

## 8. Incidentes operacionais (5) — nenhum tocou resultado

1. **`matlab -batch` com string multilinha** (heredoc) → `"No MATLAB command specified"`. **Fix:** script
   `.m` em arquivo + `matlab -batch "run('…')"`. **Vale como lição de infra para as próximas sessões.**
2. **Bug MEU no script de auditoria:** procurei `…__manifest.json`; o real é `…**.**manifest.json`
   (`nm_manifest_path`). Corrigido; auditoria re-rodada verde.
3. **Bug MEU no laço bash da regressão** (`set -- $pair` mal encadeado) → reportou **7 falsos
   vermelhos** nos gates dos algoritmos. Detectado porque rodei um deles isolado e deu **exit 0**.
   Laço reescrito → 7/7 verdes. **Lição: nunca aceitar um bloco de vermelhos sem reproduzir um deles
   isolado.**
4. **Aborto silencioso do MATLAB durante o `b4`** no 1º lote longo de regressão (8 algoritmos numa
   sessão): sem erro, sem resultado, exit 0. **Investigado até a raiz e NÃO é regressão deste cartão**
   — o b4 rodou verde **3× depois** (com e sem `maxNumCompThreads(1)`) e o único crash dump em disco é
   de **16/Jul** (sessão anterior), com stack em `ddux::matlab::LicenseLogger::initialize()` numa thread
   do pool = **telemetria/licenciamento da MathWorks**. **Hazard p/ a bateria: lotes longos de MATLAB
   podem morrer sem aviso ⇒ conferir o footer do `.jsonl` de cada run, nunca o exit code do processo.**
5. **Hipótese minha que se provou ERRADA, e fica registrada:** cheguei a atribuir o incidente 4 ao
   `maxNumCompThreads(1)` (D79) e ao crash dump. As duas atribuições caíram no teste — o dump era de
   dois dias antes e o b4 roda verde com `maxNumCompThreads(1)`. **Registrado porque uma conclusão
   errada dita com confiança teria plantado um falso hazard de D79 na SPEC.**

---

## 9. O que NÃO foi feito (declarado, não omitido)

1. **Revisão adversarial multi-agente** — a sessão do c238 rodou uma (19 agentes, 3 lentes). **Esta não
   rodou.** É a única peça do precedente da casa que ficou de fora.
2. **`experiments.m` (despachante) não tocado** — fora da faixa. Os 4 pisos **não estão no roster
   default**; a bateria por `experiments(...)` ainda não os pega. Chamada direta funciona.
3. **`cards/INDEX.md` não tocado** — por design (a torre marca).
4. **Fidelidade/convergência não julgada** — D97, é do autor. Nos pisos isso é mais simples: stock, sem
   patch; o que cabe julgar é sanidade de convergência (§17.5.1 item 5).
5. **Só semente 0 × 3 problemas** — exatamente o escopo do cartão.
6. **N=20 é PROVISÓRIO** — o `SUB-varN` (D65) reconfirma ou substitui antes da bateria.

---

## 10. Estado final

| Item | Estado |
|---|---|
| 12 runs | ✅ FE exato, CP-init ✅ |
| 12 gates `accept.py` | ✅ exit 0 |
| Auditoria pyarrow | ✅ 12/12, schema §17.2 |
| Regressão (F0 + R1-00 + 7 algs + preflight + suíte 82) | ✅ verde |
| Varredura de sombra | ✅ registrada; hazard reverso do c238 coberto 2× |
| Commits | `7170fb7` docs · `906343c` código · `349aabb` handoff |
| Árvore | limpa (só `handoff/R2-c262.md` untracked — do c262, nunca tocado) |
| Ritual anti-mistura | aplicado nos 3 commits (add → `git diff --cached --name-only` → commit) |

**Arquivos alterados no total: 7** (+630/−15) — 5 de documentação, `src/experiment.m`, `handoff/R1-pisos.md`.
