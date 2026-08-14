# REGISTRO DE DECISÕES — FASE DE IMPLEMENTAÇÃO (DI-01…)

> **O que é.** O registro canônico e detalhado das decisões tomadas DURANTE a implementação do
> pipeline (pós-SPEC v5.2) — o companheiro da fase de implementação para o
> `claude_code_context/REGISTRO_DECISOES_pingpong_v5.md` (que cobre as D53–D86 da fase de SPEC).
> **Convenção:** decisões de implementação levam o prefixo **DI-**; não colidem com o espaço D1–D100
> do Anexo D da SPEC. Quando uma DI exige mudança na SPEC, a edição é executada pela torre numa
> janela documental (sem sessão de implementação ativa) e fica referenciada aqui.
> **Formato por decisão:** Contexto → Opções → Decisão → Justificativa → Evidência de verificação →
> Efeitos/ações → Referências. Decisor: **o autor** (Guilherme), em ping-pong com a torre.
> Última atualização: **2026-07-19** (DI-17: hardening do M7 adiantado, na PARTE A6).

---

## PARTE A — O lote de 2026-07-18 (fechamento da onda MATLAB + R2 parcial)

### DI-01 — Concretizações de âncora em bloco ✅ RATIFICADA
- **Contexto.** O `anchors.json` (D80) nasceu com âncoras "descritivas" (`<...>`) onde a SPEC ainda não
  tinha o literal exato. O protocolo estabelecido desde o pré-voo/c141: a sessão que implementa o
  patch CONCRETIZA a âncora com os literais reais e sinaliza para veto do autor.
- **Itens deste lote:** `b1-doe-D94` e `e7-doe-D94` (o par gera+re-escala substituído JUNTO pela
  injeção do X0 nativo — classe D94); `c238-hypervolume-rm` (as 2 linhas do mex Windows-only viram
  comentário-marcador — o literal stock desaparece, o que o preflight patch-aware exige);
  `e103-judgemodel` (concretizada na forma OR `| logical(eye(N))`, equivalente em 1 linha ao
  `Msite(logical(eye(N)))=true` do S.2-e103); `expect_after` do e103 endurecidos (`e103-pm-D93a`
  de "1" fraco → `{1,20,1,20}`; `e103-centros-D93` → literal `ceil(sqrt(Global.n_dataset))`).
- **Opções.** (a) Ratificar em bloco; (b) revisar uma a uma; (c) reverter para descritivas.
- **Decisão: (a) — ratificar em bloco.**
- **Justificativa.** Todas seguem o precedente formal (Sessão 1/c141/b3, já ratificado em D1/D4 da
  faxina de 2026-07-17); todas foram verificadas: o preflight as reporta como APLICADO, e as
  verificações adversariais da torre conferiram os literais contra o código real (b1/e7 na Sessão A
  4/4 CONFIRMED; c238 2C+1P; e74/e103 4/4). O catálogo auditável e mecânico é o objetivo do D80.
- **Efeitos.** `anchors.json` está canônico; nenhuma ação pendente.
- **Referências.** Commits das sessões (021e5f0, 8bd66b8, 82f4d47, 974c95b) + handoffs `R1-b1/e7/c238/e103`.

### DI-02 — Fixes de infraestrutura verificados em bloco ✅ RATIFICADA
- **Contexto.** Três consertos de infraestrutura nasceram DENTRO de cartões de algoritmo (não eram
  o escopo do cartão, mas bloqueavam ou ameaçavam a validade):
  1. **`write_surrogate` O(n²)→O(n)** (Sessão A/b1): os builders `arrayfun` de coluna string do
     writer MATLAB (infra do R1-00) travaram o export da ③ do b1/ZDT1 (757k linhas, 3h30 a 100% CPU).
     Reescrito em passada única pré-alocada.
  2. **Precedência de path do e7** (sombra DRLOS-EMCMO): cópia byte-idêntica do `Dropout/` vinha antes
     no genpath e anularia os patches SILENCIOSAMENTE. Fix-padrão `ensure_paths_<alg>` (prepend +
     asserts de `which`).
  3. **Família `onCleanup`/restauração de path** (c238 → e74 → e103, em evolução): sombra reversa do
     c238 (rmpath ao fim); e74 (worker de path dedicado: snapshot → rmpath 4.15 → addpath 4.1 →
     15 asserts → `onCleanup(path(prev))` restaura TUDO); e103 (idem, 25 asserts, remove as DUAS
     árvores-gorila).
- **Decisão: ratificar os três em bloco.**
- **Justificativa/evidência.** (1) equivalência do writer provada adversarialmente (análise
  linha-a-linha do diff + probe de schema old-writer×new-writer: 20 colunas idênticas; sem o fix, a
  bateria M8 seria inviável). (2) a sombra DRLOS provada real (cópias idênticas módulo CRLF; genpath
  alfabético; same-folder NÃO cobre subpastas) e o fix coberto por asserts. (3) provas de
  não-contaminação EXECUTADAS em processo compartilhado (e74: c217→e74→nsga2→b3, 4 verdes, `which`
  limpo; e103 idem), e o adversarial conferiu que o guard restaura o path INTEIRO e é armado ANTES
  dos asserts (mais seguro que o descrito).
- **Efeitos.** Padrões oficiais do projeto: (i) todo cartão MATLAB novo faz varredura por basename +
  prepend/assert se houver colisão; (ii) o writer O(n) é o writer de todos.
- **Referências.** `handoff/R1-b1-e7_RELATORIO-EXECUCAO.md`, `handoff/R1-c238.md` §3,
  `handoff/R1-e74.md`, vereditos adversariais em `DOSSIE_FIDELIDADE_R1.md`.

### DI-03 — Convenções de export por algoritmo (③/②) em bloco ✅ RATIFICADA
- **Contexto.** O schema §17.2 é ÚNICO para os 16 algoritmos, mas cada algoritmo tem semântica
  própria de surrogate. As sessões materializaram convenções por algoritmo, todas documentadas no
  manifesto (`sigma_dict`) e/ou jsonl — nenhuma muda o schema físico.
- **Itens ratificados:**
  - **b1:** ③ mono-output (mu_0 preenchido; mu_1.. NULL — o caso D47 que o F0-03 preparou);
    P4 = idioma L4 (`den(den==0)=eps`, resultado invariante no caso são).
  - **e7:** ③ em espaço do MODELO com `transf_params={ymin}` (cru = μ+ymin, invertível; a ① dá o cru
    real — leitura D47 da C3); carimbo `geracao=ciclo` (precedente b3, D2 da faxina).
  - **c238:** ③ em espaço do modelo `{min,range}` (mesma leitura D47; precedente e7); `'N',100`
    passado ao construtor é INERTE (o EIM é q=1 — documentado); carimbo `geracao=ciclo`.
  - **e74:** ③ com `pred_tipo` POR LINHA (classe|valor — nunca "híbrido"; adversarial: 0 violações em
    63k linhas); `sigma_0` = pseudo-σ POR ESTRATÉGIA (dist_dec|HV_gain|Eucli — os 3 não cabem no
    schema M=2; dicionário no `sigma_dict`); cadência da ② = a do `NotTerminated` stock (~4
    snapshots/ciclo — fiel ao stock; a série está no jsonl).
  - **e103:** ③ com 2 LINHAS POR MEMBRO (μ dos DOIS modelos — Kriging μ+σ e RBFN, σ NULL na RBFN — a
    materialização do "μ dos DOIS modelos" da L.15); ② offline = SÓ os membros do DATASET na
    população selecionada (única leitura em que a ② segue sendo "população REAL"); geração sem membro
    real fica sem linha (série completa no `n_ds_membros` do jsonl).
  - **c262 (A3):** ② no BO = o TRAIN SET completo por iteração (não o baseline podado do
    `prune_baseline`) — consistente com "salvar-tudo" (D54); o c154 herda.
- **Decisão: ratificar em bloco.**
- **Justificativa.** Todas preservam o schema §17.2 físico; todas são recuperáveis/invertíveis; todas
  auditadas pelos probes adversariais da torre; o R4 lê pelo `sigma_dict`/manifesto de cada algoritmo.
- **Efeitos.** O leitor do R4 usa o manifesto por algoritmo como dicionário de semântica. Duas regras
  de leitura já registradas para o R4 (ORQUESTRACAO/armadilhas): dedup por `solution_id` (nunca pelo
  X float32); `real_solution_id` tolera int32 e double+NaN.
- **Referências.** Handoffs §"vetos" de cada cartão; probes nos vereditos do dossiê.

### DI-04 — Leituras do c262 (A1/A2/A4/A5) ✅ RATIFICADA
- **A1 · Fonte do ref-point da aquisição = a tabela S.5 CONGELADA** (nadir+0,1·range, escala bruta,
  fixo por problema). Alternativa rejeitada: nadir observado por iteração (o análogo D96 do c149) —
  menos estável e sem respaldo no Anexo J para o c262. Registrado no manifesto (`acqf_ref_f`).
- **A2 · Truncamento 32-bit dos 3 seeds (h0/h1/h2)** derivados do `seeds.json`: o `torch.manual_seed`
  exige <2^32; a extensão do truncamento ao sampler e ao `optimize_acqf` fica CRAVADA agora —
  mudar depois quebraria a reprodutibilidade de tudo que já rodou.
- **A4 · Filtro do `NumericalWarning`** do gpytorch (artefato esperado do `train_Yvar=1e-6`): filtrado
  do stderr, CONTADO no jsonl (não silenciado de auditoria).
- **A5 · Teto-100 do stall-guard do runner**: backstop local (o D60-b oficial é do despachante);
  streak real máximo observado = 3.
- **Decisão: ratificar as quatro.** **Evidência:** receita L.10 conferida item a item pelo
  adversarial (CONFIRMED); a fórmula dos seeds validada contra o `seeds.json` pela torre.
- **Referências.** `handoff/R2-c262_RELATORIO-EXECUCAO.md` §9-A; dossiê seção R2.

### DI-05 — Política do kernel fusionado (B1) + doc-syncs (B5) ✅ APROVADA — execução agendada
- **Contexto.** Achado S.3#9 da sessão c262, CONFIRMADO adversarialmente no nível mais forte: o wheel
  OFICIAL do BoTorch 0.18.1 no PyPI **contém** o kernel C++ fusionado (`logei_fused.cpp` presente;
  byte-identidade instalado×wheel verificada por sha256 dos 494 arquivos do RECORD, 0 divergências).
  A premissa do S.3#9 da SPEC ("o fusionado é só do fork") está DESATUALIZADA. O kernel fusionado
  compila com `-march=native` → numérica potencialmente assimétrica Mac×Linux — exatamente o risco
  que o N.2.3 quer eliminar.
- **Decisão:** (i) **desligamento explícito do kernel fusionado (DEF-L2) vira POLÍTICA da Rodada 2**
  — todo runner BoTorch desliga no arranque (o c262 já faz; o c154 foi instruído; o despachante M8
  entra no hardening M7 com o mesmo desligamento); atenção: o desligamento é estado POR PROCESSO.
  (ii) **doc-sync do S.3#9 na SPEC** (corrigir a premissa + registrar a política) + **B5**
  (divergência cosmética `cache_root` tabela-K × §22.3 — vale o §22.3/None, precedência D83).
- **Execução:** a torre edita a SPEC + regenera bundles **na próxima janela documental** (sem sessão
  ativa — hoje o c154 está rodando). Junto com o doc-sync da DI-08.
- **Referências.** Veredito `c262-l10-fusedkernel` (dossiê); `handoff/R2-c262.md`.

### DI-06 — O pacote de hardening do M7 ✅ CONFIRMADO (escopo fechado)
- **Contexto.** Itens de robustez acumulados ao longo da onda, nenhum bloqueante para pilotos, todos
  necessários antes da bateria M8. O M7 (o portão) ganha um mini-cartão de hardening com o escopo
  FECHADO agora:
  1. Varredura de `.tmp` órfãos no arranque da esteira (kill duro/spot-VMs — achado adversarial F0-03).
  2. Guarda `mu/sigma` mais LONGO que M no `write_surrogate` (truncamento silencioso — F0-03).
  3. Major R2-00 nº1: `experiments.py::_run_one` SOBRESCREVE o manifesto rico do runner e não repassa
     `data_root`/`enable_bucket` → na bateria, a evidência de CP-init evaporaria e o dual-write nunca
     ligaria.
  4. Major R2-00 nº2: resume × bucket-only (D58) inexistente — `is_run_done` exige camadas LOCAIS; a
     poda da ③ pós-upload re-executaria c262/c154 eternamente na VM. Implementar o "resume lista o
     bucket".
  5. Roster COMPLETO do despachante (`experiments.m`/`experiments.py`): os pilotos rodaram via
     `experiment()` direto; a bateria precisa de todos os 21 configs no roster (pisos incluídos).
  6. `extra_manifest` no harness BoTorch (B2 — o blob do bucket não pode ficar 1 versão atrás das
     chaves novas tipo `acqf_ref_f`/`fused_kernel`).
  7. Desligamento do kernel fusionado no DESPACHANTE M8 (DI-05, por processo).
  8. Método de projeção de custo do M7 = WALL TOTAL, não série de fit (B4 — no c262 a busca domina:
     89–98% do tempo).
- **Referências.** ORQUESTRACAO §armadilhas; handoffs F0-03/R2-00/R2-c262/R1-pisos.

### DI-07 — Os três individuais do e74 ✅ RATIFICADA (com atenção de dossiê)
- **(a) `ndsort-obj` = NDSort sobre os objetivos REAIS dos pais.** A âncora dizia "preditos".
  **Adjudicação adversarial: FIEL-EQUIVALENTE (não-violação), com elementos de melhor-que-âncora.**
  O decisivo: "preditos" só existia no PLACEHOLDER do anchors.json; a SPEC (precedência D83) manda
  "NDSort → objetivos"; o `ClassifierSelect` stock não contém NENHUM regressor (só o `newpnn`
  classificador); o único regressor do algoritmo (`newrbe`) é interpolação EXATA — predito≡real nos
  pontos do arquivo (que é de onde os pais vêm); e o re-sim alternativo podia deixar a classe-1 vazia
  → `randi(0)` = crash novo. **Ratificada.**
- **(b) Fix opcional do re-sim do PNN NÃO aplicado — mantida SÓ a telemetria, com ATENÇÃO REFORÇADA.**
  ⚠ A verificação adversarial CORRIGIU o número da sessão: o desalinhamento máscara×Parent no ZDT1 é
  **~24,8%/ciclo (máx 91/100)** — não ~8% (o 8% era só o DTLZ2). A SPEC classifica o fix como
  "opcional" (§22, precedência sobre o [IMPL] do K.5.2) e o e74 bate os pisos mesmo assim — mas o
  item vira **ponto prioritário do julgamento em lote do autor** (dossiê): se o autor julgar material,
  o fix é promovido ANTES da bateria (custo: 1 arquivo + re-piloto do e74, ~10 min).
- **(c) D74 = min-max do FRONT-1 (ideal/nadir, coerente com D69) + política dos edges degenerados =
  "roda e loga"** (`cand_vazio`, `hv_range0`/RefPoint degenerado — a SPEC diz "política nossa").
  **Ratificadas.**
- **Referências.** Veredito `e74-patches-vs-bundle` + `e74-parquet-isolamento` (dossiê);
  `handoff/R1-e74.md` §8.

### DI-08 — 🔴 Persistência da avaliação REAL do ND final OFFLINE ✅ APROVADA — execução antes do R3
- **Contexto (a decisão estrutural do lote).** O §11/B7.5 da SPEC manda avaliar o conjunto
  não-dominado FINAL dos algoritmos offline UMA vez na função verdadeira — "a única chamada real do
  offline" — e computar as métricas sobre ele. Mas o desenho do cartão offline fixa ① = o DATASET
  (31D−1 linhas exatas, exigidas pelo gate) — as ~100 avaliações finais NÃO têm casa no export atual.
  Afeta os 5 configs offline: e103, b5r, b5m, c311, piso moead_media. Nada foi perdido nos runs do
  e103 (FinalDec ≡ decisões da ③ geração 99 — a avaliação é reconstituível).
- **Opções consideradas.** (a) Camada NOVA `__final.parquet`, avaliada PÓS-HOC em Python canônico
  (`problems.py`), uniforme para os 5 offline; (b) apêndice na ① com flag de fase "final" (quebraria
  o gate 31D−1 e a semântica "① = orçamento"); (c) avaliar dentro do run MATLAB (viola a
  uniformidade cross-stack e a contabilidade FEBudget); (d) só nas métricas do R4, sem persistir
  (perderia auditabilidade).
- **Decisão: (a)** — camada própria `__final.parquet` por run offline: colunas `x0..x{D-1}`,
  `f0..f{M-1}` (avaliados em `problems.py`), `origem_solution_id`/link à ③; escrita pós-hoc pela
  torre/harness Python (não pelo MATLAB); o gate offline ganha um check adicional (presença +
  consistência do `__final`); a avaliação NÃO conta no orçamento (é a exceção §11, documentada).
- **Execução (agendada, ANTES do R3):** a torre (1) edita a SPEC (§11/§17.7 + cartões offline) e
  regenera bundles na próxima janela documental (junto com DI-05); (2) define o
  `naming.layer_path(..., "final")`; (3) implementa o avaliador pós-hoc + o check no accept;
  (4) roda para o e103 (retroativo) e valida. Os cartões b5/c311/piso-off do R3 já nascem com o
  contrato pronto.
- **Referências.** `handoff/R1-e103.md` §8; SPEC §11/B7.5.

### DI-09 — 🟡 PROPOSTA (aguardando decisão do autor) — Instrumentação de assertividade dos surrogates
- **Contexto.** Pergunta do autor (2026-07-18): temos dados p/ analisar erro dos surrogates (WAPE,
  acurácia/recall na classificação) e a evolução do surrogate com as épocas, comparando os 16? A
  torre DEMONSTROU nos dados reais: regressores JÁ analisáveis (c262 WAPE 0,0011 melhorando 6,2×;
  e103 cobertura-1σ 50% = σ subestimado) MAS com contaminação in-sample (b3 "WAPE 0") e amostra
  enviesada por algoritmo; classificadores SEM rótulo verdadeiro persistido.
- **Proposta completa:** `PROPOSTA_DI-09_instrumentacao_surrogate.md` (raiz) — A1 marcador
  in-sample (`fe_treino_max`, 🔴), A2 sonda canônica 200 pts Sobol c/ f verdadeiro (`regime='sonda'`,
  🔴), A3 rótulo verdadeiro pós-hoc (R4), B1 hiperparâmetros/loss por refit, B2 tempos por fase,
  B3 dist. do infill ao arquivo, B4 análises sem persistência nova (NLL/CRPS/sharpness/Kendall-τ/
  contrafactual greedy-μ). NÃO propostos: genealogia de operadores (invasivo no stock), serialização
  do modelo (GB+ sem pergunta).
- **Sequenciamento proposto (mínimo retrabalho):** decisão agora → contrato na SPEC na MESMA janela
  documental do DI-05/DI-08 (1 regen) + artefato da sonda → o R3 nasce nativo → retrofit dos 12
  feitos no M7 (cartão DI-09-retrofit) + pilotos de validação → a bateria M8 já produz tudo.
- **✅ DECIDIDA pelo autor (2026-07-18): A1 + A2 + B1 + B2 + B3 aprovados; sonda com S=2000 pontos,
  cadência k=2 gerações (+1ª e última).** Volume estimado na bateria: ~260 GB extras (o autor decidiu
  ciente da aritmética; checagem de disco Mac/bucket entra no piloto M7; custo GCS ~US$5/mês).
  A3/B4 = análises R4 (sem persistência nova).
- **Cronograma EXECUTIVO (ajustado pelo autor):** o retrofit dos 9 configs SA-MATLAB **começa JÁ**
  (∥ c154 — a faixa MATLAB está livre; c154 é Python e não committa; janela de committer único) com
  o contrato provisório = a própria PROPOSTA (a formalização na SPEC §17.2.2 acontece na janela
  documental pós-c154, junto de DI-05/DI-08, 1 regen). Retrofit-Python (c262+c154+export.py+helper
  no harness) = cartão pequeno logo após o commit do c154 (pode ∥ R3-00 — faixas disjuntas). R3
  nasce nativo. Retry/registro/progress-bar = M7 (DI-06 ampliado).
- **Invariante do retrofit (o gate central): NÃO-PERTURBAÇÃO** — a instrumentação é read-only; a
  prova objetiva é a ① do run pós-retrofit ser IDÊNTICA à do piloto pré-retrofit (mesma semente ⇒
  mesma trajetória). Preditores ESTOCÁSTICOS (o MC-dropout do e7!) exigem save/restore do RNG em
  volta da predição da sonda — sem isso a trajetória muda e o retrofit REPROVA.
- **▶ EXECUÇÃO no stack MATLAB: ver DI-12 (PARTE A2)** — as 5 decisões que a execução do cartão
  `DI09-retrofit-R1` exigiu do autor, mais as correções/achados do lote.

### DI-10 — ✅ DECIDIDA (autor, 2026-07-18) — Enriquecimento do `.jsonl` (mecanismo por config)
- **Contexto.** Pergunta do autor: o jsonl mostra EM DETALHES o comportamento de cada algoritmo
  (vetores de decomposição, como o BO escolheu o ponto…)? A torre fez o mapeamento profundo dos
  22 configs sobre o S.7 existente e identificou os campos que faltavam.
- **Decisão:** mínimo comum novo em todo `<alg>_gen` (`fe`, `f_best[]`, `n_front1`, `modelo_hp`,
  tempos, `dist_min_arquivo`) + campos específicos por config (b3: `apd_sel`/`sigma_sel`/
  `adapt_delta_V`; c262/c154: `acqf_todos_restarts`/`n_baseline`/`mll_final`; c311: `n_folhas`/
  `profundidade`; e103: `divergencia_modelos`/`margem_3sigma`; pisos: `n_front1`/`f_best`/vetores
  de decomposição no header; tabela completa na SPEC §S.7.1 e no CONTRATO_DE_DADOS §6.1).
  **Regra:** tudo read-only; grandezas que exigiriam patch invasivo no miolo stock REJEITADAS
  (MOEA/D replace-count, NSGA-III niching, genealogia de operadores).
- **Execução:** retrofit-R1 (já contratado) + retrofit-Python + R3 nativo.
- **Referências.** SPEC §S.7.1 (v5.2.1); `CONTRATO_DE_DADOS.md` §6.

### 📌 NOTA — Janela documental ANTECIPADA pelo autor (2026-07-18, v5.2.1)
O autor ordenou a atualização documental completa ANTES do fechamento do c154 (sessão ativa apenas
em faixa Python; regen auditado: SÓ 03_contrato_export + linha S.3 + SPEC). Executado pela torre:
**`CONTRATO_DE_DADOS.md`** (raiz — o documento-referência definitivo dos outputs, réplica+expansão
do §17 com mocks) + SPEC v5.2.1 (§17.2.2 sonda S=2000/k=2 · `fe_treino_max` na ③ · §17.6
expandida com `tempo_geracao_s`/`tempo_pred_sonda_s` + manifesto timing OBRIGATÓRIO ·
S.7.1 DI-10 · `__final` DI-08 · S.3#9 DI-05) + bundles regenerados. PENDENTE da janela original:
apenas o item B5 (`cache_root` — cosmético, card do c262).
### DI-11 — ✅ CRAVADA EM LOTE (autor delegou à recomendação da torre, 2026-07-18) — as DEFS-c154 e pendências correntes
1. **NaN-guard do JES (D-1): MANTIDO/ratificado** — guard só na SELEÇÃO, acqf crua intocada, logado
   (mesma classe das guardas já ratificadas; sem ele o ZDT1 é irrodável).
2. **Gaps v5.2.1 (D-4): já embutidos no cartão DI09-retrofit-R2** (backfill tempo_busca_s do ④ via
   jsonl; colunas novas; mll_final; n_baseline N/A no JES → logar `n_train`, doc no sigma_dict).
3. **Médias do c154:** escada de fallback do RuntimeError MANTIDA (0 disparos reais) · likelihood
   default + assimetria kernel-Gamma×likelihood MANTIDAS como implementadas (mexer = mexer em
   numérica; documentado no manifesto) · `init_batch_limit` 32 (c262) × 256 (c154) SEM unificação
   (numericamente neutro — muda só velocidade; documentado) · **projetor de wall-clock: consertar
   NO retrofit-R2** (teto de tempo DECORRIDO independente da projeção pós-10-iters — adendo B).
4. **Baixas do c154 + B5 (`cache_root`):** agendadas para a PRÓXIMA janela documental (pós-retrofits)
   — doc-syncs puros (MatheronPathModel seed; uso_id do optimize_acqf no catálogo; token c154b).
5. **Política b5/c311 (M5): tentar pins VIZINHOS no Mac com validação de equivalência do
   GPR/stack; se inviável → exceção VM** (efetivação nos cartões deles; o R3-00 só deixa o
   mecanismo subprocess-por-venv pronto).
6. **e74 re-sim (DI-07b): REAFIRMADO** — mantém telemetria; o julgamento é do autor no dossiê
   (é decisão de FIDELIDADE, não de infraestrutura — não se crava agora).
7. **D-2 (custo/dimensionamento R2) e D-3 (ZDT1 do c154): explicitamente NÃO são agora** — decisões
   de orçamento do M7, com os dados do piloto na mão.

### 📌 DEFS-c154 — histórico (levantadas pela sessão c154, 2026-07-18; RESOLVIDAS pela DI-11 acima)
Do `handoff/R2-c154_REPASSE-A-TORRE.md`: **D-1 NaN-guard do JES** (LB estoura logdet em bolsões
raros; guard só na SELEÇÃO, acqf crua intocada, logado — 24 disparos DTLZ2, 8/10 iters ZDT1; SEM
ele o ZDT1 é irrodável; **rec. torre: MANTER**, mesma classe das guardas ratificadas) · **D-2
custo** (DTLZ2 ≈18 dias·core/problema; ZDT1 ≈121 — dimensionamento da R2 pelo c154, alavancas
mapeadas) → M7 · **D-3 ZDT1**: completar ou documentar corte → M7 · **D-4 gaps v5.2.1** (backfill
tempo_busca_s do ④; colunas novas; mll_final; **n_baseline N/A no JES → decisão torre: logar
`n_train` e documentar no sigma_dict**) → escopo do retrofit-R2 · médias (escada RuntimeError,
likelihood default, init_batch_limit 256×32, projetor de wall) e baixas (doc-syncs) → lote.
**Ação já executada pela torre:** backup das baselines ①+manifesto+jsonl de TODOS os pilotos em
`data/experiments/_baseline_pre_retrofit/` (9,4 MB — a linha de base do gate de não-perturbação;
o ① do c154/DTLZ2 custou 14h37) + **artefato da SONDA gerado e verificado** (`scripts/gen_sonda.py`
+ `data/sonda/` — 25 problemas, determinismo 25/25, gabarito conferido; os retrofits só CARREGAM).

---

## PARTE A2 — O lote de 2026-07-19 (execução do retrofit DI-09/DI-10 no stack MATLAB)

### DI-12 — ✅ CRAVADAS EM LOTE (autor, 2026-07-19) — as 5 do cartão DI09-retrofit-R1
- **Contexto.** A sessão do cartão `DI09-retrofit-R1` (retrofit da sonda canônica + enriquecimento
  DI-10 nos 9 configs SA-MATLAB) fez o recon dos 9 configs + do writer compartilhado e levou ao
  autor as ambiguidades que **não eram resolvíveis com o CONTRATO_DE_DADOS + SPEC na mão**
  (protocolo D81). As cinco abaixo foram decididas pelo autor durante a sessão. As demais dúvidas
  do recon foram resolvidas pela sessão com o contrato (registradas no handoff §1, como vetáveis).

---

**DI-12.1 — "Patch aditivo" em arquivo stock NÃO é patch invasivo, exceto em hot-loop.**
- **Contexto.** O §6.1 manda: *"toda adição é read-only; grandezas inacessíveis sem patch invasivo
  no miolo stock NÃO entram"*. Três campos DI-10 caíram na fronteira: o valor é **calculado e usado**
  dentro de uma função stock, que simplesmente não o devolve. Expor exige acrescentar um valor de
  retorno — sem mudar nada do que a função faz.
  - b3 `apd_sel`: +1 output em `KrigingSelect.m` (arquivo **já patchado** pela L.2; variável já
    computada nos dois ramos).
  - e103 `margem_3sigma`: 1 linha de captura ao lado de `IBEAMS.m:67` (invalida o
    `repos.lock`/`e103_ibeams.sha256_tree` → exige re-lacre por `preflight.py --write`).
  - e7 `loss_treino`: 2º output em `trainNet.m` (valor já calculado na `:19`, RNG zero) — porém
    **dentro do laço de treino de 8e4 iterações**, no run mais caro da R1 (ZDT1, 72 min).
- **Opções.** (a) liberar os três; (b) liberar exceto no hot-loop; (c) proibir os três.
- **Decisão: (b).** Liberados `apd_sel` (b3) e `margem_3sigma` (e103); **barrado `loss_treino` (e7)**.
- **Justificativa.** Uma linha que só LÊ um valor já computado não altera o mecanismo — não é o que
  o §6.1 quer barrar (o alvo dele é reescrever o miolo). O critério que separa é **custo de
  execução**, não pureza: o e7 é o run mais caro da rodada e o campo está no laço quente.
- **Efeitos.** e7: `loss_treino` fica **NULL**, registrado como INACESSÍVEL no cartão do e7, com a
  razão. e103: o cartão inclui o re-lacre do `repos.lock` + reverificação das 3 âncoras.
- **Referências.** `handoff/DI09-retrofit-R1.md` §1; SPEC §S.7.1; CONTRATO §6.1.

---

**DI-12.2 — A sonda da ÚLTIMA geração sai de um carrier handle + bloco pós-`Solve`.**
- **Contexto.** O §17.2.2 exige *"SEMPRE a 1ª e a última"*. Mas o algoritmo **não sabe** que está na
  última geração: o orçamento acaba no MEIO do ciclo — o `FEBudget` lança `PlatEMO:Termination`
  (D21/D61) no ponto de avaliação, e a exceção salta para fora do laço. Todo bloco posicionado
  depois daquele ponto nunca executa. Em c141/b4 é pior: o lote de infill é variável (no c141 pode
  ser 0), então não há predicado a priori para "este é o último ciclo".
- **Opções.** (a) carrier handle + disparo pós-`Solve`; (b) aceitar "a última AMOSTRADA" (a curva
  perde o ponto final quando o último fit cai em geração fora da cadência); (c) k=1 nos configs
  problemáticos (dobra o volume e contraria o k=2).
- **Decisão: (a).**
- **Justificativa.** O modelo final é o **mais treinado** — é o ponto final da curva "o surrogate
  melhora com as épocas?" e o instante em que o DI-09 compara os algoritmos no fim do orçamento.
  Perdê-lo esvaziaria justamente a medida que motiva a sonda.
- **Implementação.** `SondaState` é um **handle** criado no `run_*` e injetado em `Problem.data`
  (⚠ `UserProblem.data` é `SetAccess = protected` — não há como injetar depois). O config chama
  `snd.probe(...)`, que **arma sempre** (guarda uma closure sobre o modelo recém-treinado, custo
  ~zero) e dispara só na cadência; o `run_*` chama `snd.finalProbe(buf.gen)` **depois** do
  `Algorithm.Solve`, fora do laço, e o método é no-op se aquela geração já foi sondada.
- **Efeitos.** Mecanismo ÚNICO para os 9 configs. Desfaz o veredito "INACESSÍVEL" que o recon dera
  para o stash pós-run (ele avaliara só a rota de gravar em `Problem.data` de dentro do algoritmo).
- **Referências.** `src/SondaState.m`; `handoff/DI09-retrofit-R1.md` §3.

---

**DI-12.3 — e74: a sonda mede as TRÊS RBFs, discriminadas por `modelo_flag`.**
- **Contexto.** O §3.2 fala de *"μ RBF"* no singular, mas o e74 (CLMEA) instancia **três** RBFs
  distintas no run, com conjuntos de treino distintos: *boot* (M redes mono-saída sobre o DoE,
  `CLMEA.m:63`), *s2* (rede M-saídas sobre o **arquivo inteiro**, `Hv_Select.m:9`) e *s3* (rede
  M-saídas **local**, sobre os vizinhos, `Local_infill.m:31`). "O WAPE do RBF do e74" seriam três
  números diferentes.
- **Opções.** (a) só a s2 (única M-saídas com `n_acumulado` monotônico, logo comparável no eixo FE)
  + par casado com o bloco PNN; (b) só a s2, cada bloco na sua geração natural; (c) as três.
- **Decisão: (c) — medir as três.**
- **Justificativa.** As três são modelos que o algoritmo **de fato usa para decidir**; escolher uma
  descartaria evidência sobre o mecanismo híbrido, que é o que torna o e74 interessante na tese.
- **Efeitos.** O e74 emite até **4 blocos por ciclo** (PNN + 3 RBFs) — cada um com sua
  `modelo_flag`, e a questão do "par casado PNN/RBF" se dissolve (não há par). ⚠ **Volume**: medir
  antes de rodar o ZDT1. ⚠ A s3 é treinada por ponto — o cartão do e74 deve fixar e documentar
  qual instância do ciclo é sondada (1 bloco/ciclo, não 1 por ponto).
- **Referências.** `handoff/DI09-retrofit-R1.md` §1; CONTRATO §3.2.

---

**DI-12.4 — `FEBudget.evaluate` ganha cronômetro: `tempo_aval_real_s` deixa de ser imensurável.**
- **Contexto.** O §17.6 tornou o bloco `timing` do manifesto OBRIGATÓRIO nos 21, com
  `tempo_aval_real_s` entre os quatro. Ele **não era medido em lugar nenhum** do stack MATLAB.
  Toda avaliação real passa por um portão único (`FEBudget.evaluate`) — é lá que se mede.
- **Opções.** (a) instrumentar o portão; (b) deixar NULL e documentar; (c) adiar para o M7.
- **Decisão: (a).**
- **Justificativa.** ~4 linhas, sem RNG, sem alterar decisão nenhuma; preenche os 11 configs de uma
  vez. Sem isso, o breakdown fit×busca×aval do §17.6 fica manco justo na parcela que a tese usa
  para separar custo-de-modelo de custo-de-função.
- **Implementação.** `tic/toc` acumulador em volta do `evalFcn` — **só a avaliação inédita**;
  cache-hit (D89) não avalia nada e não entra.
- **Efeitos.** Arquivo compartilhado pelos 11 configs + pisos ⇒ revalidar o que já passou (feito:
  gate de não-perturbação re-rodado).
- **Referências.** `src/FEBudget.m`; SPEC §17.6.

---

**DI-12.5 — 🔴 Cadência da sonda PADRONIZADA entre stacks: `g = 1, 2, 4, 6, …`.**
- **Contexto.** As duas sessões de retrofit implementaram a mesma frase do §17.2.2 (*"a cada k=2
  gerações + SEMPRE a 1ª e a última"*) de formas diferentes — divergência achada e escalada pela
  sessão retrofit-R2 (commit `652e24d`, D81):
  - MATLAB (`SondaState.due`): `g==1 || mod(g-1,k)==0` → 1, 3, 5, 7, …
  - Python (`sonda_due`): `it==1 or it%k==0` → 1, 2, 4, 6, …
- **Opções.** (a) alinhar o MATLAB ao Python; (b) alinhar o Python ao MATLAB; (c) escalar à torre e
  seguir sem alinhar.
- **Decisão: (a) — o MATLAB adota `g = 1, 2, 4, 6, …`.**
- **Justificativa.** Duas razões independentes. **Textual:** sob a leitura `1,3,5,…` a cláusula
  *"+SEMPRE a 1ª"* ficaria **vazia** (o 1 já pertence à progressão) — a SPEC ter se dado o trabalho
  de escrevê-la indica que a cadência sozinha não inclui a primeira. **Estrutural, decisiva:** a
  sonda é vendida como *"a régua ÚNICA, idêntica para todos os algoritmos, gerações e sementes"* —
  uma cadência que muda por STACK contradiz a própria definição. Alinhar para o lado que já tem
  runs gravados (c262/c154) custa menos, e o custo de padronizar só cresce a cada run novo.
- **Efeitos.** `SondaState.due` alterado (1 linha); c217 e c141 re-rodados e re-validados (7 runs,
  gate bit-a-bit verde). Contagem de blocos muda: c217/DTLZ2 116→117, c141/ZDT1 77→78.
  **Doc-sync pendente na torre:** cravar a fórmula no §17.2.2 e no CONTRATO §3.1 (hoje o texto
  admite as duas leituras — foi essa ambiguidade que produziu a divergência).
- **Referências.** commit `652e24d` (escalação da R2); `src/SondaState.m`;
  `handoff/DI09-retrofit-R1.md` §1.

---

### 📌 Correções e achados do lote (registrados junto)
1. **🔴 `n_acumulado` do c217 media o ARQUIVO, não o TREINO — corrigido, PENDENTE DE RATIFICAÇÃO.**
   O §17.6 define *"nº de pontos reais no **treino** naquele retreino"*; o `c217_instrument` gravava
   `numel(Arc)` (o arquivo) — outra grandeza, que achatava a curva de escalabilidade do c217.
   Corrigido para `size(TrainIn,1)` (o c217 treina numa subamostra 3/4 estratificada); o tamanho do
   arquivo segue auditável em `arc_size`. **Não toca a busca nem a ①** (gate verde), mas **muda a ④
   do c217 vs a baseline** ⇒ o autor deve ratificar.
2. **`tempo_geracao_s` DESCONTA a sonda** (alinha com a decisão D-1 do retrofit-R2, item B-0b da
   escalação `652e24d`). O relógio da geração mede o custo do ALGORITMO; incluir a sonda poria o
   preço do instrumento dentro da análise de custo (§9) e faria a MESMA coluna significar coisas
   diferentes em cada stack. **Doc-sync pendente:** explicitar no §17.6/CONTRATO §4, que hoje diz
   só "wall TOTAL da geração (fit+busca+aval+overhead)".
3. **`mkSurrogateRow` custava 148 µs/linha** (o `inputParser`) — ~87 s/run só no c217/ZDT1.
   Adicionado `RunBuffer.mkSurrogateRows` (lote): **38× mais rápido**, equivalência campo-a-campo
   provada (0 divergências em 2000 linhas × 15 campos). Mesma classe do fix DI-02 (writer O(n²)):
   o custo por linha é o que decide se a bateria M8 é viável.
4. **A sonda cobre o GRID, não os problemas de piloto.** `DTLZ2_d15` (variante dimensional, só de
   piloto) não tem artefato — e não pode ter sem um próprio, já que a sonda é Sobol com `d=D`.
   **Verificado: o grid oficial (`runs_matrix.csv`) tem 25 problemas e os 25 têm sonda** ⇒ a bateria
   não é afetada. `load_sonda` tolera a ausência e o manifesto grava
   `man.sonda.status='artefato_ausente'`, para que *"sem sonda"* nunca seja lido como *"sonda vazia"*.
5. **`scripts/accept.py` não tem NENHUMA checagem de sonda** (0 hits) — nem a invariante de ordem
   que o §3.1 promete estar *"documentada no accept"*. Faixa `.py` ⇒ repassado à torre/R3-00.

## PARTE A3 — DI-13: o lote de 2026-07-19 (as 21 decisões pós-retrofits triplos)

> **Contexto do lote.** As três sessões paralelas (`DI09-retrofit-R2` BoTorch, `DI09-retrofit-R1`
> MATLAB, `R3-00-harness`) levantaram 31 itens em aberto, muitos duplicados entre elas. A torre
> consolidou em 9 decisões substantivas + 12 ratificações, explicou cada uma didaticamente ao autor,
> e **o autor decidiu todas em 2026-07-19**. Implementação: a torre, na mesma janela (sem sessão
> ativa). Evidência: bateria completa verde (21 gates + 199 testes) após cada mudança.

### DI-13.1 — O despachante MESCLA o manifesto (nunca reconstrói) ✅ (a)
- **Problema.** `experiments.py::_run_one` chamava `new_manifest`+`write_manifest`
  INCONDICIONALMENTE após o runner, sobrescrevendo a certidão RICA que o runner acabara de gravar:
  sumiam `doe_hash`, `fe_final`, `n_geracoes`, `sigma_dict`, bloco `sonda`, `fit_series` e o timing
  MEDIDO (virava stub com 3 de 4 chaves `None`). Os pilotos escaparam por chamarem o runner direto;
  **a bateria M8 passa pelo despachante ⇒ os 16.500 runs perderiam o payload DI-09/DI-10 da camada
  ⑤, sem sintoma visível.** Levantado por 2 sessões independentes (R2 §B-1, R3 §D8).
- **Opções.** (a) mesclar; (b) manifesto separado do despachante; (c) runner escreve por último.
- **Decisão: (a) MESCLAR** — lê o manifesto do runner e injeta só o que é do despachante
  (`status`, `n_retries`, `stack_trace`, `tempo_total_despachante_s`); **nunca sobrescreve medida
  por estimativa**; se o runner não gravou (run morreu antes), cria do zero como antes.
- **Implementado.** `experiments.py` (+`read_manifest` no import). Regressão:
  `tests/test_di13.py::TestDI13_1_MesclaManifesto` (2 testes: preserva payload · cria do zero).

### DI-13.2 — `tempo_fit_s` aceita NULL (os pisos não treinam) ✅ (a)
- **Problema.** O CONTRATO §4 manda os pisos gravarem a ④ com `tempo_fit_s = NULL` ("não se
  aplica"), mas o schema declarava `nullable=False` e o writer fazia `float(None)` ⇒ estouro. Os 4
  pisos online + o piso offline **não conseguiam cumprir o contrato**; travava o cartão piso-off.
- **Opções.** (a) `nullable=True` + guarda; (b) gravar `0.0`; (c) pisos sem ④.
- **Decisão: (a)** — e o autor explicitou: *"aceita nulos para o tempo de treinamento, mas guarda o
  tempo de execução do algoritmo normalmente"*. `0.0` MENTIRIA ("treinou e custou zero") e poluiria
  qualquer média de custo; sem a ④ perderíamos o `tempo_geracao_s` dos pisos, que é o **custo-baseline**.
- **Implementado.** `src/export.py` (schema `nullable=True` + writer usa `opt()`). Regressão:
  `test_di13.py::TestDI13_2_PisoTimingNull`. **A SENTINELA que a sessão R3 plantou disparou como
  projetado** e foi convertida em teste de comportamento correto (`test_r3_harness.py`).

### DI-13.3 — Aborto por teto: manifesto `failed` + `is_run_done` mais estrito ✅ (c) → M7
- **Problema.** Run abortado pelo teto de tempo não grava certidão de falha; com artefatos de uma
  execução ANTERIOR no disco, o `is_run_done` (D58) lê o run como PRONTO ⇒ um run truncado entraria
  na bateria como completo.
- **Decisão: (c) as duas** — o aborto grava `status='failed'` (corrige a raiz, é o que a D23 manda)
  **e** o `is_run_done` passa a exigir `fe_final == maxfe` (rede independente).
- **Execução: cartão de hardening do M7**, junto com o retry (mexe na semântica de resume — merece
  o cartão dedicado, não uma janela de torre).

### DI-13.4 — e103 `margem_3sigma` = a estatística honesta ✅ (b)
- **Problema.** O DI-10 pediu "o valor que decide o KFlag", mas o mecanismo **não tem um valor**: é
  booleano sobre pares (`sum(site,3) >= M-1`).
- **Decisão: (b)** logar `margem_3sigma_stats` = `n_pares_ok`/`n_pares_total` + o `KFlag`.
  Inventar um escalar seria criar grandeza inexistente (proibido por D81); a estatística responde a
  pergunta real ("a decisão foi apertada ou folgada?").
- **Execução:** cartão de continuação do retrofit MATLAB (e103).

### DI-13.5 — 🔬 Sonda OFFLINE: `geracao=NULL` e **S=20.000** (artefato ANINHADO) ✅
- **Decisão do autor (com upgrade sobre a recomendação da torre):** (i) `geracao = NULL` nos blocos
  de sonda do regime offline (o modelo treina 1×, ANTES do laço — não há geração a que pertencer;
  NULL é mais honesto que o `0` que a torre propôs); (ii) **o offline usa 20.000 pontos**, não
  2.000 — *"como não vai ficar fazendo Sobol geração após geração, quero mais pontos no Sobol único
  que vai fazer a análise"*.
- **Como foi implementado (a propriedade que torna isto elegante).** A torre verificou
  empiricamente que **a sequência de Sobol é ANINHADA**: os 2.000 primeiros pontos de uma sequência
  de 20.000 são **BIT-IDÊNTICOS** aos 2.000 de uma sequência de 2.000 (|dif| = 0 em D=2/12/30).
  Logo: **UM único artefato de 20.000 por problema** serve aos dois regimes —
  **ONLINE lê `[0:2000]`** (a cada k=2 gerações) e **OFFLINE lê as 20.000** (1× por modelo).
  Consequências provadas: (1) a régua é a MESMA nos dois regimes na faixa compartilhada — a
  comparação online↔offline continua exata; (2) **os runs online já retrofitados (c217, c141,
  c262, c154) NÃO precisam ser refeitos** — `x_hash_online` == o `x_hash` antigo em **25/25**
  problemas (verificado).
- **Implementado.** `scripts/gen_sonda.py` (S=20000, `S_online`=2000, sidecar v2 com
  `x_hash_online`/`f_hash_online`) + artefato regerado (88 MB, determinismo 25/25) + fatiamento por
  `regime` nos **três** loaders (`botorch_harness`, `standalone_harness`, `experiment.m`) + o gate
  R3-00 passou a checar contra o S DO REGIME (não contra o literal 2000).
- **Bônus (bug latente corrigido).** A chave do cache de sonda não incluía o `data_root` — um load
  de outra pasta devolvia o artefato cacheado, **mascarando adulteração**. Agora a chave é
  `(problema, regime, data_root)` + helper público `clear_sonda_cache()` (testes não cutucam o dict
  interno). Regressão: `test_di13.py::TestDI13_5_SondaAninhada` (inclui a prova do aninhamento).
- **⚠ Nota estatística registrada:** Sobol tem balanceamento ótimo em potências de 2. 2.000/20.000
  não são (2.048/16.384 seriam). A perda de uniformidade é pequena e o autor cravou os valores;
  fica o registro (mudar exigiria regerar + refazer os 4 configs online já retrofitados).

### DI-13.6 — e74: a sonda mede a RBF do ponto ESCOLHIDO ✅ (b)
- **Problema.** O e74 tem 3 cabeças, e a terceira (`Local_infill`) é treinada **por ponto** — num
  ciclo há ~20 instâncias. "Medir as três" (DI-12.3) não definia QUAL.
- **Decisão: (b)** a s3 **do ponto que virou infill** — é a instância que **importou** (guiou a
  decisão real), rende 1 bloco/ciclo, e tem leitura defensável na dissertação: *"o modelo local que
  guiou a escolha"*. Documentar no `sigma_dict`.
- **Execução:** cartão de continuação (e74).

### DI-13.7 — pisos: estreitar o assert `piso_com_surrogate` ✅ (a)
- **Problema.** A trava "piso não produz surrogate" foi escrita conferindo TAMBÉM as linhas de
  timing — e o contrato agora EXIGE ④ dos pisos. A trava impedia o próprio contrato.
- **Decisão: (a)** estreitar para a camada ③ (a intenção original), liberando a ④.
- **Execução:** cartão de continuação (pacote dos pisos).

### DI-13.8 — camada ⑦: ratificadas `origem_linha` e `nd_pos_real` ✅ (a)
- `origem_linha` = link POSICIONAL à ③ (a regra 1 do R4 proíbe casar por X float32);
  **`nd_pos_real`** = se o ponto continua não-dominado APÓS a avaliação real — a medida DIRETA do
  **"erro de fantasia"** (quanto do "front" do modelo realmente é front). Custo: 1 int + 1 booleano.

### DI-13.9 — camada ⑦: avaliar TODOS os finais e filtrar DEPOIS ✅ (a)
- **Decisão: (a)** — filtrar pelo ND-do-modelo ANTES seria **filtrar a realidade pela fantasia**,
  destruindo justamente o que a camada mede; o custo extra é nulo (funções analíticas).
  Leitura da SPEC B7.5 confirmada. **Ação da torre: ajustar a redação do CONTRATO §7** (que dizia
  "o ND final") — feito nesta janela.

### DI-13.10 a DI-13.21 — as 12 ratificações em bloco ✅
`tempo_geracao_s` EXCLUI o custo da sonda (instrumentação não contamina a medida do mecanismo; os 2
stacks alinhados) · renome `acqf_todos_restarts` (nome normativo) · `tempo_pred_sonda_s`=NULL em run
pré-sonda ("não medido" ≠ "custou zero") · backfill = dado derivado E rotulado · `n_acumulado` do
c217 corrigido (`numel(Arc)`→`size(TrainIn,1)`, conformidade §17.6) · **`fe_treino_max` NÃO é
monotônico em b1/b4/c217** (subamostram o treino) → **vira regra 9 do R4** · dtype de
`real_solution_id` e contiguidade do bloco · endurecer o check de RNG do R2-00 (M7) · checagens de
sonda no `accept.py` (continuação) · `load_sonda` duplicado MATLAB/Python (aceito — linguagens
diferentes) · caveat float32 do e103 na ⑦ · doc-syncs pendentes (feitos nesta janela).

### 📌 Estado de execução da DI-13 (o que a torre fez nesta janela)
| Decisão | Onde | Status |
|---|---|---|
| 13.1 mescla | `experiments.py` | ✅ implementada + 2 regressões |
| 13.2 NULL do piso | `src/export.py` | ✅ implementada + regressão (sentinela do R3 convertida) |
| 13.5 sonda 20k | `scripts/gen_sonda.py`, `data/sonda/` (regerado), 3 loaders, `accept.py` | ✅ implementada + 2 regressões + prova de compatibilidade 25/25 |
| 13.8/13.9 ⑦ | redação do `CONTRATO_DE_DADOS.md` §7 + SPEC | ✅ doc-sync |
| 13.3 aborto | cartão de hardening **M7** | 📅 agendada |
| 13.4/13.6/13.7 | cartão de **continuação do retrofit MATLAB** (e103/e74/pisos) | 📅 no prompt |
| 13.10–13.21 | ratificadas; execução distribuída (M7 / continuação / feitas) | ✅/📅 |

### DI-14 — Sincronização `runs_matrix.csv` ↔ `envs.json` (achado da torre, 2026-07-19)
- **Contexto.** Ao montar o prompt do R3-c122, a torre bateu os artefatos e achou **9 configs com
  nomes de ambiente OBSOLETOS** no `runs_matrix.csv` — resquícios do desenho anterior ao S.8
  (`env_botorch`, `env_c122_thetadea`, `env_c149_lbnmobo`, `env_desdeo`), enquanto o `envs.json` já
  trazia os atuais (`env_main`, `env_b5`, `env_c311`). Ex.: o c122 precisava de env próprio por causa
  do `pymop`/`optproblems`/`autograd`; o **bypass do factory** (S.8) removeu essas deps e o env
  **encolheu para `env_main`** — o `runs_matrix` não acompanhou.
- **Gravidade real (verificada).** **Nenhum risco de runtime:** o código consome
  `envs.json:alg_to_env` (`standalone_harness.py:213`), NÃO a coluna do `runs_matrix`. O dano seria
  de **leitura humana/sessão** — um implementador do c122 provisionaria um venv inexistente.
- **Decisão/ação (torre):** `runs_matrix.csv` sincronizado com o `envs.json` (a fonte que o código
  consome): **8.700 linhas** de 19.950 atualizadas em 9 configs — b5r/b5m/moead_media→`env_b5`,
  c311→`env_c311`, c122/c149/c154/c262/sobol_batch→`env_main`. Divergências restantes: **0**;
  contagem de linhas preservada (19.950); preflight e suíte verdes.
- **Regra que fica:** em divergência de ambiente, **`envs.json` é a fonte** (é o que o D79/N.2
  consome em runtime); o `runs_matrix` é derivado e deve ser sincronizado.

## PARTE A4 — DI-15: sincronização do M5/R3 com a arquitetura (auditoria de 2026-07-19)

> **O que foi.** O autor pediu auditoria exaustiva dos 7 cartões do M5/R3 contra a arquitetura atual
> (DI-01..DI-14, CONTRATO_DE_DADOS v1.1, SPEC v5.2.1, harness real). A torre rodou **6 auditores
> paralelos + 82 verificações adversariais individuais** (88 agentes, ~1.000 tool-calls):
> **95 achados brutos → 82 críticos → 43 CONFIRMADOS** (48% de falso-positivo — a fase cética
> impediu 39 correções indevidas). O autor delegou: *"pode usar sua sugestão em todas as decisões"*.

### DI-15.0 — 🔴 A CAUSA RAIZ (estrutural, afeta TODAS as rodadas)
- **Problema.** Nenhum dos 3 contratos de rodada (R1/R2/R3) puxa o §17 (contrato de export) nem o
  S.7/S.7.1 — esse conteúdo vive só em `00_fundacao/03_contrato_export.md`, que a "regra de ouro do
  contexto" mandava ler **"uma vez, na Fase 0"**. Consequência: **uma sessão NOVA de qualquer rodada
  podia implementar um algoritmo sem NUNCA ver** a SONDA (§17.2.2), a camada ⑦ (DI-08), o jsonl
  enriquecido (S.7.1/DI-10) ou o timing v5.2.1 (§17.6). Os bundles do R3 confirmaram: **zero menções**.
  *(Isto explica retroativamente por que a torre vinha mandando "leia o CONTRATO_DE_DADOS" em todos os
  prompts — compensação manual de um buraco estrutural.)*
- **Correção.** (1) `claude_code_context/CLAUDE.md` §0: o **`CONTRATO_DE_DADOS.md` virou leitura
  OBRIGATÓRIA EM TODA SESSÃO** (item 2 de 5), com o porquê documentado; (2) os **3 contratos de
  rodada** ganharam um cabeçalho "📋 LEITURA OBRIGATÓRIA ANTES DE CODAR" resumindo sonda/⑦/timing/
  jsonl e mandando ler o contrato de dados (via `gen_bundles.py`, para não se perder na regeneração).

### DI-15.1 — 🔴 `geracao` NULL era INGRAVÁVEL (a decisão contradizia o schema)
- **Problema (achado A3).** A DI-13.5 fixou `geracao = NULL` nos blocos de sonda OFFLINE, mas
  `surrogate_schema` declarava `geracao` como `nullable=False` e `surrogate_row`/`write_surrogate`
  faziam `int(geracao)` ⇒ **o contrato que a própria decisão criou era impossível de cumprir**.
- **Correção (código, faixa da torre).** `src/export.py`: ③ `geracao` → `nullable=True`;
  `surrogate_row(geracao: int | None)`; o writer da ③ emite NULL quando None (o writer da ④
  permanece obrigatório — timing é sempre por geração). Provado: grava `[None, 3]` na mesma tabela.

### DI-15.2 — 🔴 A camada ⑦ com a redação REVOGADA na SPEC (a precedência apontava para o texto errado)
- **Problema (R3C-02/B2/C311-03).** A DI-13.9 ("TODOS os finais avaliados; ND filtrado DEPOIS") foi
  aplicada só no `CONTRATO_DE_DADOS.md`; a **SPEC ficou com a redação antiga** em §11, na tabela do
  Anexo D e na seção de métricas — e como a precedência declarada é **SPEC > CONTRATO**, o texto
  revogado é que valeria. Um implementador de b5/c311 produziria uma ⑦ pré-filtrada pela fantasia do
  modelo, destruindo o `nd_pos_real`. *(Mitigado por 3 camadas — o header novo, o CONTRATO, e o gate
  mecânico de `final_eval.py` que recomputa o filtro — mas a prosa tinha de ser consertada.)*
- **Correção.** SPEC §11 + tabela D + §métricas reescritas para a redação DI-13.9 (com as colunas
  DI-13.8 e o invariante "⑦ RECONSTITUÍVEL da ③"); `export 2 camadas` → `6–7 camadas (§17.7)` (3×).

### DI-15.3 — 🔴 O contrato R3 descrevia um harness HIPOTÉTICO (e contradizia a D90)
- **Problema (R3C-04/E1).** O E.9 mandava *"gerar dataset LHS 31D−1 no env da ponte"* — o que
  **contradiz a D90** (o dataset é ARTEFATO carregado, nunca gerado) e ignora que o
  `src/standalone_harness.py` já entrega tudo pronto.
- **Correção.** SPEC/E.9: "CARREGAR do artefato (D90)" + a lista das APIs REAIS a reusar
  (`run_in_venv`, `load_dataset`, `load_offline_budget`, `offline_guard`, `load_sonda(regime=…)`,
  `emit_sonda_block`, `minimo_comum_di10`, `SnapshotBuffer`, `write_run_outputs`, `write_final`,
  `preserve_all_rng`, `iteration_cleanup`) + "NÃO reimplemente nada disso".

### DI-15.4 — Correções editoriais em lote (aplicadas na SPEC + regeneração)
`F1/R3C-11` pin do sklearn do b5 (0.23.2 → **0.21.3**, com lápide; o conflito era interno ao cartão) ·
`C311-09` o **c311 NÃO é de treino único** (constrói a árvore incrementalmente ⇒ `fit_series` com
várias linhas — a afirmação contrária no §17.6 era falsa) · `H2/H-01/R3C-09` **INDEX: R3-00-harness
⬜→✅** · `G1/C311-04` **`envs.json`**: os envs `env_b5`/`env_c311` deixam de dizer "VM = destino
natural" e passam a carregar a **nota DI-11.5** (o cartão decide como TAREFA 0: pins vizinhos no Mac
com validação de equivalência, ou exceção documentada na VM).

### DI-15.5 — 🟡 PENDÊNCIAS ESCALADAS AO AUTOR (D81 — a torre NÃO decidiu sozinha)
São **definições ausentes**, não erros de redação — exigem escolha de escopo/mecanismo:
| # | Questão | Por que é do autor |
|---|---|---|
| P1 | **O piso OFFLINE emite sonda?** (`A2`/`R3C-06`) Ele treina um GP (§10) ⇒ TEM modelo, mas o contrato diz "pisos não têm sonda" | muda escopo de coleta e a contagem de configs com surrogate (17 → 18?) |
| P2 | **Semântica da sonda do c122** (`C122-02`): qual é a "referência corrente" contra a qual o score `e(z)` é computado? (3 leituras possíveis) | é definição de MECANISMO — D81 proíbe inventar |
| P3 | **Granularidade da ③-BUSCA dos par-a-par** (`C122-03`): o pool do c122 é N\*=7000/iteração — grava-se o pool inteiro? (idem c217) | decide volume da bateria (pode ser TB) |
| P4 | **N interno do piso offline × b5** (`I1`/DEF-E3): 100 × 50/105 quebra a "ablação exata" | é a validade da comparação piso×b5 |
| P5 | **Rota do piso no tier big** (`C311-06`): usa treed-GP do c311? colide com "b5×c311 nunca co-importar" | decisão de desenho + risco de venv |
| P6 | **`n_baseline` no e81** (`E81-04`): conceito do qNEHVI que não existe no qPOTS | análogo à DI-11 §2 (c154 → `n_train`), mas precisa do aval |

## PARTE A5 — DI-16: as 6 definições que a auditoria M5 escalou (autor, 2026-07-19)

> As pendências P1–P6 da DI-15.5 (definições AUSENTES, não erros de redação — D81 proíbe a torre
> escolher sozinha). O autor aprovou as 6 recomendações em bloco. Cravadas na SPEC + CONTRATO +
> bundles regenerados nesta janela.

### DI-16.1 — O piso OFFLINE **EMITE SONDA** (a regra "pisos não têm modelo" era falsa p/ ele)
- **Contexto.** A regra dizia «pisos (4+1) — NÃO TÊM SONDA (sem modelo)». Vale para os 4 pisos
  ONLINE (MOEAs puros). É **FALSA** para o 5º: o piso offline **treina um GP (Kriging)** e otimiza
  sobre a **média** — ele É, por desenho, "o b5 sem σ" (DEF-E3): mesmo motor (MOEA/D mode 12 do
  DESDEO), mesmo surrogate, mesmo orçamento (40k aval-surrogate).
- **Decisão: (a) o piso-off emite sonda** como qualquer config com modelo — `mu_*` preenchido,
  `sigma_*` NULL — e grava `tempo_fit_s` REAL + `modelo_hp`.
- **Justificativa.** A comparação de sonda **piso-off × b5r/b5m é a medição mais direta que o estudo
  tem do VALOR do σ**: mesmo GP, mesmo μ, mesmos 20.000 pontos ⇒ a diferença é atribuível só à
  incerteza. Excluí-la por uma frase escrita pensando nos pisos online perderia o contraste central.
- **⚠ Efeito colateral: AJUSTA a DI-13.7.** O assert passa a ser «os **4 pisos ONLINE** não produzem
  ③» (não "os pisos"). A contagem de configs COM surrogate vai de 17 → **18**.

### DI-16.2 — A referência da sonda do c122 = **a população selecionada (N=11/15)**
- **Contexto.** O modelo do c122 não responde nada absoluto sobre 1 ponto: as 2 FNNs consomem PARES
  `[x_i,x_j]` e devolvem softmax-3; `e(z)` só existe RELATIVO a um conjunto. "Referência corrente"
  nunca foi definida para ele (para o c217 sim: Pmid).
- **Decisão: (a) a POPULAÇÃO SELECIONADA corrente** (N=11 em M=2 / 15 em M=3), com `n_ref` no jsonl.
- **Justificativa.** É a única candidata que é **(i) de tamanho FIXO** — parâmetro do próprio
  algoritmo ⇒ `e(z)` comparável entre gerações, sementes e configs (o arquivo inteiro cresceria de
  11D−1 a 31D−1 e o score subiria SÓ pela escala, **falsificando a curva "o surrogate melhora com as
  épocas?"**, que é o propósito da sonda). ⟦**Perna (ii) CORRIGIDA — DI-21/D-19det, achado da
  sessão R3-c122**: a justificativa antiga ("é o contexto real em que o modelo decide") era
  factualmente errada — a população selecionada NUNCA é referência de dominância no código (a
  decisão real é rep-do-cluster → intra ≤300). **A decisão (a) FICA** — a perna (i) (tamanho fixo ⇒
  comparabilidade) sustenta sozinha —, mas a sonda do c122 é **instrumento com referência PRÓPRIA**,
  não o score interno da busca. Já declarado no `sigma_dict` dos manifestos.⟧

### DI-16.3 — ③-BUSCA do c122 = **TOP-100 do pool + agregados** (não o pool de 7.000)
- **Contexto.** A DEF-C2 classificava o c122 como "EA ⇒ grave a população selecionada" — mas a
  seleção de sobrevivência dele usa fitness **REAL**, então a população selecionada NÃO é predição
  de modelo (a ③ sairia vazia de conteúdo). O modelo prevê sobre o **pool de N\*=7.000/iteração**,
  do qual só **1** vira FE. A própria volumetria da SPEC (~1M linhas) só fechava com a leitura POOL.
- **Decisão ⟦REESCRITA — DI-21/D-19det; a (c) original era INEXEQUÍVEL (4 lentes adversariais
  4/4: `e(z)` é grandeza INTRA-conjunto, só existe na categoria vencedora ≤Q_max=300,
  `selection.py:158-168`; sobre os 7.000 o código computa `scf` INTER vs o representante; `e(z)`
  real sobre 7.000 = 49M pares/iteração, ~8-10 GB/rede) → o autor cravou a **A+** na sessão⟧:**
  ③ = **TOP-100 por `e(z)` DA CATEGORIA vencedora** (`real_solution_id` só no escolhido); jsonl =
  o que o algoritmo DE FATO computa sobre os 7.000 (`n_q1/n_q2/n_q3`, `n_acordo`/`n_desacordo`,
  `pool_scf_{min,med,max}`) + `ez_cat_{min,med,max}`. Custo e perturbação zero.
  **~2 GB** em vez de **~120 GB**.
- **Justificativa (quase sem perda analítica).** O ranking dos 6.900 restantes é **inauditável por
  construção** — nenhum deles ganha `f` real, então não há verdade contra a qual medir. As análises
  que EXISTEM (a escolha foi boa? o modelo discrimina? contrafactual greedy-μ) acontecem na CABEÇA
  do ranking + nos agregados. *(Escopo: c122. O c217, apesar de par-a-par, não tem pool — a ③ dele é
  ~1 linha/iteração, verificado nos dados.)*

### DI-16.4 — N do piso offline = **o lattice do b5m (50/105)**, não 100
- **Contexto.** O piso declarava N=100 (resíduo do default PlatEMO dos pisos ONLINE) enquanto o b5m
  usa o lattice Das-Dennis (50 em M=2 / 105 em M=3). No MOEA/D o **N É o nº de vetores de
  decomposição** — define a estrutura da busca inteira.
- **Decisão: (a) o piso usa o MESMO lattice do b5m.**
- **Justificativa.** Com N diferente, o contraste piso×b5m mediria **duas** variáveis (uso de σ **e**
  estrutura da busca) — exatamente o que a "ablação exata" da DEF-E3 existe para evitar; e com 40k
  avaliações fixas o N ainda muda o nº de gerações (400×800), alterando ③ e ④.

### DI-16.5 — Rota do piso no tier big: **DUAS instâncias, cada uma no env do seu par**
- **Contexto (a rota antiga era FISICAMENTE IMPOSSÍVEL).** O piso-big precisaria da classe `treeGP`
  (vendor do **c311**, só em `env_c311`) e do motor MOEA/D mode 12 (vendor do **b5**), mas
  **b5×c311 NUNCA podem ser co-importados** (N.1.2/D79 — mesmo nome de pacote, código diferente ⇒
  usa as classes ERRADAS *sem erro*). E o `envs.json` roteia o piso para `env_b5`.
- **Decisão: (a)** o piso offline vira **duas instâncias**: **small/medium → `env_b5`** (mode 12 +
  Kriging-média = a ablação do **b5**, que só roda nesses tiers) · **big → `env_c311`**
  (treed-GP-média + o MOEA/D de lá = a ablação do **c311**, o único que roda no big).
- **Justificativa.** Cada tier tem um PAR diferente — o piso é a ablação de quem está no tier. Um env
  por processo ⇒ zero risco de colisão. O roster do sweep (§11.5) passa a listar o piso nos 3 tiers.

### DI-16.7 / DI-16.8 / R3C-05 — o pacote que LIBERA o cartão R3-c122 (torre, 2026-07-19)
- **DI-16.7 (C122-08):** preâmbulo transversal novo na §22.4 — «**a infra JÁ EXISTE**»: lista as APIs
  do `standalone_harness.py` que os 7 cartões da R3 herdam (pin/env_info, run_in_venv, load_doe+
  FEBudget, load_dataset+offline_guard, seeds D62, preserve_all_rng, iteration_cleanup, load_sonda/
  sonda_due/emit_sonda_block, minimo_comum_di10, SnapshotBuffer, write_run_outputs/dual_write_run,
  write_final) + o esqueleto copiável `run_stubr3` + «gancho faltando ⇒ pára-e-pergunta (D81)».
- **DI-16.8 (C122-10):** o carimbo `bucket-only` (D54) passa a declarar a FASE: **vale do M8 em
  diante**; **no Mac, até o M7, `enable_bucket=False` com as camadas LOCAIS COMPLETAS, sem podar a ③**
  (RI-08). Sem isso o implementador tentaria credenciar GCS numa sessão em que isso não se aplica —
  ou pior, podaria a ③ do piloto. Aplicado nas epígrafes da R2 E da R3.
- **R3C-05:** os ponteiros de env MORTOS («env §18.6», «env §18.7») viraram os nomes canônicos
  **`env_b5`/`env_c311`**, apontando o `envs.json:alg_to_env` como FONTE ÚNICA em runtime (DI-14),
  com o pin correto do sklearn (0.21.3) e a **TAREFA 0 de Mac×VM** (DI-11.5/RI-08) explícita.

### DI-16.9 a DI-16.20 — os 17 achados dos cartões POSTERIORES (torre, 2026-07-19)
Aplicados em lote enquanto c122 e o retrofit MATLAB rodavam (faixa da torre: SPEC + artefatos;
zero interseção com `.py` do c122 ou `.m` do MATLAB). **Todos verificados nos bundles regenerados.**

**c149 (7 — era o cartão MAIS dessincronizado):**
- **DI-16.9 (A-02)** a sonda devolve `(μ,σ)` **DES-PADRONIZADOS por objetivo** (o c149 faz z-score de
  Y): `μ_nat=μ_z·std+mean`, `σ_nat=√max(σ²_z,0)·std`, com os params do refit CORRENTE; `sigma_*`
  carrega **σ, nunca σ²**.
- **DI-16.10 (E-02)** a premissa «`minimize(seed=k)` re-semeia os globais» é **FALSA no pymoo 0.6.2**
  do env_main (MEDIDO pelo R3-00) — vale só em ≤0.6.1.3 (o fallback do Colab). Usar
  `preserve_all_rng` de qualquer forma.
- **DI-16.11 (F-01)** ENV = **`env_main` no Mac** (não os pins do Colab, que são o fallback D78);
  Tarefa 0: confirmar `torch` no venv.
- **(I-03)** as sementes: os nomes `g()`/`h()` das receitas L **não existem em código** → usar
  `iteration_seed(...)` do harness (D62/D91).
- **(I-04)** DoE: **NÃO gerar** — `load_doe` do artefato (D87/D88); gerar o próprio estava MORTO.
- **(B-02)** o adapter faz **só a desnormalização** e DELEGA a `bud.evaluate` — o FEBudget é a fonte
  ÚNICA do orçamento (D89); "contagem + dedup no adapter" duplicaria a contabilidade.
- **DI-16.15 (E-01)** o cartão passa a listar as APIs do harness REAL a reusar (com destaque para o
  `iteration_cleanup`/D86, crítico no ensemble de K=10 redes).

**c311 (5):**
- **DI-16.12 (C311-02) 🔴 a premissa "offline = modelo fixo" é FALSA para ele** — o TGPR-MO constrói
  a árvore DENTRO de um laço (1 GP de folha por iteração, até 2.500 no big). Regra cravada:
  **exatamente 2 blocos de sonda** — fim da construção (`treedGP_build`) e fim do run
  (`treedGP_final`), ambos com `geracao`=NULL.
- **DI-16.13 (C311-12)** a sonda de 20.000 exige um **`predict_batch(X)` NOVO** (o `predict` canônico
  é loop 1-ponto-por-linha ⇒ 40–60k chamadas GPy por bloco); **NÃO** copiar o `predict_new` (é de
  outra classe).
- **DI-16.14 (C311-14)** o cartão se contradizia (mandava trocar NDS pygmo→pymoo e 5 linhas acima
  dizia que o pygmo nunca é importado): **o pygmo está AUSENTE do caminho `framework/` — nenhum swap
  é necessário**.
- **DI-16.19 (C311-11)** **contador de `geracao` ÚNICO e monotônico** atravessando as 2 fases (as ③
  das fases colidiam em 1..50); fase discriminada em `modelo_flag`.
- **(C311-15)** volumetria da ③ atualizada pós-D54+sonda (c311 ~80–135 k, não ~20 k; idem b5/e103).

**b5 / piso-off (4):**
- **DI-16.16 (B3) 🔴** o mini-patch do mode 7 é **REQUISITO DE GATE**, não instrumentação: sem ele o
  archive é a PROLE pré-seleção ⇒ **a ⑦ nasce IRRECONSTITUÍVEL da ③ com erro SILENCIOSO**. O aceite
  do b5r passa a incluir `final_eval --check` VERDE.
- **(D1)** o `tempo_fit_s`=NULL vale só p/ os **4 pisos ONLINE**; o piso OFFLINE **treina e grava
  tempo medido** (coerente com a DI-16.1).
- **DI-16.17 (J1)** no b5/piso a **② sai VAZIA por construção** (pop inicial = LHS novo ≠ dataset) e o
  `real_solution_id` é NULL na busca — ESPERADO, declarado no `sigma_dict`; o gate NÃO deve exigir ②
  não-vazia nesses configs.
- **DI-16.20 (H1)** âncora `b5-mode72-kde`: off-by-one reconciliado (65→**66**) + literais marcados
  para CONCRETIZAÇÃO na sessão (precedente b3/c238), já que o repo do b5 não está montado.

**e81 (1):** **DI-16.18 (E81-09)** contradições internas resolvidas por lápide — vale o corpo:
**`train_Yvar=1e-12`** (não 1e-6), **ngen=10 (D46)** (não "a fixar"), e **env PRÓPRIO
`env_e81_qpots` com botorch 0.16.1** (não "testar sobre o 0.18 primeiro").

### 📌 Estado da aplicação dos 43 achados (transparência)
**43 de 43 APLICADOS ✅** (26 no primeiro lote + os 17 dos cartões posteriores, DI-16.9..16.20).
Todos verificados nos bundles regenerados; preflight e suíte verdes. **Os 7 cartões do M5/R3 estão
sincronizados com a arquitetura atual** — nenhum abre com pendência de documentação.

### DI-16.6 — `n_baseline` → **`n_train`** no e81
- O `n_baseline` é o \|X_baseline\| **pós-prune** do qLogNEHVI. O qPOTS **não tem baseline nem
  prune** (o maximin é vs o dataset INTEIRO). **Decisão: logar `n_train`** — mesma solução já
  aplicada ao c154 (DI-11 §2), consistente.

## PARTE A6 — DI-17: hardening do M7 adiantado (torre, 2026-07-19)

> Executado enquanto o retrofit MATLAB e o R3-c122 rodavam — **em arquivos que nenhuma das duas
> sessões toca** (`experiments.py`, `src/manifest.py`, `src/export.py`, `tests/`). Verificado:
> suíte verde, gates F0/R3-00 verdes, preflight verde.

### DI-17.1 — Retry com BACKOFF + erros não-retriáveis [incremento 1 do autor / DI-06 item 1]
- **Antes:** `attempts = 2` (o 1 retry do D23), sem espera entre tentativas.
- **Agora:** `RETRY_ATTEMPTS = 3` com **backoff exponencial** (`RETRY_BACKOFF_S · 2^i` = 0s → 5s →
  20s). A espera é o que separa falha TRANSITÓRIA (licença MATLAB contendida, I/O, OOM momentâneo,
  rede no upload — certas em 16.500 runs) de falha REAL.
- **+ classe NÃO-RETRIÁVEL nova:** `FileNotFoundError`/`KeyError` (DoE/dataset/sonda/chave de env
  ausente) cortam na hora com `guard('nao_retriavel')` — retriar erro de PREPARAÇÃO só queima tempo.
  O `NotImplementedError` já cortava.
- Cada retry emite evento `retry` no jsonl (tentativa/de/espera/motivo) — alimenta a coluna
  `n_retries` da tabela de execuções.

### DI-17.2 — Varredura de `.tmp` órfãos [DI-06 item 1]
- `experiments.sweep_tmp_orfaos(data_root, idade_min_s=3600, dry_run=False)`: remove os `.tmp` que a
  escrita atômica (D58) deixa para trás num crash DURO (kill -9, spot-VM revogada, OOM). Não
  corrompem nada, mas em 16.500 runs viram dezenas de GB de lixo silencioso.
- **A sutileza que evita o desastre:** só apaga o que tem **mais de 1 h** — um `.tmp` recente pode
  ser de um run **VIVO** neste instante, e apagá-lo mataria a escrita em curso. Testado: o velho é
  removido, o recente sobrevive.

### DI-17.3 — `is_run_done` ESTRITO [DI-13.3 item (b)]
- Passa a exigir **`fe_final == maxfe`** além de `status ∈ {ok, retried_ok}` + camadas + footers.
- **Por quê:** um run abortado pelo teto de tempo não grava `failed`; se houver artefatos de uma
  execução ANTERIOR no disco, o resume o lia como PRONTO e um run **truncado entraria na bateria
  como completo, em silêncio**. Esta é a rede independente do motivo da parada; a raiz (o aborto
  gravar `failed`) é o item (a), no cartão do M7.
- Consumidor único = o despachante (`experiments.py:160`) — **não** os gates, logo nenhuma sessão
  ativa foi afetada.

### DI-17.4 — Guarda `mu/sigma > M` no export [DI-06]
- `write_surrogate` agora **ABORTA** se um vetor `mu`/`sigma` tiver MAIS componentes que M.
- **A assimetria é proposital:** o caso CURTO (`len < M`) é legítimo e vira NULL — é o mono-output
  do b1 (ParEGO, D47). O caso LONGO não é: significa que o instrumentador montou o vetor com mais
  objetivos do que o problema tem, e os extras seriam **truncados em silêncio** — exatamente a
  classe do bug do `n_front1` do retrofit-R2 (que só apareceu porque havia um teste).
- 4 testes de regressão em `tests/test_di13.py`.

**Pendente do M7 (não feito nesta janela, com razão):** DI-13.3 item (a) — o aborto gravar
`status='failed'` — toca os runners `c262`/`c154`/`standalone_harness`, e o `standalone_harness` é
lido pelo cartão R3-c122 em execução; fica para o cartão do M7. O `scripts/progress.py` apareceu na
árvore como untracked de autoria não declarada — **a torre não tocou** (regra de faixa).

---

## PARTE A7 — DI-18: auditoria de PROSA dos cartões R1/R2 (torre, 2026-07-19)

**O que foi auditado.** Um workflow adversarial de **64 agentes** leu, para cada um dos 15 algoritmos
já implementados nas rodadas R1 (MATLAB) e R2 (BoTorch), o **cartão/bundle + a seção da SPEC que o
gera + o código realmente entregue + os dados do run**, procurando *uma coisa só*: **frases que
descrevem um comportamento DIFERENTE do que o repositório faz hoje**. Não é auditoria de código — é
auditoria da **prosa vinculante**, que é o que uma sessão nova (ou o autor, no julgamento manual de
fidelidade D97) lê para decidir se o algoritmo está certo.

**Por que isso importa mais do que parece.** Nossa validação de fidelidade é **MANUAL e a
posteriori** (D97): o autor compara o comportamento observado com o comportamento DESCRITO. Se a
descrição estiver desatualizada, o autor vê uma **falsa discrepância** e reprova um algoritmo
correto — ou, pior, ratifica um errado. Uma linha de prosa obsoleta custa uma rodada inteira de
re-execução.

**Funil:** 71 achados brutos → 59 sobreviveram ao filtro de criticidade → **38 CONFIRMADOS** por
verificação independente contra o código/dados (16 🔴 = risco real de decisão errada). Os 21
descartados eram leitura desatualizada do próprio auditor ou duplicatas.

### DI-18.1 — Os dois achados que JÁ TERIAM causado dano (c217)

| # | O que a prosa dizia | O que o repositório faz | Consequência evitada |
|---|---|---|---|
| **C217-01** 🔴 | tabela de parâmetros: `DoE inicial = max(11D−1, N)`, "garante ≥50 amostras" | a implementação **injeta o artefato** (D63/D94): `fase=init` tem **21 linhas** no D=2 (=11·2−1), nunca 50 | o autor leria a tabela e concluiria que o **c217 viola o invariante 11D−1** — o mais grave dos invariantes do protocolo |
| **C217-02** 🔴 | "sob o fix: ger. 1 lote 41, depois 6 (~95 gerações)" | run real ZDT1: **588 gerações**, `lote`=1 em **585** delas (`Counter({1: 585, 6: 3})`) | o cartão descrevia o comportamento **AS-SHIPPED (pré-D17)**. O autor **já aceitou a fidelidade do c217 com nota 9/10** — conferir esse perfil teria produzido uma discrepância FALSA e reaberto um cartão fechado |

### DI-18.2 — Os 38 confirmados, por algoritmo (todos aplicados)

| Alg | Nº | Destaques |
|---|---|---|
| c217 | 6 | DoE injetado (🔴), perfil de lote medido (🔴), regra do lote v2.2, decisão superseded por D17, `.txt`→`.jsonl`, **âncora J medida a 2000 FEs** vs nosso orçamento 464 → *IGD acima da faixa é ESPERADO* |
| c141 | 4 | sinais do nível 2 `[−Fit1, Fit2, −Fit3]` (🔴), u=5 revogado (🔴), faixa de crash D≤9→D≤4, mtime do init RESOLVIDO (é stock), patch LHS → injeção classe D94 |
| b1 | 2 | 🔴 o patch de DoE substitui o **par `:29–:30` JUNTO** (patchar só a `:29` = **dupla-escala silenciosa** em WFG/BBOB); 🔴 a ③ grava a **população final do GA interno**, não best/geração |
| b3 | 3 | 🔴 critério = máx **MSE̅** (média das VARIÂNCIAS, **sem raiz** — `KrigingSelect.m:61`), não "máx σ̄"; a raiz é unidade de EXPORT apenas; D94 citada |
| b4 | 3 | 🔴 **rótulo 1 ⟺ não estritamente pior que todas as K=6 refs** — *dominação NÃO é exigida* (a prosa dizia "domina ≥1 referência", contradizendo o próprio cartão); nomes p0/p1; o stall 0-FE mora no 4º ramo |
| e7 | 2 | 🔴 dropout **0,1/0,1 do PAPER** (D30), não o 0,2/0,5 do código do autor; a divergência mora em DEF-B6.6, não no L.4; e7 **não** usa `trainNetwork` |
| c238 | 1 | **crash latente STOCK** documentado: front ND de 1 ponto → `Infill_EIM.m:25` colapsa a escalar → `Optimizer_GA.m:17` estoura. **Deliberadamente NÃO consertado** (falha honesta de código stock; conserto = decisão do autor, D81) |
| e74 | 4 | 🔴 **D94 APLICA-SE ao e74** (o gerador dizia o contrário); init nativo 100/200 substituído por 11D−1; D74 = min-max do **FRONT-1** fixo por chamada; desalinhamento máscara×Parent = **~24,8%/ciclo no ZDT1 (máx 91/100)**, não os ~8% do DTLZ2 |
| e103 | 3 | 🔴 centros RBFN = `ceil(sqrt(n_dataset))` (D93), não `ceil(sqrt(11D−1))`; 100 ger × pop 100 = 10.000 (o "99 ger" dava 9.900); **B7.7/7.8/7.9 FECHADAS** — não re-auditar |
| pisos | 2 | `UniformPoint(20,3)` → **H=4 → 15 vetores**: NSGA-III e MOEA/D rodam com **N efetivo 15** em M=3 (NSGA-II e SMS-EMOA mantêm 20) — o "N=20" **não é uniforme entre os 4 pisos**; MOEA/D com `T=2` gera **23% de duplicatas** e é o pior dos pisos — **não é bug**, é a D89 |
| c262 | 3 | 🔴 **S.3#9 era FALSO**: o `logei_fused.cpp` está no wheel OFICIAL também (byte-identidade verificada) → a política vigente é **DESLIGAR o kernel explicitamente** (DEF-L2/DI-05), não "usar o oficial porque não tem o kernel"; DEF-B8.6 **FECHADA** em D40; ref da aquisição = **oráculo S.5 congelado** ⇒ vantagem informacional declarada (D73) |
| c154 | 5 | 🔴 são **DOIS otimizadores** (caminhos ≠ aquisição), a prosa fundia num só; 🔴 B9.5 **fechada pela D75** — o piloto MEDE (×17,7), não escolhe; 🔴 o jitter 1e-6 **não basta** (NaN no LB do JES; sem a guarda o ZDT1 é irrodável); escada de fallback `(1024,10)→(2048,20)→(4096,40)`; likelihood LogNormal moderno × kernel Gamma-legado = assimetria **deliberada** |
| contrato R2 | 1 | DEF-L2 promovida a **política da rodada**, com a nota de que o desligamento é estado **POR PROCESSO** (cada subprocess D79 + despachante M8) |

### DI-18.3 — Onde as correções foram aplicadas (e por que não no cartão)

**Os bundles são ARQUIVOS GERADOS** (`gen_bundles.py`) — editá-los à mão seria perdido na próxima
regeneração. Portanto: **50 edições na `SPEC_experimentos_v5.2.md`** (fonte única) + **2 no
`gen_bundles.py`** (as duas frases que são literais *hardcoded* do gerador, não vêm da SPEC:
a faixa-guia do c217 e a nota de D94 do e74) + 1 no `DOSSIE_FIDELIDADE_R1.md` (o ~8% obsoleto).
Toda edição carrega a marca **⟦v5.2.1⟧** e, quando revoga um texto, mantém a **lápide** do texto
antigo — a rastreabilidade do que mudou é o que permite ao autor auditar a auditoria.

**⚠ PENDÊNCIA OPERACIONAL (única):** `python claude_code_context/gen_bundles.py` **NÃO foi
executado** — ele faz `rmtree` das 6 pastas de bundles, e havia **duas sessões de implementação
lendo essa árvore** (retrofit MATLAB e R3-c122). Regenerar com uma sessão aberta pode apagar o
arquivo que ela está lendo no exato instante. **Rodar assim que ambas fecharem**; até lá, SPEC e
bundles divergem nesses 52 pontos — e a precedência D83 (**vale a SPEC**) cobre o intervalo.

---

## PARTE A8 — DI-19: as 8 decisões do retrofit-R1 MATLAB (autor via sessão, renumeradas pela torre 2026-07-20)

**Por que DI-19 e não DI-17.** A sessão do retrofit MATLAB tomou 8 decisões do autor e as numerou
`DI-17.1…17.8`, sem saber que a torre **já havia ocupado `DI-17.1…17.4`** com o hardening do M7
(PARTE A6). Colisão real: uma sessão futura que lê `[DI-17.2]` num comentário `.m` e vai ao REGISTRO
encontra "varredura de `.tmp` órfãos". A torre **realocou o bloco do retrofit para `DI-19.x`**
(2026-07-20): 40 citações em 9 arquivos `.m` (`SondaState`, `c238_sonda`, `e74_sonda`, `experiment`,
`b3_sonda`, `b3_instrument`, `b4_instrument`, `KRVEA`, `ParEGO`) + 19 no `handoff/DI09-retrofit-R1-cont.md`,
todas verificadas por grep (0 `DI-17.x` do sentido-MATLAB restante). **A regra que faltava (agora
firme):** quem abre um bloco `DI-N` novo **reserva o número no REGISTRO ANTES** de usá-lo no código.

| # (novo) | decisão | efeito |
|---|---|---|
| **DI-19.1** | **e74: um `SondaState` POR CABEÇA**, `k` próprio + fase deslocada | o `g` do hook do e74 bumpa **4× por ciclo** (`CLMEA.m:46/:90/:100/:112/:135`); sob 1 estado com k=2, s1/s3 disparavam todo ciclo e a **s2 (RBF global) NUNCA** disparava. ⚠ ainda `🟡 PENDENTE DE RATIFICAÇÃO` no cabeçalho de `e74_sonda.m:27` → **D-11 do lote DI-20** (nenhum run do e74 rodou com sonda, decisão livre) |
| **DI-19.2** | `f_best`/`n_front1` = **arquivo real PÓS-ciclo** | sem definição operacional os configs divergiam (c141 pós, b1 pré → curvas defasadas de 1 infill); b1 realinhado; b3/b4 usam o `A2` (o `A1` é podado com teto NI) |
| **DI-19.3** | e103 `n_geracoes` = ③ com filtro `regime != 'sonda'` | **substitui** a instrução do cartão (a ② offline só lista membros do dataset → 4 gerações para um run de 99) |
| **DI-19.4** | `dist_min_arquivo` em espaço **NATIVO** nos 21 | a SPEC §S.7.1 diz "normalizado"; c141/c217 (aceitos) usam nativo; não é renormalizável post-hoc → **doc-sync D-14 do lote DI-20** |
| **DI-19.5** | `finalProbe` usa `g_armado`, não `buf.gen` | em overshoot-zero (c238) o `PlatEMO:Termination` sai do topo do ciclo seguinte, depois de o `outputFcn` já ter bumpado ⇒ `buf.gen` aponta geração nunca armada. Não é bit-neutro ⇒ c217/c141 re-rodados |
| **DI-19.6** | c238: sonda em espaço **CRU** | régua constante entre gerações e comparável ao gabarito (responde à pendência de `handoff/R1-c238.md` §8, aberta desde a R1) |
| **DI-19.7** | offline: `f_best` = pop corrente **+** min do dataset no header | superconjunto; vale para os 5 offline |
| **DI-19.8** | `espaco_modelo` = **`"cru"`** nos 21 | `"nativo"` estava fora do enum `("transformado","cru")` que `export.py:292` valida — o writer MATLAB não valida e passava calado. ⟦**FECHADA em 7b6ac6e** (sessão DI09-R1c, fase final): a anotação anterior — 'só o MMF1 re-rodado, 1.050.000 linhas nativo' — foi resolvida; **verificado pela torre 2026-07-22: 0 linhas 'nativo' no repo inteiro**, e o teste permanente `test_espaco_modelo_dentro_do_enum` (D-15) trava regressão⟧ |

---

## PARTE A9 — DI-20: auditoria do RETROFIT DI-09 (MATLAB R1 + BoTorch R2) — torre, 2026-07-20

**O que foi auditado.** Um workflow adversarial de **90 agentes** (10 lentes independentes +
verificadores céticos por achado, viés default REFUTAR) leu código, dados, docs e rodou os gates,
para responder às perguntas do autor: o retrofit está feito e correto? nada conflitou? os outputs
bastam para a análise? nota 0–10 de comportamento por algoritmo? Colheita: **43 achados
sobreviveram** à refutação (12 CONFIRMADOS, 31 PARCIAIS; 19 refutados como leitura de doc
desatualizado ou severidade inflada). *(17 dos 90 agentes — refutações de doc-sync/decisões — não
completaram por limite semanal de API; não afeta o núcleo, pois os achados vêm da fase de auditoria,
que fechou 10/10 lentes.)*

### DI-20.1 — O INVARIANTE CENTRAL ESTÁ PROVADO
Não-perturbação da ① (o coração da DI-09): **53/53 `__real.parquet` bit-idênticos** ao
`_baseline_pre_retrofit` (sha256 do arquivo inteiro), sendo **32 comparações INFORMATIVAS** (runs
re-executados APÓS o snapshot de 2026-07-19 09:41 — a igualdade prova algo) e o restante tautológico.
A sonda respeita a **ordem do artefato**: `max|x_sonda − artefato| = 0.0` em 100% dos blocos
verificados (não só o bloco 0), o que valida o join-por-posição do R4. Cadência **alinhada nos dois
stacks** (`{1,2,4,6,…}` em 20/20 runs) — a dúvida B-0 do repasse R2 está **fechada**.

### DI-20.2 — COBERTURA REAL (o "7/11" e o "R2 completo" são honestos, mas há letra miúda)
- **MATLAB R1:** 7/11 completos (**b1, b3, b4, c141, c217** + os **4 pisos**); os 4 declarados
  faltantes (**c238, e7, e74, e103**) estão em **ZERO** — `<alg>_sonda.m` escrito e revisado, mas
  **NÃO LIGADO** (0 referências no `run_<alg>` do `experiment.m`), `fe_treino_max` 100% NULL. As 2
  correções que a sessão alegou (isstruct→isa no e74; probeOffline no e103) **estão no disco**.
- **BoTorch R2:** "completo" é verdadeiro DENTRO do escopo, mas a **sonda cobre 3 de 5 runs**
  (c262/MMF1, c262/DTLZ2, c154/MMF1). O **c262/ZDT1 — o melhor resultado da bateria (IGD+ 0,0008)** —
  não tem sonda, `fe_treino_max`, `sigma_dict` nem `modelo_hp`: a qualidade do modelo é não-medível
  exatamente onde ele mais vence.

### DI-20.3 — O GP APRENDE, E A SONDA MEDE (a validação da tese)
c262/DTLZ2: WAPE **0,1188→0,0695** (−41,5%, corr(fe_treino_max, WAPE)=−0,969), σ médio cai pela
metade (corr=−0,988), **calibração exemplar** (cobertura 2σ=0,978 vs nominal 0,954). O **achado de
ouro**: c154/MMF1 it30–37 — o ruído inferido do GP explode 90×, o σ CAI 37% e o erro SOBE 30% (o
modelo fica **pior e mais confiante** ao mesmo tempo; cobertura 2σ despenca 0,934→0,577 e recupera na
it38). **Nenhuma métrica interna da busca veria isso — só a sonda vê.** O contraste é atribuível a UMA
escolha: c262 fixa `train_Yvar=1e-6` (D40) e nunca degenera; c154 infere o ruído e degenera.

### DI-20.4 — NOTAS DE COMPORTAMENTO (0–10, semente 0, ancoradas em número medido)
Ressalva metodológica: **1 semente por célula** — nada aqui é estatisticamente testável; o que
sustenta as notas baixas é a **evidência mecânica independente** (mu divergente, `n_ds_membros`
zerado, cache-hits saturado, sonda "chata") que corrobora o resultado ruim.

| config | nota | síntese |
|---|---|---|
| c262 (qNEHVI) | **9,5** | melhor otimizador nos 3 (IGD+ 0,039/0,030/**0,0008**); sonda cai monotônica; só não é 10 porque o ZDT1 não tem sonda |
| b1 (ParEGO) | **8,5** | sólido e consistente (2º/3º/3º); sigma sem NaN; teto pela sonda estruturalmente incomparável (mono-output D47) |
| smsemoa (piso) | **8,0** | piso mais forte e honesto; bate 6 dos 10 SA-MOEAs em DTLZ2 |
| e74 (CLMEA) | **7,5** | bate os 4 pisos em DTLZ2/ZDT1; perde ponto só por instrumentação ausente (sem sonda ainda) |
| nsga3 (piso) | **7,5** | piso saudável, sem degeneração |
| c154 (JES) | **7,5** | sonda aprende bem no MMF1 (+53%); penalizado pelo custo (DTLZ2 = 14,6 h, o pior wall) e por não bater piso |
| c238 (EIM) | **7,0** | busca boa (bate pisos em DTLZ2/ZDT1); cai por instrumentação ausente em bloco (sem sonda) |
| nsga2 (piso) | **7,0** | baseline honesto, faz o que um piso deve |
| b3 (K-RVEA) | **6,5** | **dissociação severa**: ZDT1 exemplar (2º melhor, melhor curva de sonda), mas DTLZ2 **abaixo dos 4 pisos** e sonda "chata" (+4%) |
| b4 (CSEA) | **6,5** | busca acima dos pisos, mas o classificador quase não discrimina (spearman ~0,15 oscilante) e a ③ de busca tem ~1 linha/geração |
| e7 (EDN-ARMOEA) | **6,0** | bate pisos no ZDT1/MMF1, mas não clera o piso em DTLZ2 (M=3); sem sonda |
| c217 | **4,5** | o SA-MOEA mais fraco; score de discriminação ~nula e `pred_confianca` CONSTANTE por bloco; pior que o nsga2 no ZDT1; ainda `sigma_dict=null` |
| moead (piso) | **4,0** | **régua quebrada no ZDT1**: 182 cache-hits/183 guards, IGD+ 1,89, HV=0 — piso degenerado (não é bug: D89) |
| c141 (MMRAEA) | **4,0** | dupla personalidade: 2º melhor em DTLZ2/ZDT1, mas **divergência numérica do RBF no MMF1** (mu explode para [−145, 210] vs f∈[0, 8,3]; MAE ×8,7) → pior config no MMF1, abaixo dos pisos |
| e103 (IBEA-MS, offline) | **4,0** | pior qualidade nos 3; ZDT1 falha total (a busca sai do suporte do dataset: `n_ds_membros` 82→0); **camada ⑦ AUSENTE** ⇒ o endpoint oficial do offline não existe |

### DI-20.5 — SUFICIÊNCIA DOS OUTPUTS (resposta à pergunta do autor)
Para os 7 configs completos + os 2 BoTorch com sonda: **sim, os parquets + logs bastam** — as 5
análises ((a) IGD+/HV, (b) WAPE/calibração, (c) uso da incerteza, (d) escalabilidade, (e) prova de
fidelidade) rodaram de ponta a ponta e deram número plausível. **NÃO bastam** para: os **4 MATLAB
sem retrofit** (c238/e7/e74/e103 — sem sonda, sem análise de assertividade do surrogate), o
**c262/ZDT1** (sem sonda no melhor run), o **e103** (⑦ ausente ⇒ sem métrica oficial offline), e o
**c217** (`sigma_dict=null` ⇒ a ③ é "leitura proibida" pela regra 3 do R4).

### DI-20.6 — OS 5 DEFEITOS QUE OS GATES NÃO PEGAM (os documentos os davam por resolvidos)
1. ⟦**FECHADO** pela sessão DI09-R1c (7b6ac6e) — 0 linhas 'nativo' restantes, verificado pela torre⟧
   ~~DI-19.8 incompleta: `espaco_modelo="nativo"` em 1.050.000 linhas~~
2. ⟦**FECHADO** pela mesma sessão — sigma_dict preenchido nos 3 manifestos do c217 e re-verificado
   pela torre 2026-07-22 (2 chaves, como b3/b4)⟧ ~~c217 sem `sigma_dict`~~
3. **Deriva de schema DENTRO do config**: no c238/e7/e74/e103 o MMF1 tem `fe_treino_max`+timing novo,
   DTLZ2/ZDT1 não — e onde a coluna existe é 100% NULL.
4. **`timing` do manifesto NULL** nos 9 runs de c238/e7/e74 (parcial no e103) — o CONTRATO §4 o torna
   OBRIGATÓRIO.
5. **`tempo_geracao_s` EXCLUI a sonda** (medido: 1.129/1.129) — o CONTRATO §4 dizia "wall TOTAL".
   **CORRIGIDO nesta passada** (doc-sync, DI-13.10).

### DI-20.7 — AS 21 DECISÕES EM ABERTO CONSOLIDADAS (a torre DEVE levantar com o autor)
A varredura de TODOS os handoffs + REGISTRO + SPEC + CONTRATO + cards encontrou **31 pendências
documentadas; 24 já estavam resolvidas** por commits posteriores (o custo dessa dessincronia é
justamente o que esta auditoria pagou em horas). Restam **21 decisões vivas**, consolidadas em
`handoff/DI20-AUDITORIA-RETROFIT_DECISOES.md` e resumidas na resposta ao autor. Classificação:
**4 BLOQUEIAM a M8** (D-01 `n_acumulado` NULL dos pisos; D-03 `is_run_done` bucket-aware; D-06
`experiments.py` repassa `data_root`/`enable_bucket`; D-12 ⑦ no `is_run_done`), **7 de contrato de
dados**, **3 de fidelidade** (só o autor, D97: D-04 b4 `n_acumulado`, D-11 e74 cadência, D-20 c149),
e o restante de infra/doc-sync.

### DI-20.8 — O QUE A TORRE JÁ CORRIGIU NESTA PASSADA (sem tocar faixa de sessão viva)
- Renumeração **DI-17.x → DI-19.x** (colisão resolvida — DI-19 acima).
- CONTRATO §4: `tempo_geracao_s` **EXCLUI a sonda** (era "wall TOTAL").
- CONTRATO §3.1: "2000 linhas" → **ONLINE 2000 / OFFLINE 20.000** (`geracao`=NULL) — fim da
  contradição interna.
- Registro completo (esta PARTE A9) + as notas de comportamento + as 21 decisões escaladas.

---

## PARTE A10 — DI-21: as 21 decisões RATIFICADAS pelo autor + aplicação pela torre (2026-07-22)

**O ato.** O autor leu a consolidação DI-20.7 (`handoff/DI20-AUDITORIA-RETROFIT_DECISOES.md`) e
**aprovou TODAS as recomendações em bloco** ("concordo com sua recomendacao nas 21 decisoes. pode
aplicar"). Esta parte registra o que cada decisão virou — código, doc ou registro — e a prova.

### DI-21.1 — Ratificações de FIDELIDADE (D97 — decisão do autor, agora cravada)
| ref | decisão ratificada |
|---|---|
| **D-04/R-1** | `n_acumulado` de **c217 E b4 EM BLOCO** = nº de pontos no **TREINO** (não o arquivo) — os dois subamostradores alinhados; `arc_size` no jsonl preserva o tamanho do arquivo. Muda a ④ vs baseline; a ① ficou bit-a-bit (23 gates) |
| **D-11** | e74: **um `SondaState` POR CABEÇA**, round-robin **k s1=6 / s2=3 / s3=12** (cada ciclo sonda 1 cabeça; cada cabeça a cada 3 ciclos) — como implementado; dado produzido: **71/71/71 blocos + 1 boot** no ZDT1, verificado pela torre no jsonl |
| **D-20** | c149: rota **(c) TIMEBOX explícito**, definido e decidido **ANTES do M7** — "reconstruir o loop" é o maior risco de fidelidade do R3; descobrir na M8 é o pior mundo |
| **D-19det#4** | **cache-hit D89 × arquivo crescente** (c122 §5.3): no cache-hit o arquivo **NÃO cresce**; ③ gravada com `real_solution_id` da preexistente + cap p/ hits consecutivos. **Propagado** aos checklists de c149 e e81 na SPEC (o hazard gêmeo) |

### DI-21.2 — Código aplicado pela torre (com teste para cada)
| ref | mudança | onde |
|---|---|---|
| **D-01** | `n_acumulado` NULLABLE na ④ + writer com o idioma da DI-13.2 | `export.py` |
| **D-02** | `normalize_schema` + `cast_completo` + `concat_normalized` + `INT32_NULLABLE_COLS` — o cast canônico OBRIGATÓRIO da consolidação cross-stack | `export.py` |
| **D-03** | `is_run_done` **bucket-aware** (`_bucket_has`, falha FECHADA: sem lib/rede ⇒ False) — a promessa da D58 cumprida; sem isto a VM re-executaria os 5 configs mais caros para sempre | `manifest.py` |
| **D-06** | despachante repassa `data_root` ao runner (a mescla DI-13.1 achava o manifesto no root errado) + carimbo `paths.bucket` **CONDICIONAL** ao upload confirmado | `experiments.py` |
| **D-07** | aborto por teto grava **manifesto `failed`** no sítio (padrão c122 replicado) + exceção `WallClockAbort` **não-retriável** no despachante (um teto de 8h não vira 24h) | `c262_qnehvi.py`, `c154_jes.py`, `experiments.py` |
| **D-12** | os 5 OFFLINE (`OFFLINE_ALGS` = e103/b5r/b5m/c311/moead_media) exigem a **⑦** no `is_run_done`; `plan_targets(optional_layers=…)` planeja a ⑦ na rota única | `manifest.py`, `gcs.py` |
| **D-15** | teste de CONTRATO permanente: varre os parquets REAIS do repo (normalização + enum + cast) — teria pego o "nativo" e o `n_acumulado` dos pisos antes de qualquer auditoria | `tests/test_di21_contrato.py` (19 testes) |
| **D-16** | despachante desliga o **kernel fusionado** antes de despachar BoTorch (DEF-L2/DI-05 — estado POR PROCESSO; import lazy e tolerante) | `experiments.py` |
| **B34** | `manifestBlock` do SondaState ganha o campo `regime` — **provado com o run-STUB MATLAB real** (regime=online, 4 blocos, asserts internos verdes, ① do stub intacta) | `SondaState.m` |
| — | **Validadores PROMOVIDOS a permanentes** (2 sessões seguidas os reconstruíram no scratchpad): gate 1 não-perturbação + gate 2 auditoria da sonda/④/⑤/⑦. Provados: **53/53** baselines verdes; **16/16** runs de todos os tipos (MATLAB online, offline 2×20k, multi-cabeça, pisos, BoTorch, standalone) | `scripts/naoperturbacao.py`, `scripts/auditar.py` |

### DI-21.3 — Dados corrigidos/completados
- **⑦ do e103 GERADA nos 3 problemas** (`scripts/final_eval.py`; 42/158/188 ND pós-real) — o
  endpoint oficial do offline EXISTE agora; era o achado A3/nota-4,0 da DI-20.
- **Backfill derivado do c262/ZDT1 (D-10):** ④ com 623/623 `tempo_busca_s` (0 NULL; Σ=13.389 s ≈
  89% do wall de 15.051 s), procedência `timing_backfill` no manifesto — o timing do run de ~4h
  recuperado sem re-execução.

### DI-21.4 — Doc-sync executado (as contradições ativas mortas)
- **Fórmula da cadência NORMATIVA** (`g==1 OU mod(g,k)==0` ⇒ {1,2,4,6,…}) na SPEC §17.2.2 E no
  CONTRATO §3.1 — a ambiguidade que gerou a divergência cross-stack não pode morder os 6 cartões
  R3 restantes.
- **DI-16.3 REESCRITA** (semântica A+ do autor) e **perna (ii) da DI-16.2 corrigida** — SPEC +
  este registro.
- **N.1.1 generalizada**: dtype = o que o repo do autor exige, registrado no manifesto (o c122
  exige float32 — medido).
- **Regra 2 do R4 GENERALIZADA por classe** (T-2: inclui `geracao`/`n_acumulado`/`fe_treino_max`)
  com o mecanismo `normalize_schema` como obrigatório — CONTRATO §10.
- `dist_min_arquivo` = espaço **NATIVO** (DI-19.4) + **NULL no offline** (D-08) — SPEC §S.7.1.
- **D-09/T-8**: ④ do e103 = **1 linha** (a série é por RETREINO e o e103 tem um) — exceção
  declarada; a curva por geração cabe no jsonl sem patch no stock.
- e74 = **TRÊS cabeças round-robin** no CONTRATO §3.2 (dizia "as duas") + critério DI-12.1 do
  patch read-only no §6.1.
- Renumeração DI-17→DI-19 já registrada na PARTE A8; agenda sincronizada (D-21); INDEX atualizado.

### DI-21.5 — Decisões REGISTRADAS sem ação imediata (com dono e prazo)
| ref | o quê | quando |
|---|---|---|
| D-17 | endurecer o check de RNG do R2-00 (molde do R3-00) | cartão M7 |
| D-18 | manter `load_sonda` duplicado (teste de equivalência protege); reavaliar se surgir 3ª cópia | M7 |
| D-16c | VM da M8 SEM toolchain C++ (torna o kernel fusionado impossível por construção) | provisionamento M8 |
| D-05 | ZDT1 de c238 (3h55) e e7 (72min) FORA do piloto — entram na bateria M8 normal | M8 |

## PARTE A11 — DI-22: provisionamento Mac dos 3 envs restantes + re-pin do e81 (autor, 2026-07-22)

**A decisão do autor.** "Quero implementar tudo aqui no Mac com Claude Code; a VM só na hora de
disparar os experimentos em massa." A torre verificou a viabilidade (PyPI pin a pin — ver
`requirements/README.md`) e **PROVISIONOU + VALIDOU os 3 envs no Mac**, sem tocar a faixa da
sessão R3-c149 (ativa durante a operação).

### DI-22.1 — O RE-PIN do e81 (decisão D80 do autor)
`torch==2.12.0` → **`torch==2.11.0`**. Motivo verificado: o wheel arm64 do 2.12.0 exige
macOS≥14 (o pip deste Mac rejeita — medido), não existe wheel mac x86_64 nem sdist. O 2.11.0 é
**o MESMO torch do env_main** (c262/c154/c122 já rodam nele; consistência até MELHORA) e o
botorch 0.16.1 só exige ≥2.0.1. Aplicado em `requirements/env_e81_qpots.txt` + `envs.json`.
⚠ A VM da bateria usa o MESMO requirements re-pinado.

### DI-22.2 — Os 3 envs provisionados e PROVADOS (ferramenta: micromamba osx-64, sem sudo)
| env | rota | prova executada |
|---|---|---|
| **env_b5** (b5r/b5m/piso-off) | **Rosetta x86_64, py3.7.12** — sklearn 0.21.3 + pandas 0.25.3 por wheel (a nota "inviável no Mac" valia só p/ arm64 nativo) | desdeo_* importam; **harness COMPLETO em py3.7**: 8 módulos importam, `write_timing` grava, `load_sonda` lê a fatia offline 20k |
| **env_c311** | **Rosetta x86_64, py3.8.20** + GPy 1.9.9 **compilado do sdist** | GPy treina+prediz (GPRegression+RBF, var≥0); harness importa; sonda offline OK |
| **env_e81_qpots** | **arm64 NATIVO, py3.11.9** (com o re-pin) | botorch 0.16.1 `fit_gpytorch_mll`+posterior OK; harness importa; sonda online OK |

### DI-22.3 — As 2 lições que VALEM PARA A VM (registradas nos requirements)
1. **env_c311 = Python 3.8 EXATO, nunca 3.9**: o C pré-gerado do GPy 1.9.9 usa `tp_print`
   (removido no py3.9) — o build falha em 3.9 EM QUALQUER plataforma. Descoberto aqui; a VM
   herdaria o mesmo erro.
2. **`Pillow<10` no env_c311**: o Pillow moderno exige numpy≥1.21 (`numpy.typing.NDArray`) e o
   pin é 1.20.2. Adicionado ao requirements.

**Pendência deliberada (não é lacuna):** o pin do `desdeo-emo` segue DEFERIDO ao gate R3.2 —
o cartão R3-b5 o crava com o autor (o overlay vendorizado root-first é o primário de qualquer
forma). **Caveat de regime (§19):** os gates no Mac provam corretude/mecanismo; a numérica
canônica da bateria Python sai da VM no M8.

---

## PARTE A12 — DI-23: validação do R3-c149 pela torre + correções de infra (2026-07-22)

**O cartão.** A sessão (Fable 5) reconstruiu o loop do LBN-MOBO em 6h do timebox de 10h — o maior
risco de fidelidade do R3 pago em sessão. **Validação da torre (workflow de 8 agentes Opus +
refutação): código VERDE (fiel ao checklist §22.4·3.4, não-interferência limpa — 4 arquivos, tudo
aditivo, vendorizado+repos.lock intocados) · dados VERDE TOTAL (cadência bit-exata à fórmula
normativa, ordem do artefato em TODOS os blocos, C3 100%, DI-10 completo, ③-busca reconstituível
com erro ~1e-7) · gates ao vivo todos verdes (272 testes pós-DI-23).**

### DI-23.1 — O achado de comportamento (o cartão de nota 5/10)
**Bimodal, e NÃO é defeito de pipeline** (2 refutadores confirmaram: comportamento FIEL):
- **ZDT1 exemplar**: bate os 4 pisos, val-MSE 0.18→0.024 (o ensemble aprende), HVI decai.
- **MMF1 e DTLZ2: ganho de IGD+ sobre o DoE = LITERALMENTE ZERO** (0.0956==DoE; 0.4532==DoE),
  abaixo dos 4 pisos. Mecanismo MEDIDO: em baixo-n o ensemble é preditor-da-média (val-MSE(z)~1.0)
  ⇒ HVI=0 em 40/40 gerações (MMF1) ⇒ a seleção colapsa no subconjunto de σ² MÁXIMA = os cantos do
  box (f≈(1,2), todos dominados). No DTLZ2 o HVI funciona (240/240) mas premia extremos de eixo —
  o surrogate NÃO superprediz (|mu−real| mediano [0.03,0.07,0.14]); é a seleção HVI-greedy fiel à
  D96. **É RESULTADO científico** (o que o estudo existe para medir) e o caso que o D70 já previa
  (HV degenerado excluído do Friedman). Vai como número-guia ao D97.
- Correção de precisão vs o repasse: os infills do MMF1 caem em DOIS cantos opostos (não um), e a
  via dominante é o fallback_aleatorio (32/40) DENTRO do conjunto de σ² máxima (não o desempate
  direto 8/40).

### DI-23.2 — Os 5 achados estruturais: TODOS CONFIRMADOS (linha a linha) e o que a torre fez
| § | achado | ação |
|---|---|---|
| 3.1 | seeds.json em conflito com a SPEC (seed NSGA-II constante do stock = LIVELOCK no cache-hit D89; provado) + rótulo do uso 2 STALE | ✅ **seeds.json SINCRONIZADO** (usos 0/1/2 do c149 reescritos + offset corrigido) |
| 3.2 | nota SPEC:722 factualmente incorreta ("1/30 hard-coded") — medido: pymoo 0.6.2 = `min(0.5, 1/D)`; o autor cravou o default | ✅ **SPEC:714/722 corrigidas** + bundles regenerados |
| 3.3 | `write_run_outputs` carimbava `status='ok'` fixo — o c122 prometia `failed` no teto e não cumpria | ✅ **kwarg `status=`/`motivo_parada=` no harness** + call-site do c122 corrigido + 3 testes (o aborto grava failed E o `is_run_done` o reprova) |
| 3.4 | `emit_sonda_block` sem as colunas C3 (o c149 carimbava pós-hoc) | ✅ **kwarg `c3=` no helper** + 2 testes — b5/c311/e81/piso-off já nascem sem o contorno |
| 3.5 | desempate do HVI-greedy em σ²-agregada-EM-Z (decisão de sessão declarada) | 🔴 **AGUARDA RATIFICAÇÃO DO AUTOR** (recomendação da torre: RATIFICAR — ver resposta de 2026-07-22; a evidência DI-23.1 do colapso-de-canto pertence ao D97, não muda a leitura correta da D96) |

### DI-23.3 — DEF-N4 (o c149 fica?)
Recomendação da sessão: **FICA** (risco pago, único BNN online, custo medido 3,37h<8h no ZDT1).
A torre CONCORDA, com a nota honesta: o comportamento 5/10 (ganho zero em 2/3 pilotos) NÃO muda a
recomendação — é exatamente o dado que a tese quer reportar — mas pertence ao julgamento D97 do
autor, cuja condição já estava registrada (reprovação ⇒ fallback env_c149_fallback/D78, não drop).

### DI-23.4 — Lacuna de cobertura registrada (não corrigida nesta janela)
Os caminhos de ABORTO do c149 (teto_s, cache-cap) seguem sem teste de ponta-a-ponta (achado A1,
baixo) — o plumbing do manifesto failed agora TEM teste (DI-23.2/3.3); o exercício end-to-end fica
para o M7 (registrado).

---

## PARTE A13 — DI-24: validação do R3-e81 + correções de infra (torre, 2026-07-22)

**O cartão.** Runner qPOTS (Opus... não — a sessão rodou conforme o plano) sobre o vendor INTOCADO
com 3 ganchos read-only. **Validação da torre (workflow 10 agentes Opus + refutação): código VERDE
(receita canônica; kernel = o MESMO helper de c262:195/c154:247; não-interferência limpa) · dados
VERDE (auditoria pyarrow integral; corr(mu, f_true) até 1,0000) · gates ao vivo verdes (295 testes
pós-DI-24) · NOTA DE COMPORTAMENTO 9/10** — o OPOSTO do c149: infills diversos (2,5-5,6% no bordo),
GP aprendendo limpo (MAE out-of-sample caindo monotônico nos 3), ganhos de 32-53% sobre o DoE, e o
MMF1 batendo TODOS os pisos e o c122. Ressalvas (não-bugs): MMF1-obj1 superconfiante (sin-ridge
inaprendível com <60 pts) e ZDT1 estagnando nos últimos 40% do orçamento (a natureza do qPOTS em
30-D — o GP é excelente (WAPE<1%) e o front fica grosseiro: o gargalo é o PODER da aquisição, o
contraste perfeito com o qNEHVI). **A parede de custo do e81 NÃO é o fit O(n³) (13-16% do wall,
n^1,9-2,4): é a AQUISIÇÃO (84-87%, plana em n, explode com D)** — insumo novo do M7.

### DI-24.1 — Os achados do dossiê: verificados, recalibrados e o que a torre fez
Os 10 itens são REAIS (7 confirmados integrais); os refutadores rebaixaram as severidades de
infra para "baixo" (nenhum corrompe dado atual). Correções APLICADAS (com teste; suíte 295 OK):
| item | ação |
|---|---|
| §4.2 c3= dict×string | ✅ teste do DI-23 corrigido (dict) + **guarda falha-ALTO** em `surrogate_row` (string ⇒ ValueError — o duplo-encode silencioso morreu) + 2 testes |
| §4.3 ④ NULL no cache-cap do c149 | ✅ o break sai APÓS a ④ fechar (flag `abortar_cache`; padrão do teto_wall) — o run abortado grava ④ válida |
| §4.4 `q` no manifesto | ✅ kwarg `q=` no `write_run_outputs` → `new_manifest` (o carimbo pós-hoc do e81 vira redundante; o batch M10 usa o kwarg; a MESMA lacuna existe no botorch_harness p/ c262/c154-batch — registrada p/ o cartão SUB-batch) |
| §8.7 f_hash_online | ✅ comparado ao sidecar nos DOIS load_sonda (standalone + botorch) — falha fechada |
| §8.2 granularidade ③-busca | REFUTADO como defeito: o `sigma_dict` (regra 3 do R4) JÁ crava rank-0/front nos 2 configs aceitos; as análises §9 são INTRA-config (a régua inter-config é a SONDA). Qualificador editorial "(rank-0/front)" adicionado à DEF-C2 no CONTRATO |
| §8.8 auditar.py só no env-main | aceito e documentado (o validador roda no env-main — que é onde a torre valida) |

### DI-24.2 — Decisões que aguardam o AUTOR (levantadas na resposta de 2026-07-22)
1. 🔴 **Kernel do e81** = `get_matern_kernel_with_gamma_prior(D)` (o MESMO de c262/c154; D30
   "Compartilhado"; sem ele o ZDT1 não fecha o fit). Recomendação da torre: RATIFICAR.
2. 🟠 **Fallback |ND|<q do batch** (MMF1 na borda: |ND| mín=10): definir o "qmaximin" citado.
   Recomendação: completar o lote até q por seleção maximin sobre o restante da população.
3. 🔴 (pendente desde DI-23) **desempate σ²-em-z do c149**.
4. (pendente) `scripts/progress.py` — adotar ou descartar.

---

## PARTE A14 — DI-25: as 4 ratificações do autor pós-e81, aplicadas (2026-07-22)

**O ato.** O autor aprovou em bloco as recomendações da torre ("aprovo suas recomendacoes nas 4
decisoes e em todas outras que estiverem em aberto"). Aplicado:

| # | decisão ratificada | onde foi cravada |
|---|---|---|
| 1 | **Kernel do e81 = `get_matern_kernel_with_gamma_prior(D)`** — o MESMO helper de c262:195/c154:247 (D30 "Compartilhado"); com o stock o fit do ZDT1 morre; com o helper 28/28 fits OK | SPEC §22.4·3.5 + L.12 (2 sedes) + bundles regenerados |
| 2 | **Desempate do HVI-greedy (D96/c149) = σ² agregada EM Z** (escala-neutra; σ² nativa deixaria o objetivo grande dominar) | SPEC §22.4·3.4 + linha D96 (2 sedes) — fecha a pendência da DI-23 |
| 3 | **Fallback `\|ND\|<q` do batch = qmaximin DEFINIDO**: completar o lote até q por seleção MAXIMIN sobre o restante da população (rank-1+), maximizando a distância mínima aos já-selecionados; falha-alto se nem assim fechar. Risco medido: MMF1 na borda (\|ND\| mín=10). **Implementação = cartão SUB-batch/M10** | SPEC §22.4·3.5 + L.12 (2 sedes) |
| 4 | **`scripts/progress.py` ADOTADO** — revisado pela torre linha a linha: READ-ONLY genuíno (jsonl/manifesto/grid; vivacidade pelo FOOTER — a lição das sessões MATLAB), testado ao vivo (painel + tabela + placar 64 ok/19.950 grid). Vira ferramenta permanente da esteira | commitado; é o "painel M7 incremento 3/4" que faltava rastrear |

**Varredura do "todas as outras em aberto" — também aplicado:**
- **`q`/`status`/`motivo_parada` no `botorch_harness.write_run_outputs`** — a lacuna simétrica
  registrada na DI-24 (o batch q=10 de c262/c154 nasceria com manifesto q=1): fechada AGORA, sem
  esperar o cartão SUB-batch.
- Itens que PERMANECEM agendados com dono (não são decisões): D-17 (RNG check R2-00, M7) · D-18
  (load_sonda duplicado, M7) · teste end-to-end dos abortos (M7) · dossiê itens 3/4/5 + julgamento
  D97 (a fila do autor) · enable_bucket + VM sem toolchain C++ (M8).

Suíte pós-DI-25: **295 OK**. Bundles: 44 regenerados (as ratificações já chegaram aos cartões
e81/c149 — verificado por grep).

---

## PARTE A15 — DI-26/DI-27: validação-torre do PARALELO b5 ∥ c311-Fase-A + 3 fixes de infra (2026-07-23)

**Contexto.** Primeira execução PARALELA de duas sessões de implementação (R3-b5 fechando; R3-c311
em 2 fases coreografadas, Fase A restrita a arquivos próprios). A torre validou os dois retornos com
forense de git, gates ao vivo e workflow de 15 agentes (8 auditores + 7 verificadores adversariais).

### DI-26 — fix central do `doe.py` (achado da sessão b5, aplicado pela torre DURANTE o paralelo)
`_read_matrix_parquet` usava `ChunkedArray.to_numpy(zero_copy_only=)` — kwarg inexistente no
pyarrow 12 do env_b5 (caminho offline-Python nunca exercitado antes do b5; a VM Linux herdaria).
Forma `combine_chunks().to_numpy(...)` funciona em 12/17/25 e é BIT-IDÊNTICA (hash == sidecar em
env_main E env_b5). Commit `9e9ea9c`. O shim local do b5 é auto-desativante e coexiste. Protocolo
exemplar da sessão: NÃO editou o arquivo compartilhado durante o paralelo; escalou à torre.

### DI-27 — veredito do paralelo + 3 fixes (commit `b782167`)
**Veredito: ZERO conflito.** Interseção de arquivos dos 4 commits (e3ecab1/8847f0a × 4d8a997/ba55f18)
= ∅; árvore limpa; o ÚNICO editor de compartilhados foi o b5 (aditivo — accept/dispatch/artefatos da
faixa dele; o c311-A tocou só `src/c311_tgprmo.py` + `tests/test_c311.py`). Gates ao vivo da torre:
suíte **309 OK** · preflight 0 · não-perturbação **53/53** · auditar **9/9** · final_eval **9/9**.
Notas da auditoria: compartilhados 9 · envs-docs 8,5 · patches-vendored 8,5 · código-b5 8.
- **Fix 1 — o `-I` tornava o `PYTHONHASHSEED=0` INERTE (único achado CONFIRMADO em média).**
  `run_in_venv` setava a var no child_env mas lançava o filho com `-I` (⊃ `-E`, que ignora env vars).
  Fix: `-s` + scrub explícito de `PYTHON*` herdado (isolamento N.1.2 preservado). Prova: `hash('abc')`
  estável entre processos nos 3 envs; contraprova com `-I` variava.
- **Fix 2 — `tree_sha256` selava ~66 `.pyc` gitignorados** ⇒ content-hash irreprodutível num checkout
  limpo (a VM) e lock "envelhecendo" a cada import. Agora exclui `__pycache__`/`*.pyc`; `repos.lock`
  re-lacrado INTEIRO (5 árvores) — o hash novo do `b5_desdeo` (`e73f89e1…`) bate BIT-A-BIT com o
  recomputo independente do verificador adversarial. Fecha o pedido A.1.6 do handoff R3-b5.
- **Fix 3 — RuntimeWarning do `final_eval` na `geracao=NULL`** (repasse c311 §2.5): sentinela −1.

**Achado LATENTE (alta) no c311 — fix obrigatório na Fase B (dono = a sessão):**
`c311_tgprmo.py:657-664` passa `nd_pos_real` calculado no float64 CRU — o anti-padrão que a docstring
do `write_final` proíbe e que o b5 mediu (b5m/ZDT1: 20≠19). Os 3 pilotos passaram só por ausência de
empate na borda. Fix = OMITIR `nd_pos_real` (o `write_final` calcula na vista float32) + contar o ND
do manifesto na mesma vista + re-rodar pilotos e gates. Instrução cravada no comando da Fase B.

**Achado de REDAÇÃO (dados honestos, sem re-run):** o sigma_dict do b5 diz "surrogate idêntico
[b5r/b5m] — só a seleção difere"; os μ da sonda DIFEREM (GPR `n_restarts=9` consome o RNG global,
semeado por alg_id 17≠18 ⇒ treinos independentes). Leitura correta: **mesma ESPECIFICAÇÃO, treino
independente por config**. O piso-off deve redigir assim. Observação p/ o D97: o GP do obj-2 de
b5m/DTLZ2 degenera (μ≈0, corr 0,006) — é o mecanismo do "colapso de canto" observado.

**Comportamento (insumo do lote D97; semente 0):** b5r **7** (progride sem colapso; convergência
parcial: ZDT1 dist 0,55 à frente analítica) · b5m **5** (colapso de canto em DTLZ2 nd=6/105; ZDT1
estaciona longe, dist 1,52) · c311 **7,5** (ZDT1 dist **0,0012** — o MELHOR offline até aqui; fraco
no MMF1 de dataset 61 pts). Cross-checks fortes: X da sonda BIT-IDÊNTICOS entre b5r/b5m/c311 e o
artefato canônico; os 2 blocos de sonda do c311 bit-idênticos entre si (modelo fixo na fase final);
⑦ ≡ última geração da ③ nos 6 runs b5 (ND recomputado bate EXATO).

**EM ABERTO p/ o autor (levantados pelos repasses + auditoria; recomendações da torre no chat):**
(1) D97 modo 7: `Prob_APD_select_v3` (média-MC declarada) vs `v1` "original"; (2) ratificar pins do
env_b5 (pandas 1.3.5 ✔cravado · pymoo · plotly · graphviz · pygmo=STUB); (3) ratificar o fix pyDOE
(gancho semeado, b5+c311) vs re-pin do pyDOE antigo; (4) semeadura por convenção D62 (b5 usos 1/2;
c311 uso 0) vs literal do cartão; (5) ④ granularidade (b5 1 linha; c311 1/retreino); (6) carimbo
local `geracao=NULL` como padrão da família offline vs fix central no `emit_sonda_block`;
(7) `uso_id` do c311 = `_default`/0.

---

## PARTE A16 — DI-28: as 7 ratificações do autor pós-paralelo, APLICADAS (2026-07-23)

O autor ratificou EM BLOCO as 7 recomendações da torre (PARTE A15, "EM ABERTO"). Efeitos:
1. **D97 modo 7 (b5r): `Prob_APD_select_v3` É a variante do estudo.** A aproximação média-MC
   (declarada no sigma_dict) fica; `v1` não será usada. Vira caveat de análise na dissertação
   (mesmo padrão do caveat c217/δ=0,8). Nota de comportamento b5r mantida (7).
2. **Pins do env_b5 RATIFICADOS:** pandas 1.3.5 · pymoo 0.6.1.2 (+shim `typing.Literal` py3.7) ·
   plotly 4.14.3 · graphviz · **pygmo permanece STUB** (nunca instanciado pelos modes 7/72/12;
   NÃO instalar). PROVISIONAMENTO §2 + env_b5.txt + lock já refletem (sessão b5); nada a mudar.
3. **pyDOE: o GANCHO runner-local é DEFINITIVO** (b5 + c311 + futuros da família desdeo). SEM
   re-pin do pyDOE antigo. Semântica ratificada: LHS via RandomState global semeado = réplica
   do pyDOE clássico, reprodutível da semente. A pendência §2.2 do repasse c311 está FECHADA —
   a Fase B NÃO materializa patch nem mexe em env (instrução no comando de Fase B). O piso-off
   HERDA o gancho do molde b5 (obrigatório).
4. **Semeadura por convenção D62 RATIFICADA como implementada:** b5 usos 1/2 (random/numpy
   derivados) · c311 uso 0 (mesmo s nos 2 RNGs) — ambas válidas e documentadas por config;
   o literal do cartão (`np.random.seed(s)` cru) NÃO é exigido.
5. **④ RATIFICADA:** b5 = 1 linha (motor caixa-preta); c311 = 1 linha/retreino de construção
   (C311-09). Satisfaz a §17.6 ("por geração/retreino") para os dois.
6. **`geracao=NULL` da sonda offline: o carimbo LOCAL pós-`emit_sonda_block` é o padrão
   CANÔNICO da família offline** (precedente c149→b5→c311; o piso-off herda). Fix central no
   `emit_sonda_block` = opcional, fila do M7 (não bloqueia nada).
7. **`uso_id` do c311 = `_default`/0 RATIFICADO** (sem RNG concorrente do harness). seeds.json
   INALTERADO de propósito (o `_default` cobre; não se edita artefato consumido com sessões
   em voo).

Nenhuma mudança de CÓDIGO decorre das 7 (tudo já implementado como ratificado). Mudanças de
DOC: esta PARTE + PROVISIONAMENTO (pyDOE "ratificado") + dossiê (notas b5r/b5m/c311 + decisão
modo-7) + PROGRESSO/ORQUESTRACAO/memória. SPEC/bundles: sync adiado (RI-12 — sessões em voo).
Impacto nos prompts em voo: 1 cláusula da Fase B do c311 atualizada (gancho lhs DEFINITIVO,
pendência fechada) + 1 linha informativa no prompt do piso-off (não re-levantar o já decidido).

---

## PARTE A17 — DI-29: validação-torre do FECHAMENTO 21/21 (R3-piso-off + c311-Fase-B) (2026-07-23)

**O MARCO: os 21/21 configs do estudo estão IMPLEMENTADOS e VALIDADOS.** R3-piso-off fechou
(commits `35ac50c`/`34b2a49`/`8256dfa`/`a92545f`) logo após a Fase B do c311 (`fb4fc30`/`0a6fe8e`/
`74281a0`) — o segundo paralelismo coreografado, de novo sem conflito (interseção de commits das
duas sessões = APENAS os 2 compartilhados autorizados do wiring, tocados EM SÉRIE).

**Validação da torre (a maior varredura até aqui):** suíte **321 OK** · preflight 0 ·
não-perturbação **53/53** · **accept 15/15** (4 cartões offline ×3 problemas + 3 online de
regressão) · **auditar+final_eval 24/24** (4 algs offline ×3) · workflow de 8 agentes (5 auditores
+ 3 verificação adversarial; notas 8,5–9,5) + 1 auditor dedicado ao código da Fase B do c311
(8,5/10 — "fix impecável, wiring exemplar"). **ZERO achado confirmado em média+** — os 3 suspeitos
foram refutados a baixa com verificação independente.

**Fatos fortes provados nos dados:** X da sonda BIT-IDÊNTICO entre piso, b5m e o artefato canônico;
⑦ ≡ última geração da ③ nos 3 pilotos do piso; ND recomputado na vista float32 bate EXATO no piso
(8/53/29) E no c311 pós-fix (10/77/50 — o fix nd_pos_real é ENFORÇADO pelo final_eval, não só
afirmado); os 2 blocos de sonda do c311 seguem bit-idênticos entre si pós-re-run; μ do piso vs b5m:
corr ≈1,0 onde os dois aprendem (mesma especificação) e byte-identidade sempre False (treino
independente — DI-28 confirmada no dado).

**A ABLAÇÃO D77 FUNCIONA (o resultado científico do marco):** piso μ-only vs b5m probabilístico nos
mesmos datasets — ZDT1: piso dist 0,179 à frente vs b5m 1,52 (**a maquinaria probabilística
ATRAPALHA ~8,5×**); DTLZ2: piso ESPALHA (nd 53/105) onde o b5m COLAPSA (6/105) — **a seleção
probabilística CAUSA o colapso**; MMF1: o sinal INVERTE (b5m tem mais diversidade ND, 21 vs 8) —
contraste não-monotônico e cientificamente rico. Turnover: piso troca ~8,5%/ger (conservador,
gerações estagnadas) vs b5m ~98%/ger (hiperativo guiado por σ). **Nota de comportamento
moead_media = 9,0** (ablação de manual; régua APROVADA).

**Fix da torre nesta rodada (commit `c740753`):** `check_r3_c311` endurecido (contador CONTÍGUO
1..N + presença de AMBAS as fases — antes só aferia min==1; achado de 2 auditores independentes,
mitigado por o runner ser correto por construção) + guarda de ③-vazia nas mensagens dos 3 checks
offline (crash `min([])` herdado do molde). Re-validado: accept 12/12 offline VERDE + suíte 321 OK.

**Correções de processo pegas PELA SESSÃO do piso (registro de mérito):** a suíte pegou a regressão
do teste de roteamento (cobaia venv-only esgotada com o 4º dispatch ligado → reescrito para provar
o roteamento por FileNotFoundError no spawn — solução verificada pela torre, robusta); a revisão
adversarial própria da sessão pegou o over-claim do sigma_dict (F1) e a falta da guarda DI-13.10
no teste da ④ (F2). E a resolução σ-NULL por precedência de documentos (DI-16.1 sobre o prompt) foi
exemplar.

**EM ABERTO p/ o autor (DI-30, a ratificar):**
1. **B2 — `modelo_hp` do piso:** NULL (como implementado, molde b5/D-08) vs gravar os HP ajustados
   do kernel. Recomendação da torre: **manter NULL** (gravar no piso e não no b5m criaria assimetria
   espúria na ablação).
2. **B3 — linha do ⑥/CONTRATO §6.1 p/ o moead_media:** "b5" (como implementado — ⑥ estruturalmente
   idêntico ao b5m, o par de ablação) vs "pisos" (ideal/nadir por geração + vetores no header).
   Recomendação da torre: **manter "b5"** + nota de clarificação na §6.1 no próximo doc-sync.
3. **D97-b5m/DTLZ2 (o item substantivo):** o GP do obj-2 do b5m/DTLZ2 é DEGENERADO (μ≈0 constante,
   corr 0,006 com o f real de std 0,588) enquanto o piso, com a MESMA especificação e MESMOS dados,
   ajusta corr 0,992 — sensibilidade à semente do treino único (n_restarts consome o RNG global,
   alg_id 18≠21). Dado HONESTO e determinístico; quebra o contraste da ablação NESSE problema.
   Recomendação da torre: **aceitar como está** (achado científico legítimo; protocolo de sementes
   é fixo) e documentar como caveat no D97/dissertação — decisão final é do autor no lote D97.
4. Nota informativa: cartão/bundle do piso com header "N interno = 100" STALE (conflita DI-16.4;
   o runner faz o certo) — corrige no doc-sync SPEC→bundles, agora destravado (nenhuma sessão aberta).

---

## PARTE A18 — DI-30: o autor RATIFICOU as 3 decisões do fechamento 21/21 (2026-07-23)

O autor aprovou as 3 recomendações da torre (PARTE A17, "EM ABERTO DI-30"):
- **B2 — `modelo_hp` do piso = NULL (RATIFICADO).** Coerente com o molde b5 e o D-08 (HP fixos,
  treino único). Gravar HP no piso mas não no b5m criaria assimetria espúria na ablação. Sem
  mudança de código (já era NULL).
- **B3 — linha do ⑥/CONTRATO §6.1 do moead_media = "b5" (RATIFICADO).** O ⑥ do piso fica
  estruturalmente idêntico ao do b5m (o par de ablação). AÇÃO da torre no doc-sync: clarificar
  na §6.1 que o `moead_media`, embora seja "piso", segue a linha de logging "b5" (é um config
  surrogate da família b5). Sem mudança de código.
- **B1/σ-NULL** já estava fechado (confirmado pela torre); **D97-b5m/DTLZ2** — aceitar o GP
  degenerado do obj-2 como achado científico legítimo + caveat na dissertação (RATIFICADO como
  encaminhamento; o julgamento de fidelidade final continua no lote D97). Sem mudança de código
  (dado honesto e determinístico; protocolo de sementes é fixo).

**Nenhuma mudança de código decorre da DI-30** — as 3 eram "manter como implementado". Efeito:
esta PARTE + a nota §6.1 na fila do doc-sync + a atualização do DOSSIÊ (flag b5m/DTLZ2 → ratificado).
Uma auditoria EXAUSTIVA de fechamento (9 auditores + verificação adversarial, workflow
`fechamento-implementacao-21de21`) roda em paralelo para garantir que NENHUMA outra pendência
sobrou antes do M7 — os achados confirmados dela entram como DI-31.

---

## PARTE A19 — DI-31: AUDITORIA EXAUSTIVA DE FECHAMENTO (o inventário definitivo) (2026-07-23)

**Gatilho.** O autor pediu o fechamento DEFINITIVO: uma última validação exaustiva dos 21/22
configs + repo inteiro, caçando QUALQUER decisão/correção/melhoria/pendência antes das baterias.
Workflow `fechamento-implementacao-21de21`: **9 auditores Opus** (decisões consolidadas · 13 MATLAB ·
5 Python online · 4 Python offline · infra transversal · maquinaria de gates · artefatos · prontidão
M7/M8 · integridade de dados) + **verificação adversarial por achado** (32 verificações, **32/32
procedem, 0 refutadas** — auditores disciplinados). Notas de confiança por fatia: python-online 9 ·
dados-integridade 8,5 · python-offline 8,5 · artefatos 8 · matlab-r1 8 · gates 7 · decisões 7,5 ·
m7-m8-readiness 5,5. **Infra-core: "sem bug latente ou resíduo; 193 testes OK; fixes DI-26/27/29
coerentes".**

**VEREDITO CENTRAL: a implementação dos ALGORITMOS está 100% fechada.** Os 22 runners de config
(9 Python + 13 MATLAB) estão impecáveis — nenhum defeito de algoritmo, nenhuma fidelidade
auto-decidida. O que a auditoria achou de "aberto" **não é implementação de algoritmo**: são
(a) 4 defeitos no ESTRATO DE LANÇAMENTO/GATE que a torre já corrigiu, (b) cartões de build da
bateria (M7/M8), e (c) o julgamento D97 do autor.

### FECHADO nesta rodada pela torre (commit `c9c52f2`)
1. **🔴 Bug de bateria M9 — `experiments.py` rejeitava b5r/b5m/moead_media.** `KNOWN_ALGORITHMS`
   era literal com o token-fantasma `'b5'` (chaves reais = b5r/b5m) e SEM moead_media ⇒ o parse do
   CLI (`bad_alg`) REJEITAVA os 3 offline ⇒ a bateria M9 era irrodável. Agora DERIVADO de
   `_DISPATCH_LOADERS` (drift-proof) + `DEFAULT` coerente com exp=main (só online). Teste-guard
   `tests/test_roster_bateria.py` (4) trava a regressão.
2. **Roster de `experiments.m` sem os 4 pisos ONLINE** ⇒ a M8 os pularia em silêncio. Adicionados
   nsga2/nsga3/moead/smsemoa ao default.
3. **Endurecimento de gate portado (DI-29 só cobrira o c311):** contiguidade `geracao` 1..N nos
   gêmeos `check_r3_b5` e `check_r3_piso_off` (antes min-só ⇒ buraco de geração passava VERDE);
   μ_*/σ_* conferidos em TODA a ③-busca no b5/c311/piso (antes só `idx_b[0]` = cobertura ilusória
   na dimensão-linha); guard `default='∅'` nos min/max dos 3 checks online (c149/e81/c122) contra
   crash com fe_treino_max todo-nulo.
4. **Órfão removido:** `data/experiments/off/c122` (failed stub pré-c122, config fora do grid).
Re-validado: accept **12/12 offline VERDE**, suíte **325 OK** (+4), preflight exit 0.

### CONFIRMADO já-fechado (a auditoria rastreou ~35 itens; a maioria estava fechada)
As 21 decisões da DI-20 → ratificadas (DI-21) e aplicadas com teste; R-1/D-04, D-11 (round-robin
e74 k=6/3/12), T-2, T-8 (④ e103), DEF-C4, DEF-N4 (c149 FICA), kernel-e81, desempate-c149, B34,
c262 DI-03/04/05, c154 DI-11, c122 DI-21.4, c149 DI-23/25, e81 DI-24/25, piso B1/B2/B3 (DI-30),
b5r modo-7 v3 (DI-28), c311 D1-D3 (DI-28), b5m/DTLZ2 (DI-30). Os 4 "blockers de código" da M8
existem e estão certos: D-06 repasse data_root, D-03/D-12 is_run_done bucket-aware + ⑦ offline,
D-16 fused-kernel off. repos.lock re-lacrado sem .pyc (DI-27) bate byte-a-byte.

### RESTA — CARTÕES DE BUILD DA BATERIA (torre; NÃO é implementação de algoritmo)
Estes são o M7 (portão) e o provisionamento M8 — sempre foram desta fase, não da implementação:
- **T1** Driver de portão `scripts/portao.py` (roteia accept+auditar+final_eval+naoperturbacao por
  run sobre o grid de ~19.950) — hoje o `experiments.py` grava mas não gateia. Pré-M8.
- **T2** `enable_bucket` no despachante (flag CLI + repasse ao `_adapter.run`; D-06 itens 4/6) — a VM
  efêmera gravaria só local sem isso. Pré-M8 (validar com credenciais reais = provisionamento).
- **T3** Driver de lote da ⑦ offline (varre os runs offline → `final_eval --check`) + `is_run_done_m`
  MATLAB cobrar a camada final do e103. Pré-M9.
- **T4** **doc-sync SPEC→bundles** (RI-12 destravado): header "N interno=100" stale do cartão do piso
  (→ lattice 50/105, D65 v5.2.1); clarificar §6.1 que moead_media segue linha "b5" (DI-30.B3);
  comentário `e74_sonda.m:33` "sujeita a ratificação" → RATIFICADA DI-21.1; reconciliar D88 "21" vs
  §1.5 "22 configs"; CONTRATO §7 origem_linha → par (origem_geracao, origem_linha); texto stale
  `abertas_torre`/`modelo_hp` nos sigma_dict de c311/piso (propaga a todo manifesto). Rodar
  `gen_bundles.py` + auditar o diff. **É a próxima ação da torre.**
- **T5** Portar o probe mecânico de RNG do R3-00 ao gate R2-00 (D-17); teste e2e de aborto/resume;
  smoke de sonda no ZDT1 de c238/e7/c262 (fatias que nunca rodaram sonda@D=30). Cartão M7.
- **T6** `sobol_batch` runner + qmaximin + plumbing q=10 + alg_id no seeds.json — cartão M10
  (sub-estudo batch; a M8/M9 principal q=1 NÃO depende).

### RESTA — DECISÕES DO AUTOR (a torre recomenda; só você ratifica)
- **A1 🔑 Lote D97 de FIDELIDADE (os 22 configs)** — a decisão central e o item 1 da AGENDA;
  pré-M7 (para não re-rodar). Insumos prontos no `DOSSIE_FIDELIDADE_R1.md`. Torre recomenda:
  fechar ANTES do M8 (segurança contra re-execução); sinalizações viram D81.
- **A2** sub-varN: N=20 dos pisos online é DEFINITIVO ou roda a varredura D65 {10,20,30,50}? Torre:
  N=20 definitivo (justificado §3.2), varredura como sub-estudo M11 opcional.
- **A3** D-2/D-3: teto/orçamento por config e se o ZDT1 do c154 (~121 dias-core) entra na bateria.
  Decidir no M7 com os walls medidos.
- **A4** Provisionamento da VM/bucket (D80): construir a VM Linux (sem toolchain C++, D-16c) dos
  locks + validar gcs com credenciais reais. É o pré-requisito físico do M7-lado-VM e do M8.
- **A5** Política de `teto_s` do c311 nas baterias (O(n³) do GPy em n grande sob Rosetta).
- **A6** Escopo do experimento `batch` (sobol_batch, q=10) no M8/M10.
- **A7** Timing do dossiê itens 3/4/5 (auditoria 9→10, disparo forçado de guardas, smoke semente 42):
  torre entrega o insumo; autor decide rodar antes do M8 ou em paralelo às baterias.

Achados baixa (doc-drift cosmético, e2e-test gaps, σ≈0 degenerado do obj-0 linear do ZDT1 =
robustez da CAMADA DE ANÁLISE não dos dados, e103 smoke sob `main/`) consolidados no dossiê/T4/T5.

---

## PARTE A20 — DI-32: A1-A7 RATIFICADAS + cartões de build T1-T5 EXECUTADOS (2026-07-23)

**O autor ratificou EM BLOCO as recomendações A1-A7 da PARTE A19** e mandou executar T4 + T1-T3/T5:
- **A1 (lote D97)**: será executado como a VALIDAÇÃO DEFINITIVA DE FIDELIDADE sobre a varredura
  semente-42 completa (estratégia do autor, refinada pela torre no chat de 2026-07-23 — 3 máquinas,
  todos os configs × 25 problemas, seed 42; o protocolo Fable de 3 classes vira o método oficial).
- **A2**: N=20 dos pisos online = DEFINITIVO; SUB-varN vira sub-estudo OPCIONAL do M11 (epígrafe
  ⚠ **RETIFICADO — VER PARTE A41 / T12.D2 (2026-07-31).** Esta decisão foi **superada** pela
  **DI-39** (2026-07-25), posterior e do mesmo autor: o N=20 é **PROVISÓRIO** e o **SUB-varN
  volta a ser pré-requisito do M8**. O texto abaixo permanece como registro histórico do que se
  decidiu em 2026-07-23; ele **não** é o estado vinculante.
  do bundle atualizada). **A3/A5**: teto/orçamento por config (incl. c154/ZDT1 e teto_s do c311)
  decididos no M7 com os walls da varredura-42. **A6**: batch/sobol_batch = escopo M10.
  **A7**: dossiê itens 3/4/5 ANTES do M8 — o item 5 (smoke semente 42) é SUBSUMIDO pela
  varredura-42 em largura total.
- **A4**: provisionamento VM/bucket = próxima ação física do autor (receitas prontas,
  PROVISIONAMENTO.md; D-16c sem toolchain C++).

**T4 — doc-sync SPEC→bundles EXECUTADO (commit `e18f968`):** contagem D88 21→22 nos sítios
normativos · nota DI-28 na receita L.17 (D62 canônica + drift pyDOE + gancho DEFINITIVO +
PYTHONHASHSEED) · epígrafes do gen_bundles corrigidas ("N interno=100" SUPERADA → lattice 50/105;
varN opcional) · CONTRATO §6.1 (moead_media = linha "b5", DI-30.B3; modelo_hp NULL B2) e §7
(origem_linha = PAR com origem_geracao) · e74_sonda.m "sujeita a ratificação"→RATIFICADA ·
sigma_dict de c311/piso: textos "em aberto"→RATIFICADO (chaves preservadas). Bundles regenerados
(44 arquivos; diff auditado = só os 8 esperados). Suíte 325 OK · preflight 0.

**T1+T3 — `scripts/portao.py` (commit `1ec0624`): o DRIVER DE PORTÃO das baterias.** Roteia por
run: accept (branch R3 dedicado / catch-all R1-R2) + auditar + final_eval --check (offline);
modo `--varredura` = varre todo o data/ e é TAMBÉM o driver de LOTE da ⑦ offline. Provado ao
vivo: varredura exp=off 12 runs/36 gates VERDE; catch-all MATLAB (c217) VERDE. `is_run_done_m`
do MATLAB agora COBRA a ⑦ do e103. `tests/test_portao.py` trava a cobertura de todos os configs.
**T2** — `--enable-bucket` de ponta a ponta no experiments.py (os 9 runners já aceitavam).
**T5** — probe MECÂNICO de RNG (D-17) no gate R2-00 ao lado do auto-relato; provado VERDE no
gate real. Suíte final: **328 OK**. (T5-resto: e2e de aborto + smokes ZDT1 c238/e7/c262 =
executados NA varredura-42/M7, onde são células reais.)

---

## PARTE A21 — DI-33: batch q=10 ANTECIPADO p/ a rodada-42 + o achado "fio do sweep" (2026-07-23)

**Decisão do autor:** o sub-estudo batch q=10 (c149/c262/e81/c154 + sobol_batch × 5 problemas)
ENTRA na rodada-42 de fidelidade (era M10). Rodada-42 passa a **665 células** (main 425 + off 125
+ sweep 90 + batch 25). main+off disparam imediatamente; sweep e batch dependem de T7/T6.

### T6 — o que falta p/ o batch q=10 (cartão de implementação; era M10)
O que JÁ existe: `q` no manifesto/`write_run_outputs` (DI-23) · runs_matrix com q=10 · e81 com o
lote NATIVO fiado (`q` ponta-a-ponta até `acq.qpots(q=)`) · naming `exp=batch`. O que FALTA:
1. **Orçamento batch**: `maxFE_batch = 11D−1 + K·q` (K=200 ⇒ +2000 infills, D66) — hoje NADA
   computa orçamento por exp; os runners assumem 31D−1.
2. **Fio do q nos 4 online**: c262 (`optimize_acqf(q=10, sequential=True)` — hoje q=1 hardcoded) ·
   c154 (idem, lote nativo JES) · c149 (laço HVI-greedy iterado q vezes, D42) · e81 (SÓ o
   fallback qmaximin p/ |ND|<q — DI-25 #3, definido e não-implementado; o resto está fiado).
3. **Runner `sobol_batch`** (o piso do batch: Sobol scrambled/Owen por semente, lotes de q=10 —
   trivial sobre o harness) + dispatch + alg_id no seeds.json (novo id; ratificar).
4. **Gates batch-aware**: o catch-all/check_fe espera FE=31D−1 — reprovaria um run batch correto;
   auditar/portão idem. Estender a expectativa de FE por exp.
**Instrumentação: NENHUM retrofit novo necessário** — as 7 camadas/sonda/⑥/⑤ são agnósticas de
config e JÁ são q-aware (③ multi-candidato é o padrão existente do c262; a sonda é a mesma régua;
④ por iteração; manifesto grava q). Diagnóstico do batch = mesma qualidade do main por construção.
Únicos acréscimos de log: eventos de lote no ⑥ (ex.: `lote_completado_por=qmaximin`), já previstos
na DI-25 #3.

### T7 — o achado "fio do sweep" (descoberto pela torre ANTES de queimar células)
O plumbing de BAIXO existe e está pronto: datasets dos tiers no disco (`ds_*_{tier}_{dist}`),
`load_dataset`/`load_offline_budget` aceitam tier/dist (e o orçamento vem GRÁTIS do desenho "o
orçamento É o dataset": medium=2000/big=50k), tokens no naming, ramo big do c311
(`_build_surrogates`, B15.4) implementado. **O elo que FALTA é fino: NINGUÉM deriva (tier, dist)
do token `exp=sweep-<tier>-<dist>`** — os 3 runners offline chamam `load_offline_budget(problema,
semente)` SEM tier/dist (b5_prob:292, c311:459, piso:298) ⇒ um run de sweep hoje rodaria
SILENCIOSAMENTE sobre o dataset small e gravaria sob o nome do sweep. Escopo do T7:
(1) helper `naming.parse_sweep(exp)→(tier,dist)`; (2) os 3 runners derivam do exp e repassam
(+ c311 roteia big→`_build_surrogates`); (3) e103/MATLAB: `experiment.m` carrega a variante do
tier (lado MATLAB do mesmo fio); (4) gates: expectativa de FE/n por tier (check_fe/auditar);
(5) smoke 1 célula/token (6 tokens) ANTES das 90 células.

---

## PARTE A22 — DI-34: VALIDAÇÃO FINAL da torre sobre T7/T6 + fila do congelamento (2026-07-24)

**Contexto.** A sessão T7/T6 fechou (12 commits, `9fcde9f..11845ce`): T7 = o fio do sweep nos 2
stacks; T6 = batch q=10 (orçamento D66, lote nativo nos 4 online, `sobol_batch`, gates). Em
paralelo o F1 provisionou Mac A + VM-1 + VM-2 (100% até o 🔒; 2 divergências D80 resolvidas por
veredito; handoff v4). Esta PARTE registra a VALIDAÇÃO FINAL da torre — o portão do congelamento.

**Validação:** forense de git (12 commits, 28 arquivos, faixas limpas) · suíte 369 OK · preflight 0
· **portão 78 runs/180 gates** (só os 5 stale pré-retrofit conhecidos) · **prova de regressão spot
independente da torre: b5r/MMF1 re-rodado ⇒ ⑦ e ③ BIT-IDÊNTICAS** ao validado · workflow de 10
agentes (5 auditores + verificação adversarial; notas 8/5/9/8/9). A sessão T7/T6 também passou por
auto-auditoria adversarial e corrigiu o próprio relatório (contagem de commits, sobre-afirmações).

**5 achados CONFIRMADOS — TODOS corrigidos pela torre (commit `c2a522d`):**
1. **🔴 CRÍTICO — o fio do q:** o despachante não fiava `q` ao runner ⇒ célula batch da BATERIA
   rodava q=1 SILENCIOSO (FE=11D−1+200; gates passavam pois liam o q do próprio manifesto).
   Reproduzido ao vivo pela auditoria. Fix: `Q_BATCH=10` canônico (budget.py, D66) + fio no
   `_run_one` + teste-guarda + **prova e2e** (sobol_batch via despachante ⇒ q=10, FE=2109).
   É o 3º bug da MESMA família da camada de lançamento (roster DI-31, transporte E1/T7) — a
   lição estrutural: runners perfeitos não salvam um lançador que não os chama direito.
2. **ALTO — c149 batch:** hard-stop no meio do lote deixava a ④ com 3 tempos NULL (gate reprova).
   Rito do cache-cap espelhado (flag+break+fecha parciais+re-levanta).
3. **MÉDIO — e81 straddle:** geração parcial cortada pelo orçamento perdia ③/② (pontos na ① sem
   paisagem). Grava a parcial + re-levanta após o ⑥.
4. **MÉDIO — e103/MATLAB:** `man.tier/dist` do topo vinham do SIDECAR (off ficava "small/lhs",
   divergindo do grid e do stack Python). Agora = a CÉLULA do token (null fora do sweep);
   proveniência preservada em `man.dataset`. Provado ao vivo (off/e103/MMF1/0 novo: VERDE).
5. **MÉDIO — gate:** binding por HASH do ① à célula offline no `auditar` (cp_init x/f_hash vs
   sidecar do `dataset_variant(exp)`) — fecha a assimetria do e103 no catch-all (só contava linhas).

**Fila do congelamento executada (commit `b3675ef`):** datasets sweep-42 commitados (P1, 24
arquivos, incl. MMF16_20) · `tree_sha256` exclui `{.DS_Store,.asv,.orig}` + repos.lock RE-LACRADO
(hashes agora reproduzíveis Mac×VM — achado F1) + 3 `.asv` fora do índice + `.gitignore` ·
`torch==2.11.0` na INTENÇÃO (Q4/D80#1) · PROVISIONAMENTO §2/§3 = método canônico dos LOCKS
(b5 `--no-deps` + critério das 2 exceções desdeo; c311 2-etapas + pip check limpo) · RUNBOOK §6-bis
(correções de campo do F1, incl. nota parfor/ponte do MATLAB). Órfãos removidos (off/b5
token-fantasma; batch/c262 probe-fantasma da auditoria).

**EM ABERTO p/ o autor (DI-35, a decisão que destrava o push/tag):** ver os REPASSEs T7/T6 —
(1) 🔑 custo da aquisição batch dos GP-BO (c154 ~100h medido: knob batch-only 2D/50D sugerido;
c262 ~56h: pede sonda de tuning); (2) B15.4 = cartão novo do PISO-big (a SPEC venceu o cartão —
leitura confirmada pela auditoria); (3) escopo do MMF1 no sweep (paredes D=2 em mvns e
medium/big; MMF16_20 D=20 como substituto — controle small-lhs a decidir) e no batch;
(4) piso no sweep (SPEC × runs_matrix — regen da matriz); (5) política de teto (A3/A5; b5/piso
sem teto_s; walls medidos nos REPASSEs). Itens de execução pós-decisão: regen runs_matrix +
~441 datasets de sweep (30 sementes) + cartão do piso-big + sonda de tuning do c262.

---

## PARTE A23 — DI-35: decisões do autor sobre os repasses T7/T6 (2026-07-24, PARCIAL)

O autor decidiu 4 dos 5 itens (o item 1, custo batch dos GP-BO, aguarda a explicação didática
da torre — será registrado em adendo):
- **DI-35.2 — B15.4/piso-big:** o autor delegou ("o que achar mais adequado") e a torre CRAVA a
  leitura da SPEC (confirmada pela auditoria): **piso-big = instância NOVA** (treed-GP-média via
  `build_surrogates`, env_c311, a ablação do c311 no tier big) ⇒ **cartão T8**.
- **DI-35.3 — sweep TODO em MMF16_20:** MMF1 SAI de TODOS os tokens do sweep; **MMF16_20 (D=20,
  família MMF) entra em todos** — padronização total. ⚠ Registro honesto da torre: isso remove o
  "controle D=2" que a §11.5 designava — aceito porque o controle era inexecutável em 5 dos 6
  tokens (paredes de D=2: duplicata-clip no mvns; densidade GP no medium/big); um controle que só
  existe em 1 token não controla nada. Doc-sync da §11.5 no próximo lote. (Extensão da troca ao
  BATCH: recomendada pela torre pelo mesmo motivo de densidade — aguarda 1 palavra do autor.)
- **DI-35.4 — piso no sweep: CONFIRMADO** (a SPEC §10/D38 vence o runs_matrix): moead_media
  (small/medium, env_b5) + piso-big (big, env_c311/T8) entram no grid do sweep ⇒ regen da matriz.
- **DI-35.5 — TETO UNIVERSAL 12h:** nos experimentos DEFINITIVOS, teto_s=43200 para TODOS os
  runs dos 22 configs (principais e complementares). Consequências registradas: (a) o despachante
  Python ganha default `--teto-s 43200`; b5/piso ganham o fio do teto (gap conhecido) — junto do
  T8; (b) stack MATLAB: sem plumbing de teto (pior wall observado = 33,6m — o teto de 12h é
  vácuo lá; wiring MATLAB só se o autor exigir); (c) ⚠ células que o teto de 12h VAI cortar na
  receita cheia: c154/DTLZ2 (14,6h medido, s0) e c154/ZDT1 (>8h) ⇒ virarão `failed/teto_wall`
  honestos (aborto=dado, D61) — interage com a decisão 1.
Execução (torre, após a decisão 1 fechar, num lote único): regen runs_matrix + datasets do sweep
(MMF16_20/semente-42 primeiro; 30 sementes no M8) + teto default + cartões T8/T9 + doc-sync.

**ADENDO (mesmo dia): a decisão 1 FECHOU e o lote FOI EXECUTADO (commit `e78bfdf`).**
- **DI-35.1 — custo batch dos GP-BO: alvo ~10h/run** (o ponto ótimo do autor no tradeoff
  tempo×qualidade). O knob é CALIBRADO POR MEDIÇÃO (cartão T9): probes curtos → projeção com o
  crescimento do custo em n → valores que projetem ~10h → ratificação com números. Vale p/ c154
  E c262, batch-only (o principal q=1 fica intocado, com prova de regressão bit-a-bit).
- **DI-35.3b — batch também em MMF16_20** (aprovado "ok": mesma parede de densidade D=2).
- **Executado:** runs_matrix 19.950→20.850 (690 trocas MMF1→MMF16_20 em sweep+batch; +900 do
  piso no sweep) · treed_media=23 fiado (seeds/envs/OFFLINE_*/dispatch-comentado/portão/guards)
  · teto universal 12h (default --teto-s 43200 + fio no b5/piso com aborto limpo) · 18 datasets
  s42 novos · SPEC §11.5/§V-B/D66 anotadas + 44 bundles regenerados · suíte 369 OK · portão
  78/180 (só os 5 stale). Cartões T8 (piso-big) e T9 (calibração ~10h) prontos p/ disparo
  PARALELO (faixas disjuntas — análise no chat da torre).

---

## PARTE A24 — DI-36: validação final T8/T9 (o último portão) + fix do projetor (2026-07-24)

**Os 2 últimos cartões fecharam EM PARALELO sem um arranhão** (4º paralelismo limpo: interseção de
commits VAZIA; T8 tocou `experiments.py`/`auditar.py` só nos 2 one-liners AUTORIZADOS — a fiação do
treed_media que a torre tinha deixado incompleta no lote DI-35, registro de mérito da sessão que a
detectou e escalou antes de tocar). **T8**: `treed_media` (config 23/23) validado nos 5/5 problemas
(smokes 6-14s! — o piso-big é ~100× mais barato que o c311-big), notas da auditoria 9/9,5.
**T9**: calibração POR MEDIÇÃO — **c262 batch = ~2,2h na receita CHEIA (sem knob!)**; **c154 não
fecha ~10h com nenhum knob defensável** (FLOOR ≥30h; aquisição JES-LB ~n^1,6); knob shipado
per-D (1D restarts/50D raw); prova de regressão q=1 bit-a-bit nos 2. Notas 9/7,5.

**Achado ALTA da auditoria da torre — CORRIGIDO (commits `acfac4b`+`913bd00`):** o
`_WallClockProjector` (c262, importado pelo c154) somava 1 termo POR FE em vez de POR ITERAÇÃO —
em q=10 superestimava ~10× e **abortaria espuriamente as 5 células batch do c262** sob o teto 12h.
Fix: passo inferido dos samples (mediana dos deltas; q=1 fica BIT-IGUAL, com teste-guarda).
**BÔNUS — causa-raiz do "~56h" do T6 CORRIGIDA:** era o artefato do projetor não-batch-aware, NÃO
contenção/swap como o T9 narrou (a projeção real do c262 sempre foi ~2,2h). Também preservado:
`scripts/regressao_q1.py` (a prova do T9 vivia só no scratchpad) + envs.json cosmético.

**Gates finais:** suíte **391 OK** · preflight 0 · **portão 84 runs/198 gates** (só os 5 stale) ·
árvore limpa. **A implementação da rodada-42 está TOTAL: 23/23 configs, 4 tipos de experimento,
todos com smoke verde.**

**DI-37 NA MESA DO AUTOR (o último lote antes do push/tag):** (1) c154 batch: truncado no teto
[rec] vs fora do roster; (2) ratificar c262 batch = receita cheia ~2,2h; (3) ratificar knob per-D
do c154; (4) ratificar caveat D97 do confounder; (5) T8-⑦ no teto = rito-piso [rec; house norm e o
gate exige ⑦]; (6) naoperturbacao do treed_media = teste-only [rec; doutrina máquina-com-histórico];
(7) confirmar espelhamento RVEA-final + modelo_flag do T8. Tensão registrada p/ M8 (não decide
agora): c311 sob teto NA CONSTRUÇÃO omitiria a ⑦ e o gate reprovaria — inalcançável na rodada-42.

---

## PARTE A25 — DI-37: RATIFICAÇÃO EM BLOCO (autor, 2026-07-25) + doc-sync final do congelamento

**O autor ratificou os 7 itens da mesa DI-37 seguindo as recomendações da torre — o ÚLTIMO lote
decisório antes do push/tag.** Nenhum item exigiu mudança de código (knob per-D, rito-piso e teto
universal já estavam shipados em T8/T9/DI-35); o lote é decisório+documental:

| # | Decisão ratificada | Efeito |
|---|---|---|
| DI-37.1 | **c154 batch TERMINA NO TETO 12h por desenho** (`failed/teto_wall`, ~it. 50–80/200; piso ≥30h medido — nenhum knob honesto fecha 10h) | curva parcial = dado; lente de prefixo §V-B.5; accept já pula FE-exato em aborto sancionado |
| DI-37.2 | **c262 batch = receita CHEIA, sem knob** (~2,2h medidos; o "56h" era o projetor, DI-36) | L.10 anotada |
| DI-37.3 | **c154 knob per-D BATCH-ONLY**: optimize_acqf restarts=1D/raw=50D (q=1 intacto 5D/1000D, regressão byte-idêntica) | L.11 + §V-B.4 + params.json |
| DI-37.4 | **Caveat D97**: contraste q=1×q=10 do c154 carrega 2 confounders (knob + truncamento) — declarar; contraste limpo = c262/e81 | §V-B.5 (vinculante p/ análise) |
| DI-37.5 | **T8: ⑦ no teto do treed_media = rito-piso** (⑦ parcial gravada; house norm — o gate exige ⑦) | comportamento shipado confirmado |
| DI-37.6 | **T8: não-perturbação do treed_media = teste-only/N/A** (doutrina máquina-com-histórico) | idem |
| DI-37.7 | **T8: confirmações** — seleção final RVEA espelha o c311 (10×100, mean); `modelo_flag` conforme | idem |

**Doc-sync executado (DEF-6):** SPEC §5.1 ganhou o bloco do **TETO UNIVERSAL 12h** (⟦DI-35.5/DI-37.1⟧ —
gap real: o teto nunca tinha sido anotado na SPEC) · §V-B.4 bloco ⟦DI-37⟧ (custo medido do batch) ·
§V-B.5 caveat ⟦DI-37.4⟧ · L.10/L.11 anotadas · `params.json` +3 chaves (c154.optimize_acqf/batch_q10,
c262.batch_q10; diff semântico auditado = só as 3) · **bundles regenerados** (diff auditado: só
01_regras_globais, alg_c154, alg_c262, batch_largebatch — exatamente os 4 esperados).

**Tensão registrada p/ M8 (não-decisão):** c311 sob teto NA FASE DE CONSTRUÇÃO omitiria a ⑦ e o
gate reprovaria — inalcançável na rodada-42 (build do c311 = segundos–minutos); reavaliar se o M8
introduzir tiers/problemas onde o build encoste no teto.

**Com a A25, a fila decisória do congelamento está VAZIA.** Estado: 23/23 configs · suíte verde ·
portão só-stale · docs sincronizados. Próximo ato = **push + tag `rodada-42-freeze` (AUTOR)** →
desbloqueio das 3 máquinas → disparo das ~695 células.

---

## PARTE A26 — Auditoria de PRONTIDÃO do congelamento (2026-07-25) + a DECISÃO DI-38

**Antes de declarar o repo pronto, a torre rodou a auditoria final de prontidão** (5 auditores
independentes read-only + refutação adversarial, 13 agentes): notas doc×código 6,5 · runbook×matrix
7 · spec×bundles 8,5 · pendências 9,5 · estado-repo 8,5. **7 achados confirmados (3 ALTA/4 MEDIA)
— os 3 ALTA eram do texto que a PRÓPRIA torre escreveu no doc-sync DI-37** (a SPEC prometia mais
do que o código faz). Registro de humildade: o auditor pegou o autor do doc-sync no mesmo dia.

**Correções DIRETAS aplicadas (todas de gate/metadado/doc — mandato da torre):**
1. **SPEC §5.1 reescrita para a VERDADE**: o teto 12h existe SÓ no despachante Python (o stack
   MATLAB NÃO tem teto — lacuna DECLARADA, aceita: pior célula MATLAB c238/ZDT1 ~3h55 ≪ 12h; rede
   = watchdog D60) e o RITO difere por família — standalone/pisos gravam camadas parciais (⑦ só no
   treed_media); **BoTorch (c262/c154) aborta por PROJEÇÃO ANTECIPADA (arma na 11ª iteração) SEM
   parquets** (anti-órfão D-07/DI-21; curva só no .jsonl §17.6).
2. **`check_fe` do accept ganhou o skip de aborto sancionado como FONTE ÚNICA** (antes só o cartão
   do e81 tinha; o gate genérico reprovaria exatamente as células que a DI-37.1 sanciona).
3. **Heading `## V-B.5` restaurado** (a edição DI-37 da torre o havia engolido — 5 referências
   penduradas) + caveat DI-37.4 anotado com a limitação da lente-de-prefixo.
4. **RUNBOOK**: +4 comandos do e103-sweep (20 células MATLAB estavam ÓRFÃS do bloco de disparo);
   semântica real do c154 sob teto (morre em ~min–1h por projeção, SEM parquets; NÃO re-disparar —
   `is_run_done` lê failed como não-pronto); §2.3/§3.3 corrigidos (doe/datasets RASTREADOS no git
   ~190 MB — o clone JÁ os leva; rsync = fallback).
5. **19.950→20.850** em CONTRATO_DE_DADOS/HANDOFF_MESTRE/PROGRESSO/claude_code_context/CLAUDE.md.
6. **Headers jsonl de c154/c262: `"q": int(q)`** (declaravam q=1 hard-coded mesmo em run batch;
   q=1 bit-inalterado).
7. Bundles regenerados. Suíte 391 OK · preflight 0. (1 achado REFUTADO pelo adversarial; 28 baixas
   registradas — destaques pré-existentes: env_c149_fallback sem lock; data/images 152 PNGs
   rastreados vs comentário do .gitignore; rótulos stale na ORQUESTRACAO.)

**🔴 DI-38 — NA MESA DO AUTOR (a única decisão que resta antes do push/tag):** a DI-37.1 foi
ratificada sob a premissa (da torre, ERRADA) de que o c154 truncaria no teto ~iteração 50–80
entregando curva parcial. O código real (BoTorch) aborta por projeção em ~minutos–1h **sem
produzir ①–⑦**. Células afetadas na rodada-42: c154 main/DTLZ2 (~14,6h), possivelmente
c154/ZDT1–WFG9, + as 5 c154-batch. Opções:
- **(a) Manter o comportamento atual** — aborto antecipado, custo ~zero, MAS essas células não
  entregam NENHUM dado de análise (nem parcial): furo no grid 25-problemas do c154 main e batch
  de facto sem c154.
- **(b) [RECOMENDAÇÃO DA TORRE] Cartão T10 — rito de truncamento BoTorch**: no aborto por teto,
  gravar as camadas parciais (write_run_outputs com status=failed) e, nas células sancionadas,
  critério elapsed-only (projeção vira warning) — entrega EXATAMENTE o que a DI-37.1 ratificou
  ("curva parcial é o dado"). Custo: 1 sessão curta + revalidação + ~12h/célula sancionada
  (~7 células ≈ 84h-core, paralelas ⇒ +0 no wall da rodada). T10 ANTES do push.
- **(c) Reduzir escopo**: c154 fora do batch + main sem as células >12h.

---

## PARTE A27 — DI-38 DECIDIDA = (a) · carve-out ⚪ nos gates · CONGELADO (2026-07-25)

**O autor decidiu a DI-38 = opção (a): manter o comportamento atual** (aborto por projeção,
sem camadas nas células c154 que estouram o teto) **e levar o T10 ao backlog** — com a doutrina
explícita: *"vamos rodar agora o que temos e ver o que sai; o que não estiver perfeito vira UM
refinamento final para a versão perfeita"*. A rodada-42 assume o papel adicional de COLHEITA de
imperfeições; o lote de refinamento pós-rodada as trata de uma vez.

**Execução da torre (para o (a) ser OPERÁVEL no F4):**
1. `portao.py`: run com `status=failed` + `motivo_parada ∈ {teto_wall, cache_cap}` vira
   **⚪ aborto-sancionado** — 1 linha informativa, sem rodar accept/auditar/final_eval (não há
   camadas a gatear por desenho) e SEM contar vermelho. `failed` comum (crash) segue gateando
   normal e acusando.
2. `accept.check_fe`: o skip de aborto sancionado moveu para ANTES do check de camada ① (no rito
   BoTorch a ① ausente é por desenho — antes o gate devolveria "camada ① ausente" = falso 🔴).
3. `tests/test_portao.py` +3 guards (⚪ sancionado; failed-comum gateia; check_fe skipa sem ①).
4. SPEC §5.1/§V-B.4/§V-B.5 anotadas ⟦DI-38(a)⟧ + bundles regen; RUNBOOK §7 (re-invocação sem
   c154 na lista).

**Expectativa OFICIAL da rodada-42 (para ninguém diagnosticar como falha):** ~6-7 células ⚪ —
c154 main/DTLZ2 (certa), c154 main/ZDT1-WFG9 (prováveis) e as 5 c154-batch; cada uma custa
~min-1h antes do aborto por projeção.

**BACKLOG DO REFINAMENTO PÓS-RODADA (consolidado; donos definidos na hora):** T10 rito de
truncamento BoTorch (se o autor quiser as curvas parciais do c154 em parquet) · teto de wall no
stack MATLAB (lacuna declarada §5.1; hoje inócua) · tensão ⑦×teto-na-construção do c311 (M8) ·
env_c149_fallback sem lock · data/images rastreado vs comentário do .gitignore · rótulos stale
da ORQUESTRACAO · headers/params.json §L.11 do knob (feito) · + TUDO que a execução das 695
células revelar.

**Com a A27, o congelamento está COMPLETO: zero decisões em aberto. Próximo ato = push + tag
`rodada-42-freeze` (AUTOR) → F2 desbloqueio das 3 máquinas → disparo.**

---

## PARTE A28 — Consolidação da validação final (12/32) + DI-39 (N dos pisos) + DI-40 (c154 fora do batch) (2026-07-25)

**Origem.** O workflow `wf_c451718a-b88` foi pausado com **12 de 32** finders completos. Os 12
relatórios foram lidos do `journal.jsonl` e consolidados **sem relançar nada** (custo zero).
Cobertura: `b1, b3, b4, e7, c217, c141, e74, c238, pisos_online, e103, c262, c154` — ou seja,
**100% do roster MATLAB da rodada-42**. Notas de 7 a 8,5; **113 achados** (10 ALTA, 45 MÉDIA,
58 BAIXA); todos os smokes verdes, FE exato em 100% dos casos, não-perturbação da sonda provada.

**Leitura da torre sobre os 10 ALTA — nenhum produz dado corrompido na semente 42:**

- **Três** (`b1`, `e7`, `c238`) descrevem células stale **de semente 0** que o `is_run_done`
  absorveria como prontas. Os auditores escreveram *"a RODADA-42 vai pular essas células"* —
  **incorreto**: a rodada-42 é semente **42**, e as células citadas são `..._0`. O risco é da
  **M8**, que inclui a semente 0. **Ação: re-run com `force` das células stale ANTES do M8.**
- **Dois** (`b3`/`adapt_delta_V` e `e74`/DI-07b) geram dado **incompleto ou pendente de
  julgamento**, não errado — e o julgamento D97 do e74 fica MELHOR com o dado da semente 42 na
  mão. Reclassificados como **decisão pré-M8**, não pré-rodada.
- **Um** (`pisos_online`/SUB-varN) é pré-registro ⇒ **DI-39 abaixo**.
- **Quatro** são de outras máquinas: `e103` (435 runs de sweep sem dataset — só nas outras 29
  sementes, problema do M8), `c262` (batch q=10 nunca completou um run ponta-a-ponta; único probe
  cheio OOM-killed em n=669 ⇒ risco de OOM com `--n-jobs 8` na VM-1) e `c154` ×2 — **este último
  CORRIGE UM NÚMERO OFICIAL DESTE REGISTRO**: a premissa *"~min-1h"* das linhas 1708/1756 foi
  simulada contra o ④ REAL de `main/c154/DTLZ2_0` e o trip por projeção só vem na iteração 158,
  após **~6,3 h** queimadas ⟦ERRATA T11 (2026-07-30): este número foi **superado 2×**. O "~min-1h" original foi corrigido para "~6,3 h" pela A28, e a F5 mediu na s42 o valor REAL: **0,87–2,99 h por célula, média 1,47 h** — o "6,3 h" é ~4× superestimado (a projeção arma na it 158 num run cuja iteração encarece). E, com a DI-43/44 + o T11-G5, o ponto ficou histórico: o aborto por projeção foi EXTINTO (a projeção virou `wall_projection_warning`) e o teto passa a truncar COM as camadas gravadas.⟧ (a projeção assume busca constante, enquanto a busca JES cresce
  ~n^1,6, e por isso dispara tarde). Erro de ~6× na expectativa publicada; ×30 sementes ≈ 190
  h-core só em DTLZ2 para **zero parquet**.

### DI-39 — N dos pisos na rodada-42: PROVISÓRIO, com o SUB-varN mantido antes do M8

**O achado (ALTA, finder `pisos_online`).** O SUB-varN (D65) nunca foi executado —
`cards/INDEX.md:54` marca ⬜. `SPEC:1488` e o bundle `alg_pisos_online.md:33` condicionam a
bateria à varredura N∈{10,20,30,50}, que deve reconfirmar ou substituir o N=20 cravado em
2026-07-18 (RI-10, já registrado como *"provisório até SUB-varN"*). Como a semente 42 é uma das
30 oficiais, disparar os pisos agora toca o pré-registro.

**Decisão do autor (2026-07-25).** A varredura **NÃO é dispensada**. O N=20 é declarado
**provisório** para as 100 células de piso da rodada-42, e o **SUB-varN permanece como
pré-requisito do M8**. Se a varredura eleger N≠20, as células de piso da semente 42 são
descartadas e re-rodadas sob o N eleito; se confirmar o N=20, elas são promovidas sem alteração.

**Justificativa.**

1. A rodada-42 é **validação de fidelidade e piloto de timing (M7)**, não a bateria de
   comparação: a banda dos pisos que os BO-especiais usam como referência é construída no M8/M9,
   e nenhuma interpretação comparativa é fixada aqui.
2. O custo de refazer é desprezível — as células de piso rodam em **segundos** (medido na
   `matlab-vm3`: 3 células `nsga2` em 6 s), contra as horas das células com surrogate.
3. Adiar a rodada-42 até a varredura não reduz risco algum: o dado gerado é válido para N=20 e
   nada nele é corrompido pela pendência.

**Registrado ANTES do disparo, deliberadamente:** uma dispensa — ou um adiamento — de
pré-registro decidido *depois* de ver os resultados é metodologicamente mais frágil que a mesma
decisão tomada às cegas. Esta entrada é a evidência da anterioridade.

**Pendência aberta:** SUB-varN (D65), cartão `40_subestudos/varredura_N_pisos`, ainda ⬜ —
pré-requisito do M8.

### DI-40 — `c154` SAI do roster do `batch` (q=10); PERMANECE no `main` (2026-07-25)

**O que mudou a conta.** O finder `c154` da validação final simulou o `_WallClockProjector`
(`src/c262_qnehvi.py:435-473`, reusado pelo c154) contra o ④ **real** de `main/c154/DTLZ2_0`
(241 iterações, 52.596 s = 14,6 h medidos) e mostrou que, com teto de 43.200 s, o trip por
projeção só arma na **iteração 158, após ~22.632 s ≈ 6,3 h queimadas** ⟦ERRATA T11 (2026-07-30): este número foi **superado 2×**. O "~min-1h" original foi corrigido para "~6,3 h" pela A28, e a F5 mediu na s42 o valor REAL: **0,87–2,99 h por célula, média 1,47 h** — o "6,3 h" é ~4× superestimado (a projeção arma na it 158 num run cuja iteração encarece). E, com a DI-43/44 + o T11-G5, o ponto ficou histórico: o aborto por projeção foi EXTINTO (a projeção virou `wall_projection_warning`) e o teto passa a truncar COM as camadas gravadas.⟧ — porque a projeção
assume busca constante (média das últimas 5) enquanto a busca JES cresce ~n^1,6, e por isso
dispara tarde. **As linhas 1708 e 1756 deste REGISTRO afirmam "~min–1h": erro de ~6×**, e a
DI-38(a) foi decidida com o número errado.

**Decisão do autor (2026-07-25), tomada com o número corrigido:**

- **`batch` (q=10): o `c154` SAI do roster do disparo.** As 5 células (DTLZ2, MMF16_20, WFG9,
  ZDT1, ZDT4 × semente 42) abortam **100% por desenho** — o piso medido é ≥30 h contra teto de
  12 h — e **não gravam parquet algum**. Custo de mantê-las: ~30 h-core para produzir apenas
  `jsonl` + manifesto `failed`. Roster do batch passa a ser **`c149 c262 e81 sobol_batch`**,
  **20 células** em vez de 25.
- **`main` (q=1): o `c154` PERMANECE, com as 25 células.** Aqui a remoção seria perda de
  evidência, não economia: só a classe D=12/M=3 (DTLZ1/2/3/4/7 + WFG1/2/4/5/9) e o ZDT1 devem
  estourar o teto — **~11 células ⚪ a ~6 h cada (~66 h-core)** —, enquanto as **~14 restantes**
  (MMF1, MMF4, MMF11_L, MMF16_20, ZDT3, ZDT4, ZDT6 e os sete BBOB) **completam com dado
  íntegro**. O `c154`/JES é um dos 22 SA-MOEAs e é o *curinga de custo* do conjunto: o
  comportamento dele sob orçamento apertado é parte do que a dissertação mede.

**Relação com a DI-38(a): não a reverte.** A DI-38(a) decidiu **manter o comportamento** de
aborto por projeção sem camadas, e isso segue valendo — as ~11 células ⚪ do `main` são o
resultado ESPERADO e o portão as reporta como aborto-sancionado, não vermelho. A DI-40 decide
outra coisa: **não despachar** o subconjunto de células cujo aborto é *certo por construção* e
cujo produto é *zero parquet*.

**EXPECTATIVA OFICIAL REVISADA da rodada-42** (substitui a da PARTE A27): **~11 células ⚪ no
`main` do c154** (classe D=12/M=3 + ZDT1), **zero no `batch`** (não despachadas). A estimativa
anterior de "~6-7 ⚪, cada uma a ~min-1h" está **superada**.

**Obrigatório no relatório de fidelidade (dossiê D97):** esta decisão entra explicitamente,
com o número medido (~6,3 h por célula acima do teto) e com a distinção entre o `batch`
retirado por inutilidade e o `main` mantido por conter evidência. Sem isso, a ausência das 5
células de `c154-batch` na consolidação parece lacuna de execução em vez de decisão registrada.

**Pendência para o M8:** o `runs_matrix.csv` continua agendando **150 linhas** de `c154-batch`
(5 problemas × 30 sementes). A DI-40 vale para a rodada-42; a decisão de retirá-las da matrix —
ou de mantê-las e assumir ~225-300 h-core para zero parquet — fica para antes do M8.

### Correções factuais apuradas nesta sessão

1. **A tag `rodada-42-freeze` NUNCA EXISTIU.** `git ls-remote --tags origin` → vazio; nenhuma tag
   local. O `HANDOFF_TORRE_COMPLETO.md` e a PARTE A27 acima a declaram *pushada* — **incorreto,
   confirmado pelo autor** (*"eu nunca commitei ou dei push adicionando essa tag"*). O gate
   substantivo da DI-33b permanece **verde por hash**: `1c2811b` é ancestral do HEAD e
   `git log 1c2811b..HEAD -- src/ scripts/ tests/ requirements/ algorithms/` é **vazio** (os dois
   commits posteriores, `cd67133` e `70e2d97`, são só documentação). Criar a tag é ato do autor.

2. **O `src/` do repo NÃO está no path salvo do MATLAB em NENHUMA das duas máquinas MATLAB.**
   Medido no Mac A: `entradas do repo: 0`, `which('experiment')` → `[]`, com 753 entradas no
   path. O `experiments.m` (raiz) resolve apenas porque o MATLAB busca na pasta corrente; o
   `experiment.m` (em `src/`) **não** resolvia — o mesmo erro que derrubou a primeira tentativa
   da fase 3 na `matlab-vm3` (`Undefined function 'experiment'`). **Consequência: os comandos do
   RUNBOOK §4 para o Mac A falhariam na primeira célula.** Corrigido nas DUAS máquinas com
   `~/Documents/MATLAB/startup.m` (`addpath(<repo>/src)` + `pyenv(...,'InProcess')`), fora do
   repositório. Verificado no Mac A: `which experiment` → `src/experiment.m`; ponte →
   `/Users/gmello/ponte_teste/bin/python`, que **bate com o `PROVISIONAMENTO.md` §5**; e o
   `env_bridge` do Mac recebeu o **primeiro aceite Q2 formal** — `diff` vazio contra
   `locks/env_bridge.lock.txt`. **Não invalida run algum**: o defeito era de *procedimento
   documentado*, não de dado. **Emenda ao RUNBOOK §4 e à receita de VM MATLAB: o `startup.m` é
   pré-requisito das duas máquinas.**

---

## PARTE A29 — A VALIDAÇÃO FINAL (143 agentes) · DI-41 aplicada · DI-42 na mesa (2026-07-28)

**O maior exercício de validação do projeto.** Workflow `wf_c451718a-b88`: **32 finders
fresh-eyes** (20 por-config + 12 transversais, SEM saber que o código já fora validado) rodados
em **Fable** + **111 verificadores adversariais** rodados em **Opus** (divisão pedida pelo autor:
descoberta barata, verificação cara). 143 agentes, 0 erros, ~2,97 M tokens, 1.176 tool-calls.
**310 achados brutos → 64 CONFIRMADOS (13 ALTA + 51 MÉDIA), 20 parciais, 6 refutados, 128 baixas.**
Notas por dimensão: melhores = b4/b5 8,5 · rng-determinismo 8 · matlab-arvores 8; **piores =
fe-budget 4,5 · docs-sync 4,5 · c311 6 · despachante-python 6 · testes 6**.

### DI-41 — os 3 bugs de GATE que a torre corrigiu direto (commit `eb977f2`)

1. **🔴 ⑦ do e103 com o DOBRO de linhas (bug de dado REAL, achado da rodada).** O e103 é
   IBEA-**MS** (multi-surrogate): a ③ grava 1 linha por **(membro × modelo)** —
   `{Kriging-DACE, RBFN}`. O `final_eval` pegava as 200 linhas da última geração e avaliava cada
   ponto **2× na função real**, gravando ⑦ com 200 linhas para 100 membros. Efeito grave e
   silencioso: `n_final` inflado e **`spacing` ZERADO** (duplicata tem distância 0) — e spacing é
   uma das 5 métricas do estudo. Fix: filtrar por UM `modelo_flag` (o 1º da ③), **nunca por X**
   (membros coincidentes de população convergida são legítimos — o `moead_media/BBOB_F17_42` tem
   49/50 X repetidos e DEVE mantê-los). Verificado no-op nos 5 configs de modelo único. ⑦ do
   smoke regenerada: **200→100 linhas, 21 ND, portão VERDE** (o `--check` acusara a incoerência
   corretamente — o gate funcionou).
2. **🔴 Token do aborto sancionado ERRADO (bug meu, do DI-38a/`1c2811b`).** O carve-out ⚪ procura
   `motivo_parada == 'cache_cap'`, mas os runners emitem **`cache_hit_travado`** (c122:815,
   c149:848, e81:1063); `cache_cap` só existe como *nome de parâmetro* no header. Corrigido nos
   3 sítios (portao/accept/censo42).
3. **🔴 `accept.py` dava FALSO-VERDE.** `accept.py:2784` só reprova em `ok is False`; com
   pyarrow/numpy ausentes os 3 checks devolvem SKIP (`None`) ⇒ imprimia **"VERDE"** e saía **0
   sem checar nada**. Como o `portao.py` usa esse exit code e roda no `sys.executable`, um
   `python3 scripts/portao.py` sem o `$PY` do env_main **pintava a varredura inteira de verde**.
   Agora: **INCONCLUSIVO, exit 2**.

### DI-42 — A MESA DO AUTOR (o que a torre NÃO corrigiu, por mandato)

**Bloco 1 — muda comportamento/saída de RUNNER (⇒ dados da rodada-42 passam a diferir dos do M8):**

| # | Achado (confirmado) | Recomendação da torre |
|---|---|---|
| 42.1 | **B1 — `experiments.py:209` sobrescreve `status='failed'` do runner com `'ok'`** (runners standalone abortam por `break`, sem exceção). 4 finders independentes; **prova empírica na rodada-42: `sweep-big-mvns/c311/MMF16_20/42` morreu de `gpy_bfgs_linalg` e está marcada `ok`** — e no offline `fe_final==maxfe` por construção, então `is_run_done` a lê como PRONTA. O rito ⚪ NUNCA dispara no stack standalone | **CORRIGIR antes do M8** (1 linha: não rebaixar `failed` do runner). Na rodada-42: **triar por `motivo_parada`**, não por `status` (já instruído no handoff F5) |
| 42.2 | **Evento `sonda` do ⑥ não grava o campo `fe`** — exigido pelo CONTRATO §6/§3.1 como "o eixo de comparação entre algoritmos". Transversal: b1, b3, c238, MATLAB inteiro, c122… | **CORRIGIR antes do M8** (a sonda perde o eixo de comparação sem isso) |
| 42.3 | **Manifesto ⑤ sem a chave `params`** (config efetiva) — CONTRATO §5. Transversal: c217, c262, c154, b5, moead_media (48/48 runs) | Corrigir antes do M8 (a config efetiva só existe no header do ⑥) |
| 42.4 | Falhas **determinísticas** do c154 (stall D60-b, escada RS esgotada) são **retriadas 3×** pelo despachante — queima 3× o custo para o mesmo fim | Corrigir (não retriar falha determinística) |
| 42.5 | `treed_media` **sem guard de tier**: aceitaria qualquer `exp` e rodaria fora da célula big | Corrigir (guard barato) |
| 42.6 | ⑥ **truncado/sem footer**: c311 7/58 (morre em `dual_write_run` — gcs ausente no env_c311, DEPOIS de gravar manifesto `ok`); `moead_media` 1 caso de **dois escritores concorrentes**; bucket **nunca** tem footer | Corrigir o c311 (env) + lock no ⑥; o footer-no-bucket é estrutural (documentar) |
| 42.7 | **Teste unitário escreve em `data/` de PRODUÇÃO** (`test_batch_q10.py`) — poluiu o ⑥ de `exp_batch_e81_ZDT4_42` com 90 pares header/footer | Corrigir já (tempdir) |

**Bloco 2 — vai para o D97 (fidelidade/comportamento; NÃO é bug de código):** `b5r` com RVs fixos
**colapsa a população** (ZDT4: média 9,9, mín 2) ⇒ ⑦ quase-degenerada · `MMF1` (D=2) degenerado em
vários configs (c141 μ −145..210; c238 μ |339| com f≤8,1 e θ no teto; c149 ensemble constante com
HVI=0 em 40/40) · `HV_gain` negativo em 40-73% das linhas do e74 (artefato CalHV/fmin sob D74) ·
c122 **bloco de sonda g=1 usa a população NÃO-truncada** e grava `n_ref=MU` errado (quebra a
comparabilidade prometida pela DI-16.2 — **este é o único do bloco 2 que é defeito de
instrumentação, não comportamento**).

**Bloco 3 — pré-M8 (já triado na A28, reconfirmado):** células **pré-retrofit** absorvidas pelo
resume (b1 DTLZ2/ZDT1, c238 ZDT1, c262 ZDT1, c154 DTLZ2 — todas semente **0**) ⇒ `--force` antes
do M8 · **datasets de sweep só existem para a semente 42** ⇒ 435 células e103 abortariam no M8 ·
**c262 batch nunca completou ponta-a-ponta** (probe OOM-killed em n=669; RAM em n→2109 não medida)
⇒ **medir antes de disparar o batch com `--n-jobs 8`** · SUB-varN (DI-39) segue pré-requisito.

**Bloco 4 — RUNBOOK/operação:** comandos MATLAB sem `'parallel',false` (O-09 declara parfor
incompatível) · comandos batch/sweep **sem `--problems`** (default = 25 problemas ⇒ 125 células em
vez de 25) · roster default do `experiments.m` inclui e103 com `exp='main'` · resume não-idempotente
do e103 (re-executa até o `final_eval` pós-hoc rodar).

### O que a validação CONFIRMOU de bom (ponto 4 do pedido do autor)

**Os 20 vereditos de comportamento são majoritariamente EXCELENTES.** FE exato em 100% dos smokes
de todos os configs; **não-perturbação da sonda PROVADA bit-a-bit** (① idêntica com/sem sonda) em
b1, b3, b4, e7, c141, c217, c238, e74; convergência real medida (b3 ZDT1 f1 2,25→0,017; b4
2,25→0,40; e7 DTLZ2 f_best→~0 com n_front1 37→88; c238 DTLZ2 f→1e-26); mecanismos vivos e
observáveis (c217: 585/588 gerações em estado 3 = surrogate inativo sob 31D−1, **exatamente o que
o autor já aceitou em D97 9/10**; b3: switch incerteza/APD 44/4 no M=3 e 100% APD nos demais; e7:
gatilho dual 152/48; b4: gate L>0,9 respeitado com mínimo 0,9006); guardas armadas sem disparo
espúrio; cache-hit D89 exercitado em dado real (b3: 2 infills duplicados no ZDT1). **A régua do
estudo funciona.**

---

## PARTE A30 — DI-42.1 APLICADA + o PLACAR dos 64 + a mesa DI-42.2-.7 (2026-07-28)

**DI-42.1 ratificada pelo autor e aplicada (`8e8e966`):** `experiments.py` não rebaixa mais o
`status='failed'` do runner para 'ok' (runner = autoridade do próprio fim; direção inversa
preservada). RUNBOOK: `--problems` nos comandos batch/sweep (sem ele = 125 células), roster
DI-40 (sem c154 no batch), `'parallel',false` em 7 comandos MATLAB (O-09).

**PLACAR DOS 64 CONFIRMADOS:** ✅ **9 resolvidos** (B1×3 achados + cache_cap×2 + ⑦-e103 [as 5
regeneradas] + falso-VERDE + --problems + parallel,false) · 📋 **~9 sem ação de código** (vão ao
dossiê D97 como comportamento: HV_gain e74, MMF1 degenerado em c141/c238/c149, b5r colapso de
RVs, retreino-em-cache-hit, overshoot e7, crash-latente c238 observado em n_front=2) · 🔧 **~40
= lote de refinamento pré-M8** (trabalho sancionado pela doutrina do autor, sem escolha real:
campos contratuais faltantes no ⑥/⑤/sigma_dict, guards latentes, testes-lacuna [straddle/D74/
hard-stop-b4/CACHE_CAP], teste→tempdir, guard de tier, roster e103 do experiments.m, manifesto
failed q=1 em batch, preflight content-hash, suíte hermética [D-03], datasets sweep 29 sementes,
force das células s0 pré-retrofit, probe de RAM do c262 batch, resume/final_eval e103) ·
🔴 **6 DECISÕES GENUÍNAS na mesa (DI-42.2-.7):** células comprometidas da s42 [4: c311 big-mvns
LinAlgError mascarada; moead ⑥ 2-escritores; treed ⑥ truncado; e81-batch ⑥ poluído pelo teste] ·
env_c311 sem google-cloud-storage (guard vs pin D80) · c122 sonda g=1 não-truncada · campo fe do
evento sonda (fixar todos × Python-só+③ como eixo × documentar) · params no ⑤ · no-retry de
falhas determinísticas. Detalhe/opções na resposta da torre ao autor (2026-07-28).

---

## PARTE A31 — DI-42.2-.7 DECIDIDAS pelo autor (2026-07-28) + execução parcial

**Ratificações (REVISADA 2026-07-28-b):** .2=**(c) NOVA DECISÃO DO AUTOR — NÃO re-rodar nada**: a consolidação já aconteceu e a VERSÃO OFICIAL é a do BUCKET; as 4 células comprometidas ficam em QUARENTENA documentada (sem mutação de dado agora) e serão reavaliadas após a 2ª RODADA DE FIDELIDADE que o autor vai disparar · .3=(c) blindar código E
instalar a lib (blindagem APLICADA no commit; lib = ação do autor/D80 no env_c311 de Mac+VM-2)
· .4=(a) fix c122 g=1 no T11 + caveat s42 · .5=EM DISCUSSÃO (autor pediu aprofundamento; a
evidência empírica MUDOU o quadro: o evento sonda do ⑥ JÁ carrega fe_treino_max — c217/s42
verificado — o que falta é só o campo literal `fe` do CONTRATO §6; ③ tem fe_treino_max povoado)
· .6=(a) params no ⑤ via T11 · .7=(a) lista no-retry determinística via T11.
**Aplicado agora:** blindagem do dual_write nas 2 harnesses (upload nunca mata run; falha →
`upload_status.erro`). **T11 (cartão único do refinamento) acumula:** .4, .6, .7 + os ~40
sem-escolha da A30 + o que a análise de fidelidade colher.

---

## PARTE A32 — F5 ABSORVIDA · CRUZAMENTO DAS 2 ANÁLISES · T11 CONSOLIDADO (2026-07-29)

**A análise de fidelidade F5 fechou e o autor APROVOU os 24 configs** (média 9,33; 11 aceitar +
13 aceitar+caveat; ZERO bug de algoritmo; 3 células excluídas com prova). A torre absorveu 100%
dos ~1.700 artefatos (leitura direta do PLANO_RODADA_PERFEITA + RELATORIO_FINAL + 11 leitores
estruturados = 533 itens) e cruzou com a validação de código (143 agentes, A29-A31).

**Cruzamento:** convergência total — meus fixes DI-41/42 = B-05/06/07 do plano F5 (o falso-VERDE
"quase fez a F5.1 começar errada"); meus achados eram os SINTOMAS e a F5 provou o MECANISMO
(trio is_run_done-sem-campanha + append-cego + escrita-não-atômica; 34/666 anômalas, dano real =
1 quimera). O contraditório corrigiu a torre 2×:
**ERRATA à PARTE A30/DI-42:** (1) o c122 GRAVA o campo `fe` no evento sonda (runner :752
passa fe=bud.fe) — a claim "c122 sem fe" está ERRADA; (2) o número da DI-40 ("~6,3 h/célula
queimada") é ~4× superestimado — medido na s42: 0,87–2,99 h, média 1,47 h (D7 da F5).

**T11 CONSOLIDADO** (`handoff/T11-PLANO-CONSOLIDADO.md`): 8 ✅ já-feitos · 13 🔧 bloqueadores
(~19h, TODOS valem) · ~10 🔩 instrumentação seletiva · 9 🚦 gates (3×1 pronto) · 12 📄 doc ·
14 ❌ não-corrigir (doutrina "mínimo de mudança, zero erro" aplicada) · **10 decisões T11-D1..D10
na mesa do autor** (destaques: re-run das 2 reprovadas supersedendo a quarentena; substituição
da quimera c149 pela cópia provada do Mac; batch/c262 fora do M8; REABERTURA do T10 com a math
corrigida; iteration_seed por célula [D15 — ciência]; SUB-varN/datasets/envs-Linux/tag como
pré-requisitos). Sequência F0→F9 do plano F5 adotada; re-execução obrigatória TOTAL = 1,17
h-core. Meta: re-gate das 666 devolve exatamente 1 quimera + 34 anômalas.

---

## PARTE A33 — CONSOLIDAÇÃO FINAL: 3 fontes → mesa T11-D1..D13 (2026-07-29)

**Fecha o pedido do autor: "consolidar TODAS as decisões (fidelidade + validação-143 + rodadas
passadas), filtrar pelo essencial, contar e catalogar".** Caça histórica com 7 agentes: **362
pendências avaliadas — 144 RESOLVIDAS, 52 SUPERSEDED, 166 abertas brutas → dedup → 13 DECISÕES
FINAIS (T11-D1..D13, §12 do plano) + trabalho novo absorvido (OP-6 higiene do --force; e2e de
aborto→teste do B-05; fallback-footer→B-15; regen matrix pós-D4; lote 📄 herdado) + 5 novos ❌
pela doutrina (load_sonda triplicado com gatilho D-18 atingido e RECUSADO; emit_sonda_block;
q=None c149; sweep q=20 descartado; A3/B4+D98/D99/§14 = camada R4/futuro).** Resgates notáveis
do passado: **DI-07b do e74 ABERTA DESDE 18/07** (a SPEC L.8 ainda promete promoção do fix "antes
da bateria" — vira D12, rec: NÃO promover, você já aprovou o e74 9,0 com caveat) · contra-
argumento científico ao D4 (remover batch/c262 deixa o sub-estudo com 3/5 configs; nova opção:
mantê-lo COM T10) · cache_root divergente desde o DI-05. Laudo de instrumentação (§11) já
incorporado com a REFUTAÇÃO da torre ao I-1 (Pmid reconstituível: CalFitnessPC sem RNG + ② com
37.114 ids medidos). **Estado: TODO o conhecimento das 3 fontes está em UM lugar
(handoff/T11-PLANO-CONSOLIDADO.md); falta só a mesa D1..D13 do autor → cartões T11 → execução.**

---

## PARTE A34 — DI-43: TETO 33h + RODA-SE TUDO + TRUNCAMENTO UNIVERSAL + CHECKPOINTS (autor, 2026-07-29)

**Devolutivas da mesa T11-D1..D13:** D1-D3 ✅ à risca · **D4/D5 = DI-43** (supersede DI-38a e
reverte a DI-40 no roster): teto experimental = **33 h**; **rodam TODAS as 695 células × 30
sementes** (incl. as 5 c154-batch); rito único Python = **truncamento-com-dado** (T10
obrigatório; aborto-por-projeção extinto); **NOVO requisito: outputs intermediários**
(checkpoint atômico periódico) · D6-D7 ✅ (falhas=decidir pela referência; iteration_seed ganha
a célula no M8) · **D8 revisada**: as ~29 não-ok da s42 re-rodam TODAS sob o regime novo ·
D11 ✅ (TODAS as melhorias de instrumentação, incl. sonda estratificada) · D9/D10/D12/D13
aguardam re-explicação didática. SPEC §5.1 reescrita (bloco DI-43) + bundles regen. Efeitos:
E-08 (RAM c262-batch) volta a ser obrigatório; custo re-projetado +12-17 mil h-core ⇒ E-10
(envs Linux) crítico; T11 ganha 2 frentes novas (T10-expandido + checkpoint).

---

## PARTE A35 — 🏁 MESA ZERADA: DI-44 (teto 12 h) + DI-45 (fix do e74 APROVADO) — 13/13 decididas (2026-07-29)

**DI-44 — teto FINAL = 12 h** (emenda à DI-43, que havia posto 33 h). O autor decidiu com a
conta da torre na mesa: as **25 células** que estouram o teto são **3,6% do grid** e
consumiriam **73%** da campanha a 33 h (**34.041** h-core) contra **18.291** h-core a 12 h —
economia de **15.750 h-core (46%)**; e como a F5 provou que essas células NUNCA completam
(teto de 48 h ⇒ `ok=0` em 14; projeções 41–190 h), horas extras só compram pontos adicionais de
uma curva parcial (valor marginal decrescente). **TUDO O MAIS DA DI-43 PERMANECE**: roster 100%
(695×30, c154-batch de volta), truncamento-com-dado universal (T10 obrigatório; aborto-por-
projeção extinto; teto por RELÓGIO), outputs intermediários (checkpoint atômico). Base do
custo = heatmap `f5/tempo_heatmap_30seeds.html` (Σ 10.173 h-core; c149 2.811 · c154 1.537 ·
c122 1.239 · b5m 1.123 · c262 867 · e81 680 · c238 502 · e7 452).

**DI-45 — fix do e74 APROVADO** (fecha a DI-07b, aberta desde 2026-07-18). O autor autorizou
aplicar o fix do desalinhamento máscara×Parent em `ClassifierSelect.m:46-48` — a torre REVISOU
a recomendação (antes: não-promover) porque o autor vai **re-validar fidelidade na semente 1**,
o que remove o único contra-argumento. Razões a favor: (i) **bússola D29** — bug do código
original ⇒ segue o ARTIGO; (ii) **precedente no próprio e74** — o D76 já patchou o MESMO tipo de
bug de máscara nesse algoritmo (era incoerente corrigir um e deixar o outro); (iii) o fix é
**1 linha nova + 1 alterada** (capturar `find(y_label==1)` e mapear a ordenação de volta ao
índice absoluto); (iv) restaura a **Contribuição 1 declarada do paper**. Impacto medido do
desvio (F5, 25 células): a metade "classificador guia" OPERA (elite em 96,7% dos 2.091 infills)
e a metade "incerteza escolhe" é INERTE (argmax em só 12,24%; rank mediano 43/100) + 13,31% dos
ciclos em no-op. **Não invalidou resultados** (e74 = 9,0 aceitar+caveat), mas 1 das 3
contribuições do artigo não se reproduzia. Obrigatório junto: preservar a telemetria
`n_desalinhado` (~~para PROVAR na validação da semente 1 que o argmax passou a valer~~ — ⚠ **ERRATA 15
  (2026-07-30): ISTO ESTÁ ERRADO.** O `n_desalinhado` **NÃO mede** o desalinhamento que a
  DI-45 corrigiu. São DOIS sítios distintos no e74: a DI-45 corrigiu
  `ClassifierSelect.m:56-58` (o `index` era posição DENTRO de `S` e indexava `Parent`
  inteiro); o `n_desalinhado` mede `Local_infill.m` (máscara(Offspring)×Parent), que
  **permanece por decisão registrada** — o próprio `src/e74_instrument.m:184` traz o
  comentário `% mascara(Offspring)×Parent (fix opcional NAO aplicado)`.
  MEDIDO: s42 pré-fix **93,49%** (2.860/3.059) × smoke pós-fix **89,80%** (273/304) — a
  diferença é de célula, não efeito do fix. Ele NÃO cai e cair seria suspeito.
  **A prova real do DI-45 é o gate ±3σ**, que PASSOU em 3 células (8 gates verdes cada,
  2026-07-30), mais o `preflight`: âncora `e74-classifierselect-idx` APLICADO e lacre
  `867ae5f56d8b` OK. Quem seguir a instrução original fará a verificação ERRADA) + re-lacre
de âncora/`repos.lock` do e74 (vendorizado tocado).

**🏁 PLACAR FINAL DA MESA T11: 13/13 DECIDIDAS.** D1-D3 (re-runs/quimera/⑦) · D4+D5 (DI-43+44) ·
D6 (falhas = decidir pela referência; default limitação) · D7 (iteration_seed ganha a célula no
M8) · D8 (re-rodar TODAS as ~29 não-ok) · D9 (5 conclusões cravadas no DOSSIE §D9) · D10 (fila
de pré-requisitos autorizada; ações de infra do autor anotadas p/ depois do código) · D11
(TODAS as melhorias de instrumentação, incl. sonda estratificada dos classificadores) · D12
(=DI-45) · D13 (só as 2 verificações dirigidas: b1-torneio e b3-índice). **Zero decisões em
aberto. Próximo: a torre escreve os cartões T11.**

---

## PARTE A36 — EXECUÇÃO DO T11: FASE G + FASE A + as 8 erratas que o próprio trabalho gerou (2026-07-29/30)

**Estado:** FASE G fechada (G1-G7, 7/7) + FASE A quase completa (A1-A11 com
resíduos declarados) + V1. Suíte **394 → 587 testes, 0 falhas**. ~36 commits.

### As 8 ERRATAS abertas contra os documentos-fonte (todas verificadas no DADO)

Todas nasceram da regra da casa *"se você escrever QUALQUER afirmação em doc,
verifique no código/dado antes de commitar"* — e cada uma teria virado trabalho
errado se eu tivesse seguido o texto:

| # | onde | o que o doc dizia | o que o dado diz |
|---|---|---|---|
| 1 | PLANO F5/B-11 | o splice do `main/b1/WFG1` está "nas linhas de header/sigma_dict" | o header tem **512 B**; as 49 malformadas são `b1_gen`/`sonda` (mediana 1.647 B) com um `guard` de ts POSTERIOR sobrescrito no meio |
| 2 | PLANO F5/B-11 | "`src/b1_instrument.m` (2 handles no mesmo arquivo)" | **não existe 2º handle**: só `experiment.m` tem `fopen`, 1 fid por run |
| 3 | PLANO F5/B-12 | abortar se `env.executable ≠ o intérprete da máquina` | daria **304 falsos-positivos** (a mesma máquina roda 4 venvs por desenho, E-10). O discriminador certo é o HOST ⇒ **58** verdadeiros-positivos |
| 4 | PLANO F5 §5/aceitação | "re-gate ⇒ 1 quimera + **34** anômalas" | 1 quimera ✔ + **15** anômalas + 21 `footer_faltante` que o **próprio B-15** manda NÃO acusar. Aritmética completa: 12+9+6+1+1 = 27 distintas |
| 5 | I-13/A24 | `geracoes_derivadas` = `⌈(20D+n_dup)/2⌊N_ef/2⌋⌉` | acerta **0/112**; a string antiga acerta 2/112; `floor(...)` acerta 103/112 ⇒ **`n_geracoes` é EMERGENTE**, não fechada |
| 6 | contrato_61 (meu) | `mll_final`/`loss_treino` ausentes | **ANINHADOS** em `modelo_hp` — era o meu gate olhando só o topo |
| 7 | §6.1 do CONTRATO | e103 deve ter `margem_3sigma` | o runner grava `margem_3sigma_stats`, que é **mais rico** (a estatística do gate, DI-13.4b) |
| 8 | §6.1 do CONTRATO | c154 deve ter `n_baseline` | o `sigma_dict` do PRÓPRIO runner já dizia "AUSENTE POR DESENHO" (qLBMOJES não faz prune) |

### Contratos NOVOS que a execução criou (a próxima sessão precisa saber)

1. **`fe_final` do ⑤ de checkpoint é PISO das camadas.** As 5 escritas são
   atômicas uma a uma, não como grupo; o ⑤ é a última, então um kill pode deixar
   as camadas 1 checkpoint à frente. A direção é a garantia: o ⑤ nunca promete
   dado que as camadas não têm.
2. **`is_run_done` exige `campanha_id`** (v1 ⇒ False, o que força o re-run das
   stale); auditar o passado usa `manifest.QUALQUER_CAMPANHA`.
3. **O despachante abre o ⑥ com `append=False`** — quem chega ao `_run_one` vai
   executar, logo é o dono do arquivo.
4. **O aborto sancionado passa pelos gates de PROVENIÊNCIA** (só os de conteúdo
   são dispensados): com truncamento-com-dado a célula TEM camadas.
5. **`tempo_aval_real_s` pode ser NULL** — "não medi" ≠ "custou zero".
6. **O gate G-3 tem 2 modos** (`campanha` × `historico`).

### 3 cirurgias vendorizadas, todas com âncora + re-lacre + prova

| âncora | arquivo | natureza |
|---|---|---|
| `e74-classifierselect-idx` | `ClassifierSelect.m:46` | **DI-45** — fidelidade (bússola D29) |
| `b5-pwrong-stats` | `ProbMOEAD_select.py:28` | I-05 — instrumentação read-only |
| (as 2 do b5 que já existiam) | — | re-validadas: `preflight` reporta APLICADO em 4/4 |

### Achados NOVOS que viram decisão do autor

- **VD-b1 (V1):** ~~achado 🔴, mesma classe do DI-45~~ → **ERRATA 10 · RETIRADO.**
  O registro abaixo estava errado nas duas pontas e ficou assim por 6 commits
  (achado da varredura de 2026-07-30):
  **(a) SEVERIDADE superestimada.** O torneio do `EvolALG.m:16` de fato ranqueia
  pelo PCheby do SUBCONJUNTO e indexa o `Dec` INTEIRO em 93,0% das 8.443
  gerações — mas isso constrói APENAS a metade-crossover da PRIMEIRA geração
  interna do GA de aquisição; da 2ª em diante os domínios CASAM
  (`EvolALG.m:65`). Medido: o ramo defeituoso é **3,87%** dos 87,77 M candidatos
  scorados, e o infill veio da 1ª geração interna em **12,19%** dos ciclos ⇒ o
  torneio é **INERTE em ~93,9%**. Concentrado: BBOB_F37 62,7% e BBOB_F49 61,3%.
  **(b) CLASSIFICAÇÃO errada.** A SPEC já tem este item como **🟠 IMPL → CÓDIGO,
  documentado**: `SPEC:434` cita "torneio do b1" pelo NOME entre os exemplos de
  🟠, e `SPEC:500` o lista entre as divergências periféricas mantidas no CÓDIGO
  (D30/D47). O `EvolALG.m:9-10` registra a decisão da sessão anterior: *"o bug
  do torneio (:16) fica (CODIGO K.3)"*. Marcá-lo 🔴 disparou um D81 sem motivo e
  **reabriu decisão FECHADA** — a mesa estava zerada.
  **(c) O argumento de "consistência com a DI-45" também era falso.** A bússola
  da SPEC distingue os casos: o GA interno do b1 é o otimizador de aquisição,
  **periférico** ao mecanismo que a tese mede (o surrogate e o uso da
  incerteza); a seleção assistida por classificador do e74 **É** o mecanismo.
  **NADA MUDA no b1.** O número medido vira lastro da classificação 🟠 que já
  existia. Relatório em `handoff/T11-V1-verificacoes-dirigidas.md`.
- **VD-b3:** o `Next` do `UpdataArchive` mistura domínios de índice no ramo 1.
  **FECHADO como forense read-only** — o pedido de instrumentar
  `size(Via,1)`/`NI−mu` foi RETIRADO junto com a ERRATA 10: medir mais para
  decidir algo que não está em aberto é trabalho sem destino. `nzero=0` em
  1.619/1.619 ciclos não discrimina o ramo, e isso é desfecho legítimo.
- **`sigma_dict` ausente no ⑤ dos 4 pisos online** (112 células) — resolvido
  declarando `nao_se_aplica`, no padrão que o próprio piso já usa no bloco
  `sonda`.

---

## PARTE A40 — VALIDAÇÃO DA TORRE SOBRE O T11: as 2 CAUSAS-RAIZ dos campos sentinela (2026-07-30)

**A torre validou o T11 de forma independente** (suíte **627 OK/0 falhas** re-rodada · `staleness`
0 · `preflight` exit 0 com 1 pendência conhecida de 58 manifestos forasteiros · git limpo). O
validador de fidelidade tinha nomeado a assinatura **"campo verde, dado sentinela"** (o campo
novo existe, passa nos gates, e o DADO é inútil) mas não achou a mecânica. **A torre achou as
duas, e ambas são de 1 linha:**

**(1) `c217.pmid_ids = -1` em 426/426.** `pmid_ids_c217` chama `bud.solutionIdOf(Pmid(i,:))`,
que casa **bit-a-bit no X nativo (D colunas)**. Mas o `Pmid` vem de `CalFitnessPC.m:67-73`, onde
`Input = [PopDec(...), Fitness(...)]` — ou seja, **`Pmid` tem D+1 colunas** (a última é o
Fitness anexado). O match nunca ocorre ⇒ sentinela −1 sempre. **Fix: `Pmid(i, 1:end-1)`.**

**(2) `b5m.flag_vetores_degenerados = null` em 1.144/1.144.** `_vetores_degenerados`
(`src/b5_prob.py:113-118`) acessa `evolver.population.problem.reference_vectors.values` — mas
`reference_vectors` **não existe** em `Population.py`/`Problem.py` do DESDEO (grep vazio): no
DESDEO os vetores de referência vivem no **EVOLVER** (RVEA/MOEAD), não no problem.
`AttributeError` → `except Exception: return None` (o guard D97, correto em si) **mascara o
caminho errado**. **Fix: apontar para o evolver.**

**A LIÇÃO ESTRUTURAL (vale mais que os 2 fixes):** os dois passaram por 6 portões verdes porque
**os gates da instrumentação testam TEXTO, não COMPORTAMENTO** (`inspect.getsource` + `assertIn`
— 2 arquivos de teste hoje). Regra nova proposta pela torre e endossada pelo validador: **todo
gate novo exige CONTROLE NEGATIVO** — um teste que REPROVA no código de hoje e PASSA depois do
fix; e todo campo novo de instrumentação exige **asserção sobre o VALOR** medido num run real
(ex.: "≥1 id ≠ −1", "flag não-null em ≥1 evento"), nunca sobre a existência da chave.

---

## PARTE A41 — CARTÃO T12 ABERTO: o acabamento final (torre, 2026-07-31)

**Escopo** (`handoff/T12-CARTAO.md`): os 8 bloqueadores da validação de fidelidade do T11
(BL-01/02/05/06/08/09 = ~15 linhas de código; BL-07/10 = decisões) + as 2 causas-raiz da A40
embutidas (Pmid D+1 colunas; reference_vectors no evolver) + a conversão dos gates decorativos
(texto→comportamento) + varredura de VALOR de todos os campos de instrumentação do T11.
**Doutrina do cartão: CONTROLE NEGATIVO OBRIGATÓRIO** (todo fix demonstra o defeito antes) +
asserção de VALOR (nunca de existência de chave). **2 decisões na mesa: BL-07** piso de ruído
entre máquinas (rec.: re-caracterizar dos dados existentes → `piso_ruido.json` POR problema +
regra no CONTRATO) e **BL-10** N=20 (rec.: DI-39 prevalece sobre DI-32/A2 — retificar e manter
SUB-varN pré-disparo). Score da torre pré-T12: 80% p/ disparo; projetado pós-T12: **93%**.
Banner do CLAUDE.md atualizado (campanha = T12). Pós-T12: tag final → fila D10 → DISPARO.

---

## PARTE A43 — VALIDAÇÃO DA TORRE SOBRE T12/T13: APROVADO com 9 residuais → T14 (2026-07-31)

**Protocolo cumprido: nada aceito por leitura — a torre RE-MEDIU.** (1) Suíte re-rodada:
**688 OK/0 falhas** ✓ · staleness 0 ✓ · preflight exit=1 = **a guarda anti-forasteiro fazendo
o trabalho** (58 manifestos das VMs no disco local; ação do AUTOR: limpar antes do disparo).
(2) **Controle negativo GENUÍNO verificado por worktree**: `test_t12_b5_vetores` contra o
código pré-T12 (4b4834f) = `failures=2, errors=2` — EXATAMENTE o reportado. (3) **Smoke
re-executado PELA TORRE** (c217/MMF1/s42, MATLAB, tempdir — caindo e saindo da armadilha O-01
do dataRoot no caminho): **426 pmid_ids, ZERO sentinelas** + `y_treino_dist` real com
`confere_com_TrainIn=true` e a nota honesta do rótulo binário. Reprodução independente = 100%.
(4) Forense git: 32 arquivos, +3.487/−97, **zero toques em vendorizado**, 11 commits limpos.

**Qualidade da campanha: EXEMPLAR.** A doutrina do controle negativo pagou 3× (achou 3 defeitos
sozinha); o dado corrigiu o cartão 2× (DTLZ2 sadio/DTLZ3 congelado; rótulo binário); a sessão
auto-reportou 6 erros com custo; e entregou ALÉM do cartão (T13: driver multimáquina p/ a frota
expandida de 8-9 máquinas, 695 células derivadas, venv-por-máquina).

**Os 9 bloqueadores residuais (BL-11..14,17..21): TODOS marcados `antes_do_disparo=False` pelo
próprio validador — mas a torre recomenda o micro-cartão T14 (~2h) ANTES da tag:** 6 são fixes
de 1 linha/1 token (BL-11 ⚠ o mais material: I/O do checkpoint DENTRO de `tempo_busca_s` —
53,9% de inflação medida numa célula; timing é resultado de 1ª classe §17.6/D50 · BL-14 flag
errada 2/25 · BL-17 gate G-7 sem a linha dos pisos · BL-18 literal · BL-20 f-string · BL-21
progress.py lê footers[-1] — mentiria DURANTE a campanha) e 3 são doc (BL-12/13/19). + B3
(writer MATLAB) e o comentário do jsonl_open na mesma leva.

**Triagem das 8 definições do repasse:** 1=T14 (sim) · 2=infra do autor (fila D10; frota agora
8-9 máquinas — risco env_b5/Rosetta) · 3=mapa semente→máquina balanceado por custo (aceitar a
oferta; gerar no T14) · 4=tabela de tempo do M7 sai do ④/⑤ APÓS BL-11 · 5=piso_ruido → mesa
BL-07 (pendente do autor) · 6=B3→T14 · 7=SUB-varN pré-disparo (DI-39, já decidido) · 8=doc→T14.

**Score da torre: 92% hoje · ~95% pós-T14+infra.** Os últimos pontos não saem de leitura de
código — saem da validação de fidelidade na SEMENTE 1 (já planejada) e da 1ª rodada real da
frota nova.

---

## PARTE A44 — T14 EXECUTADO: 11/11 itens · 4 desmentidos do dado · 1 decisão na mesa (2026-08-01)

**Os 9 bloqueadores residuais + B3 + os 2 de operação: FECHADOS.** 20 commits
(`7ecc0d5`…`92b5cde`), suíte **688 → 826 · 0 falhas**, staleness 0, ZERO toques em
`algorithms/` (vendorizado), `f5/` (evidência congelada) e `data/experiments/`. Nada pushado.
Handoff completo em `handoff/T14-FINAL.md`.

**⚠ O DADO DESMENTIU O CARTÃO/BLOQUEADOR EM 4 ITENS — e prevaleceu nos 4:**

1. **BL-11 (T14.1)** — o cartão diz "o padrão é o mesmo nos 8 runners". **Em 7 já estava
   certo:** o `talvez_gravar` roda DEPOIS de a ④ fechar e o I/O caía no vão ENTRE gerações
   (fora do `tempo_geracao_s`, mas SEM NOME). Medido em célula real: **4,153 s de checkpoint
   num run de 5,723 s = 72,6% do wall**, contra Σ`tempo_geracao_s` = 0,109 s — não era
   inflação, era buraco não-atribuível. Só o `treed_media` inflava. Controle negativo (célula
   real, env_c311): `tempo_busca_s` 3,2089 (OFF) × 3,2798 (cadência 1) = **+2,2%**; pré-fix
   seria +85,2%.
2. **BL-12 (T14.5)** — o cartão manda gravar `AUC 0,5065`; a re-medição das baterias dá
   **0,5075** (o valor da §6.3 do b4.md, da regra 12 e do controle cruzado; o 0,5065 aparece
   1× só, no §E1). Também caiu a frase *"elas medem outra coisa"*: em M=2 — **19/25** células
   do b4 — a leitura alternativa é numericamente IDÊNTICA à DI-18.
3. **BL-13 (T14.6)** — a fórmula que o bloqueador prescreve para o moead
   (`floor((20D+clones)/N_ef) + 1`) acerta **0/28**; sem o `+1`, **28/28**. E o "erra +1 em
   28/28" do smsemoa não reproduz (lá `N_ef`=20 sempre e os denominadores coincidem).
   Ramificada por família de operador: **103/112 → 110/112**.
4. **BL-18 (T14.7)** — o bloqueador nomeia 3 configs; pelo SEU PRÓPRIO critério (assimetria
   INTRA-run) só **2** têm o defeito: e103 e **c217** (que não está no texto do cartão). O
   c262 é uniforme-NULL ⇒ não é defeito, e declara o espaço no `sigma_dict`. Ficou de fora.

**Achados de escopo que a varredura entregou de graça:** o 3º sítio do padrão `[-1]`
(`export.py`) era **código morto** — removido em vez de "corrigido"; um **3º sítio** na SPEC
com o par inexistente `(p1,p2)` que o cartão não lista (`:1486`); e a errata do docstring do
`RunJaFechado` re-medida no corpus (**559→747**, 94 pares × 2 linhas — não "747→767").

**A DECISÃO QUE A SESSÃO TOMOU (reversível em 1 linha) — B3/T14.10:** *"fechar a exceção do
writer MATLAB"* foi lido como FORMALIZAR a recomendação do T12 §7.3 (não trocar o writer antes
da tag), não como aplicar o writer Java — porque é literalmente a exceção que o repasse
recomenda, porque 19 sítios em 13 configs é o oposto de "~15 linhas · nada toca mecanismo", e
porque o §12.6 escalou a pergunta ao autor e ela nunca foi respondida. **O que entrou no lugar
é mais forte que a prosa anterior:** a exceção virou TRIPWIRE — o escritor único é consequência
mecânica de o `experiments.py` derivar o roster dos loaders e a CLI RECUSAR os 13 MATLAB
(aferido por comportamento), e se um config MATLAB entrar no dispatch Python o teste fica
vermelho ANTES de a campanha gravar ⑥ spliced.

**T14.11 — o mapa semente→máquina existe e o driver o consome.** 14.019 h-core, wall máximo
252,8 h, **desbalanceamento 6,02%** (critério ≤10%; o guloso LPT sozinho dava 30,6% — o
gargalo nasce da interação entre grupos). Os pares são agrupados por CONJUNTO DE MÁQUINAS
ELEGÍVEIS (stack × `alg_to_env` × `envs` da máquina), então a restrição de env do
e103/env_b5/env_c311 é consequência da estrutura, não remendo. As 30 células sem wall medido
(19 c154 · 9 c262 · 1 b1 · 1 c311 — as mais caras do estudo) são imputadas pela mediana do alg
e vão DECLARADAS uma a uma no artefato.
**🔴 PENDENTE DO AUTOR:** nomes/`jobs`/`envs` das **5 máquinas NOVAS** são PLACEHOLDER (item
§12.2, nunca respondido). Editar `artifacts/frota.json` + `python3 scripts/mapa_sementes.py`
refaz o mapa inteiro — e o `jobs` (capacidade) é o que mais move o resultado.

**Achado fora de escopo, NÃO tocado:** `sweep-small-lhs/moead_media/ZDT1_42` tem 3 footers e os
dois primeiros DISCORDAM (`ok`/929 e `failed`/929/`erro_RuntimeError`). A primitiva devolve o
primeiro e o ⑤ diz `ok`. É a armadilha "status mente, motivo_parada não" (B1) numa célula real
da s42 — escolher entre dois footers FECHADOS é semântica de término (mapa_termino/O-21), não
conserto de leitura. Vale a mesa antes da R4.

**Caminho até o disparo:** frota (§4.1 do handoff, 1 comando) · B3 sim/não · limpeza dos 58
forasteiros (autor) → tag → fila D10 → DISPARO.

---

## PARTE A45 — VALIDAÇÃO DA TORRE SOBRE O T14: APROVADO — e a prova definitiva da doutrina (2026-07-31)

**Re-medição integral:** suíte **826 OK/0 falhas** ✓ · staleness 0 ✓ · forense 39 arquivos
+4.174/−89 com **zero toques** em algorithms//f5//data/experiments ✓ · **controle negativo
genuíno via worktree** (test_t14_rotulos vs 7ecc0d5^: 40 falhas — o defeito existia) ✓ ·
**mapa_sementes re-verificado independentemente**: 3 mapas (9/7/6 máquinas), 30 sementes,
zero duplicatas, cobertura total, desbalanceamento 6,02% ≤ 10% ✓.

**A prova definitiva da doutrina:** o T14 encontrou o CARTÃO DA TORRE errado em 4 pontos e o
dado venceu em todos — (1) BL-11 não era inflação em 7/8 runners, era **buraco não-atribuível**
(o I/O caía no vão entre gerações; caso extremo: 72,6% do wall sem nome no sobol_batch);
(2) o AUC de calibração era 0,5075, não 0,5065; (3) o `+1` prescrito pelo BL-13 acertava
**0/28** (sem ele, 28/28); (4) o BL-18 valia p/ e103+c217, não os 3 do texto. Duas rodadas
seguidas em que a medição corrigiu a prescrição — o pipeline agora se defende até de nós.

**Decisões fechadas pela torre:** (1) **B3 RATIFICADO como formalização + tripwire** (aplicar
o writer Java = 19 sítios × 13 configs na véspera da tag — contra a doutrina; fica no backlog
pós-M8); (2) **célula moead_media/sweep-small-lhs/ZDT1_42 (3 footers, 2 discordantes)**:
recomendação = REGRA DE LEITURA, não mutação — o ⑤ desempata (gates F5 verdes, fe=929=maxfe
nos dois footers, parquets íntegros; o footer `failed` é resíduo do incidente 2-escritores já
adjudicado na F5 §4-8) → registrar no CONTRATO §10 + anomalia no censo. **Pendente do AUTOR:**
preencher `claude_code_context/artifacts/frota.json` (nomes/jobs/envs REAIS das 5 máquinas
novas — hoje placeholder) e re-rodar `python3 scripts/mapa_sementes.py`.

**Score: ~94%.** Caminho final: limpar os 58 forasteiros → frota.json real → TAG (autor) →
fila D10 (envs/lib gcs/datasets 29 sementes/SUB-varN) → **DISPARO M8**. O residual (~5%) só
cai com a validação de fidelidade na semente 1 e a 1ª rodada real da frota de 9.

---

## PARTE B — Histórico retroativo (decisões de implementação anteriores a este lote)

| ID | Data | Decisão | Detalhe |
|---|---|---|---|
| RI-01 | 07-15 | **pandas fixado `>=2,<3`** (2.3.3) no env-main | pip resolveu 3.0.3 (major novo); reprodutibilidade > novidade. Lock refeito |
| RI-02 | 07-15 | **DoE/datasets persistidos NO REPO** (sem bucket) | 97 MB; identidade bit-a-bit Mac↔VM garantida por git |
| RI-03 | 07-15 | **BBOB canônico = `BBOB_F*`** | o token curto `BBOB1…` do código era o anômalo; renomeado + regenerado com hashes idênticos (o seed usa o índice) |
| RI-04 | 07-15 | **Seed do DoE = `SeedSequence((semente, problema_id))`**, sem alg_id | harmoniza D87×D90; ratificada pelo autor |
| RI-05 | 07-16 | **Fidelidade do c217 ACEITA 9/10** (a 1ª validação D97) | mecanismo de confiabilidade correto; caveat do orçamento vira análise |
| RI-06 | 07-17 | **Faxina D1–D5**: âncora b3 ✓ · `geracao=ciclo` ③ b3 ✓ · **Balde C b4 {1,20,1,20}** ✓ · âncora c141 ✓ · DoE DTLZ2_d15 committado ✓ | D3 verificado adversarialmente na SPEC §6.2/§6.4 |
| RI-07 | 07-17 | **Estratégia da onda**: sessões em PARES/solos; **fidelidade em LOTE** no fim (dossiê); sem paralelo MATLAB×MATLAB (o `experiment.m` é compartilhado) | pisos∥R3 e MATLAB∥Python são os paralelos seguros |
| RI-08 | 07-17 | **Tudo no MAC até M7; a VM só do M8+** | mudança de plano do autor; R2/R3 pilotados no Mac |
| RI-09 | 07-17 | **`n_empates`→`n_contradicoes`** (1 quantidade, 1 nome) + `pred_confianca`=Error1 mantido (era fiel à §17.2) | doc-sync D6 executado (+ fix do bug do gen_bundles aninhado) |
| RI-10 | 07-18 | **N=20 dos pisos ONLINE cravado** (provisório até SUB-varN) | decidido pelo autor em sessão; SPEC §3.2 com justificativa em 4 pontos; verificado adversarialmente íntegro |
| RI-11 | 07-17/18 | **Rituais de coexistência**: faixas por sessão; ritual anti-mistura de commit (add+staged-check+commit em 1 comando); janela e103∥c154 com **committer único** | evoluíram do incidente F0-03 → b3∥c217fix → e103∥c154 |
| RI-12 | 07-17 | **SPEC/bundles/params = TERRITÓRIO DA TORRE** | regra reforçada após a sessão pisos editar a SPEC (sancionada, mas o canal correto é pára-e-loga → torre executa) |

## Agenda de execução pendente deste registro
*(⟦REESCRITA — DI-21/D-21, 2026-07-22⟧: a versão anterior listava 24 itens JÁ RESOLVIDOS —
auditada item a item pela DI-20; o custo dessa dessincronia foi horas de re-verificação.
Regra nova em vigor: ao cravar uma DI-N, riscar NA MESMA PASSADA os itens de handoff que ela
fecha, citando o commit.)*

1. **Julgamento de fidelidade do autor, EM LOTE (D97)** — os 13 configs MATLAB + c262/c154 + c122.
   Insumos prontos: `DOSSIE_FIDELIDADE_R1.md` (item 1), as notas DI-20.4, os handoffs por cartão.
   Inclui os pontos priorizados: DI-07b (desalinhamento ~24,8% do e74) e a armadilha do sentinela
   `acc=1` p/ classe ausente (c122, handoff §achados).
2. **⟦REORDENADO — autor, 2026-07-22: "quero continuar a implementação no Mac"⟧**
   **Próximo: R3-c149** (env_main, Mac — RI-08) com o TIMEBOX da D-20 ativo, depois **e81**
   (env próprio, pins satisfazíveis no Mac — provisionamento do autor). A reordenação é SEGURA:
   os cartões R3 são independentes entre si (só dependem do R3-00 ✅ + lições do c122 ✅, ambas
   propagadas), e a única dependência de ordem que existia — ratificar o cache-hit×arquivo antes
   de c149/e81 — foi FECHADA na DI-21. Bônus: antecipar o c149 antecipa a decisão DEF-N4
   (manter/dropar o BNN), que a D-20 já mandava resolver ANTES do M7.
3. **Janela VM (quando o autor provisionar env_b5/env_c311):** R3-b5 (b5r/b5m) → c311 →
   piso-off — os cartões leem a cadência NORMATIVA e o CONTRATO já atualizados.
4. **M7 (PORTÃO):** piloto §22.5 + o hardening restante: D-17 (endurecer o check de RNG do R2-00 —
   molde do R3-00 pronto), sub-varN, decisões de custo D-2/D-3 do M7, revisitar D-18 (load_sonda).
5. **Antes da M8:** ligar `enable_bucket` no despachante (o repasse de kwargs já está — D-06);
   provisionar VM sem toolchain C++ (D-16c, SPEC:2764) e validar o `is_run_done` bucket-aware
   (D-03) com credenciais reais.

---

## PARTE A37 — 📄 O LOTE V3 DE DOCUMENTAÇÃO (T11, 2026-07-30)

> Os itens de doc do `T11-PLANO-CONSOLIDADO.md` §6 + §12-📄. Cada um foi
> **RE-MEDIDO** antes de virar texto — nesta campanha 10 erratas nasceram de
> "verifique antes de escrever", e copiar a afirmação do plano teria propagado
> as que estavam erradas. Onde o dado não existe, está dito que não existe.

### A37.1 · ERRATA A30 — o c122 GRAVA `fe` no evento `sonda` ✅ MEDIDO

A DI-42 afirmava que o c122 **não** gravava o `fe` no evento da sonda. Medição
nos ⑥ da rodada-42:

| | |
|---|---|
| eventos `rec='sonda'` do c122 **com** `fe` | **3.981** |
| **sem** `fe` | **0** |

Exemplo: `{"rec":"sonda","geracao":1,"fe":76,"n_pontos":2000,…}`. A afirmação da
DI-42 está **errada** e fica retificada aqui: o `fe` — que é o eixo de
comparação entre algoritmos — sempre esteve lá.

### A37.2 · R4#10 — dominância sobre a ① é LOSSY ✅ MEDIDO

Schema real das camadas (lido com `pyarrow.parquet.read_schema`):

| camada | colunas de objetivo | tipo |
|---|---|---|
| ① `__real.parquet` | `f0`, `f1`, … | **`float`** (float32) |
| ⑦ `__final.parquet` | `f0`, `f1`, `f2` | **`float`** (float32) |

**Regra de leitura R4#10.** Qualquer cálculo de **dominância / não-dominância /
front** feito a partir da ① ou da ⑦ opera sobre valores em **float32**, enquanto
o algoritmo decidiu em **float64**. Duas soluções que o algoritmo distinguiu
podem sair **empatadas** no parquet, e o front recomposto pela análise pode
diferir do front que a busca de fato viu. Isso **não é bug** — é a política D53
de export (float32 + 3 casas) valendo, e não se muda (está no NÃO-CORRIGIR:
"mexer no D53/float32"). O que se faz é **declarar**: toda métrica de dominância
da R4 carrega essa ressalva, e comparações no fio da navalha (diferenças abaixo
da resolução do float32) não são conclusivas.

### A37.3 · Glossário p0/p1 do b4 — NUNCA inverter

`p0` e `p1` do b4 **não** são "probabilidade da classe 0/1": são as taxas de
erro medidas em `CSEA.m:75-78` sobre o conjunto de teste, com semânticas
distintas e **não intercambiáveis**. O glossário está gravado no
`man.sigma_dict` do próprio run (é lá que o leitor da ③ vai procurar), junto com
a `REGRA_DO_ROTULO`. Trocar os dois derruba a contagem de acertos de **6.268
para 1.252** — é destrutivo e está no NÃO-CORRIGIR.

### A37.4 · `lnum` do c217 — DOC-SYNC, não mensurável hoje ⚠

O bundle identifica `lnum ≡ |Pmid|` (=13 para N=50) e usa `batch = ⌊lnum/2⌋`; o
dado mostra `batch = ⌊|Pbest|/2⌋`, com `|Pmid| = 2⌊|P|/8⌋+1`. As duas grandezas
**coincidem em N=50 e divergem na rampa** (|P|=22 ⇒ |Pmid|=5, |Pbest|=6).

O que a rodada-42 permite dizer, medindo o campo `lote` dos 9.078 eventos
`c217_gen`:

| `lote` | ciclos |
|---|---|
| 1 | 9.013 |
| **3** | **1** |
| 6 | 64 |

O lote 3 **existe** (1 ciclo), o que é consistente com a leitura
`⌊|Pbest|/2⌋` na rampa. Mas **`|Pmid|` e `|Pbest|` não são logados**, então a
ambiguidade **não pode ser resolvida pelo dado da s42** — fica como doc-sync
para a torre, e vira mensurável na M8 se alguém logar as duas grandezas. Com 30
sementes × D=2 as células de rampa se multiplicam por 30, então o item deixa de
ser marginal.

### A37.5 · Os 6 números publicados (E-09/D16) — o que NÃO se mexe

- **χ² do moead_media é PSEUDORREPLICADO** — a unidade independente é a célula,
  não a linha; o teste como publicado infla o n. Ressalva de leitura, não
  recálculo.
- **Endpoint do e103: 200→100 / 10→5**, conforme corrigido na F5.
- **NÃO aplicar a "correção" 0,05→0,10** do e103: a "correção" é que está errada
  (erro de 2×). Está no NÃO-CORRIGIR como "fantasia e103".

### A37.6 · Itens que ficam ABERTOS e por quê

| item | por que não fechei |
|---|---|
| SPEC L.8 do e74 pós-fix DI-45 | a SPEC é **território da torre (RI-12)** |
| D7/`iteration_seed` na SPEC §D62 | idem |
| caveats 1-24 da F5 §2.3 → dossiê | destino é a **dissertação**, não o repo |
| OP-1..OP-7 completos | OP-6 entrou no G3 (higiene do `--force`); os demais são **registro de OPERAÇÃO** (rompimento do teto 48 h na janela final, atribuição mista do c238) — factuais do autor, não meus |

### A37.7 · O que este lote NÃO tocou, de propósito

O número "~min-1h" do RUNBOOK **já estava corrigido** (`RUNBOOK:264` traz
"medido na s42, **0,87–2,99 h por célula (média 1,47 h)**"), então não há o que
fazer — é o mesmo número da correção da DI-40. Registrado para ninguém
"consertar" de novo o que já está certo.

---

## PARTE A38 — 🔍 A VARREDURA ADVERSARIAL E O QUE ELA ACHOU (T11, 2026-07-30)

> **Por que existe.** O autor pediu uma auditoria de tudo que a campanha
> produziu, com uma pergunta específica: *"há algoritmo testado ANTES do seu
> estado final de código?"*. Rodaram 6 auditores independentes read-only
> (commits×plano · suíte · dados · docs · reprodutibilidade dos números · os
> próprios gates) sobre 42 commits, 619 testes e 744 células. Saíram **78
> achados brutos** (4 CRÍTICOS · 18 ALTOS · 33 médios · 15 baixos · 8
> cosméticos). A fase de refutação adversarial processou 27 de ~156 votos antes
> de ser encerrada por orçamento, então **cada achado tratado abaixo foi
> reproduzido À MÃO antes de virar código** — nesta campanha 13 erratas
> nasceram de "verifique antes de escrever", e 3 delas eram falso-positivo de
> gate meu.

### A38.1 · O commit `4796a03` — o buraco de registro que a varredura achou

`4796a03` ("T11-P0") tocou **5 arquivos de código** e não tinha **uma única
linha** em documento nenhum da campanha, violando a regra do próprio
`T11_STATUS`. O que ele fez, registrado agora:

| arquivo | o quê |
|---|---|
| `scripts/gates_proveniencia.py` | o G-7 passou a varrer o ⑥ em **PROFUNDIDADE** — aferir PRESENÇA da chave, não POSIÇÃO |
| `claude_code_context/artifacts/contrato_61.json` | os 3 falso-positivos saíram do contrato |
| `src/b3_instrument.m` | `adapt_delta_V` DERIVADO (sem tocar a árvore vendorizada) |
| `src/experiment.m` | `sigma_dict` dos 4 pisos DECLARADO como `nao_se_aplica` |
| `tests/test_gates_g6.py` | os testes do gate novo |

E o **erro procedural** que ele contém, declarado: o b3 e os 4 pisos estão na
lista Onda-0 "SEM pendência por-algoritmo" do plano, logo mexer neles foi
**fora da FASE A**. O D81 mandava *parar e perguntar* diante de gate vermelho
inesperado, e eu implementei. Os campos são contratados (SPEC §6.1:2881 exige
`adapt_delta_V` do b3; o CONTRATO §5 lista `sigma_dict` no ⑤), então reverter
deixaria o repo violando a SPEC — ficam, com o erro de processo assumido.

### A38.2 · Os 4 CRÍTICOS — todos falso-verde, todos meus

1. **O portão dava VERDE com INCONCLUSIVO.** `vermelhos` só recebia
   `ok is False`; inconclusivo saía `return 0`. A doutrina B-07 valia só para o
   emoji, não para o veredito nem para o exit code — **e é o portão que
   autoriza o disparo**. Agora `0`=verde · `1`=vermelho · `2`=inconclusivo.
2. **A guarda G-8 era cega à raiz.** O `os.walk` estatava os FILHOS de
   `data/experiments` e nunca o diretório-raiz; uma subpasta que nasce e morre
   muda o mtime da RAIZ. `test_drivers_b12` escrevia em **produção a cada
   suíte** com a guarda verde. Ao consertar, a guarda passou a acusar o
   **próprio controle dela** — que também plantava arquivo na produção. Ambos
   hermetizados.
3. **O G-1 não tinha controle-positivo.** O critério de aceitação é "1 quimera",
   e a varredura devolve **0**: gatear `batch/c149/ZDT4/s42` dá VERDE. Sem o
   controle não havia evidência de que o gate soubesse reprovar. Entrou uma
   quimera **sintética** + o controle simétrico.
4. **O G-1 explodia** em parquet de 0 byte e derrubava o censo inteiro com
   traceback — as células seguintes nem eram gateadas.

### A38.3 · A auditoria de STALENESS — a pergunta do autor, respondida

Método: fecho de imports por AST × `git log -1` por arquivo × hora de cada teste.

| eixo | veredito |
|---|---|
| **Smokes** | ✅ 0 stale (testados 11:10–11:43; última mudança de dependência 10:02) |
| **Pares G-6** | 🔴 **9 de 10 STALE** — provados até 00:18, e o `standalone_harness.py` mudou às 08:12 |

O diff que os invalidou é `115 insertions, **0 deletions**` (puramente aditivo),
e a re-prova confirmou: **c122 voltou com o MESMO ① sha256 da prova anterior**
(`be06b54124e9c100`) — a sonda estratificada não perturbou a busca. Mas isso é
resultado, não era garantia. **Lição virou processo:** a re-auditoria de
staleness passa a ser o ÚLTIMO passo antes de declarar conformidade.

### A38.4 · Achados que NÃO viraram código, e por quê

| achado | desfecho |
|---|---|
| `b1/WFG1` perdeu **39 de 413 gerações** por splice — irrecuperável nas cópias locais | **do autor** — e o V2 já re-roda exatamente essa célula |
| wrapper do gatilho do `adapt` (A3/I-05 item 4) nunca implementado | **declarado**: é cirurgia vendorizada ⇒ âncora + re-lacre + ~90 min de nova prova. A cadeia A8 já é observável na CAUSA (`flag_vetores_degenerados`) e no EFEITO (`p_wrong_stats`≡0) |
| 33 médios + 15 baixos + 8 cosméticos | **não entraram** nesta rodada — pela nota dos próprios auditores não bloqueiam a campanha; ficam no handoff |

---

## PARTE A39 — 🔬 O DIAGNÓSTICO DOS 56 RESIDUAIS (T11, 2026-07-30, noite)

> Os 22 achados de maior gravidade da varredura foram tratados no mesmo dia. Os
> **56 restantes** (33 MÉDIO · 15 BAIXO · 8 COSMÉTICO) nunca tinham passado por
> refutação — a fase adversarial processou 27 de ~156 votos antes de ser
> encerrada por orçamento. Um agente cético dedicado os verificou **um a um**,
> read-only, sequencialmente.

### A39.1 · O placar

| classe | n | o que significa |
|---|---|---|
| **FALSO_POSITIVO** | **6** | não reproduz, ou é comportamento intencional documentado, ou leitura de dado velho |
| **SÉRIO** | **7** | pode produzir dado errado, perda de dado, ou afirmação falsa no dossiê |
| **GATE_CEGO** | **9** | não corrompe dado, mas deixa uma verificação incapaz de reprovar |
| **OPCIONAL** | **34** | estilo, redação, duplicação, processo já assumido |

**Fato que o cético levantou primeiro:** o HEAD avançou **13 commits** entre a
medição da varredura e a refutação. Ele verificou contra o HEAD, não contra o
snapshot — e 3 dos 6 falso-positivos são exatamente achados **já corrigidos**
nesse intervalo.

### A39.2 · O que foi CORRIGIDO (commit `947cfc2`)

| # | achado | conserto |
|---|---|---|
| **#42** | `accept.py` e `auditar.py` **ignoravam `--data-root`** e liam sempre `data/`. PROVADO: gatear célula INEXISTENTE num sandbox devolvia `accept=VERDE · auditar=VERDE`. Importa no **gate F4**, que roda o portão sobre o corpus CONSOLIDADO | `auditar` ganhou a flag (a função já a recebia); o `accept` vira **NÃO-AFERÍVEL** fora de `data/` — admitir que não sabe, em vez de mentir verde |
| **#48** | G-1: `frac = n_bit / len(achados)` escondia ids ÓRFÃOS no denominador. ③ com {0,777,888} × ① com {0} fechava `frac=1.000000` sobre UMA linha | denominador passa a `len(marcadas)`; o detalhe reporta quantas são órfãs |
| **#49** | G-7 aceitava `params=[]`, `0`, `False`, `'None'`, `'  '` como "⑤ 6/6 chaves" | `_vazio()` — vazio de coleção, zero, False e 9 placeholders textuais. 14 casos de borda verificados |

### A39.3 · ERRATA 16 — o `e0_trace` degenerado do b1

**Achado #20, reproduzido ao dígito:** em **597 dos 1.029 ciclos** em que "a 1ª
geração interna venceu" (o número que sustenta a leitura do VD-b1), o
`e0_trace` é **CONSTANTE** — o GA interno de aquisição rodou N gerações e o
melhor EI **nunca melhorou**. E as duas células da tese do "efeito concentrado",
`BBOB_F37` e `BBOB_F49`, são **85,8%** e **87,1%** degeneradas.

**O que isso muda.** Eu concluí que o torneio defeituoso pesa "~6,1% dos ciclos,
concentrado em F37/F49". Nessas células, "a 1ª geração venceu" quase sempre
significa **"nenhuma geração melhorou nada"**, não "a 1ª foi boa". **O número
SUPERESTIMA o peso do torneio.**

**O que NÃO muda.** O dado está correto e é válido; o que estava errado era a
minha leitura. E o achado **reforça** a classificação 🟠 IMPL → CÓDIGO do
VD-b1 (o torneio é ainda mais inerte do que a ERRATA 10 já dizia), não a
contradiz. **Nada muda no b1.**

**Escopo: 1 config.** Medido — `e0_trace` é emitido **só pelo b1** (é a
instrumentação do GA interno do ParEGO). Nenhum dos outros 23 tem o campo.

### A39.4 · O que foi ARQUIVADO — decisão do autor em 2026-07-30

| bloco | decisão | motivo |
|---|---|---|
| **População contaminada** (#21,#22,#23,#25) — números medidos em `data/experiments` (744 células) em vez das 666 oficiais | **MANTER como está** | não afeta código nem campanha; **os resultados que vão para a dissertação saem do BUCKET**, não desta pasta |
| **7 GATE_CEGO restantes** — incl. testes que nunca rodaram em ambiente nenhum (#7,#8) e `python tests/test_gates_g6.py` dando 45 testes contra 56 via discovery | **ARQUIVAR**, revisitar no M8 | nenhum produz dado errado; são cobertura de teste |
| **34 OPCIONAL** | **ARQUIVAR com nota** | o cético mediu que **16 deles** se resolvem com uma regra de redação: trocar contagem absoluta por `≥N` na prosa |

### A39.5 · As lacunas que o cético DECLAROU

Registradas porque uma lacuna não declarada é pior que um achado:
1. **Não gateou o corpus oficial das 666** (layout incompatível com
   `--data-root`) — logo refutou o `#47` por população errada, **não por
   medição**. É a lacuna mais importante.
2. **Nenhum comportamento MATLAB foi executado** — aceitou os 19 hashes do G-6
   registrados no `T11_STATUS:80-84` sem reproduzi-los.
3. **#42:** provou o mecanismo, mas não achou log de qual ferramenta gerou a
   tabela de smoke desta sessão.
4. #17/#18 verificados por **amostragem**; #1 com denominador divergente.

---

## PARTE A41 — T12: o acabamento final (2026-07-31)

Cartão `handoff/T12-CARTAO.md`. Fecha os 8 bloqueadores da validação de fidelidade do T11, as
2 causas-raiz da PARTE A40 e a conversão dos gates decorativos. Doutrina do cartão, cumprida em
todos os itens: **todo fix exige controle negativo — um teste que REPROVA no código de ontem e
PASSA depois — e todo campo de instrumentação exige asserção sobre o VALOR medido em run real.**

### A41.1 — O placar

| item | bloqueio | veredito | prova de valor (run REAL) |
|---|---|---|---|
| T12.1 | BL-01 `pmid_ids` | corrigido | **426/426 com id ≥ 0** (era 426/426 = −1) |
| T12.2 | BL-02 `flag_vetores_degenerados` | corrigido | **381/381 não-nulo** (era 0/1.144) |
| T12.3 | BL-05 `y_treino_dist` | corrigido | 42/42 com `n = \|TrainIn\| ≠ \|Input\|` (era `(0,0,n)`) |
| T12.4 | BL-06 finalProbe sob teto | corrigido | bloco final na iteração truncada, ①②③ bit-idênticas |
| T12.5 | BL-09 `fflush` | **NÃO APLICADO — medido** | ver A41.3 |
| T12.6 | BL-08 pin `scipy` | pinado 1.17.1 × 3 artefatos | sha256 do lote de Owen travado |
| T12.7 | gates decorativos | convertidos → **acharam o BL-03** | **11.000/11.000** com `pred_score` |
| T12.8 | varredura de VALOR | **achou BL-04 e BL-15** | ⑤ do c217 com as 3 chaves corrigidas |

Suíte: **627 → 671, 0 falhas.** 6 commits, todos com controle negativo demonstrado.

### A41.2 — A cadeia A8, medida em célula real pela primeira vez

O `flag_vetores_degenerados` foi o campo que a F5 pediu para fechar o laço do congelamento do
b5m e que a T11 entregou morto. Com o fix (os vetores vivem no EVOLVER, não no `problem` —
`BaseEA.py:182`), dois smokes reais dão o par de controle que faltava:

* `off/b5m/**DTLZ2**/s42` (célula SADIA): `n_norma_zero = 0` em 381/381, normas ≈ 1,
  `n_substituicoes` 3–12 por geração (Σ **7.769**), `P_wrong.max` até 1,0.
* `off/b5m/**DTLZ3**/s42` (célula CONGELADA): `n_norma_zero = **105 de 105**` em **381/381**,
  `norma_min = norma_max = 0,0`, `n_substituicoes = **0**`, `P_wrong.max = **0,0**`.

A cadeia inteira — `adapt` → norma 0 → PBI NaN → `P_wrong ≡ 0` → zero substituições — deixa de
ser inferência de bancada e passa a ser leitura direta do ⑥. **Fecha também o BL-22** (o smoke
b5m da célula congelada que nunca existira). ⚠ O cartão esperava o congelamento no DTLZ2; o dado
disse o contrário e o dado prevaleceu — as congeladas são DTLZ3 e DTLZ1
(`f5/t11/relatorios_config/b5m.md`).

### A41.3 — BL-09: o bloqueio não sobreviveu à medição, e o fix certo é outro

Com o engine MATLAB disponível, os dois modos de perda foram medidos em vez de aceitos:

1. **`fflush` não existe no MATLAB** (`exist('fflush') = 0`). O `jsonl_line` não tem `try/catch`:
   a "1 linha" prescrita **derrubaria todo run MATLAB da campanha**. É função do Octave.
2. **Perda de cauda: REFUTADA.** Uma linha de 64 B sobrevive a `kill -9` com o processo em
   busy-loop. O `fprintf` para arquivo em `'a'` não é bufferizado.
3. **SPLICE: CONFIRMADO — e o fix é ATOMICIDADE, não flush.** 4 escritores × 300 linhas de
   6,4 KB: `fprintf` **30 partidas**, `fwrite` **26**, `java.io.FileOutputStream` (append) **0**.
   Em 5 repetições do caso de produção: bytes SEMPRE 7.765.968 e newlines SEMPRE 1.200, com
   0/10/36/20/10 partidas — **nada se PERDE; o que quebra é a fronteira da linha.**

**Nenhum código mudou**: o splice exige ≥2 escritores no MESMO ⑥, e hoje o ⑥ do MATLAB tem
escritor único. A decisão de trocar o writer fica com o autor (§7(d) do cartão), com o caminho
provado e local.

### A41.4 — DI-41 (T12.D2): retificação formal do N=20 — a DI-39 prevalece

**A contradição.** A **DI-32/A2** (2026-07-23) declarou *"N=20 dos pisos online = DEFINITIVO;
SUB-varN vira sub-estudo OPCIONAL do M11"*. A **DI-39** (2026-07-25), **posterior e do mesmo
autor**, declarou o N=20 **provisório** e o **SUB-varN pré-requisito do M8**. As duas ficaram
vivas no repositório, e `cards/INDEX.md:67` seguia ⬜ sem qualificar qual valia.

**Decisão do autor (2026-07-31, T12.D2): a DI-39 PREVALECE.** Por posterioridade e porque a
justificativa dela é a mais forte — dispensar um pré-registro *depois* de ver o resultado é
metodologicamente mais frágil do que mantê-lo, e o custo de refazer os 4 pisos é **~3,3 h-core**,
desprezível contra o risco de descartar 25 células por piso.

**Textos varridos** (o estado vinculante passa a ser único):
1. `REGISTRO_DECISOES_IMPLEMENTACAO.md` (PARTE A20/A2) — marcado como superado, mantido como
   registro histórico.
2. `claude_code_context/40_subestudos/varredura_N_pisos.md` — epígrafe corrigida **e também em
   `gen_bundles.py`**, que é a fonte real dela (o bundle é GERADO; corrigir só o `.md` seria
   desfeito na próxima regeneração).
3. `cards/INDEX.md:67` — `SUB-varN` passa a declarar **PRÉ-REQUISITO do M8**.

A SPEC (`:1682`) e o bundle `01_regras_globais.md` já diziam *"valor provisório cravado"* —
estavam corretos e não precisaram de mudança.

### A41.5 — O que fica ABERTO para o autor (nada disto foi decidido sozinho)

* **(a) `moead_media`** — o `flag_vetores_degenerados` nunca foi escrito no `piso_offline.py`
  (0 ocorrências): é item NOVO, não conserto. O `MOEA_D` (mode 12) **tem** `reference_vectors`
  (`MOEAD.py:111`), então o contraste piso × b5 sobre a causa do A8 é mensurável.
* **(b) Contaminação de estado global (PRÉ-EXISTENTE)** entre teste-com-mock de BoTorch e run
  REAL no mesmo processo — sem risco para a campanha (1 célula = 1 processo); mitigado nos testes
  novos por subprocesso.
* **(c) A coleta do `flag_vetores_degenerados` segue no replay pós-busca** ⇒ valor constante nas
  gerações, contra o que o comentário do próprio código promete.
* **(d) O writer ⑥ do MATLAB não é atômico por linha** — ver A41.3.
* **(e) O `numpy` do env_main segue solto** (`>=2,<3`) enquanto o BL-08 exige o par
  numpy 2.4.6 **+** scipy 1.17.1.
* **T12.D1 (BL-07) — o piso de ruído: EM ABERTO, aguardando o autor.** Medição dos 15 pares
  Mac×vm3: **7 são bit-idênticos** (Δ = 0,0 — os 4 pisos puros + b4 + c217 + e103, isto é, os
  configs que NÃO ajustam surrogate por otimização numérica) e **8 divergem**, com **6 acima do
  piso O-18 (HV ≤ 1,55%)**: `e74/DTLZ2` 10,16% · `c238/MMF1` 9,69% · `e74/ZDT1` 3,54% ·
  `e74/MMF1` 2,93% · `c141/MMF1` 2,31% · `b1/MMF1` 2,10%. **Em IGD+ — o endpoint PRIMÁRIO (D70) —
  o piso declarado nem existe**, e é lá que está o pior número: `c238/MMF1` **80,03%**.
  A campanha passa a rodar em **9 máquinas** (2 delas Python-only), o que torna a máquina um
  confundidor **correlacionado com o config**. Recomendação levada ao autor: bloquear por
  **(problema, stack)** — toda comparação da R4 é intra-problema, então o contraste vira
  intra-máquina e o confundidor some por construção — **mais** o `artifacts/piso_ruido.json` por
  (config, problema) como rede de segurança, **mais** 2 células-calibradoras
  (`c238/MMF1/s42` e `e74/DTLZ2/s42`) em cada uma das 9 máquinas, para não extrapolar um piso
  Mac×vm3 a 7 máquinas nunca medidas.

---

## PARTE A42 — T13: as pendências do T12 + a campanha em 9 máquinas (2026-07-31)

Continuação direta da PARTE A41. Executada em série **B → C → A** por instrução do autor, para
que o repasse à torre já saísse com tudo dentro.

### A42.1 — DI-42 (T12.D1): o piso de ruído, RESOLVIDO por desenho

**A decisão do autor (2026-07-31).** *"Vamos assumir esse problema."* Cada máquina roda **TODOS
os experimentos em algumas sementes aleatórias**; a dissertação reporta média/mediana das 30, e a
agregação transforma a divergência entre máquinas em ruído aleatório.

**Por que isto FECHA o BL-07, e não o adia.** A divergência cross-máquina é real e está medida
(15 pares Mac×vm3: 7 bit-idênticos, 6 acima do piso O-18 de HV ≤1,55%, e o `c238/MMF1` com
**ΔIGD+ 80,03%** no endpoint PRIMÁRIO). O que a torna perigosa não é a magnitude — é a
**correlação com o tratamento**. Sob a regra **O-16** ("um config, uma máquina") a máquina era
CONSTANTE nas 30 sementes de um config, isto é, um **offset sistemático** que nenhuma média
dilui. Alocando por SEMENTE, a máquina varia DENTRO de cada config entre repetições: vira ruído
aleatório, e é exatamente o que a mediana de 30 dilui. **A decisão inverte o regime, e é a
inversão que resolve.**

**Consequência normativa: a O-16 está APOSENTADA para RESULTADO** (segue valendo para a tabela
de TEMPO do M7 — comparar wall entre algoritmos ainda exige a mesma máquina). Aposentada no texto
do driver (`scripts/lote3s.sh`), não só em prosa: um driver que documenta o oposto do desenho é a
armadilha doc×código que este projeto já pagou 3× no mesmo dia.

**Pendência que a decisão NÃO resolve:** sem o `host` no ⑤ não havia como *demonstrar* que a
diluição aconteceu — resolvido no C2 abaixo.

### A42.2 — O que o bloco B entregou (o único que muda NÚMERO é o B4)

* **B4 · `numpy==2.4.6`** nos 3 artefatos. O BL-08 exige o PAR `numpy` + `scipy`; o T12 pinou só
  o scipy (era o autorizado) e protegia metade. Com 9 máquinas são **8 resoluções novas de
  `pip`**, e divergência de versão é sistemática por grupo de máquinas — a diluição por semente
  **não** a desfaz. É o único item de B/C que toca número.
* **B1 · o campo no `moead_media`.** Confirmei que o `MOEA_D` (mode 12) herda o
  `manage_preferences` do `BaseDecompositionEA` (`BaseEA.py:244`), que chama
  `reference_vectors.adapt(...)` a cada `iterate()` — **o piso está sujeito à MESMA cadeia A8 do
  b5m**. Medido: `moead_media/DTLZ1` (46 s) colapsa **14 de 105** vetores, onset na geração 12;
  `DTLZ3` (53 s) colapsa **1 de 105**, onset na geração 2. **O piso colapsa PARCIALMENTE**, contra
  o colapso **TOTAL** do `b5m/DTLZ3` (105 de 105). ⇒ **O achado do b5m SOBREVIVE ao contraste da
  ablação**, e isso só é afirmável porque o campo passou a existir no piso.
* **B2 · a série por geração.** O campo era colhido 1× no replay pós-busca e o mesmo valor ia
  carimbado nas 381 gerações. Agora é amostrado na cadência do `iterate()` (a cadência real do
  `adapt`). Medido no `b5m/DTLZ1`: gerações **1–11 sadias com 1.042–1.093 substituições cada**;
  geração **12** com 105/105 colapsados e **0 substituições**; assim até a 381. Soma **10.479
  substituições, TODAS antes do onset, ZERO depois** — a cadeia A8 inteira, com o instante.

### A42.3 — O que o bloco C entregou (nada disto toca decisão de algoritmo)

* **C1 · o BLOQUEADOR real das 9 máquinas.** `interpreter_for_alg` resolvia o interpretador por
  caminho ABSOLUTO de macOS. Os 6 configs de venv próprio **nunca rodaram fora do Mac** — o perfil
  do driver dizia isso em voz alta (*"mac: TODO o venv-próprio — únicos venvs do projeto"*). Passa
  a resolver por CANDIDATOS pelo NOME do venv, a identidade que o gate G-3 já usa.
* **C2 · a MÁQUINA viaja com o dado.** `host` + `plataforma` nos 3 writers de ⑤. Antes: **zero**
  ocorrências de `gethostname`/`uname` em `src/`, e a única atribuição era a `maquina_dona` do
  censo — DERIVADA do roster planejado, que rotula errado toda célula recuperada noutra máquina.
  A arquitetura é normalizada no lado MATLAB (`maca64`→`arm64`) para a R4 não precisar de dois
  vocabulários. Os **6 portões de proveniência seguem verdes** com as chaves novas.
* **C3/C4/C5 · escalonamento e relatório abertos.** Censo sem `sys.exit` em host novo;
  `LOTE_PARES=todos` derivando o roster do ARTEFATO (medido: `LOTE_MAQ=vm7` derivou as 695
  células); lista de máquinas do relatório derivada do disco.

### A42.4 — ⚠ NOVE bloqueadores do `bloqueios.json` NUNCA foram tratados

O cartão T12 cobriu 13 dos 22. Ficaram **fora do cartão e sem tratamento**, todos baratos:
**BL-11** (treed_media: I/O do checkpoint dentro de `tempo_busca_s`) · **BL-12** (b4: 3 números de
calibração que não reproduzem) · **BL-13** (`geracoes_derivadas` declara o operador do NSGA-II
para os 4 pisos) · **BL-14** (`frente1_excede_pop` usa `N_nominal` em vez de `N_efetivo`) ·
**BL-17** (`contrato_61` não cobre a linha dos pisos) · **BL-18** (e103: `espaco_modelo` NULL na
busca e 'cru' na sonda, na MESMA ③) · **BL-19** (b4: 2 edições de doc da F5.4) · **BL-20**
(sobol_batch: `nota_potencia_de_2` literal fixa) · **BL-21** (e81: `progress.py` lê `footers[-1]`).
**Não os fiz por estarem fora do cartão (D81), e os registro aqui para o autor decidir.**

---

## PARTE A46 — SUB-varN EXECUTADO: `N=20` CONFIRMADO + 3 achados (2026-08-01)

**O pré-registro da D65 foi cumprido.** A varredura `N∈{10,20,30,50}` × 4 pisos
online × 6 problemas × 5 sementes rodou (**440 células**, dataRoot fora do repo,
corpus do M8 intocado) e **CONFIRMOU o `N=20`** nas três faixas de `D`. Os runs do
`R1-pisos` já feitos são definitivos; zero re-execução. Relatório completo com os
números em `handoff/SUB-varN_RELATORIO.md`.

**A DECISÃO (delegada pelo autor após ver os números).** `N=20` nas faixas baixa
(`D≤5`), média e alta (`D≥20`). As 4 justificativas do cravamento de 2026-07-18
sobrevivem, e o dado acrescenta uma quinta: **`N=20` é o único valor factível nas
três faixas ao mesmo tempo.**

Duas alternativas foram descartadas com motivo:

- **`N=10`** vence em quase toda linha onde existe, **mas quebra o MOEA/D** — não
  degrada, quebra, em 30/30 células. Causa provada no fonte: `MOEAD.m:26`
  `T=ceil(N/10)` dá `T=1`, `:31` deixa a vizinhança com 1 coluna, e o `P(2)` de
  `:42` estoura. Como os 4 pisos são CASADOS por princípio de seleção
  (MOEA/D→decomposição é a régua de `b3`/`c122`/`b1`), perdê-lo custa a atribuição
  limpa do ganho ao surrogate. ⇒ **`N ≥ 11` é restrição estrutural.**
- **`N=30`** vence as medianas AGREGADAS da faixa média, mas é **artefato de
  agregação**: o 13,15 do agregado É o número do `moead`, e piso a piso o `N=30` é
  PIOR que o `N=20` no `nsga2` (21,96 × 16,23) e no `smsemoa` (17,81 × 14,75). Na
  faixa alta a margem agregada é de **3%**, que 5 sementes não separam — e
  fabricar um teste estatístico DEPOIS de ver o dado seria trocar o critério
  pré-registrado (mediana do IGD+) para caber no resultado.

**OS TRÊS ACHADOS que não estavam em lugar nenhum:**

1. **MOEA/D exige `N ≥ 11`.** O bundle §3.2 registrava o vizinho disto ("com N=20
   a vizinhança é T=2, mínima") sem notar que N=10 leva a T=1 e o algoritmo não
   roda. Eleito no papel, seriam 30 células mortas no meio do M8.
2. **`N=30`/`N=50` são infactíveis em `D=2`** (população > DoE de 21 pontos). A
   guarda `piso_init` trunca e loga — a célula RODARIA, com `N` efetivo 21,
   produzindo um ponto rotulado 30 que rodou em 21. As 40 células foram
   EXCLUÍDAS por desenho, não deixadas falhar.
3. **ERRATA no §6.3 do bundle/SPEC.** A tabela de `N` efetivo em M=3 afirma
   `{10,20,30,50} → {6,15,28,45}`. Medido no `UniformPoint` real do PlatEMO:
   **`{10,15,28,45}`** — o `10` está certo por construção (`C(H+2,2) ≤ N` com
   `H=3` dá `C(5,2)=10 ≤ 10`); o `6` seria `H=2`. Três dos quatro conferiam.

**CÓDIGO.** O `N` era literal em ponto único de `src/experiment.m`; virou
`piso_n_nominal()`, que lê `UA_DD_SAEA_PISO_N` e cai em 20 na ausência dela. Valor
inválido PÁRA (`ua_dd_saea:pisoNInvalido`) em vez de cair no default — o typo
`3O` produziria uma célula rotulada N=30 que rodou em N=20, contaminando
exatamente a comparação que a varredura faz. E `piso_n_origem()` grava no ⑤/⑥
QUAL caminho produziu a célula: o corpus oficial só admite piso com
`N_origem = CRAVADO`.

⚠ **`UA_DD_SAEA_PISO_N` deve ficar AUSENTE na campanha M8.**

**LIBERA:** a tag `m8-freeze`, que estava segurada esperando esta decisão.

## PARTE A47 — O DIA DO DISPARO: dois achados de determinismo, o recorte da 1ª onda, e a campanha no ar (2026-08-02)

**1 · Veredito final do stress de 12 h: ZERO falha algorítmica.** ~430 células/VM
(todas as stacks, todos os regimes, seed 2, `data_stress` isolado, teto artificial
de 7.200 s). Os 45 "failed" se decompõem SEM resto: **40 por dataset de tier
ausente** (o achado real — ver §2) e **5 por `motivo: teto_wall`** (abortos
SANCIONADOS no teto de 2 h: `batch/e81` ×3 e `main/c122/DTLZ4` ×2, só nas máquinas
de 16 jobs — contenção, não algoritmo; no teto real de 43.200 s fecham com folga).
Um caso operacional: `main/c238/DTLZ4` na vm3 pendurado 11,5 h com CPU 0 %
(a lacuna DI-35.5 — MATLAB sem teto de wall-clock — materializada). Morto a mão,
o lote fechou sozinho. **Regra operacional derivada:** célula MATLAB longa com
CPU ~0 % ⇒ `kill`; a re-passada do MESMO comando recolhe (resume, §4).

**2 · Datasets de tier: a lacuna e a geração.** O grid da campanha exige 95
tier-células/semente e os pares `{small-mvns, medium-*, big-*}` só existiam para
s0(parcial)/s42. Sonda de plataforma ANTES de gerar: **`x_hash` bit-idêntico
arm64↔x86_64** (PCG64/LHS estável, como o D87 promete) mas **`f_hash` DIVERGE**
(libm — `cos/sin` por ULPs). Consequência: geração nas 4 VMs (x86 idênticas), com
igualdade cruzada de hashes como verificação. Resultado: **724 gerados + 26
pré-existentes validados por hash = 750/VM em ~6 min**, contagens idênticas nas 4.

**3 · Segundo achado: OpenBLAS × contagem de threads.** O digest 4×4 REPROVOU —
em DOIS grupos perfeitos que coincidem com os tipos de máquina (32 vs 12 vCPU).
Diagnóstico completo: **58 arquivos divergentes, TODOS `WFG9 × big × s0–28`,
TODOS só no `f_hash`** (`x_hash` 100 % igual; a s42, vinda do git, idêntica).
Causa provada: a avaliação do WFG9 passa por `np.dot` (`problems.py:662`); com
threads livres a OpenBLAS particiona o GEMV de 50 k pontos e soma parciais em
ordem dependente do nº de threads; `medium` (2 k) fica abaixo do limiar de
multithreading. O gerador rodou SEM os pins que o driver exporta
(`lote3s.sh:236`). **DECISÃO DO AUTOR: divergência ACEITA** — cada máquina consome
exatamente as sementes que gerou e o CP valida cada arquivo contra o próprio
sidecar. Regras derivadas: (a) geração de dataset SEMPRE com os pins de thread do
driver (backlog pós-freeze: embutir no `doe.py`); (b) **na expansão D1, semente
migrada LEVA seus datasets junto — nunca regerar na máquina nova**; (c) a 1ª onda
(main+off) nem toca sweep-big: hoje o corpus em disputa não entra em nada.

**4 · P14/H1'.** Resume PROVADO nas 4: o comando literal do P10 com
`LOTE=CONFIRMA` deu `9 já tinham manifesto` + `grade VAZIA` + exit 0 — re-colar o
comando da campanha é sempre inofensivo. H1' (auto-updater): o knob
`matlab.addons.autoupdatecheck` NÃO EXISTE no R2025a Linux ("não aplicável —
anotar", como o próprio comando previa; erro registrado em `~/upd.log` das VMs).
Risco residual baixo: o runtime Linux não se auto-atualiza.

**5 · O recorte da 1ª onda (decisão do autor, minutos antes do disparo).** Só os
25 problemas principais em main+off: **main = 13 online (b1 b3 b4 c122 c141 c149
c154 c217 c238 c262 e7 e74 e81) + 4 pisos (nsga2 nsga3 moead smsemoa); off SEM
c311 (b5m b5r e103 moead_media)** = 21 pares × 25 = 525 células/semente = 15.750.
**c311 REMOVIDO DA CAMPANHA INTEIRA** — a 2ª onda (sweep+batch, a decidir) também
sai sem ele. Detalhe de driver que definiu a forma do comando: **o modo-mapa
SOBRESCREVE `LOTE_PARES`** (o artefato manda em SEEDS e PARES), então o recorte
exigiu modo manual — `LOTE_MAPA=0` + `LOTE_SEEDS` explícito com a MESMA partição
do mapa (vm1=0–10 · vm2=11–14 · vm10=15–18 · vm3=19–28,42, s42 por último).

**6 · DISPARO: 2026-08-02, 12:39–12:41Z.** Grades: 5.766/2.091/5.766/2.091 =
**15.714 células** (36 do P10 + 1 extra na vm3 já prontas), `bucket: LIGADO`,
`LOTE_ORDEM=semente`, `setsid nohup` (sobrevive a desconexão — provado no stress
com o Mac desligado a noite inteira), guard anti-lote-duplo e guards de
CID/PISO_N no próprio comando. Makespan previsto: ~215,5 h (vm1/vm3, 16 proc) e
~209 h (vm2/vm10, 6 proc) ⇒ término ~11/08. Painel a 4 min de voo: **347 ok · 0
failed** na frota, ordem semente-major visível. (Cosmético: o banner diz
`máquina=custom` no modo manual — o rótulo, não a máquina.)

**Backlog reafirmado:** `--force` re-roda a célula mas NÃO vira `sobrescrever=True`
no mirror (código≠docstring); teste SUB-varN em sessão única de MATLAB; pins de
thread dentro do `doe.py`.

## PARTE A48 — A 5ª MÁQUINA (vm4) E O DEFEITO DO SYMLINK: 75 células perdidas por um prefixo (2026-08-06)

**A expansão.** Conta nova (`ollem.anaileh`) provisionada ponta-a-ponta em 10
bateladas, do projeto vazio ao disparo. Três achados de infraestrutura:
(1) o gargalo real da conta trial é **`CPUS_ALL_REGIONS=12` GLOBAL** — as cotas
regionais de 32 são miragem, e o erro só aparece onde HÁ estoque; (2) N2 highmem
estava em stockout em TODAS as 28 zonas US naquele horário — a máquina saiu como
`n2-highmem-8` em `us-east4-a` e foi redimensionada a frio para
`n2-custom-12-98304` (12 vCPU / 96 G / 6 jobs — o shape das vm2/vm10);
(3) **a 5ª sessão MATLAB concorrente da licença `40904996` FUNCIONA** — abriu de
primeira, versão idêntica (`25.1.0.2973910`). O maior risco da expansão morreu
como fato medido.

**O defeito (meu).** O `venvs_m8.sh` do B-1 cria `env_b5`/`env_c311` via
micromamba e o doc afirmava "não há symlinks, o PATH é exportado" — **errado para
o harness**. `standalone_harness.py:312-317` resolve o venv pelo NOME varrendo
`~/python_venvs · ~/venvs · ~/Documents/python_venvs · /home/jupyter/python_venvs`;
`~/micromamba/envs` NÃO está na lista. Sem o symlink, a resolução cai no caminho
declarado no `envs.json` — o do **Mac** — e a célula morre com
`FileNotFoundError: /Users/gmello/Documents/python_venvs/env_b5/bin/python` numa
VM Linux. **Custo: 75 células da s10** (b5r 25 + b5m 25 + moead_media 25 — os três
algs do env_b5, uma semente inteira). Conserto: dois `ln -sfn`, aplicados **sem
parar o lote** (cada célula resolve o interpretador num subprocesso novo), com
prova via `interpreter_for_alg` devolvendo caminho Linux. B-1 do
`M8-BATCHES-OPERADOR.md` corrigido (symlinks + conferência PELO symlink, já que
`micromamba run` funciona sem ele e mascara o defeito).

**O que o censo de falhas revelou nas 4 irmãs (o contraste que validou o método).**
~87 % das "falhas" é `teto_wall` — a classe SANCIONADA, concentrada em
`c154`/`c262`/`c122`/`c149`, e que o próprio modelo já previa (`lote3s.sh:306`
atribui `ABORTO` ao `c154` com `fe>=371`; `lote3s.sh:319` classifica `teto_wall`
como "abortou", não "FALHOU"). O resto (~10 %, `checkpoint_em_andamento`) são
falhas numéricas legítimas do BoTorch — `ModelFittingError`, gradiente NaN,
`random_search_optimizer` sem óptimos. **`WFG1` aparece nas QUATRO máquinas, em
sementes diferentes**: é propriedade determinística do problema, não
infraestrutura — resultado científico, não defeito.

**Vazão medida (98 h de campanha).** A frota roda a **~55-60 % do ritmo-modelo**
(o modelo foi calibrado com medianas SEM contenção): 16-jobs a ~35 h/semente
(modelo: 19,6 h), 6-jobs a ~100 h/semente (modelo: 52 h). Projeção das 30
sementes: **~18-19/08**. **Decisão do autor: não parar nenhuma irmã** — a vm4
roda as últimas sementes programadas delas (s10, s14, s18, s42) com DUPLICIDADE
ACEITA; `colidiu_412` nessas sementes passa a ser esperado, não anomalia.
Recusada (por mim, com justificativa) a proposta de subir para 18/7 jobs:
oversubscription não cria núcleos, e esticar célula cara converte finalizadora em
`teto_wall` — progresso negativo.

## PARTE A49 — T15: OS 3 PROBLEMAS DE DADOS REAIS INTEGRADOS + FILA MATLAB + D0 (torre, 2026-08-13/14)

**Escopo cravado pelo autor (13/08, = D102.16/REAL-2.16):** RE21=25 · DDMOP7=26 ·
ESTOQUE40=27 em **21 configs** (13 online + b5m/b5r/e103 + 5 pisos) × 30 sementes =
**1.890 células**; SEM q10/sweep (futuro provável) e SEM c311 (consistente com A47).
Grid 20.850 → **22.740**. Frota-alvo do disparo (decisão de 14/08): **vm1 + vm5**.

### A fila MATLAB do DDMOP7 — de "nunca executada" a fechada NO MESMO DIA (13/08)
Pré-flight VERDE no Mac (pin exato `25.1.0.2973910`); congelamento dos 120 sorteios em
**7 segundos** (init é amostragem pura — Mundo 1; PF-1 estocástico max|Δ|=1,89; PF-1b
zeros 0,494; validação independente da torre no CSV: 22.320×17, sorteios distintos);
derivação B-24/25 toda verde (DoE 30×186 sha `9fc4268d…` · dataset 30×526 sha
`03056b6e…` · disjunção ponto-a-ponto · KS p=0,915); **B-26 VERDE após 2 defeitos
REAIS medidos e consertados** (o `.p` EXIGE `DDMOP7('init')` 1×/processo antes de
'value' — init não consome o contador de 600, lote pós-init é ponto-a-ponto fiel a
chamadas individuais [3 sondagens]; e `exist()` devolve 2 OU 6 p/ .p conforme o pwd);
**B-27 VERDE** (ponte com Engine real: 526/526 hard-stop exato, 526 soluções únicas,
12 cache-hits a 0 FE; 2 defeitos no caminho: pymoo ausente no venv; BridgeTimeout do
lote de 186 → fatiamento ≤64, valor-idêntico por pureza D102.11). Medido: **~6,3 s/FE
também no Mac arm64**.

### Os commits do T15 (suíte verde antes de cada leva)
`f21533b` T15.1 opt-out sonda (ordem inegociável: ANTES do append; controle negativo
em worktree) · `207692f` T15.2 catálogo+guardas 25→28+régua (com **REAL-2.15=opção A
do autor e ERRATA MEDIDA**: nadir f2 da fase 1 = 468/690 = 0,6783 — os docs do pacote
citavam 0,44493 de memória, padrão D85; venceu a fonte `ddmop7_probe_v6.csv`) ·
`31b72fc` T15.3 sonda-None nos 10 runners+gates (agente re-medido 76/76; matou crash
latente do braço DESLIGADA de c311/treed) · `bceae0e` T15.4/5 artefatos (DoE congelado
→parquet com −0 preservado e controle de adulteração; CSVs congelados versionados;
materialização RE21/ESTOQUE40; sonda dos 2 com DDMOP7 pulado pelo opt-out EM PRODUÇÃO)
· `ed98eaa` T15.6/8 delta aplicado (kit filtrado 1.890 com **remap de 630 envs** —
achado vermelho do recon: o delta usava nomes de env inexistentes; dry-run T-20 =
22.740 run_ids únicos) + decisions.json 48→66 (D101+D102.1-.16) · `659e6a8` cartão
T15.7 · T15.7/7b (commit desta parte): runner das 3 rotas.

### T15.7/7b — o runner do DDMOP7 (agente com cartão; torre re-mediu tudo)
R2: `src/ddmop7_bridge.py` (fixes medidos embutidos; DoE do artefato com fallback CSV
+hash; contabilidade `externa` sob FEBudget — UM contador só, D89). R1:
`eval_fcn_por_x` = ponto ÚNICO de desvio no `experiment.m` (propriedade estrutural:
1 lambda, 10 sítios), `ddmop7_value_local.m` (cd-em-volta com onCleanup),
⑤ declarado via `sonda_bloco_declarado.m` LENDO a fonte única Python (zero literal
duplicado — resolve o achado §3b do T15.3). Offline: **surpresa que desmentiu o
cartão** (§3.1 "zero mudança" era FALSO — a ⑦ inline re-avalia via evaluate_problem e
morreria na casca desligada) → resolvida SEM inventar: **Processo B da D102.9 mapeado
no precedente do e103** (⑦ retroativa via `final_eval.py`; constantes
`PROBLEMAS_FINAL_POS_HOC`+`FINAL_POS_HOC_INFO`; gates com o MESMO veredito do e103,
nenhum estado novo; paridade provada ponta-a-ponta — o achado do auditar SOME após o
final_eval). Processo A: `scripts/gen_dataset_ddmop7.py` pronto (roda nas VMs).
Validação da torre: 123/123 py + **22/22 MATLAB com o `.p` REAL (0 skips)** — âncoras
f=[4/17, 307/690] ≤1e-12, guard 600 pré-Engine, recusa DDMOP_Plat. 12 decisões [T]
do agente ratificadas (destaque: motor determinístico via seam da fábrica — produção
sem knob de mock; NULL declarado ≠ 0 fingido no footer).

### Smokes de célula real (C1/C2 parciais)
c154/RE21/s0: **PORTÃO VERDE — 8 gates, 0 vermelhos** (1ª célula real de problema
novo aprovada pela bateria inteira). nsga2×{RE21,ESTOQUE40}: ok=2/2, portões com
0 vermelhos (G-1 não-aplicável é ESTRUTURAL de piso — conferido contra o corpus s42,
que ainda carrega 1 vermelho de esquema antigo no G-7; as células novas estão mais
limpas que a baseline). c122/ESTOQUE40 (parede D=40): em execução.

### D0 — autópsia das "450 falhas sistemáticas" da main (laudos em handoff/)
c154: 125 teto_wall SANCIONADO (todas 12,00–12,49h, zero antes — medição da torre
sobre 481 células teto_wall da coleta) + 35 falhas reais (24 escada-RS; 10
ModelFittingError todas WFG1; 1 fantasma s30) + 12 em-voo. b1×DTLZ4: 18/18
determinístico (`dacefit.m:102`; NO_RETRY já certificava; aceitar = incapacidade
documentada). c262: teto_wall a 85–99% com dados; projeção O-20 NUNCA abortou
("seguindo até o relógio" — DI-43/44 funcionando como especificado). Mito desfeito:
"falhas rápidas em massa" eram OKs de piso por cache-hit. **c238×BBOB RESOLVIDO pela
torre**: bug latente UPSTREAM (`Infill_EIM.m:25` — `min(reshape(...))` colapsa para
escalar com front singleton; separação 28/28 vs 0/617 por `n_front1==1`; censura
NÃO-aleatória = viés). Decisões do autor: DEC-5 confirmada (DI-44, aceitar ⚪);
DEC-6 sim (12 sementes b1×DTLZ4 por simetria); DEC-7 sim (sementes não-tentadas das
famílias seed-dependentes voltam ao grid); DEC-8 (fix `,[],1` sob freeze) NA MESA.
Correção da torre ao laudo: semente 30 é fantasma — QUARENTENAR, jamais materializar.

### Pendências ao fechar esta parte
Smokes C3 do DDMOP7 (R1+R2 no Mac como prova de encanamento; offline real nas VMs
pós-Processo A) · dossiê C5 → veredito de fidelidade do AUTOR (D97) · tag+push
(autor) · provisionamento vm1+vm5 (matlab.engine, clone DDMOP pinado, transporte,
exports) · Processo A (27,5 h-core) · grid 1.890 · disparo. Notas operacionais do
7b: o portão da ⑦ DDMOP7 exige Engine e custa |⑦|×6s/célula — planejar ONDE roda;
fluxo offline ganha o passo `final_eval.py --all-seeds` pós-lote (como o e103).

**Fechamento (14/08): SUÍTE FINAL 966 testes · 0 falhas · 38 skips** (janela
limpa, com o `.p` real ligado). Smokes C3: R1 nsga2/DDMOP7 E R2 c149/DDMOP7
com PORTÃO VERDE (8 gates, 0 vermelhos cada). Dossiê C5 entregue ao autor.

---

## PARTE A50 — T15.10: JANELA EXAUSTIVA DE VALIDAÇÃO + REVISÃO ADVERSARIAL EXECUTADA (torre, 2026-08-14)

Mandato do autor: "rode todos os testes necessários para te dar 100% de certeza…
seja exaustivo" (janela de ~6h antes do check-in). A torre rodou a bateria
completa + uma revisão adversarial multi-agente do T15 inteiro (39 achados
brutos → 20 confirmados, 7 ALTA). Causa-raiz da família dominante: **"prosa não
provisiona VM"** — código e grid evoluíram, mas locks/receitas/frota/gates
antigos ficaram com literais velhos (a MESMA classe do BL-04).

### Defeitos que a bateria pegou (e que teriam manchado a campanha)
1. **BL-04 writer×gate (latente desde T12.8)**: 3 checks offline do accept
   exigiam `tempo_aval_real_s` NÃO-nulo; o writer grava null-declarado (I-02)
   desde d17644a. Teria REPROVADO TODA célula offline da campanha. Fix:
   presença-da-chave nos 3 sítios. O corpus s42 (0.0 gravado) mascarava.
2. **F0-02**: gate de alg_id preso em 22 (sobol_batch/treed_media de julho não
   contados). Fix → 24 + comentário-tripwire.
3. **F0-04**: semântica do selo desatualizada no MESMO dia (DEC-2 preencheu a
   régua DDMOP7 à tarde). Fix → `n_seladas==0` + `REGUAS_PROVISORIAS` como fonte.

### T15.10 — os fixes de runtime da revisão (todos aplicados + testados)
nº 7 `is_run_done`: exceção DECLARADA pós-hoc (D102.9) — offline DDMOP7 com
`params.nd_final` no ⑤ está PRONTO sem a ⑦ (sem isso: ~26,6 h-core re-executadas
POR PASSE de resume + janela de quimera OP-6). A3/DI-20 intacto p/ o resto.
nº 11 `encerra()`: Engine pós-BridgeTimeout marcada `_travada` ⇒ pula o eval de
higiene (penduraria o worker para sempre) e vai direto ao quit.
nº 15 `check_final`/portão: máquina sem Engine ⇒ `(None, NÃO-AFERÍVEL)` + exit 2
⇒ `_sub` mapeia para ⛔ INCONCLUSIVO (B-07/DI-41) — nunca vermelho falso.
Locks: linha executável `matlabengine==25.1` REMOVIDA (não existe no PyPI;
quebrava `pip install -r` na VM) → bloco-comentário: instalar da ÁRVORE do
MATLAB nos 2 venvs. frota.json reescrito vm1+vm5 (decisão 14/08) + env_matlab
na convenção. mapa_sementes: custo DDMOP7 imputado 526×6,3s (erro anterior de
até 703×); lote3s idem; plano3s `parar_tudo` mata Engines órfãs. treed_media e
c311: paridade pós-hoc (footer sem zero fingido; guard `_FinalPosHoc`).

### O-18 PROMOVIDO: watchdog de partida da Engine (MEDIDO em produção)
O Processo A v3 ficou **37 min** "travado". ERRATA da 1ª autópsia (que culpou o
handshake): a causa MEDIDA é o **macOS congelar o app MATLAB em coalizões de
processo de FUNDO** neste Mac (M1 Pro) — MATLAB órfão/de-fundo: 0,03 s de CPU
em 90 s (v4/v5/v6, com e sem `taskpolicy -B`, com e sem `NSAppSleepDisabled`);
o MESMO boot+aval em chamada FOREGROUND, no mesmo instante e sob a mesma
carga: 6,4 s de boot e 6,24 s/aval cravados (A/B decisivo). `nice` é
irrelevante (o foreground voa até com RN). A vítima é o MATLAB de ENGINE
(`-layeredTransport`); os MATLAB de lote direto desta manhã não sofreram.
Consequências: (a) `_boot_com_prazo` (thread-daemon + join) embrulha o boot
INTEIRO (start+cd+init) com `TIMEOUT_PARTIDA=300s` ⇒ pendurou vira
BridgeTimeout, run failed, processo novo — nas VMs Linux o quirk não existe,
mas o watchdog fica (partida sob carga é a mesma classe); (b) o dataset s0 do
Mac nasceu por **driver FATIADO em foreground** (7 chamadas ≤10 min, cache
atômico de F, montagem canônica `gen_one`+`check_one` com motor-replay que
confere X fatia a fatia; 526/526 a 6,24 s/pt; sidecar com wall 0.0 = assinatura
da montagem — artefato de smoke, D102.14: os F oficiais nascem nas VMs).

### Incidente: DOIS escritores na mesma célula (evitado)
O relançamento do smoke e81/ESTOQUE40 desta manhã deixou o filho da 1ª
tentativa VIVO (a "falha" era só do wrapper) e criou um segundo filho
IDÊNTICO — dois processos órfãos escrevendo a MESMA célula main/s0 (quimera
OP-6 em potencial). Detectado pelo censo de processos da tarde; payloads
comparados por md5 (idênticos, ambos pinados); morto o mais novo (44 min a
menos de progresso). Lição operacional: após "falha" de wrapper em launch de
fundo, SEMPRE censar filhos órfãos (`pgrep -f`) antes de relançar.

### Prosa re-provisionada + artefatos versionados
CLAUDE.md raiz (banner T15) · claude_code_context/CLAUDE.md (5 menções: grid
22.740, D102.16, 28×12, precedência decisions.json p/ D101+) · CONTRATO §T15
(3 ausências de sonda inconfundíveis; ⑦ pós-hoc; DoE congelado do init) ·
PROVISIONAR-VM-DO-ZERO: contagens B6 841/27/845 + **BATELADA T15 obrigatória**
(engine nos 2 venvs, clone .p pinado 0f45d2c1, export nos 2 perfis, âncora
f=[4/17, 307/690], Processo A ANTES do disparo offline, conferência de
artefatos). `git add` explícito dos 244 artefatos RE21/ESTOQUE40 (ALTA nº 1 —
sem eles o clone das VMs matava 1.260 células). Testes novos:
`tests/test_t15_10_fixes.py` — 13/13 (pós-hoc ×5, travada ×2, boot ×3,
não-aferível ×2, exit-2 ×1).

### Onda B executada (fecho desta parte, 14/08 tarde)
**Dataset DDMOP7 s0 REAL**: 526/526 pts do `.p` (driver fatiado), `gen_one`
canônico + `check_one` OK (hash round-trip). **b5r/DDMOP7/s0 offline
(exp=off, o canônico do grid)**: 526/526 exato, 928 ger, `final_pos_hoc=true`
com `n_nd_pos_real` NULL-declarado, `is_run_done=True` SEM a ⑦ (fix nº 7 em
produção); ⑦ pós-hoc com Engine real = 47 finais/2 ND pós-real, `--check`
VERDE; PORTÃO 9 gates: **0 vermelhos** (G-1 ⚪ estrutural sem-sonda). Bônus de
reprodutibilidade: o run tinha saído idêntico (47/2, ger 928) num primeiro
disparo com exp=main errado — mesmo seed ⇒ mesma trajetória, bit-a-bit.
**e103/RE21/s0 offline (MATLAB -batch, receita do driver)**: PORTÃO **VERDE
9/9** (G-1 com sonda VERDE). Gap 3 do C5: FECHADO. Achados de rota: offline
roda com **exp='off'** (grid; o accept remapeia e denuncia) e e103 NÃO passa
pelo dispatch python — só pelo `experiments.m` (receita do lote3s linha ~506).
**Quarentena**: as 11 células-smoke Mac dos 3 problemas (nsga2×3, c149, c154,
b5r×4, e103, moead_media — 84 arquivos com os finais) movidas para
`data/_quarentena_smokes/` (D102.14: Mac não produz célula de campanha;
e81/ESTOQUE40 segue em voo e vai para lá após o portão).

### Pendências ao fechar esta parte
e81/ESTOQUE40 aterrissar → portão → quarentena (gap 2) · suíte final em
janela limpa (G-8: espera o e81) → commit T15.10 · adendo C5 → veredito do
autor → tag `t15-problemas-reais` + push (autor) · BAIXA nº 1 (chamadasP
persistent) descartada por inspeção: trilho R1 = `src/ddmop7_value_local.m`,
sessão única sem parfor; nº 6 coberta pela batelada T15-d da receita.

**Fechamento (14/08 noite): e81/ESTOQUE40/s0 ATERRISSOU** — 7h25, 1239/1239
exato, manifesto auto-curado da marca do gêmeo, **PORTÃO VERDE 8/8** (o
timeline engoliu o trecho intercalado); célula → quarentena (90 arquivos).
GAP 2 FECHADO. **SUÍTE FINAL: 979 testes · 0 falhas** — em COMPOSTO imposto
pelo quirk do Mac: fundo = 978 não-Engine (0 falhas; 46 skips = 38 permanentes
+ 8 gateados por Engine) + foreground com `.p` real = `test_t15_ddmop7_bridge`
25/25 e `test_t15_ddmop7_matlab` 22/22 (cobrem o erro-de-env e os 8 skips do
fundo). Commit T15.10 na sequência.
