# R3-c311 — REPASSE À TORRE

> Validação **re-executada AO VIVO** nesta sessão + definições em aberto que **a torre DEVE
> levantar com o autor**. Cartão R3-c311 (TGPR-MO, OFFLINE). **FASE A COMPLETA**; Fase B (wiring)
> aguarda o commit do b5 + o comando do autor.

## 1. O que foi entregue (Fase A) e o que falta (Fase B)
**Entregue (arquivos meus):** `src/c311_tgprmo.py` · `tests/test_c311.py` · `handoff/R3-c311*.md`
(3) · `data/experiments/off/c311/**` (3 pilotos). Vendored `c311_TGPR-MO/**` INTACTO.

**Fase B (por desenho, NÃO iniciada — faixa da torre/b5):** descomentar o dispatch do c311
(`experiment.py:156`); branch aditivo `check_r3_c311` no `accept.py` (antes do catch-all F0-01);
registrar `pymoo==0.6.1.2` do env_c311 no lock + PROVISIONAMENTO §3; SE houver patch a
materializar (ver §2.2), aplicar no vendored + âncora + re-lacre; `accept.py R3-c311 ×3`; suíte
completa + preflight no fechamento; commits finais.

## 2. 🔴 DEFINIÇÕES EM ABERTO — a torre DEVE levantar com o autor
### 2.1 `uso_id` do c311 não catalogado no `seeds.json`
`seeds.json:uso_id_catalogo` lista só online (c262/c154/c149/e81) + `_default` (uso_id=0 p/
"algoritmos sem RNG concorrente do harness"). O c311 se encaixa no `_default` (a sonda é
determinística, sob `preserve_all_rng`; não há RNG do harness concorrente dentro de uma iteração).
**Apliquei a receita L.17 literal:** `s = iteration_seed(seed_base('c311',semente), 19, 0, 0,
bits32=True)`; `np.random.seed(s); random.seed(s)` (o MESMO `s` p/ numpy e stdlib). **Torre:**
ratificar o `_default`/uso_id=0 (ou catalogar explicitamente o c311). Não editei o `seeds.json`.

### 2.2 🔴 DRIFT do pyDOE no env_c311 (a que exigiu o 4º gancho)
O `env_c311` resolveu um **pyDOE NOVO** (o pip do PROVISIONAMENTO §3 instala `pyDOE` **SEM pin**).
A pop inicial do RVEA usa o design `"LHSDesign"` (`Population.py:116`) ⇒ `lhs(n, samples)` **sem
seed**. Nesse pyDOE, `lhs(seed=None)` usa um `RandomState` PRÓPRIO (entropia do SO), **não** o
`np.random` global. **Prova (diag desta sessão):** o estado global fica IDÊNTICO após
`RVEA.__init__`, mas a pop inicial VARIA ⇒ o run é NÃO-determinístico (⑦ diverge em 0.28). A
receita L.17 ("pyDOE lhs pelo global") assumia o pyDOE ANTIGO.
**Correção mínima (GANCHO 4, `_lhs_determinismo`, runtime, vendor-intocado):** injeta `seed=`
derivado do `np.random` global (que o runner semeia por iteration_seed) ⇒ lhs volta determinístico
e atado à semente. **Torre / autor:** decidir entre (a) **PINAR** o pyDOE p/ a versão antiga
(lhs pelo global) e remover o gancho — restaura a trajetória do autor; OU (b) **RATIFICAR** o
gancho — a init-pop LHS difere de um pyDOE antigo, mas é um LHS **válido e reprodutível** da
semente. **Fidelidade da init-pop é D97 (do autor).** Se (a), é patch de env/lock (Fase B).

### 2.3 Granularidade da ④ (timing)
Decisão minha (documentada no `sigma_dict.timing_4`): **④ = 1 linha por RETREINO de construção**
(cada `addGPs`; `fit_series` MULTI-linha, C311-09 — o eixo da escalabilidade treed-GP). A fase
FINAL (sem retreino) e as 2 sondas entram no **agregado do manifesto** (não geram linha ④).
`n_acumulado` = pontos GP acumulados; `tempo_geracao_s` EXCLUI a sonda (DI-13.10). **Torre:**
confirmar que "1 linha por retreino" satisfaz a §17.6 p/ o c311 (o CONTRATO diz "por
geração/retreino"; escolhi retreino, coerente com e103/D-09).

### 2.4 Contagem de `geracao` da construção inclui o `_refresh_population`
C311-11 diz "building = 1..(Imax_eff×50)". O `_current_gen_count` do RVEA **inclui o +1/iteração
do `_refresh_population`** (RVEA.py:191-205) ⇒ na prática a construção conta **51/iteração** (4
iters ⇒ geracao 1..204). É o que a própria decisão pede ("incluindo a +1/iteração do
_refresh_population"). Uso o `_current_gen_count` como fonte da verdade (o contador do autor),
com offset p/ a fase final. **Torre:** confirmar a leitura (204, não 200, na construção).

### 2.5 Observação (não-bloqueante): warning do `final_eval` na sonda NULL
O `final_eval.py:107` (`np.asarray(tbl.column("geracao"), dtype=np.int64)`) emite
`RuntimeWarning: invalid value in cast` porque a ③ tem `geracao=NULL` nos 40.000 de sonda
(correto, DI-16.12). É COSMÉTICO (comum a TODO config offline com sonda); o `--check` passa VERDE.
Não é defeito do c311; a torre pode querer silenciar no script (fora da minha faixa).

## 3. VALIDAÇÃO RE-EXECUTADA AO VIVO (comandos + saídas desta sessão)
### 3.1 Ambiente (Fase 0)
- `env_c311`: py3.8.20 x86_64 · GPy 1.9.9 · numpy 1.20.2 · sklearn 1.1.2 · pyarrow 17 · pymoo
  0.6.1.2 (instalado, núcleo intacto). Provas GP+⑦+load_sonda+load_dataset(x_hash E f_hash): OK.
- Suíte env-main: `Ran 295 · OK (skipped=7)`. `preflight.py`: **VERDE** (lacres b5 aplicados;
  meu vendored `e3b3f802dad9` intacto — A.7 satisfeito).

### 3.2 Pilotos oficiais (deterministicos) + gates objetivos
```
MMF1  | run: ok, 1204 ger, ②=0, sonda=2, 46 finais/10 ND | auditar: VERDE | final_eval --check: VERDE
DTLZ2 | run: ok, 1204 ger, ②=0, sonda=2, 84 finais/77 ND | auditar: VERDE | final_eval --check: VERDE
ZDT1  | run: ok, 1204 ger, ②=0, sonda=2, 50 finais/50 ND | auditar: VERDE | final_eval --check: VERDE
```
(`auditar.py c311 <p> 0 --exp off --regime offline` · `final_eval.py --exp off --alg c311
--problema <p> --semente 0 --check`, no env-main.)

### 3.3 Determinismo (2 runs ⇒ ⑦ bit-a-bit) — ✅
- Teste `TestRunCompleto.test_determinismo_bit_a_bit` (C311_SLOW, env_c311): **ok**.
- Prova LIVE extra: re-run MMF1 num tempdir ⇒ ⑦ == ⑦ do piloto em `data/`: **True**.

### 3.4 Não-perturbação §3.1 (molde c122) — ✅
- Teste `test_sonda_NAO_perturba_a_busca` (sonda off vs on ⇒ ⑦ **e** ③-busca IDÊNTICAS,
  comparação NaN-aware pois a ③ tem σ=NaN nas folhas só-árvore): **ok**. A sonda roda FORA da
  busca, sob `preserve_all_rng`; a seleção "mean" ignora σ ⇒ invariante por construção.

### 3.5 Suíte de testes do cartão
- env_c311 (`C311_SLOW=1`): `Ran 14 · OK (skipped=1)` (o skip = folha-só-árvore no modelo
  minúsculo, coberta no run completo — a ③-busca dos pilotos tem centenas de σ=NaN).
- env-main: `Ran 14 · OK (skipped=10)` (ganchos+SLOW pulam; puros passam) — **a suíte env-main
  segue verde com o c311 adicionado**.

## 4. Fidelidade (D97) — NÃO me auto-aprovo
O runner INSTRUMENTA e aplica o gate OBJETIVO (FE=dataset, 7 camadas, CP-init, guardas, ganchos
restaurados, determinismo, não-perturbação). O julgamento de FIDELIDADE do mecanismo (o treed-GP
reproduz o paper/código do autor) é **MANUAL, do autor, a posteriori** — com destaque para o §2.2
(o gancho lhs muda a init-pop vs um pyDOE antigo) e o σ (extensão nossa, B15.5, que o paper
anuncia e nunca consome).

## 5. Ritual da Fase A (cumprido)
NUNCA `git push` · NUNCA `git add -A` · staged-check SÓ com arquivos meus · nada em
`_baseline_pre_retrofit/**` · pins do autor respeitados (exceção pymoo pré-autorizada; o pyDOE é
§2.2) · ambiguidade ⇒ sinalizada (§2), não auto-resolvida em fidelidade.
