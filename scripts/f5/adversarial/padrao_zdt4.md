## PADRÃO SISTÊMICO — contaminação de proveniência

**Artefatos:** `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/padrao_zdt4/` → `scan_provenance.py`, `teste_3x1.py`, `teste_camadas.py` (scripts) · `scan_cells.csv` (666 células × 60 campos), `vs_datadir.csv`, `vs_maquinas.csv`, `teste_3x1.csv`, `teste_camadas.csv`, `celulas_afetadas.csv` (tabela final), `inodes.json`. Tudo read-only sobre os dados.

### Resumo executivo

1. A varredura achou **666 células** (não 664) e **34 com assinatura de proveniência anômala (5,1%)**; das 4 que têm **conteúdo do bucket ≠ conteúdo do Mac**, **4 de 4 são ZDT4** — c149/q10_ZDT4, e81/q10_ZDT4, **sobol_batch/q10_ZDT4 (achado NOVO, nenhum analista viu)** e e103/swap_medium-lhs_ZDT4.
2. A causa não é "provisionamento copiou `data/`" e sim **duas causas encadeadas**: (a) o predicado idempotente `is_run_done` faz o disparo **PULAR** a célula quando o smoke pré-campanha já deixou artefato em `data/` — 22 células "pulou" nos `done.txt`, das quais **9 são ZDT4**; (b) `AuditLogger` abre o `.jsonl` em modo **`"a"` (append) sem nenhuma guarda** (`src/audit_log.py:55`), então toda re-invocação empilha `header`/`footer` do despachante sobre um run já fechado.
3. **ZDT4 é a ponta visível porque é a célula-de-smoke canônica**: está no roster dos 5 problemas de `batch` **e** dos 6 tokens de `sweep`, e é o **menor D (=10)** dos cinco → o mais barato (maxFE 309/2109 contra 929/2329 do ZDT1). O §6 do `RUNBOOK_VALIDACAO_42.md` manda "1 smoke por token antes das 90"; o operador escolheu o mais barato, em todas as máquinas.
4. **Dano científico real = 1 célula.** Só `c149/q10_ZDT4` é quimera; provei que a ③ do bucket bate **2.000/2.000 bit-a-bit** contra a ① do **Mac (24/07)** e **0/2.000** contra a ① do próprio bucket (VM, 26/07). As outras 3 são metadados/⑦, dano zero nos dados.
5. **O teste 3×1 rodou nas 666**: 360 aplicáveis, **359 OK a 100% bit-a-bit, 1 FALHA**. `①.nrows == manifest.fe_final` fecha **666/666**; `footer.fe_final == manifest.fe_final` fecha **666/666**; `doe_hash` e `sonda.x_hash` particionam **25/25 problemas** sem uma célula órfã. O resto da campanha está limpo.

---

### Alcance — 34 células, por assinatura

Sinais: **S1** >1 `header` · **S2** linha JSON malformada (splice de escrita) · **S3** timestamp retrocede · **S4** footer faltante vs o esperado do stack (MATLAB=1, Python=2) · **S5** footer extra · **S6** bucket ≠ `data/` do Mac · **S7** falha no 3×1 · **S8** consta como `pulou` nos `done.txt` · **S9** `ts_first` < 26/07 (pré-campanha).

| # | célula | ts_first (UTC) | sinais | classe |
|---|---|---|---|---|
| 1 | **e81/q10_ZDT4** | 24/07 11:46:33 | S1,S5,S6,S8,S9 | ⑥ poluída (94 pares espúrios no bucket, **104 no Mac**) |
| 2 | **c149/q10_ZDT4** | 26/07 14:52:58 | S6,**S7** | **quimera de camadas** |
| 3 | **e103/swap_medium-lhs_ZDT4** | 24/07 00:45:03 | S6,S9 | ⑦ obsoleta no bucket |
| 4 | **sobol_batch/q10_ZDT4** | 26/07 10:25:22 | S6 | execução dupla, payload bit-idêntico |
| 5 | moead_media/swap_small-lhs_ZDT1 | 26/07 11:24:10 | S2,S3,S5 | ⑥ com tentativa falha + run ok concatenados |
| 6 | b1/WFG1 | 26/07 23:33:56 | S2,S4 | ⑥ com **49 linhas spliced**, 0 footer |
| 7–10 | e103/{DTLZ7, WFG2, WFG4, WFG9} | 26/07 23:21–23:27 | S2 | 1 fragmento residual no fim do ⑥ |
| 11–16 | b5m/{swap_medium-lhs_MMF16_20, swap_medium-lhs_ZDT4, swap_medium-mvns_ZDT4}, b5r/swap_small-mvns_ZDT4, c311/{swap_big-lhs_ZDT4, swap_big-mvns_ZDT4} | 24/07 00:17–02:02 | S4,S8,S9 | versão oficial = smoke de 24/07 |
| 17–22 | treed_media/{swap_big-lhs_DTLZ2, swap_big-lhs_MMF16_20, swap_big-lhs_WFG9, swap_big-lhs_ZDT1, swap_big-lhs_ZDT4, swap_big-mvns_ZDT4} | 24–25/07 22:32–01:04 | S4,S8,S9 | versão oficial = smoke de 24-25/07 |
| 23–30 | c311/{swap_small-lhs_MMF16_20, -WFG9, -ZDT1, -ZDT4, swap_small-mvns_DTLZ2, -MMF16_20, -WFG9}, treed_media/swap_big-mvns_MMF16_20 | 26/07 11:07–11:09 | S4,S8 | smoke-por-token de 26/07 (15 min antes do lote das 11:23), **0 footers** |
| 31 | c311/swap_small-lhs_DTLZ2 | 26/07 11:23:02 | S8 | pulou, mas artefato íntegro (2 footers) |
| 32–34 | nsga2/{MMF1, MMF4, ZDT3} | 25/07 22:05–22:09 | S9 | herdadas dos gates de aceite da fase 3 (confirma o §11 do `HANDOFF_operacao_multimaquina.md`) |

**Concentração em ZDT4:** 49/666 células são ZDT4 (7,4%); ZDT4 responde por **12/34 das afetadas (35%)**, **9/22 dos `pulou` (41%)**, **9/11 das células de 24/07 (82%)** e **4/4 das divergências bucket↔Mac (100%)**.

---

### Causa provada

**Passo 1 — o smoke deixa artefato.** `RUNBOOK_VALIDACAO_42.md §6.3`: "1 smoke por token antes das 90". Rodado 24-25/07 com **ZDT4** (menor D dos 5 do sub-estudo). `scripts/accept.py:256` usa literalmente `("ZDT4", 42)` como par canônico de verificação. Os `doe_hash` e `sonda.x_hash` desses runs **batem 100% com os dos irmãos de tier** (artefatos congelados em `data/doe` 16/07 e `data/sonda` 19/07) → o smoke não usou insumo diferente.

**Passo 2 — o disparo pula.** `experiments.py::_stage_grid` → `src/manifest.py:143 is_run_done()` devolve True (manifesto `ok` + `fe_final==maxfe` + camadas presentes) e a célula **nunca é re-executada**. O `lote42.sh:230` infere isso pelo `mtime` do manifesto e grava `pulou`. **22 ocorrências únicas** em `_old/_lotes_mac/*done.txt` (209 ok, 69 pulou, 60 failed).

**Passo 3 — o writer faz append cego.** `src/audit_log.py:55`: `open(path, "a" if append else "w")`, com `append=True` default e **nenhuma checagem de footer preexistente**. `experiments.py:98/182` (`_run_one`) escreve `log.header(run_id, alg, problema, semente, exp, modo_rapido)` e `log.footer(status, n_retries, tempo_total_s, stack_trace)` — **exatamente os campos dos 94 headers espúrios do e81** (todos com `D`, `M`, `maxfe`, `n_init`, `regime`, `versao`, `params`, `sigma_dict` = NULL).

**Passo 4 — a prova de campo.** Os `.jsonl` locais das VMs para essa célula contêm **só os pares espúrios**, nada mais:
- `_old/_maquinas/v5/experiments/batch/e81/exp_batch_e81_ZDT4_42.jsonl` = **620 B, 2 pares**, 26/07 00:08:53
- `_old/_maquinas/v6/.../exp_batch_e81_ZDT4_42.jsonl` = **620 B, 2 pares**, 26/07 00:07:43
- `_old/_maquinas/vm3/.../exp_batch_e81_ZDT4_42.jsonl` = **2.480 B, 8 pares**, 25/07 20:51 → 26/07 00:10
- as três acompanhadas de um **manifesto-toco de 1.279 B**

`batch/e81` **não está no roster de nenhuma VM** (`lote42.sh`: v5=`main/c154`; v6=`batch/{sobol_batch,c149,c262}`+`main/c262`; vm3=MATLAB+`main/c122,c149`+`off/sweep e103`; e81 é Mac-only, venv `env_e81_qpots`). Logo essas invocações foram **smoke manual da mesma célula em cada máquina**, e cada uma criou/estendeu o `.jsonl` do run legítimo do Mac.

**Passo 5 — por que só o c149 virou quimera.** O manifesto do bucket de `batch/c149/ZDT4` traz `upload_status.surrogate = "uploaded_bucket_only"` e `env.executable = /home/jupyter/python_venvs/env_main/bin/python` (VM, torch `2.11.0+cu130`, run 26/07 14:52→19:05, wall 15.164,6 s). O Mac tem em `data/experiments/batch/c149/` um run **completo e coerente** de 24/07 11:05→13:01 (wall 6.972,0 s, torch `2.11.0` CPU). Comparação arquivo a arquivo: `③ surrogate` e `② pop` **byte-idênticos** entre bucket e Mac; `① real` (124.039 vs 126.091 B), `④ timing` (6.789 vs 6.865 B), `⑥ jsonl` e manifesto **diferentes**. Teste cruzado decisivo:

| par testado | X bit-idêntico | max‖ΔX‖ |
|---|---|---|
| ③(bucket) × ①(bucket, VM 26/07) | **0/2.000** | 9,999830 |
| ③(bucket) × ①(**Mac 24/07**) | **2.000/2.000** | **0** |

Ou seja: o objeto `..._surrogate.parquet` do bucket **é o do smoke do Mac**; as demais camadas são do run da VM. A única diferença de configuração entre os dois runs é o build do torch (`2.11.0` vs `2.11.0+cu130`) — `versao`, `params`, `sigma_dict`, `doe_hash`, `pinning`, numpy/scipy/pymoo/sklearn/gpytorch idênticos. É isso que produz o desvio ~1e-3 já em g=1 que o analista do c149 mediu.

**Passo 6 — o vazamento é atual.** O `.jsonl` do Mac (`ua-dd-saea/data/experiments/batch/e81/exp_batch_e81_ZDT4_42.jsonl`) tem hoje **767 linhas / 105 headers / 104 pares espúrios**, contra 747/95/94 no snapshot do bucket. Distribuição dos pares: 48 em 24/07, 38 em 25/07, 4 em 26/07, 6 em 28/07, **8 em 29/07 (até 01:59:34 UTC)** — **10 pares depois do congelamento do bucket**, em 5 invocações. Os parquets ①②③④ dessa célula seguem com mtime **24/07 09:21** (nunca regerados). Sempre **2 pares por invocação**, com 1–7 ms de intervalo, em todas as 4 máquinas.

**Achado adicional (mesma família, outro mecanismo):** 6 células têm **linha JSON malformada por escrita entrelaçada**. Em `b1/WFG1` (49 de 931 linhas) o splice é visível: `..."tempo_fit_s":4{"ts":"20{"ts":"2026-07-27T00:27:12Z","rec":"guard"...` — três escritas emendadas. Em `moead_media/swap_small-lhs_ZDT1` o `.jsonl` guarda o `footer status=failed / erro_RuntimeError` de 11:24:15 (o bug do `--enable-bucket` no Mac) **e** os 2 footers do run ok de 11:26:29 → 3 footers e retrocesso de **134,3 s** no timestamp. Em `e103/{DTLZ7,WFG2,WFG4,WFG9}` sobrou um fragmento de linha antiga no fim. Mesma raiz: **append sem truncar, sem lock, sem guarda**.

---

### Dano por célula

| célula | camadas confiáveis | camadas NÃO confiáveis | veredito | recuperação |
|---|---|---|---|---|
| **c149/q10_ZDT4** | nenhuma **como conjunto** no bucket; o par {③,②} é de um run, {①,④,⑥,manifesto} de outro | a coerência inter-camada; qualquer métrica que ligue ③ a ① (fantasia, calibração μ/σ, `acq_resF_*`, `transf_params`) | **REPROVADA-F5.4 na versão do bucket** — mas **RECUPERÁVEL** | **substituir a célula inteira pela cópia do Mac de 24/07** (`ua-dd-saea/data/experiments/batch/c149/`, 6 arquivos, ①③ provados coerentes 2.000/2.000). Custo: cópia + re-rodar F5.1/F5.2 nessa célula ≈ minutos. Alternativa: re-executar (1,94 h no Mac / 4,21 h na VM) |
| **e81/q10_ZDT4** | ①(2.109) ②(222.800) ③ ④ — **byte-idênticos** entre bucket e Mac, ambos do run de 24/07 | o `.jsonl` (94 pares espúrios) e o `updated_at` do manifesto (28/07 18:42 vs `created_at` 24/07 12:21) | **APROVADA com ressalva** — dano zero nos dados (confirma o B28) | filtrar do ⑥ os `header` com `D==null` e os `footer` com `fe_final==null` e `tempo_total_s<1 s`: 188 linhas, 6,686 s somados. Custo: 1 filtro, segundos. **Congelar o arquivo antes** — ele ainda cresce |
| **e103/swap_medium-lhs_ZDT4** | ①②③④⑥ — byte-idênticos ao Mac | apenas a ⑦ do bucket (200 linhas = a geração 99 inteira, `XF==XS` bit-a-bit, Kriging-DACE ≡ RBFN) | **APROVADA após troca da ⑦** | a ⑦ correta **já existe** em `ua-dd-saea/data/experiments/sweep-medium-lhs/e103/` (100 linhas = subconjunto Kriging-DACE, `n_nd_pos_real=5`). Custo: copiar 2 arquivos (10,6 KB), **zero re-run** |
| **sobol_batch/q10_ZDT4** | ①②③ **bit-idênticas** entre o run do Mac (24/07 17:21) e o da VM (26/07 10:25) | só `⑥`, `④ timing` e o manifesto (timestamps/wall) | **APROVADA** — e de brinde é uma **prova de reprodutibilidade bit-a-bit cross-máquina** para o sobol | nada a fazer |
| 22 células `pulou` + 3 `nsga2` | todas as camadas de dado: `fe_final==maxfe` (666/666), `footer.fe_final==manifest.fe_final` (666/666), `doe_hash`/`x_hash` iguais aos irmãos de tier, contagens estruturais iguais | apenas o **contrato do ⑥**: 21 células com footer faltante (9 com **zero** footer) | **APROVADAS** cientificamente, **REPROVADAS no contrato §6/S.7.1** | nenhuma re-execução justificada. **Ação obrigatória:** corrigir a regra O-22 antes do portão (ver prescrição 5) |
| b1/WFG1 | ①②③④ (T1 ok) | ⑥ (49 linhas ilegíveis, sem footer) | **APROVADA com ⑥ degradada** | ⑥ irrecuperável sem re-run (~1,1 h). Marcar como não-parseável no censo |
| moead_media/swap_small-lhs_ZDT1 · e103/{DTLZ7,WFG2,WFG4,WFG9} | todas as camadas de dado | 1 linha do ⑥ | **APROVADAS** | descartar a linha malformada na leitura |

**Correção material ao achado A25 do e103:** o analista propôs reler a fantasia dessa célula como **0,10** em vez de 0,05. Está **errado**. A ⑦ regerada dá `n_nd_pos_real=5 / n_final=100 = **0,0500**` — numericamente **igual** ao 10/200 reportado. O valor publicado em `endpoint_e103.csv` **não muda**; muda só a razão de ele estar certo. Aplicar a correção sugerida introduziria um erro de 2×.

---

### Prescrição para a F5.7 (torre central), com custo

| # | item | onde | custo |
|---|---|---|---|
| **1** | **Guarda anti-append no writer.** `AuditLogger.__init__` (`src/audit_log.py:50-55`): se o arquivo existir **e já contiver um `footer` com `fe_final` não-nulo**, levantar `RunJaFechado` em vez de abrir em `"a"`. É a correção de raiz — mata as 3 famílias (e81, moead_media, e103-fragmento) de uma vez. | `src/audit_log.py` | **~15 linhas + 2 testes.** 1 h |
| **2** | **Não abrir o ⑥ no caminho no-op.** `experiments.py::_run_one` (linhas 98/182): só instanciar o `AuditLogger` **depois** de confirmar que o runner vai de fato executar; no caminho de skip, registrar em log de operação (stdout/`done.txt`), nunca no `.jsonl` da célula. Resolve a alternativa (a) que o B28 pediu. | `experiments.py` | **~10 linhas.** 30 min |
| **3** | **Escrita de linha atômica.** Trocar o `open(..., buffering=1)` por `os.write(fd, linha.encode())` com `O_APPEND` e recusar linhas > `PIPE_BUF` (4096 B) — as linhas de `header`/`sigma_dict` passam disso e são exatamente onde o splice do `b1/WFG1` ocorreu. Alternativa mais simples: `fcntl.flock` por escrita. | `src/audit_log.py` + `src/b1_instrument.m` (2 handles no mesmo arquivo) | **~20 linhas + 1 teste de concorrência.** 2 h |
| **4** | **Rito de provisionamento: `data/experiments/` nunca viaja.** Ele já é ignorado no git; o que falta é a **guarda ativa**: no arranque, `lote42.sh`/`lote3s.sh` abortam se existir qualquer `data/experiments/**/*.manifest.json` cujo `env.executable` **não** seja o intérprete da máquina corrente. Uma linha de `find` + `jq`. | `scripts/lote42.sh`, `scripts/lote3s.sh` | **~8 linhas.** 30 min |
| **5** | **`is_run_done` com carimbo de campanha.** Acrescentar ao manifesto um `campanha_id` (ex.: hash do commit + data do disparo) e fazer `is_run_done` devolver **False** quando o `campanha_id` gravado ≠ o corrente. Isso é o que impede o smoke de virar resultado oficial — sem ele, nas 30 sementes cada smoke por token vira 1 célula silenciosamente pré-campanha. | `src/manifest.py:143`, escrita do manifesto | **~25 linhas + migração do schema (v1→v2).** 3 h |
| **6** | **Portão: 3 gates novos, todos O(1) por célula.** (i) **3×1** — X da linha da ③ com `real_solution_id` ≡ X da ① (pega a quimera do c149; roda em **6,9 s nas 666**, medido); (ii) **unicidade do ⑥** — exatamente 1 `header` e o nº de `footer` esperado **por stack** (MATLAB=1, Python=2) + 0 linhas malformadas; (iii) **coerência de proveniência** — `env.executable` do manifesto ∈ intérpretes declarados no roster daquele alg em `envs.json`. | `scripts/portao.py` (ou `f5/baterias/f54/padrao_zdt4/teste_3x1.py`, já pronto) | **~60 linhas; execução 20,5 s de CPU nas 666.** 2 h |
| **7** | **Corrigir a regra O-22** ("footer ausente = morte de máquina"). Ela dá **falso positivo em 9 células** desta rodada, todas smokes completos. O discriminador correto é: *footer do runner ausente **E** manifesto ausente/incompleto* = morte; *footer do despachante ausente com manifesto `ok` e `fe_final==maxfe`* = **smoke fora do despachante**. | `HANDOFF_validacao_fidelidade.md §7`, `scripts/portao.py` | doc + 1 condicional. 30 min |
| **8** | **`mirror_run` no fim de run *e* no aborto**, e **nunca sobrescrever objeto de outra máquina**: subir com `x-goog-if-generation-match` ou prefixar por `campanha_id/host`. Sem isso, o dual-write das VMs continua podendo passar por cima de um objeto do dono legítimo — foi assim que a ③ do c149 sobreviveu ao run da VM. | `src/gcs.py` | **~30 linhas.** 2 h |
| **9** | **Regerar a ⑦ incondicionalmente** no rito de fechamento (ou deduplicar por `modelo_flag` no driver) — item 9 do e103, confirmado: das 45 ⑦ do e103, 44 têm mtime 21:57:15–21:57:38 e a de `swap_medium-lhs_ZDT4` tem **21:42:51**, a única não regerada. | `scripts/final_eval.py` | **~5 linhas.** 20 min |
| **10** | **Ação imediata, antes de qualquer coisa:** congelar `ua-dd-saea/data/experiments/batch/e81/exp_batch_e81_ZDT4_42.jsonl` (modo 444) — ele ganhou 10 pares espúrios **depois** do snapshot do bucket, o último em 29/07 01:59:34 UTC. | — | 1 comando |

**Custo total dos 10 itens: ~12 h de trabalho de código + 1 migração de schema de manifesto. Zero re-execução obrigatória** (a única re-execução opcional é `b1/WFG1`, ~1,1 h, só para recuperar o ⑥). Sem os itens 1, 2 e 5, as 30 sementes multiplicam o padrão por 30: pela taxa observada, **~1.020 células com assinatura anômala e ~30 quimeras** em 19.980.