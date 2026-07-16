# handoff/F0-04-metrica.md — Fase 0, cartão 4/4 (esqueleto da métrica + âncora D92) · **FECHA a Fase 0**

**Data:** 2026-07-16 · **Env:** env-main (`.../mestrado_experimentos_dissertacao/bin/python`;
numpy 2.4.6 · pandas 2.3.3 · pyarrow 25.0.0 · pymoo 0.6.2 ✓)
**Gate:** `PY scripts/accept.py F0-04-metrica` → **VERDE, exit 0** ✅
**Escopo:** PURA INFRAESTRUTURA — o **esqueleto** da camada de métrica pós-hoc (§12/§13)
+ a **âncora do smoke** que fecha a Fase 0. **SEM algoritmo, SEM fidelidade** (D97); a
ANÁLISE COMPLETA é do R4, refinada/implementada pelo **AUTOR** (D100). O único gate é o
**objetivo** (D81/D97).

## Resultado (tudo verde)
- `PY scripts/accept.py F0-04-metrica` → **exit 0**. Os 5 checks:
  1. **SMOKE DECISIVO (D92):** HV(front verdadeiro do **BBOB_F1**, normalizado por
     `(ideal,nadir)` da S.5, **ref = 1,1 por coordenada**) = **1,04333** (|Δ|=2,7e-5 <
     tol 5e-4). É a âncora que **FECHA a Fase 0**.
  2. **sanity do FRONT (rotulado, NÃO é o gate — D92):** o MESMO front com ref no nadir
     `(1,0)` = **0,83333** (= 1 − 1/6). Valida a geometria do front; um gate aqui
     reprovaria a métrica D69 correta.
  3. **as 5 métricas rodam + são sãs:** front×front → IGD/IGD+/GD = 0; HV(front) = âncora;
     spacing(uniforme)≈9e-17, spacing(irregular)=0,166 (>0).
  4. **lê a camada ① ponta-a-ponta:** stub ① (objetivos REAIS de MMF1) → normaliza →
     métricas FINAIS + **trajetória** (IGD+ 3,93→0,011 ao crescer os FEs; HV sobe).
  5. **normalização D69 = tabela S.5 congelada:** 25 problemas (= `experiment.ALL_PROBLEMS`);
     o nadir do F1 na S.5 `[82,042; 82,042]` bate com o `true_pareto_front` vivo.
- **62 testes** (`PY -m unittest discover -s tests -t .`) → **OK** (44 F0-01/02/03 + **18
  novos** F0-04). Sem pymoo/pyarrow os testes de métrica **pulam** (padrão do repo).
- **Regressões:** `accept.py F0-01/F0-02/F0-03` exit 0; `preflight.py` exit 0.
- **Verificação numérica da âncora** (independente): HV converge a 1,043333 (= 1,21 − 1/6)
  com a densidade do front — n=10000→1,043300, n=50000→1,043327 (o smoke usa n=50000).

## Arquivos

**Novos:**
- `src/metrics.py` — **o esqueleto da camada de métrica pós-hoc (§12–§13 / D69/D70/D92).**
  - `F_MIN_MAX` — tabela **S.5** congelada `(ideal, nadir CRU)` por problema (25); a margem
    de 10% NÃO está embutida (mora no ref=1,1). `reference_bounds(prob)` a expõe.
  - `normalize(F, ideal, nadir)` = `(f−ideal)/(nadir−ideal)` (**D69**), guarda `range≥1e-12`.
  - `nondominated_front` (reusa `problems._nds_filter` — ENS, mesmo A2).
  - **Métricas** (sobre objetivos JÁ normalizados): `igd`, **`igd_plus` (PRIMÁRIA — D70)**,
    `gd`, `hv(ref_coord=1,1)` — via **pymoo** (lib pinada, D80) — e `spacing` (Schott L1,
    numpy). `hv` de conjunto vazio = 0,0 (HV degenerado é DADO, não NaN — §12.2); `igd`
    vazio = NaN.
  - `reference_set(prob)` — front normalizado + ND + subamostra uniforme (`|R|≈5000`);
    `true_front_raw`, `load_real` (lê a ① via `naming`+pyarrow), `metrics_of_set`,
    `trajectory` (métrica × FEs reais, §13), `metrics_from_real` (ponta-a-ponta).
  - `hv_smoke_bbob_f1()` = **1,0433** (âncora D92) e `hv_front_sanity_bbob_f1()` = **0,8333**
    (sanity rotulado). Constantes `HV_SMOKE_BBOB_F1`, `HV_SANITY_BBOB_F1`, `HV_REF_COORD=1,1`,
    `PRIMARY_METRIC="igd_plus"`, `REF_SET_SIZE=5000`.
  - Import LAZY de pymoo/pyarrow (como `export.py`): `import src.metrics` roda em qualquer
    interpretador com numpy (provado no `python3` base).
- `tests/test_metrics.py` — 18 testes (bounds/normalize + guarda range; âncora 1,0433 e
  sanity 0,8333; front×front=0, HV=âncora, HV/IGD vazios, IGD+≤IGD, spacing uniforme×irregular
  + degenerado; reference_set; **leitura da ①** + `metrics_from_real` + trajetória convergente).

**Modificados:**
- `scripts/accept.py` — branch real do cartão **`F0-04-metrica`** (`check_f0_04`): import-gate
  da métrica + o **smoke HV=1,0433** + sanity 0,8333 (rotulado) + 5 métricas + leitura da ①
  ponta-a-ponta + coerência da S.5. Tolerância da âncora `_TOL_HV_ANCHOR=5e-4`. **NÃO tocou a
  política D97** (só encanamento; nunca fidelidade).
- `cards/INDEX.md` — F0-04-metrica → ✅.

## Contrato para quem CONSOME (R4 · e o piloto de R1/c217 — leia isto)
- **Normalização (D69).** SEMPRE normalize objetivos por `metrics.reference_bounds(problema)`
  = `(ideal, nadir)` da S.5 — **fixo por problema, idêntico para todos** os algoritmos e VMs.
  `nadir` é o CRU (a folga de 10% do HV é o **ref=1,1**, não a normalização). NÃO confundir
  com o `f_max_uso` (nadir+10%) que o **c122** usa na normalização INTERNA do algoritmo (S.5,
  R3) — isso é do algoritmo, não da métrica.
- **Endpoint primário = IGD+** (`metrics.igd_plus`, mediana das 30 sementes — D70). HV
  secundária; ref-point **1,1 por coordenada** (`HV_REF_COORD`).
- **API do esqueleto:** `metrics_from_real(exp,alg,problema,semente,data_root=...)` lê a ① do
  run e devolve `{"final": {igd,igd_plus,hv,gd,spacing,n_nd}, "trajectory": [...]}`. Consome
  `naming` (caminho da ①) e o schema §17.2 (colunas `f0..f{M-1}`) do F0-03. `metrics_of_set(F,
  problema, ref_norm=)` mede um conjunto avulso; `trajectory(F, fe_index, problema)` é a §13.
- **Reference set (§12.2):** `reference_set(problema)` já entrega um `|R|≈5000` normalizado.
- **Âncora do gate objetivo (R4):** o smoke da métrica é `hv_smoke_bbob_f1()` = 1,0433 (D92) —
  o mesmo valor que o cartão R4 deve reproduzir.

## O que é ESQUELETO aqui × o que é do R4 (D100 — o autor refina/implementa)
- **Feito (encanamento):** as 5 métricas + normalização D69 + reference set + leitura da ① +
  trajetória (§13) + a âncora D92.
- **Herdado pelo R4 (NÃO feito — camada de análise):** agregação das 30 sementes
  (mediana+IQR, §13); os **4 testes** estatísticos (§14: Wilcoxon rank-sum, Friedman+Nemenyi+
  Demšar+Holm por métrica, signed-rank pareado, bayesiano de sinais-postos rope=0,05);
  **online (17) × offline (5) em quadros SEPARADOS** (D70); a **análise por característica**
  (matriz 25×8, §15/D71 — a matriz é re-derivada e congelada pelo autor, D98); **IGDX** p/ os
  4 MMF (D99); **attainment worst-case** 2-obj + GHV opcional (§13); o **re-espaçamento fino**
  do reference set (arc-length nos 2-obj / Das-Dennis·Riesz nos 3-obj — hoje é subamostra
  uniforme); a nuance **BBOB empírico** (IGD relativo — §12.1, apoiar no HV).

## Caveats / decisões honradas
- **D92:** o gate é **1,0433** (ref 1,1); **0,8333** é só sanity do FRONT (rotulado) — NÃO
  confundido. **D69:** ref 1,1 por coordenada no espaço normalizado. **D70:** IGD+ primária.
  **D80:** métricas via pymoo 0.6.2 (pinado) — **nada instalado** (D81). **D97:** zero
  julgamento de fidelidade. **D100:** só o esqueleto; a análise é do autor.
- **HV degenerado (§12.2):** `hv` retorna 0,0 (dado, não NaN) — sob `31D−1` isto pode morder
  nos 3-obj difíceis (DTLZ1/3); a leitura apoia-se no IGD+.
- **F_MIN_MAX é a S.5 congelada** (BBOB do cache i1). Se o autor regenerar o cache do BBOB
  (D98-adjacente), **re-derivar a tabela** (script: instanciar a classe, `true_pareto_front(1000)`,
  min/max por coluna). O check (6) do gate cruza a S.5 com o front vivo do F1.
- **spacing = Schott L1** sobre objetivos normalizados (documentado no código); se o R4 preferir
  outra convenção, é 1 função.

## Estado da Fase 0
**F0-01 ✅ · F0-02 ✅ · F0-03 ✅ · F0-04 ✅ → Fase 0 FECHADA.** O harness compartilhado está
provado ponta a ponta (despachante/manifesto/logger · DoE/dataset/seeds · wrapper de FE +
export 4 camadas + gcs · **camada de métrica + âncora**). Próximo na escada (D84): **R1-00-harness**
(infra transversal MATLAB) ∥ **R2-00-harness** (BoTorch) — e o CP-init 100% cross-linguagem
fecha em R1-00 (corte herdado do F0-03).

## Commits desta sessão (branch `experiment/definitive_algorythms`)
Prefixo `[F0-04-metrica]`, cada um citando a decisão. **Só meus arquivos** (`src/metrics.py`,
`tests/test_metrics.py`, `scripts/accept.py`, `cards/INDEX.md`, este handoff) — `ORQUESTRACAO_
MESTRE.md` estava modificado por outra sessão e **não foi tocado**.
