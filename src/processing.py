import numpy as np

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
    
    Algoritmo de varredura otimizado (Sweep Algorithm) - O(n log n):
    1. Ordenar pontos por fitness1 (decrescente) e fitness2 (decrescente)
    2. Percorrer os pontos mantendo o máximo de fitness2 visto
    3. Um ponto está na fronteira se seu fitness2 >= máximo visto
    
    Por que funciona:
    - Ao ordenar por fitness1 decrescente, garantimos que nenhum ponto à direita
      pode dominar um ponto à esquerda pelo critério fitness1
    - Então, basta verificar se existe um ponto anterior com fitness2 maior
    - Se fitness2 do ponto atual >= max_fitness2, ele não é dominado
    
    Args:
        df: DataFrame com colunas ['registro', 'fitness1', 'fitness2']
        
    Returns:
        DataFrame contendo apenas os pontos da fronteira de Pareto
    """
    print("Encontrando fronteira de Pareto (algoritmo otimizado)...")
    print(f"Total de pontos no espaço de busca: {len(df):,}")
    
    # Criar cópia e ordenar por fitness1 (decrescente), depois fitness2 (decrescente)
    # Isso garante que pontos com mesmo fitness1 sejam ordenados por fitness2
    df_sorted = df.sort_values(by=['fitness1', 'fitness2'], 
                                ascending=[False, False]).reset_index(drop=False)
    
    # Lista para armazenar índices dos pontos não-dominados
    pareto_indices = []
    
    # Máximo de fitness2 visto até agora
    max_fitness2 = float('-inf')
    
    # Percorrer pontos ordenados
    for idx, row in df_sorted.iterrows():
        current_fitness1 = row['fitness1']
        current_fitness2 = row['fitness2']
        
        # Como ordenamos por fitness1 decrescente, todos os pontos anteriores
        # têm fitness1 >= current_fitness1
        # 
        # Para o ponto atual não ser dominado, ele precisa ter:
        # fitness2 >= max_fitness2 (máximo fitness2 dos pontos com fitness1 >= atual)
        #
        # Se fitness2 < max_fitness2, então existe um ponto anterior com:
        # - fitness1 >= current_fitness1 (garantido pela ordenação)
        # - fitness2 > current_fitness2 (pois max_fitness2 > current_fitness2)
        # Logo, o ponto atual é dominado
        
        if current_fitness2 >= max_fitness2:
#            print(f'ponto_adicionado_front: f1 = {current_fitness1}, f2 = {current_fitness2}')
            # Ponto não é dominado - adicionar à fronteira
            pareto_indices.append(row['index'])
            # Atualizar o máximo de fitness2
            max_fitness2 = current_fitness2
    
    # Extrair os pontos da fronteira de Pareto usando os índices originais
    pareto_front = df.loc[pareto_indices].copy()
    
    # Ordenar a fronteira por fitness1 para melhor visualização
    pareto_front = pareto_front.sort_values(by='fitness1', ascending=False)
    
    print(f"✅ Fronteira de Pareto encontrada!")
    print(f"Fronteira de Pareto contém {len(pareto_front):,} pontos.")
    print(f"Isso representa {100 * len(pareto_front) / len(df):.4f}% do espaço de busca.")
    
    return pareto_front