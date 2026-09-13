# R2-c154 — REPASSE À TORRE (o que foi feito, como, com que resultado, e o que FALTA DECIDIR)

> **Para quem é este documento.** Para a instância-torre que **gerou as
> instruções** desta sessão. Ele responde três perguntas: (1) a etapa está
> pronta? (2) o que exatamente foi executado e com que resultado? (3) o que
> ainda depende de decisão do AUTOR — e que a torre precisa levantar com ele.
>
> **Data:** 2026-07-19 · **Sessão:** R2-c154 (JES, 2º algoritmo da Rodada 2)
> · **Máquina:** Mac (macOS 12.5.1, arm64), env-main por caminho completo ·
> **Commits:** `925595b` (código) + `1641011` (docs), branch
> `experiment/definitive_algorythms`.
>
> Companheiros: `handoff/R2-c154.md` (o handoff técnico) e
> `handoff/R2-c154_RELATORIO-EXECUCAO.md` (a narrativa passo a passo).
> Este arquivo é o **sumário executivo para a torre**, e é o único que traz a
> §7 (conformidade com o CONTRATO_DE_DADOS v5.2.1, publicado DEPOIS do
> cartão).

---

## 1. RESPOSTA DIRETA: a etapa está pronta?

**SIM para o cartão R2-c154 como especificado. NÃO para "o c154 está pronto
para a bateria M8"** — e a diferença importa. Sejamos precisos:

| Item do teste de aceitação do cartão | Estado |
|---|---|
| `accept.py R2-c154 --alg c154 --problema MMF1 --semente 0` → exit 0 | ✅ **exit 0** |
| `accept.py R2-c154 --alg c154 --problema DTLZ2 --semente 0` → exit 0 | ✅ **exit 0** |
| `accept.py … --problema ZDT1` (o cartão o pôs entre colchetes, sob teto 8h) | ⚠ **N/A — o teto disparou** (§4.4). Previsto pelo cartão. |
| B9.5 resolvida no piloto | ✅ **resolvida e MEDIDA** (§4.3) |
| Regressão sem quebra | ✅ **8 gates exit 0 + suíte 91 OK** |
| Working tree só com a minha faixa | ✅ **5 arquivos, verificado** |
| Nada commitado sem aprovação | ✅ (commitado só após o "pode commitar") |

**O que NÃO está pronto e não era do meu cartão** (detalhe em §6 e §7):
o ZDT1 completo (decisão de orçamento do autor, M7), o retrofit da sonda
DI-09, a conformidade com 2 exigências NOVAS do `CONTRATO_DE_DADOS` v5.2.1
que a torre publicou **depois** que implementei, e as **9 definições em
aberto** (§6).

---

## 2. SIM, RODEI CÓDIGO. O QUE RODEI E O QUE DEU

Tudo abaixo foi re-executado **agora**, do zero, para esta resposta (não é
memória de execução antiga).

### 2.1 Ambiente (gate bloqueante D81)
```
$PY -c "import botorch,torch,gpytorch,scipy,numpy,pyarrow; print(...)"
→ botorch 0.18.1 | torch 2.11.0 | gpytorch 1.15.2 | scipy 1.17.1
  | numpy 2.4.6 | pyarrow 25.0.0                                  exit=0
```
BoTorch **0.18.1 OFICIAL** (a guarda N.2.3 do harness re-verifica em runtime
a cada run: fork com `__version__=='Unknown'` ⇒ RuntimeError). Nenhum
`pip install` (D80).

### 2.2 Os gates do cartão
```
$PY scripts/accept.py R2-c154 --alg c154 --problema MMF1 --semente 0
  [OK] 4 saídas válidas: 4 saídas + jsonl presentes
  [OK] FE final = 31D-1: FE=61 (esperado 61, D=2)
  [OK] DoE (CP-init): DoE bit-a-bit OK (hash 89b8ce4ec510207f… = sidecar)
  >>> VERDE (encanamento objetivo)                                exit=0

$PY scripts/accept.py R2-c154 --alg c154 --problema DTLZ2 --semente 0
  [OK] 4 saídas válidas: 4 saídas + jsonl presentes
  [OK] FE final = 31D-1: FE=371 (esperado 371, D=12)
  [OK] DoE (CP-init): DoE bit-a-bit OK (hash 71d3398a8fd224ef… = sidecar)
  >>> VERDE (encanamento objetivo)                                exit=0
```

### 2.3 Regressão (provar que não quebrei nada do que já existia)
```
F0-01 (andaime)                    exit=0
F0-02 (DoE/dataset/seeds)          exit=0
F0-03 (export/FE/atômico)          exit=0
F0-04 (métrica + âncora D92)       exit=0
preflight.py                       exit=0
R2-00-harness (stubpy/MMF1)        exit=0
R2-00-harness (stubpy/ZDT1)        exit=0
R2-c262 (MMF1)                     exit=0
```
**Gates MATLAB NÃO rodados de propósito** — faixa da sessão e103 (instrução
de paralelismo).

### 2.4 Suíte de testes
```
$PY -m unittest discover -s tests -t .   →  Ran 91 tests — OK (skipped=1)
```
Eram **82** antes desta sessão; os **9 novos** são do c154 e todos passam:
```
test_alg_id_e_catalogo_de_usos_batem_com_seeds_json ... ok
test_seeds_rederivadas_independentes ................. ok
test_constantes_da_receita ........................... ok
test_modelo_ruido_inferido_kernel_matern_standardize . ok
test_fallback_ladder_do_runtimeerror ................. ok
test_def_l2_replicada_do_c262 ........................ ok
test_nan_guard_ics ................................... ok
test_rota_invalida_rejeitada ......................... ok
test_linha_do_dispatch ............................... ok
```
*(O skip é legítimo e pré-existente — teste do F0-03 que pula quando a lib
GCS está presente.)*

### 2.5 Auditoria pyarrow das saídas (as 4 camadas + jsonl)

| | ① real | ② pop | ③ surrogate | ④ timing | jsonl |
|---|---|---|---|---|---|
| **c154 MMF1** | 61 (21 init + 40 opt) | 1.702 / 42 ger | 410 = 41×10 | 41 pts (n 21→61) | 86 recs |
| **c154 DTLZ2** | 371 (131 + 240) | 60.622 / 242 ger | 14.460 = 241×60 | 241 pts (n 131→371) | 750 recs |
| **c154b MMF1** (rota b) | 61 (21 + 40) | 1.702 / 42 ger | 410 = 41×10 | 41 pts | 85 recs |

Em **todos**: `solution_id` único ✓ · x/f **float32** (D53) ✓ · codec
**ZSTD** ✓ · ③ com μ/σ **finitos e σ>0** ✓ · `pred_tipo='valor'`,
`modelo_flag='GP'` ✓ · `real_solution_id` preenchido em N−1 linhas (o
candidato da iteração cortada pelo hard-stop fica NULL — correto por D61) ·
manifesto `status=ok`, FE exato, `doe_hash` = sidecar.

### 2.6 Verificação de faixa e de commits
```
git show --name-only 925595b + 1641011  →  EXATAMENTE 5 arquivos:
  src/c154_jes.py · src/experiment.py · tests/test_c154.py
  handoff/R2-c154.md · handoff/R2-c154_RELATORIO-EXECUCAO.md
grep proibidos (.m|algorithms/|cards/|artifacts/|SPEC|.lock|anchors|data/)
  → nenhum. OK.
```
⚠ *Nota metodológica:* um `git diff 14b362c..HEAD` hoje **inclui arquivos da
torre**, porque a torre commitou por cima dos meus (v5.2.1/DI-10). A
verificação correta é por commit (acima), e ela está limpa.

---

## 3. O QUE FOI CONSTRUÍDO (visão de engenharia)

**`src/c154_jes.py`** (novo, 667 linhas) — o runner `run_c154`, no molde do
`run_c262`, sobre o harness R2-00 **sem tocar o harness**.

Reuso deliberado do molde (import de `src.c262_qnehvi`, **não cópia**):
`disable_fused_kernel()` (a DEF-L2 que o handoff do c262 mandou replicar —
um teste garante que é a MESMA função), `_fit_models()` (a receita de fit é
idêntica, D44) e `_WallClockProjector` (o teto do piloto).

Próprio do c154: modelo **sem `train_Yvar`** (ruído INFERIDO — a diferença
deliberada vs o c262, B9.x), o pipeline B9.5 nas duas rotas, a box
decomposition + `qLBMOJES("LB")`, o `optimize_acqf` com 5D/1000D do paper, o
**NaN-guard** (§4.2) e a materialização do catálogo de sementes D91 do c154
(usos `0` · `1..S` · `S+1..2S`).

**`src/experiment.py`** — exatamente 2 linhas (a entrada do c154 no
`_DISPATCH_LOADERS` + comentário). Nada mais do arquivo foi tocado.

**`tests/test_c154.py`** (novo, 230 linhas, 9 testes) — encanamento leve
(D97: nada de fidelidade), pulam limpo sem o stack R2.

---

## 4. OS RESULTADOS QUE INTERESSAM À TORRE

### 4.1 O achado 🔴 que teria derrubado o cartão (e a guarda que instalei)

**Sintoma:** DTLZ2, iteração 11, determinístico (reproduzido 2×) —
`RuntimeError: probability tensor contains inf, nan or element < 0`, dentro
do `torch.multinomial` da seleção Boltzmann de candidatos iniciais do
`optimize_acqf`. **O run morria** (footer `failed` gravado — o D23/D60
funcionou, mas o run se perdia).

**Causa (leitura do fonte oficial + diagnóstico dirigido):** o estimador
**LB** do JES calcula a covariância M×M por **moment-matching** da
distribuição truncada (`mom2 − mom1·mom1ᵀ`), que **não é garantidamente
PSD** ⇒ `torch.logdet` devolve NaN mesmo com o jitter 1e-6 que o próprio
BoTorch adiciona (e cujo comentário no fonte diz *"provavelmente nem é
necessário"*). O `boltzmann_sample` do BoTorch trata `+inf` (baixa o η num
laço) mas **não trata NaN/−inf**, que envenenam o `standardize` e explodem no
`multinomial`. É raro: ~1 ponto em 10⁴.
⚠ O hazard que o card ANTECIPAVA era outro (*"logdet inicial sem jitter; q=1
mitiga"* — o termo INICIAL). O que mordeu foi o termo **condicional**.

**Remédio (encanamento, NÃO mecanismo):** (i) os ICs são gerados pelo
`gen_batch_initial_conditions` **OFICIAL**, mas com a acqf embrulhada num
`_NaNGuardedAcqfICs` que troca não-finito por **pior-finito−1 SÓ na
PONTUAÇÃO** dos raw samples (o ponto nunca é escolhido como IC; se TUDO for
não-finito, o `Ystd==0` do código oficial cai sozinho no fallback aleatório);
(ii) o escolhido é o **argmax nan-masked** dos restarts; todos não-finitos ⇒
pára-e-loga (D81). **A acqf CRUA segue intocada** na otimização L-BFGS e em
todos os valores exportados/logados.

**Frequência real medida:** DTLZ2 → 23× `nan_guard_ics` + 1×
`nan_guard_argmax` em 240 iterações. **ZDT1 (D=30) → 8 disparos em apenas 10
iterações.** Sem a guarda, **o ZDT1 do c154 seria praticamente irrodável**.
Cada disparo vai para o `.jsonl` (§17.5: "cada guarda loga quando dispara").

### 4.2 A B9.5 — resolvida, e por que NÃO parei para perguntar

O prompt mandava parar se a B9.5 exigisse decisão do autor. Verifiquei a
precedência (D83) e ela **já estava fechada**: a **D75** diz *"§6.4 é a DONA;
`random_search` principal + `nsgaii(100,500)` como checagem de fidelidade;
pop-250 morta (fecha a DEF-B9.5)"*, e o **§O5** classifica o pipeline do JES
como item **[IMPL]** que *"o executor resolve na implementação/piloto — não
exige martelo do autor"*. A tarefa delegada era **medir o gap**, não escolher.

**O gap (MMF1, semente 0, mesmo DoE, mesmas sementes):**

| | rota (a) produção | rota (b) paper-faithful | razão |
|---|---|---|---|
| wall total | **96,4 s** | **1.703,3 s** | **×17,7** |
| estágio de caminhos (S=10) | 21,7 s | 1.633,7 s | ×75 |
| % do wall em caminhos | 26% | **99%** | — |
| FE / iters / CP-init | 61 / 41 / ✓ | 61 / 41 / ✓ | = |
| acqf escolhido (1ª → última) | 1,541 → 1,053 | 1,295 → **0,079** | — |

**Leitura (medição, não juízo — D97):** a rota (b) resolve os Pareto samples
muito melhor (o ganho de informação cai **uma ordem de grandeza** ao longo do
run, como o paper prevê), mas custa ×17,7 **em D=2**, o caso mais barato do
grid. **O piloto CONFIRMA a D75 como escrita**: produção = (a).
*Insumo p/ a dissertação (§20/Anexo J):* registrar que o JES da bateria usa o
helper default do BoTorch (Sobol-1024 + truncagem por slice), não o
NSGA-II+HV-greedy do paper — com este gap como evidência do custo que
justificou a escolha.

### 4.3 ⭐ A curva §17.6 e o custo (o dado-alvo do piloto)

| Run (semente 0) | fits | n | marcos (n, t_fit) | expoente | wall | fit / busca / aval |
|---|---|---|---|---|---|---|
| MMF1 (a) D=2 M=2 | 41 | 21→61 | (21, 0,40s) (61, 0,23s) | ~plano (overhead domina) | **96s** | 8s / 84s / 0,001s |
| MMF1 (b) D=2 M=2 | 41 | 21→61 | (21, 0,16s) (61, 0,19s) | ~plano | **1.703s** | 7s / 1.651s / 0,001s |
| DTLZ2 (a) D=12 M=3 | 241 | 131→371 | (131, 0,98s) (251, 3,73s) (371, **8,01s**) | **n^1,87** | **14h37** | 903s / 51.674s / 0,02s |
| ZDT1 (a) D=30 M=2 | 10 (parcial) | 329→338 | (329, 1,76s) (338, 3,60s) | **n/d** (range curto) | abortou 1h32 | 24s / 5.488s / — |

**Conclusões p/ o M7 (medição, não decisão):**
- **O JES confirma o rótulo de CURINGA DE CUSTO da SPEC.** DTLZ2 em
  **14h37 contra 2h31 do c262** no MESMO problema/semente — **×5,8**.
- **A causa NÃO é a parede O(n³) do fit.** O fit é 903s (1,7% do wall); o
  estágio de caminhos é 215s (0,4%). **A BUSCA — avaliar a aquisição — é
  98,3%.** Motivo: o custo por ponto escala com **S=10 modelos
  CONDICIONADOS** × M objetivos × J caixas, e a receita do paper avalia
  `1000·D` raw samples + `5·D` restarts L-BFGS por iteração. É o paper, não
  ineficiência nossa.
- **A parede do fit existe** (n^1,87 no range medido) mas é **coadjuvante**
  no c154: em n=371 o fit final custa 8s contra ~210s de busca na mesma
  iteração.
- ⚠ **O expoente do ZDT1 NÃO é estimável** (n variou só 2,7%: 329→338); a
  regressão devolveu ruído (−0,32) e seria desonesto reportá-la como curva.
- **Extrapolação bruta (1 core, Mac):** DTLZ2 ≈ **18,3 dias·core/problema**
  (30 sementes); ZDT1 ≈ **121 dias·core/problema**. **O dimensionamento de VM
  da R2 (HANDOFF §7.5) deve ser feito pelo c154, NÃO pelo c262.**

### 4.4 O ZDT1 e o teto de 8h

```
wall_projection_abort: it=10 · fe=339/929 · elapsed=5.514s (1h32)
                       proj_restante=345.554s (96h) · max_wall=28.800s
footer: status=failed
```
Abortou **LIMPO**, como o cartão mandou: só o `.jsonl` no disco (41 recs, com
a curva parcial e o evento de aborto), **sem parquets órfãos nem manifesto
`ok` mentiroso** (o `write_run_outputs` nunca roda no aborto). Custo medido:
**549 s/iteração**, dos quais 99,5% é busca. **Completar o ZDT1 é decisão de
orçamento do autor no M7** (D81 — eu não decido isso).

⚠ **Lacuna do projetor herdado (do c262), que a torre pode querer fechar:**
ele só projeta depois de **10 amostras** de iteração e **não testa `elapsed`
isoladamente**. Aqui não mordeu (medi a cadência — 8,2 min/iter — e confirmei
que a it 11 chegaria muito antes das 8h; chegou em 1h32). Mas se um problema
tiver ~45 min/iteração, o run **fura o teto sem o projetor disparar**. Não
mexi: o projetor é código do c262, fora da minha faixa.

---

## 5. INTERFACE COM AS DECISÕES QUE A TORRE TOMOU **DURANTE** ESTA SESSÃO

### 5.1 DI-09 (sonda de assertividade) — não afeta este cartão
O cronograma do autor diz textualmente: *"Retrofit-Python (c262 + **c154** +
export.py + helper no harness) = **cartão pequeno logo após o commit do
c154**"*. Este cartão entrega o JES **sem** a sonda, corretamente.

**⚠ AÇÃO RECOMENDADA E URGENTE (a torre deve providenciar):** o invariante-
gate da DI-09 é a **NÃO-PERTURBAÇÃO** — *"a ① do run pós-retrofit deve ser
IDÊNTICA à do piloto pré-retrofit"*. **Os 3 runs desta sessão SÃO essa linha
de base** e estão em diretório **gitignored**:
```
data/experiments/main/c154/exp_main_c154_MMF1_0__real.parquet    (61 linhas)
data/experiments/main/c154/exp_main_c154_DTLZ2_0__real.parquet   (371 linhas)
data/experiments/main/c154b/exp_main_c154b_MMF1_0__real.parquet  (61, rota b)
```
**Copiar esses arquivos para um lugar seguro ANTES do retrofit.** O do DTLZ2
custou **14h37** para produzir; sem ele, a prova de não-perturbação exigirá
re-rodar isso.
*Nota técnica p/ o cartão de retrofit:* o preditor do c154 é determinístico
sob `no_grad` (não há o hazard de MC-dropout do e7), **mas** o laço depende
do RNG global do torch via `manual_seed` por iteração — **a sonda precisa de
save/restore do RNG torch**, ou a trajetória muda e o gate reprova.

### 5.2 CONTRATO_DE_DADOS v5.2.1 — publicado DEPOIS do meu código
A torre commitou (`c2cf716`) a SPEC v5.2.1 com um `CONTRATO_DE_DADOS.md` de
precedência. **Auditei o c154 contra ele agora.** Resultado em §7.

---

## 6. ⚠ AS DEFINIÇÕES EM ABERTO — A TORRE DEVE LEVANTAR COM O AUTOR

Nenhuma bloqueou o cartão. Todas são **encanamento** (D97 intacto: nenhuma
decide fidelidade). Ordenadas por **prioridade**.

### 🔴 ALTA — decidir antes da bateria M8

**D-1. O NaN-guard do estimador LB (§4.1) — RATIFICAR.**
É código NOSSO no caminho de seleção de candidatos de um algoritmo oficial.
Sem ele o cartão não fecha e o ZDT1 é irrodável (8 disparos em 10 iterações).
Alternativas, se o autor preferir outra rota: (a) trocar `estimation_type`
para `"LB2"` (variante diagonal, sem o `logdet` M×M — mas foge da
recomendação explícita do paper); (b) aumentar o jitter (mexe na numérica do
algoritmo — **eu não faria sem ordem do autor**). **Minha recomendação:
manter como está** (a guarda é de SELEÇÃO, a acqf crua é intocada, e cada
disparo é auditável no jsonl).

**D-2. O custo do c154 na bateria — decisão de ORÇAMENTO/dimensionamento.**
DTLZ2 ≈ 18,3 dias·core/problema; ZDT1 ≈ 121 dias·core/problema. O
dimensionamento da R2 deve ser feito pelo c154. *Alavancas, da menos à mais
danosa:* (a) paralelizar por semente (embaraçoso, **não muda nada** do
algoritmo — a via natural); (b) `raw_samples` 1000·D → 500·D (desvio do
paper; mediria-se o gap num piloto); (c) reduzir S=10 (**mexe no mecanismo —
NÃO recomendo**).

**D-3. O ZDT1 completo — completar ou documentar o corte?** (M7)
Opções: (a) rodar sem teto na VM (~4 dias·core/semente); (b) aceitar e
documentar; (c) reduzir `raw_samples` (ver D-2).

**D-4. Conformidade com o CONTRATO_DE_DADOS v5.2.1 (§7) — 2 gaps.**
As colunas ④ novas e 2 campos do jsonl. Detalhe e recomendação em §7.

### 🟡 MÉDIA — ratificar quando conveniente

**D-5. A escada de fallback do `RuntimeError`** `(1024,10)→(2048,20)→
(4096,40)`. A L.11 exige "try/except obrigatório" mas **não diz o que fazer
depois** — a escada é definição MINHA. Racional: o erro do helper significa
"achei menos de P pontos não-dominados"; mais amostras é a resposta direta e
preserva a semântica. **Disparos nos 4 runs: ZERO** (só exercitada em teste
com mock). Ratificar ou substituir.

**D-6. A likelihood do ruído inferido.** A L.11 manda "não fixar
`train_Yvar`" e nada mais. Usei o **default do 0.18.1** (prior LogNormal,
piso 1e-4; noise ajustado ~3e-4). ⚠ **Assimetria deliberada a registrar:** o
**kernel** usa a rota Gamma-legada (`get_matern_kernel_with_gamma_prior`,
herdada do c262/D30) enquanto a **likelihood** usa o default moderno.
Ratificar ou uniformizar.

**D-7. `init_batch_limit=256` no c154 vs `32` no c262.** Divergência
consciente, com benchmark: valor da acqf **idêntico** em 32/256/1024
(numericamente neutro — é chunking de avaliação), e 32→256 poupa ~14% da
busca (que é 98% do custo do c154). Ratificar; se a torre uniformizar em 32,
o custo é ~14% a mais.

**D-8. A lacuna do projetor de wall-clock (§4.4)** — herdado do c262: só
projeta após 10 iterações e não testa `elapsed` isoladamente. Não morde hoje;
fechar antes da M8 seria barato (um teste de `elapsed`). **Fora da minha
faixa** (código do c262).

### 🟢 BAIXA — registro/doc-sync

**D-9. Doc-sync da S.3/L.11:** `MatheronPathModel(seed=)` **não existe** no
0.18.1 (a assinatura real é `get_matheron_path_model(model, sample_shape,
ensemble_as_batch)`), e `sample_optimal_points` também não expõe seed.
**Verifiquei** que o desenho dos caminhos e o Sobol do `random_search`
consomem o **RNG global do torch**, então materializei o `hs` do catálogo
D91 como `torch.manual_seed(hs)` antes de cada uma das S chamadas
(`num_samples=1` por chamada) — determinismo confirmado bit-a-bit.

**D-10. Ausência de `uso_id` para o seed do `optimize_acqf` no catálogo D91
do c154.** O catálogo do c262 previa (uso 2); o do c154 (`0` · `1..S` ·
`S+1..2S`) **não prevê**. Mantive o artefato à risca (os ICs saem do RNG
global, determinístico e ancorado nos `manual_seed`). Se a torre quiser
paridade com o c262, é **uma linha no `seeds.json`** — mas isso ALTERA um
artefato compartilhado, **fora da minha faixa**.

**D-11. O token `c154b`.** Namespace de ALGORITMO para a rota (b) do piloto
(precedente: `stubpy` do R2-00), porque `naming.check_exp` só aceita
`{main,off,batch,sweep-*}` (D55) e criar um token de experimento novo exigiria
tocar módulo fora da faixa. Mantém `alg_id=10` e as mesmas sementes ⇒
comparação pareada. **Não é config do estudo** — confirmar que a torre não o
quer no `runs_matrix`.

---

## 7. CONFORMIDADE COM O `CONTRATO_DE_DADOS` v5.2.1 (auditoria feita AGORA)

A torre publicou o contrato **depois** do meu código. Auditei:

| Exigência do contrato | c154 | Observação |
|---|---|---|
| ① ②③ schemas, float32, ZSTD, `solution_id` | ✅ | auditado (§2.5) |
| Manifesto: `status`, `maxfe/fe_final/n_geracoes`, `doe_hash`, `algo_version/env`, `fit_series`, `cache_hits`, `params` | ✅ | auditado |
| **Manifesto: bloco `timing` OBRIGATÓRIO** (*"estava ZERADO em 10/12 — auditoria da torre"*) | ✅ **CONFORME** | **o c154 é um dos que NÃO estão zerados.** Verificado: `tempo_total_s`, `tempo_fit_surrogate_s`, `tempo_busca_s`, `tempo_aval_real_s` todos populados nos 3 runs |
| ④ `tempo_busca_s` **por geração** (era opcional/NaN → agora OBRIGATÓRIO) | ❌ **GAP** | a coluna existe mas está **NULL nas 241 linhas**. ⚠ **O DADO EXISTE**: o jsonl tem `t_busca_s` em 240/241 decisões — é **backfill trivial**, não re-execução |
| ④ **`tempo_pred_sonda_s`** (coluna nova) | ❌ | é do retrofit DI-09 (coluna da sonda, que ainda não existe) |
| ④ **`tempo_geracao_s`** (coluna nova — wall total da geração) | ❌ | idem; o dado parcial existe no jsonl |
| jsonl c154: rota B9.5; S fronts; acqf; restarts | ✅ | logados (inclusive os **valores** dos S fronts em f) |
| jsonl c154 (novo): **`acqf_todos_restarts`** | ✅ | já logo `acqf_restarts` (240/241) — só o NOME difere; confirmar se a torre quer renomear |
| jsonl c154 (novo): **`n_baseline`** | ⚠ **N/A?** | é conceito do qNEHVI (baseline podado). **O JES não tem `X_baseline`** — a torre deve confirmar o que quer aqui para o c154 (talvez `n_train`, que eu já logo) |
| jsonl c154 (novo): **`mll_final`** | ❌ **GAP** | não logo o valor final da MLL. Adição pequena (~3 linhas no `_fit_models`) |
| `sigma_dict` (DEF-C4) no manifesto | ❌ | não existia quando implementei; vale para os 21 configs — item do retrofit, não só do c154 |

**Recomendação da minha parte:** esses gaps são **exatamente o escopo do
"cartão pequeno de retrofit-Python (c262 + c154 + export.py + helper)"** que o
autor já agendou para depois deste commit. **Não recomendo abrir um cartão
separado só para o c154** — o `tempo_busca_s`/`tempo_geracao_s` são
mudanças no **harness/export compartilhado** (fora da minha faixa de então) e
devem ser feitas uma vez, para os dois algoritmos da R2, no cartão de
retrofit. **Ponto importante e favorável:** como o dado já está no jsonl, o
retrofit pode fazer **backfill dos runs existentes** em vez de re-rodar as
14h37 do DTLZ2 — vale instruir o cartão de retrofit a fazer isso.

---

## 8. O QUE A TORRE DEVE FAZER A SEGUIR (checklist)

1. **Marcar `R2-c154` em `cards/INDEX.md`** (⬜ → ✅). Não toquei —
   paralelismo de faixas.
2. **Preservar os 3 `__real.parquet`** antes do retrofit DI-09 (§5.1) —
   **o mais urgente**, porque são gitignored e o DTLZ2 custou 14h37.
3. **Levantar com o autor as 11 definições da §6**, priorizando D-1
   (NaN-guard), D-2 (custo/dimensionamento), D-3 (ZDT1) e D-4 (contrato).
4. **Instruir o cartão de retrofit-Python** a: (a) preencher
   `tempo_busca_s`/`tempo_geracao_s` no ④; (b) fazer **backfill** dos runs
   existentes a partir do jsonl (evita re-rodar 14h37); (c) decidir o que é
   `n_baseline` para o JES; (d) adicionar `mll_final`; (e) `sigma_dict`.
5. **Considerar fechar a lacuna do projetor de wall-clock** (D-8) antes da M8.

---

## 9. RESUMO EM UMA LINHA

**O cartão R2-c154 está COMPLETO e VERDE** (2 gates exit 0, regressão intacta,
91 testes OK, 2 commits limpos na faixa); **a B9.5 foi resolvida e medida**
(a D75 confirmada: ×17,7 de custo na rota paper-faithful); **um achado 🔴 de
NaN no estimador LB foi diagnosticado e contido** por guarda logada (sem ela
o ZDT1 é irrodável); **o JES confirmou-se o curinga de custo** (×5,8 o c262,
98% em busca, ~121 dias·core/problema no ZDT1); e **restam 11 definições em
aberto** (§6) mais **4 gaps de conformidade** com o contrato v5.2.1 (§7), que
pertencem ao cartão de retrofit já agendado pelo autor.
