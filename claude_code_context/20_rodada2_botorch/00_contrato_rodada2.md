# Rodada 2 — contrato transversal BoTorch (Python, Vertex AI)

> ⚠ **ARQUIVO GERADO** da `SPEC_experimentos_v5.2.md` (fonte única da verdade) por `gen_bundles.py` — **não edite à mão; regenere**. Em conflito entre este bundle e a SPEC, **vale a SPEC** (precedência global: Anexo S > §22 > Anexo D > corpo > E/I/K/L > históricos).

**📋 LEITURA OBRIGATÓRIA ANTES DE CODAR (correção estrutural 2026-07-19):** este contrato de rodada NÃO contém o contrato de DADOS. Leia **`CONTRATO_DE_DADOS.md` (raiz do repo)** — as camadas ①②③④⑤⑥⑦, a **SONDA canônica** (§17.2.2/§3.1: artefato de 20.000 pontos; ONLINE lê a fatia de 2.000 a cada k=2 gerações; OFFLINE lê as 20.000 1× por modelo treinado, com `geracao`=NULL), a camada **⑦ `__final`** (DI-08/DI-13.9 — SÓ offline: TODOS os finais avaliados 1× e o ND filtrado DEPOIS), o **timing v5.2.1** (§17.6: `tempo_fit_s` [NULLABLE nos pisos] / `tempo_busca_s` / `tempo_pred_sonda_s` / `tempo_geracao_s` + bloco `timing` OBRIGATÓRIO no manifesto) e o **`.jsonl` enriquecido** (S.7.1/DI-10). O `REGISTRO_DECISOES_IMPLEMENTACAO.md` (DI-01..DI-14) traz o PORQUÊ de cada uma. Em divergência: SPEC > CONTRATO_DE_DADOS > este bundle.

**Decisões-chave:** BoTorch **OFICIAL 0.18.1** (nunca o fork do device — N.2.3) · D62 (`SeedSequence((base,alg_id,iter,uso_id))` p/ toda semente interna) · D79 (subprocess-por-venv; `OMP/OPENBLAS/MKL/NUMEXPR=1`; float64; CPU) · D53/D54 (export float32 sem round; **c262/c154 são bucket-only**) · D58 (resume dos bucket-only LISTA O BUCKET) · **D86 (higiene torch: `no_grad` na predição; `del`+`gc.collect()` por iteração — N.1.5)** · D61 (`BudgetExhausted`).

---

### 22.3 Rodada 2 — BoTorch (Python; Vertex AI; grava local + bucket, §17.7)

**Infra da rodada (contrato N.1 + L.18):**
- [ ] **BoTorch OFICIAL 0.18.1** — nunca o clone do device (é um **fork** com kernel C++ `-march=native` que falha silenciosamente no arm64 → numérica assimétrica Mac×Linux; N.2.3). Registrar no manifesto versão exata + hash (o fork tem `__version__=="Unknown"`).
- [ ] `torch.set_num_threads(1)` + **float64** + CPU em todo stack torch (N.1.1); `np.random.Generator` próprio p/ DoE; **salvar/restaurar o RNG global em volta de `pymoo.minimize`** (N.1.3); diretórios de export por `(alg, problema, semente)` (N.1.4).
- [ ] Adapter BoTorch: `normalize/unnormalize [0,1]↔nativo` + `−f` (maximização) + `Standardize` de Y (§5.5); **snapshot por iteração de BO** (§17.3); `torch.manual_seed(h(run,it))` **antes** de construir modelo+acqf (L.10). Registrar a versão do scipy (fast-path L-BFGS-B em [1.13,1.19) — L.18).
- [ ] **Persistência Python** (§17.7): local + upload ao bucket `mestrado_experiments` (ADC da conta de serviço) + sync de pendentes — **construída aqui, reutilizada pela Rodada 3**.

**Checklist por algoritmo:**


**Piloto da Rodada 2:** a **curva `(n_acumulado, tempo_fit_s)`** dos GP-BO é o dado-alvo (§17.6 — a parede O(n³) começa aqui); B9.5 decidida; smoke-test da persistência **local+bucket byte-idêntico + sync**. **Ao passar o gate, a VM pode rodar c262/c154 enquanto a Rodada 3 avança.**

---

### N.1 — Contrato transversal Python (fan-out por processo)
1. **`torch.set_num_threads(1)` em TODOS os stacks torch** (c122, c149, c262, c154, e81): nenhum repo o faz, e vários abrem `device='cuda'` **sem índice** (c122:100, c149 Forward_BNN:29/40) → em CPU cada processo usa todos os cores (oversubscription no grid); em nó com GPU todos pegam `cuda:0`. Fixar CPU + threads=1 + float64.
2. **⚠ Colisão de pacote vendorizado (offline — o pior achado):** b5 e c311 vendorizam `desdeo_emo`/`desdeo_problem`/`desdeo_tools` com **mesmo nome e código diferente** (b5: ProbRVEA/ProbMOEAD/SurrogateKriging; c311: OfflineRVEA/treedGP/FullGP). `sys.modules` cacheia o 1º importado → **co-importar b5 e c311 no mesmo processo usa DataProblem/RVEA ERRADOS sem erro**. Os `sys.path.insert` são hard-coded para paths do autor (`amrzr`, inexistentes aqui) → a resolução cai para o cwd. **Regra: isolar b5 e c311 em processos/venvs distintos, sempre; nunca co-importar.**
3. **Seeds globais re-semeados:** `pymoo.minimize(seed=·)` re-semeia `np.random`/`random` GLOBAIS (e81, c149, e o NSGA-II interno de vários) → **salvar/restaurar o estado do RNG numpy em volta de cada chamada** e usar um `np.random.Generator` próprio para o DoE, imune ao reset.
4. **Sem `makedirs(exist_ok=True)`:** b5/c311 (e c149) criam diretórios de saída sem `exist_ok` e logam em arquivo nomeado por `str(datetime.now())` (com espaços/`:`) compartilhado por todos os workers → TOCTOU + nomes inválidos. O nosso harness escreve o export (§17), não os drivers dos autores.
5. **[D86/v5.1] Higiene de memória nos loops torch (c149 sobretudo; e7/c122 por extensão):** `torch.no_grad()` em TODA predição; ao fim de **cada iteração** do loop de retreino, `del` dos tensores intermediários + `gc.collect()` (+ `torch.cuda.empty_cache()` quando houver GPU) — nenhum tensor de iterações passadas retido (o export grava e solta). Sem isso, o retreino-por-FE do c149 (D43) acumula grafo/tensores ao longo de centenas de FEs → OOM no MEIO do run (dado perdido; o D60 só mata). O piloto mede o pico de RAM (§22.5).

---

### L.18 · BoTorch core — ver L.10/L.11; adicionais: `fit_gpytorch_mll` (max_attempts=5; retries amostram dos priors → RNG torch); ICs do optimize_acqf = Sobol scrambled + seleção Boltzmann (eta=1, garante argmax); `batch_limit=num_restarts` default; qLogNParEGO disponível p/ o qParEGO do batch (pesos simplex no CONSTRUTOR → re-instanciar por iteração = 1 λ novo/iteração, ancorado no torch.manual_seed); prune_inferior_points: 2048 amostras, máscara ND∧>ref. Fontes de não-repro bit-a-bit (registrar no manifesto): threads, versão scipy (fast-path [1.13,1.19)), kernel fusionado `-march=native`, dtype.
