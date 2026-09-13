# Validação do rito de teto — `main/c154/DTLZ2/s42` (T11)

**Torre de fidelidade · 2026-07-31 · tudo re-medido, nada herdado do handoff**
Alvo: `evidencia_T11/teto_c154/experiments/main/c154/exp_main_c154_DTLZ2_42*`

## Veredito recomendado: ✅ **APROVADO — o rito faz exatamente o que promete**

O item **T10 do backlog** (BoTorch abortava por projeção **sem gravar parquet**) está
**fechado**. Verifiquei por medição direta, não por leitura do relatório.

---

## 1. O antes e o depois (a mesma célula)

| | rodada-42 (`INVENTARIO_nao_go_semente42.md`, linha 11) | T11 (medido agora) |
|---|---|---|
| Classe | **B — `teto_wall` por projeção** | `failed` / `motivo_parada=teto_wall` |
| Camadas gravadas | **nenhuma** | **6** (①②③④⑤⑥) |
| FE aproveitados | **0** | **282 de 371 (76 %)** |
| Curva analisável | — | **sim** (IGD+ 0.14472, monotônica) |

Na s42 esta célula não existe em `resultados_experimentos/c154/DTLZ2/42/`. Era uma das
**12 ⚪ do c154**. Agora ela rende dado.

## 2. O rito, evento a evento (do ⑥, íntegro: header + footer, 0 linhas malformadas)

```
it=34  fe=165  wall_projection_warning
       elapsed 2409.8s · proj_restante 19226.7s · max_wall 21600.0s
       "projecao indica que o run nao fecha no teto; seguindo ate o relogio
        (truncamento-com-dado, DI-43/44)"

it=151 fe=282  teto_wall_truncamento
       criterio=elapsed · elapsed 21832.8s · max_wall 21600.0s
       "fecha failed/teto_wall GRAVANDO as camadas parciais"
```

**É aqui que está a correção.** Na rodada-42 o run morria no primeiro evento (it=34, 40 min
de relógio, 165 FE jogados fora). Agora o aviso de projeção é **só aviso**: o run segue
mais 5h20 e entrega 117 FE adicionais e a curva.

## 3. Integridade das camadas parciais (medido)

| Camada | Medida | Confere? |
|---|---|---|
| ① `__real` | 282 linhas; `fase` = {init 131, opt 151}; `fe_index` denso 0..281 | ✅ 131 = 11·D−1 (D=12); 282 = `fe_final` do ⑤ |
| ② `__pop` | 31 237 linhas | ✅ |
| ③ `__surrogate` | 161 060 linhas — `online` 9 060 + `sonda` 152 000 | ✅ 152 000 = 76 blocos × 2 000 (Sobol), e o ⑥ registra exatamente 76 `sonda` |
| ④ `__timing` | 151 linhas = `n_geracoes` | ✅ |
| ⑤ `.manifest` | `status=failed`, `motivo_parada=teto_wall`, `fe_final=282`, `maxfe=371`, `campanha_id=195f64ed0a69_2026-07-31`, `q=1`, `regime=online` | ✅ carimbo de campanha presente |
| ⑥ `.jsonl` | header 1 · timing 151 · decision 151 · sonda 76 · checkpoint 11 · guard 7 · footer 1 | ✅ footer fecha com `status=failed`/`motivo=teto_wall`/`fe_final=282` |

Sem `__final` — correto, é config **online**.

## 4. A curva parcial é cientificamente utilizável (rodei as métricas oficiais)

```
IGD+ 0.14472 · HV 0.37278 · |ND| 36
trajetória: (0, 1.6297) (40, 0.5989) (80, 0.4815) (120, 0.4484)
            (161, 0.1951) (201, 0.1537) (241, 0.1461) (281, 0.1447)  → monotônica ✅
```

A queda de 1.63→0.14 e a monotonicidade em 8 checkpoints mostram que o truncamento não
produziu lixo: é uma **curva de convergência legítima interrompida**, exatamente o que a
DI-43/44 pretendia salvar.

## 5. Resultado científico que caiu de brinde: o gargalo é a aquisição, não o surrogate

| Faixa de gerações | s/geração | % em busca |
|---|---|---|
| 0–30 | 68.2 | 98.7 % |
| 30–60 | 107.3 | 98.9 % |
| 60–90 | 138.3 | 99.0 % |
| 90–120 | 184.5 | 98.9 % |
| 120–151 | 221.3 | 98.9 % |

`tempo_fit_surrogate_s` = 243.4 s no run **inteiro** (1.1 %). `tempo_busca_s` = 21 566 s
(98.8 %). O custo/geração **quadruplica** (58.7 s → 238.8 s) — é o `optimize_acqf` do JES
crescendo com n, não o GP.

**Projeção para fechar os 371 FE:** faltavam 89 iterações; extrapolação linear do custo/ger
⇒ **+7.3 h, total ≈ 13.4 h**. Ou seja: a projeção do run em it=34 estava **certa** (não
fechava em 6 h) — o que mudou foi a *reação* a ela. Um teto de 6 h nunca fechará esta célula;
com 14 h fecharia.

---

## 6. Duas ressalvas (não derrubam o veredito)

1. 🎯 **`tempo_aval_real_s = 0.0`** — a lacuna **I-3** do meu laudo de instrumentação
   (`src/budget.py:222` avalia `true_f(x)` sem cronômetro) **persiste no lado Python**. Foi
   corrigida no MATLAB (verifiquei: não-nulo em 15/15 smokes), não aqui. Impacto: nenhum
   nesta célula (DTLZ2 é analítica, o custo real é ~0), mas o campo continua não-medido e
   não deve ser usado em análise. *Classe 2 se declarada; classe 3 se não.*
2. ⚠️ **Overshoot de 232.8 s** (21 832.8 vs teto 21 600) — 3.9 min, 1.1 %. Esperado: a
   checagem é por iteração e a última durou 238.8 s. Só importa para dimensionar a janela de
   VM (reservar teto + 1 geração).

## 7. O que isto implica para a rodada de 30 sementes

- As **12 ⚪ do c154 + 3 do c262** deixam de ser buracos e viram **curvas parciais**. A
  expectativa de ~6–7 células ⚪ registrada na doutrina de congelamento fica **conservadora
  para cima** — provavelmente serão menos ainda em número de *perdas totais*.
- Mas: célula parcial **não é** célula completa. Para o c154 em DTLZ2 o dado será sempre
  truncado sob teto de 6 h. **Decisão do autor pendente:** (a) aceitar curva parcial e
  comparar por FE-comum, (b) elevar o teto para ~14 h nas células BoTorch, ou (c) declarar
  o corte como limitação metodológica. Recomendo **(a) + declarar**, porque (b) multiplica
  o custo das 3 máquinas por ~2.3 exatamente nas células mais caras.

---

**Comandos que rodei** (todos read-only, sobre `evidencia_T11/`, nenhum toque em
`data/experiments`): leitura dos 4 parquets via `pyarrow`, parse do `.jsonl`, do manifesto,
e `src.metrics.metrics_of_set` / `src.metrics.trajectory` sobre a ① truncada.
