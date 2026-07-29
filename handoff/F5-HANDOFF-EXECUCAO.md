# HANDOFF DA EXECUÇÃO DA F5 — torre de fidelidade → torre central

> **Para quem é.** Para a instância que escreveu as instruções da F5 (a torre central de
> implementação) entender **exatamente o que foi feito, como, com que resultado, e o que
> ficou pendente de decisão do autor**. Escrito ao fim da execução completa (2026-07-29).
> **Estado: as 8 fases estão CONCLUÍDAS.** O que NÃO está fechado são **16 decisões do
> autor** (§6) — nenhuma delas bloqueia a entrega, todas bloqueiam o disparo das 30
> sementes.

---

## 1. O QUE FOI PEDIDO × O QUE FOI ENTREGUE

| pedido no handoff original | entregue | onde |
|---|---|---|
| Censo e triagem: explicar CADA célula não-ok | ✅ 666/666 explicadas; as 29 ausentes já vinham com causa | `f5/RELATORIO_F5.md` §4 |
| Gates objetivos em todas as células | ✅ `portao.py` nas 666 (não amostra) | `f5/gates_f51.csv` |
| Métricas com `src/metrics.py`, nunca reimplementar | ✅ gate D92 antes de cada conta; 664/664 sem erro | `f5/metricas_finais_f52c.csv` |
| 1 agente por config com paper + receita + dados | ✅ 24 configs, 20–31 aspectos dissecados cada | `f5/relatorios_config/*.md` (1,6 MB) |
| Comparativos transversais | ✅ + 1 correção metodológica que a própria validação achou | `f5/transversais_f55*.md` |
| Dossiê no formato das notas v2 | ✅ atualizado com o veredito consolidado | `DOSSIE_FIDELIDADE_R1.md` |
| **Extras pedidos pelo autor durante a execução** | | |
| Organizar os 666 no layout `{alg}/{label}/{seed}` | ✅ hardlinks, zero disco extra | `resultados_experimentos/` |
| "OK de que nada está corrompido" | ✅ todo parquet aberto, todo jsonl parseado | `f5/integridade_f52a.csv` |
| Tempo por experimento + heatmap + projeção 30 seeds | ✅ 665/665 com wall | `f5/tempo_heatmap_30seeds.html` |
| Verificação adversarial dos achados | ✅ 14 céticos, viés de refutar | `f5/adversarial/*.md` |
| Plano da rodada perfeita | ✅ 17 bloqueadores com custo | `f5/PLANO_RODADA_PERFEITA.md` |
| Inventário exaustivo de artefatos | ✅ | `f5/INVENTARIO_ARTEFATOS_F5.md` |

---

## 2. AS 8 FASES — o que cada uma fez, com que código, e o resultado

### D1–D3 · Aquisição e organização dos dados
**Como:** `gcloud storage cp -r` do bucket inteiro (read-only) → staging; depois
`f5/baterias/organizar_666.py` monta o layout do autor por **hardlink** (zero disco
extra) e `preencher_data.py` completa o `data/experiments/` do repo com as células das
VMs (os gates operam sobre `data/`; o `accept.py` não expõe `--data-root`).
**Resultado:** 4.954/4.954 objetos, 0 erros · 666 células organizadas, 4.398 arquivos ·
**0 camadas faltantes** contra o censo · +2.136 arquivos linkados no repo, zero
sobrescrita.
**Achado que corrige uma expectativa documentada:** o caveat "o ⑥ do bucket nunca tem
footer" é **falso para a rodada-42** — o espelho é pós-conclusão, então as células das VMs
vieram COM footer (zero substituições necessárias). As 8 sem footer são do `env_c311`
(perda na ESCRITA, `ModuleNotFoundError: google` em `mirror_run`), não do upload.

### F5.1 · Gates de protocolo
**Como:** `f5/baterias/gates_f51.py` roda `scripts/portao.py` célula a célula (accept por
cartão + auditar + `final_eval --check` no offline), 6 workers, no env_main (bug B3).
**Resultado 1ª passada:** 617 verdes / 49 vermelhos. **44 dos 49 tinham causa única**: a
camada ⑦ do e103 **nunca foi gerada** — ela nasce fora do run, por driver pós-hoc
(`final_eval`, DI-08), e o driver não rodou para as células da vm3. **O censo não acusou**
porque seu gabarito de camadas é a assinatura MODAL do config (se nenhuma célula tem ⑦, a
ausência é invisível).
**Ação:** a torre gerou as 45 ⑦ (mandato DI-08 "escrita pós-hoc pela torre") — 45/45
verdes na geração e 45/45 no re-gate; 90 arquivos subidos ao bucket com autorização do
autor.
**Resultado final:** **661 verdes / 5 vermelhos**, todos dissecados: 4 são falsos-vermelhos
de tolerância (desvio **relativo** 1,5e-5–7,3e-5 no recomputo da ⑦; mecanismo provado =
ULP-float32 × número de condição do problema; o clip nos bounds foi descartado como causa)
e 1 é real — `sweep-big-mvns/c311/MMF16_20`, o bug B1 confirmado nos dados (`status=ok`
com `motivo_parada='gpy_bfgs_linalg'`, 0 blocos de sonda, só fase build).

### F5.2 · Integridade, contrato, métricas, sonda, tempo
**Como:** 5 scripts em `f5/baterias/` (`f52a` a `f52e`).
- **a) integridade:** abriu TODO arquivo das 665 (~4.490): parquet via pyarrow, jsonl
  linha a linha, manifesto. **Zero ilegíveis.** 105 ③ vazias = pisos, por desenho.
  **1 reprovação nova:** `main/b1/WFG1` (⑥ com 49 eventos truncados no meio do JSON, sem
  footer — escrita concorrente na vm3, janela O-19). 5 células com 1 linha órfã, aprovadas.
- **b) contrato:** 664 × 7 camadas contra o `CONTRATO_DE_DADOS`. **Estrutura 100%**
  (contagens por tier, fases, schemas, blocos de sonda, ⑦, `fe_final`, `q=10`,
  `sigma_dict`). **1 não-conformidade:** `params` ausente no ⑤ de **7 configs (197
  células)** — fallbacks verificados (header do ⑥ / `artifacts/params.json`), sem perda.
- **c) métricas:** gate D92 (1,04333) antes; `metrics_from_real` nas 664 → **0 erros**;
  664 trajetórias de 20 checkpoints.
- **d) tempo:** **665/665 com `timing.tempo_total_s`** (zero buracos). Heatmap +
  projeção **≈10.173 h-core** para 30 sementes. *A coluna `maquina` foi corrigida depois
  (F5.3a) para 31 células recuperadas no Mac — o roster mentia (O-19).*
- **e) sonda:** 461 células regressoras → **44.928 medições** (WAPE/corr/cobertura por
  bloco×objetivo, join posicional, des-transformação via `transf_params`), **zero avisos**.
  Reproduziu TODOS os comportamentos previamente documentados, agora em 25 problemas.

### F5.3 · Análise de fidelidade por config (o coração)
**Como:** 2 workflows. Primeiro 5 **leituras profundas** grounded (que originaram o
protocolo), depois os pilotos e o fan-out. **Todos os 24 configs foram analisados em
TODAS as suas células** — não amostra.
**Resultado:** 24 relatórios, 51–100 mil caracteres cada, com dissecação narrativa de
20–31 aspectos. Score médio **9,33**; **todos ACEITAR**; 13 achados classe (3).
**Nota de processo:** os 5 pilotos foram re-executados no formato rico a pedido do autor;
os relatórios cresceram 4–6× (c311: 16k → 100k chars) e **as notas mudaram com causa** —
c217 9,0→9,5 (duas identidades fechadas novas), c311 8,5→9,5, e81 10→9,5 (a análise mais
funda ACHOU um classe (3) que a versão rasa não via).

### F5.4 · Verificação adversarial
**Como:** 14 agentes — 13 céticos (1 por achado, viés de REFUTAR, roteiro de 4 tentativas
de derrubada) + 1 investigador de padrão sistêmico.
**Resultado:** **5 refutados** · 6 confirmados como **(d) instrumentação/log** · 1 como
**(b) comportamento legítimo → vira resultado** · 1 como **(c) dado descasado** ·
**ZERO da categoria (a) — nenhum bug de implementação de algoritmo em 24 configs.**
**O padrão sistêmico** (o achado mais valioso): 34/666 células com assinatura anômala;
4 com bucket ≠ Mac, **todas ZDT4**, incluindo uma que nenhum analista vira
(`sobol_batch/q10_ZDT4`). **A causa registrada estava errada** — não foi "provisionamento
copiou `data/`", são duas causas encadeadas: `is_run_done` pula a célula quando o smoke
deixou artefato + `AuditLogger` abre o ⑥ em append cego (`src/audit_log.py:55`).
**Por que ZDT4:** é a célula-smoke canônica (menor D dos 5 do batch; `accept.py:256` usa o
par `("ZDT4", 42)` literalmente). **Dano real = 1 célula** (`batch/c149/ZDT4`, quimera
provada: ③ bate 2.000/2.000 com a ① do Mac e 0/2.000 com a ① do próprio bucket).

### F5.5 · Transversais
**Como:** `f55_transversais.py` + `f55b_adendo.py` + (após crítica) `f55c_correcao_offline.py`.
**Resultados:** a régua SA×pisos por dimensão **e por família** · ranking global · o
endpoint ⑦ do offline · sweep · batch vs Sobol · ablações D77 e big.
**Correção metodológica que a própria validação produziu:** a §4 (sweep) usava a métrica
da camada ①, que **empata por desenho** entre os configs offline (119 linhas → 30 valores
distintos; 30/30 grupos com valor único). Refeita pela ⑦: *"mais dado → melhor"* cai de
**46×4 para 29×21**; LHS×MVNS de 32×27 para 27×32. A versão errada ficou como lápide.

### F5.6 e F5.7 · Consolidação
**Como:** 6 agentes — 4 extratores estruturados (6 configs cada → JSON), 1 consolidador de
escalações, 1 arquiteto do plano.
**Resultado:** `RELATORIO_FINAL_F5.md` (matriz-mestra 24×7 + "onde olhar primeiro" +
16 decisões do autor + 24 capítulos) e `PLANO_RODADA_PERFEITA.md` (17 bloqueadores com
arquivo:linha, número medido, impacto quantificado em 30 sementes, correção, custo e teste).

---

## 3. O CÓDIGO EXECUTADO E OS RESULTADOS (resposta à pergunta "rodou código?")

**Sim — 12 scripts próprios + os gates e a métrica oficiais do repo.** Todos preservados
em `f5/baterias/` e versionados.

| script | fase | o que faz | resultado medido |
|---|---|---|---|
| `organizar_666.py` | D2 | layout do autor por hardlink + melhor-fonte do ⑥ | 666 células, 4.398 arquivos, 0 faltas |
| `preencher_data.py` | D3 | completa o `data/` do repo | +2.136 links, 0 sobrescritas |
| `gates_f51.py` | F5.1 | `portao.py` nas 666 | 661 verdes / 5 vermelhos |
| `f52a_integridade.py` | F5.2a | abre todo arquivo | 0 ilegíveis; 1 reprovação (b1/WFG1) |
| `f52b_contrato.py` | F5.2b | 664×7 vs CONTRATO | 197 desvios, todos `params` no ⑤ |
| `f52c_metricas.py` | F5.2c | `src/metrics.py` (gate D92 antes) | 664/664, 0 erros |
| `f52d_tempo.py` | F5.2d | wall + heatmap + projeção | 665/665; ≈10.173 h-core |
| `f52e_sonda.py` | F5.2e | régua comum da sonda | 44.928 medições, 0 avisos |
| `f55_transversais.py` | F5.5 | régua, offline-⑦, sweep, batch, ablações | ver §2 |
| `f55b_adendo.py` | F5.5 | régua por família + ablação big | BBOB 66% … WFG 26% |
| `f55c_correcao_offline.py` | F5.5-corr | sweep refeito pela ⑦ | 29×21 (era 46×4) |
| `f5_autoauditoria.py` | final | audita o estado da própria F5 | **34 OK / 0 FALHAS** |

Além destes, **cada um dos 38 agentes** (24 analistas + 14 céticos) executou baterias
próprias em Python sobre os dados — preservadas em `f5/baterias/{config}/` e
`f5/baterias/f54/{achado}/` (934 arquivos, 99 MB).

**A autoauditoria final** (`f5_autoauditoria.py`, re-executada agora) confere: os 15
artefatos obrigatórios existem · 24 relatórios · 14 vereditos · 664 trajetórias · 666
células organizadas · gates 666 linhas/5 vermelhos · métricas 664 sem erro · scores 24 com
média 9,33 e todos aceitar · sonda 44.928 · **gate D92 re-executado = 1,043327** · as
correções seguem aplicadas (⑦ do e103 com 100 linhas; ⑥ do e81 com 95 footers em modo 444)
· os 666 ⑥ locais idênticos ao bucket exceto as 2 versões do Mac · git limpo · 24 commits
`[F5*]` · as 3 exclusões citadas no relatório final.

---

## 4. RESULTADO CIENTÍFICO — o que a F5 estabeleceu

1. **Nenhum dos 24 algoritmos foi implementado errado.** 14 céticos com viés de refutar,
   sobre 666 células, não acharam um único bug de mecanismo. O que precisa de reparo é a
   plumbing.
2. **A régua da tese precisa ser reformulada.** *"A vantagem do surrogate cresce com D"*
   veio de 3 problemas na R1. No grid completo o que separa é a **família**: BBOB 66% ·
   ZDT 62% · MMF 62% · DTLZ 34% · WFG 26%. ⚠ Com o freio: só **54/305 (17,7%)** das
   comparações estão acima do piso de ruído entre máquinas.
3. **No offline, o endpoint é a ⑦, não a ①** — a ① é o dataset compartilhado e empata por
   desenho. Pelo endpoint correto: e103 vence 17/25 no `off`; no sweep, c311 lidera.
4. **Os GPs locais do c311 valem 7 de 9 células big** vs a árvore pura (`treed_media`), a
   ~100× o custo.
5. **A contaminação de proveniência tem causa provada e correção barata** (~19 h) — sem
   ela, 30 sementes produzem ~1.020 células anômalas e ~30 quimeras em 19.980.

---

## 5. INCIDENTE DA PRÓPRIA VALIDAÇÃO (auto-reporte)

Um agente da F5.3 invocou `experiments.py` para `batch/e81/ZDT4`. A célula estava
`is_run_done`, então foi no-op — **exceto pelo `AuditLogger`, que appendou 10 pares
header/footer vazios ao ⑥** (28/07 23:59Z a 29/07 01:59Z). É a demonstração acidental do
bloqueador B-02 do plano.
**Apuração:** comparei os **666 ⑥ locais contra o bucket** — 665 idênticos; 3 divergentes,
dos quais 2 (`c149/ZDT4`, `sobol_batch/ZDT4`) são as versões do Mac de 24/07
(pré-existentes) e apenas `e81/ZDT4` foi alterado na minha janela.
**Correção:** restaurado bit-a-bit do bucket (95 footers) e congelado em modo 444; backup
do contaminado preservado. Nenhum parquet, manifesto ou outra célula tocado.
**Regra que fica:** agente de análise não invoca `experiments.py`, nem para no-op.

---

## 6. ⚠ AS 16 DECISÕES EM ABERTO — a torre central DEVE levantá-las com o autor

**Nenhuma bloqueia a entrega da F5; TODAS bloqueiam o disparo das 30 sementes.** Cada uma
está detalhada, com opções, recomendação da torre e consequência de cada escolha, em
`f5/RELATORIO_FINAL_F5.md` §2.2.

| # | decisão | recomendação da torre |
|---|---|---|
| **D1** | Veredito de fidelidade por config: quem é `aceitar` limpo e quem é `aceitar+caveat` | 16 limpos (incl. `moead` promovido a 10 após o M16 ser refutado) + 8 com caveat |
| **D2** | Destino da célula reprovada na F5.1 (`c311/swap_big-mvns_MMF16_20`) | re-rodar (é a única ausente da ablação big) |
| **D3** | Destino da reprovada na F5.2a (`b1/WFG1`) | manter o IGD+ (camadas de dado íntegras), re-rodar na rodada perfeita para recuperar o ⑥ |
| **D4** | Destino do dado descasado (`c149/q10_ZDT4`) | **corrigir a redação**: sai **1 camada** (a ③), não a célula |
| **D5** | Enquadramento das 25 células ⚪ sancionadas como resultado publicável | publicar como limitação medida do método |
| **D6** | As 3 falhas algorítmicas reais + 1 morte sem manifesto: defeito ou limitação? | comparar com a referência ANTES de decidir (regra do INVENTARIO §4.1) |
| **D7** | Estender a DI-40 e **corrigir o número que a justificou** (~6,3 h → 0,87–2,99 h medido) | corrigir o REGISTRO e estender com base empírica |
| **D8** | O enunciado público sobre os achados classe (3) | "14 céticos, 666 células, zero bugs de algoritmo" |
| **D9** | `b5m-A8` vira resultado da dissertação (classe b) — e **não** inserir guard | aceitar como resultado; guard seria extensão nossa e mudaria o mecanismo medido |
| **D10** | A régua por família substituir "a vantagem cresce com D" | sim, **com o freio** dos 17,7% conclusivos |
| **D11** | Tornar obrigatório o endpoint ⑦ para todo o offline (§4 e §6 da F5.5 ainda usavam a ①) | obrigatória — a §4 já foi corrigida; a §6 falta |
| **D12** | O caveat do tier `small` do c311 (fora do envelope do paper) | declarar explicitamente na dissertação |
| **D13** | **O que corrigir ANTES das 30 sementes** (bloco fechado de ~16–18 h) | os 5 itens de raiz: anti-append, no-op, `campanha_id`, gates de proveniência, `mirror_run` no aborto |
| **D14** | O que pode ir DEPOIS (doc-only) | `params` no ⑤, glosa `p0`/`p1`, regra R4 |
| **D15** | Semeadura: `iteration_seed` não depende da célula ⇒ n efetivo = 1 por config no offline | ok para a s42; **decisão explícita do autor para o M8** |
| **D16** | Corrigir 6 números publicados que a F5.4 provou errados | corrigir (o principal: o χ² pseudorreplicado do `moead_media`) |

---

## 6-bis. LAUDO DA INSTRUMENTAÇÃO (documento irmão)

`handoff/F5-LAUDO-INSTRUMENTACAO.md` responde às perguntas do autor sobre retry, sonda e
tempo, com 8 recomendações medidas. **A crítica: a identidade da referência do
classificador não é logada em c217/c122/e74 (0/25 células cada) — sem ela a qualidade do
classificador é NÃO-MENSURÁVEL, e isso é irrecuperável a posteriori.** Custo total do
laudo: ~2 h de código. Traz 1 decisão para o autor (sonda estratificada).

## 7. COMO CONTINUAR

1. **Autor decide as 16** (§6) — a maioria em bloco, com as recomendações.
2. **Torre central executa o `PLANO_RODADA_PERFEITA.md`** — bloqueadores primeiro
   (~19 h), com os testes que cada item exige.
3. **Re-validar o harness** e só então disparar as 30 sementes.
4. **A F5 vira o molde da validação da próxima rodada**: o protocolo v1.1, a bateria
   U1-U12, os 3 gates novos (já escritos em `f5/baterias/f54/padrao_zdt4/`) e a
   autoauditoria são reutilizáveis como estão.
