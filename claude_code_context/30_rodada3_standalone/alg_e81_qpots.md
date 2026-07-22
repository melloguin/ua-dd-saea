# e81 qPOTS (autor, sobre BoTorch 0.16.1)

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

**Específicas:** env BoTorch **0.16.1 PRÓPRIO** (isolamento duro); bounds=[0,1]^D no adapter (mata o bug maximin); offset D22 nos ~6 sítios de seed (D62); **bucket-only (D54)**; kernel 1 linha (Matérn — D30).

---

- [ ] **3.5 · e81 qPOTS** *(I.12, L.12, N.2.2)* — **env BoTorch 0.16.1 PRÓPRIO** (isolamento duro; py3.10/3.11; pins hoje **satisfazíveis** (torch 2.12.0 existe — S.2#11)). **Receita canônica README/ablation — NUNCA a dos exemplos** (bug do `Acquisition` stale): recriar `ModelObject`+`Acquisition` **por iteração**; `fit_gp()`; `acq.qpots(bounds=B01, iteration=i, nystrom=0, dim=D, ngen=10, q=q)` (kwargs obrigatórios; ngen=10 = D46). **bounds=[0,1]^D no adapter — OBRIGATÓRIO** (mata o bug maximin nativo×normalizado); `train_y=−f`. **Matérn = 1 linha** `covar_module=` (model_object.py:120–124 — 🔵 ARTIGO, B17.8). **Forçar float64** (o `DEFAULT_DTYPE` do repo nunca é aplicado — N.2.2). Salvar/restaurar np/random em volta do qpots (pymoo re-semeia 2430); **offset A6**: `1024+iteration` (acquisition.py:219) e `seed=2430` (:366) **+1000·s**. **Dedup do candidato** (nugget 1e-12 → `NotPSDError` fatal); ⚠ **cache-hit × dataset crescente: a MESMA regra ratificada do c122 §5.3 (DI-21) — no cache-hit o conjunto de treino NÃO cresce**; **assert |lote|==q** (|ND|<q → lote menor silencioso; fallback qmaximin). Instrumentação: monkeypatch `_gp_posterior` + wrap `select_candidates`; μ/σ des-padronizados. Cholesky exato até 4096 (N.2.2) — o custo O(n³) é o **dado** (§17.6).

---

| e81 | Biblioteca | Específico | BoTorch 0.16.1 | código oficial | Backend; importar BoTorch eleva max_cholesky_size→4096 |
| e81 | Kernel | Compartilhado (c262,e81) | Matérn 5/2 ARD | D30 (ARTIGO) | Corrige o RBF ARD default (fix de 1 linha); incerteza fiel ao paper |
| e81 | Thompson sampling | Específico | re-amostrado por geração; base samples fixos/iteração (manual_seed(1024+iter)) | código oficial | Novas amostras da posterior a cada geração do NSGA-II, congeladas dentro da iteração → superfície coerente e reprodutível |
| e81 | Amostragem dos objetivos | Específico | independente por objetivo | código oficial | Cada objetivo amostrado sem correlação cruzada |
| e81 | NSGA-II interno — pop | Específico | 100·d | paper ✓ | Pop do MO interno sobre as amostras de Thompson (escala com D) |
| e81 | NSGA-II interno — ngen | Específico | 10 | D46 (README; paper omisso) | Gerações do MO interno; casa com o Thompson (muitas amostras baratas/iteração) |
| e81 | Seleção de candidato | Específico | maximin vs dataset INTEIRO | código oficial | Escolhe por maximin contra todo o dataset (favorece dispersão) |
| e81 | Batch q>1 | Específico | top-q do mesmo ranking | paper ✓ | Para q>1, os q melhores do mesmo ranking maximin |
| e81 | Nugget (train_Yvar) | Específico | 1e-12 fixo | código oficial (paper τ²=1e-3) | Variância de observação ~0 → interpolação quase exata (mantido o 1e-12 do código) |
| e81 | Init (DoE) | Global-override | 11D−1 LHS (≠ torch.rand ntrain=20) | protocolo uniforme (Anexo J) | Sobrescreve o torch.rand nativo (20 pts) |
| e81 | Sinal / domínio | Compartilhado (BO) | Maximização interna, [0,1]^D | §5.5 | e81 maximiza; bounds [0,1] obrigatórios |
> **Notas.** Divergência de nugget: paper τ²=1e-3 vs código 1e-12 → mantido 1e-12 (fidelidade ao código; surrogate praticamente interpolante). D46: ngen=10 do README (paper omisso), escolha nossa. Importar BoTorch → max_cholesky_size 4096 → **Cholesky exato** em todo o regime (n≤929). Kernel corrigido p/ Matérn 5/2 ARD (D30).
| e81 qPOTS | GP RBF ARD (default BoTorch 0.16.1; ⟦v2.2⟧ fix Matérn = 1 linha: `covar_module=` em model_object.py:120-124); ⟦v2.2⟧ **TS re-amostrado POR GERAÇÃO na população corrente** (base samples fixos por iteração via `manual_seed(1024+iter)`, mas a MVN muda com a pop — "TS acoplado à população", não 1 caminho coerente); objetivos amostrados INDEPENDENTES; NSGA-II pymoo pop=100·d (⟦v2.2⟧ `minimize(seed=2430)` **re-semeia np.random/random GLOBAIS** a cada chamada); seleção maximin vs dataset INTEIRO; q>1 top-q do mesmo ranking (⟦v2.2⟧ se \|ND\|<q → lote MENOR silencioso — assert no harness); ⟦v2.2⟧ nugget train_Yvar=1e-12 fixo; fit SEM try/except (duplicata → NotPSDError fatal → dedup no adapter); **maximin mistura espaço nativo×normalizado → bounds=[0,1] OBRIGATÓRIOS no adapter**; init nativo = torch.rand ntrain=20 (nosso LHS injetado); deps pinadas: botorch==0.16.1, torch==2.12.0, gpytorch==1.14.2, numpy==2.2.6, pymoo==0.6.1.6, py≥3.10<3.12 | pop=100·d ✓ paper (B17.2); Matérn 5/2 = paper [DEF-B17.8]; ngen n.r. no paper (► 10); top-q = leitura do próprio paper ✓ (B17.5); τ² paper 1e-3 × código 1e-12; Nyström OFF ✓ (⟦v2.2⟧ seed do Nyström nunca varia — mais um motivo); ⟦v2.7 — corrigido, supera a nota v2.2⟧ **importar BoTorch eleva `max_cholesky_size→4096` GLOBALMENTE → Cholesky EXATO em todo o nosso regime (n≤929 online); a premissa "Lanczos rank~100 em D≥9" e a DEF-L3 estão RETIRADAS** (N.2); a preocupação real vira o custo O(n³) exato, já coberto pela política de teto de pontos (§19); ⟦v2.2⟧ exemplos têm **bug de `Acquisition` stale** (GP inicial p/ sempre) — usar o padrão README/ablation: recriar ModelObject+Acquisition por iteração; seed 2043 é quase inócuo (reset pós-seleção) |

---

### I.12 · e81 qPOTS (autor, Python/BoTorch 0.16.1)
**Fluxo real:** 1 realização conjunta de Thompson por iteração (reparametrização Y=μ+Σ^½Z) → NSGA-II (pymoo, pop=100·d, ngen a fixar) sobre os caminhos amostrados → candidato = argmax da distância maximin ao dataset (q>1: top-q do mesmo ranking) → 1 FE. **Integração:** E.6 (sinal maximiza; testar sobre 0.18; Nyström OFF; seeds internos → DEF-A6 offset). **σ exportável:** posterior BoTorch; logar a pop final do NSGA-II interno por iteração. **Divergências:** kernel RBF-código × Matérn-paper (B17.8); nugget 1e-6 × τ²=1e-3 adicionado no paper.

---

### L.12 · e81 qPOTS — receita canônica (padrão README/ablation — NUNCA o dos exemplos com bug): por iteração, RECRIAR `ModelObject(train_x, train_y, B01, nobj=M)` + `fit_gp()` + `Acquisition(tf, gps, q=q)`; `newx = acq.qpots(bounds=B01, iteration=i, nystrom=0, dim=D, ngen=NGEN, q=q)` (kwargs nystrom/dim/ngen/q OBRIGATÓRIOS; nunca passar mt/partial_info). **bounds=[0,1]^D no adapter** (mata o bug maximin nativo×normalizado); train_y=−f; salvar/restaurar estado np.random/random em volta do qpots (pymoo re-semeia 2430); DEF-A6: offsetar `1024+iteration` (acquisition.py:219) e `seed=2430` (:366) por semente; dedup do candidato (dist<ε ao dataset — nugget 1e-12); assert |lote|==q (|ND|<q → lote menor silencioso; fallback qmaximin). Instrumentação: monkeypatch `_gp_posterior` (draws por geração), wrap `select_candidates` (front + índice), μ/σ = `gps.models[j].posterior(newx)` des-padronizado. **RNG:** torch global sequestrado por iteração (manual_seed interno); np/random re-semeados pelo pymoo — variância entre sementes vem SÓ do init sem o offset A6. **FE:** ntrain + iters·q — exato, sem overshoot.

---

### M.9 · e81 qPOTS
- **Por que TS:** motivação central = **evitar computar o hipervolume** ("scales poorly with objectives"); em TS a aquisição *é* o próprio caminho posterior (α≡Y), sem função de aquisição cara a otimizar por dentro. Enquadra MOBO-HV como sofrendo de inner-optimization difícil + batch limitado + dificuldade com ruído — TS ataca os três. Maximin é **segunda camada** de diversidade (o TS já equilibra explore/exploit sozinho).
- **"Batch sem custo adicional" (o porquê):** o solver evolutivo devolve TODO o Pareto-set previsto num único solve; escolher q é só distância + ordenação — vs qNEHVI que resolve uma otimização estocástica *por ponto*.
- **Garantia (Ap. 5.2):** minimizador de soma ponderada é Pareto-ótimo (Prop. 5.1); a recíproca só vale se o conjunto atingível for **convexo** (Prop. 5.2) → em fronts não-convexos nenhuma escalarização linear recupera aqueles pontos — justificativa formal de multiobjetivo > multi-point. Ablação: robusto a ruído σ²∈{0..1e-3}.

---

### E.6 — qPOTS (e81) · autor sobre BoTorch [ENRIQUECIDO v2.1]
**⚠ Sinal: maximiza internamente** (`_gp_posterior` devolve `−Ys`) → adapter devolve `−f`, sem dupla negação. Repo pina `botorch==0.16.1`. ⟦v5.2.1 — CORRIGIDO, supera a nota v2.1 'testar sobre o env 0.18 primeiro'⟧ **o e81 roda em env PRÓPRIO `env_e81_qpots` com botorch==0.16.1** (isolamento duro — `artifacts/envs.json`); **não há teste sobre o 0.18**. Idem os valores: valem os do corpo — **nugget `train_Yvar=1e-12`** (não 1e-6) e **ngen=10 (D46)** (não 'a fixar') [E81-09/DI-16.18].
**Mecanismo:** 1 realização conjunta de Thompson (K caminhos, 1/objetivo) por iteração; NSGA-II (pymoo) sobre as amostras; seleção do candidato por **maximin-distance ao dataset**.
**Config:** pop=100·d hard-coded ✓ **confirmada no paper** (§4.1 — manter; medir custo do Cholesky em D=30 no piloto, teto documentado só se inviável — B17.2); **ngen: paper omisso** → registrar escolha nossa (► 10, do examples/README — B17.3); **⚠ kernel: paper = Matérn 5/2 ARD; código usa o default RBF ARD do BoTorch 0.16.1** → decisão de eixo de fidelidade (DEF-B17.8 nova); Nyström OFF ✓ (implementação incorreta no repo; o próprio paper o desliga no caso real); nugget: código 1e-6 fixo (paper adiciona τ²=1e-3 aos sintéticos — divergência registrada); seeds internos fixos (1024+iter, 2430, 2043) → DEF-A6.
**q>1 (batch):** código = top-q de um único ranking maximin (SEM diversidade mútua) — que é uma das DUAS leituras do próprio paper (Eq. 6 formal = greedy sequencial COM diversidade; parágrafo de implementação = top-q). ► Nativo top-q (B17.5), documentando a ambiguidade do paper; q=10 extrapola o máximo publicado (q=4).
Instrumentar o NSGA-II interno p/ camada surrogate. q=1 nativo no principal.

---

**Âncora de fidelidade (Anexo J):**

| e81 qPOTS | BraninCurrin(d2), DTLZ3(d10), DTLZ7(d5), ZDT3(d10) — K=2; NASA CRM (d24, SU2) | 10d uniforme | 50–800 FEs; CRM 200+200 | 10 (CRM: 1) | HV (refs fixas Tab. 1); SEM testes | DTLZ3 HV≈1,71e6 (800 FEs, ref (1e4,1e4)); ZDT3 ≈1,26e2 (ref (11,11)); CRM: qPOTS > qNEHVI/qParEGO em HV e tempo |
