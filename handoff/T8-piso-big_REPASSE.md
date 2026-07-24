# T8 — piso-big (`treed_media`) · REPASSE À TORRE (definições em aberto)

O runner passa TODOS os gates, INCLUSIVE o portão (VERDE após os fixes #1/#2, que o
AUTOR AUTORIZOU o T8 a aplicar em sessão). Os itens #1/#2 abaixo estão **RESOLVIDOS**;
#3/#4/#5 são notas p/ ciência/confirmação da torre.

---

## #1 ✅ RESOLVIDO (autorizado pelo autor) — `scripts/auditar.py:43` agora inclui `treed_media`
`OFFLINE = {"e103","b5r","b5m","c311","moead_media"}` — **falta `"treed_media"`**. Como o
`portao.py` (linha 78) chama `auditar.py … --exp … ` **SEM `--regime`**, e o auditar decide
`offline = (regime=="offline") or alg in OFFLINE` (auditar.py:53), o run OFFLINE de
`treed_media` é auto-classificado como **ONLINE**. Consequências (medidas):
- pula o binding DI-34 por hash do tier (auditar.py:64);
- pula a checagem da ⑦ (auditar.py:197);
- confere a sonda contra `S_ONLINE=2000` (não 20000) e reprova `geracao NULL` ⇒
  2 achados falsos: `③ bloco @2000: ORDEM ≠ artefato` e `③ sonda ONLINE com geracao NULL`.

**Prova:** `auditar treed_media ZDT4 42 --exp sweep-big-lhs` → 2 achados (VERMELHO);
o MESMO com `--regime offline` → **VERDE**. O portão herda o vermelho.

**Correção APLICADA (1 linha, autorizada):** `"treed_media"` adicionado ao set `OFFLINE`
de `scripts/auditar.py:43` (paralelo a `sh.OFFLINE_CONFIGS` e `manifest.OFFLINE_ALGS`, que
JÁ o incluíam). Resultado: `auditar` (sem `--regime`) → **VERDE**; `portao` lhs/ZDT4/42 e
mvns/ZDT4/42 → **VERDE** (0 vermelhos). O teste `test_registros_offline` voltou a asserir
`self.assertIn("treed_media", A.OFFLINE)`.
> ⚠ O cartão dizia "a torre já fiou … portão/guards"; a fiação de `auditar.OFFLINE` tinha
> ficado incompleta. Ciência à torre: o fix é idêntico ao dos outros 5 offline configs.

---

## #2 ✅ RESOLVIDO (autorizado pelo autor) — `experiments.py:57` `_OFFLINE` agora inclui `treed_media`
Antes: `treed_media ∈ KNOWN_ALGORITHMS` mas ∉ `_OFFLINE` ⇒ caía em `DEFAULT_ALGORITHMS`
(= KNOWN − _OFFLINE), e um `experiments.py` SEM `--algorithms` (batch `main` default)
tentaria rodá-lo no exp `main` (sem dataset treed_media) ⇒ falharia. `"treed_media"`
adicionado a `_OFFLINE` (paralelo aos outros 5 offline). Agora só roda com
`--exp sweep-big-{lhs,mvns} --algorithms treed_media` explícito. Ciência à torre.

---

## #3 🟢 COSMÉTICO — `artifacts/envs.json:165-167` `env_c311.algs` ainda é `["c311"]`
Não lista `treed_media`. O roteamento é AUTORITATIVO via `alg_to_env.treed_media`
(que JÁ diz `env_c311`); a lista `algs` é descritiva. Anexar `"treed_media"` por consistência
(opcional). Arquivo da torre.

---

## #4 ⚙ CONFIRMAR — política da ⑦ no teto (`teto_wall`)
Segui o **rito do piso/b5** (DI-35.5): ao estourar o teto durante o RVEA final,
`status=failed`, `motivo=teto_wall`, curva parcial preservada, e a **⑦ SAI da última pop
RVEA** (que é válida — no treed_media o teto só pode ocorrer na fase FINAL, onde a
população é sempre completa). **O c311 DIFERE:** no c311 o teto pode cair na CONSTRUÇÃO,
onde não há pop final válida, e a ⑦ é OMITIDA (`_TetoWall`). Como aqui não há construção,
o rito do piso (⑦ parcial) é o análogo direto e coerente com "curva parcial preservada".
**Confirmar com o autor** se prefere o rito-c311 (⑦ OMITIDA no teto). Declarado em
`_sigma_dict["teto"]`. Não exercitado pelos gates (teto=12h ≫ ~10s de wall).

---

## #5 ℹ NÃO-PERTURBAÇÃO clássica (baseline) — N/A p/ config novo
`scripts/naoperturbacao.py` compara contra um baseline congelado
(`data/experiments/_baseline_pre_retrofit/`) que NÃO existe p/ `treed_media` (config novo
pós-congelamento) — retorna `[--] sem baseline` (RUNBOOK §6-bis item 5: N/A, não bloqueia).
A não-perturbação foi provada pelo `test_sonda_NAO_perturba_a_busca` (sonda on/off ⇒
⑦+③-busca idênticas). Determinismo bit-a-bit: mesma-máquina (D79); provado por
`test_determinismo_bit_a_bit`.

---

## Estado do fechamento
- Código/testes/dispatch: **prontos**; **TODOS os 4 gates VERDES** (inclusive o portão,
  após #1/#2 autorizados pelo autor).
- Pendências da torre: apenas #3 (cosmético envs.json) e #4 (confirmar política ⑦ no teto).
- Commits `[T8-piso-big]` aplicados (código/testes ≠ handoffs), SEM push, SEM `add -A`,
  staged conferido vazio antes de cada `git add` (coexistência T9).
