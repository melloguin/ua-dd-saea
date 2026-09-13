# HANDOFF T12 — o acabamento final (2026-07-31)

**De:** sessão de implementação T12 · **Para:** o autor (e a próxima sessão)
**Cartão:** `handoff/T12-CARTAO.md` · **Registro:** `REGISTRO_DECISOES_IMPLEMENTACAO.md` PARTE A41
**Estado:** 8 de 10 itens do checklist fechados · **1 decisão do autor em aberto (T12.D1)**

---

## 1. Em um parágrafo

Fechei os 8 bloqueadores da validação de fidelidade do T11 e converti os gates decorativos. A
doutrina do cartão — *todo fix exige controle negativo, todo campo exige asserção sobre o VALOR
medido em run real* — foi cumprida em **todos** os itens, e ela **pagou**: a conversão dos gates
achou o **BL-03** no primeiro disparo e a varredura de valor achou o **BL-04** e o **BL-15**, três
defeitos que não estavam na minha lista de tarefas. Em compensação, **um bloqueio da lista não
sobreviveu à medição**: o BL-09 pedia `fflush(fid)`, e `fflush` não existe no MATLAB — aplicá-lo
derrubaria todo run da campanha. Suíte: **627 → 671, 0 falhas**.

---

## 2. O placar, item por item

| item | bloqueio | commit | prova de VALOR em run REAL |
|---|---|---|---|
| T12.1 | BL-01 `pmid_ids` do c217 | `f524bc4` | **426/426 com id ≥ 0** (era 426/426 = −1) |
| T12.2 | BL-02 `flag_vetores_degenerados` | `2a28e02` | **381/381 não-nulo** (era 0/1.144) |
| T12.3 | BL-05 `y_treino_dist` | `79c9282` | 42/42 com `n = \|TrainIn\| ≠ \|Input\|` (era `(0,0,n)`) |
| T12.4 | BL-06 finalProbe sob teto | `c9969a0` | bloco final na iteração truncada; ①②③ bit-idênticas |
| T12.5 | BL-09 `fflush` MATLAB | `a4e6ef8` | **não aplicado** — ver §4 |
| T12.6 | BL-08 pin do `scipy` | `219bcba` | pin × 3 artefatos + sha256 do lote de Owen |
| T12.7 | gates texto→comportamento | `8acff69` | **BL-03**: 11.000/11.000 com `pred_score` |
| T12.8 | varredura de VALOR | `d17644a` | **BL-04** e **BL-15**: ⑤ do c217 corrigido |
| T12.D2 | N=20 (DI-39 prevalece) | `a81608d` | 3 textos varridos + PARTE A41 |

**Todos os 8 fixes têm o controle negativo DEMONSTRADO** (rodei cada teste novo contra o fonte
pré-fix e registrei a reprovação): `[-1,-1,-1,-1] != [2,6,10,14]` (T12.1) · 2 falhas + 2 erros
(T12.2) · `KeyError: 'classe_melhor'` (T12.3) · `3 not found in [1, 2]` (T12.4) · 1 falha + 1 erro
(T12.6) · 5 falhas + 1 erro (T12.8).

---

## 3. Os 3 defeitos que a doutrina do cartão achou sozinha

Não estavam na lista de tarefas; apareceram porque os gates passaram a medir valor.

**BL-03 · c122 — o score do classificador ia para a coluna do regressor.**
`emit_sonda_estratificada` não ramificava por `pred_tipo`, ao contrário da função irmã
(`emit_sonda_block`), cuja própria docstring exige: score/classe vão para `pred_score`, *"NUNCA
para mu_*/sigma_*, que significam outra coisa e envenenariam a leitura da ③ pela R4"*. Com o
default do emissor sendo `'score'`, o `e(z)` par-a-par do c122 ia para `mu_0` e a confiança para
`sigma_0`, com `pred_score` NULL em **10.500/10.500** linhas. Depois do fix, no smoke real
`main/c122/MMF1/s42`: **11.000/11.000** com `pred_score` e `pred_confianca` preenchidos.

**BL-04 · os 5 offline — o ⑤ publicava o tempo de INGESTÃO como custo de avaliar.**
A carga do dataset empurra as n linhas do artefato pelo portão de avaliação (para atribuir
`solution_id` e esgotar o orçamento) e o cronômetro do I-02 contava aquilo: **0,0003 s** medido no
b5m/DTLZ2. Na s42 o campo era `0.0` exato — o I-02 trocou um número errado por outro.
`FEBudget.descarta_cronometro_de_aval()` zera relógio **e contador**: zerar só o relógio devolveria
`0.0`, que é a afirmação *"avaliar custou zero"* — o sentinela que o I-02 nasceu para matar.

**BL-15 · o `params` do ⑤ do c217 — 3 afirmações falsas.** Não era sentinela; era erro declarado,
que é pior: o §15.7 manda o validador cruzar o `params` com o paper, e para o c217 isso devolvia
*"confere, 20/20"* — falso nas duas direções (o stock roda `{1,15,1,5}` e a SPEC §567 diz que Balde
C não se aplica). Também `treino` dizia "do arquivo" (vem da POPULAÇÃO) e `surrogate` dizia alvo
ternário (é BINÁRIO `{1,2}`). As 3 corrigidas e provadas no ⑤ de um run MATLAB real.

---

## 4. BL-09: o bloqueio não sobreviveu à medição — e é o item que mais precisa da sua leitura

O engine MATLAB estava disponível nesta máquina (R2025a), então os dois modos de perda foram
**medidos** em vez de aceitos:

1. **`fflush` NÃO EXISTE no MATLAB** (`exist('fflush') = 0`; a chamada levanta `Undefined
   function`). O `jsonl_line` **não tem `try/catch`** — a "1 linha" prescrita derrubaria todo run
   MATLAB da campanha. É função do Octave.
2. **Perda de cauda: REFUTADA.** Uma linha de **64 B** sobrevive a `kill -9` com o processo em
   busy-loop. O `fprintf` para arquivo em `'a'` não é bufferizado — não há o que descarregar.
3. **SPLICE: CONFIRMADO, e o fix é ATOMICIDADE, não flush.** 4 escritores × 300 linhas de 6,4 KB
   (a maior linha real medida num ⑥: `main/b1/MMF1/42` = 6.442 B):

   | writer | linhas partidas |
   |---|---:|
   | `fprintf` (produção) | **30** |
   | `fwrite` | **26** |
   | `java.io.FileOutputStream` (append) | **0** |

   Em 5 repetições do caso de produção: **bytes SEMPRE 7.765.968 e newlines SEMPRE 1.200**, com
   0/10/36/20/10 partidas. **Nada se PERDE** (o append do B-11 continua valendo); o que o `fprintf`
   não garante é a **fronteira** da linha.

**Não troquei o writer.** O splice exige ≥2 escritores no mesmo ⑥, e hoje o ⑥ do MATLAB tem
escritor único: o `experiments.py` despacha só o roster Python e os workers de `parfor` escrevem
células distintas. Trocar o writer dos 13 configs MATLAB na véspera da tag custa mais do que o
risco que remove. **A decisão é sua** — ver §6(d).

---

## 5. A cadeia A8, medida em célula real pela primeira vez

O `flag_vetores_degenerados` era o campo que a F5 pediu para fechar o laço do congelamento do b5m
e que a T11 entregou morto (`None` em 1.144/1.144, por `AttributeError` engolido). Com o fix — os
vetores vivem no **evolver** (`BaseEA.py:182`), não no `problem`, que tem **0 ocorrências** do
atributo — dois smokes reais dão o par de controle que nunca existiu:

| célula | `n_norma_zero` | normas | `n_substituicoes` | `P_wrong.max` |
|---|---|---|---|---|
| `off/b5m/DTLZ2/s42` (SADIA) | **0** em 381/381 | ≈ 1,0 | 3–12/ger. (**Σ 7.769**) | até **1,0** |
| `off/b5m/DTLZ3/s42` (CONGELADA) | **105 de 105** em **381/381** | **0,0** | **0** | **0,0** |

A cadeia inteira — `adapt` → norma 0 → PBI NaN → `P_wrong ≡ 0` → zero substituições — deixa de ser
inferência de bancada e vira leitura direta do ⑥. **Fecha também o BL-22** (o smoke da célula
congelada do b5m, que nunca existira).

⚠ **O cartão errou o alvo e o dado prevaleceu.** Ele esperava `n_norma_zero > 0` no **DTLZ2**; o
DTLZ2 é célula **sadia**. As congeladas são **DTLZ3** (380/380 transições) e **DTLZ1** (370), como
`f5/t11/relatorios_config/b5m.md` já registrava. Rodei o DTLZ3 e o controle positivo saiu.

---

## 6. O que fica ABERTO — nada disto foi decidido sozinho (D81)

**(a) `moead_media` no T12.2.** O cartão diz *"vale para b5m/b5r/moead_media"*, mas no
`src/piso_offline.py` o campo **nunca foi escrito** (0 ocorrências de `reference_vectors`) — não há
o que "apontar ao evolver". É **item novo**, não conserto, e acrescenta chave ao ⑥ de um config
cujo contrato foi fechado (o clássico "gate vermelho misterioso", 6 sítios de fiação). Medido a
favor: o `MOEA_D` (mode 12) **tem** `reference_vectors` (`MOEAD.py:111`), então o contraste
piso × b5 sobre a causa do A8 seria mensurável. **Recomendação: fazer, com smoke + portão, se você
autorizar antes da tag.**

**(b) Contaminação de estado global entre teste-com-mock e run REAL — PRÉ-EXISTENTE.** Um run REAL
de c262 no MESMO processo em que já rodou
`tests/test_batch_q10.py::TestCalibracaoBatchT9::test_c154_call_site_usa_o_helper_nao_hardcode`
morre com `ValueError: torch.cat(): expected a non-empty list of Tensors`. **Reproduzido com o fix
do BL-06 desfeito** ⇒ não é desta campanha; ficou visível porque este é o primeiro cartão a rodar
célula real dentro da suíte. **Risco para a campanha: nenhum** (1 célula = 1 processo).
**Mitigação adotada: todo teste que roda célula real vai em subprocesso** — é a regra que produziu
os smokes do T11 e é como a campanha roda. Recomendo mantê-la nos testes futuros.

**(c) `flag_vetores_degenerados` ainda é colhido no replay pós-busca** (`b5_prob.py:536`) ⇒ valor
CONSTANTE nas gerações, contra o que o comentário do próprio código promete. ~3 linhas
(acumulador módulo-nível com chave `gen_count`, o padrão já validado do `P_WRONG_STATS`). Sem ele o
campo não distingue congelamento TOTAL de PARCIAL ao longo do tempo — 649 das 2.237 transições.

**(d) O writer ⑥ do MATLAB não é atômico por linha** (§4). **Recomendação: NÃO trocar antes da
tag.** Trocar SE você pretender: (i) dois processos na mesma célula, (ii) qualquer co-escritor
Python no ⑥ do MATLAB, ou (iii) duas máquinas gravando a mesma célula. O caminho é local:
`jsonl_write(fid, linha)` com `java.io.FileOutputStream(fopen(fid), true)` — o `fid` continua sendo
a identidade que os 19 sítios já passam e todos os guards `fid > 2` seguem valendo. ⚠ O comentário
do `jsonl_open` (B-11) descreve um co-escritor Python "durante a chamada MATLAB" que **não existe
na arquitetura de hoje**; vale corrigir junto.

**(e) O `numpy` do env_main segue solto** (`>=2,<3`) enquanto o BL-08 exige o par
`numpy 2.4.6` **+** `scipy 1.17.1`. Pinei só o scipy porque só ele estava autorizado (fila D10).
Com o numpy solto, o pip das VMs pode resolver 2.5.x e o pin do scipy protege metade do par.

**(f) T12.D1 (BL-07) — o piso de ruído: A DECISÃO EM ABERTO.** Ver §7.

---

## 7. T12.D1 — o piso de ruído com 9 máquinas (aguardando você)

**Medido nos 15 pares Mac×vm3** (`f5/t11/baterias/c141/t12_piso_maquina.csv`):

* **7 pares são bit-idênticos** (Δ = 0,0): `b4` · `c217` · `moead` · `nsga2` · `nsga3` ·
  `smsemoa` · `e103`. O padrão é mecanístico: **são exatamente os configs que NÃO ajustam
  surrogate por otimização numérica.**
* **8 divergem**, **6 acima do piso O-18 (HV ≤ 1,55%)**: `e74/DTLZ2` 10,16% · `c238/MMF1` 9,69% ·
  `e74/ZDT1` 3,54% · `e74/MMF1` 2,93% · `c141/MMF1` 2,31% · `b1/MMF1` 2,10%.
* **Em IGD+ — o endpoint PRIMÁRIO (D70) — o piso declarado nem existe**, e é lá que está o pior
  número: `c238/MMF1` **80,03%**.
* **Causa** (torre): no `c238/MMF1`, código/MATLAB/`doe_hash` idênticos e init bit-idêntico, mas
  **todos os 40 infills divergem**, nascendo no 1º fit do GP (θ 992,18 × 718,37,
  Δ lnL 9,8e-05 nat). Amplificação caótica de diferença de arredondamento — irreparável por código.

**O que muda com 9 máquinas** (Mac + VM1/2/3/4/7/10 com MATLAB, VM5/VM6 Python-only): a máquina
deixa de ser ruído e vira **confundidor correlacionado com o config** (as máquinas Python-only
puxam os 11 configs Python), e se as 30 sementes de um config se espalharem, contamina também a
**variância dentro do config** — as barras de erro da R4, não só os contrastes.

**Recomendação levada ao autor:**
1. **Bloquear por (problema, stack)** — toda comparação da R4 é *config A × config B no mesmo
   problema*; com o problema inteiro de um stack numa máquina, o contraste vira intra-máquina e o
   confundidor **some por construção**. São 25 problemas × 2 stacks = **50 blocos** para 9 máquinas.
2. **`artifacts/piso_ruido.json` por (config, problema), com piso de HV E de IGD+**, como rede de
   segurança para re-runs e spillover — e porque **7 configs têm piso 0** e podem ser escalonados
   livremente.
3. **2 células-calibradoras em cada uma das 9 máquinas** (`c238/MMF1/s42` e `e74/DTLZ2/s42`, as
   duas piores) — ~18 células, custo desprezível, e dão a impressão digital de cada máquina em vez
   de extrapolar um piso Mac×vm3 para 7 máquinas nunca medidas.

---

## 8. Como reproduzir qualquer número deste handoff

```bash
cd /Users/gmello/Documents/python_repos/mestrado/ua-dd-saea
PY=/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python
$PY -m unittest discover -s tests        # esperado: Ran 671 · OK (skipped=31)
```

Os testes novos (todos com controle negativo embutido):

| arquivo | o que tranca |
|---|---|
| `tests/test_t12_c217_instrument.py` | roda o `c217_instrument.m` em **MATLAB real** + 2 mutantes |
| `tests/test_t12_b5_vetores.py` | a cadeia A8 sobre a classe `ReferenceVectors` **vendorizada** |
| `tests/test_t12_teto_sonda.py` | célula c154/c262 **real** truncada em iteração ímpar (subprocesso) |
| `tests/test_t12_jsonl_matlab.py` | writer ⑥ **real** extraído do `experiment.m`: durabilidade + atomicidade |
| `tests/test_t12_pin_scipy.py` | pin × 3 artefatos + scipy instalado + sha256 do lote de Owen |
| `tests/test_t12_valores_t11.py` | `tempo_aval_real_s`, `params` do c217, `n_front1`/`f_best`, `repo_hash` |

⚠ Os testes MATLAB **pulam limpo** onde não há engine, e os de célula real rodam em
**subprocesso**. Rodar a suíte nas VMs Linux **re-mede** as propriedades dependentes de plataforma
(§4) — se a libc de lá bufferizar, o BL-09 volta, agora com o fix certo já identificado.

---

## 9. Próximo passo

**Nada bloqueia a tag exceto a sua decisão do T12.D1** (§7) e, se quiser, os itens (a)/(c)/(e) do
§6. Depois: tag final → fila de infra D10 → disparo das 30 sementes.
