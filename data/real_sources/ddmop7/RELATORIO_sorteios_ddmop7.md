# Sorteios oficiais do DDMOP7 — relatório de congelamento

Gerado por `derivar_doe_e_dataset_ddmop7.py` a partir de `sorteios_ddmop7_120.csv`.

| artefato | decisão | forma | sha256 |
|---|---|---|---|
| `doe_ddmop7_online_30sementes.csv` | D88.1 | 30 × 186 | `9fc4268d7c6b84e8fe8f5856b751f921c7caf2b677872708b545a64cd3832149` |
| `dataset_ddmop7_offline_30sementes.csv` | D88.9 | 30 × 526 | `03056b6eb76a5c40362547cdc0c31869e70a11088efefefde1c46317fb2ea085` |

## Checagens

- OK 120 sorteios presentes (achei 120)
- OK numeracao contigua 1..120 sem buraco
- OK mapa sorteio->uso/semente bate com o D88.2 (ordem de geracao)
- OK todo sorteio tem 186 x 17
- OK os 120 sorteios sao todos distintos
- OK online e offline disjuntos ponto-a-ponto (intersecao = 0)
- OK todo ponto tem ao menos um zero exato (1.0000)
- fracao global de zeros = 0.5003 (medido no .p: 0.494)
- fracao de zeros por coluna: min 0.498 / max 0.502 (medido: 0.435-0.538)
- KS nao-nulos ~ U[-1,1]: p = 0.9154
- nz por ponto: media 8.505 var 4.311 | Binomial(17,0.500): media 8.505 var 4.250
- OK  DoE      = 11D-1 = 186
- OK  dataset  = 31D-1 = 526
- OK  30 sementes nos dois
- OK  ida-e-volta bit-a-bit do DoE (D63)
- OK  ida-e-volta bit-a-bit do dataset (D63)
- OK  DoE e dataset disjuntos em toda semente
