# CARTÃO T15.7 — O RUNNER DO DDMOP7 NAS 3 ROTAS (torre, 2026-08-13)

> **Missão:** fazer o DDMOP7 (problema 26, avaliado no `DDMOP7.p` MATLAB — exceção
> declarada à A2, D102.5) rodar nas três rotas do pipeline SEM criar um harness
> paralelo: o FEBudget/export/gates EXISTENTES são a autoridade; o `.p` entra só
> como avaliador cru. Pré-requisitos JÁ NO LUGAR: catálogo (T15.2, `207692f`),
> DoE congelado em parquet (T15.4, `data/doe/DDMOP7/`, 30 sementes), opt-out de
> sonda (T15.1/T15.3), grid 22.740 (T15.6), régua fase-1 (REAL-2.15).
> **Doutrina:** controle negativo p/ todo fix; asserção de VALOR; mudar o mínimo;
> suíte com o venv `mestrado_experimentos_dissertacao`; NUNCA push; tempdir em
> testes; D81 em ambiguidade. NUNCA rode células DDMOP7 completas na suíte
> (526×6s cada) — smokes reais são o C3, fora da suíte.

## §0 · Fatos MEDIDOS que governam o desenho (2026-08-13, B-26/B-27)

1. O `.p` EXIGE `DDMOP7('init')` UMA vez por processo antes de `'value'`
   (estado persistente; a frio morre em assert). O sorteio devolvido é
   DESCARTADO — não é FE, não é dado, não toca o contador interno de 600.
2. `'value'` é função pura; LOTE pós-init é ponto-a-ponto idêntico às chamadas
   individuais. Custo ≈ **6 s/avaliação** (Mac arm64 E VMs — mesmo número).
3. Teto interno: **600 chamadas de 'value' por processo** (526 + fantasmas cabe).
4. Chamadas em lote pela MATLAB Engine: fatiar em ≤64 pontos/chamada (watchdog
   900 s por chamada; ver `MAX_PONTOS_POR_CHAMADA` na ponte).
5. Zeros NEGATIVOS existem no DoE congelado — bit patterns preservados nos
   parquets; qualquer conversão tem de manter float64 bit-a-bit (D63).

## §1 · ROTA R2 — algoritmos Python (c122 c149 c154 c262 e81) × DDMOP7

1. **Transplantar** `mestrado2/_real_experiments/ddmop7_bridge.py` → `src/ddmop7_bridge.py`
   (a versão de lá JÁ TEM os fixes medidos: init no setup do motor + fatiamento).
   Adaptações: (a) o DoE vem do ARTEFATO parquet via `load_doe` (D63 — mesmo
   arquivo das outras rotas; a rota por CSV vira fallback com aviso);
   (b) `problems_dir` resolve por `UA_DD_SAEA_DDMOP_DIR` (env) → default
   `~/DDMOP/DDMOP_Exp/Problems`; (c) import de matlab.engine permanece TARDIO.
2. A casca `problems.DDMOP7` já delega à ponte via `bind(semente)`. O ponto de
   ligação: nos runners Python o `_instantiate_problem('DDMOP7')` devolve a
   casca DESLIGADA — o runner que conhece a semente faz `prob.bind(semente)`
   (procure onde cada um instancia o problema; `BoTorchProblemAdapter` em
   `botorch_harness.py:555` e os standalone). Sem bind ⇒ RuntimeError D81 (bom).
3. **Contagem de FE**: D102.5 manda o contador morar no lado MATLAB só na rota
   R1 (onde não há ponte). Na R2 os harnesses Python JÁ têm FEBudget — a ponte
   NÃO pode contar em paralelo: use a ponte como avaliador cru (`avalia(X)`)
   sob o FEBudget do harness, e DESLIGUE a contabilidade própria dela nesse
   caminho (deixe-a para o modo standalone/smoke). Um contador só (D89).
4. `encerra()` (fecha a Engine, D86) precisa rodar no fim do run — inclusive
   em falha (finally). 1 Engine por run (D88.5).

## §2 · ROTA R1 — algoritmos MATLAB × DDMOP7 (a maior)

1. Em `src/experiment.m`, o problema chega por `py_problem(ctx, problema)` e o
   `evalFcn` da ponte Python (linhas ~151/421/662/…). Para `problema=='DDMOP7'`:
   **desviar ANTES da ponte** — não há Python nenhum na avaliação (caso 3 da
   D102.5): `evalRaw = @(x) ddmop7_value_local(x)` onde a função local faz
   (uma vez por processo): resolve a pasta do `.p` (`getenv('UA_DD_SAEA_DDMOP_DIR')`,
   default `~/DDMOP/DDMOP_Exp/Problems`; recusar `DDMOP_Plat`), `addpath`+`cd`,
   `clear DDMOP7`, `descarte = DDMOP7('init')` (§0.1), e depois só
   `DDMOP7('value', x)` com os guards de forma/finito (molde:
   `mestrado2/_real_experiments/matlab/DDMOP7_evalFcn.m::chamaPCode`, SEM o
   contador próprio — o FEBudget MATLAB é a autoridade, D89).
2. DoE: `load_doe('DDMOP7', semente)` já funciona (parquet padrão; bounds ±1
   no sidecar). `n_init = 11*17-1 = 186` — os asserts por-runner existentes
   (`n_init == 11*D-1`) valem sem mudança.
3. bounds/M/D vêm de `py_problem` normalmente? NÃO — py_problem instancia a
   casca via ponte py. e lê n_var/n_obj/xl/xu — isso FUNCIONA (a casca é
   barata, não abre MATLAB). Só a AVALIAÇÃO desvia. Confirme que nenhum runner
   MATLAB chama `evaluate_problem` para DDMOP7 fora do evalFcn injetado.
4. O teto de 600 do `.p`: com FEBudget cortando em 526 + fantasmas do
   construtor (DEF-A3, cache-hit do initFcn), sobra folga. Adicione um guard
   simples (contador local `chamadasP`) que PARE com erro claro se passar de
   600 — não confie, cheque (doutrina D88.5).
5. Roster R1×DDMOP7 = os 8 MATLAB online (b1 b3 b4 c141 c217 c238 e7 e74) +
   4 pisos (nsga2 nsga3 moead smsemoa). e103 é offline (§3). Nada muda nos
   .m dos algoritmos (vendorizados!) — só no harness `experiment.m`.

## §3 · ROTA OFFLINE — b5m b5r moead_media e103 × DDMOP7 (via Processo A)

1. Os runners offline consomem `data/datasets/DDMOP7/ds_DDMOP7_{s}.parquet`
   (X+F, contrato D90) — se o artefato existir, ZERO mudança nos runners.
2. **Processo A** (novo script `scripts/gen_dataset_ddmop7.py`): para cada
   semente, lê o X congelado (`data/real_sources/ddmop7/dataset_ddmop7_offline_30sementes.csv`,
   30×526×17, sha `03056b6e…`), avalia os 526 na MATLAB Engine (via
   `src/ddmop7_bridge` fatiado, ~53 min/semente) e grava
   `ds_DDMOP7_{s}.parquet` + sidecar no MESMO contrato do `src/doe.py`
   (colunas x0..x16,f0,f1; x_hash/f_hash/dataset_hash; round-trip bit-a-bit).
   ⚠ Os F que valem são os das VMs Linux (D102.14) — o script roda LÁ no
   provisionamento; aqui só se TESTA com --limite (poucos pontos) em tempdir.
3. e103 (worker MATLAB offline): confirme como ele carrega dataset
   (`experiment.m::load_dataset`) — artefato padrão ⇒ sem mudança.

## §3b · ⑤ DO MATLAB — status declarado (achado do T15.3, OBRIGATÓRIO)

O `experiment.m::build_manifest` grava `man.sonda.status='artefato_ausente'`
quando não há sonda (:3317-3322) — mas o auditar (T15.3) exige
`'sem_sonda_por_problema'` para problemas em PROBLEMAS_SEM_SONDA. Na rota R1
do DDMOP7: quando `problema=='DDMOP7'`, o ⑤ deve gravar o bloco DECLARADO
(mesmos campos do `SONDA_AUSENTE_INFO` de `src/experiment.py`) em vez do
`artefato_ausente`. Controle negativo: ⑤ sintético com `artefato_ausente`
p/ DDMOP7 ⇒ auditar REPROVA (já coberto em test_t15_sonda_declarada); célula
R1 real do smoke C3 ⇒ auditar VERDE.

## §4 · GABARITO E GATES

- `gabarito_camadas.json` já tem `por_problema.DDMOP7` (T15.6): ① via MATLAB,
  SEM regime sonda na ③. Confirme que os gates leem isso (T15.3 fez os ramos
  de sonda; aqui só conferir que a rota R1 grava as 4 saídas padrão).
- `accept.py`/`auditar.py`: DDMOP7 é online nos 12+pisos ⇒ os checks genéricos
  (FE=526 exato, CP-init hash vs sidecar, 4 saídas) valem SEM mudança.

## §5 · TESTES (unitários; o smoke real é o C3, fora da suíte)

- R1: teste MATLAB (padrão `tests.TIMEOUT_MATLAB`, guarda de corpus dos T14)
  que chama a função local `ddmop7_value_local` com 2 pontos conhecidos do
  probe (âncoras de VALOR: x com f=[4/17, 307/690] — ver
  `scratchpad/probe_lote3.log` da torre: x1=zeros com x1(3)=0.5,x1(7)=-0.2)
  e confere bit/tolerância + o guard de 600 (controle negativo: forçar
  contador>600 ⇒ erro claro). Se MATLAB indisponível ⇒ skip declarado.
- R2: mock da Engine (a ponte tem engine='mock') p/ o caminho bind/avalia/
  encerra + teste de que o FEBudget é o único contador.
- Processo A: tempdir com --limite 4 + mock/skip se sem MATLAB; round-trip.

## §6 · DEFINIÇÃO DE PRONTO

Suíte ≥875 + novos, 0 falhas · nenhuma célula real rodada pela suíte ·
`git add` explícito, SEM commit (a torre revisa/commita) · relato [T] por
decisão no retorno (modelo DECISOES_PARA_A_TORRE §7) · surpresas declaradas.
