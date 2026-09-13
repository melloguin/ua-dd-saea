# R3-b5 — RELATÓRIO COMPLETO DE EXECUÇÃO (para a torre central)

> Narrativa passo-a-passo de TUDO que a sessão de implementação do cartão R3-b5
> executou, com os comandos rodados e os resultados. Objetivo: a instância que
> gerou as instruções (a torre) entender exatamente o que foi feito, como, e com
> que resultado — **e levantar com o autor as DEFINIÇÕES EM ABERTO da §9.**
>
> Complementa (não substitui) os 3 handoffs curtos: `R3-b5.md` (o quê),
> `R3-b5_RELATORIO-EXECUCAO.md` (matriz de gates) e `R3-b5_REPASSE-A-TORRE.md`
> (decisões p/ o autor). Commit do cartão: **`[R3-b5]` e3ecab1**.

## 0. Veredito em uma linha
**Objetivamente PRONTO e COMMITADO:** os 6 gates objetivos estão VERDES (encanamento,
D97), validados rodando código de verdade. **A validação de FIDELIDADE é manual do autor
(D97) — não entra aqui.** Restam **definições EM ABERTO (§9)** que a torre deve levantar
com o autor para ratificar (não bloqueiam os gates; são vetos/ratificações).

---

## 1. FASE 0 — Gate de ambiente
**O que fiz:** confirmei o env_b5, os artefatos D90, o repo vendorizado, e o baseline
(suíte + preflight).

**Código rodado e resultado:**
- `env_b5/bin/python -c "import platform,sys; ..."` → **py 3.7.12, machine x86_64** (Rosetta),
  64-bit. ✅
- versões: **sklearn 0.21.3, pandas 0.25.3, numpy 1.21.6, desdeo-problem 0.14.0,
  desdeo-tools 0.2.6, statsmodels 0.13.5, pyarrow 12.0.1, pyDOE 0.9.1, matplotlib 3.5.3**;
  `desdeo-emo` **AUSENTE no pip** (confirma o pin = vendorizado). ✅
- prova do harness offline: `import sklearn, desdeo_problem; from src.standalone_harness
  import load_sonda; load_sonda('MMF1', regime='offline')` → **PASS**. ✅
- artefatos: `ds_{MMF1,DTLZ2,ZDT1}_0.parquet` presentes, **61/371/929 linhas = 31D−1**,
  colunas `x0..x{D-1}, f0..f{M-1}`; 21 sondas em `data/sonda/`. ✅
- **suíte baseline:** `python -m unittest discover -s tests` → **Ran 295 tests — OK (skipped=7)**. ✅
- **preflight baseline:** `python scripts/preflight.py` → **exit 0** (1 deferimento intencional:
  o placeholder do pin desdeo-emo). ✅

## 2. Leitura obrigatória
Fan-out de 8 leitores + 1 crítico de completude (workflow) sobre: CONTRATO_DE_DADOS,
03_contrato_export, 00_contrato_rodada3, o cartão `alg_b5_prob.md`, SPEC §3.2·b5, os
handoffs R3-c122/R3-e81/R3-00, e o REGISTRO DI-21..24 + DI-16.x. **Verifiquei cada API
contra o código** antes de usar (run_stubr3, surrogate_row, write_final, emit_sonda_block,
load_offline_budget, seeds.json). Produziu o checklist de 14 passos que guiou a implementação.

## 3. Decisões cravadas COM o autor (o autor delegou "o que você achar mais recomendado")
1. **Pin desdeo-emo (gate R3.2):** VENDORED root-first, **SEM pacote pip**.
2. **Sonda geracao=NULL:** carimbo pós-hoc em `buf.surr_rows[-S:]` (precedente c149).
3. **2 patches vendorizados** aplicados como apresentados.
4. **pandas 0.25.3 → 1.3.5** (ver §5).

## 4. Implementação — `src/b5_prob.py`
Molde offline (`run_stubr3` do harness + e103). Fluxo: seeds D62 (`iteration_seed`, alg_id
b5r=17/b5m=18) → import vendorizado root-first (+ stub pygmo) → `load_offline_budget` (①=
dataset) + `load_sonda` → `DataProblem` (bounds reais) → `problem.train(SurrogateKriging)`
(treino único, cronometrado) → sonda 1 bloco 20k (geracao=NULL pós-hoc) → evolver
`{7:ProbRVEA_v3, 72:ProbMOEAD}` `use_surrogates=True, n_gen_per_iter=10, FE=40000` →
`while continue_evolution(): iterate()` → replay dos arquivos por geração p/ a ③ → ⑦ `__final`
(avaliada 1× na verdade via `problems.py`, ND pós-real) → `write_run_outputs`. Detalhe
completo em `R3-b5.md §4`.

## 5. Completamento do env_b5 (o env "validado" NÃO rodava o desdeo)
O proof do R3-00 (DI-22) só exercitou `import + load_sonda`. Ao rodar b5 de verdade,
apareceram 7 lacunas — **cada fix testado; todas sinalizadas p/ veto (§9):**

| # | Problema | Como descobri | Fix |
|---|---|---|---|
| 1 | `pymoo` ausente (finais ⑦/ND via `problems.py`) | 1º run: `ModuleNotFoundError` | instalei pymoo 0.6.1.2 + shim py3.7 `typing.Literal` |
| 2 | `plotly`/`graphviz` ausentes (import-time do desdeo_emo) | run: `No module named 'plotly'` | instalei plotly 4.14.3 + graphviz (= env_c311) |
| 3 | `pygmo` force-import (NSGAIII/PPGA, nunca usados) | rastreei os `__init__.py` do desdeo_emo | STUB em `sys.modules` no runner |
| 4 | `doe.py:219` `ChunkedArray.to_numpy(zero_copy_only=)` estoura no pyarrow 12 | run: `TypeError: to_numpy() takes no keyword arguments` | **shim LOCAL** no runner (`combine_chunks()`, bit-idêntico); NÃO editei o `doe.py` compartilhado (sessão c311) |
| 5 | `pandas 0.25.3` quebra `DataProblem` (`pd.DataFrame(columns=,index=[0])`) | run: `AttributeError: 'object' has no attribute 'dtype'`; reproduzi isolado | **pandas → 1.3.5** (autor cravou; desdeo não pina pandas; harness=pyarrow ⇒ saída inalterada) |
| 6 | `DataProblem.evaluate` usa `use_surrogate` (singular) | run: `unexpected keyword 'use_surrogates'` | corrigido no `_predict` |
| 7 | 🔴 `pyDOE 0.9.1` `lhs(n,samples)` sem seed usa `default_rng()` FRESCO → ignora `np.random.seed` → pop inicial NÃO-determinística | **o gate de determinismo REPROVOU**; isolei a divergência na geração 1 (a LHS) e reproduzi `pyDOE.lhs(2,50)` variando entre processos | fix runner-local: injeta o `RandomState` global SEMEADO no `lhs` do `create_new_individuals` (replica o pyDOE clássico) + `PYTHONHASHSEED=0` |

**Os itens 4 e 7 corroboram exatamente o que a sessão c311 já tinha sinalizado para o b5.**

Atualizei `requirements/env_b5.txt`, `locks/env_b5.lock.txt`, `PROVISIONAMENTO.md §2`,
`envs.json`. **Constraints protegeram o núcleo validado** (numpy/scipy/sklearn/pyarrow
INALTERADOS em todas as instalações).

## 6. Patches vendorizados (ancorados; `preflight` = APLICADO)
- **b5m** — `ProbMOEAD_select.py:66-75` comentado (bloco KDE morto + `plt_density` crashy,
  que salvava PDF por vizinho sob `usetex` e `reshape(20,…)`). A decisão (linha 79) usa
  `compute_probability_wrong_MC`. Âncora `b5-mode72-kde`. **Prova:** nenhum `./Plots/` gerado
  em nenhum dos runs.
- **b5r** — `BaseEA._next_gen` (pós `keep()`): re-carimba o arquivo da geração com os
  SOBREVIVENTES pós-seleção (DI-16.16). Sem ele a ⑦ do mode 7 nasce irreconstituível da ③.
  Âncora NOVA `b5-mode7-archive`. **Prova:** `final_eval --check` VERDE ("X reconstituível
  da ③ ger G via origem_linha").

## 7. VALIDAÇÃO — código rodado e resultados (a resposta à sua pergunta 1)
Tudo com `PYTHONHASHSEED=0`, semente 0, thread-pins D79.

### 7.1 Determinismo (gate 5) — **VERDE**
2× `b5r/MMF1/0` (mesma semente) → resultados **idênticos** (`n_geracoes=950, n_final=44,
n_nd_pos_real=11`). Comparador bit-a-bit: **③-busca idêntica (39549=39549) · ⑦ (X,F float32)
idêntica (44=44)**. (Antes do fix pyDOE: divergia já na geração 1.)

### 7.2 Não-perturbação (gate 4) — **VERDE**
`b5r/MMF1` sonda-ON (entregável) vs sonda-OFF, mesma semente → **③-busca idêntica
(39549=39549) · ⑦ idêntica (44=44)** (a sonda roda FORA do laço, sob `preserve_all_rng`).

### 7.3 Matriz 6 configs — todos rodaram ponta-a-ponta, `cp_init_ok=True`, FE=31D−1
| config | FE | n_ger | n_final | n_nd | wall |
|---|---|---|---|---|---|
| b5r/MMF1  | 61  | 950 | 44  | 11 | 354s |
| b5r/DTLZ2 | 371 | 684 | 61  | 25 | 446s |
| b5r/ZDT1  | 929 | 859 | 48  | 8  | 284s |
| b5m/MMF1  | 61  | 801 | 50  | 21 | 2868s |
| b5m/DTLZ2 | 371 | 381 | 105 | 6  | 3220s |
| b5m/ZDT1  | 929 | 801 | 50  | 19 | 2390s |

(b5m ~8× mais lento que b5r: a MC pareada `compute_probability_wrong_MC` por seleção.)

### 7.4 Gates accept.py / auditar.py / final_eval.py — **6/6 VERDE**
Para cada um dos 6: `accept.py R3-b5{r,m} --exp off --alg b5{r,m} --problema P --semente 0`
= VERDE; `auditar.py b5{r,m} P 0 --exp off --regime offline` = VERDE; `final_eval.py
--exp off --alg b5{r,m} --problema P --semente 0 --check` = VERDE. O `check_r3_b5` afere:
①=dataset bit-a-bit + CP-init (x_hash E f_hash), ② vazia aceitável (DI-16.17), ③ sonda 20k
geracao NULL + busca (fe_treino_max=n_ds−1, real_solution_id NULL, espaco_modelo=cru, μ/σ),
④ 1 linha, ⑤ manifesto (timing+sigma_dict+sonda+regime+status), ⑦ reconstituível.

### 7.5 Estrutura das saídas (amostra b5r/MMF1) — inspeção direta
① 61 linhas (=dataset, fase `init`) · ② **0 linhas** (vazia por construção) · ③ 59547 =
20000 sonda (**geracao ALL-NULL**) + 39547 busca (geracao 1..950, espaco=cru, fe_treino_max=60,
real_solution_id=NULL) · ④ **1 linha** (tempo_fit + tempo_busca; tempo_geracao EXCLUI a sonda)
· ⑦ 40 finais, 13 ND.

### 7.6 Suíte + preflight (fechamento)
- **Suíte:** `Ran 309 tests — OK (skipped=17)` (baseline 295 + 14 do `test_c311.py` da
  sessão concorrente; corrigi o único fail — `test_r3_harness` usava `b5r` como cobaia
  'não-registrada' e eu registrei o dispatch b5r/b5m ⇒ troquei a cobaia p/ `moead_media`).
- **preflight:** exit 0; âncoras `b5-mode72-kde` e `b5-mode7-archive` = **APLICADO**; sem
  placeholders remanescentes; `b5_desdeo` re-lacrado (5e17…→3bf1…, **SÓ ele**).

### 7.7 Um bug MEU que os gates pegaram (e corrigi)
`final_eval --check` reprovou **b5m/ZDT1** (`nd_pos_real` 20 vs 19): eu passava o filtro ND
no float64 ao `write_final`; a docstring dele manda OMITIR (calcula no float32 que a ⑦
persiste). Empates próximos divergem entre float32/float64. **Fix: omitir `nd_pos_real`.**
Os outros 5 runs não tinham empate (⑦ idêntica); re-rodei só o b5m/ZDT1 → VERDE.

## 8. Commit e higiene
Commit **`[R3-b5]` e3ecab1** — 15 arquivos (11 modificados + 4 novos), **SÓ os meus**
(git status limpo de c311). **NUNCA `git push`, NUNCA `git add -A`.** `repos.lock` re-lacrado
só no b5_desdeo. Working tree limpo no fechamento.

---

## 9. ⚠ DEFINIÇÕES EM ABERTO — a torre DEVE levantar com o autor (pergunta 3)
Nenhuma bloqueia os gates; são **ratificações/vetos** que a torre precisa trazer ao autor:

1. **Pins do env_b5 (D80 — pins são do autor):** ratificar pymoo 0.6.1.2, plotly 4.14.3,
   graphviz, e **pandas 0.25.3 → 1.3.5** (o autor já cravou este; ratificar formalmente no
   lock/PROVISIONAMENTO). Decidir se o **pygmo** fica STUB (b5-only) ou é instalado.
2. **BUG DE TORRE — `doe.py:219`:** `ChunkedArray.to_numpy(zero_copy_only=)` é inválido no
   pyarrow 12; usei shim LOCAL. **Fix central** serve b5 + c311 + moead_media (e o
   `tree_sha256` idealmente deveria excluir `__pycache__`, senão o repos.lock "envelhece").
3. **🔴 pyDOE / determinismo (fidelidade da pop inicial — D97):** ratificar que a LHS via
   `RandomState` global semeado (réplica do pyDOE clássico) é a semântica desejada, e
   **propagar o fix p/ c311/moead_media** (mesmo `create_new_individuals`). Confirmar que
   b5 SEMPRE roda com `PYTHONHASHSEED=0` (o `run_in_venv` já seta).
4. **Semeadura — convenção vs. literal do cartão:** o cartão L.16 escrevia
   `np.random.seed(s)`; usei `iteration_seed(base, alg_id, 0, uso)` (D62/D91, alg_id
   b5r=17/b5m=18) — canônico e anti-descompasso. Ratificar.
5. **Mecanismo geracao=NULL da sonda offline:** carimbo pós-hoc em `buf.surr_rows[-S:]`
   (precedente c149). A torre pode preferir um fix central em `emit_sonda_block` (aceitar
   `geracao=None`) para c311/moead_media não repetirem o carimbo.
6. **④ = 1 linha (imposto pela caixa-preta):** `evolver.iterate()` roda 10 gerações internas
   sem gancho por geração ⇒ `tempo_busca_s` POR GERAÇÃO é inmensurável. Segui o cartão
   (1 linha). O ⑥ (jsonl) tem 1 evento `b5_gen`/geração com `tempo_busca_s=NULL` (exceção
   offline declarada). Ratificar a granularidade.
7. **Literais de naming (landam em artefato auditado):** `modelo_flag` =
   `"b5r/ProbRVEA-v3+GPR"` / `"b5m/ProbMOEAD-PBI+GPR"`; conteúdo do `sigma_dict` (DEF-C4).
   Se a torre/autor quiser outra convenção, trocar.
8. **repos.lock:** re-lacrei SÓ o b5_desdeo; e74/e81/c149 já estavam em drift no baseline
   (provável .pyc) e o c311_tgprmo é da sessão concorrente. **A torre deve re-lacrar o
   repos.lock inteiro de um checkout LIMPO** ao integrar.
9. **Dispatch/wiring compartilhado:** registrei b5r/b5m em `experiment.py` (o comentário
   pedia "descomente ao fechar o cartão"). Isso obrigou a ajustar `test_r3_harness` (cobaia
   b5r→moead_media). A torre deve saber que `experiment.py` e `test_r3_harness` são
   compartilhados com a sessão c311.

## 10. Notas POR-MODO (o coração da FIDELIDADE — para o AUTOR validar, D97)
- **mode 7 (b5r → `Prob_APD_select_v3`):** APD probabilístico por **aproximação MÉDIA-MC**
  ("superfast considering mean APD"). É uma **aproximação DECLARADA**, NÃO o Prob-APD
  publicado exato. O repo também traz `Prob_APD_select_v1` ("original", mais fiel e lento).
  **O autor deve decidir se `v3` é a variante do estudo.**
- **mode 72 (b5m → `ProbMOEAD_select`):** comparação **MC pareada**
  (`compute_probability_wrong_MC`, substitui vizinhos com P_wrong>0.5) — **quase-fiel** ao
  paper. O bloco KDE removido era MORTO (a decisão nunca usava o pdf).
