# HANDOFF DOS SMOKES T11 — para o AGENTE VALIDADOR DE FIDELIDADE

**Gerado em 2026-07-30/31.** Este documento descreve **exatamente** o que existe
nesta pasta, como cada artefato foi produzido, o que ele permite concluir e —
principalmente — **o que ele NÃO permite**.

> 🚨 **Leia o §5 antes de tirar qualquer conclusão.** Um smoke é verificação de
> ENCANAMENTO. Ele não diz nada sobre correção numérica nem sobre fidelidade ao
> artigo — e é justamente isso que você foi chamado para julgar.

---

## 1. O que tem aqui — 24 configs, 27 células, 72 MB

```
evidencia_T11/
├── HANDOFF-SMOKES.md   ← este arquivo
├── LEIA-ME.md          ← resumo curto
├── smoke_python/       ← 11 configs Python  (11 células)
├── smoke_matlab/       ← 13 configs MATLAB  (15 células — e74 tem 3)
├── g6_com/ · g6_sem/   ← os pares §3.1: a MESMA célula com e sem sonda (9+9)
└── teto_c154/          ← a célula que validou o rito de teto
```

Cada célula tem o **contrato de 7 camadas** (o que existir para aquele config):

| camada | arquivo | o que é |
|---|---|---|
| ① | `*__real.parquet` | **toda avaliação real** da função-objetivo |
| ② | `*__pop.parquet` | a população selecionada por geração |
| ③ | `*__surrogate.parquet` | **toda predição do modelo** — busca **+ SONDA** |
| ④ | `*__timing.parquet` | tempos por geração (fit, busca, sonda) |
| ⑤ | `*.manifest.json` | a **certidão** do run: `params`, `sigma_dict`, hashes, `campanha_id` |
| ⑥ | `*.jsonl` | o **filme das decisões** — 1 evento por geração |
| ⑦ | `*__final.parquet` | só nos 5 offline: o endpoint oficial do regime |

## 2. Inventário medido — célula por célula

### Python (`smoke_python/experiments/`)

| config | exp | problema | FE | ① | ② | ③ | ④ | ⑦ | ⑥ |
|---|---|---|---|---|---|---|---|---|---|
| `sobol_batch` | batch | ZDT4 | 309 | 309 | 42.009 | **0** | 200 | — | 210 |
| `c122` | main | MMF1 | 61 | 61 | 451 | 58.132 | 41 | — | 95 |
| `c149` | main | MMF1 | 61 | 61 | 1.660 | 82.000 | 40 | — | 104 |
| `c154` | main | MMF1 | 61 | 61 | 1.702 | 44.410 | 41 | — | 109 |
| `c262` | main | MMF1 | 61 | 61 | 1.702 | 44.410 | 41 | — | 109 |
| `e81` | main | MMF1 | 61 | 61 | 1.660 | 42.697 | 40 | — | 104 |
| `b5m` | off | MMF1 | 61 | 61 | 0 | 60.050 | 1 | 50 | 804 |
| `b5r` | off | BBOB_F22 | 309 | 309 | 0 | 59.436 | 1 | 39 | 1.147 |
| `c311` | off | BBOB_F17 | 309 | 309 | 0 | 51.857 | 4 | 2 | 8 |
| `moead_media` | off | MMF1 | 61 | 61 | 0 | 60.050 | 1 | 50 | 804 |
| `treed_media` | sweep-big-mvns | ZDT4 | **50.000** | 50.000 | 0 | 57.281 | 1 | 37 | 13 |

### MATLAB (`smoke_matlab/experiments/`)

| config | exp | problema | FE | ① | ② | ③ | ④ | ⑦ | ⑥ |
|---|---|---|---|---|---|---|---|---|---|
| `b1` | main | MMF1 | 61 | 61 | 2.640 | 61.076 | 54 | — | 105 |
| `b3` | main | MMF1 | 61 | 61 | 369 | 22.709 | 8 | — | 16 |
| `b4` | main | MMF1 | 61 | 61 | 1.915 | 59.541 | 45 | — | 100 |
| `c141` | main | MMF1 | 61 | 61 | 128 | 14.420 | 10 | — | 21 |
| `c217` | main | MMF1 | 61 | 61 | 1.806 | 55.042 | 42 | — | 91 |
| `c238` | main | MMF1 | 61 | 61 | 1.681 | 42.800 | 40 | — | 64 |
| `e7` | main | MMF11_L | 61 | 61 | 567 | 40.700 | 14 | — | 25 |
| **`e74`** | main | **MMF1** | 61 | 61 | 2.732 | 46.499 | 48 | — | 95 |
| **`e74`** | main | **DTLZ2** | 371 | 371 | 79.921 | 227.703 | 238 | — | 403 |
| **`e74`** | main | **ZDT1** | 929 | 929 | 516.445 | 591.602 | 627 | — | 1.080 |
| `moead` | main | DTLZ2 | 371 | 371 | 255 | **0** | 17 | — | 50 |
| `nsga2` | main | DTLZ2 | 371 | 371 | 260 | **0** | 13 | — | 42 |
| `nsga3` | main | DTLZ2 | 371 | 371 | 270 | **0** | 18 | — | 47 |
| `smsemoa` | main | DTLZ2 | 371 | 371 | 260 | **0** | 13 | — | 37 |
| `e103` | off | MMF1 | 61 | 61 | 2.917 | 59.800 | 1 | **100** | 108 |

**③ = 0 nos 5 pisos** (`sobol_batch`, `moead`, `nsga2`, `nsga3`, `smsemoa`): eles
**não têm surrogate** — não existe predição a gravar. **Não é falha.**

### `teto_c154/` — a validação do rito de teto

`main/c154/DTLZ2/s42` (D=12), truncada em **6 h**:
⑤ `status=failed` · **`motivo_parada=teto_wall`** · `fe_final=282/371` ·
① 282 · ② 31.237 · ③ 161.060 · ④ 151 · ⑥ 551. A ① tem exatamente
`fe_final` linhas.

### `g6_com/` × `g6_sem/` — os pares §3.1

A **mesma célula** rodada com e sem sonda, nos 9 configs MATLAB. Prova que a
instrumentação **não altera a busca**: a ① sai **byte a byte idêntica**. Você
pode usar isso para confiar que a instrumentação não contaminou o comportamento
que vai auditar.

| config | ① sha256 (idêntico nos dois lados) |
|---|---|
| b1 `4d81d858eaeb1729` · b3 `760941d23f75eb70` · b4 `2404320fa6f276b9` | |
| c141 `d7f20cd0c4648c3f` · c217 `868a15c02c09610f` · c238 `43f533269741c82f` | |
| e7 `1e1060eeaae5fa49` · e74 `fc9ced7a6f4671ef` · e103 `a94d2766d257185a` | |

---

## 3. Como cada célula foi produzida

**Python:** `experiment.run(alg, problema, semente, exp=..., data_root=<tempdir>)`
em **processo próprio** (1 por vez — `torch.set_default_dtype` é global e uma
tentativa com threads corrompeu 5 de 10 resultados). Célula **mais barata** de
cada config, medida na rodada-42.

**MATLAB:** `experiments('algorithms',{...},'seeds',42,'parallel',false,'dataRoot','<tempdir>')`.
⚠ `'parallel',false` é obrigatório: o `e103` não funciona em worker `parfor`
(a ponte `pyenv` InProcess falha).

**Nenhum smoke escreveu em `data/experiments`.** Verificado por duas medidas
independentes: **0 manifestos com `campanha_id`** (campo obrigatório desde o
B-03, logo qualquer run desta campanha o teria) e **0 arquivos modificados**.

## 4. Como auditar

```bash
cd /Users/gmello/Documents/python_repos/mestrado/ua-dd-saea
PY=/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python
D=/Users/gmello/Documents/python_repos/mestrado/evidencia_T11

$PY -c "
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'scripts')
import gates_proveniencia as G
for n,ok,det in G.gates_de_proveniencia('main','b1','MMF1',42,'$D/smoke_matlab',modo='campanha'):
    print('%-18s %s %s' % (n,{True:'OK',False:'RUIM',None:'n/a'}[ok],det))"
```

⚠ **Use `gates_proveniencia` direto, NÃO o `portao.py`** nestas pastas: o
`accept.py` não aceita `--data-root` e leria `data/` (achado #42). O portão sabe
disso e marca o `accept` como NÃO-AFERÍVEL fora de `data/`, mas o caminho direto
é mais limpo.

**Ler as camadas:**
```python
import pyarrow.parquet as pq, json
D="/Users/gmello/Documents/python_repos/mestrado/evidencia_T11"
b=f"{D}/smoke_matlab/experiments/main/c217/exp_main_c217_MMF1_42"
man=json.load(open(b+".manifest.json"))
print(man["sigma_dict"])          # ⚠ LEITURA OBRIGATÓRIA antes de usar a ③
t3=pq.read_table(b+"__surrogate.parquet")
```

---

## 5. 🚨 O QUE ESTES SMOKES **NÃO** PROVAM

**Provam:** o config roda ponta a ponta; escreve as camadas contratadas; o ⑤
traz `campanha_id`/`repo_hash`/schema v2 e as 6 chaves; o ⑥ tem header+footer
sem linha malformada; a proveniência fecha; a sonda **não perturba** a busca.
**É verificação de ENCANAMENTO.**

**NÃO provam:**
· que os **valores** produzidos estão certos — os gates conferem ESTRUTURA
· que o algoritmo faz o que o **artigo** descreve
· que a busca converge como deveria
· que os hiperparâmetros são os do paper

**Um algoritmo pode estar profundamente errado e passar nos 6 portões.**

### E o limite de UMA célula

Cada config tem **1 célula** aqui (o `e74` tem 3). Uma célula não permite
concluir nada sobre variância entre problemas, entre sementes, nem sobre
comportamento assintótico. Para isso existe a **rodada-42** em
`ua-dd-saea/data/experiments` — 5 a 58 células por config.

**A rodada-42 é VÁLIDA para análise de fidelidade em 23 dos 24 configs.** A
campanha T11 só acrescentou instrumentação **read-only**, e a não-perturbação
foi provada em **19/19** configs com a ① bit-idêntica. A busca da s42 é a mesma
que o código de hoje faria.

⚠ **Exceção: `e74`.** O fix **DI-45** mudou o comportamento **de propósito**
(`ClassifierSelect.m:56-58` — um índice relativo a subconjunto era usado como
absoluto). Para o e74, a s42 é **PRÉ-fix** e só este smoke é **PÓS-fix**.
Compare os dois.

⚠ **Ressalva de população:** `data/experiments` tem **744** células, não as 666
oficiais — inclui semente 0, o `_baseline_pre_retrofit` e stubs. Se for publicar
número, filtre por semente 42 ou use `resultados_experimentos`.

---

## 6. Onde estão as respostas que você vai precisar

| pergunta | onde |
|---|---|
| As divergências código×paper **já classificadas** | `handoff/T11-RODADA-FINAL.md` **§15.3** (10 configs) |
| Os 2 achados 🔴 desta campanha (VD-b1, VD-b3) | **§15.4** — com as ERRATAS 10 e 16 que corrigem a própria leitura |
| O que a instrumentação oferece por config | **§15.5** |
| As **regras de leitura obrigatórias** | **§15.6** e `CONTRATO_DE_DADOS.md` §10 |
| O contrato de campos por config | `claude_code_context/artifacts/contrato_61.json` |
| A bússola de classificação (🔴🔵🟠🟣🟢) | `SPEC_experimentos_v5.2.md:434` |

## 7. ⚠ Desconfie dos números do handoff

A campanha T11 produziu **16 erratas**. **Cinco** eram falso-positivo de gates
que ela mesma escreveu; **duas** corrigiram a própria leitura do VD-b1; **uma**
(a 15) descobriu que o número que ela chamou de "prova do DI-45" mede outro
sítio. A auditoria adversarial achou **4 CRÍTICOS** de falso-verde nos gates.

**Re-meça o que for usar.**
