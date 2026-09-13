## A. FICHA DO MECANISMO (do artigo)

Fonte: Mazumdar, López-Ibáñez, Chugh, Hakanen, Miettinen (2023), *Evolutionary Computation* 31(4):375–399, DOI 10.1162/evco_a_00329. Laço central (Algoritmo 1 + Fig. 2 + §3.1; pseudocódigo recuperado do OCR da p. 8):

1. **Entrada**: dataset offline (X ∈ ℝ^{N×n}, Y ∈ ℝ^{N×K}); parâmetros N_min, I_max, G_max (Alg. 1, Input). Nenhuma FE real durante a busca — regime offline puro (Abstract; §2).
2. **Árvores de regressão, uma por objetivo** (K árvores), treinadas com TODOS os dados, split por minimização do MSE total (Eq. 5–6, §2.2); recursão até que um split gerasse folha com < N_min amostras; profundidade "não controlada" (§3.1: "Just the parameter N_min is adjusted, and the depth of the trees is not controlled"). Predição da folha = média ȳ_l (§2.2). Máx. de N/N_min folhas; cada folha tem entre N_min e 2N_min−1 pontos (§3.3).
3. **Inicializa a população do MOEA** (Alg. 1 linha 2). MOEA = RVEA (Cheng et al. 2016) com parâmetros default; decomposição por vetores de referência + seleção APD; adaptação dos vetores a cada 100 gerações (§4.1.3, §4.1.5).
4. **Laço de construção** (while I < I_max E alguma solução cai em folha sem GPR — Alg. 1): roda RVEA por G_max=50 gerações sobre o surrogate corrente (árvores + GPs já colocados); offsprings por "crossover and mutation" (§3.1).
5. **Colocação de GPR dirigida por erro**: ao fim de cada rajada, para cada objetivo j, identifica as folhas que predizem as s soluções correntes, calcula H(Q) (MSE, Eq. 6) dessas folhas e constrói **um** GPR na folha i\* = argmax H (Alg. 1; §3.1; Fig. 4). Várias soluções na mesma folha ⇒ um só GPR. GPR local usa SÓ o subconjunto da folha (N_min…2N_min−1 pts).
6. **Modelo substituto local**: GPR (GPy) com kernel **Matérn 5/2 + ARD** (§2.1, §4.1.3), média zero, hiperparâmetros por máxima verossimilhança marginal (Eq. 3). Predição posterior μ e variância (Eq. 4).
7. **Regra de predição do surrogate composto**: se o ponto cai em folha com GPR → **média posterior do GPR**; senão → média da folha da árvore (§3.1, p. 383). **A variância NUNCA é consumida** — uso da incerteza é trabalho futuro declarado (§5).
8. **Parada da construção**: (i) I = I_max = N/N_min = N/(10n) iterações, ou (ii) todas as soluções da população caem em folhas que já têm GPR (§3.1, bullets p. 383).
9. **Otimização final**: RVEA por 1.000 gerações sobre o surrogate congelado (ou continuação da população da fase de construção — §3.1 p. 383/§4.1.5); adaptação de vetores a cada 100 ger.; saída = ND final.
10. **Sem gestão de arquivo própria** — população/nichos são os do RVEA; não há arquivo externo nem reavaliação real (avaliação com funções verdadeiras só como métrica de benchmark, §4.1.6).
11. **Parâmetros com valores do paper**: N_min = 10n; I_max = N/(10n); G_max = 50; otimização final 1.000 ger.; adaptação a cada 100; sparse-GP comparador com M = 10n pontos indutores; HV-ref = (2√K,…,2√K); 31 datasets/caso; Wilcoxon 2-caudas + Bonferroni, α=0,05 (§4.1.3–4.1.6). Complexidade pior caso O(KN(2N_min−1)²) tempo, O(KN(2N_min−1)) memória (§3.3).

## B. ASPECTOS COMPORTAMENTAIS VERIFICÁVEIS

Convenção: ①=`__real`, ②=`__pop`, ③=`__surrogate`, ④=`__timing`, ⑦=`__final`; `sur` = ③ lida com pandas; N=31D−1 no tier small.

| # | aspecto | paper prescreve (ref) | SPEC/bundle mudou | evidência nos dados | query | assinatura se fiel | verif. |
|---|---|---|---|---|---|---|---|
| 1 | Orçamento FE = dataset; zero FE na busca | offline: "no new data" (Abstract, §2) | D90: dataset=orçamento=31D−1; ⑦ fora do orçamento (§11/DI-08) | ①.shape; manifest `maxfe/fe_final`; timing `tempo_aval_real_s` | `len(real)==31*D-1 and man['fe_final']==man['maxfe']` | ① tem exatamente N linhas, `fe_final==maxfe==N`, `tempo_aval_real_s==0.0` | direta |
| 2 | Proveniência do dataset (CP-init) | dado precoletado (§2) | D63/D87/D90: dataset artefato + hash | manifest `cp_init_offline{x_hash,f_hash}`, header `dataset_hash`; footer `cp_init` | comparar hashes com sidecar `data/datasets/{p}/`; `footer['cp_init']==True` | hashes idênticos ao sidecar | direta |
| 3 | ① toda `fase='init'` | n/a (offline não tem infill) | D90 | ①.fase | `real.fase.value_counts()` | 100% `init`; `fe_index` 0..N−1 denso | direta |
| 4 | K árvores, 1/objetivo | Alg. 1 linha 1 | nada | jsonl `decision`: `n_folhas`, `profundidade`, `n_gps` são listas de tamanho M | agregação jsonl: `len(ev['n_gps'])==M` | listas de comprimento M em todos os eventos | direta |
| 5 | N_min = 10n | §4.1.3 | nada (paper ✓) | manifest `params.min_samples_leaf` | `params['min_samples_leaf']==10*D` | 20 (D=2) / 120 (D=12) / 300 (D=30); e `max(n_folhas)<=ceil(N/(10D))` | direta |
| 6 | max_depth | "depth not controlled" (§3.1) | código oficial: **max_depth=100** (bundle v2.2, impl 🟠 D29) | manifest `params.max_depth`; jsonl `profundidade` | `params['max_depth']==100` | 100 declarado; profundidade observada 1–2 (nunca encosta no teto) | direta (declaração) |
| 7 | I_max = N/(10n) | §4.1.3 | float→**ceil** via `continue_evolution` (bundle) | nº de eventos `decision`; ④ nº de linhas | `sum(1 for e in evs if e['rec']=='decision') == ceil(N/(10*D))` | tier small: **sempre 4** (31D−1)/(10D)≈3,1→4; ④ com 4 linhas | direta |
| 8 | G_max=50/iteração | §4.1.3 | +1 ger/iteração do `_refresh_population` ⇒ 51/iter (DI-28c) | ③ busca: `geracao` da fase build; ④ `geracao` | `busca[busca.modelo_flag=='treedGP_build'].geracao.max()==204` | blocos de 51: ④.geracao = 51/102/153/204; build = ger 1..204 | direta |
| 9 | Otimização final 1000 ger | §4.1.5 (10×100) | nada (paper ✓) | ③ `modelo_flag='treedGP_final'` | `final.geracao.min()==205 and final.geracao.max()==1204` | 1000 gerações exatas; `n_geracoes==1204` no manifest/footer | direta |
| 10 | Contador de geração único 2-fases | n/a (nosso desenho) | C311-11/DI-16.19 | ③ `geracao` 1..1204 sem furo | `set(range(1,1205))==set(busca.geracao.dropna().astype(int))` | zero buracos; fase lida SÓ em `modelo_flag` | direta |
| 11 | 1 GP/árvore/iteração na folha argmax-perda | Alg. 1; §3.1 | código: argmax da **impurity de treino** entre folhas visitadas sem GP (=paper na prática) | jsonl `n_gps`, `total_points_per_model` | monotonia: `n_gps[j]` cresce ≤1/iter; `total_points_per_model[j]` cresce e satura ≤N | incrementos de pontos ∈[N_min, 2N_min−1]; saturação em N quando cobre tudo | indireta (folha escolhida não é exportada) |
| 12 | Predição = μ_GP na folha com GP, média da árvore fora; σ só onde há GP | §3.1 p. 383 | **σ = extensão NOSSA** (B15.5/D30, 🟢): `sqrt(var_GPy)`, NaN nas folhas sem GP (DI-16.9) | ③ `sigma_*` NaN por região | `busca[busca.geracao<=50].sigma_0.isna().mean()==1.0`; NaN share por `modelo_flag` | ger 1–50 (antes do 1º GP): σ 100% NaN; fase final: ~0% NaN | direta |
| 13 | Modelo CONGELADO na fase final | §3.1 ("without further modifying the surrogates") | DI-16.12: 2 blocos de sonda | ③ sonda: 2 blocos de 20.000, `geracao=NULL` | `b1=sonda.iloc[:20000][mu+sig]; b2=sonda.iloc[20000:]...; b1.equals(b2)` | blocos **bit-idênticos** (max\|Δμ\|=0) | direta |
| 14 | Sonda offline: 2 blocos, hash, ordem posicional | n/a (§17.2.2/DI-16.12) | extensão nossa de instrumentação | jsonl `sonda` ×2; manifest bloco `sonda` | `sonda_ev['hash_check'].startswith('ok')`; `len(sonda)==40000` | 2 eventos (`treedGP_build`,`treedGP_final`), n_pontos=20000, hash ok | direta |
| 15 | RVEA pop lattice 50 (M=2)/105 (M=3), pode encolher | §4.1.3 (default Cheng 2016) | nada | ③ busca: linhas/geração = pop SELECIONADA (DEF-C2) | `busca.groupby('geracao').size().describe()` | teto 50/105 nunca excedido; colapso p/ 3–7 nas ger 1–50 (árvore constante-por-partes esvazia nichos) e recuperação após 1º GP | direta |
| 16 | Early-stop: paper = "todas as soluções em folhas com GP"; código = janela de 2 iter sem crescimento, mínimo 6 | §3.1 vs código (B15.8, nuance 🟠) | bundle adota o código | jsonl `early_stop`, `delta_total_point` | `all(e['early_stop']==False ...)` | tier small: early-stop **inerte** (I_max=4 ≤ 5) — 4ª iteração roda mesmo com cobertura completa na 3ª (MMF1) = comportamento do código, não do paper | direta (a inércia); o mecanismo em si só no sweep-big |
| 17 | ② vazia por construção | n/a (pop RVEA nunca é membro do dataset) | DI-16.17 | ② 0 linhas; ③ `real_solution_id` | `len(pop)==0 and busca.real_solution_id.notna().sum()==0` | ambas zero | direta |
| 18 | ⑦: avalia TODOS os finais, ND filtrado APÓS a real | §11/B7.5 | DI-13.9; `nd_pos_real` = erro de fantasia | ⑦ | recomputar Pareto de f0..f{M-1} de ⑦ e comparar com `nd_pos_real` | igualdade exata; `len(⑦)==footer['n_final']==pop da ger 1204`; `origem_geracao==1204`; link posicional (ger, linha) casa X bit-a-bit | direta |
| 19 | ④ por retreino; `tempo_geracao_s` EXCLUI a sonda | n/a | C311-09 + DI-13.10 | ④ 4 linhas | `(tim.tempo_fit_s+tim.tempo_busca_s<=tim.tempo_geracao_s+1e-6).all()` e na linha com sonda `fit+busca+sonda > tempo_geracao_s` | 4 linhas, geracao=51/102/153/204; sonda só na última | direta |
| 20 | `fe_treino_max` constante = N−1 | n/a | D90 (offline não retreina em FE) | ③ | `sur.fe_treino_max.unique()==[N-1]` | valor único N−1 | direta |
| 21 | Kernel Matérn 5/2 ARD, sem White/normalizer, `optimize('bfgs')` único | §2.1/§4.1.3 + código | guard try+dedup (LinAlgError) — nossa guarda | manifest `params.kernel`; jsonl `guard` (ausência) | `params['kernel']` contém 'Matern52 ARD'; contar `rec=='guard'` | declaração presente; 0 guards disparados em runs sadios | não-verificável nos dados (só declaração; prova = código/re-run) |
| 22 | seleção 'mean' — σ nunca consumido | paper nunca consome σ (§5) | 🟢 D29: σ exportado, NÃO consumido | `params.selection_type=='mean'`; sigma_dict | declarativa + contrafactual impossível nos dados | — | não-verificável (código) |
| 23 | Semeadura D62 (mesmo s em np.random+random; gancho lhs DI-28.3) | n/a | DI-28 ratificada | nenhuma coluna | só por re-execução bit-idêntica | ① e ③ bit-iguais em re-run | não-verificável (re-run) |

## C. GROUNDING NOS DADOS REAIS (executado)

**Células sondadas:** `exp_off_c311_{MMF1,DTLZ2,ZDT1}_42*` (todas `status:ok`, `n_retries:0`, `fallback_ativado:false`).

**Schemas reais (verificados):**
- ①: `algoritmo|problema|semente|solution_id|x0..x{D-1}|f0..f{M-1}|fe_index|fase` — x/f float32, ids int32. Linhas: **61/371/929 = 31D−1 exato**; `fase='init'` em 100% das linhas (não é 11D−1+opt: offline a ① é o DATASET inteiro, D90); `fe_index` denso 0..N−1; `solution_id` 100% único.
- ②: schema presente, **0 linhas** nas 3 células (DI-16.17 confirmada).
- ③: `...|regime|geracao|x*|real_solution_id|mu_*|sigma_*|pred_tipo|pred_classe|pred_score|pred_confianca|modelo_flag|espaco_modelo|transf_tipo|transf_params|fe_treino_max`. Linhas: MMF1 96.581 (busca 56.581 + sonda 40.000); DTLZ2 144.031 (104.031+40.000); ZDT1 95.114 (55.114+40.000). `pred_tipo='valor'` 100%; `espaco_modelo='cru'`, `transf_tipo=None`; `real_solution_id` 100% NULL; `fe_treino_max` único = {60/370/928}. ⚠ `geracao` lê como **float64** (int nullable + NaN da sonda — regra §10.2 do contrato em ação).
- ④: `run_id|geracao|n_acumulado|tempo_fit_s|tempo_busca_s|tempo_pred_sonda_s|tempo_geracao_s` — **4 linhas** (geracao 51/102/153/204). DI-13.10 provada numericamente: `fit+busca ≤ tempo_geracao_s` nas 4; na linha 204 `fit+busca+sonda > tempo_geracao_s`.
- ⑦: `...|x*|f*|origem_solution_id|origem_geracao|origem_linha|nd_pos_real` — 50/94/50 linhas; `origem_geracao=1204` em todas; `origem_solution_id` 100% NULL; link posicional (ger,linha)→③ **casa X bit-a-bit** (verificado).

**jsonl real:** 9 linhas/célula; discriminador é **`rec`** (não `ev`), sequência `header, decision×4, sonda×2, footer×2`. NÃO existe evento `c311_gen` nem evento por geração — o registro de decisão é **1 `decision` por iteração de construção** com campos: `caminho='c311_build'`, `motivo`, `geracao` (51/102/153/204), `iteracao`, `n_gps[M]`, `n_acumulado`, `n_folhas[M]`, `profundidade[M]`, `total_points_per_model[M]`, `delta_total_point`, `early_stop`, `fe`, `f_best[M]`, `n_front1`, `tempo_fit_s`, `tempo_busca_s`. Evento `sonda`: `modelo_flag`, `geracao:null`, `fe`, `n_pontos:20000`, `tempo_pred_sonda_s`, `fe_treino_max`, `sonda_x_hash/f_hash`, `hash_check:"ok (conferido no arranque — load_sonda)"`, `motivo`. **Dois footers**: o do runner (`status, motivo, fe_final, cp_init, cache_hits, n_geracoes, n_final, n_nd_pos_real`) e o do despachante (`status, n_retries, tempo_total_s, stack_trace`). ⚠ Não há chave `motivo_parada` em lugar nenhum — a triagem para c311 é `footer.motivo` (null quando ok) + `stack_trace` + presença dos 2 blocos de sonda + `n_geracoes==1204`.

**sigma_dict (íntegra, resumo fiel — idêntico nas 3 células exceto `fe_treino_max`):** modelo treed-GP (árvore MSE min_samples_leaf=10D, max_depth=100 + GP GPy Matern52 ARD bfgs único na folha de maior impureza; predição = μ da árvore sobreposta pelo μ do GP); `regime`: offline=busca RVEA 2 fases / sonda=régua §17.2.2; `modelo_flag`: treedGP_build×treedGP_final com contador `geracao` ÚNICO (C311-11/DI-16.19); `mu_*`: minimização, espaço NATIVO (sem normalizer — DI-16.9); `sigma_*`: **sqrt(var_GPy), extensão NOSSA (B15.5), NaN nas folhas SEM GP — semântica POR-REGIÃO, não por-run**; `espaco_modelo` cru; sonda: 2 blocos de 20.000, geracao=NULL, ordem POR POSIÇÃO, predict_batch DI-16.13; `pop_2_vazia` (DI-16.17, gate não deve exigir ②); `fe_treino_max` constante N−1; `timing_4`: ④=1 linha/retreino de construção; `abertas_torre`: TODAS ratificadas (DI-28 a/b/c + gancho lhs DI-28.3).

**Contagens/assinaturas medidas:**
- `n_geracoes=1204` nas 3 células (204 build + 1000 final) — e será 1204 em TODAS as células do tier small, pois I_max=⌈(31D−1)/(10D)⌉=4 sempre.
- Contador 1..1204 **sem furos**; build=1..204 (`treedGP_build`), final=205..1204 (`treedGP_final`).
- 2 blocos de sonda **bit-idênticos** (max|Δμ|=0; colunas x também idênticas entre blocos) nas 3 células — modelo congelado provado.
- σ-NaN: gerações 1–50 = **100% NaN** (não há GP antes do 1º addGPs); fase build 3,6–21,6%; fase final 0% (MMF1/DTLZ2) e 0,02% (ZDT1). Na SONDA: MMF1/DTLZ2 0% (cobertura total das folhas: n_gps==n_folhas) vs **ZDT1 sigma_1 32,3% NaN** (1 folha de f1 sem GP cobre ~1/3 do volume) — enquanto na busca só 0,78%: a busca se concentra na região coberta. Assinatura riquíssima e barata.
- Pop por geração: colapso a 3 (M=2) / 7 (M=3) nas ger 1–50 (árvore constante-por-partes esvazia nichos APD) → crescimento após o 1º GP → mediana 50/94/50 na fase final (M=3 nunca chega ao lattice 105; máx 95).
- Crescimento incremental: MMF1 `total_points_per_model` [20,34]→[40,61]→[61,61]→[61,61] (incrementos 20–27 ∈ [N_min=20, 2N_min−1=39] ✓; saturação = dataset inteiro coberto); `n_gps` final [3,2] == `n_folhas` [3,2]. DTLZ2: n_gps [2,3,2] == n_folhas; ZDT1: n_gps [2,2] < n_folhas [2,3] (1 folha órfã — a origem do NaN da sonda).
- `early_stop=false` nas 12 decisões; `delta_total_point=1.0` constante (sentinela: janela exige it>5, nunca alcançado no tier small).
- ⑦: ND recomputado == `nd_pos_real` (exato nas 3): MMF1 **9/50** (erro de fantasia brutal — coerente com o prior "fraco no MMF1"), DTLZ2 93/94, ZDT1 50/50.
- Curioso comportamental: `f_best` do DTLZ2 fica **negativo** (−0,309) nas iterações 3–4 — μ do GP extrapola abaixo do range físico (DTLZ2 f≥0): o "erro de fantasia" já visível em pleno voo no jsonl.

**Veredito das queries da §B:** todas as marcadas "direta" foram EXECUTADAS como propostas e passaram, com 3 ajustes necessários: (a) o filtro de busca é `regime=='offline'` (não `'busca'` — o valor real da coluna); (b) eventos filtram-se por `rec` (`decision`/`sonda`/`footer`), nunca por `<alg>_gen`; (c) `geracao` precisa de `dropna().astype(int)` (float64 nullable). Query #16 (mecanismo do early-stop) é INVIÁVEL no tier small (parâmetro estruturalmente inerte); #21–#23 são não-verificáveis por desenho (ver F.iv).

**Surpresas contrato×dado:** (1) contrato §6 promete `<alg>_gen` por geração — c311 grava 4 `decision` por run (1/iteração), 1204 gerações sem evento próprio (o filme por geração vive na ③, não no ⑥); (2) não existe `motivo_parada`; o campo é `footer.motivo`; (3) dois registros `footer` (runner + despachante) — não é duplicação; (4) contrato §1 descreve ① como "init 11D−1 + infills" — no offline é N linhas todas `init` (D90, o próprio contrato §1 nota); (5) S.7 do c311 prometia "early-stop; folha pior-MSE" — o jsonl loga `early_stop` booleano e `delta_total_point`, mas NÃO exporta a identidade/MSE da folha escolhida (ver F.iv).

## D. SETUP EXPERIMENTAL DO PAPER

**Problemas:** DBMOPP P1–P4 (Fieldsend et al. 2019; Tabela 1: variações de disconnected set regions/local fronts/dominance resistance), n ∈ {2,5,7,10} × K ∈ {3,5,7} = 48 instâncias; DTLZ só no material suplementar (não incluso no PDF; DTLZ2 n=10, K=2 aparece como ilustração na Fig. 3). **Datasets:** N ∈ {2.000, 10.000, 50.000}, LHS e MVNS (média no centro, var 0,1) — 288 casos × **31 seeds**. **Orçamento de FE na busca: ZERO** (offline; avaliação real só como métrica). **Métricas:** HV com ref (2√K,…) e RMSE multivariado das soluções + tempo de construção; Wilcoxon 2-caudas + Bonferroni α=0,05, ranking por score ±1.

**Números citáveis (Tabelas 2–3):** full GPR **OOM em N≥10k** (2,3 GiB @10k, 56 GiB @50k, cap 2 GiB/run). Tempo de build @2.000: TGPR-MO 12,7–28,3 s vs full 136–616 s vs sparse 86,4–551 s. @10.000: TGPR-MO 14,2–89,4 s vs sparse 1.450–9.370 s. @50.000: TGPR-MO **31,6**–191 s vs sparse **21.600**–50.500 s (~10²–10³×). RMSE @2.000 (LHS,P3,K=3,n=5): full **4,18E-2** < TGPR 2,67E-1 < sparse 1,04E0 (full vence em N pequeno!). @50.000 (LHS,P3,K=3,n=10): RMSE TGPR 3,91E-1 vs sparse 8,29E-1; HV TGPR 7,30E+1 vs sparse 6,04E+1. Sumário Tabela 2: TGPR melhor em tempo em 46–48/48; melhor HV que sparse em todos os N; full GPR vence HV/RMSE em N=2.000. **O paper não reporta IGD/IGD+ em nenhum lugar.**

**Interseção com os nossos 25 problemas — veredito por problema:**
- **DBMOPP (todo o corpo principal do paper): interseção VAZIA** — nenhum DBMOPP no nosso grid.
- **DTLZ2** (único nome em comum): paper usa n=10/K=2 como ilustração (Fig. 3, sem tabela) e DTLZ no suplementar (fora do corpus); nosso DTLZ2 é D=12/M=3/N=371. **Incomensurável** (dimensão 10≠12, M 2≠3, N 2.000≠371, métrica HV-2√K≠IGD+/HV-normalizado, e o paper não publica número).
- **Todos os demais 24 (MMF*, ZDT*, DTLZ1/3/4/7, WFG*, BBOB_F*): incomensuráveis por inexistência no paper.**
- **Eixo mais grave, transversal:** nosso tier small N=31D−1 (61–929) fica **1–2 ordens de grandeza ABAIXO do menor N do paper (2.000)** — e o próprio paper mostra que em N pequeno o full GP domina o TGPR-MO; rodamos o algoritmo FORA do envelope de projeto dele (explica o MMF1 com dataset 61 e nd_pos_real 9/50). **O único ponto de comparação canônica é o tier big=50k (c311-only, D38/sweep)**: aí a âncora J (build treed ~31,6 s × sparse 21.600 s @50k; OOM do full ≥10k) é diretamente confrontável em ORDEM DE GRANDEZA via ④/`fit_series` — comparação de forma/custo, nunca de HV absoluto (problemas diferentes).

## E. O QUE O AGENTE-4 ACRESCENTA

**Acréscimos reais sobre o artigo cru:** (1) consolidação dos parâmetros dispersos numa ficha única (N_min=10n, I_max=N/N_min, G_max=50, 1000 ger. finais, adaptação/100, M=10n do sparse, ref 2√K); (2) a taxonomia das **duas incertezas** — MSE intra-folha da árvore [USADO, gestão de modelo] vs variância posterior do GPR [DISPONÍVEL, NUNCA usada] — com o teste contrafactual explícito ("remover a variância do GPR não muda nada na busca"); (3) classificação de maquinaria (Offline-Confiabilidade classe 6, aderência 5, alternativa defensável Offline-Outro) e o registro de honestidade G1=outros/G5=false estrito — essencial para a dissertação não vender o c311 como exemplar de uso de incerteza; (4) HG2-FALHA fundamentado (mismatch offline×FE-orçado) — antecipou a necessidade da trilha offline separada (D77/D90); (5) racional árvore-vs-K-means (perda no espaço-objetivo) e a limitação de descontinuidade entre GPs vizinhos; (6) URL do código oficial + stack (DESDEO/sklearn/GPy).

**Contradições/lacunas (agente-4 × bundle × artigo):**
1. **Profundidade da árvore:** artigo: "the depth of the trees is not controlled" (§3.1); agente-4 repete ("profundidade livre", §3.4-2); bundle v2.2 corrige pelo código: **`max_depth=100`** ("⟦v2.2⟧ max_depth=100 (não 'livre')") — e o manifest grava 100. Vence o código (🟠 impl); o agente-4 ficou com a letra do paper.
2. **Critério de parada:** agente-4 transcreve o do paper ("todas as soluções da população caírem em folhas que já têm GPR", §3.4-5); bundle: código = `delta = total_points − sequence[counter−3]` com `counter>5` (janela de 2 iter, mínimo 6 — B15.8 "rebaixada de divergência a nuance"). **Os dados decidem:** no MMF1 a cobertura completa ocorre na iteração 3 e a 4ª iteração RODA mesmo assim — comportamento do código, não do paper. O agente-4 não conhece essa nuance.
3. **Early-stop inerte:** nem agente-4 nem o paper percebem que com N=31D−1 ⇒ I_max=4 o early-stop do código **nunca pode disparar** (exige >5 iterações) — só o bundle registra ("edge 61 pts/D=2 → 4 iterações, early-stop inativo").
4. **Hazards de engenharia ausentes no agente-4:** `optimize('bfgs')` sem try (LinAlgError mata a run — o B1/gpy_bfgs_linalg do sweep-big), predict 1-ponto-por-linha (~39M chamadas @50k sem mitigação), `graphviz` import duro, duas implementações no repo (treeGP canônica × HybridTreeGP_v2) — tudo só no bundle.
5. **Operadores:** paper diz só "crossover and mutation"; agente-4 infere "default do RVEA é SBX + mutação polinomial" (correto, confirmado pelo bundle: SBX/PM com RNG numpy global + `random.shuffle`).
6. Concordância trina onde importa: σ do GPR nunca consumido (artigo §5 = agente-4 §4 = bundle B15.5/D30 🟢) — a base da nossa extensão declarada.

## F. PROPOSTAS PARA O PROTOCOLO PADRONIZADO

**(i) Generaliza para os 24 configs:**
- **Ordem de leitura fixa:** manifest (`status`, `params`, **`sigma_dict` SEMPRE antes da ③**, `timing`, hashes) → jsonl (tipos de `rec` reais, header/footer) → ③ (regimes, `modelo_flag`, contador de geração) → ④ → ⑦/① → só então queries de mecanismo.
- **Passo zero: derivar a "tabela de constantes esperadas" do config a partir dos params ANTES de abrir dado** (para c311: n_geracoes=1204, 4 decisions, 4 linhas ④, 2 sondas, ② vazia). Fidelidade vira diff contra constantes previstas — barato e agnóstico de família.
- **Queries reutilizáveis** (copiar como estão): orçamento (①==31D−1; offline: 100% `init` + `fe_final==maxfe`); continuidade do contador de geração; hash-check CP-init vs sidecar; sonda: contagem de blocos + `hash_check` + (offline) bit-identidade entre blocos; ④: `fit+busca ≤ tempo_geracao_s` em 100% e violação exatamente nas linhas com sonda (prova DI-13.10); ⑦: recomputar o Pareto e comparar com `nd_pos_real` + casar X posicional (ger,linha); σ/μ dtypes float32 e ids int32.
- **Triagem**: nunca por `status` do despachante (B1); protocolizar como: presença do footer do runner + `footer.motivo` + `stack_trace` + contagem de blocos de sonda + `n_geracoes` esperado.
- **Regra editorial**: toda extensão nossa (classe 🟢 D29) deve ser verificada como NÃO-INTRUSIVA (aqui: σ exportado com o run bit-igual — verificável só por re-run, declarar o teto).

**(ii) Específico da FAMÍLIA (offline / GP-regressor treed):**
- Discriminar fases por `modelo_flag` (nunca por faixa de geração hard-coded em outros configs — aqui 204 é derivável, alhures não).
- **Prova de congelamento** = bit-identidade dos 2 blocos de sonda (só offline tem isso; nos online a sonda evolui).
- **σ POR-REGIÃO** (NaN = folha sem GP) é semântica exclusiva do treed-GP: o protocolo deve tratar NaN de σ como INFORMAÇÃO (cobertura das folhas), medindo NaN-share por fase e por regime — a tríade (100% em ger 1–50; ~0% no final; X% na sonda = fração do volume sem GP) é a assinatura de fidelidade mais barata do mecanismo.
- **Curva de cobertura**: `total_points_per_model`/`n_gps`/`n_folhas` do jsonl — monotonia, incrementos ∈ [N_min, 2N_min−1], saturação ≤ N; n_gps ≤ n_folhas por objetivo.
- **Colapso populacional da fase árvore-pura** (pop 3–7 sob predição constante-por-partes) — assinatura da inicialização "sem GPRs" do Alg. 1; se a pop da ger 1 já for ~lattice, algo está errado (GPs iniciais = HybridTreeGP_v2, a implementação ERRADA).
- ② vazia e `real_solution_id` todo NULL são POR-DESENHO nesta família (DI-16.17) — o gate não pode exigi-los.
- `nd_pos_real`/n_final é o endpoint de fantasia da família offline: reportar sempre a razão (9/50 vs 50/50 discrimina células saudáveis de células fora do suporte do dataset).

**(iii) Armadilhas para um agente fresco neste config:**
1. Procurar `c311_gen` no jsonl → zero resultados → falso "log quebrado" (o evento é `rec:'decision'`, 4 por run; o filme por geração está na ③).
2. Filtrar busca com `regime=='busca'` → dataframe vazio (o valor é `'offline'`).
3. Tratar σ=NaN como bug de export (é a folha sem GP; ler o sigma_dict ANTES — regra §10.3).
4. Exigir ② não-vazia ou `real_solution_id` preenchido → reprovaria um run perfeito.
5. Buscar `motivo_parada` no manifesto → não existe; é `footer.motivo`.
6. Achar que os 2 footers são gravação duplicada (runner+despachante, DI-13.1).
7. Esperar pop=105 no M=3 (o RVEA encolhe; máx observado 95) ou estranhar pop=3 nas ger 1–50.
8. Join da sonda por `sonda_id` (a ③ não tem a coluna; é POR POSIÇÃO dentro do bloco, §10.5/10.10).
9. `astype(int)` ingênuo em `geracao` (float64 com NaN da sonda) → exceção.
10. Cobrar do run o critério de parada do paper (cobertura completa) — a 4ª iteração pós-cobertura é fiel AO CÓDIGO (B15.8); e cobrar early-stop exercitado — estruturalmente impossível no tier small.
11. Comparar HV/RMSE com as tabelas do paper (DBMOPP, N≥2000, ref 2√K) — nada é comensurável no tier small; só a âncora de escalabilidade no big.
12. Interpretar `f_best` negativo (DTLZ2) como bug de sinal — é extrapolação legítima do μ do GP.
13. `delta_total_point=1.0` constante não é métrica viva — é sentinela do early-stop inerte.

**(iv) TETO de verificabilidade honesto (exige código/re-execução, NÃO sai dos dados):**
- **A escolha da folha** (argmax impurity de treino entre folhas visitadas sem GP): identidade/MSE da folha escolhida não são exportados — só vemos consequências agregadas (n_gps, points). Prova plena = código.
- **selection_type='mean' / não-consumo do σ na busca**: dos dados só se lê a declaração; o contrafactual (a busca seria idêntica sem σ) é logicamente inverificável ex-post — prova = leitura do `APD_Select` + re-run.
- **Kernel e otimização do GP** (Matérn52 ARD, sem White/normalizer/priors, bfgs único sem restarts, jitchol): invisíveis na ③ (μ/σ não fingerprintam kernel); prova = código/env lock (GPy 1.9.9).
- **Disciplina de RNG** (D62/DI-28: mesmo s nos 2 RNGs, gancho lhs, PYTHONHASHSEED=0): só re-execução bit-idêntica de ① e ③ prova.
- **Aritmética interna do APD (α=2), SBX/PM e a contagem `_refresh_population`** — a última tem prova INDIRETA forte nos dados (204=4×51), mas a decomposição 50+1 por iteração não é observável.
- **Early-stop do código**: mecanismo morto no tier small; verificável apenas nas células sweep-big (onde, atenção, vive também o B1 gpy_bfgs_linalg mascarado como ok).
- **Não-perturbação da sonda**: no offline o risco é ~nulo (modelo congelado, predict determinístico), mas a prova formal (① idêntica com/sem sonda) exige re-run pareado.

Arquivos-chave usados: artigo em `.../corpus_artigos/_artigos_markdown/c311. Treed Gaussian Process Regression....md`; `.../agente4/c311/c311_full.md` e `c311_resumo.md`; `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/claude_code_context/30_rodada3_standalone/alg_c311_tgprmo.md`; `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/CONTRATO_DE_DADOS.md`; células em `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/experiments/off/c311/`.