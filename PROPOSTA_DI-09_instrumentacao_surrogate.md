# PROPOSTA DI-09 — Instrumentação de assertividade/calibração dos surrogates
### (para decisão do autor; vira DI-09 no REGISTRO_DECISOES_IMPLEMENTACAO.md se aprovada)

> **Motivação.** A dissertação é sobre SA-MOO-**UU** — o uso explícito da incerteza do surrogate.
> Hoje a ③ permite análise de erro dos REGRESSORES (WAPE/calibração demonstradas pela torre:
> c262 WAPE 0,0011 melhorando 6,2×; e103 cobertura-1σ de só 50% = σ subestimado), mas com DOIS
> defeitos: (i) **contaminação in-sample** (o b3 "WAPE 0,0000" é interpolação sobre pontos já no
> treino — sem marcador, a comparação entre os 16 é inválida); (ii) **amostra enviesada e diferente
> por algoritmo** (cada um só é medido nos pontos que ELE escolheu avaliar). E os CLASSIFICADORES
> (c217/b4/e74-s1) não têm rótulo verdadeiro persistido → sem acurácia/precision/recall/F1.
> **Janela:** antes da bateria M8 (re-rodar 16.500 runs é inviável; o custo agora é ~zero).

---

## Componentes propostos

### A1 · Marcador in-sample/out-of-sample — 1 coluna na ③ — 🔴 CRÍTICO
- **O quê:** coluna `fe_treino_max` (int32): o maior `fe_index` presente no CONJUNTO DE TREINO do
  modelo no momento do fit que gerou a previsão. (NULL onde não se aplica.)
- **Desbloqueia:** filtrar previsões honestamente out-of-sample (`fe_index_do_alvo > fe_treino_max`);
  separar "erro de interpolação" de "erro de generalização" — sem isso, algoritmos que reavaliam o
  arquivo parecem perfeitos (o caso b3).
- **Custo:** ~1 linha por instrumentador (o n_treino/janela já é conhecido em todos); volume +4 bytes/linha.

### A2 · Sonda canônica de generalização — o divisor de águas — 🔴 CENTRAL
- **O quê:** por problema, um conjunto FIXO de **200 pontos** (Sobol, semente própria derivada do
  `seeds.json`), gerado 1× como artefato (`data/sonda/sonda_{problema}.parquet`) com o **f verdadeiro
  pré-computado em Python** (funções analíticas → ZERO FE do orçamento; mesma exceção contábil do
  `__final` da DI-08). A cada **k=5** iterações/gerações (e sempre na 1ª e na última), o
  instrumentador pede ao modelo corrente a predição da sonda inteira e grava na ③ com
  **`regime='sonda'`** (a coluna `regime` já existe no schema §17.2 — zero mudança de schema físico;
  linhas de busca seguem com o regime atual).
- **Desbloqueia:** (a) acurácia GLOBAL, não-enviesada e **diretamente comparável entre os 16**
  (GP × RBF × PNN × rede × classificador — todos medidos NOS MESMOS pontos); (b) a curva "o surrogate
  melhora com as épocas?" limpa, pareada com a curva do otimizador (IGD+×FE) — a figura-síntese da
  dissertação; (c) calibração da incerteza em região neutra (não só onde a busca foca);
  (d) **rótulo verdadeiro dos classificadores POR CONSTRUÇÃO** (o f verdadeiro da sonda + o estado
  corrente do arquivo — reconstruível de ①/② — dão dominância/classe exata).
- **Semântica por família (a sonda pergunta o que o modelo daquele algoritmo responde):**
  regressores por objetivo (b3, c141, e7, c238, e74-s2/s3, e103, c262, c154, R3-GP) → μ (e σ onde
  houver) por objetivo; **b1** → o ESCALAR Tchebycheff com o λ da iteração (é o que o modelo dele
  modela — comparação à parte, documentada); **c217 (PNN par-a-par)** → score do ponto da sonda vs a
  referência corrente (Pmid), como o algoritmo usa; **b4 (CSEA)** → classe + confiança vs o arquivo
  corrente; **e74-s1 (PNN)** → nível previsto. A semântica de cada um fica numa tabela no contrato
  (Anexo §17.2.2 novo) e no `sigma_dict`/manifesto.
- **Custo:** runtime <1% (predizer 200 pontos é trivial em todos; pior caso c217 = 200×|Pmid| pares,
  ainda ms); volume: ~200 linhas × (iters/5) — no pior caso real (b1/ZDT1) +~24k linhas sobre uma ③
  de 757k (**+3%**); implementação: gerador do artefato + hook em 10 instrumentadores `.m` + 2
  runners Python + check no accept (sonda presente/consistente).

#### Dimensionamento da sonda (tamanho S × cadência k) — a aritmética p/ decisão do autor
O autor sugeriu S=3000 por GERAÇÃO (k=1). O ganho estatístico satura e o custo de armazenamento
explode — o erro-padrão do WAPE/cobertura cai com 1/√S, e a restrição vinculante é o VOLUME da
bateria (16.500 runs; a estimativa atual do estudo já é 0,5–0,9 TB):
| Opção | SE relativo | Volume extra estimado (bateria toda) | Nota |
|---|---|---|---|
| S=200, k=5 | ~7% | ~10 GB | o mínimo defensável |
| **S=500, k=5 (recomendada)** | **~4,5%** | **~26 GB** | curva por época nítida, custo baixo |
| S=1000, k=10 | ~3,2% | ~25 GB | mais precisão pontual, menos resolução temporal |
| S=3000, k=1 | ~1,8% | **~770 GB — quase DOBRA o estudo** | ganho marginal ínfimo p/ o custo |
(Sempre: 1ª e última geração incluídas independentemente de k. Runtime: mesmo S=3000 seria barato
em CPU — a restrição é disco/bucket, não tempo.)

### A3 · Rótulo verdadeiro dos classificadores — análise R4 (pós-hoc, sem persistência nova)
Com A1+A2: na sonda, por construção; nos pontos reais, derivado de ①+② (dominância vs arquivo da
geração). Vira notebook do R4: acurácia/precision/recall/F1/AUC(confiança) por geração, comparando
c217×b4×e74-s1. (O c217 par-a-par exige cuidado de definição — documentado no contrato.)

### B1 · Hiperparâmetros e loss de treino por refit — jsonl — 🟡 BARATO E RICO
Campo padronizado `modelo_hp` no evento de fit de cada algoritmo: GP/Kriging → θ/lengthscales
(min/med/max) + nugget + (c262) MLL final; RBF → nº de centros/spread; PNN → spread + nº de pares;
redes → loss final de treino + épocas efetivas. **Já existe parcialmente** (c238 loga θ; e7 loga
Ratio) — é PADRONIZAÇÃO, não invenção. Desbloqueia: "o modelo aprende estrutura?" (lengthscales
estabilizando), diagnóstico de sub/superajuste, custo×qualidade do fit.

### B2 · Tempos por fase padronizados — jsonl — 🟡 QUASE PRONTO
`tempo_fit_s` + `tempo_busca_s` (+ `tempo_pred_sonda_s`) por iteração em TODOS (c238/c262 já têm;
generalizar). Desbloqueia: o breakdown fit×busca×avaliação por algoritmo (no c262 a busca domina
89–98% — isso vira figura), e a projeção honesta do M7.

### B3 · Distância do infill ao arquivo — jsonl — 🟡 1 LINHA
`dist_min_arquivo` (norm. no espaço de decisão) por infill escolhido (c238 já tem `min_dist_infill`).
Desbloqueia: o perfil exploração×explotação ao longo do run — teste direto da hipótese "algoritmos
guiados por incerteza exploram mais cedo" (o coração da tese, mensurável).

### B4 · Análises desbloqueadas SEM persistência nova (documentar no plano do R4)
Com ③+A1+A2: NLL/CRPS preditivo e **sharpness** (σ médio × tempo); **Kendall-τ** entre ranking
previsto×real dos candidatos (o "salvar-tudo" da ③ MATLAB já guarda todos os candidatos);
**contrafactual greedy-μ** — "qual candidato teria sido escolhido SEM o termo de incerteza?"
(recomputável da própria ③; mede QUANTO a incerteza mudou as decisões — c262 limitado aos 10
restarts persistidos, documentar).

### O que NÃO propomos (e por quê)
- **Genealogia de operadores/pais por indivíduo:** exigiria patch INVASIVO no miolo stock dos MOEAs
  (viola o princípio do patch-mínimo/D30 e contaminaria a fidelidade). Rejeitado.
- **Serializar o modelo por iteração:** GB+ por run, sem pergunta de pesquisa que justifique
  (os hp do B1 + as predições da sonda A2 são o resumo suficiente).
- **Sonda maior que 200:** 200 pontos Sobol dão IC apertado o bastante para WAPE/cobertura; dobrar
  só dobra volume.

---

## Sequenciamento (a parte não-óbvia)

**A ordem que MINIMIZA retrabalho:**
1. **AGORA (decisão):** o autor aprova/ajusta esta proposta → vira DI-09 no registro.
2. **Janela documental pós-c154 (já agendada p/ DI-05+DI-08):** o contrato entra na SPEC
   (§17.2.2 novo + tabela de semântica por algoritmo) + bundles regenerados — **1 regen só para
   as três DIs**. A torre também gera o artefato da sonda (novo, não toca faixa de ninguém).
3. **R3 (c122/b5/c311/c149/e81/piso-off) NASCE com o contrato** — os 6-7 instrumentadores restantes
   implementam A1/A2/B1-B3 nativamente, custo marginal ~zero por cartão.
4. **M7 (cartão DI-09-retrofit):** os 12 configs já feitos (R1+R2) ganham o retrofit (hook da sonda +
   coluna A1 + campos B1-B3) + **pilotos de validação** re-rodados (semente 0; os leves em 3
   problemas; c238/c262 validados só no MMF1 — a bateria M8 regenera tudo de qualquer forma).
5. **M8:** a bateria já produz TUDO.
- **Por que NÃO "implementar os 16 primeiro e depois fazer isso":** custaria retrofit em 16 em vez
  de 12, e o R3 teria que ser re-aberto — mais sessões, mais risco. Contrato-primeiro é o caminho
  mínimo.
- **Por que NÃO "implementar o código agora":** o c154 está rodando (faixa Python ativa + regra da
  janela documental para SPEC/bundles). Só a DECISÃO e o DESENHO são de agora — e são exatamente as
  partes que destravam o resto.

## Resumo de custos
| Item | Implementação | Runtime | Volume |
|---|---|---|---|
| A1 | ~1 linha × 12 retrofit + nativo no R3 | zero | +4 B/linha ③ |
| A2 | gerador (1×) + hook × 12 + nativo R3 + accept | <1% | +~3% da ③ |
| B1–B3 | campos jsonl (padronização) | zero | ~KB/run |
| A3/B4 | notebooks R4 (pós-hoc) | — | — |


---

## Anexo — mapeamento dos 4 incrementos planejados pelo autor (2026-07-18)
| Incremento do autor | Onde cai | Quando |
|---|---|---|
| 1 · Mecanismo de RETRY (execuções quebram) | Despachante/esteira — o manifesto já tem `retried_ok` e a esteira é idempotente/resumível por desenho; falta o retry automático (n tentativas + backoff) no `_run_one`, integrado aos fixes dos 2 majors do R2-00 | **M7 (DI-06 ampliado)** — o consumidor é a bateria; pilotos não precisam |
| 2 · Sonda LHS/Sobol p/ régua única de classificador/regressor | **É o A2 desta proposta** (com o dimensionamento acima — recomendação S=500/k=5, não 3000/k=1) | Contrato na janela documental; R3 nativo; retrofit R1/R2 ∥ R3 (faixa MATLAB ociosa) |
| 3 · Logs suficientes p/ fidelidade? + resultados parciais p/ auditar ao vivo + tempos + BARRA DE PROGRESSO | Fidelidade de MECANISMO: os jsonl já são o "filme" (31 campos/iter no c238; auditados). Qualidade de SURROGATE: só com A1/A2. Resultados parciais: o jsonl JÁ streama por geração (best-f/fe/ramos) — padronizar no B1/B2 um registro-resumo por geração; NÃO flushar a ① parcial (quebraria a escrita atômica D58). Barra de progresso: `scripts/progress.py` da torre (lê jsonl/manifestos, read-only — tqdm-like por run + tabela do grid) | Resumo por geração: junto do B1/B2. `progress.py`: a torre pode construir a qualquer momento (read-only) |
| 4 · Tabela-registro de execuções (grid × check × wall × retries) | JÁ EXISTE o esqueleto: `runs_matrix.csv` (o grid) + manifestos por run + `Scoreboard` (manifest.py). Falta: coluna de retries (vem do incremento 1) + a VIEW renderizada (o mesmo `progress.py`) | **M7** (junto do retry) |


---

## ⚠ REFINAMENTOS DO CONTRATO (torre, 2026-07-18 — achados na auditoria do estado atual)
**Estes 3 pontos são VINCULANTES para a sessão de retrofit (fazem parte do contrato).**

### R1 · Escopo por config: a sonda/`modelo_hp`/`fe_treino_max` são dos 17 COM surrogate, não dos 21
Os **4 pisos online** (nsga2/nsga3/moead/smsemoa) NÃO têm modelo — a ③ deles é vazia por desenho
(verificado: 0 linhas, schema válido). Deles se coleta apenas: ①②, `tempo_total_s`/`tempo_busca_s`,
e o jsonl de geração. `dist_min_arquivo` para pisos é derivável pós-hoc de ①+② (não instrumentar).

### R2 · Cadência da sonda nos OFFLINE: 1× POR TREINO, não a cada k gerações
Os 5 configs offline (e103, b5r, b5m, c311, piso-off) treinam o modelo **UMA vez** no dataset — a
predição da sonda seria **idêntica** em todas as gerações (puro desperdício de volume). Regra:
- **ONLINE (modelo re-treina):** sonda a cada **k=2** gerações + 1ª e última.
- **OFFLINE (modelo fixo):** sonda **1× por MODELO treinado** (o e103 tem DOIS: Kriging e RBFN ⇒ 2
  blocos de 2000 linhas), logo após o treino. A dinâmica por geração do offline já está no jsonl
  (`KFlag`/`n_ds_membros`), que é o que de fato varia.

### R3 · 🔴 O bloco `timing` do MANIFESTO está ZERADO — o retrofit DEVE preenchê-lo (B2 elevado a crítico)
Auditoria da torre (12 configs, MMF1 s0): `tempo_total_s` = **0 em 10 de 12**; só o c262 preenche o
bloco completo (total/fit/busca/aval_real + `fit_series`) e o e103 preenche só o total. Consequência:
**os walls medidos (c238 ZDT1 3h55, e7 72min, e74 485s…) existem SÓ em prosa nos handoffs — não são
legíveis por máquina.** Isso quebra (a) o dimensionamento do M7, (b) a análise de custo do R4,
(c) a coluna `wall_s` da tabela de execuções. **Obrigatório no retrofit, em TODOS os 21 configs
(pisos inclusive):** preencher no manifesto `timing.tempo_total_s` (wall do run inteiro),
`tempo_fit_surrogate_s`, `tempo_busca_s`, `tempo_aval_real_s` (agregados). Além disso, padronizar
`tempo_busca_s` na ④ onde hoje é NaN/0 (b3 = NaN; c262 = 0).
*(Nota de leitura, NÃO é bug: o `n_acumulado` do b3 é constante ≡ 21 = 11D−1 porque o K-RVEA CAPEIA
o arquivo de treino por clustering — |A1|≡NI, Fig. 9 do paper. É um achado: o K-RVEA escapa da
parede O(n³) por construção, ao contrário do c238/c262.)*
