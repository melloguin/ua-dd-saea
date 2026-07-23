# DOSSIÊ DE FIDELIDADE — Rodada 1 (MATLAB) · validação em lote D97

> **O que é.** O material de apoio para a validação de fidelidade MANUAL do autor (D97), em LOTE,
> ao fim da onda MATLAB — decisão autor+torre de 2026-07-17. **A torre PREPARA a evidência; o
> VEREDITO é do autor** (a assinatura "fidelidade validada" da dissertação é dele).
> **Mantido pela torre**; cresce a cada cartão fechado. Estado: 🟢 ONDA MATLAB COMPLETA (10/10 cartões) — falta a PREPARAÇÃO FINAL (itens 3/4/5) e o VEREDITO do autor.

## Escopo acordado (autor, 2026-07-17)

| # | Item | Status |
|---|---|---|
| 1 | **Curvas de convergência consolidadas** (IGD+ × FE, todos lado a lado) + monotonicidade | ✅ **FEITO** (15 configs × 3 problemas; 0 violações de monotonicidade — tabela abaixo) |
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
  desalinhamento máscara×Parent **~24,8%/ciclo no ZDT1 (máx 91/100)** — o ~8% era só o DTLZ2 (fix opcional NÃO aplicado — só telemetria; ponto PRIORITÁRIO do julgamento em lote, DI-07b).
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

## 📊 ITEM 1 — CURVAS CONSOLIDADAS (torre, 2026-07-19) — **os 15 configs lado a lado**

Recomputado do zero pela torre (semente 0; IGD+ normalizado D69/D70 · HV · melhora = IGD+ inicial ÷ final):

| config | tipo | MMF1 (D=2) | DTLZ2 (D=12) | ZDT1 (D=30) |
|---|---|---|---|---|
| `c262` | SA | 3.90e-02 · HV 0.79 · 96× | 2.97e-02 · HV 0.73 · 40× | 7.80e-04 · HV 0.87 · 5668× |
| `c154` | SA | 6.43e-02 · HV 0.74 · 58× | 1.48e-01 · HV 0.36 · 8× | — |
| `c141` | SA | 7.50e-02 · HV 0.72 · 50× | 3.65e-02 · HV 0.72 · 32× | 1.44e-02 · HV 0.85 · 306× |
| `b1` | SA | 4.74e-02 · HV 0.78 · 79× | 9.36e-02 · HV 0.52 · 13× | 3.23e-02 · HV 0.82 · 137× |
| `b3` | SA | 5.75e-02 · HV 0.76 · 65× | 3.28e-01 · HV 0.09 · 4× | 1.78e-02 · HV 0.84 · 248× |
| `c238` | SA | 6.21e-02 · HV 0.75 · 60× | 1.49e-01 · HV 0.41 · 8× | 3.96e-02 · HV 0.80 · 112× |
| `e74` | SA | 6.26e-02 · HV 0.74 · 60× | 9.88e-02 · HV 0.56 · 12× | 9.64e-02 · HV 0.72 · 46× |
| `b4` | SA | 5.32e-02 · HV 0.75 · 70× | 1.94e-01 · HV 0.31 · 6× | 3.96e-01 · HV 0.26 · 11× |
| `e7` | SA | 4.90e-02 · HV 0.76 · 76× | 2.09e-01 · HV 0.37 · 6× | 4.58e-01 · HV 0.27 · 10× |
| `c217` | SA | 6.04e-02 · HV 0.74 · 62× | 2.31e-01 · HV 0.24 · 5× | 7.02e-01 · HV 0.04 · 6× |
| `e103` | SA | 8.38e-02 · HV 0.70 · 39× | 4.57e-01 · HV 0.06 · 2× | 2.10e+00 · HV 0.00 · 3× |
| `smsemoa` | **piso** | 4.86e-02 · HV 0.76 · 77× | 1.43e-01 · HV 0.42 · 8× | 6.90e-01 · HV 0.08 · 6× |
| `nsga3` | **piso** | 5.32e-02 · HV 0.76 · 70× | 1.93e-01 · HV 0.30 · 6× | 7.47e-01 · HV 0.04 · 6× |
| `moead` | **piso** | 6.29e-02 · HV 0.74 · 59× | 3.10e-01 · HV 0.25 · 4× | 1.89e+00 · HV 0.00 · 2× |
| `nsga2` | **piso** | 6.49e-02 · HV 0.74 · 57× | 3.11e-01 · HV 0.12 · 4× | 6.12e-01 · HV 0.13 · 7× |

- **MMF1**: melhor piso = `smsemoa` (4.86e-02) · **SA que o batem: 2/11** → `c262`, `b1`
- **DTLZ2**: melhor piso = `smsemoa` (1.43e-01) · **SA que o batem: 4/11** → `c262`, `c141`, `b1`, `e74`
- **ZDT1**: melhor piso = `nsga2` (6.12e-01) · **SA que o batem: 8/10** → `c262`, `c141`, `b1`, `b3`, `c238`, `e74`, `b4`, `e7`


### 🔎 As 3 leituras que saltam da tabela

**(1) MONOTONICIDADE: 15/15 configs, 3/3 problemas, ZERO violações.** Todos os runs convergem de
forma monotônica nos checkpoints. É o teste de sanidade mais básico do pipeline — e passa limpo.

**(2) A RÉGUA — a vantagem do surrogate CRESCE com a dimensão** (o achado central p/ a dissertação):
SA-MOEAs que batem o MELHOR piso: **MMF1 (D=2): 2/11** → **DTLZ2 (D=12): 4/11** → **ZDT1 (D=30):
8/10**. Em D=2 com 61 avaliações, um MOEA puro com N=20 é competitivo (achado conhecido da
literatura); sob 929 avaliações em D=30, o surrogate domina. **É exatamente a tese da literatura
SA-MOO reproduzida nos seus dados.**

**(3) O ranking é ESTÁVEL entre problemas** — `c262` (qNEHVI) é 1º nos três; `c141`/`b1` sempre no
pelotão de frente; `c217`/`e103` sempre atrás. Ranking estável entre problemas independentes é
evidência de que o pipeline mede o algoritmo, não ruído.

### ⚠ Pontos de atenção p/ o seu julgamento (não são bugs — são o que MERECE olhar)
- **`e103`/ZDT1 (IGD+ 2,10 · HV 0,00 · melhora 3×)** e **`moead`/ZDT1 (1,89 · HV 0,00)** são as duas
  células mais fracas do estudo. O e103 é OFFLINE (busca 100% no surrogate, zero FE de correção) e o
  moead é piso com N=20 em D=30 — ambos explicáveis, mas confirme o mecanismo nos `.jsonl`.
- **`b3`/DTLZ2 (HV 0,09)** — já registrado como ponto nº1 (o ramo incerteza domina em M=3).
- **`c217`/ZDT1 (HV 0,04)** — o caveat que você já aceitou (surrogate inativo em δ=0,8).
- **`c154`/ZDT1 ausente** — abortado pelo teto de 8h (~96 h projetadas); decisão de orçamento no M7.

## Como o autor vai usar (o método, igual ao c217)
1. Curvas (item 1): convergência plausível? anomalias por contraste entre os 9?
2. Mecanismo (item 2 + `.jsonl`): cada decisão interna bate com o Algoritmo do paper?
3. Auditoria 9→10 (item 3): o código patchado é o pseudocódigo?
4. Guardas (item 4): os caminhos raros se comportam quando forçados?
5. Estabilidade (item 5): semente 42 não revela nada patológico?
6. Veredito por algoritmo: ACEITAR (com caveats documentados) ou SINALIZAR (vira D81).

---

## Item 2-bis — NOTAS DE COMPORTAMENTO v2 (torre, 2026-07-22 — pós-retrofit COMPLETO)

**O que mudou vs a v1 (DI-20.4):** a v1 foi medida com 4 configs SEM sonda, o c217 sem `sigma_dict`
e o e103 sem a ⑦ — três lacunas que puxavam nota para baixo por FALTA DE DADO, não por
comportamento. Agora **todos os 16 têm a instrumentação completa** e as notas medem SÓ o
comportamento do mecanismo (workflow de 5 analistas, ~514k tokens, leitura de ①②③④⑤⑥⑦ + gabarito
da sonda; join posicional validado em TODOS os blocos analisados). Rubrica: 10 = o mecanismo se
comporta exatamente como o esperado; <7 = algo concretamente errado. 1 semente — as notas baixas
se sustentam em evidência MECÂNICA, não em ranking.

| Nota | Config | Movimento vs v1 | Por quê (síntese; detalhes na resposta da torre de 2026-07-22) |
|---|---|---|---|
| 10 | nsga2 · nsga3 · smsemoa | ↑ | pisos IMPECÁVEIS: monotonia (0 regressões nsga3/smsemoa), turnover real, falham só onde a literatura diz (crowding em M=3) |
| 9,5 | c262 | = | GP aprende (WAPE −39/−45%), calibração 0,978, acqf decai — assinatura completa; 1º nos 3 problemas |
| 8,5 | b1 | = | bate os 4 pisos nos 3; sonda ESCALAR (D47) reconstruída e sadia; desconto: sobreconfiança tardia (cobertura 2σ→0,5) |
| 8,5 | b4 | ↑↑ (6,5) | a sonda REFUTOU o "não discrimina": AUC 0,75 (ZDT1, máx 0,92) e APRENDE no DTLZ2 (0,53→0,70, ρ=0,80 c/ treino); vence os 4 pisos no ZDT1 |
| 8,5 | e103 | ↑↑↑ (4,0) | a ⑦ nova prova: IGD+ **0,0057** no ZDT1 (ganho 99,7% sobre o dataset — melhor endpoint do painel); a "fuga do dataset" era o modelo certo agindo certo (WAPE 2,2%, cobertura 0,956) |
| 9,0 | e81 | (novo, DI-24) | qPOTS exemplar por mecanismo: GP aprende limpo (MAE out-of-sample cai monotônico nos 3), infills DIVERSOS (2,5-5,6% no bordo — o anti-c149), ganhos 32-53% sobre o DoE, MMF1 bate TODOS os pisos; ressalvas: MMF1-obj1 superconfiante (sin-ridge, <60 pts) e ZDT1 estagna nos 40% finais (natureza do qPOTS em 30-D: GP com WAPE<1% + front grosseiro = o gargalo é a aquisição) |
| 8,0 | c122 | (novo) | bate os 4 pisos em DTLZ2/ZDT1 (35× o melhor piso no ZDT1); e(z) correlaciona com dominância real (ρ 0,72-0,75) e satura POR VITÓRIA; fraqueza real só no MMF1 (ρ→0,04, confiança=1,0) |
| 8,0 | e74 | ↑ (7,5) | único que bate os 4 pisos no DTLZ2; as 3 cabeças medidas pela 1ª vez: RBF afiada perto do arquivo, mas EXPLODE fora do suporte (mu até 770; f_true máx 8,6) e o PNN INVERTE no fim do ZDT1 (ρ −0,34) |
| 7,5 | c238 | ↑ (7,0) | sonda nova: APRENDE e calibra no DTLZ2 (WAPE f2 8,1→0,9%, cobertura →0,95); degeneração numérica real no fim do MMF1 (mu até 339, θ no bound) e perde de 2 pisos lá |
| 7,0 | e7 | ↑ (6,0) | mecanismo decisório fiel (152 conv/48 incerteza, 0 stalls); mas a sonda PROVA que o ensemble NÃO aprende globalmente (DTLZ2 WAPE 21,8→26,4%) — esquecimento induzido pelo SelectTrainData — e o σ do dropout é otimista (cobertura 0,37-0,41) |
| 6,0 | b3 | ↓ (6,5) | a dissociação agora tem MECANISMO: no DTLZ2 sonda PLANA (WAPE 14% fixo com treino ×3) + switch preso 44/48 no ramo incerteza = ciclo vicioso exploração→modelo-não-melhora; empata com o pior piso |
| 6,0 | c154 | ↓ (7,5) | o achado-de-ouro é DEFEITO real: ruído inferido ×90 (it30-37) → pior E mais confiante (cobertura 0,936→0,758) com busca estagnada; perde de pisos nos 2 problemas; acqf frágil (241/241 warnings) |
| 6,0 | c217 | ↑ (4,5) | o `sigma_dict` novo RESOLVEU o flag (`pred_confianca` constante = Error1 do modelo, DESENHO); o score tem sinal (295/295 blocos direção certa no ZDT1) mas o gate δ=0,8 quase nunca abre → EA ~aleatório que perde do nsga2 |
| 5,0 | c141 | ↑ (4,0) | divergência do RBF no MMF1 CONFIRMADA bloco a bloco (mu → [−145,210], MAE ×8,5, spearman ~0,05) e abaixo dos 4 pisos lá; MAS é o MELHOR dos 7 em DTLZ2 (0,0392) e ZDT1 (0,0144) — e o ZDT1 já mostra o início da mesma deriva |
| 4,0 | moead | = | régua quebrada no ZDT1 (T=2 → clonagem → 23% duplicatas, HV=0, perde a melhor solução do seed) e REGRIDE no MMF1 (−65% vs DoE); ok só no DTLZ2 |
| 7,0 | b5r | (novo, DI-27/28) | Prob-RVEA offline (mode 7; **v3 média-MC RATIFICADA como a variante do estudo — DI-28.1**): progride sem colapso nos 3 e mantém espalhamento; convergência PARCIAL (ZDT1 dist 0,55 à frente analítica, f1 trava em ≥0,18) — o "seguro-mas-mediano" honesto |
| 5,0 | b5m | (novo, DI-27) | Prob-MOEA/D offline (mode 72, MC-pareada quase-fiel): colapso de canto no DTLZ2 (nd 6/105; o GP do obj-2 degenera μ≈0 — reversão à média fora do suporte) e ZDT1 estaciona longe (dist 1,52; nenhum ponto alcança a frente); dado HONESTO — comportamento do operador sob dataset offline |
| 7,5 | c311 | (novo, DI-27) | TGPR-MO offline: o MELHOR offline no ZDT1 (dist **0,0012**, frente completa 50/50 ND) e construção incremental viva (n_acumulado 40→122; 2 blocos de sonda bit-idênticos = modelo fixo na fase final); fraco só no MMF1 de dataset 61 pts (nd 10/46, extrapola além do suporte) |
| 9,0 | moead_media | (novo, DI-29) | O piso da ablação D77, "b5 sem σ" — e a régua FUNCIONA: mesmo motor/surrogate/orçamento/reticulado do b5m, mudando SÓ a seleção. ZDT1: piso dist 0,179 vs b5m 1,52 (a maquinaria probabilística ATRAPALHA 8,5×); DTLZ2: piso espalha (nd 53/105) onde o b5m colapsa (6/105); MMF1: inverte (b5m mais diverso, 21 vs 8 nd). Turnover: 8,5%/ger (conservador) vs 98%/ger do b5m (hiperativo guiado por σ) |
| ⚠ | b5m/DTLZ2 | (flag D97, DI-29) | O GP do obj-2 é DEGENERADO (μ≈0 constante, corr 0,006 c/ f real de std 0,588) enquanto o piso, com a MESMA especificação e MESMOS dados, ajusta corr 0,992 — sensibilidade à semente do treino único (n_restarts consome o global; alg_id 18≠21). Dado honesto; quebra o contraste da ablação NESSE problema. Recomendação: aceitar + caveat (decisão do autor no lote D97) |

**Uso no julgamento D97:** as notas ≠ fidelidade. b3/c154/c217/c141/moead têm comportamento
concretamente ruim POR MECANISMO FIEL (stock honesto sob nosso orçamento) — a decisão de aceitar/
sinalizar é sua; a evidência mecânica de cada linha está pronta para o veredito.
