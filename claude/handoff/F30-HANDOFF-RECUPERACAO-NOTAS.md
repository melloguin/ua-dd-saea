# HANDOFF — plano de recuperação pós-validação das 30 sementes

**De:** torre de validação de fidelidade · **Para:** torre central de implementação
**Data:** 2026-08-15 · **Autorizado pelo autor** (chat de 15/08: "sim, por favor propague o handoff")
**Contexto:** a validação F30 fechou — 15.129 células, 22 configs, média de confiança **86%**.
**Nenhum experimento está errado; zero bugs de mecanismo em 3 auditorias.** As notas <80%
(c154 64,5% · e103 72,3% · c238 76,6% · e7 78,9%) são **cobertura e custódia**, não infidelidade.
Este handoff lista as ações que recuperam as notas, em ordem de custo-benefício, com o ganho
estimado de cada uma.

**Leitura prévia:** `f5/f30/RELATORIO_FINAL_F30.md` (o consolidado) · `f5/f30/notas_fidelidade_alg_x_problema.csv`
(a régua: `nota = mecanismo × cobertura × custódia`) · `f5/f30/configs/*.json` (evidência por config).

---

## BLOCO A — ações baratas, SEM re-run (autorizadas; executar já)

### A1 · Gerar a ⑦ do e103 — a maior alavanca do lote

- **O quê:** a camada ⑦ (endpoint oficial do regime offline) está **ausente em 669/669** células
  do e103, enquanto b5m (679/679), b5r (725/725) e moead_media (725/725) estão em 100%. A ⑦ é
  **pós-hoc**: computa-se das camadas existentes, sem re-rodar experimento.
- **Como:** `$PY scripts/final_eval.py --alg e103 --all-seeds` — o script já aceita e103 e já tem
  o dedup DI-41 (verificado pelo agente F30 do e103; ver `f5/f30/configs/e103.json`).
- **Cuidados:** rodar sobre o canônico `resultados_experimentos/`; NÃO tocar `data/experiments`;
  conferir 2-3 células contra a semântica B7.5 (`origem_geracao` → última geração da busca)
  antes de disparar o lote todo.
- **Ganho:** e103 72,3% → **~80,3%** (custódia 0,90 → 1,0).
- **Custo:** horas de CPU. Zero experimento.

### A2 · Censo do bucket — as ~580 células com `upload_status: 403`

- **O quê:** c122 (220/738), c149 (210/717) e c154 (149) têm ⑤ com
  `upload_status = {erro: upload_failed 403 — storage.objects.delete}`, todas de vm2/vm4/vm10.
  Sob D54 a ③ delas deveria estar no bucket. O 403 é de `objects.delete`, o que **sugere** objeto
  pré-existente (o upload teria sido barrado ao tentar sobrescrever) — mas ninguém conferiu.
- **Como:**
  ```
  gsutil ls -l gs://mestrado_experiments/experiments/main/c122/*__surrogate.parquet
  gsutil ls -l gs://mestrado_experiments/experiments/main/c149/*__surrogate.parquet
  gsutil ls -l gs://mestrado_experiments/experiments/main/c154/*__surrogate.parquet
  ```
  Cruzar com as listas das células afetadas (em `f5/f30/configs/{c122,c149,c154}.json`, achados
  G1/C3-1/C2). ⚠ Bucket é read-only para nós: NUNCA `rsync --delete`, `rm` ou `mv`.
- **Ganho:** se os objetos existirem, custódia c122/c149 0,96 → ~0,99 e c154 0,94 → ~0,96 ⇒
  c122 85,5→~88 · c149 84,1→~87 · c154 64,5→~66. **Global 86% → ~88%.**
- **Custo:** minutos.

### A3 · Reparos de célula única (2 células, espelhos íntegros existem)

1. **b1/BBOB_F17/semente 8 — célula QUIMERA**: no canônico, ⑥①②③④ são de uma execução
   (mtime 09/08) e o ⑤ é de outra. O espelho `matlab-vm5` tem as 6 camadas coerentes de 14/08.
   **Repor a célula inteira a partir do espelho** (as duas opções estão no achado B1-30-C3-01
   de `f5/f30/configs/b1.json`; o autor autorizou a rota do espelho ao aprovar este handoff).
2. **c141/ZDT4/semente 9 — ⑥ órfão truncado** (368 bytes, só o header): copiar
   `~/mestrado_coleta_m8/matlab-vm5/experiments/main/c141/exp_main_c141_ZDT4_9.jsonl`
   sobre o canônico e re-rodar o recenso da célula.
- **Regras:** `cp` explícito (nunca `mv`), conferir sha256 antes/depois, registrar a troca num
  `REPAROS_F30.md` ao lado das células. O dado antigo vai para `_quarentena/`, não se apaga.
- **Ganho:** remove 2 dos 11 achados ALTA.
- **Custo:** minutos.

---

## BLOCO B — a onda de completude (já planejada; itens 16/17 da mesa do autor)

### B1 · As 430 não-rodadas (inclui as 86 do e7)

- Os grids **já existem**: `~/mestrado_coleta_m8/_analise/grid2_vm{1,5}.txt`. As VMs vm1+vm5
  estão ligadas (frota oficial, `artifacts/frota.json`).
- e7 79→**~89%** · cobertura global 94,7→~97% · **global ~89-90%**.
- ⚠ A vm5 mudou de shape em 14/08 e **os configs surrogate divergem 100% cross-shape** (F30 §3).
  **Recomendação: rodar a onda inteira na vm1** (shape estável) ou fixar a decisão de
  estratificação ANTES do disparo — senão a onda nova amplia a exposição de hardware.

### B2 · c238: o fix de 1 token + re-run das ~105 células — DECISÃO DO AUTOR, recomendada

- **A causa está provada** (laudo D0, commit `b7454ef`): bug latente **UPSTREAM** do PlatEMO
  vendorizado — `Infill_EIM.m:25`, `min(reshape(...))` colapsa com front singleton; separação
  **28/28 vs 0/617** por `n_front1==1`. Fix mínimo: `,[],1`. Pela bússola D29 é **🔴 bug →
  corrige para o artigo**.
- O `m8-freeze` vetava fixes **durante** a campanha; a campanha acabou. Para publicação de ponta,
  a recomendação da torre de fidelidade é **aplicar + re-rodar as ~105 células ausentes/failed**
  (BBOB_F1/F5/F22/F55 + ZDT6), declarando o bug upstream como achado (reportável ao PlatEMO).
- Se o autor preferir NÃO aplicar: publicar com a incapacidade declarada em tabela de taxa de
  sucesso também é honesto — mas deixa 4 problemas BBOB mancos num config saudável nos outros 21.
- **Ganho com o fix:** c238 76,6→**~89%**.
- ⚠ Depois do fix, rodar o controle: o teste que REPROVA na versão atual e passa na corrigida
  (regra da casa desde a T11 — todo gate novo nasce com controle negativo).

### B3 · (Opcional) As 404 células da vm5 pós-corte

- 404/11.618 células `main+ok` (3,48%) saíram da vm5 **após** 2026-08-14T10:26:42Z (troca de
  shape). Nos 6 configs surrogate expostos, a divergência cross-shape é 100% (c141 11/11,
  e74 10/10, b1 8/8, b3 4/4, c238 4/4, e7 2/2).
- No nível de contraste o custo é pequeno (p95 = 1,2% HV) ⇒ **declarar a estratificação basta**
  para a maioria das venues. Re-rodar as 404 na vm1 só se o alvo tiver artifact evaluation
  rigorosa. A lista das 404 sai de `_FONTES.csv` × corte temporal (script no achado C3-B de
  `f5/f30/configs/c141.json`).

---

## BLOCO C — o que NÃO re-rodar (vetado pela análise; poupar o dinheiro)

1. **As 300 ⚪ do c154 com teto maior.** Projeção medida: ~13,4h para fechar uma célula D=12 —
   dobraria o custo nas células mais caras. A curva parcial é utilizável; a análise por
   **orçamento de FE comum** (O-21) resolve. O confundimento máquina≡semente se neutraliza na
   análise, não no re-run.
2. **As incapacidades documentadas** (b1×DTLZ4 0/30 · c262×WFG1 2/30 · c154×{ZDT6,WFG1,BBOB_F5/
   F22/F49/F55}). Determinísticas, com laudo. Entram como tabela de taxa de sucesso — resultado,
   não falha.

---

## BLOCO D — os 3 bloqueadores de PUBLICAÇÃO (nenhum é re-run; todos são decisão/protocolo)

| # | bloqueador | ação | dono |
|---|---|---|---|
| D1 | **A dupla semente 42 do c122**: a s42 da M8 diverge integralmente da que a F5/T11 auditaram (0/25 células com IGD idêntico, razões 0,57×–1,75×) | cravar **qual corpus é canônico** e se os números da F5/T11 são re-emitidos sobre o novo | **autor** |
| D2 | Comparações com as ⚪ exigem **orçamento de FE comum** | escrever a regra no protocolo de análise da R4 (a O-21 já a prescreve; falta formalizar) | torre |
| D3 | **O piso O-18 está morto**: 65× otimista para HV no nível de célula, pessimista para IGD+, e não distingue hardware nem classe de config | substituir pelo **piso empírico de dois níveis** (célula: HV p95 10,60% / IGD+ 28,50% · contraste: 1,225% / 3,238%) — `f5/f30/transversal_ruido.md` | autor ratifica, torre registra |

---

## Projeção das notas

| etapa | global | o que muda |
|---|---|---|
| hoje | **86,0%** | — |
| + Bloco A (barato, sem re-run) | **~88%** | e103 ⑦ · censo do bucket · 2 reparos |
| + B1 (onda das 430) | **~89-90%** | e7 e caudas de cobertura |
| + B2 (fix c238 + 105 células) | **~92-93%** | c238 |

**A fidelidade em si já está provada** (mecanismo 92,1%, query-joias 100% em ~15 mil células).
Este plano recupera **confiança**, não fidelidade — e três quartos dele não rodam um único
experimento novo.

---

*Evidência completa: `f5/f30/` (relatório, 21 JSONs de config, 4 transversais, censos, notas).
Dúvidas de leitura: as regras O-21 estão reproduzidas no prompt da validação e no §1 do
relatório. D97: cada "recomendo" deste documento é recomendação — o veredito é do autor.*
