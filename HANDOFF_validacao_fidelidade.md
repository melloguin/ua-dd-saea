# HANDOFF — Validação de fidelidade · campanha `ua-dd-saea`, semente 42

**Data:** 2026-07-28 · **Para:** agente de validação de fidelidade
**Insumo:** 666 células OK da semente 42, todas no bucket `gs://mestrado_experiments`
**Documentos irmãos:** `FECHAMENTO_semente42.md` (o que rodou e o que não), `HANDOFF_operacao_multimaquina.md` (infraestrutura, decisões, armadilhas)

---

## 0. O que esta tarefa é — e o que ela não é

**É:** verificar se cada implementação reproduz fielmente o algoritmo que diz reproduzir, usando os artefatos já gerados.

**Não é** (e isto é regra dura do projeto):

> **D97 — fidelidade é julgamento manual e a posteriori do AUTOR.**
> Você levanta evidência, quantifica desvio, propõe hipótese. **Nunca "conserta" fidelidade automaticamente**, nunca ajusta parâmetro para fazer um resultado bater, nunca reescreve algoritmo para casar com uma referência. Achou desvio: documente com número e escale.

> **D80 — os locks são a verdade.** Se um pin divergir do lock, pare e escale. Não instale, não atualize, não improvise versão vizinha "só para testar".

> **D81 — ambiguidade ou conflito ⇒ pare e pergunte.**

Corolário prático: o produto desta tarefa é **um dossiê de evidência**, não um patch.

---

## 1. O material

### 1.1 Onde está

Tudo em `gs://mestrado_experiments/`:

| prefixo | conteúdo |
|---|---|
| `experiments/{exp}/{alg}/` | as 695 células, ~4.954 objetos, ~3,6 GB |
| `_censo/censo_bucket_42_FINAL.csv` | **o inventário autoritativo** — uma linha por célula com estado, camadas, `fe_final/maxfe`, detalhe do erro |
| `_snapshot_pre_teto48h/` | snapshot de `main/c154`, `main/c262`, `batch/c262` antes dos re-runs com `--force` |
| `_logs_teto48h/{v5,v6}/` | logs dos lotes de teto ampliado |
| `_logs_lotes/mac/` | `done.txt` e `grid.txt` de cada lote do Mac — **é o rastro de qual máquina rodou o quê** |

Baixar só o que precisa (o bucket inteiro são 3,6 GB):

```bash
gcloud storage cp gs://mestrado_experiments/_censo/censo_bucket_42_FINAL.csv .
gcloud storage cp -r gs://mestrado_experiments/experiments/main/c122 ./data/experiments/main/
```

**Comece sempre pelo CSV do censo.** Ele diz quais 666 células são material válido; as outras 29 não são falha de fidelidade e não devem entrar na análise (ver §3).

### 1.2 As 7 camadas — o que cada uma serve para checar

Nomenclatura: `exp_{exp}_{alg}_{problema}_{semente}__{camada}`

| # | camada | o que contém | serve para checar |
|---|---|---|---|
| ① | `__real.parquet` | avaliações **reais** da função objetivo | orçamento, duplicatas, DoE, arquivo monotônico |
| ② | `__pop.parquet` | população/arquivo por iteração | dinâmica evolutiva, tamanho de população |
| ③ | `__surrogate.parquet` | predições do surrogate (média e incerteza) | **o coração da fidelidade** — o modelo está sendo usado como o paper diz? |
| ④ | `__timing.parquet` | tempo por fase | onde o custo está; refit vs aquisição vs avaliação |
| ⑤ | `.manifest.json` | proveniência: status, pins, seed, `fe_final`, `maxfe`, `timing.tempo_total_s` | contrato de execução, reprodutibilidade |
| ⑥ | `.jsonl` | **traço por iteração** | a evidência mais rica: o que o algoritmo fez, iteração a iteração |
| ⑦ | `__final.parquet` | resultado final (**só offline**) | endpoint do regime offline |

**O `.jsonl` é a peça central desta tarefa.** É onde dá para ver cadência de refit, tamanho de lote, critério de aquisição, e onde o algoritmo desviou do que promete. No stack MATLAB ele tem ainda um **footer** com `status` e `erro` — o Python põe isso no manifesto, o MATLAB no footer do `.jsonl` (O-21). Um verificador que só olhe o manifesto fica cego para metade da evidência do lado MATLAB.

### 1.3 A grade

**695 células por semente** = `main` 425 (17 algs × 25 problemas) + `off` 125 (5 × 25) + `sweep-*` 120 + `batch` 25 (5 × 5).

Problemas e dimensões:

| D | maxFE = 31D−1 | DoE = 11D−1 | problemas |
|---|---|---|---|
| 2 | 61 | 21 | MMF1, MMF4, MMF11_L |
| 7 | 216 | 76 | DTLZ1 |
| 10 | 309 | 109 | ZDT4, ZDT6, BBOB_F1/F5/F17/F22/F37/F49/F55 |
| 12 | 371 | 131 | DTLZ2, DTLZ3, DTLZ4 |
| 20 | 619 | 219 | MMF16_20 |
| 22 | 681 | 241 | DTLZ7, WFG1, WFG2, WFG4, WFG5, WFG9 |
| 30 | 929 | 329 | ZDT1, ZDT3 |

Problemas de `batch` e `sweep` (5): DTLZ2, MMF16_20, WFG9, ZDT1, ZDT4.

### 1.4 Os 24 configs, por papel

| papel | algoritmos | onde aparecem |
|---|---|---|
| **propostas online (13)** | b1, b3, b4, c122, c141, c149, c154, c217, c238, c262, e7, e74, e81 | `main` |
| **pisos (5)** | nsga2, nsga3, moead, smsemoa (`main`) · sobol_batch (`batch`) | controle |
| **propostas offline (3)** | b5m, b5r, c311 | `off`, `sweep-*` |
| **medianas/piso offline (3)** | e103, moead_media, treed_media | `off`, `sweep-*` |

*(Se a taxonomia do autor separar diferente as três últimas, ajuste — o que importa é que nsga2/nsga3/moead/smsemoa/sobol_batch são **controle**, não proposta.)*

Stack: **MATLAB (13)** b1 b3 b4 c141 c217 c238 e7 e74 e103 moead nsga2 nsga3 smsemoa · **Python (11)** b5m b5r c122 c149 c154 c262 c311 e81 moead_media sobol_batch treed_media.

Ambientes (de `claude_code_context/artifacts/envs.json`, com pins travados):
`env_main` (c122, c149, c154, c262, sobol_batch) · `env_e81_qpots` (e81, botorch 0.16.1 / torch 2.11.0) · `env_b5` (b5r, b5m, moead_media — py3.7.12, sklearn 0.21.3, desdeo vendorizado) · `env_c311` (c311, treed_media — py3.8.20, GPy 1.9.9 compilado do sdist) · `env_matlab` (R2025a + PlatEMO).

---

## 2. As métricas — o contrato já congelado

De `src/metrics.py`. **Não recalcule nada disto a partir dos dados.**

- Normalização por `(ideal, nadir)` da **tabela S.5 congelada** (`F_MIN_MAX`).
- **Hipervolume:** referência `HV_REF_COORD = 1.1` por coordenada no espaço normalizado.
- **IGD+ é o endpoint PRIMÁRIO** (`PRIMARY_METRIC = "igd_plus"`, D70). HV é secundário.
- Diversidade: **Schott spacing em L1**.
- **D92** é o portão de reverificação; a análise de validação cruzada já reproduziu a âncora do D92 exatamente. O artefato está em `validacao_cruzada_indicadores.html`.

---

## 3. O que NÃO é desvio de fidelidade

Antes de investigar qualquer coisa, calibre o que é ruído e o que é decisão de desenho. Errar aqui gera dossiê inteiro sobre nada.

### 3.1 As 29 células não-OK

Nenhuma delas é falha de fidelidade. 5 foram retiradas por desenho (DI-40), 20 são **abortos sancionados por projeção de custo** (DI-38a — `motivo_parada = teto_wall`), 3 são falhas numéricas do BoTorch e 1 é um defeito determinístico do `b1` em DTLZ4. Detalhe completo em `FECHAMENTO_semente42.md`. **Filtre-as fora pelo CSV do censo (`estado == "OK"`).**

### 3.2 O piso de ruído entre máquinas — o número mais importante desta seção

A campanha rodou em 4 máquinas de microarquiteturas diferentes. Medido na validação cruzada:

- **HV varia ≤ 1,55%** entre máquinas para a mesma célula.
- **IGD+ chega a 58,98% de desvio relativo** para a mesma célula.
- **v5 e v6 deram resultado bit-idêntico** entre si (mesma microarquitetura) — ou seja, a variação é *determinística por microarquitetura*, não aleatória.

**Consequência dura:** o IGD+ é o endpoint primário **e** é o mais sensível a máquina. Um desvio de IGD+ abaixo dessa ordem de grandeza **não é evidência de infidelidade** — pode ser só a CPU. Sempre confronte um desvio suspeito contra a máquina onde a célula rodou (coluna `maquina_dona` do censo, com a ressalva da §5.3).

### 3.3 As fronteiras BBOB são EMPÍRICAS

Vêm de cache, não são analíticas. Portanto:
- o **IGD dos 7 problemas BBOB é relativo**, não absoluto — não compare com IGD de ZDT/DTLZ/WFG em escala;
- o **HV pode passar de 1,1** nos BBOB. Isso **não é bug**.

Sempre declare essa ressalva ao reportar qualquer coisa sobre BBOB_F1, F5, F17, F22, F37, F49, F55.

### 3.4 Os pisos são baratos de propósito

nsga2, nsga3, moead, smsemoa rodam em ~1 s por célula (o custo medido é o startup do MATLAB). `sobol_batch` é ~2 s. **Isso é correto** — são baselines sem surrogate. Não investigue "por que o piso é tão rápido".

### 3.5 Aborto do BoTorch não grava parquet

Por desenho anti-órfão (D-07/DI-21), uma célula que aborta **não produz parquet nenhum**. Assinatura de camadas empobrecida numa célula abortada é esperado, não corrupção.

---

## 4. Checagens de contrato — comece por aqui

São baratas, automatizáveis, e cobrem as infidelidades mais grosseiras. Rode sobre as 666 células OK antes de qualquer análise fina.

### 4.1 Orçamento

Para toda célula `main` OK: **`fe_final == maxfe == 31·D − 1`**. Qualquer célula que pare antes sem `motivo_parada` sancionado é suspeita. Qualquer célula que passe do orçamento é infidelidade grave (o algoritmo gastou avaliação real a mais que os concorrentes).

### 4.2 DoE inicial

Nas primeiras linhas de `__real.parquet`: **exatamente `11·D − 1` pontos** antes da primeira iteração online. Nos `sweep-*`, o tamanho muda por *tier* (`small`/`medium`/`big`) e a distribuição por `dist` (`lhs`/`mvns`) — as colunas `tier` e `dist` do `runs_matrix.csv` dizem qual é qual. Verifique que `lhs` é de fato Latin Hypercube e `mvns` de fato normal multivariada; é uma checagem estatística simples e é exatamente o que o experimento de swap está medindo.

### 4.3 Duplicatas e monotonicidade

Em `__real.parquet`: nenhuma avaliação real repetida (mesmo ponto avaliado duas vezes é orçamento desperdiçado e pode inflar artificialmente o arquivo). O arquivo não-dominado deve ser monotônico ao longo das iterações.

### 4.4 Lote q=10

Em `batch`, cada iteração deve propor **exatamente 10 pontos**. Verifique no `.jsonl`. `sobol_batch` é o controle: se um proposto q10 não bater o Sobol, é bandeira vermelha.

### 4.5 Proveniência

O manifesto registra os pins do ambiente. **Confronte com `envs.json`.** Divergência ⇒ D80: pare e escale, não conserte.

### 4.6 Semente

Todas as células desta rodada são semente 42. O `run_id = {exp}_{alg}_{problema}_{semente}` (D55) tem que bater com o caminho do arquivo.

---

## 5. Checagens de fidelidade propriamente ditas

### 5.1 O surrogate faz o que o paper diz?

É aqui que mora a fidelidade real, e a camada ③ + o `.jsonl` são o material.

Por algoritmo, verifique contra a referência: **cadência de refit** (todo passo? a cada k? só quando o erro cresce?), **tipo de modelo** (GP exato, esparso, floresta, ensemble), **função de aquisição** (EI, qNEHVI, JES, …), **tratamento de incerteza** (é o ponto da tese — a incerteza é usada na aquisição ou só reportada?), e **critério de seleção** dos pontos a avaliar.

O `__timing.parquet` ajuda a triangular: se o paper diz refit a cada iteração e o timing mostra custo de refit constante e baixo, alguma coisa não bate.

### 5.2 Sanidade contra os pisos

Toda proposta online deveria, na maioria dos 25 problemas, bater nsga2/nsga3/moead/smsemoa **em IGD+ sob o mesmo orçamento**. Não é obrigatório em todo problema — mas uma proposta que perde para um piso clássico na maioria dos problemas é forte indício de infidelidade na implementação, e vale investigar antes de aceitar o resultado.

Mesma lógica no offline contra `moead_media`/`treed_media`/`e103`, e no q10 contra `sobol_batch`.

### 5.3 ⚠ Atribuição de máquina — uma armadilha concreta

A vm3 não completou parte do stack MATLAB (problemas de disco e capacidade zonal — O-19), e essas células foram recuperadas **no Mac** (macOS/arm64) em vez da vm3 (Linux/Intel):

- **`main/e7`** — as 25 células rodaram no Mac. Config inteiro numa máquina só (O-16 preservada), mas máquina diferente do resto do stack MATLAB.
- **`main/c238`** — dividido entre vm3 e Mac (DTLZ7, MMF16_20, WFG1, WFG2, WFG4, WFG5, WFG9 no Mac). **Aqui a O-16 está rompida.**
- **`main/b1`** — ZDT1, ZDT3 e DTLZ4 passaram pelo Mac.
- **`main/c122`** já tinha divergido por microarquitetura de CPU (O-16 original).

**A coluna `maquina_dona` do censo é derivada do ROSTER, não medida** — ela rotula essas células como `vm3`. A atribuição real está nos `done.txt` em `gs://mestrado_experiments/_logs_lotes/mac/`.

Isso **não afeta os indicadores** (IGD+, HV, spacing são determinísticos dado o resultado) — afeta o endpoint de **tempo** e a leitura de desvio entre células do mesmo config.

### 5.4 Comparação com a implementação de referência

É o teste definitivo e o mais caro: rodar a referência (árvore PlatEMO correspondente, código do paper, ou o `_media` equivalente) num caso pequeno — D=2 (MMF1, MMF4, MMF11_L, maxFE=61) — com a mesma semente e o mesmo DoE, e comparar traço a traço.

Comece por D=2: é onde o custo é trivial (segundos) e onde uma divergência de trajetória fica visível sem ruído de escala. Se a trajetória bate em D=2 e diverge em D=22, o problema é de escalabilidade da implementação, não de fidelidade conceitual — e isso é uma conclusão diferente.

---

## 6. Ordem de trabalho recomendada

1. **Baixe o CSV do censo** e filtre as 666 OK. Nunca analise sem esse filtro.
2. **Rode as checagens de contrato (§4)** sobre as 666. São baratas e cobrem o grosso. Produza uma tabela config × problema com verde/vermelho por checagem.
3. **Calibre o ruído (§3.2)** antes de olhar desvio: use o `validacao_cruzada_indicadores.html` e a análise que o gerou.
4. **Sanidade contra os pisos (§5.2)** — é o filtro mais eficiente para achar onde vale investigar.
5. **Comparação de referência em D=2 (§5.4)** para os configs que a etapa 4 marcou.
6. **Escale** o que sobrar, com número, não com adjetivo.

---

## 7. Armadilhas que já custaram tempo

- **`anchors.json` não são âncoras de métrica.** É o arquivo de patch-anchor do D80. As âncoras estão na tabela S.5 congelada em `src/metrics.py`.
- **`timing.tempo_total_s` é aninhado** dentro de `timing` no manifesto. Um leitor que varra só as chaves de topo sai vazio.
- **O stack MATLAB certifica no footer do `.jsonl`**, não no manifesto (O-21). Célula MATLAB sem manifesto pode ter diagnóstico completo no `.jsonl`.
- **Footer ausente = morte de máquina; footer com `status=failed` = falha algorítmica** (O-22). O discriminador é limpo e vale para qualquer auditoria futura.
- **8 células foram encerradas pelo operador em 28/07** (3 de `main/c154` em DTLZ2/3/4 e 5 de `c262`) para liberar as VMs. O `.jsonl` delas fica **truncado sem footer** — que é a assinatura de morte de máquina. **Não é incidente de infraestrutura, foi decisão.**
- **`batch/e81/ZDT4`** teve cópias herdadas do `data/` de provisionamento subindo de v5 e v6 por cima da versão do Mac (dono legítimo). Foi reafirmada do Mac em 28/07 às 17h03. Se algo parecer estranho nessa célula, é por aí.
- **Provisionamento de VM copiou `data/`** e criou células com proveniência errada. Toda célula cujo host real diverge do dono do roster merece auditoria.

---

## 8. Estado que a validação herda

**666 de 695 células OK (95,8%; 96,5% descontando as retiradas por desenho).**

- `off` (main offline) fechou **100%** — 125/125.
- `sweep-*` (swap offline) fechou **100%** — 120/120.
- `main` fechou 406/425; `batch` fechou 15/25.
- **21 dos 24 configs fecharam integralmente.** Todo o déficit está em `c154`, `c262` e uma célula de `b1`.
- `final_eval.py` fechou **`>>> VERDE`** com 105 finais avaliados.
- **Zero falhas entre os pisos.** Zero falhas no offline. Zero falhas nos sweeps.

As 4 máquinas estão desligadas; o bucket é a única fonte. O censo pode ser regerado, mas hoje ele depende do SDK `google.cloud.storage` que estava na v5 — **vale portá-lo para `gcloud storage ls --recursive` + `gcloud storage cat` antes da defesa**, para que o inventário continue regenerável quando as VMs forem deletadas.

---

## 9. O que escalar, e como

Escale ao autor, com número e caminho de arquivo, nunca com adjetivo:

1. Divergência de pin entre manifesto e `envs.json` (D80 — pare imediatamente).
2. Violação de orçamento (`fe_final ≠ maxfe` sem motivo sancionado).
3. Proposta perdendo para piso na maioria dos problemas.
4. Divergência de trajetória contra a referência em D=2.
5. Qualquer suspeita de infidelidade — **com a evidência, sem a correção** (D97).

Pendências já abertas que tocam esta tarefa: o que fazer com as 3 falhas reais (`main/c262/WFG1`, `main/c154/ZDT6`, `main/c154/BBOB_F55`), o defeito determinístico de `main/b1/DTLZ4`, a extensão da DI-40 para `batch/c262` e `main/c154` D≥12, e a atribuição de máquina mista de `main/c238` antes de montar a tabela de tempo do M7.
