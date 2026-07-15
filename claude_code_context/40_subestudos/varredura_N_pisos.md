# Varredura pré-registrada do N dos pisos online [D65]

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

**D65:** N∈{10,20,30,50} × (5 problemas do sweep + 2 reps alta-D) × 5 sementes; critério = **mediana do IGD+ final (D70)**; escolhe **1 N por faixa de D** (baixa ≤5 / média / alta ≥20) ANTES da bateria. Piso offline mantém N=100.

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
- **População pequena (~20–25), calibrada no piloto de timing** (varredura curta que dá ao piso a melhor chance — vira frase de método defensável).
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
| b1, b3, e7, c238, e103, pisos | **100** | default PlatEMO (c238/e103: default do próprio código do autor); o paper não prescreve outro valor load-bearing |
| c262, c154, e81, c149 (BO) | **—** | sem N populacional; init/pop internos definidos nas linhas específicas (§6.4) |

**Consequência em M=3 (aceita):** com N=100, o NBI de b1/b3/e7 gera **91 vetores** (não 105) → no K-RVEA, δ=0,05·91≈4,55. Aceito (não micro-gerenciamos para 105). Todos os N efetivos vão para a dissertação.
