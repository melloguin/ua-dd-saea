# handoff/c217-fix-log.md — fix de instrumentação do log do c217 (2 campos)

**Data:** 2026-07-16 · **Escopo:** ENCANAMENTO objetivo (valores logados corretos), **não** fidelidade
(D97). **Arquivo tocado: SÓ `src/c217_instrument.m`** (algoritmo, gate, infra compartilhada, DoE:
intocados). **Ambiente verificado:** ponte MATLAB `py.numpy…sum→6`; env-main presente.

**Gate VERDE + regressões:** `accept.py R1-c217 --alg c217 --problema {MMF1,ZDT1,DTLZ2} --semente 0`
→ exit 0 nos 3. Regressão: `accept.py R1-c141` (MMF1, DTLZ2) VERDE; `F0-01..04` exit 0; `preflight`
exit 0. O fix é c217-only (só a `PCSAEA.m` chama `c217_instrument`) → não pode afetar c141/F0.

---

## As 2 pontas — diagnóstico e decisão da SPEC

### (A) `n_contradicoes` vs `n_empates` → **MESMO conceito. Era DUPLICAÇÃO, não erro de valor.**

**A SPEC define uma ÚNICA quantidade** = os pares em que a predição forward==reverse do PNN (rótulos
iguais) = `TestPre==1.5` (`RBFNNPC.lastpredict` flag=1: `Y(result==0)=1.5`). Ela aparece com **três
nomes**:
- **M.4:** "rótulos iguais = **contradição** = erro ALEATÓRIO → ignorar".
- **S.3#4 / S.7:** "**empates** (TestPre==1.5)".
- **§17.2.1** (a spec DEDICADA do "Log de auditoria da regra tripla do c217"): campo `n_contradicoes`.

Nenhuma seção define uma **2ª quantidade distinta** — contradição (M.4) ≡ empates (S.3#4) ≡
`sum(TestPre==1.5)`. O código emitia o valor CORRETO, mas sob **dois nomes** (`n_contradicoes` e
`n_empates`, ambos `= double(n_empates)`).

**Correção (decisão do autor: manter `n_contradicoes`):** o log emite **1 campo só, `n_contradicoes`**
(nome do §17.2.1, a spec dedicada do log), `= sum(TestPre==1.5)`; o `n_empates` duplicado foi
**removido**. Comentário no código documenta os três nomes = um conceito.

### (B) `pred_confianca` → **§17.2 diz Error1 (GERAL). Código já estava CORRETO — NENHUMA mudança.**

**§17.2 define `pred_confianca` (③) = Error1 em 3 lugares:**
- l.57: "pred_confianca = … **Error1 da geração no c217**".
- l.84: "a confiabilidade (**Error1 no c217**)".
- l.84 (decisivo): "a confiabilidade da geração (**Error1/Error2/estado**) vai no **log** (§17.5)" — i.e.,
  o ③ carrega o **resumo Error1**; o Error1/Error2/estado **por-estado já vai no `.jsonl`**
  (`p_mais`/`p_menos`/`estado`, §17.2.1).

Logo o valor por-estado (uso-reverso → Error2=p⁻, semântica M.4) é **recuperável do `.jsonl`; nada se
perde**. Mudar o ③ para estado-específico SOBREPORIA a §17.2 (uma decisão de fidelidade do autor,
D97). **Decisão do autor: manter Error1 (§17.2).** → `pred_confianca = Error1` **inalterado**.

---

## Prova dos campos (③ + `.jsonl` regenerados, semente 0)

| Problema | `n_contradicoes` presente | `n_empates` ausente | geração demonstrada | ③ `pred_confianca` | `.jsonl` p_mais/p_menos |
|---|---|---|---|---|---|
| MMF1 (d=2) | ✅ | ✅ | g21 (estado 3) | 0.25 = p_mais | 0.25 / 0.25 |
| ZDT1 (d=30) | ✅ | ✅ | g345 (estado 1) | 0.8333 = p_mais | 0.8333 / 0.1667 |
| **DTLZ2 (d=12)** | ✅ | ✅ | **g214 (estado 2 = uso-reverso)** | **0.0 = p_mais(Error1)** | **0 / 0.8333** |

**A linha do DTLZ2 é a prova-chave (B):** numa geração **estado-2 (uso-reverso)**, o ③
`pred_confianca` = **0.0 = Error1** (o resumo geral, **mantido** per §17.2) — **não** p⁻=0.8333. E o
`.jsonl` traz `p_menos(Error2)=0.8333` → o valor que justificou a inversão (M.4) **está lá,
recuperável**. Confirma: (A) 1 campo `n_contradicoes` (sem `n_empates`); (B) `pred_confianca`=Error1
fiel à §17.2, sem perda do por-estado.

*(Nota: o ③ é float32 (D53) — ex.: 0.83333331 — vs float64 no `.jsonl` (0.83333333); |Δ|<1e-5, esperado.)*

## Distribuição de estados observada (informativa — a fidelidade é do autor, D97)

- MMF1 (d=2): 40× estado 3 (a granularidade grosseira `Error∈{0,0.5,1}` de D=2 — L.5).
- ZDT1 (d=30): estado 1 ×3, estado 3 ×585.
- DTLZ2 (d=12): estado 2 ×2, estado 3 ×228.

O estado 1 domina/aparece nas gerações confiáveis e o estado 2 (inversão) só dispara quando p_menos>δ
(§17.2.1 (b)) — coerente com o esperado do paper. O **julgamento de fidelidade é seu** (D97); aqui só
se corrigiu o ENCANAMENTO dos campos.

## Arquivos / commit

- Único arquivo tocado: `src/c217_instrument.m` (variável `n_empates`→`n_contradicoes`; emissão do
  `.jsonl` de 2 campos → 1). Lógica de estado/score, `pred_confianca=Error1`, ③ schema e timing:
  **preservados**. Saídas do c217 (MMF1/ZDT1/DTLZ2/DTLZ2_d15) regeneradas.
- Commit `[c217-fix-log]`. Runs em `data/experiments/main/c217/` (gitignored, regeneráveis).
