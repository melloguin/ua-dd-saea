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
| **Mac A** (o atual) | MATLAB metade 1 + torre/gates | 6 dos 12 online MATLAB + e103 (off+sweep) |
| **Mac B** (do pai) | MATLAB metade 2 | os outros 6 online MATLAB |
| **VM-1 GCP** (32 vCPU/64 GB) | Python pesado | 5 online (c262/c154/c122/c149/e81) + batch q=10 (as células caras de 2000 infills) |
| **VM-2 GCP** (32 vCPU/64 GB) | Python offline | 4 offline (b5r/b5m/c311/moead_media) + sweeps Python |

**⚠ DECISÃO DO AUTOR (DI-33b): a rodada-42 é UMA SÓ, no estado DEFINITIVO do repo** —
dispara-se TUDO (665 células) somente APÓS T7+T6 implementados e a validação final da
torre. Nada de lote parcial pré-T6/T7 (evita duas gerações de código no mesmo dataset).
O provisionamento (F1, este runbook) corre EM PARALELO à sessão T7+T6.

Fluxo: **F1** provisionar (este runbook) → **F2** smoke de portabilidade → **F3** disparo
da rodada-42 → **F4** `portao.py --varredura` verde nas 3 → **F5** workflows Fable de
fidelidade (torre) → **F6** veredito D97 do autor → M8/M9 (expandir p/ 30 sementes).

---

## §1 · Máquina A — o Mac atual (JÁ provisionado; só verificar, ~10 min)

```bash
cd /Users/gmello/Documents/python_repos/mestrado/ua-dd-saea
PY=/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python
$PY -m unittest discover -s tests            # esperado: Ran 328 · OK
$PY scripts/preflight.py                     # exit 0 (lacres/âncoras/artefatos)
$PY scripts/naoperturbacao.py --all          # 53 verdes
```
Credencial do bucket (para o sync pós-hoc dos runs MATLAB — §5.3):
```bash
gcloud auth application-default login        # ou GOOGLE_APPLICATION_CREDENTIALS=<sa.json>
```

## §2 · Máquina B — o Mac do pai (MATLAB)

**2.1 MATLAB.** Instalar **R2025a Update 1** com as toolboxes EXATAS do lock
(`requirements/locks/env_matlab_ver.lock.txt` — confira com `matlab -batch ver`).
Divergência de versão/toolbox = pare e confira com o autor (D80).

**2.2 Código.** O repo NÃO tem remoto público (regra: nunca push). Migre por clone local:
```bash
# no Mac B (mesma rede; Compartilhamento Remoto/ssh ligado no Mac A):
git clone gmello@<IP-do-Mac-A>:/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea ua-dd-saea
# alternativa sem rede: no Mac A `git bundle create uadd.bundle --all` → copiar → `git clone uadd.bundle`
```

**2.3 Artefatos de dados** (`data/doe/` + `data/datasets/` são gitignorados — ~100 MB):
```bash
rsync -av gmello@<IP-do-Mac-A>:/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/doe/ data/doe/
rsync -av gmello@<IP-do-Mac-A>:/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/data/datasets/ data/datasets/
```
(Opção B: regenerar — é determinístico — mas o rsync é bit-idêntico por construção e mais
rápido; a verificação é a mesma: preflight + CP-init no smoke.)

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

**3.3 Código + dados:**
```bash
git clone <bundle-ou-ssh-do-Mac-A> ~/ua-dd-saea && cd ~/ua-dd-saea
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
(e103×25 no Mac + 4 Python×25) · sweep 90 (b5r/b5m/c311 Python + e103 MATLAB; tokens
`sweep-{small,medium,big}-{lhs,mvns}`) · **batch 25 (c149/c262/e81/c154/sobol_batch ×
5 problemas — INCLUÍDO por decisão do autor, DI-33; exige o cartão T6 ANTES)**.
**Total: 665 células.** ⚠ Dois PRÉ-REQUISITOS de implementação antes do disparo
completo: **T6** (batch q=10 — ver REGISTRO A21) e **T7** (o "fio do sweep": os
runners offline ainda não derivam tier/dist do token `sweep-*` — ver REGISTRO A21;
sem o T7, um run de sweep rodaria SILENCIOSAMENTE sobre o dataset small errado).
main+off (550 células) podem disparar IMEDIATAMENTE — não dependem de T6/T7.

```bash
# VM (tudo Python; ~6-10 paralelos; e7 não se aplica — é MATLAB):
$PY experiments.py --exp main --algorithms c262 c154 c122 c149 e81 --seeds 42 --n-jobs 8 --enable-bucket
$PY experiments.py --exp off  --algorithms b5r b5m c311 moead_media --seeds 42 --n-jobs 8 --enable-bucket
# sweeps (após o smoke do §6.3): 1 comando por token, ex.:
$PY experiments.py --exp sweep-small-mvns --algorithms b5r b5m c311 --seeds 42 --n-jobs 8 --enable-bucket

# Mac A (metade 1) e Mac B (metade 2) — dividir a lista de 12:
matlab -batch "experiments('algorithms',{'b1','b3','b4','e7','c217','c141'},'seeds',42)" > /tmp/lote_A.log 2>&1
matlab -batch "experiments('algorithms',{'e74','c238','nsga2','nsga3','moead','smsemoa'},'seeds',42)" > /tmp/lote_B.log 2>&1
# e103 (offline MATLAB, Mac A) + depois a ⑦ via final_eval (env_main):
matlab -batch "experiments('algorithms',{'e103'},'exp','off','seeds',42)" > /tmp/e103.log 2>&1
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
  c149/ZDT1 ~3h22 · e81/ZDT1 ~2h · e7/ZDT1 ~72min (RAM 3,3 GB) · b3/ZDT1 ~26min ·
  **c154/ZDT1 = estourou o teto de 8h → DECISÃO A3 ANTES do disparo** (manter teto e
  aceitar `failed`=dado honesto, ou excluir a célula da rodada-42).
- **c311 sweep-big (50k)**: âncora de build ~32s, mas fase final + sonda em n=50k é
  terreno novo — rode o smoke primeiro e olhe o wall antes das demais células big.
- Ordem recomendada: disparar PRIMEIRO as células caras (elas dominam o wall-clock;
  o resto preenche os cores restantes). A rodada inteira nas 3 máquinas ≈ **1–2 dias**.
- Os walls que saírem daqui SÃO o M7: `progress.py --tabela` ao final = a tabela de
  dimensionamento das 30 sementes (decisões A3/A5 com dado).
