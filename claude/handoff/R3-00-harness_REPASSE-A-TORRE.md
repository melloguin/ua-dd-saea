# R3-00-harness — REPASSE À TORRE

> **Para quem é este documento.** Para a instância-torre que redigiu o cartão
> `R3-00-harness`. É o relato completo do que foi executado, como, com que
> resultado, e — na §8 — **as definições que dependem do autor e que a torre
> precisa levantar com ele**. Companheiro de `handoff/R3-00-harness.md` (o
> contrato do que os cartões R3 herdam) e de `..._RELATORIO-EXECUCAO.md` (a
> narrativa).
>
> **Sessão:** 2026-07-19 · branch `experiment/definitive_algorythms` ·
> HEAD ao fechar: `6169435` · árvore limpa · 4 commits `[R3-00]`.

---

## 1. RESPOSTA CURTA: a etapa está pronta?

**Está pronta como INFRAESTRUTURA e o gate do cartão está verde — mas NÃO está
"100% fechada", por 3 motivos, e 2 deles são por desenho do próprio cartão.**

| # | O que falta | Por quê | Bloqueia? |
|---|---|---|---|
| 1 | **`__final` retroativo do e103** | **REGRA DE ORDEM do cartão**: só pode rodar sobre o e103 RE-PILOTADO. No fechamento o log tem `[DI09-R1] infra` e `[DI09-R1] c217`, **não** `[DI09-R1] e103`. Comando pronto no handoff. | Não bloqueia os cartões R3 |
| 2 | **Piso com `tempo_fit_s=NULL` não é gravável** | Lacuna do CONTRATO §4 **fora da minha faixa** (2 linhas em `src/export.py`, faixa do retrofit-BoTorch). Achada ao conferir o §4 item a item, a pedido do autor, DEPOIS do fechamento. | **BLOQUEIA o cartão `piso-off`** (`moead_media`) e os 4 pisos online |
| 3 | **9 definições em aberto** (§8) | 4 exigem decisão do autor; 5 têm dono sugerido | 2 delas bloqueiam cartões específicos |

O que **está** 100% pronto e provado: o harness transversal, a camada ⑦ nos dois
caminhos (nativo e retroativo), o gate, o dispatch, e o mecanismo de isolamento
por venv. Nenhum cartão R3 de algoritmo está bloqueado pelo item 1; o `piso-off`
está bloqueado pelo item 2.

---

## 2. VALIDAÇÃO — o código que rodei e o resultado (execução de 2026-07-19 17:23)

Tudo abaixo foi **re-executado do zero no fechamento**, não é resultado
lembrado. `PY = /Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python`.

### 2.1 Suíte de testes
```
$PY -m unittest discover -s tests -t .
→ Ran 194 tests in 3.828s · OK (skipped=1)
```
Era **122** antes do cartão → **+72 testes**. O skip é o legítimo herdado (F0-03,
lib presente ⇒ skip).

### 2.2 O gate do cartão — 4 problemas, 21 checks cada
```
$PY scripts/accept.py R3-00-harness --problema {MMF1,ZDT1,DTLZ2,MMF11_L} --semente 0

  R3-00/MMF1      exit=0   checks_OK=21   FAIL=0
  R3-00/ZDT1      exit=0   checks_OK=21   FAIL=0
  R3-00/DTLZ2     exit=0   checks_OK=21   FAIL=0
  R3-00/MMF11_L   exit=0   checks_OK=21   FAIL=0
```
Cobertura escolhida de propósito: MMF1 (D=2, o barato), ZDT1 (D=30, o caro),
DTLZ2 (**M=3**, exercita mais de 2 objetivos) e **MMF11_L** (o único dos 25 com
bounds não representáveis em float32 — entrou depois que a revisão mostrou que
ele quebrava; ver §5).

Os 21 checks, e o que cada um prova, estão em `check_r3_00` (`scripts/accept.py`).
Resumo: wiring do dispatch · FE = 31D−1 EXATO **e** = |dataset| · ① bit-exata ao
artefato · CP-init offline `x_hash` **E** `f_hash` · violação de regime →
exceção própria · cache-hit = 0 FE · 4+1 saídas · schemas §17.2 exatos · ③ com
`regime` por linha e `fe_treino_max` · ④ v5.2.1 completa · sonda na ordem do
artefato com hash e ZERO FE · ⑦ reconstituível da ③ · manifesto com `timing` +
`sigma_dict` · escrita atômica · pinning D79 · guarda de RNG · subprocess-por-venv
resolvido **e executado**.

### 2.3 Regressão — os gates que eu não podia quebrar
```
F0-01-harness  exit=0     R2-00-harness/MMF1  exit=0
F0-02-doe      exit=0     R2-00-harness/ZDT1  exit=0
F0-03-export   exit=0     preflight           exit=0
F0-04-metrica  exit=0
```
**Gates R1 e R2-c\* NÃO rodados** — instrução explícita do cartão (faixas MATLAB
e BoTorch ativas). Conferido que não toquei nada delas: `git status` sobre
`*.m` e `algorithms/` = **0 arquivos**.

### 2.4 A camada ⑦ isolada
```
$PY scripts/final_eval.py --exp off --alg stubr3 --problema {MMF1,ZDT1} --semente 0 --check

[OK] stubr3/MMF1/0: ⑦ presente e consistente (61 finais, 15 ND pós-real,
     f reproduz problems.py, X reconstituível da ③ ger 8 via origem_linha;
     procedência: float64 (decs em memória — caminho nativo R3))
[OK] stubr3/ZDT1/0: ⑦ presente e consistente (929 finais, 41 ND pós-real, …)
```
⚠ **Transparência sobre um FAIL intermediário:** na primeira passada da
validação o ZDT1 deu `[FAIL] camada ⑦ ausente`. **Não era defeito** — eu havia
apagado `data/experiments/off/stubr3/` durante os testes e só regerado o MMF1.
Reger o ZDT1 e re-checar deu `[OK]`. Registro porque um FAIL num relatório sem
explicação é pior que o FAIL.

### 2.5 Auditoria pyarrow dos artefatos (não só "o gate passou")
Li os parquets com pyarrow e conferi contra o CONTRATO:
- **④** colunas `[run_id, geracao, n_acumulado, tempo_fit_s, tempo_busca_s,
  tempo_pred_sonda_s, tempo_geracao_s]`, **0 nulos em todas**;
- **③** MMF1: 2488 linhas = **2000 `regime='sonda'` + 488 `regime='offline'`**;
  a linha de busca com `real_solution_id=0`, a de sonda com `NULL`;
  `fe_treino_max=60` nas duas; ZDT1: 9432 = 2000 + 7432;
- **⑤** manifesto com `timing` completo (4 chaves + `tempo_pred_sonda_s`),
  `sigma_dict`, bloco `sonda` (S/cadência/hashes) e `cp_init_offline`;
- **⑥** jsonl com evento `sonda` (n_pontos=2000, hash do artefato) e o mínimo
  comum DI-10 no `stubr3_gen`;
- **⑦** schema DI-08 exato, `nd_pos_real` reproduzível do próprio arquivo.

### 2.6 Números do STUB (para o dimensionamento M7)
| problema | D | FE (=dataset) | ③ linhas | ⑦ finais / ND | wall |
|---|---|---|---|---|---|
| MMF1 | 2 | 61 | 2488 | 61 / 15 | ~1,6 s |
| ZDT1 | 30 | 929 | 9432 | 929 / 41 | ~3,0 s |
| DTLZ2 | 12 | 371 | — | — | ~2 s |
⚠ O wall é do **STUB** (surrogate IDW trivial), **não** do harness nem de
algoritmo real — não serve para projetar a bateria.

---

## 3. O QUE FOI EXECUTADO, PASSO A PASSO

### PASSO 0 — contexto
Li integralmente: `00_contrato_rodada3.md` (N.1/N.2), `CONTRATO_DE_DADOS.md`
(§3, §3.1, §4, §7), SPEC §11/§17.7 (grep), `handoff/R2-00-harness.md`,
`handoff/R1-e103.md` (§2 e §8 — o molde offline), `CLAUDE.md` (raiz e
`claude_code_context/`), e as decisões DI-08/09/10/11 do
`REGISTRO_DECISOES_IMPLEMENTACAO.md`. Confirmei `[R2-00-harness]` e `[R2-c262]`
no log, e que **`[DI09-R1] e103` NÃO estava** (a REGRA DE ORDEM).

Paralelamente, 5 subagentes mapearam o código herdado (botorch_harness, export/
naming/budget/doe, experiment/accept, o offline do e103, sonda/datasets/envs).

### PASSO 1 — plano, e um D81 no meio dele
Ao desenhar, descobri que **as 3 exigências v5.2.1 do cartão eram inalcançáveis**
sem editar `src/export.py`, que o cartão me PROÍBE:

| exigência | impedimento |
|---|---|
| ④ `tempo_pred_sonda_s`/`tempo_geracao_s` | `timing_schema()` tinha 5 campos literais; chaves extras eram descartadas em SILÊNCIO (o helper `get()` em `export.py:337` era código morto) |
| ④ `tempo_busca_s` obrigatório | `nullable=True` cravado; `Schema.equals` compara nulabilidade |
| ③ `fe_treino_max` | ausente do schema; `surrogate_row` sem `**kwargs` |
| ③ sonda × busca na mesma tabela | `regime` era ESCALAR por chamada; a 2ª escrita SOBRESCREVIA a 1ª (provado: linhas de busca perdidas) |

Antes de escalar, tentei **refutar a mim mesmo** com 4 lentes independentes
(API, pyarrow, naming/paths, gate), com reprodução empírica: **4/4 não
refutaram**. O argumento mais curto veio da lente do gate —
`_check_export_schema` constrói o esperado a partir de `export.*_schema()`, logo
o gate é um **espelho** do `export.py`, e duplicar o writer também reprovaria.

**Escalei por D81** com 4 opções e uma recomendação. O autor informou que o
retrofit-BoTorch havia fechado. **Não segui na palavra:** conferi no repo e vi
que o topo do log mudara de `377e638` para `8e08d61` **durante a sessão** — 11
commits `[DI09-R2]`, com as colunas em `export.py:163/181-182/270`. Refiz o
recon (o mapa estava obsoleto) e segui. **`export.py` nunca foi tocado por mim.**

### PASSO 2 — implementação
Ordem: `naming.py` (aditivo) → `standalone_harness.py` → `final_eval.py` →
dispatch → branch do `accept.py` → STUB → testes.

Dois tropeços de API do `FEBudget`, ambos pegos no primeiro smoke (antes de
qualquer dado): `evaluate(x, true_f)` quer um **callable** (passei o array); e
`exhausted` é **property**, não método.

### PASSO 3 — validação, e o defeito que ela revelou
O STUB rodou verde de primeira. Em vez de fechar ali, rodei `final_eval --force`
sobre o mesmo run para comparar a rota **retroativa** (a do e103) com a
**nativa** — e os ND não bateram: **13 × 15**.

Não era float32 (`|ΔX|max = 1.63`): eram **pontos diferentes**. O laço escrevia
a ③ com `pop`, gerava `filhos`, e ao fim `pop == filhos` — o `__final` saía da
**prole da última geração, que a ③ nunca registrou**.

Isso importa muito além do STUB: para o **e103** a ③ é a **única** fonte da ⑦.
Corrigi o STUB **e transformei o invariante em check permanente**.

### PASSO 3b — revisão adversarial (antes do commit)
5 lentes de revisão + verificação cética por achado (default = falso-positivo),
**31 agentes, 753 tool calls**. **26 achados brutos → 7 CONFIRMADOS**
(1 crítico, 3 major, 3 minor), 19 refutados — inclusive uma "correção" sugerida
que teria **degradado** o regime offline. Todos os 7 corrigidos e cobertos por
regressão. Detalhe na §5.

### PASSO 3c — pós-fechamento
A pedido do autor, reconferi o `CONTRATO_DE_DADOS` §4 item a item e achei a
**lacuna do piso** (§8-D2). Registrada com sentinela de teste.

---

## 4. O QUE FOI ENTREGUE

**Novos**
- **`src/standalone_harness.py`** — infra transversal R3, irmão **torch-livre**
  do `botorch_harness` (b5/c311/piso rodam em venvs DESDEO sem torch, e aquele
  módulo faz `import torch` no topo).
- **`scripts/final_eval.py`** — o avaliador pós-hoc do DI-08 + CLI + o `--check`
  que o gate offline consome (fonte única da regra; o gate não a reimplementa).
- `tests/test_r3_harness.py` (50) + `tests/test_r3_final_eval.py` (22).

**Modificados — todos ADITIVOS**
- `src/naming.py` — `FINAL_LAYER`/`OPTIONAL_LAYERS`/`ALL_LAYERS` + `final_path`.
  **`LAYERS` INTOCADA de propósito:** é ela que `manifest.new_manifest`,
  `is_run_done`, `gcs.plan_targets` e `output_filenames` iteram; com `final` lá
  dentro **todo run ONLINE viraria "não pronto" e a esteira o re-executaria em
  loop**. Há teste dedicado.
- `src/experiment.py` — `stubr3` no dispatch + os 7 loaders R3 **comentados** +
  o **roteamento obrigatório por venv**.
- `scripts/accept.py` — branch aditivo `R3-00-harness` (21 checks) inserido
  **ANTES** do catch-all `if a.cartao.startswith("F0-01") or not a.alg:`, que o
  engoliria (o cartão não exige `--alg`) e devolveria o VERDE do andaime F0-01.

**Commits:** `488943b` (código) · `aa86711` (handoff+relatório) · `fae240d`
(sync DI-12.5) · `6169435` (sentinela da lacuna §4).

---

## 5. OS 7 ACHADOS DA REVISÃO (todos corrigidos)

1. **🔴 CRÍTICO — `evaluate_final` rejeitava a própria ⑦ em MMF11_L.** A
   tolerância de bounds era `1e-9` FIXO, ~100× **menor** que o quantum do
   float32 perto de 1.0 (~1,2e-7). Todo X que chega ali passou por camada
   float32 (D53) e clipar no bound é rotina de MOEA. `MMF11_L` (xl=0.1, xu=1.1)
   é o único dos 25 com bounds não representáveis em float32. **Medido: 8 de 29
   sementes** produziam uma ⑦ que o próprio `--check` reprovava. Corrigido para
   ~8 ULPs float32 da escala do bound + clip do ruído. **Agora 30/30.**
2. **MAJOR — o subprocess-por-venv era ferramenta, não mecanismo.** Nada
   roteava para `run_in_venv`: `experiment.run` despacha in-process, e o
   despachante serial e o paralelo (loky, que REUSA workers) chamam `run()`
   direto. A garantia N.1.2 vivia num **comentário**. O verificador reproduziu
   a falha com os overlays REAIS (21 `.py` homônimos e divergentes): o 2º
   `import desdeo_emo` devolve o pacote do b5, sem erro. Virou mecanismo em 3
   camadas: `VENV_ONLY_ALGS` + roteamento em `experiment.run` (com `_in_child`
   cortando a recursão) + `assert_overlay_coerente()`.
3. **MAJOR — a sonda não sabia escrever classificador/score.** O docstring
   mandava "ver `emit_sonda_block_score`" — **função inexistente**; e o
   `np.vstack` estourava com saída 1-D. Com o contorno óbvio, o score ia para
   `mu_0` — envenenando a ③. **Atinge o c122** (score par-a-par).
4. **MAJOR — assimetria de precisão do `nd_pos_real`.** Computado no F float64,
   mas o `--check` o recomputava no F **float32 relido**. Agora ambos usam a
   vista persistida.
5. **MAJOR — `check_final` impunha invariante mais forte que a declarada.**
   Uma ⑦ que fosse o subconjunto ND, ou reordenada, levava vermelho FALSO.
   Agora confere via `origem_linha`.
6. **MINOR — `check_final` estourava** em vez de devolver `(False, msg)`, e o
   gate morria com traceback **antes** dos checks 11–13.
7. **MINOR — dois checks do gate eram tautológicos.** `_r3_subprocess_probe`
   dizia "pin D79 no FILHO" e só conferia que o processo terminou — o
   verificador deu VERDE com `OMP_NUM_THREADS=8` no filho. Agora o filho
   **devolve** a evidência e o pai a **exige**.

Corrigidos de passagem: `run_in_venv(interpreter=...)` zerava o `env_id` e
descartava `env_flags` (o `MPLBACKEND=Agg` do c311 sumia); a ⑦ nativa nascia sem
sidecar; e a ⑦ **nunca subia ao bucket**.

---

## 6. DUAS FAIXAS VIZINHAS MUDARAM O CHÃO DURANTE A SESSÃO

Registro porque é lição operacional do paralelismo triplo:

1. **`export.py`** landou no meio do meu PASSO 1 (§3) — eu quase desenhei o
   harness em volta de uma limitação que deixou de existir.
2. **DI-12.5** cravou a cadência da sonda (`g = 1,2,4,6,…`, `a5f6eab`) **depois**
   de eu ter documentado A-12 como pendência. Meu `sonda_due` já implementava a
   fórmula vencedora — **zero mudança de código**, só do docstring e do handoff,
   que nasceram obsoletos. Idem `tempo_geracao_s` descontando a sonda
   (`47daa76`), que é a semântica que o `run_stubr3` usa.

**Sugestão à torre:** sinalizar landings de faixa cruzada às sessões ativas.
Reler o `git log` no fechamento pegou os dois casos — mas por sorte, não por
processo.

---

## 7. UM ACHADO QUE NÃO É MEU, MAS AFETA O R2-00

**MEDIDO: `pymoo 0.6.2` NÃO desloca `np.random` nem `random`** — nem com
`seed=`, nem sem. A premissa do contrato R3 item 3 / N.2.3 vale para o **pymoo
ANTIGO** dos venvs `env_b5`/`env_c311` (onde b5/c311 rodam, e onde a guarda é
indispensável).

**Consequência:** a checagem herdada do R2-00 — *"RNG-guard N.1.3 (provado
contra `pymoo.minimize` REAL)"* — é **vacuamente verde** no env-main: passaria
mesmo se `preserve_global_rng` fosse um `pass`. Endureci o meu lado (prova
mecânica sob perturbação máxima + sentinela de versão). **Recomendo o mesmo ao
check do R2-00** — fora da minha faixa.

---

## 8. 🔴 DEFINIÇÕES EM ABERTO — a torre PRECISA levantar com o autor

> Ordenadas por urgência. "Custo de mudar" = esforço se o autor decidir o
> contrário do implementado.

### D1 — 🔴 Schema da camada ⑦ (DI-08): ratificar ou cortar
- **O que a DI-08 fixou:** *"colunas `x0..x{D-1}`, `f0..f{M-1}` (avaliados em
  `problems.py`), `origem_solution_id`/link à ③"* — e delegou o resto
  (*"exige decisão de schema/naming — território da torre"*).
- **O que implementei:** `algoritmo|problema|semente|x*|f*|origem_solution_id|`
  **`origem_geracao`**`|`**`origem_linha`**`|`**`nd_pos_real`**.
- **As 3 além do literal, e o porquê:** `origem_geracao`+`origem_linha` são o
  "link à ③" materializado de forma **posicional e exata** (a regra 1 da R4
  proíbe casar por X float32); `nd_pos_real` é o filtro **B7.5 aplicado DEPOIS**
  da avaliação real — guardamos os N finais (D54) e marcamos quais sobreviveram.
  É a coluna que separa o front verdadeiro do **"erro de fantasia"**.
- **Decisão pedida:** ratificar em bloco, ou mandar cortar alguma.
- **Custo de mudar:** baixo hoje (só o STUB gravou ⑦); **alto depois** que os 4
  offline + e103 rodarem as 30 sementes.

### D2 — 🔴 A lacuna do §4: piso com `fit=NULL` não é gravável — quem conserta?
- **O contrato §4 manda:** *"Pisos: ④ por geração com `tempo_geracao_s`
  (fit=NULL)"*.
- **Estado real (executado):** `SnapshotBuffer` aceita `None` (fiel ao
  contrato), mas `export.timing_schema()` declara `tempo_fit_s` com
  `nullable=False` e `write_timing` faz `float(r["tempo_fit_s"])` sem guarda →
  **`TypeError`**.
- **Alcance:** **bloqueia o cartão `piso-off` (`moead_media`) da R3** e atinge
  os 4 pisos ONLINE da R1.
- **Decisão pedida:** quem faz as **2 linhas em `src/export.py`** (nullable +
  guarda de None) — o próximo cartão de faixa Python, um mini-cartão da torre,
  ou autorizar esta faixa a fazê-lo? **Precisa estar resolvido ANTES do
  cartão `piso-off`.**
- **Sentinela:** `test_LACUNA_CONHECIDA_piso_com_fit_NULL_nao_e_gravavel` falha
  quando for corrigido, avisando para atualizar o handoff.

### D3 — 🔴 Convenção da ⑦: "todos os finais" ou "só o ND"?
- **Tensão textual:** a DI-08 e o CONTRATO §7 dizem *"o **ND final**"*; a SPEC
  E.9-e103/B7.5 diz *"avaliar os 100 finais e **filtrar pós-real**"*.
- **O que implementei:** a leitura B7.5 — **grava os N finais** e marca
  `nd_pos_real`. Justificativa: filtrar ND **antes** seria filtrar pela fantasia
  do modelo, e é exatamente esse erro que a camada existe para medir; e o D54
  manda salvar tudo.
- **Decisão pedida:** ratificar a leitura B7.5 (e, se sim, vale um ajuste de
  redação no §7 do CONTRATO, que hoje diz só "o ND final").
- **Custo de mudar:** baixo (é um filtro no writer).

### D4 — ⚠ Caveat float32 da ⑦ retroativa (afeta SÓ o e103)
- Os decs da ③ estão em float32 (D53); a rota retroativa — **a única do e103**,
  que é MATLAB e já rodou — avalia o dec truncado.
- **MEDIDO (não estimado):** desvio relativo em `f` de até **9,7e-6** (MMF1) e
  6,0e-8 (ZDT1), com **0 inversões** de `nd_pos_real`.
- Os 4 cartões offline Python evitam isso chamando `write_final` com float64.
- **Decisão pedida:** aceitar o caveat (registrado no sidecar `origem_precisao`
  de cada ⑦), **ou** exigir que o e103 re-pilotado persista os decs finais em
  float64 à parte.

### D5 — ⚠ Resume × camada ⑦
- `manifest.is_run_done` **não conhece** a ⑦ (por desenho — ela é opcional).
  Consequência: um run offline **sem** ⑦ conta como "pronto" e a esteira não a
  gera sozinha. Hoje a ⑦ é passo pós-hoc explícito, que é o previsto pela DI-08.
- **Decisão pedida:** manter pós-hoc, **ou** fazer o resume cobrá-la nos 5
  offline (**1 condicional** em `manifest.py`). Não implementei para não mexer
  em `manifest.py` sem decisão.

### D6 — ⚠ Rota dupla de upload da ⑦
- `gcs.plan_targets` itera `naming.LAYERS`, que exclui `final`. Para a ⑦ não
  sumir com uma VM destruída, o `dual_write_run` a sobe **explicitamente**
  (+ sidecar) — na minha faixa, sem tocar `gcs.py`, e sem alterar os 16 online.
- **Custo:** ficam **duas rotas de upload**.
- **Decisão pedida:** unificar dando a `plan_targets` um parâmetro
  `optional_layers=()` (default vazio) e passando `('final',)` no caminho
  offline? É 1 função — mas `gcs.py` é faixa alheia.

### D7 — ⚠ Endurecer o check de RNG do R2-00 (ver §7)
- **Decisão pedida:** autorizar o mesmo endurecimento no `check_r2_00` (prova
  mecânica + sentinela de versão do pymoo)? Hoje aquele check não pode ficar
  vermelho.

### D8 — ⚠ B-1/A-9 herdado: `experiments.py::_run_one` apaga o manifesto do runner
- O retrofit-R2 documentou como **"item de cartão do R3-00/DI-06"**, mas
  `experiments.py` **não está na lista de faixa do meu cartão** e a correção
  muda a semântica de resume/`run_done`.
- **Efeito se não for feito:** se a bateria M8 for despachada por
  `experiments.py`, os 16.500 runs perdem `sigma_dict`, bloco `sonda`,
  `doe_hash`, `fe_final`, `env`, `fit_series` e o `timing` — **sem sintoma
  visível**.
- **Mitigação atual:** despachar por `src.experiment.run(...)` direto (foi o que
  o gate e os pilotos fizeram).
- **Decisão pedida:** confirmar o dono (DI-06/M7?) e a janela. **Antes do M8.**

### D9 — `load_sonda` duplicado (menor)
- Existe aqui e em `botorch_harness` — **necessário** (envelopes de dependência
  distintos: lá o módulo importa torch no topo). Há **teste de equivalência**
  que falha se divergirem.
- **Decisão pedida:** extrair para um módulo torch-livre compartilhado num
  cartão de hardening (M7/DI-06)? Exigiria editar `botorch_harness.py`.

### Não é decisão, é sequenciamento
- **`__final` retroativo do e103:** aguardando `[DI09-R1] e103` entrar no log.
  Comando pronto em `handoff/R3-00-harness.md` §REGRA DE ORDEM. ⚠ Antes de
  rodar, conferir o invariante ⑦×③ no e103 re-pilotado (a ③ da última geração
  tem de ser o `FinalDec`); se o re-piloto mudar isso, o `--check` acusa.

---

## 9. COMO REPRODUZIR TUDO

```bash
PY=/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python
cd /Users/gmello/Documents/python_repos/mestrado/ua-dd-saea

# o gate do cartão (4 problemas)
for p in MMF1 ZDT1 DTLZ2 MMF11_L; do
  $PY scripts/accept.py R3-00-harness --problema $p --semente 0; done

# a suíte
$PY -m unittest discover -s tests -t .            # 194 OK (1 skip)

# regressão (NÃO rodar gates R1/R2-c* — faixas ativas)
for c in F0-01-harness F0-02-doe F0-03-export F0-04-metrica; do
  $PY scripts/accept.py $c; done
$PY scripts/accept.py R2-00-harness --alg stubpy --problema MMF1 --semente 0
$PY scripts/preflight.py

# a camada ⑦ isolada (regere o run antes, se a pasta estiver vazia)
$PY -c "from src import experiment; experiment.run('stubr3','ZDT1',0,exp='off')"
$PY scripts/final_eval.py --exp off --alg stubr3 --problema ZDT1 --semente 0 --check
```
Saídas do STUB em `data/experiments/off/stubr3/` (gitignored, regeneráveis).

---

## 10. CHECKLIST PARA A TORRE

- [ ] Levantar com o autor **D1** (schema da ⑦) e **D3** (convenção "todos os
      finais") — os dois de ratificação, custo baixo agora e alto depois.
- [ ] Resolver **D2** (lacuna §4 do piso) **antes** de abrir o cartão `piso-off`.
- [ ] Decidir **D8** (`experiments.py`) **antes** do M8.
- [ ] Rodar o retroativo do e103 quando `[DI09-R1] e103` entrar no log.
- [ ] Marcar `cards/INDEX.md` (não marquei — paralelismo).
- [ ] Considerar **D7** (endurecer o check de RNG do R2-00).
- [ ] Considerar a sugestão da §6 (sinalizar landings de faixa cruzada).
