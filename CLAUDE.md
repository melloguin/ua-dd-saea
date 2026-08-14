# CLAUDE.md — porta de entrada do repositório `ua-dd-saea`

> **🚨 ESTADO (2026-08-14): ONDA T15 CONCLUÍDA — 3 problemas de DADOS REAIS integrados.**
> RE21=25 · DDMOP7=26 · ESTOQUE40=27 no catálogo; grid **22.740** células (runs_matrix
> ×14 col); 21 configs × 30 sementes = 1.890 células novas (SEM q10/sweep/c311 —
> D102.16). DDMOP7 é caixa-preta MATLAB (D102.5): 3 rotas de avaliação, sem sonda
> (D102.10), sem front D72 (D102.4), ⑦ offline PÓS-HOC via final_eval (D102.9).
> Portas de entrada: **REGISTRO PARTE A49** (a integração inteira) ·
> **handoff/C5-DOSSIE-FIDELIDADE-T15.md** (veredito D97 do autor, pendente) ·
> laudos D0 em handoff/ (falhas da main + c238 resolvido).
> **Frota de execução ATUAL: vm1 + vm5 SOMENTE** (decisão do autor 14/08;
> `artifacts/frota.json`). Tag `m8-freeze` = a 1ª rodada (25 problemas); a tag do
> T15 sai após o veredito C5. Provisionamento DDMOP7 nas VMs: batelada própria em
> handoff/PROVISIONAR-VM-DO-ZERO.md (engine nos 2 venvs, clone do .p pinado,
> Processo A ANTES do disparo offline).
>
> ⚠ Handoffs de frota anteriores a 14/08 descrevem frotas mortas (4-6 máquinas) —
> vale o frota.json.

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
