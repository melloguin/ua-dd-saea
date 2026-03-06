import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
#from src.nsga2.evaluation import genotype_to_registro


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

def find_pareto_front(df, minimize = False, fitness1 = 'fitness1', fitness2 = 'fitness2'):
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
    df_sorted = df.sort_values(by=[fitness1, fitness2], 
                                ascending=[minimize, minimize]).reset_index(drop=False)
    
    # Lista para armazenar índices dos pontos não-dominados
    pareto_indices = []
    
    # Máximo de fitness2 visto até agora
    max_fitness2 = float('inf') if minimize else float('-inf')
        
    # Percorrer pontos ordenados
    for idx, row in df_sorted.iterrows():
        current_fitness1 = row[fitness1]
        current_fitness2 = row[fitness2]
        
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
        
        if minimize:
            if current_fitness2 <= max_fitness2:
                pareto_indices.append(row['index'])
                max_fitness2 = current_fitness2
        else:
            if current_fitness2 >= max_fitness2:
                pareto_indices.append(row['index'])
                max_fitness2 = current_fitness2

    
    # Extrair os pontos da fronteira de Pareto usando os índices originais
    pareto_front = df.loc[pareto_indices].copy()
    
    # Ordenar a fronteira por fitness1 para melhor visualização
    pareto_front = pareto_front.sort_values(by=fitness1, ascending=minimize)
    
    print(f"✅ Fronteira de Pareto encontrada!")
    print(f"Fronteira de Pareto contém {len(pareto_front):,} pontos.")
    print(f"Isso representa {100 * len(pareto_front) / len(df):.4f}% do espaço de busca.")
    
    return pareto_front



############################################################
#def history_to_dataframe(history):
#    """
#    Transforma o histórico de populações do NSGA-II em um dataframe.
#    
#    Args:
#        history: lista de gerações, onde cada geração contém uma lista de 
#                 dicionários com 'genotype' e 'fitness'
#    
#    Returns:
#        DataFrame com colunas: geracao, id_solucao, genotipo (registro)
#    """
#    dados = []
#    
#    for geracao, populacao in enumerate(history):
#        for id_solucao, individuo in enumerate(populacao):
#            # Converter genótipo para registro usando a função já existente
#            registro = genotype_to_registro(individuo['genotype'])
#            
#            dados.append({
#                'geracao': geracao,
#                'id_solucao': id_solucao,
#                'genotipo': registro
#            })
#    
#    return pd.DataFrame(dados)





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




##########################################################################################
# Adicao de ruido no treinamento do modelo surrogate (MMF1)
##########################################################################################

# FUNÇÃO GERADORA DE DISTRIBUIÇÕES BRUTAS
def gerar_ruido_raw(dist, params, n_samples):
    """Gera a amostragem bruta baseada no nome da distribuição e seus parâmetros."""
    if dist == 'bimodal':
        regime = np.random.choice([0, 1], size=n_samples, p=params['p'])
        return np.where(regime == 0, 
                        np.random.normal(params['mu1'], params['sd1'], n_samples), 
                        np.random.normal(params['mu2'], params['sd2'], n_samples))
    elif dist == 'student_t':   return np.random.standard_t(df=params['df'], size=n_samples)
    elif dist == 'lognormal':   return np.random.lognormal(mean=params['mean'], sigma=params['sigma'], size=n_samples)
    elif dist == 'poisson':     return np.random.poisson(lam=params['lam'], size=n_samples)
    elif dist == 'binomial':    return np.random.binomial(n=params['n'], p=params['p'], size=n_samples)
    elif dist == 'geometric':   return np.random.geometric(p=params['p'], size=n_samples)
    elif dist == 'exponential': return np.random.exponential(scale=params['scale'], size=n_samples)
    elif dist == 'uniform':     return np.random.uniform(low=params['low'], high=params['high'], size=n_samples)
    elif dist == 'laplace':     return np.random.laplace(loc=params['loc'], scale=params['scale'], size=n_samples)
    elif dist == 'gamma':       return np.random.gamma(shape=params['shape'], scale=params['scale'], size=n_samples)
    elif dist == 'beta':        return np.random.beta(a=params['a'], b=params['b'], size=n_samples)
    elif dist == 'rayleigh':    return np.random.rayleigh(scale=params['scale'], size=n_samples)
    elif dist == 'weibull':     return np.random.weibull(a=params['a'], size=n_samples)
    elif dist == 'logistic':    return np.random.logistic(loc=params['loc'], scale=params['scale'], size=n_samples)
    elif dist == 'pareto':      return np.random.pareto(a=params['a'], size=n_samples)
    elif dist == 'rademacher':  return np.random.choice([-1.0, 1.0], size=n_samples)
    else:                       return np.random.normal(0, 1, n_samples) # Default fallback

# FUNÇÃO DE INJEÇÃO PRINCIPAL (Para o DataFrame)
def injetar_ruidos_parametrizados(df, config_dict, col_regiao='regiao'):
    """
    Injeta ruídos no DataFrame baseando-se no dicionário de configuração.
    Garante padronização de variância e ajuste fino de média.
    Agora cada região tem sua própria força de ruído (forca_ruido) definida no config_dict.
    """
    print("Iniciando injeção de ruídos parametrizados...")
    df_ruidoso = df.copy()
    
    # Médias globais das funções objetivo (para calcular escalas)
    mean_f1 = df['f1'].mean()
    mean_f2 = df['f2'].mean()
    
    print(f"Média F1: {mean_f1:.6f}")
    print(f"Média F2: {mean_f2:.6f}")
    
    # Inicializar colunas de ruído com zeros
    df_ruidoso['_ruido_f1'] = 0.0
    df_ruidoso['_ruido_f2'] = 0.0
    
    np.random.seed(42)
    
    print("\n📊 Força de ruído por região:")
    for reg, conf in config_dict.items():
        # Converter a chave para string para comparar com a coluna 'regiao'
        reg_str = str(reg)
        indices_regiao = df_ruidoso[df_ruidoso[col_regiao] == reg_str].index.tolist()
        n_samples = len(indices_regiao)
        
        if n_samples == 0: 
            print(f"⚠️  Região {reg} não encontrada no DataFrame")
            continue
            
        dist_nome = conf['dist']
        params = conf['params']
        target_mean = conf['target_mean']
        forca_ruido = conf.get('forca_ruido', 0.0)  # Lê força de ruído específica da região
        
        # Escalas específicas para esta região
        scale_f1 = forca_ruido * mean_f1
        scale_f2 = forca_ruido * mean_f2
        
        print(f"  Região {reg:2d}: força={forca_ruido:.1f}, scale_f1={scale_f1:.4f}, scale_f2={scale_f2:.4f}, dist={dist_nome}")
        
        # Se força de ruído é zero nesta região, pular
        if forca_ruido == 0:
            continue
        
        # Gera o ruído
        raw_noise = gerar_ruido_raw(dist_nome, params, n_samples)
        
        # 1. Centraliza em 0
        centered_noise = raw_noise - np.mean(raw_noise)
        
        # 2. Padroniza para std = 1
        std_val = np.std(centered_noise)
        if std_val == 0: std_val = 1e-6
        std_noise = centered_noise / std_val
        
        # 3. Aplica a escala específica da região e soma a média-alvo desejada
        # Para f1
        ruido_f1 = (std_noise * scale_f1) + target_mean
        for i, idx in enumerate(indices_regiao):
            df_ruidoso.at[idx, '_ruido_f1'] = ruido_f1[i]
        
        # Re-embaralha para criar ruído de f2 independente de f1
        np.random.shuffle(std_noise)
        ruido_f2 = (std_noise * scale_f2) + target_mean
        for i, idx in enumerate(indices_regiao):
            df_ruidoso.at[idx, '_ruido_f2'] = ruido_f2[i]
        
    # Aplicar os ruídos
    df_ruidoso['f1'] = df_ruidoso['f1'] + df_ruidoso['_ruido_f1']
    df_ruidoso['f2'] = df_ruidoso['f2'] + df_ruidoso['_ruido_f2']
    
    # Verificar se ruído foi realmente aplicado
    ruido_f1_aplicado = df_ruidoso['_ruido_f1'].abs().mean()
    ruido_f2_aplicado = df_ruidoso['_ruido_f2'].abs().mean()
    print(f"\n📈 Ruído médio absoluto aplicado em F1: {ruido_f1_aplicado:.6f}")
    print(f"📈 Ruído médio absoluto aplicado em F2: {ruido_f2_aplicado:.6f}")
    
    # Remover colunas temporárias
    df_ruidoso.drop(columns=['_ruido_f1', '_ruido_f2'], inplace=True)
    
    print("✅ Injeção concluída com sucesso!")
    return df_ruidoso






######################################################################################################################
######################################################################################################################

###########################################################
def create_landscape_from_predictions(df_previsao, df_mcmc, decision_variables=['x_1', 'x_2']):
    """
    Processa landscape a partir de dataframes de previsão e MCMC.
    
    Args:
        df_previsao: DataFrame com colunas x_1, x_2, f1, f2, f1_original, f2_original, 
                     f1_predicted, f2_predicted, regiao
        df_mcmc: DataFrame com erro_f1, erro_f2, regiao, id_simulacao
        decision_variables: Lista com nomes das variáveis de decisão (default: ['x_1', 'x_2'])
    
    Returns:
        DataFrame com colunas: x_1, x_2, f1, f2, f1_original, f2_original, 
                              f1_predicted, f2_predicted, fitness1 (lista), fitness2 (lista)
    """
    # Selecionar colunas necessárias do df_previsao
    cols_df = decision_variables + ['regiao', 'f1', 'f2', 'f1_original', 'f2_original', 'f1_predicted', 'f2_predicted']
    
    # Merge com df_mcmc para obter erros
    df_landscape = df_previsao[cols_df].merge(df_mcmc, on='regiao', how='left')
    
    # Calcular fitness1 e fitness2 (predicted + erro)
    df_landscape['fitness1'] = round(df_landscape['f1_predicted'] + df_landscape['erro_f1'], 3)
    df_landscape['fitness2'] = round(df_landscape['f2_predicted'] + df_landscape['erro_f2'], 3)
    
    # Agrupar por variáveis de decisão
    # Para as colunas escalares (f1, f2, etc), pegamos o primeiro valor (são iguais para mesma coordenada)
    # Para fitness1 e fitness2, criamos listas (múltiplas simulações)
    agg_dict = {
        'f1': 'first',
        'f2': 'first',
        'f1_original': 'first',
        'f2_original': 'first',
        'f1_predicted': 'first',
        'f2_predicted': 'first',
        'fitness1': list,
        'fitness2': list
    }
    
    df_landscape = (df_landscape
                    .groupby(decision_variables, as_index=False)
                    .agg(agg_dict))
    
    return df_landscape