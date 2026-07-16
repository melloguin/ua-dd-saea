# handoff/F0-02-doe.md — Fase 0, cartão 2/4 (artefatos de inicialização compartilhados)

**Data:** 2026-07-15 · **Env:** env-main (`.../mestrado_experimentos_dissertacao/bin/python`;
numpy 2.4.6 · pandas 2.3.3 · pyarrow 25.0.0 · scipy 1.17.1 · **pymoo 0.6.2** ✓)
**Gate:** `PY scripts/accept.py F0-02-doe` → **VERDE, exit 0** ✅
**Escopo:** PURA INFRAESTRUTURA — gera os DADOS que **todos os 21 configs CARREGAM** (D88);
**sem algoritmo, sem fidelidade** (D97). Precisão **bit-a-bit** é o coração do cartão.

## Resultado (tudo verde)
- `PY scripts/accept.py F0-02-doe` → **exit 0** (DoE bit-reprodutível · round-trip parquet+sidecar ·
  dataset F reproduz do `problems.py` · `seeds.json` coerente).
- **Cross-language Python↔MATLAB fechado NESTA sessão** (não ficou só deferido):
  `scripts/check_doe_matlab.m` rodou no MATLAB **R2025a Update 1** sobre TODOS os artefatos →
  **PASS=1505 FAIL=0** — o array decodificado que o `parquetread` enxerga é **bit-idêntico** ao
  hash gravado pelo escritor pyarrow (D87/D88). *(O MATLAB e o Python calculam o MESMO SHA256 do
  array row-major `<f8` — validado com a âncora `[[1,2],[3,4]] → 6bab56d2…`.)*
- **Oráculo independente:** uma reimplementação do DoE **do zero** (só da spec D87 + `seeds.json`,
  sem usar `src/doe.py`) reproduz os hashes EXATOS de 6 pares `(problema,semente)` de todas as
  suítes → prova que a spec+`seeds.json` são **auto-suficientes e inambíguos** (refuta o risco D91
  "duas implementações conformes divergiriam" — para o DoE compartilhado).
- **27 testes** (`PY -m unittest discover -s tests -t .`) → **OK** (17 do F0-01 + 10 novos do DoE);
  no `python3` base os 10 novos são **PULADOS** (sem numpy) → `discover` do F0-01 segue verde (17 OK, skipped=10).
- **Regressões:** `accept.py F0-01-harness` exit 0; `scripts/preflight.py` exit 0.
- **Materializado:** **750 DoE** (25×30) + **750 datasets offline** (small/lhs, 25×30) + **5 amostras
  de sweep** (medium-lhs, small/medium-mvns, big-lhs-simples) → 1505 parquet + 1505 sidecars
  (27 MB `data/doe/` + 70 MB `data/datasets/`). Geração idempotente: re-rodar → `skipped=1500`.
  Tempo total ≈ **87 s** no Mac (env-main).

## Arquivos

**Novos:**
- `src/doe.py` — **o gerador**. LHS-maximin PRÓPRIO (D87): `K=100` candidatos sobre
  `Generator(PCG64(SeedSequence))`, escolhe o de **maior distância mínima** em [0,1]^D
  (empate→menor índice), mapeia p/ bounds nativos (§5.5). API:
  `generate_doe / ensure_doe` (online 11D−1), `generate_dataset / ensure_dataset`
  (offline; small/medium/big × lhs/mvns), `decoded_hash`, `materialize_all` + CLI
  (`PY -m src.doe --kind both`). Escritor único pyarrow, float64/DOUBLE, snappy.
- `scripts/check_doe_matlab.m` — a **metade MATLAB** do CP-init (D87/D88): `parquetread` →
  array row-major `<f8` → SHA256 (via `java.security.MessageDigest`) → compara ao sidecar.
  `nfail = check_doe_matlab('data')`.
- `tests/test_doe.py` — 10 testes (reprodutibilidade, bounds/tamanho, hash=fórmula D87,
  round-trip, idempotência, F reproduz, naming main×sweep, samplers, seed sem alg_id, seeds.json).
  Pula sem numpy/pyarrow/pymoo.

**Modificados:**
- `src/naming.py` — +`doe_path/doe_manifest_path/dataset_path/dataset_manifest_path` (fonte única
  dos caminhos; `accept.py` e `doe.py` consomem — não podem divergir).
- `claude_code_context/artifacts/seeds.json` — +bloco `shared_init_artifacts` (D91):
  publica `problema_id` (0-based, ordem `ALL_PROBLEMS`), `tier_id`{small0,med1,big2},
  `dist_id`{lhs0,mvns1} e as **fórmulas de semente** do DoE/dataset. **Nada do bloco antigo mexido**
  (alg_id 22, uso_id, offset D22).
- `scripts/accept.py` — branch real do cartão `F0-02-doe` (`check_f0_02`); `check_doe_hash`
  **fortalecido** (re-hash do parquet == sidecar, não só existência) — é o CP-init objetivo por-run
  que R1/R2/R3 vão usar via `--alg`.
- `cards/INDEX.md` — F0-02-doe → ✅.

## Contrato para quem CARREGA (R1/R2/R3 — leia isto)
- **Caminho:** use SEMPRE `src.naming` — `naming.doe_path(problema, semente)` e
  `naming.dataset_path(problema, semente[, tier, dist])`. Nunca reconstrua strings.
- **DoE online:** `data/doe/{problema}/doe_{problema}_{semente}.parquet`, colunas `x0…x{D−1}`,
  **bounds NATIVOS** (§5.5), `11D−1` linhas. O adapter injeta esse X por **patch local** (A1) —
  os SAEAs não usam `Problem.Initialization`. MATLAB lê com `parquetread`.
- **Dataset offline PRINCIPAL:** `data/datasets/{problema}/ds_{problema}_{semente}.parquet`
  (= tier `small`, dist `lhs`), colunas `x0…x{D−1}, f0…f{M−1}`, `31D−1` linhas. **e103/b5r/b5m/c311/
  piso só CARREGAM** o F — nunca reavaliam (D90). Variantes do sweep têm sufixo `_{tier}_{dist}`.
- **Hash (D87):** SHA256 do **array decodificado** (`np.ascontiguousarray(A,'<f8').tobytes()`,
  row-major) — está no sidecar `.manifest.json` de cada artefato. O `doe_hash` do **manifesto do run**
  (`src/manifest.py`, campo já existe) deve ECOAR esse valor; o CP-init compara os dois.
- **`{problema}` = short name do CÓDIGO** (`experiment.ALL_PROBLEMS`): BBOB é `BBOB1,BBOB5,BBOB17,
  BBOB22,BBOB37,BBOB49,BBOB55` — **NÃO** os `BBOB_F*`. (ver ⚠ pendência abaixo.)

## ⚠ DECISÃO QUE FIXEI (para seu veto — regenerar = 1 comando)
- **Fórmula da semente do DoE compartilhado.** A D87 deixou o *tuple* do `SeedSequence` aberto
  (`SeedSequence(…)`); a D90 (offline) o cravou: `(semente, problema_id, tier_id, dist_id)`.
  **Harmonizei o online como `SeedSequence((semente, problema_id))`** (mesma convenção, sem as
  coordenadas só-offline; **sem alg_id**, D88). É **canônico por construção**: há UM único gerador
  (o harness), ninguém re-deriva o DoE — só CARREGA; o oráculo independente confirma que a spec é
  suficiente. Publiquei tudo em `seeds.json`. **Se você queria outro tuple**, é só me dizer:
  `PY -m src.doe --kind both --force` regenera tudo (87 s) e o `check_doe_matlab.m` re-valida.
- **Seleção do maximin = `scipy.spatial.distance.pdist(U,'sqeuclidean')`** (menor distância²).
  Escolha DELIBERADA: é rotina C **sequencial**, SEM `matmul`/BLAS — a expansão `‖a‖²+‖b‖²−2a·b`
  (GEMM) e até o `ndarray.sum` (soma *pairwise* do numpy) têm ordem de soma variável e poderiam
  trocar o candidato vencedor num empate de ULP, quebrando o "imune a versão" do D87. (Medido: 22
  divergências de ULP entre `pdist` e a soma-pairwise em 80 designs aleatórios — por isso a escolha
  importa e foi fixada.) Só é chamada no caminho maximin (n≤2000; tier `big`=50k usa LHS simples).

## CP-init — o que FECHOU agora vs. o CORTE (D88/§5.5)
O CP-init tem 3 provas; **2 fecharam agora, 1 é corte declarado:**
- ✅ **Bit-identidade do artefato, Python↔MATLAB** — `parquetread` lê o mesmo array (PASS=1505).
- ✅ **"avaliá-lo reproduz o F"** (metade Python) — o F persistido no dataset bate bit-a-bit com o
  `evaluate_problem(problems.py, X)` re-avaliado (e o BBOB é determinístico c/ `instance=1`).
- ⏸ **CORTE → R1-00/F0-03:** o CP-init COMPLETO exige o **X inicial capturado na CAMADA ① de um run
  REAL, nos 2 stacks** — isso depende do **export ① (F0-03)** e de **um run com adapter (R1-00)**,
  que não existem neste cartão. Quando F0-03+R1-00 fecharem: para uma amostra `(problema,semente)`,
  o `doe_hash` gravado no manifesto do run (da ① lida pelo adapter) deve bater com o sidecar do DoE —
  aí o CP-init está 100%. O gancho objetivo já está pronto: `accept.py --alg` chama `check_doe_hash`.

## O que o F0-03 (export) precisa saber
- **Reuse:** `src/atomic_io.atomic_path` (escrita atômica) já é usado pelo `doe.py`; o `doe_hash`
  do manifesto do run vem do sidecar do DoE (`naming.doe_manifest_path`).
- **CP-init por-run:** ao gravar a camada ①, capture o X inicial efetivamente usado, compute
  `doe.decoded_hash(X_init)` e grave em `manifest['doe_hash']` — o `accept.py --alg` já compara.
- **`_stage_precache` (dispatcher, `experiments.py:119`) ainda é STUB** — agora que `src/doe.py`
  existe, ligue-o a `doe.ensure_doe`/`ensure_dataset` (import **lazy** p/ não quebrar o `python3`
  base do F0-01). **NÃO** toquei `experiments.py` (é do F0-01; e o import pesado regrediria a
  runnability no base). Alternativa: os adapters carregam direto os artefatos já materializados.

## Pendências abertas / decisões do autor
1. **⚠ `runs_matrix.csv` usa `BBOB_F1…` mas o CÓDIGO usa `BBOB1…`** (o dispatcher é
   `experiments.py:49 → list(ALL_PROBLEMS)`). Materializei o DoE pelos tokens do código (o que os
   adapters carregam). O `runs_matrix` é artefato de análise dessincronizado — **reconciliar num
   cartão futuro** (não é F0-02; D100 defere análise). Se algum orquestrador alimentar `--problems`
   a partir do `runs_matrix`, `BBOB_F1` dá "problema desconhecido".
2. **Commit dos 97 MB de artefatos?** O `.gitignore` **des-ignora** `data/doe/` e `data/datasets/`
   (linhas 14-15) → intenção do autor = **rastreá-los**. Deixei-os **untracked** (não commitei blob
   binário grande sem seu aval; commitei só o código com prefixo `[F0-02-doe]`). Você decide:
   `git add data/doe data/datasets` (rastreia; regeneráveis+cross-checados) **ou** distribuir via
   bucket **ou** regenerar por máquina (`PY -m src.doe`; bit-idêntico por PCG64, mas o `pdist` só foi
   verificado neste Mac — se regenerar na VM, rode `check_doe_matlab`/re-hash contra estes canônicos).
3. **Sweep completo (experimento 3)** não foi materializado — só amostras que exercitam os 3
   caminhos. A campanha do sweep (~5 problemas × tiers × dists, big=50k c311-only) é do **SUB-sweep**;
   o gerador já suporta (`ensure_dataset(..., tier=, dist=)`).

## Commits desta sessão (branch `experiment/definitive_algorythms`)
Prefixo `[F0-02-doe]`, cada um citando a decisão. **Só meus arquivos** — deixei intactos os
pré-existentes não-meus (`HANDOFF_MESTRE.md`, `envs.json`, `ORQUESTRACAO_MESTRE.md`,
`PLANO_IMPLEMENTACAO.md`, `requirements/`).
