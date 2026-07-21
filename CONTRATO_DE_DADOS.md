# CONTRATO DE DADOS — todos os outputs da execução dos 21 configs
### O documento-referência definitivo dos dados persistidos (v1.1 · 2026-07-19 — lote DI-13)

> **O que é.** A consolidação DIDÁTICA e COMPLETA de tudo que cada execução persiste: qual informação,
> quando é coletada, em que formato, e que análise alimenta. Junta: o §17 da SPEC (o contrato
> normativo, com os mocks), as decisões DI-08/DI-09/DI-10 (camada `__final`, sonda canônica,
> enriquecimento do jsonl) e as formalizações do autor de 2026-07-18. **Precedência:** a SPEC
> (§17/§S.7) segue sendo a fonte normativa; este documento a REPLICA e EXPANDE — em divergência,
> vale a SPEC (e reporte). Mantido pela torre; sessões de retrofit/R3 leem este documento como
> contrato executável.

---

## 0. Visão geral — o que UM RUN produz

**1 run = 1 tripla `(algoritmo, problema, semente)` → 6–7 arquivos.** Bateria = 16.500 runs.
`run_id = {exp}_{alg}_{problema}_{semente}` (D55); pasta `data/experiments/{exp}/{alg}/`;
base `exp_{run_id}` + sufixo de camada (§17.7):

| # | Arquivo | O quê | Quando coleta | Formato |
|---|---|---|---|---|
| ① | `__real.parquet` | TODA avaliação real (as 31D−1) | a cada FE | Parquet float32/int32, zstd (MATLAB: brotli, re-encodado na consolidação) |
| ② | `__pop.parquet` | membership população×geração | fim de cada geração | Parquet (ints) |
| ③ | `__surrogate.parquet` | TODA predição do modelo (busca **+ SONDA**) | a cada predição decisão-relevante + sonda | Parquet float32 |
| ④ | `__timing.parquet` | custo por geração (fit/busca/sonda/geração) | a cada geração/retreino | Parquet |
| ⑤ | `.manifest.json` | certidão do run (status/params/hashes/`sigma_dict`/timing agregado) | no fim (escrita atômica D58) | JSON |
| ⑥ | `.jsonl` | o FILME das decisões (1 evento/linha, streaming) | DURANTE o run | JSON Lines |
| ⑦ | `__final.parquet` | **SÓ OFFLINE (DI-08):** o ND final avaliado 1× na função real | pós-hoc (Python canônico) | Parquet |

**Fluxo de leitura para análise:** ① = métricas oficiais (IGD+/HV/…, §12) · ①+② = dinâmica da
busca · ①+③ = erro/calibração do surrogate ("erro de fantasia") · ③(sonda) = comparação
entre modelos na régua fixa · ④ = custo/escalabilidade · ⑥ = fidelidade de mecanismo (D97) ·
⑤ = a linha da tabela de execuções.

**Diretriz-mãe (SPEC §17):** *"persistir toda avaliação de toda solução em cada ciclo — real E
surrogate — para reconstruir exatamente como cada busca funcionou (o 'filme')."* Salvar TUDO,
sem teto (D54), float32 SEM arredondamento (D53), 100% das gerações (D33).

---

## 1. Camada ① — Catálogo REAL (`__real.parquet`)

**Semântica (SPEC §17.1.1):** as soluções ÚNICAS avaliadas na função verdadeira (**dedup por X
float64 bit-a-bit em runtime — D57**; a fitness real é determinística). *Poucas e preciosas* —
exatamente **31D−1 por run** (init 11D−1 do DoE + até 20D infills). **As métricas oficiais saem
SÓ daqui.**

**Schema real (verificado nos dados):**
```
algoritmo | problema | semente | solution_id (chave int32) | x0..x{D-1} (float32) |
f0..f{M-1} (float32, verdadeiro) | fe_index (int32, 0-based: quando foi avaliada) | fase (init|opt)
```
**Mock da SPEC (DTLZ2, M=2, D=6, semente 7):**

| algoritmo | problema | semente | solution_id | x⃗ (D=6) | f⃗ verdadeiro (M=2) |
|---|---|---|---|---|---|
| b3 | DTLZ2 | 7 | R-001 | [.312,.881,.124,.503,.090,.774] | [1.834, 2.101] |
| b3 | DTLZ2 | 7 | R-002 | [.620,.140,.402,.281,.912,.331] | [2.410, 1.552] |
| b3 | DTLZ2 | 7 | R-042 | [.500,.492,.500,.511,.500,.021] | [1.021, 1.010] |

- Formato IDÊNTICO nos 21 configs. `fase=init` = as 11D−1 do DoE compartilhado (D88 — bit-exato
  ao artefato `data/doe/`, provado por hash no manifesto); `fase=opt` = os infills.
- **Offline (5 configs):** a ① = o DATASET completo (D90) — o orçamento É o dataset; CP com
  x_hash E f_hash do sidecar.
- ⚠ Regras de leitura (R4): dedup/joins por `solution_id`, NUNCA pelo X armazenado (float32 pode
  colidir pontos float64 distintos — provado); cache-hits (D89) não geram linha (0 FE).
- **Alimenta:** IGD+/HV/GD/spacing finais + trajetória (por `fe_index`); a régua vs pisos; o
  denominador-verdade de TODA análise de erro do surrogate.

## 2. Camada ② — População real por geração (`__pop.parquet`)

**Semântica (SPEC §17.1.2/D31/D32):** membership — quais soluções REAIS o algoritmo mantinha em
cada geração. Só ponteiros (X/F vêm do ① por join): `algoritmo|problema|semente|geracao|solution_id`.
100% das gerações. **Mock da SPEC:**

| algoritmo | problema | semente | geracao | solution_id |
|---|---|---|---|---|
| b3 | DTLZ2 | 7 | 1 | R-001 |
| b3 | DTLZ2 | 7 | 1 | R-002 |
| b3 | DTLZ2 | 7 | 5 | R-001 |
| b3 | DTLZ2 | 7 | 5 | R-042 |

*(R-001 nas ger. 1 E 5 = sobreviveu; R-002 sumiu = descartado.)*
- Nº de gerações NÃO é fixo (depende de N_efetivo e de cache-hits — ex.: moead/ZDT1 fechou 39).
- **Offline:** ② = SÓ os membros do DATASET na pop selecionada (DI-03); a série completa (incl.
  zeros) está no jsonl (`n_ds_membros`).
- **Alimenta:** sobrevivência/descarte, diversidade, colapso de arquivo; a reconstrução do estado
  do arquivo em qualquer geração (insumo do rótulo-verdadeiro dos classificadores, DI-09/A3).

## 3. Camada ③ — Tabela SURROGATE (`__surrogate.parquet`) — A TABELA CENTRAL

**Semântica (SPEC §17.1.3/D35/DEF-C1):** cada avaliação do modelo por (candidato, geração), SEM
dedup (a predição é DATADA — muda a cada retreino). **Tabela ÚNICA com colunas opcionais** para os
3 tipos de surrogate (regressor μ/σ · classificador classe/score · híbrido) — o join com o ① é
direto via `real_solution_id`.

**Schema (pós-retrofit DI-09 — as 2 colunas novas em negrito):**
```
algoritmo | problema | semente | regime ∈ {busca…, SONDA} | geracao | x0..x{D-1} |
real_solution_id (liga ao ① se o candidato foi avaliado; senão NULL) |
mu_0..mu_{M-1} | sigma_0..sigma_{M-1} | pred_tipo ∈ {valor,classe,score,híbrido} |
pred_classe | pred_score | pred_confianca ∈[0,1] | modelo_flag |
espaco_modelo | transf_tipo | transf_params            ← DEF-C3 (cru+transformado)
**fe_treino_max (int32)**  ← DI-09/A1: maior fe_index no TREINO do modelo no momento do fit
```
**Mock da SPEC (a saída depende do tipo — DEF-C1):**

| alg | ger | x⃗ | real_sol_id | pred_tipo | μ₁ | μ₂ | σ₁ | σ₂ | classe | score | conf | modelo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| c262 | 3 | [.312,.881,…] | R-001 | valor | 0.420 | 0.710 | 0.080 | 0.050 | ∅ | ∅ | ∅ | GP |
| c262 | 4 | [.312,.881,…] | R-001 | valor | 0.390 | 0.735 | 0.061 | 0.041 | ∅ | ∅ | ∅ | GP |
| b4 | 5 | [.20,.75,…] | ∅ | classe | ∅ | ∅ | ∅ | ∅ | bom | ∅ | 0.830 | FNN |
| c217 | 5 | [.20,.75,…] | ∅ | score | ∅ | ∅ | ∅ | ∅ | ∅ | +1 | 0.860 | PNN-par |
| e74 | 5 | [.48,.51,…] | ∅ | híbrido* | 1.050 | 0.920 | ∅ | ∅ | nível_2 | ∅ | 0.740 | RBF+PNN |

*\*Na implementação real do e74, DI-03 ratificou `pred_tipo` POR LINHA (classe|valor) — nunca
"híbrido" numa linha só; o mock da SPEC ilustra o schema, o `sigma_dict` do manifesto manda.*

**Quem preenche o quê (SPEC §17.2, leitura por tipo):**
- **Regressor** (b3, e7, c141-RBF, c238, c262, c154, e81, c149, c311, e103, b5): `mu_*`
  (+`sigma_*` se probabilístico); RBF puro dá μ SEM σ (a distinção VAR-GP × ERR-EMP).
- **Classificador de classe (b4):** `pred_classe`=bom/ruim, `pred_confianca`=L (sigmoide) — a
  classe decide QUEM GASTA FE, não quem entra no front. (e74-PNN: classe = nível de não-dominância.)
- **Score par-a-par (c217, c122):** `pred_score` = a nota agregada (ternário {−1,0,+1} no c217;
  e(z) no c122); NÃO se grava O(n²) comparações (só no piloto — DEF-C2); confiabilidade
  (Error1/Error2) no jsonl.
- **b1 (ParEGO) — caso especial D47:** mono-output — modela o ESCALAR de Tchebycheff (λ sorteado
  por iteração), não os objetivos. `mu_0/sigma_0` = o escalar; C3 carrega λ + min/max + Gbest.
  *Limitação inerente: candidato nunca-avaliado só tem o escalar (não há μ por objetivo).*
- **Granularidade (DEF-C2):** EA → a população SELECIONADA por geração; BO com EA interno →
  a população final do otimizador de aquisição por iteração; BoTorch → os candidatos dos
  restarts; offline → a pop-surrogate do MOEA interno, todas as gerações.
- **Espaços (DEF-C3):** onde o modelo opera transformado (b1 tcheby, c238 minmax, e7 translação,
  e103/c149 z/…): gravam-se os DOIS espaços + parâmetros por iteração (`transf_*`) — a análise
  não inverte nada.
- **`sigma_dict` (DEF-C4, no manifesto):** o dicionário por algoritmo do que cada coluna significa
  — LEITURA OBRIGATÓRIA antes de usar a ③ de um algoritmo.

### 3.1 O regime SONDA (DI-09/A2 — formalizado pelo autor em 2026-07-18)

**A decisão:** *"cada algoritmo prevendo OS MESMOS 2000 pontos, nos mesmos problemas, ao longo das
gerações — a comparação perfeita e justa de qual modelo é melhor"* — e busca + sonda na MESMA
tabela ③, diferenciadas pela coluna `regime`.

> **[DI-13.5 · 2026-07-19] ATUALIZAÇÃO:** o artefato passou a ter **S=20.000 pontos** e serve aos
> DOIS regimes, porque a sequência de Sobol é **ANINHADA** (provado: |dif|=0):
> **ONLINE lê as 2.000 primeiras** (a cada k=2 gerações) · **OFFLINE lê as 20.000** (1× por modelo
> treinado — o modelo é fixo, então cabe muito mais ponto pela mesma análise). A fatia online é
> BIT-IDÊNTICA a uma sonda de 2.000 ⇒ a régua é a MESMA na faixa compartilhada e os runs online já
> retrofitados NÃO precisam ser refeitos (`x_hash_online` == hash antigo em 25/25 problemas).
> O sidecar (v2) traz `S`, `S_online`, `x_hash`/`f_hash` (artefato) e `x_hash_online`/`f_hash_online`
> (a fatia) — cada regime confere o SEU hash. Nos blocos OFFLINE, `geracao = NULL` (o modelo treina
> ANTES do laço; não há geração a que pertencer).

- **OS PONTOS SÃO FIXOS E ÚNICOS POR PROBLEMA — para sempre, para todos os algoritmos, em
  todas as gerações e sementes.** Definição EXATA (sem margem para erro): o artefato
  **`data/sonda/sonda_{problema}.parquet`**, gerado UMA vez por `scripts/gen_sonda.py`:
  S=20.000 pontos **Sobol embaralhado** (online usa os 2.000 primeiros) (`scipy.stats.qmc.Sobol(d=D, scramble=True,
  seed = SeedSequence((4242, problema_id)) truncada a 32 bits)`), re-escalados aos bounds NATIVOS,
  com **f verdadeiro pré-computado** via `src/problems.py` (float64) — colunas
  `sonda_id (0..1999) | x0..x{D-1} | f0..f{M-1}` + sidecar `sonda_{problema}.manifest.json` com
  o **sha256 do array** (o CP da sonda). **Nenhum algoritmo GERA pontos de sonda — todos CARREGAM
  este artefato e o instrumentador confere o hash no arranque** (mesma disciplina do DoE D63/D87).
  Custo de FE: **ZERO** (funções analíticas avaliadas fora do orçamento — exceção contábil
  documentada, precedente DI-08).
- **Cadência:** ONLINE = a cada **k=2** gerações/iterações + SEMPRE a 1ª e a última;
  OFFLINE = **1× por modelo treinado** (o modelo não muda — e103 grava 2 blocos: Kriging e RBFN).
  Cada bloco de sonda grava também o `fe` corrente no jsonl (evento `sonda`) — **o eixo de
  comparação entre algoritmos é o FE consumido** (as "gerações" de algoritmos diferentes não são
  alinhadas entre si; o FE é).
- **Como grava:** ⟦DI-13.5 — corrigido: dizia "2000 linhas" sem qualificar o regime⟧ **ONLINE grava 2000 linhas** (`geracao`=corrente) e **OFFLINE grava 20.000 linhas** (`geracao`=**NULL** — o modelo treina antes do laço) na ③ com `regime='sonda'`, `fe_treino_max`,
  `real_solution_id=NULL`, e a MESMA semântica de saída que o modelo daquele algoritmo produz
  (tabela §3.2). O gabarito (f verdadeiro) NÃO se repete na ③ — está no artefato, join por
  `sonda_id`? **Não**: a ③ não tem coluna sonda_id; o join é POR POSIÇÃO (as 2000 linhas de cada
  bloco preservam a ORDEM do artefato — invariante do writer) — documentado aqui e no accept.
- **🔴 INVARIANTE DE NÃO-PERTURBAÇÃO:** a sonda NÃO PODE alterar a busca. Preditores estocásticos
  (MC-dropout do e7!) exigem save/restore do RNG em volta da predição. Prova objetiva por config:
  a ① do run com sonda é IDÊNTICA à do run sem (mesma semente ⇒ mesma trajetória).

**§3.2 Semântica da sonda por config (o que as 2000 linhas carregam):**

| Config | O modelo responde | Colunas preenchidas |
|---|---|---|
| b3, c141, e7, c238, e103, c311, b5, c149, e81, c262, c154 | μ (e σ onde houver) POR OBJETIVO | mu_*/sigma_* (+C3 se espaço transformado) |
| b1 | o ESCALAR Tchebycheff com o λ DA ITERAÇÃO corrente | mu_0/sigma_0 + C3{λ,min/max,Gbest} |
| c217 | score ternário do ponto vs a referência corrente (Pmid) | pred_score + pred_confianca(Error1) |
| b4 | classe bom/ruim vs o arquivo corrente + L | pred_classe + pred_confianca |
| e74 | as DUAS cabeças: nível PNN (linha classe) + μ RBF (linha valor) | 2×2000 linhas (pred_tipo por linha) |
| c122 | e(z) da EDN par-a-par **vs a POPULAÇÃO SELECIONADA corrente (N=11 em M=2 / 15 em M=3) [P2/DI-16.2]** — referência de tamanho FIXO (parâmetro do próprio algoritmo) ⇒ o score é comparável entre gerações, sementes e configs; é também o contexto REAL em que o modelo decide na busca. Logar `n_ref` no jsonl | pred_score + pred_confianca(max-softmax) |
| pisos **ONLINE** (4) | — NÃO TÊM SONDA (**sem modelo**) | — |
| piso **OFFLINE** (moead_media) | **TEM SONDA [P1/DI-16.1]** — ele TREINA um GP (Kriging) e otimiza sobre a MÉDIA: μ por objetivo, **σ NULL** (é o "b5 sem σ") | mu_* preenchido; sigma_* NULL |

- **Alimenta:** WAPE/erro global comparável entre os 17 · curva "o surrogate melhora com as
  épocas?" pareada com IGD+×FE (a figura-síntese) · calibração em região neutra · rótulo
  verdadeiro dos classificadores por construção · acurácia/precision/recall/F1/AUC por geração.

### 3.2 Sonda × previsões da busca — por que AS DUAS (autor, 2026-07-18)

| | SONDA (`regime='sonda'`) | BUSCA (regime atual) |
|---|---|---|
| Pergunta | "Quão bom é o MODELO?" | "Quão boas foram as DECISÕES?" |
| Amostra | fixa, neutra, idêntica p/ todos | enviesada DE PROPÓSITO (onde o algoritmo aposta) |
| Comparável entre algoritmos | SIM, diretamente | não (pontos diferentes) |
| Verdade | no artefato (por posição) | via `real_solution_id`→① (só os avaliados) |
| Análises | WAPE/acurácia global; curva por época; calibração global | erro no ponto escolhido; Kendall-τ ranking; contrafactual greedy-μ; acerto→consequência |

**O insight:** um surrogate pode ser globalmente medíocre e localmente excelente (ou o inverso) —
a dissociação entre as duas medidas é ELA MESMA um resultado da tese.

## 4. Camada ④ — TIMING (`__timing.parquet`) — EXPANDIDA (autor, 2026-07-18)

**A decisão do autor:** *"medir tanto o tempo de treinamento dos surrogates a cada geração quanto o
tempo total de execução do algoritmo em cada geração e no total"* — o ④ reúne TODOS os tempos.

**Schema (pós-retrofit; colunas novas em negrito):**

| coluna | significado |
|---|---|
| `run_id` | liga ao manifesto |
| `geracao` / iter | quando (sincroniza com ①②③) |
| `n_acumulado` | nº de pontos reais no TREINO naquele retreino (eixo-x da escalabilidade ⭐) |
| `tempo_fit_s` | treino do surrogate NAQUELE retreino (eixo-y da parede O(n³)) |
| `tempo_busca_s` | aquisição/otimização interna da iteração (OBRIGATÓRIO — era opcional/NaN) |
| **`tempo_pred_sonda_s`** | custo da sonda na iteração (0 quando não roda) |
| **`tempo_geracao_s`** | wall da geração **EXCLUINDO a sonda** = fit+busca+aval+overhead da busca, **SEM** `tempo_pred_sonda_s` (⟦DI-13.10 ratificada; corrigido — dizia "wall TOTAL", que incluiria a sonda⟧). A sonda é instrumentação DESTE estudo e contaminaria a curva de escalabilidade de forma desigual (só roda a cada k=2). Provado nos dados: `fit+busca ≤ tempo_geracao_s` em 100% das gerações, mas `fit+busca+sonda > tempo_geracao_s` exatamente nas gerações com sonda (1.129/1.129, 6 configs MATLAB + os 2 BoTorch). **O projetor de teto, ao contrário, vê o wall CHEIO** (paga a sonda). |

**[DI-13.2] `tempo_fit_s` é NULLABLE:** os **4 pisos ONLINE** não têm surrogate (⚠ **[P1/DI-16.1] o piso OFFLINE TEM** — treina um GP e grava `tempo_fit_s` real) ⇒ gravam `NULL` ("não se
aplica", ≠ `0.0` que significaria "treinou e custou zero" e poluiria a média de custo). O
`tempo_geracao_s` deles é gravado normalmente — é o **custo-baseline** do estudo.

**+ o bloco `timing` do MANIFESTO vira OBRIGATÓRIO nos 21** (estava ZERADO em 10/12 — auditoria
da torre): `tempo_total_s` (wall do run), `tempo_fit_surrogate_s`, `tempo_busca_s`,
`tempo_aval_real_s` (agregados). Pisos: ④ por geração com `tempo_geracao_s` (fit=NULL).
- ⚠ Ressalva de stack (§19): wall MATLAB×Python é confundido pela linguagem — comparar custo
  DENTRO de cada stack; a curva (n_acumulado, tempo_fit_s) é robusta (mede a FORMA, não segundos).
- **Alimenta:** a ⭐ curva de escalabilidade (O(n³) do GP vs ~linear do BNN/treed-GP — c238 n^2,3
  medido vs K-RVEA que CAPEIA o treino em 11D−1 e escapa da parede por construção — achado);
  breakdown fit×busca×aval (c262: busca=89–98%); dimensionamento M7; custo por família (R4).

## 5. Manifesto (`.manifest.json`) — a certidão do run

Chaves (schema v1, verificado): `run_id/exp/alg/problema/semente/regime/q/tier/dist` ·
**`status`∈{ok,retried_ok,failed} + `n_retries` + `stack_trace`** (D23) · `maxfe/fe_final/
n_geracoes` · **`doe_hash`** (o CP-init D87/D88; offline: x_hash+f_hash) · `algo_version/env`
(versões) · **`timing` (OBRIGATÓRIO pós-retrofit)** + `fit_series` · `cache_hits` ·
`fallback_ativado` · `paths` (local+bucket) · `params` (config efetiva do algoritmo) ·
**`sigma_dict`** (DEF-C4 — o dicionário semântico da ③) · timestamps.
- **Alimenta:** a TABELA DE EXECUÇÕES (grid × status × wall × retries — agregação dos manifestos
  via `Scoreboard`; view `progress.py` no M7); auditoria de reprodutibilidade; filtro de
  sucessos/falhas na análise.

> **[DI-13.1] REGRA DA MESCLA (quem escreve o manifesto):** o **runner** grava a certidão RICA
> (doe_hash, fe_final, n_geracoes, timing MEDIDO, fit_series, sigma_dict, bloco sonda); o
> **despachante** (`experiments.py`) **MESCLA** só o que é dele (`status`, `n_retries`,
> `stack_trace`, `tempo_total_despachante_s`) — **nunca reconstrói** (isso apagava tudo) e **nunca
> sobrescreve medida por estimativa**. Se o runner não gravou (run morreu antes), o despachante cria
> do zero.

## 6. Log de auditoria (`.jsonl`) — o FILME das decisões (§17.5 + DI-10)

**Princípio (D18, do autor):** *"encher a execução de logs com resultados parciais para auditar
com o Claude se a execução e a implementação estão perfeitas"*. Gravado em RUNTIME (as decisões
internas são irrecuperáveis depois — D97); a auditoria a partir dele é MANUAL do autor.

**Registros universais (todos os 21):**
- `header`: run_id, alg+versão, problema, D, M, semente, regime, maxFE, doe_hash, ambiente,
  params, sigma_dict, ts (+ smoke de path nos workers dedicados).
- `<alg>_gen` (por geração/iteração): a decisão "QUAL CAMINHO E POR QUÊ" + o motivo (a
  desigualdade que disparou) + **mínimo comum DI-10: `fe`, `f_best[]` (melhor por objetivo),
  `n_front1` (tamanho do ND corrente), `modelo_hp` (B1), `tempo_fit_s`/`tempo_busca_s` (B2),
  `dist_min_arquivo` (B3, por infill)**.
- `sonda` (DI-09): quando a sonda roda — `geracao`, `fe`, `n_pontos`, `tempo_pred_sonda_s`,
  hash-check do artefato.
- `guard`: cada guarda que dispara (clamp A4, NaN, dedup, cache-hit D89, hard-stop A2, retry A8…).
- `footer`: status/termino/fe_final/cp_init/cache_hits/n_geracoes.

**O contrato de auditoria (§17.5.1 — as 7 perguntas):** 1 mecanismo fiel? (distribuição de
caminhos × paper) · 2 protocolo? (FE=31D−1, DoE hash) · 3 adapters? (clamps/sinal) · 4 guardas? ·
5 trajetória sadia? (parciais) · 6 correções K.3 em runtime? · 7 custo esperado? (curva §17.6).

### 6.1 Campos específicos por config (S.7 da SPEC + ENRIQUECIMENTO DI-10 em negrito)

*(mapeamento profundo da torre, 2026-07-18 — regra: TODA adição é read-only; grandezas
inacessíveis sem patch invasivo no miolo stock NÃO entram — anotadas no fim)*

| Config | S.7 (já contratado) | **+ DI-10 (novo)** |
|---|---|---|
| b1 | λ; min/max da norm.; θ/dmodel; Gbest; μ/σ pop GA; guards mse<0/NaN/near-dup | **λ VETOR completo (M valores); `ei_best` (EI do escolhido — como o BO escolheu); `n_pool_ga`** |
| b3 | \|A1\|; u efetivo; NumV1/NumV2/Flag; ramo APD×σ; index; pop_por_w; nzero | **`apd_sel` (APD do escolhido no ramo APD) e `sigma_sel` (σ do escolhido no ramo incerteza) — o PORQUÊ numérico da escolha; `n_vetores_vazios` (de pop_por_w); `adapt_delta_V` (norma da adaptação dos vetores de referência por ciclo — o mecanismo K-RVEA)** |
| b4 | (p0,p1,rr,tr); regime R1–R4; L dos selecionados; \|lote\|; stalls | **os 6 `solution_id` das REFERÊNCIAS radiais da geração (o contexto da classe); `rr`/`tr` efetivos conferidos** |
| e7 | Ratio/flag; min(A.objs); μ/σ̄; dup-infill; guard sqrt | **`n_clusters_efetivo`; ramo/cluster de CADA um dos K=3 infills; `loss_treino` da EDN (B1)** |
| c217 | p+/p−/δ; n_contradicoes; ESTADO+motivo; \|lote\|; scores | **`n_best`/`n_worst` do treino; \|Pmid\| (tamanho da referência do gate)** |
| c141 | Fit1/2/3; ranks/Q/U; nível+telemetria (Q,U); \|subpops\| | **`n_por_nivel` (contagem de candidatos por nível da cascata); hp do RBF (B1)** |
| e74 | estratégia; classe_PNN; μ_RBF; dist/HV_gain; RefPoint; fração nível-1; dedup-slot | **`n_por_nivel` do PNN; `k_local_efetivo`** |
| c238 | y-scaling; [y,u,s] escolhido; pop GA; guards EIM-NaN/range/chol | **`eim_mediana_pool` (o decaimento do POOL inteiro, não só do best)** |
| c262 | seeds h1/h2; acqf do escolhido; restarts; fit-retries; fused/fallback | **`acqf_todos_restarts` (os 10 valores — a paisagem da aquisição = COMO o BO escolheu); `n_baseline` (pós-prune); `mll_final` (B1)** |
| c154 | rota B9.5; S fronts; acqf; restarts | **idem c262 (acqf dos restarts, n_baseline, mll)** |
| e81 | draws da posterior; front+índice; assert \|lote\|==q; dedup; dtype | **`n_train`** (o qPOTS NÃO tem baseline nem prune — o maximin é vs o dataset INTEIRO; `n_baseline` é conceito do qLogNEHVI. Mesma solução do c154 — DI-11 §2) **[P6/DI-16.6]**; resumo dos draws de Thompson (min/med/max) |
| c149 | val-MSE ×K=10; z-score params; HVI escolhido; tempo_fit | **`hvi_top5` (os HVI dos 5 melhores candidatos — como o greedy escolheu); `std_ensemble_sel` (a incerteza-ensemble do escolhido)** |
| c122 | softmax; Q1/Q2/Q3; accs por classe; skip-de-treino/re-init | **`n_acordo`/`n_desacordo` das 2 redes por geração (o mecanismo θ-DEA-DP)** |
| b5 | modo; geração/arquivamento; n_restarts GPR; substituições P_wrong (b5m) | **os PESOS de decomposição do b5m no HEADER (determinísticos — 1×); `p_wrong_stats` (min/med/max por geração)** |
| c311 | dict_gps; points_per_model; early-stop; folha pior-MSE | **`n_folhas` + `profundidade` da árvore por iteração (o particionamento É o mecanismo treed-GP)** |
| e103 | CurGen; KFlag; √MSE; μ dos 2 modelos; quase-singularidade | **`divergencia_modelos` (mean\|μ_Krig−μ_RBFN\| por geração — o desacordo entre as 2 cabeças); `margem_3sigma` (o valor que decide o KFlag)** |
| **pisos (5)** | só o mínimo comum | **`n_front1`; `f_best[]`; ideal/nadir da pop por geração; os VETORES de decomposição do moead/nsga3 no HEADER (determinísticos — UniformPoint(N,M), 1×)** |

**Rejeitados no DI-10 (inacessíveis sem patch invasivo no miolo stock — viola patch-mínimo/D30):**
contagem de substituições por geração do MOEA/D; niching por referência do NSGA-III; genealogia
de operadores/pais por indivíduo. *(As alternativas read-only acima cobrem o essencial.)*

## 7. Camada ⑦ — `__final.parquet` (SÓ os 5 offline — DI-08)

O §11/B7.5 manda avaliar o conjunto final do offline 1× na função verdadeira ("a única chamada
real"). **[DI-13.9] AVALIAM-SE TODOS OS FINAIS e o não-dominado é filtrado DEPOIS da avaliação
real** — filtrar pelo ND-segundo-o-modelo ANTES seria filtrar a realidade pela FANTASIA do modelo,
destruindo justamente o que a camada mede (o custo extra é nulo: funções analíticas).
Camada própria por run offline: `x0..x{D-1} | f0..f{M-1} (avaliados em problems.py) | origem_solution_id | origem_geracao |
**origem_linha** (link POSICIONAL à ③ — a regra 1 do R4 proíbe casar por X float32) |
**nd_pos_real** (se o ponto continua não-dominado APÓS a real — a medida DIRETA do "erro de
fantasia") [DI-13.8]`; escrita PÓS-HOC pela torre/harness Python; NÃO conta no orçamento
(exceção §11); o gate offline checa presença+consistência. Configs: e103, b5r, b5m, c311, piso-off.
- **Alimenta:** as métricas oficiais do regime offline (§11) — o ponto único da curva real.

## 8. Artefatos GLOBAIS (fora dos runs)

| Artefato | Conteúdo | Papel |
|---|---|---|
| `data/doe/{p}/doe_{p}_{s}.parquet` + sidecar | o DoE 11D−1 por (problema, semente) + hash | comparação justa D88 (o MESMO início p/ os 21) |
| `data/datasets/{p}/ds_{p}_{s}.parquet` + sidecar | dataset offline (D90) | o orçamento do regime offline |
| **`data/sonda/sonda_{p}.parquet` + sidecar** | **os 2000 pontos FIXOS + f verdadeiro + hash** | **a régua única da sonda (§3.1)** |
| `claude_code_context/artifacts/runs_matrix.csv` | as 19.950 linhas do grid | a lista do que TEM que rodar |
| Tabela de execuções (M7; agrega manifestos via Scoreboard) | grid × status × wall_s × n_retries | o painel do operador |
| `scripts/progress.py` (M7) | view ao vivo (jsonl+manifestos) | barra tqdm-like + tabela |

## 9. Mapa análise → dados (o "para quê" consolidado)

| Análise da dissertação | Dados |
|---|---|
| Convergência/ranking dos 21 (IGD+/HV, trajetória) | ① (+②) |
| Régua vs pisos; vantagem×dimensão | ① dos 21 |
| WAPE/erro do surrogate — global e comparável | ③ sonda + artefato da sonda |
| Erro nas DECISÕES (onde importa) | ③ busca + ① via real_solution_id |
| In-sample × out-of-sample | `fe_treino_max` (DI-09/A1) |
| Calibração da incerteza (cobertura, NLL/CRPS, sharpness) | ③ (σ×erro real) — sonda E busca |
| Acurácia/recall/F1 dos classificadores | ③ + rótulo derivado (sonda: por construção; busca: ①+②) |
| "O surrogate melhora com as épocas?" ↔ otimizador | ③ sonda por geração × IGD+×FE do ① |
| Exploração×explotação sob incerteza | `dist_min_arquivo` (B3) + ramos do jsonl |
| Contrafactual "sem incerteza" / Kendall-τ | ③ busca (salvar-tudo) |
| Parede O(n³) / custo por família | ④ + manifesto timing |
| Fidelidade de mecanismo (D97) | ⑥ jsonl (as 7 perguntas §17.5.1) |
| Hiperparâmetros/aprendizado do modelo | `modelo_hp` (B1) no jsonl |

## 10. Regras de leitura obrigatórias (R4)

1. Dedup/joins por `solution_id` — NUNCA pelo X float32 armazenado.
2. `real_solution_id`: tolerar int32 E double+NaN (dicotomia documentada).
3. Antes de ler a ③ de um algoritmo: ler o `sigma_dict` do manifesto (DEF-C4).
4. Erro de surrogate: filtrar in-sample com `fe_treino_max`; b1 compara-se à parte (escalar).
5. Sonda: join com o gabarito POR POSIÇÃO dentro do bloco (ordem do artefato preservada).
6. Comparação entre algoritmos ao longo do tempo: alinhar por FE consumido, não por "geração".
7. Wall-clock: nunca comparar cross-stack sem ressalva (§19); a curva de escalabilidade é robusta.
8. `fe_index` é 0-based; gerações são 1-based; nº de gerações varia por config/cache-hits.
9. **[DI-13.15] `fe_treino_max` NÃO é monotônico** em b1/b4/c217 — esses três SUBAMOSTRAM o conjunto
   de treino, então o valor pode cair de uma iteração p/ a outra e não coincide com `fe−1`.
10. **[DI-13.5] Sonda:** `geracao` é NULL nos blocos OFFLINE; o join com o gabarito é POR POSIÇÃO
    dentro do bloco (online = linhas 0..1999 do artefato; offline = 0..19999).
