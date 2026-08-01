# M8 — BATCHES DO OPERADOR (comandos prontos, na ordem)

> **O que é.** Todo comando que o operador precisa colar, do estado de
> 2026-08-01 até o disparo do M8, em batches numerados e auto-contidos.
> Companheiro de `PROVISIONAMENTO-M8-FROTA.md` (o *porquê*) — aqui é só o *como*.
>
> **Convenções, sem exceção:** saída sempre redirecionada (`> log 2>&1`), **nunca
> pipe com MATLAB** (o `MathWorksServiceHost` trava) · nenhum caminho de saída
> silencioso (`|| echo "FALHOU: …"`) · valores que diferem entre máquinas em
> linha própria com `# <<<` · logs em `$HOME` com o nome da máquina, nunca em
> `/tmp` · **`exit=0` não é veredito** (manda a linha `[placar]` e o rodapé do
> `.jsonl`) · fuso: VMs em **UTC**, operador em **GMT-3**.
>
> ⚠ **Nomenclatura:** leia a §0.2 do `PROVISIONAMENTO-M8-FROTA.md` antes de
> qualquer coisa. A `vm1` DESTE documento é a máquina NOVA; a que os documentos
> antigos chamam de `vm1` é hoje a **`vm2`**.

---

## B-0 · A identidade da frota (rode UMA vez por terminal novo)

Quatro contas diferentes, quatro projetos diferentes. Errar a conta produz um
403 que **parece** falta de permissão e não é — é a armadilha nº 1 do projeto.

```bash
cat > ~/frota_m8.env <<'EOF'
# Frota M8 (2026-08-01). Uso: gcloud compute ssh matlab-vm3 "${VM3[@]}" --command='...'
VM1=(--account=gdmello.nunes@gmail.com --project=skilled-text-480300-d9 --zone=us-east1-b)
VM2=(--account=melloguinn@gmail.com --project=core-cascade-341902 --zone=us-east1-b)
VM3=(--account=invest.gdmn@gmail.com --project=project-2aa33d8c-94a7-488b-89e --zone=us-east1-b)
VM10=(--account=mellohr@gmail.com --project=project-0a70dd69-8e73-4d58-819 --zone=us-east1-b)
EOF
source ~/frota_m8.env && echo "frota carregada: vm1=${#VM1[@]} vm2=${#VM2[@]} vm3=${#VM3[@]} vm10=${#VM10[@]} flags cada" || echo "FALHOU: carregar frota"
```

Esperado: `vm1=3 vm2=3 vm3=3 vm10=3 flags cada`. ⚠ Em zsh, **array vazio expande
para um argumento vazio**, não para nenhum — se algum vier `0`, o `source` não
pegou e todo comando adiante falha com `unrecognized arguments:` sem nada depois.

---

## B-1 · Os 5 venvs da `matlab-vm1` nova  *(pré-req: `parte_a.sh` concluído)*

Confira primeiro que a Parte A fechou sem `FALHOU` e que a `libpython` existe —
sem ela a ponte A2 não carrega e o MATLAB não avalia problema nenhum:

```bash
source ~/frota_m8.env; gcloud compute ssh matlab-vm1 "${VM1[@]}" --command='echo "--- FALHAS na parte A ---"; grep FALHOU ~/parte_a.log || echo "(nenhuma)"; echo "--- fim do log ---"; tail -3 ~/parte_a.log; echo "--- libpython (SEM ela a ponte A2 morre) ---"; ls -1 ~/.pyenv/versions/3.11.9/lib/libpython3.11.so* 2>/dev/null || echo "AUSENTE - recompilar 3.11.9 com --enable-shared, nao remendar"; echo "--- matlab ---"; matlab -batch "disp(version)" > /tmp/ver.log 2>&1; cat /tmp/ver.log' 2>&1 || echo "FALHOU: checar parte A"
```

Esperado: nenhuma linha `FALHOU`, `libpython3.11.so` presente, versão
`25.1.0.2973910`. Se o MATLAB pedir login, faça a licença **antes** (interativo,
**sem redirect e sem timeout** — é a única exceção à regra do redirecionamento):

```bash
source ~/frota_m8.env; gcloud compute ssh matlab-vm1 "${VM1[@]}"
# já dentro da VM:  pkill -9 -f MathWorksServiceHost; pkill -9 -f MATLABConnector; sleep 3; matlab -nodisplay
# conta: mello.guilherme@dcc.ufmg.br   ·   "Licensing shutdown" na 1a tentativa? repita, e' soluco conhecido
```

### B-1.1 — enviar o script dos venvs

```bash
source ~/frota_m8.env; gcloud compute ssh matlab-vm1 "${VM1[@]}" --command='cat > ~/venvs_m8.sh' <<'VENVS'
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
# Sem --no-deps o pip tenta reconciliar a arvore inteira contra o 3.7: ou trava
# por horas, ou instala versao diferente do lock e viola D80 EM SILENCIO.
micromamba create -y -q -n env_b5 python=3.7 \
  && micromamba run -n env_b5 pip install -q --no-deps -r "$L/env_b5.lock.txt" \
  && ok env_b5 || ko env_b5

echo "=== env_c311 (py3.8) — GPy ANTES do resto, com --no-build-isolation ==="
# GPy 1.9.9 tem extensao Cython que exige numpy JA presente em tempo de build.
# Com isolamento, o pip cria um ambiente limpo sem numpy e o build quebra com um
# erro de gcc que nao menciona numpy — uma hora perdida lendo log errado.
micromamba create -y -q -n env_c311 python=3.8 \
  && micromamba run -n env_c311 pip install -q "GPy==1.9.9" --no-build-isolation \
  && micromamba run -n env_c311 pip install -q --no-deps -r "$L/env_c311.lock.txt" \
  && ok env_c311 || ko env_c311

echo
echo "=== CONFERENCIA ==="
for E in env_bridge env_main env_e81_qpots; do
  V=$("$HOME/venvs/$E/bin/python" -c "import sys;print('.'.join(map(str,sys.version_info[:3])))" 2>&1)
  echo "  $E -> $V"
done
for E in env_b5 env_c311; do
  V=$(micromamba run -n $E python -c "import sys;print('.'.join(map(str,sys.version_info[:3])))" 2>&1)
  echo "  $E -> $V"
done
echo "########## VENVS CONCLUIDO $(date -u) ##########"
echo "Esperado: bridge/main/e81 = 3.11.9 · b5 = 3.7.x · c311 = 3.8.x"
VENVS
```

### B-1.2 — disparar (leva ~20-40 min; o `env_c311` é o demorado)

```bash
source ~/frota_m8.env; gcloud compute ssh matlab-vm1 "${VM1[@]}" --command='chmod +x ~/venvs_m8.sh && nohup ~/venvs_m8.sh > ~/venvs_m8.log 2>&1 & sleep 20; tail -5 ~/venvs_m8.log' 2>&1 || echo "FALHOU: disparar venvs"
```

Acompanhe com `tail -30 ~/venvs_m8.log`. Ao fim, **nenhuma linha `FALHOU`**.

### B-1.3 — o `startup.m` (COPIADO da vm3, não digitado)

O `startup.m` mora no **userpath** (`~/Documents/MATLAB/`), com `addpath`
**absoluto**, e tem de ser **byte-idêntico** ao das outras (md5
`3e06ae44c9dba0d9fc1e9724f0878347`). Copiar da vm3 elimina risco de encoding —
foi assim que a vm10 foi provisionada. Ele **não vai para o repositório**.

```bash
source ~/frota_m8.env; gcloud compute scp "${VM3[@]}" matlab-vm3:'~/Documents/MATLAB/startup.m' /tmp/startup.m 2>&1 && md5 -q /tmp/startup.m && echo "esperado: 3e06ae44c9dba0d9fc1e9724f0878347" || echo "FALHOU: baixar startup.m da vm3"
```

```bash
source ~/frota_m8.env; gcloud compute ssh matlab-vm1 "${VM1[@]}" --command='mkdir -p ~/Documents/MATLAB' 2>&1 && gcloud compute scp "${VM1[@]}" /tmp/startup.m matlab-vm1:'~/Documents/MATLAB/startup.m' 2>&1 && gcloud compute ssh matlab-vm1 "${VM1[@]}" --command='md5sum ~/Documents/MATLAB/startup.m; echo "--- a ponte, sob -batch (o startup.m tem de rodar SOZINHO) ---"; matlab -batch "disp(pyenv().Version); disp(char(pyenv().ExecutionMode)); assert(double(py.numpy.array([1,2,3]).sum())==6); disp(\"PONTE_NUMPY_OK\")" > /tmp/ponte.log 2>&1; cat /tmp/ponte.log' 2>&1 || echo "FALHOU: instalar startup.m na vm1"
```

Esperado: md5 `3e06ae44…` · `3.11` · `InProcess` · `PONTE_NUMPY_OK`.
Um smoke que configura a ponte *inline* prova capacidade, **não persistência** —
por isso este roda `-batch` puro, sem `pyenv(...)` na linha.

---

## B-2 · Artefatos pré-requisito nas 4 máquinas  *(o item que nenhum doc de VM cobria)*

O runner **se recusa** a gerar estes três (pára-e-loga, D81). Sem `datasets`,
**toda** célula `off/` e `sweep-*` aborta — e são 230 das 695 células por semente.

**Referência medida no Mac:** `doe` 751/751 (27 MB) · `sonda` 25/25 (71 MB) ·
`datasets` 785/785 (171 MB).

### B-2.1 — empacotar UMA vez no Mac

```bash
cd ~/Documents/python_repos/mestrado/ua-dd-saea && tar -czf /tmp/ua_prereq.tgz data/doe data/sonda data/datasets && ls -lh /tmp/ua_prereq.tgz && md5 -q /tmp/ua_prereq.tgz || echo "FALHOU: empacotar pre-requisitos"
```

### B-2.2 — enviar e extrair (uma máquina por vez; troque as 3 marcas `# <<<`)

⚠ `--skip-old-files` é o `cp -n` do tar: **nunca sobrescreve** artefato que já
existe. Artefato regenerado = hash novo = comparação contaminada em silêncio.

```bash
source ~/frota_m8.env
M=matlab-vm1; F=("${VM1[@]}")          # <<< vm1  (troque para vm2/VM2, vm3/VM3, vm10/VM10)
gcloud compute scp "${F[@]}" /tmp/ua_prereq.tgz "$M":/tmp/ua_prereq.tgz 2>&1 && gcloud compute ssh "$M" "${F[@]}" --command='cd ~/ua-dd-saea && md5sum /tmp/ua_prereq.tgz && tar -xzf /tmp/ua_prereq.tgz --skip-old-files && echo "--- contagens (esperado 751/751 · 25/25 · 785/785) ---" && for d in doe sonda datasets; do echo "  $d: $(find data/$d -name "*.parquet" | wc -l) parquet / $(find data/$d -name "*.manifest.json" | wc -l) sidecar / $(du -sh data/$d | cut -f1)"; done && echo "--- md5 de amostra (tem de bater com o Mac) ---" && md5sum data/sonda/sonda_MMF1.parquet data/doe/ZDT1/doe_ZDT1_0.parquet' 2>&1 || echo "FALHOU: artefatos em $M"
```

Amostra de conferência no Mac, para comparar:

```bash
cd ~/Documents/python_repos/mestrado/ua-dd-saea && md5 -q data/sonda/sonda_MMF1.parquet && md5 -q data/doe/ZDT1/doe_ZDT1_0.parquet || echo "FALHOU: md5 de amostra no Mac"
```

---

## B-3 · Exports por máquina (P11 — o item novo mais importante)

`UA_DD_SAEA_CAMPANHA_ID` **não é exportada pelo driver**. O default deriva da
**data UTC** — numa campanha de ~13 dias ele muda no meio, o `is_run_done` deixa
de reconhecer as células dos dias anteriores e o resume tenta **re-rodar tudo**
(com 403 no bucket nas máquinas sem `delete`). Tem de ser **idêntica na frota
inteira**, cravada uma vez.

Primeiro, no Mac, gere o valor (⚠ **depois** de a tag existir — B-5):

```bash
cd ~/Documents/python_repos/mestrado/ua-dd-saea && echo "UA_DD_SAEA_CAMPANHA_ID=$(git rev-parse --short=12 m8-freeze)_M8" || echo "FALHOU: derivar campanha_id (a tag m8-freeze existe?)"
```

Depois, uma máquina por vez — **cole o MESMO `CID` nas quatro**:

```bash
source ~/frota_m8.env
M=matlab-vm1; F=("${VM1[@]}"); HOST=vm1     # <<< maquina (vm1|vm2|vm3|vm10)
CID="COLE_AQUI_O_VALOR_DO_COMANDO_ACIMA"    # <<< IDENTICO nas 4
gcloud compute ssh "$M" "${F[@]}" --command="grep -q UA_DD_SAEA_CAMPANHA_ID ~/.bashrc || printf '%s\n%s\n' 'export UA_DD_SAEA_HOST=$HOST' 'export UA_DD_SAEA_CAMPANHA_ID=\"$CID\"' >> ~/.bashrc; grep -q UA_DD_SAEA_CAMPANHA_ID ~/.profile || printf '%s\n%s\n' 'export UA_DD_SAEA_HOST=$HOST' 'export UA_DD_SAEA_CAMPANHA_ID=\"$CID\"' >> ~/.profile; echo '--- conferindo em shell NAO-interativo (o do nohup) ---'; bash -lc 'echo HOST=\$UA_DD_SAEA_HOST CAMPANHA=\$UA_DD_SAEA_CAMPANHA_ID'" 2>&1 || echo "FALHOU: exports em $M"
```

Os dois arquivos (`.bashrc` **e** `.profile`) porque login-shell e não-login lêem
arquivos diferentes — é a pegadinha que já fez o pyenv "sumir" nas VMs.

---

## B-4 · Higiene (P12)

```bash
source ~/frota_m8.env; for X in "matlab-vm1|VM1" "matlab-vm2|VM2" "matlab-vm3|VM3" "matlab-vm10|VM10"; do M="${X%%|*}"; N="${X##*|}"; eval "F=(\"\${$N[@]}\")"; echo "===== $M ====="; gcloud compute instances describe "$M" "${F[@]}" --format='value(name,status,deletionProtection,machineType.basename())' 2>&1 || echo "FALHOU: describe $M"; done
```

Esperado: as quatro `RUNNING` e `True`. Remover o beco sem saída da vm10:

```bash
source ~/frota_m8.env; gcloud compute ssh matlab-vm10 "${VM10[@]}" --command='rm -rf ~/ua-dd-saea/data_xmachine && git -C ~/ua-dd-saea status --porcelain | head -5; echo "(vazio = arvore limpa)"' 2>&1 || echo "FALHOU: limpar data_xmachine"
```

---

## B-5 · `git pull` + suíte nas 4  🔒 *BLOQUEADO até a tag existir*

Regra do projeto: **`git pull` somente após o aviso de congelamento do autor.**
As VMs estão na era "394 testes"; o repo congelado tem **826**.

```bash
source ~/frota_m8.env; for X in "matlab-vm1|VM1" "matlab-vm2|VM2" "matlab-vm3|VM3" "matlab-vm10|VM10"; do M="${X%%|*}"; N="${X##*|}"; eval "F=(\"\${$N[@]}\")"; echo "===== $M ====="; gcloud compute ssh "$M" "${F[@]}" --command='cd ~/ua-dd-saea && git pull --ff-only 2>&1 | tail -3 && git log -1 --format="HEAD %h %s" && ~/venvs/env_main/bin/python -m unittest discover -s tests > ~/suite_$(hostname).log 2>&1; tail -3 ~/suite_$(hostname).log' 2>&1 || echo "FALHOU: pull/suite em $M"; done
```

Esperado em cada uma: **`Ran 826`** · **`OK`** · `skipped≈36`. **Qualquer outro
número ⇒ pare** (D81).

---

## B-6 · Drivers novos nas máquinas (P10)

Os `~/lote3s.sh` das VMs são da era rodada-42 e **não conhecem o mapa de
sementes** nem o `LOTE_ORDEM=semente`. ⚠ Nunca sobrescrever script **em
execução** — o bash lê o arquivo incrementalmente.

```bash
source ~/frota_m8.env; for X in "matlab-vm1|VM1" "matlab-vm2|VM2" "matlab-vm3|VM3" "matlab-vm10|VM10"; do M="${X%%|*}"; N="${X##*|}"; eval "F=(\"\${$N[@]}\")"; echo "===== $M ====="; gcloud compute ssh "$M" "${F[@]}" --command='pgrep -f "lote3s\.sh" >/dev/null && { echo "ABORTADO: ha lote RODANDO nesta maquina"; exit 1; }; cp ~/ua-dd-saea/scripts/lote3s.sh ~/lote3s.sh && cp ~/ua-dd-saea/scripts/plano3s.sh ~/plano3s.sh && sha256sum ~/lote3s.sh ~/plano3s.sh && grep -c "ORDEM_INVALIDA" ~/lote3s.sh && echo "(1 = driver NOVO, com LOTE_ORDEM=semente)"' 2>&1 || echo "FALHOU: drivers em $M"; done
```

---

## B-7 · Portões de aceitação, por máquina (P13)

⚠ `accept.py` e `auditar.py` **ignoram `--data-root` POR DESENHO**
(`portao.py:94`) — a célula de aceitação **tem de viver em `data/`**. Smoke em
dataRoot isolado nunca passa nos portões 1 e 2; isso já custou dois lotes.

Use uma **semente da própria máquina no mapa**: vm1→0 · vm2→11 · vm10→15 · vm3→19.

```bash
source ~/frota_m8.env
M=matlab-vm1; F=("${VM1[@]}"); SEM=0        # <<< maquina e semente DELA no mapa
gcloud compute ssh "$M" "${F[@]}" --command="cd ~/ua-dd-saea && for A in nsga2 c154 c262; do echo \"--- portao main/\$A/MMF1/$SEM ---\"; ~/venvs/env_main/bin/python scripts/portao.py --exp main --alg \$A --problema MMF1 --semente $SEM > ~/portao_\${A}.log 2>&1; echo \"rc=\$? (rc NAO e veredito)\"; tail -4 ~/portao_\${A}.log; done" 2>&1 || echo "FALHOU: portoes em $M"
```

Esperado por config: `accept[...]=VERDE · auditar=VERDE` → **VERDE · 0 vermelhos**.
Cobertura: um stack MATLAB (`nsga2`, via ponte `py.`) e os **dois** BoTorch
(`c154`, `c262`) — que são os únicos que dependem da SONDA.

Depois, o **primeiro lote real PEQUENO e observado**, bucket DESLIGADO (nunca
começar por uma varredura de 33 h):

```bash
source ~/frota_m8.env
M=matlab-vm1; F=("${VM1[@]}"); SEM=0; JOBS=16; JIT=25    # <<< por maquina
gcloud compute ssh "$M" "${F[@]}" --command="cd ~/ua-dd-saea && LOTE=CONFIRMA LOTE_MAPA=0 LOTE_BUCKET=0 LOTE_ORDEM=semente LOTE_PARES='main/e74' LOTE_SEEDS=$SEM LOTE_JOBS=$JOBS LOTE_MATLAB_JITTER=$JIT LOTE_PRAZO_H=2 nohup bash ~/lote3s.sh > ~/lote_teste_\$(hostname).log 2>&1 & sleep 25; sed -n '1,30p' ~/lote_teste_\$(hostname).log" 2>&1 || echo "FALHOU: lote de teste em $M"
```

---

## B-8 · Resume bucket-aware com credencial real (P14)

Pendente desde o R2-00. Re-disparar uma célula **já concluída nesta campanha**
com o bucket LIGADO tem de dar **SKIP**, sem upload novo.

⚠ Uma célula da **rodada-42** NÃO vai dar skip — o manifesto dela é v1, sem
`campanha_id`, e o `is_run_done` reprova por desenho (B-03). Isso é **correto**,
não é bug. Use uma célula que a **própria campanha M8** acabou de gravar (B-7).

```bash
source ~/frota_m8.env
M=matlab-vm1; F=("${VM1[@]}"); SEM=0        # <<<
gcloud compute ssh "$M" "${F[@]}" --command="cd ~/ua-dd-saea && LOTE=CONFIRMA LOTE_MAPA=0 LOTE_BUCKET=1 LOTE_ORDEM=semente LOTE_PARES='main/e74' LOTE_SEEDS=$SEM LOTE_JOBS=2 LOTE_REFAZER=nao bash ~/lote3s.sh > ~/resume_\$(hostname).log 2>&1; grep -E 'skip|ja tinham manifesto|grid' ~/resume_\$(hostname).log | head -10" 2>&1 || echo "FALHOU: teste de resume em $M"
```

Esperado: a grade sai **vazia** (`já tinham manifesto`) e nada é re-executado.
Se re-rodar ou tentar upload, **PARE** — é o cenário que destruiria a campanha no
segundo dia.

---

## B-9 · DISPARO M8 🚀

Só com B-1 a B-8 verdes. **Uma máquina por vez**, e **nunca dois lotes na mesma
máquina** — é a única corrupção irreversível desta operação.

As sementes saem do mapa (não passe `LOTE_SEEDS`): vm1 `[0–10]` · vm2 `[11–14]` ·
vm10 `[15–18]` · vm3 `[19–28, 42]`.

```bash
source ~/frota_m8.env
M=matlab-vm1; F=("${VM1[@]}"); MAQ=vm1; JOBS=16; JIT=25   # <<< vm2/vm10: JOBS=6 · vm3: JOBS=16
gcloud compute ssh "$M" "${F[@]}" --command="cd ~/ua-dd-saea && LOTE=CONFIRMA LOTE_MAQ=$MAQ LOTE_BUCKET=1 LOTE_ORDEM=semente LOTE_JOBS=$JOBS LOTE_MATLAB_JITTER=$JIT nohup bash ~/lote3s.sh > ~/lote_M8_$MAQ.log 2>&1 & sleep 30; sed -n '1,40p' ~/lote_M8_$MAQ.log" 2>&1 || echo "FALHOU: disparo em $M"
```

Confirme no cabeçalho: a linha `── MAPA T14.11: <maq> recebeu N celulas-semente`
e a linha `[grid] … = N células`. **`LOTE_BUCKET` sempre explícito** — o
catch-all do driver liga o bucket sozinho (`BUCKET_DEF=1`), e em máquina sem
`objects.delete` isso vira 403.

Acompanhamento (read-only, de qualquer terminal):

```bash
source ~/frota_m8.env; for X in "matlab-vm1|VM1|vm1" "matlab-vm2|VM2|vm2" "matlab-vm3|VM3|vm3" "matlab-vm10|VM10|vm10"; do M="${X%%|*}"; R="${X#*|}"; N="${R%%|*}"; Q="${R##*|}"; eval "F=(\"\${$N[@]}\")"; echo "===== $M ====="; gcloud compute ssh "$M" "${F[@]}" --command="tail -4 ~/lote_M8_$Q.log; uptime" 2>&1 || echo "FALHOU: placar $M"; done
```

⚠ **Ctrl-C não para o lote** (ele roda em outro process group). Para parar:
`bash ~/plano3s.sh parar`, ou `pkill` **ancorado** (`pkill -f 'lote3s\.sh$'`) —
padrão frouxo tem falso positivo com facilidade.
