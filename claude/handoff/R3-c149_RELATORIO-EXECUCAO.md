# R3-c149 — RELATÓRIO DE EXECUÇÃO (o COMO: a narrativa, com o que deu errado)

> Companheiro de `handoff/R3-c149.md` (o *o quê*) e do
> `R3-c149_REPASSE-A-TORRE.md` (validação + definições em aberto). Sessão de
> 2026-07-22, timebox D-20 de 10 h.

## Linha do tempo

1. **Fase 0 (gate de ambiente)** — `alg_to_env.c149 = env_main` conferido no
   `envs.json` (FONTE ÚNICA, DI-14); TAREFA 0: torch **2.11.0** presente ✅
   (nada instalado — D80); suíte **247 OK (3 skip)**; `preflight.py` exit 0
   (a âncora `c149-fix-M` do preflight segue STOCK — correto: o fix é
   aplicado na RECONSTRUÇÃO, o repo fica intocado, D30).
2. **Leitura obrigatória** — CLAUDE.md (2×), CONTRATO_DE_DADOS.md INTEIRO,
   `03_contrato_export.md` INTEIRO (releitura), contrato R3, o cartão
   `alg_c149_lbnmobo.md`, a linha §22.4·3.4 da SPEC (checklist vinculante),
   repasse c122 + R3-00 §herança, REGISTRO A10 (DI-21). ✅
3. **Recon multi-agente com verificação adversarial** (5 leitores × 5
   verificadores céticos): mapa das APIs do harness, do molde c122, dos
   gates, do export/budget e dos artefatos. Os verificadores derrubaram 3
   afirmações erradas e apontaram ~40 omissões materiais — as decisivas:
   o offset D22 entra DENTRO da base do SeedSequence (não "ao lado");
   `write_run_outputs` carimba `status='ok'` hard-coded; `enable_bucket=True`
   PODARIA a ③ local (c149 ∈ BUCKET_ONLY_ALGS); o catálogo de uso_id do c149
   é POR ITERAÇÃO (≠ c122); o check `mu_0`-só do gate c122 tinha cobertura
   ilusória (o do c149 checa TODAS as colunas μ/σ).
4. **Troca de modelo na sessão** (Opus 4.8 → Fable 5, decisão do usuário) —
   validação cruzada do estado sem retrabalho; nenhum defeito encontrado no
   que estava feito.
5. **Pergunta D81 ao autor (PM `prob_var`)** — a nota SPEC:722 ("1/30
   hard-coded, não 1/D") contradiz o código medido (o repo chama
   `NSGA2(pop_size=1000)` puro; o pymoo 0.6.2 calcula `min(0.5, 1/n_var)`).
   **Autor cravou: default do pymoo (1/D)** — 0,5 no MMF1, 1/12 no DTLZ2,
   1/30 no ZDT1. Registrado no manifesto de cada run.
6. **Implementação** (`src/c149_lbnmobo.py`) — reconstrução in-memory
   (tabela de mapeamento peça-a-peça no handoff §reconstrução). Um bloco
   vestigial de refactor (sonda final) quebrado foi pego na releitura
   imediata e corrigido antes de qualquer run.
7. **Testes unitários** — 20 novos; 2 falhas INICIAIS eram dos PRÓPRIOS
   testes: (i) o teste de simetria da normalização D96 usava candidatos que
   NÃO eram simétricos pós-normalização (4000 no obj₁ cai fora do range
   observado [0,10] ⇒ HVI=0 — o runner estava CERTO); (ii) o teste de dtype
   esperava float64 fixo, mas o contexto restaura o valor ANTERIOR (float32
   no processo de teste, onde `pin_runtime` não roda). Corrigidos os testes,
   20/20 OK.
8. **Smoke MMF1** — ponta-a-ponta na 1ª execução: fe=61 EXATO, 40 ger,
   21 blocos de sonda, wall 243 s. (Checkpoint das 5 h do timebox: CUMPRIDO
   com folga.)
9. **Gate accept 12/13 → achado real → fix → re-run.** O único FAIL foi o
   check DEF-C3 que EU desenhei mais forte que o precedente: as linhas de
   SONDA saíam com `espaco_modelo=NULL` porque `emit_sonda_block` não aceita
   as colunas C3 (lacuna do harness). Como os μ/σ da sonda TAMBÉM são
   des-padronizados, a declaração pertence a todas as linhas ⇒
   `_stamp_c3_sonda` carimba o bloco recém-emitido no buffer do runner
   (ordem intacta). MMF1 re-rodado do zero → 13/13 VERDE.
10. **Pilotos DTLZ2 → ZDT1 (teto 8 h)** — rodados SOZINHOS na máquina (a
    lição do repasse c122 §6: walls medidos sob disputa saem 2–4×
    pessimistas e contaminariam o dimensionamento do M7/M8).
11. **Provas caras** (`C149_SLOW=1`): determinismo bit-a-bit (2× MMF1) e
    não-perturbação da sonda (① com k=2 ≡ ① com k=10⁹) — molde c122,
    inclusive o mecanismo de toggle (monkeypatch de `H.SONDA_K`, por isso o
    runner lê `H.SONDA_K` DINAMICAMENTE).
12. **Regressão completa + fechamento** — re-executada AO VIVO no repasse.

## O que deu errado (e como foi pego)

- **Bloco vestigial no runner** (etapa 6): releitura imediata pós-escrita.
- **2 testes errados** (etapa 7): o próprio traceback denunciou; em ambos a
  verificação manual provou que o RUNNER estava correto e o teste não.
- **`espaco_modelo=NULL` na sonda** (etapa 9): pego pelo MEU gate — o check
  novo (herdado de um achado da recon: o gate do c122 só olhava `mu_0`) foi
  desenhado para cobrir TODAS as colunas C1/C3, e cobrou.
- **Nada de runtime quebrou nos pilotos** — o hazard cache-hit×arquivo
  (IndexError do c122) morre por construção aqui (treino ⇐ `bud.records`).

## Custo medido (insumo do M7/M8) — semente 0, Mac M1 Pro, 1 core

| Run | wall | s/ger | fit | busca | sonda |
|---|---|---|---|---|---|
| MMF1 | 240 s | ~6,0 | 18% | 80% | 0,5 s |
| DTLZ2 | 2.636 s | ~11,0 | 52% | 47% | 2,5 s |
| ZDT1 | 12.119 s | ~20,2 | 70% | 30% | 6,0 s |

- **A busca (NSGA-II pop 1000 × 100 ger) é ~CONSTANTE por geração** (~5–6 s);
  o que cresce com n é o FIT (60 épocas × n/10 batches × 10 redes = ~linear
  em n) — a assinatura do BNN que o M.11 prevê. Contraste com o c122 (fit
  87% no ZDT1 mas PLATÔ por T_max) e com a parede O(n³) dos GPs.
- ZDT1 fechou em **3,37 h < teto de 8 h** (o curinga de custo coube; ~42%
  do teto). Extrapolação M8 (30 sementes × 3 problemas piloto): dominada
  pelo ZDT1 — ~101 h de CPU por problema-30-sementes em 1 core; paralelismo
  por semente resolve (decisão de dimensionamento do M7, não deste cartão).
- ⚠ Os walls acima foram medidos com a máquina DEDICADA (lição do repasse
  c122 §6 aplicada — pilotos rodaram sozinhos, sem regressão em paralelo).
- Sonda: ~0,02–0,03 s/bloco de 2.000 — desprezível e excluída do
  `tempo_geracao_s` (DI-13.10).
