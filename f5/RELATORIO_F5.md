# RELATÓRIO F5 — Validação de fidelidade da rodada-42, ponta a ponta

> **O que é.** O registro EXAUSTIVO de tudo que a validação F5 encontrou, fase a fase:
> o que se comportou exatamente como esperado, o que não, e — para cada não — a causa
> provada, com evidência. **Destinatário: a torre central de implementação**, que usará
> este documento para corrigir o harness e deixar o código perfeito para o disparo em
> escala (M8/M9, 30 sementes). Mantido pela torre de fidelidade; cresce a cada fase.
> Contratos: `handoff/F5-FRAMEWORK-v2.md` (a tarefa) · `f5/PROTOCOLO_ANALISE_FIDELIDADE.md`
> (o método por config).
>
> **Estado: F5.3a CONCLUÍDA (2026-07-28) · placar 666 = 664 na análise + 2 REPROVADAS (1 F5.1, 1 F5.2a) · pilotos: zero classe (3) · aguarda calibração do autor p/ o fan-out.**

---

## 0. Sumário executivo (atualizado a cada fase)

| Fase | Estado | Resultado-síntese |
|---|---|---|
| D1 download | ✅ | 4.954/4.954 objetos do bucket, 0 erros |
| D2 organização | ✅ | 666 células → layout do autor; 4.398 arquivos; 0 substituição de ⑥ necessária |
| D3 verificação | ✅ | 0 camadas faltantes vs censo |
| **F5.1 gates** | ✅ | **665 aprovadas / 1 REPROVADA** (aborto interno mascarado — bug B1); 45 ⑦ do e103 geradas pós-hoc pela torre; 4 falsos-vermelhos de tolerância diagnosticados e aceitos pelo autor |
| **F5.2** | ✅ | **664 aprovadas / 1 reprovada** (b1/WFG1 ⑥ contaminado); contrato estrutural 100% (1 não-conformidade: ⑤ sem params em 7 configs); métricas 664/664; sonda 461 células; projeção 30 seeds ≈ 10.173 h-core |
| **F5.3a pilotos** | ✅ | c217 9,0 (≡ âncora do autor) · e81 10 · e7 10 · b1 9,3 · c311 8,5 — ZERO classe (3) | 
| F5.3b–F5.7 | ⬜ | aguarda calibração do autor |

**Itens já acumulados para a torre central corrigir (consolidação final na F5.7):**
1. 🔴 **B1** — `experiments.py:209` sobrescreve `status=failed` do runner com `ok`
   (provado de novo aqui: a célula REPROVADA da F5.1 estava `ok` no manifesto).
2. 🔴 **Driver da ⑦ pós-hoc ausente do rito de máquina** — as 45 células e103 da vm3
   fecharam a rodada SEM a camada ⑦ (endpoint oficial do offline); o rito F4 por máquina
   precisa incluir `portao.py --varredura` (que é o driver de lote da ⑦) ou o despachante
   MATLAB precisa acionar o `final_eval` ao fim de cada célula offline.
3. 🟠 **Tolerância do check da ⑦** (`final_eval.py:259`, `rtol=1e-5/atol=1e-6`) não
   modela a amplificação do roundtrip float32 pelo nº de condição do problema —
   4 falsos-vermelhos em DTLZ3/DTLZ4/WFG9 (desvios relativos 1,5e-5–7,3e-5).
   Sugestão: rtol=1e-4, ou tolerância condition-aware.
4. 🟠 **⑥ sem footer em runs do env_c311** (8 células; perda na ESCRITA — gcs ausente
   no env) — rito de footer resiliente a exceção de upload.
5. 🟡 Doc-sync do CONTRATO §6: o evento de geração não é sempre `<alg>_gen`
   (e81 grava `decision`; c311 grava 4 `decision`/run) e o campo de término varia
   (`motivo_parada` ⑤ | `footer.termino` | `footer.motivo`).

---

## 1. D1 — Download do bucket (a fonte única)

**Contexto**: as 4 VMs da campanha estão TERMINATED; `gs://mestrado_experiments` é a
única cópia completa. Download read-only (`gcloud storage cp -r`), conta
`gdmello.nunes@gmail.com` (⚠ a conta ativa do Mac é outra — armadilha nº 1 do tutorial,
403 enganoso).

**Resultado — tudo conforme o esperado:**
- **4.954/4.954 objetos** baixados para `resultados_experimentos/_bucket_raw/experiments/`
  (estrutura canônica preservada), **0 erros** no log (`_download.log`), throughput médio
  8,7 MiB/s.
- O staging `_bucket_raw/` fica como **espelho local permanente do bucket** (estrutura
  `{exp}/{alg}/`), além da visão organizada do autor.
- `du` reporta 5,0 GB (bytes lógicos ~3,6 GB + overhead de bloco APFS de ~4.950 arquivos).

## 2. D2 — Organização no layout centralizador do autor

**Regra de nomes implementada** (`resultados_experimentos/{alg}/{label}/{seed}/`):
- main e off → `label = {problema}` (ex.: `e81/ZDT1/42/`);
- batch → `label = q10_{problema}`;
- sweep → `label = swap_{tier}-{dist}_{problema}` — **extensão necessária do prefixo
  pedido**: só `swap_{problema}` faria os 6 tokens (`small/medium/big × lhs/mvns`)
  colidirem na MESMA pasta (ex.: c311 tem 6 células de DTLZ2 no sweep). A extensão
  preserva o prefixo `swap_` e desambigua.

**Resultado:**
- **666 células organizadas, 4.398 arquivos**, tudo por **hardlink** (zero disco extra;
  staging e visão organizada compartilham os mesmos blocos).
- Arquivos mantêm o nome canônico (`exp_{exp}_{alg}_{problema}_{semente}*`) —
  autodescritivos e compatíveis com os gates.

**Achado POSITIVO que corrige uma expectativa documentada:** o caveat nº 3 do handoff
F5 dizia "o ⑥ do bucket NUNCA tem footer (upload precede o fechamento)". **Falso para a
rodada-42**: o espelho é pós-conclusão (`mirror_run` ao fim do run), então **as células
das VMs vieram do bucket COM footer** — zero substituições de ⑥ foram necessárias
(`_FONTES.csv` gerado vazio, documentando a verificação).

**As únicas 8 células sem footer no ⑥ (esperadas — caveat conhecido, perda na ESCRITA
no env_c311, sem cópia melhor em NENHUMA fonte — verificado em repo local E _maquinas):**
`c311/swap_small-lhs_{MMF16_20, ZDT4, WFG9, ZDT1}` ·
`c311/swap_small-mvns_{MMF16_20, DTLZ2, WFG9}` · `treed_media/swap_big-mvns_MMF16_20`.
Todas passaram nos gates (accept+auditar VERDES); a certificação de término delas vem
do ⑤/censo. **Seguem para a F5.2 com esta ressalva documentada.**

## 3. D3 — Verificação contra o censo

Cada uma das 666 células teve sua assinatura de camadas (coluna `camadas` do censo do
bucket) conferida arquivo a arquivo no destino: **0 faltas**. O repo `data/experiments/`
foi completado com as células das VMs por hardlink (**+2.136 arquivos**; 2.262 já eram
locais do Mac; **nenhuma sobrescrita** de cópia local) — pré-requisito dos gates, que
operam sobre `data/` (o `accept.py` não expõe `--data-root`).

## 4. F5.1 — Gates de protocolo (o portão objetivo)

**Método**: `portao.py` célula a célula (accept por cartão + auditar + `final_eval
--check` nos offline), no env_main do Mac (bug B3: accept dá falso-VERDE sem pyarrow),
6 workers em paralelo; driver em Python (o driver zsh inicial falhou pela armadilha
O-02 — zsh não faz word-splitting de variável — revivida na prática e re-registrada).
Artefato: `f5/gates_f51.csv` (666 linhas, exit + detalhe por célula).

### 4.1 Primeira passada: 617 verdes / 49 vermelhos — e a causa única dos 44

**44 dos 49 vermelhos eram e103** (25/25 off + 19/20 sweep), todos com a MESMA
assinatura: `accept=VERDE · auditar=FALHOU · final_eval --check=FALHOU`, e o
`final_eval` dizendo a causa literal: **"camada ⑦ ausente"**.

**Causa-raiz (provada):** a ⑦ (`__final.parquet` — o ND final avaliado 1× na função
real, o ENDPOINT OFICIAL do regime offline, DI-08) é gerada **fora do run**, pós-hoc,
pelo driver Python `final_eval` — e **esse driver nunca rodou para as células da vm3**
(onde o e103, MATLAB, executou). O bucket tinha apenas 2 arquivos `final-*` em
`off/e103/` e a ⑦ de 1 célula de sweep (`sweep-medium-lhs/ZDT4`, a única verde da
primeira passada — provável resquício do smoke F2). O censo NÃO acusou porque o
gabarito de camadas dele é a assinatura MODAL do próprio config — se nenhuma célula
tem ⑦, a ausência é invisível ao censo. **Dupla lição para a torre central:**
(a) o rito de fechamento por máquina precisa incluir o driver da ⑦ (item 2 do §0);
(b) o censo ganharia um gabarito NORMATIVO de camadas por (config, regime), em vez do modal.

**Correção executada pela torre de fidelidade (o passo desenhado que faltava, mandato
DI-08 "escrita pós-hoc pela torre/harness Python"):** `final_eval` rodado para as
**45 células e103 (25 off + 20 sweep) — 45/45 VERDES** na geração (ex.: `off/MMF1`:
100 finais avaliados na geração 99, 37 ND pós-real). Re-gate das 45: **45/45 VERDES**.
Os 88 arquivos novos (⑦ + sidecars) foram propagados para a pasta organizada e,
com autorização do autor (2026-07-28), para o bucket.

### 4.2 Segunda passada: 661 verdes / 5 vermelhos — os 5 dissecados

**4 vermelhos = FALSOS-vermelhos de tolerância do gate (células ÍNTEGRAS):**

| Célula | desvio abs | desvio REL máx | mecanismo |
|---|---|---|---|
| `off/c311/DTLZ3` | 6,10e-4 | **7,3e-5** | 53/95 soluções na borda; DTLZ3 tem nº de condição ~10³ (g com 100·Σcos(20πx)) |
| `off/c311/DTLZ4` | 8,51e-6 | **4,9e-5** | α=100 → x^100, derivada enorme perto de x=1 |
| `sweep-big-mvns/c311/WFG9` | 4,29e-6 | **1,9e-5** | transformações WFG íngremes; 48/50 na borda |
| `sweep-medium-mvns/b5m/WFG9` | 1,19e-5 | **1,5e-5** | idem; 9/50 na borda |

O check da ⑦ (`final_eval.py:259`) recomputa `f = problems.py(X_float32)` e compara com
`allclose(rtol=1e-5, atol=1e-6)`. O X e o f são armazenados em float32 (D53); o erro de
arredondamento de x (~6e-8 relativo) é **amplificado pelo gradiente** do problema —
nos problemas íngremes o desvio relativo em f cai na faixa 1,5e-5–7,3e-5, logo acima do
rtol. **Prova do mecanismo**: recomputo com e sem clip nos bounds dá o MESMO desvio
(clip descartado como causa); o desvio é ULP-float32 × condição. Efeito metrológico:
nulo (não move IGD+/HV além da 4ª casa). **Decisão do autor (1), 2026-07-28: células
ACEITAS; o fix da tolerância vai à F5.7** (item 3 do §0).

**1 vermelho = célula GENUINAMENTE degradada (a única REPROVADA da fase):**

- **`sweep-big-mvns/c311/MMF16_20`** — o caso B1 pré-registrado, agora confirmado no
  gate: `manifesto status=ok` com `motivo_parada='gpy_bfgs_linalg'` (LinAlgError do GPy
  matou o `addGPs`; o despachante mascarou o failed — bug B1, `experiments.py:209`).
  Evidência nos dados: **0 blocos de sonda** (esperados 40.000 linhas), ③ SÓ com fase
  `treedGP_build` até a geração 2141 (sem fase final), contador incompleto. O accept e
  o auditar reprovaram exatamente pelos itens certos.
- **Decisão do autor (2), 2026-07-28: EXCLUÍDA da análise → nova categoria
  "REPROVADA NO GATE F5.1"**, motivo: *aborto interno mascarado como ok (B1); surrogate
  degradado; célula candidata a re-run na rodada perfeita (F5.7)*. Com isso o
  inventário da campanha passa a ter DUAS listas de exclusão: as 29 que não rodaram
  (categorias A/B/C/D do `INVENTARIO_nao_go_semente42.md`) e as reprovadas por fase da
  F5 (esta é a 1ª).

### 4.3 O que se comportou EXATAMENTE como esperado (o lado verde, igualmente importante)

- **661/666 células passaram em TODOS os gates aplicáveis** (accept por cartão + auditar
  + final_eval nos offline): FE = 31D−1 exato, CP-init bit-a-bit com o artefato do DoE,
  camadas íntegras, sonda na cadência normativa, binding por hash dos datasets offline.
- Os 13 configs MATLAB + os pisos: **zero vermelhos**.
- Os 5 problemas × 6 tokens do sweep (menos as células citadas): **zero vermelhos**,
  incluindo o binding do ① ao dataset da variante (tier/dist) por hash.
- batch (q10): 15/15 células verdes (incl. verificação de FE=11D−1+200·q).
- O caso B1 foi pego pelo GATE — o desenho "célula anômala não passa" funcionou.

### 4.4 Placar final da F5.1 e decisão de fluxo

| | células |
|---|---:|
| Entraram na F5.1 | 666 |
| **APROVADAS → seguem para F5.2** | **665** |
| REPROVADAS no gate F5.1 | 1 (`sweep-big-mvns/c311/MMF16_20`, motivo B1) |
| Aprovadas com ressalva documentada | 4 (tolerância-⑦, aceitas pelo autor) + 8 (⑥ sem footer, caveat de escrita) |

**Decisão do autor (3), 2026-07-28:** as 45 ⑦ do e103 geradas pela torre foram
autorizadas a subir ao bucket e já constam na pasta centralizadora
(`resultados_experimentos/e103/...`).

---

## 5. F5.2 — Integridade · contrato · métricas · sonda · tempo — ✅ CONCLUÍDA (2026-07-28)

**Escopo**: as 665 aprovadas da F5.1. **Saldo da fase: 1 nova REPROVADA (F5.2a) → 664
células impecáveis seguem para a F5.3.** Artefatos: `f5/integridade_f52a.csv` ·
`f5/contrato_f52b.csv` · `f5/metricas_finais_f52c.csv` + `f5/trajetorias/` (664 JSON) ·
`f5/tempo_f52d.csv` + `f5/tempo_heatmap.html` + `f5/projecao_30seeds.md` ·
`f5/sonda_f52e.csv`.

### 5.1 F5.2a — Integridade ("nada corrompido?"): ✅ com 1 reprovação e 5 ressalvas

Todo arquivo das 665 células foi ABERTO: parquet lido (pyarrow, linhas+colunas),
manifest parseado, jsonl parseado linha a linha. Resultado:
- **Zero parquets ilegíveis, zero manifests ilegíveis** em ~4.490 arquivos.
- 105 ③ com 0 linhas = **por desenho** (4 pisos online × 25 + sobol_batch × 5 — configs
  sem surrogate; o arquivo existe vazio por completude de camadas, DI-13.7).
- **🔴 REPROVADA (nova categoria F5.2a): `main/b1/WFG1`** — ⑥ com **49 eventos truncados
  no MEIO do JSON** espalhados pelo arquivo (linhas 839, 843, 845…) e **sem footer**.
  Timestamps das linhas rasgadas: madrugada de 2026-07-27 na vm3 — a janela dos
  problemas de disco/capacidade da vm3 (O-19). Assinatura de escrita
  concorrente/interrompida (possivelmente dois writers na mesma célula — vide item do
  RUNBOOK sem `'parallel',false`, achado da validação final). ①–⑤ estão íntegras e os
  gates F5.1 passaram (não parseiam o ⑥) — mas o FILME do mecanismo está contaminado
  em 49 pontos ⇒ inutilizável para a Classe A no padrão "impecável". Candidata a
  re-run na rodada perfeita.
- **Ressalva (5 células, aprovadas)**: 1 linha órfã não-parseável em
  `off/e103/{DTLZ7,WFG2,WFG4,WFG9}` (fragmento-cauda tipo `.234093}` na ÚLTIMA linha —
  resíduo de reescrita mais curta do arquivo; o filme da tentativa final está ÍNTEGRO,
  header→footer completos) e em `sweep-small-lhs/moead_media/ZDT1` (linha com TEXTO DE
  OPERADOR embutido — o caso "2-escritores" pré-registrado no caveat 3). Sem perda
  analítica relevante (≤1 evento por célula).

### 5.2 F5.2b — Contrato de dados: ✅ estrutural 100%, com 1 não-conformidade de ⑤

**O lado verde (o grosso):** nas 664 células, **ZERO desvios** de: contagem da ①
(31D−1 no main/off/small; 2.000 no medium; 50.000 no big; 11D−1+2000 no batch — tiers
todos exatos), fase init (11D−1 online; 100% init no offline), schema das camadas
①③④, ② vazia só na família sancionada, blocos de sonda (2.000×k online;
20.000×{1,2} offline conforme o config), ⑦ presente com `nd_pos_real` em 100% do
offline, `fe_final==maxfe`, `q=10` no batch, `sigma_dict` presente em todo config com
surrogate.
**A não-conformidade (197 células, 7 configs):** o ⑤ NÃO tem a chave `params` (o
CONTRATO §5 a lista como obrigatória) em **c217 (25), c262 (21), c154 (11), b5r (45),
b5m (45), moead_media (45), sobol_batch (5)** — heterogeneidade entre writers.
**Fallbacks verificados** (sem perda de dado): c262/c154 têm params no HEADER do ⑥;
c217 tem os valores achatados no header (N, delta, gmax…); b5-família/sobol_batch
recuperam de `artifacts/params.json` + `sigma_dict`. **Item nº 6 para a torre
central**: uniformizar `params` no ⑤ dos 7 configs.

### 5.3 F5.2c — Métricas oficiais: ✅ 664/664, zero erros

Gate D92 verde (1,04333) ANTES de qualquer conta; `src/metrics.py` puro (nunca
reimplementado). Por célula: IGD+ (primária), HV, IGD, GD, spacing, |ND| finais +
trajetória de 20 checkpoints. Prévia (rank médio de IGD+ nos 25 problemas do main):
**c262 3,7 · c122 4,7 · c141 4,8 · e74 6,1 · b3 6,4** — coerente com todos os priors
(c262 = melhor do set). Régua SA×pisos por dimensão (PRÉVIA de 1 semente; análise
plena na F5.5): D=2 25/39 · D=7 0/13 · D=10 74/115 · D=12 11/35 · D=20 6/11 ·
D=22 24/69 · D=30 15/23 células SA batendo o melhor piso.

### 5.4 F5.2d — Tempo: ✅ zero buracos de timing

**665/665 células com `timing.tempo_total_s` no ⑤** (a obrigatoriedade do retrofit
v5.2.1 foi cumprida em 100% da rodada). Heatmap config×célula em
`f5/tempo_heatmap.html`; matriz em `f5/tempo_f52d.csv` (com coluna de máquina:
roster + correção `mac*` via `_lotes_mac/*done.txt`). **Projeção 30 sementes ≈
10.173 h-core**; os 4 dominantes: main/c149 2.131 · main/c154 1.537 · main/c122
1.239 · main/c262 867 h-core (detalhe em `f5/projecao_30seeds.md`; caveats §19 e
atribuição de máquina documentados no arquivo).

### 5.5 F5.2e — Sonda (a régua comum): ✅ 461 células regressoras, zero avisos

44.928 medições (célula × bloco × objetivo): WAPE + correlação + cobertura ±1,96σ,
por objetivo, no espaço CRU (des-transformação via `transf_params` — 100% dos blocos
com contagem exata 2.000/20.000 e des-transformação suportada). Síntese "o surrogate
aprendeu?" (variação mediana do WAPE 1º→último bloco, main):

| config | ΔWAPE mediano | leitura (× priors) |
|---|---:|---|
| e81 | **−38%** | GP aprende limpo ✓ (prior DI-24) |
| c154 | **−32%** | GP aprende ✓ |
| c262 | **−17%** | GP aprende ✓ (prior DI-20.3) |
| c238 | −2% | quase-plano |
| c141 | −0% | plano (deriva do RBF é local, não global) |
| b3 | +4% | sonda "chata" ✓ (prior: dissociação b3) |
| e7 | +6% | NÃO aprende ✓ (esquecimento do SelectTrainData — prior v2) |
| c149 | +16% | piora ✓ (prior: preditor-da-média em baixo-n) |
| e74 | **+268%** | RBF explode fora do suporte ✓ (prior v2: μ até 770) |

A régua reproduz TODOS os comportamentos previamente documentados — agora em 25
problemas por config, não 3. b1 fica à parte (escalar D47); classificadores
(c217/b4/c122) ficam para a análise dedicada da F5.3.

### 5.6 Veredito da fase

| | células |
|---|---:|
| Entraram na F5.2 | 665 |
| **APROVADAS → seguem para F5.3** | **664** |
| REPROVADAS na F5.2a | 1 (`main/b1/WFG1`, ⑥ contaminado) |
| Aprovadas com ressalva | 5 (linha órfã no ⑥) + 197 (⑤ sem `params`) + 8 (⑥ sem footer, F5.1) |

**Novos itens para a torre central** (somam-se aos 5 do §0): **(6)** `params`
obrigatório no ⑤ dos 7 configs listados; **(7)** reescrita do ⑥ em retry não trunca o
arquivo (caudas órfãs — e103×4); **(8)** proteção contra writer concorrente/interrompido
no ⑥ (b1/WFG1) + `'parallel',false` explícito nos comandos MATLAB do RUNBOOK.

## 6. F5.3a — Pilotos de fidelidade — ✅ CONCLUÍDA (2026-07-28) · aguarda CALIBRAÇÃO do autor

5 relatórios completos em `f5/relatorios_config/{c217,e81,e7,c311,b1}.md` — protocolo
v1.0 executado em TODAS as células de cada config (não amostra): 6.762 gerações (c217),
8.020 decisões (e81, incl. 5 células batch), 2.328 ciclos (e7), 604 decisões + tiers
(c311), 7.073 iterações (b1). Agregado: ~25 mil eventos de decisão auditados, ~12M
linhas de ③ verificadas.

| config | score piloto | prior | recomendação | classe (3) | destaque |
|---|---|---|---|---|---|
| c217 | **9,0** | 9/10 AUTOR | aceitar | 0 | **âncora BATE exata**; finalProbe/hard_stop novos aspectos provados |
| e81 | **10,0** | 9/10 autor | aceitar | 0 | query-joia 8.020/8.020 (\|Δ\|≤8,1e-8); fallback qmaximin DI-25 exercitado 32× e correto; B17.5 resolvida POR DADO |
| e7 | **10,0** | 7,0 v2 | aceitar | 0 | identidade dos ramos 99,5%/99,1% em 6.984 infills; agente-4 refutado (pop não persiste: interseção 0 em 2.303 fronteiras) |
| b1 | **9,3** | 8,5 v2 | aceitar+caveat | 0 | identidade EI 7.073/7.073 (13 caudas = underflow provado); 2 células perdidas (DTLZ4 real; WFG1 infra) |
| c311 | **8,5** | 7,5 v2 | aceitar | 0 | early-stop do código PROVADO (16 disparos, janela-2/piso-6); âncora J de escalabilidade @50k confirmada; nó-puro MVNS explicado |

**ZERO aspectos classe (3) nos 5 pilotos** — todos os desvios mapeados a decisões
sancionadas com citação. Única confirmação OPCIONAL à F5.4: semântica de nó-puro do
sklearn (c311, 3 incrementos fora da banda sob MVNS — mecanismo já provado por dado).

**Achados sistêmicos novos (além dos configs):**
- **Métricas oficiais EMPATAM por desenho entre os 5 algs offline** (a ① é o MESMO
  dataset; D69 lê a ①) — ranquear offline exige a ⑦ (`nd_pos_real`/f-reais); vincula a
  F5.5.
- Caveat de leitura do `sonda_f52e.csv`: na família treed, `cobertura95` só cobre os
  pontos com σ válido — reportar junto o %σ-NaN (o próprio CSV traz `n_validas`).
- `tempo_f52d.csv` corrigido (commit 7a58bcb): 31 células com máquina real Mac
  (e7×22, c238×7, b1×2 — recuperações O-19) estavam com o roster.
- Sweep do c311 (novidade científica p/ D97): mais dado melhora a MÉTRICA do dataset
  mas REDUZ a fração do surrogate coberta por GPs (early-stop corta cedo; big ≈ árvore
  pura com ilhas de GP; σ-NaN mediano 90,3% na sonda big).

## 6-bis. F5.3b — Fan-out (19 configs) — ⬜ aguarda calibração do autor

## 7. F5.4 — Verificação adversarial — ✅ CONCLUÍDA (2026-07-29)

14 agentes Opus: 13 céticos (1 por achado classe (3), viés de REFUTAR) + 1 investigador do
padrão sistêmico. Artefatos: `f5/adversarial/*.md` (14 vereditos) + `f5/baterias/f54/`.

### 7.1 O veredito dos 13

| achado | veredito | enquadramento |
|---|---|---|
| b4-A12 (p0/p1 invertidos) | **REFUTADO** | resíduo (d) doc, severidade mínima |
| c154-J27 (desalinhamento ③×acqf) | **REFUTADO** | — |
| moead-M16 (n_front1 ±1) | **REFUTADO** | — |
| moead_media-C9b (colapso do GPR) | **REFUTADO** | reclassificado (2) sancionado |
| e103-A25 (⑦ card. 200) | **REFUTADO como (3)** | rebaixado a (d) |
| sobol_batch-S23 (n_front1 ausente) | **PARCIALMENTE REFUTADO** | (d), reduzido de 4 p/ 1 campo |
| c122-A27 (referência do bloco-1) | CONFIRMADO **(d)** | instrumentação/doc |
| e81-B28 (94 pares espúrios) | CONFIRMADO **(d)** | duplicata do defeito sistêmico |
| b5r-A30 (③ ger.1 = pop inicial) | CONFIRMADO **(d)** | instrumentação/doc |
| b5m-A25 (⑥ sem DI-10) | CONFIRMADO **(d)** | instrumentação/doc |
| sobol_batch-S24 (tempo_aval=0) | CONFIRMADO **(d)** | instrumentação |
| b5m-A8 (cadeia do congelamento) | CONFIRMADO **(b)** | **comportamento legítimo → vira RESULTADO** |
| c149-A26 (③ de outra execução) | CONFIRMADO **(c)** | **DADO DESCASADO → célula sai** |

**O resultado que mais importa: ZERO achados da categoria (a) — nenhum bug de
implementação de algoritmo em 24 configs.** 6 são defeitos de instrumentação/log (o
mecanismo está certo, o registro é que engana), 1 vira resultado científico, 1 é dado
descasado (1 célula excluída), 5 caíram na refutação.

### 7.2 O padrão sistêmico — causa-raiz provada em 6 passos

O investigador varreu as 666 células e achou **34 com assinatura anômala (5,1%)**, das
quais **4 com conteúdo do bucket ≠ do Mac — todas ZDT4**, incluindo uma que NENHUM
analista tinha visto (`sobol_batch/q10_ZDT4`).

**A causa não é a que estava registrada** ("provisionamento copiou `data/`") — são duas
causas encadeadas:
1. **`is_run_done` faz o disparo PULAR a célula** quando o smoke pré-campanha já deixou
   artefato em `data/` (22 células "pulou" nos `done.txt`, **9 delas ZDT4**);
2. **`AuditLogger` abre o ⑥ em modo `"a"` (append) sem guarda** (`src/audit_log.py:55`),
   então toda re-invocação empilha `header`/`footer` do despachante sobre um run fechado.

**Por que ZDT4**: é a célula-de-smoke canônica — está no roster de `batch` E dos 6 tokens
de `sweep`, e é o menor D (=10) dos cinco (maxFE 309/2109 contra 929/2329 do ZDT1);
`scripts/accept.py:256` usa literalmente o par `("ZDT4", 42)`.

**Dano científico real = 1 célula.** Só `batch/c149/ZDT4` é quimera, e a prova é
definitiva: a ③ do bucket bate **2.000/2.000 bit-a-bit** contra a ① do **Mac (24/07)** e
**0/2.000** contra a ① do próprio bucket (VM, 26/07) — o `__surrogate.parquet` do bucket
é o do smoke do Mac; as demais camadas são do run da VM. As outras 3 células divergentes
são metadados/⑦, dano zero.

**Saúde do resto da campanha (medida, não presumida):** o teste 3×1 (X da linha da ③ com
`real_solution_id` ≡ X da ①) rodou nas 666 — **360 aplicáveis, 359 OK a 100% bit-a-bit,
1 falha** (a do c149). `①.nrows == manifest.fe_final` fecha **666/666**;
`footer.fe_final == manifest.fe_final` fecha **666/666**; `doe_hash` e `sonda.x_hash`
particionam 25/25 problemas sem uma célula órfã.

### 7.3 ⚠ Incidente da PRÓPRIA validação (auto-reporte)

Durante a F5.3, **um agente meu invocou `experiments.py` para `batch/e81/ZDT4`** — que,
por estar `is_run_done`, foi um no-op… **exceto pelo `AuditLogger`, que appendou 10 pares
`header`/`footer` vazios ao ⑥** (timestamps 2026-07-28T23:59Z a 2026-07-29T01:59Z).
É a demonstração acidental e perfeita do bug nº 2 do §7.2.
**Apuração completa e correção:** comparei **os 666 ⑥ locais contra a cópia do bucket** —
665 idênticos, 3 divergentes: `batch/c149/ZDT4` e `batch/sobol_batch/ZDT4` divergem por
serem as versões do **Mac de 24/07** (pré-existentes, não tocadas por mim) e
`batch/e81/ZDT4` era o único alterado na minha janela (prefixo-compatível + 20 linhas).
**Restaurado bit-a-bit da cópia do bucket (95 footers, era 105) e congelado em modo 444**;
backup do arquivo contaminado preservado no scratchpad. Nenhum parquet, manifesto ou
outra célula foi tocado. Regra reforçada para a F5.7: **agente de análise não invoca
`experiments.py`, nem para no-op**.

## 8. F5.5 — Transversais — ⬜

## 9. F5.6 — Matriz-mestra e capítulos — ⬜

## 10. F5.7 — Plano da rodada perfeita — ⬜
