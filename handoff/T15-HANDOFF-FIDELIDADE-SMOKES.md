# T15 · HANDOFF PARA VALIDAÇÃO DE FIDELIDADE (D97) — smokes dos 3 problemas reais

> **De:** torre de controle · 2026-08-14 (noite, pós-commit `8fad445`)
> **Para:** o agente de validação de fidelidade do autor
> **Escopo:** TODOS os smokes rodados na integração T15 (RE21=25, DDMOP7=26,
> ESTOQUE40=27), onde cada resultado vive, e os caveats de proveniência que
> você PRECISA saber antes de balizar contra os artigos.
> **O que este handoff NÃO é:** veredito de fidelidade. Os portões que citamos
> são MECÂNICOS (orçamento/camadas/proveniência/contrato — D97 exclui
> fidelidade por desenho). Fidelidade = o SEU trabalho, manual, do autor.

---

## 0 · Mapa de 30 segundos

- **Células-smoke (12)**: todas em `data/_quarentena_smokes/` (nomes originais
  preservados; NÃO estão mais em `data/experiments/` — quarentena D102.14:
  célula de Mac nunca vira dado de campanha).
- **Instrumentação D97**: o `.jsonl` de CADA célula está lá junto (mesmo
  prefixo). É a sua matéria-prima: registros `decision`/`fit`/`footer` em
  ordem cronológica.
- **Datasets/DoE/sondas**: versionados no repo (commit `8fad445`), exceto o
  dataset DDMOP7 s0 (Mac, smoke) que fica fora do git de propósito.
- **Narrativa completa da onda**: REGISTRO PARTES **A49** (integração) e
  **A50** (validação exaustiva + erratas honestas), dossiê
  `handoff/C5-DOSSIE-FIDELIDADE-T15.md` (com §7-adendo).

## 1 · As células, uma a uma (o que rodou, o que saiu, onde está)

Todos os arquivos abaixo em `data/_quarentena_smokes/` com o prefixo dado.
Cada célula tem: `.jsonl` (instrumentação) · `.manifest.json` (⑤) ·
`__real/__pop/__surrogate/__timing.parquet` (①②③⑥) · offline tem também
`__final.parquet` + `__final.manifest.json` (⑦ + certidão).

| # | célula (prefixo) | regime | resultado mecânico | notas p/ fidelidade |
|---|---|---|---|---|
| 1 | `exp_main_nsga2_DDMOP7_0` | online piso, rota R1 (MATLAB nativo) | 526/526 exato; PORTÃO VERDE 8 gates | R1 = `src/ddmop7_value_local.m` chamando o `.p` por `eval_fcn_por_x`; contador interno do .p respeitado |
| 2 | `exp_main_c149_DDMOP7_0` | online surrogate, rota R2 (ponte Engine) | 526/526; PORTÃO VERDE 8 gates | R2 = `src/ddmop7_bridge.py` sob FEBudget `contabilidade='externa'`; batches ≤64 |
| 3 | `exp_main_c154_RE21_0` | online surrogate | PORTÃO VERDE | BoTorch/env_main |
| 4 | `exp_main_nsga2_RE21_0` | online piso | ✅ | — |
| 5 | `exp_main_nsga2_ESTOQUE40_0` | online piso | ✅ | — |
| 6 | `exp_main_c122_ESTOQUE40_0` | online surrogate | ⚠ INTERROMPIDA às 3h33 (decisão de fluxo; dado de piloto de custo) | célula INCOMPLETA de propósito — não use para fidelidade de convergência; serve p/ ver o loop do c122 em D=40 |
| 7 | `exp_main_e81_ESTOQUE40_0` | online surrogate (qPOTS) | **1239/1239 exato; 7h25; PORTÃO VERDE 8/8** | ver caveat §3.2 (gêmeo) e §3.3 (timing) |
| 8 | `exp_off_b5r_DDMOP7_0` | offline (o fechador do gap 3) | 526 dataset; 928 ger; ⑦ pós-hoc: 47 finais, **2 ND pós-real**; portão 0 vermelhos | ⑦ avaliada com Engine REAL; front ~4 pts esperado pela quantização f₁=k/17 |
| 9 | `exp_main_b5r_DDMOP7_0` | offline (duplicata em exp errado) | idêntica à #8 **bit-a-bit** (mesmos 47/2, ger 928) | use como PROVA de determinismo, não como célula extra |
| 10 | `exp_off_e103_RE21_0` | offline MATLAB (TSEMO) | ⑦: 100 finais, 100 ND; **PORTÃO VERDE 9/9** | rodada via `matlab -batch` + `experiments.m` (receita do driver) |
| 11 | `exp_off_b5r_RE21_0` | offline | ✅ 0 vermelhos, ⑦ presente | — |
| 12 | `exp_off_b5r_ESTOQUE40_0` | offline | ✅ 0 vermelhos, ⑦ presente | — |
| +1 | `exp_off_moead_media_ESTOQUE40_0` | piso offline | ✅ 0 vermelhos, ⑦ presente | — |

## 2 · O que ler no `.jsonl` (a matéria-prima D97)

Cada linha é um registro com `ts` + `rec`. Os tipos que interessam à
fidelidade:
- `rec: "decision"` — o caminho algorítmico da iteração com `motivo` em prosa
  (ex. real do e81: `"caminho": "e81_gen:thompson+nsga2+maximin"`, motivo: "1
  realização de Thompson por geração do NSGA-II (pop=4000, ngen=10) e seleção
  top-1 por maximin vs o dataset"). **É aqui que você bate contra o
  pseudocódigo do artigo, passo a passo.**
- `rec: "fit"` — n_treino, tempo, kernel, dtype, retries (ex.: e81 ger 525:
  `n_treino=963, kernel=get_matern_kern..., dtype=torch.float64`).
- `rec: "footer"` — fechamento contábil (FE, camadas, hashes).
A ③ (`__surrogate.parquet`) tem coluna `regime` por linha (busca vs `sonda`) e
`geracao` — a trilha posicional que o ⑦ referencia via `origem_geracao`/
`origem_linha`.

## 3 · CAVEATS DE PROVENIÊNCIA (leia antes de julgar qualquer número)

1. **Tudo aqui é Mac arm64/Accelerate.** O f-que-vira-dado nasce nas VMs
   Linux (D102.14). Estas células provam MECÂNICA e comportamento
   algorítmico; micro-diferenças numéricas vs VM são esperadas onde BLAS
   atravessa (f₂ do DDMOP7 em especial).
2. **e81 (#7): das 12:41 às 13:40 houve um SEGUNDO processo idêntico** rodando
   a mesma célula (incidente detectado e morto — REGISTRO A50). O `.jsonl`
   tem registros INTERCALADOS dos dois nessa janela de ~1h. O footer e as
   camadas finais são 100% do sobrevivente (escrita final atômica; manifesto
   `status=ok, fe=1239/1239`; timeline gateada VERDE). Para fidelidade:
   ignore a janela 12:41–13:40 ou filtre por continuidade de `geracao`.
3. **Timing do e81 contaminado**: ~1h42 dividindo CPU com o gêmeo + máquina
   carregada. NÃO use `__timing` desta célula para régua de custo.
4. **b5r em dose dupla (#8/#9)**: mesma semente, mesmo dataset ⇒ trajetórias
   idênticas. É evidência de determinismo, não duas amostras independentes.
5. **Dataset DDMOP7 s0 do Mac**: X = bloco 0 do CSV congelado dos sorteios
   oficiais do `DDMOP7('init')`; F = 526 avaliações do `.p` REAL neste Mac,
   geradas em 7 fatias foreground e montadas pelo caminho canônico
   (`gen_one`+`check_one` VERDES). O sidecar tem `wall_clock_s: 0.0` —
   assinatura honesta da montagem fatiada (motivo: macOS congela Engine em
   fundo; laudo na A50). Local: `data/datasets/DDMOP7/ds_DDMOP7_0.parquet`
   (+manifest) — FORA do git de propósito.
6. **c122 (#6) é incompleta por decisão** — não julgue convergência nela.

## 4 · Referências de verdade (contra o que balizar)

- **DDMOP7 — o oráculo é o BINÁRIO, não o texto**: `DDMOP7.p` oficial em
  `/Users/gmello/Documents/python_repos/mestrado2/_real_experiments/DDMOP/DDMOP_Exp/Problems/`
  (sha256 do .p: `97d3434fe7c6b777b049...`; repo DDMOP de He, Tian, Wang &
  Jin 2020, clone pinado `0f45d2c1`). Âncora de valor MEDIDA:
  `x=zeros(1,17), x[2]=0.5, x[6]=-0.2 → f=[4/17, 307/690] = [0.235294...,
  0.444927...]`. Estrutura medida: f₁=k/17 (escada), f₂=n/690; init
  obrigatório por processo; contador interno de 600 FE.
- **Contratos e decisões**: `claude_code_context/artifacts/decisions.json`
  (D101/D102.x — VENCE a SPEC p/ os 3 problemas); texto canônico em
  `mestrado2/_real_experiments/docs/DECISOES_REAL_D101_D102.md`.
- **Artigos/kits**: kits de leitura por família em
  `~/Desktop/kits_escritores/` (22 zips). Precedente de análise
  artigo-vs-código desta onda: `handoff/D0-LAUDO-C238-BADSUBSCRIPT.md`
  (bússola D29 — quando código vendorizado diverge do artigo, o artigo
  manda; fix `,[],1` no `Infill_EIM.m` com separação 28/28 vs 0/617).
- **Implementações a auditar** (código novo T15): `src/ddmop7_bridge.py`
  (rota R2 + motor), `src/ddmop7_value_local.m` (rota R1),
  `scripts/final_eval.py` (⑦ pós-hoc DDMOP7), `src/problems.py` (RE21 e
  ESTOQUE40 — busque `RE21`/`ESTOQUE40`), `scripts/gen_dataset_ddmop7.py`
  (Processo A). Runners offline com pós-hoc: `src/b5_prob.py`,
  `src/treed_media.py`, `src/c311_tgprmo.py` (paridade `_FinalPosHoc`).

## 5 · Sugestão de roteiro (se ajudar; ignore se tiver o seu)

Por célula: (a) abra o `.jsonl`, filtre `rec=decision`, e bata a SEQUÊNCIA de
caminhos contra o loop do artigo (init → fit → aquisição → seleção → update);
(b) confira no `fit` os hiperparâmetros/kernels contra o que o paper
especifica; (c) na ③, confira população/geração e o regime; (d) no offline,
confira que a ⑦ referencia a ÚLTIMA geração da busca (`origem_geracao`) e que
`nd_pos_real` marca o front APÓS avaliação real — a semântica B7.5 do
protocolo; (e) qualquer divergência: anote arquivo+linha+registro `ts` e
devolva à torre — quem julga é o autor (D97), quem conserta mediante decisão
dele somos nós.
