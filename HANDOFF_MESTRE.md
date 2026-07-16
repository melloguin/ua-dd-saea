# HANDOFF MESTRE — Pipeline Experimental do Mestrado (survey + análise experimental SA-MOEA)

> **O que é este documento.** O repasse COMPLETO da fase de preparação (auditoria → SPEC v5.2 → correções mecânicas → higiene de repo → setup de infra executado) para a fase de **implementação**. Uma instância nova de Claude Code que ler este arquivo + os que ele aponta tem **todo** o conhecimento acumulado e deve agir exatamente como a instância anterior agiria. Data do repasse: **2026-07-15**.
>
> **Leia também, nesta ordem:** (1) este arquivo; (2) `START_HERE.md` (o passo-a-passo curto de arranque); (3) `claude_code_context/CLAUDE.md` (a porta de entrada operacional do agente); (4) o bundle da fase, indicado por `claude_code_context/PROMPT_MESTRE.md`.

---

## 0. Índice dos arquivos valiosos (onde está cada coisa)

| Arquivo | O que é |
|---|---|
| **`claude_code_context/SPEC_experimentos_v5.2.md`** | A **fonte única da verdade** (639 KB). Contém as 14 decisões D87–D100 e a "Higiene v5.2" já aplicadas. Consulta pontual — **nunca** leitura integral. |
| `claude_code_context/CLAUDE.md` | Porta de entrada do agente: regra de ouro do contexto, precedência, protocolo pára-e-loga, invariantes. |
| `claude_code_context/PROMPT_MESTRE.md` | Manual do autor: o template de prompt por sessão + tabela de quais arquivos ler por fase. |
| `claude_code_context/REGISTRO_DECISOES_pingpong_v5.md` | O "porquê" rico das decisões D53–D86 (histórico). |
| `claude_code_context/{00_fundacao..50_analise_R4}/` | **30 bundles cirúrgicos** GERADOS da SPEC por `gen_bundles.py` — o que cada sessão lê de fato. |
| `claude_code_context/gen_bundles.py` | Regenera os bundles da SPEC (rode após editar a SPEC). **Corrigido na v5.2** (não apaga CLAUDE.md/PROMPT_MESTRE; aponta p/ v5.2; epígrafes atualizadas). |
| `claude_code_context/artifacts/` | 8 artefatos machine-readable que o agente CONSOME (ver §6.4 abaixo). |
| **`cards/INDEX.md`** | Lista canônica dos **25 cartões-sessão** (F0→R4), com depende-de/bundle/status. `cards/_TEMPLATE.md` = molde. |
| `scripts/preflight.py` | Pré-voo: content-hash por repo + valida âncoras. **Já rodado** — 9 pendências capturadas (ver §7.4). |
| `scripts/accept.py` | Runner de aceitação OBJETIVA por cartão (só encanamento — D97). |
| `handoff/` | 1 arquivo por sessão fechada (continuidade). |
| `START_HERE.md` | Arranque curto para a 1ª sessão. |
| `HANDOFF_setup_executado.md` | **Relatório do autor** de como o setup foi executado (estado REAL da infra — ver §7). |
| `~/Downloads/DIAGNOSTICO_AUDITORIA_SPEC_v5.1.md` | O diagnóstico completo da auditoria (85 achados verificados, com evidência arquivo:linha). |
| `~/Downloads/SPEC_v5.2/` | Cópia da SPEC v5.2 + artifacts + `diff_v51_para_v52.txt` (o diff auditável v5.1→v5.2). |

---

## 1. Identidade e objetivo

- **Autor:** Guilherme de Mello Nunes · **Programa:** PPGCC/UFMG · **Orientadora:** Gisele · **Defesa alvo:** ~fim de setembro/2026 (prorrogação até 30/09 aprovada).
- **A dissertação:** um **survey sistemático + análise experimental** de **16 algoritmos SA-MOEA** que usam **explicitamente a incerteza do surrogate** na lógica de otimização (SA-MOO-UU). *(O algoritmo próprio do autor, UA-SA-NSGA-II, é trabalho futuro — NÃO entra nos experimentos.)*
- **Este repositório (`ua-dd-saea`)** é o **pipeline experimental**: roda os 16 algoritmos (de suas implementações OFICIAIS, sem reimplementar) sobre 25 problemas × 30 sementes, e exporta tudo para análise.
- **A meta concreta:** a **bateria principal = 16.500 runs** (12.750 online + 3.750 offline).

---

## 2. A jornada desta preparação (o que fizemos, em ordem)

1. **Leitura de contexto** — dois handoffs da dissertação, a transcrição da reunião com a orientadora, a planilha do corpus (130 artigos), o PDF da dissertação, o `.drawio` das figuras.
2. **Auditoria multi-agente pré-implementação** — 28 auditores (16 algoritmos + pisos + 5 de fundação + 6 lentes) cruzaram SPEC × bundles × **código real**; cada achado critical/major passou por **verificação adversarial**; + crítico de completude. Resultado: **85 achados confirmados / 29 refutados / 3 plausíveis**. Veredito: **nenhuma falha de projeto; os 16 algoritmos são viáveis**; os achados eram dessincronização de artefatos, texto stale de precedência alta e definições em aberto.
3. **Ping-pong de 15 decisões com o autor** (3 blocos) → viraram **D87–D100** na SPEC.
4. **SPEC v5.2** — as 14 decisões tecidas na estrutura existente (novas linhas no Anexo D §D.3 + carimbos nas seções + changelog + N.0-4.1 novo).
5. **Correções mecânicas ("Higiene v5.2")** — texto stale + regeneração dos 8 artefatos.
6. **Higiene de repo** — conserto do gitlink do e103, instalação do `claude_code_context/`, scaffolding (cards/scripts/handoff), `.gitignore` preciso.
7. **Setup de infra executado pelo autor** (Mac + VM Vertex) — ver §7 (estado REAL).

---

## 3. O desenho experimental (o que vai rodar) — o essencial

**Arquitetura A2 (§2, §16.5):** UMA fonte de cada problema (`src/problems.py`, 25 classes pymoo); cada algoritmo roda de sua implementação oficial em `algorithms/`; despachantes (`experiments.py` Python + `experiments.m` MATLAB) chamam a *main* oficial via adapters. Os algoritmos MATLAB avaliam os problemas Python via **ponte `pyenv` InProcess**.

**O grid:**
| Experimento | Configs | Probl. | Sem. | Runs |
|---|---|---|---|---|
| 1a Principal ONLINE (q=1) | 17 = 13 SA-MOEA + 4 pisos | 25 | 30 | 12.750 |
| 1b Principal OFFLINE | 5 = 4 SA-MOEA (b5r,b5m,c311,e103) + 1 piso | 25 | 30 | 3.750 |
| 2 Large-batch (q=10) | 4 + Sobol | ~5 | 30 | ~750 |
| 3 Sweep offline (tier×dist) | b5r/b5m/c311/e103 | ~5 | 30 | 2.700 |

*(16 algoritmos = 13 online + 3 offline. b5 roda como 2 configs b5r/b5m. Pisos = MOEA puros de referência, não algoritmos do estudo.)*

**Os 16 algoritmos e seus stacks:**
- **MATLAB/PlatEMO (Rodada 1, Mac):** b1 ParEGO, b3 K-RVEA, b4 CSEA, e7 EDN-ARMOEA, c217 PC-SAEA, c141 MMRAEA, e74 CLMEA, c238 EIM, e103 IBEA-MS (offline) + 4 pisos.
- **BoTorch (Rodada 2, VM):** c262 qNEHVI, c154 JES.
- **Standalone Python (Rodada 3, VM):** c122 θ-DEA-DP, b5 Prob-RVEA/MOEA-D (offline), c311 TGPR-MO (offline), c149 LBN-MOBO, e81 qPOTS + piso offline MOEA/D-média.

**Protocolo compartilhado:**
- `maxFE = 31D−1` (DoE inicial `11D−1` LHS + 20D infills). **Hard-stop exato.**
- 30 sementes {0–28, 42}. DoE/dataset **novos por semente, compartilhados por (problema, semente)**.
- **Export de 3 camadas** por run (Parquet): ① avaliações reais · ② população/geração · ③ camada surrogate (μ/σ por candidato × geração, TODAS as gerações). + log `.jsonl` de auditoria + camada de tempo. Volume: **~0,5–0,9 TB** (5 volumosos = bucket-only).
- **Métrica pós-hoc** (Python): IGD, IGD+, HV, GD, spacing + trajetória. Endpoint primário **IGD+**. Ref-point do HV = **1,1 em cada coordenada** no espaço normalizado.

---

## 4. As 15 decisões do ping-pong (D87–D100) — o coração deste handoff

> **Detalhe completo de cada uma: Anexo D §D.3 da SPEC.** Aqui, o resumo + o que o autor decidiu DIFERENTE ou COM RESSALVA (o mais importante de reter).

**Bloco 1 — protocolo de base:**
- **D87 — LHS-maximin PRÓPRIO + artefatos em PARQUET.** Rotina própria (~20 linhas, K candidatos sobre `Generator(PCG64)`, argmax da distância mínima) porque nenhuma lib satisfaz maximin+reprodutível. **Formato parquet (não .npy) — decisão do autor** ("por que .npy?"): os 2 stacks leem nativo → **eliminou a dependência de leitor .npy no MATLAB**. Hash é sobre o **array decodificado**, não o arquivo.
- **D88 — Invariante de inicialização unificada + CP-init.** (Resposta à pergunta do autor: "o DoE é IGUAL entre os 21 configs, cross-repo e cross-linguagem?" → **SIM, por construção**: artefato único por (problema, semente), sem alg_id; todos CARREGAM os mesmos pontos físicos.) CP-init verifica isso no F0.
- **D89 — Cache-hit = 0 FE (⚠ DECISÃO DO AUTOR, CONTRÁRIA à minha recomendação inicial).** Eu sugeri "duplicata = 1 FE"; o autor decidiu o oposto, com razão: o catálogo ① torna re-consulta gratuita como na prática real de otimização cara. **Identidade = X NATIVO bit-a-bit** (o autor esclareceu que "N casas decimais" foi força de expressão — é igualdade exata; near-duplicata paga 1 FE). O **wrapper de FE é a única fonte do orçamento nos 2 stacks** (o `obj.FE` nativo do PlatEMO NÃO governa o término).
- **D90 — Dataset offline como artefato parquet** (estende D63 ao offline; e103/b5/c311/piso só CARREGAM; pareamento cross-stack por construção).
- **D91 — `artifacts/seeds.json`** (torna a D62 executável: tabela alg_id→int + catálogo uso_id + materialização; desambigua D22×D62).
- **D92 — Âncora do smoke da métrica re-derivada: HV(BBOB F1) = 1,0433** (ref 1,1 por coordenada, sob D69). O antigo 0,8333 vira só sanity do front. Um gate em 0,8333 reprovaria implementação correta.

**Bloco 2 — fidelidade por algoritmo:**
- **D93 — e103: centros da RBFN = `⌈√(n_dataset)⌉`** com o n INJETADO (achado CRÍTICO: o "patch NO-OP" do Anexo S partia de premissa falsa; sem isso a RBFN subdimensiona e o eixo do sweep colapsa).
- **D94 — b1/e7: injeção do DoE substitui o par gera+re-escala** (ParEGO.m:29-30; EDNARMOEA.m:31-32) — bit-exato; injetar só na :29 causava dupla-escala em WFG/BBOB.
- **D95 — e74 = OPÇÃO A** (roda na árvore PlatEMO 4.1 própria `CLMEA_Code`, worker dedicado, adendo N.0-4.1 — o UserProblem 4.1 NÃO tem `once`, então a ponte avalia por indivíduo).
- **D96 — c149: HVI-greedy (q=1) FECHADA** (normalizado pelo arquivo OBSERVADO por iteração — nunca a S.5; ref = nadir-obs×1,1; desempate = maior σ²; fallback aleatório-do-front).

**Bloco 3 — processo e análise:**
- **D97 — VALIDAÇÃO DE FIDELIDADE = análise MANUAL do autor, a posteriori; NÃO é código (⚠ REFORMULAÇÃO DO AUTOR).** O autor esclareceu que a validação de fidelidade ("rodo, meço, comparo com o artigo, e EU julgo") é dele, a posteriori — nunca uma rotina no harness. O código só **instrumenta** (log `.jsonl` + dossiê Anexo J). **±3σ = faixa-guia do julgamento, não limiar automático.** O único gate automático é o de **encanamento objetivo** (FE exato, 4 saídas, CP-init/CP-bounds/CP-sinal, guardas). Declaração canônica no §20; reparo aplicado em ~14 pontos. **NÃO confundir** com mecanismos INTERNOS de algoritmo (teste 3σ do e103; gate ±0,95 do c217 = código do algoritmo, intocados).
- **D98 — characteristics.csv = propriedade objetiva** (achado CRÍTICO: rótulos errados vs Huband; a matriz será re-derivada e congelada PELO AUTOR antes do R4). **Camada de análise.**
- **D99 — IGDX pós-hoc para os 4 MMF** (multimodalidade decisória; custo zero, do ① salvo). **Camada de análise.**
- **D100 — Fronteira implementação × análise (⚠ RE-ESCOPO DO AUTOR).** O export "salvar-tudo" DESACOPLA experimento de análise → **decisões de análise NÃO bloqueiam a implementação**; o pipeline só precisa produzir dados completos e válidos; a análise (D98/D99/testes estatísticos) o autor refina/implementa depois (R4). **Deferidos pelo autor:** família/controle dos testes (§14), backup (o autor faz manual — D64), consolidação/custo/cronograma.

---

## 5. O que mudou na SPEC (v5.2 → o que a torna definitiva)

- **Anexo D §D.3:** +14 linhas D87–D100 (nota de origem antes da tabela) + carimbos `(v5.2 — Dxx)` nas linhas antigas afetadas (D57/D62/D63/D64/D67/D82).
- **Carimbos `[v5.2 — Dxx]`** nas seções tocadas: §0, §5.2, §5.4, §5.5 (CP-init), §7/§9/§11.5, §12/§12.2, §15, §17.5/§17.5.1, §20 (declaração canônica D97), §22.0/§22.1/§22.2/§22.4/§22.5/§22.6, Anexo J, Anexo N (**N.0-4.1 novo**), Anexos L/S.
- **"Higiene v5.2"** (correções mecânicas de dessincronização, aplicadas depois): naming de export com o token **`{exp}`** (bug crítico de colisão main×sub-estudos); cartão R1 `zstd/round3`→`brotli/sem-round`; §17.4 teto-500 + "25–50 GB" → tombstones (D53/D54, real 0,5–0,9 TB); piso offline built-in → tombstone D77; "(1,1,…)" → "1,1 por coordenada".
- **Changelog no topo + registro no Anexo R.**
- Verificação: **0 quebra de markdown nova** (as 3 linhas com `**` ímpar são pré-existentes da v5.1). Diff auditável em `~/Downloads/SPEC_v5.2/diff_v51_para_v52.txt`.

---

## 6. Os artefatos machine-readable (o que o agente consome — `claude_code_context/artifacts/`)

| Artefato | O que é / estado v5.2 |
|---|---|
| `runs_matrix.csv` | As 19.950 linhas do grid. **Corrigido:** o sweep ganhou o token `sweep-{tier}-{dist}` no run_id → **0 duplicatas** (era 600 dup). |
| `envs.json` | Tabela alg→env + 7 ambientes. **Corrigido:** `env_b5` e `env_c311` SEPARADOS (pins mutuamente exclusivos); `env_main` (harness+BO+c122+c149); `env_bridge` (ponte); fallback c149. |
| `seeds.json` | **NOVO (D91):** alg_id→int + catálogo uso_id + materialização + offset D22. |
| `params.json` | **NOVO (D83):** parâmetros Balde B por config (índice do §6.4). |
| `anchors.json` | **20 patches** (era 5): nomes de arquivo corrigidos, `expect_before`/`expect_after`, + D93/D94/D95 e faltantes. *(Ainda tem pendências que o preflight achou — §7.4.)* |
| `decisions.json` | Índice D53–D100 (+14). |
| `characteristics.csv` | Matriz 25×8 — **NÃO corrigida** (é a D98, o autor re-deriva antes do R4). |
| `repos.lock` | Pin por content-hash dos 8 repos sem .git (preenchido pelo preflight). |

---

## 7. O ESTADO REAL DO SETUP (do relatório do autor — LEIA COM ATENÇÃO)

> Isto substitui o "idealizado" da SPEC pelo estado verificado. Fonte: `HANDOFF_setup_executado.md`.

### 7.1 — Ambientes
- **Mac:** macOS 12.5.1 Monterey, **arm64**. Papel: MATLAB (R1) + Fase 0 + pilotos. Grava só local.
  - **env-main (Mac): ✅ provisionado 2026-07-15** sobre pyenv 3.11.9 em `/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao` (interpretador `.../bin/python`; usar por CAMINHO COMPLETO — o shell do Claude Code não preserva `activate`). Núcleo do harness verificado (import + round-trip parquet float64 + pymoo). Versões em `<venv>/requirements.lock`. **⚠ pandas resolveu 3.0.3** (avaliar pin `>=2,<3` p/ reprodutibilidade). Falta, no mesmo venv, o stack de R2 (`botorch==0.18.1`/torch/gpytorch/gcs/deap). A partir do F0-02 as sessões Python rodam SOB este interpretador.
- **VM Vertex:** `v5-mestrado`, **Debian 12**, usuário `jupyter`, zona **`us-central1-a`**, com **micromamba (base)** + pyenv. Papel: Python (R2/R3) + análise. Grava local **e** bucket.
- **Regra de fluxo:** toda config Python é nos DOIS (Mac + VM); MATLAB só no Mac. Ao instruir, Mac primeiro, VM depois.

### 7.2 — O que está pronto ✅
- **pyenv 2.8.0** nos dois, com **3.11.9 / 3.10.14 / 3.8.19** carregando em shell novo.
- **MATLAB R2025a Update 1**, 4 toolboxes ✓, **8 workers** PCT no Mac.
- **Ponte MATLAB↔Python validada ponta a ponta** (round-trip `py.numpy.array([1,2,3]).sum()` → 6).
- **gcloud SDK 576** + ADC no Mac; conta dona `gdmello.nunes@gmail.com`.
- **Bucket `gs://mestrado_experiments`**: STANDARD, **US multi-região**, soft-delete 7d, **versionamento ON**.
- Conta de serviço da VM (`376980290238-compute@developer.gserviceaccount.com`) já cria/lê/lista/apaga no bucket (testado, sem IAM extra).

### 7.3 — Correções de SETUP que ajustam a SPEC (RETER!)
1. **`--enable-shared` é Mac-only.** O modo InProcess do MATLAB (§18) exige `libpython3.11.dylib`. O 3.11.9 do Mac **já tem** (5,4 MB — veio do build reinstalado). Se precisar recompilar: `env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install -f 3.11.9` (invalida venvs sobre ele). A VM NÃO precisa disso; 3.10/3.8 também não.
2. **Licença MATLAB é Academic Total Headcount (TAH), não Individual.** A ressalva do §21.3 ("teto de ativações = teto do paralelismo") **NÃO se aplica**. O gargalo real são os **8 workers PCT no Mac**. Adicionar 2ª máquina MATLAB é legalmente livre (opção, não necessidade).
3. **Bucket:** o autor tinha um bucket em classe **Archive** (errado — custo de leitura alto + duração mínima 365d, colide com a releitura de 0,9 TB). Trocado por `mestrado_experiments` STANDARD.
4. **Região:** o bucket é **multi-região `us`** (decisão consciente do autor, mesmo com a VM em us-central1) — custo modesto coberto por créditos. **Não "corrigir" para regional sem falar com o autor.**
5. **env-main resolve no Mac arm64:** numpy 2.4.6, pymoo 0.6.2, scipy 1.17.1 (todos wheels arm64) — os pins modernos da S.6 fecham sem conflito.

### 7.4 — As 9 pendências do preflight (a 1ª sessão resolve)
- **Família A — path do arquivo não bate (3):** `e74-mask` (Local_infill.m), `e74-ndsort-obj` (ClassifierSelect.m), `b5-mode72-kde` (ProbMOEAD_select.py). *Ação:* `find` o arquivo real e corrigir o path no `anchors.json`.
- **Família B — `expect_before` ausente (4):** `b1-mse-guard-L8` (EvolALG.m), `b4-cap109` (CSEA.m), `e81-offset1`, `e81-offset2` (acquisition.py). *Ação:* abrir o arquivo, achar a linha real, reajustar a âncora.
- **Família C — placeholders (2):** `repos.lock <SHA>` e `envs.json <PIN A CRAVAR>` (o desdeo-emo do b5 — **intencional, resolve no gate R3.2**).

### 7.5 — Pendências de otimização (não bloqueiam)
- Regra de **lifecycle** no bucket (apagar versões não-correntes após ~30d, controlar custo do versionamento).
- **Dimensionamento de VMs** (núcleos, spot, VM ~1,5 TB para R4) — decidido **após o piloto de timing** (§19/§21.3).

### 7.6 — Identificadores-chave
- Projeto GCP: **`skilled-text-480300-d9`** (número **376980290238**).
- Bucket: **`gs://mestrado_experiments`**.
- SA da VM: **`376980290238-compute@developer.gserviceaccount.com`**.
- Conta gcloud: **`gdmello.nunes@gmail.com`**.
- MATLAB License **40904996**, TAH, exp. 31/Jan/2027.

---

## 8. O PLANO DE IMPLEMENTAÇÃO (ordem, gates, quem faz o quê)

**Ordem (D84 / §22) — NUNCA tudo de uma vez; pattern-setter primeiro, depois fan-out:**
```
Pré-voo (resolver as 9 âncoras)
   ▼
Fase 0 (harness compartilhado)  →  gate F0 (accept.py verde)
   ├─ R1 MATLAB (Mac):  R1-00-harness → R1-c217 (CASO-MODELO — validar ponta-a-ponta) → fan-out (b1,b3,b4,e7,c141,e74,c238,e103,pisos)
   ∥ R2 BoTorch (VM):   R2-00-harness → R2-c262 (pattern-setter) → c154
   → R3 standalone (VM, UM POR UM): c122 → b5 → c311 → c149 → e81 → piso offline
   → sub-estudos (batch, sweep, varredura N)  →  R4 análise (o AUTOR refina/implementa)
```
- **Execução em PARALELO por stack:** ao fechar o gate de uma rodada, a bateria dela roda (semanas, desassistida) enquanto as outras são implementadas e o survey é escrito.
- **O gate mais importante:** **R1-c217 ponta-a-ponta** (harness + adapter + export + DoE + métrica + piloto). Se fecha verde, o pipeline está provado.

**Gate por cartão = (A) `python scripts/accept.py {CARTAO}` verde (encanamento objetivo) + (B) aval de fidelidade MANUAL do autor no piloto (D97).**

**Quem faz o quê:**
- **Autor (Guilherme):** dispara as sessões; dá o aval de fidelidade nos pilotos; decide os pins de env nos gates (desdeo-emo, sklearn); roda a bateria nos seus recursos; backups manuais; dimensiona VMs após o piloto.
- **Claude (sessões frescas, 1 cartão/sessão):** o código — Fase 0, os adapters/patches de cada algoritmo, a camada de métrica (depois).

---

## 9. Como a próxima instância DEVE agir (princípios inegociáveis)

1. **Leia SÓ o necessário** (CLAUDE.md + o bundle do cartão + os artefatos) — nunca a SPEC inteira, nunca este handoff a cada sessão.
2. **1 sessão = 1 cartão.** Ao fechar, escreva `handoff/{CARTAO}.md`. A próxima sessão começa lendo o anterior.
3. **Validação de fidelidade = MANUAL do autor, a posteriori (D97).** O agente só instrumenta + aplica o gate objetivo. **Nunca** auto-conserta fidelidade; **nunca** julga "está fiel".
4. **Ambiguidade / conflito ⇒ PARE e pergunte (D81).** Nunca escolha sozinho o que a SPEC não fixa.
5. **Precedência (D83):** Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos. Em divergência bundle×SPEC, vale a SPEC.
6. **Padrão de trabalho do autor:** decisão em ping-pong (opções + prós/contras + recomendação + o porquê; o autor bate o martelo); exige evidência, corrige rápido, valoriza honestidade acima de concordância; idioma português.
7. **Regenerou a SPEC? Rode `python gen_bundles.py`** (a SPEC é a única fonte; bundle editado à mão é dessincronização plantada).

---

## 10. Sessão 1 (pré-voo) — CONCLUÍDA e VERIFICADA (2026-07-15)

A 1ª sessão de implementação resolveu as 9 pendências: **8 resolvidas + 1 deferimento intencional** (pin do `desdeo-emo`, cravado no gate R3.2). `python3 scripts/preflight.py --write` → **`pré-voo OK ✓`, exit 0, idempotente**. Alterou só 3 arquivos (`anchors.json`, `repos.lock`, `scripts/preflight.py`); **zero código de algoritmo**; `envs.json` intacto. Relatório completo: `handoff/00-preflight_RELATORIO-EXECUCAO.md`.

Verifiquei de forma **adversarial** (5 verificadores independentes tentando refutar). Todos **CONFIRMED**, com destaque para o ponto sensível: a Sessão 1 mexeu no `preflight.py` (o próprio portão), mas **refinou** (isolou o deferimento `<PIN A CRAVAR` do bloqueio) sem **enfraquecer** — `<SHA>`/`<PIN>` genuínos ainda dão exit 1 (provado por injeção numa cópia).

**Reclassificações do §7.4 que a Sessão 1 corrigiu (reter):**
- **e81** não era "âncora divergente" (Família B) — era **colisão de basename no preflight** (havia `acquisition.py` em `_BoTorch` e em `e81_qPOTS`); consertou o **tooling** (resolução por sufixo), não a âncora.
- **e103** virou **arquivos planos** (sem `.git`) e faltava no `dir_map` do preflight → agora é o 9º repo content-hash; `sha:null`.
- **`python` → `python3`**: neste Mac só há `python3`. Padronizar as instruções de arranque.

## 11. ⚠️ Notas de verificação para cartões FUTUROS (armadilhas latentes)

Duas fragilidades que **não** afetam o estado atual, mas mordem se ignoradas na implementação:

1. **Cartão b1 (ParEGO): o patch do `sqrt(mse)` DEVE ser escopado ao arquivo.** O token `sqrt(mse);` é único DENTRO de `EvolALG.m` (ParEGO), mas **também existe** em `_PlatEMO/.../Single-objective optimization/EGO/EvolEI.m:23`. Um find/replace repo-wide corromperia o EvolEI.m. **Aplicar o patch SÓ em** `algorithms/_PlatEMO/PlatEMO/Algorithms/Multi-objective optimization/ParEGO/EvolALG.m` (o `file` da âncora já diz isso — respeitar).
2. **Tooling do preflight: âncoras precisam carregar o prefixo de diretório, não só o basename.** A resolução por sufixo (`endswith`) só desempata a colisão `acquisition.py` porque a âncora do e81 diz `qpots/acquisition.py`. Se alguma âncora futura trouxer só `acquisition.py` (basename puro), ela resolveria silenciosamente para a cópia do `_BoTorch` (a 1ª no `os.walk`) — arquivo errado. **Toda âncora nova deve incluir ao menos um segmento de diretório.** (Idem `c149`, cujo arquivo tem 4 cópias — hoje OK porque a âncora carrega o caminho.)

---

*Fim do handoff mestre. Foi um prazer construir esta preparação. Boa implementação — e boa defesa.*
