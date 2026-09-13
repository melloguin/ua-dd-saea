# R3-c311 — DOSSIÊ DE EXECUÇÃO COMPLETO (Fase 0 → A → B)

> **Documento único para a torre central.** Descreve TODO o processo de execução do cartão
> R3-c311 (TGPR-MO, treed-GP/GPy, OFFLINE, no Mac), etapa a etapa, com os comandos rodados e os
> resultados. Consolida os 3 handoffs (o quê / o como / repasse) num relato linear.
> **Data:** 2026-07-23 · **Branch:** `experiment/definitive_algorythms` · **Commits:** `4d8a997`,
> `ba55f18` (Fase A) · `fb4fc30`, `0a6fe8e` (Fase B).

---

## 0. SUMÁRIO EXECUTIVO — está pronto?

**SIM, o que é responsabilidade desta sessão está 100% pronto, VALIDADO por código, e committado.**
O cartão está FECHADO no sentido do **gate objetivo** (encanamento: FE, 7 camadas, CP-init, guardas,
ganchos, determinismo, não-perturbação, wiring). **Rodei código de validação em cada etapa** (a
tabela da §7 lista cada comando e seu resultado). Todos VERDES.

**A ÚNICA coisa PENDENTE não é minha:** o julgamento de **FIDELIDADE (D97)** — se o treed-GP
reproduz o paper/código do autor — é **MANUAL, do autor, a posteriori** (regra firme do repo). A
torre já pontuou o c311 provisoriamente em **7,5/10** (o melhor offline até aqui). Os pontos
específicos que o autor deve olhar no D97 estão na **§8** (é o que a torre deve me levantar).

| Dimensão | Estado |
|---|---|
| Runner `src/c311_tgprmo.py` (Fase A) | ✅ implementado, vendor INTOCADO + 4 ganchos runtime |
| Testes `tests/test_c311.py` (14) | ✅ verdes (env-main-safe + ganchos + runs completos) |
| 3 pilotos determinísticos (MMF1/DTLZ2/ZDT1) | ✅ VERDES em todos os gates |
| FIX obrigatório `nd_pos_real` (Fase B, DI-27) | ✅ aplicado + provado |
| Wiring (dispatch + accept + locks) (Fase B) | ✅ completo + despachante validado |
| Gate objetivo (accept/auditar/final_eval/suíte/preflight) | ✅ TODOS VERDES |
| Julgamento de FIDELIDADE (D97) | ⏳ do autor, a posteriori (torre: 7,5 provisório) |
| Definições EM ABERTO (que a torre deve me levantar) | ver §8 (3 pontos D97 + 1 nota de escopo) |

---

## 1. CONTEXTO E REGRAS (a "faixa em 2 fases")
Sessão coreografada para COEXISTIR com a sessão R3-b5 (ativa no mesmo repo). **Fase A** = só meus
arquivos (`src/c311_tgprmo.py`, `tests/test_c311.py`, `handoff/R3-c311*.md`, `data/experiments/off/c311/**`),
sem tocar a faixa do b5/torre. **Fase B** (gatilho: o b5 committar o wiring + comando do autor) =
o wiring compartilhado (`experiment.py`, `accept.py`, `requirements/**`). Regra de ouro: vendor
`algorithms/c311_TGPR-MO/**` INTOCADO — toda instrumentação por **monkeypatch em runtime** (o
precedente oficial do e81).

---

## 2. FASE 0 — GATE DE AMBIENTE (env_c311 + artefatos)
**Comandos rodados / resultados:**
- `git status --porcelain` no arranque → só a faixa do b5 (esperado, A.7). `preflight.py` = **VERDE**
  (meu vendored intacto, hash `e3b3f802dad9`).
- **env_c311 validado:** py3.8.20 x86_64/Rosetta · GPy 1.9.9 · numpy 1.20.2 · sklearn 1.1.2 ·
  Pillow 9.5.0 (<10) · pyarrow 17 · graphviz 0.20.3 · matplotlib 3.7.5. Sempre `MPLBACKEND=Agg`.
- **pymoo AUSENTE ⇒ instalei `pymoo==0.6.1.2`** (pré-autorizado) com constraints do freeze → o
  núcleo validado (numpy/GPy/sklearn/pyarrow) NÃO se moveu; puro-python (`py3-none-any.whl`);
  py3.8 tem `typing.Literal` nativo (SEM o shim do env_b5). Provas: GP treina+prediz ✅ ·
  `problems._nds_filter(evaluate_problem(...))` importa+roda ✅ · `load_sonda('MMF1',regime='offline')` ✅ ·
  os 3 datasets carregam com x_hash **E** f_hash ✅.
- **Datasets + sonda já existiam** (committados; D90 = carregar, nunca gerar) → nada regenerado.
- **Suíte env-main:** `Ran 295 · OK (skipped=7)`. **preflight VERDE.**
- **Seeds:** `alg_id.c311 = 19`. `uso_id` não catalogado → apliquei o `_default`/0 (receita L.17).

---

## 3. ENTENDIMENTO (workflow read-only, 8 leitores + síntese)
Antes de codar, um workflow multi-agente (só leitura) digeriu em paralelo: harness/export APIs ·
padrão dos ganchos e81 · prova de não-perturbação c122 · o vendored c311 (fluxo + mecanismo) ·
REGISTRO A10–A14 + REPASSEs · seeds/envs/gates. **Verifiquei na fonte** os pontos críticos (não
confiei só na síntese): DI-16.12 (2 blocos de sonda) no REGISTRO:734; a seleção `"mean"` do
`APD_Select_constraints` lê SÓ `pop.fitness` (nunca `uncertainity`) — a base da não-perturbação
do σ; o `_current_gen_count` inclui o +1 do `_refresh_population` (RVEA.py:191).

---

## 4. FASE A — RUNNER (`src/c311_tgprmo.py`, molde run_stubr3, vendor intocado)
Fluxo OFFLINE 2-fases (o dataset É o orçamento, D90): **construção** (árvore MSE
`min_samples_leaf=10D`/`max_depth=100` por objetivo + RVEA `Imax=N/(10D)`×`Gmax=50`, 1 GP na folha
de maior impureza/iteração, `_refresh_population` +1 ger/iter, early-stop `it>5`) → **final** (RVEA
`10×100=1000` ger sobre o surrogate FIXO) → ⑦ (todos os finais avaliados 1× na verdade; ND
filtrado DEPOIS — DI-13.9). **4 ganchos em runtime (vendor bit-a-bit):**
1. **σ (B15.5)** — expõe `σ=sqrt(var_GPy)` que o `treeGP.predict` descartava; μ BYTE-idêntico ao
   stock; NaN nas folhas só-árvore; σ NUNCA σ² (DI-16.9). A seleção "mean" ignora σ ⇒ não-perturbação
   por construção.
2. **predict_batch (DI-16.13)** — vetoriza a predição da sonda (20.000 pts) por folha.
3. **snapshot + contador C311-11 (DI-16.19)** — ③ por geração com contador ÚNICO e monotônico
   atravessando as 2 fases (fase no `modelo_flag`, não colide em 1..50).
4. **lhs-determinismo** — semeia o `lhs` da pop inicial do RVEA (ver §5, achado 2).

### 4-bis. 🔴 DOIS achados de DETERMINISMO (o debugging que valeu a sessão)
O smoke fechou de 1ª, mas o gate de **determinismo** (2 runs ⇒ ⑦ bit-a-bit) REPROVOU. Diagnóstico
em camadas localizou DUAS causas — NENHUMA no algoritmo, ambas de AMBIENTE:
1. **BLAS multi-thread**: o `pin_runtime` NÃO limita threads em env SEM torch (só registra; o pin
   autoritativo é o `run_in_venv`). Invocação direta sem `OMP/OPENBLAS=1` ⇒ ruído de redução que
   1000 gerações amplificam. **Fix:** env-vars no topo do módulo + `threadpoolctl.threadpool_limits(1)`.
2. **🔴 DRIFT do pyDOE (a causa MAIOR)**: o env resolveu um pyDOE NOVO cujo `lhs(seed=None)` usa um
   `RandomState` PRÓPRIO (entropia), NÃO o `np.random` global. Prova (diag): o estado global fica
   IDÊNTICO após `RVEA.__init__`, mas a pop inicial VARIA. **Fix (4º gancho):** injeta `seed=`
   derivado do global semeado. **⚠ Vale para TODA a família desdeo — o b5 herda o mesmo fix.**

Um TERCEIRO "falso-positivo" (não-perturbação): o `assertEqual(dict)` reprovava `NaN==NaN` espúrio
(σ=NaN nas folhas só-árvore). Bug do TESTE (não do runner) — corrigido p/ `pandas.equals` (NaN-aware).

---

## 5. FASE A — GATES E PILOTOS (exp='off', semente 0)
| piloto | status | n_geracoes | ③ linhas | ② | sonda | n_final | ND-real | wall |
|---|---|---|---|---|---|---|---|---|
| MMF1  | ok | 1204 | 90124  | 0 | 2 | 46 | 10 | 23–29 s |
| DTLZ2 | ok | 1204 | 131779 | 0 | 2 | 84 | 77 | 58–70 s |
| ZDT1  | ok | 1204 | 96467  | 0 | 2 | 50 | 50 | 44–49 s |

`n_geracoes=1204` = construção (4×51=204, inclui o +1/iter do refresh) + final (1000). ② VAZIA por
construção (DI-16.17: a pop RVEA são candidatos gerados, ≠ dataset). **2 blocos de sonda**
(treedGP_build + treedGP_final, geracao=NULL, DI-16.12). **Gates Fase A (rodados):** determinismo
✅ (2 runs ⇒ ⑦ bit-a-bit + prova live vs data/) · não-perturbação §3.1 ✅ (sonda off vs on ⇒ ⑦ e
③-busca idênticas, NaN-aware) · auditar VERDE ×3 · final_eval --check VERDE ×3. Commits `[R3-c311]`
Fase A: `4d8a997` (runner+testes), `ba55f18` (handoffs).

---

## 6. FASE B — FIX OBRIGATÓRIO + WIRING (gatilho: [R3-b5] committado + comando do autor)
**Reconheci o novo git log:** `[R3-b5]` wiring (`e3ecab1`/`8847f0a`), `b782167` (DI-27: `-I`→`-s`
+scrub que faz o PYTHONHASHSEED=0 valer · tree_sha256 sem .pyc + repos.lock re-lacrado · warning do
final_eval silenciado), `4aec48c` (DI-28: as 7 ratificações — **as minhas 3 pendências fechadas**).

### 6.1 🔴 FIX OBRIGATÓRIO (achado ALTA, DI-27/A15) — aplicado
O runner passava `nd_pos_real` calculado no **float64 CRU** ao `write_final` — o anti-padrão que a
docstring proíbe (o b5 mediu b5m/ZDT1: 20≠19 no `--check`; meus 3 pilotos passavam SÓ por ausência
de empate de borda). **Fix (molde `b5_prob.py`):** OMITO `nd_pos_real` (o `write_final` o calcula na
**vista float32** que a ⑦ persiste e o `--check` relê) + conto o ND do footer na MESMA vista.
Pilotos re-rodados (contagens iguais: sem empate de borda nestes, mas agora CONSISTENTE com o `--check`).

### 6.2 Wiring
- `src/experiment.py:159` — descomentei `'c311': ('src.c311_tgprmo','run_c311','standalone')`.
- `scripts/accept.py` — `check_r3_c311` (molde `check_r3_b5`; adapta: ③ **2 blocos** de sonda =
  40000 geracao-NULL; ③-busca contador ÚNICO 1..N modelo_flag∈{treedGP_build,treedGP_final}; ④
  1-linha/retreino) + branch ADITIVO `R3-c311` ANTES do catch-all F0-01.
- `requirements/env_c311.txt` + `locks/env_c311.lock.txt` (regenerado, `pip freeze`) +
  `PROVISIONAMENTO.md §3` — registram `pymoo==0.6.1.2` + o stub `optproblems` + a ratificação do
  gancho pyDOE (DI-28.3). **NÃO** toquei `repos.lock`/`anchors.json`/pyDOE (re-lacrados pela torre
  em `b782167`; DI-28.3 = gancho lhs DEFINITIVO, sem patch vendorizado).

### 6.3 Coexistência com R3-piso-off (Fase A ativa)
`git diff --cached` vazio antes de cada `add`; NUNCA toquei `src/piso_offline.py`/`test_piso_off.py`/
`moead_media/**`. Commits `[R3-c311]` Fase B: `fb4fc30` (fix+wiring), `0a6fe8e` (handoffs) — só
arquivos meus, staged-check por commit, **sem push, sem `-A`**.

---

## 7. VALIDAÇÃO POR CÓDIGO — todos os comandos e resultados (RESPOSTA À PERGUNTA "você rodou código?")
| # | Comando (env) | Resultado |
|---|---|---|
| 1 | `preflight.py` (env-main) | **VERDE** (exit 0) — lacres/âncoras OK, meu vendored intacto |
| 2 | `unittest discover -s tests` (env-main) | **`Ran 321 · OK (skipped=22)`** (309→321: os testes do piso-off entraram e estão verdes) |
| 3 | GPy fit+predict + ND-filter + load_sonda/load_dataset (env_c311) | **OK** (provas Fase 0) |
| 4 | `accept.py R3-c311 --alg c311 --problema {MMF1,DTLZ2,ZDT1} 0 --exp off` (env-main) | **VERDE ×3, 10 checks cada** (6-7 camadas · FE=31D−1=dataset bit-a-bit · CP-init x_hash E f_hash · ② vazia OK · ③ sonda 2×20000 geracao-NULL · ③ busca 1..1204 · μ/σ · ④ 4 linhas · ⑤ manifesto · ⑦ reconstituível) |
| 5 | `auditar.py c311 {…} 0 --exp off --regime offline` (env-main) | **VERDE ×3** |
| 6 | `final_eval.py --alg c311 --problema {…} --semente 0 --check` (env-main) | **VERDE ×3** (⑦ presente+consistente: 46/10, 84/77, 50/50) |
| 7 | `unittest TestRunCompleto` C311_SLOW=1 (env_c311) | **`Ran 3 · OK`** — determinismo + 7-camadas + não-perturbação §3.1 |
| 8 | determinismo live: re-run vs data/ (env_c311) | ⑦ re-run **== ⑦ piloto: True** |
| 9 | **despachante e2e:** `experiment.run('c311','MMF1',0)` → subprocess env_c311 (env-main) | status=ok; **⑦ do subprocesso == ⑦ do piloto direto: True** (valida o dispatch + determinismo cross-invocação) |

(Todos re-executados AO VIVO no fechamento; §7 é o retrato do estado ATUAL do repo committado.)

---

## 8. 🔴 DEFINIÇÕES EM ABERTO — a torre DEVE levantar com o autor para DECIDIR

> **Resumo honesto:** NÃO há definição NOVA que BLOQUEIE o cartão — as 3 pendências da Fase A foram
> FECHADAS pelo autor (DI-28: `uso_id`=_default/0 · gancho lhs DEFINITIVO · ④=1/retreino) e o FIX da
> torre foi aplicado. O que resta é **o julgamento de FIDELIDADE (D97), que é do autor** — e os
> pontos ESPECÍFICOS do c311 que o autor deve olhar (a torre me levanta estes para decidirmos):

**D1 — Fidelidade da INIT-POP sob o gancho pyDOE (o mais material).** O gancho lhs-determinismo
(DI-28.3, ratificado como MECANISMO) faz o `lhs` da pop inicial ser reprodutível da semente, MAS os
valores da init-pop LHS **diferem** dos de um pyDOE clássico (é uma réplica determinística, sequência
diferente). Como a init-pop semeia toda a busca, o autor deve **decidir/declarar** se o resultado do
c311 (nota 7,5) é "fiel o bastante" ou se vira caveat de análise na dissertação (mesmo padrão do
caveat c217/δ=0,8). *Não muda código; é um selo de fidelidade.*

**D2 — σ das folhas é EXTENSÃO NOSSA (B15.5), não do paper.** O paper anuncia σ e NUNCA o consome;
nosso patch o EXPÕE (`sqrt(var_GPy)`, NaN nas folhas só-árvore). O autor deve **confirmar/declarar**
isso como extensão nossa na dissertação (ponto honesto e interessante — o "único treed-GP" que nem
usa o σ que motiva sua inclusão no nosso eixo de incerteza).

**D3 — Nuances código≠paper a ratificar no D97:** (a) o contador `geracao` da CONSTRUÇÃO conta
**204 (=4×51)**, incluindo o +1/iter do `_refresh_population` (não 200) — é o que a C311-11 pede,
mas o autor deve ratificar a semântica; (b) o **early-stop** (`delta=total_pts−seq[it−3]`, `it>5`)
é o do CÓDIGO, ≈ o do paper com persistência (B15.8, rebaixada a nuance) — INATIVO nos pilotos
small (4 iters < 5); no tier big pode ativar. Ambos são "fidelidade a olhar", sem decisão de código.

**N1 — Nota de ESCOPO (não é decisão, é para não surpreender):** os 3 pilotos rodaram no tier
**SMALL** (31D−1). O achado-alvo do c311 (a curva de escalabilidade O(n) do treed-GP) é o tier
**BIG (50k)**, que é um SUB-ESTUDO à parte (§11.5 sweep, VM/M8+) — **fora deste cartão**. Confirmar
a fronteira: o c311-big e o piso-off-big (treed-GP-média, DI-16.5) são outras sessões.

*(Se o autor quiser algo além do encanamento — ex.: uma linha ④ para a fase FINAL, que hoje entra
só no agregado do manifesto — é uma decisão nova; hoje segue a DI-28.5 "④=1/retreino".)*

---

## 9. MANIFESTO DE ARQUIVOS E COMMITS
**Meus arquivos (Fase A + B):** `src/c311_tgprmo.py` · `tests/test_c311.py` · `src/experiment.py`
(1 linha) · `scripts/accept.py` (+`check_r3_c311`+branch) · `requirements/env_c311.txt` ·
`requirements/locks/env_c311.lock.txt` · `requirements/PROVISIONAMENTO.md` (§3) ·
`handoff/R3-c311{,_RELATORIO-EXECUCAO,_REPASSE-A-TORRE,_DOSSIE-EXECUCAO}.md` ·
`data/experiments/off/c311/**` (gitignored — artefato local, como todo config).
**Commits `[R3-c311]`:** `4d8a997` · `ba55f18` · `fb4fc30` · `0a6fe8e` (branch
`experiment/definitive_algorythms`; nunca push).
**NÃO tocado:** vendor `algorithms/c311_TGPR-MO/**` · `repos.lock` · `anchors.json` · pyDOE · a
faixa do b5 · a faixa do piso-off.
