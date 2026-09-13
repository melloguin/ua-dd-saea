# Catálogo de análises candidatas — Capítulo 5 (Resultados Experimentais e Análise)

**Versão 1 · 06/09/2026 · 64 candidatas** · Documento-chave do processo de decisão da lista definitiva de análises do cap. 5.
Autor do processo: Guilherme de Mello Nunes (PPGCC/UFMG; orientadora Gisele Lobo Pappa). Redação desta versão: agente de sessão (Cowork), a partir da mineração de 06/09/2026 e das três planilhas do processo seletivo (piloto de 10 artigos; 38 artigos; 38 artigos × SPEC v3.3).

**Versão 2 · 06/09/2026 (noite) · 81 candidatas** · Mineração definitiva: **72 artigos** (38 iniciais + 7 do roster ainda não minerados + 27 complementares), lidos integralmente por 72 agentes de extração com cartão único (`mineracao/CARTAO.md`), **698 análises** extraídas com literal e localizador, das quais **197 não cabiam nas 64 fichas** e foram consolidadas em **17 fichas novas (65–81)** e em adendos às existentes. Cada ficha recebeu: a lista das referências no corpus (artigo a artigo, com localizador), a contagem "de 72", complementos/correções, e um **score 0–10 com justificativa** (recomendação do agente; regra 5 continua valendo). **Diretriz (1) de 06/09/2026: não haverá novos experimentos** — as fichas 15 (contrafactual σ = 0), 63 (sweep offline) e 64 (lote q = 10) estão descartadas e permanecem como registro. Tudo é aditivo (regra 2): o texto da v1 não foi alterado.

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

**Adendo 06/09/2026 (v2) às regras.** (4′) As contagens passam a ser **"de 72"** (mineração definitiva); as contagens "de 38" da v1 permanecem como estão nas fichas, como histórico. (7) **Score.** Cada ficha traz um score 0–10 e uma justificativa (§0.6); é a recomendação do agente, não decisão. (8) **Diretriz (1).** Nenhuma análise que exija executar algoritmos (variantes, sementes novas, ruído, lote) entra; as fichas afetadas ficam marcadas DESCARTADA e são citadas em 61. (9) **Sigla nova:** [MIN] = mineração definitiva de 06/09/2026 (`mineracao/json/{id}.json`, um por artigo; campos `analises[]`, `setup`, `calibracao_do_sigma`, `custo`, `resultados_negativos`, `equivalencia_criterios`, `caracteristica_x_desempenho`, `roster_bloco`).


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


### 0.6 Critérios do score (v2, 06/09/2026)

O score de 0 a 10 é uma **recomendação de entrada** no capítulo 5 (como análise, seção, figura, apêndice ou nota), atribuída pelo agente a cada uma das 81 fichas e justificada em texto. Critérios, na ordem em que foram aplicados: **G** — gate da diretriz (1): se a análise exige executar algoritmos (variante, semente nova, ruído injetado, lote), o score é 0–2 e a ficha é registro/limitação; **P** — quanto responde à pergunta-guia (uso explícito da incerteza; as seis perguntas do cap. 4; a lei do teto; a contribuição de medida); **D** — dados prontos e custo (feita/torre = pronto; N com dado nas camadas = barato; exige ③ dos 13 ou métrica nova = médio; lacuna = zero); **C** — convenção do corpus (nº de artigos, de 72, em que aparece; ausência não penaliza leituras próprias da tese, mas presença forte obriga a declarar quando não se faz); **V** — vínculos com promessas de outros capítulos (cap. 1 OE e "contribuição de medida"; cap. 4 l.102/117/364/450; cap. 6 ecos) e com as decisões vinculantes de 22/08 (§D9). Leitura das faixas: 9–10 núcleo; 7–8 entra (seção, figura ou apêndice); 5–6 entra se houver espaço (parágrafo/nota/apêndice); 3–4 provavelmente fora, citar como limitação; 0–2 descartada ou não aplicável.

### 0.7 A mineração definitiva (06/09/2026) em números

72 artigos (Anexo 7) · 698 análises com literal + localizador · 197 novas → 166 nas 17 fichas novas (65–81) e 37 absorvidas por fichas existentes, 6 em ambas (Anexo 9) · 60 análises "só mencionadas" (conteúdo em material suplementar ausente do corpus) · 19/72 medem alguma qualidade da incerteza (Anexo 8.1) · 60/72 reportam custo (8.2) · 268 passagens de resultados negativos/ressalvas (8.3) · 71 de equivalência de critérios/modelo como limitante (8.4) · 283 afirmações característica × desempenho (8.5) · 15 blocos-roster com o mecanismo próprio e os parâmetros do uso da incerteza (8.6). Rankings: por score (Anexo 5) e por nº de referências (Anexo 6).

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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 53 artigos / 139 análises** — dos 38 iniciais: 28 · dos 7 do roster minerados agora: 5 · dos 27 complementares: 20 · artigos do roster (15): 11.

- **b1** (ParEGO, 2006; roster): Sec. VIII, Table VI — Tabela algoritmo x problema do S-measure (indicador de hipervolume) após 100 avaliações de ParEGO e 100 de NSGA-II, nas 9 funções MOO, com média e… · Sec. VIII, Table VII — Mesma tabela algoritmo x problema do S-measure, agora após o orçamento total (250 avaliações ParEGO / 260 NSGA-II), com média, desvio-padrão e teste… · Sec. VIII, Table VIII — Tabela algoritmo x problema do indicador epsilon binário aditivo (ambas as direções, I_ParEGO,NSGA-II e I_NSGA-II,ParEGO) após 100 avaliações de cada… · Sec. VIII, Table IX; p. 62–63 — Mesma tabela do indicador epsilon binário aditivo, agora no orçamento total (250/260 avaliações), mediana (IQR) e Mann–Whitney por função.
- **b13** (AdaMoR-DDMOEA, 2025): Sec. 5.2, Table 4 (colunas DNN-DDMOEA e XGBOOST-DDMOEA) — Tabela de IGD (média ± dp, teste de Wilcoxon rank-sum, símbolos +/≈/−, melhor em negrito) comparando AdaMoR-DDMOEA (seleção adaptativa DNN/XGBoost)… · Sec. 5.2, Table 4 (coluna AdaMoR-DDMOEA (WO/MU)) — Mesma Tabela 4, coluna AdaMoR-DDMOEA (WO/MU): variante do algoritmo SEM a fase de atualização do surrogate por indivíduos confiáveis (Algoritmo 3… · Sec. 5.4, Table 5 — Tabela final de IGD (média ± dp, Wilcoxon rank-sum, símbolos +/≈/− relativos ao AdaMoR-DDMOEA, melhor em negrito) comparando AdaMoR-DDMOEA contra 4…
- **b14** (SA²-MOEA, 2024): Sec. 4.6.1, Table 5 — Comparação final de IGD entre SA²-MOEA e 6 SA-MOEAs da literatura (ADSAPSO, HeEMOEA, MOEA/D-EGO, KRVEA, KTA2, PCSAEA) nos 7 problemas DTLZ1-DTLZ7,… · Sec. 4.6.2, Table 6 — Mesma comparação da análise anterior, agora nos 9 problemas WFG1-WFG9, cada um com 4 combinações (M,D) - 36 configurações no total - mesma convenção…
- **b15** (U-RankMOEA, 2026): Sec. 4.2, Table 1 — Tabela algoritmo x problema do IGD final apos 300 avaliacoes nos problemas DTLZ1-7 biobjetivo, D em {30,50,100,200}, comparando U-RankMOEA contra 10… · Sec. 4.2, Table 2 — Mesma tabela algoritmo x problema do IGD final, agora nos problemas ZDT1, ZDT2, ZDT3, ZDT4 e ZDT6 biobjetivo, D em {30,50,100,200}, mesmos 10… · Sec. 4.3, Table 3 — Tabela algoritmo x problema do IGD final nos problemas DTLZ1-7 triobjetivo (M=3), D em {30,50,100,200}, mesmos 10 baselines, mesmo orcamento de 300… · Apendice L.2, Table 11 — Extensao de escala: tabela algoritmo x problema do IGD final nos 7 problemas DTLZ, agora com D=500 e M=5 (5 objetivos), orcamento de 300 avaliacoes,… · Apendice M, Table 13 — Comparacao adicional contra 3 metodos MOBO recentes do estado da arte (MORBO, EGBO, CDM-PSL), em DTLZ2-100D, ZDT3-100D e DTLZ2-200D, reportando IGD e…
- **b2** (MOEA/D-EGO, 2010): Sec. VII-D-1 (Comparison); Table I; Table II — Tabelas I e II comparam MOEA/D-EGO com ParEGO (10 instâncias) e com SMS-EGO (KNO1, VLMOP2) sob o mesmo número de avaliações reais (200 ou 300),…
- **b3** (K-RVEA, 2018; roster): Sec. IV-A; Sec. IV-B; Table I — Tabela algoritmo × problema (DTLZ1-DTLZ7) × k (3,4,6,8,10 objetivos, n=10 fixo) do IGD (min/média/máximo) de K-RVEA contra RVEA (piso sem surrogate,… · Sec. IV-B; Table II — Mesma estrutura de tabela (IGD min/média/máximo, Wilcoxon), agora só para k=3 e k=4, num orçamento MENOR e determinado externamente (120 e 115… · Sec. IV-B; Table III — Tabela IGD (min/média/máximo) de K-RVEA contra MOEA/D-EGO apenas, para k=3 (única contagem de objetivos em que a implementação de MOEA/D-EGO dos… · Sec. IV-B, parágrafo antes da Tabela I — O artigo também computa hypervolume (métrica secundária) para a MESMA matriz algoritmo×problema×k da Tabela I (DTLZ, K-RVEA/RVEA/ParEGO), usando como… · Sec. IV-B, último parágrafo antes da discussão de custo (p. 10) — O artigo repete o mesmo desenho experimental da Tabela I (K-RVEA vs RVEA vs ParEGO/MOEA-D-EGO/SMS-EGO conforme aplicável) na suíte WFG (objetivos com…
- **b4** (CSEA, 2019; roster): Sec. IV-C, Table III — Tabela final de comparação entre CSEA e cinco algoritmos (NSGA-III — único piso sem surrogate — ParEGO, CPS-MOEA, K-RVEA, MOEA/D-EGO) em 35…
- **b5** (Prob-RVEA / Prob-MOEA/D (+ Hyb-RVEA / Hyb-MOEA/D), 2022; roster): Sec. IV-A, Table I — Tabela com a mediana (e o desvio-padrão entre as 31 execuções) do HV e do RMSE — ambos calculados reavaliando as soluções aproximadas retornadas na… · Sec. IV-A, Fig. 8 — Mapas de calor (heatmap) do HV e do RMSE (ambos na função verdadeira) para TODAS as instâncias DBMOPP testadas (não só as 'poucas' da Tabela I), com…
- **b7** (DR (Dual-Ranking), 2026): Sec. 4.4 (Comparison Experiments with Baseline Methods), Table 2; Sec. 4.1 (Performance… — Tabela final de comparação com os 5 baselines nos 8 problemas não-restringidos, dataset limitado (11D-1): MSE, IGD+ e HV por algoritmo x problema,… · Material Suplementar, Sec. 1.4 (Comparative Analysis against Baselines), Table 9 — A mesma tabela final de comparação com baselines (MSE, IGD+, HV por algoritmo x problema, 8 problemas não-restringidos), repetida com os surrogates…
- **b8** (KTA2, 2021): Sec. IV-C, Table I — O artigo substitui o modelo substituto de KTA2 (o modelo insensível a pontos influentes) pelo Kriging original, criando a variante KTA2(O), e compara… · Sec. IV-E-1, Table III — Comparação principal do artigo: KTA2 contra 5 SAEAs da literatura (HSMEA, CSEA, KRVEA, MOEA/D-EGO, ParEGO) em 35 instâncias DTLZ1-DTLZ7 (M em… · Sec. IV-E-2, Table IV — Mesma comparação de 6 algoritmos (KTA2 vs HSMEA, CSEA, KRVEA, MOEA/D-EGO, ParEGO), agora em 45 instâncias WFG1-WFG9 (M em {3,4,6,8,10}, D em… · Sec. IV-E (abertura), Table S-I (material suplementar - não incluído neste documento) — O artigo reporta, apenas no material suplementar (Table S-I), os resultados sob a métrica PD (pure diversity) para os 6 algoritmos comparados - a…
- **c1** (BS-MOBO, 2018): Sec. IV-A, Table I — Tabela I: matriz média[desvio-padrão](rank) do IGD para os 27 problemas de 8 dimensões, obtida por 8 configurações (ParEGO, HypI, SMS-EGO… · Sec. IV-B, Table II — Tabela II: mesma estrutura da Tabela I, agora para os 27 problemas em D=50, orçamento NFE=1000, com 7 configurações (2 pisos sem surrogate: MOEA/D,… · Sec. IV-A (texto corrido, antes da Table I); repetido em Sec. IV-B para a Table II — O artigo declara ter calculado também a métrica de diferença de hipervolume (I-_H) para todas as comparações de pequena e grande escala (o mesmo…
- **c10** (SP-RV-MOEANet, 2021): Table I; Sec. Experiments on synthetic networks — Tabela com a média ± desvio-padrão do HV do conjunto não-dominado final para 5 algoritmos (MOEA-RSFMMA, MOEA0, P-MOEANet, P-RV-MOEANet,… · Table II; Sec. Experiments on synthetic networks — Tabela comparando MOEA-RSFMMA e SP-RV-MOEANet em HV médio e tempo de execução para redes SF de 500 nós (médias sobre 5 realizações) e 1000 nós… · Table III; Fig. 5; Sec. Experiments on real-world networks — Tabela e figura com o desempenho (HV médio ± dp, teste de Wilcoxon vs. SP-RV-MOEANet, e tempo de execução) dos 5 algoritmos em duas redes reais — a…
- **c100** (qEHVI, 2020): Apêndice F.1 (ausente deste corpus); citado na Sec. 5 — [nova] Benchmarks sintéticos adicionais (conteúdo não descrito)
- **c105** (SMS-EGO, 2008): Sec. 4 (Experiments), Table 1, p. 790 — Tabela unica (Tabela 1) reportando, para cada uma das 5 funcoes de teste (OKA2, R-ZDT1, R-ZDT4relax, R-DTLZ2 m=3, R-DTLZ2 m=5) e cada um dos 3… · Fig. 3, p. 791 — Figura 3 apresenta boxplots (quartis, mediana, whiskers, entalhes/notches) da distancia media (calculada analiticamente) entre a frente de Pareto…
- **c106** (EMMI (EMmI), 2016): Sec. 6.1 (MOP2 Function), Table 1, p. 16 — Compara seis configurações (3 criterios de melhoria esperada -- EMMI, CWPI, PI -- cada um com GP independente ou GP de dependencia nao-separavel) no… · Sec. 6.2 (DTLZ2 Function), Table 2, p. 18-19 — Repete o desenho da Secao 6.1 no problema DTLZ2 (d=4, m=4, frente concava), com DoE inicial de 20 pontos e 20 pontos sequenciais adicionais (n=40 no… · Sec. 7 (Conclusions and Discussion), p. 19 — Nas conclusoes, o artigo cita exemplos adicionais realizados pelos autores e reportados apenas no Material Suplementar/Online Resource (nao incluido… · Sec. 7 (Conclusions and Discussion), p. 20 — Nas conclusoes, menciona brevemente um criterio alternativo baseado em melhoria de hipervolume esperado (EIH, Expected Hypervolume Improvement,…
- **c122** (θ-DEA-DP, 2022; roster): Sec. IV-B, Table IV — Tabela de comparação final entre θ-DEA-DP e cinco algoritmos (θ-DEA — piso interno sem preselecão via surrogate, mesma engine evolutiva — ParEGO,… · Sec. IV-C, Table V — Mesma estrutura da Tabela IV, agora nos 6 problemas escalados para 5 objetivos (DTLZ1/2/4/7, WFG6/7, n=10 variáveis) — primeira leitura de desempenho… · Sec. IV-C, Table VI — Mesma estrutura, nos mesmos 6 problemas escalados para 8 objetivos (n=10) — segunda leitura em regime many-objective, no limite superior testado pelo… · Sec. IV-A1 — O artigo MENCIONA, mas não mostra neste texto, experimentos adicionais em outros quatro problemas WFG (WFG4, WFG5, WFG8, WFG9), remetendo os… · Sec. IV-A2 — O artigo MENCIONA, mas não mostra neste texto, experimentos em quatro problemas reais de engenharia (projeto de vaso de pressão, treliça de duas…
- **c123** (EPBII / EIPBII, 2017): Sec. VI-A, Table I, Table II — Tabelas I e II reportam o valor médio (sobre 10 execuções) de IH e IGD ao final do orçamento de amostragem, para os seis critérios de infill (EST,… · Appendix A (Table, IH), Appendix B (Table, IGD) — Apêndices A e B reproduzem as Tabelas I e II acrescentando desvio padrão, melhor e pior valor entre as 10 execuções, célula a célula, para o mesmo… · Sec. VI-B, Table III, Table IV — Tabelas III e IV reportam o valor médio de IH e IGD ao final do orçamento para os seis critérios, nas três variantes de maximização propostas pelos… · Sec. VI-B-3 (texto que remete às tabelas); Appendix C, Appendix D — Apêndices C e D reproduzem as Tabelas III e IV acrescentando desvio padrão, melhor e pior valor entre as 10 execuções, para cada critério × variante…
- **c141** (MMRAEA, 2025; roster): Sec. Main comparison, Table 4 — Tabela de comparação final entre MMRAEA e quatro SAEAs do estado da arte (CPS-MOEA, MOEA/D-RBF, EDN-ARMOEA, MCEA/D) em 48 instâncias (DTLZ1-7 3-obj +… · Sec. Main comparison, Table 5 — Mesma estrutura da Table 4, agora nos 36 instâncias do WFG1-9 (3-obj) × d=20,40,60,100 — segunda suíte da comparação principal. · Sec. Results and discussions (BWBUG), Table 8 — Tabela final de IGD e HV para os 5 algoritmos no caso real BWBUG (43D, 2 objetivos: peso W e tensão equivalente máxima σmax), com referência de IGD =…
- **c217** (PC-SAEA, 2023; roster): Sec. 4.3, Table 1 — Tabela final de IGD média±dp para PC-SAEA e os 7 baselines em DTLZ1–DTLZ7 (m=2,3; 14 instâncias), com teste de Wilcoxon rank-sum (α=0,05) e símbolos… · Sec. 4.3, Table 2 — Tabela final de IGD média±dp para PC-SAEA e os 7 baselines em WFG1–WFG9 (m=2,3; 18 instâncias), mesmo protocolo de Wilcoxon e símbolos da Tabela 1. · Sec. 4.3, Table 3 — Tabela final de IGD média±dp para PC-SAEA e os 7 baselines em MaF1–MaF5 (m=2,3; 10 instâncias), mesmo protocolo de Wilcoxon e símbolos das Tabelas 1… · Sec. 4.3, Table 4 — Tabela final de HV média±dp (não IGD, pois a frente verdadeira é desconhecida) para PC-SAEA e os 7 baselines nos 3 problemas reais CSI (m=13,d=7),…
- **c238** (EIM, 2017; roster): Sec. VI-A, Table II, Figs. 9-11 — Tabela com mediana, média e desvio-padrão do hypervolume e do IGD, sobre 10 execuções independentes, para os 6 critérios (EIe, EIMe, EIm, EIMm, EIh,… · Sec. VI-B, Table III, Fig. 12 — Mesma estrutura da A1 (mediana/média/s.t.d. de HV e IGD sobre 10 execuções, teste t pareado + Wilcoxon pareado, α=0.05), aplicada ao DTLZ2 com… · Sec. VI-C, Table IV, Fig. 13 — Mesma estrutura da A1/A2 (mediana/média/s.t.d. de HV e IGD sobre 10 execuções, teste t pareado + Wilcoxon pareado, α=0.05), aplicada ao DTLZ5 com… · Sec. VI-D, Table V, Fig. 14 — Mesma estrutura da A1-A3 aplicada ao DTLZ7 com m∈{3,4,6} objetivos (n=6, orçamento 200) — problema com frente desconexa em múltiplas peças (2^(m-1)…
- **c24** (DTK-MODE, 2015): Sec. IV-B, Table III — No problema real TEAM 22 (SMES, D=8, M=2), a Tabela III compara, ao longo de configurações do DTK com números crescentes de pontos de amostragem…
- **c241** (EMMOEA, 2023): Sec. III-D (corpo principal remete a 'Table I of the Supplementary material') — O artigo MENCIONA (sem detalhar no corpo principal) uma comparação adicional com o algoritmo SMS-EGO [35] em problemas DTLZ1-7 de 3 objetivos,… · Sec. III-E, Table IV — Tabela de IGD (média±dp) do EMMOEA contra 5 algoritmos surrogate-assisted estado-da-arte (CSEA, K-RVEA, HSMEA, MOEA/D-EGO, EIM) em DTLZ1-DTLZ7 com 3,… · Sec. III-E, Table V — Mesma estrutura da análise anterior (IGD média±dp, Wilcoxon vs. EMMOEA, 20 execuções), aplicada a MaF1-MaF6 e MaF13 com 3, 5 e 10 objetivos (21… · Sec. III-E, Table VI — Mesma estrutura das duas análises anteriores (IGD média±dp, Wilcoxon vs. EMMOEA, 20 execuções), aplicada a WFG1-WFG9 com 3, 5 e 10 objetivos (27… · Sec. III-F, Table VIII — Tabela de HV (média±dp) e melhoria percentual (PI) do EMMOEA contra os mesmos 5 baselines em dois problemas reais de engenharia: projeto de cabine de…
- **c250** (K-MOGA, 2008): Sec. 4.1.1, Table 1 (p. 031401-6) — Para o exemplo ZDT2, o artigo calcula duas metricas de qualidade da fronteira propostas na literatura (Wu e Azarm 2001): a diferenca de hiperarea…
- **c261** (DirHV-EGO, 2024): Sec. V-B/V-C, p.8-9, Table III — Com q=1 (busca sequencial, sem seleção de lote), compara quatro critérios de EI multiobjetivo — EHVI, ADirHV-EI (média ponderada do DirHV-EI), ETI e… · Sec. V-C, p.9-10, Table IV — Compara os quatro algoritmos paralelos completos (KB&EHVI-EGO, PEIM-EGO, MOEA/D-EGO, DirHV-EGO — cada um com sua própria estratégia de seleção de q… · Sec. V-E, p.11, Table V — Testa DirHV-EGO contra os mesmos três concorrentes paralelos em cinco problemas reais de engenharia (RE1-RE5: hatch cover, treliça de 4 barras,… · Supplementary Sec. III-C, p.8-9, Table III (Supplementary) — Testa DirHV-EGO (N=295 para m=4, N=462 para m=6 direções via incremental lattice design, q=5) contra quatro algoritmos de otimização many-objective…
- **c267** (SAMOEA-TL2M, 2025): Sec. IV-C, Table I — Tabela final de desempenho (Tabela I) com o IGD médio(desvio-padrão) obtido pelos 5 baselines e pelo SAMOEA-TL2M nos 7 problemas tri-objetivo… · Sec. IV-C, Table II — Mesmo desenho da Tabela I, aplicado aos 9 problemas tri-objetivo WFG1–WFG9 em D=30, 50, 70, 100 (36 células): IGD médio(desvio-padrão), símbolo de… · Sec. IV-C, Table III — Mesmo desenho das Tabelas I–II, aplicado aos 7 problemas tri-objetivo MaF1–MaF7 em D=30, 50, 70, 100 (28 células). Diferente das duas tabelas… · Sec. IV-C, Table IV — Extensão de generalização: para verificar se a vantagem do SAMOEA-TL2M sobre os dois concorrentes mais fortes (SPGP-SAEA e TP-SAEA, os que mais… · Sec. IV-D-1, Table V — Ablação da estratégia de dois níveis (Tabela V): SAMOEA-TL2M-v1 (só o primeiro nível — convergência/diversidade via SDE, SEM gestão de incerteza/IDW)… · Sec. IV-D-2, Table VI — Ablação do indicador ARI (Tabela VI): SAMOEA-TL2M-R substitui o gatilho informado (ARI ≥ α decide entre nível 1 e nível 2) por uma escolha ALEATÓRIA… · Sec. IV-E, Table VII — Aplicação a um caso real (Tabela VII): os mesmos 5 baselines e o SAMOEA-TL2M são comparados em 6 problemas TREE (estimação de erro de razão em…
- **c29** (MO P-algorithm, 2014): Sec. 7, Table 1, p. 89-90 — Tabela (Table 1) com médias e desvios-padrão, sobre 1000 execuções independentes, de quatro métricas (NP, NN, MD, DP) do multi-objective P-algorithm… · Sec. 7, Table 2, Eq. 14, p. 90-92 — Tabela (Table 2) com médias e desvios-padrão de três métricas (NN, GD, EI) do multi-objective P-algorithm e do Monte Carlo, para os problemas de duas…
- **c48** (IBE-CSEA, 2021): Sec. 4.1/4.5/4.6, Table 3 (IGD), Table 4 (HV) — Tabela principal de comparação: IGD (Table 3) e HV (Table 4) do IBE-CSEA contra NSGA-III (piso) e 5 SAEAs (CPS-MOEA, MOEA/D-EGO, K-RVEA, KTA2, CSEA)… · Sec. 4.7, Table 5 — Estudo de caso real: problema de otimização de crashworthiness veicular, 9 objetivos (ex.: carga abdominal, deflexão de costela, força púbica), D=11…
- **c59** (UA-DBO, 2026): Sec. 4.2, Table 3, p. 15–16 — Tabela final (Tabela 3) comparando os 3 frameworks (CFD-based, DBO, UA-DBO) nos 3 casos de divergência de arrasto (A1, A2, A3): para DBO/UA-DBO,… · Appendix C.4.2, Table 6, p. 31–32 — Tabela final (Tabela 6) com o desempenho CFD-verificado (C_L,buffet e (L/D)_cruzeiro) de uma 'amostra típica' selecionada da frente de Pareto de DBO…
- **c66** (PAL-SAPSO, 2019): Sec. IV-A, Table I — Tabela final com a média (desvio-padrão) do IGD sobre 20 execuções independentes, para PAL-SAPSO e os 3 MOPSOs sem surrogate (MOPSO, dMOPSO, SMPSO),… · Sec. IV-B-1), Table II — Tabela com MSE1, MSE2 (erro quadrático médio de cada uma das 2 saídas) e MSE total (soma), média (desvio-padrão) sobre 10 execuções independentes,…
- **c71** (SAEA/ME, 2020): Sec. 4.1, Table 1 — Tabela única (Table 1) compara SAEA/ME contra três SAEAs do estado da arte (ParEGO, MOEA/D-EGO, K-RVEA) nos 12 problemas (ZDT1,2,3,4,6; DTLZ1–7) com…
- **c75** (MO-EI/PI (Keane), 2006): Multiobjective Example 2, Table 2 (p. 890) — No 'Multiobjective Example 2' (aerofólio VGK robusto, M=2: Cd × desvio-padrão de Cd sob 20 perturbações geométricas de ±5%), a Tabela 2 tabula, para…
- **c81** (UA-MORL-Diff, 2025): Sec. 4.2.2, Table 1 — Tabela 1 compara o método proposto ('Ours') contra o modelo de difusão vanilla sem RL ('W/O RL', o piso) e 4 baselines de RL-guided diffusion… · Appendix C.3, Table C.3 — Estende a comparação de desempenho (mesmas 7 métricas, só QM9) a 5 métodos adicionais da literatura de guidance/amostragem para modelos de difusão,…
- **c82** (TC-SAEA, 2022): Sec. 4.4 (Comparison with Some State-of-the-art algorithms), Table 1 — Tabela única (Table 1) reportando, para os 16 problemas biobjetivo (DTLZ1-7, DTLZ1a, DTLZ3a, UF1-7), a média e o desvio-padrão do IGD sobre 20… · Sec. 4.4, Table 2 — Repete exatamente o desenho da Table 1 (mesmos 16 problemas, 8 algoritmos, IGD média±dp sobre 20 execuções, Wilcoxon rank-sum vs. TC-SAEA), mas com… · Sec. 4.4, Table 3 — Tabela adicional (Table 3) comparando TC-SAEA com Tr-SAEA (Wang et al. 2021 — antecessor direto dos mesmos autores, baseado em adaptação de domínio +…
- **c91** (EHVIMOPSO, 2019): Sec. 3.4.3, Tables 3-5 — Compara o algoritmo proposto (EHVIMOPSO, assistido por Kriging) com seu piso sem surrogate (MOPSO-CD, mesma maquinaria de dominância + distância de…
- **e1** (EMO, 2014): Sec. 4.3, Table 2 — Tabela principal (Table 2): comparação problema × orçamento × algoritmo entre as 14 configurações do EMO (EIeuclid, EIeuclid^gauss, EIhv [só em…
- **e102** (MOEA/D-ASS, 2021): Sec. V-C, Tables I–VIII (Supplemental File — não incluído neste corpus) — Tabela final de desempenho (Tabelas I–VIII do Supplemental File, não incluído neste corpus) reportando os valores de IGD e HV obtidos pelos sete…
- **e103** (IBEA-MS, 2023; roster): Sec. IV-A, Table I — Tabela algoritmo×problema (média±desvio-padrão de IGD sobre 30 execuções, DTLZ1-7 e ZDT1-4,6, D=10) comparando K-IBEA (sempre Kriging, ignora a… · Sec. IV-B, Fig. 6; tabelas numéricas completas só em Tables S.V/S.IX (material… — Comparação principal de IBEA-MS contra NSGA-II-GP e as 3 variantes AK-IBEA, via Wilcoxon rank-sum (base IGD) em DTLZ1-7, ZDT1-4 e ZDT6 (D=10) e, só…
- **e104** (RVMM, 2022): Sec. IV-C, Table I — Tabela com os valores de IGD+ (média ± desvio-padrão sobre as execuções independentes) obtidos por RVMM e sete algoritmos comparados (K-RVEA, KTA2,… · Sec. IV-C, Table II — Tabela com os valores de IGD+ (média ± desvio-padrão) obtidos por RVMM e os mesmos sete comparados em 48 instâncias de problemas com PF irregular… · Sec. IV-D; Tables SI-SII (material suplementar, não visível no corpus) — Comparação de escalabilidade: RVMM (usando GP incremental em vez do GP completo, por custo) contra EDN-ARMOEA, K-RVEA, CSEA, MOEA/D-EGO e KTA2 em 87… · Sec. IV-I, Table III — Tabela IGD+ (média±dp, mesmo esquema de símbolos +/−/∼ vs. RVMM das Tabelas I-II, confirmado por fragmento via OCR) para RVMM e os sete comparados em…
- **e16** (EGBO, 2024): Sec. Synthetic studies (parágrafo final); Supplementary Discussion subsection 2.2 (não… — O artigo menciona ter testado EGBO e qNEHVI-BO em problemas adicionais do MW test suite e do ZDT test suite (2 e 3 objetivos), afirmando que EGBO…
- **e21** (PIO, 2025): Table 2; Results, 'Optimization results of single-objective task' — Compara três funções de fitness — DOM (maximização direta da média, sem incerteza), EI (expected improvement, incerteza usada de forma exploratória)… · Table 3; Results, 'Optimization results of multi-objective tasks' — Estende a comparação de placar para as 6 tarefas multi-objective, contrastando três funções agnósticas à incerteza — WS (soma ponderada pelo inverso…
- **e3** (HeE-MOEA, 2019): Sec. V-D, Table I — Tabela com a média (linha 1) e desvio-padrão (linha 2) de HV para HeE-MOEA e GP-MOEA, em 16 problemas de teste (DTLZ1-7, WFG1-9) com N=40 variáveis… · Sec. V-D, Table II — Tabela com a média (desvio-padrão) de IGD para HeE-MOEA e GP-MOEA usando apenas o critério LCB, nos mesmos 16 problemas mas cobrindo as quatro… · Sec. V-F, Table III (linha NSGA-II) — Dentro da Table III (HV, média±dp, critério ExI, DTLZ1-7, N=10/20/40/80), a linha que compara HeE-MOEA contra o piso NSGA-II SEM surrogate — o único… · Sec. V-F, Table IV — Table IV: média (desvio-padrão) de IGD para HeE-MOEA (base MOEA/D) contra o piso MOEA/D SEM surrogate, nos 9 problemas WFG com N=20, critério ExI…
- **e4** (TSEMO, 2018): Sec. 8.3, Fig. 6; Sec. 8.7 — Para os 9 problemas de teste, o artigo compara TSEMO (b=1), BS-TSEMO (b=4), ParEGO, EHV e NSGA-II via boxplots do indicador de hipervolume apos 20… · Sec. 8.4, Fig. 7; Sec. 8.7 — A mesma bateria de 9 problemas x 5 algoritmos x 20 execucoes e reavaliada com a distancia geracional invertida modificada (IGD de Ishibuchi et al.… · Sec. 8.5, Fig. 8; Sec. 8.7 — A mesma bateria e reavaliada com o espalhamento generalizado (Delta*, metrica de diversidade nao Pareto-compliant, Zhou et al. [67]), em boxplots…
- **e40** (SBP-BO, 2023): Sec. IV-B-1 (Comparison with state-of-the-art methods), Tables I-II, p.8-11 — Tabela comparativa do IGD+ final (media(desvio-padrao) sobre 20 execucoes) de K-RVEA, HK-RVEA e SBP-BO em DTLZ1-7 e WFG1-9, com m=3,5,10 objetivos,… · Sec. IV-B-3 (Results on bi-objective heterogeneous problems), Table V, p.11-12; mencao a… — Comparacao do SBP-BO com tres metodos de transfer learning especificos para heterogeneidade bi-objetivo (T-SAEA, Tr-SAEA, TC-SAEA) em 16 problemas…
- **e64** (SA-MOPSO (PPD), 2025): Sec. 5.1.1, Table 2, Fig. 8, Fig. 9 — Para cada uma das 3 funções de benchmark (KUR, ZDT, OSY), SA-MOPSO (assistido por GPR) e PB-MOPSO (a mesma MOPSO rodando direto sobre a função… · Sec. 5.1.1 (menção); Table S1 (Supporting Information S1, não disponível neste PDF) — O artigo menciona, sem reproduzir no corpo do texto, que uma comparação de métricas de hipervolume entre os resultados de SA-MOPSO e PB-MOPSO nos 3… · Sec. 5.2.2, Table 4, Fig. 14 — Além do Run A (desenho inicial 100% inviável), um Run B usa uma população inicial 100% viável as restrições simples (100 de 25.200 vetores gerados…
- **e7** (EDN-ARMOEA, 2022; roster): Sec. IV-C, Table II (DTLZ1-7); número agregado citado no texto combina com Table SIII… — Tabela de desempenho final EDN-ARMOEA × GP-ARMOEA × HeE-ARMOEA em DTLZ1-7, para d∈{20,40,60,100} com m=3 fixo — testando o efeito da DIMENSÃO DE… · Sec. IV-C, Table III (DTLZ1-7); equivalente WFG em Table SIV (Supplementary material,… — Mesma estrutura da tabela anterior, mas variando o NÚMERO DE OBJETIVOS m∈{3,5,10,20} com d=40 fixo, em DTLZ1-7 — testando o efeito da escalada em… · Sec. IV-E; Tables SVIII-SIX (Supplementary material, ausentes deste corpus — achados… — Comparação de EDN-ARMOEA com dois métodos de estado da arte externos — K-RVEA (GP-assistido, RVEA) e MOEA/D-EGO (GP-assistido, MOEA/D) — na suíte…
- **e74** (CLMEA, 2023; roster): Sec. IV-D, Table III; Fig. 6 (curvas 100D); Fig. 7(a) (violin plot); Fig. 8 (frentes… — CLMEA é comparado com 5 algoritmos SOTA assistidos por surrogate (CPS-MOEA, K-RVEA, CSEA, EDN-ARMOEA, MCEA/D) em 7 problemas DTLZ bi-objetivo,… · Sec. IV-E, Table IV; Fig. 9 (curvas 100D); Fig. 7(b) (violin plot); Fig. 8 (frente ZDT2… — Mesma estrutura da análise anterior, em 5 problemas ZDT bi-objetivo (ZDT1-4, ZDT6), D∈{30,50,100,200} (20 células). · Sec. IV-F, Table V; Fig. 10 (curvas 50D); Fig. 7(c) (violin plot); Fig. 11 (frentes 3-obj) — Mesma estrutura das duas análises anteriores, agora em 7 problemas DTLZ 3-objetivo, D∈{30,50,100,200} (28 células).
- **e86** (NSGAIII-EHVI, 2023): Sec. IV-D, Table VI — NSGAIII-EHVI é comparado com sete algoritmos SOTA assistidos por surrogate (ParEGO, SMS-EGO, EIM-EGO, KTA2, CSEA, K-RVEA, HSMEA) em DTLZ1-7 e… · Sec. IV-D, Table VII — Mesma estrutura da análise anterior (mesmos 8 algoritmos, mesmo teste, referência fixa NSGAIII-EHVI), agora em WFG1-9 e IWFG4-6 (12 problemas ×…
- **emo1** (MPoI / HypI / DomRank / MSD (4 estratégias de infill), 2017): Sec. 5 Illustration, Fig. 3, p. 878-879 — O artigo compara o hipervolume (HV) final, após 250 avaliações reais (65 de DoE inicial + 185 de busca adaptativa), das quatro estratégias propostas…
- **f9** (UA-IBEA (sigla não-oficial, proposta por mim; paper não nomeia — "Approach 1/2/3"), 2019): Sec. 4 (Experimental Results), Table 1, p. 471 — Tabela 1 reporta média e desvio-padrão do IGD (5000 pontos de referência) do arquivo final não-dominado -- obtido após a busca sobre os modelos… · Sec. 4, p. 470 (parágrafo final antes da Fig. 3) — O artigo afirma que resultados adicionais -- para mais problemas (DTLZ1, DTLZ3, WFG1-3, WFG5, WFG9) além dos 5 problemas DTLZ detalhados no artigo --…
- **jin3** (GS-MOMA / GSM (mono: GS-SOMA), 2010): Sec. IV-B-1, Tables V-XIV — Para cada um dos 10 problemas SOO (F1-F10, d=30), o artigo reporta em tabela separada (Tables V a XIV) as estatísticas — média, desvio-padrão,… · Sec. IV-C-1, Figs. 15-20 — Para cada um dos 6 problemas MOO, três painéis com Generational Distance (GD), Maximum Spread (MS) e Hypervolume Ratio (HR) por algoritmo (A:NSGA-II,…
- **mtm4** (MAES (variante MO: M-NSGA-II), 2006): Sec. V-D e V-F, Fig. 14 (p.11) e Fig. 28 (p.12) — Para a função de Ackley (Fig. 14) e para o problema de Keane (Fig. 28), o artigo apresenta um gráfico de barras com a média e o desvio-padrão do…
- **pp6** (AB-MOEA, 2020): Sec. 4.4.1, Table 1, Table 2 — Estudo piloto que compara as três configurações do próprio método (SM-MOEA = LCB fixa + amostragem adaptativa; AS-MOEA = AF adaptativa + amostragem… · Sec. 4.4.2, Table 3, Table 4 — Comparação principal do artigo: AB-MOEA contra três SAEAs bayesianas do estado da arte (K-RVEA, MOEA/D-EGO, SMS-EGO), todas baseadas em GP, nos 16… · Sec. 4.4.2, Table 5, Table 6 — Decomposição da comparação principal em convergência (GD) e diversidade (spread/Δ) separadamente, para um SUBCONJUNTO de 8 problemas (DTLZ1a, DTLZ2,… · Sec. 5, Table 7 — Estudo de caso em um problema real de engenharia (projeto de aerofólio RAE2822 via simulação CFD, 2 objetivos: arrasto e sustentação, orçamento de…
- **wang4** (SA-NSGA-II, 2016): Sec. V-D, Table II — Compara, sob o MESMO número de gerações (100), o IGD (contra o conjunto de referência da avaliação exata) e o tempo computacional (s) de três… · Sec. V-D, Table III — Recomputa a comparação sob orçamento apertado, mas medido em TEMPO DE PAREDE (1 hora de execução, não gerações/avaliações) para as mesmas três…

**Complementos e correções (06/09/2026).** A mineração confirma o split por comunidade (§0.4): EA/PlatEMO → IGD/IGD+ média(dp) + Wilcoxon (b3, b4, c122, c141, c217, e103, e74); BO/BoTorch → log HV difference/regret, média ± 2 EP, sem teste (c100, c154, c262, c131, c149, e81). Convenções minoritárias dignas de nota: mediana e IQR (b1, c238 mediana+média+dp, b5 mediana), min/média/máximo (b3), média[dp](rank) (c1), rank médio com contagem +/=/− (c241, c267). Onze do roster aparecem; e103 e b5 (offline) reavaliam na função verdadeira antes de tabular (⑦).

**Score (0–10): 10.** **Justificativa.** P alta: é o substrato factual de todas as leituras (quem entrega o quê, onde). D: feita (F), cache pronto; só pede recomputar a matriz offline com a ⑦ do e103 (decisão 12). C: 53/72 — a análise mais frequente do corpus ao lado da visualização de fronteiras; a forma tabular com teste é a convenção dominante (26/38 na R2, agora 53/72 incluindo mapas de calor). V: base das fichas 2, 3, 4, 6, 17, 22. Núcleo do capítulo; a única decisão real é editorial (corpo × apêndice; mediana × média).


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 9 artigos / 13 análises** — dos 38 iniciais: 5 · dos 7 do roster minerados agora: 1 · dos 27 complementares: 3 · artigos do roster (15): 2.

- **b14** (SA²-MOEA, 2024): Sec. 4.6.1, Table 5 — Comparação final de IGD entre SA²-MOEA e 6 SA-MOEAs da literatura (ADSAPSO, HeEMOEA, MOEA/D-EGO, KRVEA, KTA2, PCSAEA) nos 7 problemas DTLZ1-DTLZ7,… · Sec. 4.6.2, Table 6 — Mesma comparação da análise anterior, agora nos 9 problemas WFG1-WFG9, cada um com 4 combinações (M,D) - 36 configurações no total - mesma convenção…
- **b5** (Prob-RVEA / Prob-MOEA/D (+ Hyb-RVEA / Hyb-MOEA/D), 2022; roster): Sec. IV-A (parágrafo imediatamente antes da apresentação da Table I) — Teste de Wilcoxon pareado (rank-sum) conduzido entre TODAS as 8 abordagens (não apenas cada uma contra a melhor), com os p-valores corrigidos por… · Sec. IV-A, Fig. 8 — Mapas de calor (heatmap) do HV e do RMSE (ambos na função verdadeira) para TODAS as instâncias DBMOPP testadas (não só as 'poucas' da Tabela I), com…
- **b7** (DR (Dual-Ranking), 2026): Sec. 4.4, Table 3; Material Suplementar Sec. 1.4, Table 8 — Ranking agregado dos 9 métodos (5 baselines + 4 variantes +DR) sobre os 8 problemas não-restringidos, dataset limitado: rank (1=melhor) calculado por… · Sec. 4.4, Table 4; Material Suplementar Sec. 1.4, Table 10 — O mesmo ranking agregado (rank médio +/- desvio-padrão sobre MSE/IGD+/HV x 8 problemas) recomputado para a condição de dataset com 1.000 amostras…
- **c1** (BS-MOBO, 2018): Sec. IV-A, Table I — Tabela I: matriz média[desvio-padrão](rank) do IGD para os 27 problemas de 8 dimensões, obtida por 8 configurações (ParEGO, HypI, SMS-EGO… · Sec. IV-B, Table II — Tabela II: mesma estrutura da Tabela I, agora para os 27 problemas em D=50, orçamento NFE=1000, com 7 configurações (2 pisos sem surrogate: MOEA/D,…
- **c131** (MORBO, 2022): Apendice F.4, Table 6 — Ranking medio de cada metodo atraves dos 3 problemas (DTLZ3, DTLZ5, DTLZ7), calculado a partir do HV medio final de cada replica, separadamente para…
- **c241** (EMMOEA, 2023): Sec. III-E, Table VII — Tabela-resumo que agrega as contagens de +/-/≈ (Wilcoxon vs. EMMOEA) das três tabelas de comparação em uma única contagem por baseline, sobre as 69…
- **e102** (MOEA/D-ASS, 2021): Sec. V-C, Tables I–VIII (Supplemental File — não incluído neste corpus) — Tabela final de desempenho (Tabelas I–VIII do Supplemental File, não incluído neste corpus) reportando os valores de IGD e HV obtidos pelos sete…
- **e74** (CLMEA, 2023; roster): Fig. 7 (a, b, c) — Gráficos de violino (distribuição, não só a média) do ranking do algoritmo em cada problema, agregados por suíte/dimensionalidade de objetivos: DTLZ…
- **emo1** (MPoI / HypI / DomRank / MSD (4 estratégias de infill), 2017): Sec. 5 Illustration, Fig. 3, p. 878-879 — O artigo compara o hipervolume (HV) final, após 250 avaliações reais (65 de DoE inicial + 185 de busca adaptativa), das quatro estratégias propostas…

**Score (0–10): 8.** **Justificativa.** Derivada barata de 1 (rank médio por linha), já feita (F). C: 9/72 — o corpus a usa como linha-resumo (average rank, contagem +/=/−) mais do que como figura própria; c1, b7, c131, c241 e e74 (violin do ranking) são os exemplos. P média: resume, não explica. Entra como uma linha/figura pequena ao lado de 1 e 3; não como seção própria.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 28 artigos / 73 análises** — dos 38 iniciais: 15 · dos 7 do roster minerados agora: 3 · dos 27 complementares: 10 · artigos do roster (15): 7.

- **b1** (ParEGO, 2006; roster): Sec. VIII, Table VI — Tabela algoritmo x problema do S-measure (indicador de hipervolume) após 100 avaliações de ParEGO e 100 de NSGA-II, nas 9 funções MOO, com média e… · Sec. VIII, Table VII — Mesma tabela algoritmo x problema do S-measure, agora após o orçamento total (250 avaliações ParEGO / 260 NSGA-II), com média, desvio-padrão e teste… · Sec. VIII, Table VIII — Tabela algoritmo x problema do indicador epsilon binário aditivo (ambas as direções, I_ParEGO,NSGA-II e I_NSGA-II,ParEGO) após 100 avaliações de cada… · Sec. VIII, Table IX; p. 62–63 — Mesma tabela do indicador epsilon binário aditivo, agora no orçamento total (250/260 avaliações), mediana (IQR) e Mann–Whitney por função.
- **b13** (AdaMoR-DDMOEA, 2025): Sec. 5.2, Table 4 (colunas DNN-DDMOEA e XGBOOST-DDMOEA) — Tabela de IGD (média ± dp, teste de Wilcoxon rank-sum, símbolos +/≈/−, melhor em negrito) comparando AdaMoR-DDMOEA (seleção adaptativa DNN/XGBoost)… · Sec. 5.2, Table 4 (coluna AdaMoR-DDMOEA (WO/MU)) — Mesma Tabela 4, coluna AdaMoR-DDMOEA (WO/MU): variante do algoritmo SEM a fase de atualização do surrogate por indivíduos confiáveis (Algoritmo 3… · Sec. 5.4, Table 5 — Tabela final de IGD (média ± dp, Wilcoxon rank-sum, símbolos +/≈/− relativos ao AdaMoR-DDMOEA, melhor em negrito) comparando AdaMoR-DDMOEA contra 4…
- **b14** (SA²-MOEA, 2024): Sec. 4.6.1, Table 5 — Comparação final de IGD entre SA²-MOEA e 6 SA-MOEAs da literatura (ADSAPSO, HeEMOEA, MOEA/D-EGO, KRVEA, KTA2, PCSAEA) nos 7 problemas DTLZ1-DTLZ7,… · Sec. 4.6.2, Table 6 — Mesma comparação da análise anterior, agora nos 9 problemas WFG1-WFG9, cada um com 4 combinações (M,D) - 36 configurações no total - mesma convenção…
- **b3** (K-RVEA, 2018; roster): Sec. IV-A; Sec. IV-B; Table I — Tabela algoritmo × problema (DTLZ1-DTLZ7) × k (3,4,6,8,10 objetivos, n=10 fixo) do IGD (min/média/máximo) de K-RVEA contra RVEA (piso sem surrogate,… · Sec. IV-B; Table II — Mesma estrutura de tabela (IGD min/média/máximo, Wilcoxon), agora só para k=3 e k=4, num orçamento MENOR e determinado externamente (120 e 115… · Sec. IV-B; Table III — Tabela IGD (min/média/máximo) de K-RVEA contra MOEA/D-EGO apenas, para k=3 (única contagem de objetivos em que a implementação de MOEA/D-EGO dos… · Sec. IV-B, parágrafo antes da Tabela I — O artigo também computa hypervolume (métrica secundária) para a MESMA matriz algoritmo×problema×k da Tabela I (DTLZ, K-RVEA/RVEA/ParEGO), usando como… · Sec. IV-B, último parágrafo antes da discussão de custo (p. 10) — O artigo repete o mesmo desenho experimental da Tabela I (K-RVEA vs RVEA vs ParEGO/MOEA-D-EGO/SMS-EGO conforme aplicável) na suíte WFG (objetivos com…
- **b4** (CSEA, 2019; roster): Sec. IV-C, Table III — Tabela final de comparação entre CSEA e cinco algoritmos (NSGA-III — único piso sem surrogate — ParEGO, CPS-MOEA, K-RVEA, MOEA/D-EGO) em 35…
- **b8** (KTA2, 2021): Sec. IV-C, Table I — O artigo substitui o modelo substituto de KTA2 (o modelo insensível a pontos influentes) pelo Kriging original, criando a variante KTA2(O), e compara… · Sec. IV-E-1, Table III — Comparação principal do artigo: KTA2 contra 5 SAEAs da literatura (HSMEA, CSEA, KRVEA, MOEA/D-EGO, ParEGO) em 35 instâncias DTLZ1-DTLZ7 (M em… · Sec. IV-E-2, Table IV — Mesma comparação de 6 algoritmos (KTA2 vs HSMEA, CSEA, KRVEA, MOEA/D-EGO, ParEGO), agora em 45 instâncias WFG1-WFG9 (M em {3,4,6,8,10}, D em…
- **c1** (BS-MOBO, 2018): Sec. IV-A, Table I — Tabela I: matriz média[desvio-padrão](rank) do IGD para os 27 problemas de 8 dimensões, obtida por 8 configurações (ParEGO, HypI, SMS-EGO… · Sec. IV-B, Table II — Tabela II: mesma estrutura da Tabela I, agora para os 27 problemas em D=50, orçamento NFE=1000, com 7 configurações (2 pisos sem surrogate: MOEA/D,…
- **c10** (SP-RV-MOEANet, 2021): Table I; Sec. Experiments on synthetic networks — Tabela com a média ± desvio-padrão do HV do conjunto não-dominado final para 5 algoritmos (MOEA-RSFMMA, MOEA0, P-MOEANet, P-RV-MOEANet,… · Table III; Fig. 5; Sec. Experiments on real-world networks — Tabela e figura com o desempenho (HV médio ± dp, teste de Wilcoxon vs. SP-RV-MOEANet, e tempo de execução) dos 5 algoritmos em duas redes reais — a…
- **c105** (SMS-EGO, 2008): Sec. 4 (Experiments), Table 1, p. 790 — Tabela unica (Tabela 1) reportando, para cada uma das 5 funcoes de teste (OKA2, R-ZDT1, R-ZDT4relax, R-DTLZ2 m=3, R-DTLZ2 m=5) e cada um dos 3…
- **c122** (θ-DEA-DP, 2022; roster): Sec. IV-B, Table IV — Tabela de comparação final entre θ-DEA-DP e cinco algoritmos (θ-DEA — piso interno sem preselecão via surrogate, mesma engine evolutiva — ParEGO,… · Sec. IV-C, Table V — Mesma estrutura da Tabela IV, agora nos 6 problemas escalados para 5 objetivos (DTLZ1/2/4/7, WFG6/7, n=10 variáveis) — primeira leitura de desempenho… · Sec. IV-C, Table VI — Mesma estrutura, nos mesmos 6 problemas escalados para 8 objetivos (n=10) — segunda leitura em regime many-objective, no limite superior testado pelo…
- **c141** (MMRAEA, 2025; roster): Sec. Main comparison, Table 4 — Tabela de comparação final entre MMRAEA e quatro SAEAs do estado da arte (CPS-MOEA, MOEA/D-RBF, EDN-ARMOEA, MCEA/D) em 48 instâncias (DTLZ1-7 3-obj +… · Sec. Main comparison, Table 5 — Mesma estrutura da Table 4, agora nos 36 instâncias do WFG1-9 (3-obj) × d=20,40,60,100 — segunda suíte da comparação principal. · Sec. Main comparison, Table 6 — Sumário do teste de Friedman (+/−/≈, α=0.05) correspondendo às Tabelas 4 e 5, agregado por bloco de problemas (DTLZ1-7+ZDT1-4,6; WFG1-9) e total,…
- **c217** (PC-SAEA, 2023; roster): Sec. 4.3, Table 1 — Tabela final de IGD média±dp para PC-SAEA e os 7 baselines em DTLZ1–DTLZ7 (m=2,3; 14 instâncias), com teste de Wilcoxon rank-sum (α=0,05) e símbolos… · Sec. 4.3, Table 2 — Tabela final de IGD média±dp para PC-SAEA e os 7 baselines em WFG1–WFG9 (m=2,3; 18 instâncias), mesmo protocolo de Wilcoxon e símbolos da Tabela 1. · Sec. 4.3, Table 3 — Tabela final de IGD média±dp para PC-SAEA e os 7 baselines em MaF1–MaF5 (m=2,3; 10 instâncias), mesmo protocolo de Wilcoxon e símbolos das Tabelas 1… · Sec. 4.3, Table 4 — Tabela final de HV média±dp (não IGD, pois a frente verdadeira é desconhecida) para PC-SAEA e os 7 baselines nos 3 problemas reais CSI (m=13,d=7),…
- **c241** (EMMOEA, 2023): Sec. III-E, Table IV — Tabela de IGD (média±dp) do EMMOEA contra 5 algoritmos surrogate-assisted estado-da-arte (CSEA, K-RVEA, HSMEA, MOEA/D-EGO, EIM) em DTLZ1-DTLZ7 com 3,… · Sec. III-E, Table V — Mesma estrutura da análise anterior (IGD média±dp, Wilcoxon vs. EMMOEA, 20 execuções), aplicada a MaF1-MaF6 e MaF13 com 3, 5 e 10 objetivos (21… · Sec. III-E, Table VI — Mesma estrutura das duas análises anteriores (IGD média±dp, Wilcoxon vs. EMMOEA, 20 execuções), aplicada a WFG1-WFG9 com 3, 5 e 10 objetivos (27… · Sec. III-E, Table VII — Tabela-resumo que agrega as contagens de +/-/≈ (Wilcoxon vs. EMMOEA) das três tabelas de comparação em uma única contagem por baseline, sobre as 69…
- **c261** (DirHV-EGO, 2024): Sec. V-B/V-C, p.8-9, Table III — Com q=1 (busca sequencial, sem seleção de lote), compara quatro critérios de EI multiobjetivo — EHVI, ADirHV-EI (média ponderada do DirHV-EI), ETI e… · Sec. V-C, p.9-10, Table IV — Compara os quatro algoritmos paralelos completos (KB&EHVI-EGO, PEIM-EGO, MOEA/D-EGO, DirHV-EGO — cada um com sua própria estratégia de seleção de q… · Sec. V-E, p.11, Table V — Testa DirHV-EGO contra os mesmos três concorrentes paralelos em cinco problemas reais de engenharia (RE1-RE5: hatch cover, treliça de 4 barras,… · Supplementary Sec. III-C, p.8-9, Table III (Supplementary) — Testa DirHV-EGO (N=295 para m=4, N=462 para m=6 direções via incremental lattice design, q=5) contra quatro algoritmos de otimização many-objective…
- **c267** (SAMOEA-TL2M, 2025): Sec. IV-C, Table I — Tabela final de desempenho (Tabela I) com o IGD médio(desvio-padrão) obtido pelos 5 baselines e pelo SAMOEA-TL2M nos 7 problemas tri-objetivo… · Sec. IV-C, Table II — Mesmo desenho da Tabela I, aplicado aos 9 problemas tri-objetivo WFG1–WFG9 em D=30, 50, 70, 100 (36 células): IGD médio(desvio-padrão), símbolo de… · Sec. IV-C, Table III — Mesmo desenho das Tabelas I–II, aplicado aos 7 problemas tri-objetivo MaF1–MaF7 em D=30, 50, 70, 100 (28 células). Diferente das duas tabelas… · Sec. IV-C, Table IV — Extensão de generalização: para verificar se a vantagem do SAMOEA-TL2M sobre os dois concorrentes mais fortes (SPGP-SAEA e TP-SAEA, os que mais… · Sec. IV-D-1, Table V — Ablação da estratégia de dois níveis (Tabela V): SAMOEA-TL2M-v1 (só o primeiro nível — convergência/diversidade via SDE, SEM gestão de incerteza/IDW)… · Sec. IV-D-2, Table VI — Ablação do indicador ARI (Tabela VI): SAMOEA-TL2M-R substitui o gatilho informado (ARI ≥ α decide entre nível 1 e nível 2) por uma escolha ALEATÓRIA… · Sec. IV-E, Table VII — Aplicação a um caso real (Tabela VII): os mesmos 5 baselines e o SAMOEA-TL2M são comparados em 6 problemas TREE (estimação de erro de razão em…
- **c48** (IBE-CSEA, 2021): Sec. 4.1/4.5/4.6, Table 3 (IGD), Table 4 (HV) — Tabela principal de comparação: IGD (Table 3) e HV (Table 4) do IBE-CSEA contra NSGA-III (piso) e 5 SAEAs (CPS-MOEA, MOEA/D-EGO, K-RVEA, KTA2, CSEA)…
- **c71** (SAEA/ME, 2020): Sec. 4.1, Table 1 — Tabela única (Table 1) compara SAEA/ME contra três SAEAs do estado da arte (ParEGO, MOEA/D-EGO, K-RVEA) nos 12 problemas (ZDT1,2,3,4,6; DTLZ1–7) com…
- **c82** (TC-SAEA, 2022): Sec. 4.4 (Comparison with Some State-of-the-art algorithms), Table 1 — Tabela única (Table 1) reportando, para os 16 problemas biobjetivo (DTLZ1-7, DTLZ1a, DTLZ3a, UF1-7), a média e o desvio-padrão do IGD sobre 20… · Sec. 4.4, Table 2 — Repete exatamente o desenho da Table 1 (mesmos 16 problemas, 8 algoritmos, IGD média±dp sobre 20 execuções, Wilcoxon rank-sum vs. TC-SAEA), mas com… · Sec. 4.4, Table 3 — Tabela adicional (Table 3) comparando TC-SAEA com Tr-SAEA (Wang et al. 2021 — antecessor direto dos mesmos autores, baseado em adaptação de domínio +…
- **e102** (MOEA/D-ASS, 2021): Sec. V-C, Tables I–VIII (Supplemental File — não incluído neste corpus) — Tabela final de desempenho (Tabelas I–VIII do Supplemental File, não incluído neste corpus) reportando os valores de IGD e HV obtidos pelos sete…
- **e103** (IBEA-MS, 2023; roster): Sec. IV-A, Table I — Tabela algoritmo×problema (média±desvio-padrão de IGD sobre 30 execuções, DTLZ1-7 e ZDT1-4,6, D=10) comparando K-IBEA (sempre Kriging, ignora a… · Sec. IV-B, Fig. 6; tabelas numéricas completas só em Tables S.V/S.IX (material… — Comparação principal de IBEA-MS contra NSGA-II-GP e as 3 variantes AK-IBEA, via Wilcoxon rank-sum (base IGD) em DTLZ1-7, ZDT1-4 e ZDT6 (D=10) e, só…
- **e104** (RVMM, 2022): Sec. IV-C, Table I — Tabela com os valores de IGD+ (média ± desvio-padrão sobre as execuções independentes) obtidos por RVMM e sete algoritmos comparados (K-RVEA, KTA2,… · Sec. IV-C, Table II — Tabela com os valores de IGD+ (média ± desvio-padrão) obtidos por RVMM e os mesmos sete comparados em 48 instâncias de problemas com PF irregular… · Sec. IV-I, Table III — Tabela IGD+ (média±dp, mesmo esquema de símbolos +/−/∼ vs. RVMM das Tabelas I-II, confirmado por fragmento via OCR) para RVMM e os sete comparados em…
- **e3** (HeE-MOEA, 2019): Sec. V-D, Table I — Tabela com a média (linha 1) e desvio-padrão (linha 2) de HV para HeE-MOEA e GP-MOEA, em 16 problemas de teste (DTLZ1-7, WFG1-9) com N=40 variáveis… · Sec. V-D, Table II — Tabela com a média (desvio-padrão) de IGD para HeE-MOEA e GP-MOEA usando apenas o critério LCB, nos mesmos 16 problemas mas cobrindo as quatro… · Sec. V-F, Table III (linha NSGA-II) — Dentro da Table III (HV, média±dp, critério ExI, DTLZ1-7, N=10/20/40/80), a linha que compara HeE-MOEA contra o piso NSGA-II SEM surrogate — o único… · Sec. V-F, Table IV — Table IV: média (desvio-padrão) de IGD para HeE-MOEA (base MOEA/D) contra o piso MOEA/D SEM surrogate, nos 9 problemas WFG com N=20, critério ExI…
- **e40** (SBP-BO, 2023): Sec. IV-B-1 (Comparison with state-of-the-art methods), Tables I-II, p.8-11 — Tabela comparativa do IGD+ final (media(desvio-padrao) sobre 20 execucoes) de K-RVEA, HK-RVEA e SBP-BO em DTLZ1-7 e WFG1-9, com m=3,5,10 objetivos,… · Sec. IV-B-3 (Results on bi-objective heterogeneous problems), Table V, p.11-12; mencao a… — Comparacao do SBP-BO com tres metodos de transfer learning especificos para heterogeneidade bi-objetivo (T-SAEA, Tr-SAEA, TC-SAEA) em 16 problemas…
- **e86** (NSGAIII-EHVI, 2023): Sec. IV-D, Table VI — NSGAIII-EHVI é comparado com sete algoritmos SOTA assistidos por surrogate (ParEGO, SMS-EGO, EIM-EGO, KTA2, CSEA, K-RVEA, HSMEA) em DTLZ1-7 e… · Sec. IV-D, Table VII — Mesma estrutura da análise anterior (mesmos 8 algoritmos, mesmo teste, referência fixa NSGAIII-EHVI), agora em WFG1-9 e IWFG4-6 (12 problemas ×…
- **emo1** (MPoI / HypI / DomRank / MSD (4 estratégias de infill), 2017): Sec. 5 Illustration, Fig. 3, p. 878-879 — O artigo compara o hipervolume (HV) final, após 250 avaliações reais (65 de DoE inicial + 185 de busca adaptativa), das quatro estratégias propostas…
- **jin3** (GS-MOMA / GSM (mono: GS-SOMA), 2010): Sec. IV-B-1, Table XV — Teste-t com 95% de confiança comparando GS-SOMA contra cada um dos cinco algoritmos de referência (GA, SS-SOMA-GP, SS-SOMA-PR, SS-SOMA-RBF,…
- **pp6** (AB-MOEA, 2020): Sec. 4.4.1, Table 1, Table 2 — Estudo piloto que compara as três configurações do próprio método (SM-MOEA = LCB fixa + amostragem adaptativa; AS-MOEA = AF adaptativa + amostragem… · Sec. 4.4.2, Table 3, Table 4 — Comparação principal do artigo: AB-MOEA contra três SAEAs bayesianas do estado da arte (K-RVEA, MOEA/D-EGO, SMS-EGO), todas baseadas em GP, nos 16… · Sec. 4.4.2, Table 5, Table 6 — Decomposição da comparação principal em convergência (GD) e diversidade (spread/Δ) separadamente, para um SUBCONJUNTO de 8 problemas (DTLZ1a, DTLZ2,…
- **wang4** (SA-NSGA-II, 2016): Sec. V-D, Table III — Recomputa a comparação sob orçamento apertado, mas medido em TEMPO DE PAREDE (1 hora de execução, não gerações/avaliações) para as mesmas três…

**Complementos e correções (06/09/2026).** Variações da convenção observadas: rank-sum com Bonferroni (c241), com Holm (e40), t pareado + Wilcoxon pareado (c238), Friedman por bloco (c141 Table 6), teste t 95% (jin3), Bayesian signed-rank com ROPE (e103 — ficha 4). α = 0,05 em todos os que declaram. A 'referência' do teste é sempre o algoritmo proposto (coluna base), o que difere da nossa 'melhor de cada problema'.

**Score (0–10): 9.** **Justificativa.** P alta: é o 'quem empata com o melhor' que a banca espera. D: feita (F). C: 28/72 usam rank-sum com símbolos +/=/− (convenção EA/PlatEMO; b3, b4, c122, c141, c217, c238, e103 do roster). V: decisão 3 (família de testes) — a convenção do corpus é rank-sum sem correção; a ficha 5 é o complemento pareado. Núcleo; recomendo manter a convenção do corpus como leitura principal e a pareada (5) como robustez.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 2 artigos / 3 análises** — dos 38 iniciais: 2 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 0 · artigos do roster (15): 2.

- **b5** (Prob-RVEA / Prob-MOEA/D (+ Hyb-RVEA / Hyb-MOEA/D), 2022; roster): Sec. IV-A (parágrafo imediatamente antes da apresentação da Table I) — Teste de Wilcoxon pareado (rank-sum) conduzido entre TODAS as 8 abordagens (não apenas cada uma contra a melhor), com os p-valores corrigidos por…
- **e103** (IBEA-MS, 2023; roster): Sec. IV-B, Fig. 8, Table II — Teste Bayesiano de postos sinalizados (ROPE=0,05) comparando IBEA-MS contra cada uma das 3 variantes AK-IBEA, sobre uma matriz 131×4 (todas as… · Sec. IV-B; Section S.VI (material suplementar) — O mesmo teste Bayesiano de postos sinalizados (ROPE=0,05, matriz 131×4) da análise anterior, repetido usando HV em vez de IGD como métrica de base —…

**Complementos e correções (06/09/2026).** Só dois artigos do corpus usam ranking agregado formal e ambos são do roster: b5 (Wilcoxon entre TODAS as 8 abordagens) e e103 (Bayesian signed-rank, ROPE = 0,05, matriz 131×4) — ou seja, a convenção existe no offline, não no BO.

**Score (0–10): 7.** **Justificativa.** Teste global (Friedman + Nemenyi + CD) já feito (F). C: 2/72 — só b5 e e103 (ambos do roster!) usam ranking agregado formal; no corpus BO não existe. P média: é o único resumo inferencial em uma figura (o diagrama CD). V: decisão C13 (recorte do Friedman) pendente. Entra como figura única de fechamento do placar, condicionada ao recorte; não substitui 3.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 1 artigos / 4 análises** — dos 38 iniciais: 0 · dos 7 do roster minerados agora: 1 · dos 27 complementares: 0 · artigos do roster (15): 1.

- **c238** (EIM, 2017; roster): Sec. VI-A, Table II, Figs. 9-11 — Tabela com mediana, média e desvio-padrão do hypervolume e do IGD, sobre 10 execuções independentes, para os 6 critérios (EIe, EIMe, EIm, EIMm, EIh,… · Sec. VI-B, Table III, Fig. 12 — Mesma estrutura da A1 (mediana/média/s.t.d. de HV e IGD sobre 10 execuções, teste t pareado + Wilcoxon pareado, α=0.05), aplicada ao DTLZ2 com… · Sec. VI-C, Table IV, Fig. 13 — Mesma estrutura da A1/A2 (mediana/média/s.t.d. de HV e IGD sobre 10 execuções, teste t pareado + Wilcoxon pareado, α=0.05), aplicada ao DTLZ5 com… · Sec. VI-D, Table V, Fig. 14 — Mesma estrutura da A1-A3 aplicada ao DTLZ7 com m∈{3,4,6} objetivos (n=6, orçamento 200) — problema com frente desconexa em múltiplas peças (2^(m-1)…

**Complementos e correções (06/09/2026).** c238 (EIM, roster) é o único que pareia: t pareado + Wilcoxon pareado sobre 10 execuções. O DoE compartilhado por semente (D25) torna o pareamento legítimo na bateria — nenhum artigo do corpus tem esse desenho.

**Score (0–10): 7.** **Justificativa.** T (torre 22/08). C: 1/72 (c238 usa t pareado + Wilcoxon pareado). P: o DoE compartilhado por semente (D25/cap. 4) é um ativo de desenho que o corpus não tem — o teste pareado por semente com Holm e região de equivalência é a leitura que esse desenho compra; e a rope conversa com o piso de ruído (59). Custo baixo (já computada). Recomendo como robustez de 3 (um parágrafo + tabela no apêndice), não como leitura principal, para não abrir a discussão de multiplicidade no corpo.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 1 artigos / 1 análises** — dos 38 iniciais: 0 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 1 · artigos do roster (15): 0.

- **jin3** (GS-MOMA / GSM (mono: GS-SOMA), 2010): Sec. IV-C-1, Figs. 15-20 — Para cada um dos 6 problemas MOO, três painéis com Generational Distance (GD), Maximum Spread (MS) e Hypervolume Ratio (HR) por algoritmo (A:NSGA-II,…

**Score (0–10): 8.** **Justificativa.** T. C: 1/72 como 'taxa por bloco' (jin3), mas a leitura por família é a moldura de §D9.1 (régua por família, não por D — conclusão vinculante). P alta: os blocos {ZDT} ≫ {BBOB, MMF} ≫ {WFG, DTLZ} organizam a narrativa de 9/16 e explicam por que D não é a variável. D: pronta. Entra como a leitura que ordena a §5.x do placar; custo zero.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 12 artigos / 16 análises** — dos 38 iniciais: 8 · dos 7 do roster minerados agora: 2 · dos 27 complementares: 2 · artigos do roster (15): 5.

- **b15** (U-RankMOEA, 2026): Sec. 4.2 (Table 1); Apendice L (Table 11, D=500) — Reivindicacao textual, cruzando as Tabelas 1, 3 e 11, de que a vantagem de U-RankMOEA sobre os baselines CRESCE com a dimensao de decisao D (30 -> 50… · Apendice O, Fig. 17 — Figura de escalonamento em alta dimensao: IGD final em funcao do orcamento disponivel (escala log), afirmando estabilidade do metodo ate D=500 e…
- **b4** (CSEA, 2019; roster): Sec. IV-E, Fig. 10 — Examina o desempenho de CSEA e outros cinco algoritmos (NSGA-III, CPS-MOEA, ParEGO, MOEA/D-EGO, K-RVEA) em ZDT1 (bi-objetivo) com d=10, 20 e 30…
- **c10** (SP-RV-MOEANet, 2021): Table II; Sec. Experiments on synthetic networks — Tabela comparando MOEA-RSFMMA e SP-RV-MOEANet em HV médio e tempo de execução para redes SF de 500 nós (médias sobre 5 realizações) e 1000 nós…
- **c100** (qEHVI, 2020): Apêndice F.4 (ausente deste corpus); citado nas Sec. 3.3 e 6 — [nova] qEHVI em espaços de objetivos de alta dimensão via decomposição aproximada
- **c131** (MORBO, 2022): Apendice F.1 ('Low-dimensional problems'), Fig. 9 — Curva de HV medio x 200 avaliacoes (q=1, exceto NSGA-II com q=5 para evitar populacao unitaria) em dois problemas de BAIXA dimensao, fora do…
- **c149** (LBN-MOBO, 2023; roster): Sec. C.7, Fig. 19 — Repete a comparação (LBN-MOBO, NSGA-II, DGEMO, Random) no gamut de 8 tintas (espaço de design menor que o de 44 tintas), evolução do HV e gamut…
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF), 2021; roster): Apendice H.8, Fig. 16 — [nova] Escalabilidade em numero de objetivos (M=5)
- **c71** (SAEA/ME, 2020): Sec. 4.1, Table 1 — Tabela única (Table 1) compara SAEA/ME contra três SAEAs do estado da arte (ParEGO, MOEA/D-EGO, K-RVEA) nos 12 problemas (ZDT1,2,3,4,6; DTLZ1–7) com…
- **c82** (TC-SAEA, 2022): Sec. 4.4 (parágrafo de transição entre Table 1 e Table 2) — [nova] Sensibilidade à razão de tempos de avaliação τ entre objetivo lento e rápido
- **e40** (SBP-BO, 2023): Sec. IV-B-2 (Influence of different r and rthres on the optimization performance), Tables… — [nova] Sensibilidade ao vetor de razao de custo r e ao limiar rthres
- **e7** (EDN-ARMOEA, 2022; roster): Sec. IV-C, Table II (DTLZ1-7); número agregado citado no texto combina com Table SIII… — Tabela de desempenho final EDN-ARMOEA × GP-ARMOEA × HeE-ARMOEA em DTLZ1-7, para d∈{20,40,60,100} com m=3 fixo — testando o efeito da DIMENSÃO DE… · Sec. IV-E; Tables SVIII-SIX (Supplementary material, ausentes deste corpus — achados… — Comparação de EDN-ARMOEA com dois métodos de estado da arte externos — K-RVEA (GP-assistido, RVEA) e MOEA/D-EGO (GP-assistido, MOEA/D) — na suíte…
- **e74** (CLMEA, 2023; roster): Sec. IV-D, Table III; Fig. 6 (curvas 100D); Fig. 7(a) (violin plot); Fig. 8 (frentes… — CLMEA é comparado com 5 algoritmos SOTA assistidos por surrogate (CPS-MOEA, K-RVEA, CSEA, EDN-ARMOEA, MCEA/D) em 7 problemas DTLZ bi-objetivo,… · Sec. IV-E, Table IV; Fig. 9 (curvas 100D); Fig. 7(b) (violin plot); Fig. 8 (frente ZDT2… — Mesma estrutura da análise anterior, em 5 problemas ZDT bi-objetivo (ZDT1-4, ZDT6), D∈{30,50,100,200} (20 células). · Sec. IV-F, Table V; Fig. 10 (curvas 50D); Fig. 7(c) (violin plot); Fig. 11 (frentes 3-obj) — Mesma estrutura das duas análises anteriores, agora em 7 problemas DTLZ 3-objetivo, D∈{30,50,100,200} (28 células).

**Complementos e correções (06/09/2026).** Afirmações contrárias ao nosso resultado, para o texto: b15 ('a vantagem CRESCE com D'), e74/c141 (alta dimensão como motivação), c131 (100D+). Afirmações a favor: c1 (GP perde para BNN só em 50D com 1000 pontos — o regime muda com o orçamento, não com D isolado), e103 (insensível a D em 10→30). Ver Anexo 8.5 ('alta dimensão').

**Score (0–10): 9.** **Justificativa.** T. C: 12/72 fazem escalabilidade em D (b4, b15, c122, e7, e74, e103 do roster/entorno; R2#8 19/38) — é convenção forte. P alta: o resultado NEGATIVO da bateria (a vantagem não cresce com D; a régua é por família) contradiz a expectativa do corpus (b15 'vantagem cresce com D'; e74/c141 'alta dimensão'). V: cap. 4 l.117 (degrau de falha) e §D9.1. Núcleo — é um dos achados com maior potencial de contribuição, justamente por ser contra.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 8 artigos / 13 análises** — dos 38 iniciais: 4 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 4 · artigos do roster (15): 0.

- **c105** (SMS-EGO, 2008): Fig. 3, p. 791 — Figura 3 apresenta boxplots (quartis, mediana, whiskers, entalhes/notches) da distancia media (calculada analiticamente) entre a frente de Pareto…
- **c106** (EMMI (EMmI), 2016): Sec. 6.1 (MOP2 Function), Table 1, p. 16 — Compara seis configurações (3 criterios de melhoria esperada -- EMMI, CWPI, PI -- cada um com GP independente ou GP de dependencia nao-separavel) no… · Sec. 6.2 (DTLZ2 Function), Table 2, p. 18-19 — Repete o desenho da Secao 6.1 no problema DTLZ2 (d=4, m=4, frente concava), com DoE inicial de 20 pontos e 20 pontos sequenciais adicionais (n=40 no…
- **c123** (EPBII / EIPBII, 2017): Appendix A (Table, IH), Appendix B (Table, IGD) — Apêndices A e B reproduzem as Tabelas I e II acrescentando desvio padrão, melhor e pior valor entre as 10 execuções, célula a célula, para o mesmo… · Sec. VI-B-3 (texto que remete às tabelas); Appendix C, Appendix D — Apêndices C e D reproduzem as Tabelas III e IV acrescentando desvio padrão, melhor e pior valor entre as 10 execuções, para cada critério × variante…
- **c250** (K-MOGA, 2008): Sec. 4.1.1, Table 1 (p. 031401-6) — Para o exemplo ZDT2, o artigo calcula duas metricas de qualidade da fronteira propostas na literatura (Wu e Azarm 2001): a diferenca de hiperarea…
- **c65** (SABBa, 2022): Sec. 5.1.1, Fig. 5 — Para o caso-teste 1 (Taguchi biobjetivo) com surrogate de ALTA qualidade (kernel ARD anisotrópico), o artigo plota curvas de QB (distância de… · Sec. 5.1.2, Fig. 7 — O mesmo caso-teste 1 é resolvido usando um surrogate de BAIXA qualidade (kernel RBF isotrópico, 1 único lengthscale para todas as dimensões,… · Sec. 5.2, Fig. 9 — No caso-teste 2 (otimização de desempenho médio sob restrição de quantil 95%, D=4, 3 incertos — mais dimensional e com restrição de confiabilidade),…
- **c66** (PAL-SAPSO, 2019): Sec. IV-A, Table I — Tabela final com a média (desvio-padrão) do IGD sobre 20 execuções independentes, para PAL-SAPSO e os 3 MOPSOs sem surrogate (MOPSO, dMOPSO, SMPSO),…
- **e4** (TSEMO, 2018): Sec. 8.3, Fig. 6; Sec. 8.7 — Para os 9 problemas de teste, o artigo compara TSEMO (b=1), BS-TSEMO (b=4), ParEGO, EHV e NSGA-II via boxplots do indicador de hipervolume apos 20… · Sec. 8.4, Fig. 7; Sec. 8.7 — A mesma bateria de 9 problemas x 5 algoritmos x 20 execucoes e reavaliada com a distancia geracional invertida modificada (IGD de Ishibuchi et al.…
- **mtm4** (MAES (variante MO: M-NSGA-II), 2006): Sec. V-D e V-F, Fig. 14 (p.11) e Fig. 28 (p.12) — Para a função de Ackley (Fig. 14) e para o problema de Keane (Fig. 28), o artigo apresenta um gráfico de barras com a média e o desvio-padrão do…

**Score (0–10): 7.** **Justificativa.** N; dados prontos (endpoint por semente). C: 8/72 usam boxplots/dispersão entre execuções (c105, e4, c65, c123). P: responde 'o surrogate adiciona variância?' — pergunta própria da tese sobre a incerteza como fonte de instabilidade; barata (IQR por célula). Entra como figura de apoio a 9/16 (dispersão assistido × piso) ou apêndice; a ficha 77 (peso do sorteio) é a sua decomposição.



### 77. O peso do sorteio inicial: qualidade do DoE (11D−1) × endpoint, por semente

**Fontes.** [MIN] 3 análises em 3 artigos (e103 LHS × aleatória 'pouco efeito'; e3 tamanho do DoE 'sem diferença significativa'; e8 qualidade do clustering inicial) · ficha 8 (dispersão entre sementes) · [CAP4] DoE compartilhado por semente (D25).

**O que analisa.** Quanto do resultado final é o sorteio: correlação, por célula, entre a qualidade do DoE (IGD+/HV do ND do DoE, igual para todos os algoritmos na mesma semente) e o endpoint; e quanto da variância entre sementes (8) é explicada pelo DoE.

**Dados.** ① (fase = DoE vs infill; fe_index ≤ 11D−1); C (endpoint por semente).

**Objetivo.** Justificar o pareamento por semente (5/9) e medir se algoritmos 'gulosos' dependem mais do ponto de partida que os exploratórios (a incerteza como seguro contra um DoE ruim).

**O que busca revelar.** Se a ordem entre algoritmos muda com a qualidade do sorteio (interação DoE × algoritmo) — e se o piso é mais sensível ao DoE que o assistido (ou o contrário).

**Como é realizada.** Por célula: IGD+ do DoE e IGD+ final; Spearman entre os dois sobre as 30 sementes, por (algoritmo, problema); fração da variância do endpoint explicada pelo DoE (R² de regressão simples); figura: Δ(final − DoE) × qualidade do DoE por família de algoritmo.

**Técnicas.** Correlação de Spearman; R²; boxplots pareados.

**Implementação.** Sobre o cache de endpoint + um cálculo do ND do DoE por semente (① filtrado por fase) — uma célula.

**Em quantos artigos aparece (dos 72).** 3 artigos (3 análises): dos 38 iniciais 1, dos 7 do roster 0, dos 27 complementares 2; do roster (15): 1. Nas planilhas dos 38 (Ranking 2) o tipo mais próximo está indicado em Fontes.

**Estado.** N — dado pronto; custo baixo.

**Demais detalhes.** Relação: 5, 8, 9, 14 (versão offline: o dataset é o DoE). Nenhum artigo do corpus mede isso — leitura própria e barata.

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 3 artigos / 3 análises** — dos 38 iniciais: 1 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 2 · artigos do roster (15): 1.

- **e103** (IBEA-MS, 2023; roster): Sec. IV-B (parágrafo sobre aplicação a problemas reais); Table S.VIII (material… — [nova] Robustez ao método de amostragem do dataset offline (LHS × aleatória)
- **e3** (HeE-MOEA, 2019): Sec. V-E.2; Table II do material suplementar (mencionada, não incluída neste corpus) — [nova] Sensibilidade ao tamanho do DoE inicial (orçamento offline × online)
- **e8** (NN-EGO, 2020): Text S4 (S40); Figure S24 (S41); Figure S25 (S41); Table S20 (S42) — [nova] Qualidade da amostra inicial por clustering diversidade-orientado

**Score (0–10): 7.** **Justificativa.** Reproduzível e barata: ① tem o DoE (11D−1, compartilhado por semente) — HV/IGD+ do DoE vs endpoint por semente, correlação por célula. C: 3/72 (e103 LHS × aleatória 'pouco efeito', e3 tamanho do DoE, e8 clustering) — ninguém mede quanto do resultado é o sorteio. P alta: quantifica a variância que 8 atribui às sementes e justifica o pareamento (5/9); também mostra se algoritmos 'gulosos' dependem mais do sorteio. Entra como figura pequena junto de 8.

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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 19 artigos / 36 análises** — dos 38 iniciais: 10 · dos 7 do roster minerados agora: 1 · dos 27 complementares: 8 · artigos do roster (15): 5.

- **b1** (ParEGO, 2006; roster): Sec. VIII, Table VI — Tabela algoritmo x problema do S-measure (indicador de hipervolume) após 100 avaliações de ParEGO e 100 de NSGA-II, nas 9 funções MOO, com média e… · Sec. VIII, Table VII — Mesma tabela algoritmo x problema do S-measure, agora após o orçamento total (250 avaliações ParEGO / 260 NSGA-II), com média, desvio-padrão e teste… · Sec. VIII, Table VIII — Tabela algoritmo x problema do indicador epsilon binário aditivo (ambas as direções, I_ParEGO,NSGA-II e I_NSGA-II,ParEGO) após 100 avaliações de cada… · Sec. VIII, Table IX; p. 62–63 — Mesma tabela do indicador epsilon binário aditivo, agora no orçamento total (250/260 avaliações), mediana (IQR) e Mann–Whitney por função. · Sec. VII; Sec. VIII, p. 61 — O artigo também roda busca aleatória (21 execuções, até 10000 avaliações) em todos os problemas para servir de piso trivial adicional, mas os…
- **b2** (MOEA/D-EGO, 2010): Sec. VII-E-1 (The Effect of the Gaussian Model); Fig. 8(a)–(b) — Para isolar o efeito do modelo Gaussiano, os autores rodam a versão original do MOEA/D (Zhang & Li [28]), sem qualquer surrogate, com população 20 e…
- **b3** (K-RVEA, 2018; roster): Sec. IV-A; Sec. IV-B; Table I — Tabela algoritmo × problema (DTLZ1-DTLZ7) × k (3,4,6,8,10 objetivos, n=10 fixo) do IGD (min/média/máximo) de K-RVEA contra RVEA (piso sem surrogate,… · Sec. IV-B; Table II — Mesma estrutura de tabela (IGD min/média/máximo, Wilcoxon), agora só para k=3 e k=4, num orçamento MENOR e determinado externamente (120 e 115… · Sec. IV-B, parágrafo antes da Tabela I — O artigo também computa hypervolume (métrica secundária) para a MESMA matriz algoritmo×problema×k da Tabela I (DTLZ, K-RVEA/RVEA/ParEGO), usando como… · Sec. IV-B, último parágrafo antes da discussão de custo (p. 10) — O artigo repete o mesmo desenho experimental da Tabela I (K-RVEA vs RVEA vs ParEGO/MOEA-D-EGO/SMS-EGO conforme aplicável) na suíte WFG (objetivos com…
- **b4** (CSEA, 2019; roster): Sec. IV-C, Table III — Tabela final de comparação entre CSEA e cinco algoritmos (NSGA-III — único piso sem surrogate — ParEGO, CPS-MOEA, K-RVEA, MOEA/D-EGO) em 35…
- **c10** (SP-RV-MOEANet, 2021): Sec. Experiments on synthetic networks (texto); Table I; Fig. 2; Fig. 3 — O artigo compara, nas mesmas condições (redes SF/ER/SW, N=300), quatro variantes degeneradas do próprio algoritmo — MOEA0 (motor básico, sem…
- **c122** (θ-DEA-DP, 2022; roster): Sec. IV-B, Table IV — Tabela de comparação final entre θ-DEA-DP e cinco algoritmos (θ-DEA — piso interno sem preselecão via surrogate, mesma engine evolutiva — ParEGO,… · Sec. IV-C, Table V — Mesma estrutura da Tabela IV, agora nos 6 problemas escalados para 5 objetivos (DTLZ1/2/4/7, WFG6/7, n=10 variáveis) — primeira leitura de desempenho… · Sec. IV-C, Table VI — Mesma estrutura, nos mesmos 6 problemas escalados para 8 objetivos (n=10) — segunda leitura em regime many-objective, no limite superior testado pelo… · Sec. IV-C (texto entre Table VI e Fig. 6) — Discussão textual (não uma tabela/figura isolada, mas comentário comparativo cruzando as Tabelas IV/V/VI) sobre como a relação competitiva entre…
- **c24** (DTK-MODE, 2015): Sec. IV-B, Table III — No problema real TEAM 22 (SMES, D=8, M=2), a Tabela III compara, ao longo de configurações do DTK com números crescentes de pontos de amostragem…
- **c250** (K-MOGA, 2008): Sec. 4.1.1, Table 1 (p. 031401-6) — Para o exemplo ZDT2, o artigo calcula duas metricas de qualidade da fronteira propostas na literatura (Wu e Azarm 2001): a diferenca de hiperarea…
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF), 2021; roster): Apendice H.9, Fig. 17 — Comparacao de qNEHVI, qNEHVI-1, qNParEGO, TS-TCH e busca Sobol pura contra o COMO-CMA-ES -- uma estrategia evolutiva multiobjetivo SEM surrogate, ja…
- **c29** (MO P-algorithm, 2014): Sec. 7, Table 1, p. 89-90 — Tabela (Table 1) com médias e desvios-padrão, sobre 1000 execuções independentes, de quatro métricas (NP, NN, MD, DP) do multi-objective P-algorithm… · Sec. 7, Table 2, Eq. 14, p. 90-92 — Tabela (Table 2) com médias e desvios-padrão de três métricas (NN, GD, EI) do multi-objective P-algorithm e do Monte Carlo, para os problemas de duas…
- **c91** (EHVIMOPSO, 2019): Sec. 3.4.3, Tables 3-5 — Compara o algoritmo proposto (EHVIMOPSO, assistido por Kriging) com seu piso sem surrogate (MOPSO-CD, mesma maquinaria de dominância + distância de…
- **e16** (EGBO, 2024): Sec. Synthetic studies, Fig. 4c — O mesmo experimento (MW7, n=8, 10 execuções, 48 iterações) inclui também qNParEGO (aquisição por escalarização) e U-NSGA-III puro (piso evolutivo SEM… · Sec. Synthetic studies (parágrafo final); Supplementary Discussion subsection 2.2 (não… — O artigo menciona ter testado EGBO e qNEHVI-BO em problemas adicionais do MW test suite e do ZDT test suite (2 e 3 objetivos), afirmando que EGBO… · Sec. Handling input and output constraints, Fig. 5c — No problema AgNP (usando um GP treinado sobre TODOS os dados reais da campanha como pseudo-verdade de referência para HV), o artigo compara…
- **e17** (MOBO, 2021): Sec. IV-A, Fig. 7(a) — Para o problema real do fotoinjetor AWA (7 objetivos, 6 parametros), o artigo compara a evolucao do hipervolume medio (+/- 1 sigma, 10 execucoes) em…
- **e3** (HeE-MOEA, 2019): Sec. V-F, Table III (linha NSGA-II) — Dentro da Table III (HV, média±dp, critério ExI, DTLZ1-7, N=10/20/40/80), a linha que compara HeE-MOEA contra o piso NSGA-II SEM surrogate — o único… · Sec. V-F, Table IV — Table IV: média (desvio-padrão) de IGD para HeE-MOEA (base MOEA/D) contra o piso MOEA/D SEM surrogate, nos 9 problemas WFG com N=20, critério ExI…
- **e4** (TSEMO, 2018): Sec. 8.2.4; Sec. 8.6, Figs. 9-13; Sec. 8.7 — Para os 5 problemas biobjetivo, o artigo plota, num unico grafico por problema (Fig. 9), a superficie de pior caso de attainment (fracamente dominada…
- **e64** (SA-MOPSO (PPD), 2025): Sec. 5.1.1, Table 2, Fig. 8, Fig. 9 — Para cada uma das 3 funções de benchmark (KUR, ZDT, OSY), SA-MOPSO (assistido por GPR) e PB-MOPSO (a mesma MOPSO rodando direto sobre a função… · Sec. 5.2.1, Figs. 12-13 — No problema real de gestão de aquífero costeiro, com um desenho inicial de 100 vetores por LHS completamente INVIÁVEL (nenhum vetor satisfaz as… · Sec. 5.2.2, Table 4, Fig. 14 — Além do Run A (desenho inicial 100% inviável), um Run B usa uma população inicial 100% viável as restrições simples (100 de 25.200 vetores gerados…
- **e8** (NN-EGO, 2020): Figure S18 (S29); Figure S19 (S30) — Compara a distribuição de ΔGox(sol) e logP dos complexos selecionados pelo processo guiado por E[I] (front final de 8 complexos, mais os complexos de…
- **pp6** (AB-MOEA, 2020): Sec. 4.4.1, Table 1, Table 2 — Estudo piloto que compara as três configurações do próprio método (SM-MOEA = LCB fixa + amostragem adaptativa; AS-MOEA = AF adaptativa + amostragem…
- **wang4** (SA-NSGA-II, 2016): Sec. V-D, Table II — Compara, sob o MESMO número de gerações (100), o IGD (contra o conjunto de referência da avaliação exata) e o tempo computacional (s) de três… · Sec. V-D, Table III — Recomputa a comparação sob orçamento apertado, mas medido em TEMPO DE PAREDE (1 hora de execução, não gerações/avaliações) para as mesmas três…

**Complementos e correções (06/09/2026).** Convenção do corpus: o piso entra como UMA coluna (NSGA-II/III, MOEA/D, RVEA, MOPSO-CD, GA) na tabela final, sem casamento por motor; b2 (MOEA/D original vs MOEA/D-EGO) e c91 (MOPSO-CD vs EHVIMOPSO) são os casos de piso casado como o nosso. b1 compara com busca aleatória (21 execuções, 10.000 avaliações).

**Score (0–10): 10.** **Justificativa.** F. C: 19/72 comparam contra piso sem surrogate (b1, b3, b4, c122, c262 do roster; e3, e4, wang4 etc.), mas quase sempre como uma coluna a mais — o Δ pareado por semente com casamento por motor (D25) é desenho próprio. P máxima: 'o surrogate compra alguma coisa?' é a pergunta que precede a da incerteza. V: d19 (não decretar vencedor EA×BO) exige a leitura por algoritmo, não global. Núcleo.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 1 artigos / 1 análises** — dos 38 iniciais: 1 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 0 · artigos do roster (15): 1.

- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF), 2021; roster): Apendice H.9, Fig. 17 — Comparacao de qNEHVI, qNEHVI-1, qNParEGO, TS-TCH e busca Sobol pura contra o COMO-CMA-ES -- uma estrategia evolutiva multiobjetivo SEM surrogate, ja…

**Score (0–10): 8.** **Justificativa.** F. C: 1/72 (c262 vs. COMO-CMA-ES) — o corpus BO raramente compara com pisos evolutivos. P: é a versão de 9 para c154/e81/c149, que não têm piso casado; sem ela esses três ficam fora do 'compra alguma coisa'. D pronta. Entra junto com 9 (mesma figura/tabela, coluna 'banda dos 4 pisos').


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 25 artigos / 35 análises** — dos 38 iniciais: 15 · dos 7 do roster minerados agora: 4 · dos 27 complementares: 6 · artigos do roster (15): 9.

- **b13** (AdaMoR-DDMOEA, 2025): Sec. 5.2, Table 4 (colunas DNN-DDMOEA e XGBOOST-DDMOEA) — Tabela de IGD (média ± dp, teste de Wilcoxon rank-sum, símbolos +/≈/−, melhor em negrito) comparando AdaMoR-DDMOEA (seleção adaptativa DNN/XGBoost)… · Sec. 5.2, Table 4 (coluna AdaMoR-DDMOEA (WO/MU)) — Mesma Tabela 4, coluna AdaMoR-DDMOEA (WO/MU): variante do algoritmo SEM a fase de atualização do surrogate por indivíduos confiáveis (Algoritmo 3…
- **b14** (SA²-MOEA, 2024): Sec. 4.3, Table 2 — Ablação do método de quantificação de incerteza do SA²-MOEA: compara o método proposto (baseado na mudança de rank entre o melhor ensemble EMbest e o…
- **b15** (U-RankMOEA, 2026): Apendice D, Table 5 (citada no corpo como 'Table D', Sec. 4.1) — Ablacao de componentes em DTLZ2-100D (300 avaliacoes): compara o U-RankMOEA completo contra 5 variantes - excluindo a quantificacao de incerteza… · Apendice L.3 — Segunda ablacao de contribuicao de componentes, desta vez na extensao de alta dimensao (D=500, M=5): estima a fracao do gap de desempenho entre… · Apendice O, Fig. 16 (legenda interna via OCR: 'w/o Rank Classifier +0.055', 'w/o DeepGP… — Figura de barras (visualizacao) da mesma ablacao de componentes de 100D-DTLZ2, mostrando o aumento de IGD ao remover cada um de 4 modulos:…
- **b4** (CSEA, 2019; roster): Sec. III-E, Table I — Compara CSEA com uma variante própria, CSEA−, em que o segundo loop (Fig. 2) — toda a seleção assistida por surrogate (classificação + configuração…
- **b5** (Prob-RVEA / Prob-MOEA/D (+ Hyb-RVEA / Hyb-MOEA/D), 2022; roster): Sec. IV-A (discussão logo após Table I / Fig. 8) — Comparação que isola o efeito do uso da incerteza: Prob-RVEA vs. Gen-RVEA e Prob-MOEA/D vs. Gen-MOEA/D usam exatamente a mesma maquinaria evolutiva… · Sec. IV-A — Nuance sobre o componente híbrido: Hyb-RVEA e Hyb-MOEA/D (mistura 50/50 de seleção probabilística e genérica) foram propostos para combinar os…
- **b7** (DR (Dual-Ranking), 2026): Sec. 4.3 (Ablation Study and Sensitivity Analysis), Table 1; Material Suplementar Sec.… — Estudo de ablação e sensibilidade no dataset limitado (11D-1 amostras): para cada um dos 4 surrogates (GPR-RBF, GPR-Matérn, Autogluon-QR, BNN),… · Material Suplementar, Sec. 1.3 ('Optimization Results with 1000 Training data'), Table 7 — A mesma ablação DR-vs-baseline da análise anterior, repetida sobre os surrogates treinados com o dataset maior (1.000 amostras, mesma seed=42), com… · Sec. 4.3 (fim); Material Suplementar, 'Ablation Study Between Dual-Ranking and the… — Ablação isolando o componente 'dual' do dual-ranking: compara, para cada um dos 4 surrogates, a variante DR completa (não-dominância no espaço 2M…
- **b8** (KTA2, 2021): Sec. IV-D, Table II — O artigo compara KTA2 (amostragem adaptativa completa: convergência+diversidade+incerteza, escolhida por um mecanismo de avaliação de estado) contra…
- **b9** (USeMO, 2020): Sec. 5.2 ("Uncertainty maximization vs. random selection"); Fig. 4 — Ablação da segunda etapa de USeMO (seleção do candidato final dentre o conjunto de Pareto barato obtido no primeiro estágio): substitui-se a…
- **c100** (qEHVI, 2020): Sec. 4.3, Fig. 2b — Compara três estratégias de construção do lote de q candidatos que competem entre si só na forma como tratam a incerteza sobre os pontos pendentes…
- **c141** (MMRAEA, 2025; roster): Sec. Effectiveness of multi-mode RBFs, Table 2 — Ablação do mecanismo tri-modo de RBFs: MMRAEA completo (seleciona por nondominated sorting de Q=soma dos 3 ranks de qualidade, mais U=soma das…
- **c149** (LBN-MOBO, 2023; roster): Sec. 5.4, Fig. 5 — Repete os experimentos de aerofólio e gamut de cores excluindo o termo de incerteza epistêmica da aquisição 2MD (usando só os M objetivos de… · Sec. E.1, Fig. 20 — Repete os experimentos das Seções C.1.4/C.1.5 (ZDT1-30D, ZDT2-30D, ZDT3-6D) usando o Deep Ensembles original (com incerteza aleatória + epistêmica)…
- **c217** (PC-SAEA, 2023; roster): Sec. 4.5, Table 8 — A ablação central do mecanismo de confiança de PC-SAEA: compara a estratégia de gestão dinâmica (state 1/2/3 — usar diretamente, usar invertido, ou…
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF), 2021; roster): Apendice H.10, Fig. 18 — Ablacao de tres variantes de DGEMO (um metodo de lote diferente de qNEHVI) no BraninCurrin ruidoso (sigma=5%, q=1): DGEMO puro (usa a fronteira…
- **c267** (SAMOEA-TL2M, 2025): Sec. IV-D-1, Table V — Ablação da estratégia de dois níveis (Tabela V): SAMOEA-TL2M-v1 (só o primeiro nível — convergência/diversidade via SDE, SEM gestão de incerteza/IDW)…
- **c82** (TC-SAEA, 2022): Sec. 4.5, Tables 4 e 5 — Compara TC-SAEA com NS-SAEA, idêntico em tudo (incluindo o co-surrogate GP) exceto que a etapa de seleção por intervalo de confiança (CI = Y_s^a ±…
- **c97** (EnGP-MRO, 2011): Sec. 6.3 [44], Fig. 14 — O artigo compara a fronteira de Pareto obtida usando um único surrogate (o de menor erro de treino, sem qualquer tratamento de incerteza — resíduo…
- **e103** (IBEA-MS, 2023; roster): Sec. IV-A, Table I — Tabela algoritmo×problema (média±desvio-padrão de IGD sobre 30 execuções, DTLZ1-7 e ZDT1-4,6, D=10) comparando K-IBEA (sempre Kriging, ignora a…
- **e104** (RVMM, 2022): Sec. IV-E, Fig. 7 — ABLAÇÃO EXATA DA INCERTEZA: RVMM (usa a AUCB, Eq. 6, que amplifica σ elevando-o ao quadrado quando σ>1) é comparado com duas variantes que alteram só… · Sec. IV-F, Fig. 8 — Ablação fatorial 2×2 que cruza o tipo de conjunto de vetores de referência (adaptativo, usado no processo de convergência, vs. fixo/predefinido,…
- **e21** (PIO, 2025): Table 2; Results, 'Optimization results of single-objective task' — Compara três funções de fitness — DOM (maximização direta da média, sem incerteza), EI (expected improvement, incerteza usada de forma exploratória)… · Table 3; Results, 'Optimization results of multi-objective tasks' — Estende a comparação de placar para as 6 tarefas multi-objective, contrastando três funções agnósticas à incerteza — WS (soma ponderada pelo inverso…
- **e64** (SA-MOPSO (PPD), 2025): Sec. 3 (parágrafo de abertura, antes de 3.1); Figs. S1-S6 (Supporting Information S1) — Antes de propor a PPD, os autores relatam um teste preliminar feito durante o desenvolvimento do algoritmo: aplicar o critério de dominância de… · Sec. 3.4.1; Fig. S7 (Supporting Information S1), problema ZDT (Apêndice A) — Para gerir o repositório de posições não-dominadas dentro das iterações internas, os autores primeiro testaram uma função de fitness baseada em…
- **e7** (EDN-ARMOEA, 2022; roster): Sec. IV-B, Table I — Comparação de três variantes que isolam o efeito do CRITÉRIO de seleção de novos pontos reais, todas usando GP como surrogate (não EDN) e a mesma…
- **e74** (CLMEA, 2023; roster): Sec. IV-C, Table II (DTLZ bi-obj); Table S-II (DTLZ bi-obj, versão com números distintos… — CLMEA é comparado com três variantes que usam, cada uma, SOMENTE uma das três subestratégias de infill que compõem o algoritmo completo: CLMEA-s1 (só…
- **e86** (NSGAIII-EHVI, 2023): Sec. IV-B, Table IV — O artigo compara o NSGAIII-EHVI completo (que usa a MSE do kriging como dimensão extra na ordenação não-dominada, Algorithm 2) com o NSGAIII-EHVI2,…
- **f9** (UA-IBEA (sigla não-oficial, proposta por mim; paper não nomeia — "Approach 1/2/3"), 2019): Sec. 4, p. 469 (parágrafo após a Tabela 1) — Lendo a Tabela 1 como ablação: a mesma maquinaria IBEA/Kriging roda com (Approach 1/2) e sem (Generic) sigma incluído no vetor de objetivos…
- **jin3** (GS-MOMA / GSM (mono: GS-SOMA), 2010): Table XVII (definição de SS-MOMA-I); resultados em Figs. 9-20 — SS-MOMA-I usa exatamente o mesmo M1 (ensemble de GP+PR+RBF) que o GS-MOMA, mas SEM o modelo de suavização M2 (PR) — a diferença de desempenho entre…

**Complementos e correções (06/09/2026).** Ablações do próprio σ no corpus (com tudo o mais fixo): b5 Gen×Prob (a nossa), e104 (AUCB × só μ), e21 (DOM × EI × PIO), f9 (Approach 1/2 × Generic), c149 (sem termo epistêmico), b9 (incerteza × aleatório), e86 (MSE como dimensão extra × sem). Resultados NEGATIVOS ou fracos entre eles: e40 (termo SBP só melhora 9/48), c241 (EMMOEA-IP: 'mais incerteza na busca o tempo todo' perde 8/11), b15 LMC piora, c106 GP dependente não ajuda (Anexo 8.3).

**Score (0–10): 10.** **Justificativa.** F-parcial. C: 25/72 fazem ablação de componente (R2#3 26/38); 9 do roster (b4 CSEA−, b5 Gen×Prob, c141, c149 sem termo epistêmico, c217, c262, e103, e7, e74) — mas só b5 e e104/e21/f9 isolam σ com TUDO o mais fixo. P máxima: com a diretriz (1), Prob-MOEA/D × MOEA/D-média é a ÚNICA ablação exata do σ disponível na bateria — vira o substituto do OE5. V: §D9.4 (o congelamento do b5m é resultado; duas leituras 45/31), cap. 1 OE5. Núcleo; pede só a decisão das duas leituras.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 0 artigos.** Nenhuma análise dos 72 foi mapeada a esta ficha — leitura própria da tese (ou regra/nota), sem correspondente nomeado no corpus.

**Score (0–10): 8.** **Justificativa.** Subconjunto de 11 nos três reais (T). C: 0/72 como recorte nomeado; os offline reais do corpus (b13 RAE2822, c59) fazem o caso real, não a ablação. P alta: 'o primeiro resultado conclusivo, contra' — a incerteza NÃO ajudou onde mais importava (reais). D pronta. Entra como parágrafo de 11 com tabela própria; o asterisco do DDMOP7 (C14) já tem texto pronto.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 4 artigos / 6 análises** — dos 38 iniciais: 3 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 1 · artigos do roster (15): 1.

- **b5** (Prob-RVEA / Prob-MOEA/D (+ Hyb-RVEA / Hyb-MOEA/D), 2022; roster): Sec. IV-A, Table I — Tabela com a mediana (e o desvio-padrão entre as 31 execuções) do HV e do RMSE — ambos calculados reavaliando as soluções aproximadas retornadas na… · Sec. IV-A, Fig. 8 — Mapas de calor (heatmap) do HV e do RMSE (ambos na função verdadeira) para TODAS as instâncias DBMOPP testadas (não só as 'poucas' da Tabela I), com…
- **b7** (DR (Dual-Ranking), 2026): Sec. 4.4 (Comparison Experiments with Baseline Methods), Table 2; Sec. 4.1 (Performance… — Tabela final de comparação com os 5 baselines nos 8 problemas não-restringidos, dataset limitado (11D-1): MSE, IGD+ e HV por algoritmo x problema,… · Material Suplementar, Sec. 1.4 (Comparative Analysis against Baselines), Table 9 — A mesma tabela final de comparação com baselines (MSE, IGD+, HV por algoritmo x problema, 8 problemas não-restringidos), repetida com os surrogates…
- **c59** (UA-DBO, 2026): Sec. 4.2, Table 3, p. 15–16 — Tabela final (Tabela 3) comparando os 3 frameworks (CFD-based, DBO, UA-DBO) nos 3 casos de divergência de arrasto (A1, A2, A3): para DBO/UA-DBO,…
- **f9** (UA-IBEA (sigla não-oficial, proposta por mim; paper não nomeia — "Approach 1/2/3"), 2019): Sec. 4 (Experimental Results), Table 1, p. 471 — Tabela 1 reporta média e desvio-padrão do IGD (5000 pontos de referência) do arquivo final não-dominado -- obtido após a busca sobre os modelos…

**Complementos e correções (06/09/2026).** Os offline do corpus reavaliam na verdade e reportam HV + RMSE (b5), MSE + IGD+ + HV (b7), frente acreditada × verificada (c59), IGD do arquivo reavaliado (f9) — a ⑦ é a convenção. Nenhum compara online × offline na mesma bateria como nós.

**Score (0–10): 9.** **Justificativa.** F-parcial; endpoint offline = ⑦ é vinculante (§D9.2). C: 4/72 (b5, b7, c59, f9 — o regime offline é raro no corpus: 8/72 artigos offline) e todos reavaliam na verdade (b5 'HV e RMSE na função verdadeira'). P alta: é o único lugar onde a incerteza é a ÚNICA defesa contra o modelo (não há reavaliação). D: pede a regeneração com a ⑦ do e103 (B1(a) feita; decisão 12). Núcleo do bloco offline.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 3 artigos / 5 análises** — dos 38 iniciais: 2 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 1 · artigos do roster (15): 1.

- **b5** (Prob-RVEA / Prob-MOEA/D (+ Hyb-RVEA / Hyb-MOEA/D), 2022; roster): Sec. IV-A, Table I — Tabela com a mediana (e o desvio-padrão entre as 31 execuções) do HV e do RMSE — ambos calculados reavaliando as soluções aproximadas retornadas na… · Sec. IV-A, Fig. 8 — Mapas de calor (heatmap) do HV e do RMSE (ambos na função verdadeira) para TODAS as instâncias DBMOPP testadas (não só as 'poucas' da Tabela I), com…
- **c50** (PD-MOEA, 2018): Sec. 5.1, Fig. 4b-c, p.16-17 — O artigo compara, via p(x≺z)/ρ(z), a população inicial do arquivo (medições brutas dos 654 pontos, mapeadas para a carga-alvo de 300MW antes de…
- **c75** (MO-EI/PI (Keane), 2006): Multiobjective Example 1, Fig. 12a-b (p. 889) — No 'Multiobjective Example 1' (viga de Norwacki, M=2: área × tensão de flexão), o artigo compara visualmente os conjuntos de Pareto obtidos por… · Multiobjective Example 2, Fig. 13 (p. 890) — Complementando a Tabela 2, a Fig. 13 mostra visualmente, em dois painéis, os conjuntos de Pareto obtidos pelo P[I]avg (a) e pelo E[I]avg (b) contra…

**Score (0–10): 7.** **Justificativa.** N; barata (① DoE vs ⑦). C: 3/72 (b5 HV do dataset vs. final; c50; c75 visual). P média-alta: 'quanto cada offline melhora o que recebeu' é a métrica honesta do offline e mostra quando o algoritmo PIORA o dataset (fantasia). Entra como coluna/figura de 13.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 10 artigos / 13 análises** — dos 38 iniciais: 6 · dos 7 do roster minerados agora: 2 · dos 27 complementares: 2 · artigos do roster (15): 2.

- **b14** (SA²-MOEA, 2024): Sec. 4.3, Table 2 — Ablação do método de quantificação de incerteza do SA²-MOEA: compara o método proposto (baseado na mudança de rank entre o melhor ensemble EMbest e o…
- **b15** (U-RankMOEA, 2026): Apendice D, Table 5 (citada no corpo como 'Table D', Sec. 4.1) — Ablacao de componentes em DTLZ2-100D (300 avaliacoes): compara o U-RankMOEA completo contra 5 variantes - excluindo a quantificacao de incerteza… · Apendice L.3 — Segunda ablacao de contribuicao de componentes, desta vez na extensao de alta dimensao (D=500, M=5): estima a fracao do gap de desempenho entre… · Apendice O, Fig. 16 (legenda interna via OCR: 'w/o Rank Classifier +0.055', 'w/o DeepGP… — Figura de barras (visualizacao) da mesma ablacao de componentes de 100D-DTLZ2, mostrando o aumento de IGD ao remover cada um de 4 modulos:…
- **b8** (KTA2, 2021): Sec. IV-D, Table II — O artigo compara KTA2 (amostragem adaptativa completa: convergência+diversidade+incerteza, escolhida por um mecanismo de avaliação de estado) contra…
- **b9** (USeMO, 2020): Sec. 5.2 ("Uncertainty maximization vs. random selection"); Fig. 4 — Ablação da segunda etapa de USeMO (seleção do candidato final dentre o conjunto de Pareto barato obtido no primeiro estágio): substitui-se a…
- **c141** (MMRAEA, 2025; roster): Sec. Effectiveness of multi-mode RBFs, Table 2 — Ablação do mecanismo tri-modo de RBFs: MMRAEA completo (seleciona por nondominated sorting de Q=soma dos 3 ranks de qualidade, mais U=soma das…
- **c149** (LBN-MOBO, 2023; roster): Sec. 5.4, Fig. 5 — Repete os experimentos de aerofólio e gamut de cores excluindo o termo de incerteza epistêmica da aquisição 2MD (usando só os M objetivos de…
- **c81** (UA-MORL-Diff, 2025): Appendix B.6; Table 2 (linhas scalarization/constraint/gradient-based) — O restante da Tabela 2 (12 métodos: 4 scalarization-based — WS/POO/MMM/LSDW; 4 constraint-based — NMD/NMD-WS/CP/PFM; 4 gradient-based —…
- **e104** (RVMM, 2022): Sec. IV-E, Fig. 7 — ABLAÇÃO EXATA DA INCERTEZA: RVMM (usa a AUCB, Eq. 6, que amplifica σ elevando-o ao quadrado quando σ>1) é comparado com duas variantes que alteram só…
- **e86** (NSGAIII-EHVI, 2023): Sec. IV-B, Table IV — O artigo compara o NSGAIII-EHVI completo (que usa a MSE do kriging como dimensão extra na ordenação não-dominada, Algorithm 2) com o NSGAIII-EHVI2,…
- **jin3** (GS-MOMA / GSM (mono: GS-SOMA), 2010): Sec. IV-B (nota de rodapé 5), Sec. IV-B-2 — O artigo introduz SS-SOMA-Perfect (e seu análogo MOO, SS-MOMA-Perfect), uma variante com modelo substituto 'perfeito' (RMSE=0: usa a função exata mas… · Sec. IV-C-1 — Análogo à análise da SS-SOMA-Perfect, mas para o contexto multiobjetivo: GS-MOMA e os SS-MOMAs são comparados contra SS-MOMA-Perfect (oracle com…

**Complementos e correções (06/09/2026).** Diretriz (1) de 06/09: descartada. Os 10 artigos listados fazem o contrafactual como variante executada — é a forma canônica de 'a incerteza importa?' no corpus, e por isso a ausência deve ser declarada em 61 e coberta por 11 + 52.

**Diretriz (1) de 06/09/2026.** Sem novos experimentos: esta candidata está **DESCARTADA** (permanece no catálogo como registro; é citada em 61 como limitação).

**Score (0–10): 0.** **Justificativa.** DESCARTADA pela diretriz (1) de 06/09 (sem novos experimentos): o contrafactual σ = 0 online exige rodar variantes dos 13 algoritmos. C: 10/72 fazem exatamente isso (b14, b15, b8, b9, c141, c149, c81, e104, e86, jin3) — é a convenção do corpus para 'a incerteza importa?', o que torna a ausência uma limitação declarada (61), coberta por 11 (b5) e 52 (quase-gêmeos). Fica no catálogo como registro; não entra.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 6 artigos / 6 análises** — dos 38 iniciais: 1 · dos 7 do roster minerados agora: 1 · dos 27 complementares: 4 · artigos do roster (15): 1.

- **c1** (BS-MOBO, 2018): Sec. IV-B-1 — Dentro da mesma discussão da Tabela II, o artigo identifica nomeadamente os casos em que os métodos baseados em GP (BS-MOBO-GP, K-RVEA, MOEA/D-EGO)…
- **c131** (MORBO, 2022): Sec. 5.1 ('Optical design problem'), Fig. 3 (centro) — Curva de HV medio x ate 10.000 avaliacoes (lote q=50, 250 pontos iniciais) no problema de design otico AR/VR (d=146, eficiencia x qualidade de…
- **c149** (LBN-MOBO, 2023; roster): Sec. C.6.2, Fig. 18 — Compara LBN-MOBO com NSGA-II e DGEMO no problema real de aerofólio (GAN 5D + CFD OpenFOAM, lote 15.000): evolução do HV, fronteira final e regret…
- **e1** (EMO, 2014): Sec. 4.3, Table 2 — Tabela principal (Table 2): comparação problema × orçamento × algoritmo entre as 14 configurações do EMO (EIeuclid, EIeuclid^gauss, EIhv [só em…
- **e3** (HeE-MOEA, 2019): Sec. V-F, Table III (linha NSGA-II) — Dentro da Table III (HV, média±dp, critério ExI, DTLZ1-7, N=10/20/40/80), a linha que compara HeE-MOEA contra o piso NSGA-II SEM surrogate — o único…
- **jin3** (GS-MOMA / GSM (mono: GS-SOMA), 2010): Sec. IV-C-1, Figs. 15-20 — Para cada um dos 6 problemas MOO, três painéis com Generational Distance (GD), Maximum Spread (MS) e Hypervolume Ratio (HR) por algoritmo (A:NSGA-II,…

**Score (0–10): 9.** **Justificativa.** F-parcial. C: 6/72 nomeiam onde o piso vence (c1 'os métodos de modelo perdem em UF5/UF6', c131, c149, e1, e3, jin3). P alta: 'onde e por que o piso vence' é a leitura com maior valor de contribuição (o corpus a esconde numa linha). V: d19 — o texto lê por algoritmo/família, sem vencedor global. D pronta. Núcleo, ligada a 6/7/18.



### 65. Sensibilidade a hiperparâmetros de projeto do algoritmo (fora do uso da incerteza)

**Fontes.** [MIN] 28 análises em 18 artigos (lista abaixo) · [PL-38] R2#9 (18/38; R1#12 'não recomendada') · [CAP4] tabela de hiperparâmetros (valores fixados nos artigos).

**O que analisa.** O efeito, sobre o endpoint (IGD/HV), de variar um hiperparâmetro do próprio algoritmo que NÃO define o uso da incerteza: tamanho de pool/ensemble (b14 Smax, c48 Q), nº de neurônios/profundidade (b4 H, c122 U/D, e7 J=K), frequência de retreino (b3 wmax, c122 Tmax), nº de gerações de busca no modelo (c241 gmax, e86 t_max), nº de pontos indutores (b15), fração de pareamento (c217 N/4), orçamento do solver interno (b9), η da seleção de subproblemas (e102), itertrain/iterr (e7), K de referência (b4).

**Dados.** Nenhuma camada: exige reexecução com valores alternativos. A ⑤ (manifesto) registra apenas o valor efetivamente usado — insumo da tabela de valores, não da sensibilidade.

**Objetivo.** No corpus: justificar os valores fixados ('confirms that our parameter setting is reasonable' — e102) e mostrar robustez ('relatively insensitive' — b3, c241). Na dissertação: nenhum (diretriz 1).

**O que busca revelar.** Nos artigos: quase sempre saturação ou ótimo intermediário (b14 Smax=5/T=30; c48 Q=40; b4 K≈6; c241 gmax 10–50 'insensível'; e7 'sem orientação teórica para a taxa de dropout') e, com frequência, a escolha final feita por CUSTO e não por qualidade (c241 gmax=10 'to reduce computation time'; e7 J=K=40 'in consideration of the computational time').

**Como é realizada.** Um parâmetro por vez, demais no valor padrão; 1–4 problemas 'representativos'; curvas de IGD × valor (média ou mediana de 20–30 execuções; c122 mediana de 21 nas últimas 100 avaliações; b15 5 sementes); raramente com teste (b15 Wilcoxon p<0,05 para K=3).

**Técnicas.** Varredura unidimensional (one-at-a-time); curvas de perfil; média±dp; ocasionalmente rank médio por valor (c241).

**Implementação.** Não implementável sob a diretriz (1). O que se implementa é a TABELA dos valores usados por algoritmo (⑤ manifesto + cap. 4), com a nota 'valores dos artigos de origem, sem varredura' — em 61.

**Em quantos artigos aparece (dos 72).** 18 artigos (28 análises): dos 38 iniciais 12, dos 7 do roster 2, dos 27 complementares 4; do roster (15): 6. Nas planilhas dos 38 (Ranking 2) o tipo mais próximo está indicado em Fontes.

**Estado.** N — descartada como análise (diretriz 1); vira declaração em 61.

**Demais detalhes.** Relação com 66 (o subconjunto de hiperparâmetros que define o USO da incerteza) e 45 (o que se pode medir sem reexecutar: acionamentos no ⑥). Nota de leitura: em 8 dos 18 artigos a sensibilidade está só no material suplementar (b3, e7, e103, e104, e86, e3, c267, c82) — o corpus a trata como obrigação editorial, não como resultado. Decisão que pede: como declarar no cap. 4/61 que os hiperparâmetros são os dos artigos.

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 18 artigos / 28 análises** — dos 38 iniciais: 12 · dos 7 do roster minerados agora: 2 · dos 27 complementares: 4 · artigos do roster (15): 6.

- **b14** (SA²-MOEA, 2024): Sec. 4.2, Fig. 2 — [nova] Sensibilidade a hiperparâmetros próprios do algoritmo (capacidade do pool de modelos Smax; período de controle de…
- **b15** (U-RankMOEA, 2026): Apendice B.2, Fig. 2 — [nova] Sensibilidade da HV final ao numero de pontos indutores (M_ind) do Deep GP esparso · Apendice E, Table 6 — [nova] Sensibilidade da HV mediana ao tamanho do pool de candidatos na triagem em dois estagios · Apendice F, Fig. 6 — [nova] Sensibilidade da HV e da calibracao (ECE) ao numero de categorias de rank K do classificador · Apendice G.1, Table 9 — [nova] Custo de re-tuning de hiperparametros ao transferir para uma nova tarefa (protocolo de 2 estagios)
- **b3** (K-RVEA, 2018; roster): Sec. IV-B, parágrafo sobre parâmetros adicionais (u e wmax), números no material… — [nova] Sensibilidade ao tamanho do lote de reavaliação (u) no K-RVEA · Sec. IV-B (menção ao estudo); Sec. V Conclusions (achado qualitativo) — [nova] Sensibilidade à frequência de retreino do Kriging (wmax)
- **b4** (CSEA, 2019; roster): Sec. III-B, Fig. 5 — [nova] Sensibilidade ao nº de soluções de referência K (fronteira de classificação) · Sec. IV-D, Table IV — [nova] Sensibilidade ao nº de neurônios ocultos H do FNN
- **b8** (KTA2, 2021): Sec. IV-B, Fig. 8(a) — [nova] Sensibilidade ao parâmetro de amostragem aleatória da estratégia de incerteza (phi) · Sec. IV-B, Fig. 8(b) — [nova] Sensibilidade ao limiar de pontos influentes do modelo substituto (tau)
- **b9** (USeMO, 2020): Sec. 5.1 ("Cheap MO solver") — [nova] Sensibilidade ao orçamento do MO barato interno (nº de avaliações do NSGA-II)
- **c122** (θ-DEA-DP, 2022; roster): Sec. IV-D, Fig. 7 — [nova] Sensibilidade multiparâmetro do surrogate/evolução (U, D, N*, Qmax, Tmax, γ) medida no IGD final
- **c123** (EPBII / EIPBII, 2017): Sec. III-B-6 (Discussion on the arbitrariness of the parameters) — [nova] Discussão qualitativa de sensibilidade a θ_PBI e H (não tabulada)
- **c217** (PC-SAEA, 2023; roster): Sec. 4.1, Fig. 5 — [nova] Sensibilidade dos parâmetros próprios dos algoritmos BASELINE (não de PC-SAEA) · Sec. 4.5, Table 7 — [nova] Sensibilidade à fração de pareamento treino best/worst (N/4 × N/3 × N/2)
- **c241** (EMMOEA, 2023): Sec. III-B, Table I — [nova] Sensibilidade ao nº de gerações da busca no surrogate (gmax)
- **c48** (IBE-CSEA, 2021): Sec. 4.4.2, Fig. 4 — [nova] Sensibilidade do hiperparâmetro de poda do ensemble (Q) medida na acurácia/erro do classificador
- **c97** (EnGP-MRO, 2011): Sec. 6.2 [40] — [nova] Sensibilidade do NSGA-II a tamanho de população e número de gerações
- **e102** (MOEA/D-ASS, 2021): Sec. VI-D, Fig. 9 — [nova] Sensibilidade ao parâmetro η do grau de resolução (solving degree) na seleção de subproblemas
- **e103** (IBEA-MS, 2023; roster): Sec. IV (abertura); Tables S.III e S.IV (material suplementar) — [nova] Robustez a hiperparâmetros do surrogate e ao dataset offline inicial
- **e104** (RVMM, 2022): Sec. IV-A (menção); Figs. S1-S3 (material suplementar, não anexado ao corpus) — [nova] Sensibilidade aos hiperparâmetros k (peso da incerteza na AUCB), Nv (nº de vetores de referência adaptativos) e ωmax…
- **e3** (HeE-MOEA, 2019): Sec. V-E.1; Table I do material suplementar (mencionada, não incluída neste corpus) — [nova] Sensibilidade ao método de agregação das saídas do ensemble
- **e7** (EDN-ARMOEA, 2022; roster): Sec. IV-F.1; Figs. S2-S3 (Supplementary material, ausentes deste corpus — achado descrito… — [nova] Sensibilidade às iterações de treino do surrogate (itertrain, iterr) · Sec. IV-F.2; Fig. S4 (Supplementary material, ausente deste corpus — achado descrito em… — [nova] Sensibilidade ao tamanho da rede (neurônios ocultos J=K) · Sec. IV-F.4; Fig. S6 (Supplementary material, ausente deste corpus — achado descrito em… — [nova] Sensibilidade ao tamanho do lote k de avaliações reais por geração · Sec. IV-F (abertura); ver também Sec. IV-A item 2) ('based on our pilot study given in… — [nova] Estudo piloto de tamanho de população e nº de gerações (P, iter) da AR-MOEA interna
- **e86** (NSGAIII-EHVI, 2023): Sec. IV-A, p. 8 — [nova] Sensibilidade aos hiperparâmetros internos de busca e diversidade (t_max, β)

**Score (0–10): 1.** **Justificativa.** Gate: não reproduzível — exige rodar variantes com hiperparâmetros alternativos (a bateria fixa os valores dos artigos; ⑤ registra só o valor usado). C: 18/72 fazem (R2#9 18/38; 6 do roster: b3 u/wmax, b4 K/H, c122 seis parâmetros, c217, e7 quatro estudos, e103) — é convenção forte, logo a ausência precisa ser declarada em 61 ('hiperparâmetros nos valores dos artigos, sem varredura', com a tabela dos valores). Não entra como análise.


### 66. Sensibilidade ao parâmetro que governa o uso da incerteza (δ do gate, taxa de dropout, k da AUCB, β/ω do LCB) — nos artigos

**Fontes.** [MIN] 3 análises diretas (b8 τ, e104 k/Nv/ωmax, e7 taxa de dropout) + os 15 blocos-roster 'parametros_do_uso_da_incerteza' (Anexo 8.6) · ficha 45 (a versão que a bateria pode fazer: contar acionamentos no ⑥) · [CAP4] tabela de parâmetros.

**O que analisa.** O efeito, sobre o endpoint, de variar o hiperparâmetro que define quanto/quando a incerteza entra na decisão: δ do K-RVEA (b3, fichas 45), δ da confiabilidade do PC-SAEA (c217), taxa de dropout da EDN (e7: 'no theoretic guidance… needs to be properly tuned'), k da AUCB (e104), φ/τ do KTA2 (b8), β do LCB (e64), ω do LB (mtm4), S/p da estimativa de entropia (c154), α/β do termo aleatório (c149).

**Dados.** Sensibilidade fim-a-fim: nenhuma camada (exige reexecução). Tabela de valores: ⑤ (manifesto: sigma_dict, params) + artigos. Acionamentos sob o valor usado: ⑥ (ficha 45).

**Objetivo.** Nos artigos: mostrar que o mecanismo é robusto ou escolher o valor. Na dissertação: documentar, para cada um dos 15, QUAL é o parâmetro que liga a incerteza à decisão e com que valor rodou — a legenda indispensável para ler 45, 52 e 36.

**O que busca revelar.** Nos artigos: e7 admite que o parâmetro central do mecanismo não tem justificativa teórica; b3 relata que aumentar δ 'deteriora a diversidade' porque a incerteza é usada menos vezes; b8 escolhe φ=0,1N (o menor) 'por risco de indivíduos de incerteza muito alta prejudicarem a convergência'; c154 vê ganho nulo de S ou p maiores. Ou seja: a intensidade do uso da incerteza é ajustada empiricamente e, com frequência, para BAIXO.

**Como é realizada.** Varredura do parâmetro em 1–4 problemas, IGD × valor; nos blocos-roster, a listagem nome = valor com localizador.

**Técnicas.** Varredura unidimensional; nos blocos-roster, catalogação (nome do parâmetro, papel, valor, onde está no artigo).

**Implementação.** Tabela 'parâmetros do uso da incerteza dos 15' a partir do Anexo 8.6 cruzada com ⑤ (valores efetivamente usados na bateria); 30 linhas; vai para o cap. 4 (apêndice) e serve de legenda a 45/52.

**Em quantos artigos aparece (dos 72).** 3 artigos (3 análises): dos 38 iniciais 2, dos 7 do roster 0, dos 27 complementares 1; do roster (15): 1. Nas planilhas dos 38 (Ranking 2) o tipo mais próximo está indicado em Fontes.

**Estado.** N — a tabela é factível hoje; a sensibilidade fim-a-fim é descartada (diretriz 1).

**Demais detalhes.** É a ficha que separa 'hiperparâmetro do algoritmo' (65) de 'hiperparâmetro da incerteza' — distinção que o cartão de extração pediu e que os agentes aplicaram (várias análises ficaram em 65 e não em 45 por isso). Relação: 45 (acionamentos), 52 (pares), 36 (por classe de medição). Decisão: onde publicar a tabela (cap. 4 × apêndice).

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 3 artigos / 3 análises** — dos 38 iniciais: 2 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 1 · artigos do roster (15): 1.

- **b8** (KTA2, 2021): Sec. IV-B, Fig. 8(b) — [nova] Sensibilidade ao limiar de pontos influentes do modelo substituto (tau)
- **e104** (RVMM, 2022): Sec. IV-A (menção); Figs. S1-S3 (material suplementar, não anexado ao corpus) — [nova] Sensibilidade aos hiperparâmetros k (peso da incerteza na AUCB), Nv (nº de vetores de referência adaptativos) e ωmax…
- **e7** (EDN-ARMOEA, 2022; roster): Sec. IV-F.3; Fig. S5 (Supplementary material, ausente deste corpus — achado descrito em… — [nova] Sensibilidade à taxa de dropout — parâmetro central do próprio mecanismo de incerteza

**Score (0–10): 4.** **Justificativa.** Gate parcial: a sensibilidade fim-a-fim ao parâmetro do uso da incerteza (δ do gate, taxa de dropout, k da AUCB, β) exige reexecução — não entra. O que entra sem experimento é a TABELA dos parâmetros do uso da incerteza dos 15 (Anexo 8.6, 'parametros_do_uso_da_incerteza', com valores e localizador), casada com ⑤ (manifesto) — útil no cap. 4 (apêndice) e como legenda de 45. C: 3/72 diretos (b8 τ, e104 k, e7 dropout) + os 15 blocos-roster.


### 67. Ablação de componentes do próprio algoritmo que não são a incerteza (otimizador, seleção de subproblemas/lote, arquitetura do modelo)

**Fontes.** [MIN] 21 análises em 14 artigos (lista abaixo) · [PL-38] R2#3 (26/38) · fichas 11/12/15 (ablação do σ) e 52.

**O que analisa.** A contribuição de um componente que não é o σ: otimizador híbrido IBEA/NSGA-II (b14), aprendizado da combinação da aquisição (b15 Static-EHVI), regiões de confiança/aquisição/reinicialização (c131), separação busca/gestão (c241 EMMOEA-IP), seleção de lote e otimizador interno (c261), arquitetura do classificador (c48), componentes da recompensa (c81), transferência (c82), seleção de subproblemas e ALCB (e102), motor de base (e103), indicador × aleatório (e104), EA interno (e16), dados extra/termo SBP (e40).

**Dados.** Nenhuma camada: exige variantes executadas.

**Objetivo.** Nos artigos: mostrar de onde vem o ganho declarado. Na dissertação: leitura literária — quanto do ganho dos métodos vem de componentes que NÃO são a incerteza.

**O que busca revelar.** Resultados fracos ou negativos para a própria contribuição são comuns: e40 (termo SBP só melhora 9/48 e 'quase desaparece' em rc=10; 'highly tricky to measure the search bias'), c241 (expor toda a busca ao EI perde 8/11), c131 (GP global iguala em 2 de 3 problemas a custo 30 h × <1 h), c261 (submodular vs k-means é marginal), c48 (ensemble podado não é monotonicamente melhor), c82 (vantagem 'não universal'). Ver Anexo 8.3.

**Como é realizada.** Variante com um componente removido/trocado, demais fixos; IGD/HV com Wilcoxon (+/=/−) ou média±EP; 3–16 problemas.

**Técnicas.** Ablação one-component-out; Wilcoxon rank-sum α=0,05 (b14, c241 Bonferroni, c261, e40 Holm); curvas (c131).

**Implementação.** Não implementável (diretriz 1). Uso: parágrafo do cap. 6 / 61 sobre o que a bateria não separa (o motor casado por D25 é o máximo de controle disponível: 9).

**Em quantos artigos aparece (dos 72).** 14 artigos (21 análises): dos 38 iniciais 9, dos 7 do roster 0, dos 27 complementares 5; do roster (15): 1. Nas planilhas dos 38 (Ranking 2) o tipo mais próximo está indicado em Fontes.

**Estado.** N — descartada como análise.

**Demais detalhes.** Diferença para 11/15: aqui ambas as variantes usam σ (o que muda não é a incerteza). Diferença para 68: aqui o tipo de surrogate é o mesmo. Relação: 9 (o casamento por motor é a nossa 'ablação' de motor), 51.

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 14 artigos / 21 análises** — dos 38 iniciais: 9 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 5 · artigos do roster (15): 1.

- **b14** (SA²-MOEA, 2024): Sec. 4.4, Table 3 — [nova] Ablação do otimizador híbrido (alternância de seleção ambiental IBEA/NSGA-II por paridade de geração) · Sec. 4.5, Table 4 — [nova] Ablação da amostragem de preenchimento adaptativa por estágio (early-only / late-only / sem controle de probabilidade)
- **b15** (U-RankMOEA, 2026): Apendice L.6, Table 12 e Fig. 9 — [nova] Aquisicao aprendida on-line x combinacao linear fixa (Static-EHVI) sobre as mesmas features
- **c1** (BS-MOBO, 2018): Sec. IV-A-2 (texto corrido, após a discussão da Table I) — [nova] Algoritmo híbrido por ensemble simples (GP+BNN) para pequena e grande escala
- **c131** (MORBO, 2022): Sec. 5.2 ('Ablation study'), Fig. 4 — [nova] Ablacao dos componentes de busca do proprio algoritmo (n. de regioes de confianca, tolerancia a falha, compartilhamento…
- **c241** (EMMOEA, 2023): Sec. III-C, Table II — [nova] Ablação da separação busca-de-candidatos/gestão-do-surrogate (EMMOEA × EMMOEA-IP) · Sec. III-D, Table III — [nova] Ablação do indicador de desempenho próprio vs. matriz EIM (EMMOEA × EMMOEA-EIM)
- **c261** (DirHV-EGO, 2024): Supplementary Sec. III-B.1, p.6-7, Table I (Supplementary) — [nova] Ablação da estratégia de seleção de lote (submodular-greedy × aleatória × k-means) · Supplementary Sec. III-B.2, p.7, Table II (Supplementary) — [nova] Ablação do otimizador interno usado para maximizar a EI (MOEA/D-GR × MOEA/D-DE) · Supplementary Sec. IV-A/IV-B, p.9-10, Table IV (Supplementary) + Fig. 8 (Supplementary) — [nova] Ablação da estratégia adaptativa do ponto de referência z* + comparação pareada sob seleção k-means comum
- **c48** (IBE-CSEA, 2021): Sec. 4.2, Table 1 — [nova] Ablação da arquitetura do classificador substituto (modelo único × ensemble completo × ensemble podado)
- **c81** (UA-MORL-Diff, 2025): Appendix B.6; Table 2 (linhas 'Ours W/O') — [nova] Ablação dos componentes auxiliares da recompensa (reward boost, penalidade de diversidade, corte dinâmico)
- **c82** (TC-SAEA, 2022): Sec. 4.5 (Ablation Studies), Tables 4 e 5 — [nova] Ablação do esquema de transferência como um todo (dois GPs independentes, sem co-surrogate nem seleção)
- **e102** (MOEA/D-ASS, 2021): Sec. VI-A, Table IX e Table X (Supplemental File — não incluídas neste corpus) — [nova] Ablação da estratégia de seleção de subproblemas (ASS vs. seleção aleatória) · Sec. VI-C, Table IX (Supplemental File — não incluída neste corpus) — [nova] Ablação da função de aquisição (ALCB de γ adaptativo vs. LCB de γ fixo)
- **e103** (IBEA-MS, 2023; roster): Sec. IV (abertura); Table S.II (material suplementar) — [nova] Escolha do motor evolutivo de base para o framework offline (piloto)
- **e104** (RVMM, 2022): Sec. IV-G; Tables SIV-SV (material suplementar, não visível no corpus) — [nova] Ablação da amostragem por indicador de desempenho vs. amostragem aleatória (RVMM-RI)
- **e16** (EGBO, 2024): Sec. Further discussion; Supplementary Discussion subsection 2.2 (não presente neste… — [nova] Ablação do componente evolutivo interno do híbrido assistido (troca de EA e do otimizador de aquisição)
- **e40** (SBP-BO, 2023): Sec. IV-B-4 (Ablation studies), Table VI, p.12-13; mencao a Table SVI (Supplementary… — [nova] Ablacao da estrategia de selecao de dados extras do ensemble (completo vs. clustering vs. amostra aleatoria) · Sec. IV-B-4, Table VI (coluna 'BO-NoGP_c'), p.12-13; mencao a Table SVI (Supplementary… — [nova] Ablacao do surrogate nos objetivos baratos (modelo vs. avaliacao instantanea/ilimitada) · Sec. IV-B-4, Table VI (coluna 'BO-AAF'), p.12-13; mencao a Table SVI (Supplementary… — [nova] Ablacao do termo de penalizacao de vies de busca (SBP)

**Score (0–10): 1.** **Justificativa.** Gate: não reproduzível — ablação de componentes não-σ (otimizador híbrido, seleção de subproblemas, seleção de lote, arquitetura do classificador) exige variantes. C: 14/72 (R2#3) — é a convenção 'ablation study' do corpus. Registro para 61; o único uso é literário (o corpus mostra que boa parte do ganho declarado vem de componentes que não são a incerteza — c261, e40 'termo SBP só melhora 9/48', c241).


### 68. Tipo de surrogate sob a mesma maquinaria (GP × NN × RBF × ensemble; independente × dependente; heterogêneo × homogêneo)

**Fontes.** [MIN] 20 análises em 11 artigos (lista abaixo) · fichas 20 (taxonomia como variável) e 36 (sonda por classe de medição) · [CAP3] eixo surrogate (GP/RG/NN/CL).

**O que analisa.** O efeito de trocar o tipo de modelo mantendo o resto: BNN × GP por escala (c1: GP vence em 8D/poucos dados; BNN vence em 50D/1000 pontos), par-a-par × regressão × classificação (c217: 0/18/0 e 0/12/6, com tempos 1118 s × 1627 s × 245 s), heterogêneo × homogêneo (e3: HoE nunca vence), CoMOGP × GPs independentes (e102), GP dependente × independente (c106: 'little advantage' — negativo), LMC × independente (b15: LMC piora), Deep GP hetero × GP esparso × GP raso (b15), DNN × XGBoost por validação (b13), kernels por CV (c50), co-surrogate GP × polinomial (c82), arquiteturas por acurácia e correlação de erros (e8), surrogates por lote (c149).

**Dados.** Nenhuma camada para a ablação. Entre algoritmos, ① + ③ dão a leitura confundida por classe de surrogate (20/36).

**Objetivo.** Nos artigos: escolher/justificar o modelo. Na dissertação: contexto para ler o eixo surrogate da taxonomia com humildade (a bateria varia surrogate E motor E função ao mesmo tempo).

**O que busca revelar.** Dois achados transversais úteis ao texto: (i) o regime (orçamento/dimensão) decide o modelo — c1 inverte o vencedor entre 8D e 50D; (ii) modelar correlação entre objetivos raramente compensa sob poucos dados — c106 e b15 negativos, c81 mede |ρ|<0,3 e assume independência (ficha 80).

**Como é realizada.** Mesmo algoritmo com o modelo trocado; IGD/HV; às vezes só acurácia do modelo (b13, c50, e8).

**Técnicas.** Ablação de modelo; validação cruzada k-fold; comparação de MAE/RMSE por partição (treino/teste/extrapolação — e8).

**Implementação.** Não implementável como ablação. A leitura por eixo de surrogate (20) e a sonda por classe de medição (36) são as versões pós-hoc.

**Em quantos artigos aparece (dos 72).** 11 artigos (20 análises): dos 38 iniciais 6, dos 7 do roster 2, dos 27 complementares 3; do roster (15): 2. Nas planilhas dos 38 (Ranking 2) o tipo mais próximo está indicado em Fontes.

**Estado.** N — descartada como análise; alimenta 20/36/61 e o cap. 6.

**Demais detalhes.** Relação com 37 (agregação de m sigmas) e 80 (correlação entre objetivos). Nota: c217 reporta que 'o treino dos surrogates consome <10% do runtime' — dado de custo para 48.

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 11 artigos / 20 análises** — dos 38 iniciais: 6 · dos 7 do roster minerados agora: 2 · dos 27 complementares: 3 · artigos do roster (15): 2.

- **b13** (AdaMoR-DDMOEA, 2025): Sec. 5.1, Tables 2 e 3 — [nova] Comparação treino × validação (k-fold CV) entre dois candidatos a surrogate (diagnóstico de overfitting)
- **b15** (U-RankMOEA, 2026): Apendice E.1, Table 7 — [nova] Ablacao da estrutura do surrogate: Deep GP heterocedastico x GP esparso homocedastico x GP raso RBF · Apendice G, Table 8 e Fig. 7 — [nova] GP independente por objetivo x GP com correlacao entre objetivos (coregionalizacao linear)
- **c1** (BS-MOBO, 2018): Sec. IV-A-2 — [nova] Ablação do tipo de surrogate (BNN vs GP) sob poucos dados/baixa dimensão · Sec. IV-A-3 — [nova] Ablação da informação de gradiente (Sobolev training) sobre o surrogate, pequena escala · Sec. IV-B-2 — [nova] Ablação do tipo de surrogate (BNN vs GP) sob muitos dados/alta dimensão — escalabilidade · Sec. IV-B-3 — [nova] Ablação da informação de gradiente (Sobolev training) sobre o surrogate, alta dimensão
- **c106** (EMMI (EMmI), 2016): Sec. 6.1, p. 17; Sec. 6.2, p. 18-19; Sec. 7 (Conclusions and Discussion), p. 19-20 — [nova] Ablacao da estrutura de covariancia do GP multiobjetivo (independente x dependencia nao-separavel) · Sec. 6.1, p. 17 — [nova] Ablacao da estrutura de covariancia do GP multiobjetivo (independente x dependencia nao-separavel)
- **c149** (LBN-MOBO, 2023; roster): Sec. 3, Fig. 1 — [nova] Curva de escalabilidade por tamanho de lote (batch size): HV e tempo em função de S · Sec. 5.1, Fig. 3 — [nova] Curva de escalabilidade por tamanho de lote (batch size): HV e tempo em função de S · Sec. C.3, Fig. 13 — [nova] Curva de escalabilidade por tamanho de lote (batch size): HV e tempo em função de S
- **c217** (PC-SAEA, 2023; roster): Sec. 4.4, Table 6 — [nova] Ablação do tipo de surrogate dentro do mesmo framework (regressão × classificação × comparação par-a-par)
- **c50** (PD-MOEA, 2018): Sec. 3, p.8 (antes da Eq. 4) — [nova] Seleção de kernel do GP por validação cruzada
- **c82** (TC-SAEA, 2022): Sec. 4.5, Tables 4 e 5 — [nova] Ablação do tipo de modelo do co-surrogate (GP vs. regressão polinomial)
- **e102** (MOEA/D-ASS, 2021): Sec. VI-B, Table IX (Supplemental File — não incluída neste corpus) — [nova] Ablação do modelo colaborativo (CoMOGP) vs. GPs independentes por subproblema
- **e3** (HeE-MOEA, 2019): Sec. V-F, Table III (linha HoE-MOEA) — [nova] Heterogêneo × homogêneo — ablação do mecanismo de diversidade do ensemble
- **e8** (NN-EGO, 2020): Table S3 (S12); Figure S6 (S13) — [nova] Comparação de arquiteturas de surrogate por acurácia (μ) · Table S4 (S13) — [nova] Correlação de erro entre arquiteturas de modelo (teste) · Table S5 (S15) — [nova] Correlação de erro entre arquiteturas de modelo (extrapolação)

**Score (0–10): 2.** **Justificativa.** Gate: não reproduzível como ablação (trocar GP por NN/RBF sob a mesma maquinaria exige rodar). C: 11/72 (c1 GP×BNN por escala — a inversão em 50D é resultado clássico; c217 par-a-par × regressão × classificação; e3 heterogêneo × homogêneo; e102; e8; b15 hetero × homo; c106 GP dependente × independente NEGATIVO). O que a bateria oferece é a leitura por eixo de surrogate entre algoritmos (20/36), confundida. Registro; alimenta o cap. 6 (trabalhos futuros) e 61.


### 79. O front por nível de confiança — filtrar o ND acreditado pelo σ e reavaliar (regime offline)

**Fontes.** [MIN] 4 análises em 2 artigos (c49: preferência + tolerância de incerteza do DM sobre 1,96σ; c97: fronteiras por confiabilidade 0,99/0,8/0,66/0,5 e por tamanho do ensemble) · fichas 13/14/42 · [CD] ③ + ⑦.

**O que analisa.** No offline, a incerteza é a única defesa contra o modelo: o front 'acreditado' filtrado por quantil de σ (só soluções com σ baixo) e reavaliado na verdade (⑦) — c97 mostra que ensembles pequenos subestimam σ e produzem fronteiras 'aparentemente melhores' mas infactíveis; c49 aplica tolerâncias do DM e fica com poucas soluções.

**Dados.** ③ (σ das soluções do ND final, regime busca) para b5 (Prob-RVEA/MOEA/D) e e103; ⑦ (reavaliação); ① (dataset).

**Objetivo.** Mostrar se o σ do modelo offline separa as soluções que sobrevivem à reavaliação das que não sobrevivem — a versão 'de decisão' de 33/34 no offline.

**O que busca revelar.** Se 'confiar menos' (filtrar por σ) compra fidelidade ao custo de cobertura: HV reavaliado × nível de confiança; e se o b5m (que usa σ na seleção) chega a um ND mais confiável que o moead_media (11).

**Como é realizada.** Para cada célula offline: ordenar o ND final por σ (médio entre objetivos — ver 37); para quantis 100/75/50/25%: HV acreditado (μ) e HV reavaliado (⑦) do subconjunto; curva HV_real × quantil, com o moead_media como controle (sem σ).

**Técnicas.** Filtragem por quantil de σ; HV com referência D69; curva por confiança; comparação pareada por semente.

**Implementação.** Sobre ③ + ⑦ das 5 configs offline (b5m, b5r, e103, treed_media?, moead_media): join por solution_id; ~1 célula.

**Em quantos artigos aparece (dos 72).** 2 artigos (4 análises): dos 38 iniciais 2, dos 7 do roster 0, dos 27 complementares 0; do roster (15): 0. Nas planilhas dos 38 (Ranking 2) o tipo mais próximo está indicado em Fontes.

**Estado.** N — dado pronto se ③ do offline gravar σ por solução do ND (conferir); custo baixo.

**Demais detalhes.** Relação: 11, 13, 14, 33, 42. Caveat: e103 (IBEA-MS) usa classe/ordem, não σ contínuo — só b5 e treed. Decisão: entra no bloco offline como figura.

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 2 artigos / 4 análises** — dos 38 iniciais: 2 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 0 · artigos do roster (15): 0.

- **c49** (Interactive Offline DD-MOEA Framework (sigla não-oficial, proposta por mim), 2020): Sec. 3.1, Fig. 2 e Fig. 3(a)-(b) — [nova] Ilustração da 1ª etapa de pré-filtragem por hipercone (preferência de objetivo) · Sec. 3.1, Fig. 3(b)-(c) — [nova] Ilustração da 2ª etapa de pré-filtragem por ordenação não-dominada com incerteza
- **c97** (EnGP-MRO, 2011): Sec. 6.3 [42]-[44], Figs. 11, 12, 13, 14; equivalência MRO≈CC em Sec. 6.4 [47] — [nova] Fronteiras de Pareto por nível de confiabilidade (múltiplas realizações × chance-constrained) · Sec. 6.4 [48], Fig. 18 — [nova] Sensibilidade da fronteira de Pareto ao número de membros do ensemble (5/10/15/30)

**Score (0–10): 6.** **Justificativa.** Reproduzível no offline (b5, e103) com ③ + ⑦: filtrar o ND acreditado por quantil de σ e reavaliar — 'o front por nível de confiança'. C: 2/72 (c49 tolerância do DM sobre 1,96σ; c97 fronteiras por confiabilidade 0,99/0,8/0,66/0,5 — ensembles pequenos subestimam a incerteza e produzem fronteiras infactíveis). P alta no offline (a incerteza como filtro de decisão, não só de busca) e original. Entra como figura de 13/42 se ③ do offline tiver σ por ponto do ND.

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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 1 artigos / 1 análises** — dos 38 iniciais: 1 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 0 · artigos do roster (15): 0.

- **c82** (TC-SAEA, 2022): Sec. 4.6 (Impact of the Correlation between Objectives), Table 6 — Usa o problema sintético cm-OneMax, cuja correlação entre objetivos é controlável por um parâmetro corr ∈ {−1, −0,75, −0,5, −0,25, 0, 0,25, 0,5,…

**Complementos e correções (06/09/2026).** A análise por característica no corpus é majoritariamente PROSA: 283 afirmações minadas (Anexo 8.5), p.ex. c1 ('BS-MOBO-GP perde em UF5/UF6, frente desconexa e muitos ótimos locais'), c241, e40 (frente-curva DTLZ5), e102 (PF irregular ZDT3/ZDT6), c82 (correlação entre objetivos controlável). Isso é o contraste literário para 17–19.

**Score (0–10): 8.** **Justificativa.** F-parcial (piloto). C: 1/72 como rank por característica (c82, correlação controlável), mas o corpus faz a leitura por característica em PROSA: 283 afirmações 'característica × desempenho' minadas nos 72 (Anexo 8.5) — multimodalidade, frente desconexa, degenerada, muitos objetivos, alta dimensão. P alta (lei da §4.1; DIR-14). D: pede a matriz canônica (D98, decisão 5). Entra como a tabela-síntese do bloco C; as 283 afirmações são o contraste literário para 19.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 6 artigos / 10 análises** — dos 38 iniciais: 4 · dos 7 do roster minerados agora: 2 · dos 27 complementares: 0 · artigos do roster (15): 5.

- **c122** (θ-DEA-DP, 2022; roster): Sec. IV-C (texto entre Table VI e Fig. 6) — Discussão textual (não uma tabela/figura isolada, mas comentário comparativo cruzando as Tabelas IV/V/VI) sobre como a relação competitiva entre…
- **c141** (MMRAEA, 2025; roster): Sec. Effectiveness of multi-mode RBFs, Table 2 — Ablação do mecanismo tri-modo de RBFs: MMRAEA completo (seleciona por nondominated sorting de Q=soma dos 3 ranks de qualidade, mais U=soma das… · Sec. Effectiveness of bi-population based on CSO and GA, Table 3 — Ablação do motor de busca bi-populacional: MMRAEA completo (população final Ptot = P1∪P2, buscada em paralelo por CSO e por GA) é comparado a… · Sec. Main comparison, Table 4 — Tabela de comparação final entre MMRAEA e quatro SAEAs do estado da arte (CPS-MOEA, MOEA/D-RBF, EDN-ARMOEA, MCEA/D) em 48 instâncias (DTLZ1-7 3-obj +… · Sec. Main comparison, Table 5 — Mesma estrutura da Table 4, agora nos 36 instâncias do WFG1-9 (3-obj) × d=20,40,60,100 — segunda suíte da comparação principal.
- **c154** (JES, 2022; roster): Apêndice L.4, Figs. 17, 18 — No problema ZDT2 (D=6, M=2), com a recomendação obtida por argmax da média posterior, varia o nível de ruído de observação gaussiano injetado…
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF), 2021; roster): Apendice H.5; Fig. 7, Fig. 8 — Desempenho sequencial (hipervolume e log HV diff) no DTLZ2 biobjetivo com ruido fixo (sigma=5%), variando a dimensao de entrada d em {5,10,15,20},… · Apendice H.6, Fig. 14 — Desempenho sequencial no DTLZ2 (d=6, M=2) sob niveis de ruido crescentes (sigma = 1%, 2%, 3%, 4%, 5%, 10%, 15%, 20% do range de cada objetivo;…
- **c82** (TC-SAEA, 2022): Sec. 4.6 (Impact of the Correlation between Objectives), Table 6 — Usa o problema sintético cm-OneMax, cuja correlação entre objetivos é controlável por um parâmetro corr ∈ {−1, −0,75, −0,5, −0,25, 0, 0,25, 0,5,…
- **e103** (IBEA-MS, 2023; roster): Sec. IV-B, Fig. 7; Tables S.IX–S.XI (material suplementar) — Estudo de escalabilidade com a dimensão de decisão D (10→20→30) para IBEA-MS vs. as 3 variantes AK-IBEA (Tables S.IX-S.XI, mencionadas) mais um caso…

**Complementos e correções (06/09/2026).** Degraus no corpus: c122 (M = 3→5→8), c141/e74 (D = 20→100/200), c154 e c262 (ruído crescente — fora do recorte), e103 (D = 10→30), c82 (τ = 5→10; correlação −1→+1), e40 (r e rthres). A convenção é escalar M, D ou ruído; escalar a CARACTERÍSTICA (multimodal, desconexa…) com a régua por família é próprio da tese.

**Score (0–10): 8.** **Justificativa.** N. C: 6/72 (c122 'muitos objetivos', c141, c154 ruído, c262 D e ruído, c82, e103 D) fazem 'degraus' de dificuldade (escalonando M, D ou ruído). P alta. V: cap. 4 l.117 promete o 'degrau de falha' ao cap. 5 — vinculante. D: pronta (é 7 + 6 reorganizadas por classe). Entra como a tabela 'em que degrau cada classe deixa de funcionar'.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 0 artigos.** Nenhuma análise dos 72 foi mapeada a esta ficha — leitura própria da tese (ou regra/nota), sem correspondente nomeado no corpus.

**Score (0–10): 9.** **Justificativa.** N (síntese). C: 0/72 como estrutura; mas as 283 afirmações característica × desempenho do corpus (Anexo 8.5) são exatamente o que as seis perguntas confrontam. V: cap. 4 l.102 promete as seis perguntas ao cap. 5 — vinculante; é a espinha narrativa que casa resultado (17/18) com mecanismo (33/36/45). D: sem cômputo próprio (usa as outras fichas). Recomendo como estrutura de seção (uma subseção por pergunta), não como análise nova; decisão 14.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 0 artigos.** Nenhuma análise dos 72 foi mapeada a esta ficha — leitura própria da tese (ou regra/nota), sem correspondente nomeado no corpus.

**Score (0–10): 6.** **Justificativa.** N. C: 0/72 (o corpus não agrega por classe — cada artigo defende uma classe). P alta em tese (a taxonomia como variável é a contribuição do cap. 3), D barata (group-by), mas com confundimento forte: classes com 1–3 algoritmos, motores diferentes, e a ressalva do d19. Entra como leitura descritiva com aviso explícito (ou apêndice); a ficha 36 (sonda por classe de medição) é a versão com mecanismo, mais defensável.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 0 artigos.** Nenhuma análise dos 72 foi mapeada a esta ficha — leitura própria da tese (ou regra/nota), sem correspondente nomeado no corpus.

**Score (0–10): 5.** **Justificativa.** N. C: 0/72. Redundante com 20 e com a §3.8 (cobertura 7/7 é fato do cap. 3, não resultado do cap. 5). D barata. Entra no máximo como frase de abertura do bloco C; não como análise.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 0 artigos.** Nenhuma análise dos 72 foi mapeada a esta ficha — leitura própria da tese (ou regra/nota), sem correspondente nomeado no corpus.

**Score (0–10): 7.** **Justificativa.** T. C: 0/72 como transferência formal (o corpus faz o caso real como capítulo à parte: 16/72, ficha 23/75). P alta: 'o sintético prediz o real?' é pergunta que a banca fará; D barata (Spearman entre rankings sintético × real, por real). Cautela: n = 3 reais e DDMOP7 só HV. Entra como parágrafo com tabela pequena dentro de 23.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 14 artigos / 24 análises** — dos 38 iniciais: 6 · dos 7 do roster minerados agora: 4 · dos 27 complementares: 4 · artigos do roster (15): 4.

- **b13** (AdaMoR-DDMOEA, 2025): Sec. 5.6, Table 6, Figures 7–8 — Estudo de caso real: otimização de forma de aerofólio transônico RAE 2822 (offline; 10 variáveis de decisão via parametrização CST — 5 parâmetros da… · Sec. 5.6, Figures 9–10 — Comparação, em gráficos de barras empilhadas (stacked charts), dos valores brutos de CL e CD (não do IGD) para pontos de Pareto obtidos pelo…
- **b15** (U-RankMOEA, 2026): Sec. 4.5, Fig. 12 — Estudo de caso real proprio do artigo: otimizacao de extracao de calor num reservatorio geotermico fraturado, 160 variaveis de decisao (taxas de…
- **c1** (BS-MOBO, 2018): Sec. IV-D, Fig. 7 — Estudo de caso do problema real Rosetta (trajetória espacial, biobjetivo, D=22, gradiente disponível): evolução do hipervolume mediano (10 execuções…
- **c10** (SP-RV-MOEANet, 2021): Table III; Fig. 5; Sec. Experiments on real-world networks — Tabela e figura com o desempenho (HV médio ± dp, teste de Wilcoxon vs. SP-RV-MOEANet, e tempo de execução) dos 5 algoritmos em duas redes reais — a… · Eqn. (5); Fig. 5; Fig. S4 (Supplementary Materials, só mencionada); Sec. Experiments on… — [nova] Custo estrutural de edição (distância média entre nós) para seleção de solução final na frente · Sec. Experiments on synthetic networks (após a discussão de Fig. 3); Supplementary… — [nova] Sensibilidade ao tipo de remoção nos ataques nodais (aleatória vs. betweenness) (material suplementar)
- **c107** (MS-VHGP-EIHV, 2017): Sec. IV, Figs. 25-26 — Estudo de caso no robô-cobra físico real (sidewinding gait): compara as frentes de Pareto (velocidade x estabilidade de cabeça) obtidas pelo método…
- **c131** (MORBO, 2022): Sec. 5.1 ('Trajectory Planning'), Fig. 3 (esquerda) — Curva de Hypervolume medio x ate 2.000 avaliacoes reais (lote q=50, 200 pontos iniciais) no problema de planejamento de trajetoria (d=60, 2 objetivos… · Sec. 5.1 ('Optical design problem'), Fig. 3 (centro) — Curva de HV medio x ate 10.000 avaliacoes (lote q=50, 250 pontos iniciais) no problema de design otico AR/VR (d=146, eficiencia x qualidade de… · Sec. 5.1 ('Mazda vehicle design problem'), Fig. 3 (direita) — Curva de HV medio x ate 10.000 avaliacoes (lote q=50, 300 pontos iniciais) no problema veicular Mazda (d=222, 2 objetivos, 54 restricoes black-box de…
- **c141** (MMRAEA, 2025; roster): Sec. Results and discussions (BWBUG), Table 8 — Tabela final de IGD e HV para os 5 algoritmos no caso real BWBUG (43D, 2 objetivos: peso W e tensão equivalente máxima σmax), com referência de IGD =…
- **c149** (LBN-MOBO, 2023; roster): Sec. 5.3, Fig. 4 — Aplica LBN-MOBO com dois surrogates (Deep Ensembles vs. MC Dropout) a dois problemas reais próprios do artigo: aerofólio (Cl, Cl/Cd, via GAN 5D + CFD… · Sec. C.6.1, Fig. 17 — Compara LBN-MOBO com NSGA-II (piso evolutivo, lote 20.000) e DGEMO (lote limitado a 1.000, 5 iterações) no gamut de 44 tintas: evolução do HV e gamut… · Sec. C.6.2, Fig. 18 — Compara LBN-MOBO com NSGA-II e DGEMO no problema real de aerofólio (GAN 5D + CFD OpenFOAM, lote 15.000): evolução do HV, fronteira final e regret… · Sec. C.7, Fig. 19 — Repete a comparação (LBN-MOBO, NSGA-II, DGEMO, Random) no gamut de 8 tintas (espaço de design menor que o de 44 tintas), evolução do HV e gamut…
- **c238** (EIM, 2017; roster): Sec. VIII, Figs. 18-20, Appendix B — Estende os três critérios EIM multiplicando-os pela probabilidade de factibilidade (PoF) de cada restrição (uma Kriging por restrição), formando os…
- **e16** (EGBO, 2024): Sec. Self-driving lab for AgNP experimental campaign, Fig. 3a,b — No único run de cada otimizador na plataforma SDL real de síntese de AgNP (5D de decisão, 3 objetivos, 2 restrições, 15 iterações, lote q=4), o…
- **e17** (MOBO, 2021): Sec. III-C, Fig. 4 — [nova] Restricao de desigualdade probabilistica (gate via posterior de GP) num problema de brinquedo · Sec. IV-B, Fig. 8 — [nova] Preferencia (subdominio truncado) vs. restricao probabilistica vs. irrestrito no problema real AWA
- **e81** (qPOTS, 2025; roster): Sec. 4.2, Fig. 7 (painel direito) — No caso real do CRM (d=24, K=2), curva de HV ao longo das iterações comparando qPOTS contra qNEHVI ('EHVI'), qPAREGO ('ParEGO') e Sobol, numa única…
- **pp6** (AB-MOEA, 2020): Sec. 5, Table 7 — Estudo de caso em um problema real de engenharia (projeto de aerofólio RAE2822 via simulação CFD, 2 objetivos: arrasto e sustentação, orçamento de… · Sec. 5, Fig. 6 — Visualização do conjunto não-dominado obtido por cada um dos 3 algoritmos (AB-MOEA, BO, K-RVEA) no problema real do aerofólio, no espaço de objetivos…
- **wang4** (SA-NSGA-II, 2016): Sec. V-D, Fig. 17 e Fig. 18 — Plota o conjunto não-dominado da execução com IGD MEDIANO (dentre as 20 de 1h) para as três configurações da Table III (Fig. 17), e detalha sobre um…

**Complementos e correções (06/09/2026).** Roster com caso real: c141 (BWBUG 43D), c149 (aerofólio GAN+CFD; gamut de impressora), c238 (restrições PoF), e81 (CRM d = 24), b3 (polimerização — só no suplemento), e7 (destilação — só no suplemento), e74 (geotérmico). Convenção: HV (frente verdadeira desconhecida), 1–5 execuções, interpretação de engenharia (ficha 75).

**Score (0–10): 8.** **Justificativa.** F-parcial. C: 14/72 fazem o caso real (R2#6 20/38; roster: c141 BWBUG, c149, c238, e81 CRM) + 16/72 interpretam as soluções (75). P alta: RE21/ESTOQUE40/DDMOP7 são os únicos lugares onde 'a incerteza ajuda' pode virar 'ajudou aqui'. D pronta (endpoint) mas o texto por caso é caro. V: C14 (DDMOP7 asterisco + inferencial por classe), 12. Entra como seção curta (um caso nomeado por parágrafo).


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 0 artigos.** Nenhuma análise dos 72 foi mapeada a esta ficha — leitura própria da tese (ou regra/nota), sem correspondente nomeado no corpus.

**Score (0–10): 5.** **Justificativa.** N. C: 0/72. P média: 'que aquisição acha as redes esparsas boas' é interessante mas o DDMOP7 é HV-only, sem sonda (S), com zona morta τ=0,5 e FE redundante (50) — três ressalvas para uma pergunta. Entra no máximo como parágrafo em 23; não como análise própria.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 0 artigos.** Nenhuma análise dos 72 foi mapeada a esta ficha — leitura própria da tese (ou regra/nota), sem correspondente nomeado no corpus.

**Score (0–10): 5.** **Justificativa.** N. C: 0/72 (nenhum artigo do corpus usa IGDX/PSP; os MMF só aparecem na nossa bateria). P: mede o espaço de decisão nos 4 MMF — pertinente à característica 'multimodal' (18/19) mas exige métrica nova, front de decisão de referência e só 4 problemas. Decisão 6. Recomendo apêndice ou cair; a característica 'multimodal' já é lida por IGD+ em 18.



### 75. Interpretação de engenharia/decisão das soluções não-dominadas nos problemas reais

**Fontes.** [MIN] 29 análises em 16 artigos (lista abaixo) · [PL-38] R2#6 (20/38) · ficha 23 (os três reais) · ficha 24 (DDMOP7).

**O que analisa.** O que as soluções da frente SÃO no domínio: diagramas de tensão (c141 BWBUG), Cp/geometria da asa (e81, c59), campo de escoamento (c91), segmentos da frente × poços/barreiras (e64), custo estrutural de edição (c10), operating point por probabilidade de dominância (c50), status quo dominado (wang4: 'algumas soluções dominam a configuração real vigente'), validação por docking/MD/FEP (c81), envelope operacional (c91), preferência/tolerância do DM (c49), efeito do ponto de referência (c49).

**Dados.** ① (x e f do ND final por célula); M (semântica das variáveis: RE21 (viga), ESTOQUE40 (política de estoque), DDMOP7 (rede esparsa)); ⑦ no offline.

**Objetivo.** Dar aos três reais uma leitura de decisão (o que muda entre as soluções extremas e a do 'joelho') — e, no DDMOP7, dizer que redes a aquisição achou (24).

**O que busca revelar.** Se as frentes dos assistidos e dos pisos cobrem regiões DIFERENTES do espaço de decisão (não só de objetivos) — e se a incerteza levou a soluções 'estranhas' (fantasia, 40) ou a soluções plausíveis.

**Como é realizada.** Para cada real: 3 soluções do ND mediano (extremos + joelho) por 2–3 algoritmos, tabela x/f e uma frase de interpretação; comparação com a solução de referência do problema, se houver (RE21 tem front empírico D72; ESTOQUE40 tem política-base?).

**Técnicas.** Seleção de soluções representativas (extremos, joelho por distância à reta); tabela; interpretação de domínio.

**Implementação.** Célula pequena por real sobre ①; nenhuma métrica nova.

**Em quantos artigos aparece (dos 72).** 16 artigos (29 análises): dos 38 iniciais 11, dos 7 do roster 3, dos 27 complementares 2; do roster (15): 5. Nas planilhas dos 38 (Ranking 2) o tipo mais próximo está indicado em Fontes.

**Estado.** N — dado pronto; custo de texto.

**Demais detalhes.** A dissertação é metodológica: recomendo no máximo um parágrafo por caso (23). Relação: 22, 23, 24, 54. Decisão: quais casos ganham interpretação.

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 16 artigos / 29 análises** — dos 38 iniciais: 11 · dos 7 do roster minerados agora: 3 · dos 27 complementares: 2 · artigos do roster (15): 5.

- **b3** (K-RVEA, 2018; roster): Sec. IV-B, último parágrafo antes de Sec. V — [nova] Estudo de caso real (polimerização de acetato de vinila, 3 obj.)
- **c10** (SP-RV-MOEANet, 2021): Sec. Experiments on synthetic networks (fim do parágrafo sobre redes SF); Supplementary… — [nova] Análise de desempenho de soluções representativas em redes sintéticas (material suplementar) · Sec. Experiments on real-world networks (após Table III/Fig. 5); Supplementary Materials… — [nova] Análises intuitivas da estrutura das redes reais otimizadas (material suplementar)
- **c141** (MMRAEA, 2025; roster): Sec. Results and discussions (BWBUG), Fig. 14 — [nova] Interpretação de engenharia das soluções ND vs. solução-base (diagramas de tensão equivalente)
- **c49** (Interactive Offline DD-MOEA Framework (sigla não-oficial, proposta por mim), 2020): Sec. 4, Fig. 5(a)-(c) — [nova] Efeito da preferência de objetivo (ponto de referência) entre iterações — estudo de caso GAA · Sec. 4, Fig. 5(d) — [nova] Efeito da tolerância de incerteza do DM sobre o conjunto mostrado — estudo de caso GAA
- **c50** (PD-MOEA, 2018): Sec. 5.1, Fig. 4a, p.16 — [nova] Probabilidade de dominância no espaço de objetivos — mapa (dim. 1) · Sec. 5.1, Fig. 5a-b, Eq. 17, p.17-18 — [nova] Probabilidade de dominância no espaço de objetivos — seleção de operating point (dim. 2) · Sec. 6, Fig. 8, p.22-23 — [nova] Probabilidade de dominância no espaço de objetivos — extensão 3D/carga (dim. 3)
- **c59** (UA-DBO, 2026): Sec. 4.2, Figs. 10-11, p. 18–20 — [nova] Comparação qualitativa da geometria/aerodinâmica da solução otimizada · Appendix C.4.2, Fig. 5, p. 32 — [nova] Comparação qualitativa da geometria/aerodinâmica da solução otimizada
- **c65** (SABBa, 2022): Sec. 6.1, Figs. 11-12 — [nova] Estudo de caso de engenharia RBDO mono-objetivo com refinamento sequencial de acurácia (treliça de 2 barras)
- **c66** (PAL-SAPSO, 2019): Sec. IV-B-2), Fig. 4 — [nova] Caso real dinâmico: reotimização periódica vs. modelo estático (deriva do processo)
- **c81** (UA-MORL-Diff, 2025): Sec. 4.2.2, Fig. 3 — [nova] Distribuições marginais dos objetivos (QED/SAS/afinidade) das moléculas geradas, com vs. sem RL · Sec. 4.2.4, Fig. 4; Appendix C.6 — [nova] Validação real de candidatos via docking + MD + perfil ADMET contra inibidor conhecido de EGFR · Appendix C.5, Table C.5 — [nova] Validação da afinidade de ligação via Free Energy Perturbation (FEP) para os 3 candidatos selecionados · Appendix C.3, Table C.4 — [nova] Generalização a dois novos grupos de propriedades quânticas reais no QM9 (HOMO-LUMO / dipolo-Cv-polarizabilidade) · Appendix C.8, Table C.6 — [nova] Generalização do framework a outras arquiteturas de difusão (GeoLDM, GFMDiff) · Appendix C.7, Fig. C.3 — [nova] Galeria dos 8 melhores candidatos moleculares gerados por dataset, selecionados por score composto de incerteza
- **c91** (EHVIMOPSO, 2019): Sec. 4.4, Fig. 17, Table 6 — [nova] Caso real de engenharia com aplicação única do método (sem baseline algorítmico nem frente verdadeira conhecida) · Sec. 4.4, Figs. 18-21 — [nova] Validacao fisica qualitativa do design via campo de escoamento (ondas de choque, contornos de pressao) · Sec. 4.4, Figs. 22-23 — [nova] Curvas de desempenho ao longo de uma faixa continua de condicao operacional (envelope operacional)
- **e17** (MOBO, 2021): Sec. IV-A, Fig. 7(b) — [nova] Comparacao visual do front 2D projetado entre algoritmos, sem frente verdadeira conhecida
- **e64** (SA-MOPSO (PPD), 2025): Sec. 5.2.3, Figs. 14-15 — [nova] Interpretação físico-decisória dos projetos ótimos do caso real (segmentos x variáveis de decisão x física do domínio)
- **e7** (EDN-ARMOEA, 2022; roster): Sec. V (Conclusão); estudo completo no Sec. VII do Supplementary material (ausente deste… — [nova] Estudo de caso real — unidades de destilação de petróleo bruto
- **e74** (CLMEA, 2023; roster): Sec. IV-H; Fig. 13 (rede de fraturas e poços); Fig. 14 (soluções ND e valores de HV) — [nova] Estudo de caso real — extração de calor geotérmico (EGS fraturado)
- **e81** (qPOTS, 2025; roster): Sec. 4.2, Fig. 9 e Fig. 10 — [nova] Interpretação aerodinâmica dos designs (coeficiente de pressão) · Sec. 4.2, Fig. 11 — [nova] Interpretação aerodinâmica dos designs (geometria do perfil/asa)
- **wang4** (SA-NSGA-II, 2016): Sec. V-D (final), Fig. 19 — [nova] Confronto do ND obtido com a configuração real vigente do sistema (status quo), sob restrições relaxadas

**Score (0–10): 5.** **Justificativa.** Reproduzível para RE21/ESTOQUE40/DDMOP7 (interpretar 2–3 soluções ND por caso: política de estoque, geometria, rede esparsa). C: 16/72 (R2#6; roster: c141 tensões, e81 Cp da asa, e74 geotérmico, b3, e7) — convenção forte nos casos reais. P média: a dissertação é metodológica; a interpretação de domínio consome texto e não responde à pergunta da incerteza. Entra no máximo como um parágrafo por caso em 23 (o ESTOQUE40 é o mais legível).


### 80. Correlação entre objetivos nos problemas da bateria (característica do problema)

**Fontes.** [MIN] 1 análise (c81 Table C.1: |ρ| < 0,3 justifica a agregação multiplicativa) + c82 (ficha 17: correlação controlável muda a vantagem) + b15/c106 (68: modelar a correlação não ajuda) · ficha 17 (matriz de características D98) · ficha 37.

**O que analisa.** A correlação (Pearson/Spearman) entre os objetivos sobre o espaço amostrado (DoE) e sobre o front de referência, por problema — uma coluna da matriz de características, que explica quando 'm sigmas independentes' são um problema (37) e quando escalarizações (b1, b3) sofrem.

**Dados.** ① (f do DoE, comum a todos por semente) ou S (gabarito da sonda: 2.000 pontos com f); M (fronts de referência).

**Objetivo.** Completar a matriz de características (D98) com uma medida contínua e reproduzível, e testar se a correlação prediz a vantagem das classes de função (17/20).

**O que busca revelar.** Se problemas com objetivos anticorrelacionados (conflito forte) favorecem métodos de hipervolume/informação e os correlacionados favorecem escalarização — hipótese de c82.

**Como é realizada.** Por problema: matriz de correlação dos objetivos nos 2.000 pontos Sobol (S) e no front de referência; escalar (ρ médio); coluna na tabela de características; cruzamento com 17.

**Técnicas.** Pearson/Spearman; tabela.

**Implementação.** Sobre S (`data/sonda/sonda_{problema}.parquet`) — trivial; DDMOP7 sem sonda (usar ①).

**Em quantos artigos aparece (dos 72).** 1 artigos (1 análises): dos 38 iniciais 1, dos 7 do roster 0, dos 27 complementares 0; do roster (15): 0. Nas planilhas dos 38 (Ranking 2) o tipo mais próximo está indicado em Fontes.

**Estado.** N — dado pronto; custo mínimo.

**Demais detalhes.** Relação: 17, 18, 20, 37. Decisão: entra como coluna, não como seção.

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 1 artigos / 1 análises** — dos 38 iniciais: 1 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 0 · artigos do roster (15): 0.

- **c81** (UA-MORL-Diff, 2025): Appendix C.1, Table C.1 — [nova] Análise de correlação entre os 3 objetivos para justificar a independência assumida na agregação multiplicativa da…

**Score (0–10): 5.** **Justificativa.** Reproduzível de ① (Pearson/Spearman entre objetivos sobre as avaliações ou o front de referência) — uma característica do problema, não uma análise. C: 1/72 direto (c81 |ρ| < 0,3 justifica agregação multiplicativa) + c82 (correlação controlável muda a vantagem). P média: entra como coluna da matriz de características (D98, ficha 17) e como explicação de 37; não como seção.

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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 44 artigos / 90 análises** — dos 38 iniciais: 23 · dos 7 do roster minerados agora: 6 · dos 27 complementares: 15 · artigos do roster (15): 11.

- **b13** (AdaMoR-DDMOEA, 2025): Sec. 5.5.1, Figure 5 — Sensibilidade do IGD final ao número máximo de iterações (gerações) do AdaMoR-DDMOEA, varrido de 10 a 600 (execuções completas separadas para cada…
- **b14** (SA²-MOEA, 2024): Fig. 3, Sec. 4.4 — Curvas de convergência (trajetória, não só endpoint) para a mesma ablação do otimizador híbrido da análise anterior: IGD médio ao longo das…
- **b15** (U-RankMOEA, 2026): Sec. 4.2 (texto) e Apendice O, Fig. 10, Fig. 11, Fig. 15 — Curvas de convergencia de IGD (e HV, no caso do estudo Static-EHVI) ao longo das avaliacoes reais, para varios problemas/dimensoes: 'Type A problems'…
- **b2** (MOEA/D-EGO, 2010): Sec. VII-D-1 (Comparison); Fig. 7(a)–(l) — A Fig. 7 traça, para cada uma das 12 instâncias, a evolução da média do IGD das soluções não-dominadas encontradas até então em função do número de… · Sec. VII-E-3 (Why Some Instances Are Harder Than Others); Fig. 7(e); Fig. 3(d) — Cruzando a Fig. 3(d) — que mostra que o MOEA/D-EGO já encontrou boas soluções em ZDT6 — com a Fig. 7(e) — que mostra que o IGD médio para de cair nas…
- **b5** (Prob-RVEA / Prob-MOEA/D (+ Hyb-RVEA / Hyb-MOEA/D), 2022; roster): Sec. IV-A, Fig. 10 — Três curvas, da mesma execução com HV mediano, ao longo de FE (checkpoints a cada 1000 avaliações, até 40000, na instância DBMOPP P1 K=5/LHS): (a) HV…
- **b9** (USeMO, 2020): Sec. 5.2 ("USeMO vs. State-of-the-art"); Fig. 2; Table 1 (definição dos benchmarks) — Para os 8 benchmarks sintéticos (Tabela 1), o artigo plota a evolução do log da diferença de hipervolume (PHV) e do log do indicador R2 em função do… · Sec. 5.2 ("USeMO vs. State-of-the-art"); Fig. 3; Sec. 5.1 (descrição dos 6 benchmarks… — Mesmo tipo de comparação da Figura 2, mas nos 6 benchmarks reais (rede neural/MNIST, SW-LLVM, SNW, NOC, SMA, PEM): curvas de log da diferença de… · Sec. 5.2 ("USeMO vs. State-of-the-art") — menção; conteúdo do Apêndice ausente do texto… — O artigo menciona fornecer resultados adicionais de USeMO com a função de aquisição LCB no Apêndice (complementando EI e TS, mostrados nas Figuras… · Sec. 5.1 (logo após a Tabela 1, antes de "Real-world benchmarks") — menção; conteúdo do… — Ao descrever os 8 benchmarks sintéticos e antes de passar aos benchmarks reais, o texto indica que, por restrição de espaço, parte dos resultados…
- **c1** (BS-MOBO, 2018): Sec. IV-B-3, Fig. 5 — Curvas de convergência (execução mediana do IGD, escala logarítmica) versus número de avaliações reais, para 4 instâncias selecionadas (ZDT1, F2,… · Sec. IV-D, Fig. 7 — Estudo de caso do problema real Rosetta (trajetória espacial, biobjetivo, D=22, gradiente disponível): evolução do hipervolume mediano (10 execuções…
- **c10** (SP-RV-MOEANet, 2021): Fig. 3 — Curva da evolução do HV ao longo das GERAÇÕES (não da fração do orçamento de avaliações reais) para os 5 algoritmos comparados, evidenciando… · Fig. 4 — Curva de HV em função do orçamento REAL de avaliações (custo relativo R:Rl=1:5, orçamento máximo de 10000) para quatro algoritmos — P0-MOEANet…
- **c100** (qEHVI, 2020): Sec. 5.1, Fig. 3(a-d) — Curvas de convergência da otimização sequencial (q=1) em 4 problemas — Branin-Currin, C2-DTLZ2 (restrito), VEHICLESAFETY e ABR — medidas em… · Sec. 5.1, Fig. 4(a-b) — Desempenho de otimização paralela no problema ABR variando o tamanho do lote q em {1,2,4,8}, visto por (a) iteração de BO (lote) e (b) avaliações de…
- **c107** (MS-VHGP-EIHV, 2017): Sec. III-E1, Fig. 9 — Compara o GP padrão (homocedástico) sozinho — o 'método existente' [3] — contra o VHGP (heterocedástico) sozinho, SEM nenhum mecanismo de seleção… · Sec. III-E2, Fig. 12 — Compara o desempenho (HV x avaliações) obtido usando o EIHV exato (quadratura de Gauss-Hermite) versus o EIHV aproximado (aproximação Gaussiana), no… · Sec. III-E3, Fig. 14 — Compara o desempenho (HV x avaliações) de duas alternativas para o critério de seleção de modelo (GP padrão vs. VHGP) na função MAT, Ni=15, ruído… · Sec. III-E4, Figs. 15-22 — Compara 3 métodos — proposto (GP+VHGP com seleção de modelo por LOO), existente [3] (GP padrão sozinho) e VHGP sozinho — nas 4 funções de teste 2-D… · Sec. III-E5, Fig. 23 — Testa a versão 10-D de T3 (D=10 em (22), mesmo HV verdadeiro 10.0444, Ni=50, Nm=100 no total), comparando apenas o método proposto contra o método… · Sec. IV, Fig. 27 — Compara o HV do método proposto, do método existente e da mediana de 5 execuções de busca aleatória (random search, sem banda de erro), no…
- **c122** (θ-DEA-DP, 2022; roster): Sec. IV-B, Fig. 5 — Curvas de evolução da mediana do IGD (sobre 21 execuções) versus o número de avaliações de função, para θ-DEA-DP e os 5 comparados, nos problemas ZDT… · Sec. IV-C, Fig. 6 — Mesma estrutura da Fig. 5, agora para os problemas de 5 e 8 objetivos (subconjunto de DTLZ/WFG), permitindo comparar visualmente a velocidade de…
- **c123** (EPBII / EIPBII, 2017): Sec. VI-C, Figs. 24, 25 — Estudo de sensibilidade ao tamanho do lote de pontos adicionados por iteração (nadd = 3, 5, 10) para EPBII e EIPBII no problema LZ08-F2, plotando o… · Sec. VI-B-2, Fig. 21 — Para o problema DTLZ2max2 de 4 objetivos, o artigo plota a evolução do valor médio de IGD (Fig. 21a) e de IH (Fig. 21b) ao longo do número de…
- **c131** (MORBO, 2022): Sec. 5.1 ('Trajectory Planning'), Fig. 3 (esquerda) — Curva de Hypervolume medio x ate 2.000 avaliacoes reais (lote q=50, 200 pontos iniciais) no problema de planejamento de trajetoria (d=60, 2 objetivos… · Sec. 5.1 ('Optical design problem'), Fig. 3 (centro) — Curva de HV medio x ate 10.000 avaliacoes (lote q=50, 250 pontos iniciais) no problema de design otico AR/VR (d=146, eficiencia x qualidade de… · Sec. 5.1 ('Mazda vehicle design problem'), Fig. 3 (direita) — Curva de HV medio x ate 10.000 avaliacoes (lote q=50, 300 pontos iniciais) no problema veicular Mazda (d=222, 2 objetivos, 54 restricoes black-box de… · Apendice F.4 ('Additional benchmark problems'), Fig. 11 (M=2), Fig. 12 (M=4) — Curva de HV medio x 2.000 avaliacoes (q=50) nas variantes de 2 e 4 objetivos de DTLZ3, DTLZ5 e DTLZ7 (d=100 em todas), comparando MORBO a NSGA-II,…
- **c141** (MMRAEA, 2025; roster): Sec. Effectiveness of bi-population based on CSO and GA, Fig. 5 e Fig. 6 — Curvas de IGD ao longo das avaliações reais para as três variantes da ablação bi-populacional (MMRAEA-GA, MMRAEA-CSO, MMRAEA), em DTLZ2 (Fig. 5) e… · Sec. Results and discussions (BWBUG), Fig. 13 — Curvas de IGD e HV ao longo das avaliações reais para os 5 algoritmos no caso BWBUG.
- **c149** (LBN-MOBO, 2023; roster): Sec. C.1.4 (Apêndice), Figs. 9, 10 — Compara LBN-MOBO com USeMO, DGEMO, TSEMO e NSGA-II (piso evolutivo sem surrogate) no ZDT3 em 6D e 30D, lote fixo em 1000, por até 10 iterações: (a)… · Sec. C.1.5, Fig. 12 — Mesma comparação (LBN-MOBO, USeMO, DGEMO, TSEMO, NSGA-II) repetida em ZDT1 (frente convexa) e ZDT2 (frente não-convexa), 30D, reportando evolução do… · Sec. C.4, Figs. 14, 15 — Compara LBN-MOBO (testado com lotes de 1000 e 4000 amostras) contra DGEMO, TSEMO, USeMO e NSGA-II no DTLZ4 (6D entrada, 3 objetivos): fronteira de… · Sec. C.4, Fig. 16 — Mesma comparação (LBN-MOBO, DGEMO, TSEMO, USeMO, NSGA-II) no DTLZ1 (6D entrada, 3 objetivos): fronteira final, tempo decorrido e evolução do HV (em… · Sec. 5.3, Fig. 4 — Aplica LBN-MOBO com dois surrogates (Deep Ensembles vs. MC Dropout) a dois problemas reais próprios do artigo: aerofólio (Cl, Cl/Cd, via GAN 5D + CFD… · Sec. C.6.1, Fig. 17 — Compara LBN-MOBO com NSGA-II (piso evolutivo, lote 20.000) e DGEMO (lote limitado a 1.000, 5 iterações) no gamut de 44 tintas: evolução do HV e gamut… · Sec. C.6.2, Fig. 18 — Compara LBN-MOBO com NSGA-II e DGEMO no problema real de aerofólio (GAN 5D + CFD OpenFOAM, lote 15.000): evolução do HV, fronteira final e regret… · Sec. C.7, Fig. 19 — Repete a comparação (LBN-MOBO, NSGA-II, DGEMO, Random) no gamut de 8 tintas (espaço de design menor que o de 44 tintas), evolução do HV e gamut…
- **c154** (JES, 2022; roster): Sec. 5.2, Fig. 5 (painel superior) — Compara JES-LB com Sobol, TSEMO, NParEGO, NEHVI, PES e MES-LB (subconjunto dos ~15 algoritmos/variantes testados) nos 4 problemas de benchmark, no…
- **c214** (PFES, 2020): Sec. 6.1, Fig. 4 — Comparação central de desempenho: PFES (em três variantes, |PF|=10, 30 e 50 amostras de Pareto-frontier) contra os quatro métodos existentes (ParEGO,… · Sec. 6.2, Fig. 5 — Em um dataset real de ciência de materiais (Bi2O3, 335 candidatos discretos, 3 dimensões de entrada, objetivos de condutividade iônica e… · Sec. 6.2, Fig. 6 — Mesmo desenho experimental da análise anterior (regime desacoplado, RHV × custo cumulativo, duas razões de custo λ1/λ2, 10 execuções, 5 pontos…
- **c217** (PC-SAEA, 2023; roster): Sec. 4.3, Fig. 6 — Figura dupla para 2-objective DTLZ3 (frente altamente multimodal): (a) as populações finais (espaço de objetivos) dos 8 algoritmos na execução de IGD… · Sec. 4.3, Fig. 7 — Mesma figura dupla (população na execução de IGD mediano + curva de IGD médio × fração de avaliações) para 3-objective WFG2, problema com frente de…
- **c222** (MESMO, 2019): Sec. 5.2, Fig. 1 — Curvas de PHV_diff (log da diferença entre o hipervolume ideal e o estimado) e de R2 Indicator ao longo das iterações (avaliações reais), comparando… · Sec. 5.2, Fig. 2 — As mesmas duas curvas (PHV_diff log e R2 × iterações), para os mesmos algoritmos, nos benchmarks do mundo real (ajuste de hiperparâmetros de rede… · Sec. 5.2 (menção); Fig. 3 do Appendix — não presente nesta extração (o documento… — O artigo MENCIONA resultados adicionais nos dois benchmarks sintéticos definidos na Seção 5.1 mas não plotados na Fig. 1 do corpo principal (OKA2-2,3…
- **c241** (EMMOEA, 2023): Sec. III-E, Fig. 9 — Curvas de convergência do IGD e do HV em função do número de avaliações caras (de 100, fim do DoE, a 300), para os mesmos 5 problemas de 3 objetivos…
- **c261** (DirHV-EGO, 2024): Sec. V-C, p.9, Fig. 4 (+ Fig. 10, Supplementary Sec. VI) — Curvas de convergência (log IGD+ × nº de avaliações de função) para os mesmos quatro critérios EI (q=1) da análise anterior. O corpo principal mostra… · Sec. V-C, p.9, Fig. 5 (+ Figs. 11-12, Supplementary Sec. VI) — Curvas de convergência (log IGD+ × FE) para os quatro algoritmos paralelos da análise anterior. O corpo principal mostra q=5 (12 problemas); o… · Supplementary Sec. VI, Fig. 13 — Curvas de convergência (HV × nº de avaliações de função) para os quatro algoritmos paralelos nos cinco problemas reais (RE1-RE5), q=5, média±dp de 21… · Supplementary Sec. III-C.4/III-D.1, p.9-10, Fig. 7 (Supplementary) — Curvas de convergência (log IGD+ × FE) para a comparação many-objective da análise anterior, m=4 e m=6 lado a lado, DTLZ1-7, 5 algoritmos, 21…
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF), 2021; roster): Fig. 3 (Sec. 9); Fig. 9(a) (Apendice H.3) — Curvas de convergencia (log da diferenca de hipervolume x avaliacoes de funcao, sequencial q=1) para 8 problemas -- BraninCurrin, DTLZ2, ABR,… · Fig. 9(b,c) (Apendice H.3); Fig. 11 (mesmos dados, eixo x em avaliacoes) — Curvas de 'anytime performance' (log HV diff x avaliacoes de funcao OU x iteracao de lote) decompostas por tamanho de lote q, para os metodos… · Fig. 10 (Apendice H.3); Fig. 12 (mesmos dados, eixo x em avaliacoes) — Mesma familia de curvas 'anytime', restrita a comparacao dentro da familia EHVI: qNEHVI (via CBD) vs. qEHVI-PM-CBD, em varios q, isolando o efeito…
- **c276** (ε-PAL, 2016): Sec. 7.4, Fig. 6 — Para os três data sets (SNW, NoC, SW-LLVM), o artigo plota o erro percentual de predição e(P,P̂) (mediana de 200 repetições) em função do número de…
- **c48** (IBE-CSEA, 2021): Sec. 4.5, Fig. 6 — Curvas de convergência do IGD ao longo do número de avaliações (eixo confirmado pelo OCR da figura — 'Number of evaluations') para os 7 algoritmos em…
- **c50** (PD-MOEA, 2018): Sec. 5, Fig. 3, p.14-15 — Com carga fixa em L=300MW e α=0,5, o algoritmo evolutivo de dominância probabilística roda por 20.000 gerações (checagem extra a 10^5 gerações),… · Sec. 6, Fig. 7, p.21-22 — O artigo estende o algoritmo removendo a restrição de carga fixa: a carga passa a ser uma terceira dimensão do arquivo (UBC, NOx, Load), e soluções…
- **c59** (UA-DBO, 2026): Sec. 4.2, Fig. 8, p. 16–17 — Para cada um dos 3 casos, uma execução (dentre as 5) é selecionada para plotar a convergência do objetivo ao longo das 50 iterações (Fig. 8): a curva…
- **c65** (SABBa, 2022): Sec. 5.1.1, Fig. 5 — Para o caso-teste 1 (Taguchi biobjetivo) com surrogate de ALTA qualidade (kernel ARD anisotrópico), o artigo plota curvas de QB (distância de… · Sec. 5.1.2, Fig. 7 — O mesmo caso-teste 1 é resolvido usando um surrogate de BAIXA qualidade (kernel RBF isotrópico, 1 único lengthscale para todas as dimensões,… · Sec. 5.2, Fig. 9 — No caso-teste 2 (otimização de desempenho médio sob restrição de quantil 95%, D=4, 3 incertos — mais dimensional e com restrição de confiabilidade),…
- **c66** (PAL-SAPSO, 2019): Sec. IV-A, Fig. 2 — Curvas da média do IGD (escala log) em função do número de avaliações reais consumidas (500, 1000, 1500 e 2000), uma por problema, comparando a…
- **c75** (MO-EI/PI (Keane), 2006): First Example and Some Basic Searches, Fig. 6 (p. 883-884) — [nova] Convergência SO ilustrativa (pré-MOO): krig+E[I] sequencial vs GA direto
- **c81** (UA-MORL-Diff, 2025): Sec. 4.2.2, Fig. 2 — Fig. 2 mostra, para cada um dos 3 datasets, a evolução de 5 métricas de qualidade (validade, unicidade, novidade, estabilidade atômica, estabilidade…
- **c82** (TC-SAEA, 2022): Sec. 4.4, Fig. 8 — Estende o orçamento para FEs_max_s=1000 (5× o padrão do artigo) apenas em DTLZ1a, e plota a evolução do IGD ao longo das gerações para cada um dos 8…
- **e102** (MOEA/D-ASS, 2021): Sec. V-C, Fig. 6 (d=8) e Fig. 7 (d=10) — Curvas de evolução do valor MÉDIO de IGD (não mediana) em função do número de avaliações reais, uma por problema, para os 21 problemas de teste…
- **e103** (IBEA-MS, 2023; roster): Sec. IV-A, Fig. 4 — Curvas de IGD média (±1 desvio-padrão sombreado, 30 execuções) ao longo das iterações no problema ZDT4 (D=10), comparando K-IBEA, R-IBEA, IBEA-MS e… · Sec. IV-B, Fig. 7; Tables S.IX–S.XI (material suplementar) — Estudo de escalabilidade com a dimensão de decisão D (10→20→30) para IBEA-MS vs. as 3 variantes AK-IBEA (Tables S.IX-S.XI, mencionadas) mais um caso…
- **e16** (EGBO, 2024): Sec. Self-driving lab for AgNP experimental campaign, Fig. 3c — Para a mesma campanha AgNP (execução única por otimizador), o artigo plota a evolução de HV, NU (não-uniformidade) e da fração infactível cumulativa… · Sec. Synthetic studies, Fig. 4c — Curvas de logΔHV, NU e violação de restrição (CV, separada para c1 e c2) ao longo de 48 iterações, média ± IC95% sobre 10 execuções, comparando… · Sec. Synthetic studies, Fig. 4c — O mesmo experimento (MW7, n=8, 10 execuções, 48 iterações) inclui também qNParEGO (aquisição por escalarização) e U-NSGA-III puro (piso evolutivo SEM… · Sec. Handling input and output constraints, Fig. 5c — No problema AgNP (usando um GP treinado sobre TODOS os dados reais da campanha como pseudo-verdade de referência para HV), o artigo compara…
- **e17** (MOBO, 2021): Sec. IV-A, Fig. 7(a) — Para o problema real do fotoinjetor AWA (7 objetivos, 6 parametros), o artigo compara a evolucao do hipervolume medio (+/- 1 sigma, 10 execucoes) em… · Sec. IV-C, Fig. 9(c) — Ainda no problema AWA, compara o hipervolume medio (10 execucoes, com as MESMAS inicializacoes aleatorias para as duas variantes) ao longo das…
- **e3** (HeE-MOEA, 2019): Sec. V-D, Fig. 3 — Curvas da IGD MÉDIA (não mediana) em função do número de avaliações de função (FEs), para N=20, comparando HeE-MOEA-ExI (linha vermelha com 'o') e…
- **e40** (SBP-BO, 2023): Sec. IV-B-1, Tables SI-SII e Figs. S3-S6 (Supplementary material, nao incluido no PDF… — Curvas/tabelas do IGD+ obtido por cada algoritmo em funcao do numero de avaliacoes reais (FEs), com significancia estatistica marcada em cortes de FE…
- **e7** (EDN-ARMOEA, 2022; roster): Fig. 2 (a-d) — Curvas de convergência (IGD médio com barras de erro versus número de avaliações reais, no intervalo 450-550 FEs) para 4 problemas amostrados (DTLZ4,…
- **e74** (CLMEA, 2023; roster): Fig. 6, Fig. 9, Fig. 10 (corpo principal); Figs. S-1–S-9 (Supplementary material) — Curvas de IGD médio (com banda de variância entre execuções) ao longo do orçamento de FEs (do fim do DoE até 300), para os 6 algoritmos comparados.…
- **e8** (NN-EGO, 2020): Table S6 (S17) — [nova] Evolução das médias do front de Pareto real por geração
- **e81** (qPOTS, 2025; roster): Sec. 4.1, Fig. 4, Table 1 — Curvas de hipervolume × número de avaliações para amostragem sequencial (q=1) nos 4 problemas sintéticos (Branin-Currin, DTLZ3, DTLZ7, ZDT3),… · Sec. 4.1, Fig. 5 — As mesmas curvas de HV × avaliações, agora em modo lote (q=2 e q=4), nos mesmos 4 problemas sintéticos, com a mesma lista de concorrentes sufixados… · Sec. 4.2, Fig. 7 (painel direito) — No caso real do CRM (d=24, K=2), curva de HV ao longo das iterações comparando qPOTS contra qNEHVI ('EHVI'), qPAREGO ('ParEGO') e Sobol, numa única…
- **e9** (SUR, 2015): Sec. 5.1, Fig. 7 — Comparação de desempenho entre o SUR proposto e o SMS-EGO (Ponweiser et al., 2008) no mesmo problema de brinquedo 1D/biobjetivo, usando três… · Sec. 5.2, Fig. 8 — Repetição do mesmo protocolo de comparação SUR vs. SMS-EGO (três indicadores: hipervolume, epsilon, R2) num problema de brinquedo 6D/biobjetivo (Sec.…
- **jin3** (GS-MOMA / GSM (mono: GS-SOMA), 2010): Sec. IV-B-1, Fig. 4 — Curvas de convergência (fitness em escala log natural ou linear, conforme o problema, x avaliações exatas em milhares) para GS-SOMA, SS-SOMA-Perfect…
- **mtm4** (MAES (variante MO: M-NSGA-II), 2006): Sec. V-D e V-F, Figs. 10, 11, 12, 13, 27 (pp. 10-12) — Para 5 problemas de teste (esfera, elipsoide/esfera escalada, degrau e Ackley, 20-D, sem restrição; e o problema de Keane, 10-D, restrito e…

**Complementos e correções (06/09/2026).** Convenções minadas: eixo x em avaliações reais (maioria), em gerações (c10 Fig. 3) ou em custo cumulativo (c214); eixo y log (c1, c261, c262, c66, jin3); média ± EP (BO), IGD médio com barras (e7, e74, e3), execução mediana (c1, c217), curva da execução com HV mediano (b5); janelas parciais (c122 'últimas 100 avaliações'). Nossa mediana + IQR × fração do orçamento é a variante EA com dispersão explícita — declarar.

**Score (0–10): 10.** **Justificativa.** F. C: 44/72 — a segunda análise mais frequente (R2#5 22/38, agora 44/72); convenções variam (média±EP no BO; mediana no EA; log no eixo y em c1, c261, c262). P alta: 'quando' o surrogate compra (cedo e perde depois, ou tarde). V: cap. 4 l.364 (prefixo), 27/28/29. Núcleo; decisão só de convenção (mediana+IQR é a nossa; declarar).


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 4 artigos / 5 análises** — dos 38 iniciais: 2 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 2 · artigos do roster (15): 1.

- **b1** (ParEGO, 2006; roster): Sec. VIII, Table VI — Tabela algoritmo x problema do S-measure (indicador de hipervolume) após 100 avaliações de ParEGO e 100 de NSGA-II, nas 9 funções MOO, com média e… · Sec. VIII, Table VIII — Tabela algoritmo x problema do indicador epsilon binário aditivo (ambas as direções, I_ParEGO,NSGA-II e I_NSGA-II,ParEGO) após 100 avaliações de cada…
- **c66** (PAL-SAPSO, 2019): Sec. IV-B-1), Table II — Tabela com MSE1, MSE2 (erro quadrático médio de cada uma das 2 saídas) e MSE total (soma), média (desvio-padrão) sobre 10 execuções independentes,…
- **e1** (EMO, 2014): Sec. 5 (Conclusion) — Menção, como resultado preliminar de trabalho futuro (sem tabela, figura ou números), de que a vantagem do EMO sobre alternativas seria maior quanto…
- **wang4** (SA-NSGA-II, 2016): Sec. V-D, Table III — Recomputa a comparação sob orçamento apertado, mas medido em TEMPO DE PAREDE (1 hora de execução, não gerações/avaliações) para as mesmas três…

**Score (0–10): 8.** **Justificativa.** N. C: 4/72 (b1 em 100 vs 250 avaliações; wang4 sob 1 h de parede; e1 menção; c66). P alta e V forte: cap. 4 l.364 promete 'a comparação sob orçamento apertado' — vinculante; e o cap. 6 ecoa. D barata (recorte por prefixo em ①, D25 já tem o casamento). Entra como tabela 'placar em 1/3 e 2/3 do orçamento'.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 1 artigos / 1 análises** — dos 38 iniciais: 1 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 0 · artigos do roster (15): 0.

- **b2** (MOEA/D-EGO, 2010): Sec. VII-E-3 (Why Some Instances Are Harder Than Others); Fig. 7(e); Fig. 3(d) — Cruzando a Fig. 3(d) — que mostra que o MOEA/D-EGO já encontrou boas soluções em ZDT6 — com a Fig. 7(e) — que mostra que o IGD médio para de cair nas…

**Score (0–10): 6.** **Justificativa.** F. C: 1/72 (b2 'por que algumas instâncias são mais difíceis' cruza início × fim). P média: 'quem mais melhora na segunda metade' é leitura derivada de 26/27. Já feita; entra como uma frase/figura pequena ou apêndice.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 0 artigos.** Nenhuma análise dos 72 foi mapeada a esta ficha — leitura própria da tese (ou regra/nota), sem correspondente nomeado no corpus.

**Score (0–10): 7.** **Justificativa.** T. C: 0/72 (o corpus não tem teto de parede — roda até o fim). P: não é resultado, é a chave metodológica das 615 células ⚪ (C8 parcial; decisão 2). D pronta. Recomendo decidir cedo (a lente de prefixo permite incluir as 615 em 27 sem violar C8) e reportar em 57/60; se ficar de fora do corpo, apêndice.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 0 artigos.** Nenhuma análise dos 72 foi mapeada a esta ficha — leitura própria da tese (ou regra/nota), sem correspondente nomeado no corpus.

**Score (0–10): 5.** **Justificativa.** T. C: 0/72 como sanidade de pipeline (a 'validação numérica' do corpus é do estimador da aquisição — ficha 70, 12/72). Necessária para o autor, invisível para o leitor: uma frase no cap. 4/apêndice. Custo zero.



### 72. Análise a alvo fixo: avaliações até atingir um nível de IGD+ (ERT / fixed-target), por família

**Fontes.** [MIN] 3 análises em 3 artigos (lista abaixo) · ficha 26/27 · convenção COCO/BBOB (a bateria tem 7 funções BBOB) · [CAP4] (as funções BBOB entram via fronts empíricos D72).

**O que analisa.** Em vez de 'qual IGD+ em 31D−1' (alvo fixo de orçamento), 'quantas avaliações para atingir IGD+ ≤ τ' (alvo fixo de qualidade): b1 mede o múltiplo de avaliações que a busca aleatória precisa para igualar o EGO (2×–250×), c250 conta chamadas até convergência (K-MOGA usa ~50% menos), c29 mede quantas observações o Monte Carlo precisa para igualar o P-algorithm (6× num problema, 2× noutro).

**Dados.** ① (trajetória de IGD+ por FE, já computada para 26 no cache `trajetorias`); M (alvos por problema: quantis do IGD+ final dos pisos, ou frações fixas).

**Objetivo.** Medir eficiência amostral — o que 'expensive' quer dizer — e dar uma leitura robusta às células que não chegaram ao fim (teto de parede: se atingiram o alvo antes, contam).

**O que busca revelar.** Quantas vezes menos avaliações o assistido precisa para chegar onde o piso chega no fim (e vice-versa onde o piso vence — 16); ERT infinito onde nunca chega (58).

**Como é realizada.** Para cada célula, o FE em que a trajetória cruza o alvo (alvo = IGD+ final mediano do piso casado, por problema; ou 3 alvos: 2×, 1,5×, 1× do piso); ERT = média das avaliações sobre execuções com sucesso, penalizando insucesso (definição COCO); tabela por família de problema × algoritmo.

**Técnicas.** Fixed-target; ERT (expected running time) com taxa de sucesso; razão ERT_assistido/ERT_piso; mediana entre sementes.

**Implementação.** Sobre o cache de trajetórias (26): interpolar o primeiro FE com IGD+ ≤ alvo; alvo por problema derivado de 1/9; tabela e uma figura (razão por família). ~1 célula de notebook.

**Em quantos artigos aparece (dos 72).** 3 artigos (3 análises): dos 38 iniciais 2, dos 7 do roster 0, dos 27 complementares 1; do roster (15): 1. Nas planilhas dos 38 (Ranking 2) o tipo mais próximo está indicado em Fontes.

**Estado.** N — dado pronto; custo baixo.

**Demais detalhes.** Caveats: o DoE de 11D−1 é comum (contar FE a partir de 0 ou do fim do DoE — declarar); DDMOP7 sem IGD+; alvo derivado do piso é circular se o piso não converge (usar alvo por quantil). Relação: 26, 27, 16, 29, 58. Decisão: definição do alvo.

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 3 artigos / 3 análises** — dos 38 iniciais: 2 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 1 · artigos do roster (15): 1.

- **b1** (ParEGO, 2006; roster): Sec. III-B; Table I; Table II — [nova] EGO x busca aleatória -- múltiplo de avaliações para vitória/empate (single-objective)
- **c250** (K-MOGA, 2008): Sec. 4.1 (Fig. 4) e Sec. 4.3, Table 3 (p. 031401-5 a 031401-9) — [nova] Economia de avaliacoes reais ate convergencia sob parada adaptativa (custo em chamadas de simulacao, sem orcamento fixo)
- **c29** (MO P-algorithm, 2014): Sec. 7, último parágrafo, p. 92 — [nova] Equivalência de avaliações — quantas avaliações o piso precisa para igualar a qualidade do assistido

**Score (0–10): 7.** **Justificativa.** Reproduzível com ① (trajetórias): 'quantas avaliações para atingir IGD+ ≤ alvo' (fixed-target / ERT) é a convenção COCO/BBOB — e a bateria tem 7 funções BBOB (F1, F5, F17, F22, F37, F49, F55). C: 3/72 (b1 'EGO é até 250× mais rápido que busca aleatória', c250 '50% menos chamadas', c29 '600 observações para igualar'). P alta: é a leitura de EFICIÊNCIA AMOSTRAL (o que 'expensive' significa) e complementa 26/27 com uma tabela pequena. Entra como tabela 'orçamento para atingir o alvo, por família'.

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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 19 artigos / 24 análises** — dos 38 iniciais: 11 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 8 · artigos do roster (15): 1.

- **b15** (U-RankMOEA, 2026): Apendice E, Fig. 4 — Densidade log-preditiva negativa (NLPD) de validacao do Deep GP ao longo das iteracoes de otimizacao, comparando a variante com triagem seletiva… · Apendice K, Fig. 13 — Evolucao media da incerteza epistemica e aleatoria do Deep GP ao longo da otimizacao em DTLZ2-100D, mostrando a incerteza epistemica caindo a medida…
- **b2** (MOEA/D-EGO, 2010): Sec. VII-E-3 (Why Some Instances Are Harder Than Others); Table IV — Para investigar por que algumas instâncias são mais difíceis, os autores constroem um modelo Gaussiano preditivo para o objetivo f2 em cada uma das…
- **b7** (DR (Dual-Ranking), 2026): Sec. 4.2 (Surrogate Prediction Performance Results); Material Suplementar Sec. 1.2,… — Comparação da qualidade preditiva bruta dos 4 surrogates (GPR-RBF, GPR-Matérn, Autogluon-QR, BNN) nos 11 problemas, medida por MSE (acurácia da…
- **c24** (DTK-MODE, 2015): Sec. IV-A, Fig. 3 — O artigo compara a acurácia de ajuste (RMSE) de quatro tipos de modelo Kriging — Ordinary Kriging (OK), Universal Kriging de 2a ordem (UK), Taylor… · Sec. IV-A, Table II — Para o DTK especificamente, a Tabela II reporta o RMSE de ajuste à medida que o número de pontos de amostragem aumenta (via o processo de amostragem…
- **c45** (GP-DGS, 2024): Sec. 2.2 (definição da métrica) e Table 1, Sec. 3 Results and Discussion — Tabela 1: o artigo reporta o erro quadrático médio normalizado (NRMSE) entre as predições dos GPs e os valores 'verdadeiros' calculados por SEAWAT,…
- **c50** (PD-MOEA, 2018): Sec. 3.1, Fig. 2, p.8-9 — Os dois GPs independentes (G_UBC, G_NOx) são avaliados por validação cruzada 10-fold sobre os 654 pontos coletados: para cada ponto, a predição vem…
- **c59** (UA-DBO, 2026): Sec. 4.1.1, Table 1, p. 13–14 — [nova] Acurácia da média: modelo determinístico vs. modelo com UQ, em treino/teste (pré-treino)
- **c66** (PAL-SAPSO, 2019): Sec. IV-B-1), Fig. 3 — [nova] Validação visual do modelo-alvo tunado (predito × real, downstream)
- **c81** (UA-MORL-Diff, 2025): Sec. 4.2.1; definição em Appendix B.8.1; painéis em Appendix C.2, Fig. C.1–C.2 — Avalia a acurácia (R², via parity plots, Fig. C.1) e a calibração da incerteza (AUCE, via curvas de calibração/diagramas de confiabilidade, Fig. C.2)…
- **c82** (TC-SAEA, 2022): Sec. 4.7 (Effects of the Co-surrogate); Figs. S1 e S2 (material suplementar, não incluído… — Roda TC-SAEA em cada instância biobjetivo DTLZ (10 execuções independentes, FEs_max_s=200) e calcula, a cada geração, o erro quadrático médio (MSE)…
- **e1** (EMO, 2014): Sec. 4.3, Fig. 6 — Validação cruzada 20-fold da acurácia da MÉDIA do Kriging (não da variância) sobre os 250 pontos amostrados, para o primeiro objetivo de DTLZ1…
- **e21** (PIO, 2025): Fig. 2; Results, 'Surrogate model and UQ performance' — Avalia a acurácia da MÉDIA predita (μ) pelo D-MPNN em um conjunto de teste held-out (10% do split Tartarus, ou os 10.000 pontos de teste do…
- **e3** (HeE-MOEA, 2019): Sec. V-E.3 (Discussions); Fig. 1 do material suplementar (mencionada, não incluída neste… — Experimento adicional (Discussions, V-E.3) em que HeE e GP são treinados nos MESMOS 11N−1 dados para 4 problemas DTLZ, e então usados para prever f̂…
- **e64** (SA-MOPSO (PPD), 2025): Sec. 5.1.2, Fig. 10; Eq. 20 — No benchmark KUR, 5 execuções de SA-MOPSO com beta em {0.40, 0.50, 0.60, 0.70, 0.80} (cada uma com 50 iterações internas por 4 iterações externas)…
- **e7** (EDN-ARMOEA, 2022; roster): Sec. IV-D; resultados completos em Tables SV-SVII (Supplementary material, ausentes deste… — Comparação da acurácia de fitness (erro absoluto médio, MAE) e da capacidade de expressar incerteza (desvio-padrão médio da variância estimada σ̂²,…
- **e8** (NN-EGO, 2020): Table S9 (S20), Table S10 (S21), Figure S12 (S22) — Acompanha a acurácia (MAE, RMSE) do ANN multitarefa ao longo das 5 gerações de active learning por dois ângulos complementares: (a) erro "lookahead"…
- **jin3** (GS-MOMA / GSM (mono: GS-SOMA), 2010): Sec. IV-B-2, Fig. 5, Eq. (19) — Erro quadrático médio normalizado (N-RMSE) das predições de GP, PR, RBF e do modelo ensemble (M1) para cada um dos 10 problemas F1-F10, calculado… · Sec. IV-C-2, Fig. 7 — Igual à análise de N-RMSE do contexto SOO, mas para os 6 problemas MOO (MF1-MF6): N-RMSE de GP, PR, RBF e Ensemble (M1) na predição da função…
- **mtm4** (MAES (variante MO: M-NSGA-II), 2006): Sec. V-D, Fig. 16 (p.11) — Execução isolada de longo prazo (2000 avaliações reais) do PoI-MAES no problema elipsoide 20-D: plota, ao longo do nº de avaliações (escala log), o… · Sec. V-D/E, Fig. 25 (p.14) — Para uma única execução do PoI-MAES na função de Ackley (20-D, multimodal), o artigo compara, num gráfico de dispersão, o valor predito ŷ contra o…
- **wang4** (SA-NSGA-II, 2016): Sec. IV-B, Fig. 9 — Varre o nº de clusters K (o parâmetro de fidelidade do surrogate por redução de dados) e mede, contra uma execução de referência do NSGA-II com… · Sec. V-C2, Fig. 15 — [nova] Convergência dos parâmetros do modelo de regressão que estima o erro do surrogate (β1, β2)

**Complementos e correções (06/09/2026).** Como o corpus mede a média: RMSE/N-RMSE (c24, c45, jin3), MAE treino × validação (b13, c59), NLPD (b15), validação cruzada k-fold antes da busca (c50, e1 20-fold), MAE por geração (e8, e7). Quase sempre em um único instante; só e8 e c82 acompanham ao longo da busca — a sonda com pontos fixos re-preditos a cada retreino não aparece em nenhum dos 72.

**Score (0–10): 9.** **Justificativa.** F. C: 19/72 medem a acurácia da média (RMSE/MAE/NRMSE/CV; R2#10 16/38) — b2, b7, c24, c45, c50, e1, e3, e7, jin3 — quase sempre em UM instante (pré-busca ou fim), não ao longo do orçamento. P alta: 'o modelo aprende? esquece?' é a primeira dimensão da sonda e a premissa da lei do teto. V: cap. 4 l.450 (calibração via sonda). D: feita para os 8 do cache; decisão 11 (13 exige ③ do bucket). Núcleo do bloco E.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 7 artigos / 10 análises** — dos 38 iniciais: 3 · dos 7 do roster minerados agora: 2 · dos 27 complementares: 2 · artigos do roster (15): 4.

- **b15** (U-RankMOEA, 2026): Apendice E, Fig. 3 — Correlacao de postos (Spearman) entre o proxy de triagem barato e a contribuicao real de HV, para um pool grande de candidatos, comparando um proxy…
- **b4** (CSEA, 2019; roster): Sec. III-D, Fig. 7(a)-(b) — Compara, ao longo da busca em DTLZ1 3-objetivos, a taxa PREVISTA de soluções de categoria II (rp, saída do classificador FNN) com a taxa REAL (rr,… · Sec. III-D, Fig. 7(b)-(c)-(d) — Compara rp × rr (mesma medição da análise anterior, sempre COM o particionamento balanceado) em DTLZ1 com M=3, 5 e 10 objetivos, para investigar como…
- **c122** (θ-DEA-DP, 2022; roster): Sec. IV-D, Table VIII — Compara a acurácia (%) de classificação de dominância Pareto e θ dos classificadores Pareto-Net/θ-Net (FNN profunda com perda ponderada por classe)… · Table VIII, linha DTLZ4, colunas de acurácia de θ-dominância — Sub-achado dentro da Tabela VIII: no problema DTLZ4 (3 objetivos, espaço de busca enviesado), a acurácia de predição de θ-dominância do próprio θ-Net…
- **c217** (PC-SAEA, 2023; roster): Sec. 4.4, Table 5 — Comparação direta da acurácia de classificação dos 6 surrogates comparáveis (CPS-MOEA, K-RVEA, CSEA, EDN-ARMOEA, REMO, PC-SAEA — SOCEMO e HeE-MOEA… · Sec. 4.5, Fig. 9 — Acurácia de classificação do surrogate de PC-SAEA (medida pelo mesmo método da Seç. 4.4/Tabela 5) ao longo da fração do orçamento consumida, em DTLZ2…
- **e103** (IBEA-MS, 2023; roster): Sec. IV-A, Fig. 5 — Taxa de acerto ('correct rate') da seleção ambiental por geração: a proporção de indivíduos que a seleção baseada em Kriging (e, separadamente, a…
- **mtm4** (MAES (variante MO: M-NSGA-II), 2006): Sec. V-B (definição) e V-E (discussão), Figs. 17-24 (pp. 11-13) — Para os 4 problemas mono-objetivo sem restrição (esfera, elipsoide, degrau, Ackley) e os 4 critérios de pré-crivo (MI, LB, PoI, ExI), o artigo mede e…
- **wang4** (SA-NSGA-II, 2016): Sec. IV-B, Fig. 9 — Varre o nº de clusters K (o parâmetro de fidelidade do surrogate por redução de dados) e mede, contra uma execução de referência do NSGA-II com…

**Complementos e correções (06/09/2026).** O roster mede a própria classificação: b4 (rp prevista × rr real por geração), c122 (acurácia de Pareto/θ-dominância em 1000 exemplos; DTLZ4 é o pior), c217 (acurácia dos 6 surrogates comparáveis e ao longo da busca), e103 (correct rate da seleção ambiental por geração). Para a sonda dos CL a métrica de referência do corpus é acurácia (não AUROC).

**Score (0–10): 8.** **Justificativa.** N. C: 7/72 — e 4 do roster medem a acurácia do próprio classificador (b4 rp×rr, c122 Table VIII, c217 Table 5/Fig. 9, e103 correct rate), mais mtm4 e b15 (Spearman proxy×HV). P alta: para as classes CL/ordem é a ÚNICA medida de qualidade possível (não há σ), e o roster já a pratica. D: exige ③ classe/score (regime sonda) para b4/c122/c217/e103 — decisão 11. Entra como a metade 'classificador' da sonda.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 13 artigos / 18 análises** — dos 38 iniciais: 8 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 5 · artigos do roster (15): 1.

- **b15** (U-RankMOEA, 2026): Apendice I.4 (Eq. 40-42) — Validacao empirica da calibracao do classificador bayesiano de rank apos escalonamento de temperatura + MC-Dropout adaptativo, reportando ECE, MCE e… · Apendice O, Fig. 18 (legenda interna via OCR: 'Temperature scaling (ECE=0.009)',… — Diagrama de confiabilidade (reliability diagram) comparando visualmente a calibracao do escalonamento de temperatura contra a do MC-Dropout…
- **b7** (DR (Dual-Ranking), 2026): Sec. 4.2 (Surrogate Prediction Performance Results); Material Suplementar Sec. 1.2,… — Comparação da qualidade preditiva bruta dos 4 surrogates (GPR-RBF, GPR-Matérn, Autogluon-QR, BNN) nos 11 problemas, medida por MSE (acurácia da…
- **c24** (DTK-MODE, 2015): Sec. IV-A, Table II — Para o DTK especificamente, a Tabela II reporta o RMSE de ajuste à medida que o número de pontos de amostragem aumenta (via o processo de amostragem…
- **c250** (K-MOGA, 2008): Sec. 4.1.3, Fig. 7 (p. 031401-6 a 031401-7) — So para o exemplo ZDT2, numa unica geracao (a 10a) de uma execucao, o artigo compara, ponto a ponto para cada um dos individuos da populacao daquela…
- **c50** (PD-MOEA, 2018): Sec. 3.1, Fig. 2, p.8-9 — Os dois GPs independentes (G_UBC, G_NOx) são avaliados por validação cruzada 10-fold sobre os 654 pontos coletados: para cada ponto, a predição vem…
- **c59** (UA-DBO, 2026): Sec. 4.1.2, Table 2, p. 13–15 — Tabela (Tabela 2) comparando a QUALIDADE da incerteza calibrada entre o GS-ED proposto e um 'deep ensemble' clássico (n=3 e n=6 modelos… · Sec. 4.2, Fig. 9, p. 17–18 — Para a mesma execução da Fig. 8, o artigo plota (Fig. 9) o erro real do modelo contra a largura do intervalo de confiança de 90% predito, para cada… · Appendix B, p. 26–27 — [nova] Sensibilidade da calibração do σ aos hiperparâmetros de treino do modelo probabilístico (peso KL β, nº de amostras Nl)
- **c81** (UA-MORL-Diff, 2025): Sec. 4.2.1; definição em Appendix B.8.1; painéis em Appendix C.2, Fig. C.1–C.2 — Avalia a acurácia (R², via parity plots, Fig. C.1) e a calibração da incerteza (AUCE, via curvas de calibração/diagramas de confiabilidade, Fig. C.2)…
- **c97** (EnGP-MRO, 2011): Sec. 4.2 (eqs. 13-15); Sec. 6.3 [43], Figs. 15, 16, 17 — Para cada local de monitoramento (C1, C2, C3), o artigo constrói a função de distribuição cumulativa (CDF) empírica dos resíduos de predição do… · Sec. 6.3 [45]-[46], Tables 3 e 4 — Para as mesmas cinco soluções (agora obtidas pelas abordagens de múltiplas realizações e chance-constrained), o artigo tabula o resíduo (diferença…
- **e21** (PIO, 2025): Fig. 3; Results, 'Surrogate model and UQ performance' — Avalia a calibração do σ (incerteza total) do D-MPNN via curvas de calibração baseadas em confiança — a fração dos dados de teste cujo valor real cai… · Fig. 5; Results, 'Optimization results of single-objective task' — Mostra, para os top-50 candidatos SELECIONADOS por cada método (DOM/EI/PIO) em cada tarefa single-objective, o valor médio predito (μ) com barra de…
- **e7** (EDN-ARMOEA, 2022; roster): Sec. IV-D; resultados completos em Tables SV-SVII (Supplementary material, ausentes deste… — Comparação da acurácia de fitness (erro absoluto médio, MAE) e da capacidade de expressar incerteza (desvio-padrão médio da variância estimada σ̂²,…
- **e8** (NN-EGO, 2020): Algorithm S1 (S9), passos 4 e 13; Figure S4 (S10) — Descreve e ilustra a calibração paramétrica do modelo de incerteza da ANN: a cada geração, um modelo de erro heterocedástico ε(d) ~ N(0, σ1² +…
- **mtm4** (MAES (variante MO: M-NSGA-II), 2006): Sec. V-D/E, Fig. 26 (p.14) — Para a mesma execução do PoI-MAES em Ackley (Fig. 25), o artigo verifica a validade do limite inferior de confiança: plota y (valor real) contra y_lb…
- **wang4** (SA-NSGA-II, 2016): Sec. V-C2, Fig. 14 — Durante a otimização adaptativa (Kmax=1000, 20 execuções), registra a evolução de ER (o erro empírico REAL de aproximação, medido comparando a…

**Complementos e correções (06/09/2026).** Métricas de calibração vistas no corpus (Anexo 8.1): CICP/cobertura de IC (b7, c59, mtm4 LB ω = 2), ECE/MCE/ACE (b15, c59), AUCE (c81), CDF empírica dos resíduos (c97), curvas de calibração por confiança (e21), erro × largura do intervalo (c59, c24), ER empírico (wang4), 'magnitude' do σ (e7). Ressalvas literais dos autores sobre σ mal calibrado: c59 ('poorly calibrated' sem KL), b15 (ECE piora com K ≥ 6), e21 (métodos de UQ falham por dataset), c29 (viés do campo gaussiano em paisagem plana).

**Score (0–10): 10.** **Justificativa.** F-parcial. C: 13/72 medem calibração/cobertura/σ×erro de alguma forma (b7 CICP, b15 ECE, c59 ECE+cobertura, c81 AUCE, c97 CDF dos resíduos, e21 curvas de calibração, e8, mtm4, wang4 ER) — 19/72 medem ALGUMA qualidade da incerteza (Anexo 8.1) mas raríssimos ao longo da busca e nenhum com sonda fixa. P máxima: é A pergunta do título (a incerteza reportada é confiável?). V: cap. 4 l.450 promete a calibração via sonda — vinculante. D: feita para 8; decisão 11. Núcleo do capítulo.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 3 artigos / 4 análises** — dos 38 iniciais: 1 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 2 · artigos do roster (15): 0.

- **c59** (UA-DBO, 2026): Sec. 4.2, Fig. 9, p. 17–18 — Para a mesma execução da Fig. 8, o artigo plota (Fig. 9) o erro real do modelo contra a largura do intervalo de confiança de 90% predito, para cada…
- **e3** (HeE-MOEA, 2019): Sec. V-E.3 (Discussions); Fig. 1 do material suplementar (mencionada, não incluída neste… — Experimento adicional (Discussions, V-E.3) em que HeE e GP são treinados nos MESMOS 11N−1 dados para 4 problemas DTLZ, e então usados para prever f̂…
- **e8** (NN-EGO, 2020): Figure S7 (S14) — Testa se o proxy de incerteza de cada modelo (desvio-padrão posterior do GP; distância média aos 10 vizinhos de treino mais próximos no espaço… · Figure S9 (S15) — Repete a análise de discriminação por exclusão de pontos incertos da Figura S7, agora no conjunto extrapolativo fora de distribuição (107 complexos…

**Complementos e correções (06/09/2026).** Protocolo de e8 (Fig. S7/S9): excluir os pontos mais incertos e medir se o erro cai — é uma discriminação operacional, replicável com ③ + gabarito S. c59 (Fig. 9): erro real × largura do intervalo.

**Score (0–10): 8.** **Justificativa.** N. C: 3/72 (c59 erro × largura do intervalo; e3; e8 'excluir os incertos reduz o erro?'). P alta: discriminação é o que o critério de aquisição precisa (σ grande onde o erro é grande), independente da calibração absoluta; e8 dá o protocolo (excluir os k% mais incertos e medir o MAE). D barata dado ③ (AUROC/correlação σ × |μ−f| por retreino). Entra junto com 33 (mesma figura, segundo painel).


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 1 artigos / 1 análises** — dos 38 iniciais: 0 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 1 · artigos do roster (15): 0.

- **e8** (NN-EGO, 2020): Table S9 (S20), Table S10 (S21), Figure S12 (S22) — Acompanha a acurácia (MAE, RMSE) do ANN multitarefa ao longo das 5 gerações de active learning por dois ângulos complementares: (a) erro "lookahead"…

**Score (0–10): 6.** **Justificativa.** N. C: 1/72 (e8 acompanha MAE/RMSE por geração). P média: é a síntese qualitativa de 31–34 (aprende / plana / degenera) — útil como tipologia no texto, não como análise separada. D: derivada. Entra como parágrafo classificando os 8–13 algoritmos.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 6 artigos / 10 análises** — dos 38 iniciais: 3 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 3 · artigos do roster (15): 1.

- **b7** (DR (Dual-Ranking), 2026): Sec. 4.2 (Surrogate Prediction Performance Results); Material Suplementar Sec. 1.2,… — Comparação da qualidade preditiva bruta dos 4 surrogates (GPR-RBF, GPR-Matérn, Autogluon-QR, BNN) nos 11 problemas, medida por MSE (acurácia da…
- **c97** (EnGP-MRO, 2011): Sec. 6.1 [38], Figs. 4, 5, 6 — [nova] RMSE individual dos membros do ensemble por saída (variabilidade entre bootstraps) · Sec. 6.1 [38]-[39], Fig. 7 — [nova] RMSE do ensemble agregado em função do número de membros (C1) · Sec. 6.1 [39], Figs. 8, 9, 10 — [nova] Convergência da incerteza (CV do RMSE) com o tamanho do ensemble — escolha de N=30
- **e3** (HeE-MOEA, 2019): Sec. V-E.3 (Discussions); Fig. 1 do material suplementar (mencionada, não incluída neste… — Experimento adicional (Discussions, V-E.3) em que HeE e GP são treinados nos MESMOS 11N−1 dados para 4 problemas DTLZ, e então usados para prever f̂…
- **e7** (EDN-ARMOEA, 2022; roster): Sec. IV-D; resultados completos em Tables SV-SVII (Supplementary material, ausentes deste… — Comparação da acurácia de fitness (erro absoluto médio, MAE) e da capacidade de expressar incerteza (desvio-padrão médio da variância estimada σ̂²,…
- **e8** (NN-EGO, 2020): Figure S7 (S14) — Testa se o proxy de incerteza de cada modelo (desvio-padrão posterior do GP; distância média aos 10 vizinhos de treino mais próximos no espaço… · Figure S9 (S15) — Repete a análise de discriminação por exclusão de pontos incertos da Figura S7, agora no conjunto extrapolativo fora de distribuição (107 complexos…
- **jin3** (GS-MOMA / GSM (mono: GS-SOMA), 2010): Sec. IV-B-2, Fig. 5, Eq. (19) — Erro quadrático médio normalizado (N-RMSE) das predições de GP, PR, RBF e do modelo ensemble (M1) para cada um dos 10 problemas F1-F10, calculado… · Sec. IV-C-2, Fig. 7 — Igual à análise de N-RMSE do contexto SOO, mas para os 6 problemas MOO (MF1-MF6): N-RMSE de GP, PR, RBF e Ensemble (M1) na predição da função…

**Complementos e correções (06/09/2026).** Comparações entre tipos de surrogate na qualidade da incerteza: b7 (GPR-RBF, GPR-Matérn, Autogluon-QR, BNN), e7 (EDN × GP × HeE: σ da EDN mais informativo), e3 (HeE × GP nos mesmos dados), e8 (GP × ANN: GP nunca vence a extrapolação), c97 (ensemble: CV do RMSE estabiliza em 30 membros). Nenhum agrupa por classe de medição.

**Score (0–10): 8.** **Justificativa.** N. C: 6/72 (b7 4 surrogates; c97 ensemble; e3 HeE×GP; e7 EDN×GP×HeE; e8 GP×ANN; jin3) comparam a qualidade da incerteza entre tipos de modelo — mas nenhum por CLASSE de medição, que é o eixo do cap. 3. P alta: 'a qualidade do σ depende de onde o número vem' é a validação empírica do eixo de medição da taxonomia — contribuição própria e defensável (mais que 20). D: 33 agrupada. Entra como a leitura de fechamento do bloco E.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 2 artigos / 2 análises** — dos 38 iniciais: 2 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 0 · artigos do roster (15): 0.

- **c45** (GP-DGS, 2024): Sec. 2.2 (definição da métrica) e Table 1, Sec. 3 Results and Discussion — Tabela 1: o artigo reporta o erro quadrático médio normalizado (NRMSE) entre as predições dos GPs e os valores 'verdadeiros' calculados por SEAWAT,…
- **c81** (UA-MORL-Diff, 2025): Sec. 4.2.1; definição em Appendix B.8.1; painéis em Appendix C.2, Fig. C.1–C.2 — Avalia a acurácia (R², via parity plots, Fig. C.1) e a calibração da incerteza (AUCE, via curvas de calibração/diagramas de confiabilidade, Fig. C.2)…

**Score (0–10): 6.** **Justificativa.** N. C: 2/72 (c45 NRMSE por objetivo; c81 por propriedade). P média: 'agregação silenciosa de m sigmas' é uma observação fina (b15 mostra LMC piorando; c106 GP dependente não ajuda — Anexo 8.4), mas só rende quando os objetivos diferem em escala/dificuldade. D: ③ por objetivo. Entra como parágrafo de 33 se os dados mostrarem assimetria; senão apêndice.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 3 artigos / 5 análises** — dos 38 iniciais: 3 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 0 · artigos do roster (15): 0.

- **b15** (U-RankMOEA, 2026): Apendice E.1, Fig. 5 — Corte unidimensional da incerteza preditiva (media, banda epistemica, banda aleatoria) numa fatia do problema DTLZ2-100D, ilustrando como a banda… · Apendice K, Fig. 13 — Evolucao media da incerteza epistemica e aleatoria do Deep GP ao longo da otimizacao em DTLZ2-100D, mostrando a incerteza epistemica caindo a medida…
- **c107** (MS-VHGP-EIHV, 2017): Sec. IV, Figs. 25-26 — Estudo de caso no robô-cobra físico real (sidewinding gait): compara as frentes de Pareto (velocidade x estabilidade de cabeça) obtidas pelo método… · Sec. IV, Table II — Verificação empírica direta da heterocedasticidade no robô real: escolhe 3 pontos fixos do espaço de entrada (x1=[0.7177,0.3569], x2=[0.5634,0.0538],…
- **c82** (TC-SAEA, 2022): Sec. 4.7 (Effects of the Co-surrogate); Figs. S1 e S2 (material suplementar, não incluído… — Roda TC-SAEA em cada instância biobjetivo DTLZ (10 execuções independentes, FEs_max_s=200) e calcula, a cada geração, o erro quadrático médio (MSE)…

**Score (0–10): 5.** **Justificativa.** N. C: 3/72 (b15 bandas epistêmica/aleatória; c107 mede heterocedasticidade no robô real; c82). P média: interessante para 'onde o modelo erra', mas exige regionalização do espaço (por quadrante/distância ao ND) e a bateria é sem ruído (a heterocedasticidade aqui é do erro do modelo, não do ruído). Apêndice ou cair.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 1 artigos / 1 análises** — dos 38 iniciais: 1 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 0 · artigos do roster (15): 0.

- **c24** (DTK-MODE, 2015): Sec. IV-B, Table III — No problema real TEAM 22 (SMES, D=8, M=2), a Tabela III compara, ao longo de configurações do DTK com números crescentes de pontos de amostragem…

**Score (0–10): 7.** **Justificativa.** N. C: 1/72 explícito (c24), mas 71 passagens de equivalência de critérios / modelo como limitante minadas nos 72 (Anexo 8.4: 'imperfect model', 'hardly any difference', 'the dependence GP model appears to offer little advantage') sustentam a hipótese. P alta (P-1, decisão 10). D: cruza 31/33 com o endpoint — correlação delicada (n pequeno, confundida por família). Recomendo formular como hipótese antes dos resultados e testar com uma figura (qualidade do modelo × Δ vs piso); não como 'lei'.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 6 artigos / 8 análises** — dos 38 iniciais: 1 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 5 · artigos do roster (15): 0.

- **c59** (UA-DBO, 2026): Sec. 4.2, Table 3, p. 15–16 — Tabela final (Tabela 3) comparando os 3 frameworks (CFD-based, DBO, UA-DBO) nos 3 casos de divergência de arrasto (A1, A2, A3): para DBO/UA-DBO,… · Appendix C.4.1, Table 5, p. 30–31 — Tabela (Tabela 5) reportando o MAE do coeficiente de sustentação de início de buffet (C_L,buffet) nas populações finais de DBO e UA-DBO, para os 6…
- **e21** (PIO, 2025): Fig. 5; Results, 'Optimization results of single-objective task' — Mostra, para os top-50 candidatos SELECIONADOS por cada método (DOM/EI/PIO) em cada tarefa single-objective, o valor médio predito (μ) com barra de…
- **e64** (SA-MOPSO (PPD), 2025): Sec. 5.2.1, Figs. 12-13 — Nas primeiras iterações do Run A (desenho inicial concentrado perto de salinidade 0 g/L, incapaz de capturar a sensibilidade real da salinidade a…
- **e8** (NN-EGO, 2020): Table S9 (S20), Table S10 (S21), Figure S12 (S22) — Acompanha a acurácia (MAE, RMSE) do ANN multitarefa ao longo das 5 gerações de active learning por dois ângulos complementares: (a) erro "lookahead"…
- **f9** (UA-IBEA (sigla não-oficial, proposta por mim; paper não nomeia — "Approach 1/2/3"), 2019): Sec. 4, Fig. 3, p. 470 — Para os casos biobjetivo (k=2) sob amostragem LHS, a Fig. 3 traz o RMSE entre os valores das soluções finais e seus valores verdadeiros, para cada…
- **mtm4** (MAES (variante MO: M-NSGA-II), 2006): Sec. V-D, Fig. 16 (p.11) — Execução isolada de longo prazo (2000 avaliações reais) do PoI-MAES no problema elipsoide 20-D: plota, ao longo do nº de avaliações (escala log), o… · Sec. V-D/E, Fig. 25 (p.14) — Para uma única execução do PoI-MAES na função de Ackley (20-D, multimodal), o artigo compara, num gráfico de dispersão, o valor predito ŷ contra o…

**Score (0–10): 7.** **Justificativa.** F. C: 6/72 (c59 fantasia 'acreditada' vs CFD; e21 top-50 selecionados; e64; e8; f9 RMSE das finais; mtm4). P alta: 'quem acredita demais no próprio modelo' é a leitura do σ pelo lado do risco. D: feita para o cache. Entra como figura por terço; 41 é a versão cara, 42 a versão offline.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 5 artigos / 5 análises** — dos 38 iniciais: 3 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 2 · artigos do roster (15): 2.

- **b5** (Prob-RVEA / Prob-MOEA/D (+ Hyb-RVEA / Hyb-MOEA/D), 2022; roster): Sec. IV-A, Fig. 10 — Três curvas, da mesma execução com HV mediano, ao longo de FE (checkpoints a cada 1000 avaliações, até 40000, na instância DBMOPP P1 K=5/LHS): (a) HV…
- **c250** (K-MOGA, 2008): Sec. 4.1.2, Fig. 6 (p. 031401-6 a 031401-7) — So para o exemplo ZDT2, o artigo compara, geracao a geracao ao longo de uma execucao, a MMD_fm (a distancia minima entre os conjuntos nao-dominado e…
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF), 2021; roster): Apendice J, Fig. 19 — Recomputacao do desempenho dos metodos principais usando uma definicao alternativa de 'resposta do algoritmo': em vez do conjunto nao-dominado bruto…
- **c59** (UA-DBO, 2026): Sec. 4.2, Fig. 8, p. 16–17 — Para cada um dos 3 casos, uma execução (dentre as 5) é selecionada para plotar a convergência do objetivo ao longo das 50 iterações (Fig. 8): a curva…
- **e64** (SA-MOPSO (PPD), 2025): Sec. 5.2.1, Figs. 12-13 — Nas primeiras iterações do Run A (desenho inicial concentrado perto de salinidade 0 g/L, incapaz de capturar a sensibilidade real da salinidade a…

**Score (0–10): 6.** **Justificativa.** N. C: 5/72 (b5 curvas por FE, c250 geração a geração, c262 'resposta alternativa', c59, e64). P: mesma de 40 com granularidade geracional (② + ③ + ①); custo alto (join por geração) para ganho marginal sobre 40. Apêndice ou uma execução mediana ilustrativa.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 5 artigos / 7 análises** — dos 38 iniciais: 4 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 1 · artigos do roster (15): 0.

- **b7** (DR (Dual-Ranking), 2026): Sec. 4.4 (Comparison Experiments with Baseline Methods), Table 2; Sec. 4.1 (Performance… — Tabela final de comparação com os 5 baselines nos 8 problemas não-restringidos, dataset limitado (11D-1): MSE, IGD+ e HV por algoritmo x problema,… · Material Suplementar, Sec. 1.4 (Comparative Analysis against Baselines), Table 9 — A mesma tabela final de comparação com baselines (MSE, IGD+, HV por algoritmo x problema, 8 problemas não-restringidos), repetida com os surrogates…
- **c45** (GP-DGS, 2024): Fig. 2 e Sec. 3 Results and Discussion; anotações de PPO na Fig. 2 (ANEXO — OCR, Página 2) — Figura 2: o artigo apresenta os conjuntos Pareto-ótimos (POPS) obtidos em cada cenário de treino (T1–T4) no espaço de objetivos (Qp vs. fOC), com…
- **c59** (UA-DBO, 2026): Appendix C.4.1, Fig. 4, p. 30 — Para os 6 casos do problema de buffet onset (Apêndice C), o artigo plota a frente não-dominada ACREDITADA pelo modelo (população final, avaliada só…
- **c97** (EnGP-MRO, 2011): Sec. 6.3 [45], Table 2 — Para cinco soluções ótimas selecionadas em diferentes regiões da fronteira de Pareto obtida com o surrogate único (sem ensemble), o artigo reavalia… · Sec. 6.3 [45]-[46], Tables 3 e 4 — Para as mesmas cinco soluções (agora obtidas pelas abordagens de múltiplas realizações e chance-constrained), o artigo tabula o resíduo (diferença…
- **f9** (UA-IBEA (sigla não-oficial, proposta por mim; paper não nomeia — "Approach 1/2/3"), 2019): Sec. 4, Fig. 3, p. 470 — Para os casos biobjetivo (k=2) sob amostragem LHS, a Fig. 3 traz o RMSE entre os valores das soluções finais e seus valores verdadeiros, para cada…

**Complementos e correções (06/09/2026).** Os offline fazem exatamente isto: b7 (MSE + IGD+ + HV das soluções reavaliadas), c59 (frente acreditada × verificada por CFD), c97 (5 soluções da frente reavaliadas: Tables 2–4), f9 (RMSE das finais). É a leitura padrão do offline — a ⑦ nasceu para ela.

**Score (0–10): 8.** **Justificativa.** N; barata (③ + ⑦). C: 5/72 — e são os offline: b7 (MSE/IGD+/HV), c45, c59 (frente acreditada × verificada), c97 (5 soluções reavaliadas), f9. P alta: no offline a fantasia é o único risco e a ⑦ mede exatamente |ND acreditado| vs |ND real|. Entra no bloco offline (13/14) como a figura da fantasia.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 4 artigos / 5 análises** — dos 38 iniciais: 2 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 2 · artigos do roster (15): 1.

- **e17** (MOBO, 2021): Sec. IV-A, Fig. 7(c) — Ainda no problema AWA, o artigo mostra a projecao 2D do front (dE vs. epsilon_x) obtida so pelo MOBO em 100, 200 e 500 observacoes (execucao unica),…
- **e21** (PIO, 2025): Fig. 4; Results, 'Optimization results of single-objective task' — [nova] Distribuição do valor real dos top-K por método vs. corte
- **e64** (SA-MOPSO (PPD), 2025): Sec. 5.1.1, Table 2, Fig. 8, Fig. 9 — Para cada uma das 3 funções de benchmark (KUR, ZDT, OSY), SA-MOPSO (assistido por GPR) e PB-MOPSO (a mesma MOPSO rodando direto sobre a função… · Sec. 5.2.2, Table 4, Fig. 14 — Além do Run A (desenho inicial 100% inviável), um Run B usa uma população inicial 100% viável as restrições simples (100 de 25.200 vetores gerados…
- **e7** (EDN-ARMOEA, 2022; roster): Sec. IV-D; Fig. S1 (Supplementary material, ausente deste corpus — achado descrito em… — Número de soluções que contribuíram para a melhoria do IGD (soluções não-dominadas/relevantes no momento em que foram avaliadas) versus número de FEs…

**Score (0–10): 7.** **Justificativa.** F. C: 4/72 (e7 conta 'soluções que contribuíram', e17, e21, e64). P alta: 'quanto do orçamento de busca vira fronteira' é a utilidade do infill — a métrica de decisão por FE. D pronta (① solution_id + ND). Entra como coluna/figura de 44/45.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 8 artigos / 10 análises** — dos 38 iniciais: 4 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 4 · artigos do roster (15): 1.

- **b1** (ParEGO, 2006; roster): Sec. VIII, p. 63–64; Fig. 10 — Para uma única execução de cada algoritmo na função OKA1 (após 250/260 avaliações), plota-se lado a lado os pontos visitados no espaço de decisão…
- **c105** (SMS-EGO, 2008): Fig. 1, p. 788 — Figura 1 ilustra esquematicamente os 3 casos do criterio de fitness interno do SMS-EGO (solucao nao-epsilon-dominada, epsilon-dominada, e dominada)…
- **c106** (EMMI (EMmI), 2016): Sec. 6.1 (MOP2 Function), Fig. 3, p. 17 — Para o MOP2, plota os pontos sequencialmente adicionados por cada criterio (CWPI, EMMI, PI) sobre a frente de Pareto verdadeira, separadamente para o…
- **e17** (MOBO, 2021): Sec. III-D, Fig. 5 — Ainda na Eq. 5 (2D, 2 objetivos), partindo dos mesmos 5 pontos aleatorios, o artigo roda 25 iteracoes com UCB-HVI padrao e depois repete com… · Sec. IV-C, Fig. 9(a-b) — No problema AWA, o artigo compara a trajetoria do parametro K1 (forca do Solenoide 1) ao longo de 300 observacoes e a distribuicao de delta-K1 por…
- **e4** (TSEMO, 2018): Sec. 7, Fig. 4 — Antes dos experimentos numericos, o artigo mostra passo a passo, num problema-brinquedo 1D biobjetivo (funcao de Schaffer No. 1, x em [-10,10]), como…
- **e8** (NN-EGO, 2020): Text S3 (S35); Tables S13-S14 (S33); Figures S20-S21 (S31-S32) — [nova] Sobre-amostragem pelo E[I] de regiões estruturais de baixa taxa de conversão · Figure S13 (S23) — [nova] Distribuição de metais entre candidatos tentados e convergidos por geração
- **mtm6** (EHVI (EI_H) / "EHVI-EGO", 2011): Sec. V-A (Numerical Experiment), parágrafo 'Result' (item c) — Na mesma execução única do Algoritmo 1 (Sec. V-A), o artigo descreve textualmente a ordem/geometria em que os pontos de infill são escolhidos: nas…
- **pp6** (AB-MOEA, 2020): Sec. 3.2, Fig. 3 — Exemplo ilustrativo (não sistemático — 1 problema, 1 modelo GP, 2 instantes) mostrando os 5 novos pontos escolhidos pela AF proposta versus os 5…

**Score (0–10): 6.** **Justificativa.** N. C: 8/72 (b1 Fig. 10, c105, c106, e17, e4, e8 'sobre-amostragem de regiões de baixa conversão', mtm6, pp6) — quase sempre ilustrativo, 1 execução. P alta em princípio (exploração × explotação é o que a incerteza controla), mas exige ⑥/③ e uma definição operacional de 'exploração' (distância ao ND acreditado). Entra se 45 for feita (mesmo insumo); senão apêndice.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 14 artigos / 17 análises** — dos 38 iniciais: 6 · dos 7 do roster minerados agora: 1 · dos 27 complementares: 7 · artigos do roster (15): 4.

- **b13** (AdaMoR-DDMOEA, 2025): Sec. 5.5.2, Figure 6 — Sensibilidade do MAE (do surrogate escolhido) ao número k de folds usado na validação cruzada que decide a seleção adaptativa de modelo — o parâmetro…
- **b3** (K-RVEA, 2018; roster): Sec. III-C.1 (definição do mecanismo, Algorithm 3); Sec. IV-B, penúltimo parágrafo… — Análise de sensibilidade do parâmetro δ (Algoritmo 3), que é o GATE que decide se os indivíduos para reavaliação/retreino são escolhidos pela…
- **b7** (DR (Dual-Ranking), 2026): Sec. 4.3 (Ablation Study and Sensitivity Analysis), Table 1; Material Suplementar Sec.… — Estudo de ablação e sensibilidade no dataset limitado (11D-1 amostras): para cada um dos 4 surrogates (GPR-RBF, GPR-Matérn, Autogluon-QR, BNN),…
- **b8** (KTA2, 2021): Sec. IV-D, Fig. 9 — Para os mesmos quatro problemas do estudo de ablação (DTLZ1, DTLZ2, DTLZ4, WFG5, M=3), o artigo conta quantas vezes cada uma das três estratégias de…
- **c217** (PC-SAEA, 2023; roster): Sec. 4.5, Fig. 8 — Sensibilidade de PC-SAEA ao parâmetro δ (limiar de confiabilidade que decide entre usar diretamente, usar invertido, ou ignorar o surrogate), varrido…
- **c250** (K-MOGA, 2008): Sec. 3.2 (Predicted Error for Constraint Functions), p. 031401-3 a 031401-4 — Na definicao do criterio de aceitacao para restricoes (Eq. 13), o artigo relata ter testado, alem do multiplicador padrao de 2x o desvio-padrao do…
- **c267** (SAMOEA-TL2M, 2025): Sec. IV-D-1 (texto); Supplementary Sec. V (não incluído neste corpus) — SÓ MENCIONADA (Regra 3 do cartão): dentro da mesma subseção da Tabela V, o artigo menciona um estudo — sem reproduzir números ou a tabela/figura no… · Sec. IV-B (menção); Supplementary Sec. III (não incluído neste corpus) — SÓ MENCIONADA (Regra 3 do cartão): o artigo aponta que o limiar α (que decide se o primeiro ou o segundo nível é acionado a cada iteração — ARI ≥ α…
- **c65** (SABBa, 2022): Sec. 6.3, Figs. 16-20 — SABBa SA-CS é aplicado ao projeto de um sistema de proteção térmica (TPS) de reentrada atmosférica (Stardust/TACOT, modelo PATO): MONO-objetivo…
- **e103** (IBEA-MS, 2023; roster): Sec. IV-A, Fig. 4 — Curvas de IGD média (±1 desvio-padrão sombreado, 30 execuções) ao longo das iterações no problema ZDT4 (D=10), comparando K-IBEA, R-IBEA, IBEA-MS e…
- **e64** (SA-MOPSO (PPD), 2025): Sec. 5.1.2, Fig. 10; Eq. 20 — No benchmark KUR, 5 execuções de SA-MOPSO com beta em {0.40, 0.50, 0.60, 0.70, 0.80} (cada uma com 50 iterações internas por 4 iterações externas)… · Sec. 5.1.3, Fig. 11; Eq. 17 — No benchmark OSY (6 restrições, todas emuladas), 4 execuções de SA-MOPSO com lambda_m em {0.10, 0.25, 0.40, 0.50} (limiar de probabilidade de…
- **e7** (EDN-ARMOEA, 2022; roster): Sec. IV-F.5; Fig. S7 (Supplementary material, ausente deste corpus — achado descrito em… — Sensibilidade da FREQUÊNCIA média com que o critério de diversidade/incerteza é acionado (isto é, quantas vezes o ramo 'usar σ para selecionar' é…
- **jin3** (GS-MOMA / GSM (mono: GS-SOMA), 2010): Sec. IV-B-2, Fig. 6, Eq. (20) — Melhoria de fitness normalizada atribuída à busca local via M1 (ensemble) versus M2 (PR de suavização) durante as buscas do GS-SOMA, para os 10… · Sec. IV-C-2, Fig. 8, Table I, Algorithm 5 — Razão Gamma entre arquivamento (novas soluções não-dominadas guardadas em Al) e substituição (Lamarckian replacement), derivada das 6 ações possíveis…
- **mtm4** (MAES (variante MO: M-NSGA-II), 2006): Sec. V-D, Fig. 15 (p.11) — Estudo de sensibilidade paramétrica na função de Ackley (20-D): o artigo varia o fator de confiança ω (0, 1, 2, 3) do critério de limite inferior (LB…
- **wang4** (SA-NSGA-II, 2016): Sec. V-C2, Fig. 16 — Compara, na mesma otimização adaptativa (Kmax=1000), o número de vezes que K é alterado COM e SEM o controle de suavidade (CS: limita a redução…

**Complementos e correções (06/09/2026).** O corpus conta acionamentos: b8 (quantas vezes cada uma das 3 estratégias foi escolhida, Fig. 9), e7 (frequência do critério de diversidade/incerteza, Fig. S7), wang4 (nº de mudanças de K com/sem controle), jin3 (razão arquivamento × substituição), b3 e c217 (δ como gate), mtm4 (ω). Os 15 blocos-roster (Anexo 8.6) trazem, por algoritmo, o mecanismo próprio, o parâmetro que o governa e a camada que o reproduz — é o roteiro do parser do ⑥.

**Score (0–10): 8.** **Justificativa.** N. C: 14/72 — e o roster faz isso sobre si mesmo: b3 (δ liga/desliga a incerteza), b8 (conta quantas vezes cada estratégia foi escolhida), c217 (δ do gate), e7 (frequência de acionamento do critério de incerteza), wang4 (nº de mudanças de K), jin3, mtm4 (ω). Os 15 blocos-roster (Anexo 8.6) listam os parâmetros do uso da incerteza — a tabela de 66. P máxima: 'o mecanismo em ação' é a evidência direta do USO explícito (título da dissertação) e o substituto natural do contrafactual. D: ⑥ existe para todos, mas o parser é por algoritmo (eventos heterogêneos) — custo médio-alto. Recomendo fazer para 4–6 algoritmos com gate/contagem clara (b3, b4, c217, e7, c141, e74) e declarar o resto.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 12 artigos / 13 análises** — dos 38 iniciais: 8 · dos 7 do roster minerados agora: 2 · dos 27 complementares: 2 · artigos do roster (15): 5.

- **b14** (SA²-MOEA, 2024): Sec. 4.7, Table 7 — Análise TEÓRICA (não medida empiricamente) de complexidade de tempo e de espaço, decomposta em três fases (construção do modelo, busca assistida por…
- **b15** (U-RankMOEA, 2026): Apendice N.1, Table 14 e Table 15; Sec. 4.4, Fig. 14 — Comparacao de tempo de parede (total e por iteracao) entre U-RankMOEA e 6 baselines (CPS-MOEA, K-RVEA, CSEA, EDN-ARMOEA, MCEA/D, CLMEA) em 3 cenarios… · Apendice L.3 — No estudo de escalabilidade estendida (D=500, M=5), o artigo reporta como o tempo de parede por iteracao cresce ao ir de 200D para 500D, e como a…
- **b2** (MOEA/D-EGO, 2010): Sec. VII-E-2 (FuzzyCM Versus One Single Model); Table III; Fig. 9(a)–(d) — Para medir o custo-benefício da FuzzyCM (a técnica de clusterização fuzzy usada pelo MOEA/D-EGO para conter o custo do GP), os autores treinam também…
- **b3** (K-RVEA, 2018; roster): Sec. II-B (motivação teórica, O(n³)); Sec. IV-B; Fig. 9 — Compara o tempo de treinamento do Kriging/surrogate (segundos) em função do número de avaliações/amostras de treino acumuladas, para K-RVEA, ParEGO,…
- **b4** (CSEA, 2019; roster): Sec. IV-F, Fig. 11 — Compara o tempo de execução (wall-clock, segundos) acumulado versus o número de avaliações, para CSEA, CPS-MOEA, ParEGO, MOEA/D-EGO e K-RVEA…
- **c1** (BS-MOBO, 2018): Sec. III-A-1, Fig. 3 — O artigo compara o tempo de treinamento (fit) do Gaussian Process e da rede neural bayesiana (BNN, com MC dropout), com e sem incorporação de…
- **c131** (MORBO, 2022): Apendice E ('Complexity improvements from local modeling'), E.1; Fig. 7; Fig. 8 — Caracteriza empiricamente como a modelagem LOCAL do MORBO evita a parede cubica do GP: numero de pontos por TR, fracao de pontos de uma TR que foram…
- **c141** (MMRAEA, 2025; roster): Sec. Runtime comparison, Fig. 9 — Tempo médio de execução (runtime) de CPS-MOEA, MOEA/D-RBF, EDN-ARMOEA, MCEA/D e MMRAEA em DTLZ2 (3-obj), nas 4 dimensões (20,40,60,100), com…
- **c50** (PD-MOEA, 2018): Sec. 5, p.14-15 (parágrafo após Fig. 3) — O artigo relata o tempo de treino de cada GP (feito uma única vez, <10s) e descreve analiticamente o custo de avaliação subsequente (produto escalar…
- **e3** (HeE-MOEA, 2019): Sec. V-D, Fig. 6 — Curvas do tempo MÉDIO de treino do surrogate versus o número de variáveis de decisão, para quatro problemas de exemplo (DTLZ2, DTLZ3, WFG2, WFG3),…
- **e7** (EDN-ARMOEA, 2022; roster): Fig. 3 (a-h); DTLZ7 — Tempo de treino do surrogate e tempo total de otimização por execução, medidos em segundos, versus d∈{20,40,60,100} (m=3) e versus m∈{3,5,10,20}…
- **e74** (CLMEA, 2023; roster): Sec. IV-G; Fig. 12 (bi-objetivo 200D DTLZ1) — Análise teórica da complexidade computacional de treino/predição do RBF e PNN contra a complexidade O(n³) do Kriging (símbolos exatos das fórmulas…

**Complementos e correções (06/09/2026).** O corpus mede tempo de treino × n ou × D: b3 (Fig. 9), b4 (Fig. 11), c1 (GP × BNN, Fig. 3), c131 (local × global), e3 (Fig. 6), e7 (Fig. 3), e74 (RBF/PNN × O(n³)), b15 (por iteração). A 'parede' O(n³) é citada como motivação em b3, c131, e74, e103.

**Score (0–10): 8.** **Justificativa.** F. C: 12/72 (b3 O(n³), b4, c1 GP×BNN, c131 'parede cúbica', c141, e3, e7, e74 do roster/entorno). P alta: a parede do retreino é o custo que a incerteza (GP) cobra — cap. 1 'contribuição de medida'. D feita (④ tempo_fit_s). Entra como figura (tempo de ajuste × n acumulado por família de surrogate).



### 71. Ilustração didática: o mapa μ/σ do surrogate e a paisagem da aquisição sobre o espaço de decisão (D = 2)

**Fontes.** [MIN] 12 análises em 10 artigos (lista abaixo) · [PL-38] R2#17 (3/38) · [CD] ③ regime `sonda` (2.000 pontos Sobol, f verdadeiro em S) · problemas com D = 2 na bateria (MMF1, MMF4).

**O que analisa.** A figura que mostra, para uma execução e um instante, a média predita, a incerteza e (quando possível) o critério de aquisição sobre todo o espaço — c238 (contornos EI × EIM), emo1 (paisagem do infill com σ fixo), mtm6 (μ, σ e EI_H após 25 iterações), e17 (mapas de calor μ × verdade), c24 (superfície predita × real), e9 e c154 (curvas de nível em brinquedo), c1 (BNN com/sem gradiente em 1D), c241 (exemplo numérico do conflito entre EIs), c29 (localização pelo limiar).

**Dados.** ③ (regime sonda: μ/σ ou score dos 2.000 pontos, por retreino, `fe_treino_max`); S (f verdadeiro nos mesmos pontos); ① (pontos avaliados até o instante); ⑥ (ponto escolhido).

**Objetivo.** Dar ao leitor a intuição do que a sonda mede antes das curvas agregadas (31–34): onde o modelo acerta, onde o σ é grande, onde o algoritmo foi buscar.

**O que busca revelar.** Se o σ é grande longe dos dados e pequeno perto (comportamento GP), se o classificador acerta a região certa, e se o infill cai onde σ é alto (exploração) ou onde μ é bom (explotação) — a versão visual de 44.

**Como é realizada.** Para MMF1 e MMF4 (D = 2), 2–3 algoritmos com μ/σ (b3, c238, c262) e 1 com classe (b4/c217): painéis μ, σ, |μ − f| e pontos avaliados, em 3 retreinos (início, meio, fim) da execução mediana; interpolação dos 2.000 pontos Sobol para o mapa.

**Técnicas.** Interpolação/scatter dos pontos da sonda; mapas de calor; execução mediana; sem estatística (é ilustração).

**Implementação.** Novo bloco no notebook §6 (sonda): filtrar ③ por problema ∈ {MMF1, MMF4}, regime = sonda, e três valores de `fe_treino_max`; juntar com S; `tricontourf`. Uma figura por algoritmo escolhido; o resto no repositório (56).

**Em quantos artigos aparece (dos 72).** 10 artigos (12 análises): dos 38 iniciais 6, dos 7 do roster 1, dos 27 complementares 3; do roster (15): 2. Nas planilhas dos 38 (Ranking 2) o tipo mais próximo está indicado em Fontes.

**Estado.** N — dado pronto para os algoritmos com ③ no cache (8) e MMF1/MMF4 (só se a sonda existir para MMF — conferir `data/sonda/`).

**Demais detalhes.** Caveats: MMF são multimodais no espaço de decisão (ficha 25) — a figura mostra isso de graça; só D = 2 é desenhável; a sonda é fixa (não densa como uma grade dedicada). Relação: 31–34, 44, 45. Decisão: quais algoritmos e se entra no corpo ou como abertura do bloco E.

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 10 artigos / 12 análises** — dos 38 iniciais: 6 · dos 7 do roster minerados agora: 1 · dos 27 complementares: 3 · artigos do roster (15): 2.

- **c1** (BS-MOBO, 2018): Sec. III-A-2, Fig. 2 — [nova] Ilustração 1D do ganho de acurácia do modelo com gradiente (poucos dados)
- **c154** (JES, 2022; roster): Apêndice J, Figs. 7-11 — [nova] Curvas de nível da aquisição em problema de brinquedo single-objective — comparação visual PES x MES x JES x EI x PoI x…
- **c238** (EIM, 2017; roster): Sec. IV-E, Fig. 8 — [nova] Contornos da função de aquisição no espaço de projeto (EI exato × EIM fechado) · Sec. III-C, Sec. IV-C, Figs. 6-7 — [nova] Prova/ilustração das propriedades de monotonicidade da aquisição em relação a μ e σ (N1, N2)
- **c24** (DTK-MODE, 2015): Sec. IV-A, Fig. 2 — [nova] Superfície do surrogate vs função verdadeira (inspeção visual pontual)
- **c241** (EMMOEA, 2023): Sec. I (Introdução), Fig. 1 — [nova] Exemplo numérico ilustrativo do conflito entre EI por objetivo (motivação, Fig. 1)
- **c29** (MO P-algorithm, 2014): Sec. 7, ¶3-4 (problem 10, Fig. 3) e ¶ sobre Fig. 6 (problem 12), p. 87-90 — [nova] Sensibilidade ao vetor-limiar de aspiração (exploração uniforme vs. localização) · Sec. 7, ¶ sobre Fig. 8 / problem (13), p. 91-92 — [nova] Viés do modelo estatístico por paisagem quase-plana com picos (localização do limiar na direção errada)
- **e17** (MOBO, 2021): Sec. III-B, Fig. 3(a-d) — [nova] Verificacao visual da acuracia da media do GP num problema de brinquedo 2D
- **e9** (SUR, 2015): Sec. 3.4, Fig. 1 — [nova] Demonstração didática do critério (caso single-objective)
- **emo1** (MPoI / HypI / DomRank / MSD (4 estratégias de infill), 2017): Sec. 3.2 (Fig. 1, p. 876); Sec. 4.4 (Fig. 2, p. 877); Sec. 5 (Fig. 4, p. 879) — [nova] Paisagem de aptidão do critério de infill (ilustração sintética em grade fixa)
- **mtm6** (EHVI (EI_H) / "EHVI-EGO", 2011): Sec. V-A (Numerical Experiment), parágrafo 'Result' (item c), Fig. 6 (painéis do topo, do… — [nova] Mapa visual do surrogate (μ/σ) e da paisagem do critério de aquisição

**Score (0–10): 6.** **Justificativa.** Reproduzível para D = 2 (MMF1, MMF4 têm D = 2): com ③ (regime sonda, 2.000 pontos Sobol) dá para desenhar μ, σ e |μ − f| sobre o espaço de decisão em 2–3 retreinos, para os algoritmos com μ/σ — a figura didática que o corpus usa (c238 contornos EI×EIM, emo1 paisagem do infill, mtm6 μ/σ, e17, e9, c24, c1). C: 10/72. P média (ilustra 31/33/44), custo baixo, valor pedagógico alto para a banca. Entra como uma figura na abertura do bloco E.


### 73. A recomendação final: ND avaliado (in-sample, ①) × ND acreditado pelo modelo (③) — o custo da convenção de endpoint para métodos informacionais

**Fontes.** [MIN] 1 análise (c154 JES, roster: Sec. 5.2 e Apêndice L.5, Fig. 19) · fichas 40/42 (fantasia) · [REG] D70 (endpoint = ND das avaliações reais) · d19.

**O que analisa.** c154 repete a comparação principal trocando a recomendação: em vez de otimizar a média posterior sobre todo X, restringe-a aos pontos já avaliados X_N — e os métodos informacionais (PES, MES, JES) pioram ('picked points more greedily' favorece os de melhoria/escalarização). A nossa convenção de endpoint (D70) É a versão in-sample.

**Dados.** ① (ND das avaliações reais — a convenção); ③ (μ nos pontos de busca e da sonda) para reconstruir o ND acreditado; ⑦ no offline (onde a reavaliação já existe).

**Objetivo.** Declarar que o placar (1/3/9) mede o que foi AVALIADO, não o que o modelo acredita — e quantificar, para c154/e81/c149, quanto a leitura muda se a recomendação for a 'acreditada' (μ) reavaliada — o que, online, não se pode reavaliar sem experimento; logo, medir a distância |ND acreditado| vs |ND avaliado| (40/42) e argumentar.

**O que busca revelar.** Se os métodos que exploram (informação/Thompson) são penalizados pela convenção — ressalva obrigatória para não 'decretar vencedor' (d19) — e se o mesmo vale para os pisos (que não têm modelo: a convenção os favorece).

**Como é realizada.** Parágrafo de método + para c154 e e81: comparar o HV do ND avaliado (①) com o HV do ND 'acreditado' (μ de ③ nos candidatos da última geração; sem reavaliação, portanto HV acreditado, ficha 40) — a diferença mede a fantasia, não o desempenho.

**Técnicas.** Comparação in-sample × recomendação; HV acreditado × HV avaliado; caveat textual.

**Implementação.** Usa 40 (erro de fantasia) — nada novo além do texto e de um painel para c154/e81.

**Em quantos artigos aparece (dos 72).** 1 artigos (1 análises): dos 38 iniciais 1, dos 7 do roster 0, dos 27 complementares 0; do roster (15): 1. Nas planilhas dos 38 (Ranking 2) o tipo mais próximo está indicado em Fontes.

**Estado.** N — parte textual pronta; painel depende de ③ de c154/e81 (decisão 11).

**Demais detalhes.** Vinculante para a leitura de c154/e81/c149 (BO-especiais) no placar; entra no cap. 4 (convenção) ou no cap. 5 (ressalva). Relação: 10, 40, 42, 61.

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 1 artigos / 1 análises** — dos 38 iniciais: 1 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 0 · artigos do roster (15): 1.

- **c154** (JES, 2022; roster): Sec. 5.2 (discussão) e Apêndice L.5, Fig. 19 — [nova] Recomendação restrita às amostras visitadas (X_N) vs. otimizada sobre todo X — custo da avaliação 'in-sample' para…

**Score (0–10): 7.** **Justificativa.** Reproduzível em parte: ① dá a versão in-sample (nossa convenção D70); ③ (μ) daria a recomendação 'acreditada'. C: 1/72 — mas é c154 (JES, do roster) mostrando que a avaliação in-sample DESFAVORECE os métodos informacionais ('picked points more greedily'). P alta: é uma ressalva vinculante à leitura de c154/e81/c149 no placar (d19) e liga 40/42 ao endpoint. Entra como parágrafo de método (cap. 4/5) + uma figura para c154 se ③ existir; senão nota em 61.


### 78. O decaimento do valor da aquisição ao longo do orçamento (o modelo acha que ainda há o que ganhar?)

**Fontes.** [MIN] 1 análise (e8 Fig. S11: KDE de E[I] e P[I] por geração) · fichas 43/45 · [CD] ⑥ (campos por evento — verificar se há `acq_value`).

**O que analisa.** A distribuição do valor do critério (EI/EHVI/UCB/entropia) nos pontos escolhidos, geração a geração — tende a zero quando o modelo 'acha' que convergiu (ou quando o σ colapsa: 35 'degenera').

**Dados.** ⑥ (se o evento de escolha grava o valor do critério) ou ③ (μ/σ do escolhido → recomputar EI para os GP simples: b1, b3, c238).

**Objetivo.** Ler a auto-avaliação do algoritmo (quanto ele espera melhorar) contra a melhoria real (43): descolamento = fantasia (40) ou σ degenerado (35).

**O que busca revelar.** Se os algoritmos param de 'esperar ganho' antes de parar de ganhar (σ degenerado) ou depois (fantasia).

**Como é realizada.** Curva do valor mediano do critério por geração × Δ IGD+ real por geração; por algoritmo com critério explícito.

**Técnicas.** Séries por geração; correlação defasada.

**Implementação.** Depende do parser do ⑥ (45); se o valor não estiver gravado, recomputar EI de μ/σ (③) só para GP com EI/UCB fechados.

**Em quantos artigos aparece (dos 72).** 1 artigos (1 análises): dos 38 iniciais 0, dos 7 do roster 0, dos 27 complementares 1; do roster (15): 0. Nas planilhas dos 38 (Ranking 2) o tipo mais próximo está indicado em Fontes.

**Estado.** N — verificar disponibilidade no ⑥; senão cair.

**Demais detalhes.** Relação: 35, 40, 43, 45. Decisão: só se 45 for feita.

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 1 artigos / 1 análises** — dos 38 iniciais: 0 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 1 · artigos do roster (15): 0.

- **e8** (NN-EGO, 2020): Figure S11 (S18) — [nova] Distribuição do critério de aquisição (E[I]/P[I]) por geração

**Score (0–10): 4.** **Justificativa.** Reproduzível só se ⑥ registra o valor do critério (EI/EHVI/UCB) do ponto escolhido — verificar por algoritmo. C: 1/72 (e8, KDE de E[I] por geração). P média: 'o decaimento da aquisição' diz quando o modelo acha que não há mais o que ganhar (relação com 43/45/39). Apêndice se ⑥ tiver o campo; senão cair.

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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 15 artigos / 23 análises** — dos 38 iniciais: 10 · dos 7 do roster minerados agora: 1 · dos 27 complementares: 4 · artigos do roster (15): 2.

- **b15** (U-RankMOEA, 2026): Apendice N.1, Table 14 e Table 15; Sec. 4.4, Fig. 14 — Comparacao de tempo de parede (total e por iteracao) entre U-RankMOEA e 6 baselines (CPS-MOEA, K-RVEA, CSEA, EDN-ARMOEA, MCEA/D, CLMEA) em 3 cenarios…
- **b2** (MOEA/D-EGO, 2010): Sec. VII-E-2 (FuzzyCM Versus One Single Model); Table III; Fig. 9(a)–(d) — Para medir o custo-benefício da FuzzyCM (a técnica de clusterização fuzzy usada pelo MOEA/D-EGO para conter o custo do GP), os autores treinam também…
- **c100** (qEHVI, 2020): Sec. 5.1, Table 1 — Tabela única de tempo de parede — apenas da etapa de otimização da aquisição, não do ajuste do modelo nem da avaliação real — em CPU e GPU, para…
- **c107** (MS-VHGP-EIHV, 2017): Sec. III-E2, Fig. 13(a) — Mede o tempo de parede (wall-clock) necessário para completar cada passo do procedimento usando o EIHV exato (quadratura de Gauss-Hermite) versus a… · Sec. II-C; Sec. III-E3, Fig. 13(b) — Mede o tempo de parede por passo do procedimento para o critério LOO versus o critério MC de seleção de modelo, e discute a complexidade assintótica…
- **c149** (LBN-MOBO, 2023; roster): Sec. C.1.4 (Apêndice), Figs. 9, 10 — Compara LBN-MOBO com USeMO, DGEMO, TSEMO e NSGA-II (piso evolutivo sem surrogate) no ZDT3 em 6D e 30D, lote fixo em 1000, por até 10 iterações: (a)… · Sec. C.4, Figs. 14, 15 — Compara LBN-MOBO (testado com lotes de 1000 e 4000 amostras) contra DGEMO, TSEMO, USeMO e NSGA-II no DTLZ4 (6D entrada, 3 objetivos): fronteira de… · Sec. C.4, Fig. 16 — Mesma comparação (LBN-MOBO, DGEMO, TSEMO, USeMO, NSGA-II) no DTLZ1 (6D entrada, 3 objetivos): fronteira final, tempo decorrido e evolução do HV (em…
- **c214** (PFES, 2020): Sec. 6.1, Table 1, p. 8 — O artigo mede o tempo de parede (segundos) para avaliar a função de aquisição em 100 pontos candidatos no problema DTLZ4 (L=4, a maior dimensão de…
- **c24** (DTK-MODE, 2015): Sec. IV-B — O artigo quantifica o ganho de eficiência numérica central da proposta: o número de chamadas de FEA (avaliações reais, caras) necessárias pelo MODE…
- **c241** (EMMOEA, 2023): Sec. IV (Conclusion) — O artigo MENCIONA (sem detalhar no corpo principal) uma análise do tempo computacional exigido pelos 6 algoritmos comparados, remetendo ao material…
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF), 2021; roster): Table 3, Table 4 (Apendice H.1) — Tabelas de tempo de parede (CPU e GPU) para a etapa de otimizacao da funcao de aquisicao (incluindo decomposicoes de caixa), para os 12 metodos, nos…
- **c59** (UA-DBO, 2026): Sec. 4.1.2, Table 2, p. 13–15 — Tabela (Tabela 2) comparando a QUALIDADE da incerteza calibrada entre o GS-ED proposto e um 'deep ensemble' clássico (n=3 e n=6 modelos… · Sec. 4.3, Table 4, p. 21 — Tabela (Tabela 4) decompondo o tempo de parede de um caso completo de otimização em preparação de dados (construção do dataset de pré-treino), treino…
- **c75** (MO-EI/PI (Keane), 2006): Multiobjective Example 1, discussão após a Fig. 12 (p. 889) — Ainda no Exemplo MOO 1, o artigo quantifica textualmente a eficiência em avaliações de função: a frente do E[I]dom (135 avaliações totais) é dita… · Multiobjective Example 2, Table 2 (p. 890) — No 'Multiobjective Example 2' (aerofólio VGK robusto, M=2: Cd × desvio-padrão de Cd sob 20 perturbações geométricas de ±5%), a Tabela 2 tabula, para…
- **c91** (EHVIMOPSO, 2019): Sec. 3.4.2, Table 1 — Compara duas variantes do próprio critério de amostragem do EHVIMOPSO — EHVI 'estática' (usa todas as soluções não-dominadas correntes para… · Sec. 3.4.3, Tables 3-5 — Compara o algoritmo proposto (EHVIMOPSO, assistido por Kriging) com seu piso sem surrogate (MOPSO-CD, mesma maquinaria de dominância + distância de…
- **e104** (RVMM, 2022): Sec. IV-C (menção); Seção III do material suplementar (não anexado ao corpus) — [nova] Comparação de tempo de execução (runtime) entre os oito algoritmos
- **e64** (SA-MOPSO (PPD), 2025): Table 3; Sec. 5.2.1 — A Tabela 3 decompõe, para a aplicação real (aquífero costeiro), o tempo médio de execução (forward run) e o tempo de parede paralelizado (100 nucleos…
- **wang4** (SA-NSGA-II, 2016): Sec. V-B, Fig. 12 — Fixa K (sem adaptação) em dez níveis de 100 a 2000 (passo 100), 20 execuções independentes por nível, e reporta o IGD médio (contra o conjunto de… · Sec. V-C1, Fig. 13 — Com o esquema adaptativo de K ativo, varia o limite superior Kmax em {500, 1000, 1500, 2000}, 20 execuções independentes por valor, e reporta o… · Sec. V-D, Table II — Compara, sob o MESMO número de gerações (100), o IGD (contra o conjunto de referência da avaliação exata) e o tempo computacional (s) de três…

**Complementos e correções (06/09/2026).** c122 é o modelo de prudência: compara CPU só entre os três em Python (exclui MATLAB/PlatEMO) e relativiza ('avaliações reais dominam'). wang4 recomputa o placar sob 1 h de parede. c214/c222 medem só o tempo da aquisição. Cuidado com a rota MATLAB × Python na bateria.

**Score (0–10): 8.** **Justificativa.** F. C: 15/72 reportam tempo × qualidade ou tempo total (R2#2 26/38; c122 CPU 'de mesma ordem apesar do IGD', wang4 sob 1 h). P: 'o custo se paga?' — a leitura em quadrantes é a resposta honesta ao 'expensive' (a avaliação real domina — c122; jin3 assume sem medir). D feita. Entra como figura de fechamento do bloco F; cuidado com a rota MATLAB × Python (tempos não comparáveis entre plataformas — c122 só compara os Python).


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 20 artigos / 23 análises** — dos 38 iniciais: 11 · dos 7 do roster minerados agora: 3 · dos 27 complementares: 6 · artigos do roster (15): 6.

- **b14** (SA²-MOEA, 2024): Sec. 4.7, Table 7 — Análise TEÓRICA (não medida empiricamente) de complexidade de tempo e de espaço, decomposta em três fases (construção do modelo, busca assistida por…
- **b15** (U-RankMOEA, 2026): Apendice N.1, Table 14 e Table 15; Sec. 4.4, Fig. 14 — Comparacao de tempo de parede (total e por iteracao) entre U-RankMOEA e 6 baselines (CPS-MOEA, K-RVEA, CSEA, EDN-ARMOEA, MCEA/D, CLMEA) em 3 cenarios…
- **b9** (USeMO, 2020): Sec. 5.2 ("Comparison of acquisition function optimization time"); Table 2 — O artigo mede o tempo médio (segundos, média±desvio-padrão) de otimização da função de aquisição por iteração — excluindo deliberadamente o tempo de…
- **c100** (qEHVI, 2020): Sec. 5.1, Table 1 — Tabela única de tempo de parede — apenas da etapa de otimização da aquisição, não do ajuste do modelo nem da avaliação real — em CPU e GPU, para…
- **c131** (MORBO, 2022): Apendice E.1, Table 2, Table 3 — Tempo de ajuste do modelo (model fitting), em segundos, medido SEPARADAMENTE da busca da aquisicao, para MORBO e para os baselines de BO com GP… · Apendice F.2 ('Candidate generation wall time'), Table 4, Table 5 — Tempo de geracao de candidatos (selecao do lote, EXCLUINDO o ajuste do modelo), em segundos, para MORBO e baselines em Welded Beam/Vehicle…
- **c149** (LBN-MOBO, 2023; roster): Sec. C.1.4 (Apêndice), Figs. 9, 10 — Compara LBN-MOBO com USeMO, DGEMO, TSEMO e NSGA-II (piso evolutivo sem surrogate) no ZDT3 em 6D e 30D, lote fixo em 1000, por até 10 iterações: (a)…
- **c154** (JES, 2022; roster): Sec. 5.2 (resumo) e Apêndice L.9, Figs. 29 (box-plots) e 29 (decomposição por fase) — Compara o tempo de parede (wall-clock) da etapa de AQUISIÇÃO (não inclui o ajuste do modelo GP) entre os ~15 algoritmos/variantes, nos 4 problemas e…
- **c214** (PFES, 2020): Sec. 6.1, Table 1, p. 8 — O artigo mede o tempo de parede (segundos) para avaliar a função de aquisição em 100 pontos candidatos no problema DTLZ4 (L=4, a maior dimensão de…
- **c222** (MESMO, 2019): Sec. 5.2, Table 1 — Tabela de tempo médio±desvio-padrão (segundos) de otimização da FUNÇÃO DE AQUISIÇÃO (excluindo explicitamente o tempo de ajuste do GP, dito igual… · Sec. 5.2 (menção); Fig. 4 do Appendix — não presente nesta extração — O artigo MENCIONA uma comparação de tempo adicional, com desenho mais limpo que a Table 1: dimensão de entrada d fixada em 5 e número de objetivos K…
- **c238** (EIM, 2017; roster): Sec. VII, Figs. 15-17 — Mede o tempo médio (1000 repetições) para AVALIAR (não para otimizar) cada um dos 6 critérios de aquisição isoladamente, com μ e σ do Kriging fixados…
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF), 2021; roster): Table 3, Table 4 (Apendice H.1) — Tabelas de tempo de parede (CPU e GPU) para a etapa de otimizacao da funcao de aquisicao (incluindo decomposicoes de caixa), para os 12 metodos, nos…
- **c59** (UA-DBO, 2026): Sec. 4.3, Table 4, p. 21 — Tabela (Tabela 4) decompondo o tempo de parede de um caso completo de otimização em preparação de dados (construção do dataset de pré-treino), treino…
- **c81** (UA-MORL-Diff, 2025): Sec. 4.1 (Device); Appendix B.9 — Reporta, em prosa (não em tabela), o tempo de parede decomposto por fase — pré-treino do modelo de difusão (por iteração), otimização por RL (por…
- **c91** (EHVIMOPSO, 2019): Sec. 4.4 (texto) — Reporta o custo computacional decomposto da aplicação real (DSI): tempo de geração de malha, tempo de simulação CFD por amostra, tempo combinado de…
- **e3** (HeE-MOEA, 2019): Sec. V-D, Fig. 4 — Boxplots do tempo de TREINO (ajuste) do surrogate por problema (numerados 1–16 = DTLZ1-7, WFG1-9), um painel separado para HeE-MOEA e para GP-MOEA em… · Sec. V-D, Fig. 5 — Boxplots do tempo TOTAL de uma execução completa (não apenas o ajuste do modelo) por problema, mesmo esquema de 8 painéis (HeE-MOEA vs. GP-MOEA ×…
- **e64** (SA-MOPSO (PPD), 2025): Table 3; Sec. 5.2.1 — A Tabela 3 decompõe, para a aplicação real (aquífero costeiro), o tempo médio de execução (forward run) e o tempo de parede paralelizado (100 nucleos…
- **e7** (EDN-ARMOEA, 2022; roster): Fig. 3 (a-h); DTLZ7 — Tempo de treino do surrogate e tempo total de otimização por execução, medidos em segundos, versus d∈{20,40,60,100} (m=3) e versus m∈{3,5,10,20}…
- **e74** (CLMEA, 2023; roster): Sec. IV-G; Fig. 12 (bi-objetivo 200D DTLZ1) — Análise teórica da complexidade computacional de treino/predição do RBF e PNN contra a complexidade O(n³) do Kriging (símbolos exatos das fórmulas…
- **e8** (NN-EGO, 2020): Text S2 (S10); Figure S3 (S8) para a decomposição do tempo de correção de… — Reporta o custo computacional de duas etapas do fluxo: (a) avaliação (inferência) do ANN sobre o espaço de desenho inteiro, processado em 140 lotes…
- **e86** (NSGAIII-EHVI, 2023): Sec. IV-C, Table V — O artigo compara o NSGAIII-EHVI (EHVI estimado por amostragem por importância, IS) com o NSGAIII-EHVI3, uma variante idêntica que estima o EHVI pela…

**Complementos e correções (06/09/2026).** Decomposições vistas: só aquisição (b9, c100, c154, c214, c222, c262 CPU/GPU), ajuste separado da aquisição (c131 Tables 2–5), ajuste + total (e3 Figs. 4–5, e7 Fig. 3), preparação + treino + otimização (c59 Table 4), fases em Big-O (b14, c261, e103, jin3). A ④ (fit/busca/sonda/avaliação por geração) é mais fina que qualquer uma delas.

**Score (0–10): 9.** **Justificativa.** F-parcial. C: 20/72 decompõem o custo (ajuste × aquisição × avaliação): b9, c100, c131 (fit separado), c154 (só aquisição), c214, c222, c238, c262 (CPU/GPU), c59, e3, e7 — a decomposição é convenção no BO (só aquisição) e rara no EA. P alta. V: cap. 1 promete a 'contribuição de medida' (tempo de ajuste separado) — vinculante; ④ tem fit/busca/sonda por geração. Núcleo do bloco F; 69 é o complemento (tempo de busca × D).


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 1 artigos / 2 análises** — dos 38 iniciais: 0 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 1 · artigos do roster (15): 0.

- **wang4** (SA-NSGA-II, 2016): Sec. V-B, Fig. 12 — Fixa K (sem adaptação) em dez níveis de 100 a 2000 (passo 100), 20 execuções independentes por nível, e reporta o IGD médio (contra o conjunto de… · Sec. V-C1, Fig. 13 — Com o esquema adaptativo de K ativo, varia o limite superior Kmax em {500, 1000, 1500, 2000}, 20 execuções independentes por valor, e reporta o…

**Score (0–10): 4.** **Justificativa.** N. C: 1/72 (wang4 K × qualidade). P baixa-média: 'qualidade por hora' contradiz a premissa 'expensive' (a avaliação real domina — c122, jin3) e mistura rotas MATLAB/Python. Derivada de 47/48. Cair ou apêndice.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 0 artigos.** Nenhuma análise dos 72 foi mapeada a esta ficha — leitura própria da tese (ou regra/nota), sem correspondente nomeado no corpus.

**Score (0–10): 6.** **Justificativa.** R (nota). C: 0/72. Nota obrigatória de transparência sobre o FE redundante no DDMOP7 (custo, não análise). Entra como nota de rodapé em 23/47; score reflete 'deve constar', não 'é análise'.



### 69. Custo da otimização da aquisição (tempo de busca) e complexidade assintótica por fase

**Fontes.** [MIN] 15 análises em 13 artigos (lista abaixo) · ficha 48 (decomposição fit/busca/sonda) · [CD] ④ (`tempo_busca_s` por geração) · [CAP3/4] complexidades declaradas dos 15.

**O que analisa.** O custo do CRITÉRIO (não do modelo): tempo para otimizar/avaliar a aquisição por iteração e como cresce com D, M, |ND| e q — c100 (gradiente exato 10× mais rápido que diferenças finitas/CMA-ES), c154 (tempo de parede da aquisição cresce com S), c214/c222 (tempo de avaliar a aquisição em 100 candidatos; MESMO O(SK) × PESMO O(SKm³)), c238 (tempo de avaliar cada critério, 1000 repetições), c261 (Big-O por fase + CPU × q: 818 s × 9066 s em q=15), c262 (CBD × IEP: exponencial em q), emo1 (SMS-EGO O(|P*|^D)), e1 (nº de células da decomposição), c122 (CPU só entre os Python), e103/b14/jin3/c267 (Big-O por fase, sem medição).

**Dados.** ④ (`tempo_busca_s`, `tempo_fit_s`, `tempo_pred_sonda_s` por geração; `n_acumulado`); ⑤ (timing agregado); M (D por problema; família de aquisição por algoritmo).

**Objetivo.** Separar, no custo do surrogate, o que é pagar pelo σ (ajuste do GP, O(n³): 46/48) do que é pagar pelo CRITÉRIO que usa o σ (busca da aquisição: informacionais e hipervolume pagam aqui).

**O que busca revelar.** Se os métodos que usam a incerteza de forma mais elaborada (c154 JES, c262 qNEHVI, c238 EIM-h) são caros no ajuste ou na busca — e como isso cresce com D e com o tamanho do ND (c261/emo1: hipervolume explode com M e |P*|).

**Como é realizada.** Por célula, somar `tempo_busca_s` e `tempo_fit_s` sobre gerações; razão busca/(busca+fit) por algoritmo e por família de aquisição (melhoria, hipervolume, informação, classificação); curvas de tempo_busca por geração × n_acumulado; tabela por D (3 níveis) e por M.

**Técnicas.** Agregação por célula; mediana entre sementes; regressão log-log tempo × n (expoente empírico vs. Big-O declarado); comparação só dentro da mesma rota (Python × MATLAB não comparáveis — c122).

**Implementação.** Sobre o cache de ④ (existe `timing` no notebook §7 para 46/48): adicionar a coluna `tempo_busca_s` à decomposição e a razão busca/fit; figura de barras empilhadas por algoritmo (fit | busca | sonda) — a sonda é custo NOSSO e deve ser descontada (declarar).

**Em quantos artigos aparece (dos 72).** 13 artigos (15 análises): dos 38 iniciais 6, dos 7 do roster 1, dos 27 complementares 6; do roster (15): 3. Nas planilhas dos 38 (Ranking 2) o tipo mais próximo está indicado em Fontes.

**Estado.** N — dado pronto (④); custo baixo (extensão de 48).

**Demais detalhes.** Caveats: teto de parede 12 h só na rota Python (615 ⚪ — fichas 29/58 — são exatamente os algoritmos com busca cara: c154, c262, c149, e81); tempos de máquinas diferentes (a torre mediu a dispersão por máquina — ficha 8). Relação: 46, 47, 48, 58. Decisão: descontar a sonda; publicar como painel de 48.

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 13 artigos / 15 análises** — dos 38 iniciais: 6 · dos 7 do roster minerados agora: 1 · dos 27 complementares: 6 · artigos do roster (15): 3.

- **b15** (U-RankMOEA, 2026): Apendice G.1, Table 9 — [nova] Custo de re-tuning de hiperparametros ao transferir para uma nova tarefa (protocolo de 2 estagios)
- **c1** (BS-MOBO, 2018): Sec. IV-C, Fig. 6 — [nova] Sensibilidade ao tamanho do lote (parâmetro de paralelismo k) sobre a frequência de retreino
- **c100** (qEHVI, 2020): Sec. 4.2, Fig. 2a — [nova] Custo do método de otimização da aquisição (gradiente exato vs. aproximado vs. livre) · Fig. 11 (Apêndice — ausente deste corpus); citado na Sec. 3.3 — [nova] Escalabilidade do tempo de computação do qEHVI com o tamanho do lote q (saturação de hardware)
- **c106** (EMMI (EMmI), 2016): Sec. 6.1, p. 17 (7 parametros); Sec. 6.2, p. 18-19 (26 parametros) — [nova] Custo de estimacao via REML por numero de parametros de covariancia (independente x dependente)
- **c122** (θ-DEA-DP, 2022; roster): Sec. IV-C, Table VII — [nova] Custo agregado (CPU) de gerenciar os surrogates, comparado entre subconjunto de algoritmos
- **c261** (DirHV-EGO, 2024): Sec. V-D.1, p.10-11 (texto principal); Supplementary Sec. III-D.2 — [nova] Decomposição analítica (não-empírica) do custo computacional por fase (ajuste do GP, maximização da EI, seleção de lote) · Sec. V-D.2, p.11, Fig. 6 — [nova] Escalabilidade do tempo de CPU com o tamanho do lote (batch size q)
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF), 2021; roster): Fig. 2 (Sec. 6); Fig. 6 (Apendice H.2); derivacao teorica no Apendice D — [nova] CBD x IEP -- escalabilidade do custo de otimizacao da aquisicao com o lote q
- **c267** (SAMOEA-TL2M, 2025): Sec. IV (parágrafo de abertura da Seção IV, antes de IV-A); Supplementary Sec. IV (não… — [nova] Complexidade computacional teórica (Big-O) do SAMOEA-TL2M
- **c276** (ε-PAL, 2016): Sec. 7.5, Fig. 7 — [nova] Speedup de runtime ε-PAL vs PAL por ε e por |E|, sob custo de avaliação assumido (0 min / 30 min)
- **e1** (EMO, 2014): Sec. 3.4, Fig. 5 — [nova] Escalabilidade sintética do custo de decomposição em células (tempo, nº de células) vs. nº de objetivos e tamanho do…
- **e103** (IBEA-MS, 2023; roster): Sec. III-B; Table S.I (material suplementar) — [nova] Análise de complexidade computacional assintótica (Big-O) por fase, entre 7 algoritmos
- **emo1** (MPoI / HypI / DomRank / MSD (4 estratégias de infill), 2017): Sec. 5, Fig. 5, p. 879 — [nova] Custo isolado da avaliação do critério de infill × nº de objetivos e |P*|
- **jin3** (GS-MOMA / GSM (mono: GS-SOMA), 2010): Sec. IV-D, Eq. (24)-(25) — [nova] Decomposição analítica (não-empírica) do custo computacional

**Score (0–10): 6.** **Justificativa.** Reproduzível em parte: ④ tem tempo_busca_s por geração (otimização da aquisição) para todos — dá 'tempo de busca × D × família de aquisição' sem experimento; a complexidade assintótica (Big-O) é texto do cap. 3/4. C: 13/72 (c100 gradiente exato 10×, c154, c214, c222, c238 tempo por avaliação do critério, c261 Big-O + CPU × q, c262 CBD×IEP, e103, emo1, jin3 fórmula de custo). P média-alta: separa o custo do σ (ajuste, 46/48) do custo do CRITÉRIO (busca) — os informacionais (c154) pagam na busca, os GPs pagam no ajuste. Entra como painel de 48.

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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 0 artigos.** Nenhuma análise dos 72 foi mapeada a esta ficha — leitura própria da tese (ou regra/nota), sem correspondente nomeado no corpus.

**Score (0–10): 6.** **Justificativa.** F. C: 0/72 (o corpus compara seminal e SOTA como concorrentes, não como pares sob o mesmo DoE). P média-alta: 'o que a evolução da classe comprou' é narrativa boa para o cap. 6, com dado pronto (mesmo DoE por semente). Entra como parágrafo com tabela pequena (b1→c262; b3→e74/c141; b4→c217; c238→c261 não está; c154 é SOTA sem seminal na bateria).


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 7 artigos / 10 análises** — dos 38 iniciais: 5 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 2 · artigos do roster (15): 0.

- **b14** (SA²-MOEA, 2024): Sec. 4.3, Table 2 — Ablação do método de quantificação de incerteza do SA²-MOEA: compara o método proposto (baseado na mudança de rank entre o melhor ensemble EMbest e o…
- **b7** (DR (Dual-Ranking), 2026): Sec. 4.3 (fim); Material Suplementar, 'Ablation Study Between Dual-Ranking and the… — Ablação isolando o componente 'dual' do dual-ranking: compara, para cada um dos 4 surrogates, a variante DR completa (não-dominância no espaço 2M…
- **c1** (BS-MOBO, 2018): Sec. IV-A-1 — [nova] Efeito isolado do framework de aquisição em lote, controlando o modelo (GP), pequena escala · Sec. IV-B-1 — [nova] Efeito isolado do framework de aquisição em lote, controlando o modelo (GP), alta dimensão
- **c59** (UA-DBO, 2026): Sec. 4.2, Table 3, p. 15–16 — Tabela final (Tabela 3) comparando os 3 frameworks (CFD-based, DBO, UA-DBO) nos 3 casos de divergência de arrasto (A1, A2, A3): para DBO/UA-DBO,… · Appendix C.4.2, Table 6, p. 31–32 — Tabela final (Tabela 6) com o desempenho CFD-verificado (C_L,buffet e (L/D)_cruzeiro) de uma 'amostra típica' selecionada da frente de Pareto de DBO…
- **c81** (UA-MORL-Diff, 2025): Appendix B.6; Table 2 (linhas UCB/EI/MVC/BORE) — Dentro da Tabela 2 (ablação, só QM9), o subgrupo 'uncertainty-based' compara 'Ours' contra 4 formulações alternativas de uso da incerteza para guiar…
- **e21** (PIO, 2025): Table 2; Results, 'Optimization results of single-objective task' — Compara três funções de fitness — DOM (maximização direta da média, sem incerteza), EI (expected improvement, incerteza usada de forma exploratória)… · Table 3; Results, 'Optimization results of multi-objective tasks' — Estende a comparação de placar para as 6 tarefas multi-objective, contrastando três funções agnósticas à incerteza — WS (soma ponderada pelo inverso…
- **f9** (UA-IBEA (sigla não-oficial, proposta por mim; paper não nomeia — "Approach 1/2/3"), 2019): Sec. 4, p. 469 (+ definições em Eqs. 5-7, Sec. 3, pp. 467-468) — As três formulações de incerteza compartilham o mesmo motor EMO (IBEA/Iepsilon+) e os mesmos modelos Kriging, diferindo apenas em como sigma entra no…

**Complementos e correções (06/09/2026).** Pares 'mesma maquinaria, incerteza distinta' no corpus: b7 (DR × função UA por surrogate), b14 (método de UQ × alternativas), c59 (DBO × UA-DBO), c81 (UCB/EI/MVC/BORE × U_multi), e21 (DOM × EI × PIO), f9 (3 formulações), c1 (GP fixo entre 6 frameworks). Todos exigem executar as variantes; os nossos três pares já estão executados.

**Score (0–10): 9.** **Justificativa.** N. C: 7/72 controlam o modelo e variam a incerteza (b14, b7 dual × UA, c1 GP fixo, c59 DBO×UA-DBO, c81 4 formulações, e21 DOM×EI×PIO, f9 3 formulações) — é a versão do corpus para 'mesma maquinaria, incerteza distinta'. P máxima: b3×b5(RVEA), c154×e81 (informação × Thompson), c141×e74 são os experimentos naturais da bateria sobre a FUNÇÃO da incerteza, sem rodar nada. V: substituto do OE5 junto com 11. D pronta. Núcleo.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 0 artigos.** Nenhuma análise dos 72 foi mapeada a esta ficha — leitura própria da tese (ou regra/nota), sem correspondente nomeado no corpus.

**Score (0–10): 5.** **Justificativa.** R (moldura). C: 0/72. O quadro de equivalências do cap. 3 abre a §5.1 — é texto, não análise; o Anexo 8.4 (71 passagens de equivalência de critérios no corpus) dá o material literário. Entra como moldura; não pontua como análise.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 54 artigos / 82 análises** — dos 38 iniciais: 26 · dos 7 do roster minerados agora: 7 · dos 27 complementares: 21 · artigos do roster (15): 12.

- **b1** (ParEGO, 2006; roster): Sec. VI-C; Figs. 4, 5 — Para os 4 problemas biobjetivo (KNO1, OKA1, OKA2, VLMOP2), plota-se no mesmo gráfico a superfície de attainment mediana e a pior (método formal de… · Sec. VI-C; Figs. 6, 7, 8, 9 — Para os 4 problemas com 3 objetivos (DTLZ2a, DTLZ4a, DTLZ7a, VLMOP3), plota-se apenas a superfície de attainment do pior caso (sobre as 21 execuções)…
- **b13** (AdaMoR-DDMOEA, 2025): Sec. 5.4, Figure 4 — Visualização qualitativa (Figura 4) do conjunto não-dominado obtido pelos algoritmos offline contra a frente de Pareto verdadeira, na legenda para os…
- **b15** (U-RankMOEA, 2026): Apendice O, Fig. 19 (legenda interna via OCR: 'True Pareto Front', 'Enhanced CLMEA… — Comparacao visual 2-D entre a frente de Pareto verdadeira e as solucoes encontradas por U-RankMOEA (e possivelmente outros metodos) num problema…
- **b2** (MOEA/D-EGO, 2010): Sec. VII-D-1 (Comparison); Figs. 2, 3, 4, 5, 6 — As Figs. 2–6 mostram, no espaço de objetivos, a aproximação final — da execução de menor IGD entre as 10 — de cada algoritmo em cada uma das 12… · Sec. VII-E-1 (The Effect of the Gaussian Model); Fig. 8(a)–(b) — Para isolar o efeito do modelo Gaussiano, os autores rodam a versão original do MOEA/D (Zhang & Li [28]), sem qualquer surrogate, com população 20 e…
- **b3** (K-RVEA, 2018; roster): Sec. IV-B; Fig. 6 — Para DTLZ1 (3 objetivos), plota-se o conjunto não-dominado obtido pela EXECUÇÃO COM MELHOR IGD (não a mediana) de K-RVEA, RVEA e ParEGO, um painel… · Sec. IV-B; Fig. 7 — Para DTLZ7 (3 objetivos, frente desconexa em 4 regiões), plota-se o conjunto não-dominado da execução com melhor IGD de K-RVEA, RVEA, ParEGO e…
- **b4** (CSEA, 2019; roster): Sec. IV-C, Fig. 8 — Visualização 3D do conjunto não-dominado final obtido por cada um dos 6 algoritmos (CSEA, MOEA/D-EGO, NSGA-III, CPS-MOEA, ParEGO, K-RVEA) em DTLZ1… · Sec. IV-C, Fig. 9 — Visualização (gráfico de valor por dimensão, já que M=10 impede uma vista 3D direta) do conjunto não-dominado final de cada um dos 6 algoritmos em… · Sec. IV-E, Fig. 10 — Examina o desempenho de CSEA e outros cinco algoritmos (NSGA-III, CPS-MOEA, ParEGO, MOEA/D-EGO, K-RVEA) em ZDT1 (bi-objetivo) com d=10, 20 e 30…
- **b5** (Prob-RVEA / Prob-MOEA/D (+ Hyb-RVEA / Hyb-MOEA/D), 2022; roster): Sec. IV-A, Fig. 9 — Visualização qualitativa (execução com HV mediano) da convergência das soluções — avaliadas na função verdadeira — em direção ao front de Pareto…
- **b8** (KTA2, 2021): Sec. IV-E (abertura), Figs. S1-S16 (material suplementar - não incluído neste documento) — O artigo menciona que as soluções não-dominadas finais da execução com IGD+ mediano, para os 6 algoritmos comparados, nos 16 problemas de 3 objetivos…
- **c1** (BS-MOBO, 2018): Sec. IV-D, Fig. 8 — [nova] Fronteira aproximada entre algoritmos sem frente verdadeira conhecida (caso real)
- **c10** (SP-RV-MOEANet, 2021): Fig. 2 — Visualização qualitativa dos conjuntos não-dominados obtidos pelos 5 algoritmos (MOEA-RSFMMA, MOEA0, P-MOEANet, P-RV-MOEANet, SP-RV-MOEANet) no…
- **c105** (SMS-EGO, 2008): Fig. 2(b), p. 790 — Figura 2(b) mostra a distribuicao das solucoes no espaco de objetivos para DTLZ2 com 3 objetivos, plotando - para cada algoritmo - a execucao que…
- **c106** (EMMI (EMmI), 2016): Sec. 6.1 (MOP2 Function), Fig. 3, p. 17 — Para o MOP2, plota os pontos sequencialmente adicionados por cada criterio (CWPI, EMMI, PI) sobre a frente de Pareto verdadeira, separadamente para o…
- **c122** (θ-DEA-DP, 2022; roster): Sec. IV-B, Fig. 4 — Visualização do conjunto não-dominado final de cada um dos 5 algoritmos comparados no espaço de objetivos (θ-DEA-DP, ParEGO, DomRank, MOEA/D-EGO,…
- **c123** (EPBII / EIPBII, 2017): Sec. VI-A/VI-B, Figs. 13-20, 22, 23 — Para praticamente todos os problemas testados, o artigo plota as soluções não-dominadas obtidas contra a fronteira/POS verdadeira (Figs. 13-20,…
- **c131** (MORBO, 2022): Sec. 2.3 ('Issues with scalarized TuRBO'), Sec. 3.1; Fig. 1; Fig. 2 — Comparacao qualitativa ilustrativa (scatter dos pontos avaliados, coloridos por regiao de confianca/TR, mais a fronteira aproximada) entre uma… · Apendice F.3 ('Pareto frontiers'), Fig. 10 — Mostra, lado a lado em 3 colunas, as fronteiras nao-dominadas das replicas PIOR/MEDIANA/MELHOR (segundo o HV final) para welded beam, trajectory…
- **c141** (MMRAEA, 2025; roster): Sec. Main comparison, Fig. 7 e Fig. 8 — Visualização do conjunto não-dominado final de cada um dos 5 algoritmos comparados no espaço de objetivos, contra a frente de Pareto verdadeira, para… · Sec. Results and discussions (BWBUG), Fig. 12 — Visualização do conjunto não-dominado final dos 5 algoritmos no espaço de objetivos (peso × tensão) para o caso BWBUG.
- **c149** (LBN-MOBO, 2023; roster): Sec. C.1.4 (Apêndice), Figs. 9, 10 — Compara LBN-MOBO com USeMO, DGEMO, TSEMO e NSGA-II (piso evolutivo sem surrogate) no ZDT3 em 6D e 30D, lote fixo em 1000, por até 10 iterações: (a)… · Sec. C.1.5, Fig. 12 — Mesma comparação (LBN-MOBO, USeMO, DGEMO, TSEMO, NSGA-II) repetida em ZDT1 (frente convexa) e ZDT2 (frente não-convexa), 30D, reportando evolução do… · Sec. C.4, Figs. 14, 15 — Compara LBN-MOBO (testado com lotes de 1000 e 4000 amostras) contra DGEMO, TSEMO, USeMO e NSGA-II no DTLZ4 (6D entrada, 3 objetivos): fronteira de… · Sec. C.4, Fig. 16 — Mesma comparação (LBN-MOBO, DGEMO, TSEMO, USeMO, NSGA-II) no DTLZ1 (6D entrada, 3 objetivos): fronteira final, tempo decorrido e evolução do HV (em…
- **c217** (PC-SAEA, 2023; roster): Sec. 4.3, Fig. 6 — Figura dupla para 2-objective DTLZ3 (frente altamente multimodal): (a) as populações finais (espaço de objetivos) dos 8 algoritmos na execução de IGD… · Sec. 4.3, Fig. 7 — Mesma figura dupla (população na execução de IGD mediano + curva de IGD médio × fração de avaliações) para 3-objective WFG2, problema com frente de…
- **c238** (EIM, 2017; roster): Figs. 9-14 (legendas), Sec. VI-A a VI-D (discussão) — Para cada um dos 12 problemas sintéticos, plota-se a aproximação final da frente de Pareto obtida por cada um dos 6 critérios, usando a execução com…
- **c24** (DTK-MODE, 2015): Sec. IV-B, Fig. 4 — A Fig. 4 mostra visualmente as fronteiras de Pareto obtidas pelo MODE assistido por DTK (modelo construído com 350 pontos de amostragem) comparadas…
- **c241** (EMMOEA, 2023): Sec. III-E, Figs. 4-8 — Para 5 problemas de 3 objetivos (DTLZ2, DTLZ5, DTLZ7, MaF1, WFG2), plota-se o conjunto não-dominado da execução cujo IGD é o mais próximo da mediana… · Sec. III-E, Figs. 10-12 — Para 3 problemas de 10 objetivos (DTLZ3, WFG3, WFG9), plotam-se as coordenadas paralelas do conjunto não-dominado da execução de IGD mais próxima da…
- **c250** (K-MOGA, 2008): Sec. 4.1, Fig. 3 (p. 031401-5); Sec. 4.2, Fig. 8 (p. 031401-7); Sec. 4.3, Table 2 (p.… — Para cada um dos 7 exemplos, o artigo plota qualitativamente o conjunto nao-dominado obtido por MOGA e por K-MOGA no espaco de objetivos - de uma…
- **c261** (DirHV-EGO, 2024): Sec. V-E, p.11, Fig. 7 — Visualização qualitativa do conjunto não-dominado final obtido pelos quatro algoritmos paralelos (q=5) na execução com hypervolume MÉDIO (não… · Supplementary Sec. VI, Figs. 14-22 — Conjunto exaustivo de visualizações do ND final (execução com IGD+ ou HV MEDIANO entre as 21) cobrindo todos os 12 problemas sintéticos × os 4…
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF), 2021; roster): Sec. 5 (texto, antes da eq. 2); Fig. 1 — Ilustracao qualitativa em um unico problema (BraninCurrin, ruido gaussiano aditivo de 5% do range de cada objetivo, q=1 sequencial): mostra o…
- **c267** (SAMOEA-TL2M, 2025): Sec. IV-C, Figs. 2–4 — Visualização qualitativa do conjunto não-dominado obtido pelos 6 métodos (5 baselines + SAMOEA-TL2M) na execução associada à mediana do IGD, em três…
- **c276** (ε-PAL, 2016): Sec. 7.4, Fig. 5 — Para o data set SNW, o artigo plota qualitativamente o front ε-acurado Z(P̂) obtido por ε-PAL (linha preta) contra o front verdadeiro Z(P) (linha…
- **c29** (MO P-algorithm, 2014): Sec. 7, Figs. 2, 3 (esquerda), 4, 5, 6 (esquerda), p. 87-90 — Comparação visual/qualitativa, no espaço de objetivos, entre os pontos gerados pelo multi-objective P-algorithm (com limiar 'ideal', mais…
- **c45** (GP-DGS, 2024): Fig. 2 e Sec. 3 Results and Discussion; anotações de PPO na Fig. 2 (ANEXO — OCR, Página 2) — Figura 2: o artigo apresenta os conjuntos Pareto-ótimos (POPS) obtidos em cada cenário de treino (T1–T4) no espaço de objetivos (Qp vs. fOC), com…
- **c48** (IBE-CSEA, 2021): Sec. 4.5, Fig. 5 — Visualização qualitativa das soluções não-dominadas da execução de IGD mediana dos 7 algoritmos em DTLZ1: painéis (a)-(g) mostram a dispersão das… · Sec. 4.6, Fig. 7 — Mesma análise visual da Fig. 5, agora para MaF1: painéis (a)-(g) mostram as soluções não-dominadas finais dos 7 algoritmos com M=3 objetivos contra a…
- **c50** (PD-MOEA, 2018): Sec. 5, Fig. 3, p.14-15 — Com carga fixa em L=300MW e α=0,5, o algoritmo evolutivo de dominância probabilística roda por 20.000 gerações (checagem extra a 10^5 gerações),… · Sec. 6, Fig. 7, p.21-22 — O artigo estende o algoritmo removendo a restrição de carga fixa: a carga passa a ser uma terceira dimensão do arquivo (UBC, NOx, Load), e soluções…
- **c59** (UA-DBO, 2026): Appendix C.4.1, Fig. 4, p. 30 — Para os 6 casos do problema de buffet onset (Apêndice C), o artigo plota a frente não-dominada ACREDITADA pelo modelo (população final, avaliada só…
- **c65** (SABBa, 2022): Sec. 5.1.1, Fig. 6 — Ainda no caso-teste 1 de alta qualidade, o artigo plota qualitativamente a PIOR das 10 execuções (greyscale ∝ POP) para SABBa SA-CS (93 avaliações,… · Sec. 5.1.2, Fig. 8 — Pior das 10 execuções no cenário de baixa qualidade (Fig. 7): SABBa SA-CS (196 avaliações, QB=1.23×10⁻²) contra APMM (200 avaliações, QB=7.94×10⁻¹),… · Sec. 5.2, Fig. 10 — Pior das 10 execuções do caso-teste 2, visualizada em COORDENADAS PARALELAS (por ser D=4, não plotável em 2D): APMM (150 avaliações, QB=1.0×10⁰ —… · Sec. 6.2, Figs. 13-15 — SABBa SA-CS é aplicado à otimização de forma de uma pá de turbina ORC (BI-objetivo: média e variância do desvio-padrão azimutal de pressão ΔP; 1…
- **c66** (PAL-SAPSO, 2019): Sec. IV-A, Fig. 1 — Comparação visual, um painel por problema (os mesmos 8 problemas da Tabela I), das fronteiras não-dominadas obtidas pelos 4 algoritmos contra a…
- **c71** (SAEA/ME, 2020): Figs. 2–8 (Sec. 4.1) — Sete figuras (Figs. 2–8), cada uma com 4 painéis (um por algoritmo), mostram, apenas para n=50, o conjunto não-dominado obtido na execução de MELHOR…
- **c75** (MO-EI/PI (Keane), 2006): Multiobjective Example 1, Fig. 12a-b (p. 889) — No 'Multiobjective Example 1' (viga de Norwacki, M=2: área × tensão de flexão), o artigo compara visualmente os conjuntos de Pareto obtidos por… · Multiobjective Example 2, Fig. 13 (p. 890) — Complementando a Tabela 2, a Fig. 13 mostra visualmente, em dois painéis, os conjuntos de Pareto obtidos pelo P[I]avg (a) e pelo E[I]avg (b) contra…
- **c82** (TC-SAEA, 2022): Sec. 4.4, Figs. 5, 6 e 7 — Para DTLZ2, DTLZ7 e UF3, plota o conjunto não-dominado final obtido por cada um dos 8 algoritmos (Waiting, Fast-first, BI, SI, K-RVEA, HK-RVEA,…
- **c91** (EHVIMOPSO, 2019): Sec. 3.4.3, Figs. 4-12 — Para cada uma das 9 funções-teste, plota a frente de Pareto verdadeira sobreposta ao resultado de uma execução estocástica de cada um dos dois…
- **e1** (EMO, 2014): Sec. 4.3, Fig. 7 — Visualização qualitativa dos conjuntos de Pareto finais gerados em DTLZ2 (9 painéis a-i), comparando a cobertura/distribuição do critério baseado em…
- **e102** (MOEA/D-ASS, 2021): Sec. V-C, Fig. 8 — Gráficos de dispersão dos vetores objetivo não-dominados obtidos pelos sete algoritmos na execução de MELHOR valor de IGD (não a execução mediana) em…
- **e104** (RVMM, 2022): Fig. 5, Sec. IV-C — Gráficos de dispersão do conjunto não-dominado obtido por RVMM, K-RVEA, KTA2 e EIMEGO em DTLZ1 (linear) e DTLZ2 (côncavo), 3 objetivos, D=10,… · Fig. 6, Sec. IV-C — Mesmo esquema da Fig. 5, agora para MaF1 (invertido) e MaF7 (descontínuo), 3 objetivos, D=10, FEmax=300, execução mediana dentre 20.
- **e16** (EGBO, 2024): Sec. Self-driving lab for AgNP experimental campaign, Fig. 3a,b — No único run de cada otimizador na plataforma SDL real de síntese de AgNP (5D de decisão, 3 objetivos, 2 restrições, 15 iterações, lote q=4), o… · Sec. Synthetic studies, Fig. 4a — Para o caso simples de MW7 com apenas n=2 variáveis (EGBO, 3 execuções de 30 iterações), o artigo plota a trajetória de amostragem nos espaços de… · Sec. Synthetic studies, Fig. 4b — Em MW7 com n=8 variáveis (10 execuções, 48 iterações), o artigo plota mapas de densidade de probabilidade de amostragem no espaço de objetivos para… · Sec. Handling input and output constraints, Fig. 5b — Para uma única execução de EGBO com pré-reparo no problema AgNP, o artigo plota a posição das amostras dominadas (discos cinza) e não-dominadas…
- **e17** (MOBO, 2021): Sec. III-B, Fig. 3(e-f) — No mesmo problema de brinquedo 2D, o artigo compara o conjunto de pontos observados no espaco de objetivos (Fig. 3f) contra a frente de Pareto…
- **e3** (HeE-MOEA, 2019): Sec. V-F; Fig. 2 do material suplementar (mencionada, não incluída neste corpus) — Referência textual (não reproduzida na tabela) a uma figura do material suplementar mostrando as soluções não-dominadas obtidas por HeE-MOEA e…
- **e4** (TSEMO, 2018): Sec. 8.2.4; Sec. 8.6, Figs. 9-13; Sec. 8.7 — Para os 5 problemas biobjetivo, o artigo plota, num unico grafico por problema (Fig. 9), a superficie de pior caso de attainment (fracamente dominada…
- **e40** (SBP-BO, 2023): Sec. IV-B-1, Fig. 3 (p.9-10); Figs. S1-S2 (Supplementary material, coordenadas paralelas… — Visualizacao qualitativa do conjunto nao-dominado da execucao com IGD+ mediano (entre 20 execucoes) obtido por K-RVEA, HK-RVEA e SBP-BO em DTLZ2,… · Sec. IV-B-2, Figs. 4-5, p.11-12 — Visualizacao da frente aproximada (execucao com IGD+ mediano) obtida por HK-RVEA e SBP-BO em DTLZ5 (frente-curva de baixa dimensao, degenerada),…
- **e64** (SA-MOPSO (PPD), 2025): Sec. 5.1.1, Table 2, Fig. 8, Fig. 9 — Para cada uma das 3 funções de benchmark (KUR, ZDT, OSY), SA-MOPSO (assistido por GPR) e PB-MOPSO (a mesma MOPSO rodando direto sobre a função… · Sec. 5.2.2, Table 4, Fig. 14 — Além do Run A (desenho inicial 100% inviável), um Run B usa uma população inicial 100% viável as restrições simples (100 de 25.200 vetores gerados…
- **e74** (CLMEA, 2023; roster): Fig. 8 (bi-objetivo DTLZ2/DTLZ5, também ZDT2); Fig. 11 (3-objetivo DTLZ) — Visualização qualitativa do conjunto não-dominado final obtido por cada um dos 6 algoritmos contra a frente de Pareto verdadeira, em problemas…
- **e81** (qPOTS, 2025; roster): Sec. 4.2, Fig. 7 (painel esquerdo) e Fig. 8 — Scatterplots dos pares de objetivos (CD1, CD2) do CRM, com pontos Pareto-ótimos destacados, para qPOTS (Fig. 7 esquerda) e para EHVI/qNEHVI,…
- **e9** (SUR, 2015): Sec. 5.1, Figs. 5-6 — No problema de brinquedo 1D/biobjetivo (Sec. 5.1), dois modelos GP são ajustados a 4 observações iniciais; a tesselação do espaço de objetivos e o… · Sec. 5.1, Fig. 7 — Comparação de desempenho entre o SUR proposto e o SMS-EGO (Ponweiser et al., 2008) no mesmo problema de brinquedo 1D/biobjetivo, usando três… · Sec. 5.2, Fig. 8 — Repetição do mesmo protocolo de comparação SUR vs. SMS-EGO (três indicadores: hipervolume, epsilon, R2) num problema de brinquedo 6D/biobjetivo (Sec.…
- **f9** (UA-IBEA (sigla não-oficial, proposta por mim; paper não nomeia — "Approach 1/2/3"), 2019): Sec. 4, Fig. 4, p. 472 — A Fig. 4 mostra, só para DTLZ2, o gráfico no espaço de objetivos das soluções finais não-dominadas (após reavaliação na função verdadeira) da…
- **jin3** (GS-MOMA / GSM (mono: GS-SOMA), 2010): Sec. IV-C-1, Figs. 9-14 — Para cada um dos 6 problemas MOO (MF1-MF6), o artigo plota as frentes de Pareto obtidas combinando (sobrepondo) os pontos das 20 execuções…
- **mtm6** (EHVI (EI_H) / "EHVI-EGO", 2011): Sec. V-A (Numerical Experiment), parágrafo 'Result' (item c), Fig. 6 (painel… — O artigo roda uma única vez o Algoritmo 1 (otimização bayesiana multiobjetivo genérica guiada por EI_H) no problema-esfera generalizado 2-D…
- **pp6** (AB-MOEA, 2020): Sec. 4.4.2, Fig. 4, Fig. 5 — Visualização qualitativa do conjunto não-dominado obtido por cada um dos 4 algoritmos comparados (K-RVEA, MOEA/D-EGO, SMS-EGO, AB-MOEA), na execução… · Sec. 5, Fig. 6 — Visualização do conjunto não-dominado obtido por cada um dos 3 algoritmos (AB-MOEA, BO, K-RVEA) no problema real do aerofólio, no espaço de objetivos…
- **wang4** (SA-NSGA-II, 2016): Sec. V-D, Fig. 17 e Fig. 18 — Plota o conjunto não-dominado da execução com IGD MEDIANO (dentre as 20 de 1h) para as três configurações da Table III (Fig. 17), e detalha sobre um…

**Complementos e correções (06/09/2026).** Convenção majoritária: 'execução mediana' (c48, c241, c261, e40, wang4, b8 no suplemento), 'melhor execução' (b2, b3, e102), 'pior execução' (c65), percentil 80 (c154). 54/72 fazem a figura; a regra 56 (amostra no texto, resto no repositório) é praticada por quase todos (figuras no suplemento).

**Score (0–10): 8.** **Justificativa.** F. C: 54/72 — a análise mais frequente do corpus (R2#1 27/38); convenções: execução mediana (c48, c241, c261, e40, wang4) × melhor execução (b2, b3, e102) × pior (c65). P média (ilustra, não decide). V: regra 56 (amostra no texto, resto no repositório). Entra com 2–4 painéis escolhidos (um por bloco de família) e a convenção 'execução mediana' declarada.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 16 artigos / 20 análises** — dos 38 iniciais: 7 · dos 7 do roster minerados agora: 1 · dos 27 complementares: 8 · artigos do roster (15): 4.

- **b1** (ParEGO, 2006; roster): Sec. VI-C; Figs. 4, 5 — Para os 4 problemas biobjetivo (KNO1, OKA1, OKA2, VLMOP2), plota-se no mesmo gráfico a superfície de attainment mediana e a pior (método formal de… · Sec. VI-C; Figs. 6, 7, 8, 9 — Para os 4 problemas com 3 objetivos (DTLZ2a, DTLZ4a, DTLZ7a, VLMOP3), plota-se apenas a superfície de attainment do pior caso (sobre as 21 execuções)…
- **b3** (K-RVEA, 2018; roster): Sec. IV-B; Fig. 8 — Para DTLZ2 com 10 objetivos, plota-se um gráfico de coordenadas paralelas do conjunto não-dominado da execução com melhor IGD de K-RVEA e de RVEA,…
- **c105** (SMS-EGO, 2008): Fig. 2(a), p. 790 — Figura 2(a) mostra a superficie de attainment mediana (sobre as 5 execucoes) de cada um dos 3 algoritmos no problema biobjetivo R-ZDT1, sobreposta a…
- **c131** (MORBO, 2022): Apendice F.3 ('Pareto frontiers'), Fig. 10 — Mostra, lado a lado em 3 colunas, as fronteiras nao-dominadas das replicas PIOR/MEDIANA/MELHOR (segundo o HV final) para welded beam, trajectory…
- **c154** (JES, 2022; roster): Sec. 5.2, Fig. 6 — [nova] Hipervolume generalizado (GHV) por região do espaço de objetivos — desempenho local em vez de global · Sec. 4 (texto) e Apêndice L.8, Figs. 26-29 — [nova] Robustez do ranking sob reparametrização do espaço de objetivos — hipervolume generalizado em muitas parametrizações
- **c238** (EIM, 2017; roster): Sec. VIII, Figs. 18-20, Appendix B — Estende os três critérios EIM multiplicando-os pela probabilidade de factibilidade (PoF) de cada restrição (uma Kriging por restrição), formando os…
- **c241** (EMMOEA, 2023): Sec. III-E, Figs. 10-12 — Para 3 problemas de 10 objetivos (DTLZ3, WFG3, WFG9), plotam-se as coordenadas paralelas do conjunto não-dominado da execução de IGD mais próxima da…
- **c50** (PD-MOEA, 2018): Sec. 5.1, Fig. 4d, p.16-17 — Repetindo a otimização de carga fixa 10 vezes de forma independente, o artigo calcula superfícies de atingimento (attainment surfaces, método de… · Sec. 5.2, Fig. 6, p.19-20 — Para as dez soluções x1 a x10 selecionadas na Figura 5b (cobrindo a faixa de trade-off UBC-NOx), a Figura 6 mostra, num gráfico de coordenadas…
- **c65** (SABBa, 2022): Sec. 5.2, Fig. 10 — Pior das 10 execuções do caso-teste 2, visualizada em COORDENADAS PARALELAS (por ser D=4, não plotável em 2D): APMM (150 avaliações, QB=1.0×10⁰ —…
- **c75** (MO-EI/PI (Keane), 2006): Multiobjective Example 1, Fig. 12a-b (p. 889) — No 'Multiobjective Example 1' (viga de Norwacki, M=2: área × tensão de flexão), o artigo compara visualmente os conjuntos de Pareto obtidos por…
- **e16** (EGBO, 2024): Sec. Synthetic studies, Fig. 4b — Em MW7 com n=8 variáveis (10 execuções, 48 iterações), o artigo plota mapas de densidade de probabilidade de amostragem no espaço de objetivos para…
- **e21** (PIO, 2025): Fig. 6; Results, 'Optimization results of multi-objective tasks' — Para as 6 tarefas multi-objective, visualiza em coordenadas paralelas os valores reais dos top-50 candidatos de cada método (WS, NMD, NMD-WS, PIO),…
- **e4** (TSEMO, 2018): Sec. 8.2.4; Sec. 8.6, Figs. 9-13; Sec. 8.7 — Para os 5 problemas biobjetivo, o artigo plota, num unico grafico por problema (Fig. 9), a superficie de pior caso de attainment (fracamente dominada…
- **e40** (SBP-BO, 2023): Sec. IV-B-1, Fig. 3 (p.9-10); Figs. S1-S2 (Supplementary material, coordenadas paralelas… — Visualizacao qualitativa do conjunto nao-dominado da execucao com IGD+ mediano (entre 20 execucoes) obtido por K-RVEA, HK-RVEA e SBP-BO em DTLZ2,…
- **jin3** (GS-MOMA / GSM (mono: GS-SOMA), 2010): Sec. IV-C-1, Figs. 9-14 — Para cada um dos 6 problemas MOO (MF1-MF6), o artigo plota as frentes de Pareto obtidas combinando (sobrepondo) os pontos das 20 execuções…
- **mtm4** (MAES (variante MO: M-NSGA-II), 2006): Sec. V-G, Figs. 29, 30, 31 (p.13) — Para os problemas de Schaffer generalizados 10-D com frente de Pareto de curvatura escalável por γ (γ=2 convexa, γ=1 linear, γ=0.5 côncava), o artigo… · Sec. VI, Figs. 33, 34, 35 (pp.15-16) — No caso real de otimização aerodinâmica do perfil RAE 2822 (3 objetivos — arrasto em 3 pontos operacionais — e 6 restrições de sustentação/momento,…

**Complementos e correções (06/09/2026).** Attainment (EAF/median attainment): b1, c105, e4, c50; coordenadas paralelas (M ≥ 4): b3, c241, c65, e21; GHV por região e por reparametrização (c154). Poucos problemas da bateria têm M ≥ 4.

**Score (0–10): 5.** **Justificativa.** N. C: 16/72 (attainment: b1, c105, e4, c50; coordenadas paralelas: b3, c241, c65, e21; GHV regional em c154). P média: EAF é honesta para o pior caso, coordenadas paralelas só valem em M ≥ 4 (a bateria tem poucos). Apêndice; 54 cobre o essencial.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 0 artigos.** Nenhuma análise dos 72 foi mapeada a esta ficha — leitura própria da tese (ou regra/nota), sem correspondente nomeado no corpus.

**Score (0–10): 8.** **Justificativa.** R (regra editorial). C: 0/72 como regra, mas 6/38 'material suplementar mencionado' (R2#14) e a maioria dos 72 remete figuras ao suplemento (b3, b8, c261, e7, e74, e102, e103 — Anexo 7 marca 'só mencionada'). Aplicar: amostra no texto, resto no repositório com índice.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 1 artigos / 1 análises** — dos 38 iniciais: 1 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 0 · artigos do roster (15): 0.

- **b7** (DR (Dual-Ranking), 2026): Table 2 (legenda); Sec. 4.4 ('as most baseline methods cannot handle constraints') — Cobertura da bateria de comparação com baselines: os 3 problemas restringidos (BNH, Truss2D, Welded Beam) são excluídos INTEIRAMENTE da comparação…

**Score (0–10): 9.** **Justificativa.** F-parcial. C: 1/72 (b7 declara cobertura) — o corpus não reporta células faltantes (roda tudo ou omite). P: obrigação de transparência do contrato honesto (16.811 células; 16.021 ok / 790 failed; 615 ⚪). V: censo canônico 22/08, C6/C8. Entra como tabela no apêndice + frase no corpo; decisão 13 (corpo × apêndice).


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 4 artigos / 4 análises** — dos 38 iniciais: 1 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 3 · artigos do roster (15): 0.

- **b7** (DR (Dual-Ranking), 2026): Table 2 (legenda); Sec. 4.4 ('as most baseline methods cannot handle constraints') — Cobertura da bateria de comparação com baselines: os 3 problemas restringidos (BNH, Truss2D, Welded Beam) são excluídos INTEIRAMENTE da comparação…
- **e21** (PIO, 2025): Results, 'Surrogate model and UQ performance' (texto principal); Supplementary Figs. S1,… — [nova] Falhas de convergência do treino do UQ por dataset
- **e8** (NN-EGO, 2020): Table S7 (S18) — [nova] Taxa de sucesso/falha da avaliação real (DFT) por geração e causa
- **mtm4** (MAES (variante MO: M-NSGA-II), 2006): Sec. VI, Fig. 32 (p.15) — [nova] Taxa de soluções factíveis por execução (eficiência de tratamento de restrições)

**Complementos e correções (06/09/2026).** Falhas nomeadas no corpus: b7 (baselines não tratam restrições), e21 (perda MVE diverge; evidencial não converge), e8 (49–64% das simulações DFT bem-sucedidas, com o E[I] insistindo em regiões de baixa conversão), mtm4 (factíveis por execução). A nossa tabela (orçamento 4.645; teto de parede 615; checkpoint 158) é da mesma natureza: incapacidade sob o protocolo.

**Score (0–10): 8.** **Justificativa.** N. C: 4/72 nomeiam falhas (b7 baselines sem restrições; e21 divergência do treino de UQ; e8 49–64% de DFT bem-sucedidas; mtm4 factíveis) — 'a incapacidade é resultado' é leitura própria. P alta: c154 (439 células failed), c262 (158), c122 (98), c149 (72), e81 (22) — orçamento 4.645 e teto de parede 615 são resultados sobre o custo da incerteza (métodos informacionais/BO não cabem em 31D−1 sob 12 h). D pronta (censo). Entra como tabela curta com julgamento pela referência.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 0 artigos.** Nenhuma análise dos 72 foi mapeada a esta ficha — leitura própria da tese (ou regra/nota), sem correspondente nomeado no corpus.

**Score (0–10): 6.** **Justificativa.** T. C: 0/72 (o corpus não mede piso de ruído entre repetições da mesma configuração). P: dá a região de equivalência de 5 e a tolerância de 3; útil, não é resultado. Apêndice (decisão 4).


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 2 artigos / 2 análises** — dos 38 iniciais: 2 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 0 · artigos do roster (15): 1.

- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF), 2021; roster): Apendice J, Fig. 19 — Recomputacao do desempenho dos metodos principais usando uma definicao alternativa de 'resposta do algoritmo': em vez do conjunto nao-dominado bruto…
- **c81** (UA-MORL-Diff, 2025): Appendix C.3, Table C.2 — Reexecuta a comparação da Tabela 1 (4 baselines RL vs. 'Ours', QM9) trocando a formulação de recompensa binária original dos baselines por uma soma…

**Score (0–10): 7.** **Justificativa.** T. C: 2/72 (c262 'resposta alternativa'; c81 troca a recompensa) refazem o placar sob outra definição. P: robustez do veredito às políticas de cobertura (P1/P2/FE comum) é obrigatória dado 790 células failed; se o placar não muda, uma frase; se muda, uma tabela. Entra no apêndice com a frase no corpo (decisão 2).


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 2 artigos / 2 análises** — dos 38 iniciais: 1 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 1 · artigos do roster (15): 0.

- **c105** (SMS-EGO, 2008): Sec. 3.1, p. 786 — O artigo revisa o metodo de Keane (EI multiobjetivo via probabilidade de dominancia do conjunto de Pareto) mas declara explicitamente que ele nao…
- **e21** (PIO, 2025): Results, 'Optimization results of single-objective task' (parágrafo final, após a Tabela… — Discute, com base nos resultados da Tabela 2, por que DOM, EI e PIO falham simultaneamente em três tarefas (singlet-triplet gap, escore 1SYH,…

**Score (0–10): 8.** **Justificativa.** F-parcial. C: 2/72 nomeiam o que não respondem (c105, e21) — mas 268 passagens de resultados negativos/ressalvas minadas (Anexo 8.3) mostram que o corpus se defende em prosa. P: 'o que a bateria não responde' inclui agora, pela diretriz (1), o contrafactual, o sweep e o lote — precisa ser reescrita. V: decisão 9 (onde moram as limitações: cap. 4 §4.9, cap. 5 ou cap. 6 §6.3). Entra, e é onde 15/63/64 são citadas.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 3 artigos / 3 análises** — dos 38 iniciais: 1 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 2 · artigos do roster (15): 1.

- **b3** (K-RVEA, 2018; roster): Sec. IV-B, antes da Table I (p. 8-9) — Discussão metodológica, antes da Tabela I, sobre como a escolha do tamanho do conjunto de referência do IGD e do ponto de referência do hypervolume…
- **c267** (SAMOEA-TL2M, 2025): Sec. IV-E, Remark 2 — Nota de esclarecimento (Remark 2) sobre por que algumas células da Tabela VII mostram HV=0: o conjunto não-dominado do algoritmo, naquele problema…
- **e3** (HeE-MOEA, 2019): Sec. V-D, Table I — Tabela com a média (linha 1) e desvio-padrão (linha 2) de HV para HeE-MOEA e GP-MOEA, em 16 problemas de teste (DTLZ1-7, WFG1-9) com N=40 variáveis…

**Score (0–10): 6.** **Justificativa.** R (notas). C: 3/72 (b3 sobre tamanho do conjunto de referência do IGD; c267 HV = 0; e3). Notas de régua/clip obrigatórias (ideais arredondados A53; decisão 8; ficha 81 é a robustez correspondente). Entra como nota.



### 70. Validação numérica do estimador da aquisição (MC × analítico; aproximações; corretude)

**Fontes.** [MIN] 17 análises em 12 artigos (lista abaixo) · [PL-38] R2#20 (2/38) · ficha 30 (sanidade do pipeline).

**O que analisa.** Checagens de que o número da aquisição está certo: qEHVI MC × EHVI analítico e gradiente amostral × exato (c100), EIHV exato × aproximado (c107), RFF × amostragem exata por dimensão (c131: RFF degrada em alta D), sensibilidade a S/p e às aproximações de entropia JES-0/LB/LB2/MC (c154: 'recomendamos contra a estimativa de variância zero'), |PF| (c214), S (c222: MESMO robusto com S=1, PESMO não), β_t exato do Teorema 1 (c276), POPmin × POPtrue (c65), fórmula fechada × código de referência (e1), Nyström (e81: 'sem perda, ganho leve'), IS/MCS × exato com R² por M (e86: concordância cai com M), proxy de informação × HMC (b15 ρ=0,96).

**Dados.** Nenhuma: a instrumentação não grava o valor da aquisição nem uma referência exata. (⑥ grava o ponto escolhido; alguns algoritmos logam o valor — verificar por algoritmo, ficha 78.)

**Objetivo.** Nos artigos: garantir que a implementação do critério é correta antes de compará-lo. Na dissertação: não se aplica (usamos implementações publicadas/oficiais — cap. 4 homologação, §D9.5).

**O que busca revelar.** Que as aproximações baratas costumam bastar (c154, c222, e81) exceto quando M cresce (c154 Marine M=4; e86) ou D cresce (c131) — argumento para o cap. 6.

**Como é realizada.** Comparação do valor/gradiente do critério calculado de duas formas nos mesmos pontos; dispersão com R²; curvas de desempenho por variante do estimador.

**Técnicas.** Correlação/R² entre estimadores; curvas por variante; teste em problema de brinquedo.

**Implementação.** Não implementável sem gravar o critério; a homologação (§D9.5) e a ficha 30 são o nosso equivalente.

**Em quantos artigos aparece (dos 72).** 12 artigos (17 análises): dos 38 iniciais 6, dos 7 do roster 1, dos 27 complementares 5; do roster (15): 2. Nas planilhas dos 38 (Ranking 2) o tipo mais próximo está indicado em Fontes.

**Estado.** N — não entra.

**Demais detalhes.** Registro para 61/cap. 6 (as aproximações usadas pelos 15 são as dos autores). Relação: 30, 78.

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 12 artigos / 17 análises** — dos 38 iniciais: 6 · dos 7 do roster minerados agora: 1 · dos 27 complementares: 5 · artigos do roster (15): 2.

- **b15** (U-RankMOEA, 2026): Apendice H, Fig. 8 — [nova] Fidelidade do proxy de ganho de informacao (MC-Dropout) contra uma referencia gold-standard num problema de brinquedo · Apendice J.7, Table 10 — [nova] Estimacao empirica do fator de fidelidade da aquisicao (rho) e das constantes do limite teorico de HV
- **c100** (qEHVI, 2020): Fig. 5a (Apêndice — ausente deste corpus); citado na Sec. 3.3 — [nova] Acurácia da estimativa Monte Carlo do qEHVI vs. EHVI analítico · Fig. 5b (Apêndice — ausente deste corpus); citado na Sec. 4.1 — [nova] Acurácia do gradiente amostral do qEHVI vs. gradiente exato do EHVI (M=3)
- **c107** (MS-VHGP-EIHV, 2017): Sec. III-E2, Figs. 10-11 — [nova] Fidelidade numérica da aproximação do critério de aquisição (EIHV exato x aproximado) · Sec. II-C — [nova] Comparação informal LOO x log-pseudo-verossimilhança como critério de seleção de modelo · Appendix — [nova] MCMC x Monte Carlo ingênuo para a verossimilhança marginal (aparte do Apêndice)
- **c131** (MORBO, 2022): Apendice A.1 ('RFFs for fast posterior sampling'), Fig. 6 — [nova] Fidelidade da amostragem posterior aproximada (RFF) vs. exata para Thompson Sampling, por dimensao
- **c154** (JES, 2022; roster): Apêndice L.3, Figs. 14, 15, 16 — [nova] Sensibilidade da aquisição aos hiperparâmetros de estimação (nº de amostras MC S; nº de pontos ótimos p) · Apêndice L.6, Figs. 20, 21 — [nova] Comparação das estratégias de aproximação numérica da entropia condicional (JES-0/LB/LB2/MC; MES-0/LB/LB2/MC)
- **c214** (PFES, 2020): Sec. 6.1, Fig. 4 (texto); anunciado em Sec. 3.2.1 — [nova] Sensibilidade de PFES ao nº de amostras MC da Pareto-frontier (|PF|)
- **c222** (MESMO, 2019): Sec. 5.2 (parágrafo 'MESMO vs. State-of-the-art', entre a Fig. 2 e a Table 1) — [nova] Robustez da qualidade e do custo ao número de amostras Monte-Carlo (S) do termo de entropia
- **c276** (ε-PAL, 2016): Sec. 7.4, Fig. 6 — [nova] Validação empírica da garantia teórica de corretude (β_t exato do Teorema 1, ε=0)
- **c65** (SABBa, 2022): Sec. 3.2, Table 1 (exemplos da Fig. 2a-b) — [nova] Validação numérica de POPmin (aproximação) contra POPtrue (exato, combinatorial) em exemplos ilustrativos
- **e1** (EMO, 2014): Sec. 3.3.1 — [nova] Verificação de corretude da fórmula fechada da EI/PoI multiobjetivo contra implementação de referência e Monte Carlo
- **e81** (qPOTS, 2025; roster): Sec. 4.1 (parágrafo após Fig. 4), Fig. 4 e Fig. 5 — [nova] Ablação da aproximação de Nyström (exata vs Nystrom-Pareto)
- **e86** (NSGAIII-EHVI, 2023): Sec. IV-C, Fig. 3 — [nova] Fidelidade do critério de aquisição aproximado (IS/MCS) em relação ao cálculo exato, por nº de objetivos

**Score (0–10): 2.** **Justificativa.** Gate: não aplicável — a instrumentação não grava o valor do critério de aquisição nem um cálculo de referência; validar estimadores (MC × analítico, Nyström, RFF) é tarefa dos artigos de método. C: 12/72 (R2#20 2/38; c100, c107, c131, c154, c214, c222, c276, c65, e1, e81, e86, b15). A ficha 30 (monotonicidade) é a única sanidade análoga. Não entra.


### 74. Robustez a ruído injetado nas avaliações (fora do recorte epistêmico)

**Fontes.** [MIN] 6 análises em 5 artigos (lista abaixo) · [PL-38] R2#18 (3/38; R1#11 'não recomendada') · [CAP4] bateria determinística (sem ruído).

**O que analisa.** Desempenho sob ruído gaussiano injetado: c149 (peso α/β do termo aleatório: sem peso, 93% das amostras vão para o máximo ruidoso), c154 (ParEGO × NParEGO, EHVI × NEHVI: 'ignorar o ruído vai razoavelmente bem'), c262 (controle SEM ruído: qNEHVI não perde quando não há ruído a tratar), e81 (σ² ∈ {0, 1e-6, 1e-4, 1e-3}), b14 (IBEA × NSGA-II sob ruído, sem surrogate).

**Dados.** Nenhuma (a bateria é sem ruído). O regime 'noiseless' de c262 corresponde ao nosso — ①.

**Objetivo.** Nos artigos: mostrar que a incerteza aleatória modelada protege contra ruído. Na dissertação: fora do recorte (epistêmico); só nota.

**O que busca revelar.** Que modelar ruído nem sempre paga (c154) e não custa quando não há ruído (c262) — útil para ler qNEHVI (roster) na bateria determinística.

**Como é realizada.** Níveis de σ² injetado; curvas HV × iteração; contagem de amostras na região ruidosa.

**Técnicas.** Ruído aditivo controlado; curvas por nível.

**Implementação.** Nenhuma.

**Em quantos artigos aparece (dos 72).** 5 artigos (6 análises): dos 38 iniciais 3, dos 7 do roster 2, dos 27 complementares 0; do roster (15): 4. Nas planilhas dos 38 (Ranking 2) o tipo mais próximo está indicado em Fontes.

**Estado.** N — não entra (fora do recorte).

**Demais detalhes.** Nota em 16/61: c262 é 'noise-aware' rodando sem ruído — o resultado do artigo (Fig. 15) diz que isso não o penaliza. Relação: 61.

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 5 artigos / 6 análises** — dos 38 iniciais: 3 · dos 7 do roster minerados agora: 2 · dos 27 complementares: 0 · artigos do roster (15): 4.

- **b14** (SA²-MOEA, 2024): Sec. 2.2.2, Table 1 — [nova] Robustez de mecanismos de seleção ambiental (dominância+crowding vs. indicador Iε+) a ruído gaussiano injetado -…
- **c149** (LBN-MOBO, 2023; roster): Sec. 5.5, Fig. 6 — [nova] Robustez a ruído irredutível via peso (α, β) do termo aleatório na aquisição · Sec. 5.5, Fig. 7 — [nova] Robustez a ruído irredutível via peso (α, β) do termo aleatório na aquisição
- **c154** (JES, 2022; roster): Apêndice L.7, Fig. 22 — [nova] Comparação entre variantes gulosas e cientes de ruído dos métodos por melhoria (ParEGO x NParEGO; EHVI x NEHVI)
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF), 2021; roster): Apendice H.7, Fig. 15 — [nova] Controle sem ruido -- placar sob sigma=0
- **e81** (qPOTS, 2025; roster): Apêndice 5.3, Fig. 12 — [nova] Robustez a ruído de observação injetado (ablação de σ²)

**Score (0–10): 1.** **Justificativa.** Fora do recorte epistêmico (R1#11): a bateria é sem ruído. C: 5/72 (b14, c149 α/β, c154 gulosos × cientes de ruído — 'ignorar o ruído vai tão bem quanto modelá-lo', c262 controle sem ruído, e81). O único aproveitamento é textual: c262 (qNEHVI, do roster) mostra que a maquinaria ciente de ruído não penaliza sem ruído — o nosso regime. Não entra; nota em 16/61.


### 76. Comparação com resultados publicados (fora do protocolo, orçamento não pareado)

**Fontes.** [MIN] 3 análises em 3 artigos (b1 vs EANA; jin3 vs Deb & Nain; c10 vs MOEA-RSFMMA no suplemento) · [CAP4] homologação das implementações (§D9.5).

**O que analisa.** Confrontar o próprio número com o publicado por terceiros no mesmo problema, sem pareamento de orçamento/implementação (b1: 'comparison is difficult').

**Dados.** ① (endpoint por célula) + números publicados (b3 Table I, b4 Table III, c122, c141, c217, e7, e74 nas mesmas DTLZ/WFG/ZDT).

**Objetivo.** Sanidade: as implementações da bateria (oficiais/PlatEMO/BoTorch) reproduzem a ORDEM DE GRANDEZA publicada em DTLZ/ZDT/WFG sob orçamento parecido? (proteção contra bug de configuração).

**O que busca revelar.** Discrepâncias grosseiras (uma ordem de grandeza) que indicariam erro de implementação ou de régua; nada além disso é interpretável (orçamentos, D, M e réguas diferem).

**Como é realizada.** Tabela pequena: para 4–6 (algoritmo, problema) com orçamento próximo de 31D−1 nos artigos, IGD publicado × IGD/IGD+ nosso (mesma régua, se possível); comentário.

**Técnicas.** Comparação descritiva; sem teste.

**Implementação.** Manual (ler tabelas dos artigos); uma tarde.

**Em quantos artigos aparece (dos 72).** 3 artigos (3 análises): dos 38 iniciais 2, dos 7 do roster 0, dos 27 complementares 1; do roster (15): 1. Nas planilhas dos 38 (Ranking 2) o tipo mais próximo está indicado em Fontes.

**Estado.** N — não recomendada como análise; como sanidade do cap. 4 (homologação), opcional.

**Demais detalhes.** Relação: 61, §D9.5. Cuidado com N15 (nenhum número de b15).

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 3 artigos / 3 análises** — dos 38 iniciais: 2 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 1 · artigos do roster (15): 1.

- **b1** (ParEGO, 2006; roster): Sec. III-B; Table III — [nova] Comparação heterogênea com resultado publicado de outro algoritmo (orçamento não pareado)
- **c10** (SP-RV-MOEANet, 2021): Sec. SP-RV-MOEANet / The Framework; Supplementary Materials I — [nova] Comparação conceitual do framework MOEA-RSFMMA vs. SP-RV-MOEANet (material suplementar)
- **jin3** (GS-MOMA / GSM (mono: GS-SOMA), 2010): Sec. IV-C-1 — [nova] Validação cruzada com resultado publicado na literatura

**Score (0–10): 3.** **Justificativa.** Não alinhada ao protocolo (orçamentos e implementações diferentes). C: 3/72 (b1 vs EANA, jin3 vs Deb & Nain, c10). O único uso é sanidade: conferir se ParEGO/K-RVEA/CSEA na bateria ficam na ordem de grandeza dos números publicados em DTLZ (proteção contra bug de implementação) — uma frase no cap. 4. Não entra como análise.


### 81. Sensibilidade do placar ao ponto de referência do HV e à normalização (régua)

**Fontes.** [MIN] 2 análises em 2 artigos (c261: z* da decomposição — 'pouco sensível, exceto ZDT1–3 e DTLZ7'; e86: método de Ishibuchi para o ponto de referência — 'sem melhora evidente') · fichas 61/62 (avisos de régua; ideais arredondados A53) · [REG] D69 (referência 1,1), S.5 (ideal/nadir).

**O que analisa.** Se as conclusões do placar (1/3/9) mudam quando a referência do HV vai de 1,1 para 1,2 ou para a regra de Ishibuchi (1 + 1/H), e quando a normalização usa os ideais exatos em vez dos arredondados (ZDT6/MMF4/MMF1 — A53).

**Dados.** ① (ND por célula — recomputar HV); M (réguas `F_MIN_MAX`; ideais alternativos).

**Objetivo.** Robustez de régua: mostrar que o veredito não depende da convenção (ou onde depende).

**O que busca revelar.** Problemas em que o ranking inverte com a referência (frentes com extremos longos — DTLZ7, WFG desconexos) e o efeito dos ideais arredondados.

**Como é realizada.** Recomputar HV para 3 referências × 2 réguas; comparar rank médio (2) e símbolos (3) entre variantes; tabela de concordância (Kendall τ entre rankings).

**Técnicas.** Recomputação de HV; Kendall τ; tabela de inversões.

**Implementação.** `metrics.metrics_of_set` com `reference_bounds` alternativos — uma célula; custo de cômputo (HV para 16.020 células × 6 variantes) moderado.

**Em quantos artigos aparece (dos 72).** 2 artigos (2 análises): dos 38 iniciais 1, dos 7 do roster 0, dos 27 complementares 1; do roster (15): 0. Nas planilhas dos 38 (Ranking 2) o tipo mais próximo está indicado em Fontes.

**Estado.** N — dado pronto.

**Demais detalhes.** Relação: 1, 2, 3, 61, 62; decisão 8 (ideais arredondados: manter declarando × recomputar — esta ficha responde 'quanto muda').

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 2 artigos / 2 análises** — dos 38 iniciais: 1 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 1 · artigos do roster (15): 0.

- **c261** (DirHV-EGO, 2024): Supplementary Sec. III-A.1, p.5-6, Fig. 5 (Supplementary) — [nova] Sensibilidade ao ponto de referência z* (Utopian point) da decomposição/Tchebycheff
- **e86** (NSGAIII-EHVI, 2023): Sec. IV-A, p. 8 — [nova] Efeito do método de especificação do ponto de referência do HV

**Score (0–10): 6.** **Justificativa.** Reproduzível e barata de ①: recomputar HV com referência 1,1 × 1,2 × Ishibuchi e conferir se o placar (1/3) muda. C: 2/72 (c261 z*; e86 método de Ishibuchi 'sem melhora evidente'). P: robustez de régua exigida pelos ideais arredondados (A53) e pelas notas 61/62 — se nada muda, uma frase; se muda, apêndice. Entra como verificação (decisão 8).

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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 4 artigos / 6 análises** — dos 38 iniciais: 3 · dos 7 do roster minerados agora: 0 · dos 27 complementares: 1 · artigos do roster (15): 0.

- **b13** (AdaMoR-DDMOEA, 2025): Sec. 5.3, Figure 3 — Sensibilidade do AdaMoR-DDMOEA ao TAMANHO do dataset offline inicial: tamanhos 1D, 5D, 10D, 15D, 20D, 25D e 30D (D = nº de variáveis de decisão),…
- **b7** (DR (Dual-Ranking), 2026): Material Suplementar, Sec. 1.2 (Prediction Results with 1000 Training data); Sec. 4.4… — Síntese transversal (Seções 4.2, 4.4 e Suplemento 1.2) de como o TAMANHO do dataset offline inicial (11D-1 'limited' vs. 1.000 amostras) afeta tanto…
- **c45** (GP-DGS, 2024): Sec. 2.2 (definição da métrica) e Table 1, Sec. 3 Results and Discussion — Tabela 1: o artigo reporta o erro quadrático médio normalizado (NRMSE) entre as predições dos GPs e os valores 'verdadeiros' calculados por SEAWAT,… · Fig. 2 e Sec. 3 Results and Discussion; anotações de PPO na Fig. 2 (ANEXO — OCR, Página 2) — Figura 2: o artigo apresenta os conjuntos Pareto-ótimos (POPS) obtidos em cada cenário de treino (T1–T4) no espaço de objetivos (Qp vs. fOC), com… · Sec. 3 Results and Discussion, parágrafo de abertura — O artigo menciona, sem apresentar dados (nem tabela, nem figura), testes preliminares que variam o número de pontos de treino permitido (NM) na…
- **f9** (UA-IBEA (sigla não-oficial, proposta por mim; paper não nomeia — "Approach 1/2/3"), 2019): Sec. 4 (Experimental Results), Table 1, p. 471 — Tabela 1 reporta média e desvio-padrão do IGD (5000 pontos de referência) do arquivo final não-dominado -- obtido após a busca sobre os modelos…

**Complementos e correções (06/09/2026).** Diretriz (1): descartada. Convenção do offline no corpus: b13 (1D–30D), b7 (11D−1 × 1000), c45 (cenários T1–T4), f9, e103 (LHS × aleatória: 'pouco efeito'). Declarar em 61.

**Diretriz (1) de 06/09/2026.** Sem novos experimentos: esta candidata está **DESCARTADA** (permanece no catálogo como registro; é citada em 61 como limitação).

**Score (0–10): 0.** **Justificativa.** DESCARTADA pela diretriz (1): o sweep offline de volume de dados (c311, treed_media; small/medium/big × LHS/MVNS) está só em s42 (121 células) e exigiria as 29 sementes restantes. C: 4/72 (b13 varre 1D–30D; b7 11D−1 vs 1000; c45; f9; R2#13 7/38) — convenção do offline, portanto limitação a declarar (61). Fica como registro.


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

**Adendo 06/09/2026 — mineração definitiva (72 artigos).**

**Referências no corpus (mineração definitiva, 72 artigos): 11 artigos / 21 análises** — dos 38 iniciais: 6 · dos 7 do roster minerados agora: 2 · dos 27 complementares: 3 · artigos do roster (15): 4.

- **c1** (BS-MOBO, 2018): Sec. IV-C, Fig. 6 — [nova] Sensibilidade ao tamanho do lote (parâmetro de paralelismo k) sobre a frequência de retreino
- **c100** (qEHVI, 2020): Sec. 5.1, Fig. 4(a-b) — Desempenho de otimização paralela no problema ABR variando o tamanho do lote q em {1,2,4,8}, visto por (a) iteração de BO (lote) e (b) avaliações de… · Fig. 11 (Apêndice — ausente deste corpus); citado na Sec. 3.3 — [nova] Escalabilidade do tempo de computação do qEHVI com o tamanho do lote q (saturação de hardware)
- **c123** (EPBII / EIPBII, 2017): Sec. VI-C, Figs. 24, 25 — Estudo de sensibilidade ao tamanho do lote de pontos adicionados por iteração (nadd = 3, 5, 10) para EPBII e EIPBII no problema LZ08-F2, plotando o…
- **c149** (LBN-MOBO, 2023; roster): Sec. 3, Fig. 1 — [nova] Curva de escalabilidade por tamanho de lote (batch size): HV e tempo em função de S · Sec. 5.1, Fig. 3 — [nova] Curva de escalabilidade por tamanho de lote (batch size): HV e tempo em função de S · Sec. C.3, Fig. 13 — [nova] Curva de escalabilidade por tamanho de lote (batch size): HV e tempo em função de S · Sec. B.1.3 (método); Figs. 11, 15(c), 16(c), 18(c) (aplicações) — [nova] Regret de Pareto cumulativo em lote (batch) × iteração — métrica alternativa à trajetória de IGD+/HV
- **c154** (JES, 2022; roster): Sec. 5.2, Fig. 5 (painel inferior) — Mesma comparação de algoritmos (JES-LB, Sobol, TSEMO, NParEGO, NEHVI, PES, MES-LB) nos mesmos 4 problemas, agora no regime EM LOTE: log HV…
- **c261** (DirHV-EGO, 2024): Sec. V-C, p.9-10, Table IV — Compara os quatro algoritmos paralelos completos (KB&EHVI-EGO, PEIM-EGO, MOEA/D-EGO, DirHV-EGO — cada um com sua própria estratégia de seleção de q… · Sec. V-C, p.9, Fig. 5 (+ Figs. 11-12, Supplementary Sec. VI) — Curvas de convergência (log IGD+ × FE) para os quatro algoritmos paralelos da análise anterior. O corpo principal mostra q=5 (12 problemas); o… · Sec. V-D.2, p.11, Fig. 6 — [nova] Escalabilidade do tempo de CPU com o tamanho do lote (batch size q) · Supplementary Sec. III-A.2, p.6, Fig. 6 (Supplementary) — Varre o tamanho de lote q ∈ {1,2,5,8,10,15,20} para DirHV-EGO sozinho (mantendo Ctotal fixo, então q maior implica menos iterações/retreinos do GP) e…
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF), 2021; roster): Fig. 4 (Sec. 9); Fig. 13 (Apendice H.3, mesma analise reapresentada) — Qualidade final da frente de Pareto (log HV diff) sob orcamento fixo de 224 avaliacoes, variando o tamanho do lote q em {1,8,16,32}, para os mesmos 8… · Fig. 9(b,c) (Apendice H.3); Fig. 11 (mesmos dados, eixo x em avaliacoes) — Curvas de 'anytime performance' (log HV diff x avaliacoes de funcao OU x iteracao de lote) decompostas por tamanho de lote q, para os metodos… · Fig. 10 (Apendice H.3); Fig. 12 (mesmos dados, eixo x em avaliacoes) — Mesma familia de curvas 'anytime', restrita a comparacao dentro da familia EHVI: qNEHVI (via CBD) vs. qEHVI-PM-CBD, em varios q, isolando o efeito… · Apendice H.4 — Reanalise diagnostica dos dados da analise 'Fig. 4/13' focada num achado especifico e contra-intuitivo: em varios problemas, qEHVI (que ignora ruido)…
- **c82** (TC-SAEA, 2022): Sec. 4.8 (Parameter Sensitivity Analysis); Fig. S3 (material suplementar, não incluído… — Investiga, via boxplots de IGD na suíte DTLZ (Fig. S3, material suplementar), a sensibilidade de TC-SAEA ao parâmetro u — o número de novas soluções…
- **e104** (RVMM, 2022): Sec. IV-H; Tables SIV-SV e SVI-SVII (material suplementar, não visível no corpus) — Compara a estratégia de infill de UMA solução por rodada de atualização do surrogate (RVMM) com uma variante que consulta um LOTE de u=5 soluções por…
- **e4** (TSEMO, 2018): Sec. 8.1; Sec. 8.7; Sec. 9 (Conclusoes) — O artigo estende a heuristica gulosa de selecao em lote do TSEMO (a cada iteracao, escolher sequencialmente 4 pontos do conjunto candidato que mais…
- **e81** (qPOTS, 2025; roster): Sec. 4.1, Fig. 5 — As mesmas curvas de HV × avaliações, agora em modo lote (q=2 e q=4), nos mesmos 4 problemas sintéticos, com a mesma lista de concorrentes sufixados…

**Complementos e correções (06/09/2026).** Diretriz (1): descartada. Convenção do BO em lote: c100 (q ∈ {1,2,4,8}), c262 (224 avaliações, q variável), c261 (q ∈ {1…20}), c154 (q ∈ {2,4,8}), e81 (q = 2, 4), c149 (lotes 10¹–10³), c1 (k), c123 (nadd), e4 (b = 4). Declarar em 61.

**Diretriz (1) de 06/09/2026.** Sem novos experimentos: esta candidata está **DESCARTADA** (permanece no catálogo como registro; é citada em 61 como limitação).

**Score (0–10): 0.** **Justificativa.** DESCARTADA pela diretriz (1): o sub-estudo de lote (q = 10) tem 23 células só em s42. C: 11/72 fazem sensibilidade ao lote (c1, c100, c123, c149, c154, c261, c262, c82, e104, e4, e81 — 4 do roster) — convenção do BO em lote; o cap. 4 já declara como não concluído. Fica como limitação (61).


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

# Anexo 5 — Ranking por score (06/09/2026; recomendação do agente, não decisão)

| Score | Ficha | Nome | Refs (de 72) | Obs. |
|---|---|---|---|---|
| 10 | 1 | Matrizes de mediana do IGD+ e do HV, algoritmo × problema | 53 |  |
| 10 | 26 | Trajetórias de convergência — mediana + IQR × fração do orçamento, com a banda dos pisos | 44 |  |
| 10 | 11 | Ablação exata do σ — Prob-MOEA/D × MOEA/D-média, em duas leituras | 25 |  |
| 10 | 9 | Assistido × piso casado — Δ IGD+ pareado por semente e placar por algoritmo | 19 |  |
| 10 | 33 | Sonda, dimensão 3 — a calibração do σ (a incerteza reportada é confiável?) | 13 |  |
| 9 | 3 | "Quem empata com o melhor" — teste de postos vs. o melhor de cada problema (+/=/−) | 28 |  |
| 9 | 48 | O custo com o tempo de ajuste do modelo — a decomposição fit / busca / sonda / avaliação | 20 |  |
| 9 | 31 | Sonda, dimensão 1 — a acurácia da média ao longo do orçamento (o modelo aprende? esquece?) | 19 |  |
| 9 | 7 | Tendência com a dimensão D — o resultado negativo | 12 |  |
| 9 | 52 | Os pares quase-gêmeos experimentais — mesma maquinaria, incerteza distinta, ambos no… | 7 |  |
| 9 | 16 | Os pisos como resultado — onde e por que o piso vence o assistido | 6 |  |
| 9 | 13 | O regime offline pela camada ⑦ — as quatro configurações mais o e103 | 4 |  |
| 9 | 57 | A completude do corpus — n efetivo por configuração × problema | 1 |  |
| 9 | 19 | As seis perguntas sobre a incerteza — uma por característica, casando resultado e… | 0 |  |
| 8 | 54 | As fronteiras da execução mediana contra a frente verdadeira | 54 |  |
| 8 | 47 | Tempo × qualidade — o custo se paga? (quadrantes) | 15 |  |
| 8 | 23 | Os três problemas reais como casos nomeados | 14 |  |
| 8 | 45 | O mecanismo em ação — contar o que o filme (⑥) registra | 14 |  |
| 8 | 46 | A parede do retreino — o tempo de ajuste por geração cresce com D (e com n) | 12 |  |
| 8 | 2 | Ranking agregado por rank médio | 9 |  |
| 8 | 32 | Sonda, dimensão 2 — a preservação da ordem (μ ordena como f? o classificador acerta a… | 7 |  |
| 8 | 18 | As escadas de dificuldade — em que degrau cada classe deixa de funcionar | 6 |  |
| 8 | 36 | A sonda por classe de medição — a qualidade do σ depende de onde o número vem? | 6 |  |
| 8 | 42 | A fantasia offline — |ND acreditado| vs |ND real| depois da reavaliação (⑦) | 5 |  |
| 8 | 27 | A comparação sob orçamento apertado — o placar recomputado no prefixo | 4 |  |
| 8 | 58 | A tabela de incapacidades — falha julgada pela referência; a incapacidade é resultado | 4 |  |
| 8 | 34 | Sonda, dimensão 4 — a discriminação do σ (a incerteza separa os candidatos de erro… | 3 |  |
| 8 | 61 | "O que a bateria não responde" — os limites declarados | 2 |  |
| 8 | 6 | Blocos de problemas — a taxa de comparações favoráveis ao surrogate por família de… | 1 |  |
| 8 | 10 | A banda dos pisos — os BO-especiais contra o melhor dos quatro pisos | 1 |  |
| 8 | 17 | Rank médio por característica estressada do problema (a versão-piloto) | 1 |  |
| 8 | 12 | A ablação do σ nos problemas reais — o primeiro resultado conclusivo, contra | 0 |  |
| 8 | 56 | Regra editorial das figuras — amostra no texto, o resto no repositório | 0 | regra/nota |
| 7 | 8 | Dispersão entre sementes — o surrogate adiciona variância? | 8 |  |
| 7 | 40 | O erro de fantasia por terço do orçamento — quem acredita demais no próprio modelo | 6 |  |
| 7 | 43 | A utilidade do infill — quanto do orçamento de busca vira fronteira | 4 |  |
| 7 | 14 | O ganho sobre o dataset — quanto cada offline melhora (ou piora) o que recebeu | 3 |  |
| 7 | 72 | Análise a alvo fixo: avaliações até atingir um nível de IGD+ (ERT / fixed-target), por… | 3 |  |
| 7 | 77 | O peso do sorteio inicial: qualidade do DoE (11D−1) × endpoint, por semente | 3 |  |
| 7 | 4 | Friedman + Nemenyi + diagrama de diferença crítica (Demšar) | 2 |  |
| 7 | 60 | A sensibilidade do veredito às políticas de cobertura — P1, P2, FE comum | 2 |  |
| 7 | 5 | Comparação pareada por semente vs. o melhor, com Holm e região de equivalência | 1 |  |
| 7 | 39 | A lei do teto relida — quando o modelo é bom o bastante, o teto vem do surrogate, não do… | 1 |  |
| 7 | 73 | A recomendação final: ND avaliado (in-sample, ①) × ND acreditado pelo modelo (③) — o… | 1 |  |
| 7 | 22 | O sintético prediz o real? — a transferência do ranking para RE21, ESTOQUE40 e DDMOP7 | 0 |  |
| 7 | 29 | A lente de prefixo para as células que bateram no teto de parede | 0 |  |
| 6 | 69 | Custo da otimização da aquisição (tempo de busca) e complexidade assintótica por fase | 13 |  |
| 6 | 71 | Ilustração didática: o mapa μ/σ do surrogate e a paisagem da aquisição sobre o espaço de… | 10 |  |
| 6 | 44 | Exploração × explotação — onde os infills caem | 8 |  |
| 6 | 41 | A fantasia geracional completa — a fronteira acreditada vs a real, geração a geração | 5 |  |
| 6 | 62 | Avisos de régua e clip — notas de normalização | 3 | regra/nota |
| 6 | 37 | A calibração por objetivo — a "agregação silenciosa de m sigmas" | 2 |  |
| 6 | 79 | O front por nível de confiança — filtrar o ND acreditado pelo σ e reavaliar (regime… | 2 |  |
| 6 | 81 | Sensibilidade do placar ao ponto de referência do HV e à normalização (régua) | 2 |  |
| 6 | 28 | Quem mais melhora na segunda metade — Δ meio → fim | 1 |  |
| 6 | 35 | A tipologia das curvas da sonda — aprende, plana, degenera | 1 |  |
| 6 | 20 | A taxonomia como variável — desempenho agregado por classe de cada eixo | 0 |  |
| 6 | 50 | FE redundante no DDMOP7 — nota de custo, não análise | 0 | regra/nota |
| 6 | 51 | Pares seminal → estado da arte sob o mesmo DoE — o que a evolução da classe comprou | 0 |  |
| 6 | 59 | O piso empírico de ruído — em dois níveis | 0 |  |
| 5 | 55 | Superfícies de attainment (worst-case) e coordenadas paralelas | 16 |  |
| 5 | 75 | Interpretação de engenharia/decisão das soluções não-dominadas nos problemas reais | 16 |  |
| 5 | 38 | Heterocedasticidade — o erro do modelo por região do espaço | 3 |  |
| 5 | 80 | Correlação entre objetivos nos problemas da bateria (característica do problema) | 1 |  |
| 5 | 21 | As famílias da §3.8 sob teste — o roster cobre 7/7 | 0 |  |
| 5 | 24 | DDMOP7 — "que aquisição acha as redes esparsas boas?" | 0 |  |
| 5 | 25 | Métricas no espaço de decisão nos MMF (IGDX / PSP) | 0 |  |
| 5 | 30 | Monotonicidade das curvas — o teste de sanidade do pipeline | 0 |  |
| 5 | 53 | O eco do quadro de equivalências na abertura da §5.1 — moldura, não análise | 0 | regra/nota |
| 4 | 66 | Sensibilidade ao parâmetro que governa o uso da incerteza (δ do gate, taxa de dropout, k… | 3 |  |
| 4 | 49 | O ganho descontado do custo — qualidade por hora, e a fronteira custo × qualidade | 1 |  |
| 4 | 78 | O decaimento do valor da aquisição ao longo do orçamento (o modelo acha que ainda há o… | 1 |  |
| 3 | 76 | Comparação com resultados publicados (fora do protocolo, orçamento não pareado) | 3 |  |
| 2 | 70 | Validação numérica do estimador da aquisição (MC × analítico; aproximações; corretude) | 12 |  |
| 2 | 68 | Tipo de surrogate sob a mesma maquinaria (GP × NN × RBF × ensemble; independente ×… | 11 |  |
| 1 | 65 | Sensibilidade a hiperparâmetros de projeto do algoritmo (fora do uso da incerteza) | 18 |  |
| 1 | 67 | Ablação de componentes do próprio algoritmo que não são a incerteza (otimizador, seleção… | 14 |  |
| 1 | 74 | Robustez a ruído injetado nas avaliações (fora do recorte epistêmico) | 5 |  |
| 0 | 64 | O sub-estudo de lote (q = 10) — sobol_batch e as células `batch` | 11 | DESCARTADA |
| 0 | 15 | O contrafactual σ = 0 online — cravado, nunca executado | 10 | DESCARTADA |
| 0 | 63 | O sweep offline de volume de dados — c311 e treed_media em small/medium/big × LHS/MVNS | 4 | DESCARTADA |

**Por faixa.** 9–10: 1, 26, 11, 9, 33, 3, 48, 31, 7, 52, 16, 13, 57, 19 · 7–8: 54, 47, 23, 45, 46, 2, 32, 18, 36, 42, 27, 58, 34, 61, 6, 10, 17, 12, 56, 8, 40, 43, 14, 72, 77, 4, 60, 5, 39, 73, 22, 29 · 5–6: 69, 71, 44, 41, 62, 37, 79, 81, 28, 35, 20, 50, 51, 59, 55, 75, 38, 80, 21, 24, 25, 30, 53 · 3–4: 66, 49, 78, 76 · 0–2: 70, 68, 65, 67, 74, 64, 15, 63

---

# Anexo 6 — Ranking por número de referências no corpus (de 72 artigos)

| Refs | Análises | Ficha | Nome | dos 38 | roster 7 | compl. 27 | roster 15 | Score |
|---|---|---|---|---|---|---|---|---|
| 54 | 82 | 54 | As fronteiras da execução mediana contra a frente verdadeira | 26 | 7 | 21 | 12 | 8 |
| 53 | 139 | 1 | Matrizes de mediana do IGD+ e do HV, algoritmo × problema | 28 | 5 | 20 | 11 | 10 |
| 44 | 90 | 26 | Trajetórias de convergência — mediana + IQR × fração do orçamento, com a banda… | 23 | 6 | 15 | 11 | 10 |
| 28 | 73 | 3 | "Quem empata com o melhor" — teste de postos vs. o melhor de cada problema… | 15 | 3 | 10 | 7 | 9 |
| 25 | 35 | 11 | Ablação exata do σ — Prob-MOEA/D × MOEA/D-média, em duas leituras | 15 | 4 | 6 | 9 | 10 |
| 20 | 23 | 48 | O custo com o tempo de ajuste do modelo — a decomposição fit / busca / sonda /… | 11 | 3 | 6 | 6 | 9 |
| 19 | 36 | 9 | Assistido × piso casado — Δ IGD+ pareado por semente e placar por algoritmo | 10 | 1 | 8 | 5 | 10 |
| 19 | 24 | 31 | Sonda, dimensão 1 — a acurácia da média ao longo do orçamento (o modelo… | 11 | 0 | 8 | 1 | 9 |
| 18 | 28 | 65 | Sensibilidade a hiperparâmetros de projeto do algoritmo (fora do uso da… | 12 | 2 | 4 | 6 | 1 |
| 16 | 29 | 75 | Interpretação de engenharia/decisão das soluções não-dominadas nos problemas… | 11 | 3 | 2 | 5 | 5 |
| 16 | 20 | 55 | Superfícies de attainment (worst-case) e coordenadas paralelas | 7 | 1 | 8 | 4 | 5 |
| 15 | 23 | 47 | Tempo × qualidade — o custo se paga? (quadrantes) | 10 | 1 | 4 | 2 | 8 |
| 14 | 24 | 23 | Os três problemas reais como casos nomeados | 6 | 4 | 4 | 4 | 8 |
| 14 | 21 | 67 | Ablação de componentes do próprio algoritmo que não são a incerteza… | 9 | 0 | 5 | 1 | 1 |
| 14 | 17 | 45 | O mecanismo em ação — contar o que o filme (⑥) registra | 6 | 1 | 7 | 4 | 8 |
| 13 | 18 | 33 | Sonda, dimensão 3 — a calibração do σ (a incerteza reportada é confiável?) | 8 | 0 | 5 | 1 | 10 |
| 13 | 15 | 69 | Custo da otimização da aquisição (tempo de busca) e complexidade assintótica… | 6 | 1 | 6 | 3 | 6 |
| 12 | 17 | 70 | Validação numérica do estimador da aquisição (MC × analítico; aproximações;… | 6 | 1 | 5 | 2 | 2 |
| 12 | 16 | 7 | Tendência com a dimensão D — o resultado negativo | 8 | 2 | 2 | 5 | 9 |
| 12 | 13 | 46 | A parede do retreino — o tempo de ajuste por geração cresce com D (e com n) | 8 | 2 | 2 | 5 | 8 |
| 11 | 21 | 64 | O sub-estudo de lote (q = 10) — sobol_batch e as células `batch` | 6 | 2 | 3 | 4 | 0 |
| 11 | 20 | 68 | Tipo de surrogate sob a mesma maquinaria (GP × NN × RBF × ensemble;… | 6 | 2 | 3 | 2 | 2 |
| 10 | 13 | 15 | O contrafactual σ = 0 online — cravado, nunca executado | 6 | 2 | 2 | 2 | 0 |
| 10 | 12 | 71 | Ilustração didática: o mapa μ/σ do surrogate e a paisagem da aquisição sobre o… | 6 | 1 | 3 | 2 | 6 |
| 9 | 13 | 2 | Ranking agregado por rank médio | 5 | 1 | 3 | 2 | 8 |
| 8 | 13 | 8 | Dispersão entre sementes — o surrogate adiciona variância? | 4 | 0 | 4 | 0 | 7 |
| 8 | 10 | 44 | Exploração × explotação — onde os infills caem | 4 | 0 | 4 | 1 | 6 |
| 7 | 10 | 32 | Sonda, dimensão 2 — a preservação da ordem (μ ordena como f? o classificador… | 3 | 2 | 2 | 4 | 8 |
| 7 | 10 | 52 | Os pares quase-gêmeos experimentais — mesma maquinaria, incerteza distinta,… | 5 | 0 | 2 | 0 | 9 |
| 6 | 10 | 18 | As escadas de dificuldade — em que degrau cada classe deixa de funcionar | 4 | 2 | 0 | 5 | 8 |
| 6 | 10 | 36 | A sonda por classe de medição — a qualidade do σ depende de onde o número vem? | 3 | 0 | 3 | 1 | 8 |
| 6 | 8 | 40 | O erro de fantasia por terço do orçamento — quem acredita demais no próprio… | 1 | 0 | 5 | 0 | 7 |
| 6 | 6 | 16 | Os pisos como resultado — onde e por que o piso vence o assistido | 1 | 1 | 4 | 1 | 9 |
| 5 | 7 | 42 | A fantasia offline — |ND acreditado| vs |ND real| depois da reavaliação (⑦) | 4 | 0 | 1 | 0 | 8 |
| 5 | 6 | 74 | Robustez a ruído injetado nas avaliações (fora do recorte epistêmico) | 3 | 2 | 0 | 4 | 1 |
| 5 | 5 | 41 | A fantasia geracional completa — a fronteira acreditada vs a real, geração a… | 3 | 0 | 2 | 2 | 6 |
| 4 | 6 | 13 | O regime offline pela camada ⑦ — as quatro configurações mais o e103 | 3 | 0 | 1 | 1 | 9 |
| 4 | 6 | 63 | O sweep offline de volume de dados — c311 e treed_media em small/medium/big ×… | 3 | 0 | 1 | 0 | 0 |
| 4 | 5 | 27 | A comparação sob orçamento apertado — o placar recomputado no prefixo | 2 | 0 | 2 | 1 | 8 |
| 4 | 5 | 43 | A utilidade do infill — quanto do orçamento de busca vira fronteira | 2 | 0 | 2 | 1 | 7 |
| 4 | 4 | 58 | A tabela de incapacidades — falha julgada pela referência; a incapacidade é… | 1 | 0 | 3 | 0 | 8 |
| 3 | 5 | 14 | O ganho sobre o dataset — quanto cada offline melhora (ou piora) o que recebeu | 2 | 0 | 1 | 1 | 7 |
| 3 | 5 | 38 | Heterocedasticidade — o erro do modelo por região do espaço | 3 | 0 | 0 | 0 | 5 |
| 3 | 4 | 34 | Sonda, dimensão 4 — a discriminação do σ (a incerteza separa os candidatos de… | 1 | 0 | 2 | 0 | 8 |
| 3 | 3 | 62 | Avisos de régua e clip — notas de normalização | 1 | 0 | 2 | 1 | 6 |
| 3 | 3 | 66 | Sensibilidade ao parâmetro que governa o uso da incerteza (δ do gate, taxa de… | 2 | 0 | 1 | 1 | 4 |
| 3 | 3 | 72 | Análise a alvo fixo: avaliações até atingir um nível de IGD+ (ERT /… | 2 | 0 | 1 | 1 | 7 |
| 3 | 3 | 76 | Comparação com resultados publicados (fora do protocolo, orçamento não pareado) | 2 | 0 | 1 | 1 | 3 |
| 3 | 3 | 77 | O peso do sorteio inicial: qualidade do DoE (11D−1) × endpoint, por semente | 1 | 0 | 2 | 1 | 7 |
| 2 | 4 | 79 | O front por nível de confiança — filtrar o ND acreditado pelo σ e reavaliar… | 2 | 0 | 0 | 0 | 6 |
| 2 | 3 | 4 | Friedman + Nemenyi + diagrama de diferença crítica (Demšar) | 2 | 0 | 0 | 2 | 7 |
| 2 | 2 | 37 | A calibração por objetivo — a "agregação silenciosa de m sigmas" | 2 | 0 | 0 | 0 | 6 |
| 2 | 2 | 60 | A sensibilidade do veredito às políticas de cobertura — P1, P2, FE comum | 2 | 0 | 0 | 1 | 7 |
| 2 | 2 | 61 | "O que a bateria não responde" — os limites declarados | 1 | 0 | 1 | 0 | 8 |
| 2 | 2 | 81 | Sensibilidade do placar ao ponto de referência do HV e à normalização (régua) | 1 | 0 | 1 | 0 | 6 |
| 1 | 4 | 5 | Comparação pareada por semente vs. o melhor, com Holm e região de equivalência | 0 | 1 | 0 | 1 | 7 |
| 1 | 2 | 49 | O ganho descontado do custo — qualidade por hora, e a fronteira custo ×… | 0 | 0 | 1 | 0 | 4 |
| 1 | 1 | 6 | Blocos de problemas — a taxa de comparações favoráveis ao surrogate por família… | 0 | 0 | 1 | 0 | 8 |
| 1 | 1 | 10 | A banda dos pisos — os BO-especiais contra o melhor dos quatro pisos | 1 | 0 | 0 | 1 | 8 |
| 1 | 1 | 17 | Rank médio por característica estressada do problema (a versão-piloto) | 1 | 0 | 0 | 0 | 8 |
| 1 | 1 | 28 | Quem mais melhora na segunda metade — Δ meio → fim | 1 | 0 | 0 | 0 | 6 |
| 1 | 1 | 35 | A tipologia das curvas da sonda — aprende, plana, degenera | 0 | 0 | 1 | 0 | 6 |
| 1 | 1 | 39 | A lei do teto relida — quando o modelo é bom o bastante, o teto vem do… | 1 | 0 | 0 | 0 | 7 |
| 1 | 1 | 57 | A completude do corpus — n efetivo por configuração × problema | 1 | 0 | 0 | 0 | 9 |
| 1 | 1 | 73 | A recomendação final: ND avaliado (in-sample, ①) × ND acreditado pelo modelo… | 1 | 0 | 0 | 1 | 7 |
| 1 | 1 | 78 | O decaimento do valor da aquisição ao longo do orçamento (o modelo acha que… | 0 | 0 | 1 | 0 | 4 |
| 1 | 1 | 80 | Correlação entre objetivos nos problemas da bateria (característica do problema) | 1 | 0 | 0 | 0 | 5 |
| 0 | 0 | 12 | A ablação do σ nos problemas reais — o primeiro resultado conclusivo, contra | 0 | 0 | 0 | 0 | 8 |
| 0 | 0 | 19 | As seis perguntas sobre a incerteza — uma por característica, casando resultado… | 0 | 0 | 0 | 0 | 9 |
| 0 | 0 | 20 | A taxonomia como variável — desempenho agregado por classe de cada eixo | 0 | 0 | 0 | 0 | 6 |
| 0 | 0 | 21 | As famílias da §3.8 sob teste — o roster cobre 7/7 | 0 | 0 | 0 | 0 | 5 |
| 0 | 0 | 22 | O sintético prediz o real? — a transferência do ranking para RE21, ESTOQUE40 e… | 0 | 0 | 0 | 0 | 7 |
| 0 | 0 | 24 | DDMOP7 — "que aquisição acha as redes esparsas boas?" | 0 | 0 | 0 | 0 | 5 |
| 0 | 0 | 25 | Métricas no espaço de decisão nos MMF (IGDX / PSP) | 0 | 0 | 0 | 0 | 5 |
| 0 | 0 | 29 | A lente de prefixo para as células que bateram no teto de parede | 0 | 0 | 0 | 0 | 7 |
| 0 | 0 | 30 | Monotonicidade das curvas — o teste de sanidade do pipeline | 0 | 0 | 0 | 0 | 5 |
| 0 | 0 | 50 | FE redundante no DDMOP7 — nota de custo, não análise | 0 | 0 | 0 | 0 | 6 |
| 0 | 0 | 51 | Pares seminal → estado da arte sob o mesmo DoE — o que a evolução da classe… | 0 | 0 | 0 | 0 | 6 |
| 0 | 0 | 53 | O eco do quadro de equivalências na abertura da §5.1 — moldura, não análise | 0 | 0 | 0 | 0 | 5 |
| 0 | 0 | 56 | Regra editorial das figuras — amostra no texto, o resto no repositório | 0 | 0 | 0 | 0 | 8 |
| 0 | 0 | 59 | O piso empírico de ruído — em dois níveis | 0 | 0 | 0 | 0 | 6 |

Fichas com 0 referências (leituras próprias da tese, regras ou notas): 12, 19, 20, 21, 22, 24, 25, 29, 30, 50, 51, 53, 56, 59.

---

# Anexo 7 — Os 72 artigos da mineração definitiva

### 7.1 Protocolo

Um agente de extração por artigo (modelo Sonnet), com o cartão `mineracao/CARTAO.md` (contexto mínimo da bateria; campos por análise: fichas, nova, descrição, literal ≤ 40 palavras, localizador, métricas, testes, convenções, achado, aplicabilidade com as 7 camadas; campos por artigo: setup, calibração do σ, custo, resultados negativos, equivalência de critérios, característica × desempenho, bloco-roster) e a tipologia das 64 fichas (`mineracao/tipologia_64.md`). Regras: literal + localizador em tudo (Lei 1), exaustividade, nada inventado (material suplementar ausente = 'só mencionada'), JSON validado. Execução em 9 lotes de 7–9 agentes em paralelo; 72/72 JSONs válidos; consolidação por script (`mineracao/build_v2.py`): mapeamento das 197 novas por leitura integral (Anexo 9), contagens por ficha, e escrita das fichas 65–81 e dos scores pelo agente de sessão. Limitações: (i) 60 análises são 'só mencionadas' (suplementos não convertidos — b3, b8, c261, e7, e74, e102, e103, e104, e86, c267, c82, e3, c100 apêndices); (ii) e8 tem só a Supporting Information no corpus; (iii) b15 sob N15 (nenhum número seu entra na prosa); (iv) c100 sem apêndices (14 páginas); (v) mapeamento ficha ↔ análise é do extrator + revisão do agente de sessão — auditável em `refs_full.json`.

### 7.2 Os 27 complementares e os critérios da escolha

Critérios usados na escolha dos 27 (sessão de 06/09, sobre a planilha `mapa_literatura_v7.xlsx`, aba corpus, 130 artigos): (a) cobrir classes da taxonomia sub-representadas entre os 38 — função O2 ganho de informação (e9 SUR, c222 MESMO, c214 PFES), O3 aprendizado ativo/reparo (c276 ε-PAL, b8 KTA2, c267), A1 penalização avessa a risco (e40, e21, f9), A2 dominância probabilística (e64), A3 gestão de confiança (jin3, c250, wang4), surrogates não-GP (e3 ensemble heterogêneo, e8 NN, e21 NN, c267 RG, wang4 resíduo); (b) os seminais e clássicos que as fichas citam como origem das convenções (mtm4 2006, c75 2006, mtm6 2011, c250 2008, jin3 2010, e1 2014, e9 2015, c276 2016); (c) vizinhos diretos dos 15 do roster — b8 e pp6 (K-RVEA/CSEA), e3 (e7), e4 TSEMO (e81, Thompson), c261/c123/e102 (b1/c238, decomposição), c131 MORBO e e16 EGBO (c262/c149, BoTorch), emo1 (critérios de infill baratos; b1/c238), e40 (RVEA); (d) o regime offline, raro entre os 38 (e21, f9, wang4); (e) recência 2024–2026 para as convenções atuais (c261, e16, e64, e21, c267). Restrição prática: só entraram artigos com texto convertido na pasta `_artigos_markdown` (c31 e e18, propostos em 06/09, não têm conversão; c118, DB-SAEA 2026, meta-black-box com classes 'resíduo' nos dois eixos, ficou fora por relevância marginal ao recorte).

### 7.3 Tabela dos 72

| id | Sigla | Ano | Grupo | Roster | Motor | Função | Surrogate | Medição | Regime | Análises | Novas | Execuções | Testes | Plataforma |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| c122 | θ-DEA-DP | 2022 | R7 | sim | EA-Decomposição | A2 · Dominância probabilística | CL -… | NAT-nonGP (distribuição… | online | 13 | 2 | 21 execuções independentes por algoritmo × problema (não 30 sementes,… | Wilcoxon rank-sum test (não pareado), α=5%, símbolos +/−/≈ contra θ-DEA-DP nas… | θ-DEA-DP e θ-DEA implementados em Python (surrogates em… |
| c141 | MMRAEA | 2025 | R7 | sim | EA-Dominância | O1 · Aquisição exploratória | RG — Regressor Clássico… | DISC-ENS (discordância… | online | 12 | 1 | 20 execuções independentes por instância na bateria sintética (não 30… | Wilcoxon rank-sum test, α=0.05, símbolos +/−/≈ (convenção DIRETA: '+' =… | PlatEMO (MATLAB) para toda a Sec. 'Experimental studies on… |
| c149 | LBN-MOBO | 2023 | R7 | sim | BO-Especiais | O1 · Aquisição exploratória | NN — Rede Neural | DISC-ENS (discordância… | online | 16 | 6 | Não relatado explicitamente. Todas as figuras mostram curvas de… | nenhum — não há teste estatístico de significância em nenhuma comparação do… | BoTorch para qEHVI/qNEHVI/qParEGO; pymoo (Blank e Deb,… |
| c217 | PC-SAEA | 2023 | R7 | sim | EA-Dominância | A3 · Gestão de confiança | CL -… | ERR-EMP (erro empírico vs.… | online | 13 | 3 | 30 execuções independentes por algoritmo × problema; MÉDIA (não… | Wilcoxon rank-sum test, α=0,05, símbolos +/−/≈ — IMPORTANTE: a comparação é… | Todos os experimentos conduzidos na plataforma PlatEMO… |
| c238 | EIM | 2017 | R7 | sim | BO-Melhoria-de-Pareto | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 9 | 2 | 10 execuções independentes por critério × problema nos 12 problemas… | paired t-test (p1); Wilcoxon signed-rank test (p2); α = 0.05 — comparação… | MATLAB. Kriging via DACE toolbox (regpoly0, corrgauss, θ… |
| e74 | CLMEA | 2023 | R7 | sim | EA-Dominância | O3 · Aprendizado ativo / reparo | RG — Regressor Clássico… | GEO-DIST… | online | 9 | 1 | 20 execuções independentes por algoritmo × problema nos benchmarks… | Wilcoxon signed-rank test (assim nomeado no texto — não 'rank-sum'), símbolos… | MATLAB R2021a, sobre a plataforma PlatEMO (Tian et al.,… |
| e81 | qPOTS | 2025 | R7 | sim | BO-Especiais | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 8 | 4 | Sintéticos: 10 repetições por problema/política de aquisição, com a… | nenhum teste de hipótese em nenhuma parte do artigo (sem Wilcoxon, sem… | GPyTorch e BoTorch (GPs e infraestrutura de BO),… |
| b1 | ParEGO | 2006 | 38 | sim | BO-Decomposição | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 10 | 2 | Estudo principal: 21 execuções independentes por algoritmo/função… | Mann–Whitney rank-sum test (todas as comparações; sem correção para múltiplas… | Implementação própria em C: EGO usa a biblioteca matpack… |
| b13 | AdaMoR-DDMOEA | 2025 | 38 |  | EA-Decomposição | A3 · Gestão de confiança | NN — Rede Neural | ERR-EMP (erro empírico vs.… | offline | 10 | 1 | 21 execuções independentes por algoritmo × problema ("Over the course… | Wilcoxon rank-sum test, α=0.05, símbolos +/≈/− relativos ao AdaMoR-DDMOEA,… | AdaMoR-DDMOEA e NSGA-II-DNN implementados em Python 3.9.14… |
| b14 | SA²-MOEA | 2024 | 38 |  | EA-Dominância | O3 · Aprendizado ativo / reparo | RG — Regressor Clássico… | DISC-ENS (discordância… | online | 9 | 4 | 30 execuções independentes por configuração problema x algoritmo em… | Wilcoxon rank-sum (WRS), α=0.05 - único teste estatístico usado em todo o… | PlatEMO (MATLAB) - 'All of them are implemented with the… |
| b15 | U-RankMOEA | 2026 | 38 |  | BO-Especiais | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 30 | 9 | 20 execucoes independentes nas Tabelas 1-3 (Wilcoxon rank-sum,… | Wilcoxon rank-sum (alfa=0,05) - declarado no protocolo geral (Sec. 4.1) para 20… | Nao nomeado - nenhuma mencao a PlatEMO, BoTorch, GPyTorch… |
| b2 | MOEA/D-EGO | 2010 | 38 |  | BO-Decomposição | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 7 | 0 | 10 execuções independentes por algoritmo por instância (não fica… | nenhum — apenas estatísticas descritivas (menor valor/lowest, média,… | Não explicitamente declarada para o MOEA/D-EGO;… |
| b3 | K-RVEA | 2018 | 38 | sim | EA-Decomposição | O3 · Aprendizado ativo / reparo | GP — Processo… | VAR-GP (posterior fechada… | online | 14 | 3 | CONTRADIÇÃO NO PRÓPRIO ARTIGO: a lista de parâmetros (Sec. IV-A, item… | Wilcoxon rank-sum test, nível de significância α = 0,05, aplicado par a par… | K-RVEA e SMS-EGO implementados em MATLAB; ParEGO em C;… |
| b4 | CSEA | 2019 | 38 | sim | EA-Dominância | A3 · Gestão de confiança | CL -… | ERR-EMP (erro empírico vs.… | online | 11 | 2 | CONTRADIÇÃO NO PRÓPRIO ARTIGO: a introdução da Seção IV diz Wilcoxon… | Wilcoxon rank-sum test, α=0,05, símbolos +/−/≈ contra CSEA (declarado como… | Todos os algoritmos comparados implementados em PlatEMO… |
| b5 | Prob-RVEA / Prob-MOEA/D (+ Hyb-RVEA /… | 2022 | 38 | sim | EA-Decomposição | A2 · Dominância probabilística | GP — Processo… | VAR-GP (posterior fechada… | offline | 8 | 0 | 31 execuções independentes por instância ('Number of Independent Runs… | Wilcoxon pareado (rank-sum) entre TODAS as abordagens (não só contra a melhor),… | Python, framework DESDEO (desdeo.it.jyu.fi), código… |
| b7 | DR (Dual-Ranking) | 2026 | 38 |  | EA-Dominância | A1 · Penalização avessa a risco | GP — Processo… | Resíduo | offline | 10 | 0 | 30 execuções independentes por configuração (algoritmo x problema x… | nenhum teste de hipótese formal (sem Wilcoxon/Friedman/Nemenyi em nenhuma parte… | pymoo (Blank & Deb, 2020) para NSGA-II, SBX (prob.=1.0,… |
| b9 | USeMO | 2020 | 38 |  | BO-Especiais | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 7 | 1 | 10 execuções independentes por configuração/benchmark ('the mean and… | nenhum teste estatístico de significância é mencionado em qualquer parte do… | Biblioteca Spearmint (fork 'PESM',… |
| c1 | BS-MOBO | 2018 | 38 |  | BO-Hipervolume | O1 · Aquisição exploratória | NN — Rede Neural | DISC-ENS (discordância… | online | 17 | 10 | 25 execuções independentes para os bancos de pequena e de grande… | Wilcoxon rank-sum test, α=0.05, símbolos +/=/- — mas comparando cada algoritmo… | K-RVEA: implementação oficial via PlatEMO (MATLAB) [46].… |
| c10 | SP-RV-MOEANet | 2021 | 38 |  | EA-Decomposição | O3 · Aprendizado ativo / reparo | RG — Regressor Clássico… | DISC-ENS (discordância… | online | 12 | 5 | 10 execuções independentes para as 3 redes sintéticas N=300 (Table I)… | Wilcoxon rank-sum test, α=0.05, comparando cada algoritmo contra SP-RV-MOEANet,… | Não informado no texto (nenhuma menção a PlatEMO, BoTorch,… |
| c100 | qEHVI | 2020 | 38 |  | BO-Hipervolume | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 10 | 6 | 20 execuções independentes ('trials') em todas as figuras e na Table… | nenhum teste de hipótese formal (sem Wilcoxon/Friedman/sinal); todas as… | BoTorch (biblioteca open-source dos próprios autores, sobre… |
| c105 | SMS-EGO | 2008 | 38 |  | BO-Hipervolume | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 6 | 0 | 5 execucoes independentes por algoritmo x funcao de teste (bem menor… | Kruskal-Wallis unilateral (one-sided), pareado entre os 3 algoritmos por… | MATLAB (todos os algoritmos); CMA-ES de Hansen (MLE dos… |
| c106 | EMMI (EMmI) | 2016 | 38 |  | BO-Melhoria-de-Pareto | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 8 | 3 | Cada uma das 6 configurações (3 critérios de melhoria — EMMI, CWPI,… | nenhum teste estatístico de hipótese em lugar nenhum do artigo (sem… | MATLAB: função bestlh (LHD maximin;… |
| c107 | MS-VHGP-EIHV | 2017 | 38 |  | BO-Hipervolume | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 13 | 3 | 60 execuções/trials independentes para cada configuração dos testes… | Nenhum teste de hipótese é usado para comparar desempenho de algoritmos em… | Não especificada explicitamente no artigo — nenhuma menção… |
| c154 | JES | 2022 | 38 | sim | BO-Especiais | O2 · Ganho de informação | GP — Processo… | VAR-GP (posterior fechada… | online | 11 | 7 | 100 sementes/execuções independentes por problema x algoritmo ('All… | nenhum — nenhum teste de significância estatística (Wilcoxon, Friedman, sinal,… | Python 3.8; BoTorch 0.5.1; GPyTorch 1.6.0; NumPy 1.21.2;… |
| c24 | DTK-MODE | 2015 | 38 |  | EA-Dominância | O3 · Aprendizado ativo / reparo | GP — Processo… | VAR-GP (posterior fechada… | offline | 6 | 1 | "For the comparison, both the algorithms have 30 independent runs" —… | nenhum (nenhum teste estatístico de hipótese é reportado em todo o artigo — nem… | Não informado no texto (nenhuma menção a PlatEMO, BoTorch,… |
| c241 | EMMOEA | 2023 | 38 |  | EA-Decomposição | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 14 | 4 | 20 execuções independentes por algoritmo × problema/configuração, em… | Wilcoxon rank-sum test com correção de Bonferroni, α=0.05 — compara cada… | PlatEMO (todos os 5 algoritmos-baseline implementados nessa… |
| c262 | qNEHVI (NEHVI sequencial; qNEHVI-1 =… | 2021 | 38 | sim | BO-Hipervolume | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 15 | 3 | 100 execucoes independentes por celula metodo x problema (declarado… | nenhum teste de hipotese formal em lugar nenhum do artigo (confirmado por busca… | BoTorch/PyTorch (implementacoes de qEHVI, qNParEGO, TS-TCH… |
| c29 | MO P-algorithm | 2014 | 38 |  | BO-Melhoria-de-Pareto | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 6 | 3 | 1000 execuções independentes por algoritmo, explicitamente reportado… | nenhum teste de hipótese formal — apenas média ± desvio-padrão sobre execuções… | MATLAB (implementação própria do multi-objective… |
| c45 | GP-DGS | 2024 | 38 |  | BO-Especiais | A2 · Dominância probabilística | GP — Processo… | VAR-GP (posterior fechada… | offline | 3 | 0 | Sem sementes/réplicas múltiplas no sentido da dissertação: cada… | nenhum teste de hipótese estatística (sem Wilcoxon, sem Friedman); comparação… | SEAWAT versão 4 (USGS) como simulador numérico de… |
| c48 | IBE-CSEA | 2021 | 38 |  | EA-Dominância | A3 · Gestão de confiança | CL -… | ERR-EMP (erro empírico vs.… | online | 7 | 2 | 20 execuções independentes nos problemas sintéticos (DTLZ, MaF), com… | Wilcoxon rank-sum (α=0,05), símbolos +/=/−, ancorado no IBE-CSEA (não no melhor… | NÃO LOCALIZADO |
| c49 | Interactive Offline DD-MOEA Framework… | 2020 | 38 |  | EA-Decomposição | Resíduo | GP — Processo… | VAR-GP (posterior fechada… | offline | 5 | 4 | Não relata número de execuções/sementes independentes — é um estudo… | nenhum | Não informado explicitamente para o framework/algoritmo… |
| c50 | PD-MOEA | 2018 | 38 |  | EA-Dominância | A2 · Dominância probabilística | GP — Processo… | VAR-GP (posterior fechada… | offline | 11 | 4 | 10 execuções independentes do otimizador são usadas apenas para as… | nenhum teste estatístico formal (sem Wilcoxon rank-sum, sem Friedman/Nemenyi)… | GPy (framework Python para Processos Gaussianos, referência… |
| c59 | UA-DBO | 2026 | 38 |  | EA-Dominância | A1 · Penalização avessa a risco | NN — Rede Neural | DISC-ENS (discordância… | offline | 12 | 4 | Divergência de arrasto: 5 execuções independentes (populações… | nenhum — todo o artigo reporta média ± erro-padrão (ou valores únicos) sem… | Otimização evolutiva: código próprio in-house 'AeroOPT' (Li… |
| c65 | SABBa | 2022 | 38 |  | Resíduo | A2 · Dominância probabilística | GP — Processo… | VAR-GP (posterior fechada… | online | 10 | 2 | 10 execuções independentes por configuração nos 2 casos-teste… | nenhum teste estatístico formal em todo o artigo (sem Wilcoxon, sem Friedman,… | NOMAD v3.6.2 (otimizador derivative-free MADS) como 'motor'… |
| c66 | PAL-SAPSO | 2019 | 38 |  | EA-Dominância | A2 · Dominância probabilística | GP — Processo… | VAR-GP (posterior fechada… | online | 6 | 2 | 20 execuções independentes nos 8 problemas de benchmark (Sec. IV-A);… | nenhum teste estatístico de significância em todo o artigo (sem Wilcoxon, sem… | MOPSO, dMOPSO e SMPSO: código-fonte do PlatEMO [31]… |
| c71 | SAEA/ME | 2020 | 38 |  | BO-Especiais | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 2 | 0 | 20 execuções independentes por célula (algoritmo × problema × D) —… | Wilcoxon rank-sum test, α = 5% — "the widely used Wilcoxon's rank sum test at… | Não especificado no texto — nenhuma plataforma (PlatEMO,… |
| c81 | UA-MORL-Diff | 2025 | 38 |  | Resíduo | A1 · Penalização avessa a risco | NN — Rede Neural | NAT-nonGP (distribuição… | offline | 16 | 8 | 3 execuções/trials independentes por configuração para toda avaliação… | nenhum teste estatístico formal em todo o artigo (sem Wilcoxon, sem Friedman,… | Framework próprio de RL-guided diffusion (PPO-style, código… |
| c82 | TC-SAEA | 2022 | 38 |  | EA-Decomposição | A3 · Gestão de confiança | GP — Processo… | VAR-GP (posterior fechada… | online | 12 | 3 | 20 execuções independentes por configuração para as Tabelas 1, 2, 3,… | Wilcoxon rank-sum test, α=0,05, símbolos (+)/(–)/(≈) indicando se o algoritmo… | MATLAB R2019a, Intel Core i7 @ 2.21 GHz; modelo GP… |
| c91 | EHVIMOPSO | 2019 | 38 |  | EA-Dominância | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 7 | 3 | 20 execuções independentes (Tabela 1) — "the statistical results with… | nenhum — apenas média e desvio-padrão (Ave/Std ou Mean/Std) são reportados; não… | "All codes mentioned above are programmed with MATLAB 16a"… |
| c97 | EnGP-MRO | 2011 | 38 |  | EA-Dominância | Resíduo | RG — Regressor Clássico… | DISC-ENS (discordância… | offline | 10 | 6 | Não relatado — o artigo não menciona número de execuções… | nenhum teste estatístico de hipótese é usado em todo o artigo (sem Wilcoxon,… | Discipulus (software comercial de programação genética,… |
| e103 | IBEA-MS | 2023 | 38 | sim | EA-Indicador | A3 · Gestão de confiança | GP — Processo… | VAR-GP (posterior fechada… | offline | 11 | 4 | 30 execuções independentes por configuração, em todas as comparações… | Wilcoxon rank-sum, α=0,05, símbolos +/−/= (quase sempre contra IBEA-MS como… | PlatEMO (MATLAB) [51]; Kriging via MATLAB Toolbox DACE… |
| e104 | RVMM | 2022 | 38 |  | BO-Especiais | A1 · Penalização avessa a risco | GP — Processo… | VAR-GP (posterior fechada… | online | 12 | 3 | 20 execuções independentes por célula (algoritmo × problema),… | Friedman (implementado no software KEEL [49]) — usado APENAS nas duas ablações… | PlatEMO [42] (MATLAB) para todos os experimentos; teste de… |
| e17 | MOBO | 2021 | 38 |  | BO-Hipervolume | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 10 | 4 | 10 execucoes independentes para as comparacoes agregadas no AWA (Fig.… | nenhum teste estatistico formal em nenhuma analise do artigo; apenas media +/-… | Python; GPflow [42] sobre TensorFlow [43] para os modelos… |
| e7 | EDN-ARMOEA | 2022 | 38 | sim | EA-Indicador | O3 · Aprendizado ativo / reparo | NN — Rede Neural | DISC-ENS (discordância… | online | 15 | 6 | 20 execuções independentes por algoritmo × problema (não 30 como na… | Wilcoxon rank-sum test, α=5% (0,05), símbolos +/−/≈ — em Table I a referência… | Matlab R2014a sobre o toolbox PlatEMO; GP implementado via… |
| e86 | NSGAIII-EHVI | 2023 | 38 |  | EA-Decomposição | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 7 | 3 | 30 execuções independentes por função de teste ("the experiments are… | Wilcoxon rank-sum, α=0,05, símbolos +/−/≈ (superior/inferior/sem diferença… | MATLAB, plataforma PlatEMO [44] (todos os algoritmos… |
| b8 | KTA2 | 2021 | 27 |  | EA-Indicador | O3 · Aprendizado ativo / reparo | GP — Processo… | VAR-GP (posterior fechada… | online | 9 | 2 | 30 execuções independentes por instância (algoritmo x problema x M). | Wilcoxon rank-sum (WRS) test, alfa=0.05, símbolos +/aprox/- relativos a KTA2 (o… | PlatEMO (MATLAB) para todos os algoritmos comparados,… |
| c123 | EPBII / EIPBII | 2017 | 27 |  | BO-Decomposição | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 8 | 1 | 10 execuções independentes por configuração (critério × problema),… | nenhum teste estatístico formal em lugar nenhum do artigo — só destaque em… | Framework EGO próprio dos autores (não nomeado como… |
| c131 | MORBO | 2022 | 27 |  | BO-Hipervolume | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 13 | 2 | 20 replicacoes independentes por metodo x problema. 'We run all… | Nenhum teste de hipotese formal (sem Wilcoxon/Friedman/Nemenyi); reporta media… | MORBO implementado em BoTorch [Balandat et al., 2020];… |
| c214 | PFES | 2020 | 27 |  | BO-Especiais | O2 · Ganho de informação | GP — Processo… | VAR-GP (posterior fechada… | online | 5 | 1 | 10 execuções independentes por configuração/algoritmo/problema, cada… | nenhum teste de hipótese formal em lugar nenhum do artigo; apenas média ± erro… | NÃO LOCALIZADO — o artigo não menciona explicitamente a… |
| c222 | MESMO | 2019 | 27 |  | BO-Especiais | O2 · Ganho de informação | GP — Processo… | VAR-GP (posterior fechada… | online | 6 | 1 | 10 execuções independentes por configuração ('We run all experiments… | nenhum teste estatístico formal em nenhuma parte do artigo (nem Wilcoxon, nem… | Biblioteca BO Spearmint (fork PESM:… |
| c250 | K-MOGA | 2008 | 27 |  | EA-Dominância | A3 · Gestão de confiança | GP — Processo… | VAR-GP (posterior fechada… | online | 6 | 1 | 30 execucoes independentes de cada algoritmo (MOGA e K-MOGA) em cada… | nenhum teste de significancia formal (sem Wilcoxon/Friedman/Holm) em nenhuma… | Implementacao propria dos autores (MOGA baseado em NSGA +… |
| c261 | DirHV-EGO | 2024 | 27 |  | BO-Decomposição | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 17 | 6 | 21 execuções independentes por configuração/problema (vs. 30 sementes… | Wilcoxon rank-sum, α=0.05, símbolos +/−/≈ (significativamente… | Todos os algoritmos implementados em MATLAB sobre a… |
| c267 | SAMOEA-TL2M | 2025 | 27 |  | EA-Dominância | O3 · Aprendizado ativo / reparo | RG — Regressor Clássico… | GEO-DIST… | online | 12 | 1 | 31 execuções independentes de cada método em cada problema (Seção… | Wilcoxon rank-sum test, nível de significância de 5% (α=0.05), símbolos +/=/−… | MATLAB R2021a; hardware Intel Core i9-12900H, 2.50 GHz. A… |
| c276 | ε-PAL | 2016 | 27 |  | BO-Especiais | O3 · Aprendizado ativo / reparo | GP — Processo… | VAR-GP (posterior fechada… | online | 4 | 2 | 200 repetições por configuração; mediana dos resultados é o que… | nenhum teste estatístico de hipótese (Wilcoxon, Friedman etc.) em lugar nenhum… | Gaussian Process Regression and Classification Toolbox for… |
| c75 | MO-EI/PI (Keane) | 2006 | 27 |  | BO-Melhoria-de-Pareto | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 5 | 1 | Heterogêneo entre as análises e muito abaixo do padrão de 30 sementes… | nenhum teste de hipótese formal em nenhuma das análises — apenas média ± 1… | Código próprio do autor, não PlatEMO/BoTorch/MATLAB Toolbox… |
| e1 | EMO | 2014 | 27 |  | BO-Hipervolume | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 6 | 2 | 10 execuções independentes por configuração (não 30 sementes como na… | nenhum teste de significância estatística (nem Wilcoxon, nem Friedman) — só… | MATLAB; hiperparâmetros do Kriging (correlação Matérn… |
| e102 | MOEA/D-ASS | 2021 | 27 |  | BO-Decomposição | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 7 | 4 | 21 execuções independentes (Sec. V-A1c), usadas tanto na comparação… | não especificado no corpo do artigo — o texto só afirma que as Tabelas I–X… | PlatEMO (MATLAB) para ParEGO, CPS-MOEA, K-RVEA e CSEA;… |
| e16 | EGBO | 2024 | 27 |  | BO-Hipervolume | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 10 | 1 | AgNP campanha real: 1 execução por otimizador (qNEHVI-BO, EGBO) —… | Nenhum teste de hipótese formal em nenhuma análise do artigo (sem Wilcoxon,… | BoTorch 0.8.5 + GPyTorch 1.10 (lista de SingleTaskGP via… |
| e21 | PIO | 2025 | 27 |  | EA-Dominância | A1 · Penalização avessa a risco | NN — Rede Neural | NAT-nonGP (distribuição… | offline | 9 | 2 | 15 corridas independentes do GA por combinação tarefa×função de… | nenhum teste estatístico em nenhuma parte do artigo (sem Wilcoxon, sem… | Chemprop (D-MPNN, com UQ por deep ensemble+MVE ou… |
| e3 | HeE-MOEA | 2019 | 27 |  | EA-Dominância | O1 · Aquisição exploratória | RG — Regressor Clássico… | DISC-ENS (discordância… | online | 13 | 3 | 20 execuções independentes por problema×algoritmo para N=10, 20, 40;… | Wilcoxon rank-sum, α=0,05 (5%), símbolos +/=/− (relativos ao HeE-MOEA);… | MATLAB R2014a, Intel Core i7 3,4GHz, Windows 7 Enterprise… |
| e4 | TSEMO | 2018 | 27 |  | BO-Hipervolume | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 6 | 0 | 20 execucoes independentes por combinacao algoritmo x problema de… | nenhum teste de hipotese em lugar nenhum do artigo (sem Wilcoxon, Friedman,… | MATLAB. GPs ajustados via toolbox GPML (Rasmussen &… |
| e40 | SBP-BO | 2023 | 27 |  | EA-Decomposição | A1 · Penalização avessa a risco | GP — Processo… | VAR-GP (posterior fechada… | online | 9 | 4 | 20 execuções independentes por algoritmo x problema (não 30 como no… | Wilcoxon rank-sum, alfa=0.05, com correção de Holm-Bonferroni; símbolos… | MATLAB R2019a, Intel Core i7-8750H @ 2.21GHz; RVEA como… |
| e64 | SA-MOPSO (PPD) | 2025 | 27 |  | EA-Dominância | A2 · Dominância probabilística | GP — Processo… | VAR-GP (posterior fechada… | online | 11 | 1 | NÃO HÁ sementes/réplicas independentes com estatística em lugar… | nenhum (nenhum teste estatístico formal em nenhum lugar do artigo; sem… | PESTPP-MOU (White et al., 2022), modificado pelos autores… |
| e8 | NN-EGO | 2020 | 27 |  | BO-Melhoria-de-Pareto | O1 · Aquisição exploratória | NN — Rede Neural | GEO-DIST… | online | 15 | 9 | Uma ÚNICA trajetória sequencial de active learning (5 gerações, sem… | Shapiro-Wilk (normalidade da distribuição aleatória; p=0.02 para ΔGox(sol),… | ANN customizado em TensorFlow 1.14 (arquiteturas… |
| e9 | SUR | 2015 | 27 |  | BO-Especiais | O2 · Ganho de informação | GP — Processo… | VAR-GP (posterior fechada… | online | 4 | 1 | Não relatado explicitamente. Não há menção a sementes múltiplas,… | nenhum teste estatístico em lugar nenhum do artigo (execução única por… | R: pacote pbivnorm (Kenkel, 2012) para a CDF normal… |
| emo1 | MPoI / HypI / DomRank / MSD (4… | 2017 | 27 |  | BO-Melhoria-de-Pareto | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 3 | 2 | 11 execuções (runs) independentes por método por problema. Runs… | Friedman (teste global por problema, entre os 6 métodos bayesianos, usando os… | GPy (framework de GP em Python) para os modelos de processo… |
| f9 | UA-IBEA (sigla não-oficial, proposta… | 2019 | 27 |  | EA-Indicador | A1 · Penalização avessa a risco | GP — Processo… | VAR-GP (posterior fechada… | offline | 6 | 0 | 31 execuções independentes por combinação problema x k x técnica de… | nenhum teste estatístico em lugar nenhum do artigo — apenas média +/-… | MATLAB para os modelos de Kriging (função de regressão… |
| jin3 | GS-MOMA / GSM (mono: GS-SOMA) | 2010 | 27 |  | EA-Dominância | A3 · Gestão de confiança | RG — Regressor Clássico… | ERR-EMP (erro empírico vs.… | online | 14 | 2 | 20 execuções independentes por configuração, tanto em SOO quanto em… | t-test, 95% confidence level — usado apenas na comparação SOO (Table XV),… | Não mencionada explicitamente no artigo (implementação… |
| mtm4 | MAES (variante MO: M-NSGA-II) | 2006 | 27 |  | EA-Dominância | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 10 | 1 | 20 execuções independentes (sementes distintas) para esfera,… | nenhum teste de significância formal (sem Wilcoxon/Friedman/Holm) — o artigo é… | Implementação própria dos autores (ES/MAES/NSGA-II com… |
| mtm6 | EHVI (EI_H) / "EHVI-EGO" | 2011 | 27 |  | BO-Hipervolume | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 3 | 1 | 1 execução única — não há replicação por sementes. O próprio artigo… |  | MATLAB — 'The MATLAB implementation of the expected… |
| pp6 | AB-MOEA | 2020 | 27 |  | EA-Decomposição | O1 · Aquisição exploratória | GP — Processo… | VAR-GP (posterior fechada… | online | 7 | 0 | 20 execuções independentes por algoritmo/problema nos 16 benchmarks… | Wilcoxon rank-sum test, α=0,05, símbolos '(+)' (algoritmo de referência supera… | AB-MOEA e suas duas variantes (SM-MOEA, AS-MOEA)… |
| wang4 | SA-NSGA-II | 2016 | 27 |  | EA-Dominância | A3 · Gestão de confiança | Resíduo | ERR-EMP (erro empírico vs.… | offline | 10 | 2 | Padrão geral: 20 execuções independentes por configuração com dados… | Wilcoxon signed-rank test [83] — usado APENAS em Table III (comparação sob… | Não mencionado no texto (nenhuma plataforma como PlatEMO,… |

Legenda: Grupo 38 = artigo das planilhas do processo seletivo; R7 = os 7 do roster minerados agora; 27 = complementares. O `setup` completo (benchmarks, orçamento, baselines, métricas, apresentação) de cada artigo está no arquivo-companheiro `mineracao_definitiva_transversais_06-09-2026.md`, §A.

### 7.4 Roster: quem mede o quê sobre o próprio mecanismo (resumo; detalhe no Anexo 8.6)

- **c122** (θ-DEA-DP): 3 análise(s) do mecanismo próprio; calibração medida: sim; custo reportado: sim; resultados negativos registrados: 5; equivalências: 0; característica × desempenho: 4.
- **c141** (MMRAEA): 2 análise(s) do mecanismo próprio; calibração medida: não; custo reportado: sim; resultados negativos registrados: 6; equivalências: 2; característica × desempenho: 7.
- **c149** (LBN-MOBO): 5 análise(s) do mecanismo próprio; calibração medida: não; custo reportado: sim; resultados negativos registrados: 4; equivalências: 0; característica × desempenho: 4.
- **c217** (PC-SAEA): 6 análise(s) do mecanismo próprio; calibração medida: sim; custo reportado: sim; resultados negativos registrados: 6; equivalências: 0; característica × desempenho: 6.
- **c238** (EIM): 3 análise(s) do mecanismo próprio; calibração medida: não; custo reportado: sim; resultados negativos registrados: 4; equivalências: 3; característica × desempenho: 4.
- **e74** (CLMEA): 1 análise(s) do mecanismo próprio; calibração medida: não; custo reportado: sim; resultados negativos registrados: 5; equivalências: 1; característica × desempenho: 6.
- **e81** (qPOTS): 2 análise(s) do mecanismo próprio; calibração medida: não; custo reportado: sim; resultados negativos registrados: 2; equivalências: 0; característica × desempenho: 2.
- **b1** (ParEGO): 0 análise(s) do mecanismo próprio; calibração medida: não; custo reportado: sim; resultados negativos registrados: 3; equivalências: 0; característica × desempenho: 4.
- **b3** (K-RVEA): 1 análise(s) do mecanismo próprio; calibração medida: não; custo reportado: sim; resultados negativos registrados: 2; equivalências: 0; característica × desempenho: 4.
- **b4** (CSEA): 2 análise(s) do mecanismo próprio; calibração medida: sim; custo reportado: sim; resultados negativos registrados: 5; equivalências: 1; característica × desempenho: 6.
- **b5** (Prob-RVEA / Prob-MOEA/D (+ Hyb-RVEA / Hyb-MOEA/D)): 3 análise(s) do mecanismo próprio; calibração medida: não; custo reportado: sim; resultados negativos registrados: 6; equivalências: 0; característica × desempenho: 2.
- **c154** (JES): 6 análise(s) do mecanismo próprio; calibração medida: não; custo reportado: sim; resultados negativos registrados: 5; equivalências: 3; característica × desempenho: 4.
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF)): 5 análise(s) do mecanismo próprio; calibração medida: não; custo reportado: sim; resultados negativos registrados: 7; equivalências: 3; característica × desempenho: 4.
- **e103** (IBEA-MS): 3 análise(s) do mecanismo próprio; calibração medida: não; custo reportado: sim; resultados negativos registrados: 5; equivalências: 1; característica × desempenho: 4.
- **e7** (EDN-ARMOEA): 4 análise(s) do mecanismo próprio; calibração medida: sim; custo reportado: sim; resultados negativos registrados: 5; equivalências: 1; característica × desempenho: 3.

---

# Anexo 8 — Achados transversais da mineração definitiva (com literais; versão completa no arquivo-companheiro)

### 8.1 Quem mede a qualidade da incerteza que usa (calibracao_do_sigma.mede = true): 19/72

- **b13** (AdaMoR-DDMOEA, 2025) — O artigo compara o MAE de treino vs. MAE de validação cruzada (10-fold) dos dois candidatos a surrogate (DNN e XGBoost) em cada problema (Tabelas 2 e 3), diagnosticando overfitting (MAE de treino baixo mas validação alta) e argumentando que o modelo com menor MAE de validação de fato generaliza melhor e produz melhor IGD final — validando indiretamente que o critério de seleção adotado (erro empírico de validação… «a higher MAE on the validation set and a lower MAE on the training set also indicate that the XGBoost model is overfitting the training data.» [Sec. 5.1, Tables 2–3]
- **b15** (U-RankMOEA, 2026) — O artigo mede calibracao em varias frentes, mas majoritariamente do CLASSIFICADOR bayesiano de rank (nao diretamente do sigma do Deep GP): (1) ECE/MCE/ACE do classificador apos escalonamento de temperatura + MC-Dropout adaptativo, com comparacao contra metodos isolados (Apendice I.4); (2) reliability diagram comparando temperatura vs MC-Dropout isolados (Fig. 18) - cujos numeros contradizem os de I.4 (ver… «ECE = 0.032 ± 0.004, (40) MCE = 0.056 ± 0.006, (41) ACE = 0.028 ± 0.003, (42)» [Apendice I.4 (Eq. 40-42); Fig. 18; Apendice F; Apendice E (Fig. 4); Apendice H (Fig. 8)]
- **b4** (CSEA, 2019; roster) — A cada retreino do FNN, o artigo calcula por validação cruzada (split 75/25 estratificado por categoria, Algoritmo 5) o erro empírico (MAE, Eq. 4) das predições separadamente para categoria I (p1) e categoria II (p2) — usados como medida de confiabilidade/incerteza do classificador (não é σ contínuo tipo GP, é taxa de erro de classificação). Complementarmente, a Seção III-D compara a taxa PREVISTA de soluções de… «Cross validation is performed for calculating the error on the test data as a measure for estimating the prediction uncertainty of the FNN.» [Sec. III-C.3; Sec. III-D, Fig. 7]
- **b7** (DR (Dual-Ranking), 2026) — O artigo mede calibração via CICP (Confidence Interval Coverage Probability, Sluijterman et al. 2024) - a fração dos valores reais que caem dentro do intervalo de confiança predito - reportada por surrogate x problema, para os dois tamanhos de dataset (Tables 2-3 do Suplemento). Complementarmente, o método propõe e usa um algoritmo de calibração (Algorithm 1, 'Auto-alfa Selection') que ajusta o hiperparâmetro alfa… «CICP evaluates uncertainty estimates by computing the fraction of function values that fall inside the corresponding confidence intervals.» [Sec. 4.1 (Performance Indicators); Sec. 3.2 (Auto-alfa Selection Algorithm, Algorithm 1,…]
- **c122** (θ-DEA-DP, 2022; roster) — Mede a ACURÁCIA (%) de classificação de dominância (Pareto e θ) dos classificadores Pareto-Net/θ-Net (Table VIII) num conjunto de teste sintético (1000 exemplos/classe, 3000 total) gerado uma vez após o LHS inicial de cada execução — mediana±DP sobre 21 execuções, comparado contra SVM/RF/CNB e contra variantes sem ponderação de classe (Pareto-Net*/θ-Net*), com Wilcoxon rank-sum a 5%. Isso é o análogo operacional de… «Table VIII shows the median prediction accuracy (over 21 runs) and the standard deviation of different algorithms.» [Sec. IV-D, Table VIII]
- **c217** (PC-SAEA, 2023; roster) — PC-SAEA não tem um σ contínuo (não é um GP); sua 'incerteza' é operacionalizada como acurácia de classificação empírica em um conjunto de VALIDAÇÃO com rótulo verdadeiro conhecido (p+ = fração corretamente classificada, p− = fração classificada de forma invertida, Algoritmo 4), recalculada A CADA GERAÇÃO e usada diretamente como o sinal de confiança que decide o estado (usar/inverter/ignorar) — ou seja, a própria… «For this aim, the classification accuracy on validation set is calculated as the degree of reliability.» [Sec. 3.3; Sec. 4.4, Table 5; Sec. 4.5, Fig. 9]
- **c24** (DTK-MODE, 2015) — O artigo compara o erro de ajuste do modelo (RMSE, Table II) com o comportamento de d(x) — a largura da banda do intervalo de predição (1-alpha) do Kriging, derivada em forma fechada da variância posterior (VAR-GP) — mostrando que a diminuição do erro de ajuste acompanha a diminuição de d(x) à medida que mais pontos de amostragem são inseridos via amostragem adaptativa, e usando esse d(x) como critério de… «It is also found, from the Table II, that the fitting error decreases as the number of sampling points increases, and furthermore it can be predicted through the behavior of d(x), i.e., the bandwidth…» [Sec. IV-A, Table II]
- **c250** (K-MOGA, 2008) — Duas verificacoes pontuais, ambas restritas ao exemplo ZDT2 e nao generalizadas com numeros para os demais 6 problemas: (1) Fig. 6, geracao a geracao, compara MMD_fm calculada so com valores de simulacao (verdade) contra a MMD_fm calculada com a mistura de valores reais e preditos pelo Kriging que o proprio K-MOGA usa internamente para decidir o gate; (2) Fig. 7, na 10a geracao de uma execucao, compara o erro real… «As shown in Fig. 7, for most design points (i.e., 25 out of 30 designs) in the tenth generation, the real error is less than the predicted error, which means that sm(x) is a valid estimation of the…» [Sec. 4.1.2-4.1.3, Figs. 6-7 (p. 031401-6 a 031401-7)]
- **c48** (IBE-CSEA, 2021) — Mede a taxa de erro de classificação (error rate) do ensemble podado final variando o hiperparâmetro Q (número de modelos selecionados, de 10% a 70% de T=200) sobre 'vários DTLZ diferentes', 20 execuções por valor de Q, para escolher o Q que minimiza o erro — não usa uma sonda comum a todos os algoritmos, nem mede calibração de intervalo/cobertura de um σ contínuo (o surrogate aqui é um classificador, não produz… «The influence of different values of Q on the error rate of the final model was verified on several different DTLZ respectively, and 20 independent experiments were carried out for each Q and the…» [Sec. 4.4.2, Fig. 4]
- **c50** (PD-MOEA, 2018) — Validação cruzada 10-fold sobre os 654 pontos coletados: para cada GP (UBC, NOx), o RMSE entre predição média e medição é calculado e comparado ao desvio-padrão do ruído de medição assumido no treino (0,2% para UBC; 17ppm para NOx, incorporados à matriz de covariância via K:=K+diag(σ²)); checagem visual complementar de que a maioria das medições cai dentro de 2 desvios-padrão da predição média (Figura 2). Não há… «The average root mean squared errors (RMSE) between the mean predictions and the measurements are 0.07% for GUBC and 6.67ppm for GNOx, which is well within the estimated measurement noise variance of…» [Sec. 3.1, Fig. 2]
- **c59** (UA-DBO, 2026) — Duas frentes complementares, ambas no conjunto de teste (não visto) após calibração linear feita no treino (fatores κ_L, κ_U, Eq. 10): (1) cobertura empírica do IC de 90% — fração de amostras com erro real abaixo do limite inferior, dentro do intervalo, e acima do limite superior, comparada aos alvos teóricos 5%/90%/5%; (2) ECE (expected calibration error) — calculado sobre 9 níveis de confiança α=0,1,...,0,9: para… «The ECE is then defined by averaging the distance between ĉα and target α: ECE = Σ α=0.1,···0.9 wα |ĉα −α| where wα = 1/9.» [Sec. 2.3.3 (Eq. 10, calibração linear); Sec. 4.1.2, Table 2, p. 13–15; Appendix B, p.…]
- **c81** (UA-MORL-Diff, 2025) — Sim — avaliação explícita e central no artigo. Usa duas métricas sobre os 9 surrogates (3 propriedades × 3 datasets), calculadas uma única vez sobre o split de teste held-out (scaffold-based), sem qualquer retreino durante a busca (regime offline): (1) R² — acurácia da média predita μ(m) contra o valor real; (2) AUCE (Area Under the Calibration Error curve) — calculada a partir de diagramas de confiabilidade/curvas… «The AUCE remains low across datasets and properties (0.02–0.10), indicating well-calibrated uncertainty estimates.» [Sec. 4.2.1 (resultado agregado); Appendix B.8.1 (definição formal de R² e AUCE); Appendix…]
- **c97** (EnGP-MRO, 2011) — O artigo mede a qualidade da incerteza de duas formas complementares: (1) constrói a CDF empírica dos resíduos de predição do ensemble para C1/C2/C3 (Figs. 15-17), usada para converter um nível de confiabilidade α na margem de erro correspondente, e observa que os erros são aproximadamente simétricos em torno de zero (p≈0,5 de resíduo nulo); (2) reavalia com o modelo numérico verdadeiro (FEMWATER) 5 soluções ótimas… «it is evident that the errors are less when the reliability level is high.» [Sec. 4.2 (eqs. 13-15); Sec. 6.1 Figs. 8-10; Sec. 6.3 Figs. 15-17 e Tables 3-4]
- **e21** (PIO, 2025) — O artigo compara DOIS métodos de UQ do D-MPNN/Chemprop — deep ensemble+MVE (incerteza aleatória via neurônio de variância com softplus; epistêmica via variância entre 10 modelos) e aprendizado evidencial (via distribuição Normal-Inversa-Gama, 4 saídas por neurônio) — quanto à qualidade da incerteza TOTAL (σ²_aleatória+σ²_epistêmica) que produzem, em conjunto de teste held-out, usando duas leituras complementares:… «the calibration curves closely follow the diagonal line across all test sets, with AUCE values remaining below 0.1, suggesting that the residual distribution for the test data does not significantly…» [Fig. 2 e Fig. 3; Results, 'Surrogate model and UQ performance'; elo qualitativo com…]
- **e3** (HeE-MOEA, 2019) — Comparação pontual da qualidade da estimativa de incerteza entre HeE e GP: ambos treinados nos mesmos 11N−1 dados (4 problemas DTLZ), usados para prever f̂ e ŝ² em 500 pontos aleatórios; reporta-se o MSE de f̂ (acurácia da média) e o desvio-padrão de ŝ (variabilidade da incerteza estimada) — NÃO há cálculo de cobertura (%) nem correlação σ×erro explícitos; é uma medida única, pós-treino final, não uma curva ao longo… «the estimated function values fˆ and variances sˆ2 of 500 randomly generated points are used to compute the mean square error (MSE) and the standard deviation of ˆs, respectively» [Sec. V-E.3 (Discussions); Fig. 1 do material suplementar (mencionada, não incluída)]
- **e7** (EDN-ARMOEA, 2022; roster) — Não é calibração por cobertura (fração de pontos dentro de μ±2σ) nem correlação σ×erro — é uma medida mais crua de MAGNITUDE/informatividade: o desvio-padrão médio (STD) da variância estimada σ̂² sobre 50 amostras de teste aleatórias, comparando EDN/HeE/GP treinados nos mesmos dados, ao longo de 20 execuções independentes, com a hipótese declarada a priori de que 'maior STD = melhor capacidade de expressar… «we calculate the mean standard deviation (STD) of the estimated variance (ŝ2) to assess the ability of the compared models to provide uncertainty information... the larger the mean STD, the better…» [Sec. IV-D; Tables SV-SVII (Supplementary material, ausentes deste corpus)]
- **e8** (NN-EGO, 2020) — A cada geração, um modelo paramétrico de erro heterocedástico ε(d) ~ N(0, σ1² + d·σ2²) é ajustado por máxima verossimilhança (MLE) sobre 10% dos dados de teste retidos do ANN multitarefa, onde d(x) é a distância latente média aos 10 vizinhos de treino mais próximos na representação final da rede (a mesma distância que serve de proxy de incerteza — daí a classe de medição GEO-DIST). O procedimento roda no laço… «The parameters are fit to dimensionless errors with the model ε(d) ∼ N(0, σ1² + dσ2²).» [Figure S4 (S10); Algorithm S1 (S9), passo 13]
- **mtm4** (MAES (variante MO: M-NSGA-II), 2006) — Verificação pontual (não sistemática/agregada) da validade do limite inferior de confiança (LB, ω=2, ~97% de confiança nominal, Eq. 36 com ny=1): para todas as 1000 avaliações reais de UMA execução do PoI-MAES na função de Ackley, plota-se y (valor real) contra y_lb = ŷ − 2ŝ (o limite inferior predito no momento da escolha) para checar se y_lb é de fato um limite inferior 'afiado' e válido para os valores reais… «It turns out that ylb is a good approximation to the sharp lower bound for the true function values.» [Sec. V (fim da subseção de resultados D/E, antes da Sec. VI), Figs. 25-26, p.14]
- **wang4** (SA-NSGA-II, 2016) — O artigo mede diretamente a qualidade/erro do 'surrogate' (aqui um estimador por redução de dados via clustering hierárquico, não um modelo probabilístico com σ): (i) MAPE dos dois objetivos e das duas restrições data-driven, e acurácia de seleção de pais, em função do nº de clusters K (Fig. 9); (ii) ER (erro real medido comparando a avaliação aproximada com a exata nos não-dominados correntes) versus ER* (erro… «we calculate the mean absolute percentage error (MAPE) averaged over 200 individuals (the combined population before selection) at each generation for the two objectives and two constraints,…» [Sec. IV-B, Fig. 9; Sec. IV-C (Eqs. 10-11); Sec. V-C2, Figs. 14-15]

Os 53 que NÃO medem incluem 11 do roster (b1, b3, b5, c141, c149, c154, c238, c262, e103, e74, e81) — o σ é insumo operacional, nunca objeto de medição; a única exceção do roster é a acurácia de classificação (b4, c122, c217; e7 mede 'magnitude').

### 8.2 Como o corpus reporta custo (custo.reporta = true): 60/72

- **b1** (ParEGO): Descrição qualitativa/narrativa, sem tabela nem gráfico de tempo medido: o custo de reajustar o modelo DACE cresce com o número de pontos acumulados ("several hundred or thousand matrix inversions" por reinício de Nelder-Mead),… [Sec. III-A]
- **b14** (SA²-MOEA): Complexidade assintótica de tempo e espaço (notação Big-O), decomposta em 3 fases (construção do modelo / busca assistida por surrogate / amostragem de preenchimento), para KTA2, ADSAPSO e SA²-MOEA (Tabela 7, Sec. 4.7). NÃO há… [Sec. 4.7, Table 7]
- **b15** (U-RankMOEA): Tempo de parede total e por iteracao por algoritmo em 3 cenarios, com speedup vs o baseline mais rapido (Table 14); decomposicao percentual do tempo de U-RankMOEA em 5 componentes - classificador, Deep GP, rede de aquisicao,… [Sec. 4.4 (Fig. 14); Apendice N (Table 14, Table 15); Apendice L.3;…]
- **b2** (MOEA/D-EGO): Tempo médio de CPU (10 execuções) comparando duas arquiteturas de modelagem GP (FuzzyCM local vs. modelo único global) em ZDT1/ZDT2 — 936 s e 1260 s (FuzzyCM) contra 4248 s e 4428 s (modelo único) — citado como evidência do… [Sec. VII-E-2 (FuzzyCM Versus One Single Model), Table III; Sec. VII-D…]
- **b3** (K-RVEA): (a) Complexidade teórica O(n³) do treino do Kriging, n=nº de amostras de treino (Sec. II-B), motivando a estratégia de arquivo de tamanho fixo NI — uma das duas contribuições centrais do artigo. (b) Tempo de treino medido… [Sec. II-B; Sec. IV-B; Fig. 9]
- **b4** (CSEA): Tempo de execução total (wall-clock, segundos) acumulado versus número de avaliações reais, comparando CSEA, CPS-MOEA, ParEGO, MOEA/D-EGO e K-RVEA em DTLZ2 3-objetivos (Fig. 11) — sem decompor em ajuste do modelo / busca no… [Sec. IV-F, Fig. 11]
- **b5** (Prob-RVEA / Prob-MOEA/D (+ Hyb-RVEA / Hyb-MOEA/D)): Apenas complexidade computacional teórica (Big-O), SEM tempo de parede medido: custo da atribuição probabilística de indivíduos a subpopulações/vetores de referência O(N·|P|) — reduzido por um mecanismo de votação (contar quantas… [Sec. III-A2]
- **b7** (DR (Dual-Ranking)): Apenas complexidade de tempo assintótica (Big-O) teórica: O(MN^2) para a não-dominância padrão do NSGA-II, O(MN) para a concatenação de f_sur e f_UA-sor, e O(2MN^2) para a não-dominância no espaço 2M-dimensional do dual-ranking -… [Sec. 3.3, subseção 'Time Complexity']
- **b8** (KTA2): Apenas complexidade computacional teórica (assintótica), sem nenhuma medição empírica de tempo de parede e sem decomposição fit/busca/avaliação/instrumentação. O artigo deriva que construir um modelo Kriging tem complexidade… [Sec. III-A (último parágrafo)]
- **b9** (USeMO): Tempo médio (segundos, média±desvio-padrão) de otimização da função de aquisição por iteração, comparando USeMO, PESMO, ParEGO e SMSego nos 6 benchmarks sintéticos (Tabela 2); tempo de ajuste do GP explicitamente excluído da… [Sec. 5.2 ("Comparison of acquisition function optimization time");…]
- **c1** (BS-MOBO): (1) Tempo de treinamento (fit) do surrogate — GP vs. BNN MC-dropout, com/sem gradiente — em função do número de amostras de treinamento, para uma função de 30 variáveis (Fig. 3, Sec. III-A-1): mostra que o custo do GP cresce… [Sec. III-A-1 (Fig. 3); Sec. IV-B (texto antes da Table II)]
- **c10** (SP-RV-MOEANet): Tempo de execução total (wall-clock) por execução, em HORAS, reportado ao lado do HV nas Tabelas I (N=300), II (escalabilidade N=500/1000) e III (redes reais), para cada algoritmo × rede. Não há decomposição explícita em tempo de… [Introduction (parágrafo final); Table I; Table II; Table III]
- **c100** (qEHVI): Tempo de parede da ETAPA DE OTIMIZAÇÃO DA AQUISIÇÃO especificamente (não do ajuste do GP nem da avaliação real) — Table 1, em CPU e GPU, por algoritmo e por tamanho de lote q (1,2,4,8 para métodos paralelos); comparação do tempo… [Table 1 e Sec. 5.1; Fig. 2a (Sec. 4.2); complexidade teórica na Sec.…]
- **c106** (EMMI (EMmI)): Nao e reportado tempo de execucao (wall-clock) em nenhum lugar do artigo; o que e reportado e a complexidade de estimacao via REML pelo NUMERO de parametros de covariancia a maximizar conjuntamente no modelo de dependencia… [Sec. 6.1, p. 17; ver tambem Sec. 6.2, p. 18-19 ('this model depends…]
- **c107** (MS-VHGP-EIHV): Tempo de parede (wall-clock) total por execução/trial, comparando duas formas de calcular o EIHV (quadratura exata ~6h vs. aproximação Gaussiana ~44min, Fig. 13a) e dois critérios de seleção de modelo (LOO vs. Monte Carlo, tempo… [Sec. III-E2/III-E3, Fig. 13]
- **c122** (θ-DEA-DP): Tempo médio de CPU (minutos), agregado 'over all runs', gasto em gerenciar os surrogates (ajuste + predição, não decomposto em fit/busca/avaliação, sem quebra por problema ou por fração do orçamento), comparável apenas entre os 3… [Sec. IV-C, Table VII]
- **c131** (MORBO): Decompoe explicitamente o tempo de ajuste do modelo (model fitting) e o tempo de geracao de candidatos/selecao do lote (batch selection, 'excluding model fitting') separadamente, por problema e por metodo (Tables 2-5); apresenta… [Sec. 5.2; Apendice E, E.1, F.2; Tables 2-5; Fig. 7-8]
- **c141** (MMRAEA): Tempo médio de execução (runtime total, não decomposto em fit/busca/avaliação) por algoritmo, em função da dimensão d (20,40,60,100), para um único problema (DTLZ2, 3 objetivos) — ver Fig. 9. Discussão textual qualitativa do… [Sec. Runtime comparison, Fig. 9]
- **c149** (LBN-MOBO): Tempo decorrido (wall-clock) por iteração e por tamanho de lote, para todos os métodos comparados (Figs. 1, 3, 10, 13, 15a, 16a, 18a); uma decomposição pontual entre tempo de treino do ensemble (fit) e tempo de busca da aquisição… [Sec. 3]
- **c154** (JES): Complexidade computacional teórica completa (Tabelas 1 e 2, Apêndice H) por operação (amostragem do GP, otimização multiobjetivo da amostra, decomposição em caixas O(p^(⌊M/2⌋+1)), condicionamento, avaliação da entropia… [Sec. 5.2 e Apêndice H, L.9]
- **c214** (PFES): Tempo de parede (segundos) para avaliar a função de aquisição em 100 pontos candidatos no problema DTLZ4 (L=4), comparando 5 métodos (Tabela 1a); decomposição do tempo do PFES em 4 sub-etapas — RFM, NSGA-II, QHV, cálculo de… [Sec. 6.1, Table 1, p. 8]
- **c217** (PC-SAEA): Tempo de execução TOTAL médio (wall-clock, segundos, sobre todos os problemas de WFG1-9) de 3 variantes de PC-SAEA (regressão, classificação, par-a-par) — não decomposto em ajuste do modelo / busca no modelo / avaliação real /… [Sec. 4.4, Table 6 (última linha) e parágrafo seguinte]
- **c222** (MESMO): Tempo médio (segundos, média±desvio-padrão) de OTIMIZAÇÃO DA FUNÇÃO DE AQUISIÇÃO — explicitamente excluindo o tempo de ajuste do GP, dito igual entre todos os algoritmos — para MESMO-{1,10,100}, PESMO-{1,10,100}, ParEGO e SMSego,… [Sec. 3 (afirmação teórica); Sec. 5.2, Table 1 (medição empírica)]
- **c238** (EIM): (1) Motivação na Introdução: cálculo hipotético de que 2.000.000 avaliações do critério EI de 6 objetivos (100×100×200, população×gerações×iterações do GA usado para maximizar a aquisição), a 1s cada, levariam ≈23 dias — não é… [Sec. I (motivação, Eq. 19); Sec. VII, Figs. 15-17]
- **c24** (DTK-MODE): Número de chamadas de FEA (avaliações reais) requeridas pelo MODE assistido por DTK comparado ao número usado pelo MODE que adota FEA diretamente (referência de ~20.000 avaliações, TEAM22): o assistido usa apenas 1-2% desse… [Sec. IV-B]
- **c241** (EMMOEA): (1) Argumento QUALITATIVO de complexidade no corpo principal (Conclusão): EMMOEA precisa treinar m+1 GPs por iteração (um por objetivo + um para o indicador de desempenho), herdando a complexidade cúbica O(n³) do GP, apontada… [Sec. IV (Conclusion)]
- **c250** (K-MOGA): Custo medido exclusivamente como numero de chamadas de simulacao (avaliacoes reais de objetivo/restricao) ate a convergencia, nao como tempo de CPU/parede; sem decomposicao de tempo de ajuste do Kriging separado da busca; sem… [Sec. 2.2 (p. 031401-2, caveat geral) e Table 3 / Sec. 4.3 (p.…]
- **c261** (DirHV-EGO): Duas frentes: (1) derivação ANALÍTICA de complexidade Big-O por iteração, decomposta em ajuste do GP O(mn³), maximização da EI via MOEA/D O((mn²+mN)Ntmax) e seleção de lote O(mN²+qN), com extensão ao caso many-objective no… [Sec. V-D, p.10-11 (texto principal); Supplementary Sec. III-D.2]
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF)): Tempo de parede da otimizacao da aquisicao (incluindo decomposicoes de caixa), em CPU e GPU, por metodo x problema x tamanho de lote q (Tabelas 3-4, Apendice H.1); NAO decompoe separadamente tempo de ajuste do GP nem de avaliacao… [Legenda da Table 3 / Table 4; Apendice D; Apendice H.1]
- **c267** (SAMOEA-TL2M): Não há tempos de execução medidos, nem decomposição de tempo (ajuste do modelo vs. busca vs. avaliação) no corpo principal — só o hardware (Intel Core i9-12900H, 2.50 GHz) e a plataforma (MATLAB R2021a) usados para rodar os… [Sec. IV (parágrafo final antes de IV-A, hardware/plataforma);…]
- **c276** (ε-PAL): Complexidade assintótica TEÓRICA por estágio de cada iteração (Sec. 3.7): modelagem GP O(s³+ns²) (s = nº de pontos amostrados, n=|E|); descarte via Pareto pessimista O(n log n) para m=2,3 e O(n(log n)^{m−2}) para m>3 (adaptação… [Sec. 3.7 (Analysis of Execution Time); Sec. 6.5; Sec. 7.5, Fig. 7]
- **c29** (MO P-algorithm): Apenas complexidade computacional teórica — não há tempos de parede/wall-clock empíricos reportados. A cada passo, o cálculo da probabilidade de melhoria (Eq. 9, produto de m CDFs gaussianas usando médias/variâncias condicionais)… [Sec. 4, ¶ final (equivalente à p. 84-85 do artigo; ANEXO camada de…]
- **c45** (GP-DGS): Apenas afirmação qualitativa (sem números de tempo de parede, sem complexidade, sem decomposição fit/busca/avaliação) de que a estratégia de amostragem proposta é computacionalmente menos intensiva que os métodos tradicionais de… [Sec. 3 Results and Discussion; reafirmado na Sec. 4 Conclusions ('the…]
- **c49** (Interactive Offline DD-MOEA Framework (sigla não-oficial, proposta por mim)): Apenas afirmações qualitativas, não quantificadas: a filtragem por incerteza (Etapa 4) e a re-visualização com diferentes tolerâncias têm 'baixo custo computacional' porque reaproveitam o arquivo já construído, sem novas… [Sec. 3.3, Step 4]
- **c50** (PD-MOEA): Tempo de treino de cada GP (uma única vez, <10s por modelo) e custo qualitativo/analítico de avaliação subsequente (produto escalar para a média; solução de um sistema de N equações lineares para a variância); contagem total de… [Sec. 5, p.14-15 (parágrafo após Fig. 3)]
- **c59** (UA-DBO): Tempo total de parede por caso completo de otimização, decomposto em: preparação de dados/dataset de pré-treino (830h, aparentemente compartilhado entre DBO e UA-DBO), treino do modelo (0,47h DBO / 0,53h UA-DBO), avaliação de… [Sec. 4.3, Table 4, p. 21; Sec. 4.1.2, Table 2, p. 13–15 (colunas GPU…]
- **c65** (SABBa): Reporta sistematicamente o Nº de avaliações reais (Neval) necessário para atingir cada patamar de acurácia sequencial, como métrica central de parcimônia em TODOS os experimentos (analíticos e de engenharia) — essa é a principal… [Sec. 6.3]
- **c66** (PAL-SAPSO): (a) Complexidade computacional TEÓRICA (Big-O) de uma geração do algoritmo, derivada analiticamente na Seção III-E (não é medição empírica de tempo de parede, não há decomposição fit/busca/avaliação/instrumentação como na camada… [Sec. III-E; Sec. IV-B-2)]
- **c71** (SAEA/ME): Não reporta tempo de execução (wall-clock), nem custo de ajuste do GP separado da busca, nem decomposição fit/busca/avaliação/instrumentação como na camada ④ da dissertação. Reporta apenas um argumento de COMPLEXIDADE em número… [Sec. 3.1]
- **c75** (MO-EI/PI (Keane)): Apenas contagem de avaliações de função reais — nunca tempo de parede, nunca decomposição fit/busca/avaliação, nunca complexidade assintótica medida empiricamente: comparações percentuais/multiplicativas de esforço ('250% do… [First Example and Some Basic Searches, p. 883-884 (discussão da Fig.…]
- **c81** (UA-MORL-Diff): Reporta tempo de parede em prosa (não em tabela dedicada), decomposto por fase — pré-treino do modelo de difusão (por iteração), otimização por RL (por passo de política, incluindo geração+avaliação de propriedade+reuso de… [Sec. 4.1 (Device); Appendix B.9 (Devices and Computational Setup)]
- **c91** (EHVIMOPSO): (a) Tempo de parede (Time/s, média±desvio-padrão) comparando EHVI estática x dinâmica em ZDT1-3 (Tabela 1). (b) Número de avaliações reais (ActualSimulationCost) e razão de eficiência (EfficiencyRatio) entre EHVIMOPSO e MOPSO-CD… [Sec. 4.4 (texto); Table 1; Table 3.]
- **e1** (EMO): Dois tipos de custo relatados, nenhum como tempo de parede total por execução completa nos problemas DTLZ: (1) um microbenchmark isolado (Fig. 5) do tempo (segundos) e do número de células da decomposição do espaço de objetivos,… [Sec. 4.3 (parágrafo de limitações); Sec. 3.4, Fig. 5]
- **e102** (MOEA/D-ASS): Apenas complexidade computacional TEÓRICA do ajuste do modelo CoMOGP, derivada da necessidade de inverter a matriz de covariância Ky de tamanho (nT)×(nT): O((nT)^3), maior que a de treinar T GPs independentes; nenhuma medição… [Sec. II-D]
- **e103** (IBEA-MS): Só complexidade computacional TEÓRICA (Big-O), sem tempo de parede medido em segundos/minutos: Seção III-B decompõe cada um dos 7 algoritmos (IBEA-MS; os offline AK-IBEA e NSGA-II-GP; os online Par-EGO, MOEA/D-EGO, K-RVEA, CSEA)… [Sec. III-B; Table S.I (material suplementar)]
- **e104** (RVMM): Menção qualitativa ao custo de treino do GP como motivação para usar GP incremental (em vez do GP completo) nos experimentos de 50-D, e menção a uma comparação de runtime entre os oito algoritmos cujos resultados estão… [Sec. IV-D (economia de custo via GP incremental); Sec. IV-C menciona…]
- **e16** (EGBO): Não reporta custo COMPUTACIONAL do otimizador (sem tempo de ajuste do GP, sem tempo de otimização da aquisição/optimize_acqf, sem complexidade O(n³) discutida). Reporta apenas custo/tempo EXPERIMENTAL (wet-lab) da plataforma SDL:… [Methods, Sec. Experimental platform]
- **e17** (MOBO): So discussao qualitativa de complexidade computacional, sem tabela e sem decomposicao fit/busca/avaliacao/sonda: (a) EHVI ingenuo escala O(N^P) na integracao da Eq. 3; com decomposicao eficiente do espaco de objetivos cai para… [Sec. V (Conclusion); complexidade da aquisicao em Sec. III-B]
- **e3** (HeE-MOEA): Tempo de treino (ajuste) do surrogate por iteração/geração (Fig. 4, boxplot por problema × N); tempo TOTAL de uma execução (Fig. 5, boxplot por problema × N); tempo médio de treino versus número de variáveis de decisão N para 4… [Sec. I; Sec. III-C; Sec. V-D, Figs. 4–6; Sec. VI (Conclusão, caveat…]
- **e64** (SA-MOPSO (PPD)): Tempo médio de execução (forward run, minutos) separado por tipo -- GPR vs. PBM -- e tempo de parede paralelizado (100 nucleos HPC) por iteração interna (só GPR) e por iteração externa (Tabela 3), para SA-MOPSO e PB-MOPSO na… [Table 3; Sec. 5.2.1]
- **e7** (EDN-ARMOEA): Tempo de treino do surrogate (separado) e tempo total de otimização por execução, versus d∈{20,40,60,100} e versus m∈{3,5,10,20}, mas medido em UM ÚNICO problema (DTLZ7), comparando EDN vs. GP e EDN vs. HeE (Fig. 3);… [Sec. III-C; Fig. 3]
- **e74** (CLMEA): Complexidade computacional teórica de treino/predição do RBF+PNN vs. Kriging (O(n³), citado como custoso e sensível ao número de pontos de treino); tempo de execução TOTAL empírico (treino+seleção+avaliação, não decomposto… [Sec. IV-G; Fig. 12]
- **e8** (NN-EGO): Tempo de avaliação (inferência) do ANN sobre todo o espaço de desenho (140 lotes de 20k candidatos: ~1.6s de chamada do modelo + 0.8s de distância latente + 1.3s de I/O por lote, ~9min seriais ou ~3.4min com 8 processos… [Text S2 (S10); Figure S3 (S8)]
- **e81** (qPOTS): Só menção qualitativa (sem números/tabela/segundos): o custo da computação de aquisição do qPOTS é dito 'substancialmente mais rápido' que qNEHVI e qPAREGO no CRM (d=24), o que motivou não ligar a aproximação de Nyström nesse… [Sec. 4.2 (parágrafo de configuração do experimento CRM); complexidade…]
- **e86** (NSGAIII-EHVI): (a) Complexidade teórica O(·) das etapas do cálculo do EHVI por IS versus por MCS (Sec. III-F, Tables I e II): para o IS, o total é O(N_E·M + PE_max·N_E·N_P·M); para a MCS convencional, cada etapa análoga ganha um fator extra N_P… [Sec. III-F (Tables I-II, teórico); Sec. IV-C (Table V, Fig. 3,…]
- **emo1** (MPoI / HypI / DomRank / MSD (4 estratégias de infill)): Tempo médio de computação POR avaliação do critério de infill (não o tempo total de uma execução completa nem o tempo de ajuste/retreino do GP), sobre 1000 repetições, variando sinteticamente o nº de objetivos (2 a 6) e o tamanho… [Sec. 5, Fig. 5, p. 879]
- **jin3** (GS-MOMA / GSM (mono: GS-SOMA)): Fórmula analítica (não medição empírica) do custo total: Tcomp = Gdb*Npop*sum(Fi) + (Gmax-Gdb)*[Npop*(Tens+TPR+2*kterm*sum(Fi)+Toverhead)] para GS-SOMA/GS-MOMA (Eq. 24), versus Tcomp = Gdb*Npop*sum(Fi) +… [Sec. IV-D]
- **mtm4** (MAES (variante MO: M-NSGA-II)): Apenas complexidade TEÓRICA (Big-O), sem medição empírica de tempo de parede/CPU em segundos e sem decomposição fit/busca/avaliação: treino do metamodelo custa O(N·m³·d + m²·d) (N iterações da otimização de verossimilhança, m… [Sec. II, p.4 (complexidade teórica); Sec. VI, p.16 ('almost the same…]
- **mtm6** (EHVI (EI_H) / "EHVI-EGO"): Apenas uma menção qualitativa de tempo total de parede para a única execução do experimento (25 avaliações, incluindo re-ajustes do modelo a cada iteração), sem decomposição por fase (ajuste do modelo vs. otimização do critério… [Sec. V-A (Numerical Experiment), parágrafo 'Result' (item c)]
- **wang4** (SA-NSGA-II): Tempo total por execução (s) para 3 configurações sob 100 gerações iguais (Table II); tempo como CRITÉRIO DE PARADA (1h) numa segunda comparação (Table III); custo-proxy = nº de chamadas ao algoritmo de alocação de pacientes (=nº… [Abstract; Sec. V-A; Table II]

Sem custo reportado (12): b13, c105, c123, c48, c82, c97, e21, e4, e40, e9, f9, pp6.

### 8.3 Resultados negativos e ressalvas dos autores (268 passagens): contagem por artigo e seleção

Contagem por artigo: c241 10 · c107 9 · c65 8 · c262 7 · e16 7 · e40 7 · b14 6 · b5 6 · b7 6 · b8 6 · c123 6 · c141 6 · c217 6 · c59 6 · e102 6 · e21 6 · f9 6 · b13 5 · b4 5 · c122 5 · c131 5 · c154 5 · c82 5 · e103 5 · e64 5 · e7 5 · e74 5 · b2 4 · c1 4 · c105 4 · c149 4 · c238 4 · c261 4 · c267 4 · c97 4 · e3 4 · pp6 4 · b1 3 · b15 3 · c106 3 · c276 3 · c29 3 · c71 3 · c81 3 · e1 3 · e86 3 · jin3 3 · mtm4 3 · wang4 3 · b3 2 · c24 2 · c250 2 · c50 2 · c66 2 · c75 2 · c91 2 · e4 2 · e81 2 · e9 2 · emo1 2 · b9 1 · c10 1 · c214 1 · c48 1 · c49 1 · e8 1.

Seleção (passagens em que a incerteza/σ/calibração é o objeto — as demais estão no companheiro, §C):

- **b1** (ParEGO) [Sec. VIII, p. 62]: A 100 avaliações (orçamento mais apertado), NSGA-II (piso sem surrogate) supera ParEGO no S-measure em DTLZ4a (sem significância) e vence significativamente em DTLZ7a -- o único caso, entre as 4 tabelas de resultado, em que o piso evolutivo puro bate a… «At 100 function evaluations, the outcome is much the same, except for the functions DTLZ4a and DTLZ7a, where NSGA-II obtains a higher mean value (and is significantly better on DTLZ7a).»
- **b13** (AdaMoR-DDMOEA) [Sec. 5.4]: O próprio artigo reconhece que o método completo perde para 3 dos 4 baselines em ZDT3 (frente desconexa) e para o IBEA-MS em vários DTLZ degenerados, admitindo mau desempenho geral em geometrias difíceis apesar do mecanismo de confiança. «it performs poorly on degenerated or disconnected problems.»
- **b14** (SA²-MOEA) [Sec. 4.6.2 (discussão do WFG7)]: A amostragem baseada em incerteza (o mecanismo central do artigo) é explicitamente apontada como ineficiente para manter diversidade no WFG7 (problema separável e unimodal, que exige alta manutenção de diversidade). «SA2-MOEA adopts the uncertainty-based sampling strategy, which is inefficient to the maintenance of diversity.»
- **b14** (SA²-MOEA) [Sec. 4.4 (discussão da Fig. 3(d), WFG5)]: Nos problemas enganosos (deceptive, ex. WFG5), a má aproximação do ensemble faz com que TODAS as variantes de otimizador (Fig. 3) e de amostragem (Tabela 4) tenham desempenho parecido entre si - o mecanismo de incerteza deixa de discriminar entre estratégias… «the ensemble models are poorly approximated for this problem [38].»
- **b15** (U-RankMOEA) [Apendice G, Table 8]: Modelar explicitamente a correlacao entre objetivos (Deep GP multi-saida via coregionalizacao linear, LMC) PIORA a HV mediana em vez de melhorar, nos dois problemas testados - atribuido a variancia de estimacao extra introduzida pelos parametros adicionais… «The independent model attains higher median hypervolume in both cases. A plausible explanation is that the extra parameters introduced by the LMC formulation increase estimation variance when only a few hundred…»
- **b15** (U-RankMOEA) [Fig. 3, texto de imagem via OCR, pag. 17 (contradiz a…]: Segundo a legenda da Fig. 3 (capturada via OCR da imagem), o proxy de triagem 'penalizado por incerteza' tem correlacao de Spearman MENOR (rho=0,18) que o proxy 'so media' (rho=0,23) - o oposto do que o texto corrido afirma ('alinhamento substancialmente… «Mean-only proxy (Spearman p=0.23) - Uncertainty-penalised proxy (Spearman p=0.18)»
- **b15** (U-RankMOEA) [Apendice F, Fig. 6]: Granularidade excessiva do classificador de rank (K>=6 categorias) nao melhora a HV final e ainda piora a calibracao (ECE aumenta); K muito pequeno (K=3) tambem piora significativamente o desempenho - expondo que mais 'resolucao' na representacao de… «Differences between K = 5 and K ≥ 6 are not accompanied by additional HV gains, while smaller choices (e.g., K = 3) produce significantly worse outcomes»
- **b2** (MOEA/D-EGO) [Sec. VIII (Conclusion); ver também Sec. VII-D-1 e Sec.…]: A qualidade de predição do processo Gaussiano é ruim em ZDT4 (instância multimodal, 'many local PFs'), levando os dois algoritmos (ParEGO e MOEA/D-EGO) a falhar em aproximar a PF satisfatoriamente — a única instância, entre as 12 testadas, em que o… «We also found that the prediction quality of Gaussian stochastic process modeling is poor in ZDT4 and it makes the algorithms fail in approximating the PF»
- **b2** (MOEA/D-EGO) [Sec. VII-E-3 (Why Some Instances Are Harder Than Others)]: Em ZDT6, o IGD do MOEA/D-EGO deixa de melhorar nas últimas 60 (de 200) avaliações reais — os autores atribuem isso a uma falha do próprio critério de aquisição (expected improvement) em equilibrar exploração e explotação, desperdiçando orçamento computacional… «the IGD value has not effectively reduced during the last 60 function evaluations. It suggests that the last 60 test points are mainly for exploration, which wastes the computational resource in this instance.»
- **b2** (MOEA/D-EGO) [Sec. VII-E-2 (FuzzyCM Versus One Single Model)]: A simplificação de modelagem que o próprio MOEA/D-EGO usa em produção (FuzzyCM, clusterização fuzzy para conter o custo do GP) produz qualidade de solução mensuravelmente PIOR do que um único modelo GP global treinado com todos os pontos — o atalho que torna… «We can conclude that MOEA/D-EGO with single model does performance better in terms of solution quality.»
- **b3** (K-RVEA) [Sec. IV-B, p. 9 (Table I, discussão)]: Em DTLZ1 e DTLZ3, para TODOS os k testados (3,4,6,8,10), K-RVEA empata estatisticamente (≈) com RVEA — o piso sem surrogate — no teste de Wilcoxon rank-sum: usar o Kriging não produz nenhuma vantagem detectável nesses dois problemas multimodais, atribuído… «We surmise that DTLZ1 and DTLZ3 have many local Pareto optimal solutions.»
- **b4** (CSEA) [Sec. III-C.4]: Na região R3, o classificador está sistematicamente enganado: soluções que ele prevê como categoria I são, na prática, muito provavelmente categoria II (o inverso do esperado). O algoritmo lida com essa miscalibração invertendo deliberadamente a decisão —… «Region R3 represents the region in which category I solutions will be very likely to be predicted as category II solutions.»
- **b5** (Prob-RVEA / Prob-MOEA/D (+ Hyb-RVEA / Hyb-MOEA/D)) [Sec. IV-A]: Ignorar a incerteza faz os algoritmos convergirem, no espaço verdadeiro, para soluções piores do que o valor observado no espaço do surrogate durante a busca — o 'engano' do modelo é a causa central do mau desempenho das abordagens sem σ. «The performances of the generic approaches and TL were poor because they did not consider uncertainty in the solutions during the optimization process.»
- **b5** (Prob-RVEA / Prob-MOEA/D (+ Hyb-RVEA / Hyb-MOEA/D)) [Sec. IV-A, Fig. 10]: O HV no espaço do surrogate ('acreditado') das abordagens probabilísticas efetivamente DIMINUI ao longo da busca, mesmo enquanto o HV verdadeiro aumenta — a seleção probabilística rejeita deliberadamente soluções de média melhor mas alta incerteza; confiar só… «the surrogate HV for TL improved with function evaluations and the probabilistic approaches it gradually decreased. This is because the probabilistic approaches reject solutions with better objective values if they have…»
- **b5** (Prob-RVEA / Prob-MOEA/D (+ Hyb-RVEA / Hyb-MOEA/D)) [Sec. IV-A, Fig. 9]: Mesmo as abordagens propostas (com incerteza) falham completamente em problemas com frente de Pareto desconexa, por falta de dados offline suficientes — um limite reconhecido pelos próprios autores, não resolvido pelo uso do σ. «We also observed that all approaches failed to get solutions closer to both disconnected Pareto sets in the bottom row. This is because of the lack of adequate offline data for solving such MOPs.»
- **b7** (DR (Dual-Ranking)) [Sec. 1 (Introduction)]: Motivação central do artigo: a incerteza epistêmica do surrogate (mesmo sem ruído aleatório no dataset) pode degradar seriamente o desempenho da otimização ao enganar a busca, levando a soluções sub-ótimas - é o problema que o dual-ranking tenta resolver. «This approximation uncertainty can severely degrade optimization performance [Wang et al., 2018] by misleading the search, resulting in suboptimal solutions [Smith and Winkler, 2006].»
- **b7** (DR (Dual-Ranking)) [Sec. 3.1 (Motivation)]: Mecanismo explícito do erro: quando o otimizador explora regiões de baixa densidade de dados, o surrogate pode prever valores irrealisticamente bons com alta incerteza, e essas soluções são falsamente preferidas por parecerem não-dominadas - a causa-raiz do… «the predicted objective values may be unrealistically small with high uncertainty. Such solutions will be falsely preferred by the algorithm as they are regarded as non-dominated solutions»
- **b7** (DR (Dual-Ranking)) [Sec. 4.2 (Surrogate Prediction Performance Results)]: Caveat de calibração: o surrogate BNN exibe grande variabilidade tanto na acurácia da predição quanto nas estimativas de incerteza entre problemas - a fonte de incerteza menos confiável entre as 4 testadas. «The BNN model shows larger variability in both prediction accuracy and uncertainty estimates.»
- **b8** (KTA2) [Sec. IV-E-2, Discussions (comentário sobre WFG3)]: Em WFG3 (PF em curva degenerada), tanto KRVEA quanto KTA2 pioram seu desempenho ao amostrarem excessivamente por incerteza - um efeito colateral negativo explícito do critério de incerteza nessa geometria de frente. «Since the PF of WFG3 is a degenerated curve, KRVEA and KTA2 frequently sample too many uncertain solutions which result in poor performance.»
- **b8** (KTA2) [Sec. IV-B]: Os autores evitam valores altos de phi (que tornariam a escolha do infill por incerteza mais pura/gulosa) por temerem que indivíduos de incerteza muito alta prejudiquem a convergência do algoritmo - um caveat explícito sobre o risco de sobre-explorar pela… «Considering that individuals with large uncertainty may may cause the algorithm converged, φ is set to 0.1N as a general setting for all test instances.»
- **b8** (KTA2) [Sec. V, Conclusions]: Limitação de escalabilidade assumida pelos autores: por depender de Kriging (custo cúbico, degradação em alta dimensão), o método só é aplicável a problemas de baixa dimensão; sugerem substituir o Kriging por RBFN ou redes com dropout para obter incerteza em… «as the dimension limitation of Kriging model, our method can be only applied to low-dimensional problems.»
- **b9** (USeMO) [Sec. 5.2 ("Uncertainty maximization vs. random selection");…]: O artigo relata explicitamente que, embora a maximização de incerteza (volume do hiper-retângulo LCB/UCB) supere a seleção aleatória na escolha do candidato final, em ALGUNS casos a política aleatória é competitiva — evidência de que o ganho atribuível ao uso… «However, in some cases, random policy is competitive, which shows that all candidates from the solution of cheap MO problem are promising and improve the efficiency.»
- **c1** (BS-MOBO) [Sec. IV-A-1]: O framework de seleção em lote proposto (B-HUCB + seleção gulosa) fica preso em ótimos de Pareto locais em problemas com frente/conjunto de Pareto desconectado, resultando em convergência pobre mesmo com o mesmo modelo GP que outros métodos usam com sucesso. «BS-MOBO-GP is outperformed by other Kriging-based algorithms on the UF5 and UF6 test instances which both have disconnected Pareto set and many local Pareto optimal points.»
- **c1** (BS-MOBO) [Sec. IV-A-2]: Em orçamento pequeno e baixa dimensão, a escolha de modelo do próprio método proposto (BNN com MC dropout) é PIOR que a alternativa mais simples (Gaussian Process) — resultado negativo específico para o regime de poucos dados, atribuído à necessidade de mais… «The performances of BS-MOBO are worse than those of BS-MOBO-GP for most test instances.»
- **c1** (BS-MOBO) [Sec. IV-B-1]: Em alta dimensão, os métodos baseados em modelo Gaussian Process (incluindo variantes do próprio método) perdem para pisos SEM surrogate em problemas específicos, porque o modelo com poucos dados de treino não aproxima bem a função e o orçamento é gasto… «The Gaussian process model with limited training examples cannot approximate the large scale complicated objective functions well. The model-based methods spend all evaluation budget on exploring the decision space for…»
- **c105** (SMS-EGO) [Sec. 3.1 (SMS-EGO), p. 787]: O uso da LCB (que incorpora a incerteza/sigma do GP) para prever solucoes potenciais pode gerar previsoes ligeiramente alem do espaco objetivo real, o que motiva a necessidade de introduzir epsilon-dominancia aditiva adaptativa para lidar com o problema. «Due to the use of the LCB, potential solutions can be predicted slightly beyond the real objective space.»
- **c105** (SMS-EGO) [Sec. 5 (Conclusions), p. 792]: Nas conclusoes, os autores reconhecem explicitamente que o uso da lower confidence bound (mecanismo que embute a incerteza do GP) para calcular a contribuicao de hipervolume gera efeitos colaterais indesejados, incluindo a ocorrencia de solucoes dominadas… «Since the use of the lower confidence bound for computing the hypervolume contribution in SMS-EGO also leads to some undesired side effects, such as the occurrence of dominated solutions»
- **c106** (EMMI (EMmI)) [Sec. 6.1, p. 17]: O modelo de GP com dependencia nao-separavel entre objetivos -- a principal contribuicao de modelagem do artigo, alem do proprio EMMI -- nao entrega a vantagem esperada nos dois exemplos testados: em media piora o desempenho de quase todos os criterios no… «The somewhat surprising result here is that the dependence GP model appears to offer little advantage over the less computationally demanding independence model. In fact, on average, it seems to perform slightly worse…»
- **c106** (EMMI (EMmI)) [Sec. 7 (Conclusions and Discussion), p. 20]: Apesar de a dependencia ser a contribuicao central de modelagem do artigo (GP multivariado nao-separavel), os autores concluem recomendando o modelo mais simples (independente) para uso pratico, citando facilidade de implementacao e menor custo computacional… «However, the authors recommend the EMMI-Ind procedure because it is simpler to implement, and requires considerably less computational overhead.»
- **c107** (MS-VHGP-EIHV) [Sec. II-C]: O achado mais crítico do artigo para o tema da incerteza: um dos dois tipos de superajuste específicos da regressão heterocedástica (VHGP) faz com que o EIHV fique ALTO perto de pontos JÁ AMOSTRADOS (em vez de em regiões inexploradas), levando a experimentos… «This leads to large EIHV values around sampled points, rather than unevaluated regions, and leads to dense, noninformative experiments at a few fixed points.»
- **c107** (MS-VHGP-EIHV) [Sec. III-E4]: Em T6 sob ruído homocedástico, o método proposto (com seleção de modelo) é superado pelo método existente (GP padrão sozinho) — os próprios autores tratam isso como falha do mecanismo de seleção de modelo. «For T6, the proposed method is outperformed by the existing method in the case where the noise is homoscedastic.»
- **c107** (MS-VHGP-EIHV) [Sec. III-E4]: Em T6, o VHGP usado sozinho é o pior dos três métodos mesmo sob ruído heterocedástico (o cenário em que, a priori, deveria ser favorecido) — resultado que os próprios autores chamam de contraintuitivo, atribuído a superajuste da oscilação da função latente… «This is a somewhat counterintuitive result because VHGP regression seemed appropriate for fitting samples wherein the noise level is actually a function of input and should, therefore, provide a good surrogate.»
- **c107** (MS-VHGP-EIHV) [Sec. II-C]: O custo do critério de seleção de modelo proposto (LOO) escala como O(N^4) — pior do que o MC — tornando-se proporcionalmente mais lento conforme o número de avaliações aumenta, apesar de ser mais rápido para poucos pontos (<~40). «The computation requires that both the GP and HGP regressions are proportional to O(N3). Therefore, LOO will require O(N4) calculations.»
- **c122** (θ-DEA-DP) [Sec. III-E]: Dropout, técnica de regularização comum em redes profundas (e usada por outros métodos como estimador de incerteza via MC-dropout), foi testado e EXPLICITAMENTE REJEITADO no treino de Pareto-Net/θ-Net por piorar o desempenho final de otimização; os autores… «we find that it usually worsens the final optimization performance in our experiments and a very modest weight decay without dropout is usually a better configuration.»
- **c123** (EPBII / EIPBII) [Sec. VI-A-1]: Nenhum dos seis critérios consegue alcançar a fronteira verdadeira em ZDT4 e ZDT6, devido à baixa acurácia do modelo Kriging nesses problemas. «no criterion can reach PF in ZDT4 and 6 due to the poor approximation accuracy of the Kriging models.»
- **c123** (EPBII / EIPBII) [Sec. VI-B-3]: Com modelo pouco acurado (DTLZ2max3, k=8, 2 objetivos), o EHVI tem IH e IGD médios muito altos — o critério baseado só em hipervolume não consegue obter boas NDSs quando a acurácia do modelo Kriging é ruim. «We note that when model accuracy is poor, EHVI cannot efficiently obtain good NDSs.»
- **c131** (MORBO) [Apendice A.1]: Tentativa de otimizar continuamente as amostras de RFF da posterior por gradiente falha: muitos parametros acabam na fronteira da caixa de busca, causando sobre-exploracao e piorando o desempenho de BO -- um caso claro em que uma forma especifica de explorar… «We tried to optimize these RFF samples using a gradient based optimizer, but found that many parameters ended up on the boundary, which led to over-exploration and poor BO performance»
- **c131** (MORBO) [Apendice A.1]: A aproximacao da posterior via Random Fourier Features degrada com o aumento da dimensao: em espacos de alta dimensao, amostrar exatamente a posterior sobre um conjunto discreto supera usar RFFs, atribuido a perda de qualidade da aproximacao RFF -- ou seja, a… «we find that exact posterior sampling over a discrete set achieves better performance than using RFFs, which we hypothesize is due to the quality of the RFF approximations degrading in higher dimensions»
- **c131** (MORBO) [Sec. 5.1 ('Optical design problem')]: No problema de design otico (alta dimensao, d=146), NENHUM dos outros baselines de BO com GP global e competitivo com o piso evolutivo sem surrogate NSGA-II fora do regime de amostra muito pequena -- os metodos de BO 'assistidos' convencionais perdem… «no other baselines are competitive with NSGA-II except in the very small sample regime (less than 500 evaluations)»
- **c131** (MORBO) [Sec. 6 (Discussion)]: Limitacao reconhecida na Discussao: a aquisicao baseada em hipervolume (usada pelo MORBO) tem complexidade computacional que escala mal com o numero de objetivos, e o MORBO e otimizado para o regime de lote grande/alto orcamento, podendo perder para outros… «using hypervolume-based acquisition means the computational complexity scales poorly with the number of objectives»
- **c141** (MMRAEA) [Table 2, linha de placar agregado (coluna MMRAEA-V3)]: Contra a variante MMRAEA-V3 (seleção só pelo modo de número de fronteira, sem ensemble tri-modo nem termo de incerteza), o MMRAEA completo (com Q,U e exploração por incerteza máxima) empata estatisticamente em 30 das 48 instâncias e PERDE em 3 — o menor… «MMRAEA-V3 ... +/−/≈ 3/15/30»
- **c141** (MMRAEA) [Sec. Effectiveness of bi-population based on CSO and GA…]: Em problemas fortemente multimodais (DTLZ1 nas 4 dimensões; DTLZ3 em d=20,40), a variante MMRAEA-CSO (busca só pelo operador CSO, sem GA) bate SIGNIFICATIVAMENTE o MMRAEA completo (bi-população) — juntar a sub-população GA piora o resultado nesses casos… «Since the evolutionary operator based on CSO shows good ability on exploration, MMRAEA-CSO outperforms MMRAEA on DTLZ1 and DTLZ3 which have multimodal landscapes.»
- **c149** (LBN-MOBO) [Sec. 4.1]: A incerteza aleatória prevista pelo Deep Ensembles é pouco confiável em problemas complexos de alta dimensão, podendo prever ruído inexistente ou não captar o ruído real — o que pode desestabilizar LBN-MOBO se usada sem cuidado. «it often predicts high aleatoric uncertainty where it is non-exist or fails to capture the existing ones. This is a fundamental limitation of Bayesian neural networks»
- **c149** (LBN-MOBO) [Sec. E.1, Fig. 20]: Incluir incerteza aleatória quando o ruído do problema é desprezível não ajuda e pode atrasar a convergência (ZDT1/ZDT2/ZDT3) — resultado negativo direto do próprio mecanismo do artigo. «incorporating aleatoric uncertainty does not affect the exploration process in a beneficial manner, as showcased by the ZDT1 results, and may even delay the convergence, as observed in the ZDT2 and ZDT3 experiments»
- **c149** (LBN-MOBO) [Sec. 5.4]: Sem o termo de incerteza epistêmica na aquisição, o artigo reconhece que pode haver um pequeno ganho LOCAL de otimização em uma região específica — um contra-exemplo pontual à vantagem geral de usar incerteza. «when uncertainty is excluded from the process, the budget for surrogate Pareto front optimization is concentrated solely on performance dimensions. This concentration may occasionally lead to a slight local enhancement…»
- **c154** (JES) [Apêndice L.6]: A estimativa de entropia condicional que assume ruído zero (JES-0/MES-0) é nitidamente mais fraca que as demais no problema Marine (M=4) mesmo após a correção ad hoc para ruído — os autores recomendam explicitamente não usá-la quando possível. «we generally recommend against using the zero-variance estimate if possible»
- **c154** (JES) [Apêndice L.7]: Entre os baselines de melhoria/escalarização, a versão que ignora o ruído de observação (ParEGO, EHVI) tem desempenho comparável ou melhor que a versão que o modela explicitamente (NParEGO, NEHVI) — modelar o ruído não compensa claramente nesses dois métodos. «the greedier strategy which ignores the noise seems to perform reasonably well compared to the strategy which accounts for the noise»
- **c24** (DTK-MODE) [Sec. IV-B]: Pequenas discrepâncias residuais entre as soluções mais próximas do ponto utópico obtidas pelo MODE assistido por DTK e pelo MODE com FEA direta são admitidas mesmo na maior configuração de amostragem testada, e atribuídas pelos autores à falta de pontos de… «The small discrepancies are thought to be caused by the lack of sampling points and maximum number of iterations or the imperfection of the MODE algorithm itself.»
- **c24** (DTK-MODE) [Sec. II-B]: Krigings de ordem fixa têm fraquezas conhecidas que motivam a proposta do DTK: Simple Kriging (SK) e Ordinary Kriging (OK) tendem a ter maior erro de ajuste para funções com flutuações acentuadas, enquanto Taylor Kriging (TK) e Universal Kriging (UK) de ordem… «It is expected that, as shown in Table I, simple Kriging (SK) and ordinary Kriging (OK) may have a bigger fitting error for a function with sharp fluctuations, while TK and universal Kriging (UK) give oscillation for a…»
- **c241** (EMMOEA) [Sec. I]: Caveat geral e não-quantificado dos autores: a estimativa de incerteza do GP pode se tornar pouco confiável quando há poucos dados de treino — motivação da Introdução, sem medição de calibração no artigo. «the performance of the GP model for estimating the uncertainty level may become unreliable when the amount of training data is highly limited.»
- **c241** (EMMOEA) [Sec. I]: Crítica geral (não específica ao EMMOEA) à 2ª categoria de critérios de infill da literatura: erros na estimativa da incerteza E dos valores dos objetivos podem induzir à escolha errada de solução para avaliação cara. «errors in estimating the uncertainty information and the objective values may mislead the selection of the right solutions for expensive evaluations.»
- **c241** (EMMOEA) [Sec. IV (Conclusion)]: Limitação de escalabilidade declarada pelos próprios autores: EMMOEA precisa de m+1 GPs (complexidade cúbica), tornando-o pouco adequado a problemas de alta dimensão/grande escala; desempenho pode deteriorar com mais variáveis de decisão e mais amostras de… «EMMOEA needs to build a large number (m+1 for m-objective problems) of Gaussian process models, making it less suited for solving high-dimensional or large-scale multi-/many-objective optimization problems.»
- **c250** (K-MOGA) [Sec. 5 (Summary), p. 031401-9 a 031401-10]: Os proprios autores reconhecem que o criterio de aceitacao do metamodelo (Eq. 12-14, ligando erro previsto do Kriging a MMD) foi derivado a partir de um cenario de PIOR CASO, sendo portanto conservador - o que sugere que K-MOGA provavelmente usa mais chamadas… «it should be noticed that the relation between Kriging's predicted error and MMD for the objective functions, and also for the constraints, is devised based on a worst case scenario and thus the proposed criterion can…»
- **c250** (K-MOGA) [Sec. 5 (Summary), p. 031401-9 a 031401-10]: Caveat metodologico explicito: o conjunto de pontos usado para treinar o Kriging nao e escolhido por nenhum criterio de amostragem proprio para metamodelagem - e simplesmente o subconjunto de individuos que os operadores geneticos (crossover/mutacao)… «the sample set used in Kriging metamodel can affect the accuracy of the metamodel (currently, they are generated by GA operations). By devising a less conservative criterion and an improved sampling strategy for…»
- **c261** (DirHV-EGO) [Sec. VI CONCLUSION (Limitations), p.12]: Limitação explícita dos autores: como DirHV-EGO usa modelos GP para aproximar os objetivos, e GPs sofrem da maldição da dimensionalidade, o método enfrenta dificuldade em problemas de alta dimensão de decisão — um caveat sobre o próprio surrogate, não sobre o… «DirHV-EGO uses GP models to approximate the objectives. Due to the fact that GP models are prone to suffer from the curse of dimensionality, it can be a challenge for DirHV-EGO to deal with high-dimensional MOPs.»
- **c261** (DirHV-EGO) [Supplementary Sec. III-D.1, p.9-10]: Em problemas com PF degenerada (DTLZ5/6, curva 2-D mesmo com m objetivos) ou descontínua (DTLZ7), conforme m aumenta, muitos vetores de direção deixam de ter interseção com a PF verdadeira, tornando os subproblemas correspondentes 'desnecessários' e… «when direction or weight vectors have no intersection with the true PF, the corresponding subproblems might be unnecessary and result in an inefficient use of computing resources»
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF)) [Sec. 5 (antes da eq. 2); Fig. 1]: Achado central do artigo (a passagem citada pela dissertacao): sem tratamento adequado do ruido, a EHVI gasta o orcamento de avaliacoes tentando otimizar picos de ruido que PARECEM otimos de Pareto, produzindo uma frente final aglomerada ('clumped'), pouco… «EHVI proceeds to spend its evaluation budget trying to optimize noise, resulting in a clumped Pareto frontier that lacks diversity.»
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF)) [Sec. 5]: A heuristica de 'plug-in' (usar a media posterior do GP como estimativa pontual dos valores verdadeiros nos pontos ja avaliados) -- uma tentativa razoavel de regularizar contra o ruido -- TAMBEM falha e produz frentes aglomeradas. «we find that this heuristic also leads to clustered Pareto frontiers (EHVI-PM in Fig. 1)»
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF)) [Sec. 5; detalhado no Apendice H.10]: O mesmo padrao de falha (clumping sob ruido) aparece em DGEMO, um metodo de lote que nao modela ruido, e em outras baselines que usam a media posterior em vez dos valores observados ao computar melhoria de hipervolume -- o problema nao e especifico da familia… «Similar patterns emerge with DGEMO (which does not account for noise), and other baselines that utilize the posterior mean rather than the observed values when computing hypervolume improvement»
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF)) [Sec. 3 Related Work]: Contraste explicito com a literatura de simulacao anterior: outros autores concluiram que MODELAR o ruido explicitamente NAO melhorava o desempenho da otimizacao (um deles recomendou simplesmente ignora-lo); os autores de c262 relatam o oposto para o metodo… «Horn et al. [26] suggest that the best approach is to ignore noise, and Koch et al. [33] concluded that further research was needed to determine if modeling techniques such as re-interpolation could improve BO…»
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF)) [Apendice H.5]: A variante de amostra unica (qNEHVI-1, que aproxima o GP por Random Fourier Features em vez de amostrar exatamente a posterior) degrada em espacos de busca de alta dimensao -- uma limitacao propria do mecanismo aproximado de incerteza do artigo. «qNEHVI-1 does not perform as well a qNEHVI on higher dimensional problems. We hypothesize that the RFF approximation degrades in higher dimensional search spaces»
- **c267** (SAMOEA-TL2M) [Sec. I (Introduction) e Sec. II-D (Motivation), citando [45]]: Caveat conceitual, repetido três vezes ao longo do artigo (Introdução, Motivação, Discussão) e atribuído a Li et al. [45]: a incerteza do surrogate NÃO deveria ser tratada o tempo todo — só quando ela efetivamente atrapalha a melhoria de desempenho do… «uncertainty in surrogate models should be addressed only when it hinders the overall performance improvement of the algorithms»
- **c267** (SAMOEA-TL2M) [Sec. IV-D-1, Table V]: Na ablação da Tabela V, a variante que seleciona infills SOMENTE por incerteza alta (SAMOEA-TL2M-v2, sem o critério de convergência/diversidade do nível 1) perde para o método completo em 4 dos 7 problemas MaF — evidência direta de que priorizar a incerteza… «This is because SAMOEA-TL2M-v1 has difficulty managing uncertainty, while SAMOEA-TL2M-v2 ignores the balance between convergence and diversity.»
- **c29** (MO P-algorithm) [Sec. 7, ¶ sobre Fig. 8 / problem (13), p. 91-92]: No problema (13) (Fonseca-Fleming), usar um limiar mais próximo do conjunto de Pareto (em vez do vetor ideal) NÃO produz o aumento esperado de densidade de soluções não-dominadas perto do centro do Pareto set; ao contrário, a densidade aumenta perto dos… «Contrary to the expectations, increase of the density is seen near to the limit points of the Pareto set.»
- **c29** (MO P-algorithm) [Sec. 6, último parágrafo, p. 86-87]: Antes mesmo dos experimentos, os autores alertam (Sec. 6, a propósito do problema 13) que a discrepância entre o modelo estatístico assumido (campo gaussiano homogêneo e isotrópico) e a forma real da função-objetivo (platô quase constante com picos agudos)… «The discrepancy between the statistical model and the modelled functions can negatively influence the efficiency of the P-algorithm.»
- **c49** (Interactive Offline DD-MOEA Framework (sigla não-oficial, proposta por mim)) [Sec. 3.2, final do parágrafo]: Os autores alertam que a função de corte de tolerância (baseada em 1.96·σ̂, assumindo distribuição Gaussiana da predição do Kriging) pode precisar ser modificada dependendo da real distribuição de predição do surrogate usado — ou seja, a validade do cutoff de… «However, it has to be noted that the cutoff tolerance function can be modified depending on the prediction distribution of the surrogate.»
- **c50** (PD-MOEA) [Sec. 3.1, p.9 (após Fig. 2)]: Os autores alertam explicitamente que a incerteza preditiva dos GPs é uma fração considerável da faixa de variação de UBC e NOx, e que otimizar essas métricas SEM contabilizar a incerteza pode levar a configurações de parâmetros irrealisticamente otimistas e… «optimising these performance measures without accounting for the uncertainty may lead to unrealistically optimistic and wrong settings of the boiler parameters.»
- **c50** (PD-MOEA) [Sec. 5, p.15 (após Fig. 3)]: As grandes incertezas associadas a todos os pontos do arquivo probabilístico tornam a seleção de um único ponto de operação um desafio real: não é óbvio, a partir das predições médias isoladamente, como discriminar entre soluções ou como incorporar a… «the large uncertainties associated with all the points in the Pareto archive makes the selection of an operating point rather challenging: it is not obvious how to discriminate between the mean predictions»
- **c59** (UA-DBO) [Appendix B, p. 26–27]: Sem o termo extra de regularização KL (β=0), embora a acurácia da média seja boa, a incerteza estimada fica mal calibrada — um caveat explícito dos autores sobre a necessidade da regularização. «However, the corresponding calibrated ECE is significantly worse and remains far above the ensemble reference line, demonstrating that the resulting uncertainty estimates are poorly calibrated.»
- **c59** (UA-DBO) [Sec. 4.2, p. 17–18]: No caso A1 (fora da distribuição de treino), o modelo é menos bem calibrado e tanto DBO quanto UA-DBO acabam incluindo amostras numa região enganosa de subestimação do erro. «For Case A1, the model is less well-calibrated, so both DBO and UA-DBO include some samples that fall into a misleading under-estimated region.»
- **c59** (UA-DBO) [Sec. 4.2, p. 18]: No caso A2, a melhoria do UA-DBO sobre o DBO é apenas marginal, já que os erros de ambos já eram pequenos e a UQ era a mais precisa desse caso. «Most errors in Case A2 correspond to over-predictions, yet UA-DBO drives the population toward regions with small predicted uncertainty, resulting in only marginal improvement over DBO.»
- **c65** (SABBa) [Sec. 4.2]: Os próprios autores reconhecem que o limite conservador do erro (ε̄=3σ, derivado da variância preditiva do GP) NÃO garante matematicamente que o erro verdadeiro esteja contido no intervalo — apenas que a probabilidade de violação é baixa; é uma suposição… «Although this does not imply ε(z) ≥|ε(z)|, with ε the true error of the surrogate, the probability of dissatisfying the conservative assumption is very low.»
- **c65** (SABBa) [Sec. 4.2.1 / Appendix B]: A fórmula de erro conservador para a medida de VARIÂNCIA (ao contrário da de expectativa) carrega risco maior de superestimação, admitido explicitamente pelos autores. «The same can be conducted for the variance measure, with a bit more risks of overestimation:»
- **c65** (SABBa) [Sec. 7 (Conclusions)]: Limitações auto-declaradas na conclusão: os critérios de refinamento locais usados são mais baratos mas menos eficientes que critérios integrais; o uso de GP como surrogate limita o número de dimensões de entrada manejáveis (dezenas de dimensões exigiriam… «We used local refinement criteria, which are cheaper but less efficient than integral criteria. The use of GP surrogate models also limits the number of manageable input dimensions.»
- **c75** (MO-EI/PI (Keane)) [Kriging, p. 881 (parágrafo de abertura da seção)]: O próprio autor adverte que o kriging (o surrogate GP usado em todo o artigo) tem limitações práticas de escala: fica difícil ajustar modelos com mais de ~15-20 variáveis, e o custo numérico cresce muito com mais de algumas centenas de pontos de dado, porque… «Kriging is not a panacea for all evils, however. It is commonly found that it is difficult to set up such models for more than 15–20 variables and also that the approach is numerically expensive...»
- **c82** (TC-SAEA) [Sec. 3 (Proposed Algorithm), parágrafo final antes da Sec.…]: Os próprios autores reconhecem, já na formulação do método, que os valores sintéticos gerados pelo co-surrogate podem ser prejudiciais se as predições forem muito imprecisas — motivo pelo qual introduzem o filtro por intervalo de confiança (σ de GPs) ANTES de… «some synthetic values may be detrimental if the predicted values are extremely inaccurate.»
- **c82** (TC-SAEA) [Sec. 3.3 (Transferable Instance Selection)]: Caveat explícito sobre o risco de transferência negativa: se as instâncias do conjunto auxiliar forem preditas incorretamente, os valores sintéticos conflitam com os valores/rótulos reais e enganam o treinamento do modelo, prejudicando seu desempenho —… «if the instances are incorrectly predicted, the corresponding synthetic values or pseudo labels are likely to conflict with the real values/labels, thereby misleading the training of the model and undermining the…»
- **c82** (TC-SAEA) [Sec. 4.5 (Ablation Studies)]: Resultado negativo empírico central (ablação NS-SAEA, ver análise ficha 11): removendo o gate de confiança baseado em σ e aceitando TODOS os dados sintéticos sem filtro, o algoritmo deixa de convergir para soluções aceitáveis na maioria dos problemas — só… «Despite the use of transfer learning in NS-SAEA, it fails to converge towards a set of acceptable solutions. This observation clearly indicates the benefit of the proposed transferable instance selection.»
- **c82** (TC-SAEA) [Sec. 4.4 (discussão da Table 2)]: Com τ maior (10 em vez de 5), vários métodos baseados em surrogate — não só o TC-SAEA — degradam devido ao viés de busca introduzido pelo maior número de avaliações do objetivo rápido; o exemplo citado nominalmente é o concorrente HK-RVEA, também baseado em… «the performance of HK-RVEA on DTLZ1, DTLZ1a, DTLZ2, DTLZ3a and DTLZ6 is impacted negatively by a larger τ.»
- **c91** (EHVIMOPSO) [Sec. 3.3 (apos o passo 6 do algoritmo)]: Os autores reconhecem explicitamente que o grau de infactibilidade aproximado usado durante a busca (IFD, calculado a partir da média predita pelo Kriging mais uma margem beta x mse baseada na incerteza do modelo, Eq. 12) é DIFERENTE do grau de… «the symbol IFD is an approximate value of infeasibility degree, which is calculated on the basis of the mean values predicted by Kriging model, it is different from the real infeasibility degree IFD»
- **c97** (EnGP-MRO) [Sec. 6.3 [44]]: Como a maioria das soluções ótimas do problema é do tipo 'estado-limite' (na fronteira das restrições de salinidade), mesmo um pequeno erro do surrogate é suficiente para empurrar a solução para a região inviável — a própria arquitetura do problema amplifica… «the uncertainty in the surrogate model structure often causes the optimal solution to move into the infeasible region.»
- **e1** (EMO) [Sec. 4.3]: No único problema (DTLZ1) em que o EMO não supera claramente os MOEAs em hipervolume, a causa apontada pelos autores é diretamente a imprecisão do Kriging (não o critério de aquisição): o primeiro objetivo de DTLZ1 é mal aproximado, especialmente para valores… «After a closer examination it is observed that the accuracy of the Kriging models of DTLZ1 for most statistical criteria is sub-optimal.»
- **e1** (EMO) [Sec. 4.3]: Os autores generalizam o caso DTLZ1 num caveat explícito: o EMO depende de o Kriging capturar bem o comportamento das funções objetivo à medida que mais amostras chegam, o que reconhecem que 'pode nem sempre ser o caso' — a garantia prática do método depende… «they should be able to capture the behavior of the objective functions sufficiently well when enough samples become available, which might not always be the case»
- **e1** (EMO) [Sec. 4.3]: Os autores admitem que o custo computacional do EMO (ajuste do Kriging + otimização dos critérios estatísticos) é comparável ao do MOEA mais caro testado (SMS-EMOA, que depende do hipervolume), o que pode limitar o uso prático do EMO em problemas menos caros… «which might limit the practical usage of the EMO algorithm for some (less expensive) optimization problems»
- **e102** (MOEA/D-ASS) [Sec. I (Introduction)]: Motivação central do artigo: os autores mostram que as funções de aquisição de sucesso no caso monobjetivo (PI, EI, LCB) não são perfeitas em otimização multiobjetivo, podendo encorajar exploração excessiva quando o conjunto de treino tem muitos vetores… «these successful single-objective acquisition functions are not perfect for multiobjective optimization. They may unduly encourage exploration when the training dataset contains many crowded nondominated objective…»
- **e102** (MOEA/D-ASS) [Sec. IV-B]: Mecanismo explícito pelo qual a incerteza (σ) pode ATRAPALHAR: quando há muitos vetores não-dominados próximos no dataset de treino, o modelo prediz variância pequena na região promissora; a LCB clássica, então, prefere buscar em regiões menos exploradas (σ… «With such imbalances, the LCB will encourage searching in less explored areas but miss the promising region unless a sufficiently small γ is adopted.»
- **e103** (IBEA-MS) [Sec. V (Conclusion)]: Os próprios autores admitem que a incerteza (variância predita do Kriging) fica pouco confiável em alta dimensão e pode enganar o próprio mecanismo de seleção de modelo que ela alimenta — o caveat mais direto do artigo sobre o risco de confiar no σ. «the predicted values and predicted variances of the Kriging models are unreliable when the dimension of the decision space is high. This may mislead the proposed adaptive model selection mechanism.»
- **e103** (IBEA-MS) [Sec. IV-B]: IBEA-MS usa a incerteza SOMENTE para decidir qual modelo usar, nunca para manter diversidade da população — ao contrário dos comparadores (AK-IBEA, NSGA-II-GP), que reaproveitam a mesma incerteza para isso — e essa escolha de design é apontada como a causa… «IBEA-MS is slightly weak in dealing with the practical problems with very high demand for solutions diversity.»
- **e103** (IBEA-MS) [Sec. V (Conclusion)]: Ao listar limitações, os autores admitem que talvez NENHUM dos dois modelos disponíveis (Kriging ou RBFN) consiga de fato guiar a população rumo ao conjunto ótimo em certos casos — o gargalo pode estar no par de modelos disponível, não só no mecanismo que… «it is likely that neither the Kriging nor the RBFN model can guide the population toward the optimal solution set.»
- **e103** (IBEA-MS) [Sec. IV-B]: Apesar da vantagem crescente de IBEA-MS com a dimensão D (10→20→30), os próprios autores estabelecem um limite declarado de aplicabilidade acima de D=30, pela perda de confiabilidade do Kriging nessas dimensões. «it is not recommended to perform IBEA-MS for the practical problems with decision dimensions greater than 30.»
- **e16** (EGBO) [Sec. Evolution-guided Bayesian optimization (parágrafo…]: Citação central pela qual este artigo é referenciado na dissertação: os autores invocam Rasmussen et al. para justificar que um surrogate mal calibrado pode não comprometer a otimização se a estratégia de busca (aqui, a pressão de seleção evolutiva) já fizer… «a poorly calibrated surrogate model may be inconsequential as optimization is driven by the search strategy or with enough random sampling.»
- **e16** (EGBO) [Sec. Synthetic studies (discussão da Fig. 4b)]: Em MW7 (n=8), os mapas de densidade de amostragem indicam que o qNEHVI-BO puro (dependente só da predição de restrição do GP) NÃO controla bem a infactibilidade, desperdiçando amostras longe da região factível — e é exatamente a pressão de seleção do EA (que… «The probability maps suggest that qNEHVI-BO did not handle constraints well, whereas EGBO managed to minimize sampling far from the feasible space.»
- **e16** (EGBO) [Sec. Handling input and output constraints (discussão da…]: No estudo de reparo de restrições (AgNP), a abordagem PÓS-reparo (que usa o GP/EGBO para escolher candidatos e só depois reparar os infactíveis) chegou a sugerir MAIS pontos infactíveis do que a amostragem puramente aleatória (Sobol) — ou seja, o otimizador… «Finally, Fig. 5c (bottom) shows that optimization with post-repair suggested more infeasible points than Sobol sampling.»
- **e16** (EGBO) [Sec. Handling input and output constraints]: Os autores alertam que o viés introduzido por um operador de reparo pós-hoc mal escolhido pode ter efeito dramático quando a fronteira ótima (POS) coincide com a própria fronteira de restrição — a maior parte da amostragem fica presa explorando só uma região… «This bias can have dramatic effect if the POS is located at the constraint boundary, since most of the samples will be used to only explore a narrow region of the PF.»
- **e21** (PIO) [Results, 'Optimization results of single-objective task'…]: Apesar de incorporar incerteza, o método EI não supera de forma consistente o DOM (agnóstico à incerteza) nas tarefas single-objective — um resultado negativo específico para o uso EXPLORATÓRIO (não avesso a risco) da incerteza, já que EI tende a favorecer… «despite integrating uncertainty, the EI method does not consistently outperform the uncertainty-agnostic DOM method.»
- **e21** (PIO) [Results, 'Optimization results of single-objective task']: Na tarefa de similaridade à mestranol, o D-MPNN generaliza mal para a região estrutural do alvo (extrapolação para anéis fundidos complexos) e as previsões erradas frequentemente vêm acompanhadas de incerteza PEQUENA — ou seja, o modelo está mal calibrado… «these predictions frequently showed small uncertainty estimates, suggesting that D-MPNN may have inaccurately assessed uncertainty in these cases.»
- **e21** (PIO) [Discussion (parágrafo final)]: Os autores relatam explicitamente que a vantagem da PIO depende da qualidade da calibração da incerteza: quando essa calibração é pobre, a vantagem de usar incerteza (PIO) diminui — uma qualificação/defesa do papel do σ, não uma garantia incondicional de que… «When UQ calibration is poor, PIO's advantages are reduced, underscoring the need for more accurate and robust UQ techniques in molecular optimization.»
- **e3** (HeE-MOEA) [Sec. V-E.3 (Discussions)]: GP-MOEA tem desempenho fraco em DTLZ5, atribuído pelos autores à baixa variabilidade/informatividade das variâncias estimadas pelo GP entre diferentes pontos de amostra (as variâncias do GP quase não mudam de ponto para ponto, ao contrário das do HeE). «the ineffective uncertainty estimation of GP leads to the poor performance of GP-MOEA on some MOPs, such as DTLZ5»
- **e3** (HeE-MOEA) [Sec. V-D]: Os resultados de HV usando ExI e usando LCB são CONFLITANTES entre si em vários problemas WFG de 40D (um critério aponta vantagem do HeE-MOEA, o outro do GP-MOEA) — os autores suspeitam que o ponto de referência do HV pode não ter sido definido corretamente,… «the statistical results of HV in terms of ExI and LCB on some 40-dimensional test problems are conflicting with each other, e.g., WFG4, WFG6 and WFG8»
- **e3** (HeE-MOEA) [Sec. V-E.3 (Discussions)]: Em DTLZ7, o GP tem MSE quase zero (alta acurácia) mesmo com desvio-padrão de σ quase zero (baixa informatividade/discriminação da incerteza) — e ainda assim vence o HeE-MOEA, sugerindo que a acurácia do modelo pode compensar/dominar sobre a qualidade da… «although the standard deviation of ˆs obtained by GP on DTLZ7 is almost zero, its MSE also approaches to zero. This may explains why HeE-MOEA is outperformed by GP-MOEA on DTLZ7»
- **e4** (TSEMO) [Sec. 8.7 (Discussion of results)]: Falha do modelo por descasamento entre a hipotese de estacionariedade da GP (covariancia Matern) e a nao-estacionariedade real de 2 dos 3 objetivos de DTLZ4a, levando o TSEMO a ter o pior desempenho relativo entre os 9 problemas de teste — um caso conclusivo… «In this case two of the three functions, f2 and f3, are highly non-stationary and, hence, the GPs yield very poor predictions.»
- **e40** (SBP-BO) [Sec. IV-B-1, Table I, p.8-9]: K-RVEA e HK-RVEA batem o SBP-BO de forma significativa em DTLZ7 (frente desconexa), atribuido pelos autores ao uso de um conjunto de referencia fixo nesses dois baselines, que garante exploracao mesmo com uma frente desconexa. «both K-RVEA and HK-RVEA show significantly better performance than SBP-BO on DTLZ7.»
- **e40** (SBP-BO) [Sec. IV-B-1, p.10 (comentario sobre a Table II)]: Os proprios autores admitem que o SBP-BO pode falhar em manter boa diversidade em alguns problemas (DTLZ7, WFG9), efeito colateral de priorizar a exploracao do objetivo caro em detrimento da cobertura geral da frente. «the proposed algorithm may fail to maintain a good diversity of the obtained solutions on some test problems, such as DTLZ7 and WFG9.»
- **e40** (SBP-BO) [Sec. IV-B-4, comentario sobre a Table SVI (Supplementary…]: A ablacao do termo SBP (variante BO-AAF) mostra que sua contribuicao e pequena e piora com rc=10: SBP-BO perde em 1 e so vence 7 de 48 celulas; os autores atribuem isso a dificuldade intrinseca de medir e calibrar o grau apropriado de penalizacao de vies. «SBP-BO is worse than BO-AFF on one test instance, but it only outperforms BO-AFF on 7 out of 48 instances.»
- **e64** (SA-MOPSO (PPD)) [Sec. 3.4.1 (parágrafo final)]: O RESULTADO NEGATIVO central do artigo (citado no pedido): a função de fitness alternativa para o repositório, baseada em distância esperada (que soma variância como termo aditivo, Eq. 12), enviesa o algoritmo para exploração extrema porque pontos muito… «employing such a measure of distance in a fitness function biases the algorithm toward extreme exploration as highly uncertain points are deemed less crowded ... Employing this criterion for crowding distance…»
- **e64** (SA-MOPSO (PPD)) [Sec. 3.4.2 (antes da introdução da pseudo-variância)]: Caveat sobre o próprio mecanismo VENCEDOR (a função de fitness PD/Ni, Sec. 3.4.2): sem uma 'pseudo-variância' artificial (Eq. 15), o método perde totalmente a eficácia quando as variâncias emuladas ficam muito pequenas (perto da convergência) -- toda posição… «each position in the repository will result in Ni = 0 and therefore have an assigned fitness of 1.0, regardless of the crowding taking place.»
- **e64** (SA-MOPSO (PPD)) [Sec. 5.1.2]: Na sensibilidade a beta (limiar de confiança da PPD), valores altos demais (beta=0.80) degradam a eficiência de aprendizado do GPR e produzem 'disinformation': a exploração fica excessiva por confiar demais no modelo ainda pouco treinado, resultando em… «learning efficiency starts to deteriorate and some disinformation may happen as seen in slight increase of ℓ3 when β = 0.80. This disinformation arises from overshooting the sampling too far from the vicinity of…»
- **e64** (SA-MOPSO (PPD)) [Sec. 5.1.2]: Ainda na sensibilidade a beta, um valor intermediário (beta=0.60) também prejudicou o aprendizado nos estágios iniciais: a PPD 'desinformou levemente' o algoritmo sobre bons candidatos de infill, causando um início lento (embora corrigível com… «β = 0.60 had a slow start for GPR's learning progress as a result of PPD slightly misinforming the algorithm of good infill candidates at the early stages of the optimization.»
- **e64** (SA-MOPSO (PPD)) [Abstract]: Caveat geral (abstract/introdução) sobre o risco estrutural que motiva todo o artigo: a incerteza preditiva do surrogate pode enganar a otimização assistida, ou levando a pouca economia computacional (retreino excessivo) ou a soluções subótimas/inviáveis --… «surrogate model predictive uncertainty remains a profound challenge for MOO, as it could mislead surrogate-assisted optimization, which may result in either little computational savings from excessive retraining, or…»
- **e7** (EDN-ARMOEA) [Sec. IV-D]: GP produz estimativas de incerteza (σ) sistematicamente menos informativas (STD colapsada) que EDN e HeE em problemas de alta dimensão com poucos dados de treino — falha em expressar incerteza útil justamente no regime em que EDN-ARMOEA opera. «the mean STD of ŝ obtained by GP is the smallest, which agrees with the observations obtained in [31], [62], indicating that GP fails to properly predict the uncertainty for high-dimensional problems when the number of…»
- **e7** (EDN-ARMOEA) [Sec. III-C]: Autocrítica explícita dos autores: a EDN usada é deliberadamente simples (poucos neurônios/camadas, dado o tamanho limitado do treino), o que pode reduzir a acurácia tanto da estimativa de fitness quanto da estimativa de incerteza. «The EDN we used in this work is relatively simple, which may reduce the accuracy in fitness and uncertainty estimation.»
- **e7** (EDN-ARMOEA) [Sec. IV-B, Table I]: A estratégia de seleção proposta (balanceada, GP-ARMOEA) não domina universalmente mesmo dentro da própria ablação interna do artigo: variantes de critério único (só convergência OU só incerteza) vencem em problemas específicos, e a maioria das comparações é… «GPC-ARMOEA and GPD-ARMOEA perform best on DTLZ2 and WFG1, respectively.»
- **e7** (EDN-ARMOEA) [Sec. IV-F.3]: Não há orientação teórica para ajustar a taxa de dropout — o parâmetro central do próprio mecanismo de incerteza do EDN precisa ser sintonizado empiricamente por problema, sem garantia de generalização. «There is no theoretic guidance for setting the dropout probability, meaning that this parameter needs to be properly tuned for different problems.»
- **e74** (CLMEA) [Sec. IV-C, Table II]: Na ablação própria, a subestratégia SEM nenhum componente de distância/incerteza (CLMEA-s2, só HV) vence o CLMEA completo em 7 de 28 problemas DTLZ e empata em 1 de 20 ZDT — ou seja, adicionar os dois componentes de 'incerteza' geométrica nem sempre melhora… «CLMEA outperforms CLMEA-s1 and CLMEA-s3 on all benchmark functions, while worse than CLMEA-s2 on 7 out of 28 benchmark problems.»
- **e8** (NN-EGO) [Text S3 (S35)]: A busca guiada por E[I] concentra-se desproporcionalmente em heterociclos five-membered O-conectores (He, Hd) com baixíssima taxa de conversão para cálculos DFT bem-sucedidos, reduzindo a diversidade de funcionalizações exploradas em relação à amostragem… «In general, the E[I] algorithm substantially oversamples five-member O-connecting heterocycles He (1,3-oxathiole) and Hd (2,3-dihydro-1,3-oxazole) relative to random sampling, and this region appears to have generally…»
- **e81** (qPOTS) [Sec. 5 (Conclusion, Known limitations)]: Caveat explícito sobre a aproximação de Nyström (o mecanismo que barateia a amostragem da incerteza/posterior em alta dimensão): não existe ainda uma estratégia bem definida para controlar o trade-off custo-acurácia dessa aproximação. «however, a well-defined strategy to control the cost-accuracy tradeoff in the algorithm performance doesn’t yet exist.»
- **e86** (NSGAIII-EHVI) [Sec. III-B, p. 5 (em torno da Eq. 9 e do Algorithm 2, Steps…]: O mecanismo central do artigo (a ordenação não-dominada assistida por incerteza) é construído como uma salvaguarda explícita contra deixar a MSE do kriging dominar cegamente a seleção: no subconjunto NÃO-dominado pela PF corrente (R1), a MSE entra com sinal… «It should be noted that 𝑅𝑅2 is combined with the negative 𝑈𝑈2 value because the points in 𝑅𝑅2 with large uncertainty are desired.»
- **e9** (SUR) [Sec. 6 (Discussion)]: Caveat explícito dos autores sobre o descasamento entre a hipótese do modelo GP (tipicamente estacionariedade) e a função real: quando essa hipótese não se sustenta, a eficiência da própria estratégia de amostragem (que depende do σ do GP) é penalizada — uma… «Most models also have restrictive conditions on the approximated function (typically, stationarity), and the strategy efficiency may be greatly penalized by important inadequations between the model hypothesis and the…»
- **e9** (SUR) [Sec. 3.3 (Remark)]: O artigo endossa explicitamente um resultado da literatura (Jones, 2001) segundo o qual usar a incerteza de forma ingênua — maximizando apenas a probabilidade de melhoria p_n(x, y_n^min), que já embute σ — é ineficiente, porque ignora a amplitude do ganho… «Simply choosing points that maximize pn(x, ynmin) is known to be inefficient (Jones, 2001), as it does not consider the amplitude of the gain in the objective function.»
- **emo1** (MPoI / HypI / DomRank / MSD (4 estratégias de infill)) [Sec. 5, p. 879 (parágrafo antes da análise de tempo…]: Caveat dos autores: nos problemas mais difíceis (DTLZ1, WFG1, WFG2 — difíceis de modelar com GP e kernel estacionário), as diferenças refinadas entre as paisagens de aptidão dos diferentes critérios de infill deixam de importar porque o modelo surrogate é… «For harder problems, the subtle differences in infill fitness landscape have litle impact because of an imperfect model.»
- **f9** (UA-IBEA (sigla não-oficial, proposta por mim; paper não nomeia — "Approach 1/2/3")) [Sec. 4, p. 469]: Approach 3, que otimiza Expected Improvement por objetivo em vez de médias+sigma brutos, é uniformemente pior que as outras abordagens (frequentemente pior que Generic também) em todos os problemas, contagens de objetivos e técnicas de amostragem testadas --… «Approach 3 did not produce good results for any of the problems, objectives or sampling technique.»
- **f9** (UA-IBEA (sigla não-oficial, proposta por mim; paper não nomeia — "Approach 1/2/3")) [Sec. 4, pp. 469-470 (frase 'This is because EI tries to'…]: Os autores explicam mecanicamente a falha de Approach 3: o EI balanceia convergência e diversidade e por isso pode escolher uma solução de alta incerteza (imprecisa) só para satisfazer esse trade-off -- ou seja, o termo de incerteza pode enganar a busca. «balance between convergence and diversity. Therefore, it can select a solution with a high uncertainty for achieving its goal.»
- **f9** (UA-IBEA (sigla não-oficial, proposta por mim; paper não nomeia — "Approach 1/2/3")) [Sec. 4, p. 469]: Ressalva geral de interpretabilidade para usar incerteza como objetivo(s) extra(s): como a paisagem de aptidão dos termos de incerteza é majoritariamente desconhecida, explicar o efeito dos objetivos adicionados na otimização é difícil. «Adding uncertainties as additional objectives pose a major problem in explaining the effect of optimization as the fitness landscape of the uncertainties is mostly unknown.»
- **f9** (UA-IBEA (sigla não-oficial, proposta por mim; paper não nomeia — "Approach 1/2/3")) [Sec. 3, p. 467]: Approach 1 dobra o número de objetivos (uma média predita mais um sigma por objetivo original), o que os próprios autores notam poder aumentar a dificuldade de resolver o problema de otimização resultante -- uma ressalva estrutural/de custo dessa formulação… «We double the number of objectives which may increase the complexity of solving the resulting optimization problem.»
- **jin3** (GS-MOMA / GSM (mono: GS-SOMA)) [Sec. IV-B-2]: Nenhum SS-SOMA nem o GS-SOMA supera o SS-SOMA-Perfect (oracle sem erro) em F3 (Rosenbrock) — evidência explícita de 'curse of uncertainty' nesse problema específico. «neither SS-SOMAs nor GS-SOMA manage to outperform the SS-SOMA-Perfect on F3(Rosenbrock), suggesting the presence of 'curse of uncertainty' due to the surrogate(s).»
- **jin3** (GS-MOMA / GSM (mono: GS-SOMA)) [Sec. IV-B-1, Table XV]: Em 7 das 50 comparações da Table XV, GS-SOMA é estatisticamente pior (s-) que o baseline comparado (SS-SOMA-PR em F1, F5, F9; SS-SOMA-Perfect em F2, F3; SS-SOMA-GP em F3; SS-SOMA-RBF em F4) — o artigo reconhece essas 7 exceções à sua própria conclusão de… «On the remaining 7 cases, GS-SOMA also displays solution qualities close to that of the superior SS-SOMA, see the highlighted results in Tables V-XIV.»
- **mtm4** (MAES (variante MO: M-NSGA-II)) [Sec. V-D, p.10 (parágrafo sobre a função esfera)]: Nos problemas mais simples e bem comportados (esfera e elipsoide, convexos/unimodais, 20-D), o pré-crivo por valor médio (MI, SEM uso de incerteza) obteve o melhor desempenho médio, superando as três variantes que usam σ (LB, PoI, ExI) — a incerteza não… «The best average performance was obtained using the mean value pre-screening.»
- **pp6** (AB-MOEA) [Sec. 6 (Conclusion)]: Os próprios autores admitem, na Conclusão, que AB-MOEA converge lentamente em 3 dos 16 problemas sintéticos (DTLZ1, DTLZ3, UF6), atribuindo isso à qualidade ruim da predição do GP em paisagens muito rugosas — um caveat explícito de que o gargalo é o MODELO,… «we find that the proposed algorithm suffers from slow convergence when solving DTLZ1, DTLZ3 and UF6. This might be attributed to the poor prediction quality of GP models due to the strong ruggedness of the fitness…»

(128 passagens selecionadas por palavra-chave de incerteza/modelo; 268 no total.)

### 8.4 Equivalência de critérios / o modelo como limitante (71 passagens — todas)

- **b14** (SA²-MOEA) [Sec. 4.3 (discussão da Table 2)]: A semelhança de desempenho entre o método de incerteza proposto (rank-change) e o baseado em distância (SA²-MOEA-D) em DTLZ1 e WFG5 é atribuída explicitamente à baixa qualidade de aproximação do surrogate nesses dois problemas, não à… «it is possible that the poor approximation of the surrogate models on them caused the performance of uncertainty quantification to suffer.»
- **b14** (SA²-MOEA) [Sec. 4.4 (discussão da Fig. 3(d))]: As três variantes do otimizador híbrido (SA²-MOEA, -IBEA, -NSGA-II) convergem para desempenho parecido em WFG5; a semelhança é atribuída à má aproximação do ensemble nesse problema, não à irrelevância da escolha do otimizador. «the performance of SA2-MOEA, SA2-MOEA-IBEA, and SA2-MOEA-NSGA-II is relatively similar on WFG5... the ensemble models are poorly approximated for this problem»
- **b14** (SA²-MOEA) [Sec. 4.5 (discussão da Table 4)]: As quatro variantes da amostragem de preenchimento adaptativa (ES/LS/PC/completo) também convergem para desempenho parecido em WFG5, de novo atribuído à aproximação ineficaz do ensemble, não à indiferença do mecanismo de amostragem… «the similarity of all variants may be caused by the ineffective approximation of the ensemble models to the test problem»
- **b15** (U-RankMOEA) [Apendice G]: O artigo atribui o fraco desempenho da modelagem explicita de correlacao entre objetivos (LMC) em parte ao fato de que o mecanismo de aquisicao ja captura implicitamente trade-offs inter-objetivo via informacao condicionada a rank,… «mechanism already leverages rank-conditioned information, which captures important aspects of inter-objective trade-offs and therefore reduces the marginal utility of an explicit covariance model.»
- **b2** (MOEA/D-EGO) [Sec. VII-D-1 (Comparison)]: Em 4 das 12 instâncias (LZ08-F2, LZ08-F3, LZ08-F4 e DTLZ2), MOEA/D-EGO e ParEGO — algoritmos com estratégias de seleção/decomposição bem diferentes, mas ambos baseados em GP + expected improvement — obtêm desempenho estatisticamente… «On LZ08-F2 LZ08-F3, LZ08-F4, and DTLZ2, there is no much difference between ParEGO and MOEA/D-EGO in terms of both metrics.»
- **b2** (MOEA/D-EGO) [Sec. VII-D-1 (Comparison)]: Em KNO1 e VLMOP2, MOEA/D-EGO (seleção em lote via MOEA/D sobre EI decomposto) e SMS-EGO (seleção de 1 ponto via hipervolume/S-metric otimizado por CMA-ES) — critérios de infill conceitualmente distintos (EI decomposto vs. contribuição de… «On KNO1 and VLMOP2, Both the IGD and I−H metrics indicate that MOEA/D-EGO performs very similarly to SMS-EGO»
- **b4** (CSEA) [Sec. IV-C]: Em DTLZ2/DTLZ4 (convergência fácil, diversidade difícil), quatro dos seis métodos comparados (NSGA-III, ParEGO, CPS-MOEA, K-RVEA — com desenhos de surrogate/aquisição bem distintos entre si) atingem desempenho parecido entre si, sugerindo… «CSEA and MOEA/D-EGO have achieved the best results, and the other four compared algorithms exhibit similar performance.»
- **b7** (DR (Dual-Ranking)) [Material Suplementar, Sec. 1.3 (Optimization Results with…]: Ao explicar por que o dual-ranking não garante melhora consistente de IGD+ com o dataset de 1000 amostras (para GPR-Matérn e Autogluon-QR), os autores atribuem a causa à qualidade da ESTIMATIVA de incerteza (o modelo), não ao desenho do… «This may also be attributed to limitations in uncertainty estimation quality, which can reduce the effectiveness of dual-ranking in some cases.»
- **b9** (USeMO) [Sec. 5.1 ("Multi-objective BO algorithms")]: O artigo relata que os resultados de USeMO seguem a mesma tendência qualitativa independentemente da função de aquisição de base plugada no arcabouço (EI, TS, e implicitamente outras, com LCB detalhado à parte no Apêndice) — o desempenho… «noting that results show similar trend with other acquisition functions»
- **b9** (USeMO) [Sec. 5.2 ("USeMO vs. State-of-the-art", observação 2)]: Reforçando o ponto anterior com dados de fato mostrados (Figs. 2-3): a taxa de convergência de USeMO varia entre TS e EI, mas AMBAS as variantes superam consistentemente os métodos baseline — outra formulação da mesma equivalência… «Rate of convergence of USeMO varies with different acquisition functions (i.e., TS and EI), but both cases perform better than baseline methods.»
- **c10** (SP-RV-MOEANet) [Sec. Experiments on synthetic networks (discussão de Table…]: O desempenho (HV) de MOEA-RSFMMA (estado da arte, sem surrogate) é muito próximo ao de P-MOEANet (variante própria com paralelismo e inicialização, mas sem vetores de referência nem surrogate), sugerindo que a estratégia de avaliação… «the state-of-the-art algorithm MOEA-RSFMMA performs similarly to P-MOEANet, which indicates that the parallel evaluation strategy might not contribute substantially to the search capability.»
- **c10** (SP-RV-MOEANet) [Sec. Experiments on real-world networks (discussão de Table…]: Na rede real UAN (alta densidade de links), quase todos os algoritmos testados — exceto MOEA0 — alcançam HV satisfatório e próximo entre si; a vantagem de SP-RV-MOEANet ali vem principalmente da redução de custo computacional, não de uma… «All the tested algorithms achieve satisfactory results on UAN, except for MOEA0 which does not maintain the initial operation. Nevertheless, SP-RV-MOEANet slightly outperforms other algorithms at a…»
- **c105** (SMS-EGO) [Sec. 4 (Discussion), p. 791]: O artigo nota que SMS-EGO (baseado em hipervolume/epsilon-indicator) e ParEGO (baseado em agregacao de Tchebycheff, da mesma familia matematica do indicador R2) deveriam, por parentesco de formulacao, exibir desempenho mais parecido no… «Thus, it is particularly surprising that SMS-EGO significantly outperforms ParEGO with respect to this metric»
- **c106** (EMMI (EMmI)) [Sec. 6.2, p. 19]: No DTLZ2 sob o modelo de dependencia, CWPI-Dep e EMMI-Dep ficam com desempenho essencialmente equivalente: cada um vence em um dos dois indicadores, e as faixas (range) das 5 execucoes se sobrepoem consideravelmente -- um caso de empate… «The range of both performance measures shows considerable overlap between the two improvement criteria.»
- **c106** (EMMI (EMmI)) [Sec. 7 (Conclusions and Discussion), p. 20]: Os autores afirmam que o criterio baseado em hipervolume esperado (EIH) rende aproximacoes de Pareto competitivas com as do EMMI quando e possivel implementa-lo -- dois criterios de melhoria bem diferentes na formulacao (maximin vs.… «While the authors have found that when EIH(x) can be implemented, it produces Pareto Front approximations that are competitive with those created using EIM(x).»
- **c107** (MS-VHGP-EIHV) [Sec. II-B / III-E2]: A aproximação Gaussiana do EIHV (eq. 16) e o cálculo exato via quadratura de Gauss-Hermite (eq. 14) divergem na superfície geral, mas convergem para a mesma decisão (o maximizador) na vizinhança do ótimo — a diferença de formulação não… «the discrepancy becomes small at the neighbor of the maximum of EIHV, which implies that this approximation is sufficient for experiment planning.»
- **c107** (MS-VHGP-EIHV) [Sec. II-C]: O artigo relata, sem mostrar dados, que a métrica alternativa de seleção de modelo (log pseudo-verossimilhança, L_LOO) teria desempenho empírico semelhante ao critério LOO (a_i, p_i) proposto — dois critérios distintos para a mesma decisão… «Detailed examination on this metric compared to ours is left to our future work, but empirically, these two metrics results in similar performances.»
- **c123** (EPBII / EIPBII) [Sec. VI-A-1]: Em ZDT1-3, a diversidade das NDSs obtidas por EST (sem incerteza) e por EI (usa EI por objetivo) é igualmente pobre, mesmo com os seis critérios convergindo bem devido à alta acurácia do Kriging nesses problemas — trocar EST por EI não… «the diversity of the NDSs that are obtained by EST and EI is poor, even though all six criteria, including these two, can find suitably converging NDSs due to the high approximation accuracy of the…»
- **c123** (EPBII / EIPBII) [Sec. VI-B-3]: Em DTLZ2max3 de 4 objetivos (k=8), o EIPBII (usa incerteza via IPBI) iguala EST/EI/EHVI+EST — o mecanismo geométrico dos vetores de peso (território deixando de cruzar a PF), não a presença de incerteza na fórmula do critério, é o fator… «EIPBII has nearly the same IH and IGD as EST, EI, and EHVI+EST for the four-objective DTLZ2max3 (k = 8)»
- **c131** (MORBO) [Apendice D.1.1]: O artigo observa explicitamente que qNEHVI (usado como um dos baselines/componentes) e matematicamente equivalente a qEHVI em problemas sem ruido -- um caso textual do 'parentesco' entre criterios de aquisicao mencionado na moldura da… «We note that qNEHVI is mathematically equivalent to qEHVI on noiseless problems»
- **c131** (MORBO) [Sec. 5.2]: Na ablacao da estrategia de reinicializacao de TR (Fig. 4, Sec. 5.2), a estrategia padrao (maximizar uma escalarizacao aleatoria de hipervolume sob uma amostra da posterior) e uma estrategia MUITO mais simples (escolher o novo centro… «we find consistently strong performance for both our default HV scalarization-based re-initialization strategy and a strategy that selects a new design at random (denoted as "Random restart points")»
- **c141** (MMRAEA) [Sec. Main comparison (texto sobre Table 5)]: O artigo atribui o desempenho inferior no WFG à escolha do MODELO surrogate (regressão RBF) sendo inadequado para aquela geometria de problema, não ao critério de seleção (Q,U) em si — implicitamente sugerindo que um critério de seleção… «It can be concluded that RBFs are not suitable for approximating the objective functions of the WFG problems, and the SVM classifiers perform well on them.»
- **c141** (MMRAEA) [Sec. Main comparison (texto após Table 6)]: No WFG (36 instâncias), apesar de motores/surrogates distintos (RBF tri-modo+incerteza do MMRAEA vs. classificador SVM do MCEA/D), o teste de Friedman marca empate estatístico ('≈') em 23/36 instâncias — maioria dos casos é indistinguível… «achieves similar performance when compared with the recently proposed MCEA/D on most of the WFG problems, i.e, 23 instances out of 36.»
- **c154** (JES) [Sec. 2, Proposição 1]: JES é formalmente uma cota superior a qualquer combinação convexa de PES e MES (Proposição 1) — um resultado teórico de parentesco entre os três critérios informacionais, não uma coincidência empírica. «The JES is an upper bound to any convex combination of the PES and MES acquisition functions»
- **c154** (JES) [Sec. 5.2, referenciando Apêndice L.6]: As 4 formas de aproximar a entropia condicional (estimador zero-variância, cota inferior com covariância completa, cota inferior diagonal, Monte Carlo) rendem desempenho de otimização parecido na maioria dos casos, tanto para JES quanto… «we observed that in the majority of cases all the estimates exhibit similar performance»
- **c154** (JES) [Apêndice L.7]: Entre os baselines de melhoria, ignorar ou modelar o ruído de observação (ParEGO vs NParEGO; EHVI vs NEHVI) rende desempenho aproximadamente equivalente — mais uma instância de critérios/variantes distintas convergindo para desempenho… «the greedier strategy which ignores the noise seems to perform reasonably well compared to the strategy which accounts for the noise»
- **c222** (MESMO) [Sec. 5.1]: O artigo justifica a exclusão do baseline PAL da bateria comparativa porque, segundo a literatura citada, PAL (que classifica pontos em Pareto-ótimo/não-ótimo/incerto) tem desempenho similar ao de SMSego (que otimiza hipervolume sobre as… «We did not include PAL [31] as it is known to have similar performance as SMSego [7] and works only for finite discrete input space.»
- **c238** (EIM) [Sec. VI-A]: Não há diferença estatisticamente significativa entre o critério maximin exato (EIm) e sua versão EIM (EIMm), nem entre o hipervolume exato (EIh) e sua versão EIM (EIMh), nos três problemas ZDT — a formulação fechada e barata (EIM) entrega… «No significant difference is detected between the EIm criterion and the EIMm criterion, and between the EIh criterion and the EIMh criterion at the significant level of α = 0.05.»
- **c238** (EIM) [Sec. VI-C]: No problema DTLZ5 (3 objetivos), a eficiência do EIMm é descrita como similar à do EIm exato. «The efficiency of the EIMm criterion is similar to the EIm criterion on the 3-objective DTLZ5 test problem.»
- **c238** (EIM) [Sec. VI-A]: Resumo geral da suíte ZDT: as versões EIM de 2 objetivos têm desempenho competitivo com as versões EI de 2 objetivos — a barateza computacional da EIM (A7) não custa desempenho perceptível na maioria dos casos (exceção: EIe, que já era… «Overall, the 2-objective EIM criteria have competitive performances compared with the 2-objective EI criteria on the three ZDT test problems.»
- **c24** (DTK-MODE) [Sec. IV-B, Table III]: O MODE (mesmo motor/critério de seleção) atinge desempenho cada vez mais próximo do MODE-FEA-direto à medida que a precisão do surrogate (DTK) aumenta com mais pontos de amostragem — sugerindo que é a qualidade do modelo, e não o… «The proposed algorithm gives the extreme solutions approaching to those from the FEA combined MODE as the number of sampling points increases.»
- **c241** (EMMOEA) [Sec. I (Introdução, parágrafo sobre a 1ª categoria de…]: O artigo argumenta que, na 1ª categoria de critérios de infill (escalarização mono-objetivo), a estimativa de incerteza do GP já é pouco confiável com poucos dados de treino, e esse problema piora com o crescimento do nº de objetivos… «This problem may become even worse as the number of objectives increases in many-objective optimization since the error in estimating the uncertainty information and the objective values may…»
- **c241** (EMMOEA) [Sec. I (Introdução, parágrafo sobre a 2ª categoria de…]: Para a 2ª categoria de critérios de infill (escolhem entre candidatos já filtrados pelos surrogates dos objetivos), o artigo afirma que erros tanto na incerteza quanto no valor aproximado dos objetivos podem induzir à escolha errada de… «errors in estimating the uncertainty information and the objective values may mislead the selection of the right solutions for expensive evaluations.»
- **c241** (EMMOEA) [Sec. I (Contribuições, item 1)]: Como justificativa de projeto, os autores afirmam que separar a busca de candidatos (nos GPs dos objetivos) da gestão do surrogate (GP do indicador + EI) evita que a gestão seja influenciada pela PROPAGAÇÃO de erros na aproximação dos… «surrogate management can be directly carried out without being influenced by the propagation of the errors in approximating multiple objective functions and in estimating the uncertainty levels of…»
- **c250** (K-MOGA) [Sec. 3.2, p. 031401-3 a 031401-4]: O artigo testa variar o multiplicador de confianca do gate de restricoes (1x, 2x padrao, 3x o desvio-padrao do Kriging, Eq. 13) e relata que o desempenho de K-MOGA em numero de chamadas de simulacao nao muda significativamente - o valor… «We have observed that by using a different setting, e.g., one or three times instead of two times sj as in Eq. (13), the performance of K-MOGA does not change significantly in terms of the number of…»
- **c261** (DirHV-EGO) [Sec. V-C, p.9]: ADirHV-EI (a média do DirHV-EI sobre os vetores de direção, provada na Proposição 3 como uma hipervolume improvement ponderada) tem desempenho semelhante ao EHVI padrão em mais da metade dos problemas testados, confirmando empiricamente a… «ADirHV-EI, i.e. the mean of DirHV-EI with respect to Pλ, performs similarly to EHVI on 7 out of 12 test problems.»
- **c261** (DirHV-EGO) [Supplementary Sec. IV-B, p.10]: Quando o método de seleção de lote é igualado (k-means em ambos), DirHV-EGO-K (usa o critério DirHV-EI) e MOEA/D-EGO (usa o critério ETI, com z* adaptativo) têm desempenho semelhante na maioria dos problemas — evidência de que boa parte da… «DirHV-EGO-K performs similarly with MOEA/D-EGO on 8 out of 12 test problems.»
- **c261** (DirHV-EGO) [Supplementary Sec. I-C.2, p.4]: Prova teórica de que o critério de probabilidade de melhoria (PI) induzido por IT (Tchebycheff) e por ID (direction-based hypervolume) são EXATAMENTE equivalentes como eventos de probabilidade (P(IT>0)=P(ID>0)), mas suas ESPERANÇAS (os… «the probability of improvement (PI) criteria induced by IT (y|λ) and ID(y|λ) are equivalent... However, their expectations... are not equivalent.»
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF)) [Sec. 5.1]: NEHVI reduz-se EXATAMENTE a EHVI no caso sem ruido -- nao e coincidencia empirica, e uma equivalencia matematica direta da formulacao (a integral sobre a incerteza da fronteira de Pareto colapsa quando nao ha ruido nas observacoes). «in noiseless environments, NEHVI is equivalent to EHVI»
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF)) [Apendice H.7]: Confirmacao empirica da equivalencia acima: em benchmarks SEM ruido injetado, qNEHVI tem desempenho equivalente/competitivo (nao superior) ao par qEHVI/qEHVI-PM-CBD -- a vantagem de qNEHVI so aparece quando ha ruido; sem ruido, os… «Figure 15 shows that qNEHVI performs competitively with qEHVI(-PM-CBD) and outperforms DGEMO, TS-TCH and qNParEGO across all benchmark problems.»
- **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF)) [Apendice C.2]: A formulacao CBD (cached box decompositions) e a formulacao IEP (inclusion-exclusion principle) para calcular qNEHVI/qEHVI sao matematicamente EXATAMENTE equivalentes (mesmo valor de aquisicao para o mesmo conjunto de candidatos, via… «using the method of common random numbers, the CBD formulation is mathematically equivalent to IEP formulation, but the computing qNEHVI with the CBD trick is much more efficient»
- **c59** (UA-DBO) [Sec. 4.1.2, p. 14]: O GS-ED (mecanismo de incerteza proposto, um único modelo com amostragem Monte Carlo barata) e o deep ensemble tradicional (caro, múltiplos modelos independentes treinados do zero) alcançam qualidade de calibração comparável, apesar de… «Overall, GS-ED and deep ensembles demonstrate comparable capability in estimating predictive uncertainty, with all models achieving good calibration.»
- **c65** (SABBa) [Sec. 3.2, Table 1]: As duas formulações da Probabilidade de Otimalidade de Pareto — POPtrue (exata, combinatorial) e POPmin (a aproximação barata proposta) — produzem rankings/scores muito parecidos nos dois exemplos ilustrativos testados, justificando a… «POPmin and POPtrue metrics are quantitatively compared in Table 1 on the two small examples depicted in Figure 2, and show very similar scoring.»
- **c65** (SABBa) [Sec. 4.4]: Os autores relacionam explicitamente suas variantes SABBa (formuladas via Bounding-Box/POP) com as formulações 3 e 4 de Eldred et al. [24] — uma equivalência conceitual entre diferentes formulações de otimização sob incerteza assistida por… «Parallels can be made between these strategies and formulations 3 and 4 from [24].»
- **c71** (SAEA/ME) [Sec. 2.2]: Passagem das Preliminares (não um resultado empírico do próprio artigo) observando que as três funções de aquisição clássicas (PI, EI, UCB) são, estruturalmente, formas agregadas de combinar a média e a variância preditas pelo GP —… «all these acquisition functions are designed as a combination of the predicted mean and its associated variance»
- **c75** (MO-EI/PI (Keane)) [Multiobjective Example 2, final da discussão, antes de…]: Com base nos dois exemplos multiobjetivo, o artigo conclui explicitamente que a escolha precisa entre as seis formulações de critério introduzidas (P[I]aug, P[I]dom, P[I]avg, E[I]aug, E[I]dom, E[I]avg) não é crucial para o resultado,… «Based on these results and those from the first example, it would appear that the precise choice of improvement metric is not crucial but should reflect the stability of the analysis tool,...»
- **c75** (MO-EI/PI (Keane)) [Multiobjective Example 1, discussão após a Fig. 12 (p. 889)]: No Exemplo MOO 1 (viga de Norwacki), o artigo afirma que todas as métricas de melhoria introduzidas (as seis variantes de P[I]/E[I]) tendem a superar de forma semelhante a NSGA-ii aplicada diretamente ao krig sob o mesmo orçamento — ou… «In fact, all of the improvement metrics introduced here are generally better than those achieved by simply applying NSGA-ii to the krig models directly, using the same number of function evaluations…»
- **c81** (UA-MORL-Diff) [Table 2]: Dentro da ablação (Tabela 2, QM9), o método PFM (Penalty Function Method, constraint-based, SEM uso de incerteza preditiva) atinge um VUN praticamente empatado com 'Ours' (incerteza-consciente) — 88,75±0,78 vs. 88,90±0,68 — embora 'Ours'… «PFM: VUN 88.75 ± 0.78; Ours: VUN 88.90 ± 0.68 (Table 2).»
- **c82** (TC-SAEA) [Sec. 4.4 (discussão da Table 3)]: Comparando dois mecanismos distintos de transferência de conhecimento entre o objetivo rápido e o lento — o co-surrogate GP + seleção por intervalo de confiança (TC-SAEA) contra a adaptação de domínio + co-training (Tr-SAEA, antecessor dos… «Although TC-SAEA and Tr-SAEA show similar performance on most test instances, it should be noted that TC-SAEA outperforms Tr-SAEA on DTLZ1 and DTLZ3.»
- **c91** (EHVIMOPSO) [Sec. 1 (Introducao)]: Passagem de contextualização da Introdução (não um teste empírico do próprio artigo) observando que o EHVI é estruturalmente uma alternativa de agregação à abordagem mais antiga de tratar cada EI por objetivo como um objetivo separado do… «which updates surrogate model using a single criterion rather than giving many EIs as the objective functions»
- **c97** (EnGP-MRO) [Sec. 6.4 [47]]: Quando o ensemble tem membros suficientes (30) para caracterizar bem a incerteza do surrogate, a abordagem de múltiplas realizações (que empilha os N surrogates como restrições) passa a impor uma restrição tão rígida quanto a abordagem… «the constraints imposed by stochastic optimization using multiple realization is as rigid as the chance constraints when the number of surrogate models in the ensemble is large enough to quantify the…»
- **c97** (EnGP-MRO) [Sec. 6.4, final]: Reforçando o achado anterior, o artigo generaliza que a equivalência entre múltiplas realizações e chance-constrained se mantém para outros níveis de confiabilidade também, desde que o ensemble seja suficientemente grande — a diferença de… «With a sufficiently large number of models in the ensemble, the multiple-realization approach performs similar to the chance-constrained optimization approach.»
- **e1** (EMO) [Abstract; Sec. 4.3, Table 2]: O critério Phv — mais barato porque move a variância prevista para FORA da função de melhoria (mantendo-a só na parte de probabilidade P[I]) — iguala ou supera o critério EIhv — mais caro, que integra a variância DENTRO da melhoria de… «a new statistical criterion is proposed, based on the hypervolume-based EI, which is significantly cheaper to compute while still delivering promising results»
- **e102** (MOEA/D-ASS) [Sec. V-C]: No problema WFG8, o desempenho do MOEA/D-ASS (usando ALCB) e do K-RVEA (que usa outro mecanismo de seleção, guiado por vetores de referência e incerteza) é estatisticamente indistinguível, apesar de o MOEA/D-ASS ser nominalmente… «On WFG8, MOEA/D-ASS is slightly worse than K-RVEA. Nevertheless, the statistical significance tests indicate that the performance differences between the two algorithms are not remarkable on WFG8.»
- **e103** (IBEA-MS) [Sec. V (Conclusion)]: Ao discutir limitações, o artigo admite que o gargalo de desempenho pode estar no MODELO disponível (Kriging e RBFN, ambos potencialmente inadequados) e não no critério/mecanismo que arbitra entre eles — eco direto do padrão 'modelo… «it is likely that neither the Kriging nor the RBFN model can guide the population toward the optimal solution set»
- **e104** (RVMM) [Sec. IV-C (discussão da Fig. 6)]: O artigo observa que K-RVEA e KTA2 já incorporam convergência e diversidade no desenho da própria função de aquisição, mas ainda assim produzem frentes mal espalhadas em MaF1 (invertido) e MaF7 (descontínuo); os autores concluem que o… «the balance of exploration and exploitation of multiobjectives of the search process is also vital in order to achieve a set of well-converged and well-diversified solutions.»
- **e16** (EGBO) [Sec. Synthetic studies (discussão da Fig. 4c)]: Em MW7 (n=8), qNEHVI-BO (aquisição de hipervolume) e qNParEGO (aquisição por escalarização/ParEGO) atingem valores de não-uniformidade (NU) próximos entre si, apesar de mecanismos de aquisição teoricamente distintos (hipervolume vs.… «qNEHVI-BO has a NU metric close to qNParEGO and EGBO lies between qNEHVI-BO and U-NSGA-III.»
- **e16** (EGBO) [Sec. Further discussion; detalhes em Supplementary…]: Substituir o componente evolutivo U-NSGA-III por MOEA/D-IEpsilon dentro do framework EGBO produz desempenho comparável em múltiplos problemas sintéticos — sugerindo que o mecanismo específico do EA importa menos que o princípio de combinar… «we observed comparable performance using either U-NSGA-III or MOEA/D-IEpsilon in EGBO framework across multiple synthetic problems.»
- **e17** (MOBO) [Sec. III-B]: O artigo argumenta que UCB-HVI e EHVI atingem desempenho de otimizacao similar, mas UCB-HVI e muito mais barato computacionalmente quando ha muitos objetivos (P>3); por isso os autores optam por usar exclusivamente UCB-HVI no restante do… «The use of these advanced algorithms allows UCB-HVI to be a much faster calculation than EHVI when the number of objectives is large (P > 3), while still achieving similar optimization performance.»
- **e21** (PIO) [Discussion (primeiro parágrafo)]: O artigo cita trabalho anterior (Fromer/Graff/Coley; Graff et al.) segundo o qual, em cenários de virtual screening sobre bibliotecas bem definidas, funções de aquisição AGNÓSTICAS à incerteza podem igualar ou até superar abordagens de… «Previous research has indicated that in virtual screening settings, uncertainty-agnostic acquisition functions can exhibit surprisingly equivalent or even superior performance compared to…»
- **e21** (PIO) [Results, 'Optimization results of single-objective task']: Ao discutir a falha na tarefa de mestranol, o artigo atribui a limitação ao MODELO (não ao critério de aquisição/seleção): mesmo um modelo bem calibrado no conjunto de teste pode falhar em generalizar durante a otimização sobre um espaço… «even well-calibrated models may struggle to generalize accurately during molecular optimization over an extensive chemical space, leading to unreliable predictions not only for mean values but also…»
- **e3** (HeE-MOEA) [Sec. V-E.3 (Discussions)]: O artigo atribui a divergência de desempenho entre HeE-MOEA e GP-MOEA à qualidade do MODELO (acurácia da média e informatividade da variância) mais do que ao critério de infill em si (ExI/LCB são usados igualmente por ambos) — se os dois… «Theoretically, if the heterogeneous ensemble (HeE) can estimate the fitness and uncertainty information exactly as the GP, the final optimization results should be very similar»
- **e40** (SBP-BO) [Sec. IV-B-4, comentario sobre Table VI/SVI, p.13]: A remocao do termo de penalizacao SBP (variante BO-AAF, que mantem a funcao de aquisicao adaptativa AFA baseada em media e sigma do GP) produz desempenho estatisticamente equivalente ao SBP-BO completo na maioria das 48 celulas testadas -… «since it is highly tricky to measure the search bias, it is challenging to apply an appropriate degree of penalty. This is might be the reason why SBP-BO and BO-AAF show similar performance on most…»
- **e64** (SA-MOPSO (PPD)) [Sec. 5.2.1]: Ao justificar por que lambda_m deve ser < 0,50 (tolerando alguma violação de restrição emulada em vez de trata-la deterministicamente), os autores reconhecem explicitamente que o MODELO (não o critério/threshold em si) e a fonte de… «This relaxation is in line with the idea of handling constraints through probability of feasibility ... because we recognize that surrogate model predictions are imperfect.»
- **e7** (EDN-ARMOEA) [Sec. IV-B, Table I]: Na ablação de Table I (16 instâncias), a maioria das comparações entre a estratégia balanceada (GP-ARMOEA) e as variantes de critério único (GPC-ARMOEA: só convergência; GPD-ARMOEA: só incerteza) é estatisticamente EMPATADA — 10 de 16… «+/−/≈ ... 5/1/10 ... 8/1/7 (linha final da Table I)»
- **e74** (CLMEA) [Sec. IV-C, Table II]: Na ablação (Table II, 28 problemas DTLZ bi-objetivo), a subestratégia puramente exploitativa (CLMEA-s2, HV-based, sem incerteza) e o CLMEA completo (que combina HV + duas subestratégias de incerteza geométrica) produzem resultado… «worse than CLMEA-s2 on 7 out of 28 benchmark problems»
- **emo1** (MPoI / HypI / DomRank / MSD (4 estratégias de infill)) [Sec. 5, p. 879 (parágrafo final antes de 'We also…]: Passagem central de equivalência (motivo do apontamento especial para este artigo): em problemas mais difíceis de modelar com GP e kernel estacionário (DTLZ1, WFG1, WFG2), as diferenças sutis entre as paisagens de aptidão dos vários… «For harder problems, the subtle differences in infill fitness landscape have litle impact because of an imperfect model. As such, the methods presented here are mostly equivalent.»
- **emo1** (MPoI / HypI / DomRank / MSD (4 estratégias de infill)) [Sec. 6 Conclusions, p. 880]: Achado de fechamento (Conclusões): em metade dos problemas de teste, as quatro estratégias de infill propostas (mais baratas) têm desempenho tão bom quanto o SMS-EGO (mais caro), apesar de usarem a incerteza do GP de formas algebricamente… «Te proposed fast infill strategies perform as well as SMSEGO in half of the test problems presented here, while outperforming ParEGO.»
- **f9** (UA-IBEA (sigla não-oficial, proposta por mim; paper não nomeia — "Approach 1/2/3")) [Sec. 4, pp. 469-470]: Mesmo quando o dataset offline inicial já contém muitos pontos quase-ótimos (não-dominados), sob amostragem optimal-random, a abordagem Generic (sem incerteza) ainda falha em produzir boas soluções; os autores atribuem isso ao modelo… «This is because the surrogate models do not provide a perfect representation of the true objectives.»
- **mtm4** (MAES (variante MO: M-NSGA-II)) [Sec. IV-A (fim), p.7]: Os autores provam uma equivalência formal entre versões dos critérios de pré-crivo: uma versão de limiar (threshold τ) do PoI equivale a um pré-crivo LB com um ω tal que τ=Φ(−ω); em particular, o limiar PoI com τ=0.5 é formalmente… «It turns out, that this strategy is equivalent to a LB pre-screening using a value of ω such that τ = Φ(−ω). In particular, a threshold version of the PoI pre-screening with τ = 0.5 is formally…»
- **mtm4** (MAES (variante MO: M-NSGA-II)) [Sec. V-F (Discussion of results on constrained…]: No problema restrito e multimodal de Keane, as diferenças de desempenho entre os três critérios que usam informação de confiança (limite inferior, PoI e ExI) foram pouco significativas entre si — sugerindo que, uma vez que se usa ALGUMA… «The differences between the three pre-screening criteria that use confidence information (lower bound, PoI and ExI) are less significant for this problem.»

### 8.5 Característica do problema × desempenho: 283 afirmações, por característica (normalizada por palavra-chave; texto completo no companheiro, §D)

| Característica | Afirmações | Artigos |
|---|---|---|
| ruído | 6 | b14, c107, c154, c262, c81, e21 |
| correlação entre objetivos | 3 | c82, e21, e40 |
| restrições / factibilidade | 13 | b7, c131, c65, c75, c97, e16, e64, mtm4 |
| muitos objetivos (M) | 35 | b13, b14, b3, b4, b5, b9, c1, c100, c105, c106, c122, c123, c131, c141, c154, c217, c222, c238, c241, c261, c262, c48, c49, c71, c81, e1, e103, e17, e64, e7, emo1 |
| alta dimensão (D) | 48 | b1, b13, b15, b3, b4, b9, c1, c10, c107, c131, c141, c149, c154, c214, c238, c261, c262, c267, c276, c29, c65, c71, e1, e103, e104, e3, e4, e40, e7, e74, e86, e9, emo1, jin3, mtm4 |
| frente desconexa | 38 | b1, b13, b14, b3, b4, b5, b8, c1, c122, c123, c141, c217, c238, c241, c250, c267, c29, c71, e102, e104, e16, e3, e4, e40, e64, e7, e74, e81, e86, e9, emo1, mtm4, pp6 |
| frente degenerada / irregular | 11 | b4, b8, c141, c217, c48, e104, e3, f9, mtm4 |
| multimodalidade / ótimos locais / enganoso | 36 | b13, b14, b2, b3, b4, b8, c105, c122, c123, c141, c217, c24, c261, c267, c29, c48, c71, e102, e103, e104, e3, e40, e86, emo1, jin3, mtm4, pp6 |
| não separabilidade | 12 | b14, b8, c106, c123, c141, e104, f9 |
| geometria da frente (côncava/convexa/mista) | 16 | b14, b4, b8, c1, c105, c123, c149, c214, c241, c261, c59, c91, e16, e86 |
| densidade enviesada / cobertura | 23 | b1, b2, c10, c105, c122, c141, c276, c48, c65, c71, c81, c82, e102, e16, e21, e3, e4, e74, pp6, wang4 |
| orçamento / dados iniciais / DoE | 4 | b7, b8, c107, e4 |
| problema real / domínio | 6 | c1, c123, e104, e74, e8, e9 |
| outra | 32 | b14, b15, b7, c107, c123, c154, c217, c241, c250, c267, c29, c48, c50, c59, c65, c75, c81, c82, c97, e104, e17, e4, e40, e81, e86, jin3 |

Amostra de afirmações (uma por artigo e característica, as primeiras 60 pelo índice):

- [ruído] **b14** (SA²-MOEA) [Sec. 2.2.2]: IBEA (seleção por indicador) tolera melhor o ruído e converge melhor sob ruído não-nulo; NSGA-II (dominância+crowding) mantém melhor diversidade em todos os níveis de ruído testados - motivando a hibridização dos dois… «IBEA has better convergence and noise tolerance compared to NSGA-II.»
- [ruído] **c107** (MS-VHGP-EIHV) [Sec. IV]: Quanto maior o movimento do robô, maior o nível de ruído nas medições — heterocedasticidade fisicamente motivada a priori e depois confirmada estatisticamente (Tabela II, teste F a 1%). «it is appropriate to consider that the larger the movement, the greater the noise level.»
- [ruído] **c154** (JES) [Apêndice L.4]: O desempenho de todas as variantes de JES/MES piora monotonicamente com o ruído crescente; a estimativa que assume ruído zero (JES-0/MES-0) degrada mais rápido que as demais. «we observe that the performance decreases as the noise levels increases»
- [ruído] **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF)) [Apendice H.6, Fig. 14]: qNEHVI mantem desempenho superior consistente em toda a faixa testada (1% a 20%, com discussao estendendo a 30%) -- muito alem do 1% tipicamente testado em trabalhos anteriores; qNEHVI-1 (aproximacao de amostra unica)… «qNEHVI-1 achieves the best final hypervolume when the noise standard deviation sigma is less than 15% of the range of each objective, but performs worse than…»
- [ruído] **c81** (UA-MORL-Diff) [Sec. 4.2.1]: o surrogate é sistematicamente menos acurado para o objetivo mais ruidoso/caro (afinidade via docking, R²=0,86–0,88) do que para os objetivos de fórmula fechada (QED/SAS, R²=0,95–0,99) — a incerteza epistêmica reportada… «R² values of 0.95–0.99 for QED and SAS, and 0.86–0.88 for binding affinity.»
- [ruído] **e21** (PIO) [Results, 'Surrogate model and UQ performance']: A natureza não-determinística dos procedimentos computacionais usados para gerar os dados do Tartarus (amostragem de confôrmeros, sítios de docking, otimização de geometria) introduz ruído nos valores de propriedade,… «These challenges in model training may be partly attributed to data noise inherent in the property values, a consequence of the non-deterministic computational…»
- [correlação entre objetivos] **c82** (TC-SAEA) [Sec. 4.6, Table 6]: TC-SAEA tem o melhor desempenho quando há correlação positiva OU negativa entre os objetivos (não nula); com corr=1 (correlação perfeita) todos os métodos com surrogate atingem IGD≈0,00 (problema trivial); Waiting (sem… «TC-SAEA exhibits the best performance on the cm-OneMax problem when there is a positive or negative correlation between the objectives, and HK-RVEA is the…»
- [correlação entre objetivos] **e21** (PIO) [Results, 'Optimization results of multi-objective…]: Há correlação positiva moderada entre os dois objetivos do problema de emissores orgânicos multiobjetivo, o que dificulta a otimização por criar direções conflitantes (minimizar o gap enquanto maximiza a força do… «there is a moderate positive correlation between the singlet-triplet gap and oscillator strength (Supplementary Fig. S24), complicating the task, which demands…»
- [correlação entre objetivos] **e40** (SBP-BO) [Sec. IV-B-3, p.12]: Metodos de transfer learning exploram a correlacao entre fc e fe para estimar o objetivo caro a partir da busca no barato, o que os faz superar o SBP-BO na maioria dos problemas bi-objetivo; o SBP-BO nao usa essa… «information on the correlation of the two objectives is acquired, which allows for an estimation of the expensive objective from the search experience on the…»
- [restrições / factibilidade] **b7** (DR (Dual-Ranking)) [Material Suplementar, Sec. 1.3 (Ablation Study…]: Dentre os 11 problemas da ablação, os 3 restringidos (BNH, Truss2D, Welded Beam) são os que mais se beneficiam do dual-ranking - MSE e IGD+ consistentemente reduzidos e HV melhorado, mais do que a média dos problemas… «In particular, constrained benchmarks benefit the most from the dual-ranking strategy, where MSE and IGD+ are consistently reduced while HV is improved.»
- [restrições / factibilidade] **c131** (MORBO) [Sec. 5.1 ('Mazda vehicle design problem')]: Mesmo o piso quase-aleatorio (Sobol) tem dificuldade de permanecer factivel apos o ponto inicial dado a todos os metodos, ilustrando o quao dificil e satisfazer 54 restricoes simultaneas por amostragem cega; MORBO, por… «in subsequent evaluations Sobol did not find another feasible design, illustrating the challenge of satisfying the 54 constraints»
- [restrições / factibilidade] **c65** (SABBa) [Sec. 6.1]: quando o objetivo é quase constante em relação a uma restrição, a solução final fica levemente fora do valor ótimo exato nessa coordenada, por haver pouca informação de gradiente para refinar precisamente naquela… «the second constraint c2 is slightly off its optimal value 0 because the objective value V is nearly constant w.r.t. c2, as can be observed in Figure 11(b).»
- [restrições / factibilidade] **c75** (MO-EI/PI (Keane)) [Multiobjective Example 1, discussão após a Fig.…]: Tanto a NSGA-ii direta quanto a NSGA-ii+krig falham em identificar as extremidades verdadeiras da frente de Pareto (conhecidas analiticamente) na viga de Norwacki, enquanto todas as execuções do critério E[I] as… «Notice also that both the direct and krig-based variants of NSGA-ii fail to identify the true ends of the front, whereas all runs of the E[I] metric identify…»
- [restrições / factibilidade] **c97** (EnGP-MRO) [Sec. 6.3 [44]]: Como a maioria das soluções ótimas do problema de bombeamento é do tipo 'estado-limite' (na fronteira das restrições de salinidade), mesmo um pequeno erro do surrogate pode empurrar a solução para a região inviável… «Since most of the optimal solutions are limit state designs, i.e., optimal solution lying on the constraint bounds, the uncertainty in the surrogate model…»
- [restrições / factibilidade] **e16** (EGBO) [Sec. Synthetic studies (discussão da Fig. 4c)]: A pressão de seleção evolutiva preserva e transfere a viabilidade dos pais para os filhos via crossover, fazendo a violação da restrição distante da PF (c1) convergir rapidamente a zero; já a restrição que intersecta a… «as selection pressure preserves and transfers parent feasibility to the children via crossover, EGBO candidates are more likely to evolve within the feasible…»
- [restrições / factibilidade] **e64** (SA-MOPSO (PPD)) [Sec. 5.1.3]: Em OSY (6 restrições emuladas), tratar as restrições de forma próxima ao determinístico (lambda_m=0,50) impede cobrir toda a frente verdadeira; tolerar mais violação emulada (lambda_m menor, ótimo em 0,25) permite… «P after four outer iterations did not fully span the true front, even when continued for a few more iterations»
- [restrições / factibilidade] **mtm4** (MAES (variante MO: M-NSGA-II)) [Sec. V-F, p.11]: Qualquer estratégia assistida por metamodelo supera significativamente a EA correspondente sem metamodelo; e estratégias que usam informação de confiança superam claramente a que usa só o valor predito — o ganho da… «any metamodel assisted strategy performs significantly better than the corresponding EA without metamodel assistance. Second, strategies using the confidence…»
- [muitos objetivos (M)] **b13** (AdaMoR-DDMOEA) [Sec. 5.4]: BDDEA-LDG, desenhado para problemas mono-objetivo, degrada à medida que o número de objetivos aumenta. «Due to its special design for single-objective problems, BDDEA-LDG performs poorly when the number of objectives increases.»
- [muitos objetivos (M)] **b14** (SA²-MOEA) [Sec. 4.6.1 (discussão do DTLZ2)]: O aumento do número de variáveis de decisão degrada a maioria dos algoritmos comparados no DTLZ2, tornando-os incapazes de identificar corretamente a demanda do estágio de otimização atual - um efeito atribuído aos… «the increasing number of decision variables causes it be unable to accurately determine the current optimization demand.»
- [muitos objetivos (M)] **b3** (K-RVEA) [Sec. IV-A, final]: Para um n fixo, aumentar k torna o problema mais FÁCIL (não mais difícil), porque menos variáveis de decisão restam para 'dirigir' a convergência à medida que mais objetivos particionam o mesmo espaço de busca — um… «the landscape of the problems is getting easier as the number of objectives increases. This is due to the fact that the number of decision variables for…»
- [muitos objetivos (M)] **b4** (CSEA) [Sec. III-D]: A fração real de soluções de categoria II (rr) cresce com o número de objetivos (mais desbalanceamento), mas, contraintuitivamente, a acurácia de predição do classificador FNN (proximidade entre rp e rr) na verdade… «the class imbalance in data becomes worse as the number of objectives increases (rr increases), and the FNN with data partition can achieve a satisfactory…»
- [muitos objetivos (M)] **b5** (Prob-RVEA / Prob-MOEA/D (+ Hyb-RVEA / Hyb-MOEA/D)) [Sec. I]: MOEAs tradicionais baseados em dominância degradam com o aumento do número de objetivos; por isso os autores escolhem, como motor, MOEAs baseados em decomposição (RVEA, MOEA/D), que lidam explicitamente com muitos… «the performance of traditional MOEAs, such as MOGA [10], MO-CMA-ES [11], NSGA-II [12], etc., deteriorates when the number of objectives increases [13]–[15].»
- [muitos objetivos (M)] **b9** (USeMO) [Sec. 5.2 ("Comparison of acquisition function…]: O tempo de otimização da função de aquisição de PESMO e de SMSego cresce significativamente conforme o número de objetivos k passa de 2, enquanto USeMO e ParEGO escalam bem (Tabela 2) — uma caracterização de custo… «The time for PESMO and SMSego increases significantly as the number of objectives grow beyond two.»
- [muitos objetivos (M)] **c1** (BS-MOBO) [Sec. IV-B (texto antes da Table II)]: HIGA-MO (piso sem surrogate baseado em gradiente do indicador de hipervolume) só resolve problemas biobjetivo; fica indisponível ('NA') nos 7 problemas de 3 objetivos da bateria de 50D (DTLZ1, DTLZ2, F4, F8, UF8, UF9,… «The gradient-based HIGA-MO method is now only suitable for solving bi-objective problems, so its results on three objective problems are unavailable.»
- [muitos objetivos (M)] **c100** (qEHVI) [Sec. 6 (Discussion)]: qEHVI tem escalabilidade limitada pelo algoritmo de decomposição em caixas usado para computar hipervolume, o que impede seu uso em espaços de objetivos de alta dimensão sem recorrer a uma decomposição aproximada… «Another limitation of qEHVI is that its scalability is limited the partitioning algorithm, precluding its use in high-dimensional objective spaces.»
- [muitos objetivos (M)] **c105** (SMS-EGO) [Sec. 4 (Discussion), p. 791]: Nos problemas com mais de dois objetivos, SMS-EGO lida melhor com o aumento da dimensao do espaco de objetivos que ParEGO e Jeong, evidenciado nos boxplots de distancia media a frente de Pareto para DTLZ2 com 5… «the results on the test functions, which feature more than two objectives, show that SMS-EGO copes best to increasing objective dimensions.»
- [muitos objetivos (M)] **c106** (EMMI (EMmI)) [Sec. 6.2 (DTLZ2 Function), p. 18]: Com m=4, os metodos de comparacao grafica/visual das aproximacoes de Pareto deixam de ser viaveis, restando so os indicadores numericos (hipervolume e epsilon aditivo); e o numero de parametros de covariancia do modelo… «In this m = 4 dimensional example, graphical methods are problematic to evaluate»
- [muitos objetivos (M)] **c122** (θ-DEA-DP) [Sec. IV-C]: Com m=8, o piso θ-DEA (sem preselecão via surrogate) torna-se estatisticamente comparável ao assistido em 2/6 problemas — o único momento em que o piso alcança paridade estatística em toda a bateria; atribuído à… «θ-DEA becomes competitive to all surrogate-assisted algorithms including θ-DEA-DP in the eight-objective case.»
- [muitos objetivos (M)] **c123** (EPBII / EIPBII) [Sec. VI-D]: Para problemas com mais de dois objetivos, o uso do EPBII é preferível ao EIPBII, pois obtém NDSs diversos de forma robusta até quatro objetivos; o EIPBII é recomendado só para dois objetivos, sobretudo quando a forma… «For problems with more than two objectives, using EPBII is preferable, since it can robustly obtain diverse NDSs in up to four-objective problems.»
- [muitos objetivos (M)] **c131** (MORBO) [Sec. 6 (Discussion)]: Uma limitacao reconhecida pelos proprios autores: a aquisicao baseada em hipervolume (nucleo do MORBO) tem complexidade computacional que piora mal conforme o numero de objetivos M cresce, ao contrario da escalabilidade… «using hypervolume-based acquisition means the computational complexity scales poorly with the number of objectives»
- [muitos objetivos (M)] **c141** (MMRAEA) [Sec. Conclusion]: O próprio artigo afirma (não testa empiricamente) que MMRAEA não é adequado para problemas muitos-objetivos, pois sua seleção usa relação de dominância de Pareto (que degrada com M alto); nenhuma instância do artigo… «MMRAEA is not suitable for handling many-objective problems since it uses selection strategies based on the Pareto dominance relation.»
- [muitos objetivos (M)] **c154** (JES) [Apêndice L.9]: O custo da decomposição em caixas (exclusiva dos métodos informacionais conjuntos, O(p^(⌊M/2⌋+1))) passa a dominar o tempo de parede à medida que M cresce, tornando JES/MES proporcionalmente mais caros em problemas de… «As the number of objectives increases, the one time box decomposition is the dominant contributor to the wall time for the MES and JES.»
- [muitos objetivos (M)] **c217** (PC-SAEA) [Sec. 4.3]: PC-SAEA vence em 2 dos 3 problemas reais (CSI, WRM); REMO vence no terceiro (GAA, o de maior dimensão de decisão, d=27) — o artigo não atribui essa exceção à dimensão ou ao nº de objetivos, apenas relata o resultado… «PC-SAEA obtains two best HV values and REMO obtains one best result, both of which are based on pairwise comparison based surrogate models.»
- [muitos objetivos (M)] **c222** (MESMO) [Sec. 5.2]: O tempo de otimização da aquisição de PESMO e SMSego cresce muito com o número de objetivos; o de MESMO cresce pouco — atribuído à complexidade assintótica O(SK) do MESMO contra O(SKm³) do PESMO. «the time for PESMO and SMSego increases significantly as the number of objectives grow from two to six, whereas the corresponding growth in time is relatively…»
- [muitos objetivos (M)] **c238** (EIM) [Sec. VI-B]: O desempenho relativo dos critérios EIM (frente aos EI originais) se mantém competitivo ou melhora conforme m cresce de 3 para 6, tanto em qualidade (Tabelas III-V, com exceções pontuais como EIh no DTLZ7 m=6) quanto… «When the number of objectives becomes high, the performance of the three EIM criteria are still competitive and even better compared against the…»
- [muitos objetivos (M)] **c241** (EMMOEA) [Sec. III-E]: DTLZ6 tem frente degenerada, difícil para vetores de referência uniformemente distribuídos convergirem, agravada pela função de potência em g; EMMOEA não vence em DTLZ6 (m=3,5) nem em DTLZ5 (m=10). «DTLZ6 has a degenerated Pareto front, which is difficult for an algorithm using a set of evenly distributed reference vectors to converge to.»
- [muitos objetivos (M)] **c261** (DirHV-EGO) [Supplementary Sec. III-C.4/III-D.1, p.9-10]: O desempenho de DirHV-EGO deteriora conforme m aumenta de 4 para 6 nesses problemas, porque mais vetores de direção deixam de ter interseção com a PF verdadeira; em m=4, DirHV-EGO ainda é competitivo, mitigado… «the performance of DirHV-EGO deteriorates on DTLZ5 and DTLZ6 as m increases»
- [muitos objetivos (M)] **c262** (qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF)) [Apendice H.8, Fig. 16]: O custo de otimizar a aquisicao cresce fortemente com M (mais hiper-retangulos na decomposicao de caixas, complexidade super-polinomial em M); apesar disso, qNEHVI-1 (via CBD + amostra unica) e o primeiro metodo baseado… «using CBD and a single sample path approximation, qNEHVI-1 can be used for 5-objective optimization»
- [muitos objetivos (M)] **c48** (IBE-CSEA) [Sec. 4.7, Table 5]: No único problema real testado, o artigo não atribui uma razão mecânica específica para a ordem observada (KTA2 melhor, IBE-CSEA em segundo), apenas relata a ordem de desempenho — diferente do tratamento qualitativo… «Vehicle crashworthiness optimization design is a 9 objectives optimization problem with optimization objectives such as abdomen load, rib deflection and pubic…»
- [muitos objetivos (M)] **c49** (Interactive Offline DD-MOEA Framework (sigla não-oficial, proposta por mim)) [Sec. 5, Conclusions]: O framework é apresentado como capaz de lidar com problemas many-objective, demonstrado pelo estudo de caso GAA com 10 objetivos (+1 restrição tratada como objetivo adicional). «We also demonstrated it by solving the GAA problem that proved its capability in solving many-objective problems.»
- [muitos objetivos (M)] **c71** (SAEA/ME) [Sec. 5 (Conclusions)]: Autocrítica interna do próprio método: o problema de busca que consome a incerteza (Eq. 9, 2m objetivos: média + limite de confiança inferior por objetivo original) é otimizado com NSGA-II, cujas fraquezas em contextos… «given its reported drawbacks for many-objective optimisation»
- [muitos objetivos (M)] **c81** (UA-MORL-Diff) [Appendix C.1]: à medida que o número de objetivos cresce além de ~5, a suposição de independência condicional entre eles (base da agregação por produto de probabilidades) fica menos sustentável, exigindo modelagem explícita de… «as the number of properties increases (e.g., more than 5), the assumption of independence may become less reasonable due to the potential rise in…»
- [muitos objetivos (M)] **e1** (EMO) [Sec. 4.1]: Apesar da desconexão da frente, o critério Phv obtém o melhor resultado marcado no artigo (negrito+itálico) tanto em convergence measure (0.0280) quanto em hipervolume (43.5404) entre as configurações testadas em DTLZ7… «the DTLZ7 function with four objective functions which has 2m−1 = 24−1 = 8 disconnected Pareto-optimal regions in the objective space»
- [muitos objetivos (M)] **e103** (IBEA-MS) [Sec. IV-B]: IBEA-MS é fraco em problemas de dez objetivos que exigem boa distribuição de soluções (ex.: DTLZ4), porque usa a incerteza SOMENTE para escolher entre modelos, não para promover diversidade — diferente de AK-IBEA e… «Both the AK-IBEA variants and NSGA-II-GP use the uncertainty information of the Kriging models to increase the diversity of the population. Instead, our…»
- [muitos objetivos (M)] **e17** (MOBO) [Sec. IV-A]: Com um espaco de objetivos de alta dimensao (7 objetivos), e preciso um grande numero de observacoes (100-200) para o algoritmo construir uma frente de Pareto bem definida antes que ganhos adicionais passem a vir… «Since the objective space is high dimensional, it takes a large number of observations (100-200) for the algorithm to build up a well-defined Pareto front.»
- [muitos objetivos (M)] **e64** (SA-MOPSO (PPD)) [Sec. 5.1.1]: No ZDT, só o 2o objetivo precisa ser emulado (o 1o e só uma variável de decisão); isso torna o problema o mais simples dos 3 benchmarks e contribui para a convergência muito rápida do SA-MOPSO nele. «The first objective of ZDT is simply the value of one of the decision variables; hence, emulating this objective is unnecessary and only the second objective…»
- [muitos objetivos (M)] **e7** (EDN-ARMOEA) [Sec. IV-C]: HeE-ARMOEA (ensemble heterogêneo baseado em SVM+RBF, single-output) degrada com o aumento do número de objetivos, ao contrário de EDN-ARMOEA (rede neural multi-saída), que os autores concluem ser especialmente adequado… «although HeE-ARMOEA also shows promising performance, its performance degrades as the number of objectives increases... we conclude that the proposed…»
- [muitos objetivos (M)] **emo1** (MPoI / HypI / DomRank / MSD (4 estratégias de infill)) [Sec. 5, p. 878; Fig. 3, painel DTLZ5, p. 879]: Nota metodológica explícita dos autores: SMS-EGO e ParEGO nunca haviam sido testados com mais de três objetivos antes deste artigo; mesmo assim, em DTLZ5 (D=6) o SMS-EGO vence isoladamente (contagem 0) e o MPoI… «It should be noted that SMS-EGO and ParEGO have not been tested in more than three objectives before in the literature.»
- [alta dimensão (D)] **b1** (ParEGO) [Sec. VIII, p. 62]: Com DoE inicial de 11d-1 (=87 para d=8) e orçamento de 100 avaliações, ParEGO só executa 13 iterações guiadas pelo modelo em DTLZ2a/4a/7a; o artigo aponta isso como a causa provável do desempenho inferior a NSGA-II em… «If one were interested in a strong performance after 100 evaluations on these functions, a sparser latin hypercube may be worth considering.»
- [alta dimensão (D)] **b13** (AdaMoR-DDMOEA) [Sec. 5.4]: IBEA-MS (Kriging com troca para RBFN por limiar de incerteza) supera AdaMoR-DDMOEA especificamente em problemas que não exigem muita diversidade (ZDT2, ZDT3, DTLZ6, DTLZ7), mas seu surrogate RBF não é bom o bastante em… «it performs badly in other 2- and 3-dimensional multi-modal problems, as the chosen RBF surrogate model is not good enough on small dimensional problems.»
- [alta dimensão (D)] **b15** (U-RankMOEA) [Apendice L.4]: Mesmo com vantagem relativa consistente sobre os baselines em D=500, o desempenho ABSOLUTO nesses dois problemas segue fraco, indicando que a dificuldade estrutural persiste mesmo quando o metodo vence a comparacao… «The absolute performance on challenging landscapes such as DTLZ3 and DTLZ6 indicates room for improvement, while extreme-scale problems (D > 1000) may require…»
- [alta dimensão (D)] **b3** (K-RVEA) [Sec. IV-B, p. 9]: A frente de DTLZ5 sendo uma curva que ocupa um subespaço pequeno do espaço de objetivos deixa a maioria dos vetores de referência vazios, travando a convergência do mecanismo baseado em vetores de referência (K-RVEA e… «As the Pareto front of DTLZ5 is a curve that covers a small subspace in the objective space, most of the reference vectors in K-RVEA and RVEA are empty, i.e.,…»
- [alta dimensão (D)] **b4** (CSEA) [Sec. IV-E]: CSEA mantém desempenho competitivo/melhor nos três níveis de d; MOEA/D-EGO (baseado em Kriging), que vence em d=10, produz soluções longe da frente de Pareto em d=20 e d=30 e é excluído dessas comparações — atribuído à… «the non-dominated solutions achieved by MOEA/D-EGO on ZDT1 with 20 and 30 decision variables are far from the Pareto optimal front»
- [alta dimensão (D)] **b9** (USeMO) [Sec. 5.2 ("USeMO vs. State-of-the-art",…]: USeMO mantém um comportamento de convergência consistente conforme a dimensão do espaço de entrada cresce (para um número fixo de objetivos), enquanto o concorrente PESMO fica progressivamente mais lento para convergir… «The convergence rate of PESMO becomes slower as the dimensionality of input space grows for a fixed number of objectives, whereas USeMO maintains a consistent…»
- [alta dimensão (D)] **c1** (BS-MOBO) [Sec. IV-B-1]: O Gaussian Process com poucos dados de treino (subamostrados) não consegue aproximar bem a função; métodos baseados nesse modelo perdem para pisos sem surrogate nesses problemas específicos. «the model-based methods with the Gaussian process model (BS-MOBO-GP, K-RVEA and MOEA/D-EGO) are outperformed by those two model-free methods on some test…»
- [alta dimensão (D)] **c10** (SP-RV-MOEANet) [Sec. Experiments on synthetic networks]: SP-RV-MOEANet obtém a melhoria mais notável entre os três tipos de rede sintética justamente nas redes SF, atribuída à capacidade de mitigar via reconexão (rewiring) a fragilidade característica dessas redes a ataques… «This unique structure makes SF networks “robust yet fragile” [43]; that is to say, SF networks tend to have a good tolerance against random attacks but can be…»
- [alta dimensão (D)] **c107** (MS-VHGP-EIHV) [Sec. V (Conclusion)]: O método é declarado pelos próprios autores como pouco eficiente quando a dimensionalidade do espaço de busca é muito alta. «it is not so efficient if the dimensionality of the search space is very large, as is the case for hyper-redundant robots.»
- [alta dimensão (D)] **c131** (MORBO) [Abstract; Sec. 1]: A maioria dos metodos de BO multiobjetivo existentes (com GP global) falha em escalar e ter bom desempenho em espacos de busca com mais de algumas dezenas de parametros; o MORBO estende BO multiobjetivo a centenas de… «most existing multi-objective BO methods perform poorly on search spaces with more than a few dozen parameters and rely on global surrogate models that scale…»
- [alta dimensão (D)] **c141** (MMRAEA) [Sec. Introduction]: Eixo central do artigo inteiro: IGD de todos os algoritmos piora sistematicamente conforme d cresce de 20 para 100 em praticamente todas as 84+48 instâncias das Tabelas 2-5; atribuído (Introdução) à queda de acurácia… «with the increasing of decision variables, the approximation or prediction accuracy of the surrogate model based on a limited number of training samples is…»
- [alta dimensão (D)] **c149** (LBN-MOBO) [Sec. C.7]: A vantagem de LBN-MOBO sobre NSGA-II/DGEMO diminui quando a dimensionalidade cai de 44 para 8 tintas — os concorrentes 'chegam mais perto' do resultado de LBN-MOBO. «both NSGA-II and DGEMO exhibit results that are closer to LBN-MOBO, which could be attributed to the lower dimensionality of the problem»

### 8.6 Os 15 do roster: o mecanismo próprio, o que o reproduz nas camadas e os parâmetros do uso da incerteza (roster_bloco, íntegra)

#### c122 — θ-DEA-DP (2022) · A2 · Dominância probabilística · CL - Relação/Classificação · NAT-nonGP (distribuição nativa não-GP)

**Mecanismo próprio (análises que o artigo faz sobre o próprio uso da incerteza):**
  - Comparação de acurácia (%) de classificação de dominância dos classificadores Pareto-Net/θ-Net contra SVM/RF/CNB e contra variantes sem ponderação de classe (Pareto-Net*/θ-Net*), em 9 problemas de 2-3 objetivos, mediana±DP sobre 21 execuções com Wilcoxon rank-sum. É ao mesmo tempo (i) acurácia do classificador que É o mecanismo de incerteza do próprio algoritmo (A2 · dominância probabilística) e (ii) ablação do componente de tratamento de desbalanceamento de classe (perda ponderada vs. não ponderada). (literal: Table VIII shows the median prediction accuracy (over 21 runs) and the standard deviation of different algorithms.; localizador: Sec. IV-D, Table VIII)
  - Sensibilidade do IGD final (DTLZ1, 2 objetivos, últimas 100 avaliações) a 6 hiperparâmetros, dos quais γ (limiar de acurácia que decide se o classificador é retreinado, com base na acurácia mínima estimada acc_min) e Qmax (tamanho máximo de categoria, que trunca candidatos pela soma de probabilidades preditas p_sum) são os que mais diretamente definem COMO a probabilidade/confiança do classificador é usada na seleção. (literal: Fig. 7 plots the evolutionary trajectories of median IGD for two-objective DTLZ1 under various parameter settings.; localizador: Sec. IV-D, Fig. 7)
  - Sub-achado da Tabela VIII: em DTLZ4, RF (80.87%) e SVM (54.53%) superam significativamente θ-Net (53.67%) na predição de θ-dominância — diagnóstico direto de uma fraqueza pontual do mecanismo de predição do próprio método, não comentada em prosa pelos autores mas presente nos números. (literal: θ-Net 53.67(2.29) ... RF 80.87(4.33)− [linha DTLZ4, colunas de θ-dominância]; localizador: Table VIII, linha DTLZ4)

**Reprodutível com as camadas:** Item 1 (Table VIII, acurácia do classificador) é reproduzível de forma ADAPTADA via camada ③ (predições do surrogate): como Pareto-Net/θ-Net classificam PARES de soluções (não pontos únicos), a 'sonda' de 2.000 pontos fixos da dissertação precisaria ser usada em pares (entre si, ou pontos-sonda × arquivo) — comparando classe prevista × classe real (computável via f verdadeiro conhecido dos pontos-sonda) — para produzir uma acurácia por classe análoga à Table VIII, e essa métrica poderia ser estendida ao longo de todo o orçamento (o artigo só mede uma vez, na inicialização). O sub-achado da anomalia em DTLZ4 (item 3) usa a mesma adaptação, mas exigiria também rodar/registrar classificadores-baseline (RF/SVM) para comparação — fora do desenho padrão da bateria, que registra só o modelo de fato usado por cada algoritmo. Item 2 (Fig. 7, sensibilidade a γ/Qmax/U/D/N*/Tmax) NÃO é reproduzível com o desenho fatorial padrão das 7 camadas (28 problemas × 30 sementes × 1 config por algoritmo) — exigiria execuções extras com hiperparâmetros variados; seria reconstruível via camada ④ (tempos) + camada ⑤ (manifesto de params) + camada ① (endpoint/curva) SE a dissertação decidir rodar essas configs alternativas como um estudo dedicado. Nenhum dos três itens fornece, no corpo do artigo, uma contagem explícita de quantas vezes cada categoria (Q1/Q2/Q3/Q5) foi de fato selecionada durante as execuções reais — essa contagem (ficha 45) teria de ser reconstruída do zero pela dissertação usando a camada ⑥ (filme); não está no artigo.

**Parâmetros do uso da incerteza:**
  - γ (gamma) — limiar de acurácia mínima (acc_min) acima do qual o classificador NÃO é retreinado na iteração corrente; valor usado no artigo: 0.9 (Table III). É o parâmetro mais próximo de um 'gate de confiança', mas gate SOBRE O PRÓPRIO CLASSIFICADOR (decide se retreina), não um gate de exploração na aquisição.
  - Qmax — tamanho máximo de categoria (Q1/Q2/Q3/Q5) mantido após truncar pelo somatório de probabilidades preditas p_sum(z); valor usado no artigo: 300 (Table III). Define quantos candidatos 'sobrevivem' com base na confiança agregada do classificador.
  - Tmax — janela de dados mais recentes (11n+24 pontos) usada para retreinar Pareto-Net/θ-Net a cada iteração; valor usado no artigo: 11n+24 (Table III). Não gate de confiança em si, mas afeta a base empírica de onde a confiança é calculada; Fig. 7 mostra que Tmax MENOR tende a ser melhor.
  - Mecanismo de desempate (Eq. 4) — quando [u,v] e [v,u] dão predições inconsistentes, usa-se o vetor de entrada com MAIOR probabilidade/confiança (p(u,v) vs p(v,u)) para decidir a relação de dominância final; não tem um único hiperparâmetro nomeado, é regra fixa.
  - EDN — expected dominance number (Eq. 6-7): métrica de ranqueamento dos candidatos dentro da categoria escolhida, soma ponderada pela probabilidade predita de cada comparação par-a-par; sem hiperparâmetro livre, mas é o ponto onde a 'incerteza' (confiança) entra diretamente no ranqueamento final.
  - αk (peso de classe na entropia cruzada, Eq. 3) = frequência inversa de cada classe no conjunto de treino corrente — não um valor fixo, recalculado a cada retreino; é o mecanismo de tratamento de desbalanceamento ablado na Table VIII (Pareto-Net vs Pareto-Net*).

#### c141 — MMRAEA (2025) · O1 · Aquisição exploratória · RG — Regressor Clássico (não-GP) · DISC-ENS (discordância entre predições)

**Mecanismo próprio (análises que o artigo faz sobre o próprio uso da incerteza):**
  - Ablação do mecanismo de qualidade+incerteza (Q,U) do MMRAEA: comparação contra três variantes de modo único (V1=só ARBFs, V2=só FitRBF, V3=só FNRBF), cada uma sem ensemble e sem termo de incerteza/exploração — a análise mais próxima de uma 'ablação exata' da bateria do roster para este algoritmo, embora confunda simultaneamente a remoção do ensemble de qualidade (3 ranks somados) e a remoção do termo de incerteza (discrepância entre ranks + pick de incerteza máxima), não isolando os dois efeitos separadamente. (literal: although its three variants achieve the best performance on some instances, MMRAEA outperforms them under overall consideration and shows the best performance on most of the instances.; localizador: Sec. Effectiveness of multi-mode RBFs, Table 2)
  - Sub-achado da mesma tabela: contra MMRAEA-V3 especificamente (só o modo de ranking por número de fronteira), o ganho do mecanismo completo de incerteza é fraco (empate em 30/48, derrota em 3/48) — diagnóstico direto de que a 'incerteza' (U, discrepância entre ranks) agrega pouco valor quando comparada a um único modo de ranking já robusto. (literal: MMRAEA-V3 ... +/−/≈ 3/15/30; localizador: Table 2, linha de placar agregado (coluna MMRAEA-V3))

**Reprodutível com as camadas:** O item 1 (Table 2, ablação tri-modo) é reproduzível via camada ① (endpoint IGD+ por config) SE a dissertação registrar as 3 variantes extras (V1/V2/V3) como configs adicionais no manifesto (camada ⑤) — fora do desenho padrão de 1 config por algoritmo × 28 problemas × 30 sementes. A camada ③ (sonda) permitiria IR ALÉM do artigo: verificar diretamente se U (a soma das discrepâncias |Ri−Rk| entre os 3 ranks nos pontos-sonda de f verdadeiro conhecido) de fato se correlaciona com o erro real |μ−f| — checagem de calibração/discriminação (fichas 33/34) que o próprio artigo NUNCA faz (ver calibracao_do_sigma.mede=false). O item 2 (sub-achado V3) usa a mesma base de dados do item 1, mesma aplicabilidade. Nenhum dos dois itens fornece uma contagem de quantas vezes, durante as execuções reais, o indivíduo de incerteza máxima (Pb, Algorithm 3 linha 15) foi de fato distinto dos indivíduos já selecionados por qualidade (Pa) — essa contagem (ficha 45) teria que ser reconstruída do zero via camada ⑥ (filme), caso a dissertação rode o MMRAEA como parte de sua própria bateria.

**Parâmetros do uso da incerteza:**
  - U_j = Σ_{i,k∈{1,2,3}, k≠i} |R_{i,j} − R_{k,j}| (Eq. 8) — a incerteza de cada candidato é a soma das discrepâncias absolutas entre os ranks dados pelos 3 modos de RBF (ARBFs/ARBF-quality, FitRBF, FNRBF); é a operacionalização exata de DISC-ENS (discordância entre predições) da taxonomia. Não tem hiperparâmetro livre — é uma fórmula fixa.
  - Passo de seleção por incerteza máxima (Algorithm 3, linha 15: 'Pb ← Maximum uncertainty of P') — INCONDICIONAL: a cada geração, exatamente 1 indivíduo de U máximo é sempre adicionado às novas amostras (Ps = Pa ∪ Pb), sem gate/limiar de confiança que decida SE usar a incerteza — diferente de mecanismos com gate condicional (ex.: δ do EDN-ARMOEA, citado no próprio artigo como comparação).
  - u = número máximo de novas amostras por geração; usado como teto para decidir se entra a etapa de ranking Q/U (Algorithm 3: 'if |P|>u then ...'); valor usado para MMRAEA: 5 (Sec. Parameter settings, item 5). Não é um parâmetro do TERMO de incerteza em si, mas governa quando o mecanismo de qualidade+incerteza é sequer acionado (se |P|≤u, todo P vira Ps diretamente, sem calcular Q/U).
  - N = tamanho de população (50) e wmax = nº de gerações de otimização evolutiva interna (20) — parâmetros gerais do motor de busca, não específicos da incerteza, mas que definem |Ptot| e portanto o tamanho do conjunto sobre o qual Q/U são calculados a cada retreino.
  - σ (parâmetro da função de base multiquádrica RBF, fixado em 1 por padrão) — hiperparâmetro do PRÓPRIO regressor RBF (kernel width), não do mecanismo de uso da incerteza; mencionado aqui só para não confundir com o 'σ' de incerteza da notação da dissertação — são conceitos homônimos e não relacionados neste artigo.

#### c149 — LBN-MOBO (2023) · O1 · Aquisição exploratória · NN — Rede Neural · DISC-ENS (discordância entre predições)

**Mecanismo próprio (análises que o artigo faz sobre o próprio uso da incerteza):**
  - Ablação exata: aquisição 2MD com e sem o termo de incerteza epistêmica (só os M objetivos de desempenho) em dois problemas reais (aerofólio e gamut de impressora), comparando a dispersão espacial dos candidatos. (literal: in the absence of uncertainty, the candidates have a tendency to cluster within particular areas. This clustering leads to diminished diversity; localizador: Sec. 5.4, Fig. 5)
  - Sensibilidade dos pesos α, β do termo de incerteza aleatória na aquisição, em problema-brinquedo 1D com um máximo local contaminado por ruído gaussiano. (literal: Running one iteration of LBN-MOBO on this problems with batch size 1000 leads to over 93% of acquisition samples being chosen from the noisy region; localizador: Sec. 5.5, Fig. 6)
  - Mesma sensibilidade de α, β no gamut de impressora simplificado com ruído injetado em um canal, contando amostras válidas por configuração de peso. (literal: resulting in only 46 samples from noise-free regions after 8 iterations; localizador: Sec. 5.5, Fig. 7)
  - Ablação epistêmico-só × epistêmico+aleatório (Deep Ensembles completo) em ZDT1/ZDT2/ZDT3 — resultado negativo do termo aleatório quando o ruído do problema é desprezível. (literal: incorporating aleatoric uncertainty does not affect the exploration process in a beneficial manner, as showcased by the ZDT1 results, and may even delay the convergence, as observed in the ZDT2 and ZDT3 experiments; localizador: Sec. E.1, Fig. 20)
  - Escolha da forma de medição da incerteza (o surrogate): comparação de Deep Ensembles, MC Dropout, SGHMC, HMC, DKL e IBNN sob a mesma aquisição 2MD, decidindo por Deep Ensembles/Dropout como mais escaláveis e informativos. (literal: DE and MC dropout prove to be the most time-efficient models, adeptly conducting optimizations for batch sizes up to 1000; localizador: Sec. 5.1, Fig. 3)

**Reprodutível com as camadas:** Ablação com/sem incerteza epistêmica (Fig. 5): reproduzível de forma adaptada via ① (endpoint) e ⑥ (filme, SE o roster registrar o motivo de seleção de cada candidato — Pareto por desempenho vs. Pareto por incerteza) para o LBN-MOBO do roster, mas exige rodar a variante sem o termo de incerteza (σ=0 na aquisição), que corresponde exatamente ao contrafactual da ficha 15 ('cravado, nunca executado' na dissertação) — este artigo é evidência externa de que esse contrafactual É executável e do sentido esperado do efeito (mais aglomeração/menos diversidade sem σ). Sensibilidade a α/β (Figs. 6, 7): NÃO reproduzível só com as 7 camadas — exige reexecuções com pesos diferentes do termo de incerteza aleatória sobre um problema com ruído local injetado; a camada ⑤ (manifesto) registraria os valores de α/β usados SE essas variantes fossem de fato rodadas, e a camada ⑥ (filme) poderia contar a fração de FEs caindo em região ruidosa. Ablação epistêmico × epistêmico+aleatório (Fig. 20): reproduzível via ① + ② (HV por geração) para cada variante, se ambas estiverem gravadas como configurações distintas do mesmo algoritmo no roster. Escolha do surrogate/medição (Fig. 3): a forma correta de comparar VA/DE/Dropout no desenho da dissertação seria via ③ (sonda, RMSE e calibração por classe de medição — ficha 36), em vez do HV final de tarefa usado pelo artigo.

**Parâmetros do uso da incerteza:**
  - K (nº de sub-redes no ensemble Deep Ensembles) = 10 — define diretamente o cálculo de σ_epistêmico (Eq. 2b: variância das médias entre os K membros).
  - Diversidade de funções de ativação entre os K membros do ensemble (Tanh×2, ReLU×2, CELU×2, LeakyReLU×2, ELU×1, Hardswish×1) — citada como decisiva para 'higher quality uncertainty'.
  - α, β — pesos do termo de incerteza aleatória F_σA subtraído dos objetivos e das incertezas na aquisição (Eq. 4); testados em (0,0), (1,1) e (7,7)/(10,10) conforme o experimento.
  - T (nº de passagens estocásticas do MC Dropout na inferência) = 100 — define σ quando o surrogate é MC Dropout em vez de Deep Ensembles.
  - Taxa de dropout = 0,05, usada em todas as camadas de dropout do surrogate MC Dropout.

#### c217 — PC-SAEA (2023) · A3 · Gestão de confiança · CL - Relação/Classificação · ERR-EMP (erro empírico vs. verdade)

**Mecanismo próprio (análises que o artigo faz sobre o próprio uso da incerteza):**
  - Comparação direta de acurácia de classificação (Recall/Precision/Accuracy/F1) do surrogate par-a-par de PC-SAEA contra 5 outros tipos de surrogate (kNN, Kriging, FNN-classificador, rede com dropout, par-a-par concorrente), com o MESMO split treino/teste compartilhado entre todos, em 4 problemas fixos. (literal: Table 5 lists the performance of the surrogate models used in the six compared MOEAs on DTLZ2, DTLZ3, WFG7, and MaF4, where the indicator values of Recall, Precision, Accuracy, and F1 averaged over 30 runs are reported.; localizador: Sec. 4.4, Table 5)
  - Ablação do TIPO de surrogate (regressão RBF × classificação PNN × comparação par-a-par PNN) dentro do mesmo framework algorítmico de PC-SAEA, em IGD e tempo de execução, sobre WFG1-9. (literal: Table 6 presents the IGD values of PC-SAEA with different surrogate models on WFG1–WFG9, where the original PC-SAEA based on a pairwise comparison based model considerably outperforms those based on a regression model or a classification model.; localizador: Sec. 4.4, Table 6)
  - Ablação da fração de pareamento treino best/worst (N/4 × N/3 × N/2), que determina que amostras alimentam o treino do surrogate a cada geração — parâmetro de construção dos dados de treino, não do gate em si, mas que molda diretamente a qualidade do sinal de confiança calculado. (literal: the original PC-SAEA outperforms the two variants with more training samples. Besides, the last row of Table 7 presents the test accuracies of the three MOEAs averaged over all the problems, where pairing the N/4 best solutions with the N/4 worst solutions leads to the highest test accuracy.; localizador: Sec. 4.5, Table 7)
  - A ablação MAIS DIRETA do mecanismo A3 (gestão de confiança): compara a estratégia dinâmica (usar/inverter/ignorar conforme p+/p− vs δ) contra sempre-usar-diretamente e contra sempre-usar-invertido, isolando o efeito líquido de GERIR a confiabilidade em vez de confiar cegamente (ou desconfiar cegamente) do surrogate. (literal: the original PC-SAEA outperforms the two variants, hence the effectiveness of the proposed reliability based model management strategy can be evidenced.; localizador: Sec. 4.5, Table 8)
  - Sensibilidade ao parâmetro δ (limiar de confiabilidade que define diretamente o uso da confiança/incerteza) em 4 problemas, identificando δ=0,8 como o melhor valor entre os 7 testados. (literal: It is obvious that PC-SAEA obtains the best overall performance when δ = 0.8, which strikes a good balance between the use of promising surrogate models and the elimination of unpromising surrogate models.; localizador: Sec. 4.5, Fig. 8)
  - Estabilidade da acurácia do classificador ao longo do orçamento (não sobe, pois o treino não é cumulativo — reamostra a população corrente a cada geração) e sensibilidade dessa acurácia ao tamanho da população N, em DTLZ2. (literal: the surrogate models hold stable learning performance during the evolutionary process, where the accuracies are not increased since a new model is trained at each generation.; localizador: Sec. 4.5, Fig. 9)

**Reprodutível com as camadas:** Item 1 (Tabela 5, acurácia comparada entre 6 surrogates): a acurácia PRÓPRIA de PC-SAEA (predição × verdade) é reproduzível via camada ③ cruzada com ①, mas a comparação SIMULTÂNEA e justa entre os 6 modelos com split de treino/teste compartilhado NÃO é reproduzível — exigiria uma harmonização entre execuções independentes de algoritmos distintos do roster, fora do desenho da instrumentação. Item 2 (Tabela 6, ablação do tipo de surrogate) e Item 3 (Tabela 7, ablação da fração de pareamento): NÃO reproduzíveis — ambos exigem reexecutar PC-SAEA com uma configuração diferente da de fato executada (outro tipo de modelo; outra fração de pareamento), o que a camada ⑤ (manifesto) só registraria se essas variantes tivessem sido de fato rodadas, o que não é o caso do desenho padrão da dissertação (1 configuração por algoritmo). Item 4 (Tabela 8, gestão de confiança dinâmica × fixa): as variantes fixas ('directly'/'reversely used') NÃO são reproduzíveis pela mesma razão; mas a variante 'dynamically used' É a execução real registrada — a camada ⑥ (filme) permitiria, SÓ para essa execução real, contar quantas vezes cada estado (1=usar direto, 2=usar invertido, 3=ignorar) ocorreu por geração — uma contagem que o PRÓPRIO ARTIGO nunca relata numericamente em lugar nenhum (nem na Tabela 8, nem na Fig. 8, nem em qualquer outro ponto), apesar de a tipologia citar 'c217' precisamente como exemplo de 'quantas vezes o gate abriu' (ficha 45) — essa contagem teria que ser inteiramente reconstruída do zero pela dissertação a partir da execução real de PC-SAEA, sem nenhum número de referência do próprio artigo para comparar. Item 5 (Fig. 8, sensibilidade a δ): não reproduzível — exige reexecução com cada valor de δ, registrado na camada ⑤ só para o δ=0,8 de fato usado. Item 6 (Fig. 9, acurácia × orçamento × N): a curva de acurácia ao longo do orçamento, PARA O N=50 de fato executado, é reproduzível via ③×①; a varredura de N (10 a 100) não é.

**Parâmetros do uso da incerteza:**
  - δ (threshold of reliability measurement) = 0,8 — o parâmetro central: limiar sobre p+ (fração de amostras de validação corretamente classificadas) e p− (fração invertidamente classificada) que decide entre state=1 (usar diretamente, se p+>δ), state=2 (usar invertido, se p−>δ), ou state=3 (ignorar o surrogate, caso contrário); sensibilidade testada em {0,65; 0,70; 0,75; 0,80; 0,85; 0,90; 0,95} (Fig. 8).
  - p+ e p− (Algoritmo 4) — a MEDIÇÃO operacional da confiança em si: acurácia empírica (fração corretamente/invertidamente classificada) sobre um conjunto de validação com rótulo verdadeiro conhecido, recalculada do zero a cada geração; é literalmente o número que δ filtra.
  - score > 0,95 (state=1) / score < −0,95 (state=2) — limiares adicionais, internos ao loop de geração de prole (Algoritmo 5), sobre a saída contínua do PNN (score = output(⟨x,y⟩) − output(⟨y,x⟩)) para filtrar quais dos candidatos gerados virtualmente são 'confiantes o bastante' para receber avaliação real — uma segunda camada de uso da confiança, além do δ no nível do modelo.
  - no máximo seis soluções por geração — cap no nº de candidatos com maior |score| selecionados de AllQ para avaliação real, por geração (Algoritmo 5, linhas 10 e 18).
  - Gmax (número máximo de predições/gerações virtuais do surrogate antes de parar de buscar e avaliar de fato) = 3000 — governa POR QUANTO TEMPO o surrogate (já validado/gated) é explorado antes de gastar avaliações reais; não é o limiar de confiança em si, mas a duração da busca que o confia.
  - N/4 (fração da população pareada como melhor/pior para treino do surrogate) — molda os DADOS de onde p+/p− são calculados; sensibilidade testada contra N/3 e N/2 (Tabela 7); incluído por completude/proximidade conceitual, não é o gate em si.
  - N (tamanho da população) = 50 — afeta a acurácia do classificador (Fig. 9: N maior → acurácia maior) mas não é, ele próprio, um parâmetro de uso da incerteza; incluído por completude.

#### c238 — EIM (2017) · O1 · Aquisição exploratória · GP — Processo Gaussiano/Kriging · VAR-GP (posterior fechada de GP)

**Mecanismo próprio (análises que o artigo faz sobre o próprio uso da incerteza):**
  - Prova formal (Sec. IV-C) de que os três critérios EIM propostos satisfazem as propriedades de monotonicidade N1 (decrescente na média predita ŷ) e N2 (crescente na incerteza σ), decorrentes diretamente da monotonicidade do EI de base — ao contrário do critério EI euclidiano estado-da-arte concorrente, que falha nessas propriedades (Sec. III-C); ilustrado com um exemplo numérico (pontos 1, A, B, Figs. 6-7) mostrando como a EIM corrige uma inversão de preferência causada pelo uso de distância absoluta (sem sinal) na versão EI. (literal: The monotonicity properties can be easily proven for the three proposed multiobjective EIM criteria.; localizador: Sec. IV-C, Figs. 6-7)
  - Demonstração (Sec. IV-D) de que, para função sem ruído, a EIM nunca é zero em pontos ainda não amostrados (pois σ>0 implica EI>0 em cada elemento da matriz, logo EIM>0), garantindo que o próximo ponto escolhido nunca coincide com um ponto já avaliado — o que sustenta a densidade da amostragem e a garantia de convergência (citando a teoria de [45]); a propriedade deixa de valer sob ruído, pois então σ é sempre positivo mesmo em pontos já amostrados. (literal: This means that the next point selected by the EIM criteria to evaluate would be anywhere but the sampled points. As a consequence, the iterative sampling based on the EIM criteria is dense and the convergence of the EIM approach can be guaranteed according to the theory of [45].; localizador: Sec. IV-D)
  - Regra prática de salvaguarda (item 5c dos ajustes experimentais): se o ponto de atualização proposto está a menos de 10^-8 (distância Euclidiana) de um ponto já avaliado, ele é substituído por um ponto que MAXIMIZA a incerteza do Kriging, para evitar mau-condicionamento numérico ao reajustar o modelo — um uso explícito e direto de σ como critério de exploração pura em modo de salvaguarda (fallback), distinto do uso normal via EI/EIM. (literal: If the updating point is too close to an existing point (Euclidean distance is small than 10−8), it is replaced by maximizing the uncertainty of the Kriging model to avoid ill conditioning when building the Kriging model.; localizador: Sec. V-B, item (5)(c))

**Reprodutível com as camadas:** Item 1 (monotonicidade N1/N2, Figs. 6-7): NÃO reproduzível como medição de dados — é uma propriedade estrutural da fórmula, provada analiticamente, não uma medição de execução. Poderia ser verificada empiricamente de forma indireta recomputando a fórmula do critério do roster sobre pares de μ/σ registrados em ③ (a sonda), mas isso exige reimplementar o critério fora do fluxo normal de instrumentação — não é uma leitura direta do que já é registrado. Item 2 (densidade de amostragem / nunca reamostrar pontos já avaliados): reproduzível via ① (todas as avaliações reais, x, ordem) — permite checar diretamente, para a execução real do algoritmo do roster, se algum x_novo coincide (ou quase coincide, dentro de um limiar) com um x já avaliado anteriormente na mesma execução; é a camada mais diretamente aplicável dos três itens. Item 3 (fallback de maximizar a incerteza quando o ponto colide com um já avaliado): reproduzível SOMENTE se o algoritmo do roster implementar um fallback análogo E registrá-lo como evento em ⑥ (o filme das decisões internas) — nesse caso ⑥ contaria quantas vezes foi acionado; se o fallback existir mas não for registrado como evento distinto, teria de ser inferido indiretamente cruzando ① (o ponto de fato avaliado) com o ponto que a busca realmente propôs internamente (não registrado se descartado antes de ①).

**Parâmetros do uso da incerteza:**
  - O critério EI/EIM não tem peso explícito de exploração-explotação ajustável pelo usuário (tipo β do UCB, ou δ de um gate) — o balanceamento é 'automático', embutido na integral fechada da EI de base; não há hiperparâmetro de uso da incerteza no sentido usual dos algoritmos com gate/threshold do roster.
  - Ponto de referência r do critério baseado em hipervolume (EIh/EIMh/CEIMh): fixado em ri=1.1 para todo i no espaço de objetivos normalizado [0,1] (Sec. V-B, item 5a) — molda diretamente como os elementos EI^j_i(x) da matriz são combinados nesse critério específico.
  - Limiar de distância 10^-8 (Euclidiana) que aciona a substituição do ponto proposto por um ponto que MAXIMIZA σ, como salvaguarda numérica (Sec. V-B, item 5c) — o único gatilho explícito e discreto ligado ao uso de σ no artigo.
  - θ_i (hiperparâmetros de correlação do Kriging, i=1..n): valor inicial 1, região de busca [10^-3, 10^3] (Sec. V-B, item 2) — determina a forma de σ(x) mas não é, em si, um parâmetro do USO da incerteza pela aquisição; incluído por completude.

#### e74 — CLMEA (2023) · O3 · Aprendizado ativo / reparo · RG — Regressor Clássico (não-GP) · GEO-DIST (geometria/distância aos dados)

**Mecanismo próprio (análises que o artigo faz sobre o próprio uso da incerteza):**
  - Ablação das três subestratégias de infill que compõem o mecanismo próprio de CLMEA: CLMEA-s1 (só distância no espaço de decisão), CLMEA-s2 (só HV, sem incerteza), CLMEA-s3 (só 'incerteza' no espaço de objetivos), contra CLMEA completo (as três combinadas) — a única ablação de componente que o artigo realiza. (literal: CLMEA outperforms CLMEA-s1 and CLMEA-s3 on all benchmark functions, while worse than CLMEA-s2 on 7 out of 28 benchmark problems.; localizador: Sec. IV-C, Table II, Table S-II, Table S-III)

**Reprodutível com as camadas:** O item único (ablação s1/s2/s3) NÃO é reproduzível a partir da execução real de CLMEA completo no roster da dissertação — exige rodar 3 variantes do algoritmo (cada uma restrita a uma das 3 subestratégias) que não fazem parte do desenho de execução única por algoritmo do roster. SE essas variantes fossem rodadas, o resultado seria diretamente comparável via camada ① (endpoint IGD por problema, célula a célula). Não há, neste artigo, nenhum mecanismo de GATE ou de branching condicional entre subestratégias para contar via camada ⑥ (filme): a Algorithm 1 executa as 3 subestratégias INCONDICIONALMENTE em toda iteração do laço externo (3 FEs reais garantidos por iteração, um por subestratégia) — logo a ficha 45 (contagem de acionamentos) não tem correlato neste algoritmo, já que não há decisão/ramo a contar. A qualidade das duas medidas de 'incerteza' geométrica (eq. 7 e eq. 10) em si — não seu efeito no IGD final — poderia em princípio ser inspecionada via camada ③ (sonda), mas o artigo não realiza esse tipo de estudo (ver calibracao_do_sigma).

**Parâmetros do uso da incerteza:**
  - Limiar de proporção de primeiro nível = 0,9 (Algorithm 2, passo 5: 'While sum(l_i=1)/NP < 0.9') — controla quantos descendentes de elite (nível 1) devem ser gerados pelo operador de rank-based learning ANTES que a seleção por 'incerteza' (distância euclidiana, eq. 7-8) seja aplicada entre eles; não testado quanto à sensibilidade neste artigo.
  - n (número de soluções de infill por subestratégia) = 1, fixo em todos os experimentos — determina quantos pontos 'mais incertos' são selecionados por subestratégia a cada iteração; o texto observa que 'the infill number can be larger if the decision maker wishes to make use of parallel computing power', mas nenhum experimento com n>1 (lote) é reportado.
  - max_gen1 (gerações da HV-based non-dominated search) = 50 — número de gerações evoluídas no surrogate RBF antes de calcular a melhoria de HV (eq. 9) que seleciona o candidato para FE real; não testado quanto à sensibilidade.
  - max_gen2 (gerações da local search in the sparse objective space) = 10 — número de gerações evoluídas no RBF local antes de calcular a 'incerteza' no espaço de objetivos (eq. 10) que seleciona o candidato; não testado quanto à sensibilidade.
  - Número de pontos para construir o surrogate local = 100 (D<100) ou 200 (D≥100) — determina a vizinhança usada para treinar o RBF local em torno do ponto esparso escolhido por distância de aglomeração (crowding distance); afeta indiretamente a qualidade da medida de 'incerteza' objetivo-espaço; não testado quanto à sensibilidade.

#### e81 — qPOTS (2025) · O1 · Aquisição exploratória · GP — Processo Gaussiano/Kriging · VAR-GP (posterior fechada de GP)

**Mecanismo próprio (análises que o artigo faz sobre o próprio uso da incerteza):**
  - Ablação da aproximação de Nyström (Sec. 3.3) usada para amostrar a posterior do GP de forma barata em alta dimensão — o mecanismo computacional que viabiliza a amostragem de Thompson (a incerteza propriamente dita) do qPOTS: comparação de HV da variante 'exata' vs 'qPOTS-Nystrom-Pareto' em DTLZ3 e ZDT3 (d=10), tanto sequencial quanto lote. (literal: We show qPOTS-Nystrom-Pareto (that is Xm chosen as the current Pareto set) for the d = 10 experiments which shows no loss of accuracy for the DTLZ3 function and, surprisingly, a slight gain in accuracy for the ZDT3 function.; localizador: Sec. 4.1, Fig. 4 e Fig. 5)
  - Sensibilidade/robustez do mecanismo de incerteza do qPOTS (amostragem de trajetórias da posterior do GP) a diferentes variâncias de ruído de observação injetado (σ² ∈ {0, 1e-6, 1e-4, 1e-3}) no Branin-Currin. (literal: We report hypervolume convergence curves (mean ± std over 10 repeats) showing that qPOTS maintains stable convergence relative to baselines up to the tested noise levels.; localizador: Apêndice 5.3, Fig. 12)

**Reprodutível com as camadas:**   - mecanismo: Ablação da aproximação de Nyström; camada: não reproduzível com as camadas — exige rodar duas variantes do algoritmo qPOTS (com e sem Nyström na amostragem da posterior) e comparar o endpoint (via ①) de cada uma; nenhuma camada isolada permite decompor esse efeito a partir de uma única execução já instrumentada.
  - mecanismo: Ablação de ruído de observação injetado; camada: não reproduzível — exige ruído controlado injetado nas avaliações reais como variável manipulada, fora do desenho padrão (sem ruído) da bateria; a camada ③ (sonda, cobertura μ±2σ) poderia em tese informar uma versão análoga de calibração sob ruído, mas não é isso que este experimento do artigo mede…

**Parâmetros do uso da incerteza:**
  - kernel: Matérn anisotrópico, ν = 5/2 — define a covariância/estrutura de incerteza do GP; usado por padrão em todos os experimentos ('Throughout the manuscript, we default to the anisotropic Matérn class kernel with ν = 5/2', Sec. 4.1)
  - q_batch_size: q ∈ {1, 2, 4} nos sintéticos (Table 1); q = 1 no CRM — número de trajetórias/amostras de Thompson (uma por objetivo) usadas para gerar o lote de candidatos a cada iteração
  - tau2_ruido_observacional: τ² = 1e-3 adicionado às observações nos experimentos sintéticos, para condicionamento da matriz de covariância do GP ('We add Gaussian noise with variance τ2 = 10−3 to all our observations to assist with the conditioning of the GP covariance matrix', Sec. 4.1); no estudo de robustez do Apêndice 5.3, σ² ∈ {0, 1e-6, 1e-4, 1e-3}
  - m_nystrom: tamanho do subconjunto Xm da aproximação de Nyström (Sec. 3.3): NÃO é um valor numérico fixo — escolhido dinamicamente como o subconjunto de pontos não-dominados em {Xn, yn} ('we choose them to be the subset of nondominated points in {Xn, yn}'); desligado (não usado) no experimento do CRM
  - populacao_nsga2_interno: 100 × d indivíduos — população do NSGA-II que resolve o subproblema multiobjetivo barato (Eq. 5) sobre as trajetórias amostradas da posterior, em todos os problemas
  - n_seed_doe: n = 10 × d pontos-semente (DoE inicial) nos sintéticos; 200 pontos-semente no CRM

#### b1 — ParEGO (2006) · O1 · Aquisição exploratória · GP — Processo Gaussiano/Kriging · VAR-GP (posterior fechada de GP)

**Mecanismo próprio (análises que o artigo faz sobre o próprio uso da incerteza):**
  - (nenhuma)

**Reprodutível com as camadas:** Vazio -- não há, no artigo, nenhuma análise que isole o mecanismo de incerteza do próprio ParEGO (sem ablação EI-vs-média-apenas, sem gráfico de sigma ao longo do orçamento, sem contagem de acionamentos). Se a dissertação quiser diagnosticar o mecanismo a partir de uma execução própria de ParEGO no roster, a camada ③ (sonda) seria a única aplicável para calibração/discriminação do sigma; a camada ⑥ (filme) não tem evento para contar porque o EI é a ÚNICA regra de seleção em ParEGO -- não há ramo condicional "usa incerteza / não usa incerteza" para contar acionamentos (ao contrário do que a ficha 45 pressupõe). O contrafactual necessário seria a ablação sigma=0 (fichas 11/15: EI completo vs. seleção pela média predita apenas), que este artigo não executa. IMPORTANTE para a sonda: ParEGO reajusta um modelo DACE/GP DIFERENTE a cada iteração, sobre um alvo escalarizado por um vetor lambda sorteado de novo a cada iteração (Eq. 2) -- não um único GP persistente sobre um objetivo fixo. Isso significa que mu/sigma de iterações diferentes se referem a superfícies escalarizadas distintas; reproduzir a sonda (camada ③) para ParEGO exigiria reescalarizar os 2000 pontos fixos sob o lambda vigente em cada retreino antes de comparar contra o f verdadeiro escalarizado, não apenas contra f original.

**Parâmetros do uso da incerteza:**
  - Não há hiperparâmetro explícito de peso da incerteza: o sigma do DACE/GP entra apenas via a fórmula fechada do Expected Improvement (EI), sem termo de balanceamento ajustável (ao contrário de, por exemplo, um beta de UCB).
  - epsilon = 0.05 -- constante aditiva da função de Tchebycheff aumentada (Eq. 2); não é parâmetro da incerteza, é da escalarização, citado aqui para registro.
  - Tamanho do subconjunto de treino do DACE/GP a cada retreino (afeta indiretamente a qualidade do sigma): se iteração < 25, usa todos os pontos avaliados; senão, metade os melhores sob o vetor de escalarização vigente + metade aleatórios sem reposição, respeitando um teto de tamanho do modelo (EGO: teto fixo de 80; ParEGO: "seleção um pouco mais avançada", teto numérico não especificado no texto limpo).
  - s (número de vetores de escalarização no simplex, Eq. 1) e k (número de objetivos: 2 ou 3): o texto descreve o critério de escolha de s ("permitir várias passagens por vetor") mas não dá o valor numérico usado.

#### b3 — K-RVEA (2018) · O3 · Aprendizado ativo / reparo · GP — Processo Gaussiano/Kriging · VAR-GP (posterior fechada de GP)

**Mecanismo próprio (análises que o artigo faz sobre o próprio uso da incerteza):**
  - Análise de sensibilidade do parâmetro δ — o limiar (0,05×N) sobre a variação do nº de vetores de referência fixos inativos entre dois retreinos que decide se a reavaliação/retreino usa seleção por INCERTEZA (σ médio do Kriging) ou por APD/convergência. É o único parâmetro do artigo que literalmente liga/desliga o uso da incerteza no mecanismo de model management. (literal: As expected, increase in the value of δ deteriorates the diversity and thus the hypervolume. This is due to fact that frequency of using uncertainty information from Kriging models decreases with the increase in value of δ.; localizador: Sec. III-C.1 (Algorithm 3); Sec. IV-B (sensibilidade, números no suplementar))

**Reprodutível com as camadas:** A sensibilidade de δ poderia ser reproduzida com a camada ⑥ (filme), registrando a cada retreino se ΔVf ≤ δ (branch = convergência/APD, sem uso de incerteza) ou ΔVf > δ (branch = incerteza), variando δ e contando quantas vezes cada branch é escolhido ao longo do orçamento — o artigo original NÃO fornece essas contagens brutas, só a direção qualitativa do efeito sobre diversidade/HV (números ficaram no material suplementar, ausente desta conversão). A camada ③ (sonda) complementaria avaliando se, nos retreinos em que o branch 'incerteza' foi escolhido, o σ médio de fato discrimina pontos de maior erro real (ficha 34) — não testado no artigo. Não há, neste artigo, nenhuma ablação limpa do tipo 'K-RVEA com σ sempre ignorado' (contrafactual σ=0, ficha 15) nem contagem explícita de acionamentos (ficha 45 propriamente dita) — só a evidência indireta da sensibilidade de δ.

**Parâmetros do uso da incerteza:**
  - δ = 0,05 × N (N = número de vetores de referência): limiar sobre ΔVf (variação do nº de vetores de referência FIXOS inativos entre dois retreinos consecutivos). Se ΔVf > δ, os u indivíduos para reavaliação são escolhidos pela MÁXIMA incerteza média do Kriging (σ médio dos k objetivos); caso contrário (ΔVf ≤ δ), são escolhidos pela MÍNIMA APD (convergência) — a incerteza só é 'ligada' quando δ é excedido. No primeiro retreino, APD é sempre usado (incerteza nunca aciona na primeira atualização).
  - u = 5: número de indivíduos reavaliados/adicionados ao arquivo a cada rodada de atualização — não define SE a incerteza é usada, só QUANTOS pontos usam o critério (incerteza ou APD) vigente naquela rodada.
  - wmax = 20: número de gerações em que o Kriging é usado sem retreino entre atualizações — parâmetro de frequência de model management geral, não define o uso da incerteza.
  - NI = 11n − 1 (=109 para n=10): tamanho do DoE inicial e tamanho MÁXIMO do arquivo de treino A1 (mantido fixo para limitar o custo O(n³) do Kriging) — não é parâmetro de incerteza, listado para registro.

#### b4 — CSEA (2019) · A3 · Gestão de confiança · CL - Relação/Classificação · ERR-EMP (erro empírico vs. verdade)

**Mecanismo próprio (análises que o artigo faz sobre o próprio uso da incerteza):**
  - Ablação do componente central de CSEA: remove-se inteiramente o segundo loop (classificação + configuração de confiabilidade + seleção assistida) do Algoritmo 3, mantendo o resto do algoritmo idêntico. Testado em 9 instâncias (DTLZ1/3/5 × M=3,6,10), métrica IGD. É a única ablação de componente do próprio mecanismo relatada no corpo do artigo — mas ablação CONJUNTA (classificação + confiabilidade/incerteza juntas), não isola σ/incerteza isoladamente da classificação em si. (literal: we compare the CSEA with its variant without using the surrogate, denoted by CSEA−, on DTLZ1, DTLZ3, DTLZ5 with 3, 6, and 10 objectives, respectively.; localizador: Sec. III-E, Table I)
  - Diagnóstico direto da acurácia do classificador FNN ao longo da busca: compara a taxa prevista de soluções de categoria II (rp) com a taxa real (rr, calculada a partir da função verdadeira) para os mesmos candidatos, em função do 'Internal Evaluation No.'. Testado (a) com e sem o particionamento balanceado dos dados de treino/teste (ablação de uma técnica de balanceamento, não do mecanismo de incerteza em si) e (b) para M=3, 5, 10 objetivos (sensibilidade ao desbalanceamento de classes). (literal: The rp obtained by CSEA with data partition is compared with the corresponding rr on DTLZ1 with 5 and 10 objectives, respectively, which aims to investigate the influence of class imbalance; localizador: Sec. III-D, Fig. 7)

**Reprodutível com as camadas:** Item 1 (CSEA×CSEA−) NÃO é reproduzível com as 7 camadas — exige rodar uma VARIANTE do algoritmo (sem o segundo loop/surrogate), configuração que não é a de fato executada e registrada pela instrumentação da dissertação (as camadas registram só a execução real de CSEA, com surrogate ativo). Item 2 (Fig. 7, rp×rr) é PARCIALMENTE reproduzível: a camada ③ (predições de classe do surrogate) cruzada com a camada ① (avaliações reais, para obter a categoria verdadeira a cada ponto) permitiria recalcular uma taxa prevista vs. real de categoria II análoga — embora o eixo original do artigo seja o contador interno de avaliações do FNN ('Internal Evaluation No.'), não diretamente a fração do orçamento real ①, então a curva não seria idêntica, só comparável em espírito. A vertente 'sem particionamento balanceado' do Item 2 não é reproduzível pelo mesmo motivo do Item 1 (exige variante do algoritmo). Nenhum dos dois itens fornece, no corpo do artigo, uma contagem explícita de quantas vezes cada região de confiabilidade (R1/R2/R3) foi de fato visitada durante as execuções reais — essa contagem (ficha 45, que cita 'b4' como exemplo de 'fração de FEs em que o surrogate foi usado') teria de ser reconstruída do zero pela dissertação usando a camada ⑥ (filme); não está no artigo.

**Parâmetros do uso da incerteza:**
  - tr (limiar de confiabilidade) = 0,5 × min{rr, 1−rr}, recalculado a cada geração a partir de rr (taxa real corrente de soluções de categoria II no arquivo) — método de 'rescaling' para reduzir a influência do desbalanceamento de classes; é o parâmetro central que define os limites das regiões R1/R2/R3.
  - Fronteiras da configuração de confiabilidade (Fig. 6): R1 = {p2<tr} ∪ {p1<tr AND p2<(1−tr)} (predições confiáveis, usa-se a predição como está); R3 = {p1>1−tr AND p2>tr} (predições sistematicamente invertidas, usa-se a predição INVERTIDA); caso contrário, R2 (nenhuma solução selecionada, Q=∅).
  - Limiares rígidos embutidos na seleção final (Algoritmo 6): L>0,9 para aceitar como categoria II em R1 (linha 11); L<0,1 para aceitar como categoria I/flip em R3 (linha 19) — L é a saída (score) do FNN para cada candidato.
  - gmax (nº máximo de predições do surrogate antes de retreinar) = igual ao usado em K-RVEA e MOEA/D-EGO nas mesmas condições — governa a FREQUÊNCIA com que o classificador (e, portanto, a configuração de confiabilidade) é atualizado, não o limiar de confiança em si.
  - |treino|:|teste| = 3:1 (75%/25%), estratificado para preservar a proporção de categoria I/II em ambos os conjuntos (Algoritmo 5, DataPartition) — a base empírica de onde p1 e p2 (e, portanto, tr) são calculados a cada retreino.
  - H (nº de neurônios ocultos do FNN) = 0,5d, escolhido por sensibilidade (Tabela IV) — não é um parâmetro de USO da incerteza propriamente dito (não define limiares/regiões), mas afeta a capacidade/qualidade do classificador cujos erros alimentam tr; incluído aqui por completude.
  - K (nº de soluções de referência da fronteira de classificação) = 6, escolhido por sensibilidade (Fig. 5) — define QUAIS soluções contam como categoria I/II (a fronteira em si), não o limiar de confiança sobre essa classificação; incluído por completude/proximidade conceitual.

#### b5 — Prob-RVEA / Prob-MOEA/D (+ Hyb-RVEA / Hyb-MOEA/D) (2022) · A2 · Dominância probabilística · GP — Processo Gaussiano/Kriging · VAR-GP (posterior fechada de GP)

**Mecanismo próprio (análises que o artigo faz sobre o próprio uso da incerteza):**
  - Ablação exata do uso da incerteza (a própria ficha 11 da tipologia, nominalmente): Prob-RVEA / Prob-MOEA/D (ranking probabilístico via Monte-Carlo + KDE sobre a posterior gaussiana do Kriging, Eq. 7-14) vs. Gen-RVEA / Gen-MOEA/D (apenas a média posterior, mesma maquinaria evolutiva, mesmo dataset inicial compartilhado) — único fator manipulado é usar ou não o σ na seleção. (literal: Overall, the probabilistic approaches outperformed their generic counterparts, TL, and initial sampling in both HV and RMSE.; localizador: Sec. IV-A)
  - Componente do híbrido: mistura 50/50 de seleção probabilística e genérica (Hyb-RVEA, Hyb-MOEA/D); Hyb-MOEA/D não supera Prob-MOEA/D porque a metade genérica (Gen-MOEA/D) tem desempenho muito ruim — mostra que o mecanismo de mistura não é robusto ao desempenho do componente sem incerteza. (literal: However, we found that Hyb-MOEA/D did not perform better than Prob-MOEA/D. This is because of the extremely poor performance of Gen-MOEA/D in terms of both HV and RMSE.; localizador: Sec. IV-A)
  - σ do modelo em ação ao longo da busca, via proxy do HV no espaço do surrogate: o HV 'acreditado' das abordagens probabilísticas cai ao longo do orçamento porque o mecanismo rejeita deliberadamente soluções de média melhor mas incerteza alta — evidência direta e explicada pelos próprios autores do mecanismo de incerteza operando (não é um efeito colateral não-explicado). (literal: the surrogate HV for TL improved with function evaluations and the probabilistic approaches it gradually decreased. This is because the probabilistic approaches reject solutions with better objective values if they have high uncertainties.; localizador: Sec. IV-A, Fig. 10)

**Reprodutível com as camadas:** Item 1 (Prob×Gen, a ablação exata do σ) é DIRETAMENTE reproduzível com ① + ⑦: comparar o endpoint (ND final reavaliado na função verdadeira) de b5r/b5m (as variantes do roster) contra uma variante 'motor-média' equivalente rodada a partir do MESMO dataset inicial compartilhado — é literalmente a ficha 11 aplicada aos problemas da dissertação. Item 2 (Hyb×Prob, o híbrido não supera o puro quando o genérico é ruim) NÃO é reproduzível com o roster atual, porque este inclui só duas das quatro variantes do artigo (b5m, b5r — pela sigla do pedido de extração e pela ênfase da conclusão do próprio artigo em favor da abordagem puramente probabilística, presumivelmente Prob-MOEA/D e Prob-RVEA, não as híbridas); reproduzir exigiria rodar Hyb-RVEA/Hyb-MOEA/D à parte, fora do roster — mas essa correspondência b5m/b5r=Prob-MOEA/D/Prob-RVEA é inferência deste extrator, não está no texto de b5. Item 3 (trajetória HV-surrogate vs. HV-verdadeiro vs. RMSE a cada 1000 FE) é PARCIALMENTE reproduzível: no regime offline, a dissertação registra a camada ⑦ só no FINAL da busca (não em checkpoints intermediários), então recriar a curva completa exigiria reavaliações reais extras do ND corrente ao longo do orçamento, fora do desenho padrão de 7 camadas; a camada ③ (predições registradas) permite reconstruir o RMSE de acurácia da média em qualquer ponto salvo, mas não substitui a reavaliação real necessária para o HV verdadeiro em checkpoints intermediários.

**Parâmetros do uso da incerteza:**
  - S (nº de amostras Monte-Carlo por indivíduo, extraídas da posterior gaussiana multivariada do Kriging, Eq. 10) = 1000 — Algorithm 1 linha 9; Sec. IV-A item 6 ('Number of samples for Monte-Carlo sampling S = 1000').
  - Bandwidth do KDE (kernel Gaussiano usado para estimar a PDF do critério de seleção — APD em RVEA, PBI em MOEA/D) definido pela regra de Silverman ('Silvermann's rule') — sem valor numérico único fixo, recalculado por amostra a cada seleção.
  - Proporção de mistura do híbrido (Hyb-RVEA, Hyb-MOEA/D) = 50%/50% entre seleção probabilística e seleção genérica (pela média), explicitamente sem parâmetros extras: "no further parameters are required".
  - Não há gate/limiar (tipo δ de confiança ou β de UCB) que module QUANDO usar a incerteza: a seleção probabilística via P_wrong (Eq. 7-9) é aplicada uniformemente a toda a população/subpopulação em cada geração; o único parâmetro numérico próximo é α=2 do APD, que é do RVEA em si (penalização ângulo-distância), não do uso da incerteza.

#### c154 — JES (2022) · O2 · Ganho de informação · GP — Processo Gaussiano/Kriging · VAR-GP (posterior fechada de GP)

**Mecanismo próprio (análises que o artigo faz sobre o próprio uso da incerteza):**
  - Sensibilidade da aquisição a S (nº de amostras de Monte Carlo do conjunto/frente de Pareto ótimos) e p (nº de pontos ótimos retidos por amostra) — os dois hiperparâmetros que definem a fidelidade numérica com que a informação/incerteza é estimada a cada iteração. (literal: there does not appear to be much benefit in using a larger number of Monte Carlo samples S or Pareto optimal points p; localizador: Apêndice L.3, Figs. 14-16)
  - Comparação entre as 4 fórmulas de estimação da entropia condicional (JES-0/LB/LB2/MC) que aproximam a MESMA quantidade teórica (o ganho de informação conjunto) por vias numéricas diferentes — o equivalente, para este mecanismo, a comparar classes de medição da incerteza. (literal: we generally recommend against using the zero-variance estimate if possible; localizador: Apêndice L.6, Figs. 20-21)
  - Decomposição do tempo de parede da aquisição por fase, mostrando que a decomposição em caixas — etapa exclusiva de JES/MES, necessária justamente por condicionarem sobre o conjunto Y* (ou (X*,Y*)) — passa a dominar o custo total conforme M cresce. (literal: the one time box decomposition is the dominant contributor to the wall time for the MES and JES; localizador: Apêndice L.9)
  - Diagnóstico mecanístico de POR QUE a busca guiada por informação difere de uma busca gulosa: JES/MES/PES preferem pontos informativos (que reduzem a incerteza sobre (X*,Y*)) em vez dos pontos de melhor valor esperado — evidenciado pela queda de desempenho quando a recomendação é restrita aos pontos de fato visitados (X_N). (literal: information-theoretic strategies have a tendency to not directly query the best performing points but instead opt for more informative points that will reduce the overall model uncertainty over the optimal points; localizador: Sec. 5.2 / Apêndice L.5)
  - Degradação específica da estimativa JES-0/MES-0 (que assume ruído de observação zero) conforme o nível de ruído injetado cresce de 0% a 20% — diagnóstico de robustez de UMA das 4 variantes de medição da incerteza usada na aquisição. (literal: the MES-0 estimate is noticeable weaker than the rest even after the ad hoc correction described in Appendix E; localizador: Apêndice L.4, Figs. 17-18)
  - Resultado teórico central do artigo: JES é uma cota superior a qualquer combinação convexa de PES (só sobre X*) e MES (só sobre Y*) — formaliza o mecanismo próprio de JES como estritamente mais informativo que seus componentes isolados, por construção. (literal: The JES is an upper bound to any convex combination of the PES and MES acquisition functions; localizador: Sec. 2, Proposição 1)

**Reprodutível com as camadas:** IMPORTANTE antes de mapear qualquer item: a métrica de desempenho deste artigo (log HV discrepancy da Fig. 5 e de quase todos os itens acima) é calculada sobre uma RECOMENDAÇÃO obtida otimizando a média posterior do GP via NSGA2 (camada ③ + otimização extra), NÃO sobre o ND das avaliações reais (camada ①) — a diferença entre essas duas convenções é justamente o objeto do item L.5 (in-sample), que mostra que a convenção ① (a da dissertação) é estruturalmente desfavorável a JES/MES/PES. Item 1 (sensibilidade S,p) e item 2 (comparação de estimadores JES-0/LB/LB2/MC): NÃO reproduzíveis apenas com os dados coletados — ambos mudam QUAL ponto é escolhido a cada iteração, exigindo reexecução com cada config (S, p, ou estimador) registrada na camada ⑤ (manifesto) como um estudo dedicado fora do desenho padrão de 1 config por algoritmo. Item 3 (decomposição do tempo de parede): reproduzível via camada ④ se a dissertação subdividir o tempo de 'busca' de JES em sub-fases equivalentes a amostragem de Pareto/decomposição em caixas/otimização — mais fino que a granularidade padrão de ④. Item 4 (recomendação in-sample x livre): ① fornece diretamente a leitura in-sample (a própria convenção padrão da dissertação); a leitura livre/otimista do artigo exigiria adicionalmente a camada ③ (μ do surrogate) para rodar uma otimização de posterior mean sobre todo X a cada checkpoint — não incluída no desenho padrão, mas computável post-hoc se ③ for gravada com granularidade suficiente. Item 5 (degradação de JES-0/MES-0 com ruído): não reproduzível diretamente — exige reexecuções com ruído artificial injetado em níveis crescentes sobre um problema, fora do desenho padrão; SE a dissertação gravar qual variante de estimador foi usada (camada ⑤), o mesmo padrão poderia ao menos ser verificado nos problemas já ruidosos da bateria via ③ (sonda). Item 6 (Proposição 1): resultado teórico, não uma contagem reproduzível por dados — mas justifica por que, SE JES/MES/PES entrassem simultaneamente no roster, seria esperado JES >= max(PES,MES) em expectativa de informação (não necessariamente em desempenho final).

**Parâmetros do uso da incerteza:**
  - S = 10 — nº de amostras de Monte Carlo dos conjuntos/frentes de Pareto ótimos (X*_s,Y*_s) usadas para estimar a expectativa na informação mútua; sensibilidade testada em {1,5,10,25,50} (Apêndice L.3).
  - p = 10 — nº de pontos de Pareto retidos por amostra, via truncamento guloso pela contribuição ao HV da amostra; sensibilidade testada em {1,5,10,25,50} (Apêndice L.3).
  - Estratégia de estimação da entropia condicional (a 'medição' operacional do ganho de informação): JES-LB (moment-matching, covariância completa, cota inferior — usada como padrão na comparação principal, Fig. 5) vs. JES-0 (assume ruído de observação zero) vs. JES-LB2 (ignora termos fora da diagonal da covariância, cota inferior mais fraca e decomponível por objetivo) vs. JES-MC (Monte Carlo, I=128 amostras-base para o truque de reparametrização).
  - L = 500 — nº de features de Fourier aleatórias usadas para amostrar trajetórias do GP via random Fourier features + regra de Matheron.
  - NSGA2 para amostrar (X*_s,Y*_s) por trajetória: N_pop=100, N_gen=500, N_off=10.
  - NSGA2 para a recomendação final (argmax da média posterior): N_pop=500, N_gen=500, N_off=10, conjunto aumentado com a recomendação da iteração anterior para evitar perder soluções promissoras.
  - Estratégia dinâmica de ponto de referência para truncamento por HV (tanto da amostra de Pareto quanto da recomendação): r̂_n − 0,1|r̂_n|, onde r̂_n é o nadir estimado a partir das observações correntes.

#### c262 — qNEHVI (NEHVI sequencial; qNEHVI-1 = aprox. sample-path RFF) (2021) · O1 · Aquisição exploratória · GP — Processo Gaussiano/Kriging · VAR-GP (posterior fechada de GP)

**Mecanismo próprio (análises que o artigo faz sobre o próprio uso da incerteza):**
  - Comparacao-ilustracao de tres tratamentos da incerteza na fronteira de Pareto sob ruido, com toda a maquinaria (mesmo GP, mesmo problema, mesmo q=1) mantida fixa: NEHVI (integra a distribuicao posterior completa sobre a fronteira), EHVI (ignora o ruido, usa a fronteira observada bruta) e EHVI-PM (usa a media posterior como estimativa pontual). E a ablacao mais direta do mecanismo de incerteza do proprio metodo. (literal: EHVI proceeds to spend its evaluation budget trying to optimize noise, resulting in a clumped Pareto frontier that lacks diversity.; localizador: Sec. 5, Fig. 1)
  - Versao sistematica da mesma ablacao (NEHVI vs EHVI vs EHVI-PM, sob CBD) estendida a 8 problemas, sequencial e em lote (q ate 32), com 100 execucoes -- qNEHVI supera consistentemente qEHVI-PM-CBD, que por sua vez frequentemente supera qEHVI puro. (literal: qNEHVI also consistently outperforms qEHVI-PM-CBD; localizador: Sec. 9.1)
  - Varredura do nivel de ruido do problema (1% a 20%, discussao a 30%) isolando como a vantagem de integrar a incerteza cresce com a magnitude do ruido -- o mecanismo 'em acao': mais ruido, maior o beneficio relativo de NEHVI sobre EHVI/EHVI-PM. (literal: We observe that all methods degrade as the noise level increases, however qNEHVI consistently exhibits excellent performance relative to other methods; localizador: Apendice H.6, Fig. 14)
  - Condicao de controle sem ruido: a formulacao teorica preve que NEHVI colapsa a EHVI quando sigma=0; confirmado empiricamente (qNEHVI ~= qEHVI(-PM-CBD) nos benchmarks sem ruido) -- mostra que usar a maquinaria de NEHVI nao tem custo de desempenho quando a incerteza extra e desnecessaria. (literal: in noiseless environments, NEHVI is equivalent to EHVI; localizador: Sec. 5.1 (teorico); Apendice H.7, Fig. 15 (confirmacao empirica))
  - Ablacao cruzada em um algoritmo hospedeiro diferente (DGEMO): DGEMO puro (fronteira observada bruta) vs. DGEMO-PM (media posterior so na geracao de candidatos) vs. DGEMO-PM-NEHVI (adicionalmente usa qNEHVI, em vez de HVI sob a media, como criterio de selecao do lote) -- isola a contribuicao especifica do criterio qNEHVI quando acoplado a uma maquinaria de geracao de candidatos alheia. (literal: using qNEHVI to integrate over the uncertainty in the Pareto frontier over the previously evaluated points, results in identifying higher quality Pareto frontiers; localizador: Apendice H.10, Fig. 18)

**Reprodutível com as camadas:**   - mecanismo: NEHVI vs EHVI vs EHVI-PM (ablacao direta, Fig. 1, e sua versao sistematica, Sec. 9.1); camada: nao reproduzivel com as camadas -- corresponde ao contrafactual 'sigma=0 online' da ficha 15, nunca executado na dissertacao; exigiria rodar qEHVI/qEHVI-PM como configuracoes adicionais sob o mesmo DoE/orcamento/protocolo do roster.
  - mecanismo: Varredura de nivel de ruido do problema (Apendice H.6); camada: nao reproduzivel -- a bateria congelada tem ruido fixo (ou ausente) por problema; exigiria reexecucao com ruido injetado em multiplos niveis, fora do escopo pos-hoc.
  - mecanismo: Controle sem ruido, sigma=0 (Apendice H.7); camada: camada 1 (avaliacoes reais) diretamente, SE os sinteticos da dissertacao ja forem avaliados sem ruido injetado -- nesse caso o desempenho de qNEHVI ja registrado na bateria congelada corresponde ao regime noiseless investigado aqui, sem necessidade de nova execucao.
  - mecanismo: Ablacao cruzada em DGEMO (DGEMO x DGEMO-PM x DGEMO-PM-NEHVI, Apendice H.10); camada: nao reproduzivel -- exige implementar e rodar variantes aumentadas de um algoritmo (DGEMO-PM, DGEMO-PM-NEHVI) que nao fazem parte do roster tal como executado.

**Parâmetros do uso da incerteza:**
  - N_amostras_qmc: N = 128 amostras quasi-Monte Carlo para a expectativa externa sobre a incerteza da fronteira de Pareto, em todas as funcoes de aquisicao MC (Apendice G.2)
  - sigma_ruido_observacional: Sigma_i (variancia/covariancia do ruido de observacao): assumida CONHECIDA/observada em todos os problemas, EXCETO ABR, onde e inferida junto aos hiperparametros do GP via MAP (Sec. 9)
  - qnehvi1_rff: qNEHVI-1 (variante de amostra unica) aproxima a trajetoria do GP via Random Fourier Features com 500 funcoes de base (Apendice G.2, Sec. 8)
  - kernel_gp: Matern 5/2 ARD, um GP independente por objetivo, hiperparametros via estimacao MAP (Sec. 9)
  - ponto_referencia: r = f_nadir(x) - beta*(f_ideal(x) - f_nadir(x)), com beta = 0,1 (Apendice G.4)
  - poda_dominancia: poda opcional de Xn: remocao de pontos dominados com alta probabilidade, estimada via MC (nota de rodape 4 do artigo); sem limiar numerico explicitado
  - tamanho_lote_q: q em {1, 8, 16, 32} -- interage diretamente com o mecanismo de incerteza via selecao sequencial-gulosa, com amostras-base redesenhadas a cada novo candidato i (Apendice G.2)

#### e103 — IBEA-MS (2023) · A3 · Gestão de confiança · GP — Processo Gaussiano/Kriging · VAR-GP (posterior fechada de GP)

**Mecanismo próprio (análises que o artigo faz sobre o próprio uso da incerteza):**
  - Ablação que isola o efeito do mecanismo adaptativo de troca Kriging↔RBFN: K-IBEA (sempre Kriging, ignora a checagem de confiabilidade) e R-IBEA (sempre RBFN, sem incerteza) comparados contra IBEA-MS (adaptativo, via σ/RMSE do Kriging) em DTLZ1-7 e ZDT1-4,6 (D=10), com Wilcoxon rank-sum e marcação de acerto/erro do mecanismo por problema. (literal: The results are shown in Table I, where the shaded cells represent the adaptive model selection mechanism with a correct decision between the Kriging models and the RBFNs.; localizador: Sec. IV-A, Table I)
  - Sensibilidade do critério de relaxação (parâmetro-gate) que decide a troca de modelo: comparação entre o critério padrão (≥ M−1 de M objetivos julgados 'confiáveis', Eq. 26) e uma variante estrita sem tolerância (IBEA-MS-NT, exige M de M) no problema ZDT4 (D=10, M=2). (literal: A version of the adaptive model selection with no reliability tolerance of the Kriging models (IBEA-MS-NT) is also tested; localizador: Sec. IV-A, Fig. 4)
  - Verificação indireta da correção do mecanismo: taxa de acerto da seleção ambiental sob Kriging e sob RBFN (cada um comparado à seleção sob a função real) por geração, em DTLZ2, DTLZ5, ZDT1, ZDT2 — confirmando que o modelo de maior taxa de acerto em cada problema é o que o mecanismo adaptativo de fato escolhe. (literal: the proportion of the individuals selected by the Kriging and RBFN models in the individuals selected under the real function evaluation is calculated as the correct rate.; localizador: Sec. IV-A, Fig. 5)

**Reprodutível com as camadas:**   - mecanismo: Ablação K-IBEA/R-IBEA/IBEA-MS (Table I); camada: ⑦ (ND final reavaliado, regime offline) para o endpoint de cada variante + reteste de postos por célula — exige implementar e rodar K-IBEA e R-IBEA explicitamente (variantes próprias do artigo-fonte, não algoritmos do roster de 15).
  - mecanismo: Sensibilidade da tolerância de relaxação (IBEA-MS-NT); camada: ⑥ (filme) para contar disparos do flag de troca sob cada critério (M−1 vs. M) + ⑦ para o endpoint — exige implementar a variante NT, que não é um parâmetro exposto na configuração padrão do roster.
  - mecanismo: Correct rate da seleção ambiental (Fig. 5); camada: ③ (predições do surrogate) registrando AMBOS Kriging e RBFN por geração — mesmo o modelo 'não escolhido' — cruzada com ① (avaliação real da mesma população); a sonda fixa padrão (2000 pontos comuns) não cobre isso por definição, pois aqui a checagem é sobre a população evolutiva corrente, não uma…

**Parâmetros do uso da incerteza:**
  - epsilon_limiar_proximidade: ε = 1e-5 — limiar abaixo do qual Dm(i,j) e Em(i,j) são tratados como 'quase zero' e a relação é considerada confiável por definição (Eq. 25)
  - fator_do_intervalo_de_confianca: k=3 desvios-padrão (RMSE) em torno da média predita, [f̃m−3sm, f̃m+3sm], correspondendo a 99,7% de confiança nominal (não validada empiricamente — ver calibracao_do_sigma)
  - criterio_de_relaxacao_do_gate: UF(i,j)=1 requer que pelo menos M−1 dos M objetivos tenham Rm(i,j)=1 (padrão, Eq. 26); a variante de sensibilidade IBEA-MS-NT exige os M de M (sem tolerância)
  - flag_de_troca_de_modelo: switch binário e GLOBAL por geração: switch=1 assim que UF(i,j)=0 é encontrado para QUALQUER par (i,j) na população — não há score contínuo nem troca parcial/gradual, é tudo-ou-nada Kriging→RBFN para a geração inteira

#### e7 — EDN-ARMOEA (2022) · O3 · Aprendizado ativo / reparo · NN — Rede Neural · DISC-ENS (discordância entre predições)

**Mecanismo próprio (análises que o artigo faz sobre o próprio uso da incerteza):**
  - A ablação MAIS DIRETA do critério de seleção que governa quando o algoritmo usa σ: GP-ARMOEA (estratégia balanceada, alterna via gate δ) vs. GPC-ARMOEA (NUNCA usa σ — só distância ao ideal) vs. GPD-ARMOEA (SEMPRE usa σ — máxima incerteza média). Mesma maquinaria (GP + AR-MOEA + k-means) nos três, isolando o efeito do critério. (literal: GP-ARMOEA achieves the best performance in terms of convergence and diversity on eight out of the sixteen test instances, while GPC-ARMOEA and GPD-ARMOEA perform best on DTLZ2 and WFG1, respectively.; localizador: Sec. IV-B, Table I)
  - Sensibilidade à taxa de dropout (1−pI, 1−pR) — o hiperparâmetro que literalmente define a magnitude estocástica de σ̂² produzida pela Eq. (11); medida via IGD fim-a-fim, não via qualidade direta do σ. (literal: The error bars of the mean IGD of EDN-ARMOEA over 1 − pI and 1 − pR is plotted in Fig. S5... indicating that a dropout probability between 0.1 and 0.2 for both input and hidden layers should work well for most problems.; localizador: Sec. IV-F.3; Fig. S5 (Supplementary))
  - Sensibilidade do gate δ, medida diretamente como a FREQUÊNCIA com que o ramo 'diversidade/incerteza' é acionado (contagem de decisões, não só o IGD resultante) — o experimento mais próximo, na literatura, de uma contagem de acionamentos do mecanismo de incerteza (ficha 45, que cita 'e7' explicitamente como exemplo canônico na própria tipologia). (literal: an increase in delta decreases the frequency of selecting the uncertain solutions for the real FE... The frequency decreases quickly as delta increases, and the effect of delta on the frequency is different for different problems.; localizador: Sec. III-B; Sec. IV-F.5, Fig. S7 (Supplementary))
  - Comparação de MAE (acurácia da média) e STD de σ̂² (informatividade da incerteza) entre EDN, GP e HeE, sob os mesmos dados de treino — valida se o mecanismo de incerteza do próprio EDN (dropout estocástico) produz um σ mais útil que os dois concorrentes. (literal: the mean STD of ŝ obtained by GP is the smallest... indicating that GP fails to properly predict the uncertainty for high-dimensional problems when the number of training data is small. By the contrast, the proposed EDN is still able to provide the uncertainty information for high-dimensional…; localizador: Sec. IV-D)

**Reprodutível com as camadas:** Item 1 (Table I, ablação GP-ARMOEA×GPC×GPD): NÃO reproduzível — exige rodar duas variantes do algoritmo (só-convergência, só-incerteza) que não fazem parte da execução real de EDN-ARMOEA no roster da dissertação; SE fossem rodadas, o resultado seria comparável via camada ① (endpoint). Item 2 (sensibilidade a pI/pR): NÃO reproduzível fim-a-fim (exige re-treinar com múltiplas taxas de dropout, fora do desenho de execução única); mas a QUALIDADE do σ resultante para a taxa REALMENTE usada (0,1/0,1) é diretamente reproduzível via camada ③ (sonda), cruzando as fichas 33-34 (calibração/discriminação do σ). Item 3 (frequência de acionamento do gate δ): a versão MAIS diretamente reproduzível de todo o bloco — a camada ⑥ (filme, 1 evento por linha) permitiria, PARA A EXECUÇÃO REAL com δ=0,08 de fato usado, contar exatamente quantas vezes cada ciclo de retreino escolheu o ramo convergência vs. o ramo diversidade/incerteza, algo que o PRÓPRIO ARTIGO nunca reporta como número absoluto (só a direção qualitativa do efeito de δ na Fig. S7, ausente deste corpus) — essa contagem exata teria que ser inteiramente reconstruída do zero pela dissertação a partir do log de decisões da execução real de EDN-ARMOEA. Item 4 (MAE/STD comparativo EDN×GP×HeE): a parte referente à QUALIDADE PRÓPRIA de EDN-ARMOEA (MAE e STD de σ̂² nos próprios dados) é diretamente reproduzível via camada ③ (sonda: RMSE = ficha 31; magnitude/informatividade do σ ≈ fichas 33-34); a comparação SIMULTÂNEA com GP e HeE sob o mesmo split de treino exigiria rodar variantes-surrogate específicas fora do desenho padrão de execução única por algoritmo do roster.

**Parâmetros do uso da incerteza:**
  - δ (delta) = 0,08 — o parâmetro CENTRAL do gate: compara a queda na proporção de pontos de referência válidos (r_{i-1} − r_i) entre gerações consecutivas contra δ; se a queda excede δ, o ramo 'diversidade' (seleciona pela incerteza média máxima em cada cluster) é escolhido em vez do ramo 'convergência' (distância euclidiana mínima ao ideal); sensibilidade testada em Fig. S7 (Supplementary, ausente deste corpus) via a frequência resultante de acionamento do ramo diversidade.
  - itertest (nº de passagens estocásticas do dropout no teste) = 100 — fixo em TODOS os experimentos; é o parâmetro mais diretamente análogo ao 'nº de passagens do dropout' citado como exemplo no próprio CARTÃO, mas NUNCA tem sensibilidade testada neste artigo (só delta, pI/pR, J/K, itertrain/iterr e k são varridos).
  - pI, pR (probabilidade de RETENÇÃO de neurônios no dropout, camada de entrada e ocultas) = 0,9 / 0,9 (isto é, taxa de dropout 0,1/0,1) — determina a magnitude estocástica de σ̂² (Eq. 7/11); sensibilidade testada em Fig. S5, faixa recomendada 0,1-0,2 de taxa de dropout, sem justificativa teórica declarada.
  - k (nº de soluções avaliadas pela função real por geração / nº de clusters do k-means) = 5 — determina QUANTOS pontos por ciclo de retreino são escolhidos sob o critério ativo (convergência OU diversidade, todo o lote sob o mesmo critério na mesma geração); sensibilidade testada entre k=3 e k=5 (Fig. S6); não fica claro se k=1 (puramente sequencial) fez parte da varredura.


---

# Anexo 9 — As 197 análises 'novas' e seu destino (índice do JSON consolidado `novas_full.json`)

| # | id | Nome sugerido pelo extrator | Localizador | Ficha(s) de destino |
|---|---|---|---|---|
| 0 | b1 | EGO x busca aleatória -- múltiplo de avaliações para vitória/empate (single-objective) | Sec. III-B; Table I; Table II | 72 |
| 1 | b1 | Comparação heterogênea com resultado publicado de outro algoritmo (orçamento não pareado) | Sec. III-B; Table III | 76 |
| 2 | b13 | Comparação treino × validação (k-fold CV) entre dois candidatos a surrogate (diagnóstico de overfitting) | Sec. 5.1, Tables 2 e 3 | 68 |
| 3 | b14 | Robustez de mecanismos de seleção ambiental (dominância+crowding vs. indicador Iε+) a ruído gaussiano… | Sec. 2.2.2, Table 1 | 74 |
| 4 | b14 | Sensibilidade a hiperparâmetros próprios do algoritmo (capacidade do pool de modelos Smax; período de… | Sec. 4.2, Fig. 2 | 65 |
| 5 | b14 | Ablação do otimizador híbrido (alternância de seleção ambiental IBEA/NSGA-II por paridade de geração) | Sec. 4.4, Table 3 | 67 |
| 6 | b14 | Ablação da amostragem de preenchimento adaptativa por estágio (early-only / late-only / sem controle de… | Sec. 4.5, Table 4 | 67 |
| 7 | b15 | Sensibilidade da HV final ao numero de pontos indutores (M_ind) do Deep GP esparso | Apendice B.2, Fig. 2 | 65 |
| 8 | b15 | Sensibilidade da HV mediana ao tamanho do pool de candidatos na triagem em dois estagios | Apendice E, Table 6 | 65 |
| 9 | b15 | Ablacao da estrutura do surrogate: Deep GP heterocedastico x GP esparso homocedastico x GP raso RBF | Apendice E.1, Table 7 | 68 |
| 10 | b15 | Sensibilidade da HV e da calibracao (ECE) ao numero de categorias de rank K do classificador | Apendice F, Fig. 6 | 65 |
| 11 | b15 | GP independente por objetivo x GP com correlacao entre objetivos (coregionalizacao linear) | Apendice G, Table 8 e Fig. 7 | 68 |
| 12 | b15 | Custo de re-tuning de hiperparametros ao transferir para uma nova tarefa (protocolo de 2 estagios) | Apendice G.1, Table 9 | 65, 69 |
| 13 | b15 | Fidelidade do proxy de ganho de informacao (MC-Dropout) contra uma referencia gold-standard num problema de… | Apendice H, Fig. 8 | 70 |
| 14 | b15 | Estimacao empirica do fator de fidelidade da aquisicao (rho) e das constantes do limite teorico de HV | Apendice J.7, Table 10 | 70 |
| 15 | b15 | Aquisicao aprendida on-line x combinacao linear fixa (Static-EHVI) sobre as mesmas features | Apendice L.6, Table 12 e Fig. 9 | 67 |
| 16 | b3 | Sensibilidade ao tamanho do lote de reavaliação (u) no K-RVEA | Sec. IV-B, parágrafo sobre parâmetros adicionais (u e… | 65 |
| 17 | b3 | Sensibilidade à frequência de retreino do Kriging (wmax) | Sec. IV-B (menção ao estudo); Sec. V Conclusions (achado… | 65 |
| 18 | b3 | Estudo de caso real (polimerização de acetato de vinila, 3 obj.) | Sec. IV-B, último parágrafo antes de Sec. V | 75 |
| 19 | b4 | Sensibilidade ao nº de soluções de referência K (fronteira de classificação) | Sec. III-B, Fig. 5 | 65 |
| 20 | b4 | Sensibilidade ao nº de neurônios ocultos H do FNN | Sec. IV-D, Table IV | 65 |
| 21 | b8 | Sensibilidade ao parâmetro de amostragem aleatória da estratégia de incerteza (phi) | Sec. IV-B, Fig. 8(a) | 65 |
| 22 | b8 | Sensibilidade ao limiar de pontos influentes do modelo substituto (tau) | Sec. IV-B, Fig. 8(b) | 65, 66 |
| 23 | b9 | Sensibilidade ao orçamento do MO barato interno (nº de avaliações do NSGA-II) | Sec. 5.1 ("Cheap MO solver") | 65 |
| 24 | c1 | Ilustração 1D do ganho de acurácia do modelo com gradiente (poucos dados) | Sec. III-A-2, Fig. 2 | 71 |
| 25 | c1 | Efeito isolado do framework de aquisição em lote, controlando o modelo (GP), pequena escala | Sec. IV-A-1 | 52 |
| 26 | c1 | Ablação do tipo de surrogate (BNN vs GP) sob poucos dados/baixa dimensão | Sec. IV-A-2 | 68 |
| 27 | c1 | Ablação da informação de gradiente (Sobolev training) sobre o surrogate, pequena escala | Sec. IV-A-3 | 68 |
| 28 | c1 | Efeito isolado do framework de aquisição em lote, controlando o modelo (GP), alta dimensão | Sec. IV-B-1 | 52 |
| 29 | c1 | Ablação do tipo de surrogate (BNN vs GP) sob muitos dados/alta dimensão — escalabilidade | Sec. IV-B-2 | 68 |
| 30 | c1 | Ablação da informação de gradiente (Sobolev training) sobre o surrogate, alta dimensão | Sec. IV-B-3 | 68 |
| 31 | c1 | Sensibilidade ao tamanho do lote (parâmetro de paralelismo k) sobre a frequência de retreino | Sec. IV-C, Fig. 6 | 69, 64 |
| 32 | c1 | Fronteira aproximada entre algoritmos sem frente verdadeira conhecida (caso real) | Sec. IV-D, Fig. 8 | 54 |
| 33 | c1 | Algoritmo híbrido por ensemble simples (GP+BNN) para pequena e grande escala | Sec. IV-A-2 (texto corrido, após a discussão da Table I) | 67 |
| 34 | c10 | Custo estrutural de edição (distância média entre nós) para seleção de solução final na frente | Eqn. (5); Fig. 5; Fig. S4 (Supplementary Materials, só… | 23 |
| 35 | c10 | Comparação conceitual do framework MOEA-RSFMMA vs. SP-RV-MOEANet (material suplementar) | Sec. SP-RV-MOEANet / The Framework; Supplementary Materials… | 76 |
| 36 | c10 | Sensibilidade ao tipo de remoção nos ataques nodais (aleatória vs. betweenness) (material suplementar) | Sec. Experiments on synthetic networks (após a discussão de… | 23 |
| 37 | c10 | Análise de desempenho de soluções representativas em redes sintéticas (material suplementar) | Sec. Experiments on synthetic networks (fim do parágrafo… | 75 |
| 38 | c10 | Análises intuitivas da estrutura das redes reais otimizadas (material suplementar) | Sec. Experiments on real-world networks (após Table… | 75 |
| 39 | c100 | Custo do método de otimização da aquisição (gradiente exato vs. aproximado vs. livre) | Sec. 4.2, Fig. 2a | 69 |
| 40 | c100 | Acurácia da estimativa Monte Carlo do qEHVI vs. EHVI analítico | Fig. 5a (Apêndice — ausente deste corpus); citado na Sec.… | 70 |
| 41 | c100 | Acurácia do gradiente amostral do qEHVI vs. gradiente exato do EHVI (M=3) | Fig. 5b (Apêndice — ausente deste corpus); citado na Sec.… | 70 |
| 42 | c100 | Escalabilidade do tempo de computação do qEHVI com o tamanho do lote q (saturação de hardware) | Fig. 11 (Apêndice — ausente deste corpus); citado na Sec.… | 69, 64 |
| 43 | c100 | Benchmarks sintéticos adicionais (conteúdo não descrito) | Apêndice F.1 (ausente deste corpus); citado na Sec. 5 | 1 |
| 44 | c100 | qEHVI em espaços de objetivos de alta dimensão via decomposição aproximada | Apêndice F.4 (ausente deste corpus); citado nas Sec. 3.3 e 6 | 7 |
| 45 | c106 | Ablacao da estrutura de covariancia do GP multiobjetivo (independente x dependencia nao-separavel) | Sec. 6.1, p. 17; Sec. 6.2, p. 18-19; Sec. 7 (Conclusions… | 68 |
| 46 | c106 | Custo de estimacao via REML por numero de parametros de covariancia (independente x dependente) | Sec. 6.1, p. 17 (7 parametros); Sec. 6.2, p. 18-19 (26… | 69 |
| 47 | c106 | Ablacao da estrutura de covariancia do GP multiobjetivo (independente x dependencia nao-separavel) | Sec. 6.1, p. 17 | 68 |
| 48 | c107 | Fidelidade numérica da aproximação do critério de aquisição (EIHV exato x aproximado) | Sec. III-E2, Figs. 10-11 | 70 |
| 49 | c107 | Comparação informal LOO x log-pseudo-verossimilhança como critério de seleção de modelo | Sec. II-C | 70 |
| 50 | c107 | MCMC x Monte Carlo ingênuo para a verossimilhança marginal (aparte do Apêndice) | Appendix | 70 |
| 51 | c122 | Custo agregado (CPU) de gerenciar os surrogates, comparado entre subconjunto de algoritmos | Sec. IV-C, Table VII | 69 |
| 52 | c122 | Sensibilidade multiparâmetro do surrogate/evolução (U, D, N*, Qmax, Tmax, γ) medida no IGD final | Sec. IV-D, Fig. 7 | 65 |
| 53 | c123 | Discussão qualitativa de sensibilidade a θ_PBI e H (não tabulada) | Sec. III-B-6 (Discussion on the arbitrariness of the… | 65 |
| 54 | c131 | Ablacao dos componentes de busca do proprio algoritmo (n. de regioes de confianca, tolerancia a falha,… | Sec. 5.2 ('Ablation study'), Fig. 4 | 67 |
| 55 | c131 | Fidelidade da amostragem posterior aproximada (RFF) vs. exata para Thompson Sampling, por dimensao | Apendice A.1 ('RFFs for fast posterior sampling'), Fig. 6 | 70 |
| 56 | c141 | Interpretação de engenharia das soluções ND vs. solução-base (diagramas de tensão equivalente) | Sec. Results and discussions (BWBUG), Fig. 14 | 75 |
| 57 | c149 | Curva de escalabilidade por tamanho de lote (batch size): HV e tempo em função de S | Sec. 3, Fig. 1 | 68, 64 |
| 58 | c149 | Curva de escalabilidade por tamanho de lote (batch size): HV e tempo em função de S | Sec. 5.1, Fig. 3 | 68, 64 |
| 59 | c149 | Curva de escalabilidade por tamanho de lote (batch size): HV e tempo em função de S | Sec. C.3, Fig. 13 | 68, 64 |
| 60 | c149 | Robustez a ruído irredutível via peso (α, β) do termo aleatório na aquisição | Sec. 5.5, Fig. 6 | 74 |
| 61 | c149 | Robustez a ruído irredutível via peso (α, β) do termo aleatório na aquisição | Sec. 5.5, Fig. 7 | 74 |
| 62 | c149 | Regret de Pareto cumulativo em lote (batch) × iteração — métrica alternativa à trajetória de IGD+/HV | Sec. B.1.3 (método); Figs. 11, 15(c), 16(c), 18(c)… | 64 |
| 63 | c154 | Sensibilidade da aquisição aos hiperparâmetros de estimação (nº de amostras MC S; nº de pontos ótimos p) | Apêndice L.3, Figs. 14, 15, 16 | 70 |
| 64 | c154 | Comparação das estratégias de aproximação numérica da entropia condicional (JES-0/LB/LB2/MC; MES-0/LB/LB2/MC) | Apêndice L.6, Figs. 20, 21 | 70 |
| 65 | c154 | Comparação entre variantes gulosas e cientes de ruído dos métodos por melhoria (ParEGO x NParEGO; EHVI x… | Apêndice L.7, Fig. 22 | 74 |
| 66 | c154 | Recomendação restrita às amostras visitadas (X_N) vs. otimizada sobre todo X — custo da avaliação 'in-sample'… | Sec. 5.2 (discussão) e Apêndice L.5, Fig. 19 | 73 |
| 67 | c154 | Hipervolume generalizado (GHV) por região do espaço de objetivos — desempenho local em vez de global | Sec. 5.2, Fig. 6 | 55 |
| 68 | c154 | Robustez do ranking sob reparametrização do espaço de objetivos — hipervolume generalizado em muitas… | Sec. 4 (texto) e Apêndice L.8, Figs. 26-29 | 55 |
| 69 | c154 | Curvas de nível da aquisição em problema de brinquedo single-objective — comparação visual PES x MES x JES x… | Apêndice J, Figs. 7-11 | 71 |
| 70 | c214 | Sensibilidade de PFES ao nº de amostras MC da Pareto-frontier (|PF|) | Sec. 6.1, Fig. 4 (texto); anunciado em Sec. 3.2.1 | 70 |
| 71 | c217 | Sensibilidade dos parâmetros próprios dos algoritmos BASELINE (não de PC-SAEA) | Sec. 4.1, Fig. 5 | 65 |
| 72 | c217 | Ablação do tipo de surrogate dentro do mesmo framework (regressão × classificação × comparação par-a-par) | Sec. 4.4, Table 6 | 68 |
| 73 | c217 | Sensibilidade à fração de pareamento treino best/worst (N/4 × N/3 × N/2) | Sec. 4.5, Table 7 | 65 |
| 74 | c222 | Robustez da qualidade e do custo ao número de amostras Monte-Carlo (S) do termo de entropia | Sec. 5.2 (parágrafo 'MESMO vs. State-of-the-art', entre a… | 70 |
| 75 | c238 | Contornos da função de aquisição no espaço de projeto (EI exato × EIM fechado) | Sec. IV-E, Fig. 8 | 71 |
| 76 | c238 | Prova/ilustração das propriedades de monotonicidade da aquisição em relação a μ e σ (N1, N2) | Sec. III-C, Sec. IV-C, Figs. 6-7 | 71 |
| 77 | c24 | Superfície do surrogate vs função verdadeira (inspeção visual pontual) | Sec. IV-A, Fig. 2 | 71 |
| 78 | c241 | Sensibilidade ao nº de gerações da busca no surrogate (gmax) | Sec. III-B, Table I | 65 |
| 79 | c241 | Ablação da separação busca-de-candidatos/gestão-do-surrogate (EMMOEA × EMMOEA-IP) | Sec. III-C, Table II | 67 |
| 80 | c241 | Ablação do indicador de desempenho próprio vs. matriz EIM (EMMOEA × EMMOEA-EIM) | Sec. III-D, Table III | 67 |
| 81 | c241 | Exemplo numérico ilustrativo do conflito entre EI por objetivo (motivação, Fig. 1) | Sec. I (Introdução), Fig. 1 | 71 |
| 82 | c250 | Economia de avaliacoes reais ate convergencia sob parada adaptativa (custo em chamadas de simulacao, sem… | Sec. 4.1 (Fig. 4) e Sec. 4.3, Table 3 (p. 031401-5 a… | 72 |
| 83 | c261 | Decomposição analítica (não-empírica) do custo computacional por fase (ajuste do GP, maximização da EI,… | Sec. V-D.1, p.10-11 (texto principal); Supplementary Sec.… | 69 |
| 84 | c261 | Escalabilidade do tempo de CPU com o tamanho do lote (batch size q) | Sec. V-D.2, p.11, Fig. 6 | 69, 64 |
| 85 | c261 | Sensibilidade ao ponto de referência z* (Utopian point) da decomposição/Tchebycheff | Supplementary Sec. III-A.1, p.5-6, Fig. 5 (Supplementary) | 81 |
| 86 | c261 | Ablação da estratégia de seleção de lote (submodular-greedy × aleatória × k-means) | Supplementary Sec. III-B.1, p.6-7, Table I (Supplementary) | 67 |
| 87 | c261 | Ablação do otimizador interno usado para maximizar a EI (MOEA/D-GR × MOEA/D-DE) | Supplementary Sec. III-B.2, p.7, Table II (Supplementary) | 67 |
| 88 | c261 | Ablação da estratégia adaptativa do ponto de referência z* + comparação pareada sob seleção k-means comum | Supplementary Sec. IV-A/IV-B, p.9-10, Table IV… | 67 |
| 89 | c262 | CBD x IEP -- escalabilidade do custo de otimizacao da aquisicao com o lote q | Fig. 2 (Sec. 6); Fig. 6 (Apendice H.2); derivacao teorica… | 69 |
| 90 | c262 | Controle sem ruido -- placar sob sigma=0 | Apendice H.7, Fig. 15 | 74 |
| 91 | c262 | Escalabilidade em numero de objetivos (M=5) | Apendice H.8, Fig. 16 | 7 |
| 92 | c267 | Complexidade computacional teórica (Big-O) do SAMOEA-TL2M | Sec. IV (parágrafo de abertura da Seção IV, antes de IV-A);… | 69 |
| 93 | c276 | Validação empírica da garantia teórica de corretude (β_t exato do Teorema 1, ε=0) | Sec. 7.4, Fig. 6 | 70 |
| 94 | c276 | Speedup de runtime ε-PAL vs PAL por ε e por |E|, sob custo de avaliação assumido (0 min / 30 min) | Sec. 7.5, Fig. 7 | 69 |
| 95 | c29 | Sensibilidade ao vetor-limiar de aspiração (exploração uniforme vs. localização) | Sec. 7, ¶3-4 (problem 10, Fig. 3) e ¶ sobre Fig. 6 (problem… | 71 |
| 96 | c29 | Viés do modelo estatístico por paisagem quase-plana com picos (localização do limiar na direção errada) | Sec. 7, ¶ sobre Fig. 8 / problem (13), p. 91-92 | 71 |
| 97 | c29 | Equivalência de avaliações — quantas avaliações o piso precisa para igualar a qualidade do assistido | Sec. 7, último parágrafo, p. 92 | 72 |
| 98 | c48 | Ablação da arquitetura do classificador substituto (modelo único × ensemble completo × ensemble podado) | Sec. 4.2, Table 1 | 67 |
| 99 | c48 | Sensibilidade do hiperparâmetro de poda do ensemble (Q) medida na acurácia/erro do classificador | Sec. 4.4.2, Fig. 4 | 65 |
| 100 | c49 | Ilustração da 1ª etapa de pré-filtragem por hipercone (preferência de objetivo) | Sec. 3.1, Fig. 2 e Fig. 3(a)-(b) | 79 |
| 101 | c49 | Ilustração da 2ª etapa de pré-filtragem por ordenação não-dominada com incerteza | Sec. 3.1, Fig. 3(b)-(c) | 79 |
| 102 | c49 | Efeito da preferência de objetivo (ponto de referência) entre iterações — estudo de caso GAA | Sec. 4, Fig. 5(a)-(c) | 75 |
| 103 | c49 | Efeito da tolerância de incerteza do DM sobre o conjunto mostrado — estudo de caso GAA | Sec. 4, Fig. 5(d) | 75 |
| 104 | c50 | Seleção de kernel do GP por validação cruzada | Sec. 3, p.8 (antes da Eq. 4) | 68 |
| 105 | c50 | Probabilidade de dominância no espaço de objetivos — mapa (dim. 1) | Sec. 5.1, Fig. 4a, p.16 | 75 |
| 106 | c50 | Probabilidade de dominância no espaço de objetivos — seleção de operating point (dim. 2) | Sec. 5.1, Fig. 5a-b, Eq. 17, p.17-18 | 75 |
| 107 | c50 | Probabilidade de dominância no espaço de objetivos — extensão 3D/carga (dim. 3) | Sec. 6, Fig. 8, p.22-23 | 75 |
| 108 | c59 | Acurácia da média: modelo determinístico vs. modelo com UQ, em treino/teste (pré-treino) | Sec. 4.1.1, Table 1, p. 13–14 | 31 |
| 109 | c59 | Comparação qualitativa da geometria/aerodinâmica da solução otimizada | Sec. 4.2, Figs. 10-11, p. 18–20 | 75 |
| 110 | c59 | Sensibilidade da calibração do σ aos hiperparâmetros de treino do modelo probabilístico (peso KL β, nº de… | Appendix B, p. 26–27 | 33 |
| 111 | c59 | Comparação qualitativa da geometria/aerodinâmica da solução otimizada | Appendix C.4.2, Fig. 5, p. 32 | 75 |
| 112 | c65 | Validação numérica de POPmin (aproximação) contra POPtrue (exato, combinatorial) em exemplos ilustrativos | Sec. 3.2, Table 1 (exemplos da Fig. 2a-b) | 70 |
| 113 | c65 | Estudo de caso de engenharia RBDO mono-objetivo com refinamento sequencial de acurácia (treliça de 2 barras) | Sec. 6.1, Figs. 11-12 | 75 |
| 114 | c66 | Validação visual do modelo-alvo tunado (predito × real, downstream) | Sec. IV-B-1), Fig. 3 | 31 |
| 115 | c66 | Caso real dinâmico: reotimização periódica vs. modelo estático (deriva do processo) | Sec. IV-B-2), Fig. 4 | 75 |
| 116 | c75 | Convergência SO ilustrativa (pré-MOO): krig+E[I] sequencial vs GA direto | First Example and Some Basic Searches, Fig. 6 (p. 883-884) | 26 |
| 117 | c81 | Distribuições marginais dos objetivos (QED/SAS/afinidade) das moléculas geradas, com vs. sem RL | Sec. 4.2.2, Fig. 3 | 75 |
| 118 | c81 | Ablação dos componentes auxiliares da recompensa (reward boost, penalidade de diversidade, corte dinâmico) | Appendix B.6; Table 2 (linhas 'Ours W/O') | 67 |
| 119 | c81 | Validação real de candidatos via docking + MD + perfil ADMET contra inibidor conhecido de EGFR | Sec. 4.2.4, Fig. 4; Appendix C.6 | 75 |
| 120 | c81 | Validação da afinidade de ligação via Free Energy Perturbation (FEP) para os 3 candidatos selecionados | Appendix C.5, Table C.5 | 75 |
| 121 | c81 | Generalização a dois novos grupos de propriedades quânticas reais no QM9 (HOMO-LUMO /… | Appendix C.3, Table C.4 | 75 |
| 122 | c81 | Generalização do framework a outras arquiteturas de difusão (GeoLDM, GFMDiff) | Appendix C.8, Table C.6 | 75 |
| 123 | c81 | Análise de correlação entre os 3 objetivos para justificar a independência assumida na agregação… | Appendix C.1, Table C.1 | 80 |
| 124 | c81 | Galeria dos 8 melhores candidatos moleculares gerados por dataset, selecionados por score composto de… | Appendix C.7, Fig. C.3 | 75 |
| 125 | c82 | Sensibilidade à razão de tempos de avaliação τ entre objetivo lento e rápido | Sec. 4.4 (parágrafo de transição entre Table 1 e Table 2) | 7 |
| 126 | c82 | Ablação do esquema de transferência como um todo (dois GPs independentes, sem co-surrogate nem seleção) | Sec. 4.5 (Ablation Studies), Tables 4 e 5 | 67 |
| 127 | c82 | Ablação do tipo de modelo do co-surrogate (GP vs. regressão polinomial) | Sec. 4.5, Tables 4 e 5 | 68 |
| 128 | c91 | Caso real de engenharia com aplicação única do método (sem baseline algorítmico nem frente verdadeira… | Sec. 4.4, Fig. 17, Table 6 | 75 |
| 129 | c91 | Validacao fisica qualitativa do design via campo de escoamento (ondas de choque, contornos de pressao) | Sec. 4.4, Figs. 18-21 | 75 |
| 130 | c91 | Curvas de desempenho ao longo de uma faixa continua de condicao operacional (envelope operacional) | Sec. 4.4, Figs. 22-23 | 75 |
| 131 | c97 | RMSE individual dos membros do ensemble por saída (variabilidade entre bootstraps) | Sec. 6.1 [38], Figs. 4, 5, 6 | 36 |
| 132 | c97 | RMSE do ensemble agregado em função do número de membros (C1) | Sec. 6.1 [38]-[39], Fig. 7 | 36 |
| 133 | c97 | Convergência da incerteza (CV do RMSE) com o tamanho do ensemble — escolha de N=30 | Sec. 6.1 [39], Figs. 8, 9, 10 | 36 |
| 134 | c97 | Sensibilidade do NSGA-II a tamanho de população e número de gerações | Sec. 6.2 [40] | 65 |
| 135 | c97 | Fronteiras de Pareto por nível de confiabilidade (múltiplas realizações × chance-constrained) | Sec. 6.3 [42]-[44], Figs. 11, 12, 13, 14; equivalência… | 79 |
| 136 | c97 | Sensibilidade da fronteira de Pareto ao número de membros do ensemble (5/10/15/30) | Sec. 6.4 [48], Fig. 18 | 79 |
| 137 | e1 | Escalabilidade sintética do custo de decomposição em células (tempo, nº de células) vs. nº de objetivos e… | Sec. 3.4, Fig. 5 | 69 |
| 138 | e1 | Verificação de corretude da fórmula fechada da EI/PoI multiobjetivo contra implementação de referência e… | Sec. 3.3.1 | 70 |
| 139 | e102 | Ablação da estratégia de seleção de subproblemas (ASS vs. seleção aleatória) | Sec. VI-A, Table IX e Table X (Supplemental File — não… | 67 |
| 140 | e102 | Ablação do modelo colaborativo (CoMOGP) vs. GPs independentes por subproblema | Sec. VI-B, Table IX (Supplemental File — não incluída neste… | 68 |
| 141 | e102 | Ablação da função de aquisição (ALCB de γ adaptativo vs. LCB de γ fixo) | Sec. VI-C, Table IX (Supplemental File — não incluída neste… | 67 |
| 142 | e102 | Sensibilidade ao parâmetro η do grau de resolução (solving degree) na seleção de subproblemas | Sec. VI-D, Fig. 9 | 65 |
| 143 | e103 | Análise de complexidade computacional assintótica (Big-O) por fase, entre 7 algoritmos | Sec. III-B; Table S.I (material suplementar) | 69 |
| 144 | e103 | Escolha do motor evolutivo de base para o framework offline (piloto) | Sec. IV (abertura); Table S.II (material suplementar) | 67 |
| 145 | e103 | Robustez a hiperparâmetros do surrogate e ao dataset offline inicial | Sec. IV (abertura); Tables S.III e S.IV (material… | 65 |
| 146 | e103 | Robustez ao método de amostragem do dataset offline (LHS × aleatória) | Sec. IV-B (parágrafo sobre aplicação a problemas reais);… | 77 |
| 147 | e104 | Ablação da amostragem por indicador de desempenho vs. amostragem aleatória (RVMM-RI) | Sec. IV-G; Tables SIV-SV (material suplementar, não visível… | 67 |
| 148 | e104 | Sensibilidade aos hiperparâmetros k (peso da incerteza na AUCB), Nv (nº de vetores de referência adaptativos)… | Sec. IV-A (menção); Figs. S1-S3 (material suplementar, não… | 65, 66 |
| 149 | e104 | Comparação de tempo de execução (runtime) entre os oito algoritmos | Sec. IV-C (menção); Seção III do material suplementar (não… | 47 |
| 150 | e16 | Ablação do componente evolutivo interno do híbrido assistido (troca de EA e do otimizador de aquisição) | Sec. Further discussion; Supplementary Discussion… | 67 |
| 151 | e17 | Verificacao visual da acuracia da media do GP num problema de brinquedo 2D | Sec. III-B, Fig. 3(a-d) | 71 |
| 152 | e17 | Comparacao visual do front 2D projetado entre algoritmos, sem frente verdadeira conhecida | Sec. IV-A, Fig. 7(b) | 75 |
| 153 | e17 | Restricao de desigualdade probabilistica (gate via posterior de GP) num problema de brinquedo | Sec. III-C, Fig. 4 | 23 |
| 154 | e17 | Preferencia (subdominio truncado) vs. restricao probabilistica vs. irrestrito no problema real AWA | Sec. IV-B, Fig. 8 | 23 |
| 155 | e21 | Falhas de convergência do treino do UQ por dataset | Results, 'Surrogate model and UQ performance' (texto… | 58 |
| 156 | e21 | Distribuição do valor real dos top-K por método vs. corte | Fig. 4; Results, 'Optimization results of single-objective… | 43 |
| 157 | e3 | Heterogêneo × homogêneo — ablação do mecanismo de diversidade do ensemble | Sec. V-F, Table III (linha HoE-MOEA) | 68 |
| 158 | e3 | Sensibilidade ao método de agregação das saídas do ensemble | Sec. V-E.1; Table I do material suplementar (mencionada,… | 65 |
| 159 | e3 | Sensibilidade ao tamanho do DoE inicial (orçamento offline × online) | Sec. V-E.2; Table II do material suplementar (mencionada,… | 77 |
| 160 | e40 | Sensibilidade ao vetor de razao de custo r e ao limiar rthres | Sec. IV-B-2 (Influence of different r and rthres on the… | 7 |
| 161 | e40 | Ablacao da estrategia de selecao de dados extras do ensemble (completo vs. clustering vs. amostra aleatoria) | Sec. IV-B-4 (Ablation studies), Table VI, p.12-13; mencao a… | 67 |
| 162 | e40 | Ablacao do surrogate nos objetivos baratos (modelo vs. avaliacao instantanea/ilimitada) | Sec. IV-B-4, Table VI (coluna 'BO-NoGP_c'), p.12-13; mencao… | 67 |
| 163 | e40 | Ablacao do termo de penalizacao de vies de busca (SBP) | Sec. IV-B-4, Table VI (coluna 'BO-AAF'), p.12-13; mencao a… | 67 |
| 164 | e64 | Interpretação físico-decisória dos projetos ótimos do caso real (segmentos x variáveis de decisão x física do… | Sec. 5.2.3, Figs. 14-15 | 75 |
| 165 | e7 | Sensibilidade às iterações de treino do surrogate (itertrain, iterr) | Sec. IV-F.1; Figs. S2-S3 (Supplementary material, ausentes… | 65 |
| 166 | e7 | Sensibilidade ao tamanho da rede (neurônios ocultos J=K) | Sec. IV-F.2; Fig. S4 (Supplementary material, ausente deste… | 65 |
| 167 | e7 | Sensibilidade à taxa de dropout — parâmetro central do próprio mecanismo de incerteza | Sec. IV-F.3; Fig. S5 (Supplementary material, ausente deste… | 66 |
| 168 | e7 | Sensibilidade ao tamanho do lote k de avaliações reais por geração | Sec. IV-F.4; Fig. S6 (Supplementary material, ausente deste… | 65 |
| 169 | e7 | Estudo piloto de tamanho de população e nº de gerações (P, iter) da AR-MOEA interna | Sec. IV-F (abertura); ver também Sec. IV-A item 2) ('based… | 65 |
| 170 | e7 | Estudo de caso real — unidades de destilação de petróleo bruto | Sec. V (Conclusão); estudo completo no Sec. VII do… | 75 |
| 171 | e74 | Estudo de caso real — extração de calor geotérmico (EGS fraturado) | Sec. IV-H; Fig. 13 (rede de fraturas e poços); Fig. 14… | 75 |
| 172 | e8 | Comparação de arquiteturas de surrogate por acurácia (μ) | Table S3 (S12); Figure S6 (S13) | 68 |
| 173 | e8 | Correlação de erro entre arquiteturas de modelo (teste) | Table S4 (S13) | 68 |
| 174 | e8 | Correlação de erro entre arquiteturas de modelo (extrapolação) | Table S5 (S15) | 68 |
| 175 | e8 | Evolução das médias do front de Pareto real por geração | Table S6 (S17) | 26 |
| 176 | e8 | Taxa de sucesso/falha da avaliação real (DFT) por geração e causa | Table S7 (S18) | 58 |
| 177 | e8 | Distribuição do critério de aquisição (E[I]/P[I]) por geração | Figure S11 (S18) | 78 |
| 178 | e8 | Sobre-amostragem pelo E[I] de regiões estruturais de baixa taxa de conversão | Text S3 (S35); Tables S13-S14 (S33); Figures S20-S21… | 44 |
| 179 | e8 | Qualidade da amostra inicial por clustering diversidade-orientado | Text S4 (S40); Figure S24 (S41); Figure S25 (S41); Table… | 77 |
| 180 | e8 | Distribuição de metais entre candidatos tentados e convergidos por geração | Figure S13 (S23) | 44 |
| 181 | e81 | Ablação da aproximação de Nyström (exata vs Nystrom-Pareto) | Sec. 4.1 (parágrafo após Fig. 4), Fig. 4 e Fig. 5 | 70 |
| 182 | e81 | Interpretação aerodinâmica dos designs (coeficiente de pressão) | Sec. 4.2, Fig. 9 e Fig. 10 | 75 |
| 183 | e81 | Interpretação aerodinâmica dos designs (geometria do perfil/asa) | Sec. 4.2, Fig. 11 | 75 |
| 184 | e81 | Robustez a ruído de observação injetado (ablação de σ²) | Apêndice 5.3, Fig. 12 | 74 |
| 185 | e86 | Fidelidade do critério de aquisição aproximado (IS/MCS) em relação ao cálculo exato, por nº de objetivos | Sec. IV-C, Fig. 3 | 70 |
| 186 | e86 | Sensibilidade aos hiperparâmetros internos de busca e diversidade (t_max, β) | Sec. IV-A, p. 8 | 65 |
| 187 | e86 | Efeito do método de especificação do ponto de referência do HV | Sec. IV-A, p. 8 | 81 |
| 188 | e9 | Demonstração didática do critério (caso single-objective) | Sec. 3.4, Fig. 1 | 71 |
| 189 | emo1 | Paisagem de aptidão do critério de infill (ilustração sintética em grade fixa) | Sec. 3.2 (Fig. 1, p. 876); Sec. 4.4 (Fig. 2, p. 877); Sec.… | 71 |
| 190 | emo1 | Custo isolado da avaliação do critério de infill × nº de objetivos e |P*| | Sec. 5, Fig. 5, p. 879 | 69 |
| 191 | jin3 | Validação cruzada com resultado publicado na literatura | Sec. IV-C-1 | 76 |
| 192 | jin3 | Decomposição analítica (não-empírica) do custo computacional | Sec. IV-D, Eq. (24)-(25) | 69 |
| 193 | mtm4 | Taxa de soluções factíveis por execução (eficiência de tratamento de restrições) | Sec. VI, Fig. 32 (p.15) | 58 |
| 194 | mtm6 | Mapa visual do surrogate (μ/σ) e da paisagem do critério de aquisição | Sec. V-A (Numerical Experiment), parágrafo 'Result' (item… | 71 |
| 195 | wang4 | Convergência dos parâmetros do modelo de regressão que estima o erro do surrogate (β1, β2) | Sec. V-C2, Fig. 15 | 31 |
| 196 | wang4 | Confronto do ND obtido com a configuração real vigente do sistema (status quo), sob restrições relaxadas | Sec. V-D (final), Fig. 19 | 75 |

Novas absorvidas por fichas existentes: 37 análises, nas fichas 1, 7, 23, 26, 31, 33, 36, 43, 44, 47, 52, 54, 55, 58, 64. Novas nas fichas 65–81: 166.

---

## Histórico (aditivo)

- **06/09/2026 — v1.** Criação com 64 fichas, a partir da mineração 1–8 (documentos internos: dissertação, SPEC, ua-dd-saea, corpus congelado, torre de validação de 22/08, notebook) e das três planilhas do processo seletivo (piloto 10; 38 artigos; 38 × SPEC v3.3). Nenhuma decisão tomada.
- **06/09/2026 (noite) — v2.** Mineração definitiva de 72 artigos (698 análises; 197 novas). Acrescentados, sem alterar a v1: §0.6 (critérios do score), §0.7 (números da mineração), adendo às regras; adendo datado em cada uma das 64 fichas (referências artigo a artigo com localizador; contagem 'de 72'; complementos/correções; score + justificativa); 17 fichas novas (65–81) nos grupos A–I; Anexos 5 (ranking por score), 6 (ranking por referências), 7 (os 72 artigos, os 27 escolhidos e o protocolo), 8 (achados transversais: calibração, custo, resultados negativos, equivalência de critérios, característica × desempenho, blocos-roster) e 9 (mapa das 197 novas). Diretriz (1) aplicada: fichas 15, 63 e 64 descartadas (score 0). Arquivo-companheiro com as íntegras: `mineracao_definitiva_transversais_06-09-2026.md`. Nenhuma decisão tomada.
