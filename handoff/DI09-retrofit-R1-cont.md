# DI09-retrofit-R1-cont — retrofit DI-09/DI-10 nos 11 configs MATLAB (COMPLETO)

> **Cartão:** continuação do `DI09-retrofit-R1`. Instrumentação **read-only** (sonda canônica
> DI-09 + enriquecimento DI-10 do `.jsonl`) nos 11 configs MATLAB que faltavam.
> **Estado: ✅ COMPLETO — 11/11 configs entregues, validados e commitados.**
> **Teste de aceitação do cartão: ATINGIDO** (11 configs com sonda + DI-10 + ④/manifesto ·
> 11+ provas de não-perturbação · gates verdes · regressão total verde).
> **Ambiente (D81):** MATLAB R2025a U1 · ponte → 6 ✓ · venv `mestrado_experimentos_dissertacao`.
> **Datas:** 2026-07-19 → 2026-07-21. **Decisões do autor: DI-19.1…19.8** (REGISTRO PARTE A8 —
> renumeradas pela torre de DI-17.x; auditoria da torre por cima: DI-20, PARTE A9).

---

## 0. Placar final

| # | config | problemas | ① bit-a-bit | auditoria | accept | commit |
|---|---|---|---|---|---|---|
| 1 | b1 (ParEGO) | 3/3 | ✅ | ✅ | ✅ | `f1ef8b8` |
| 2 | b4 (CSEA) | 3/3 | ✅ | ✅ | ✅ | `76fbbd7`/`7652ad4` |
| 3 | b3 (K-RVEA) | 3/3 | ✅ | ✅ | ✅ | `f7c5c24` |
| 4–7 | 4 pisos ONLINE | 12/12 | ✅ | ✅ | ✅ | `145fd3d` |
| 8 | c238 (EIM) | 2/2 (ZDT1 fora: 3h55) | ✅ | ✅ | ✅ | `941901f` |
| 9 | e7 (EDN-ARMOEA) | 2/2 (ZDT1 fora: 72min) | ✅ | ✅ | ✅ | `29d4c74` |
| 10 | e74 (CLMEA) | 3/3 | ✅ | ✅ | ✅ | `1a64bd0` |
| 11 | e103 (IBEA-MS, OFFLINE) | 3/3 | ✅ | ✅ | ✅ | `fd4a9c1` |
| — | infra transversal + stub 8/8 flags | — | — | — | — | `7652ad4`/`76fbbd7` |
| — | DI-19.8 completa + c217 `sigma_dict` (DI-20.6 #1/#2) | 6 re-runs | ✅ | — | — | `7b6ac6e` |

**Regressão total de encerramento (2026-07-21): VERDE.** 14 runs MATLAB ×MMF1 (stub + 13
configs) re-executados · F0×4 exit 0 · 13× accept + 13× não-perturbação verdes · preflight
exit 0 · suíte **228 unittest OK** (`python -m unittest discover -s tests` — a suíte é
unittest; a ressalva "pytest ausente" da versão anterior deste handoff era um falso bloqueio).

**Total de provas de não-perturbação bit-a-bit na sessão: 40+** (cada run validado contra
`_baseline_pre_retrofit` ao ser produzido, + re-validações após cada mudança transversal, +
a bateria final). **Falhas: 0.**

---

## 1. O que cada config ganhou (resumo por config — detalhe nos commits)

- **b1** — sonda do ESCALAR Tchebycheff com o λ da iteração (D47 mono-output) + C3{λ,min/max,
  Gbest reconstruído read-only}; chunking 250 no predictor; ftm sobre o PDec pós-cap/dedup
  (NÃO-monotônico, regra 9 R4), calculado no hook e propagado.
- **b4** — sonda de CLASSE (bom/ruim + L) vs as K refs radiais; ftm sobre TrainIn (subamostra
  3/4 estratificada); fix `n_acumulado` |Arc|→|TrainIn| (**pendente ratificação R-1, em bloco
  com o do c217**); instrument movido para depois do RefSelect (wall TOTAL da geração).
- **b3** — sonda μ+σ dos M DACEs com `pred_h=@predictor` resolvido no escopo da KRVEA (30
  cópias na árvore); patch aditivo `apd_sel` (+1 output em KrigingSelect — DI-12.1); sigma_sel
  em DUAS formas nomeadas (critério meanMSE + sqrt por objetivo); f_best/n_front1 do **A2**.
- **pisos** — assert estreitado à ③ [DI-13.7]; ④ com `tempo_fit_s`/`busca`/`sonda` **NULL**
  (não 0.0) e `tempo_geracao_s` real via delta do outputFcn (containers.Map, sem persistent);
  DI-10 (n_front1, f_best/ideal, nadir_pop + nadir_front1); vetores de decomposição
  moead/nsga3 no header; `man.sonda.status='nao_se_aplica'`.
- **c238** — sonda em espaço **CRU** [DI-19.6] (mu·yrange+ymin — régua constante entre
  gerações); `finalProbe` com `g_armado` [DI-19.5 — o c238 é o overshoot-zero que motivou a
  decisão]; `eim_mediana_pool` (mediana de −ga_fit).
- **e7** — o teste de fogo do I1: MC-dropout ~1,4e7 draws/bloco, ① idêntica com 8 e 42 blocos.
  SEM chunking (semântica: dropout sorteia rand(|lote|,·)). `loss_treino` INACESSÍVEL
  [DI-12.1, barrado]; hp efetivos REAIS (8000/1e-5 hardcoded no stock, medido).
  `tempo_busca_s` ligado (era NaN da R1; CONTRATO §4 o tornou obrigatório; a busca é separável
  PopDec→IndividualSelect); `n_clusters_efetivo` = |PopNew| (sem patch — 1 linha por cluster
  não-vazio do kmeans); cluster por infill = posicional (labels do kmeans são arbitrários).
- **e74** — [DI-19.1] **um SondaState POR CABEÇA** (boot/s1/s2/s3) com calibração D-11
  **round-robin k s1=6/s2=3/s3=12**: cada ciclo sonda exatamente UMA cabeça, cada cabeça a
  cada 3 ciclos, boot em g=1. VERIFICADO no ZDT1: 71/71/71 blocos, gerações 6,18,30 / 3,15,27
  / 12,24,36 + boot. `man.sonda` por cabeça; finalProbe em cada handle. `n_por_nivel`
  (histograma 1..4 do cand_classe) + `k_local_efetivo` (o parâmetro real = 20; a 1ª tentativa
  gravava |x_train| da RBF-local — outra grandeza, corrigido ANTES de commitar dado).
- **e103** — sonda OFFLINE [DI-13.5]: 2 blocos × 20.000 (Kriging c/ σ; RBFN sem σ),
  **geração NULL** nos 40.000 E inteira na busca no MESMO parquet (o teste do adendo da torre,
  provado no dado real); `margem_3sigma_stats` [DI-13.4/B30] com réplica literal do JudgeModel
  — **verificável contra a decisão** (`n_pares_ok==total ⇔ kflag`; conferido: ZDT1
  1058841/1058841, kflag=1); `divergencia_modelos`; `n_geracoes` = ③ filtrada [DI-19.3];
  `f_best_dataset` 1× [DI-19.7]; timing completo; **re-lacre do repos.lock** (`preflight
  --write`, e103_ibeams `e5f8c26e`).

## 2. Infra transversal (commits `7652ad4`/`76fbbd7`)

1. **`geracao` NULLABLE na ③** (adendo da torre): idioma do `n_acumulado` da ④ — double+NaN
   se houver ausente, int32 se completa; `RunBuffer` trata NaN como "geração nula" (um `[]`
   descartaria o bloco em silêncio). **Bit-neutro provado** nos online.
2. **`finalProbe`/`g_armado`** [DI-19.5] + **`probeOffline`** + **S por regime** no construtor.
3. **Docstring-armadilha do SondaState corrigido** (dizia `(sd,buf,bud,fid,alg)` — quem
   copiasse matava o jsonl em silêncio).
4. **stub +3 regressões**: DI-19.5 nos dois ramos, bloco offline 20k com conferência dos DOIS
   lados da coluna `geracao` pós-export, `final_carimbou_armado`.

## 3. Incidentes e como foram tratados (honestidade de processo)

- **3 configs reprovaram na 1ª auditoria** (c238: `eim_mediana_pool` faltando; e7:
  `tempo_busca_s` NaN + `n_clusters_efetivo`; e74: `n_por_nivel`/`k_local_efetivo`) — em TODOS
  os casos o instrument foi corrigido e o run **re-executado do zero** (nunca remendado; o
  MATLAB pode recarregar função editada no meio do run e o jsonl sairia inconsistente).
- **e74 `k_local_efetivo`**: a 1ª implementação gravava a grandeza ERRADA (|x_train| da RBF
  local ≠ k_local); pego por conferência de valor (100 ≠ min(20,|Arc|)), corrigido e re-rodado.
- **e103: o validador estava errado 2×, não o dado** — exigia `tempo_geracao_s`>0 (T-8 em
  aberto: ④ do e103 é 1 linha agregada por design) e `n_geracoes`==② (DI-19.3 manda ③
  filtrada). Corrigido o validador COM verificação de que o online não regrediu.
- **Numeração DI**: a torre ocupou DI-15/16/17 em sessões concorrentes; as decisões desta
  sessão são **DI-19.x** (regra nova da torre: reservar o número no REGISTRO antes de citar).

## 4. Decisões do autor desta sessão — DI-19.1…19.8 (REGISTRO PARTE A8)

Ver tabela completa no REGISTRO. Uma correção factual ao registro: a DI-19.8 está lá anotada
como "APLICAÇÃO INCOMPLETA (1.050.000 linhas 'nativo')" — **isso foi FECHADO nesta sessão**
(commit `7b6ac6e`): c141/c217 DTLZ2+ZDT1 re-rodados, **0 'nativo' restante** nos 6 runs,
verificado no parquet.

## 5. Definições EM ABERTO (para a torre levantar com o autor)

> A torre já consolidou 21 decisões vivas em `handoff/DI20-AUDITORIA-RETROFIT_DECISOES.md`
> (DI-20.7). Abaixo, o que esta sessão ADICIONA ou ATUALIZA naquele conjunto:

- **R-1 (= D-04 do DI-20) · Ratificação em bloco do `n_acumulado`** — c217 E b4 (os dois
  subamostradores; ambos mudam a ④ vs baseline). *Só o autor (D97).*
- **D-11 (DI-20) · e74 calibração da cadência** — implementada como round-robin k=6/3/12
  (§1). Dado real produzido; ratificação em lote.
- **T-8 · e103 ④ por geração** — segue 1 linha agregada; `tempo_geracao_s` NULL. Mudar = patch
  no laço do IBEAMS + ④ 1→99 linhas + novo re-lacre. *Autor.*
- **T-2 · Regra 2 do R4 não cobre a coluna `geracao`** — Python grava int32-nullable, MATLAB
  double+NaN. Leitor com `astype(int32)` quebra no e103. *Doc-sync torre.*
- **B34 (menor) · `manifestBlock` sem campo `regime`** — S=20000 desambigua; não mexi no
  SondaState com runs em curso. *1 linha, qualquer sessão futura.*
- **Validadores da sessão** (`naoperturbacao.py`/`auditar.py`) — 2ª sessão seguida
  reconstruídos no scratchpad (receita §4.5 os manda não-versionar; faixa `.py` vedada).
  **Recomendação forte: a torre os promova a `scripts/` permanentes** — o accept.py continua
  sem NENHUMA checagem de sonda (DI-20 D-?/item herdado) e estes dois já cobrem ordem do
  artefato, contagens, NULL dos dois lados, timing e DI-10.
- **e103 camada ⑦** segue AUSENTE (DI-20.4: "o endpoint oficial do offline não existe") —
  pós-hoc Python, faixa da torre/R3, `scripts/final_eval.py` já existe.

## 6. Walls medidos (para o M7)

| config | MMF1 | DTLZ2 | ZDT1 | sonda custou |
|---|---|---|---|---|
| b1 | 19s | 167s | 2022s | ~+18% no ZDT1 (303 blocos) |
| b4 | 39s | 198s | 885s | ~+21% |
| b3 | 8s | 41s | 539s | ~neutra |
| pisos | 0,3–3s | — | — | n/a |
| c238 | 9s | 611s | (fora) | ~neutra |
| e7 | 322s | 1819s | (fora) | +7,6% no DTLZ2 |
| e74 | 22s | 259s | 471s | ~neutra (round-robin) |
| e103 | 9s | 11s | 36s | ~+4s no MMF1 (2×20k) |

## 7. Receita consolidada (para futuros retrofits)

A receita §4 do handoff anterior + o que esta sessão acrescentou: (a) SEMPRE re-executar o run
inteiro após corrigir instrument (nunca confiar em reload parcial do MATLAB); (b) validar a
GRANDEZA, não só a presença do campo (o k_local_efetivo=100 passava no teste de presença);
(c) o validador também erra — na dúvida, conferir contra o handoff/decisão ANTES de "corrigir"
o dado; (d) `containers.Map` como relógio inter-hook quando o stock não pode receber tic;
(e) tabela de aritmética modular ANTES de escolher k por cabeça (due é `mod(g,k)==0`).
