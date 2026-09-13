Todas as medições fecharam. Composição do laudo final.

---

# LAUDO — PISO DE RUÍDO FINAL + VALIDADE ESTATÍSTICA (corpus congelado, 16.811 células)

Método: read-only; nenhum experimento invocado; nenhum arquivo do repo tocado. Reconciliação com o F30 (transversal_ruido.md), não refazimento — magnitudes de HV/IGD+ do F30 são herdadas (os artefatos do scratchpad do F30 expiraram; pipeline de métricas NÃO re-executado); tudo abaixo do que é bit-nível/censitário foi re-MEDIDO hoje.

## 1. Piso de dois níveis do F30 — CONFIRMADO sobre o corpus final (com 2 atualizações)

**As duplicatas cross-VM ainda existem.** Inventário direto dos 6 stagings `~/mestrado_coleta_m8/matlab-vm{1,2,3,4,5,10}/experiments`: **111.880 arquivos** (F30: 111.866; os +14 são exatamente as cópias de 2 células novas, abaixo) → **15.129 células distintas** (EXATO vs F30) · **11.046 em ≥2 VMs** (EXATO) · **764 células com ① em ≥2 VMs** (F30: 762; **+2 chegadas pós-inventário F30**) → 768 pares brutos − 14 mesma-máquina = **754 pares cross-máquina** (F30: 752).

Re-medição bit-nível (md5 + arrays; host = `env.host` do manifest, normalizado `matlab-vmN`→`vmN`; corte 2026-08-14T10:26:42Z):

| regime | n pares | ①-divergentes | veredito |
|---|---|---|---|
| A (vm1×vm5 pré-corte) | 517 | **0/517 bit-idênticos em ①** | confirma deriva ZERO |
| B (vm1×vm5 pós-corte) | 168 | **44 (26,2%)** | confirma F30 (43) **+1 novo** |
| C (demais combinações) | 69 | 0 (7 md5≠, todos **bit-idênticos no FE comum** — artefato de orçamento c122×5/c262×2, reproduzido DI-43/44) | confirma |

Por config em B: c141 11/11 · e74 10/10 · b1 8/8 · b3 4/4 · c238 4/4 · e7 2/2 · **b4 1/11** · nsga3 2/31 · smsemoa 2/33 · nsga2 0/26 · moead 0/23 · c217 0/5. (1 par migrou de classe vs F30 por fonte de timestamp — manifest `updated_at` vs timestamps do jsonl; totais fecham em 752+2.)

**Atualização 1 — 🔵 (D29, toca surrogate ⇒ artigo):** `b4/DTLZ7/12` é duplicata NOVA (cópia vm5 datada 14/08T16:04Z, pós-corte) e **diverge de verdade** (2.069/19.068 valores de ①, máx abs 0,958; n_gerações difere). O b4 sai de "0/11, bit-estável" para **1/11 sensível a microarquitetura** — a lista das configs sensíveis passa a 7: c141, e74, b1, b3, c238, e7, **b4**. O corpus canônico NÃO é afetado: `resultados_experimentos/b4/DTLZ7/12` é md5-idêntico ao lado vm1 pré-corte (conferido).

**Atualização 2 — 🎯 inexplicado (D81, registro e escalo):** `moead/WFG9/8`, duplicata nova, vm5 em 10:26:15Z — **27 s ANTES do corte**: ① bit-idêntica (deriva de métrica = 0, pois HV/IGD+ derivam da ①), mas a camada ② difere em 7/1.560 valores (máx rel 3,2e-2). Único md5≠ do regime A em 517 pares. Causa não medida; se a régua do corte algum dia usar camadas ≠①, o corte teria de recuar para 10:26:15Z.

Extra medido: os 14 pares mesma-máquina descartados pelo F30 são benignos — 13 são truncamentos-checkpoint da MESMA trajetória vm1 (prefixo comum bit-idêntico 13/13) copiados ao staging da vm5; 1 é cópia bit-idêntica integral.

**T (teto):** os problemas REAIS têm **ZERO duplicatas ① cross-VM** — a deriva vm1×vm5-nova para RE21/DDMOP7/ESTOQUE40 **não é medível deste acervo**. A transferência do piso do F30 (medido em sintéticos) para os reais é extrapolação declarada, mitigada pela co-locação (item 2).

## 2. Exposição de hardware do corpus final (manifests canônicos, 16.811/16.811 lidos)

| estrato | n | vm5 pós-corte | exposição |
|---|---|---|---|
| main+ok sintéticos | 11.618 | 404 | **3,48%** (bate F30 EXATO) |
| main+ok reais | 1.143 | 424 | **37,10%** |
| **main+ok total** | **12.761** | **828** | **6,49%** |
| off | 3.122 | 120 | 3,84% |
| corpus inteiro | 16.811 | 965 | 5,74% |

Estratificação dos reais (main+ok) — **a exposição nova é 100% DDMOP7 e é CO-LOCADA**:
- **RE21: 476/476 na vm1** (15/08) — mono-máquina.
- **ESTOQUE40: 236/236 na vm1** (15–18/08) — mono-máquina.
- **DDMOP7: 424/431 na vm5 pós-corte (98,4%)** + 7 na vm1 (as sondas/seed 0 de b3, c238, e7, moead, nsga2, nsga3, smsemoa); vm5 pré-corte: 0. Mistura de hardware dentro de um contraste: no máximo **1/30 sementes** (a seed 0 dos 7 configs mistos vs configs puro-vm5) — mediana de 30 sementes é imune na prática (troca de 1 valor move a mediana no máximo ao estatístico de ordem adjacente).

Robustez da atribuição: só 3/16.813 células têm manifest vindo de staging diferente do jsonl (`_FONTES.csv`); os 343 manifests sem `env.host` são todos failed ou fora de main+ok (os 47 pós-corte: todos failed) — zero efeito no corpus analisável. **Não medido:** fidelidade da vm1 pós-14/08 vs pré (zero duplicatas temporais intra-vm1; evidência fraca a favor: os 13 prefixos-checkpoint bit-idênticos).

## 3. n efetivo e onde o pareado perde poder (main, ok, sementes {0–28,42}; semente 30 ausente — confere)

17 configs × 28 problemas = 476 blocos: **316 com n=30 · 134 com 0<n<30 · 26 com n=0**. Contrastes pareados possíveis (pares de configs com dados no mesmo problema, n = interseção de sementes ok): **3.431** — n_comum ≥15: **3.232 (94,2%)** · ≥20: 92,0% · =30: 50,6%. Sintéticos: 2.980/3.163 com n≥15 (≈ os 2.983 do F30; meu critério — interseção — é um pouco mais estrito); reais: 252/268.

Os **199 pares com n_comum<15** concentram-se em 5 configs: **c154** (65 pares: 12 problemas zerados incl. DDMOP7/RE21/EST40, e n=2–23 no resto — o config é estatisticamente inutilizável fora de MMF1/MMF4/MMF11_L) · **c122** (55: WFG4 n=5, ZDT3 n=5, WFG9 n=6, WFG2 n=16) · **c262** (52: MMF16_20 **n=1**, WFG1 n=2, ZDT1 n=11; DTLZ7/ZDT3/EST40 = 0) · **c149** (39: ZDT3 n=12, ZDT1 n=14, DDMOP7 n=17) · **b1** (27: DDMOP7 **n=1**, DTLZ4 = 0). Pareado impraticável (n=1): todos os 15 pares b1×* em DDMOP7 e os 11 c262×* em MMF16_20. ESTOQUE40 tem só 8 configs com dados (28 contrastes, 15 com n=30). Fase 2 pooled DDMOP7: computável (431 ok), mas b1 contribui 1 célula.

## 4. Recomendação da régua de ruído para a R4 — texto pronto (recomendação, não veredito — D97)

> **Régua de ruído de máquina (substitui O-18).** A deriva numérica entre máquinas da frota foi medida diretamente em 754 pares de execuções duplicadas da mesma célula (mesmo algoritmo, problema e semente) em máquinas distintas. Em hardware de microarquitetura idêntica a deriva é **exatamente zero**: 586 pares (517 vm1×vm5 anteriores a 2026-08-14T10:26Z + 69 entre as demais máquinas) apresentam avaliações reais bit-idênticas, 7 deles após truncamento ao orçamento comum de avaliações. Toda a deriva observada ocorre num único regime — vm1×vm5 após a troca de microarquitetura da vm5 (14/08, 10:26 UTC) — e é traço de classe algorítmica: nas 7 configurações assistidas por surrogate com pares nesse regime (c141, e74, b1, b3, c238, e7, b4) a divergência ocorre em 40/40 dos pares dessas seis primeiras e 1/11 da última, enquanto NSGA-II, MOEA/D e c217 permanecem bit-estáveis (0/54) e NSGA-III/SMS-EMOA divergem residualmente (4/64). Quando diverge, a deriva por célula alcança ΔHV p95 = 10,6% e ΔIGD+ p95 = 28,5% [F30].
> No nível em que a campanha é lida — contrastes entre medianas de 30 sementes — o piso é função da exposição da coleta ao regime heterogêneo. No corpus final, 3,48% das células sintéticas válidas provêm da vm5 pós-troca, e o piso de contraste correspondente, obtido por Monte Carlo sobre as razões medidas [F30], é **ΔHV = 1,225% e ΔIGD+ = 3,238%**: contrastes sintéticos abaixo desses valores são indistinguíveis de ruído de máquina (1,8% e 2,1% dos contrastes da campanha, respectivamente). Os três problemas reais não adicionam exposição interna: cada um foi coletado em máquina única (RE21 e ESTOQUE40 integralmente na vm1; DDMOP7 98,4% na vm5, com mistura máxima de 1/30 sementes por braço), de modo que seus contrastes internos herdam o regime homogêneo — piso ≈ 0. Em contrapartida, por serem coletas mono-máquina, a **reprodutibilidade em outro hardware** desses blocos (e de qualquer contraste envolvendo configuração assistida por surrogate) deve ser lida contra o piso de exposição total, **ΔHV = 5,012% e ΔIGD+ = 10,876%** [F30] — este é o limite de generalização declarado, não um defeito dos dados: os algoritmos evolutivos puros são bit-reprodutíveis entre máquinas; os assistidos por Kriging são reprodutíveis apenas estatisticamente.

Nota de uso (não vai para o texto): se for exigido UM número pooled para main+ok (exposição 6,49%), a interpolação em lei de potência entre os dois pontos medidos do F30 dá HV ≈ 1,59% / IGD+ ≈ 4,05% — é **interpolação, não medição**, e é conceitualmente pior que a leitura estratificada acima, porque a exposição adicional é co-locada (não mistura braços).

## Artefatos (absolutos, scratchpad)
- `/private/tmp/claude-501/-Users-gmello/16c0ba84-843b-49d1-9ce6-6cecc418b734/scratchpad/hosts_final.csv` — 16.811 células × host/updated_at/status (fonte: manifests canônicos).
- `/private/tmp/claude-501/-Users-gmello/16c0ba84-843b-49d1-9ce6-6cecc418b734/scratchpad/pares_crossvm_final.csv` — 754 pares cross-máquina com regime e veredito md5 (real e pop).
- `/private/tmp/claude-501/-Users-gmello/16c0ba84-843b-49d1-9ce6-6cecc418b734/scratchpad/dup_sides.csv` — 1.530 lados das 764 células duplicadas.
- Scripts: `scan_manifests.py`, `inv_stagings.py`, `pares_md5.py` no mesmo diretório.

## Pendências escaladas (D81)
1. 🎯 `moead/WFG9/8` — camada ② difere com ① idêntica, 27 s antes do corte (item 1, Atualização 2).
2. 🔵 b4 entra na lista de configs sensíveis a microarquitetura (1/11) — ressalva de reprodutibilidade no artigo; corpus canônico não afetado.
3. O conflito c238×MMF1 do F30 (§5 do transversal) permanece como lá registrado — nada novo no acervo o resolve (a única duplicata desse par segue sendo seed 7, regime A, Δ=0).