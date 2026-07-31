# Varredura pré-registrada do N dos pisos online [D65]

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

**D65:** N∈{10,20,30,50} × (5 problemas do sweep + 2 reps alta-D) × 5 sementes; critério = **mediana do IGD+ final (D70)**; escolhe **1 N por faixa de D** (baixa ≤5 / média / alta ≥20) ANTES da bateria. Piso offline mantém o lattice do b5m (50 M=2 / 105 M=3 — DI-16.4). **[DI-32/A2 → RETIFICADO pela DI-39, 2026-07-25 — ver REGISTRO PARTE A41/T12.D2] N=20 dos pisos ONLINE é PROVISÓRIO; esta varredura é PRÉ-REQUISITO do M8, não sub-estudo opcional do M11.**

---

### 3.2 Online — 4 pisos não-surrogate [DECIDIDO; casamento re-mapeado v2.0; 4º piso SMS-EMOA + banda p/ BO-especiais na D25/v3.0.8]

**NSGA-II, NSGA-III, MOEA/D e SMS-EMOA puros** (todos nativos no PlatEMO, via A2; SMS-EMOA acrescentado na D25). **Propósito:** os SA-MOEA comparam surrogate contra surrogate; o piso responde a pergunta que eles *não* respondem sozinhos — **"o surrogate compra alguma coisa, afinal?"**. É a régua que mostra o valor do surrogate sob orçamento apertado.

**Por que três (não um):** cada piso é **casado** ao *princípio de seleção* de uma família de motor, dando **atribuição limpa** do ganho ao surrogate. **Mapa re-mapeado ao set de 16 (v2.0),** pelos 3 princípios espelhados EA↔BO:
- **NSGA-II → dominância/Pareto:** EA-Dominância (b4, c217, c141, e74) · BO-Melhoria-de-Pareto (c238).
- **MOEA/D → decomposição:** EA-Decomposição (b3, c122) · BO-Decomposição (b1).
- **NSGA-III → referência/indicador:** EA-Indicador (e7).
- **[D25/v3.0.8] SMS-EMOA → hipervolume:** BO-Hipervolume (c262 qNEHVI). O SMS-EMOA seleciona por **contribuição de hipervolume (S-metric)** — **espelho mecânico exato** do princípio de aquisição do c262 (mesma seleção por HV; um com GP, outro sem) → a **atribuição a mais limpa possível** do ganho ao surrogate, e justamente na métrica principal (§12). Nativo no PlatEMO (custo-zero de integração), **não treina GP** (compute trivial); M≤3 aqui, então o custo exato do HV é irrelevante. *(SMS-EMOA PURO — ≠ mtm5 SMS-EMOA-MA, variante surrogate que é só reserva, §3.6.)*
- ✔ **[DEF-A13 RESOLVIDA — D25/v3.0.8] BO-especiais (c154 JES, e81 qPOTS, c149 LBN-MOBO) = comparados contra a BANDA dos pisos.** Esses três têm mecanismos **sem análogo populacional** (JES = ganho de informação/entropia; qPOTS = Thompson sampling; LBN-MOBO = batch local por rede bayesiana) → não há piso "casado por princípio" para eles. Regra: são interpretados contra o **envelope (banda min–máx) dos 4 pisos por problema**, não contra um piso único eleito. **Não adiciona runs** (os 4 pisos já correm nos 25 problemas — é decisão de interpretação/plot) e o Friedman global (§14/§15) já os ranqueia contra as 17 configs. *Rejeitadas:* "NSGA-III único" (piso arbitrário, não casa com nenhum dos três) e "melhor piso por problema" (máximo de baselines correlacionados = enviesado; a régua mudaria de problema para problema).

**Protocolo de FE dos pisos [DECIDIDO — precedente ParEGO/Knowles]:** o MOEA puro gasta FE de forma "gulosa" (avalia a população inteira por geração). Como orçamento e (população × gerações) são amarrados, a única decisão é **o tamanho da população** (as gerações são derivadas: `= K ÷ população`). O precedente canônico é o ParEGO: roda NSGA-II puro no mesmo orçamento minúsculo, **reduzindo a população** (para 20, escolhida por varredura de 10–50 para dar ao baseline sua melhor chance). Aplicado aqui:
- Mesmo orçamento dos SA-MOEA: `maxFE = 31D−1` (§5.1).
- **População `N = 20` — CRAVADO [decisão do autor, 2026-07-18; supersede o "~20–25 calibrada no piloto" desta linha].** A D65 havia superseditado tanto o "100" (§6.3) quanto o "~20" (§6.4/§3.2) delegando o valor à varredura pré-registrada, mas essa varredura é o cartão `SUB-varN`, que **depende-de `R1-pisos`** — o piso precisa existir antes de ser varrido. Para desatar a circularidade, o autor cravou **N=20** como o valor em vigor. **Justificativa (4 pontos, defensável em banca):**
  1. **Precedente canônico** — é exatamente o valor do **Knowles/ParEGO**, que varreu 10–50 e elegeu 20 para o NSGA-II puro sob orçamento minúsculo; é o precedente literário que este protocolo já declara seguir.
  2. **Interseção das fontes vivas** — 20 é o **único** valor que satisfaz ao mesmo tempo a faixa `~20–25` desta seção e o conjunto pré-registrado `{10,20,30,50}` da D65 ⇒ o cravamento **não introduz um valor novo**, apenas elege o ponto comum.
  3. **Viabilidade em todo o grid** — `20 ≤ 11D−1` para todo `D≥2` (o menor DoE é 21, em D=2) ⇒ roda nos 25 problemas **sem teto anti-crash**. Já `N=100` é **infactível** em D=2 (população 100 > DoE de 21 pontos; 20D=40 infills não fecham uma geração) e degenerado no resto (2–6 gerações).
  4. **Densidade de gerações** — rende 2 gerações no pior caso (D=2), 12 no DTLZ2 (D=12) e 30 no ZDT1 (D=30): evolução real em todo o grid, sem colapsar a diversidade populacional (que `N=10` comprometeria, sobretudo nos vetores de referência de NSGA-III/MOEA-D em M=3).
5. **Efeito colateral CONHECIDO e ACEITO — MOEA/D ⟦v5.2.1⟧:** com `N=20` a vizinhança do MOEA/D é `T = ceil(N/10) = 2`, mínima ⇒ os mesmos dois pais se repetem e a taxa de **duplicata bit-exata** sobe (medido no R1-pisos, ZDT1 semente 0: **182 cache-hits ≈ 23% dos 780 offspring**), e o MOEA/D fica o **pior dos 4 pisos** (ZDT1, por larga margem). **Não é bug** — é o algoritmo stock sob a D89: duplicata **não gasta FE, gasta o SLOT do infill**. Registrado para que a **dupla prova de sanidade do §17.5.1** não leia esse IGD+ como defeito de integração.

  A varredura da D65 (`SUB-varN`) **reconfirma ou substitui** este valor antes da bateria; se eleger 20 para alguma faixa de D, os runs do `R1-pisos` já são os definitivos.
- **Semeada do DoE compartilhado** (§5.2): parte dos mesmos `11D−1` pontos LHS, iniciando a evolução com os melhores por não-dominância. **[v5.2 — D88] Desempate quando a fronteira-1 do DoE excede a população: crowding distance, determinístico** (o critério nativo do NSGA-II) — dois runs da mesma semente selecionam o mesmo subconjunto.
- Mesmas 30 sementes. Custo trivial (não treina GP).

*(Histórico: a confusão "piso com surrogate" desfeita, e a distinção dos dois papéis de baseline — corpo vs régua — no Anexo G.4.)*

---

### 6.3 Política do tamanho de população `N` (Balde B transversal) [D20]

`N` (tamanho de população / nº de vetores de referência / teto de treino, conforme o algoritmo) é **idiossincrático** e **não comparável** entre algoritmos — forçá-lo igual seria pior que respeitar o default. **Política:** **N=100 (default PlatEMO)** como regra; **override para o valor do paper apenas onde é load-bearing** (muda o mecanismo); **tetos de segurança anti-crash** são implementação obrigatória.

| Algoritmo | N | Justificativa |
|---|---|---|
| c217 PC-SAEA | **50** | paper (D17) — controla o lote de infill (≤6/geração com o patch do init) |
| b4 CSEA | **50** | paper — N limita o conjunto de treino e o nº de gerações sob orçamento (load-bearing) |
| c122 θ-DEA-DP | **11 (M=2) / 15 (M=3)** | nº de vetores de decomposição do paper (estrutural) |
| c141 MMRAEA | **min(100, 11D−1)** por subpopulação | evita crash em D≤4 (ES_PDR.m:20); paper = 50/subpop |
| e74 CLMEA | **min(100, \|Arc\|)** | evita crash; init nativo 100/200 |
| b1, b3, e7, c238, e103 | **100** | default PlatEMO (c238/e103: default do próprio código do autor); o paper não prescreve outro valor load-bearing |
| **pisos ONLINE** (NSGA-II/III, MOEA/D, SMS-EMOA) | **20** | **[CRAVADO 2026-07-18 — supersede o "100" desta linha]** protocolo Knowles/ParEGO: sob orçamento mínimo o piso se calibra REDUZINDO a população (gerações = 20D ÷ N). Justificativa completa em **§3.2**. `N=100` é infactível em D=2 (pop > DoE de 21) e degenerado no resto. Reconfirmado pela varredura D65 (`SUB-varN`) antes da bateria |
| c262, c154, e81, c149 (BO) | **—** | sem N populacional; init/pop internos definidos nas linhas específicas (§6.4) |

**Consequência em M=3 (aceita) — vale para N=100 E para o N=20 dos pisos ⟦v5.2.1⟧:** o lattice das-dennis do `UniformPoint(N,M)` **arredonda para BAIXO** até o maior H com C(H+M−1,M−1) ≤ N. **(a)** Com **N=100**, o NBI de b1/b3/e7 gera **91 vetores** (não 105) → no K-RVEA, δ=0,05·91≈4,55. **(b)** Com **N=20 nos PISOS ONLINE**, `UniformPoint(20,3)` dá **H=4 → 15 vetores** (H=5 → 21 > 20) ⇒ **NSGA-III e MOEA/D rodam com `N efetivo = 15` em M=3** (medido no gate: DTLZ2 D=12, n_ger = 19 e 17 em vez de 13); **NSGA-II e SMS-EMOA não usam vetores de referência e mantêm 20**. Como M=3 é metade do grid, o 'N=20' **não é uniforme entre os 4 pisos**. Aceito, mesmo precedente do (a). **O mesmo vale para a varredura D65/`SUB-varN`: em M=3 os N nominais {10,20,30,50} viram efetivos {6,15,28,45}** (o critério compara os N nominais; o efetivo é registrado). Todos os N efetivos vão no **manifesto de cada run** e para a dissertação.
