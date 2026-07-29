## A. FICHA DO MECANISMO (do artigo)

Knowles, "ParEGO: A Hybrid Algorithm With On-Line Landscape Approximation for Expensive Multiobjective Optimization Problems", IEEE TEVC 10(1):50–66, 2006. Laço central (Alg. 1, §III–IV):

1. **Init DoE**: Latin hypercube de `11d−1` soluções (procedimento LATINHYPERCUBE, Alg. 1 linhas 2–5 e 15–18; escolha herdada de Jones et al. [35], §III-A), todas avaliadas na função cara.
2. **Normalização do espaço de custo**: cada objetivo re-escalado para [0,1] "with respect to the known (or estimated) limits of the cost space" (§IV, antes da Eq. 1). *O paper normaliza por limites conhecidos/estimados — não pelo arquivo.*
3. **Sorteio de λ por iteração**: vetor de pesos sorteado uniformemente do conjunto de vetores uniformemente distribuídos da Eq. (1), parametrizado por s; |Λ| = C(s+k−1, k−1) → **11 vetores (k=2), 15 vetores (k=3)** (Table V; §VII-B: número escolhido para permitir "várias passadas" por vetor dentro do orçamento). Alg. 1 linha 19 (NEWLAMBDA).
4. **Escalarização Tchebycheff aumentada**: `f_λ(x) = max_j(λ_j·f_j) + ρ·Σ_j λ_j·f_j`, **ρ=0,05** (Eq. 2); re-escalariza TODAS as soluções visitadas sob o λ corrente (a mesma solução muda de custo escalar a cada iteração). Escolhida porque o termo max alcança soluções não-suportadas e o termo linear pune fracamente-dominadas (§IV).
5. **Subset de treino**: iteração < 25 → todas as soluções; senão subconjunto de `11d−1+25`, **metade as melhores sob o λ vigente + metade aleatórias sem reposição** (§IV, parágrafo pós-lista do EA). No EGO base, cap da matriz de correlação em 80 (§III-A); em ParEGO "we also cap the size of the model but use a slightly more advanced selection procedure". Ressalva do autor: "on a very expensive cost function, all solutions evaluated should be used… at every iteration" — o cap é concessão aos 21 runs.
6. **Modelo substituto**: DACE/Kriging (Sacks et al. 1989) **mono-output sobre o custo escalarizado** (1 GP, não M GPs); 2d+2 parâmetros; interpola sempre; verossimilhança e erro de predição em forma fechada — "the model estimates its own uncertainty" (§III, bullets). **Retreina a cada iteração** (Alg. 1: DACE dentro do while). MLE via **Nelder–Mead com 20 restarts** (§IV/Alg. 1 linha 25; implementação em C/matpack).
7. **Aquisição = Expected Improvement**: EI clássico do EGO sob N(μ(x),σ(x)²) — "a parte da curva do erro-padrão que cai abaixo do melhor custo amostrado" (Fig. 1, §III); pesa μ E σ, "EGO does NOT just choose the solution that the model predicts would minimize the cost". Maximizado por **GA interno** (EVOLALG, Alg. 1 linha 28): pop **20**, **steady-state** (1 filho/geração), torneio binário sem reposição, SBX p=0,2, mutação por shift ±(1/100)·μ_r·range com p_gene=1/d, **10.000 avaliações do modelo** (§IV texto; **Table V diz 200.000 — inconsistência interna do paper**), init = 5 mutantes dos 5 melhores sob λ + 15 em LHS.
8. **1 FE real/iteração**: o argmax-EI é avaliado na função cara e entra no conjunto (Alg. 1 linhas 11–12); sem paralelismo (feature 3, §I).
9. **Parada e saída**: orçamento fixo (100 e 250 FEs nos experimentos); saída = conjunto não-dominado de todos os pontos visitados (§VII).
10. **Gestão de população/arquivo**: não há população evolutiva externa — o "arquivo" é o conjunto de TODAS as soluções avaliadas; a diversidade emerge da varredura de λ (sem niching; limitação reconhecida no §IX-2).

## B. ASPECTOS COMPORTAMENTAIS VERIFICÁVEIS

Notação: ① `__real`, ② `__pop`, ③ `__surrogate`, ④ `__timing`, ⑥ `.jsonl`. `ge` = eventos `rec=='b1_gen'` do ⑥; `sur` = ③; `busca` = `sur[sur.regime=='online']` (⚠ o literal é `'online'`, não "busca").

| # | aspecto | paper prescreve (ref) | SPEC/bundle mudou | evidência nos dados | query | assinatura se fiel | verificab. |
|---|---|---|---|---|---|---|---|
| U1 | Orçamento FE exato | 100/250 FEs fixos (§VII) | 31D−1, hard-stop D21/D61 | ①.fe_index; manifest.fe_final; footer | `len(real)==31*D-1 and real.fe_index.is_unique and man['fe_final']==man['maxfe']` | 31D−1 linhas, fe_index 0..31D−2 sem furo | direta |
| U2 | DoE init 11D−1 do artefato | LHS 11d−1 (Alg.1 l.2) | D63/D88: carregado de `data/doe/`, bit-exato | ①.fase=='init'; manifest.doe_hash | `(real.fase=='init').sum()==11*D-1`; `np.abs(init[xc].values - doe[xc].values).max()` | contagem exata; ΔX ≤ arredondamento float32 (~1e-7); doe_hash == sidecar | direta |
| U3 | Retreino a cada iteração | DACE dentro do while (Alg.1 l.7) | nada | ④ 1 linha/iteração com tempo_fit_s>0; ⑥ modelo_hp por gen | `tim.tempo_fit_s.notna().all(); len(tim)==len(ge)` | nº fits == nº iterações | direta |
| U4 | Cadência da sonda | — (instrumentação nossa) | DI-12.5: g==1 ∨ g%2==0 + última; 2000 pts; hash | manifest.sonda.geracoes; ③ regime='sonda'; ⑥ rec='sonda' | `set(sonda.geracao.unique())=={1}∪{g par}∪{g_final}`; `n_blocos*2000==n_linhas` | blocos nas gens {1,2,4,…}; última geração SEMPRE coberta (mesmo ímpar) | direta |
| U5 | Não-perturbação da sonda | — | invariante 🔴 do CONTRATO §3.1 | exigiria ① de run pareado sem sonda | — | ① idêntica com/sem sonda | **não-verificável** (só re-execução) |
| U6 | q=1 sequencial | 1 ponto/iteração (Alg.1 l.11) | nada | ⑥ lote; diffs de fe | `set(np.diff([e['fe'] for e in ge]))<={0,1}` e `lote==1` | incremento 1 (0 apenas em cache-hit D89) | direta |
| B1 | λ sorteado POR ITERAÇÃO, com reposição, do grid uniforme | Eq.(1); 11/15 vetores (Table V) | **CÓDIGO (D20/D30): N=100 (M=2) / NBI 91 (M=3)** — quebra o racional "várias passadas" (§VII-B) | ⑥ ge[i].lambda (vetor M); ③ transf_params.lambda | `l0=[e['lambda'][0] for e in ge]; max(abs(l0*99-round(l0*99)))` ≈0; `len(set(map(tuple,lams)))` | grid 1/99 (M=2); repetições existem (reposição); N_lambda do manifest = 100/91 | direta |
| B2 | Escalarização PCheby ρ=0,05 | Eq.(2) | nada (ρ=0,05 mantido) | ⑥ gbest + norm_min/max + lambda; ① f | `Fn=(F-nm)/(nx-nm); pc=(Fn*lam).max(1)+.05*(Fn*lam).sum(1); abs(pc.min()-e['gbest'])<1e-6` | gbest reconstruído bate em 100% das gens | direta |
| B3 | Normalização | por limites CONHECIDOS do espaço de custo (§IV) | **CÓDIGO (B1.6): min/max do ARQUIVO, por iteração** | ⑥ norm_min/norm_max; ① acumulado | `real[real.fe_index<fe-1][fcols].min()==e['norm_min']` (idem max) | bate com acumulado PRÉ-infill em 100% | direta |
| B4 | Mono-output (1 GP do escalar) | §IV: DACE sobre f_λ | D47 ratifica (rejeitou M GPs) | ③ mu_1../sigma_1.. ; sigma_dict | `busca.mu_1.isna().all() and busca.sigma_1.isna().all()`; `pred_tipo=='valor'`, `transf_tipo=='escalar-tcheby'` | colunas ≥1 100% NULL (por-desenho, D47 — não bug) | direta |
| B5 | Subset de treino | ½ melhores sob λ + ½ aleatórias, tamanho 11d−1+25 (§IV) | **CÓDIGO: top-(11D−1+25) determinístico + dedup 1e-6** | ⑥ n_subset/n_treino/n_dedup; ④ n_acumulado | `max(e['n_treino'] for e in ge)==11*D-1+25`; `e['n_treino']==e['n_subset']-e['n_dedup']` | satura no cap; curva (n_acumulado, tempo_fit) PLANA pós-cap | direta (o "top" em si é indireta: exigiria re-ranquear ① sob λ e comparar — possível, não executei) |
| B6 | Guard P2 `sqrt(max(mse,0))` | — (DEF-L8, patch nosso 🟠) | D76: obrigatório, logado | ③ sigma_0; ⑥ n_mse_neg | `(busca.sigma_0<0).sum()==0`; `sum(e['n_mse_neg'])` | zero σ negativos; contador loga cada clamp | direta |
| B7 | NaN-guard P4 (objetivo constante) | — (DEF-A8) | patch nosso | ⑥ nan_guard, n_ei_nan | `sum(bool(e['nan_guard']) for e in ge)` | 0 em problemas sadios; >0 dispararia sem crash | direta |
| B8 | GA interno: IFEs=10.000, decremento pós-geração, lote ≈2·\|arquivo\| | pop 20 steady-state 10k evals (§IV) | **CÓDIGO: geracional c/ truncamento elitista; lote 2·\|A\|** | ⑥ ga_iters/ga_pop/n_pool_ga | `all(it*p>=10000>(it-1)*p for it,p in ...)`; `ga_pop-2*n_arquivo ∈ {0,-2}` | ga_iters==ceil(10000/ga_pop) em 100%; ga_pop cresce com o arquivo (74→14→6 iterações internas) | direta |
| B9 | Infill = argmax EI; EI canônico | Fig. 1/§III (forma fechada) | nada | ⑥ mu_best/sigma_best/gbest/ei_best/best_sid; ① | `z=(g-mu)/s; ei=(g-mu)*Φ(z)+s*φ(z); abs(ei-(-e['ei_best']))/ei<1e-6`; `best_sid ∈ real.solution_id` | identidade EI fecha em 100%; best_sid presente no ① | **direta (a query-joia deste config)** |
| B10 | σ entra no EI (aceita-explora) | §III: "automatically balances" | nada | ⑥ sigma_best>0; contrafactual no ③ (pool com μ menor que o escolhido) | por gen: `pool=busca[busca.geracao==g]; (pool.mu_0<mu_best).any()` — escolhidos com μ não-mínimo = incerteza pesou | fração das gens em que argmax-EI ≠ argmin-μ > 0 | direta |
| B11 | Retreino/warm-θ, bounds | NM 20 restarts (Alg.1 l.25), θ livre | **CÓDIGO: boxmin SEM restarts, θ0=10 1ª iter, warm depois, bounds [1e-5,20]** | ⑥ modelo_hp.theta, theta_min/max | `all(1e-5<=t<=20 for t in hp['theta'])` | θ dentro dos bounds (θ=20 saturado aparece — MMF1 ger48) | bounds: direta; warm-start/boxmin: **não-verificável** (trajetória MLE não logada) |
| B12 | Hazard near-dup / mutação-clone | — (K.3/L.1: "Bad parameter region", mse≈0) | guarda dedup_treino + cache_hit D89 | ⑥ guard names; ③ real_solution_id em busca; ② dupes | `guards['dedup_treino']`; `busca.real_solution_id.notna().mean()`; `pop[g==gmax].solution_id.duplicated().sum()` | remoções logadas; clones do pai no pool (MMF1 20% vs ZDT1 0,05%); ② com dupes == cache-hits | direta |
| B13 | Granularidade ③ = POP FINAL do GA interno | — (DEF-C2/bundle I.1) | política "BO com EA interno" | ③ busca rows/gen × ⑥ ga_pop | `busca.groupby('geracao').size() == {g: ga_pop}` | igualdade em 100% das gens | direta |
| B14 | fe_treino_max NÃO-monotônico | — (DI-13.15) | subamostragem do treino | ③ fe_treino_max por gen | `ftm=busca.groupby('geracao').fe_treino_max.first(); (ftm.diff()>=0).all()` | False em D alto (subset), True possível em D=2 | direta |
| B15 | Torneio bugado EvolALG:16 mantido | sem contraparte (GA do paper é outro) | 🟠 CÓDIGO (K.3) — favorece pontos antigos pós-27º treino | — | — | — | **não-verificável** (só código/re-execução) |
| B16 | Calibração do σ escalar | — (análise nossa) | sonda escalar D47 | ③ sonda + artefato + transf_params | reconstrói PCheby do gabarito com λ/min/max do bloco; `mean(abs(mu-pc)<=2*sig)` | cobertura ~0,95 se calibrado; medido: 0,59→0,47 (sobreconfiança tardia — prior confirmado) | direta |

## C. GROUNDING NOS DADOS REAIS (executado)

**Células**: MMF1_42 (D=2, M=2), DTLZ2_42 (D=12, M=3), ZDT1_42 (D=30, M=2); todas `status=ok`, `termino='normal'`, `fallback_ativado=False`, `n_retries=0`.

**Schemas reais (verificados):**
- ①: `algoritmo|problema|semente|solution_id|x0..x{D-1}|f0..f{M-1}|fe_index|fase` — linhas: 61/371/929 = 31D−1 exato ✓; `fe_index` único 0-based ✓; `fase`: init=11D−1 (21/131/329) + opt (40/240/600) ✓; `solution_id` único ✓.
- ②: `algoritmo|problema|semente|geracao|solution_id` — gens 49/241/604; ger 1 = exatamente os ids do DoE ✓; cresce +1/iteração; **última ger tem solution_id DUPLICADOS** (8 no MMF1 — re-adds de cache-hit).
- ③: `…|regime|geracao|x0..|real_solution_id|mu_0..mu_{M-1}|sigma_0..|pred_tipo|pred_classe|pred_score|pred_confianca|modelo_flag|espaco_modelo|transf_tipo|transf_params|fe_treino_max` — rows 54.224/362.000/1.365.176. **`regime ∈ {'online','sonda'}`** (literal `'online'`, não "busca"). `pred_tipo='valor'`, `modelo_flag='GP-DACE'`, `espaco_modelo='transformado'`, `transf_tipo='escalar-tcheby'`; `mu_1../sigma_1..` 100% NULL (D47, por-desenho); `transf_params` = dict `{lambda,min,max,gbest}` ✓.
- ④: `run_id|geracao|n_acumulado|tempo_fit_s|tempo_busca_s|tempo_pred_sonda_s|tempo_geracao_s` — 48/240/603 linhas; `fit+busca ≤ tempo_geracao_s` em 100% ✓; `n_acumulado` satura no cap (46/156/354) ✓.
- ⑥: **chave do evento é `rec`** (não "event"). Tipos: `header`(1), `guard`, `sonda`, `b1_gen`, `footer`(1). Campos do `b1_gen` (36): `ts,rec,geracao,fe,lambda,norm_min,norm_max,gbest,theta_min,theta_max,theta_media,n_arquivo,n_subset,n_treino,n_dedup,ga_iters,ga_pop,e0_trace,ei_best,mu_best,sigma_best,best_sid,lote,n_mse_neg,n_ei_nan,nan_guard,n_pool_ga,modelo_hp,f_best,n_front1,fe_treino_max,tempo_busca_s,tempo_geracao_s,tempo_pred_sonda_s,dist_min_arquivo,tempo_fit_s` — os 3 itens DI-10 (λ vetor, ei_best, n_pool_ga) presentes ✓. `guard.name ∈ {cache_hit, dedup_treino}`. `footer`: `status,fe_final,maxfe,n_geracoes,cache_hits,cp_init,termino` (**o campo é `termino`, não `motivo_parada`**).
- **sigma_dict (íntegra, idêntico nas 3):** `mu_0` = "escalar de Tchebycheff aumentado (rho=0.05) PREDITO pelo GP mono-output — LOSSY (D47): nao des-agrega em mu por objetivo; reais por-objetivo via real_solution_id → ①"; `sigma_0` = "sqrt(max(mse,0)) do GP mono-output do escalar (guard P2/L8) — regua muda por iteracao (o lambda muda); interpretar com transf_params"; `transf_params` = "{lambda, min, max, gbest} da iteracao (C3/D47) — obrigatorios p/ interpretar mu_0/sigma_0".
- **Manifest**: tem bloco `sonda` rico (artefato, x_hash/f_hash, S=2000, k=2, n_blocos, n_linhas, n_falhas=0, lista `geracoes`) + `fit_series` + `params` com toda a config efetiva (N_lambda 100/91/100, IFEs 10000, rho, dace, theta0, bounds, mle, subset, normalizacao, ga_interno).

**Contagens-chave e resultados de query (tudo executado):**
- Sonda: 25/121/303 blocos ×2000 pts; gens {1,2,4,…}; **ZDT1 fecha na ger 603 (ÍMPAR) → finalProbe funciona** ✓; join posicional provado: max|X_sonda−X_artefato| = 1,19e-07 (arredondamento float32) ✓; artefato tem 20.000 linhas (fatia online = 2000 primeiras) ✓; `fe_treino_max` preenchido nos blocos (20,21,23,25,… no MMF1).
- B2/B3: `gbest` == min PCheby do arquivo PRÉ-infill em 48/48, 27/27, 26/26 gens amostradas; `norm_min/max` == min/max acumulado do ① PRÉ-infill em 100% (pós-infill falha — desambigua o timing do fit).
- B9: **identidade EI fechada bate em 891/891 iterações (erro relativo mediano 0,0)** — `-ei_best = (gbest−mu_best)Φ(z)+sigma_best·φ(z)`. `best_sid` presente no ① (spot-check ok). ⚠ `ei_best` é NEGATIVO (PlatEMO minimiza −EI): `ei_best == min(e0_trace)` em 100%; **`e0_trace` NÃO é monotônico** (subidas em 42/48, 230/240, 522/603 gens; maior subida 0,017) — é o best −EI da POPULAÇÃO CORRENTE por geração interna, não best-so-far; `ei_best ≠ last(e0_trace)` em ~35–70% das gens. Protocolo NÃO deve exigir monotonicidade.
- B8: `ga_iters == ceil(10000/ga_pop)` em 891/891 ✓; `ga_pop − 2·n_arquivo ∈ {0,−2}` exatamente meio-a-meio (24/24, 120/120, 302/301); ga_iters cai 74→14→6 com D.
- B5: n_treino max = cap exato (46/156/354); gens no cap: 17/48, 143/240, 158/603; `n_treino = n_subset − n_dedup` ✓ (ZDT1 ger603: 354−9=345).
- B6/B7: `sigma_0` min = 2,2e-4 / 4,6e-4 / **5,15e-9** (ZDT1 — quase-zero, hazard do clone visível); zero negativos, zero exatamente 0; `n_mse_neg = n_ei_nan = nan_guard = 0` nas 3 células (guardas instaladas, nunca dispararam).
- B12: guards `dedup_treino`: 6/77/423 eventos (Σ n_dedup por gen = 18/867/2571 — a dupe re-conta a cada fit); `cache_hit`: 9/1/4 == manifest.cache_hits ✓; incrementos de fe {0,1} com n(0) = 8/0/3 (o cache-hit restante ocorre no init); `real_solution_id` não-nulo na busca: 832/4224 (19,7%!) MMF1 vs 181/120.000 DTLZ2 vs 354/759.176 ZDT1 — clones do pai dominam em D baixo; `dist_min_arquivo` min = 0 (infill idêntico a arquivado = iteração cache-hit).
- B13: busca rows/gen == ga_pop em 48/48, 240/240, 603/603 ✓ (granularidade = pop final do GA interno, confirmada).
- B14: `fe_treino_max` monotônico no MMF1 (True — arquivo < cap quase sempre), NÃO-monotônico em DTLZ2/ZDT1 ✓ DI-13.15.
- B16: reconstrução do gabarito ESCALAR executada (MMF1): ger1 corr=0,42, WAPE=0,37, cobertura-2σ=0,59; ger48 corr=0,28, WAPE=0,55, **cobertura-2σ=0,47** — bate o prior "sobreconfiança tardia ~0,5".
- B1: grid λ: `λ0·99` inteiro (desvio máx 9,9e-5) em M=2; distintos 44/48, 84/240 (N=91), 100/603 (todos os 100 visitados; máx 13 repetições) — sorteio COM reposição ✓.

**Surpresas contrato×dado (para o protocolo):**
1. ⑥ usa `rec` como chave de evento e `termino` no footer (não "motivo_parada" — a triagem D-B1 deve ler `footer.termino` + `status` do manifesto).
2. ③ regime literal = `'online'` (contrato escreve "busca…" genérico).
3. **OFF-BY-ONE estrutural**: manifest `n_geracoes` (49/241/604) = gens do ② (inclui ger1=DoE puro); `b1_gen`/④/blocos de busca têm N−1 (48/240/603). ② ger g = arquivo ANTES da iteração g.
4. ② contém solution_id duplicados na mesma geração (cache-hit re-add) — reconstrução de arquivo exige dedup por solution_id.
5. `aritmética de iterações: n_iter = n_infills(opt) + cache_hits − 1` nas 3 células (um cache-hit cai no init).
6. `e0_trace` não-monotônico e `ei_best` negativo (ver B9) — assinaturas corretas, mas contraintuitivas.
7. `modelo_hp` é rico (θ vetor completo, n, sigma2, regr, corr, tempo_fit) — mais que o mínimo B1.

## D. SETUP EXPERIMENTAL DO PAPER

**Suite**: 9 funções, d=2–8, M=2–3, TODAS versões próprias/modificadas ("a"): KNO1 (d=2,M=2, própria), OKA1 (d=2,M=2), OKA2 (d=3,M=2), VLMOP2 (d=2,M=2), VLMOP3 (d=2,M=3), DTLZ1a (d=6,M=2, g com 2π em vez de 20π), DTLZ2a (d=8,M=3), DTLZ4a (d=8,M=3, α=100), DTLZ7a (d=8,M=3). **Protocolo**: 21 runs; cortes a 100 e 250 FEs (NSGA-II 260); init LHS 11d−1; baseline NSGA-II pop 20 (KANGAL) + random search 10k. **Métricas**: S-measure/HV com bounding point b_j = max_j + 0,01·(max_j−min_j) do superset agregado; epsilon-indicador binário aditivo (mediana+IQR); attainment surfaces (mediana/pior); Mann–Whitney 99%.

**Números (S-measure, média(SD), ParEGO × NSGA-II):**
- 100 FEs (Tab. VI): KNO1 94,54(7,28)×87,71(8,28) · OKA1 16,97(0,36)×14,14(1,25) · OKA2 22,22(0,89)×15,51(1,43) · VLMOP2 0,3200(0,0056)×0,2636(0,0387) · VLMOP3 46,39(0,16)×34,87(12,58) · DTLZ1a 189262(209)×186855(1943) · DTLZ2a 4,4078(0,0906)×4,0687(0,1730) · DTLZ4a 0,673(0,264)×0,825(0,409) [sem vencedor] · **DTLZ7a 12,99(0,66)×16,90(1,01) [NSGA-II vence >99%]**.
- 250/260 FEs (Tab. VII): KNO1 108,48(5,84)×103,2(7,93) · OKA1 18,08(0,37)×15,98(0,68) · **OKA2 24,03(0,47)×19,13(1,45)** · VLMOP2 0,3128(0,0040)×0,3050(0,0120) · VLMOP3 89,93(0,11)×83,10(18,84) · DTLZ1a 64869,6(7,0)×64682,7(154,8) · **DTLZ2a 4,4620(0,0277)×4,0755(0,1460)** · DTLZ4a ~2,142(0,478)×1,426(0,810) [extração parcialmente embaralhada — conferir no PDF] · DTLZ7a 15,84(0,43)×13,65(0,93). Traço-assinatura: SD do ParEGO ordens de magnitude menor (pior-caso melhor). Epsilon (Tab. IX): OKA2 mediana negativa (−0,0001) = estritamente melhor em >50% dos runs. Nota d=8/100FEs: LHS de 87 consome 87% do orçamento ("only chosen 13 of 100").

**Interseção com os NOSSOS 25 (orçamento 31D−1) — veredito por problema:**

| nosso problema | contraparte no paper | veredito |
|---|---|---|
| DTLZ1 (D=7, M=3, 216 FEs) | DTLZ1a (d=6, **M=2**, g modificado 2π, 100/250 FEs) | **incomensurável**: M difere (3×2), g modificado; d e orçamento na mesma ordem |
| DTLZ2 (D=12, M=3, 371 FEs) | DTLZ2a (d=8, M=3, 250 FEs) | **quase-comparável (a melhor ponte que existe)**: mesma família e M; diverge d (+50%: 12×8 ⇒ k=10×6) e orçamento (371×250, mesma ordem). Comparação DIRECIONAL válida (ParEGO≫NSGA-II esperado), numérica não |
| DTLZ3 (D=12) | — | incomensurável (ausente no paper) |
| DTLZ4 (D=12, M=3) | DTLZ4a (d=8, M=3, α=100) | eixo-d idem DTLZ2; e a nossa célula DTLZ4_42 FALHOU (least squares underdetermined — já inventariada) |
| DTLZ7 (D=22, M=3, 681 FEs) | DTLZ7a (d=8, M=3, 250 FEs) | **incomensurável**: d 2,75×, orçamento 2,7×; mas o CASO DE ESTRESSE do paper (NSGA-II vence a 100 FEs) merece checagem qualitativa da trajetória |
| MMF1/4/11_L (D=2, 61 FEs) | nenhum; KNO1/OKA1/VLMOP2 são d=2, M=2 | incomensurável por função; MAS d=2/61FEs é o regime mais próximo do paper (100 FEs, d=2–3) — é onde o "comportamento-ParEGO" (DoE 34% do orçamento, EI decisivo) deve aparecer mais parecido |
| ZDT1/3 (D=30), ZDT4/6 (D=10), BBOB (D=10), WFG (D=22), MMF16_20 (D=20) | — | **incomensuráveis**: fora do envelope do paper ("up to eight dimensions", §I) — D=30 é 3,75× o máximo testado; extrapolação declarada |

Nota estrutural: nosso desenho mantém fração DoE/orçamento constante ((11D−1)/(31D−1) ≈ 35%) — o paper a 100 FEs/d=8 tinha 87%; nossa configuração é mais generosa com a fase de infill do que o pior caso do paper.

## E. O QUE O AGENTE-4 ACRESCENTA

**Acréscimos reais do `b1_full.md`:** (i) parâmetros do GA interno consolidados e legíveis (pop 20, steady-state, torneio binário s/ reposição, SBX p=0,2, mutação shift, init 5 mutantes+15 LHS) — a extração markdown do PDF mutila essa lista; (ii) a regra do subset (todas se iter<25; senão 11d−1+25 ½/½) explicitada com números; (iii) leitura G5 do papel do σ (contrafactual: sem σ o EI degenera em busca gananciosa) — vira o aspecto B10; (iv) genealogia (qParEGO/MOEA/D-EGO) e status do código oficial (link UMIST morto → PlatEMO canônica por mantenedores); (v) motivação GC-MS e as 9 features do regime; (vi) nota "10 000 (até 200 000 nas execuções)" — registra a inconsistência texto×Table V do paper.

**Contradições/imprecisões detectadas:**
1. **agente-4 §3.1 diz "Tabela V mostra s=11 para k=2 e s=15 para k=3"** — errado: 11/15 é |Λ| (nº de VETORES), não o parâmetro s (s=10 e s=4 geram 11 e 15 vetores). O bundle (DEF-B1.1) lê certo: "paper usa 11/15 vetores λ".
2. **agente-4 §3.1/§3.4 diz "matriz capada em 80" para o ParEGO** — o cap 80 é do EGO (§III-A); ParEGO usa "a slightly more advanced selection procedure" com teto 11d−1+25 (que passa de 80 para d≥6). O M.1 do bundle mistura os dois no mesmo fôlego ("o cap=80 e o subset ½/½ são concessão aos 21 runs") — a citação do autor é correta, mas o número 80 não é o cap do ParEGO.
3. agente-4 afirma "10.000 avaliações" como canônico com parêntese "(até 200 000)"; o bundle crava "10k ✓ (Tab. V diz 200k — inconsistência do paper)" e o código usa 10k — coerentes entre si, mas o protocolo deve citar a inconsistência ao defender IFEs=10.000.
4. agente-4 §3.2 "MLE via Nelder-Mead 20 restarts" descreve o paper; nossos dados/manifesto declaram "boxmin SEM restarts (CODIGO)" — não é contradição, é a divergência D30 JÁ classificada (🟠 periférica); citar sempre o manifest.params.mle como fonte da verdade do implementado.

## F. PROPOSTAS PARA O PROTOCOLO PADRONIZADO

**(i) Generaliza para os 24 configs:**
- **Ordem de leitura fixa**: manifest (status+params+`sigma_dict`+bloco sonda) → header/footer do ⑥ (chave `rec`; parada = `footer.termino`+`status`, NUNCA `status` do despachante sozinho — bug B1) → schemas das camadas → só então queries.
- **Bateria universal U1–U6** (executável tal qual em qualquer config): 31D−1 exato + fe_index único; init == 11D−1 e ΔX vs artefato DoE ≤ float32-eps; 1 fit/iteração no ④; cadência da sonda pela FÓRMULA g==1∨g%k==0 + checar que a ÚLTIMA geração tem bloco (o caso ZDT1 ger 603 ímpar prova o finalProbe — teste discriminante); fit+busca ≤ tempo_geracao em 100%; incrementos de fe ∈ {0,q}.
- **Queries reutilizáveis**: (a) join posicional sonda↔artefato com prova de ordem (max|ΔX|); (b) `fe_treino_max` para separar in/out-of-sample; (c) contadores de guard do ⑥ == agregados do manifesto (cache_hits); (d) reconciliação ②×①×cache_hits (com dedup por solution_id no ②); (e) curva (n_acumulado, tempo_fit_s) do ④.
- **Aritmética de alinhamento**: documentar por config o offset ②(N+1)×⑥/④(N) e a regra `n_iter = n_infills + cache_hits − c0`; comparações entre configs SEMPRE por fe (regra 6 do R4).
- **Formato do achado**: cada aspecto = {prescrição+ref do paper, decisão D-xx que a alterou, query, valor medido, veredito} — a tabela B acima é o template.

**(ii) Específico da FAMÍLIA (GP-regressor mono-output / BO-decomposição — b1 e primos):**
- Ler `sigma_dict` ANTES de tocar o ③ é literalmente obrigatório aqui: `mu_0` não é um objetivo, é o escalar; `mu_1..` NULL é desenho (D47), não bug.
- A **régua do escalar muda por iteração** (λ, min/max): toda análise de erro/calibração exige reconstruir o gabarito com `transf_params` do PRÓPRIO bloco (query B16); jamais comparar mu_0 entre gerações sem re-escalarizar; b1 compara-se À PARTE dos multi-output (regra 4 do R4).
- **A query-joia da família BO**: identidade fechada da aquisição — aqui EI(mu_best, sigma_best, gbest) == −ei_best fechou em 891/891. Para c262/c154 (qLogNEHVI) o análogo é acqf dos restarts; para e81, os draws de Thompson. Onde a identidade fecha, o "uso da incerteza" está PROVADO sem código.
- Verificações de decomposição: grade de λ (1/(N−1) ou NBI), reposição, cobertura do conjunto; `gbest` reconstruível do ① (prova que a escalarização opera sobre o arquivo declarado).
- Granularidade ③ = pop final do otimizador interno: validar rows/gen == n_pool_ga (aqui 100%); atenção que para c149/e81 a DI-24 manda rank-0, não pop cheia — conferir o sigma_dict de cada um.

**(iii) Armadilhas para um agente fresco NESTE config:**
1. Tratar `mu_0` como f0 predito e "descobrir" um erro gigante vs f0 real — é o escalar PCheby.
2. Exigir monotonicidade do `e0_trace` (não é best-so-far; sobe em ~87% das gens) ou estranhar `ei_best<0` (é −EI minimizado).
3. Usar `n_geracoes` do manifesto para indexar ⑥/③/④ (off-by-one; ② tem uma geração a mais).
4. Interpretar 423 eventos `dedup_treino`/2571 remoções acumuladas no ZDT1 como bug — é o hazard near-dup OPERANDO (a mesma dupe re-conta a cada fit).
5. Esperar `fe_treino_max == fe−1` (subamostragem: não-monotônico, DI-13.15) ou n_treino == n_subset (dedup desconta).
6. Julgar a curva de fit "suspeita de não crescer" — n_acumulado satura no cap top-(11D−1+25) POR DESENHO.
7. Comparar σ do b1 com σ multi-output dos outros configs na mesma régua (estruturalmente incomparáveis).
8. Procurar 11/15 vetores λ (paper) e reprovar os 100/91 do código — divergência D20/D30 já sancionada; idem boxmin vs NM-20-restarts, subset top vs ½/½, GA geracional vs steady-state e torneio bugado (K.3: fica).
9. Contar `guard cache_hit` como FE ou esperar linha no ① (D89: 0 FE, sem linha; mas o ② GANHA membro duplicado).
10. Recalcular a normalização com min/max PÓS-infill (o fit é pré-infill — 100% vs falha).

**(iv) TETO de verificabilidade honesto (exige código/re-execução, não os dados):**
- **Torneio bugado (EvolALG:16)** e seu viés pró-pontos-antigos pós-cap: nenhum rastro no ③/⑥ (genealogia de pais foi rejeitada no DI-10 como patch invasivo).
- **Miolo da MLE**: warm-start de θ, θ0=10 na 1ª iteração, boxmin sem restarts — só o θ FINAL é logado (`modelo_hp.theta`); a trajetória e o critério de parada da MLE são invisíveis.
- **Operadores internos do GA** (SBX/PM efetivos, seleção): só o efeito agregado (pool final + e0_trace); a mecânica geração-a-geração interna não é reconstruível.
- **Não-perturbação da sonda** (invariante 🔴): exige run pareado com/sem sonda comparando o ①.
- **Contabilidade de RNG** (1 randi λ + 2×randi torneio + …): não-verificável sem instrumentar o gerador.
- **Dupla-escala do patch D94 (P1)**: o ① init dentro dos bounds nativos + ΔX≈float32-eps vs artefato é evidência forte, mas a prova de que a :30 "nunca roda" é do código.
- **Predições intermediárias do GA interno**: o ③ grava só a população FINAL por iteração — as ~10.000 avaliações de EI por iteração são irrecuperáveis (o contrafactual greedy-μ só é computável sobre o pool final).
- Limitação inerente D47 (irremediável por qualquer análise): candidato nunca-avaliado não tem μ/σ por objetivo — o "erro de fantasia" por objetivo do b1 só existe para os pontos que viraram FE real (join `real_solution_id`→①).