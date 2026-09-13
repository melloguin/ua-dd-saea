## sobol_batch-S23 — VEREDITO: PARCIALMENTE REFUTADO → CONFIRMADO(d), reduzido de 4 campos para 1 (`n_front1`)

**Resumo em 3 linhas**
O achado foi enunciado como "`n_front1` **e ideal/nadir** ausentes"; três dos quatro campos caem: `ideal` **está presente** (o instrumento canônico do projeto define `ideal ≡ f_best`, e o `f_best` logado é exatamente esse vetor), e `nadir_pop`/`nadir_front1` são convenção de **4/47** linhas (alg,exp) do estudo inteiro — ausentes inclusive no **5º piso** (`moead_media`), por decisão **DI-30.B3 ratificada pelo autor**. Sobrevive **um único campo**, `n_front1`, e sobrevive forte: **46/47** linhas do estudo o logam, sobol_batch é a única exceção, e o custo de gravá-lo seria de 0,3–1,6 % do wall. Enquadramento: **(d) defeito de instrumentação** — o mecanismo está intacto (S3, bit-a-bit) e a informação é **integralmente recuperável**; recuperei os 1.000 valores e validei o método contra o rival do mesmo sub-estudo com acerto 1.000/1.000.

---

### O que tentei para derrubar (os 4 passos, com números)

**1 · Por DECISÃO — DERRUBOU 3 dos 4 campos.**
Achei a decisão que o analista não conhecia (ele a cita no §5 do próprio relatório, mas não a aplica ao S23). `CONTRATO_DE_DADOS.md:197`, literal:

> "**[DI-30.B3, autor 2026-07-23]** No ⑥/logging o moead_media segue a linha **"b5"** (⑥ estruturalmente idêntico ao b5m, seu par de ablação) — **NÃO a linha "pisos" (ideal/nadir por geração)**, embora seja "piso" na taxonomia."

E a ratificação em `REGISTRO_DECISOES_IMPLEMENTACAO.md:1365`: *"B3 — linha do ⑥/CONTRATO §6.1 do moead_media = 'b5' (**RATIFICADO**)"*, com a alternativa explicitamente recusada em `:1345` (*"'b5' … **vs** 'pisos' (ideal/nadir por geração + vetores no header). Recomendação da torre: manter 'b5'"*). Ou seja: **o autor já julgou exatamente esta questão** — "ser piso na taxonomia" não obriga à linha "pisos" do §6.1 quando o ⑥ do config segue outra família. O ⑥ do `sobol_batch` é a linha standalone-Python/b5 (`rec='decision'`, `caminho='<alg>_gen'`, término por `motivo_parada` no ⑤, sem `footer.termino`) — o próprio §5 do relatório documenta a assimetria e a chama de "exatamente a mesma [do] moead_media". **A regra citada como violada (§6.1 linha "pisos") não vincula este config pelo mesmo raciocínio que o autor já sancionou.**

Reforços: (a) `CONTRATO_DE_DADOS.md` tem **zero** ocorrências de "sobol" ou "batch" — o documento é "dos **21 configs**" (v1.1 · 2026-07-19) e o mapeamento §6.1 é datado **2026-07-18**; o `sobol_batch` nasceu em **DI-33, 2026-07-23**, com `alg_id=22` (`artifacts/seeds.json`), 5 dias depois; (b) `src/piso_instrument.m:2` declara-se "instrumentacao dos **4** PISOS ONLINE (nsga2/nsga3/moead/smsemoa)" — o `sobol_batch` nunca esteve sob ele; (c) o cartão T6/DI-33 escopa o log do batch: *"Instrumentação: NENHUM retrofit novo necessário … **Únicos acréscimos de log: eventos de lote no ⑥**"*.

**O que a decisão NÃO salva:** DI-30.B3 manda seguir a linha **"b5"**, e a linha b5 **carrega `n_front1`** (b5m/b5r/moead_media: `fe, f_best, n_front1`). A mesma decisão que exonera ideal/nadir **condena** a omissão do `n_front1`.

**2 · Por QUERY — NÃO derrubou; a evidência sobrevive a uma formulação independente.**
Reescrevi o censo do zero, duas vezes, sem reusar nada da bateria do analista.
- `r1` (reconhecimento por sufixo `_gen`): 33 linhas (alg,exp).
- `r2` (**critério alternativo**: "evento de geração = qualquer `rec` que carregue `fe` **e** `f_best`") — captura `c154`/`c262` (`decision/infill`), `c311` (`c311_build`) e `e74` (`e74_boot`), que o filtro do analista perdia: **47 linhas (alg,exp) · 245 células · ~200 mil eventos**.

Resultado idêntico nas duas formulações:
| campo | linhas (alg,exp) que logam |
|---|---:|
| `n_front1` | **46/47** — falta só em `sobol_batch` |
| `ideal` / `nadir_pop` / `nadir_front1` | **4/47** — só nsga2, nsga3, moead, smsemoa |

Off-by-one/janela/float/ordenação: não se aplicam (é presença de chave, não valor); amostra: as 5/5 células, **1.000/1.000** eventos, `variacao_chaves=1` (o conjunto de chaves é constante). Confirmei também que `n_front1` **não está em lugar nenhum** do run: ausente do evento, do `header`, dos **2 footers** e das 31 chaves do manifesto — enquanto e81/c149/c122 o gravam até no `footer`.

**O erro do analista foi de *inferência*, não de query**: a linha `moead_media … ideal=False, nadir_pop=False, nadir_front1=False` está no **próprio `minimo_comum_di10.csv` dele** (4/10). Ele tinha o controle que derruba metade do achado e não o leu.

**3 · Por CÓDIGO — confirma o campo residual e refuta a "causa provável".**
`src/sobol_batch.py:159-165` monta o evento à mão:
```python
log.decision(caminho="sobol_batch_gen", motivo=...,
             geracao=g, fe=bud.fe, q=q, seed_sobol=int(seed_it),
             f_best=[float(v) for v in np.vstack([r.f for r in bud.records]).min(axis=0)])
```
A "causa provável" do analista ("montou à mão em vez de chamar `H.minimo_comum_di10`") **é falsa para 3 dos 4 campos**: o helper canônico (`src/standalone_harness.py:874-911`) devolve `{fe, f_best, n_front1}` + opcionais **e nunca emite `ideal`/`nadir_pop`/`nadir_front1`**. Prova viva: `src/piso_offline.py:432` (moead_media) **chama o helper** e mesmo assim tem 0/3 desses campos em 45 células. O helper explica **exatamente um** campo: `n_front1`.

E `ideal` já está lá: `src/piso_instrument.m:38` `f_best = min(PopObj,[],1); % == ideal` e `:58` `'ideal', f_best, ... % identico a f_best por definicao; emitido sob os DOIS nomes`. Recomputei: o `f_best` do sobol_batch == min por objetivo do arquivo cumulativo com **Δmáx 2,67e-10 (DTLZ2) · 5,36e-11 (MMF16_20) · 3,21e-8 (WFG9) · 9,01e-8 (ZDT1) · 3,43e-6 (ZDT4)** — puro ULP de float32. **A grandeza "ideal" está gravada em 1.000/1.000 eventos.** Consequência: o "6/10 dos pisos MATLAB" do relatório conta `f_best` **duas vezes**; em quantidades distintas os 4 pisos têm 5, não 6.

Tentei ainda a defesa por custo (critério do próprio CONTRATO: *"o que barra é CUSTO NOVO em hot-loop"*, DI-12.1/DI-21) e **ela não se sustenta** — cronometrei `problems._nds_filter` nas 200 gerações: **0,020–0,052 s por célula = 0,3 % a 1,6 % do wall** (3,16–6,82 s). Barato. Honestamente: não havia razão de custo para omitir.

**4 · Controle positivo/negativo — discrimina.**
- **Negativo (o "defeito" está em todo lugar?)**: para `ideal`/`nadir_*` — **sim**, 43/47 não têm ⇒ convenção, não achado. Para `n_front1` — **não**, 46/47 têm ⇒ achado real.
- **Positivo (o mesmo teste no rival direto)**: `e81`/`batch` e `c149`/`batch` — mesmas 5 células, mesma semente, mesmo `q=10`, mesmo DoE — logam `n_front1` em 1.000/1.000 eventos cada, e o fazem com **a mesma definição** que se aplicaria ao piso: `e81_qpots.py:1028` passa `F_arc` (o arquivo) e `c149_lbnmobo.py:908` passa `F_arc_pos`.
- **Controle de recuperação (o teste decisivo do impacto)**: apliquei meu recomputo a partir da ① ao `e81`/batch e comparei com o `n_front1` **logado** → **1.000/1.000 exatos, dif_absmax = 0**. (`c149`: 900/1.000, os 90 desencontros só em MMF16_20 com |dif| ≤ 2, explicados pelo `F_arc_**pos**` — arquivo filtrado, particularidade do c149, não do método.) Como o "population" do piso É o arquivo cumulativo (S17), o mesmo recomputo recupera o campo **sem perda**: gerei os 1.000 valores (`n_front1` de 42→116 no DTLZ2, 51→221 no MMF16_20, 12→25 no WFG9, 14→27 no ZDT1, 5→11 no ZDT4 — série informativa e **não** trivialmente monótona: cai de 11 para 7 no ZDT4 e de 27 para 26 no ZDT1).
- **Bônus**: `nadir_pop` do piso é **monótono não-decrescente em 5/5** (é o máximo cumulativo de um arquivo que só cresce) — se tivesse sido logado seria um campo **enganoso**, comparável em nome mas não em grandeza com o nadir de uma população N=20 que rotaciona. Não gravá-lo é melhor que gravá-lo.

---

### Por que não caiu (o resíduo) / por que caiu (o resto)

**Caiu** porque a regra citada (§6.1 linha "pisos", `ideal/nadir da pop por geração`) foi **julgada e afastada pelo autor em DI-30.B3** para o caso estruturalmente idêntico (`moead_media`), porque `ideal` é definicionalmente `f_best` e **está gravado**, e porque `nadir_*` é convenção de 4/47 — dos quais o sobol_batch está fora por desenho de ⑥ e por degenerescência da grandeza.

**Não caiu** o `n_front1` porque: (i) é do **mínimo comum DI-10 universal** (`CONTRATO §6`, "Registros universais"), não da linha "pisos"; (ii) a linha "b5" que a DI-30.B3 manda seguir **inclui** `n_front1`; (iii) `scripts/auditar.py:42` matricula explicitamente `PISOS_ONLINE = {"nsga2","nsga3","moead","smsemoa","sobol_batch"}` — o projeto **decidiu** que ele é piso online, e nenhum piso do estudo deixa de logar `n_front1`; (iv) o cartão T6/DI-33 prometeu *"Diagnóstico do batch = mesma qualidade do main por construção"*, e este é o único ponto em que a promessa falha; (v) 46/47 e custo de 1 %.

**Ponto de instrumentação que o gate deixou passar (nota lateral)**: `scripts/auditar.py` **não inspeciona o ⑥** — zero ocorrências de `jsonl`/`decision`/`_gen`/`f_best` no arquivo. O gate não sancionou nada; ele simplesmente não olha. Isso é o que permitiu a lacuna atravessar 5 células verdes.

---

### Enquadramento e bússola D29

**(d) DEFEITO DE INSTRUMENTAÇÃO — item para a torre central**, com escopo reduzido a **um campo**.
Não é (a) BUG: nenhuma linha de decisão do algoritmo lê ou escreve `n_front1`; a trajetória de busca está provada bit-a-bit (S3, 10.000/10.000 pontos) e independe do log. Não é (b) nem (c): o dado está íntegro e nenhuma célula sai da análise.

**Bússola D29 — não aplicável a este item.** A D29 classifica *divergências código × artigo* de um algoritmo publicado ("BUG→artigo; VERSÃO→artigo se toca o surrogate; IMPL→código; ERRATUM→código; EXTENSÃO→nossa", SPEC:1647). O `sobol_batch` **não tem artigo nem código de referência**: é construção nossa (D37/D66) ⇒ a única casa possível seria 🟢 **EXTENSÃO nossa, declarada** — e ainda assim a D29 governa *mecanismo*, não *campo de log*. O mecanismo está 🟢 declarado e provado; a lacuna é de contrato de dados (CONTRATO §6), fora do alcance da D29.

Localização exata para a torre: **`/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/src/sobol_batch.py:159-165`** — o `log.decision(...)` que não chama `H.minimo_comum_di10`.

---

### Impacto

- **Nenhuma célula é excluída.** 5/5 permanecem: `status=ok`, FE exato, ①②④⑤⑥ íntegras, mecanismo provado por reconstrução total.
- **Nenhum número publicado muda.** Varri `f5/f55_transversais.py`, `f5/f55b_adendo.py`, `f5/transversais_f55*.md`, `f5/RELATORIO_F5.md` e as baterias `f52*`: **zero** consumo de `n_front1`. IGD+/HV/gate/placar do §4, projeção 30 sementes — todos lêem a ①, intocados.
- **O que muda no relatório do config**: o S23 deve ser reescrito de "`n_front1` **e ideal/nadir** ausentes" para "**`n_front1` ausente**"; a contagem "2/10 vs 6/10 vs 7/10" é um **artefato de denominador** (mistura o mínimo comum DI-10 com extras de 4 configs MATLAB e conta `ideal` como distinto de `f_best`) e deve sair — a métrica honesta é "1 campo do mínimo comum universal, único caso em 47 linhas (alg,exp)". A classe (3) do config cai de 3/25 para 2/25 na contagem principal (e para 1/25 sob a convenção c154 do §3).
- **Correção adicional à armadilha (d) do §9**: "Não existe `n_front1`/`ideal`/`nadir`" está errado — `ideal` existe, sob o nome `f_best` (a própria armadilha (h) já dizia isso, em contradição com a (d)).
- **A F5.5 (transversal dos pisos) não fica bloqueada**: a série está recuperada e no disco.

---

### Ação recomendada para a rodada perfeita (F5.7) + custo

**Prioridade 1 — recuperação a posteriori, SEM tocar no pipeline congelado (recomendada).** Já entregue: `r3_n_front1_recomputado.csv` (1.000 linhas, 5 células × 200 gerações), com o método validado a **1.000/1.000** contra o `n_front1` logado do e81/batch. Estender às 150 células das 30 sementes: **~5 s de CPU**, ~20 linhas de script, **zero risco** ao HEAD `1c2811b`. Isto **fecha o impacto analítico integralmente**.

**Prioridade 2 — corrigir o runner, se e só se houver re-disparo do batch por outro motivo.** Uma linha em `src/sobol_batch.py:159-165`:
```python
log.decision(caminho="sobol_batch_gen", motivo=..., geracao=g, q=q,
             seed_sobol=int(seed_it),
             **H.minimo_comum_di10(np.vstack([r.f for r in bud.records]),
                                   fe=bud.fe, tempo_busca_s=t_busca))
```
Isso entrega `fe`, `f_best` (idêntico ao atual), `n_front1` e ainda promove `tempo_busca_s` ao ⑥. **Custo de execução: +0,3–1,6 % de wall** (medido) sobre os ≈10 min projetados das 150 células ⇒ **+6 a +10 s no total**. **Custo de risco: alto em proporção** — mexe num runner congelado e altera o `.jsonl` de um config cuja prova-joia (S3) é justamente a reprodução bit-a-bit; exige re-rodar as 5 células da s42 e reconferir o determinismo. **Não recomendo disparar só por isto.**

**Prioridade 3 — doc-sync (custo ~0).** Registrar por escrito, no CONTRATO §6.1, a mesma nota que a DI-30.B3 exigiu para o `moead_media`, agora para o `sobol_batch`: *"embora seja piso na taxonomia, segue a linha de logging standalone/b5 — sem `ideal`/`nadir` por geração; o `f_best` do mínimo comum É o ideal do arquivo"*. Isto converte 3 dos 4 campos de "desvio inexplicado" em "comportamento declarado" **sem tocar em código**, e ainda cobre a assimetria de `motivo_parada` que o §5 do relatório já pedia. **Uma decisão do autor no lote D97, custo zero de execução.**

**Prioridade 4 — dívida de gate, para a torre.** `scripts/auditar.py` não valida nenhum campo do ⑥; a ausência do mínimo comum DI-10 atravessou 5 gates verdes. Um check de presença de `{fe, f_best, n_front1}` no evento de geração custaria ~15 linhas e pegaria esta classe inteira de lacuna antes do M8.

**Arquivos** (todos em `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/sobol_batch-S23/`): `VEREDITO.md` · `r1_censo_campos.py` + `r1_censo_campos_{alg,celula}.csv` · `r2_censo_amplo.py` + `r2_censo_amplo_{alg,celula}.csv` (47 linhas alg×exp, 245 células) · `r3_recuperabilidade.py` + `r3_recuperabilidade.csv` + **`r3_n_front1_recomputado.csv`** (os 1.000 valores recuperados) · `r4_validacao_recuperacao.py` + `r4_validacao_recuperacao.csv` (controle positivo 1.000/1.000 no e81).