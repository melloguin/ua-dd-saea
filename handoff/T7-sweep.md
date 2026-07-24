# T7-sweep — o fio do sweep offline (`exp` → `(tier, dist)` → dataset)

> Sessão de implementação · 2026-07-23 · branch `experiment/definitive_algorythms`
> Commit de código+testes: **`9fcde9f`**
> Baseline de entrada: HEAD `0155686` · suíte 328 OK (skipped=22) · preflight 0 ·
> `portao --varredura --exp off` 12 runs / 36 gates VERDE.

## 1. O que o cartão pedia e o que o diagnóstico encontrou

O cartão (REGISTRO A21) descrevia o T7 como "um elo fino": o andar de baixo estaria
pronto e faltaria só derivar `(tier, dist)` do token `exp`. **O elo era mesmo fino e
está fechado** — mas o reconhecimento (workflow de 8 leitores + verificação
adversarial) achou que **3 das premissas do cartão não se sustentam** e que havia
**2 defeitos de lançamento** no caminho. Tudo está documentado abaixo com file:line.

| Premissa do cartão | Realidade verificada |
|---|---|
| "datasets dos tiers **no disco**" | Existiam **5 arquivos-piloto**, todos da **semente 0** (MMF1 + 1 ZDT4). Para a **semente 42 havia ZERO**. Faltam 446 dos 450 do grid completo. |
| "ramo big do c311 = `_build_surrogates` **já implementado**" | A **função** existe (`c311_tgprmo.py:407-425`), mas é chamada **incondicionalmente** (`:548`) e **não há roteamento** algum por tier. Pior: a SPEC **não sustenta** rotear c311-big para lá — ver §4.1. |
| `load_dataset`/`load_offline_budget` aceitam tier/dist | ✅ Verdadeiro (`standalone_harness.py:523,584`). O buraco era só nos runners. |
| naming valida `sweep-<tier>-<dist>` | ✅ Verdadeiro — mas **não existia a inversa** (parser). Era exatamente o elo. |
| "o orçamento vem GRÁTIS do desenho" | ✅ Verdadeiro: `load_offline_budget` já monta `FEBudget(maxfe=n)` com o `n` **lido do artefato**. |
| os 3 runners offline (incl. `piso_offline`) | ✅ Fiados — mas o `moead_media` **não tem nenhuma célula de sweep** no `runs_matrix` (conflito com a SPEC — §4.3). |

## 2. O que foi implementado (commit `9fcde9f`)

### 2.1 `src/naming.py` — o parser (o elo)
- `SWEEP_TIERS`/`SWEEP_DISTS`: vocabulário canônico, espelho de `doe.py::TIER_ID/DIST_ID`
  e de `seeds.json:dataset_offline`. Vive em `naming` porque é stdlib puro e é a fonte
  única da nomenclatura (`doe` importa `naming`, nunca o inverso).
- `parse_sweep(exp) -> (tier, dist)`: `main/off/batch` e qualquer token não-sweep ⇒
  `(None, None)`. Token **com forma de sweep mas vocabulário inválido ⇒ `ValueError`**
  (pára-e-loga). Devolver `(None, None)` nesse caso recriaria exatamente o bug
  silencioso que o T7 existe para fechar.
- `is_main_variant(tier, dist)`: `small`+`lhs` **É** o offline principal e é gravado
  **sem sufixo** (`seeds.json:dataset_offline.principal_offline`, D90). Espelha a regra
  `is_main` de `doe.py::ensure_dataset` — quem escreve o artefato.
- `dataset_variant(exp)`: o par pronto para os loaders (`(None,None)` quando o alvo é o
  principal). **É esta que os runners chamam**; `parse_sweep` fica para quem quer o par
  LITERAL do token (manifesto, logs, gates).

### 2.2 Os 3 runners offline
`b5_prob.py`, `c311_tgprmo.py`, `piso_offline.py` derivam **do `exp`** (nunca de kwarg —
fonte única: o nome do run e os dados não podem divergir), repassam a
`load_offline_budget(tier=, dist=)` e gravam:
- `tier`/`dist` no **manifesto** (`write_run_outputs` ganhou os 2 kwargs, default `None`
  ⇒ nenhuma mudança para os 16 online);
- `tier`/`dist` + `dataset_path` (**o arquivo realmente lido**) no **header do `.jsonl`**.

### 2.3 Gates tier-aware (`scripts/accept.py`)
- Novo `n_dataset_esperado(exp, problema, semente, D, data_root)`: fora do sweep ⇒
  `31D−1`; no sweep ⇒ **o `n` do sidecar do dataset daquele tier**. O 2000/50000
  **não entra no gate** — duplicar a constante criaria duas fontes da verdade.
  Sidecar ausente ⇒ `(None, motivo)` e o gate **reprova com mensagem honesta**, nunca
  compara contra um número inventado.
- `check_fe` e os 3 checks offline (`check_r3_b5`, `check_r3_c311`, `check_r3_piso_off`)
  passam a aferir por célula **e a carregar a MESMA variante que o runner**.
- `auditar.py`: **verificado — nenhuma mudança necessária.** Ele não assume `31D−1` em
  lugar nenhum; suas constantes (`S_ONLINE/S_OFFLINE`) são de **sonda**, que é a régua
  fixa e **não** varia por tier (decisão registrada em §5).
- `portao.py`: **verificado — repassa `--exp` aos 3 gates** e a `--varredura` é
  drift-proof (enumera de disco pelo manifesto). Nenhuma mudança necessária.

### 2.4 🔴 FIX de LANÇAMENTO (bug latente — mesma classe do M9 da DI-31)
`src/experiment.py:211` repassava `**kwargs` **cru** a `run_in_venv`, cuja assinatura é
de **TRANSPORTE** (`exp/data_root/envs/interpreter/timeout/extra_kwargs/capture_output`).
Como `experiments.py:129` **sempre** passa `enable_bucket`, **todo run dos 4 configs
venv-only (b5r, b5m, moead_media, c311) despachado pela bateria estourava
`TypeError`** — engolido pelo `except Exception` genérico do despachante e convertido
em 3 retries + `status='failed'`. Latente porque os cartões R3 chamaram os runners direto.

**Reproduzido antes do fix** e corrigido por **camada** (não por lista de nomes): o que o
transporte entende fica nele; **todo o resto desce por `extra_kwargs`** — drift-proof,
de modo que um kwarg de runner novo (`tier`, `dist`, `q`, `teto_s`) passa a funcionar
sem editar o transporte. É a lição da DI-31 aplicada.

### 2.5 FIX D23/D60 — manifesto honesto em parada anômala
`b5_prob.py` e `piso_offline.py` tinham `try/finally` **sem `except`**: uma exceção
terminava o run **sem manifesto nenhum**. Numa bateria isso é **pior que um vermelho** —
`portao.py --varredura` enumera as células a partir dos manifestos em disco, então um run
assim **desaparece** da varredura (o total cai e nada fica vermelho: o ponto cego).
O `c311_tgprmo.py` já fazia certo. Novo `H.write_failed_manifest` escreve a certidão de
óbito e a exceção **é re-levantada** (o retry D23 do despachante segue intocado; o caminho
de sucesso é bit-idêntico). Exposto pelo T7 — ver §4.2.

## 3. Validação

| Gate | Resultado |
|---|---|
| Suíte completa | **344 OK** (skipped=22) — baseline 328, **+16 testes novos** |
| `scripts/preflight.py` | exit **0** |
| `portao --varredura --exp off` (não-regressão) | **12 runs / 36 gates VERDE** |
| Smoke `sweep-small-lhs/b5r/MMF1/42` | **VERDE nos 3 gates** · fe=61=31D−1 · cp_init_ok · `tier='small'/dist='lhs'` no manifesto · wall **142 s** |
| Smoke `sweep-small-mvns/b5r/ZDT4/42` | **VERDE nos 3 gates** · fe=309=31D−1 · cp_init_ok · `tier='small'/dist='mvns'` · wall **148 s** |
| Prova NEGATIVA (① do sweep ≠ 31D−1) | **OBTIDA**: o manifesto de `sweep-medium-lhs/b5m/MMF1/42` traz `maxfe=2000` e `fe_final=2000` (31·2−1 seria **61**) — o fio do tier chega ao orçamento. |

Testes novos: `tests/test_naming.py` (+5: round-trip dos 6 tokens, não-sweep, vocabulário
inválido, `is_main_variant`, casamento com o arquivo em disco) e
`tests/test_fio_sweep.py` (+11: transporte venv-only incl. a regressão do `enable_bucket`,
drift-proof de kwargs novos, online não desviado, 6 tokens em arquivos distintos, gate
tier-aware lendo do sidecar, sidecar ausente reprovando).

## 4. 🚩 O QUE **NÃO** FOI FECHADO — e por quê (D81: não decido fidelidade sozinho)

### 4.1 B15.4 — o "ramo big" do c311 **não** foi implementado (CONFLITO com a SPEC)
O cartão manda: *"roteie `tier=='big'` → `_build_surrogates` (B15.4: pula o while de
construção)"*. **A SPEC não sustenta essa leitura**, e a mudança seria invisível e grave:
- **D38** (SPEC:1628): *"**Pisos**: Kriging-média (small/medium), **tree-média (big)**"* —
  B15.4 descreve o **PISO** do tier big, **não** o c311.
- **§10 [P5/DI-16.5]** (SPEC:865): o piso offline vira **duas instâncias**, e a do big é
  *"**treed-GP-média** … = **a ablação do c311**, o único que roda no big"* (em `env_c311`).
- **SPEC:1520/1779/1904**: as âncoras de escalabilidade **do próprio c311 no big**
  (*"build @50k treed **31,6 s**"*; *"N=50k, D=2 → **2500 iterações** máx"*) **só fazem
  sentido se o c311-big RODA a construção iterativa**.

Rotear o c311-big para `_build_surrogates` transformaria **o único config do tier big na
sua própria ablação** — o mecanismo treed-GP (o `addGPs` iterativo) **é** o c311.
**O laço ficou INTOCADO** e a nota completa está no docstring de `_build_surrogates`.
**Decisão do autor.**

### 4.2 🔴 MVNS gera DUPLICATA em D=2 ⇒ 3 tokens do sweep morrem no MMF1
A D67 manda *"clip aos bounds"*; com μ=0,3 e σ=√0,1≈0,316 a probabilidade de uma
coordenada cair **exatamente** em 0,0 ou 1,0 é ≈**18,4 %**. Uma duplicata bit-a-bit exige
que **todas as D** coordenadas caiam no clip ⇒ P≈0,1845^D. Medido (semente 42):

| problema | D | small-mvns | medium-mvns | big-mvns |
|---|---|---|---|---|
| **MMF1** | **2** | **2**/61 | **76**/2000 | **1757**/50000 |
| ZDT4 | 10 | 0/309 | 0/2000 | 0/50000 |
| DTLZ2 | 12 | 0/371 | 0/2000 | 0/50000 |
| WFG9 | 22 | 0/681 | 0/2000 | 0/50000 |
| ZDT1 | 30 | 0/929 | 0/2000 | 0/50000 |

Qualquer duplicata ⇒ `RuntimeError … hazard L.15 … Pára-e-loga (D81)`
(`standalone_harness.py:608`) e o **assert gêmeo fatal no MATLAB** (`experiment.m:1975`).
**Raio de impacto: só o MMF1** — **9 das 90 células** da rodada-42 (MMF1 × 3 tokens mvns ×
os configs do roster), **270 dos 2700** runs do grid completo.
**O eixo mvns em si está PROVADO** (smoke 2, ZDT4). **Decisão do autor.**

### 4.3 🔴 O GP não treina no tier `medium` do MMF1 (parede numérica) — **só MMF1**
`sweep-medium-lhs/b5m/MMF1/42` estoura
`LinAlgError: kernel 1**2 * RBF(length_scale=10) is not returning a positive definite matrix`.
Causa: densidade. Em D=2 com n=2000 o espaçamento típico é **n^(−1/D)=0,022** — uma ordem
de grandeza mais denso que qualquer outra célula (a 2ª mais densa é MMF1-small, 0,128) ⇒
K numericamente singular. O bundle afirma *"Medium ≈2000 (**GP padrão ainda treina**)"* —
**falso para D=2**. Atinge b5r/b5m e o piso Kriging (mesmo `SurrogateKriging`).

**✅ CONFIRMADO restrito ao MMF1:** `sweep-medium-lhs/b5m/ZDT4/42` (D=10, n=2000)
**fechou com sucesso** — fe=2000, `cp_init_ok=True`, 801 gerações. Ou seja: **o tier
medium é viável**; o que não é viável é a combinação **medium × D=2**. Exatamente o mesmo
raio de impacto da §4.2 — **o MMF1 é o problema-filho do sweep nos DOIS eixos**, e pela
mesma causa de fundo (D=2). **Decisão do autor.**

### 4.4 Custo do tier `medium` — dado novo e relevante para A3/A5
**Medido:** `sweep-medium-lhs/b5m/ZDT4/42` = **2.480 s (41,3 min)** por run, contra
**148 s** no small ⇒ **~17× mais caro**. O `SurrogateKriging` é O(n³) com
`n_restarts_optimizer=9` **por objetivo**.

Extrapolação para a rodada-42: as células de `medium` são 4 configs × 2 dists × 5
problemas = **40**; descontando as 8 do MMF1 (bloqueadas pela §4.3) sobram **32 células ≈
22 h-core** só no medium — praticável em paralelo, mas **não desprezível**, e ainda sem
contar o `big`.

⚠ **O b5 não tem `teto_s` nenhum** (`grep teto b5_prob.py` = 0 hits) ⇒ não há aborto
limpo se uma célula degenerar. O `c311` tem `teto_s`, mas **o despachante nunca o passa**
(`experiments.py:129`) — o `_TetoWall` está inalcançável na bateria. Recomendo à torre
tratar isso junto com a decisão A3/A5.

### 4.5 e103 / MATLAB — ✅ patch ESCRITO e VALIDADO ao vivo
O cartão autorizava pará-e-perguntar *"se o custo/risco do lado MATLAB se mostrar alto"*.
O risco era **não poder validar**; verificado que **MATLAB R2025a Update 1 está instalado**
(`/Applications/MATLAB_R2025a.app/bin/matlab`, apenas fora do PATH) com as 4 toolboxes
(nnet/stats/optim/parallel) ⇒ **é validável ao vivo**, então o patch foi feito.

O e103 responde por **20 das 90 células** da rodada-42 (600 do grid) — deixá-lo de fora
inviabilizaria o sweep.

**Patch: `src/experiment.m` apenas** (`experiments.m` = 0 linhas, como previsto):
1. **Novos helpers** `nm_parse_sweep` / `nm_is_main_variant` / `nm_dataset_sufixo` —
   espelhos EXATOS de `naming.parse_sweep`/`is_main_variant`, incl. o **erro** em
   vocabulário inválido (devolver o principal recriaria o bug silencioso).
2. `nm_dataset_path` / `nm_dataset_manifest_path` ganham `tier`/`dist` opcionais e a
   regra do sufixo — **`sweep-small-lhs` continua caindo no nome SEM sufixo** (a armadilha
   que quebraria 150 runs por arquivo inexistente).
3. `load_dataset(..., tier, dist)`: o assert que **exigia small/lhs** (`:2636`, que fazia
   TODA variante do sweep abortar) virou **conferência contra o que foi PEDIDO**; expõe
   `ds.tier`/`ds.dist`/`ds.n`.
4. `run_e103`: deriva `[tier,dist]` do `exp`; **`n_ds` passa a vir do ARTEFATO**
   (`ds.n`) em vez do `31*D−1` cravado — a identidade 31D−1 segue sendo aferida **só no
   principal**. Assim medium=2000/big=50000 nunca viram constante duplicada no MATLAB.
5. Manifesto: `'tier',"small",'dist',"lhs"` **constante** → vem do sidecar, e
   `man.tier`/`man.dist` de topo passam a ser preenchidos (antes ficavam `""` mesmo nos
   runs `off` — dívida que a auditoria já apontara).

**Validação executada:**
- `checkcode` — **0 erros de sintaxe**.
- **Regressão bit-a-bit** (`e103/MMF1/0/exp=main` num tempdir vs o run validado em
  `data/experiments/main/e103/`): `status=ok`, `fe_final=61`, `n_geracoes=99` — idênticos.
  **①real, ②pop (2996 linhas) e ③surrogate (59.800 linhas) BIT-IDÊNTICAS**; a ④timing
  difere **apenas** em `tempo_fit_s`/`tempo_busca_s`/`tempo_pred_sonda_s` (medições de
  wall — não-determinísticas por natureza). **O patch não altera comportamento algorítmico.**
  Único delta de manifesto pretendido: `tier: '' → 'small'`, `dist: '' → 'lhs'`.
- Smoke de sweep (`sweep-medium-lhs/e103/ZDT4/42`) — ver §4.7.

### 4.6 Os datasets do sweep NÃO existiam (e ainda faltam 441)
`doe.materialize_all` só materializa o **principal** (`doe.py:401`, sem tier/dist) e o CLI
`_main` **não expõe** `--tier/--dist`. Gerei em `data/datasets/` **apenas o necessário aos
smokes** (MMF1/42 nas 5 variantes + ZDT4/42 medium-lhs, medium-mvns, small-mvns) pelo
escritor canônico `doe.ensure_dataset` (determinístico por
`SeedSequence((semente, problema_id, tier_id, dist_id))`). **Não foram commitados** — são
dados, e a decisão de materializar as 441 restantes (volume/repo) é da torre.
Comando para a rodada-42 (5 problemas × semente 42):

```bash
python -c "from src import doe; [doe.ensure_dataset(p,42,tier=t,dist=d) for p in ['MMF1','ZDT4','DTLZ2','WFG9','ZDT1'] for t in ['small','medium','big'] for d in ['lhs','mvns']]"
```

### 4.7 Smokes

**⚠ Desvio deliberado da lista do cartão, e por quê.** O cartão fixava **MMF1** em todos
os 6 smokes. O MMF1 (D=2) é justamente a célula que **não roda** nos eixos mvns (§4.2) e
medium/big (§4.3). Como o cartão pede *"1 célula REAL por token"* e o objetivo é **provar
o fio**, troquei o problema por **ZDT4 (D=10)** nos tokens bloqueados — **ZDT4 é célula
igualmente real da rodada-42** (está no `runs_matrix` nos 5 problemas do sweep). Assim os
tokens ficam provados e o problema do MMF1 fica **isolado** como questão do autor, em vez
de mascarado como "falha do fio".

**✅ OS 6 TOKENS ESTÃO PROVADOS — 7 smokes, todos VERDES nos 3 gates.**

| Token | Célula | fe | wall |
|---|---|---|---|
| `sweep-small-lhs` | b5r/MMF1/42 | 61 | 142 s |
| `sweep-small-mvns` | b5r/**ZDT4**/42 | 309 | 148 s |
| `sweep-medium-lhs` | b5m/ZDT4/42 | 2 000 | 48,7 min |
| `sweep-medium-lhs` | **e103**/ZDT4/42 (**MATLAB**) | 2 000 | 187 s |
| `sweep-medium-mvns` | b5m/ZDT4/42 | 2 000 | 50,1 min |
| `sweep-big-lhs` | c311/ZDT4/42 | 50 000 | **69,7 s** |
| `sweep-big-mvns` | c311/ZDT4/42 | 50 000 | **51,9 s** |

**🔍 Achado de custo que contraria a expectativa:** o tier `big` é **BARATO** (~1 min),
não o terreno perigoso que o cartão temia (*"se >2h, aborte"*). A âncora do paper
(*"build @50k treed 31,6 s"*) estava certa. O caro é o **`medium` do b5** (~50 min), por
causa do `SurrogateKriging` O(n³) com `n_restarts=9` por objetivo — o c311 no big usa
árvore + GPs locais, que escalam muito melhor. **Isso remove qualquer argumento de custo
para o roteamento B15.4 do §4.1.**

Teste adicional (para a decisão do autor sobre o MMF1): `MMF16_20` (D=20, M=3, o único
MMF da lista canônica que sobrevive aos dois modos de falha) **roda no medium** —
fe=2000, `cp_init_ok`, **55,2 min** (1,13× o ZDT4, coerente com M=3).

**O smoke do e103 é a prova mais forte do cartão:** manifesto com `tier='medium'`,
`dist='lhs'`, `maxfe=fe_final=2000` (31·10−1 seria **309**), bloco `dataset` com
`n=2000`/`cp_x=True`/`cp_f=True` e `path` = **`ds_ZDT4_42_medium_lhs.parquet`** — isto é,
o CP-init casou contra **o arquivo do tier**, não contra o principal. É exatamente o erro
silencioso que o T7 existe para fechar, agora impossível.

⚠ Nota operacional: a ⑦ `__final` é **pós-hoc** (não sai do runner). Um smoke offline só
fica verde depois de `scripts/final_eval.py` (sem `--check`) — os 2 vermelhos iniciais do
e103 eram isso, não defeito do patch.

### 4.8 ✅ Determinismo e não-perturbação — AMBAS PASSAM

Executadas sobre `sweep-big-lhs/c311/ZDT4/42` — o token **mais barato** (~65 s/run) e que
exercita o caminho **mais novo** (tier big + rota venv-only, i.e. o fix do transporte).

| prova | camadas comparadas | veredito |
|---|---|---|
| **Determinismo** (2 runs, mesmas condições) | ⑦ (50) · ① (50.000) · ③ completa (215.061) · ② | **BIT-IDÊNTICAS** |
| **Não-perturbação** (sonda ON × OFF) | ⑦ (50) · ① (50.000) · ③-busca (175.061) | **BIT-IDÊNTICAS** |

⚠ **Armadilha de método, registrada para quem repetir:** comparar colunas com
`to_pylist()` reporta diferença FALSA em qualquer coluna com NaN, porque `NaN != NaN`.
No c311 só as colunas `sigma_*` têm NaN (contrato: *"NaN nas folhas SEM GP"*, DI-16.9) —
então a primeira rodada da comparação acusou "difere em sigma_0/sigma_1" com **zero**
valores diferentes e padrões de NaN idênticos. A comparação correta é NaN-aware
(`np.array_equal(..., equal_nan=True)`). Registrado porque o mesmo erro reprovaria
qualquer prova bit-a-bit futura do c311/b5.

## 5. Decisões que registrei (não são do autor, mas ficam explícitas)
- **Sonda não é parametrizada por tier** — os 3 runners seguem chamando
  `load_sonda(problema, regime='offline')`. É a **régua fixa** (§17.2.2): os mesmos 20.000
  pontos em todos os tiers é o que **torna os tiers comparáveis**. Mantido de propósito.
- **`tier`/`dist` no manifesto = o par LITERAL do token**, não a variante de arquivo: um
  run de `sweep-small-lhs` declara `tier='small'/dist='lhs'` ainda que leia o dataset sem
  sufixo. Quem consome o manifesto quer a **célula do grid**; quem escolhe o arquivo usa
  `dataset_variant`.

## 6. Estado do cartão — ✅ T7 FECHADO

Os 6 tokens provados (7 smokes VERDES nos 3 gates) · determinismo e não-perturbação
BIT-IDÊNTICOS · prova negativa obtida por 2 vias · suíte 348 OK · preflight 0 ·
`portao --varredura` sem NENHUM vermelho novo (os 5 existentes são pré-retrofit em
`main/`, todos do `auditar.py`, que estes commits **não tocam** — verificado no diff).

Commits: **`9fcde9f`** (Python + gates) · **`82317a3`** (MATLAB + paridade).

### Decisões do autor tomadas nesta sessão
| # | Questão | Resolução |
|---|---|---|
| §4.1 | B15.4 / ramo big do c311 | **Laço INTOCADO** (leitura da SPEC). B15.4 = o PISO do tier big ⇒ vira **cartão próprio** |
| §4.2/§4.3 | MMF1 nos tiers altos | **Trocar MMF1 → MMF16_20** em todo o sweep (proposta do autor; validada: computável, mesma família MMF) |
| — | Piso no sweep (§SPEC ×`runs_matrix`) | **Participa** — a SPEC vence (D83) |

### Pendências que NÃO são deste cartão
1. **Regerar `runs_matrix.csv`** (torre): incluir o piso nos 3 tiers + trocar MMF1→MMF16_20.
   `claude_code_context/artifacts/**` é território da torre — não toquei.
2. **Cartão novo: piso-big** = treeGP-média em `env_c311` (2ª instância do piso offline).
   Decorre da ratificação "piso participa"; não existe hoje (`piso_offline.py` só faz
   Kriging em `env_b5`).
3. **Materializar ~441 datasets** do sweep (§4.6) — comando pronto ali.
4. **`teto_s` inalcançável na bateria** (§4.4): o `b5` não tem, o `c311` tem mas o
   despachante não passa. Recomendo amarrar em A3/A5.
