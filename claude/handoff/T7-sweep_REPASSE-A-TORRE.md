# T7-sweep — REPASSE À TORRE: o que precisa do AUTOR

> Complemento de `handoff/T7-sweep.md` (detalhe técnico completo lá).
> Código commitado: **`9fcde9f`** (Python) + o patch MATLAB (ver §0).
> **Nada aqui foi decidido por mim** — são conflitos SPEC×artefato e paredes
> numéricas que o cartão não previa. Protocolo D81/D97.

---

## 0. Estado em uma linha
O **fio do T7 está implementado, testado e validado nos dois stacks** (Python +
MATLAB). O que impede o "verde total" do cartão **não é código**: são **4 decisões**
e um **conflito de roster** que a torre precisa levar ao autor.

---

## D-A · 🔴 B15.4: o "ramo big" do c311 — o cartão pede o OPOSTO da SPEC

**O cartão manda:** rotear `tier=='big'` → `_build_surrogates`, *"pulando o while de
construção"*.

**A SPEC não sustenta.** B15.4 descreve o **PISO** do tier big, não o c311:
- **D38** (SPEC:1628): *"**Pisos**: Kriging-média (small/medium), **tree-média (big)**"*.
- **§10 [P5/DI-16.5]** (SPEC:865): o piso offline vira **duas instâncias**; a do big é
  *"treed-GP-média … = **a ablação do c311**, o único que roda no big"* (em `env_c311`).
- **SPEC:1520/1779/1904**: as âncoras de escalabilidade **do próprio c311 no big**
  (*"build @50k treed 31,6 s"*, *"N=50k, D=2 → 2500 iterações máx"*) **só fazem sentido
  se o c311-big RODA a construção iterativa**.

**Consequência de obedecer ao cartão:** o **único config do tier big** viraria a **sua
própria ablação** — o `addGPs` iterativo *é* o mecanismo treed-GP. Erro invisível
(o run sai verde) e destruiria a análise do big.

**O que fiz:** laço **INTOCADO**; nota completa no docstring de `_build_surrogates`.
**Bloqueia:** os 2 tokens `sweep-big-*` (10 das 90 células).

> **Pergunta ao autor:** B15.4 é (a) o **piso** do tier big — uma **instância nova** do
> `moead_media` em `env_c311` (leitura da SPEC), ou (b) o **comportamento do c311** no
> big (leitura do cartão)? Se (a), falta implementar esse piso — e o roster do sweep
> muda (ver D-D).

---

## D-B · 🔴 MVNS gera duplicata em D=2 ⇒ 3 tokens morrem no MMF1

A **D67** manda *"clip aos bounds"*. Com μ=0,3 e σ=√0,1≈0,316, P(uma coordenada cair
**exatamente** em 0,0 ou 1,0) ≈ **18,4 %**; uma duplicata bit-a-bit exige as **D**
coordenadas no clip ⇒ P ≈ 0,1845^D. **Medido (semente 42):**

| problema | D | small-mvns | medium-mvns | big-mvns |
|---|---|---|---|---|
| **MMF1** | **2** | **2**/61 | **76**/2000 | **1757**/50000 |
| ZDT4 | 10 | 0/309 | 0/2000 | 0/50000 |
| DTLZ2 | 12 | 0/371 | 0/2000 | 0/50000 |
| WFG9 | 22 | 0/681 | 0/2000 | 0/50000 |
| ZDT1 | 30 | 0/929 | 0/2000 | 0/50000 |

Qualquer duplicata ⇒ `RuntimeError … hazard L.15 … Pára-e-loga (D81)`
(`standalone_harness.py:608`) **e** o assert gêmeo fatal no MATLAB (`experiment.m`).

**O eixo mvns está PROVADO** (smoke verde em ZDT4). **Só o MMF1 quebra.**
**Bloqueia:** 9 das 90 células (270 de 2700 no grid).

> **Pergunta:** (a) MMF1 sai dos tokens mvns (documentado como impossibilidade
> numérica, como já se fez com "e103/b5 não rodam no big"), (b) a D67 ganha um
> tratamento (re-amostrar duplicatas? truncated normal em vez de clip?) — **mudança de
> protocolo**, ou (c) o guard L.15 é relaxado no offline mvns — **não recomendo**: o
> guard existe porque duplicata quebra o ajuste do surrogate.

---

## D-C · 🔴 O GP não treina em `medium × D=2` (parede numérica)

`sweep-medium-lhs/b5m/MMF1/42` estoura
`LinAlgError: kernel … is not returning a positive definite matrix`.
**Causa: densidade.** Em D=2 com n=2000 o espaçamento típico é **n^(−1/D)=0,022** — uma
ordem de grandeza mais denso que qualquer outra célula ⇒ K numericamente singular.

O bundle afirma *"Medium ≈2000 (**GP padrão ainda treina**)"* — **falso para D=2**.
**✅ Confirmado restrito ao MMF1:** o mesmo run em **ZDT4 (D=10) fechou** (fe=2000,
cp_init_ok, 801 gerações). Atinge b5r/b5m e o piso Kriging.

**⇒ O MMF1 é o problema-filho do sweep nos DOIS eixos (D-B e D-C), pela mesma causa
de fundo: D=2.** Vale considerar uma decisão única para os dois.

> **Pergunta:** MMF1 sai do tier medium/big (fica só no small, onde é o controle), ou
> o `SurrogateKriging` ganha jitter/`alpha` maior — o que é **mudança de fidelidade**
> do b5 e contamina a comparação com os runs `off` já validados?

---

## D-D · ⚠ CONFLITO SPEC × runs_matrix: o piso está no sweep ou não?

- **SPEC §10 (:865) e D38 (:1628)** dizem que o piso offline roda no sweep, **nos 3
  tiers**, em 2 envs.
- **`runs_matrix.csv` não tem NENHUMA linha `moead_media` com `exp=sweep-*`**; o bundle
  D67 lista só 4 configs; o RUNBOOK conta 90 células — que **batem sem o piso**.

Pela precedência **D83 (Anexo D > corpo > bundles)**, a SPEC vence e **faltariam
células** no grid. Deixei o fio do `piso_offline` **pronto e inerte** (sem célula, o
caminho não é exercitado).

> **Pergunta:** o artefato está desatualizado (⇒ regerar `runs_matrix` com o piso, e a
> rodada-42 cresce) ou a SPEC §10/D38 está superada (⇒ doc-sync)? Liga-se ao **D-A**.

---

## D-E · ℹ️ Dois achados que NÃO precisam de decisão, mas a torre deve saber

**E1 · 🔴 Bug de lançamento corrigido (mesma classe do M9 da DI-31).**
`experiment.run` repassava `**kwargs` cru a `run_in_venv` (que é **transporte**); como
`experiments.py` **sempre** passa `enable_bucket`, **todo run dos 4 configs venv-only
(b5r/b5m/moead_media/c311) despachado pela bateria estourava `TypeError`**, engolido pelo
`except` genérico como 3 retries + `failed`. **A bateria offline M9 era irrodável** —
exatamente o gêmeo do bug que a DI-31 achou no roster. Corrigido por camada
(drift-proof) + 5 testes-guarda.

**E2 · Lacuna D23/D60 fechada.** `b5_prob` e `piso_offline` tinham `try/finally` **sem
`except`**: exceção ⇒ run **sem manifesto**. E um run sem manifesto **some da
`portao --varredura`** (que enumera de disco) — o total cai e **nada fica vermelho**.
Novo `H.write_failed_manifest` + re-`raise` (retry D23 intocado).

---

## D-F · Insumos para as decisões A3/A5 (custo) que a torre já pode usar

| medição | valor |
|---|---|
| `small` (b5r, D=2 e D=10) | **142 s** e **148 s** por run |
| `medium` (b5m, ZDT4 D=10, n=2000) | **2.480 s (41,3 min)** — **~17×** o small |
| `medium` × 32 células viáveis da rodada-42 | **≈ 22 h-core** |
| e103 `small` (MATLAB, MMF1) | **12,2 s** |

⚠ **O b5 não tem `teto_s` nenhum** ⇒ sem aborto limpo se uma célula degenerar. O `c311`
tem, mas **o despachante nunca o passa** (`experiments.py:129`) ⇒ o `_TetoWall` está
**inalcançável na bateria**. Recomendo tratar junto de A3/A5.

---

## D-G · Provisionamento: os datasets do sweep NÃO existiam

`doe.materialize_all` só faz o **principal**; o CLI não expõe `--tier/--dist`. Havia **5
arquivos-piloto (semente 0)**; para a **semente 42, zero**. Gerei apenas o necessário aos
smokes (não commitados — são dados). **Faltam ~441** para o grid completo.

```bash
python -c "from src import doe; [doe.ensure_dataset(p,42,tier=t,dist=d) for p in ['MMF1','ZDT4','DTLZ2','WFG9','ZDT1'] for t in ['small','medium','big'] for d in ['lhs','mvns']]"
```

---

## Resumo para o autor (4 perguntas)
1. **B15.4**: o "piso big" é uma instância nova do piso (SPEC) ou o comportamento do
   c311 no big (cartão)? — destrava 10 células
2. **MMF1 × mvns**: sai do roster, muda a D67, ou relaxa o guard? — destrava 9 células
3. **MMF1 × medium/big**: sai do roster ou mexe no GP? — destrava 8 células
4. **Piso no sweep**: SPEC ou runs_matrix? — pode **aumentar** o grid
