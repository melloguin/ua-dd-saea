# REGISTRO DE DECISÕES — FASE DE IMPLEMENTAÇÃO (DI-01…)

> **O que é.** O registro canônico e detalhado das decisões tomadas DURANTE a implementação do
> pipeline (pós-SPEC v5.2) — o companheiro da fase de implementação para o
> `claude_code_context/REGISTRO_DECISOES_pingpong_v5.md` (que cobre as D53–D86 da fase de SPEC).
> **Convenção:** decisões de implementação levam o prefixo **DI-**; não colidem com o espaço D1–D100
> do Anexo D da SPEC. Quando uma DI exige mudança na SPEC, a edição é executada pela torre numa
> janela documental (sem sessão de implementação ativa) e fica referenciada aqui.
> **Formato por decisão:** Contexto → Opções → Decisão → Justificativa → Evidência de verificação →
> Efeitos/ações → Referências. Decisor: **o autor** (Guilherme), em ping-pong com a torre.
> Última atualização: **2026-07-18** (bloco DI-01…DI-08 decidido em lote pelo autor).

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
1. **Janela documental (quando o c154 fechar):** DI-05 (S.3#9 + B5) + DI-08-1 (SPEC do `__final`) —
   edições da SPEC + regen de bundles + diff auditado, pela torre.
2. **Antes do R3:** DI-08-2/3/4 (naming + avaliador pós-hoc + check no accept + retroativo e103).
3. **M7:** DI-06 (o mini-cartão de hardening com os 8 itens).
4. **Dossiê/lote do autor:** DI-07b (o desalinhamento ~24,8% do e74 como ponto prioritário).
