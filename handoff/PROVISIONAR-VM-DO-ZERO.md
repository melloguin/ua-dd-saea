# PROVISIONAR UMA VM DO ZERO ATÉ O DISPARO — 10 bateladas

> **Versão 2026-08-06.** Este documento é a receita COMPLETA, destilada de dois
> provisionamentos reais (a `vm1` em 01/08 e a `vm4` em 04-05/08) e de todos os
> erros cometidos neles. Ele SUBSTITUI o `TUTORIAL_provisionar_vm_matlab_do_zero.md`
> e o `HANDOFF_aceitacao_vm10.md` (que viviam em `~/Downloads` e se perderam).
>
> **Quem lê isto está provisionando UMA máquina nova para a campanha M8 em voo.**
> Nada aqui toca as máquinas que já rodam. Siga as bateladas em ordem; cada uma
> tem um critério de aceitação objetivo. Se um critério falhar, **PARE e reporte**
> (protocolo D81) — não improvise.

---

## §0 · A MÁQUINA DESTA VEZ (preencha antes de começar)

| campo | valor |
|---|---|
| nome | `matlab-vm5` |
| conta | `gdmello.nunes@gmail.com` |
| projeto | `skilled-text-480300-d9` |
| zona | `us-east4-a` |
| shape | `n2-highmem-48` (48 vCPU / 377 GB) |
| **jobs** | **24** (= vCPU ÷ 2; 1 job por núcleo FÍSICO, D79; ~16 GB/job) |
| jitter MATLAB | `25` (16+ jobs) — use `12` em máquinas de 6-8 jobs |
| rótulo de frota | `vm5` (vai em `UA_DD_SAEA_HOST`) |
| **sementes** | **`"42 9 8 28 27 7 26"`** (a cauda da campanha — ver §3) |

**Já feito (não repita):** a VM foi criada com `--deletion-protection`,
`--scopes=storage-rw,logging-write,monitoring-write`, disco 250 GB `pd-balanced`,
imagem `debian-12`. A sonda passou: `nproc` = 48, RAM 377 G.

**Detalhe que economiza uma batelada inteira:** a `vm5` está no **mesmo projeto da
`vm1`**, logo compartilha a mesma service account — que **já tem acesso ao bucket**.
Não é preciso conceder IAM; só verificar (B8).

---

## §1 · CONTEXTO MÍNIMO (o que esta máquina vai fazer)

A campanha **M8** roda 30 sementes × 525 células (21 pares `exp/alg` × 25
problemas) do pipeline `ua-dd-saea`. Cinco máquinas já rodam desde 02/08
(`vm1` 16 jobs, `vm2` 6, `vm3` 16, `vm10` 6, `vm4` 6). A `vm5` entra para
**encurtar o caminho crítico**, assumindo as sementes que hoje só sairiam por
volta de 19/08.

- **CAMPANHA_ID (idêntica em toda a frota, nunca mude):** `7f4f0e429a46_M8`
- **Tag do código:** `m8-freeze` · branch `experiment/definitive_algorythms`
- **Bucket:** `gs://mestrado_experiments`
- **Roster da 1ª onda (21 pares, `c311` REMOVIDO da campanha inteira):**
  ```
  main/b1 main/b3 main/b4 main/c122 main/c141 main/c149 main/c154 main/c217
  main/c238 main/c262 main/e7 main/e74 main/e81 main/moead main/nsga2
  main/nsga3 main/smsemoa off/b5m off/b5r off/e103 off/moead_media
  ```
- **Duplicidade é ACEITA** (decisão do autor, 05/08): a `vm5` roda sementes que
  também estão nas filas de outras máquinas. Quem terminar primeiro grava no
  bucket; o segundo toma `colidiu_412`, que é **benigno** (create-or-refuse,
  B-10) e não perde dado.

---

## §2 · AS 10 BATELADAS

Todas são pastes únicos para o terminal do operador. Onde houver `# <<<`, é valor
por máquina.

### B1 · Identidade da frota + sonda

```bash
cat > ~/frota_m8.env <<'EOF'
VM1=(--account=gdmello.nunes@gmail.com --project=skilled-text-480300-d9 --zone=us-east1-b)
VM5=(--account=gdmello.nunes@gmail.com --project=skilled-text-480300-d9 --zone=us-east4-a)
EOF
source ~/frota_m8.env
gcloud compute ssh matlab-vm5 "${VM5[@]}" --ssh-flag="-o ConnectTimeout=20" --command="echo '== SSH_OK =='; nproc; free -g | sed -n 2p; df -h / | sed -n 2p"
```

**Aceita se:** `SSH_OK` + `nproc` = 48 + Mem ~377 G.
⚠ Se o ssh recusar nos primeiros minutos após criação/boot, é a chave propagando —
espere 1 min e repita. Não conclua "VM quebrada".

---

### B2 · Colher o kit da `vm1` (a receita VIVA, nunca digitada à mão)

```bash
source ~/frota_m8.env; mkdir -p /tmp/vmkit
gcloud compute scp "${VM1[@]}" matlab-vm1:'~/parte_a.sh' /tmp/vmkit/parte_a.sh 2>&1 || echo "FALHOU: parte_a.sh"
gcloud compute scp "${VM1[@]}" matlab-vm1:'~/painel.sh' /tmp/vmkit/painel.sh 2>&1 || echo "FALHOU: painel.sh"
gcloud compute scp "${VM1[@]}" matlab-vm1:'~/Documents/MATLAB/startup.m' /tmp/vmkit/startup.m 2>&1 || echo "FALHOU: startup.m"
echo "== md5 do startup.m (TEM de ser 3e06ae44c9dba0d9fc1e9724f0878347) =="; md5 -q /tmp/vmkit/startup.m
ls -la /tmp/vmkit
```

**Aceita se:** 3 arquivos + md5 do `startup.m` **exatamente**
`3e06ae44c9dba0d9fc1e9724f0878347` (340 bytes).

⚠ **O `startup.m` NÃO está no repositório e não pode ser digitado** — ele contém
`addpath` ABSOLUTO + `pyenv(...InProcess)` e é a ponte MATLAB↔Python. Sempre
copiado byte-a-byte de uma irmã.

---

### B3 · Bootstrap do sistema (~30–50 min, em `setsid nohup`)

```bash
source ~/frota_m8.env
gcloud compute scp "${VM5[@]}" /tmp/vmkit/parte_a.sh matlab-vm5:'~/parte_a.sh' && \
gcloud compute ssh matlab-vm5 "${VM5[@]}" --command='chmod +x ~/parte_a.sh; (setsid nohup bash ~/parte_a.sh > ~/parte_a.log 2>&1 &); sleep 5; echo "== bootstrap DISPARADO =="; tail -2 ~/parte_a.log'
```

Acompanhamento (rode quando quiser; pode fechar o laptop):

```bash
source ~/frota_m8.env; gcloud compute ssh matlab-vm5 "${VM5[@]}" --command='V=$(pgrep -f "parte_a\.sh" >/dev/null && echo RODANDO || echo parado); echo "[$V]"; grep -E "^=== |FALHOU|CONCLUIDA|PRESENTE|AUSENTE" ~/parte_a.log | tail -10'
```

**Aceita se:** `[parado]` + `########## PARTE A CONCLUIDA` + **zero linhas
`FALHOU`** + `A7 libpython3.11.so PRESENTE`.

O que o `parte_a.sh` faz (A0–A7b): apt update · deps de build + X11 · X11
forwarding · **libs do MathWorks Service Host** · clone do repo (branch
`experiment/definitive_algorythms`, HTTPS público) · **MATLAB R2025a via `mpm`
com a lista de produtos LIDA DO LOCK** (`requirements/locks/env_matlab_ver.lock.txt`)
· `license_info.xml` em modo `onlinelicensing` · **pyenv 3.11.9 com
`--enable-shared`** · pyenv no `.bashrc` e no `.profile`.

⚠ **Armadilhas embutidas (já resolvidas pelo script — não "otimize"):**
- as libs do Service Host **precisam vir ANTES do primeiro `matlab`**, senão dá
  erro **5201**;
- sem `--enable-shared` não existe `libpython3.11.so` e **a ponte A2 morre**;
  o conserto é recompilar, nunca remendar;
- a lista de produtos MATLAB vem do lock (D80) — nunca de uma lista digitada.

---

### B4 · Licença MATLAB (INTERATIVO — o único lugar sem redirecionamento)

Abra a sessão:

```bash
source ~/frota_m8.env; gcloud compute ssh matlab-vm5 "${VM5[@]}"
```

Já dentro da VM:

```bash
pkill -9 -f MathWorksServiceHost; pkill -9 -f MATLABConnector; sleep 3; matlab -nodisplay
```

- conta: **`mello.guilherme@dcc.ufmg.br`** (licença online `40904996`);
- `"Licensing shutdown"` na 1ª tentativa é **soluço conhecido** — repita;
- quando o prompt `>>` abrir, o banner já é a prova. Deve dizer
  **`R2025a Update 1 (25.1.0.2973910)`** — idêntico à frota;
- `exit` para sair do MATLAB e `exit` de novo para voltar ao laptop.

**Aceita se:** o banner apareceu com a versão acima.
⚠ Esta é a **6ª sessão concorrente** da licença. A 5ª foi provada em 05/08. Se
vier recusa por limite de sessões, **PARE e reporte o texto exato** — isso muda
o desenho da expansão.

---

### B5 · Os 5 venvs (a partir dos locks — D80) + `startup.m`

Crie o script localmente:

```bash
cat > /tmp/vmkit/venvs_m8.sh <<'VENVS'
#!/usr/bin/env bash
# Os 5 venvs, SEMPRE a partir de requirements/locks/*.lock.txt (D80).
ts(){ date -u +%H:%M:%S; }
ok(){ echo "[$(ts)] OK     $1"; }
ko(){ echo "[$(ts)] FALHOU $1"; }
R="$HOME/ua-dd-saea"; L="$R/requirements/locks"
export PYENV_ROOT="$HOME/.pyenv"; export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)" 2>/dev/null
PYBIN="$PYENV_ROOT/versions/3.11.9/bin/python"
[ -x "$PYBIN" ] || { ko "3.11.9 ausente - a parte A nao fechou"; exit 1; }

echo "=== venvs pyenv 3.11.9: env_bridge, env_main, env_e81_qpots ==="
mkdir -p "$HOME/venvs"
for E in env_bridge env_main env_e81_qpots; do
  "$PYBIN" -m venv --clear "$HOME/venvs/$E" \
    && "$HOME/venvs/$E/bin/pip" install --upgrade pip -q \
    && "$HOME/venvs/$E/bin/pip" install -q -r "$L/$E.lock.txt" \
    && ok "$E" || ko "$E"
done

echo "=== micromamba (interpretadores 3.7/3.8 nao existem no Debian 12) ==="
if ! command -v micromamba >/dev/null 2>&1; then
  cd "$HOME" && curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj bin/micromamba \
    && export PATH="$HOME/bin:$PATH" && ok "micromamba instalado" || ko "micromamba"
fi
export PATH="$HOME/bin:$PATH"
export MAMBA_ROOT_PREFIX="$HOME/micromamba"
eval "$(micromamba shell hook -s bash)" 2>/dev/null

echo "=== env_b5 (py3.7) — --no-deps OBRIGATORIO ==="
micromamba create -y -q -n env_b5 python=3.7 \
  && micromamba run -n env_b5 pip install -q --no-deps -r "$L/env_b5.lock.txt" \
  && ok env_b5 || ko env_b5

echo "=== env_c311 (py3.8) — GPy ANTES do resto, com --no-build-isolation ==="
micromamba create -y -q -n env_c311 python=3.8 \
  && micromamba run -n env_c311 pip install -q "GPy==1.9.9" --no-build-isolation \
  && micromamba run -n env_c311 pip install -q --no-deps -r "$L/env_c311.lock.txt" \
  && ok env_c311 || ko env_c311

echo "=== SYMLINKS ~/venvs -> micromamba — OBRIGATORIO (A48) ==="
# standalone_harness.py:312-317 resolve o venv pelo NOME varrendo ~/python_venvs,
# ~/venvs, ~/Documents/python_venvs, /home/jupyter/python_venvs. ~/micromamba/envs
# NAO esta na lista: sem symlink o harness cai no caminho do MAC declarado no
# envs.json e TODA celula de b5r/b5m/moead_media morre com FileNotFoundError.
# Custo medido na vm4: 75 celulas perdidas.
ln -sfn "$HOME/micromamba/envs/env_b5"   "$HOME/venvs/env_b5"
ln -sfn "$HOME/micromamba/envs/env_c311" "$HOME/venvs/env_c311"
ls -l "$HOME/venvs/" | grep -E "env_b5|env_c311" && ok "symlinks" || ko "symlinks"

echo
echo "=== CONFERENCIA ==="
for E in env_bridge env_main env_e81_qpots env_b5 env_c311; do
  # SEMPRE pelo caminho do harness (~/venvs/$E) — `micromamba run` funciona sem
  # o symlink e MASCARA o defeito.
  V=$("$HOME/venvs/$E/bin/python" -c "import sys;print('.'.join(map(str,sys.version_info[:3])))" 2>&1)
  echo "  $E -> $V"
done
echo "=== gcs (P4) ==="
for E in env_b5 env_c311 env_e81_qpots env_main; do
  V=$("$HOME/venvs/$E/bin/python" -c "import google.cloud.storage as s;print(s.__version__)" 2>&1 | tail -1)
  echo "  $E -> $V"
done
echo "########## VENVS CONCLUIDO $(date -u) ##########"
echo "Esperado: bridge/main/e81 = 3.11.9 · b5 = 3.7.x · c311 = 3.8.x"
echo "gcs: b5/c311 = 3.9.0 · e81/main = 3.13.0"
VENVS
```

Envie e dispare (o `startup.m` vai junto):

```bash
source ~/frota_m8.env
gcloud compute scp "${VM5[@]}" /tmp/vmkit/venvs_m8.sh matlab-vm5:'~/venvs_m8.sh' && \
gcloud compute scp "${VM5[@]}" /tmp/vmkit/startup.m matlab-vm5:'~/startup_tmp.m' && \
gcloud compute ssh matlab-vm5 "${VM5[@]}" --command='mkdir -p ~/Documents/MATLAB && mv ~/startup_tmp.m ~/Documents/MATLAB/startup.m && echo "startup.m: $(md5sum ~/Documents/MATLAB/startup.m | cut -d" " -f1)"; chmod +x ~/venvs_m8.sh; (setsid nohup bash ~/venvs_m8.sh > ~/venvs_m8.log 2>&1 &); sleep 3; echo "== venvs DISPARADOS (~20-40 min) =="'
```

**Aceita se:** md5 `3e06ae44…` + `venvs DISPARADOS`.
💡 **B4 e B5 podem correr em paralelo** — os venvs não dependem do MATLAB.

⚠ **Armadilhas:** `--no-deps` no micromamba é OBRIGATÓRIO (sem ele o pip
re-resolve a árvore e viola o D80 **em silêncio**); `GPy==1.9.9` precisa de
`--no-build-isolation` e **antes** do resto (a extensão Cython exige numpy já
presente; o erro sem isso é um traceback de `gcc` que não menciona numpy).

---

### B6 · Artefatos pré-requisito + exports + drivers + painel

Empacote no laptop (uma vez) e envie:

```bash
cd ~/Documents/python_repos/mestrado/ua-dd-saea && tar -czf /tmp/vmkit/ua_prereq.tgz data/doe data/sonda data/datasets && ls -lh /tmp/vmkit/ua_prereq.tgz && md5 -q /tmp/vmkit/ua_prereq.tgz
```

```bash
source ~/frota_m8.env
gcloud compute scp "${VM5[@]}" /tmp/vmkit/ua_prereq.tgz matlab-vm5:/tmp/ua_prereq.tgz && \
gcloud compute scp "${VM5[@]}" /tmp/vmkit/painel.sh matlab-vm5:'~/painel.sh' && \
gcloud compute ssh matlab-vm5 "${VM5[@]}" --command='cd ~/ua-dd-saea || exit 1; md5sum /tmp/ua_prereq.tgz; tar -xzf /tmp/ua_prereq.tgz --skip-old-files && echo "--- contagens (esperado: doe 751 · sonda 25 · datasets 785) ---" && for d in doe sonda datasets; do echo "  $d: $(find data/$d -name "*.parquet" | wc -l) parquet / $(find data/$d -name "*.manifest.json" | wc -l) sidecar"; done; echo "--- md5 de amostra ---"; md5sum data/sonda/sonda_MMF1.parquet data/doe/ZDT1/doe_ZDT1_0.parquet; echo "--- exports P11 ---"; grep -q UA_DD_SAEA_CAMPANHA_ID ~/.bashrc || printf "%s\n%s\n" "export UA_DD_SAEA_HOST=vm5" "export UA_DD_SAEA_CAMPANHA_ID=\"7f4f0e429a46_M8\"" >> ~/.bashrc; grep -q UA_DD_SAEA_CAMPANHA_ID ~/.profile || printf "%s\n%s\n" "export UA_DD_SAEA_HOST=vm5" "export UA_DD_SAEA_CAMPANHA_ID=\"7f4f0e429a46_M8\"" >> ~/.profile; bash -lc "echo conferencia-nohup: HOST=\$UA_DD_SAEA_HOST CID=\$UA_DD_SAEA_CAMPANHA_ID"; echo "--- drivers ---"; cp ~/ua-dd-saea/scripts/lote3s.sh ~/lote3s.sh && cp ~/ua-dd-saea/scripts/plano3s.sh ~/plano3s.sh && echo "ORDEM_INVALIDA: $(grep -c ORDEM_INVALIDA ~/lote3s.sh) (1 = driver novo)"; chmod +x ~/painel.sh ~/lote3s.sh ~/plano3s.sh; echo "== B6 CONCLUIDA =="'
echo "== md5 de amostra NO LAPTOP (tem de bater) =="
md5 -q ~/Documents/python_repos/mestrado/ua-dd-saea/data/sonda/sonda_MMF1.parquet
md5 -q ~/Documents/python_repos/mestrado/ua-dd-saea/data/doe/ZDT1/doe_ZDT1_0.parquet
```

**Aceita se:** md5 do tgz igual nos dois lados · contagens `751 / 25 / 785` ·
os 2 md5 de amostra **idênticos** · `conferencia-nohup: HOST=vm5
CID=7f4f0e429a46_M8` · `ORDEM_INVALIDA: 1` · `B6 CONCLUIDA`.

⚠ **Por que os exports em `.bashrc` E `.profile`:** o driver **não** exporta
`UA_DD_SAEA_CAMPANHA_ID`; o default dele deriva da data UTC e **mudaria no meio
da campanha, quebrando o resume**. A linha `conferencia-nohup` prova que o shell
não-interativo (o do `nohup`) enxerga os valores — não pule essa checagem.
⚠ `--skip-old-files` é o `cp -n` do tar: **nunca sobrescreve artefato existente**.
Artefatos pré-requisito jamais são regenerados (D81).

---

### B7 · Verificação: ponte + venvs + higiene

```bash
source ~/frota_m8.env
gcloud compute ssh matlab-vm5 "${VM5[@]}" --command='echo "===== venvs ====="; grep -E "OK |FALHOU|-> |CONCLUIDO" ~/venvs_m8.log | tail -16; echo; echo "===== ponte (startup.m rodando SOZINHO, sob -batch) ====="; source ~/.profile 2>/dev/null; matlab -batch "disp(version); disp(pyenv().Version); disp(char(pyenv().ExecutionMode)); assert(double(py.numpy.array([1,2,3]).sum())==6); disp(\"PONTE_NUMPY_OK\")" > ~/ponte.log 2>&1; cat ~/ponte.log; echo; echo "===== symlinks (A48) ====="; cd ~/ua-dd-saea && ~/venvs/env_main/bin/python -c "
import sys; sys.path.insert(0, \".\")
from src.standalone_harness import interpreter_for_alg
for a in (\"moead_media\", \"b5r\", \"b5m\"):
    print(\"  \", a, \"->\", interpreter_for_alg(a))
"; echo; echo "===== auto-updater MathWorks (esperado: nao aplicavel) ====="; ( matlab -batch "s=settings; s.matlab.addons.autoupdatecheck.Enable.PersonalValue=false; disp(\"autoupdate OFF\")" > ~/upd.log 2>&1 && tail -1 ~/upd.log ) || echo "(nao aplicavel nesta versao — anotar, igual as irmas)"'
```

**Aceita se:** 5 venvs nas versões certas (`3.11.9` ×3, `3.7.x`, `3.8.x`) · gcs
`3.9.0/3.9.0/3.13.0/3.13.0` · zero `FALHOU` · ponte com
`25.1.0.2973910` + `3.11` + `InProcess` + **`PONTE_NUMPY_OK`** · os 3 algs
resolvendo para **`/home/gmello/venvs/env_b5/bin/python`** (caminho **Linux** —
se aparecer `/Users/…`, o symlink falhou: veja §4 nº 4).

---

### B8 · Bucket: verificação de acesso + portão de aceitação (9 células REAIS)

```bash
source ~/frota_m8.env
gcloud compute ssh matlab-vm5 "${VM5[@]}" --command='echo "--- a SA le o bucket? ---"; ~/venvs/env_main/bin/python -c "from google.cloud import storage; b=storage.Client().bucket(\"mestrado_experiments\"); print(\"LEITURA OK:\", len(list(b.list_blobs(max_results=3))), \"objetos\")"; source ~/.profile 2>/dev/null; cd ~/ua-dd-saea; echo "--- lote-portao: 9 celulas reais da s42, bucket LIGADO ---"; LOTE=CONFIRMA LOTE_MAPA=0 LOTE_BUCKET=1 LOTE_ORDEM=semente LOTE_PARES="main/nsga2 main/c154 main/c262" LOTE_SEEDS=42 LOTE_JOBS=3 LOTE_MATLAB_JITTER=12 LOTE_DMAX=2 bash ~/lote3s.sh > ~/lote_gate.log 2>&1; echo "lote rc=$? (rc NAO e veredito)"; grep -E "células:|fora da grade|bucket:|FIM" ~/lote_gate.log | tail -6; for A in nsga2 c154 c262; do echo "--- portao main/$A/MMF1/42 ---"; ~/venvs/env_main/bin/python scripts/portao.py --exp main --alg $A --problema MMF1 --semente 42 > ~/portao_$A.log 2>&1; tail -3 ~/portao_$A.log; done'
```

**Aceita se:** `LEITURA OK` · o lote fecha com `ok=9` (ou pula células que a
frota já fez — a s42 pode ter manifestos) · e os portões dão VERDE **ou** os
"vermelhos" esperados descritos abaixo.

⚠ **Leitura dos portões (não confunda com defeito):**
- `FileNotFoundError: ..._surrogate.parquet` em `c154`/`c262` é a **PODA
  FUNCIONANDO**: esses algoritmos são bucket-only, a camada ③ sobe ao bucket,
  é conferida por MD5 e apagada localmente. É a assinatura do sucesso.
- `INCONCLUSIVO ⚪` em `nsga2` = gate G-1 não-aplicável a piso (piso não tem
  surrogate). Benigno.
- `Lembrete (D97)` é lembrete impresso, não falha.
- **`portao.py` JULGA, não executa.** Rodá-lo antes de existirem células dá
  vermelho por ausência. Por isso o lote vem primeiro.

---

### B9 · DRY-RUN do disparo (o `[grid]` — nada executa)

```bash
source ~/frota_m8.env
gcloud compute ssh matlab-vm5 "${VM5[@]}" --command='source ~/.profile 2>/dev/null; cd ~/ua-dd-saea; LOTE_MAPA=0 LOTE_BUCKET=1 LOTE_ORDEM=semente LOTE_SEEDS="42 9 8 28 27 7 26" LOTE_JOBS=24 LOTE_MATLAB_JITTER=25 LOTE_PARES="main/b1 main/b3 main/b4 main/c122 main/c141 main/c149 main/c154 main/c217 main/c238 main/c262 main/e7 main/e74 main/e81 main/moead main/nsga2 main/nsga3 main/smsemoa off/b5m off/b5r off/e103 off/moead_media" bash ~/lote3s.sh > ~/dry.log 2>&1; grep -E "sementes=|células:|fora da grade|custo estimado|bucket:|DRY-RUN" ~/dry.log'
```

**Aceita se:** `sementes=42,9,8,28,27,7,26` · `células:` perto de **3.666**
(7×525 menos o que já tem manifesto) · `bucket: LIGADO` · a linha `DRY-RUN…`
provando que **nada rodou**.

⚠ **Sem `LOTE=CONFIRMA` o driver SEMPRE faz dry-run** — é o comportamento
padrão, e é a rede de segurança.

---

### B10 · 🚀 DISPARO

```bash
source ~/frota_m8.env
gcloud compute ssh matlab-vm5 "${VM5[@]}" --command='source ~/.profile 2>/dev/null; cd ~/ua-dd-saea || exit 1; [ "$UA_DD_SAEA_CAMPANHA_ID" = 7f4f0e429a46_M8 ] || { echo "FATAL: CID errada — nada disparado"; exit 1; }; [ -z "${UA_DD_SAEA_PISO_N:-}" ] || { echo "FATAL: PISO_N setado — nada disparado"; exit 1; }; if pgrep -f "[l]ote3s\.sh$" >/dev/null; then echo "JA HA LOTE RODANDO — nada disparado"; else LOTE=CONFIRMA LOTE_MAPA=0 LOTE_BUCKET=1 LOTE_ORDEM=semente LOTE_SEEDS="42 9 8 28 27 7 26" LOTE_JOBS=24 LOTE_MATLAB_JITTER=25 LOTE_PARES="main/b1 main/b3 main/b4 main/c122 main/c141 main/c149 main/c154 main/c217 main/c238 main/c262 main/e7 main/e74 main/e81 main/moead main/nsga2 main/nsga3 main/smsemoa off/b5m off/b5r off/e103 off/moead_media" setsid nohup bash ~/lote3s.sh > ~/lote_M8_vm5.log 2>&1 & sleep 30; grep -E "sementes=|células:|fora da grade|bucket:|custo estimado" ~/lote_M8_vm5.log | tail -5; pgrep -f "[l]ote3s\.sh$" >/dev/null && echo "✅ vm5 NO AR — pode fechar o laptop" || echo "🔴 NAO SUBIU — cole: tail -30 ~/lote_M8_vm5.log"; fi'
```

**Aceita se:** os MESMOS números do B9 + **`✅ vm5 NO AR`**.

Painel ao vivo (Ctrl-C sai sem afetar nada):

```bash
source ~/frota_m8.env; gcloud compute ssh matlab-vm5 "${VM5[@]}" --command="bash ~/painel.sh"
```

---

## §3 · O MAPA DE SEMENTES DA FROTA (estado em 06/08, ~98 h de campanha)

**A frota completa e o que cada máquina tem na fila.** As 30 sementes sancionadas
são `{0…28, 42}` (a 29 e a 30 **não existem**).

| VM | conta / projeto | zona | jobs | fila (nesta ordem) | ✅ concluídas | 🔄 em curso | ⏳ faltam |
|---|---|---|---|---|---|---|---|
| **vm1** | `gdmello.nunes` / `skilled-text-480300-d9` | us-east1-b | 16 | s0→s10 | s0, s1 | **s2** (97 %) | s3…s10 |
| **vm2** | `melloguinn` / `core-cascade-341902` | us-east1-b | 6 | s11→s14 | s11 | — | s12, s13, s14 |
| **vm3** | `invest.gdmn` / `project-2aa33d8c-94a7-488b-89e` | us-east1-b | 16 | s19→s28→s42 | s19, s20 | **s21** (84 %) | s22…s28, s42 |
| **vm10** | `mellohr` / `project-0a70dd69-8e73-4d58-819` | us-east1-b | 6 | s16→s15→s17→s18 | s16 | **s15** (63 %) | s17, s18 |
| **vm4** | `ollem.anaileh` / `project-922af1ae-1760-4822-aea` | us-east4-a | 6 | s10→s14→s18→s42 | — | **s10** (78 %)¹ | s14, s18, s42 |
| **vm5** | `gdmello.nunes` / `skilled-text-480300-d9` | us-east4-a | **24** | **s42→s9→s8→s28→s27→s7→s26** | — | (a provisionar) | as 7 |

¹ A `s10` da `vm4` tem um buraco de **75 células** (`b5r`/`b5m`/`moead_media`)
causado pelo defeito de symlink já corrigido (§4 nº 4). Elas serão refeitas
depois — ou pela `vm1`, que também tem a `s10` na fila.

**Cobertura de cada semente (quem a fará, e quando sairia sem a `vm5`):**

| semente | máquina(s) | previsão SEM a vm5 |
|---|---|---|
| s0, s1, s11, s16, s19, s20 | ✅ prontas | — |
| s2, s21 | vm1, vm3 | ~1 dia |
| s3–s6 | vm1 (sequencial) | 2,5 – 7 dias |
| **s7, s8, s9** | vm1 (fim da fila) | **8,5 – 11,5 dias** |
| s10 | vm4 (agora) + vm1 (fim) | ~1 dia |
| s12, s13 | vm2 | 4 – 8 dias |
| s14 | vm4 (2ª) + vm2 (fim) | ~5 dias |
| s15, s17 | vm10 | 1,5 – 5,5 dias |
| s18 | vm10 (fim) + vm4 (3ª) | ~9 dias |
| s22–s25 | vm3 (sequencial) | 2,5 – 7 dias |
| **s26, s27, s28** | vm3 (fim da fila) | **8 – 11 dias** |
| **s42** | vm3 (última) + vm4 (última) | **12,5 – 13 dias** ← a mais atrasada |

### Por que a `vm5` recebe `42 9 8 28 27 7 26`

A campanha termina quando **cada** semente estiver completa **por alguém**. As
sete escolhidas são exatamente as de previsão mais longa — as caudas de `vm1`,
`vm3` e `vm4`. Cobrindo-as, o caminho crítico cai de **~19/08 para ~14/08**.

`LOTE_ORDEM=semente` põe TODA a semente na fila — da célula mais barata à mais
cara — antes de passar à seguinte, **na ordem em que aparecem em `LOTE_SEEDS`**.
Por isso a `s42` (a mais atrasada de todas) vem primeiro. Com 24 jobs, a `vm5`
faz ~23 h por semente, ou seja ~6-7 dias para as sete.

Se a `vm5` não chegar às últimas da lista, **as irmãs as cobrem de qualquer
forma** — não há perda, só sobreposição. E a sobreposição é **decisão explícita
do autor**: nenhuma máquina em produção será parada para "limpar" duplicidade;
quem gravar primeiro no bucket vence, e o segundo toma `colidiu_412`, que é
benigno.

---

## §4 · COMPÊNDIO DE ARMADILHAS (cada uma custou tempo real)

1. **`cat > arquivo && comando &`** — o `&` manda o `cat` para background, que em
   shell não-interativa lê `/dev/null`: o arquivo nasce **vazio** e o comando
   "roda com sucesso" em 0 s. Sempre em **duas fases**: copie em foreground,
   dispare depois. Confirme com `wc -c`.
2. **`( setsid nohup cmd & )`** — isole o disparo em subshell quando houver
   outros comandos na mesma linha; senão o `&` engole o que vem antes.
3. **`for X in $VAR` no zsh NÃO separa por espaços** (diferente do bash). Use
   `for X in $(echo $VAR)`. Um loop de 28 zonas virou 1 tentativa por causa disso.
4. **Symlinks `~/venvs/env_b5` e `env_c311` → micromamba** (A48). Sem eles o
   harness resolve para o caminho do **Mac** e mata `b5r`/`b5m`/`moead_media`.
   Custou 75 células. Conferir SEMPRE por `~/venvs/$E/bin/python`, nunca por
   `micromamba run` (que funciona sem o symlink e mascara o defeito).
   O symlink pode ser criado **com o lote rodando** — a resolução é por
   subprocesso, então vale para todas as células seguintes.
5. **MATLAB sempre com `> log 2>&1`, nunca em pipe.** Única exceção: o login
   interativo da licença.
6. **`exit=0` não é veredito.** Sempre leia o conteúdo do log.
7. **Nunca dois lotes na mesma máquina** — o driver **não tem lock**. Use sempre
   o guard `pgrep -f "[l]ote3s\.sh$"` (com colchete, senão o `pgrep` casa consigo
   mesmo).
8. **`LOTE_BUCKET` sempre explícito.** O catch-all do driver assume `1`, o que
   vira 403 em máquina sem `objects.delete`.
9. **O modo-mapa SOBRESCREVE `LOTE_PARES`.** Para rodar um roster recortado (a 1ª
   onda, sem `c311`), use **`LOTE_MAPA=0` + `LOTE_SEEDS` explícito**.
10. **`UA_DD_SAEA_PISO_N` deve estar AUSENTE** na campanha (o `N=20` é cravado).
11. **Stockout ≠ cota.** `currently unavailable` = falta máquina na zona (tente
    outra zona/horário); `Quota exceeded` = cota (o teto **global**
    `CPUS_ALL_REGIONS` costuma ser o cadeado escondido em contas novas).
12. **Redimensionar VM vazia é grátis:** `stop` → `set-machine-type` → `start`.
13. **`teto_wall` NÃO é falha** — é a classe sancionada (DI-38a). O `done.txt`
    marca `failed`, mas o manifesto diz `motivo_parada=teto_wall`, e o driver
    classifica como "abortou". `c154` com D≥12 **é esperado abortar** — o próprio
    modelo de custo atribui o custo-de-aborto a ele.
14. **Célula MATLAB longa com CPU ~0% por horas** = o travamento conhecido
    (o stack MATLAB não tem teto de wall-clock, DI-35.5). Mate só aquele
    processo; a re-passada recolhe a célula.
15. **Se a VM parar de aceitar ssh novo mas o painel antigo continuar rodando**,
    é exaustão de recursos. Diagnostique pelo **console serial**
    (`gcloud compute instances get-serial-port-output`), que funciona de fora.
    `instances reset` custa apenas as células em voo (sem manifesto ⇒ voltam à
    grade) — e a proteção contra deleção não impede reset.
16. **Re-colar o comando de disparo é INOFENSIVO** (provado): a grade se
    reconstrói só com o que falta. É assim que se retoma qualquer máquina.

---

## §5 · REGRAS PERMANENTES (do autor — não negociáveis)

- **NUNCA** `git push`, `git add -A` ou criar tag: são atos do autor.
- **NUNCA** `rm`/`mv`/`rsync --delete` no bucket.
- **NÃO PARAR** `vm1`, `vm2`, `vm3`, `vm4`, `vm10` — estão em produção com
  processos de horas. A `vm5` é aditiva.
- **D80:** os locks são a verdade; nunca improvisar um pin.
- **D81:** ambiguidade ⇒ **pare e pergunte**.
- **D97:** validação de fidelidade é manual do autor, a posteriori.
- Não tocar em `src/gcs.py`.
- Logs sempre em `$HOME`; diagnóstico de credencial nunca imprime token.
- Artefatos pré-requisito (`data/doe`, `data/sonda`, `data/datasets`) **nunca**
  são regenerados — só copiados.

---

## §6 · ACOMPANHAMENTO (durante e depois do disparo)

### 6.1 · Painel ao vivo, uma máquina por terminal

Atualiza a cada 60 s; `Ctrl-C` sai **sem afetar** o lote (o painel é só um visor).

```bash
source ~/frota_m8.env; gcloud compute ssh matlab-vm5 "${VM5[@]}" --command="bash ~/painel.sh"
```

As irmãs (exigem que as contas delas continuem autenticadas no `gcloud` deste
laptop; se der erro de credencial, ignore — não é problema da `vm5`):

```bash
gcloud compute ssh matlab-vm1 --account=gdmello.nunes@gmail.com --project=skilled-text-480300-d9 --zone=us-east1-b --command="bash ~/painel.sh"
```
```bash
gcloud compute ssh matlab-vm2 --account=melloguinn@gmail.com --project=core-cascade-341902 --zone=us-east1-b --command="bash ~/painel.sh"
```
```bash
gcloud compute ssh matlab-vm3 --account=invest.gdmn@gmail.com --project=project-2aa33d8c-94a7-488b-89e --zone=us-east1-b --command="bash ~/painel.sh"
```
```bash
gcloud compute ssh matlab-vm10 --account=mellohr@gmail.com --project=project-0a70dd69-8e73-4d58-819 --zone=us-east1-b --command="bash ~/painel.sh"
```
```bash
gcloud compute ssh matlab-vm4 --account=ollem.anaileh@gmail.com --project=project-922af1ae-1760-4822-aea --zone=us-east4-a --command="bash ~/painel.sh"
```

**Como ler:** `RODANDO` deve ficar cravado no número de jobs da máquina. Células
com `min` subindo por horas são **normais** na cauda cara (`c154`, `c262`,
`e81`). O alarme real é **CPU ~0 % por horas** — que o painel não mostra, mas o
censo (6.3) pega.

### 6.2 · Kit M1 — o pulso da frota em um comando (rotina 2×/dia)

```bash
for M in "matlab-vm1|gdmello.nunes@gmail.com|skilled-text-480300-d9|us-east1-b" "matlab-vm2|melloguinn@gmail.com|core-cascade-341902|us-east1-b" "matlab-vm3|invest.gdmn@gmail.com|project-2aa33d8c-94a7-488b-89e|us-east1-b" "matlab-vm10|mellohr@gmail.com|project-0a70dd69-8e73-4d58-819|us-east1-b" "matlab-vm4|ollem.anaileh@gmail.com|project-922af1ae-1760-4822-aea|us-east4-a" "matlab-vm5|gdmello.nunes@gmail.com|skilled-text-480300-d9|us-east4-a"; do N="${M%%|*}"; R="${M#*|}"; C="${R%%|*}"; R="${R#*|}"; P="${R%%|*}"; Z="${R##*|}"; echo; echo "======= $N ======="; gcloud compute ssh "$N" --account="$C" --project="$P" --zone="$Z" --command="D=\$(ls -td /tmp/lote3s_* 2>/dev/null | head -1); echo \"lote \$(basename \$D) · grade \$(wc -l < \$D/grid.txt) · done \$(wc -l < \$D/done.txt)\"; awk '{c[\$5]++} END {for (k in c) printf \"  %s=%d\", k, c[k]; print \"\"}' \$D/done.txt; echo \"  disco: \$(df -h \$HOME | sed -n 2p)\"; echo \"  MATLAB >3h com CPU<5%: \$(ps -eo etimes,pcpu,comm | grep -i matlab | awk '\$1>10800 && \$2<5' | wc -l)\"; echo \"  colidiu_412 nos logs: \$(grep -rl colidiu_412 \$D/logs 2>/dev/null | wc -l)\"" 2>&1 || echo "FALHOU: $N"; done
```

**Como agir:**

| sinal | leitura | ação |
|---|---|---|
| `failed` crescendo na cauda | quase sempre `teto_wall` sancionado | nada — confirme com 6.4 |
| `MATLAB >3h com CPU<5%: 1+` | o travamento da DI-35.5 | mate **só** aquele processo; a re-passada recolhe |
| `colidiu_412 > 0` em s10/s14/s18/s42 | **esperado** (duplicidade aceita) | nada |
| `colidiu_412` em outra semente | investigar | reporte |
| disco > 80 % | inesperado | reporte |
| `done == grade` | a máquina terminou | re-cole o comando de disparo: a grade renasce só com o que faltou |

### 6.3 · Censo completo com veredito de ritmo (o diagnóstico geral)

Coleta em paralelo nas 6 e analisa localmente: sementes concluídas, ritmo real
contra o modelo, ETA por máquina e as células em voo.

```bash
mkdir -p /tmp/censo6; for M in "matlab-vm1|gdmello.nunes@gmail.com|skilled-text-480300-d9|us-east1-b|16" "matlab-vm2|melloguinn@gmail.com|core-cascade-341902|us-east1-b|6" "matlab-vm3|invest.gdmn@gmail.com|project-2aa33d8c-94a7-488b-89e|us-east1-b|16" "matlab-vm10|mellohr@gmail.com|project-0a70dd69-8e73-4d58-819|us-east1-b|6" "matlab-vm4|ollem.anaileh@gmail.com|project-922af1ae-1760-4822-aea|us-east4-a|6" "matlab-vm5|gdmello.nunes@gmail.com|skilled-text-480300-d9|us-east4-a|24"; do N="${M%%|*}"; R="${M#*|}"; C="${R%%|*}"; R="${R#*|}"; P="${R%%|*}"; R="${R#*|}"; Z="${R%%|*}"; J="${R##*|}"; ( gcloud compute ssh "$N" --account="$C" --project="$P" --zone="$Z" --command="D=\$(ls -td /tmp/lote3s_* 2>/dev/null | head -1); if [ -z \"\$D\" ]; then echo NOLOTE; exit 0; fi; B=\$(basename \$D); DP=\${B%_*}; DP=\${DP##*_}; TP=\${B##*_}; T0=\$(date -d \"\${DP:0:4}-\${DP:4:2}-\${DP:6:2} \${TP:0:2}:\${TP:2:2}:\${TP:4:2}\" +%s); echo LOTE \$B; echo EL \$(( \$(date +%s) - T0 )); awk '{s+=\$6} END {printf \"GRID %d %.0f\n\", NR, s}' \$D/grid.txt; awk '{t++; c[\$5]++; m[\$4]++; if (\$5==\"ok\" || \$5==\"retried_ok\") d+=\$6} END {printf \"DONE %d %d %d %d %.0f\n\", t+0, c[\"ok\"]+c[\"retried_ok\"], c[\"failed\"]+0, t-c[\"ok\"]-c[\"retried_ok\"]-c[\"failed\"], d+0; printf \"SEM\"; for (s in m) printf \" %s=%d\", s, m[s]; printf \"\n\"}' \$D/done.txt; echo VIVO; tail -$J \$D/inicio.txt 2>/dev/null | awk '{print \"  \" \$1 \"/\" \$2, \$3, \"s\" \$4}'" > /tmp/censo6/$N.txt 2>&1 ) & done; wait; echo "coletado: $(ls /tmp/censo6 | wc -l)"
python3 - <<'PY'
import datetime
JOBS = {"matlab-vm1":16,"matlab-vm2":6,"matlab-vm3":16,"matlab-vm10":6,"matlab-vm4":6,"matlab-vm5":24}
now = datetime.datetime.now()
for vm in JOBS:
    print(f"\n======= {vm} (jobs={JOBS[vm]}) =======")
    try: linhas = open(f"/tmp/censo6/{vm}.txt").read().splitlines()
    except FileNotFoundError: print("  (sem coleta)"); continue
    if not linhas or linhas[0].startswith("NOLOTE"): print("  sem lote nesta maquina"); continue
    d={}; vivo=[]; em=False
    for ln in linhas:
        if ln.startswith("VIVO"): em=True; continue
        if em: vivo.append(ln); continue
        p=ln.split()
        if p and p[0] in ("LOTE","EL","GRID","DONE","SEM"): d[p[0]]=p[1:]
    if not {"EL","GRID","DONE"} <= set(d): print("  coleta incompleta:", linhas[:3]); continue
    el=int(d["EL"][0]); j=JOBS[vm]
    ng,gs=int(d["GRID"][0]),float(d["GRID"][1])
    tot,okr,fail,outros,ds=int(d["DONE"][0]),int(d["DONE"][1]),int(d["DONE"][2]),int(d["DONE"][3]),float(d["DONE"][4])
    print(f"  decorrido {el/3600:.1f} h · grade {ng} celulas ({gs/3600:.0f} h-core-modelo)")
    print(f"  prontas: {okr} ok · {fail} failed · {outros} outros · {'  '.join(sorted(d.get('SEM',[])))}")
    cap=el*j; r=ds/cap if cap else 0
    print(f"  ritmo vs modelo: {r*100:.0f}%  (o normal MEDIDO da frota e 55-60%: o modelo ignora contencao)")
    if r>0:
        resta=(gs-ds)/(j*r)/3600
        print(f"  ETA no ritmo atual: ~{resta:.0f} h -> ~{(now+datetime.timedelta(hours=resta)).strftime('%d/%m %H:%M')}")
    if vivo: print("  em execucao agora:"); [print(v) for v in vivo]
PY
```

⚠ **Leitura honesta do "ritmo":** o índice **subconta**, porque o trabalho das
células em voo (até J por máquina) não entra na soma — numa máquina parada na
cauda cara ele despenca sem que nada esteja errado. A régua confiável é
**parede por semente completa**: ~35 h/semente com 16 jobs, ~100 h com 6 jobs,
~23 h com 24 jobs.

### 6.4 · Autópsia das falhas (por que uma célula morreu)

```bash
source ~/frota_m8.env; gcloud compute ssh matlab-vm5 "${VM5[@]}" --command='D=$(ls -td /tmp/lote3s_* 2>/dev/null | head -1); cd ~/ua-dd-saea && ~/venvs/env_main/bin/python -c "
import json, collections, sys
d = sys.argv[1]
L = [l.split() for l in open(d + \"/done.txt\")]
F = [x for x in L if len(x) > 4 and x[4] == \"failed\"]
mot = collections.Counter(); alg = collections.Counter(); ex = []
for r in F:
    e, a, p, s = r[0], r[1], r[2], r[3]
    alg[e + \"/\" + a] += 1
    f = \"data/experiments/%s/%s/exp_%s_%s_%s_%s.manifest.json\" % (e, a, e, a, p, s)
    try: m = json.load(open(f))
    except Exception: mot[\"SEM_MANIFESTO\"] += 1; continue
    k = str(m.get(\"motivo_parada\") or \"?\")
    mot[k] += 1
    if k not in (\"teto_wall\",) and len(ex) < 3:
        t = (m.get(\"stack_trace\") or \"\").strip().splitlines()
        ex.append((e + \"/\" + a, p, s, k, t[-1][:130] if t else \"-\"))
print(\"  total\", len(F), \"|\", dict(mot))
print(\"  por alg\", dict(alg.most_common(6)))
for x in ex: print(\"  ex\", x)
" "$D"'
```

**Como classificar o que sair:**

| `motivo_parada` | o que é | ação |
|---|---|---|
| `teto_wall` | **classe sancionada** (DI-38a). Domina em `c154`/`c262`/`c122`/`c149`; o próprio modelo já prevê que `c154` com D≥12 aborte. As camadas parciais são gravadas. | nenhuma |
| `checkpoint_em_andamento` com `ModelFittingError` / gradiente `NaN` / `random_search_optimizer` | falha numérica legítima do BoTorch. `WFG1` faz isso nas 4 máquinas em sementes distintas ⇒ é **propriedade do problema**, resultado científico | nenhuma — anotar |
| `SEM_MANIFESTO` ou `FileNotFoundError …/venvs/…` | **defeito de ambiente** (foi o caso do symlink, §4 nº 4) | **PARE e reporte** |

Referência da frota (06/08): ~87 % `teto_wall`, ~10 % numérico do BoTorch. Uma
máquina saudável fica em **3-4 % de falhas** sobre as células despachadas; a
`vm4` chegou a 16 % e isso denunciou o defeito do symlink.

---

## §7 · RELATÓRIO FINAL (traga isto de volta ao chat mestre)

```
VM: matlab-vm5 · n2-highmem-48 · us-east4-a · 24 jobs
B1 sonda .............. [ ] nproc=48, RAM=377G
B2 kit ................ [ ] startup.m md5 3e06ae44…
B3 bootstrap .......... [ ] PARTE A CONCLUIDA, zero FALHOU, libpython PRESENTE
B4 licenca ............ [ ] 25.1.0.2973910 (6a sessao concorrente: OK / recusada?)
B5 venvs .............. [ ] 3.11.9×3, 3.7.x, 3.8.x + gcs + symlinks
B6 pre-requisitos ..... [ ] 751/25/785, md5 batendo, CID no nohup, driver novo
B7 ponte .............. [ ] PONTE_NUMPY_OK + 3 algs em /home/gmello/venvs/env_b5
B8 portao ............. [ ] LEITURA OK + lote ok + portoes (verde/poda esperada)
B9 dry-run ............ [ ] sementes=42,9,8,28,27,7,26 · celulas=~3666
B10 disparo ........... [ ] ✅ vm5 NO AR
Painel apos 30 min .... [ ] RODANDO=24, ok subindo, failed baixo
Imprevistos: ...
```
