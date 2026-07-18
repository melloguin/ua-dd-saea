# R1-e103 — RELATÓRIO DE EXECUÇÃO da sessão (narrativa do processo, p/ a torre)

**Data:** 2026-07-18 · **Cartão:** R1-e103 (IBEA-MS — standalone do autor, OFFLINE — L.15/N.3/D90/D93).
**Resultado:** 3 gates VERDES (MMF1 8,9s / DTLZ2 15,3s / ZDT1 36,9s ×semente 0) + prova de
não-contaminação de path + regressão total verde (12 configs ×MMF1 + stub + F0-01..04 +
preflight + suíte 90 OK). **FECHA A RODADA 1 MATLAB.** Fidelidade = lote (D97).

## 1. Ambiente (D81 — verificado ANTES de qualquer código)

MATLAB R2025a + pyenv InProcess `~/ponte_teste/bin/python` (3.11) → `py.numpy.array([1,2,3]).sum()`
= **6** ✓; Statistics Toolbox ✓ (kmeans/pdist/pdist2 — as dependências do e103; sem DL);
env-main com pyarrow ✓; datasets D90 MMF1/DTLZ2/ZDT1 semente 0 presentes em `data/datasets/`
com sidecars (x_hash/f_hash/dataset_hash) ✓. Lições operacionais seguidas: MATLAB SEMPRE via
`-batch` com saída em ARQUIVO (nunca pipe); término lido pelo estado final do log/`.jsonl`.

## 2. Contexto lido (na ordem do cartão, e SOMENTE ele)

HANDOFF_MESTRE (§10/§11) → R1-e74 (o molde do worker de path dedicado PROVADO) → R1-c238
(classdef/onCleanup/sombra reversa) → claude_code_context/CLAUDE.md → linha R1-e103 do INDEX →
00_contrato_rodada1 (N.0/N.3/S.2-e103) → **alg_e103_ibeams.md INTEIRO** → 01_regras_globais
(D87–D100) → 03_contrato_export (§17/S.7-e103). Greps pontuais na SPEC: §22-e103 (:1442),
E.9-e103, I.15, **§11 (avaliação final offline)**, B7.5. NENHUM alg_*.md de outro algoritmo.
Artefatos: anchors.json (3 âncoras e103), seeds.json (`_default` — harness não cria semente p/
e103; dataset_offline: tier small = nome sem sufixo), params.json (por_config/e103), repos.lock.

## 3. Verificação prévia do código real (antes do plano)

- Repo AUTOCONTIDO confirmado (S.2-e103): DACE/RBFN/IBEA/PopOperate próprios; 397 linhas .m.
- As âncoras batem no stock: `{1,20,1/Global.D,20}` em IBEAMS:43 × `Site = rand<proM/D` em
  GA.m:69 (o 1/D² efetivo); diagonal do JudgeModel (:19-21 I=0/MSEI=6√MSE → :32 `all` zera);
  `ceil(sqrt(Global.D*11-1))` em construct_Rnets:4; `inv(Z'Z)Z'` na :10; `cd+addpath(genpath)`
  em :32-33; hardcodes D=20/M=3/DTLZ1 em :23-31; sem retorno na assinatura.
- Confirmei o marcador MSE=zeros: `AmendKriCal:6`/`AmendRBFCal:5` filtram `SumMSE==0` e
  preservam o Obj real — a injeção (c) funciona por construção.
- **Varredura de sombra** (find por basename): CalFitness ×62 / EnvironmentalSelection ×155 /
  dacefit+predictor ×29 / regpoly*/corr* ×2 / GA ×1 / TournamentSelection ×2 na `_PlatEMO`;
  TournamentSelection também na CLMEA_Code 4.1; dsmerge ×2 (c141, AB-SAEA); **zero vs src/**.
  → worker dedicado com REMOÇÃO DAS DUAS árvores-gorila + addpath próprio POR ÚLTIMO.
- `accept.py`: o gate genérico serve ao e103 SEM MUDANÇA (check_fe deriva D das colunas da ① e
  exige 31D−1 linhas = exatamente o tamanho do dataset; scripts/*.py fora da minha faixa).
- FEBudget: `n_init` parametrizável → `n_init = 31D−1` faz TODO o dataset ser fase `init` e
  `init_X()` devolver o dataset inteiro (o CP-init offline sai de graça do molde online).

## 4. As decisões de desenho (registradas p/ veto na §8 do handoff)

1. **Orçamento = o dataset**: as 31D−1 linhas entram via `bud.evaluate` com evalFcn devolvendo
   o F DO ARTEFATO (não a ponte) → ① bit-exata ao ds por construção + o FEBudget esgotado vira
   a rede que TRANSFORMA qualquer FE na busca em exceção não-engolida (violação D90, não
   término). A ponte fica metadata-only (CP-bounds).
2. **CP-init offline = x_hash E f_hash** (mais forte que o online): o F injetado também é
   artefato — hash float64 dos dois contra o sidecar.
3. **Concretização da âncora e103-judgemodel**: OR com `logical(eye(N))` na própria :32 (1
   linha, mesma semântica do `Msite(...)=true` exemplificado no S.2-e103) — escolhida porque o
   literal stock DESAPARECE (o preflight distingue STOCK/APLICADO por substring; um insert
   deixaria o expect_before presente e o preflight leria "STOCK" p/ sempre).
4. **③ = 2 linhas/membro (μ dos DOIS modelos por re-predição read-only)**: a L.15 pede "μ dos
   DOIS modelos (RBFN_cal incondicional — barato)"; re-predizer Kriging E RBFN sobre a pop
   selecionada dá a visão CRUA de cada modelo (a alternativa — copiar os objs amendados da pop
   — mistura F real com μ e não produz o RBFN quando o Kriging lidera).
5. **② offline = membros do DATASET na pop selecionada** (única leitura em que o ② continua
   sendo "população REAL"); geração sem membro real = sem linha; série completa no jsonl.
6. **e103_gen minimalista conforme S.7** (CurGen/KFlag/√MSE + contadores) — NÃO instrumentei o
   interior do JudgeModel (fração de pares reprovados por objetivo etc.): a S.7 não pede e o
   custo de patch extra em código de decisão não se justifica sem pedido (D81 conservador).
7. **exp='main' no piloto** (precedente c238/e74; o gate default do cartão); a bateria usa
   `exp='off'` pela runs_matrix — o runner recebe exp por argumento.

## 5. Implementação (ordem real)

1. Patches na árvore (3 arquivos): IBEAMS.m (L.15 a–d + âncora pm + hooks inst) →
   JudgeModel.m:32 (âncora diagonal) → construct_Rnets.m:4/:10 (D93 + mldivide).
2. `src/e103_instrument.m` novo (setup/gen/busca_fim; ② por solutionIdOf; ③ 2×100×99; guards
   `quase_singular_setup`/`mse_neg`; timing §17.6 de 1 linha).
3. `src/experiment.m`: case 'e103' + `run_e103` + `ensure_paths_e103` (25 asserts which-all) +
   `load_dataset` + `nm_dataset_*`.
4. anchors.json concretizado → `preflight.py` = APLICADO ×3 (rodado ANTES do 1º run).
5. Armadilha evitada: o expect_before `1/Global.D` casaria com o COMENTÁRIO do patch (o
   preflight busca substring no arquivo inteiro) — comentário reescrito sem o token.

## 6. Validação (comando a comando)

- **MMF1/0**: VERDE na 1ª execução (8,9s; RCOND 1,3e-17 no mldivide da RBFN = o warning
  ESPERADO, contado no e103_setup). **DTLZ2/0** 15,3s; **ZDT1/0** 36,9s — VERDES.
- **3 gates accept.py exit 0** (① = 31D−1 = dataset completo).
- **Prova de não-contaminação**: `c217 → e103 → nsga2 → b3` no MESMO processo (4.15
  pré-carregada): 4 verdes; asserts `which` pós-estágio (zero resíduos e103; dacefit → K-RVEA
  4.15 no fim). Direção inversa provada pelos 25 asserts do ensure_paths_e103 (smoke no header).
- **Auditoria pyarrow dos 3**: 30+ checks/problema — ① bit-consistente (X e F vs artefato,
  pós-cast float32), ② ⊆ ① e contagem/geração == n_ds_membros do jsonl (99/99), ③ 19.800
  linhas (2/membro; sigma só nas Kriging; rsi sem órfãos; μ_Kriging ≡ F real nos membros do ds
  — max|Δ|=0), timing 1 linha, manifesto/jsonl coerentes. 1 check meu inicial era ingênuo
  (② "até g99" — o ZDT1 zera membros reais na g5) → check refinado com cross-check jsonl.
- **Regressão**: accept_r1_00 (stub) 0 falhas + c141/b1/b4/e7/c238/e74/nsga3/moead/smsemoa
  ×MMF1 verdes (1 processo; c217/nsga2/b3 re-validados na prova) + **12 gates accept.py exit
  0** + F0-01..04 exit 0 + `preflight.py --write` exit 0 (re-hash `e103_ibeams` →
  `7ab83a7e…`) + suíte unittest **90 OK** (1 skip; 82→90 = testes novos da faixa paralela).
  Gates do c154/c262 NÃO rodados (faixa da sessão paralela).

## 7. Números p/ o dossiê (M7/§17.6 — guia D97)

| | MMF1 | DTLZ2 | ZDT1 |
|---|---|---|---|
| wall total / alg | 8,9 / 4,2 s | 15,3 / 11,6 s | 36,9 / 35,8 s |
| fit único (krig+rbfn) | 0,06+0,12 s | 4,7+0,1 s | **24,0**+0,1 s |
| busca (99 ger) | 4,4 s | 6,7 s | 11,7 s |
| KFlag=1 (Kriging líder) | 0/99 | 0/99 | **99/99** |
| membros ds na pop g1→g99 | 50→29 | 75→15 | 82→**0 (g5)** |
| centros RBFN (D93) | 8 | 20 | 31 |
| σ²_DACE por obj | 4,7e-2 · 2,7 | ~4e-2 ×3 | **3,8e-32** · 1,2e-2 |

O e103 é o run mais BARATO da R1 (ZDT1 37s vs c238 3h55); 30 sementes ZDT1 ≈ 19 min/core. O
custo é o fit O(n³) do DACE — exatamente o eixo que o sweep (2k/50k) vai estressar; a linha
§17.6 única por run alimenta a curva.

## 8. DEFINIÇÕES EM ABERTO p/ a torre levantar com o autor

1. **Persistência da avaliação REAL do ND final offline (§11/B7.5)** — decidir ANTES do R3
   (afeta os 5 configs offline). Recomendação: pós-hoc em Python canônico, camada própria
   (`__final.parquet`?) — schema/naming = território da torre. Este run já salva FinalDec (≡ ③
   g99) — nada se perde.
2. Vetos/ratificações: âncora e103-judgemodel concretizada (OR com eye) · expect_after das
   outras 2 âncoras concretizados · ③ 2-linhas/membro (re-predição crua) · ② = membros do
   dataset (gerações sem membro real ficam vazias).
3. INDEX: a torre marca o R1-e103 (e a R1 MATLAB inteira) como ✅.
