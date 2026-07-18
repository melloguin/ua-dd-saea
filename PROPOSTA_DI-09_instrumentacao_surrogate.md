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
