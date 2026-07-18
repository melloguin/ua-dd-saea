# handoff/R1-pisos.md — Rodada 1: os 4 PISOS ONLINE (NSGA-II, NSGA-III, MOEA/D type=1, SMS-EMOA)

**Data:** 2026-07-18 · **Env:** MATLAB **R2025a Update 1** (Mac arm64) + PONTE `pyenv` InProcess
(`~/ponte_teste/bin/python`, 3.11; `py.numpy.array([1,2,3]).sum()` → **6** verificado ANTES — D80/D81).
Leitor Python independente no **env-main** (`.../mestrado_experimentos_dissertacao/bin/python`).
Nenhuma toolbox extra: os pisos são MOEAs puros (sem DL/Optimization).

**Gate objetivo (encanamento, D97):** `accept.py R1-pisos --alg {nsga2,nsga3,moead,smsemoa}
--problema {MMF1,DTLZ2,ZDT1} --semente 0` → **exit 0 (VERDE) nos 12**: 4 saídas, **FE = 31D−1 EXATO**,
CP-init bit-a-bit. ✅
**Fidelidade:** não se aplica no sentido dos SA-MOEA — os pisos são **stock do PlatEMO 4.15, sem patch
por design**. O que instrumentei é **sanidade de convergência** para a sua leitura (D97/§17.5.1).
**Regressão:** F0-01/02/03/04, R1-00 (stub), c217, c141, b1, b3, b4, e7, c238 (todos ×MMF1) seguem
VERDES; `preflight.py` exit 0; suíte **82 testes OK** (1 skip).

**Escopo:** o 8º cartão da R1 e o **último antes de e74/e103**. Os pisos não são algoritmos do estudo —
são a **RÉGUA** (§3.2/D25): respondem *"o surrogate compra alguma coisa, afinal?"*. Um cartão, 4 configs,
**um único runner** (`run_piso`), infra transversal INTOCADA.

---

## 0. ⚠ A DECISÃO QUE ESTE CARTÃO DESATOU — `N = 20` cravado

O cartão começou **bloqueado** (D81): o `N` dos pisos estava dito de **três formas conflitantes** dentro
da própria SPEC, e a fonte de maior precedência delegava a decisão a um cartão que depende deste.

| Onde | Dizia |
|---|---|
| §6.3 (tabela D20) | pisos `N = 100` (default PlatEMO) |
| §3.2 / §6.4 / `params.json` | `N ≈ 20–25`, "calibrado no piloto" |
| **D65** (Anexo D — precede as duas) | `N ∈ {10,20,30,50}` por varredura, **"supersede o '100' e o '~20'"** |

E a varredura da D65 é o **`SUB-varN`**, que em `cards/INDEX.md:54` está como **depende-de `R1-pisos`** —
circularidade: o piso precisa existir para ser varrido.

**Você cravou `N = 20`** (2026-07-18). A justificativa em 4 pontos ficou escrita na SPEC §3.2:

1. **Precedente canônico** — é o valor do **Knowles/ParEGO**, que varreu 10–50 e elegeu 20 para o
   NSGA-II puro sob orçamento minúsculo. É o precedente que o próprio protocolo já declara seguir.
2. **Interseção das fontes vivas** — 20 é o **único** valor que satisfaz ao mesmo tempo a faixa `~20–25`
   e o conjunto `{10,20,30,50}` da D65 ⇒ **não introduz valor novo**, elege o ponto comum.
3. **Viabilidade no grid inteiro** — `20 ≤ 11D−1` para todo `D≥2` (o menor DoE é 21, em D=2) ⇒ roda nos
   25 problemas sem teto anti-crash. Já `N=100` é **infactível** em D=2 (população 100 > DoE de 21
   pontos; 20D=40 infills não fecham uma geração) e degenerado no resto (2–6 gerações).
4. **Densidade de gerações** — 2 (D=2), 12 (DTLZ2 D=12), 30 (ZDT1 D=30): evolução real em todo o grid
   sem colapsar diversidade (o que `N=10` comprometeria nos vetores de referência em M=3).

**Regularizado em 5 pontos** (commit `7170fb7`): SPEC §3.2, §6.3, §6.4, checklist §22.2 e a linha D65 do
Anexo D — mais `artifacts/params.json`. Os bundles **não** foram editados à mão: rodei `gen_bundles.py`
(verificado **no-op** antes da edição ⇒ o churn é exclusivamente dos pisos; `20_rodada2_botorch/`, a
faixa do c262, ficou intacta).

> ⚠ **PARA O SEU VETO:** eu toquei SPEC/bundles/`params.json`, que o prompt desta sessão marcava como
> PROIBIDO na minha faixa. Fiz por instrução explícita sua ("regularize esse ponto em todos os
> documentos"). Se preferir reverter, é `git revert 7170fb7` — o commit do código (`906343c`) é
> independente e não depende dele.

**O `SUB-varN` reconfirma ou substitui** o 20 antes da bateria. Se eleger 20 para alguma faixa de D, os
runs deste cartão **já são os definitivos**.

---

## 1. Resultado do gate (semente 0)

| Piso | Problema | D | M | maxFE | FE final | EXATO | N nom | **N efetivo** | n_ger | cache-hits | wall | accept.py |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **NSGA-II** | MMF1 | 2 | 2 | 61 | **61** | ✅ | 20 | 20 | 3 | 21 | 4,1 s | **VERDE** |
| | DTLZ2 | 12 | 3 | 371 | **371** | ✅ | 20 | 20 | 13 | 28 | 3,4 s | **VERDE** |
| | ZDT1 | 30 | 2 | 929 | **929** | ✅ | 20 | 20 | 31 | 32 | 0,8 s | **VERDE** |
| **NSGA-III** | MMF1 | 2 | 2 | 61 | **61** | ✅ | 20 | 20 | 3 | 23 | 3,0 s | **VERDE** |
| | DTLZ2 | 12 | 3 | 371 | **371** | ✅ | 20 | **15** | 19 | 28 | 0,7 s | **VERDE** |
| | ZDT1 | 30 | 2 | 929 | **929** | ✅ | 20 | 20 | 31 | 40 | 0,6 s | **VERDE** |
| **MOEA/D** | MMF1 | 2 | 2 | 61 | **61** | ✅ | 20 | 20 | 3 | 23 | 0,5 s | **VERDE** |
| | DTLZ2 | 12 | 3 | 371 | **371** | ✅ | 20 | **15** | 17 | 25 | 0,6 s | **VERDE** |
| | ZDT1 | 30 | 2 | 929 | **929** | ✅ | 20 | 20 | 39 | **182** | 0,8 s | **VERDE** |
| **SMS-EMOA** | MMF1 | 2 | 2 | 61 | **61** | ✅ | 20 | 20 | 3 | 23 | 0,5 s | **VERDE** |
| | DTLZ2 | 12 | 3 | 371 | **371** | ✅ | 20 | 20 | 13 | 21 | 1,3 s | **VERDE** |
| | ZDT1 | 30 | 2 | 929 | **929** | ✅ | 20 | 20 | 31 | 21 | 0,6 s | **VERDE** |

**CP-init ✅ nos 12** (hash da ① init == sidecar do DoE, bit-a-bit).

**Leitura das colunas que surpreendem:**
- **`N efetivo = 15` em DTLZ2 (M=3), só NSGA-III e MOEA/D:** os dois chamam `UniformPoint(N,M)`, cujo
  lattice das-dennis **arredonda para BAIXO** (H=4 → 15 ≤ 20; H=5 → 21 > 20). NSGA-II e SMS-EMOA não
  usam vetores de referência e mantêm 20. É o **precedente §6.3 já aceito** ("com N=100 o NBI gera 91,
  não 105 — todos os N efetivos vão para a dissertação"). O N efetivo está no manifesto de cada run.
- **`cache-hits ≥ 21` sempre:** 1 (o probe do construtor) + 20 (a população inicial selecionada, que é
  re-avaliada pelo Solve e **bate no cache** — 0 FE, D89, ver §2). O excedente são offspring duplicados.
- **`cache-hits = 182` no MOEA/D/ZDT1:** ~23% dos 780 offspring foram duplicatas bit-exatas. Causa
  provável: com N=20 a vizinhança do MOEA/D é `T = ceil(N/10) = 2`, minúscula ⇒ os mesmos 2 pais se
  repetem muito. **Não é bug** (é o algoritmo stock + a política D89), mas é o efeito colateral que a
  D89 manda vigiar: duplicata não gasta FE, **gasta o SLOT do infill**. Está logado como evento
  `cache_hit` no `.jsonl`. ⚠ **Este é um dado de entrada para o `SUB-varN`**: o N escolhido mexe
  diretamente no T do MOEA/D e, portanto, na taxa de duplicata.

---

## 2. O desenho — as 3 peças que NENHUM dos 7 fan-outs anteriores tinha

Fora isso, `run_piso` é a receita N.0 do caso-modelo c217 sem desvio (ponte → `load_doe` → `FEBudget`
ANTES do Problem → `rng` DEPOIS do Problem → `save=-K` + `outputFcn` → try/catch `PlatEMO:Termination`
→ export 4 camadas → CP-init → falha honesta). **Um runner só para os 4**: `piso_spec` isola a única
diferença real (a classe PlatEMO + o `parameter`).

### (a) Semeadura §3.2/D88 — o piso não tem onde guardar o DoE

O SA-MOEA absorve as `11D−1` do DoE no seu **arquivo de surrogate**. O piso é MOEA puro: não tem
arquivo. O protocolo Knowles manda partir dos **mesmos** pontos, iniciando a evolução com os
**melhores por não-dominância**, desempate por **crowding distance determinístico** (D88).

A ordem implementada é a **única que fecha CP-init E orçamento ao mesmo tempo**:

1. **Pré-avalia as `11D−1` do DoE pelo `bud`, NA ORDEM DO ARTEFATO** → fase `init` da ①, `11D−1` FE
   gastos, `init_X()` **bit-idêntico ao sidecar** (CP-init fecha exatamente como nos outros 7).
2. **`NDSort` + `CrowdingDistance`** sobre essas `11D−1` → ordem canônica do NSGA-II (frente asc,
   crowding desc, **desempate final por índice** ⇒ totalmente reprodutível).
3. O `initFcn` devolve os **N primeiros dessa ordem** → o `Solve` os re-avalia e eles **batem no cache**
   (0 FE, D89) ⇒ a evolução fica com **exatamente 20D**.

> Por que não "avaliar só os N melhores": não daria. A ① teria `N` linhas de init em vez de `11D−1`, e o
> **CP-init reprovaria** (o hash é sobre o artefato inteiro) — além de violar §5.1 (`maxFE = 11D−1 [DoE]
> + 20D [infills]`). O DoE **é** gasto por inteiro; a seleção decide só **quem entra na população**.

O evento `seeding` do `.jsonl` registra `n_frentes`, `n_frente1` e o booleano `frente1_excede_pop` — que
é exatamente a condição que a D88 previu ("desempate quando a fronteira-1 do DoE excede a população").

### (b) Sync D89 no `piso_hook` — obrigatório aqui por um motivo A MAIS

```matlab
Problem.FE = bud.fe;                              % sync D89
hook_output(Algorithm, Problem, buf, bud, []);    % ② ; ③/timing vazias
```

Nos outros runners o sync existe porque o `obj.FE` nativo **soma cache-hits** e correria à frente do
saldo distinto (o achado do c217: ZDT1 fechava 926 em vez de 929). Nos pisos há um segundo motivo, mais
grave: **`ALGORITHM.Solve` ZERA `pro.FE` (`:80`)**, mas as `11D−1` do DoE foram gastas **FORA do Solve**.
Sem o sync, o `NotTerminated` enxergaria só as 20D da evolução e o `rate` do `save=-K` ficaria fora de
escala.

**Posição verificada no código:** `ALGORITHM.m:126` chama o `outputFcn` **ANTES** da checagem `:127`
(`nofinish = pro.FE < pro.maxFE`) ⇒ sincronizar no hook é lido no MESMO ciclo. Prova empírica: o
MOEA/D/ZDT1 teve **182 cache-hits** e ainda assim fechou **929 exato**.

⚠ O sync mora num **wrapper LOCAL** (`piso_hook`), não em `src/hook_output.m` — infra transversal
**intocada**, zero risco de regressão nos outros 7.

### (c) Sem surrogate — ③ e timing VAZIAS, e isso é ASSERTADO

Conforme o bundle ("tabela ③ vazia; série §17.6 vazia") e S.7 (pisos = "só o mínimo comum" no `.jsonl`).
As duas tabelas saem com **0 linhas mas SCHEMA COMPLETO** (§17.2/§17.6) — a auditoria pyarrow confere
coluna a coluna. **Não fiz `pisos_instrument.m`**: não há semântica de surrogate a instrumentar.
O invariante não é presumido: se `buf.srows`/`buf.trows` vierem não-vazios, dispara o guard
`piso_com_surrogate` no `.jsonl`.

---

## 3. Patches aplicados

**NENHUM.** Os 4 pisos são **stock do PlatEMO 4.15 por design** (o bundle não prevê patch de fidelidade
para eles). `anchors.json` e `repos.lock` **não foram tocados**; `preflight.py` exit 0.

O único parâmetro fixado é o do contrato: **`MOEAD 'parameter',{1}`** = `type=1` (PBI, θ≈5) —
**explícito**, como manda a S.2#19, ainda que coincida com o default do `MOEAD.m:22`. Registrado no
manifesto. `SMSEMOA` é o **PURO** (não o SMS-EMOA-MA surrogate do §3.6). NSGA-II e NSGA-III não expõem
parâmetro.

---

## 4. Varredura de sombra de path (obrigatória — lição R1-e7/S.8)

`find algorithms -name '<basename>'` para cada arquivo que os pisos chamam:

- **`NSGAII.m` / `NSGAIII.m` / `MOEAD.m` / `SMSEMOA.m`: ÚNICOS** na árvore ✔
- **`EnvironmentalSelection.m`: 156 cópias** — é o **idioma do PlatEMO** (cada algoritmo tem a sua). A
  **regra same-folder** resolve: `ALGORITHM.Solve:81` prepende a pasta do próprio algoritmo, então o
  `main` do NSGA-II chama a **sua**. Já provado pelos 7 fan-outs (o c217 também tem a sua). ✔
- **`Reduce.m`: 2 cópias** (SMS-EMOA + NNDREA-MO) — mesma regra same-folder; o SMS-EMOA chama a sua. ✔
- **`NDSort` / `CrowdingDistance` / `OperatorGA` / `OperatorGAhalf` / `TournamentSelection` / `UniformPoint`:**
  as cópias extras vivem em `e74_CLMEA/` (árvore 4.1, isolada em worker dedicado — D95) e em
  `c238_EIM/` (`UniformPoint.m` do Zhan).

> ⚠ **O risco real é a SOMBRA REVERSA do c238**, e ela **atinge este cartão em cheio**: o handoff do
> c238 já previu que "um run posterior de b1/b3/e7/**pisos** no MESMO processo resolveria `UniformPoint`
> para a cópia do Zhan" — e **NSGA-III e MOEA/D chamam `UniformPoint`**. Além disso o `run_piso` chama
> `NDSort`/`CrowdingDistance` **diretamente do adapter** (na semeadura), fora de qualquer pasta de
> algoritmo, logo pela ordem GLOBAL do path.
> **Coberto por dois lados:** (1) o `onCleanup(rmpath)` do `run_c238` tira aquela pasta do path ao fim
> do run; (2) o `ensure_paths_piso` **asserta** que a classe do piso + `UniformPoint` + `NDSort` +
> `CrowdingDistance` + `OperatorGA` resolvem para `_PlatEMO/` — se o cleanup do c238 algum dia falhar, o
> piso **falha honestamente** em vez de corromper em silêncio.

---

## 5. Instrumentação e os NÚMEROS DA RÉGUA (para o dossiê)

Por run: **① real** (`31D−1` linhas, init+opt) · **② pop** (membership, todas as gerações) ·
**③ surrogate VAZIA** · **timing §17.6 VAZIA** · **`.jsonl`** (header + `seeding` + eventos `guard`/
`cache_hit` + footer — o mínimo comum da S.7).

**`IGD_raw` (semente 0) — GUIA, não gate (D97).** Mesma convenção dos handoffs c217/c238, para serem
diretamente comparáveis: DTLZ2 ref = das-dennis H=100 (5151 pts) projetado à esfera unitária; ZDT1 ref =
front analítico `f2 = 1 − √f1` (10k pts). MMF1 não tem IGD (MMF ⇒ **IGDX pós-hoc, D99**).

| Piso | DTLZ2 (d=12, M=3) · IGD_raw | \|ND\| | ZDT1 (d=30, M=2) · IGD_raw | \|ND\| | MMF1 \|ND\| |
|---|---|---|---|---|---|
| NSGA-II | 3,4641e-1 | 39 | 6,1746e-1 | 18 | 13 |
| NSGA-III | 2,4954e-1 | 47 | 7,5234e-1 | 17 | 8 |
| MOEA/D | 3,5218e-1 | 35 | **1,8881e+0** | 13 | 9 |
| **SMS-EMOA** | **2,1960e-1** | 40 | 6,8975e-1 | 34 | 13 |

**A régua contra os SA-MOEA já medidos** (números dos handoffs anteriores, mesma semente e convenção):

| | DTLZ2 (d=12) | ZDT1 (d=30) |
|---|---|---|
| **melhor piso** | **2,1960e-1** (SMS-EMOA) | **6,1746e-1** (NSGA-II) |
| c238 EIM | 2,3032e-1 | **4,9908e-2** |
| c217 PC-SAEA | ≈2,63e-1 | — |

> ⚠ **CAVEATS (D97 — eu não julgo, só entrego o número):**
> 1. **É 1 semente (0), não a mediana de 30.** Nada aqui é conclusão; a §14/§15 é que decide, com as 30.
> 2. **Os dois problemas contam histórias opostas, e isso é informação, não ruído.** No **ZDT1 (d=30)** o
>    surrogate abre **uma ordem de grandeza** (c238 4,99e-2 × melhor piso 6,17e-1) — coerente com o
>    regime: 600 infills / N=20 = 30 gerações é pouquíssimo para um MOEA puro em 30 dimensões. No
>    **DTLZ2 (d=12)** os dois **encostam**, e o SMS-EMOA fica **numericamente à frente** do c238 e do
>    c217. Se isso se sustentar nas 30 sementes, é exatamente o achado que o §3.2 diz que a régua existe
>    para produzir — e é **material de dissertação**, não defeito.
> 3. **O SMS-EMOA ser o melhor piso no DTLZ2 é o par mais sensível do estudo:** ele é o espelho mecânico
>    do **c262 qNEHVI** (D25 — mesma seleção por HV, um com GP, outro sem). Quando o c262 fechar (sessão
>    paralela), esse é o primeiro contraste a olhar.
> 4. **IGD é raw** (fora do `metrics.py`, sem a normalização D69) — compute do SEU jeito a partir da ①
>    crua se quiser o número oficial. O endpoint primário é **IGD+** (D70), não IGD.
> 5. **MOEA/D é o pior nos dois**, e no ZDT1 por larga margem (1,89). Olhe junto com os **182 cache-hits**
>    (§1): com N=20 o `T=ceil(N/10)=2` estrangula a vizinhança. É um **efeito do N**, e portanto um dado
>    de entrada direto para o `SUB-varN`.

---

## 6. Como reproduzir

```
# MATLAB (raiz do repo):
addpath('src'); addpath(genpath('algorithms/_PlatEMO/PlatEMO'));
experiment('nsga2','MMF1',0,'main','data')    % idem nsga3 / moead / smsemoa
                                              % idem DTLZ2 / ZDT1

# Python (env-main), gate objetivo:
python3 scripts/accept.py R1-pisos --alg nsga2 --problema MMF1 --semente 0
```

Outputs em `data/experiments/main/{nsga2,nsga3,moead,smsemoa}/` (gitignored — regeneráveis).

---

## 7. Pendências / notas

1. **Commits (2):** `7170fb7` = regularização do N=20 (SPEC + bundles regenerados + `params.json`);
   `906343c` = `src/experiment.m` (os 4 cases + `run_piso`/`piso_spec`/`piso_init`/`piso_hook`/
   `ensure_paths_piso`). Nenhum blob. `cards/INDEX.md` **NÃO tocado** (a torre marca).
2. **`experiments.m` (o despachante) NÃO foi tocado** — está fora da faixa que você me deu. Os 4 pisos
   **não estão no roster default** dele, então a bateria por `experiments(...)` ainda não os pega.
   Chamada direta por `experiment(...)` funciona (é como os 12 runs rodaram). **Ação de 1 linha para
   quem pegar o próximo cartão** (ou para você): incluir `nsga2/nsga3/moead/smsemoa` no roster.
3. **Incidente operacional (transitório, NÃO reproduzível):** no 1º lote de regressão, o processo MATLAB
   **abortou em silêncio** durante o `b4` (sem erro, sem resultado, exit 0). **Não é regressão deste
   cartão** e não é do b4: o b4 rodou **verde 3× depois** (com e sem `maxNumCompThreads(1)`), e o único
   crash dump em disco é de **16/Jul** (sessão anterior), não deste run — seu stack aponta
   `ddux::matlab::LicenseLogger::initialize()` numa thread do pool, ou seja, **telemetria/licenciamento
   da MathWorks**, mesma família do `MathWorksServiceHost` que o protocolo já mandava evitar por pipe.
   Registro como hazard de infra: **lotes longos de MATLAB podem morrer sem aviso**. Mitigação barata na
   bateria: rodar em lotes menores e conferir o **footer do `.jsonl`** de cada run (o manifesto/footer é
   que diz se o run fechou) — nunca confiar no exit code do processo.
4. **Sem `pisos_instrument.m`** — proposital (§2c). Se um dia quiser telemetria de piso (ex.: contagem de
   duplicatas por geração, para o `SUB-varN`), o molde é o `b1_instrument`.
5. **A validação de fidelidade continua SUA (D97).** Nos pisos ela é mais simples — não há mecanismo de
   surrogate a auditar, o código é stock e sem patch. O que cabe julgar é **sanidade de convergência**
   (§17.5.1 item 5): a trajetória melhora? o ND não colapsa? Os `|ND|` da §5 e a ② por geração dão isso.
6. **Entrada direta para o `SUB-varN` (D65):** o N mexe em três coisas que este cartão já mediu — (a) o
   nº de gerações (`20D ÷ N`); (b) o **N efetivo** via lattice em M=3 (20→15 no NSGA-III/MOEA-D); (c) a
   **taxa de duplicata do MOEA/D** via `T = ceil(N/10)`. Sugiro que a varredura reporte os três, não só
   a mediana de IGD+.
