# Function to calculate fitness with hardcoded equations using vectorized operations
def calculate_fitness(equations1, equations2, df):
    """
    Calculate fitness based on the system of equations using vectorized operations.
    
    This function applies each equation to the entire 'registro' column at once,
    creating intermediate columns for each equation result, then sums them to get
    the final fitness1 and fitness2 values.
    
    Args:
        equations1: List of lambda functions for fitness1
        equations2: List of lambda functions for fitness2
        df: DataFrame with a 'registro' column containing the values to evaluate
        
    Returns:
        DataFrame with added columns for each equation and fitness1/fitness2
    """
    
    # Apply each equation from equations1 and create columns
    for i, equation in enumerate(equations1):
        col_name = f'eq1_{i}'
        df[col_name] = equation(df['registro'].values)
    
    # Apply each equation from equations2 and create columns
    for i, equation in enumerate(equations2):
        col_name = f'eq2_{i}'
        df[col_name] = equation(df['registro'].values)
    
    # Calculate fitness1 as sum of all eq1_* columns
    eq1_cols = [f'eq1_{i}' for i in range(len(equations1))]
    df['fitness1'] = df[eq1_cols].sum(axis=1)
    
    # Calculate fitness2 as sum of all eq2_* columns
    eq2_cols = [f'eq2_{i}' for i in range(len(equations2))]
    df['fitness2'] = df[eq2_cols].sum(axis=1)
    
    return df


# ============================================================================
# FRONTEIRA DE PARETO - Problema de Maximização Bi-Objetivo
# ============================================================================

def find_pareto_front(df):
    """
    Encontra a fronteira de Pareto para um problema de maximização bi-objetivo.
    
    Um ponto A domina um ponto B se:
    - A.fitness1 >= B.fitness1 AND A.fitness2 >= B.fitness2
    - E pelo menos uma das desigualdades é estrita (>)
    
    A fronteira de Pareto contém todos os pontos não-dominados.
    
    Algoritmo eficiente:
    1. Ordenar pontos por fitness1 (decrescente)
    2. Iterar mantendo o máximo de fitness2 visto até agora
    3. Um ponto está na fronteira se seu fitness2 > máximo visto
    
    Args:
        df: DataFrame com colunas ['registro', 'fitness1', 'fitness2']
        
    Returns:
        DataFrame contendo apenas os pontos da fronteira de Pareto
    """
    print("Encontrando fronteira de Pareto...")
    print(f"Total de pontos no espaço de busca: {len(df):,}")
    
    # Criar cópia para não modificar o dataframe original
    df_sorted = df.copy()
    
    # Ordenar por fitness1 (decrescente, pois queremos maximizar)
    # Em caso de empate em fitness1, ordenar por fitness2 (decrescente)
    df_sorted = df_sorted.sort_values(by=['fitness1', 'fitness2'], 
                                       ascending=[False, False])
    
    # Lista para armazenar índices dos pontos não-dominados
    pareto_indices = []
    
    # Máximo de fitness2 visto até agora
    max_fitness2 = float('-inf')
    
    # Iterar pelos pontos ordenados
    for idx, row in df_sorted.iterrows():
        # Se fitness2 do ponto atual é maior que o máximo visto,
        # então este ponto não é dominado
        if row['fitness2'] > max_fitness2:
            pareto_indices.append(idx)
            max_fitness2 = row['fitness2']
    
    # Extrair os pontos da fronteira de Pareto
    pareto_front = df.loc[pareto_indices].copy()
    
    # Ordenar a fronteira por fitness1 para melhor visualização
    pareto_front = pareto_front.sort_values(by='fitness1', ascending=False)
    
    print(f"✅ Fronteira de Pareto encontrada!")
    print(f"Fronteira de Pareto contém {len(pareto_front):,} pontos.")
    print(f"Isso representa {100 * len(pareto_front) / len(df):.4f}% do espaço de busca.")
    
    return pareto_front