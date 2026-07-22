# R3-e81 — REPASSE À TORRE (o dossiê da sessão, para a instância que gerou o cartão)

> **Para quem lê:** a torre central. Autossuficiente: contexto, cada validação
> **RE-EXECUTADA AO VIVO no fechamento**, os achados, e — na §6 — as
> **DEFINIÇÕES EM ABERTO que a torre DEVE levantar com o autor**.
> Companheiros: `handoff/R3-e81.md` (o *o quê*) e
> `R3-e81_RELATORIO-EXECUCAO.md` (o *como*).

**Data da sessão:** 2026-07-22 · **Cartão:** R3-e81 (qPOTS), ONLINE,
`env_e81_qpots` no Mac (DI-14/RI-08).
**Veredito: CARTÃO FECHADO** — `accept.py R3-e81` **exit 0 (18/18) nos 3
problemas**, `auditar.py` **VERDE ×3**, provas caras verdes, regressão completa
verde (**293 testes**), commits `[R3-e81]`. O teto de 8 h do ZDT1 **NÃO
disparou** (1,99 h).
**Fidelidade NÃO julgada** (D97 — validação manual do autor; números-guia na §5).

---

## 1. Resposta direta: o que foi RODADO para provar?

| # | Comando | Resultado |
|---|---|---|
| 1 | `run_e81('main','e81','MMF1',0)` | `fe_final=61` (=31·2−1 EXATO), 40 ger, `status=ok`, wall **10,9 s** |
| 2 | `run_e81('main','e81','DTLZ2',0)` | `fe_final=371` (=31·12−1), 240 ger, `status=ok`, wall **549,0 s** |
| 3 | `run_e81('main','e81','ZDT1',0, teto_s=8*3600)` | `fe_final=929` (=31·30−1), 600 ger, `status=ok`, **`motivo_parada='orcamento'`** (o teto de 8 h NÃO disparou), wall **7.167,7 s = 1,99 h** |
| 4 | `accept.py R3-e81 --alg e81 --problema {MMF1,DTLZ2,ZDT1} --semente 0` | **exit 0 nos 3, 18/18 checks cada** |
| 5 | `auditar.py e81 {MMF1,DTLZ2,ZDT1} 0` | **VERDE ×3** (exit 0) |
| 6 | `E81_SLOW=1 unittest tests.test_e81.TestRunsCompletos` | **2 OK em 42,8 s** — determinismo bit-a-bit **e** não-perturbação §3.1 |
| 7 | `naoperturbacao.py e81 MMF1 0 --tolerar-ausente` | VERDE (config **NOVO**: sem baseline congelado — o esperado) |
| 8 | `unittest discover` + `preflight.py` + accept {F0×4, R3-00×2, R3-c122×3, R3-c149×3} | **293 OK (7 skip)** — era 272, **+21 do e81** · preflight exit 0 · **12/12 gates existentes exit 0** (re-executados no fechamento) |

Os 3 pilotos rodaram **em sequência, com a máquina livre** — os walls acima são
limpos (lição c122 §6 aplicada).

## 2. Validação consolidada (auditoria pyarrow dos 3 runs)

| Verificação | MMF1 | DTLZ2 | ZDT1 |
|---|---|---|---|
| ① linhas (=31D−1) | 61 | 371 | 929 |
| ① fases init/opt | 21/40 ✓ | 131/240 ✓ | 329/600 ✓ |
| ② membership (linhas) | 1.660 | 60.360 | 377.700 |
| ③ blocos sonda (×2000, ordem do artefato) | 21 ✓ | 121 ✓ | 301 ✓ |
| ③ linhas de busca (front rank-0 do NSGA-II) | 697 | 68.187 | 18.821 |
| ③ `mu_*`/`sigma_*` nulos | 0 / 0 | 0 / 0 | 0 / 0 |
| ③ `fe_treino_max` nulos · sonda `real_solution_id` NULL | 0 · ✓ | 0 · ✓ | 0 · ✓ |
| ③ C3 `espaco_modelo` em TODAS as linhas | `{cru}` | `{cru}` | `{cru}` |
| ③ q=1: EXATAMENTE 1 escolhido/geração | ✓ 40/40 | ✓ 240/240 | ✓ 600/600 |
| ④ nulos nas 5 colunas | 0 | 0 | 0 |
| ④ `n_acumulado` = TREINO | 21→60 | 131→370 | 329→928 |
| ⑤ status · motivo_parada | ok · orcamento | ok · orcamento | ok · orcamento |
| ⑤ cache_hits · q | 0 · 1 | 0 · 1 | 0 · 1 |
| ⑤ sigma_dict (chaves) · sonda.regime | 11 · online | 11 · online | 11 · online |

Zero cache-hits, zero lotes menores que q, zero guardas de `front_1d` — o
mecanismo rodou limpo nos 3.

## 3. 🔴 O achado estrutural da sessão: a D30 "Compartilhado" não é só o nome do kernel

**O que aconteceu.** Implementei o patch Matérn como o cartão escreve
literalmente (*"Matérn = 1 linha `covar_module=`"*): `ScaleKernel(MaternKernel(
nu=2.5, ard_num_dims=D))`. MMF1 e DTLZ2 rodaram; o **ZDT1 morreu no primeiro
fit** com `ModelFittingError: All attempts to fit the model have failed`.

**O que medi** (4 eixos, para não perguntar a coisa errada):

| eixo | resultado |
|---|---|
| nugget `1e-12` vs `1e-6` | as **duas** falham ⇒ não é o nugget |
| kernel RBF stock (sem patch) | **OK** ⇒ é o patch |
| Matérn **sem** `train_Yvar` (ruído inferido) | **OK** ⇒ é Matérn × ruído FIXO |
| n-scan do obj 1 (n=50…329) | 50 ✓, 100 ✓, **150 ✗**, 200 ✓, 250 ✓, 300 ✓, **329 ✗** ⇒ **intermitente** |
| causa subjacente | `OptimizationWarning: scipy_minimize ... "ABNORMAL"` ⇒ **L-BFGS-B não converge**, NÃO é PSD/Cholesky |

**Cheguei a montar a pergunta de pára-e-loga (D81) com 4 remédios** (subir
`max_attempts`, re-semear e re-tentar, cair para `fit_gpytorch_mll_torch`, ou
abortar). **Era a pergunta errada.** A resposta estava no repo:

> A **D30 é marcada "Compartilhado (c262, e81)"** no bundle do e81 — e os DOIS
> runners BoTorch já aceitos materializam essa mesma decisão com uma chamada só:
> `covar_module=get_matern_kernel_with_gamma_prior(D)`
> (**`c262_qnehvi.py:195`** e **`c154_jes.py:247`**), que é
> `ScaleKernel(MaternKernel(nu=2.5, ARD, lengthscale_prior=Gamma(3,6)),
> outputscale_prior=Gamma(2,0.15))`.

Trocado pelo helper: **28/28 fits OK em toda a trajetória do ZDT1**
(n=329→929, os 2 objetivos), e o run fechou em 1,99 h.

**Por que isto é normativo e não estético.** Um Matérn sem prior e um Matérn com
`GammaPrior` são **surrogates diferentes**. Se c262/c154 usam um e o e81 usa
outro sob o rótulo de *uma* decisão, a comparação entre esses configs passa a
medir a diferença de priors, não a diferença de algoritmo — e "compartilhado"
vira falso no dado.

**Recomendação de doc-sync (§6.1):** a redação do checklist §22.4·3.5
("**Matérn = 1 linha** `covar_module=` (model_object.py:120–124)") admite a
leitura que eu segui e que torna o ZDT1 irrodável. Sugiro cravar a chamada:
`covar_module=get_matern_kernel_with_gamma_prior(D)` — **a mesma de c262/c154**.

**Achado de fidelidade colateral, travado por teste:** o default do
`SingleTaskGP` no **BoTorch 0.16.1** é um **`RBFKernel` PURO** — sem
`ScaleKernel`, logo **sem outputscale**. A prosa da SPEC diz "RBF ARD default";
está correta quanto ao RBF, mas a ausência do `ScaleKernel` é o detalhe que
muda o que a D30 de fato acrescenta.

## 4. Os outros 3 achados de infra (todos MEDIDOS, não inferidos)

### 4.1 O kwarg `c3=` do DI-23 exige **dict** — e o próprio teste do DI-23 passa string

As duas rotas de C3 têm formatos **opostos**: `_stamp_c3_sonda` (c149) muta a
row já construída ⇒ **string**; o `c3=` repassa `**c3` ao `surrogate_row`, que
faz o `json.dumps` ⇒ **dict**. Medido:

```
c3 com DICT   -> {"mu": [0, 0]}          json.loads -> dict
c3 com STRING -> "{\"mu\": [0, 0]}"      json.loads -> str    (precisa de 2 loads)
```

⚠ **`tests/test_di23_harness.py:90-91` passa `json.dumps({...})` dentro de
`c3=`** — e o teste passa porque as asserções (`:94-96`) só olham
`espaco_modelo` e `transf_tipo`, **nunca** `transf_params`. Qualquer config
futuro (b5 / c311 / piso-off) que copie esse teste como exemplo de uso grava a
③ **duplo-encodada em silêncio**, e a R4 precisaria de dois `json.loads` sem
nunca ser avisada. O `check_r3_e81` decodifica uma amostra e **reprova se não
for dict**.

### 4.2 O `break` do cache-cap do c149 deixa a ④ com NULL — e reprovaria o próprio gate

Em `c149_lbnmobo.py`, `buf.add_timing(...)` abre a linha da ④ na **:665**, o
`break` do cache-cap está na **:738** e o `buf.update_timing(...)` só vem na
**:760-762**. Num aborto, a geração fica com
`tempo_busca_s`/`tempo_pred_sonda_s`/`tempo_geracao_s` = **NULL** — o que
**reprova o check `④ timing v5.2.1 completa`** do `accept.py:928-933` (que testa
`any(v is None)`). Pior: se a sonda de cadência rodou nessa geração, o bloco
final não roda (guardado por `ultima_sonda_g != g`) e o `t_snd` medido se perde.

**No e81 a ④ é fechada em `finally`**, então o aborto por teto — que o cartão
trata como **DADO** ("manifesto failed + curva parcial é o entregável correto")
— produz uma ④ **válida**. *Não foi exercitado ao vivo* (o ZDT1 fechou em 1,99 h);
é a mesma lacuna de cobertura que a DI-23.4 registrou para o c149.

### 4.3 `write_run_outputs` não repassa `q` — os 150 runs de `exp=batch` mentiriam

`new_manifest` fixa `q=1` (`manifest.py:45`) e o `write_run_outputs` não o
repassa (`standalone_harness.py:1044-1053`). O `runs_matrix.csv` tem **900
linhas de e81: 750 em `main` com q=1 e 150 em `batch` com q=10**. O runner
carimba `man["q"]` quando diverge, mas a lacuna é de infra e atinge qualquer
config do sub-estudo batch (D66).

## 5. Custo medido (o insumo do M7/M8) — e a parede está onde não se esperava

| Run | wall | fit% | busca% | sonda% | s/geração |
|---|---|---|---|---|---|
| MMF1 (D=2) | 10,9 s | 22,6 | 37,4 | 11,1 | 0,17 |
| DTLZ2 (D=12) | 549,0 s | 12,0 | **82,2** | 2,3 | 2,18 |
| ZDT1 (D=30) | **7.167,7 s (1,99 h)** | 15,5 | **83,0** | 0,6 | 11,7 |

**A curva de escalabilidade (④), por regressão log-log:**

| | fit | busca |
|---|---|---|
| DTLZ2 (n 131→370) | 0,118 s → 0,462 s (×3,9) — **n^1,81** | 1,81 s → 1,96 s (×1,1) — **n^0,10** |
| ZDT1 (n 329→928) | 0,521 s → 3,409 s (×6,5) — **n^2,53** | 9,41 s → 10,22 s (×1,1) — **n^0,10** |

**A leitura, e é um resultado do §17.6:** o `tempo_fit_s` **exibe a parede
O(n³)** — o expoente sobe de n^1,81 (D=12) para **n^2,53** (D=30), convergindo
para o cúbico à medida que n cresce. Mas o fit é só **15% do wall**. Os **83%**
estão na **busca**, que é **essencialmente PLANA em n (n^0,10)** e explode com
**D**: 1,8 s (D=12, pop=1.200) → 9,4 s (D=30, pop=3.000).

Ou seja: **no qPOTS o gargalo não é o treino, é a aquisição** — o Thompson
sampling exige uma amostra da posterior sobre `pop = 100·D` pontos, a cada uma
das `ngen=10` gerações do NSGA-II, por objetivo; o custo é dominado pela
decomposição da covariância **do lado do TESTE** (3.000×3.000 no ZDT1, exata
porque importar BoTorch eleva `max_cholesky_size` a 4096 — N.2), que não depende
de n. É um contraste direto e limpo com o c238/c262 (parede no treino) e com o
c122/c149 (que escapam da parede por construção).

**Dimensionamento M8 (30 sementes):** ZDT1 domina — **~60 h·core por
problema-D30**; paraleliza por semente. O e81 **não** é o curinga imprevisível
que o cartão temia: é um custo MEDIDO, e o teto de 8 h tem folga de 75%.

## 6. 🔴 DEFINIÇÕES EM ABERTO — a torre DEVE levantar com o autor

1. **RATIFICAR o kernel `get_matern_kernel_with_gamma_prior(D)`** (§3) — **a
   única decisão desta sessão que toca fidelidade.** Ancorada no precedente
   c262:195 / c154:247 e no rótulo "Compartilhado (c262, e81)", mas o cartão diz
   apenas "1 linha `covar_module=`". A evidência de que a alternativa sem prior
   torna o **ZDT1 irrodável** está na §3. **Se o autor vetar, o cartão precisa de
   uma decisão sobre o fit que falha** (os 4 remédios que eu tinha levantado).
2. **Doc-sync do checklist §22.4·3.5** — cravar a chamada exata do kernel, para
   o próximo leitor não repetir o meu caminho.
3. **`c3=` exige dict + o teste do DI-23 usa string** (§4.1) — corrigir
   `tests/test_di23_harness.py:90-91` e, idealmente, fazer o `surrogate_row`
   **recusar** uma string em `transf_params` (falha aberta em vez de
   duplo-encode silencioso). **Bloqueia risco em b5 / c311 / piso-off.**
4. **`update_timing` antes de qualquer `break` no c149** (§4.2) — o aborto por
   teto/cache-cap do c149 grava uma ④ que o próprio gate reprova. Decisão de
   infra (M7); o padrão correto está no e81 (`finally`).
5. **`q` no `write_run_outputs`** (§4.3) — kwarg no harness, senão os 150 runs
   de e81 em `exp=batch` (e todo o sub-estudo D66) gravam `q=1` mentido.
6. **`load_sonda` recalcula `f_hash_online` e nunca o compara ao sidecar**
   (`standalone_harness.py:701-707`) — o campo EXISTE nos 3 sidecars conferidos.
   É uma comparação esquecida; o `f_hash` que vai ao manifesto não é auditado.
7. **`auditar.py` usa `.to_pandas()`** (`:98`) e o `env_e81_qpots` **não tem
   pandas** — o validador permanente **só roda no env-main**. Funciona (foi como
   rodei), mas convém registrar, ou trocar por pyarrow puro.
8. **Fila de outras mãos:** julgamento de fidelidade D97 (autor, em lote —
   números-guia na §5 e no handoff); `cards/INDEX.md` (torre).

## 7. Onde está cada coisa

- **Mapa técnico** (os 3 ganchos, a semântica do σ, as 9 decisões de sessão):
  `handoff/R3-e81.md`
- **Narrativa** (o que deu errado e como foi pego): `handoff/R3-e81_RELATORIO-EXECUCAO.md`
- **Dados:** `data/experiments/main/e81/exp_main_e81_{MMF1,DTLZ2,ZDT1}_0.*`
- **Reprodução:** `handoff/R3-e81.md` §6 (comandos literais)
- **Commits:** `[R3-e81]` no branch `experiment/definitive_algorythms`
  (código+gate+testes · handoff+relatório · este repasse). **`cards/INDEX.md`
  NÃO marcado** — a torre marca. **Vendor `algorithms/e81_qPOTS/` INTOCADO**
  (o `repos.lock` segue válido).
