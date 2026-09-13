# RELATÓRIO DE FIDELIDADE T11 — `treed_media` (Treed-média, PISO-BIG · alg_id 23) · validação da rodada T11 · comparação com a F5

**Universo desta análise — e a novidade que muda tudo.**
**(A) s42 (mecanismo):** 10/10 células (`ZDT4 D=10`, `DTLZ2 D=12`, `MMF16_20 D=20`, `WFG9 D=22`, `ZDT1 D=30` × {LHS, MVNS}), todas `tier=big` (N=50.000), todas `mac` ⇒ piso de ruído entre máquinas (HV ≤1,55% / IGD+ ≤58,98%, O-18) **não se aplica**. Agregados re-medidos por mim: **876.627 linhas de ③** (676.627 busca + 200.000 sonda) · **500.000 de ①** · **678 de ⑦** · **32 eventos de ⑥** · **10.000 gerações**.
**(B) Smoke T11 — 🆕 ELE EXISTE, contra o que o handoff diz.** O briefing desta missão e o próprio T11 (§15.2) e o `evidencia_T11/LEIA-ME.md` afirmam que *"os smokes PYTHON não estão preservados (tempdirs removidos)"*. **É FALSO.** Existe `/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/` com **11 células Python**, criada em 2026-07-31 10:45–11:41, e uma delas é **`sweep-big-mvns/treed_media/ZDT4/42`** — **exatamente a mesma célula** do meu `swap_big-mvns_ZDT4` da s42. Isso me deu o que nenhum outro analista Python tem: **um par PRÉ-T11 × PÓS-T11 da MESMA célula**, e com ele a não-perturbação da campanha T11 deixou de ser veredito registrado e virou **medida bit-a-bit**.

---

## 1. Ficha do mecanismo

`treed_media` **não é algoritmo da literatura** — é a **ablação cirúrgica do c311 (TGPR-MO, Mazumdar et al. 2023, *ECJ* 31(4)) no tier big**, criada por B15.4 / DI-16.5[P5] / D38 / **DI-35.2** para responder a UMA pergunta: *quanto os GPs locais acrescentam em N=50.000?* Sem artigo ⇒ o gabarito é a especificação canônica do bundle (`alg_c311_tgprmo.md` + cartão `handoff/T8-piso-big.md`) mais as decisões do REGISTRO; a Entrega 2 é **N/A** e no lugar dela vai o **PAPEL DE CONTROLE** (§5).

Fluxo (à risca de `src/treed_media.py`, HEAD pós-T11): `ds_{prob}_42_big_{dist}.parquet` (① = dataset, orçamento nasce ESGOTADO) → `_build_surrogates` **importada de `src.c311_tgprmo`** (1 `treeGP` por objetivo, **só a árvore**: nenhum `addGPs`, `error_leaves=None`) → **SONDA** (1 bloco de 20.000, μ da árvore, σ NULL, sob `preserve_all_rng`) → **RVEA final 10 × 100 = 1.000 gerações** sobre a árvore FIXA (`selection_type="mean"`, α=2) → **⑦** do ND real pós-hoc (fora do orçamento, DI-08). Predição = média da folha; sem GP não há variância ⇒ **σ NULL em TODA a ③** (DI-16.1). Contador `geracao` **simples 1..1000**. `env_c311` (py3.8.20, sklearn 1.1.2, pymoo 0.6.1.2, torch/gpytorch ausentes), `OMP/OPENBLAS/MKL/NUMEXPR=1`.

**Divergências sancionadas nomeadas:** `max_depth=100` (🟠 impl→código, bússola D29, ⟦v2.2⟧ do bundle) · σ como extensão nossa no c311 (🟢 D30/`SPEC:434`), aqui **removida** por DI-16.1 · tiers D38/D90/D51 · ② vazia DI-16.17 · 1 bloco de sonda (vs 2 do c311/DI-16.12) · ④ de 1 linha (T8) · sonda fora de `tempo_geracao_s` (DI-13.10) · teto universal DI-35.5.

**Delta T11 no código deste config — a lista é FECHADA e eu a li inteira** (`git diff bfe68a2 HEAD -- src/treed_media.py`): (i) `Checkpointer` [DI-43/G5]; (ii) **guard de tier** [DI-42.5/A10]; (iii) `enable_bucket` no `write_failed_manifest` [B-09/G4]; (iv) `tempo_aval_real_s=bud.tempo_aval_real_s` no lugar de `0.0` literal [I-02/G7]. Mais, fora do arquivo: `campanha_id` (G3), `repo_hash` (I-09), `schema_version` 1→2, e B-01/B-11 no `AuditLogger`.

---

## 2. DISSECAÇÃO DOS ASPECTOS — o CORE

### 2.1 Tabela-resumo (32 aspectos classificados + 3 T)

| # | aspecto | classe | verif. | resultado-síntese (re-medido por mim, 10/10 células salvo indicação) |
|---|---|---|---|---|
| A1 | Offline puro: FE = dataset, zero FE na busca | **(1)** | direta | `fe_final==maxfe==50.000` 10/10; ① 100% `fase=init`; `fe_index` denso 0..49.999 (igualdade com `np.arange`) |
| A2 | Binding ① ↔ artefato (D63/D87/D90) | **(2)** | direta | sha256-float64 **recomputado**: `x_hash` 10/10 ✓, `f_hash` 10/10 ✓; max\|ΔX\|=max\|ΔF\|=**0,0** |
| A3 | Treino ÚNICO: ④=1 linha, `fe_treino_max`≡49.999 | **(2)** | direta | `n4=1`, `fit_series=1` 10/10; `fe_treino_max` **valor único** em 876.627 linhas |
| A4 | Sonda: 1 bloco × 20.000, `geracao`=NULL | **(2)** | direta | 1 evento `sonda` 10/10; 20.000 linhas; NULL em 20.000/20.000; `sonda_x_hash`≡manifesto 10/10 |
| A5 | Régua: join posicional + WAPE + cobertura N/A | **(2)** | direta | max\|ΔX\|=**0,0 exato** (f32) 10/10; WAPE recomputado ≡ `sonda_f52e.csv` na 6ª casa 24/24; cobertura **N/A por regra** |
| A6 | ④: `fit+busca ≤ tempo_geracao_s`, sonda FORA (DI-13.10) | **(2)** | direta | identidade **exata** 8/10, 1 ULP-f32 2/10; **`+sonda` estoura 10/10** — e **segue valendo no smoke T11** (Δ=4,77e-7) |
| A7 | Reconciliação entre camadas + guardas | **(2)** | direta | 0 eventos `guard`; `cache_hits=0` no ⑤ e no footer; `n_ger` footer≡⑤≡③=1000 10/10 |
| A8 | ⑦: ND recomputado ≡ `nd_pos_real` + link posicional | **(2)** | direta | recomputo **exato 10/10** (678 pts, 309 ND); `(ger,linha)`→③ **bit-a-bit** 678/678; `origem_geracao`≡1000 10/10 |
| A9 | **Congelamento** do surrogate (prova sem 2º bloco) | **(1)** | direta | **9.443 X reavaliados**, **675.616 linhas**, até **1.000** reavaliações do mesmo X: **0 divergências de μ** |
| A10 | σ NULL em 100% da ③ (DI-16.1) | **(2)** | direta | `sigma_*` NaN em **876.627/876.627**; μ NaN em **0** |
| A11 | σ **não consumido** na seleção | **(1)** | direta | contrafactual **impossível**: não existe σ na ③ (≠ c311, onde isso era T) |
| A12 | ② vazia + `real_solution_id` NULL (DI-16.17) | **(2)** | direta | ②=0 linhas 10/10; `real_solution_id` NULL em 876.627/876.627 |
| A13 | Fantasia: endpoint é a ⑦ (`nd_pos_real/n_final`) | **(2)** | direta | mediana **0,2909** (0,1944–0,7524), re-medida célula a célula |
| A14 | Métricas oficiais da ① EMPATAM entre offline (D69) | **(2)** | direta | IGD+/HV/IGD/GD/spacing/\|ND\| **dígito a dígito** ≡ c311 em **9/9** pares |
| A15 | **A ABLAÇÃO**: μ distintos ≤ ⌊N/(10D)⌋ = medidor de GP | **(2)** | direta | folhas tocadas **115–393** ≤ tetos 166–500 em **10/10**; quantização 99,98–100,00% |
| A16 | Árvore MSE, `min_samples_leaf = 10D` | **(1)** | direta | `msl`∈{100,120,200,220,300}≡10·D em 10/10; ocupação do teto **74,4–78,6%** |
| A17 | `max_depth=100` (🟠 código, não "livre") | **(2)** | **direta-declarativa** | declarado 10/10; não-vinculante por inferência (quem para é o `min_samples_leaf`) |
| A18 | **RVEA final 10×100=1000 ger** | **(1)** | **direta — 🆕 AGORA DETERMINÍSTICA** | smoke: **10 eventos `checkpoint` em `iteracao`=100,200,…,1000**, 1 por `iterate()`. Na s42 era estatística (\|Δpop\| nas fronteiras **9,5×–54,2×** o basal) |
| A19 | Contador `geracao` SIMPLES 1..1000 (sem offset C311-11) | **(2)** | direta | `set(geracao)`≡{1..1000}, zero furos, 10/10 |
| A20 | Pop lattice 50 (M=2) / 105 (M=3), **pode encolher** | **(1)** | direta | teto **nunca** excedido 10/10 (máx 105/104/103 · 50/48/46/45); mín **32–78**; encolheu 10/10 |
| A21 | Espaço do modelo **CRU**, μ nunca extrapola | **(1)** | direta | `espaco_modelo='cru'`/`transf_*` NULL em 876.627/876.627; μ ∈ envelope do dataset **24/24** |
| A22 | Tier big=50k + eixo LHS×MVNS (D38/D51/D90) | **(2)** | direta | `tier/dist` manifesto ≡ artefato ≡ label 10/10 |
| A23 | Teto universal DI-35.5 (43.200 s) | **(2)** | direta-declarativa | declarado 10/10; wall 5,86–15,71 s ⇒ folga **2.749×–7.370×**; ramo nunca exercitado |
| A24 | Receita/ordem (build→sonda→RVEA→⑦) | **(2)** | direta | prova pelo relógio (F5) + **prova estrutural nova**: `emit_sonda_block` é chamado na linha 433, ANTES de `RVEA(...)` na 443 |
| A25 | DI-28: "mesma ESPECIFICAÇÃO, treino INDEPENDENTE" | **(2)** | direta | μ bit-idêntico ao c311 em **694.998/695.030** pts sem GP = **99,9954%**; 32 divergentes, todos MVNS, \|Δμ\|≤2,6e-5 |
| A26 | Rito de escrita: footer / `motivo_parada` / B-01/B-11 | **(2)** | direta | `motivo_parada='orcamento'` 10/10; **3 células com 2 footers, 6 com 1, 1 com 0** (⚠ errata contra a minha F5) |
| A27 | O motor busca de fato? | **(2)** | direta | Σμ melhora **1,69%–25,57%** de ger 1→1000 |
| **N1** | 🆕 **DI-43 checkpoint — não muda o resultado** | **(2)** | **direta, MEDIDA** | ①③⑦② **BIT-IDÊNTICAS** s42 × smoke (57.281+50.000+37+0 linhas; ③ com os MESMOS 1.472.124 bytes) |
| **N2** | 🆕 **DI-42.5 guard de tier** | **(2)** | **direta, EXECUTADA** | barra 5/5 tiers errados, passa 2/2 corretos, **0 arquivos criados** |
| **N3** | 🆕 **I-02 `tempo_aval_real_s` no offline** | **(3)** 🎯 | direta | o código promete NULL; o dado dá **0,0572 s** (e 0,0001–0,0003 s nos outros 4 offline) |
| **N4** | 🆕 **custo do checkpoint DENTRO de `tempo_busca_s`** | **(3)** 🎯 | direta | **3,7539 s de 6,9699 s = 53,9%** do `tempo_busca_s` pós-T11 é I/O de checkpoint |
| **N5** | 🆕 Proveniência T11 no ⑤ (G3/I-09/schema v2) | **(2)** | direta | `campanha_id`, `repo_hash=9ad0138a…`, `schema_version=2` presentes no smoke, **ausentes** em 10/10 da s42 |
| T1 | `selection_type='mean'` / agregador da folha | **T** | não-verif. | declarado 10/10; média × mediana da folha não separável ex-post |
| T2 | Vendor c311 intocado / fonte única / env / pinning | **T** | não-verif. | declarativo; corroboração indireta forte via A25 (99,995%) |
| T3 | Semeadura D62 + `_lhs_determinismo` (DI-28.3) | **T** | não-verif. | exige re-run bit-idêntico |

---

### 2.2 Blocos narrativos

#### A1 — Offline puro: o orçamento É o dataset, e a busca não gasta um FE

**(a)** O TGPR-MO é offline puro ("no new data", Mazumdar et al., Abstract/§2): todo o orçamento é o dataset pré-coletado; a única avaliação real fora dele é a do ND final. **(b)** D90 fixa `maxfe = n_dataset`, D38 abre `big=50.000`, e o runner instala `OfflineBudgetViolation` (pára-e-loga D81, `treed_media.py:418`) para qualquer FE real durante a busca. **(c)** Re-medido: `fe_final == maxfe == 50.000` em **10/10**; a ① tem 50.000 linhas com `fase='init'` em 100%; `fe_index` é denso `0..49.999` (comparação com `np.arange` — igualdade exata) em **10/10**; zero X duplicado. **(d)** A ① não é produzida pelo run: é o artefato injetado por `load_offline_budget` (A2); o laço RVEA nunca chama a função real; o único `evaluate` real é o pós-hoc da ⑦ (`treed_media.py:469-471`), fora do orçamento por DI-08. **⚠ Ressalva NOVA:** a assinatura que a F5 usou para este aspecto — `tempo_aval_real_s == 0` em 10/10 — **deixou de valer no código de hoje** (ver N3). Isto não muda a classe deste aspecto (nenhum FE foi consumido: `fe_final` continua igual a `maxfe` e o `offline_guard` nunca disparou), mas quebra o teste que a auditoria usava. **(e) (1) conforme · direta.**

#### A2 — Binding ① ↔ artefato: hash recomputado, não citado

**(a/b)** O método canônico supõe o dataset dado; D63/D87/D90 exigem binding criptográfico (`doe_hash` = sha256 dos bytes float64 row-major do X; `cp_init_offline.f_hash` idem para F). **(c)** Abri os 10 artefatos `data/datasets/{prob}/ds_{prob}_42_big_{dist}.parquet` e **recomputei o sha256 do zero**: `x_hash` bate em **10/10** e `f_hash` em **10/10**. Linha a linha: **max\|ΔX\| = 0,0** e **max\|ΔF\| = 0,0** entre a ① (float32) e o artefato castado a float32, ordem preservada. **(d)** O runner carrega o parquet, converte a float32 (D53) e grava na ordem de leitura — nenhuma reordenação. **(e) (2) sancionado (D63/D87/D90) · direta.**

#### A3 — Treino ÚNICO: ④ com 1 linha e `fe_treino_max` congelado

**(a)** No c311 a ④ tem uma linha por iteração de construção (44–99 nas células big) — é o eixo de escalabilidade do `addGPs`. **(b)** A ablação remove esse eixo: o cartão T8 fixa "④ = 1 LINHA" e o `sigma_dict` declara `fe_treino_max` "constante 49999 em TODA linha (busca+sonda)". **(c)** ④ com **1 linha** em 10/10 (`geracao=1`, `n_acumulado=50.000`), `fit_series` com 1 entrada em 10/10, e `fe_treino_max` com **um único valor distinto** (`nunique()==1`, valor 49.999) em todas as **876.627** linhas. **(d)** Uma chamada a `_build_surrogates` produz as M árvores e o modelo nunca mais é tocado — o que A9 prova independentemente pelos dados. **(e) (2) sancionado (T8/D90) · direta.**

#### A4 — Cadência da sonda: 1 bloco, não 2 — e a diferença é informativa

**(a/b)** §17.2.2 fixa 20.000 pontos Sobol no offline; DI-16.12 dá **dois** blocos ao c311 porque o modelo dele MUDA entre fases, e a bit-identidade dos dois vira a prova do congelamento. Aqui o `sigma_dict` declara "1 bloco (modelo unico, sem retreino)". **(c)** Exatamente **1** evento `rec='sonda'` por célula (10/10), `n_pontos=20.000`, `modelo_flag='treed_media/RVEA-arvore-media'` (valor ÚNICO em 876.627 linhas — sem a dicotomia `treedGP_build`/`treedGP_final`), `sonda_x_hash` do evento ≡ do manifesto em 10/10; na ③, 20.000 linhas com `regime='sonda'` e `geracao` **NULL em 20.000/20.000** (DI-13.5). **(d)** Um bloco basta porque o modelo é único. O evento do ⑥ carrega `geracao:1` (obrigatório por DI-09) enquanto a ③ carimba NULL — convenções distintas, ambas normativas, sem contradição. **(e) (2) sancionado · direta.**

#### A5 — A régua: join posicional exato, WAPE reproduzido, cobertura N/A por regra

**(a/b)** §5 do protocolo congela WAPE por objetivo no espaço CRU e cobertura ±1,96σ, com join **posicional** (regra 5/10 do CONTRATO §10). **(c)** Join posicional dos 20.000 pontos contra `data/sonda/sonda_{prob}.parquet`: **max\|ΔX\| = 0,0 exato** (após cast f32) em 10/10. **Recomputei o WAPE do zero** (`espaco_modelo='cru'`, `transf_params` NULL ⇒ des-transformação é a identidade): bate com `sonda_f52e.csv` na 6ª casa em **24/24** pares (ex.: `lhs/DTLZ2` obj0 **0,105582**; `mvns/WFG9` obj1 **0,282738**; `lhs/ZDT4` obj0 **0,001953**). Painel: WAPE de **0,00195** (ZDT4-lhs f0) a **0,3068** (ZDT1-mvns f1); correlações de **0,1219** (WFG9-mvns f0) a **1,0000** (ZDT4/ZDT1 f0). **Cobertura = N/A em 24/24** — o `sonda_f52e.csv` traz `cobertura95` vazio com `n_validas=20000, n_nan=0`, tratamento CORRETO (contra a inflação que o `cobertura95` produz no c311). **(d)** Sem σ, o WAPE é a única métrica de calibração; a família do problema domina (ZDT f0 quase-exato; WFG9 com corr ≈0,12–0,42 — a árvore não captura as transformações WFG). **(e) (2) instrumentação nossa · direta.**

#### A6 — A invariante dupla do timing: a sonda está fora, e continua fora no código de hoje

**(a/b)** DI-13.10 (ratificada) manda `tempo_geracao_s` EXCLUIR a sonda, porque a sonda é instrumentação deste estudo e contaminaria a curva de escalabilidade. **(c)** Com 1 linha de ④ a invariante vira identidade: `tempo_fit_s + tempo_busca_s` **igual bit-a-bit** a `tempo_geracao_s` em **8/10** e a 1 ULP-f32 nas outras 2 (`lhs/MMF16_20` Δ=+9,54e-7; `mvns/MMF16_20` Δ=−9,54e-7). O contrapositivo fecha em 10/10: somar `tempo_pred_sonda_s` (0,088–0,166 s) estoura em todas. **E re-verifiquei no smoke T11**: `0,620631 + 6,969877 = 7,590508` contra `tempo_geracao_s = 7,590508` (Δ=4,77e-7); com sonda, 7,679582 > 7,590508. **(d)** O runner mede fit e busca separadamente e soma (`treed_media.py:488-490`); o resíduo é arredondamento f32 do export (D53). **(e) (2) sancionado (DI-13.10) · direta.** ⚠ **Mas a invariante hoje protege a coisa errada:** ela mantém a sonda fora e deixa o checkpoint dentro (ver **N4**).

#### A7 — Reconciliação: nenhuma guarda disparou, e a aritmética fecha

**(c)** ⑥ com **0 eventos `rec='guard'`** nas 10 células (contraste: o c311 teve 2 `hard_error` de `ModuleNotFoundError: google`); `cache_hits=0` no ⑤ **e** no footer; `n_geracoes` do footer ≡ do manifesto ≡ `max(geracao)` da ③ = **1000** em 10/10; `footer.n_final` ≡ `len(⑦)` e `footer.n_nd_pos_real` ≡ `⑦.nd_pos_real.sum()` em 9/9 células com footer. **Nenhum off-by-one** — não há laço de construção. **(e) (2) · direta.**

#### A8 — A ⑦: Pareto recomputado, link posicional bit-a-bit

**(a/b)** DI-08 define a ⑦ como o ENDPOINT do offline (ND final avaliado 1× na função real, fora do orçamento); DI-13.9/B7.5 exigem que ela seja reconstituível da ③; DI-27/A15 mandam o `write_final` calcular o `nd_pos_real` sobre a **vista float32** — e é isso que blinda esta camada contra a **regra 11 nova do CONTRATO** (dominância sobre ①/⑦ é LOSSY): o algoritmo não decidiu nada com a ⑦, e o `nd_pos_real` gravado é, por construção, o filtro sobre a mesma vista f32 que eu recomputo. **(c)** Recomputei a dominância nas 678 linhas: o vetor `nd_pos_real` bate **10/10** (309 ND). `origem_linha` denso `0..n−1` 10/10, `origem_geracao` **constante 1000** 10/10, e o X da ⑦ bate **bit-a-bit** (max\|ΔX\|=0,0) com a ③ da geração 1000 em **678/678**. **(e) (2) instrumentação (DI-08/DI-13.9) · direta**, com a ressalva R4#11 **neutralizada por desenho neste config**.

#### A9 — CONGELAMENTO: a prova que substitui os dois blocos do c311

**(a)** §3.1 exige que a otimização final rode sobre o surrogate **congelado**. **(b)** No c311 isso se prova pela bit-identidade dos 2 blocos (DI-16.12); aqui há 1 bloco só, por desenho, então a prova tem de ser outra. **(c)** Se o surrogate mudasse, um MESMO x reavaliado em gerações diferentes teria μ diferente (o modelo é uma função determinística x↦μ). Agrupei as 676.627 linhas de busca por X **bit-a-bit** (chave = os bytes do f32, não comparação numérica — regra 1 do CONTRATO) e contei μ distintos por grupo: dos **10.454 X únicos**, **9.443 são reavaliados** em gerações distintas, cobrindo **675.616 linhas**, com até **1.000 reavaliações** do mesmo ponto. **Em ZERO deles μ divergiu** (`n_X_com_mu_divergente = 0` em 10/10). **(d)** O RVEA é elitista o bastante para carregar indivíduos por centenas de gerações; cada carregamento é uma reavaliação do surrogate. **Esta prova é mais forte que a do c311**: 675.616 pontos de verificação contra 2 blocos. **(e) (1) conforme · direta.**

#### A10 — σ NULL em 100% da ③: NaN total é INFORMAÇÃO

**(a/b)** No paper a variância do GPR é "anunciada mas não consumida" (§5); no c311 ela virou extensão nossa (🟢 D30, `SPEC:434`). **DI-16.1** manda o oposto aqui: sem GP não há variância, e excluí-la é o que torna o contraste c311×treed atribuível **só** a σ. **(c)** `sigma_*` é NaN em **876.627 de 876.627** linhas (busca E sonda, 10/10) — 100,00%, não 99,9%; `mu_*` é NaN em **0**. **(d)** `_Recorder.capture` passa `sigma=None` (`treed_media.py:151`) e `_sonda_predict_media` descarta o σ all-NaN do `_predict_batch` (`treed_media.py:208-210`). **(e) (2) sancionado (DI-16.1) · direta.** ⚠ Armadilha (20): σ-NaN **total** ≠ σ-NaN **por região** (c311: 63,0–99,5% na sonda).

#### A11 — σ **não consumido**: o único aspecto que a ablação PROMOVE de T para verificado

**(a)** M.17 do bundle: "o GPR fornece a variância, mas a otimização usa só a média; consumir a variância fica como trabalho futuro". **(b)** No c311 isso ficou no **balde T** (contrafactual inverificável ex-post: σ existia na ③ e nada nos dados prova que a busca não o leu). **(c)** Aqui o contrafactual é **impossível**: σ não existe em nenhuma das 876.627 linhas, e o `APD_Select` do vendor lê só `pop.fitness`. Não há o que consumir. **(e) (1) conforme, VERIFICADO · direta.**

#### A12 — ② vazia e `real_solution_id` NULL, por construção

**(a/b)** DI-16.17: a pop inicial do RVEA é um LHS NOVO + SBX/PM contínuos ⇒ nenhum indivíduo coincide com o dataset; o gate NÃO exige ② não-vazia. **(c)** ② com **0 linhas** 10/10; `real_solution_id` NULL em **876.627/876.627**. Corroboração: `n_X_unicos` da busca é **359–2.137**, ordens de grandeza abaixo dos 50.000 do dataset, e a ① tem 0 X duplicados. **(d)** Amostragem contínua nova + operadores contínuos: colisão bit-a-bit em f32 com D∈[10,30] tem probabilidade nula. **(e) (2) sancionado (DI-16.17) · direta.** É também a razão pela qual o **portão G-1 é ⚪ n/a** neste config (T11 §5) — sem linha marcada, não há identidade ③↔① a conferir: **não-aplicável, não pendência**.

#### A13 — Fantasia: no offline o U11 muda de endereço (da ② para a ⑦)

**(a/b)** O U11 canônico pede o erro de fantasia dos infills via `real_solution_id`→①. **Impossível aqui** (A12), então o endpoint de fantasia da família offline é `nd_pos_real/n_final` da ⑦ (DI-08): a fração do "front" do MODELO que sobrevive à realidade. **(c)** Re-medido: `lhs/MMF16_20` **0,7524** (79/105) · `mvns/MMF16_20` 0,6765 · `lhs/DTLZ2` 0,5810 · `mvns/DTLZ2` 0,3627 · `lhs/WFG9` 0,3478 · `mvns/WFG9` 0,2340 · `lhs/ZDT1` 0,2200 · `mvns/ZDT4` 0,2162 · `mvns/ZDT1` 0,2083 · `lhs/ZDT4` **0,1944** (7/36) — **mediana 0,2909**. **(d)** A média de folha achata a superfície: dentro de uma folha o modelo não distingue pontos, então o RVEA acumula empates que a função real desempata — ~71% do "front do modelo" morre na realidade. **(e) (2) sancionado (DI-08) · direta.**

#### A14 — As métricas oficiais EMPATAM por desenho — e isso é o que dá sentido à §5

**(a/b)** D69 manda a métrica ler o `f` gravado na ①. No offline a ① **É** o dataset compartilhado ⇒ todos os configs offline sobre a mesma célula produzem exatamente o mesmo IGD+/HV/\|ND\|. **(c)** `metricas_finais_f52c.csv`, 9 pares c311×treed_media no big: `igd_plus`, `hv`, `igd`, `gd`, `spacing` e `n_nd` são **idênticos dígito a dígito** — ex.: `sweep-big-lhs/DTLZ2` IGD+ **0,173895**, HV 0,379981, GD 0,426752, spacing 0,084088, \|ND\| 300 nos dois; `sweep-big-mvns/ZDT4` IGD+ **45,514661** nos dois. **(e) (2) sancionado (D69) · direta.** ⚠ **Consequência prática, e é grande**: a métrica oficial é **estruturalmente incapaz** de ranquear o piso contra o c311. O papel de controle deste config vive **inteiramente** na ⑦ (§5).

#### A15 — A ABLAÇÃO em si: μ distintos é um medidor direto de quanto GP existe

**(a)** O paper prescreve a construção iterativa: a cada iteração, a folha de PIOR MSE ganha um GP local (Matérn 5/2 ARD), até I_max=⌈N/(10D)⌉ ou early-stop. **(b)** B15.4/DI-16.5[P5]/**DI-35.2** removem esse laço inteiro (`build_surrogates` DIRETO, `error_leaves=None`); DI-35.2 explica por que é módulo próprio: rotear `tier=='big'` para dentro do c311 transformaria o único config do tier big **na sua própria ablação**. **(c) Quatro assinaturas independentes, re-medidas.** (i) **Zero eventos `decision`** no ⑥ (o ⑥ inteiro tem 32 eventos nas 10 células; o c311 emite 44–99 por célula big). (ii) **1 fit**. (iii) **σ NaN total** (A10). (iv) A prova quantitativa: como a árvore prediz a média da folha, μ_j é constante por folha ⇒ **nº de valores distintos de μ_j = nº de folhas TOCADAS**, e tem que respeitar ⌊N/(10D)⌋. Medido nos 20.000 pontos de sonda: **115–393** valores distintos contra tetos de **166–500** — **≤ teto em 10/10 células e 24/24 objetivos**; quantização (fração de pontos que compartilham μ) **99,98%–100,00%**. **(d)** Qualquer valor distinto acima do nº de folhas só pode vir de um GP local (predição contínua). O contador lê **zero GP**, em 10/10. **(e) (2) sancionado (B15.4/DI-16.5[P5]/DI-35.2) · direta.**

#### A16 ⊕ A17 — A árvore: `min_samples_leaf = 10D` (paper ✓) e `max_depth = 100` (código 🟠)

**(a)** §4.1.3: N_min = 10n — o bundle marca ✓ paper. Sobre profundidade, o paper diz que não é controlada (§3.1); o ⟦v2.2⟧ do bundle corrigiu: o **código oficial** fixa `max_depth=100` (🟠 impl→código, bússola D29). **(c)** `params.min_samples_leaf` = 100/120/200/220/300 para D = 10/12/20/22/30 — igualdade `msl == 10·D` em **10/10**; folhas tocadas ≤ ⌊50000/msl⌋ em 10/10 com **ocupação 74,4%–78,6%** (mediana 76,1%). `max_depth=100` está declarado em 10/10 **e só**: o ⑥ deste config **não tem evento de geração** (32 eventos em 10 células), então a profundidade efetiva não é observável como no c311 (que grava `profundidade` nos `decision`). **(d)** A ocupação estável em ~76% do teto mostra que quem para a árvore é o `min_samples_leaf`, não a profundidade: um teto de 100 níveis só vincularia numa árvore patologicamente desbalanceada. **(e) A16 (1) conforme (paper ✓) · direta; A17 (2) sancionado (🟠 código) · direta-declarativa** (marca visível, Botão 3).

#### A18 — RVEA final 10×100=1000: 🆕 **de estatística para observação DIRETA**

**(a/b)** §4.1.5 e o bundle: otimização final RVEA `n_iterations=10` × 100 gerações = 1.000. O manifesto **declara** `n_iter_final=10 / n_gen_final=100 / n_gen_total_final=1000` — mas 1.000 gerações num contador simples são compatíveis com "1×1000", e a decomposição seria puramente declarativa. **(b′) O que a F5 fez:** a query-joia estatística — o RVEA do DESDEO readapta os vetores de referência no INÍCIO de cada `iterate`, logo há saltos de população em g≡1 (mod 100). Re-medido: \|Δpop\| médio nas 9 fronteiras é **9,51×–54,21×** o \|Δpop\| global (mediana global 0,0) em 10/10. Bom, mas indireto. **(c) 🆕 O que a T11 entregou.** `treed_media.py:457-460` chama `ckpt.talvez_gravar(bud, buf, iteracao=int(evf._current_gen_count))` **exatamente uma vez por `evf.iterate()`**, e o `Checkpointer` emite um evento `checkpoint` no ⑥ com esse `iteracao`. No smoke: **10 eventos, com `iteracao` = 100, 200, 300, …, 1000**. Dez chamadas a `iterate()`, cada uma avançando **exatamente 100** gerações, num contador que termina em 1000. E o cruzamento fecha: o `n_linhas_terceira` de cada checkpoint (24.566 · 28.238 · 31.838 · 35.510 · 39.109 · 42.709 · 46.407 · 49.982 · 53.582 · 57.281) é **idêntico** ao cumulativo da ③-busca em g=100,200,…,1000 somado às 20.000 da sonda — 10/10. **(d)** O checkpoint é chamado no corpo do `while evf.continue_evolution()`, depois do `iterate()`; o `_current_gen_count` é o contador interno do RVEA. Ele virou, sem querer, o instrumento que faltava. **(e) (1) conforme (paper ✓), agora com prova DETERMINÍSTICA e não estatística · direta.** **Este é o maior ganho de fidelidade da T11 neste config.**

#### A19 ⊕ A20 — Contador simples 1..1000 e a população que encolhe

**(a/b)** C311-11/DI-16.19 obriga o c311 a um contador ÚNICO atravessando as duas fases; o cartão T8 dispensa o offset ("fase única; o RVEA final nunca chama `_refresh_population`"). §4.1.3 (Cheng 2016): o tamanho da população é o nº de vetores de referência do lattice — 50 para M=2, 105 para M=3 — e **pode encolher**. **(c)** `set(geracao)` ≡ **{1,…,1000} exato** em 10/10, zero furos; `modelo_flag` valor ÚNICO em 876.627 linhas. Teto **nunca** excedido em 10/10 (máx **105/105/104/103** nos M=3 e **50/48/48/46/45** nos M=2); a população encolheu em **10/10**, com mínimos de **32** (`lhs/ZDT4`) a **78** (`mvns/DTLZ2`). **(d)** Uma fase ⇒ um contador; a seleção APD só mantém um indivíduo por vetor ativo, e em fronts degenerados (ZDT4 com g enorme, WFG9) muitos vetores ficam vazios. **(e) A19 (2) desenho nosso (T8) · direta; A20 (1) conforme (paper ✓) · direta.**

#### A21 — Espaço do modelo CRU: o μ nunca extrapola

**(a/b)** O bundle é explícito: a `treeGP` treina em Y cru, sem normalizer/z-score. O `sigma_dict` declara `espaco_modelo: cru`, `transf_tipo/params = NULL`. **(c)** `espaco_modelo='cru'` e `transf_*` NULL em **876.627/876.627**; e a consequência forte: **μ dentro do envelope [min f, max f] do dataset em 24/24 pares célula×objetivo** — a árvore **nunca extrapola** (contraste com o e74/RBF, cujo μ explodiu fora do suporte). **(e) (1) conforme (código oficial) · direta.**

#### A22 ⊕ A23 — Tier big, eixo LHS×MVNS, teto DI-35.5

**(c)** `tier='big'`, `n_dataset=50.000`, `q=1`, `regime='offline'` em 10/10; `dist` do manifesto ≡ do artefato ≡ do token do label em 10/10. Não existe célula `off`/`small`/`medium` deste config — o piso-big só vive no big, como manda DI-35.2 (e agora o **guard N2 o garante em código**). Teto: `sigma_dict.teto` declara 43.200 s em 10/10; wall observado **5,86–15,71 s** ⇒ folga **2.749×–7.370×**; `motivo_parada='orcamento'` e `status='ok'` em 10/10; **o ramo de aborto nunca foi exercitado**. **(e) A22 (2) sancionado (D38/D51/D90) · direta; A23 (2) sancionado (DI-35.5) · direta-declarativa.**

#### A24 — A receita provada: build → SONDA → RVEA → ⑦

**(a/b)** O cartão T8 fixa a ORDEM. Se a sonda rodasse depois da busca, ela mediria o mesmo modelo (congelado), mas a receita declarada estaria errada. **(c)** A F5 provou pelo relógio (Δ(header→sonda) − (fit+sonda) = +0,017 a +0,027 s em 10/10). Acrescento a **prova estrutural** que li no código de hoje: `emit_sonda_block` é chamado na linha **433**, dentro do `if emitir_sonda`, e `RVEA(problem, use_surrogates=True, n_iterations=10)` só é construído na linha **443**. A ordem não é uma inferência de timestamp — é a ordem das instruções. **(e) (2) receita do cartão T8 · direta.**

#### A25 — DI-28 resolvida POR DADO: a árvore do treed_media **é** a do c311 (com 2 erratas contra a minha F5)

**(a/b)** O `sigma_dict` avisa: "⚠ NÃO é 'a mesma árvore byte-a-byte': o treino é INDEPENDENTE por config (DI-28); alg_id 19 vs 23 semeia RNGs distintos". Se as árvores diferissem materialmente, **toda a ablação estaria confundida**. **(c) O teste, re-executado e AMPLIADO.** Os dois configs recebem o MESMO dataset (`doe_hash` idêntico em 9/9) e a MESMA régua (`sonda.x_hash` idêntico em 9/9), com X bit-a-bit iguais no join posicional (verificado por `array_equal`). Nos pontos em que o c311 tem `sigma_j` NaN — folha SEM GP, onde o μ dele **é** a média da folha —, comparei μ ponto a ponto **nos DOIS blocos de sonda do c311** (a F5 usou um): **694.998 de 695.030 idênticos bit-a-bit = 99,9954%**; **32 divergentes**, \|Δμ\| máximo **2,59e-5**. **⚠ ERRATA 1 contra a minha F5:** ela disse "5/9 células 100% idênticas, todas LHS" e "as 4 células MVNS têm 2 a 8 divergentes". Medido: **6/9 são 100,0000%** — as 5 LHS **e `mvns/WFG9`** — e apenas **3 MVNS divergem** (`mvns/DTLZ2` 12, `mvns/ZDT1` 16, `mvns/ZDT4` 4, somando os 2 blocos). **(d)** O `DecisionTreeRegressor` com `splitter='best'` é determinístico dado o dataset; o `random_state=None` só entra no **desempate** entre cortes de ganho idêntico, que exige valores repetidos de f — fenômeno **exclusivo do MVNS** (quantização f32 + concentração). **(e) (2) sancionado (DI-28) · direta** — e o veredito é o oposto do temido: **a ablação é limpa**; 99,995% da superfície de predição é a mesma árvore, e a diferença c311×treed é atribuível **aos GPs locais**, que é a premissa inteira da F5.5.

#### A26 — Rito de escrita: `motivo_parada` normativo em 10/10, footer heterogêneo (2ª errata) — e o que a T11 consertou

**(a/b)** Etapa 1.2 do protocolo: para a família offline standalone o campo normativo é `footer.motivo` (e `motivo_parada` no ⑤), nunca `status` sozinho (bug B1). **(c)** `motivo_parada='orcamento'` + `status='ok'` no ⑤ em **10/10**; `footer.motivo='orcamento'` em 9/10. **⚠ ERRATA 2 contra a minha F5:** ela disse "4 células com 2 footers, 5 com 1, 1 com 0". Medido linha a linha: **3 com 2** (`mvns/DTLZ2`, `mvns/WFG9`, `mvns/ZDT1` — todas do lote 2026-07-26T11:23), **6 com 1**, **1 com 0** (`mvns/MMF16_20`). A célula sem footer é a única com `upload_status={'real':'pending',…}`, e o run científico está **provadamente completo**: 1.000 gerações densas, sonda de 20.000 com `hash_check='ok'`, ⑦ com 102 linhas / 69 ND, e todas as checagens estruturais desta bateria passam nela. **(d) 🆕 O que a T11 mudou aqui.** (i) `AuditLogger` ganhou **B-01** (`RunJaFechado` + `footer_fechado()`, que elege o **primeiro footer com `fe_final` não-nulo** como a certidão de fechamento). Medi: nas 3 células de 2 footers, o segundo footer tem **`fe_final = None`** em 3/3 ⇒ o discriminador do B-01 acerta e **a armadilha (25) da F5 fica desarmada para quem usar a função canônica** (quem contar footers continua errando). (ii) **B-11** (1 linha = 1 `os.write` sob `O_APPEND`, `flock` acima de `PIPE_BUF`): medi os tamanhos de linha deste config — o `header` tem **5.895–5.966 B**, ou seja **11,5× o `PIPE_BUF` do macOS (512 B)**, e **10 das 32 linhas (31,2%)** do ⑥ da s42 estavam acima do limiar atômico. **Zero linhas malformadas** em ambos os corpora — o risco era latente e nunca se realizou neste config, mas a superfície era real. (iii) O que **NÃO** foi consertado: o caminho que perdeu o footer/`upload_status=pending` no `env_c311` — nenhum item da T11 o nomeia. **(e) (2) por ambiente, caveat pré-registrado · direta.**

#### A27 — O motor busca de fato? Sim, e a curva mostra onde ele para

**(c)** Média de Σμ_j por geração, ger 1 → 1000: melhora de **1,69%** (`lhs/ZDT1`) a **25,57%** (`lhs/ZDT4`), mediana ~14,3%. **(d)** Duas causas: (i) o RVEA readapta os vetores 10 vezes (A18), o que reembaralha a população; (ii) a superfície é constante por partes — depois de achar as folhas boas não há gradiente, e a busca vira exploração entre folhas. **(e) (2) comportamento esperado do desenho · direta.**

---

## 3. Percentuais por classe

**Denominador explícito = 35 aspectos enumerados − 3 T = 32.**

| classe | contagem | % (denominador **32**) |
|---|---|---|
| **(1)** conforme o método canônico | **7/32** | **21,9%** |
| **(2)** desvio sancionado (decisão citada em cada linha) | **23/32** | **71,9%** |
| **(3)** desvio inexplicado 🎯 | **2/32** | **6,3%** |
| **T** teto declarado (**fora** do denominador) | **3** | T1 agregador da folha · T2 vendor/env/fonte única · T3 semeadura D62 + LHS DI-28.3 |

**(1)** = A1 · A9 · A11 · A16 · A18 · A20 · A21.
**(2)** = A2 · A3 · A4 · A5 · A6 · A7 · A8 · A10 · A12 · A13 · A14 · A15 · A17 · A19 · A22 · A23 · A24 · A25 · A26 · A27 · N1 · N2 · N5 (23).
**(3)** = **N3** (`tempo_aval_real_s` no offline) · **N4** (custo do checkpoint dentro de `tempo_busca_s`).

**Comparação com a F5:** ela imprimiu 27 no denominador com **(1) 25,9% · (2) 74,1% · (3) 0,0%**. A proporção alta de (2) permanece ESPERADA e não penaliza — `treed_media` é artefato de desenho nosso, então quase todo aspecto é uma decisão nossa citada. **A mudança real é 0 → 2 na classe (3), e ambos nasceram NA T11.**

---

## 4. 🆕 AS CORREÇÕES DA T11 — implementadas? funcionam de fato?

> Legenda da evidência: **(i) código lido** (arquivo:linha) · **(ii) veredito registrado pela T11** · **(iii) dado medido** (s42 ou smoke).

### N1 · DI-43 · Checkpoint atômico periódico — ✅ **IMPLEMENTADO E FUNCIONA; não-perturbação MEDIDA**

**(i)** `src/treed_media.py:72` (import), `:372-374` (instância), `:459-460` (`ckpt.talvez_gravar` dentro do laço); `src/checkpoint.py:104-131` grava ①②③④ + um ⑤ `failed`/`checkpoint_em_andamento` **por último** (o `fe_final` é PISO, nunca promessa).
**(iii) O campo existe E o dado é real:** 10 eventos `checkpoint` no ⑥ do smoke, com `iteracao` 100…1000, `n_linhas_terceira` 24.566→57.281 e `tempo_checkpoint_s` 0,3066–0,4502 s. **Não é sentinela** — cruzei `n_linhas_terceira` contra o cumulativo real da ③ e casa em 10/10.
**A prova que ninguém tinha — o invariante nº 1 do módulo ("não muda o resultado"), medido em produção e não em brinquedo.** O repo o testa com `test_checkpoint_nao_muda_o_resultado` (tempdir sintético). Eu o testei na célula real:

| camada | s42 (pré-T11, `bfe68a2`) | smoke T11 (`9ad0138a`) | veredito |
|---|---|---|---|
| ① real | 50.000 × 18, hash `7456ba78017ee7f6` | 50.000 × 18, hash `7456ba78017ee7f6` | **BIT-IDÊNTICA** |
| ③ surrogate | 57.281 × 29, hash `e5b30488d7853c24`, **1.472.124 B** | 57.281 × 29, hash `e5b30488d7853c24`, **1.472.124 B** | **BIT-IDÊNTICA** |
| ⑦ final | 37 × 19, hash `f9edf25002155bcd` | 37 × 19, hash `f9edf25002155bcd` | **BIT-IDÊNTICA** |
| ② pop | 0 linhas | 0 linhas | idêntica |
| ⑥ footer | `ok/orcamento/fe=50000/n_ger=1000/n_final=37/n_nd=8` | idem, campo a campo | idêntico |

**Consequência para esta missão:** a premissa "a busca da rodada-42 é a mesma busca que o código de hoje faria" deixou de ser inferência para este config — **está medida**, em 107.318 linhas de dado. E, de brinde, entregou a prova determinística do 10×100 (A18).
**O que ainda falta:** nada funcional. Uma nota de operação: em `treed_media` a cadência efetiva é **1 checkpoint por `iterate()`** (o `iteracao` salta de 100 em 100 e o gatilho é `≥ 25`), ou seja **10 reescritas completas das 4 camadas por célula**, não a cadência "K=25" que o docstring sugere.

### N2 · DI-42.5/A10 · Guard de tier — ✅ **IMPLEMENTADO E VERIFICADO POR EXECUÇÃO**

**(i)** `src/treed_media.py:329-335` — é a **primeira instrução** da função, antes de `_import_vendor` (o que o comentário diz e o teste confirma).
**(iii) Executei o guard** (`tm11_06_guard_tier.py`, tempdir vazio, zero arquivos escritos):

| `exp` | `parse_sweep` | resultado |
|---|---|---|
| `off` · `main` · `batch` | tier=`None` | **BARROU** `ValueError` |
| `sweep-small-lhs` · `sweep-medium-mvns` | tier=`small`/`medium` | **BARROU** `ValueError` |
| `sweep-big-lhs` · `sweep-big-mvns` | tier=`big` | **PASSOU** (falha depois, em `No module named 'GPy'` — prova de que o guard fira ANTES do `_import_vendor`) |
| `alg='c311'` | — | **BARROU** (guarda antiga do T8) |

**Este é um gate que REPROVA** (5 recusas + 2 passagens), não decorativo. **E o perigo que ele fecha é grande e eu o quantifiquei:** `naming.dataset_variant('off')` e `dataset_variant('sweep-small-lhs')` devolvem **`(None, None)`**, o que faria `load_offline_budget` carregar o dataset **PRINCIPAL** (31D−1 = **309** linhas em D=10, **162× menor**) e gravá-lo sob o nome desta célula, com `tier`/`dist` do manifesto dizendo outra coisa — **um dataset trocado, internamente coerente e indetectável a jusante**. No código pré-T11 (`bfe68a2`) essa chamada seguia adiante em silêncio. **O que ainda falta:** nada. Ressalva de escopo: nenhuma célula da s42 exercitou o buraco (as 300 linhas do grid deste config são todas `tier=big`) — o guard é defesa em profundidade, não conserto de incidente.

### N3 · I-02 · `tempo_aval_real_s` no OFFLINE — ⚠ **IMPLEMENTADO, MAS NÃO FAZ O QUE DIZ** 🎯 classe (3)

**Este é o padrão que a missão mandou caçar** — só que na direção inversa do c217: lá o campo existia com dado sentinela; **aqui o dado existe e é a semântica que está errada.**

**(i) O que o código promete.** `src/treed_media.py:520-526`:
> `# [I-02] NULL, não 0.0: no OFFLINE o orçamento nasce ESGOTADO (a ① é o dataset, D90) e nenhuma avaliação real acontece DENTRO do run — gravar zero afirmaria "avaliar custou zero". `bud.tempo_aval_real_s` **devolve None quando nenhuma avaliação passou pelo portão**.`

(o gêmeo literal está em `src/standalone_harness.py:1661-1666`.)

**(iii) O que o dado diz.**

| corpus | `treed_media` | b5m | b5r | c311 | moead_media |
|---|---:|---:|---:|---:|---:|
| **s42 (pré-T11)** | 0,0 em 10/10 | 0,0 em 45/45 | 0,0 em 45/45 | 0,0 em 55/55 | 0,0 em 45/45 |
| **smoke T11** | **0,0572** | **0,0001** | **0,0003** | **0,0003** | **0,0001** |

**Não é NULL em nenhum dos 5 configs offline Python.** Nas 200 células offline Python da s42 o valor era `0.0` exato; hoje é um número positivo.

**(d) Por quê — a cadeia, medida e lida.** `src/standalone_harness.py:647-653`, dentro de `load_offline_budget`, ingere o dataset assim:
```python
bud = _budget.FEBudget(D=ds["D"], maxfe=n, n_init=n, logger=logger)
for i in range(n):
    bud.evaluate(X[i], lambda _x, _f=F[i]: _f)
```
Ou seja: **as 50.000 linhas passam pelo portão único** `FEBudget.evaluate`, cujo cronômetro novo (`src/budget.py:249-252`) mede o tempo do `true_f` — que aqui é um **lambda pass-through** devolvendo a linha já congelada do artefato. E `src/budget.py:198-202` só devolve `None` quando `_n_avals_cronometradas == 0`; após a ingestão ele vale 50.000. **A premissa "nenhuma avaliação passou pelo portão" é falsa por construção do próprio harness offline.**

**A assinatura quantitativa que prova que nada foi avaliado:** o custo por FE é **0,97–1,64 µs** nos 5 offline contra **22,95–34,43 µs** nos 5 online do mesmo smoke (c122/c149/c154/c262/e81, mesmo problema MMF1, mesma máquina) — **~21× mais barato**, porque no offline não há função-objetivo nenhuma sendo chamada, só um `lambda` e um `reshape`. Em `treed_media` são **1,144 µs/FE × 50.000 = 0,0572 s** de despacho de ingestão.

**(iii-b) E o teste passa verde.** `tests/test_g7_instrumentacao.py:118-126` (`test_os_offline_declaram_NULL_em_vez_de_zero`) é um **grep de texto-fonte**: ele só assere que a string `"tempo_aval_real_s=0.0"` não aparece nos 5 runners offline. Nunca abre um manifesto, nunca chama `bud.tempo_aval_real_s`. É exatamente a espécie que a §4.2 do próprio T11 declara extinta ("um gate que nunca reprova é decorativo") — e é a razão pela qual isto atravessou a campanha.

**Impacto — delimitado, mas real.** Não move a busca (N1 prova bit-identidade). Mas: (a) **quebra a assinatura U1** que a auditoria de fidelidade usa para provar "offline puro" — um auditor que aplique o teste da F5 (`tempo_aval_real_s == 0`) ao dado novo levanta falso-alarme em 100% das células offline; (b) publica um número que **afirma o contrário do que a I-02 quis afirmar**: "avaliar custou 57 ms" num run que não avaliou nada.

**Conserto (recomendação, 1 linha):** zerar o cronômetro ao fim da ingestão em `standalone_harness.py:654` (`bud._tempo_aval_real_s = 0.0; bud._n_avals_cronometradas = 0`) ou expor um `bud.reset_cronometro()`, **com um teste de COMPORTAMENTO** (abrir o ⑤ de um run offline em tempdir e assertar `is None`), não de grep. **Verdadeiro para os 5 configs offline Python — escalar como item transversal, não como item do `treed_media`.**

### N4 · DI-43 · O custo do checkpoint está DENTRO de `tempo_busca_s` e `tempo_geracao_s` 🎯 classe (3)

**(i)** `src/treed_media.py:444` (`t_f0 = time.time()`) → laço com `evf.iterate()`, `H.iteration_cleanup()` **e `ckpt.talvez_gravar(...)`** → `:461` (`t_busca_total = time.time() - t_f0`) → `:490` (`tempo_geracao_s = t_fit + t_busca_total`). O I/O do checkpoint cai inteiro dentro do cronômetro da busca.
**(iii) A conta fecha:**

| | s42 (sem checkpoint) | smoke T11 (10 checkpoints) |
|---|---:|---:|
| `tempo_fit_s` | 0,625579 | 0,620631 |
| `tempo_busca_s` | **3,270513** | **6,969877** |
| Σ `tempo_checkpoint_s` (⑥) | — | **3,753900** |
| `tempo_busca_s` − checkpoint | 3,270513 | **3,215977** (−1,67%) |
| `tempo_geracao_s` | 3,896092 | 7,590508 |
| `tempo_total_s` (wall) | **5,8615** | **11,7240** (2,00×) |

⇒ **53,9% do `tempo_busca_s` e 49,5% do `tempo_geracao_s` pós-T11 são I/O de checkpoint, não busca.** Subtraindo o checkpoint, a busca reproduz a s42 a menos de 1,7%.

**Por que isso é (3) e não (2):** a **DI-13.10 é ratificada** e diz que `tempo_geracao_s` deve EXCLUIR a instrumentação deste estudo, precisamente para não contaminar a curva de escalabilidade — e o config a honra à risca para a sonda (A6, invariante dupla exata em 10/10 + no smoke). O checkpoint é instrumentação da mesma natureza e **não é excluído**. A DI-43/44 (REGISTRO A34/A35) manda gravar outputs intermediários e **não diz nada** sobre a contabilidade do tempo — não há decisão que sancione a contaminação; é omissão, não escolha.
**Escala projetada às 10 células** (regressão `t_ckpt = 0,2188 + 3,83e-6·n_linhas_③`, R²=0,71 sobre os 10 pontos do smoke — projeção, não medida): custo **3,75–5,16 s/célula**, **43,8 s** somados, inflação **30,1%–64,0%, mediana 48,5%**. Para este config é dinheiro miúdo em absoluto (células de 6–16 s), mas **envenena a razão** que a F5.2d/M8 usa: qualquer projeção de 30 sementes lida de `tempo_busca_s`/`tempo_total_s` pós-T11 estará ~50% inflada para os pisos offline, e o efeito é **maior nas células baratas** (proporcionalmente), o que distorce o ranking de custo entre configs.
**Conserto (recomendação, 2 linhas):** cronometrar o checkpoint fora (`t_busca_total -= ckpt.tempo_total_s`, que **já existe** — `checkpoint.py:122`) ou publicar `tempo_checkpoint_total_s` no bloco `timing` do ⑤ e mandar a R4 subtraí-lo. O instrumento já mede o próprio custo; falta descontá-lo.

### N5 · G3/I-09/schema v2 · Proveniência no ⑤ — ✅ **IMPLEMENTADO E PRESENTE**

**(iii)** No smoke: `campanha_id="9ad0138aa9a4_2026-07-31"`, `repo_hash="9ad0138aa9a464a7d9f89d247f81092f8c4ef26f"`, `schema_version=2`. Na s42: **ausentes em 10/10** (`campanha_id` inexistente, `repo_hash=null`, `schema_version=1`). Confirma, por medida direta neste config, o que a torre já mediu em c122/b5m/c217/b4 — **a instrumentação nova não existe no dado da s42**, e por isso a fidelidade de mecanismo teve de ser medida na s42 e as correções no smoke/código.
**Ressalva honesta:** o `repo_hash` do smoke (`9ad0138a…`) **não é o HEAD atual** do repo — é o commit da execução do smoke; é o que se espera de um carimbo de proveniência, mas quem for auditar `anchors.json`/`repos.lock` tem de ancorar nele, não no HEAD.

### N6 · B-09 (espelho no aborto) — ✅ implementado, ⬜ **não exercitado neste config**

**(i)** `src/treed_media.py:507-511` passa `enable_bucket=enable_bucket` ao `write_failed_manifest`. **(iii)** Nenhuma célula deste config falhou (status `ok` em 10/10, teto com folga 2.749×), então o ramo é **código não-testado nesta rodada** — mesma situação do rito de teto (A23).

### N7 · B-01 / B-11 no ⑥ — ✅ implementado; efeito **latente** aqui

Medido em A26: o discriminador do B-01 (`fe_final` não-nulo) resolve corretamente as 3 células de 2 footers (segundo footer com `fe_final=None` em 3/3); o B-11 cobre as **10 de 32 linhas (31,2%)** que passam do `PIPE_BUF` do macOS neste config — **zero malformadas** em ambos os corpora, ou seja, risco real nunca realizado.

### O que a T11 **NÃO** fechou neste config

1. **A célula `swap_big-mvns_MMF16_20`**: ⑥ sem footer + `upload_status` `pending` (única das 10). Nenhum item da T11 nomeia o caminho `gcs` do `env_c311`. A triagem de término dela continua dependendo de `n_geracoes`+③+bloco de sonda (regra da Etapa 1.2), não do footer.
2. **A heterogeneidade de rito de footer** (armadilha 25 da F5) segue viva no dado; o B-01 dá a leitura canônica, mas qualquer checagem que **conte** footers continua quebrando.
3. **Os 3 itens do balde T** (agregador da folha, vendor/env, semeadura) continuam exigindo código/re-run — a T11 não os tocou.

---

## 5. PAPEL DE CONTROLE (a Entrega 2 é **N/A** — config sem artigo)

**(i) A régua oficial não serve, e é estrutural.** Re-verificado em `metricas_finais_f52c.csv`: IGD+, HV, IGD, GD, spacing e \|ND\| são **idênticos dígito a dígito** entre c311 e `treed_media` em **9/9** pares (D69, A14). Qualquer ranking do tier big feito sobre a métrica oficial é vazio por construção. **O papel de régua do `treed_media` vive INTEIRAMENTE na ⑦.**

**(ii) Na ⑦, o piso discrimina.** Re-medi a fantasia (`nd_pos_real/n_final`) dos dois configs nas 10 células:

| dist/problema | fantasia c311 | fantasia treed | quem vence |
|---|---:|---:|---|
| lhs/DTLZ2 | 0,9619 (101/105) | 0,5810 (61/105) | c311 |
| lhs/MMF16_20 | 0,9524 | 0,7524 | c311 |
| lhs/WFG9 | 0,9800 (49/50) | 0,3478 | c311 |
| lhs/ZDT1 | 0,5600 | 0,2200 | c311 |
| **lhs/ZDT4** | **0,0800** (4/50) | **0,1944** | **treed ✔** |
| mvns/DTLZ2 | 0,9048 | 0,3627 | c311 |
| mvns/MMF16_20 † | 1,0000 (105/105) | 0,6765 | c311 |
| **mvns/WFG9** | **0,0200** (1/50) | **0,2340** | **treed ✔** |
| mvns/ZDT1 | 0,6531 | 0,2083 | c311 |
| **mvns/ZDT4** | **0,1400** | **0,2162** | **treed ✔** |

† o par da sonda desta célula é inválido (o ③ do c311 tem **0 linhas de sonda** — célula REPROVADA-F5.1); a ⑦ existe e entra aqui.

**c311 vence a fantasia em 7/10, `treed_media` em 3/10. O piso cumpre a função** — é pior que o SA na maioria, o que dá ao c311 uma régua com contraste real onde a métrica oficial dava zero.
**(iii) E o piso também é alarme.** Nas 3 células onde o `treed_media` ganha, a fantasia do c311 **colapsa** (0,0200 em `mvns/WFG9` — 1 ponto de 50 sobreviveu; 0,0800 em `lhs/ZDT4`; 0,1400 em `mvns/ZDT4`). Os GPs locais são uma **aposta de alta variância**: quando acertam levam a fantasia a 0,90–1,00; quando erram, abaixo do piso. Um controle que só perdesse não sinalizaria isso.
**(iv) A correção de prior segue de pé.** O prior "~100× mais barato que o c311-big" **não se confirma** (F5: 3,90×–29,81×, mediana 10,0× no wall). E **a T11 pioura o número**: com os 10 checkpoints por célula, o wall do piso infla ~48,5% (N4), estreitando ainda mais a vantagem de custo que justifica o config. Recalibrar antes do D97.

---

## 6. Saúde (s42 = corpus principal)

**Contrato e integridade.** `contrato_f52b.csv` e `integridade_f52a.csv` filtrados a `treed_media`: **ZERO linhas** — limpos nas 10 células. `params` presente no ⑤ em 10/10 (a **ERRATA 11 da T11** — "7 configs sem `params` na s42, eram 1" — não toca este config). Gates F5.1: 10/10 verdes. Portões T11: **6/6 exceto G-1 e G-7, ambos ⚪ n/a por desenho** — G-1 porque `real_solution_id` é 100% nulo (A12: sem marca não há identidade a conferir) e G-7 porque o ⑥ não tem evento de geração; a T11 registra que o ⑤ **foi auditado assim mesmo** (4/4) depois do conserto de 2026-07-30.

**Sonda — a régua Sobol, bloco ÚNICO (regra 12 do CONTRATO: não há bloco `sonda_estratificada` neste config; a ③ tem só `offline` e `sonda`, verificado em 10/10).** Padrão nítido por família e idêntico ao do c311: **ZDT f0 quase-exato** (WAPE 0,00195–0,00811, corr >0,9999) · **MMF16_20** 0,0339–0,0949 (corr 0,984–0,996) · **DTLZ2** 0,0910–0,1304 (corr 0,956–0,977) · **WFG9 ruim** (WAPE 0,2208–0,2827, **corr 0,1219–0,4244**) · **segundo objetivo teimoso** no ZDT4/ZDT1 (0,1292–0,3068, corr 0,418–0,814) — a componente `g` desses problemas é multimodal e a média de folha não a captura. **Cobertura N/A em 24/24 por regra do protocolo §5** (σ NULL) — este config é o exemplo limpo de como a métrica DEVE ser reportada.

**Endpoint.** Fantasia mediana **0,2909** (0,1944–0,7524). Par LHS×MVNS sem padrão monotônico, **1 semente** ⇒ descritivo, não teste (M13 fará a estatística).

**Comportamento do motor.** Progride 1,69%–25,57% na média de Σμ; num surrogate constante por partes com ~76% do teto de folhas ocupado, as 1.000 gerações são folgadas — o custo marginal delas é o que o piso paga para ser comparável ao c311, não para convergir.

**Ressalva de leitura R4#11 (regra nova).** Toda dominância que calculei sobre a ⑦ carrega a perda do float32. Neste config a ressalva é **inócua por desenho**: o `write_final` (DI-27/A15) computa o `nd_pos_real` **na mesma vista f32** que eu recomputo, e a busca nunca decidiu nada com a ⑦. Onde a distinção importaria (a ③), usei chave de **bytes** e não comparação numérica (A9).

---

## 7. SCORE, recomendação e VEREDITO vs a F5

### SCORE: **9,5/10** · RECOMENDAÇÃO: **ACEITAR o mecanismo + CORRIGIR 2 itens de instrumentação ANTES do disparo** (ambos ≤2 linhas, ambos transversais aos 5 offline Python)

### VEREDITO: **MANTEVE** — com o mecanismo mais VERIFICÁVEL e duas regressões de instrumentação nomeadas

**A causa do "manteve", nomeada:** **o mecanismo não mudou, e desta vez isso não é inferência — é medida.** As camadas ①③⑦② da célula `sweep-big-mvns/ZDT4/42` saem **bit-idênticas** antes e depois da T11 (107.318 linhas; a ③ com os mesmos 1.472.124 bytes). Não há "amostra diferente", não há deriva numérica, não há re-classificação de aspecto por mais evidência: o algoritmo de hoje é literalmente o algoritmo de 24/07. Por isso a nota de FIDELIDADE fica onde estava.

**O que MELHOROU (e é substantivo):**
1. **A18 saiu do balde estatístico.** A decomposição 10×100 do RVEA — o único aspecto do mecanismo central que a F5 só sustentava com um teste de permutação (p≤0,053 em 10/10) — agora é **observação determinística**: 10 eventos `checkpoint` em `iteracao`=100,200,…,1000, um por `iterate()`, com `n_linhas_terceira` casando com a ③ em 10/10.
2. **A premissa desta campanha inteira ficou provada para este config.** "A busca da s42 é a que o código de hoje faria" era, no briefing, uma extrapolação de 19 pares MATLAB. Aqui está medida, bit-a-bit.
3. **Um buraco real de silêncio foi fechado e eu o executei** (N2): o guard de tier barra 5/5 despachos errados, e o dano que ele evita é um dataset **162× menor** gravado sob o nome desta célula com o manifesto internamente coerente.
4. **A proveniência chegou ao ⑤** (`campanha_id`/`repo_hash`/schema v2), medida.

**O que PIOROU (0 → 2 aspectos classe (3)):** ambos nasceram na T11, ambos vivem na camada de TEMPO, nenhum toca o laço de decisão — mas ambos publicam número errado. **N3**: `tempo_aval_real_s` = 0,0572 s num run que não avaliou nada, contra um comentário de código que promete `None`, com o teste que deveria pegá-lo sendo um **grep de texto-fonte** que passa verde. **N4**: 53,9% do `tempo_busca_s` pós-T11 é I/O de checkpoint, contaminando exatamente a grandeza que a DI-13.10 protege da sonda.

**Por que não cai para 8** (a régua diria "(3) periférico com explicação plausível não provada"): meus dois (3) **estão provados**, com a cadeia causal lida linha a linha e o efeito quantificado; nenhum está no mecanismo (que é bit-idêntico); e cada um tem conserto de 1–2 linhas já identificado. **Por que não sobe para 10:** existem 2 (3), 1/10 células perdeu o footer (caveat pré-registrado, não fechado pela T11), o ⑥ só tem 32 eventos em 10 células (não há registro por geração) e o balde T continua com 3 itens.

**Se os dois (3) estivessem no mecanismo, a nota seria 7.** Estão na instrumentação, e a instrumentação é reparável antes do disparo — daí a recomendação dupla.

**Escalações ao autor (D97):**
- 🔴 **N3 e N4 são TRANSVERSAIS** aos 5 configs offline Python (`treed_media`, `c311`, `b5r`, `b5m`, `moead_media`) e o N4 aos 8 runners com checkpoint. Consertar **antes** do disparo das 695 células, ou toda a projeção de 30 sementes e todo o `tempo_heatmap` nascem com ~50% de inflação nos pisos e com um `tempo_aval_real_s` que mente.
- 🟠 **Substituir `test_os_offline_declaram_NULL_em_vez_de_zero` por um teste de comportamento.** É o exemplar vivo do "gate decorativo" que a §4.2 da T11 diz ter extinguido.
- 🟡 **Errata ao `evidencia_T11/LEIA-ME.md` e ao T11 §15.2**: os smokes Python **estão** preservados em `evidencia_T11/smoke_python/` (11 células). O documento está mandando os validadores de fidelidade jogarem fora evidência que existe.

---

## 8. Aspectos classe (3) 🎯 — evidência completa

### 🎯 (3) N3 — `tempo_aval_real_s` no offline: o campo mede a INGESTÃO do dataset, não uma avaliação

- **O que se afirma:** `src/treed_media.py:520-524` e `src/standalone_harness.py:1661-1665` — "nenhuma avaliação real acontece DENTRO do run · `bud.tempo_aval_real_s` devolve None quando nenhuma avaliação passou pelo portão".
- **O que o dado diz:** **0,0572 s** no smoke de `treed_media`; **0,0001–0,0003 s** em b5m/b5r/c311/moead_media. Zero NULLs em 5/5 configs offline. Na s42 (pré-T11) era `0.0` exato em **200/200** células offline Python.
- **Cadeia causal, lida:** `standalone_harness.py:647-653` chama `bud.evaluate(X[i], lambda _x,_f=F[i]: _f)` **n vezes** na ingestão → `budget.py:249-252` cronometra cada uma → `budget.py:198-202` só devolve `None` se `_n_avals_cronometradas == 0`, que aqui vale 50.000.
- **Assinatura quantitativa que prova que nada foi avaliado:** 0,97–1,64 µs/FE nos offline contra 22,95–34,43 µs/FE nos 5 online do MESMO smoke (mesmo problema, mesma máquina) — **~21×**.
- **Por que ninguém pegou:** `tests/test_g7_instrumentacao.py:118-126` é grep de texto-fonte; passa verde com o comportamento errado.
- **Impacto:** quebra a assinatura U1 usada pela auditoria de fidelidade em 100% das células offline; publica um número que afirma o contrário da intenção da I-02. **Não toca a busca** (provado por N1).
- **Conserto:** zerar o cronômetro ao fim de `load_offline_budget` (`standalone_harness.py:654`) + teste de COMPORTAMENTO sobre o ⑤.

### 🎯 (3) N4 — o custo do checkpoint (DI-43) está dentro de `tempo_busca_s` e `tempo_geracao_s`

- **Sítio:** `src/treed_media.py:444` (`t_f0`) … `:459-460` (`ckpt.talvez_gravar`) … `:461` (`t_busca_total`) … `:490` (`tempo_geracao_s = t_fit + t_busca_total`).
- **Medida (smoke × s42, mesma célula):** `tempo_busca_s` 3,270513 → **6,969877** s; Σ `tempo_checkpoint_s` do ⑥ = **3,753900** s; `busca − checkpoint` = 3,215977 s, que reproduz a s42 a **−1,67%**. ⇒ **53,9% do `tempo_busca_s`** e **49,5% do `tempo_geracao_s`** são I/O. Wall total 5,8615 → 11,7240 s (**2,00×**).
- **Por que é (3):** a **DI-13.10** (ratificada) manda excluir a instrumentação deste estudo de `tempo_geracao_s`, e o config a honra à risca para a sonda (invariante dupla exata em 10/10 e no smoke). A **DI-43/44** (REGISTRO A34/A35) manda gravar outputs intermediários e **é silenciosa** sobre a contabilidade do tempo. Não há decisão que sancione a contaminação.
- **Escala (projeção, R²=0,71):** 3,75–5,16 s/célula, 43,8 s nas 10, inflação **30,1%–64,0% (mediana 48,5%)** — proporcionalmente **maior nas células baratas**, o que distorce o ranking de custo entre configs no `tempo_heatmap`/M8.
- **Conserto:** `checkpoint.py:122` **já acumula** `self.tempo_total_s`; basta descontá-lo de `t_busca_total` ou publicá-lo no bloco `timing` do ⑤ para a R4 subtrair.

---

## 9. Teto de verificabilidade (T) e armadilhas

**T — 3 itens (fora do denominador de 32):**
1. **T1 · `selection_type='mean'` e o agregador da folha** — declarado em 10/10; a condição NECESSÁRIA (μ ∈ envelope do dataset) passa em 24/24, mas **média × mediana da folha não é separável ex-post**. Exige código.
2. **T2 · Vendor c311 INTOCADO / fonte única / `env_c311` / pinning** — declarativo (`algo_version`, `sigma_dict.vendor`, `env`), com corroboração indireta muito forte via A25 (árvore idêntica em 99,995%). Elo coberto por `anchors.json`+`repos.lock` — e agora **ancorável no `repo_hash=9ad0138a…`** do ⑤ (N5), que é um ganho real de rastreabilidade sobre a F5.
3. **T3 · Semeadura D62 `iteration_seed(42,23,0,0)` + gancho `_lhs_determinismo` (DI-28.3)** — só re-run bit-idêntico prova. ⚠ **Nuance nova:** a bit-identidade s42×smoke (N1) é evidência **forte mas não conclusiva** para o T3 — ela prova que o mesmo código com a mesma semente na mesma máquina dá o mesmo resultado, não que o LHS seja reprodutível **através de máquinas/versões de pyDOE**.

**Fora do balde T, limitações de OBSERVABILIDADE:** (a) o ⑥ **não tem evento de geração** — 32 eventos em 10 células na s42, 13 no smoke; o filme do mecanismo vive na ③, e por isso `max_depth` e a identidade da folha escolhida não são observáveis como no c311; (b) o **ramo de aborto por teto** (DI-35.5) e o **B-09** (espelho no aborto) nunca foram exercitados — código não-testado nesta rodada.

**Armadilhas (numeração continuando a da F5, que ia até 27):**
- **(28) 🆕 "O smoke Python não existe" é falso.** `evidencia_T11/smoke_python/` tem 11 células (2026-07-31 10:45–11:41), incluindo a de `treed_media`. O `LEIA-ME.md` e o T11 §15.2 dizem o contrário. **Errata nova para a torre.**
- **(29) 🆕 `tempo_aval_real_s ≠ 0` no offline NÃO significa que houve avaliação real** (N3). Quem usar o campo como discriminador de regime a partir da T11 erra em 5 configs.
- **(30) 🆕 `tempo_busca_s`/`tempo_geracao_s` pós-T11 incluem o I/O do checkpoint** (N4). Toda análise de custo/escalabilidade tem de subtrair `tempo_checkpoint_s` do ⑥ — que existe e está medido, mas não está descontado.
- **(31) 🆕 Os eventos `checkpoint` são um instrumento de FIDELIDADE, não só de resiliência.** Em `treed_media` eles cravam a decomposição 10×100 (A18); em qualquer config cujo `iteracao` seja o contador do motor, o mesmo truque vale.
- **(32) 🆕 A cadência real do checkpoint não é "K=25".** Como `iteracao` salta de 100 em 100, o gatilho `≥25` dispara a cada `iterate()` — **10 reescritas completas das 4 camadas por célula**, não a cadência que o docstring sugere.
- **(33) 🆕 Contar footers continua quebrando; use `audit_log.footer_fechado()`.** Medido: 3 células com 2 footers, 6 com 1, 1 com 0 — e o segundo footer tem `fe_final = None` em 3/3, que é exatamente o discriminador do B-01. *(Corrige a armadilha 25 da F5, que dizia 4/5/1.)*
- **Correções às minhas próprias armadilhas da F5:** a (22) e a (23) seguem válidas; a **(25)** vira 3/6/1 (acima); e a leitura de A25 vira **6/9 células 100% idênticas** (5 LHS **+ `mvns/WFG9`**), **3 MVNS divergentes**, não 5/9 e 4.

**O que este corpus NÃO permite verificar:** (i) qualquer coisa que exija re-run bit-idêntico em OUTRA máquina (T3); (ii) o agregador da folha e o `selection_type` (T1); (iii) o elo código↔dado do vendor (T2); (iv) o ramo de teto e o de aborto; (v) **a não-perturbação sonda-on/sonda-off deste config** — o par G-6 do `treed_media` (hash `dd03ee216118d017`, ① BIT-IDÊNTICA, e antes `9c06dd44`) é **veredito registrado (T11_STATUS.md:348)**, não dado preservado: `evidencia_T11/g6_com|g6_sem` só contêm os 8 MATLAB + e103. O que eu pude verificar é o **mecanismo** (`emit_sonda_block` roda sob `preserve_all_rng`, `standalone_harness.py:824`, e é chamado na linha 433, **antes** de o RVEA sequer ser construído na 443 — a sonda deste config é estruturalmente incapaz de mover a busca); (vi) comportamento em **escala** (695 células × 30 sementes: concorrência, disco, memória) — 10 células numa máquina não o cobrem.

---

### Artefatos desta análise
Tudo em **`/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/treed_media/`** (interpretador `/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python`; READ-ONLY sobre os dados — nada foi escrito em `data/`, `resultados_experimentos/` ou `evidencia_T11/`, e nenhuma célula foi rodada).

**Scripts:** `tm11_01_estrutura.py` (10 células s42 + smoke, 134 colunas) · `tm11_02_prepos.py` (**pré×pós T11 bit-a-bit**) · `tm11_03_i02.py` (**o achado N3**, 11 smokes + 245 células offline da s42) · `tm11_04_mecanismo.py` (**re-medida completa** U1/U2/U3/U4/U5/U6/U7/U12/F1/F2/C1/C2/C5/C7/C9/C17) · `tm11_05_arvore_footer.py` (identidade da árvore vs c311 + footers + **projeção do custo do checkpoint**) · `tm11_06_guard_tier.py` (**execução do guard N2**, tempdir, 0 arquivos).
**Evidência:** `tm11_estrutura_s42.csv` · `tm11_prepos.txt` · `tm11_i02_smoke.csv` · `tm11_i02_s42_offline.csv` · `tm11_mecanismo_s42.csv` · `tm11_arvore_identidade.csv` · `tm11_footers.csv` · `tm11_checkpoint_projecao.csv`.
**Insumos pré-computados consumidos (não recomputados):** `f5/metricas_finais_f52c.csv` · `f5/sonda_f52e.csv` (recomputei o WAPE e conferi 24/24) · `f5/contrato_f52b.csv` · `f5/integridade_f52a.csv` · `f5/tempo_f52d.csv`.
**Fontes normativas lidas:** `f5/PROTOCOLO_ANALISE_FIDELIDADE.md` · `handoff/F5-FRAMEWORK-v2.md` · `f5/relatorios_config/treed_media.md` · `handoff/T11-RODADA-FINAL.md` (§3, §5, §8, §15) · `CONTRATO_DE_DADOS.md` §10 (regras 11 e 12) · `claude_code_context/30_rodada3_standalone/alg_c311_tgprmo.md` · `REGISTRO_DECISOES_IMPLEMENTACAO.md` (A34/A35 = DI-43/44/45) · `handoff/T11-CONFORMIDADE.md` · `T11_STATUS.md`.
**Código lido (nunca escrito):** `src/treed_media.py` (562 linhas, integral) · `src/checkpoint.py` · `src/budget.py:150-270` · `src/standalone_harness.py` (`load_offline_budget`, `emit_sonda_block`, `preserve_all_rng`) · `src/audit_log.py` (diff T11) · `tests/test_g7_instrumentacao.py` · `tests/test_checkpoint.py` · `git diff bfe68a2..HEAD -- src/treed_media.py`.