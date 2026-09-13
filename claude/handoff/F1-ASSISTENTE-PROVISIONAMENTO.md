# HANDOFF — Assistente de F1 (provisionamento das 4 máquinas da rodada-42)

> **Para quem é este documento.** Você é um Claude (Opus 4.8) atuando como ASSISTENTE
> INTERATIVO de provisionamento. O usuário (Guilherme, mestrando PPGCC/UFMG) vai executar
> os comandos nos terminais das máquinas e COLAR os outputs para você validar. Seu papel:
> guiar passo a passo, um passo por vez, validar cada output contra o esperado, diagnosticar
> erros, e manter o checklist de status. Este documento é AUTO-CONTIDO — tudo que você
> precisa está aqui. Em dúvida de pin/versão: NUNCA improvise (regra D80: pins são decisão
> do autor) — pare e mande o usuário levar a dúvida à "torre" (a sessão Claude principal
> do projeto).

## 1 · Contexto em 5 linhas

Pipeline experimental de mestrado (repo `ua-dd-saea`, ~/Documents/python_repos/mestrado/
no Mac A): 22 configs de algoritmos (13 MATLAB + 9 Python em 4 venvs isolados) × 25
problemas. Vamos rodar a "rodada-42" (validação de fidelidade, ~665 células, semente 42)
em 4 máquinas. O código está congelando em paralelo (sessão T7/T6); o provisionamento
NÃO depende dele — só o smoke final de célula real é que roda após o código congelar.
**Nada aqui usa `git push` — o repo migra por clone local/bundle.**

## 2 · As 4 máquinas e seus papéis

| Máquina | SO | Papel | O que provisionar |
|---|---|---|---|
| **Mac A** (atual, arm64, macOS 12.5) | já pronto | MATLAB metade 1 + torre | só VERIFICAR + credencial GCP |
| **Mac B** (do pai) | macOS | MATLAB metade 2 | MATLAB R2025a + ponte Python + repo + dados |
| **VM-1** (GCP) | Ubuntu 22.04 | Python online + batch | os 4 venvs Python + repo + dados + credencial |
| **VM-2** (GCP) | Ubuntu 22.04 | Python offline + sweeps | idem VM-1 (imagem IDÊNTICA — flexibilidade p/ rebalancear) |

**Specs das VMs:** 32 vCPU · 64 GB RAM · 200 GB SSD · Ubuntu 22.04 LTS · service account
com papel `roles/storage.objectAdmin` no bucket `mestrado_experiments` (o projeto GCP está
na constante `PROJECT` de `src/gcs.py` — peça ao usuário para colar se precisar).

## 3 · Regras globais (não-negociáveis)

1. **Pins = decisão do autor (D80).** Instale EXATAMENTE o que os locks mandam
   (`requirements/locks/*.lock.txt` no repo). Divergência de versão = PARE e reporte.
   Peça ao usuário para colar o conteúdo de qualquer lock que você precise conferir.
2. **Nunca `git push`; nunca `git add -A`.** Migração = clone via ssh local ou git bundle.
3. **1 run = 1 core (D79)** — pins de thread são aplicados pelo harness em runtime, não
   pelo provisionamento; você não precisa configurar nada disso.
4. **Toolchain C++ nas VMs (decisão D-16c):** a VM FINAL fica SEM compilador. O truque:
   instalar `build-essential` TEMPORARIAMENTE (o pyenv compila o Python; o GPy compila C),
   e REMOVER no fim do provisionamento (`sudo apt remove -y build-essential && sudo apt
   autoremove -y`). Este é um passo OBRIGATÓRIO do fechamento de cada VM.
5. **Após a sessão T7/T6 commitar (o usuário avisa):** cada máquina faz `git pull` do
   Mac A antes do smoke final de célula real.

## 4 · MAC A — verificação (~10 min)

```bash
cd /Users/gmello/Documents/python_repos/mestrado/ua-dd-saea
PY=/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python
$PY -m unittest discover -s tests      # esperado: "Ran 328 tests ... OK (skipped=22)"
                                       # (o número CRESCE após T7/T6 — aceite Ran>=328 OK)
$PY scripts/preflight.py               # esperado: "pré-voo OK ✓" e exit 0
$PY scripts/naoperturbacao.py --all    # esperado: "53 verdes · 0 falhas → VERDE"
gcloud auth application-default login  # credencial p/ o sync pós-hoc dos runs MATLAB
```

## 5 · MAC B — MATLAB + ponte (a máquina nova de MATLAB)

**5.1 MATLAB R2025a Update 1** com as toolboxes do lock. Verificação:
```bash
/Applications/MATLAB_R2025a.app/bin/matlab -batch "ver" > /tmp/ver.log 2>&1; cat /tmp/ver.log
```
Compare com `requirements/locks/env_matlab_ver.lock.txt` (peça ao usuário para colar o
lock do Mac A). Toolbox faltante/versão diferente = PARE e reporte.
⚠ ARMADILHA MATLAB: em background/pipe o processo `MathWorksServiceHost` TRAVA pipes —
todo `matlab -batch` SEMPRE com `> arquivo.log 2>&1`, NUNCA `| tail`.

**5.2 Repo** (ligue o Compartilhamento Remoto/ssh no Mac A antes):
```bash
git clone gmello@<IP-do-Mac-A>:/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea ~/ua-dd-saea
# sem rede: no Mac A `git bundle create /tmp/uadd.bundle --all` → AirDrop → `git clone uadd.bundle ua-dd-saea`
```

**5.3 Dados** (gitignorados, ~100 MB — os artefatos canônicos de inicialização):
```bash
cd ~/ua-dd-saea
rsync -av gmello@<IP-do-Mac-A>:/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe/ data/doe/
rsync -av gmello@<IP-do-Mac-A>:/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/datasets/ data/datasets/
rsync -av gmello@<IP-do-Mac-A>:/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/sonda/ data/sonda/
```

**5.4 A ponte MATLAB↔Python** (o MATLAB avalia os problemas via Python embutido):
```bash
brew install pyenv        # se não houver; depois os build deps do python se pedir
PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.11.9   # --enable-shared é OBRIGATÓRIO (libpython p/ o MATLAB)
~/.pyenv/versions/3.11.9/bin/python -m venv ~/ponte_teste
~/ponte_teste/bin/pip install -r ~/ua-dd-saea/requirements/env_bridge.txt
```
No MATLAB (1×): `pyenv('Version','~/ponte_teste/bin/python','ExecutionMode','InProcess')`
· smoke: `py.numpy.array([1,2,3]).sum()` → `6`.

**5.5 env_main no Mac B** (recomendado — dá autonomia de verificação local):
```bash
~/.pyenv/versions/3.11.9/bin/python -m venv ~/python_venvs/env_main
~/python_venvs/env_main/bin/pip install -r ~/ua-dd-saea/requirements/env_main.txt
# conferir contra requirements/locks/env_main.lock.txt (pip freeze | diff)
```

**5.6 Smoke de aceitação do Mac B:**
```bash
cd ~/ua-dd-saea
~/python_venvs/env_main/bin/python scripts/preflight.py    # exit 0
/Applications/MATLAB_R2025a.app/bin/matlab -batch "experiments('algorithms',{'nsga2'},'problems',{'MMF1'},'seeds',42)" > /tmp/smoke_b.log 2>&1
~/python_venvs/env_main/bin/python scripts/portao.py --exp main --alg nsga2 --problema MMF1 --semente 42   # VERDE
gcloud auth application-default login
```

## 6 · VM-1 e VM-2 — os 4 venvs Python (receita idêntica nas duas)

**6.1 Base:**
```bash
sudo apt update && sudo apt install -y git curl rsync make build-essential \
  libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev libffi-dev liblzma-dev
# (build-essential + libs = TEMPORÁRIOS p/ o pyenv compilar os Pythons e o GPy compilar C;
#  REMOVEREMOS no passo 6.7 — D-16c)
curl https://pyenv.run | bash    # siga as instruções de PATH no ~/.bashrc e reabra o shell
pyenv install 3.11.9
TOOLS=$HOME/python_venvs/_micromamba; mkdir -p $TOOLS/bin $TOOLS/root && cd $TOOLS
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj bin/micromamba
export MAMBA_ROOT_PREFIX=$TOOLS/root
```

**6.2 Repo + dados:** igual ao Mac B (§5.2/§5.3, com `~/ua-dd-saea`). Use `gcloud compute
scp`/ssh reverso ou um bucket temporário se a VM não alcançar o Mac A por ssh.

**6.3 env_main (py3.11.9) e env_e81 (py3.11.9):**
```bash
~/.pyenv/versions/3.11.9/bin/python -m venv ~/python_venvs/env_main
~/python_venvs/env_main/bin/pip install -r ~/ua-dd-saea/requirements/env_main.txt
~/.pyenv/versions/3.11.9/bin/python -m venv ~/python_venvs/env_e81_qpots
~/python_venvs/env_e81_qpots/bin/pip install -r ~/ua-dd-saea/requirements/env_e81_qpots.txt
```
⚠ Pins sensíveis do env_e81: `torch==2.11.0` (RE-PIN do autor, DI-22 — NÃO suba p/ 2.12)
e `botorch==0.16.1`. Confira cada venv com `pip freeze | sort` vs o lock correspondente.

**6.4 env_b5 (py3.7 EXATO, linux-64 nativo — SEM Rosetta/CONDA_SUBDIR na VM):**
```bash
$TOOLS/bin/micromamba create -y -p ~/python_venvs/env_b5 -c conda-forge python=3.7 pip
~/python_venvs/env_b5/bin/pip install "scikit-learn==0.21.3" "desdeo-problem==0.14.0" \
  "desdeo-tools==0.2.6" statsmodels matplotlib pyDOE "pandas==1.3.5" numpy \
  "pyarrow==12.0.1" "pymoo==0.6.1.2" "plotly==4.14.3" graphviz typing_extensions
```
⚠ NÃO instalar: `desdeo-emo` (é VENDORIZADO no repo — pin cravado no gate R3.2),
`pygmo` (fica STUB no runner). `pandas==1.3.5` é o pin RATIFICADO (DI-28 — o 0.25.3
antigo quebra o DataProblem; se algum doc antigo disser 0.25.3, vale o lock).

**6.5 env_c311 (py3.8 EXATO — ⚠ NUNCA 3.9: o GPy 1.9.9 usa `tp_print`, removido no 3.9,
e o build falha em QUALQUER plataforma):**
```bash
$TOOLS/bin/micromamba create -y -p ~/python_venvs/env_c311 -c conda-forge python=3.8 pip
~/python_venvs/env_c311/bin/pip install "numpy==1.20.2" "scikit-learn==1.1.2" scipy pyDOE \
  "plotly==4.14.3" "plotly-express==0.4.1" matplotlib statsmodels pandas "Pillow<10" \
  pyarrow graphviz "pymoo==0.6.1.2"
~/python_venvs/env_c311/bin/pip install --no-build-isolation "GPy~=1.9.9"   # COMPILA (usa o gcc temporário)
```
⚠ `Pillow<10` é obrigatório (≥10 exige numpy≥1.21; o pin é 1.20.2). `optproblems` NÃO se
instala (o runner tem stub em runtime). Rodar sempre com `MPLBACKEND=Agg`.

**6.6 Credencial GCP:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS=$HOME/sa.json   # ou use o SA nativo da VM
# persistir no ~/.bashrc
```

**6.7 FECHAMENTO da VM (obrigatório — D-16c):**
```bash
sudo apt remove -y build-essential && sudo apt autoremove -y
gcc --version 2>&1 | head -1    # esperado: "command not found"
```

**6.8 Smoke de aceitação de cada VM** (o último item só APÓS o git pull pós-T7/T6):
```bash
cd ~/ua-dd-saea && PY=~/python_venvs/env_main/bin/python
$PY -m unittest discover -s tests          # Ran >= 328 ... OK
$PY scripts/preflight.py                   # exit 0
$PY scripts/naoperturbacao.py --all        # 53 verdes
# provas por-env:
~/python_venvs/env_b5/bin/python -c "import sklearn, desdeo_problem; print('b5 ok')"
MPLBACKEND=Agg ~/python_venvs/env_c311/bin/python -c "import GPy, numpy as np; m=GPy.models.GPRegression(np.random.rand(20,2), np.random.rand(20,1)); m.optimize(max_iters=5); print('c311 ok')"
~/python_venvs/env_e81_qpots/bin/python -c "import torch, botorch; print('e81 ok', torch.__version__)"
# célula REAL + bucket + gate (APÓS o pull pós-T7/T6):
$PY experiments.py --exp off --algorithms moead_media --problems MMF1 --seeds 42 --enable-bucket
$PY scripts/portao.py --exp off --alg moead_media --problema MMF1 --semente 42   # VERDE
```

## 7 · Armadilhas conhecidas (do histórico do projeto — cheque antes de debugar do zero)

- **pyenv sem build deps** → o `pyenv install` falha com erros de ssl/zlib: instale as
  libs do §6.1 primeiro.
- **`python` vs `python3`**: nos Macs o binário é `python3`; nas VMs após o pyenv, use
  sempre caminhos ABSOLUTOS dos venvs (o shell do usuário pode não ter o pyenv no PATH).
- **zsh não faz word-splitting** de variáveis (`$var` com espaços NÃO vira 2 args).
- **MATLAB em background**: sempre `> log 2>&1`, nunca pipe (trava).
- **Wheels linux**: os locks foram validados no Mac; em linux-64 as versões PINADAS têm
  manylinux wheel (cp37/cp38 antigos) — se um pip resolver DIFERENTE do lock, PARE e
  reporte a diferença exata (não aceite upgrade silencioso).
- **A suíte é `unittest`**, não pytest: `python -m unittest discover -s tests`.
- **Espaço em disco**: a rodada-42 gera dezenas de GB na ③ dos online pesados — o
  `--enable-bucket` + poda local (D54) é o plano; monitore `df -h`.

## 8 · O checklist que você mantém (atualize a cada turno da conversa)

```
MAC A : [ ] suíte OK  [ ] preflight  [ ] naoperturbacao  [ ] gcloud auth
MAC B : [ ] MATLAB+toolboxes=lock  [ ] repo  [ ] dados  [ ] ponte 3.11.9-shared
        [ ] env_main  [ ] smoke nsga2/MMF1/42 + portão  [ ] gcloud auth
VM-1  : [ ] base+pyenv+micromamba  [ ] repo+dados  [ ] env_main  [ ] env_e81
        [ ] env_b5  [ ] env_c311(GPy)  [ ] credencial  [ ] gcc REMOVIDO
        [ ] suíte/preflight/provas  [ ] (pós-T7/T6) pull + célula real + portão
VM-2  : [ idem VM-1 ]
```

## 9 · Protocolo de interação com o usuário

1. UM passo por vez; espere o output colado; valide contra o esperado ANTES de avançar.
2. Output divergente: diagnostique com o §7 primeiro; se for pin/versão, aplique a regra
   D80 (pare e reporte a divergência exata para levar à torre).
3. Ao fechar cada máquina, imprima o checklist §8 atualizado.
4. NUNCA sugira `git push`, mudanças de pins, ou edição de código do repo — qualquer
   sintoma de bug de código vai para a torre, não se conserta aqui.
```
