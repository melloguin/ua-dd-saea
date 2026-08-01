# INVENTÁRIO DAS CÉLULAS QUE NÃO FECHARAM — semente 42

**Data:** 2026-07-28 · **Fonte:** `gs://mestrado_experiments/_censo/censo_bucket_42_FINAL.csv`
**Total:** 695 células · **666 OK (95,8%)** · **29 não-OK**

> **Nota sobre o número.** São **29**, não 32. 695 − 666 = 29. O "32" que circulou é o tamanho do *lote de recuperação do Mac* de 28/07 (32 células, das quais 31 fecharam) — coisa diferente.

---

## 1. As 29, uma por linha

Legenda de categoria: **A** retirada por desenho · **B** aborto por projeção de custo (sancionado, DI-38a) · **C** falha algorítmica real · **D** morte de processo sem manifesto.

| # | algoritmo | papel | problema | D | maxFE | experimento | cat. | motivo (resumo) |
|---:|---|---|---|---:|---:|---|:--:|---|
| 1 | c154 | proposta online | DTLZ2 | 12 | 371 | q10 (`batch`) | A | DI-40 — retirada do roster antes de rodar |
| 2 | c154 | proposta online | MMF16_20 | 20 | 619 | q10 (`batch`) | A | DI-40 |
| 3 | c154 | proposta online | WFG9 | 22 | 681 | q10 (`batch`) | A | DI-40 |
| 4 | c154 | proposta online | ZDT1 | 30 | 929 | q10 (`batch`) | A | DI-40 |
| 5 | c154 | proposta online | ZDT4 | 10 | 309 | q10 (`batch`) | A | DI-40 |
| 6 | c262 | proposta online | DTLZ2 | 12 | 371 | q10 (`batch`) | B | `teto_wall` por projeção |
| 7 | c262 | proposta online | MMF16_20 | 20 | 619 | q10 (`batch`) | B | `teto_wall` por projeção |
| 8 | c262 | proposta online | WFG9 | 22 | 681 | q10 (`batch`) | B | `teto_wall` por projeção |
| 9 | c262 | proposta online | ZDT1 | 30 | 929 | q10 (`batch`) | B | `teto_wall` por projeção |
| 10 | c262 | proposta online | ZDT4 | 10 | 309 | q10 (`batch`) | B | `teto_wall` por projeção |
| 11 | c154 | proposta online | DTLZ2 | 12 | 371 | main online | B | `teto_wall` por projeção |
| 12 | c154 | proposta online | DTLZ3 | 12 | 371 | main online | B | `teto_wall` por projeção |
| 13 | c154 | proposta online | DTLZ4 | 12 | 371 | main online | B | `teto_wall` por projeção |
| 14 | c154 | proposta online | MMF16_20 | 20 | 619 | main online | B | `teto_wall` por projeção |
| 15 | c154 | proposta online | DTLZ7 | 22 | 681 | main online | B | `teto_wall` por projeção |
| 16 | c154 | proposta online | WFG1 | 22 | 681 | main online | B | `teto_wall` por projeção |
| 17 | c154 | proposta online | WFG2 | 22 | 681 | main online | B | `teto_wall` por projeção |
| 18 | c154 | proposta online | WFG4 | 22 | 681 | main online | B | `teto_wall` por projeção |
| 19 | c154 | proposta online | WFG5 | 22 | 681 | main online | B | `teto_wall` por projeção |
| 20 | c154 | proposta online | WFG9 | 22 | 681 | main online | B | `teto_wall` por projeção |
| 21 | c154 | proposta online | ZDT1 | 30 | 929 | main online | B | `teto_wall` por projeção |
| 22 | c154 | proposta online | ZDT3 | 30 | 929 | main online | B | `teto_wall` por projeção |
| 23 | c262 | proposta online | DTLZ7 | 22 | 681 | main online | B | `teto_wall` por projeção |
| 24 | c262 | proposta online | MMF16_20 | 20 | 619 | main online | B | `teto_wall` por projeção |
| 25 | c262 | proposta online | ZDT3 | 30 | 929 | main online | B | `teto_wall` por projeção |
| 26 | c154 | proposta online | ZDT6 | 10 | 309 | main online | C | `random_search_optimizer` falhou nas 3 tentativas da escada (it 62) |
| 27 | c154 | proposta online | BBOB_F55 | 10 | 309 | main online | C | idem (it 55) |
| 28 | c262 | proposta online | WFG1 | 22 | 681 | main online | C | `botorch ModelFittingError: All attempts to fit the model have failed` |
| 29 | b1 | proposta online | DTLZ4 | 12 | 371 | main online | D | `least squares problem is underdetermined` (footer do `.jsonl`) |

### Consolidado

| categoria | células | cor |
|---|---:|---|
| A · retiradas por desenho (DI-40) | 5 | ⚪ sancionado |
| B · aborto por projeção de custo (DI-38a) | 20 | ⚪ sancionado |
| C · falha algorítmica real | 3 | 🔴 |
| D · morte sem manifesto | 1 | 🔴 |

**Apenas 3 algoritmos aparecem:** `c154` (19 células), `c262` (9), `b1` (1).

**Zero falhas** entre os **pisos** (nsga2, nsga3, moead, smsemoa, sobol_batch), **zero** no **main offline** (125/125) e **zero** no **swap offline** (120/120). Todo o déficit está no regime online e no q10, e concentrado nos dois algoritmos BoTorch/qNEHVI mais pesados.

*(A identidade nominal das 12 do `main/c154` e das 3 do `main/c262` vem do corte por dimensão e dos processos que estavam em voo na v5/v6 no encerramento; a coluna `problema` do CSV do censo confirma célula a célula.)*

---

## 2. Categoria A — retiradas por desenho (5 células)

**`batch/c154` nos 5 problemas do q10.**

### Por que não rodou

Não é falha: **nunca foi despachada**. A decisão **DI-40** tirou `batch/c154` do roster antes da rodada, porque a combinação (algoritmo mais caro da campanha) × (aquisição em lote q=10, que multiplica o custo de aquisição por iteração) dava aborto certo com zero parquet produzido. Rodar seria queimar ~5 h-core por célula para obter cinco abortos.

### O que aprendemos

**Um número da própria decisão estava errado, e a medição corrigiu.** A DI-40 justificava a retirada citando "~6,3 h por célula". Quando o `c154` finalmente rodou no `main` da v5, o trip de projeção mediu entre **0,87 h e 2,99 h**, média **1,47 h** — quatro vezes menor. A decisão continua correta (aborto certo é aborto certo), mas a justificativa numérica precisa ser corrigida no `REGISTRO_DECISOES_IMPLEMENTACAO.md`.

A lição operacional é mais geral: **decisão de retirada baseada em estimativa precisa ser reauditada quando a medição chega.** Se o número real tivesse sido 4× *maior* em vez de menor, a retirada teria sido tímida demais — havia outras células a retirar.

---

## 3. Categoria B — aborto por projeção de custo (20 células)

**`main/c154` × 12 (todas de D≥12) · `main/c262` × 3 · `batch/c262` × 5 (5/5, o experimento q10 do c262 inteiro).**

### O mecanismo, em detalhe

O `_WallClockProjector` (`src/c262_qnehvi.py`, ~linha 408) tem **dois critérios de parada, não um**:

1. **Projeção.** Ajusta o custo de refit do GP como `t_fit ≈ c·n³` sobre as iterações já observadas, projeta quanto falta para fechar os `maxFE = 31D−1` avaliações, e compara **`decorrido + projetado > teto`**. Só arma depois de 10 amostras — ou seja, **na 11ª iteração**.
2. **Relógio.** `elapsed > max_wall_s`.

As 20 células pararam pelo critério **(1)**, e o manifesto registra isso literalmente:

```
WallClockAbort("...por 'projecao': Xs decorridos + Ys projetados > 43200s")
```

Isso tem uma consequência contraintuitiva: **a célula aborta cedo, em poucas horas, não depois de esgotar a janela.** Ela nem chega perto do teto — ela é interrompida assim que o projetor conclui que não chegaria lá.

### O teste que fizemos — e por que ele vale como resultado

Numa janela exploratória (27–28/07, com autorização explícita do autor e rompendo a DI-35.5), o teto foi ampliado de **12 h para 48 h** e as 23 células foram redisparadas com `--force`. Resultado sobre as 14 que fecharam nessa janela: **`ok = 0`**. Reabortaram, e reabortaram rápido.

A leitura ingênua seria "teto maior não recupera nada". **Está errada, e importa corrigir**: o teto *é* um limiar sobre `decorrido + projetado`, e ampliá-lo resgataria qualquer célula cuja projeção caísse na faixa nova. A leitura correta é mais forte:

> **A razão projeção/orçamento é bimodal.** Ou a célula fecha com folga, ou estoura por **ordem de grandeza**. As projeções observadas foram de **41 a 190 horas** contra um teto de 12 h. Não existe faixa marginal a resgatar em escala.

Prova indireta: 8 células ainda estavam **vivas** ao fim da janela (3 de `main/c154` em DTLZ2/3/4 e 5 de `c262`) — são exatamente as poucas cuja projeção caía entre 12 h e 48 h. Foram encerradas por decisão do operador para liberar as VMs, então nunca saberemos se fechariam; mas a existência delas é o que sustenta a formulação correta acima, e não a ingênua.

### O que aprendemos

**1 · Isto não é limitação de infraestrutura. É propriedade do algoritmo — e é resultado publicável.**
`c154` e `c262` são BoTorch/qNEHVI. O refit exato de GP cresce com `n³` no número de pontos, e o orçamento `maxFE = 31D−1` coloca o run exatamente na região onde o refit **domina o custo total**, engolindo o tempo que deveria ir para avaliação. Com D≥12 o orçamento cresce linearmente com D enquanto o custo por iteração cresce cubicamente com `n` — e `n` cresce com o orçamento. É uma cauda que nenhuma máquina razoável alcança.

O enunciado defensável para a dissertação: *sob orçamento `31D−1`, a abordagem qNEHVI com refit exato de GP não escala além de D≈10–12; a barreira é o custo de refit, não a qualidade da busca.* Isso é uma contribuição negativa legítima e foi **testada**, não suposta.

**2 · O corte de viabilidade é nítido em D.**
O `c154` completou **exatamente** os problemas com **D≤10** (menos os dois onde o amostrador falhou) e abortou **exatamente** os de **D≥12**. Não há zona cinzenta. O `c262` aguentou mais fundo (21/25) mas quebrou nos mesmos extremos: MMF16_20 (D=20), DTLZ7 (D=22), ZDT3 (D=30).

**3 · O q10 amplifica.** `batch/c262` abortou **5/5**, quatro delas abaixo de 30% de progresso — enquanto `main/c262` fechou 21/25. Propor 10 pontos por iteração multiplica o custo da aquisição sem diluir o custo do refit. **O q10 é onde o método quebra primeiro.**

**4 · Consequência de desenho.** O padrão da DI-40 deveria ser estendido, agora com base empírica em vez de projeção: **`batch/c262`** (5/5) e **`main/c154` com D≥12** são candidatos naturais a retirada formal do roster. É decisão do autor.

**5 · Consequência de ferramenta.** O driver `lote3s.sh` não repassava `--teto-s` ao `experiments.py`, o que obrigou a sair do driver e disparar à mão para este teste. Corrigido em 28/07 (`LOTE_TETO_S`), com aviso explícito de que ampliar o teto rompe a DI-35.5.

---

## 4. Categoria C — falhas algorítmicas reais (3 células)

### 4.1 `main/c154` / ZDT6 e `main/c154` / BBOB_F55 — o amostrador JES

```
RuntimeError: c154 rota (a): random_search_optimizer falhou nas 3 tentativas
da escada p/ a amostra 2 (it 62)     [ZDT6]
                                (it 55)     [BBOB_F55]
```

**O que aconteceu.** O `c154` usa uma aquisição do tipo JES (Joint Entropy Search), que precisa amostrar pontos ótimos do posterior. Esse passo é feito por `random_search_optimizer` com uma *escada* de tentativas (relaxações sucessivas). Nas duas células, as três tentativas da escada falharam em produzir a **amostra 2** — o otimizador não encontrou candidato válido, e o run levantou exceção em vez de continuar com amostragem degradada.

**O padrão é informativo.** Os dois problemas têm **D=10** e são **multimodais/deceptivos** (ZDT6 tem frente não uniforme com densidade concentrada; BBOB_F55 é da família de funções com estrutura global fraca). As falhas ocorreram em iterações adiantadas (55 e 62 de ~200), ou seja, **depois** que o posterior já tinha muitos pontos — não é falha de inicialização.

**Aprendizado.** O amostrador de ótimos do JES é o ponto frágil da implementação: quando o posterior fica multimodal e mal-condicionado, a busca aleatória não encontra a segunda amostra e não há caminho de degradação graciosa. Duas linhas de ação, ambas do autor: (a) tratar como resultado — "o JES é frágil nesta classe de problema sob orçamento apertado" — e reportar; (b) tratar como defeito de implementação e checar contra a referência se o paper prevê fallback quando a amostragem falha. **Não misturar as duas** sem antes olhar a referência: se o paper prevê fallback e nós não implementamos, é infidelidade; se não prevê, é resultado.

### 4.2 `main/c262` / WFG1 — ajuste do modelo

```
botorch.exceptions.errors.ModelFittingError: All attempts to fit the model have failed.
```

**O que aconteceu.** O BoTorch tentou ajustar o GP (todas as tentativas internas de otimização da verossimilhança marginal) e desistiu. Tipicamente é mal-condicionamento da matriz de covariância — pontos quase duplicados, escalas muito díspares entre objetivos, ou hiperparâmetros indo para região degenerada.

**Por que WFG1 especificamente.** WFG1 é notoriamente o mais difícil da família WFG: tem transformações de achatamento e polinomiais que criam uma paisagem com regiões quase planas. Sob `maxFE = 681` e D=22, o GP recebe muitos pontos com valores objetivos quase idênticos — exatamente a condição que degenera a matriz de covariância.

**Aprendizado.** Isolada (1 célula em 25 do `c262`), mas **é o mesmo eixo das outras 24**: o gargalo do `c262` é o GP, seja por custo (categoria B) ou por condicionamento (esta). O algoritmo não tem problema de busca; tem problema de **modelo substituto**. Se a dissertação discutir limitações do `c262`, esse é o eixo único a discutir — o que é uma narrativa mais forte do que três limitações independentes.

---

## 5. Categoria D — morte sem manifesto (1 célula)

### `main/b1` / DTLZ4

```
least squares problem is underdetermined
```
(no **footer do `.jsonl`**, com `status=failed`)

**O que aconteceu.** O `b1` resolve um problema de mínimos quadrados em algum passo interno (ajuste de modelo local, ou projeção). Em DTLZ4 esse sistema saiu **subdeterminado** — menos equações independentes do que incógnitas. DTLZ4 tem uma parametrização com expoente que concentra fortemente as soluções numa região do espaço objetivo; a amostra vira quase degenerada e o posto da matriz cai.

**A evidência é forte.** A célula foi tentada **duas vezes, em duas arquiteturas diferentes** — vm3 (Linux/Intel) e Mac (macOS/arm64) — e falhou identicamente nas duas. **Não é flake, não é infraestrutura, não é BLAS.** É um defeito determinístico do `b1` naquele problema.

**Por que aparece como "sem manifesto".** O stack MATLAB certifica a própria falha no *footer* do `.jsonl`, não no `.manifest.json` (achado **O-21**). Um inventário que só olhe a camada ⑤ classifica isso como `SEM-MANIFESTO` e perde o diagnóstico, que está a um `tail` de distância.

**Aprendizado.** Dois, e os dois valem para além desta célula:

**1 · A assimetria de instrumentação Python × MATLAB é um risco de auditoria.** O Python grava `status`/`stack_trace` no manifesto; o MATLAB grava no footer do `.jsonl`. Qualquer verificador (`is_run_done`, `censo_bucket.py`) que olhe só o manifesto fica cego para metade da evidência. **Correção recomendada: cair para o footer do `.jsonl` quando a camada ⑤ faltar.**

**2 · O footer discrimina falha algorítmica de morte de máquina** (achado **O-22**), e o discriminador é limpo:

| evidência no `.jsonl` | interpretação |
|---|---|
| footer presente, `status=failed`, campo `erro` preenchido | **falha algorítmica real** — o run morreu e soube dizer por quê |
| **sem footer**, arquivo simplesmente para | **morte de máquina** — o processo foi extinto antes de escrever |

Foi assim que separamos esta célula das **6 células de `main/c238`** que morreram juntas em `2026-07-27T01:27:00Z` — cinco parando no mesmo segundo, uma com linha rasgada no meio da escrita. Aquilo foi extinção do host; isto aqui é defeito do algoritmo. As 6 do `c238` foram recuperadas no Mac e hoje estão OK.

---

## 6. Aprendizados transversais

**1 · O ambiente, não a CPU, é o que aloca.** Das 695 células por semente, 345 só rodam onde há MATLAB, 230 só rodam no Mac (venvs `env_b5` py3.7 e `env_c311` py3.8, ambos sob Rosetta) e 120 rodam em qualquer lugar. O Mac — um laptop de 4 processos — é o caminho crítico da campanha inteira e não pode ser ajudado por nenhuma VM. **Com 30 sementes isso vira 6.900 células num laptop.** Provisionar `env_b5`/`env_c311`/`env_e81_qpots` numa VM Linux deixa de ser conveniência e vira pré-requisito do M8.

**2 · Aborto sancionado ≠ falha.** A taxonomia (`teto_wall`/`cache_cap` = ⚪ sancionado, DI-38a) é o que permite dizer "96,5% de cobertura" com honestidade em vez de "temos 29 problemas". Sem essa distinção o relatório vira alarme falso.

**3 · Modelo de custo mente na cauda, e é na cauda que dói.** O único número *estimado* da tabela de custo (`batch/c262` = 4 h) foi o único que errou feio — as 5 células bateram no teto de 12 h. E o `c154` era superestimado em 4×. **Extrapolação log-log entre dois pontos medidos não sobrevive a expoente 3,5.**

**4 · O inventário tem que ser lido do bucket, não das máquinas.** Enquanto o inventário era varredura local, cada máquina offline virava buraco cego. O censo do bucket resolveu isso — e a validação cruzada entre os dois métodos bateu **célula a célula nas 695, sem uma divergência**, o que prova de quebra que o `mirror_run` não perde objeto nos runs bem-sucedidos.

**5 · Mas o `mirror_run` só dispara no fim de run bem-sucedido.** Célula que aborta ou falha **não espelha** — a evidência fica órfã no disco da máquina e morre com ela. Foi por isso que o `rsync` manual das 4 máquinas precisou acontecer **antes** do desligamento. É uma lacuna de desenho que merece item próprio no REGISTRO.

**6 · Provisionamento nunca deveria copiar `data/`.** Cópias herdadas do `data/` durante o provisionamento de VM criaram células com proveniência errada (`batch/e81/ZDT4`, `batch/c149/ZDT4`), que depois subiram por cima dos originais no bucket. Toda célula cujo host real diverge do dono do roster precisa de auditoria.

---

## 7. O que fica para decisão do autor

1. **Corrigir o número da DI-40** no REGISTRO: "~6,3 h por célula" → medido 0,87–2,99 h, média 1,47 h.
2. **Estender a DI-40** para `batch/c262` (5/5 abortadas) e `main/c154` com D≥12 — agora com base empírica.
3. **Registrar o rompimento da DI-35.5** (teto de 48 h na janela exploratória), com o resultado e o achado da §3 como justificativa retrospectiva.
4. **Redigir O-20, O-21 e O-22** no `REGISTRO_OPERACAO_RODADA42.md`.
5. **Registrar que as 8 células vivas foram encerradas por decisão**, não por incidente — sem isso o `.jsonl` truncado delas será lido como morte de máquina numa auditoria futura.
6. **Decidir o enquadramento das 3 falhas reais**: resultado sobre fragilidade do método, ou defeito de implementação a corrigir? Depende da comparação com a referência, que é tarefa da validação de fidelidade.
7. **Resolver a atribuição de máquina de `main/c238`** (dividido entre vm3 e Mac) antes de montar a tabela de tempo do M7.
