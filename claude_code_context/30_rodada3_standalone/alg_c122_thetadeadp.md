# c122 θ-DEA-DP (autor, Python/torch+DEAP)

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

**Específicas:** f_min/f_max dos fronts VERDADEIROS pela ASSINATURA (vantagem informacional DECLARADA — D73b); driver próprio bypassa o factory (env encolhe — S.8); cap anti-spin (fork do main loop); **bucket-only (D54)**; stub do visualizer.

---

- [ ] **3.1 · c122 θ-DEA-DP** *(I.6, L.6, N.2.5)* — **DEF-B11.1 (patch obrigatório e fiel ao paper): fixar `f_min/f_max` por problema** — formalizar os **25 pares** no harness (fronts verdadeiros/nadir + margem) e entregá-los **pela assinatura** de `scalar_dom_ea_dp` (sem tocar o core). Adapter: objeto `n_var/n_obj/xl/xu/name` + `evaluate(lista de Individuals)→(N,M)`; driver = fork do `tdeadp_main.py` (CPU). ⚠ `pymop`/`optproblems`/`autograd` são **imports duros** — satisfazer ou cortar `problems/wfg.py`; rodar com `cwd=examples/` **e** `PYTHONPATH=raiz` (N.2.5). x normalizado [−1,1]; **cap anti-spin** (fork do main loop — retries geram 7000 offsprings sem FE); T′=min fica (🟣 CÓDIGO). Determinismo: `random.seed`+`np.random.seed`+`torch.manual_seed`+`use_deterministic_algorithms(True)`+threads=1; `creator` DEAP + PerCounter **novos por run**; matplotlib instalado (import duro). Gate warm-start `acc≥0,9` (edge: 0,9 exato → zero épocas). Export: softmax do escolhido + agregados por categoria + accs (C1). FE exato; custo D=30 ~1,25e5 pares/época ×≤20 ×2 redes — medir.

---

| c122 | N (vetores decomposição / pop) | Específico | 11 (M=2) / 15 (M=3) | D20 (estrutural); paper ✓ | Nº de vetores Das-Dennis = subproblemas/pop; fixa a malha de decomposição |
| c122 | Operadores GA | Específico | SBX proC=1,0/disC=30; PM proM=1/n/disM=20 | código oficial (Balde B); paper Tab.III ✓ | Reprodução; disC=30 → filhos colados aos pais (busca fina) |
| c122 | Pool de candidatos N* | Específico | 7000 | código oficial | Candidatos gerados/iteração p/ o classificador filtrar (varredura ampla) |
| c122 | Infill por iteração | Específico | 1 | código oficial; paper ✓ | Só o melhor candidato do pool é avaliado de fato (1 FE/iter) |
| c122 | Arquitetura FNN | Específico | 2×200 ReLU (softmax só na inferência) | código oficial; paper Tab.III ✓ | Classificador de θ-dominância; softmax só na inferência |
| c122 | Adam lr / batch / wd | Específico | 1e-3 / 32 / 1e-5 | código oficial; paper ✓ | Treino do classificador |
| c122 | E_init (épocas) | Específico | 20 | código oficial; paper ✓ | Épocas do 1º treino (do zero) |
| c122 | T_max (re-init) | Específico | 11n+24 (re-init treina no arquivo INTEIRO) | código oficial | Orçamento de épocas do re-treino; erratum T′ usa MIN ✓ |
| c122 | Gate do warm-start | Específico | acc ≥ 0,9 | código oficial (hazard de borda) | Se acc≥0,9 pula o treino (acc=0,9 exato → zero épocas) |
| c122 | γ / Q_max / θ_PBI | Específico | 0,9 / 300 / 5 | código oficial; paper ✓ | Coef. de atualização (0,9); buffer de treino (300); penalidade angular PBI (5) |
| c122 | Normalização de x | Específico | [−1, 1] | código oficial | Escala as variáveis antes da FNN |
| c122 | Normalização f_min/f_max | Específico | fixos por problema (patch) | fidelidade (patch obrigatório → paper) | Fixa f_min/f_max; o código com 0/1 implícito viola o paper — patch obrigatório |
> **Notas.** Toda a Tab. III do paper confere. `survival` trunca o front excedente por `random.sample` → CÓDIGO (D30, mantido). Predição simetrizada (2 direções, vence maior softmax). Único patch obrigatório: f_min/f_max (senão a normalização 0/1 distorce os objetivos).
| c122 θ-DEA-DP | torch 2.x CPU; SBX 1.0/30 + PM 1/n/20; pool N*=7000; FNN 2×200 ReLU (logits-3; ⟦v2.2⟧ softmax só na INFERÊNCIA — treino = CE sobre logits); Adam lr=1e-3, B=32, wd=1e-5; E_init=20; T_max=11n+24 (⟦v2.2⟧ janela SÓ no update; **re-init treina no arquivo INTEIRO**); ⟦v2.2⟧ gate do warm-start é **`>=`** (acc=0.9 exato → zero treino); γ=0.9; Q_max=300; θ_PBI=5; 1 FE/iteração; ⟦v2.2⟧ **survival trunca o front excedente por `random.sample`** (SEM crowding/SPEA2); x normalizado p/ [−1,1] na entrada das redes; predição simetrizada (2 direções, vence o maior softmax); f_min/f_max entram pela **assinatura** de `scalar_dom_ea_dp` (patch sem tocar o core) | Tab. III ✓ todos; N do paper: 11/15 ✓; init conta ✓; **normalização: patch obrigatório** (DEF-B11.1 (a)); ⟦v2.2⟧ **visualization gasta FE só em M=2** (early-return p/ M≠2) e **BLOQUEIA em plt.show()** → desligar continua obrigatório; ⟦v2.2⟧ erratum T′ **fechado: código usa MIN** ✓; re-sample sem cap fiel (fn. 6); cold-start: classe ausente → modelo None → seleção aleatória (design); matplotlib é dependência de import mesmo desligado |

---

### I.6 · c122 θ-DEA-DP (autor, Python/torch)
**Fluxo real:** duas FNNs 2×200 ReLU softmax-3 sobre pares concatenados [x_i,x_j] no espaço de DECISÃO — Pareto-Net (dominância) e θ-Net (θ-dominância PBI, θ=5), sempre usadas em conjunto (estágio 1: filtros Q1>Q2>Q3 por acordo das duas; estágio 2: EDN e(z)=Σ I(vence)·p̂ + e_θ; z*=argmax) → 1 FE/iteração; retreino warm-start gateado por acc_min>γ=0.9 e dosado por E_upd=(1−acc/γ)·20, janela T_max=11n+24; CE ponderada por frequência inversa de classe. **Integração:** patch de normalização (fixar f_min/f_max por problema — OBRIGATÓRIO, fiel ao paper); visualization=False; adapter às nossas classes (⟦v2.7⟧ mas `pymop`/`optproblems`/`autograd` são imports DUROS — satisfazer ou cortar `problems/wfg.py`; N.2); CPU + determinismo torch. **Export:** softmax do escolhido + agregados por categoria + accs de validação (C1). **Nuance central (paper):** a incerteza é gestão do *approximation noise* — confiança max-softmax pondera a seleção (p_sum/EDN) e a acurácia por classe gateia o retreino; não há bônus de exploração.

---

### L.6 · c122 θ-DEA-DP — adapter: objeto com `n_var/n_obj/xl/xu/name` + `evaluate(lista de Individuals)→(N,M)`; driver = fork do tdeadp_main.py (constantes; device CPU); **f_min/f_max entram pela ASSINATURA** de `scalar_dom_ea_dp` (sem tocar o core); visualization omitir (default False no core). x normalizado [−1,1] na entrada das redes. Cap anti-spin exige fork do main loop (retries regeneram 7000 offsprings sem FE). Reprodutibilidade: `random.seed`+`np.random.seed`+`torch.manual_seed`+`use_deterministic_algorithms(True)`+threads=1; creator DEAP + PerCounter novos por run. matplotlib precisa estar instalado (import hard). **RNG:** stdlib random (DEAP SBX/PM, variation, survival random.sample, PerCounter shuffle, fallbacks) + numpy (LHS) + torch (init pesos, randperm minibatch). **FE:** contador local; init conta; +1/iteração; término EXATO sem overshoot; retry sem FE. Custo D=30: ~1,25e5 pares/época de update ×≤20 épocas ×2 redes; filtro 7000×2×2 forwards/iteração.

---

### M.12 · c122 θ-DEA-DP
- **Por que DUAS redes:** só Pareto-dominância perde pressão em alta-dim; só θ-dominância converge devagar (uma solução pode θ-dominar o rep local e ser Pareto-dominada por outro cluster) → as duas juntas, e a busca segue guiada "even if one of the two surrogates performs poorly" (robustez declarada). **N\* → approximation noise:** N* grande amostra boas candidatas, mas grande demais usa o surrogate "too frequently → too much approximation noise since surrogates are imperfect" — é ESTE o motivo do cap Q_max, e a **confiança max-softmax é o antídoto** (dominância confiante pesa mais). Preseleção pura: a survival selection sempre usa fitness REAL — o surrogate nunca substitui a avaliação.
- **Ablação (Fig. 7):** U, N*, Q_max "need to be sufficiently large" mas valores maiores "may harm final performance"; T_max menor é preferível (focar nos mais recentes); redes não podem ser complexas demais (overfitting com dados limitados) → sustenta a arquitetura enxuta 2×200.

---

### E.7 — θ-DEA-DP (c122) · autor/PyTorch+DEAP [ENRIQUECIDO v2.1]
**Sem manifesto de deps** → congelar env (§18.3). ⟦v2.7 — corrigido: `pymop`/`optproblems`/`autograd` são imports DUROS (N.2)⟧ — satisfazer os imports ou cortar `problems/wfg.py`; os nossos 26 entram pelo adapter, mas o import tem de resolver. q=1 estrito nativo (1 FE/iteração; init conta no orçamento — igual à nossa §5.4, confirmado no Alg. 1 do paper).
**⚠⚠ Normalização (DEF-B11.1 — FECHADA NA DIREÇÃO, resta formalizar):** o paper DECLARA normalização à la ParEGO no início (§III-A; objetivos normalizados ≥0, §II-B fn.2) com limites do problema; **o código nunca seta f_min/f_max reais** (fica 0/1 implícito — quebra PBI/clustering em BBOB/WFG/DTLZ1). **Patch obrigatório e FIEL AO PAPER:** fixar f_min/f_max por problema (fronts verdadeiros/nadir; estender a factory aos 26) — sem isso o código viola o próprio paper.
**⚠ Desligar `visualization`** (consome FEs reais não contadas — o Alg. 1 do paper conta TODAS).
**Custo de treino:** T_max=11n+24 recentes (não S(S−1) sobre o arquivo todo — o cap é do paper); pareamento O(T_max²) (D=30: 354² ≈ 1,3×10⁵ pares/retreino); retreino gateado por acc_min>γ e dosado pela Eq. 5 (E_upd=(1−acc/γ)·E_init). Anti-spin: re-gerar sem cap é fiel ao paper (fn. 6); cap de segurança logado como desvio documentado (► 10 tentativas → fallback melhor p_sum).
**Erratum do paper:** §III-C-2 imprime "max{|A|,T_max}−1" (semântica correta = min) — conferir qual o código implementa. Schema de export: classificador (DEF-C1). Pop/vetores do paper: N=11 (M=2) / 15 (M=3).

---

**Âncora de fidelidade (Anexo J):**

| c122 θ-DEA-DP | ZDT1–4 (n=10), DTLZ1mod (m=2,n=6), DTLZ2/4/7 (m=3,n=8), WFG6/7 (m=3,n=10,k=m−1); m=5/8 | 11n−1 LHS (conta no total) | 250 (m≤3)/300/400 | 21 | IGD mediano (ND de TODAS as avaliações); Wilcoxon+Holm | ZDT1 1,61e-2; DTLZ2 1,23e-1; WFG7 1,46e-1; ZDT4 2,80e+1 (falha admitida) |
