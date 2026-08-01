# HANDOFF — Operação multimáquina da campanha `ua-dd-saea`

**Versão 2 · data de corte: 2026-07-28**
v1 (27/07) cobria infraestrutura e o disparo das 3 sementes. v2 incorpora o handoff da torre auxiliar (27–28/07): censo do bucket, lotes de recuperação com teto ampliado, e o fechamento da semente 42. **As correções que eu faço ao documento auxiliar estão na §16** — leia-a antes de agir sobre a §5.1 ou a §10 dele.

**Operador:** Guilherme (PPGCC/UFMG, defesa ~set/2026, GMT-3)
**Repo:** `ua-dd-saea` · **Bucket:** `gs://mestrado_experiments` · **Projeto GCP principal:** `skilled-text-480300-d9`
**Papel a desempenhar:** engenheiro de operação da campanha — alocação de carga entre 4 máquinas, disparadores em bash, diagnóstico de falha, tabelas e figuras. **Não** decidir metodologia: isso é do autor (§7, §13).

---

## 0. Como usar este documento

§1–§3 para saber onde você está. **§12 antes de escrever uma linha de bash** — é o caderno de armadilhas, cada item custou de 20 min a 3 h. §10 é o fechamento da semente 42. §14 é o que precisa ser executado. §16 são as minhas correções ao handoff auxiliar.

`célula` = tupla (experimento, algoritmo, problema, semente). Unidade atômica de trabalho e de resultado.

---

## 1. Contexto humano

**Guilherme Mello** (`melloguinn@gmail.com`), mestrado no PPGCC/UFMG, defesa ~setembro/2026. GMT-3. Responda em português.

- Opera as máquinas num **grid 2×2 de terminais** e acompanha progresso ao vivo. Barra tipo tqdm foi pedido explícito.
- Quer **comandos prontos para colar, um por vez**, com o que esperar da saída. Diz claramente quando um comando não segue o paradigma que pediu — respeite ("não toco nos terminais em execução" significa que todo check é one-shot externo).
- **Cola saídas de terminal cruas.** Leia com atenção: várias vezes o diagnóstico estava numa linha que parecia ruído (o `Killed` do MATLAB, o `zsh: command not found: #`, o `-t` do gcloud).
- **Tem bom faro.** Quando disse "a v5 não está indo muito bem", a v5 estava bem e o *contador* estava errado. Trate as hipóteses dele como sérias e teste-as com número.
- **Prefere ser corrigido a ser agradado.** Retratações públicas de conclusão minha foram bem recebidas. Nenhum comando entregue a ele pode ter caminho de saída silencioso (§12.16).
- Enquadrou as células que não fecharam como *"o que não rodou vai virar aprendizado dessa rodada"* — e é isso mesmo (§10.4).

---

## 2. A tese e o que a campanha produz

Algoritmos **surrogate-assisted evolutionary** multiobjetivo com tratamento de incerteza (*uncertainty-aware, data-driven*). ~22 algoritmos × 25 problemas, sob orçamento de avaliações reais muito baixo.

| família | pasta | pergunta |
|---|---|---|
| **main online** | `main` | desempenho no regime online (resultado principal) |
| **main offline** | `off` | desempenho no regime offline (dataset fixo) |
| **swap offline** | `sweep-{small,medium,big}-{lhs,mvns}` | sensibilidade ao tamanho e à distribuição do DoE |
| **q10 (batch)** | `batch` | aquisição em lote q=10 |

`maxFE = 31·D − 1` no online; DoE inicial `11·D − 1`. `run_id = {exp}_{alg}_{problema}_{semente}` (D55).

---

## 3. A grade exata (verificada contra `runs_matrix.csv`)

**695 células por semente · 30 sementes = 20.850 runs.** Colunas do artefato: `run_id, exp, regime, alg, config, problema, semente, q, tier, dist, stack, env`.

| exp | células | algs | problemas |
|---|---|---|---|
| `main` | **425** | 17: b1 b3 b4 c122 c141 c149 c154 c217 c238 c262 e7 e74 e81 moead nsga2 nsga3 smsemoa | 25 |
| `off` | **125** | 5: b5m b5r c311 e103 moead_media | 25 |
| `sweep-{small,medium}-{lhs,mvns}` | 25 cada = **100** | 5: b5m b5r c311 e103 moead_media | 5 |
| `sweep-big-{lhs,mvns}` | 10 cada = **20** | 2: c311 treed_media | 5 |
| `batch` | **25** | 5: c149 c154 c262 e81 sobol_batch | 5 |

**Sementes sancionadas: `0..28` e `42` — 30 réplicas. A semente 30 NÃO existe.** O `lote3s.sh` tem guarda.

### Problemas e dimensões (`characteristics.csv`)

| D | maxFE | n | problemas |
|---|---|---|---|
| 2 | 61 | 3 | MMF1, MMF4, MMF11_L |
| 7 | 216 | 1 | DTLZ1 |
| 10 | 309 | 9 | ZDT4, ZDT6, BBOB_F1/F5/F17/F22/F37/F49/F55 |
| 12 | 371 | 3 | DTLZ2, DTLZ3, DTLZ4 |
| 20 | 619 | 1 | MMF16_20 |
| 22 | 681 | 6 | DTLZ7, WFG1, WFG2, WFG4, WFG5, WFG9 |
| 30 | 929 | 2 | ZDT1, ZDT3 |

Os 5 problemas de `batch` e `sweep`: DTLZ2, MMF16_20, WFG9, ZDT1, ZDT4.

### Stack por algoritmo

**MATLAB (13):** b1 b3 b4 c141 c217 c238 e7 e74 e103 moead nsga2 nsga3 smsemoa
**Python (11):** b5m b5r c122 c149 c154 c262 c311 e81 moead_media sobol_batch treed_media

### O que realmente determina a alocação: o ambiente, não a CPU

| classe | células/semente | h-core/semente | onde PODE rodar |
|---|---|---|---|
| MATLAB | **345** | 41,8 | **só vm3 e mac** |
| `env_main` (Python) | **120** | 268,2 | qualquer máquina |
| venv próprio (Python) | **230** | 49,6 | **SÓ O MAC** |

Os 230 do Mac: `e81` (env_e81_qpots), `c311` + `treed_media` (env_c311), `b5r` + `b5m` + `moead_media` (env_b5). `env_b5` é py3.7.12 sob Rosetta x86_64; `env_c311` é py3.8.20 sob Rosetta com GPy compilado do sdist. Provisioná-los numa VM Linux destravaria 230 células/semente — **é obra de M8** (ver `nota_mac_vm_DI11` em `envs.json`).

**Consequência: o Mac é o caminho crítico e ninguém pode ajudá-lo.** Com 30 sementes, 230 cél/semente presas a um laptop de 4 processos = 6.900 células. Não fecha. É o problema estrutural do M8.

---

## 4. As quatro máquinas

### 4.1 `mac` — MacBook Pro do autor (M1 Pro, arm64)
8 núcleos, 16 GiB, **4 processos** (limite de RAM). Repo `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea`. MATLAB em `/Applications/MATLAB_R2025a.app/bin/matlab`. venvs em `/Users/gmello/Documents/python_venvs/` + ponte em `/Users/gmello/ponte_teste`.
**bash 3.2, rsync 2.6.9, `stat` BSD, `date -r` = epoch** (§12). **`--enable-bucket` DESLIGADO** (perfil `mac) BUCKET_DEF=0`) — os venvs próprios não têm o SDK e D80 proíbe instalar. **Consequência crítica: nada que roda no Mac espelha para o bucket automaticamente.** Use `caffeinate -dis` em rodadas longas.

### 4.2 `v5-mestrado` — GCP, projeto `skilled-text-480300-d9`, conta `gdmello.nunes@gmail.com`
16 núcleos físicos, 125 GiB, **12 processos**. `us-central1-a`. Vertex AI Workbench (`(base) jupyter@v5-mestrado`). Repo `/home/jupyter/ua-dd-saea`, venv `/home/jupyter/python_venvs/env_main`. Sem MATLAB, sem venvs próprios.
**O login do `gcloud compute ssh` não é o jupyter.** Tudo que escreve arquivo roda como `sudo -u jupyter -H bash ...`; caso contrário o git acusa "dubious ownership" e checagens saem vazias.

### 4.3 `mestrado-v6` — GCP, projeto `project-2aa33d8c-94a7-488b-89e`, conta `invest.gdmn@gmail.com`
8 núcleos físicos, 62 GiB, **6 processos**. Mesmo padrão jupyter da v5. Foi de onde saiu a `matlab-vm3`.

### 4.4 `matlab-vm3` — GCP, mesmo projeto/conta da v6
8 núcleos físicos, 62 GiB, **6 processos**. Login **é** `invest_gdmn`. Repo `/home/invest_gdmn/ua-dd-saea`, venv `/home/invest_gdmn/venvs/env_main`. MATLAB R2025a em `/opt/matlab/R2025a/bin/matlab` (link em `/usr/local/bin/matlab`). `tmux` instalado com autorização explícita.

> ### 🔴 REGRA INVIOLÁVEL
> **NUNCA apagar/recriar a `matlab-vm3`.** A licença do MATLAB está ancorada ao MAC `42:01:0a:80:00:05`. `stop`/`start` é permitido; `delete` destrói a licença e a campanha MATLAB inteira.

**Limpeza pendente de custo** (confirmar com o autor antes): instância `vm3-resgate` e disco `vm3-leitura`.

### 4.5 Acesso — as flags que o `gcloud` exige

```bash
V5=(--zone=us-central1-a --project=skilled-text-480300-d9         --account=gdmello.nunes@gmail.com)
V6=(--zone=us-central1-a --project=project-2aa33d8c-94a7-488b-89e --account=invest.gdmn@gmail.com)
V3=(--zone=us-central1-a --project=project-2aa33d8c-94a7-488b-89e --account=invest.gdmn@gmail.com)
```

**Flags SEMPRE antes dos posicionais** — o argparse do gcloud fecha a lista `nargs='+'` no primeiro bloco contíguo. Em zsh, array não definido expande para **um argumento vazio** (`unrecognized arguments:` sem nada depois).

---

## 5. Repositório, artefatos e o bucket

```
ua-dd-saea/
├── experiments.py                 # despachante Python. ⚠ É AQUI que vive --teto-s (default 43200)
├── experiments.m                  # despachante MATLAB (parfor — DI-34)
├── src/
│   ├── experiment.py              # run(); roteia VENV_ONLY_ALGS p/ standalone_harness.run_in_venv
│   ├── metrics.py                 # tabela S.5 congelada, HV_REF_COORD, PRIMARY_METRIC
│   ├── c262_qnehvi.py             # _WallClockProjector (linha ~408) — ver §11.1
│   └── gcs.py                     # ⚠ NÃO TOCAR
├── claude_code_context/artifacts/
│   ├── runs_matrix.csv            # A GRADE. Nunca digite a grade à mão.
│   ├── characteristics.csv        # problema → D
│   ├── envs.json                  # alg → venv, pins, thread_pin
│   └── anchors.json               # NÃO são âncoras de HV — é o patch-anchor do D80
├── scripts/  lote3s.sh plano3s.sh lote42.sh preflight42.sh estado42.sh tempo42.sh
│             coletar42.sh tabela42.py preflight.py
├── data/experiments/{exp}/{alg}/
│   └── _baseline_pre_retrofit/    # ⚠ NUNCA ESCREVER AQUI
├── REGISTRO_DECISOES_IMPLEMENTACAO.md   # decisões D.. e DI.. — fonte da verdade
└── REGISTRO_OPERACAO_RODADA42.md        # diário de operação (O-01..O-18)
```

### Nomenclatura e camadas

`data/experiments/{exp}/{alg}/exp_{exp}_{alg}_{problema}_{semente}__{camada}.parquet`

**7 camadas (CONTRATO_DE_DADOS):** ① `__real.parquet` ② `__pop.parquet` ③ `__surrogate.parquet` ④ `__timing.parquet` ⑤ `.manifest.json` ⑥ `.jsonl` ⑦ `__final.parquet` (só offline).

**O `.manifest.json` é o marcador de conclusão** para o stack Python: `status` (`ok`|`retried_ok`|`failed`), `motivo_parada` (`teto_wall`/`cache_cap` = aborto sancionado), `stack_trace`, `timing.tempo_total_s` (**aninhado** — §12.14), `fe_final`, `maxfe`.

**O stack MATLAB certifica no FOOTER do `.jsonl`, não no manifesto** (§11.3). Qualquer auditoria que só olhe a camada ⑤ fica cega para metade da evidência.

### O bucket `gs://mestrado_experiments`

Espelho remoto, escrito por `mirror_run` quando `--enable-bucket` está ligado. Duas propriedades que mordem:

1. **`mirror_run` só dispara no fim de um run BEM-SUCEDIDO.** Célula que aborta ou falha **não espelha** — a evidência (manifesto + `.jsonl`) fica órfã no disco da máquina e morre com ela.
2. **O Mac roda com bucket desligado.** Nada produzido no Mac chega ao bucket sem `rsync` manual.

`gcloud storage rsync` compara **tamanho + mtime** e **nunca apaga** sem `--delete-unmatched-destination-objects`. Seguro por default; a consequência é que **acumula** (§16.5).

Prefixos relevantes hoje:
- `experiments/` — o dado
- `_snapshot_pre_teto48h/{main/c154, main/c262, batch/c262}` — 107+152+10 objetos, caminho de reversão dos lotes de 48h
- `_logs_teto48h/{v5,v6}/` — a criar (§14.2)
- `_censo/` — a criar (§14.3)

### O roteamento obrigatório por venv (D79 / N.1.2)

`src/experiment.run()` roteia os `VENV_ONLY_ALGS` por `standalone_harness.run_in_venv`. Os caminhos vêm de `envs.json` e **são caminhos do Mac** — por isso esses configs só rodam lá. `experiments.m` não tem despacho por venv (chama `_adapter.run` in-process).

---

## 6. Métricas e portão de validação

- Normalização por `(ideal, nadir)` da **tabela S.5 congelada** (`F_MIN_MAX` em `src/metrics.py`). Não recalcule dos dados.
- **Hipervolume:** referência `HV_REF_COORD = 1.1` por coordenada, no espaço normalizado.
- **IGD+ é o endpoint PRIMÁRIO** (`PRIMARY_METRIC="igd_plus"`, D70). HV é secundário. Não inverta: entre máquinas, o HV variava ≤1,55% e o IGD+ chegava a 58,98% relativo.
- Diversidade: **Schott spacing em L1**.
- **Fronteiras BBOB são EMPÍRICAS** (cache). O IGD dos BBOB é *relativo* e o HV **pode passar de 1,1**. Sempre declare a ressalva.
- **D92** é o portão de reverificação; a validação cruzada reproduziu a âncora exatamente.
- `final_eval.py` fechou **`>>> VERDE`** com 105 finais avaliados (28/07).

---

## 7. Decisões vinculantes e regras invioláveis

| id | conteúdo |
|---|---|
| **D55** | `run_id = {exp}_{alg}_{problema}_{semente}` |
| **D58** | resume idempotente + escrita atômica — célula com manifesto não roda de novo |
| **D69/D70** | normalização por S.5; **IGD+ primário** |
| **D79** | 1 run = 1 core + pino de thread; despacho por venv-alvo. **Governa CPU, não RAM** (§11.5) |
| **D80** | **os locks são a verdade.** Divergência de pin ⇒ pare e escale. Nunca improvise pin, nunca instale para "destravar" |
| **D81** | ambiguidade ou conflito ⇒ **pare e pergunte** |
| **D92** | portão de reverificação dos indicadores |
| **D97** | **fidelidade é julgamento manual e a posteriori do autor** |
| **D-07/DI-21** | anti-órfão: aborto do BoTorch **não grava parquet nenhum** |
| **DI-34** | `parfor` quebra a ponte InProcess do MATLAB — 1 processo por célula, `'parallel',false` |
| **DI-35.5 / DI-37.1** | **teto universal de 12 h** (`--teto-s 43200` default). **O stack MATLAB não tem teto de wall-clock** — lacuna declarada e aceita |
| **DI-38(a)** | aborto sancionado (`motivo_parada ∈ {teto_wall, cache_cap}`) é ⚪, não vermelho |
| **DI-40** | `batch/c154` fora do roster (5 células). Justificativa original citava "~6,3 h por célula" — **falsificado**: medido 0,87–2,99 h, média 1,47 h. Corrigir no REGISTRO |
| **O-16** | "um config, uma máquina" — o `c122` divergiu por microarquitetura de CPU |
| **O-18** | 6 MATLABs subindo juntos → segfault em `MatlabLicensing::getInstance`. Mitigado por `LOTE_MATLAB_JITTER=12` (confirmado em campo, sem recorrência) |

### Regras que não se quebram

1. **NUNCA `git push`. NUNCA `git add -A`.** Push e tag são ação exclusiva do autor.
2. **NUNCA apagar/recriar a `matlab-vm3`.**
3. **NUNCA instalar ou atualizar nada** nas máquinas sem autorização explícita.
4. **NUNCA escrever em `data/experiments/_baseline_pre_retrofit/**`. NUNCA tocar em `src/gcs.py`.**
5. **NUNCA improvisar pin** (D80) nem **auto-corrigir fidelidade** (D97).
6. **Sempre redirecionar (`> log 2>&1`), nunca pipe** — o MathWorksServiceHost trava em pipe.
7. **Diagnóstico de credencial nunca imprime token.**
8. Ambiguidade ⇒ pare e pergunte (D81).

---

## 8. O ferramental

### `scripts/lote3s.sh` — o disparador (v3.1)

N processos de UMA célula cada via `xargs -P`, com pino real de 1 core. Existe porque `experiments.py --n-jobs N` usa joblib com `verbose=0` e divide os núcleos (estourando o pino), e `experiments.m` usa `parfor` (DI-34).

Variáveis: `LOTE=CONFIRMA`, `LOTE_MAQ=v5|v6|vm3|mac`, `LOTE_SEEDS`, `LOTE_PARES`, `LOTE_JOBS`, `LOTE_PRAZO_H`/`LOTE_PRAZO_TS`, `LOTE_CUSTO_MAX`, `LOTE_DMAX`, **`LOTE_TETO_S`**, `LOTE_REFAZER=nao|falhas|tudo`, `LOTE_BUCKET`, `LOTE_ORDEM=hibrida|barata|cara`, `LOTE_MATLAB_JITTER`, `CENSO=1`.

Perfis: `v5) JOBS=12` · `v6) JOBS=6` · `vm3) JOBS=6` · `mac) BUCKET_DEF=0; JOBS=4`.

O que faz: grade multi-semente com ordem híbrida valendo *entre* sementes; **pré-filtro** (célula com manifesto não entra na grade — no MATLAB economiza ~20 s de startup por célula já pronta); **ETA que credita células em voo** (§12.5); prazo absoluto; `LOTE_DMAX` para cortar dimensão; jitter no arranque do MATLAB; `CENSO=1` read-only.

> **v3.1 (28/07) — fechada a lacuna do `--teto-s`.** O worker do v3.0 **não repassava `--teto-s`**, então ampliar o teto exigia sair do driver e disparar `experiments.py` à mão (foi o que a torre auxiliar teve de fazer). Agora `LOTE_TETO_S=172800` chega ao run e o cabeçalho imprime um aviso. **Ampliar o teto rompe a DI-35.5 e exige decisão do autor no REGISTRO.**
>
> Cuidado com a confusão que já custou tempo duas vezes: o `TETO = 43200.0` e o `ABORTO = 22632.0` no corpo Python do `lote3s.sh` são **só do modelo de custo interno** (ordenação de fila e ETA). **Não chegam ao run.**

### `scripts/plano3s.sh` — operação por verbo, sem terminal aberto

Larga o lote **destacado** (`setsid`+`nohup`, log em `$HOME/lote3s_{maq}.log`) e expõe verbos chamáveis de fora: `censo`, `estado`, `parar`, `disparar [horas]`, `placar`, `seco`. Detecta a máquina pelo hostname.

**`parar` não é substituível por Ctrl-C**: o `xargs` roda em `( ... ) &`, que num shell interativo fica em outro process group — o Ctrl-C mata o contador e **deixa os workers vivos** escrevendo nos mesmos parquets. Os padrões de `pkill` são ancorados (`lote42\.sh$`, `/lote42_.*worker\.sh`, `experiments\.py --exp`, `maxNumCompThreads`) porque no macOS um padrão `worker.sh` solto pega o `com.apple.mdworker.shared` do Spotlight.

### Ferramentas da torre auxiliar (fora do repo, entregues por heredoc)

| ferramenta | o que faz |
|---|---|
| **`censo_bucket.py`** | O censo autoritativo. Read-only. Lista `gs://mestrado_experiments/experiments/` paginado, baixa **só os `.manifest.json`** em 24 threads, classifica as 695 células, grava `~/censo_bucket_42.csv`. Gabarito de camadas **auto-calibrado pela assinatura MODAL** dos OK de cada `(exp,alg)`. Roda na v5. **Ver §16.3: precisa deixar de depender da v5.** |
| **`triagem2.py`** | Estima o custo de fechar os FE restantes de cada célula não-OK, sob três hipóteses de crescimento (`a=1,2,3` → `T·r^(a+1)`). A instrumentação é boa; a *leitura* dela foi o erro da §16.1. Tempo já gasto pelas abortadas: 0,07–7,47 h. |
| **`painel.sh`** | Painel ao vivo no molde do `lote3s.sh`, com a categoria **`abortou`** separada de `falhou` (necessária pela DI-38a). ⚠ usa `date -d` — **GNU only, quebra no Mac** (§12.4). |

O fonte integral das três está no handoff da torre auxiliar (§6 daquele documento). **Vale promovê-las a `scripts/`** — hoje elas só existem em `/tmp` de máquinas que vão ser desligadas.

### Os demais (v2, ainda úteis)

`preflight42.sh` (portão read-only: repo+commit+árvore, import do env_main, MATLAB, **todos os venvs do roster resolvidos via `envs.json`**, núcleos, RAM, sonda de bucket; log em `$HOME`, nunca em `/tmp`) · `estado42.sh` (inventário local; superado pelo `CENSO=1`) · `tempo42.sh` (projeção com os walls que a própria máquina mediu) · `coletar42.sh` (centraliza no Mac por rsync sobre a linha de SSH do gcloud, removendo o `-t`; `--link-dest` para hardlink) · `tabela42.py` (mescla e gera `INDICE.csv`, `DUPLICADAS.csv`, `TABELA_ALGORITMOS.{csv,md,html}`) · `validacao_cruzada_indicadores.html`.

---

## 9. O modelo de custo

Serve **só** para ordenar fila e estimar ETA — nunca entra em resultado. Interpolação log-log entre walls **medidos**, indexada por `maxFE = 31D−1`.

```python
ANC = {"b1":{61:14,371:165,929:2014},   "b3":{61:4,371:40,929:537},
       "b4":{61:41,371:196,929:883},    "c122":{371:709,929:5054},
       "c141":{61:1,371:18,929:169},    "c149":{61:239,371:2632,929:12107},
       "c154":{61:95,371:52596},        "c217":{371:49,929:132},
       "c238":{61:6,371:610,929:14100}, "c262":{61:34,371:8972,929:15051},
       "e103":{61:7,371:10,929:35},     "e7":{61:317,371:1818,929:4320},
       "e74":{61:21,371:258,929:469},   "e81":{61:10,371:549,929:7167},
       "moead"/"nsga2"/"nsga3"/"smsemoa": {61:1, 929:1}}
OFF  = {"b5m":2826,"b5r":306,"c311":41,"moead_media":63,"e103":10,"treed_media":9}
TIER = {"small":0.35,"medium":1.10,"big":1.40}
BAT  = {"c149":6972,"e81":2077,"sobol_batch":2,"c262":14400}   # c262 = ESTIMADO
```

**Onde o modelo mente:**
- `BAT["c262"]=14400` era o **único número estimado** — e errado: as 5 células bateram no teto. Origem da minha previsão errada de "zero falhas na v6".
- `c154` é superestimado: expoente 3,5 entre FE=61 e FE=371, extrapola mal. **Use `LOTE_DMAX` e não `LOTE_CUSTO_MAX`** para cortá-lo — o override de `ABORTO` torna o custo **não monótono** em D.
- Os baselines pymoo têm âncora 1 s. É real: o custo é o startup do MATLAB.

**Custo por semente:** 364,6 h-core / 695 células. Concentração: `main/c154` 147,1 · `main/c262` 53,5 · `main/c149` 28,4 · `batch/c262` 20,0 · `off/b5m` 19,6 · `main/c238` 18,4 · `main/e7` 14,5.

---

## 10. FECHAMENTO DA SEMENTE 42

### 10.1 O censo do bucket — metodologia

Até 27/07 o inventário era varredura local em cada máquina: frágil (máquina offline = buraco cego) e não prova que o dado chegou ao bucket. O censo inverte o eixo: **lê o GCS como fonte da verdade** e confronta com `runs_matrix.csv`.

Taxonomia:

| Estado | Significado |
|---|---|
| `OK` | `status ∈ {ok, retried_ok}` **e** todas as camadas do gabarito |
| `OK-INCOMPLETO` | `status=ok` mas faltando camada vs. o gabarito modal do `(exp,alg)` |
| `ABORTADO` | `motivo_parada ∈ {teto_wall, cache_cap}` — **⚪ sancionado, DI-38(a)** |
| `FALHOU` | manifesto presente, status não-ok, motivo fora do conjunto sancionado |
| `SEM-MANIFESTO` | há artefato no bucket mas não a camada ⑤ |
| `RETIRADO` | `batch/c154` (DI-40) |
| `S/BUCKET` | nenhuma camada no bucket |

### 10.2 Resultado ANTES da recuperação

```
4772 objetos no bucket · volume da semente 42: 3,62 GB · células da grade: 695
```

| Estado | n |
|---|---:|
| OK | **634** |
| OK-INCOMPLETO | 1 |
| ABORTADO | 20 |
| FALHOU | 3 |
| SEM-MANIFESTO | 7 |
| RETIRADO (DI-40) | 5 |
| S/BUCKET | 25 |
| **TOTAL** | **695** |

Rosters fecham exatamente: `mac` 230 · `vm3` 345 · `v5` 50 · `v6` 70 = 695.

> **Leitura que o documento auxiliar não fez explícita:** as **25 `S/BUCKET` são células do Mac que rodaram bem mas nunca espelharam**, porque o Mac roda com bucket desligado. Não eram trabalho faltando — eram trabalho invisível. Somadas às 7 `SEM-MANIFESTO`, dão exatamente as 32 do lote do Mac.

**✅ Validação cruzada:** varredura local nas 4 máquinas e listagem do GCS produziram **o mesmo veredito para as 695 células, sem uma divergência**. Isso prova que o `mirror_run` não perde objeto nos runs bem-sucedidos, que o `rsync` não corrompeu nada, e que inventário local e remoto são intercambiáveis para auditoria. São 695 comparações independentes — merece entrada no REGISTRO.

### 10.3 Os lotes de recuperação (28/07)

55 células candidatas, ordenadas do mais barato ao mais caro:

| lote | células | teto | resultado |
|---|---:|---|---|
| **Mac** (`lote3s.sh`, 4 jobs, `caffeinate -dis`, 06h17m) | 32 | default | ✅ **ok=31**, 1 sem-manifesto (`main/b1/DTLZ4`) |
| **v5** (`experiments.py` direto, tmux `teto48h`, 06h11m) | 14 `main/c154` | **172800 s** | ❌ **ok=0** · 9 abortou · 2 falhou · 3 cortadas em voo |
| **v6** (idem, 06h11m) | 9 `c262` | **172800 s** | ❌ **ok=0** · 2 abortou · 1 falhou · 6 cortadas em voo |

> **⚠ RUPTURA DE INVARIANTE:** os lotes das VMs rodaram com `--teto-s 172800` contra o teto universal de 12 h (DI-35.5). Decisão explícita do operador para janela exploratória. **Precisa de entrada no REGISTRO — é decisão do autor.**

Snapshot de proteção feito antes do `--force`: `gs://mestrado_experiments/_snapshot_pre_teto48h/` (107 + 152 + 10 objetos). **É o caminho de reversão.**

### 10.4 Contagem final

| origem | Δ | acum. |
|---|---:|---:|
| censo do bucket | — | **634** |
| ⑦ de `sweep-big-mvns/c311/MMF16_20` (INCOMPLETO → OK, VERDE no `final_eval.py`) | +1 | 635 |
| lote do Mac | +31 | 666 |
| lote da v5 | +0 | 666 |
| lote da v6 | +0 | 666 |

**≈666 OK / 695 = 95,8%** · **666/690 = 96,5%** descontando as retiradas por desenho.

Fecha por dois caminhos: 695 − 666 = 29 = 5 (RETIRADO) + 1 (`b1/DTLZ4`) + 14 (v5) + 9 (v6) ✅ · e 61 não-OK do censo = 32 + 14 + 9 + 5 + 1 ✅

**⚠ É projeção aritmética, não medição.** Só o censo re-rodado (§14.3) transforma em fato. Se divergir, **o censo manda**.

### 10.5 As 29 que não fecharam

| # | categoria | n | motivo | cor |
|---|---|---:|---|---|
| A | retiradas por desenho | **5** | `batch/c154` — DI-40 | ⚪ |
| B | falha algorítmica determinística | **1** | `main/b1/DTLZ4` — `least squares problem is underdetermined`. **Reproduzida em Linux/Intel (vm3) E macOS/arm64 (Mac)**, certificada no footer do `.jsonl`. Não é flake | 🔴 |
| C | aborto por projeção, `main/c154` | **14** | `_WallClockProjector` critério de projeção. Reabortaram com 48 h. Inclui 3 cortadas em voo | ⚪ |
| D | aborto por projeção, `c262` | **9** | 4 `main/c262` + 5 `batch/c262` (5/5, quatro abaixo de 30% de progresso). Inclui 6 cortadas em voo | ⚪ |

Dentro de C e D, **3 células viraram `FALHOU` em vez de `ABORTADO`** no lote de 48 h (2 v5, 1 v6). Degradação de estado **não diagnosticada** — hipótese de pressão de memória (§11.5).

**A lista célula a célula sai do CSV do censo**, não deste documento:

```bash
python3 - <<'PY'
import csv, collections
L = list(csv.DictReader(open("censo_bucket_42_FINAL.csv", encoding="utf-8")))
nok = [r for r in L if r["estado"] != "OK"]
print("nao-OK: %d de %d\n" % (len(nok), len(L)))
por = collections.defaultdict(list)
for r in nok: por[r["estado"]].append(r)
for est in sorted(por):
    print("=== %s (%d) ===" % (est, len(por[est])))
    for r in sorted(por[est], key=lambda x: (x["exp"], x["alg"], x["problema"])):
        print("  %-22s %-14s [%s] camadas=%-8s fe=%-12s %s"
              % ("%s/%s" % (r["exp"], r["alg"]), r["problema"], r["maquina_dona"],
                 r["camadas"] or "-", r["fe_final_maxfe"], r["detalhe"][:70]))
    print()
PY
```

Âncoras nominais para conferir o CSV: `main/b1/DTLZ4` (única falha real) · `main/c238` (as 6 mortes coletivas de `2026-07-27T01:27:00Z`) · `sweep-big-mvns/c311/MMF16_20` (a ⑦ que faltava) · `batch/c154` (as 5 retiradas) · `batch/c149/ZDT4` (**⚠ cruzamento de donos, §16.4**).

---

## 11. Achados técnicos

### 11.1 ⭐ O-20 · O teto de wall-clock não é a variável que decide

O `_WallClockProjector` (`src/c262_qnehvi.py:~408`) tem **dois critérios**: (1) **projeção** — ajusta `t_fit ≈ c·n³` e compara `decorrido + projetado > teto`, **armando só na 11ª iteração** (depois de 10 amostras); (2) **relógio** — `elapsed > max_wall_s`. Os 20 abortos do censo gravaram literalmente `WallClockAbort("...por 'projecao': Xs decorridos + Ys projetados > 43200s")`.

Como o critério dominante é (1) e ele arma cedo, **a célula aborta em poucas horas, não depois de esgotar a janela** — foi o que se viu: 14 células fecharam em ~6 h com `ok=0`.

> **Correção minha ao enunciado auxiliar (§16.1):** o teto **é** um limiar sobre `decorrido + projetado`, então ampliá-lo **rescataria** qualquer célula cuja projeção caia na faixa entre o teto velho e o novo. O que o experimento mostrou é mais forte e mais específico: **quase nenhuma célula de `c154`/`c262` com D≥12 cai nessa faixa.** A razão projeção/orçamento é **bimodal** — ou fecha com folga, ou estoura por ordem de grandeza (41 a 190 h contra 12 h). Não existe faixa marginal a resgatar.

**Corolário para a dissertação:** o aborto **não é limitação de infraestrutura, é propriedade do algoritmo**. `c154`/`c262` (BoTorch/qNEHVI) com D≥12 têm refit de GP crescendo com `n³`, e `maxFE = 31D−1` põe o run na região onde o refit domina. **Isso é resultado, não falha** — e agora com evidência empírica de irrecuperabilidade, não só projeção.

**Corolário para o desenho:** estender o padrão da DI-40. Candidatos: **`batch/c262`** (5/5) e **`main/c154` com D≥12**.

### 11.2 Aborto do BoTorch é SEM parquets, por desenho (D-07/DI-21)

Duas implicações: (a) célula abortada aparece com assinatura de camadas empobrecida — não é corrupção; (b) re-run com `--force` sobre célula que já tinha parquets de aborto anterior produz **estado híbrido** no bucket (parquets velhos + manifesto novo), porque o rsync não apaga. **Ver §16.5 — isso precisa de decisão, não de convivência.**

### 11.3 ⭐ O-21 · O MATLAB certifica no footer do `.jsonl`, não no manifesto

Afirmei antes que o stack MATLAB "não certifica a própria falha". **Falso** — ele certifica, no `footer` do `.jsonl`, com `status=failed` e o campo `erro`. O que não existe é o `.manifest.json`.

**A lacuna é de instrumentação, não de honestidade do stack.** Quem está cego: o `censo_bucket.py` e o `is_run_done`, que só olham a camada ⑤. Isso produz a categoria enganosa `SEM-MANIFESTO`, que mistura duas coisas radicalmente diferentes. **Correção recomendada:** cair para o footer do `.jsonl` quando a camada ⑤ faltar. Pequena e de alto valor de auditoria.

### 11.4 ⭐ O-22 · O footer discrimina falha algorítmica de morte de máquina

| evidência no `.jsonl` | interpretação |
|---|---|
| footer presente, `status=failed`, `erro` preenchido | **falha algorítmica real** — morreu e soube dizer por quê |
| **sem footer**, arquivo simplesmente para | **morte de máquina** — o processo foi extinto antes de escrever |

Aplicado às 7 `SEM-MANIFESTO`: **1 falha real** (`main/b1/DTLZ4`) e **6 mortes coletivas** (todas `main/c238`, sem footer, **cinco parando no mesmo segundo — `2026-07-27T01:27:00Z`** — uma com linha rasgada no meio da escrita). Assinatura inconfundível de extinção do host.

### 11.5 ⚠ Os 3 `FALHOU` novos — NÃO diagnosticados

Eram `ABORTADO` no censo e viraram `FALHOU` nos lotes de 48 h. **Hipótese não verificada:** pressão de memória — a v5 disparou **14 processos `c154` simultâneos** e a v6, 9 de `c262`. **D79 governa CPU, não RAM**, e GP com `n` grande é pesado em memória. Os `stack_trace` estão nos manifestos que só existem no disco das VMs (§14.2).

### 11.6 Outros

- **`main/b1/DTLZ4`** — determinística em duas arquiteturas. Defeito do `b1` naquele problema, não flake.
- **Herança de `data/` entre máquinas:** `batch/e81/ZDT4` foi rastreado à cópia feita no provisionamento de VM. `batch/c149/ZDT4` tem sintoma parecido (§16.4). **Mesma classe de bug — não trate como caso isolado.**
- **`nsga2` (MMF1, MMF4, ZDT3)** precisa ser refeito com `force` na vm3 para não ser herdado dos gates de aceite da fase 3.
- **O-18 confirmado em campo:** `LOTE_MATLAB_JITTER=12` foi usado nos lotes de 28/07 sem nenhuma recorrência de segfault de licença.

---

## 12. Caderno de armadilhas — leia antes de escrever bash

### 12.1 O bash 3.2 do macOS perde aspas aninhadas dentro de `$( )`
Sintoma: a barra de progresso nunca aparece e o script parece travado. O `bash -x` mostrou `++ awk 'BEGINprintf "%.1f"'`. O bash 3.2 perde as aspas internas, a chave do awk fica exposta, a vírgula dispara **brace expansion**, o awk perde o programa e **bloqueia lendo stdin**.
**Regra: todo valor por `-v`, todo programa awk em aspa SIMPLES, todo `BEGIN` com `</dev/null`.** Corolário: `awk "BEGIN{print $X/3600}"` (sem vírgula) funciona e mascara o problema.

### 12.2 Não-ASCII no `printf` do contador
Em-dash chegou como `?\200\224'`. Blocos (`█░`) funcionam; hífens tipográficos não.

### 12.3 `/tmp` compartilhado entre usuários
Arquivo entregue por `gcloud compute scp` cai com modo **600** e o `jupyter` não lê → `chmod 644` **no mesmo comando ssh**. Log em `/tmp` pertencente a outro usuário fez o redirecionamento falhar em silêncio, o `preflight.py` nunca rodou e o `tail` leu arquivo velho → BLOQUEIO falso. **Log sempre em `$HOME`, com o nome da máquina.**

### 12.4 Portabilidade de `stat` e `date`
`date -r ARQUIVO` é GNU; no BSD/macOS `-r` é **epoch**. `date -d` é **GNU only** (o `painel.sh` usa — quebra no Mac). `stat -c %Y` é GNU, `stat -f %m` é BSD, e `-f` no GNU imprime lixo com rc=1. Ordem correta: GNU primeiro **com validação numérica**.

### 12.5 ETA ponderada por custo mente com fila híbrida
Creditar só a célula **concluída** faz o denominador congelar quando as caras entram todas de uma vez. Foi assim que a v5 mostrou `ETA ~260h32m` rodando perfeitamente. **Credite as em voo pelo tempo decorrido**, com teto de 95% do custo. E use `FILENAME==df`, não `FNR==NR` — este último quebra se o primeiro arquivo estiver vazio.

### 12.6 Ctrl-C não para o lote
`( xargs ... ) &` fica em outro process group. Sempre `pkill` ancorado, drivers primeiro.

### 12.7 `pkill -f` e falsos positivos
`pgrep -f worker.sh` no macOS deu 15 por causa do `com.apple.mdworker.shared`. Ancore.

### 12.8 `gcloud compute scp` — flags e incrementalidade
Flags antes de todos os posicionais. **Não é incremental**: para diff, pegue a linha de SSH com `--dry-run`, separe o último token (`user@ip`), **remova o `-t`** e passe ao `rsync -e`. Sob carga, o scp da vm3 caiu com `Connection reset`; alternativa: `gcloud compute ssh HOST --command='cat > /caminho' < arquivo_local`.

### 12.9 O rsync do macOS é 2.6.9
`--info=stats1` não existe. Use `--stats`. O silêncio dessa falha deixou `_maquinas/mac/` vazio numa coleta inteira.

### 12.10 Nunca sobrescreva um script que está rodando
O bash lê o arquivo **incrementalmente**. Foi por isso que o driver novo virou `lote3s.sh` e não uma v3 do `lote42.sh`.

### 12.11 zsh
Array não definido expande para **um argumento vazio**. Linha começando com `#` dá `command not found: #` (inofensivo; `setopt interactive_comments`).

### 12.12 Dois lotes ao mesmo tempo na mesma máquina
Única situação de corrupção real desta operação. Sempre `parar` antes de `disparar`.

### 12.13 `--enable-bucket` não é universal
1 nas VMs (dual-write é o desenho, DI-32), **0 no Mac**. Com bucket ligado no Mac, as células de venv próprio morrem em `RuntimeError: google-cloud-storage ausente`.

### 12.14 Campos aninhados no manifesto
`timing.tempo_total_s` está **dentro** de `timing`. Um detector que varre só as chaves de topo sai vazio. Use achatamento recursivo.

### 12.15 Grep no escopo errado
`--teto-s` vive em `experiments.py`, na **raiz** do repo. Procurar só em `src/` e `scripts/` levou à conclusão errada de que o teto não era parametrizável. **Nunca concluir ausência de alavanca a partir de busca em subdiretório.**

### 12.16 Guard mudo engole diagnóstico
`[ -n "$CB" ] && gcloud ...` curto-circuita **sem imprimir nada** quando o arquivo não existe. O operador: *"rodei esses aqui, e não respondeu nada"*. **Nenhum comando entregue ao operador pode ter caminho de saída silencioso.** Prefira heredoc a depender de achar arquivo local.

### 12.17 `env VAR="a b" cmd` não sobrevive a word splitting
`env $extra ...` com `$extra` contendo `LOTE_SEEDS=1 2` faz o `env` tratar `2` como comando.

### 12.18 `anchors.json` não é o que o nome sugere
É o patch-anchor do D80. As âncoras de métrica estão na S.5 congelada em `src/metrics.py`.

### 12.19 A armadilha do próprio dry-run do `lote3s.sh`
A mensagem sugere `LOTE=CONFIRMA LOTE_MAQ=mac bash scripts/lote3s.sh`, que **perde o `LOTE_PARES`** e cai no perfil padrão de 230 células. Sempre avisar o operador antes do disparo. *(A corrigir no script.)*

### 12.20 Comunicação: três coisas que confundiram o operador
`tmux new-session -d` é **detached por desenho** e devolve o prompt na hora (*"por que não disparou?"* — tinha disparado). **Timestamps dos logs são UTC**; 12:52 UTC = 09:52 BRT — converta sempre. E **existe convenção estabelecida** nesta operação (`tmux new -s lote42` nas VMs, `caffeinate` no Mac, `tmux capture-pane -pt lote42 | tail -3` para acompanhar de fora, registrada no `TUTORIAL_disparo_rodada42.md`): não invente procedimento onde já há rito.

---

## 13. Decisões pendentes do autor

Nenhuma é sua. Apresente número e opções; espere resposta (D81).

1. **Entrada no REGISTRO sobre o rompimento da DI-35.5** — lotes de 48 h contra o teto de 12 h. Com o resultado (`ok=0`) e o achado da §11.1 como justificativa retrospectiva.
2. **Tratamento em molde DI-40** para `batch/c262` (5/5 abortadas) e `main/c154` com D≥12 — agora com base empírica, não só projeção.
3. **O que fazer com `main/b1/DTLZ4`** — falha determinística reproduzida em duas arquiteturas.
4. **Diagnóstico dos 3 `FALHOU` novos** (§11.5) — depende dos `stack_trace` que estão no disco das VMs.
5. **Assimetria Python × MATLAB no rito de para-e-loga** (§11.3) — corrigir `is_run_done` e o censo para caírem no footer do `.jsonl`.
6. **`mirror_run` não cobre runs abortados** — evidência órfã no disco. Promover a item próprio do REGISTRO.
7. **Gabarito de camadas por assinatura modal** — o censo auto-calibra pela moda dos OK. Funciona, mas o correto é cruzar contra o **CONTRATO_DE_DADOS**; um erro sistemático que afetasse todas as células de um `(exp,alg)` passaria despercebido.
8. **Estado híbrido no bucket** (§16.5) — decisão necessária, não só documentação.
9. **O-16 rompido nas células recuperadas no Mac** (§16.2) — como reportar na tabela de tempo do M7.
10. **Corrigir o número falsificado da DI-40** no REGISTRO ("~6,3 h/célula" → medido 0,87–2,99 h, média 1,47 h).
11. **O-19 (vm3)** continua aberto: disco `pd-standard` estrangulando I/O, UUID duplicado no clone de boot, capacidade zonal `n2` esgotada. Decisão desta rodada: *"chega de tentar a vm3 por enquanto"*.
12. **Licença MATLAB para uma futura "vm2"** — faz sentido para M8, **não** para esta rodada: o MATLAB custa 41,8 h-core/semente; o gargalo é o Mac.

---

## 14. ROTEIRO DE EXECUÇÃO — o que está pendente

**Nenhuma das 4 tarefas pedidas pelo operador foi executada.** A ordem que ele pediu (1→2→3→4) **não funciona**: o item 3 (censo) roda na v5 e o item 2 desliga a v5. Ordem correta:

```
(1) rsync das 4 máquinas  →  (3) censo  →  (2) desligar v5/v6/vm3  →  (4) consolidação escrita
```

### 14.0 Antes de tudo — a v5 e a v6 estão de pé?

O operador disse *"parei a v5 e a v6"*. **Não se sabe se parou os lotes (`^C`) ou as instâncias.** O `^C` mata só o painel; runs em voo continuariam.

```bash
for P in $(gcloud projects list --format='value(projectId)' 2>/dev/null); do
  gcloud compute instances list --project="$P" \
    --format="table[no-heading](name,zone.basename(),status,machineType.basename())" 2>/dev/null \
    | sed "s|^|  $P  |"
done
```

Se estiver `TERMINATED`, subir por ~20 min só para o rsync + censo e desligar em seguida.

### 14.1 Mac — subir os 31 outputs + as ⑦

O Mac rodou com bucket desligado: **nada** desse lote está no GCS. Se o disco do Mac se perder, perdem-se as 31 recuperações.

```bash
cd ~/Documents/python_repos/mestrado/ua-dd-saea || echo "FATAL: ajuste o caminho"
echo "repo: $(pwd)"; echo "conta: $(gcloud config get account 2>/dev/null)"
gcloud storage rsync -r data/experiments gs://mestrado_experiments/experiments \
  --project=skilled-text-480300-d9 \
  -x '(^|/)_baseline_pre_retrofit/|(^|/)\.DS_Store$|/stub/|/stubpy/|/stubr3/|/c154b/|/c154diag/'
echo "---- rc=$? ----"
```

Esperado: ~124 objetos novos. Conta `gdmello.nunes@gmail.com`. Os excludes são obrigatórios.

### 14.2 v5 e v6 — subir os manifestos/`.jsonl` dos abortos + salvar os logs

Confirmar antes que nada escreve (`tmux ls`, `pgrep -f experiments.py`). Se houver run em voo, matar — a máquina vai ser desligada de qualquer forma, e um `.jsonl` rasgado é informação legítima (§11.4).

```bash
for M in v5 v6; do
  echo "==== $M ===="
  gcloud compute ssh "$M" --project=<PROJ> --zone=<ZONA> -- -t '
    cd /home/jupyter/ua-dd-saea || exit 2
    echo "em voo:"; pgrep -af experiments.py || echo "  (nenhum)"
    gcloud storage rsync -r data/experiments gs://mestrado_experiments/experiments \
      --project=skilled-text-480300-d9 \
      -x "(^|/)_baseline_pre_retrofit/|/stub/|/stubpy/|/stubr3/|/c154b/|/c154diag/"
    echo "rc=$?"
    gcloud storage cp -r /home/jupyter/teto48h \
      gs://mestrado_experiments/_logs_teto48h/'"$M"'/ 2>&1 | tail -3
  '
done
```

A segunda parte salva `/home/jupyter/teto48h/` — **é a evidência primária do achado da §11.1** e morre com a máquina.

### 14.3 Censo final + arquivamento

```bash
gcloud compute ssh v5 --project=<PROJ_V5> --zone=<ZONA_V5> -- -t '
  REPO_DIR=/home/jupyter/ua-dd-saea SEMENTE=42 \
    /home/jupyter/python_venvs/env_main/bin/python /tmp/censo_bucket.py'

gcloud compute scp v5:~/censo_bucket_42.csv ./censo_bucket_42_FINAL.csv \
  --project=<PROJ_V5> --zone=<ZONA_V5>

gcloud storage cp ./censo_bucket_42_FINAL.csv \
  gs://mestrado_experiments/_censo/censo_bucket_42_FINAL.csv
```

Se `/tmp/censo_bucket.py` não sobreviveu ao reboot, reentregar por heredoc (fonte no handoff auxiliar §6.1). **E ver §16.3: o censo precisa deixar de depender da v5 antes que ela seja deletada.**

### 14.4 Desligar (SÓ depois do censo)

```bash
gcloud compute instances stop v5  --project=<PROJ_V5> --zone=<ZONA_V5>
gcloud compute instances stop v6  --project=<PROJ_V6> --zone=<ZONA_V6>
gcloud compute instances stop vm3 --project=<PROJ_V6> --zone=<ZONA_VM3>
```

> **🔴 `stop`, NUNCA `delete` na `matlab-vm3`.**

### 14.5 Depois

- **O-19 a O-22 no `REGISTRO_OPERACAO_RODADA42.md`**: as quatro descobertas de 27–28/07 (§11.1, §11.3, §11.4) mais as suposições GNU/bash-4 do driver.
- `COLETA=CONFIRMA bash scripts/coletar42.sh` → `python3 scripts/tabela42.py` → `TABELA_ALGORITMOS.html`.
- `portao.py --varredura` e `progress.py --tabela` (= entregável do **M7**).
- **Validação de fidelidade** — a próxima etapa do autor.
- **M8**: a VM efêmera com as 30 sementes; provisionar `env_b5`/`env_c311`/`env_e81_qpots` em Linux deixa de ser luxo.

---

## 15. Ponte com a máquina do autor

A sessão Cowork enxerga o Mac por `mcp__remote-devices__*`. Pasta conectada: **só** `/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea`. `resultados_experimentos/` **não está conectada** (peça `device_request_folder_access`).

**Não existe `device_bash`: você não executa comandos no Mac.** Só `device_list_dir` (≤2000 entradas), `device_stage_files` (≤50 arquivos) e `device_commit_files`. Fluxo que funciona: escreva no container → `SendUserFile` → pegue o `file_uuid` → `device_commit_files`.

Consequência: **você depende do operador colar saída de terminal.** Projete tudo para emitir diagnóstico compacto e colável — foi por isso que `censo`, `placar` e `estado` existem como verbos.

---

## 16. ⭐ MINHAS CORREÇÕES AO HANDOFF DA TORRE AUXILIAR

Cinco pontos. Os dois primeiros mudam conclusão.

### 16.1 A §5.1 dele está mecanicamente errada no enunciado (certa no mecanismo)

Ele escreveu: *"teto maior NÃO recupera célula abortada por projeção... subir `--teto-s` não muda a curva de custo, só desloca o limiar"*. **A segunda metade contradiz a primeira.** O critério é `decorrido + projetado > teto`; deslocar o limiar **é exatamente** o que resgataria uma célula cuja projeção caísse entre 43200 s e 172800 s.

O que o experimento realmente estabeleceu é mais específico e **mais forte**: a razão projeção/orçamento em `c154`/`c262` com D≥12 é **bimodal** — 41 a 190 h contra um teto de 12 h. **Não existe faixa marginal.** Enunciado correto para o REGISTRO: *"ampliar o teto não resgata porque nenhuma célula abortada está próxima do limiar; estão de 3 a 15× acima dele."* Assim a conclusão sobrevive a revisão de banca; do jeito dele, um leitor atento derruba o argumento em uma frase.

### 16.2 O-16 foi rompido e o documento não registra

A §4.1 dele diz que o Mac rodou *"todo o stack MATLAB pendente"*. Essas células (`main/c238` ×6, `main/b1/DTLZ4`) são do **roster da vm3**. Foram recuperadas em **macOS/arm64** enquanto suas irmãs rodaram em **Linux/Intel**. Para a tabela de tempo do M7 isso é contaminação — e é exatamente o que a O-16 ("um config, uma máquina") existe para evitar.

Foi a decisão certa (ter a célula é melhor que não ter, e a vm3 estava em O-19), mas **precisa ser reportado**, e o mecanismo de rastreio está furado: **a coluna `maquina_dona` do `censo_bucket.py` é derivada do ROSTER, não medida.** O censo vai rotular essas células como `vm3` quando rodaram no Mac.

**Correção:** adicionar uma coluna `maquina_real` lida do manifesto (host/arch, se registrado — **verificar se está**). Se o manifesto não registrar host, as 31 do Mac são identificáveis pelo `done.txt` do lote (`/tmp/lote3s_mac_20260728_094142/done.txt`) e pelo mtime. **Salvar esse `done.txt` antes que o `/tmp` do Mac seja limpo.**

### 16.3 O censo não pode continuar dependendo da v5

Ele roda na v5 porque usa `google.cloud.storage`. **As VMs vão ser desligadas e um dia deletadas** — e aí o inventário autoritativo da campanha nunca mais poderá ser regenerado. Para uma dissertação que será defendida em setembro e arguida depois, isso é inaceitável.

**Correção:** reescrever a listagem e o download para `gcloud storage ls --recursive --long` + `gcloud storage cat`, que são **CLI e não exigem o SDK Python**. Aí o censo roda do Mac, de qualquer lugar, para sempre. Enquanto isso não acontece, o mínimo é arquivar no bucket, junto com o CSV, a **listagem crua de objetos** — o insumo bruto, não só o veredito.

### 16.4 `batch/c149/ZDT4` não é um caso isolado

Ele marcou como "⚠ VERIFICAR: possível cruzamento de donos". **Eu já vi essa classe de bug:** o manifesto de `batch/e81/ZDT4` numa VM foi rastreado até a cópia de `data/` feita durante o provisionamento — não tinha sido produzido lá. Mesmo padrão, direção espelhada.

**Correção:** não trate como curiosidade. Toda célula cujo host real ≠ dono do roster precisa ser auditada, e o provisionamento de máquina **nunca deve copiar `data/`**. Vale um item no REGISTRO.

### 16.5 O estado híbrido precisa de decisão, não de convivência

Ele descreve o risco (parquets velhos de um aborto + manifesto novo, porque o rsync não apaga) e propõe conviver, com o snapshot como reversão. **Isso é otimista demais:** o pipeline de métricas lê parquet, e a assinatura de camadas do censo detecta **presença, não frescor**. Um `__real.parquet` de um aborto anterior pode ser lido em silêncio junto com um manifesto novo.

**Detector barato**, para as 23 células das VMs: comparar mtime de cada parquet com o mtime do manifesto da mesma célula. Qualquer parquet mais velho que seu manifesto é órfão. Com a lista em mãos, a decisão do autor é binária — reverter pelo snapshot, ou apagar os órfãos. **Não é bookkeeping; é risco de correção do resultado.**

### 16.6 Duas notas menores

- **A lacuna do `--teto-s` está fechada.** O `scripts/lote3s.sh` agora aceita `LOTE_TETO_S`, repassa ao `experiments.py` e imprime aviso de que ampliar rompe a DI-35.5. Não é mais preciso sair do driver (§8).
- **`painel.sh` usa `date -d`**, que é GNU only. Funciona nas VMs, quebra no Mac (§12.4).

---

## Apêndice A — comandos de operação

```bash
cd ~/Documents/python_repos/mestrado/ua-dd-saea
V5=(--zone=us-central1-a --project=skilled-text-480300-d9         --account=gdmello.nunes@gmail.com)
V6=(--zone=us-central1-a --project=project-2aa33d8c-94a7-488b-89e --account=invest.gdmn@gmail.com)
V3=(--zone=us-central1-a --project=project-2aa33d8c-94a7-488b-89e --account=invest.gdmn@gmail.com)
```

Verbo em cada máquina (`estado`, `censo`, `placar`, `parar`, `seco`, `disparar 32`):

```bash
gcloud compute ssh "${V3[@]}" invest_gdmn@matlab-vm3 --command='bash ~/plano3s.sh VERBO'
gcloud compute ssh "${V5[@]}" v5-mestrado --command='sudo -u jupyter -H bash /home/jupyter/plano3s.sh VERBO'
gcloud compute ssh "${V6[@]}" mestrado-v6  --command='sudo -u jupyter -H bash /home/jupyter/plano3s.sh VERBO'
bash scripts/plano3s.sh VERBO
```

Instalar/atualizar script nas VMs:

```bash
gcloud compute scp "${V3[@]}" scripts/lote3s.sh scripts/plano3s.sh invest_gdmn@matlab-vm3:/home/invest_gdmn/

gcloud compute scp "${V5[@]}" scripts/ARQ.sh v5-mestrado:/tmp/ARQ.sh
gcloud compute ssh "${V5[@]}" v5-mestrado --command='chmod 644 /tmp/ARQ.sh && sudo cp /tmp/ARQ.sh /home/jupyter/ARQ.sh && sudo chown jupyter:jupyter /home/jupyter/ARQ.sh && ls -l /home/jupyter/ARQ.sh'
```

Fallback quando o scp cair: `gcloud compute ssh "${V3[@]}" invest_gdmn@matlab-vm3 --command='cat > /home/invest_gdmn/ARQ.sh' < scripts/ARQ.sh`

## Apêndice B — rosters por máquina

**vm3** (17 pares, 345 cél/semente): `main/nsga2 main/nsga3 main/moead main/smsemoa main/c141 main/c217 main/b3 main/e74 main/b4 main/b1 main/e7 main/c238 off/e103 sweep-small-lhs/e103 sweep-small-mvns/e103 sweep-medium-lhs/e103 sweep-medium-mvns/e103`

**mac** (26 pares, 230 cél/semente): `off/c311 off/moead_media off/b5r off/b5m main/e81 batch/e81 sweep-{small,medium,big}-{lhs,mvns}/c311 sweep-big-{lhs,mvns}/treed_media sweep-{small,medium}-{lhs,mvns}/{moead_media,b5r,b5m}`

**v6** (4 pares): `main/c262 main/c122 batch/c149 batch/sobol_batch` (+`batch/c262`, fora das sementes extras)

**v5**: `main/c149`, depois `main/c154` com `LOTE_DMAX=10` só nas sementes extras.

---

*O CSV do censo final é a fonte autoritativa; este documento é a narrativa. Onde divergirem, o CSV manda.*
