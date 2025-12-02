# Implementação MCMC para Geração de Amostras Sintéticas

## 📋 Visão Geral

Este documento descreve as funções MCMC (Monte Carlo Markov Chain) implementadas no arquivo `src/statistics.py` para gerar amostras sintéticas que seguem distribuições empíricas de dados.

## 🎯 Objetivo

Gerar amostras que reproduzem fielmente a distribuição de erros de predição dos surrogates, permitindo simular incerteza nas avaliações durante o processo de otimização (UA-SAEA - Uncertainty-Aware Surrogate-Assisted Evolutionary Algorithm).

## 🔧 Funções Implementadas

### 1. `gerar_amostra_mcmc()`

Gera N amostras que seguem a distribuição empírica de uma coluna específica do DataFrame.

**Algoritmo:** Metropolis-Hastings com Kernel Density Estimation (KDE)

**Parâmetros:**
- `df` (DataFrame): DataFrame contendo os dados
- `col` (str): Nome da coluna cuja distribuição será replicada
- `n_samples` (int): Número de amostras a serem geradas
- `burn_in` (int, default=1000): Iterações iniciais descartadas
- `thinning` (int, default=10): Intervalo entre amostras consecutivas
- `proposal_std` (float, optional): Desvio padrão da proposta (calculado automaticamente se None)
- `proposal_scale` (float, default=0.7): Fator de escala para calcular proposal_std
- `adaptive` (bool, default=True): Ativa ajuste automático de proposal_std
- `random_state` (int, optional): Seed para reprodutibilidade

**Retorna:**
- `np.ndarray`: Array com n_samples valores que seguem a distribuição de df[col]

**Exemplo:**
```python
amostras = gerar_amostra_mcmc(
    df=df_surrogate1,
    col='erro1_c1',
    n_samples=500,
    burn_in=1000,
    thinning=10,
    adaptive=True,
    random_state=42
)
```

### 2. `gerar_amostras_mcmc_por_regiao()`

Wrapper que aplica `gerar_amostra_mcmc()` para cada região do DataFrame separadamente.

**Parâmetros:** (mesmos da função anterior, exceto df deve ter coluna 'regiao')

**Retorna:**
- `dict`: Dicionário {regiao: np.ndarray} com amostras MCMC para cada região

**Exemplo:**
```python
amostras_por_regiao = gerar_amostras_mcmc_por_regiao(
    df=df_surrogate1,
    col='erro1_c1',
    n_samples=500,
    proposal_scale=0.7,
    adaptive=True,
    random_state=42
)
```

## 🧮 Algoritmo Metropolis-Hastings

### Como funciona:

1. **Inicialização**: Começa em um ponto (mediana dos dados)
2. **Proposta**: Propõe novo estado usando random walk Normal
3. **Aceitação/Rejeição**: 
   - Calcula razão de aceitação baseada nas densidades (via KDE)
   - Aceita com probabilidade min(1, densidade_nova/densidade_atual)
4. **Repetição**: Repete até coletar n_samples amostras

### Modo Adaptativo:

Durante o burn-in, o algoritmo ajusta automaticamente `proposal_std` a cada 100 iterações:
- **Taxa de aceitação > 50%**: Aumenta proposal_std em 20% (passos maiores)
- **Taxa de aceitação < 20%**: Diminui proposal_std em 20% (passos menores)
- **Meta**: Taxa de aceitação entre 20-50% (ideal ~35%)

## 📊 Taxa de Aceitação

- **Muito baixa (< 15%)**: Passos muito grandes, muita rejeição
  - **Solução**: Diminuir `proposal_scale`
  
- **Ideal (15-70%)**: Boa exploração do espaço
  - **Ótimo**: 20-50%
  
- **Muito alta (> 70%)**: Passos muito pequenos, exploração lenta
  - **Solução**: Aumentar `proposal_scale` ou ativar modo adaptativo

## 🎨 Uso no Projeto UA-DD-SAEA

### Workflow:

1. **Treinar surrogates** (Notebook 2)
2. **Obter erros de predição** dos surrogates
3. **Gerar amostras MCMC** das distribuições de erro por região
4. **Criar depara** região → amostras de erro
5. **Usar no NSGA-II** para simular incerteza nas avaliações

### Exemplo Completo:

```python
# 1. Gerar amostras para problema 1, fitness 1
amostras_p1_f1 = gerar_amostras_mcmc_por_regiao(
    df=df_surrogate1,
    col='erro1_c1',
    n_samples=200,
    burn_in=1000,
    thinning=10,
    proposal_scale=0.7,
    adaptive=True,
    random_state=42
)

# 2. Criar DataFrame com amostras
df_mcmc = pd.DataFrame({
    'regiao': np.repeat(
        list(amostras_p1_f1.keys()), 
        [len(v) for v in amostras_p1_f1.values()]
    ),
    'erro1_c1': np.concatenate(list(amostras_p1_f1.values()))
})

# 3. Validar qualidade (teste KS)
for regiao in amostras_p1_f1.keys():
    original = df_surrogate1[df_surrogate1['regiao'] == regiao]['erro1_c1']
    mcmc = df_mcmc[df_mcmc['regiao'] == regiao]['erro1_c1']
    ks_stat, ks_pval = stats.ks_2samp(original, mcmc)
    print(f"Região {regiao}: KS p-value = {ks_pval:.4f}")

# 4. Usar no algoritmo de otimização
def avaliar_com_incerteza(individuo, regiao):
    """Avalia indivíduo considerando incerteza do surrogate"""
    # Predição do surrogate
    pred = surrogate.predict(individuo)
    
    # Amostra erro aleatório da distribuição MCMC
    erro_sample = np.random.choice(amostras_p1_f1[regiao])
    
    # Fitness com incerteza
    fitness_com_incerteza = pred + erro_sample
    
    return fitness_com_incerteza
```

## ✅ Validação

As amostras MCMC devem ser validadas usando:

1. **Teste de Kolmogorov-Smirnov**: Verifica se distribuições são estatisticamente iguais
   - H0: distribuições são iguais
   - p-value ≥ 0.05 → Não rejeita H0 (✅ distribuições iguais)

2. **Comparação de momentos**:
   - Média
   - Desvio padrão
   - Mediana
   - Quantis (25%, 75%)

3. **Inspeção visual**:
   - Histogramas sobrepostos
   - Q-Q plots
   - Gráficos de densidade

## 📈 Desempenho

- **Tempo típico**: ~1-2 segundos por região (com 1000 burn-in + 500 amostras × 10 thinning)
- **Qualidade**: Alta fidelidade à distribuição original (KS p-value > 0.05)
- **Convergência**: Garantida assintoticamente pelo algoritmo Metropolis-Hastings

## 🔬 Referências

- Metropolis et al. (1953) - "Equation of State Calculations by Fast Computing Machines"
- Hastings (1970) - "Monte Carlo Sampling Methods Using Markov Chains"
- Gelman et al. (2013) - "Bayesian Data Analysis" (Cap. 11-12)

## 📝 Notas

- O modo adaptativo só funciona durante o burn-in (não modifica a distribuição estacionária)
- Thinning é importante para reduzir autocorrelação entre amostras consecutivas
- Burn-in garante que as amostras venham da distribuição estacionária
- KDE (Kernel Density Estimation) é usado para estimar a densidade empírica dos dados

### 2.1 Gerando Amostras via MCMC

**Algoritmo:** Metropolis-Hastings com Kernel Density Estimation (KDE)

**Características:**
- **Distribuição alvo**: KDE estimada a partir dos dados empíricos
- **Distribuição proposta**: Normal centrada no estado atual (random walk)
- **Modo adaptativo**: Ajusta automaticamente o `proposal_std` durante burn-in para taxa de aceitação ideal (~35%)
- **Burn-in**: 1000 iterações descartadas para garantir convergência
- **Thinning**: Intervalo de 10 entre amostras para reduzir autocorrelação

**Parâmetros importantes:**
- `proposal_scale`: Controla o tamanho dos passos (maior = passos maiores = menor aceitação)
- `adaptive`: Se True, ajusta `proposal_std` automaticamente durante burn-in
- Taxa de aceitação ideal: 15-70% (modo adaptativo busca ~35%)


### 2.3 Resumo da Implementação MCMC

#### ✅ O que foi implementado:

1. **Função `gerar_amostra_mcmc()`**: Gera N amostras que seguem a distribuição empírica de `df[col]`
   - Algoritmo: Metropolis-Hastings
   - Densidade alvo: Estimada via KDE (Kernel Density Estimation)
   - Proposta: Random walk com distribuição Normal

2. **Função `gerar_amostras_mcmc_por_regiao()`**: Wrapper para gerar amostras por região

3. **Modo Adaptativo**: Ajusta automaticamente `proposal_std` durante burn-in
   - Monitora taxa de aceitação a cada 100 iterações
   - Aumenta `proposal_std` em 20% se aceitação > 50%
   - Diminui `proposal_std` em 20% se aceitação < 20%
   - Busca taxa de aceitação ideal: 20-50%

#### 📊 Parâmetros principais:

- **`n_samples`**: Número de amostras finais desejadas
- **`burn_in`**: Iterações iniciais descartadas (padrão: 1000)
- **`thinning`**: Intervalo entre amostras (padrão: 10)
- **`proposal_scale`**: Escala inicial dos passos (padrão: 0.7)
- **`adaptive`**: Ativa ajuste automático (padrão: True)

#### 🎯 Resultado esperado:

As amostras MCMC geradas devem:
- Seguir a mesma distribuição dos dados originais (validado via teste KS)
- Ter momentos estatísticos similares (média, desvio padrão, quantis)
- Taxa de aceitação entre 15-70% (idealmente 20-50%)

