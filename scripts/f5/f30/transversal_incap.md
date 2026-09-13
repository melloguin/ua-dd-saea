# CONSOLIDAÇÃO DAS INCAPACIDADES — m8 (medido em 15/08/2026, READ-ONLY)

## 0. ACHADO ESTRUTURAL: as 209 "fail" do censo são TRÊS coisas diferentes

Reli o rodapé do ⑥ das **209** células `fail` (não o manifesto). Aplicando O-21:

| classe | n | critério medido |
|---|---|---|
| **incapacidade** (erro do algoritmo) | **157** | rodapé com `erro`/`stack` |
| **interrompida sem rodapé** | **51** | nenhum rodapé; último registro é `b4_gen`/`sonda`/`timing` normal |
| **ambiente** | **1** | `erro_Forbidden` (sobol_batch, IAM do bucket) |

Censo reclassificado (15.129): **ok 14.419 · ⚪ teto_wall 501 · incapacidade 157 · interrompida 51 · ambiente 1**.

**A taxa de falha algorítmica real é 157/15.129 = 1,04%, não 209 (1,38%).** Misturar as 51 infla a incapacidade em 32%.

### Por que as 51 não são falhas (prova por fronteira de espelho)
Calculei o `mtime` máximo do espelho por VM (= instante da cópia) e comparei com o último `ts` de cada célula:

```
matlab-vm1  fronteira 2026-08-14 23:20:57 UTC
matlab-vm5  fronteira 2026-08-14 23:20:16
matlab-vm10 fronteira 2026-08-13 22:59:41
matlab-vm3  fronteira 2026-08-13 22:59:36
matlab-vm2  fronteira 2026-08-13 22:57:14
matlab-vm4  fronteira 2026-08-13 23:00:10
```
**29 das 51 têm último registro a <15 min da fronteira do próprio espelho** (18 a <1 min; 4 com delta NEGATIVO). Estavam **em voo quando a cópia foi feita** — é corte de snapshot, não morte. Confirma e estende o §0.3 do LAUDO_D0 ("16 em voo"): são 29, e continuam sem rodapé no canônico, ou seja **não pousaram**. As outras 22 (grupo vm1/vm5 semente 7, 13/08 23:06–23:08) pararam com o espelho ainda ativo por +24h → morte real de processo, mas **sem exceção registrada** (não é erro de algoritmo).

Verificação cruzada: das 51, **só 1 tem cópia com rodapé em outra VM** (ver E1). As 50 restantes estão truncadas em todas as cópias.

---

## 1. MATRIZ 22×25

Gerei 5 matrizes (CSV, uma célula por par):
- `/private/tmp/claude-501/-Users-gmello/33c29160-6eb6-4277-a041-db4855486063/scratchpad/M_ok.csv` (n_ok)
- `.../M_teto_wall.csv` · `.../M_incapacidade.csv` · `.../M_interrompida.csv` · `.../M_tentado_efetivo.csv`
- `.../MATRIZ_util_sobre_tentado.csv` (útil = ok+⚪, sobre tentado efetivo = presentes − interrompidas)
- `.../censo_classificado.csv` (as 15.129 com coluna `classe` e `mech`)

**Denominadores — declaro os dois:** grid nominal 22×25×30 = **16.500**; presentes no censo **15.129**; **1.371 células nunca existiram em disco** (⚪ T — teto de verificabilidade, fora do denominador). O grosso: `sobol_batch` 747 (config de 3 células por desenho), `e7` 86, `c154` 111, `e103` 81, `b5m` 64, `c238` 74, `c262` 72, `c149` 33, `e81` 25 (nota: e81×ZDT4 aparece com 31 — são 30 `main` + **1 célula `batch`**, regime diferente, não uma 31ª semente).

Recorte de taxa de sucesso **ok/tentado_efetivo** só nos pares problemáticos (o resto é 27–30/27–30):

```
       DTLZ4  ZDT6   WFG1  BBOB_F55 BBOB_F5 BBOB_F22 BBOB_F1  DTLZ1
b1      0/30                                                   29/30
b4             29/30 28/28   27/30    29/30
c154            3/24  6/25    9/24    17/23    23/24   24/24
c238           27/30          24/27    17/27    19/27   24/27
c262            26/27  2/27
e74   (MMF1 29/30)
```

---

## 2. INCAPACIDADES **NÃO DOCUMENTADAS** — 4 novas + 3 extensões

Classifiquei as 157 por mecanismo lendo o ⑥:

```
RS_ESCADA esgota (c154 rota-a)        47   ← documentado
BoTorch ModelFittingError (fit GP)    42   ← documentado (+1 extensão)
MATLAB:badsubscript                   34   ← documentado só p/ c238 (+5 NOVAS em b4)
kriging/dacefit subdeterminado        31   ← documentado só p/ DTLZ4 (+1 extensão)
OptimizationGradientError (optimize_acqf) 2 ← laudo citava 1×; são 2
stats:pdist2:SizeMismatch              1   ← laudo: "causa não investigada"; PERSISTE
```

### 🎯 NOVA-1 — **b4 (CSEA) × MATLAB:badsubscript** — config inteiramente ausente do LAUDO_D0
**5 células**: BBOB_F5 s12 · BBOB_F55 s9/26/27 · ZDT6 s28. Taxas: BBOB_F55 27/30, BBOB_F5 29/30, ZDT6 29/30.

Assinatura do rodapé (lida em 3 células — BBOB_F55/9, BBOB_F5/12, ZDT6/28):
```json
{"rec":"footer","status":"failed",
 "erro":"Array indices must be positive integers or logical values.",
 "identifier":"MATLAB:badsubscript","fe_final":221|111|109}
```
`fe_final` ∈ {109, 111, 111, 221}, **mediana 110 = fim do DoE** (maxfe=309, D=10). Em ZDT6/28 o crash vem com **apenas 3 registros** (header + 1 guard cache_hit + footer) — morre antes da 1ª geração. Em BBOB_F5/12, morre logo após a sonda da geração 2. **0 parquets** nas 5 → célula vazia, nada aproveitável.

Hipótese de mecanismo (medida, **não** provada): no último `b4_gen` antes do crash a classe positiva do classificador FNN do CSEA está quase vazia — `classe_1` = 4, 2 e 5 (de n=109, 109, 219), `ramo=4` ("inconclusivo") nas três. Contraprova honesta: **25 células ok também terminaram com `classe_1`≤5** (BBOB_F55 ok tem min `classe_1`=2). Logo desbalanceamento extremo é **necessário-plausível, não suficiente** — correlação, não causa. Registro como inexplicado 🎯.

**Nota forte, e é aqui que escalo:** a mensagem do b4 (`Array indices must be positive integers`) é **diferente** da do c238 (`Index exceeds the number of array elements. Index must not exceed 1.`), mas **mesmo `identifier`, mesmo `fe≈110`, mesmos problemas (M=2)**. Sugere causa comum no arnês MATLAB na transição DoE→laço, não dois bugs independentes. **NÃO toquei no c238** (🔴 torre).

### 🎯 NOVA-2 — **b5m × semente 25 (7 células)**: morte dura sem exceção
BBOB_F49/F5/F55, DTLZ1/2/3/4 — todas semente 25, todas na vm3. Cada arquivo tem **exatamente 2 registros (header + 1ª sonda), ~4,9 kB, 0 parquets**, e morre **1–11 s após o header**, em janelas espaçadas (21:26 → 22:51 UTC de 13/08). Sem rodapé, sem stack ⇒ o processo foi morto por sinal, não por exceção Python.
Testei o diferenciador óbvio e **não existe**: a 1ª sonda das 7 falhas é idêntica às das 4 células ok da MESMA semente 25 (`n_pontos`=20000, `tempo_pred_sonda_s` 0,67–1,26 s, `modelo_flag` b5m/ProbMOEAD-PBI+GPR). **Classifiquei como `interrompida`, não incapacidade** — mas as 6 primeiras estão a 62–93 min da fronteira do espelho vm3, logo **não** são corte de snapshot. Causa não determinada pelo ⑥. **Não medido: RAM/dmesg da vm3** (fora do meu alcance read-only).

### 🎯 NOVA-3 — **e74 (CLMEA) × MMF1 s3** — continua inexplicada após o recenso
```json
{"rec":"footer","status":"failed","erro":"X and Y must have the same number of columns.",
 "identifier":"stats:pdist2:SizeMismatch","fe_final":37}
```
maxfe=61 (D=2), morre a 61% do orçamento, 0 parquets. Única falha do e74 em 750. O laudo marcou "re-rodar e observar" — **no canônico ela persiste**; o item segue aberto.

### 🎯 NOVA-4 — **c238 × ZDT4 s9 e BBOB_F37 s8** — badsubscript fora da lista documentada
O laudo documenta c238×{F1,F5,F22,F55}+ZDT6. Medi **mais dois problemas** com a assinatura idêntica (`fe_final` 110 e 111). Só registro; **não investiguei** (🔴 c238).

### Extensões de mecanismo documentado (não são novas causas)
- **b1 × DTLZ1 s17**: `least squares problem is underdetermined`, `fe_final`=204 — **mesma assinatura do b1×DTLZ4**, que o laudo trata como exclusivo do DTLZ4. Esporádico (1/30). Extensão do DEC-6.
- **c262 × ZDT6 s17**: `ModelFittingError` em `c262_qnehvi.py:640 → botorch/fit.py:289` — mesma falha de fit do WFG1, agora **fora do WFG1** (1/27, `fe_final`=259/309).
- **c262 × WFG1 s1 e s19**: `OptimizationGradientError` via `botorch/optim/optimize.py:821` (o laudo citava 1×; são **2**). Total c262×WFG1 = 25 incapacidades / 27 tentadas → **2/27 ok**, coerente com o "2/30" documentado.

### Fato novo útil para a análise (fecha pendência do §3 do laudo)
O laudo dizia "não foi verificado se as camadas pré-crash dessas células são utilizáveis". **Verifiquei:**
- incapacidades **MATLAB** (badsubscript 34, kriging 31, pdist2 1) → **0 parquets em 66/66**. Célula vazia.
- incapacidades **Python/BoTorch** (ModelFittingError, RS-escada, gradiente) → **4 parquets em 76 de 91**, com `fe_final` mediano em 42–51% do orçamento. **Dado parcial existe e é recuperável**, como nas ⚪.

---

## 3. AS 501 ⚪ — todas `teto_wall`, e sim, concentram em D alto

**Motivo do rodapé: `teto_wall` em 501/501** (390 na chave `motivo`, 111 na chave `motivo_parada` — c122/c149 usam a outra chave; não é diferença de causa). `tempo_total_s` ∈ **[12,001 h ; 12,488 h]**, confirmando a medição da torre. Só 4 configs produzem ⚪: **c154 300 · c262 90 · c122 85 · c149 26** — os 4 do arnês BoTorch/Python.

### fe_final / maxfe (n=501)
```
mediana 0,774 · média 0,696 · min 0,374 · max 1,000
>80% do orçamento: 234 (46,7%)   >90%: 126   =100%: 4   <50%: 197 (39,3%)
```
Distribuição bimodal: um modo em ~0,39–0,50 (c154 nos D=22/30) e outro em ~0,88–0,97 (c122/c149/c262).

Por config: **c122 mediana 0,914 (83/85 acima de 80%) · c149 0,914 (26/26) · c262 0,893 (80/90) · c154 0,462 (só 45/300)**. O c154 é o caso caro; os outros três fecham com folga pequena de teto.

### Concentração em D
```
D=30 (ZDT1,ZDT3)   136 ⚪  taxa 0,645  frac_med 0,882
D=22 (WFG*,DTLZ7)  213 ⚪  taxa 0,328  frac_med 0,470
D=20 (MMF16_20)     49 ⚪  taxa 0,450  frac_med 0,816
D=12 (DTLZ2/3/4)    75 ⚪  taxa 0,221  frac_med 0,755
D=10                28 ⚪  taxa 0,028  frac_med 0,953
D=7 e D=2            0 ⚪  taxa 0,000
```
**Spearman(D, taxa de ⚪) = 0,915 (p < 1e-4, n=25 problemas)** — nos 4 configs que produzem ⚪. Resposta direta: **sim, fortemente**.

**Exceção que confirma a mecânica: WFG1 (D=22) tem taxa de ⚪ de apenas 0,065.** Não porque seja barato, mas porque **o crash de fit do GP chega antes do relógio** — c154×WFG1: 19 incapacidades / 0 ok / 6 ⚪; c262×WFG1: 25 incapacidades / 2 ok / 0 ⚪. A incapacidade **preempta** o teto.

### Camadas das ⚪ (o caveat do briefing, conferido)
**499 das 501 têm exatamente `__pop` + `__real` + `__timing`; falta a ③ `__surrogate`** — o que é **esperado** (D54 bucket-only: c122, c149, c154, c262 são 4 dos 5 configs bucket-only). **2 células têm as 4** (inconsistência menor com D54, registrada). **Nenhuma ⚪ está sem parquets.** Para o c154 especificamente — o item que o laudo deixou por conferir — as 300 ⚪ têm as 3 camadas locais presentes.

---

## 4. A PERGUNTA CIENTÍFICA

**O que eu medi** (fato, sem interpretação de artigo):

**(a) Separação perfeita por número de objetivos.** As 157 incapacidades partem em duas famílias disjuntas:
```
M=2 (19 problemas)  126 incapacidades  ← badsubscript 34, ModelFittingError 42,
                                          RS-escada 47, gradiente 2, pdist2 1
M=3 (6 problemas)    31 incapacidades  ← 100% kriging/dacefit subdeterminado (b1)
```
**126/126 dos mecanismos de surrogate/aquisição caem em M=2; 31/31 da degeneração do kriging caem em M=3.** Sob a base do grid (76% dos problemas são M=2), 126/126 tem p ≈ 1e-15. Não é acaso amostral.

**(b) 16 dos 22 configs têm ZERO incapacidade** — b3, b5m, b5r, c122, c141, c149, c217, e103, e7, e81, moead, moead_media, nsga2, nsga3, smsemoa, sobol_batch. Só **6 quebram**: b1, b4, c154, c238, c262.

**(c) 12 dos 25 problemas têm ZERO incapacidade** — inclusive DTLZ2, DTLZ3, DTLZ7, MMF16_20, WFG2, WFG4, WFG5, ZDT1, ZDT3, BBOB_F17, MMF4, MMF11_L. As incapacidades concentram-se em:
```
WFG1     44 (c154, c262)      D=22 M=2
DTLZ4    30 (b1)              D=12 M=3
ZDT6     26 (b4,c154,c238,c262) D=10 M=2   ← 4 configs distintos
BBOB_F55 21 (b4,c154,c238)    D=10 M=2   ← 3 configs
BBOB_F5  17 (b4,c154,c238)    D=10 M=2   ← 3 configs
BBOB_F22  9 (c154,c238)
```
**ZDT6, BBOB_F55 e BBOB_F5 quebram 3–4 métodos independentes** (MATLAB e Python, mecanismos distintos) → sinal de **dificuldade do problema**, não de bug de um implementador. **WFG1 e DTLZ4 quebram um mecanismo específico cada** (fit de GP; kriging pós-dedup) → sinal de **limite do método**.

**(d) Onde no orçamento a incapacidade ocorre** — separa "nunca começou" de "degradou":
```
MATLAB:badsubscript   fe_final mediano 110  (35,6% do orçamento) — fim do DoE
kriging subdeterminado           212  (57,7%)
RS-escada (c154)                 167  (50,8%)
ModelFittingError                285  (41,9%)
pdist2 (e74)                      37  (60,7%)
```
O badsubscript é **falha de arranque**; os demais são **degradação após o modelo começar a operar**.

**O que eu NÃO posso afirmar — e por que escalo (D97 + D81).** A pergunta "o método está falhando onde o artigo dizia que funcionaria?" exige o **envelope declarado de cada artigo** (conjunto de teste, M, D, orçamento de FE). **Não li nenhum artigo nesta sessão e não tenho os PDFs no escopo** — qualquer afirmação minha sobre o que ParEGO/CSEA/JES/qNEHVI/EIM prometem seria memória, não medição. **Não medido: envelope declarado dos artigos.**

O que a evidência **habilita** o autor a checar, com as três perguntas já instrumentadas:
1. **b4 = CSEA** (`b4-CSEA-PlatEMO4.15`) é método **baseado em classificação**, e quebra **só em M=2**, exatamente onde a classe positiva colapsa para 2–5 exemplares. Se o artigo do CSEA declara alvo **many-objective (M≥3)**, isto é o método **fora do envelope**, não bug — e vira resultado, não defeito. **Checar o artigo.** É a checagem de maior retorno da lista.
2. **b1 = ParEGO** quebra **100% em DTLZ4** (α=100 colapsa os x ⇒ dedup ⇒ mínimos quadrados subdeterminados) e **1/30 em DTLZ1**. Se DTLZ4 (ou DTLZ4a) está no conjunto de teste do artigo original, é **falha dentro do envelope declarado** — o caso mais forte da dissertação. **Checar.**
3. **c154 (JES) e c262 (qNEHVI)** quebram no **WFG1** — que tem região flat/transformação de viés — pelo mesmo `ModelFittingError` do BoTorch, em duas rotas de aquisição diferentes. Aponta para o **GP**, comum às duas, não para a aquisição. Coerente com "surrogate não modela plateau", mas **checar se os artigos testam WFG1**.
4. **c238 = EIM** — 🔴 fora de análise por ordem da torre.

---

## 5. ESCALAÇÕES (D81 — não escolhi sozinho)

**E1 🎯 DEFEITO NO CANÔNICO — `c122 × ZDT1 × semente 7` está marcada `fail` mas COMPLETOU.**
O espelho `~/mestrado_coleta_m8/matlab-vm1/experiments/main/c122/exp_main_c122_ZDT1_7.jsonl` (1.209.476 B) tem rodapé completo:
```json
{"rec":"footer","status":"ok","fe_final":929,"maxfe":929,"motivo_parada":"orcamento","n_geracoes":600}
```
O canônico `/Users/gmello/Documents/python_repos/mestrado/resultados_experimentos/c122/ZDT1/7/exp_main_c122_ZDT1_7.jsonl` tem **1.207.619 B — 1.857 bytes a menos — e nenhum rodapé**. É uma **cópia truncada de uma célula que terminou o orçamento inteiro**. Correção sugerida: `fail → ok, fe=929/929`. Não alterei nada.

**E2 — varredura de integridade do canônico contra os 6 espelhos (15.129 arquivos, 16.011 cópias).** 359 canônicos (2,37%) são menores que a maior cópia do espelho, mas a mediana do déficit é **4 bytes** (linha final incompleta, benigno). **Só 4 perdem conteúdo relevante:**
| célula | canônico | espelho | consequência |
|---|---|---|---|
| `c122/ZDT1/7` | 1.207.619 B, 0 rodapé | 1.209.476 B, 2 rodapés | **muda o veredito** (E1) |
| `c141/ZDT4/9` | **368 B, 1 linha (só header)** | 61.966 B, rodapé ok | ⑥ **perdida**; censo diz `ok` pelo manifesto |
| `nsga3/MMF1/14` | 6.139 B, 0 rodapé | 6.316 B, rodapé ok | ⑥ sem rodapé |
| `c217/WFG4/12` | 560.265 B, 0 rodapé | 560.417 B, rodapé ok | ⑥ sem rodapé |
Nos 4 casos existe cópia melhor no espelho. Nenhum canônico tem rodapé onde o espelho não tem. **Recomendação: recopiar essas 4 do espelho.** Não copiei.

**E3 — as 51 `interrompida` precisam de veredito do autor.** 29 são corte de snapshot (em voo), 22 são morte de processo sem exceção. Nenhuma é erro de algoritmo. Entram na taxa de sucesso como **⚪ T (teto de verificabilidade, fora do denominador)** ou como célula a re-disparar — **é decisão de protocolo, não minha**. O `censo_completo_22.csv` hoje as conta como `fail`.

**E4 — b4 e c238 compartilham `MATLAB:badsubscript` em fe≈110, em M=2.** Mensagens diferentes, arnês igual. Se a torre achar a linha do c238, **testar se explica o b4 também**. Não investiguei o c238.

**E5 — `b5m` semente 25 na vm3 (7 células, morte em ~3 s, sem exceção)** não tem explicação no ⑥ e não é corte de snapshot. Requer log de sistema da vm3, que não tenho.

**E6 — inconsistência menor com D54:** 2 das 501 ⚪ têm `__surrogate.parquet` local, sendo de configs bucket-only.

---

## 6. ARQUIVOS PRODUZIDOS (scratchpad, nada tocado no repo)
Base: `/private/tmp/claude-501/-Users-gmello/33c29160-6eb6-4277-a041-db4855486063/scratchpad/`
- `censo_classificado.csv` — as 15.129 com `classe` (ok/teto_wall/incapacidade/interrompida/ambiente), `mech`, `D`, `M`
- `MATRIZ_util_sobre_tentado.csv` · `M_ok.csv` · `M_teto_wall.csv` · `M_incapacidade.csv` · `M_interrompida.csv` · `M_tentado_efetivo.csv`
- `fail_class.csv` — as 209 com mecanismo, último `ts`, `fe_final`
- `incapacidades_fe.csv` — as 157 com `fe_final`, `frac` do orçamento, nº de parquets sobreviventes
- `teto_full2.csv` — as 501 ⚪ com `motivo`, `fe_final`, `maxfe`, `frac`, `tempo_s`, `D`, `M`
- `integridade.csv` — canônico × espelho, 15.129 linhas
- `dup_semfooter.csv` — 59 cópias das 51 interrompidas, com fronteira de espelho
- `b4_mech.csv` — 745 células b4 com `classe_1`/`classe_0` do último `b4_gen`

**Confirmo:** não editei o repo, não commitei, não invoquei `experiments.py`/`experiment.run`/`experiments.m`, não desliguei VM, não apaguei nada, não disparei célula. Todas as leituras foram `open()` em modo texto/binário sobre `.jsonl`, `.manifest.json` e listagem de `.parquet` (não abri parquet). Não usei `_quarentena/`. Nenhum veredito de fidelidade emitido — o material acima é evidência e recomendação.