# T11 — HANDOFF FINAL DA CAMPANHA (2026-07-29/30)

> # ⚠ ESTE ARQUIVO ESTAVA OBSOLETO — leia este bloco antes de qualquer número abaixo
>
> Ele foi escrito no commit `e492d39` e se apresentava como "HANDOFF FINAL"
> enquanto **11 commits** aconteciam depois, incluindo uma auditoria adversarial
> que achou **4 CRÍTICOS**. Itens listados aqui como pendentes já fecharam;
> itens dados como fechados voltaram atrás. **A fonte viva é o
> `T11_STATUS.md`**; este arquivo é a fotografia de 30/07 08:27, mantida pelo
> histórico.
>
> ### O que mudou depois dele
>
> | | |
> |---|---|
> | Suíte | 587 → **627 testes**, 0 falhas |
> | **A3/I-05** | ✅ **PROVA PASSOU** — ①③⑦ byte-idênticas com × sem o patch vendorizado (worktrees isolados). E a ERRATA 9 derrubou minha alegação de "2,5× de lentidão": medido, COM 2.781 s × STOCK 2.810 s |
> | **A11** | ganhou o **gêmeo MATLAB** (b4/c217/e74) |
> | **G-6** | saiu de 10 para **19 configs** (gêmeo MATLAB da flag `UA_DD_SAEA_SONDA_OFF`) |
> | **V1/VD-b1** | **ERRATA 10 — RETIRADO.** Estava superestimado (inerte em ~93,9%) e MAL CLASSIFICADO: a SPEC já o tem como 🟠 IMPL → CÓDIGO. **Nada muda no b1** |
> | **A9/c217** | era **CARIMBO FALSO** — a `regra do rótulo` nunca foi escrita; escrita agora (e o pareamento é POSICIONAL E CÍCLICO, não o do b4) |
> | **Varredura** | 78 achados · **4 CRÍTICOS**, todos falso-verde: portão dava VERDE com INCONCLUSIVO · guarda G-8 cega à raiz (e um teste escrevia em produção) · G-1 sem controle-positivo · G-1 explodia e derrubava o censo |
> | **Staleness** | 9 de 10 pares G-6 estavam STALE; re-provados c122/c311/treed_media/b5m — o c122 voltou com o **mesmo ①** |
> | **Erratas** | 8 → **13** |
>
> As §§ abaixo permanecem como estavam em 30/07 08:27.

---


> **Para quem lê primeiro:** o `T11_STATUS.md` tem o hash e as pendências de CADA
> item; este arquivo tem o **como**, o **porquê** e — o mais importante — as
> **erratas** e os **contratos novos** que mudam como o próximo agente deve ler o
> repo. O relatório das verificações dirigidas está em
> `handoff/T11-V1-verificacoes-dirigidas.md`; o parcial da FASE G, em
> `handoff/T11-parcial-2026-07-29.md`.

## 1. Placar

| | |
|---|---|
| Commits | **36** (`519b3e4` … `a23b1da`), a partir de `fbf8df8` |
| Código | 72 arquivos · **+8.831 / −275** linhas |
| Suíte | **394 → 587 testes, 0 falhas** (35 arquivos de teste; +193 testes) |
| FASE G | **7/7** (G1-G7; G6 com os 9 gates + 4 artefatos) |
| FASE A | **A1-A11** — 8 fechados, 3 parciais (falta o que exige máquina) |
| FASE V | V1 ✔ (relatório) · V3 parcial · V2 é CPU do autor |

## 2. O que mudou, em uma linha por item

| item | entrega |
|---|---|
| **G1** | ⑥ blindado: `RunJaFechado` (B-01) + 1 linha = 1 `os.write`/O_APPEND + `flock` (B-11), nos DOIS writers |
| **G2** | o skip não abre o ⑥ (B-02) · `NO_RETRY` (B-16) · ⑤ do aborto com a célula (I-10) · DI-40 revogada |
| **G3** | `campanha_id` schema v2 (B-03) · `limpar_celula` no `--force` (OP-6) · `certidao_do_run` (O-21) |
| **G4** | `mirror_evidencia` no aborto (B-09) · `if-generation-match` + poda só com md5 (B-10) |
| **G5** | teto **elapsed-only** + truncamento-com-dado · `src/checkpoint.py` em 8 runners · kill-test |
| **G6** | 4 artefatos normativos + `gates_proveniencia.py` (G-1..G-4, G-7, B-15) + `content_hash.py` (G-9) + `--par` (G-6) + suíte hermética + guarda anti-escrita + 9 drivers no git |
| **G7** | cronômetro no portão de avaliação (I-02, com NULL) · `repo_hash` nos 2 stacks (I-09) |
| **A1-A11** | ver §5 |
| **V1** | VD-b1 🔴 confirmado com número · VD-b3 🔴 estrutural |

## 3. As 8 ERRATAS — o que o documento dizia × o que o dado diz

Todas nasceram da regra *"verifique antes de escrever"*. Cada uma teria virado
trabalho errado se eu tivesse seguido o texto.

| # | fonte | dizia | é |
|---|---|---|---|
| 1 | PLANO/B-11 | splice nas linhas de header/sigma_dict | header = **512 B**; as 49 malformadas são `b1_gen`/`sonda` (mediana 1.647 B) |
| 2 | PLANO/B-11 | "`b1_instrument.m`: 2 handles" | **não existe** 2º handle (só `experiment.m` tem `fopen`) |
| 3 | PLANO/B-12 | abortar se venv ≠ o da máquina | daria **304 falsos-positivos**; o discriminador é o **host** ⇒ **58** reais |
| 4 | aceitação | re-gate = 1 quimera + **34** anômalas | 1 ✔ + **15**; as outras 21 são as que o **B-15 manda não acusar** |
| 5 | I-13 | `geracoes_derivadas` = `⌈…⌉` | acerta **0/112**; `floor(…)` 103/112 ⇒ é **EMERGENTE** |
| 6 | (meu gate) | `mll_final`/`loss_treino` ausentes | **ANINHADOS** em `modelo_hp` |
| 7 | §6.1 | e103 sem `margem_3sigma` | grava `margem_3sigma_stats`, **mais rico** |
| 8 | §6.1 | c154 deve ter `n_baseline` | o `sigma_dict` do runner já dizia "AUSENTE POR DESENHO" |

## 4. Os 6 CONTRATOS NOVOS (leia antes de tocar em qualquer coisa)

1. **`fe_final` de um ⑤ `checkpoint_em_andamento` é PISO das camadas.** As 5
   escritas são atômicas uma a uma, não como grupo; o ⑤ é a última. Um ⑤ *atrás*
   subdeclara dado que existe; um ⑤ *à frente* prometeria dado que não existe — e
   é essa a mentira que a campanha não pode ter.
2. **`is_run_done` exige `campanha_id`**; v1 ⇒ False (força o re-run das stale).
   Para auditar o passado: `manifest.QUALQUER_CAMPANHA`.
3. **O despachante abre o ⑥ com `append=False`** — quem chega ao `_run_one` é o
   dono do arquivo. Reverter isso reativa o B-01 contra o resume.
4. **Aborto sancionado passa pelos gates de PROVENIÊNCIA** (só os de conteúdo
   são dispensados): com truncamento-com-dado a célula TEM camadas.
5. **`tempo_aval_real_s` pode ser NULL** — "não medi" ≠ "custou zero".
6. **O gate G-3 tem 2 modos**: `campanha` (estrito) × `historico` (audita a s42,
   cujos ⑤ não têm `campanha_id`/`repo_hash`).

## 5. FASE A — o que entrou por config

| config | entregue | número que prova |
|---|---|---|
| **c154** | `params` ⑤ · regra I-12 · `executable` ⑤ | I-12 fecha **1.200/1.200 blocos** |
| **c122** | `n_ref` real · `ref_ids` · regra-rótulo · `y_treino_dist` | **n_ref=21 (=11D−1) no g=1 × 11 no g≥2** |
| **b5r/b5m/moead_media** | `p_wrong_stats` (patch vendorizado) · `params` · granularidade ③ | era **0/30.165** eventos |
| **c262** | 8+2 hp da acqf · `params` · `fit_retries` guard | 24 células sem `params` |
| **e103** | `tempo_geracao_s` | era o único config sem |
| **sobol_batch** | `minimo_comum_di10` | era **1/47** pares sem `n_front1` |
| **nsga3+pisos** | `geracoes_derivadas` reescrita | a fórmula do plano acerta **0/112** |
| **b4** | regra-rótulo + glossário p0/p1 + `y_treino_dist` | trocar p0/p1 derruba 6.268→1.252 |
| **e74** | **FIX DI-45** + âncora + re-lacre | argmax inerte em **87,76%** dos ciclos |
| **c217** | `pmid_ids` · `y_treino_dist` · `params` | identidade era **0/25** células |
| **c311/treed** | guard de tier · aviso `n_sigma_valido` | σ-NaN mediano **90,3%** no big |
| **A11** | sonda estratificada (c122) | prevalência **7,4% × 0,4%** = 18× |

## 6. O QUE FALTA — por quem depende

### 6.1 Precisa das SUAS máquinas (não fecho aqui)
1. **Smoke MATLAB** de 1 célula por config (13 configs) — toquei `experiment.m`,
   `b3/b4/c217/e103_instrument.m` e o vendorizado do e74; o engine MATLAB não
   importa neste venv.
2. **e74 pós-DI-45**: smoke de 3 células + gate ±3σ, e conferir que
   `n_desalinhado` **cai a ~0** (é a prova do fix).
3. **c154 D≥12**: validar que morre às 12 h **com** camadas parciais.
4. **c262-batch**: probe de RAM → `--n-jobs` no RUNBOOK.
5. **V2**: os re-runs da s42 (1,17 h-core) + as ~29 não-ok no regime novo.
6. **Limpar os 58 manifestos forasteiros** de `data/experiments` (o preflight
   sai ≠ 0 até isso).
7. **`export UA_DD_SAEA_CAMPANHA_ID=...`** nas 4 máquinas (§ do RUNBOOK).

### 6.2 Decisões que são suas
1. **Ratificar o placar do re-gate**: 1 quimera + **15** anômalas + 21
   `footer_faltante` (a aritmética completa está no T11_STATUS e no §3 acima).
2. **VD-b1** (93,0% das gerações): manter como fidelidade-ao-código, corrigir
   como o DI-45, ou corrigir só no M8. Relatório completo no arquivo do V1.
3. **VD-b3**: autorizar as ~2 linhas que instrumentam `size(Via,1)`/`NI−mu`.

### 6.3 Código que sobra (próxima sessão)
1. **A11 nos 3 classificadores MATLAB** (b4, c217, e74) — o mecanismo está no
   harness Python; falta o gêmeo MATLAB.
2. **`params` no ⑤** dos writers MATLAB que ainda não têm (o c217 já entrou).
3. **V3**: `cards/INDEX`, SPEC L.8 do e74 pós-fix, D7/`iteration_seed` na SPEC
   §D62 — **a SPEC é território da torre (RI-12)**, por isso não a editei.
4. **`scripts/tabela42.py:37`**: o filtro DI-40 está CORRETO para o censo da s42
   e ERRADO para o M8 — precisa virar condicional por semente.

## 7. Como verificar tudo

```bash
PY=/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python
$PY -m unittest discover -s tests -t .                       # 587, 0 falhas
$PY scripts/preflight.py                                     # lacres + âncoras + forasteiros
$PY scripts/gates_proveniencia.py --varredura --historico    # G-1..G-4, G-7, B-15
$PY scripts/naoperturbacao.py c122 MMF1 0 --par              # G-6 (par de runs)
$PY scripts/content_hash.py <origem> <destino>               # G-9
```
