# R1-e74 — RELATÓRIO DE EXECUÇÃO da sessão (narrativa do processo, p/ a torre)

**Data:** 2026-07-18 · **Cartão:** R1-e74 (CLMEA — árvore PlatEMO 4.1 própria, D95/N.0-4.1).
**Resultado:** 3 gates VERDES (MMF1/DTLZ2/ZDT1 ×semente 0) + prova de não-contaminação de path +
regressão total verde (12 configs ×MMF1, F0-01..04, preflight, suíte 82 OK). Fidelidade = lote (D97).

## 1. Ambiente (D81 — verificado ANTES de qualquer código)

MATLAB R2025a **Update 1** + pyenv InProcess `~/ponte_teste/bin/python` → `py.numpy.array([1,2,3]).sum()`
= **6** ✓; Deep Learning Toolbox ✓ (newrbe/newpnn/sim) + Statistics ✓ (pdist2); env-main com
pyarrow 25.0.0 ✓; DoE MMF1/DTLZ2/ZDT1 semente 0 presentes em `data/doe/` ✓. Lições operacionais
seguidas: MATLAB SEMPRE via `-batch` com saída em ARQUIVO (nunca pipe); término lido pelo FOOTER
do `.jsonl`.

## 2. Contexto lido (na ordem do cartão, e SOMENTE ele)

HANDOFF_MESTRE (§10/§11) → R1-c238 (onCleanup/sombra reversa) → R1-c217 (template run_*/receita
N.0/sync D89) → claude_code_context/CLAUDE.md → linha R1-e74 do INDEX → 00_contrato_rodada1
(N.0 + **N.0-4.1**) → **alg_e74_clmea.md INTEIRO** → 01_regras_globais (D53–D100) →
03_contrato_export (§17/S.7). Greps pontuais na SPEC: ClassifierSelect (fix :9), K.5.2 (fix
opcional), D74 (REGISTRO_DECISOES), S.2#16-17, B16.x, S.7-e74. NENHUM alg_*.md de outro algoritmo.

## 3. Verificação prévia do código real (antes do plano)

- As âncoras batem: 3 chamadas em CLMEA.m:56/:66/:76; `x_offspring(Choose,:)` em Local_infill:47;
  `NDSort(Parent,inf)` em ClassifierSelect:9; N=100/200 em :28-32; FE em :34/:50/:59/:69/:79.
- Núcleo 4.1 confirmado (N.0-4.1): parser do UserProblem SEM `once` (:43) → Evaluation POR
  INDIVÍDUO (:80-84, `CallFcn(evalFcn, x_1xD, data)`); `pro.FE=0` em ALGORITHM.m:74; addpath do
  Solve :75-76; ALGORITHM aceita só {parameter,save,outputFcn}; `Problem.FE` é público (sync ok).
- **518 basenames** colidem entre CLMEA_Code e _PlatEMO (`comm` dos `find`) — número que dimensiona
  o risco; zero colisão da CLMEA_Code com `src/*.m`.
- `anchors.json`: `e74-mask` já literal; `e74-ndsort-obj` com expect_after DESCRITIVO
  (`<NDSort sobre objetivos preditos>`) → exigiria concretização sinalizada.
- `params.json` sem chave e74 própria no por_config além de N/árvore/CR/init/dedup — defaults do
  ParameterSet cobrem o Balde B (registrado no manifesto).

## 4. A decisão delicada: concretizar o `e74-ndsort-obj`

O texto descritivo ("objetivos preditos") não é implementável literalmente na :9 — ali NÃO existe
regressor (só o PNN, que prevê CLASSE, não objetivos). Três candidatos avaliados:
1. `y_label = vec2ind(sim(net_pnn,Parent'))` (classes preditas) — REJEITADO: o nível-1 pode sair
   VAZIO (PNN com spread grande vota na classe majoritária) → `randi(0,…)` = crash NOVO que o
   stock não tinha; e muda o idioma (o stock RE-computa por ND-sort).
2. `y_label = y_train'` (classes-quota do Data_Process) — REJEITADO: perde o cap `>4→4` e a
   semântica de NÍVEL ND que a :9 stock computa.
3. **`[y_label,~] = NDSort(y_obj_e74,inf)`** (NDSort sobre os OBJETIVOS REAIS dos pais, com o
   pareamento x_train↔obj recuperado por um 3º output read-only do Data_Process) — **ESCOLHIDO**:
   é a correção MÍNIMA do bug confirmado ("NDSort sobre DECISÃO → sobre OBJETIVOS", §22/K.5.2),
   mantém o idioma e o cap, nível-1 nunca vazio, e nos pontos do arquivo "predito ≡ real"
   (newrbe interpola exato) — o "preditos" da âncora não contradiz.
Sinalização de veto registrada no anchors.json (campo `nota`), no handoff (§8.2) e aqui.

## 5. Implementação (ordem real)

1. Patches na árvore (5 arquivos): Data_Process (+y_obj_e74) → ClassifierSelect (🔴 :9 + inst) →
   Local_infill (🔴 :47 + inst) → Hv_Select (D74 + inst) → CLMEA.m (init injetado + assert L.8 +
   mins ×3 + k_local + syncs D89 ×5 + boot instrumentado + D60-c stall).
2. `src/e74_instrument.m` novo (③ por estratégia + e74_gen/e74_boot + guards + timing §17.6).
3. `src/experiment.m`: case 'e74' + `run_e74` (molde run_c238, SEM once, evalFcn por indivíduo
   `e74_eval_one` com [dec,obj,con]) + `ensure_paths_e74` (path-swap + 15 asserts which-all +
   onCleanup(path(prev))).
4. anchors.json concretizado → `preflight.py` = APLICADO nos 2 e74 ✓ (rodado ANTES do 1º run).

## 6. Validação (comando a comando)

- **MMF1/0**: VERDE na 1ª execução (FE=61, cp ✓, wall 20,6s) — accept.py exit 0.
- **DTLZ2/0**: VERDE (371, 261s). **ZDT1/0**: VERDE (929, 485s) — background, wall MEDIDO SOLO
  (nenhum processo concorrente — dado limpo p/ M7).
- **Auditoria pyarrow dos 3**: schema §17.2 coluna a coluna (①②③/timing), ① com 31D−1 exatas
  (init+opt, fe_index contíguo, sid único), ② referencia ①, ③ rsi órfão-zero, manifesto ok.
  1º check de semântica ③ acusou FAIL — era o CHECK ingênuo (linhas do boot têm μ só no
  objetivo i por construção); refinado → OK nos 3.
- **Prova de não-contaminação**: `c217 → e74 → nsga2 → b3` no MESMO processo (4.15 pré-carregada
  = pior caso): 4 verdes; `which` volta à 4.15 após o e74; `which('CLMEA')` vazio ao fim
  (asserts, não inspeção). Direção inversa provada pelos asserts do ensure_paths_e74 (smoke no
  header do jsonl de cada run).
- **Regressão**: accept_r1_00 (stub) 7/7 + c141/b1/b4/e7/c238/nsga3/moead/smsemoa ×MMF1 verdes
  (1 processo, lotes curtos — lição pisos) + 12 gates accept.py exit 0 + F0-01..04 exit 0 +
  `preflight.py --write` exit 0 (re-hash e74_clmea) + suíte `unittest` 82 OK (1 skip).
  Gates do c262 NÃO rodados (faixa paralela).

## 7. Números p/ o dossiê (semente 0)

| | MMF1 | DTLZ2 | ZDT1 |
|---|---|---|---|
| FE / wall | 61 / 21s | 371 / 261s | 929 / **485s** |
| ciclos · extremos | 15 · 2/2 | 79 · 3/3 | 211 · 2/2 |
| aceites s1·s2·s3 | 8·15·15 | 79·79·79 | 176·211·211 |
| frac_n1 med · count med | 0,53 · 51 | 0,91 · 20 | 0,91 · 7 |
| n_desalinhado med | 7/23 | 8/100 | 9/100 |
| hv_gain>0 | 15/15 | 76/79 | 211/211 |
| guards | 7 cand_vazio | — | 35 dedup_slot_perdido |
| IGD_raw · \|ND\| | — · 14 | 1,1770e-1 · 83 | 9,6400e-2 · 45 |
| ③ linhas · retreinos | 1.950 · 46 | 23.703 · 238 | 63.302 · 634 |

O e74 NÃO é gargalo de wall (ZDT1 8 min vs 3h55 do c238); a curva newrbe (s2, arquivo inteiro)
cresceu 56→851 ms/fit no ZDT1 — gravada na §17.6.

## 8. ⚠ DEFINIÇÕES EM ABERTO — TORRE: levantar com o autor (ping-pong de veto/ratificação)

Nenhuma bloqueou o cartão (todas têm implementação em vigor, escolhida pela leitura mais
conservadora da SPEC e sinalizada); mas são **decisões que o AUTOR precisa ratificar ou vetar**
antes (ou junto) da validação de fidelidade em lote. Em caso de veto, o custo de mudança é
baixo (1 arquivo cada; nenhum re-desenho).

1. **Concretização da âncora `e74-ndsort-obj` (a mais importante).** A âncora descritiva dizia
   `<NDSort sobre objetivos preditos>`; o implementado é **NDSort sobre os objetivos REAIS dos
   pais** (`[y_label,~] = NDSort(y_obj_e74,inf)`, com `y_obj_e74` = 3º output read-only do
   `Data_Process` que preserva o pareamento x_train↔objetivos). Racional: na `ClassifierSelect`
   NÃO existe regressor (só o PNN, que prevê CLASSE — "objetivos preditos" é inimplementável
   literalmente ali); nos pontos do arquivo predito ≡ real (newrbe interpola exato); e a
   alternativa (re-sim do PNN) podia deixar o nível-1 VAZIO → crash novo em `randi`. **Perguntar:
   ratifica a leitura "objetivos reais dos pais"?** (nota também gravada no próprio anchors.json).
2. **Leitura do D74** ("min-max sobre o arquivo corrente"): implementado como **min-max do
   FRONT-1 do arquivo** (Ymin/Ymax das :31-32 stock = ideal/nadir estimados, coerente com o
   enunciado D69), **fixo por chamada** (comparabilidade entre os candidatos j do mesmo ciclo).
   Alternativa rejeitada: min-max do arquivo INTEIRO (máximo de ponto dominado ≠ nadir).
3. **③ do híbrido — `pred_tipo` POR LINHA** (`classe` p/ s1, `valor` p/ s2/s3/boot; a
   estratégia vai no `modelo_flag`): o mock da §17.2 mostra UMA linha `hibrido` com as 2
   cabeças, mas nenhuma linha do e74 REAL tem as duas ao mesmo tempo — fabricar μ p/ a pop do
   s1 exigiria chamada de modelo que o mecanismo não faz. **`pred_tipo=hibrido` NÃO é emitido.**
   Se o autor preferir aderência literal ao mock, decidir COMO preencher a cabeça ausente.
4. **`sigma_0` = pseudo-σ POR ESTRATÉGIA** (s1=dist_dec · s2=HV_gain · s3=Eucli; semântica no
   `sigma_dict` do manifesto, DEF-C4): as "3 colunas de pseudo-σ" da I.8 **não cabem** no schema
   `sigma_0..sigma_{M-1}` quando M=2. O score CalHV absoluto do s2 foi p/ `pred_score`.
5. **Cadência do ②** = a cadência REAL do `NotTerminated` stock (~4 bumps/ciclo: topo + 1 por
   bloco; ZDT1 → 845 "gerações", 521k linhas de ② — ints, comprimem bem). Alternativa (1
   bump/ciclo) exigiria suprimir chamadas do stock.
6. **Fix opcional do desalinhamento máscara×Parent (re-sim do PNN) — NÃO aplicado** (o §22 o
   marca "opcional"; K.5.2 o lista como [IMPL] — precedência §22 vence). Telemetria entregue:
   `n_desalinhado` mediana 7–9%/ciclo; ZDT1 com 35× `dedup_slot_perdido` no s1 (o "no-op
   silencioso" que a v2.2 previu). **Perguntar: mantém sem o fix (só telemetria) ou promove?**
7. **Política dos edges degenerados = SÓ LOGAR** (decidido por mim sob "instrumentar, não
   consertar"): `cand_vazio` (rank-learning sem nível-1 — 7× no MMF1), `hv_range0` (front-1
   degenerado na norm D74 — 0 ocorrências s0; se disparar, os scores viram NaN e o `max` pega o
   1º índice, determinístico). A SPEC chama o RefPoint degenerado de "edge não previsto no
   paper = política nossa" SEM fixar a política — a vigente é "roda e loga". Ratificar.

## 9. Incidentes / notas operacionais

1. **Nenhum crash de MATLAB** nesta sessão (lotes curtos; saída por arquivo).
2. O cwd do shell da sessão resetou 1× entre comandos (accept rodou de `~` e falhou "No such
   file") — refeito com `cd` explícito; nenhum efeito nos artefatos.
3. `pytest` não existe no env-main — a suíte roda por `python -m unittest discover -s tests`
   (82 testes, mesmo número da sessão pisos).
4. A sessão paralela do c262 criou `handoff/R2-c262.md` (untracked) — NÃO tocado, NÃO commitado.
5. Sem edição de SPEC/bundles/params.json; sem INDEX (a torre marca); fidelidade NÃO julgada (D97).
