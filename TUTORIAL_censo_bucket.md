# TUTORIAL — rodar o censo do bucket a partir de uma instância Claude Code

**Data:** 2026-07-28 · **Bucket:** `gs://mestrado_experiments` · **Projeto:** `skilled-text-480300-d9`
**Script:** `scripts/censo_bucket.py` (v2 — só CLI do gcloud, sem SDK Python)

---

## 0. Leia isto antes de rodar qualquer comando

> ### 🔴 O bucket é a única cópia completa da campanha.
> As quatro máquinas (`v5-mestrado`, `mestrado-v6`, `matlab-vm3`, `vm3-resgate`) estão **TERMINATED**. Os discos existem mas não estão montados em lugar nenhum, e o Mac tem só a fatia dele. **Um comando destrutivo no bucket não tem desfazer.**

**Permitido no bucket — só leitura:**

| comando | uso |
|---|---|
| `gcloud storage ls` | listar |
| `gcloud storage cat` | ler um objeto |
| `gcloud storage cp gs://... <destino-local>` | baixar |

**Proibido, sem exceção:**

- `gcloud storage cp <local> gs://...` — escrever no bucket
- `gcloud storage rsync` em qualquer direção (ele sobrescreve, e com `--delete-unmatched-destination-objects` apaga)
- `gcloud storage rm` / `mv` — nunca, em nenhuma circunstância
- `gcloud compute instances delete` — em especial na `matlab-vm3`, cuja licença do MATLAB está ancorada ao MAC `42:01:0a:80:00:05`

**Outras regras do projeto que atravessam qualquer sessão:**

- **Nunca `git push`. Nunca `git add -A`.** Push e tag são ação exclusiva do autor.
- **Nunca instalar ou atualizar nada** (pip, apt, componentes do gcloud) sem autorização explícita. O censo v2 existe justamente para não precisar instalar o SDK.
- **Nunca escrever em `data/experiments/_baseline_pre_retrofit/`.**
- **Diagnóstico de credencial nunca imprime token.**
- Ambiguidade ⇒ pare e pergunte.

O censo é **read-only por construção**: ele faz um `ls` e um `cp` do bucket para um diretório temporário local, e escreve um único CSV em `~`. Não toca no repo.

---

## 1. Pré-requisitos

| item | como conferir |
|---|---|
| `gcloud` no PATH | `gcloud version` |
| conta autenticada com acesso ao bucket | `gcloud auth list` |
| `python3` ≥ 3.8 (só stdlib) | `python3 -V` |
| repo `ua-dd-saea` local | precisa de `claude_code_context/artifacts/runs_matrix.csv` e `characteristics.csv` |

### ⚠ A armadilha nº 1: conta errada dá 403 que parece falta de permissão

O Mac tem **duas contas** autenticadas:

| conta | projeto | o que ela vê |
|---|---|---|
| `gdmello.nunes@gmail.com` | `skilled-text-480300-d9` | **o bucket** e a `v5-mestrado` |
| `invest.gdmn@gmail.com` | `project-2aa33d8c-94a7-488b-89e` | `mestrado-v6`, `matlab-vm3`, `vm3-resgate` |

Se a conta ativa for a `invest.gdmn`, o bucket responde:

```
HTTPError 403: invest.gdmn@gmail.com does not have storage.objects.get access
```

**Não é falta de permissão — é conta errada.** Não peça acesso ao administrador, não mude IAM. Passe a conta certa:

```
GCS_ACCOUNT=gdmello.nunes@gmail.com
```

O script já detecta esse 403 e imprime a dica.

---

## 2. Teste de fumaça — 10 segundos, antes de tudo

```bash
gcloud auth list --format="value(account,status)"
gcloud storage ls gs://mestrado_experiments/ --account=gdmello.nunes@gmail.com --project=skilled-text-480300-d9
```

Deve listar cinco prefixos:

```
gs://mestrado_experiments/_censo/
gs://mestrado_experiments/_logs_lotes/
gs://mestrado_experiments/_logs_teto48h/
gs://mestrado_experiments/_snapshot_pre_teto48h/
gs://mestrado_experiments/experiments/
```

Se listou, a autenticação está resolvida e o resto vai funcionar.

---

## 3. Rodar o censo

```bash
cd ~/Documents/python_repos/mestrado/ua-dd-saea

GCS_ACCOUNT=gdmello.nunes@gmail.com \
GCS_PROJECT=skilled-text-480300-d9 \
GCS_BUCKET=mestrado_experiments \
SEMENTE=42 \
REPO_DIR="$(pwd)" \
python3 scripts/censo_bucket.py
```

Leva de 1 a 3 minutos: uma listagem de ~4.954 objetos e um download em lote de ~670 manifestos (só JSON pequeno — **nenhum parquet é baixado**, por isso é rápido).

Para inspecionar os manifestos depois sem baixar de novo, fixe o cache:

```bash
CENSO_CACHE=/tmp/censo42 ... python3 scripts/censo_bucket.py
```

---

## 4. O que a saída deve dizer

Referência do fechamento de 28/07/2026 — **se divergir, algo mudou e vale investigar antes de seguir**:

```
 celulas da grade: 695 · objetos no bucket: ~4954

por familia          OK  INCOMPL  ABORT  FALHOU  S/MANIF  ILEGIV  RETIR  S/BUCKET
main                406        .     15       3        1       .      .         .
off                 125        .      .       .        .       .      .         .
sweep               120        .      .       .        .       .      .         .
batch                15        .      5       .        .       .      5         .
TOTAL               666        .     20       3        1       .      5         .
```

**666 OK de 695 = 95,8%** (96,5% descontando as 5 retiradas por desenho).

Taxonomia:

| estado | significado | é problema? |
|---|---|---|
| `OK` | `status ∈ {ok, retried_ok}` e todas as camadas do gabarito | não |
| `INCOMPL` | `status=ok` mas faltando camada vs. o gabarito modal do `(exp,alg)` | investigar |
| `ABORT` | `motivo_parada ∈ {teto_wall, cache_cap}` | **não** — aborto sancionado, DI-38(a) |
| `FALHOU` | manifesto presente, status não-ok, motivo fora do conjunto sancionado | sim |
| `S/MANIF` | há artefato no bucket mas não a camada ⑤ | sim, mas veja §6 |
| `RETIR` | `batch/c154` — fora do roster por DI-40 | não |
| `S/BUCKET` | nenhuma camada no bucket | sim — **deveria ser 0** |

As 7 camadas: ① `__real.parquet` ② `__pop.parquet` ③ `__surrogate.parquet` ④ `__timing.parquet` ⑤ `.manifest.json` ⑥ `.jsonl` ⑦ `__final.parquet` (só offline). A coluna `camadas` traz os dígitos presentes — `123456` é uma célula online completa.

**As 29 não-OK esperadas** (detalhe em `INVENTARIO_nao_go_semente42.md`): 5 `batch/c154` retiradas pela DI-40 · 20 abortos por projeção (12 `main/c154` com D≥12, 3 `main/c262`, 5 `batch/c262`) · 3 falhas reais (`main/c154/ZDT6`, `main/c154/BBOB_F55`, `main/c262/WFG1`) · 1 sem manifesto (`main/b1/DTLZ4`).

---

## 5. O CSV

Sai em `~/censo_bucket_42.csv`, uma linha por célula:

```
maquina_roster, exp, alg, problema, D, semente, estado, camadas, fe_final_maxfe, detalhe
```

Vale arquivar no bucket como registro de fechamento — **mas isso é escrita, então só com autorização explícita do autor**:

```bash
gcloud storage cp ~/censo_bucket_42.csv gs://mestrado_experiments/_censo/censo_bucket_42_FINAL.csv --account=gdmello.nunes@gmail.com --project=skilled-text-480300-d9
```

Consultas típicas:

```bash
python3 - <<'PY'
import csv, collections
L = list(csv.DictReader(open("censo_bucket_42.csv", encoding="utf-8")))
nok = [r for r in L if r["estado"] != "OK"]
print("nao-OK: %d de %d\n" % (len(nok), len(L)))
por = collections.defaultdict(list)
for r in nok: por[r["estado"]].append(r)
for est in sorted(por):
    print("=== %s (%d) ===" % (est, len(por[est])))
    for r in sorted(por[est], key=lambda x: (x["exp"], x["alg"], x["problema"])):
        print("  %-22s %-12s D=%-3s camadas=%-8s fe=%-12s %s"
              % ("%s/%s" % (r["exp"], r["alg"]), r["problema"], r["D"],
                 r["camadas"] or "-", r["fe_final_maxfe"], r["detalhe"][:70]))
    print()
PY
```

### ⚠ A armadilha nº 2: `maquina_roster` é o dono PLANEJADO, não onde rodou

Quando a `matlab-vm3` teve problemas de disco e capacidade zonal (O-19), parte do stack MATLAB foi recuperada **no Mac** (macOS/arm64) em vez da vm3 (Linux/Intel): **`main/e7` inteiro**, parte de **`main/c238`** e de **`main/b1`**. O censo continua rotulando essas células como `vm3`.

A atribuição **real** está em `gs://mestrado_experiments/_logs_lotes/mac/*done.txt`. Isso não afeta os indicadores (IGD+, HV, spacing são determinísticos dado o resultado) — afeta o endpoint de **tempo** do M7.

---

## 6. Diagnosticar `S/MANIF` — o `.jsonl` é que manda

O stack **MATLAB certifica a própria falha no *footer* do `.jsonl`**, não no `.manifest.json` (achado O-21). Uma auditoria que só olhe a camada ⑤ classifica isso como `SEM-MANIFESTO` e perde o diagnóstico.

```bash
gcloud storage cat gs://mestrado_experiments/experiments/main/b1/exp_main_b1_DTLZ4_42.jsonl --account=gdmello.nunes@gmail.com --project=skilled-text-480300-d9 | tail -2
```

E o discriminador (achado O-22) é limpo:

| evidência no `.jsonl` | interpretação |
|---|---|
| footer presente, `status=failed`, campo `erro` preenchido | **falha algorítmica real** |
| **sem footer**, arquivo simplesmente para | **morte de processo** — extinto antes de escrever |

Uma ressalva de contexto: **8 células foram encerradas por decisão do operador em 28/07** (3 de `main/c154` em DTLZ2/3/4 e 5 de `c262`) para liberar as VMs. O `.jsonl` delas fica truncado sem footer — que é a assinatura de morte de processo. **Não é incidente de infraestrutura.**

---

## 7. Se der errado

| sintoma | causa | conserto |
|---|---|---|
| `HTTPError 403 ... does not have storage.objects.get` | conta ativa errada | `GCS_ACCOUNT=gdmello.nunes@gmail.com` |
| `FATAL: repo nao encontrado` | não achou `.git` | `REPO_DIR=/caminho/do/ua-dd-saea` |
| `FATAL: gcloud nao esta no PATH` | SDK ausente | instalar o Google Cloud SDK — **peça autorização** |
| `FATAL: semente N nao existe` | semente fora do conjunto | sancionadas: `0..28` e `42`. **A 30 não existe** |
| `S/BUCKET` > 0 | célula sem nenhuma camada no bucket | provavelmente ficou em disco de máquina; o `mirror_run` **só espelha no fim de run bem-sucedido** |
| censo lento (> 5 min) | baixando manifestos um a um | o `cp` em lote caiu no fallback; confira a versão do gcloud |

---

## 8. Briefing pronto para colar no Claude Code

```
Contexto: campanha experimental da dissertação `ua-dd-saea` (PPGCC/UFMG). Os
resultados da semente 42 estão em gs://mestrado_experiments, projeto
skilled-text-480300-d9. As 4 VMs da campanha estão TERMINATED — o bucket é a
única cópia completa.

REGRAS DURAS:
- O bucket é READ-ONLY para você. Permitido: `gcloud storage ls`,
  `gcloud storage cat`, `gcloud storage cp gs://... <local>`. PROIBIDO:
  escrever no bucket, `gcloud storage rsync`, `rm`, `mv`. Não tem desfazer.
- Nunca `git push`, nunca `git add -A`.
- Nunca instalar/atualizar nada sem me perguntar.
- Nunca imprimir token ou credencial.
- Ambiguidade ⇒ pare e pergunte.

Tarefa: rodar o censo do bucket e me reportar o resultado.

1. Confira a auth:
   gcloud auth list --format="value(account,status)"
   gcloud storage ls gs://mestrado_experiments/ --account=gdmello.nunes@gmail.com --project=skilled-text-480300-d9
   Se der 403, é CONTA ERRADA, não falta de permissão — use
   --account=gdmello.nunes@gmail.com. Não mexa em IAM.

2. Rode, da raiz do repo:
   GCS_ACCOUNT=gdmello.nunes@gmail.com GCS_PROJECT=skilled-text-480300-d9 \
   SEMENTE=42 REPO_DIR="$(pwd)" python3 scripts/censo_bucket.py

3. O esperado é 666 OK de 695 (main 406/425, off 125/125, sweep 120/120,
   batch 15/25). Se divergir, PARE e me diga o que mudou antes de seguir.

4. Me reporte: a tabela por família, a tabela por config, e as listas de
   FALHOU / SEM-MANIFESTO / S/BUCKET. `ABORT` e `RETIR` são estados
   SANCIONADOS (DI-38a e DI-40) — não são falha, não alarme sobre eles.

Referência: TUTORIAL_censo_bucket.md, INVENTARIO_nao_go_semente42.md e
FECHAMENTO_semente42.md, na raiz do repo.
```
