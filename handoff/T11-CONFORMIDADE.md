# T11 · RELATÓRIO DE CONFORMIDADE POR ALGORITMO (2026-07-30)

> **O que este documento afirma e o que NÃO afirma.** Ele reporta **encanamento
> verificado**: o config roda ponta a ponta, escreve as camadas contratadas, o
> ⑤ traz `campanha_id`/`repo_hash`/schema v2, o ⑥ tem header+footer sem linha
> malformada, a proveniência fecha e a sonda **não perturba a busca**.
> Ele **NÃO** afirma correção numérica, fidelidade ao artigo, nem que a busca
> faz o que deveria — um algoritmo pode estar profundamente errado e passar nos
> 6 portões. A validação de fidelidade é MANUAL e do autor (D97).
>
> Código congelado em `25e95b4`. Suíte **627 testes, 0 falhas**. Preflight
> **11/11 lacres**. Varredura de proveniência: **744 células**.

## 1. Placar

| | configs |
|---|---|
| ✅ **verde pleno** — smoke + 6/6 portões + §3.1 bit-idêntica | **6** |
| ⚠ **verde com inconclusivo POR DESENHO** (G-1 sem linha marcada na ③) | **5** |
| ⚪ **sem cobertura nesta máquina** (MATLAB) | **13** |

**§3.1 — o invariante 🔴 do CONTRATO (a sonda não pode alterar a busca):
10 de 10 configs Python provados BIT-IDÊNTICOS**, todos com o **mesmo sha256**
das provas anteriores à campanha. A mudança do A11 (115 linhas, 0 remoções) não
perturbou nenhuma busca — não é inferência, é o mesmo hash.

## 2. A tabela

| # | config | stack | smoke | portão | par G-6 §3.1 | o que falta |
|---|---|---|---|---|---|---|
| 1 | `b1` | matlab | ⚪ falta (MATLAB) | — | ⚪ falta | smoke MATLAB + par G-6 |
| 2 | `b3` | matlab | ⚪ falta (MATLAB) | — | ⚪ falta | smoke MATLAB + par G-6 |
| 3 | `b4` | matlab | ⚪ falta (MATLAB) | — | ⚪ falta | smoke MATLAB + par G-6 |
| 4 | `b5m` | python | ⚪ falta | — | ✅ BIT-IDÊNTICA | — |
| 5 | `b5r` | python | ✅ 132.5s | ⚠ G-1 | ✅ BIT-IDÊNTICA | — |
| 6 | `c122` | python | ✅ 50.4s | ✅ 6/6 | ✅ BIT-IDÊNTICA | — |
| 7 | `c141` | matlab | ⚪ falta (MATLAB) | — | ⚪ falta | smoke MATLAB + par G-6 |
| 8 | `c149` | python | ✅ 251.1s | ✅ 6/6 | ✅ BIT-IDÊNTICA | — |
| 9 | `c154` | python | ✅ 98.1s | ✅ 6/6 | ✅ BIT-IDÊNTICA | — |
| 10 | `c217` | matlab | ⚪ falta (MATLAB) | — | ⚪ falta | smoke MATLAB + par G-6 |
| 11 | `c238` | matlab | ⚪ falta (MATLAB) | — | ⚪ falta | smoke MATLAB + par G-6 |
| 12 | `c262` | python | ✅ 34.8s | ✅ 6/6 | ✅ BIT-IDÊNTICA | — |
| 13 | `c311` | python | ✅ 26.0s | ⚠ G-1 | ✅ BIT-IDÊNTICA | — |
| 14 | `e103` | matlab | ⚪ falta (MATLAB) | — | ⚪ falta | smoke MATLAB + par G-6 |
| 15 | `e7` | matlab | ⚪ falta (MATLAB) | — | ⚪ falta | smoke MATLAB + par G-6 |
| 16 | `e74` | matlab | ⚪ falta (MATLAB) | — | ⚪ falta | smoke MATLAB + par G-6 |
| 17 | `e81` | python | ✅ 23.5s | ✅ 6/6 | ✅ BIT-IDÊNTICA | — |
| 18 | `moead` | matlab | ⚪ falta (MATLAB) | — | ⚪ n/a | smoke MATLAB + par G-6 |
| 19 | `moead_media` | python | ✅ 35.0s | ⚠ G-1 | ✅ BIT-IDÊNTICA | — |
| 20 | `nsga2` | matlab | ⚪ falta (MATLAB) | — | ⚪ n/a | smoke MATLAB + par G-6 |
| 21 | `nsga3` | matlab | ⚪ falta (MATLAB) | — | ⚪ n/a | smoke MATLAB + par G-6 |
| 22 | `smsemoa` | matlab | ⚪ falta (MATLAB) | — | ⚪ n/a | smoke MATLAB + par G-6 |
| 23 | `sobol_batch` | python | ✅ 1.7s | ⚠ G-1 | ⚪ n/a | — |
| 24 | `treed_media` | python | ✅ 27.9s | ⚠ G-1,G-7 | ✅ BIT-IDÊNTICA | — |

## 3. Como ler os ⚠

| config | aviso | por quê é ESPERADO |
|---|---|---|
| `b5r` `c311` `moead_media` `sobol_batch` `treed_media` | G-1 3×1 INCONCLUSIVO | a ③ desses configs não tem linha com `real_solution_id` — o gate 3×1 confere a identidade ③↔① das linhas MARCADAS, e sem marca não há o que conferir. **Não-aplicável ≠ falha** |
| `treed_media` | + G-7 INCONCLUSIVO | o ⑥ não tem evento de geração. **O ⑤ foi auditado assim mesmo** (4/4) — esse foi o conserto de 2026-07-30: antes, um ⑥ sem evento absolvia o manifesto inteiro |

## 4. O que os 13 MATLAB precisam — e quanto custa

Medido: a **célula mais barata de cada config** soma **405 s ≈ 6,7 min** de
algoritmo (`e7` é 293 s deles; `moead`/`nsga3` são 0 s). Com o boot da sessão
MATLAB, o realista é **15–25 min em série**. A estimativa anterior de "3–6 h"
estava **10× errada** — ela media células de produção, não a mais barata.

**O bloqueio nunca foi tempo: é que `matlab.engine` não importa neste venv.**

## 5. O que falta, por dono

| item | dono | custo |
|---|---|---|
| 13 smokes MATLAB + 9 pares G-6 MATLAB | autor | ~5 min (4 em ∥) |
| `e74` pós-DI-45: 3 células + gate ±3σ + `n_desalinhado`→~0 | autor | ~2 min |
| **`c154/DTLZ2/s42` (D=12) — validação do teto** | **rodando aqui** | teto de 6 h |
| probe de RAM do `c262-batch` | Python — pode rodar aqui | ~2,2 h |
| V2 · re-runs da s42 | autor | ~2–4 h |
| Limpar os 58 manifestos forasteiros | autor | ~15 min |
| `export UA_DD_SAEA_CAMPANHA_ID` nas 4 máquinas | autor | ~10 min |
| Decidir o wrapper do gatilho do `adapt` (A3/I-05 item 4) | autor | decisão |
| Tag `t11-definitivo` + push + disparo | autor | — |

## 6. Ressalvas honestas

1. **11 de 24 configs têm encanamento verificado.** Os 13 MATLAB não têm
   verificação nenhuma nesta máquina — nem smoke, nem par G-6.
2. **A validação do teto está em curso, com 6 h em vez de 12 h.** O que se
   prova é o MECANISMO (truncar COM dado, ⑤ coerente com
   `motivo_parada='teto_wall'`); o valor do teto é parâmetro. Decisão do autor,
   para o resultado sair no mesmo dia.
3. **56 achados da varredura (médios/baixos/cosméticos) ficaram fora** desta
   rodada. Pela nota dos próprios auditores não bloqueiam a campanha.
4. **13 erratas nasceram nesta campanha de "verifique antes de escrever"** —
   e 4 delas eram falso-positivo de gate MEU. Nenhum número deste relatório foi
   copiado de documento: todos foram re-medidos hoje.
