# START_HERE — ponto de partida da implementação (pós-preparação, 2026-07-15)

> Este arquivo é o handoff da fase de **preparação** (auditoria → SPEC v5.2 → correções mecânicas → higiene)
> para a fase de **implementação**. Leia-o uma vez; depois cada sessão de implementação segue o `PROMPT_MESTRE`.

## Onde tudo está
- **Fonte da verdade:** `claude_code_context/SPEC_experimentos_v5.2.md` (consulta pontual; nunca leitura integral).
- **Porta de entrada do agente:** `claude_code_context/CLAUDE.md` (regra de ouro, precedência, invariantes).
- **Manual do autor (como abrir cada sessão):** `claude_code_context/PROMPT_MESTRE.md`.
- **Bundles cirúrgicos:** `claude_code_context/{00_fundacao..50_analise_R4}/` — GERADOS da SPEC por `gen_bundles.py`.
- **Artefatos machine-readable:** `claude_code_context/artifacts/` (runs_matrix, envs, seeds, anchors, decisions, params, characteristics, repos.lock).
- **Lista de cartões-sessão:** `cards/INDEX.md` (25 cartões, F0→R4, com depende-de/bundle/status).
- **Runner de aceitação objetiva:** `scripts/accept.py` (só encanamento — D97). **Pré-voo:** `scripts/preflight.py`.
- **Diagnóstico completo da auditoria:** `~/Downloads/DIAGNOSTICO_AUDITORIA_SPEC_v5.1.md` (85 achados verificados).

## O que JÁ está pronto
- SPEC v5.2 com as 14 decisões do ping-pong (D87–D100) tecidas + reparo D97 (validação de fidelidade = manual do autor).
- 8 artefatos corrigidos (run_id do sweep sem duplicatas; envs b5/c311 separados; anchors com 20 patches; etc.).
- Repo git-limpo: e103 versionado como arquivos planos; claude_code_context/ instalado; scaffolding.
- Os 16 algoritmos + pisos: código presente e viável no repo (`code_ok` na auditoria).

## O que FALTA — dono e ordem
### Você (autor) — pré-requisitos que só você faz
1. **Infra GCP:** projeto + VMs Vertex AI + bucket `mestrado_experiments` + IAM (papel de escrita da service account).
2. **MATLAB R2025a:** confirmar ativações de licença (o teto real pode ser licença, não nº de VMs — §21.3).
3. **Rodar `python scripts/preflight.py --write`** e resolver as ~9 pendências de âncora (refinar `expect_before` exatos + resolver paths glob no `anchors.json`).
4. Nos gates: pin do `desdeo-emo` (R3.2), wheel do sklearn do b5.
5. Backups (manual, à medida que os resultados saem — D64/D100).
6. O **aval de fidelidade** em cada piloto (é seu — D97) e o "go" de cada gate.

### Claude (sessões frescas, 1 cartão por vez) — o código
Ordem (D84 / §22), **pattern-setter primeiro, depois fan-out**:
```
Fase 0 (harness compartilhado)  →  gate F0
   ├─ R1 MATLAB:  R1-00-harness → R1-c217 (CASO-MODELO, validar ponta-a-ponta) → fan-out (b1,b3,b4,e7,c141,e74,c238,e103,pisos)
   ∥ R2 BoTorch:  R2-00-harness → R2-c262 (pattern-setter) → c154
   → R3 standalone (um-por-um): c122 → b5 → c311 → c149 → e81 → piso offline
   → sub-estudos (batch, sweep, varredura N)  →  R4 análise (autor refina)
```
Execução em PARALELO por stack: ao fechar o gate de uma rodada, a bateria dela roda (semanas, desassistida) enquanto as outras são implementadas / o survey é escrito.

## Como começar a PRIMEIRA sessão de implementação
Abra uma **instância NOVA** do Claude Code neste repo e cole o prompt do `PROMPT_MESTRE.md` preenchido para o cartão **F0-01-harness** (arquivos da fase = os 5 de `00_fundacao/`). O gate objetivo de cada cartão = `python scripts/accept.py {CARTAO}` verde; a fidelidade é seu aval manual no piloto.

## O gate mais importante
**R1-c217 ponta-a-ponta** (harness + adapter + export + DoE + métrica + piloto). Se fecha verde, o pipeline está provado e o resto é multiplicação. Concentre energia aí.

## Princípios inegociáveis (do autor)
- Validação de fidelidade = **manual, sua, a posteriori** (D97). O harness só instrumenta + aplica o gate objetivo.
- **1 sessão = 1 cartão**; ao fechar, escreva `handoff/{CARTAO}.md`. Ambiguidade ⇒ **pare e pergunte** (D81).
- **Nunca** auto-consertar fidelidade; nunca decidir sozinho o que a SPEC não fixa.
