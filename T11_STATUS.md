# T11_STATUS — rastreador vivo do refinamento final (atualize a CADA item concluído)

> Regra: ao concluir um item → ☑ + hash do commit + data. Suíte verde antes de cada commit.
> Retomada (qualquer conta): primeiro ☐ de cima para baixo. NUNCA pular a ordem.
> Fonte da verdade do escopo: `SPEC_T11_REFINAMENTO_FINAL.md`.

## FASE G — globais habilitadoras
- [x] G1 · audit_log: anti-append (B-01) + escrita atômica (B-11) + testes — `519b3e4` + `945b6be` (2026-07-29)
      · **suíte 407, 1 falha** — só a ambiental D-03 (some no G6.7)
      · `519b3e4`: B-01 (`RunJaFechado` + `footer_fechado()`) e B-11 no lado Python (1 linha =
        1 `os.write` sob O_APPEND; > `select.PIPE_BUF` sob `flock`) + 11 testes
      · `945b6be` (autorizado pelo autor): B-11 no writer MATLAB (`experiment.m:jsonl_open` trunca
        1× e reabre em `'a'` — vale p/ os 13 configs MATLAB) + **B-13(a)** teste→tempdir
        (a guarda `tearDownModule` = B-13(b) segue no G6) + 2 testes de paridade do `.m`
      · ⚠ ERRATA ao PLANO F5/B-11 (2 claims não confirmadas pelo dado, anotadas no código):
        o splice do `main/b1/WFG1` NÃO está nas linhas de header/sigma_dict (header = 512 B; as 49
        malformadas são `b1_gen`/`sonda`, mediana 1.647 B) · não existe "2º handle" em
        `src/b1_instrument.m` (só `experiment.m` tem `fopen`, 1 fid por run)
      · ⚠ PENDENTE PARA O AUTOR: smoke MATLAB de 1 célula (o engine não importa no venv da suíte)
- [x] G2 · despachante: no-op sem ⑥ (B-02) · NO_RETRY (B-16) · q real no ⑤ de aborto (I-10) · revogação DI-40 no dispatch — `65c835f` (2026-07-29)
      · suíte 421, 1 falha (a ambiental D-03) · 14 testes novos em `tests/test_despachante.py`
      · B-02 fecha 2 buracos: o skip não abre o ⑥ **e** o despachante passa a abrir com
        `append=False` (sem isso a guarda B-01 mataria o resume de toda célula `failed`)
      · I-10 foi além do `q`: o ⑤ do aborto também herda `tier`/`dist` (de `naming.parse_sweep`)
        e `regime` — mesma classe de defeito, ⑤ de sweep abortado não dizia o tier
      · DI-40: **verificado** que não há filtro de dispatch (e2e travando o despacho de
        `batch/c154`). ⚠ O único filtro DI-40 vivo está em `scripts/tabela42.py:37` (UNTRACKED,
        driver do autor) e ele está CORRETO para o censo da s42 (as 5 células nunca foram
        despachadas então) — precisa virar CONDICIONAL por semente quando o B-12/G6 commitar
        os drivers, senão o M8 reporta 690 em vez de 695 células
- [x] G3 · manifest: campanha_id + is_run_done v2 (B-03) · higiene do --force (OP-6) · fallback-footer (O-21) — `4253fa4` (2026-07-29)
      · suíte 439, 1 falha (a ambiental D-03) · 18 testes novos em `tests/test_campanha.py`
      · **AÇÃO DO AUTOR NO DISPARO:** `export UA_DD_SAEA_CAMPANHA_ID="$(git rev-parse --short=12 HEAD)_<data>"`
        nos 4 drivers de máquina. Sem a env, o default `{commit12}_{data UTC}` MUDA à meia-noite
        e o resume re-roda tudo. O despachante imprime o id em uso no arranque do grid
      · os dois stacks derivam o id pela MESMA fórmula e da MESMA env (`experiment.m` também)
      · sentinela `QUALQUER_CAMPANHA` para auditar o passado (o re-gate das 666 lê ⑤ v1)
      · CONTRATO_DE_DADOS §5 atualizado (schema v2)
- [x] G4 · gcs/harnesses: mirror no aborto (B-09) · identidade do blob + poda segura (B-10) — `73f5a18` (2026-07-29)
      · suíte 454, 1 falha (a ambiental D-03) · 15 testes novos em `tests/test_espelho.py`
        (cliente GCS FALSO, sem rede — o 412 e o md5 corrompido são simulados)
      · B-10 = **if-generation-match**, NÃO o prefixo `campanha_id/host`: o prefixo mudaria
        `naming.blob_path` e com ele o layout do bucket da s42, o resume bucket-aware, o censo,
        o `coletar42.sh` e o layout de análise — raio largo para o mesmo efeito
      · poda da ③ agora exige md5 do blob == md5 local; colisão ⇒ `colidiu_412` e local PRESERVADO
      · ⚠ o smoke REAL de rede (412 de verdade) só roda na VM — fica para o autor
- [x] G5 · truncamento-com-dado (elapsed-only; projeção=warning) + CHECKPOINT atômico periódico + kill-test — `936a687` (2026-07-29)
      · suíte 473, 1 falha (a ambiental D-03) · 19 testes novos em `tests/test_checkpoint.py`
      · bit-identidade PROVADA (①②③ byte-idênticas com/sem checkpoint; ④ estrutural, regra do
        molde `scripts/regressao_q1.py:69`) · kill-test com SIGKILL real ✓ · retomada não duplica ✓
      · checkpoint em 8 runners (c262 c154 c122 c149 e81 c311 treed_media sobol_batch);
        **b5r/b5m/moead_media FORA por desenho** — a ③ deles nasce no replay pós-laço, um
        checkpoint no meio gravaria ③ vazia; eles já truncam com dado via `teto_s` (DI-35.5)
      · ⚠ CONTRATO NOVO (achado do kill-test): em ⑤ `checkpoint_em_andamento`, `fe_final` é
        **PISO** das camadas (o ⑤ é o último dos 5 arquivos; um kill pode deixar as camadas 1
        checkpoint à frente). O ⑤ nunca promete dado que as camadas não têm — a direção é a
        garantia. Consumidores do censo/gates precisam saber disso
      · `tests/test_di09_r2.py::test_a_projecao_original_segue_funcionando` MUDOU de contrato
        junto com a DI-43 (era `assertTrue(over)` na projeção) → `..._segue_sendo_CALCULADA`
      · ⚠ FALTA (fase A): validar numa célula D≥12 real do c154 que ela morre às 12 h COM
        camadas parciais (A1) e o probe de RAM do c262-batch (A4) — precisam de máquina
- [~] G6 · gates G-1..G-9 + motivos_parada.json + mapa_termino.json + gabarito_camadas.json + B-12/13/14/15 + suíte hermética (D-03) — `f5b172c` + `789900e` (2026-07-29)
      · **suíte 516 testes, 0 FALHAS** (a ambiental D-03 morreu no G6.7) · +43 testes novos
      · FEITO: 3 artefatos (`motivos_parada` B-06 · `mapa_termino` I-08 · `gabarito_camadas` G-4)
        · `envs.json` +`venvs_aceitos` (o roster que o G-3 exigia e não existia)
        · `scripts/gates_proveniencia.py` = G-1 3×1 (porte do f5) · G-2 ⑥ · G-3 · G-4 · B-15
        · ligado no `portao.py` (com marca ⚠ p/ INCONCLUSIVO — nunca verde, lição do B-07)
        · B-06 fonte única nos 3 sítios (portao/accept/censo42) · **B-12** (9 drivers no git +
          preflight anti-forasteiro) · **B-13(b)/G-8** (guarda de suíte) · **B-14/G-5** (rtol 1e-4)
        · **G6.7** suíte hermética (D-03 com lib/rede simuladas + o caminho blob-presente)
      · **G-7 FEITO** (`5b6df3e`): `artifacts/contrato_61.json` (extração + CURAÇÃO contra a
        medição — 3 falsos-positivos removidos: `n_baseline` do e81 que o §6.1 cita para NEGAR,
        `solution_id` do b4 que é `ref_ids`, `tempo_fit_s` dos pisos que é NULL por contrato) +
        `gate_contrato_61` no portão. Reproduz I-03/I-05/I-07 e acha **5 pendências SEM ITEM NO
        T11** (`adapt_delta_V` b3 · `mll_final` c262 · `loss_treino` e7 · `margem_3sigma` e103 ·
        `sigma_dict` ausente no ⑤ dos 4 pisos online, 112 células) → **decisão do autor**
      · **G-9 FEITO** (`15586b0`): `scripts/content_hash.py` + a mescla do `tabela42.py` deixou
        de decidir por tamanho+mtime±2s (heurística que apagava o destino em silêncio) e agora
        registra `DIVERGENCIAS_CONTEUDO.csv`. Só paga md5 quando precisa
      · **G-6 CÓDIGO FEITO** (`398d253`): flag `sonda_on` UNIFORME nos 5 runners que não a tinham
        (c122 c149 e81 c154 c262), em TODOS os sítios de emissão (cadência + os 2 ramos de
        hard-stop dos BoTorch + a emissão final fora do laço) e atravessando o wrapper→inner;
        `naoperturbacao.py --par` roda a célula 2× em tempdir e compara a ① bit-a-bit.
        **PROVA COLHIDA: c122/MMF1/s0 ⇒ ① BIT-IDÊNTICA** (sha256 be06b54124e9c100, 91 s o par)
      · **G-6 · 9 de 11 PARES PROVADOS** (① BIT-IDÊNTICA com e sem sonda, MMF1/s0):
        c122 `be06b541` · c149 `38b5584b` · e81 `b9525753` · c262 `75c52d8b` · c154 `eadf899d` ·
        moead_media `8e690c81` · b5r `c02703c2` · treed_media `9c06dd44` · c311 `9e605 2bc`
        (o moead_media rodou em py3.7 via `run_in_venv` — prova de brinde que a flag atravessa
        o transporte de venv). **b5m rodando · e103 falta o gêmeo da flag no `experiment.m`**
      · 🔴 O par PEGOU um bug do meu próprio patch: c154/c262 estouravam `NameError` porque a
        flag parava no wrapper e os sítios de emissão vivem no `_run_*_body` — e o teste por
        GREP passou verde. Trocado por checagem de ESCOPO via AST (`4ef4d47`), com controle
        provando que o grep antigo dizia PASSA no código quebrado
      · verificado que os 8 módulos que toquei importam em **py3.7 (env_b5)** e **py3.8
        (env_c311)** — sem isso c311/b5/treed_media/moead_media quebrariam no DISPARO
      · ⚠ AÇÃO DO AUTOR: o preflight agora acusa **58 manifestos de OUTRA MÁQUINA** em
        `data/experiments` (as células que voltaram das VMs por rsync). Já estão no bucket e em
        `resultados_experimentos` — o disco local tem de partir limpo antes do disparo
- [x] G7 · cronômetro tempo_aval (I-02) + export NULL + repo_hash no ⑤ (I-09) — `83dbdac` (2026-07-29)
      · **suíte 532 testes, 0 falhas** · 16 testes novos em `tests/test_g7_instrumentacao.py`
      · cronômetro no `budget.py:evaluate` (o portão ÚNICO) — cache-hit e hard-stop NÃO contam
      · `tempo_aval_real_s` pode ser **NULL** ("não medi" ≠ "custou zero"): os 4 runners offline
        + o stub deixaram de gravar `0.0`, e o sobol_batch passa o valor MEDIDO
      · `repo_hash` nasce preenchido nos DOIS writers (Python e MATLAB) — era `''` em 666/666
      · ⇒ o gate **G-3 em modo `campanha` fecha VERDE** num ⑤ novo (fio completo travado por teste)
      · ⚠ NÃO mexi nas 5 medições manuais que já funcionam (`adapter/oracle.tempo_aval_real_s`
        em c122/c149/c154/c262/e81) — o laudo I-3 as chama de "opcional: enxugar"; tocar código
        de medição validado por ganho estético não vale o risco
- [~] 🏁 MARCO G · re-gate das 666 ⇒ exatamente 1 quimera + 34 anômalas → **ONDA-0 LIBERADA: c149 · e81 · e7 · c238 · b3 · c141 · b1 · nsga2 · nsga3 · moead · smsemoa · treed_media**
      · **RE-GATE RODADO (2026-07-29)** sobre as 666 células oficiais de
        `~/Documents/python_repos/mestrado/resultados_experimentos`:
        - **G-1 3×1: 360 aplicáveis · 359 OK · 1 falha** — IDÊNTICO ao placar da F5
        - **a quimera:** `c149/q10_ZDT4`, 0/2000 bit-idênticos, `max|ΔX| = 9,99983` (a F5 mediu
          9,999830) — reproduzida ao dígito
        - **G-2: os 11 que o plano manda acusar** (9 sem footer + 1 com 3 + 1 com 95 pares)
          **+ 4 e103 com linha malformada** = 15 células
        - **B-15: 21 footer-faltante** (12 com 1 footer + 9 com zero) reclassificadas —
          é exatamente o número que o B-15 mede
      · ⚠ **DECISÃO PENDENTE DO AUTOR (D81):** o critério "1 quimera + **34** anômalas" NÃO é
        reproduzível como escrito, e a razão é uma tensão DENTRO do plano: as 21 células
        "footer faltante" que compõem a maior parte das 34 são justamente as que o **B-15 manda
        NÃO acusar** (~270 falsos alarmes/campanha) e que o §4-item-9 declara "aprovadas
        cientificamente, reprovadas no contrato §6". Aritmética medida nas 666: 12 (1 footer onde
        o despachante daria 2) + 9 (zero footer) + 6 (linha malformada) + 1 (95 headers) + 1
        (footer a mais) = **27 células distintas** (2 caem em 2 famílias). **Nenhuma família de
        anomalia ficou sem detecção** — a diferença é contabilidade, não cobertura.
        **Placar proposto:** 1 quimera + **15 anômalas** + 21 `footer_faltante` contadas e não
        vermelhas. Aguarda ratificação
      · ⚠ FALTA p/ liberar a Onda-0: preflight 0 (as 58 forasteiras acima) + G7 (o `repo_hash`
        do G-3 em modo campanha) + smoke 24/24

## FASE A — por algoritmo (cada ☑ = DEFINITIVO ✅ = autor pode disparar em escala)
- [~] A1 · c154 (herda G5; validar teto D≥12 com camadas; params ⑤; doc I-12) — `7cad932` (2026-07-30)
      · **FEITO:** `params` no ⑤ (I-07) via `_params_efetivos` (fonte única header⑥/⑤) ·
        regra I-12 da ordem da ③ no CONTRATO + no `sigma_dict` dos 2 gêmeos + utilitário
        `botorch_harness.restart_de_linha` · `env.executable` no ⑤ do stack BoTorch (achado do G-3)
      · **I-12 VERIFICADO NO DADO:** 1.200 blocos de c154+c262 na s42 ⇒ vencedor na ÚLTIMA
        linha em 1.200 (100,0%)
      · **SMOKE de célula REAL** (c154/MMF1/s0): ⑤ completo (params+campanha_id+repo_hash+
        checkpoint+tempo_aval MEDIDO), fe_final==maxfe==61, gates G-1..G-4/B-15 VERDES em modo
        CAMPANHA (G-1 3×1 = 40/40 bit-idênticos)
      · ⚠ **FALTA p/ o carimbo:** (a) G-7 acusa `mll_final`/`n_baseline` ausentes no ⑥ — 2 das
        5 pendências "SEM ITEM NO T11" (o `n_baseline` pode ser NÃO-APLICÁVEL aqui como no e81:
        qLBMOJES não tem prune de baseline; decidir sozinho seria escolher semântica de
        contrato — **D81, decisão do autor**); (b) validar célula D≥12 morrendo às 12 h COM
        camadas parciais (precisa de máquina)
- [x] A2 · c122 — `73d9fef` (2026-07-30) · **SMOKE: n_ref=21 (=11D−1) no g=1 × 11 (=MU) no g≥2**
      — o teste de aceitação do I-01. ref_ids (21/11 ids) · y_treino_dist (462/484 pares) ·
      REGRA_DO_ROTULO no sigma_dict · params já existia
- [~] A3 · família b5 — `b74c620` + `08a4019` (2026-07-30)
      · I-05: acumulador P_wrong no VENDORIZADO (âncora `b5-pwrong-stats` + re-lacre) +
        `p_wrong_stats`/`n_substituicoes`/`flag_vetores_degenerados` no ⑥
      · `params` no ⑤ dos 3 · granularidade_③ no sigma_dict dos 3 (I-04)
      · ⏳ FALTA: a prova ①③⑦ byte-idênticas com×sem o patch (rodando; o b5m leva ~22 min/run)
- [x] A4 · c262 — `52befff` (2026-07-30) · `ACQF_HP` (os 8+2 do T1) como fonte única do
      `_make_acqf`/header/⑤ · `params` no ⑤ · `fit_retries>0` vira guard amarelo
      · ⚠ FALTA (máquina): o PROBE DE RAM do batch → `--n-jobs` no RUNBOOK
- [x] A5 · e103 — `5aa31e3` (2026-07-30) · `tempo_geracao_s` na ④ (era o único config sem)
      · ⚠ FALTA (máquina): validar o rito da ⑦ numa célula
- [x] A6 · sobol_batch + nsga3 — `40df11a` (2026-07-30) · `minimo_comum_di10` no sobol_batch
      (n_front1=8 no smoke; tempo_fit NULL) · a string do piso reescrita CONTRA O DADO: a
      fórmula do plano acerta **0/112**, a antiga 2/112, `floor(...)` 103/112 ⇒ declarado
      EMERGENTE ("não derive, LEIA")
- [x] A7 · b4 — `52befff` (2026-07-30) · REGRA_DO_ROTULO + glossário p0/p1 no sigma_dict
      (trocá-los derruba a reprodução de 6.268/6.268 para 1.252/6.268) · `y_treino_dist`
      DERIVADO de `rr`×`n_treino`, sem tocar o vendorizado
- [~] A8 · e74 — **FIX DI-45 APLICADO** `b74c620` (2026-07-30) · `S=find(y_label==1)` +
      índice absoluto · `n_desalinhado` PRESERVADO (é a prova na semente 1) · âncora
      `e74-classifierselect-idx` + `repos.lock` re-lacrado · preflight: APLICADO
      · ⚠ FALTA (máquina): smoke de 3 células + gate ±3σ · regra-rótulo/y_treino_dist do e74
- [x] A9 · c217 — `52befff` (2026-07-30) · `pmid_ids` (era 0/25 células com a identidade) +
      `y_treino_dist` ternário · ⚠ params ⑤ do c217 ainda pendente (writer MATLAB)
- [x] A10 · c311/treed_media — `5aa31e3` (2026-07-30) · guard de tier ANTES do import do
      vendor (verificado: off/main/sweep-small BARRADOS, big passa) · aviso
      `n_sigma_valido` no sigma_dict do c311 (σ-NaN mediano 90,3% no big)
- [~] A11 · sonda estratificada — `b74c620` (2026-07-30) · mecanismo no harness
      (`emit_sonda_estratificada`/`amostra_estratificada`, RNG local uso_id=91, sob
      `preserve_all_rng`) + ligado no **c122**
      · **PREVALÊNCIA 7,4% no bloco contra 0,4% da régua = 18× mais positivos**
      · regimes separados na ③: 44.000 sonda · 10.500 estratificada · 3.632 busca
      · ⚠ FALTA: os 3 classificadores MATLAB (b4, c217, e74) — gêmeo MATLAB do mecanismo

## FASE V — verificações & re-runs
- [x] V1 · VD b1-torneio + VD b3-índice — `ca157d8` (2026-07-30) ·
      `handoff/T11-V1-verificacoes-dirigidas.md`
      · **VD-b1 🔴 CONFIRMADO:** o torneio ranqueia pelo PCheby do SUBCONJUNTO e indexa o
        `Dec` INTEIRO — **93,0% de 8.443 gerações**, mediana **44,9%** da população
        inalcançável, 25/28 células. MESMA CLASSE do DI-45 ⇒ **decisão de fidelidade do autor**
      · **VD-b3 🔴 estrutural:** `Next` mistura domínios de índice no ramo 1; `nzero=0` em
        1.619/1.619 não discrimina o ramo ⇒ instrumentar `size(Via,1)`/`NI−mu` (~2 linhas)
- [ ] V2 · re-runs s42: c311/big-mvns + b1/WFG1 · quimera c149 (rota A0→Mac) · ⑦ e103→bucket · ~29 não-ok no regime novo
- [~] V3 · lote de docs — `66195cf` (2026-07-30) · **PARTE A36** no REGISTRO (execução do T11 +
      as 8 ERRATAS + os 6 contratos novos) · nº da DI-40 corrigido nos 2 pontos (1,47 h medido) ·
      RUNBOOK: rito NOVO do teto (truncamento-com-dado) + seção do `campanha_id` + números
      · ⚠ FALTA: cards/INDEX · SPEC L.8 do e74 pós-fix · D7/iteration_seed na SPEC §D62 (a SPEC
        é TERRITÓRIO DA TORRE — RI-12 — então deixei para o autor)

## ACEITAÇÃO FINAL
- [ ] Suíte ≥410, 0 falhas · preflight 0 · re-gate 666 = 1+34 · smoke 24/24 · kill-test ✓ · handoffs escritos
- [ ] AUTOR: tag `t11-definitivo` + push · fila de infra D10 (envs Linux · lib gcs env_c311 · pins · datasets 29 sementes · SUB-varN) · DISPARO
