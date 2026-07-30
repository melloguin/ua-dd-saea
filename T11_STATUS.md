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
      · ✅ **G-6 · 10 de 11 PARES PYTHON PROVADOS** — o b5m fechou em 2026-07-30:
        `① BIT-IDÊNTICA com e sem sonda (sha256 bcda99b31dfb2c35)`. O hash bate com o ① da
        prova I-05 rodada em worktree separado — cruzamento independente
      · ✅ **GÊMEO MATLAB DA FLAG** (`4126b78`): `UA_DD_SAEA_SONDA_OFF` lido no construtor do
        `SondaState`, que se DESARMA. O gate sai de **10 para 19 configs**. DESARMAR e não
        SUMIR porque `build_manifest` lê `snd.n_blocos` direto e `[].n_blocos` é erro — com o
        objeto vivo o manifesto declara `desligada=true` e a sonda nunca some calada.
        Os **4** caminhos até o `fire` têm guard (`due`, `probeOffline`, `finalProbe`,
        `probeEstratificada`) — só a cadência deixaria o bloco final e o offline dispararem
      · ✅ **G-6 FECHADO — 19 de 19 configs com sonda, BIT-IDÊNTICOS** (2026-07-30, runs
        reais do autor). 10 Python + **9 MATLAB** (b1 `4d81d858` · b3 `760941d2` · b4
        `2404320f` · c141 `d7f20cd0` · c217 `868a15c0` · c238 `43f53326` · e7 `1e1060ee` ·
        e74 `fc9ced7a` · **e103 `a94d2766`**). Os 5 pisos sem surrogate são não-aplicáveis.
        **0 perturbaram · 0 falharam.**
      · O desarme foi CONFIRMADO por 3 sinais independentes em cada par, não só pelo hash:
        `sonda.desligada=true` no ⑤ · `n_blocos` caindo a 0 · a ③ ENCOLHENDO (e74:
        46.499→1.999 linhas; e103: 59.800→19.800). Se só o hash batesse, um desarme que
        nunca disparou daria o mesmo resultado — os 3 juntos provam que a sonda RODOU e
        MESMO ASSIM não mexeu na busca
      · ⚠ O **e103 é o caso mais exigente**: regime OFFLINE, sonda de 20.000 pontos, e o
        disparo dele é `probeOffline` — que chama o `fire` DIRETO, sem passar pela cadência.
        É exatamente o caminho que um desarme ingênuo (só barrar o `due()`) deixaria passar.
        Foi por isso que o guard entrou nos 4 caminhos, e o offline é a prova de que valeu
      · Este item era **T1 ou T2 em 11 dos 24 relatórios** do estudo — o mais repetido
      · **G-7 FEITO** (`5b6df3e`): `artifacts/contrato_61.json` (extração + CURAÇÃO contra a
        medição — 3 falsos-positivos removidos: `n_baseline` do e81 que o §6.1 cita para NEGAR,
        `solution_id` do b4 que é `ref_ids`, `tempo_fit_s` dos pisos que é NULL por contrato) +
        `gate_contrato_61` no portão. Reproduz I-03/I-05/I-07 e acha **5 pendências SEM ITEM NO
        T11** (`adapt_delta_V` b3 · `mll_final` c262 · `loss_treino` e7 · `margem_3sigma` e103 ·
        `sigma_dict` ausente no ⑤ dos 4 pisos online, 112 células)
      · ✅ **AS 5 JÁ FORAM RESOLVIDAS em `4796a03`** — esta linha ficou roteando "decisão do
        autor" por mais 6 commits e a varredura de 2026-07-30 pegou. O desfecho de cada uma:
        **3 eram FALSO-POSITIVO DO GATE** (`mll_final` do c262 e `loss_treino` do e7 estavam
        ANINHADOS em `modelo_hp`; o e103 grava `margem_3sigma_stats`, mais rico que o
        `margem_3sigma` cobrado) ⇒ o gate passou a varrer em PROFUNDIDADE, aferindo PRESENÇA e
        não POSIÇÃO — é a **ERRATA 6/7**. **2 eram REAIS e foram implementadas**:
        `adapt_delta_V` DERIVADO no `b3_instrument.m` (sem tocar a árvore vendorizada) e o
        `sigma_dict` dos 4 pisos DECLARADO como `nao_se_aplica` (declarar a
        não-aplicabilidade é informação; omitir é silêncio)
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
      · ✅ **(a) RESOLVIDO em `4796a03`** (esta linha estava OBSOLETA, achado da varredura):
        `mll_final` era FALSO-POSITIVO do gate — está aninhado em `modelo_hp`, e o gate passou
        a varrer em profundidade (ERRATA 6). O `n_baseline` foi declarado NÃO-APLICÁVEL, como
        no e81 — o próprio `sigma_dict` do runner já dizia "AUSENTE POR DESENHO" (ERRATA 8)
      · ⚠ **FALTA p/ o carimbo:** validar célula D≥12 morrendo às 12 h COM camadas parciais
        (precisa de máquina — item do autor)
- [x] A2 · c122 — `73d9fef` (2026-07-30) · **SMOKE: n_ref=21 (=11D−1) no g=1 × 11 (=MU) no g≥2**
      — o teste de aceitação do I-01. ref_ids (21/11 ids) · y_treino_dist (462/484 pares) ·
      REGRA_DO_ROTULO no sigma_dict · params já existia
- [~] A3 · família b5 — `b74c620` + `08a4019` (2026-07-30)
      · I-05: acumulador P_wrong no VENDORIZADO (âncora `b5-pwrong-stats` + re-lacre) +
        `p_wrong_stats`/`n_substituicoes`/`flag_vetores_degenerados` no ⑥
      · `params` no ⑤ dos 3 · granularidade_③ no sigma_dict dos 3 (I-04)
      · ⚠ **ERRATA 13 (varredura 2026-07-30):** o item (4) do A3 — "amplitude em float64 no
        ⑥" — foi dado por AUSENTE porque a palavra literal não aparecia. **Meio
        falso-positivo, da família da ERRATA 6:** a medida já estava lá, em
        `flag_vetores_degenerados.norma_min`/`.norma_max`, ambos float64, lidos direto do
        `evolver` (sem patch vendorizado). Ficou EXPLÍCITA como `amplitude` para ninguém
        repetir a busca — é ela que discrimina o congelamento **PARCIAL** (`n_norma_zero>0`
        só diz "colapsou alguns"; a amplitude mostra os vetores encolhendo ANTES de zerar,
        que é onde a cadeia A8 começa)
      · 🔴 **NÃO IMPLEMENTADO, e agora declarado:** o **wrapper read-only no gatilho do
        `adapt`** (b5m-A8, ~8 linhas). É cirurgia VENDORIZADA em
        `ReferenceVectors.adapt` ⇒ exige âncora nova + re-lacre + **nova prova de
        não-perturbação** (~90 min de b5m). Não o fiz, e o buraco estava sem declaração em
        lugar nenhum — foi achado da varredura.
        **Por que dá para decidir sem pressa:** a cadeia A8 já é observável nas DUAS pontas
        — a CAUSA em `flag_vetores_degenerados` (norma dos vetores colapsando) e o EFEITO em
        `p_wrong_stats` (max≡0,0) + `n_substituicoes`≡0. O wrapper acrescentaria QUANDO o
        `adapt` dispara, que é corroboração, não a única evidência. **Decisão do autor**,
        pelo custo da prova.
      · ✅ **PROVA I-05 PASSOU** (`27ef86d`, 2026-07-30): ①③⑦ **BYTE-IDÊNTICAS** com × sem o
        patch vendorizado. STOCK (`b74c620~1`, 0 ocorrências) × COM (2 ocorrências), cada perna
        no SEU worktree isolado — a árvore principal nunca foi tocada:
        ① `bcda99b31dfb2c35` · ③ `17b6f9b68a6675fb` · ⑦ `cc06fcfa61e5a582` nos DOIS lados
      · ✅ **CUSTO MEDIDO, e a minha alegação anterior era FALSA (ERRATA 9)**: COM 2.781 s ×
        STOCK 2.810 s — o patch é até marginalmente mais rápido. Eu havia atribuído a ele um
        wall de 43 min ("2,5× de lentidão") e reescrito o acumulador em O(1) por causa disso;
        microbenchmark isolado (100k chamadas, array de 20) deu 30,5 µs × 7,1 µs por chamada
        ⇒ ~1,9 s por run, NÃO 23 min. Caiu o motivo, a reescrita foi **REVERTIDA** para a
        versão planejada (que preserva a MEDIANA) e o lacre voltou a bater sem artefato novo
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
- [~] A8 · e74 — **FIX DI-45 APLICADO**
      · ⚠ **ERRATA 15 (2026-07-30):** eu registrei aqui, e repeti ao autor duas vezes, que
        "`n_desalinhado` cai a ~0 é a PROVA do fix". **É FALSO, e a resposta estava a uma
        linha do campo:** `src/e74_instrument.m:184` diz
        `% mascara(Offspring)×Parent (fix opcional NAO aplicado)`. São DOIS
        desalinhamentos diferentes no e74: o da **DI-45** vive em
        `ClassifierSelect.m:56-58` (o `index` era posição DENTRO de `S` e indexava `Parent`
        inteiro) e **foi corrigido**; o `n_desalinhado` mede o de `Local_infill.m`
        (máscara(Offspring)×Parent), que **continua lá POR DECISÃO REGISTRADA**. O número
        não podia cair — e ter caído seria suspeito
      · MEDIDO: s42 pré-fix 93,49% (2.860/3.059) × smoke pós-fix 89,80% (273/304). A
        diferença é ruído de célula, não efeito do fix — porque o fix não toca esse sítio
      · ✅ **A PROVA REAL é o gate ±3σ**, e ele PASSOU: 3 células (MMF1, DTLZ2, ZDT1),
        **8 gates VERDES em cada**, sobre o smoke de 2026-07-30. Mais o `preflight`:
        âncora `e74-classifierselect-idx` **APLICADO** e lacre `867ae5f56d8b` **OK** `b74c620` (2026-07-30) · `S=find(y_label==1)` +
      índice absoluto · `n_desalinhado` PRESERVADO (⚠ ERRATA 15: NÃO é a prova — mede o
        desalinhamento de `Local_infill.m`, que fica por decisão) · âncora
      `e74-classifierselect-idx` + `repos.lock` re-lacrado · preflight: APLICADO
      · ⚠ FALTA (máquina): smoke de 3 células + gate ±3σ · regra-rótulo/y_treino_dist do e74
- [~] A9 · c217 — `52befff` (2026-07-30) · `pmid_ids` (era 0/25 células com a identidade) +
      · ⚠ **CARIMBO FALSO CORRIGIDO (2026-07-30, varredura):** este item estava `[x]`
        DEFINITIVO e o título do `52befff` diz "b4 e c217 (regra do rótulo…)", mas **só o b4
        recebeu**. Sem ela a ③ do c217 é "leitura proibida" pela regra 3 do R4 — o autor
        dispararia achando que estava auditável. Regra escrita agora no `sigma_dict`
      · ⚠ E a regra do c217 **não é a do b4**: o b4 julga contra as K referências radiais
        ("não é pior que TODAS"); o c217 é par-a-par **POSICIONAL E CÍCLICO** —
        `RBFNNPC.m:61` faz `Preference(mod(i+numberP,numberP)+1,…)`, ou seja cada ponto da
        sonda é julgado contra **UMA** referência, dada pela POSIÇÃO dele no bloco. Agregar
        contra o Pmid inteiro mede outra coisa
      · ⚠ Escrevi a fórmula **errada na 1ª vez** (off-by-one ao converter 1-based→0-based) e
        peguei ao simular o laço. A regra final traz as duas convenções, o aviso do
        deslocamento e o aviso de que sort/unique na ③ corrompe o rótulo (o pareamento
        depende da posição). `tests/test_a9_regra_rotulo_c217.py` trava a fórmula, com
        CONTROLE provando que a versão off-by-one não reproduz o laço
      `y_treino_dist` ternário · ⚠ params ⑤ do c217 ainda pendente (writer MATLAB)
- [x] A10 · c311/treed_media — `5aa31e3` (2026-07-30) · guard de tier ANTES do import do
      vendor (verificado: off/main/sweep-small BARRADOS, big passa) · aviso
      `n_sigma_valido` no sigma_dict do c311 (σ-NaN mediano 90,3% no big)
- [~] A11 · sonda estratificada — `b74c620` (2026-07-30) · mecanismo no harness
      (`emit_sonda_estratificada`/`amostra_estratificada`, RNG local uso_id=91, sob
      `preserve_all_rng`) + ligado no **c122**
      · **PREVALÊNCIA 7,4% no bloco contra 0,4% da régua = 18× mais positivos**
      · regimes separados na ③: 44.000 sonda · 10.500 estratificada · 3.632 busca
      · ✅ **GÊMEO MATLAB FEITO** (`9a53a51`, 2026-07-30): `SondaState.probeEstratificada` +
        `manifestBlockEstrat`/`takePendingTimeEstrat` (contadores SEPARADOS da régua) +
        `FEBudget.arquivoX()` + fiação em b4/c217/e74 sob `snd.due(g)`, depois da régua
      · 2 armadilhas minhas, pegas ANTES do commit: (i) o derivador de semente era FNV-1a em
        `uint64` e MATLAB **satura** em vez de dar wrap ⇒ TODA geração receberia a mesma
        semente (controle numérico: 1 valor distinto em 8). Trocado por MINSTD, cujo produto
        `(2^31−2)·16807 ≈ 3,6e13 < 2^53` é exato em double — 0 colisões em 1.600 pares;
        (ii) eu ia usar `Problem.CalObj` para a prevalência, mas o `UserProblem` é construído
        com `evalFcn` e SEM `objFcn` ⇒ cairia no stub da PROBLEM base e devolveria ZEROS,
        dando prevalência 1,0 falsa e silenciosa
      · DIVERGÊNCIA DELIBERADA: sem `true_f` no MATLAB — a ponte Python custa 1 round-trip
        POR PONTO (500 × ~200 sondas ≈ 100 mil por run) para um agregado que a análise
        recompõe EXATO do X da ③ (doutrina I-12). `prevalencia_nd_no_bloco` sai NaN por desenho
      · ⚠ FALTA (máquina): o gate G-6 de não-perturbação em b4/c217/e74 antes do carimbo

## 🔍 RODADA DE VALIDAÇÃO CRUZADA (2026-07-30, tarde) — auditoria de STALENESS

> **Por que existe.** O autor levantou a pergunta certa: *"houve algoritmo testado ANTES do
> seu estado de código final?"* — isto é, testamos, e depois mexemos num arquivo que aquele
> algoritmo usa. Um teste verde sobre código que mudou depois não vale nada, e nenhum gate
> desta campanha media isso.

**Método.** Fecho de imports por config (AST sobre `src/*.py`, recursivo) × `git log -1` por
arquivo × horário de cada teste. Nada de memória de sessão — só timestamp contra timestamp.

**Resultado — eixo SMOKE:** ✅ **0 stale.** Os 11 configs Python foram testados entre 11:10 e
11:43; a última mudança em qualquer dependência deles foi às **10:02** (`27ef86d`).

**Resultado — eixo PAR G-6:** 🔴 **9 de 10 STALE.**

| | |
|---|---|
| os 9 pares foram provados até | **30/07 00:18:27** (`dca0e37`) |
| `src/standalone_harness.py` (dependência de TODOS) mudou em | **30/07 08:12:50** (`b74c620`) |
| defasagem | **~8 horas** |

Atenuante MEDIDO: o diff é `115 insertions, **0 deletions**` — puramente aditivo (constantes
+ funções novas da sonda estratificada); nada existente foi modificado. Mas o **c122 é caso
à parte**: o mesmo commit fiou o bloco estratificado **dentro do laço de busca dele**.

**RE-PROVA (em série, um processo por vez):**

| config | ① sha256 | veredito |
|---|---|---|
| **c122** | `be06b54124e9c100` | ✅ BIT-IDÊNTICA — **e é o MESMO hash da prova de ontem** (linha 94), ou seja a sonda estratificada NÃO perturbou a busca |
| c311 | `07530706e23cdddd` | ✅ BIT-IDÊNTICA |
| treed_media | `dd03ee216118d017` | ✅ BIT-IDÊNTICA |
| e81 · c262 · moead_media · c154 · b5r · c149 | — | ⏳ interrompidos pelo autor p/ entrar junto com o lote de correções |
| b5m | `bcda99b31dfb2c35` | ✅ já era pós-mudança (12:11) |

**CLASSIFICAÇÃO DAS MUDANÇAS — o que pode alterar RESULTADO, e o que já está provado:**

| mudança | pode alterar? | prova |
|---|---|---|
| **e74 · fix DI-45** | **SIM — intencional** (autor aprovou) | ✅ **gate ±3σ PASSOU** — 3 células, 8 gates verdes cada (2026-07-30). ⚠ o `n_desalinhado→~0` que eu prometia era **ERRATA 15**: mede OUTRO sítio, deliberadamente não-corrigido |
| **b5 · acumulador vendorizado** | poderia (código DENTRO do algoritmo) | ✅ ①③⑦ byte-idênticas stock × patch, worktrees isolados |
| **A11 · sonda estratificada (c122)** | poderia (RNG + roda no laço) | ✅ ① idêntica à de antes do A11 |
| **G5 · checkpoint periódico** | poderia (escreve no meio do run) | ✅ `test_checkpoint_nao_muda_o_resultado` **com controle** provando que o checkpoint rodou |
| flag `sonda_on` / `UA_DD_SAEA_SONDA_OFF` | não, quando ligada (default) | ✅ é o próprio par G-6 |
| G1–G4, G7, instrumentação I-xx | não tocam a busca | ✅ construção + pares |

**ERRATA 11 — a tabela de `params` da s42 engana.** Medir `params` no ⑤ dos manifestos da
rodada-42 mostra "SEM params" em b5m/b5r/c154/c262/c217/moead_media/sobol_batch — mas isso é
**dado PRÉ-T11**, gerado antes de o I-07 existir. O que vale é o que o código de HOJE emite,
medido nos smokes: **9 de 10 configs Python gravam `params`; falta em UM — `sobol_batch`.**

**O QUE UM SMOKE PROVA, E O QUE NÃO PROVA.** Prova: o config roda ponta a ponta, escreve as
camadas contratadas, o ⑤ traz `campanha_id`/`repo_hash`/schema v2, o ⑥ tem header+footer sem
linha malformada, a proveniência fecha. **É verificação de ENCANAMENTO.** NÃO prova correção
numérica, fidelidade ao artigo nem que a busca faz o que deveria — um algoritmo pode estar
profundamente errado e passar nos 6 portões. Cobertura atual: **11 de 24 configs**, 6 deles
inteiramente verdes, 3 com inconclusivo esperado, 2 com achado aberto, **13 sem cobertura**.


## FASE V — verificações & re-runs
- [x] V1 · VD b1-torneio + VD b3-índice — `ca157d8` (2026-07-30) ·
      `handoff/T11-V1-verificacoes-dirigidas.md`
      · **VD-b1 🔴 CONFIRMADO:** o torneio ranqueia pelo PCheby do SUBCONJUNTO e indexa o
        `Dec` INTEIRO — **93,0% de 8.443 gerações**, mediana **44,9%** da população
        inalcançável, **28/28** células com ≥1 geração afetada (24 com a maioria)
      · ⚠ **ERRATA 10 — eu SUPERESTIMEI este achado.** Lendo o `EvolALG` até o fim: o torneio
        defeituoso constrói APENAS a metade-crossover da PRIMEIRA geração interna do GA de
        aquisição; da 2ª em diante os domínios CASAM (`EvolALG.m:65`). Medido: o ramo é
        **3,87%** dos 87,77 M candidatos scorados, e o infill veio da 1ª geração interna em
        **12,19%** dos ciclos ⇒ o torneio é **INERTE em ~93,9%**. Concentrado: BBOB_F37 62,7%
        e BBOB_F49 61,3%
      · ⚠ **E eu classifiquei ERRADO.** A SPEC já tem este item como **🟠 IMPL → CÓDIGO,
        documentado** (`SPEC:434` cita "torneio do b1" pelo nome; `SPEC:500` o lista entre as
        divergências periféricas mantidas no CÓDIGO, D30/D47), e o `EvolALG.m:9-10` registra a
        decisão anterior "o bug do torneio (:16) fica (CODIGO K.3)". Marcá-lo 🔴 disparou um
        D81 sem motivo e reabriu decisão FECHADA. **Retirada a proposta de conserto: nada muda.**
        A bússola da SPEC distingue os casos — o GA interno do b1 é periférico ao mecanismo que
        a tese mede; a seleção do e74 (DI-45) É o mecanismo
      · **VD-b3 🔴 estrutural:** `Next` mistura domínios de índice no ramo 1; `nzero=0` em
        1.619/1.619 não discrimina o ramo ⇒ instrumentar `size(Via,1)`/`NI−mu` (~2 linhas)
- [ ] V2 · re-runs s42: c311/big-mvns + b1/WFG1 · quimera c149 (rota A0→Mac) · ⑦ e103→bucket · ~29 não-ok no regime novo
- [~] V3 · lote de docs — `66195cf` (2026-07-30) · **PARTE A36** no REGISTRO (execução do T11 +
      as 8 ERRATAS + os 6 contratos novos) · nº da DI-40 corrigido nos 2 pontos (1,47 h medido) ·
      RUNBOOK: rito NOVO do teto (truncamento-com-dado) + seção do `campanha_id` + números
      · ✅ **PARTE A37** (`8123e92`): ERRATA A30 MEDIDA (c122 grava `fe` — 3.981 eventos com,
        0 sem; a DI-42 dizia o contrário) · **R4#10** virou a regra **11** do CONTRATO
        (dominância sobre ① ou ⑦ é LOSSY: `f0`/`f1` são float32 nas duas camadas, medido com
        `read_schema`) · regra **12** nova (bloco estratificado NUNCA na mesma análise que a
        régua) · `lnum` do c217 medido (`lote` = {1: 9.013, **3: 1**, 6: 64} — o lote 3 existe,
        mas `|Pmid|`/`|Pbest|` NÃO são logados ⇒ não resolvível pelo dado da s42)
      · ✅ **cards/INDEX**: 3 cartões estavam ⬜ desde o fim da R3 e os configs rodaram — status
        virado CONTRA O DADO (48 b5m · 49 b5r · 58 c311 · 48 moead_media com ⑤) + seção de
        campanhas (F5 ✅ · T10 ⏸ · T11 🟡)
      · ⚠ FICA COM A TORRE (RI-12): SPEC L.8 do e74 pós-fix · D7/`iteration_seed` na SPEC §D62
      · ⚠ NÃO MEXI, de propósito: o "~min-1h" do RUNBOOK **já estava certo** (`RUNBOOK:264`
        traz o medido 0,87–2,99 h/célula, média 1,47 h)

## ACEITAÇÃO FINAL
- [~] Suíte ≥410, 0 falhas · preflight 0 · re-gate 666 = 1+34 · smoke 24/24 · kill-test ✓ · handoffs escritos
      · ✅ **suíte 613 testes, 0 falhas** (era 394 no início da campanha; +219)
      · ✅ kill-test do checkpoint (G5) verde
      · ⚠ preflight: **1 pendência** — os 58 manifestos forasteiros (é item do AUTOR: as
        células que voltaram das VMs por rsync; já estão no bucket e o disco local tem de
        partir limpo)
      · ⚠ re-gate: **1 quimera + 15 anômalas + 21 `footer_faltante`** — o "34" do plano NÃO
        se reproduz (ERRATA 4); as 21 são exatamente as que o **B-15 manda não acusar**.
        Placar RATIFICADO pelo autor em 2026-07-30
      · 🟡 **SMOKE 11 de 24** — os 11 configs PYTHON, 1 célula real cada, em tempdir:
        | config | s | portão |
        |---|---|---|
        | c154 | 98,1 | ✅ verdes |
        | c122 | 50,4 | ✅ verdes |
        | c262 | 34,8 | ✅ verdes |
        | c149 | 251,1 | ✅ verdes |
        | e81 | 23,5 | ✅ verdes |
        | b5m | 2.781 | ✅ (as 2 pernas do I-05) |
        | b5r | 172,1 | ⚠ G-1 inconclusivo (③ sem linha marcada) |
        | c311 | 26,0 | ⚠ G-1 inconclusivo |
        | treed_media | 27,9 | ⚠ G-1 + G-7 inconclusivos |
        | moead_media | 56,8 | 🔴 G-7: ⑥ sem `p_wrong_stats` |
        | sobol_batch | 1,7 | 🔴 G-7: ⑤ sem `params` |
      · ⚠ **NOTA DE MÉTODO — a 1ª tentativa destes smokes foi INVÁLIDA e está registrada
        para não se repetir.** Rodei os 10 num `ThreadPoolExecutor` (4 threads, 1 processo).
        Os tempdirs eram isolados, o **estado global do torch não**: `c122_thetadeadp.py:192`
        põe `set_default_dtype(float32)` e `botorch_harness.py:112` põe `float64`, e em
        threads concorrentes um sobrescreve o outro no meio do forward — o c122 morreu com
        `mat1 and mat2 must have the same dtype`. **Não era bug do c122.** O `envs.json` crava
        a regra violada: *"dispatch: subprocess no python do venv-alvo (D79); 1 run = 1 core"*.
        Os 5 configs de venv PRÓPRIO (b5r, moead_media, c311, treed_media, e81) rodaram em
        subprocess e valem; os 5 do `env_main` foram refeitos **EM SÉRIE**, um processo por vez
      · ⏳ FALTA: os **13 smokes MATLAB** (máquina do autor)
- [ ] 🗳 **DECISÕES DO AUTOR abertas pelos gates** (D81 — reportado, NÃO implementado):
      · `sobol_batch` sem `params` no ⑤: a lacuna é REAL (reproduzida isolada), mas a
        exigência é regra GLOBAL do gate, ancorada no `CONTRATO_DE_DADOS.md:26`; o **I-07 do
        plano nomeia só 5 configs** e sobol_batch não está entre eles. Preencher = implementar
        fora do plano
      · `moead_media` sem `p_wrong_stats` no ⑥: o moead_media é a **ABLAÇÃO sem a maquinaria
        probabilística** (mode 12), então pode ser falso-positivo do MEU `contrato_61`, da
        família da ERRATA 6 — a conferir antes de qualquer conserto
- [ ] AUTOR: tag `t11-definitivo` + push · fila de infra D10 (envs Linux · lib gcs env_c311 · pins · datasets 29 sementes · SUB-varN) · DISPARO
