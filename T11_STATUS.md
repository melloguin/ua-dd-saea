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
- [ ] G4 · gcs/harnesses: mirror no aborto (B-09) · identidade do blob + poda segura (B-10)
- [ ] G5 · truncamento-com-dado (elapsed-only; projeção=warning) + CHECKPOINT atômico periódico + kill-test
- [ ] G6 · gates G-1..G-9 + motivos_parada.json + mapa_termino.json + gabarito_camadas.json + B-12/13/14/15 + suíte hermética (D-03)
- [ ] G7 · cronômetro tempo_aval (I-02) + export NULL + repo_hash no ⑤ (I-09)
- [ ] 🏁 MARCO G · re-gate das 666 ⇒ exatamente 1 quimera + 34 anômalas → **ONDA-0 LIBERADA: c149 · e81 · e7 · c238 · b3 · c141 · b1 · nsga2 · nsga3 · moead · smsemoa · treed_media**

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
