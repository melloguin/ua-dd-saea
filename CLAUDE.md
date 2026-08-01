# CLAUDE.md — porta de entrada do repositório `ua-dd-saea`

> **🚨 ESTADO (2026-08-01): T14 CONCLUÍDO — 11/11 itens, suíte 826/0 falhas.** Leia
> **`handoff/T14-FINAL.md`** (placar, os 4 pontos em que o dado desmentiu o cartão, e o que
> ainda precisa do AUTOR) + REGISTRO **PARTE A44**. T11/T12/T13 estão CONCLUÍDOS e validados
> (REGISTRO A36-A43). Regras de operação e armadilhas: `handoff/T11-PROMPT-SESSAO.md` §3-§4.
> **Antes da tag, 2 itens do autor:** a frota do `mapa_sementes.json` (5 máquinas com nomes
> PLACEHOLDER — `artifacts/frota.json` + `scripts/mapa_sementes.py`) e o B3 (aplicar o writer
> ⑥ atômico do MATLAB ou manter a exceção, hoje fechada com tripwire). Contexto geral:
> `MAPA_ARTEFATOS.md`.

> Este repositório executa o **pipeline experimental do mestrado** (survey + análise experimental
> de 16 algoritmos SA-MOEA). Toda a especificação, contexto e protocolo de implementação vivem
> na pasta **`claude_code_context/`**.

## Antes de qualquer sessão de implementação, leia (nesta ordem):
1. **`claude_code_context/CLAUDE.md`** — a porta de entrada real: regra de ouro do contexto,
   precedência, protocolo pára-e-loga, invariantes, mapa de leitura. **Siga-o à risca.**
2. O(s) arquivo(s) da fase indicada pelo `claude_code_context/PROMPT_MESTRE.md` (o manual do autor).

## Fonte da verdade
- **`claude_code_context/SPEC_experimentos_v5.2.md`** — referência completa (consulta pontual; nunca leitura integral).
- **`claude_code_context/artifacts/`** — dados machine-readable que você CONSOME (grid, envs, sementes, âncoras, decisões, params).
- Os **bundles** (`00_fundacao/`…`50_analise_R4/`) são GERADOS da SPEC por `gen_bundles.py` — nunca editados à mão.

## Regras firmes (do autor)
- **Validação de fidelidade = MANUAL do autor, a posteriori (D97)** — não é código; o harness só instrumenta (log `.jsonl`) e aplica o gate objetivo (FE/saídas/CP-init/guardas).
- **1 sessão = 1 cartão** (`cards/INDEX.md`); ao terminar, escreva `handoff/{CARTAO}.md`.
- Ambiguidade/conflito ⇒ **PARE e pergunte** (protocolo D81) — nunca escolha fidelidade sozinho.
