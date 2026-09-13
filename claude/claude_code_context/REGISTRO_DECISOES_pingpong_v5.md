# REGISTRO DE DECISÕES — Ping-pong pós-red-team (material da SPEC v5.0)

> **O que é este arquivo.** Registro vivo das decisões do ping-pong aberto após a revisão externa da SPEC v4.2/v4.3 por 6 pareceres independentes (consolidados e deduplicados em **32 decisões [PP] + 1 lote de higiene [β]**). A cada rodada, uma decisão entra aqui **ricamente descrita** (problema → opções → decisão do autor → racional → efeitos na SPEC). **Nada é aplicado à SPEC durante o ping-pong**; ao final, este registro inteiro é injetado de uma vez na SPEC — que vira a **v5.0** — respeitando a organização e o formato da refatoração (v3.3+): decisões novas entram no **Anexo D** (numeração continuada D53+), efeitos aplicados nas seções vigentes com carimbo, changelog no **Anexo R**, higiene β numa passada mecânica única.
> **Numeração:** continua a série do Anexo D (última: D52; refatoração: REF-1..7). Este registro começa em **D53**.

---

## Fila do ping-pong (status)

| # | Decisão | Status |
|---|---|---|
| A1 | Arredondamento por camada + fonte da métrica | ✅ **D53** |
| A1b | Teto de 500 aval.-surrogate/iteração | ✅ **D54** |
| A2 | Identidade do run (token de experimento) | ✅ **D55** |
| A3 | b5 = 1 ou 2 configs offline | ✅ **D56** |
| A4 | `solution_id`: semântica + geração + cache-por-x | ✅ **D57** |
| A5 | "Run concluído" + escrita atômica + manifesto + skip-local | ✅ **D58** |
| B1 | Ordem do `rng` × topologia MATLAB | ✅ **D59** |
| B2 | Watchdog 2 níveis (chamada da ponte + run) + teto de iterações sem FE | ✅ **D60** |
| B3 | Hard-stop no meio do lote + exceção Python + c238 | ✅ **D61** |
| B4 | Fórmula canônica das sementes internas h()/g() | ✅ **D62** |
| B5 | DoE cross-stack como artefato (formato + hash + teste bit-a-bit) | ✅ **D63** |
| B6 | Backup do lado MATLAB | ✅ **D64** (sem backup automático) |
| C1 | N/varredura dos pisos (protocolo pré-registrado) | ✅ **D65** |
| C2 | V-B.4: K/orçamento batch + roster + Sobol | ✅ **D66** |
| C3 | MVNS: μ, Σ, espaço, clipping | ✅ **D67** |
| C4 | Avaliação final offline: cap do \|ND\| | ✅ **D68** (sem cap) |
| D1 | Enunciado único do ref-point do HV | ✅ **D69** |
| D2 | Endpoint primário + tabela operacional dos 4 testes + blocos do Friedman | ✅ **D70** |
| D3 | §15 operacional: matriz 25×8 + unidade + multiplicidade | ✅ **D71** |
| D4 | Reference set 2-obj por segmento + cache BBOB + notas | ✅ **D72** |
| D5 | Enquadramentos de honestidade (online×offline; vantagens informacionais; IGD+) | ✅ **D73** |
| E1 | DEF-L5 (e74 × CalHV em BBOB) | ✅ **D74** |
| E2 | JES/B9.5: dono + rota pré-registrada | ✅ **D75** |
| E3 | Máscara do e74 + registrar L4/L8 | ✅ **D76** |
| E4 | Casa do piso offline MOEA/D-média | ✅ **D77** |
| E5 | Fallbacks dos SPOFs (c149/c311) | ✅ **D78** |
| F1 | LOTE infra (multi-env, BLAS/OMP, ponte, licença, pilotos Linux) | ✅ **D79** |
| F2 | LOTE reprodutibilidade (SHA repos, anchors.json, .patch, lockfiles, schema_version) | ✅ **D80** |
| F3 | LOTE qualidade (testes F0, CP-fonte-única/bounds/sinal, protocolo de falha, ±3σ) | ✅ **D81** |
| F4 | LOTE cartões (Cartão A análise, sub-estudos, consolidação, R1∥R2) | ✅ **D82** |
| F5 | LOTE handoff (CLAUDE.md, precedência, bundles, artefatos machine-readable) | ✅ **D83** |
| F6 | Cronograma: escada de prioridade + gate de timing numérico | ✅ **D84** |
| F7 | Semente 42: manter (preferência do autor, sem racional fabricado) | ✅ **D85** |
| G1 | Higiene de memória intra-run (c149/torch; ponte MATLAB↔pymoo) + eixo de RAM no piloto | ✅ **D86** (pós-encerramento, red-team 2) |
| β | Lote de higiene mecânica (~35 edições sem decisão) | ✅ (executada na injeção v5.0) |

**🏓 PING-PONG ENCERRADO em D85 (33 decisões) → injetado na SPEC v5.0. Adendo pós-encerramento: D86 (2ª rodada de pareceres externos, lidos sobre a v4.2/v4.3) → SPEC v5.1.**

---

## D53 — Fim do arredondamento a 3 casas decimais (mantidas as demais táticas de economia) [decidido 2026-07-14]

**O problema.** As decisões D32/D35 aplicavam a TODAS as tabelas do export as reduções: arredondamento a **3 casas decimais** + float32 + zstd. Três dos seis pareceres do red-team convergiram nos danos: (1) a métrica oficial (§12) lê o `f` da camada ① — arredondado a 3 casas (resolução absoluta ~5×10⁻⁴), ele **quantiza IGD/HV exatamente na faixa onde algoritmos convergidos se separam** (ZDT/DTLZ em escala [0,1]), fabrica **empates artificiais** no Wilcoxon pareado (perda de poder do teste que justifica o pareamento por DoE) e **inviabiliza conferir âncoras finas** (e103: IGD 4,596×10⁻³ ± 1,3×10⁻⁴); (2) o **σ da camada ③ morre**: GP em fim de run tem σ ~10⁻⁴–10⁻⁶ → 3 casas *decimais* (régua absoluta) o colapsam para 0.000 — destruindo a análise de calibração (D49) do eixo que dá **título à tese**; (3) `x` arredondado pode colidir pontos distintos no dedup-por-X. Agravante: a economia no ①/② é ilusória (custam <1 GB; todo o ganho de storage vem da ③).

**Opções apresentadas.** (1) Reduções por camada: ①/② cruas em float64 + ③ em 5 dígitos *significativos* + float32 + zstd (recomendação do assistente); (2) manter 3 casas em tudo (status quo); (3) tirar toda redução, float64 cru inclusive na ③ (volumetria explode ~100–300 GB sem ganho analítico).

**✅ DECISÃO DO AUTOR (variante própria, mais simples que a Opção 1): parar de arredondar EM TUDO; manter float32 EM TUDO; manter todas as demais táticas de economia.**
- **Sem arredondamento** em nenhuma tabela (nem 3 casas, nem dígitos significativos) — o dado vai como float32 cru.
- **float32 mantido em todas as camadas** (inclusive ①) para economizar espaço.
- **Mantidas:** compressão zstd, IDs/`geracao` como inteiros (dict/RLE), `real_solution_id` evitando repetir `x`, separação de arquivos por camada.

**Racional registrado.** Regra única e uniforme (mais simples de implementar e auditar que um regime por camada); o float32 tem ~7 dígitos significativos (erro relativo ~10⁻⁷) — resolução de sobra para as métricas (âncoras na escala 10⁻³±10⁻⁴ permanecem conferíveis) e para o σ (10⁻⁶ é representável sem perda relevante em float32, cujo menor normal é ~10⁻³⁸); elimina os 3 danos apontados pelo red-team sem abrir mão da economia estrutural.

**Consequências/efeitos na injeção v5.0.**
- **Supersede parcialmente D32/D35**: cai apenas o item "arredondamento a 3 casas"; float32+zstd+inteiros+`real_solution_id` permanecem (espírito da compressão preservado).
- §17.2/§17.4 (texto das reduções), **§17.7** (a receita MATLAB perde o `round(X,3)` — fica `single` + zstd/brotli), §0 (linha do export), cartões S.4, Anexo D (nova linha D53), Anexo R (changelog).
- **Frase da fonte da métrica cravada junto** (parte do pacote A1, sem controvérsia): *"a métrica lê o `f` GRAVADO na camada ① (que já é a re-avaliação limpa feita no momento da escrita); a análise nunca re-avalia."* — encerra a ambiguidade §0×§12 apontada pelo red-team.
- **Notas técnicas registradas:** (i) o erro relativo ~10⁻⁷ do float32 no ① é aceito e documentado (inócuo para IGD/HV/testes; âncoras finas seguem verificáveis); (ii) o dedup-por-X usa **os bytes float32 gravados** como chave (consistente entre stacks; colisões <10⁻⁷ são quase-duplicatas genuínas e inofensivas); (iii) volumetria da ③ recalculada: float32 sem round comprime um pouco pior que com round (~1,3–2×) — nova estimativa incorporada no D54 abaixo.

---

## D54 — Fim do teto de ~500 avaliações-surrogate/iteração ("salvar TUDO") + topologia de persistência por algoritmo [decidido 2026-07-14]

**O problema.** O D27/DEF-C2 limitava a camada ③ a ~500 linhas por iteração (subamostragem uniforme quando o otimizador interno avalia mais). O teto **só dispara em 5 configs, todas Python/VM**: c154 (pool de aquisição 1000·D/iter — até 30k linhas), c122 (7.000 offsprings pontuados/iter), e81 (pop final 100·D), c149 (pop final 1.000), c262 (raw 512, marginal). Nos 11 MATLAB + pisos o teto nunca dispara (populações ≤ ~300). Subamostrar descarta dado **irrecuperável** (re-obter custaria re-rodar a bateria); por outro lado, "tudo" multiplica a ③ por ~10.

**Análise de custo apresentada (com D53 aplicado — float32 sem round):** ③ com teto ≈ 30–65 GB; **③ TUDO ≈ 0,5–0,9 TB**, dominada por c154 (~250–450 GB) e c122 (~110–170 GB). Viabilidade: bucket Standard ≈ **US$ 10–20/mês**; egress único ~US$ 55–80 se baixar tudo ao Mac (ou ~zero analisando na VM); escrita por iteração desprezível frente ao custo do GP; consolidação mais lenta porém tratável (Parquet particionado). **Restrição nova declarada pelo autor: a VM tem só 100 GB de disco.**

**Opções apresentadas.** (1) TUDO com salvaguardas (prune-local-pós-sync, partição por algoritmo, teto local futuro só se o piloto estourar projeção); (2) TUDO seletivo (populações de busca sem teto; teto 2.000 nos dois "floods" c154/c122); (3) manter 500.

**✅ DECISÃO DO AUTOR: Opção 1 — TIRAR O TETO e salvar TUDO, com topologia de persistência DIFERENCIADA por algoritmo (resolve os 100 GB da VM):**
- **Os 5 que disparariam o teto (c154, c122, e81, c149, c262): salvam APENAS NO BUCKET** (`gs://mestrado_experiments/...`) — sem cópia durável na VM.
- **Todos os demais algoritmos Python: mantêm o dual-write** (VM local + bucket), como no §17.7.
- **MATLAB/Mac: inalterado** (só local; o teto nunca disparava lá).

**Racional registrado.** "Quero tudo": dado de tese descartado na escrita é irrecuperável, e a pergunta de 2027 não é conhecida hoje; o custo real (~US$ 15/mês + egress único) é ordens de magnitude menor que re-rodar; a topologia bucket-only nos 5 volumosos elimina a pressão sobre os 100 GB da VM sem tocar no desenho dos demais.

**Consequências/efeitos na injeção v5.0.**
- **Supersede o TETO do D27** (a subamostragem-500 morre); **as políticas por classe do D27 permanecem** (o que constitui o snapshot: EA = pop selecionada/geração; BO-EA-interno = pop final da aquisição/iter; BoTorch = candidatos avaliados dos restarts+pool).
- **§17.7 ganha a topologia por algoritmo:** classe "bucket-only" = {c154, c122, e81, c149, c262} — implementação recomendada: gravar em staging local transitório → upload → verificação (tamanho/hash) → **delete local imediato** (prune-pós-sync); alternativa direta via `gcsfs` aceitável. *(Interpretação registrada: TODAS as camadas desses 5 seguem bucket-only — as camadas pequenas ①/②/timing/jsonl custam ~nada em qualquer lugar, e uma regra única por algoritmo é mais simples; corrigir aqui se o autor preferir bucket-only só para a ③.)*
- **⚠ Consequência operacional crítica (entra no cartão F0):** para os 5 bucket-only, o **`skip_existing`/resume consulta O BUCKET**, não o disco local — senão uma VM recriada re-roda tudo.
- Volumetrias de §17.4/§17.7/S.8 atualizadas (③ total ≈ 0,5–0,9 TB; VM local permanece ≲ 40–80 GB pelos demais algoritmos, dentro dos 100 GB — com margem monitorada no piloto).
- **Regra herdada do red-team (achado #46), registrada junto:** se algum teto LOCAL voltar no futuro (ex.: piloto revelar c154 >> projeção), a subamostragem será **determinística** (seed = hash(run_id, geração)) — nunca mais amostragem não-reprodutível.
- Anexo D (nova linha D54), Anexo R (changelog), cartões S.4 (F0: resume-via-bucket; R2/R3: prune-pós-sync nos 5).

---

## D55 — Identidade do run: token de experimento em run_id, arquivos, pastas e manifesto [decidido 2026-07-14]

**O problema.** O nome-base era `exp_{alg}_{problema}_{semente}` e o `run_id` não tinha formato. Mas o mesmo trio (algoritmo, problema, semente) roda em experimentos DIFERENTES: c149/c262/e81/c154 no principal (q=1) E no large-batch (q=10); b5/c311/e103 no offline principal E no sweep (3 tiers × 2 distribuições). Mesmo trio → mesmo nome → o `skip_existing` pula o run do sub-estudo achando que já rodou, ou sobrescreve o do principal — bug silencioso que só aparece na análise (achado do red-team, 1 parecer, verificado).

**Opções.** (1) Token de experimento em tudo; (2) manter nome e separar só por pastas+colunas de manifesto (colisão ainda possível); (3) run_id opaco UUID/hash (hostil a grep/humano/auditoria).

**✅ DECISÃO DO AUTOR: Opção 1 (recomendada).**
- **`run_id` canônico = `{exp}_{alg}_{problema}_{semente}`**, com `exp ∈ {main, off, batch, sweep-{tier}-{dist}}`, `tier ∈ {small, medium, big}`, `dist ∈ {lhs, mvns}` (ex.: `main_c262_ZDT1_7`, `batch_e81_DTLZ2_42`, `sweep-big-mvns_c311_MMF1_3`).
- **Arquivos e pastas herdam o token**: `data/experiments/{exp}/{alg}/exp_{run_id}__{camada}.parquet` (local e bucket, mesmo prefixo); o log `.jsonl` e o fragmento de manifesto usam a mesma base.
- **Manifesto ganha colunas explícitas**: `exp`, `regime`, `q`, `tier`, `dist` (além de alg/problema/semente/status).

**Racional.** Colisão impossível por construção; partição física natural por experimento (a análise filtra sem ler nada a mais); legível por humano e grep — coerente com toda a filosofia de auditabilidade. Custo zero: o F0 ainda não foi implementado.

**Efeitos na injeção v5.0.** §17.7 (template de nomes/pastas — supersede o template da REF-4 na parte do nome), §0 (linha da persistência), cartão F0 (naming + colunas do manifesto + o resume-via-bucket do D54 usa o run_id novo), §19 (manifesto), Anexo D (D55), Anexo R. O log `.txt` do c217 (§17.2.1) adota a mesma base de nome (fecha o achado menor #47 do red-team — vai no lote β).

---

## D56 — b5 = DUAS configs offline: `b5r` (Prob-RVEA) e `b5m` (Prob-MOEA/D) [decidido 2026-07-14]

**O problema.** O grid contava o offline como 4 configs (3 SA-MOEA + 1 piso) = 3.000 runs, mas o "b5" são DOIS algoritmos com mecanismos de seleção distintos: mode 7 = **Prob-RVEA** (APD probabilístico — média do APD amostrado, aproximação não publicada) e mode 72 = **Prob-MOEA/D** (decomposição com MC pareado — o modo **quase-fiel ao paper**). A §6.4 já parametrizava os dois como linhas separadas; a tabela de planejamento do autor lista "Prob-RVEA / Prob-MOEA/D". Rodar um só descartaria ou o modo fiel (72) ou o headline do paper (7).

**Opções.** (1) Rodar os dois como configs separadas; (2) só Prob-RVEA (mantém a aproximação não publicada, descarta o quase-fiel — irônico); (3) só Prob-MOEA/D (descarta o método-título).

**✅ DECISÃO DO AUTOR: Opção 1 (recomendada) — rodar OS DOIS como configs separadas.**
- **Tokens canônicos:** `b5r` = Prob-RVEA (mode 7) e `b5m` = Prob-MOEA/D (mode 72) — entram assim no run_id (D55), no manifesto, no Friedman e em todos os exports.
- **As variantes Hyb (modes 8/82) seguem FORA** (decisão anterior mantida: o próprio paper mostra Hyb não superando Prob).

**Racional.** Mecanismos genuinamente diferentes que o paper trata como métodos distintos; o offline é barato (<1 dia de VM — +750 runs custam horas); o quadro offline fica mais rico (5 configs); captura os dois lados da fidelidade (72 quase-fiel + 7 headline).

**Efeitos na injeção v5.0 (recontagem canônica).**
- **O estudo segue com 16 *ids* de algoritmo** (b5 = 1 id com 2 configs) — a nota "dois 16" da §1.5 ganha a terceira cláusula: *16 ids · 17 séries SA-MOEA (13 online + 4 offline)*.
- **Grid offline: 5 configs** (b5r, b5m, c311, e103 + piso MOEA/D-média) × 25 × 30 = **3.750 runs** (antes 3.000). Total principal: 12.750 + 3.750 = **16.500 runs**.
- §0 (tabela do grid), §1.5, §3.3 (roster com os 2 modes rotulados), §6.4 (linhas b5r/b5m), §14 (Friedman offline com 5 colunas), S.8 (timing do b5 ×2 — segue <1–2 dias), sweep §11.5 (b5r e b5m herdam os dois? — **sim, ambos entram no sweep**, tiers small/medium, coerente com "mesmo roster do offline"), Anexo D (D56), Anexo R.

---

## D57 — `solution_id`: identidade da SOLUÇÃO, geração sequencial, igualdade bit-a-bit, casamento na emissão [decidido 2026-07-14]

**O problema.** O `solution_id` é a chave que costura as 3 camadas do export (①↔②↔③ via `real_solution_id`) e o red-team achou: (a) definição contraditória ("por solução/dedup-X" × "por avaliação"); (b) ausência de regra de geração (ordem? escopo? formato? idêntico entre MATLAB e Python?); (c) mecanismo de casamento do `real_solution_id` indefinido (igualdade em float? antes/depois do float32? emissão ou pós-hoc?). Somado: a chave de igualdade do cache-por-x (§5.4) nunca foi definida.

**Opções.** (1) Pacote "identidade da solução, resolvido na escrita" (recomendada); (2) id por avaliação (quebra o dedup do ①/D35); (3) id = hash/UUID do x (perde ordem temporal, opaco).

**✅ DECISÃO DO AUTOR: Opção 1 (recomendada).**
1. **Semântica:** `solution_id` = identidade da **solução** (dedup por X). 1 id por `x` único no run; ① tem exatamente 1 linha por id (com `first_fe_index`); re-encontros **reusam** o id; ② referencia o id em quantas gerações for.
2. **Geração:** inteiro sequencial **pela ordem da 1ª avaliação real** (DoE = 0…11D−2; infills na sequência). Escopo = run; unicidade global = par (`run_id`, `solution_id`). Idêntico nos 2 stacks **por construção** (toda avaliação passa pelo ponto único do wrapper/contador — o mesmo do hard-stop D21).
3. **Chave de igualdade** (cache-por-x E dedup do ①): **bytes exatos do x em float64** no ponto de avaliação — bit-a-bit, SEM tolerância. Nota documentada: o ① armazena x em float32 (D53); dois x distintos abaixo da resolução float32 = 2 ids com x gravado idêntico — inócuo (join é por id).
4. **`real_solution_id` (③→①):** casado **no momento da emissão**, consultando o mesmo dicionário do cache; grava id ou NULL. **Proibido** matching por float na análise.
5. **Cache-hit = 0 FE mantido** (§5.4 intacto); a guarda contra "saldo congelado" (e7 re-propondo x conhecido) fica na **B2** (teto de iterações sem consumo de FE).

**Racional.** Consistente com D34/D35; join exato e gratuito (o dicionário do cache já existe no mesmo processo); determinístico e idêntico entre stacks; elimina qualquer matching frouxo — a classe de bug mais difícil de detectar na análise.

**Efeitos na injeção v5.0.** §17.2 (definição única do `solution_id` + mock atualizado; some a frase "único por avaliação"), §5.4 (chave do cache cravada), §17.1/§17.3 (emissão da ③ com lookup no dicionário), cartão F0 (wrapper: contador + dicionário + atribuição de ids), DDL do schema (F5), Anexo D (D57), Anexo R.

---

## D58 — "Run concluído", escrita atômica, manifesto por fragmento + parâmetro de skip rápido por parquets locais [decidido 2026-07-14]

**O problema.** O manifesto `run_id → status` é o coração da esteira, mas: (1) sem formato/nome/local definidos; (2) o resume por "arquivo local existe" pula para sempre um Parquet **truncado** por worker morto no meio da escrita (corrupção silenciosa — 3 pareceres); (3) multi-máquina (Mac + VMs) com manifesto compartilhado = corrida de escrita; (4) os 5 bucket-only do D54 precisam de resume que olhe o bucket.

**Opções.** (1) Fragmento por run + escrita atômica + "pronto = manifesto ok E arquivos válidos"; (2) manifesto único com lock/SQLite (contenção, locks em FS de rede são traiçoeiros); (3) status quo (bomba do truncado).

**✅ DECISÃO DO AUTOR: Opção 1 (recomendada).**
- **Escrita atômica universal:** todo artefato nasce `*.tmp` → `rename`/`movefile` para o nome final (atômico no mesmo FS); no GCS o objeto só aparece completo + verificação tamanho/hash.
- **Manifesto = 1 fragmento JSON por run** (`{run_id}.manifest.json` ao lado dos Parquet, local e/ou bucket conforme D54): status {started→ok/retried_ok/failed}, timestamps, wall-clock + desdobramento (§17.6), FE final, hashes (DoE + arquivos), n_retries, stack trace, versões, `schema_version`. **Zero lock, zero corrida** (nada compartilhado); merge dos fragmentos na consolidação (grep-ável).
- **Critério de "pronto" (resume completo):** fragmento com status ok/retried_ok **E** todos os sufixos de camada presentes **E** footers dos Parquet válidos (pyarrow). Bucket-only (D54) → checagem nos blobs.

**➕ ADIÇÃO DO AUTOR — parâmetro de skip rápido por parquets locais:**
- Parâmetro (ex.: `--skip-if-local-outputs`) que considera um run **PRONTO se os parquets que ele gera já existem na pasta LOCAL** (NÃO olha o bucket) → não re-executa. Modo rápido de resume (o default operacional que o autor quer).
- **Por que é seguro (reconciliação com o D58):** com a escrita atômica (tmp→rename), um parquet de nome final é sempre COMPLETO → "existe local com nome final" ≈ "completo". A checagem exige **todos os sufixos de camada** (①②③+timing) presentes, senão o run morreu no meio.
- **Bucket-only (D54) — regra confirmada pelo autor:** c154/c122/e81/c149/c262 não gravam parquet durável local. Para eles, o resume **lista os objetos do bucket** e checa se já existe um objeto com o **nome do experimento** no prefixo onde ele gravaria (`gs://mestrado_experiments/experiments/{exp}/{alg}/exp_{run_id}__*.parquet`) — exatamente a mesma lógica do skip-local, só que sobre o bucket. Se existe → **pula e imprime "[skip] {run_id} já pronto"**. (Otimização opcional: listar o prefixo `{exp}/{alg}/` uma vez por lote e casar em memória, evitando um HEAD por run.) O fragmento de manifesto continua sendo escrito em todos os configs (fonte de status/timing/auditoria) mesmo quando o resume usa o atalho de existência.

**Racional.** Elimina a armadilha do Parquet truncado; multi-máquina sem coordenação (cada run autocontido — espírito "embaraçosamente paralelo"); merge trivial e auditável; o atalho local dá resume barato sem reintroduzir risco (a atomicidade garante).

**Efeitos v5.0.** §19 (escrita atômica + fragmento + regras de resume + o parâmetro + resume-via-bucket dos 5), §17.7, cartão F0 (implementar o wrapper de escrita atômica, o fragmento, os dois modos de resume), DDL do schema (F5, com `schema_version`), Anexo D (D58), Anexo R. Fecha os achados #9 e a parte "escrita atômica/resume" do red-team.

---

## D59 — Topologia MATLAB = `parfor` canônico; `rng(seed)` DEPOIS de construir o Problem, com isolamento do probe [decidido 2026-07-14]

**O problema.** (i) Contradição vinculante: D24/L7 mandava semear ANTES do UserProblem; §0/§16.5/N.0/N.4/§22 mandavam DEPOIS. (ii) Topologia do Mac ambígua: pool `parfor` (workers persistentes) × 1 processo `matlab -batch` por run (A12). Nó técnico: o construtor do UserProblem faz um "probe" (`Initialization(1)`) que consome RNG + 1 avaliação real (descartada, `FE=0` em ALGORITHM.m:80). **Os revisores DISCORDARAM** — um pró-ANTES (D24, alega que DEPOIS não é bit-reprodutível), outro pró-DEPOIS (convenção v4.x, parfor-aware).

**Opções.** (1) `parfor` canônico + semear DEPOIS, com **isolamento do probe** (algoritmo começa exatamente em rng(seed), idêntico entre workers; o probe aleatório é descartado e os hooks de cache/catálogo só ligam no Solve → não vaza); A12 vira scale-out em VM. (2) semear ANTES (D24). (3) `matlab -batch` por run (~10–20 s startup × 16.500 = dias só ligando o MATLAB).

**✅ DECISÃO: Opção 1.** A objeção pró-ANTES ("depois não é bit-reprodutível") só valeria se o probe vazasse para o catálogo — e não vaza (descartado + hooks no Solve). Ganha-se "algoritmo começa exatamente no seed" (trivialmente igual entre workers/topologias) + é a convenção das 5 seções v4.x.
- **Requisito explícito cravado: isolamento do probe** — a avaliação e o sorteio do probe NUNCA tocam cache, catálogo ①, contador de FE ou hook (garantido: hooks anexam no `Solve`, FE reseta). Isso neutraliza a objeção do revisor pró-ANTES.
- **e103 sempre em worker MATLAB dedicado** (N.3, poluição de path).
- **Receita `parfor` por worker:** `addpath(genpath(PLATEMO))` → construir UserProblem (com DoE injetado) → `rng(seed,'twister')` → construir Algorithm(`'save',0,'outputFcn',@hook`) → try/catch Solve → ler `Algorithm.result`.

**Efeitos v5.0.** **Supersede D24/L7 na ordem do rng** (carimbar "SUPERSEDIDO por D59"); rebaixa **A12** a "modo scale-out em VM (matlab -batch), não o do Mac"; §0/§16.5.3/N.0.2/N.4/§22.2 já dizem DEPOIS (mantêm; ganham a cláusula do isolamento do probe); K.5.2-L7 marcado supersedido. Anexo D (D59), Anexo R.

---

## D60 — Watchdog de 2 níveis (chamada da ponte + run) + teto de iterações sem consumir FE [decidido 2026-07-14]

**O problema.** `maxRuntime=inf` (correto) remove o relógio interno mas nada o substitui. Stalls documentados: b4 "0-FE sem limite", c122 regenera 7.000 offsprings sem gastar FE, e a **ponte Python pode pendurar por IPC sem lançar erro** → o try/catch+1 retry (D23) nunca dispara (o run não termina). Além disso: cache-hit=0 FE (§5.4) + e7 sem dedup de infill → o saldo pode **nunca zerar** → hard-stop nunca chega → run potencialmente infinito.

**Opções.** (1) Três guardas; (2) só timeout por run (não pega o saldo-congelado se cada iteração é rápida); (3) nada.

**✅ DECISÃO: Opção 1 — três guardas complementares** (valores pinados no piloto de timing):
- **(a) Timeout na chamada do `evalFcn` da ponte** — pega o pendura IPC/sidecar Python → mata a chamada, loga o run como `failed`, segue. *(Cobre o "sidecar Python trava/vaza memória no parfor" apontado por 2 pareceres.)*
- **(b) Timeout por run** (wall-clock) = múltiplo (ex.: 5×) do pior caso medido no piloto para aquele (alg, faixa-de-D) → mata o run, `failed`.
- **(c) Teto de iterações sem consumo de FE** (ex.: N iterações consecutivas com Δfe=0) → pega o stall lógico (algoritmo gira rápido mas não progride; saldo congelado).

**Racional.** Os três modos de morte (IPC/pendura, wall-clock, stall lógico) são distintos e um não cobre o outro; toda parada vira `failed` no manifesto (dado de robustez, D23). Sem eles, um run pendurado ocupa o worker para sempre.

**Efeitos v5.0.** Novo bloco em §19 (política de watchdog) + N.1 (Python) + N.0 (MATLAB); cartão F0 (implementar as 3 guardas, valores parametrizáveis pinados no piloto); §17.6 (o timeout usa o pior-caso da série de tempo); Anexo D (D60), Anexo R. Fecha os achados de stall (b4/c122) + o "saldo congelado" (§5.4×e7).

---

## D61 — Hard-stop no meio do lote: avaliar o saldo, gravar, e então lançar (exato 31D−1 nos 2 stacks) [decidido 2026-07-14]

**O problema.** Com `once=true` a ponte recebe o lote inteiro. Se **saldo < tamanho do lote**, qual a regra? Lançar sem avaliar → FE final **< 31D−1**, violando o D21 ("exatamente 31D−1"). E o Python não tinha exceção equivalente à `PlatEMO:Termination` definida (classe? captura? repos que engolem exceção como o c149?).

**Opções.** (1) Avaliar os primeiros `saldo` pontos do lote, gravá-los no ①, e então lançar; (2) parar antes de avaliar (FE < 31D−1, quebra o pareamento); (3) deixar estourar e truncar pós-hoc (mas o D21 escolheu hard-stop *em vez de* truncar).

**✅ DECISÃO: Opção 1.** No ponto único de avaliação (o `evalFcn` da ponte / o wrapper de FE no Python), quando o lote recebido excede o saldo: **avalia exatamente os primeiros `saldo` pontos, grava-os no catálogo ①, e então lança a terminação** → todo run fecha em **exatamente 31D−1**.
- **MATLAB/c238-standalone:** lança `MException('PlatEMO:Termination')` (o mesmo id que o Solve engole; c238 via N.5 usa o mesmo).
- **Python:** classe canônica **`BudgetExhausted`** + ponto de captura por repo no adapter; os repos que engolem exceção (c149 reconstruído, wait-loops removidos) capturam explicitamente.

**Efeitos v5.0.** §5.4/§17 (regra do meio-de-lote), cartão F0 (wrapper dos 2 stacks) + cartões R (captura por repo), Anexo D (D61), Anexo R. Fecha o achado do hard-stop Python subespecificado (#32).

---

## D62 — Derivação canônica das sementes internas via `SeedSequence` [decidido 2026-07-14]

**O problema.** As receitas do Anexo L usam `h(run,it)`, `h1`, `h2`, `hs`, `g(s,net_n)` — **nunca definidas**. Sem fórmula canônica, duas implementações geram streams diferentes → reprodução independente falha por construção. O §5.3 só define o offset `+1000·semente` (D22) de e81/c149.

**Opções.** (1) `np.random.SeedSequence((base, alg_id, iteração, uso_id))` (Python); (2) fórmula linear `h=1000·s+17·iter+uso` (pode correlacionar streams); (3) deixar ao implementador (irreprodutível).

**✅ DECISÃO: Opção 1 — `SeedSequence` como derivação canônica.**
- Toda semente interna deriva de **`np.random.SeedSequence((base_entropy, alg_id, iteracao, uso_id))`** → `.generate_state()` / `.spawn()`, onde `base_entropy` **já embute o offset D22** (`base = 1000·semente` para e81/c149; `= semente` para os demais). `uso_id` distingue usos concorrentes na mesma iteração (DoE × aquisição × Thompson etc.).
- Substitui todos os `h()/g()/hs` das receitas L por essa forma única.
- MATLAB: onde houver semente interna, usar `RandStream` com substream por iteração derivado do mesmo esquema (documentado); a maioria dos MATLAB semeia só `rng(seed)` (D59) e não precisa.

**Racional.** `SeedSequence` é o padrão-ouro para gerar sub-streams independentes sem correlação; unifica com o D22; mata a ambiguidade em todas as receitas de uma vez.

**Efeitos v5.0.** §5.3 (a fórmula canônica), Anexo L (as receitas trocam `h()/g()` pela forma única — vai no lote β), cartões R2/R3, Anexo D (D62), Anexo R. Fecha o achado #11.

---

## D63 — DoE como artefato persistido (fonte única dos pontos iniciais) + teste de igualdade bit-a-bit [decidido 2026-07-14]

**O problema.** O DoE `11D−1` LHS é gerado uma vez por (problema, semente) e injetado em TODOS os stacks — "o coração da comparação pareada". Mas o Python gera (`np.random.Generator`) e o MATLAB roda no Mac; LHS do numpy ≠ LHS do MATLAB bit-a-bit; o caminho concreto (gerar→persistir→ler→verificar) não era entregável.

**Opções.** (1) Python gera TODO o DoE antecipadamente → 1 arquivo por (problema, semente) → os dois stacks CARREGAM desse arquivo → hash + teste bit-a-bit no F0; (2) cada stack gera do mesmo seed (não casa); (3) Python gera, MATLAB regenera e checa "próximo" (destrói o pareamento).

**✅ DECISÃO: Opção 1 — o DoE vira artefato = fonte única dos pontos iniciais.**
- **`src/doe.py`** gera antecipadamente, para cada (problema, semente), a matriz **X (`11D−1 × D`) em bounds nativos**, via `np.random.Generator(PCG64(SeedSequence(semente)))` (LHS), e persiste **1 arquivo por (problema, semente)** — formato `.npy` **float64, little-endian, row-major** — em `data/doe/{problema}/doe_{problema}_{semente}.npy`, com **sha256 registrado no manifesto**.
- **Ambos os stacks CARREGAM desse arquivo** (o MATLAB lê o `.npy`; nunca regenera). O adapter injeta X no algoritmo (patch local por repo — A1).
- **Teste de aceitação no F0:** o X que o MATLAB carrega == o X que o Python gravou, **bit-a-bit** (sha256 igual nos dois lados) para uma amostra de (problema, semente).

**Racional.** Um artefato = uma verdade; elimina a divergência de implementação de LHS; o teste bit-a-bit blinda o pareamento (a base de todo o poder estatístico).

**Efeitos v5.0.** §5.2 (o DoE como artefato + caminho + serialização), §22.1/cartão F0 (`src/doe.py` + teste de igualdade), §19 (hash no manifesto), Anexo D (D63), Anexo R. Fecha os achados #5/#B5 (hash sem serialização; handoff do DoE).

---

## D64 — Sem backup automático do lado MATLAB (backup manual a critério do autor) [decidido 2026-07-14]

**O problema.** O Mac grava só local; o stack MATLAB é semanas de compute num único SSD sem backup — falha de disco perderia tudo. O assistente recomendou um rsync automático Mac→bucket.

**✅ DECISÃO DO AUTOR: não implementar backup automático.** O autor fará **backup manual se/quando necessário**; risco de disco **aceito e declarado**.

**Efeitos v5.0.** §17.7 mantém "MATLAB grava só local" + nota: *"sem sync automático; backup manual a critério do autor (risco de disco aceito)"*. Fecha o achado #16/B6 como risco aceito. *(Reversível a qualquer momento com uma linha de cron, caso o autor mude de ideia.)*

---

## D65 — N dos pisos: varredura pré-registrada, um N por faixa de D [decidido 2026-07-14]

**O problema.** N dos 4 pisos online tinha três valores (100 §6.3 / ~20 §6.4 / ~20–25 §3.2); 100 é infactível em D=2 (maxFE=61). Os pisos gastam TODO o orçamento em avaliações reais → N é crítico, e "calibrar para dar a melhor chance" é um grau de liberdade sobre a régua do estudo.

**Opções.** (1) Varredura pré-registrada; (2) N fixo global zero-DOF; (3) N=f(orçamento) por fórmula.

**✅ DECISÃO DO AUTOR: Opção 1 — varredura pré-registrada.**
- **Grade:** N ∈ {10, 20, 30, 50}, testada nos **5 problemas do sweep** (MMF1, ZDT4, DTLZ2, WFG9, ZDT1) + **2 reps de alta-D** (ex.: ZDT1-D30, WFG9-D22), **5 sementes**.
- **Critério:** melhor **mediana da métrica primária (D2 — IGD+ final)** por faixa de D.
- **Escolha:** **um N por faixa de D** — baixa (D≤5) / média / alta (D≥20) — cravado ANTES da bateria (pré-registro elimina o DOF pós-hoc).
- **Aplica-se aos 4 pisos ONLINE** (NSGA-II/III, MOEA/D, SMS-EMOA). O **piso offline** (MOEA/D-média) otimiza sobre o surrogate sem gastar avaliações reais na busca → mantém N=100 interno (sem pressão de orçamento), documentado.

**Efeitos v5.0.** **Supersede** o "100" (§6.3) e o "~20 vago" (§6.4/§3.2) para os pisos online (carimbar); nova subseção de protocolo da varredura (§3.2 ou §6.3); cartão do piloto; Anexo D (D65), Anexo R. *(Dependência: o critério usa a métrica primária do D2, decidido na próxima rodada.)*

---

## D66 — V-B.4 large-batch fechada: q=10, orçamento 11D−1+K·q com K=200, roster 4+Sobol, qParEGO fora [decidido 2026-07-14]

**O problema.** V-B.4 seguia "[PENDÊNCIA]" (~2.000–3.000 aval.) — não gerava manifesto. Faltava q, K, fórmula do orçamento, roster, spec do piso Sobol.

**✅ DECISÃO DO AUTOR (recomendação do assistente):**
- **q = 10** (uniforme, D36).
- **Orçamento: `maxFE_batch = 11D−1 + K·q` com K = 200** → **DoE `11D−1` compartilhado/pareado com o principal + 2.000 infills de lote**. K·q é exato (sem sobra de módulo). O n atinge ~2.000+DoE (a "parede" O(n³) — o achado ⭐ de escalabilidade §V-B.3).
- **Roster: os 4 batch-nativos** (c149, c262, e81, c154) **+ piso Sobol-batch** (scrambled/Owen por semente, q=10, DoE compartilhado — D37). **qParEGO FORA** (D36 confirmado; limpar os estados "opcional/se-aprovado" em §18/§21.2/E.10 no lote β).
- ~5 problemas × 30 sementes (o subset do sweep); **run_id com `exp=batch`** (D55).

**Racional.** DoE pareado com o principal permite a "lente a FEs iguais" do c149 (D39); K fixo dá reprodutibilidade; qParEGO fora evita braço vetado. Ajustável se o piloto mostrar custo proibitivo (o assistente medirá).

**Efeitos v5.0.** §V-B.4 (fecha a pendência; some o "[PENDÊNCIA]"), §0/§1.5 (grid do Experimento 2 gerável), l.181/l.917 (a regra q=1 do c149 já é D41 — lote β), Anexo D (D66), Anexo R. Fecha o achado #B7/C2.

---

## D67 — MVNS totalmente especificada [decidido 2026-07-14]

**O problema.** A MVNS (D51, eixo de distribuição do sweep offline) só dizia "normal multivariada enviesada, var=0,1". Faltava μ, Σ, espaço e tratamento de fora-dos-bounds.

**✅ DECISÃO DO AUTOR (recomendação do assistente):**
- Amostrar no **espaço normalizado [0,1]^D**; **μ = 0,3·𝟙** (vetor off-center **fixo** — o enviesamento: dataset concentrado longe do centro, o cenário "dataset ruim que você não escolheu"); **Σ = diag(0,1)** (var=0,1 por dimensão); amostras fora de [0,1] → **clip** aos bounds; depois **mapear para os bounds nativos** do problema.
- μ **fixo** (não por semente — o viés é consistente; a semente varia só as amostras).

**Racional.** Casa com a intenção "dataset enviesado" (precedente b5/c311 MVNORM, var=0,1); clip é simples e realista (empilha massa na borda, como amostragem ruim real).

**Efeitos v5.0.** §11.5/§9 (spec completa da MVNS), cartão do sweep, Anexo D (D67), Anexo R. Fecha o achado #C3/#14. *(O valor 0,3 de μ fica pinado na implementação; se o autor quiser casar exatamente os `.mat` MVNORM do b5/c311, extraio os parâmetros de lá.)*

---

## D68 — Avaliação final offline: SEM cap do |ND| (gerar o dado completo; truncar/normalizar a posteriori) [decidido 2026-07-14]

**O problema.** O ND final offline é avaliado 1× na função real para as métricas verdadeiras; sem cap, o HV cresce com |ND| (confundidor de tamanho) e as avaliações finais crescem. O assistente recomendou truncar a N=100 por crowding.

**✅ DECISÃO DO AUTOR: NÃO limitar o dado — gerar o ND completo, avaliar tudo na função real, salvar completo.** O tratamento (truncar/normalizar para comparabilidade do HV) é **pós-hoc, a critério do autor**, sobre os dados salvos.

**Racional (coerente com D53/D54).** Dado descartado é irrecuperável; o autor prefere gerar o conjunto completo e tratar depois. O |ND| final é ≤ tamanho de população (não são milhares) → custo de gerar tudo é baixo.

**Efeitos v5.0.** §11 (o ND final é salvo COMPLETO, sem truncagem na geração), §12 (nota: **a comparabilidade do HV entre configs com |ND| diferentes é resolvida na análise pós-hoc — truncagem/normalização a critério do autor**; o confundidor de tamanho é tratado ali, não na geração), Anexo D (D68), Anexo R. *(Registrado como passo pós-execução conhecido, não como limitação não-endereçada.)*

---

## D69 — Reference-point do HV: enunciado único no espaço normalizado [decidido 2026-07-14]

**O problema.** Duas fórmulas coexistiam: §12/§12.2 "nadir×1,1" × S.5 "nadir+0,1·(nadir−ideal)" — só coincidem se ideal=0; e "nadir×1,1" quebra silenciosamente se algum nadir≤0 (fronts empíricos BBOB têm negativos → ref cai dentro do front → HV errado).

**✅ DECISÃO (recomendação): Opção 1 — enunciado único.** *"As métricas são computadas sobre objetivos NORMALIZADOS f′=(f−ideal)/(nadir−ideal); o ref-point do HV = (1,1, …, 1,1)^M no espaço normalizado."* Equivale à fórmula da S.5 no espaço cru (Ishibuchi 2018); robusto a nadir≤0; comparável entre problemas. **Efeitos:** substitui "nadir×1,1" em §12/§12.2/§6.2/S.5; define que o HV é computado no espaço normalizado; Anexo D (D69), Anexo R. Fecha achados #B2/#13.

---

## D70 — Endpoint primário IGD+ + tabela operacional dos 4 testes [decidido 2026-07-14]

**O problema.** 5 métricas × 4 famílias × 25 problemas sem operacionalização: qual métrica no Friedman "oficial", agregação das 30 sementes, α, papéis Nemenyi×Holm, escala da rope, online/offline juntos×separados, HV degenerado (zeros em DTLZ1/3 violam Friedman).

**✅ DECISÃO (recomendação): Opção 1 — pacote pré-registrado.**
- **Endpoint primário = IGD+ final** (mediana das 30 sementes por célula); HV secundária. *(IGD+ = Pareto-compatível, não colapsa a 0 sob orçamento apertado, definida p/ todos incl. BBOB.)* **Autor confirmou IGD+ como primária.**
- **α = 0,05.**
- **Friedman POR MÉTRICA** (um p/ IGD+, um p/ HV) — os problemas onde o HV degenera são **declaradamente excluídos** do Friedman-HV (nunca um bloco único misturando células degeneradas).
- **Nemenyi** = post-hoc all-pairs do Friedman (diagrama CD de Demšar). **Holm** = correção das comparações **rank-sum pareadas** fora do Friedman (vs-controle).
- **Bayesiano (Benavoli):** rope = **0,05 sobre a métrica NORMALIZADA (D69)**.
- **Online (17 configs) e offline (5 configs) em quadros SEPARADOS** (regimes/rosters disjuntos — não se rankeia q=1 online contra offline na mesma tabela).

**Efeitos:** §14 (tabela operacional completa), §12 (agregação por mediana), §15.1 (Friedman por métrica com blocos declarados), Anexo D (D70), Anexo R. Fecha achados #B8/#12/#41.

---

## D71 — §15 (análise por característica, ⭐) operacionalizada [decidido 2026-07-14]

**O problema.** Sem matriz booleana 25×8 multi-rótulo, sem teste definido, sem unidade amostral (problema×semente = pseudo-replicação), sem multiplicidade; cobertura fraca em algumas características (enganosidade=1 suíte; flat=1 problema).

**✅ DECISÃO (recomendação): Opção 1.**
- **Matriz 25×8 multi-rótulo pré-registrada** como artefato `characteristics.csv` (cada problema recebe TODAS as propriedades que estressa, derivadas da P.2/P.4 — ZDT3 = desconexo E multimodal).
- **Unidade amostral = PROBLEMA** (mediana sobre as 30 sementes); sementes são réplicas — usá-las como independentes seria pseudo-replicação (significância inflada).
- **Análise DESCRITIVA primária** (ranks, tamanhos de efeito, vitórias/derrotas) por característica; **Friedman-por-característica só onde ≥5 problemas** (declarado); nunca superafirmar poder com 2–3 problemas.
- **Coberturas fracas declaradas como limitação** (analisadas descritivamente, não testadas).

**Efeitos:** §15 (procedimento), artefato `characteristics.csv` (F5), P.3 (declarar as coberturas fracas honestamente), Anexo D (D71), Anexo R. Fecha achados #B9/#10/#D3.

---

## D72 — Reference set 2-obj por segmento + cache BBOB fixado + notas [decidido 2026-07-14]

**O problema.** Re-espaçamento por comprimento de arco (§12.2) em fronts DESCONEXOS (ZDT3, WFG2) interpola através dos gaps → pontos inatingíveis → IGD viesado. Cache BBOB sem protocolo na §12.1 ("empírico nos 7" contradiz o F1 analítico).

**✅ DECISÃO (recomendação): Opção 1.**
- **Re-espaçar POR SEGMENTO**: detectar segmentos desconexos e re-espaçar dentro de cada um, **nunca através dos gaps** (2-obj).
- **Cache BBOB fixado na §12.1:** NSGA-II pop 200 × 300 gerações × 5 sementes (seed 0), subamostra uniforme por f₁ (já no L.19 — trazer à §12.1); corrigir **"empírico nos 7" → "nos 6; F1 analítico"**.
- **Nota da dupla assimetria:** no BBOB, IGD **e** HV herdam a incerteza do front empírico (o "apoiar no HV" é mais fraco do que o texto sugeria).

**Efeitos:** §12.1/§12.2, Anexo D (D72), Anexo R. Fecha achados #D4/#39/#86.

---

## D73 — Três enquadramentos de honestidade [decidido 2026-07-14]

**O problema.** Três pontos a declarar explicitamente para blindar a banca.

**✅ DECISÃO (recomendação): Opção 1 — registrar os três.**
- **(a) online×offline confundido com identidade do algoritmo:** nenhum algoritmo roda nos dois regimes → a comparação é "estes online × aqueles offline", com o efeito-regime confundido com o efeito-algoritmo. Declarar como limitação (à la D50); o piso offline (MOEA/D-média ≈ b5-sem-σ) isola parcialmente.
- **(b) vantagens informacionais declaradas:** c122 recebe f_min/f_max dos fronts VERDADEIROS (info-oráculo que nenhum outro online tem — é requisito de fidelidade do paper, mas declara-se); σ do c311 é patch nosso ("author-modified", M.17); relaxação M−1 do e103 custa acurácia em **19/25 = 76%** dos problemas (M=2). A **ablação estrita do e103** (sem a relaxação M−1) fica **OPCIONAL, não-default** — o autor aciona se quiser; a limitação fica declarada de qualquer forma.
- **(c) IGD+ recreditado:** é **Ishibuchi et al. 2015** (métrica consolidada, fracamente Pareto-compatível) — apresentar como "adotamos uma métrica Pareto-compatível que os papers-fonte omitiram", NÃO como "extensão nossa" (§6.2).

**Efeitos:** §2.4/§15 (limitação online×offline), §6.2 (crédito do IGD+; vantagens informacionais), M.6/M.17 (e103/c311), Anexo D (D73), Anexo R. Fecha achados #D5/parte do #3.4.

---

## D74 — CalHV INTERNO do e74 normalizado (DEF-L5, órfã, agora fechada) [decidido 2026-07-14]

**O problema.** O e74 (CLMEA) usa `CalHV` (hipervolume, herdado do HypE) **internamente** como sinal da seleção ambiental durante a busca. O paper assume objetivos **normalizados**. No set há **6 problemas BBOB** (bi-objetivo) cujos objetivos têm escala grande e podem ser **negativos** → com objetivos crus: (a) o ref-point pode cair **dentro** do front → HV interno = 0 → o sinal de seleção morre (e74 seleciona "no escuro"); (b) uma escala domina a outra e o HV vira lixo numérico. É a DEF-L5, marcada `[PP]` mas **órfã** — o K.5.2 dizia "decidir no ping-pong" e nenhum cartão §22/S a herdou (achado dos 2 pareceres: revisao l.68, parecer l.96).

**⚠ Distinção do D69.** O D69 trata da **métrica final** (a análise). O D74 trata do **CalHV interno do e74** (a maquinaria do algoritmo durante o run). Mesma filosofia (normalizar), lugar diferente — os dois coexistem sem conflito.

**Opções.** (1) Normalizar antes do CalHV interno (min-max sobre o arquivo corrente do e74 a cada chamada, ref 1,1 no espaço normalizado — receita do D69 aplicada por dentro); (2) excluir os 6 BBOB do e74; (3) deixar como está.

**✅ DECISÃO DO AUTOR: Opção 1 (recomendada).** A cada chamada do CalHV interno, os objetivos são **min-max-normalizados sobre o arquivo corrente do e74** e o **ref-point = 1,1·𝟙 no espaço normalizado** — idêntico ao enunciado do D69, porém aplicado à seleção interna do algoritmo (não à métrica).

**Racional.** Consistente com o D69; **fiel ao paper**, que pressupõe objetivos normalizados para seleção baseada em HV; patch mínimo; funciona uniformemente em BBOB e não-BBOB. O comportamento numérico difere do código cru **porque o código cru está errado em BBOB** — é correção (🔵/🟠 na bússola D29: o paper assume normalizado, o código omitiu), não desvio nosso.

**Efeitos na injeção v5.0.** Fecha a DEF-L5 (K.5.2 deixa de dizer "decidir no ping-pong" → aponta o D74); **cria o cartão herdeiro** (R-e74) que o red-team apontou como ausente; §12/M.6 (nota de que o e74 normaliza internamente, coerente com o D69); Anexo D (D74), Anexo R. Fecha o achado #28 (parte CalHV) e a órfã da revisao l.68/parecer l.96.

---

## D75 — JES (c154): §6.4 é a dona; `random_search` principal + `nsgaii` como checagem de fidelidade; pop-250 morta (DEF-B9.5) [decidido 2026-07-14]

**O problema.** O JES (c154) precisa **otimizar a função de aquisição** internamente (sub-problema multi-objetivo). A SPEC dá **três instruções conflitantes**: §22.3 (l.1426) manda "decidir no piloto entre (a) `random_search` default e (b) paper-faithful `nsgaii(pop=100,gen=500)`"; §6.4 lista uma **terceira** variante (pop 250) que não é nem (a) nem (b); Anexo K (l.1848) diz "paper-faithful se trivial"; D30 (l.2392) **não** lista a B9.5 como resolvida. É a **única receita entre os 16 genuinamente sem fechamento** — no algoritmo mais frágil do set (c154 = loop do c262 + estágio JES + fallback obrigatório do `RuntimeError`). Convergência dos revisores (revisao l.47–50, l.143 #6): eleger um dono, pré-registrar rota (a) principal + rota (b) como checagem, sincronizar as três seções.

**Opções.** (1) §6.4 dona; (a) `random_search_optimizer` principal + (b) paper-faithful `nsgaii(pop=100,gen=500)` como checagem de fidelidade no piloto em 1–2 problemas; matar a pop-250; (2) paper-faithful nsgaii em tudo (×3–10 de custo); (3) deixar "decidir no piloto".

**✅ DECISÃO DO AUTOR: Opção 1 (recomendada).**
- **§6.4 = seção dona** da receita do otimizador interno do JES (as demais seções apontam para ela).
- **Rota (a) PRINCIPAL:** `random_search_optimizer` (default de todos os runs de produção do c154).
- **Rota (b) CHECAGEM DE FIDELIDADE:** paper-faithful `nsgaii(pop=100, gen=500)` rodado **no piloto, em 1–2 problemas**, só para **quantificar o gap** (a) vs (b) — não é braço de produção.
- **Terceira variante (pop 250) MORTA** (some de §6.4).

**Racional.** Fecha a única receita aberta; mantém o c154 tratável (random_search é barato — coerente com o loop reaproveitado do c262, S.8); a checagem de 1–2 problemas limita o risco de "random_search é crude demais e injustiça o algoritmo" **medindo** o gap em vez de supô-lo; é a sugestão convergente dos revisores. A rota (b)-em-tudo fica disponível como escalonamento (a própria B9.5) se a checagem revelar gap grande.

**Efeitos na injeção v5.0.** §6.4 (vira dona; pré-registro (a)/(b); some a pop-250), §22.3 (aponta p/ §6.4; o "decidir no piloto" vira "medir o gap (a)vs(b) no piloto"), Anexo K l.1848 (alinhado), **D30 ganha a B9.5 como resolvida** (fecha o "não lista B9.5"), cartão do piloto (a checagem (b) em 1–2 problemas é item do piloto de fidelidade), Anexo D (D75), Anexo R. Fecha o achado #6 (BLOQ) e a órfã B9.5.

---

## D76 — Máscara do e74 OBRIGATÓRIA (🔴 por D29) + L4/L8 formalmente no Anexo D [decidido 2026-07-14]

**O problema (duas partes).** **(a)** No e74, a seleção de quais offspring são avaliados usa a máscara `Choose`; o código aplica `x_offspring(index(Choose),:)` de forma que **contradiz o paper**. O K.5.2 (l.1887) marca o fix como `[IMPL]` **obrigatório**; o cartão §22 (l.1408) diz **"fix opcional"** — contradição vinculante. Sob a bússola **D29** (fonte-por-causa), é 🔴 **BUG que o paper contradiz** → obrigatório. **(b)** Duas correções têm recomendação (►) mas **nunca entraram no Anexo D**: **L4** (c141: NaN do SDE → `+eps`) e **L8** (b1: `mse<0` → `sqrt(max(mse,0))`). O D52 afirma "todas as `[PP]` resolvidas", mas L4/L8 foram fechadas só em §22/§6.5 — o registro vinculante (Anexo D) está dessincronizado da realidade (achado revisao l.68/l.107, parecer l.107).

**Opções.** (1) máscara obrigatória (🔴, alinha §22↔K.5.2) + registrar L4/L8 no D; (2) deixar a máscara "opcional"; (3) registrar L4/L8 mas deixar a máscara opcional (meia-medida).

**✅ DECISÃO DO AUTOR: Opção 1 (recomendada).**
- **Máscara do e74 = fix OBRIGATÓRIO** (🔴 por D29): o cartão §22 é alinhado ao K.5.2 (some o "opcional"); a aceitação R1 do e74 **exige** a máscara aplicada.
- **L4 (c141: `+eps` no SDE) e L8 (b1: `sqrt(max(mse,0))`) registrados formalmente** no Anexo D como decisões fechadas (🟠 IMPL — guarda numérica), encerrando a divergência "D52 diz resolvido mas não há linha em D".

**Racional.** O R1 smoke-test (MMF1+ZDT1) **não** pegaria uma reconstrução com a máscara semanticamente errada → "opcional" é perigoso justamente no e74, cuja fidelidade já é sensível (SelectTrainData, DEF-L5); tornar 🔴 alinha com a bússola D29 que o próprio projeto adotou; registrar L4/L8 põe o Anexo D (vinculante) em dia com o que já vale na prática.

**Efeitos na injeção v5.0.** Cartão §22 do e74 (máscara: opcional→obrigatório, 🔴), K.5.2 (mantém, agora sem conflito), §6.5 (L4/L8 apontam p/ as novas linhas do D), **Anexo D ganha 3 registros** (a máscara-e74 como sub-item do D76 + L4 + L8), Anexo R. Fecha o achado #28 (parte máscara) + o descompasso D52×L4/L8.

---

## D77 — Piso offline MOEA/D-média = DESDEO mode 12 (Python/R3, GP-média = b5-sem-σ); listagem PlatEMO morta [decidido 2026-07-14]

**O problema.** O piso offline MOEA/D-média aparece em **dois lugares incompatíveis**: §22.2 (l.1411) o põe na **Rodada 1 como built-in do PlatEMO** no Mac (surrogate **dacefit**); a E.9 (l.1631) manda "**mesmo motor do b5** = mode 12 do repo **DESDEO** sobre **GP-média** — máxima comparabilidade com b5, **DEF-E3**" = **Python/Rodada 3** (surrogate **SurrogateKriging**). São stacks **e** surrogates diferentes; implementar em PlatEMO **quebra a comparabilidade que a DEF-E3 exige**. Nenhum cartão do S.4 o testa (achado revisao l.69 #8, parecer l.37 B6).

**Por que a comparabilidade é o ponto.** O piso offline existe para **isolar o valor de usar a incerteza (σ)**. Se o piso = GP-média = **b5 sem σ** (mesmo motor, mesmo surrogate, sem a parte probabilística), "piso vs b5" mede **exatamente** o efeito de usar σ. Se o piso = PlatEMO/dacefit, a diferença piso-vs-b5 **confunde** "sem σ" com "surrogate+stack diferentes" → o contraste perde o sentido e o "isolamento parcial do regime" citado no D73(a) deixa de valer.

**Opções.** (1) DESDEO mode 12, Python/R3, GP-média (= b5-sem-σ), por DEF-E3, e **matar** a listagem PlatEMO/R1; (2) manter built-in PlatEMO (MATLAB/dacefit); (3) rodar os dois.

**✅ DECISÃO DO AUTOR: Opção 1 (recomendada).** O piso offline MOEA/D-média roda no **mesmo motor do b5** (mode 12 do DESDEO), em **Python, Rodada 3**, sobre **GP-média** (Kriging só-média, sem σ) — a ablação limpa do b5. A listagem "built-in PlatEMO / Rodada 1" **sai** de §22.2.

**Racional.** Satisfaz a DEF-E3 (o piso difere de b5 **só** pela ausência de σ → contraste interpretável); um cartão único e claro (R3). Move um algoritmo do Mac para a VM, mas o offline é barato (<1 dia) e a VM comporta.

**Efeitos na injeção v5.0.** **Supersede** a listagem de §22.2 (piso offline sai da Rodada 1/PlatEMO), E.9/DEF-E3 confirmada como a casa canônica, **novo cartão R3** (piso offline = mode 12 GP-média), §14 (o piso da tabela offline é a coluna GP-média DESDEO), S.8/timing (o piso migra p/ a coluna VM), Anexo D (D77), Anexo R. Fecha o achado #8/B6.

---

## D78 — Fallbacks pré-registrados dos dois pontos-únicos-de-falha (c149, c311) [decidido 2026-07-14]

**O problema.** Dois algoritmos concentram peso **narrativo** e risco de implementação desproporcionais (scores S.8): **c149** (LBN-MOBO, **A=5/B=7** — o mais caro) é o **único surrogate não-GP entre os online** → sustenta a narrativa "o não-GP atravessa a parede O(n³)"; seu loop **tem de ser reconstruído** (notebook ausente → Colab; driver é pipeline de cluster com TypeErrors). **c311** (TGPR-MO, **A=6,5/B=5**) é treed-GP offline, também narrativo, com **venv frágil** (py3.9+GPy). Os revisores sinalizaram os dois (parecer l.89, revisao l.96). Se **qualquer um** falhar na reconstrução/ambiente, um pedaço da narrativa cai **sem plano B**.

**Natureza da decisão.** Diferente das demais — é **gestão de risco/contingência**, não definição de spec. Pré-compromete o "plano B" AGORA, com calma, em vez de improvisar no meio do experimento.

**Opções.** (1) pré-registrar fallbacks (degradação graciosa); (2) sem fallback (apostar nas duas reconstruções); (3) tirar os dois do estudo agora.

**✅ DECISÃO DO AUTOR: Opção 1 (recomendada).**
- **c311 — fallback:** se o venv py3.9+GPy/TGPR não fechar, substituir por um **treed-GP / sparse-GP genérico** (ex.: pilha GP padrão particionada por árvore), **declarado como "author-modified surrogate substitute"** (M.17) — preserva a **classe** de surrogate (treed/particionado) mesmo sem o código exato.
- **c149 — fallback:** **reconstrução best-effort** do loop (núcleo ~250 linhas reaproveitável — MLP parametrizado + ensemble μ/σ² + NSGA-II pymoo; D41 já define a seleção). **Se falhar**, a narrativa "não-GP atravessa a parede" passa a **repousar no c311 offline** + uma **nota de trabalho-futuro** (BNN online) — limitação declarada, não buraco silencioso.
- **Gatilho e rótulo:** o fallback só é acionado se o cartão R3.x do respectivo algoritmo **não passar no smoke-test**; quando acionado, o manifesto e o texto (M.17) **marcam explicitamente** "fallback ativado" (auditabilidade).

**Racional.** A narrativa **degrada com graça** em vez de colapsar; a decisão é tomada fora da pressão da execução; os fallbacks preservam a *classe* de contribuição (não-GP / treed-GP) mesmo quando o código exato não fecha; tudo declarado (coerente com a filosofia de honestidade do D73).

**Efeitos na injeção v5.0.** M.17 (fallback do c311 + rótulo), cartões R3 de c149 e c311 (critério de acionamento = falha no smoke; ramo de fallback documentado), §2.4/§15 (a limitação "narrativa não-GP repousa em c311 se c149 falhar" entra como risco declarado), §19 (flag "fallback_ativado" no manifesto), Anexo D (D78), Anexo R. Fecha os achados de fragilidade c149/c311 (parecer l.89, revisao l.96).

---

## D79 — LOTE infra de execução: despacho multi-env por subprocess + fixação de 1 thread em todas as pilhas + piloto na VM Linux [decidido 2026-07-14]

**O problema (lote — achados #18/#19 + licença + SO do piloto).** (a) **Despacho multi-env não especificado** (#19): `experiments.py` usa joblib/loky, mas b5 (py3.8/9), c311 (py3.8), e81 (BoTorch) e c122 exigem venvs **incompatíveis entre si**; como uma task invoca a `main` de outro venv nunca foi escrito. (b) **Threads BLAS/OMP fora do contrato** (#18): `torch.set_num_threads(1)` (N.1) não alcança numpy/sklearn/GPy (b5/c311) nem kmeans/pdist2 do MATLAB → oversubscription → **o wall-clock (§17.6, dado de 1ª classe da tese) fica não-comparável**. (c) Licença MATLAB/Parallel e o SO do piloto de timing.

**✅ DECISÃO DO AUTOR (recomendação): contrato de execução explícito.**
- **Isolamento de env = Opção 1 (subprocess-por-venv):** tabela **`alg→env`** + despacho por **subprocess chamando o Python do venv-alvo** (`subprocess.run([venv_python, main.py, ...])`), com stdout/stderr capturados no `.jsonl`. Sem import in-process; cada run é um processo limpo (casa com o "embaraçosamente paralelo" e a escrita atômica do D58).
- **1 thread por processo em TODAS as pilhas:** `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=NUMEXPR_NUM_THREADS=1` no ambiente de cada subprocess + `maxNumCompThreads(1)` no MATLAB → 1 run = 1 core (D26), wall-clock comparável.
- **Piloto de timing roda na VM Linux de produção** (o Mac serve só ao stack MATLAB).

**Racional.** Subprocess-por-venv é zero-infra-nova, compatível com joblib e imune ao inferno de dependências entre venvs; a fixação uniforme de threads é o que torna o §17.6 comparável entre algoritmos (senão o "dado de tempo" da tese é ruído de oversubscription); o overhead de startup por run é amortizado (runs de minutos/horas).

**Efeitos na injeção v5.0.** §16.5.2/§17.7 (contrato de despacho: tabela `alg→env` + subprocess + captura), N.1 (estende o pin de threads a OMP/MKL/OPENBLAS/NUMEXPR por processo; alcança b5/c311/MATLAB), §18/S.6 (tabela `alg→env`), cartão F0 (implementar o despachante), §22.5 (piloto na VM Linux), Anexo D (D79), Anexo R. Fecha achados #18/#19.

---

## D80 — LOTE reprodutibilidade: pinagem total (SHA dos 9 repos + anchors.json + lockfile por env + lib de métrica) como gate [decidido 2026-07-14]

**O problema (lote — #21/#23/anchors/#15).** (a) **9 repos de autor sem SHA** (#21): PlatEMO e BoTorch pinados; c122/c141/e74/c238/e81/c149/e103/b5/c311 só com URL → `git pull` acidental muda o experimento. (b) **`anchors.json` por patch**: falta um artefato que amarre cada patch a (repo, arquivo, linha, **conteúdo esperado**, hash) e faça o script **abortar** em divergência (a classe "patch na linha errada" que a S.2 já pegou 1×). (c) **Lockfile por env** (#23): pins frouxos + conflito sklearn do b5 (0.23.2 × **0.21.3**, sendo 0.21.3 a evidência do repo) + `desdeo-emo` sem pin. (d) **Lib de métrica não pinada** (#15): IGD/IGD+/HV/GD/spacing sem lib/versão; `spacing`/`GD` com definições múltiplas.

**✅ DECISÃO DO AUTOR (recomendação): pinagem total como gate (sem trade-off — higiene que a banca cobra).**
- **SHA dos 9 repos** no manifesto **e** num `repos.lock`.
- **`anchors.json`**: fonte que o script de patch consome e **aborta** em divergência de conteúdo/hash.
- **Lockfile por env** (pip freeze / conda-lock) como artefato de aceitação do gate R3.2; **sklearn do b5 cravado em 0.21.3**; `desdeo-emo` com pin explícito.
- **Lib de métrica pinada** (recomendação: `moocore`/`pymoo` nomeado + versão) e **definição de `spacing`/`GD` fixada** no manifesto; smoke `HV(F1)=0,8333` mantido.

**Efeitos na injeção v5.0.** §3.5 (coluna SHA dos 9 repos), §19/§20 (manifesto: SHA + hashes + lib de métrica + definições), §18/S.6 (lockfile por env como gate; sklearn b5→0.21.3; desdeo-emo pinado), §12 (nomear lib+versão da métrica + definição de spacing/GD), novos artefatos `repos.lock` e `anchors.json` (F5/D83), cartão de patch (aborta em divergência), Anexo D (D80), Anexo R. Fecha achados #21/#23/#15. *(Na injeção v5.0 eu já deixo os esqueletos de `anchors.json` e `repos.lock`.)*

---

## D81 — LOTE qualidade: gate de fidelidade ±3σ + protocolo "pára-e-loga" + F0 expandido + fonte-única/bounds/sinal [decidido 2026-07-14]

**O problema (lote — gate ±σ / #13 / fonte-única / N.5).** (a) **Gate do c217 com tolerância tripla:** §22.2 diz **±7,78e-3 = ±1σ**; S.4 diz **±3σ**. Gate de ±1σ em 1 semente **reprova ~1/3 das implementações CORRETAS por acaso**. (b) **F0 é subconjunto do §22.1** (#13): omite hard-stop, validação das 25 classes, smoke da métrica, schemas C1/C3/C4. (c) **Fonte-única/bounds/sinal** (trecho pedido pelo autor): `problems.py` como única fonte via `PYTHONPATH`/monkeypatch; checar bounds e **sinal** (minimização) em todo adapter. (d) **Protocolo de falha:** o que o agente faz num gate vermelho.

**✅ DECISÃO DO AUTOR (recomendações):**
- **Tolerância do gate = ±3σ sobre 1 semente** (Opção 1): unifica no valor permissivo (~99,7% das corretas passam); o gate pega implementação **errada**, o ranqueamento fino é a bateria de 30 sementes. *(Some o ±1σ de §22.2.)*
- **Protocolo de falha = "pára-e-loga" (Opção 1):** gate vermelho ⇒ o agente **interrompe o cartão, grava o diagnóstico no `.jsonl`/manifesto e devolve o controle** — **nunca** auto-conserta fidelidade (decisão de fidelidade é do autor).
- **F0 expandido:** inclui hard-stop, as 25 classes, smoke da métrica (`HV(F1)=0,8333`), schemas C1/C3/C4 + nota "itens do §22.1 não repetidos aqui continuam obrigatórios".
- **Fonte-única cravada:** `problems.py` via `PYTHONPATH`, checagem de bounds+sinal no adapter; **passo N.5 do JES reescrito** para **receber o X injetado** (`Problem.Evaluation(X)`) em vez de gerar LHS local não-pareado.

**Efeitos na injeção v5.0.** §22.2/S.4 (gate unificado ±3σ — supersede o ±1σ), CLAUDE.md/§0 (protocolo pára-e-loga), cartão F0 (expandido; nota de herança do §22.1), §16.5/N.5 (fonte-única + bounds/sinal; N.5 recebe X injetado), Anexo D (D81), Anexo R. Fecha achados #13 + gate ±σ + N.5.

---

## D82 — LOTE cartões faltantes: grade completa, sub-estudos, consolidação, análise (R4) [decidido 2026-07-14]

**O problema (lote — #11 + sub-estudos sem casa).** Toda aceitação hoje para no smoke "MMF1+ZDT1 seed 0". Faltam cartões para: **(a)** disparo da grade completa (16×25×30 = 16.500 runs); **(b)** sub-estudos (batch q=10, piso Sobol-batch, sweep offline por tier, MVNS) — as 3 rodadas fecham "prontas" **sem esses braços e nada trava**; **(c)** consolidação (estágio 3 do §17.4: mescla Mac local + bucket, reencoda brotli→zstd, funde fragmentos de manifesto); **(d)** análise **R4** (Parte VI: métricas, 4 testes, rankings, §15 — hoje só uma "casca").

**✅ DECISÃO DO AUTOR (recomendação): criar os 4 cartões, cada um com aceitação objetiva; R1∥R2 em paralelo onde independentes.**
- **Cartão grade-completa:** dispara os 16.500 runs (usa run_id do D55, resume do D58).
- **Cartões dos sub-estudos:** um por braço (batch/Sobol/sweep/MVNS), herdando D66/D67/D65.
- **Cartão consolidação:** estágio 3 (lê Mac+bucket, reencoda zstd, funde manifesto).
- **Cartão R4/análise:** aceitação = **métrica no F1 analítico = 0,8333**; consolidação lê Mac+bucket; saída dos 4 testes (D70) reproduzível.

**Efeitos na injeção v5.0.** §22 (Rodadas ganham os 4 cartões; nota R1∥R2), S.4 (cartões dos sub-estudos + consolidação + R4), Anexo D (D82), Anexo R. Fecha achados #11 + sub-estudos órfãos.

---

## D83 — LOTE handoff: regra de precedência global + CLAUDE.md + 6 artefatos machine-readable + 1 sessão por cartão [decidido 2026-07-14]

**O problema (lote — a espinha do handoff).** (a) Precedência hoje só cobre "S > §22". (b) Falta um `CLAUDE.md` porta-de-entrada. (c) O agente hoje faria **parsing da SPEC inteira** em vez de consumir artefatos estruturados. (d) Falta a disciplina "1 sessão por cartão".

**✅ DECISÃO DO AUTOR (recomendação): adotar o pacote de handoff inteiro.**
- **Regra de precedência no §0:** *"Ordem em qualquer conflito: **Anexo S > §22 > Anexo D > corpo (§1–§21) > anexos E/I/K/L > históricos (F/G/R)**. Estado vinculante = Anexo D + S."*
- **`CLAUDE.md`** = porta de entrada: precedência + **protocolo de falha (D81)** + **mapa de leitura por cartão** (o agente lê só o que o cartão manda).
- **6 artefatos machine-readable** (a fonte que o agente consome; a SPEC vira referência): `decisions.json`, `runs_matrix.csv` (16.500 linhas exp/alg/problema/semente/env), `params.*` (por algoritmo), `characteristics.csv` (matriz 25×8 do D71), `envs.*` (4 envs + MATLAB), `anchors.json` (do D80).
- **1 sessão por cartão**, todas partindo do mesmo `CLAUDE.md`.

**Racional.** É o item que mais aumenta a chance de o Claude Code acertar de primeira; `runs_matrix.csv` e `characteristics.csv` saem quase de graça do que já decidimos.

**Efeitos na injeção v5.0.** §0 (linha de precedência), novo `CLAUDE.md` (artefato de repo), §22 (1 sessão por cartão + mapa de leitura), geração dos 6 artefatos, Anexo D (D83), Anexo R. Fecha a agenda de handoff do red-team.

---

## D84 — Cronograma: escada de prioridade + piloto de timing como GATE numérico bloqueante [decidido 2026-07-14]

**O problema (lote).** (a) Os revisores pediram a ordem de ataque "por prioridade". (b) A S.8 declara o piloto de timing (§22.5) como **gate, não formalidade** — os curingas (c149, rota JES/B9.5, parede O(n³) em n≈929/2500) só se pinam medindo; mas não estava escrito que o piloto **trava** a bateria.

**✅ DECISÃO DO AUTOR (recomendações):**
- **Escada de prioridade:** Fase 0 (infra D79/D80 + DoE D63 + wrapper + F0 expandido D81) → **R1 (MATLAB, gate ±3σ) ∥ R2 (Python online)** → R3 (offline + piso D77) → sub-estudos (D82) → **R4 (análise)**.
- **Piloto de timing = gate bloqueante (Opção 1):** mede 1–2 sementes dos configs-curinga **antes** de liberar as 30; se um config estoura o orçamento de tempo, dispara o escalonamento **já decidido** (JES→B9.5 do D75; scale-out do D59; vetorizar predict do c311) **antes** de gastar semanas.

**Racional.** Descobrir na semente 30/30 que o c149 leva 8 dias é catastrófico; o gate numérico transforma "estimei" (S.8) em "medi" — o que a banca espera. Custo: 1–2 dias de piloto adiantados.

**Efeitos na injeção v5.0.** §22 (escada de prioridade explícita + R1∥R2), §22.5/S.8 (piloto = gate bloqueante com os escalonamentos ligados a D75/D59/c311), Anexo D (D84), Anexo R. Fecha a agenda de cronograma.

---

## D85 — Semente 42 mantida por preferência do autor (sem racional fabricado) [decidido 2026-07-14]

**O problema.** O conjunto é **{0, 1, …, 28, 42} = 30 sementes** (D19). Um parecer (#36) apontou que o **42 não tem racional documentado** e "parece arbitrário". O assistente havia sugerido acrescentar um parágrafo de justificativa (semente cultural + distância numérica sob o offset D22).

**✅ DECISÃO DO AUTOR: manter {0–28, 42}; racional = PREFERÊNCIA DO AUTOR ("gosto desse número, e ponto"); NÃO adicionar parágrafo de justificativa.** O autor avalia que **a banca não perguntará sobre a escolha de semente**.

**Racional registrado.** O **único requisito metodológico sobre sementes** — que sejam **fixas e reportadas** (garantido: as 30 estão listadas na D19 e no `runs_matrix.csv`) — **já está satisfeito**; o valor específico de uma semente é irrelevante para validade/reprodutibilidade. Fabricar uma justificativa científica para uma escolha estética seria desonesto; registra-se a causa real (preferência) e encerra-se o achado como *won't-fix por decisão do autor*.

**Efeitos na injeção v5.0.** §5 mantém {0–28, 42} **sem** parágrafo de racional; o achado #36 é fechado no Anexo R como "mantido por preferência do autor; requisito de reprodutibilidade (sementes fixas+reportadas) satisfeito". Anexo D (D85). *(Nenhuma edição de conteúdo além do fechamento do achado — zero re-trabalho.)*

---

## D86 — Higiene de memória intra-run + eixo de RAM no piloto (adendo pós-encerramento) [decidido 2026-07-14]

**Origem.** Segunda rodada de pareceres externos (2 revisores, lendo a v4.2/v4.3 — anteriores ao ping-pong). Dos 5 pontos únicos deduplicados, 4 já estavam cobertos/decididos (D60 watchdog = timeout da ponte; D58 fragmento-por-run = melhor que filelock/SQLite; D66/D41 = V-B.4 e q=1 do c149 fechados — faltava só o carimbo no corpo, aplicado; D83 = mapa de leitura/1 sessão por cartão, faltando o passo físico dos bundles). **Este é o único ponto genuinamente novo.**

**O problema.** O risco de memória é DENTRO de um run (o D79, subprocess-por-venv, já libera tudo ENTRE runs): (a) **c149** retreina o deep-ensemble de BNNs a cada FE (D43) → tensores/grafos do PyTorch acumulam ao longo de centenas de FEs → OOM no meio do run; risco análogo (menor) em e7/c122 e nos loops torch em geral; (b) a **ponte MATLAB→pymoo** pode reter instâncias/estado do `Problem` ao longo das 31D−1 avaliações (o MATLAB é notório em não liberar o ambiente Python sob `parfor`). O watchdog D60 é REATIVO (mata o run que estourou → perde o dado); faltava a prevenção.

**Opções.** (1) Higiene explícita + eixo de RAM no piloto (recomendada); (2) confiar só no watchdog D60 (reativo, perde runs); (3) nada.

**✅ DECISÃO DO AUTOR: Opção 1.**
- **Loops torch (c149 e, por extensão, e7/c122 e demais):** `torch.no_grad()` em toda predição; `del` dos tensores intermediários + `gc.collect()` (+ `torch.cuda.empty_cache()` quando houver GPU) **a cada iteração** do loop de retreino; nenhum tensor de iterações passadas retido (o export grava e solta).
- **Ponte MATLAB→Python:** a instância do `Problem` pymoo é **resetada/reciclada ao fim de cada run** (e `clear` explícito de qualquer estado retido pela ponte); o worker não acumula objetos Python entre runs.
- **Piloto de timing (D84) ganha o eixo de RAM:** medir **pico de memória por config-curinga** (c149 em D=30 é o caso-teste canônico); teto configurável dispara alarme — **entra no gate bloqueante** do D84.

**Racional.** Prevenir > matar: o D60 protege a esteira, mas o run morto é dado perdido; a higiene custa ~zero e elimina a classe de OOM de acúmulo; o eixo de RAM no piloto transforma "esperamos que caiba" em "medimos que cabe" — coerente com a filosofia do gate numérico (D84).

**Efeitos (aplicados na SPEC v5.1).** N.1 (novo item: higiene torch por iteração), N.0 (novo item: reset do `Problem` na ponte ao fim do run), §22.5 (novo item do piloto: pico de RAM por config + alarme no gate), Anexo D §D.3 (linha D86), Anexo R (changelog v5.1), cartão F0/R (implementar a higiene nos adapters torch e na ponte). `decisions.json` atualizado.

---

*(Registro encerrado em D86. As próximas edições deste arquivo, se houver, entram abaixo.)*
