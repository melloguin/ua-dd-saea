# CARTÃO T12 — O ACABAMENTO FINAL (torre, 2026-07-31)

> **Missão:** fechar os 8 bloqueadores da validação de fidelidade do T11 + as 2 causas-raiz
> diagnosticadas pela torre (REGISTRO **A40**) + a conversão dos gates decorativos — para
> chegar à VERSÃO FINAL do código antes das 30 sementes (~18.291 h-core).
> **Fontes:** `handoff/T11-HANDOFF-TORRE-CENTRAL.md` (§3-§4) · `f5/t11/RELATORIO_FINAL_T11.md`
> · `f5/t11/dados/bloqueios.json` · REGISTRO A40.
> **Estimativa: ~3-4h.** Trabalho de código: ~15 linhas + testes. O resto é prova e doc.

## §0 · A DOUTRINA DESTE CARTÃO (inegociável — é a lição do T11)

**Todo fix exige CONTROLE NEGATIVO: um teste que REPROVA no código de hoje e PASSA depois do
fix.** E todo campo de instrumentação exige **asserção sobre o VALOR medido em run real** —
nunca sobre a existência da chave. Os 2 campos sentinela do T11 passaram por 6 portões verdes
porque os gates testavam texto (`inspect.getsource`+`assertIn`); isso acaba aqui. Se um fix
não tiver como demonstrar o defeito ANTES, pare e pergunte (D81).

## §1 · OS FIXES DE CÓDIGO (ordem de execução)

**T12.1 · BL-01 — `pmid_ids` do c217 (causa-raiz A40-1).** `src/c217_instrument.m:192-206`
casa `bud.solutionIdOf(Pmid(i,:))` bit-a-bit em D colunas, mas o `Pmid` de
`CalFitnessPC.m:67-73` tem **D+1 colunas** (`Input = [PopDec, Fitness]`). Fix: **`Pmid(i,
1:end-1)`**. Controle negativo: teste que monta um Pmid D+1 sintético e prova que a versão
antiga devolve −1 e a nova devolve o id certo. Prova de valor: smoke real do c217 com
`pmid_ids` contendo **ids ≥ 0** (na s42 era −1 em 426/426).

**T12.2 · BL-02 — `flag_vetores_degenerados` da família b5 (causa-raiz A40-2).**
`src/b5_prob.py:113-118` lê `evolver.population.problem.reference_vectors` — **o atributo não
existe no problem do DESDEO; os vetores vivem no EVOLVER** (RVEA/MOEAD). O `except` D97
mascara o `AttributeError` → `None` em 1.144/1.144. Fix: apontar ao evolver (verificar o nome
exato no objeto vivo: `evolver.reference_vectors` — provar com run, não com grep). Vale para
b5m/b5r/moead_media. Controle negativo + prova de valor: smoke b5m com a flag **não-null** e,
no DTLZ2 (o caso do congelamento A8), `n_norma_zero > 0` aparecendo — é o resultado D9-4
finalmente instrumentado.

**T12.3 · BL-05 — `y_treino_dist` degenerado no c217.** Diagnóstico no
`f5/t11/relatorios_config/c217.md`; corrigir a fonte (o `Output` ternário real, não o
degenerado) com a mesma dupla prova (controle negativo + valor real no smoke).

**T12.4 · BL-06 — finalProbe sob `teto_wall` (c154/c262).** 1 linha: no rito de truncamento
(G5), disparar o `finalProbe` da sonda ANTES de fechar as camadas parciais (~0,08s — o bloco
final é a foto mais importante da célula truncada). Controle negativo: kill-por-teto artificial
sem/com o fix — o ⑥/③ ganham o bloco final.

**T12.5 · BL-09 — `fflush` por linha no writer MATLAB.** `experiment.m:jsonl_line` ganha
`fflush(fid)` (1 linha) — sem ele, morte de processo MATLAB perde a cauda do ⑥ mesmo pós-B-11.
Controle negativo: kill de um run MATLAB curto sem/com fflush (pendência de máquina: se o
engine não estiver disponível na sessão, deixar o teste escrito e marcar ⚠ p/ o autor rodar).

**T12.6 · BL-08 — pinar `scipy` na `envs.json`/locks** (1 linha; a decisão de pin é do AUTOR
— D80 — mas ele já a autorizou na fila D10; use a versão instalada medida: 1.17.1).

## §2 · A CONVERSÃO DOS GATES DECORATIVOS

**T12.7** — Os 2 arquivos com `inspect.getsource`+`assertIn` (`tests/test_a2_c122.py`,
`tests/test_piso_off.py`): converter cada asserção-de-texto em asserção-de-comportamento
(executar o caminho e medir o efeito). **T12.8** — Varredura de TODOS os campos de
instrumentação criados no T11 (`pmid_ids`, `ref_ids`, `y_treino_dist`, `p_wrong_stats`,
`n_substituicoes`, `flag_vetores_degenerados`, `tempo_aval_real_s`, `n_front1`/`f_best` do
sobol_batch, `repo_hash`, `params` no ⑤, regra-do-rótulo no sigma_dict): 1 teste de VALOR por
campo, sobre artefato de smoke real (tempdir), no padrão dos controles do c149/sobol_batch
(o modelo citado pelo validador). Qualquer campo que reprove ⇒ mesma cirurgia dos T12.1-3.

## §3 · AS 2 DECISÕES DO AUTOR (embutidas; levar recomendação, não resolver sozinho)

**T12.D1 · BL-07 — o piso de ruído entre máquinas.** O piso O-18 (HV ≤1,55%) foi medido em 24
células e NÃO cobre o observado (`c238/MMF1`: ΔHV −9,69%, 6,3×). **Recomendação da torre:**
(a) re-caracterizar o piso com os dados cross-máquina JÁ EXISTENTES (validação cruzada +
`data_xmachine/` + os 58 manifests forasteiros) → publicar `artifacts/piso_ruido.json` POR
PROBLEMA (não global) + regra de leitura no CONTRATO ("comparação entre configs de máquinas
distintas só é conclusiva acima do piso do problema") — 0 CPU novo, só análise. Alternativa
(b): alocar configs-a-comparar sempre na mesma máquina (restringe o escalonamento). A regra
"um config, uma máquina" já vigente resolve o INTRA-config; o piso resolve o INTER.

**T12.D2 · BL-10 — a contradição N=20.** DI-32/A2 ("definitivo") × DI-39 ("provisório") —
**a DI-39 é posterior e do autor: prevalece.** Recomendação: retificação formal no REGISTRO +
varrer os 3 textos que citam "definitivo" + **manter o SUB-varN na fila pré-disparo** (D10);
se eleger N≠20, re-rodar os 4 pisos custa ~3,3 h-core (trivial). O autor só precisa confirmar.

## §4 · REGRAS DE OPERAÇÃO

As mesmas do `handoff/T11-PROMPT-SESSAO.md` §3-§4 (serial · suíte SEMPRE antes de commit com
`/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python` · add
explícito · NUNCA push · D81/D97 · tempdir SEMPRE · checklist abaixo atualizado a cada item).
⚠ `CalFitnessPC.m` é VENDORIZADO — o fix T12.1 é no `c217_instrument.m` (NOSSO), que só LÊ o
Pmid: nenhum re-lacre necessário. Nenhum outro item toca árvore vendorizada.

## §5 · CHECKLIST (atualizar aqui mesmo)

- [x] T12.1 · BL-01 pmid_ids (fix + controle negativo + smoke com ids ≥0) — `src/c217_instrument.m`
      fatia `Pmid(i, 1:D)`; `tests/test_t12_c217_instrument.py` (4 testes, MATLAB real: valor +
      mutante que reproduz o −1). Controle negativo demonstrado: contra o fonte de ontem o teste
      REPROVA (`[-1,-1,-1,-1] != [2,6,10,14]`). Smoke real `main/c217/MMF1/s42` em tempdir:
      **426/426 com id ≥ 0** (min 0, max 59, 0 sentinelas) onde a s42 tinha 426/426 = −1. Suíte 631 OK.
- [x] T12.2 · BL-02 flag_vetores_degenerados — `src/b5_prob.py` lê `evolver.reference_vectors`
      (o `desdeo_problem` vendorizado tem **0 ocorrências** do atributo); `tests/test_t12_b5_vetores.py`
      (5 testes sobre a classe `ReferenceVectors` VENDORIZADA real: sadio, colapso A8 total, colapso
      PARCIAL, mutante). Controle negativo: contra o fonte de ontem, 2 falhas + 2 erros.
      **Smoke real `off/b5m/DTLZ2/s42`** (2.808 s, env_b5, tempdir): **381/381 não-nulo** (era
      0/1.144). ⚠ **A expectativa do cartão não se confirmou e o dado manda**: `n_norma_zero = 0`
      em 381/381, `norma_min≈norma_max≈1`, `n_substituicoes` 3–12/geração (Σ 7.769), `P_wrong.max`
      até 1,0 — **o DTLZ2 é célula SADIA**. Pelo `f5/t11/relatorios_config/b5m.md` as congeladas são
      **DTLZ3 (380/380) e DTLZ1 (370)**, não DTLZ2. **Controle positivo COLHIDO em
      `off/b5m/DTLZ3/s42`** (2.736 s — fecha também o **BL-22**, o smoke que faltava da cadeia A8):
      flag não-nula **381/381**, `n_norma_zero = 105 de 105 vetores` em **381/381 gerações**,
      `norma_min = norma_max = 0,0`, `n_substituicoes = 0` (soma 0) e `P_wrong.max = 0,0`. **A
      cadeia A8 inteira — `adapt` → norma 0 → PBI NaN → P_wrong ≡ 0 → zero substituições — está
      medida em célula real pela primeira vez**, e o par DTLZ3 (colapsada) × DTLZ2 (sadia) é o
      controle positivo/negativo do campo. Ver §7 · pendência (a) `moead_media`.
- [x] T12.3 · BL-05 y_treino_dist c217 — os DOIS defeitos: rótulo **binário {1,2}**
      (`CalFitnessPC.m:69-71`), não ternário, e conjunto = **TrainIn**, não Input. Agora
      `classe_melhor`/`classe_pior`/`prevalencia` + `n_input` + `confere_com_TrainIn` (o controle
      interno publicado). 4 testes novos em `tests/test_t12_c217_instrument.py` (8 no total, MATLAB
      real) + mutante que reproduz o `(0,0,n)`. Controle negativo contra o fonte de ontem:
      3 erros (`KeyError: 'classe_melhor'`) + 1 falha. ⚠ `params.surrogate` do ⑤ ainda repete a
      ficção do ternário — é **BL-15**, endereçado no T12.8 (o cartão o põe na varredura de `params`).
- [x] T12.4 · BL-06 finalProbe sob teto_wall (c154/c262) — não era 1 linha: no ponto do `break` o
      modelo já morrera no `del` (D86). O `del`/`iteration_cleanup` desceram para DEPOIS do teto (o
      `exceeded` aborta só por `elapsed` desde a DI-43, então o INSTANTE do teto não se move) e o
      bloco final sai no ramo do truncamento, com `motivo="ultima iteracao (teto_wall DI-43/44)"`.
      `tests/test_t12_teto_sonda.py`: 12 testes, run REAL truncado na **iteração 3** (ímpar ⇒ fora
      da cadência ⇒ o bloco só pode ter vindo do teto). Controle negativo: 4 falhas + 2 erros no
      código de ontem (`3 not found in [1, 2]`). **Bit-identidade**: ①②③ byte-idênticas pré×pós
      nos 2 configs; ④ difere — e o CONTROLE mostra que ela difere entre 2 execuções do MESMO
      código (são wall-times). ⚠ Achado colateral em §7 · pendência (b).
- [x] T12.5 · BL-09 — **NENHUMA linha de código; o bloqueio não sobreviveu à medição.** O engine
      estava disponível (R2025a nesta máquina), então tudo foi medido, não alegado:
      (1) **`fflush` não existe no MATLAB** (`exist('fflush')=0`) — e `jsonl_line` não tem
      `try/catch`, logo a "1 linha" prescrita **derrubaria todo run MATLAB da campanha**;
      (2) **modo perda-de-cauda REFUTADO** — 1 linha de 64 B sobrevive a `kill -9` (o writer não é
      bufferizado); (3) **modo SPLICE CONFIRMADO, mas o fix não é flush, é atomicidade** — 4
      escritores × 300 linhas de 6,4 KB: `fprintf` **30 partidas**, `fwrite` **26**,
      `java.io.FileOutputStream` append **0** (1.200/1.200 linhas nos três — nada se PERDE).
      **Não troquei o writer dos 13 configs na véspera da tag**: o ⑥ do MATLAB tem escritor ÚNICO
      hoje (o `experiments.py` só despacha o roster Python; `parfor` escreve células distintas).
      `tests/test_t12_jsonl_matlab.py` (4 testes, writer REAL extraído do `experiment.m`) tranca o
      que é determinístico e **re-mede em cada máquina** — se a libc do Linux bufferizar, fica
      vermelho lá. Decisão em §7 · pendência (d).
- [x] T12.6 · BL-08 pin scipy — `scipy==1.17.1` nos **três** sítios (`envs.json` `key_pins`,
      `repos.lock` ao lado do botorch, `requirements/env_main.txt`), com o motivo do torch
      (DI-34/Q4: intenção solta = o pip da VM resolve outra). `tests/test_t12_pin_scipy.py`
      (4 testes) não afere a linha no artefato: casa os 3 artefatos entre si, casa o pin com o
      scipy **instalado** e trava o **sha256 do lote de Owen** de `_sobol_batch01` em 3 pontos
      (D=2/10/30) + controle de determinismo por semente. Controle negativo: sem o pin, 1 falha
      + 1 erro. ⚠ `numpy` segue `>=2,<3` — ver §7 · pendência (e).
- [x] T12.7 · gates texto→comportamento (2 arquivos) — **a conversão pegou o BL-03 no 1º disparo.**
      `tests/test_a2_c122.py`: os 5 gates do bloco `sonda_estratificada` (220-260) agora EXECUTAM
      `emit_sonda_estratificada` e aferem a LINHA emitida; o `meta` do `emit_sonda_block` é aferido
      no evento, não na assinatura; o RNG é aferido no ESTADO (não no texto do `with`).
      `tests/test_piso_off.py`: o gancho do mode 12 aferia `inspect.getsource` do `__init__`/
      `_next_gen` — agora casa o objeto (`mod.MOEAD_select is MOEAD_select`, e **não** o
      probabilístico) e constrói uma `Population` VENDORIZADA real para provar que os 3 archives
      são indexados por geração. **Cirurgia BL-03** (`src/standalone_harness.py`): o emissor
      estratificado não ramificava por `pred_tipo` — o score par-a-par do c122 ia para `mu_0` e a
      confiança para `sigma_0`, com `pred_score` NULL em 10.500/10.500 linhas. Ramificado como a
      função irmã. **Smoke real `main/c122/MMF1/s42`** (51,8 s): **11.000/11.000** linhas
      `sonda_estratificada` com `pred_score` e `pred_confianca` preenchidos e `mu_0`/`sigma_0`
      NULL. ⚠ 4 gates de texto do `test_a2_c122.py` exigem artefato de run real
      (`n_ref` do ⑥, `REGRA_DO_ROTULO` do ⑤, `n_front1` do sobol_batch, `geracoes_derivadas` do
      ⑤ MATLAB) e foram **movidos para o T12.8**, que é onde os testes sobre smoke vivem.
- [x] T12.8 · varredura de VALOR de todos os campos T11 — **mais 2 reprovaram, e foram operados.**
      **BL-04** (`tempo_aval_real_s` dos 5 offline): a CARGA do dataset era cronometrada, então o
      ⑤ publicava o tempo de INGESTÃO como custo de avaliar (medido **0,0003 s** no b5m/DTLZ2; era
      `0.0` exato na s42). `FEBudget.descarta_cronometro_de_aval()` zera relógio **e contador** —
      zerar só o relógio devolveria `0.0`, que é a afirmação "avaliar custou zero", o sentinela que
      o I-02 nasceu para matar. Agora o offline publica **NULL**. **BL-15** (`params` do ⑤ do c217):
      as 3 chaves eram AFIRMAÇÃO ERRADA — `treino` dizia "do arquivo" (vem da POPULAÇÃO),
      `surrogate` dizia alvo ternário (é BINÁRIO {1,2}) e `operadores` dizia "Balde C 20/20"
      (o stock roda `{1,15,1,5}` e a SPEC §567 diz que Balde C não se aplica). Corrigidas e
      **provadas no ⑤ de um run MATLAB real**. `tests/test_t12_valores_t11.py` (9 testes): o
      `params` é cruzado com o LITERAL do vendorizado (não com um texto esperado); `n_front1`/
      `f_best` são medidos num `FEBudget` real com front conhecido + controle degenerado;
      `repo_hash` é validado com `git cat-file`. Controle negativo: 5 falhas + 1 erro.
      Campos já cobertos em arquivo próprio: `pmid_ids`/`y_treino_dist`/`fe_treino_max` (T12.1/3),
      `flag_vetores_degenerados` (T12.2), `p_wrong_stats`/`n_substituicoes` (medidos nos 2 smokes
      b5m: DTLZ2 Σ7.769 × DTLZ3 Σ0), `pred_score` da sonda estratificada (T12.7).
- [ ] T12.D1 · piso de ruído → `piso_ruido.json` + regra no CONTRATO (após OK do autor)
- [x] T12.D2 · retificação N=20 — **autor confirmou (2026-07-31): a DI-39 prevalece.** Retificação
      formal no REGISTRO (PARTE A41.4 / DI-41) + os 3 textos varridos: A20/A2 marcado como superado,
      `40_subestudos/varredura_N_pisos.md` **e o `gen_bundles.py` que o gera** (corrigir só o `.md`
      seria desfeito na próxima regeneração), e `cards/INDEX.md:67` passa a declarar `SUB-varN` =
      **PRÉ-REQUISITO do M8**. A SPEC (:1682) e o `01_regras_globais.md` já diziam "provisório" —
      estavam certos, não mudaram.
- [ ] REGISTRO A41 (fechamento) + handoff `handoff/T12-FINAL.md`

## §6 · DEFINIÇÃO DE PRONTO DO CARTÃO

Suíte ≥627 + novos, **0 falhas** · cada fix com controle negativo demonstrado (reprovava →
passa) · smokes reais de c217, b5m e 1 célula-teto com os campos carregando VALORES (zero
sentinelas) · as 2 decisões registradas com o veredito do autor · `staleness` 0 · handoff.
**Depois deste cartão: a tag final do autor → fila de infra D10 → DISPARO das 30 sementes.**

## §7 · PENDÊNCIAS ABERTAS PELA EXECUÇÃO (para o AUTOR — D81)

**(a) `moead_media` no T12.2.** O cartão diz *"vale para b5m/b5r/moead_media"*, mas no
`src/piso_offline.py` **o campo nunca foi escrito** (0 ocorrências de `reference_vectors`) — não
há o que "apontar ao evolver". Escrever o wrapper lá é **item novo** (a F5.4 o pediu; o
`bloqueios.json` o precifica em ~90 min à parte), e acrescenta chave ao ⑥ de um config cujo
contrato foi fechado — o clássico "gate vermelho misterioso" (6 sítios de fiação). Medido a favor:
o `MOEA_D` (mode 12) **tem** `reference_vectors` (`MOEAD.py:111`), então o contraste
piso × b5 sobre a causa do A8 seria mensurável. **Recomendação: fazer, com smoke de
`moead_media` + portão, se o autor autorizar antes da tag.** Não fiz sozinho.

**(b) Contaminação de estado global entre teste-com-mock e run REAL (PRÉ-EXISTENTE).** Um run
REAL de c262 no MESMO processo em que já rodou
`tests/test_batch_q10.py::TestCalibracaoBatchT9::test_c154_call_site_usa_o_helper_nao_hardcode`
morre com `ValueError: torch.cat(): expected a non-empty list of Tensors` dentro do
`optimize_acqf`. **Reproduzido com o fix do BL-06 desfeito** ⇒ não é desta campanha; ficou visível
agora porque este cartão é o primeiro a rodar célula REAL dentro da suíte. Aquele teste faz
`mock.patch` em `botorch.optim.optimize_acqf` e em `gen_batch_initial_conditions`. **Risco para a
campanha: nenhum** — 1 célula = 1 processo no despachante. **Mitigação adotada:** todo teste que
roda célula real vai em **subprocesso** (é a regra que produziu os smokes do T11, e é como a
campanha roda). Recomendação: manter essa regra nos testes novos do T12.7/T12.8.

**(d) O writer ⑥ do MATLAB não é atômico por linha — trocar agora ou não?** Medido (§5 · T12.5):
`fprintf` parte 30 de 1.200 linhas de 6,4 KB sob 4 escritores; o `write(byte[])` do Java parte 0.
Hoje isso **não** expõe a campanha (escritor único por ⑥), e por isso não mexi. **Recomendação:
NÃO trocar antes da tag** — o custo é o writer dos 13 configs MATLAB (o `jsonl_line` + 18
`fprintf(fid,…)` diretos nos `*_instrument.m`), justo o tipo de mudança larga que a doutrina manda
evitar na véspera. **Trocar SE** o autor pretender: (i) dois processos na mesma célula (retomada
concorrente), (ii) qualquer co-escritor Python no ⑥ do MATLAB, ou (iii) duas máquinas gravando a
mesma célula. O caminho está provado e é local: `jsonl_write(fid, linha)` usando
`java.io.FileOutputStream(fopen(fid), true)` — o `fid` continua sendo a identidade que os 19
sítios já passam, e todos os guards `fid > 2` seguem valendo. ⚠ O comentário do `jsonl_open`
(B-11) descreve um co-escritor Python "durante a chamada MATLAB" que **não existe na arquitetura
de hoje** — vale corrigir o comentário junto (armadilha doc×código).

**(e) O `numpy` do env_main continua solto (`>=2,<3`).** O próprio BL-08 diz que a bit-identidade
do scramble de Owen vale *"SÓ sob numpy 2.4.6 **+** scipy 1.17.1 nos dois lados"* — pinei só o
scipy porque só ele estava autorizado (fila D10). Com o numpy solto, o pip de VM-1/VM-2 pode
resolver 2.5.x e o pin do scipy protege metade do par. **Recomendação: `numpy==2.4.6` no mesmo
movimento** (o `tests/test_t12_pin_scipy.py` já falharia no hash do lote se isso mudasse o
scramble — mas falharia DEPOIS do provisionamento, não antes). 1 linha × 3 artefatos, decisão do
autor (D80).

**(c) `flag_vetores_degenerados` continua sendo colhido no replay pós-busca**
(`b5_prob.py:536`) ⇒ valor CONSTANTE nas gerações, contra o que o comentário do próprio código
promete ("mostra os vetores encolhendo ANTES de zerar"). O `bloqueios.json` chama isso de defeito
secundário (~3 linhas: acumulador módulo-nível com chave `gen_count`, o padrão já validado do
`P_WRONG_STATS`) e o cartão não o incluiu no fix. **Recomendação: fazer junto de (a)** — sem ele o
campo não distingue congelamento TOTAL de PARCIAL ao longo do tempo, que é 649 das 2.237
transições congeladas.
