# RELATÓRIO DE FIDELIDADE — b5r (Prob-RVEA, mode 7) · **validação T11** · protocolo v1.1 · Etapa 7

**Corpora usados, e o que cada um autoriza afirmar.**
**(A) s42 — o MECANISMO.** As **45 células** de `resultados_experimentos/b5r/{label}/42/` (25 `off` + 20 sweep). Re-medidas integralmente nesta rodada (`b5r_t11_bateria.py`, 45/45 lidas): **1.772.336** linhas de ③-busca · **900.000** de ③-sonda · **57.836** eventos `decision` · **57.836** gerações arquivadas (= **57.791** passos de seleção + 45 snapshots iniciais) · **2.195** linhas de ⑦ · **104** pares (célula,objetivo) de sonda · **56.081** transições pai→filho · wall **3,64 h-core**. 45/45 `status=ok`, `motivo_parada=orcamento`, `n_retries=0`, `fallback_ativado=False`, **0 linhas** em `integridade_f52a.csv`, todas no `mac` ⇒ **piso de ruído entre máquinas não se aplica**.
**(B) T11 — a INSTRUMENTAÇÃO.** 🆕 **O smoke Python do b5r EXISTE e está preservado**, ao contrário do que o prompt e o `evidencia_T11/LEIA-ME.md` afirmam (o LEIA-ME é de 10:13; a pasta é de 10:52). Local: `/Users/gmello/Documents/python_repos/mestrado/evidencia_T11/smoke_python/experiments/off/b5r/` — célula `BBOB_F22/42`, `campanha_id=9ad0138aa9a4_2026-07-31`, `repo_hash=9ad0138aa9a464a7…` (= HEAD). **Isso muda o teto desta análise**: as correções da T11 no b5r puderam ser **MEDIDAS**, não só lidas no código.

> **A prova de não-perturbação, para o MEU config, medida diretamente (não por analogia com os 19 pares g6 — o b5r não está em `g6_com/g6_sem`, que só tem os 9 MATLAB).** A célula `BBOB_F22/42` da s42 e o smoke T11 da mesma célula são **BIT-IDÊNTICOS**: ① (309×18), **③ (59.436 linhas × 29 colunas, coluna a coluna)** e ⑦ (39×19), `n_geracoes=1144` nos dois, mesmo `doe_hash`. ⇒ (i) a busca da s42 **é** a busca que o código de hoje faz; (ii) **A31 (determinismo bit-a-bit) sai do balde T** — re-run em código diferente, 3 dias depois, resultado idêntico.

---

## 1. Ficha do mecanismo (condensada)

Mazumdar, Chugh, Hakanen & Miettinen, *IEEE TEVC* **26**(5):1182–1191 (2022). **Offline puro**: 1 Kriging/GP por objetivo treinado **uma vez** no dataset (Alg. 1 l. 1); busca só no surrogate até **FEmax = 40.000** avaliações-surrogate (§IV-A4); zero reavaliação real. A contribuição é a **seleção**: S=1000 amostras MC da posterior (Eq. 10) → PDF do critério por **KDE** → ranking por **P_wrong** (Eq. 7–9). No RVEA isso muda (i) a **atribuição** a vetores de referência por **votação** (§III-A-1, Eq. 11–12, Fig. 4) e (ii) a seleção intra-subpopulação pelo **APD probabilístico** (Eq. 13–15). RVs por *simplex lattice*, **adaptados a cada 10 gerações** (§IV-A8); SBX η=30/p=1,0 + PM η=20/p=1/n; α=2; **pop inicial = o dataset** (Alg. 1 l. 2). Métricas do paper: HV e RMSE, 31 execuções, DBMOPP P1/P2 (n=10, K=2–10, **N_D=109**).

**Nossa config b5r** (D56: `b5` = 2 configs; `b5r`=mode 7 headline): `src/b5_prob.py` sobre o DESDEO **vendorizado** (`algorithms/b5_Prob-RVEA/`, root-first, `env_b5` py3.7.12 / sklearn 0.21.3), `ProbRVEA_v3 → Prob_APD_select_v3`. **Divergências sancionadas nomeadas**: **DI-28.1** (mode 7 = APD por **média-MC**, ratificada) · **B18.9** (pop inicial = **LHS novo**) · **v2.2/adapt** (RVs **FIXOS**, `adapt()` comentado em `ProbRVEA.py:226`) · **DI-16.16** (mini-patch pós-`keep()` em `BaseEA._next_gen`) · **DI-16.17** (② vazia + `real_solution_id` NULL) · **DI-13.5** (sonda `geracao`=NULL) · **DI-28.3** (gancho pyDOE) · **D90/D67/D51** (dataset = orçamento; tiers; LHS×MVNS) · **D-08** (`modelo_hp`/`dist_min_arquivo` NULL no offline) · **D56** (Hyb fora). 🆕 T11: **I-04** (`granularidade_③`), **I-07** (`params` no ⑤), **I-05** (3 campos DI-10 no ⑥), **I-02** (cronômetro no portão de avaliação).

---

## 2. DISSECAÇÃO DOS ASPECTOS — o CORE

### 2.1 Tabela-resumo

| # | aspecto | classe F5 | **classe T11** | verif. | resultado-síntese (re-medido na s42, salvo indicação) |
|---|---|---|---|---|---|
| A1 | offline puro: zero FE real na busca | (1) | **(1)** | direta | `fe`≡`maxfe` em **57.836/57.836** eventos · **0** `guard` · ② 0 linhas · `real_solution_id` NULL 100% |
| A2 | orçamento = dataset (31D−1 / 2.000); ① = dataset | (2) | (2) | direta | `len(①)==maxfe` **45/45**; `fase=='init'` 100%; `fe_index` denso 45/45 |
| A3 | proveniência ①↔artefato + CP-init | (1) | (1) | direta (gate) | `doe_hash==cp_init.x_hash` **45/45** |
| A4 | Kriging treinado 1× ⇒ ④ com 1 linha | (1) | (1) | direta | ④ = **1 linha 45/45**; `n_acumulado==N` 45/45; `fit_series` 1 entrada 45/45 |
| A5 | GPR `C(1,(1e-3,1e3))·RBF(10,(1e-2,1e2))`, α=0, 9 restarts, `normalize_y=False` | (2) | (2) | decl. **+ digital numérica** | σ máx global = **31,62277603** = √1e3 (teto exato do ConstantKernel) |
| A6 | consequência de A5: **colapso ao prior** | (2) | (2) | direta | **4/104** pares com σ no teto ≥99,90% (DTLZ3 f0 99,97% · f1 100% · f2 100% · DTLZ1 f2 99,90%); **3/104** com μ constante (DTLZ3 f1/f2, DTLZ4 f2) |
| A7 | σ exportado = desvio-padrão posterior | (2) | (2) | direta | `n_nan=0` em **104/104**; σ**=0** exato em **12** pares, **7** com >50%, máx **91,95%** (ZDT4/f0) |
| A8 | MC S=1000, `truncnorm(−3,3)` | **T** | **T** | não-verif. | amostras descartadas por desenho (L.16) |
| A9 | seleção = **média-MC do APD** ≠ P_wrong+KDE | (2) | (2) | decl. | `sigma_dict.fidelidade_por_modo` **45/45**; DI-28.1 |
| A10 | atribuição por **média de cos θ** ≠ votação | (2) | (2) | decl. | mesmo arquivo ratificado (v3) |
| A11 | 🎯 **o efeito do artigo sobrevive à aproximação** | (1) | **(1)** | direta | σ(desc)>σ(mant) em **35.647/56.081 = 63,56%** (z≈**64**); razão >1 em **39/45**, mediana **1,0429**, máx **2,3835** |
| A12 | identidade do argmin da média-MC | **T** | **T** | não-verif. | prole pré-seleção sobrescrita pelo DI-16.16 |
| A13 | pop inicial = **LHS novo** ≠ dataset | (2) | (2) | direta | **727/727 dimensões LHS-perfeitas em 45/45** (bounds reais); interseção X busca×dataset = **0** em 45/45 |
| A14 | **RVs FIXOS** ≠ "adapted every 10th gen" | **T** | **T** | não-verif. | continua sem eco em dado — e a instrumentação nova **não** o resolve (ver A32) |
| A15 | lattice 50 (M=2)/105 (M=3); \|pop\|≤N_RV | (1) | (1) | direta | teto nunca excedido **45/45**; `pop_final/N_RV` mediana **0,84** |
| A16 | orçamento interno **40.000** aval-surrogate | (1) | (1) | direta | `FE_antes ≤ 40000 < FE_final` **45/45**; `FE_antes` ∈ [39.917; 40.000] |
| A17 | overshoot ≤ 1 geração | (2) | (2) | direta | overshoot ∈ **[2; 87]**, mediana 24; **≤ \|prole\| em 45/45** |
| A18 | α=2 + rampa θ por FE/40.000 | (2) | (2) | decl. | `sigma_dict.rampa_theta` 45/45 |
| A19 | SBX η=30/p=1,0 + PM η=20/p=1/n | **T** | **T** | não-verif. (pareamento: indireta ✓) | prole = `par(\|pop\|)` fecha o invariante 45/45 |
| A20 | ② vazia · `real_solution_id` NULL | (2) | (2) | direta | ② **0 linhas 45/45**; `rsid` NaN em **100%** das 2.672.336 linhas |
| A21 | patch DI-16.16 ⇒ ⑦ reconstituível da ③ | (2) | (2) | direta | X da ⑦ ≡ X da última geração da ③ **bit-a-bit 45/45** |
| A22 | ⑦ = ND pós-real (DI-08) | (2) | (2) | direta | recomputo do ND na vista float32 ≡ `nd_pos_real` **45/45**; fantasia mediana **0,346** |
| A23 | sonda: 1 bloco de 20.000, `geracao` NULL, join posicional | (2) | (2) | direta | 45/45 com 1 bloco × 20.000; `geracao` NaN 100%; **max\|ΔX\| = 0,0 em float32** |
| A24 | `fe_treino_max` ≡ N−1 constante | (2) | (2) | direta | 1 valor único por célula **45/45**, = N−1 **45/45** |
| A25 | ⑥ DI-10: `f_best`/`n_front1` | (2) | (2) | direta | `f_best` exato (float32) **57.836/57.836 = 100%**; `n_front1` **356/360** na amostra (98,9%), Δ ∈ [−1,0] |
| A26 | semeadura D62/DI-28 + gancho pyDOE | (2) | (2) | direta | LHS inicial **idêntica** entre células do mesmo (M,D) — 8 grupos |
| A27 | ⑤ sem `params` | (2) | **(2) ✅ CORRIGIDO** | direta | s42: **0/45** têm `params`; **smoke T11: presente, 9 chaves** |
| A28 | Hyb fora do estudo (D56) | (2) | (2) | decl. | `modelo_flag='b5r/ProbRVEA-v3+GPR'` 45/45 |
| A29 | baseline de guardas/timing | (1) | (1) | direta | **0** eventos `guard` em 58.015 linhas; `fit+busca ≤ tempo_geracao_s` **45/45** |
| A30 | ③ geração 1 = pop inicial PRÉ-seleção | **(3) 🎯** | **(2) ✅ RESOLVIDO** | direta | `granularidade_③` no `sigma_dict` do smoke; e **prova executável nova** (§4) |
| A31 | determinismo / re-run bit-idêntico | **T** | **(1) ✅ SAIU DO TETO** | direta | s42 × smoke T11 de `BBOB_F22`: ①/③/⑦ **bit-idênticas** |
| **A32** | 🆕 `flag_vetores_degenerados` (I-05) | — | **(3) 🎯 NOVO** | direta + código | **null em 1144/1144** (b5r) e **801/801** (b5m) — caminho de atributo errado |
| **A33** | 🆕 `tempo_aval_real_s` no offline (I-02) | — | **(3) 🎯 NOVO** | direta + código | s42: **0,0 em 45/45** · smoke T11: **3e-4 s**, proporcional a N — mede a **carga do dataset** |
| **A34** | 🆕 `campanha_id` + `repo_hash` (proveniência) | — | **(2) ✅ NOVO** | direta | s42: `campanha_id` ausente 45/45, `repo_hash` **null 45/45**; smoke: ambos preenchidos |

### 2.2 Blocos narrativos

**A1 · Regime offline puro.** *(a)* O paper: "*there is no reevaluation of the true function during the search*"; o laço 5–12 da Alg. 1 roda só com previsões. *(b)* Nossa SPEC materializa com o `offline_guard` (`OfflineBudgetViolation`) + D90 (o dataset É o orçamento). *(c)* Re-medido: o campo `fe` dos **57.836** eventos `decision` é **constante e igual a `maxfe`** em 45/45 (ZDT1 `fe=929` nas 878 gerações; `swap_medium-lhs_DTLZ2` `fe=2000` nas 408); **zero eventos `guard`** em 58.015 linhas de ⑥; ② com 0 linhas e `real_solution_id` NULL em 2.672.336/2.672.336. *(d)* O `bud` nasce esgotado na carga e o motor recebe `use_surrogates=True`. *(e)* **(1) · direta.** ⚠ **Uma das cinco provas mudou de natureza sob a T11** — ver A33.

**A2 · O orçamento é o dataset.** *(a)* N_D=109 fixo (§IV-A11). *(b)* D90 troca por `N = 31D−1` (o que torna offline×online comparável) + D67 abre os tiers. *(c)* `len(①)==maxfe==fe_final` **45/45**: 61 (D=2) · 216 (D=7) · 309 (D=10) · 371 (D=12) · 619 (D=20) · 681 (D=22) · 929 (D=30) no main/small e **2.000** nas 10 medium; `fase=='init'` 100%; `fe_index` denso 45/45. *(e)* **(2) · direta** — e é **por isso que nenhum número absoluto nosso compara com o paper** (§5).

**A4 · Kriging 1×.** ④ com **1 linha em 45/45**, `n_acumulado==N` 45/45, `fit_series` 1 entrada. Custo re-medido: **0,0275 s @ N=61 → 566,64 s @ N=2.000** — a parede O(N³). Repartição do wall: **27,3% fit · 69,5% busca · 2,3% sonda**. **(1) · direta.**

**A5+A6 · O GPR concreto e o colapso ao prior.** *(a)* O paper só diz "*Scikit-learn … Kriging with Gaussian kernel and BFGS*" (§IV-A5). *(b)* O código oficial crava `C(1.0,(1e-3,1e3))*RBF(10,(1e-2,1e2))`, `alpha=0`, `n_restarts=9`, `normalize_y` ausente ⇒ **False**, kernel **isotrópico** para até D=30 — 🟠 impl→código, declarado no `sigma_dict` (e agora **também** no `params` do ⑤, A27). *(c)* A digital numérica fecha: o **σ máximo em toda a campanha é 31,62277603** = √1000 = teto exato do ConstantKernel. Censo re-medido nos **104 pares (célula,objetivo)** × 20.000 pontos: **4 pares** com σ cravado no teto ≥99,90% — `DTLZ3/f0` **99,97%**, `DTLZ3/f1` **100%**, `DTLZ3/f2` **100%**, `DTLZ1/f2` **99,90%**; **3 pares** com μ **constante** em 20.000 pontos (`DTLZ3/f1`, `DTLZ3/f2`, `DTLZ4/f2`). *(d)* `normalize_y=False` dá média a priori **zero** contra dados de média 445–687; com `alpha=0` e a multimodalidade do DTLZ3, a verossimilhança foge para o canto degenerado ⇒ **posterior = prior**. Em DTLZ3 o b5r otimiza uma função **constante** e a seleção vira ruído MC puro — confirmado pelo outro lado: razão σ(desc)/σ(mant) = **1,000000 exata** ali. *(e)* **(2) · direta — caveat científico central para o D97, não item de bug.**

**A7 · O σ exportado.** Extensão nossa 🟢 (D30/DI-16.9). `n_nan = 0` nas **104/104** medições ⇒ a `cobertura95` do `sonda_f52e.csv` é legítima para b5r (mediana **0,901**), sem o caveat N/A do c311. O extremo oposto é real: **σ = 0 exato** em **12 pares**, **7** deles em >50% dos pontos, máx **91,95%** (`ZDT4/f0`) — nos objetivos lineares o GP interpola e a variância cai abaixo do float32. É o limite σ→0 do próprio paper: a seleção probabilística **degenera na genérica** naquele objetivo. Isso explica cobertura 0,0001 com WAPE ~1e-5. **(2) · direta.**

**A9 · O coração: média-MC do APD (DI-28.1).** *(a)* O paper (Eq. 13–15) manda estimar a PDF do APD por **KDE** e ranquear por **P_wrong**. *(b)* O `Prob_APD_select_v3` faz `rank_apd = np.mean(apd, axis=2)` + `argmin` ("*superfast by considering mean APD*") — aproximação **não publicada**, ratificada pela **DI-28.1** como a variante do estudo. Declaração literal presente em 45/45 células. *(d)* P_wrong ordena por **sobreposição das distribuições**; a média-MC por **E[APD]**. Mas a média-MC **não é cega ao σ**: como o APD é `‖f_amostra‖·(1+pen·θ)` e a norma é convexa, Jensen dá E[‖f+εσ‖] > ‖μ‖ com excesso crescente em σ ⇒ há penalização de incerteza de **segunda ordem**, de mesmo sinal que o P_wrong. *(e)* **(2) · direta-declarativa.** Não se re-litiga.

**A11 · 🎯 O efeito declarado sobrevive — a query-joia, re-medida.** *(a)* A tese do paper (§III/Fig. 6): "*the probabilistic approaches reject solutions with better objective values if they have high uncertainties*". *(b)* Nossa variante não implementa P_wrong; a pergunta do D97 é se o efeito ainda existe. *(c)* Para cada geração g≥2 separei os pais de g−1 em **mantidos** (X bit-a-bit presente em g) e **descartados** e comparei o σ médio. Em **56.081 transições válidas**, **35.647 = 63,56%** têm σ(descartado) > σ(mantido) — contra 50% sob a hipótese nula de seleção σ-cega (**z ≈ 64**). Razão σ_desc/σ_mant **>1 em 39/45 células**, mediana **1,0429**, picos `swap_medium-mvns_ZDT1` **2,3835**, `MMF1` **2,2287**, `ZDT1` **1,9425**, `MMF11_L` **1,7487**, `DTLZ7` **1,2882**. As 6 exceções são exatamente as da F5: **DTLZ3 1,000000** (surrogate degenerado, A6), `WFG1` 0,9819, `BBOB_F49` 0,9848, `BBOB_F37` 0,9968 e `MMF16_20` 0,9967 (×2 com a réplica). Confirmação independente: a **deriva do σ da população** (últimos 10% / primeiros 10%) é **< 1 em 44/45 células**, mediana **0,4868**, mínimo **0,1421** — a única exceção é DTLZ3 (1,000). *(d)* É Jensen operando dentro do `np.mean(apd, axis=2)`. *(e)* **(1) · direta** — o comportamento prescrito é **medido**, por rota funcional distinta. (A F5 mediu 62,8% com agregação de σ ligeiramente diferente; **re-medi 63,56%** — mesma conclusão, z inalterado.)

**A13 · Pop inicial = LHS novo.** *(a)* Alg. 1 l. 2: "*Use the given data as the initial population*". *(b)* `init_pop` está **comentado em todos os modes**; `Population.__init__` chama `create_new_individuals("LHSDesign")` ⇒ **B18.9 NÃO** — e a **DI-28.3** injeta o `RandomState` global semeado no `lhs` do pyDOE 0.9.1 (que senão cria um `default_rng()` fresco e quebra a reprodutibilidade). *(c)* Re-medido **com os bounds REAIS do problema** (`H._bounds`), não com proxy: a geração 1 é LHS-perfeita (1 ponto por estrato 1/n) em **727/727 dimensões, 45/45 células**, **0 pontos fora dos bounds**, zero colisões de estrato; a geração 2 cai para **9/727** — o que confirma, por contraste, que só a geração 1 é o desenho. E a interseção X entre a busca inteira (1.772.336 linhas) e o dataset é **exatamente 0 em 45/45**. *(e)* **(2) · direta.**

**A16 · Os 40.000 aval-surrogate, fechados por reconstrução.** O contador interno não é logado; reconstruí `FE = N_RV + Σ_g par(|P_{g−1}|)` com `par(n)=n+(n mod 2)` (o SBX empareilha consecutivos e duplica o primeiro se ímpar). O invariante de terminação `FE_antes ≤ 40000 < FE_final` **fecha em 45/45**, com `FE_antes` ∈ **[39.917; 40.000]** e `FE_final` ∈ **[40.002; 40.087]** — `ZDT1`, `ZDT4`, `swap_small-lhs_ZDT1` e `swap_small-lhs_ZDT4` batem `FE_antes` **exatamente 40.000**. Subproduto: valida **indiretamente** a estrutura de pareamento do SBX (A19). **(1) · direta.**

**A17 · Overshoot.** Medido `FE_final − 40.000` ∈ **[2; 87]** (mediana 24) e **≤ |prole da última geração| em 45/45**. **(2) · direta.**

**A21+A22 · O patch DI-16.16 e a ⑦.** Sem o patch, o archive do mode 7 grava a **prole pré-seleção** e a ⑦ nasce irreconstituível da ③ (o 🔴 do R3-00). Verificado: X da ⑦ ≡ X da última geração da ③ **bit-a-bit (float32) em 45/45**. E o ND recomputado **na vista float32** (regra 11 do CONTRATO) é **idêntico a `nd_pos_real` em 45/45**. Razão de fantasia (`nd_pos_real/n_final`) mediana **0,346**, mín **0,043**, máx **0,900**. **(2) · direta.**

**A23 · A sonda.** 45/45 com exatamente **1 bloco**, `S=20.000`, 20.000 linhas `regime='sonda'`, `geracao` NaN em 100%. **Join posicional** contra `data/sonda/sonda_{prob}.parquet`: **max|ΔX| = 0,0 em float32** (o resíduo de 1,9e-06 que aparece contra o gabarito float64 é a quantização do float32 — regra 11). ⚠ **Regra 12 é N/A neste config**: os regimes de b5r são apenas `offline|sonda` em 45/45 — **não existe bloco `sonda_estratificada`** (b5r não é classificador). O único bloco é a régua Sobol, comparável entre configs. **(2) · direta.**

**A25 · O ⑥.** Chaves observadas nos 57.836 `decision` da s42: exatamente `{ts, rec, caminho, motivo, geracao, n_ds_membros, fe, f_best, n_front1}` + `tempo_fit_s` só em g=1. `f_best` ≡ mínimo por objetivo da geração, **exato em float32 nas 57.836 (100%)**. `n_front1`: re-medido por amostra de **360 gerações** (8 por célula, semente 7) → **356/360 = 98,89%** exatos, Δ ∈ **[−1, 0]**, |Δ| médio 0,011 (a F5 mediu o censo completo: 97,43%). O resíduo é a assimetria float64(⑥)×float32(③) — a mesma que levou o `write_final` a calcular `nd_pos_real` na vista float32, e a **regra 11 da T11** hoje nomeia. **(2) · direta.**

**A27 · ⑤ sem `params` — CORRIGIDO.** *(c)* s42: **0/45** manifestos com a chave (é a não-conformidade F5.2b que atingia 197 células em 7 configs, e o `contrato_f52b.csv` traz 45 linhas iguais `camada 5 · CHAVES · faltam ['params']`). **Smoke T11: `params` presente com 9 chaves** — `alg, mode, motor, surrogate, treino, n_dataset, regime, q, patches_vendorizados` — e o `patches_vendorizados` carimba `["b5-mode72-kde","b5-mode7-archive","b5-pwrong-stats"]`, levando o elo D80 para dentro do próprio manifesto. Evidência: `src/b5_prob.py:233-245` (código) + manifesto do smoke (dado). **(2) ✅ · direta.**

**A29 · Guardas e tempo.** **0 eventos `guard`** em 58.015 linhas; `cache_hits=0`; `fallback_ativado=False`, `n_retries=0` em 45/45; `tempo_fit_s + tempo_busca_s ≤ tempo_geracao_s` em **45/45** e `tempo_pred_sonda_s > 0` separado (a sonda roda **fora** do laço, sem a exceção DI-13.10 dos configs online). **(1) · direta.**

**A30 · 🎯→✅ A geração 1 da ③ é a POPULAÇÃO INICIAL — RESOLVIDO.** Era o **único aspecto (3)** da F5. *(b)* A T11 (**I-04**, commit `08a4019`) inseriu no `sigma_dict` a chave `granularidade_③`: *"ger 1 = pop INICIAL (LHS, PRÉ-seleção); 2..n = PÓS-seleção; passos de seleção = n_geracoes−1; FE conta init+pop"* + o controle negativo declarado (`treed_media`, que engancha em `_next_gen`, não tem o fenômeno). *(c)* **Medido nos dois lados**: o `sigma_dict` do smoke tem **19 chaves** (contra **18 em 45/45 da s42**) e a nova é exatamente essa; e as 3 provas da F5 continuam de pé re-medidas — `|pop| ger 1 == N_RV` **45/45**, LHS-perfeito **727/727 dims** na ger 1 contra **9/727** na ger 2, e o invariante de 40k fecha **45/45** só sob essa leitura. **🆕 Prova nova, executável (a que faltava):** construí o `ProbRVEA_v3` em `env_b5` e, **antes de qualquer `iterate()`**, o `individuals_archive` já contém a chave `'1'` com **|pop| = N_RV = 50** (`probe_vetores.log`, item 5). O fenômeno é do `Population.__init__`, e o patch DI-16.16 re-carimba `str(gen_count−1)` — que já vale ≥2 na 1ª `_next_gen`. *(e)* **Reclassificado (3) → (2) · direta.** A correção é exatamente a que a F5 recomendou, e ela **funciona de fato** (o campo existe **e** o texto está certo).

**A31 · ✅ Determinismo — saiu do teto.** Era **T** na F5 ("exige re-run"). O re-run existe: o smoke T11 de `BBOB_F22/42` (HEAD `9ad0138`, 2026-07-31) reproduz a célula da s42 (código anterior) com **①, ③ (59.436×29) e ⑦ bit-idênticas**, `n_geracoes=1144` nos dois. Caveat honesto: **1 célula, 1 semente, mesma máquina** — prova o determinismo do wrapper (gancho pyDOE, DI-28.3) e a não-perturbação da instrumentação; **não** prova bit-identidade cross-máquina. **(1) · direta (1/45 células).**

**A32 · 🎯 NOVO — `flag_vetores_degenerados` é sentinela em 100% dos eventos (o padrão do c217).** *(b)* A T11 (**I-05**) acrescentou 3 campos DI-10 ao `log.decision` do b5 (`src/b5_prob.py:534-536`): `p_wrong_stats`, `n_substituicoes` e `flag_vetores_degenerados`. O terceiro é declarado como *"a CAUSA a montante do PBI NaN (A8)"*, e a **ERRATA 13** (commit `65ace70`) ainda lhe acrescentou `amplitude = norma_max − norma_min` argumentando que ela discrimina o **congelamento parcial**. *(c)* **Medido no smoke T11 do b5r: `flag_vetores_degenerados` = `null` em 1144/1144 eventos `decision`.** E no **controle b5m** (mesma campanha, `MMF1/0`): `p_wrong_stats` e `n_substituicoes` **preenchidos em 800/801** — a instrumentação funciona — mas **`flag_vetores_degenerados` = `null` em 801/801**. *(d)* **Causa provada, não inferida.** `src/b5_prob.py:118` lê `evolver.population.problem.reference_vectors.values`; os vetores de referência moram no **evolver** (`BaseEA.py:182: self.reference_vectors = ReferenceVectors(...)`) e `desdeo_problem/` tem **ZERO ocorrências** do nome. Rodei a prova em `env_b5` (`probe_vetores_degenerados.py`): `_vetores_degenerados(evolver)` → **`None`**; a exceção que o `except Exception` engole é **`AttributeError: 'DataProblem' object has no attribute 'reference_vectors'`**; pelo caminho correto (`evolver.reference_vectors`) o dado existe e é sadio — **50 vetores, norma_min = norma_max = 1,000000000000, amplitude 1,11e-16, n_norma_zero = 0**. *(e)* **Classe (3) 🎯 · direta (dado) + código (arquivo:linha).** Três consequências: (i) o campo é o retrato exato do padrão que o prompt mandou caçar — **presente e sentinela**; (ii) a ERRATA 13 adicionou a `amplitude` **dentro do ramo morto**, logo o "conserto" não conserta nada; (iii) a afirmação do handoff de que *"a cadeia A8 já é observável nas DUAS pontas — CAUSA em `flag_vetores_degenerados`"* é **falsa, medida**: a ponta do EFEITO (`p_wrong_stats`/`n_substituicoes`) funciona no b5m; a ponta da CAUSA **não existe em nenhum config**. Correção: **um token** (`evolver.population.problem.reference_vectors` → `evolver.reference_vectors`) + trocar o `except Exception: return None` por um que **logue** a exceção. **Impacto no mecanismo: ZERO** (é campo read-only; a ③ é bit-idêntica à da s42).
*Nota de escopo para o b5r:* mesmo corrigido, este campo **não** tiraria A14 (RVs FIXOS) do teto — `ReferenceVectors.adapt` faz `values = initial_values*(max−min)` seguido de `normalize()`, logo as normas voltam a 1,0 adaptando ou não. Só um `hash(reference_vectors.values)` por iteração discriminaria fixo × adaptado.

**A33 · 🎯 NOVO — `tempo_aval_real_s` no offline: o I-02 mudou a semântica e contradiz a própria justificativa.** *(b)* A T11 (**I-02**, commit `83dbdac`) pôs o cronômetro no portão único de avaliação (`src/budget.py:241`), e a docstring da property (`budget.py:192-202`) justifica o `None` assim: *"No offline o orçamento nasce ESGOTADO (a ① é o dataset, D90) e nenhuma avaliação real acontece no run — gravar 0.0 ali afirmaria que avaliar custou zero."* *(c)* **Medido**: na s42 o campo é **0,0 exato em 45/45**. No smoke T11 do b5r ele é **0,0003 s** — **nem None, nem 0**. E o padrão é sistemático nos 5 offline Python da campanha: b5r/`BBOB_F22` (N=309) **0,0003** · c311/`BBOB_F17` (N=309) **0,0003** · b5m/`MMF1` (N=61) **0,0001** · moead_media/`MMF1` (N=61) **0,0001** — **proporcional a N**, que é a digital da carga do dataset. *(d)* `standalone_harness.load_offline_budget:648-653` passa as **n linhas do dataset** por `bud.evaluate(X[i], lambda _x,_f=F[i]: _f)`; o cronômetro novo mede exatamente esses n retornos de lambda. Ou seja: **o caso que a docstring usa para justificar o `None` é justamente o caso em que ela não devolve `None`**, e o valor gravado não é "custo de avaliação real" — é overhead de ingestão. *(e)* **Classe (3) 🎯 · direta (dado, 4 configs) + código (arquivo:linha).** **Impacto no mecanismo: ZERO** — mas custa uma prova: a F5 usava `tempo_aval_real_s == 0,0 em 45/45` como uma das cinco provas de A1 (offline puro). Sob a T11 essa prova **deixa de discriminar** e A1 passa a apoiar-se nas outras quatro (`fe`≡`maxfe` em 57.836 eventos, 0 `guard`, ② vazia, `real_solution_id` 100% NULL) — que sozinhas já bastam. Correção sugerida: excluir do cronômetro o caminho de ingestão offline (ou marcar `fase='init'` no acumulador), para o campo voltar a significar o que promete.

**A34 · ✅ NOVO — proveniência: `campanha_id` e `repo_hash`.** *(c)* Na s42, `campanha_id` está **ausente em 45/45** e — achado novo — `repo_hash` **existe mas é `null` em 45/45** (mais um "campo presente, dado sentinela", este **fechado** pela T11). No smoke: `campanha_id='9ad0138aa9a4_2026-07-31'` e `repo_hash='9ad0138aa9a464a7d9f89d247f81092f8c4ef26f'`. *(d)* Efeito prático para a auditoria: com `params` + `repo_hash` + `patches_vendorizados` no manifesto, o elo **run → árvore de código que rodou** deixa de depender do `repos.lock` externo. *(e)* **(2) · direta.**

*(Blocos A3, A10, A12, A14, A15, A18, A19, A20, A24, A26, A28 sem mudança material em relação à F5 — números re-medidos e idênticos, resumidos na tabela §2.1.)*

---

## 3. Percentuais por classe

**Total de aspectos enumerados = 34. Balde T (fora do denominador) = 4** → **DENOMINADOR = 30.**

| classe | contagem | % (den. **30**) | aspectos |
|---|---:|---:|---|
| **(1) conforme o artigo** | **8/30** | **26,7%** | A1, A3, A4, A11, A15, A16, A29, **A31** |
| **(2) desvio sancionado** | **20/30** | **66,7%** | A2, A5, A6, A7, A9, A10, A13, A17, A18, A20, A21, A22, A23, A24, A25, A26, **A27**, A28, **A30**, **A34** |
| **(3) desvio inexplicado 🎯** | **2/30** | **6,7%** | **A32** (`flag_vetores_degenerados` sentinela) · **A33** (`tempo_aval_real_s` offline) |
| **T (à parte)** | **4** | — | A8 (S/truncnorm) · A12 (identidade do argmin) · A14 (RVs fixos) · A19 (índices SBX/PM) |

**F5 → T11**: denominador 26→30 · (1) 26,9%→26,7% · (2) 69,2%→66,7% · (3) 3,8%→**6,7%** · T 5→**4**.
**Leitura**: os dois (3) novos são **instrumentação read-only**, não mecanismo — e a bit-identidade ③ s42×smoke prova que **nenhum deles toca a busca**. O único (3) de mecanismo-adjacente da F5 (A30) foi **fechado**.
*Marca declarativa (Botão 3)*: 5 dos 20 aspectos (2) são `direta-declarativa` — A5 (com digital numérica independente), A9, A10, A18, A28. Elo de código coberto por `anchors.json` (`b5-mode7-archive`) + `repos.lock` + agora `params.patches_vendorizados` no ⑤.

---

## 4. 🆕 AS CORREÇÕES DA T11 — implementada? funciona de fato?

| # | correção | tocou b5r? | implementada? | **funciona de fato?** | evidência |
|---|---|---|---|---|---|
| **I-04** `granularidade_③` | a recomendação da F5 (A30) | **SIM** | ✅ `src/b5_prob.py:270-285` | ✅ **SIM** — chave presente no smoke, texto **correto** e verificável, com controle negativo nomeado | **(iii) dado**: `sigma_dict` do smoke tem 19 chaves × 18 na s42 (45/45) · **(i) código** `b5_prob.py:281` · **prova nova (i+dado)**: archive já tem `'1'` com \|pop\|=50 antes do 1º `iterate()` |
| **I-07** `params` no ⑤ | A27 (contrato) | **SIM** | ✅ `src/b5_prob.py:233-245` | ✅ **SIM** — 9 chaves, inclusive `patches_vendorizados` | **(iii) dado**: smoke tem `params`; s42 **0/45** · fecha as 45 linhas de `contrato_f52b.csv` |
| **I-09** `repo_hash` no ⑤ | proveniência | **SIM** | ✅ | ✅ **SIM** — s42 tinha o campo **null 45/45**; smoke traz o SHA | **(iii) dado** |
| **G-3** `campanha_id` | proveniência | **SIM** | ✅ | ✅ **SIM** | **(iii) dado** |
| **I-05** `p_wrong_stats` / `n_substituicoes` | b5m, **não** b5r | SIM (o campo é emitido) | ✅ `b5_prob.py:534-535` | ⚪ **null 1144/1144 no b5r — CORRETO por desenho** (mode 7 não passa pelo `ProbMOEAD_select`; **ERRATA 12** já corrigiu o gate invertido). **Controle b5m: 800/801 preenchidos ✅** | **(iii) dado** nos dois configs |
| **I-05** `flag_vetores_degenerados` | **SIM** | ✅ emitido | 🔴 **NÃO FUNCIONA — null em 1144/1144 (b5r) e 801/801 (b5m)**. Caminho de atributo errado; `except Exception` engole o `AttributeError` | **(iii) dado** + **(i) código** `b5_prob.py:118` + **prova executada** em `env_b5` |
| **ERRATA 13** `amplitude` explícita | **SIM** | ✅ `b5_prob.py:129` | 🔴 **INERTE** — foi adicionada **dentro do ramo morto** acima; nunca chega ao ⑥ | **(i) código** + **(iii) dado** |
| **I-02** cronômetro no portão | **SIM** | ✅ `budget.py:241` | ⚠ **funciona, mas com efeito colateral não declarado no offline**: mede a ingestão do dataset (3e-4 s ∝ N), não avaliação real; contradiz a própria docstring (`budget.py:196-198`) | **(iii) dado** em 4 configs offline + **(i) código** `standalone_harness.py:648-653` |
| **§3.1** não-perturbação da sonda | **SIM** | ✅ | ✅ **SIM, e mais forte que o par g6**: célula inteira bit-idêntica pré×pós-T11 | **(iii) dado** |
| **wrapper do gatilho do `adapt`** | b5m (A8) | **NÃO IMPLEMENTADO — e agora declarado** (commit `65ace70`) | — | honesto; mas a justificativa ("a causa já é observável em `flag_vetores_degenerados`") **é falsa** — ver A32 | **(ii) veredito registrado** + **(iii) dado refuta** |

**Placar do b5r: 5 correções que funcionam · 1 que não funciona (A32) · 1 com efeito colateral (A33) · 1 declarada como não-feita cuja justificativa cai.**

**Números do handoff que RE-MEDI e confirmo:** LHS ger 2 = **9/727** (bate exato) · `|pop| ger1 == N_RV` **45/45** · contabilidade de 40k fecha **45/45** só na leitura "chave 1 = init" · `real_solution_id` 100% nula no b5r (o handoff diz "0/57.997"; **eu meço 0/2.672.336 linhas de ③, das quais 1.772.336 de busca** — o 57.997 do handoff é contagem de **gerações**, não de linhas; a conclusão é a mesma, o número está rotulado errado).
**Número do handoff que NÃO se sustenta:** §5 marca o b5r com **"§3.1 (par G-6) ✅ `2d217703d7086d0f`"**, mas **o b5r não está em `g6_com/g6_sem`** (só os 9 MATLAB estão preservados). O veredito é (ii) registrado, não auditável nesses diretórios — mas eu o **substituí por evidência melhor**: a bit-identidade s42×smoke de célula inteira.

---

## 5. Comparação canônica (Entrega 2)

**Setup do paper**: DBMOPP P1/P2, n=10, K=2–10, **N_D=109**, FEmax 40.000 aval-surrogate, LHS e MVNS, 31 execuções, HV + RMSE, Wilcoxon+Bonferroni. DTLZ só no suplementar, sem tabela numérica no texto.

| interseção | veredito | evidência |
|---|---|---|
| DBMOPP P1–P4 (o corpo do paper) | **incomensurável (eixo X)** — interseção **vazia** | nenhum DBMOPP no grid dos 25 |
| DTLZ1/2/3/4/7 | **incomensurável** | n 7/12/22 ≠ 10 · K só 3 (paper 2–10) · N_D 216–2.000 ≠ 109 · métrica primária nossa = IGD+ normalizado (D69/D70) × HV+RMSE do paper · **o paper não publica número de DTLZ no texto** |
| ZDT · WFG · MMF · BBOB (20 problemas) | **incomensuráveis por inexistência no paper** | — |
| **eixo COMPARÁVEL (único)**: orçamento interno | **IGUAL** | `FEmax = 40.000`, idêntico ao §IV-A4 — **fechado por dado em 45/45** (A16) |

**Âncoras direcionais (endpoint = IGD+ da ⑦; 1 semente ⇒ SENTIDO, nunca magnitude; Wilcoxon pareado nas 40 células distintas):**

| # | afirmação do paper | teste | veredito |
|---|---|---|---|
| **J1** | "*the probabilistic approaches outperformed their generic counterparts*" | **b5r × `moead_media`** (= mode 12, o **Gen-MOEA/D do próprio paper**): **31–14** nas 45 · **27–13, p=0,0025** nas 40 | **SENTIDO CONFIRMADO** (caveat: motor distinto) |
| **J1b** | idem, ablação de mesmo motor | b5m × moead_media | **não conclusivo em 1 semente** → F5.5 |
| **J2** | "*Prob-RVEA … followed by Prob-MOEA/D*" | **b5r × b5m**: 27–18 nas 45 · **25–15, p=0,0250** nas 40 | **SENTIDO CONFIRMADO** |
| **J3** | assinatura da Fig. 10 (HV-surrogate cai, HV real sobe) | 1.125 checkpoints com re-avaliação real (F5) | **PARCIAL** — confirmada do lado surrogate (IGD+ do surrogate piora em 33/45 na 2ª metade), **não** do lado real na maioria; o surrogate é **otimista em 81,5%** dos checkpoints |
| **J5** | custo O(N³) do Kriging | `t_fit` **0,0275 s @ N=61 → 566,64 s @ N=2.000**; log-log inclinação **2,74** | **CONFIRMADO** |
| **J6** | LHS × MVNS | WAPE mediana small-lhs 0,076 × small-mvns 0,196; medium-lhs 0,033 × medium-mvns 0,061 | **MVNS pior na régua**, consistente |

**Posição no endpoint (re-medida em `b5r_C_pares7.csv`, 45 células comuns aos 5 offline):** rank médio IGD+ da ⑦ — **e103 2,000 · b5r 2,889 · c311 3,022 · b5m 3,267 · moead_media 3,822**; vitórias 27/11/3/3/1; fantasia média do b5r **0,408**. Head-to-head nas 40 distintas: **b5r > moead_media 27–13 (p=0,0025)** · **b5r > b5m 25–15 (p=0,0250)** · b5r ≈ c311 22–18 (p=0,19) · **b5r < e103 11–29 (p=0,0090)**.

> **NUNCA "artigo melhor"**: sob interseção vazia (DBMOPP) e orçamentos/métricas/dimensões distintos (DTLZ), o veredito é **incomensurável (Botão 4)** + as âncoras J acima.

---

## 6. Saúde (s42 = corpus principal)

**Contrato.** `integridade_f52a.csv` filtrado a b5r: **ZERO linhas**. `contrato_f52b.csv`: 45 linhas, todas `camada 5 · CHAVES · faltam ['params']` — **corrigido pela T11** (A27). Anomalia de escrita nova da F5 **confirmada e ainda presente na s42**: `swap_small-mvns_ZDT4` tem **1 footer, não 2** (falta o do despachante; o do runner está completo e o ⑤ está íntegro) — 44/45 com 2. Por-desenho, todos com regra citada: ② vazia (DI-16.17), `real_solution_id` NULL (idem), `geracao` NULL na sonda (DI-13.5), `modelo_hp`/`dist_min_arquivo` ausentes (D-08), `n_front1` com 1,1% de resíduo float64×float32 (regra 11).

**Sonda — a régua Sobol (o ÚNICO bloco; regra 12 é N/A: b5r não tem `sonda_estratificada`).** 104 medições, `n_nan = 0` em todas, `n_validas = 20.000` em todas, 1 bloco (`blk0`). WAPE mediana por família nas 104: **ZDT 0,0129 · BBOB 0,0752 · DTLZ 0,0915 · MMF 0,1553 · WFG 0,2752**. Cobertura ±1,96σ mediana **0,901**, com caudas patológicas nos dois sentidos (mín 0,0001 por σ subestimado, máx 1,0000 por σ largo) e **3 `corr` NaN** — todas em DTLZ3, onde μ é constante. Curva "o surrogate aprendeu?" é **N/A por desenho** (treino único, A4/A24).

**Trajetórias.** 0 violações de monotonicidade de IGD+ em 855 transições — mas **no offline a trajetória percorre a acumulação do dataset**, monotônica por construção: é sanidade de métrica, não convergência.

**Comportamento.** População final mediana **0,84·N_RV**, sem colapso (exceções DTLZ4=14, ZDT4-sweep 8–15, BBOB_F17=29 — todas multimodais/deceptivas). "Seguro-mas-mediano": 2º de 5 offline, ganha do piso do próprio paper, perde do e103.

**Métricas oficiais (D69) são INDISCRIMINANTES no offline** — spread de `igd_plus`/`hv`/`n_nd` **exatamente 0,0** entre os 5 configs offline nas 45 células (leem a ①=dataset compartilhado). O endpoint discriminante é a ⑦.

---

## 7. SCORE, recomendação e VEREDITO vs F5

### **SCORE: 9,0/10** · **RECOMENDAÇÃO: ACEITAR + CAVEAT** (caveats **científicos**, não de fidelidade) · **VEREDITO: MANTEVE**

**Por que MANTEVE, com a causa nomeada — e por que isso é o resultado certo.**

1. **O mecanismo não mudou — e isso não é inferência, é bit-identidade.** ①, ③ (59.436 linhas × 29 colunas) e ⑦ da célula `BBOB_F22/42` são idênticas entre a s42 (pré-T11) e o smoke T11. A campanha acrescentou **só instrumentação read-only** no b5r. Toda a fidelidade de mecanismo é a mesma, re-medida com os mesmos números: 63,56% de rejeição-por-σ em 56.081 transições (z≈64), 727/727 dimensões LHS, 45/45 no invariante de 40k, ⑦≡③ bit-a-bit 45/45, ND recomputado 45/45.
2. **O que PUXOU PARA CIMA (+):** o único (3) da F5 (**A30**) foi **corrigido exatamente como recomendei** e a correção **funciona** — `granularidade_③` no `sigma_dict`, texto correto, controle negativo declarado; ganhei ainda uma **prova executável** que a F5 não tinha. O contrato fechou (**A27**, `params`). **A31 saiu do teto T** (determinismo agora é dado). Proveniência ficou auditável dentro do manifesto (**A34**). Sozinhos, esses quatro itens justificariam **9,5**.
3. **O que PUXOU PARA BAIXO (−):** dois (3) NOVOS, ambos achados por medição e ambos do tipo que o prompt mandou caçar. **A32** é o padrão do c217 na forma pura — `flag_vetores_degenerados` presente em 1144/1144 eventos e **sentinela em 1144/1144**, por caminho de atributo errado, com o `except Exception` mudo; e a ERRATA 13 "consertou" a `amplitude` **dentro do ramo morto**. **A33** é uma regressão semântica silenciosa: `tempo_aval_real_s` deixou de ser 0/None no offline e passou a medir a ingestão do dataset, contradizendo a docstring que justifica o próprio campo — e custando uma das cinco provas de A1.
4. **O saldo é zero, e o score fica em 9,0.** Pela régua: 9 = "tudo (1)/(2), com (3) menores já investigados e provados benignos". É exatamente o caso — os dois (3) são **instrumentação read-only**, com **causa provada** (arquivo:linha + exceção capturada em execução), **efeito nulo sobre a busca** (provado pela bit-identidade) e conserto de **um token** cada. Não sobem para 9,5 porque um deles **desmente uma afirmação central do handoff T11** e o outro degradou uma prova de fidelidade que a F5 usava; não descem para 8 porque nenhum toca mecanismo, contrato de dados ou métrica.
5. **O caveat científico que rebaixa de 10 é o mesmo, e continua sendo o item mais importante para o D97**: o GPR do código oficial (`normalize_y=False`, ConstantKernel ≤1e3, α=0) **colapsa ao prior** em DTLZ3 (3/3 objetivos), DTLZ1/f2 e DTLZ4/f2 — ali o b5r otimiza uma função constante e a seleção é ruído MC puro. Isso vai para o **texto da dissertação**, não para a lista de bugs.

---

## 8. Aspectos classe (3) 🎯 — evidência completa

### A32 — `flag_vetores_degenerados`: campo presente, dado sentinela em 100% dos eventos

**Declarado.** `src/b5_prob.py:110-136`, docstring: *"[I-05 item 3] `flag_vetores_degenerados`: a norma dos vetores de referência colapsou a zero? É a CAUSA a montante do PBI NaN (A8)."* Commit `65ace70` (ERRATA 13) reforça: *"a cadeia A8 já é observável nas DUAS pontas — CAUSA em `flag_vetores_degenerados` (norma colapsando) e EFEITO em `p_wrong_stats` (max≡0,0) + `n_substituicoes`≡0"*, e por isso o autor **decidiu não implementar** o wrapper do `adapt` (~90 min de b5m).

**Medido (dado).**
- b5r, smoke T11 `off/b5r/BBOB_F22/42`: `flag_vetores_degenerados` **null em 1.144/1.144** eventos `decision`.
- b5m, smoke T11 `off/b5m/MMF1/0` (o controle onde a cadeia A8 vive): `p_wrong_stats` **preenchido em 800/801** e `n_substituicoes` **preenchido em 800/801** (a instrumentação I-05 funciona), mas `flag_vetores_degenerados` **null em 801/801**.

**Causa (código + execução).** `src/b5_prob.py:118` lê

```python
V = evolver.population.problem.reference_vectors.values
```

Os vetores de referência são atributo do **evolver** — `desdeo_emo/EAs/BaseEA.py:182`: `self.reference_vectors = ReferenceVectors(lattice_resolution, problem.n_of_objectives)` — e `grep -rn "reference_vectors" desdeo_problem/` retorna **zero linhas**. A prova executada em `env_b5` (`probe_vetores_degenerados.py`, log anexo):

```
_vetores_degenerados(evolver) = None
AttributeError: 'DataProblem' object has no attribute 'reference_vectors'
caminho CORRETO: n_vetores=50  norma_min=1.000000000000  norma_max=1.000000000000
                 amplitude=1.110e-16  n_norma_zero=0
hasattr(problem,'reference_vectors') = False | hasattr(evolver,'reference_vectors') = True
```

**Efeito.** (i) A ponta da CAUSA da cadeia A8 **não existe em dado nenhum** — a justificativa para não fazer o wrapper do `adapt` cai; (ii) a `amplitude` da ERRATA 13 foi acrescentada **dentro do ramo morto**; (iii) para o b5r, o campo que poderia ter dado eco à assimetria RVEA×MOEA/D não dá nada. **Zero efeito sobre a busca** (③ bit-idêntica). **Conserto**: `evolver.population.problem.reference_vectors` → `evolver.reference_vectors`, e `except Exception` → `except Exception as e: ... {"erro": repr(e)}` (um gate que nunca reprova é decorativo — lição 4.2.1 da própria T11).

### A33 — `tempo_aval_real_s` no offline mede a ingestão do dataset, não avaliação real

**Declarado.** `src/budget.py:192-202`: *"`None` … 'não medi' ≠ 'custou zero'. No offline o orçamento nasce ESGOTADO (a ① é o dataset, D90) e nenhuma avaliação real acontece no run — gravar 0.0 ali afirmaria que avaliar custou zero."*

**Medido.** s42 (pré-T11): **0,0 exato em 45/45**. Smoke T11: b5r/`BBOB_F22` (N=309) = **0,0003** · c311/`BBOB_F17` (N=309) = **0,0003** · b5m/`MMF1` (N=61) = **0,0001** · moead_media/`MMF1` (N=61) = **0,0001**. Nunca `None`; **proporcional a N**.

**Causa.** `src/standalone_harness.py:648-653` — `load_offline_budget` empurra as n linhas do dataset por `bud.evaluate(X[i], lambda _x, _f=F[i]: _f)`; o cronômetro de I-02 (`budget.py:241`) cronometra esses n retornos. `_n_avals_cronometradas = n > 0` ⇒ a property nunca devolve `None` no offline.

**Efeito.** Nenhum sobre a busca. Sobre a auditoria: A1 perde uma das cinco provas (as outras quatro bastam). Para a R4, o campo **não pode** ser lido como "custo de avaliação real" nos 5 configs offline. **Conserto**: não cronometrar o caminho de ingestão (`fase='init'` no acumulador) — 1 linha.

---

## 9. Teto de verificabilidade (T) e armadilhas

**T — 4 itens (era 5; A31 saiu):**
- **A8 — S=1000 / `truncnorm(−3,3)`**: amostras MC descartadas por desenho (L.16). *Sairia do teto* com um contador de amostras por geração no ⑥ (custo zero).
- **A12 — identidade do `argmin` da média-MC**: bloqueada pelo próprio patch DI-16.16 (a prole pré-seleção é sobrescrita). *Sairia do teto* com o **duplo carimbo** (`str(g)` prole + `str(g)_sel` sobreviventes) — e aí o b5r ganharia a query-joia fechada que b1 (EI, 891/891) e e81 (maximin) têm. **Recomendação mantida da F5, ainda não implementada.**
- **A14 — RVs FIXOS (`adapt()` comentado)**: **o item mais caro do teto**, porque contradiz um parâmetro **explícito** do setup do paper (§IV-A8) e cria assimetria com os modes 12/72. ⚠ **A instrumentação nova NÃO o resolve**, nem se A32 for consertada: `ReferenceVectors.adapt` re-normaliza, então as normas ficam em 1,0 nos dois regimes (medido: `norma_min=norma_max=1,000000000000`). *Sairia do teto* só com `hash(reference_vectors.values)` por iteração.
- **A19 — índices η do SBX/PM**: declarativos (a estrutura de pareamento já está provada indiretamente pelo invariante de 40k).

**O que ESTE corpus NÃO permite verificar:** (i) qualquer coisa que exija as 1000 amostras MC ou a prole pré-seleção; (ii) se os RVs foram adaptados; (iii) determinismo **cross-máquina** (só provei mesma máquina, 1 célula); (iv) variância entre sementes — 1 semente ⇒ **sentido**, nunca magnitude, em toda a §5; (v) qualquer comparação numérica com o paper (interseção vazia).

**Armadilhas confirmadas em escala (7 — as 6 da F5 + 1 nova):**
1. **`③.geracao == 1` NÃO é geração de seleção** — é a pop inicial LHS. Toda contagem de gerações do b5r usa `n_geracoes − 1` (**agora declarado no `sigma_dict`**: `granularidade_③`).
2. **As 5 células `swap_small-lhs_*` são réplicas bit-a-bit das `off`** (D90: small/lhs reusa o dataset principal). N efetivo = **40**, não 45. Contá-las como independentes infla o sweep em 12,5%.
3. **σ = 31,622776 não é "σ grande": é o TETO √1e3** do ConstantKernel — GP colapsado ao prior (DTLZ3 inteiro, DTLZ1/f2). Ali μ é constante, `corr` sai NaN e a seleção é ruído MC puro.
4. **σ = 0 exato em até 91,95% dos pontos** (objetivos lineares: ZDT4/f0, ZDT1/f0, …). Não é bug: é o GP interpolando. Cobertura baixa **com WAPE 1e-5** = intervalo nulo, não modelo ruim.
5. **Para a semente 42, todas as células do mesmo (M,D) partem do MESMO LHS inicial** (8 grupos). Bom para o contraste small→medium; ruim para tratar as células como independentes nesse fator.
6. **As métricas oficiais F5.2c EMPATAM exatamente entre os 5 offline** (spread 0,0 em 45/45 — D69 lê a ①=dataset). Ranquear offline exige a ⑦.
7. 🆕 **`tempo_aval_real_s` ≠ 0 no offline pós-T11 não significa avaliação real** — é a ingestão do dataset (A33). E **`flag_vetores_degenerados` = null não significa "vetores sadios"**: significa que a sonda não roda (A32). Ambos são **null-como-artefato**, não null-como-informação.

---

**Artefatos desta análise** (em `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/t11/baterias/b5r/`):
`b5r_t11_bateria.py` → `b5r_t11_celulas.csv` (45 células × 80 checagens: estrutura, T11, LHS, FE-40k, GP, seleção, ⑦, ⑥) · `b5r_t11_gp_pares.csv` (104 pares célula×objetivo: teto/zero/NaN de σ, ptp de μ) · `probe_vetores_degenerados.py` + `probe_vetores.log` (**a prova executada em `env_b5` do A32 e da granularidade da ③**) · `b5r_t11_smoke_audit.log` (auditoria do smoke T11 de b5r + controle b5m).
**Insumos pré-computados consumidos sem recomputar**: `f5/sonda_f52e.csv`, `f5/contrato_f52b.csv`, `f5/integridade_f52a.csv`, `f5/tempo_f52d.csv`, `f5/baterias/b5r/b5r_C_pares7.csv`.
**Interpretadores**: `/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python` (análise) · `/Users/gmello/Documents/python_venvs/env_b5/bin/python` (a prova do A32, em tempdir).
**Read-only respeitado**: nenhuma célula executada, `experiments.py` nunca invocado, `data/experiments` nunca tocado, código de algoritmo e bundles apenas lidos. A única escrita foi na pasta autorizada acima.