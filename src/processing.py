import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
from src.nsga2.evaluation import genotype_to_registro


######################################################################################################################
######################################################################################################################

###########################################################
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
        col_name = f'fitness1_eq{i}'
        df[col_name] = equation(df['registro'].values)
    
    # Apply each equation from equations2 and create columns
    for i, equation in enumerate(equations2):
        col_name = f'fitness2_eq{i}'
        df[col_name] = equation(df['registro'].values)


    # Calculate fitness1 as sum of all eq1_* columns
    eq1_cols = [f'fitness1_eq{i}' for i in range(len(equations1))]
    df['fitness1'] = df[eq1_cols].sum(axis=1)
    
    # Calculate fitness2 as sum of all eq2_* columns
    eq2_cols = [f'fitness2_eq{i}' for i in range(len(equations2))]
    df['fitness2'] = df[eq2_cols].sum(axis=1)


    # Ajustes
    df['fitness_full'] = df['fitness1'] + df['fitness2']

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



###########################################################
def history_to_dataframe(history):
    """
    Transforma o histórico de populações do NSGA-II em um dataframe.
    
    Args:
        history: lista de gerações, onde cada geração contém uma lista de 
                 dicionários com 'genotype' e 'fitness'
    
    Returns:
        DataFrame com colunas: geracao, id_solucao, genotipo (registro)
    """
    dados = []
    
    for geracao, populacao in enumerate(history):
        for id_solucao, individuo in enumerate(populacao):
            # Converter genótipo para registro usando a função já existente
            registro = genotype_to_registro(individuo['genotype'])
            
            dados.append({
                'geracao': geracao,
                'id_solucao': id_solucao,
                'genotipo': registro
            })
    
    return pd.DataFrame(dados)





######################################################################################################################
######################################################################################################################


###########################################################
def criando_cenarios_amostragem(df, 
                                taxa_amostragem_global,
                                n_regioes,
                                proporcionalidade):

    # calcula fitness_full por região
    df_amostragem = df.groupby('regiao').agg({'fitness1': 'mean', 
                                              'fitness2': 'mean', 
                                              'fitness_full': 'mean', 
                                             }).reset_index()

    # cria cenários de amostragem
    df_amostragem['desvio_media'] = (df_amostragem['fitness_full'] - df_amostragem['fitness_full'].mean())/df_amostragem['fitness_full'].mean()

    df_amostragem['cenario1'] = taxa_amostragem_global
    df_amostragem['cenario2'] = (-df_amostragem['desvio_media'] * proporcionalidade * taxa_amostragem_global + taxa_amostragem_global).clip(0,1)
    df_amostragem['cenario3'] = (df_amostragem['desvio_media']  * proporcionalidade * taxa_amostragem_global + taxa_amostragem_global).clip(0,1)

    print('taxa % amostragem média')
    display(df_amostragem[['cenario1', 'cenario2', 'cenario3']].mean())


    return df_amostragem



###########################################################
def amostrar_por_regiao(df2, df_amostragem, cenario):
    """
    Amostra df2 baseado nos percentuais definidos em df_amostragem
    
    Parameters:
    -----------
    df2 : DataFrame
        DataFrame original com coluna 'regiao'
    df_amostragem : DataFrame
        DataFrame com colunas 'regiao' e 'percentual' (percentual entre 0 e 100)
    
    Returns:
    --------
    DataFrame amostrado
    """
    amostras = []
    regioes = sorted(df_amostragem['regiao'].unique())
    
    # Criar um dicionário de percentuais para acesso rápido
    percentuais_dict = df_amostragem.set_index('regiao')[cenario].to_dict()
    
    # Iterar sobre cada região
    for regiao in regioes:  # 0 a 99
        # Filtrar registros da região
        df_regiao = df2[df2['regiao'] == regiao]
        
        # Obter o percentual de amostragem
        percentual = percentuais_dict.get(regiao, 0)  # 0 se não especificado
        
        # Se percentual > 0, amostrar
        if percentual > 0 and len(df_regiao) > 0:
            # Calcular o número de amostras
            n_amostras = int(len(df_regiao) * percentual)
            # Garantir pelo menos 1 amostra se percentual > 0
            n_amostras = max(1, n_amostras)
            
            # Amostrar sem reposição (ou com reposição se n_amostras > len(df_regiao))
            if n_amostras <= len(df_regiao):
                amostra = df_regiao.sample(n=n_amostras, random_state=42)
            else:
                # Se pedir mais amostras do que existem, pegar todas
                amostra = df_regiao
            
            # coleta amostra por região
            amostras.append(amostra)
    
    # Concatenar todas as amostras
    df_amostrado = pd.concat(amostras, ignore_index=True)
    
    return df_amostrado



######################################################################################################################
######################################################################################################################

###########################################################
def treinar_catboost(df_treino, features, target, colunas_categoricas, 
                     iterations=1000, learning_rate=0.1, depth=6, 
                     verbose=1000, random_state=42, **kwargs):
    """
    Treina um modelo CatBoost Regressor
    
    Parameters:
        - df_treino (DataFrame):              DataFrame de treino
        - features (list):                    Lista com nomes das colunas de features 
        - target (str):                       Nome da coluna target
        - colunas_categoricas (list):         Lista com nomes das colunas categóricas
        - iterations (int, default=1000):     Número de iterações
        - learning_rate (float, default=0.1): Taxa de aprendizado
        - depth (int, default=6):             Profundidade das árvores 
        - verbose (int, default=100):         Frequência de impressão do log
        - random_state (int, default=42):     Seed para reprodutibilidade
        - **kwargs (dict):                    Outros parâmetros do CatBoost
    
    Returns:
        - modelo (CatBoostRegressor): Modelo treinado

    """
    # Separar features e target
    X_train = df_treino[features]
    y_train = df_treino[target]
    
    # Encontrar índices das colunas categóricas
    cat_features_indices = [features.index(col) for col in colunas_categoricas if col in features]
    
    # Inicializar o modelo
    modelo = CatBoostRegressor(
        iterations=iterations,
        learning_rate=learning_rate,
        depth=depth,
        cat_features=cat_features_indices,
        random_state=random_state,
        verbose=verbose,
        **kwargs
    )
    
    # Treinar o modelo
    print(f"Treinando CatBoost com {len(features)} features...")
    print(f"Total de observações: {len(X_train)}")
    
    modelo.fit(X_train, y_train)
    
    print(f"--- Feature importance ---")
    feature_importance = pd.DataFrame({
        'feature': features,
        'importance': modelo.feature_importances_
    }).sort_values('importance', ascending=False).head(10)
    print(feature_importance)
    
    
    return modelo



###########################################################
def prever_catboost(modelo, df_teste, features, col_name):
    """
    Faz previsões com um modelo CatBoost treinado
    
    Parameters:
        - modelo (CatBoostRegressor): Modelo CatBoost treinado
        - df_teste (DataFrame):       DataFrame de teste    
        - features (list):            Lista com nomes das colunas de features (mesma ordem do treino)
        - colunas_categoricas (list): Lista com nomes das colunas categóricas
    
    Returns:
        - df_resultado (DataFrame): DataFrame de teste com coluna de previsão adicionada  
    
    """
    # Fazer uma cópia do dataframe para não modificar o original
    df_resultado = df_teste.copy()
    
    # Separar features
    X_teste = df_resultado[features]
    
    # Fazer previsões
    previsoes = modelo.predict(X_teste)    
    df_teste[col_name] = previsoes
    
    return df_teste



######################################################################################################################
######################################################################################################################

###########################################################
def treinar_surrogate(df_cenario1, df_cenario2, df_cenario3,
                      features_surrogate, target_surrogate, colunas_categoricas):
    
    # criando dataframes para treinamento
    cols_surrogate     = [target_surrogate]+features_surrogate

    df_surrogate1 = df_cenario1[cols_surrogate].copy()
    df_surrogate2 = df_cenario2[cols_surrogate].copy()
    df_surrogate3 = df_cenario3[cols_surrogate].copy()

    # treinando surrogates
    surrogate1 = treinar_catboost(df_surrogate1, features_surrogate, target_surrogate, colunas_categoricas)
    surrogate2 = treinar_catboost(df_surrogate2, features_surrogate, target_surrogate, colunas_categoricas)
    surrogate3 = treinar_catboost(df_surrogate3, features_surrogate, target_surrogate, colunas_categoricas)

    return surrogate1, surrogate2, surrogate3


###########################################################
def prever_surrogate(df2, features_surrogate, id_objetivo,
                     surrogate1, surrogate2, surrogate3):

    # gerando previsoes
    df3 = prever_catboost(surrogate1, df2, features_surrogate, f'fitness{id_objetivo}_c1')
    df3 = prever_catboost(surrogate2, df3, features_surrogate, f'fitness{id_objetivo}_c2')
    df3 = prever_catboost(surrogate3, df3, features_surrogate, f'fitness{id_objetivo}_c3')

    # apurando erros
    for cenario in ['c1', 'c2', 'c3']:
        df3[f'erro{id_objetivo}_{cenario}'] = df3[f'fitness{id_objetivo}'] - df3[f'fitness{id_objetivo}_{cenario}']
        df3[f'erro_abs{id_objetivo}_{cenario}'] = df3[f'erro{id_objetivo}_{cenario}'].abs()

        print(f'WAPE fitness{id_objetivo} {cenario}: {df3[f"erro_abs{id_objetivo}_{cenario}"].sum() / df3[f"fitness{id_objetivo}"].sum()}')


    return df3