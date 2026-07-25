# HANDOFF COMPLETO DA TORRE DE CONTROLE — ua-dd-saea (2026-07-25)

> **Para a instância Claude que acaba de nascer:** este arquivo te dá TODO o conhecimento da
> torre de controle deste projeto. Leia-o inteiro, depois leia a memória persistente
> (`/Users/gmello/.claude/projects/-Users-gmello/memory/`) e o `REGISTRO_DECISOES_IMPLEMENTACAO.md`.
> Com esses 3, você É a torre.

---

## 1. QUEM VOCÊ É E COMO TRABALHA

Você é a **"torre de controle"** do pipeline experimental do mestrado do Guilherme (PPGCC/UFMG,
defesa ~set/2026). Você NÃO implementa algoritmos — sessões frescas de Claude Code implementam,
1 cartão por sessão. Você:
1. **Escreve os prompts** dessas sessões (molde: `claude_code_context/PROMPT_MESTRE.md`).
2. **Valida exaustivamente cada retorno**: forense git (commits/arquivos/interseções em
   paralelismos) → gates ao vivo (suíte, preflight, portão) → workflow multi-agente com
   **refutação adversarial** → corrige direto o que é do seu mandato (gates/lançamento/docs/
   metadados) → escala o resto como DECISÕES numeradas (DI-xx) para o autor ratificar.
3. **Mantém TODA a documentação** (território RI-12): SPEC + bundles gerados, CONTRATO,
   REGISTRO, PROGRESSO, ORQUESTRACAO, RUNBOOK, memória persistente.
4. **Responde no padrão 4-partes**: (1) decisões em aberto p/ o autor; (2) validação exaustiva;
   (3) registro rico nos artefatos; (4) tabela de 15 milestones (o atual decomposto) + próximos
   5 passos.

**REGRAS INVIOLÁVEIS (do autor):**
- **NUNCA `git push`** (push/tag = ação do AUTOR) · **NUNCA `git add -A`** (add explícito;
  staged alheio = aguardar 2-5min, nunca unstage).
- **Pins/ambientes = decisão do autor (D80)**; locks são a verdade.
- **Fidelidade = julgamento MANUAL do autor, a posteriori (D97)** — NUNCA auto-consertar
  fidelidade; divergência código×paper segue a bússola D29 (🔴🔵🟠🟣🟢).
- **Ambiguidade/conflito ⇒ PARE e pergunte (D81).**
- `data/experiments/_baseline_pre_retrofit/**` — NUNCA escrever.
- Bundles NUNCA regenerados com sessão de implementação aberta; repo hands-off da torre
  enquanto sessões de implementação estiverem ativas.
- Coexistência de sessões paralelas: write-sets disjuntos, testes importáveis desde o 1º write,
  1 core/run (D79), PYTHONHASHSEED=0 + pins de thread em invocação direta. Funcionou 4× sem
  conflito (b5∥c311 · c311-B∥piso-off · T7→T6 · T8∥T9).

## 2. O PROJETO EM UMA PÁGINA

Comparação experimental de **22 algoritmos SA-MOEA + pisos = 24 configs** × **25 problemas** ×
**30 sementes {0-28,42}** em **4 tipos de experimento**: `main` (online q=1, 17 configs,
maxFE=31D−1), `off` (offline: e103/b5r/b5m/c311/moead_media, surrogate treinado 1× num dataset),
`sweep-{small,medium,big}-{lhs,mvns}` (offline variando tamanho/distribuição do dataset; big =
só c311+treed_media), `batch` (q=10: c149/c262/e81/c154/sobol_batch, maxFE=11D−1+200·q).
**Grid total: `runs_matrix.csv` = 20.850 runs; na semente 42 = 695 células.**
Stacks: MATLAB/PlatEMO (13 configs, Mac) + Python (BoTorch/standalone/DESDEO/GPy, 6 venvs).
Protocolo: DoE 11D−1 do artefato bit-a-bit; cache-hit=0 FE (D89); hard-stop exato; SeedSequence
(base, alg_id, iter, uso_id) D62; export 7 camadas (①real ②pop ③surrogate+SONDA ④timing
⑤manifesto ⑥jsonl ⑦__final p/ offline); sonda 2000 (online) / 1×20000 (offline), custo 0 FE;
teto wall 12h só no stack Python (DI-35.5/DI-38a); MMF16_20 substituiu MMF1 em sweep+batch (DI-35.3).

## 3. O FILME (cronologia completa)

- **F0 (jul/15-16):** harness, DoE artefato, export, métrica (HV âncora D92). M1 ✅.
- **R1 MATLAB (jul/16-18):** c217 (caso-modelo, D97 9/10) → c141, b3+b4 (fusão), b1+e7, c238
  (classdef N.5), pisos (nsga2/nsga3/moead/smsemoa N=20), e74 (árvore 4.1 própria), e103
  (offline). 10/10 ✅. Dossiê de fidelidade R1 materializado.
- **R2 BoTorch (jul/17-18):** R2-00 ∥ c238 → c262 (qNEHVI, melhor do set nos pilotos) → c154
  (JES, curinga de custo). ✅.
- **R3 standalone (jul/19-23):** R3-00 → c122 → b5 (b5r mode-7-v3 + b5m mode-12, env_b5
  py3.7/pandas 1.3.5 DI-28) ∥ c311 (env_c311 py3.8/GPy, predict_batch p/ sonda, contador
  geracao 2-fases) → c149 (HVI-greedy D96) ∥ e81 (qPOTS 0.16.1, straddle fix) → piso-off
  (moead_media DESDEO mode 12, D77). **21/21 ✅** (DI-29).
- **Fechamento (jul/23):** auditoria exaustiva de encerramento DI-31 (9 auditores; roster
  fantasma 'b5' corrigido → KNOWN_ALGORITHMS derivado do dispatch). DI-30 (B2/B3/D97-b5m).
- **Builds da torre (jul/23):** DI-32: T1 portao.py (driver de portão) + T2 enable_bucket +
  T3 driver ⑦-offline + T4 doc-sync + T5 hardening RNG R2-00.
- **T7+T6 (jul/24):** fio do sweep (tier/dist do token) + batch q=10. Validação DI-34: 5 fixes,
  incl. 🔴 fio do q (Q_BATCH=10 não chegava ao runner — 3º bug da "família camada-de-lançamento").
- **F1 provisionamento (jul/23-25, ∥):** cowork com handoff próprio. Mac A ✅ + VM-1
  `v5-mestrado` ✅ + VM-2 `mestrado-v6` ✅ (100% até o 🔒). **Mac B FALHOU** (High Sierra) →
  Mac A leva os 12 MATLAB + e103 (e103 SERIAL — ponte falha em parfor). Azure F64s_v2 = trilha
  M8 (⚠ pin R2025a; template default R2025b = problema D80).
- **DI-35 (jul/24):** grid definitivo — MMF16_20 total no sweep+batch, piso no sweep
  (treed_media=23), teto universal 12h (`--teto-s 43200`), matrix 19.950→20.850, datasets s42.
- **T8∥T9 (jul/24):** T8 = treed_media (piso-big, 6-14s/célula!); T9 = calibração batch POR
  MEDIÇÃO (c262 batch=2,2h CHEIO; c154 FLOOR ≥30h; knob per-D 1D/50D batch-only shipado).
- **DI-36 (jul/24):** validação T8/T9 — 1 ALTA: projetor de wall-clock não-batch-aware
  (superestimava ~q×; abortaria espúrio o c262 batch; era a causa-raiz do falso "56h" do T6).
  Fix `acfac4b` (passo=mediana dos deltas; q=1 bit-igual) + guard `913bd00`. 4º bug da família.
- **DI-37 (jul/25):** autor ratificou 7 itens em bloco (c154 truncado, c262 cheio, knob per-D,
  caveat D97 confounders, ⑦-teto=rito-piso, naoperturbacao teste-only, confirmações T8) +
  doc-sync (commit `649d0ea`).
- **Auditoria de prontidão (jul/25):** pegou **3 ALTA no doc-sync da própria torre**: (i) teto
  NÃO existe no MATLAB; (ii) BoTorch aborta por PROJEÇÃO ANTECIPADA (11ª iter) SEM parquets —
  a premissa "truncado ~it 50-80 com curva parcial" da DI-37.1 era FALSA; (iii) e103-sweep órfão
  dos comandos. + 4 MEDIA (heading V-B.5 engolido; 19.950 stale; §2.3 rsync; check_fe skip só
  no e81). Tudo corrigido (`e8e5709`).
- **DI-38 (jul/25):** autor decidiu **(a) manter aborto-por-projeção**; T10 (rito de truncamento
  BoTorch) → backlog. Doutrina nova: **rodar → colher imperfeições → UM refinamento final**.
  Torre tornou o (a) operável: portão reporta **⚪ aborto-sancionado** (não vermelho), check_fe
  skipa antes da ①, +3 testes (`1c2811b`). Suíte **394 OK**.
- **CONGELADO:** autor deu **push + tag `rodada-42-freeze`** (HEAD `1c2811b`).
- **AGORA (em voo):** a **VALIDAÇÃO FINAL** — workflow `wf_c451718a-b88` com 32 auditores
  fresh-eyes (20 por-config + 12 transversais) + refutação adversarial, 100% do código + os 94
  smokes em disco. Ver §6.

## 4. MAPA DE ARTEFATOS (onde está TODO o conhecimento)

**Raiz do repo: `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/`**

| Artefato | Para quê / quando ler |
|---|---|
| `CLAUDE.md` | Porta de entrada do repo. Ler SEMPRE em sessão nova. |
| `HANDOFF_TORRE_COMPLETO.md` | ESTE arquivo — o handoff da torre. |
| `REGISTRO_DECISOES_IMPLEMENTACAO.md` | **O CÉREBRO**: PARTES A1-A27 = DI-01..DI-38 com o porquê de tudo + PARTE B histórico. Ler para qualquer decisão/contexto. |
| `PROGRESSO.md` | Diário cronológico do projeto. Ler para "onde estamos". |
| `ORQUESTRACAO_MESTRE.md` | Status board da torre + invariantes de prompt + matriz de envs + plano por milestone. Ler antes de montar prompt de cartão. |
| `RUNBOOK_VALIDACAO_42.md` | **Manual do disparo da rodada-42**: 3 máquinas, comandos exatos por máquina/experimento, critérios F2, §6-bis correções de campo, §7 custos/expectativas (⚪ do c154). Ler ANTES de disparar qualquer célula. |
| `CONTRATO_DE_DADOS.md` | Contrato COMPLETO do export (7 camadas + sonda + jsonl por config). Obrigatório p/ qualquer cartão que grave dados. |
| `HANDOFF_MESTRE.md` | Orientação geral p/ sessões de implementação. |
| `handoff/*.md` | 1 handoff por cartão executado (o "o quê" + relatórios). `handoff/F1-ASSISTENTE-PROVISIONAMENTO.md` = handoff do cowork de provisionamento das máquinas. |
| `cards/INDEX.md` | Índice de cartões (1 sessão = 1 cartão). |
| `DOSSIE_FIDELIDADE_R1.md` | Dossiê p/ o julgamento D97 do autor (21 notas). |
| `claude_code_context/SPEC_experimentos_v5.2.md` | **FONTE ÚNICA DA VERDADE** (consulta pontual, nunca leitura integral). Precedência: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos. |
| `claude_code_context/artifacts/` | 8 machine-readable: `runs_matrix.csv` (20.850), `seeds.json` (24 alg_ids; sobol_batch=22, treed_media=23), `envs.json` (alg→env), `params.json` (Balde B), `decisions.json` (D53-D100), `anchors.json` (âncoras de patch), `repos.lock`, `characteristics.csv`. |
| `claude_code_context/{00_fundacao..50_analise_R4}/` | Bundles GERADOS da SPEC por `gen_bundles.py` (regenerar após QUALQUER edição da SPEC; regen é in-place e idempotente). 1 arquivo por algoritmo. |
| `claude_code_context/PROMPT_MESTRE.md` | Molde de prompt por sessão. |
| `scripts/` | Os gates: `accept.py` (cartões+catch-all F0-01), `auditar.py` (conteúdo/sonda/binding offline), `final_eval.py` (⑦), `portao.py` (driver: accept+auditar+final_eval por run; `--varredura`; ⚪ sancionado DI-38a), `preflight.py` (lacres/tree_sha256), `progress.py` (censo/timing), `regressao_q1.py` (prova bit-a-bit do knob c154). |
| `requirements/` | PROVISIONAMENTO.md + manifests + `locks/` (lock-as-truth D80). |
| `data/doe/` (1502 arq.) `data/datasets/` (1570) | RASTREADOS NO GIT (~190MB) — vêm no clone. |
| `data/experiments/` | 94 runs de smoke (main/off/sweep/batch) + stubs. `_baseline_pre_retrofit/` = INTOCÁVEL. |
| `src/` | Runners: 13 MATLAB (`*_instrument.m`+`*_sonda.m`+experiment.m/FEBudget.m/RunBuffer.m) + Python (`c262_qnehvi.py`, `c154_jes.py`, `c122_thetadeadp.py`, `b5_prob.py`, `c311_tgprmo.py`, `c149_lbnmobo.py`, `e81_qpots.py`, `piso_offline.py`, `treed_media.py`, `sobol_batch.py`) + núcleo (`export.py`, `manifest.py`, `naming.py`, `budget.py` [K_BATCH=200/Q_BATCH=10], `doe.py`, `atomic_io.py`, `gcs.py`, `experiment.py`, `botorch_harness.py`, `standalone_harness.py`). |
| `algorithms/` | Árvores vendorizadas: PlatEMO 4.2, PlatEMO 4.1 (e74), b5_Prob-RVEA, framework/ c311. NÃO editar vendored (ganchos em runtime). |

**Fora do repo:**

| Onde | O quê |
|---|---|
| `/Users/gmello/.claude/projects/-Users-gmello/memory/MEMORY.md` + `implementacao-experimentos-estado.md` | **Memória persistente da torre** — estado vivo + lições. Toda sessão nova da torre lê isto automaticamente. |
| `/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python` | O interpretador env_main do Mac (suíte/gates/pyarrow). Usar por caminho completo. |
| VM-1 `v5-mestrado`, VM-2 `mestrado-v6` (Vertex, us-central1-a) | Provisionadas 100%, aguardando `git pull` da tag (🔒). Evidências D80 em `~/d80_evidencia`. |
| `gs://mestrado_experiments` | Bucket (dual-write Python; `_provision_check/` a limpar no final). |
| GitHub `github.com/melloguin/ua-dd-saea` | Remoto; tag `rodada-42-freeze` já pushada (HEAD `1c2811b`). |

## 5. LIÇÕES APRENDIDAS (as armadilhas que já mordemos)

1. **Família camada-de-lançamento (4 bugs)**: roster fantasma 'b5' (DI-31) · kwargs-transporte
   E1 (T7) · fio do q (DI-34) · projetor não-batch-aware (DI-36). Moral: o fio
   despachante→runner é o ponto cego; TODO config/experimento novo exige teste do fio.
2. **Fiação de config novo tem ~6 sítios**: manifest.OFFLINE_ALGS, standalone.OFFLINE_CONFIGS,
   auditar.OFFLINE, experiments._OFFLINE, portão CARTAO_POR_ALG, dispatch loaders.
3. **Doc-sync exige auditoria doc×código ANTES do commit** — a torre escreveu 3 ALTA na SPEC
   no dia do congelamento (teto "universal" que não era; camadas parciais que o BoTorch não grava).
4. **Rodar a suíte ANTES de commitar** (2 quebras por commit prematuro).
5. **zsh word-splitting**: `set -- $spec` não separa; usar `${var%%:*}`.
6. **json.dump**: detectar o indent original antes de reescrever artifacts (diff de 261 linhas
   por reformatação acidental).
7. **Sessões desobedecem o prompt para obedecer a SPEC** — correto (precedência); o prompt da
   torre pode estar errado (caso B15.4→T8).
8. **Auditores de workflow podem violar read-only** (manifesto fantasma batch/c262) — sempre
   caçar artefatos espúrios após auditorias.
9. **`is_run_done` lê `failed` como não-pronto** ⇒ células ⚪ re-rodam se re-despachadas
   (re-invocação SEM c154 na lista).
10. **Portabilidade §6.2**: cross-machine = gates + CP-init bit-exato; NUNCA byte-identity de
    floats entre máquinas; bit-a-bit vale NA MESMA máquina.

## 6. ESTADO ATUAL EXATO + O QUE ESTÁ EM VOO

- **Repo CONGELADO e PUSHADO**: tag `rodada-42-freeze`, HEAD `1c2811b`, suíte 394 OK,
  preflight 0, portão 84 runs (5 stale conhecidos), zero decisões em aberto.
- **EM VOO — A VALIDAÇÃO FINAL** (pedido do autor: validação 100% fresh-eyes de todo o código +
  todos os smokes, com correção de bugs, decisões em aberto, melhorias — relatório em 5 pontos):
  - Workflow **`wf_c451718a-b88`** (task `w5ec9rskx`): 32 finders (20 por-config: b1,b3,b4,e7,
    c217,c141,e74,c238,pisos_online,e103,c262,c154,c122,b5,c311,c149,e81,moead_media,
    treed_media,sobol_batch + 12 transversais: despachante-python, despachante-matlab,
    export-core, gates, testes, artefatos, dados-global, rng-determinismo, fe-budget, docs-sync,
    matlab-arvores, portabilidade-vm) → dedup → refutação adversarial (2 lentes ALTA/1 MEDIA).
  - **Resultados persistem em disco mesmo se a sessão morrer**:
    output → `/private/tmp/claude-501/-Users-gmello/1dad1ee9-8028-4d8e-a5cf-e0264dcc7966/tasks/w5ec9rskx.output`
    journal (1 linha JSON por agente) → `/Users/gmello/.claude/projects/-Users-gmello/1dad1ee9-8028-4d8e-a5cf-e0264dcc7966/subagents/workflows/wf_c451718a-b88/journal.jsonl`
    script → `.../workflows/scripts/validacao-final-100pct-wf_c451718a-b88.js` (mesma pasta base do journal, dir `workflows/scripts/`)
  - **Instância nova**: NÃO relance o workflow (caro!). LEIA o journal/output prontos e
    consolide. Se incompleto, os resultados por-agente do journal bastam para consolidar
    manualmente. (resumeFromRunId só funciona na MESMA sessão.)
  - **Pós-consolidação (o plano combinado)**: aplicar correções do mandato da torre → escalar
    decisões → docs (REGISTRO A28+) → se houver fix de código: novo commit + AUTOR re-tagueia
    (`rodada-42-freeze` bump ou tag nova) e re-pusha → só então disparo.
- **Célula suspeita já anotada p/ o auditor de dados**: `data/experiments/main/c154b/` (1 run
  "ok" — NÃO é config do grid; investigar origem e deletar se espúrio).

## 7. EXPECTATIVAS OFICIAIS DA RODADA-42 (p/ ninguém diagnosticar errado)

- ~688 células com dados completos + **~6-7 células ⚪ aborto-sancionado** (c154 main/DTLZ2
  certa; ZDT1/WFG9 prováveis; 5 c154-batch) — morrem em ~min-1h por projeção, SEM parquets,
  curva no jsonl. Portão as reporta ⚪ (não vermelho). NÃO re-disparar.
- Pior célula com dados: c154/DTLZ2 seria 14,6h (morre no teto); célula cara real: c238/ZDT1
  ~3h55 (MATLAB, sem teto). Rodada ≈ 1-2 dias nas 3 máquinas.
- 5 runs stale pré-retrofit em data/ (c154/c217/c238/c262/e7 semente 0) serão SUBSTITUÍDOS.

## 8. BACKLOG DO REFINAMENTO PÓS-RODADA (REGISTRO A27)

T10 (rito truncamento BoTorch c/ camadas parciais) · teto wall no MATLAB · tensão ⑦×teto-
construção do c311 (M8) · env_c149_fallback sem lock · data/images vs .gitignore · rótulos
stale ORQUESTRACAO · varredura-N dos pisos (M11) · workflows Fable de fidelidade (F5) · lote
D97 do autor · limpeza `gs://mestrado_experiments/_provision_check/` · Azure/M8 (pin R2025a)
· + TUDO que a validação final e a execução das 695 células revelarem.

## 9. MILESTONES + PRÓXIMOS PASSOS

| M | Milestone | Estado |
|---|---|---|
| M0-M6 | Preparação → 23/23 configs + gates + F1 | ✅ |
| **M7** | **RODADA-42** (fidelidade definitiva + piloto timing) | 🟡 **ATUAL** |
| M8 | Bateria ONLINE (12.750) | ⬜ |
| M9 | Bateria OFFLINE (3.750) | ⬜ |
| M10 | SUB-batch 30 sementes | ⬜ |
| M11 | SUB-sweep + varredura-N | ⬜ |
| M12 | Consolidação/integridade | ⬜ |
| M13-M15 | Métricas · Estatística+IGDX · Dissertação | ⬜ |

**M7 decomposto:** M7.0 congelamento ✅ (push+tag feitos) → **M7.1 VALIDAÇÃO FINAL (em voo —
consolidar resultados do wf_c451718a-b88)** → M7.2 correções/decisões/re-tag se necessário →
M7.3 F2 desbloqueio das 3 máquinas (cowork F1: pull da tag + célula real + portão) → M7.4
disparo das 695 células (RUNBOOK §4) → M7.5 F4 portão-varredura nas 3 + F5 fidelidade Fable →
M7.6 F6 lote D97 do autor + GO/NO-GO M8.

**Próximos 5 passos:** (1) consolidar a validação final (ler journal/output do workflow);
(2) aplicar correções + escalar decisões + REGISTRO A28 + re-tag do autor SE houver fix;
(3) F2: desbloquear Mac A/VM-1/VM-2; (4) DISPARAR a rodada-42; (5) F4/F5: portão nas 3 máquinas
+ workflows de fidelidade → dossiê p/ o D97.
