# DISPARO DA RODADA-42 — passo a passo, máquina por máquina

> **690 células · 357 h-core estimadas · makespan previsto ~14 h** com as quatro máquinas
> a 75% dos núcleos físicos. Ordem de disparo: **v5 → v6 → vm3 → Mac**.
>
> Dois arquivos novos fazem todo o trabalho: `preflight42.sh` (checagem read-only) e
> `lote42.sh` (disparador único, Python **e** MATLAB, com contador ao vivo).

---

## 0 · A alocação, e por que ela é essa

| máquina | proc | células | h-core | makespan | o que roda |
|---|---|---|---|---|---|
| **v5-mestrado** | 12 | 25 | 147,1 | ~14,0 h | `main/c154` (só isso — é 41% de toda a rodada) |
| **mestrado-v6** | 6 | 40 | 83,2 | ~14,7 h | `main/c262` · `batch/c262` · `batch/c149` · `batch/sobol_batch` |
| **matlab-vm3** | 6 | 395 | 79,8 | ~13,5 h | **todo o MATLAB** (12 configs do `main` + `e103` em `off`/sweeps) + `main/c122` + `main/c149` |
| **Mac A** | 4 | 230 | 49,7 | ~12,5 h | **tudo que exige venv exótico**: `env_b5` (b5r/b5m/moead_media), `env_c311` (c311/treed_media), `env_e81_qpots` (e81) |

Quatro restrições moldaram isso, nesta ordem de força:

**1. O venv manda mais que a CPU.** `src/experiment.run()` roteia `b5r`, `b5m`, `moead_media`,
`c311`, `treed_media` e `e81` obrigatoriamente para venvs próprios (D79/N.1.2) — e os caminhos
desses venvs no `envs.json` são **do Mac**. O Mac é a única máquina onde eles estão provados
(provisionados em 22/07). Por isso o Mac ficou com exatamente esses 230 células, e nada mais.
Se o pré-voo mostrar que as VMs também têm `env_b5`, dá para mover `off/b5m` (19,6 h-core) para
a v6 e encurtar o Mac — mas isso é resultado do pré-voo, não suposição.

**2. MATLAB só existe no Mac e na vm3.** Como o Mac está ocupado com os venvs exóticos, **todo
o MATLAB foi para a vm3** — 345 células, 40,8 h-core. Sobrou folga lá, preenchida com
`main/c122` e `main/c149` (env_main, que existe em toda máquina).

**3. 75% dos núcleos FÍSICOS, não dos vCPU.** v5 = 16 físicos → 12 · v6 e vm3 = 8 físicos → 6 ·
Mac = 8 → **4, e aqui quem manda é a RAM**: 16 GiB / 6 daria 2,7 GiB por processo, abaixo dos
~3,3 GiB medidos de uma célula pesada. Com 4, são 4 GiB. O pré-voo confere isso e avisa.

**4. Um config, uma máquina** (O-16). Nenhum `(exp, alg)` foi partido entre máquinas — a rodada-42
**é** o piloto de timing do M7, e misturar CPUs dentro de um config contamina justamente a medida
que a tabela do M7 vai reportar.

### O que o `lote42.sh` faz que o despachante nativo não faz

- **Pino de thread real, 1 core por run** (D79). O caminho joblib do `experiments.py` divide os
  núcleos por `n_jobs` e furou o pino na validação cruzada (O-15: 4 threads por processo na vm3,
  2 no Mac, 1 nas Vertex). Sem o driver, a tabela de timing do M7 nasce contaminada.
- **Contador ao vivo** — `[███████░░░] 213/395 (53,9%) · ok=213 falhou=0 pulou=0 · 02h11m · ETA ~04h50m`,
  atualizado a cada 15 s, tanto em Python quanto em MATLAB.
- **Ordem híbrida.** Tudo que dura menos de 15 min sai primeiro (barato→caro), o resto depois
  (caro→barato). Na vm3 isso põe **288 das 395 células no placar na primeira hora** sem alongar
  o makespan em nada (13,5 h nas duas ordens). Ordem pura barato→caro custaria +5 h na v6.
- **MATLAB sem `parfor`** — um processo `matlab -batch` por célula, cada um com sua ponte
  InProcess. É o que contorna a DI-34 e recupera o stderr que o `parfor` engolia.

O custo de cada célula vem de **interpolação log-log entre os walls medidos** da R1/R2 (âncoras em
FE 61 / 371 / 929, mais as duas do REGISTRO D-05). Serve só para ordenar a fila e estimar ETA —
não entra em resultado nenhum.

---

## 1 · Antes de tudo: levar os dois scripts para as quatro máquinas

Do terminal do Mac:

```bash
cd ~/Downloads     # ou onde você baixou lote42.sh e preflight42.sh
chmod 644 lote42.sh preflight42.sh          # scp entrega 600; sem isto o jupyter não lê (O-03)

V5=(--zone=us-central1-a --project=skilled-text-480300-d9        --account=gdmello.nunes@gmail.com)
V6=(--zone=us-central1-a --project=project-2aa33d8c-94a7-488b-89e --account=invest.gdmn@gmail.com)
V3=(--zone=us-central1-a --project=project-2aa33d8c-94a7-488b-89e --account=invest.gdmn@gmail.com)

gcloud compute scp lote42.sh preflight42.sh "${V5[@]}" v5-mestrado:/tmp/
gcloud compute scp lote42.sh preflight42.sh "${V6[@]}" mestrado-v6:/tmp/
gcloud compute scp lote42.sh preflight42.sh "${V3[@]}" invest_gdmn@matlab-vm3:~/
cp lote42.sh preflight42.sh ~/                                   # o próprio Mac
```

Nas duas Vertex (v5 e v6) o repo é do usuário `jupyter`, então os scripts precisam ir de `/tmp`
para lá depois do `sudo -u jupyter -i`. Está no passo de cada máquina.

---

## 2 · `v5-mestrado` — o pau-mandado mais longo, dispare PRIMEIRO

25 células de `main/c154`, 147 h-core, ~14 h. É o gargalo da rodada: quanto antes começar, antes
a rodada inteira acaba.

```bash
gcloud compute ssh v5-mestrado "${V5[@]}"
sudo -u jupyter -i                       # ← rode SOZINHO e espere o prompt trocar (O-13)
```

Já como `jupyter`:

```bash
cp /tmp/lote42.sh /tmp/preflight42.sh ~/ && chmod 644 ~/lote42.sh ~/preflight42.sh
PRE_MAQ=v5 bash ~/preflight42.sh
```

**Só siga se fechar VERDE.** Se aparecer bloqueio, pare e me mande a saída (D81).

```bash
LOTE_MAQ=v5 bash ~/lote42.sh             # DRY-RUN: mostra a grade e as 12 primeiras
```

Confira: `células: 25 (python 25 · matlab 0)` e `custo estimado: ~147 h-core`. Aí sim:

```bash
tmux new -s lote42
# DENTRO do tmux:
LOTE=CONFIRMA LOTE_MAQ=v5 bash ~/lote42.sh
# desanexar: Ctrl+B, solta, aperta D
```

⚠ **12 das 25 células vão fechar `failed/teto_wall`** — é o aborto por projeção do c154, previsto
pela DI-38(a)/DI-40, ~6,3 h cada, sem gravar parquet. **Não é falha e não deve ser re-disparado.**
O próprio script lembra disso no fim.

---

## 3 · `mestrado-v6` — c262 online + o sub-estudo batch

```bash
gcloud compute ssh mestrado-v6 "${V6[@]}"
sudo -u jupyter -i                       # sozinho, espere o prompt
```

```bash
cp /tmp/lote42.sh /tmp/preflight42.sh ~/ && chmod 644 ~/lote42.sh ~/preflight42.sh
PRE_MAQ=v6 bash ~/preflight42.sh
LOTE_MAQ=v6 bash ~/lote42.sh             # dry-run: 40 células, ~83 h-core
tmux new -s lote42
LOTE=CONFIRMA LOTE_MAQ=v6 bash ~/lote42.sh
```

⚠ **RAM.** As 5 células de `batch/c262` vão a n=2109 e são as mais pesadas de memória da rodada
inteira (o auditor registrou um probe OOM-killed em n=669 numa máquina de 16 GB). A ordem híbrida
já ajuda — elas são as mais caras, então caem no **fim** da fila, quando as outras já terminaram
e no máximo 5 processos disputam os 62 GiB. Mesmo assim, olhe o `free -g` quando o contador passar
de ~35/40. Se apertar, `Ctrl+C` e religue com `LOTE_JOBS=3` — a esteira é idempotente (D58), nada
se perde.

O custo de `batch/c262` é o **único número estimado** de toda a tabela (4 h/célula). Nunca foi
medido. Se ele desviar muito, a previsão da v6 desvia junto.

---

## 4 · `matlab-vm3` — todo o MATLAB + dois configs Python

395 células, mas 345 delas são MATLAB barato. É a máquina onde o contador voa.

```bash
gcloud compute ssh invest_gdmn@matlab-vm3 "${V3[@]}"
command -v tmux || sudo apt-get install -y tmux
PRE_MAQ=vm3 bash ~/preflight42.sh
LOTE_MAQ=vm3 bash ~/lote42.sh            # dry-run: 395 células (python 50 · matlab 345)
tmux new -s lote42
LOTE=CONFIRMA LOTE_MAQ=vm3 bash ~/lote42.sh
```

O pré-voo aqui é o mais importante dos quatro, porque é o único que precisa de MATLAB **e** de
env_main ao mesmo tempo. Se o MATLAB não aparecer, o script para antes de disparar.

Espere ver o contador em ~**288/395 na primeira hora** — são os pisos MOEA (`nsga2`, `nsga3`,
`moead`, `smsemoa`, ~1 s cada), o `e103` e os configs leves. O que sobra depois é `e7` (~35 min/cél),
`c238` (~44 min/cél) e `c149` (~68 min/cél), que ocupam o resto das 13 h.

⚠ **Olhe a RAM nas primeiras células de `e7`** — ~3,3 GiB por run medidos no Mac. Seis processos
dariam ~20 GiB dos 62 GiB: folga confortável, mas nunca foi medido com 6 MATLABs completos.

---

## 5 · Mac A — os venvs exóticos

```bash
cd ~
PRE_MAQ=mac bash ~/preflight42.sh
LOTE_MAQ=mac bash ~/lote42.sh            # dry-run: 230 células, ~50 h-core
tmux new -s lote42
LOTE=CONFIRMA LOTE_MAQ=mac bash ~/lote42.sh
```

Se você não usa `tmux` no Mac, `caffeinate -i` na frente resolve o sono da máquina:

```bash
caffeinate -i bash -c 'LOTE=CONFIRMA LOTE_MAQ=mac bash ~/lote42.sh'
```

⚠ **`env_b5` e `env_c311` rodam sob Rosetta** (x86_64, py3.7 e py3.8). São 4 processos traduzidos
concorrentes num M1 Pro — se a máquina engasgar, `LOTE_JOBS=3` e siga.

⚠ **`gsutil ls` falha no Mac** (sabido); o caminho Python (`storage.Client`), que é o que o
`mirror_run` usa, está verde. O pré-voo testa o caminho certo.

---

## 6 · Acompanhar de fora, sem entrar no tmux

```bash
gcloud compute ssh v5-mestrado "${V5[@]}" --command='tail -c 400 /dev/null; \
  sudo -u jupyter tmux capture-pane -pt lote42 | tail -3; free -g | head -2'
```

Ou, direto na máquina, o painel do próprio repo (que lê os `.jsonl`, não o driver):

```bash
$PY scripts/progress.py --watch
```

Reanexar: `tmux attach -t lote42`.

**Se cair a conexão, a queda não custa nada** — o `tmux` segura o processo, e a esteira é
idempotente (D58). Reconectou, re-executa o mesmo comando: as células prontas aparecem como
`pulou` em segundos.

---

## 7 · O QUE NÃO É FALHA

- **12 células `failed` de `c154` na v5** — aborto por projeção, previsto (DI-38a/DI-40).
- **Ausência total de `c154` no `batch`** — retirado pela DI-40.
- **`pulou` em massa ao re-executar** — é a idempotência D58 funcionando.
- **Contagem de testes diferente entre máquinas** — critério é `Ran ≥ 328 OK`, nunca igualdade.
- **`ger` diferente entre máquinas no mesmo config** — permitido (RUNBOOK §6.2, O-16).

---

## 8 · Fechamento, quando os quatro lotes terminarem

```bash
$PY scripts/portao.py --varredura        # esperado: verde, ~12 ⚪ do c154, zero vermelho
$PY scripts/progress.py --tabela         # ESTA tabela é o M7
```

Resgatar os dados MATLAB da vm3 para o Mac (a vm3 não usa bucket — decisão (b)):

```bash
gcloud compute scp --recurse "${V3[@]}" \
  invest_gdmn@matlab-vm3:~/ua-dd-saea/data/experiments \
  ~/Documents/python_repos/mestrado/ua-dd-saea/data/
```

Só **depois** disso: `git pull` nas máquinas e a sessão do Claude Code com o
`PROMPT_CC_decisoes_pre_disparo.md`.

---

## 9 · Uma decisão que é sua, e que muda a rodada em 40%

O `main/c154` sozinho custa **147 h-core — 41% de toda a rodada-42** — e, pelo modelo,
**12 das 25 células abortam sem gravar parquet nenhum**, queimando ~75 h-core para produzir
apenas `jsonl` + manifesto `failed`.

A DI-40 já fez essa conta para o `batch` e retirou o c154 de lá. Para o `main` ela decidiu o
contrário — manter as 25 células, porque "o comportamento dele sob orçamento apertado é parte do
que a dissertação mede" — mas o número que embasou aquela decisão era a classe D=12/M=3 mais o
ZDT1, **~11 células**. Com a interpolação sobre os walls medidos, a classe que estoura é maior:
todo problema com maxFE ≥ 371, ou seja **DTLZ1–4, DTLZ7, WFG1/2/4/5/9, MMF16_20, ZDT1 e ZDT3 = 12
células**, mais 9 células de FE=309 que completam mas levam ~7,7 h cada.

Se você retirar as 12 abort-certas, a rodada cai de 357 para ~282 h-core e o makespan de ~14 h
para ~11 h. **Eu não decido isso** (D97/D81) — é julgamento de evidência, não de custo. Fica
registrado com o número na mão, para você bater o martelo antes ou depois do disparo (depois
também serve: a esteira é idempotente, basta não re-disparar).
