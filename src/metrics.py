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
    print("="*70)
    print("MÉTRICA DE CONVERGÊNCIA GAMMA (γ)")
    print("="*70)
    print(f"\n📊 Informações dos Fronts:")
    print(f"   • Pontos no front verdadeiro: {results['n_real']:,}")
    print(f"   • Pontos no front encontrado: {results['n_surrogate']:,}")
    
    print(f"\n🎯 Métrica de Convergência:")
    print(f"   • Gamma (γ) - Média:        {results['gamma_mean']:.6f}")
    print(f"   • Desvio Padrão:            {results['gamma_std']:.6f}")
    
    print(f"\n📈 Estatísticas das Distâncias Mínimas:")
    print(f"   • Mínima:                   {np.min(results['min_distances']):.6f}")
    print(f"   • Máxima:                   {np.max(results['min_distances']):.6f}")
    print(f"   • Mediana:                  {np.median(results['min_distances']):.6f}")
    
    print(f"\n💡 Interpretação:")
    if results['gamma_mean'] < 1.0:
        print(f"   ✅ EXCELENTE convergência (γ < 1.0)")
    elif results['gamma_mean'] < 5.0:
        print(f"   ✅ BOA convergência (1.0 ≤ γ < 5.0)")
    elif results['gamma_mean'] < 10.0:
        print(f"   ⚠️  MODERADA convergência (5.0 ≤ γ < 10.0)")
    else:
        print(f"   ❌ FRACA convergência (γ ≥ 10.0)")
    
    print(f"\n   Quanto menor o valor de γ, melhor a convergência.")
    print(f"   γ = 0 indica que todas as soluções estão exatamente no front real.")
    print("="*70)

