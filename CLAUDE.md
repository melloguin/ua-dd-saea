# CLAUDE.md — porta de entrada do repositório `ua-dd-saea`

> **🚨 CAMPANHA ATUAL: PROVISIONAMENTO DA FROTA PARA O M8.** Porta de entrada:
> **`handoff/PROVISIONAMENTO-M8-FROTA.md`** — comece pela **§0.2**, que traduz a
> nomenclatura: a máquina que TODO documento anterior chama de `vm1` é hoje a
> **`vm2`**, e existe uma **`vm1` NOVA** (criada 2026-08-01) que não tem nada
> provisionado. A frota vigente é `claude_code_context/artifacts/frota.json`
> (4 máquinas: vm1, vm2, vm10, vm3 — o Mac e as v5/v6 estão FORA do grid).
> Ordem de execução do M8: **`LOTE_ORDEM=semente`** (semente-major, barato→caro).
>
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
