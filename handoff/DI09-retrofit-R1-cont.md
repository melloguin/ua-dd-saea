# DI09-retrofit-R1-cont — continuação do retrofit DI-09/DI-10 no stack MATLAB

> **Cartão:** continuação do `DI09-retrofit-R1`. Instrumentação **read-only** (sonda canônica DI-09 +
> enriquecimento DI-10 do `.jsonl`) nos 11 configs MATLAB que faltavam.
> **Estado:** 🟡 **PARCIAL — 7 de 11 configs entregues e verdes.** Faltam **c238, e7, e74, e103**.
> **Ambiente (D81, conferido ANTES de qualquer edição):** MATLAB R2025a Update 1 (25.1) · ponte
> `pyenv` → `~/ponte_teste/bin/python` 3.11, `py.numpy.array([1,2,3]).sum()` = **6** ✓ ·
> venv `mestrado_experimentos_dissertacao`, pyarrow 25.0.0.
> **Data:** 2026-07-19/20.

---

## 0. RESPOSTA DIRETA: a etapa NÃO está 100% pronta

**7 de 11 configs** do escopo estão entregues, validados e commitados. **4 não foram iniciados**
(c238, e7, e74, e103) — os `<alg>_sonda.m` dos quatro **já estão escritos, revisados
adversarialmente e commitados**, mas **não estão ligados** (falta o wiring do arquivo stock, do
`<alg>_instrument.m` e do `run_<alg>`) e **nenhum run foi executado** para eles.

| # | config | problemas | ① bit-a-bit | auditoria | accept.py | commit |
|---|---|---|---|---|---|---|
| 1 | **b1** (ParEGO) | 3/3 | ✅ | ✅ | ✅ exit 0 | `f1ef8b8` |
| 2 | **b4** (CSEA) | 3/3 | ✅ | ✅ | ✅ exit 0 | `76fbbd7` |
| 3 | **b3** (K-RVEA) | 3/3 | ✅ | ✅ | ✅ exit 0 | `f7c5c24` |
| 4–7 | **4 pisos** (nsga2/nsga3/moead/smsemoa) | 12/12 | ✅ | ✅ | ✅ exit 0 | `145fd3d` |
| — | infra transversal | stub 8/8 flags | ✅ | — | — | `7652ad4`, `76fbbd7` |
| — | c217/c141 (revalidados 2×) | MMF1 | ✅ | — | — | — |
| 8 | **c238** (EIM) | 0/2 | ❌ NÃO FEITO | — | — | sonda escrita |
| 9 | **e7** (EDN-ARMOEA) | 0/2 | ❌ NÃO FEITO | — | — | sonda escrita |
| 10 | **e74** (CLMEA) | 0/3 | ❌ NÃO FEITO | — | — | sonda escrita |
| 11 | **e103** (IBEA-MS, offline) | 0/3 | ❌ NÃO FEITO | — | — | sonda escrita |

**Runs executados e validados: 23** (21 do escopo + 2 revalidações). **Provas de não-perturbação
bit-a-bit: 23. Falhas: 0.**

**O teste de aceitação do cartão NÃO foi atingido.** Ele pede 11 configs + 11 provas + regressão
total. Falta também a **regressão total de encerramento** (F0×4 + 13 configs ×MMF1 + preflight +
suíte completa) — não foi executada.

---

## 1. Que código foi rodado, e o que deu

### 1.1 Gate de ambiente (D81 — antes de tudo)
```
/Applications/MATLAB_R2025a.app/bin/matlab -batch "run('envcheck.m')"
```
→ `PYVER=3.11 · PYEXE=/Users/gmello/ponte_teste/bin/python · SOMA=6 · MATLAB=25.1 (R2025a)` ✓

### 1.2 Os três validadores
A sessão anterior **não versionou** os validadores (`handoff/DI09-retrofit-R1.md` §4.5 os deixou "no
scratchpad da sessão"). Foram **reconstruídos do zero**:

| ferramenta | o que checa |
|---|---|
| `naoperturbacao.py <alg> <prob> <sem>` | ① do run vs `_baseline_pre_retrofit`: x/f/fe_index/solution_id/fase **bit-a-bit** (compara os bytes brutos, não com tolerância), + contagem de linhas e dtype |
| `auditar.py <alg> <prob> <sem> [--regime offline] [--piso] [--di10 ...]` | blocos de sonda = S × nº disparos, **contíguos**; **ORDEM DO ARTEFATO** conferida linha a linha contra `data/sonda/sonda_<prob>.parquet` (o invariante que o join por posição exige); `fe_treino_max ≤ fe_final`; ④ com as 5 colunas; `tempo_fit_s` NULL nos pisos; `geracao` NULL na sonda offline **e** inteira na busca; manifesto `timing` preenchido; `n_geracoes` do manifesto == ② ; campos DI-10 no jsonl |
| `scripts/accept.py` (do repo) | gate objetivo: 4 saídas + FE=31D−1 + CP-init |

**Auto-teste dos validadores:** rodados contra o **c141**, que já estava verde e validado pela
sessão anterior — os dois passaram, confirmando que medem o que devem antes de eu confiar neles.

### 1.3 Experimento de controle (antes de tocar em qualquer coisa)
Re-rodei **b1, b4, b3 em MMF1** com o código como estava, para verificar se as mudanças de infra já
em disco (cronômetro do `FEBudget` da DI-12.4, etc.) tinham perturbado as baselines:
→ **as 3 ① idênticas.** Isso estabeleceu que o harness era determinístico e reprodutível, e que
qualquer divergência posterior seria **inequivocamente minha**.

### 1.4 Autoteste de infra (`stub`) — a rede de regressão transversal
`experiment('stub','MMF1',0)` — 8 flags, **todos verdes**:
```
rng_intacto: 1              rng_mesma_sequencia: 1
final_armou_sem_disparar: 1 final_disparou: 1
final_carimbou_armado: 1    final_foi_noop: 1        ← DI-17.5, os dois ramos
sonda_off_linhas: 20000     ger_null_ok: 1  ger_busca_ok: 1  ← DI-13.5 + adendo da torre
```

### 1.5 Resultados por config (o que observei em cada um)

**b1** — MMF1 ① 61×10 · 22 blocos ×2000 · accept 0 · 19 s | DTLZ2 ① 371×21 · 122 blocos · accept 0 ·
167 s | ZDT1 ① 929×38 · **303 blocos = 606.000 linhas** · accept 0 · 2022 s.

**b4** — MMF1 ① 61×10 · 26 blocos · accept 0 · 39 s | DTLZ2 ① 371×21 · 129 blocos · accept 0 ·
198 s | ZDT1 ① 929×38 · 239 blocos · accept 0 · 885 s.

**b3** — MMF1 ① 61×10 · 6 blocos · accept 0 · 8 s | DTLZ2 ① 371×21 · 25 blocos · accept 0 · 41 s |
ZDT1 ① 929×38 · 62 blocos · accept 0 · 539 s.

**4 pisos** — 12 runs, 12 ① idênticas, 12 auditorias verdes, 4 accept 0. Walls 0,3–3,0 s.
`tempo_fit_s` NULL em **31/31, 39/39** linhas da ④ (conferido no parquet, não presumido).

**Em todos:** a ORDEM DO ARTEFATO foi conferida bloco a bloco, e o `n_geracoes` do manifesto bate
com a camada ②.

### 1.6 RE-EXECUÇÃO CONSOLIDADA FINAL (a evidência de fechamento dos 7 configs)

Rodada ao final, de uma vez, sobre **os 23 runs**:

```
GATE 1  NAO-PERTURBACAO : 23/23 verdes, 0 falhas
GATE 2  AUDITORIA       : 23/23 verdes, 0 falhas
GATE 3  accept.py       : 21/21 verdes, 0 falhas
preflight.py            : exit 0 — "pré-voo OK ✓" (1 deferimento intencional, pré-existente)
```

> ⚠ **A suíte Python NÃO foi verificável daqui:** `pytest` não está instalado em nenhum venv
> (`No module named pytest` no venv do mestrado e nos demais). **Nenhum arquivo `.py` foi tocado
> nesta sessão** (faixa proibida), então não há razão para regressão — mas a **verificação está
> ausente** e deve ser feita por quem tiver o ambiente. O handoff anterior reportava "122 testes OK",
> então o pytest existia em algum momento.

---

## 2. Infra transversal — o que mudou e por quê (afeta os 9 configs com sonda)

### 2.1 `geracao` NULLABLE na ③ *(adendo da torre, DI-13.5)*
`int32(NaN)` = **0** em MATLAB ⇒ o bloco de sonda OFFLINE do e103 viraria silenciosamente
"geração 0". Aplicado o **mesmo idioma do `n_acumulado` da ④**: a coluna fica `double` (NaN→NULL) se
houver qualquer ausente; só casta `int32` quando completa.
- `write_surrogate`: `GER = NaN(n,1)` + atribuição guardada + branch do cast.
- `RunBuffer.addGeneration`: **NaN é o portador do NULL**, tratado como "geração nula" e não como
  "sem geração" — um `[]` cairia no early-return e **descartaria o bloco inteiro em silêncio**.
- **Provado bit-neutro:** c217/c141/b1/b4 seguem com `geracao` `int32`, 0 nulls.

### 2.2 `finalProbe` usa `g_armado`, não `buf.gen` *(DI-17.5)*
Em configs de overshoot ZERO (c238), a `PlatEMO:Termination` sai do **topo do ciclo seguinte**
(`ALGORITHM.m:128`) **depois** de o `outputFcn` já ter bumpado ⇒ `buf.gen` pós-Solve aponta uma
geração **nunca armada**, e o bloco final sairia carimbado com ela. Agora o `SondaState` guarda a
geração do modelo armado. O argumento posicional legado é aceito e ignorado.

### 2.3 `S` por regime + `probeOffline`
O `assert(obj.S == 2000)` era incondicional e **abortava toda sonda offline**. Agora valida contra o
S **do regime** (online 2000 / offline 20000). `probeOffline` dispara 1 bloco por modelo treinado,
com `geracao` NULL, **sem armar** (não há hard-stop no e103 capaz de matar o bloco).

### 2.4 Docstring do `SondaState` corrigido — era uma armadilha real
O cabeçalho documentava `SondaState(sd, buf, bud, fid, alg)`; a assinatura real é
`(sd, buf, fid, alg, k)` — **sem `bud`** (invariante I2). Quem copiasse do cabeçalho passaria o
`FEBudget` na posição do `fid`, e o `.jsonl` morreria **em silêncio** (`fid > 2` é falso para um
objeto). Afetava os 7 configs restantes.

### 2.5 Duas regressões novas no config `stub`
- **DI-17.5 nos dois ramos**: último fit fora da cadência ⇒ dispara carimbando `g_armado`; dentro da
  cadência ⇒ no-op. *O teste antigo asseverava o comportamento BUGADO* (disparar com geração nunca
  armada) — foi reescrito.
- **DI-13.5**: bloco offline de 20.000 no **mesmo arquivo** das linhas de busca, conferindo os
  **dois lados** da coluna após o export. Cobre o e103 **sem pagar o run do e103**.
  *(O teste permanente foi para o `stub` porque a suíte de regressão do repo é `.py` — faixa
  proibida nesta sessão. Ver §5, item T-1.)*

---

## 3. Achados que NÃO estavam no cartão

### 3.1 🔴 A instrução do cartão sobre o `n_geracoes` do e103 estava errada — os dados provam
O cartão mandava derivar da camada ②. **Medido:** a ② offline só lista membros do dataset, e no
ZDT1 eles somem na g5 ⇒ **② dá 4 gerações** para um run que executa **99**.
Levado ao autor (D81) → **DI-17.3: ③ filtrando `regime != 'sonda'`**. Substitui a instrução do cartão.

### 3.2 🔴 `espaco_modelo="nativo"` está FORA do enum e passa CALADO
`src/export.py:67` fixa `ESPACOS = ("transformado","cru")` e **valida** em `:292`. O writer MATLAB
**não valida**, então gravava e seguia. Já estava em **c141 e c217, entregues e aceitos**.
Estouraria só na consolidação Python — **depois dos 16.500 runs da M8**.
→ **DI-17.8: padronizado em `"cru"` nos 21.** c141/c217 re-rodados, ① idênticas. (O `e7` já estava
correto e serviu de precedente.)

### 3.3 🔴 `n_acumulado` do b4 media o ARQUIVO, não o TREINO
Gravava `|Arc|`; o §17.6/CONTRATO:220 define "nº de pontos reais **no TREINO** naquele retreino".
O b4 treina em `TrainIn` (subamostra 3/4 **estratificada**). Corrigido para `size(TrainIn,1)`.
**É exatamente o mesmo erro do c217** (§5.3 do handoff anterior), que segue **pendente de
ratificação**. São os dois subamostradores — devem ser ratificados **em bloco**.
⚠ **Muda a ④ do b4 vs a baseline.**

### 3.4 🟡 Sessão CONCORRENTE no repo durante a execução
Entraram os commits `a9d906b`..`26a8c83` (DI-15/DI-16, cartões R3) enquanto este cartão rodava.
**Faixas verificadas disjuntas** — nenhum `.m` deste cartão foi tocado (eles mexeram em docs,
`export.py`, `envs.json`, `anchors.json`, bundles).
**Mas ocuparam a numeração DI-15.x**, que eu usava para as decisões do autor desta sessão.
→ **Renumeradas para DI-17.1…DI-17.8**, e as citações que já tinham entrado no código foram
corrigidas (senão o handoff apontaria para decisões alheias).

### 3.5 🟡 Assimetria cross-stack do `geracao` (consequência do §2.1)
A torre fez `geracao` = `pa.int32()` **nullable** no Python. O MATLAB **não expressa int32-NULL**,
então grava `double`+NaN. É a mesma dicotomia do `real_solution_id` — **mas a regra 2 do R4 nomeia
só o `real_solution_id`**, não a `geracao`. Ver §5, item T-2.

### 3.6 A revisão adversarial pegou 2 defeitos que os GATES NÃO pegariam
- **e74**: a guarda de disparo usava `isstruct` sobre um handle `SondaState` (que devolve `false`)
  ⇒ a sonda seria um **NO-OP SILENCIOSO**: zero linhas, zero evento, **e o gate passando** — porque
  o gate só prova que a busca não mudou, e ela de fato não mudaria. Corrigido.
- **e103**: chamava `probeOffline` antes de o método existir; o revisor "consertou" revertendo para
  `probe(1)` (`geracao=1`), **contradizendo o adendo da torre**. Restaurado para `probeOffline`/NULL
  depois que a infra passou a suportá-lo.

---

## 4. As 8 decisões do autor desta sessão (DI-17.x) — para a torre registrar

| # | decisão | efeito |
|---|---|---|
| **DI-17.1** | **e74: um `SondaState` POR CABEÇA**, com `k` próprio e fase deslocada | O `g` do hook do e74 bumpa **4× por ciclo** (`CLMEA.m:90/:100/:112/:135`); sob k=2, s1 e s3 disparavam todo ciclo e **o s2 — a RBF global — NUNCA dispararia**. |
| **DI-17.2** | `f_best`/`n_front1` = **arquivo real PÓS-ciclo** | Sem definição operacional, os configs divergiram (c141 pós, b1 pré ⇒ curvas defasadas de um infill). b1 realinhado; b3 usa `A2` (o `A1` é podado com teto NI). |
| **DI-17.3** | e103 `n_geracoes` = ③ com filtro `regime != 'sonda'` | **Substitui a instrução do cartão** (§3.1). |
| **DI-17.4** | `dist_min_arquivo` em espaço **NATIVO** nos 21 + doc-sync | A SPEC §S.7.1 diz "normalizado"; c141/c217 (aceitos) usam nativo; não é renormalizável post-hoc. |
| **DI-17.5** | `finalProbe` usa `g_armado` | §2.2. Não é bit-neutro ⇒ c217/c141 re-rodados. |
| **DI-17.6** | c238: sonda em espaço **CRU** | Régua constante entre gerações e comparável ao gabarito. *Responde a pendência de `handoff/R1-c238.md` §8 item 2(b), aberta desde a R1.* |
| **DI-17.7** | offline: `f_best` = pop corrente **+** min do dataset no header | Superconjunto; vale para os 5 offline. |
| **DI-17.8** | `espaco_modelo` = **`"cru"`** nos 21 | §3.2. |

---

## 5. 🔴 DEFINIÇÕES EM ABERTO — a torre DEVE levantar estas com o autor

### R-1 · Ratificação em bloco do `n_acumulado` (c217 **e** b4)
Os dois subamostradores gravavam o **arquivo** em vez do **treino**. O c217 já estava pendente de
ratificação (§5.3 do handoff anterior); o b4 tem agora o mesmo fix. **Ambos mudam a ④ vs a
baseline.** Precisam ser ratificados juntos — ratificar um só deixaria a curva de escalabilidade
inconsistente entre os dois.

### T-1 · O teste permanente do `geracao` NULL mora no lugar errado
O adendo da torre pediu "adicione um teste". A suíte de regressão do repo é `.py` (**faixa proibida
nesta sessão**), então o teste foi para o config `stub` (`.m`). Funciona e é versionado, mas
**a torre deve decidir** se quer também um teste em `tests/test_di13.py` do lado Python — hoje a
cobertura do writer MATLAB depende de alguém rodar o `stub`.

### T-2 · Regra 2 do R4 não cobre a coluna `geracao`
A regra diz "tolerar int32 E double+NaN" **nomeando só o `real_solution_id`**. Com a `geracao`
nullable, o MATLAB grava `double`+NaN e o Python grava `int32` nullable para a MESMA coluna.
**Um leitor a jusante que faça `astype(int32)` sem tratar NaN quebra no e103.** Doc-sync necessário.

### T-3 · Doc-sync da DI-17.4 na SPEC §S.7.1
O texto diz "espaço de decisão NORMALIZADO"; a decisão do autor foi **nativo**. Faixa SPEC.

### T-4 · Doc-sync da DI-13.5 no CONTRATO §3.1
A linha 171 ainda diz *"Como grava: **2000 linhas** na ③"* — desatualizada pelo próprio §3.1
(linhas 145-153, que já traz o S=20.000 do offline). **Contradição interna do CONTRATO.**

### T-5 · `accept.py` continua sem NENHUMA checagem de sonda
Pendência herdada (§6 do handoff anterior, DI-13 item B-5). O gate objetivo **não enxerga** as
606.000 linhas de sonda do b1/ZDT1, nem a invariante de ordem. Faixa `.py`.

### T-6 · `n_acumulado` é `nullable=False` no schema do `export.py`
Os pisos não têm treino ⇒ a coluna sai NULL. Hoje é **latente** (o gate R1 não checa schema);
**estoura na consolidação**. Mesma classe da DI-13.2. Faixa `.py`.

### T-7 · `dist_min_arquivo` e `modelo_hp` no regime OFFLINE
O "mínimo comum" da S.7.1 diz "os 21" sem exceção declarada, mas os dois campos **pressupõem infill
guiado por modelo** — não existem no offline. Afeta e103 + b5r/b5m/c311/piso-off da R3.

### T-8 · `tempo_fit_s`/`tempo_busca_s` por geração no e103
O e103 tem treino ÚNICO e mede a busca só no agregado. Preencher por geração muda a ④ de 1 para 99
linhas e exige patch no stock (⇒ re-lacre do `repos.lock`). **Decisão do autor.**

---

## 6. O que falta para fechar o cartão

1. **c238** — wiring (`EIM.m`, `c238_instrument.m`, `run_c238`) + 2 runs (MMF1, DTLZ2).
   ⚠ ZDT1 fica de fora: **3h55** documentado.
2. **e7** — wiring + 2 runs. ⚠ ZDT1 fora: **72 min**. `loss_treino` = **INACESSÍVEL** por decisão
   do autor (DI-12.1) — registrar a ausência.
3. **e74** — wiring dos **4 pontos de hook** (`CLMEA.m`, `ClassifierSelect.m`, `Hv_Select.m`,
   `Local_infill.m`) + os **3 `SondaState`** da DI-17.1 + 3 runs.
4. **e103** — wiring + `margem_3sigma` (patch em `IBEAMS.m:67` ⇒ **re-lacre por
   `scripts/preflight.py --write`**) + `n_geracoes` da DI-17.3 + 3 runs.
5. **Re-execução consolidada dos gates** (ver ressalva do §1.5).
6. **Regressão total**: F0×4 + 13 configs ×MMF1 + preflight + suíte completa.
7. **RELATÓRIO padrão** de execução.

**Estimativa:** ~3–5 h, dominadas por wall-clock de MATLAB.

---

## 7. Notas operacionais para quem continuar

- **RI-07 é real e mordeu várias vezes:** não editar `src/experiment.m` com MATLAB rodando. O
  fluxo que funcionou foi: batelar edições → rodar → validar → commitar.
- **`Bash` tem teto de 10 min.** Runs longos precisam de `nohup ... &` + detecção pelo **FOOTER**
  do arquivo de saída (como o cartão manda).
- **zsh não faz word-splitting** em `$var` — loops de validação devem usar Python ou arrays.
- **O `parquetwrite` do MATLAB converte NaN em NULL de verdade** (provado empiricamente antes de
  escrever qualquer código que dependesse disso). É o que faz o idioma do `n_acumulado`/`geracao`
  funcionar.
- **Os `<alg>_sonda.m` dos 4 restantes já existem e foram revisados adversarialmente** — cada um
  traz no cabeçalho a lista exata das linhas a inserir no stock e no instrument.
