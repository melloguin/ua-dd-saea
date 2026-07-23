# R3-b5 — RELATÓRIO DE EXECUÇÃO

> Narrativa da implementação e a validação **re-executada AO VIVO**. Complementa
> `R3-b5.md` (o quê) e `R3-b5_REPASSE-A-TORRE.md` (o que a torre decide).

## 1. Ambiente de execução
- `env_b5` = py3.7.12 x86_64/Rosetta. Runs OFFLINE, 1 core, thread-pins D79,
  `MPLBACKEND=Agg`, **`PYTHONHASHSEED=0`** (o `run_in_venv` o seta — DETERMINISMO).
- Datasets D90 + sonda de 20.000 lidos do repo; escrita em `data/experiments/off/{b5r,b5m}/`.

## 2. Percurso — o env "validado" não rodava o desdeo
O proof do R3-00 (DI-22) só exercitou `import + load_sonda`. Ao rodar b5 de fato,
apareceram (e foram fechados) — cada um sinalizado no REPASSE p/ veto:
1. `pymoo` ausente → instalado 0.6.1.2 + shim py3.7 `typing.Literal`.
2. `plotly`/`graphviz` ausentes (import-time desdeo_emo) → instalados (= env_c311).
3. `pygmo` force-import (NSGAIII/PPGA, nunca usados por b5) → STUB no runner.
4. `doe.py:219` `ChunkedArray.to_numpy(zero_copy_only=)` estoura no pyarrow 12 →
   shim LOCAL no runner (`combine_chunks()`, bit-idêntico); bug de torre p/ fix central.
5. `pandas==0.25.3` quebra `DataProblem` → subido p/ 1.3.5 (autor cravou; harness=pyarrow).
6. `DataProblem.evaluate` usa `use_surrogate` (singular), não `use_surrogates`.
7. **DETERMINISMO**: `pyDOE 0.9.1` mudou a API — `lhs(n,samples)` SEM semente usa
   `np.random.default_rng()` FRESCO (ignora `np.random.seed`), tornando a pop inicial do
   motor NÃO-reprodutível. Fix runner-local: injeta o `RandomState` GLOBAL semeado no
   `lhs` do `create_new_individuals` (replica o pyDOE clássico → determinístico e fiel).

## 3. Gates de aceite — VALIDAÇÃO AO VIVO

### 3.0 Determinismo (gate 5) — **VERDE**
2 runs b5r/MMF1/0, mesma semente, `PYTHONHASHSEED=0` + fix pyDOE:
`n_geracoes=950, n_final=44, n_nd=11` IDÊNTICOS; ③-busca bit-a-bit (39549=39549) e
⑦ (X,F float32) bit-a-bit (44=44). **VERDE** (antes do fix: divergia já na geração 1 —
a pop LHS inicial).

### 3.1 accept.py / auditar.py / final_eval.py — matriz 6 configs
Todos: OFFLINE, semente 0, `PYTHONHASHSEED=0`, FE_final=31D−1, `cp_init_ok=True`.

| config | FE | n_ger | n_final | accept | auditar | final_eval | wall |
|---|---|---|---|---|---|---|---|
| b5r/MMF1  | 61  | 950 | 44  | VERDE | VERDE | VERDE | 354s |
| b5r/DTLZ2 | 371 | 684 | 61  | VERDE | VERDE | VERDE | 446s |
| b5r/ZDT1  | 929 | 859 | 48  | VERDE | VERDE | VERDE | 284s |
| b5m/MMF1  | 61  | 801 | 50  | VERDE | VERDE | VERDE | 2868s |
| b5m/DTLZ2 | 371 | 381 | 105 | VERDE | VERDE | VERDE | 3220s |
| b5m/ZDT1  | 929 | 801 | 50  | VERDE | VERDE | VERDE (re-run pós-fix nd_pos_real float32) | 2804s |

b5m é ~8× mais lento que b5r (a MC pareada do `compute_probability_wrong_MC` por seleção).
O único VERMELHO na 1ª passada foi b5m/ZDT1 no `final_eval --check` (`nd_pos_real` 20 vs 19:
eu passava o filtro ND no float64; o correto é OMITIR e deixar o `write_final` filtrar no
float32 — os outros 5 não tinham empate, ⑦ idêntica). Fix aplicado, b5m/ZDT1 re-rodado.

### 3.2 Não-perturbação (gate 4) — **VERDE**
b5r/MMF1 sonda-ON (entregável) vs sonda-OFF, `PYTHONHASHSEED=0`, mesma semente:
③-busca bit-a-bit (39549=39549) e ⑦ (X,F float32) bit-a-bit (44=44). A sonda roda FORA do
laço, sob `preserve_all_rng` — não move o RNG da busca.

### 3.3 Suíte + preflight — re-executados no fechamento
- **Suíte:** `Ran 309 tests — OK (skipped=17)`, exit 0. (Baseline do início: 295 OK; os +14
  são `tests/test_c311.py` da sessão concorrente — o meu único fail, `test_r3_harness`, foi
  corrigido: usava `b5r` como cobaia 'não-registrada' e eu registrei o dispatch b5r/b5m ⇒
  troquei a cobaia p/ `moead_media`.)
- **preflight:** anchors `b5-mode72-kde` e `b5-mode7-archive` = **APLICADO**; sem placeholders
  remanescentes (pin desdeo-emo cravado); `b5_desdeo` re-lacrado (5e17…→3bf1…, SÓ ele). exit 0.

## 4. Amostra de saída conformante (b5r/MMF1/0, run determinístico)
- ① `__real`: 61 linhas (=31·2−1), bit-a-bit ao dataset, fase `init`, CP-init x+f OK.
- ② `__pop`: **0 linhas** (VAZIA por construção — DI-16.17).
- ③ `__surrogate`: sonda 20.000 (geracao NULL, fe_treino_max=60) + busca (geracao 1..950,
  espaco_modelo=cru, real_solution_id NULL, μ_0/1 + σ_0/1).
- ④ `__timing`: **1 linha** (tempo_fit_s + tempo_busca_s; tempo_geracao_s EXCLUI a sonda).
- ⑤ manifesto: timing §17.6 + sigma_dict (DEF-C4) + sonda + regime=offline + status=ok.
- ⑥ `.jsonl`: header + 1 evento sonda + `b5_gen` por geração (DI-10, exceções offline NULL).
- ⑦ `__final`: os finais avaliados 1× na verdade (`problems.py`), ND filtrado pós-real,
  reconstituível da ③ (última geração) — DI-16.16/DI-08.

## 5. Notas por-modo
- mode 7 (b5r): `Prob_APD_select_v3` = APD probabilístico por aproximação MÉDIA-MC (DECLARADA).
- mode 72 (b5m): `ProbMOEAD_select` = MC pareada (`compute_probability_wrong_MC`) — quase-fiel;
  KDE morto + `plt_density` crashy removidos (nenhum `./Plots/` gerado — patch confirmado).
