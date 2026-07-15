# Rodada 3 — contrato transversal standalone (Python; offline + BO de autor)

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

**Decisões-chave:** D77 (**piso offline = DESDEO mode 12, GP-média = b5-sem-σ**; a listagem PlatEMO morreu) · D56 (b5 = 2 configs `b5r`/`b5m`) · D78 (**fallbacks pré-registrados**: c311→treed/sparse-GP substituto 'author-modified'; c149→best-effort, senão narrativa repousa no c311 + nota BNN futuro; flag `fallback_ativado`) · D68 (ND final SEM cap — salvar completo) · D62 (SeedSequence; base=1000·semente p/ e81/c149 — D22) · D79 (venv PRÓPRIO por repo; b5×c311 NUNCA co-importados — N.1.2) · **D86 (higiene torch por iteração no c149 — N.1.5)** · D54 (e81/c149/c122 bucket-only).

---

### 22.4 Rodada 3 — standalone de implementação própria (uma sub-rodada cada, nesta ordem)


**Piloto da Rodada 3:** por sub-rodada (o gate é por algoritmo); offline (b5/c311) fecham o regime offline com o e103 da Rodada 1; a série §17.6 do c311 no **sweep big** é o espelho offline do achado (§11.5).

---

### N.1 — Contrato transversal Python (fan-out por processo)
1. **`torch.set_num_threads(1)` em TODOS os stacks torch** (c122, c149, c262, c154, e81): nenhum repo o faz, e vários abrem `device='cuda'` **sem índice** (c122:100, c149 Forward_BNN:29/40) → em CPU cada processo usa todos os cores (oversubscription no grid); em nó com GPU todos pegam `cuda:0`. Fixar CPU + threads=1 + float64.
2. **⚠ Colisão de pacote vendorizado (offline — o pior achado):** b5 e c311 vendorizam `desdeo_emo`/`desdeo_problem`/`desdeo_tools` com **mesmo nome e código diferente** (b5: ProbRVEA/ProbMOEAD/SurrogateKriging; c311: OfflineRVEA/treedGP/FullGP). `sys.modules` cacheia o 1º importado → **co-importar b5 e c311 no mesmo processo usa DataProblem/RVEA ERRADOS sem erro**. Os `sys.path.insert` são hard-coded para paths do autor (`amrzr`, inexistentes aqui) → a resolução cai para o cwd. **Regra: isolar b5 e c311 em processos/venvs distintos, sempre; nunca co-importar.**
3. **Seeds globais re-semeados:** `pymoo.minimize(seed=·)` re-semeia `np.random`/`random` GLOBAIS (e81, c149, e o NSGA-II interno de vários) → **salvar/restaurar o estado do RNG numpy em volta de cada chamada** e usar um `np.random.Generator` próprio para o DoE, imune ao reset.
4. **Sem `makedirs(exist_ok=True)`:** b5/c311 (e c149) criam diretórios de saída sem `exist_ok` e logam em arquivo nomeado por `str(datetime.now())` (com espaços/`:`) compartilhado por todos os workers → TOCTOU + nomes inválidos. O nosso harness escreve o export (§17), não os drivers dos autores.
5. **[D86/v5.1] Higiene de memória nos loops torch (c149 sobretudo; e7/c122 por extensão):** `torch.no_grad()` em TODA predição; ao fim de **cada iteração** do loop de retreino, `del` dos tensores intermediários + `gc.collect()` (+ `torch.cuda.empty_cache()` quando houver GPU) — nenhum tensor de iterações passadas retido (o export grava e solta). Sem isso, o retreino-por-FE do c149 (D43) acumula grafo/tensores ao longo de centenas de FEs → OOM no MEIO do run (dado perdido; o D60 só mata). O piloto mede o pico de RAM (§22.5).

---

## 7. Tamanho do dataset fixo — [DECIDIDO: `31D−1`]
Dataset offline = **`31D−1`** por LHS — **igual ao orçamento total de avaliações verdadeiras do online**.

**Justificativa (corrigida com base na literatura, ver nota):** dar só `11D−1` (o padrão DDEA, usado por e103/f9/b13, que o chamam explicitamente de "o padrão") seria **injusto no confronto cross-regime**: o online já tem a vantagem da **aquisição ativa** (escolher quais pontos avaliar); se também visse *mais* pontos verdadeiros no total, empilharia duas vantagens e não se saberia qual causou a diferença. Igualando o **total de avaliações caras** (`31D−1`) — que é o recurso que custa —, a única diferença entre regimes vira a **adaptatividade**, que é exatamente o que a comparação online×offline deve isolar. Como `11D−1` é justamente o **DoE inicial do online**, os dois regimes **partem do mesmo tipo de amostra**, e o online apenas ganha o direito de consultar 20D pontos a mais — a comparação mede o **valor da aquisição ativa**.
> *Nota de honestidade:* `11D−1` é o padrão de quem estuda offline **isolado**; `31D−1` é o **principiado** para o confronto justo online×offline (não é uma convenção da literatura, é uma escolha de desenho fundamentada). Além disso, `31D−1` > `11D−1` **ajuda o c311** (big-data), que sofreria em dataset pequeno. *(Histórico das duas correções que geraram esta decisão — Anexo G.3.)*

**[v5.2 — D90] O dataset offline é um ARTEFATO persistido, análogo ao DoE (estende D63/D87).** `data/datasets/{problema}/ds_{problema}_{semente}[_{tier}_{dist}].parquet` — colunas `x0…x{D−1}, f0…f{M−1}`, float64 —, gerado **uma vez, no env da ponte** (Python; o F sai do `problems.py` canônico), com **SHA256 do array decodificado** no manifesto. **e103 (MATLAB), b5r/b5m e c311 (venvs) e o piso apenas CARREGAM** — o pareamento cross-stack exigido pelo §9 (o e103 é MATLAB; b5/c311 são Python) vale **por construção**, exatamente como o D63 resolveu para o DoE online. **Derivação da semente do gerador SEM `alg_id`** — `SeedSequence((semente, problema_id, tier_id, dist_id))` — para que os 4 configs offline + piso recebam **o MESMO dataset** da semente k (usar `alg_id` aqui quebraria o compartilhamento silenciosamente). O sweep (§11.5) materializa seus datasets (tiers `medium`/`big`; distribuição MVNS — D67) pela **mesma convenção**. Tier `big` (50k): LHS **simples** (D87 — maximin inviável nesse n).

## 8. Amostragem do dataset — [DECIDIDO: LHS]
Latin Hypercube. Padrão nos papers offline (e103, f9), mesma família do DoE do online (reforça a comparação cross-regime), reprodutível. **Respaldo empírico do autor:** experimento próprio comparando métodos de amostragem (aleatória × LHS × Sobol) confirmou o LHS → documentar na dissertação (parágrafo + tabela em apêndice) como decisão **embasada em dado**, não em convenção.

## 9. Sementes e dataset — [DECIDIDO: dataset novo por semente]
Cada uma das 30 sementes gera um **dataset LHS novo** de `31D−1` pontos (não um dataset fixo). **[v5.2 — D90] Mecanismo: o artefato persistido do §7** — um único arquivo por `(problema, semente[, tier, dist])`, compartilhado por **todos** os configs offline; nenhum config regenera dados. **Justificativa:** no offline, o dataset **é** a variável de risco — o algoritmo aposta tudo nele, sem poder corrigir com avaliações reais. Medir a **robustez a qual dataset foi recebido** é a questão central do regime (o e103 examina isso no material suplementar; é a convenção DDEA). **Pareamento preservado:** todos os algoritmos offline (e o piso) compartilham o **mesmo dataset da semente k**.

## 10. Surrogate do piso offline — [DECIDIDO: GP-média]
O piso treina um **GP (Kriging)** no dataset e otimiza sobre a **média** — **mesma família dos 3 viáveis** (todos GP). Isola *uma* variável (usar σ vs só a média); RBF/NN introduziria uma segunda diferença (família do modelo) e poluiria o isolamento.
- **Ajuste no tier big-data (~50k):** o GP padrão não treina (parede O(n³)); **só nesse tier** o piso usa **treed-GP-média**, mantendo o conceito "GP-média" e a presença do piso em todos os tiers.

## 11. Orçamento interno do MOEA + avaliação final — [DECIDIDO]

**Orçamento interno** (MOEA rodando sobre o surrogate — avaliações no modelo, de graça): **default do autor** para cada algoritmo, em suas próprias unidades (não equiparado — cada um converge no seu ritmo):

| Algoritmo | Motor interno | Orçamento interno (default do código, corroborado no paper — [CORRIGIDO v2.1]) |
|---|---|---|
| e103 (IBEA-MS) | IBEA | **10.000 avaliações-surrogate** = 100 gerações nominais × pop 100 (paper §IV-4; o código executa 99 — off-by-one documentado) |
| b5 (Prob-MOEA/D & Prob-RVEA) | RVEA / MOEA/D | **40.000 avaliações-surrogate** (paper FE_max ✓) + S=1000 amostras MC/indivíduo |
| c311 (TGPR-MO) | RVEA | **Construção** (= treino do surrogate, parte do método): `Imax = N/(10D)` iterações (float → executa ⌈Imax⌉) × 50 gerações, com early-stop **[re-lido v2.2]**: para quando o nº de soluções em folhas SEM GP não cresce por 2 iterações (mínimo de 6 iterações) — **implementa ≈ o critério do paper** ("todas em folhas com GPR") com persistência; B15.8 rebaixada a nuance + **otimização final**: 10 iterações × 100 ger = 1.000 gerações (vetores adaptados no início de cada iteração). ⚠ O "1.500 ger (50×30)" das versões anteriores estava **errado** — sem base no paper nem no código |
| **Piso** (MOEA/D-média) | MOEA/D | **40.000 avaliações-surrogate** (ancorado no b5) |

**Piso ancorado no b5 (40k):** porque piso-MOEA/D vs Prob-MOEA/D com o **mesmo orçamento interno** é a ablação cirúrgica (única diferença = seleção probabilística).

**Avaliação final [DECIDIDO]:** o algoritmo termina com uma frente aproximada *no surrogate*; o **conjunto não-dominado final** é avaliado na **função verdadeira uma única vez** (a única chamada real no offline), e as métricas são computadas sobre ele. Revela o "erro de fantasia" do surrogate (soluções ótimas no modelo, ruins na verdade). Padrão do offline data-driven.

---

### E.9 — Offline (b5, c311 DESDEO · e103 standalone MATLAB) [ENRIQUECIDO v2.1]
- **Harness offline próprio:** gerar dataset LHS `31D−1` por (problema, semente) **no env da ponte** (pymoo moderno — os envs DESDEO usam pymoo antigo; injeta-se X,F como arrays, DEF-D1) → treinar surrogate → MOEA interno (orçamentos §11 corrigidos) → avaliar o não-dominado final 1× na verdade → export 2 camadas.
- **b5 [CORRIGIDO v2.2]:** wrapper `run_optimizer_ours(X,F,bounds,mode,seed)` bypassando `read_dataset` (bounds hard-coded por testbench com UnboundLocalError p/ nomes novos); **modos: 7 (Prob-RVEA-v3 = média do APD amostrado — aproximação NÃO publicada, declarar) e 72 (Prob-MOEAD = P_wrong via MC pareado — QUASE-FIEL ao paper: troca só o KDE pela CDF empírica de amostras, coisa que o próprio paper sanciona)**; ⚠ patch obrigatório no 72: comentar o **bloco 66–75** do ProbMOEAD_select.py (KDE morto + plt_density); B18.8 ✓ rampa θ existe (passar sempre FE_total=40000 — ZeroDivision se 0); B18.9 ✗ pop inicial = LHS novo (diverge do Alg. 1 L2 do paper — declarar); ⚠ **mode 7 tem adapt() dos RVs COMENTADO** (RVs fixos; modes 12/72 adaptam) — assimetria a documentar; seeds np+random ANTES do `problem.train` (o GPR usa n_restarts=9 no RNG global); snapshots: modes 12/72 já arquivam a pop completa por geração; mode 7 arquiva só offspring pré-seleção (mini-patch); piso = mode 12 pronto; env §18.6 (⚠ locks conflitam — fixar no piloto). Receita completa: Anexo L.16.
- **c311:** env §18.7; **ignorar o testbench MATLAB/DBMOPP**; orçamentos reais na §11; early-stop código≠paper documentado (B15.8); patch do σ nas folhas (`sqrt(var_GPy)` + NaN nas sem-GP) = **extensão nossa** — o paper anuncia e nunca consome σ (ponto narrativo para a dissertação); piso big = classe `treeGP` sem `addGPs` (B15.4 ✓); Imax explode em D baixo/N grande (N=50k, D=2 → 2500 iterações máx) — logar Imax efetivo e nº de GPs construídos.
- **e103:** **standalone** (`IBEAMS(Global)` struct própria — FATO B7.1) → wrapper MATLAB próprio casado ao harness offline; adaptar centros RBFN p/ ⌈√(31D−1)⌉ (fórmula do paper é função do dataset — B7.2 ✓); pm=1/D² é bug confirmado (decisão K.3); Kriging trend (regpoly0×1) e KFlag sticky×stateless e init-pop dataset≠N=100: verificar no código (B7.7–7.9); front final: avaliar os 100 finais e filtrar pós-real (B7.5 ► — harmonizado com a convenção offline uniforme).
- **Piso offline (MOEA/D-média):** implementação própria fina — **mesmo motor do b5** (mode 12 do próprio repo é o candidato natural) sobre GP-média; 40k avaliações-surrogate; piso small/medium = SurrogateKriging do DESDEO com σ ignorado (máxima comparabilidade com b5 — DEF-E3).
