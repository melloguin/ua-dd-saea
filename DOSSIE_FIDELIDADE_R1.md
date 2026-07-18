# DOSSIÊ DE FIDELIDADE — Rodada 1 (MATLAB) · validação em lote D97

> **O que é.** O material de apoio para a validação de fidelidade MANUAL do autor (D97), em LOTE,
> ao fim da onda MATLAB — decisão autor+torre de 2026-07-17. **A torre PREPARA a evidência; o
> VEREDITO é do autor** (a assinatura "fidelidade validada" da dissertação é dele).
> **Mantido pela torre**; cresce a cada cartão fechado. Estado: 🟢 ONDA MATLAB COMPLETA (10/10 cartões) — falta a PREPARAÇÃO FINAL (itens 3/4/5) e o VEREDITO do autor.

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

**Veredito adversarial da torre (2026-07-18) sobre os pisos: 3/3 CONFIRMED** — (1) a semeadura D88
(NDSort+crowding, replicada em Python independente, bate a ② geração 1 EXATA nos 5 runs testados);
(2) a edição N=20 da SPEC íntegra e mínima (5 hunks todos no tema; bundles fiéis; aritmética conferida);
(3) parquets recomputados do zero: init = DoE INTEIRO bit-a-bit nos 12 (a pergunta adversarial central
falhou em refutar). **Nota mantida: 9,5/10.** Caveat p/ o R4: dedup por `solution_id`, nunca pelo X
float32 armazenado (colisões de cast provadas; o orçamento contou certo em float64).

### e74 CLMEA
- Guia (s0): DTLZ2 IGD+ 9,88e-2 (**4º/13, bate o melhor piso**) · ZDT1 9,64e-2 (6º/13, bate) · MMF1
  6,26e-2 (10º — run minúsculo). Monotônico ×3. IGD_raw sessão: DTLZ2 1,177e-1 · ZDT1 9,64e-2.
- Mecanismo: **as 3 estratégias em rotação PERFEITA 211/211/211** no ZDT1 (o ciclo do CLMEA visível);
  dedup ε=1e-5 com 35 slots perdidos no s1 (o "no-op silencioso" previsto na v2.2 — telemetrado);
  desalinhamento máscara×Parent ~8%/ciclo (fix opcional NÃO aplicado — só telemetria, decisão aberta).
- **Isolamento = padrão-ouro do projeto:** 518 basenames colidentes; prova c217→e74→nsga2→b3 no MESMO
  processo + asserts which. Wall leve (ZDT1 485s).
- **Veredito adversarial da torre (2026-07-18): patches CONFIRMED; desvio `ndsort-obj` classificado
  FIEL-EQUIVALENTE (não-violação)** — "preditos" só existia no placeholder do anchors.json; a SPEC
  (precedência D83) manda "NDSort → objetivos"; o stock não tem regressor; o newrbe é interpolação
  EXATA (predito≡real nos pontos do arquivo); o re-sim arriscava crash `randi(0)`. Parquets PARTIAL
  (tudo confirmado — contabilidade 329+2+176+211+211=929 recomputada; ③ 0 violações em 63k linhas;
  isolamento restaura o path INTEIRO, guard armado ANTES dos asserts) **com 1 CORREÇÃO quantitativa:
  o desalinhamento máscara×Parent no ZDT1 é ~24,8%/ciclo (máx 91/100!) — não ~8% (o ~8% era só o
  DTLZ2). ⚠ PONTO PRIORITÁRIO do seu julgamento: com ~25% de desalinhamento, o fix opcional do
  re-sim (não aplicado) merece sua atenção no lote.** Nota torre: **9/10** (mantida).

### e103 IBEA-MS (OFFLINE — o 1º do regime)
- **Regime offline PROVADO:** ① = o dataset (31D−1 bit-exato, CP com x_hash E f_hash — o CP mais forte
  do set); ZERO FE na busca (violação = pára-e-loga armado, nunca disparou). O run MAIS LEVE da R1
  (ZDT1 37s; 30 sementes ≈ 19 min/core).
- Mecanismo: **o fix D93 DISCRIMINA de verdade** — KFlag=1 (Kriging líder) 99/99 gerações no ZDT1
  (f₀=x₁ interpola exato, σ²~e-32) e 0/99 em MMF1/DTLZ2 (gate 3σ reprova → RBFN); o **decay dos
  membros reais** instrumentado (ZDT1: 82→0, somem na g5 — o "erro de fantasia" em câmera lenta,
  cruzável ③×①). Confronto com o paper no lote. Nota torre: **9,5/10**.
- ⚠ âncora J (ZDT1 4,596e-3) NÃO comparável (setup do paper ≠). Decisão aberta: persistência da
  avaliação REAL do ND final (§11/B7.5) — ANTES do R3.

### R2 — c262 qNEHVI (fora da onda MATLAB, mesmo método de dossiê)
- **O MELHOR do set: 1º/13 nos TRÊS problemas.** ZDT1 IGD+ **7,8e-4** (melhora 5.668×!), HV 0,875,
  |ND|=345. Monotônico ×3. 22 cache-hits D89 no ótimo convergido (29/30 coords clampadas = convergência
  real). Custo: busca domina (89–98%); ZDT1 4h11 → ~5,2 dias·core p/ 30 sementes (M7).
- **Achado S.3#9 CONFIRMADO adversarialmente:** o wheel oficial CONTÉM o `logei_fused.cpp`
  (byte-identidade instalado×wheel VERIFICADA: sha256 dos 494 arquivos do RECORD, 0 divergências);
  o desligamento DEF-L2 é efetivo (`_load_attempted=True` + `_C=None` antes de qualquer acqf). ⚠ é
  estado POR PROCESSO → todo runner BoTorch repete a política (c154 já instruído; despachante M8 idem).
- **Parquets PARTIAL (precisões, 0 defeitos):** contabilidade FE recomputada FECHA (929 = 329 init +
  622 iters − 22 cache-hits); os 22 hits = canto de Pareto x=(1,0,…) bit-exato (D89 legítimo); a ③
  tem 9 NULLs/geração por DESENHO (restarts não-escolhidos) + 1 do hard-stop; curva n^2,28 (ZDT1) e
  n^1,97 (DTLZ2) — MMF1 plano (overhead, esperado). Nota p/ análise: corr(mu_1,f1) fraca no MMF1
  multimodal (−0,155; orientação correta) — qualidade preditiva, não bug. Nota torre: **9,5/10**.

## Como o autor vai usar (o método, igual ao c217)
1. Curvas (item 1): convergência plausível? anomalias por contraste entre os 9?
2. Mecanismo (item 2 + `.jsonl`): cada decisão interna bate com o Algoritmo do paper?
3. Auditoria 9→10 (item 3): o código patchado é o pseudocódigo?
4. Guardas (item 4): os caminhos raros se comportam quando forçados?
5. Estabilidade (item 5): semente 42 não revela nada patológico?
6. Veredito por algoritmo: ACEITAR (com caveats documentados) ou SINALIZAR (vira D81).
