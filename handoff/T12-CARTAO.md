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
- [ ] T12.2 · BL-02 flag_vetores_degenerados (fix + prova no DTLZ2/A8)
- [ ] T12.3 · BL-05 y_treino_dist c217
- [ ] T12.4 · BL-06 finalProbe sob teto_wall (c154/c262)
- [ ] T12.5 · BL-09 fflush por linha (MATLAB; ⚠ engine)
- [ ] T12.6 · BL-08 pin scipy (autorização D10 do autor)
- [ ] T12.7 · gates texto→comportamento (2 arquivos)
- [ ] T12.8 · varredura de VALOR de todos os campos T11 (1 teste/campo)
- [ ] T12.D1 · piso de ruído → `piso_ruido.json` + regra no CONTRATO (após OK do autor)
- [ ] T12.D2 · retificação N=20 (após confirmação do autor)
- [ ] REGISTRO A41 (fechamento) + handoff `handoff/T12-FINAL.md`

## §6 · DEFINIÇÃO DE PRONTO DO CARTÃO

Suíte ≥627 + novos, **0 falhas** · cada fix com controle negativo demonstrado (reprovava →
passa) · smokes reais de c217, b5m e 1 célula-teto com os campos carregando VALORES (zero
sentinelas) · as 2 decisões registradas com o veredito do autor · `staleness` 0 · handoff.
**Depois deste cartão: a tag final do autor → fila de infra D10 → DISPARO das 30 sementes.**
