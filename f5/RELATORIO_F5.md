# RELATÓRIO F5 — Validação de fidelidade da rodada-42, ponta a ponta

> **O que é.** O registro EXAUSTIVO de tudo que a validação F5 encontrou, fase a fase:
> o que se comportou exatamente como esperado, o que não, e — para cada não — a causa
> provada, com evidência. **Destinatário: a torre central de implementação**, que usará
> este documento para corrigir o harness e deixar o código perfeito para o disparo em
> escala (M8/M9, 30 sementes). Mantido pela torre de fidelidade; cresce a cada fase.
> Contratos: `handoff/F5-FRAMEWORK-v2.md` (a tarefa) · `f5/PROTOCOLO_ANALISE_FIDELIDADE.md`
> (o método por config).
>
> **Estado: F5.1 CONCLUÍDA (2026-07-28) · placar 666 = 665 APROVADAS + 1 REPROVADA-F5.1.**

---

## 0. Sumário executivo (atualizado a cada fase)

| Fase | Estado | Resultado-síntese |
|---|---|---|
| D1 download | ✅ | 4.954/4.954 objetos do bucket, 0 erros |
| D2 organização | ✅ | 666 células → layout do autor; 4.398 arquivos; 0 substituição de ⑥ necessária |
| D3 verificação | ✅ | 0 camadas faltantes vs censo |
| **F5.1 gates** | ✅ | **665 aprovadas / 1 REPROVADA** (aborto interno mascarado — bug B1); 45 ⑦ do e103 geradas pós-hoc pela torre; 4 falsos-vermelhos de tolerância diagnosticados e aceitos pelo autor |
| F5.2 | 🟡 em execução | integridade + contrato + métricas + sonda + tempo |
| F5.3–F5.7 | ⬜ | — |

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

## 5. F5.2 — Integridade · contrato · métricas · sonda · tempo — 🟡 EM EXECUÇÃO

*(seção preenchida ao fechar a fase)*

## 6. F5.3a/b — Análises de fidelidade por config — ⬜

## 7. F5.4 — Verificação adversarial — ⬜

## 8. F5.5 — Transversais — ⬜

## 9. F5.6 — Matriz-mestra e capítulos — ⬜

## 10. F5.7 — Plano da rodada perfeita — ⬜
