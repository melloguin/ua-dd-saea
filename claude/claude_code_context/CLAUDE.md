# CLAUDE.md — porta de entrada do implementador (SPEC v5.2)

> Este arquivo é o **primeiro** (e muitas vezes o único global) que o agente lê em cada sessão de implementação. Ele NÃO repete a SPEC — diz **o que ler, em que ordem, e como agir**. A `SPEC_experimentos_v5.2.md` (na raiz desta pasta) é a **referência passiva** (fonte única da verdade); os **bundles** e os **artefatos machine-readable** abaixo são o que você consome de fato.

## 0. Regra de ouro do contexto
**Leia SOMENTE:** (1) este CLAUDE.md; (2) **`CONTRATO_DE_DADOS.md` (raiz do repo) — OBRIGATÓRIO EM TODA SESSÃO**; (3) a pasta `00_fundacao/` (uma vez, na primeira sessão / Fase 0 — mas o `03_contrato_export.md` é releitura obrigatória se o seu cartão grava dados); (4) o `00_contrato_*.md` da rodada atual; (5) o `alg_*.md` do ÚNICO algoritmo desta sessão.

> **⚠ POR QUE o (2) é novo e obrigatório [correção estrutural da torre, 2026-07-19].** O contrato de export (§17) vive na `00_fundacao/`, que a regra antiga mandava ler "uma vez, na Fase 0" — então uma sessão NOVA de R1/R2/R3 podia implementar um algoritmo **sem nunca ver** a SONDA (§17.2.2), a camada ⑦ `__final` (DI-08), o enriquecimento do `.jsonl` (S.7.1/DI-10) ou o timing v5.2.1 (§17.6). Foi exatamente o que a auditoria dos bundles do R3 encontrou: **zero menções** a qualquer um deles. O `CONTRATO_DE_DADOS.md` (raiz) é a consolidação didática e COMPLETA de tudo que um run persiste — **é o contrato executável de qualquer cartão que grave dados**. Precedência: SPEC > CONTRATO_DE_DADOS > bundles.

**NÃO leia** os `alg_*.md` de outros algoritmos, outras rodadas, nem a SPEC inteira — cada patch de fidelidade pertence a UM algoritmo (aplicar o dropout do e7 ou o kernel do c262 em outro lugar é o erro clássico). A SPEC completa existe para consulta pontual (grep de uma seção citada), nunca para leitura integral.

## 1. Ordem de precedência

> ⚠ **[T15] Para D101/D102.x (os 3 problemas de dados reais): `artifacts/decisions.json`
> VENCE o texto da SPEC** — a SPEC v5.2 ainda não absorveu esse delta (dívida
> registrada; texto canônico em `mestrado2/_real_experiments/docs/DECISOES_REAL_D101_D102.md`).
> Não trate o decidido como divergência a favor da SPEC.

## 1b. Ordem de precedência (texto original) (em QUALQUER conflito) — D83
**Anexo S > §22 > Anexo D (decisões) > corpo (§1–§21) > anexos E/I/K/L > anexos históricos (F/G/R).** Bundles são GERADOS da SPEC (`gen_bundles.py`); em divergência bundle×SPEC, **vale a SPEC** — e reporte a divergência em vez de escolher sozinho. O estado vinculante é **Anexo D §D.3 (D53–D102.16) + Anexo S**.

## 2. Protocolo de falha ("pára-e-loga") — D81
Gate vermelho (fidelidade ±3σ, bounds, sinal, hard-stop, DoE bit-a-bit, smoke da métrica) ⇒ **INTERROMPA o cartão, grave o diagnóstico no `.jsonl`/manifesto e devolva o controle ao autor**. **NUNCA** auto-conserte fidelidade, **NUNCA** invente uma definição ausente — pare e pergunte. Divergência entre o código do autor e o paper segue a bússola D29 (🔴 bug→artigo · 🔵 versão→artigo se toca o surrogate · 🟠 impl→código · 🟣 erratum→código · 🟢 extensão→nossa, declarada).

## 3. Estrutura desta pasta (o mapa de leitura)
```
claude_code_context/
├── CLAUDE.md                    ← você está aqui (leia SEMPRE, primeiro)
├── PROMPT_MESTRE.md             ← modelo de prompt por sessão (para o AUTOR, não para você)
├── SPEC_experimentos_v5.2.md    ← referência passiva completa (consulta pontual; nunca leitura integral)
├── REGISTRO_DECISOES_pingpong_v5.md ← o PORQUÊ rico de cada decisão D53–D102.16 (consulta)
├── gen_bundles.py               ← regenera os bundles a partir da SPEC (rode após editar a SPEC)
├── artifacts/                   ← dados que você CONSOME (não parseie a SPEC p/ isto)
│   ├── runs_matrix.csv          ← as 22.740 linhas do grid (20.850 + 1.890 dos 3 problemas reais, D101/D102.16) — DI-35 (run_id, exp, alg, problema, semente, q, tier, dist, stack, env)
│   ├── decisions.json           ← índice vinculante D53–D102.16 (id → título, supersedes, seções)
│   ├── envs.json                ← tabela alg→env + pin de threads (D79) + 6 ambientes
│   ├── characteristics.csv      ← matriz 28×12 da análise por característica (D71; +RE21/DDMOP7/ESTOQUE40 e a coluna real_world)
│   ├── repos.lock               ← SHA por repo (D80; <SHA> preenchidos no pre-flight)
│   └── anchors.json             ← âncoras de patch (D80; o patcher ABORTA em divergência)
├── 00_fundacao/                 ← Fase 0 (leia os 5, em ordem, UMA vez)
│   ├── 01_regras_globais.md     ← §0 + §1 + §5 (orçamento/DoE/sementes/FE/bounds) + §16 + TODAS as decisões D53–D102.16
│   ├── 02_arquitetura_harness.md← §2 (A2) + §16.5 (repo/despachantes/adapters) + §18/§19/§21 + N.4 + S.6 (envs)
│   ├── 03_contrato_export.md    ← §17 completo (3 camadas, solution_id, timing, .jsonl, persistência/bucket) + S.7
│   ├── 04_plano_F0_piloto_gates.md ← §22.0/22.1 (Fase 0) + §22.5 (piloto = GATE) + §22.6 (gates) + cartões S.4 + S.8
│   └── 05_problemas.md          ← §4 (os 25 sintéticos; +3 reais via decisions.json D101/D102) + S.5 (f_min/f_max) + L.19 (notas do problems.py)
├── 10_rodada1_matlab/           ← R1: contrato transversal + 1 arquivo por algoritmo MATLAB + pisos
├── 20_rodada2_botorch/          ← R2: contrato + c262 + c154
├── 30_rodada3_standalone/       ← R3: contrato + c122, b5(b5r/b5m), c311, c149, e81 + piso offline (D77)
├── 40_subestudos/               ← batch q=10 (D66) · sweep offline (D67) · varredura N dos pisos (D65)
└── 50_analise_R4/               ← §12–§15 + Anexo O (D69–D73; IGD+ primária; ref normalizado)
```

## 4. Escada de prioridade (ordem de ataque) — D84
**Fase 0** (`00_fundacao/`: infra D79/D80 + `src/doe.py` D63 + wrapper FE/escrita-atômica D57/D58/D61 + F0 expandido D81) →
**R1 (MATLAB, gate ±3σ) ∥ R2 (BoTorch)** → **R3 (standalone + piso offline D77)** → **sub-estudos** → **R4 (análise)**.
**Piloto de timing (§22.5) = GATE BLOQUEANTE (D84):** 1–2 sementes dos curingas (c149, JES, parede O(n³)) + **pico de RAM (D86)** ANTES de liberar as 30 sementes; estouro dispara o escalonamento JÁ decidido (D75/D59/vetorizar-c311) — nunca improvise um novo.

## 5. Invariantes que não se negociam
`maxFE = 31D−1` com **hard-stop exato** (D21/D61; MATLAB `MException('PlatEMO:Termination')`, Python `BudgetExhausted`). DoE `11D−1` LHS **carregado do artefato** `data/doe/{problema}/doe_{problema}_{semente}.npy` (D63) — **nunca regenerado**; teste bit-a-bit no F0. 30 sementes {0–28, 42}; offset `+1000·semente` p/ e81/c149 (D22); sementes internas via `SeedSequence((base, alg_id, iter, uso_id))` (D62). Export **float32 SEM arredondamento** (D53), **salvar TUDO** (D54); **bucket-only: c154, c122, e81, c149, c262** (resume lista o bucket — D58). `run_id = {exp}_{alg}_{problema}_{semente}` (D55); `solution_id` = dedup-por-X bit-a-bit (D57). Métrica lê o `f` **gravado na ①**; objetivos **normalizados**, ref HV = (1,1,…) normalizado (D69); endpoint primário **IGD+** (D70). 1 run = 1 core; `OMP/OPENBLAS/MKL/NUMEXPR=1` + `maxNumCompThreads(1)` (D79). **Higiene de memória (D86):** `torch.no_grad()` na predição + `del`+`gc.collect()` por iteração nos loops torch; a ponte MATLAB reseta o `Problem` pymoo ao fim de cada run. Toda parada anômala = `failed` no manifesto (D23/D60) — nunca silenciosa.

## 6. Definition of done (por sessão/cartão)
O cartão da sessão diz o teste de aceitação. Genericamente (§22.6): mecanismo fiel (dupla prova §17.5.1 + âncora J em ±3σ) · FE final exato · DoE/semente pareados por hash · guardas instaladas e logando · as 4 saídas válidas (3 Parquet + `.jsonl` + timing + fragmento de manifesto) · persistência conforme D54/D58. Ao terminar, escreva um sumário do que foi feito + pendências no diretório `handoff/` do repo (1 arquivo por sessão) — a próxima sessão começa lendo o seu.
