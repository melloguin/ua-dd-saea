# R3-b5 — REPASSE À TORRE

> O que a torre **DEVE levantar com o autor** antes de fechar o R3, e as notas
> por-modo. A validação objetiva foi re-executada AO VIVO — ver
> `R3-b5_RELATORIO-EXECUCAO.md`. Fidelidade = manual do autor (D97).

## A. Definições EM ABERTO — "a torre DEVE levantar com o autor"

### A.1 — Completamento do env_b5 (D80 — pins são do autor) ⚠ PRIORIDADE
O env "PROVISIONADO E VALIDADO (DI-22)" **não rodava o desdeo**: o proof do R3-00 só
exercitou `import sklearn/desdeo_problem + load_sonda`, nunca o caminho
evolver/DataProblem/dataset-read que b5 (e c311, e moead_media) percorrem. Fechei os gaps
(autor delegou "o que você achar mais recomendado" em cada pergunta), mas **cada um é um
pin/decisão de torre a RATIFICAR**:
1. **pymoo==0.6.1.2** em env_b5 (finais ⑦ + filtro ND via `src/problems.py`). Requer o
   shim py3.7 `typing.Literal` no runner (o NDS-loader do pymoo importa `typing.Literal`,
   py3.8+). Roda puro-python (sem Cython) — só velocidade; os finais são pequenos.
2. **plotly==4.14.3 + graphviz** em env_b5 (import-time do desdeo_emo). Iguais ao env_c311.
3. **pandas 0.25.3 → 1.3.5**: o 0.25.3 QUEBRA o `DataProblem` do desdeo
   (`pd.DataFrame(columns=,index=[0])` é bug do pandas 0.25). O desdeo NÃO pina pandas
   (a nota "forçado pelo desdeo" era incorreta); o harness escreve parquet 100% via
   pyarrow ⇒ **nenhum byte de saída muda**. Autor CRAVOU o 1.3.5.
4. **pygmo NÃO instalado — STUB no runner**: `desdeo_emo.EAs.__init__` force-importa
   NSGAIII/PPGA (→ pygmo) e `selection.__init__` importa NSGAIII_select (→ pygmo), mas o
   caminho do b5 (ProbRVEA_v3/ProbMOEAD) NUNCA os instancia. pygmo é dep Boost pesada,
   ausente até no env_c311. O stub oferece só `fast_non_dominated_sorting` (nunca chamado).
   **A torre deve decidir**: manter o stub (b5-only) ou instalar pygmo no env_b5.
5. **BUG DE TORRE — `doe.py:219`**: `ChunkedArray.to_numpy(zero_copy_only=False)` é inválido
   no pyarrow 12 (o kwarg é do `Array.to_numpy`). Funciona no pyarrow 25 do env_main (onde
   o stub R3-00 rodou), mas estoura em env_b5 — o caminho `load_dataset` do offline-Python
   nunca fora exercitado. **NÃO editei o `doe.py` compartilhado** (sessão c311 concorrente
   tocaria o mesmo arquivo); apliquei um **shim LOCAL no runner** (`combine_chunks()`,
   saída bit-idêntica). **A torre deve aplicar o fix central** (vale p/ b5 + c311 +
   moead_media) e então o shim do runner vira no-op.

### A.1.6 — repos.lock: re-lacre SÓ do b5_desdeo (drift pré-existente nos outros)
Re-lacrei APENAS `b5_desdeo` (5e17…→3bf1…, os 2 patches vendorizados) editando a linha à
mão. ⚠ Rodar `preflight --write` cheio muda TAMBÉM `e74_clmea`, `e81_qpots`, `c149_lbnmobo`
(stored ≠ computed já no BASELINE do meu início — drift PRÉ-EXISTENTE, provável bytecode
`__pycache__`/.pyc na árvore) e `c311_tgprmo` (sessão concorrente). NÃO commitei esses — não
são meu trabalho. **A torre deve re-lacrar o repos.lock inteiro de um checkout LIMPO** (sem
.pyc) ao integrar, e idealmente o `tree_sha256` deveria excluir `__pycache__` (senão o lock
"envelhece" a cada import). `preflight` fica verde de qualquer forma (não compara hashes).

### A.2 — Semeadura: convenção vs. literal do cartão
O cartão (L.16) escreve `np.random.seed(s); random.seed(s)`. Usei a **convenção do
pipeline** (D62/D91): `iteration_seed(base, ALG_ID, 0, uso)` com **ALG_ID b5r=17, b5m=18**
do `seeds.json` — idêntico ao c122/c154 e coberto pelo teste anti-descompasso. É a leitura
canônica (senão o `seeds.json` não definiria alg_ids para o b5), mas **o autor deve
ratificar** que a semântica do cartão era "semear determinístico do `s`", não o `seed(s)` cru.

### A.3 — Mecanismo geracao=NULL da sonda offline (precedente p/ c311/moead_media)
b5 é o 1º config offline-**Python**. `emit_sonda_block` faz `int(geracao)` (não aceita
None), mas `auditar` exige geracao=NULL na sonda offline. Resolvi carimbando geracao=None
em `buf.surr_rows[-S:]` pós-`emit_sonda_block` (precedente `c149._stamp_c3_sonda`). É local
e não toca o harness. **A torre pode preferir** um fix central em `emit_sonda_block`
(aceitar geracao=None) para c311/moead_media não repetirem o carimbo.

### A.4 — ④ = 1 linha (imposto pela caixa-preta)
Segui o cartão (④ = 1 linha por config). Nota para a torre: o motor desdeo é **caixa-preta**
— `evolver.iterate()` roda 10 gerações internas sem gancho por geração, então
`tempo_busca_s` POR GERAÇÃO é **inmensurável** (ao contrário do `run_stubr3`, que faz ④
por-geração porque é dono do laço). O ⑥ (jsonl) tem 1 evento `b5_gen` por geração (DI-10),
com `tempo_busca_s=NULL` por-gen (exceção offline declarada no `sigma_dict`).

### A.5 — Literais de naming (landam em artefato auditado)
`modelo_flag` = `"b5r/ProbRVEA-v3+GPR"` / `"b5m/ProbMOEAD-PBI+GPR"`. O `sigma_dict` (DEF-C4)
declara ② vazia, os NULLs offline, σ=desvio GPR, a rampa θ, o overshoot ≤1, o pin, os
patches e o shim. Se a torre quiser outra convenção de nomes, é trivial trocar.

### A.6 — Patch b5r muda o CONTEÚDO da ③ (survivors, não prole)
O mini-patch DI-16.16 faz a ③ de b5r gravar os SOBREVIVENTES pós-seleção (não a prole).
Isso é o que torna a ⑦ reconstituível da ③ (o `final_eval --check` confirma). A torre deve
estar ciente de que a ③ de b5r ≠ "todos os filhos avaliados" — é "a população mantida por
geração". (b5m já era assim por construção do seu `_next_gen`.)

### A.7 — pyDOE 0.9.1 quebra o determinismo da pop inicial (fix runner-local; fidelidade)
⚠ **Achado forte na validação.** O `pyDOE 0.9.1` mudou a API: `lhs(n, samples)` SEM
`random_state`/`seed` cria um `np.random.default_rng()` FRESCO (semeado da entropia do SO)
— **ignora `np.random.seed`**. O `create_new_individuals` vendorizado chama exatamente
assim, então a população inicial do motor era **não-reprodutível** (o determinismo divergia
já na geração 1). Fix runner-local: injeto o `RandomState` GLOBAL semeado no `lhs` do
`create_new_individuals` — replica o pyDOE CLÁSSICO (que usava `np.random.rand`, o global),
logo é **fiel à intenção do desdeo** e agora determinístico (gate 5 VERDE). **A torre deve:**
(a) ratificar que a LHS-via-global-semeado é a semântica desejada (é a única com
reprodutibilidade); (b) propagar o fix a c311/moead_media (mesmo `create_new_individuals`);
(c) rodar b5 SEMPRE com `PYTHONHASHSEED=0` (o `run_in_venv` já seta — a iteração de set do
desdeo depende disso). Também corrigi um bug MEU: passava `nd_pos_real` ao `write_final` no
float64; o correto é OMITIR (ele calcula no float32 que a ⑦ persiste) — senão empates
próximos reprovam o `--check` (medido em b5m/ZDT1).

## B. Notas POR-MODO (o coração da fidelidade — para o autor validar)
- **mode 7 — b5r (`ProbRVEA_v3` → `Prob_APD_select_v3`):** APD probabilístico por
  **APROXIMAÇÃO MÉDIA-MC** (o `_v3` "superfast considering mean APD"). É uma **aproximação
  DECLARADA**, não o Prob-APD publicado exato. O autor deve decidir se essa é a variante do
  estudo (o repo também traz `Prob_APD_select_v1` = "original", mais fiel e mais lento).
- **mode 72 — b5m (`ProbMOEAD` → `ProbMOEAD_select`):** comparação **MC pareada**
  (`compute_probability_wrong_MC`, substitui vizinhos com P_wrong>0.5). **Quase-fiel** ao
  paper. O bloco KDE (`compute_pdf`/`plt_density`) era MORTO (a decisão nunca usava o pdf) e
  crashy (`plt_density` sob `usetex`, `reshape(20,…)`) — removido (patch b5-mode72-kde).
  SF_type default = **PBI**, n_neighbors=20 (o `reshape(20,…)` do KDE morto assumia isso).

## C. O que NÃO mexi (respeitado)
SPEC/bundles/CONTRATO/REGISTRO = da torre (não editados). `_baseline_pre_retrofit/**`
intacto. `doe.py` compartilhado NÃO editado. Arquivos da sessão c311 (src/c311_tgprmo.py,
tests/test_c311.py, off/c311) IGNORADOS. Nunca `git push`, nunca `git add -A`.
