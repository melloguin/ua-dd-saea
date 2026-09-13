# RELATÓRIO DE EXECUÇÃO — cartão F0-04-metrica (narrativa completa p/ a torre de controle)

> **Propósito.** Repasse detalhado, passo a passo, de TUDO o que esta sessão fez ao executar o
> cartão **F0-04-metrica** — o 4º e último da Fase 0. Escrito para a instância que gerou as
> instruções entender exatamente o quê, como e com que resultado. O handoff de continuidade
> (curto, p/ a próxima sessão) é o irmão `handoff/F0-04-metrica.md`; ESTE é a narrativa longa.
>
> **Veredito:** ✅ **VERDE, exit 0.** Âncora D92 batida (`HV(BBOB_F1)=1,04333`). **Fase 0 FECHADA**
> (F0-01·02·03·04 ✅). **Nenhum pára-e-loga (D81) disparado; nenhuma ambiguidade exigiu parar.**
> **Nada instalado (D80/D81); zero código de algoritmo; zero julgamento de fidelidade (D97).**

- **Data:** 2026-07-16 · **Branch:** `experiment/definitive_algorythms`
- **Env:** env-main por caminho completo (`/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python`) — numpy 2.4.6 · pandas 2.3.3 · pyarrow 25.0.0 · pymoo 0.6.2 · scipy 1.17.1
- **Gate:** `PY scripts/accept.py F0-04-metrica` → **exit 0**

---

## 0. O contrato desta sessão (o que era pedido)

Esqueleto ("casca") da **camada de métrica pós-hoc** + o **smoke da âncora** que fecha a Fase 0.
Ainda infraestrutura: **SEM algoritmo, SEM fidelidade** (D97). Especificamente: um módulo que
(a) LÊ a camada ① (avaliações reais do export do F0-03), (b) NORMALIZA os objetivos por
`f_min/f_max` do problema (S.5), (c) calcula **IGD, IGD+ (primária — D70), HV, GD, spacing** +
a **trajetória** ao longo das avaliações; e (d) o **smoke** `HV(BBOB_F1, ref=1,1/coord,
normalizado) = 1,0433` (D92). A análise COMPLETA é do R4, refinada/implementada pelo AUTOR (D100).

Regras de operação vinculantes que segui: precedência D83; pára-e-loga D81 (parar em
ambiguidade/definição ausente); não instalar pins (D80); não inventar definição; não julgar
fidelidade (D97); 1 sessão = 1 cartão; ao fechar, escrever o handoff.

---

## 1. PASSO 0 — Verificação de ambiente (feito ANTES de tudo)

Comando (o exigido pelo prompt, por caminho completo):
```
PY -c "import numpy,pandas,pyarrow,pymoo; print('ok')"   →  ok
```
Verde ⇒ prossegui. (Se falhasse, o protocolo era PARAR e avisar — D81 — e **não** instalar nada.)

---

## 2. PASSO 0 — Leitura de contexto (na ordem exigida) e os fatos-chave

Li **somente** o que o prompt mandou, nesta ordem, e extraí os fatos que governam o cartão:

1. **`HANDOFF_MESTRE.md` (§10 estado, §11 armadilhas)** — Fase 0 em andamento (F0-01/02/03 ✅);
   §11 são armadilhas de cartões MATLAB futuros (b1 `sqrt(mse)`, âncoras com prefixo de dir) —
   não tocam o F0-04. §3/§4 reafirmam: **IGD+ primário; ref-point do HV = 1,1 por coordenada no
   espaço normalizado**.
2. **`handoff/F0-03-export.md`** — o que herdei do F0-03: `src/export.py` (schemas das 4
   camadas; a ① tem colunas `f0..f{M-1}` **0-based**, float32), `src/naming.py` (caminhos;
   `layer_path(exp,alg,prob,sem,"real")`), `src/budget.py` (`RealEval(solution_id,x,f,fe_index,
   fase)`). Contrato explícito: "a métrica lê o `f` gravado na ①". **Reusei todos.**
3. **`claude_code_context/CLAUDE.md`** (íntegro) — precedência D83, pára-e-loga D81, invariantes
   (ref HV normalizado 1,1; **IGD+ primário D70**; a métrica lê a ①).
4. **`cards/INDEX.md`** — a linha F0-04: "Esqueleto da camada de métrica + smoke F1 = **1,0433**
   (D92)", bundle `00_fundacao/04, 50_analise_R4`.
5. **Os 5 de `00_fundacao/`**, com foco em:
   - **`04_plano_F0_piloto_gates.md`** — §22.1 lista o item "**Esqueleto da camada de métrica**
     (§12, pós-hoc — casca apenas)" e o "*smoke-test* da métrica com o F1 analítico (D92: HV
     oficial com ref = 1,1 por coordenada → **1,0433**; 0,8333 = sanity do front com ref no
     nadir (1,0), rotulado — L.19)". Este é o teste de aceitação do cartão.
   - **`05_problemas.md` (S.5)** — a tabela `f_min/f_max` CRUS por problema: **BBOB F1 = ideal
     [0,0], nadir [82,042; 82,042]**. Nota crítica: "f_max = nadir do front (CRU); a **margem de
     10% aplica-se no harness**" e "os BBOB vêm do front **EMPÍRICO** do cache, exceto F1
     (analítico)". Também L.19: F1 analítico é o teste de fumaça (HV normalizado 0,8333 sanity).
6. **`50_analise_R4/metricas_estatistica_caracteristicas.md` (§12–§15)** — **D69** (métricas
   sobre `f′=(f−ideal)/(nadir−ideal)`; ref HV = 1,1 por coordenada normalizado; supersede
   "nadir×1,1" que quebrava com nadir≤0 nos BBOB), **D70** (IGD+ final = endpoint primário),
   **D92** (âncora re-derivada: `∫(1−√x)²dx=1/6` ⇒ HV(ref 1,1)=1,0433; 0,8333 = ref no nadir =
   sanity do front), **§12.1** (BBOB IGD relativo ao ref empírico → apoiar no HV), **§12.2** (HV
   pode ZERAR sob orçamento apertado → é dado, não NaN; reference set |R|≈5000; 2-obj re-espaça
   por arco, 3-obj Das-Dennis/Riesz), **§13** (trajetória mediana+IQR), **D100** (esta camada é
   pós-experimento — o autor refina no R4).

Também li o **código** que iria consumir/estender: `src/export.py`, `src/naming.py`,
`src/problems.py` (o `true_pareto_front` de cada problema; a classe `BBOB_F1_Sphere_Sphere` tem
front **analítico** = segmento entre os dois ótimos de esfera), `scripts/accept.py` (onde entra
o branch do cartão), `src/experiment.py` (`PROBLEM_CLASSES`/`_instantiate_problem` — mapa short
name→classe, ex.: `BBOB_F1`→`BBOB_F1_Sphere_Sphere`), `src/processing.py` (legado de ruído —
**não** reaproveitável), e o cabeçalho de `tests/test_export_budget.py` (convenção de skip sem
pymoo/pyarrow).

**Não li** (por disciplina de contexto): a SPEC íntegra (só grep pontual do 1,0433/0,8333/
tolerância), nem bundles de rodadas/algoritmos.

---

## 3. Derivação analítica da âncora (a "prova antes de codar")

Antes de escrever qualquer código, provei o número no papel e depois numericamente.

**A matemática.** O front do BBOB_F1 é o segmento `X = a + t·(b−a)`, `t∈[0,1]`, entre os dois
ótimos de esfera `a,b`. Como `f_α=‖x−a‖²` e `f_β=‖x−b‖²`:
`f_α = t²·L²`, `f_β = (1−t)²·L²`, com `L²=‖b−a‖²`. Logo **ideal=[0,0]**, **nadir=[L²,L²]**.
Normalizando por `(ideal,nadir)`: `f′_α=t²`, `f′_β=(1−t)²` ⇒ front normalizado
**`f′_β=(1−√f′_α)²`**, independente de `L` (por isso a âncora é robusta ao instance).

HV com ref `(1,1;1,1)`:
```
HV = 1,1·1,1 − ∫₀¹ (1−√y)² dy = 1,21 − (1 − 4/3 + 1/2) = 1,21 − 1/6 = 1,04333…  →  1,0433  ✓ (D92)
```
Sanity com ref no nadir `(1,0;1,0)`: `1 − 1/6 = 0,8333…` ✓ (é a geometria do front, NÃO o gate).

**A verificação numérica prévia** (rodada num script descartável, ANTES de implementar), para
confirmar a lib e a convergência do HV discreto ao analítico:

| n (densidade do front) | HV(ref 1,1) | |Δ| a 1,0433 |
|---|---|---|
| 500    | 1,042664 | 6,4e-4 |
| 1 000  | 1,042999 | 3,0e-4 |
| 5 000  | 1,043267 | 3,3e-5 |
| 10 000 | 1,043300 | 1,1e-7 |
| 50 000 | 1,043327 | 2,7e-5 |
| 200 000| 1,043332 | 1,2e-6 |

Confirmações: `nadir` do front vivo = **82,04197** (bate com S.5 82,042 a 4 casas); pymoo tem
`HV/IGD/IGDPlus/GD`; `IGD(front,front)=IGD+(front,front)=GD(front,front)=0`. **Conclusão:** com
`n≥5000` o HV discreto arredonda a 1,0433; escolhi **n=50000** para o smoke (7 ms, 1,043327).

---

## 4. Decisões de projeto que tomei (e o porquê) — nenhuma exigiu pára-e-loga

Todas dentro do que a SPEC fixa; onde havia latitude de engenharia, escolhi o mais fiel/robusto
e documentei no código. **Nenhuma ambiguidade genuína** (definição ausente/conflito) apareceu —
por isso não parei (D81).

1. **Base de normalização = tabela S.5 congelada** (`F_MIN_MAX`, 25 problemas), exatamente como
   o prompt pediu ("normaliza por f_min/f_max — S.5"). É `(ideal, nadir CRU)`. Coincide com o
   `true_pareto_front` vivo (D69 diz "ideal/nadir do front verdadeiro"; S.5 = min/max do front),
   e é FIXA por problema/idêntica p/ todos (exigência do §12). O check (6) do gate cruza a S.5
   com o front vivo do F1 para pegar tabela stale.
2. **A margem de 10% NÃO entra no denominador.** Normalizo por `nadir CRU`; a folga de Ishibuchi
   entra pelo **ref=1,1**. É o que reproduz 1,0433 (se eu embutisse a margem no denominador, o
   ref teria de ser 1,0 e daria 0,8333 — o erro que o D92 alerta). Deixei isso explícito no
   docstring e distingui do `f_max_uso` (nadir+10%) que o **c122** usa na normalização INTERNA
   dele (S.5/R3) — isso é do algoritmo, não da métrica.
3. **Tolerância da âncora = 5e-4** (`_TOL_HV_ANCHOR`). O HV denso dá 1,043327 (|Δ|=2,7e-5),
   folga ~18×. 5e-4 separa com sobra do ref errado (1,0→0,8333, Δ≈0,21) e do não-normalizado
   (ordens de grandeza), sem exigir densidade excessiva. O prompt não fixou número; escolhi um
   defensável e o documentei.
4. **Densidade do smoke = n=50000.** Ver tabela do §3. Rápido e estável.
5. **Métricas via pymoo 0.6.2 (pinado, D80).** IGD/IGD+/HV/GD são exatos no pymoo (HV por
   box-decomposition). **Nada instalado** — pymoo já está no env-main. `spacing` (que o pymoo
   não tem) implementei em numpy: **Schott (1995), distância L1** sobre objetivos normalizados,
   documentado; se o R4 preferir outra convenção é 1 função.
6. **Reference set = subamostra uniforme do front normalizado** (`|R|≈5000`). O **re-espaçamento
   FINO** (arc-length 2-obj / Das-Dennis·Riesz 3-obj, §12.2) é refinamento do R4 (D100) —
   marquei no docstring. A subamostra entrega um ref set válido e reprodutível p/ o encanamento.
7. **HV de conjunto vazio = 0,0** (HV degenerado é DADO, não NaN — §12.2). **IGD de vazio = NaN**
   (sem aproximação, a distância inversa é indefinida). Documentado.
8. **`import src.metrics` só exige numpy** (pymoo/pyarrow LAZY, como `export.py`) — provei que
   importa no `python3` base. Mantém o padrão do repo (o runner de aceitação e o despachante
   rodam em interpretador magro).
9. **Escopo = esqueleto (D100).** Implementei as funções-núcleo + a âncora; deixei explicitamente
   para o R4: agregação das 30 sementes (mediana+IQR §13), os 4 testes §14, online×offline
   separados, análise por característica §15/matriz D98, IGDX D99, attainment/GHV, re-espaçamento
   fino, nuance BBOB empírico. Isso está listado no handoff e nos docstrings.

---

## 5. Implementação — arquivo por arquivo

### 5.1 NOVO `src/metrics.py` (o esqueleto)
Módulo único, agnóstico a stack, pós-hoc. Conteúdo:
- **Constantes de decisão:** `PRIMARY_METRIC="igd_plus"` (D70), `HV_REF_COORD=1.1` (D69),
  `HV_SMOKE_BBOB_F1=1.0433` / `HV_SANITY_BBOB_F1=0.8333` (D92), `REF_SET_SIZE=5000`, guarda de
  range `1e-12`.
- **`F_MIN_MAX`** — a tabela S.5 congelada `(ideal, nadir)` p/ os 25 problemas (chaves =
  `experiment.ALL_PROBLEMS`). Transcrita a 4 casas da S.5.
- **`reference_bounds(problema)`** → `(ideal, nadir)` da S.5 (KeyError se desconhecido).
- **`normalize(F, ideal, nadir)`** = `(F−ideal)/max(nadir−ideal, 1e-12)` (D69).
- **`nondominated_front(F)`** — reusa `problems._nds_filter` (ENS do pymoo moderno; mesmo A2).
- **Métricas (sobre objetivos JÁ normalizados):** `igd`, **`igd_plus`** (primária), `gd`, `hv`
  (`ref_point=[ref_coord]*M`), `spacing` (Schott L1, loop numpy — N≤31D−1≤929, barato, sem NxN).
- **`true_front_raw(problema, n)`** — instancia via `experiment._instantiate_problem` e chama
  `true_pareto_front(n)` (analítico p/ a maioria; cache empírico p/ BBOB≠F1).
- **`reference_set(problema, size)`** — front normalizado → ND → subamostra uniforme.
- **`load_real(exp,alg,problema,semente,data_root)`** — lê a ① (`__real.parquet`) via
  `naming.layer_path` + pyarrow; devolve `{F(n,M) float64, fe_index, fase, M}` (detecta M pelas
  colunas `f0..`).
- **`metrics_of_set(F_raw, problema, ref_norm=)`** — normaliza + ND + as 5 métricas → dict.
- **`trajectory(F_raw, fe_index, problema, n_checkpoints=20, ref_norm=)`** — em cada checkpoint
  de FE, mede o não-dominado ACUMULADO (§13); reusa o ref set 1×.
- **`metrics_from_real(...)`** — ponta-a-ponta: lê a ① do run → métricas FINAIS + trajetória.
- **`hv_smoke_bbob_f1(n=50000)`** = 1,0433 (âncora D92) e **`hv_front_sanity_bbob_f1()`** =
  0,8333 (sanity rotulado).

### 5.2 MODIF `scripts/accept.py` (o gate)
Novo `check_f0_04()` + branch no `main()` para `F0-04*`. **Não tocou a política D97** (só
encanamento). Os 5 checks (ver §6). Constante `_TOL_HV_ANCHOR=5e-4`. Helper `_f0_04_stub_real`
que escreve uma ① STUB com objetivos REAIS (via `export.write_real` + `budget.RealEval`) para
provar a leitura ponta-a-ponta — não é um run FE-exato (isso é o F0-03; a métrica opera sobre
QUALQUER ①).

### 5.3 NOVO `tests/test_metrics.py`
18 testes, com o padrão de skip do repo (sem pymoo/pyarrow → pulam).

### 5.4 MODIF `cards/INDEX.md`
F0-04-metrica → ✅.

---

## 6. Aceitação — o gate `check_f0_04`, saída literal

`PY scripts/accept.py F0-04-metrica` (exit 0):
```
  [OK  ] SMOKE D92: HV(BBOB_F1, ref=1,1/coord, normalizado) = 1,0433: HV=1.04333 (|Δ|=2.7e-05 < tol 5e-04)
  [OK  ] sanity do FRONT (0,8333 = ref no nadir 1,0 — NÃO é o gate; D92): HV_sanity=0.83333 (|Δ|=2.7e-05)
  [OK  ] 5 métricas rodam · front×front→IGD/IGD+/GD=0 · HV=âncora · spacing sã: IGD=0.0e+00 IGD+=0.0e+00 GD=0.0e+00 HV=1.0432 spacing(unif)=9.1e-17 spacing(irreg)=0.166
  [OK  ] lê a ① ponta-a-ponta: normaliza → métricas + trajetória: final IGD+=0.0115 HV=0.8424 n_nd=41 · trajetória 5 pts (IGD+ 3.934→0.011)
  [OK  ] normalização D69 = tabela S.5 (25 problemas; F1 nadir = front vivo): |F_MIN_MAX|=25, F1 nadir S.5=[82.042, 82.042] ~ front [82.042, 82.042]
  >>> VERDE (encanamento objetivo) — FECHA a Fase 0
```

Os 5 checks, em prosa:
1. **Âncora decisiva (D92)** — HV(BBOB_F1, normalizado por S.5, ref 1,1/coord) = **1,04333**
   (|Δ|=2,7e-5 < 5e-4). É o que FECHA a Fase 0.
2. **Sanity do front (0,8333)** — o mesmo front, ref no nadir (1,0) = **0,83333**. **Rotulado
   como sanity, NÃO como gate** (o prompt alertou para não confundir).
3. **As 5 métricas rodam e são sãs** — front×front ⇒ IGD/IGD+/GD = 0 exatos; HV(front) = âncora;
   `spacing` = 9e-17 no front uniforme (é matematicamente ~0: no front `t²,(1−t)²` a distância L1
   entre vizinhos é constante 2·Δt) e 0,166 num conjunto de gaps irregulares (>0).
4. **Lê a ① ponta-a-ponta** — stub ① (objetivos reais de MMF1, dominados primeiro) → normaliza →
   métricas FINAIS + **trajetória** que converge (IGD+ 3,93→0,011).
5. **Coerência S.5×front** — a `F_MIN_MAX` cobre os 25 problemas e o nadir do F1 bate com o front
   vivo (pega tabela stale).

---

## 7. Testes e regressões

- **`tests/test_metrics.py`:** **18/18 OK.** Cobrem: tabela cobre 25 e bate com `ALL_PROBLEMS`;
  `reference_bounds` conhecido/desconhecido; `normalize` mapeia ideal→0/nadir→1 + guarda de
  range (sem div/0); **âncora 1,0433** e **sanity 0,8333**; front×front=0; HV(front)=âncora;
  HV vazio=0 / IGD vazio=NaN; **IGD+≤IGD**; spacing uniforme(~0)×irregular(>0)×degenerado(=0);
  `reference_set` (tamanho ≤ size, normalizado); **leitura da ①** (`load_real` shape,
  `metrics_from_real` completo, trajetória convergente).
- **Suíte inteira:** `PY -m unittest discover -s tests -t .` → **62 testes OK** (44 anteriores
  de F0-01/02/03 + 18 novos). (Aparece um `ResourceWarning` de tracemalloc na saída — é ruído
  não-fatal pré-existente da suíte; a suíte reporta OK.)
- **Regressões (nada quebrou — mexi num arquivo compartilhado, o `accept.py`):**
  `accept.py F0-01` exit 0 · `accept.py F0-02` exit 0 · `accept.py F0-03` exit 0 ·
  `preflight.py` exit 0.
- **Import-gate no `python3` base:** `import src.metrics` funciona só com numpy (pymoo/pyarrow
  lazy) — `F_MIN_MAX` tem 25 problemas.

---

## 8. Git — o que foi commitado (e o que foi deliberadamente NÃO tocado)

Branch `experiment/definitive_algorythms`. **3 commits pequenos**, prefixo `[F0-04-metrica]`,
cada um citando a decisão, **só meus arquivos**:
```
68f8230  [F0-04-metrica] src/metrics.py: esqueleto da camada de métrica pós-hoc
34a7213  [F0-04-metrica] accept.py: gate do cartão (smoke HV=1,0433, D92) + INDEX ✅
ca2b783  [F0-04-metrica] handoff: F0-04 fechado — FECHA a Fase 0
```
(Este relatório entra num 4º commit `[F0-04-metrica]`.)

**⚠ Concorrência.** No `git status` havia `ORQUESTRACAO_MESTRE.md` **modificado por OUTRA
sessão** (não por mim). **NÃO o toquei nem o commitei** — igual à convivência que o F0-03 já
havia registrado. Só stageei explicitamente os meus 5 arquivos (`src/metrics.py`,
`tests/test_metrics.py`, `scripts/accept.py`, `cards/INDEX.md`, os 2 handoffs).

---

## 9. Fronteira esqueleto × R4 (o que NÃO foi feito, por decisão — D100)

**Feito (encanamento, F0-04):** normalização D69 · as 5 métricas · reference set · leitura da ①
· trajetória (§13) · a âncora D92. **Herdado pelo R4 (camada de análise, o AUTOR refina/implementa):**
agregação das 30 sementes (mediana+IQR, §13) · os 4 testes estatísticos (§14: Wilcoxon rank-sum;
Friedman+Nemenyi+Demšar+Holm **por métrica**; signed-rank pareado; bayesiano de sinais-postos
rope=0,05) · **online (17) × offline (5) SEPARADOS** (D70) · análise por característica (matriz
25×8, §15/D71 — matriz re-derivada e congelada pelo autor, D98) · **IGDX** p/ os 4 MMF (D99) ·
**attainment worst-case** 2-obj + GHV opcional (§13) · **re-espaçamento fino** do reference set
(arc-length 2-obj / Das-Dennis·Riesz 3-obj) · a nuance **BBOB empírico** (IGD relativo, apoiar
no HV — §12.1).

**O que o R1/c217 (piloto) herda desta camada:** a API (`metrics_from_real`, `metrics_of_set`,
`reference_bounds`, `normalize`, as 5 métricas), a convenção de normalização (S.5, ref 1,1),
IGD+ como primária, e a âncora reproduzível (mesma que o cartão R4 deve bater).

---

## 10. Riscos, caveats e notas para a torre (o que vigiar)

1. **`F_MIN_MAX` é a S.5 congelada** (BBOB do cache i1). Se o autor **regenerar o cache do
   BBOB** (D98-adjacente), a tabela precisa ser **re-derivada** (script: instanciar a classe,
   `true_pareto_front(1000)`, min/max por coluna). O check (6) do gate cruza S.5×front do F1 e
   **falharia** se ficarem inconsistentes — é a rede de segurança.
2. **HV pode ZERAR** sob `31D−1` nos 3-obj difíceis (DTLZ1/3) — por projeto (§12.2) `hv` devolve
   0,0 (dado, não NaN); a leitura apoia-se no IGD+. O R4 deve sinalizar as células com HV=0.
3. **BBOB (exceto F1) tem front EMPÍRICO** (cache NSGA-II) → IGD/IGD+/GD são **relativos** ao ref
   empírico (§12.1). O esqueleto calcula; a **interpretação** (apoiar no HV) é do R4.
4. **`spacing` = Schott L1** — escolha documentada; trocável em 1 função se o R4 quiser L2/outra.
5. **`reference_set` = subamostra uniforme** (não o re-espaçamento fino do §12.2) — é esqueleto;
   o R4 troca pelo arc-length/Das-Dennis.
6. **Tolerância do smoke = 5e-4** — escolha minha (o cartão só dava "= 1,0433"). Folga real ~18×.
   Se a torre preferir outro número, é a constante `_TOL_HV_ANCHOR` em `accept.py`.
7. **`ResourceWarning` (tracemalloc)** na saída da suíte — ruído pré-existente, não-fatal; a
   suíte reporta OK. Não introduzido por esta sessão (meus testes usam `TemporaryDirectory` como
   context manager e fecham handles).

---

## 11. Ambiguidades encontradas e como resolvi (nenhuma exigiu D81)

- **"Normaliza por S.5" vs "D69 = front verdadeiro"** — não é conflito: S.5 = min/max do
  `true_pareto_front` (a própria S.5 declara isso). Usei S.5 congelada como base (fixa/idêntica
  p/ todos, §12) e ADICIONEI um check que a cruza com o front vivo. Sem parar.
- **"f_max com margem de 10%?"** — a S.5 é explícita: a tabela é o nadir CRU; a margem "aplica-se
  no harness" via ref=1,1. Normalizei pelo CRU. Sem parar.
- **Densidade/tolerância do smoke não fixadas** — resolvi por engenharia (verificação numérica
  prévia + folga), documentei. Sem parar.
- **Re-espaçamento do reference set / testes estatísticos** — explicitamente do R4 (D100), não do
  esqueleto. Deixei stubs/subamostra + marquei no docstring. Sem parar.

Nenhuma definição estava genuinamente **ausente** e nenhum **conflito** de precedência apareceu —
por isso segui direto (o prompt autorizava seguir sem OK, com a exceção de parar só em
ambiguidade real).

---

## 12. Estado da Fase 0 e próximos passos

**F0-01 ✅ · F0-02 ✅ · F0-03 ✅ · F0-04 ✅ → Fase 0 FECHADA.** O harness compartilhado está
provado ponta a ponta: despachante/manifesto/logger (F0-01) · DoE/dataset/seeds (F0-02) ·
wrapper de FE + export 4 camadas + gcs (F0-03) · **camada de métrica + âncora (F0-04)**.

**Próximo na escada (D84):** **R1-00-harness** (infra transversal MATLAB) ∥ **R2-00-harness**
(BoTorch/VM). Corte herdado a fechar em R1-00: o **CP-init 100% cross-linguagem** (o `doe_hash`
lido da ① que o adapter MATLAB injeta) — o gancho objetivo já existe (`accept.py --alg` →
`check_doe_hash`).

---

## 13. Como reproduzir tudo (comandos)

```
PY=/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python
$PY -c "import numpy,pandas,pyarrow,pymoo; print('ok')"     # ambiente
$PY scripts/accept.py F0-04-metrica                          # o gate (exit 0)
$PY -m unittest tests.test_metrics -v                        # 18 testes da métrica
$PY -m unittest discover -s tests -t .                       # suíte inteira (62 OK)
$PY scripts/accept.py F0-01-harness ; $PY scripts/accept.py F0-02-doe
$PY scripts/accept.py F0-03-export  ; $PY scripts/preflight.py   # regressões (todos exit 0)
```

*Fim do relatório de execução do F0-04-metrica. Fase 0 fechada.*
