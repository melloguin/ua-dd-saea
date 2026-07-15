# handoff/00-preflight.md — Sessão "Pré-voo" (resolver as 9 pendências das âncoras)

**Data:** 2026-07-15 · **Gate:** `python3 scripts/preflight.py --write` → **`pré-voo OK ✓`** (exit 0). ✅
**Escopo:** as 9 pendências do §7.4 do `HANDOFF_MESTRE.md` (Famílias A/B/C). NÃO tocou código de algoritmo.
**Obs. de ambiente:** neste Mac o interpretador é `python3` (não há `python` no PATH).

## Resultado
8/9 resolvidas + 1 deferimento intencional (desdeo-emo @ gate R3.2). Preflight verde e **idempotente**
(roda verde de novo sem `--write`). Arquivos alterados: `anchors.json`, `repos.lock`, `scripts/preflight.py`.
`envs.json` **não** foi alterado (o TODO do pin segue visível — nada cravado/fingido).

## Família A — paths com glob `...` resolvidos (só o campo `file`; conteúdo e linha já batiam)
- `e74-mask`      → `CLMEA_Code/Algorithms/Multi-objective optimization/CLMEA/Local_infill.m` (:47 ok)
- `e74-ndsort-obj`→ `CLMEA_Code/Algorithms/Multi-objective optimization/CLMEA/ClassifierSelect.m` (:9 ok)
- `b5-mode72-kde` → `desdeo_emo/selection/ProbMOEAD_select.py` (:65 KDE / :75 plt_density; expect descritivo)

## Família B — `expect_before` divergentes
- `b1-mse-guard-L8` (EvolALG.m:25): a linha real é alinhada por coluna (`s         = sqrt(mse);`), então o
  literal aparado não era substring. Reduzi para o token exato e único **`sqrt(mse);` → `sqrt(max(mse,0));`**
  (mesmo resultado do patch, robusto a espaçamento).
- `b4-cap109` (CSEA.m:29): idem → **`min(11*Problem.D-1,109);` → `11*Problem.D-1; % remover cap 109 (S.2#2)`**.
- `e81-offset1` (acquisition.py:219) e `e81-offset2` (acquisition.py:366): **as âncoras já estavam CORRETAS**
  (`torch.manual_seed(1024 + seed_iter)` e `seed=2430,`). O "DIVERGE" era um **falso-negativo do preflight**:
  ele achava `acquisition.py` só por *basename* e pegava `algorithms/_BoTorch/.../acquisition.py` (colide;
  `_BoTorch` ordena antes de `e81_qPOTS`). Corrigir a âncora aqui teria **corrompido** o patch real do R2/R3.
  → consertei a **resolução de arquivo do preflight** (ver abaixo). Âncoras do e81 intactas.

## Família C — placeholders
- **`repos.lock <SHA>`**: os campos `sha:"<SHA>"` eram vestigiais (repos content-hash pinam por `sha256_tree`).
  O preflight agora **zera `sha`→null** ao gravar o content-hash. Também: **e103 virou arquivos planos**
  (sem `.git`) → adicionei `e103_ibeams` ao `dir_map` do preflight (9º repo content-hash) e seu `sha256_tree`
  foi preenchido (`6a6fafb0e72b…`). Nota do `repos.lock` atualizada (não diz mais que e103 tem `.git`).
- **`envs.json <PIN A CRAVAR NO GATE R3.2>`** (desdeo-emo do b5): **deferimento intencional** (§7.4). Decisão do
  autor (ping-pong desta sessão): o preflight passa a **distinguir** `<PIN A CRAVAR …>` (deferimento explícito →
  NOTA, não bloqueia) de `<SHA>`/`<PIN>` (placeholder → bloqueia). O pin **continua a cravar no gate R3.2**.

## Mudanças em `scripts/preflight.py` (tooling, não-algoritmo — revisar se desejar)
1. **Resolução de âncora por sufixo de caminho**: junta todos os candidatos por basename e prefere o que
   *termina* com o `file` (repo-relativo) da âncora; fallback = 1º por basename (compat com âncoras só-basename).
   Determinístico e à prova da colisão `acquisition.py` (BoTorch × qPOTS). Não regride nenhuma âncora antiga.
2. **`dir_map` += `e103_ibeams: e103_IBEA-MS`** e, no ramo content-hash, **`meta["sha"]=None`** (limpa o `<SHA>`).
3. **Seção 3**: `<PIN A CRAVAR` classificado como **deferimento** (nota), não pendência. Resumo imprime
   `pré-voo OK ✓ (N deferimento(s) intencional(is))` e sai 0 quando não há pendência dura.

## Pendências que seguem abertas (por design)
- **desdeo-emo pin** → cravar no **gate R3.2** (cartão do b5). É o único deferimento reportado pelo preflight.
- Âncoras com `expect_before` **descritivo** (`c141-sde-eps-L4`, `e103-judgemodel`, `b1-doe-D94`, `e7-doe-D94`,
  `b3-updataarchive-guard`, `b5-mode72-kde`) — resolvidas **no cartão de cada algoritmo**, não no pré-voo.
- Nada foi commitado (não solicitado). Working tree: `M anchors.json, repos.lock, scripts/preflight.py`
  (+ `HANDOFF_MESTRE.md`, `HANDOFF_setup_executado.md` untracked).

## Próximo passo
Fase 0 — cartão **F0-01-harness** (bundle `00_fundacao/01–05`), conforme `START_HERE.md`.
