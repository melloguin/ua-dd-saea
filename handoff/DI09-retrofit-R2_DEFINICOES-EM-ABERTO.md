# DI09-retrofit-R2 — DEFINIÇÕES EM ABERTO

> Pontos que **eu decidi para não travar o cartão** (o cartão manda "SIGA
> DIRETO; D81 se ambíguo") mas que são **decisões da torre/autor** e devem ser
> ratificados ou revertidos. Cada um traz o que foi feito, por quê, e o custo de
> mudar. Nenhum deles é decisão de FIDELIDADE (D97) — são de contrato de dados.

---

## A-1 🔴 `acqf_restarts` → `acqf_todos_restarts` (renomeado)

**O que fiz.** Renomeei o campo nos 2 runners para o nome NORMATIVO da SPEC
§S.7.1 / CONTRATO §6.1. Runs PRÉ-retrofit (c154/DTLZ2, c262/ZDT1, c154/ZDT1)
têm a MESMA grandeza sob o nome antigo `acqf_restarts`. A divergência está
documentada no `sigma_dict` dos 2 configs.

**Por quê.** A SPEC é a fonte normativa e o repasse do c154 (§7, linha 399)
pediu explicitamente que a torre confirmasse o rename. Emitir os dois nomes
duplicaria ~340 KB no jsonl do DTLZ2 por pura indecisão.

**Decisão pendente.** (a) ratificar o rename [o que está implementado];
(b) voltar ao nome antigo; (c) emitir os dois durante uma janela de transição.
**Custo de mudar:** 1 linha por runner. A análise R4 precisa tolerar os 2 nomes
de qualquer forma, porque os runs pré-retrofit não serão re-executados.

## A-2 🔴 `tempo_geracao_s` EXCLUI o custo da sonda

**O que fiz.** O wall da geração na ④ é `(fim − início da iteração) − tempo da
sonda`. O custo da sonda vai à parte, em `tempo_pred_sonda_s`. **O projetor de
teto de wall-clock, ao contrário, enxerga o wall CHEIO.**

**Por quê.** São duas perguntas diferentes. A ④ alimenta a curva de
escalabilidade e a comparação de custo entre famílias (§17.6) — incluir a
instrumentação deste estudo contaminaria a medida do *mecanismo*, e pior:
contaminaria de forma DESIGUAL, porque a sonda só roda a cada 2 iterações. Já o
teto de wall-clock é o relógio de parede do operador, que paga a sonda também.

**Decisão pendente.** Ratificar a semântica, e — se ratificada — o CONTRATO §4
merece uma frase explícita (hoje diz só "fit+busca+aval+overhead", que não
resolve o caso). **Custo de mudar:** 1 linha por runner.

## A-3 `tempo_pred_sonda_s` = NULL (não 0) nos runs pré-sonda

**O que fiz.** No ④ backfillado do c154/DTLZ2 a coluna ficou NULL.

**Por quê.** O CONTRATO §4 diz "0 quando não roda", mas isso descreve uma
iteração de um run COM sonda. Num run pré-retrofit não havia grandeza a medir —
gravar 0 afirmaria "a sonda rodou e custou zero", que é falso. NULL diz "não
medido", que é verdade.

**Decisão pendente.** Ratificar NULL para runs pré-sonda (a distinção "0 = rodou
e foi barato" × "NULL = não existia" importa em qualquer agregação).

## A-4 `tempo_geracao_s` do backfill é DERIVADO

**O que fiz.** Reconstruído das âncoras `ts(timing) − tempo_fit_s` do jsonl, e a
procedência gravada no manifesto (`timing_backfill`). Idem o `tempo_busca_s` da
ÚLTIMA iteração (1 de 241), cuja `decision` é o `hard_stop`.

**Por quê.** A alternativa era NULL, e o cartão pede as 241 linhas preenchidas.
O estimador foi calibrado contra as 240 iterações de valor conhecido (erro +8 ms
em ~450 s) e validado por dois agregados independentes do manifesto (§4 do
RELATÓRIO).

**Decisão pendente.** Aceitar dado derivado-e-rotulado na ④, ou exigir NULL onde
não houve medição direta. **Se a torre preferir NULL**, o backfill é
re-executável em segundos (`export.backfill_timing_from_jsonl`).

## A-5 c262/ZDT1 e c154/ZDT1 seguem SEM as colunas novas

**O que fiz.** Nada — o cartão diz "ZDT1: nenhum (teto)".

**O estado real.** c262/ZDT1 tem ④ completa mas `tempo_busca_s` NULL e **o
jsonl do c262 nunca logou a busca por iteração** (0 ocorrências), então o
backfill ali só recuperaria `tempo_busca_s` por derivação de `ts` (não há valor
exato a copiar, ao contrário do c154). c154/ZDT1 abortou pelo teto e só tem
jsonl (sem parquets — aborto limpo, por desenho).

**Decisão pendente.** (a) deixar como está; (b) rodar o backfill derivado no
c262/ZDT1 — recupera `tempo_busca_s`/`tempo_geracao_s` de um run de ~4h sem
re-executá-lo, tudo rotulado como derivado. Recomendo (b) se o custo do ZDT1
entrar na análise R4; é 1 comando.

## A-6 `n_baseline` × `n_train` — a comparação c262 × c154

**Não é decisão minha** (a torre já cravou na DI-11: logar `n_train` no JES).
**Registro um risco de leitura** que a implementação deixou explícito no
`sigma_dict`: **não são a mesma grandeza.** `n_baseline` é o subconjunto PODADO
que a aquisição do qNEHVI enxerga (medido: **7** contra `n_train`=21 na 1ª
iteração do MMF1 — a poda corta ~2/3); `n_train` é o arquivo inteiro. Uma
análise que ponha as duas colunas lado a lado como "tamanho do baseline" vai
concluir que o JES tem 3× mais dados. O `sigma_dict` avisa; um teste unitário
trava o aviso contra refactor.

## A-7 Escopo NÃO coberto por este cartão (herdado do repasse do c154 §7)

Dois itens do repasse não entraram no resumo da DI-11 e **continuam abertos**:

- **`sigma_dict` nos outros 19 configs.** Implementei nos 2 da minha faixa
  (c262/c154). O repasse (linha 402) nota que vale para os 21 — é retrofit-R1 /
  R3, fora da minha faixa.
- **`fe_treino_max`, sonda e mínimo comum DI-10 nos 9 configs MATLAB e nos do
  R3.** Fora da faixa por construção (paralelismo triplo).

## A-8 Nota de manutenção — armadilha do `_nds_filter`

`src/problems._nds_filter` devolve **ÍNDICES**, não máscara booleana. Um
`count_nonzero` sobre ele descarta silenciosamente o índice 0. Isso já custou um
bug nesta sessão (pego pelo teste, antes de qualquer dado ser consumido). Quem
for instrumentar `n_front1` nos demais configs: use `len(...)`.
