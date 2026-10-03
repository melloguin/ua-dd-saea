# Catálogo de análises candidatas — Capítulo 5 (Resultados Experimentais e Análise)

**Versão 1 · 06/09/2026 · 64 candidatas** · Documento-chave do processo de decisão da lista definitiva de análises do cap. 5.
Autor do processo: Guilherme de Mello Nunes (PPGCC/UFMG; orientadora Gisele Lobo Pappa). Redação desta versão: agente de sessão (Cowork), a partir da mineração de 06/09/2026 e das três planilhas do processo seletivo (piloto de 10 artigos; 38 artigos; 38 artigos × SPEC v3.3).

---

## 0. Propósito, regras e como ler

### 0.1 Propósito

Este documento é o **histórico único** das análises de resultados candidatas ao capítulo 5. Cada candidata recebe uma ficha exaustiva: o que é, de onde veio, o que analisa, que dados usa, como se faz, como se implementa no nosso pipeline, em quantos artigos do corpus aparece, e o que ainda pede de decisão. Ele **não decide nada**: a triagem (quais entram), as regras (métricas, testes, políticas de cobertura) e o encaixe no texto são decisões do Guilherme, tomadas depois do entendimento profundo de cada ficha. O documento existe para que nada do que foi minerado se perca entre sessões e para que a lista definitiva seja auditável — cada análise escolhida poderá apontar a ficha que a justifica.

### 0.2 Regras do documento

1. **Numeração fixa.** As candidatas 1–64 não mudam de número nem de nome curto. Candidatas novas (da mineração dos 15 do roster e dos 15–20 dirigidos) entram como 65, 66, … no grupo que lhes couber.
2. **Atualização aditiva e datada.** Nada é reescrito; correções e acréscimos entram como blocos datados dentro da ficha ("Adendo dd/mm") e no histórico ao fim do documento. Se uma ficha for superada, ela recebe a marca "SUPERSEDIDA por N" e permanece.
3. **Proveniência obrigatória.** Toda fonte citada traz localizador (arquivo e seção/linha/célula). Os números citados foram lidos nas fontes indicadas nesta sessão (censo, torre de validação, notebook, planilhas, registros); nenhum foi derivado por subtração ou estimativa. Onde um número é da torre (22/08) e não do notebook (17/08), isso está dito.
4. **Contagens "de 38".** Os campos "em quantos artigos aparece" usam as planilhas do processo seletivo, que cobrem **38 dos 127 artigos classificados** (aba Cobertura). As ordens tendem a se manter com a mineração seguinte; as magnitudes crescem. A tipologia é a do "Ranking 2" (25 tipos de análise); quando a candidata não corresponde a um tipo do Ranking 2, o campo diz "0/38 como tipo nomeado" e aponta o tipo mais próximo.
5. **O catálogo não decide.** O campo "decisões que pede" apenas nomeia a decisão; não a recomenda.
6. **Vocabulário.** Nas fichas usa-se a linguagem interna (IDs b3, c141, camadas ①–⑦, códigos OV/AV etc.) porque o documento é de trabalho. Na prosa da dissertação valem as travas do contrato (sem IDs internos, "eixo de classificação", "classe", "medição").

### 0.3 Legenda

**Estado** — F = feita na leva de 17/08 e publicada no retrato do cap. 5 · F-parcial = feita em parte · T = computada pela torre de validação em 22/08, fora do notebook · N = não feita · L = lacuna de dado (a bateria congelada não tem o insumo, ou só tem em uma semente) · R = regra ou nota, não é análise.

**Camadas (contrato de dados, 1 célula = 1 execução algoritmo × problema × semente):** ① `__real.parquet` (toda avaliação verdadeira: x, f, fe_index, fase, solution_id — fonte única das métricas oficiais) · ② `__pop.parquet` (pertencimento população × geração) · ③ `__surrogate.parquet` (toda predição do modelo, regimes busca/sonda/sonda_estratificada; μ/σ ou classe/score; fe_treino_max) · ④ `__timing.parquet` (por geração: tempo_fit_s, tempo_busca_s, tempo_pred_sonda_s, tempo_geracao_s sem a sonda, n_acumulado) · ⑤ `.manifest.json` (status, campanha_id, fe_final, n_geracoes, sigma_dict, timing agregado) · ⑥ `.jsonl` (o filme das decisões, um evento por linha) · ⑦ `__final.parquet` (só offline: ND final reavaliado na função verdadeira; nd_pos_real). Insumos fora das camadas: **S** = gabarito da sonda (`data/sonda/sonda_{problema}.parquet`, 2.000 pontos Sobol com f verdadeiro; 20.000 no offline; DDMOP7 sem sonda) · **C** = caches do notebook (`data/analysis_cache/*_2026-08-17.*`) · **M** = metadados (`characteristics.csv`, `censo_final.csv`, `F_MIN_MAX`/réguas do `metrics.py`, `_contagem_seeds_por_algoritmo_problema.xlsx`).

**Siglas de fontes:** [PL-38] planilhas `analises_experimentais_38artigos.xlsx` e `..._38art_SPECv3.3.xlsx` (R1#n = linha n do Ranking 1; R2#n = linha n do Ranking 2; abas Métricas, Testes, Cobertura, Plano) · [PL-10] planilha piloto de 10 artigos · [NB] notebook `ua-dd-saea/4. analises_resultados.ipynb` (célula [n] ou §) · [CAP5] `chapters/05-resultados.tex`, retrato de 17/08 · [CAP4] `chapters/04-procedimentos.tex` (linha) · [CAP1] `chapters/01-introducao.tex` (prosa comentada) · [ESQ] `SPEC/dissertacao/esqueleto_v10.md` (bloco do cap. 5, l.745–762) · [PC5] `planos/plano_cap5_resultados.md` · [PC6] `planos/plano_cap6_conclusao.md` · [P37] `planos/plano_3_7_cruzamentos.md` · [CHK] `planos/checklist_qualidade_banca.md` · [DIA] `planos/diario_escrita.md` (adendos de 17/08) · [REG] `registro/registro_decisoes.md` (dNN) · [RDI] `ua-dd-saea/REGISTRO_DECISOES_IMPLEMENTACAO.md` (parte/linha) · [DOS] `ua-dd-saea/DOSSIE_FIDELIDADE_R1.md` (§D9 = as 5 conclusões vinculantes; item 2-bis = notas de comportamento) · [RF] `f5/final/RELATORIO_FINAL_DEFINITIVO.md` · [TC] `f5/final/transversal_ciencia.md` · [TP] `f5/final/transversal_plano.md` · [CD] `ua-dd-saea/CONTRATO_DE_DADOS.md` (§10 regras R4) · [R4] `claude_code_context/50_analise_R4/metricas_estatistica_caracteristicas.md` · [MET] `ua-dd-saea/src/metrics.py` · [CEN] `f5/final/censo_final.csv` (16.811 células) · [HO] `SPEC/handoff/HANDOFF_ESCRITA_CAPS_4_5_15-08-2026.md` e `HANDOFF_TORRE_CAPS_4_5.md`.

### 0.4 O que as planilhas dos 38 contam (resumo para leitura das fichas)

Ranking 2 — tipos de análise e nº de artigos (de 38): (1) visualização da fronteira 27 · (2) custo computacional 26 · (3) ablação/contribuição de componente 26 · (4) tabela de qualidade final + significância 26 · (5) curvas de convergência 22 · (6) estudo de caso/aplicação real 20 · (7) análise por característica do problema 19 · (8) escalabilidade em D e/ou M 19 · (9) sensibilidade de hiperparâmetro 18 · (10) acurácia/calibração da incerteza do surrogate 16 · (11) análise teórica 13 · (12) outras/mistas 12 · (13) varredura de tamanho de amostra offline 7 · (14) material suplementar mencionado 6 · (15) coordenadas paralelas 4 · (16) in-sample vs fora-da-amostra/etapa de decisão 3 · (17) ilustração conceitual 3 · (18) sensibilidade ao ruído 3 · (19) sensibilidade ao lote 2 · (20) validação de estimador numérico 2 · (21) comparação vs heurística forte não-BO (piso) 1 · (22) diagnóstico do valor das amostras selecionadas 1 · (23) restrição/preferência 1 · (24) hipervolume generalizado 1 · (25) teste agregado/ranking Friedman-Bayes-CD 1.

Métricas (de 38): HV 23 · IGD 16 · tempo/wall-clock 14 · RMSE/MAE do surrogate 12 · ε-indicator 5 · IGD+ 3 · contagem vitórias/empates/derrotas 3 · spacing/spread 3 · ECE 2 · GD 2 · R2-indicator 2 · regret 2 · taxa de acerto do classificador 2 · ACE, AUCE, Brier, CICP, cobertura empírica de IC, MCE, NLPD, Spearman, STD da variância estimada: 1 cada.

Testes (de 38): nenhum teste formal (só média±dp/SEM) 17 · Wilcoxon rank-sum 16 · Friedman + pós-teste 3 · Bayesian signed-rank com ROPE 1 · Kruskal-Wallis 1 · sistema de pontuação +1/0/−1 1 · teste F de variâncias 1 · Wilcoxon signed-rank pareado 1 · correção múltipla Holm/Bonferroni 1.

Achado transversal das planilhas (Leia-me): há um **split por comunidade** — artigos EA/PlatEMO usam IGD/IGD+ + Wilcoxon/Friedman + tabela final; artigos BO/BoTorch usam só hipervolume (log-regret) + média±erro-padrão, sem teste formal. Nos 38, "nenhum teste formal" (17) supera o Wilcoxon (16).

Dos 15 algoritmos do roster, **8 estão entre os 38** (b1, b3, b4, b5, c154, c262, e7, e103) e **7 não** (c122, c141, c149, c217, c238, e74, e81) — os 7 da Etapa 1b.

### 0.5 A bateria (referência fixa para as fichas)

Roster: 15 algoritmos (13 online: b1 ParEGO, b3 K-RVEA, b4 CSEA, c122 θ-DEA-DP, c141 MMRAEA, c149 LBN-MOBO, c154 JES, c217 PC-SAEA, c238 EIM, c262 qNEHVI, e7 EDN-ARMOEA, e74 CLMEA, e81 qPOTS; 2 offline: b5 Prob-RVEA/Prob-MOEA/D, e103 IBEA-MS) + pisos (NSGA-II, MOEA/D, NSGA-III, SMS-EMOA online; MOEA/D-média offline) = 21 configurações analisadas (o censo tem 24 diretórios: + c311, treed_media, sobol_batch, só s42). Problemas: 25 sintéticos (ZDT1/3/4/6; DTLZ1/2/3/4/7; WFG1/2/4/5/9; MMF1/4/11_L/16_20; BBOB F1/F5/F17/F22/F37/F49/F55) + RE21, DDMOP7 (zona morta τ=0,5; HV-only), ESTOQUE40. Sementes: 30 ({0–28, 42}). Orçamento 31D−1 (DoE 11D−1 compartilhado; 20D infills); pisos N=20; teto de parede 12 h só na rota Python. Casamento SA × piso (D25): b4, c217, e74, c141, c238 → NSGA-II; b3, c122, b1 → MOEA/D; e7 → NSGA-III; c262 → SMS-EMOA; c154, e81, c149 → banda dos 4 pisos. Métrica primária IGD+ (D70), normalização ideal/nadir por problema (S.5), HV com referência 1,1 por coordenada (D69), fronts empíricos para BBOB/RE21/EST40 (D72). Censo canônico (22/08): 16.811 células, 16.021 ok / 790 failed; 615 células no teto de parede; primeiras análises só com células a orçamento pleno (16.020), por decisão do autor (C8 parcial).

---

## Template da ficha

Cada ficha tem os campos: **Nome** · **Fontes** (onde aparece, com localizador) · **O que analisa** · **Dados** (camadas ①–⑦ e insumos S/C/M) · **Objetivo** · **O que busca revelar** · **Como é realizada** · **Técnicas** · **Implementação** (no nosso pipeline) · **Em quantos artigos aparece** (dos 38) · **Estado** · **Demais detalhes** (caveats vinculantes, decisões que pede, encaixe provável no texto, relação com outras fichas).

---

# Grupo A — O placar: desempenho final e comparação global

### 1. Matrizes de mediana do IGD+ e do HV, algoritmo × problema

**Fontes.** [NB] §4, célula [9] (funções `medianas` e `heat`; figs. `fig51_matriz_igdplus`, `fig52_matriz_hv`) · [CAP5] §5.2 "As matrizes de desempenho" (`sec:matrizes-desempenho`, figs. 5.1 e 5.2; Apêndice B com a tabela célula a célula) · [PL-38] R1#1 (score 9,5) e R2#4 · SPEC L367 (cor normalizada por linha) · [PC5] plano do cap. 5 (§5.2) · [TC] (ranking descritivo).

**O que analisa.** O desempenho final de cada configuração em cada problema: a mediana, sobre as sementes, da métrica de endpoint (IGD+ e HV) calculada sobre o conjunto não-dominado de todas as avaliações verdadeiras da célula. É o "quem entrega o quê, onde" — o substrato factual de todas as leituras seguintes.

**Dados.** ① (F de todas as avaliações reais da célula → ND → métricas); ⑦ no regime offline (o endpoint offline é a ⑦, nunca a ① — DOSSIÊ §D9.2); M (réguas ideal/nadir `F_MIN_MAX`; fronts de referência; DDMOP7 só HV); C (`metricas_endpoint_snapshot_2026-08-17.csv`, 16.202 linhas: exp, alg, problema, semente, igd_plus, hv, igd, gd, spacing, n_nd, n_aval, erro, selo).

**Objetivo.** Ser a base auditável de "quem ganha onde", de onde saem as leituras por característica, por classe e por família. Sozinha é catálogo; por isso é tratada como base, não como clímax (R1#1).

**O que busca revelar.** A distribuição do desempenho pela grade: onde cada algoritmo é forte, onde é fraco, onde os pisos competem, e a heterogeneidade entre famílias de problemas (que a torre chamou de blocos {ZDT} ≫ {BBOB, MMF} ≫ {WFG, DTLZ}; ficha 6).

**Como é realizada.** Uma célula por (algoritmo × problema) com a mediana do IGD+ (e, em matriz separada, do HV) sobre as sementes válidas; cor normalizada por linha (o problema é a régua), para que a leitura seja "quem é melhor NESTE problema"; número de sementes < 30 impresso em vermelho na célula; hachura onde não há dado. Linhas separadas por família de problema (ZDT / DTLZ / WFG / MMF / BBOB / reais). Pisos à direita, separados por linha vertical. O DDMOP7 só entra na matriz de HV (não tem IGD+ — problema sem front de referência).

**Técnicas.** Mediana por célula (robusta; o corpus usa média±dp, mas a mediana é o endpoint D70); IGD+ (métrica primária, corrige o artefato de dominância do IGD) e HV (convergência + diversidade + extensão num número); normalização de cor por linha; mapa de calor.

**Implementação.** Por célula: `metrics.metrics_of_set(F_raw, problema)` → normaliza f′ = (f − ideal)/(nadir − ideal) com `reference_bounds`, extrai o ND (`nondominated_front`), calcula IGD+ contra `reference_set(problema)` (front analítico, ou empírico D72 para BBOB/RE21/EST40), HV contra a referência 1,1 por coordenada, e ainda igd, gd, spacing, n_nd. O gate D92 (`hv_smoke_bbob_f1() = 1,0433`) é conferido antes ([NB] §2). O `checa_regua` (T15.13b) tolera furos ≤ 1e-3 do range e registra `avisos_regua`. O notebook lê o CSV de endpoint (com `fillna("")` antes de filtrar `erro == ""` — aprendizado 25 do diário), filtra `exp == "main"` para online e `exp == "off"` para offline, e monta as matrizes com `medianas(base, metrica, algs, problemas)`; `heat()` desenha. Figuras vão para `dissertacao/figures/`.

**Em quantos artigos aparece (dos 38).** A forma tabular "qualidade final por algoritmo × problema" é R2#4: **26/38**. A variante em mapa de calor com cor por linha não foi contada separadamente. Métricas: HV 23/38, IGD 16/38, IGD+ 3/38.

**Estado.** F (retrato de 17/08; cache anterior à materialização da ⑦ do e103 — a matriz offline precisa de recomputação para o e103).

**Demais detalhes.** Caveats vinculantes: n_nd/spacing/GD do DTLZ4 são inválidos por float32 (IGD+ e HV são invariantes) — DOSSIÊ §D9 caveats; DDMOP7 entra nas tabelas descritivas com asterisco (texto pronto em [RDI] l.3367–3375). Convenção de cobertura vigente: só células a orçamento pleno (C8 parcial); o destino das 615 ⚪ é decisão pendente (ficha 29). Decisões que pede: cor por linha × cor global; mediana × média(dp) (a convenção do corpus); publicar a tabela completa no apêndice (como hoje) × só as matrizes. Encaixe: §5.2 (hoje). Relações: alimenta 2, 3, 4, 6, 17, 22.

### 2. Ranking agregado por rank médio

**Fontes.** [NB] célula [9] (impressão "rank médio (IGD+, 25 sintéticos + RE21/ESTOQUE40; 1 = melhor)") e `resumo_analises_2026-08-17.json` (`rank_medio_igdp_online`) · [CAP5] §5.5 (Tabela `tab:vs-melhor`) · [TC] ("ranking agregado imune aos reais — A27 idêntico ao A11; Spearman 0,990; c141 1º inferencial, c262 1º descritivo") · [PL-38] R1#2 (o rank médio é a entrada do Friedman).

**O que analisa.** A posição média de cada configuração quando os algoritmos são ordenados dentro de cada problema pela mediana do IGD+ (ou HV).

**Dados.** ① via C (endpoint); ⑦ para o offline.

**Objetivo.** Colapsar a matriz num vetor de ordenação comparável entre recortes (só sintéticos; com reais; por família de problema; por política de cobertura).

**O que busca revelar.** A ordem geral e, sobretudo, a **estabilidade** da ordem sob recortes — a torre mostrou que o ranking agregado não muda ao incluir os reais (Spearman 0,990 entre A11 e A27), o que é evidência de que a bateria mede o algoritmo, não ruído.

**Como é realizada.** Para cada problema, ranks 1..k das medianas (empates com rank médio); média dos ranks por algoritmo; ordenação. Variante: rank médio dentro de subconjuntos de problemas (por família, por característica — ficha 17).

**Técnicas.** Rank médio (average rank); correlação de Spearman entre rankings de recortes distintos (estabilidade).

**Implementação.** `med.rank(axis=1).mean()` sobre a matriz de medianas (`MED_IGDP`); recortes por lista de problemas. Para a estabilidade entre recortes, `scipy.stats.spearmanr` entre dois vetores de rank médio.

**Em quantos artigos aparece (dos 38).** "Rank médio" como métrica: BS-MOBO (c1) e "escore médio (ranking Friedman)" em RVMM (e104) — **2/38** como métrica nomeada; como entrada do Friedman, R2#25 (1/38).

**Estado.** F (descritivo, no notebook); T (a estabilidade com/sem reais, na torre).

**Demais detalhes.** Trava d19: leitura por grupos, sem decretar vencedor EA × BO. Decisões que pede: quais recortes publicar (só sintéticos; com reais; por família); métrica-base do rank (IGD+, HV, ou ambos). Relações: entrada de 4 e 5; espelho de 6 e 60.

### 3. "Quem empata com o melhor" — teste de postos vs. o melhor de cada problema (+/=/−)

**Fontes.** [NB] célula [18] (bloco A1: `st.ranksums`, α = 0,05, sem correção; tabela `WX` com melhor / indistinguível / pior) · [CAP5] §5.5 (`tab:vs-melhor`) · [PL-38] R1#1 e R2#4 (a "tabela canônica do campo": símbolo +/=/− vs. referência, linha agregada) · [PL-38] aba Testes (Wilcoxon rank-sum 16/38, "teste de significância par-a-par +/−/∼") · [NB] célula [16] (convenção adotada: "rank-sum α=0,05 sem correção = a convenção dominante").

**O que analisa.** Por problema, se cada algoritmo é estatisticamente distinguível do melhor algoritmo daquele problema (o de menor mediana de IGD+), com base nas 30 sementes.

**Dados.** ① via C (IGD+ por semente).

**Objetivo.** Transformar a matriz de medianas num placar de "quantas vezes cada algoritmo é o melhor ou empata com o melhor", na convenção que a banca reconhece.

**O que busca revelar.** A distância real ao topo: um algoritmo pode nunca ser o melhor e ainda assim ser indistinguível do melhor em muitos problemas (o que a mediana sozinha esconde).

**Como é realizada.** Para cada problema: identifica o melhor (mediana mínima); para cada outro algoritmo, aplica o teste de soma de postos de Wilcoxon (Mann-Whitney) sobre as duas amostras de 30 valores; p ≥ 0,05 → "=", p < 0,05 → "−"; o melhor recebe "+". Linha agregada com a contagem de +/=/− por algoritmo.

**Técnicas.** Wilcoxon rank-sum bicaudal (`scipy.stats.ranksums`), α = 0,05, sem correção de multiplicidade (a convenção dominante do corpus; a correção é decisão pendente — ficha 5); mínimo de 5 sementes por lado.

**Implementação.** [NB] célula [18], laço sobre `ONLINE × SINTS` (25 sintéticos); tabela `WX` ordenada por `melhor_ou_ind`. Extensível aos reais e ao offline (pela ⑦).

**Em quantos artigos aparece (dos 38).** Tabela final com significância: **26/38** (R2#4); Wilcoxon rank-sum como teste: 16/38.

**Estado.** F (25 sintéticos, online).

**Demais detalhes.** A convenção do campo não corrige multiplicidade; a torre, ao contrário, usou pareamento por semente + Holm + região de equivalência (ficha 5) — a escolha entre as duas é decisão do Guilherme (D100). Decisões que pede: referência = melhor do problema (como hoje) × piso casado × algoritmo fixo; correção de multiplicidade; incluir reais e offline. Relações: 1, 5, 9.

### 4. Friedman + Nemenyi + diagrama de diferença crítica (Demšar)

**Fontes.** [NB] célula [18] (bloco A2: `st.friedmanchisquare` sobre as medianas; CD com tabela de q até k = 20; `fig55_cd_diagram`) · [CAP5] §5.5 (`fig:cd-diagram`) · [PL-38] R1#2 (score 9,5) e R2#25 (1/38, IBEA-MS) · [REG] d44–d47 (insumo arquivado: Demšar 2006) · [TP] C13 ("recorte do quadro Friedman §15.1 — segue sem decisão").

**O que analisa.** A comparação global dos k algoritmos sobre N problemas, colapsada num ranking com grupos estatisticamente indistinguíveis.

**Dados.** ① via C (uma mediana por algoritmo × problema).

**Objetivo.** "Contrastar, não catalogar": condensar a matriz num veredito visual único.

**O que busca revelar.** Quais algoritmos formam grupos que não se distinguem dado o número de problemas; onde a diferença de rank médio excede a diferença crítica.

**Como é realizada.** Ranks das medianas por problema → rank médio → teste de Friedman (omnibus, χ²) → pós-teste de Nemenyi com CD = q_α · √(k(k+1)/(6N)) → diagrama: eixo de rank médio, algoritmos ligados por barra quando |Δ rank| ≤ CD.

**Técnicas.** Friedman; Nemenyi (CD); alternativa Holm contra um controle (Demšar 2006); alternativa bayesiana (signed-rank com ROPE — IBEA-MS, e103, é o único dos 38 que a usa).

**Implementação.** [NB] célula [18]: `med = on[...].groupby(["problema","alg"]).igd_plus.median().unstack()`; `dropna()` (só problemas com todos os algoritmos — o que exclui problemas onde algum algoritmo não tem célula válida); `ranks = med.rank(axis=1)`; tabela `Q_05`; varredura clássica para as barras. No retrato de 17/08: k = 17 (13 assistidos + 4 pisos), N = problemas sintéticos com linha completa.

**Em quantos artigos aparece (dos 38).** **1/38** como tipo nomeado (R2#25); Friedman como teste 3/38; Holm/Bonferroni 1/38.

**Estado.** F, mas com o recorte (quais algoritmos e problemas entram; o que fazer com células faltantes; um diagrama por métrica?) ainda não decidido (C13).

**Demais detalhes.** O `dropna()` faz o N depender das lacunas: qualquer algoritmo sem célula válida num problema derruba o problema inteiro — a regra de cobertura (fichas 29, 57, 60) afeta diretamente o CD. Decisões que pede: C13 (recorte executável); Nemenyi × Holm × bayesiano; IGD+ e/ou HV; incluir pisos no k. Relações: 2, 3, 5.

### 5. Comparação pareada por semente vs. o melhor, com Holm e região de equivalência

**Fontes.** [TC] (torre, 22/08: Wilcoxon pareado por semente + correção de Holm + rope ±5 %; "conclusividade 75–80 %"; `metricas_final.csv`, 19.230 linhas, scripts no scratchpad da sessão da torre) · [RF] §4 e §7 · [PL-38] aba Testes (signed-rank pareado 1/38; Holm 1/38; bayesiano com ROPE 1/38) · [NB] §8 fila item 3 ("testes estatísticos — decisão de família/multiplicidade é do AUTOR, D100") · [CAP4] §4.5 (DoE 11D−1 compartilhado: "mesmo ponto de partida", o que autoriza o pareamento).

**O que analisa.** A mesma pergunta da ficha 3, mas explorando o desenho pareado: como todas as configurações partem do mesmo DoE por semente, a diferença entre dois algoritmos pode ser medida semente a semente, o que remove a variância do sorteio inicial.

**Dados.** ① via C (IGD+ e HV por semente); interseção de sementes entre os dois algoritmos comparados.

**Objetivo.** Ganhar poder estatístico com o pareamento e, ao mesmo tempo, proteger-se da multiplicidade e de diferenças sem relevância prática.

**O que busca revelar.** Quais diferenças sobrevivem a três filtros simultâneos: pareamento, correção de Holm e uma região de equivalência prática (±5 %). A torre chamou de "conclusividade" a fração de comparações que passa.

**Como é realizada.** Para cada problema e cada par (algoritmo, referência): diferenças pareadas por semente; teste de Wilcoxon signed-rank; p-valores corrigidos por Holm dentro da família de comparações; diferença mediana comparada à rope (±5 % da métrica da referência): "vence" só se significativo e fora da rope.

**Técnicas.** Wilcoxon signed-rank (`scipy.stats.wilcoxon`); Holm step-down; região de equivalência prática (rope) inspirada em Benavoli et al. (o bayesiano signed-rank com ROPE é a variante do e103); alternativa: bayesiano.

**Implementação.** Não está no notebook. A torre a computou em 22/08 sobre o corpus congelado (`metricas_final.csv`, 19.230 linhas — número de linhas da torre, que inclui os reais e as células ⚪ pela lente de FE comum); o arquivo pode sobreviver no scratchpad do Mac (`/private/tmp/claude-501/-Users-gmello/16c0ba84-843b-49d1-9ce6-6cecc418b734/scratchpad/`). Reimplementar é direto a partir do CSV de endpoint: `merge` por semente, `wilcoxon`, `multipletests(method="holm")`.

**Em quantos artigos aparece (dos 38).** Nenhum dos 38 faz exatamente isto; os ingredientes aparecem em 1 artigo cada (signed-rank pareado: U-RankMOEA, b15 — cujos números são inutilizáveis por N15, mas o desenho conta; Holm: b5; bayesiano com ROPE: e103).

**Estado.** T.

**Demais detalhes.** O pareamento exige a interseção de sementes (caveat D9 da torre: "contrastes pareados usam a interseção de sementes"). A rope de 5 % e o piso empírico de ruído (ficha 59) são dois filtros diferentes para a mesma preocupação (diferenças pequenas demais para significar algo) — usar um, outro ou ambos é decisão. Decisões que pede: família de testes (D100); rope sim/não e largura; referência (melhor do problema × piso casado). Relações: 3, 4, 9, 59.

### 6. Blocos de problemas — a taxa de comparações favoráveis ao surrogate por família de problema

**Fontes.** [DOS] §D9.1 (conclusão vinculante: "a régua é por FAMÍLIA, não por dimensão": BBOB 66 % · ZDT 62 % · MMF 62 % · DTLZ 34 % · WFG 26 % de comparações favoráveis, em 1 semente; freio: só 17,7 % (54/305) excedem o piso de ruído; MMF 0/50 e WFG 1/58 conclusivas) · [TC] (reproduzido em 30 sementes: "blocos {ZDT} ≫ {BBOB, MMF} ≫ {WFG, DTLZ}, tudo reproduzido dígito a dígito") · [RF] §4 · [DOS] item 1 (a leitura R1 "a vantagem cresce com D", SUPERSEDIDA).

**O que analisa.** A fração de comparações assistido-vs-piso favoráveis ao assistido dentro de cada família de problema (suíte).

**Dados.** ① via C (endpoint por semente); M (rótulo de família por problema).

**Objetivo.** Descobrir em que blocos de problemas o surrogate paga e em quais não paga — a versão grossa da leitura por característica (fichas 17–19).

**O que busca revelar.** Que a separação entre "onde o surrogate ajuda" e "onde atrapalha" é por família de problema, e que ela é forte: ZDT no topo, WFG/DTLZ no fundo. A torre também mostrou que essa leitura sobrevive aos reais (ficha 22).

**Como é realizada.** Para cada família, contar as comparações (algoritmo assistido × problema × piso) em que o assistido vence, com e sem o filtro de conclusividade (ficha 59); apresentar como taxa por família e como matriz família × algoritmo.

**Técnicas.** Contagem de vitórias; proporção; opcionalmente teste de proporções entre famílias; filtro pelo piso de ruído.

**Implementação.** Agrupar o CSV de endpoint por família (dicionário problema → família), reaproveitar o placar pareado da ficha 9 e agregar. Números publicáveis dependem da política de cobertura e do filtro escolhido.

**Em quantos artigos aparece (dos 38).** Como "análise por característica do problema" (R2#7): **19/38** — a família da suíte é a forma mais grossa dessa análise.

**Estado.** T (números da torre; não está no notebook).

**Demais detalhes.** As porcentagens do DOSSIÊ são de 1 semente (s42, F5) e valem como auditoria, não como dado (C6: números F5/T11 não são citáveis) — os publicáveis são os da torre de 22/08 sobre 30 sementes, a recomputar. Relações: 9, 17, 22, 59.

### 7. Tendência com a dimensão D — o resultado negativo

**Fontes.** [DOS] item 1 e §D9.1 ("a vantagem do surrogate cresce com D" foi construída sobre 3 problemas na R1 e não se sustenta nos 25) · [TC] ("a tendência-D morre de vez: ρ = −0,076, p = 0,57") · [PL-38] R2#8 (escalabilidade 19/38) · [PL-38] aba Plano ("análise por dimensão + interação D × algoritmo — SPEC §15-D50; só rankings intra-D; ressalva D50").

**O que analisa.** Se a vantagem do assistido sobre o piso cresce, decresce ou é indiferente à dimensão de decisão D.

**Dados.** ① via C; M (D por problema).

**Objetivo.** Testar a tese mais repetida da literatura de SA-MOO no nosso desenho — e registrar honestamente que ela não aparece.

**O que busca revelar.** Que, no nosso regime (orçamento 31D−1, 25 problemas), a dimensão não organiza o resultado; a família do problema organiza (ficha 6).

**Como é realizada.** Correlação entre D e a vantagem mediana do assistido (Δ IGD+ pareado, ficha 9) por problema; leitura visual Δ × D com os problemas rotulados por família.

**Técnicas.** Spearman ρ (a torre reportou ρ = −0,076, p = 0,57); gráfico de dispersão.

**Implementação.** A partir da matriz Δ da ficha 9 e do dicionário `DD` (dimensões, [NB] célula [24]); `spearmanr`.

**Em quantos artigos aparece (dos 38).** Escalabilidade em D e/ou M: **19/38** (R2#8).

**Estado.** T.

**Demais detalhes.** A SPEC (D50) limita a leitura por D a rankings intra-D porque o orçamento cresce com D (31D−1) — D e orçamento são confundidos por desenho. É um resultado negativo: entra em uma frase ou é omitido (decisão). Relações: 6, 9.

### 8. Dispersão entre sementes — o surrogate adiciona variância?

**Fontes.** [TP] C4 (piso empírico de dois níveis: "6 configs surrogate sensíveis a microarquitetura, EAs puros bit-estáveis") · [TC]/`transversal_ruido.md` (ruído entre máquinas) · [PL-38] aba Testes ("nenhum teste formal — média±dp/SEM": 17/38; teste F de variâncias: 1/38) · leitura da mineração de 06/09.

**O que analisa.** A variabilidade do endpoint entre sementes (IQR ou desvio) para cada célula, comparando assistidos e pisos: o surrogate torna o resultado mais ou menos previsível?

**Dados.** ① via C (30 valores por célula).

**Objetivo.** Complementar a mediana com a dispersão — a banca pergunta "e a variância?" e o corpus a reporta como dp nas tabelas.

**O que busca revelar.** Se o uso do modelo adiciona um modo de falha (colapsos ocasionais, como o "colapso ao prior" do b5r nos reais, D7 da torre) que aparece como cauda longa, ou se estabiliza a busca.

**Como é realizada.** Por célula: IQR/mediana (coeficiente de dispersão robusto); matriz algoritmo × problema da dispersão; comparação pareada assistido × piso casado; gráficos de caixa por algoritmo.

**Técnicas.** IQR, MAD; teste de Levene/Brown-Forsythe ou F entre assistido e piso (a convenção do corpus é só descritiva).

**Implementação.** `groupby(["alg","problema"]).igd_plus.agg(["median", lambda v: v.quantile(.75)-v.quantile(.25)])` sobre o CSV de endpoint; pareamento com `PISO_DE`.

**Em quantos artigos aparece (dos 38).** **0/38** como análise nomeada; o dp acompanha a média em 17/38 (descritiva) e o teste F de variâncias aparece em 1/38.

**Estado.** N.

**Demais detalhes.** Deve separar duas fontes de dispersão: semente (sorteio do DoE e do RNG) e máquina (a torre mediu que 6 configurações são sensíveis à microarquitetura — ficha 59). Relações: 1, 59.

---

# Grupo B — O surrogate compra alguma coisa? (assistido × piso, ablação do σ, regime offline)

### 9. Assistido × piso casado — Δ IGD+ pareado por semente e placar por algoritmo

**Fontes.** [NB] §5, célula [11] (`PISO_DE`, `BANDA`, matriz `D` com mediana dos Δ pareados; `PLACAR`; `fig53_sa_vs_pisos`) · [CAP5] §5.3 "O surrogate compra alguma coisa?" (`fig:sa-vs-pisos`, `tab:placar-pisos`) · SPEC §3.2/D25 (casamento SA × piso pelo motor) · [ESQ] l.754 (d103.9: "os pisos sem surrogate como resultado") · [DIA] 17/08 (achados: "assistidos por regressor vencem seus pisos com folga (θ-DEA-DP 23×2); os 2 de surrogate classificador PERDEM do NSGA-II (CSEA 6×19, PC-SAEA 5×20); BO-especiais perdem da banda") · [PL-38] R2#21 (comparação vs. heurística forte não-BO: 1/38).

**O que analisa.** Para cada algoritmo assistido, a diferença de IGD+ em relação ao piso da sua própria classe de motor (NSGA-II, MOEA/D, NSGA-III ou SMS-EMOA), semente a semente, em cada problema.

**Dados.** ① via C (endpoint por semente, assistido e piso, mesmo DoE).

**Objetivo.** Responder à pergunta mais simples e mais dura da bateria: o surrogate compra alguma coisa sobre o mesmo motor sem surrogate, sob o mesmo orçamento e o mesmo ponto de partida?

**O que busca revelar.** Onde e para quem o surrogate paga; e o achado que o Guilherme já antecipara ("em alguns casos, algoritmos que não usam surrogate são melhores do que os que usam" — verbatim, [ESQ] l.754): os dois classificadores perdem do NSGA-II; os BO-especiais perdem da banda.

**Como é realizada.** Para cada (assistido, problema): junta as 30 sementes com as do piso casado (`merge` por semente), calcula Δ = IGD+_piso − IGD+_assistido por semente, publica a mediana dos Δ (verde = assistido melhor; laranja = piso melhor) e conta vitórias × derrotas por algoritmo (mínimo 5 pares). Para c154, e81, c149 (sem motor evolutivo casável) a referência é o melhor dos 4 pisos em cada semente (a "banda", teste mais severo, declarado).

**Técnicas.** Diferença pareada; mediana dos Δ; mapa de calor divergente com limite no percentil 92 dos |Δ|; placar V × D. Sem teste de significância nesta forma (o teste entra pelas fichas 3 e 5).

**Implementação.** [NB] célula [11] sobre `on` (exp == main) e `SINTS` (25 sintéticos). Extensível aos reais (a torre já o fez: RE21 9/12 pró-SA conclusivas, EST40 3/4 — [TC]).

**Em quantos artigos aparece (dos 38).** Como tipo nomeado "comparação vs. heurística forte não-surrogate (piso)": **1/38** (qNEHVI, c262). Os pisos evolutivos aparecem como competidores nas tabelas de 26/38 (R2#4), mas o desenho "mesmo motor, mesmo DoE, pareado" não foi contado à parte.

**Estado.** F (25 sintéticos).

**Demais detalhes.** O casamento é por classe de motor (D25); o smsemoa × c262 fica restrito a M = 2 no EST40 (D11 da torre: o CalHV stock degenera com f1 < 0). O placar depende da política de cobertura (P1 × P2) e da interseção de sementes. Decisões que pede: incluir reais e DDMOP7 (estratificado); estatística (só mediana × teste); publicar a matriz e/ou o placar. Relações: 3, 5, 6, 10, 16, 22.

### 10. A banda dos pisos — os BO-especiais contra o melhor dos quatro pisos

**Fontes.** [NB] célula [11] (`BANDA = ["c154","e81","c149"]`; `best = ... groupby("semente").igd_plus.min()`) · SPEC D25 · [CAP5] §5.3 · [DIA] 17/08 ("BO-especiais perdem da banda (teste mais severo, declarado)").

**O que analisa.** O mesmo que a ficha 9 para os três algoritmos sem motor evolutivo casável (JES, qPOTS, LBN-MOBO): a diferença por semente para o melhor piso daquela semente.

**Dados.** ① via C.

**Objetivo.** Não deixar os BO-especiais sem piso; escolher o piso mais exigente e declará-lo.

**O que busca revelar.** Se um otimizador bayesiano "puro" vence o melhor evolutivo sem modelo sob o mesmo orçamento — e o retrato de 17/08 diz que não, nos sintéticos.

**Como é realizada.** Idêntica à ficha 9, com a referência trocada: para cada semente, o menor IGD+ entre NSGA-II, MOEA/D, NSGA-III e SMS-EMOA naquele problema; Δ = melhor_piso − assistido; mediana dos Δ; placar.

**Técnicas.** Mínimo por semente sobre os 4 pisos; diferença pareada; mediana; placar V × D.

**Implementação.** [NB] célula [11], ramo `else` (`best = on[on.alg.isin(PISOS) & ...].groupby("semente").igd_plus.min()`), `merge` por semente.

**Em quantos artigos aparece (dos 38).** Idem ficha 9 (1/38 como tipo).

**Estado.** F (dentro da ficha 9).

**Demais detalhes.** A banda é mais severa que o casamento (usa o melhor de 4); isso deve ficar explícito na prosa para não penalizar os BO-especiais por desenho. Alternativa a decidir: comparar com a mediana dos 4 pisos, ou com cada piso separadamente. Relações: 9.

### 11. Ablação exata do σ — Prob-MOEA/D × MOEA/D-média, em duas leituras

**Fontes.** SPEC D77 (o piso offline `moead_media` = "b5 sem σ": mesmo motor, surrogate, orçamento e reticulado, mudando só a seleção) · [NB] §6, célula [13] (`ABL`: Δ IGD+ pareado por semente, `moead_media − b5m`; `fig54_offline`) · [CAP5] §5.4 "O regime offline e a ablação exata da incerteza" (`fig:offline-igdp`) · [DIA] 17/08 ("ablação exata do σ: ajuda em 15/25 com assimetria brutal — top-3 = DTLZ1/DTLZ3/ZDT4, multimodais severos, +43 a +56 de Δ IGD+; danos ≤ 1,25; 'seguro contra o pior caso', primeira evidência direta da tese") · [DOS] §D9.4 (vinculante: "o congelamento do b5m é RESULTADO, não bug; b5m/DTLZ1 e b5m/DTLZ3 são cientificamente vazios; a ablação D77 é publicada em DUAS leituras (45 e 31 células): o efeito em σ sobrevive (p = 0,0012 → 0,0020), o efeito direcional em IGD+ enfraquece (p = 0,281 → 0,624)") · [DOS] item 2-bis (moead_media: "a maquinaria probabilística ATRAPALHA 8,5× no ZDT1; turnover 8,5 %/ger vs 98 %/ger do b5m") · [CAP1] OE5 (o contrafactual que "desliga o uso da incerteza") · [PL-38] R2#3 (ablação 26/38).

**O que analisa.** O efeito isolado de usar a incerteza (σ do GP) na seleção do Prob-MOEA/D, contra a mesma maquinaria selecionando pela média: a única ablação exata da bateria.

**Dados.** ⑦ (endpoint offline reavaliado na função verdadeira) das duas configurações; ① (dataset compartilhado por semente — igual por desenho); ⑥ para o mecanismo (turnover, substituições).

**Objetivo.** Dar à tese a sua evidência mais direta: com tudo o mais fixo, o σ ajuda, atrapalha ou é indiferente — e onde.

**O que busca revelar.** A assimetria: onde o σ ajuda, ajuda muito (os multimodais severos); onde atrapalha, atrapalha pouco — a leitura "seguro contra o pior caso" do retrato de 17/08.

**Como é realizada.** Por problema, Δ = IGD+(moead_media) − IGD+(b5m) pareado por semente (mesmo dataset), mediana dos Δ, contagem de problemas com Δ > 0; duas leituras obrigatórias: 45 células (todas) e 31 (excluindo os problemas em que o b5m congela — DTLZ1/DTLZ3, e o que mais a torre listou) — os números do DOSSIÊ referem-se à rodada F5 e devem ser recomputados sobre o canônico.

**Técnicas.** Diferença pareada; mediana; teste pareado (a torre reportou p do efeito em σ e p do efeito direcional em IGD+); gráfico de barras ordenado por Δ.

**Implementação.** [NB] célula [13] sobre `off` (exp == off), `b5m` × `moead_media`, `SINTS`; `merge` por semente. A segunda leitura exige a lista de células "cientificamente vazias" ([DOS] §D9.4; [TP] E9: abortos do b5m de 13/08). Os reais entram pela ⑦ (ficha 12). A ⑦ do e103 foi materializada em 22/08 — não afeta esta ficha, mas afeta a 13.

**Em quantos artigos aparece (dos 38).** Ablação/contribuição de componente: **26/38** (R2#3), "frequentemente o próprio mecanismo de uso da incerteza (ex.: AUCB vs UCB vs só média)".

**Estado.** F-parcial (leitura única, só sintéticos).

**Demais detalhes.** Caveat vinculante: o GP do objetivo 2 do b5m degenera no DTLZ2 (μ ≈ 0) enquanto o piso, com a mesma especificação, ajusta corr 0,992 — sensibilidade à semente de treino; "dado honesto; quebra o contraste NESSE problema" ([DOS] item 2-bis, ratificado DI-30). Decisões que pede: as duas leituras (obrigatórias pelo §D9) e como apresentá-las; teste pareado sim/não; papel desta ficha frente ao OE5 (ficha 15). Relações: 12, 13, 14, 15, 45.

### 12. A ablação do σ nos problemas reais — o primeiro resultado conclusivo, contra

**Fontes.** [TC] ("a ablação do σ (b5) ganha seu primeiro resultado conclusivo — contra (ESTOQUE40, par RVEA, p_holm = 0,024)") · [RF] §4 · [TP] D7 (b5r: "colapso ao prior nos reais — EST40 4/30 com ⑦ HV 0,048–0,333 e b5r⑦ < dataset em 28/30; RE21 7/30 invertido; réplicas não-independentes s1/s2/s27") · [TP] D6 (moead_media × RE21: "22/30 células com ⑦ de 1 único x duplicado 50× — declarado não-informativo como régua nesse problema").

**O que analisa.** A ficha 11 estendida a RE21 e ESTOQUE40 (o DDMOP7 offline não tem ⑦ — B2 da torre), incluindo a variante Prob-RVEA.

**Dados.** ⑦ das configurações offline nos reais; ① (dataset).

**Objetivo.** Ver se o efeito do σ nos sintéticos se transfere aos reais.

**O que busca revelar.** Que nos reais o σ pode atrapalhar de modo conclusivo (o único resultado que passou Holm + rope na ablação, segundo a torre) — o que dialoga com o eco M13 do cap. 6 ("injetar incerteza nem sempre ajuda").

**Como é realizada.** Como a 11 (Δ pareado por semente entre a configuração com σ e o piso offline, pela ⑦), restrita a RE21 e ESTOQUE40, com o teste pareado + Holm + rope da ficha 5; reporte de |X únicos| junto do endpoint onde a ⑦ degenera.

**Técnicas.** Diferença pareada; Wilcoxon signed-rank; Holm; rope ±5 %; contagem de células degeneradas.

**Implementação.** Idem 11, sobre `problema ∈ {RE21, ESTOQUE40}`; atenção aos caveats D6/D7 (células degeneradas devem ser declaradas, não silenciadas).

**Em quantos artigos aparece (dos 38).** Ablação (26/38) cruzada com estudo de caso real (20/38); como combinação, não contada.

**Estado.** T.

**Demais detalhes.** O "par RVEA" citado pela torre precisa ser reconferido na fonte (`transversal_ciencia.md`) antes de qualquer prosa — o piso offline oficial é o moead_media; a comparação b5r × piso é a que a torre chamou de par RVEA. Relações: 11, 22, 23.

### 13. O regime offline pela camada ⑦ — as quatro configurações mais o e103

**Fontes.** DI-08 (persistência da avaliação real do ND final offline) e DI-13.8/13.9 (`origem_linha`, `nd_pos_real`; "avaliar TODOS os finais e filtrar DEPOIS") · [DOS] §D9.2 (vinculante: "o endpoint do regime OFFLINE é a camada ⑦, nunca a ①"; pela ⑦ na F5: e103 IGD+ 0,2251/17 vitórias · b5r 0,3814 · b5m 0,4868 · moead_media 0,5959 · c311 0,7211 — números de auditoria, não citáveis) · [RDI] l.3354–3365 (22/08: "⑦ DO e103 MATERIALIZADA — 703 ⑦ novas, 25 legadas de s42; n_nd_pos_real mediana 28/100; pendente e103 × DDMOP7") · [NB] célula [13] (matriz offline; "IBEA-MS: ⑦ ausente — hachura") · [CAP5] §5.4 · [PL-38] R2#16 (in-sample vs fora-da-amostra: 3/38) e Cobertura (11 dos 38 são offline).

**O que analisa.** O desempenho final dos algoritmos offline (b5m, b5r, moead_media, e103) medido no ND final reavaliado na função verdadeira — porque a ① deles é o mesmo dataset compartilhado e empata por desenho.

**Dados.** ⑦ (nd_pos_real; origem_linha); ① (para o "ganho sobre o dataset", ficha 14); ⑤ (sidecar DI-08 com `fora_do_orcamento = true`).

**Objetivo.** Dar ao regime offline um endpoint legítimo e comparável entre configurações; corrigir a exclusão silenciosa do e103 que o retrato de 17/08 carregava.

**O que busca revelar.** A ordem entre as quatro configurações offline e a distância delas ao dataset de partida.

**Como é realizada.** Por célula: métricas da ficha 1 sobre o conjunto da ⑦ (ND reavaliado), depois matriz de medianas e as leituras das fichas 2–5 restritas ao offline.

**Técnicas.** As mesmas da ficha 1; regra "nunca consumir ⑦ de célula com motivo de falha" ([TP] C10-vi).

**Implementação.** O cache de 17/08 traz 826 linhas `erro = final_ausente` (das quais as do e103); com a ⑦ materializada em 22/08 (`scripts/final_eval.py --exp off --alg e103 --all-seeds`), o CSV de endpoint precisa ser regenerado para o e103 antes de qualquer matriz offline. O e103 × DDMOP7 (30 células) fica declarado fora do endpoint (B2), com a frase pronta da torre.

**Em quantos artigos aparece (dos 38).** É o endpoint padrão dos **11 artigos offline** entre os 38 (b13, b5, b7, c24, c45, c49, c50, c59, c81, c97, e103); a variante "recomendação pela média posterior vs pontos avaliados" é R2#16 (3/38).

**Estado.** F sem o e103 (cache defasado).

**Demais detalhes.** Caveats: moead_media × RE21 colapsa a um ponto em 22/30 (D6); b5r colapsa ao prior nos reais (D7); DDMOP7 offline sem ⑦ (B2). Decisões que pede: regenerar o endpoint offline com o e103 (execução, quando chegar a hora); DDMOP7 offline "sem endpoint" por frase. Relações: 11, 12, 14, 42, 63.

### 14. O ganho sobre o dataset — quanto cada offline melhora (ou piora) o que recebeu

**Fontes.** [DOS] item 2-bis (e103: "IGD+ 0,0057 no ZDT1 — ganho 99,7 % sobre o dataset; melhor endpoint do painel"; e81: "ganhos 32–53 % sobre o DoE") · [TP] D7 ("b5r⑦ < dataset em 28/30 no ESTOQUE40") · [TP] C10-iii (errata: "'c122 empata com DoE' veio de célula morta — em 30 sementes melhora 100 %") · DI-08.

**O que analisa.** A diferença entre a métrica do dataset inicial (o ND do próprio dataset compartilhado, avaliado como conjunto) e a métrica da ⑦ — o que o algoritmo acrescentou ao que recebeu. Versão online análoga: métrica do DoE (11D−1) vs endpoint.

**Dados.** ① (dataset/DoE) e ⑦ (offline) ou ① completa (online).

**Objetivo.** Situar o endpoint contra o ponto de partida, que no offline é idêntico para todos — a régua natural do regime.

**O que busca revelar.** Quem "estraga" o dataset (o b5r nos reais fica abaixo do próprio dataset em 28/30 no EST40, segundo a torre) e quem o transforma (o e103 no ZDT1).

**Como é realizada.** Por célula: métrica do ND do dataset; métrica da ⑦; ganho relativo; matriz por algoritmo × problema; contagem de células com ganho negativo.

**Técnicas.** Ganho relativo; mediana; contagem.

**Implementação.** `metrics_of_set` sobre as linhas `fase == init` da ① (dataset/DoE) e sobre a ⑦; diferença. Não há cache.

**Em quantos artigos aparece (dos 38).** Não contada como tipo; é a leitura implícita dos 11 offline e da "utilidade" (R2#22, 1/38).

**Estado.** N.

**Demais detalhes.** No online, o mesmo cálculo (endpoint vs DoE) mede "o que a busca comprou" e é o denominador natural da ficha 43. Decisões que pede: publicar como razão, diferença ou porcentagem; incluir no texto do offline. Relações: 13, 43.

### 15. O contrafactual σ = 0 online — cravado, nunca executado

**Fontes.** [REG] d48 (verbatim: "adorei esse experimento que voce propos!!! vamos adotar ele sim… selecione 8 algoritmos… sobre todos os 25 problemas teoricos"; cravado: 8 algoritmos × 25 problemas × {σ normal, σ ← 0}; JES/PESMOC excluídos porque a incerteza é constitutiva da aquisição — "demonstração empírica da fronteira OL") · [REG] d86 (§4.6-bis = sub-experimento contrafactual) · [REG] d67 (cláusula de escopo: "sob a hipótese de que a incerteza em questão é epistêmica") · [CAP1] OE5 ("incluindo um contrafactual que desliga o uso da incerteza para medir a sua contribuição isolada") · [CEN] (nenhuma configuração σ = 0 no corpus) · o martelo "não vou rodar mais nenhum experimento" (06/09).

**O que analisa.** (Analisaria) o efeito isolado da incerteza em cada algoritmo online: a mesma configuração com σ forçado a zero na aquisição/seleção.

**Dados.** Não existem: o corpus congelado tem 24 diretórios de configuração e nenhum é uma variante σ = 0.

**Objetivo.** Honrar o OE5 e a d48: medir "a contribuição isolada" do uso da incerteza.

**O que busca revelar.** O mesmo que a ficha 11, para os algoritmos online e por classe de função (OV/OM/AV/AM…).

**Como é realizada (seria).** Duas execuções por célula (σ, σ ← 0), Δ pareado por semente, leitura por classe de função.

**Técnicas.** As da ficha 11.

**Implementação.** Inexistente. O que a bateria oferece como substituto: (a) a ablação exata offline (ficha 11); (b) as "quase-ablações naturais" medidas pela torre: c217 com gate que abre em 4,6 % dos ciclos (opera como amostrador aleatório + SPEA2 em 7 problemas — [TP] D5), b4 usando o surrogate em 25,8 % dos FEs, e7 com 152 decisões por convergência contra 48 por incerteza, b3 com o switch preso 44/48 no ramo incerteza ([DOS] item 2-bis e §D9 caveats) — ver ficha 45.

**Em quantos artigos aparece (dos 38).** A ablação do mecanismo de incerteza é R2#3: **26/38**.

**Estado.** L.

**Demais detalhes.** É a decisão de maior alcance que a mineração devolveu: o cap. 1 promete o contrafactual; o corpus não o tem. Opções que a triagem vai encontrar (sem recomendação aqui): reescrever o OE5 para o que existe (ablação offline + quase-ablações); declarar o contrafactual online como limitação; ou reabrir a execução (contra o martelo de 06/09). Relações: 11, 45, 61.

### 16. Os pisos como resultado — onde e por que o piso vence o assistido

**Fontes.** [ESQ] l.754 (d103.9, acréscimo do Guilherme: "já rodei alguns experimentos e em alguns casos, algoritmos que não usam surrogate são melhores do que os que usam" — deixa de ser controle de formalidade e vira achado; §5.6 com 3 páginas; literatura de apoio b5 §IV p. 1188 e b9 §5.2 Fig. 4; corpus CL-C6-15/16, MD-C6-04) · [ESQ] "Lei 1 — trava: os experimentos preliminares não estão registrados" (a bateria congelada levanta a trava) · [DOS] item 2-bis (mecanismos: c217 gate quase nunca abre → EA ~aleatório que perde do nsga2; c154 ruído inferido ×90 → pior E mais confiante; b3 ciclo vicioso exploração → modelo-não-melhora) · [TP] D5 · [CHK] adendo 31/07 ("a dissertação não afirma que usar incerteza é sempre melhor; afirma que COMO se usa é uma dimensão de projeto") · [PC6] §4.1 (eco M13 no cap. 6).

**O que analisa.** O subconjunto do placar da ficha 9 em que o piso vence, com a explicação mecânica de cada caso.

**Dados.** ① via C (placar); ③ (sonda) e ⑥ (filme) para o mecanismo; ⑤ (sigma_dict).

**Objetivo.** Transformar "o piso venceu" de anomalia em resultado: a incerteza mal usada, ou não usada, custa.

**O que busca revelar.** As três razões tipo que a torre já nomeou: o mecanismo não dispara (c217), o mecanismo dispara e engana (c154, b3), o modelo não aprende (e7 no DTLZ2).

**Como é realizada.** Lista das células/problemas com Δ < 0 na ficha 9; para cada algoritmo com derrota sistemática, uma leitura do mecanismo pelas fichas 31–35 e 45; tabela "algoritmo → onde perde → por quê (evidência)".

**Técnicas.** Contagem; leitura por mecanismo (contagem de disparos em ⑥; curvas da sonda).

**Implementação.** Reúso da matriz `D` da ficha 9 (`D < 0`), cruzado com contagens do ⑥ (eventos de gate/switch por geração) e com `sonda_2026-08-17.parquet`.

**Em quantos artigos aparece (dos 38).** Piso não-surrogate como comparação nomeada: 1/38 (R2#21). A leitura "o piso venceu e eis por quê" não aparece como tipo.

**Estado.** F-parcial (o placar existe; o "por quê" está espalhado nos laudos da torre, não no notebook).

**Demais detalhes.** É a seção que impede o triunfalismo (N8) e conversa com o eco M13. Decisões que pede: se vira seção própria (§5.6 do esqueleto) ou parágrafos dentro da ficha 9; quanto mecanismo entra. Relações: 9, 31, 35, 45.

---

# Grupo C — Característica do problema × característica do algoritmo (a lei da §4.1 e a diretriz DIR-14)

> A pergunta-guia do capítulo, decidida em 06/09: *"que característica do algoritmo explica o resultado, diante de que característica do problema?"* ([CAP4] §4.1, l.24). Diretriz da orientadora (DIR-14 ii, verbatim): *"o algoritmo da família tal teve esse comportamento com base na característica que a gente escreveu lá atrás — vai fazendo o link"*. Este grupo é o que responde à pergunta; os grupos A, B e D fornecem o "resultado", o grupo E fornece o "mecanismo".

### 17. Rank médio por característica estressada do problema (a versão-piloto)

**Fontes.** [NB] célula [20] (bloco A3: `characteristics.csv`, 7 colunas de característica — multimodal, deceptive, disconnected, biased_density, nonseparable, high_dim, concave_front; rank médio de IGD+ dentro de cada grupo; `fig56_caracteristica`) · [CAP5] §5.6 "Característica do problema × algoritmo" (`fig:caracteristica`) · [CAP4] §4.3 (a matriz `fig:matriz-problemas`: "linha = característica estressada, coluna = degrau de dificuldade, célula = problema") · [R4] e `claude_code_context/artifacts/characteristics.csv` (28 × 12: problema, M, D, e as 7 características, empirical_front_bbob, real_world) · D98 ("a matriz deve ser re-derivada: WFG1/4/5 marcados como não-separáveis por engano, entre outros") · [PL-38] R1#3 (score 10: "é a tese") e R2#7 (19/38) · [DIA] 17/08 ("estatuto do characteristics.csv (D98 — usei com ressalva declarada)").

**O que analisa.** Para cada característica de problema, o rank médio de cada algoritmo restrito aos problemas que estressam aquela característica.

**Dados.** ① via C (medianas por célula); M (`characteristics.csv`, matriz binária problema × característica).

**Objetivo.** Dar o primeiro elo entre a matriz do cap. 4 e o desempenho: qual algoritmo responde melhor a qual dificuldade.

**O que busca revelar.** Se a ordem entre algoritmos muda com a característica (se não muda, a característica não explica nada; se muda, é onde a explicação mora).

**Como é realizada.** Ranks por problema (como na ficha 2); para cada característica c, média dos ranks sobre os problemas com c = 1; matriz característica × algoritmo (verde = melhor na linha); n de problemas por característica impresso.

**Técnicas.** Rank médio estratificado; mapa de calor.

**Implementação.** [NB] célula [20]: `CAR[CAR[c] == 1].problema` → `ranks.loc[probs].mean()`. A matriz de características precisa ser re-derivada e ratificada (D98) antes de qualquer número publicável — no retrato de 17/08 foi usada com ressalva.

**Em quantos artigos aparece (dos 38).** Análise por característica do problema: **19/38** (R2#7), "muitas vezes com hipótese causal dos próprios autores" (R1#3).

**Estado.** F como piloto; insumo em ressalva.

**Demais detalhes.** Um problema pertence a várias características, logo as linhas não são independentes (o mesmo problema pesa em várias) — a leitura é descritiva. As características com n pequeno (o notebook imprime n por linha) não sustentam afirmação. Decisões que pede: a matriz de características canônica (D98); rank × Δ pareado (ficha 9) como estatística por característica; teste por característica sim/não. Relações: 6, 18, 19, 20.

### 18. As escadas de dificuldade — em que degrau cada classe deixa de funcionar

**Fontes.** [CAP4] l.100 ("dentro de cada propriedade os problemas formam uma 'escada de dificuldade', que diagnostica não só SE um algoritmo falha, mas A PARTIR DE QUE INTENSIDADE") e l.117 (promessa explícita: "é esse desenho que autoriza o Capítulo 5 a perguntar em que degrau de cada escada cada classe deixa de funcionar") · [CAP4] `fig:matriz-problemas` e `tab:problemas`/`tab:problemas2` (a ordem dos degraus) · [NB] §8 fila item 1 ("escadinhas por característica — exige o congelamento do corpus + a matriz re-derivada") · [PC5] (§5.3 do plano: escadas) · [PL-38] R1#3 ("agrupa os 26 problemas pela 'escadinha' de características que você já montou").

**O que analisa.** Dentro de cada característica, os problemas ordenados por intensidade (degrau 1 → n); para cada algoritmo (e para cada classe), a curva de desempenho relativo ao longo dos degraus — e o degrau em que ele "deixa de funcionar" (passa a perder do piso, ou cai abaixo de um limiar).

**Dados.** ① via C; M (matriz característica × degrau × problema, transcrita da `fig:matriz-problemas` do cap. 4).

**Objetivo.** Cumprir a promessa do cap. 4: um diagnóstico graduado, não binário.

**O que busca revelar.** Limiares: a partir de que intensidade de multimodalidade (por exemplo) a incerteza deixa de impedir o colapso; se as classes de motor/surrogate/função têm limiares diferentes.

**Como é realizada.** Para cada característica: eixo x = degrau; eixo y = Δ pareado vs piso (ficha 9) ou rank; uma linha por algoritmo (ou por classe, agregando); o "degrau de falha" = primeiro degrau em que Δ < 0 de forma conclusiva (critério a decidir); tabela classe × característica com o degrau de falha.

**Técnicas.** Curvas por degrau; mediana; critério de falha (Δ < 0; ou teste pareado; ou piso de ruído); agregação por classe.

**Implementação.** Não existe. Exige (i) a tabela de degraus por característica (do cap. 4), (ii) a matriz Δ da ficha 9 ou os ranks, (iii) uma função "primeiro degrau de falha". As extremidades da matriz são deliberadas: a primeira coluna são "testes de sanidade" e a última os "chefes de fase" ([CAP4] l.117).

**Em quantos artigos aparece (dos 38).** Combina característica (19/38) e escalabilidade/degrau (19/38); a forma "escada com degrau de falha" não foi contada como tipo.

**Estado.** N.

**Demais detalhes.** É a análise que a matriz do cap. 4 foi construída para permitir; sem ela a matriz é só seleção de problemas. Decisões que pede: o critério de "deixa de funcionar"; por algoritmo ou por classe; quantas escadas publicar. Relações: 9, 17, 19, 20.

### 19. As seis perguntas sobre a incerteza — uma por característica, casando resultado e mecanismo

**Fontes.** [CAP4] l.102 (verbatim: "Multimodalidade é o coração: um surrogate com poucas amostras alisa bacias distintas numa superfície única, e é aí que uma incerteza honesta deveria impedir o colapso prematuro da busca. Não separabilidade infla o erro dos regressores que modelam dimensões independentemente. Paisagens enganosas ensinam o caminho errado com alta confiança. Regiões planas estagnam o modelo num platô. Frentes desconexas induzem regressores contínuos a alucinar pontes. Densidade não uniforme cria heterocedasticidade: pouca informação onde a busca mais precisa. A cada situação correspondem uma pergunta sobre a incerteza e ao menos dois problemas, em suítes diferentes.") · [CAP4] §4.1 l.26 ("para que afirmações como 'em problemas multimodais, o mecanismo X supera o Y' tenham apoio em observações independentes") · DIR-14 · [ESQ] l.752 (a sonda "dá mecanismo ao resto do capítulo").

**O que analisa.** Cada uma das seis situações como uma mini-análise com duas metades: o resultado (quem vence/perde nos problemas daquela característica — fichas 9, 17, 18) e o mecanismo previsto pela pergunta (a sonda e o filme: fichas 31–38, 45). Por exemplo: em paisagens enganosas, o σ é baixo onde o erro é alto? (calibração local); em densidade não uniforme, o erro é heterocedástico? (ficha 38); em frentes desconexas, o modelo "alucina pontes"? (predições com μ na lacuna da frente); em multimodalidade, quem colapsa cedo e o σ dele era honesto? (trajetória + cobertura).

**Dados.** ① via C (resultado); ③ regime sonda + S (mecanismo, por problema); ⑥ (decisões); M (matriz de características).

**Objetivo.** Fazer a prosa do cap. 5 cumprir a frase da §4.1: cada característica de problema recebe a característica do algoritmo que a explica, com evidência dos dois lados.

**O que busca revelar.** Se a hipótese específica de cada situação se sustenta, se sustenta só para algumas classes, ou se cai — e é essa a matéria da "releitura" que o cap. 6 vai ecoar.

**Como é realizada.** Seis blocos com o mesmo formato: pergunta (do cap. 4) → problemas que a estressam (matriz) → resultado (placar/rank por característica) → mecanismo (a medida da sonda que responde à pergunta) → veredito por classe.

**Técnicas.** As das fichas 9/17/18 para o resultado; as das fichas 31–38 para o mecanismo, restritas aos problemas da característica.

**Implementação.** Composição de análises existentes filtradas por característica; a única peça nova é o cruzamento sonda × característica (a sonda cache tem `problema`, logo o filtro é direto). Algumas perguntas exigem medidas que não estão nos caches (heterocedasticidade por região — ficha 38; μ na lacuna da frente — pontos da sonda entre os segmentos da frente verdadeira).

**Em quantos artigos aparece (dos 38).** Característica × mecanismo com hipótese causal: dentro dos 19/38 (R2#7). A forma "pergunta declarada antes, respondida pela instrumentação" não aparece nos 38 — a sonda é instrumento que "nenhum trabalho do corpus dispõe" ([CAP4] l.450).

**Estado.** N (é uma composição; nenhum bloco foi montado).

**Demais detalhes.** É a espinha do capítulo sob a pergunta-guia. Decisões que pede: quais das seis perguntas viram seção, quais viram parágrafo; a ordem; o que fazer com a pergunta cujo mecanismo não é mensurável com os caches atuais. Relações: 9, 17, 18, 31–38, 45.

### 20. A taxonomia como variável — desempenho agregado por classe de cada eixo

**Fontes.** DIR-14 (ii) (verbatim acima) · [CAP4] §4.1 l.24 ("algoritmos de classes diferentes diante de problemas de propriedades diferentes, sob protocolo único") e l.26 ("do lado dos algoritmos, cobrir as classes da taxonomia") · [CAP5] §5.3 (a leitura já é por classe informalmente: "assistidos por regressor vencem seus pisos; os 2 de surrogate classificador PERDEM do NSGA-II; n = 2, devolvido ao cap. 3 como pergunta") · [DIA] 17/08 · [PC5] · [CHK] P7 ("ganchos 🧪 para o cap. 5 nas classes com representantes experimentais").

**O que analisa.** O desempenho (Δ pareado vs piso; rank; taxa de vitórias) agregado pela classe do algoritmo em cada um dos quatro eixos: motor (7 classes), surrogate (4), função da incerteza (6), medição (5) — e cruzado com a característica do problema.

**Dados.** ① via C; M (a classificação de cada algoritmo do roster nos 4 eixos — da planilha/base127, que vence em conflito).

**Objetivo.** Tornar a taxonomia do cap. 3 uma variável explicativa do cap. 5: é a forma direta de "que característica do algoritmo explica o resultado".

**O que busca revelar.** Se as classes de função e de medição (as duas sobre a incerteza) explicam mais ou menos que as classes de maquinaria (motor, surrogate); onde a taxonomia separa desempenho e onde não separa.

**Como é realizada.** Para cada eixo: tabela classe × característica de problema com a mediana dos Δ (ou taxa de vitórias) dos algoritmos da classe; n de algoritmos por classe declarado (várias classes têm 1 ou 2 representantes no roster — o retrato de 17/08 devolveu a leitura dos classificadores ao cap. 3 justamente por n = 2).

**Técnicas.** Agregação por classe; mediana; contagem; sem teste (n de algoritmos por classe é pequeno demais; a unidade estatística é o algoritmo, não a célula).

**Implementação.** Dicionário algoritmo → (motor, surrogate, função, medição) lido da planilha de classificação; `groupby` sobre a matriz Δ da ficha 9. Não existe no notebook.

**Em quantos artigos aparece (dos 38).** **0/38** — nenhum artigo compara algoritmos agrupados por uma taxonomia; é a contribuição própria.

**Estado.** N.

**Demais detalhes.** Armadilha de banca: com 15 algoritmos, várias classes têm um único representante; afirmações por classe precisam de hedge explícito (N1/N13: "no roster de 15"). A trava d19 (não decretar vencedor EA × BO) vale aqui. Decisões que pede: quais eixos publicar; a estatística por classe; como declarar n. Relações: 9, 17, 21, 36.

### 21. As famílias da §3.8 sob teste — o roster cobre 7/7

**Fontes.** [ESQ] §3.8 (famílias = os ≤7 grupos finais, termo reservado d25; respondem à RQ3) · `chapters/03-8-familias.tex` (banner: "F1 61 · F2 20 · F3 15 · F4 10 · F5 4 · F6 12 · F7 5 = 127; roster cobre 7/7"; "os NOMES das famílias aguardam o crivo (D-10)"; `fig:familias-mosaico` com "os algoritmos do plantel experimental" marcados nas células) · [PC6] §3 (cap. 6 confirma "as ≤7 famílias construídas") · [PL-38] R1#7 (contraste por família).

**O que analisa.** O desempenho agregado por família da §3.8 (em vez de por classe de um eixo, como na ficha 20): cada família do survey representada pelos seus algoritmos no roster.

**Dados.** ① via C; M (de-para algoritmo → família, da §3.8).

**Objetivo.** Fechar o arco do cap. 1 ("as famílias construídas, a avaliação experimental feita"): a avaliação experimental lida na unidade que o cap. 3 construiu.

**O que busca revelar.** Se as famílias — definidas por perfil de classificação — se comportam como grupos também no desempenho; onde a família prediz e onde não.

**Como é realizada.** Como a ficha 20, com o de-para de famílias; tabela família × característica de problema; leitura com n de algoritmos por família.

**Técnicas.** Agregação; mediana; contagem.

**Implementação.** Depende do de-para (existe como regra lexicográfica; os nomes aguardam D-10). Reúso da ficha 9.

**Em quantos artigos aparece (dos 38).** **0/38** como tipo (comparação por família de uma taxonomia própria).

**Estado.** N (bloqueada pelos nomes/de-para da §3.8).

**Demais detalhes.** Com 15 algoritmos em 7 famílias, o n por família é 1–4; é uma leitura descritiva, com o hedge de N1/N13. Decisões que pede: se entra como análise ou só como coluna adicional na ficha 20; o de-para canônico. Relações: 20.

### 22. O sintético prediz o real? — a transferência do ranking para RE21, ESTOQUE40 e DDMOP7

**Fontes.** [TC] (tese nova da torre: "A família sintética prediz mal o problema real. A derrota do surrogate fica confinada a WFG/DTLZ sintéticos e ao DDMOP7 degenerado; nos dois reais estruturados o surrogate vence com efeito 3–6× (RE21: 9/12 comparações pró-SA conclusivas; ESTOQUE40: 3/4). Substitui 'o surrogate perde onde conta'") · [RF] §4 ("ranking agregado imune aos reais — Spearman 0,990") e §3 (RE21 "o problema mais pró-surrogate do corpus inteiro, p ≈ 1e-97") · [PL-38] R2#6 (estudo de caso/aplicação real: 20/38).

**O que analisa.** Duas coisas distintas: (a) se o ranking agregado muda quando os reais entram (não muda — Spearman 0,990); (b) se a taxa de vitórias do surrogate nos reais é predita pela taxa nos sintéticos (não é — os reais estruturados são mais pró-surrogate do que a média sintética).

**Dados.** ① via C (sintéticos e reais); ⑦ (offline nos reais).

**Objetivo.** Responder à pergunta que a banca fará sobre os três problemas reais: "servem para quê?" — servem para testar se o benchmark sintético prediz o comportamento fora dele.

**O que busca revelar.** Que a "família sintética" (WFG/DTLZ em particular) é mais hostil ao surrogate que os reais estruturados; e que a ordem entre algoritmos, ao contrário, é estável.

**Como é realizada.** (a) Rank médio com e sem reais, Spearman; (b) placar assistido × piso (ficha 9) nos reais, com o teste pareado (ficha 5), comparado ao placar por família sintética (ficha 6); efeito (razão de Δ) nos reais vs sintéticos.

**Técnicas.** Spearman; placar pareado; Holm + rope; razão de efeitos.

**Implementação.** Reúso das fichas 2, 5, 6 e 9 sobre `problema ∈ {RE21, ESTOQUE40, DDMOP7}` (DDMOP7 só HV e estratificado — ficha 24). A torre já computou tudo em 22/08.

**Em quantos artigos aparece (dos 38).** Estudo de caso real: **20/38**; a pergunta "o sintético prediz o real?" não é contada como tipo.

**Estado.** T.

**Demais detalhes.** Caveats vinculantes nos reais: smsemoa × EST40 com seleção inoperante (D11); f3 do EST40 clipado (D12); moead_media × RE21 colapsa (D6); b5r colapsa ao prior (D7); e103 × RE21 troca de modelo intra-run (D14). Decisões que pede: se os reais entram como seção própria (ficha 23) ou distribuídos nas leituras. Relações: 6, 9, 23, 24.

### 23. Os três problemas reais como casos nomeados

**Fontes.** [RF] §3 (tabela: RE21 score 9,3 ACEITAR; ESTOQUE40 8,5 ACEITAR + pendências; DDMOP7 8,5 ACEITAR "como comparação de resolução declaradamente baixa") · [TP] D11 (smsemoa × EST40), D12 (f3 > 1 clipado), D13 (DDMOP7 resolução baixa), D14 (e103 × RE21), D15 (cadeia de citação do RE21) · [RDI] l.3367–3375 (C14: DDMOP7 nas tabelas descritivas com asterisco, texto pronto; inferencial estratificado por classe de operador) · [CAP4] §4.4 (`subsec:re21`, `subsec:ddmop7`, `subsec:estoque40`, `subsec:colapso-zona-morta`) · [ESQ] l.748 ("os 3 experimentos de dados reais") · [PL-38] R2#6 (20/38).

**O que analisa.** Cada problema real como um caso com a sua própria história: o que a formulação exige, como os algoritmos se comportaram, e o que só ali se vê (o quantizado do DDMOP7; o f1 negativo do EST40; a treliça do RE21 como "primeiro degrau da escada de dimensão").

**Dados.** ① (e ⑦ no offline) dos três problemas; ⑥ para os casos de mecanismo (e103 × RE21; c149 × DDMOP7); ⑤ (`params.zona_morta` só na rota Python — C2).

**Objetivo.** Não deixar os reais como "mais três linhas na matriz": cada um foi escolhido por uma razão declarada no cap. 4 e deve devolver essa razão.

**O que busca revelar.** RE21: o problema mais favorável ao surrogate; ESTOQUE40: um piso (SMS-EMOA) que deixa de ser piso por um detalhe de escala (f1 < 0), e um f3 cujo nadir não majoriza o interior; DDMOP7: uma comparação de resolução baixa em que a discriminação existe entre classes de operador e nos extremos, não no típico.

**Como é realizada.** Uma subseção (ou bloco) por problema: matriz/placar restritos (fichas 1, 9), a leitura estratificada do DDMOP7 (ficha 24), os caveats com frase pronta (D11–D14), e o que o problema acrescenta à pergunta-guia.

**Técnicas.** As das fichas 1, 9, 24; para o DDMOP7, HV apenas e contagens sobre `x_efetivo`.

**Implementação.** Filtros por problema sobre os caches; DDMOP7 exige a função de dedup por zona morta antes de qualquer contagem (C1) — não existe no notebook.

**Em quantos artigos aparece (dos 38).** Estudo de caso/aplicação real: **20/38**.

**Estado.** F-parcial (os reais estão nas matrizes; as histórias e os caveats não estão no texto).

**Demais detalhes.** A régua do DDMOP7 está ratificada (ideal [0;0], nadir 468/690; selo retirado); as 17 células s0 pré-errata estão sancionadas. D15 é ação do autor (baixar a fonte que define a formulação do RE21 e citá-la). Decisões que pede: seção própria × distribuídos; quais caveats entram no corpo e quais no apêndice. Relações: 22, 24, 62.

### 24. DDMOP7 — "que aquisição acha as redes esparsas boas?"

**Fontes.** [RDI] parte A52 (smoke-gate da zona morta: tabela por config de f1 < 1 na busca, ND da busca, melhor f2 — c141 f2 = 0,1304 (melhor global); pisos 0,1377; c149 1/153 e 0 ND: "propõe |x| ≥ τ em 98,8 % das coordenadas… não produz redes esparsas"; "o DDMOP7 saiu de 'não discrimina nada' para 'discrimina fortemente por estratégia de aquisição'"; errata da própria torre: "o front efetivo de cada célula tem 1 a 6 pontos distintos, mediana 3 — a zona morta consertou a DEGENERESCÊNCIA, não a QUANTIZAÇÃO") · [RF] §3 ("HV separa classes (p = 4,3e-26) mas não o topo-8 (0,6 %)") · [TP] C1 ("|ND| do DDMOP7 sem dedup x_efetivo é ~3× inflado; publicar |ND| efetivo + nº de F distintos"), C7 (convenção de empate ≤; "empate é REAL — grade 1/17, 1/690"), D13 · [CD] §T15.13 (regra de leitura do `x_efetivo`) · [RDI] C14 decidido.

**O que analisa.** No único problema com objetivos em grade (f1 = k/17, f2 = n/690), quatro medidas que a métrica padrão não dá: |ND| efetivo (após dedup por `x_efetivo`), número de valores distintos de F, melhor f2 alcançado (a ponta), e a fração de coordenadas propostas dentro da zona morta (a "vontade" de esparsidade de cada aquisição) — por classe de operador.

**Dados.** ① (x proposto → `x_efetivo = zona_morta(x_proposto)`; f já é do efetivo); ⑤ (τ vive no código pinado na rota MATLAB — C2); ⑥ (decisões).

**Objetivo.** Ler o DDMOP7 pelo que ele pode dizer (resolução baixa, discriminação por classe e nos extremos) e não pelo que não pode (IGD+, ranking fino no topo).

**O que busca revelar.** Que a codificação dá a todos a mesma capacidade de propor esparsidade e cada aquisição decide se a usa — o c149 (deep ensemble + desempate por σ) empurra para os extremos da caixa e não produz redes esparsas; o c141 atinge o fundo do front pooled.

**Como é realizada.** Por célula: dedup por `x_efetivo`, contagem de ND efetivo e de F distintos; melhor f2; fração de coordenadas na zona morta; agregação por config e por classe de operador; HV com a régua ratificada; teste entre classes (a torre reportou p = 4,3e-26 entre classes e p = 0,096 no topo-8).

**Técnicas.** Dedup por identidade de ponto efetivo; contagens; HV; Kruskal-Wallis/Friedman entre classes; convenção de empate ≤.

**Implementação.** Função `zona_morta(x)` (canônica no `ddmop7_bridge`/`T15.13`) aplicada à ① antes de contar; não existe no notebook (`n_nd` do cache está inflado para o DDMOP7). Sem sonda no DDMOP7 (D102.10).

**Em quantos artigos aparece (dos 38).** Estudo de caso real (20/38) e "diagnóstico do valor das amostras" (1/38); a leitura por esparsidade é própria deste problema.

**Estado.** N.

**Demais detalhes.** Caveats: b1 × DDMOP7 falha 29/30 (dacefit, objetivos quantizados — "material do capítulo 5", A53); b4 × DDMOP7 6/29 badsubscript (censura não-aleatória, D2); c154 × DDMOP7 nenhuma célula a orçamento pleno (D3); FE redundante idêntico entre configs (C3). Decisões que pede: quais das quatro medidas publicar; a classe de operador usada na estratificação. Relações: 23, 44, 58.

### 25. Métricas no espaço de decisão nos MMF (IGDX / PSP)

**Fontes.** [REG] d86 (estrutura do cap. 4 adotada: "§4.7 = casca-de-protocolo (declara reavaliação na função verdadeira padrão-f9 e IGDX/PSP nos MMF; escolhas finais na rodada do cap. 5, d44–d47)") · [PL-38] R1#3 ("para os MMF, adicionar IGDX/PSP — diversidade no ESPAÇO DE DECISÃO"), R1#8 ("para MMF, plotar também o ESPAÇO DE DECISÃO (múltiplos Pareto sets)") e aba Plano ("IGDX = cálculo, não export") · [CAP4] `tab:problemas` (MMF1/MMF4/MMF11_L/MMF16_20: "no espaço de decisão") · [MET] (não há IGDX/PSP).

**O que analisa.** Nos quatro problemas multimodais multiobjetivo (MMF), a cobertura dos múltiplos conjuntos de Pareto equivalentes no espaço de decisão — o que o espaço de objetivos esconde por construção (dois pontos distintos de x com o mesmo f).

**Dados.** ① (x das soluções ND); M (o conjunto de Pareto verdadeiro dos MMF — a conferir em `problems.py`).

**Objetivo.** Medir a multimodalidade que motivou a inclusão da suíte MMF; sem IGDX, o MMF é lido como se fosse um ZDT.

**O que busca revelar.** Se a incerteza (o σ como sinal de exploração) ajuda a manter soluções em bacias distintas — a pergunta "multimodalidade" do cap. 4 no seu terreno próprio.

**Como é realizada.** IGDX = IGD calculado no espaço de decisão contra o PS verdadeiro; PSP = razão cobertura/IGDX (Yue, Qu & Liang 2018); matriz algoritmo × MMF; gráfico do espaço de decisão da execução mediana.

**Técnicas.** IGDX, PSP, CR (cover rate); visualização 2D do espaço de decisão (MMF1/4/11_L são D = 2).

**Implementação.** Não existe: `metrics.py` não tem IGDX/PSP nem o PS verdadeiro dos MMF; exige código novo e a fonte do PS (o relatório CEC'2019 dos MMF traz o gerador).

**Em quantos artigos aparece (dos 38).** **0/38** — nenhuma das métricas de decisão (IGDX, PSP, CR) aparece na aba Métricas.

**Estado.** N (e exige implementação).

**Demais detalhes.** É a única métrica "declarada" (d86) que não existe no pipeline. Decisões que pede: entra ou cai; se entra, com que fonte de PS. Relações: 19 (pergunta da multimodalidade), 54.

---

# Grupo D — Quando: trajetórias e orçamento

### 26. Trajetórias de convergência — mediana + IQR × fração do orçamento, com a banda dos pisos

**Fontes.** [NB] célula [22] (bloco A4: `trajetorias_2026-08-17.parquet`, 47.016 linhas: alg, problema, semente, fe, frac_fe, igd_plus, hv; 8 vitrines ZDT1, ZDT4, DTLZ1, DTLZ2, WFG4, MMF4, BBOB_F5, RE21; 6 destaques c262, c141, b3, c122, b1, e7; banda min–max das medianas dos 4 pisos; `fig57_trajetorias`) · [MET] `trajectory(F_raw, fe_index, problema, n_checkpoints=20)` · [CAP5] §5.7 (`fig:trajetorias`) · [PL-38] R1#4 (score 9; "convenção c241/e7/c262; EMMOEA converge devagar e acelera depois") e R2#5 (22/38) · SPEC §13 (mediana + IQR p25–p75).

**O que analisa.** A evolução da métrica ao longo do orçamento (IGD+ do ND acumulado das avaliações reais até cada checkpoint), por algoritmo e problema, sobre as sementes.

**Dados.** ① (fe_index e F de todas as avaliações — o ND acumulado por corte de fe_index); C (trajetórias em 20 checkpoints).

**Objetivo.** Mostrar QUANDO cada método ganha — cedo ou tarde no orçamento — o que os endpoints escondem.

**O que busca revelar.** Perfis: quem sai na frente e estagna; quem começa devagar e acelera; se a adaptatividade online aparece na segunda metade; onde a banda dos pisos é atravessada.

**Como é realizada.** Para cada célula, 20 checkpoints igualmente espaçados em fe; métrica sobre o ND acumulado até o checkpoint; mediana e IQR sobre as sementes; eixo x = fração do orçamento (comparável entre problemas de D diferente), eixo y = IGD+ em log; banda cinza = envelope das medianas dos 4 pisos; painéis por problema-vitrine.

**Técnicas.** Mediana + IQR; escala log; banda de referência; fração de orçamento como eixo comum.

**Implementação.** `metrics.trajectory` por célula (a "célula-fonte" que gerou o cache vive fora do notebook); [NB] célula [22] desenha. Cobre os 17 algoritmos online e 30 sementes; o offline não tem trajetória (a ① é o dataset).

**Em quantos artigos aparece (dos 38).** Curvas de convergência: **22/38** (R2#5), sem teste formal.

**Estado.** F (8 vitrines; a escolha de vitrines e destaques foi da leva de 17/08).

**Demais detalhes.** Vale a regra editorial [ESQ] l.761: uma amostra no texto, o resto no repositório. Decisões que pede: critério de escolha das vitrines (por característica? por surpresa?); IGD+ e/ou HV; quantos algoritmos por painel. Relações: 27, 28, 29, 30.

### 27. A comparação sob orçamento apertado — o placar recomputado no prefixo

**Fontes.** [CAP4] l.364 (promessa explícita: "E o teto não é a lente: qualquer corte menor pode ser analisado a posteriori pelo prefixo das avaliações — o Capítulo 5 pode perguntar como a comparação muda quando o orçamento aperta, sem rodar nada de novo") · [PL-38] aba Plano ("contraste q=1 × q=10 a FEs-iguais — recorte de fe_index ≤ 31D−1", o mesmo princípio) · [NB] célula [22] (o cache de trajetórias já tem 20 cortes).

**O que analisa.** As matrizes, o placar assistido × piso e o ranking (fichas 1, 2, 9) recomputados em cortes do orçamento (por exemplo 25 %, 50 %, 75 %, 100 %).

**Dados.** ① (prefixo por fe_index) ou C (trajetórias nos checkpoints).

**Objetivo.** Cumprir a promessa do cap. 4 e responder a uma pergunta prática: se o orçamento fosse menor, o veredito mudaria?

**O que busca revelar.** Se o surrogate paga mais no início (quando o piso ainda não convergiu) e perde a vantagem no fim, ou o inverso; se o ranking é estável ao orçamento (Spearman entre cortes).

**Como é realizada.** Para cada corte: a métrica do ND acumulado até o corte (já nos checkpoints); refazer o placar pareado e o rank médio; Spearman entre o ranking do corte e o do orçamento pleno; curva "taxa de vitórias do assistido × fração do orçamento".

**Técnicas.** As das fichas 1/2/9 por corte; Spearman; curva de vitórias.

**Implementação.** Filtrar `TR` por `frac_fe` próximo do corte (os checkpoints são discretos; escolher o mais próximo) e reaplicar as funções das fichas 2 e 9. Não existe no notebook.

**Em quantos artigos aparece (dos 38).** Implícita nas curvas de convergência (22/38); como "placar a orçamento reduzido" não foi contada.

**Estado.** N.

**Demais detalhes.** É também a lente natural para as células ⚪ do teto (ficha 29): no corte comum, elas entram sem ressalva. Decisões que pede: os cortes; quais leituras recomputar. Relações: 9, 26, 29.

### 28. Quem mais melhora na segunda metade — Δ meio → fim

**Fontes.** [NB] célula [22] (impressão "quem mais melhora na 2ª metade (Δ mediano meio→fim, 8 problemas-vitrine)": mediana em 0,45 < frac < 0,60 vs > 0,99) · [CAP5] §5.7.

**O que analisa.** A melhoria relativa da mediana do IGD+ entre a metade e o fim do orçamento, por algoritmo.

**Dados.** C (trajetórias).

**Objetivo.** Um número que resume o perfil temporal: quem ainda está aprendendo no fim.

**O que busca revelar.** Adaptatividade tardia (o surrogate melhora com mais dados) vs estagnação (o modelo satura ou degenera — ligação com a ficha 31).

**Como é realizada.** (mediana_meio − mediana_fim)/mediana_meio por algoritmo, sobre os problemas-vitrine ou sobre todos.

**Técnicas.** Razão de medianas.

**Implementação.** Três linhas no notebook; extensível a todos os problemas.

**Em quantos artigos aparece (dos 38).** Dentro das curvas (22/38); não contada como número.

**Estado.** F (número solto, 8 vitrines).

**Demais detalhes.** Sensível à escolha de "meio" (janela 0,45–0,60); é um resumo da ficha 26, não uma análise independente. Relações: 26, 31.

### 29. A lente de prefixo para as células que bateram no teto de parede

**Fontes.** [CAP4] l.378 ("quem o atinge é encerrado com aborto limpo — os dados até ali são gravados íntegros, porque a curva parcial É dado, e a célula entra na análise pela lente de prefixo, com a ressalva declarada"), `tab:padronizacoes` l.407 ("a célula que estoura vira categoria declarada de resultado, não dado descartado") e `tab:limitacoes` l.488 · [RDI] l.3347–3352 (C8 parcial: "as primeiras análises usam SÓ as que chegaram ao fim — 16.020 de 16.811; o destino das 615 células ⚪ teto fica para decisão posterior") · [TP] C8 (FE comum por problema: c149 × DDMOP7 526; c154 × DDMOP7 ≤ 266; c154 × EST40 447; c262 × EST40 ≤ 612 ou perda seca s0–7; e81 × EST40 464; c122 85 ⚪ em FE comum) · [TC] (políticas P1 = 12.761 plenas; P2 = P1 + teto = 13.371; ranking sob as duas) · [CEN] (motivo teto_wall = 615; concentradas em c154 439 failed, c262 158, c122 98, c149 72).

**O que analisa.** O que acontece com as leituras (matrizes, placar, ranking) quando as 615 células do teto entram pela lente de prefixo — no FE comum por problema — em vez de ficarem fora.

**Dados.** ① (prefixo até o FE comum); C (trajetórias); M (censo: motivo teto_wall; FE comum por problema).

**Objetivo.** Honrar a regra do cap. 4 ("categoria declarada, não dado descartado") sem contaminar as comparações a orçamento pleno.

**O que busca revelar.** Se a exclusão das células caras enviesa contra (ou a favor de) os algoritmos caros (JES, qNEHVI, θ-DEA-DP, LBN-MOBO) — a torre mediu que a sensibilidade do ranking às políticas P1/P2 é pequena, mas a decisão é do autor.

**Como é realizada.** Definir o FE comum por (algoritmo × problema) onde há células ⚪; recomputar as leituras no corte comum (ficha 27); comparar P1 × P2 × FE comum.

**Técnicas.** Corte por prefixo; comparação de rankings (Spearman); tabela de n efetivo.

**Implementação.** Cruzar `censo_final.csv` (status/motivo) com as trajetórias; a coluna `chegou_ao_fim` da aba `base_dados` já identifica as células; o FE comum vem do próprio ① (min do fe_final das células ⚪).

**Em quantos artigos aparece (dos 38).** **0/38** — nenhum artigo reporta células interrompidas por teto de parede como categoria.

**Estado.** N (e é decisão: o destino das 615 ⚪).

**Demais detalhes.** Regra da torre: "filtre por motivo, nunca por status" (A10-v). Nota: c154 tem 439 células failed no censo (125 teto sancionadas + escada + em voo — D0), logo é o algoritmo mais afetado por qualquer política. Decisões que pede: a política (P1 × P2 × FE comum) e como declará-la. Relações: 27, 57, 60.

### 30. Monotonicidade das curvas — o teste de sanidade do pipeline

**Fontes.** [DOS] item 1 ("MONOTONICIDADE: 15/15 configs, 3/3 problemas, ZERO violações — o teste de sanidade mais básico do pipeline, e passa limpo") · [MET] (o ND acumulado só pode melhorar IGD+ e HV a cada checkpoint).

**O que analisa.** Se as trajetórias (ficha 26) são monotônicas (IGD+ não-crescente; HV não-decrescente) em todas as células — o que é propriedade do ND acumulado e, portanto, um invariante do pipeline.

**Dados.** C (trajetórias) ou ① direto.

**Objetivo.** Provar que a acumulação, a normalização e a régua não introduzem artefatos (uma violação indicaria bug de contabilidade, régua furada ou clip).

**O que busca revelar.** Nada científico; é o "0 violações" que autoriza as demais fichas do grupo.

**Como é realizada.** Para cada célula, diff entre checkpoints consecutivos; contagem de violações; tolerância numérica declarada.

**Técnicas.** Verificação de invariante.

**Implementação.** `TR.sort_values(["alg","problema","semente","fe"]).groupby(...).igd_plus.diff() > tol` — uma célula de notebook.

**Em quantos artigos aparece (dos 38).** **0/38** (é sanidade interna).

**Estado.** T (na R1, sobre 3 problemas e semente 0); não refeita sobre o canônico.

**Demais detalhes.** Material de apêndice ou de uma frase na §5.1 ("contrato de leitura"). Relações: 26, 62.

---

# Grupo E — O modelo por dentro: a sonda, a fantasia, o infill e o mecanismo

> A sonda é o instrumento que "nenhum trabalho do corpus dispõe" ([CAP4] l.450): 2.000 pontos Sobol fixos por problema — os mesmos para todos os algoritmos, sementes e gerações — que cada modelo re-prediz a cada retreino (online a cada 2 gerações; offline 20.000 pontos, uma vez), com os valores verdadeiros pré-computados fora do orçamento (gabarito `data/sonda/sonda_{problema}.parquet`; join por posição; eixo oficial `fe_treino_max`). Invariante: a sonda não altera a busca (camada ① com e sem sonda idêntica — prova T11; teto de verificabilidade declarado, D10 da torre). Sem sonda: DDMOP7 (D102.10) e os pisos online; o piso offline `moead_media` tem sonda com σ nulo. O esqueleto reservou à sonda a §5.4 com 5 páginas, "a segunda maior seção do capítulo" (d103.7), em quatro dimensões: acurácia da média · preservação da ordem · calibração do σ · discriminação do σ ([ESQ] l.752).

### 31. Sonda, dimensão 1 — a acurácia da média ao longo do orçamento (o modelo aprende? esquece?)

**Fontes.** [ESQ] l.752 (d103.7) · [NB] célula [24] (bloco A6, painel (a): RMSE mediano nos 2.000 pontos × fração do orçamento consumida no retreino; cache `sonda_2026-08-17.parquet`, 150.364 linhas, 8 algoritmos b1, b3, b4, c141, c217, c238, e7, e74 × sementes 0–10; colunas alg, problema, semente, fe_treino_max, rmse, rho_sigma_erro, cobertura_2sigma, modelo) · [CAP5] §5.8 (`fig:sonda`) · [DOS] item 2-bis (c262: "GP aprende, WAPE −39/−45 %"; e81: "MAE out-of-sample cai monotônico nos 3"; e7: "o ensemble NÃO aprende globalmente (DTLZ2 WAPE 21,8 → 26,4 %) — esquecimento induzido pelo SelectTrainData"; b3: "sonda PLANA (WAPE 14 % fixo com treino ×3)"; c141: "divergência do RBF no MMF1 confirmada bloco a bloco (mu → [−145, 210], MAE ×8,5)"; e74: "RBF afiada perto do arquivo, mas EXPLODE fora do suporte (mu até 770; f_true máx 8,6)"; c238: "aprende e calibra no DTLZ2 (WAPE f2 8,1 → 0,9 %); degeneração numérica no fim do MMF1 (mu até 339, θ no bound)") · [CD] (regras R4: join por posição; `fe_treino_max` como eixo; sigma_dict antes da ③; in-sample via fe_treino_max não-monotônico em b1/b4/c217) · [PL-38] R1#6 (score 9: "LACUNA no corpus… b3, e86, e104, c262, e17 usam σ mas NUNCA o validam; e7 é a exceção rara") e R2#10 (16/38).

**O que analisa.** O erro da média predita (RMSE, ou WAPE) nos 2.000 pontos fixos, a cada retreino, em função da fração do orçamento já consumida — a curva de aprendizado do surrogate, comparável entre algoritmos porque os pontos são os mesmos.

**Dados.** ③ regime `sonda` (μ por ponto × retreino; `fe_treino_max`); S (f verdadeiro dos 2.000 pontos); ⑤ (`sigma_dict` — a semântica de μ/σ por algoritmo, obrigatória antes de ler a ③); C (cache).

**Objetivo.** Dar mecanismo ao resultado: se um algoritmo perde, o modelo dele não aprendeu? Se ganha, aprendeu a partir de quando?

**O que busca revelar.** Três formas de curva (ficha 35): a que cai (aprende), a plana (o modelo não melhora com mais dados) e a que sobe ou explode (degenera) — e o momento do orçamento em que cada uma se instala.

**Como é realizada.** Por célula e retreino: RMSE entre μ e f nos 2.000 pontos (por objetivo e agregado); normalização do eixo x pelo orçamento (fe_treino_max/(31D−1)) em buckets de 0,1; mediana sobre problemas × sementes; uma curva por algoritmo em escala log.

**Técnicas.** RMSE (e WAPE, que a torre usa por ser adimensional); buckets de fração de orçamento; mediana; log.

**Implementação.** A "célula-fonte" que gerou o cache fica fora do notebook: lê a ③ (regime == sonda), casa por posição com o gabarito S, aplica `sigma_dict`, agrega por (célula, fe_treino_max). O notebook ([NB] célula [24]) só desenha. Cobertura atual do cache: 8 algoritmos com camada ③ local e 11 sementes — as ③ volumosas dos demais (c122, c149, c154, c262, e81) moram no bucket; o `_FONTES.csv` do corpus congelado diz qual fonte local foi usada por camada. Sonda sem σ (c141, RBF) rende só esta dimensão.

**Em quantos artigos aparece (dos 38).** Acurácia/calibração do surrogate: **16/38** (R2#10); RMSE/MAE do surrogate como métrica: 12/38. A forma "mesmos pontos fixos, a cada retreino, para todos os algoritmos" não aparece.

**Estado.** F (8 algoritmos × 11 sementes).

**Demais detalhes.** Caveats: a sonda do c122 mede a ordem contra a dominância real (DI-16.2: referência = população selecionada), não μ; a do e74 mede a RBF do ponto escolhido (DI-13.6); a ③ do c217 é "leitura proibida" sem `sigma_dict` (regra 3 do R4). Decisões que pede: RMSE × WAPE; por objetivo × agregado; cobertura (8 vs 13 algoritmos — exige baixar as ③ do bucket ou confirmar que estão no corpus congelado). Relações: 19, 32–36, 39.

### 32. Sonda, dimensão 2 — a preservação da ordem (μ ordena como f? o classificador acerta a classe?)

**Fontes.** [ESQ] l.752 (d103.7: "preservação da ordem") · [DOS] item 2-bis (b4: "a sonda REFUTOU o 'não discrimina': AUC 0,75 no ZDT1, máx 0,92; aprende no DTLZ2 0,53 → 0,70, ρ = 0,80 com o treino"; c122: "e(z) correlaciona com dominância real, ρ 0,72–0,75, e satura POR VITÓRIA; fraqueza real só no MMF1 (ρ → 0,04, confiança = 1,0)"; e74: "o PNN INVERTE no fim do ZDT1 (ρ −0,34)"; c141: "spearman ~0,05" na divergência) · [RDI] DI-43 D11 ("TODAS as melhorias de instrumentação, incl. sonda estratificada dos classificadores") · [CD] (regime `sonda_estratificada` nunca junto da `sonda`) · [PL-38] aba Métricas ("taxa de acerto/erro do classificador": CSEA e IBEA-MS, 2/38; Spearman ρ: U-RankMOEA, 1/38).

**O que analisa.** Não o valor, mas a ordem: se a ordenação dos 2.000 pontos por μ preserva a ordenação por f (correlação de postos); para os classificadores (b4, c217) e para o preditor de dominância (c122), se a classe/score prevista acerta a classe real (AUC, acurácia, precisão/revocação) — porque é a ordem, não o valor, que a seleção consome.

**Dados.** ③ regime `sonda` (μ ou score/classe) e `sonda_estratificada` (classificadores); S.

**Objetivo.** Medir o que o otimizador realmente usa: um modelo com RMSE alto pode ordenar bem (e vencer); um com RMSE baixo pode inverter a ordem no fim (e perder).

**O que busca revelar.** Onde a ordem se mantém ou se inverte ao longo do orçamento; para os classificadores, se o "não discrimina" é real (o retrato de 17/08 os devolveu ao cap. 3 sem essa medida).

**Como é realizada.** Por célula e retreino: Spearman ρ entre μ e f (por objetivo) nos 2.000 pontos; para classificadores, AUC/acurácia do score contra o rótulo real (dominância/pertencimento calculado a partir de f no gabarito, com a mesma referência que o algoritmo usa); curvas × fração do orçamento.

**Técnicas.** Spearman ρ; AUC-ROC; acurácia/precisão/revocação; para c122 a correlação entre e(z) e a dominância real.

**Implementação.** A mesma célula-fonte da ficha 31, acrescentando `spearmanr` e, para os classificadores, a construção do rótulo real a partir do gabarito (a sonda estratificada foi desenhada para isso — DI-43 D11). Não está no cache.

**Em quantos artigos aparece (dos 38).** Dentro de acurácia/calibração (16/38); taxa de acerto do classificador em 2/38; Spearman em 1/38.

**Estado.** N (medido pela torre em células isoladas; não no notebook).

**Demais detalhes.** É a dimensão que explica o paradoxo dos classificadores (perdem do piso mas "discriminam") e a divergência do c141 (RBF sem σ, mas com ordem). Decisões que pede: a estatística de ordem por tipo de surrogate; o rótulo real dos classificadores. Relações: 16, 31, 33, 35.

### 33. Sonda, dimensão 3 — a calibração do σ (a incerteza reportada é confiável?)

**Fontes.** [ESQ] l.752 (d103.7: "calibração do σ") · [CAP4] l.450 ("é ela que sustenta a análise de calibração do Capítulo 5") · [NB] célula [24] (painéis (b) ρ de Spearman entre σ e |erro| e (c) cobertura empírica de μ ± 2σ contra o nominal 95,4 %) · [CAP5] §5.8 (`tab:calibracao`: EIM ρ 0,62 / cobertura 94 %; K-RVEA 0,55 / 92 %; EDN-ARMOEA 0,40 / 53 %; ParEGO 0,18 / 2 %) · [DIA] 17/08 ("σ do ParEGO cobre 1,8 % vs 92–94 % dos GPs modernos; EDN 53 %") · [DOS] item 2-bis (c262 calibração 0,978; b1 "sobreconfiança tardia, cobertura 2σ → 0,5"; e7 "σ do dropout otimista, cobertura 0,37–0,41"; c154 "pior E mais confiante, cobertura 0,936 → 0,758"; e103 cobertura 0,956; e81 "MMF1-obj1 superconfiante") · [PC6] §4.3 (M9: "o campo inteiro consome um σ cuja qualidade quase ninguém mede") · [P37] §10 (desafio "calibração quase ausente — só a minoria mede a medição: b15 ECE, c59 κ, c81 AUCE, c250; conformal só como alternativa rejeitada (c267)" — hoje classificado como "trabalho futuro + gancho cap. 6") · [CHK] N15 (nenhum número de b15) · [PL-38] aba Métricas (ECE 2/38: U-RankMOEA = b15, UA-DBO = c59; AUCE 1: c81; CICP 1: NSGAII-DR = b7; cobertura empírica de IC 1: c59; Brier, ACE, MCE, NLPD 1 cada: b15; "STD da variância estimada" 1: e7) · [PL-38] R1#6.

**O que analisa.** Se o σ reportado tem a magnitude certa (cobertura: a fração dos 2.000 pontos cujo f cai em μ ± 2σ, contra 95,4 % nominal) e se ele ordena o erro (ρ entre σ e |μ − f|) — ao longo do orçamento.

**Dados.** ③ regime `sonda` (μ e σ; `sigma_dict` define o que σ é em cada algoritmo: desvio, variância, MSE do Kriging, dispersão do dropout…); S.

**Objetivo.** Transformar o "argumento de carga" do survey (a incerteza do GP é a mais confiável para dirigir a otimização) em evidência — e responder empiricamente à ferida M9 que o cap. 6 quer ecoar.

**O que busca revelar.** Sobreconfiança (cobertura muito abaixo do nominal: ParEGO, EDN-ARMOEA), subconfiança, e a deriva ao longo do orçamento (b1 fica sobreconfiante no fim; c154 fica pior e mais confiante ao mesmo tempo).

**Como é realizada.** Por célula e retreino: cobertura = média de 1[|f − μ| ≤ 2σ]; ρ = Spearman(σ, |f − μ|); curvas × fração do orçamento; tabela por algoritmo (mediana global); opcionalmente curva de calibração (cobertura empírica × nível nominal z) e métricas resumo (ECE de regressão, AUCE, CICP — as que os poucos artigos que medem calibração usam).

**Técnicas.** Cobertura empírica de intervalos; Spearman; curva de calibração / diagrama de confiabilidade; ECE/AUCE/CICP como resumo; NLL/CRPS/sharpness como alternativas (não usadas até aqui).

**Implementação.** Célula-fonte da ficha 31 (o cache já traz `rho_sigma_erro` e `cobertura_2sigma` por retreino); [NB] célula [24] desenha; a tabela do cap. 5 é a mediana por algoritmo. O `sigma_dict` de cada manifesto converte a coluna σ para desvio-padrão antes da cobertura (ex.: b1 exporta a sonda ESCALAR reconstruída — D47).

**Em quantos artigos aparece (dos 38).** Acurácia/calibração: 16/38 (R2#10), mas **calibração propriamente dita (métrica de calibração de intervalo/probabilidade) em 4 dos 38** — b15 (ECE/ACE/MCE/Brier/NLPD; números inutilizáveis por N15, o desenho conta), c59 (ECE, cobertura empírica), c81 (AUCE), b7 (CICP) — e o e7 mede o desvio da variância estimada. O painel do corpus-130 registra o conflito "3 de 128 vs 5" (M9, Conflito 3) — só entra no texto com a definição colada.

**Estado.** F-parcial (8 algoritmos × 11 sementes; sem os BO com ③ no bucket).

**Demais detalhes.** É a ficha que muda a partição P7 da §3.7: "calibração quase ausente" está hoje como trabalho futuro e a bateria a ataca. Caveat: "cobertura 2σ" pressupõe σ como desvio-padrão gaussiano — para dropout/ensemble (DE) e para classificadores a leitura precisa de tradução (N14). Decisões que pede: as métricas de calibração a publicar; a relação com M9 e com o eco do cap. 6; o tratamento dos algoritmos sem σ gaussiano. Relações: 31, 34, 36, 37, 39.

### 34. Sonda, dimensão 4 — a discriminação do σ (a incerteza separa os candidatos de erro grande?)

**Fontes.** [ESQ] l.752 (d103.7: "discriminação do σ", a quarta dimensão nomeada, em negrito no esqueleto) · [RDI] DI-09 (instrumentação de assertividade dos surrogates) · [DOS] item 2-bis (b4: AUC 0,75; e o uso de AUC como medida de discriminação).

**O que analisa.** Distinto da calibração (magnitude certa) e da ordem do erro (ρ): se o σ, usado como detector, separa os pontos em que o modelo erra muito dos pontos em que acerta — a propriedade que uma aquisição exploratória explora (ir onde σ é alto porque lá o erro é alto).

**Dados.** ③ regime `sonda` (σ; para classificadores, a confiança/score); S.

**Objetivo.** Medir a utilidade operacional do σ, não a sua honestidade: um σ mal calibrado pode ainda discriminar bem (e servir à busca); um σ calibrado na média pode não discriminar (e ser inútil).

**O que busca revelar.** Para cada algoritmo, se "alto σ" é um sinal informativo de "alto erro" — e se essa capacidade muda com o orçamento.

**Como é realizada.** Por célula e retreino: rotular os 2.000 pontos por erro grande (|f − μ| acima do quantil q, por exemplo o decil superior); AUC-ROC do σ como classificador desse rótulo; precisão no top-k de σ; curvas × fração do orçamento.

**Técnicas.** AUC-ROC; precisão@k; curvas de ganho.

**Implementação.** Célula-fonte da ficha 31 com `roc_auc_score(erro_grande, sigma)`; não está no cache.

**Em quantos artigos aparece (dos 38).** **0/38** como medida nomeada (a mais próxima é a calibração, 4/38).

**Estado.** N.

**Demais detalhes.** É a ponte entre a sonda e a função da incerteza (grupo C, ficha 20): as classes de "oportunidade" (OV/OM/OL) precisam de discriminação; as de "ameaça" (AV/AM/AR) precisam de calibração. Decisões que pede: o limiar de "erro grande"; a estatística. Relações: 33, 36, 44.

### 35. A tipologia das curvas da sonda — aprende, plana, degenera

**Fontes.** [DOS] item 2-bis (b3/DTLZ2 "sonda PLANA"; c141/MMF1 e c238/MMF1 "degeneração"; e74 "explode fora do suporte"; e7 "esquecimento"; c262/e81/c238-DTLZ2 "aprende") · [DOS] item 1 ("as 3 leituras que saltam da tabela") · leitura da mineração de 06/09.

**O que analisa.** A forma de cada curva da ficha 31 (e das fichas 32–33), classificada em três tipos, por algoritmo × problema: cai (aprende), não cai (plana), sobe/explode (degenera) — e a associação entre o tipo e o resultado (ficha 9).

**Dados.** C (sonda) ou ③ + S.

**Objetivo.** Converter 8 × 25 curvas em uma tabela legível: que algoritmo aprende em que família de problema.

**O que busca revelar.** Se as derrotas para o piso coincidem com curvas planas ou degeneradas (o modelo não aprendeu) e as vitórias com curvas que caem — a versão mais direta da "lei do teto" (ficha 39).

**Como é realizada.** Por célula: inclinação da curva (RMSE no último terço vs primeiro terço; razão), com limiares para os três tipos; tabela algoritmo × problema colorida por tipo; cruzamento com Δ da ficha 9 (tabela de contingência tipo × vitória/derrota).

**Técnicas.** Razões de RMSE por terço; classificação por limiar; tabela de contingência; opcionalmente teste exato de Fisher.

**Implementação.** Agregação simples sobre `sonda_2026-08-17.parquet` (RMSE por bucket de fração); junção com a matriz `D` da ficha 9.

**Em quantos artigos aparece (dos 38).** **0/38**.

**Estado.** N.

**Demais detalhes.** Os limiares definem a tipologia; declará-los é o que a torna auditável. Relações: 9, 16, 31, 39.

### 36. A sonda por classe de medição — a qualidade do σ depende de onde o número vem?

**Fontes.** Pergunta-guia da §4.1 aplicada ao eixo de medição (VA/VN/DE/EE/DG) · [PC6] §3 (RQ2 "como a incerteza é medida" — o cap. 6 registra a delimitação de `medição` "e é onde a ferida da calibração ecoa") · [CHK] N14 (VN × DE: "a variância de ensemble aproxima SÓ a parcela EPISTÊMICA; o σ² do GP é TOTAL — não são a mesma espécie de número") · [DOS] item 2-bis (GPs: c262, e81, c238 calibrados; dropout: e7 otimista; Kriging DACE: b1 sobreconfiante tardio; ensemble: c149).

**O que analisa.** As dimensões 3 e 4 da sonda (fichas 33–34) agregadas pela classe de medição de cada algoritmo: a posterior fechada do GP (VA) é mais calibrada que a dispersão de um ensemble/dropout (DE)? que a saída nativa de um modelo não-GP (VN)?

**Dados.** C (sonda) / ③ + S; M (classe de medição de cada algoritmo do roster — da planilha, que vence).

**Objetivo.** Dar à RQ2 uma resposta experimental: a taxonomia da medição prediz a qualidade da medida?

**O que busca revelar.** Se as classes se separam em calibração/discriminação (a hipótese de N14: espécies diferentes de número) — com o hedge de n pequeno por classe.

**Como é realizada.** Tabela classe de medição × {cobertura mediana, ρ mediano, AUC mediano}, com n de algoritmos por classe; leitura ao longo do orçamento.

**Técnicas.** Agregação por classe; mediana; sem teste (n por classe pequeno).

**Implementação.** `groupby` do cache da sonda por classe (dicionário algoritmo → classe de medição).

**Em quantos artigos aparece (dos 38).** **0/38**.

**Estado.** N.

**Demais detalhes.** Armadilha #1 (N14) — classificar a camada que produz o número que o otimizador consome. Decisões que pede: se entra como tabela ou como parágrafo da ficha 33. Relações: 20, 33, 34.

### 37. A calibração por objetivo — a "agregação silenciosa de m sigmas"

**Fontes.** [P37] §10 (desafio M21: "agregação silenciosa de m sigmas — média × média geométrica × volume × diâmetro, e nenhum artigo justifica" — destino: trabalho futuro) · [CD] (a ③ traz `mu_*`/`sigma_*` por objetivo) · [DOS] item 2-bis (c238: "WAPE f2 8,1 → 0,9 %"; e81: "MMF1-obj1 superconfiante"; b5m: "o GP do obj-2 degenera").

**O que analisa.** A calibração e a acurácia por objetivo (não agregadas), e a relação entre a qualidade por objetivo e a regra de agregação que cada algoritmo usa para produzir o número escalar que consome.

**Dados.** ③ regime `sonda` (μ/σ por objetivo); S; ⑤ (`sigma_dict` — a semântica por objetivo).

**Objetivo.** Ver se a incerteza é boa em um objetivo e ruim em outro (o que a agregação esconde) — e se a agregação usada preserva ou destrói a calibração.

**O que busca revelar.** Assimetrias por objetivo (o obj-2 do b5m degenera; o obj-1 do e81 é superconfiante no MMF1) que a leitura agregada não mostra.

**Como é realizada.** As medidas das fichas 31/33 por objetivo; tabela algoritmo × objetivo × problema; para os algoritmos que agregam (média, produto, volume), a mesma medida sobre o agregado.

**Técnicas.** As das fichas 31/33, por objetivo.

**Implementação.** Célula-fonte da ficha 31 sem agregar objetivos (o cache atual agrega).

**Em quantos artigos aparece (dos 38).** **0/38** como análise; o desafio M21 nasceu da leitura do corpus (nenhum artigo justifica a agregação).

**Estado.** N.

**Demais detalhes.** Converte um "trabalho futuro" da §3.7 em evidência parcial do cap. 5, se entrar. Relações: 33, 36.

### 38. Heterocedasticidade — o erro do modelo por região do espaço

**Fontes.** [CAP4] l.102 ("Densidade não uniforme cria heterocedasticidade: pouca informação onde a busca mais precisa") · [PC6] §6.4 e [ESQ] l.768 (d31: "a heterocedasticidade medida — WAPE 5 %–37 %, pp. 9–10 — pode justificar o fator-ruído do cap. 4 em 1 frase"; da prova de conceito) · [PL-38] aba Métricas ("variância preditiva (mapa de cor)", 1/38) · leitura da mineração de 06/09.

**O que analisa.** Se o erro do modelo (e o σ) variam sistematicamente com a região do espaço: proximidade da frente verdadeira, quantil do valor do objetivo, distância ao arquivo de treino, dimensão — em particular nos problemas de densidade não uniforme (ZDT6, DTLZ4, WFG…).

**Dados.** ③ regime `sonda` (μ/σ por ponto); S (f e x dos 2.000 pontos); ① (arquivo de treino, para a distância ao suporte).

**Objetivo.** Responder a uma das seis perguntas do cap. 4 (ficha 19) e dar à d31 a sua frase.

**O que busca revelar.** Se o modelo erra mais exatamente onde a busca precisa acertar (perto da frente) e se o σ acompanha (sabe que erra) ou não (heterocedasticidade não capturada).

**Como é realizada.** Estratificar os 2.000 pontos por região (bins de distância à frente; bins de distância ao ponto de treino mais próximo); RMSE, cobertura e ρ por bin; comparação entre problemas de densidade uniforme e não uniforme.

**Técnicas.** Estratificação; RMSE/cobertura por bin; teste de Levene entre bins (opcional); mapas de calor no espaço de objetivos (M = 2).

**Implementação.** Célula-fonte da ficha 31 com bins por região (a distância à frente vem de `reference_set`; a distância ao suporte, da ① até `fe_treino_max`). Não existe.

**Em quantos artigos aparece (dos 38).** **0/38** como análise; o mapa de variância preditiva aparece em 1/38.

**Estado.** N.

**Demais detalhes.** É a análise que a característica "densidade não uniforme" do cap. 4 pede e que nenhuma outra ficha cobre. Relações: 19, 31, 33.

### 39. A lei do teto relida — quando o modelo é bom o bastante, o teto vem do surrogate, não do critério

**Fontes.** [ESQ] l.756 (d103.10, "lugar 3 de 4": "o cap. 4 declarou a hipótese; aqui ela é relida à luz do que a bateria mostrou, com a sonda fornecendo o mecanismo"; 🚫 numeral agregado dos artigos) · [CHK] adendo 31/07 (resposta preparada: "(2) quando o modelo é bom o bastante, o teto é dado pela qualidade do surrogate, não pelo critério — e a sonda mede exatamente essa variável, mostrando a partir de quando o teto se instala; (3) o corpus já relata o fenômeno, emo1 §5 p. 879: 'the subtle differences in infill fitness landscape have little impact because of an imperfect model'… e o achado é simétrico: se os métodos se equalizarem, confirmamos emo1 em 25 problemas — se não, o achado é mais forte") · [PC6] §4.2 (eco M14: "informa se a hipótese se sustentou: sim, não, ou sob quais condições") · [P37] §8 (a hipótese H1 candidata sai do "gradiente de exigência"; pendência P-1 do Guilherme) · verificação de 06/09: a hipótese ainda NÃO está escrita nos `.tex` dos caps. 3 e 4.

**O que analisa.** A relação entre a qualidade do surrogate (fichas 31–33) e a diferença de desempenho entre critérios de aquisição/seleção que usam esse surrogate: se, quando o RMSE cai abaixo de um nível, os algoritmos com o mesmo tipo de modelo convergem para o mesmo desempenho (o teto), independentemente do critério.

**Dados.** C (sonda + endpoint + trajetórias); ③ + S; ①.

**Objetivo.** Converter a bateria de "mais uma comparação" em "teste da lei do teto" — a justificativa que o painel M14 deu para a hipótese.

**O que busca revelar.** Se a dispersão de desempenho entre algoritmos com surrogate semelhante é explicada pela qualidade do modelo (curva desempenho × RMSE da sonda) e se existe um ponto do orçamento a partir do qual as diferenças entre critérios deixam de importar.

**Como é realizada.** Por problema: dispersão do IGD+ entre algoritmos de mesmo surrogate vs RMSE mediano da sonda no fim; ao longo do orçamento: correlação entre a queda do RMSE e a redução da dispersão entre critérios; pares quase-gêmeos (ficha 52) como caso limpo.

**Técnicas.** Correlação; regressão simples; leitura por pares; gráfico desempenho × qualidade do modelo.

**Implementação.** Junção dos caches (`sonda`, `endpoint`, `trajetorias`) por (alg, problema); não existe.

**Em quantos artigos aparece (dos 38).** **0/38** como análise; a constatação existe como prosa em artigos do corpus (emo1, e1, c122, c241 — citar nominalmente, nunca como numeral; conflito 4 × 5 não arbitrado).

**Estado.** N (e a hipótese não está declarada no texto — pré-requisito editorial).

**Demais detalhes.** Precisa da hipótese escrita antes dos resultados (§3.7 → cap. 4 → cap. 5 → cap. 6, os "4 lugares" do d103.10), senão vira descoberta post hoc (N3/N8). Decisões que pede: a formulação da hipótese (P-1); a estatística da "lei"; se entra dentro da §5.4 ou como camada 3 da §5.3, como o esqueleto previu. Relações: 31, 33, 35, 52.

### 40. O erro de fantasia por terço do orçamento — quem acredita demais no próprio modelo

**Fontes.** [NB] célula [24] (bloco A5: `fantasia_2026-08-17.parquet`, 5.909 linhas: alg, problema, semente, terco, n, rmse; 8 algoritmos × sementes 0–10; `fig59_fantasia`) · [CAP5] §5.8 (`fig:fantasia`) · [DIA] 17/08 ("CLMEA fantasia 21× no 3º terço") · [PL-38] R1#5 (score 9,5: "'O filme': fantasia do surrogate — fronteira acreditada vs real; é o SEU diferencial; nenhum dos 10 do piloto faz isso diretamente; o mais próximo é o 'clumping' do qNEHVI, Fig. 1") · SPEC §15-D49 e §17.1.3 ("erro de fantasia") · [CD] (⑦: "nd_pos_real = erro de fantasia direto" no offline).

**O que analisa.** O erro da predição μ nos pontos que o algoritmo ESCOLHEU avaliar (não nos pontos fixos da sonda): RMSE entre o μ que motivou a escolha e o f real obtido, por terço do orçamento.

**Dados.** ③ regime `busca` (μ do candidato escolhido) casada com ① (f real) por `real_solution_id`/`solution_id` (regra R4: nunca por x float32); C (cache).

**Objetivo.** Medir a ilusão no ponto onde ela custa: a decisão. A sonda mede o modelo onde ninguém pediu; a fantasia mede onde o algoritmo apostou.

**O que busca revelar.** Quem "acredita demais" (erro de fantasia alto, sobretudo no 3º terço — CLMEA) e quem aposta onde o modelo é bom; a relação com a função da incerteza (oportunidade explora onde o modelo erra por desenho; ameaça evita).

**Como é realizada.** Por célula: para cada avaliação de busca, |μ_escolhido − f_real|; RMSE por terço do orçamento; mediana sobre problemas × sementes; barras por algoritmo × terço (log).

**Técnicas.** RMSE por terço; mediana; log.

**Implementação.** Célula-fonte fora do notebook (junção ③ × ① por id); [NB] célula [24] desenha. Cobertura: 8 algoritmos × 11 sementes (mesma limitação de ③ da ficha 31).

**Em quantos artigos aparece (dos 38).** **0/38** diretamente (R1#5); os mais próximos: "avaliação in-sample vs fora-da-amostra" 3/38 (R2#16) e "erro do modelo no ótimo" (UA-DBO, 1/38).

**Estado.** F (8 algoritmos × 11 sementes).

**Demais detalhes.** Um erro de fantasia alto não é necessariamente ruim para quem explora (a aposta é ir onde o modelo erra); a leitura precisa da classe de função. Decisões que pede: RMSE × erro assinado (acreditar que é melhor do que é × pior); normalização por objetivo. Relações: 41, 42, 44.

### 41. A fantasia geracional completa — a fronteira acreditada vs a real, geração a geração

**Fontes.** [PL-38] R1#5 ("plota as duas trajetórias e o gap ao longo da busca, por família"; "gap de fantasia = HV que o surrogate acredita ter − HV real") · SPEC §15-D49/§17.1.3 · [NB] célula [16] ("Nota sobre a ②: o pertencimento população × geração alimenta o 'filme' completo do erro de fantasia por geração (fronteira ACREDITADA vs real) — fica na fila, exige as ③ do bucket para os volumosos") e §8 fila item 6.

**O que analisa.** A cada geração, a fronteira que o algoritmo acredita ter (ND da população pelos μ) contra a fronteira real dos mesmos indivíduos (pelo f da ①): o gap de HV/IGD+ ao longo da busca — "o filme".

**Dados.** ② (pertencimento população × geração); ③ regime `busca` (μ dos membros); ① (f real por solution_id); ⑤ (sigma_dict).

**Objetivo.** A versão completa da ficha 40: não só nos pontos escolhidos, mas em toda a população acreditada.

**O que busca revelar.** Quanto da "fronteira" que guia a seleção é fantasia, e se a fantasia cresce ou diminui com o orçamento.

**Como é realizada.** Por geração: ND da população pelos μ → HV_acreditado; ND dos mesmos pontos pelos f reais → HV_real; gap; curva × geração/fe; mediana sobre sementes.

**Técnicas.** HV/IGD+ sobre conjuntos acreditado e real; gap; curvas.

**Implementação.** Não existe; exige a ② e a ③ completas (as ③ dos algoritmos volumosos moram no bucket — conferir no `_FONTES.csv` do corpus congelado se a camada ③ está local).

**Em quantos artigos aparece (dos 38).** **0/38**.

**Estado.** N (L se as ③ não estiverem no corpus congelado).

**Demais detalhes.** É a análise que a SPEC desenhou o export de 2 camadas para permitir (R1#5: "é o que a SPEC desenhou"). Custo alto. Relações: 40, 42.

### 42. A fantasia offline — |ND acreditado| vs |ND real| depois da reavaliação (⑦)

**Fontes.** [CD] (⑦: `nd_pos_real` = "erro de fantasia direto") · DI-08, DI-13.8/13.9 · [RDI] l.3354–3365 (e103: "n_nd_pos_real mediana 28/100" nas 748 células) · [DOS] item 2-bis (b5m/DTLZ2: "colapso de canto, nd 6/105"; b5r: "convergência PARCIAL"; c311: "frente completa 50/50 ND").

**O que analisa.** No regime offline, a fração do ND final acreditado (pelo modelo, sem nenhuma avaliação real durante a busca) que continua não-dominada depois de reavaliada na função verdadeira — e a métrica de cada um dos dois conjuntos.

**Dados.** ⑦ (`origem_linha`, `nd_pos_real`, f real); ③ (μ final).

**Objetivo.** Medir a ilusão no único regime em que ela é total: sem avaliação real para corrigir, o modelo é a única verdade até o fim.

**O que busca revelar.** Quem entrega um ND "cheio" que evapora na reavaliação (poucos sobrevivem) e quem entrega poucos pontos que sobrevivem — a leitura direta de "acreditar demais".

**Como é realizada.** Por célula: |ND acreditado|, |ND pós-real|, razão; HV/IGD+ dos dois conjuntos; matriz por config × problema; mediana.

**Técnicas.** Contagens; razão; métricas.

**Implementação.** Leitura direta da ⑦ (colunas já existem); não está no notebook.

**Em quantos artigos aparece (dos 38).** Dentro do endpoint dos 11 offline; "in-sample vs fora-da-amostra" 3/38.

**Estado.** N.

**Demais detalhes.** Caveat: nunca consumir ⑦ de célula com motivo de falha (C10-vi); moead_media × RE21 com ⑦ de um único x duplicado (D6) — reportar |X únicos| junto. Relações: 13, 40.

### 43. A utilidade do infill — quanto do orçamento de busca vira fronteira

**Fontes.** [NB] célula [28] (bloco A10: `infill_2026-08-17.parquet`, 12.232 linhas: alg, problema, semente, n_busca, n_uteis, frac_util; 17 algoritmos online × 30 sementes; `fig5C_infill`, boxplot) · [CAP5] §5.11 (`fig:infill`) · [PL-38] R2#22 ("Diagnóstico do valor das amostras selecionadas": EDN-ARMOEA, 1/38 — "nº de soluções contribuintes") e aba Plano ("utilidade do infill: nº de soluções que melhoraram o IGD ao longo dos FEs — SPEC §13, métrica do e7") · [NB] célula [27] ("a métrica do EDN-ARMOEA").

**O que analisa.** A fração das avaliações reais da fase de busca (fe_index ≥ 11D−1) que entram no conjunto não-dominado corrente no momento em que são avaliadas — o aproveitamento do orçamento.

**Dados.** ① (fe_index, fase, f).

**Objetivo.** Uma métrica de eficiência da seleção que não depende de frente verdadeira: cada infill "contribuiu" ou não.

**O que busca revelar.** Se a seleção guiada por incerteza aproveita melhor o orçamento que a seleção do piso — e a assimetria entre algoritmos que propõem muitos pontos medíocres e poucos pontos bons.

**Como é realizada.** Por célula: varredura em ordem de fe_index; a cada avaliação de busca, testa se o novo ponto é não-dominado em relação ao arquivo acumulado; conta úteis/total; boxplot por algoritmo (30 sementes × 25 problemas).

**Técnicas.** Dominância incremental; fração; boxplot.

**Implementação.** Célula-fonte fora do notebook (dominância em float32 é lossy — R4#10, ressalva obrigatória); [NB] célula [28] desenha.

**Em quantos artigos aparece (dos 38).** **1/38** (EDN-ARMOEA, e7).

**Estado.** F.

**Demais detalhes.** Uma variante mais exigente: "contribuiu para o ND FINAL" (sobrevive até o fim) em vez de "entrou no ND corrente". No DDMOP7 as contagens exigem dedup por x_efetivo (C1). Relações: 14, 24, 44.

### 44. Exploração × explotação — onde os infills caem

**Fontes.** [DOS] item 2-bis (e81: "infills DIVERSOS (2,5–5,6 % no bordo — o anti-c149)"; c149: no DDMOP7 "propõe |x| ≥ τ em 98,8 % das coordenadas… empurra para os extremos da caixa — onde a incerteza é alta") · [RDI] parte A52 (tabela de fração de coordenadas na zona morta por config: 51,8 % a 92,2 % nos demais) · leitura da mineração de 06/09 (dist_min ao arquivo).

**O que analisa.** A geometria das escolhas: a distância de cada infill ao ponto já avaliado mais próximo (explotação = perto; exploração = longe), a fração de infills no bordo da caixa, e — no DDMOP7 — a fração de coordenadas propostas dentro da zona morta; ao longo do orçamento e por classe de função.

**Dados.** ① (x de todas as avaliações, fe_index); ③ (σ do ponto escolhido, para ligar a distância à incerteza).

**Objetivo.** Ver a função da incerteza em ação no espaço de decisão: as classes de oportunidade deveriam explorar (longe, σ alto), as de ameaça evitar (perto, σ baixo).

**O que busca revelar.** Se o comportamento observado bate com a classe declarada; assinaturas como a do c149 (extremos da caixa) e do e81 (diversidade).

**Como é realizada.** Por infill: distância normalizada ao arquivo (min sobre os pontos anteriores); fração no bordo (alguma coordenada a menos de ε do limite); curvas por terço; comparação por classe.

**Técnicas.** Distâncias no espaço normalizado; frações; curvas; agregação por classe.

**Implementação.** Não existe; cálculo direto sobre a ① (O(n²) por célula, barato).

**Em quantos artigos aparece (dos 38).** **0/38** como análise nomeada (a discussão exploração–explotação é prosa em vários artigos de BO).

**Estado.** N.

**Demais detalhes.** Complementa a ficha 34 (o σ discrimina?) com a pergunta "e o algoritmo vai lá?". Relações: 24, 34, 40, 43.

### 45. O mecanismo em ação — contar o que o filme (⑥) registra

**Fontes.** [RDI] DI-10 (enriquecimento do `.jsonl`: mecanismo por config) · [DOS] item 2-bis (e7: "152 conv / 48 incerteza, 0 stalls"; b3: "switch preso 44/48 no ramo incerteza"; c217: "o gate δ = 0,8 quase nunca abre"; c154: "241/241 warnings"; c122: "satura POR VITÓRIA") · [DOS] §D9 caveats ("b4 usou surrogate em 25,8 % dos FEs; c217 gateou 4,6 %") · [TP] D5 (c217: "0 disparos em 24.000 gerações, modelo empatado em 1,02 M sondas, em 7 problemas") e D14 (e103 × RE21: "30/30 começam Kriging e assentam RBFN; primeiras 32 trocas do corpus") · [PL-38] R2#9 (métrica "frequência média de acionamento do critério" aparece em 1 artigo, na análise de sensibilidade) · [PL-38] R1#12 ("exceção que valeria: mini-análise dirigida só do(s) parâmetro(s) que definem o USO da incerteza — β do UCB, δ do gate").

**O que analisa.** As contagens das decisões internas em que a incerteza intervém: quantas vezes o ramo "incerteza" foi escolhido (b3, e7), quantas vezes o gate abriu (c217), a fração de FEs em que o surrogate foi usado (b4), quantos warnings/estagnações (c154), a troca de modelo (e103) — por célula, problema e terço do orçamento.

**Dados.** ⑥ (um evento por linha: `<alg>_gen`, `sonda`, `guard`, `footer`); ⑤ (params); ③ (`modelo_flag`).

**Objetivo.** Tornar visível o uso efetivo da incerteza — o "contrafactual natural" (ficha 15): um algoritmo cujo mecanismo de incerteza nunca dispara é, de fato, a sua própria ablação.

**O que busca revelar.** Onde o mecanismo opera (e o resultado pode ser atribuído a ele) e onde não opera (e o resultado é do motor sem incerteza); a condição de contorno de cada algoritmo (c217 em 7 problemas é "amostrador aleatório + SPEA2").

**Como é realizada.** Parser do ⑥ por algoritmo (o vocabulário de eventos é por config — DI-10 e o CONTRATO); contagens por célula; tabela algoritmo × problema com a taxa de acionamento; cruzamento com o Δ da ficha 9 (o mecanismo disparou e ajudou / disparou e atrapalhou / não disparou).

**Técnicas.** Contagem de eventos; taxas; tabela de contingência com o placar.

**Implementação.** Não existe no notebook; a torre fez leituras célula a célula. Exige um parser por config (o header do ⑥ tem 19 chaves — T-2) e as regras de rodapé (célula sem rodapé é ⚪/O-21).

**Em quantos artigos aparece (dos 38).** ≤ 1/38 (a "frequência de acionamento" como métrica de sensibilidade).

**Estado.** N.

**Demais detalhes.** É o substituto factual do contrafactual não executado e a base da ficha 16. Custo: um parser por algoritmo. Decisões que pede: quais mecanismos contar; se substitui, declaradamente, o contrafactual do OE5. Relações: 15, 16, 24.

### 46. A parede do retreino — o tempo de ajuste por geração cresce com D (e com n)

**Fontes.** [NB] célula [26] (bloco A9, painel (b): `TE.fit_total_s / n_ger` × D, 8 algoritmos com camada de timing local: b3, b1, c238, e7, e74, c141, b4, c217; `fig5A_tempo_qualidade`) · [CAP5] §5.9 · [CD] (④: tempo_fit_s por geração, n_acumulado) · [PL-38] R1#9 ("a curva ⭐ do achado de escalabilidade: tempo de treino × nº de pontos acumulados — GP O(n³) vs BNN/treed-GP — precisa do tempo de FIT por retreino" → exportado como ④) · [RF] (DI-13.2: tempo_fit_s aceita NULL nos pisos).

**O que analisa.** O custo de retreinar o surrogate a cada geração, em função da dimensão do problema (o arquivo cresce com 31D−1) e do número de pontos acumulados — a parede O(n³) do GP contra as alternativas.

**Dados.** ④ (tempo_fit_s, n_acumulado por geração); ⑤ (timing agregado; máquina); C (`tempo_2026-08-17.parquet`: n_ger, fit_total_s, busca_total_s, sonda_total_s, fit_ultimo_s, n_acum_max, wall_total_s, aval_real_s).

**Objetivo.** Quantificar o preço da maquinaria de incerteza no eixo em que ele explode — e sustentar a recomendação de protocolo do cap. 6 (d43).

**O que busca revelar.** A ordem de crescimento por tipo de surrogate (GP/Kriging × RBF × NN/ensemble × classificador); o `fit_ultimo_s` (o custo no fim, com o arquivo cheio) como a medida mais dura.

**Como é realizada.** Por célula: fit por geração (mediana) × D; ou fit_ultimo_s × n_acum_max em log-log com a inclinação estimada (expoente empírico); curvas por algoritmo.

**Técnicas.** Mediana por D; regressão log-log (expoente); ressalva de plataforma (§4.9).

**Implementação.** [NB] célula [26] (painel b); o expoente log-log não está feito.

**Em quantos artigos aparece (dos 38).** Custo computacional: **26/38** (R2#2); tempo como métrica 14/38; a curva "tempo de treino × n" é rara (R1#9 a chamou de "achado de escalabilidade").

**Estado.** F (painel); N (expoente).

**Demais detalhes.** A sonda é excluída de `tempo_geracao_s` por contrato; tempos entre stacks (MATLAB × Python) são tendência, não número fino ([NB] célula [25]). Relações: 47, 48, 49.

---

# Grupo F — Custo

### 47. Tempo × qualidade — o custo se paga? (quadrantes)

**Fontes.** [NB] célula [26] (bloco A9, painel (a): tempo de parede mediano por execução × rank médio de IGD+; pisos como quadrados cinza; `fig5A_tempo_qualidade`; tabela `tq`) · [CAP5] §5.9 "O custo se paga? Tempo contra qualidade" (`tab:tempo-rank`, `fig:tempo-qualidade`; prosa: "o quadrante barato-e-bom existe: o MMRAEA entrega o segundo melhor rank do estudo gastando menos de um minuto por execução, e o K-RVEA fica no pelotão da frente com menos de dois; o qNEHVI compra o primeiro lugar…"; legenda: "O JES opera no teto de parede de 12 horas; retrato de 17/08") · [DIA] 17/08 ("quadrante barato-e-bom existe: MMRAEA 0,7 min / rank 4,4") · [PL-38] R1#9 (score 7; "tempos absolutos entre linguagens diferentes NÃO são diretamente comparáveis — tendência, não número fino") e R2#2 (26/38) · [NB] célula [25] ("todos os sintéticos rodaram no mesmo parque (VMs Linux), com a heterogeneidade declarada na §4.9") · [TP] C4/C5 (ruído de máquina; normalizar host).

**O que analisa.** A posição de cada configuração no plano (custo, qualidade): tempo de parede mediano por execução contra o rank médio de IGD+ nos 25 sintéticos.

**Dados.** ⑤ (wall-clock total; máquina) e ④ (decomposição) via C (`tempo_2026-08-17.parquet`: wall_total_s, fit_total_s, busca_total_s, sonda_total_s, aval_real_s, n_ger, n_acum_max, status); ① via C (rank).

**Objetivo.** Expor o trade-off que a banca cutuca — e mostrar que ele tem quadrantes, não uma reta.

**O que busca revelar.** O quadrante barato-e-bom (existe), o caro-e-bom, o caro-e-ruim; e onde os pisos ficam (baratos, medianos).

**Como é realizada.** Mediana do tempo de parede por algoritmo (sobre células ok), eixo x em log; rank médio por algoritmo; um ponto por algoritmo, rotulado; pisos com marcador distinto.

**Técnicas.** Mediana; escala log; dispersão rotulada.

**Implementação.** [NB] célula [26] (painel a); a tabela `tq` (min, rank). O tempo da sonda (`sonda_total_s`) deve ser subtraído do parede quando o algoritmo tem sonda — a sonda não é custo do algoritmo (o `tempo_geracao_s` do ④ já a exclui por contrato; o `wall_total_s` do ⑤ não necessariamente).

**Em quantos artigos aparece (dos 38).** Custo computacional/tempo: **26/38** (R2#2) — o segundo tipo mais frequente; tempo como métrica 14/38.

**Estado.** F.

**Demais detalhes.** Caveats: MATLAB sem teto (maior célula ~4 h) vs Python com teto de 12 h; o JES aparece no teto (o tempo dele é censurado, não medido); campanha em 9 máquinas e 2 stacks (§4.9). Decisões que pede: tempo com ou sem sonda; parede × CPU; incluir reais; como declarar a censura do teto. Relações: 46, 48, 49.

### 48. O custo com o tempo de ajuste do modelo — a decomposição fit / busca / sonda / avaliação

**Fontes.** [CAP1] (prosa comentada: "uma contribuição de medida: os nossos experimentos registram, por execução, o tempo de construção de cada substituto (Capítulos 4 e 5) — a grandeza cuja falta de reporte a Seção 1.1.1 registrou") · [REG] d43 e adendo `registro:382` ("cap. 4 protocolo + cap. 5 análises + §5/cap. 6 recomendação de protocolo"; "nunca generalizar os 29,8 %") · [PC6] TF-2 ("protocolos de custo em SAEA devem contabilizar o tempo de ajuste do modelo; evidência com literal de c31 p. 2068: 'It spends 2700s on average to assemble each surrogate optimization function…'; o próprio cap. 5 já pratica a recomendação") · [CD] (④: tempo_fit_s, tempo_busca_s, tempo_pred_sonda_s, tempo_geracao_s exclui a sonda; DI-13.2: tempo_fit_s NULL nos pisos) · [RDI] DI-44 (heatmap `f5/tempo_heatmap_30seeds.html`: Σ 10.173 h-core — c149 2.811 · c154 1.537 · c122 1.239 · b5m 1.123 · c262 867 · e81 680 · c238 502 · e7 452; campanha projetada 18.291 h-core a 12 h) · [PL-38] R1#9 (a coluna "exportar timing por retreino" — feita).

**O que analisa.** Quanto do tempo de cada execução é ajuste do modelo, quanto é busca no modelo (otimização da aquisição), quanto é avaliação verdadeira, e quanto é instrumentação (sonda, a descontar) — por algoritmo, problema e ao longo do orçamento.

**Dados.** ④ (por geração); ⑤ (agregado); C (`tempo_2026-08-17.parquet` já traz fit_total_s, busca_total_s, sonda_total_s, aval_real_s).

**Objetivo.** Cumprir a "contribuição de medida" do cap. 1 e a matéria-prima da recomendação de protocolo do cap. 6 (d43): mostrar o que os protocolos do campo deixam de contar.

**O que busca revelar.** Que o custo dominante em SA-MOO com orçamento pequeno é o modelo, não a função (aval_real_s é desprezível nos sintéticos); a fração de ajuste por tipo de surrogate; a escala em horas-núcleo de uma bateria honesta.

**Como é realizada.** Por célula: frações fit/busca/aval/sonda do tempo total; barras empilhadas por algoritmo (mediana); a fração de fit ao longo do orçamento (cresce com n); a soma em h-core por algoritmo.

**Técnicas.** Frações; barras empilhadas; mediana; soma.

**Implementação.** Agregação direta sobre o cache de tempo (as colunas existem); o painel de frações não existe no notebook.

**Em quantos artigos aparece (dos 38).** Custo computacional 26/38 (R2#2), mas a decomposição com tempo de ajuste declarado é rara — a evidência do d43 (c31) é externa aos 38; "nº de pontos de treinamento como proxy" e "complexidade assintótica" aparecem no lugar.

**Estado.** F-parcial (os totais estão no cache; a decomposição declarada não está no texto).

**Demais detalhes.** Trava: "nunca generalizar os 29,8 %" (d43); a recomendação de protocolo TERMINA no cap. 6 — o cap. 5 só mede. Decisões que pede: publicar frações ou horas; incluir os h-core da campanha (número de infraestrutura, não de resultado). Relações: 46, 47, 49.

### 49. O ganho descontado do custo — qualidade por hora, e a fronteira custo × qualidade

**Fontes.** Leitura da mineração de 06/09 (derivada da ficha 47) · [PL-38] aba Métricas ("razão de eficiência relativa 'EGO wins'/'no dif'": ParEGO, 1/38; "Efficiency Ratio" na lista do R2#2) · [CAP5] §5.9 (a prosa já fala em "quadrantes").

**O que analisa.** A ficha 47 transformada em número: (a) o conjunto não-dominado dos algoritmos no plano (tempo, IGD+) — quem está na fronteira custo × qualidade; (b) o custo marginal de cada ponto de rank/IGD+ entre vizinhos da fronteira.

**Dados.** C (tempo; endpoint).

**Objetivo.** Dizer, com um número, o que o quadrante diz com uma figura: a que preço se compra o primeiro lugar.

**O que busca revelar.** Se a fronteira custo × qualidade é povoada por classes (assistidos baratos com regressor simples; BO caros) e onde os pisos entram nela.

**Como é realizada.** Dominância no plano (tempo mediano, IGD+ mediano ou rank) → fronteira; por problema e agregada; razão Δqualidade/Δtempo entre vizinhos.

**Técnicas.** Dominância 2D; razões.

**Implementação.** `metrics.nondominated_front` sobre a matriz (tempo, rank) por problema — trivial.

**Em quantos artigos aparece (dos 38).** ≤ 1/38 (razão de eficiência do ParEGO).

**Estado.** N.

**Demais detalhes.** Sujeita às mesmas ressalvas de plataforma da ficha 47. Relações: 47, 48.

### 50. FE redundante no DDMOP7 — nota de custo, não análise

**Fontes.** [TP] C3 ("registrar FE redundante na leitura de custo do DDMOP7: smsemoa 48,1 %, moead 59,2 % — idêntico entre configs por desenho (comparabilidade intacta)") · [CD] §T15.12/13 (dedup opera sobre x proposto).

**O que analisa.** A fração de avaliações verdadeiras do DDMOP7 gastas em pontos cujo x efetivo (após zona morta) já havia sido avaliado — custo "redundante" por desenho da codificação.

**Dados.** ① (x proposto → x efetivo).

**Objetivo.** Declarar, na leitura de custo do DDMOP7, que parte do orçamento é gasto por desenho — sem alterar comparações (é idêntico entre configs).

**O que busca revelar.** Nada comparativo: a fração é a mesma para todas as configurações; serve para que o custo por avaliação "útil" do DDMOP7 não seja lido como ineficiência de algum algoritmo.

**Como é realizada.** Por célula: aplicar `zona_morta` a cada x proposto, contar quantos x efetivos repetem um já avaliado, dividir pelo total de FEs.

**Técnicas.** Dedup por identidade de ponto efetivo; fração.

**Implementação.** A mesma função de dedup da ficha 24; a torre mediu smsemoa 48,1 % e moead 59,2 %.

**Em quantos artigos aparece (dos 38).** 0/38.

**Estado.** R (uma frase; a torre já mediu).

**Demais detalhes.** Relações: 24, 47.

---

# Grupo G — Pares e evolução

### 51. Pares seminal → estado da arte sob o mesmo DoE — o que a evolução da classe comprou

**Fontes.** [NB] célula [28] (bloco A7: `PARES = [(b4, c217, "CSEA → PC-SAEA (EA·dom, classificador)"), (b1, c262, "ParEGO → qNEHVI (BO, escalarização → hipervolume)"), (b3, e7, "K-RVEA → EDN-ARMOEA (vetores GP → indicador NN)")]`; Δ pareado por semente seminal − SOTA; `fig5B_pares`) · [CAP5] §5.10 "O que a evolução comprou: pares seminal–estado da arte" (`fig:pares`) · [DIA] 17/08 ("K-RVEA → EDN-ARMOEA 3×22 — o SOTA perde do seminal sob protocolo neutro") · [PL-38] R1#7 (score 8,5: "atribuição do ganho ao mecanismo — o HERDOU/MUDOU/POR QUÊ/RESULTADO das análises 1-1; a diretriz da Gisele: ligar o survey à parte experimental"; EMMOEA faz via ablações) e aba Plano ("atribuição seminal → SOTA — SPEC §15") · [CAP4] §4.2 (`subsec:canonico-soat`: o critério de seleção canônico/SOTA por classe) · [PC6] §1.2 (os quase-gêmeos "como evidência retroativa").

**O que analisa.** Para os três pares em que o roster tem o canônico e o estado da arte da mesma linhagem, quanto do progresso publicado sobrevive quando os dois rodam sob o mesmo DoE, orçamento e protocolo.

**Dados.** ① via C (endpoint por semente dos dois membros do par).

**Objetivo.** Ligar a genealogia do survey ao experimento: o que o SOTA introduziu vira desempenho, ou não.

**O que busca revelar.** Que a evolução nem sempre compra: no retrato de 17/08, ParEGO → qNEHVI melhora na maioria dos problemas; CSEA → PC-SAEA divide; K-RVEA → EDN-ARMOEA regride — o SOTA perde do seminal sob protocolo neutro.

**Como é realizada.** Por par e problema: Δ = IGD+(seminal) − IGD+(SOTA) pareado por semente; mediana; mapa de calor (verde = SOTA melhor); placar por par; leitura por família de problema.

**Técnicas.** Diferença pareada; mediana; placar; opcionalmente o teste pareado (ficha 5).

**Implementação.** [NB] célula [28]; extensível a testes e aos reais.

**Em quantos artigos aparece (dos 38).** Como "ablação/contribuição de componente" (26/38, R2#3) — a forma mais próxima; o par seminal ↔ SOTA sob protocolo neutro, comparando dois artigos, não é contado como tipo.

**Estado.** F.

**Demais detalhes.** A atribuição do Δ ao mecanismo (o que o SOTA mudou) é prosa que depende das análises 1-1 do cap. 3; os dois membros de cada par não são quase-gêmeos no sentido do d26 (b4/c217 são idênticos nas quatro classes; b1/c262 e b3/e7 diferem em maquinaria). Decisões que pede: publicar como está; acrescentar teste; ler por característica. Relações: 52, 20.

### 52. Os pares quase-gêmeos experimentais — mesma maquinaria, incerteza distinta, ambos no roster

**Fontes.** [REG] d26 e [CHK] P8 ("Contraste quase-gêmeo — prioridade narrativa máxima: onde a classe contém pares de mesma maquinaria e incerteza distinta, a subseção explora ao menos o mais nítido") · `planos/inventario_pares_quase_gemeos.md` (v3; errata P-LAP 06/08, l.795–805: os pares com AMBOS os membros no roster de 15 são exatamente três — **b3 × b5** (K-RVEA × Prob-RVEA, EA-Dec × GP, funções OM × AR, regimes ≠ online × offline), **c154 × e81** (JES × qPOTS, BO-Esp × GP, OL × OV, ambos online) e **c141 × e74** (MMRAEA × CLMEA, EA-Dom × RG, tipo B: OV × OM e DE × DG, ambos online); "nenhum é offline × offline"; o antigo par b5 × c311 deixou de existir com a saída do c311) · [ESQ] l.758 (d103.8: o eco do quadro de equivalências) · [PC6] §1.2 ("os quase-gêmeos como evidência retroativa do poder discriminante das características de incerteza — no cap. 6 é uma frase").

**O que analisa.** Os três pares em que a maquinaria é a mesma e o que muda é a incerteza (função e/ou medição): a diferença de desempenho entre eles é a diferença que a incerteza faz, com a maquinaria controlada — a "lupa da incerteza" (a contribuição da dissertação) em ação experimental.

**Dados.** ① via C (endpoint por semente); ③ + S (as sondas dos dois membros: a qualidade do σ de cada um); ⑦ para o b5.

**Objetivo.** Dar ao cap. 5 o mesmo dispositivo que organiza o cap. 3: o contraste de gêmeos.

**O que busca revelar.** Se OL (ganho de informação: JES) e OV (aquisição exploratória: qPOTS) diferem em desempenho sobre o mesmo GP e o mesmo motor BO-Esp; se OV (MMRAEA) e OM (CLMEA) diferem sobre o mesmo EA-Dom × RG; e, no par b3 × b5, o que muda entre O e A atravessando o regime (≠ regime é conteúdo: "o offline muda o que vence", d24/M16).

**Como é realizada.** Por par: Δ pareado por semente (os dois membros partem do mesmo DoE) por problema; leitura por família/característica; a sonda dos dois lado a lado (RMSE, calibração) para separar "a incerteza é usada melhor" de "o modelo é melhor".

**Técnicas.** Diferença pareada; mediana; placar; sonda comparada; teste pareado opcional.

**Implementação.** Reúso das fichas 9 e 31–33 restrito aos pares; b3 × b5 exige ① (online) contra ⑦ (offline) — comparação declaradamente entre regimes.

**Em quantos artigos aparece (dos 38).** **0/38** como desenho entre artigos; a forma intra-artigo ("só média vs com σ") é a ablação (26/38).

**Estado.** N.

**Demais detalhes.** c154 e e81 têm ③ no bucket (a sonda deles não está no cache de 17/08). O par c141 × e74 é do tipo B (mudam função E medição), logo o contraste não isola uma característica só — declarar. Decisões que pede: os três pares entram? com sonda? Relações: 9, 20, 31–33, 39, 51.

### 53. O eco do quadro de equivalências na abertura da §5.1 — moldura, não análise

**Fontes.** [ESQ] l.758 (d103.8: "pré-explicar, ANTES dos números, que critérios algebricamente próximos podem render desempenhos próximos — com o contraponto e40 §II-B no mesmo fôlego, para que a candura não vire relativismo") · [CHK] adendo 31/07 (a pergunta de banca "se os critérios de aquisição dão resultados parecidos, sua taxonomia não está distinguindo coisas que na prática são iguais?").

**O que analisa.** Nada por si: é um movimento de prosa na abertura do capítulo — avisar que a álgebra das aquisições (EI, EHVI, UCB, Thompson…) tem parentescos que podem aparecer como desempenhos próximos, e que isso é previsto, não descoberta.

**Dados.** Nenhum; é moldura textual que prepara as fichas 39 e 52. O "quadro de equivalências" vem do cap. 3 (as equivalências algébricas entre critérios registradas no survey).

**Objetivo.** Evitar que a semelhança de desempenho entre critérios próximos seja lida pela banca como "a taxonomia não distingue" — a resposta preparada do checklist.

**O que busca revelar.** Nada empírico; enquadra o que as fichas 39 e 52 vão medir.

**Como é realizada.** Um parágrafo no Movimento 2 da §5.1, com o contraponto e40 §II-B no mesmo fôlego.

**Técnicas.** Nenhuma.

**Implementação.** Texto.

**Em quantos artigos aparece (dos 38).** Não se aplica (a constatação existe como prosa em emo1, e1, c122, c241 — citar nominalmente).

**Estado.** R (moldura; vira análise só se casada com 52).

**Demais detalhes.** Relações: 39, 52.

---

# Grupo H — Fronteiras e visualização

### 54. As fronteiras da execução mediana contra a frente verdadeira

**Fontes.** [NB] célula [30] (bloco A8: `CASOS = [ZDT3 "frente desconexa", DTLZ7 "desconexa 3-obj", MMF4 "multimodal no espaço de decisão"]`; `MOSTRAR = [c262, b3, nsga2]`; a semente cujo IGD+ está mais próximo da mediana; `metrics.true_front_raw(p, 2000)`; `nondominated_front` da ①; `fig5D_fronteiras`) · [CAP5] §5.11 (`fig:fronteiras`) · [PL-38] R1#8 (score 7,5: "onipresente mas complementar — use POUCAS figuras representativas (a Gisele: 'não dá pra botar 75 imagens'); para os MMF, o espaço de decisão") e R2#1 (**27/38** — o tipo mais frequente do corpus) · [NB] célula [29] ("convenção do corpus: plotar a run do IGD+ MEDIANO, nunca a melhor").

**O que analisa.** Qualitativamente, a cobertura e a distribuição do conjunto não-dominado obtido, contra a frente verdadeira, em problemas de geometria difícil.

**Dados.** ① (F do ND da execução mediana); M (frente verdadeira: `true_front_raw`).

**Objetivo.** Dar intuição visual ao que os números dizem — poucas figuras, escolhidas por característica.

**O que busca revelar.** As falhas típicas que o IGD+ resume: pontes alucinadas na frente desconexa, coleção de um só segmento, colapso de canto (DTLZ7 3-obj), e nos MMF a diversidade que só o espaço de decisão mostra (ficha 25).

**Como é realizada.** Escolha da execução mediana por algoritmo (convenção do corpus); ND das avaliações reais; sobreposição à frente verdadeira; 2D ou 3D; um painel por caso.

**Técnicas.** Dispersão 2D/3D; ND; execução mediana.

**Implementação.** [NB] célula [30] lê o parquet ① da célula escolhida diretamente do corpus (`CORPUS/{alg}/{problema}/{semente}/*__real.parquet`).

**Em quantos artigos aparece (dos 38).** **27/38** (R2#1).

**Estado.** F (3 casos × 3 algoritmos).

**Demais detalhes.** Regra editorial [ESQ] l.761 (amostra no texto, resto no repositório via link). Decisões que pede: quais casos e quais algoritmos; incluir o espaço de decisão dos MMF; reais (RE21 2D; EST40 3D; DDMOP7 em grade). Relações: 25, 55.

### 55. Superfícies de attainment (worst-case) e coordenadas paralelas

**Fontes.** SPEC §13-D52 (attainment worst-case, Knowles — "de graça dos fronts persistidos"; adotado na aba Plano: "Superfícies de attainment worst-case — 1a, 19 problemas 2-obj") · [NB] §8 fila item 5 ("attainment worst-case (D52) e coordenadas paralelas many-objective — próxima leva") · [PL-38] R2#15 (coordenadas paralelas: **4/38** — EMMOEA, IBE-CSEA, K-RVEA, SABBa) e R2#1/R2#4 (superfície de atingimento: 1/38, "inspeção visual de superfícies de atingimento") · leitura de 06/09 (GHV/coordenadas paralelas entre os "vistos e deixados de fora").

**O que analisa.** (a) Attainment: para cada problema biobjetivo, a região do espaço de objetivos atingida por todas as 30 execuções (worst-case), pela mediana, ou pela melhor — um resumo distribucional das 30 fronteiras que a execução mediana (ficha 54) não dá; (b) coordenadas paralelas: a cobertura por objetivo em M = 3.

**Dados.** ① (ND de cada uma das 30 execuções).

**Objetivo.** Substituir "a run mediana" por "o que as 30 runs garantem" — a leitura de robustez visual.

**O que busca revelar.** Onde a fronteira atingida com certeza (worst-case) difere da mediana — algoritmos com colapsos ocasionais mostram um worst-case muito pior.

**Como é realizada.** Attainment k-ésimo (Fonseca & Fleming; Knowles 2005) sobre os 30 fronts normalizados; sobreposição worst/mediana/melhor; coordenadas paralelas para M = 3 (DTLZ, WFG, MMF16_20, EST40).

**Técnicas.** EAF (empirical attainment function); coordenadas paralelas.

**Implementação.** Não existe; os fronts por célula estão na ① (ou podem ser persistidos); código de EAF é curto.

**Em quantos artigos aparece (dos 38).** Coordenadas paralelas 4/38; superfície de atingimento 1/38.

**Estado.** N.

**Demais detalhes.** A bateria tem no máximo M = 3, o que limita o valor das coordenadas paralelas; o attainment é o mais útil dos dois. Relações: 8, 54.

### 56. Regra editorial das figuras — amostra no texto, o resto no repositório

**Fontes.** [ESQ] l.761 ("Imagens/visualizações: inserir no texto só uma amostra das mais características; o restante no repositório (via link)") · [CAP5] §5.12 "Imagens e Visualizações" (existe como seção; figuras 5.10–5.13 são placeholders no retrato).

**O que analisa.** Nada: é regra de exibição, define quantas figuras de cada ficha entram no corpo do capítulo e onde vive o restante.

**Dados.** As figuras geradas pelo notebook em `dissertacao/figures/` (fonte única, por convenção da leva de 17/08).

**Objetivo.** Manter o capítulo dentro do orçamento (teto 25 · alvo 40 páginas, B-01) sem perder as figuras — a orientadora: "não dá pra botar 75 imagens".

**O que busca revelar.** Nada; garante que toda figura citada seja localizável.

**Como é realizada.** Uma amostra "das mais características" por análise no texto; o restante no repositório, com link/identificador no texto.

**Técnicas.** Nenhuma.

**Implementação.** Convenção de nomes já usada (`fig5X_*.pdf/png`); falta o mecanismo do link.

**Em quantos artigos aparece (dos 38).** Não se aplica (o análogo do corpus é "material suplementar mencionado", 6/38).

**Estado.** R.

**Demais detalhes.** Decisão que pede: o mecanismo do "link" (repositório público? apêndice digital?). Relações: 26, 54, 55.

---

# Grupo I — O contrato honesto: completude, incapacidades, ruído, validade

### 57. A completude do corpus — n efetivo por configuração × problema

**Fontes.** [NB] §1, célula [3] ("Completude do corpus (o placar honesto)": contadores de sementes, distribuição, abortadas) · [CAP5] §5.1 "O que já pousou, e como ler este capítulo" (16.202 células no retrato; "todo número reconferido no congelamento") · [CEN] (`censo_final.csv`, 22/08: 16.811 células; 16.021 ok / 790 failed; motivos: orcamento 4.645, teto_wall 615, checkpoint_em_andamento 158, sem motivo 11.391 (rota MATLAB), gpy_bfgs_linalg 1, erro_Forbidden 1; failed por config: c154 439, c262 158, c122 98, c149 72, e81 22, sobol_batch 1) · `_contagem_seeds_por_algoritmo_problema.xlsx` (abas ≥1/≥4/≥6 arquivos; base_dados 16.814 linhas; finalizaram_orcamento) · [TP] D9 (caveat pronto: "878 nunca-rodadas = 430 main-sint + 195 off-sint + 253 reais; concentradas em sementes inteiras (18/25/26; 13/17/26; 26); + nsga2 sem RE21 s12/s18 e EST40 s10/s13/s28; RE21 = 566 células/19 configs; c311/treed_media/sobol_batch = s42-only" e a frase: "o corpus está congelado; toda tabela declara o n efetivo por config × problema (apêndice X), separa 'nunca-rodada' de 'rodada-e-falhada', nenhuma análise interpola células ausentes, e contrastes pareados usam a interseção de sementes") · [RF] §1–2 (cobertura do grid 95,5 %; notas por config) · [TP] A10 (script de correção do censo: 4 células fe_final == maxfe com status failed → ok; nsga3/DTLZ3/17 → failed; 28 censo-ok sem rodapé; 604 failed+teto legítimas; c154/DTLZ4/7 kill só-⑥; DDMOP7: censo vê 594 de 629 diretórios).

**O que analisa.** Quantas células existem, quantas são válidas, por que as demais não são — por configuração × problema — antes de qualquer resultado.

**Dados.** ⑤ (status, fe_final, n_geracoes), ⑥ (rodapé, motivo), ①; M (censo; contagem xlsx).

**Objetivo.** O "placar honesto": a banca precisa saber o n de cada célula da matriz e a razão de cada lacuna.

**O que busca revelar.** A distinção entre "nunca rodou" (sementes inteiras que não entraram na campanha) e "rodou e falhou" (incapacidade, teto, defeito upstream) — que têm leituras científicas diferentes (ficha 58).

**Como é realizada.** Tabela n efetivo (config × problema), com marcação por motivo; contagem por categoria; apêndice com a lista.

**Técnicas.** Contagem; classificação por motivo ("filtre por motivo, nunca por status" — A10-v).

**Implementação.** A partir de `censo_final.csv` + aba `base_dados` (chegou_ao_fim, pct_orcamento, tempo) + `motivos_parada.json` para as reprovadas com status ok; o notebook §1 fez a recontagem sobre a pasta de 17/08 e deve ser refeito sobre o censo de 22/08 (os totais diferem: 16.202 vs 16.811).

**Em quantos artigos aparece (dos 38).** **0/38** — nenhum artigo reporta completude célula a célula.

**Estado.** F (17/08), a refazer sobre o canônico.

**Demais detalhes.** Decisões que pede: a forma do apêndice de n efetivo; o tratamento das 4 células fe_final == maxfe com status failed e das 28 ok sem rodapé (A10). Relações: 29, 58, 60.

### 58. A tabela de incapacidades — falha julgada pela referência; a incapacidade é resultado

**Fontes.** [RDI] parte A35 (mesa T11, D6: "falhas = decidir pela referência; default limitação") · [RDI] parte A49 D0 (autópsia: c154 "125 teto_wall sancionados + 35 falhas reais (24 escada-RS; 10 ModelFittingError todas WFG1; 1 fantasma s30)"; b1 × DTLZ4 "18/18 determinístico (dacefit.m:102) — aceitar = incapacidade documentada"; c238 × BBOB "bug latente UPSTREAM (Infill_EIM.m:25: min(reshape(...)) colapsa com front singleton; separação 28/28 vs 0/617 por n_front1 == 1; censura NÃO-aleatória = viés)") · [RDI] parte A53 (b1 × DDMOP7: "dacefit underdetermined — objetivo QUANTIZADO produz empates suficientes… incapacidade PARCIAL documentada, achado sobre o algoritmo (limitação do ParEGO diante de objetivos quantizados), material do capítulo 5"; campanha: 29/30 medida — C10-viii) · [TP] D1–D5 (caveats prontos: c238 sintéticos 29 badsubscript em 6 problemas M = 2; b4 × DDMOP7 6/29; c154 × DDMOP7 escada 12/30 e 0 células a orçamento pleno; c154 × EST40 8–9 infills sobre DoE 439; c217 nunca dispara em 7 problemas — 25 % das células) e E1–E12 (exclusões célula a célula: b4 × DDMOP7 n = 23; c154 escada; c238 29 badsubscript + 2 em voo; e74/MMF1/3; c122 13 mortes em checkpoint; b3 4 células; c262 kills; e81 × EST40; b5m 7 abortos de 13/08; b1 × DTLZ4 30 e × DDMOP7 29; c311 MMF16_20/42; sobol_batch/MMF16_20/1) · [CAP4] `tab:limitacoes`.

**O que analisa.** As células que não produziram resultado por limitação do algoritmo (não da infraestrutura), organizadas por algoritmo × problema × causa, com o veredito "incapacidade documentada" — e o que cada incapacidade diz sobre o algoritmo diante da característica do problema.

**Dados.** ⑤/⑥ (motivo, rodapé, erro); ① parcial (quando existe); M (listas E1–E12).

**Objetivo.** Cumprir a decisão D6: uma falha é julgada contra o artigo de referência; por default é limitação do algoritmo, logo é achado, não buraco.

**O que busca revelar.** Incapacidades com conteúdo científico: o Kriging DACE do ParEGO degenera com objetivos quantizados (DDMOP7) e no DTLZ4; o EIM herda um defeito upstream com front singleton (censura não-aleatória concentrada em M = 2); o CSEA cai no DDMOP7 pela mesma degenerescência que faz o classificador brilhar; o JES esgota a escada no DDMOP7; o PC-SAEA nunca dispara em 7 problemas.

**Como é realizada.** Tabela: algoritmo · problema(s) · n perdido · causa (com a linha de código/laudo) · leitura (o que diz sobre o mecanismo) · tratamento (excluída / ⚪ / declarada); frases prontas D1–D5 no corpo ou no apêndice.

**Técnicas.** Classificação; contagem; texto.

**Implementação.** Consolidação das listas E1–E12 e dos laudos D0/A53 com o censo; não existe como tabela.

**Em quantos artigos aparece (dos 38).** **0/38** — artigos não reportam incapacidades das próprias propostas.

**Estado.** N.

**Demais detalhes.** É onde a "censura não-aleatória" do c238 precisa ser declarada como viés (D1); e onde as sementes fantasmas (s30) e quarentenas (e81 × EST40 s22–26) ficam registradas. Decisões que pede: corpo × apêndice; o grau de detalhe técnico (linha de código sim ou não). Relações: 24, 57, 61.

### 59. O piso empírico de ruído — em dois níveis

**Fontes.** [TP] C4 ("O-18 → piso empírico de dois níveis: (i) homogêneo: deriva exatamente 0; (ii) contraste real HV 1,225 % / IGD+ 3,238 %; (iii) exposição total HV 5,012 % / IGD+ 10,876 %; (iv) 6 configs surrogate sensíveis a microarquitetura, EAs puros bit-estáveis; testes pareados não cobrem ruído cross-VM") · [DOS] §D9.1 (o freio: "só 17,7 % (54/305) das comparações excedem o piso de ruído entre máquinas (HV ≤ 1,55 %)") · [RDI] A42.1 (DI-42: "o piso de ruído, RESOLVIDO por desenho") · [TP] C5 (identidade de campanha; normalizar host; "par DDMOP7/0 vm1 × vm5 bit-idêntico") · `f5/final/transversal_ruido.md`.

**O que analisa.** A magnitude da variação da métrica que se deve à máquina/stack (e não ao algoritmo ou à semente): a mesma célula rodada em máquinas diferentes.

**Dados.** ① de células replicadas entre máquinas; ⑤ (host, campanha_id, repo_hash).

**Objetivo.** Dar um limiar abaixo do qual uma diferença entre algoritmos não significa nada — o complemento físico do teste estatístico (que só vê a semente).

**O que busca revelar.** Que os EAs puros são bit-estáveis e seis configurações com surrogate variam com a microarquitetura (BLAS, arm64 × Rosetta) — logo diferenças abaixo de ~1,2 % de HV / ~3,2 % de IGD+ (contraste real) não devem ser lidas.

**Como é realizada.** Pares de células idênticas (config × problema × semente) em hosts distintos; diferença relativa da métrica; percentis por nível de exposição; tabela dos dois níveis.

**Técnicas.** Diferenças relativas; percentis; classificação por sensibilidade.

**Implementação.** A torre computou (transversal_ruido); replicar exige os pares cross-VM identificáveis pelo ⑤ (host) — normalizar `matlab-vmX`.

**Em quantos artigos aparece (dos 38).** **0/38**.

**Estado.** T.

**Demais detalhes.** É um filtro alternativo ou complementar à rope da ficha 5. Decisões que pede: usar como filtro de "conclusividade" (e qual nível) ou só declarar. Relações: 5, 8, 60.

### 60. A sensibilidade do veredito às políticas de cobertura — P1, P2, FE comum

**Fontes.** [TC] (P1 = células a orçamento pleno, 12.761 na main; P2 = P1 + teto de parede, 13.371; ranking sob as duas; C8 FE comum) · [RDI] C8 parcial (decisão do autor: primeiras análises só com P1) · [TP] C8 (FE comum por problema) · [DOS] §D9.1 ("a inferência é do M8/M9 com 30 sementes").

**O que analisa.** Quanto as leituras principais (matrizes, placar, ranking, CD) mudam quando a política de inclusão de células muda.

**Dados.** ① via C; M (censo; motivo; FE comum).

**Objetivo.** Provar que o veredito não depende da política escolhida — ou declarar onde depende.

**O que busca revelar.** Robustez (a torre reportou ranking imune) e as exceções (os algoritmos caros, onde P1 exclui muitas células).

**Como é realizada.** Recomputar as fichas 1, 2, 4, 9 sob P1, P2 e FE comum; Spearman entre rankings; Δ do placar.

**Técnicas.** Recomputação; Spearman; tabela de deltas.

**Implementação.** Filtros sobre o CSV de endpoint (P2 exige métricas das células ⚪ no FE comum — via trajetórias ou prefixo da ①).

**Em quantos artigos aparece (dos 38).** **0/38**.

**Estado.** T.

**Demais detalhes.** Vai junto com a ficha 29 (a política é a decisão; esta ficha é a evidência de que a decisão importa pouco ou muito). Relações: 4, 29, 57.

### 61. "O que a bateria não responde" — os limites declarados

**Fontes.** [CAP4] `tab:limitacoes` (l.480–489: teto de parede em algumas centenas de células concentradas nos algoritmos caros; ausência de teto no ambiente MATLAB; sub-estudos large-batch e sweep offline não concluídos) · [RDI] A53 (ideais de ZDT6 0,2809, MMF4 0,001 e MMF1 0,0005 furados pelo dado real por ≤ 3,6e-4 do range em 533 células — "decisão do autor: manter declarando a precisão, ou recomputar os três ideais na fase de análise") · [DOS] §D9.3 (c311 no tier small fora do envelope do artigo) e §D9 caveats (N efetivo 40 ≠ 45 nos DESDEO; repo_hash vazio em 666/666 da F5) · [REG] d75 (a seção de ameaças/limitações: as 4 rejeições frágeis c43, e15, e84, c195; "local final na dD-01") · [PC6] §5 (§6.3 condicional; §4.9 = ameaças experimentais; risco de duplicação em 3 lugares) · ficha 15 (sem contrafactual online) · ficha 24 (DDMOP7 quantizado) · fichas 63–64 (sweeps em 1 semente).

**O que analisa.** A lista do que a bateria, tal como congelada, não pode responder — e por quê.

**Dados.** Todos (é meta).

**Objetivo.** A sobriedade N8 em forma de tabela: o que a banca não vai poder cobrar porque já está declarado.

**O que busca revelar.** Os limites de escopo (sem ruído; sem contrafactual online; q = 1), de dado (sweeps s42-only; DDMOP7 offline sem ⑦; ③ dos volumosos no bucket), de instrumento (ideais arredondados; MATLAB sem teto; 2 stacks) e de inferência (30 sementes; teste pareado não cobre ruído de máquina).

**Como é realizada.** Tabela limite · causa · efeito nas leituras · onde está declarado (cap. 4 / cap. 5 / cap. 6).

**Técnicas.** Nenhuma estatística; classificação dos limites em escopo / dado / instrumento / inferência.

**Implementação.** Consolidação a partir de `tab:limitacoes` (cap. 4), dos caveats da torre (D1–D15, §D9) e das fichas 15, 24, 29, 63, 64; não existe como tabela única.

**Em quantos artigos aparece (dos 38).** 0/38 como tabela (seções de limitações existem, mas não foram contadas como tipo).

**Estado.** F-parcial (cap. 4 já declara parte).

**Demais detalhes.** Decisão estrutural pendente: onde moram as limitações (dD-01: cap. 4 §4.9, cap. 5, ou cap. 6 §6.3) — sem duplicar. Relações: 15, 24, 29, 57, 63, 64.

### 62. Avisos de régua e clip — notas de normalização

**Fontes.** [RDI] A53/T15.13b (folga de 1e-3 do range no `checa_regua`; furo tolerado vira `metrics.avisos_regua` — problema → n_pontos, pior furo relativo — "consultável por quem publica"; 0 explosões em 9.580 células) · [TP] D12 (EST40: "f3 normalizado excede 1 em todas as células — nadir canto-derivado; pontos clipados pelo ref 1,1 do HV — clip declarado, sem efeito na régua guardada") e C15 (RE21: "56 pontos abaixo do ideal são 2,2e-8–1,4e-7 do range = ruído float32; reportar avisos_regua junto do HV") · D53 (⑥ em float64 × ① em float32).

**O que analisa.** Os pontos que furam a régua (ideal/nadir) por problema e o efeito do clip do HV — uma nota de rodapé por problema afetado.

**Dados.** ① (F); M (`F_MIN_MAX`; `avisos_regua`).

**Objetivo.** Publicar, ao lado de cada HV/IGD+, a folga da régua que o número carrega — como o guard prevê.

**O que busca revelar.** Onde a normalização toca o dado (ideais arredondados; nadir canto-derivado do EST40) e que o efeito nas métricas é desprezível ou declarado (clip no ref 1,1).

**Como é realizada.** Coletar `metrics.avisos_regua` durante o cômputo do endpoint; tabela problema → n_pontos furando, pior furo relativo; nota por problema afetado.

**Técnicas.** Verificação de invariante com tolerância (1e-3 do range); contagem.

**Implementação.** `metrics.checa_regua` / `avisos_regua` já existem no `metrics.py` (T15.13b); falta consumi-los na publicação.

**Em quantos artigos aparece (dos 38).** 0/38.

**Estado.** R (notas; a torre mediu).

**Demais detalhes.** Decisão pendente sobre os três ideais arredondados (ficha 61). Relações: 1, 30, 61.

---

# Grupo J — Experimentos secundários (dado só em uma semente)

### 63. O sweep offline de volume de dados — c311 e treed_media em small/medium/big × LHS/MVNS

**Fontes.** [ESQ] l.748 ("experimentos secundários: variação de volume de dados/avaliações, offline sweep") · [DOS] §D9.2–3 (pela ⑦: "'mais dado → melhor' no sweep cai de 46×4 para 29×21; LHS × MVNS = 27×32"; "os GPs locais do c311 melhoram o endpoint em 7 de 9 células big vs treed_media, a ~100× o custo"; "c311 no tier small opera ABAIXO do regime reivindicado (n = 2.000); mais dado REDUZ a fração do surrogate coberta por GPs — σ-NaN mediano 90,3 % no big") · [CEN] (exp `sweep-*`: 121 células, só semente 42 — sweep-small-lhs 26, sweep-small-mvns 25, sweep-medium-lhs 25, sweep-medium-mvns 25, sweep-big-lhs 10, sweep-big-mvns 10; por config: c311 30 (5 por tier × distribuição), treed_media 10 (só big), e b5m, b5r, e103 e moead_media com 5 células por tier small/medium × distribuição; o c311 tem ainda 25 células fora do sweep, total 55) · [CAP4] `tab:limitacoes` ("sweep offline NÃO concluído — futuro") · [PL-38] R1#10 (score 7) e R2#13 (**7/38**) · o martelo do roster ("já tirei ele dos experimentos. agora são só 15 algoritmos" — c311 fora).

**O que analisa.** Como o tamanho (small/medium/big) e a distribuição (LHS × MVNS) do dataset offline afetam o endpoint (pela ⑦) do TGPR-MO (c311), do piso treed_media (só big) e — nos tiers small/medium — dos quatro offline do roster (b5m, b5r, e103, moead_media).

**Dados.** ⑦ e ① das 121 células do sweep; ⑤ (tamanho/distribuição).

**Objetivo.** A "segunda história" das planilhas (escalabilidade): a dependência de dados dos métodos offline.

**O que busca revelar.** Que "mais dado → melhor" não é monotônico; que o custo do treed-GP local é ~100× por um ganho em 7/9 células big.

**Como é realizada.** Métrica da ⑦ × tier × distribuição; contagem de vitórias; custo.

**Técnicas.** Métricas de endpoint pela ⑦; contagem de vitórias por tier; razão de custo.

**Implementação.** Existe como leitura da torre (F5/T11) sobre as células do sweep; o CSV de endpoint de 17/08 não inclui os diretórios `sweep-*`/`treed_media`; exigiria uma passada própria de `metrics_of_set` sobre as ⑦ dessas células (regra: nunca a ⑦ da célula reprovada `c311/sweep-big-mvns/MMF16_20/42`).

**Em quantos artigos aparece (dos 38).** Varredura de tamanho de amostra offline: 7/38 (R2#13).

**Estado.** L — dado só em s42 (n = 1 por célula), com um algoritmo fora do roster; o cap. 4 já declara o sub-estudo como não concluído.

**Demais detalhes.** Decisão: entra como seção secundária com n = 1 declarado, vai para apêndice, ou cai (e fica na `tab:limitacoes`, como hoje). Relações: 13, 61.

### 64. O sub-estudo de lote (q = 10) — sobol_batch e as células `batch`

**Fontes.** [CEN] (exp = batch: 23 células, só s42 — c149 5, c262 5, e81 5, sobol_batch 8) · [RDI] DI-33 (batch q = 10 antecipado para a rodada-42) e DI-40 (c154 fora do batch) · [PL-38] aba Plano ("5 · Large-batch (Exp 2): performance batch + contraste q = 1 × q = 10 a FEs-iguais — SPEC V-B, recorte fe_index ≤ 31D−1") · [PL-38] R1#13 (não recomendada, 2,5: "seu protocolo é q = 1 sequencial; cite como limitação de comparação, não como análise") e R2#19 (**2/38**: JES, qNEHVI) · [CAP4] `tab:limitacoes` ("sub-estudo large-batch NÃO concluído — futuro").

**O que analisa.** O desempenho a FEs iguais quando q pontos são escolhidos por iteração (qNEHVI/qPOTS em lote) contra q = 1.

**Dados.** ① das células batch (recorte fe_index ≤ 31D−1); ⑤ (q).

**Objetivo.** Caracterizar o trade-off paralelismo × qualidade dos métodos em lote sob orçamento igual.

**O que busca revelar.** Se escolher 10 pontos por iteração custa qualidade a FEs iguais — pergunta dos artigos de BO em lote, não da tese.

**Como é realizada.** Métrica do endpoint no recorte fe_index ≤ 31D−1 das células batch contra as células q = 1 dos mesmos algoritmos; Δ por problema.

**Técnicas.** Métricas de endpoint; recorte por prefixo; diferença.

**Implementação.** Inexistente no notebook; o CSV de endpoint de 17/08 não inclui `exp = batch`.

**Em quantos artigos aparece (dos 38).** Sensibilidade ao lote: 2/38 (R2#19).

**Estado.** L — 23 células, s42; o cap. 4 já declara como não concluído.

**Demais detalhes.** Decisão: cai (e fica como limitação, como hoje) ou apêndice. Relações: 61.

---

# Anexo 1 — Índice por estado

**F (feita na leva de 17/08, no retrato do cap. 5):** 1, 2, 3, 4, 9, 10, 26, 28, 31, 40, 43, 46, 47, 51, 54 — e as parciais 11, 13, 16, 17, 23, 33, 48, 57, 61.
**T (computada pela torre em 22/08, fora do notebook):** 5, 6, 7, 12, 22, 30, 59, 60.
**N (não feita):** 8, 14, 18, 19, 20, 21, 24, 25, 27, 29, 32, 34, 35, 36, 37, 38, 39, 41, 42, 44, 45, 49, 52, 55, 58.
**L (lacuna de dado):** 15, 63, 64.
**R (regra/nota, não é análise):** 50, 53, 56, 62.

# Anexo 2 — Mapa: os 25 tipos do Ranking 2 (38 artigos) → fichas

| R2# | Tipo de análise (nº de artigos de 38) | Fichas correspondentes |
|---|---|---|
| 1 | Visualização da fronteira / conjunto de soluções (27) | 54, 55 (e 25 para o espaço de decisão) |
| 2 | Custo computacional / tempo (26) | 46, 47, 48, 49 |
| 3 | Ablação / contribuição de componente (26) | 11, 12, 15, 51 (forma mais próxima), 52 |
| 4 | Tabela de qualidade final + significância (26) | 1, 3 (e 2 como derivada) |
| 5 | Curvas de convergência (22) | 26, 27, 28 |
| 6 | Estudo de caso / aplicação real (20) | 22, 23, 24 |
| 7 | Análise por característica do problema (19) | 6, 17, 18, 19 (e 20, 21 como leituras próprias) |
| 8 | Escalabilidade em D e/ou M (19) | 7, 46 |
| 9 | Sensibilidade de hiperparâmetro (18) | não recomendada (R1#12); a exceção admitida vira 45 |
| 10 | Acurácia/calibração da incerteza do surrogate (16) | 31, 32, 33 (calibração propriamente dita: 4/38), 34–38 |
| 11 | Análise teórica (13) | — (fora do capítulo) |
| 12 | Outras / mistas (12) | — |
| 13 | Varredura de tamanho de amostra offline (7) | 63 |
| 14 | Material suplementar mencionado (6) | — (regra 56, por analogia) |
| 15 | Coordenadas paralelas (4) | 55 |
| 16 | In-sample vs fora-da-amostra / etapa de decisão (3) | 13, 40, 42 |
| 17 | Ilustração conceitual (3) | — (53, como moldura) |
| 18 | Sensibilidade ao ruído (3) | não recomendada (R1#11) — fora do recorte epistêmico |
| 19 | Sensibilidade ao lote (2) | 64 |
| 20 | Validação de estimador numérico (2) | — (30, por analogia de sanidade) |
| 21 | Comparação vs heurística forte não-BO / piso (1) | 9, 10, 16 |
| 22 | Diagnóstico do valor das amostras selecionadas (1) | 43, 44 |
| 23 | Restrição / preferência (1) | — (fora do recorte) |
| 24 | Hipervolume generalizado (1) | — (55, por analogia) |
| 25 | Teste agregado / ranking Friedman-Bayes-CD (1) | 4, 5, 2 |

Fichas sem tipo correspondente nos 38 (contribuições próprias ou contrato interno): 8, 14, 20, 21, 29, 30, 34–39, 41, 45, 49, 50, 52, 57–62.

# Anexo 3 — As decisões que o catálogo pede (nomeadas, não recomendadas)

1. O destino do OE5 sem o contrafactual σ = 0 (fichas 15, 11, 45).
2. A política de cobertura: P1, P2, FE comum; o destino das 615 células ⚪ (fichas 29, 60, 57).
3. A família de testes e a multiplicidade — convenção do corpus (rank-sum sem correção) × pareado + Holm + rope × bayesiano (fichas 3, 5, 4); o recorte do Friedman (C13).
4. O uso do piso empírico de ruído como filtro (ficha 59) e/ou a rope (ficha 5).
5. A matriz de características canônica (D98) e a tabela de degraus (fichas 17, 18).
6. IGDX/PSP nos MMF: entra ou cai (ficha 25).
7. Sweep offline e batch (s42-only): seção secundária, apêndice ou limitação (fichas 63, 64).
8. Os ideais arredondados de ZDT6/MMF4/MMF1: manter declarando ou recomputar (fichas 61, 62).
9. Onde moram as limitações — cap. 4 §4.9, cap. 5 ou cap. 6 §6.3 (dD-01; ficha 61).
10. A hipótese da lei do teto: formulação (P-1) e lugar antes dos resultados (ficha 39).
11. A cobertura da sonda: 8 algoritmos (cache) ou 13 (exige as ③ do bucket) (fichas 31–41, 52).
12. A regeneração do endpoint offline com a ⑦ do e103 (ficha 13) — execução, quando chegar a hora.
13. Mediana × média(dp) nas tabelas; cor por linha × global; corpo × apêndice (fichas 1, 57, 58).
14. Quais das seis perguntas do cap. 4 viram seção (ficha 19) e como a taxonomia entra como variável (fichas 20, 21).

# Anexo 4 — O que muda com as próximas minerações

A mineração dos 15 do roster (lente: análises que cada artigo faz sobre o próprio mecanismo; afirmações característica × desempenho; o que é reproduzível com as sete camadas) e dos 15–20 dirigidos por lacuna (calibração; resultados negativos; lei do teto; degradação do σ fora do regime; custo com ajuste; conjunto solução) entra aqui como fichas 65+ e como adendos datados às fichas existentes (sobretudo 31–39, 45, 48). Dos 23 IDs propostos em 06/09, 10 já estão entre os 38 (c105, c107, b2, c241, c1, c59, c81, b15, e86, c82) e 13 não (e64, emo1, e1, c250, c267, e16, c131, e40, c31, e3, c118, e8, e18).

---

## Histórico (aditivo)

- **06/09/2026 — v1.** Criação com 64 fichas, a partir da mineração 1–8 (documentos internos: dissertação, SPEC, ua-dd-saea, corpus congelado, torre de validação de 22/08, notebook) e das três planilhas do processo seletivo (piloto 10; 38 artigos; 38 × SPEC v3.3). Nenhuma decisão tomada.
