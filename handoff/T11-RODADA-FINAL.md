# T11 · HANDOFF SUPREMO DA RODADA FINAL — 2026-07-29/30

> **Para quem abre este arquivo primeiro.** Ele é o registro COMPLETO da sessão
> de refinamento final do código antes do disparo de ~18.291 h-core. Contém o
> que foi feito, o que **deu errado**, o que se aprendeu, o estado exato de cada
> validação e **as decisões que ainda são do autor**. Os outros documentos são
> recortes: `T11_STATUS.md` (item a item, com hash), `T11-CONFORMIDADE.md` (os
> 24 configs), `REGISTRO_DECISOES_IMPLEMENTACAO.md` PARTES A36/A37/A38 (o
> ledger permanente), `T11-V1-verificacoes-dirigidas.md` (VD-b1/VD-b3).
>
> ⚠ `handoff/T11-FINAL.md` é uma FOTOGRAFIA de 30/07 08:27 e **está obsoleto** —
> ele mesmo traz o aviso no topo. Este arquivo o supersede.

---

## 0. VEREDITO EM UMA PÁGINA

### A etapa está 100% pronta?

**NÃO — e a distinção importa.** O **código** está pronto e congelado; a
**validação** está a dois vereditos de fechar; a **fidelidade** nunca foi
verificada e é trabalho do autor (D97).

| camada | estado | confiança |
|---|---|---|
| Código do harness/gates/instrumentação | ✅ **congelado** em `25e95b4`(→`67b8541`) | alta |
| Encanamento (roda, grava, rastreia) | ✅ **24/24 configs** com smoke + portões | 85% |
| Invariante §3.1 (sonda não perturba) | ✅ **19/19 configs**, 0 perturbaram | alta |
| Rito de teto (truncar COM dado) | 🟡 **em curso** — veredito às 23:58 | — |
| Pico de RAM do `c262-batch` | 🟡 **em curso** | — |
| **Fidelidade de cada algoritmo ao artigo** | ⚪ **NUNCA VERIFICADA** — é D97, manual, do autor | **25%** |
| **Correção numérica dos resultados** | ⚪ **nenhum teste compara VALOR** — os gates conferem ESTRUTURA | **20%** |
| Camada de análise (R4) | ⚪ **não existe** (`cards/INDEX`: `R4-analise` ⬜) | 0% |

> **Confiança de que o código atual produz resultados 100% válidos para
> publicação em revista de primeira linha: ~45%.** O número não é sobre o
> encanamento — esse está bom. É sobre fidelidade e análise, que estão fora do
> que esta sessão fez. Ver §8.

### Que código foi rodado para validar, e com que resultado

| verificação | comando | resultado |
|---|---|---|
| Suíte unitária | `python -m unittest discover -s tests -t .` | **627 testes, 0 falhas** (era 394 no início) |
| Lacres + âncoras | `python scripts/preflight.py` | **11/11 repos**, 14 âncoras APLICADO |
| Proveniência (censo) | `python scripts/gates_proveniencia.py --varredura --historico` | **744 células** varridas |
| Não-perturbação §3.1 | `python scripts/naoperturbacao.py <alg> --par` (10 Python) + pares MATLAB manuais (9) | **19/19 BIT-IDÊNTICAS** |
| Smoke por config | 11 Python em tempdir + 13 MATLAB em `/tmp/smoke_matlab` | **24/24**, `ok=N skipped=0` |
| Contrato §6.1 | `gates_de_proveniencia(..., modo='campanha')` sobre dado FRESCO | **24/24 VERDE** |
| Staleness | `python scripts/staleness.py` | **STALE: 0** |
| Prova I-05 (b5 vendorizado) | 2 worktrees isolados, ①③⑦ comparadas | **BYTE-IDÊNTICAS** |
| Suítes `*_SLOW` (4) | `C122_SLOW=1 …`, idem c149/e81/c311 | **4/4 OK** — incl. determinismo bit-a-bit |
| Kill-test do checkpoint | na suíte | verde, **com controle** |

---

## 1. PLACAR DA SESSÃO

| | |
|---|---|
| Commits | **56** (`fbf8df8` … `67b8541`) |
| Código | **89 arquivos · +11.673 / −295 linhas** |
| Suíte | **394 → 627 testes**, 0 falhas (+233) |
| Erratas registradas | **15** — todas MEDIDAS, nenhuma inferida |
| Configs com smoke | **24/24** |
| Configs com §3.1 provado | **19/19** (5 pisos sem sonda: não-aplicável) |
| Achados da auditoria adversarial | **78** (4 CRÍTICO · 18 ALTO · 33 MÉDIO · 15 BAIXO · 8 COSMÉTICO) |
| Achados tratados | **22** (todos os CRÍTICO + ALTO) |

---

## 2. A TABELA SUPREMA — tudo que foi feito, em ordem

### FASE G · globais habilitadoras (destravam todos os configs de uma vez)

| item | o que entrou | prova/medida |
|---|---|---|
| **G1** | ⑥ blindado: `RunJaFechado` (B-01) + 1 linha = 1 `os.write` com `O_APPEND` + `flock` (B-11), nos DOIS writers | ERRATA 1/2: o splice NÃO estava no header (512 B) — as 49 malformadas são `b1_gen`/`sonda` |
| **G2** | despachante honesto: skip não abre o ⑥ (B-02) · `NO_RETRY` (B-16) · ⑤ do aborto com a célula (I-10) · revogação DI-40 | 3 padrões de `NO_RETRY` MEDIDOS, não supostos |
| **G3** | `campanha_id` schema v2 (B-03) · `limpar_celula` no `--force` (OP-6) · fallback-footer (O-21) | `is_run_done` exige o carimbo ANTES de tocar camada |
| **G4** | espelho resiliente: `mirror_evidencia` no aborto (B-09) · `if_generation_match=0` + poda só após md5 (B-10) | teste hermético com cliente GCS falso |
| **G5** | truncamento-com-dado (teto ELAPSED-only) + **checkpoint atômico** (K=25 its OU 30 min) em 8 runners + kill-test | `fe_final` do ⑤ declarado **PISO** — as 5 escritas são atômicas uma a uma, o ⑤ vai por último |
| **G6** | 9 gates + 4 artefatos normativos + `content_hash.py` + par de runs (G-6) + suíte hermética + guarda anti-escrita + 9 drivers no git | ERRATA 3: o critério literal do B-12 daria **304 falso-positivos**; o discriminador é o **HOST** ⇒ 58 reais |
| **G6b** | **gêmeo MATLAB da flag** `UA_DD_SAEA_SONDA_OFF` — o gate sai de **10 para 19 configs** | "desarmar, não sumir": `build_manifest` lê `snd.n_blocos` direto, e `[].n_blocos` é erro |
| **G7** | cronômetro no portão de avaliação (I-02, com NULL) · `repo_hash` nos 2 stacks (I-09) | `tempo_aval_real_s` pode ser NULL — "não medi" ≠ "custou zero" |

### FASE A · por algoritmo

| item | config | o que entrou | número que prova |
|---|---|---|---|
| **A1** | c154 | `params` ⑤ · regra I-12 (ordem da ③) · `executable` ⑤ | I-12 fecha **1.200/1.200 blocos** |
| **A2** | c122 | `n_ref` REAL · `ref_ids` · regra-do-rótulo · `y_treino_dist` | **n_ref=21 (=11D−1) no g=1 × 11 (=MU) no g≥2** |
| **A3** | família b5 | `p_wrong_stats`/`n_substituicoes`/`flag_vetores_degenerados` (patch vendorizado) · `params` · granularidade ③ · **`amplitude` float64** | era **0/30.165** eventos · prova I-05 ①③⑦ byte-idênticas |
| **A4** | c262 | 8+2 hp da acqf (`ACQF_HP` fonte única) · `params` · guard de `fit_retries` | 24 células sem `params` |
| **A5** | e103 | `tempo_geracao_s` | era o ÚNICO config sem |
| **A6** | sobol_batch + nsga3 | `n_front1` pelo `minimo_comum_di10` · string `geracoes_derivadas` | ERRATA 5: a fórmula do plano acerta **0/112** ⇒ EMERGENTE |
| **A7** | b4 | regra-do-rótulo + glossário p0/p1 + `y_treino_dist` | trocar p0/p1 derruba **6.268 → 1.252** |
| **A8** | e74 | **FIX DI-45** + âncora + re-lacre | argmax inerte em **87,76%** dos ciclos |
| **A9** | c217 | `pmid_ids` · `y_treino_dist` · `params` · **regra-do-rótulo** | identidade era **0/25** células · ⚠ era CARIMBO FALSO (§4) |
| **A10** | c311/treed | guard de tier ANTES do import · aviso `n_sigma_valido` | σ-NaN mediano **90,3%** no big |
| **A11** | 4 classificadores | sonda ESTRATIFICADA — Python (c122) **+ gêmeo MATLAB** (b4/c217/e74) | prevalência **7,4% × 0,4%** = **18×** mais positivos |

### FASE V · verificações

| item | resultado |
|---|---|
| **V1** | VD-b1 e VD-b3, forense read-only. **Ambos FECHADOS sem mudar código** — ver §4/ERRATA 10 |
| **V2** | re-runs da s42 — **do autor**, ainda pendente |
| **V3** | lote de docs RE-MEDIDO (PARTES A36/A37) · regras **11 e 12** novas no CONTRATO · `cards/INDEX` destravado |

### FASE C0 · a auditoria adversarial e as correções (o bloco não planejado)

| achado | classe | correção |
|---|---|---|
| **Portão dava VERDE com INCONCLUSIVO** | 🔴 CRÍT | `0`=verde · `1`=vermelho · `2`=inconclusivo. **É o portão que autoriza o disparo** |
| **Guarda G-8 cega à raiz** de `data/experiments` | 🔴 CRÍT | a raiz entrou na impressão; `test_drivers_b12` escrevia em **produção a cada suíte** |
| **G-1 sem controle-positivo** (a quimera sumiu do corpus) | 🔴 CRÍT | quimera **sintética** + controle simétrico ⇒ o gate discrimina |
| **G-1 explodia** em parquet ilegível e derrubava o censo | 🟠 ALTO | vira INCONCLUSIVO com o tipo do erro |
| **G-3 passava calado** com roster vazio (13 configs) | 🟠 ALTO | MATLAB com `executable` = FALTA; alg sem roster = aviso explícito |
| **G-7 creditava `rec` errado** — 21 tipos contavam como geração | 🟠 ALTO | whitelist POR CONFIG. Efeito: **383 → 432 vermelhos** no censo |
| **G-7 absolvia o ⑤** quando o ⑥ não tinha evento | 🟠 ALTO | ⑤ sempre auditado — `treed_media` escapava 100% |
| **PlatEMO sem lacre** — 12 arquivos invisíveis | 🟠 ALTO | repo ANINHADO: o `git status` do repo-mãe não o vê e o HEAD não muda com a árvore suja. Content-hash resolve |
| **botorch sem pin conferido** (11º repo) | 🟠 ALTO | versão pypi comparada |
| **`portao.py` sem `--historico`** | 🟠 ALTO | pintava as 666 células da s42 de vermelho por campo que elas não podiam ter |
| **Suíte não importava em py3.7/py3.8** | 🟠 ALTO | 13 skips prometiam cobertura que nem chegava ao import |
| **`*_SLOW` nunca rodavam** | 🟠 ALTO | rodados: **4/4 OK** (c122 23 testes/193 s · c149 20/976 s · e81 21/37 s · c311 14/102 s) |
| **A9/c217 · carimbo falso** | 🟠 ALTO | `[x]` DEFINITIVO sem a regra-do-rótulo — ver §4 |
| **A3/I-05 item 4 nunca implementado** | 🟠 ALTO | metade era ERRATA 13; a outra (wrapper do `adapt`) **declarada**, não feita |
| **5 pendências fantasma** no `T11_STATUS` | 🟠 ALTO | roteadas como "decisão do autor" 6 commits depois de resolvidas |
| **3 docs obsoletos** | 🟠 ALTO | `T11-FINAL`, A36 sem ERRATA 10, `4796a03` sem registro |
| **b1/WFG1 perdeu 39 de 413 gerações** | 🟠 ALTO | **do autor** — o V2 já re-roda essa célula |
| **NÃO-APLICÁVEL × NÃO-AFERÍVEL colapsados** | 🟠 ALTO | separados: `⚪` não bloqueia, `⛔` sai 2 |

### FASE T · os testes finais

| item | resultado |
|---|---|
| **T1** · 6 pares G-6 restantes (Python) | ✅ **6/6 BIT-IDÊNTICAS**, com os MESMOS hashes das provas anteriores |
| **T2** · re-smoke dos configs tocados | ✅ 3/3 |
| **T3** · suíte final | ✅ **627, 0 falhas** |
| **T5** · re-auditoria de staleness | ✅ **STALE: 0** (achou e fechou o `b5m`) |
| **G-6 MATLAB** (runs do autor) | ✅ **9/9 BIT-IDÊNTICAS** — b1, b3, b4, c141, c217, c238, e7, e74, **e103** |

---

## 3. AS 15 ERRATAS — o documento dizia × o dado diz

Todas nasceram da regra *"verifique antes de escrever"*. **Cada uma teria virado
trabalho errado.** Cinco delas (6, 7, 8, 12, 14) são **falso-positivo de gate
que eu mesmo escrevi**.

| # | fonte | dizia | é |
|---|---|---|---|
| 1 | PLANO/B-11 | splice nas linhas de header/sigma_dict | header = **512 B**; as 49 malformadas são `b1_gen`/`sonda` |
| 2 | PLANO/B-11 | "`b1_instrument.m`: 2 handles" | **não existe** 2º handle |
| 3 | PLANO/B-12 | abortar se venv ≠ o da máquina | daria **304 falso-positivos**; o discriminador é o **HOST** ⇒ 58 |
| 4 | aceitação | re-gate = 1 quimera + **34** anômalas | 1 ✔ + **15**; as outras 21 são as que o **B-15 manda não acusar** |
| 5 | I-13 | `geracoes_derivadas = ⌈…⌉` | acerta **0/112**; `floor(…)` 103/112 ⇒ **EMERGENTE** |
| 6 | meu gate | `mll_final`/`loss_treino` ausentes | **ANINHADOS** em `modelo_hp` — o gate aferia POSIÇÃO, não PRESENÇA |
| 7 | §6.1 | e103 sem `margem_3sigma` | grava `margem_3sigma_stats`, **mais rico** |
| 8 | §6.1 | c154 deve ter `n_baseline` | o `sigma_dict` do runner já dizia "AUSENTE POR DESENHO" |
| 9 | **eu** | o acumulador P_wrong causa "2,5× de lentidão" | microbenchmark: **30,5 µs → 7,1 µs**/chamada ⇒ ~1,9 s/run, **não 23 min**. A reescrita foi **REVERTIDA** |
| 10 | **eu (V1)** | VD-b1 é 🔴, mesma classe do DI-45 | **INERTE em ~93,9%** dos ciclos, e a SPEC já o tem como **🟠 IMPL → CÓDIGO**. Reabri decisão FECHADA |
| 11 | **eu** | 7 configs sem `params` no ⑤ | tabela lida da **s42, que é PRÉ-T11**. Hoje: **9 de 10** gravam |
| 12 | meu artefato | `p_wrong_stats` exigido de b5r e moead_media | só o **b5m** passa pelo `ProbMOEAD_select`. E o gate era **INVERTIDO**: ficava vermelho quando a ablação estava CERTA |
| 13 | varredura | "amplitude float64 nunca implementada" | já estava em `norma_min`/`norma_max` — mesma armadilha da 6 |
| 14 | meu artefato | e103 deve ter `tempo_busca_s`/`tempo_fit_s` | **0 de 5.148** eventos os têm. Offline com fit ÚNICO |
| 15 | **eu** | `n_desalinhado → ~0` é a prova do DI-45 | mede **OUTRO sítio** (`Local_infill.m`), deliberadamente não-corrigido. A resposta estava **a uma linha do campo** |

---

## 4. O QUE DEU ERRADO — e o que se aprendeu

> Esta seção existe porque um handoff que só conta acertos é inútil. **Cada erro
> abaixo custou tempo e todos foram achados por VERIFICAÇÃO, não por revisão.**

### 4.1 · Erros de método (os que mais custaram)

| erro | o que aconteceu | lição |
|---|---|---|
| **Paralelizei com THREADS** | 10 smokes num `ThreadPoolExecutor`. Tempdirs isolados, **estado global do torch não**: `c122` põe `float32`, `botorch_harness` põe `float64`, e um sobrescreveu o outro no meio do forward. **5 de 10 resultados eram lixo**, e o `c122` "quebrou" sem ter bug | O `envs.json` já cravava: *"dispatch: subprocess no python do venv-alvo (D79); 1 run = 1 core"*. **Processo, nunca thread** |
| **Copiei comando de CAMPANHA para fazer SMOKE** | `dataRoot`/`data_root` têm produção como default nos DOIS stacks. Os 13 smokes MATLAB deram `skipped=6/4/1/1`: **zero executados**, e o `nohup` engoliu o log | Smoke NUNCA aponta para `data/`. Virou §X do RUNBOOK |
| **Commitei com um job de background trocando arquivo tracked** | A prova do I-05 alternava o arquivo vendorizado; no instante do `git add` o lado "SEM" estava no disco ⇒ o git viu "nada mudou". **O HEAD ficou com leitor novo + acumulador antigo e não rodava b5m** | Nunca trocar arquivo versionado em background. A prova final usa **worktrees isolados** |
| **Ancorei controle de teste em referência MÓVEL** | `HEAD~1` e depois `HEAD`. Dois commits depois o "controle" já continha a correção e **passava**, dando falso-verde. **Errei DUAS vezes**, a segunda no commit onde documentei a lição | Controle ancora em **commit fixo**, sempre |
| **Reportei "relançado" sem olhar a saída** | Os 5 smokes morreram em 1 s por bug de aspas no loop zsh. `nohup ... &` não mostra erro | Conferir o ARRANQUE, não o comando |
| **Afirmei sem ler o que estava ao lado** | "`n_desalinhado → ~0` é a prova do DI-45" — repetido 3×. O comentário `% fix opcional NAO aplicado` estava **na mesma linha do campo** | ERRATA 15 |
| **Li dado VELHO como se fosse o de hoje** | A s42 é PRÉ-T11. Acusei 7 configs sem `params` (eram 1) e 4 configs com campo faltando (era 1) | ERRATAs 11 e 14 |
| **Quase movi 58 células de produção** | Listei "limpar os forasteiros" como tarefa minha. É **decisão operacional do autor** sobre dado real | O autor barrou. Ficam |

### 4.2 · O que se aprendeu sobre gates (e virou código)

1. **Um gate que nunca reprova é decorativo.** O `preflight` RECALCULAVA o content-hash e imprimia o valor recalculado — que por construção sempre bate. Nunca comparava. Todo gate novo desta sessão veio com **controle medido**: a checagem rodada contra a versão ANTERIOR tem de REPROVAR.
2. **INCONCLUSIVO tem duas espécies.** "Não-aplicável por desenho" (permanente, ok) e "não consegui aferir" (problema). Colapsá-las esconde um parquet corrompido atrás de nove pisos sem sonda.
3. **⑥ e ⑤ são camadas INDEPENDENTES.** O silêncio de uma não perdoa a outra — dois sítios do G-7 absolviam o manifesto inteiro.
4. **Teste stale não vale nada.** Nasceu daí o `scripts/staleness.py`, que cruza fecho de imports × `git log` × hora do teste. Achou **9 pares G-6 stale** e depois o `b5m`.
5. **Verificar o mecanismo, não só o hash.** Nos pares G-6, o hash bater é fraco sozinho — um desarme que nunca disparasse daria o mesmo. Os **três sinais** (⑤ `desligada=true`, `n_blocos`→0, ③ ENCOLHENDO) provam que a sonda RODOU e mesmo assim não mexeu na busca.

### 4.3 · O que se fez certo

- **Nenhum smoke escreveu em produção.** Verificado por duas medidas independentes: **0 manifestos com `campanha_id`** (obrigatório desde o G3) e **0 arquivos tocados** em `data/experiments`.
- **Toda errata é medida.** Nenhuma foi inferida de leitura.
- **A prova I-05 foi refeita 3× até ficar correta** — as duas primeiras comparavam o lado errado.
- **A auditoria adversarial foi contra o próprio trabalho** e achou 4 CRÍTICOS que a revisão normal não pegaria.

---

## 5. ESTADO DAS VALIDAÇÕES — os 24 configs

| # | config | stack | smoke | portões | §3.1 (par G-6) |
|---|---|---|---|---|---|
| 1 | `b1` | MATLAB | ✅ | ✅ 6/6 | ✅ `4d81d858eaeb1729` |
| 2 | `b3` | MATLAB | ✅ | ✅ 6/6 | ✅ `760941d23f75eb70` |
| 3 | `b4` | MATLAB | ✅ | ✅ 6/6 | ✅ `2404320fa6f276b9` |
| 4 | `b5m` | Python | ✅ 2.506 s | ✅ 6/6 | ✅ `bcda99b31dfb2c35` |
| 5 | `b5r` | Python | ✅ 132 s | ⚪ G-1 n/a | ✅ `2d217703d7086d0f` |
| 6 | `c122` | Python | ✅ 50 s | ✅ 6/6 | ✅ `be06b54124e9c100` |
| 7 | `c141` | MATLAB | ✅ | ✅ 6/6 | ✅ `d7f20cd0c4648c3f` |
| 8 | `c149` | Python | ✅ 251 s | ✅ 6/6 | ✅ |
| 9 | `c154` | Python | ✅ 98 s | ✅ 6/6 | ✅ `eadf899dddf5b4d5` |
| 10 | `c217` | MATLAB | ✅ | ✅ 6/6 | ✅ `868a15c02c09610f` |
| 11 | `c238` | MATLAB | ✅ | ✅ 6/6 | ✅ `43f533269741c82f` |
| 12 | `c262` | Python | ✅ 35 s | ✅ 6/6 | ✅ `75c52d8b082b8093` |
| 13 | `c311` | Python | ✅ 26 s | ⚪ G-1 n/a | ✅ `07530706e23cdddd` |
| 14 | `e103` | MATLAB | ✅ | ✅ 6/6 | ✅ `a94d2766d257185a` |
| 15 | `e7` | MATLAB | ✅ | ✅ 6/6 | ✅ `1e1060eeaae5fa49` |
| 16 | `e74` | MATLAB | ✅ ×3 | ✅ 6/6 | ✅ `fc9ced7a6f4671ef` |
| 17 | `e81` | Python | ✅ 24 s | ✅ 6/6 | ✅ `b9525753d5f17862` |
| 18 | `moead` | MATLAB | ✅ | ⚪ G-1 n/a | ⚪ sem sonda |
| 19 | `moead_media` | Python | ✅ 35 s | ✅ 6/6 | ✅ `8e690c81e3f095a5` |
| 20 | `nsga2` | MATLAB | ✅ | ⚪ G-1 n/a | ⚪ sem sonda |
| 21 | `nsga3` | MATLAB | ✅ | ⚪ G-1 n/a | ⚪ sem sonda |
| 22 | `smsemoa` | MATLAB | ✅ | ⚪ G-1 n/a | ⚪ sem sonda |
| 23 | `sobol_batch` | Python | ✅ 1,5 s | ⚪ G-1 n/a | ⚪ sem sonda |
| 24 | `treed_media` | Python | ✅ 28 s | ⚪ G-1,G-7 n/a | ✅ `dd03ee216118d017` |

**Os `⚪` são NÃO-APLICÁVEL POR DESENHO, não pendência.** Medido: a ③ desses
configs tem `real_solution_id` **100% nula** (b5r 0/57.997 · c311 0/86.240 ·
moead_media 0/60.005 · treed_media 0/69.874) ou **0 linhas** (os 4 pisos +
sobol_batch, que não têm surrogate). O G-1 confere a identidade ③↔① das linhas
MARCADAS — sem marca, não há o que conferir, hoje nem nunca.

### O que o smoke prova e o que NÃO prova

**Prova:** roda ponta a ponta, escreve as camadas contratadas, ⑤ com
`campanha_id`/`repo_hash`/schema v2, ⑥ com header+footer sem linha malformada,
proveniência coerente. **É verificação de ENCANAMENTO.**

**NÃO prova:** correção numérica, fidelidade ao artigo, que a busca faz o que
deveria. **Um algoritmo pode estar profundamente errado e passar nos 6 portões.**

---

## 6. DECISÕES EM ABERTO — 🚨 A TORRE PRECISA LEVANTAR ESTAS COM O AUTOR

> Nenhuma bloqueia o trabalho técnico. Todas mudam o que vai (ou não) para a
> dissertação. **A torre deve trazê-las à mesa antes do disparo do M8.**

### D-A · Os 56 achados residuais da auditoria
33 MÉDIO + 15 BAIXO + 8 COSMÉTICO, **nunca refutados** (a fase adversarial
processou 27 de ~156 votos antes de ser encerrada por orçamento). Um agente
cético está diagnosticando-os em `/tmp/refutacao56.md`, classificando em
FALSO_POSITIVO / SÉRIO / GATE_CEGO / OPCIONAL.
**Pergunta ao autor:** tratar os SÉRIO e GATE_CEGO agora, no M8, ou arquivar?
**Recomendação:** triagem por CONSEQUÊNCIA (o que pode gerar dado errado ou
afirmação falsa entra agora; o resto datado no handoff). Pelo histórico, 30–50%
devem ser falso-positivo.

### D-B · O wrapper do gatilho do `adapt` (A3/I-05 item 4)
**NUNCA implementado**, e o buraco não estava declarado em lugar nenhum até
2026-07-30. É cirurgia VENDORIZADA em `ReferenceVectors.adapt` ⇒ âncora nova +
re-lacre + **nova prova de não-perturbação (~90 min de b5m)**.
**Estado atual:** a cadeia A8 (`adapt` zera `values` → PBI NaN → P_wrong ≡ 0 →
zero substituições) **já é observável nas DUAS pontas** — a CAUSA em
`flag_vetores_degenerados` (com `norma_min`/`norma_max`/`amplitude`) e o EFEITO
em `p_wrong_stats` + `n_substituicoes`. O wrapper diria QUANDO o `adapt` dispara.
**O autor decidiu em 2026-07-30: NÃO FAZER.** Registrado aqui para que a decisão
não se perca — se o congelamento aparecer no M8 e o instante exato importar,
revisitar.

### D-C · VD-b1 — o torneio do b1 (RESOLVIDO, mas registre-se o porquê)
**NADA MUDA.** A SPEC já o classifica como **🟠 IMPL → CÓDIGO, documentado**
(`SPEC:434` cita "torneio do b1" pelo nome; `SPEC:500` o lista entre as
divergências periféricas mantidas no CÓDIGO — D30/D47) e o `EvolALG.m:9-10`
registra a decisão anterior: *"o bug do torneio (:16) fica (CODIGO K.3)"*.
Esta sessão o marcou 🔴 por engano, disparou um D81 sem motivo e **reabriu
decisão fechada** — ver ERRATA 10. O que fica de útil é o NÚMERO: o torneio é
**INERTE em ~93,9% dos ciclos** (3,87% dos 87,77 M candidatos scorados), com
concentração em `BBOB_F37` (62,7%) e `BBOB_F49` (61,3%). Isso vira lastro da
classificação 🟠 que já existia.

### D-D · VD-b3 — o `Next` do `UpdataArchive` (FECHADO como forense)
🔴 estrutural: no ramo 1, `current` é posição em `Via` (vetores de referência) e
é usado para indexar `Total` (soluções). `nzero=0` em **1.619/1.619** ciclos NÃO
discrimina qual ramo rodou, porque nem `size(Via,1)` nem `NI−mu` são logados.
**O pedido de instrumentar (~2 linhas) foi RETIRADO** junto com a ERRATA 10:
medir mais para decidir algo que não está em aberto é trabalho sem destino.
**Se a torre quiser transformar isso em número no M8**, são 2 linhas read-only.

### D-E · Os 58 manifestos forasteiros — **DECIDIDO: FICAM**
Células legítimas que voltaram das VMs por rsync em 26–27/07
(`/home/jupyter/python_venvs/env_main/bin/python`): 25 `main/c122`, 25
`main/c149`, 4 `batch/c149`, 4 `batch/sobol_batch`. O `preflight` as marca como
pendência e sai ≠ 0 — **é ruído conhecido, não impedimento**. O efeito prático é
que a esteira idempotente PULA essas células num disparo local.
**O autor decidiu em 2026-07-30: manter intocadas.**

### D-F · `b1/WFG1` perdeu 39 de 413 gerações do ⑥
Dano REAL e verificado: 930 linhas, **49 malformadas**, 374 eventos `b1_gen`
para uma geração máxima de 413 — bloco contíguo perdido a partir da 358. As
DUAS cópias locais (`data/experiments` e `resultados_experimentos`) estão
danificadas do mesmo jeito.
**As outras camadas estão íntegras** (⑤ `ok`, ① 681 linhas, ② 205.350, ③
854.888, ④ 443) — perdeu-se o rastro de auditoria, não o dado experimental.
A causa (splice B-11) **está corrigida** pelo G1 para runs futuros.
**Pendente:** essa célula já está na lista do V2 para re-run. **Antes disso,
conferir se o bucket GCS tem uma cópia do ⑥ anterior ao dano** — se tiver, o
re-run vira opcional.

### D-G · `UA_DD_SAEA_CAMPANHA_ID` nas 4 máquinas
**Opcional** — sem a variável, o `manifest.py` deriva `<commit-curto>_<data>`.
O que ela resolve é ter **um id ÚNICO e IGUAL** nas 4 máquinas; sem isso cada
uma deriva o seu e o `is_run_done` cruzado quebra. Comando no RUNBOOK §X.1.

### D-H · Tag + push + disparo
`t11-definitivo` (ou o nome que o autor escolher) + push + fila de infra D10.
**Esta sessão NUNCA fez push** — a regra é firme.

---

## 7. O QUE FALTA — por dono

### 🟡 Em execução nesta máquina (aguardando o relógio)

| # | item | veredito esperado | quando |
|---|---|---|---|
| 1 | **`c154/DTLZ2/s42` (D=12) · validação do teto** — `teto_s=21600` (6 h) | camadas parciais **+ ⑤ com `motivo_parada='teto_wall'`**. Se abortar SEM arquivo, o rito FALHOU | **23:58** |
| 2 | **Probe de RAM do `c262-batch` q=10** | pico de RSS → crava `--n-jobs` no RUNBOOK | ~23:30 |
| 3 | **Diagnóstico dos 56** (agente cético) | `/tmp/refutacao56.md` | — |

> **Nota de método sobre o item 1.** O teto foi posto em **6 h em vez das 12 h
> oficiais, por decisão do autor**. Para o MECANISMO é indiferente: o gatilho é
> `elapsed > teto` e o rito depois dele é o mesmo código; o valor do teto é só o
> operando da comparação. O que 6 h dá a menos é volume de dado truncado, não
> cobertura de caminho.
>
> **Nota sobre o item 2.** As duas primeiras tentativas morreram por `SIGKILL`
> (jetsam do macOS sob pressão de memória) **sem deixar número**. A terceira
> grava o pico **a cada novo máximo** (tmp+rename) — mesma doutrina do
> checkpoint do G5: estado parcial em disco para que uma morte súbita não leve
> tudo. Um pico parcial sob pressão é resultado, e é CONSERVADOR para o
> `--n-jobs` porque erra para cima.

### 🔵 Sessão de código (o que ainda é trabalho de agente)

| # | item | tempo |
|---|---|---|
| 4 | **Atualizar ESTE handoff** com os resultados do `c154` e do probe de RAM | 15 min |
| 5 | Triagem dos 56 com o diagnóstico do cético → levar as decisões ao autor | 20 min |
| 6 | Última passada: suíte + preflight + staleness + portão + `cards/INDEX` | 10 min |

### ⚪ Autor · máquina

| # | item | custo |
|---|---|---|
| 7 | **V2 · re-runs da s42** — `c311/big-mvns`, `b1/WFG1`, quimera `c149`, ⑦ do `e103`, ~29 não-ok | ~2–4 h |
| 8 | Conferir se o bucket tem o ⑥ íntegro de `b1/WFG1` (ver D-F) | ~15 min |

### 🗳 Autor · decisão
Ver **§6** — D-A (os 56) e D-H (tag+push) são as que faltam decidir.
D-B, D-E foram decididas em 2026-07-30; D-C e D-D estão fechadas.

---

## 8. CONFIANÇA — a leitura honesta para a torre

**~45%** de que o código ATUAL produza resultados 100% válidos para publicação
em revista de primeira linha. Decomposto:

| dimensão | confiança | por quê |
|---|---|---|
| Pipeline roda e entrega dado completo e rastreável | **85%** | 24/24 smokes, 19/19 §3.1, 627 testes, 11 lacres |
| Reprodutibilidade auditável por revisor | **80%** | content-hash de árvore, âncoras, DoE bit-a-bit, `campanha_id` |
| **Fidelidade de cada algoritmo ao seu artigo** | **25%** | **NUNCA verificada** — D97 diz que é manual, do autor |
| **Correção numérica** | **20%** | nenhum teste compara VALOR; os gates conferem ESTRUTURA |
| Camada de análise (R4) | **0%** | não existe |

**As sete razões do número:**
1. Fidelidade nunca foi verificada, e a SPEC §500 lista divergências
   paper×código **mantidas de propósito** no b1 (λ, subset, GA geracional, MLE
   sem restarts, o torneio).
2. Achados 🔴 conhecidos e não resolvidos: VD-b3 sem medida; 2º desalinhamento
   do e74 deliberadamente mantido.
3. A rodada-42 tem dados danificados (b1/WFG1, 1 quimera, 15 anômalas, 21 sem
   footer).
4. Validou-se **1 célula por config**; a campanha são 695 × 30 sementes — outro
   regime (concorrência, disco, memória, teto em escala).
5. 56 achados ainda não refutados.
6. **O trabalho desta sessão teve taxa de erro alta**: 15 erratas, 5 delas
   falso-positivo dos gates que a própria sessão escreveu, e **4 CRÍTICOS de
   falso-verde**. Se o código novo errou assim, não há base para supor que o
   resto do repo — de sessões anteriores — esteja melhor.
7. Já apareceu **um gate que nunca falha** (`test_cli_expoe_teto_s`, skip
   permanente auto-realizável). Onde há um, costuma haver outros.

**O que move o número:** a **validação de fidelidade da torre**, algoritmo por
algoritmo, código × artigo → **45% → ~70%**. É o maior salto disponível, e é o
que um parecerista pergunta primeiro.

---

## 9. COMO VERIFICAR TUDO

```bash
PY=/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python
cd /Users/gmello/Documents/python_repos/mestrado/ua-dd-saea

$PY -m unittest discover -s tests -t .          # 627 testes, 0 falhas
$PY scripts/preflight.py                        # 11/11 lacres · 14 âncoras
$PY scripts/staleness.py                        # STALE: 0  (exit != 0 se algum teste for anterior ao código)
$PY scripts/gates_proveniencia.py --varredura --historico   # 744 células
$PY scripts/portao.py --varredura --historico   # 0=verde · 1=vermelho · 2=NÃO-AFERÍVEL
$PY scripts/naoperturbacao.py <alg> --par       # o par §3.1 de um config PYTHON
$PY scripts/content_hash.py <origem> <destino>  # G-9
```

**Par G-6 de um config MATLAB** (o adapter Python NÃO despacha MATLAB):
```bash
MAT=/Applications/MATLAB_R2025a.app/bin/matlab
rm -rf /tmp/g6_com /tmp/g6_sem && mkdir -p /tmp/g6_com /tmp/g6_sem
for d in com sem; do for e in doe datasets sonda; do ln -s "$PWD/data/$e" /tmp/g6_$d/$e; done; done
unset UA_DD_SAEA_SONDA_OFF
$MAT -batch "experiments('algorithms',{'b1'},'problems',{'MMF1'},'seeds',42,'parallel',false,'dataRoot','/tmp/g6_com')"
export UA_DD_SAEA_SONDA_OFF=1
$MAT -batch "experiments('algorithms',{'b1'},'problems',{'MMF1'},'seeds',42,'parallel',false,'dataRoot','/tmp/g6_sem')"
unset UA_DD_SAEA_SONDA_OFF
# conferir: ⑤ com `sonda.desligada=true` e `n_blocos=0` no lado SEM · ① com o MESMO sha256
```

⚠ **Smoke NUNCA aponta para `data/`** — ver RUNBOOK §X. `dataRoot`/`data_root`
têm produção como default nos DOIS stacks.

---

## 10. MAPA DOS DOCUMENTOS

| arquivo | o que é |
|---|---|
| **`handoff/T11-RODADA-FINAL.md`** | **este** — o registro completo da sessão |
| `T11_STATUS.md` | item a item, com hash de commit e o que falta em cada |
| `handoff/T11-CONFORMIDADE.md` | os 24 configs: smoke, portões, §3.1 |
| `handoff/T11-V1-verificacoes-dirigidas.md` | VD-b1 e VD-b3, com as ERRATAS 10 |
| `REGISTRO_DECISOES_IMPLEMENTACAO.md` | ledger PERMANENTE — PARTES A36 (execução), A37 (docs re-medidos), A38 (a varredura) |
| `RUNBOOK_VALIDACAO_42.md` §X | **smoke × campanha** + `UA_DD_SAEA_CAMPANHA_ID` |
| `CONTRATO_DE_DADOS.md` | regras de leitura — **11** (dominância é lossy) e **12** (sonda estratificada) são novas |
| `handoff/T11-FINAL.md` | ⚠ **OBSOLETO** — fotografia de 30/07 08:27, com aviso no topo |
| `handoff/T11-parcial-2026-07-29.md` | o parcial da FASE G |

**Artefatos machine-readable tocados:** `contrato_61.json` (novo, G-7),
`motivos_parada.json` (novo, B-06), `mapa_termino.json` (novo, I-08),
`gabarito_camadas.json` (novo, G-4), `anchors.json` (+2 âncoras),
`repos.lock` (PlatEMO e botorch passaram a ser conferidos), `envs.json`
(+`venvs_aceitos`).

**Scripts novos:** `gates_proveniencia.py` (os 9 gates), `content_hash.py`
(G-9), `staleness.py` (o gate que não existia), `src/checkpoint.py` (G5).
