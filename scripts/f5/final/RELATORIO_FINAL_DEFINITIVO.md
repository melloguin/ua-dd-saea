# RELATÓRIO FINAL DEFINITIVO — validação de fidelidade do corpus experimental completo

**Torre de validação de fidelidade · 2026-08-22 · doutrina D97: analiso e recomendo; o veredito é do autor**
**Corpus CONGELADO:** 16.811 células · 24 configs · 28 problemas (25 sintéticos + RE21/DDMOP7/ESTOQUE40) · 30 sementes {0–28, 42}
**Método:** 33 agentes (24 configs + 3 reais + 2 pendências + 4 transversais), 3 retomadas por limite de uso,
**auditoria de integridade dos 33 resultados feita e aprovada** (schema 11/11 e 8/8 completos, zero autodeclaração
de incompletude, nsga3 replicado 2× de forma independente com concordância integral).
**Herança:** F5 (666 células, s42) → T11 (s42 pós-refinamento) → F30 (15.129, 30 sementes) → T15 (3 reais, smokes) → **ESTA (definitiva)**.

---

## 1. VEREDITO FINAL RECOMENDADO

**ACEITAR o corpus para a dissertação.** Nota global de confiança: **87%**
(mecanismo **92,2%** · conformidade contratual **98,6%** · cobertura do grid **95,5%**).

Os três números-síntese, cada um medido em censo total (não amostra):

1. **O mecanismo dos 24 algoritmos é fiel aos artigos e invariante de semente, máquina e problema.**
   Query-joias fechadas em **100% da história do estudo** — só o b1: **223.581/223.581 eventos**
   (erro máximo 2,6e-13), incluindo as células que falharam (a identidade fecha até o último evento
   antes do crash). Zero bugs de algoritmo em **cinco exames consecutivos**.
2. **Conformidade contratual final: 99,4%** (16.710/16.811 células classe 1 + classe 2 sancionada);
   classe 3 inexplicada: **0,6%** (101 células, todas mapeadas e com destino no plano de correção).
3. **A fidelidade numérica dos problemas foi provada por reimplementação independente**:
   RE21 erro ≤5,5e-7 em 566 células · ESTOQUE40 query-joia 100% em 488.646 avaliações ·
   DDMOP7 identidades k/17 e n/690 a 100% em 302.643 pontos.

---

## 2. NOTAS FINAIS POR CONFIG (0–100%)

Régua declarada e reproduzível: `nota = mecanismo(score×10) × contratual × cobertura` — `f5/final/notas_finais.csv`.

| config | mecanismo | contratual | cobertura | **NOTA** | trajetória (F5→T11→F30→FINAL) |
|---|---:|---:|---:|---:|---|
| c217 | 95 | 99,9% | 100% | **94,9%** | 9,5→9,0→9,5→9,5 |
| c141 | 93 | 99,9% | 100% | **92,9%** | 9,5→9,5→9,3→9,3 |
| e74 | 93 | 100% | 99,9% | **92,9%** | 9,0→9,5→9,2→9,3 |
| moead_media | 93 | 100% | 99,4% | **92,4%** | 9,0→9,3→9,5→9,3 |
| e81 | 96 | 98,9% | 96,5% | **91,7%** | 9,5→9,7→9,6→9,6 |
| b5r | 91 | 100% | 99,5% | **90,6%** | 9,0→9,0→9,2→9,1 |
| smsemoa · moead | 90 | 100% | 100% | **90,0%** | 10→10→9,0→9,0 |
| nsga3 | 90 | 99,8% | 100% | **89,8%** | 10→10→9,0→9,0 ‡ |
| nsga2 | 90 | 100% | 99,4% | **89,5%** | 10→10→9,0→9,0 |
| b3 | 93 | 100% | 95,7% | **89,0%** | 9,6→9,8→9,4→9,3 |
| c262 | 96 | 98,1% | 93,1% | **87,7%** | 9,5→9,7→9,6→9,6 |
| c149 | 93 | 97,2% | 96,7% | **87,4%** | 9,0→9,5→9,2→9,3 |
| c122 | 93 | 98,4% | 95,0% | **86,9%** | 9,5→9,5→9,2→9,3 |
| e103 | 90 | 100% | 92,6% | **83,4%** | 9,3→9,5→9,0→9,0 |
| b1 | 93 | 99,9% | 87,1% | **81,0%** | 9,4→9,6→9,2→9,3 |
| b4 | 85 | 100% | 94,2% | **80,0%** | 9,0→9,5→9,0→8,5 |
| b5m | 90 | 100% | 86,8% | **78,1%** | 8,0→8,5→9,0→9,0 |
| e7 | 90 | 100% | 86,2% | **77,6%** | 10→10→9,0→9,0 |
| c238 | 90 | 98,1% | 87,4% | **77,1%** | 9,5→9,5→9,0→9,0 |
| c154 | 93 | 98,0% | 83,1% | **75,7%** | 8,5→9,0→9,2→9,3 |
| sobol_batch † | 95 | 100% | 100%† | 95,0%† | escopo batch (8 células) |
| treed_media † | 95 | 90,0% | 100%† | 85,5%† | escopo sweep (10 células) |
| c311 † | 95 | 87,3% | 100%† | 82,9%† | escopo sweep (55 células) |

† cobertura relativa ao próprio escopo (ondas antigas — lacuna D9 declarada); não comparável ao grid 840.
‡ nsga3 auditado **duas vezes** de forma independente nesta rodada, com concordância integral.

**Como ler:** nenhuma nota <80% é infidelidade — é cobertura (lacunas que você aceitou ao congelar:
b5m/e7 sem reais completos, c154 sem RE21, c238 com o badsubscript censurado) e custódia. A coluna
mecanismo — a fidelidade em si — vai de 85 a 96, e o 8,5 do b4 é o badsubscript alcançando o DDMOP7
(6/29 células), um defeito **upstream** documentado, não da implementação.

## 3. OS 3 PROBLEMAS REAIS

| problema | score | veredito | o essencial |
|---|:--:|---|---|
| **RE21** | 9,3 | ACEITAR | 566 células, fidelidade ≤5,5e-7, régua coerente por 3 vias independentes, **o problema mais pró-surrogate do corpus inteiro** (p≈1e-97) |
| **ESTOQUE40** | 8,5 | ACEITAR + pendências operacionais | query-joia 100% em 488.646 avaliações; D102.19 disparado 60/60; **piso offline VIVO 30/30** (bandeira amarela morta); e81 s22–26 embrionárias → quarentena (A9) |
| **DDMOP7** | 8,5 | ACEITAR como comparação de **resolução declaradamente baixa** | identidades 100%; zona morta cumpriu (front pooled de 6 pontos, **100% vindos da busca**); fase 2 computada: z\*=[1/17; 84/690]; HV separa **classes** (p=4,3e-26) mas não o topo-8 (0,6%) |

## 4. O RESULTADO CIENTÍFICO NOVO (transversal_ciencia.md)

**Nada do F30 cai** — conclusividade 75–80%, blocos {ZDT}≫{BBOB,MMF}≫{WFG,DTLZ}, ranking, tudo
reproduzido dígito a dígito. O que os reais acrescentam é uma **tese nova**:

> **"A família sintética prediz mal o problema real."** A derrota do surrogate fica confinada a
> WFG/DTLZ sintéticos e ao DDMOP7 degenerado; nos dois reais estruturados o surrogate **vence com
> efeito 3–6×** (RE21: 9/12 comparações pró-SA conclusivas; ESTOQUE40: 3/4). Substitui
> "o surrogate perde onde conta".

Mais: ranking agregado **imune aos reais** (A27 idêntico ao A11; Spearman 0,990) — c141 1º
inferencial, c262 1º descritivo; a ablação do σ (b5) ganha seu **primeiro resultado conclusivo — contra**
(ESTOQUE40, par RVEA, p_holm=0,024); a tendência-D morre de vez (ρ=−0,076, p=0,57).

## 5. O PLANO DE CORREÇÃO (transversal_plano.md — cobertura 24/24)

**Zero re-runs necessários.** 4 blocos: **A** (11 reposições de arquivo/censo — quimera do b1,
órfã do c141, 14 ⑥ do c238×EST40, quarentena e81 s22–26, script de correção do censo; todos os
espelhos conferidos íntegros HOJE) · **B** (pós-hoc computável: **B1 a ⑦ do e103** — a análise atual
o exclui SILENCIOSAMENTE, o que é proibido: rodar `final_eval` ou declarar em 1 frase; **B2** a ⑦ do
DDMOP7-offline; **B3** ratificar a fase 2 — recomendação: manter [0;0]/468) · **C** (15 regras de
leitura e erratas — dedup x_efetivo, `params.zona_morta` na rota MATLAB, FE comum por problema,
8 erratas a relatórios anteriores incluindo 2 contra mim) · **D** (caveats prontos, 1 frase cada).

## 6. AS DECISÕES FINAIS DO AUTOR (D97/D81)

1. **B1 — o destino do e103**: rodar a ⑦ (1 sessão, sem re-run) ou declarar fora do endpoint. A exclusão silenciosa atual é a única opção proibida.
2. **B3/C12 — ratificar a régua do DDMOP7** ([0;0]/468, retirar o selo) e sancionar as 17 células s0 pré-errata.
3. **C8 — os orçamentos de FE comum** por problema (denominadores da R4).
4. **C14/D102.8 — o DDMOP7 no ranking**: estratificado por classe de operador (recomendado) ou seção própria.
5. **C6 — declarar o corpus canônico** (M8/T15; os números F5/T11-s42 viram documentação de auditoria, não dado).
6. **A9 — quarentenar e81×EST40 s22–26** (embrionárias, estáticas desde 21/08 — confirmado que PARARAM).
7. **C13 — o recorte do Friedman §15.1** antes da R4.

## 7. ARTEFATOS DESTA RODADA

`f5/final/`: `censo_final.csv` (16.811) · `configs/*.json` (24) · `reais/*.json` (3) ·
`pendencias_{1,2}.json` · `transversal_{ciencia,ruido,plano,contrato}.md` · `notas_finais.csv` ·
este relatório. Métricas recomputadas: `metricas_final.csv` (19.230 linhas) + scripts no scratchpad
da sessão. Histórico completo: `f5/` (F5) · `f5/t11/` · `f5/f30/` · `handoff/T15-*`.

**Encerramento da torre:** cinco exames, ~34 mil células-exame acumuladas, zero bugs de algoritmo.
O que este corpus afirma sobre os 16 algoritmos, ele afirma com o mecanismo provado, o contrato
medido e as lacunas declaradas — que é o que uma banca pode exigir.
