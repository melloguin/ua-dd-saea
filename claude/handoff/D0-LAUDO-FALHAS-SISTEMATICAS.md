# LAUDO FINAL — DIAGNÓSTICO D0 (síntese das 3 autópsias · snapshot da coleta de 13–14/08/2026)

**Regra de leitura usada em todo o laudo (O-21):** o rodapé do `.jsonl` é a autoridade sobre o que aconteceu com o algoritmo; o `status` do manifest é a visão do despachante. `manifest:failed` + `rodapé:ok` = aborto sancionado ⚪ (teto), não falha. `motivo_parada="checkpoint_em_andamento"` é sentinela ambíguo — nunca classifique por ele.

## 0. Limites deste laudo (antes de qualquer número)

1. **O snapshot está vivo.** A coleta foi tirada com o sync a ~46% em partes; vm5 ainda sincronizava (manifests cresceram 129→182 durante a análise) e havia células **em execução** no instante da foto. Toda contagem abaixo é do snapshot, não da campanha.
2. **Os censos divergem entre autópsias.** A autópsia c154 contou 306 manifests (vm1/vm2/vm10, "vm3 zero"); o censo por-VM viu c154 também em vm3 (88/153 failed) e vm4 (27/53). A matriz da missão (ZDT6=2, F55=8, F1=13) diverge de ambos. São cópias/momentos de sync diferentes. **As causas-raiz são estáveis e provadas; as contagens finais exigem recenso pós-sync.**
3. **Conflito entre autópsias sobre células sem rodapé.** O censo por-VM classificou 34 células sem rodapé como O-22 (morte de máquina). As autópsias profundas **refutam isso para 16 delas**: as 12 de c154 e as 4 de c262 têm último registro com `ts` de 2026-08-13 22:48–22:59 UTC ≈ hora do snapshot — estavam **em voo**, não mortas. Para as ~18 restantes (vm3 semente 25, vm4 semente 18, células fora de c154/c262) **ninguém verificou timestamp — inconclusivo**; recontar depois que pousarem.
4. **RAM não foi medida por nenhuma autópsia.** A recomendação de "menos jobs por host" vem do custo superlinear do GP em *tempo de parede*; não há evidência de pressão de memória nos dados coletados.
5. **Atribuição fina em c154×WFG1 diverge**: a autópsia c154 viu ModelFittingError (10/12); o censo por-VM (frota inteira) também viu RuntimeError rota (a) em WFG1 (16×). Ambas as exceções ocorrem na família; o rateio exato por problema fica para o recenso.

## 1. Tabela: família → causa-raiz PROVADA → classe

| Família (alg × problema) | Causa-raiz provada | Evidência citada | Classe |
|---|---|---|---|
| c154 × DTLZ2/3/4 | Teto de 12h com 73–87% do orçamento cumprido; parada limpa do harness | `exp_main_c154_DTLZ2_0.manifest.json` (`teto_wall`, 43.361s, fe 284/371) + rodapé `status="ok"`; 125 casos com tempo ∈ [43200, 44728]s | ⚪ sancionado (recuperável com teto maior, se o protocolo quiser) |
| c154 × DTLZ7, MMF16_20, WFG2/4/5/9, ZDT1, ZDT3 | Teto de 12h com apenas 39–50% cumprido | mesmo padrão manifest×rodapé nas 3 VMs | ⚪ sancionado (recuperação cara: 48h + host dedicado) |
| c154 × ZDT6, BBOB_F5/F22/F49/F55 (+2 WFG9) | Escada do `random_search_optimizer` esgota (`pop_size=1024, max_tries=10`, "Only found N optimal points instead of 10") → política D81 pára-e-loga | `RuntimeError` em **`src/c154_jes.py:327`**; rodapé de `exp_main_c154_BBOB_F55_0.jsonl`; `rec="rs_runtimeerror_fallback"` em `WFG9_13` | precisa-fix (ou aceitar como incapacidade — decisão de protocolo sob freeze) |
| c154 × WFG1 | Falha de fit do GP (10/12 células) | `ModelFittingError` em `botorch/fit.py:289`, rodapé de `exp_main_c154_WFG1_1.jsonl` | precisa-fix / aceitar (fix vetado pelo `m8-freeze`) |
| c262 × DTLZ7, ZDT3, MMF16_20 | Teto de 12h cravado; **projeção O-20 nunca abortou** — projetor só avisa e "segue até o relógio" | `exp_main_c262_DTLZ7_0.jsonl:1285` (warning literal) + rodapé duplo teto_wall/ok; parquets `__pop/__real/__timing` presentes; fe_final: DTLZ7 507–595/681, ZDT3 845–904/929, MMF16_20 529–612/619 | ⚪ sancionado, dado parcial íntegro |
| c262 × WFG1 | Crash de fit do GP na região flat; determinístico por semente (guard no-retry); 2/14 sementes sobrevivem | 11× `ModelFittingError` (`src/c262_qnehvi.py:640` → `botorch/fit.py:289`) + 1× `OptimizationGradientError` NaN (`botorch/generation/gen.py:468`); guard casa `experiments.py:87` | incapacidade seed-dependente — aceitar + reportar taxa (fix vetado pelo freeze) |
| b1 × DTLZ4 | Regressão do kriging subdeterminada após dedup (`n_treino=156, n_dedup=0`; α=100 do DTLZ4 colapsa os x) | `error` em **`ParEGO/dacefit.m:102`**; rodapé idêntico em 18/18 células (26 na frota, 6 VMs); determinismo provado em 2 arquiteturas — `experiments.py:77-88` (`NO_RETRY_SUBSTRINGS`); **0 parquets** | aceitar como incapacidade documentada (re-execução provadamente inútil; fix vetado pelo freeze) |
| c238 × BBOB (F1/F5/F22/F55) | `MATLAB:badsubscript` ("Index must not exceed 1") sempre em fe≈109–110, 20× em 5 VMs — intrínseco e reprodutível | `exp_main_c238_BBOB_F5_11.jsonl` (vm2) | precisa-fix — **mas arquivo:linha NÃO localizado** (nenhuma autópsia desceu ao código MATLAB do c238; investigação pendente) |
| b5m, b5r, moead_media × semente 10 (vm4, 75 células) | venv `env_b5` inexistente na vm4 (path default do Mac) — morte em 0,065s | `FileNotFoundError` em `exp_off_b5m_ZDT3_10.jsonl:stack_trace` | ambiente — recuperável trivialmente |
| sobol_batch (vm2, 2 células) | IAM do GCS sem `storage.objects.delete` para o SA `894264959151-compute@...` | `403 Forbidden` em `exp_batch_sobol_batch_MMF16_20_0.jsonl` | ambiente — recuperável |
| c154/c262 × MMF1 semente 30 (vm10, 2 células) | DoE não materializado | `FileNotFoundError data/doe/MMF1/doe_MMF1_30.parquet` (D63) | infra — recuperável (F0-02) |
| nsga3 × DTLZ3_17 (vm10, 1) | Licença MATLAB (Error 15, Statistics Toolbox) | `MATLAB:license:checkouterror` no jsonl | ambiente pontual — re-rodar |
| e74 (vm1, 1) | `stats:pdist2:SizeMismatch` — **causa não investigada** | jsonl vm1 | inconclusivo — re-rodar e observar |
| c122, c149 (failed) | ~100% teto_wall com rodapé ok | censo por-VM (59 + 16 células) | ⚪ sancionado |
| ~34 células sem rodapé | 16 provadas EM VOO (ts ≈ snapshot); ~18 sem verificação | ver §0.3 | inconclusivo — recontar pós-pouso; **não re-disparar antes** |

Achados negativos importantes: `cache_hit_travado` = **zero** ocorrências na coleta inteira; nenhum indício de symlink A48 quebrado; as "centenas de falhas rápidas em vm2/vm10" relatadas pelo monitor **não existem** — eram células *ok* de baselines fechando em segundos por cache-hit (vm2: 313 ok <60s, 269 com `cache_hits>0`; vm10: 374/331; padrão idêntico na vm1).

## 2. Plano de ação por família

**A. Re-rodar sem mexer em código (ambiente/infra) — fazer ANTES de qualquer re-disparo:**
1. **vm4**: provisionar o venv `env_b5` (via `requirements/`) ou passar `interpreter=` explícito → re-rodar as **75 células** b5m/b5r/moead_media semente 10 (custo de re-teste quase nulo: morriam em 0,065s; vm3 rodou b5m ok, confirmando que é só ambiente).
2. **vm2**: conceder `storage.objects.delete` ao service account → re-rodar as 2 sobol_batch.
3. **Materializar `data/doe/MMF1/doe_MMF1_30.parquet`** → re-rodar c154 e c262 MMF1_30 (e conferir se outras sementes altas de MMF1 têm DoE).
4. **vm10**: conferir disponibilidade de licença do Statistics Toolbox → re-rodar nsga3×DTLZ3_17. Re-rodar também o e74 (1 célula) e observar.

**B. Re-rodar só se o protocolo decidir fechar as ⚪ (decisão de teto, não recuperação):**
- c154 × DTLZ2/3/4: teto **24h** (estavam a 73–87%).
- c154 × DTLZ7/MMF16_20/WFG2/4/5/9/ZDT1/ZDT3: teto **48h** em VM com **menos jobs por host** — a 39–50% em 12h, e o custo por FE do GP cresce superlinearmente, 24h provavelmente não basta. Melhor ainda: **resume dos checkpoints existentes**, se o harness suportar.
- c262 × MMF16_20 (pararam a 1–15% do fim), ZDT3 (91–97%), DTLZ7 (74–87%): fecham com acréscimo menor de teto, mas dê folga generosa pela mesma superlinearidade.
- Sem dado de RAM nas autópsias: se subir teto, **instrumentar memória** no re-disparo.

**C. Aceitar como aborto/incapacidade e documentar (consistente com o congelamento `m8-freeze`):**
- **b1 × DTLZ4**: incapacidade determinística certificada (2 arquiteturas, 6 VMs, 18 sementes idênticas, NO_RETRY do próprio harness). Documentar como taxa 0/N. As 12 sementes pendentes falharão igual em ~2 min cada — rodá-las por simetria do protocolo ou excluí-las é escolha sua; o custo é desprezível.
- **c262 × WFG1**: incapacidade seed-dependente (2/14 ok até agora) — reportar taxa de sucesso; não re-tentar sementes já falhadas (determinístico); sementes novas podem rodar.
- **c154 × ZDT6/BBOB/WFG1**: mesmo tratamento sob o freeze. Se o autor decidir emendar o protocolo: os fixes seriam (i) relaxar a política D81 da escada RS / fallback em `src/c154_jes.py:327` e (ii) robustecer o fit do GP (jitter/prior/normalização) — ambos vetados enquanto o freeze valer.
- **c238 × BBOB**: intrínseco e reprodutível (fe≈110, 5 VMs), mas o ponto exato no código não foi localizado — abrir investigação dedicada antes de decidir fix vs. incapacidade.

**D. Não fazer nada ainda:** as ~34 células sem rodapé — 16 comprovadamente em voo no snapshot (sementes 7/13/17 de c154/c262). Esperar pousarem + sync da vm5 completar, e **recensear a matriz inteira**.

## 3. Impacto na análise

- **Células ⚪ (teto_wall) contam como truncamento-com-dado: SIM**, por DI-43/44 — é a nota literal do próprio projetor ("truncamento-com-dado") e o fechamento grava as camadas parciais. Para **c262** os parquets `__pop/__real/__timing` foram **conferidos presentes**; para **c154** a mecânica de fechamento é a mesma (rodapé ok = parada limpa), mas a presença dos parquets **não foi conferida** na autópsia — verificar no recenso. Na análise: registrar `fe_final` de cada célula ⚪ e comparar em orçamento de FE comum (ou reportar o ponto de truncamento); a variância de fe_final entre sementes é pequena (~1–5% em c262).
- **Falhas algorítmicas reais NÃO são truncamento-com-dado.** b1×DTLZ4 não tem parquet nenhum — célula vazia, entra como incapacidade (taxa de sucesso 0). c262×WFG1 e c154×ZDT6/BBOB entram como incapacidade com taxa reportada; não foi verificado se as camadas pré-crash dessas células são utilizáveis (c154 morre em ~3–5 min; c238 em fe≈110) — não assumir que são.
- A matriz de status por célula deve distinguir 5 estados: **ok · ⚪ teto_wall (com fe_final) · incapacidade algorítmica · falha de ambiente (re-rodável) · em-voo/pendente**. Misturar ⚪ com falha infla artificialmente a taxa de falha em 367 células (o grosso do "failed" de manifest da frota).

## 4. Briefing para a instância que vai re-disparar as 1.875

1. **Pré-condições obrigatórias** (senão re-falha instantânea): venv `env_b5` na vm4; IAM `storage.objects.delete` na vm2; `doe_MMF1_30.parquet` materializado; licença Statistics Toolbox conferida na vm10.
2. **Grid — remover retries de sementes deterministicamente falhadas**: b1×DTLZ4 (todas), c262×WFG1 (as 12 falhadas), c154×{ZDT6, BBOB_F5/F22/F49/F55, WFG1}, c238×BBOB. O harness já suprime via NO_RETRY, mas excluir do grid limpa a fila e o log. **Sementes novas dessas famílias podem rodar** (WFG1 é seed-dependente; b1×DTLZ4 é 100% falha mas custa ~2 min/célula — decisão do autor).
3. **Teto**: manter 12h no grosso; só ajustar se o protocolo decidir fechar as ⚪ (24h para c154×DTLZ2/3/4; 48h + menos jobs/host para o grupo a 39–50%; preferir resume de checkpoint). Não há dado de RAM — monitorar no disparo.
4. **Não re-disparar** as células sem rodapé (sementes 7/13/17 em vm1/vm2/vm10; semente 25 vm3; semente 18 vm4) antes do recenso pós-sync — 16 estavam comprovadamente vivas; re-disparo duplicaria execução.
5. **Contabilidade**: rodapé O-21 é a autoridade; `teto_wall` no manifest com rodapé ok = ⚪, não falha; `checkpoint_em_andamento` é sentinela ambíguo; **células MATLAB (b1) não geram manifest** — censo delas só por `.jsonl` (jsonl órfãos em 6 VMs).
6. **Sem ajuste necessário** para: cache (cache_hit_travado inexistente; "falhas rápidas" do monitor eram oks por cache-hit), symlinks A48, projeção O-20 (não aborta ninguém).
7. **Recensear tudo pós-sync**: os censos deste laudo vieram de um espelho parcial (vm5 a meio, vm3/vm4 divergentes entre autópsias); as classes e causas ficam de pé, os totais não.

---

## 5. DECISÕES DO AUTOR (14/08/2026) — atualizam o briefing §4

- **DEC-5 → encerrada por confirmação da DI-44**: as 481 células teto_wall
  (medição da torre: TODAS pararam entre 12,00h e 12,49h; zero antes) são
  truncamento-com-dado VÁLIDO. Nada a re-rodar; a análise usa fe_final.
- **DEC-6 → SIM**: incluir no grid as 12 sementes pendentes de b1×DTLZ4
  (falha determinística ~2 min/célula; o protocolo fecha "0/30 tentadas").
- **DEC-7 → SIM**: devolver ao grid as sementes NÃO-TENTADAS das famílias
  seed-dependentes — c262×WFG1 e c154×{ZDT6, WFG1, BBOB_F5/F22/F49/F55}.
  NÃO re-tentar sementes já falhadas (determinístico por semente).
  c238×BBOB continua FORA até a investigação da torre.
- **CORREÇÃO DA TORRE ao item MMF1_30 do §2.A.3**: a semente 30 NÃO existe
  no protocolo ({0–28, 42}) — as 2 células exp_main_{c154,c262}_MMF1_30 da
  vm10 são fantasmas da herança de julho. Ação certa: QUARENTENAR os
  arquivos; JAMAIS materializar doe_MMF1_30 (legitimaria célula fora do
  grid). O item original do laudo está superseded por esta nota.
