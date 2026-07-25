# T9-calibracao — RELATÓRIO DE EXECUÇÃO

> O que foi executado, na ordem, com evidências. Detalhe técnico em
> `T9-calibracao.md`; a tabela-entregável em `T9-calibracao_REPASSE.md`.

## 0. Reconhecimento
Li: T6-batch{,_REPASSE}, REGISTRO A23/DI-35.1, os 2 runners (`c262_qnehvi.py`,
`c154_jes.py`), `experiment.py`/`budget.py`/`botorch_harness.load_doe/load_sonda`,
`envs.json` (env_main = `.../mestrado_experimentos_dissertacao`, py3.11.9, botorch
0.18.1). Achei os artefatos do smoke T6 (`/private/tmp/data/...batch...`,
`batch_smoke_c262.log`): o "56 h" veio do projetor embutido em fe=209 SOB CONTENÇÃO
(4 configs ∥ + swap; o c262 do T6 foi OOM-killed) — não é a receita.

## 1. Harness de probe (tempdir, 1 core, sem tocar src/)
`scratchpad/probes/probe.py`: patcha `budget.K_BATCH` (cap de iterações) + as
constantes de módulo do runner (monkeypatch em memória), roda o runner REAL no
tempdir (`doe`/`sonda` symlink p/ `data/`), extrai a curva por iteração do jsonl.
`sweep.sh` (hardened: captura stderr, sem `set -e`, loga RAM, rescue de jsonl parcial
em OOM), `analyze.py` (projeção componente-a-componente + método da razão). Smoke
3-iter OK (maxfe=139 = 11·10−1 + 3·10; knob confirmado no header).

## 2. Probes c262 (ZDT4/42, q=10, serial, 1 core)
- **Fase A** — MC ∈ {128,64,32,16}, 40 iters cada: `t_busca@n≈499` ~13–23 s em TODOS
  ⇒ **MC é dud** (não muda custo).
- **Fase B** — deep receita cheia (10/512/128): rodou limpo n=109→669 (57 iters;
  **OOM-killed em n=669** — evidência viva do D-2). Projeção componente: busca ~1,6 h
  (p≈0,54) + fit ~0,6 h (p≈2,17) + overhead ~0 = **~2,2 h**.
- **CONFIRMAÇÃO** (runner REAL, empty knob, q=10, 15 iters): header = 128/10/512
  (cheio, como esperado — c262 sem knob); `t_busca` 5,2→17,3 s (n=109→259), bate com
  a Fase A. Wiring OK.

## 3. Probes c154 (ZDT4/42, q=10, serial, 1 core)
- **Anchor cheio (5D/1000D):** it 1 limpa = `t_busca@n=109 = 1051 s` (~17,5 min).
  Matei após 1 it (o caro não se repete — card). Custo cresce ~n^1,6 (JES-LB, SEM
  prune de baseline — ≠ c262).
- **Bracket (14/14/12 iters, n→239, limpo — ts_delta ≈ t_busca).** Projeção pela
  PRÓPRIA curva medida + FLOOR sem extrapolação:
  2D/50D (150→867 s, floor 47 h, ~255 h) · 1D/50D (101→567 s, **FLOOR 30 h**, ~147 h) ·
  1D/25D (81→295 s, floor 16 h, ~62 h). **🔴 TODO FLOOR > teto 12 h ⇒ ~10 h COMPLETO
  é INVIÁVEL.**
- **🔴 Correção (revisão adversária, D-4 do REPASSE):** meu 1º "~10–14 h" via *método
  da razão* (÷ âncora-cheia NÃO medida) estava ERRADO; refeito por integração direta.
  Shipado **`1D/50D`** (≈ default BoTorch) = maior redução DEFENSÁVEL; o teto TRUNCA
  (parcial). CONFIRMAÇÃO (runner REAL, empty knob): header num_restarts=10/raw=500
  (batch ativo). A estratégia (truncar/limitar/agressivo/drop) é do autor.

## 4. Implementação (batch-only)
- `src/c154_jes.py`: `NUM_RESTARTS_PER_D_BATCH=1`, `RAW_SAMPLES_PER_D_BATCH=50`,
  helper `_restarts_raw_for_q(q,D)` (fonte única), threaded no
  `_optimize_acqf_restarts`/greedy/header. q=1 = 5D/1000D byte-idêntico.
- `src/c262_qnehvi.py`: só COMENTÁRIO (decisão medida: sem knob).
- `tests/test_batch_q10.py`: `TestCalibracaoBatchT9` (4 testes) — valores calibrados,
  q=1 intocado em D∈{2,10,12,22,30}, q>1 reduzido, ausência intencional de knob c262.

## 5. Gates
- **Prova de regressão ①②③④ (q=1 main/MMF1/s0):** c262 e c154 **BIT-IDÊNTICOS**
  (③ surrogate de 44 410 linhas inclusive; só `tempo_*_s` de wall variam). Re-rodada
  após TODAS as edições. ✅
- **Revisão adversária (5 agentes)** sobre o diff: pegou o ERRO do "~10–14 h" do 1º
  cálculo (método da razão sobre âncora-cheia não medida) ⇒ CORRIGIDO por integração
  direta (§3). Também motivou o teste de WIRING do call site e a correção de 3
  comentários stale.
- **CONFIRMAÇÃO c154 (runner REAL, empty knob):** header num_restarts=10/raw=500
  (batch 1D/50D ATIVO); t_busca 100→265 s (n=109→179) bate com o probe monkeypatch.
- Suíte `tests/test_batch_q10.py`: **23 OK** (`TestCalibracaoBatchT9`: 5 — valores
  calibrados, q=1 intocado em D∈{2,10,12,22,30}, q>1 reduzido, WIRING do call site,
  c262 sem knob). `test_c154`+`test_c262`: 16 OK (inalterados).
- **Suíte completa:** `unittest discover -s tests` → **389 OK** (30 skip, gated por
  venv/MATLAB), exit 0. **preflight** → exit **0**.
- Commit: `[T9-calibracao]` (ver git log).

## 6. Pendências
Ver `T9-calibracao_REPASSE.md` D-1…D-6 (ratificação dos números; c154 1D/50D vs
1D/25D; confounder D97; D-dependência; RAM/M8; doc-sync params.json).
