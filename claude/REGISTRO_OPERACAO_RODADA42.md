# REGISTRO DE OPERAÇÃO — rodada-42 (F2 → F3)

> **O que é.** O diário dos problemas *operacionais* enfrentados entre o fim do
> provisionamento e o disparo da rodada-42, com sintoma, causa provada e correção. Não
> substitui o `REGISTRO_DECISOES_IMPLEMENTACAO.md` (que guarda as decisões DI-xx); este aqui
> guarda os **tropeços de execução** — o tipo de coisa que custa uma hora e some da memória.
>
> **Iniciado:** 2026-07-26 · **Contexto:** 4 máquinas validadas VERDE em `aee6630`.

---

## O-01 · `--data-root` governa também a LEITURA dos artefatos de entrada

**Sintoma.** As 4 células da validação cruzada falharam em 2,1 s cada, com o placar
`failed=1` e nenhuma mensagem no log — o despachante engole o traceback por desenho (D23: o
grid segue, o status carrega o erro).

**Diagnóstico.** O erro está no `stack_trace` do manifesto:

```
FileNotFoundError('artefato da SONDA ausente p/ MMF1:
data_xmachine/sonda/sonda_MMF1.parquet (+sidecar). O runner NUNCA gera pontos de sonda
(§17.2.2) — materialize antes com scripts/gen_sonda.py. Pára-e-loga (D81).')
```

**Causa.** `naming.doe_path`, `naming.dataset_path` e o caminho da sonda **todos derivam de
`data_root`**. Apontar `--data-root data_xmachine` muda a raiz de *saída* **e** de *entrada*.
Eu havia criado symlinks para `doe` e `datasets` e esquecido a **sonda** — que é o terceiro
diretório de entrada, com 50 arquivos, e que o próprio `validar_maquina.sh` já reportava
(`doe=1502 datasets=1570 sonda=50`).

**Correção.** Três symlinks, não dois:

```bash
mkdir -p data_xmachine
ln -sfn ../data/doe      data_xmachine/doe
ln -sfn ../data/datasets data_xmachine/datasets
ln -sfn ../data/sonda    data_xmachine/sonda
```

**Prevenção.** Qualquer uso de `--data-root` alternativo exige os **três** symlinks. Vale
registrar na documentação do despachante que `data_root` não é só saída.

**Nota positiva do episódio:** a mensagem de erro do runner é exemplar — diz o artefato, o
caminho, por que ele não é gerado automaticamente, qual script o materializa, e cita a decisão
(D81). Foi ela que resolveu o caso em um comando.

---

## O-02 · `zsh` não faz word-splitting de variável não-citada

**Sintoma.** `gcloud compute scp ... $V3` →
`Invalid value for field 'zone': 'us-central1-a --project=... --account=...'`.

**Causa.** Diferente do bash, o zsh **não** separa a expansão de `$VAR` em palavras. As três
flags viraram um argumento só. É a lição nº 5 do handoff v5 reaparecendo em outra roupa.

**Correção.** Array, com chaves e aspas:

```bash
V3=(--zone=us-central1-a --project=... --account=...)
gcloud compute scp arquivo host:/tmp/ "${V3[@]}"
```

---

## O-03 · `scp` entrega com modo 600 e o `jupyter` não lê

**Sintoma.** `sudo -u jupyter -H bash /tmp/validar_maquina.sh` →
`bash: /tmp/validar_maquina.sh: Permission denied`.

**Causa.** O `gcloud compute scp` preserva a permissão restritiva do arquivo local; ele chega
como `600`, do usuário do OS Login. O `jupyter` — que é quem possui o repo e os venvs — não
consegue lê-lo.

**Correção.** `chmod 644` antes de executar como outro usuário.

---

## O-04 · OS Login separa o usuário da sessão do dono dos arquivos

**Sintoma.** Nas duas Workbench, `whoami` devolve `invest_gdmn_gmail_com` /
`gdmello_nunes_gmail_com`, e `$HOME` é `/home/<esse usuário>` — mas o repo e os venvs moram em
`/home/jupyter/`.

**Causa.** As instâncias têm `enable-oslogin: TRUE`; o usuário da sessão é derivado da conta
Google e não é o `jupyter` que provisionou o ambiente.

**Correção.** Rodar como o dono: `sudo -u jupyter -i` (interativo) ou
`sudo -u jupyter -H env VAR=… bash script` (não-interativo). Scripts que detectam o repo devem
procurar também em `/home/jupyter`, não só em `$HOME`.

---

## O-05 · Workbench recusa mutação pela API `compute`

**Sintoma.** `gcloud compute instances start mestrado-v6` →
`403 Current principal doesn't have permission to mutate this resource!`, **logo depois** de um
`instances list` bem-sucedido na mesma conta.

**Causa.** Instâncias Vertex Workbench são gerenciadas por um service account do Google; a API
`compute` bloqueia a mutação mesmo para o dono. Listar funciona, mutar não.

**Correção.** `gcloud workbench instances start <nome> --location=<zona> --project=… --account=…`
(ou `gcloud notebooks instances start` em SDK antigo, ou o botão Start no console).

---

## O-06 · Idle shutdown ligado na `v5-mestrado` — e não desligável pela CLI

**Sintoma.** As duas VMs Python estavam `TERMINATED` sem ninguém as ter desligado. O
`describe` da v5 revelou `idle-timeout-seconds: '10800'` (3 h) no metadata.

**Gravidade.** As células mais caras da v5 passam disso: `c262/ZDT1` ~4h11, `c149/ZDT1` ~3h22.
E o timer conta inatividade do **JupyterLab**, não uso de CPU — um lote por SSH pode não
registrar atividade nenhuma. O handoff v6 registrava "idle-shutdown OFF" nas duas: **errado
para a v5**.

**Correção.** `--metadata=idle-timeout-seconds=0` é **recusado** (valores válidos entre 600 e
86400). Desligado pela interface (Vertex AI → Workbench → Edit). A `mestrado-v6` não tinha o
campo — nela já estava off.

**Mitigação de fundo:** a idempotência D58 torna o lote retomável — desligamento perde as
células em voo, não o lote.

---

## O-07 · Especificações reais divergem do handoff

Medido, não lido:

| máquina | handoff v6 dizia | realidade |
|---|---|---|
| `mestrado-v6` | "idem VM-1" (32 vCPU / 128 Gi) | **16 vCPU / 62 Gi** |
| `v5-mestrado` | 32 vCPU / 128 Gi | 32 vCPU / **125 Gi** (16 núcleos físicos) |
| Mac A | — | **8 núcleos / 16 Gi** |

**Consequência.** O `--n-jobs` não pode ser copiado entre máquinas, e o plano original — que
dava os 12 configs MATLAB ao Mac A — teria sido penoso em 8 núcleos e 16 GB.

---

## O-08 · `src/` fora do path salvo do MATLAB nas DUAS máquinas

**Sintoma.** Na `matlab-vm3`, a primeira célula real morreu com
`Undefined function 'experiment'`. Medido depois no Mac A: `entradas do repo: 0`,
`which('experiment')` → `[]`, com 753 entradas no path.

**Causa.** O `experiments.m` (raiz) resolve porque o MATLAB busca na pasta corrente; o
`experiment.m` (em `src/`) não. **Nada no código faz `addpath(src)`** — no Mac isso vinha de
uma preferência de GUI gravada meses atrás, invisível para qualquer handoff.

**Correção.** `~/Documents/MATLAB/startup.m` nas duas máquinas, com `addpath(<repo>/src)` +
`pyenv(...,'InProcess')`. Fora do repositório, explícito e versionável.

**Achado colateral (bom):** a ponte do Mac aponta para `/Users/gmello/ponte_teste/bin/python`,
que **bate com o `PROVISIONAMENTO.md` §5**, e o `env_bridge` do Mac passou no **primeiro aceite
Q2 formal** (diff vazio contra o lock). A configuração sempre esteve certa — faltava estar
escrita.

---

## O-09 · `parfor` é incompatível com a ponte A2

**Sintoma.** As mesmas duas células passam com `'parallel',false` e falham com
`'parallel',true` — `ok=2 failed=0` × `ok=0 failed=2`.

**Causa.** O modo InProcess carrega a `libpython` de forma preguiçosa, na primeira chamada
`py.` real, e é dentro do worker que ela morre. Os workers **herdam** a configuração (uma sonda
mostrou `worker_scores=11 11`) — **configurado ≠ carregado**.

**Correção.** Disparo por **N processos `matlab -batch` independentes**, cada um o processo
principal do seu MATLAB. Confirma a DI-34 para além do e103 e vale para todo worker no Linux.

---

## O-10 · `experiments.py --n-jobs>1` não mostra progresso

**Sintoma.** Com paralelismo, o terminal fica mudo até o placar final.

**Causa.** `Parallel(n_jobs=…, backend='loky', verbose=0)` — o `verbose` é literal no código, e
mudá-lo alteraria a geração de código no meio da rodada (DI-33b).

**Correção.** Driver externo `lote_python.sh`: uma célula por processo via `xargs -P`, contador
`N/M` a cada 15 s, um log por célula, grade derivada do `runs_matrix.csv`, dry-run por default.
Mesma arquitetura do `vm3_lote_matlab.sh` — o parque fica uniforme.

**Complemento:** `scripts/progress.py --watch` dá a barra por run ativo (FE/maxFE, geração,
ETA, semáforo de saúde). **Vermelho no semáforo é o único detector de célula travada no
MATLAB**, que não tem teto de wall-clock.

---

## O-11 · `py-spy` no `env_main` do Mac quebrava o aceite Q2

**Sintoma.** `FALTANDO=0 EXTRAS=1 ILEGAIS=1 → py-spy==0.4.2`.

**Análise.** Profiler de amostragem, não importado por runner nenhum, sem dependências e sem
dependentes — inerte. Mas fora do lock, e o lock foi gerado *deste* venv em 22/07: o ambiente
derivou em um pacote.

**Correção.** Desinstalado, restaurando paridade exata. Se o profiler for necessário depois,
vive melhor num venv separado ou via `pipx`.

---

## O-12 · Bugs meus, registrados

1. **`date -Is` não existe no BSD** do macOS — o cabeçalho do `validar_maquina.sh` saiu sem
   data no Mac. Cosmético, sem efeito no veredito.
2. **Primeira versão do `lote_python.sh` sem filtro de problemas** — o cross-check teria pegado
   os 25 problemas em vez de 2. Corrigido com `LOTE_PROBS` antes de rodar.
3. **Symlinks incompletos no `data_xmachine`** — ver O-01. Dois em vez de três.

---

## Pendências abertas deste registro

- **`gsutil ls` falha no Mac A** (aviso, não falha) enquanto a escrita via `storage.Client`
  passa. Não bloqueia: é o caminho Python que o `mirror_run` usa. Investigar quando sobrar
  tempo.
- **`gsutil` na `matlab-vm3`**: vermelho sancionado (decisão (b) do autor). A correção conhecida
  é `rm -f ~/.gsutil/gcecredcache` — cache de token anterior à troca de escopo, que sobrevive ao
  `stop`/`start`.
- **Tag `rodada-42-freeze` nunca criada** (confirmado pelo autor). Gate DI-33b verde por hash.
- **Células stale de semente 0** (`b1`, `e7`, `c238`) precisam de `force` antes do M8.

---

## O-13 · Colar bloco multi-linha logo após troca de shell

**Sintoma.** Mordeu duas vezes. `sudo -u jupyter -i` seguido de `cd`/`PY=`/`whoami` colados juntos: as
linhas seguintes são consumidas antes de o novo shell existir, e acabam rodando **no shell errado**.
Na `mestrado-v6` isso criou `data_xmachine` em `/home/invest_gdmn_gmail_com/` com symlinks quebrados.

**Regra.** Rodar `sudo -u jupyter -i` (ou qualquer comando que troca de shell) **sozinho**, esperar o
prompt mudar, e só então colar o resto. Vale também para `$PY`/`$M`: variáveis não sobrevivem à troca.

---

## O-14 · Idle shutdown desativado pela UI **não** afeta a instância em execução

**Sintoma.** A `v5-mestrado` desligou sozinha ~3 h após o start, **depois** de o
`idle-timeout-seconds` ter sido removido do metadata pela interface. O `describe` confirmava a
ausência do campo; a máquina parou mesmo assim, em `10800 s` cravados.

**Causa provada.** O agente do Workbench lê o metadata **no boot** e mantém o valor em memória.
Remover o campo com a instância ligada não desarma o timer já carregado. Agravante: o timer conta
inatividade do **JupyterLab**, então os 28 minutos de cross-check por SSH não contaram como atividade.

**Correção.** `stop` → `start`. Verificação pós-boot, de dentro da VM:

```bash
curl -s -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/attributes/ | grep -i idle \
  || echo "SEM idle-timeout — agente sem timer"
```

Confirmado `SEM idle-timeout` após o restart. **Descoberto num cross-check de 30 min, não numa
bateria de 60 h** — foi sorte de calendário.

---

## O-15 · O pino de thread (D79) depende do CAMINHO de invocação — e o driver é o único correto

**O achado.** O campo `env.pinning` do manifesto revelou três valores diferentes de
`OMP_NUM_THREADS` para a MESMA célula:

| máquina | invocação | `OMP_NUM_THREADS` |
|---|---|---|
| v5, v6 | `lote_python.sh` (uma célula por processo, `--n-jobs 1`) | **1** ✓ |
| Mac A | `experiments.py --n-jobs 4` | **2** |
| `matlab-vm3` | `experiments.py --n-jobs 4` | **4** |

`torch_num_threads` é 1 em todas — o desvio está no OMP/OpenBLAS/MKL/NUMEXPR. O padrão: no caminho
**paralelo** do joblib o harness distribui `núcleos / n_jobs` por processo; no caminho **serial**
(`--n-jobs 1`) pina em 1.

**A consequência que explicou a anomalia.** Na vm3 foram 4 processos × 4 threads = **16 threads em 8
núcleos físicos**, duas vezes sobrescrito. Foi isso — não CPU mais fraca — que fez o
`c122/BBOB_F17` levar **3599 s** lá contra 1687 s na v5. No Mac, 4 × 2 = 8 threads em 8 núcleos:
saturado, sem sobrescrever.

**Consequência para a bateria.** `experiments.py --n-jobs 8` na v5 daria 8 × 4 = **32 threads em 16
núcleos físicos** — sobrescrito por dois, inflando a tabela de timing do M7 em silêncio.
**O `lote_python.sh` é obrigatório, não opcional: é a única invocação que honra o D79.**

---

## O-16 · `c122` diverge por MICROARQUITETURA de CPU, não por arquitetura de SO

**Medido.** `main_c122_MMF1_42`, mesma semente, mesmo código, hashes idênticos:

| Mac (arm64) | v5 (e2/AMD Rome) | v6 (e2/AMD Rome) | vm3 (n2/Intel) |
|---|---|---|---|
| `ger=42` | `ger=40` | `ger=40` | `ger=41` |

**Três valores distintos.** As duas AMD concordam; a Intel dá outro. Não é arm64 × x86 — é o caminho
de kernel do BLAS (AVX-512 × AVX2) mudando o arredondamento, que muda uma classificação da rede
neural, que muda o número de gerações. O `fe` fecha `61/61` em todas: o orçamento é exato, só a
trajetória difere. Nenhum outro config divergiu — `c262`, `c217` e `nsga2` batem em todas as
máquinas, nos dois problemas.

**Regra que isso impõe:** **um config, uma máquina** — e não "uma classe de máquina". Retomar um
config numa máquina diferente no meio da bateria mistura duas trajetórias na mesma amostra. Vale
sobretudo para o M8, com 30 sementes por config.

---

## O-17 · Retratação: a razão de velocidade que eu calculei estava contaminada

Afirmei, com base no cross-check, que o Mac era ~1,9× mais rápido por núcleo que as VMs, e que as
estimativas do RUNBOOK §7 deveriam ser dobradas. **A comparação não era válida:** o Mac rodou com 2
threads por célula e a vm3 com 4, enquanto v5 e v6 rodaram com 1 (O-15). Os únicos números limpos e
comparáveis entre si são v5 × v6, cuja razão é **1,07**.

A medição honesta da razão Mac × VM só sai quando as quatro rodarem sob o mesmo pino — o que a
bateria fará, porque toda ela passa pelo driver.

---

## VEREDITO DA VALIDAÇÃO CRUZADA (2026-07-26)

Quatro máquinas, 4 configs (`c262`, `c122` Python · `nsga2`, `c217` MATLAB) × 2 problemas
(`MMF1` D=2 · `BBOB_F17` D=10 multimodal), semente 42, em `data_xmachine`.

**VERDE.** Os três hashes — `doe_hash`, `sonda.x_hash`, `sonda.f_hash` — são **idênticos nas quatro
máquinas** nos dois problemas (`d15aed2c60ef`/`b4682dc218d2`, `7870969e81b8`/`186b726e7d62`,
`2fe294607160`/`0d6547d63f92`). O `fe_final` fecha exato (`61/61` e `309/309`) em todos os 24 runs.
Zero falhas. **O CP-init e os artefatos de sonda são portáveis entre macOS/arm64, e2/AMD e n2/Intel.**

A única divergência é a do `ger` do `c122` (O-16), permitida pelo RUNBOOK §6.2 e coberta pela regra
um-config-uma-máquina.

---

## O-18 · Análise de indicadores da validação cruzada (2026-07-26)

Pergunta do autor: *"às vezes os resultados não bateram, mas em indicadores são parecidos"* —
transformada em medida. As 24 células da validação cruzada foram passadas pelo **próprio
`src/metrics.py` do repositório** (sem reimplementação), com a normalização `(ideal, nadir)` da
tabela S.5 (D69), ref-point do HV = 1,1 por coordenada (D69/D92), IGD/IGD+/GD via pymoo e spacing de
Schott em L1.

**Gate da métrica antes de qualquer conta:** `hv_smoke_bbob_f1()` devolveu **1,04333** contra a
âncora congelada 1,0433 (D92) e `hv_front_sanity_bbob_f1()` devolveu **0,83333** contra 0,8333. A
camada de métrica está reproduzível fora das máquinas do projeto.

**Resultado.**

| célula | HV entre máquinas | leitura |
|---|---|---|
| `c217/MMF1`, `c217/BBOB_F17`, `nsga2/MMF1`, `nsga2/BBOB_F17` (MATLAB) | amplitude **0** | fronts bit-a-bit idênticos Mac × vm3 (`array_equal` em float64) |
| `c262/MMF1` | amplitude **5,4 × 10⁻⁹** | fronts diferem no 16º dígito; HV, IGD+ e spacing iguais até a 5ª casa |
| `c122/MMF1` | **0,29 %** | |
| `c262/BBOB_F17` | **1,22 %** | |
| `c122/BBOB_F17` | **1,55 %** | pior caso das 8 |

**v5 e v6 são bit-a-bit idênticos** em todas as 4 células Python (verificado com `array_equal` em
float64) — mesma microarquitetura AMD Rome. A variável explicativa é a CPU, não a VM; confirma O-16.

**Régua de grandeza (com ressalva).** No `c122/MMF1`, trocar a semente (0 → 42, mesma máquina, Mac)
move o HV **11,9× mais** do que trocar de máquina (ΔHV 0,0269 contra 0,0023); em IGD+, 4,5×. No
`c262/MMF1` a razão é ~10⁵. **Ressalva registrada:** é n=1, existe só no MMF1 e as corridas de
semente 0 são de 2026-07-19 — anteriores ao commit da rodada-42. No `BBOB_F17`, justamente onde a
dispersão entre máquinas é maior, **não há semente de comparação**: ali a frase "máquina importa
menos que semente" não tem lastro e não deve ser escrita no dossiê.

**Correção a uma leitura anterior minha.** Eu havia descrito o `c122/BBOB_F17` como uma ordenação de
dominância total `vm3 > mac > v5/v6` e sugerido que existia um ordenamento de máquinas. **Em
`c262/BBOB_F17` a ordem se inverte** — v5/v6 tem o maior HV e `C(v5→mac)=0,80` contra
`C(mac→v5)=0,60`. Não há máquina consistentemente melhor: o efeito é ruído numérico amplificado por
problema multimodal, não viés de plataforma. A regra **um config, uma máquina** continua valendo,
mas pela razão certa — impedir que um fator não controlado entre na amostra —, não porque alguma
máquina produza resultado pior.

**Caveat do `BBOB_F17` para o dossiê.** O front verdadeiro dele é **empírico** (cache NSGA-II,
§12.1). Duas consequências: o IGD é relativo àquele cache, e o HV passa de 1,1 (valores 1,09–1,15)
porque as corridas encontram pontos melhores que o ideal empírico. Comparação entre máquinas é
válida; comparação com a literatura, não.

**Artefato:** `validacao_cruzada_indicadores.html` — fronts ND, trajetórias de HV × FE, dispersão em
eixo comum e a tabela das 24 células com as 5 métricas, todas etiquetadas
`vm/experimento/algoritmo/problema/semente`.
