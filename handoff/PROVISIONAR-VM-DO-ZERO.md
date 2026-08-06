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

## §3 · POR QUE ESTAS SEMENTES (`42 9 8 28 27 7 26`)

A campanha termina quando **cada** semente estiver completa **por alguém**. Estas
sete são as que hoje sairiam por último (as caudas das filas de `vm1`, `vm3` e
`vm4`). Cobrindo-as, o caminho crítico cai de ~19/08 para ~14/08.

`LOTE_ORDEM=semente` põe TODA a semente na fila — da célula mais barata à mais
cara — antes de passar à seguinte, na ordem em que aparecem em `LOTE_SEEDS`.
Logo a `s42` (a mais atrasada) sai primeiro. Se a `vm5` não chegar às últimas da
lista, as irmãs as cobrem de qualquer forma — não há perda.

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

## §6 · RELATÓRIO FINAL (traga isto de volta ao chat mestre)

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
Imprevistos: ...
```
