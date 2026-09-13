# env_matlab — o "ambiente" MATLAB (NÃO é um venv)

> **Resposta à pergunta "como fazemos venv no MATLAB?":** não fazemos. MATLAB **não tem** ambiente
> virtual (não há pip/venv). O isolamento vem de outros eixos. Não há nada para salvar em
> `python_venvs/` para o MATLAB — este arquivo É a especificação do ambiente MATLAB.

## O que define o ambiente MATLAB
- **MATLAB R2025a Update 1** (licença Academic Total Headcount) + toolboxes: **Deep Learning,
  Statistics and Machine Learning, Optimization, Parallel Computing**.
- **Paralelismo:** 8 workers PCT no Mac (o gargalo real; a licença TAH não limita ativações).
- **Export:** parquet **brotli** (o MATLAB não tem zstd) — os `.parquet` do MATLAB usam brotli; os do Python, zstd/brotli.

## Isolamento (o análogo do "venv" no MATLAB) = a árvore PlatEMO + a ponte
- **PlatEMO 4.15** (padrão, @b686ca2): b1, b3, b4, e7, c217, c141, c238 + pisos (nsga2, nsga3, moead type=1, smsemoa).
- **e74 (CLMEA):** roda na **sua própria árvore PlatEMO 4.1** (`CLMEA_Code`), com worker dedicado
  e o adendo N.0-4.1 (o UserProblem 4.1 não tem `once` → a ponte avalia por indivíduo). (D95)
- **e103 (IBEA-MS, offline):** **worker dedicado**; centros da RBFN = ⌈√n_dataset⌉ com n injetado. (D93)
- **Ponte (`env_bridge`):** os algoritmos MATLAB avaliam os 25 problemas de `src/problems.py` via
  `pyenv(ExecutionMode="InProcess")`, que embute o Python `--enable-shared` de `requirements/env_bridge.txt`.

## Algoritmos servidos (13 configs)
b1, b3, b4, e7, c217, c141, e74, c238, e103 (9 SA-MOEA) + nsga2, nsga3, moead, smsemoa (4 pisos online).

## Provisionamento
Nada a instalar via pip. Garantir: MATLAB + as 4 toolboxes ativas; o `pyenv` do MATLAB apontando
para o `env_bridge` (feito no cartão **R1-00-harness**); a árvore PlatEMO correta por algoritmo (acima).
