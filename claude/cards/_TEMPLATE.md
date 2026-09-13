# Cartão {ID} — {título curto}

- **Fase / rodada:** {F0 | R1 | R2 | R3 | SUB | R4}
- **Depende de:** {ID(s) que precisam estar ✅}
- **Bundle(s) a ler:** `claude_code_context/{...}` (+ `00_fundacao/01` e `03` se tocar pontos transversais)
- **Artefatos a consultar:** `artifacts/{runs_matrix.csv | envs.json | seeds.json | anchors.json | params.json}`

## Tarefa
{descrição objetiva do que implementar — patches (arquivo:linha), guardas, instrumentação, export}

## Teste de aceitação (o que torna o cartão VERDE)
**Automático (harness — bloqueia):**
- [ ] FE final = `31D−1` exato (avaliações reais distintas — D89)
- [ ] as 4 saídas válidas (3 parquets + `.jsonl` + timing + manifesto)
- [ ] CP-init / CP-bounds / CP-sinal passam
- [ ] guardas instaladas e logando
- [ ] `python scripts/accept.py {ID}` sai 0

**Validação de fidelidade (MANUAL, do autor, a posteriori — D97; NÃO bloqueia o harness):**
- [ ] leitura do `.jsonl` pelo checklist §17.5.1
- [ ] onde reproduzível: número-âncora do Anexo J (±3σ = faixa-guia, não limiar)

## Ao fechar
- Verde ⇒ escrever `handoff/{ID}.md` (feito, arquivos, resultado, pendências) e encerrar.
- Vermelho ⇒ **pára-e-loga** (D81): gravar diagnóstico, devolver ao autor. **Nunca** auto-consertar fidelidade.
