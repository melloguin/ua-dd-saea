# c217-fix-log — RELATÓRIO DE EXECUÇÃO (narrativa do processo)

> **Propósito.** Descrever o PROCESSO INTEIRO da sessão de fix dos 2 campos de log do c217 — passo a
> passo, com o diagnóstico, as decisões, cada código rodado e cada resultado — para a torre de
> controle (a instância que gerou as instruções) entender exatamente o que foi feito e por quê. O
> `handoff/c217-fix-log.md` é o repasse técnico; **este é o relatório de PROCESSO**. Data: 2026-07-16.
> Branch: `experiment/definitive_algorythms`. Modelo: Opus 4.8.

---

## 0. Veredito em uma linha

**100% pronto e validado por execução.** Tarefa = ENCANAMENTO objetivo (valores de log corretos), não
fidelidade (D97) → não há parte pendente do autor. **Resultado inesperado (importante):** só UMA das 2
pontas era um problema real — (A) duplicação; (B) já estava correto per a SPEC → o autor decidiu não
mudar. Fix final: `src/c217_instrument.m`, 9+/2−.

---

## 1. PASSO 0 — Ambiente + contexto (na ordem exigida, e só isto)

- **Ambiente (D80/D81):** ponte MATLAB `double(py.numpy.array([1,2,3]).sum()) → 6` ✅; env-main
  (`/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python`) presente.
- **Contexto lido:** `HANDOFF_MESTRE.md`, `handoff/R1-c217.md`, `CLAUDE.md` (raiz + contexto),
  `00_fundacao/03_contrato_export.md` (§17.2 — DEFINIÇÃO das colunas ③ e dos campos do `.jsonl`,
  incl. `pred_confianca`/`n_contradicoes`/`n_empates`), `10_rodada1_matlab/alg_c217_pcsaea.md`
  (I.5/L.5/**M.4** — semântica do PNN, p⁺/p⁻, estados, contradições), e o alvo `src/c217_instrument.m`
  inteiro. NÃO li `alg_*.md` de outro algoritmo; NÃO toquei em algoritmo/gate/infra.

## 2. PASSO 1 — Diagnóstico (o núcleo desta sessão)

Rastreei as DEFINIÇÕES no SPEC, campo a campo:

### (A) `n_contradicoes` vs `n_empates` — **MESMO conceito** (não distintos)
- **M.4:** "o modelo deveria rotular ⟨x,y⟩ e ⟨y,x⟩ de forma OPOSTA. p⁺=consistente-e-certo;
  p⁻=consistente-e-invertido=erro SISTEMÁTICO; **rótulos iguais = contradição = erro ALEATÓRIO →
  ignorar**." → `rótulos iguais` = forward==reverse = `result==0` = **`TestPre==1.5`** (verifiquei em
  `RBFNNPC.lastpredict` flag=1: `Y(result==0)=1.5`).
- **S.3#4 / S.7:** "**empates** (TestPre==1.5)". → contradição (M.4) ≡ empates (S.3#4) ≡
  `sum(TestPre==1.5)`. **Uma quantidade, dois nomes.** Nenhuma seção define uma 2ª quantidade distinta.
- **§17.2.1** (a spec DEDICADA do "Log de auditoria da regra tripla do c217") lista **só**
  `n_contradicoes`; S.7 lista os dois nomes mas só `empates` tem def operacional.
- **Diagnóstico:** não é bug de VALOR (o código computava `sum(TestPre==1.5)` e o atribuía aos DOIS
  campos — valor certo), é **DUPLICAÇÃO** (dois nomes p/ um conceito).

### (B) `pred_confianca = Error1` — **§17.2 diz Error1 (GERAL); código já CORRETO**
- §17.2, **3 citações**: l.57 "pred_confianca = … **Error1 da geração no c217**"; l.84 "a confiabilidade
  (**Error1 no c217**)"; l.84 (decisivo) "a confiabilidade da geração (**Error1/Error2/estado**) vai no
  **log** (§17.5)" — i.e., o ③ leva o **resumo Error1**; o por-estado (Error1/Error2/estado) **já vai no
  `.jsonl`** (`p_mais`/`p_menos`/`estado`, §17.2.1).
- **Diagnóstico:** o código atual (`pred_confianca=Error1`) está **FIEL à §17.2**. Não é bug. A
  alternativa "estado-específico" (uso-reverso→Error2=p⁻, semântica M.4) **SOBREPORIA a §17.2** = uma
  decisão de fidelidade do autor (D97), não minha. E o por-estado é **recuperável do `.jsonl`** (nada
  se perde).

## 3. Checkpoint — parei e perguntei (D81), 2 decisões do autor

O card mandou "me apresente ANTES de corrigir". Como (B) exigia a decisão do autor (SPEC diz Error1,
mas ele sinalizou; sobrepor é call dele) e (A) tinha uma escolha de NOME, **apresentei o diagnóstico e
usei `AskUserQuestion`** (não editei código antes):

| Ponta | Pergunta | **Decisão do autor** |
|---|---|---|
| (B) `pred_confianca` | Manter Error1 (§17.2) ou sobrepor p/ estado-específico? | **Manter Error1 (§17.2)** → 0 mudança |
| (A) campo único | Manter `n_contradicoes` ou `n_empates`? | **`n_contradicoes`** (nome do §17.2.1) |

> **Nuance que a torre deve saber:** o PASSO 3 do card deu como exemplo de prova "numa geração de
> uso-reverso, `pred_confianca` = p⁻" — isso **presumia** que (B) viraria estado-específico. O autor
> decidiu **manter Error1**, então a prova correta virou: numa geração estado-2, `pred_confianca`=Error1
> (mantido), **com p⁻=Error2 presente no `.jsonl`** (recuperável). Adaptei a prova à decisão real.

## 4. PASSO 2 — A correção (só `src/c217_instrument.m`)

Duas edições, ambas para (A); **(B) sem mudança**:
1. Variável `n_empates` → **`n_contradicoes`** (`= sum(TestPre(:)==1.5)`), com bloco de comentário
   documentando os três nomes = um conceito (M.4/S.3#4/§17.2.1) e por que 1 campo só.
2. Emissão do `.jsonl`: `'n_contradicoes', double(n_empates), 'n_empates', double(n_empates)` →
   **`'n_contradicoes', double(n_contradicoes)`** (remove o duplicado).

**Preservados intactos:** lógica de estado/score (regra tripla D17), `pred_confianca=Error1` (B), o
schema da ③, o timing §17.6, e os helpers. Diff: **9 inserções / 2 remoções**.

## 5. PASSO 3 — Validação (todo o código rodado + resultado)

| # | Comando | Resultado |
|---|---|---|
| 1 | `checkcode src/c217_instrument.m` | 2 notas de ESTILO pré-existentes (`nnz`/`sum` na linha herdada; vírgula de `catch, end`) — 0 erros; card manda preservar o resto |
| 2 | `grep n_empates / pred_confianca / n_contradicoes` | 0 ref de código a `n_empates` (só no comentário); `pred_confianca=Error1` intacto; `n_contradicoes` computado 1× e emitido 1× |
| 3 | Re-run c217 MATLAB: MMF1, ZDT1, DTLZ2, DTLZ2_d15 (s0) | FE **61/929/371/464** exatos; `cp_ok=1`; cache_hits 1/4/1/1 — o fix (instrumentação) não afeta a execução |
| 4 | **Gate** `accept.py R1-c217 --alg c217 --problema {MMF1,ZDT1,DTLZ2} --semente 0` | **VERDE (exit 0)** nos 3 |
| 5 | Regressão `accept.py R1-c141 --alg c141 --problema {MMF1,DTLZ2} --semente 0` | **VERDE** nos 2 (c141 já está ✅; o fix c217-only não pode afetá-lo — só `PCSAEA.m` chama `c217_instrument`) |
| 6 | Regressão `accept.py F0-0{1,2,3,4}-*` + `preflight` | exit **0** em todos |
| 7 | `prove_fields.py` (lê ③+`.jsonl` regenerados) | ver §6 |

*(Nota: descobri nesta sessão que o **c141 já foi implementado** por uma sessão posterior à minha de
R1-c217 — `case 'c141'` no `experiment.m`, outputs em disco, INDEX `R1-c141` → ✅. Por isso a regressão
nele é significativa. Não toquei em nada do c141.)*

## 6. Prova dos campos (③ + `.jsonl` regenerados, semente 0)

| Problema | `n_contradicoes` presente | `n_empates` ausente | geração demonstrada | ③ `pred_confianca` | `.jsonl` p_mais / p_menos |
|---|---|---|---|---|---|
| MMF1 (d=2) | ✅ | ✅ | g21 (estado 3) | 0.25 = p_mais | 0.25 / 0.25 |
| ZDT1 (d=30) | ✅ | ✅ | g345 (estado 1) | 0.8333 = p_mais | 0.8333 / 0.1667 |
| **DTLZ2 (d=12)** | ✅ | ✅ | **g214 (estado 2 = uso-reverso)** | **0.0 = p_mais(Error1)** | **0 / 0.8333** |

**A linha do DTLZ2 é a prova-chave (B):** numa geração **estado-2 (uso-reverso)**, o ③ `pred_confianca`
= **0.0 = Error1** (resumo geral, **mantido** per §17.2) — **não** p⁻=0.8333; e o `.jsonl` traz
`p_menos(Error2)=0.8333` → o valor que justificou a inversão (M.4) **está lá, recuperável**. Confirma
(A) [1 campo `n_contradicoes`, sem `n_empates`] e (B) [Error1 fiel à §17.2, sem perda do por-estado].
*(O ③ é float32 (D53): 0.83333331 vs 0.83333333 no `.jsonl` float64; |Δ|<1e-5, esperado.)*

## 7. Arquivos + commit

- **Único arquivo tocado:** `src/c217_instrument.m` (9+/2−). Saídas do c217 (MMF1/ZDT1/DTLZ2/DTLZ2_d15)
  regeneradas (`data/experiments/main/c217/`, gitignored). Handoff técnico `handoff/c217-fix-log.md` +
  este relatório.
- **Commit `[c217-fix-log]` `f8f9835`.** Working tree limpa (só `data/` gitignored resta).

## 8. Status honesto para a torre

- ✅ **100% pronto.** Gate VERDE (3 problemas), regressões VERDES (c141, F0-01..04, preflight), campos
  provados. Nada pendente — a tarefa era encanamento (D97 não se aplica ao meu julgamento aqui).
- 🔎 **Para a torre revisar (2 pontos de processo):**
  1. **(B) não era bug** — a §17.2 já mandava Error1 (3 citações) e o código já fazia. Confirmei com o
     autor (ele escolheu manter). Se a torre PRETENDIA estado-específico, isso é uma **mudança de
     definição da §17.2** (fidelidade, D97) — precisa ser decidida como tal, não como "fix de bug".
  2. **(A) foi decidido pelo nome `n_contradicoes`** (§17.2.1, a spec dedicada do log). Se a torre
     preferir `n_empates` (o nome com def operacional em S.3#4/S.7), é trocar 1 string — me avise.
