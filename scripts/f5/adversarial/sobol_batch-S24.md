## sobol_batch-S24 — VEREDITO: CONFIRMADO (d) — DEFEITO DE INSTRUMENTAÇÃO

**Resumo em 3 linhas**
O achado sobrevive aos quatro ataques e sai **mais forte** do que entrou: 5/5 células gravam `tempo_aval_real_s = 0.0` contra **0 zeros em 416 células online** dos outros 17 configs (o analista disse 0/395; ele deixou os 21 manifestos do c262 de fora do denominador), e a medição direta mostra que o valor verdadeiro é **≈4,11 s-VM nas 5 células (20,6 % do wall; 57,2 % do wall só no WFG9)**, não zero. Nenhuma decisão sanciona — pelo contrário, o cartão DI-33 promete *"Diagnóstico do batch = mesma qualidade do main por construção"*. Mas o enquadramento é (d), não (a): o mecanismo, as camadas ①②④ e todas as métricas estão corretos; o que mente é o campo agregado do ⑤ — e a causa-raiz não é o runner, é o **portão único de FE do Python nunca ter recebido o cronômetro que a DI-12.4 instalou no gêmeo MATLAB**, somado a um helper de export que **proíbe estruturalmente escrever NULL**.

---

**O que tentei para derrubar (os 4 passos, com os números)**

**1 · Por DECISÃO — falhou, e o tiro saiu pela culatra.** Varri `REGISTRO_DECISOES_IMPLEMENTACAO.md` (DI-01..DI-40), `CONTRATO_DE_DADOS.md`, `claude_code_context/` (SPEC + bundles + `artifacts/*.json`) e o `sigma_dict` gravado nas 5 células. Achados:
- **DI-13.2** (CONTRATO l.233) isenta explicitamente **só** `tempo_fit_s`, e a isenção é nominal aos *"4 pisos ONLINE"* — rótulo anterior ao `sobol_batch`, que é o 5.º. E o racional textual da própria DI-13.2 é a condenação do achado: gravam `NULL` *("não se aplica", ≠ `0.0` que significaria "treinou e custou zero" e poluiria a média de custo)*.
- **DI-12.4** (l.352) decidiu **(a) instrumentar o portão**: *"`tic/toc` acumulador em volta do `evalFcn` — só a avaliação inédita"*, justificado como *"~4 linhas, sem RNG, sem alterar decisão nenhuma"*. Foi aplicado em `src/FEBudget.m` (MATLAB) e **nunca no gêmeo Python** `src/budget.py`.
- **DI-33** (l.1515-1517), o cartão que criou este runner, afirma: *"**Instrumentação: NENHUM retrofit novo necessário** … Diagnóstico do batch = mesma qualidade do main por construção."* Não sanciona a omissão — **assevera o contrário**.
- `sigma_dict` das 5 células (7 chaves: modelo/regime/mu_*/sigma_*/sonda/modelo_hp/lote) **não menciona timing**. Pela cadeia de precedência §0 (dados → sigma_dict → bundle → decisões), não há sanção em nenhum degrau.
- Única defesa real encontrada: SPEC §17.6(1) tem a cláusula de escape *"quando separável **sem custo extra**"*. Ela não salva — invocá-la exigiria **NULL** ("não separei"), que é exatamente a convenção viva dos 4 pisos EA (medida: `tempo_fit_surrogate_s` e `tempo_busca_s` = `null` em **25/25 células de cada um** dos nsga2/nsga3/moead/smsemoa). O `sobol_batch` grava `0.0` nos dois — o único valor que é afirmativamente falso.

**2 · Por QUERY — reproduzido do zero, e a conclusão fica mais forte.** Reimplementei a varredura sem tocar em `bateria3_contrato.py`, classificando regime pelo campo `regime` do manifesto (não por lista fixa), sobre **666 manifestos** (421 online + 245 offline), separando `0.0` de `None`/ausente (o teste `== 0.0` do analista devolve `False` para `None` — armadilha real, mas **0 `None` e 0 ausentes** em 421):
- `t_aval == 0.0` exato: **5/421**, todas `sobol_batch`. Critério alternativo `t_aval < 1e-3 s`: as mesmas 5. Menor valor não-nulo do estudo: **0,0019 s** (e81).
- Cobertura do wall pelos 4 componentes: **0,0358–0,0803** (não-contabilizado 0,9197–0,9642) — bate com o analista até a 3.ª casa.
- Proxy da ④ `Σ tempo_geracao − Σ tempo_busca`: **0,1180 / 0,1135 / 0,1403 / 0,1517 / 3,1655 s** — reproduz exato.
- **Correção ao denominador**: 18 configs online / 421 células, não 17/400. O placar honesto é **0 zeros em 416** células online alheias.

**3 · Por CÓDIGO — o comportamento é por construção, e a construção é o defeito.** `src/sobol_batch.py:186` passa `tempo_aval_real_s=0.0` literal (e `:182` passa `tempo_fit_surrogate_s=0.0`, onde os pisos EA põem null). A cadeia:
- `src/budget.py:195-229` — `FEBudget.evaluate` chama `true_f(x)` na linha 222 **sem cronômetro nenhum**. É o portão único do Python; a DI-12.4 só fechou o do MATLAB.
- `src/export.py:548-568` — `manifest_timing_block` faz `round(float(...))` nas 4 chaves obrigatórias: passar `None` levanta `TypeError`. **No stack Python "não medi" é inexprimível**; `0.0` é o único valor que o helper aceita. Os pisos MATLAB escrevem null porque não passam por este helper.
- Controle de autoria: dos **6 runners Python online**, 5 medem à mão — `e81_qpots.py:230/252`, `c149_lbnmobo.py:184/205`, `c122_thetadeadp.py:251/266` e, via adaptador compartilhado, `botorch_harness.py:529/559` (c154 e c262). O `sobol_batch` é o **1/6** que não. Nenhum teste guarda isso: `tests/test_di09_r2.py:135-149` só assere **presença** das 4 chaves — e a linha 149 chega a passar `tempo_aval_real_s=0.0` como caso válido.

**4 · Controle positivo/negativo — separa, mas menos do que o relatório sugere.**
- *Positivo*: os 4 pisos EA gravam 0,126–0,142 s medianos para ~309 avaliações (225–3.804 µs/aval) — o campo carrega grandeza plausível onde é medido.
- *Negativo (importante)*: o "92–96 % do wall não-contabilizado" **não é anomalia do sobol_batch**. Cobertura mediana por config online: **nsga3 2,76 % · moead 2,78 % · nsga2 3,02 % · smsemoa 3,05 % · sobol_batch 4,91 %** — os pisos EA estão *piores* (97,0–97,2 % não-contabilizado). Fração enorme não-contabilizada é a regra dos pisos baratos (arranque de processo + I/O), não o achado.
- *Robustez do critério*: sob critério **relativo** (`t_aval/wall < 1e-4`) o sobol_batch deixa de ser único (138 células, 9 configs). O que discrimina é o critério **absoluto**: zero exato num runner que chama o oráculo 2.109–2.329 vezes.

**Medição direta do que o zero esconde** (mediana de 5 repetições; fator de máquina VM/Mac = 1,07–1,40 calibrado pelo `tempo_busca_s`, que é o *mesmo* trabalho scipy gravado no manifesto):

| célula | wall VM | `t_aval` gravado | `t_aval` medido (s-VM) | % do wall | proxy §9(e) | proxy/medido |
|---|---:|---:|---:|---:|---:|---:|
| ZDT4 (D=10) | 3,1561 | **0,0** | 0,0380 | 1,20 % | 0,1135 | 2,98× |
| DTLZ2 (D=12) | 3,2655 | **0,0** | 0,0652 | 2,00 % | 0,1403 | 2,15× |
| MMF16_20 (D=20) | 3,3378 | **0,0** | 0,0716 | 2,14 % | 0,1517 | 2,12× |
| WFG9 (D=22) | 6,8203 | **0,0** | **3,8979** | **57,15 %** | 3,1655 | **0,81×** |
| ZDT1 (D=30) | 3,3356 | **0,0** | 0,0369 | 1,11 % | 0,1180 | 3,19× |
| **Σ** | **19,915** | **0,0** | **4,110** | **20,6 %** | 3,689 | — |

**Por que não caiu** — três independências fecham o cerco: (i) nenhuma decisão, regra de contrato, nota de bundle ou entrada de `sigma_dict` menciona o campo; (ii) a query sobrevive a reformulação com denominador maior, com classificação de regime independente e com a distinção 0.0×None; (iii) o código mostra o valor sendo passado como literal, sem cronômetro em lugar nenhum do caminho Python. E o controle mede que a grandeza omitida é **grande** (57 % do wall no WFG9), não ruído.

**Duas correções que a refutação produziu contra o próprio relatório** (o analista errou para o lado severo em dois pontos e para o lado leniente em um):
1. A **armadilha (e) do §9** recomenda `Σ(tempo_geracao_s − tempo_busca_s)` como "o proxy honesto". Ele **não é confiável**: superestima 2,12×–3,19× nos problemas baratos (carrega o bookkeeping O(n) do laço — `buf.add_pop` sobre todos os records + `np.vstack([r.f for r in bud.records])` do `f_best`, ambos crescendo a cada geração) e **subestima 19 %** justamente no WFG9, onde a grandeza importa. Não é sequer conservador numa direção só.
2. *"parcialmente irrecuperável (o custo do DoE inicial não está em nenhuma camada)"* é forte demais: a parcela do DoE init vale **0,438 s-VM = 2,20 % do wall das 5 células**, e — porque o run é bit-reprodutível (S3, 10.000/10.000 pontos) — **a grandeza inteira é recuperável por re-medição**, que é o que fiz em ~30 s de CPU. O que não se recupera é o valor *daquela máquina*, e o §19 do próprio contrato já proíbe comparar wall entre stacks.
3. Para o lado leniente: o relatório não notou que **`tempo_fit_surrogate_s` também vai 0.0** (linha 182), onde os 4 pisos EA gravam `null` em 25/25 — mesmo racional da DI-13.2, mesmo defeito, segundo campo.

---

**Enquadramento e bússola D29**
**(d) DEFEITO DE INSTRUMENTAÇÃO/DOC — item para a torre central.** O mecanismo está certo (S3 provou os 10.000 pontos bit-a-bit; S12 recomputou as 11.029 avaliações), o log é que engana: `0.0` lê-se como "avaliação instantânea" e significa "não medido". Não é (a) BUG de implementação porque nenhuma decisão do algoritmo depende do campo; não é (b) porque não vira resultado; não é (c) porque nenhum dado está corrompido.

**A bússola D29 não tem jurisdição aqui** e isso precisa ser dito explicitamente no D97: a D29 arbitra divergência **código-oficial × paper** pelo critério *"muda o mecanismo que a tese mede (o surrogate e o uso da incerteza)?"* — e o `sobol_batch` **não tem paper** (construção nossa, D37/D66), nem o campo toca mecanismo algum. Se for preciso carimbar, o config inteiro é 🟢 **verde (extensão nossa, declarada)** e este defeito específico é do tipo 🟠 **laranja** (detalhe periférico de implementação ⇒ segue o CÓDIGO) — mas a norma violada é `CONTRATO_DE_DADOS.md` §4 + DI-12.4 + o racional da DI-13.2, não o Anexo D.

**Arquivo:linha da causa-raiz** (a ordem importa — corrigir só o 3.º deixa a armadilha viva):
1. `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/src/budget.py:222` — `f = np.asarray(true_f(x), …)` sem cronômetro; a DI-12.4 fechou o portão MATLAB (`src/FEBudget.m`) e deixou o Python aberto.
2. `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/src/export.py:559-564` — `round(float(...))` nas 4 chaves torna `NULL` inexprimível no stack Python; "não medi" e "medi zero" colapsam no mesmo literal.
3. `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/src/sobol_batch.py:186` (e `:182`) — onde os dois defeitos se encontram.

---

**Impacto**
- **Células a excluir: NENHUMA.** Nenhum dado corrompido, nenhum número de mecanismo afetado.
- **Métricas, ranking, placar do §4, ganho sobre o DoE, contrafactuais, gate D92: inalterados** — todos leem ① e ⑤/`tempo_total_s`, que estão corretos (665/665 com wall, F5.2d).
- **Eixo 2 do payoff (§V-B.3) — o dano é MUITO menor do que o relatório afirma.** Medi o breakdown das 15 células batch q=10: c149 wall 15.112–17.894 s com `fit` 13.094–15.602 s (86,7–87,2 %) e `busca` 1.973–2.247 s; e81 wall 2.077–12.963 s com `fit` 1.616–10.719 s; **`tempo_aval_real_s` dos dois vale 0,043–3,424 s = 0,0004 %–0,05 % do wall deles**. A curva de custo do sub-estudo é fit×busca; a manchete (piso 3,3 s × e81 5.721 s × c149 16.727 s, ~1.700× e ~5.000×) não muda em um dígito. O que de fato se perde é o **breakdown interno do piso** — e é exatamente a frase que o §6 do relatório publica sem lastro: *"o WFG9 é 2,1× o resto inteiramente por custo de avaliação da função (3,17 s dos 6,82 s)"*. Esse 3,17 s vinha do proxy enviesado; o número defensável é **3,90 s-VM = 57,2 % do wall** (medido). **Corrija esse número no relatório** — é o único publicado que muda.
- **Score 9,0/10 e recomendação ACEITAR + CAVEAT: mantidos.** A justificativa do §7 deve trocar "deixando 92–96 % do wall sem breakdown justo" por "deixando sem breakdown a parcela de avaliação, que vale 1,1 %–57,2 % do wall conforme o problema — enquanto os 4 pisos EA, que medem o campo, têm 97,0–97,2 % do wall igualmente não-contabilizado".
- **Alcance real do defeito**: hoje 5 células; **em 30 sementes serão 150**, e o mesmo buraco reaparece em qualquer runner Python online futuro, porque o helper de export não permite dizer "não medi".

---

**Ação para F5.7 + custo**

| # | ação | arquivo | esforço |
|---|---|---|---|
| 1 | Cronômetro acumulador em volta de `true_f(x)` + property `tempo_aval_real_s` — o espelho exato da DI-12.4 no portão Python (só avaliação inédita; cache-hit não entra) | `src/budget.py:195-229` | **~5 linhas**, 15 min |
| 2 | `tempo_aval_real_s=bud.tempo_aval_real_s` e `tempo_fit_surrogate_s=None` | `src/sobol_batch.py:182,186` | **2 linhas** |
| 3 | Aceitar `None` nas 4 chaves obrigatórias (ou sentinela explícita), para que "não separei" seja exprimível no Python como já é no MATLAB | `src/export.py:559-564` | **~4 linhas** |
| 4 | Teste-guarda: config `regime='online'` ⇒ `timing.tempo_aval_real_s > 0`; hoje só se testa presença da chave | `tests/test_batch_q10.py` + `tests/test_di09_r2.py` | **~10 linhas** |
| 5 | Enxugar as 3 duplicatas manuais (e81/c149/c122) para lerem do portão | `src/e81_qpots.py`, `src/c149_lbnmobo.py`, `src/c122_thetadeadp.py` | opcional, ~30 min |
| 6 | Re-rodar o config inteiro em 30 sementes | — | **≈10 min · 1 core** (as 5 células da s42 custam 19,92 s de wall = 0,0055 h-core) |
| 7 | Item para a torre: *o retrofit DI-12.4 foi aplicado a um só dos dois stacks; e o `manifest_timing_block` do Python impede a semântica NULL que a DI-13.2 exige* — vale para os **21 configs**, não só para este | `REGISTRO` (nova DI) | 20 min |

**Custo total ≈ 1 h de implementação + 10 min de máquina; ganho: o item deixa de ser caveat do D97 e a rodada perfeita publica o breakdown do baseline com número medido.** Recomendo fazer **antes do disparo das 695 células** — depois, custa 150 células re-rodadas em vez de 5.

**Artefatos** (todos em `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/sobol_batch-S24/`): `s24_01_varredura_timing.py` → `varredura_timing_TODAS_celulas.csv` (666 manifestos), `resumo_online_por_config.csv`, `resumo_offline_por_config.csv` · `s24_02_quanto_vale_o_zero.py` → `A_proxy_e_cobertura.csv`, `B_medicao_direta_aval.csv`, `C_controle_pisos_matlab.csv` · `s24_03_controles.py` → `D_cobertura_online.csv` (421 células), `E_batch_q10.csv` · `s24_04_calibra_maquina.py` → `F_calibracao_maquina.csv` · `s24_05_medicao_final.py` → `G_medicao_final.csv` (a tabela publicável, mediana de 5 repetições). Nenhuma escrita fora dessa pasta; `resultados_experimentos/` e `src/` só foram lidos.