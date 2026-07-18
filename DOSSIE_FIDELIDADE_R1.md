# DOSSIÊ DE FIDELIDADE — Rodada 1 (MATLAB) · validação em lote D97

> **O que é.** O material de apoio para a validação de fidelidade MANUAL do autor (D97), em LOTE,
> ao fim da onda MATLAB — decisão autor+torre de 2026-07-17. **A torre PREPARA a evidência; o
> VEREDITO é do autor** (a assinatura "fidelidade validada" da dissertação é dele).
> **Mantido pela torre**; cresce a cada cartão fechado. Estado: 🟡 ESQUELETO (preenchimento final
> quando a onda fechar: falta c238, pisos, e74, e103).

## Escopo acordado (autor, 2026-07-17)

| # | Item | Status |
|---|---|---|
| 1 | **Curvas de convergência consolidadas** (IGD+ × FE dos 9 algoritmos lado a lado, por problema) + checagem de monotonicidade | 🟡 parcial (6/9 computadas) |
| 2 | **Resumo de mecanismo por algoritmo** extraído dos `.jsonl` (o "filme" que o autor confronta com o pseudocódigo do paper) | 🟡 parcial |
| 3 | **Auditoria linha-a-linha estilo "9→10"** (código patchado × Algoritmos do paper) — para TODOS, não só o c217 | ⬜ na preparação final |
| 4 | **Testes de disparo forçado das guardas nunca-exercitadas** (casos sintéticos: ramos 2/3 do b4, `nzero` do b3, `mse_neg` do b1, `saldo_congelado` do e7, …) | ⬜ na preparação final |
| 5 | **Smoke multi-semente** (semente 42 × 1 problema por algoritmo — estabilidade além da semente 0) | ⬜ na preparação final |
| 6 | Números-guia por algoritmo com os caveats de orçamento (as âncoras J são de orçamentos/dimensões DIFERENTES — comparar MECANISMO, não IGD cru) | 🟡 parcial (abaixo) |

## Estado por algoritmo (o que já está pronto para o seu julgamento)

### c217 PC-SAEA — ✅ FIDELIDADE JÁ ACEITA (9/10, autor, 2026-07-16)
Gestão de confiabilidade operando certo (estados saem de 3 só quando a validação cruza δ=0.8; lote 6
"at most six"; params do paper). **Insight aceito:** sob 31D−1 o surrogate fica majoritariamente
inativo em δ=0.8 = o mecanismo acertando (caveat documentado p/ a dissertação). Pendente aqui: só a
auditoria "9→10" (item 3) se o autor quiser fechar o ponto que falta.

### c141 MMRAEA
- Guia (semente 0): ZDT1 IGD_raw 1,88e-2 (|ND|=104)… *(ver handoff/R1-c141.md §4)*. σ D45 = 2
  componentes (sigma_2 NULL em M=3) verificado pela torre na ③.
- Mecanismo p/ conferir: cascata de 3 níveis (Fit1/2/3), ramo (Q,U) — **ativo em 100% dos ciclos**
  (a expectativa "raro" era de leitura pré-v2.2; conferir com o paper).
- ⚠ Único sem o diagnóstico de comportamento da torre ainda (cartão solo antigo) — entra no item 1.

### b3 K-RVEA
- Guia: ZDT1 IGD+ 1,78e-2 / HV 0,84 (**o melhor ZDT1 do set**, melhora 248×, monotônico) · MMF1 64,9× ·
  **⚠ DTLZ2 = a célula mais fraca do set (HV 0,089, melhora 3,6×)** — mecanicamente correto (ramo
  incerteza 44/48, aritmética v2.2 δ=4,55 confirmada pela torre independentemente), perfil do K-RVEA
  sob 371 FE em M=3 — **ponto de atenção nº1 do seu julgamento**.
- Switch APD×incerteza: APD 100% em M=2 (esperado), incerteza dominante em M=3. |A1|≡NI (Fig. 9).
- Guard `nzero` NUNCA disparou em run real (bit-idêntico provado por probe 20k casos) → item 4.

### b4 CSEA
- Guia: ZDT1 IGD+ 3,96e-1 (melhora 11,2×) · DTLZ2 1,94e-1 (6,1×) · monotônico nos 3.
- Mecanismo: gate de 4 ramos — **só os ramos 1 (confiável) e 4 (inconclusivo→aleatório) dispararam**
  (140/335 no ZDT1); ramos 2/3 NUNCA → item 4 (disparo forçado). Stalls 0-FE (69/16) = design (gate
  L>0.9), logados. n_treino cresce com o arquivo (patch B4.6 em ação).
- Balde C {1,20,1,20} ratificado (protocolo; manifesto/jsonl registram).

### b1 ParEGO
- Guia: ZDT1 IGD+ 3,23e-2 / HV 0,82 (melhora 136,8×) · DTLZ2 9,36e-2 (12,6×) · monotônico.
- Mecanismo: hazard near-dup documentado OPERANDO (490 remoções logadas no ZDT1, sem crash);
  n_treino satura no cap top-(11D−1+25) → curva de fit plana (design). Sem âncora numérica no paper
  (KNO/OKA fora do set) → validação qualitativa via `b1_gen` (λ/min-max/Gbest/e0_trace).
- Guards `mse_neg`/`nan_guard`/`ei_nan` armados, 0 disparos → item 4.

### e7 EDN-ARMOEA
- Guia: ZDT1 IGD+ 4,58e-1 (melhora 9,6×) · DTLZ2 2,19e-1 (5,6×) · monotônico. Convergência lenta =
  perfil do EDN sob 31D−1 (âncora J é d=20, orçamento ≠).
- Mecanismo: **gatilho dual VIVO** — `RatioOld−Ratio ≷ δ=0.05` decidindo convergência 152× /
  incerteza 48× no ZDT1 (aritmética visível e correta nos logs). Dropout 0,1 do paper ativo (D30).
- `saldo_congelado`/`dup_infill` armados, 0 disparos → item 4. RAM pico 3,25 GB (ZDT1) → dado p/ M7.

### c238 EIM
- Guia (semente 0): ZDT1 IGD+ 3,96e-2 / HV 0,80 (|ND|=27; melhora 111,7×, monotônico) · DTLZ2 1,49e-1
  (3º/7 no ranking) · MMF1 6,21e-2 (6º/7, pelotão apertado). IGD_raw da sessão: ZDT1 4,99e-2 · DTLZ2 2,30e-1.
- Mecanismo p/ conferir: assinatura EGO exata (n_treino +1/iter nos 3; q=1); critério EIMe (Euclidean);
  eim_best decai em DTLZ2/ZDT1. **Pontos de atenção:** (1) eim_best RUIDOSO no MMF1 (40 iters; a re-escala
  {min,range} muda por iteração — explicável, confrontar com o paper do EIM); (2) salto tardio do eim_best
  no fim do ZDT1 (~5e-5→1,3e-1 — idem re-escala; o IGD+ seguiu caindo). Guards: 0 disparos em 880 iters.
- Nota de comportamento da torre: **9/10** (encanamento perfeito recomputado do zero; assinatura EGO de
  livro-texto; ranking no perfil esperado; o ponto que falta = confronto mecanismo×paper + os 2 pontos acima).
- ⚠ custo: ZDT1 3h55/run → ~118 h/core p/ 30 sementes (M7).

### pisos ONLINE (nsga2 · nsga3 · moead type=1 · smsemoa) — A RÉGUA do estudo
- **N=20 CRAVADO pelo autor (2026-07-18, provisório até o SUB-varN):** o bundle não pinava N e a
  cadeia era circular (SUB-varN depende de R1-pisos); cravado 20 = valor do Knowles/ParEGO ∩ faixa
  ~20–25 ∩ conjunto {10,20,30,50} da D65; N=100 era infactível em D=2 (pop>DoE de 21). SPEC/§3.2
  tem a justificativa em 4 pontos; a varredura D65 reconfirma ou substitui antes da bateria.
- **Comportamento: monotônico nos 12 runs** (4 pisos × 3 problemas); smsemoa = o piso mais forte
  (2/3 problemas — seleção por HV, esperado); moead o mais fraco no ZDT1 (1,89 — N=20 em D=30).
- **🔬 A RÉGUA (o achado central p/ a dissertação):** SA-MOEAs que batem o MELHOR piso:
  **MMF1 (D=2): 1/7** (só o b1) · **DTLZ2 (D=12): 2/7** (c141, b1) · **ZDT1 (D=30): 6/7** (todos
  menos o c217). **A vantagem do surrogate CRESCE com a dimensão/pressão de orçamento — exatamente
  a tese da literatura SA-MOO.** O c217 abaixo dos pisos no ZDT1 é o caveat já aceito (surrogate
  majoritariamente inativo em δ=0.8). Em D=2 com 61 FE, MOEA puro com N=20 é competitivo (achado
  conhecido). Guias: melhor piso MMF1 smsemoa=4,86e-2 · DTLZ2 smsemoa=1,43e-1 · ZDT1 nsga2=6,12e-1.

### e74 CLMEA · e103 IBEA-MS
⬜ Aguardando os cartões fecharem.

## Como o autor vai usar (o método, igual ao c217)
1. Curvas (item 1): convergência plausível? anomalias por contraste entre os 9?
2. Mecanismo (item 2 + `.jsonl`): cada decisão interna bate com o Algoritmo do paper?
3. Auditoria 9→10 (item 3): o código patchado é o pseudocódigo?
4. Guardas (item 4): os caminhos raros se comportam quando forçados?
5. Estabilidade (item 5): semente 42 não revela nada patológico?
6. Veredito por algoritmo: ACEITAR (com caveats documentados) ou SINALIZAR (vira D81).
