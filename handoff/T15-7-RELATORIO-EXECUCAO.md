# T15.7 — RELATÓRIO DE EXECUÇÃO (runner do DDMOP7 nas 3 rotas)

> Sessão implementadora, 2026-08-14, sobre HEAD `e6b4e1f` (o cartão citava
> `659e6a8`; o repo avançou — trabalhei sobre o HEAD atual). NADA commitado,
> NADA em stage (regra da sessão sobrepõe o "git add" do cartão §6).
> Testes direcionados: **194 execuções, 0 falhas** (9 skips: 2 declarados
> novos por matlab.engine ausente no env-main + 6 pré-existentes de venv +
> 1 pré-existente). O relatório COMPLETO (decisões [T] no modelo §7 +
> surpresas) foi entregue no retorno da sessão à torre; aqui fica o essencial
> para a próxima sessão.

## O que existe agora

**R2 (c122 c149 c154 c262 e81).** `src/ddmop7_bridge.py` (novo, 629 l) =
transplante da ponte de fusão COM os fixes medidos (init no setup, fatiamento
≤64) + 3 adaptações do cartão: (a) DoE do ARTEFATO parquet (lazy; fallback CSV
com aviso E conferência de hash contra o sidecar — o venv da Engine não tem
pyarrow, medido); (b) pasta do .p por `UA_DD_SAEA_DDMOP_DIR` → default
`~/DDMOP/DDMOP_Exp/Problems` (`resolve_problems_dir`); (c) matlab.engine
tardio. **Contabilidade dupla-modo (D89):** `contabilidade='externa'` (default
do `problems.DDMOP7.bind`) = avaliador CRU `avalia(X)` — sem FE/dedup/catálogo/
hard-stop próprios; ficam SÓ forma/finito (D81) e o teto 600 (`chamadas_p`,
D88.5). `'propria'` = arnês histórico intacto (standalone/smoke).
Fiação: `problema_ligado`/`encerra_problema` (gêmeos em `botorch_harness` e
`standalone_harness`); c262/c154/stubpy criam o problema no run externo e
encerram no `finally` (inclusive falha); c122/c149/e81 ligam no
`_Adapter`/`_Oracle(semente=...)` e encerram no `except` de falha + no
`finally` final. Engine REAL provada 1× nesta sessão (venv env_matlab_engine):
âncoras batidas a ≤1e-12.

**R1 (8 MATLAB online + 4 pisos).** `src/ddmop7_value_local.m` (novo) =
avaliador local do .p (init descartado por processo; guard 600 com controle
negativo; forma/finito; cd-em-volta-da-chamada, pwd do harness preservado;
ações de teste `chamadas|reset|forca_contador`). Em `experiment.m`, os **10
sítios** de evalFcn agora passam pelo ponto único `eval_fcn_por_x(ctx, pp,
problema)` — DDMOP7 desvia ANTES da ponte. ÂNCORAS DE VALOR batidas no .p
real: x=zeros com x(3)=0.5, x(7)=−0.2 ⇒ f=[4/17, 307/690] (cartão §5) e
x=zeros ⇒ [1/17, 307/690] (VEREDICTO; `scratchpad/probe_lote3.log` da torre
não existe mais — segunda âncora substituída pelo dado do VEREDICTO + medição
própria na Engine, declarado).

**§3b (⑤ do MATLAB).** `src/sonda_bloco_declarado.m` (novo) lê
PROBLEMAS_SEM_SONDA + SONDA_AUSENTE_INFO da FONTE ÚNICA `src/experiment.py`
pela ponte py (zero literal duplicado; teste MATLAB confere campo a campo).
`fill_manifest_timing` grava o bloco declarado p/ problema sem sonda (as 3
ausências seguem inconfundíveis; pisos continuam sobrescrevendo com
`nao_se_aplica`); `load_sonda` MATLAB devolve `[]` SEM warning p/ o opt-out
(espelho dos gêmeos Python). Célula R1 real ⇒ auditar VERDE fica p/ o C3.

**Offline (Processo A).** `scripts/gen_dataset_ddmop7.py` (novo): CSV
congelado (sha `03056b6e…` conferido e CRAVADO no script) → 30×526×17 →
avalia na ponte (1 Engine POR SEMENTE; 526<600) → `ds_DDMOP7_{s}.parquet` +
sidecar no contrato D90 (round-trip bit-a-bit; -0 preservado). Consumo provado
pelo `load_dataset`/`load_offline_budget` OFICIAIS (mock, tempdir) — runners
offline sem NENHUMA mudança no CONSUMO. `--limite` exige `--data-root`
explícito e carimba `PARCIAL_LIMITE`; mock carimba `engine='mock'`+AVISO.
Sidecar declara `tier=small/dist=lhs` como SLOT de contrato (os dois
load_dataset o exigem p/ o nome sem sufixo); proveniência real nos campos
`sampler='frozen-ddmop7-init-offline'`+`fonte_csv*` (espelho do DoE online).
⚠ o F que vale é das VMs (D102.14) — rodar LÁ no provisionamento.

## Testes novos (rodar direcionado, nunca a suíte inteira nesta fase)

- `tests/test_t15_ddmop7_bridge.py` — 25 (1 skip declarado: Engine real).
- `tests/test_t15_ddmop7_matlab.py` — 22 (estrutural + VALOR no .p + fonte
  única; guardas: MATLAB ausente e corpus ausente ⇒ skips declarados; use
  `UA_DD_SAEA_DDMOP_DIR` p/ o clone com o .p).
- `tests/test_t15_dataset_ddmop7.py` — 8 (1 skip declarado).
- Regressão dirigida verde: test_d102_sem_sonda · test_t15_sonda_declarada ·
  test_t15_catalogo · test_t15_doe_ddmop7 · test_botorch_harness · test_c262 ·
  test_c154 · test_c122 · test_c149 · test_e81 + célula stub R1 REAL de MMF1
  em tempdir (status ok, FE 61/61, cache-hit, hard-stop, ⑤ com hashes).

## ⚠ SURPRESAS / PENDÊNCIAS DA TORRE

1. ~~⑦ `__final` dos offline quebra no DDMOP7~~ — **RESOLVIDO no T15.7b**
   (decisão da torre, D102.9/"Processo B"): ver a seção T15.7b abaixo.
2. **Provisionamento**: matlab.engine precisa existir no env-main (c122/c149/
   c154/c262) e no env_e81_qpots nas VMs p/ as células online DDMOP7 — no Mac
   NÃO está (medido); e o venv da Engine não tem pyarrow (fallback CSV cobre).
3. ~~gabarito desatualizado~~ — **RESOLVIDO no T15.7b** (torre autorizou a
   edição direta do JSON).
4. Janela residual: em c122/c149/e81 uma falha de validação ENTRE o bind e o
   1º try deixa a Engine aberta até o fim do processo (só erros de config;
   declarado, não corrigido para não reestruturar os runners).

## T15.7b — ⑦ pós-hoc do DDMOP7 offline (D102.9/"Processo B", decisão da torre)

O discriminador canônico é **`experiment.PROBLEMAS_FINAL_POS_HOC`**
(`frozenset({'DDMOP7'})` — "avaliação exige processo externo"; NÃO confundir
com o opt-out da sonda) + a declaração canônica **`FINAL_POS_HOC_INFO`**
(a MESMA gramática `params.nd_final` do e103, com a decisão no lugar do
"DEFINICAO EM ABERTO"). Fiação:

- **Runners offline `b5_prob`/`piso_offline`** (+ `treed_media` por paridade,
  fora do roster DDMOP7): a ⑦ NÃO é avaliada inline quando o problema está no
  conjunto — o run declara no ⑤ (`params.nd_final`) e no ⑥ (footer
  `final_pos_hoc`; `n_final`/`n_nd_pos_real` = NULL declarado). O caminho
  inline dos outros 27 é bit-intocado. `c311` NÃO foi guardado (fora do
  roster DDMOP7, env py3.8 congelado, torre não pediu) — se um dia rodar
  DDMOP7, quebra ALTO no ⑦ (o estado seguro).
- **`scripts/final_eval.py` ramo DDMOP7**: mesma fonte (③, última geração),
  mesmo contrato DI-08, mesmo `write_final`; só o avaliador muda —
  `_avalia_pos_hoc` (motor da ponte `_MotorMatlab`, fatiamento ≤64, guard de
  600 ANTES de abrir a Engine, encerra em finally) em vez de `problems.py`.
  Sem matlab.engine ⇒ RuntimeError ACIONÁVEL (aponta o venv/VM). O sidecar da
  ⑦ ganha a certidão honesta (`avaliador` = "DDMOP7.p ... POS-HOC D102.9";
  `write_final` ganhou o kwarg `avaliador`, default inalterado). O `--check`
  re-avalia pelo MESMO caminho — numa máquina com Engine custa |⑦|×~6 s/célula
  (nota operacional p/ o portão).
- **Gates INALTERADOS**: provado por teste — a célula offline DDMOP7 sem ⑦
  leva do `auditar` EXATAMENTE o achado do e103 ("⑦ __final AUSENTE") e ele
  SOME após o final_eval; `check_final` ausente = mesmo veredito b5m×e103.
- **`gabarito_camadas.json::por_problema.DDMOP7`**: `camada_1_de_onde_vem` e
  `camada_7_final` atualizados (① via FEBudget do harness/ponte crua;
  ⑦ pós-hoc Processo B).
- **Testes**: `tests/test_t15_final_pos_hoc.py` (12: constante; fiação
  estrutural dos 3 runners venv-only + controle do caminho inline; final_eval
  com motor determinístico ⇒ ⑦ no contrato + check verde + idempotência;
  controle negativo f adulterado ⇒ INCONSISTENTE; guard 600 antes do motor;
  erro acionável sem engine; problema normal NÃO passa pelo ramo; veredito
  dos gates idem e103). Blast radius verde: test_r3_final_eval ·
  test_r3_harness · test_piso_off · test_treed_media · test_t12_b5_vetores ·
  test_gates_g6 (161, 13 skips pré-existentes) + todo o conjunto do T15.7
  re-rodado verde (184 py + 22 MATLAB).
- **Operacional**: o fluxo do DDMOP7 offline nas VMs vira o do e103 — rodar a
  célula, depois `final_eval.py --exp off --alg {b5m|b5r|moead_media|e103}
  --problema DDMOP7 --all-seeds` num interpretador com matlab.engine e
  `UA_DD_SAEA_DDMOP_DIR` exportado (1 processo = 1 chamada ≤600 pontos;
  |⑦|~10² por célula cabe com folga).
