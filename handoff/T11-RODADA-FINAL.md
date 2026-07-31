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
| Rito de teto (truncar COM dado) | ✅ **APROVADO** — ver §12 | alta |
| Pico de RAM do `c262-batch` | ✅ **medido** (piso) → `--n-jobs` cravado | média |
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

| # | item | veredito | quando |
|---|---|---|---|
| 1 | **`c154/DTLZ2/s42` (D=12) · validação do teto** | ✅ **APROVADO** — §12 | fechou 00:02 |
| 2 | **Probe de RAM do `c262-batch` q=10** | ✅ **1.205 MB (piso)** → `--n-jobs` no RUNBOOK §Y | fechou |
| 3 | **Diagnóstico dos 56** (agente cético) | ✅ 6 falso-positivo · 7 sério · 9 gate-cego · 34 opcional | fechou |

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

---

## 11. OS ACHADOS TRATADOS — problema → opção escolhida

> Os 22 de maior gravidade (4 CRÍTICO + 18 ALTO) da auditoria adversarial, mais
> os achados que surgiram fora dela. Para cada um: **o que estava errado**,
> **quais eram as opções** e **por que a escolhida**.

### 🔴 CRÍTICOS — todos "falso-verde", todos do código desta campanha

#### C-1 · O portão dava VERDE com INCONCLUSIVO
**Problema.** `portao.py:181` só colhia `ok is False` em `vermelhos`;
INCONCLUSIVO (`ok is None`) ficava de fora, e `return 0 if not vermelhos else 1`
imprimia **"VERDE"**. A doutrina B-07 — *inconclusivo nunca conta como verde* —
valia só para o EMOJI. **E este é o portão que autoriza o disparo das 695
células.**
**Opções.** (a) tratar inconclusivo como vermelho (exit 1); (b) manter exit 0 e
só destacar no texto; (c) **código de saída próprio**.
**Escolhida: (c)** — `0`=verde · `1`=vermelho · `2`=inconclusivo. Colapsar
"reprovou" e "não consegui medir" foi o que criou o falso-verde; quem chama
precisa poder tratá-los diferente. A (a) tornaria o portão permanentemente
vermelho por causa de configs não-aplicáveis — o caminho conhecido para um gate
ser ignorado.

#### C-2 · A guarda G-8 era cega à raiz de `data/experiments`
**Problema.** O `os.walk` estatava os FILHOS e **nunca o diretório-raiz**. Uma
subpasta que nasce e morre não muda filho nenhum — muda o mtime da RAIZ. Efeito
real: `test_drivers_b12` criava `data/experiments/_teste_b12` **na produção a
cada execução da suíte**, com a guarda verde. Escrita em `data/` é proibição
absoluta da casa.
**Opções.** (a) só consertar o teste; (b) só consertar a guarda; (c) **os dois**.
**Escolhida: (c).** Consertar só o teste deixaria a guarda cega para o próximo;
consertar só a guarda deixaria a escrita acontecendo. E o conserto **se provou
sozinho**: ao fechar o ponto cego, a guarda passou a acusar o **próprio controle
dela**, que também plantava arquivo na produção. Os dois foram hermetizados, e
entrou `test_a_impressao_reage_a_mudanca_SO_NA_RAIZ`.

#### C-3 · O G-1 não tinha controle-positivo
**Problema.** O critério de aceitação da campanha é *"re-gate ⇒ exatamente 1
quimera"*. Medido: a varredura devolve **0 quimeras**, e gatear
`batch/c149/ZDT4/s42` (o arquivo existe, 17 MB) dá **VERDE**. Sem o
controle-positivo não havia evidência nenhuma de que o G-1 soubesse reprovar.
**Opções.** (a) achar a quimera real (é item do autor, V2/T11-D2); (b) declarar
o gate não-provado; (c) **construir uma quimera SINTÉTICA**.
**Escolhida: (c)** + o controle simétrico (par coerente tem de PASSAR, senão um
gate que reprova tudo passaria no primeiro). Não substitui achar a real —
garante que, quando ela aparecer, o gate a reconhece.

#### C-4 · O G-1 explodia e levava o censo junto
**Problema.** `pq.ParquetFile(...)` estava fora de qualquer `try` que pegasse
erro de leitura. Um ③ de 0 byte levantava e **derrubava a varredura inteira com
traceback** — as células seguintes nem eram gateadas.
**Opções.** (a) reprovar a célula; (b) **INCONCLUSIVO com o tipo do erro**.
**Escolhida: (b).** Ilegível não é o mesmo que errado — e gate que EXPLODE é
pior que gate vermelho: o vermelho você vê, a explosão some com o resto do censo.

### 🟠 ALTOS

| # | problema | opções | escolhida |
|---|---|---|---|
| A-1 | **G-3 passava calado** com roster vazio: `if exe and roster` caía no `elif not exe` e nenhuma checagem acontecia. Um `env.executable` INVENTADO passava verde em **13 dos 24** configs | (a) sempre reprovar sem roster; (b) **distinguir MATLAB de alg desconhecido** | **(b)** — um ⑤ do stack MATLAB que TRAZ `executable` é anomalia (não pode ter nascido no stack que declara) ⇒ FALTA; alg sem roster não é aferível ⇒ AVISO explícito. O elenco MATLAB sai do `envs.json`, nunca hardcoded |
| A-2 | **G-7 creditava `rec` errado**: blacklist de 8 nomes ⇒ **21 tipos** contavam como evento de geração (`decision` 166.962, `fit` 17.800, `optimize_acqf_warning`…). Chaves de um AVISO satisfaziam o contrato | (a) ampliar a blacklist; (b) **whitelist POR CONFIG derivada do dado** | **(b)** — a blacklist precisa ser atualizada a cada `rec` novo (o `sonda_estratificada` que esta sessão criou já entrava na conta). A whitelist é `{alg}_gen` no MATLAB, `decision` no Python, medida em `rec × config`. Efeito: **383 → 432 vermelhos** — o gate ficou honesto, não mais severo |
| A-3 | **G-7 absolvia o ⑤** quando o ⑥ não tinha evento: `if not n_eventos: return None` saía antes de olhar o manifesto. `treed_media` escapava 100% de params/sigma_dict/timing/doe_hash | (a) manter; (b) **auditar o ⑤ sempre** | **(b)** — ⑥ e ⑤ são camadas INDEPENDENTES do contrato; o silêncio de uma não perdoa a outra. Sem evento no ⑥ ⇒ INCONCLUSIVO se o ⑤ está completo, VERMELHO se falta chave |
| A-4 | **PlatEMO sem lacre**: o `dir_map` tinha 9 dos 11 repos do lock. Pior — o PlatEMO tem `.git` PRÓPRIO e ninguém commita nele, então os **12 arquivos patchados** vivem como working-tree changes e o HEAD continua `b686ca2` com a árvore suja. O `git status` do repo-mãe também não os vê (repo aninhado). **Invisível dos dois lados** | (a) commitar no repo aninhado; (b) **content-hash da árvore** | **(b)** — o hash mede o DISCO, com os patches. Commitar no aninhado mudaria o pin e exigiria coordenação com o upstream. O HEAD passou a ser COMPARADO com o pin (antes era só sobrescrito) |
| A-5 | **botorch sem pin conferido** (11º repo) | (a) ignorar (não é árvore); (b) **conferir a versão pypi** | **(b)** — `pin_kind: pypi` não tem o que hashear, mas a VERSÃO INSTALADA é aferível. Sem isso o "0.18.1" era texto que ninguém lia, e um upgrade silencioso passaria (c154/c262 dependem dele) |
| A-6 | **`portao.py` sem `--historico`**: pintava as 666 células da s42 de vermelho por falta de `campanha_id`/`repo_hash` — campos do B-03, desta campanha, que um ⑤ v1 não podia ter | (a) relaxar o gate; (b) **expor o modo que já existia** | **(b)** — o `gates_proveniencia` já tinha os dois modos desde o G6; o portão é que não os expunha. Medido: `main/c122/ZDT1/s42` sai REPROVADO sem a flag e VERDE com ela |
| A-7 | **Suíte não importava em py3.7/py3.8** — os venvs de 13 `skipUnless`. `tuple[int,str]` é py3.9+ e `str \| None` é py3.10+ (este introduzido HOJE, por mim) | (a) `typing.Optional`; (b) **`from __future__ import annotations`** | **(b)** — uma linha, anotações lazy, py3.7+. E entrou `test_zy_portabilidade_venvs.py`: um teste que só roda no intérprete mais novo **não vê regressão de portabilidade** |
| A-8 | **15 testes `*_SLOW` nunca rodavam** — carregam o invariante §3.1 e o determinismo bit-a-bit | (a) ligar por padrão; (b) **rodar agora e registrar**; (c) declarar | **(b)** — medido: 3 min cada, não caros, só desligados. **4/4 OK** (c122 23/193 s · c149 20/976 s · e81 21/37 s · c311 14/102 s). Ligar por padrão encareceria a suíte de 90 s para ~20 min |
| A-9 | **A9/c217 · CARIMBO FALSO**: `[x]` DEFINITIVO e o título do commit dizia "b4 e c217 (regra do rótulo)", mas **só o b4 recebeu**. Sem ela a ③ do c217 é "leitura proibida" pela regra 3 do R4 | (a) desmarcar; (b) **escrever a regra** | **(b)** — a regra ESTÁ no plano do A9. E ela não é a do b4: o c217 é par-a-par **POSICIONAL E CÍCLICO** (`RBFNNPC.m:61`). Escrevi a fórmula ERRADA na 1ª vez (off-by-one 1-based→0-based) e peguei simulando o laço |
| A-10 | **A3/I-05 item 4 nunca implementado** | (a) implementar; (b) **metade era falso-positivo + declarar a outra** | **(b)** — a "amplitude float64" JÁ existia em `norma_min`/`norma_max` (ERRATA 13, mesma armadilha da 6); o wrapper do `adapt` nunca existiu e foi **declarado**, não feito (cirurgia vendorizada + 90 min de prova; a cadeia A8 já é observável nas duas pontas) |
| A-11 | **5 pendências fantasma** roteadas como "decisão do autor" 6 commits depois de resolvidas, e uma **bloqueava o carimbo do c154** | — | corrigido com o desfecho de cada: 3 eram falso-positivo do gate (ERRATAs 6/7/8), 2 foram implementadas |
| A-12 | **3 documentos obsoletos**: `T11-FINAL` se dizia FINAL com 11 commits depois; A36 mantinha o VD-b1 como 🔴 sem a ERRATA 10; `4796a03` tocou 5 arquivos de código **sem uma linha** em documento nenhum | (a) reescrever; (b) **aviso datado no topo + PARTE A38** | **(b)** — reescrever apagaria o histórico; o aviso preserva a fotografia e aponta a fonte viva |
| A-13 | **b1/WFG1 perdeu 39 de 413 gerações** por splice (B-11) | — | **do autor** — as outras camadas estão íntegras, a causa está corrigida pelo G1, e a célula já está no V2. Ação: conferir o bucket antes do re-run |
| A-14 | **NÃO-APLICÁVEL × NÃO-AFERÍVEL colapsados** no mesmo ⚠ | (a) enum (quebra a API); (b) **marca textual + classificador** | **(b)** — a API `(bool\|None, str)` está em uso pelo portão, pelo CLI e por 30+ testes. `MARCA_NAO_APLICAVEL`/`MARCA_NAO_AFERIVEL` + `especie_do_none()` padronizam o que já era convenção de redação, com teste. E o conserto expôs um terceiro sítio: **`⑥ ausente` absolvia o ⑤** |

---

## 12. OS DOIS VEREDITOS FINAIS

### 12.1 · Rito de teto — **APROVADO**

`main/c154/DTLZ2/s42`, a **única** célula D≥12 do grid (`maxfe=371` ⇒ `31D−1`
com D=12; na rodada-42 ela levou **14,6 h** e terminou `ok`).

Teto de **6 h** em vez das 12 h oficiais, por decisão do autor. **Para o
mecanismo é indiferente:** o gatilho é `elapsed > teto` e o rito depois dele é
o mesmo código — o valor do teto é só o operando da comparação. O que 6 h dá a
menos é volume de dado truncado, não cobertura de caminho.

| | |
|---|---|
| Wall | **21.835 s** = 6h03 — disparou em 21.600 s e gastou **235 s escrevendo** |
| Saída do processo | **`rc=0`** — encerramento LIMPO, não crash |
| ⑤ | `status=failed` · **`motivo_parada=teto_wall`** · `fe_final=282/371` |
| ⑤ · as 6 chaves | `campanha_id` ✅ `repo_hash` ✅ `params` ✅ `sigma_dict` ✅ `timing` ✅ `doe_hash` ✅ |
| ① `__real` | **282 linhas** × 21 cols — legível |
| ② / ③ / ④ / ⑥ | 31.237 / 161.060 / 151 / 551 linhas |
| **Coerência** | a ① tem **282** linhas e o ⑤ declara `fe_final=282` — **batem exatamente** |

**E o portão trata certo:** `aborto-sancionado` (DI-38a) **e ainda assim roda os
6 gates de proveniência**, todos VERDES — incluindo `G-1 3x1 = 151/151
bit-idênticos, 0 ids órfãos`, já sob o denominador corrigido do achado #48.

**O que isso valida.** O rito completo do **G5/DI-43/DI-44**: uma célula que
estoura o teto morre **COM dado**, com ⑤ coerente e rastreável, e o gate a
reconhece como estado ESPERADO em vez de falha. É o teste que protege as
**~485 h-core** que o plano estimava perder se as células de 12 h morressem sem
dado.

### 12.2 · Pico de RAM — **1.205 MB (piso)** → `--n-jobs` cravado

Probe instrumentado sobre `batch/c262/ZDT4/q=10`, amostrando o RSS do próprio
processo a cada 2 s: **1.205 MB em 1.306 amostras**.

⚠ **É PISO, não pico definitivo.** O run não chegou ao fim — foi morto sob
pressão de memória. O número sobreviveu porque o probe grava o pico **a cada
novo máximo** (tmp+rename), a mesma doutrina do checkpoint do G5. **As duas
tentativas anteriores morreram deixando NADA**, e foi esse conserto que
transformou "sem resultado" em "resultado parcial utilizável".

**Há um SEGUNDO ponto medido, e ele é maior:** o `c154/DTLZ2` (D=12) chegou a
**2,2 GB** observado por `ps` durante as 6 h. Também é piso — parou no teto com
282 de 371 FEs.

⚠ **Por que os dois são pisos, e por que isso importa.** Em métodos baseados em
GP a memória cresce com o número de observações (a matriz de covariância é
O(n²)). O consumo real ao FIM de um run é maior que ambas as medidas.

**Teto adotado: 4 GB por job, com `n-jobs` sobre 80% da RAM** (decisão do autor,
2026-07-31). A primeira versão usava 6 GB e dividia a RAM INTEIRA — o que
escondia a margem de segurança dentro do número por-job, tornando impossível
saber quanta folga existia. **Teto e folga são coisas separadas.**

| máquina | vCPU | RAM | 80% utilizável | **`--n-jobs`** |
|---|---|---|---|---|
| Mac A | 8 | 16 GB | 12,8 GB | **3** |
| VM-1 `v5-mestrado` | 32 | 64 GB | 51,2 GB | **12** |
| VM-2 `mestrado-v6` | 32 | 64 GB | 51,2 GB | **12** |
| VM-3 | 16 | 32 GB | 25,6 GB | **6** |

🚨 **REGRA DE ARRANQUE:** o primeiro lote roda com **METADE** desses valores; o
autor observa o pico real por ~1 h e só então sobe. **Nenhum `n-jobs` derivado
de duas medições INCOMPLETAS merece confiança cega**, e o custo de errar para
cima não é lentidão — é o OS matando células de madrugada, sem aviso e sem
dado. Foi exatamente o que aconteceu com o probe desta campanha, DUAS vezes.

**A RAM é o gargalo em TODA máquina.** Com 1 thread por run (D79) caberiam
tantos jobs quantos vCPU (16 no VM-1), mas com a folga de SO a memória esgota
antes. Detalhe e comandos no **RUNBOOK §Y**.

---

## 13. TODAS AS DECISÕES DA SESSÃO — problema → opção escolhida

> As de gate/código estão em §11. Estas são as de **rumo**, tomadas com o autor.

| # | problema | opções | **escolhida** | por quê |
|---|---|---|---|---|
| **1** | O acumulador de P_wrong parecia custar 2,5× de lentidão | (a) manter a reescrita O(1); (b) **reverter** | **(b)** | microbenchmark REFUTOU a causa (ERRATA 9): 30,5→7,1 µs/chamada ⇒ ~1,9 s/run, não 23 min. Caiu o motivo, cai a mudança — e reverter fez o lacre voltar a bater sem artefato novo |
| **2** | VD-b1: o torneio do b1 indexa lista errada | (a) documentar; (b) corrigir como o DI-45; (c) corrigir só no M8; (d) instrumentar e decidir | **(a) NADA MUDA** | a SPEC já o classifica **🟠 IMPL → CÓDIGO** (`:434`/`:500`) e o `EvolALG.m:9-10` registra "fica (CODIGO K.3)". Marcá-lo 🔴 reabriu decisão FECHADA (ERRATA 10) |
| **3** | VD-b3: `Next` mistura domínios de índice | (a) instrumentar 2 linhas; (b) **fechar como forense** | **(b)** | medir mais para decidir algo que não está em aberto é trabalho sem destino |
| **4** | Wrapper do gatilho do `adapt` (A3/I-05 item 4) nunca implementado | (a) implementar; (b) **declarar e não fazer** | **(b)** | cirurgia vendorizada ⇒ âncora + re-lacre + **90 min de nova prova**. A cadeia A8 já é observável nas DUAS pontas (causa em `flag_vetores_degenerados`, efeito em `p_wrong_stats`) |
| **5** | 58 manifestos forasteiros acusados pelo preflight | (a) mover para quarentena; (b) apagar; (c) **manter** | **(c)** | são células legítimas das VMs (26–27/07). O preflight sair ≠ 0 é ruído conhecido, não impedimento. **Nunca foi pendência minha** — é decisão operacional sobre dado real |
| **6** | Teto do `c154`: 12 h (oficial) ou menos? | (a) 12 h; (b) **6 h**; (c) matar o processo | **(b)** | o mecanismo é idêntico; (c) não testaria nada (matar ≠ o código disparar o rito) |
| **7** | Pico de RAM: esperar o run completo? | (a) esperar 2,2 h; (b) **cravar 6 GB sobre o piso** | **(b)** | 5× o medido é conservador o bastante, e a RAM já era o gargalo em toda máquina |
| **8** | Os 56 achados residuais | (a) tratar todos; (b) refutar antes; (c) arquivar | **(b) → tratar os sérios** | um agente cético os diagnosticou: 6 falso-positivo, 7 sério, 9 gate-cego, 34 opcional. Tratados #42, #48, #49, #33, #20 |
| **9** | População contaminada nos números descritivos | (a) re-medir; (b) **manter** | **(b)** | não afeta código nem campanha — **os resultados da dissertação saem do BUCKET**, não de `data/experiments` |
| **10** | Paralelizar os testes finais? | (a) paralelo; (b) **série** | **(b)** | medido: o ganho seria ~7 min contra reintroduzir a classe de erro que já custou uma rodada (threads compartilhando `torch.set_default_dtype`) |

---

## 14. ARQUIVOS NOVOS — o que é cada um e por que existe

> ⚠ **Três categorias distintas.** Nem tudo que aparece como "novo no git" foi
> criado nesta sessão: os 9 drivers já existiam **untracked** e foram
> COMMITADOS pelo B-12 (o plano manda versioná-los porque um driver fora do git
> é um procedimento que ninguém consegue auditar).

### 14.1 · Código NOVO — escrito nesta sessão

| arquivo | linhas | por que existe · o que faz |
|---|---|---|
| **`scripts/gates_proveniencia.py`** | 645 | **O coração do G6.** Nenhum gate conferia campo DI-10 de config algum — I-05, I-07 e I-03 atravessaram CINCO gates verdes. Implementa **G-1** (3×1: a ③ diz ter copiado o X de uma avaliação real? confere contra a ①), **G-2** (unicidade/integridade do ⑥), **G-3** (proveniência: venv ∈ roster + `campanha_id` + `repo_hash`), **G-4** (gabarito normativo de camadas), **G-7** (o CONTRATO §6.1 aferido por config) e **B-15** (discriminador O-22). Distingue **NÃO-APLICÁVEL** de **NÃO-AFERÍVEL** — a doutrina B-07 diz que inconclusivo nunca é verde, mas só o segundo pede investigação |
| **`scripts/staleness.py`** | 80 | **O gate que a campanha não tinha, e que nasceu de uma pergunta do autor:** *"houve algoritmo testado ANTES do seu estado final de código?"*. Cruza o **fecho de imports** (AST, recursivo) de cada config × `git log -1` por arquivo × a hora do smoke. Sai ≠ 0 se algum teste for anterior ao código que testa. Achou **9 pares G-6 stale** e depois o `b5m` — este último só porque a 1ª versão do próprio gate era cega ao caso |
| **`scripts/content_hash.py`** | 115 | **G-9.** A mescla do `tabela42.py` decidia por `tamanho + mtime±2s` — heurística que **apagava o destino em silêncio** quando dois arquivos coincidiam. Substitui por comparação real: inode → tamanho → md5. Alimenta o `DIVERGENCIAS_CONTEUDO.csv` |
| **`src/checkpoint.py`** | 162 | **G5/DI-43.** Checkpoint atômico periódico (K=25 iterações **OU** 30 min) em 8 runners Python: flush do buffer + parquets parciais via tmp+rename. **O ⑤ é escrito por ÚLTIMO e o `fe_final` dele é PISO** — as 5 escritas são atômicas uma a uma, não como grupo; um ⑤ atrás subdeclara dado que existe, um ⑤ à frente prometeria dado que não existe, e essa é a mentira que a campanha não pode ter |

### 14.2 · Artefatos normativos NOVOS (machine-readable)

| arquivo | linhas | por que existe |
|---|---|---|
| **`contrato_61.json`** | 301 | O §6.1 do CONTRATO em forma legível por máquina: por config, quais chaves o ⑥ (evento de geração) e o ⑤ têm de carregar, **e o que NÃO SE APLICA com o motivo**. Sem ele o G-7 inventaria falso-vermelho onde o contrato já disse "aqui não". Foi fonte de **5 erratas** (6, 7, 8, 12, 14) — escrevi-o do TEXTO da SPEC sem confrontar com o que cada runner emite |
| **`motivos_parada.json`** | 63 | **B-06 — fonte ÚNICA** da classificação de motivo, consumida por `portao`/`accept`/`censo`. A divergência entre os literais `'cache_cap'` e `'cache_hit_travado'` espalhados no código custou a DI-41.2 |
| **`mapa_termino.json`** | 46 | **I-08.** Mapeia término × o que se espera da célula — usado pelo G-2 e pelo G-7 para não acusar ausência que é desenho |
| **`gabarito_camadas.json`** | 53 | **G-4.** O gabarito NORMATIVO de quais camadas cada config deve produzir. Substitui o "modal do censo", que inferia o esperado da maioria — e a maioria pode estar errada junto |

### 14.3 · Testes NOVOS — 19 arquivos

Cada um traz **CONTROLE MEDIDO**: a mesma checagem rodada contra a versão
ANTERIOR do alvo tem de **REPROVAR**. Sem isso, um teste estrutural não prova
nada — e nesta sessão dois controles falharam por estarem ancorados em
referência **móvel** (`HEAD`/`HEAD~1`), passando quando deveriam reprovar.

| arquivo | linhas | o que trava |
|---|---|---|
| `test_gates_g6.py` | 784 | os 9 gates do G6, incl. a partição dos 24 configs e o evento de geração por config |
| `test_checkpoint.py` | 432 | o G5: kill-test com SIGKILL, resíduo limpável, **`checkpoint_nao_muda_o_resultado`** com controle provando que o checkpoint de fato rodou |
| `test_audit_log.py` | 296 | B-01 (anti-append) + B-11 (1 linha = 1 `os.write`), com controle medido de perda por splice |
| `test_espelho.py` | 289 | G4: cliente GCS falso — `if_generation_match`, poda só após md5, e o caminho blob-presente |
| `test_a2_c122.py` | 257 | o teste de aceitação do I-01: `n_ref=21 (=11D−1)` no g=1 × `11 (=MU)` no g≥2 |
| `test_campanha.py` | 234 | B-03: `campanha_id`, `is_run_done` v1⇒False, `QUALQUER_CAMPANHA` |
| `test_despachante.py` | 231 | G2: o skip não abre o ⑥, `NO_RETRY`, ⑤ do aborto com a célula |
| `test_a11_matlab.py` | 224 | A11 MATLAB: a aritmética do mixer MINSTD (com controle reproduzindo a **saturação de `uint64`** do MATLAB), a fiação nos 3 classificadores, a separação régua × bloco |
| `test_g6_matlab.py` | 203 | o gêmeo MATLAB da flag: cobertura dos 24, os **4 caminhos** até o `fire`, restauração do env |
| `test_g7_instrumentacao.py` | 178 | G7: cronômetro com NULL, `repo_hash` nos 2 stacks |
| `test_a1_c154.py` | 138 | A1: `params` no ⑤ e a regra I-12 de leitura da ③ |
| `test_lacre_vendorizado.py` | 133 | o lacre: `tree_sha256` reage a 1 byte **e** o preflight COMPARA (controle: a versão anterior reprova) |
| `test_g1_controle_positivo.py` | 122 | a **quimera sintética** — a prova de que o G-1 sabe dizer NÃO |
| `test_drivers_b12.py` | 109 | B-12: os 9 drivers no git + o discriminador de forasteiro (por HOST, não por venv) |
| `test_a9_regra_rotulo_c217.py` | 105 | a fórmula do pareamento cíclico do c217 contra o laço do stock, com controle do off-by-one |
| `test_zy_portabilidade_venvs.py` | 85 | a suíte IMPORTA em py3.7/py3.8 — os venvs de 13 `skipUnless` |
| `test_zz_guarda_data.py` | 84 | **G-8**: a suíte não escreveu em `data/`. Roda por último (`zz`) e inclui a RAIZ na impressão |

### 14.4 · Drivers COMMITADOS (já existiam untracked) — B-12

`censo_bucket.py` (272) · `tabela42.py` (333) · `lote3s.sh` (450) ·
`lote42.sh` (294) · `plano3s.sh` (184) · `preflight42.sh` (148) ·
`estado42.sh` (122) · `tempo42.sh` (117) · `coletar42.sh` (98).

**Por que versionar:** um driver fora do git é um procedimento que ninguém
consegue auditar nem reproduzir — e três deles decidem o que entra no censo.

### 14.5 · Documentos NOVOS

| arquivo | linhas | o que é |
|---|---|---|
| **`handoff/T11-RODADA-FINAL.md`** | ~700 | **este** — o registro completo |
| `handoff/T11-V1-verificacoes-dirigidas.md` | 220 | VD-b1 e VD-b3, com a ERRATA 10 que desmontou minha própria conclusão |
| `handoff/T11-parcial-2026-07-29.md` | 159 | o parcial da FASE G |
| `handoff/T11-FINAL.md` | 152 | ⚠ **OBSOLETO** — fotografia de 30/07 08:27, com aviso no topo |
| `handoff/T11-CONFORMIDADE.md` | 130 | os 24 configs: smoke, portões, §3.1 |

---

## 15. 🔬 PARA O AGENTE VALIDADOR DE FIDELIDADE

> **Leia esta seção primeiro se sua missão é validar FIDELIDADE.** Ela existe
> porque a validação de fidelidade é **explicitamente MANUAL e do autor (D97)** —
> nada nesta campanha a fez, e é a maior lacuna do trabalho (confiança 25%, §8).

### 15.1 · O que esta campanha PROVOU, e o que ela NÃO prova

| provado | NÃO provado |
|---|---|
| Cada config **roda ponta a ponta** e escreve as 7 camadas contratadas | Que os **valores** produzidos estão certos |
| O ⑤ traz `campanha_id`/`repo_hash`/schema v2 e as 6 chaves | Que o algoritmo faz o que o **artigo** descreve |
| O ⑥ tem header+footer e zero linha malformada | Que a busca converge como deveria |
| A **sonda não perturba a busca** (§3.1, 19/19 configs, ① bit-idêntica) | Que os hiperparâmetros são os do paper |
| A proveniência fecha e o dado é rastreável | Que as divergências código×paper são aceitáveis |

**Um algoritmo pode estar profundamente errado e passar nos 6 portões.** Os
gates conferem **estrutura**; nenhum confere **valor**.

### 15.2 · Onde estão os smokes que você vai auditar

| stack | onde | células |
|---|---|---|
| **MATLAB** (13 configs) | `/tmp/smoke_matlab/experiments/` | b1·b3·b4·c141·c217·c238·e7·e74(×3)·moead·nsga2·nsga3·smsemoa em `main`; e103 em `off` |
| **Python** (11 configs) | tempdirs **já removidos** — os vereditos dos gates estão em §5 | — |
| **Pares §3.1** (com × sem sonda) | `/tmp/g6_com` e `/tmp/g6_sem` | b1·b3·b4·c141·c217·c238·e7·e74·e103 |
| **Teto** | `/tmp/teto_c154_*/experiments/main/c154/` | `DTLZ2/s42`, truncada em `teto_wall` |

⚠ Os tempdirs Python foram limpos por desenho (nenhum smoke escreveu em
produção — verificado: **0 manifestos com `campanha_id`** em `data/experiments`).
Para re-gerar qualquer um: `RUNBOOK §X` traz a invocação de SMOKE.

### 15.3 · As DIVERGÊNCIAS código×paper já conhecidas — comece por aqui

A SPEC as classifica com uma bússola única: *"o parâmetro muda o mecanismo que a
tese mede (o surrogate e o uso da incerteza)?"*

| config | divergência | classe SPEC | onde |
|---|---|---|---|
| **b1** ParEGO | λ=100/91 vs 11/15 · subset top-determinístico vs ½ melhores+½ aleatórias · GA geracional c/ truncamento elitista vs steady-state pop 20 · MLE boxmin sem restarts vs Nelder-Mead 20 restarts · **torneio bugado** | 🟠 **IMPL → CÓDIGO** (D30/D47) | `SPEC:500` |
| **c217** PC-SAEA | spread da PNN 0,1925 (paper: 0,2) · operadores GA η_c=15/η_m=5 (Balde C: 20/20) · pares todos×todos | 🟠 CÓDIGO documentado (K.3) | `SPEC:559,564` |
| **c122** | `random.sample` | 🟠 IMPL | `SPEC:434` |
| **e74** CLMEA | **DI-45 CORRIGIDO** (índice de subconjunto usado como absoluto). ⚠ Há um **SEGUNDO** desalinhamento em `Local_infill.m` (máscara(Offspring)×Parent) **deliberadamente NÃO corrigido** | 🔴 → corrigido / 🟠 mantido | `e74_instrument.m:184` |
| **c149** | `[:, :2]`→`[:, :M]` | 🔴 BUG → **ARTIGO** | `SPEC:434` |
| **e103** | `pm=1/D²`→`1/D` | 🔴 BUG → **ARTIGO** | `SPEC:434` |
| **c262/e81** | kernel RBF→**Matérn 5/2 ARD** | 🔵 VERSÃO → **ARTIGO** (toca a incerteza) | `SPEC:434` |
| **c311** | σ das folhas | 🟢 EXTENSÃO nossa | `SPEC:434` |
| **c238** EIM | GA de aquisição (paper usa DE 50×50) · anti-clustering **não existe no repo** | ⚠ divergência aberta | `SPEC:811` |
| **c141** MMRAEA | `Problem.N` é POR subpopulação · crash real D≤4 com N=100 | fixes documentados | `SPEC:809` |

### 15.4 · Os dois achados 🔴 desta campanha — leia antes de decidir qualquer coisa

**VD-b1 · o torneio do ParEGO.** `TournamentSelection(K,N,PCheby)` devolve
índices no domínio de `PCheby` (o subconjunto pós-cap e pós-dedup) e o chamador
os usa em `Dec` (o arquivo INTEIRO). Dois danos: linhas `|PCheby|+1..|Dec|`
nunca podem ser pais, e a aptidão que ganha o torneio pertence a outro
indivíduo. **NADA FOI MUDADO** — a SPEC já o classifica 🟠 e o `EvolALG.m:9-10`
registra "fica (CODIGO K.3)".
**Números medidos, com DUAS erratas contra minha própria leitura:**
· afeta a metade-crossover da **PRIMEIRA** geração interna do GA de aquisição;
  da 2ª em diante os domínios CASAM (`EvolALG.m:65`) — **ERRATA 10**
· o ramo é **3,87%** dos candidatos scorados; inerte em **~93,9%** dos ciclos
· ⚠ **ERRATA 16:** em **597 dos 1.029** ciclos onde "a 1ª geração venceu", o
  `e0_trace` é **CONSTANTE** — o GA não melhorou nada. `BBOB_F37`/`BBOB_F49`
  (as células do "efeito concentrado") são **85,8%/87,1%** degeneradas. **O
  número superestima o peso do torneio**
· o conserto seria **um token** (`Population.decs` → `PDec` em `ParEGO.m:92`,
  onde `PDec` já existe em lockstep com `PCheby`) — mas isso também estreitaria
  o ramo de MUTAÇÃO, que hoje varre o arquivo inteiro

**VD-b3 · o `Next` do `UpdataArchive` (K-RVEA).** No ramo 1, `current` é posição
em `Via` (vetores de referência) e é usado para indexar `Total` (soluções) —
dois domínios. `nzero=0` em **1.619/1.619** ciclos **não discrimina qual ramo
rodou**, porque nem `size(Via,1)` nem `NI−mu` são logados. **Fechado como
forense read-only.** Se a validação de fidelidade quiser transformar isso em
número, são **2 linhas read-only** no `b3_instrument`.

### 15.5 · O que a instrumentação oferece para a auditoria de fidelidade

Cada config grava no ⑥ (`.jsonl`) um evento de geração com os campos DI-10 do
seu contrato (`claude_code_context/artifacts/contrato_61.json`). Os mais úteis:

| campo | config | o que permite auditar |
|---|---|---|
| `sigma_dict` (⑤) | **todos** | **LEITURA OBRIGATÓRIA antes de usar a ③** (DEF-C4) — o dicionário semântico de cada coluna |
| `REGRA_DO_ROTULO` (⑤) | b4, c217, c122 | como recuperar o rótulo VERDADEIRO de uma linha da sonda. ⚠ **A do c217 é POSICIONAL E CÍCLICA** (`RBFNNPC.m:61`), não a do b4 |
| `regime='sonda'` (③) | 19 configs | a **régua Sobol** — 2.000 pontos FIXOS, iguais para todos: "o modelo é bom GLOBALMENTE?" |
| `regime='sonda_estratificada'` (③) | 4 classificadores | ~500 pontos perto do arquivo: "ele acerta ONDE a decisão acontece?". Prevalência **7,4% × 0,4%** da régua |
| `p_wrong_stats` + `flag_vetores_degenerados` | b5m | a **cadeia A8**: `adapt` zera `values` → PBI NaN → P_wrong ≡ 0 → zero substituições (congelamento) |
| `n_ref` + `ref_ids` | c122 | a referência REAL usada (21 = 11D−1 no g=1 × 11 = MU no g≥2) |
| `pmid_ids` | c217 | a identidade das referências Pmid do ciclo |
| `margem_3sigma_stats` | e103 | a estatística do gate ±3σ |
| `e0_trace` | **b1 apenas** | o melhor EI por geração interna — ⚠ **constante em 58% dos ciclos** (ERRATA 16) |

### 15.6 · Regras de leitura que a auditoria DEVE respeitar

Do `CONTRATO_DE_DADOS.md` §10 — as duas últimas são desta campanha:

1. Dedup/joins por `solution_id`, **nunca** pelo X float32 armazenado
3. **Antes de ler a ③: leia o `sigma_dict` do manifesto** (DEF-C4)
5. Sonda: join com o gabarito **POR POSIÇÃO** dentro do bloco
9. `fe_treino_max` **NÃO é monotônico** em b1/b4/c217 (subamostram o treino)
11. ⚠ **Dominância sobre ① ou ⑦ é LOSSY** — `f0`/`f1` são **float32** e o
    algoritmo decidiu em float64. Duas soluções que a busca distinguiu podem
    sair EMPATADAS no parquet. **Diferenças abaixo da resolução do float32 não
    são conclusivas**
12. ⚠ **`regime='sonda_estratificada'` NUNCA entra na mesma análise que
    `regime='sonda'`** — a régua é comparável entre configs; o bloco
    estratificado não (cada config tem um arquivo diferente)
+ **I-12** (c154/c262): a ordem da ③ BoTorch é regra de leitura, não campo

### 15.7 · Roteiro sugerido

1. **Leia §15.3** — as divergências já classificadas. Não re-descubra o que a
   SPEC já decidiu; **valide se a classificação continua defensável**.
2. **Para cada config, cruze o smoke com o artigo:** os hiperparâmetros do
   `params` do ⑤ batem com a Tabela do paper? A `sigma_dict` descreve o que o
   modelo realmente é?
3. **Use a sonda como régua de qualidade do surrogate** — ela existe para isso.
   Nos 4 classificadores, o bloco estratificado responde a pergunta que a régua
   não responde.
4. **Os 🔴 abertos:** o 2º desalinhamento do e74 e o VD-b3 sem medida.
5. **Desconfie dos meus números.** Esta campanha produziu **16 erratas**, cinco
   delas falso-positivo de gates que eu mesmo escrevi, e duas contra minha
   própria leitura do VD-b1. **Re-meça o que for usar.**
