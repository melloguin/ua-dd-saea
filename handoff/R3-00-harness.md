# handoff/R3-00-harness.md — Rodada 3, cartão 00 (infra TRANSVERSAL standalone + camada ⑦)

**Data:** 2026-07-19 · **Env:** env-main NO MAC (D81/RI-08 — a VM só no M8) —
`/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python`;
python 3.11.9 · numpy 2.4.6 · pymoo 0.6.2 · pyarrow 25.0.0 · torch 2.11.0 (opcional).
**Gate:** `PY scripts/accept.py R3-00-harness --problema {MMF1,ZDT1,DTLZ2,MMF11_L}`
→ **VERDE, exit 0 nos 4** (21/21 checks). ✅
**Escopo:** PURA INFRAESTRUTURA TRANSVERSAL (contrato N.2/§22.4) + a camada
`__final.parquet` do regime offline (DI-08). **SEM algoritmo** (c122, b5r/b5m,
c311, c149, e81 e piso-off são os próximos cartões), **SEM fidelidade** (D97).
Prova por run-STUB **`stubr3`** — token distinto de propósito: `stub` é o STUB
MATLAB do R1-00 e `stubpy` o do R2-00; cada um tem a sua pasta.

## Paralelismo (faixas)

Sessão em PARALELO TRIPLO com retrofit-MATLAB e retrofit-BoTorch na MESMA
árvore. Toquei SÓ a minha faixa — **zero `.m`, zero `algorithms/**`, zero
`src/export.py`/`botorch_harness.py`/`c262`/`c154`, zero SPEC/bundles/artifacts,
zero `data/{doe,datasets,sonda}`**. `cards/INDEX.md` NÃO marcado (a torre marca).

**Um bloqueio de faixa foi levantado e resolvido durante a sessão:** ao desenhar
o harness, as 3 exigências v5.2.1 (③ `fe_treino_max`, ③ `regime` POR LINHA,
④ `tempo_pred_sonda_s`/`tempo_geracao_s`) eram **inalcançáveis** pelas APIs de
`src/export.py`, que é faixa do retrofit-BoTorch. Verifiquei adversarialmente
(4 lentes, 4/4 não refutaram, com reprodução empírica) e **parei para perguntar
(D81)**, como o cartão manda. O autor informou que o retrofit havia fechado;
confirmei no repo (11 commits `[DI09-R2]`, `export.py:163/181-182/270`) e segui.
**Nada de `export.py` foi tocado por mim.**

## Resultado (tudo verde)

- **Gate R3-00 — 21 checks × 4 problemas:** wiring `experiment.run`→dispatch
  lazy (stack `standalone`) · **FE = 31D−1 EXATO e = |dataset|** (MMF1 61 ·
  ZDT1 929 · DTLZ2 371 · MMF11_L 61) · ① = o dataset **bit-a-bit**, fase toda `init` ·
  **CP-init OFFLINE `x_hash` E `f_hash`** · violação de regime ⇒
  `OfflineBudgetViolation` · cache-hit = 0 FE com saldo esgotado (D89) ·
  4 saídas + jsonl · **schemas §17.2 EXATOS** (①②③+timing) + a ⑦ do DI-08 ·
  **③ v5.2.1: `regime` POR LINHA** (sonda 2000 × busca na MESMA tabela) e
  `fe_treino_max` sem nulos · **④ v5.2.1 COMPLETA** (busca/sonda/geração, 0
  nulos) · sonda na ORDEM do artefato + hash + ZERO FE · **⑦ consistente e
  RECONSTITUÍVEL da ③** · manifesto com bloco `timing` + `sigma_dict` +
  CP offline · atômico sem `.tmp` · pinning D79 · guarda de RNG N.2.3 ·
  **subprocess-por-venv resolvido E executado de verdade**.
- **Regressão Python:** suíte **193 OK (1 skip)** — era 122, **+71 testes
  novos** · accept F0-01/F0-02/F0-03/F0-04 **exit 0** · **R2-00 exit 0** (MMF1 e
  ZDT1) · `preflight.py` **exit 0**. **Gates R1/R2-c\* NÃO rodados** (faixas
  MATLAB/BoTorch ativas — instrução do cartão).
- **Revisão adversarial (5 lentes × verificação cética por achado — 31 agentes):**
  26 achados brutos → **7 CONFIRMADOS** (1 crítico, 3 major, 3 minor), todos
  **corrigidos e cobertos por regressão**; 19 refutados. Detalhe na §Revisão.
- **Auditoria pyarrow** das saídas do `stubr3` (`data/experiments/off/stubr3/`,
  gitignored): 5 camadas com schema exato, codec ZSTD, ③ com
  `{sonda: 2000, offline: 488|7432}`, ④ com as 3 colunas novas preenchidas,
  ⑦ com `nd_pos_real` conferido contra o filtro recomputado.

## Arquivos

**Novos:**
- **`src/standalone_harness.py`** (~1450 linhas) — a infra transversal R3, o
  irmão **torch-livre** do `botorch_harness`. Por que um módulo novo em vez de
  reusar aquele: `b5`/`c311`/`piso-off` rodam em venvs DESDEO **sem torch**, e
  `botorch_harness` faz `import torch` no topo — importá-lo lá quebra o
  processo. Peças:
  - **Pinning D79/N.1.1** — env vars no TOPO (antes de `import numpy`) +
    `pin_runtime()`, com o torch **opcional** (registra `torch: None` quando
    ausente, em vez de estourar).
  - **`run_in_venv()` — o subprocess-por-venv (D79/N.2).** O mecanismo que
    torna b5 × c311 seguros: os dois vendorizam `desdeo_emo`/`desdeo_problem`/
    `desdeo_tools` com o MESMO NOME e código DIFERENTE; `sys.modules` cacheia o
    primeiro e **co-importá-los usa DataProblem/RVEA errados SEM ERRO**. Um
    processo por run elimina a classe inteira. Usa `-I` (ignora `PYTHONPATH` e
    site-packages do usuário — senão o overlay de um venv sombreia o do outro),
    env limpo com o pin **aplicado no FILHO** (é lá que o `import` acontece), e
    o filho chama `src.experiment.run(...)` — o MESMO ponto de entrada do
    processo local, para não haver um 2º caminho de código a auditar. O
    resultado viaja entre sentinelas porque o stdout é território dos drivers
    dos autores.
  - **`load_dataset()` / `load_offline_budget()` / `offline_guard()`** — o molde
    OFFLINE do e103 em Python: o orçamento **É** o dataset (D90), a ① é o
    dataset, CP-init com `x_hash` **E** `f_hash` (mais forte que o online, que
    só cobre X — no offline o F é *insumo* do modelo, não resultado), e
    **FE na busca = VIOLAÇÃO**, não término (`OfflineBudgetViolation`, uma
    exceção própria que NÃO é subclasse de `BudgetExhausted`, justamente para
    ninguém a engolir como fim natural D61).
  - **Sonda §17.2.2** — `load_sonda` (gêmeo torch-livre, com teste de
    equivalência contra o do `botorch_harness`), `sonda_due`, `emit_sonda_block`
    com `predict` INJETADO pelo cartão, sob `preserve_all_rng()`.
  - **`minimo_comum_di10()`** — o mínimo comum do jsonl, já com a armadilha A-8
    tratada (`_nds_filter` devolve ÍNDICES; `len`, nunca `count_nonzero`).
  - **`SnapshotBuffer`** — mesma API do R2-00 de propósito, mas `tempo_fit_s`
    aceita `None` (o **piso** não treina surrogate — CONTRATO §4).
  - **`write_run_outputs()` / `dual_write_run()`** — 4 camadas via `src.export`
    (REUSO, nada duplicado) + manifesto com `timing`/`sigma_dict`/CP offline.
  - **`final_schema()` / `write_final()`** — a camada ⑦ (DI-08).
  - **`run_stubr3()`** — o STUB OFFLINE.
- **`scripts/final_eval.py`** (~360 linhas) — o avaliador PÓS-HOC do DI-08: lê a
  ③, pega a última geração da BUSCA (descartando as linhas de sonda), avalia 1×
  em `problems.py` (float64, FORA do orçamento) e grava a ⑦ + sidecar de
  procedência. Determinístico e idempotente. `--check` faz a verificação de
  presença+consistência que o gate offline usa. Serve os 5 configs offline pelo
  MESMO caminho — **é isso que tira a ponte MATLAB da equação** e faz o
  pareamento cross-stack do §9 valer por construção.
- `tests/test_r3_harness.py` (49 testes) + `tests/test_r3_final_eval.py` (22).

**Modificados (todos ADITIVOS):**
- `src/naming.py` — `FINAL_LAYER`/`OPTIONAL_LAYERS`/`ALL_LAYERS` + `final_path`/
  `final_filename`; `check_layer` passa a validar contra `ALL_LAYERS`.
  **`LAYERS` ficou INTOCADA de propósito** — é ela que `manifest.new_manifest`,
  `manifest.is_run_done`, `gcs.plan_targets` e `naming.output_filenames`
  iteram. Se `final` entrasse ali, **todo run ONLINE viraria "não pronto" para
  sempre e a esteira idempotente o re-executaria em loop**. Há teste para isso.
- `src/experiment.py` — 1 linha do `stubr3` no `_DISPATCH_LOADERS` + as 7 linhas
  dos configs R3 **comentadas** (cada cartão descomenta a sua) + o **roteamento
  obrigatório por venv** em `run()` (achado 2 da revisão): os algs de
  `VENV_ONLY_ALGS` vão para `run_in_venv` ANTES do despacho in-process, com
  `_in_child` cortando a recursão do bootstrap. `ALGORITHM_DISPATCH` segue
  VAZIO no import (o check do F0-01 segue verde).
- `scripts/accept.py` — branch **ADITIVO** `R3-00-harness` + `check_r3_00` e 5
  helpers. Zero branch existente tocado; D97 intacto. Reusa `check_fe`/
  `check_outputs`. ⚠ O branch foi inserido **ANTES** do catch-all
  `if a.cartao.startswith("F0-01") or not a.alg:` — sem isso o cartão (que não
  exige `--alg`) seria engolido e devolveria o VERDE do andaime F0-01.

## 🔴 O DEFEITO QUE A PROVA DESCOBRIU (leia antes de escrever um cartão offline)

**A ⑦ tem de ser RECONSTITUÍVEL da ③.** O meu STUB, na 1ª versão, escrevia a ⑦
a partir da **prole** da última geração — pontos que a ③ **nunca registrou**. As
duas camadas ficavam bem-formadas, o `f` era mesmo o verdadeiro daqueles `x`, e
o run passava em todo o resto. Só apareceu porque comparei a rota nativa com a
retroativa e os ND não bateram (13 × 15).

Por que é grave: para o **e103** (MATLAB, já executado) a ③ é a **única** fonte
da ⑦ — uma ⑦ irreconstituível faria o retroativo avaliar **outro conjunto**, em
silêncio. Agora é **check permanente** (`final_eval.check_final`, dentro do gate):
mesmo `n`, mesmo `X` (em float32) que a última geração de busca da ③.

**Para os cartões offline:** grave a ⑦ a partir da população que a ③ REGISTROU,
não da seguinte. Se o seu algoritmo devolve um `FinalDec` separado, **grave-o
também como uma geração da ③** antes de chamar `write_final`.

## Revisão adversarial — os 7 achados confirmados (todos corrigidos)

Rodei 5 lentes independentes sobre o diff e submeti CADA achado a um verificador
cético (o default era falso-positivo). 26 brutos → **7 reais**, 19 refutados.

1. **🔴 CRÍTICO — `evaluate_final` rejeitava a própria ⑦ em MMF11_L.** A
   tolerância de bounds era `1e-9` FIXO, ~100× **menor** que o quantum do
   float32 perto de 1.0 (~1,2e-7). Todo X que chega ali passou por uma camada
   float32 (D53), e clipar no bound é rotina de MOEA. `MMF11_L` (xl=0.1,
   xu=1.1) é o único dos 25 canônicos com bounds não representáveis em float32:
   `float32(1.1)` excede `xu` em 2,4e-8. **Medido: 8 de 29 sementes produziam
   uma ⑦ que o próprio `--check` reprovava.** Corrigido para uma tolerância de
   ~8 ULPs float32 da escala do bound + clip do ruído. **Agora 30/30.**
2. **MAJOR — o subprocess-por-venv era ferramenta, não mecanismo.** `run_in_venv`
   existia mas **nada roteava para ele**: `experiment.run` despacha sempre
   in-process, e o despachante serial (`experiments.py`, n_jobs=1) e o paralelo
   (loky, que REUSA workers) chamam `run()` direto. No dia em que b5r/c311
   fossem descomentados, a bateria co-importaria os dois overlays `desdeo_*`
   homônimos — o revisor **reproduziu** com os overlays REAIS do repo (21 `.py`
   de mesmo caminho e conteúdo diferente): o 2º `import desdeo_emo` devolve o
   pacote do b5, sem erro nem warning. Corrigido em 3 camadas: `VENV_ONLY_ALGS`
   + **roteamento obrigatório em `experiment.run`** (com `_in_child` cortando a
   recursão do bootstrap) + **`assert_overlay_coerente()`**, sentinela de
   processo que ABORTA se dois overlays de raízes distintas aparecerem.
3. **MAJOR — a sonda não sabia escrever classificador/score.** O docstring
   mandava "ver `emit_sonda_block_score`" — função que **não existia**; e o
   `np.vstack` estourava com saída 1-D (o formato do próprio contrato). Com o
   contorno óbvio, o score ia parar em `mu_0` e a confiança em `sigma_0` —
   envenenando a ③. **Afeta o c122 da R3** (score par-a-par). Implementado o
   despacho por `pred_tipo`: `pred_score`/`pred_classe`/`pred_confianca`,
   `concatenate` no caminho escalar, e recusa de `pred_tipo` inválido.
4. **MAJOR — assimetria de precisão no `nd_pos_real`.** Era computado sobre o F
   float64 mas o `--check` o recomputava sobre o F **float32 relido** — empates
   próximos reprovariam uma ⑦ correta. Agora ambos usam a vista float32
   persistida: a coluna é reproduzível a partir do arquivo, por construção.
5. **MAJOR — `check_final` impunha invariante MAIS FORTE que a declarada.**
   Exigia igualdade posicional da tabela inteira, então uma ⑦ que fosse o
   subconjunto ND, ou reordenada, levava vermelho FALSO. Agora confere pelo
   `origem_linha` que a própria ⑦ declara — o bug-alvo (a PROLE da última
   geração) continua morto, e há teste para os dois lados.
6. **MINOR — `check_final` estourava em vez de devolver `(False, msg)`**, e o
   gate morria com traceback **antes** dos checks 11–13 (manifesto, pinning,
   subprocesso nunca rodavam). Embrulhado.
7. **MINOR — dois checks do gate eram tautológicos.** `_r3_subprocess_probe`
   dizia "pin D79 no FILHO" mas só conferia que o processo terminou — o revisor
   deu VERDE com `OMP_NUM_THREADS=8` no filho. Agora o filho **devolve** a
   evidência (`pin_filho`, `isolated_filho`, `fe_final`) e o pai a EXIGE. E
   `_r3_env_resolution` só comparava duas strings do `envs.json` (verdadeiro por
   construção): agora prova que `VENV_ONLY_ALGS` cobre os 4 e que a sentinela de
   colisão realmente aborta.

Também corrigidos de passagem: `run_in_venv(interpreter=...)` zerava o `env_id`
e descartava os `env_flags` (o `MPLBACKEND=Agg` do c311 sumia); a ⑦ do caminho
nativo nascia sem sidecar de procedência; e a ⑦ **nunca subia ao bucket**
(`gcs.plan_targets` itera `LAYERS`) — resolvido dentro do `dual_write_run`, que
é da minha faixa, sem tocar `gcs.py`.

## O que os 7 cartões da R3 HERDAM — leia isto

1. **Esqueleto do runner** (copie do `run_stubr3`): `pin_runtime()` →
   `env_info()` → `load_offline_budget()` (offline) **ou** `load_doe()` +
   `FEBudget(D, logger)` (online) → `AuditLogger.for_run(..., append=False)` →
   `log.header(... sigma_dict=...)` → laço → `write_run_outputs` →
   `log.footer`. Assinatura: `runner(exp, alg, problema, semente, **kwargs)`.
2. **Offline (b5r, b5m, c311, piso-off):** o laço vai DENTRO de
   `with offline_guard(log, alg=..., problema=...)`. Nada no caminho do
   algoritmo pode chamar `bud.evaluate` com X inédita. `regime="offline"`.
3. **Online (c122, c149, e81):** `regime="online"`, `except BudgetExhausted`
   como fim NATURAL (D61), sonda por `sonda_due` (ver A-12 abaixo), e o offset
   **D22** já vem de `seed_base(alg, semente)` (`1000·semente` p/ e81 e c149).
4. **Sementes:** `iteration_seed(seed_base(alg, s), ALG_ID, it, uso_id)`, com
   `bits32=True` onde a API exige 32 bits (`pymoo.minimize`, `torch.manual_seed`).
   O catálogo de `uso_id` é de cada cartão (precedente c262: 0/1/2).
5. **pymoo interno:** SEMPRE `guarded_pymoo_minimize` (N.2.3).
6. **Fim de iteração:** `del` + `iteration_cleanup()` (D86). No **c149** isto
   não é higiene, é sobrevivência: o retreino-por-FE (D43) estoura no MEIO do
   run sem isso.
7. **Sonda:** `emit_sonda_block(..., predict=<seu preditor>)`. O `predict`
   recebe (n, D) NATIVO e devolve μ **em f de minimização** (o sinal do motor
   nunca vaza) + σ (ou `None` — RBF puro). Roda sob `preserve_all_rng()`.
   Classificadores/scores: passe `pred_tipo='classe'|'score'`.
   Prova objetiva exigida: a ① do run COM sonda = a ① do run SEM.
8. **`sigma_dict` (DEF-C4) é OBRIGATÓRIO** em `write_run_outputs`. A R4 o
   declara "leitura obrigatória antes de usar a ③" — sem ele a tabela é
   inauditável. Hoje só 2 dos 21 configs o têm (A-7/M-3 do retrofit R2).
9. **⑦:** offline chama `write_final(...)` no fim do run com os decs
   **float64** em memória (evita o caveat float32), respeitando o invariante
   acima. Depois: `PY scripts/final_eval.py --exp off --alg <cfg> ... --check`.
10. **Registro no dispatch:** descomente a sua linha em `_DISPATCH_LOADERS`.
11. **Venv:** `b5r/b5m/moead_media → env_b5`, `c311 → env_c311`,
    `e81 → env_e81_qpots`, `c122/c149 → env_main`. **b5 e c311 NUNCA no mesmo
    processo.** No Mac só o `env_main` está provisionado — os outros são
    decisão do autor (DI-11.5: pins vizinhos × exceção VM); o **mecanismo já
    está pronto e testado** com o env-main.

## ⚠ REGRA DE ORDEM do e103 — NÃO APLIQUEI (conforme o cartão)

O `__final` retroativo do e103 só pode rodar sobre o e103 **RE-PILOTADO** pelo
retrofit-MATLAB. No meu encerramento o log tem `[DI09-R1] infra` (`cc3eee1`) e
`[DI09-R1] c217` (`845743a`), **mas NÃO `[DI09-R1] e103`**. Portanto **não
apliquei**. Os runs do e103 em `data/experiments/main/e103/` são PRÉ-retrofit.

Comando pronto, para a torre rodar **depois** que o `[DI09-R1] e103` entrar:

```bash
PY=/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python
for p in MMF1 DTLZ2 ZDT1; do
  $PY scripts/final_eval.py --exp main --alg e103 --problema $p --semente 0
  $PY scripts/final_eval.py --exp main --alg e103 --problema $p --semente 0 --check
done
# na bateria (30 sementes, exp=off):
$PY scripts/final_eval.py --exp off --alg e103 --problema MMF1 --all-seeds
```

⚠ Antes de rodar, confira o invariante ⑦×③ no e103 re-pilotado: a ③ da última
geração tem de ser o `FinalDec`. O handoff R1-e103 §5 diz "os decs finais estão
na ③ (geração 99) e em FinalDec" — se o re-piloto mudar isso, o `--check` acusa.

## Definições em aberto / decisões para o autor

1. **🔴 Schema da camada ⑦ — SINALIZADO PARA VETO.** A DI-08 fixou
   `x*|f*|origem_solution_id/link à ③` e delegou o resto ("exige decisão de
   schema/naming — território da torre"). Concretizei (precedente das âncoras):
   `algoritmo|problema|semente|x*|f*|origem_solution_id|origem_geracao|
   origem_linha|nd_pos_real`. As duas colunas que vão além do literal da DI-08:
   **`origem_linha`** (o link posicional exato à ③ — a R4 regra 1 proíbe casar
   por X float32) e **`nd_pos_real`** (o filtro B7.5 aplicado DEPOIS da
   avaliação real: guardamos todos os N finais, D54, e marcamos quais
   sobreviveram — é a coluna que separa o front verdadeiro do "erro de
   fantasia"). **Ratificar ou mandar cortar.**
2. **✅ A-12 (cadência da sonda) — RESOLVIDA durante a sessão, sem ação minha.**
   A divergência Python (1,2,4,6,…) × MATLAB (1,3,5,7,…) foi cravada pelo autor
   na **DI-12.5**: vale a fórmula **Python**, e o MATLAB foi alinhado a ela
   (`a5f6eab`). Meu `sonda_due` já a implementava — **nenhuma mudança de código
   foi necessária**; só atualizei o docstring, que a descrevia como pendente.
   Idem o `tempo_geracao_s` DESCONTANDO a sonda (`47daa76` alinhou o MATLAB à
   semântica A-2/D-1 do retrofit R2, que é a que o `run_stubr3` usa).
   *Registro por transparência: escrevi esta pendência antes de a decisão
   entrar no log e a corrigi ao reler o log no fechamento.*
3. **⚠ A premissa do N.2.3 não se reproduz no env-main — MEDIDO.**
   `pymoo 0.6.2` **não desloca** `np.random` nem `random`, nem com `seed=`, nem
   sem. Logo a checagem "guarda de RNG provada contra `pymoo.minimize` REAL"
   (herdada do R2-00) é **vacuamente verde** ali: passaria mesmo se
   `preserve_global_rng` fosse um `pass`. A premissa vale para o **pymoo
   ANTIGO** dos venvs `env_b5`/`env_c311` — que é onde b5/c311 rodam e onde a
   guarda é indispensável. **O que fiz:** o gate e os testes agora provam o
   MECANISMO (perturbação máxima dentro da guarda + restauração bit-a-bit) e
   trazem uma sentinela de versão que falha se um upgrade de pymoo voltar a
   mexer nos globais. **Sugestão à torre:** aplicar o mesmo endurecimento ao
   check do R2-00 (fora da minha faixa).
4. **⚠ Caveat float32 da ⑦ retroativa.** Os decs da ③ estão em float32 (D53),
   então a rota retroativa (a única do e103) avalia o dec truncado. **MEDIDO**
   (não estimado): desvio relativo em `f` de até **9,7e-6** (MMF1) e 6,0e-8
   (ZDT1), com **0 inversões** de `nd_pos_real`. Os cartões R3 evitam isso
   chamando `write_final` com float64. Registrado no sidecar
   (`origem_precisao`). **Aceitar ou exigir que o e103 re-pilotado persista os
   decs finais em float64 à parte.**
5. **⚠ Herdo o bloqueador B-1/A-9 do retrofit R2, e ele é da faixa R3-00.**
   `experiments.py::_run_one` **recria** o manifesto depois do `run()`,
   apagando `sigma_dict`, o bloco `sonda`, `doe_hash`, `fe_final`, `env`,
   `fit_series` e trocando `timing` por um stub com 3 chaves `None`. **Não
   consertei:** `experiments.py` (raiz, o despachante) não está na lista de
   faixa do meu cartão, e a correção muda a semântica de resume/`run_done` —
   é decisão de infra (DI-06/M7). **Enquanto não for consertado, despachar por
   `src.experiment.run(...)` direto** (foi o que o gate e os pilotos fizeram).
   Se a bateria M8 for por `experiments.py`, os 16.500 runs perdem o payload
   DI-09/DI-10 do manifesto **sem sintoma visível**.
6. **⚠ Resume × camada ⑦.** `manifest.is_run_done` não conhece a ⑦ (por
   desenho — ela é opcional). Consequência: um run offline **sem** a ⑦ conta
   como "pronto" e a esteira não a gera sozinha. Hoje a ⑦ é passo pós-hoc
   explícito (`final_eval.py`), o que é o previsto pela DI-08; **se a torre
   quiser que o resume a cobre nos 5 offline, é 1 condicional em
   `is_run_done`** — não a pus para não mexer em `manifest.py` sem decisão.
7. **⚠ A ⑦ sobe ao bucket por um caminho PRÓPRIO, não pelo `plan_targets`.**
   `gcs.plan_targets` itera `naming.LAYERS`, que exclui a `final` de propósito
   (§Modificados). Para a ⑦ não sumir com uma VM destruída, o
   `standalone_harness.dual_write_run` a sobe explicitamente (+ sidecar). Isso
   mantém os 16 online intactos e não toca `gcs.py` (fora da faixa), mas cria
   **duas rotas de upload**. **Sugestão à torre:** dar a `plan_targets` um
   parâmetro `optional_layers=()` e passar `('final',)` no caminho offline —
   1 função, e a rota volta a ser única. Não fiz por ser faixa alheia.
8. **🔴 LACUNA DO §4 SEM DONO — o piso com `fit=NULL` NÃO é gravável.**
   O CONTRATO §4 manda: *"Pisos: ④ por geração com `tempo_geracao_s`
   (fit=NULL)"*. O `SnapshotBuffer` aceita `tempo_fit_s=None` (fiel ao
   contrato), mas o **escritor não grava**: `export.timing_schema()` declara
   `tempo_fit_s` com `nullable=False` e `export.write_timing` faz
   `float(r["tempo_fit_s"])` sem guarda → `TypeError`. **Conserto = 2 linhas em
   `src/export.py`** (nullable + guarda de None), que é **faixa do
   retrofit-BoTorch** — por isso não o fiz. **Atinge o cartão `piso-off`
   (`moead_media`) da R3 e os 4 pisos ONLINE da R1.** Há sentinela em
   `tests/test_r3_harness.py::test_LACUNA_CONHECIDA_piso_com_fit_NULL_nao_e_gravavel`
   que falha quando a lacuna for fechada, para quem corrigir lembrar de
   atualizar este handoff. *Descoberta ao conferir o contrato §4 item a item
   depois do fechamento, a pedido do autor.*
8. **`load_sonda` duplicado** (aqui e em `botorch_harness`) — necessário
   (envelopes de dependência distintos: lá o módulo importa torch no topo).
   Há **teste de equivalência** que falha se divergirem. **Sugestão:** extrair
   para um módulo torch-livre compartilhado num cartão de hardening (M7/DI-06);
   não fiz porque exigiria editar `botorch_harness.py` (fora da faixa).
9. **`KNOWN_ALGORITHMS` do `experiments.py`** não tem `stubr3` (nem precisa — o
   gate não passa pelo CLI). Quando os configs R3 entrarem, conferir o roster.

## Como reproduzir

```bash
PY=/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python
$PY scripts/accept.py R3-00-harness --problema MMF1  --semente 0   # exit 0
$PY scripts/accept.py R3-00-harness --problema ZDT1  --semente 0   # exit 0
$PY scripts/accept.py R3-00-harness --problema DTLZ2 --semente 0   # exit 0
$PY scripts/accept.py R3-00-harness --problema MMF11_L --semente 0 # exit 0
$PY -m unittest discover -s tests -t .                             # 193 OK (1 skip)
# regressão (NÃO rodar gates R1/R2-c* — faixas ativas):
for c in F0-01-harness F0-02-doe F0-03-export F0-04-metrica; do $PY scripts/accept.py $c; done
$PY scripts/accept.py R2-00-harness --alg stubpy --problema MMF1 --semente 0
$PY scripts/preflight.py
# a camada ⑦ isolada:
$PY scripts/final_eval.py --exp off --alg stubr3 --problema MMF1 --semente 0 --check
```
Saídas do `stubr3` em `data/experiments/off/stubr3/` (gitignored; regeneráveis).

## Commits desta sessão (branch `experiment/definitive_algorythms`)

Prefixo `[R3-00]`, ritual anti-mistura (`git add` EXPLÍCITO da faixa, nunca
`git add -A`). Nada de `.m`, de `algorithms/**`, de `export.py`/`botorch_harness`
ou de SPEC/bundles/artifacts foi staged. **SEM INDEX** (a torre marca).
