# ORQUESTRAÇÃO MESTRE — control tower da implementação (versão técnica, para o orquestrador)

> **Uso:** referência operacional da instância-orquestradora (eu). Guia a montagem de cada prompt de cartão, os gates, e o estado. Fonte da verdade continua sendo `claude_code_context/SPEC_experimentos_v5.2.md` + `cards/INDEX.md`; este arquivo é o **plano de execução** por cima deles. Par didático: `PLANO_IMPLEMENTACAO.md`. Atualizar o **Status board** a cada handoff recebido.

## Invariantes que EU imponho ao montar cada prompt (checklist pré-envio)
- [ ] **1 cartão / sessão** (D83). O prompt cobre exatamente 1 ID de `cards/INDEX.md`.
- [ ] **Leitura mínima** (regra de ouro CLAUDE.md §0): `HANDOFF_MESTRE.md` (orientação) + `handoff/{cartão_anterior}.md` + `claude_code_context/CLAUDE.md` + os bundles do cartão (mapa PROMPT_MESTRE §"como preencher") + artefatos sob demanda. **Nunca** a SPEC inteira nem bundles de outros algoritmos.
- [ ] **`python3`**, não `python` (só há python3 no Mac; padronizar em todo comando).
- [ ] **D81** (pára-e-pergunta em ambiguidade/conflito) e **D97** (nunca auto-consertar fidelidade; accept.py só encanamento) explícitos no prompt.
- [ ] **Precedência D83** no conflito: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos; bundle×SPEC ⇒ vale a SPEC.
- [ ] Se o cartão toca ponto transversal (ponte/export/watchdog), incluir o `00_contrato_*` da rodada mesmo em sessões 2+.
- [ ] Gate objetivo do cartão nomeado: `python3 scripts/accept.py {ID}` + o gate específico do bundle.
- [ ] Handoff de saída nomeado: `handoff/{ID}.md`.
- [ ] Após QUALQUER edição da SPEC: rodar `python3 gen_bundles.py` (bundle à mão = dessincronização plantada).

## Matriz de ambientes
| Ambiente | Papel | Grava onde |
|---|---|---|
| **Mac** (arm64, macOS 12.5.1) | MATLAB R2025a → R1; Fase 0; pilotos; ponte InProcess (`--enable-shared`, Mac-only) | local |
| **VM** `v5-mestrado` (Debian 12, micromamba+pyenv, us-central1-a) | R2 (BoTorch), R3 (standalone), R4 (análise) | local **+** `gs://mestrado_experiments` (dual-write) |
| **Bucket** `gs://mestrado_experiments` | STANDARD, US multi-região, versioning on, soft-delete 7d | — |
- Config Python nos DOIS ambientes; MATLAB só no Mac. Bucket-only (só bucket, não local): **c154, c122, e81, c149, c262** (D58).

### Venvs × algoritmos (detalhe + estratégia: `requirements/README.md`)
- **Contagem:** 4 venvs Python que rodam algoritmos (`env_main`→c262/c154/c122/c149 · `env_e81_qpots`→e81 · `env_b5`→b5r/b5m/moead_media · `env_c311`→c311) + `env_bridge` (ponte MATLAB, não roda alg) + `env_c149_fallback` (condicional). **MATLAB = 0 venv** (1 instalação; isolamento por árvore PlatEMO + ponte).
- **Manifestos:** `requirements/<env>.txt` (1 por ambiente) + `requirements/env_matlab.md`. Venvs em `/Users/gmello/Documents/python_venvs/<nome>`. Provisionar just-in-time: `pip install -r requirements/<env>.txt` + `pip freeze > <venv>/requirements.lock`.
- **Viabilidade Mac (honesta):** `env_main` ✅ (feito) · `env_bridge` ✅ **provisionado 2026-07-16 (`~/ponte_teste` + numpy/pymoo0.6.2/pyarrow25; MATLAB aponta pra ele)** · `env_e81_qpots` ⚠ verificar pins · **`env_b5`/`env_c311` ❌ inviáveis no Mac arm64 (sklearn 0.21.3 / numpy 1.20.2 sem wheel) → só na VM Linux.** Por isso NÃO se cria tudo no Mac; os `.txt` ficam prontos e cada venv nasce no ambiente certo, no seu milestone.

> **⚠ ENV-MAIN — ✅ Mac PROVISIONADO (2026-07-15), verificado por mim (import + round-trip parquet float64 + pymoo DTLZ2):** venv sobre pyenv 3.11.9 em `/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao` → interpretador **`/Users/gmello/Documents/python_venvs/mestrado_experimentos_dissertacao/bin/python`** (usar por CAMINHO COMPLETO em todo prompt/comando; o shell do Claude Code não preserva `activate`). Núcleo instalado: numpy 2.4.6, **pandas 3.0.3 (⚠ avaliar pin `>=2,<3`)**, pyarrow 25, pymoo 0.6.2, scipy 1.17.1, joblib, tqdm, sklearn 1.9 — lock em `<venv>/requirements.lock`. **FALTA no mesmo venv antes do M4/R2:** botorch==0.18.1, torch, gpytorch, google-cloud-storage, deap. Pins/versões = decisão do AUTOR (D80); o agente NUNCA instala. VM: provisionar o mesmo env-main antes de R2/R3.

## Plano por milestone (cards · gate · env · risco)
| M | Cards (ordem) | Env | Gate objetivo | Gate fidelidade (autor) | Riscos/notas |
|---|---|---|---|---|---|
| **M0** ✅ | pré-voo | Mac | preflight OK ✓ exit 0 | — | feito+verificado (5 verificadores) |
| **M1** | F0-01-harness → F0-02-doe → F0-03-export → F0-04-metrica | Mac | accept.py verde; **CP-init bit-idêntico** (Py↔MATLAB); smoke **HV F1=1,0433** (D92) | — (sem algoritmo) | DoE parquet D87; hash sobre array decodificado; FE wrapper cache-hit=0 D89; escrita atômica D58 |
| **M2** 🔑 | R1-00-harness → R1-c217 | Mac | accept.py verde; FE=31D−1 exato; 4 saídas; CP-*; **ponta-a-ponta** | **1ª validação** (c217 vs paper PC-SAEA; ±3σ=faixa-guia) | contrato N.0; 2 guardas SAS:21/:39; DoE injetado; rng após Problem (D59) |
| **M3** | R1-b1, b3, b4, e7, c141, e74, c238, e103, pisos (paralelizável) | Mac | accept.py verde por alg | validação por alg no piloto | **b1: patch `sqrt(mse)` SÓ no EvolALG.m do ParEGO** (existe em EGO/EvolEI.m); **e74: árvore 4.1 própria, N.0-4.1, worker dedicado (D95)**; **e103: centros √n_dataset (D93), offline, worker dedicado**; b1/e7: injeção DoE substitui gera+re-escala (D94); b4: cap109→11D−1 |
| **M4** | R2-00-harness → c262 → c154 | VM | accept.py verde; dual-write GCS OK | validação por alg | contrato N.1; c154 JES = curinga de custo; env_main (BO) |
| **M5** | R3-00-harness → c122 → b5(b5r/b5m) → c311 | VM | accept.py verde; **gate R3.2: cravar pin desdeo-emo** em envs.json | validação por alg | **venvs isolados: b5(env_b5) × c311(env_c311) NUNCA co-importar**; b5/c311 offline; c122 f_min/f_max pela assinatura |
| **M6** | R3-c149 → e81 → piso-off | VM | accept.py verde | validação por alg | **c149: reconstruir loop HVI-greedy (D96)**; **e81: env botorch 0.16.1 próprio; offset +1000·s (D22)**; piso-off = MOEA/D-média DESDEO mode 12 (D77) |
| **M7** | (checkpoint, não-cartão) piloto §22.5 | Mac+VM | **BLOQUEANTE**: tempo+**pico RAM (D86)** dos curingas (c149, JES, c311 O(n³)) medidos; VM sizing/spot/lifecycle decididos | — | estouro ⇒ escalonamento já decidido (D75/D59/vetorizar-c311); nunca improvisar |
| **M8** 🚀 | bateria ONLINE (17×25×30=12.750) | Mac+VM | todos run_id presentes; manifestos OK; 0 `failed` silencioso | — | esteira idempotente/resume; dual-write; monitorar; backups manuais (autor) |
| **M9** | bateria OFFLINE (5×25×30=3.750) | VM (+Mac e103) | idem | — | dataset offline (D90) pareado por construção |
| **M10** | SUB-batch (q=10, D66, ~750) | VM | idem | — | Sobol; ~5 problemas |
| **M11** | SUB-sweep (tier×dist, D67, run_id `sweep-{tier}-{dist}`, ~2.700) + SUB-varN (D65) | VM | idem | — | depende de e103/R3 (sweep) e pisos (varN) |
| **M12** | consolidação/integridade | VM | contagem = 16.500 + sub; manifestos íntegros; backup | — | conferir bucket vs runs_matrix.csv |
| **M13** | R4: characteristics.csv (D98) + métricas | VM | — (camada de análise) | autor re-deriva/congela D98; IGD+ primária D70; ref HV 1,1 normalizado D69 | D100: análise não bloqueia; autor refina/implementa |
| **M14** | R4: testes estatísticos + IGDX (D99) + multiplicidade/Holm (§14, deferido) | VM | — | autor | Holm foi deferido no bloco 3 |
| **M15** | tabelas/figuras → dissertação | VM+escrita | — | autor | integra survey |

## Mapa de bundles por cartão (para preencher `{ARQUIVOS_DA_FASE}`)
- **Fase 0 (qualquer F0-*):** os 5 de `00_fundacao/` (01→05). [F0-02 foca 01,05; F0-03 foca 03; F0-04 foca 04+50_analise_R4 — mas ler os 5 uma vez na 1ª sessão.]
- **R1 alg X:** `00_fundacao/01` + `03` + (1ª sessão da rodada: `10_rodada1_matlab/00_contrato_rodada1.md`) + `10_rodada1_matlab/alg_{X}.md`.
- **R1 pisos:** `10_rodada1_matlab/00_contrato_rodada1.md` + `alg_pisos_online.md`.
- **R2 c262/c154:** `20_rodada2_botorch/00_contrato_rodada2.md` + `alg_{X}.md`.
- **R3 c122/b5/c311/c149/e81/piso-off:** `30_rodada3_standalone/00_contrato_rodada3.md` + `alg_{X}.md`.
- **Sub-estudos:** o `.md` correspondente em `40_subestudos/`.
- **R4:** `50_analise_R4/metricas_estatistica_caracteristicas.md` + `artifacts/characteristics.csv`.

## Catálogo de gates
1. **F0 CP-init/smoke** (M1): DoE bit-idêntico Py↔MATLAB (5 amostras); HV F1=1,0433.
2. **c217 ponta-a-ponta** (M2): o gate que prova harness+adapter+DoE+export+métrica juntos. Prioridade máxima.
3. **Gate R3.2** (M5): cravar pin `desdeo-emo` (único deferimento do pré-voo).
4. **Piloto de timing §22.5** (M7): **BLOQUEANTE** antes de qualquer bateria de 30 sementes. Tempo + pico de RAM (D86).
5. **Consolidação** (M12): completude (todo run_id), zero `failed` silencioso.
- Regra transversal: gate vermelho ⇒ pára-e-loga (D81); fidelidade nunca é gate automático (D97).

## Armadilhas conhecidas (verificadas / da SPEC) — repassar ao prompt do cartão certo
- **b1:** patch `sqrt(mse)` escopado ao `_PlatEMO/.../ParEGO/EvolALG.m` (colide com `EGO/EvolEI.m:23`). [verificado 2026-07-15]
- **Âncoras novas:** sempre com prefixo de diretório (resolução por sufixo do preflight; basename puro pega cópia errada, ex. `_BoTorch/acquisition.py`). [verificado]
- **e74:** árvore PlatEMO 4.1 própria (`CLMEA_Code`), adendo N.0-4.1 (UserProblem 4.1 sem `once` → ponte por indivíduo), worker dedicado (D95).
- **e103:** centros RBFN = ⌈√n_dataset⌉ com n injetado (D93); offline; worker dedicado.
- **b5×c311:** venvs mutuamente exclusivos, NUNCA co-importar (pins incompatíveis).
- **e81/c149:** offset de semente +1000·s (D22); e81 em env botorch 0.16.1 próprio.
- **Bucket-only (D58):** c154, c122, e81, c149, c262.
- **✅ DESYNC BBOB RESOLVIDA (2026-07-15):** canônico = **`BBOB_F1/F5/F17/F22/F37/F49/F55`** (nome da SPEC §4 / characteristics / runs_matrix). O anômalo era o token CURTO `BBOB1…` nas 7 chaves de `experiment.py` + os folders do DoE. Renomeei p/ `BBOB_F*` e regenerei os 7 BBOB — **valores INALTERADOS** (o seed usa o índice `problema_id`, não a string; hashes idênticos ao baseline), gate verde, prova MATLAB vale por identidade de conteúdo. `runs_matrix`/`characteristics` já estavam corretos (nada a mudar neles).
- **F0-03 verificado adversarialmente (2026-07-16, 6 lentes):** hard-stop exato 31D−1, cache-hit=0 bit-a-bit (bordas -0.0/+0.0/NaN/2D/dtype OK), solution_id dedup, float32-sem-round, schema §17.2/mono-output — **todos CONFIRMED**. **2 itens de robustez (NÃO-corrupção, endereçar antes do M8):** (1) **órfão `.tmp` em kill duro (SIGKILL/power/spot-preempt):** a atomicidade do arquivo FINAL vale sempre (nunca corrompe, resume não é enganado — `is_run_done` só olha layers+manifesto), mas o `finally` não roda sob SIGKILL → `.tmp` órfãos ACUMULAM. **Crítico p/ spot VMs no M8** → adicionar varredura de `.tmp` stale no arranque/esteira (R2-00/R3-00 ou cartão de hardening). (2) **mu/sigma MAIS LONGO que M é truncado em silêncio** no `write_surrogate` (o caso b1 `len<M` está perfeito; falta guarda p/ `len>M`) → assert/warning defensivo. (3) Consequência de design (não-bug, D89): -0.0/+0.0 e NaN de payloads distintos contam como soluções distintas (2 FE) — ciente na validação de fidelidade.
- **Seed do DoE (F0-02, ratificar):** o agente fixou `SeedSequence((semente, problema_id))` SEM alg_id — consistente com D88 (DoE único por problema×semente, todos carregam o mesmo). Ratificado; `PY -m src.doe --force` regenera em 87 s se mudar.
- **Blob de DoE/datasets (F0-02, ~97 MB):** `.gitignore` rastreia `data/doe`+`data/datasets`, mas não foi commitado. Decisão do autor (D64): git vs bucket vs regenerar-por-máquina. Recomendo **bucket** (garante identidade Mac↔VM sem inchar o git; regeneração cross-plataforma tem risco de ULP).

## Status board (atualizar a cada handoff)
```
M0 pré-voo ................................. ✅ (verificado)
M1 F0-01-harness ........................... ✅ (verificado 2026-07-15: accept verde, 17 tests, 0 algos tocados)
   F0-02-doe ............................... ✅ (verificado 2026-07-15: accept verde, 27 tests, 750 DoE+755 datasets, MATLAB CP-init PASS=1505, 0 algos tocados)
   F0-03-export ........................... ✅ (verif. adversarial 6 lentes: 5 CONFIRMED + 1 PARTIAL não-corrupção; hardening .tmp/mu>M p/ M8)
   F0-04-metrica .......................... ✅ (verif. por leitura + probe: âncora HV(BBOB_F1)=1,04333 D92, normalização/IGD+/HV corretos; 62 tests) → FASE 0 COMPLETA
M2 R1-00-harness (MATLAB) ................... ✅ (verif. torre 2026-07-16: CP-init cross-lang MATCH, schema §17.2 idêntico, FE exato 4 probl., MATLAB-only; fix check_fe deriva D da ①)
   R1-c217 (caso-modelo 🔑) ................. ✅ PROVADO (verif. torre 2026-07-16: gate VERDE em MMF1/ZDT1/DTLZ2/DTLZ2_d15, FE=31D−1 exato mesmo c/ cache-hits, schema §17.2, CP-init; fidelidade = julgamento do autor D97, pendente) → M2 COMPLETO, pipeline PROVADO
M3 fan-out MATLAB (b1,b3,b4,e7,c141,e74,c238,e103,pisos) . 🟡 PRÓXIMO — herda o FIX D89 do c217 (obj.FE=bud.fe; todo PlatEMO)
M4 R2-00-harness (BoTorch/VM) ............... ⬜ pode ir ∥ (na VM)
M2 R1-00-harness / R1-c217 ................. ⬜
M3 b1 b3 b4 e7 c141 e74 c238 e103 pisos .... ⬜×9
M4 R2-00 / c262 / c154 ..................... ⬜×3
M5 R3-00 / c122 / b5 / c311 (+gate R3.2) ... ⬜×4
M6 c149 / e81 / piso-off ................... ⬜×3
M7 piloto timing (BLOQUEANTE) .............. ⬜
M8 bateria ONLINE (12.750) ................. ⬜
M9 bateria OFFLINE (3.750) ................. ⬜
M10 SUB-batch .............................. ⬜
M11 SUB-sweep / SUB-varN ................... ⬜
M12 consolidação ........................... ⬜
M13 características+métricas ................ ⬜
M14 estatística+IGDX ....................... ⬜
M15 dissertação ............................ ⬜
```

## Loop de orquestração (o que EU faço a cada rodada)
1. Recebo `handoff/{cartão}.md` do autor. **Verifico** (leitura + gate; adversarial se o cartão mexeu em infra crítica/gate).
2. Atualizo o Status board + a memória `implementacao-experimentos-estado`.
3. Registro armadilhas novas descobertas (aqui + HANDOFF_MESTRE §11).
4. Monto o prompt do próximo cartão (checklist de invariantes acima) e entrego ao autor.
5. Em fim de rodada, confirmo pré-requisitos do próximo gate (ex.: M7 antes de M8).
