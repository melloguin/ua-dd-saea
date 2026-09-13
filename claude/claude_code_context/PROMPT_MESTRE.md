# PROMPT_MESTRE — como iniciar cada sessão do Claude Code (SPEC v5.2)

> **Para o AUTOR (Guilherme).** Este arquivo não é lido pelo agente — é o seu manual de operação. Cada sessão do Claude Code recebe **um prompt curto** montado do template abaixo. A regra: **1 sessão = 1 cartão** (D83). Nunca cole a SPEC inteira no prompt; o agente lê os arquivos indicados com as próprias ferramentas (Read), na ordem que o CLAUDE.md manda.

---

## O template (copie, preencha os `{…}`, cole no Claude Code)

```text
Você é o implementador do pipeline experimental do meu mestrado (survey + análise
experimental de 16 algoritmos SA-MOEA). O repositório é o `ua-dd-saea` e todo o
contexto está na pasta `claude_code_context/`.

PASSO 0 — CONTEXTO (nesta ordem, e SOMENTE isto):
1. Leia `claude_code_context/CLAUDE.md` INTEIRO — ele define precedência, protocolo
   de falha ("pára-e-loga"), invariantes e o mapa de leitura. Siga-o à risca.
2. Leia {ARQUIVOS_DA_FASE}.
3. Consulte `claude_code_context/artifacts/` quando precisar de DADOS (grid de runs,
   envs, âncoras, decisões) — use os CSV/JSON, não parseie a SPEC.
4. NÃO leia os arquivos de outros algoritmos/rodadas nem a SPEC completa. Se uma
   seção específica da SPEC for citada e você precisar dela, leia SÓ aquela seção
   (busque o header). Se algo estiver ambíguo ou em conflito, PARE e me pergunte —
   não escolha sozinho (protocolo D81).

PASSO 1 — PLANO: antes de escrever código, me apresente em ≤15 linhas: o que vai
fazer, em que arquivos, e qual é o teste de aceitação do cartão. Aguarde meu OK.

PASSO 2 — EXECUÇÃO: implemente. Commits pequenos e frequentes com mensagem
`[{CARTAO}] descrição`. Cada guarda/patch de fidelidade referencia a decisão
(ex.: "D76: máscara e74") em comentário no código.

PASSO 3 — ACEITAÇÃO: rode o teste de aceitação do cartão. Se VERDE: escreva
`handoff/{CARTAO}.md` (o que foi feito, arquivos tocados, resultado do teste,
pendências) e encerre. Se VERMELHO: pare, grave o diagnóstico, me devolva o
controle (NUNCA "conserte" fidelidade por conta própria).

TAREFA DESTA SESSÃO ({CARTAO}):
{DESCRICAO_DA_TAREFA}

Teste de aceitação: {ACEITACAO}
```

---

## Como preencher `{ARQUIVOS_DA_FASE}` (o mapa por fase)

| Fase / sessão | `{ARQUIVOS_DA_FASE}` |
|---|---|
| **Fase 0** (andaime: DoE, wrapper FE, export, esteira, despachante) | os 5 arquivos de `00_fundacao/`, em ordem (01→05) |
| **R1 — algoritmo MATLAB X** (ex.: c217) | `00_fundacao/01` e `03` (se 1ª sessão da rodada: também `10_rodada1_matlab/00_contrato_rodada1.md`) + `10_rodada1_matlab/alg_c217_pcsaea.md` |
| **R1 — pisos online** | `10_rodada1_matlab/00_contrato_rodada1.md` + `10_rodada1_matlab/alg_pisos_online.md` |
| **R2 — c262 / c154** | `20_rodada2_botorch/00_contrato_rodada2.md` + o `alg_*.md` do algoritmo |
| **R3 — c122 / b5 / c311 / c149 / e81 / piso offline** | `30_rodada3_standalone/00_contrato_rodada3.md` + o `alg_*.md` |
| **Sub-estudos** (batch / sweep / varredura N) | o `.md` correspondente em `40_subestudos/` |
| **R4 — análise** | `50_analise_R4/metricas_estatistica_caracteristicas.md` + `artifacts/characteristics.csv` |

> Nas sessões 2+ de uma mesma rodada, o contrato da rodada já foi absorvido — mas como cada sessão é NOVA (contexto zerado), inclua o contrato sempre que a sessão tocar pontos transversais (ponte, export, watchdog). Custo baixo, engano zero.

---

## Exemplo 1 — pronto para colar (Fase 0, primeira sessão)

```text
Você é o implementador do pipeline experimental do meu mestrado (survey + análise
experimental de 16 algoritmos SA-MOEA). O repositório é o `ua-dd-saea` e todo o
contexto está na pasta `claude_code_context/`.

PASSO 0 — CONTEXTO (nesta ordem, e SOMENTE isto):
1. Leia `claude_code_context/CLAUDE.md` INTEIRO.
2. Leia os 5 arquivos de `claude_code_context/00_fundacao/`, em ordem (01→05).
3. Consulte `claude_code_context/artifacts/` quando precisar de dados.
4. NÃO leia bundles de rodadas/algoritmos nem a SPEC completa. Dúvida/conflito ⇒
   PARE e pergunte (D81).

PASSO 1 — PLANO: ≤15 linhas + teste de aceitação; aguarde meu OK.
PASSO 2 — EXECUÇÃO: commits pequenos `[F0] …`; patches referenciam a decisão.
PASSO 3 — ACEITAÇÃO: verde ⇒ `handoff/F0-doe.md`; vermelho ⇒ pára-e-loga.

TAREFA DESTA SESSÃO (F0-doe):
Implementar `src/doe.py` (D63): gerar, para cada (problema, semente) dos 25×30,
a matriz X (11D−1 × D) em bounds nativos via
np.random.Generator(PCG64(SeedSequence(semente))) [LHS], e persistir 1 arquivo
`.npy` float64 little-endian row-major em `data/doe/{problema}/doe_{problema}_{semente}.npy`,
com sha256 registrado. Incluir o leitor MATLAB do `.npy` (função `load_doe.m`).

Teste de aceitação: para uma amostra de 5 (problema, semente), o X carregado no
MATLAB é bit-a-bit idêntico ao gravado pelo Python (sha256 igual dos dois lados);
shape e bounds conferem para os 25 problemas.
```

## Exemplo 2 — pronto para colar (R1, c217, o caso-modelo)

```text
[... PASSO 0 com:
2. Leia `claude_code_context/00_fundacao/01_regras_globais.md`,
   `claude_code_context/00_fundacao/03_contrato_export.md`,
   `claude_code_context/10_rodada1_matlab/00_contrato_rodada1.md` e
   `claude_code_context/10_rodada1_matlab/alg_c217_pcsaea.md`.
... PASSOS 1–3 idênticos ao template, com {CARTAO} = R1-c217]

TAREFA DESTA SESSÃO (R1-c217):
Integrar o c217 PC-SAEA conforme o alg_c217_pcsaea.md: patch das 2 guardas
(SAS:21/:39 — D17), N=50, fix PCS:55, clip do lote ao saldo, DoE injetado do
artefato (D63), rng DEPOIS do Problem (D59), hook outputFcn com as camadas
②/③ + timing, log .txt por geração (§17.2.1), export brotli/float32 sem
arredondamento (D53), escrita atômica (D58).

Teste de aceitação: run completo MMF1 e ZDT1 seed 0 com FE final = 31D−1 exato;
DTLZ2 m=3 d=15 → IGD dentro de ±3σ (=±2,335e-2) de 6,9212e-2 (D81); .jsonl passa
o checklist §17.5.1; 4 saídas válidas.
```

---

## As 3 regras de operação que evitam 90% dos problemas

1. **1 sessão = 1 cartão.** Sessão que "aproveita para fazer mais um" é onde o contexto contamina. A sessão seguinte começa lendo o `handoff/` da anterior.
2. **O agente nunca decide fidelidade.** Se ele propuser "corrigir" algo fora do cartão, a resposta é: registrar em `handoff/` e me trazer — vira decisão D-numerada se for o caso.
3. **Regenere os bundles após editar a SPEC** (`python3 gen_bundles.py`) — a SPEC é a única fonte da verdade; bundle editado à mão é dessincronização plantada (a lição nº 1 do red-team).
