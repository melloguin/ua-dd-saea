## moead_media-C9b — VEREDITO: **REFUTADO** (classe (3) cai; reclassificar como **(2) desvio sancionado — DI-30 item 3, RATIFICADO**)

**Resumo em 3 linhas**
A *medição* do analista está correta e é reproduzível (28/9/5 em 104 pares, 14/45 células) — não caiu por query nem por critério. O que cai é o **enquadramento como "desvio inexplicado"**: (a) o fenômeno, o mecanismo e o veredito já estão escritos e **ratificados** no REGISTRO (`REGISTRO_DECISOES_IMPLEMENTACAO.md:1348-1353` levantado, `:1369-1371` ratificado — DI-30 item 3), e (b) a estatística que sustenta a palavra "assimetria" é **pseudorreplicação**: a unidade de aleatorização é a **semente**, e há **exatamente 1 semente por braço** — as 45 células de um config partilham o MESMO `np.random.seed`. Experimento direto: refazendo o fit com 27 sementes eu reproduzo o padrão observado na campanha em **4/4 células e 8/8 braços** a partir da semente sozinha, num sklearn diferente.

---

### O que tentei para derrubar (os 4 passos, com números)

**Passo 1 — DECISÃO. ACERTOU EM CHEIO (é aqui que o achado morre).**
`REGISTRO_DECISOES_IMPLEMENTACAO.md:1348-1353` (PARTE A17, "EM ABERTO p/ o autor (DI-30)"), item 3, textual:
> "**D97-b5m/DTLZ2 (o item substantivo):** o GP do obj-2 do b5m/DTLZ2 é DEGENERADO (μ≈0 constante, corr 0,006 com o f real de std 0,588) enquanto o piso, com a MESMA especificação e MESMOS dados, ajusta corr 0,992 — **sensibilidade à semente do treino único (n_restarts consome o RNG global, alg_id 18≠21)**. Dado HONESTO e determinístico; quebra o contraste da ablação NESSE problema. Recomendação da torre: **aceitar como está** (achado científico legítimo; protocolo de sementes é fixo) e documentar como caveat no D97/dissertação"

E a ratificação, `:1369-1371` (PARTE A18 — DI-30):
> "**D97-b5m/DTLZ2** — aceitar o GP degenerado do obj-2 como achado científico legítimo + caveat na dissertação (**RATIFICADO** …). Sem mudança de código (**dado honesto e determinístico; protocolo de sementes é fixo**)."

Corroboram: `:1243-1247` ("os μ da sonda DIFEREM (GPR `n_restarts=9` consome o RNG global, semeado por alg_id 17≠18 ⇒ treinos independentes)… o GP do obj-2 de b5m/DTLZ2 degenera (μ≈0, corr 0,006)") e a **declaração embarcada no próprio run**: `sigma_dict["sigma_*"]` (`src/piso_offline.py:213-220`), presente no header de 45/45 células — "alg_id 21 vs 18 semeia RNGs distintos; os 9 restarts do GPR podem convergir a μ nao identico".

O analista escreveu "**Não** há decisão que sancione taxa de degeneração 3× maior". Falso na substância: a decisão sanciona **o fenômeno e o mecanismo por nome**, e declara o protocolo de sementes **fixo**. Só não cita um número — e o número, como mostro no passo 2, não existe (n=1). **Erro clássico nomeado no briefing: decisão já ratificada que o analista não conhecia.** Agravante diagnóstico: em DI-30 o lado degenerado em DTLZ2 era o **b5m** (semente 0) e o piso era o sadio (corr 0,992); na campanha (semente 42) o sinal **inverteu** — mesmíssima célula, mesma especificação, lado oposto. Isso é a loteria em duas campanhas independentes.

**Passo 2 — QUERY. A medição sobrevive; a ESTATÍSTICA não.**
Reproduzi tudo do zero, lendo a ③ bruta (não o CSV do analista) — `r2_mu_invariante.py`:
- Critério do relatório (WAPE=1,000±1e-4): **28 / 9 / 5** ✔ idêntico. Células: **14/45** ✔.
- Critério **invariante a deslocamento e escala** (`std(μ)/std(f) ≤ 1e-3`, que também pegaria colapso para constante ≠ 0): **28 / 9 / 4**. Discordância com o critério do relatório: 1 par no b5r. Colapso para constante ≠ 0: **0 em todos**. ⇒ **não é artefato de critério**.
- χ² do analista: **21,6 não é o χ² do teste enunciado** — é a soma só sobre as 3 caselas "colapsado", ignorando o complemento (`(28−14)²/14+(9−14)²/14+(5−14)²/14 = 21,57`). O χ² 2×3 correto é **24,93** (p=3,9e-6). Defeito menor, mas sintomático.
- **Pseudorreplicação #1 (duplicata literal)**: `off/{DTLZ2,MMF16_20,WFG9,ZDT1,ZDT4}` ≡ `sweep-small-lhs/{idem}` — **max Δwape = 0,0 em 15/15 grupos**; são o MESMO fit contado duas vezes (armadilha 26 do próprio relatório). 12 dos 104 pares são cópias.
- **Escada de unidade de análise** (`r5_escada_unidades.csv`):

| unidade | n/config | piso | b5m | b5r | razão | χ² | p |
|---|---:|---:|---:|---:|---:|---:|---|
| par célula×objetivo (o do relatório) | 104 | 28 | 9 | 5 | 3,11 | 24,93 | 3,9e-06 |
| par, dedup do re-run | 92 | 25 | 9 | 5 | 2,78 | 20,07 | 4,4e-05 |
| **CÉLULA (1 fit), dedup** | 40 | 13 | 5 | 3 | 2,60 | 9,70 | 0,0078 |
| **PROBLEMA (1 paisagem)** | 25 | 8 | 4 | 3 | 2,00 | 3,50 | **0,174 (n.s.)** |
| par, sem os 2 problemas dominantes | 74 | 10 | 7 | 5 | 1,43 | 1,92 | 0,383 |

  **64% dos colapsos do piso (18/28) vêm de 2 problemas** (DTLZ2 12, MMF16_20 6) — que são exatamente 2 dos 5 problemas replicados 5× no grid pelo sweep. Permutação com cluster=problema (20.000 sorteios): obs 28, nula média 14,0, p95 25, **p = 0,0098**. McNemar célula-dedup: 8×0, p=0,0078. Controle negativo: **b5m × b5r = 9 vs 5, Fisher p = 0,41** — dois configs que ambos usam σ e diferem entre si só pelo `alg_id` (18 vs 17) exibem a mesma espécie de "assimetria", só que menor.

**Passo 3 — CÓDIGO. Responde os 3 pedidos (i)(ii)(iii) da §8 e mata o "viés de 3×".**
- (i) `src/piso_offline.py:294-295` e `src/b5_prob.py:287-288` são a **única** semeadura de cada run: `np.random.seed(H.iteration_seed(base, _ALG_ID, 0, USO_NUMPY, bits32=True))`. `iteration_seed(base, alg_id, iteracao, uso_id)` (`src/standalone_harness.py:425-439`) **não recebe problema nem exp**, `iteracao` é o literal `0`, `base = seed_base(alg,42) = 42`. `_ALG_ID` = **21** (piso, `piso_offline.py:72`) contra **{b5r:17, b5m:18}** (`b5_prob.py:56`). Sementes efetivas: piso **4248879191**, b5m **3248766207**, b5r **2863622864**. Entre a semente e `problem.train(SurrogateKriging)` (`piso_offline.py:351` / `b5_prob.py:343`) os dois runners são **linha a linha o mesmo fluxo** (mesmo `load_offline_budget`, mesmo `load_sonda`, mesmo `DataProblem`). ⇒ **as 45 células de um config começam o fit do GPR do MESMO estado MT19937**, e os três braços diferem por **um único inteiro de 32 bits, sorteado uma vez**.
- (ii) `y` é o mesmo array: ambos montam `pd.DataFrame(np.hstack((X_ds,F_ds)), columns=xn+yn)` na mesma ordem, e verifiquei a ① dos 3 configs em 7 células (incl. as duas de n=2000): **maxΔX = 0 e maxΔF = 0 bit-a-bit em 7/7**. Sem flip, sem reordenação, mesmo vendor (`_VENDOR = algorithms/b5_Prob-RVEA` nos dois — `piso_offline.py:86`, `b5_prob.py:70`).
- (iii) `algorithms/b5_Prob-RVEA/desdeo_problem/surrogatemodels/SurrogateKriging.py:23-24`: `kernel = C(1.0,(1e-3,1e3))*RBF(10,(1e-2,1e2))`; `GaussianProcessRegressor(alpha=0, kernel=kernel, n_restarts_optimizer=9)` — `normalize_y` ausente ⇒ **False**; `random_state` ausente ⇒ **None** ⇒ os 9 restarts sorteiam θ₀ do **RandomState GLOBAL**. É **um só arquivo, compartilhado pelos dois lados**. Não existe caminho de código pelo qual o piso possa degenerar *sistematicamente* mais.

**Passo 4 — CONTROLE POSITIVO/NEGATIVO (o experimento que fecha).** `r3_semente_experimento.py`: mesmo dataset ① (bit-idêntico), mesma especificação, **27 sementes** (as 3 reais + 24 arbitrárias), refit numa implementação independente minha (**sklearn 1.9.0**, contra 0.21.3 da campanha):

| célula | sementes com ≥1 colapso | % de fits colapsados | semente REAL do piso | semente REAL do b5m | campanha (piso/b5m) |
|---|---:|---:|---:|---:|---|
| off/DTLZ2 (a "célula-prova") | **11/27** | 18,5% | **3/3** | **0/3** | **3 / 0** ✔ |
| off/DTLZ1 | 26/27 | 66,7% | 2 | 3 | **2 / 3** ✔ |
| off/DTLZ3 | 27/27 | 82,7% | 2 | 3 | **2 / 3** ✔ |
| off/ZDT6 | 10/27 | 20,4% | 1 | 0 | **1 / 0** ✔ |

**4/4 células, 8/8 braços previstos exatamente a partir de (dataset, semente)** — inclusive a célula-prova do analista, em que o piso colapsa nos 3 objetivos e o b5m em nenhum. A "identidade do config" entra na predição **apenas pelo inteiro `_ALG_ID`**.

---

### Por que caiu

O achado exige que a diferença de taxa seja um **efeito de config**. Não é: é **uma realização de uma variável aleatória com n = 1 por braço**. O `np.random.seed` não depende da célula, logo a "taxa de colapso do config sobre 45 células" é função determinística de **um** inteiro; os 104 pares são 104 leituras correlacionadas de **um** sorteio (12 delas literalmente o mesmo fit duplicado, 12 do mesmo problema DTLZ2, 6 do mesmo MMF16_20). Qualquer χ²/Fisher/McNemar sobre células é pseudorreplicação. Quando a unidade sobe para a paisagem — o mais grosso que os dados permitem — **p = 0,17, não significativo**. E o experimento direto mostra que, na célula que sustenta o argumento, a moeda tem P(colapso) ≈ 0,41 por semente: o piso tirou a ruim, o b5m a boa. Causa nomeada do falso-positivo: **(a) decisão ratificada desconhecida pelo analista (DI-30 item 3 / PARTE A18) + (b) pseudorreplicação de um sorteio único**.

*O que NÃO caiu e deve ser preservado*: a medição (28/9/5 · 14/45) e o **caveat analítico** — em 14/45 células um dos lados tem GP degenerado e ali o contraste não mede σ. O conjunto confundido é o mesmo para os três configs (união piso∪b5m∪b5r = as mesmas 14 células).

---

### Enquadramento e bússola D29

**CONFIRMADO como (b) COMPORTAMENTO LEGÍTIMO** sob o nosso desenho — mas do achado *correto*, não do achado enunciado. Reclassificar C9b de **(3) 🎯 → (2) desvio sancionado**, citando **DI-30 item 3 (PARTE A17:1348-1353, ratificado PARTE A18:1369-1371)** + **DI-28** + `sigma_dict` embarcado.
**Bússola D29: 🟠 laranja (detalhe de implementação → segue o CÓDIGO)** — `normalize_y=False`/`alpha=0`/kernel isotrópico com bounds fechados são do vendor DESDEO (já é o enquadramento dado ao C9a); a semeadura por `alg_id` é convenção D62/D91 nossa, **🟢 verde declarada** (DI-28 item 4: "Semeadura por convenção D62 RATIFICADA como implementada"). **Nenhum item vermelho, azul ou roxo. Não há BUG. Não há dado corrompido.** O único resíduo é **(d) defeito de DOC**: o relatório publica um p-valor pseudorreplicado.

---

### Impacto

1. **Nenhuma célula sai da análise.** Os dados são honestos e determinísticos (DI-30, literal).
2. **Muda número publicado:** apagar de `f5/relatorios_config/moead_media.md` (§2.1 linha C9b, §7 item 4, §8) o par **"3,1× · χ²=21,6 · p<1e-4"**. É pseudorreplicado *e* aritmeticamente errado (o χ² 2×3 seria 24,93). Substituir por: *"com 1 semente, 8/25 paisagens (piso) × 4/25 (b5m) × 3/25 (b5r), χ²=3,50, p=0,17 — não separável de sorteio; mecanismo declarado em DI-28/DI-30 item 3"*.
3. **SCORE:** o §7.4 do relatório diz que este item "é o que impede 9,5+". Com C9b em (2), **`moead_media` 9,0 → 9,5**; `scores_f53.csv` a atualizar. O b5m/b5r herdam a mesma nota de leitura.
4. **F5.5 / D97:** o caveat das **14/45 células** permanece obrigatório, com a redação corrigida — não é "o piso degenera mais", é "sob a semente fixa, um dos lados degenerou". A direção **não é sistemática**: em DTLZ1 e DTLZ3 quem colapsa mais é o **b5m** (3 vs 2 em ambos), e em ZDT6 o piso colapsa **e ganha 61×** (IGD+⑦ 0,108 vs 6,64). Nas 25 `off`: 6 confundidas / 19 limpas; piso pior que b5m em 16/25 (todas) e 11/19 (limpas) — a leitura da ablação **não se inverte**.
5. **Torre:** entra 1 item de doc — "χ² de taxa entre configs com semente única é pseudorreplicação" — que vale para **qualquer** contraste de quantidade de treino estocástico entre configs (b5m×b5r, c311, e103).

---

### Ação p/ F5.7 + custo

| # | ação | custo |
|---|---|---|
| 1 | **Reclassificar C9b (3)→(2)** citando DI-30 item 3; remover χ²/p do relatório e do `scores_f53.csv`; subir `moead_media` para 9,5. | ~20 min de edição, **0 CPU** |
| 2 | **M8/M9, 30 sementes = a única medição válida.** Só com 30 sementes há 30 réplicas da unidade de aleatorização. Já planejado — **não gerar re-run extra na F5.7 por causa deste item**. | **0 adicional** |
| 3 | **Sugestão à torre, decisão do AUTOR (D81):** hoje `iteration_seed(base, alg_id, **0**, uso)` não depende da célula ⇒ as 45 células de um config compartilham o mesmo stream de restarts. Passar a célula (ou `iteracao`) para a semente elevaria o n efetivo de 1 para 45 por config **a custo zero de CPU**. **Não implementar sem ratificação** — muda a semeadura de toda a campanha e invalidaria a comparabilidade com o freeze `rodada-42`. | decisão; se aceita, ~2 linhas + re-run completo |
| 4 | Gravar `modelo_hp` **nos dois lados** (sugestão da §8 do relatório): compatível com o *racional* de DI-30.B2 (a assimetria que ela evita não existe se ambos gravarem), e tornaria o diagnóstico direto (θ no bound inferior). Só vale **acoplado ao M8/M9**, não como re-run isolado. | 1 linha em cada runner + o re-run já previsto; isolado seria ~40 h (b5m) + 2,2 h (piso) |

**Evidências/scripts** (READ-ONLY nos dados; único local de escrita): `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/f5/baterias/f54/moead_media-C9b/` — `r1_recontagem.py` + `r1_recontagem.json` + `r1_pares.csv` (reprodução, dedup do re-run, permutação com cluster, McNemar) · `r2_mu_invariante.py` + `r2_mu_invariante.csv` + `.json` (recontagem direta da ③ com critério invariante a deslocamento/escala) · `r3_semente_experimento.py` + `r3_log_parcial_8celulas.txt` (o experimento das 27 sementes; 4 células, 8/8 braços reproduzidos) · `r4_loteria_semente.py` (distribuição nula da semente, pronto para rodar sobre o JSON) · `r5_escada_unidades.csv` (a escada de unidade de análise). Interpretador `/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python`. Uma reexecução ampliada do `r3` (DTLZ4/BBOB_F17/ZDT1/WFG9) ficou em curso e é dispensável para o veredito.