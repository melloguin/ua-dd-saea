# Fundação 3/5 — Contrato de export (§17 completo: 3 camadas, timing, jsonl, persistência)

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

## 17. Contrato de export — [DECIDIDO: histórico completo, TRÊS camadas — 3ª sincronizada na D31]

**Diretriz (objetivo do autor):** persistir **toda avaliação de toda solução em cada ciclo da execução — real E surrogate** — para reconstruir exatamente como cada busca funcionou ("o filme" da execução). Vale para **todos os regimes** (online, offline, batch). **[D31] Uma 3ª camada** grava a **população real sincronizada** com os snapshots do surrogate (§17.1.3), para o cruzamento pareado geração a geração.

**Correção importante sobre o offline:** afirmações anteriores de que "o offline não tem trajetória" referem-se **apenas** à curva de métrica × **avaliações reais** (que tem 1 ponto só no offline — §11). O offline **tem, sim, uma trajetória de busca inteira** — a evolução do MOEA interno **sobre o surrogate** (e103: ~100 ger; b5: 40k aval-surrogate; c311: construção `N/(10D)`×50 + final 10×100 ≈ 1000 ger — §11, ⟦corrigido v2.7; não '1.500'⟧). Essa trajetória-surrogate **é gravada**.

### 17.1 As três camadas gravadas [3ª = D31/v3.0.14]
O histórico completo de cada `(algoritmo, problema, semente)` é gravado em **3 tabelas Parquet** — o lado REAL normalizado (catálogo + registro de população) e o lado SURROGATE em **tabela única** — mais o **log de auditoria** (§17.5, QA à parte).

1. **① Catálogo REAL** — as **soluções únicas avaliadas na função verdadeira** (**dedup por X**; a fitness real é determinística). `solution_id` (chave) → `x_1..x_D`, `f_1..f_M` verdadeiro. **Poucas e preciosas** (≤ 31D−1 por run) — daqui saem as métricas oficiais (§12).
2. **② Registro de POPULAÇÃO REAL / geração** — **membership**: `(algoritmo, problema, semente, geracao, solution_id)`, **100% das gerações**. Quais soluções reais o algoritmo mantinha em cada geração (X/F vêm do ① por join). Mostra o comportamento no tempo (quem sobreviveu × foi descartado).
3. **③ Tabela SURROGATE (única — catálogo+população juntos) [D35]** — **cada avaliação do modelo por (candidato, geração)**, **100% das gerações**. `(algoritmo, problema, semente, geracao, x_1..x_D, real_solution_id, pred_tipo, μ/σ, pred_classe, pred_score, pred_confianca, modelo_flag)`. Schema único do C1 — a "saída" depende do tipo: **μ/σ** p/ regressor, **classe/score** p/ classificador. `real_solution_id` liga ao ① quando o candidato foi mesmo avaliado (pareia predição × verdade, e evita repetir o X).

**Por que 3 (e não 4):** o lado **REAL** vale normalizar — a fitness é determinística, então dedup por X colapsa os sobreviventes (que se repetem em muitas gerações). O lado **SURROGATE não**: a predição é **datada** (muda a cada retreino), então cada (candidato, geração) é único → um catálogo surrogate teria o tamanho do registro de população, sem ganho; melhor **uma tabela só**. O `solution_id`/`real_solution_id` é a **chave de join**; o `geracao` **sincroniza** real×surrogate para o cruzamento do *erro de fantasia*.

**Valor analítico das duas camadas juntas:** cruzar a camada surrogate com a real expõe o **erro de fantasia** do surrogate em câmera lenta — regiões que o modelo *achava* ótimas (alto μ) e que a avaliação real desmentiu. Para uma tese sobre *uso da incerteza*, é material central (liga-se à análise por característica, §15).

### 17.2 Schema — as 4 tabelas [D34/v3.0.16]
**Camada real** (por linha = uma avaliação real):
```
algoritmo | problema | semente | **solution_id** (chave — único por solução real) |
x_1..x_D | f_1..f_M (verdadeiro) | fe_index (quando foi avaliada) | fase (init|opt)
```
**① Catálogo REAL** (mock; DTLZ2, M=2, D=6, semente 7 — uma linha por solução única, dedup por X):

| algoritmo | problema | semente | solution_id | x⃗ (D=6) | f⃗ verdadeiro (M=2) |
|---|---|---|---|---|---|
| b3 | DTLZ2 | 7 | R-001 | [.312,.881,.124,.503,.090,.774] | [1.834, 2.101] |
| b3 | DTLZ2 | 7 | R-002 | [.620,.140,.402,.281,.912,.331] | [2.410, 1.552] |
| b3 | DTLZ2 | 7 | R-042 | [.500,.492,.500,.511,.500,.021] | [1.021, 1.010] |

O formato é **idêntico para os 16 algoritmos** (é o dado verdadeiro, independe do surrogate): `init` = ponto do DoE (11D−1=65 em D=6), `opt` = infill gasto na busca (até 20D=120). Total = **31D−1 linhas por run**, apuradas uma a uma. As métricas oficiais (§12) saem SÓ daqui.

*(Nota [D31/D32]: o **`solution_id`** (único por avaliação real na camada real) é a **chave de join** que liga tudo — a camada `pop_real` é só `(run_id, geracao, solution_id)` (membership; `x`/`f` vêm da camada real). Assim a `pop_real` guarda **100% das gerações em <1 GB**.)*

**[D33] Snapshots da camada surrogate:** **TODAS as gerações** (resolução máxima). ~~Teto ~500 linhas/iter mantido.~~ **[SUPERSEDIDO por D54 (v5.0): teto REMOVIDO — salvar TUDO; os 5 volumosos (c154, c122, e81, c149, c262) gravam BUCKET-ONLY, os demais dual-write. ③ total ≈ 0,5–0,9 TB.]** **[D32→D53] Compressão:** `x`/`μ`/`σ` em **float32** (7 dígitos — suficiente num benchmark determinístico; metade dos bytes do float64) + Parquet com **codec zstd** (~1,5–2× sobre o snappy default) → a camada surrogate cai **~3–4×**. Onde um candidato surrogate coincide com uma solução real (tem `solution_id`), a linha aponta o id em vez de repetir o `x`.

**Tabela SURROGATE (única — D35; por linha = 1 avaliação do modelo, por candidato×geração):**
```
algoritmo | problema | semente | regime | geracao (TODAS — D33) |
x_1..x_D | real_solution_id (liga ao Catálogo REAL se o candidato foi avaliado; senão NULL) |
mu_1..mu_M (predição) | sigma_1..sigma_M (se disponível) |
pred_tipo | pred_classe | pred_score | pred_confianca | modelo_flag   ← [C1/D26] saída conforme o tipo
fe_treino_max (int32) ← [DI-09/A1 v5.2.1] maior fe_index no TREINO do modelo no fit desta predição
```
**[DI-09 v5.2.1]** A coluna `regime` da ③ distingue `'sonda'` (as predições na régua fixa —
§17.2.2) das predições da busca; `fe_treino_max` separa in-sample de out-of-sample na análise.
**Manifesto por run** (JSON): parâmetros efetivos, **wall-clock total + desdobramento (fit-surrogate / busca / avaliação-real) e a série de tempo de fit por retreino `{n_acumulado, tempo_fit_s}` — §17.6**, nº de FEs efetivo, nº de gerações internas, **q (tamanho de lote; 1 no principal)**, versão do algoritmo/repo, hash do DoE inicial, e **[D23] `status` ∈ {`ok`, `retried_ok`, `failed`} + `n_retries` + stack trace se falhou** (o mesmo status vai também no Parquet, para filtrar sucessos/falhas por algoritmo×problema×semente na análise).

**✔ [DEF-C1 — DECIDIDO na D26/v3.0.9] Schema ÚNICO com colunas opcionais (base única).** Os 4 classificadores (b4, c122, c217, e o e74 híbrido) **não** preveem μ/σ de valor — preveem *relações* (classe, score de ranking). Em vez de duas bases separadas por tipo de surrogate, adotamos **uma única tabela** com colunas opcionais: o regressor preenche `mu/sigma` (o resto NULL); o classificador preenche a coluna de relação (μ/σ NULL); o híbrido preenche os dois. **Racional:** a análise central é cruzar a camada surrogate com a real por indivíduo (§17.1) — na base única isso é um **join direto**; em bases separadas exigiria **unir** duas tabelas e o híbrido e74 ficaria **partido** em duas. O "custo" da tabela larga com NULLs é ilusório: em Parquet (colunar), sequências de NULL comprimem a quase zero. A única dor real — "o que cada coluna significa em cada algoritmo" — é resolvida pelo dicionário de σ (DEF-C4). *(Opção rejeitada: bases separadas por tipo de surrogate — mais "pura" por tabela, mas 2 formatos, UNION em toda visão global, e o e74 partido em duas.)*

**Colunas opcionais dos classificadores (estendem o schema surrogate acima):**
- `pred_tipo` ∈ {`valor`, `classe`, `score`, `híbrido`} — a natureza da predição daquela linha.
- `pred_classe` (texto) — o rótulo categórico previsto (ex.: `bom`/`ruim` no b4; `nível_k` de não-dominância no e74-PNN). NULL para regressor e para score.
- `pred_score` (numérico) — a nota agregada por candidato (ex.: ternário {−1,0,+1} no c217; EDN e(z) no c122). NULL para regressor e para classe.
- `pred_confianca` (numérico ∈ [0,1]) — a confiança/probabilidade do modelo na predição da linha (ex.: L do b4; Error1 da geração no c217; max-softmax no c122). NULL quando o modelo não a fornece.
- `modelo_flag` (texto) — qual modelo gerou a linha (GP, RBF, FNN, PNN-par, RBF+PNN…), para desambiguar a semântica das colunas por algoritmo.

**③ Tabela SURROGATE (única — catálogo+população juntos) [D35/v3.0.17]** (mock; cada linha = 1 avaliação do modelo por candidato×geração, SEM dedup — a predição muda com o retreino. Além das colunas abaixo, tem `geracao` (a coluna ger) e `real_solution_id` = liga ao ① quando o candidato foi avaliado de verdade). A saída depende do tipo (schema C1):

| algoritmo | problema | semente | geracao | x⃗ | real_sol_id | pred_tipo | μ₁ | μ₂ | σ₁ | σ₂ | pred_classe | pred_score | conf | modelo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| c262 | DTLZ2 | 7 | 3 | [.312,.881,…] | R-001 | valor | 0.420 | 0.710 | 0.080 | 0.050 | ∅ | ∅ | ∅ | GP |
| c262 | DTLZ2 | 7 | 4 | [.312,.881,…] | R-001 | valor | 0.390 | 0.735 | 0.061 | 0.041 | ∅ | ∅ | ∅ | GP |
| b4 | DTLZ2 | 7 | 5 | [.20,.75,…] | ∅ | classe | ∅ | ∅ | ∅ | ∅ | bom | ∅ | 0.830 | FNN |
| c217 | DTLZ2 | 7 | 5 | [.20,.75,…] | ∅ | score | ∅ | ∅ | ∅ | ∅ | ∅ | +1 | 0.860 | PNN-par |
| e74 | DTLZ2 | 7 | 5 | [.48,.51,…] | ∅ | híbrido | 1.050 | 0.920 | ∅ | ∅ | nível_2 | ∅ | 0.740 | RBF+PNN |

**② Registro de POPULAÇÃO REAL / geração** (membership; `solution_id` = o do catálogo ①):

| algoritmo | problema | semente | geracao | solution_id |
|---|---|---|---|---|
| b3 | DTLZ2 | 7 | 1 | R-001 |
| b3 | DTLZ2 | 7 | 1 | R-002 |
| b3 | DTLZ2 | 7 | 5 | R-001 |
| b3 | DTLZ2 | 7 | 5 | R-042 |

*(R-001 aparece na ger. 1 E na 5 = **sobreviveu**; R-002 sumiu = descartado. X/F vêm do ① por join.)* **[D35] O lado surrogate NÃO tem registro separado** — a tabela ③ (única) já é por (candidato, geração).

**Por que cada tipo preenche o que preenche (leitura linha a linha):**
- **Regressor** (c262 no mock; também b1, b3, e7, c141-RBF, c238, e81, c149, c311, e103, b5): produz média `μ` e, quando o modelo é probabilístico (GP), incerteza `σ` por objetivo. Preenche `mu_*` (+`sigma_*` se houver); `pred_classe/score/confianca` = NULL. *(RBF puro — c141, cabeça RBF do e74 — dá μ SEM σ ⇒ `sigma_*` NULL; é exatamente a distinção do eixo de medição VAR-GP × ERR-EMP.)*
- **Classificador de classe (b4 CSEA):** prevê um rótulo **binário** — o candidato é "bom" (não estritamente pior que TODAS as K=6 soluções de referência escolhidas radialmente do não-dominado corrente) ou "ruim". `pred_classe` = bom/ruim; `pred_confianca` = L ∈ (0,1), a saída sigmoide da FNN (probabilidade de "bom"); μ/σ/score = NULL. O gate L>0,9 → o candidato ganha uma avaliação **real** (infill); L<0,1 → descartado — a classe decide *quem gasta um FE real*, não "quem entra no front". *(O e74-PNN é um classificador de classe multi-nível: `pred_classe` = nível de não-dominância.)*
- **Score agregado de rede par-a-par (c217, c122):** a rede é treinada com pares (todos×todos de um subconjunto pequeno best/worst), mas o que se **usa e grava** é uma **nota por candidato**, não as comparações cruas: c217 → score ternário {−1,0,+1} (a ação da regra tripla corrigida, D17); c122 → e(z) da EDN (Σ vitórias·p̂ + termo θ). `pred_score` = a nota; `pred_confianca` = a confiabilidade (Error1 no c217; max-softmax no c122); `pred_classe`/μ/σ = NULL. **NÃO gravamos O(n²) comparações** — a confiabilidade da geração (Error1/Error2/estado) vai no log de auditoria (§17.5).
- **Híbrido (e74 CLMEA):** tem as DUAS cabeças — RBF dá `μ` (σ NULL, RBF não dá incerteza) e PNN dá `pred_classe` (nível). Uma linha só carrega ambas; `pred_tipo=híbrido`.

**Caso especial — b1 (ParEGO), surrogate ESCALARIZADO [D47].** O b1 é regressor, mas **mono-output**: a cada iteração sorteia um vetor de pesos `λ`, colapsa os M objetivos em UM escalar de Tchebycheff aumentado (ρ=0,05, objetivos normalizados a [0,1] pelo min/max do arquivo) e treina **um único GP** sobre esse escalar. Logo a saída surrogate do b1 é o **valor escalarizado previsto `μ` e sua incerteza `σ`** — um por candidato, **não** μ/σ por objetivo. Na tabela ③ o b1 preenche `mu_1`/`sigma_1` com o escalar de Tchebycheff (`mu_2…`/`sigma_2…` = NULL) e as colunas C3 (`espaco_modelo`, `transf_params`) carregam **λ, o min/max da normalização e o Gbest (incumbente)** daquela iteração — sem eles o escalar é ininterpretável (o λ muda a cada iteração, então o mesmo `x` pontuado em iterações diferentes tem σ em réguas diferentes). Os **objetivos reais separados** `f₁…f_M` continuam no catálogo ①, recuperáveis por `real_solution_id` **quando o candidato foi de fato avaliado** — de modo que a análise vê, na leitura conjunta, **tanto os objetivos reais separados (①) quanto o objetivo colapsado + incerteza (③)**, que é exatamente o "cru + transformado" da DEF-C3 aplicado ao b1. *(Ressalva de honestidade: para um candidato **só** pontuado pelo surrogate — nunca avaliado de verdade — só existe o escalar previsto; não há valores por-objetivo em lugar nenhum, porque o GP do ParEGO prevê o escalar direto de `x`, não objetivo a objetivo. E **não** fabricamos um surrogate por-objetivo: treinar M GPs extras mudaria o mecanismo e violaria a fidelidade D29 — o σ do b1 é, por natureza, escalarizado.)*

**Dicionário de colunas por algoritmo (DEF-C4 — [IMPL]):** como a mesma coluna significa coisas diferentes por algoritmo (σ do GP × pseudo-σ geométrico do e74 × "extensão nossa" do c311 × gate booleano do e103, não σ contínuo × **σ escalarizado de Tchebycheff do b1 — não por-objetivo [D47]**), o dicionário por algoritmo — o que cada coluna representa e sua unidade — é registrado no **manifesto de análise** (bloco de export, DEF-C4).

**Nota — os dados VERDADEIROS dos classificadores.** A camada real guarda **sempre a fitness verdadeira** `f₁…f_M`, para os 16 algoritmos, **inclusive os classificadores** — ela não muda de natureza. A avaliação cara que gasta orçamento é sempre a função objetivo devolvendo a fitness; o classificador só treina sobre pares (x, fitness) que já temos, e o "rótulo verdadeiro" (bom/ruim, domina/não) é **função determinística da fitness**, recomputada na análise (fitness → rótulo é mão-única: da fitness sempre reconstruo o rótulo, mas não o inverso). Por isso a tabela de verdadeiros **é a fitness**, não a resposta à pergunta do classificador — e é o formato mais informativo, além de ser o que as métricas oficiais precisam. A acurácia do classificador é aferida reconstruindo o rótulo verdadeiro a partir da fitness **onde há avaliação real** (arquivo + infills selecionados); os candidatos reprovados nunca ganham fitness real (é o ponto do surrogate), e é por isso que a confiabilidade é medida no conjunto de validação do arquivo (`p1/p2` do b4, `Error1/Error2` do c217 — no log §17.5).

**[D35 · parcialmente SUPERSEDIDO por D53/D54 — carimbos Higiene v5.2 inline]** **Cobertura:** guardamos **100% das populações de TODAS as gerações**, tanto real (registro ②) quanto surrogate (tabela ③) — nada é amostrado no eixo de gerações. **Reduções aplicadas a TODAS as tabelas:** (1) ~~floats arredondados a 3 casas decimais~~ **[SUPERSEDIDO por D53: NÃO arredondar — o `round3` colapsava o σ 10⁻⁴–10⁻⁶ e colidia o dedup-por-X]**; (2) armazenados em **float32** (metade dos bytes do float64); (3) Parquet com **codec zstd** (~1,5–2× melhor que o snappy default; MATLAB grava `brotli` e a consolidação reencoda — S.6); (4) IDs e `geracao` são **inteiros** (comprimem quase a nada, com dicionário/RLE); (5) na tabela ③, `real_solution_id` **evita repetir o `x`** quando o candidato já é uma solução real. **Efeito [SUPERSEDIDO por D54 — salvar TUDO, sem teto]:** ~~a tabela surrogate cai para ~25–50 GB~~ → com o fim do teto (D54) a **③ do estudo ≈ 0,5–0,9 TB** (bucket-only p/ os 5 volumosos); catálogo+população reais **<1 GB**. O piloto de timing confirma e afina por algoritmo.

### 17.2.1 Log de auditoria da regra tripla do c217 [NOVO v3.0.2 — D17]
Decorrência da DEF-B5.1 (corrigimos a fiação da regra) e exigência explícita do autor: além da camada surrogate em Parquet (§17.1), o **c217 grava um log `.txt` legível por humano, um por `run_id`**, registrando **a cada geração** a decisão de gestão de confiança do algoritmo — para **auditar pós-hoc** que a correção reproduz o comportamento previsto pelo paper. Cada bloco contém:

```
run_id | problema | semente | geracao g | |Arc| | delta=0.8 |
p_mais (=Error1: fração de pares CORRETAMENTE classificados) | p_menos (=Error2: fração INVERTIDA) | n_contradicoes |
ESTADO {1 = confiável -> MAXIMIZA score | 2 = invertido -> MINIMIZA score | 3 = ignorar -> ALEATÓRIO | NaN -> ALEATÓRIO} |
motivo (desigualdade que disparou, ex.: p_mais=0.86 > delta=0.80 -> estado 1) |
tamanho_do_lote_infill | scores_dos_selecionados
```

**O que a auditoria verifica** (cruzando os `.txt` com o esperado do paper): (a) com um modelo decente, o **estado 1 domina** as gerações iniciais; (b) o **estado 2 (inversão) só dispara quando p_menos > delta** — se nunca disparar, tudo bem (é raro; acurácia típica ~0,6); (c) o **regime-NaN cai no estado 3 (aleatório)**, e não no "maximiza" da versão bugada; (d) a distribuição de estados ao longo do run é coerente com a Tabela 5 / Fig. 9 do paper. Isto **fecha o loop** com o check de reprodução (§20): se os números-âncora baterem E os logs mostrarem os estados certos, a fiação está fiel. **Template extensível** (não obrigatório agora): o mesmo formato serve aos demais classificadores (b4 regime R1/R2/R3; c122 acordo das 2 redes; e74 estratégia 1/2/3) — decidir na DEF-C1 se generalizamos.

**✔ [DEF-C3 — DECIDIDO D28/v3.0.11] Espaços transformados: gravar CRU + TRANSFORMADO, ambos completos.** Alguns algoritmos modelam num espaço transformado, não no cru: **b1 (ParEGO)** escalariza os M objetivos num único valor Tchebycheff (peso λ sorteado por iteração) + normaliza o arquivo min-max; **c238 (EIM)** normaliza y por min-max a cada iteração (do paper); **e7** translada os objetivos. *(Mais normalizações de Y triviais e invertíveis em poucos outros — ex.: o z-score que adicionamos ao c149 — que caem na mesma regra.)* **Decisão:** para esses casos a base surrogate grava **os dois espaços de uma vez** — o valor no espaço do modelo, o valor no cru (onde a transformação é invertível: c238, e7) **E** os parâmetros da transformação por iteração — mais colunas opcionais: `espaco_modelo` (transformado|cru), `transf_tipo` (escalar-tcheby|minmax|translacao|zscore), `transf_params` (λ / min,max / vetor de translação). **Racional:** são só ~3 algoritmos e o custo de storage é desprezível (~+1–2 GB no total, §17.4); em troca, a análise **não precisa inverter nada** — os dois espaços já vêm prontos (escolha do autor pelo cronograma apertado). *(Exceção honesta: a escalarização do b1 é **lossy** — grava-se o escalar + λ, que é interpretável mas não des-agrega em μ por objetivo; é inerente ao ParEGO, não uma perda evitável.)* Rejeitadas: "só o transformado" (sem os parâmetros, o valor de uma iteração não é comparável ao de outra e não volta ao cru → quebra o cruzamento com a camada real §17.1) e "cru + parâmetros, inverter na análise" (economiza ~1–2 GB mas custa tempo de análise — não compensa dado o cronograma).

### 17.2.2 — SONDA canônica de generalização [DI-09 — decisão do autor 2026-07-18 · v5.2.1]
**O quê.** Um conjunto FIXO de pontos por problema — **artefato de S=20.000; o regime ONLINE lê as
2.000 primeiras e o OFFLINE lê todas [DI-13.5, autor 2026-07-19]** — o MESMO para todos os algoritmos,
gerações e sementes — que cada modelo prediz periodicamente, gravando na ③ com `regime='sonda'`.
É a régua única que torna a qualidade dos surrogates DIRETAMENTE comparável entre os 17 configs
com modelo (GP × RBF × PNN × rede × classificador), livre do viés de amostragem da busca.
- **Definição EXATA dos pontos (sem margem p/ erro):** artefato `data/sonda/sonda_{problema}.parquet`
  gerado 1× por `scripts/gen_sonda.py` — Sobol embaralhado `scipy.stats.qmc.Sobol(d=D, scramble=True,
  seed=SeedSequence((4242, problema_id)) truncada a 32 bits)`, re-escalado aos bounds NATIVOS,
  colunas `sonda_id | x0..x{D-1} | f0..f{M-1}` com o **f verdadeiro pré-computado** em
  `src/problems.py` (float64) + sidecar com sha256 do array. **Nenhum algoritmo gera pontos de
  sonda — todos CARREGAM o artefato e conferem o hash no arranque** (disciplina D63/D87). Custo de
  FE: ZERO (avaliação analítica fora do orçamento — exceção contábil, precedente do `__final` §11).
- **Cadência e TAMANHO por regime [DI-13.5]:** ONLINE = **2.000 pontos** (a fatia `[0:S_online]`
  do artefato) a cada **k=2** gerações/iterações + SEMPRE a 1ª e a última; OFFLINE = **os 20.000**,
  **1× por modelo treinado**, com `geracao = NULL` (o modelo treina ANTES do laço — não há geração
  a que pertencer). A sequência de Sobol é **ANINHADA** (verificado |dif|=0): a fatia online é
  BIT-IDÊNTICA a uma sonda gerada com 2.000, logo a régua é a MESMA nos dois regimes na faixa
  compartilhada. O sidecar v2 traz `S`/`S_online` + `x_hash`/`x_hash_online` — cada regime confere
  o SEU hash (e103 grava 2 blocos: Kriging e RBFN). O evento `sonda` do `.jsonl`
  registra `geracao`, `fe` e `tempo_pred_sonda_s` — o eixo de comparação entre algoritmos é o
  **FE consumido** (gerações não são alinhadas entre configs).
- **Gravação:** 2000 linhas na ③ (`regime='sonda'`, `real_solution_id=NULL`, `fe_treino_max`
  preenchido), na ORDEM do artefato (join com o gabarito POR POSIÇÃO dentro do bloco — invariante
  do writer). A saída segue a semântica do modelo de cada algoritmo (tabela no
  `CONTRATO_DE_DADOS.md` §3.2, raiz do repo): regressores → μ/σ por objetivo; b1 → o escalar
  Tchebycheff com o λ corrente; c217/c122 → score vs referência corrente; b4 → classe+L;
  e74 → 2×2000 linhas (nível PNN + μ RBF). Pisos NÃO têm sonda (sem modelo).
- **🔴 Invariante de NÃO-PERTURBAÇÃO:** a sonda não pode alterar a busca — preditores estocásticos
  (MC-dropout do e7) exigem save/restore do RNG em volta da predição; a prova objetiva por config
  é a ① do run com sonda ser IDÊNTICA à do run sem (mesma semente ⇒ mesma trajetória).

### 17.3 Formato físico e implementação
- **Parquet** (colunar, comprime bem o histórico grande) + manifesto JSON. Um diretório por (algoritmo, problema); arquivos separados por semente e por camada (a camada surrogate é muito maior — separá-la facilita carregar só o que a análise precisa). **As métricas NÃO são gravadas aqui** — derivadas em §12.
- **PlatEMO [⟦corrigido v2.7 — ver N.0#3⟧]:** ⚠ **NÃO usar `save>0`** — com `UserProblem` o nome do `.mat` colide (todos os 25 problemas viram `UserProblem`) e o auto-incremento de `run` é uma corrida TOCTOU sob paralelismo. Usar **`save=-K`** (K snapshots {FE, Population} em memória, sem `.mat`, sem figura) só para **ler o resultado final** (`Algorithm.result`). **[D31] As camadas surrogate E população-real são emitidas pelo hook `outputFcn`** (chamado a cada geração; todas as gerações entram) — o MESMO hook emite os dois nos MESMOS pontos, garantindo a sincronização §17.1.3. Para os stacks não-PlatEMO (BoTorch/standalone), a instrumentação equivalente emite os dois por iteração de BO. Ponto de implementação por algoritmo (auditado pelos logs §17.5).
- **Métodos BO puros (b1, c238, c262, c154, e81, c149):** ⚠ a granularidade "por geração" (todas as gerações) é **EA-cêntrica e não mapeia diretamente** aqui — BO sequencial não tem gerações de população, tem **iterações de BO** (1 infill cada). Política equivalente: **um snapshot por iteração de BO**. O conteúdo do snapshot é o **conjunto de candidatos avaliados no surrogate naquela iteração**: para os que otimizam a aquisição por EA interno (ParEGO/GA, EIM/DE, qPOTS e c149/NSGA-II), grava-se a **população final desse EA interno** com `μ`/`σ`; para os que otimizam por multi-start L-BFGS/analítico (BoTorch), grava-se o **conjunto de candidatos avaliados** (os `x` testados + `μ`/`σ` do posterior). Objetivo: reconstruir o que o modelo "achava" a cada passo para cruzar com a realidade (§17.1). No sub-estudo batch, o snapshot registra também o **lote selecionado** por iteração.
- **Offline (DESDEO/b5/c311, e103):** instrumentar o MOEA interno para emitir a população-surrogate em todas as gerações; a camada real é o conjunto final avaliado uma vez (§11).

### 17.4 — Granularidade e volume da camada surrogate [DEF-C2 — DECIDIDO D27/v3.0.10]

**Política de granularidade (o que entra no snapshot, por classe de motor).** A camada surrogate NÃO grava toda consulta ao modelo (são milhões, baratas) — grava **snapshots** da população/candidatos *decisão-relevantes*, com a unidade natural de cada motor:
- **EA** (b3, b4, e7, c141, e74, c217, c122): a **população SELECIONADA por geração** (a que sobrevive à seleção, não todo rascunho interno), em **todas as gerações** (100%, nada amostrado no eixo de gerações).
- **BO com EA interno** (b1 ParEGO/GA, c238 EIM/DE, e81 qPOTS/NSGA-II, c149/NSGA-II): a **população final do otimizador de aquisição** por **iteração de BO**.
- **BoTorch** (c262, c154): os **candidatos avaliados nos restarts** de multi-start por iteração.
- **Offline** (b5, c311, e103): a população-surrogate do MOEA interno em todas as gerações.

**~~Teto de ~500 linhas/iteração.~~ [SUPERSEDIDO por D54 — Higiene v5.2: salvar TUDO, sem teto.]** *(Registro do que foi rejeitado e depois revertido:)* a v3.x subamostrava snapshots >500 linhas para 500; a **D54 removeu o teto** — guarda-se a população-modelo **completa** de todas as gerações (o "filme" da busca é o diferencial da tese; a parede é de storage, resolvida com bucket-only para os 5 volumosos — §17.7). O custo (③ ≈ 0,5–0,9 TB) é aceito e medido no piloto. *(A opção "só o não-dominado por iteração" segue rejeitada — perderia a população-modelo completa.)*

**Granularidade dos classificadores par-a-par (c217, c122) — score agregado na bateria, vetor completo só no piloto.** Esses classificadores comparam cada candidato contra um conjunto de referência (~N/4 ≈ 13 soluções), gerando ~13 resultados que **agregam numa nota por candidato**. Decisão:
- **Bateria completa (~12,5k runs):** grava-se a **nota agregada por candidato** (`pred_score`) + a **confiabilidade da geração** (`Error1/Error2`) no log de auditoria §17.5.
- **Piloto (punhado de runs):** grava-se o **vetor completo de comparações** (candidato × referência: resultado + confiança), verbosidade máxima, para **auditar com o Claude que a fiação do classificador está fiel ao paper** (objetivo do D18).

**Racional (por que não o vetor completo em toda a bateria).** A maioria das comparações é **inauditável**: o candidato pontuado é um offspring novo, SEM fitness real (o classificador existe justamente para *não* avaliá-lo); só os poucos selecionados como infill ganham fitness real e podem ser conferidos contra a verdade. O vetor completo persistiria **~13× mais dado majoritariamente não-verificável**, sem abrir análise nova para a tese — o sinal verificável já está no `Error1/Error2` (medido pelo próprio algoritmo no arquivo real) + no cruzamento score×desfecho-real dos selecionados. O vetor completo agrega valor **no piloto** (QA da implementação), onde inspecionar cada comparação valida a correção; a §17.5 já prevê **verbosidade por fase**. *(O b4 bom/ruim faz 1 classificação por candidato — o L —, que já é 1 linha; suas 6 referências da geração, re-escolhidas a cada geração, vão no log de auditoria como contexto.)*

**Volumetria estimada por algoritmo (ordem de grandeza — o piloto mede exato; premissa D=10: 31D−1=309 aval. reais/run, init 109 + infill 200):**

| Alg | Tipo de surrogate | Real % | Real/run | Surr. consultas/run | Surr. guard./run | Surr. % |
|---|---|---|---|---|---|---|
| b1 | GP · valor escalarizado (μ/σ) | 100% | ~309 | ~2 M | ~50–100 k | ~3–5% |
| b3 | GP · μ/σ (K-RVEA) | 100% | ~309 | ~2–5×10⁵ | ~30–50 k | ~10–20% |
| e7 | NN-dropout · μ/σ | 100% | ~309 | ~2–5×10⁵ | ~30–50 k | ~10–20% |
| c141 | RBF · μ (σ geométrico SDE) | 100% | ~309 | ~2–5×10⁵ | ~20–40 k | ~8–12% |
| c238 | GP-kriging próprio · μ/σ | 100% | ~309 | ~4 M | ~20–40 k | ~0,5–1% |
| c262 | GP · μ/σ (BoTorch, qNEHVI) | 100% | ~309 | ~1 M | ~50–100 k | ~5–10% |
| c154 | GP · μ/σ (entropia, JES) | 100% | ~309 | ~5 M | ~50 k | ~1% |
| e81 | GP · μ/σ (Thompson) | 100% | ~309 | ~2 M | ~100 k (teto) | ~5% |
| c149 | NN-ensemble · μ+σ² (K=10) | 100% | ~309 | ~2×10⁷ | ~100 k (teto) | ~0,5% |
| b4 | FNN · **bom/ruim** (vs 6 refs) | 100% | ~309 | ~1–1,5 M | ~30–60 k | ~3–5% |
| c217 | PNN · **par-a-par**→score | 100% | ~309 (D15–21→465–650) | ~1 M | ~50–150 k | ~5–12% |
| c122 | 2×FNN · **par-a-par** (θ-dom)→score | 100% | ~309 | ~1 M | ~50–150 k | ~5–12% |
| e74 | **híbrido** (RBF μ + PNN classe) | 100% | ~309 | ~3–5×10⁵ | ~30–50 k | ~8–12% |
| b5 (off) | GP · μ/σ (Prob-RVEA/MOEA-D) | 100% | ~309 +final | ~40 k | ~8 k | ~20% |
| c311 (off) | árvore-GP local · μ+σ | 100% | ~309 +final | ~10⁵ | ~20 k | ~20% |
| e103 (off) | **seleção de modelo** (Kriging↔RBFN) | 100% | ~309 +final | ~9,9 k | ~2 k | ~20% |

**As duas leituras:** (i) **REAL = 100% em todos**, exatas 31D−1/run (~309 em D=10; ~929 em D=30), fonte das métricas oficiais — nunca amostramos; (ii) **SURROGATE = fração pequena** (0,5–20%): o modelo é consultado milhões de vezes, mas só os snapshots persistem; quanto mais pesado o otimizador interno, MENOR o % guardado (o teto corta mais).

**[D31] Camada de população real (3ª — membership-only):** só `(run_id, geracao, solution_id)` = dois inteiros por linha (comprimem muito em Parquet). Guardando **100% das gerações** de todos os online (~15k linhas/run × ~10k runs × ~5 B) ≈ **<1 GB no total** — a camada mais leve. O `x` e a `f` não se repetem (join pela camada real via `solution_id`).

**Peso estimado dos Parquets** (ordem de grandeza; piloto confirma) **[atualizado por D53/D54 — Higiene v5.2]**: **camada real <1 GB**; **camada de população real <1 GB** (membership-only); **tabela surrogate ≈ 0,5–0,9 TB** do estudo [D33/D54 todas as gerações **sem teto** + float32 + zstd, **sem** arredondamento (D53); o ~25–50 GB da estimativa antiga pressupunha o teto-500 + round3, ambos mortos]; log `.jsonl` menor. **Total ≈ 0,5–0,9 TB** (os 5 volumosos c154/c122/e81/c149/c262 = bucket-only, §17.7); catálogo+população reais <1 GB. O piloto confirma e afina por algoritmo. *(Piso: o vetor completo dos classificadores par-a-par só no piloto, senão +~50–90 GB — DEF-C2.)*

### 17.5 — Camada de auditoria de execução (log legível por run) [NOVO v3.0.3 — D18]
**Princípio (decidido pelo autor).** Além das camadas **real** (§17.1) e **surrogate** (§17.1), TODA execução de TODO algoritmo (os 13 online + 3 offline + pisos), em TODOS os regimes/experimentos, emite um **log de auditoria legível por run** — arquivo **`.jsonl`** (uma decisão/evento por linha; texto puro, greppável, legível e parseável, inclusive pelo Claude). **Propósito:** durante o piloto e as primeiras execuções, *auditar com o Claude que a implementação está fiel ao mecanismo do paper* — e, ao longo da bateria, capturar **resultados parciais** para detecção precoce de erros. É instrumento de **QA/fidelidade**; **não** é fonte de métrica (as métricas oficiais saem da camada real, §12). **[v5.2 — D97] O log é GRAVADO em runtime (as decisões internas do algoritmo são irrecuperáveis depois); a auditoria/validação de fidelidade a partir dele é MANUAL — do autor, a posteriori — não é código nem gate do harness (§20).** Distingue-se da camada surrogate (dados numéricos para análise, Parquet) por ser a **narrativa das DECISÕES** do algoritmo. **O que exatamente esses logs permitem auditar — pergunta × campo do log × veredito — está consolidado na §17.5.1.**

**Conteúdo mínimo comum a TODOS (o formato fino por algoritmo é refinado depois — DEF-C5):**
- **Cabeçalho do run:** `run_id`, algoritmo (+versão/hash do repo), problema, D, M, semente, regime, `maxFE`, hash do DoE inicial, ambiente (libs+versões), timestamp.
- **Por iteração/geração/infill — a decisão "qual caminho e por quê"** (generalização do c217 §17.2.1), quando o algoritmo escolhe COMO usar o modelo: K-RVEA (APD × incerteza + `Flag`), e7 (convergência × diversidade + razão de vetores), e103 (`KFlag` Kriging↔RBFN + teste 3σ), c141 (nível 1/2/3 da cascata + `|front|`), e74 (estratégia 1/2/3), b4 (regime R1/R2/R3), c122 (acordo Pareto-Net × θ-Net + confiança), c217 (estado 1/2/3, §17.2.1), b1 (λ sorteado + min/max da normalização), BO (valor da aquisição do escolhido, nº de restarts, refit) — cada um com o **motivo** (a desigualdade/condição que disparou o caminho).
- **Resultados parciais:** melhor-até-agora por objetivo, tamanho do arquivo não-dominado corrente, `fe_index`, e (quando barato) IGD/HV parcial — ou ao menos o conjunto ND corrente; wall-clock parcial. *(O tempo de fit do surrogate por retreino, antes só aqui, é **promovido a dado de primeira classe** na §17.6 — o log fica como cross-check.)*
- **Flags de guarda acionadas:** clamp de bounds (A4), NaN-guard, retry/erro-duro (A8), dedup, hard-stop/overshoot (A2) — cada guarda que definimos **loga quando dispara**.
- **Rodapé do run:** **[D23] status (`ok` | `retried_ok` | `failed`) + `n_retries` + stack trace se falhou**, FE final, nº de gerações, resumo. O mesmo status é gravado no manifesto/Parquet (§17.2) e contabilizado num **placar corrido de console** (sucessos × falhas acumulados) para acompanhamento em tempo real pelo operador e pelo Claude.

**Verbosidade por fase.** No **piloto**: verbosidade MÁXIMA (auditoria linha a linha com o Claude). Na **bateria completa**: mantém-se o essencial (decisões + parciais + flags); a verbosidade pode ser afinada por algoritmo/fase no refinamento. **Volume:** o `.jsonl` é pequeno perto da camada surrogate (§17.4); mesmo assim, o teto de verbosidade por fase entra no refinamento.

**Refinamento (na fila — DEF-C5).** O CONTEÚDO exato por algoritmo (campos, parciais, cadência, verbosidade) é refinado **junto com a DEF-C1** (schema dos classificadores) e distribuído no **lote de integração por stack** (passo 8 do ping-pong), com uma **passada de consolidação dedicada ANTES do piloto**. A D18 fixa o princípio e o mínimo comum; os formatos finos vêm depois, quando cada algoritmo estiver bem entendido.

### 17.5.1 — O que os logs permitem auditar (o contrato de auditoria de fidelidade a partir do log de execução — auditoria MANUAL do autor, D97) [NOVO — v4.0.2 · reenquadrado v5.2]

Esta subseção responde direto: **o que os logs (§17.5) + os números-âncora (§20) nos deixam auditar, e como se lê o veredito.** O princípio (D18) sempre foi *"encher a execução de logs com resultados parciais para auditar com o Claude se a execução e a implementação estão perfeitas"* — aqui isso vira um **checklist explícito**: cada pergunta de auditoria, o campo do log que a responde e o critério de veredito. É a generalização, para todo o pipeline, do *"o que a auditoria verifica"* que a §17.2.1 já faz para o c217.

| # | Pergunta de auditoria | O que no log responde | Veredito (o que confirma "está bem") |
|---|---|---|---|
| 1 | **A implementação é fiel ao MECANISMO do paper?** (o cerne) | a decisão *"qual caminho e por quê"* por iteração + o `motivo` (a condição que disparou): c217 estado 1/2/3, K-RVEA APD×incerteza+Flag, e103 KFlag+teste 3σ, c141 cascata 1/2/3, e74 estratégia 1/2/3, b4 R1/R2/R3, c122 acordo das 2 redes, BO valor da aquisição/refit | a **distribuição de caminhos** ao longo do run bate com o que o paper prevê (ex.: c217 estado 1 domina no início; inversão só quando p_menos>δ). Cruzado com o número-âncora (§20) = **dupla prova** (mecanismo + número) |
| 2 | **O PROTOCOLO (orçamento/DoE/semente) foi respeitado?** | cabeçalho (`maxFE`, hash do DoE, semente) + flags de hard-stop/overshoot (A2) + FE final no rodapé | **FE final = exatamente 31D−1** nos dois stacks; hash do DoE = o par compartilhado por (problema,semente); nenhum run passou do teto |
| 3 | **Os contratos de ADAPTER (bounds/sinal, §5.5) estão certos?** | flags de clamp de bounds (A4) + o sinal do objetivo entregue ao motor | o clamp **não** dispara o tempo todo (dispararia se o algoritmo amostrasse fora dos bounds → parametrização errada); BoTorch operando em [0,1]; a métrica saindo do `f` de minimização |
| 4 | **As GUARDAS numéricas estão segurando?** | flags de NaN-guard, Cholesky/PSD guard, dedup, retry/erro-duro (A8) + status do rodapé | a **taxa de disparo/falha por (algoritmo, característica)** é coerente e reportável; uma guarda disparando o tempo todo num algoritmo **denuncia** erro de implementação, não de otimização |
| 5 | **A TRAJETÓRIA de convergência é sadia?** | parciais: melhor-até-agora por objetivo, tamanho do arquivo ND corrente, IGD/HV parcial, `fe_index` | melhora ~monótona; o arquivo ND **não colapsa** para 1 ponto (colapso de diversidade); sem estagnação que sinalize busca quebrada |
| 6 | **As CORREÇÕES código×paper (Anexo K.3) estão aplicadas em runtime?** | o caminho logado reflete a **fiação corrigida**: c217 regime-NaN→ALEATÓRIO (não "maximiza"); kernel Matérn (c262/e81); treino no arquivo inteiro (b4); `[:, :M]` (c149) | o log mostra o caminho **corrigido** disparando; casa com o patch auditável (arquivo:linha) do Anexo K.3 |
| 7 | **O CUSTO/escalabilidade é o esperado?** | wall-clock parcial no log (cross-check) + a série de fit promovida à §17.6 | a curva `(n_acumulado, tempo_fit_s)` cresce como a família prevê — O(n³) do GP × ~linear do BNN (§17.6) |

**Como se usa (o fluxo).** No **piloto** (verbosidade máxima): roda-se cada algoritmo em ~1–2 `(problema, semente)`, abre-se o `.jsonl` **com o Claude** e percorre-se este checklist da linha 1 à 7 — confirmando mecanismo (1), protocolo (2–3), robustez (4), saúde (5) e correções (6) **ANTES** de comprometer a bateria completa (~16 mil runs). **[v5.2 — D97] Este percurso é um JULGAMENTO DO AUTOR (o Claude atua como assistente de leitura) — não uma asserção do harness; o harness não decide fidelidade.** Na **bateria**: os mesmos campos (já enxutos) continuam saindo, e as flags (4) + o status do rodapé alimentam o **placar corrido de console** → detecção **precoce** de erro, sem esperar a análise. É exatamente para isso que os logs existem: transformar *"a execução parece ok"* num **veredito auditável campo a campo**.

### 17.6 — Camada de tempo: custo computacional e curva de escalabilidade [NOVO — v4.0.1]

Duas saídas de tempo promovidas a **dado de primeira classe** (antes: só o total no manifesto §17.2 e o parcial no log de auditoria §17.5, que *não é fonte de métrica*). Servem a duas análises: **(a)** custo computacional por run comparado **entre famílias** de algoritmos; **(b)** a **⭐ curva de escalabilidade** — o achado-alvo dos dois sub-estudos (§V-B.3 online, §11.5 offline): *"a parede do GP (O(n³)) aparece nos dois regimes; BNN (online) e treed-GP (offline) a atravessam."* Sem esta camada o achado fica em inspeção qualitativa; com ela vira curva quantitativa.

**(1) Wall-clock por run (custo total).** Já no manifesto (§17.2); reafirmado aqui como dado de análise. **[v5.2.1 — CRÍTICO, auditoria da torre 2026-07-18: o bloco `timing` do manifesto estava ZERADO em 10/12 configs implementados (os walls só existiam em prosa). O preenchimento de `tempo_total_s` + desdobramento vira OBRIGATÓRIO nos 21 configs — retrofit DI-09.]** Grava-se o **tempo total do run** e, quando separável sem custo extra, o **desdobramento** `tempo_total_s`, `tempo_fit_surrogate_s` (soma de todos os retreinos), `tempo_busca_s` (aquisição/otimização interna) e `tempo_aval_real_s` (avaliação da função verdadeira) — para atribuir o custo ao **mecanismo** (treino do surrogate × busca × avaliação), não só ao relógio.
⚠ **Ressalva de stack (§19):** wall-clock entre **MATLAB e Python** é **confundido pela linguagem** — comparar custo **dentro** de cada stack, ou reportar com a ressalva explícita; nunca "família X é mais rápida que Y" cruzando stacks. A **curva (2)** é mais robusta a isso, porque mede o *escalonamento* (a forma da curva vs `n`), não segundos absolutos.

**(2) ⭐ Série de tempo de fit do surrogate por retreino.** Uma **mini-tabela** por run (Parquet leve, ou array no manifesto) — **uma linha por evento de retreino** (a iteração/geração em que o surrogate é re-treinado):

| coluna | significado |
|---|---|
| `run_id` | liga ao manifesto (algoritmo, problema, semente) |
| `geracao` / `iter` | quando o retreino ocorreu (sincroniza com ①②③ via `geracao`) |
| `n_acumulado` | nº de pontos reais no conjunto de treino **naquele** retreino (eixo-x da escalabilidade) |
| `tempo_fit_s` | tempo de treino do surrogate **naquele** retreino (eixo-y). **NULLABLE [DI-13.2]:** os pisos não treinam ⇒ `NULL` = "não se aplica" (≠ `0.0` = "treinou e custou zero") |
| `tempo_busca_s` | tempo da aquisição/otimização interna na mesma iteração — **OBRIGATÓRIO [v5.2.1, autor: era opcional]** |
| `tempo_pred_sonda_s` | **[DI-09 v5.2.1]** custo da sonda na iteração (0 quando não roda) |
| `tempo_geracao_s` | **[v5.2.1, autor]** wall TOTAL da geração (fit+busca+aval+overhead) — o relógio por geração, nos 21 configs (pisos: fit=NULL) |

O par `(n_acumulado, tempo_fit_s)` **é** a curva custo-de-treino × tamanho-de-dados: o O(n³) do GP aparece como crescimento super-linear; o retreino ~linear do **BNN (c149)** e o **treed-GP (c311)** aparecem achatados. É **barato** (um float por retreino; dezenas a centenas de linhas por run) e sai do **mesmo hook por geração** que já emite as camadas ②③ (§17.1) — o valor já era computado e apenas logado em §17.5; agora é promovido a coluna.

Aplica-se a **todo algoritmo com surrogate** (online e offline). Nos que **não retreinam** (offline de treino único — b5, c311, e103 no small/medium), a série tem **uma linha** (`n_acumulado` = tamanho do dataset; `tempo_fit_s` = treino único) — já basta para o ponto de custo do sweep. Nos **pisos MOEA puros** (sem surrogate) a série é vazia.

**(3) [OPCIONAL — refinamento, não bloqueio] RMSE global em test-set independente.** Para a análise de calibração (#6, fora dos top-5): exportar as **predições do surrogate final** sobre um **LHS held-out fixo por problema** (o mesmo held-out para todos os algoritmos → comparável) → um RMSE global num conjunto que o algoritmo **não** viu. O RMSE "no arquivo entregue" já é reconstruível de ①③ (§17.1) — logo isto é **refinamento** da calibração, não pré-requisito. Se ativado, grava-se um mini-Parquet `(run_id, problema, x_heldout_id, f_pred, sigma_pred)`; o `f_true` do held-out é fixo por problema (calculado uma vez).

### 17.7 — Topologia de persistência: onde cada run grava (local + bucket GCS) [NOVO — v4.0.3]

**Plano de execução (v4.0.3).** Os **experimentos Python** rodam nas **VMs do GCP Vertex AI**; os **experimentos MATLAB** rodam no **Mac (M1 Pro)**. A regra de gravação segue esse split:

- **Python** (`src/experiment.py`, chamado pelo despachante `experiments.py`; um run = um `(algoritmo, problema, semente)`): grava cada Parquet em **DOIS destinos** — local **e** bucket GCS.
- **MATLAB** (`src/experiment.m` / `experiments.m`): grava **APENAS local** (o Mac é a fonte; nada de bucket).

**Convenção de caminhos e nomes.** `{alg}` = o **id-acrônimo canônico** do algoritmo (o mesmo do manifesto e do Anexo I: `b1, b3, b4, e7, c217, c122, c141, e74, c238, c262, c154, e81, c149` online; `b5, c311, e103` offline). **[Higiene v5.2 — D55] O caminho e a base carregam o token de experimento `{exp}`** — sem ele, `off`×`sweep-*`×`batch` do mesmo `(alg,problema,semente)` colidiriam no mesmo arquivo (skip/overwrite silencioso — o próprio bug que a D55 fecha). `run_id = {exp}_{alg}_{problema}_{semente}` (`exp∈{main, off, batch, sweep-{tier}-{dist}}`); **pasta = `data/experiments/{exp}/{alg}/`**; base = `exp_{run_id}`:

```
# Python (VMs Vertex AI) — grava nos DOIS:
LOCAL :  data/experiments/{exp}/{alg}/exp_{exp}_{alg}_{problema}_{semente}.parquet
BUCKET:  gs://mestrado_experiments/experiments/{exp}/{alg}/exp_{exp}_{alg}_{problema}_{semente}.parquet

# MATLAB (Mac) — grava SÓ local:
LOCAL :  data/experiments/{exp}/{alg}/exp_{exp}_{alg}_{problema}_{semente}.parquet
```

> **Camadas por run (§17.1/§17.6).** Como o export tem camadas de tamanhos muito diferentes (① catálogo real, ② população/geração, ③ surrogate — a grande, §17.4 — e a série de tempo §17.6), a §17.3 já decidiu **separá-las por arquivo**. Realiza-se isso com um **sufixo de camada** sobre a base (com o token `{exp}` — Higiene v5.2/D55): `exp_{exp}_{alg}_{problema}_{semente}__surrogate.parquet` (③, o payload volumoso — ver §17.4, ~0,5–0,9 TB no total do estudo), `__real.parquet` (①), `__pop.parquet` (②), `__timing.parquet` (§17.6), **`__final.parquet` [DI-08 v5.2.1 — SÓ os 5 configs offline: o conjunto final avaliado 1× na função verdadeira via `src/problems.py`, pós-hoc, fora do orçamento (§11). **[DI-13.9] TODOS os finais são avaliados e o ND é filtrado DEPOIS da avaliação real** (filtrar pelo ND-do-modelo antes seria filtrar a realidade pela fantasia); colunas `x*|f*|origem_solution_id|origem_geracao|origem_linha|nd_pos_real` [DI-13.8]; o gate offline checa presença+consistência]**, mais o log de auditoria `exp_{exp}_{alg}_{problema}_{semente}.jsonl` (§17.5) e o fragmento de manifesto. O nome/pasta acima é a **base**; o sufixo distingue a camada. *(Nos runs Python, TODOS esses artefatos — parquets + `.jsonl` + manifesto — são espelhados no bucket, para uma VM Vertex AI destruída não levar embora nem dados nem trilha de auditoria; os **parquets** são os obrigatórios.)*

**Criar a pasta se não existe.**
- **Local:** antes de gravar, `Path(dir).mkdir(parents=True, exist_ok=True)` (Python) / `if ~exist(dir,'dir'); mkdir(dir); end` (MATLAB) — cria `data/experiments/{exp}/{alg}/` na primeira vez.
- **Bucket:** o GCS **não tem pastas de verdade** — "diretórios" são apenas **prefixos** no nome do objeto. Gravar o objeto `experiments/{exp}/{alg}/exp_....parquet` **cria o prefixo implicitamente**; não há "mkdir" a fazer (o prefixo `dataframes/` já existente no bucket é exatamente isso). Basta escrever no caminho certo.

**Como gravar no bucket (Python).** Escrever **local primeiro** (a fonte-de-verdade idempotente da esteira §19) e então **subir o mesmo arquivo** → local e bucket ficam **byte-idênticos**. Cliente recomendado `google-cloud-storage`:
`storage.Client(project="skilled-text-480300-d9").bucket("mestrado_experiments").blob(f"experiments/{alg}/{fname}").upload_from_filename(local_path)`.
Nas VMs Vertex AI a **conta de serviço** já traz credenciais (ADC) — sem chave em arquivo; basta a SA ter papel de escrita no bucket (`roles/storage.objectAdmin` em `mestrado_experiments`). *(Alternativa: gravar direto em `gs://…` via `pyarrow`+`gcsfs`; o local-first+upload é mais seguro — a cópia local sobrevive a falha de rede.)*

**Idempotência com dois destinos (§19).** O `skip_existing` usa o **arquivo local** como fonte-de-verdade da esteira. Um run está **plenamente persistido** quando local **e** blob existem; um passo leve de **sync** re-sobe qualquer local cujo blob falte (upload é idempotente — sobrescreve). O manifesto registra **os dois caminhos** + status do upload. Se o upload falhar, o run **não se perde** (o local existe) e o sync posterior completa.

**Classe de armazenamento do bucket = Standard ✓ [v4.2].** O bucket **`mestrado_experiments`** (us, multi-região; projeto `skilled-text-480300-d9`; não-público; exclusão reversível) é classe **Standard** — sem taxa de recuperação nem duração mínima: adequado ao ciclo gravar-agora/baixar-para-análise-em-semanas. Opcional: regra de ciclo de vida transitando objetos antigos para Nearline/Coldline após a fase de análise.

**MATLAB grava Parquet com as MESMAS reduções (§17.3/§17.4/D32/D35).** Sim — o MATLAB escreve Parquet nativo e aplica as reduções combinadas:
- **`parquetwrite(arquivo, T, 'VariableCompression','brotli')`** — **[FATO verificado v4.2]** o MATLAB do Mac (R2025a) aceita `{snappy, gzip, brotli, uncompressed}` — **sem zstd** (o zstd só existe em releases mais novas) → **o Mac grava `'brotli'`** (razão de compressão próxima) e a **consolidação em Python (§17.4)** re-encoda o export final para zstd — o codec é livre por-nó; o export final padroniza.
- **float32:** colunas numéricas como **`single`** (viram FLOAT no Parquet — metade dos bytes).
- ~~**arredondar a 3 casas:** `round(X,3)` antes de gravar~~ **[SUPERSEDIDO por D53 (v5.0): NÃO arredondar em nenhuma camada — o `round(X,3)` quantizava IGD/HV, colapsava o σ (10⁻⁴–10⁻⁶) e colidia o dedup-por-X. Manter float32 + zstd + ints + `real_solution_id`; só o arredondamento cai.]**
- **IDs e `geracao` inteiros:** `int32`/`uint32` (comprimem quase a nada).
→ Os Parquets do MATLAB-local ficam no **mesmo formato** dos do Python; a análise (§12) e a consolidação (§17.4) leem os dois indistintamente.

---

### S.7 — DEF-C5 consolidada: campos do `.jsonl` por algoritmo (além do mínimo comum §17.5)

| Config | Campos específicos por iteração/geração |
|---|---|
| b1 | λ sorteado; min/max da normalização; θ/dmodel resumo; Gbest; μ/σ da pop do GA interno; eventos: guard mse<0, NaN-guard, near-dup |
| b3 | \|A1\|; u efetivo; NumV1/NumV2/Flag; ramo (APD×σ); `index` exportado; eventos: guard Next=0, dedup DoE |
| b4 | (p0,p1,rr,tr); regime R1/R2/R3 + motivo; L dos selecionados; \|lote\| (0 = geração sem FE — contar stalls); eventos: guard randperm |
| e7 | Ratio/flag do infill; `min(A.objs)` (translação, C3); μ/σ̄ do Estimate; infill duplicado (FE desperdiçado); evento: guard sqrt |
| c217 | p+/p−/δ; **n_contradicoes (TestPre==1.5)** (S.3#4 "empates" ≡ M.4 "contradição" — MESMA quantidade, campo ÚNICO unificado no c217-fix-log [decisão do autor, v5.2]); ESTADO 1/2/3 + motivo (desigualdade); \|lote\|; scores selecionados (§17.2.1) |
| c141 | Fit1/2/3 resumo; ranks/Q/U; nível da cascata (1/2/3) + **telemetria de ativação do ramo (Q,U)**; \|subpops\| pós-ES_PDR; eventos: guard batch-vazio, guard +eps (L4) |
| e74 | estratégia (1/2/3); classe_PNN; μ_RBF; dist_dec/dist_obj; HV_gain; aceito/rejeitado-dedup (slot perdido); fração nível-1; RefPoint; evento: SelectTrainData reconstruído (S.3#1) |
| c238 | min/max do y-scaling da iteração (C3); [y,u,s] do escolhido; pop final do GA; eventos: EIM-NaN→0, guard range, chol-guard/dedup |
| c262 | seeds h1/h2; valor da acqf no escolhido; nº restarts; fit-retries; retry do optimize_acqf (deslocamento de RNG); **caminho fused/fallback** (S.3#9) |
| c154 | rota (a-default/b-paper) B9.5; S fronts amostrados (shapes); RuntimeError capturado; valor da acqf; restarts 5D/1000D |
| e81 | iteração; draws da posterior por geração (resumo); front+índice do select_candidates; **assert \|lote\|==q**; dedup disparado; dtype-check float64; nystrom==0 |
| c149 | val-MSE por rede (K=10); params do z-score da iteração; res.F resumo; HVI-greedy escolhido (q=1); tempo_fit por retreino (§17.6) |
| c122 | softmax do escolhido; agregados por categoria (Q1/Q2/Q3); accs de validação por classe; **eventos: skip-de-treino (gate), weight=None→re-init (S.3#3), retry-spin count**; f_min/f_max carregados (S.5) |
| b5 | modo (7/72/12); geração/arquivamento; n_restarts do GPR consumidos; substituições por P_wrong>0.5 (72) |
| c311 | nº de GPs por objetivo (`dict_gps`); `total_points_per_model_sequence`; iterações efetivas + early-stop; folha pior-MSE escolhida; evento: try do bfgs |
| e103 | CurGen; KFlag (Kriging↔RBFN); √MSE por geração; μ dos DOIS modelos; evento: quase-singularidade do RBFN (esperado, contar) |
| pisos | só o mínimo comum (cabeçalho, parciais, FE, rodapé) — sem surrogate |

### S.7.1 — Enriquecimento DI-10 do `.jsonl` [decisão do autor 2026-07-18 · v5.2.1]
**Mínimo comum NOVO em todo `<alg>_gen` (os 21):** `fe` · `f_best[]` (melhor por objetivo) ·
`n_front1` (|ND| corrente) · `modelo_hp` (hiperparâmetros/loss do fit — B1) · `tempo_fit_s`/
`tempo_busca_s` (B2) · `dist_min_arquivo` (por infill, espaço de decisão normalizado — B3) —
mais o evento `sonda` (§17.2.2). **Campos específicos ADICIONAIS por config** (regra: TUDO
read-only; grandezas que exigiriam patch invasivo no miolo stock NÃO entram — MOEA/D replace-count,
NSGA-III niching e genealogia de operadores REJEITADOS):

| Config | + DI-10 |
|---|---|
| b1 | λ VETOR completo; `ei_best`; `n_pool_ga` |
| b3 | `apd_sel`/`sigma_sel` (o PORQUÊ numérico da escolha por ramo); `n_vetores_vazios`; `adapt_delta_V` (norma da adaptação dos vetores de referência/ciclo) |
| b4 | os 6 `solution_id` das referências radiais da geração; `rr`/`tr` efetivos |
| e7 | `n_clusters_efetivo`; ramo/cluster de cada um dos K=3 infills; `loss_treino` |
| c217 | `n_best`/`n_worst` do treino; \|Pmid\| |
| c141 | `n_por_nivel` da cascata; hp do RBF |
| e74 | `n_por_nivel` do PNN; `k_local_efetivo` |
| c238 | `eim_mediana_pool` |
| c262/c154 | `acqf_todos_restarts` (a paisagem da aquisição = COMO o BO escolheu); `n_baseline`; `mll_final` |
| e81 | `n_baseline`; resumo dos draws de Thompson (min/med/max) |
| c149 | `hvi_top5`; `std_ensemble_sel` |
| c122 | `n_acordo`/`n_desacordo` das 2 redes por geração |
| b5 | pesos de decomposição do b5m no HEADER (determinísticos, 1×); `p_wrong_stats` |
| c311 | `n_folhas` + `profundidade` da árvore por iteração |
| e103 | `divergencia_modelos` (mean\|μ_Krig−μ_RBFN\|/geração); `margem_3sigma` |
| pisos | `n_front1`; `f_best[]`; ideal/nadir da pop; vetores de decomposição do moead/nsga3 no HEADER (1×) |

*(Expansão didática completa + racional por campo: `CONTRATO_DE_DADOS.md` §6.1, raiz do repo.)*
