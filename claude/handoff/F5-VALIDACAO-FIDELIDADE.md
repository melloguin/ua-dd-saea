# HANDOFF F5 — VALIDAÇÃO DE FIDELIDADE DA RODADA-42 (torre → agente de fidelidade)

> **Missão:** analisar os resultados da rodada-42 (semente 42; 666/695 células ok) e produzir o
> **dossiê de fidelidade** que alimenta o julgamento D97 do autor. Você ANALISA e RECOMENDA;
> **o VEREDITO é do autor** — essa é a regra mais importante deste projeto.

---

## 1. A DOUTRINA (as regras que não se negociam)

1. **D97 — fidelidade é julgamento MANUAL do autor, a posteriori.** Seu produto é EVIDÊNCIA
   organizada + análise + score RECOMENDADO por config. Você NUNCA "conserta" fidelidade, NUNCA
   altera código de algoritmo. Se achar bug/divergência: documente com arquivo:linha e escale.
2. **D29 — bússola de divergência código×paper** (use ao classificar qualquer divergência):
   🔴 bug do código do autor original → segue o ARTIGO · 🔵 diferença de versão → artigo se toca
   o surrogate · 🟠 detalhe de implementação → segue o CÓDIGO · 🟣 erratum → código ·
   🟢 extensão NOSSA → declarada como nossa. Cada `alg_*.md` (bundles) já traz o checklist K.3/L/N
   dos patches de fidelidade com arquivo:linha — é a sua lista de verificação por algoritmo.
3. **§17.5.1 — o contrato de auditoria** (SPEC): a tabela pergunta-de-auditoria × campo-do-log ×
   veredito. É o molde do seu método: mecanismo ("dupla prova"), protocolo, contratos de adapter,
   guardas numéricas, saúde da trajetória, custo.
4. **Âncoras ±3σ (D81/§20/Anexo J)** = faixa-GUIA, não gate duro. Fora da faixa ⇒ investigar e
   reportar, nunca reprovar sozinho.
5. **D81 — ambiguidade/conflito ⇒ PARE e pergunte.**

## 2. O PROTOCOLO DE 3 CLASSES (o formato acordado com o autor)

Por config (22 algoritmos + 2 pisos extras = 24), produza score **0-10** + % de conformidade por
classe + recomendação (`aceitar` / `aceitar+caveat` / `investigar` / `reprovar`):

- **Classe A — Fidelidade de MECANISMO:** o algoritmo fez o que o paper descreve? Evidência: ⑥
  jsonl (eventos por iteração: acqf, seleções, fallbacks, guardas disparadas), ③ snapshots do
  surrogate, `params`/`sigma_dict` do ⑤ vs a receita L.x da SPEC, checklist D29 do `alg_*.md`.
- **Classe B — SAÚDE de comportamento:** trajetória saudável? HV/IGD+ progride; o surrogate
  APRENDE (sonda: correlação μ×f-real cresce ao longo do run); σ calibrado; sem estagnação
  inexplicada; âncoras do Anexo J em ±3σ; SA-configs vs pisos (a razão de ser do estudo).
- **Classe C — CONFORMIDADE de protocolo/export:** FE exato (①), CP-init/DoE pareado por hash,
  7 camadas íntegras, sonda na cadência (§17.2.2), determinismo, timing plausível (④).

**A SONDA é o seu instrumento-mestre da Classe B**: 2000 pontos Sobol idênticos (online) /
1 bloco de 20000 (offline) avaliados pelo surrogate de CADA config a custo 0 FE — é a régua COMUM
que torna a qualidade dos surrogates comparável entre algoritmos. μ da ③-sonda × f real dos mesmos
pontos (artefato `data/sonda/`) = correlação/RMSE por bloco → a curva "o surrogate aprendeu?".

## 3. AS 7 CAMADAS (sua matéria-prima, por run)

① real (X,F float32 de TODAS as avaliações) · ② populações/geração · ③ surrogate por geração +
blocos de SONDA · ④ timing (série n×tempo_fit) · ⑤ manifesto rico (params, sigma_dict, guards,
motivo_parada) · ⑥ jsonl DI-10 (o filme do mecanismo) · ⑦ __final (offline: ND final avaliado na
função REAL — o endpoint oficial do regime). `CONTRATO_DE_DADOS.md` = o dicionário completo.
⚠ c154/c122/e81/c149/c262 são **bucket-only na ③** (D54/D58): a ③ pode estar só no
`gs://mestrado_experiments`.

## 4. PIPELINE RECOMENDADO

1. **CENSO E TRIAGEM (antes de qualquer métrica):** mapear as 695 células por máquina
   (`scripts/censo42.py`, `portao.py --varredura`) e explicar CADA uma das ~29 não-ok
   (esperadas: ~11 ⚪ c154-main >12h [DI-40]; 5 c154-batch nem disparadas [DI-40]; resto = triar).
   **⚠ NÃO CONFIE NO `status` (bug B1, §6): filtre por `motivo_parada != 'orcamento'` também nos
   runs 'ok'** — caso provado: `sweep-big-mvns/c311/MMF16_20/42` = `gpy_bfgs_linalg` mascarado.
2. **GATES OBJETIVOS:** portão verde (accept+auditar+final_eval) em TODAS as células que entrarem
   na análise — no env_main do Mac (bug B3: accept sai VERDE sem checar em env sem pyarrow).
   ⑦ do e103: conferir que o driver pós-hoc rodou (é gerada FORA do run, via final_eval).
3. **MÉTRICAS:** `src/metrics.py` do repo (NUNCA reimplementar): normalização (ideal,nadir) da
   S.5 (D69), ref-HV=1,1/coord, **IGD+ primária (D70)**, +HV/IGD/GD/spacing. GATE antes de
   qualquer conta: `hv_smoke_bbob_f1()==1,04333` (D92). Molde pronto: o O-18 da operação
   (`validacao_cruzada_indicadores.html` + REGISTRO_OPERACAO_RODADA42.md) já fez isso p/ 24 células.
4. **POR CONFIG (o coração):** 1 workflow/agente por algoritmo com (a) o `alg_*.md` do bundle
   (checklist D29), (b) a receita L.x da SPEC, (c) as camadas das suas ~25 células. Ler o ⑥
   (mecanismo), a sonda (aprendizado), as curvas métrica×FE, as guardas disparadas, o ④ (custo).
   Kits de leitura dos papers: `~/Desktop/kits_escritores` (22 zips, 1 por família).
5. **COMPARATIVOS TRANSVERSAIS:** SA vs pisos (régua; esperado do R1: SA-vantagem CRESCE com D);
   online vs offline do mesmo alg; sweep small→medium→big (mais dado → melhor? c311 vs
   treed_media = o achado de escalabilidade); batch: c149 no habitat (D12) vs seu q=1 degradado.
6. **DOSSIÊ:** atualizar `DOSSIE_FIDELIDADE_R1.md` (formato já estabelecido — notas v2 lá dentro
   mostram o padrão) → mesa de julgamento D97 do autor, config a config.

## 5. PRIORS — o que JÁ foi julgado/notado (não parta do zero)

- **Aceitos pelo autor:** c217 **9/10** (surrogate quase-inativo em δ=0,8 sob 31D−1 = mecanismo
  CERTO, vira caveat de análise) · e81 9/10 · piso-off/ablação D77 9/10 · c311-fase-B 8,5.
- **Notas de comportamento v2 (1 semente, pós-retrofit)** no DOSSIE §2-bis; b5r 7,0 · b5m **5,0**
  (GP degenerado no DTLZ2 obj-2: μ≈0, corr 0,006 — FLAG aceitar+caveat, sensibilidade ao treino
  único) · c311 7,5 (ZDT1 dist 0,0012 da frente analítica = melhor offline).
- **Validação final (32 finders, journal `wf_c451718a-b88`):** cada finder tem um bloco
  `comportamento_smoke` por config — pré-leitura útil; notas 6-8,5.

## 6. ⚠ CAVEATS OBRIGATÓRIOS (sem eles você vai gerar falso-alarme)

1. **B1 (bug CONFIRMADO, ainda não corrigido):** `experiments.py:209` sobrescreve `status=failed`
   do runner com `ok` quando o aborto é por `break` (standalone). Triagem: use `motivo_parada`.
2. **B2:** o carve-out ⚪ procura `cache_cap`, mas os runners emitem `cache_hit_travado` — células
   nesse estado aparecem erradas no portão.
3. **⑥ sem footer** em parte dos runs (c311 ~7/58 por gcs ausente no env; moead_media 1 caso de
   2-escritores; bucket NUNCA tem footer — upload precede o fechamento). Jsonl truncado ≠
   mecanismo ruim; cruze com ⑤/①.
4. **Cross-machine:** NUNCA compare floats bit-a-bit entre máquinas. MATLAB = bit-idêntico
   Mac×vm3 (provado O-18); Python difere por microarquitetura de CPU (~1,5% pior caso em HV);
   regra vigente: **um config, uma máquina** (dado de 1 config vem TODO da mesma máquina).
5. **BBOB:** front verdadeiro é EMPÍRICO (cache NSGA-II §12.1) — IGD relativo ao cache; HV pode
   passar de 1,1; comparação com literatura NÃO vale (só interna).
6. **Esperados que NÃO são bugs:** c149 degradado no main (fora do habitat, D12 — é ACHADO);
   qNEHVI sem ruído (ressalva §16); σ do c311/treed = extensão NOSSA (paper nunca consome);
   b5r modo-7 = variante v3 DECLARADA (DI-28); N=20 dos pisos PROVISÓRIO (DI-39; células podem
   ser re-rodadas se o SUB-varN eleger N≠20); cache-hit=0 FE (D89 — duplicata perde SLOT, não FE;
   nº de cache-hits no ⑥ é dado de robustez); MMF16_20 no sweep/batch (DI-35.3, não MMF1);
   `main/c154b/` em data/ = artefato espúrio conhecido (ignorar; não é config do grid).
7. **c154:** ~11 células main ⚪ (>12h, aborto por PROJEÇÃO ~6,3h queimadas, SEM parquets — curva
   só no ⑥) e 5 batch nem disparadas (DI-40). As ~14 células main restantes são dado ÍNTEGRO.
8. **Semente 42 é UMA amostra:** notas baixas por comportamento em 1 semente ≠ infidelidade
   (precedente: as notas v2 do dossiê). Separe SEMPRE "mecanismo errado" de "semente infeliz".

## 7. ENTREGÁVEL

Por config: **score 0-10 + % por classe (A/B/C) + recomendação + evidência (arquivo:linha /
célula / gráfico)**. Consolidado: tabela 24×(A,B,C,score,rec) + lista de achados escalados
(bugs → torre; divergências D29 → mesa do autor) + os comparativos transversais. Formato-molde:
`DOSSIE_FIDELIDADE_R1.md` (§ notas v2). O DoD do autor: *"só sai dessa etapa com o diagnóstico
de que está 100% impecável"* — impecável = TUDO explicado (cada célula, cada anomalia com causa),
não "tudo perfeito".

## 8. ONDE ESTÁ CADA COISA

Dados: `data/experiments/` (Mac; VMs têm os seus; ③ bucket-only no `gs://mestrado_experiments`) ·
sonda real: `data/sonda/` · Gates: `scripts/{portao,accept,auditar,final_eval,censo42}.py` ·
Métrica: `src/metrics.py` · Receitas: SPEC §L.1-L.19 + `claude_code_context/2x_*//alg_*.md` ·
Âncoras: `anchors.json` + SPEC §20/Anexo J · Doutrina: SPEC §17.5.1, D29 (Anexo D), D69/D70/D92 ·
Priors: `DOSSIE_FIDELIDADE_R1.md` + `handoff/*.md` + REGISTRO PARTES A1-A28 · Operação:
`REGISTRO_OPERACAO_RODADA42.md` (O-01..O-18) + `validacao_cruzada_indicadores.html` (molde) ·
Interpretador p/ gates/métricas: `/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python`.
