# HANDOFF — PROVISIONAMENTO DEFINITIVO DA FROTA PARA O M8

> **Autor:** torre de controle (sessão 2026-08-01, pós-validação do T14).
> **Público-alvo:** uma instância NOVA do Claude Code, sem contexto nenhum, com acesso a este
> repositório, operando junto ao operador humano (Guilherme, GMT-3) que executa os comandos.
> **Missão:** deixar as ~9 máquinas da frota PERFEITAMENTE prontas para o disparo em massa do
> M8 (20.850 rodadas · 695 células × 30 sementes · ~14.019 h-core · wall projetado ~253 h na
> máquina mais carregada). O maior desastre possível é disparar com algo mal provisionado e
> descobrir dias de wall-clock perdidos — este documento existe para tornar isso impossível.
>
> **Modelo de operação:** você (Claude) NÃO executa nada nas VMs. O operador cola comandos e
> devolve saídas. Todo comando: colável, com `> log 2>&1` (NUNCA pipe com MATLAB), sem caminho
> de saída silencioso, e com valores que diferem entre máquinas em linha própria com `# <<<`.
>
> **Documentos-irmãos (leia junto):**
> `TUTORIAL_provisionar_vm_matlab_do_zero.md` (o passo-a-passo A0–A7+licença+venvs, com as
> armadilhas do erro 5201) e `HANDOFF_aceitacao_vm10.md` (o estado real da vm10 e as correções
> aos docs anteriores — onde eles conflitarem com o tutorial, o handoff da vm10 VENCE).
> Estão em `~/Downloads/` do Mac do operador (peça a ele se não os encontrar). Este documento
> resume o essencial deles, mas não os substitui para provisionamento do zero.

---

## §0 — O QUE JÁ ESTÁ PRONTO (inventário VERIFICADO pela torre em 2026-08-01)

Tudo abaixo foi conferido diretamente no repo/máquinas — não é relato.

| item | estado | evidência |
|---|---|---|
| **Código congelado** (T11+T12+T14 validados) | ✅ | HEAD `c797018` · suíte **826 OK, 0 falhas (skipped=36)** · REGISTRO A36–A45 |
| Suíte na máquina | ✅ | `$PY -m unittest discover -s tests` (PY = venv `mestrado_experimentos_dissertacao`) |
| **Drivers no git** (D10 fechado) | ✅ | `scripts/lote3s.sh`, `plano3s.sh`, `lote42.sh`, `coletar42.sh`, `estado42.sh`, `tempo42.sh`, `preflight42.sh` |
| **Driver consome o mapa** | ✅ | `lote3s.sh` [T14.11]: com `LOTE_MAQ` setado e `LOTE_SEEDS` vazio, deriva as sementes de `claude_code_context/artifacts/mapa_sementes.json` |
| **Datasets de sweep: 30 sementes** (D10 fechado) | ✅ | `data/datasets/` no Mac: 25 problemas × sementes {0–28, 42} + sidecars (171 MB) |
| DoE local | ✅ | `data/doe/`: 26 problemas (25 + DTLZ2_d15), 30 sementes, 27 MB |
| SONDA local | ✅ | `data/sonda/`: 25 pares (71 MB) — **NUNCA regenerar** |
| **C1** interpretador por máquina | ✅ | `src/standalone_harness.py::interpreter_for_alg` — candidatos por NOME do venv nos prefixos `~/venvs`, `~/python_venvs`, `~/Documents/python_venvs`, `/home/jupyter/python_venvs` + override `UA_DD_SAEA_VENVS` |
| **C2** hostname no ⑤ | ✅ | `standalone_harness._host_info` (override `UA_DD_SAEA_HOST`) + `experiment.m:3417` |
| **C3** mapa host→máquina aberto | ✅ | `scripts/censo42.py` — host desconhecido vira rótulo, nunca aborta |
| **C4** rosters por semente | ✅ | subsumido pelo mapa (T14.11): grupos de pares × `sementes_por_maquina` |
| **C5** listas fechadas | ✅/🟡 | `tabela42.py` deriva do disco (`MAQS=` sobrepõe) · **residual cosmético:** `censo_bucket.py:236` só IMPRIME a quebra por-máquina de mac/vm3/v5/v6 (totais corretos; máquinas novas somem só daquele bloco) |
| **C6** teste do modelo por semente | ✅ | `tests/test_t14_mapa_sementes.py` (cobertura total, interseção vazia, ≤10%) + dry-run real com `LOTE_MAQ=vm1` |
| Pins nos locks | ✅ | `requirements/locks/env_main.lock.txt`: `numpy==2.4.6`, `scipy==1.17.1`, `torch==2.11.0`, `botorch==0.18.1`, `google-cloud-storage==3.13.0` |
| vm1/vm3/vm10: 5 venvs + MATLAB + suíte + fidelidade | ✅ | `HANDOFF_aceitacao_vm10.md` §1.1 — bit-idêntico (o gargalo "envs Linux" do D10 FOI resolvido nessas 3) |
| Teste que falhava nas VMs | ✅ consertado | `test_camada_ausente_sem_gcs_e_nao_pronto` reescrito hermético — após `git pull`, VMs devem ver **0 falhas** |
| Blindagem do dual-write (DI-42.3) | ✅ | falha de upload NÃO mata mais o run — vira `upload_status.erro`, re-executável via `gcs.sync` (isso SUAVIZA o risco "403→DI-32 mata a rodada" descrito nos docs de VM, mas não elimina a necessidade de roteamento por IAM: célula sem espelho não é oficial) |

## §0.1 — O QUE ESTÁ ABERTO (o resto deste documento é isto)

1. 🔴 **Teste de licença MATLAB concorrente** — nunca feito; **decide a forma do M8**.
2. 🔴 **`frota.json` real** — os nomes vm2/vm4/vm7/vm8 do mapa são PLACEHOLDER; o mundo real
   tem `matlab-vm1`, `matlab-vm3`, `matlab-vm10` (+ v5/v6 da rodada-42, estado a confirmar).
3. 🔴 **`google-cloud-storage` ausente em 3 venvs/locks** (env_b5, env_c311, env_e81_qpots) —
   runs do c311 na rodada-42 morreram exatamente disso (comentários em
   `src/botorch_harness.py:791` e `src/standalone_harness.py:1407`). Pin = decisão do autor (D80).
4. 🔴 **`UA_DD_SAEA_CAMPANHA_ID` não é exportada pelo driver** — sem export manual idêntico na
   frota inteira, o default derivado da DATA muda no meio da campanha e o resume re-roda tudo.
5. 🔴 **58 manifestos forasteiros** em `data/experiments` do Mac (preflight aborta por desenho).
6. 🔴 **Tag nunca existiu** (`git tag -l` vazio) + push do congelamento.
7. 🟠 Máquinas novas a criar/aceitar · artefatos pré-requisito (DoE/SONDA/**DATASETS** — os
   datasets não constam de NENHUM doc de VM) · drivers novos nas máquinas · exports por máquina
   · portões de aceitação · roteamento mapa×IAM · resume bucket-aware com credencial real ·
   SUB-varN · deletion-protection · auto-updater.

---

## §0.2 — 🔴 LEIA ANTES DE QUALQUER OUTRO DOCUMENTO: OS NOMES MUDARAM (2026-08-01)

**A frota foi consolidada e uma máquina foi RENOMEADA.** Todo documento escrito
antes de 2026-08-01 — este inclusive, acima desta seção — usa a nomenclatura
antiga. A tabela de tradução:

| documento antigo diz | hoje é | o que é a máquina |
|---|---|---|
| `vm1` / `matlab-vm1` | **`vm2`** | 12 vCPU / 6 físicos / **96 GB** / 1000 GB pd-standard · `core-cascade-341902` · sem `objects.delete` |
| — (não existia) | **`vm1`** | **MÁQUINA NOVA** · 32 vCPU / 16 físicos / 251 GB / 492 GB pd-balanced · `skilled-text-480300-d9` · **com `objects.delete`** (projeto dono do bucket) |
| `vm3` | `vm3` | cresceu: 16→**32 vCPU**, 62→**251 GB**, 300→**492 GB** · `objectAdmin` |
| `vm10` | `vm10` | cresceu: 62→**96 GB**, 200→**246 GB** |
| `v5`, `v6` | — | **FORA da frota** (Workbench `e2`, TERMINATED; quota migrou para a `vm1` nova) |
| `mac` | — | **FORA do grid do M8** (ver `artifacts/frota.json:_mac_fora`) |

⚠ **O erro que isto evita:** ler *"vm1/vm3/vm10 já têm os 5 venvs e o DoE"* (§0
acima, §1.1 do handoff da vm10) e concluir que a `vm1` está pronta. **Não está** —
a `vm1` de hoje nasceu em 2026-08-01 e o provisionamento dela é o item aberto.
Quem tem os 5 venvs é a **`vm2`**.

**Frota vigente:** `claude_code_context/artifacts/frota.json` (fonte única) e o
mapa derivado `artifacts/mapa_sementes.json` — 4 máquinas, 1 grupo de
elegibilidade, **11/4/4/11 sementes**, desbalanceamento 1,54%, wall máx 321 h.

**Ordem de execução do M8 [autor, 2026-08-01]:** `LOTE_ORDEM=semente` —
SEMENTE-major, do mais barato ao mais caro dentro de cada semente. É modo NOVO
do `lote3s.sh`; o default `hibrida` faz o oposto (custo-major ENTRE sementes) e
**não serve** para esta campanha.

---

## §1 — TAREFA 0: A FROTA REAL (`frota.json`)

O mapa `claude_code_context/artifacts/mapa_sementes.json` foi gerado com a frota DEFAULT
embutida em `scripts/mapa_sementes.py` (bloco `FROTA_DEFAULT`): as 4 conhecidas
(`mac` jobs=4 · `vm3` jobs=6 · `v5` jobs=12 Python-only · `v6` jobs=6 Python-only) + **5
placeholders** (`vm1 vm2 vm4 vm7 vm8`, todos "jobs=6, matlab, 4 venvs" — chutes declarados).

**O que o operador precisa decidir/informar (D81 — pergunte, não assuma):**
1. Quais máquinas EXISTEM hoje e entram no M8. Estado conhecido: `matlab-vm1` (12 vCPU/6
   físicos/35 GB, disco pd-standard LENTO — O-19), `matlab-vm3` (16/8/62 GB, objectAdmin no
   bucket), `matlab-vm10` (12/6/62 GB, aceita 2026-07-30, IAM sem delete). `v5`/`v6` (Python,
   rodada-42): confirmar se seguem vivas e com qual quota. O Mac entra com 4 jobs.
2. Quantas máquinas novas criar (o plano fala em ~9 no total) e com que shape (regra: núcleos
   FÍSICOS; BoTorch é limitado por RAM — pico transiente medido 7,6 GiB/processo).
3. `jobs` por máquina POR COLUNA (ver §12 do tutorial + §7 do handoff vm10): vm10 BoTorch=6 ·
   vm3 BoTorch=6 (recomendação pós-RSS; 8 é defensável) · vm1 BoTorch=4 🔴 (35 GB!).

**Como aplicar:** criar `claude_code_context/artifacts/frota.json` copiando a ESTRUTURA do
`FROTA_DEFAULT` (chave `maquinas`, cada uma com `nome`, `jobs`, `matlab`, `envs`, `fonte`),
com os nomes/jobs/envs REAIS. Depois:

```bash
cd ~/Documents/python_repos/mestrado/ua-dd-saea
python3 scripts/mapa_sementes.py            # regenera o mapa (valida sozinho)
/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python \
  -m unittest tests.test_t14_mapa_sementes  # cobertura/interseção/desbalanceamento
git add claude_code_context/artifacts/frota.json claude_code_context/artifacts/mapa_sementes.json
git commit -m "frota real do M8 + mapa semente->maquina regenerado"
```

⚠ O nome no `frota.json` é o ROTULO da campanha (o que vai em `LOTE_MAQ` e no ⑤ via
`UA_DD_SAEA_HOST`) — não precisa ser o hostname GCP, mas escolha UMA convenção e use-a em
tudo (recomendação: `vm10` para `matlab-vm10`, etc.).

## §1.1 — CROSS-CHECK OBRIGATÓRIO: mapa × IAM do bucket

O gerador do mapa balanceia por CUSTO e não sabe nada de IAM. Depois de regenerar, confira à
mão para onde foram as sementes **0, 1 e 42**:

- **Censo do bucket (2026-07-30):** semente 0 = 506 objetos · semente 1 = 6 · semente 42 =
  4.541 (FECHADA) · **sementes 2–28 = ZERO (limpas)**.
- Máquina **sem `objects.delete`** (vm1, vm10, e toda SA nova com o papel recomendado
  objectViewer+objectCreator) não consegue re-espelhar célula já existente no bucket →
  o upload falha (403). Com a blindagem DI-42.3 o run local sobrevive, mas a célula fica **sem
  espelho oficial** — inaceitável na doutrina "oficial = bucket" (DI-42.2).
- Logo: **sementes 0 e 1 → só em máquina com objectAdmin (hoje: vm3) OU o autor limpa os
  prefixos antes** (só o autor decide isso; o resto da operação NUNCA apaga nada do bucket).
- **Semente 42:** está fechada com 666/695 ok; o que resta dela são as **29 células não-ok
  (D8: re-rodar todas)**. O resume bucket-aware pula as 666; as 29 podem ter resíduo parcial
  no bucket → a máquina dona da s42 no mapa também precisa de delete OU de prefixos limpos
  dessas 29. No mapa placeholder a s42 caiu em `vm8` — RECONFIRA no mapa real.

---

## §2 — A FILA ORDENADA (P1 → P15)

A ordem importa: P1 pode REPLANEJAR tudo; P2–P6 são no Mac; P7+ é por máquina.

### P1 · 🔴 Teste de licença MATLAB concorrente (30 min — DECIDE O M8)
As máquinas MATLAB usam a MESMA licença online `40904996` (conta
`mello.guilherme@dcc.ufmg.br`). Nunca foi testado se ela permite 2+ sessões simultâneas na
frota. Se NÃO permitir, as colunas MATLAB das máquinas são mutuamente exclusivas e o plano
inteiro muda — por isso é o passo 1. Dois terminais, disparados juntos (§15.3 do handoff vm10):

```bash
# terminal 1 — vm3
date -u; matlab -batch "pause(90); disp('VM3_MATLAB_OK')" > ~/lic_vm3.log 2>&1; echo "rc=$? (rc NAO e veredito)"; date -u; cat ~/lic_vm3.log
# terminal 2 — vm10 (imediatamente após)
date -u; matlab -batch "pause(90); disp('VM10_MATLAB_OK')" > ~/lic_vm10.log 2>&1; echo "rc=$? (rc NAO e veredito)"; date -u; cat ~/lic_vm10.log
```
Ambas imprimem `..._MATLAB_OK` com janelas sobrepostas ⇒ concorrência OK, siga. Qualquer erro
de licença ⇒ PARE e replaneje com o autor (D81).

### P2 · Frota real + mapa + cross-check IAM (§1 e §1.1 acima) e commit

### P3 · Limpar os 58 forasteiros do Mac (5 min)
58 células em `data/experiments/**` do Mac foram escritas nas VMs da rodada-42
(`env.executable = /home/jupyter/...`) e viajaram no coletor. O preflight B-12 aborta por
desenho enquanto existirem. Endereços: `data/experiments/main/c122/` (25 células),
`data/experiments/main/c149/` (25), `data/experiments/batch/c149/` (4),
`data/experiments/batch/sobol_batch/` (4) — todas da semente 42, cada célula = 6 arquivos
(manifest + jsonl + 4 parquet). ⚠ NÃO apague os diretórios inteiros: eles contêm também
células legítimas do Mac. Quarentenar (não deletar) só as forasteiras:

```bash
cd ~/Documents/python_repos/mestrado/ua-dd-saea && Q="data/_quarentena_forasteiros_$(date +%Y%m%d)" && mkdir -p "$Q" && /Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python -c "
import importlib.util, os, shutil, sys
sys.path.insert(0, os.path.abspath('scripts')); sys.path.insert(0, os.path.abspath('.'))
spec = importlib.util.spec_from_file_location('preflight', 'scripts/preflight.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
q = os.environ.get('Q', '$Q')
n = 0
for rel, _ in m._manifestos_forasteiros():
    stem = rel[:-len('.manifest.json')]
    for suf in ('.manifest.json', '.jsonl', '__pop.parquet', '__real.parquet', '__surrogate.parquet', '__timing.parquet', '__final.parquet'):
        p = stem + suf
        if os.path.exists(p):
            dst = os.path.join(q, p); os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(p, dst); n += 1
print(f'movidos {n} arquivos para {q}')
sobra = m._manifestos_forasteiros(); print(f'forasteiros restantes: {len(sobra)}')" && echo "== preflight de conferencia ==" && /Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python scripts/preflight.py | tail -20
```
Esperado: `movidos ~348 arquivos` · `forasteiros restantes: 0`. Os oficiais dessas células
vivem no bucket (e a evidência em `f5/`); a quarentena pode ser apagada depois pelo autor.

### P4 · gcs nos 3 venvs que faltam (decisão de PIN do autor — D80)
`google-cloud-storage` existe SÓ no `env_main.lock.txt` (3.13.0). Faltam: **env_c311**
(py3.8), **env_b5** (py3.7), **env_e81_qpots** (py3.11) — nos LOCKS e nos venvs (Mac + todas
as VMs). Sem isso, com `LOTE_BUCKET=1`, todo upload desses stacks falha (blindado ⇒
`upload_status.erro` ⇒ célula sem espelho oficial; e81 é ainda BUCKET-ONLY, o mais crítico).
Processo: (a) o AUTOR escolhe o pin por env (py3.7/3.8 exigem a família 2.x; py3.11 pode
seguir o 3.13.0 do env_main — **não improvise: D80**); (b) adicionar a linha (e transitivas)
ao lock de cada env; (c) instalar DO LOCK em cada máquina; (d) smoke:
`<venv>/bin/python -c "import google.cloud.storage; print('OK')"` nos 3 venvs, nas ~9 máquinas.

### P5 · TAG final + push (o congelamento — ato do AUTOR)
Ver bloco de comandos no §8. Só depois do push as VMs podem dar `git pull` (regra: pull
somente após o aviso de congelamento do autor).

### P6 · SUB-varN no Mac (pré-registro DI-39 — nunca rodou)
Varredura N∈{10,20,30,50} dos 4 pisos (custa segundos por célula). O N=20 está CRAVADO pelo
autor; a varredura pré-registrada o reconfirma (ou o substitui) — precisa existir antes da
análise M9, e o pré-registro pede antes da bateria. Cartão:
`claude_code_context/40_subestudos/varredura_N_pisos.md` (em M=3 os N nominais viram efetivos
{6,15,28,45} — o manifesto registra). Não há flag pronta no `experiments.py` — é uma
mini-sessão própria; agendar com o autor (pode correr em paralelo ao provisionamento).

### P7 · Provisionar as máquinas novas do zero
Seguir o `TUTORIAL_provisionar_vm_matlab_do_zero.md` **com as correções do
`HANDOFF_aceitacao_vm10.md` §11**, que prevalecem. Resumo dos pontos que o tutorial erra/omite:
1. **`startup.m`** vai em `~/Documents/MATLAB/startup.m` (userpath), `addpath` ABSOLUTO
   (`/home/<user>/ua-dd-saea/src`) + `pyenv(...InProcess)` — byte-idêntico ao das vm3/vm10
   (340 B, md5 `3e06ae44c9dba0d9fc1e9724f0878347`). O `provisionar_matlab_vm.sh` NÃO o cria.
   NÃO vai para o repo.
2. **DoE é parquet+manifest** (751 pares, 27 MB) — o `.npy` da spec é obsoleto.
3. **SONDA** (`data/sonda/`, 25 pares, 71 MB) — o runner NUNCA gera; **NUNCA regenerar**;
   copiar com `cp -n` + md5 conferido nos DOIS arquivos do par.
4. **A3 (libs do Service Host) ANTES do primeiro `matlab`** — senão erro 5201, um dia perdido.
5. pyenv 3.11.9 **`--enable-shared`** (sem `libpython3.11.so` a ponte A2 morre; recompilar,
   não remendar).
6. env_b5/env_c311 via micromamba com **`--no-deps`** do lock; `GPy==1.9.9` com
   `--no-build-isolation` ANTES do resto.
7. **IAM da SA nova no bucket** (conta dona `gdmello.nunes@gmail.com`):
   `objectViewer`+`objectCreator` (§10.2 do tutorial). Consequência: máquina nova = só
   sementes limpas (§1.1).
8. `--deletion-protection` na criação; SEM escopo de Compute (deliberado);
   300 GB pd-balanced se a quota SSD permitir (O-19: pd-standard estrangula o startup do MATLAB).
9. Desabilitar o auto-updater da MathWorks (um update silencioso viola o D80).

### P8 · `git pull` + suíte em TODAS as máquinas existentes (vm1/vm3/vm10/v5/v6)
Após a tag: `git -C ~/ua-dd-saea pull` (as VMs estão na era "394 testes"; o repo congelado tem
826). Esperado na suíte: `Ran 826` · **0 falhas** · skipped≈36 (o teste que falhava foi
reescrito). Qualquer outro número ⇒ pare (D81). Comando:
`~/venvs/env_main/bin/python -m unittest discover -s ~/ua-dd-saea/tests > ~/suite_<maq>.log 2>&1; tail -3 ~/suite_<maq>.log`
(no Mac o venv é `~/Documents/python_venvs/mestrado_experimentos_dissertacao`).

### P9 · Materializar os artefatos pré-requisito em TODAS as máquinas
O runner se RECUSA a gerá-los (D81 — pára-e-loga). Três classes, todas conferidas por hash:

| artefato | onde | volume | como materializar |
|---|---|---|---|
| DoE | `data/doe/{prob}/doe_{prob}_{sem}.parquet`+sidecar | 751 pares · 27 MB | copiar do Mac (ou `src.doe.ensure_doe`) + conferir contagem |
| SONDA | `data/sonda/sonda_{prob}.parquet`+sidecar | 25 pares · 71 MB | **copiar SEMPRE** (`cp -n` + md5 §4.2 do handoff vm10) — NUNCA gerar |
| **DATASETS** | `data/datasets/{prob}/ds_{prob}_{sem}[...].parquet`+sidecar | 25 probs × 30 sems · 171 MB | copiar do Mac — **este item NÃO consta de nenhum doc de VM anterior**; sem ele TODA célula `off/`/`sweep-*` da máquina aborta em D81 |

vm1/vm3/vm10 já têm DoE+SONDA (verificado na vm10) — **falta conferir DATASETS nas três**
(a aceitação da vm10 não cobria off/sweep). v5/v6 têm no máximo a semente 42 de tudo.
⚠ A regra "provisionamento nunca copia `data/`" refere-se a **`data/experiments`**
(resultados/proveniência); os pré-requisitos (doe/sonda/datasets) são INSUMOS determinísticos
com sidecar de hash — copiar com conferência é o método sancionado (foi o da vm10).
Transporte: `gcloud compute scp --recurse` do Mac (flags ANTES dos posicionais; não é
incremental) ou tar por partes. md5 de amostra + contagem de arquivos nas duas pontas.

### P10 · Drivers novos nas máquinas
Os `~/lote3s.sh`/`~/plano3s.sh` das VMs são da ERA rodada-42 (sha `dd7945e8…`/`a325ccb1…`) —
**não conhecem o mapa de sementes**. Após o pull, substituir pelos canônicos do repo:
`cp ~/ua-dd-saea/scripts/lote3s.sh ~/lote3s.sh && cp ~/ua-dd-saea/scripts/plano3s.sh ~/plano3s.sh`
⚠ NUNCA sobrescrever um script EM EXECUÇÃO (o bash lê incrementalmente — comportamento sem
nome). Confirmar antes que nenhum lote roda (`pgrep -f lote3s`).
O driver novo: com `LOTE_MAQ=<nome-da-frota>` e sem `LOTE_SEEDS`, deriva as sementes do mapa;
`LOTE_MAPA=0` volta ao manual; sem `LOTE=CONFIRMA` é SEMPRE dry-run (guarda na linha ~424).

### P11 · Exports padronizados por máquina (o item novo mais importante)
No `~/.bashrc`/`~/.profile` de CADA máquina (e conferido no ambiente do `nohup`):

```bash
# <<< por máquina — nome da FROTA (o rótulo do mapa/roster), não o hostname GCP
export UA_DD_SAEA_HOST=vm10
# IDÊNTICO NA FROTA INTEIRA — cravar UMA vez no disparo e nunca mudar no meio:
export UA_DD_SAEA_CAMPANHA_ID="<commit12-da-tag>_M8"     # ex.: $(git rev-parse --short=12 <tag>)_M8
```
**Por quê (B-03, `src/manifest.py:44-52`):** o default do carimbo deriva da DATA UTC — numa
campanha de ~10-21 dias ele MUDA no meio, o `is_run_done` deixa de reconhecer as células dos
dias anteriores e o resume tenta RE-RODAR tudo (com 403 no bucket nas máquinas sem delete).
O driver NÃO exporta essa variável — é responsabilidade do provisionamento. Os dois stacks
(Python e MATLAB `experiment.m:3186`) leem a mesma variável.
`UA_DD_SAEA_VENVS` só é necessário se os venvs morarem fora dos prefixos conhecidos
(`~/venvs` das VMs e `/home/jupyter/python_venvs` de v5/v6 já estão na lista).

### P12 · Higiene por máquina (minutos, do Mac)
- `--deletion-protection`: VERIFICAR na vm10 e na vm1 (pendência 🔴 do handoff vm10 §1.3d;
  comando de uma linha lá) e ligar nas novas na criação.
- Auto-updater MathWorks desabilitado em toda máquina MATLAB.
- Remover `data_xmachine/` da vm10 (beco sem saída reconhecido, sem valor).
- Jitter MATLAB por máquina: default 12 (medido p/ 6 jobs); vm3 20–25; vm1/vm10 25–30
  (recomendação por velocidade de disco — não é medição).

### P13 · Portões de aceitação POR máquina (nada de "deveria funcionar")
Uma máquina só entra na frota depois de (tudo em `data/`, jamais em dataRoot isolado —
`accept.py`/`auditar.py` ignoram `--data-root` POR DESENHO, `portao.py:94`):
1. suíte 826/0 (P8) · preflight limpo;
2. `portao.py` numa célula MATLAB (`main/nsga2/MMF1/<semente-da-máquina>`) e nas duas BoTorch
   (`c154`, `c262`) — VERDE, 0 vermelhos;
3. **fidelidade D97**: mesma célula × referência do bucket ⇒ `diff` de parquet BIT-IDÊNTICO
   (a vm10 fechou `maxabsdiff=0.000e+00`, `identicos=61/61` — é a régua);
4. **primeiro lote real PEQUENO e observado** (nunca começar com varredura de 33 h): par
   barato, semente limpa DA PRÓPRIA máquina no mapa, `LOTE_BUCKET=0` → depois um segundo,
   pequeno, com `LOTE_BUCKET=1`, para exercitar `disparar → placar → consolidação →
   espelhamento` (a vm10 provou tudo ATÉ a fronteira do disparo e nada depois — §1.3a).
⚠ `stubpy`/`stubr3` NUNCA em portão. ⚠ `exit=0` não é veredito — manda a linha `[placar]` e
o rodapé do `.jsonl` (O-21/O-22).

### P14 · Validar o resume bucket-aware com credencial REAL (pendente desde o R2-00)
Numa VM com IAM pronto: re-disparar uma célula JÁ CONCLUÍDA (da semente da própria máquina)
com `LOTE_BUCKET=1` ⇒ o esperado é **skip** (`is_run_done` consulta o bucket p/ os bucket-only
— D58) sem nenhum upload novo. Se re-rodar ou tentar upload, PARE (D81) — é exatamente o
cenário que destruiria a campanha no dia 2.

### P15 · DISPARO M8
Com P1–P14 verdes: cada máquina dispara com o driver novo,
`LOTE=CONFIRMA LOTE_MAQ=<nome> LOTE_BUCKET=1 LOTE_JOBS=<coluna> LOTE_MATLAB_JITTER=<maq>`,
sementes derivadas do mapa, `nohup ... > ~/lote_<maq>_<data>.log 2>&1 &`, `sleep 20` + `sed`
p/ confirmar o `[grid]`. **NUNCA dois lotes na mesma máquina** (única corrupção real).
Colunas de paralelismo por máquina: handoff vm10 §7 (BoTorch: vm10=6, vm3=6, vm1=4 — RAM).
DI-34: e103/workers dedicados são SERIAIS por dentro (1 processo MATLAB por célula,
`'parallel',false`) — nada a configurar, só não "otimizar".
Acompanhamento: `plano3s.sh placar`/`censo` + `scripts/progress.py` (agora lê
`footer_fechado()` — T14.2). Fuso: VMs em UTC, operador GMT-3.

---

## §3 — CHECKLIST-MATRIZ (marcar por máquina)

| item | mac | vm3 | vm1 | vm10 | v5 | v6 | novas… |
|---|---|---|---|---|---|---|---|
| existe/decidida (P2) | ✅ | ✅ | ✅ | ✅ | ? | ? | ☐ |
| git pull pós-tag + suíte 826/0 (P8) | ✅(já) | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5 venvs (ou env_main p/ Python-only) | ✅ | ✅ | ✅ | ✅ | env_main | env_main | ☐ |
| gcs nos 3 venvs extras (P4) | ☐ | ☐ | ☐ | ☐ | n/a | n/a | ☐ |
| DoE 751 pares | ✅ | ✅ | ✅ | ✅ | ☐ | ☐ | ☐ |
| SONDA 25 pares | ✅ | ✅ | ✅ | ✅ | ☐ | ☐ | ☐ |
| DATASETS 30 sementes (P9) | ✅ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| drivers novos em ~ (P10) | n/a(repo) | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| exports HOST+CAMPANHA_ID (P11) | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| startup.m md5 `3e06ae44…` | n/a | ✅ | ☐conferir | ✅ | n/a | n/a | ☐ |
| IAM bucket da SA | ✅ | ✅(admin) | ✅ | ✅ | ✅ | ✅ | ☐ |
| deletion-protection (P12) | n/a | ✅? | ☐🔴 | ☐🔴 | n/a? | n/a? | ☐ |
| auto-updater off (P12) | n/a | ☐ | ☐ | ☐ | n/a | n/a | ☐ |
| portões + fidelidade D97 (P13) | ✅ | ✅(s42) | ✅? | ✅ | ☐ | ☐ | ☐ |
| 1º lote real pequeno (P13.4) | ✅(s42) | ✅(s42) | ☐ | ☐ | ✅(s42) | ✅(s42) | ☐ |

(? = confirmar com o operador; a linha de v5/v6 pressupõe que sobrevivem na frota.)

---

## §4 — ARMADILHAS CURADAS (as que mais custaram, em uma linha cada)

1. **`exit=0` não é veredito** — placar + rodapé do `.jsonl`; os stubs F0-02/F0-03 saem 0 sem criar nada.
2. **Erro 5201 = biblioteca faltando**, não licença — A3 antes do primeiro `matlab`; `ldd` do §5.3 do tutorial.
3. **Smoke em dataRoot isolado NUNCA passa nos portões 1/2** — célula de aceitação vive em `data/`.
4. **Catch-all do `lote3s.sh` liga o bucket** (`BUCKET_DEF=1`) — em máquina sem perfil, SEMPRE passar `LOTE_BUCKET` explícito.
5. **MATLAB + pipe trava** (MathWorksServiceHost) — sempre `> log 2>&1`; única exceção: login interativo.
6. **Ctrl-C não para o lote** — `pkill` ancorado; **nunca dois lotes na mesma máquina**.
7. **Nunca sobrescrever script em execução** (leitura incremental do bash).
8. **`cp -n` + md5 para SONDA; procure antes de gerar** — artefato regenerado = hash novo = comparação contaminada silenciosamente.
9. **403 no bucket = conta errada** na maioria das vezes — nunca mexa em IAM às cegas.
10. **`gcloud compute scp`**: flags antes dos posicionais; não é incremental.
11. **zsh: array vazio expande para argumento vazio**; bash 3.2 do Mac quebra aspas aninhadas em `$( )`; `date -d` é GNU-only.
12. **O-16 vive para a EXECUÇÃO** (nunca trocar família de CPU; `n2` sempre; zona ≠ quota) — para o RESULTADO foi aposentada pela alocação por semente (T13/D1).
13. **Medições pesadas com `python -u`** (o buffer descartado no SIGTERM já engoliu um log inteiro).
14. **Logs em `$HOME` com nome da máquina**, nunca `/tmp`.
15. **`--modo-rapido` NÃO usar** (semântica de orçamento não verificada — D80).

## §5 — REGRAS INEGOCIÁVEIS (verbatim, em vigor)

**NUNCA `git push` / `git add -A`** (push e tag = ato do AUTOR; pull só após o aviso de
congelamento) · **NUNCA instalar/atualizar fora dos locks** (`requirements/locks/*.lock.txt`;
pins = D80, sempre do autor) · **NUNCA escrever em `data/experiments/_baseline_pre_retrofit/**`**
· **bucket: nenhum `rm`/`mv`/`rsync --delete`, jamais — não há undo** · **semente 42 FECHADA**
(execução das 29 não-ok só conforme D8 e o mapa) · **fidelidade = manual do autor (D97), nunca
auto-corrigida** · **não tocar em `src/gcs.py`** · **ambiguidade ⇒ pare e pergunte (D81)** ·
**diagnóstico de credencial nunca imprime token** · **a SA das VMs não tem escopo de Compute
(deliberado)** · **`stubpy`/`stubr3` nunca em portão** · **artefatos pré-requisito nunca
regenerados** · **o `startup.m` não vai para o repositório**.

## §6 — REFERÊNCIAS (o que ler para cada coisa)

| documento | serve para |
|---|---|
| `TUTORIAL_provisionar_vm_matlab_do_zero.md` (~/Downloads) | provisionar máquina nova A0→portões (com §11 do handoff vm10 por cima) |
| `HANDOFF_aceitacao_vm10.md` (~/Downloads) | estado da vm10, RSS medido, censo do bucket, correções aos docs anteriores |
| `HANDOFF_operacao_multimaquina.md` (raiz, untracked) | operação de lotes da rodada-42 |
| `handoff/T14-FINAL.md` + REGISTRO A44/A45 | o que o T14 mudou (cronômetro, footer, mapa) |
| `scripts/mapa_sementes.py` (docstring) + `artifacts/mapa_sementes.json` | o modelo de alocação por semente |
| `claude_code_context/artifacts/envs.json` + `runs_matrix.csv` | envs por algoritmo · o grid (NUNCA gerado na hora) |
| `CONTRATO_DE_DADOS.md` | tudo que um run persiste (⑤ host/campanha_id incluídos) |
| `claude_code_context/40_subestudos/varredura_N_pisos.md` | o SUB-varN (P6) |
| `MAPA_ARTEFATOS.md` | mapa geral do repo |

---

*Gerado pela torre em 2026-08-01, após a validação final do T14 (suíte 826/0; HEAD `c797018`).
Qualquer conflito entre este documento e o código/artefatos do repo congelado: vale o repo —
e reporte a divergência em vez de escolher sozinho (D81).*
