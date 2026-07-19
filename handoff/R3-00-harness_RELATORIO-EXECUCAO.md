# R3-00-harness — RELATÓRIO DE EXECUÇÃO (a narrativa do processo)

> Companheiro do `handoff/R3-00-harness.md` (que é o *o quê*). Este é o *como* —
> o que aconteceu na sessão, na ordem em que aconteceu, incluindo o que deu
> errado. Escrito para a torre entender as decisões sem ter que reconstruí-las.

## 1. O bloqueio de faixa logo no PASSO 1 (e o D81)

O cartão manda o harness nascer com o timing v5.2.1 COMPLETO e os hooks de sonda
nativos. Ao mapear as APIs, percebi que **as três exigências eram inalcançáveis**
sem editar `src/export.py` — que o próprio cartão me PROÍBE (faixa do
retrofit-BoTorch):

| exigência | por quê era impossível |
|---|---|
| ④ `tempo_pred_sonda_s`/`tempo_geracao_s` | `timing_schema()` tinha 5 campos literais; chaves extras nas rows eram descartadas em SILÊNCIO (o helper `get()` em `export.py:337` era código morto) |
| ④ `tempo_busca_s` obrigatório | cravado `nullable=True`; `Schema.equals` compara nulabilidade |
| ③ `fe_treino_max` | ausente do schema; `surrogate_row` sem `**kwargs` |
| ③ sonda × busca na mesma tabela | `regime` era ESCALAR por chamada (broadcast); a 2ª escrita SOBRESCREVIA a 1ª |

Antes de escalar, **tentei refutar a mim mesmo**: 4 lentes independentes (API,
pyarrow, naming/paths, gate), com reprodução empírica. **4/4 não refutaram** — e
a lente do gate achou o argumento mais curto: `_check_export_schema` constrói o
esperado a partir de `export.*_schema()`, então o gate é um **espelho** do
`export.py`; duplicar o writer também reprovaria.

Escalei por **D81** com 4 opções e uma recomendação. O autor respondeu que o
retrofit-BoTorch já havia fechado. **Não aceitei a informação de plano:**
conferi no repo e vi que o topo do log havia mudado de `377e638` para `8e08d61`
durante a sessão — 11 commits `[DI09-R2]`, com as 3 colunas em
`export.py:163/181-182/270`. Refiz o recon (o mapa anterior estava obsoleto) e
segui. **`export.py` não foi tocado por mim em momento algum.**

*Lição para a torre:* o paralelismo triplo funcionou, mas por pouco — eu quase
desenhei um harness em volta de uma limitação que deixou de existir no meio da
sessão. Vale a pena a torre sinalizar landings de faixa cruzada.

## 2. O molde offline saiu barato (o e103 pagou a conta)

`load_dataset` + `load_offline_budget` + `offline_guard` foram diretos porque o
`handoff/R1-e103.md` §2 já tinha o desenho provado em MATLAB. Duas coisas que
valeram a leitura atenta:

- **`FEBudget.evaluate(x, true_f)` quer um CALLABLE**, não o array. O primeiro
  esboço passava `F[i]` e estourava. O `lambda _x, _f=F[i]: _f` fecha sobre `i`
  por default-arg de propósito — ligar a variável do laço tarde daria a ÚLTIMA
  linha do dataset a todas as FEs, e o CP-init de `f_hash` teria pego isso (que
  é exatamente o valor de ter os dois hashes).
- **`exhausted` é property, não método.** `if not bud.exhausted()` avaliava um
  bool como callable.

Ambos pegos no primeiro smoke, antes de qualquer dado.

## 3. O defeito que só apareceu porque comparei as DUAS rotas

O STUB rodou verde de primeira: FE exato, 5 camadas, CP-init, sonda. Poderia ter
fechado ali. Em vez disso rodei o `final_eval --force` sobre o mesmo run, para
comparar a rota retroativa (a do e103) com a nativa — e os ND não bateram:
**13 × 15**.

Investiguei achando que era truncamento float32. Não era: `|ΔX|max = 1.63`.
Eram **pontos diferentes**. O laço do STUB escrevia a ③ com `pop`, produzia
`filhos`, e ao fim do laço `pop == filhos` — então o `__final` saía da **prole da
última geração, que a ③ nunca registrou**.

Por que isso importa muito além do meu STUB: para o **e103** (MATLAB, já
executado) a ③ é a **única** fonte da ⑦. Uma ⑦ irreconstituível faria o
retroativo avaliar outro conjunto, em silêncio, com as duas camadas
bem-formadas.

Corrigi o STUB (`pop_final`) **e** transformei o invariante em **check
permanente** — que é a parte que interessa aos 4 cartões offline que vêm.

## 4. A revisão adversarial (o que ela custou e o que rendeu)

31 agentes, 5 lentes de revisão + verificação cética por achado (default =
falso-positivo), 753 tool calls. **26 achados brutos → 7 confirmados**
(1 crítico, 3 major, 3 minor), 19 refutados.

O crítico é o que eu mais gostaria de ter pego sozinho e não peguei:

> **A tolerância de bounds do `evaluate_final` era `1e-9` FIXO** — ~100× menor
> que o quantum do float32 perto de 1.0. Como todo X que chega ali passou por
> uma camada float32 (D53) e clipar no bound é rotina de MOEA, `MMF11_L`
> (xl=0.1, xu=1.1 — o único dos 25 canônicos com bounds não representáveis em
> float32) produzia uma ⑦ que o **próprio `--check` rejeitava em 8 de 29
> sementes**. Eu havia testado MMF1/ZDT1/DTLZ2 e nenhum expõe o caso.

Os outros dois que valem registro porque são de *classe*, não de detalhe:

- **Dois checks do meu gate eram tautológicos.** `_r3_subprocess_probe` dizia
  "pin D79 no FILHO" e só conferia que o processo terminou — o verificador deu
  VERDE com `OMP_NUM_THREADS=8` no filho. `_r3_env_resolution` comparava duas
  strings do `envs.json`, verdadeiro por construção. Um gate que não pode
  ficar vermelho não é gate. Agora o filho **devolve** a evidência e o pai a
  exige; e o check de env prova o roteamento e a sentinela.
- **O subprocess-por-venv era ferramenta, não mecanismo.** `run_in_venv`
  existia, mas nada roteava para ele — `experiment.run` despacha in-process, e o
  despachante serial e o paralelo (loky, que REUSA workers) chamam `run()`
  direto. A garantia N.1.2 vivia num **comentário**. O verificador reproduziu a
  falha com os overlays REAIS do repo. Virou mecanismo em 3 camadas
  (`VENV_ONLY_ALGS` + roteamento + sentinela `assert_overlay_coerente`).

Todos os 7 foram corrigidos **e cobertos por regressão** (+19 testes só para
eles). Vale dizer que o mesmo processo também me poupou de "consertar" 19 coisas
que não eram problema — incluindo uma correção sugerida que teria **degradado**
o regime offline.

## 5. Um achado que não é meu, mas que a torre precisa ver

Ao instrumentar a cadência da sonda, cruzei com o `652e24d`
(`[DI09-R2] D81: cadencia da SONDA diverge entre Python e MATLAB`): **A-12**
segue sem decisão. Python dá blocos em 1,2,4,6…; MATLAB em 1,3,5,7…

Segui a fórmula **Python** por coerência com o R2, e deixei isso explícito no
docstring do `sonda_due`. **A boa notícia para a R3:** o alcance é pequeno —
só os 3 configs ONLINE (c122, c149, e81) usam `sonda_due`; os 4 offline têm
cadência "1× por modelo treinado" e são **imunes**. Se a torre cravar a fórmula
MATLAB, o conserto do meu lado é 1 linha.

Também MEDI uma coisa que contradiz o texto do contrato: **`pymoo 0.6.2` não
desloca `np.random` nem `random`** — nem com `seed=`, nem sem. A premissa do
N.2.3 vale para o pymoo ANTIGO dos venvs `env_b5`/`env_c311` (onde b5/c311
rodam, e onde a guarda é indispensável), mas isso torna a checagem herdada
"guarda provada contra `pymoo.minimize` REAL" **vacuamente verde** no env-main:
ela passaria mesmo se `preserve_global_rng` fosse um `pass`. Endureci o meu lado
(prova mecânica + sentinela de versão) e **sugiro o mesmo ao check do R2-00**,
que está fora da minha faixa.

## 6. Números

| | |
|---|---|
| Gate R3-00 | exit 0 em MMF1, ZDT1, DTLZ2 **e MMF11_L** (21/21 checks) |
| FE (offline = dataset) | 61 · 929 · 371 · 61 — todos `31D−1` exatos |
| ③ do STUB | 2488 (MMF1) / 9432 (ZDT1) linhas = 2000 sonda + busca |
| ⑦ do STUB | 61 / 929 finais; 15 / 41 ND pós-real |
| Wall do STUB | ~2,5 s (MMF1) · ~3,0 s (ZDT1) — é o STUB, não o harness |
| Suíte | **193 OK (1 skip)** — era 122 (+71) |
| Regressão | F0-01..04 · R2-00 (MMF1, ZDT1) · preflight — todos exit 0 |
| Não rodados | gates R1 e R2-c\* (faixas ativas — instrução do cartão) |
| MMF11_L pós-fix | 30/30 sementes (antes: 8/29 reprovavam) |

## 7. O que NÃO fiz, e por quê

- **O `__final` retroativo do e103** — a REGRA DE ORDEM do cartão. No
  encerramento o log tem `[DI09-R1] infra` e `[DI09-R1] c217`, mas **não**
  `[DI09-R1] e103`. Comando pronto no handoff §REGRA DE ORDEM.
- **`experiments.py::_run_one`** (o bloqueador B-1/A-9 herdado do retrofit R2,
  que apaga o manifesto do runner). Não está na lista de faixa do meu cartão e a
  correção muda a semântica de resume/`run_done` — é DI-06/M7.
- **`gcs.plan_targets`** — resolvi o espelho da ⑦ dentro do `dual_write_run`
  (minha faixa) em vez de mexer em `gcs.py`. Fica a sugestão de unificar.
- **Extrair o `load_sonda` duplicado** para um módulo compartilhado — exigiria
  editar `botorch_harness.py`. Há teste de equivalência enquanto isso.
- **Descomentar os 7 loaders R3** — cada cartão descomenta o seu.
