# RUNBOOK — Validação definitiva SEMENTE-42 (F1 provisionamento → F5 fidelidade)

> **O que é.** O tutorial passo-a-passo para provisionar as 3 máquinas, migrar o código,
> disparar a rodada semente-42 (a validação definitiva de fidelidade, que é TAMBÉM o piloto
> de timing do M7) e verificar tudo. Escrito pela torre em 2026-07-23 (DI-32; contexto no
> REGISTRO PARTES A19-A20). **Regra de ouro: cada run = 1 core (D79); a seed 42 é uma das
> 30 oficiais — tudo que rodar aqui CONTA para a bateria (a esteira `is_run_done` pula
> células prontas no M8/M9).**

## §0 · O plano numa página

| Máquina | Papel | Configs |
|---|---|---|
| **Mac A** (o atual) | **TODOS os 12 MATLAB** + e103 + torre/gates | 12 online MATLAB + e103 (off+sweep; e103 SERIAL — ponte InProcess falha em workers parfor) |
| **VM-1 GCP** `v5-mestrado` (32 vCPU/64 GB) | Python pesado | 5 online (c262/c154/c122/c149/e81) + batch q=10 (as células caras de 2000 infills) |
| **VM-2 GCP** `mestrado-v6` (32 vCPU/64 GB) | Python offline | 4 offline (b5r/b5m/c311/moead_media) + treed_media + sweeps Python |

**⚠ Mac B está FORA da rodada-42** (High Sierra — F1 falhou; §2 abaixo fica como
referência histórica/M8). A trilha alternativa de scale-out MATLAB é a **VM Azure
F64s_v2 (M8; pin R2025a OBRIGATÓRIO — o template default é R2025b, problema D80)**.

**⚠ DECISÃO DO AUTOR (DI-33b): a rodada-42 é UMA SÓ, no estado DEFINITIVO do repo** —
dispara-se TUDO (~695 células) somente APÓS T7+T6+T8+T9 e a validação final da torre
(DI-36/DI-37 — FECHADAS 2026-07-25; fila decisória VAZIA). Nada de lote parcial
(evita duas gerações de código no mesmo dataset).

Fluxo: **F1** provisionar (este runbook) → **F2** smoke de portabilidade → **F3** disparo
da rodada-42 → **F4** `portao.py --varredura` verde nas 3 → **F5** workflows Fable de
fidelidade (torre) → **F6** veredito D97 do autor → M8/M9 (expandir p/ 30 sementes).

---

## §1 · Máquina A — o Mac atual (JÁ provisionado; só verificar, ~10 min)

```bash
cd /Users/gmello/Documents/python_repos/mestrado/ua-dd-saea
PY=/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python
$PY -m unittest discover -s tests            # esperado: Ran 587 · OK  [T11]
$PY scripts/preflight.py                     # exit 0 (lacres/âncoras/artefatos
                                             #  + manifesto forasteiro, B-12)
$PY scripts/naoperturbacao.py --all          # 53 verdes
$PY scripts/gates_proveniencia.py --varredura --historico   # G-1..G-4+B-15+G-7
```

### ⚠ ANTES DE QUALQUER DISPARO — crave o `campanha_id` [B-03, T11-G3]

```bash
export UA_DD_SAEA_CAMPANHA_ID="$(git rev-parse --short=12 HEAD)_$(date +%F)"
```

**Em TODAS as máquinas, com o MESMO valor**, e uma vez só no início da campanha
(não por lote). O `is_run_done` passou a exigir este carimbo: manifesto sem ele
(schema v1) ou de campanha anterior conta como NÃO-PRONTO — é o que impede as
células stale de semente 0 (b1 DTLZ2/ZDT1, c238 ZDT1, c262 ZDT1, c154 DTLZ2)
entrarem como resultado oficial. Sem a env, o default é `{commit12}_{data UTC}`
e ele **muda à meia-noite** — no dia 2 o resume re-rodaria tudo. O despachante
imprime o id em uso no arranque do grid: confira que é o mesmo nas 4 máquinas.
Credencial do bucket (para o sync pós-hoc dos runs MATLAB — §5.3):
```bash
gcloud auth application-default login        # ou GOOGLE_APPLICATION_CREDENTIALS=<sa.json>
```

## §2 · Máquina B — o Mac do pai (MATLAB) — **⚠ FORA da rodada-42 (F1 falhou: High Sierra); seção mantida como referência p/ M8/Azure**

**2.1 MATLAB.** Instalar **R2025a Update 1** com as toolboxes EXATAS do lock
(`requirements/locks/env_matlab_ver.lock.txt` — confira com `matlab -batch ver`).
Divergência de versão/toolbox = pare e confira com o autor (D80).

**2.2 Código.** O repo NÃO tem remoto público (regra: nunca push). Migre por clone local:
```bash
# no Mac B (mesma rede; Compartilhamento Remoto/ssh ligado no Mac A):
git clone gmello@<IP-do-Mac-A>:/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea ua-dd-saea
# alternativa sem rede: no Mac A `git bundle create uadd.bundle --all` → copiar → `git clone uadd.bundle`
```

**2.3 Artefatos de dados** — ⚠ correção da auditoria DI-38: `data/doe/` + `data/datasets/`
estão **RASTREADOS no git** (~190 MB; `.gitignore` tem `!data/doe/`/`!data/datasets/`) —
**o clone JÁ os leva**. O rsync abaixo é só FALLBACK/verificação (bit-idêntico):
```bash
rsync -av gmello@<IP-do-Mac-A>:/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe/ data/doe/
rsync -av gmello@<IP-do-Mac-A>:/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/datasets/ data/datasets/
```
(A verificação em qualquer caso é a mesma: preflight + CP-init no smoke.)

**2.4 A ponte MATLAB↔Python** (`env_bridge` — PROVISIONAMENTO.md §5):
```bash
brew install pyenv   # se não houver
PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.11.9
~/.pyenv/versions/3.11.9/bin/python -m venv ~/ponte_teste
~/ponte_teste/bin/pip install -r requirements/env_bridge.txt
# no MATLAB, 1×:  pyenv('Version','~/ponte_teste/bin/python','ExecutionMode','InProcess')
# smoke:          py.numpy.array([1,2,3]).sum()  % = 6
```

**2.5 Smoke de aceitação do Mac B** (o critério do F2 — ver §6):
```bash
/Applications/MATLAB_R2025a.app/bin/matlab -batch "experiments('algorithms',{'nsga2'},'problems',{'MMF1'},'seeds',42)" > /tmp/smoke_b.log 2>&1
# valida com o leitor Python (instale env_main mínimo OU rode o portão a partir do Mac A
# apontando --data-root para uma cópia):
```
No Mac B recomendo provisionar também o **env_main** (PROVISIONAMENTO §1) para rodar
`preflight`/`portao.py` localmente — 10 min, e o Mac B ganha autonomia de verificação.

## §3 · Máquina C — a VM GCP (todo o Python)

**3.1 Criar a VM.** Ubuntu 22.04 LTS · **32 vCPU / 64 GB** (o que você propôs serve com
folga; e7 usa ~3,3 GB/run — 20 paralelos = ~66 GB, então com 64 GB limite e7 a ~12
paralelos) · disco **≥ 200 GB SSD** · service account com `roles/storage.objectAdmin`
no bucket `mestrado_experiments`.

**3.2 Base do sistema** (⚠ D-16c: a VM final fica SEM toolchain C++ — o gcc entra só
temporariamente para compilar o GPy, e sai):
```bash
sudo apt update && sudo apt install -y git curl rsync   # SEM build-essential por padrão
# pyenv (py 3.11.9 p/ env_main e env_e81):
curl https://pyenv.run | bash    # + PATH no ~/.bashrc conforme instruções
pyenv install 3.11.9
# micromamba (envs x86_64 — na VM é linux-64 NATIVO, sem Rosetta):
TOOLS=$HOME/python_venvs/_micromamba; mkdir -p $TOOLS/bin $TOOLS/root && cd $TOOLS
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj bin/micromamba
```

**3.3 Código + dados** (doe/datasets vêm NO CLONE — rastreados no git; rsync = fallback):
```bash
git clone <bundle-ou-ssh-do-Mac-A> ~/ua-dd-saea && cd ~/ua-dd-saea
# fallback/verificação apenas (bit-idêntico):
rsync -av gmello@<IP-Mac-A>:.../data/doe/ data/doe/ && rsync -av gmello@<IP-Mac-A>:.../data/datasets/ data/datasets/
```

**3.4 Os 4 envs Python** — siga `requirements/PROVISIONAMENTO.md` §1-§4 trocando
`CONDA_SUBDIR=osx-64` por nada (linux-64 nativo) e conferindo cada um contra
`requirements/locks/*.lock.txt`:
```bash
# env_main (§1) e env_e81 (§4): venv do pyenv 3.11.9 + pip install -r requirements/env_*.txt
# env_b5 (§2): micromamba python=3.7 + os pins (pandas 1.3.5! pymoo 0.6.1.2! — o lock manda)
# env_c311 (§3): micromamba python=3.8 EXATO (NUNCA 3.9 — GPy 1.9.9/tp_print) + pins:
sudo apt install -y build-essential          # TEMPORÁRIO — só p/ compilar o GPy
<env_c311>/bin/pip install --no-build-isolation "GPy~=1.9.9"
sudo apt remove -y build-essential && sudo apt autoremove -y   # D-16c: sai da VM final
```

**3.5 Credencial + smoke de 10 min:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS=$HOME/sa.json     # (ou o SA da própria VM)
PY=<env_main>/bin/python
$PY -m unittest discover -s tests && $PY scripts/preflight.py && $PY scripts/naoperturbacao.py --all
# provas por-env do PROVISIONAMENTO §2/§3/§4 (load_sonda, GPy fit, BoTorch fit)
$PY experiments.py --exp off --algorithms moead_media --problems MMF1 --seeds 42 --enable-bucket
$PY scripts/portao.py --exp off --alg moead_media --problema MMF1 --semente 42
```
O último par é o teste-fim-a-fim: roda 1 célula REAL da rodada-42 na VM, espelha no
bucket e gateia. Verde = a VM está pronta.

## §4 · A rodada-42 — quem dispara o quê

**Células (todas com `--seeds 42`):** main 425 (12 MATLAB×25 + 5 Python×25) · off 125
(e103×25 no Mac + 4 Python×25) · **sweep 120** (b5r 20 · b5m 20 · c311 30 · moead_media 20
· treed_media 10 Python + e103 20 MATLAB; tokens `sweep-{small,medium,big}-{lhs,mvns}`,
grid DI-35) · **batch 25** (c149/c262/e81/c154/sobol_batch × 5 problemas).
**Total: 695 células** (345 MATLAB + 350 Python — censo do `runs_matrix.csv`, seed 42).
✅ Pré-requisitos T6/T7/T8/T9 IMPLEMENTADOS E VALIDADOS (REGISTRO A21–A25); a fila
decisória está vazia (DI-37) — o disparo é liberado pelo push+tag do autor + F2.

```bash
# VM (tudo Python; ~6-10 paralelos; e7 não se aplica — é MATLAB):
$PY experiments.py --exp main --algorithms c262 c154 c122 c149 e81 --seeds 42 --n-jobs 8 --enable-bucket
$PY experiments.py --exp off  --algorithms b5r b5m c311 moead_media --seeds 42 --n-jobs 8 --enable-bucket
# batch q=10 (VM-1; as 5 células c154 SEGURAM 12h cada e morrem no teto POR DESENHO — §7):
$PY experiments.py --exp batch --algorithms c149 c262 e81 sobol_batch --seeds 42 --n-jobs 8 --enable-bucket --problems MMF16_20 ZDT4 DTLZ2 WFG9 ZDT1
# ⚠ DI-40: c154 FORA do batch · DI-42: SEM --problems o default são os 25 problemas
#   (125 células em vez de 25!) — o batch/sweep rodam SÓ nos 5 problemas do sub-estudo.
# sweeps (após o smoke do §6.3): 1 comando por token — rosters por tier (DI-35.4):
#   small/medium → b5r b5m c311 moead_media (Python) + e103 (MATLAB, Mac A — comandos abaixo)
#   big → c311 treed_media (SÓ os treed)
$PY experiments.py --exp sweep-small-mvns --algorithms b5r b5m c311 moead_media --seeds 42 --n-jobs 8 --enable-bucket --problems MMF16_20 ZDT4 DTLZ2 WFG9 ZDT1
$PY experiments.py --exp sweep-big-lhs    --algorithms c311 treed_media        --seeds 42 --n-jobs 8 --enable-bucket --problems MMF16_20 ZDT4 DTLZ2 WFG9 ZDT1

# Mac A — TODOS os 12 MATLAB (Mac B está fora; pode dividir em 2 lotes p/ log):
matlab -batch "experiments('algorithms',{'b1','b3','b4','e7','c217','c141'},'seeds',42,'parallel',false)" > /tmp/lote_A.log 2>&1
matlab -batch "experiments('algorithms',{'e74','c238','nsga2','nsga3','moead','smsemoa'},'seeds',42,'parallel',false)" > /tmp/lote_B.log 2>&1
# e103 (offline MATLAB, Mac A — SERIAL) + depois a ⑦ via final_eval (env_main):
matlab -batch "experiments('algorithms',{'e103'},'exp','off','seeds',42,'parallel',false)" > /tmp/e103.log 2>&1
# e103 no SWEEP (small/medium apenas — big é só c311/treed_media), 1 comando por token:
matlab -batch "experiments('algorithms',{'e103'},'exp','sweep-small-lhs','seeds',42,'parallel',false)"   > /tmp/e103_sw_sl.log 2>&1
matlab -batch "experiments('algorithms',{'e103'},'exp','sweep-small-mvns','seeds',42,'parallel',false)"  > /tmp/e103_sw_sm.log 2>&1
matlab -batch "experiments('algorithms',{'e103'},'exp','sweep-medium-lhs','seeds',42,'parallel',false)"  > /tmp/e103_sw_ml.log 2>&1
matlab -batch "experiments('algorithms',{'e103'},'exp','sweep-medium-mvns','seeds',42,'parallel',false)" > /tmp/e103_sw_mm.log 2>&1
```
Monitorar: `scripts/progress.py --watch` · Gatear ao fim: `scripts/portao.py --varredura`.

## §5 · Bucket

1. **Python: nativo.** `--enable-bucket` liga o dual-write §17.7 — o `mirror_run` sobe
   TODAS as camadas do run (①②③④⑦ + manifesto + jsonl). Para os 5 online pesados
   (c262/c154/c122/c149/e81) a ③ é `bucket-only` (D54): pode ser podada localmente após
   upload confirmado — é o que segura o disco da VM.
2. **MATLAB: SEM código novo.** O espelho é pós-hoc, do lado Python, com o MESMO
   `mirror_run` (ele enumera os arquivos pela convenção de nomes — funciona para
   qualquer run, MATLAB incluso). Loop de sync no Mac (a cada 30 min, ou ao fim do lote):
```bash
$PY - <<'EOF'
from src import gcs, manifest
import glob, os, json
for man in glob.glob('data/experiments/*/*/*.manifest.json'):
    if '__final' in man: continue
    m = json.load(open(man))
    if m.get('status') in ('ok', 'retried_ok'):
        print(m['alg'], m['problema'], m['semente'],
              gcs.mirror_run(m['exp'], m['alg'], m['problema'], m['semente']))
EOF
```
3. Validar 1× com credencial real: `gcs.blob_exists` de um blob subido (o accept R2-00
   tem o smoke GCS: `accept.py R2-00 --gcs-smoke`).

## §6 · Critérios de aceite do F2 (portabilidade) — LEIA ANTES de comparar máquinas

1. **O que TEM de bater bit-a-bit entre máquinas:** os HASHES dos artefatos (CP-init:
   `x_hash`/`f_hash` do manifesto ≡ sidecar do DoE/dataset). O gate confere.
2. **O que NÃO se exige bit-a-bit entre máquinas:** floats da ③/⑦ (BLAS arm64 vs linux
   ≠ ordem de redução). O protocolo garante determinismo bit-a-bit NA MESMA máquina
   (gates de determinismo), e correção por GATES em qualquer máquina.
3. **Critério de aceite por máquina nova:** suíte OK + preflight 0 + 3 células reais
   (1 por stack presente) com `portao.py` VERDE. Sweep: 1 smoke por token antes das 90
   (o plumbing existe e está testado em unidade, mas NUNCA rodou run real — em especial
   `sweep-big-*` do c311, ramo `_build_surrogates`, e o sweep do e103 no MATLAB).

## §6-bis · CORREÇÕES DE CAMPO do F1 (o que o provisionamento real ensinou — handoff v4)

1. **O remoto EXISTE** (`github.com/melloguin/ua-dd-saea`, público): migração = clone do
   origin + **`git checkout experiment/definitive_algorythms`** (o clone cai em `main`).
   ssh/bundle viram fallback. `git push` segue proibido nas máquinas.
2. **Os dados (`doe`/`datasets`/`sonda`) são RASTREADOS** — vêm no clone; os rsync do
   §5.3/§6.2 caem.
3. **Envs SEMPRE dos LOCKS** (nunca das intenções): env_main/env_e81 direto do lock;
   **env_b5 = lock + `--no-deps`** (aceite: pip check com EXATAMENTE as 2 reclamações
   desdeo — DI-28); **env_c311 = lock-sem-GPy → `GPy==1.9.9 --no-build-isolation`**
   (pip check LIMPO). Critério Q2 em linux: extras permitidos SÓ da família
   `{nvidia-*, triton, cuda-*}` (o wheel linux do torch as traz; versões são função
   do torch).
4. **D-16c em Workbench:** `sudo apt-get remove -y --auto-remove gcc` (não
   build-essential), prova `gcc/cc → command not found`; `gcc-12` residual documentado.
5. **`naoperturbacao` = N/A em máquina nova** (gate de máquina-com-histórico; baselines
   só existem no Mac A). Critério de suíte: `Ran ≥ 328 OK` + 0 FAIL/ERROR — nunca
   igualdade de contagem entre máquinas.
6. Vertex: conferir QUOTA de CPUs antes de criar; idle-shutdown E auto-upgrade OFF;
   IAM de bucket ao SA da instância (cross-projeto ok; sem sa.json); ignorar o conda
   da imagem (tudo por caminho absoluto).
7. **Nota MATLAB (achado DI-34):** a ponte Python InProcess pode falhar dentro de
   workers do parfor — o e103 (e worker dedicado em geral) deve rodar SERIAL no lote;
   conferir no disparo do Mac (o run direto `experiment(...)` está provado).

## §7 · Avisos de custo e ordem de disparo

- **Células caras conhecidas (1 core cada):** c238/ZDT1 ~3h55 · c262/ZDT1 ~4h11 ·
  c149/ZDT1 ~3h22 · e81/ZDT1 ~2h · e7/ZDT1 ~72min (RAM 3,3 GB) · b3/ZDT1 ~26min.
  ⚠ Os MATLAB NÃO têm teto de wall-clock (lacuna aceita — todos ≪ 12h; rede = D60).
- **⚠ c154/c262 sob o teto 12h — O RITO MUDOU ⟦DI-43+DI-44, aplicado no T11-G5⟧:**
  **TRUNCAMENTO-COM-DADO.** O teto dispara **só por RELÓGIO** (`elapsed`), o run vai
  até as 12h e fecha `failed`/`teto_wall` **GRAVANDO as camadas parciais** — "curva
  parcial é o dado" (DI-37.1). A **projeção não aborta mais**: virou
  `wall_projection_warning` (1 linha por run), porque ela é a estimativa que EXPLICA
  por que a célula não fecha, não motivo para matá-la.
  *Como era antes (e por que mudou):* o aborto por projeção matava o run antes de
  qualquer parquet existir — medido na s42, **0,87–2,99 h por célula (média 1,47 h)**
  queimadas para ZERO dado. ⚠ O "~minutos–1h" das versões antigas e o "~6,3 h" da
  DI-40 são os DOIS superados: 1,47 h é o número medido.
  Afeta as mesmas células (**c154 main D≥12**, as 5 de **c154-batch**), mas agora
  elas ENTREGAM curva parcial. O portão segue reportando ⚪ aborto-sancionado, e
  **agora também roda os gates de PROVENIÊNCIA nelas** (elas têm dado). **Continua
  valendo NÃO re-disparar** — `is_run_done` as lê como não-prontas e o re-disparo
  re-queima as 12h.
  Os runners Python também gravam **checkpoint atômico a cada 25 iterações OU 30 min**
  (DI-43): uma morte matada (spot revogada, OOM, SIGKILL) deixa camadas parciais
  legíveis + ⑤ coerente. ⚠ Nesse ⑤, `fe_final` é **PISO** das camadas.
- **Batch q=10 (DI-37):** c262 ≈ 2,2h/célula (receita cheia, sem knob) ·
  c149/e81/sobol_batch baratos · c154 = bullet acima.
- **c311 sweep-big (50k)**: âncora de build ~32s, mas fase final + sonda em n=50k é
  terreno novo — rode o smoke primeiro e olhe o wall antes das demais células big.
- Ordem recomendada: disparar PRIMEIRO as células caras (elas dominam o wall-clock;
  o resto preenche os cores restantes). A rodada inteira nas 3 máquinas ≈ **1–2 dias**.
- Os walls que saírem daqui SÃO o M7: `progress.py --tabela` ao final = a tabela de
  dimensionamento das 30 sementes (decisões A3/A5 com dado).

---

## §X · SMOKE × CAMPANHA — a distinção que NÃO existia aqui

> **Por que esta seção existe.** Em 2026-07-30 um agente rodou os smokes MATLAB
> copiando os comandos do §1 deste RUNBOOK e obteve `skipped=6/4/1/1`: **zero
> células executadas**. Os comandos estavam CERTOS — para o que o §1 é, que é o
> disparo da campanha REAL, em `data/`. Usados como smoke, apontaram para
> produção, onde aquelas células já existiam da rodada-42, e a esteira
> idempotente pulou todas. Ninguém percebeu até alguém olhar o log.

**A armadilha:** `dataRoot` (MATLAB) e `data_root` (Python) **têm produção como
default nos DOIS stacks**.

```matlab
p.addParameter('dataRoot', 'data');        % experiments.m
```
```python
data_root: str = naming.DEFAULT_DATA_ROOT  # runners Python
```

### Invocação de CAMPANHA (escreve em `data/` — é o desejado)
```bash
$PY experiments.py --exp main --algorithms c122 --seeds 42
matlab -batch "experiments('algorithms',{'b1'},'seeds',42)"
```

### Invocação de SMOKE (NUNCA toca produção)
```bash
SMOKE=/tmp/smoke_$(date +%H%M%S)
mkdir -p "$SMOKE/experiments"
for e in doe datasets sonda; do ln -s "$PWD/data/$e" "$SMOKE/$e"; done   # entradas READ-ONLY

matlab -batch "experiments('algorithms',{'b1'},'problems',{'MMF1'},'seeds',42,'parallel',false,'dataRoot','$SMOKE')"
$PY -c "import sys;sys.path.insert(0,'.');from src import experiment as a;a.run('c122','MMF1',0,exp='main',data_root='$SMOKE')"
```

**Como saber que deu certo:** o placar tem de dizer `ok=N skipped=0`. Se vier
`skipped`, o `dataRoot` aponta para um lugar que já tem aquelas células.

⚠ **`'parallel',false` no MATLAB:** o `e103` NÃO funciona em worker `parfor` (a
ponte `pyenv` InProcess falha). Paralelize entre TERMINAIS, não dentro do
`experiments.m`.

## §X.1 · `UA_DD_SAEA_CAMPANHA_ID` — o mesmo id nas 4 máquinas

O `campanha_id` (B-03) carimba cada ⑤ e é o que o `is_run_done` exige para não
reaproveitar célula de outra campanha. **Ele é OPCIONAL**: sem a variável, o
`manifest.py` deriva `<commit-curto>_<data>` (ex.: `25e95b464a67_2026-07-30`).

O que a variável resolve é ter **um id ÚNICO e IGUAL nas 4 máquinas** para a
mesma campanha — sem ela, cada máquina deriva o seu e as células ficam com ids
diferentes, o que quebra o `is_run_done` cruzado.

**Antes do disparo, em CADA máquina (Mac A, VM-1, VM-2, VM-3):**
```bash
export UA_DD_SAEA_CAMPANHA_ID="m8-$(git -C <repo> rev-parse --short HEAD)"
echo "$UA_DD_SAEA_CAMPANHA_ID"          # confira que as 4 imprimem o MESMO texto
```
Para persistir na sessão da VM, ponha a linha no `~/.bashrc` da máquina.

---

## §Y · `--n-jobs` POR MÁQUINA — a RAM é o gargalo, não a CPU

> **Medido em 2026-07-30/31.** Dois pontos, e **os DOIS são PISO** — nenhum dos
> runs chegou ao fim:
>
> | config | pico observado | contexto |
> |---|---|---|
> | `batch/c262/ZDT4` q=10 | **1.205 MB** | probe com RSS amostrado a cada 2 s (1.306 amostras); morto sob pressão de memória a ~1/3 do caminho |
> | `main/c154/DTLZ2` D=12 | **2,2 GB** | observado por `ps` durante as 6 h até bater o teto |
>
> ⚠ **Por que são pisos, e por que isso importa.** Em métodos baseados em GP a
> memória cresce com o número de observações (a matriz de covariância é O(n²)).
> O `c262-batch` tem 2.000 infills e foi interrompido cedo; o `c154` parou no
> teto com 282 de 371 FEs. **O consumo real ao fim do run é maior que ambos.**

### O teto e a folga são coisas SEPARADAS

**Teto por job: 4 GB** (~3,3× o piso do c262, ~1,8× o pico do c154).
**`n-jobs` calculado sobre 80% da RAM** — os 20% restantes são do sistema
operacional, do cache de página e do próprio despachante.

Embutir a margem inflando o teto por-job (era 6 GB) e depois dividir a RAM
INTEIRA esconde a margem no lugar errado: fica impossível saber quanto de folga
existe de fato.

| máquina | vCPU | RAM | 80% utilizável | **`--n-jobs`** | gargalo |
|---|---|---|---|---|---|
| **Mac A** (torre/gates/MATLAB) | 8 | 16 GB | 12,8 GB | **3** | RAM |
| **VM-1 GCP** `v5-mestrado` | 32 | 64 GB | 51,2 GB | **12** | RAM |
| **VM-2 GCP** `mestrado-v6` | 32 | 64 GB | 51,2 GB | **12** | RAM |
| **VM-3** | 16 | 32 GB | 25,6 GB | **6** | RAM |

```bash
# VM-1 — Python pesado (5 online + batch q=10)
$PY experiments.py --exp batch --algorithms c149 c262 e81 sobol_batch --seeds 42 \
    --n-jobs 12 --enable-bucket --problems MMF16_20 ZDT4 DTLZ2 WFG9 ZDT1
```

### 🚨 REGRA DE ARRANQUE — não confie neste número de cara

**O primeiro lote de produção roda com METADE do `--n-jobs` da tabela.** Observe
o pico real por ~1 h (`ps -eo rss,command | grep experiments`) e só então suba.

Nenhum `n-jobs` derivado de **duas medições incompletas** merece confiança cega,
e o custo de errar para cima não é lentidão: é o OS matando células de
madrugada, sem aviso e sem dado. Foi exatamente o que aconteceu com o probe
desta campanha — **duas vezes, deixando ZERO resultado** — até ele passar a
gravar o pico a cada novo máximo.

⚠ **O `c154` conta como 1 job INTEIRO e não desconte:** sozinho chegou a 2,2 GB
e segurou 6 h até o teto.

**Por que a CPU não manda.** Todo run é pinado em **1 thread** (D79:
`OMP_NUM_THREADS=1` e afins), então em tese caberiam tantos jobs quantos vCPU —
16 no VM-1 com 4 GB. Mas com a folga de SO a memória esgota antes, **em toda
máquina do parque**.
