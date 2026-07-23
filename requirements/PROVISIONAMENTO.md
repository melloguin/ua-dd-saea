# PROVISIONAMENTO — receitas EXECUTÁVEIS, máquina zero-contexto → pipeline rodando

> **Para quem é.** Alguém (ou uma VM nova) sem NENHUM contexto, que precisa recriar os ambientes
> e rodar o pipeline. Cada env tem: a **intenção** (`requirements/env_*.txt` — pins decididos pelo
> autor, D80), o **lock resolvido** (`requirements/locks/env_*.lock.txt` — a foto `pip freeze`
> exata dos ambientes VALIDADOS — data no cabeçalho de cada lock) e a **receita** abaixo. Instale pela intenção;
> confira contra o lock; divergência de versão = pare e pergunte ao autor (D80).
> Mapa alg→env: `claude_code_context/artifacts/envs.json` (`alg_to_env` — FONTE ÚNICA, DI-14).

## 0. Pré-requisitos da máquina

| Item | Mac (referência: macOS 12.5.1 arm64) | VM Linux (bateria M8+) |
|---|---|---|
| Compilador C | Xcode CLT (`xcode-select --install`) — exigido pelo build do GPy | gcc/build-essential |
| Rosetta 2 | `softwareupdate --install-rosetta` (para env_b5/env_c311 x86_64) | n/a (x86_64 nativo) |
| pyenv | py 3.11.9 (env_main/env_e81/bridge) | idem ou micromamba |
| micromamba | bootstrap abaixo (sem sudo) | idem (linux-64) |
| MATLAB | R2025a Update 1 + toolboxes do lock (`locks/env_matlab_ver.lock.txt`) | não roda na VM (MATLAB = só Mac) |

**Bootstrap do micromamba (usado p/ os envs x86_64; versão validada: 2.8.1):**
```bash
TOOLS=/Users/gmello/Documents/python_venvs/_micromamba
mkdir -p "$TOOLS/bin" "$TOOLS/root" && cd "$TOOLS"
curl -Ls https://micro.mamba.pm/api/micromamba/osx-arm64/latest | tar -xj bin/micromamba
# (VM Linux: trocar osx-arm64 por linux-64)
```

**Pins de thread (D79) — SEMPRE, em todo run:** `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1`; MATLAB: `maxNumCompThreads(1)` (o harness já aplica).
**Determinismo (família desdeo/GPy — b5, c311, moead_media) [DI-27]:** rodar SEMPRE com
`PYTHONHASHSEED=0` (o `run_in_venv` já aplica de fato desde o fix `b782167`; em invocação MANUAL,
exporte antes). ⚠ **Drift do pyDOE**: os pyDOE novos (ex.: 0.9.1) ignoram `np.random.seed` no
`lhs(seed=None)` — a pop inicial do RVEA/DESDEO vira não-reprodutível. Os runners corrigem em
RUNTIME (gancho/injeção do RandomState global semeado — `src/b5_prob.py` e `src/c311_tgprmo.py`);
qualquer runner novo da família DEVE herdar o mesmo fix (**RATIFICADO pelo autor — DI-28.3:
o gancho é DEFINITIVO; NÃO re-pinar o pyDOE antigo**).

## 1. env_main — py 3.11.9 arm64 (c262 · c154 · c122 · c149 + harness/despachante/métrica)
```bash
pyenv install 3.11.9
~/.pyenv/versions/3.11.9/bin/python -m venv /Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao
<venv>/bin/python -m pip install -r requirements/env_main.txt   # conferir vs locks/env_main.lock.txt
```

## 2. env_b5 — py **3.7 EXATO** x86_64 (b5r · b5m · moead_media/piso-off) — OFFLINE
Por quê 3.7: o único Python com wheel do `scikit-learn==0.21.3` (cp37m). No Mac arm64 NÃO existe
wheel nativo ⇒ a rota é **x86_64 sob Rosetta** (validada 2026-07-22); na VM Linux, manylinux1 cp37.
```bash
export MAMBA_ROOT_PREFIX=/Users/gmello/Documents/python_venvs/_micromamba/root
CONDA_SUBDIR=osx-64 micromamba create -y -p /Users/gmello/Documents/python_venvs/env_b5 \
    -c conda-forge python=3.7 pip          # VM Linux: omitir CONDA_SUBDIR (linux-64 nativo)
/Users/gmello/Documents/python_venvs/env_b5/bin/python -m pip install \
    "scikit-learn==0.21.3" "desdeo-problem==0.14.0" "desdeo-tools==0.2.6" \
    statsmodels matplotlib pyDOE "pandas==1.3.5" numpy pyarrow \
    "pymoo==0.6.1.2" "plotly==4.14.3" graphviz
# pygmo: NÃO instalar (force-import de NSGAIII/PPGA no desdeo_emo, mas b5 nunca os usa;
#        dep pesada Boost, ausente até no env_c311). O runner b5_prob.py stuba em sys.modules.
```
- ⚠ `desdeo-emo`: **CRAVADO no gate R3.2 (cartão R3-b5, autor delegou) = VENDORED, SEM pacote pip.**
  Fonte única = `algorithms/b5_Prob-RVEA/desdeo_emo` (overlay root-first no sys.path; a SurrogateKriging
  de kernel fixo mora no `desdeo_problem` vendorizado). Travado por content-hash (`b5_desdeo` no repos.lock).
- ⚠ `pymoo==0.6.1.2` **[R3-b5 2026-07-23]**: os finais ⑦ e o filtro ND são avaliados via `src/problems.py`
  DENTRO do runner offline (env_b5) — o env não o tinha (gap; o R3-00 REPASSE já assumia "pymoo antigo"
  em env_b5). Instalado com constraints (o core validado NÃO se moveu). **py3.7:** o runner aplica o shim
  `typing.Literal = typing_extensions.Literal` ANTES de importar `src.problems` (o NDS loader do pymoo
  importa `typing.Literal`, que só existe em py3.8+). Roda puro-python (sem Cython) — só velocidade; os
  conjuntos finais são pequenos. Vale igual p/ c311/moead_media (env_b5-família).
- Prova de aceitação ⑦: `MPLBACKEND=Agg <env>/bin/python -c "import typing,typing_extensions; typing.Literal=getattr(typing,'Literal',typing_extensions.Literal); from src import problems as P, standalone_harness as H; import numpy as np; P._nds_filter(P.evaluate_problem(H._instantiate('DTLZ2'), np.random.rand(8,12)))"`.
- Resolvidos validados: **pandas 1.3.5** (⚠ [R3-b5 2026-07-23] SUBIDO de 0.25.3 pelo autor — o 0.25.3
  QUEBRA o `DataProblem` do desdeo; o desdeo NÃO pina pandas, então "forçado pelo desdeo" era incorreto;
  o harness escreve parquet 100% via pyarrow ⇒ a saída não muda), numpy 1.21.6, pyarrow 12.0.1 (lock).
- Prova de aceitação: `<env>/bin/python -c "import sklearn, desdeo_problem; from src.standalone_harness import load_sonda; load_sonda('MMF1', regime='offline')"` (na raiz do repo).

## 3. env_c311 — py **3.8 EXATO** x86_64 (c311/TGPR-MO) — OFFLINE
⚠ **NUNCA 3.9**: o C pré-gerado do GPy 1.9.9 usa `tp_print` (removido no py3.9) — o build falha
em QUALQUER plataforma com 3.9 (lição medida no provisionamento; vale na VM). ⚠ `Pillow<10`
(Pillow≥10 exige numpy≥1.21; o pin é 1.20.2). Rodar sempre com `MPLBACKEND=Agg`.
```bash
CONDA_SUBDIR=osx-64 micromamba create -y -p /Users/gmello/Documents/python_venvs/env_c311 \
    -c conda-forge python=3.8 pip
PY=/Users/gmello/Documents/python_venvs/env_c311/bin/python
$PY -m pip install "numpy==1.20.2" "scikit-learn==1.1.2" scipy pyDOE "plotly==4.14.3" \
    "plotly-express==0.4.1" matplotlib statsmodels pandas "Pillow<10" pyarrow graphviz
$PY -m pip install --no-build-isolation "GPy~=1.9.9"    # COMPILA o sdist (precisa do CLT/gcc)
$PY -m pip install "pymoo==0.6.1.2"                     # [R3-c311 Fase B] finais ⑦/ND via src/problems.py
```
- Prova GPy: `MPLBACKEND=Agg $PY -c "import GPy; import numpy as np; m=GPy.models.GPRegression(np.random.rand(20,2), np.random.rand(20,1)); m.optimize(max_iters=5); m.predict(np.random.rand(3,2))"`.
- ⚠ `pymoo==0.6.1.2` **[R3-c311 Fase B 2026-07-23]**: os finais ⑦ e o filtro ND são avaliados via
  `src/problems.py` DENTRO do runner offline (env_c311) — **MESMO gap do env_b5** (§2). Instalado com
  constraints do freeze (o núcleo validado — numpy 1.20.2 / GPy 1.9.9 / sklearn 1.1.2 / pyarrow 17 — NÃO
  se moveu). **py3.8 tem `typing.Literal` nativo ⇒ SEM o shim do env_b5.** Puro-python
  (`py3-none-any.whl`, sem Cython — só velocidade; conjuntos finais pequenos). Prova ⑦: `MPLBACKEND=Agg
  $PY -c "from src import problems as P, standalone_harness as H; import numpy as np; P._nds_filter(P.evaluate_problem(H._instantiate('DTLZ2'), np.random.rand(8,12)))"`.
- ⚠ `optproblems` **NÃO instalado**: dep de import-time do `desdeo_problem/__init__` via `testproblems`,
  que o caminho `DataProblem` do c311 NUNCA usa. O runner `src/c311_tgprmo.py` **STUBA**
  `optproblems.{zdt,dtlz}` em `sys.modules` ANTES do import (respeita D80 — não instala pacote no env).
  `pygmo`: idem AUSENTE do caminho `framework/` do c311 (DI-16.14) — **nenhum shim** (≠ b5).
- ⚠ `pyDOE`: drift do §0 — o runner c311 herda o **gancho lhs-determinismo** (RandomState global
  semeado). RATIFICADO DEFINITIVO (DI-28.3): NÃO re-pinar o pyDOE antigo, NÃO materializar patch.
- Prova offline: `<env>/bin/python -c "import GPy, sklearn, desdeo_problem; from src.standalone_harness import load_sonda; load_sonda('MMF1', regime='offline')"` (na raiz do repo).

## 4. env_e81_qpots — py 3.11.9 **arm64 nativo** (e81/qPOTS) — ONLINE
Pin do torch **RE-PINADO pelo autor (DI-22)**: `2.12.0 → 2.11.0` (o 2.12 exige macOS≥14, sem
wheel x86_64/sdist; o 2.11.0 é o MESMO do env_main). O `.txt` já reflete.
```bash
~/.pyenv/versions/3.11.9/bin/python -m venv /Users/gmello/Documents/python_venvs/env_e81_qpots
<venv>/bin/python -m pip install -r requirements/env_e81_qpots.txt
```
- Prova: fit BoTorch (`SingleTaskGP` + `fit_gpytorch_mll`) + `load_sonda('MMF1', regime='online')`.

## 5. env_bridge — py 3.11.9 `--enable-shared` (a ponte MATLAB↔Python)
O MATLAB embute este Python via `pyenv(Version=...)` InProcess — **precisa do libpython dylib**:
```bash
PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.11.9   # se ainda não for shared
python -m venv ~/ponte_teste && ~/ponte_teste/bin/pip install -r requirements/env_bridge.txt
# no MATLAB (1×): pyenv('Version','/Users/gmello/ponte_teste/bin/python','ExecutionMode','InProcess')
# smoke: py.numpy.array([1,2,3]).sum() == 6
```

## 6. env_matlab — R2025a Update 1 (13 configs: 9 SA-MOEAs + 4 pisos)
Toolboxes EXATAS no lock `locks/env_matlab_ver.lock.txt` (capturado por `matlab -batch ver`).
PlatEMO + repos dos autores já estão VENDORIZADOS em `algorithms/` (lacre: `repos.lock` +
`anchors.json`; qualquer divergência de SHA ⇒ o preflight aborta). Parquet MATLAB = brotli
(sem zstd no R2025a; a consolidação re-encoda — decisão registrada).

## 7. Ordem de verificação numa máquina nova (o smoke de 10 minutos)
```bash
$ENV_MAIN/bin/python -m unittest discover -s tests   # 247+ OK
$ENV_MAIN/bin/python scripts/preflight.py            # exit 0 (lacres/âncoras/artefatos)
$ENV_MAIN/bin/python scripts/naoperturbacao.py --all # baselines bit-a-bit
# + as provas por-env das seções 2-5
```
