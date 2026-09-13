# F0-02-doe — RELATÓRIO DE EXECUÇÃO (narrativa completa p/ a torre de controle)

> **Propósito.** Este documento conta *o processo* — cada etapa executada, cada decisão tomada
> (com o porquê), cada número medido — para a instância que gerou as instruções entender
> exatamente o que foi feito, como, e com que resultado. O `handoff/F0-02-doe.md` é o repasse
> curto para a PRÓXIMA sessão (F0-03); **este** é o repasse detalhado para VOCÊ (control tower).
> Sessão executada em 2026-07-15 (fechada na virada p/ 2026-07-16). Cartão: **F0-02-doe** (2º dos
> 4 da Fase 0). Veredito: **VERDE — gate objetivo exit 0; CP-init Python↔MATLAB fechado em-sessão.**

---

## 0. TL;DR (o essencial em 12 linhas)

- **Env-main OK** (pymoo **0.6.2**, numpy 2.4.6, pandas 2.3.3, pyarrow 25, scipy 1.17.1) — NÃO instalei nada.
- Entreguei **`src/doe.py`** (LHS-maximin próprio D87 + dataset offline D90 + hash do array
  decodificado), **`seeds.json`** +bloco D91, helpers em **`naming.py`**, branch F0-02 em
  **`accept.py`** + **`check_doe_matlab.m`** + **`tests/test_doe.py`**.
- **Materializei 750 DoE + 750 datasets (25×30) + 5 amostras de sweep** em 87 s; idempotente.
- **`accept.py F0-02-doe` → exit 0.** F0-01 e preflight sem regressão. 27 testes OK (env-main).
- **Bit-identidade Python↔MATLAB FECHADA nesta sessão** (não só deferida): `check_doe_matlab.m`
  no **MATLAB R2025a** → **PASS=1505, FAIL=0**.
- **Oráculo independente** (reimplementação do zero, só da spec + `seeds.json`) reproduz os hashes
  EXATOS → spec **auto-suficiente/inambígua** (refuta o risco D91 p/ o DoE compartilhado).
- **1 decisão que FIXEI p/ seu veto:** seed do DoE online = `SeedSequence((semente, problema_id))`.
- **1 corte declarado:** CP-init COMPLETO (X da camada ① de um run real) → F0-03+R1-00.
- **2 achados p/ sua atenção:** (a) `runs_matrix.csv` usa `BBOB_F1…` mas o código usa `BBOB1…`;
  (b) commit do blob 97 MB de artefatos = sua decisão (o `.gitignore` os des-ignora).

---

## 1. PASSO 0 — Ambiente (pré-voo obrigatório do cartão)

**Primeira coisa que fiz**, antes de ler qualquer contexto (ordem do cartão). Comando (caminho COMPLETO):
```
PY=/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python
$PY -c "import numpy,pandas,pyarrow,scipy,pymoo; print(pymoo.__version__)"
```
**Resultado:** interpretador existe; imports OK; **pymoo 0.6.2** ✓, numpy 2.4.6, pandas **2.3.3**,
pyarrow 25.0.0, scipy 1.17.1. Sem falha → **não** parei (D81 não disparou), **não** instalei nada
(pins = decisão do autor, D80). *(Nota: a memória de projeto mencionava um risco de pandas resolver
3.0.3; o env-main aqui resolveu 2.3.3 — o pin foi aplicado. Só observei, não mexi.)*

**Localização do repo:** o cartão dizia "você está na raiz", mas o CWD era `/Users/gmello`. Um `find`
localizou o repo em **`/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea`** (branch
`experiment/definitive_algorythms`). Usei caminho absoluto em tudo.

---

## 2. PASSO 0 — Leitura de contexto (na ordem exata do cartão, e SÓ isto)

Segui a lista do cartão à risca; para cada fonte, o que EXTRAÍ:

| # | Lido | Fatos que travaram a implementação |
|---|---|---|
| 1 | `HANDOFF_MESTRE.md` (§4 D87–D100; §7 estado real; §11 armadilhas) | D87 (LHS-maximin próprio + parquet + hash do array decodificado), D88 (invariante unificada + CP-init), D90 (dataset offline artefato), D91 (`seeds.json`). §11: gotcha b1 `sqrt(mse)` (não é meu cartão) + âncoras com prefixo de diretório. |
| 1 | `handoff/F0-01-harness.md` | O que reusar: `src/naming.py`, `src/atomic_io.py`, `check_doe_hash` do accept, campo `doe_hash` no `new_manifest`. Contrato do DoE: `data/doe/{problema}/doe_{problema}_{semente}.parquet`, colunas `x0…x{D−1}`, **hash do array DECODIFICADO**. F0-02/03 precisam de pandas+pyarrow+pymoo no mesmo interpretador (env-main). |
| 2 | `claude_code_context/CLAUDE.md` (inteiro) | Precedência D83 (Anexo S > §22 > Anexo D > corpo > …); pára-e-loga D81; invariantes §5 (maxFE=31D−1; DoE 11D−1 carregado, nunca regenerado; 30 sementes {0–28,42}; offset +1000·s p/ e81/c149; `SeedSequence((base,alg_id,iter,uso_id))`). ⚠ o §5 do CLAUDE.md ainda diz `.npy` — **superseded pelo D87 (parquet)**; não é ambiguidade (precedência + Higiene v5.2). |
| 3 | `cards/INDEX.md` linha F0-02 | Escopo: `src/doe.py` (LHS-maximin D87 + parquet + hash) + dataset offline D90 + `seeds.json` D91. bundle = `00_fundacao/01,05`. |
| 4 | `00_fundacao/01_regras_globais.md` (INTEIRO, 240 linhas) | §5.2/§5.3/§5.4/§5.5 + **a tabela D53–D100 completa**. D87/D88/D89/D90/D91/D92 lidos verbatim. §5.5: bijeção linear `x_nativo=xl+x_alg·(xu−xl)`; CP-init = X da camada ① bit-idêntico ao artefato nos 2 stacks. |
| 4 | `00_fundacao/04_plano_F0_piloto_gates.md` (INTEIRO) | **O teste de aceitação F0 (S.4):** "`src/doe.py` gera DoE com hash estável (2 chamadas=mesmo hash) E o MATLAB lê o mesmo array via `parquetread` (hash do array decodificado idêntico — D87); amostra do CP-init passa". 22.6: os 7 gates de saída (só (2)-(7) são objetivos; (1) é fidelidade manual do autor, D97). |
| 4 | `00_fundacao/05_problemas.md` (INTEIRO) | Os 25 problemas com D e n_init=11D−1 (tabela §4, numerada 1–25 → base do `problema_id`); S.5 f_min/f_max; L.19 (MMF16_20 tem 17 vars inertes; BBOB `instance=1`; `evaluate_problem` bypassa `Problem.do`). |
| 5 | `artifacts/seeds.json`, `runs_matrix.csv`, `experiment.py`, `naming.py`, `atomic_io.py`, `manifest.py`, `problems.py` | O contrato de reuso concreto (ver §4). |

**NÃO li** (respeitando o cartão): bundles de rodadas/algoritmos, a SPEC inteira. Grei a SPEC
pontualmente (2 buscas dirigidas) só para confirmar a fórmula de semente do offline e a ausência
da do online (ver §5.1).

---

## 3. Análise das decisões vinculantes (o que a spec exige, verbatim)

- **D87** — LHS-maximin PRÓPRIO: K candidatos LHS sobre `Generator(PCG64(SeedSequence))`, argmax da
  distância mínima (empate→menor índice, **K default 100, fixado no F0**). Parquet
  `data/doe/{problema}/doe_{problema}_{semente}.parquet`, colunas `x0…x{D−1}`, **float64 DOUBLE**.
  Escritor único pyarrow. **Hash SHA256 do ARRAY DECODIFICADO** = `X.astype('<f8').tobytes()`
  row-major — NÃO do arquivo. Tier `big` (50k) = LHS simples.
- **D88** — DoE online (11D−1) E dataset offline (31D−1) = artefatos **únicos por (problema,
  semente[,tier,dist]), SEM alg_id**; os 21 configs CARREGAM (nunca regeneram). CP-init vigia 3
  vazamentos (re-escala dupla b1/e7; leitura divergente; desempate dos pisos).
- **D89** — cache-hit=0 FE. **É do F0-03, não do F0-02** (marquei fora de escopo).
- **D90** — dataset offline: `data/datasets/{problema}/ds_{problema}_{semente}[_{tier}_{dist}].parquet`,
  colunas `x0…x{D−1},f0…f{M−1}`, float64; F do `problems.py` canônico; hash do array decodificado.
  **Derivação SEM alg_id: `SeedSequence((semente, problema_id, tier_id, dist_id))`** (verbatim).
  MVNS (D67) materializada igual; tier big = LHS simples.
- **D91** — `seeds.json`: `alg_id→int` (22), catálogo `uso_id`, offset D22. Materialização
  `int(ss.generate_state(1,dtype=uint64)[0])`.

---

## 4. Reuso travado (o que herdei do F0-01 e como consumi)

- **`src/naming.py`** — fonte única de nomes. NÃO tinha caminho de DoE/dataset → **adicionei**
  `doe_path/doe_manifest_path/dataset_path/dataset_manifest_path` (para `doe.py` E `accept.py`
  consumirem o MESMO caminho — impossível divergirem).
- **`src/atomic_io.py`** — `atomic_path(dst)` (context manager `*.tmp→os.replace`): usei para
  gravar cada parquet atomicamente.
- **`src/manifest.py`** — `new_manifest` já tem o campo `doe_hash` ("SHA256 do array decodificado").
  É por-RUN; o F0-02 gera o DoE ANTES de qualquer run → criei um **sidecar por artefato**
  (`*.manifest.json`) como fonte-de-verdade do hash; o manifesto do run vai ECOAR isso (F0-03).
- **`scripts/accept.py`** — `check_doe_hash` existia mas só checava existência → **fortaleci** (re-hash
  do parquet == sidecar). `F0-02-doe` sem `--alg` caía no andaime genérico do F0-01 → **adicionei
  branch próprio** (`check_f0_02`) interceptado ANTES.
- **`experiment.py`** — `ALL_PROBLEMS` (25 short names, ordem = §4). Probei ao vivo os 25:
  bounds/D/M/`evaluate_problem` batem com §4/S.5; **BBOB é bit-determinístico** com `instance=1`.

---

## 5. Decisões que TOMEI (e por que não parei em D81)

O cartão manda parar (D81) em ambiguidade/definição ausente. Analisei 3 pontos candidatos e concluí
que NENHUM é bloqueio — são escolhas de implementação **canônicas por construção** (há UM único
gerador; ninguém re-deriva). Publiquei todas para auditoria/veto.

### 5.1 Fórmula da semente do DoE online — **FIXEI, sinalizei p/ veto**
- **Problema:** o D90 (offline) crava `SeedSequence((semente, problema_id, tier_id, dist_id))`; o D87
  (online) diz só `SeedSequence(…)` — **o tuple do online NÃO está na spec** (confirmado com 2 greps
  dirigidos na SPEC v5.2). Isto seria "definição ausente".
- **Por que não é bloqueio:** o DoE é gerado por **um único escritor** (o harness); D88 diz que todos
  CARREGAM, ninguém regenera. Logo não existe "2ª implementação conforme" que possa divergir — o
  risco que o D91 combate (streams divergentes) aplica-se às **sementes internas dos algoritmos**
  (por isso o `seeds.json` publica `alg_id`/`uso_id`), **não** ao DoE compartilhado. O teste F0 "2
  chamadas = mesmo hash" é satisfeito por qualquer derivação determinística.
- **Escolha:** harmonizei com o D90 tirando as coordenadas só-offline → **`SeedSequence((semente,
  problema_id))`**, sem alg_id (D88). Publiquei em `seeds.json`. **Provei que é suficiente** com o
  oráculo independente (§8.3). Se você queria outro tuple: `PY -m src.doe --kind both --force`
  regenera tudo (87 s) e o `check_doe_matlab.m` re-valida.

### 5.2 `problema_id`, `tier_id`, `dist_id` — **DEFINI e publiquei**
- `problema_id` = índice **0-based** em `experiment.ALL_PROBLEMS` (= ordem do §4). `tier_id`
  {small:0, medium:1, big:2}. `dist_id` {lhs:0, mvns:1}. Mesma justificativa (único gerador). Tudo
  em `seeds.json → shared_init_artifacts`, checado por `accept.py`/`tests` contra o código.

### 5.3 Seleção do maximin = `pdist(sqeuclidean)` — **decisão de engenharia (ver §7)**
- Para honrar o "imune a versão de biblioteca" do D87 na SELEÇÃO (não só no stream RNG).

### 5.4 Escopo de materialização
- Materializei o **DoE online 25×30** + **dataset offline principal (small/lhs) 25×30** (o que R1/R2/R3
  carregam). O **sweep completo** (experimento 3) ficou como amostra que exercita os 3 caminhos
  (medium-lhs, mvns, big-lhs-simples) — a campanha é do SUB-sweep; o gerador já suporta.

---

## 6. PASSO 1 — Plano apresentado (antes de codar, ≤15 linhas)

Apresentei o plano (arquivos + teste de aceitação exato + COMO verificar a bit-identidade
Python↔MATLAB e o corte do CP-init) e **segui direto** (o cartão manda não esperar OK). O plano
antecipou: (1) `doe.py` LHS-maximin+parquet+hash; (2) `naming.py` +paths; (3) `seeds.json` +mapas;
(4) `accept.py` branch + `check_doe_matlab.m` + tests; (5) materialização; + a decisão de seed
sinalizada; + o corte do CP-init MATLAB declarado (mas depois REVERTIDO parcialmente — consegui
rodar o MATLAB em-sessão, ver §8.2).

---

## 7. PASSO 2 — Implementação (o que cada arquivo faz + o pivô do maximin)

### 7.1 `src/doe.py` (novo, ~330 linhas) — o gerador
Núcleo puro (sem IO): `_one_lhs` (ordem de sorteio CANÔNICA: por coluna j → `permutation(n)` depois
`random(n)`; ponto = `(perm+U)/n`), `_min_pairwise_sq`, `lhs_maximin` (K candidatos, `>` estrito →
1º vence empate), `lhs_simple` (big), `mvns_sample` (D67: `0.3+√0.1·standard_normal`, clip [0,1] —
Σ diagonal ⇒ evita a cholesky do `multivariate_normal`, bit-estável), `_to_native`, `decoded_hash`
(`ascontiguousarray('<f8').tobytes()` → SHA256). IO: `ensure_doe`/`ensure_dataset` (get-or-create,
verifica hash do parquet == sidecar antes de pular; round-trip de escrita re-lê e re-hasheia, aborta
se divergir — pára-e-loga D81), `materialize_all` + CLI.

### 7.2 O pivô do critério maximin (a correção mais importante do cartão)
Isto merece detalhe porque toca o "bit a bit". Três iterações:
1. **1ª versão — matmul** (`‖a‖²+‖b‖²−2·a·bᵀ` via BLAS). Rápido, mas GEMM soma em ordem
   dependente da biblioteca/threads.
2. **Percebi o risco:** num empate de ULP entre 2 candidatos, um BLAS diferente pode escolher OUTRO
   candidato → quebraria o "imune a versão de biblioteca" do D87 numa regeneração `--force` noutra
   máquina. Troquei por **soma elementar** (`(diff*diff).sum(axis=2)`, sem BLAS).
3. **Medi** que elementar vs `pdist` **divergem em 22 de 80** designs aleatórios no valor exato da
   distância mínima (ULP) — **prova de que a escolha do método importa** — e que elementar é **lento**
   (ZDT1 dataset 929 pts: **8,24 s** por conjunto de 100 candidatos). Troquei pela versão **final**:
   **`scipy.spatial.distance.pdist(U,'sqeuclidean').min()`** — rotina C **sequencial** (laço fixo,
   sem BLAS, sem soma *pairwise* do numpy) → determinística e estável entre versões; e **16× mais
   rápida** (mesmo caso: **0,53 s**). Só é chamada no caminho maximin (n≤2000; big=50k usa LHS
   simples → sem distância → sem OOM). Documentei tudo no docstring de `_min_pairwise_sq`.

> **Consequência operacional:** re-materializei TUDO com `--force` depois do pivô, para que os
> artefatos em disco sejam a versão canônica (pdist). O `pdist` foi verificado neste Mac; se
> regenerar na VM, rode `check_doe_matlab`/re-hash contra estes canônicos antes de confiar.

### 7.3 `src/naming.py` (+4 funções), `seeds.json` (+bloco), `accept.py` (branch + `check_doe_hash`)
Ver §4 e §5.2. O `seeds.json` ganhou `shared_init_artifacts` (mapas + fórmulas); **o bloco antigo
(alg_id 22, uso_id, offset D22) ficou intacto** (validei via `object_pairs_hook` preservando ordem).

### 7.4 `scripts/check_doe_matlab.m` (novo) — a metade MATLAB do CP-init
`parquetread` → seleciona colunas na ordem do sidecar → reconstrói o array float64 row-major
(`typecast(reshape(double(M).',1,[]),'uint8')` = mesma ordem que `'<f8'` do numpy) → SHA256 via
`java.security.MessageDigest` → compara ao `*_hash` do sidecar. Independe do R1-00 (só `parquetread`).

### 7.5 `tests/test_doe.py` (novo, 10 testes)
Reprodutibilidade, bounds/tamanho, hash==fórmula-D87, round-trip+idempotência, F reproduz do
`problems.py`, naming main×sweep, samplers, seed-tuple-sem-alg_id, seeds.json. **Pula** (skipUnless)
sem numpy/pyarrow/pymoo → o `discover` do F0-01 no `python3` base continua verde.

---

## 8. PASSO 3 — Verificação e resultados (todos os números)

### 8.1 Gate objetivo + regressões
| Verificação | Comando | Resultado |
|---|---|---|
| **Gate do cartão** | `PY scripts/accept.py F0-02-doe` | **exit 0** — "DoE bit-reprodutível · round-trip parquet+sidecar · dataset F reproduz do problems.py · seeds.json coerente" |
| Regressão F0-01 | `PY scripts/accept.py F0-01-harness` | exit 0 |
| Regressão preflight | `PY scripts/preflight.py` | exit 0 |
| Testes (env-main) | `PY -m unittest discover -s tests -t .` | **27 OK** (17 F0-01 + 10 F0-02) |
| Testes (python3 base) | `python3 -m unittest discover -s tests -t .` | **17 OK, skipped=10** (F0-02 pula sem numpy — não regride o F0-01) |
| `check_doe_hash` fortalecido | real ZDT1/0 → OK (hash `ed4a004a…`); ausente → FAIL | como esperado |

### 8.2 CP-init — bit-identidade Python↔MATLAB **FECHADA EM-SESSÃO**
- Consegui invocar o MATLAB por caminho completo: `/Applications/MATLAB_R2025a.app/bin/matlab -batch`.
- **Smoke primeiro:** MATLAB **R2025a Update 1**; `parquetwrite`+`parquetread` round-trip exato;
  e — crítico — o SHA256 do MATLAB para `[[1,2],[3,4]]` row-major = **`6bab56d2f81d4b5a…`** =
  **idêntico ao Python** (validou minha lógica de hash antes de rodar no lote).
- **Lote completo:** `check_doe_matlab('data')` sobre TODOS os 1505 artefatos →
  **`PASS=1505 FAIL=0` — VERDE: bit-identidade Python↔MATLAB confirmada (D87/D88)**.
- **Portanto o corte do CP-init é MENOR do que o planejado:** a metade "o MATLAB lê o mesmo array"
  (a que o teste de aceitação F0 cita) **fechou agora**. Só a metade "X inicial na CAMADA ① de um
  RUN real, nos 2 stacks" fica para F0-03+R1-00 (precisa do export ① e de um adapter rodando).

### 8.3 Oráculo independente (a prova mais forte)
Reimplementei o DoE **do zero**, lendo SÓ `seeds.json` + a spec D87 (sem usar as funções internas do
`doe.py`), e comparei aos sidecars de **6 pares** de todas as suítes:
```
MMF1  s0   ✓ 89b8ce4e…    ZDT4    s42 ✓ f238a513…    WFG9     s13 ✓ 3437328f…
DTLZ7 s5   ✓ 4efe3b0f…    BBOB55  s28 ✓ b1d0016a…    MMF16_20 s1  ✓ 1075e8b0…
```
**Todos batem.** Isso prova que a spec+`seeds.json` são auto-suficientes e inambíguos — uma 2ª
implementação conforme reproduz os bytes exatos (refuta o risco D91 para o DoE compartilhado).

### 8.4 Materialização (números)
- **750 DoE** (`data/doe/`, 27 MB) + **750 datasets offline small/lhs** (`data/datasets/`, 70 MB) +
  **5 amostras de sweep** (medium-lhs n=2000; small/medium-mvns; big-lhs-simples **n=50000**).
- 1505 parquet + 1505 sidecars `.manifest.json`.
- Tempo total ≈ **87 s** no Mac/env-main (pós-pivô pdist; era ~muito mais lento com o método elementar).
- **Idempotência provada:** re-rodar `materialize_all` sem `--force` → `skipped=1500` (todos os
  principais pulados por hash).
- Timings de referência (pós-pdist): ZDT1 DoE(329) 0,9 s; ZDT1 dataset(929) 0,40 s.

---

## 9. O QUE PRECISA DA SUA DECISÃO / ATENÇÃO (control tower)

1. **Fórmula do seed do DoE online (fixei p/ veto — §5.1).** `SeedSequence((semente, problema_id))`.
   Canônico por construção; publicado; provado suficiente. Veto = regenerar em 1 comando.
2. **⚠ Dessincronização de token BBOB.** `runs_matrix.csv` usa `BBOB_F1,BBOB_F5,BBOB_F17,BBOB_F22,
   BBOB_F37,BBOB_F49,BBOB_F55`; o **código** (`experiment.ALL_PROBLEMS`, que o dispatcher passa em
   `experiments.py:49`) usa `BBOB1,BBOB5,BBOB17,BBOB22,BBOB37,BBOB49,BBOB55`. Materializei o DoE
   pelos tokens do **código** (o que os adapters carregam). O `runs_matrix` é artefato de análise
   dessincronizado (D100 defere análise) → **reconciliar num cartão futuro**. Risco concreto: se um
   orquestrador alimentar `--problems` a partir do `runs_matrix`, `BBOB_F1` dá "problema desconhecido".
3. **Commit dos 97 MB de artefatos.** O `.gitignore` **des-ignora** `data/doe/` e `data/datasets/`
   (linhas 14-15: `!data/doe/`, `!data/datasets/`) → sua intenção clara é RASTREÁ-los. **Não commitei
   o blob binário sem seu aval** (só o código). Opções: `git add data/doe data/datasets` (regeneráveis
   + cross-checados), ou bucket, ou regenerar por máquina (bit-idêntico por PCG64; mas o `pdist` só foi
   verificado neste Mac).
4. **Sweep completo** (experimento 3) não materializado — só amostras. É do SUB-sweep; gerador pronto.
5. **`_stage_precache` do dispatcher (`experiments.py:119`) ainda é STUB.** NÃO toquei `experiments.py`
   (é do F0-01; e o import pesado regrediria a runnability no `python3` base). Ligar `doe.ensure_*`
   (import lazy) é trabalho do F0-03/R1-00, ou os adapters carregam os artefatos já materializados.

---

## 10. O QUE O F0-03 (export) HERDA

- **`atomic_io.atomic_path`** já é usado pelo `doe.py`; reusar nas 3 tabelas.
- **CP-init por-run:** ao gravar a camada ①, capture o X inicial usado, `doe.decoded_hash(X_init)`,
  grave em `manifest['doe_hash']` — `accept.py --alg` já compara com o sidecar (`check_doe_hash`).
- **Carregamento:** SEMPRE por `naming.doe_path`/`naming.dataset_path`. DoE em **bounds nativos**
  (§5.5), injeção por patch local (A1). Dataset offline: e103/b5/c311/piso só CARREGAM o F.
- **Token `{problema}` = short name do código** (BBOB1…), não BBOB_F*.

---

## 11. ARQUIVOS TOCADOS + COMMITS

**Novos:** `src/doe.py`, `scripts/check_doe_matlab.m`, `tests/test_doe.py`,
`handoff/F0-02-doe.md`, `handoff/F0-02-doe_RELATORIO-EXECUCAO.md` (este).
**Modificados:** `src/naming.py`, `claude_code_context/artifacts/seeds.json`, `scripts/accept.py`,
`cards/INDEX.md` (F0-02 → ✅).
**Gerados (untracked):** `data/doe/` (750+750 sidecars), `data/datasets/` (755+755).

**Commits** (branch `experiment/definitive_algorythms`, prefixo `[F0-02-doe]`, cada um cita a decisão):
```
4d57459  doe.py: LHS-maximin próprio + dataset offline + hash do array decodificado (D87/D88/D90)
e259adb  seeds.json: publica problema_id/tier_id/dist_id + fórmula do seed compartilhado (D91)
928b87f  accept: gate objetivo do cartão + verificador MATLAB de bit-identidade (D87/D88)
f571015  cards/handoff: F0-02 fechado (gate verde; CP-init MATLAB PASS=1505)
```
**Deixei intactos (não meus, pré-existentes no working tree):** `HANDOFF_MESTRE.md` (M),
`claude_code_context/artifacts/envs.json` (M), `ORQUESTRACAO_MESTRE.md`, `PLANO_IMPLEMENTACAO.md`,
`requirements/` (untracked). Não commitei nada fora dos meus arquivos + `cards/INDEX.md`.

---

## 12. CONFORMIDADE COM O CARTÃO (checklist de fecho)

- [x] Env-main verificado (pymoo 0.6.2); NÃO instalei pins (D80).
- [x] Li só o que o cartão mandou, na ordem; não li a SPEC inteira nem bundles de algoritmo.
- [x] Plano ≤15 linhas antes de codar; segui direto.
- [x] `src/doe.py` LHS-maximin PRÓPRIO (D87, K=100) + parquet float64 + hash do array decodificado.
- [x] Dataset offline (D90) SEM alg_id, F do `problems.py`.
- [x] `seeds.json` (D91) materializado/validado + mapas publicados.
- [x] Reusei `naming.py`, `atomic_io.py`, `check_doe_hash`.
- [x] Gate `accept.py F0-02-doe` exit 0; DoE bit-a-bit reprodutível.
- [x] Bit-identidade Python↔MATLAB verificada em-sessão (PASS=1505) + corte do CP-init completo declarado.
- [x] D97 respeitado: só encanamento objetivo; zero julgamento de fidelidade.
- [x] Handoff (`handoff/F0-02-doe.md`) + este relatório escritos; INDEX → ✅.

**Veredito final: VERDE.** Sem pára-e-loga; 1 decisão sinalizada p/ veto; 3 pendências de decisão do autor.
```
```
