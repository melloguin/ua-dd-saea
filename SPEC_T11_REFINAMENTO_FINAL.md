# SPEC T11 — O REFINAMENTO FINAL DO CÓDIGO (a rodada suprema de melhoria)

> **Autor:** torre de controle, 2026-07-29 · **Status: VINCULANTE** (todas as decisões abaixo
> foram RATIFICADAS pelo autor — DI-41..DI-45 + mesa T11-D1..D13 13/13; REGISTRO A29-A35).
> **Leitor-alvo: um Claude Code SEM NENHUM contexto prévio** (possivelmente em outra conta).
> Lendo esta SPEC + o `MAPA_ARTEFATOS.md` + os documentos da ordem do §1, você terá o
> conhecimento necessário para implementar no nível de qualidade das rodadas anteriores.

---

## §0 · A MISSÃO EM UM PARÁGRAFO

O pipeline está cientificamente validado (duas campanhas independentes, zero bugs de
algoritmo). Esta rodada conserta **o encanamento**: 13 bloqueadores de proveniência/escrita,
o novo regime de execução DI-43/44 (truncamento-com-dado + checkpoints), ~20 itens de
instrumentação, 9 gates automáticos, 1 fix de fidelidade ratificado (e74) e o lote de docs —
para então disparar as 30 sementes (~18.291 h-core) com o portão se auto-validando.
**Critério de ordem (do autor): destravar o máximo de algoritmos para rodar em escala, o mais
cedo possível** — globais habilitadoras primeiro, depois algoritmo a algoritmo, porque a quota
pode acabar no meio e o autor dispara os experimentos dos algoritmos já finalizados.

## §1 · ORDEM DE LEITURA OBRIGATÓRIA (antes de escrever 1 linha)

1. `CLAUDE.md` (raiz) + `claude_code_context/CLAUDE.md` — regras invioláveis. Em especial:
   **D81** (ambiguidade ⇒ PARE e pergunte ao autor) · **D97** (NUNCA "melhorar" fidelidade por
   conta própria) · **D29** (bússola de divergência código×paper) · **NUNCA `git push`** ·
   **NUNCA `git add -A`** · suíte SEMPRE antes de commitar · commits pequenos com prefixo
   `[T11-<fase>]`.
2. `MAPA_ARTEFATOS.md` — onde está cada coisa.
3. **`T11_STATUS.md` — o rastreador vivo.** Retome SEMPRE do primeiro item ☐. Ao concluir um
   item: marque ☑ com o hash do commit, rode a suíte, commite o próprio T11_STATUS.md junto.
   É isto que torna a troca de conta/quota indolor.
4. `CONTRATO_DE_DADOS.md` — antes de tocar qualquer writer de camada.
5. `f5/PLANO_RODADA_PERFEITA.md` §1-§2-§5 — **a fonte de detalhe** de cada B-xx/I-xx/G-x:
   arquivo:linha, número medido na rodada-42, correção proposta e TESTE DE ACEITAÇÃO. Esta SPEC
   dá a ordem e o escopo; o detalhe fino de cada item está LÁ (não duplicado aqui).
6. `handoff/F5-LAUDO-INSTRUMENTACAO.md` — detalhe dos itens de instrumentação (I-1..I-8).
7. `REGISTRO_DECISOES_IMPLEMENTACAO.md` **PARTES A29-A35** — as decisões que governam tudo aqui.
8. Por algoritmo (na hora de tocá-lo): `claude_code_context/*/alg_<X>.md` +
   `f5/relatorios_config/<X>.md`.

## §2 · AS DECISÕES VINCULANTES (resumo executivo; detalhe no REGISTRO A29-A35)

- **DI-41/42** (aplicadas): status do runner é autoridade; token `cache_hit_travado`; accept
  INCONCLUSIVO≠verde; ⑦ multi-surrogate; blindagem dual_write; eixo da sonda = `fe_treino_max`.
- **DI-43 (emendada pela DI-44): teto = 12 h (`--teto-s 43200`, o default JÁ NO CÓDIGO — não
  mudar o número!)** · **roster 100%**: TODAS as 695 células × 30 sementes, incluindo as 5
  c154-batch (a restrição DI-40 de DISPATCH está revogada — o `runs_matrix.csv` nunca as
  removeu) · **truncamento-com-dado universal**: no stack BoTorch o aborto-por-projeção está
  EXTINTO; teto dispara por RELÓGIO (elapsed) e fecha `failed/teto_wall` GRAVANDO as camadas
  parciais (a projeção vira warning logado) · **checkpoints intermediários** nos runners Python.
- **DI-45: fix do e74 APROVADO** (desalinhamento máscara×Parent em `ClassifierSelect.m:46-48`;
  1 linha nova + 1 alterada; preservar telemetria `n_desalinhado`; re-lacre de âncora).
- **D6:** falhas algorítmicas reais (c154/ZDT6, c154/BBOB_F55, c262/WFG1, b1/DTLZ4) = conferir
  contra o paper; default = LIMITAÇÃO documentada (não implementar fallback sem ordem do autor).
- **D7:** `iteration_seed` passa a incluir a CÉLULA (problema) no M8 — D62 emendada; declarar
  no protocolo que os streams offline mudam vs s42.
- **D11:** TODAS as melhorias de instrumentação (incl. sonda estratificada dos classificadores).
- **D13:** verificações dirigidas: SÓ b1-torneio (`EvolALG.m:16`) e b3-índice (`UpdataArchive`).
- **NÃO-FAZER (vinculante!):** a lista do `handoff/T11-PLANO-CONSOLIDADO.md` §7 e §10-12 —
  destaques: NUNCA inverter p0/p1 do b4; NÃO mudar QUANDO a sonda do c122 dispara (só o
  metadado); NÃO inserir guard no vendorizado do b5 (o congelamento é RESULTADO); NÃO tocar
  no float32/D53; NÃO consolidar os 3 `load_sonda` (recusado); NÃO aplicar "correção" da
  fantasia do e103 (0,05 está CERTO).

## §3 · O PLANO — FASES SERIAIS (a ordem é NORMATIVA)

> Formato de cada item no detalhe: ver `f5/PLANO_RODADA_PERFEITA.md`. Toda fase termina com:
> suíte verde (394+, mesma 1 falha ambiental até o item G6.7 consertá-la) + commit + T11_STATUS
> atualizado. **Depois da FASE G, cada algoritmo finalizado ganha o carimbo "DEFINITIVO ✅" no
> T11_STATUS e o AUTOR PODE DISPARAR os experimentos dele em escala.**

### FASE G — GLOBAIS HABILITADORAS (destravam TODOS os algoritmos de uma vez)

**G1 · O ⑥ blindado** (`src/audit_log.py`) — B-01 anti-append (RunJaFechado se footer com
fe_final≠null preexistir) + B-11 escrita atômica de linha (`os.write` com O_APPEND, linhas ≤
PIPE_BUF; header/sigma_dict grandes → fragmentar ou flock). Testes: reabrir-fechado levanta;
8 processos × 10k linhas ⇒ 80k parseáveis.

**G2 · O despachante honesto** (`experiments.py`) — B-02 no-op NÃO abre o ⑥ (instanciar
AuditLogger só depois de decidir executar; skip → stdout/done.txt) + B-16 lista `NO_RETRY`
(exceções determinísticas: `least squares problem is underdetermined`, `random_search_optimizer
falhou nas 3 tentativas`, `ModelFittingError: All attempts to fit`) + I-10 manifesto de aborto
batch grava o q REAL (ramo `new_manifest`) + REVOGAÇÃO DI-40: nenhum filtro de dispatch exclui
c154 do batch.

**G3 · Identidade de campanha** (`src/manifest.py` + schema ⑤ v2) — B-03 `campanha_id`
(hash-do-commit + data do disparo) gravado no ⑤ e exigido pelo `is_run_done` (v1/id-antigo ⇒
False) + OP-6 higiene do `--force` (limpar artefatos da célula ANTES de re-rodar) + fallback-
footer (O-21/E-04: sem ⑤, cair para o footer do ⑥ antes de declarar "sem-manifesto").

**G4 · Espelho resiliente** (`src/gcs.py` + harnesses) — B-09 `mirror_run` também no ABORTO
(finally do runner e do despachante) + B-10 identidade de execução no blob (prefixo
`campanha_id/host` OU if-generation-match) + NUNCA podar a ③ local antes de upload confirmado
E coerência 3×1.

**G5 · Truncamento-com-dado + CHECKPOINTS** (harnesses + c262/c154) — o coração da DI-43:
(a) rito de teto BoTorch = gravar camadas parciais via `write_run_outputs(status='failed',
motivo_parada='teto_wall')` e SÓ então encerrar; critério ELAPSED-only (a projeção do
`_WallClockProjector` vira `log.event('wall_projection_warning')`); (b) **checkpoint atômico
periódico** em TODOS os runners Python: flush do SnapshotBuffer + parquets parciais a cada
**K=25 iterações OU 30 min** (o que vier primeiro), escrita via tmp+rename (`atomic_io`),
sobrescrevendo o checkpoint anterior; na retomada/crash, o dado até o último checkpoint existe.
Teste: matar um run no meio (SIGKILL) ⇒ camadas parciais legíveis + manifesto coerente; run
completo ⇒ saída bit-idêntica à de antes (checkpoint não muda o resultado final).

**G6 · Gates & artefatos** (`scripts/` + `claude_code_context/artifacts/`) — G-1 3×1
(código pronto em `f5/baterias/f54/padrao_zdt4/teste_3x1.py`; controle + = quimera c149) ·
G-2 unicidade/integridade do ⑥ (+`mapa_termino.json`) · G-3 proveniência (`env.executable` ∈
roster de `envs.json` + campanha_id + repo_hash≠'') · G-4 gabarito NORMATIVO de camadas
(`gabarito_camadas.json`; substitui o modal no censo) · G-5 tolerância-⑦ `rtol=1e-4` ·
G-6 não-perturbação por par de runs (flag `--sem-sonda`) · G-7 contrato §6.1 por teste ·
G-8 guarda de suíte anti-escrita em `data/` (+ B-13 teste→tempdir) · G-9 content-hash na
propagação · B-15 discriminador O-22 · `motivos_parada.json` (fonte única portao/accept/censo)
· B-12 commitar os 9 drivers + preflight anti-`data/`-forasteiro · **G6.7 suíte hermética**
(o teste D-03 não consulta mais o bucket real — mock/skip-sem-rede).

**G7 · Instrumentação global Python** — I-02 cronômetro no portão de avaliação
(`src/budget.py:222`) + `export.py` aceita NULL em `tempo_aval_real_s` ("não medi" ≠ "0") +
I-09 `repo_hash` no ⑤ (todos os stacks; no MATLAB via arg do despachante).

**🏁 MARCO G:** suíte verde + preflight 0 + **re-gate das 666 células da rodada-42 com os
gates novos ⇒ DEVE devolver exatamente 1 quimera (c149/q10_ZDT4) e 34 células com assinatura
anômala** — se devolver outra coisa, o GATE está errado (é o teste de aceitação do plano F5).
Após o marco G: **Onda-0 de disparo liberada** — os configs SEM pendência por-algoritmo:
**c149, e81, e7, c238, b3, c141, b1, nsga2, nsga3, moead, smsemoa, treed_media** (12 configs,
incl. o mais caro do estudo, c149/2.811 h-core).

### FASE A — POR ALGORITMO (ordem = horas-de-campanha destravadas, maiores primeiro)

> Cada bloco fecha com: suíte + smoke de 1 célula real + portão VERDE + carimbo
> **DEFINITIVO ✅** no T11_STATUS (= autor pode disparar aquele config nas 30 sementes).

**A1 · c154 (1.537 h-core + batch)** — herda G5 (truncamento/checkpoint; validar numa célula
D≥12: morre às 12h COM camadas parciais) + `params` no ⑤ + doc I-12 (ordem da ③) no CONTRATO.
**A2 · c122 (1.239)** — I-01 metadado `n_ref` do bloco g=1 (o valor REAL da referência usada;
NÃO mudar quando a sonda dispara) + `ref_ids`/ids da população no ⑥ (laudo I-1; molde = b4) +
regra-do-rótulo no sigma_dict (I-2) + `y_treino_dist` (I-5) + `params` no ⑤.
**A3 · família b5 (b5m 2.246 · b5r 218 · moead_media 132)** — I-05: `p_wrong_stats`,
`n_substituicoes`, `flag_vetores_degenerados`, amplitude em float64 no ⑥ (molde b5) + wrapper
read-only no gatilho do `adapt` (b5m-A8, ~8 linhas, NÃO altera o mecanismo!) + `params` no ⑤
(3 configs) + declarar granularidade da ③ no sigma_dict (b5r-A30).
**A4 · c262 (867 + batch)** — herda G5 + 8 hiperparâmetros da acqf no header (T1 do relatório)
+ `params` no ⑤ + `fit_retries>0` vira warning amarelo no ⑥ + **probe de RAM do batch**
(1 célula q10 até o fim OU teto medindo pico de RSS → cravar `--n-jobs` seguro no RUNBOOK).
**A5 · e103 (352)** — `tempo_geracao_s` (I-7) + confirmar o rito da ⑦ do G6/B-08 numa célula.
**A6 · sobol_batch + nsga3 (baratos, 2 itens)** — I-03/I-08-laudo: `n_front1`/`f_best` via
`minimo_comum_di10` + `tempo_fit_s=NULL` correto; nsga3: string `geracoes_derivadas` real.
**A7 · b4 (182)** — regra-do-rótulo no sigma_dict + `y_treino_dist` (ref_ids JÁ loga; NUNCA
inverter p0/p1).
**A8 · e74 (71) — O FIX DI-45** — `ClassifierSelect.m:46-48`: capturar `S = find(y_label==1)`
e selecionar `x_candidate = Parent(S(index(1:num_infill)),:)` (mapear a ordenação de volta ao
índice ABSOLUTO); manter `n_desalinhado` (deve cair a ~0 no regime produtivo — é a PROVA);
re-lacre `anchors.json` + `repos.lock` da árvore e74; smoke 3 células + gate ±3σ; regra-do-
rótulo + `y_treino_dist`.
**A9 · c217 (16)** — `pmid_ids` no ⑥ (laudo I-1; ~2 linhas; `bud.solutionIdOf` como no b4) +
regra-do-rótulo + `y_treino_dist` + `params` no ⑤.
**A10 · c311/treed_media (nota σ)** — I-11: coluna/nota `n_sigma_valido` na leitura da sonda
(doc + 1 linha se barato); guard de tier do treed_media (rejeitar exp fora de sweep-big).
**A11 · SONDA ESTRATIFICADA (D11/I-6; por último — muda O QUE SE MEDE)** — bloco extra de
~500 pontos amostrados perto do arquivo corrente, `regime='sonda_estratificada'`, NUNCA
misturado à régua Sobol; só nos 4 classificadores (b4/c217/c122/e74); gate G-6 de
não-perturbação obrigatório antes do carimbo.

### FASE V — VERIFICAÇÕES & RE-RUNS (pós-código)

**V1** VD-b1 (torneio `EvolALG.m:16` — forense read-only) e VD-b3 (índice `UpdataArchive`) —
relatório, sem mexer em código salvo achado 🔴 (⇒ D81, parar e perguntar).
**V2** Re-runs da s42: `sweep-big-mvns/c311/MMF16_20` + `main/b1/WFG1` (1,17 h-core) ·
substituição da quimera c149 (rota A0: geração noncurrent do bucket; senão cópia do Mac) ·
⑦ correta do e103/medium-lhs/ZDT4 → espelho+bucket (content-hash) · **as ~29 não-ok da s42
re-rodadas sob o regime novo** (D8 — é também o smoke do G5 em células reais).
**V3** Lote de docs da torre (a executar pela torre OU pela sessão se a torre não estiver
disponível): itens do `handoff/T11-PLANO-CONSOLIDADO.md` §6 + §12-📄 (ERRATA A30; número
DI-40; 6 números F5; cards/INDEX; RUNBOOK "~min-1h"; OP-1..7; SPEC L.8 do e74 pós-fix; D7 do
iteration_seed na SPEC §D62; DI-44 nos textos de teto remanescentes).

## §4 · ACEITAÇÃO FINAL DA CAMPANHA T11

1. Suíte ≥410 testes, **0 falhas** (hermética).
2. `preflight` 0 · re-gate das 666: **1 quimera + 34 anômalas, nem mais nem menos**.
3. Smoke de 1 célula real POR CONFIG (24/24) com portão VERDE no regime novo.
4. Kill-test do checkpoint (G5) verde.
5. `T11_STATUS.md` 100% ☑ com hash por item; handoff final em `handoff/T11-<fase>.md`.
6. O AUTOR: tag nova (ex.: `t11-definitivo`) + push + provisionamento (fila D10) → disparo.

## §5 · PROTOCOLO DE SOBREVIVÊNCIA À QUOTA (por que a ordem é sagrada)

Implemente **EM SÉRIE, na ordem do §3**, um item por vez, commit por item. Se a quota morrer:
o próximo agente (outra conta, zero contexto) lê `CLAUDE.md` → esta SPEC → `T11_STATUS.md` e
retoma do primeiro ☐ — nada se perde, nada se repete. NUNCA adiante itens de fases futuras
"porque estava perto"; a ordem existe para que cada carimbo DEFINITIVO ✅ libere experimentos
reais do autor o quanto antes.
