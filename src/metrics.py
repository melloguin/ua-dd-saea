import numpy as np
from scipy.spatial.distance import cdist


def calculate_gamma_convergence_metric(df_main, pareto_real, pareto_surrogate):
    """
    Calcula a métrica de convergência Gamma entre o front de Pareto encontrado
    e o front de Pareto verdadeiro.
    
    A métrica Gamma mede a qualidade da convergência do conjunto de soluções 
    encontrado pelo algoritmo. Valores menores indicam melhor convergência.
    
    Parâmetros:
    -----------
    df_main : pd.DataFrame
        DataFrame principal contendo os valores VERDADEIROS de fitness1 e fitness2
        para todos os registros (incluindo coluna 'registro')
    pareto_real : pd.DataFrame
        DataFrame com o front de Pareto verdadeiro (deve conter coluna 'registro')
    pareto_surrogate : pd.DataFrame
        DataFrame com o front de Pareto encontrado pelo algoritmo (deve conter coluna 'registro')
    
    Retorna:
    --------
    dict : Dicionário contendo:
        - 'gamma_mean': Média das distâncias mínimas (métrica gamma)
        - 'gamma_std': Desvio padrão das distâncias mínimas
        - 'min_distances': Array com todas as distâncias mínimas individuais
        - 'n_real': Número de pontos no front verdadeiro
        - 'n_surrogate': Número de pontos no front encontrado
    
    Interpretação:
    --------------
    - Valores menores de gamma_mean indicam melhor convergência
    - gamma_mean = 0 indica que todas as soluções encontradas estão exatamente no front real
    - gamma_std mede a dispersão das soluções (diversidade fraca)
    """
    
    # Obter os valores VERDADEIROS de fitness para o front real
    pareto_real_values = pareto_real.merge(
        df_main[['registro', 'fitness1', 'fitness2']], 
        on='registro', 
        how='left',
        suffixes=('', '_real')
    )
    
    # Obter os valores VERDADEIROS de fitness para o front encontrado
    pareto_surrogate_values = pareto_surrogate.merge(
        df_main[['registro', 'fitness1', 'fitness2']], 
        on='registro', 
        how='left',
        suffixes=('', '_real')
    )
    
    # Extrair as coordenadas (fitness1, fitness2) VERDADEIRAS
    real_points = pareto_real_values[['fitness1', 'fitness2']].values
    surrogate_points = pareto_surrogate_values[['fitness1', 'fitness2']].values
    
    # Calcular a matriz de distâncias euclidianas
    # Cada linha i contém as distâncias do ponto i do front encontrado
    # para todos os pontos do front verdadeiro
    distances_matrix = cdist(surrogate_points, real_points, metric='euclidean')
    
    # Para cada ponto do front encontrado, pegar a distância mínima ao front real
    min_distances = np.min(distances_matrix, axis=1)
    
    # Calcular a métrica gamma (média das distâncias mínimas)
    gamma_mean = np.mean(min_distances)
    
    # Calcular o desvio padrão (medida de diversidade)
    gamma_std = np.std(min_distances)
    
    # Retornar resultados
    results = {
        'gamma_mean': gamma_mean,
        'gamma_std': gamma_std,
        'min_distances': min_distances,
        'n_real': len(real_points),
        'n_surrogate': len(surrogate_points)
    }
    
    return results


def print_gamma_metric(results):
    """
    Imprime os resultados da métrica gamma de forma formatada.
    
    Parâmetros:
    -----------
    results : dict
        Dicionário retornado pela função calculate_gamma_convergence_metric
    """
    print(f"🎯 Métrica de Convergência:")
    print(f"   • Gamma (γ) - Média:        {results['gamma_mean']:.6f}")
    print(f"   • Desvio Padrão:            {results['gamma_std']:.6f}")


def calculate_fitness_sum_statistics(df_main, pareto_front):
    """
    Calcula a média e o desvio padrão dos valores de (fitness1 + fitness2)
    das soluções encontradas no front de Pareto.
    
    Parâmetros:
    -----------
    df_main : pd.DataFrame
        DataFrame principal contendo os valores VERDADEIROS de fitness1 e fitness2
        para todos os registros (incluindo coluna 'registro')
    pareto_front : pd.DataFrame
        DataFrame com o front de Pareto (deve conter coluna 'registro')
    
    Retorna:
    --------
    dict : Dicionário contendo:
        - 'fitness_sum_mean': Média de (fitness1 + fitness2)
        - 'fitness_sum_std': Desvio padrão de (fitness1 + fitness2)
        - 'fitness_sum_values': Array com todos os valores de (fitness1 + fitness2)
        - 'n_solutions': Número de soluções no front
    """
    
    # Obter os valores VERDADEIROS de fitness para o front
    pareto_values = pareto_front.merge(
        df_main[['registro', 'fitness1', 'fitness2']], 
        on='registro', 
        how='left',
        suffixes=('', '_real')
    )
    
    # Calcular fitness1 + fitness2 para cada solução
    fitness_sum = pareto_values['fitness1'] + pareto_values['fitness2']
    
    # Calcular estatísticas
    fitness_sum_mean = np.mean(fitness_sum)
    fitness_sum_std = np.std(fitness_sum)
    
    # Retornar resultados
    results = {
        'fitness_sum_mean': fitness_sum_mean,
        'fitness_sum_std': fitness_sum_std,
        'fitness_sum_values': fitness_sum.values,
        'n_solutions': len(fitness_sum)
    }
    
    return results


def print_fitness_sum_statistics(results):
    """
    Imprime os resultados das estatísticas de soma de fitness de forma formatada.
    
    Parâmetros:
    -----------
    results : dict
        Dicionário retornado pela função calculate_fitness_sum_statistics
    """
    print(f"📊 Estatísticas de (Fitness1 + Fitness2):")
    print(f"   • Média:                    {results['fitness_sum_mean']:.6f}")
    print(f"   • Desvio Padrão:            {results['fitness_sum_std']:.6f}")
    print(f"   • Número de Soluções:       {results['n_solutions']}")


def calculate_delta_diversity_metric(df_main, pareto_real, pareto_found):
    """
    Calcula a métrica de diversidade Delta (Δ) que mede a uniformidade
    do espaçamento das soluções ao longo do front de Pareto.
    
    A métrica Delta mede quão uniformemente distribuídas estão as soluções
    encontradas ao longo do front de Pareto. Valores menores indicam melhor
    diversidade (distribuição mais uniforme).
    
    Parâmetros:
    -----------
    df_main : pd.DataFrame
        DataFrame principal contendo os valores VERDADEIROS de fitness1 e fitness2
        para todos os registros (incluindo coluna 'registro')
    pareto_real : pd.DataFrame
        DataFrame com o front de Pareto verdadeiro (usado para identificar extremos)
    pareto_found : pd.DataFrame
        DataFrame com o front de Pareto encontrado pelo algoritmo
    
    Retorna:
    --------
    dict : Dicionário contendo:
        - 'delta': Valor da métrica Delta
        - 'd_f': Distância entre extremo e primeira solução
        - 'd_l': Distância entre extremo e última solução
        - 'd_mean': Média das distâncias consecutivas
        - 'consecutive_distances': Array com distâncias consecutivas
        - 'n_solutions': Número de soluções no front encontrado
    
    Interpretação:
    --------------
    - Valor ideal: 0 (distribuição perfeitamente uniforme)
    - Valores maiores indicam pior diversidade
    - Pode ser maior que 1 para distribuições muito irregulares
    """
    
    # Obter os valores VERDADEIROS de fitness para o front real
    pareto_real_values = pareto_real.merge(
        df_main[['registro', 'fitness1', 'fitness2']], 
        on='registro', 
        how='left',
        suffixes=('', '_real')
    )
    
    # Obter os valores VERDADEIROS de fitness para o front encontrado
    pareto_found_values = pareto_found.merge(
        df_main[['registro', 'fitness1', 'fitness2']], 
        on='registro', 
        how='left',
        suffixes=('', '_real')
    )
    
    # Extrair as coordenadas (fitness1, fitness2) VERDADEIRAS
    real_points = pareto_real_values[['fitness1', 'fitness2']].values
    found_points = pareto_found_values[['fitness1', 'fitness2']].values
    
    # Ordenar os pontos encontrados por fitness1 (para ter ordem consistente)
    sorted_indices = np.argsort(found_points[:, 0])
    found_points_sorted = found_points[sorted_indices]
    
    N = len(found_points_sorted)
    
    # Se há menos de 2 pontos, não é possível calcular Delta
    if N < 2:
        return {
            'delta': np.nan,
            'd_f': np.nan,
            'd_l': np.nan,
            'd_mean': np.nan,
            'consecutive_distances': np.array([]),
            'n_solutions': N
        }
    
    # Calcular distâncias consecutivas (d_i)
    consecutive_distances = []
    for i in range(N - 1):
        dist = np.linalg.norm(found_points_sorted[i + 1] - found_points_sorted[i])
        consecutive_distances.append(dist)
    consecutive_distances = np.array(consecutive_distances)
    
    # Calcular média das distâncias consecutivas (d̄)
    d_mean = np.mean(consecutive_distances)
    
    # Identificar soluções extremas do front real
    # Extremo 1: solução que maximiza fitness1 no front real
    # Extremo 2: solução que maximiza fitness2 no front real
    idx_max_f1 = np.argmax(real_points[:, 0])
    idx_max_f2 = np.argmax(real_points[:, 1])
    extreme_1 = real_points[idx_max_f1]  # Extremo que favorece fitness1
    extreme_2 = real_points[idx_max_f2]  # Extremo que favorece fitness2
    
    # Calcular d_f: distância do extremo 1 até a primeira solução do conjunto encontrado
    d_f = np.linalg.norm(extreme_1 - found_points_sorted[0])
    
    # Calcular d_l: distância do extremo 2 até a última solução do conjunto encontrado
    d_l = np.linalg.norm(extreme_2 - found_points_sorted[-1])
    
    # Calcular o numerador: d_f + d_l + Σ|d_i - d̄|
    numerator = d_f + d_l + np.sum(np.abs(consecutive_distances - d_mean))
    
    # Calcular o denominador: d_f + d_l + (N-1)×d̄
    denominator = d_f + d_l + (N - 1) * d_mean
    
    # Calcular Delta
    if denominator > 0:
        delta = numerator / denominator
    else:
        delta = np.nan
    
    # Retornar resultados
    results = {
        'delta': delta,
        'd_f': d_f,
        'd_l': d_l,
        'd_mean': d_mean,
        'consecutive_distances': consecutive_distances,
        'n_solutions': N
    }
    
    return results


def print_delta_metric(results):
    """
    Imprime os resultados da métrica Delta de forma formatada.
    
    Parâmetros:
    -----------
    results : dict
        Dicionário retornado pela função calculate_delta_diversity_metric
    """
    print(f"🌈 Métrica de Diversidade:")
    print(f"   • Delta (Δ):                {results['delta']:.6f}")
    print(f"   • d_f (dist. extremo 1):    {results['d_f']:.6f}")
    print(f"   • d_l (dist. extremo 2):    {results['d_l']:.6f}")
    print(f"   • d̄ (média dist. consec.):  {results['d_mean']:.6f}")
    print(f"   • Número de Soluções:       {results['n_solutions']}")

