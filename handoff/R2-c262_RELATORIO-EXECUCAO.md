# R2-c262 — RELATÓRIO DE EXECUÇÃO (narrativa completa p/ a torre de controle)

> **Propósito.** Descreve, passo a passo, TUDO o que a sessão do cartão
> **R2-c262** executou: verificação de ambiente, leitura de contexto, decisões
> de leitura da SPEC, implementação, os 3 pilotos e — o mais importante para o
> veto do autor — **cada comando rodado e o resultado exato**. Companheiro do
> handoff conciso `handoff/R2-c262.md`.
>
> **Data:** 2026-07-17/18 · **Máquina:** Mac (macOS 12.5.1, arm64), env-main
> por caminho completo · **Veredito final: VERDE ✅** (gate objetivo nos 3
> problemas; SEM julgamento de fidelidade — D97, validação em LOTE do autor).
>
> ⚠ **Sessão em PARALELISMO DE FAIXAS** com o c238/MATLAB na mesma árvore.
> Faixa tocada: `src/c262_qnehvi.py` (novo) · `src/experiment.py` (1 linha) ·
> `tests/test_c262.py` (novo) · `handoff/R2-c262*.md`. **Zero** `.m`,
> `algorithms/**`, `botorch_harness.py`, `accept.py`, artefatos. Commits com
> o ritual (add+verify+commit atômico; staging conferida antes de commitar).

---

## 0. TL;DR

- **Gate `accept.py R2-c262` exit 0 nos 3 problemas** (semente 0): MMF1
  FE=61 · DTLZ2 FE=371 · ZDT1 FE=929 — todos com DoE bit-a-bit (CP-init) e
  4 saídas válidas. ZDT1 coube no teto de 8h (4h11; a projeção não disparou).
- **Regressão intacta:** R2-00 (stubpy) + F0-01..04 + preflight exit 0;
  suíte **82 OK (1 skip)** = 75 pré-existentes + 7 novos.
- **A curva §17.6 (dado-alvo O(n³)) medida nos 3 runs:** fit ≈ n^2,0 (DTLZ2)
  e n^2,3 (ZDT1, 0,64s→4,89s em n 329→929); custo dominante do c262 = a
  BUSCA (98% no DTLZ2 M=3; 89% no ZDT1), não o fit.
- **1 achado relevante p/ doc-sync da torre:** o BoTorch 0.18.1 OFICIAL do
  PyPI TAMBÉM embarca o kernel fusionado (premissa do S.3#9 desatualizada);
  DEF-L2 aplicada = OFF explícito, Python puro determinístico (§3 abaixo).
- **Zero mudança no harness R2-00** (cobriu tudo) · zero item fora da faixa.

## 1. AMBIENTE (gate bloqueante — antes de tudo)

```
PY -c "import botorch,torch,gpytorch,pymoo; print(...)"
→ 0.18.1 2.11.0 1.15.2 0.6.2                                    (exit 0)
git log --oneline -5 → contém a96cc7a [R2-00-harness] ✓ (pré-requisito)
git status → faixa do c238 em andamento (algorithms/c238_EIM/*.m,
  src/experiment.m, anchors.json, EIM.m, c238_instrument.m) — JAMAIS tocada.
```
Nota: o repo está em `~/Documents/python_repos/mestrado/ua-dd-saea` (o
prompt dizia `ua-dd-saea` na raiz; localizado via mdfind — sem impacto).

## 2. CONTEXTO LIDO (na ordem e SOMENTE o prescrito)

HANDOFF_MESTRE (§10/§11) → handoff/R2-00-harness.md → CLAUDE.md do contexto
→ linha R2-c262 do cards/INDEX.md → 00_contrato_rodada2.md → alg_c262_qnehvi
INTEIRO → 01_regras_globais.md + 03_contrato_export.md. Consultas pontuais
(grep) na SPEC: refs do c262 (Anexo J linha ~2184: ref FIXO por problema;
linha ~2196: c262 = escala BRUTA), D44, N.2.3/S.3#9, D97. Artefatos:
seeds.json (c262 alg_id=9; usos 0/1/2) e params.json (Balde B do c262).

## 3. DECISÕES DE LEITURA (nenhuma escalada — nenhum conflito real)

1. **Ref-point da aquisição.** O card traz "nadir×1,1" (§22.3) e
   "nadir−0,1·(ideal−nadir)" (tabela) — **algebricamente a MESMA fórmula**
   (nadir−0,1·(ideal−nadir) = nadir+0,1·(nadir−ideal); o próprio D69
   explicita a equivalência do shorthand "×1,1"). O Anexo J crava: **fixo
   por problema** (Tab. 2 do paper), escala **bruta**. Implementado sobre o
   (ideal, nadir) CONGELADO da S.5 (`metrics.reference_bounds`) — a fonte
   por-problema canônica do harness; negado p/ o espaço de maximização.
   Logado no jsonl (header) e manifesto (`acqf_ref_f`). Sem ambiguidade
   restante ⇒ sem pára-e-pergunta.
2. **`cache_root`.** A tabela K do card diz "True"; o checklist §22.3 e a
   L.10 (precedência maior, D83) dizem `None` ⇒ **None** (que é também o
   default do 0.18.1).
3. **Kernel fusionado (o achado da sessão).** O smoke inicial revelou que o
   botorch instalado (`__version__=='0.18.1'`, guarda N.2.3 passa) TENTA
   compilar `csrc/logei_fused.cpp` com `-march=native` (falha no clang
   arm64 → fallback silencioso — o hazard EXATO do S.3#9, que a SPEC
   atribuía só ao fork). **Verificação conduzida:** (a) sha256 do csrc
   instalado ≠ o do clone `_BoTorch` (não é o fork); (b) `pip download`
   do wheel oficial botorch==0.18.1 do PyPI (download apenas — NADA
   instalado, D80 respeitado) e comparação de RECORD: **byte-idêntico**
   (diff = só INSTALLER/REQUESTED do pip). Conclusão: o 0.18.1 OFICIAL
   embarca o kernel fusionado; a premissa "ausente do oficial" do S.3#9
   está desatualizada (o recurso do fork foi incorporado upstream).
   **Remédio (a política DEF-L2 já prevista):** OFF EXPLÍCITO no runner
   (`_load_attempted=True`, `_C=None`) ⇒ caminho Python puro determinístico
   Mac×Linux; logado. **Ação p/ a torre:** doc-sync S.3#9 + replicar o OFF
   no c154 e no despachante M8.
4. **NumericalWarning do gpytorch** ("Very small noise values… rounding up
   to 1e-06", ~2/iteração): artefato ESPERADO do `train_Yvar=1e-6` (B8.6a)
   sob Standardize (divide por std² → cai abaixo do piso 1e-6 do gpytorch,
   que arredonda de volta). Comportamento documentado do stack oficial;
   filtro estreito por mensagem no runner + registro no header do jsonl.
5. **② para BO** (contrato §17.3 não fixa membership p/ BoTorch): gravado o
   **conjunto de treino por iteração** (o arquivo real que o modelo VIU) —
   ger 0 = DoE; ger it = ids 0..n_train−1. Barato (ints, RLE) e é a
   semântica de "população mantida" de um BO de arquivo-completo.
6. **Fim natural D61:** o laço é `while True` com o hard-stop no ponto único
   de avaliação (padrão herdado do R2-00) ⇒ a última iteração ajusta o
   modelo no n final e morre no infill. Custo: 1 fit+acqf extra; ganho: o
   ponto MAIS CARO da curva §17.6 de graça + o contrato "o wrapper governa"
   intacto (o algoritmo nunca espia o saldo).

## 4. IMPLEMENTAÇÃO

- **`src/c262_qnehvi.py`** (novo, ~450 linhas): `run_c262` com a receita
  L.10 na íntegra — detalhes no handoff §"O desenho". Micro-smoke da
  iteração-núcleo ANTES de escrever o arquivo (modelo+acqf+optimize_acqf
  com `return_best_only=False` num toy 2-obj: shapes (10,1,D)/(10,)
  confirmados; assinaturas do 0.18.1 verificadas por `inspect.signature`,
  nunca de memória).
- **`src/experiment.py`**: `'c262': ('src.c262_qnehvi', 'run_c262',
  'botorch')` no `_DISPATCH_LOADERS` (única linha).
- **`tests/test_c262.py`** (7 testes): alg_id/usos × seeds.json;
  h0/h1/h2 re-derivados independentes (anti-tautologia); ref × S.5 (3
  problemas); modelo por objetivo (ScaleKernel+Matérn nu=2.5 ARD,
  Standardize, noise>0); params da acqf (sampler 128/seed, alpha=0,
  tau_max=1e-3, fat); fused OFF; linha do dispatch. Pulam sem torch.
- **Sem mudanças** em `botorch_harness.py` (o `Standardize(m=1)`
  por-objetivo veio direto do botorch — o `make_standardize()` de m=M não
  era o que a receita de ModelListGP pede; nenhum gancho novo necessário).

## 5. OS 3 PILOTOS (semente 0, LOCAL — nada ao bucket)

```
experiment.run('c262','MMF1',0)   → FE 61/61 · 41 fits · hard-stop ✓ ·
  CP-init ✓ · 38s (fit 3,4s · busca 30,8s)                        (exit 0)
accept.py R2-c262 --alg c262 --problema MMF1 --semente 0          (exit 0)

experiment.run('c262','DTLZ2',0)  → FE 371/371 · 241 fits · 2h31
  (fit 130s · busca 8.893s = 98% — partição exata M=3/amostra MC) (exit 0)
accept.py ... --problema DTLZ2                                    (exit 0)

experiment.run('c262','ZDT1',0, max_wall_s=28800) → FE 929/929 ·
  623 iters (600 infills + 22 cache-hits D89 + 1 hard-stop) · 4h11
  (fit 1.627s · busca 13.386s); projeção de 8h NUNCA disparou     (exit 0)
accept.py ... --problema ZDT1                                     (exit 0)
```
Ordem MMF1→DTLZ2→ZDT1 estritamente sequencial (1 run = 1 core — curva de
tempo limpa, D79). Os 22 cache-hits do ZDT1 = D89 em ação (duplicata
bit-exata do ótimo com 29/30 coords clampadas em 0,0; streak máx 3; guard
logado; FE final exato mesmo assim) — detalhe no handoff.

## 6. AUDITORIA pyarrow (os 3 runs)

- **①** = 31D−1 linhas EXATAS (init 11D−1 + opt 20D), `solution_id` únicos,
  float32. **②** membership por iteração (MMF1 1.702 · DTLZ2 60.622 · ZDT1
  397.343 linhas). **③** = 10 candidatos dos restarts × iteração com μ/σ
  finitos, σ>0, μ em MINIMIZAÇÃO (§5.5: o −f nunca vaza), escolhido linkado
  por `real_solution_id` (240/240 no DTLZ2; 622/623 no ZDT1 — o do
  hard-stop NULL, correto). **timing** = 1 linha/fit incl. o fit final do
  hard-stop. **jsonl** = header (ref, fused, params, env) + decisions com
  TODOS os campos S.7 (h0/h1/h2, acqf do escolhido E dos 10 restarts,
  n_restarts, fit_retries, acqf_warnings, cache_hit, n_train) + guards
  (cache_hit ×22 no ZDT1; hard_stop ×1/run) + footer ok. **manifesto** =
  fit_series + env N.2.3/L.18 + pinning + acqf_ref_f + fused_kernel.
- Sanidade de encanamento (não é juízo de fidelidade): |μ−f| dos escolhidos
  mediana 9e-4 (MMF1) — GP interpola noiseless; `acqf_escolhido` decresce
  ao longo do run (−0,885→−2,204 no MMF1) — o log-EHVI esperado encolhe.

## 7. REGRESSÃO FINAL

```
accept.py R2-00-harness --alg stubpy --problema MMF1 --semente 0  (exit 0)
accept.py F0-01/F0-02/F0-03/F0-04                                 (exit 0 ×4)
preflight.py → pré-voo OK ✓ (1 deferimento intencional)           (exit 0)
python -m unittest discover -s tests -t . → 82 OK (1 skip)        (exit 0)
```
Gates R1 = da sessão paralela (a torre roda tudo no merge).

## 8. PENDÊNCIAS (nenhuma bloqueia; herança + 3 novas anotações)

1–2. As do R2-00 (manifesto sobrescrito pelo `_run_one`; resume×bucket-only)
   seguem em pé — fora da faixa; antes da M8.
3. Doc-sync S.3#9 (kernel fusionado no oficial) + política OFF no c154/M8.
4. Manifesto re-gravado com `acqf_ref_f`/`fused_kernel` APÓS o
   write_run_outputs — na M8 com bucket, o blob do manifesto ficaria 1
   versão atrás dessas 2 chaves (fix aditivo trivial no harness, se a torre
   quiser: `extra_manifest` no write_run_outputs).
5. INDEX: linha R2-c262 fica ⬜ até a torre marcar (paralelismo).
