# sobol_batch-S23 — F5.4 · verificação adversarial

**VEREDITO: PARCIALMENTE REFUTADO → CONFIRMADO(d) reduzido a 1 campo (`n_front1`).**

## O que caiu
| campo alegado ausente | veredito | causa do falso-positivo |
|---|---|---|
| `ideal` | **REFUTADO** | `src/piso_instrument.m:38,58` define `ideal ≡ f_best` (mesmo array, dois nomes). O `f_best` logado == min por objetivo do arquivo, Δmáx 2,7e-10 a 3,4e-6 (roundtrip float32). A grandeza ESTÁ no ⑥. |
| `nadir_pop` | **REFUTADO** | (i) DI-30.B3 (autor, 2026-07-23) — "piso na taxonomia" ≠ "linha pisos no ⑥"; (ii) censo: 4/47 (alg,exp) do estudo logam, incl. 0/5 sweeps do 5º piso `moead_media`; (iii) para este config é o máximo CUMULATIVO ⇒ monótono não-decrescente em 5/5 (degenerado e incomparável ao nadir de população dos EAs). |
| `nadir_front1` | **REFUTADO** | idem (4/47; DI-30.B3). |
| `n_front1` | **CONFIRMADO** | 46/47 (alg,exp) do estudo logam; sobol_batch é o único que não. |

## Artefatos
- `r1_censo_campos.py` / `r1_censo_campos_{alg,celula}.csv` — censo por sufixo `_gen`.
- `r2_censo_amplo.py` / `r2_censo_amplo_{alg,celula}.csv` — censo por critério ALTERNATIVO
  (qualquer rec com `fe` **e** `f_best`); captura c154/c262/c311 que o R1 perdia. **47 linhas
  (alg,exp), 245 células, ~200 mil eventos.** Mesma conclusão ⇒ não é artefato de query.
- `r3_recuperabilidade.py` / `r3_recuperabilidade.csv` — `ideal≡f_best`, degenerescência do
  `nadir_pop`, custo do NDS no laço quente (0,3–1,6 % do wall).
- `r3_n_front1_recomputado.csv` — **os 1.000 valores recuperados** (5 células × 200 gerações).
- `r4_validacao_recuperacao.py` / `r4_validacao_recuperacao.csv` — controle positivo: o mesmo
  recomputo aplicado ao e81/batch bate o `n_front1` LOGADO em **1.000/1.000** eventos.
