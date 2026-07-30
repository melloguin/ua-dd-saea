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
      · ⚠ **FALTA no G6** (próxima sessão): **G-6** não-perturbação por par de runs (flag
        `--sem-sonda`; precisa RODAR 21 pares) · **G-7** contrato §6.1 aferido por teste (exige
        a tabela §6.1 em artefato machine-readable) · **G-9** content-hash na propagação
        (rito F4/`coletar42.sh`)
      · ⚠ AÇÃO DO AUTOR: o preflight agora acusa **58 manifestos de OUTRA MÁQUINA** em
        `data/experiments` (as células que voltaram das VMs por rsync). Já estão no bucket e em
        `resultados_experimentos` — o disco local tem de partir limpo antes do disparo
- [ ] G7 · cronômetro tempo_aval (I-02) + export NULL + repo_hash no ⑤ (I-09)
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
- [ ] A1 · c154 (herda G5; validar teto D≥12 com camadas; params ⑤; doc I-12)
- [ ] A2 · c122 (n_ref real g=1 · ref_ids · regra-rótulo · y_treino_dist · params ⑤)
- [ ] A3 · família b5: b5m/b5r/moead_media (I-05 campos DI-10 · wrapper A8 read-only · params ⑤ · granularidade ③)
- [ ] A4 · c262 (herda G5; 8 hp da acqf; params ⑤; fit_retries warning; PROBE DE RAM do batch → --n-jobs no RUNBOOK)
- [ ] A5 · e103 (tempo_geracao_s; validar rito da ⑦)
- [ ] A6 · sobol_batch (n_front1/f_best; tempo_fit NULL) + nsga3 (string geracoes_derivadas)
- [ ] A7 · b4 (regra-rótulo; y_treino_dist; NUNCA inverter p0/p1)
- [ ] A8 · e74 — FIX DI-45 (ClassifierSelect:46-48; n_desalinhado preservado; re-lacre âncora/repos.lock; smoke ±3σ) + regra-rótulo + y_treino_dist
- [ ] A9 · c217 (pmid_ids; regra-rótulo; y_treino_dist; params ⑤)
- [ ] A10 · c311/treed_media (nota n_sigma_valido; guard de tier)
- [ ] A11 · sonda estratificada dos 4 classificadores (por último; G-6 obrigatório)

## FASE V — verificações & re-runs
- [ ] V1 · VD b1-torneio + VD b3-índice (forense read-only; 🔴 ⇒ D81)
- [ ] V2 · re-runs s42: c311/big-mvns + b1/WFG1 · quimera c149 (rota A0→Mac) · ⑦ e103→bucket · ~29 não-ok no regime novo
- [ ] V3 · lote de docs (T11-PLANO §6+§12-📄: ERRATA A30 · nº DI-40 · 6 números F5 · cards/INDEX · RUNBOOK · OP-1..7 · SPEC L.8 e74 · D62/iteration_seed · textos de teto)

## ACEITAÇÃO FINAL
- [ ] Suíte ≥410, 0 falhas · preflight 0 · re-gate 666 = 1+34 · smoke 24/24 · kill-test ✓ · handoffs escritos
- [ ] AUTOR: tag `t11-definitivo` + push · fila de infra D10 (envs Linux · lib gcs env_c311 · pins · datasets 29 sementes · SUB-varN) · DISPARO
