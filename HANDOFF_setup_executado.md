# HANDOFF — Execução do Setup Experimental (ponta a ponta)

**Para:** a instância de Claude Code que redigiu o guia de setup.
**De:** sessão de setup com o autor (Guilherme), 15/07/2026.
**Objetivo:** descrever exatamente **como** cada item do guia foi executado — incluindo desvios, pegadinhas e decisões — para que a implementação (Fase 0 / Rodadas) parta do estado real, não do idealizado.

> **Regra de fluxo acordada nesta sessão (vale para tudo daqui pra frente):**
> Toda configuração de **Python** é feita **nos dois ambientes** (Mac **e** VM). Toda configuração de **MATLAB** é **só no Mac**. Ao instruir, mostrar sempre o **Mac primeiro** e, se for Python, a **VM em seguida**.

---

## 0. Ambientes (estado verificado)

**Mac (autor):**
- macOS **12.5.1 (Monterey)**, **Apple Silicon (arm64)**. Atenção: para o Homebrew isto é uma configuração **Tier 3** (sem suporte oficial) — funciona, mas o brew emite avisos. Não é bloqueio.
- Homebrew **6.0.9** (não estava no PATH no início — ver 1.1).
- Papel: MATLAB (Rodada 1) + Fase 0 (harness Python) + pilotos. Grava só local (§17.7).

**VM (Vertex AI):**
- **Debian 12 (bookworm)**, hostname `v5-mestrado`, usuário `jupyter`, shell **bash**.
- Vem com **micromamba** em `/opt/micromamba` (env `base` ativo por padrão — o prompt mostra `(base)`). **Não** é conda clássico, mas o comportamento é o mesmo (ativa um env e põe seu `python` no PATH).
- Zona: **`us-central1-a`**.
- Papel: bateria Python (Rodadas 2–3) + análise final. Grava local **e** no bucket (§17.7).

---

## 1. BLOCO 1 — Mac (+ Python na VM)

### 1.1 — Python + pyenv (Mac **e** VM) ✅

**Resultado:** `pyenv 2.8.0` nos dois ambientes, com **3.11.9 / 3.10.14 / 3.8.19** instaladas lado a lado, e **carregando sozinho em shell novo** nos dois. Todas as versões passaram no teste de módulos (`ssl, sqlite3, lzma, ctypes, zlib, readline`).

**Como foi no Mac — desvio importante do guia:**
- O guia assumia `brew install pyenv` direto. Na prática, **o `brew` não estava no PATH** e o **pyenv nunca tinha sido instalado**. A impressão de que "já havia pyenv" vinha de venvs em `~/Documents/python_venvs/` que na verdade foram criados com o **Python 3.12 do python.org** via `python -m venv` (autocontidos — o `activate` não usa pyenv). Confirmado: `~/.pyenv` não existia e `which pyenv` não achava nada.
- Sequência real: (1) `brew` ao PATH via `eval "$(/opt/homebrew/bin/brew shellenv)"` adicionado ao **`~/.zprofile`**; (2) `brew install pyenv openssl readline sqlite3 xz zlib tcl-tk`; (3) bloco pyenv no **`~/.zshrc`** (`PYENV_ROOT` + PATH + `eval "$(pyenv init - zsh)"`); (4) `pyenv install` das 3 versões.
- **Pegadinha do 3.8.19:** o build tentou `openssl@1.1` (que o brew já removeu), caiu de volta para `openssl@3` e **funcionou** — o teste de módulos confirmou `ssl` saudável. Não exigiu flags extras.
- OpenSSL efetivo no Mac: **3.6.3**.

**Como foi na VM — o problema central foi shell login vs não-login:**
- Debian 12 já traz OpenSSL 3, então bastou instalar os `-dev`. Sequência: (1) `sudo apt install` de `build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev curl git llvm wget` (vários já estavam instalados); (2) `curl -fsSL https://pyenv.run | bash` (trouxe também o plugin **pyenv-virtualenv**); (3) bloco pyenv no **`~/.bashrc`**.
- **Pegadinha 1 (recorrente):** o pyenv "sumia" em alguns shells (`command not found`, com o `(base)` do micromamba de volta). Causa: esses shells eram **login shells**, que leem `~/.profile`/`~/.bash_profile` e **não** o `~/.bashrc` (onde estava o pyenv). **Correção definitiva aplicada:** bloco pyenv também no **`~/.profile`** (redundante mas inofensivo) **e** `[ -f ~/.bashrc ] && source ~/.bashrc` no **`~/.bash_profile`** — fechando a corrente `login shell → .bash_profile → .bashrc → pyenv`. Depois disso, aba nova carrega o pyenv sozinho (validado: `pyenv 2.8.0`, `python → ~/.pyenv/shims/python`).
- **Pegadinha 2:** durante a troca de shells, a **3.11.9 não chegou a instalar** (os 3 `pyenv install` iniciais rodaram no shell errado e deram `command not found`; ao migrar, só 3.10.14 e 3.8.19 completaram). Detectado por `pyenv versions`. **Reinstalada** depois; passou no teste.
- OpenSSL efetivo na VM: **3.0.20**.

**Observação para o Claude Code:** os venvs por algoritmo ainda **não** foram criados (correto — são das sessões). O 1.1 entregou só as **versões disponíveis**, como o guia pedia.

**Arquivos de shell alterados (estado atual):**
- Mac `~/.zprofile`: + `eval "$(/opt/homebrew/bin/brew shellenv)"`
- Mac `~/.zshrc`: + bloco pyenv, + blocos `source` do gcloud (ver 2.1)
- VM `~/.bashrc`: + bloco pyenv
- VM `~/.profile`: + bloco pyenv (redundante)
- VM `~/.bash_profile`: + `source ~/.bashrc`

---

### 1.2 — MATLAB + 4 toolboxes (Mac) ✅

- **MATLAB R2025a Update 1** (`25.1.0.2973910`), License **40904996**.
- As 4 toolboxes confirmadas via `ver('nnet'), ver('stats'), ver('optim'), ver('parallel')` — todas retornaram **Version 25.1 (R2025a)**, não-vazio:
  - Deep Learning Toolbox ✓
  - Statistics and Machine Learning Toolbox ✓
  - Optimization Toolbox ✓
  - Parallel Computing Toolbox ✓
- Isto **bate com o Anexo S.6** da SPEC (já verificado em 2026-07-14, `data/matlab_check.txt`). Reconfirmado ao vivo nesta sessão.
- Paralelismo local conhecido: **8 workers** (parfor) no Mac.

---

### 1.3 — Ponte MATLAB ↔ Python ✅ (fundação + teste ponta a ponta; env-main definitivo fica para R1-00)

Este item exigiu mais do que o guia sugeria, e **o autor insistiu (com razão) em rodar os comandos de fato dentro do MATLAB** — o que revelou um pré-requisito real.

**Descoberta técnica (verificada por busca):** o modo **`InProcess`** que a SPEC fixa (§18) carrega a `libpython` **dentro do processo do MATLAB**, o que exige um Python compilado com **biblioteca compartilhada** (`libpython3.11.dylib`). O **pyenv, por padrão, NÃO compila com shared library** — o conserto documentado é `PYTHON_CONFIGURE_OPTS="--enable-shared"`. Sintoma clássico de falta: campo `Library` vazio no `pyenv(...)` do MATLAB → `Status: NotLoaded` → `py.*` quebra.

**Verificação:** no Mac, o **3.11.9 já tinha** `~/.pyenv/versions/3.11.9/lib/libpython3.11.dylib` (5,4 MB) — provavelmente porque foi o build **reinstalado**. Ou seja, a fundação já estava correta; **não foi preciso recompilar**.

> **IMPORTANTE para o Claude Code:** este `--enable-shared` é **só no Mac** (é para o MATLAB embutir Python — e MATLAB só roda no Mac). Na VM os Pythons rodam standalone (multiprocessing/joblib), **não** precisam de shared lib. As versões 3.10.14/3.8.19 também não precisam (algoritmos Python que rodam sozinhos). **Se em R1-00 o 3.11.9 do Mac precisar ser recompilado por qualquer motivo, use `env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install -f 3.11.9`** — e lembre que isso invalidaria venvs construídos sobre ele.

**Teste executado (Opção B — venv mínimo, para honrar a sequência sem antecipar o env-main):**
1. Criado venv descartável `~/ponte_teste` a partir do 3.11.9, com `pip install numpy pymoo`. Instalou **numpy 2.4.6 + pymoo 0.6.2** (pymoo puxou **scipy 1.17.1**) — todos wheels `arm64` (arquitetura consistente). Nota: isto já mostra que os pins modernos da S.6 (env-main) se resolvem sem conflito no Mac.
2. No MATLAB (sessão fresca): `pe = pyenv('Version','/Users/gmello/ponte_teste/bin/python','ExecutionMode','InProcess')`.
   - `Library` **populado**: `/Users/gmello/.pyenv/versions/3.11.9/lib/libpython3.11.dylib`. Detalhe-chave: o **venv não tem shared lib própria**, então o MATLAB resolveu a `libpython` do **Python-base do pyenv**. Isso confirma que **um env-main construído sobre o mesmo 3.11.9 vai funcionar igual**.
   - Sem erro de arquitetura (MATLAB e Python ambos arm64).
3. `py.importlib.import_module('numpy')` e `('pymoo')` → carregaram os módulos, origem confirmada em `.../ponte_teste/.../__init__.py`.
4. **Round-trip:** `a = py.numpy.array([1,2,3]); double(a.sum())` → **`6`**. Ou seja, o ciclo completo (MATLAB manda dados → Python avalia → resultado volta ao MATLAB) funciona — que é exatamente o que a arquitetura A2 fará.

**Limpeza:** o venv `~/ponte_teste` pode ser removido (`rm -rf ~/ponte_teste`) — cumpriu o papel. O `pyenv` do MATLAB ficou apontado para esse caminho; em R1-00 é só reapontar para o env-main.

**O que fica para R1-00 (não é setup):** montar o **env-main definitivo** (pins da S.6: `numpy>=2,<3`, `pymoo==0.6.2`, `botorch==0.18.1`, `scipy` registrada, `torch`, etc.) e apontar a ponte para o `src/problems.py` real. A **mecânica** já está validada; resta trocar o Python-alvo.

---

### 1.4 — Licença MATLAB ✅ (resolvido pelo **tipo** da licença)

**Achado que muda o §21.3:** a licença do autor é **Academic | Total Headcount (TAH)** — licença **institucional** da UFMG vinculada ao nome, **não** a "Individual" que o §21.3 assumia. Licenças no portal: MATLAB, MATLAB Copilot, Online Training Suite — todas **Academic Total Headcount, expiram 31 Jan 2027**.

- A ressalva do §21.3 ("teto de ativações pode ser o teto real do paralelismo") foi escrita sob a hipótese de licença **Individual** e **não binda** aqui. TAH de usuário nomeado permite tipicamente **2 (até 4) ativações por usuário** (confirmado por busca).
- **Gargalo real do paralelismo MATLAB no plano atual:** os **8 workers do PCT no Mac**, sob **uma** ativação — não múltiplas ativações.
- Consequência prática: se a estimativa de 5–10 dias no Mac (§21.3) incomodar, adicionar uma **2ª máquina MATLAB** é **legalmente livre** na TAH (opção, não necessidade).

> **Recomendação para o Claude Code:** ao referenciar o §21.3, ler sob esta correção — a trava de ativação da SPEC não se aplica à licença TAH do autor.

---

## 2. BLOCO 2 — GCP ✅ (todos os itens verificados)

### 2.1 — gcloud CLI + autenticação (Mac) ✅

- **gcloud não estava instalado no Mac** (o autor tinha criado o bucket pela **UI web** do GCS, que não exige CLI). Confirmado: `~/google-cloud-sdk` e a versão brew não existiam; `gsutil` também ausente.
- Instalado via `brew install --cask google-cloud-sdk` → **Google Cloud SDK 576.0.0** (bq 2.1.34, gsutil 5.37, core 2026.07.10). O brew **já linkou** `gcloud`/`gsutil` em `/opt/homebrew/bin` (que está no PATH), então funcionou mesmo sem os `source` — mas adicionamos os blocos `path.zsh.inc`/`completion.zsh.inc` ao **`~/.zshrc`** por completude.
- Autenticação (3 etapas):
  - `gcloud auth login` → logado como **`gdmello.nunes@gmail.com`** (conta **pessoal** Gmail). **O autor confirmou que ESTA conta é dona do projeto e do bucket** — portanto, é a conta correta.
  - `gcloud config set project skilled-text-480300-d9` → projeto fixado (confirmado com `get-value`).
  - `gcloud auth application-default login` → **ADC** salvas em `~/.config/gcloud/application_default_credentials.json`, com quota project = `skilled-text-480300-d9`.

> **Sobre a VM:** o gcloud **não** precisa ser instalado nela — imagens Vertex AI já trazem o SDK. Confirmado empiricamente: `gcloud` funciona na `v5-mestrado` (usado no 2.3). O que o **código Python** usa na VM é a biblioteca `google-cloud-storage` (entra no env-main), autenticada pela conta de serviço da VM — não pela ADC do Mac.

### 2.2 — Bucket ✅

**Correção importante feita nesta sessão:** o autor tinha um bucket `ua-sa-nsga2` em **classe Archive** — **errado** para este pipeline. Motivos (confirmados por busca): Archive tem **custo de recuperação alto** (~$0.05/GB de leitura) e **duração mínima de 365 dias**; o pipeline **relê 0,5–0,9 TB** na consolidação (§12) e **regrava/sobrescreve** snapshots (esteira resumível). Ambos colidem com Archive.

**Bucket final criado (pela UI, depois inspecionado por CLI):**
- Nome: **`gs://mestrado_experiments`**
- Classe: **STANDARD** (sem taxa de leitura, sem duração mínima) ✓
- Localização: **`US` (multi-região)** · `location_type: multi-region`
- Proteção: **soft delete** ativo (`retentionDurationSeconds: 604800` = 7 dias)
- **Versionamento LIGADO** (`versioning_enabled: true`; `gsutil versioning get` → `Enabled`) — a dica do guia 2.2, decisão do autor.
- `public_access_prevention: enforced` · `uniform_bucket_level_access: true` (permissões só por IAM, sem ACLs por objeto).

**Decisão de região registrada:** o autor optou por **manter multi-região `us`** mesmo com a VM em `us-central1-a`. Justificativa: já rodou VM+bucket em regiões diferentes, funciona; a diferença é **custo modesto** (possível egress ao ler da VM + armazenamento multi-região mais caro que regional), coberto pelos créditos. Tecnicamente correto. (A alternativa — bucket regional `us-central1` para egress zero — foi apresentada e recusada conscientemente.)

**Pegadinha registrada:** `--format="yaml(versioning)"` retornou `null` mesmo com versionamento ligado, porque no `gcloud storage` o campo cru é **`versioning_enabled`** (plano), não uma chave aninhada `versioning:`. Para campos aninhados, usar `describe` sem filtro ou `gsutil versioning get`.

### 2.3 — Permissão de escrita da conta de serviço ✅ (sem conceder IAM)

- Conta de serviço da `v5-mestrado`: **`376980290238-compute@developer.gserviceaccount.com`** — a **conta padrão do Compute Engine** (portanto o **número do projeto é 376980290238**).
- **Não** concedemos IAM. Em vez disso, **testamos empiricamente de dentro da VM** o ciclo completo que o pipeline exige:
  - `gcloud storage cp` (escrita) → `Completed 1/1` ✓
  - `gcloud storage cat` (leitura) → retornou o conteúdo ✓
  - `gcloud storage ls` (listagem) → ✓
  - `gcloud storage rm` (exclusão) → `Completed 1/1` ✓ (e limpou o smoke test em `_smoke_test/`)
- Conclusão: a conta padrão **já tem** criar/ler/listar/apagar no bucket. O 2.3 está satisfeito **sem alteração de IAM**.

> **Nota de segurança (registro, não ação):** a conta padrão do Compute Engine com acesso amplo é conveniente mas não segue menor-privilégio. Para o contexto (mestrado, um bucket, prazo), está OK. Em produção, o ideal seria uma SA dedicada com só o papel de escrita naquele bucket.

### 2.4 — VMs ✅

- A **`v5-mestrado`** já existe e está funcional (pyenv, gcloud, acesso ao bucket — tudo testado). Suficiente para desenvolvimento e pilotos.
- **Dimensionamento da bateria completa** (mais núcleos, VMs spot/preemptíveis, VM com disco ~1,5 TB para R4) **deferido para depois do piloto de timing** — como a própria SPEC (§19, §21.3) determina. Nenhuma VM adicional criada.

---

## 3. BLOCO 3 — Pré-voo ✅ (3.1 rodado; 3.2 é gate R3.2)

### 3.1 — `preflight.py --write` (Mac) ✅

- Repo `ua-dd-saea` está **só no Mac**. `scripts/preflight.py` confirmado.
- O script é **autocontido** (imports só stdlib: `hashlib, json, os, sys, subprocess`) → roda com qualquer Python 3. Rodou com **Python 3.14.6** (do sistema/Homebrew, **não** do pyenv — irrelevante, pois é stdlib puro).
- `--write` **persiste os content-hashes no `repos.lock`** (é o comportamento esperado; **não** altera código de algoritmo nem conserta âncoras).

**Saída — exatamente 9 pendências, como o guia previu.** Detalhamento completo abaixo (o Claude Code precisa disto para a 1ª sessão de pré-voo):

**Seção 1 — repos.lock:** 8 repos com content-hash calculado e `repos.lock` atualizado:
`c122_thetadeadp 283d5167ec9f · c141_mmraea d0cf8b2d2081 · e74_clmea 59806b6b6a6c · c238_eim a7ad45118934 · e81_qpots d2fa63a41241 · c149_lbnmobo 8efa3ec701a3 · b5_desdeo 774bc18bd5ff · c311_tgprmo e3b3f802dad9` (todos "sem .git próprio").

**Seção 2 — anchors.json (17 validadas):**
- **OK (9):** c217-B5.1-guard1, c217-B5.1-guard2 (SurrogateAssistedSelectionPC.m); e103-pm-D93a (IBEAMS.m); e103-centros-D93 (construct_Rnets.m); b4-cpu (CSEA.m); c238-hypervolume-rm (MultiObjective_EIM.m); e81-matern (model_object.py); c149-fix-M (BO_surrogate_function_uncertainty.py).
- **DIVERGE (`expect_before` ausente) (5):** b1-mse-guard-L8 (EvolALG.m); b4-cap109 (CSEA.m); e81-offset1, e81-offset2 (acquisition.py). *(o 5º DIVERGE aparece consolidado no resumo)*
- **"expect descritivo — resolver no cartão" (6):** c141-sde-eps-L4; e103-judgemodel; b1-doe-D94; e7-doe-D94; b3-updataarchive-guard. *(âncoras cujo expect é descritivo, resolvidas no cartão do algoritmo, não são contadas como falha bloqueante)*

**Seção 3 — placeholders inline:** nenhum listado inline (os 2 aparecem no resumo).

**RESUMO — 9 pendências, agrupáveis em 3 famílias:**

- **Família A — arquivo não-resolvido (3)** — caminho no anchors.json não bate com a árvore real do repo vendorizado:
  - `e74-mask` → `CLMEA_Code/.../CLMEA/Local_infill.m`
  - `e74-ndsort-obj` → `CLMEA_Code/.../CLMEA/ClassifierSelect.m`
  - `b5-mode72-kde` → `desdeo_emo/.../ProbMOEAD_select.py`
  - *Ação de sessão:* `find` o arquivo real e corrigir o path.

- **Família B — `expect_before` ausente (4)** — o arquivo existe, mas a string âncora não está lá como anotada (versão/espaçamento do código difere):
  - `b1-mse-guard-L8` → `EvolALG.m`
  - `b4-cap109` → `CSEA.m`
  - `e81-offset1` → `acquisition.py`
  - `e81-offset2` → `acquisition.py`
  - *Ação de sessão:* abrir cada arquivo, achar a linha real, reajustar a âncora.

- **Família C — placeholders a cravar (2):**
  - `repos.lock: <SHA>` pendente (algum pin de commit ainda placeholder).
  - `envs.json: <PIN A CRAVAR>` pendente — **bate exatamente com a S.6**: `env-b5` tem `desdeo-emo==<PIN A CRAVAR NO GATE R3.2>`. **Pendência conhecida e intencional**, resolve no **gate R3.2** (Rodada 3), não agora.

> **Interpretação:** nada surpreendente — o guia disse "~9 pendências de âncora" e vieram 9. A parte do autor (rodar e capturar) está feita; a **correção é de sessão** com o repo aberto, como o guia instrui.

### 3.2 — Decisões de ambiente (gate R3.2) — não agora

- pin do `desdeo-emo` (b5) — gate R3.2.
- wheel do `scikit-learn 0.21.3` (b5; define Python/arquitetura do venv; roda melhor em VM Linux x86) — gate R3.2.

---

## 4. Estado final consolidado

| Item | Estado | Onde |
|---|---|---|
| 1.1 Python + pyenv (3.11.9/3.10.14/3.8.19) | ✅ carrega em shell novo nos dois | Mac + VM |
| 1.2 MATLAB R2025a + 4 toolboxes | ✅ reconfirmado ao vivo | Mac |
| 1.3 Ponte MATLAB↔Python | ✅ fundação + round-trip validados | Mac |
| 1.4 Licença MATLAB | ✅ TAH, sem trava de ativação | — |
| 2.1 gcloud + auth (login/projeto/ADC) | ✅ SDK 576.0.0 | Mac (VM já tem) |
| 2.2 Bucket mestrado_experiments | ✅ Standard, US multi-região, soft-delete+versioning | GCP |
| 2.3 SA escreve/lê/lista/apaga no bucket | ✅ sem IAM extra | VM |
| 2.4 VMs | ✅ v5-mestrado basta; sizing pós-piloto | GCP |
| 3.1 preflight.py --write | ✅ rodado, 9 pendências capturadas | Mac |
| 3.2 decisões de ambiente | ⏳ gate R3.2 (Rodada 3) | — |

**Identificadores-chave:**
- Projeto GCP: **`skilled-text-480300-d9`** (número **376980290238**).
- Bucket: **`gs://mestrado_experiments`** (STANDARD, US multi-região, soft-delete 7d, versioning on).
- SA da VM: **`376980290238-compute@developer.gserviceaccount.com`**.
- Conta gcloud (dona): **`gdmello.nunes@gmail.com`**.
- VM: `v5-mestrado`, zona `us-central1-a`, Debian 12, micromamba(base) + pyenv blindado.
- MATLAB License **40904996**, Academic TAH, exp. 31/Jan/2027.

---

## 5. O que fica para as sessões (não é setup)

**Primeira sessão de implementação / pré-voo:**
1. Resolver as **9 pendências do preflight** (Famílias A/B/C acima) — abrir os arquivos, corrigir paths e âncoras no `anchors.json`, cravar placeholders.
2. Montar o **env-main definitivo** (pins da S.6) e apontar a ponte MATLAB para o `src/problems.py` real (a mecânica já está validada — trocar o Python-alvo do `pyenv()` de `~/ponte_teste` para o env-main).

**Pendências de otimização (não bloqueiam, registradas):**
- **Lifecycle no bucket** — regra para apagar versões **não-correntes** após ~30 dias, controlando o custo do versionamento que foi ligado. (Cuidado com as durações mínimas ao definir a regra.)
- **Dimensionamento de VMs** — definido após o **piloto de timing** (§19/§21.3): quantos núcleos, VMs spot, e a VM ~1,5 TB para consolidação R4.

**Gate R3.2 (Rodada 3):** pin do `desdeo-emo` e wheel do `scikit-learn 0.21.3` para o env-b5.

---

## 6. Notas técnicas que o Claude Code deve reter

1. **Shell login vs não-login na VM:** já resolvido (`.bash_profile → .bashrc → pyenv`), mas se algo "sumir" em aba nova, é aqui que se olha.
2. **`--enable-shared` é Mac-only** (para o InProcess do MATLAB). A VM não precisa. Os 3.10/3.8 não precisam.
3. **Filtro `yaml(campo)` do `gcloud storage`** engole chaves não-aninhadas (ex.: `versioning_enabled`). Preferir `describe` cru ou `gsutil` para confirmar campos de bucket.
4. **Multi-região `us` ≠ região `us-central1`** — decisão consciente de manter multi-região; não "corrigir" sem falar com o autor.
5. **Conta de serviço da VM já tem acesso ao bucket** — não regravar IAM sem necessidade.
6. **O `env-b5` (`<PIN A CRAVAR>`) já é esperado como pendência** — não tratar como bug; é o gate R3.2.
7. **Python 3.14.6 é o `python3` do sistema no Mac** (não pyenv). Só apareceu no preflight (stdlib puro). Para qualquer coisa com dependências, usar `pyenv shell <versão>` ou o venv apropriado.
