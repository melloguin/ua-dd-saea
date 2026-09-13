# ESTOQUE40 — dataframe de vendas (fonte legível do problema)

`ESTOQUE40_vendas.xlsx` — a matriz de demanda que a função objetivo usa: **40 SKUs × 106 semanas**
(2009-11-30 a 2011-12-05), mais a aba `constantes` com price, hold, categoria, estoque atual e
limite superior por SKU.

**Estatuto.** É o artefato **derivado**, extraído de `data/estoque_problem.npz` — não é a base bruta
de transações (`online_retail_II.xlsx`, ~45,6 MB, UCI DOI 10.24432/C5CG6D), que não integra este
repositório. Serve para leitura humana e para as figuras da dissertação.

**Conferência executada em 16/08/2026** (contra `data/estoque_problem.npz`):
matriz 40×106 idêntica (erro absoluto máximo **0,0**) · `price`, `hold`, `category`,
`current_stock` e `xu` conferem em todas as 40 linhas.

- sha256 deste arquivo: `b68d46def8a4e6cff2c5c193ac2952fe9f39fbca228e7949d3cda53d15b5935b`
- sha256 do `.npz` de origem: `660b589611c2512ee1e02978dd4edd0f42f5db1cd0f0ba01a2ade67844e9ccc0`
- sha256 da base bruta (pré-registrado em `estoque_config.json`, para prova de identidade se ela
  for rebaixada): `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`

**Regra do preço** (cabeçalho da aba `constantes`): `price (preco mediano observado)` — a mediana
dos preços unitários praticados nas transações daquele SKU.

---

## ⚖️ Adendo (16/08/2026) — a base BRUTA foi recuperada e verificada

`online_retail_II.xlsx` (43,5 MB · 1.067.371 linhas em 2 abas) foi baixado do repositório público
da UCI (`archive.ics.uci.edu/static/public/502/online+retail+ii.zip`, DOI 10.24432/C5CG6D) em
16/08/2026 e conferido:

> **sha256 = `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`** — idêntico, dígito
> a dígito, ao `raw_sha256` pré-registrado em `data/estoque_config.json` antes de qualquer
> resultado.

A cadeia de proveniência do ESTOQUE40 fica assim fechada de ponta a ponta: **base bruta (hash
pré-registrado, agora conferido) → datamart congelado (`estoque_problem.npz`) → planilha legível
(`ESTOQUE40_vendas.xlsx`, conferida contra o `.npz` com erro 0,0)**.

⚠️ **Peso:** 43,5 MB. O arquivo **não está coberto pelo `.gitignore`** — avaliar antes de commitar
(a alternativa é mantê-lo local e confiar no hash pré-registrado, que é o que o config já faz).

**Colunas da base bruta** (conferidas no arquivo): `Invoice · StockCode · Description · Quantity ·
InvoiceDate · Price · Customer ID · Country`.
