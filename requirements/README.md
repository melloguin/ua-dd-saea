# requirements/ — ambientes virtuais × algoritmos (estratégia de provisionamento)

> Um arquivo por ambiente. Cada um é o manifesto de instalação (`pip install -r requirements/<env>.txt`)
> do venv que roda um ou mais dos 21 configs. Derivado de S.6/D79 da SPEC e de `claude_code_context/artifacts/envs.json`.
> Venvs Python ficam em **`/Users/gmello/Documents/python_venvs/<nome>`**. Data: 2026-07-15.

## Resposta rápida (quantos ambientes)
- **Venvs Python que rodam algoritmos: 4** — `env_main`, `env_e81_qpots`, `env_b5`, `env_c311`.
- **+ 1 venv-ponte** (`env_bridge`) — infraestrutura que o MATLAB embute p/ avaliar os problemas (não roda algoritmo).
- **+ 1 condicional** (`env_c149_fallback`) — criado **só** se o piloto do c149 divergir do env-main.
- **MATLAB: 0 venvs.** MATLAB não tem ambiente virtual — é **1 instalação** (R2025a + toolboxes). Ver `env_matlab.md`.

## Por que não é 1:1 (e por que é conservador)
Cada algoritmo roda da sua implementação oficial, com pins que às vezes **conflitam** entre si
(botorch 0.16.1 do e81 vs 0.18.1 do env-main; sklearn 0.21.3 do b5 vs 1.1.2 do c311; numpy 2.x vs 1.20.2).
Agrupamos por **compatibilidade**: onde os pins convivem, um venv serve vários algoritmos; onde brigam, isolamos.
É deliberadamente conservador — melhor um venv a mais do que um import errado que corrompe um resultado em silêncio.

## Mapa venv ↔ algoritmo (os 21 configs = 13 online + 3 offline + 5 pisos)
| Config | Tipo | Stack | Ambiente | Onde roda | Nota |
|---|---|---|---|---|---|
| b1 ParEGO | online | MATLAB | env_matlab | Mac | |
| b3 K-RVEA | online | MATLAB | env_matlab | Mac | |
| b4 CSEA | online | MATLAB | env_matlab | Mac | |
| e7 EDN-ARMOEA | online | MATLAB | env_matlab | Mac | |
| c217 PC-SAEA | online | MATLAB | env_matlab | Mac | caso-modelo |
| c141 MMRAEA | online | MATLAB | env_matlab | Mac | |
| e74 CLMEA | online | MATLAB | env_matlab | Mac | **árvore PlatEMO 4.1 própria** (D95) |
| c238 EIM | online | MATLAB | env_matlab | Mac | |
| c262 qNEHVI | online | Python | **env_main** | VM (dev Mac) | |
| c154 JES | online | Python | **env_main** | VM (dev Mac) | |
| c122 θ-DEA-DP | online | Python | **env_main** | VM (dev Mac) | driver próprio + deap |
| c149 LBN-MOBO | online | Python | **env_main** (fallback `env_c149_fallback`) | VM (dev Mac) | |
| e81 qPOTS | online | Python | **env_e81_qpots** | VM (dev Mac) | botorch 0.16.1 (≠ env-main) |
| e103 IBEA-MS | offline | MATLAB | env_matlab | Mac | **worker dedicado** (D93) |
| b5 (→ b5r + b5m) | offline | Python | **env_b5** | **VM Linux** | 2 configs; sklearn 0.21.3 |
| c311 TGPR-MO | offline | Python | **env_c311** | **VM Linux** | GPy; numpy 1.20.2 |
| nsga2 (piso) | piso online | MATLAB | env_matlab | Mac | |
| nsga3 (piso) | piso online | MATLAB | env_matlab | Mac | |
| moead (piso) | piso online | MATLAB | env_matlab | Mac | type=1 |
| smsemoa (piso) | piso online | MATLAB | env_matlab | Mac | |
| moead_media (piso) | piso offline | Python | **env_b5** | **VM Linux** | DESDEO mode 12 (D77) |

**Contagem:** MATLAB = 13 configs (1 env). Python = 8 configs (b5 roda como b5r+b5m) em 4 venvs: env_main(4) · env_e81_qpots(1) · env_b5(3) · env_c311(1).

## Viabilidade por plataforma (honesta)
| Ambiente | Mac arm64 | VM Linux x86 |
|---|---|---|
| env_matlab | ✅ (MATLAB é só Mac) | — |
| **env_main** | ✅ **provisionado 2026-07-15** (núcleo; falta stack R2) | ✅ a provisionar |
| env_e81_qpots | ⚠ verificar pins (torch 2.12/botorch 0.16.1) no provisionamento | ✅ a provisionar (M6) |
| env_b5 | ❌ **inviável** (sklearn 0.21.3 sem wheel arm64) | ✅ **destino natural** (M5) |
| env_c311 | ❌ **inviável** (numpy 1.20.2 sem wheel arm64) | ✅ **destino natural** (M5) |
| env_bridge | ✅ (`--enable-shared` 3.11.9; wire no R1-00) | — (a ponte é Mac/MATLAB) |
| env_c149_fallback | ⚠ condicional | ✅ condicional |

> **Por isso NÃO criamos todos os venvs no Mac agora.** O `env_main` é o único ao mesmo tempo **viável no Mac E necessário já** (F0-02/03). Os demais têm o `requirements/*.txt` **pronto** e são provisionados *just-in-time* no ambiente certo — b5/c311 **só existem na VM Linux** (os pins não têm wheel arm64). Os algoritmos Python **rodam na VM**; o Mac serve para desenvolvimento/piloto do que for viável.

## Estratégia de orquestração
1. **Despacho por subprocesso (D79):** o harness executa cada algoritmo chamando o `python` do **venv-alvo** por caminho completo; 1 run = 1 core; threads pinadas a 1 (`OMP/OPENBLAS/MKL/NUMEXPR=1`).
2. **Isolamento duro b5 × c311 (D79/N.1.2):** venvs separados, **nunca co-importar** (pins mutuamente exclusivos); overlay `desdeo_*` vendorizado *root-first* no `sys.path`.
3. **MATLAB:** isolamento por instalação + toolboxes + **árvore PlatEMO** (padrão 4.15 · e74 usa a 4.1 própria · e103 worker dedicado) + a ponte `env_bridge`.
4. **Provisionamento just-in-time:** ao chegar o milestone de um algoritmo, `pip install -r requirements/<env>.txt` no ambiente certo; registrar o `pip freeze` num `<venv>/requirements.lock` (D80).
5. **Reprodutibilidade:** os `requirements/*.txt` são o alvo; o `requirements.lock` de cada venv é a foto exata do que foi instalado.

## Comandos de provisionamento (por ambiente)
```bash
# padrão (Mac): escolher o Python do pyenv, criar o venv na pasta, instalar
pyenv shell <versão>
python -m venv /Users/gmello/Documents/python_venvs/<nome>
/Users/gmello/Documents/python_venvs/<nome>/bin/python -m pip install -U pip
/Users/gmello/Documents/python_venvs/<nome>/bin/python -m pip install -r requirements/<env>.txt
/Users/gmello/Documents/python_venvs/<nome>/bin/python -m pip freeze > /Users/gmello/Documents/python_venvs/<nome>/requirements.lock
```
- **env_main** → nome `mestrado_experimentos_dissertacao`, py 3.11.9 — **já feito** (núcleo).
- **env_bridge** → py 3.11.9 `--enable-shared` (o que o MATLAB embute) — provisionar no **R1-00**.
- **env_e81_qpots** → py 3.10/3.11 — provisionar no **M6** (verificar disponibilidade dos pins).
- **env_b5 / env_c311** → **na VM Linux** (M5), não no Mac.
