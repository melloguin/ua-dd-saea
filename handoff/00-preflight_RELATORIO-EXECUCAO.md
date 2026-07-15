# RELATÓRIO DE EXECUÇÃO — Sessão 1 "Pré-voo" (resolver as 9 pendências das âncoras)

> **Para quem é este documento.** Para a instância que redigiu `HANDOFF_MESTRE.md` / `START_HERE.md`
> entender **exatamente** o que a instância de implementação fez no pré-voo, **como**, **por que** houve
> desvios do roteiro do §7.4, e **quais resultados** foram atingidos — com evidência arquivo:linha e diffs.
> **Data:** 2026-07-15 · **Repo:** `ua-dd-saea` · **Branch:** `experiment/definitive_algorythms`
> **Escopo:** só o pré-voo (âncoras + repos.lock + política de placeholder do preflight). **Zero** código de algoritmo tocado.

---

## 0. TL;DR (resultado)

- **Gate atingido:** `python3 scripts/preflight.py --write` → **`pré-voo OK ✓`** e **exit 0**. Idempotente
  (roda verde de novo, mesmo sem `--write`).
- **9 pendências → 8 resolvidas + 1 deferimento intencional** (pin do `desdeo-emo`, cravado no gate R3.2).
- **Arquivos alterados (3):** `claude_code_context/artifacts/anchors.json`, `claude_code_context/artifacts/repos.lock`,
  `scripts/preflight.py`. **`envs.json` NÃO foi alterado** (o TODO do pin segue visível — nada cravado/fingido).
- **2 desvios materiais do §7.4** que a instância de origem deve reter (detalhe no §5):
  1. As 2 âncoras do `e81` **já estavam corretas**; o "DIVERGE" era **falso-negativo do preflight** (colisão de
     basename `acquisition.py` entre `_BoTorch` e `e81_qPOTS`). Corrigir a âncora teria **corrompido** o patch real.
  2. `repos.lock <SHA>` e o `e103` exigiram **conserto de tooling** (não era "só apagar placeholder"): `e103`
     virou **arquivos planos** (sem `.git`) e não estava no `dir_map` do preflight.
- **Nada foi commitado** (não solicitado).

---

## 1. Contexto lido (ordem exata)

Li, nesta ordem: `HANDOFF_MESTRE.md` → `START_HERE.md` → `CLAUDE.md` (raiz) → `claude_code_context/CLAUDE.md`
→ `scripts/preflight.py` → `claude_code_context/artifacts/{anchors.json, repos.lock, envs.json}`. Reforcei os
princípios D81 (pára-e-loga em conflito), D83 (precedência), D97 (fidelidade = manual do autor) — e agi como
instância de implementação. **Ambiente:** neste Mac o interpretador é **`python3`** (`python` não existe no PATH —
`command not found`); registrei isso no handoff de continuidade.

---

## 2. Diagnóstico — as 9 pendências REAIS (baseline)

`python3 scripts/preflight.py` (sem `--write`), saída resumida inicial:

```
== RESUMO ==
  9 pendência(s):
   - anchors[e74-mask]: file não-resolvido ('CLMEA_Code/.../CLMEA/Local_infill.m')
   - anchors[b1-mse-guard-L8]: expect_before ausente em EvolALG.m
   - anchors[b4-cap109]: expect_before ausente em CSEA.m
   - anchors[e74-ndsort-obj]: file não-resolvido ('CLMEA_Code/.../CLMEA/ClassifierSelect.m')
   - anchors[e81-offset1]: expect_before ausente em acquisition.py
   - anchors[e81-offset2]: expect_before ausente em acquisition.py
   - anchors[b5-mode72-kde]: file não-resolvido ('desdeo_emo/.../ProbMOEAD_select.py')
   - repos.lock: placeholder '<SHA>' pendente
   - envs.json: placeholder '<PIN A CRAVAR' pendente
```

Mapeamento às Famílias do §7.4: **A** = e74-mask, e74-ndsort-obj, b5-mode72-kde (path com `...`);
**B** = b1-mse-guard-L8, b4-cap109, e81-offset1, e81-offset2 (`expect_before`); **C** = `<SHA>` (repos.lock)
e `<PIN A CRAVAR` (envs.json / desdeo-emo).

---

## 3. Execução passo-a-passo por família (com evidência)

### Família A — paths com glob `...` (3). *Só o campo `file`; conteúdo e linha já batiam.*
Localização real (via `find algorithms -name …`):

| âncora | `file` resolvido (repo-relativo) | verificação de conteúdo |
|---|---|---|
| `e74-mask` | `CLMEA_Code/Algorithms/Multi-objective optimization/CLMEA/Local_infill.m` | linha 47 = `x_candidates = [x_candidates; x_offspring(Choose,:)];` ✔ (literal, confere) |
| `e74-ndsort-obj` | `CLMEA_Code/Algorithms/Multi-objective optimization/CLMEA/ClassifierSelect.m` | linha 9 = `[y_label,~] = NDSort(Parent,inf);` ✔ (literal, confere) |
| `b5-mode72-kde` | `desdeo_emo/selection/ProbMOEAD_select.py` | :65 `##### KDE here…` / :75 `pwrong_current.plt_density(…)` ✔ (bate o expect descritivo) |

*O `...` foi a única causa da falha (o preflight rejeita `*`/`...`). Os paths novos são **sufixos exatos**
dos caminhos reais sob `algorithms/`, consistentes com as âncoras do PlatEMO (que já eram repo-relativas).*

### Família B — `expect_before` (4). *Dois casos genuínos + dois falso-negativos.*

**b1-mse-guard-L8 (EvolALG.m:25) e b4-cap109 (CSEA.m:29) — divergência REAL (whitespace por coluna).**
As linhas reais são alinhadas por coluna, então o literal aparado do §7.4 não era substring:
```
EvolALG.m:25  ->  '            s         = sqrt(mse);'          (repr exato; note os espaços internos)
CSEA.m:29     ->  '            N          = min(11*Problem.D-1,109);'
```
Correção adotada: **token exato, único e robusto a espaçamento** (mesmo resultado do patch original):
- `b1`: `expect_before` `s = sqrt(mse);` → **`sqrt(mse);`** ; `expect_after` `s = sqrt(max(mse,0));` → **`sqrt(max(mse,0));`**
- `b4`: `expect_before` `N = min(11*Problem.D-1,109);` → **`min(11*Problem.D-1,109);`** ; `expect_after`
  `N = 11*Problem.D-1; …` → **`11*Problem.D-1; % remover cap 109 (S.2#2)`**

Unicidade confirmada por grep: `sqrt(mse)` só na :25; `min(11*Problem.D-1,109)` só na :29 (a :61 tem
`min(rr,1-rr)`). O patcher real faz find/replace inequívoco; o código resultante é idêntico ao pretendido.

**e81-offset1 (acquisition.py:219) e e81-offset2 (acquisition.py:366) — NÃO eram âncoras erradas.**
Conteúdo real confere byte-a-byte:
```
acquisition.py:219 -> '        torch.manual_seed(1024 + seed_iter)'   (== expect_before da âncora)
acquisition.py:366 -> '                seed=2430,'                    (== expect_before da âncora)
```
Raiz do "DIVERGE": o preflight resolvia `acquisition.py` **só por basename** via `os.walk`, e havia **DUAS**:
```
algorithms/_BoTorch/botorch/acquisition/acquisition.py   <- os.walk pega esta 1º (_BoTorch < e81_qPOTS)
algorithms/e81_qPOTS/qpots/acquisition.py                <- a correta (alvo da âncora)
```
Ele validava a de `_BoTorch` (onde os strings não existem) → falso-negativo. **As âncoras do e81 foram
mantidas intactas**; consertei a **resolução de arquivo do preflight** (§6.1). Editar a âncora para "passar"
teria corrompido o patch real que o R2/R3 aplica no `qpots/acquisition.py`.

### Família C — placeholders (2).

**`repos.lock <SHA>` — campos vestigiais + `e103` faltando no tooling.**
Os 8 repos "content-hash" tinham `sha:"<SHA>"` inútil (o pin real é `sha256_tree`). Além disso descobri que
**`e103` agora são arquivos planos** em `algorithms/e103_IBEA-MS/` **sem `.git` próprio** (confere o
`START_HERE.md`: "e103 versionado como arquivos planos"), mas o `repos.lock` ainda dizia "e103 @c3e8733 têm
.git" e o `dir_map` do preflight **não incluía** `e103` → seu `sha256_tree` ficava `<preencher no pre-flight>`
para sempre. Resolução: ver §6.2 (o preflight passa a pinar e103 e a zerar `sha`→`null`).

**`envs.json <PIN A CRAVAR NO GATE R3.2>` (desdeo-emo do b5) — deferimento intencional (§7.4).**
Conflito real: o §7.4 diz que é intencional (cravar no R3.2), mas o check estrito de placeholder fazia o
preflight sair `1` → nunca imprimia `pré-voo OK ✓`. **Parei e perguntei ao autor (D81).** Ver §7.

---

## 4. Ponto de decisão (D81) e ruling do autor

**Pergunta apresentada (ping-pong, 3 opções):** como fechar a Sessão 1 dado que o único item restante é o
deferimento intencional do desdeo-emo?
1. *(recomendada)* Ensinar o preflight a **distinguir deferimento explícito** (`<PIN A CRAVAR …>`) de placeholder
   duro (`<SHA>`/`<PIN>`) → vira NOTA, não bloqueia; artefato mantém o TODO visível.
2. Manter estrito; fechar em "8/9 + 1 deferimento" (sem a linha literal verde).
3. Cravar um sentinela agora (não recomendada — assa pin falso).

**Ruling do autor:** **Opção 1** — "Preflight reconhece o deferimento". Implementado no §6.3.
Consequência: o pin do desdeo-emo **continua a cravar no gate R3.2**; nada foi cravado agora.

---

## 5. Desvios materiais do §7.4 (o que a instância de origem deve reter)

1. **e81 não era "ajustar expect_before".** As âncoras `e81-offset1/2` estavam corretas; o problema era o
   **matcher por basename** do preflight colidindo com a `acquisition.py` vendorizada do BoTorch. Classificar
   isso como Família B ("expect_before ausente") induz ao erro de mexer na âncora certa. **Sugestão:** no §7.4,
   reclassificar e81 como "colisão de basename no preflight (tooling)", não como âncora divergente.
2. **`repos.lock <SHA>` + `e103` eram tooling, não "apagar placeholder".** `e103` migrou para arquivos planos
   e não estava no `dir_map`; o `<SHA>` era vestigial dos repos content-hash. **Sugestão:** o `repos.lock`/§6.4
   da SPEC deveria listar **9** repos content-hash (incluir `e103`) e descrever `sha:null` para eles.
3. **`python` vs `python3`.** O `START_HERE.md`/`HANDOFF` mandam `python scripts/preflight.py`; neste Mac só há
   `python3`. **Sugestão:** padronizar para `python3` (ou criar alias/shim) nas instruções de arranque.
4. **Nenhum desvio de projeto.** Nada disso indica falha de desenho — só dessincronização de artefato/tooling,
   coerente com o veredito da auditoria. Os 8 patches literais conferiram exatamente onde o §7.4 esperava.

---

## 6. Mudanças em `scripts/preflight.py` (tooling; revisar se desejar)

Três mudanças, todas retrocompatíveis (nenhuma âncora antes-OK regrediu):

### 6.1 Resolução de âncora por **sufixo de caminho** (conserta a colisão e81)
Antes: pegava o 1º basename no `os.walk`. Agora: junta todos os candidatos e prefere o que **termina** com o
`file` (repo-relativo) da âncora; fallback = 1º por basename (compat com âncoras só-basename, ex.: e103).
Determinístico e à prova de colisão. (Também blinda `c149`, cuja `BO_surrogate_function_uncertainty.py`
existe em 4 cópias — o sufixo mantém o alvo de topo.)

### 6.2 `dir_map += e103_ibeams: e103_IBEA-MS` e limpeza do `<SHA>`
No ramo content-hash, além de gravar `sha256_tree`, agora faz `meta["sha"]=None` (limpa o `<SHA>`). `e103`
passa a ser pinado como 9º content-hash (`sha256_tree` = `6a6fafb0e72b…`). Nota do `repos.lock` atualizada.

### 6.3 Seção 3: deferimento ≠ placeholder
`HARD_PH=["<SHA>","<PIN>"]` bloqueiam; `DEFER_PH=["<PIN A CRAVAR"]` vira NOTA "(deferido)". O resumo imprime
`pré-voo OK ✓ (N deferimento(s) intencional(is) — ver seção 3)` e sai 0 quando não há pendência dura.
Observação de segurança: `<PIN>` (com `>`) **não** casa dentro de `<PIN A CRAVAR NO GATE R3.2>` (após `<PIN`
vem espaço, não `>`), então não há falso-bloqueio.

*(Diff exato dos 3 arquivos no §9.)*

---

## 7. Verificação final (evidência)

```
# 1) gate principal
$ python3 scripts/preflight.py --write
== 3. placeholders remanescentes ==
  (deferido) - envs.json: deferimento intencional '<PIN A CRAVAR ...>' (cravar no gate indicado)
== RESUMO ==
  pré-voo OK ✓ (1 deferimento(s) intencional(is) — ver seção 3)      # exit 0

# 2) idempotência (sem --write)
$ python3 scripts/preflight.py ; echo $?
0

# 3) e81 resolve para o arquivo CERTO agora (checagem independente, replicando o matcher)
e81-offset1 -> algorithms/e81_qPOTS/qpots/acquisition.py   expect_before in file? True
e81-offset2 -> algorithms/e81_qPOTS/qpots/acquisition.py   expect_before in file? True
c149-fix-M  -> algorithms/c149_LBN-MOBO/BO_surrogate_function_uncertainty.py   in file? True

# 4) nada foi cravado no envs.json
$ grep -n "PIN A CRAVAR" claude_code_context/artifacts/envs.json
79:        "desdeo-emo==<PIN A CRAVAR NO GATE R3.2>",
```

Seção 2 do preflight, estado final das 20 âncoras: **12 `OK` (literais conferidos)** +
**6 "(expect descritivo — resolver no cartão)"** (`c141-sde-eps-L4`, `e103-judgemodel`, `b1-doe-D94`,
`e7-doe-D94`, `b3-updataarchive-guard`, `b5-mode72-kde`) + **2 e81 agora OK**. Zero DIVERGE.

---

## 8. O que segue ABERTO por design (não é dívida do pré-voo)

- **Pin do `desdeo-emo`** → cravar no **gate R3.2** (cartão do b5). Único deferimento reportado.
- **6 âncoras com `expect_before` descritivo** → resolvidas **no cartão de cada algoritmo** (não no pré-voo),
  exatamente como o preflight sinaliza.
- **Sem commit.** Working tree: `M anchors.json`, `M repos.lock`, `M scripts/preflight.py`
  (+ `HANDOFF_MESTRE.md`, `HANDOFF_setup_executado.md` untracked). Mensagem sugerida se for commitar:
  `chore(preflight): resolve 9 âncoras do pré-voo (Famílias A/B/C; matcher por sufixo; e103 content-hash)`.

---

## 9. Diff completo (3 arquivos)

### 9.1 `claude_code_context/artifacts/anchors.json` (5 âncoras)
```diff
- "file": "CLMEA_Code/.../CLMEA/Local_infill.m",
+ "file": "CLMEA_Code/Algorithms/Multi-objective optimization/CLMEA/Local_infill.m",
--- (b1-mse-guard-L8)
- "expect_before": "s = sqrt(mse);",
- "expect_after": "s = sqrt(max(mse,0));"
+ "expect_before": "sqrt(mse);",
+ "expect_after": "sqrt(max(mse,0));"
--- (b4-cap109)
- "expect_before": "N = min(11*Problem.D-1,109);",
- "expect_after": "N = 11*Problem.D-1; % remover cap 109 (S.2#2)",
+ "expect_before": "min(11*Problem.D-1,109);",
+ "expect_after": "11*Problem.D-1; % remover cap 109 (S.2#2)",
--- (e74-ndsort-obj)
- "file": "CLMEA_Code/.../CLMEA/ClassifierSelect.m",
+ "file": "CLMEA_Code/Algorithms/Multi-objective optimization/CLMEA/ClassifierSelect.m",
--- (b5-mode72-kde)
- "file": "desdeo_emo/.../ProbMOEAD_select.py",
+ "file": "desdeo_emo/selection/ProbMOEAD_select.py",
```
*(e81-offset1/2 NÃO aparecem no diff — mantidas intactas de propósito.)*

### 9.2 `claude_code_context/artifacts/repos.lock`
- `note`: atualizada (e103 é flat/content-hash; 9 repos; preflight zera `sha`).
- 9 entradas content-hash: `"sha": "<SHA>"` → `"sha": null`.
- `e103_ibeams.sha256_tree`: `"<preencher no pre-flight>"` → `"6a6fafb0e72bb90c4b2ed73696bd59300a7d88bfd7cb18eebfb5abc40ed20941"`.

### 9.3 `scripts/preflight.py`
- `dir_map += "e103_ibeams": "e103_IBEA-MS"`.
- ramo content-hash: `+ meta["sha"] = None`.
- resolução de arquivo: basename→**sufixo de caminho** (candidatos + `endswith(norm)`, fallback 1º).
- seção 3: split `HARD_PH` (bloqueia) × `DEFER_PH` (nota); resumo imprime deferimentos e sai 0.

---

## 10. Artefatos deixados no repo
- `handoff/00-preflight.md` — handoff de continuidade curto (a próxima sessão lê este).
- `handoff/00-preflight_RELATORIO-EXECUCAO.md` — **este relatório** (para repasse à instância de origem).

**Próximo passo do plano:** Fase 0 · cartão **F0-01-harness** (bundle `00_fundacao/01–05`), por `START_HERE.md`.
