# e7 EDN-ARMOEA (PlatEMO 4.15 built-in)

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

**Decisões específicas:** Built-in 4.15 (N.2.1 — dilema E.8 morto). Sem dedup de infill → guarda (c) do D60 (saldo congelado). Higiene torch não se aplica (MATLAB DLT), mas monitorar RAM do trainNetwork (D86/§22.5.7).

---

- [ ] **e7 EDN-ARMOEA** *(I.4, L.4, N.2.1, N.3)* — **built-in 4.15** (API moderna; sem porte — N.2.1). Patch de fidelidade: **dropout 0,1 do paper** (🟠→ARTIGO, D30; código dropP=[0.2, 0.5]); Ke=3 e demais ficam (CÓDIGO, B6.6 registrada). Hardcodes que ignoram Params: decay (trainNet.m:42), run/batch (updatemodel.m:4–5). Guard `sqrt(max(s2−mu.²,0))` (Estimate.m:26 — PopStd complexo). Logar `min(A.objs)`/ciclo (translação, C3) e infill duplicado (sem dedup nativo — **v5.2/D89: cache-hit = 0 FE; a duplicata desperdiça o SLOT do infill, não FE — logar**). **Patch do DoE (v5.2 — D94): substituir `EDNARMOEA.m:31–:32` JUNTAS** (X nativo direto; a :32 re-escala e causaria dupla-escala). FE: init (EDNARMOEA.m:30–32) + 3/ciclo (:75); D=30 fecha exato em 929. Custo ~1,7M passos SGD/run em D=30 — **medir no piloto, nunca reduzir** (B6.4). `assert ver('nnet')` + pdist2.

---

| e7 | Ke (infills/ciclo) | Específico | 3 | código oficial (paper k=5) | Nº de soluções por ciclo p/ avaliação real (k-means nos objetivos preditos) |
| e7 | wmax | Compartilhado (b3,e7) | 20 (→ 19 gerações internas) | código oficial | Nº de gerações do EA interno por ciclo (laço efetivo 19) |
| e7 | δ (limiar) | Específico | 0,05 (`<` estrito) | código oficial (paper 0,08) | Limiar de mudança/convergência que rege atualização/seleção |
| e7 | Rede (arquitetura) | Específico | 40/40 (2 ocultas), ReLU+tanh, única multi-saída M | código oficial + paper ✓ | Uma só rede prediz todos os M objetivos |
| e7 | Treino (SGD) | Específico | 8e4/8e3 passos, lr=0,01, wd=1e-5 só em W, batch=d, sem momentum | código oficial | SGD puro; 80k passos no 1º treino, 8k nos re-treinos (warm restart) |
| e7 | Dropout | Específico | 0,1 (entrada+oculta), invertido, ATIVO na inferência | D30 (ARTIGO) | Corrigido do código [0,2/0,5] → 0,1; ativo na inferência p/ gerar as T passagens (base da incerteza) — o default alteraria o σ que a tese mede |
| e7 | T (passagens MC-dropout) | Específico | 100 → μ e σ | código oficial + paper ✓ | 100 forward passes estocásticos; μ=média, σ=desvio populacional das T passagens (alimenta a ARMOEA) |
| e7 | Init de pesos | Específico | N(0, 1/fan_in) | código oficial (paper U[−0,5;0,5]) | Inicialização normal escalada pelo fan-in |
| e7 | Pop interna (Problem.N) | Compartilhado (b1,b3,e7) | 100 (M=3 → 91) | D20 (default; paper P=50 não load-bearing) | Tamanho da pop do EA interno sobre o surrogate |
| e7 | Translação pelo ideal | Específico | do 2º re-treino em diante | código oficial | A partir do 2º re-treino translada objetivos pelo ideal (melhor condicionamento) |
> **Notas.** 4 divergências paper×código mantidas no CÓDIGO: δ (0,05 vs 0,08), Ke (3 vs 5), P/N (100 vs 50, via D20), init de pesos. D30: dropout CORRIGIDO p/ 0,1 (ARTIGO — toca o σ que a tese mede); fica ativo na inferência (é o mecanismo de incerteza da EDN). σ = desvio populacional das T=100 passagens. Balde C: e7 (EA) usa SBX 1/20 + PM 1/D/20.
| e7 EDN-ARMOEA | Ke=3 infills/ciclo; wmax=20 → ⟦v2.2⟧ **19 gerações internas** (`while w<wmax`); ⟦v2.2⟧ **δ=0.05** (default do código; `<` estrito); rede à mão 40/40 (ReLU+tanh — comentário "%Sigmoid" é errado), **única multi-saída M**; SGD puro 8e4/8e3 (lr=0.01, wd hardcoded 1e-5 só em W, batch=d com viés nos extremos, **sem momentum**); ⟦v2.2⟧ **dropout invertido dropP=[0.2, 0.5]** (entrada 0.2 + oculta 0.5), TAMBÉM na inferência; T=100; ⟦v2.2⟧ **init de pesos N(0,1/fan_in)** (Marsaglia polar; B{1}=0,0158 const); pop interna = **Problem.N=100** (⟦v2.2⟧ NBI: M=3 → NW=91 vetores, denominador do Ratio); σ = desvio POPULACIONAL das T passagens; translação pelo ideal só do 1º retreino em diante (ciclo 1 treina cru); sem warm-start de pop entre ciclos; kmeans nos objetivos preditos; **sem dedup do infill** (pode re-avaliar ponto já visto) | ⚠ paper: **δ=0.08, k=5, P=50, dropout 0.1, U[−0,5,0,5]** — **quatro divergências código×paper** [DEF-B6.6 ampliada]; 40/40 ✓, T=100 ✓, 8e4/8e3 ✓, lr/wd ✓, batch=d ✓, sem momentum ✓; cap treino 11d−1 (recentes+máx-ângulo) ✓; ⟦v2.2⟧ overshoot = (3−(20D mod 3)) mod 3 → D=30: **0**; D=2: +2; D=10: +1; custo D=30: 1,68M passos SGD/run |

---

### I.4 · e7 EDN-ARMOEA (PlatEMO 4.15 built-in — API moderna; ver N.2)
**Fluxo real:** rede densa feita à mão (40/40, ReLU+Tanh, dropout na entrada e 1ª oculta) treinada por SGD puro (8e4 passos init / 8e3 update, lr 0.01, batch=d) sobre dados escalados; predição = T=100 forward passes com máscaras dropout → μ = média, σ = desvio (MC-dropout); motor ARMOEA (pontos de referência adaptativos IGD-NS); infill Ke por k-means na pop final: cluster com queda de diversidade → máx σ̄, senão → mín distância à origem (transladada). **Integração:** built-in 4.15 API moderna (N.2 — sem porte/env especial); patch LHS (EDNARMOEA.m:31); Statistics Toolbox não-declarada (kmeans/pdist2). **σ exportável:** vetor por objetivo (Estimate.m:30); μ em espaço transladado pós-retreino → logar `min(A.objs)` do ciclo (B6.1/C3). **Divergências:** Ke=3 × k=5 do paper (B6.6); treino transladado × [−1,1] do paper; custo ~1,7M passos SGD/run em D=30 (B6.4 — medir, nunca reduzir orçamento).

---

### L.4 · e7 EDN-ARMOEA — hardcodes que ignoram Params: decay (trainNet.m:42), run/batch do update (updatemodel.m:4–5). Rede única multi-M; ciclo 1: treina em y CRU e roda 8k passos redundantes de update; translação a partir do 1º retreino → logar `min(A.objs)` por ciclo (C3). Sem warm-start de pop entre ciclos (pop nova `rand(N,D)` + RefPoint zerado por ciclo). Sem dedup do infill (FE desperdiçado possível — logar). **RNG (ordem):** probe; LHS; init da rede (Marsaglia — consumo VARIÁVEL); minibatches rand(1,8e4·D)/rand(1,8e3·D); máscaras dropout (2/passo de treino; 2×T=200/chamada do Estimate); pop rand(N,D)/ciclo; torneio+GA/geração; kmeans++/ciclo; perturbação rara 1e-6·rand. **FE:** init (EDNARMOEA.m:30–32) + 3/ciclo (:75); D=30 fecha EXATO em 929. Instrumentação: μ/σ em Estimate.m:29–30 (call sites :50/:61); Ratio/flag/New (:72–75). **[v5.2 — D94] Patch do DoE: substituir EDNARMOEA.m:31–:32 JUNTAS** (X nativo direto na Evaluation; a :32 re-escala e causaria dupla-escala).

---

### M.5 · e7 EDN-ARMOEA
- **Racional (por que dropout-como-incerteza):** dropout-NN ≈ deep GP (Gal & Ghahramani); dropout no TESTE (T=100 passagens numa única rede) dá a variância preditiva sem guardar/retreinar T redes — inviável em SAEA. **Justificativa empírica decisiva (nova):** as tabelas do suplemento mostram que **a incerteza do GP COLAPSA/fica não-informativa em alta-dim/poucos-dados**, enquanto o EDN mantém incerteza discriminativa — é o *porquê concreto* de preferir dropout a σ-de-GP neste regime (liga-se ao nosso eixo "como cada um usa a incerteza").
- **Ablação do gatilho de diversidade:** a Tabela I isola a gestão de modelo usando GP em todas as variantes — o dual (convergência + switch-por-incerteza) vence convergência-pura e diversidade-pura (melhor em 8/16) → **a cadência de troca é feature, nenhum critério isolado basta**. delta é o botão explor/explot (delta maior → menos seleção-por-incerteza). AR-MOEA foi escolhido em parte porque suas reference vectors já fornecem o sinal |Wv|/|W| do gatilho.
- **Honestidade:** dropout 0,1 "no theoretic guidance" (abaixo do 0,2/0,5 de Srivastava — nosso código usa 0,2/0,5, Anexo L.4 → divergência já registrada); heurística itertrain≈30×#params.

---

**Âncora de fidelidade (Anexo J):**

| e7 EDN-ARMOEA | DTLZ1–7+WFG1–9; d∈{20,40,60,100} M=3; m∈{3,5,10,20} d=40 | 11d−1 LHS | 11d+119 | 20 | IGD (1000 ref); Wilcoxon 5% | DTLZ7 d=40 M=3: 4,574 (GP 8,581; HeE 6,393); DTLZ2 d=20: 0,647 (HeE 0,311 vence); vs K-RVEA 9/21 |
