# R3-piso-off — REPASSE À TORRE / AO AUTOR (validação ao vivo + definições em aberto)

Sessão 2026-07-23 · `moead_media` (mode 12), OFFLINE, `env_b5` · **FASE A**.
Runner `src/piso_offline.py` (molde direto `src/b5_prob.py`). Gates da Fase A:
**todos VERDES** (ver RELATORIO). Abaixo: o que validei ao vivo e **cada definição
que deixei em aberto para o autor ratificar** (D81 — não escolhi fidelidade sozinho).

---

## A. Validado AO VIVO nesta sessão
1. **env_b5 RODA o desdeo mode-12** (não só importa): `MOEA_D` de
   `desdeo_emo.EAs.ProbMOEAD`, root-first, `SurrogateKriging`, sonda offline 20000,
   filtro ND pymoo+shim. `load_offline_budget` roda **sem o shim pyarrow do b5**.
2. **Ablação cirúrgica confirmada:** `n_ger`/`n_final` do piso == b5m em 3/3
   (50/105/50) ⇒ mesma geometria (lattice, FE); só a seleção difere (o
   `n_nd_pos_real` diverge: 8/53/29). É EXATAMENTE o que a DEF-E3 mede.
3. **σ NULL** ponta-a-ponta: a ③ (busca E sonda) sai com `sigma_* = NULL`, μ
   preenchido — auditar e final_eval VERDES, e o teste assere σ all-NULL.
4. **Determinismo e não-perturbação** bit-a-bit (⑦ + ③-busca), NaN-aware.
5. **⑦ reconstituível da ③** (DI-16.16): `final_eval --check` confirma "X
   reconstituível da ③ ger N via origem_linha" nos 3.

---

## B. DEFINIÇÕES EM ABERTO — pedem ratificação do autor

> ### ⚠⚠ TORRE CENTRAL: LEVANTAR COM O AUTOR ⚠⚠
> **B2 e B3 são DECISÕES do autor ainda em aberto** (não são falhas de gate — o
> cartão fecha VERDE com os defaults consistentes-com-b5 que adotei). A torre
> central DEVE apresentá-las ao autor para decisão. **B7** pede ciência (1 teste
> COMPARTILHADO alterado). B1/B8 resolvidos; B4/B5/B6 informativos.

### B1. ✅ RESOLVIDO (torre, 2026-07-23) — σ do piso = **NULL**, definitivo
> **A torre confirmou:** a resolução por PRECEDÊNCIA está correta e é DEFINITIVA
> (DI-16.1 + CONTRATO §3.2 governam; a frase "σ = desvio do GPR" era ruído de
> herança do molde b5). Registrado como "contradição do prompt resolvida por
> precedência, confirmada pela torre". Sem re-trabalho. (Detalhe abaixo, p/ registro.)
- **Conflito interno do cartão.** A epígrafe (i) e a linha OUTPUTS do MEU cartão
  dizem *"③ … σ = desvio do GPR — NUNCA variância"*. Isso é **cópia literal** do
  `sigma_dict` do b5 (`b5_prob.py:189`) e **contradiz** a decisão que o próprio
  cartão cita:
  - **DI-16.1** (REGISTRO:637): *"`sigma_*` **NULL**"*.
  - **CONTRATO §3.2:637/191**: piso offline = *"mu_* preenchido; **sigma_* NULL**"*.
  - o **gate 4 do próprio cartão**: *"comparação NaN-aware **se houver σ=NaN**"* —
    antecipa σ=NaN na ③-busca.
- **O que fiz:** σ **NULL** (5 fontes × 1 frase-resíduo). O piso é "b5 sem σ": a
  incerteza NÃO é reportada nem na busca nem na sonda. O `problem.evaluate` ainda
  CALCULA `.uncertainity` (o motor a arquiva), mas o runner a DESCARTA.
- **Peço ratificar:** σ NULL é o correto? (Estou confiante; sinalizo só porque é
  contradição textual do cartão.) Se o autor quiser σ = desvio do GPR (para
  comparar calibração piso×b5 na MESMA régua), a mudança é 1 linha (`_predict`
  devolve `(mu, sg)` e as linhas de busca lêem `uncertainty_archive`) — mas isso
  DESFAZ o "b5 sem σ" da DI-16.1.

### B2. 🟠 `modelo_hp`: **NULL** (implementado) × "grava modelo_hp" (DI-16.1)
- A **DI-16.1** diz que o piso *"grava `tempo_fit_s` REAL + `modelo_hp`"*. O molde
  b5 e o **D-08** gravam `modelo_hp = NULL` no offline ("HP fixos, treino único").
- **O que fiz:** `modelo_hp = NULL` (idem b5, o meu par de ablação — gravar HP no
  piso mas não no b5m introduziria uma diferença espúria; a ablação quer SÓ a
  seleção diferente). Declarado no `sigma_dict` com a ressalva.
- **Leitura:** a DI-16.1 contrasta o piso-OFFLINE (tem modelo ⇒ o conceito
  `modelo_hp` se aplica) com os pisos-ONLINE (sem modelo). O **valor** segue NULL
  por HP fixos (D-08). **Ratificar?**

### B3. 🟡 `⑥`/HEADER: enriquecimento "piso" da CONTRATO §6.1 NÃO adicionado
- A CONTRATO §6.1 (linha "pisos (5)") pede, além do mínimo comum: *"ideal/nadir da
  pop por geração; os VETORES de decomposição do moead no HEADER (determinísticos —
  1×)"*. O `moead_media` é ao mesmo tempo "um piso" E "um config surrogate da
  família b5". A **linha "b5" da §6.1** pede outra coisa (pesos no header +
  p_wrong).
- **O que fiz:** segui o molde b5 (config surrogate) — `⑥` = `minimo_comum_di10`
  (`fe`, `f_best[]`, `n_front1`); SEM ideal/nadir por geração, SEM vetores de
  decomposição no header. É read-only/opt-in (não gated; auditar não checa).
- **Peço decisão:** o piso-off deve seguir a linha **"pisos"** (add ideal/nadir por
  geração + `UniformPoint(N,M)` no header) ou a linha **"b5"** (config surrogate,
  como está)? Se "pisos", adiciono na Fase B (é read-only, não perturba).

### B4. 🟢 Shim pyarrow do b5 OMITIDO (informativo)
- O `_patch_doe_pyarrow_compat` do b5 NÃO está no runner: `doe.py` já é
  pyarrow-12-safe (DI-26, `combine_chunks().to_numpy`), provado ao vivo
  (`load_offline_budget` roda limpo). Menos monkey-patch num módulo COMPARTILHADO.

### B5. 🟢 `final_eval` roda no env_main (informativo)
- O `scripts/final_eval.py` não aplica o shim `typing.Literal`; em env_b5 cru
  falha (py3.7). Rodei-o no **env_main** (py3.11, Literal nativo) — o `f` de
  `problems.py` é analítico/determinístico e reproduz a ⑦ escrita no env_b5.
  Mesmo caminho do b5. (Se a torre preferir, dá para embrulhar o final_eval com o
  shim para rodá-lo no env_b5 — não alterei o script compartilhado.)

### B6. 🟢 Seed pela convenção D62 (informativo — idêntico ao b5, já ratificado)
- O cartão L.16 escreve `np.random.seed(s)`; segui a convenção D62/seeds.json
  (`iteration_seed(base, alg_id=21, 0, uso)`), como o b5 (ratificado lá).

---

### B7. 🟡 `tests/test_r3_harness.py` — 1 teste ATUALIZADO (necessário na Fase B)
- O `test_experiment_run_roteia_venv_only_para_subprocesso` usava `moead_media`
  como cobaia de "venv-only AINDA-NÃO-registrado" (o docstring documenta a migração
  anterior `b5r → moead_media`). Ao ligar o dispatch de `moead_media` (Fase B), essa
  cobaia se ESGOTA — os 4 venv-only (b5r/b5m/moead_media/c311) estão TODOS
  registrados agora.
- **O que fiz:** reescrevi a prova para forçar um INTERPRETADOR inexistente ⇒ `run()`
  roteia p/ o subprocesso (venv-only) e `run_in_venv` falha com `FileNotFoundError`
  no spawn (jamais `NotImplementedError`, que só o despacho in-process daria). Prova
  o roteamento IGUAL, sem rodar o piso (~40s) e sem cobaia não-registrada.
- **Peço ciência:** foi a única mudança num teste COMPARTILHADO — exigida para a
  suíte fechar em `Ran 321, OK` (critério de fechamento da torre). Alternativa se a
  torre preferir: mover a prova para um alg sintético + monkeypatch de
  `VENV_ONLY_ALGS` (mais verboso; o `FileNotFoundError` de interpretador é o caminho
  mais limpo e já usado por `test_run_in_venv_com_interpreter_preserva`).

### B8. 🟢 Revisão adversarial própria — 2 achados MINOR corrigidos (informativo)
- **F1:** `sigma_dict['sigma_*']` reafirmava "mesmo GP, mesmo μ" (contradizia o campo
  `modelo`, ratificado DI-28: treino INDEPENDENTE, nunca idêntico). Reescrito.
- **F2:** o teste da ④ não guardava a DI-13.10 (`tempo_geracao_s` EXCLUI a sonda).
  Asserções adicionadas. Pilotos re-rodados; ⑦ inalterada (byte-idêntica).

## C. Fase B — WIRING (COMPLETA, 2026-07-23)
1. ✅ `experiment.py:163` descomentado (dispatch `moead_media → run_piso_offline`).
2. ✅ `accept.py::check_r3_piso_off` + bloco CLI do cartão — accept ×3 VERDE.
3. ✅ e2e: `experiment.run(...)` → subprocesso env_b5 → status ok · ⑦ byte-idêntica.
4. ✅ Fechamento: suíte COMPLETA env-main `Ran 321 · OK` · preflight `exit 0`.
5. ✅ B1 (σ NULL) confirmado pela torre; B2/B3/B4/B5/B6 seguem p/ ciência/ratificação.

Nenhum vendored editado; `requirements/**` intocado; `git push`/`add -A` não usados;
`data/experiments/` é gitignored (outputs locais). Único teste compartilhado tocado:
`test_r3_harness.py` (B7, necessário).

**CARTÃO FECHADO — com este cartão, os 21/21 configs do estudo estão implementados.**
