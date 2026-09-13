# T11 — O REFINAMENTO FINAL CONSOLIDADO (torre, 2026-07-29)

> **O que é.** A unificação das DUAS grandes análises — (1) a validação exaustiva de código
> (143 agentes, 64 achados confirmados; REGISTRO A29-A31) e (2) a análise de fidelidade F5
> (666 células, 24 configs, 38 agentes + 14 adversariais; `f5/`) — numa ÚNICA lista-mestra com
> o veredito da torre por item, sob a **doutrina do autor (2026-07-29): "corrigir só o
> essencial; mudar o código o mínimo possível; mas deixá-lo sem nenhum erro."**
> Fonte primária de cada item: `f5/PLANO_RODADA_PERFEITA.md` (B/I/G/E) e REGISTRO A29-A31.

## 0. O CRUZAMENTO DAS DUAS ANÁLISES — o veredito da torre

**As duas análises convergem, se explicam e se corrigiram mutuamente. Nenhuma contradição
material sobreviveu.**

1. **Meus 3 fixes de gate (DI-41/42.1) são os B-05/B-06/B-07 do plano da F5** — reconhecidos
   como "🟡 corrigido no HEAD". O do falso-VERDE **salvou a própria F5** ("foi assim que a
   F5.1 quase começou errada"). A célula que meu B1 desmascarou (`c311/big-mvns`) é
   exatamente a célula que a F5.1 REPROVOU no gate.
2. **Meus achados eram os SINTOMAS; a F5 achou o MECANISMO.** Eu vi: jsonl com 2 escritores
   (moead), teste escrevendo em produção (e81), ⑥ truncado (treed), header duplicado. A F5
   provou a causa única por trás de todos: `is_run_done` sem campanha + `AuditLogger` em
   append cego + escrita não-atômica (o trio B-01/B-02/B-03/B-11) — e mediu: 34/666 células
   com assinatura anômala (5,1%), dano científico real = 1 quimera.
3. **Impacto dos meus achados nos resultados da F5: PEQUENO E JÁ CONTIDO.** Dos meus 64:
   nenhum invalidou config algum; o que tocava dado real (⑦ do e103 dobrada, célula
   mascarada) foi corrigido/excluído ANTES ou PELO gate da F5. A F5 validou a ciência JÁ COM
   os meus fixes aplicados.
4. **O contraditório funcionou nas duas direções:** a F5 REFUTOU 2 afirmações minhas —
   (i) o c122 GRAVA o `fe` no evento sonda (minha DI-42 dizia que não; ERRATA na A30);
   (ii) o número da DI-40 ("~6,3 h/célula queimada") está 4× superestimado (medido:
   0,87–2,99 h, média 1,47 h) — D7 corrige o REGISTRO.
5. **Zero bug de algoritmo nas duas análises, por caminhos independentes** — 143 agentes
   lendo código + 38 agentes lendo dados chegaram à mesma conclusão. A ciência está boa;
   o reparo é todo de plumbing/registro.

## 1. VOLUMES CONSOLIDADOS

| fonte | brutos | sobreviventes ao contraditório |
|---|---:|---|
| Validação de código (143 agentes) | 310 | 64 confirmados (13 ALTA + 51 MÉDIA) |
| Fidelidade F5 (38+14 agentes) | 533 itens estruturados | 16 bloqueadores + 13 instrumentação + 9 gates + 26 decisões (E+D) + 11 vereditos de célula |
| **Deduplicado (esta lista-mestra)** | — | **16 🔧 código-bloqueador · 9 🔩 código-menor · 9 🚦 gates · 12 📄 doc/registro · 10 🗳 decisões · 8 ✅ já-feitos · 14 ❌ não-corrigir** |

## 2. ✅ JÁ FEITO (ação zero)

B-05 status do runner (8e8e966) · B-06 token cache (eb977f2) · B-07 falso-VERDE (eb977f2) ·
⑦-e103 multi-surrogate + 5 regeneradas no Mac (eb977f2) · blindagem dual_write (10d4cf5) ·
eixo da sonda = fe_treino_max no CONTRATO/SPEC (3fbb841) · RUNBOOK --problems/parallel,false/
roster DI-40 (8e8e966) · lote3s.sh --teto-s (operação, 28/07).

## 3. 🔧 T11-CÓDIGO: os bloqueadores (TODOS valem — ~19 h, zero re-execução)

Veredito da torre: **os 13 abertos passam TODOS no critério "só o essencial"** — cada um tem
dano quantificado em 30 sementes e correção pequena (10-60 linhas). Detalhe completo com
evidência/teste em `f5/PLANO_RODADA_PERFEITA.md §1`.

| # | item | dano se não fizer (30 sementes) | custo |
|---|---|---|---|
| B-01 | guarda anti-append no AuditLogger (`audit_log.py:55`) | ~1.020 células c/ ⑥ anômalo | 1h |
| B-02 | no-op não abre o ⑥ (`experiments.py:98`) | ~660 células poluídas + ~270 falsos alarmes | 30min |
| B-03 | `campanha_id` no `is_run_done` (+migração schema ⑤) | smokes/stale-s0 viram resultado oficial | 3h |
| B-04 | gates de proveniência (G-1..G-3) | ~30 quimeras invisíveis | 2h |
| B-05/06/07 | blindar os 3 fixes (testes de regressão + artefato `motivos_parada.json` + exit-2 duro no portão) | regressão silenciosa | 2h |
| B-08 | ⑦ no rito de fechamento + `final_eval` regenera incond. + gabarito NORMATIVO no censo | 1.350 células sem endpoint, invisíveis | 3h |
| B-09/10 | `mirror_run` também no aborto + identidade de execução no blob + não podar ③ antes de confirmar | evidência de ~870 falhas morre com a VM; quimera irrecuperável | 2,5h |
| B-11 | escrita atômica de linha no ⑥ (O_APPEND ≤ PIPE_BUF) | ~180 células ⑥ ilegível | 2h |
| B-12 | commitar os 8 drivers untracked + preflight anti-`data/` forasteiro | disparo fora do controle de versão | 45min |
| B-13 | teste→tempdir + guarda de suíte anti-escrita em `data/` | recontaminação | 40min |
| B-14 | tolerância da ⑦: `rtol=1e-4` (versão simples; NÃO a condition-aware) | ~120 falsos-vermelhos | 30min |
| B-15 | discriminador O-22 (footer ausente ≠ morte se ⑤ ok) | ~270 falsos alarmes | 30min |
| B-16 | lista `NO_RETRY` de falhas determinísticas | ~285 h-core queimados | 40min |

## 4. 🔩 T11-CÓDIGO-MENOR: instrumentação (seletiva — só o que muda leitura de RESULTADO)

| item | veredito | por quê |
|---|---|---|
| I-01 c122 `n_ref` do bloco g=1 | 🔩 SIM (só o metadado) | comparabilidade da sonda g=1; NÃO mudar quando a sonda dispara (mudaria o que ela mede) |
| I-02 `tempo_aval_real_s` cronometrado | 🔩 SIM | análise de custo §17.6 lê 0,0 como "instantâneo" |
| I-05 b5: DI-10 específicos (p_wrong_stats, n_substituicoes, flag vetores_degenerados, amplitude float64) | 🔩 SIM | é o que torna o RESULTADO b5m (D9) auditável nas 30 sementes sem re-run |
| I-07 `params` no ⑤ (7 configs) | 🔩 SIM (já ratificado DI-42.6a) | 197→~6.450 células violando CONTRATO §5 |
| I-08 `mapa_termino.json` | 🔩 SIM | pré-requisito do gate G-2 |
| I-09 `repo_hash` no ⑤ | 🔩 SIM | elo D80 run↔código vazio em 666/666 |
| I-10 ⑤ de batch abortado com q real | 🔩 SIM (família fio-do-q) | metadado errado em toda célula batch abortada |
| I-03 `n_front1` do sobol_batch via mínimo-comum | 🔩 SIM (pequeno) | log do piso do batch 2/10 campos |
| I-13 string `geracoes_derivadas` nsga3 | 🔩 SIM (trivial) | metadado errado em 750 células |
| I-04 ③ ger-1 DESDEO · I-06 p0/p1 · I-11 σ do c311 · I-12 ordem ③ BoTorch | 📄 DOC (regra de leitura/glossário) | mecanismo certo; corrigir o código mudaria dado ou não acrescenta |
| +c262: 8 hiperparâmetros da acqf no header | 🔩 SIM (linhas) | auditabilidade direta |
| +pinar scipy/numpy em envs.json/locks | 🗳 autor (D80) | reprodutibilidade M8 |

## 5. 🚦 GATES G-1..G-9 — TODOS valem (~6 h; 20,5 s de CPU nas 666)

G-1 3×1 inter-camadas (código PRONTO) · G-2 unicidade/integridade do ⑥ · G-3 proveniência ·
G-4 gabarito normativo de camadas · G-5 tolerância-⑦ · G-6 não-perturbação por par de runs ·
G-7 contrato §6.1 por teste · G-8 guarda de suíte · G-9 content-hash na propagação.
É a máquina que transforma "a F5 validou uma vez" em "toda rodada se auto-valida".

## 6. 📄 T11-DOC/REGISTRO (barato, zero risco)

ERRATA A30 (c122 grava `fe`) · correção do número DI-40 (D7: 1,47 h médio) · E-09/D16: os 6
números publicados (χ² pseudorreplicado do moead_media; endpoint e103 200→100/10→5; NÃO
aplicar a "correção" 0,05→0,10) · glossário p0/p1 (NUNCA inverter valores) · regra R4#10
(dominância sobre ① float32 é lossy) · regra de leitura da ③ BoTorch no CONTRATO · lnum do
c217 · assimetria de logging do sobol_batch · O-21 formalizado (falha MATLAB certificada no
footer) · caveats 1-24 da F5 §2.3 → dossiê/dissertação · suíte hermética (teste D-03 não
consulta bucket real) · itens cosméticos herdados (env_c149_fallback lock; data/images;
rótulos ORQUESTRACAO).

## 7. ❌ NÃO-CORRIGIR (consolidado das duas análises — a doutrina aplicada)

Trocar valores p0/p1 (destrutivo) · sonda do c122 pós-truncagem (mudaria a medida) · α por
linha na ③ (re-run por zero info) · re-rodar b5m pela instrumentação (1.123 h-core por nada)
· duplo carimbo b5r isolado · re-disparar sobol_batch pelo n_front1 (recuperável em 5s) ·
mexer no D53/float32 · guard no vendorizado b5 (mudaria o mecanismo = o RESULTADO D9) ·
limpar o ⑥ do e81 (vetado DI-42.2; congelado 444) · "corrigir" fantasia e103 0,05→0,10 (erro
de 2×) · descartar transição ger1→ger2 b5r · campo `fe` em runners MATLAB (DI-42.5b resolveu
por contrato) · condition-aware da B-14 (a simples basta) · células "pulou"/tolerância-⑦/sem-
footer-env_c311 (aprovadas; resolvem-se por B-15/B-14/DI-42.3).

## 8. 🗳 AS 10 DECISÕES DO AUTOR (o que resta da mesa D1-D16 + E-01..E-10)

| # | decisão | recomendação consolidada (F5 + torre) |
|---|---|---|
| T11-D1 | Re-rodar as 2 células reprovadas (c311/big-mvns 0,075h; b1/WFG1 1,09h)? — supersede a quarentena DI-42.2 | SIM, com os fixes B-05/B-11 aplicados (1,17 h-core) |
| T11-D2 | Quimera c149: substituir pela cópia ÍNTEGRA do Mac + re-gate | SIM (0 h; a cópia é provada 2.000/2.000) |
| T11-D3 | e103/medium-lhs/ZDT4: copiar a ⑦ correta (100 linhas) p/ espelho+bucket | SIM (2 arquivos, content-hash) |
| T11-D4 | E-01/D7: batch/c262 SAI do roster M8 (abortou 5/5); main/c154 FICA completo; corrigir o número da DI-40 | SIM às três |
| T11-D5 | E-05: reabrir T10 (rito truncamento BoTorch) p/ o main/c154 D≥12? Math corrigida: (a) queima ~485 h-core p/ zero dado; (b) T10 = ~3.960 h-core COM curva parcial, preenchendo o furo D=12/M=3 onde a tese de escalabilidade se decide | Torre: **(b)**, dentro do T11 (nunca patch avulso). Decisão de custo é sua |
| T11-D6 | E-03/E-04/D6: as 3 falhas reais (c154×2, c262/WFG1) + b1/DTLZ4 — defeito ou limitação? | Decidir PELA REFERÊNCIA config a config; default = (a) resultado/limitação (zero código, zero quebra de comparabilidade) |
| T11-D7 | D15: `iteration_seed` ganha a CÉLULA no M8 (n efetivo 1→45 por config no offline)? | Ciência pura, SUA — a torre nota: muda streams ⇒ s42 offline não é réplica exata do M8; se sim, declarar no protocolo |
| T11-D8 | D5: publicar as 29 não-go como taxonomia/resultado (95,8% com honestidade) | SIM (rec. F5) |
| T11-D9 | D10/D11/D12: régua por FAMÍLIA (com o freio dos 17,7%) · endpoint offline = ⑦ · caveat tier-small do c311 | SIM às três (dissertação) |
| T11-D10 | E-02: SUB-varN antes do disparo (DI-39) · E-07 datasets 29 sementes · E-10 provisionar env_b5/c311/e81 em Linux · F0: commitar 8 drivers + CRIAR A TAG (nunca existiu) + backup imutável | Pré-requisitos: executar todos |

## 9. SEQUÊNCIA (a do plano F5, adotada)

F0 higiene → F1 bloqueadores (~19h) → F2 instrumentação seletiva (~5h) → F3 gates (~6h) →
F4 validação do reparo (suíte ~410 + smoke 21 configs + **re-gate das 666: deve devolver
EXATAMENTE 1 quimera e 34 anômalas** — se devolver outra coisa, o gate está errado) →
F5-mesa (as 10 decisões acima) → F6 re-runs (1,17 h-core + I/O) → F7 provisionamento (CAMINHO
CRÍTICO — dias) → F8 SUB-varN → F9 DISPARO das 30 sementes.
**Total de engenharia: ~30-37 h em 1-3 cartões de implementação + validação da torre.**

## 10. RASTREABILIDADE — os "~40 itens" da validação de código (A30) neste plano

Prestação de contas (pergunta do autor, 2026-07-29): **nenhum item se perdeu**. Destino:

| grupo dos ~40 (A30) | destino no T11 |
|---|---|
| Campos contratuais do ⑥/⑤ (params, DI-10 do b5, n_front1, sigma_dict) | 🔩 I-07 / I-05 / I-03; o `fe` da sonda RESOLVIDO por contrato (DI-42.5b) |
| teste→tempdir + poluição do ⑥ | 🔧 B-13 |
| manifesto de batch abortado com q=1 | 🔩 I-10 |
| células stale de semente 0 (force) | 🔧 B-03 (campanha_id resolve de raiz) + §4-item-5 |
| datasets de sweep p/ 29 sementes | 🗳 T11-D10 (pré-requisito) |
| probe de RAM do c262 batch | SUPERSEDED por T11-D4 (c262 fora do batch) |
| resume/⑦ do e103 | 🔧 B-08 |
| suíte hermética (teste D-03 consulta bucket real) | 📄 §6 + guarda B-13 |
| docs (e7_sonda.m; §3.2 pisos; teto-MATLAB; ⑦×teto-c311; cosméticos) | 📄 §6 |
| **4 itens que estavam FORA e entram agora (adição desta seção):** | |
| Guard de tier no `treed_media` (aceita qualquer exp) | 🔩 NOVO (5 linhas) |
| Roster/exp-default do e103 no `experiments.m` (bateria main criaria 750 runs fantasma) | 🔩 NOVO (guard 2 linhas) |
| Testes-lacuna seletivos: straddle do e81 (dispara na bateria com cache-hits reais — e81 FICA no batch M8) + smoke D74/BBOB do e74 | 🔩 NOVO (~2h) |
| Preflight confere content-hash das âncoras (c141 com 1/6) | 🔩 NOVO (barato) |
| **4 itens REBAIXADOS a risco-aceito (❌), com o porquê:** | |
| Guard de predição RBF não-finita (c141) | log-only em runner MATLAB por evento nunca observado; os gates de integridade pegam a célula se ocorrer |
| NaN-guard dos passos 2..q do lote (c262) | MOOT — c262 saiu do batch (T11-D4); no main q=1 o caminho não existe |
| Crash latente n_front=1 do c238 | aceito e registrado desde a R1; F5 observou n_front=2 sem crash; corrigir mudaria runner por evento raro |
| Semântica do CACHE_CAP (conta gerações-com-hit, não 0-FE-puro) | comportamento sancionado; vira nota de doc, não código |

## 11. LAUDO DE INSTRUMENTAÇÃO DA F5 (`handoff/F5-LAUDO-INSTRUMENTACAO.md`) — 8 itens + a refutação da torre

O autor pediu à F5 um diagnóstico do NÍVEL de instrumentação (não de fidelidade). Veredito da
F5: **8,5/10** — completa para regressores e para provar mecanismo; incompleta para a análise
COMPARATIVA de classificadores. Os 8 itens (I-1..I-8 do laudo; **numeração distinta** dos
I-01..I-13 do PLANO_RODADA_PERFEITA) entram assim no T11:

| item do laudo | veredito da torre | destino |
|---|---|---|
| **I-1 🔴 logar `pmid_ids`/`ref_ids`** (c217, c122; b4 já faz) | 🔩 **SIM, mas NÃO é bloqueador — a F5 superestimou: NÃO é irrecuperável.** Refutação medida pela torre (abaixo) | T11-código-menor (~2 linhas/config) |
| **I-2 🔴 declarar a REGRA do rótulo no `sigma_dict`** | 📄 **SIM — é o item de maior valor/custo do laudo** (a acurácia publicada varia 0,35↔0,995 conforme a regra; hoje não está escrita em lugar nenhum) | T11-doc (custo ~0) |
| I-3 🟠 cronômetro no portão Python + permitir NULL | 🔩 SIM — **é o I-02 do outro plano** (mesma causa: `budget.py:222`) | dedup |
| I-4 🟠 lista `NO_RETRY` | 🔩 SIM — **é o B-16** (dedup) | dedup |
| I-5 🟠 `y_treino_dist` (prevalência das classes no treino) | 🔩 SIM (~1 linha × 4 configs) — separa "classificador ruim" de "problema desbalanceado" | T11-código-menor |
| **I-6 🟡 sonda estratificada p/ classificadores** | 🗳 **DECISÃO NOVA DO AUTOR (T11-D11)** — muda o que a sonda mede; ver §8 | mesa |
| I-7 🟡 `tempo_geracao_s` no e103; `tempo_fit_s` no sobol_batch | 🔩 SIM (~2 linhas) | T11-código-menor |
| I-8 🟡 `n_front1`/`f_best` no sobol_batch | 🔩 SIM — **é o I-03 do outro plano** (dedup) | dedup |

### ⚖ REFUTAÇÃO DA TORRE ao I-1 ("irrecuperável a posteriori") — MEDIDA, não opinião

O laudo afirma que sem os ids "o rótulo verdadeiro não é reconstituível — irrecuperável". **É
falso para os dois configs**, e a prova está no código e nos dados:

- **c217:** `PCSAEA.m:39` — `[Input,Output,Pa,Pmid] = CalFitnessPC(Population.objs,
  Population.decs, Problem.FE/Problem.maxFE)`. Verificado: `CalFitnessPC.m` tem **ZERO**
  chamadas de RNG (`grep -c "rand|randn|randperm"` = 0) ⇒ é uma função DETERMINÍSTICA da
  população + razão de orçamento. E a ② grava `(geracao, solution_id)` — medido em
  `main/c217/ZDT4/42`: **37.114 linhas, 182 gerações**. Com ②+①+`fe` do ⑥, o `Pmid` de
  qualquer geração é **recomputável**.
- **c122:** `MU = len(ref_points)` (`c122_thetadeadp.py:641`) são os **vetores de decomposição
  Das-Dennis FIXOS** (11 em M=2, 15 em M=3), deriváveis de M — não indivíduos cujos ids se
  perderam. A referência do classificador é a população selecionada
  (`pop = sel_scalar_dea(pop + [escolhido], MU)`, `:826`), cujos ids estão na ②
  (medido: 2.100 linhas).

**Consequência para a doutrina "mínimo de mudança":** o I-1 **deixa de ser bloqueador** e vira
conveniência de alto valor — 2 linhas por config que eliminam o risco de uma reimplementação
divergente de `CalFitnessPC` na fase de análise (R4). Recomendo FAZER (é barato e remove risco
analítico), mas registrando que **não** é o item crítico que o laudo pintou.

### T11-D11 (nova) — a sonda dos classificadores deve ganhar um bloco estratificado?

**Contexto.** A sonda são 2.000 pontos Sobol por bloco. Pontos aleatórios quase nunca são
"bons": prevalência **0,4%** ⇒ ~8 positivos por bloco ⇒ precision/recall instáveis (o AUC é
robusto e já funciona: 0,72–0,92 no b4).
**Opções.** (a) manter 2.000 Sobol puros — régua perfeitamente comparável, métricas de
classe instáveis; (b) **acrescentar** ~500 pontos amostrados perto do arquivo corrente, com
`regime='sonda_estratificada'` (nunca misturado com a régua) — destrava precision/recall/F1,
mas o bloco novo NÃO é comparável entre algoritmos e aumenta o volume da ③; (c) subir para
3.000 Sobol — quase não ajuda (a prevalência não muda, só o n).
**Recomendação: (b)**, alinhada com a F5 — **mas com a ressalva da torre**: é o único item de
todo o T11 que **muda o que a instrumentação MEDE** (os demais mudam o que ela REGISTRA), então
exige gate de não-perturbação (G-6) e nota explícita no CONTRATO §17.2.2.

## 12. A CAÇA HISTÓRICA (7 caçadores, 362 pendências) + A MESA DEFINITIVA T11-D1..D13

**Varredura completa do histórico** (REGISTRO A1-A32, SPEC, cards, handoffs, ORQUESTRACAO,
PROGRESSO, DOSSIE, F5): 362 pendências → **144 RESOLVIDAS + 52 SUPERSEDED** (verificadas) +
166 abertas brutas → dedup → o que segue. Incorporado ao plano:

**Trabalho novo absorvido (sem decisão):**
- 🔩 **OP-6 — higiene do `--force`**: re-run sobre célula com parquets órfãos de aborto
  anterior produz ESTADO HÍBRIDO (quimera local) — o force deve limpar os artefatos da célula
  antes de re-executar (parente do B-03/B-10)
- 🔩 e2e de aborto (DI-23.4, adiado desde o R3-c149) → vira o TESTE do B-05 (teto_s pequeno)
- 🔩 fallback-footer no `is_run_done`/censo quando ⑤ ausente (O-21/E-04) → dobra no B-15
- 🔩 regen do `runs_matrix.csv` pós-D4 (as 150 linhas c154-batch + eventuais c262-batch)
- 📄 lote de doc herdado: cache_root (B5 do DI-05, divergência tabela-K×L.10 desde 18/07) ·
  baixas do c154 (MatheronPathModel-seed inexistente no 0.18.1; uso_id do optimize_acqf) ·
  `cards/INDEX.md` stale (5 cartões) · cabeçalhos PROGRESSO/ORQUESTRACAO · número "~min-1h"
  do RUNBOOK (4× errado) · OP-1..OP-7 do registro de operação (incl. o rompimento deliberado
  do teto 48h na janela final e a atribuição mista do c238) · prosa dos 6 relatórios F5 +
  scores_f53.csv revisto + cabeçalho do RELATORIO_F5 · nota N_efetivo (só nsga2/smsemoa=20)
- ❌ novos não-corrigir (doutrina): `load_sonda` triplicado (gatilho da D-18 ATINGIDO e
  RECUSADO — refactor sem efeito em resultado) · fix central do `emit_sonda_block` (DI-28.6,
  opcional) · q=None no dict de retorno do c149 (cosmético) · sweep q=20 (V-B.4) DESCARTADO
  formalmente · A3/B4 do DI-09 e D98/D99/multiplicidade-§14 = camada R4 (autor, pré-análise,
  não bloqueiam M8 — registrados como FUTURO)

### A MESA DEFINITIVA — 13 decisões (renumerada; supersede o §8)

D1 re-run das 2 reprovadas · D2 quimera c149 (rota A0: checar geração noncurrent no bucket
ANTES da cópia do Mac) · D3 ⑦ e103→bucket · **D4 roster batch do M8 (AMENDADA: o caçador
achou o contra-argumento científico — remover c262 deixa o sub-estudo batch com 3/5 configs;
alternativa nova (c): manter batch/c262 COM o rito T10 = curvas parciais de 12h também no
batch)** · D5 T10 · D6 falhas reais = defeito ou limitação · D7 iteration_seed por célula ·
D8 taxonomia das 29 · D9 dissertação (régua família + endpoint ⑦ + tier-small + b5m-A8
resultado + homologação em bloco dos enquadramentos F5.4) · D10 pré-requisitos (fila: SUB-varN
· datasets 29 sementes · envs Linux · TAG · 9 drivers · lib gcs env_c311 · pins scipy/numpy ·
enable_bucket+validação D-03 com credencial real) · **D11 sonda estratificada (laudo I-6)** ·
**D12 fechar FORMALMENTE a DI-07b do e74 (aberta desde 18/07! rec: NÃO promover o fix — a F5
quantificou [eq.7-8 inerte em 87,8%] e você aprovou 9,0 aceitar+caveat; doc-sync da SPEC L.8
que ainda promete promoção) + b3 `adapt_delta_V` (rec: documentar como não-emitido)** ·
**D13 verificações dirigidas órfãs — quais rodar (rec: SÓ as 2 do teto-T: b1-torneio
EvolALG.m:16 e b3-índice UpdataArchive; nsga3-D88, c141-WFG5 e sobol_batch-5cel = NÃO)**

## 13. DEVOLUTIVAS DO AUTOR (2026-07-29) — DI-43 — e o que muda no plano

**Ratificações:** D1-D3 ✅ · D6-D7 ✅ · D11 ✅ ("aplique TODAS as melhorias de instrumentação",
incl. sonda estratificada dos classificadores). **D9/D10/D12/D13 aguardam re-explicação.**

**D4+D5 = DI-43 (a mudança de regime; SPEC §5.1 atualizada, bundles regen):**
- **Teto experimental = 33 h** (118.800 s; era 12 h).
- **Roster 100%**: 695 células × 30 sementes — as 5 c154-batch VOLTAM (DI-40 revertida
  p/ o roster); c262-batch FICA; nenhuma célula sai por custo.
- **Truncamento-com-dado universal** (T10 vira obrigatório e é o rito único do stack Python):
  rodar até completar OU 33 h por RELÓGIO; teto ⇒ `failed/teto_wall` + camadas parciais.
  Aborto-por-projeção EXTINTO (projeção = warning).
- **Outputs intermediários (requisito NOVO)**: checkpoint atômico periódico das camadas nos
  runners Python (cadência a definir no cartão; proposta da torre: flush a cada K iterações
  OU X minutos, escrita atômica via tmp+rename; MATLAB fora — células ≤4 h).
- **D8 revisada**: TODAS as ~29 células não-ok da s42 re-rodam sob o regime novo (vira também
  o smoke de aceitação do T10/checkpoint em células reais).

**Trabalho NOVO que a DI-43 cria (entra nos cartões):**
1. T10 expandido (rito de truncamento em TODOS os runners BoTorch + critério elapsed-only).
2. Checkpoint intermediário (design + implementação + teste de crash-recovery).
3. `--teto-s` default 43200→118800 + RUNBOOK/drivers/SPEC-refs.
4. **Probe de RAM do c262-batch VOLTA a ser obrigatório** (E-08 des-superseded: com o c262
   de volta ao batch, o OOM em n=669 precisa de mitigação — medir e dimensionar --n-jobs).
5. Dispatch/rosters completos (o RUNBOOK que tirava c154 do batch é revertido).
6. Custo da campanha re-projetado: base 10.173 + **~12-17 mil h-core** das células que antes
   abortavam baratas e agora rodam até 33 h ⇒ **E-10 (envs Linux/VMs) vira ainda mais crítico**.
