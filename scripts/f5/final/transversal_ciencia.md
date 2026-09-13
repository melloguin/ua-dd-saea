Todas as medições fecharam. Composição do retorno final.

---

# SÍNTESE CIENTÍFICA FINAL — 28 problemas, corpus congelado (recompute integral com `src/metrics.py`, régua nova)

**Método e validação do encanamento (tudo medido nesta sessão):** gate D92 reproduzido ANTES de qualquer número (`hv_smoke_bbob_f1()=1,043327`; sanity 0,833327). Harvest próprio sobre o canônico `/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/` guiado pelo `censo_final.csv`: 16.811 células → 16.790 com ① legível (21 `sem_arquivo`) + 2.420 ⑦. `checa_regua` executado em 100% dos conjuntos: **0 réguas FURADAS**; 730 células com furos TOLERADOS via `avisos_regua` (ZDT6 11.660 pts, pior 1,7e-4 do range — ideal arredondado, achado T15.13b já escalado; MMF4 121 · MMF1 50 · BBOB_F5 15 · MMF11_L 7 · DTLZ1 8 · **RE21 1.514 pts, pior 1,4e-7 = float32 D53**) — reportar junto de qualquer número publicado. Cross-check contra o aceito da F5 (s42): **519/664 idênticas <1e-9; 145 divergentes das quais 132 com `n_nd` mudado** — reproduz exatamente a escalação nº 7 do F30 (s42 superseded nos configs Python), meu encanamento é o mesmo. Políticas: **P1 = ok (12.761 células main)** primária; P2 = ok+teto_wall (13.371); as 158 `checkpoint_em_andamento` fora de ambas (O-21: motivo ambíguo). Ref-sets: BBOB 233–523 pts, RE21 702, EST40 511 (<5000 do §12.2 — resolução declarada; estende a escalação F30 nº 9 aos reais). Teste: Wilcoxon pareado por semente + Holm na família reportada + rope ±5% em razão (registro); ≥20 pares; DDMOP7 só HV (D102.4), score=−HV.

## (1) Contraste surrogate × piso — F30 CONFIRMADO EXATO; os reais mudam a DIREÇÃO, não a taxa

25 sintéticos (P1): **C 234/294=79,6% (91 pró-SA/143 pró-piso) · A 221/294=75,2% (101/120) · B 204/294=69,4% (117/87)** — dígito a dígito o F30. Família: Friedman χ²=31,53 p=2,4e-06, ranks ZDT 1,33·BBOB 2,50·MMF 2,58·WFG 4,17·DTLZ 4,42; post-hoc 8/10 separam, BBOB~MMF (0,353) e DTLZ~WFG (0,677) não — os 3 blocos {ZDT}≫{BBOB,MMF}≫{WFG,DTLZ} seguram. P2: 79,8/75,7/70,0% (estável).

Com os **28**: C 253/320=79,1% · A 240/320=75,0% · B 220/320=68,8% — **a conclusividade 75–80% não se move**. Nos reais (26 comparações sob C): 20 conclusivas (76,9%), **50% pró-SA vs 41,5% no geral**:
- **RE21 = o problema mais pró-SA do corpus inteiro**: 12/12 conclusivas sob C, 9 PRÓ-SA (b1, b3, c122, c141, c238, c262, e7, e74, e81; log2-razão mediana −1,62 ≈ 3,1×; c238 0,0045 vs piso 0,047) e 3 pró-piso (b4, c149, c217).
- **ESTOQUE40** (P1, 4 SA com n≥20): c141/c238/e74 PRÓ-SA conclusivas (log2r até −3,14; e74 0,0066 vs 0,0588), c217 empata (é o modo "nunca dispara" — mede SPEA2, não surrogate). P2: c262 PRÓ-SA conclusivo MESMO truncado a ≤852 FE; c154/c149 pró-piso conclusivos mas **confundidos por orçamento** (⚪ a ~50-70% do FE — não citar como desempenho antes da decisão C8).
- **DDMOP7** (HV): **0 comparações pró-SA**; 5/10 conclusivas pró-piso (b3, c141, e7, e74, e81); c122/c217/c262/b4/c238 empatam no teto degenerado (~0,876).
- Tendência-D: segue não sustentada e piora com os reais (D=4 e D=40 novos): ρ mediano **−0,076**, p=0,569, 3/12 positivos (e81 único individual +0,49 p=0,011 s/correção); dentro-DTLZ ρ=−0,600 p=5,0e-07 (sinal contrário, como no F30).

**Resposta direta: os reais NÃO mudam a taxa de conclusividade; mudam a tese.** A derrota do surrogate fica confinada a WFG/DTLZ sintéticos e ao DDMOP7 degenerado; nos reais estruturados (RE21, EST40) o SA vence com efeito 3–6×. A família sintética prediz mal o real.

## (2) Ranking final com os 28 (recortes declarados)

- **Réplica F30 A11×25**: χ²=84,63 p=6,2e-14, ordem e ranks idênticos (c141 2,92 … moead 9,48).
- **A27 (11 configs × 27, +RE21 +DDMOP7-por-HV)**: χ²=88,58 p=1,0e-14, CD=2,906 — **ordem IDÊNTICA** (c141 3,00 · b3 4,04 · e74 4,52 · smsemoa 4,78 · nsga2 5,54 · nsga3 6,06 · e7 6,22 · b4 7,13 · c217 7,17 · e81 8,00 · moead 9,56). Incluir os reais é inócuo no bloco.
- **A28 completo só existe com 7 configs** (EST40 elimina b3/b4/e7/e81/b1/c122/c262; c238 entra com n=26–29): c141 2,29 · e74 3,14 · smsemoa 3,25 · nsga2 3,79 · nsga3 4,23 · c217 4,91 · moead 6,39 (χ²=65,35 p=3,7e-12, CD=1,703 — c141 separa de nsga3/c217/moead; c141~e74~smsemoa~nsga2 não separam).
- **Descritivo 17×28** (rank entre presentes): c262 3,59 · c141 4,43 · c122 4,74 · b3 6,11 · e74 6,54 · c238 7,12 · b1 7,40 · smsemoa 7,46 · c154 7,62† · nsga2 8,27 · nsga3 8,70 · e7 9,41 · c217 9,91 · b4 10,13 · e81 11,41 · moead 12,54 · c149 14,75. Spearman com o descritivo 25-sint = **0,990**: os reais promovem c238 e c217, rebaixam b3, e nada mais. († c154 = 8 problemas, não comparável; c149 sem DDMOP7 no n≥20 [17 ok]; b1 sem DTLZ4/DDMOP7/EST40 — A53.)

## (3) O DDMOP7 discrimina no HV? — SIM entre classes, NÃO no topo

Amplitude entre medianas (n≥20): **0,1736 = 19,8% do topo** ≫ piso de contraste (1,225%) e ≫ piso de célula (10,6%). Friedman pareado 13×30: χ²=150,58 **p=4,3e-26**. Mas: topo (c217 0,8763 · nsga3 0,8763 · c122 0,8762 · c262 0,8742 · smsemoa 0,8734 · b4/nsga2 0,8726 · c238 0,8708) espremido em **0,6%** ≈ piso de contraste; **96 células ok de 12 configs com o MESMO HV exato 0,876327** (grade 1/17, 1/690); CD Nemenyi=3,331 não separa pares dentro do topo-8 (Friedman só do topo-8 [c217,nsga3,nsga2,c122,c262,smsemoa,c238,e7] p=0,008 — ordenação fraca existe, puxada pela borda). Quem abre a amplitude é a cauda: e74 0,821 · moead 0,819 · e81 0,703 · c149 0,612 (b1 1/30 — dacefit). IQR/mediana: EAs puros 0,4–0,6% vs surrogates 4–8% — **o surrogate adiciona variância aqui**. |ND| bruto infla 49,8% vs x_efetivo (56.790→28.500); F distintos/célula mediana 3, máx 8 — publicar |ND| efetivo + par {HV, melhor-f2} (C1/D102.8 estratificado, confirmado por medição independente). **Fase-2 pooled verificada por mim**: z\*=[1/17; 84/690], nuvem-máx=[1; 593/690] — bit-idêntico ao laudo dos reais; sensibilidade da régua: Spearman(medianas fase-1 × z\*-pooled) = **0,9993** → a decisão de régua não muda ranking (recomendo manter ideal [0;0], nadir 468/690; selo REGUAS_PROVISORIAS até o autor cravar). Offline: ① dos 4 offline com spread **0,0 exato** por semente (empate por desenho) e ⑦ 0/629 → DDMOP7 offline incomputável (B2).

## (4) Ablação b5m × b5r final

- **b5m×b5r** (par do enunciado — que NÃO é a ablação de σ; escalação F30 mantida): ⑦, 25 sintéticos: 12/25 pró-b5m, 6 conclusivas (5/1), global p=0,958; Friedman do trio p=0,852 — **indistinguíveis** (idêntico ao F30). **Nos reais é INTESTÁVEL: b5m não tem RE21/EST40** (teto do corpus congelado).
- Ablação cirúrgica **b5m×moead_media**: 10/25 conclusivas (4/6), global p=0,182 — σ segue não conclusivo nos sintéticos.
- **NOVO — b5r×moead_media com reais (27 problemas)**: 15 conclusivas (8/7), global p=0,400; **ESTOQUE40: pró-moead_media CONCLUSIVO (0,0647 vs 0,0808, p_holm=0,024)** — primeira derrota conclusiva do mecanismo probabilístico num real (b5r com 4 sementes doentes {1,2,16,27}, colapso de pop); RE21 empate vácuo (p=0,557; ambos degeneram a 1–2 pontos).
- fantasia (n_nd⑦/n⑦, minha definição, corpus completo): b5m 0,300 · b5r 0,306 · moead_media 0,340 — assinatura do paper segue não reproduzida. **e103: ⑦ só nas 45 células s42 legadas → fora de todo o quadro offline (B1 pendente: RE21 30 + EST40 29 células vermelhas).**

## (5) O que muda nas conclusões da dissertação vs F30

1. **Nada do F30 cai** — todos os headlines reproduzidos dígito a dígito (conclusividade, famílias, ranking A11×25, ablação, D-trend).
2. **Nova tese central possível**: o padrão de derrota do surrogate é um artefato do benchmark sintético — nos 2 reais estruturados o SA vence com efeito grande (RE21 9/12 pró-SA; EST40 3/4), e no real degenerado (DDMOP7) ninguém vence porque o problema não resolve o topo. "A família prediz mal o real" substitui "o surrogate perde onde conta".
3. **Ranking agregado imune aos reais** (A27 idêntico; descritivo ρ=0,990) — c141 1º inferencial robusto, c262 1º descritivo; a instabilidade continua vindo do CONJUNTO DE PROBLEMAS, não das sementes.
4. **DDMOP7 entra estratificado** (separa classes p=4e-26; topo estruturalmente empatado) — não diluir no agregado fino.
5. **σ do b5 ganha o primeiro resultado conclusivo — contra** (EST40, par RVEA), a ser reportado com a ressalva das 4 sementes doentes.
6. D-trend fica mais morto com D=4/D=40 reais no eixo.

## Escalações (D81) — decisões que NÃO tomei

(i) endpoint misto no ranking (DDMOP7 por HV) — sancionar ou excluir (sensibilidade medida: inócuo); (ii) escolha do comparador A/B/C segue movendo ~10 p.p. (F30 nº 2, aberta); (iii) linhas P2 dos reais de c154/c149/c262/e81 comparam FE desigual — exigem a decisão C8; recomendo P1 como primário; (iv) cravar a fase-2 do DDMOP7 (evidência pooled verificada; recomendação: manter [0;0]/468-690) e retirar o selo; (v) B1 (⑦ e103) e B2 (⑦ DDMOP7) seguem bloqueando o quadro offline completo; (vi) |R|<5000 nos BBOB e reais — declarar resolução do IGD+; (vii) os 730 avisos_regua devem acompanhar qualquer métrica publicada.

**Não medido:** bayesiano de sinais-postos e bootstrap de incerteza (não re-rodados; herdo F30), trajetórias §13, IGDX/attainment, sub-corpus sweep/batch e c311/treed_media/sobol_batch (55/10/8 células — lacuna D9 declarada).

**Artefatos (scratchpad `/private/tmp/claude-501/-Users-gmello/16c0ba84-843b-49d1-9ce6-6cecc418b734/scratchpad/`):** `metricas_final.csv` (19.230 linhas ①+⑦, com regua_flag/n_nd_ef/hv_alt/extremos pooled) · `t1_contraste_{P1,P2}_{sint25,full28}.csv` · `t2_medianas.csv` · `t3_ddmop7_hv.csv` · `t4_*.csv` · `refsets/*.npy` · scripts `build_refsets.py`/`harvest.py`/`analise_sintese.py` · logs `refsets.log`/`harvest.log`/`analise_sintese.out`. READ-ONLY respeitado: nada no repo foi tocado; nenhuma célula executada.