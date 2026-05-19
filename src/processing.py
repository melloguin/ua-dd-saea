import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting
#from src.nsga2.evaluation import genotype_to_registro


######################################################################################################################
######################################################################################################################

###########################################################
# Function to calculate fitness with hardcoded equations using vectorized operations


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


def find_pareto_front_nd(df, obj_cols, minimize=True):
    """
    Non-dominated front for 3+ objectives using pymoo NDS.

    Parameters
    ----------
    df : pd.DataFrame
    obj_cols : list of str
        Column names of objectives (e.g. ['f1', 'f2', 'f3']).
    minimize : bool
        If True, lower is better (standard benchmark convention).

    Returns
    -------
    pd.DataFrame
        Rows of ``df`` that belong to the first non-dominated front.
    """
    F = df[list(obj_cols)].values.astype(float)
    if not minimize:
        F = -F
    nds = NonDominatedSorting(method="efficient_non_dominated_sort")
    front0 = nds.do(F, only_non_dominated_front=True)
    return df.iloc[front0].copy()


def adicionar_regioes_bins(df, n_bins_x1=4, n_bins_x2=4, x1_col='x_1', x2_col='x_2'):
    """
    Assign ``regiao`` (1..n_bins_x1*n_bins_x2) from a 4x4-style binning on two decision variables.
    """
    out = df.copy()
    out['bin_x1'] = pd.cut(out[x1_col], bins=n_bins_x1, labels=False)
    out['bin_x2'] = pd.cut(out[x2_col], bins=n_bins_x2, labels=False)
    out['regiao'] = (out['bin_x1'] * n_bins_x2 + out['bin_x2'] + 1).astype(str)
    return out


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



###########################################################



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


###########################################################




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
    
    has_f3 = 'f3' in df_ruidoso.columns

    # Médias globais das funções objetivo (para calcular escalas)
    mean_f1 = df['f1'].mean()
    mean_f2 = df['f2'].mean()
    mean_f3 = df['f3'].mean() if has_f3 else None
    
    print(f"Média F1: {mean_f1:.6f}")
    print(f"Média F2: {mean_f2:.6f}")
    if has_f3:
        print(f"Média F3: {mean_f3:.6f}")
    
    # Inicializar colunas de ruído com zeros
    df_ruidoso['_ruido_f1'] = 0.0
    df_ruidoso['_ruido_f2'] = 0.0
    if has_f3:
        df_ruidoso['_ruido_f3'] = 0.0
    
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
        scale_f3 = forca_ruido * mean_f3 if has_f3 else None
        
        msg = f"  Região {reg:2d}: força={forca_ruido:.1f}, scale_f1={scale_f1:.4f}, scale_f2={scale_f2:.4f}, dist={dist_nome}"
        if has_f3:
            msg += f", scale_f3={scale_f3:.4f}"
        print(msg)
        
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
        
        if has_f3:
            np.random.shuffle(std_noise)
            ruido_f3 = (std_noise * scale_f3) + target_mean
            for i, idx in enumerate(indices_regiao):
                df_ruidoso.at[idx, '_ruido_f3'] = ruido_f3[i]
        
    # Aplicar os ruídos
    df_ruidoso['f1'] = df_ruidoso['f1'] + df_ruidoso['_ruido_f1']
    df_ruidoso['f2'] = df_ruidoso['f2'] + df_ruidoso['_ruido_f2']
    if has_f3:
        df_ruidoso['f3'] = df_ruidoso['f3'] + df_ruidoso['_ruido_f3']
    
    # Verificar se ruído foi realmente aplicado
    ruido_f1_aplicado = df_ruidoso['_ruido_f1'].abs().mean()
    ruido_f2_aplicado = df_ruidoso['_ruido_f2'].abs().mean()
    print(f"\n📈 Ruído médio absoluto aplicado em F1: {ruido_f1_aplicado:.6f}")
    print(f"📈 Ruído médio absoluto aplicado em F2: {ruido_f2_aplicado:.6f}")
    if has_f3:
        ruido_f3_aplicado = df_ruidoso['_ruido_f3'].abs().mean()
        print(f"📈 Ruído médio absoluto aplicado em F3: {ruido_f3_aplicado:.6f}")
    
    # Remover colunas temporárias
    drop_noise = ['_ruido_f1', '_ruido_f2']
    if has_f3:
        drop_noise.append('_ruido_f3')
    df_ruidoso.drop(columns=drop_noise, inplace=True)
    
    print("✅ Injeção concluída com sucesso!")
    return df_ruidoso






######################################################################################################################
# NoisyProblem wrapper for online algorithms
######################################################################################################################

from pymoo.core.problem import Problem as _PymooProblem


class NoisyProblem(_PymooProblem):
    """Wrap a clean pymoo Problem so that ``_evaluate`` returns noisy fitness.

    Replicates the exact noise model used by ``injetar_ruidos_parametrizados``:
    region-based distribution, centred/standardised, scaled by
    ``forca_ruido * mean_fj_global``.

    Parameters
    ----------
    base : Problem
        The clean (noise-free) problem instance.
    noise_config : dict
        ``{region_int: {'dist': ..., 'params': ..., 'forca_ruido': ...,
        'target_mean': ...}, ...}`` — same dict used in NB2.
    mean_f : array-like, shape (n_obj,)
        Global mean of each objective over the full landscape
        (pre-computed from ``df_{name}.parquet``).
    n_bins_x1, n_bins_x2 : int
        Number of bins along x_1 / x_2 used for region assignment (default 4).
    """

    def __init__(self, base, noise_config, mean_f,
                 n_bins_x1=4, n_bins_x2=4):
        super().__init__(n_var=base.n_var, n_obj=base.n_obj,
                         n_ieq_constr=0, xl=base.xl, xu=base.xu)
        self.base = base
        self.noise_config = noise_config
        self.mean_f = np.asarray(mean_f, dtype=float)
        self.n_bins_x1 = n_bins_x1
        self.n_bins_x2 = n_bins_x2
        self._x1_edges = np.linspace(base.xl[0], base.xu[0], n_bins_x1 + 1)
        self._x2_edges = np.linspace(base.xl[1], base.xu[1], n_bins_x2 + 1)

    def true_pareto_front(self, *args, **kwargs):
        return self.base.true_pareto_front(*args, **kwargs)

    def _assign_regions(self, X):
        """Return 1-indexed region (1..n_bins_x1*n_bins_x2) for each row."""
        b1 = np.clip(np.searchsorted(self._x1_edges, X[:, 0], side='right') - 1,
                      0, self.n_bins_x1 - 1)
        b2 = np.clip(np.searchsorted(self._x2_edges, X[:, 1], side='right') - 1,
                      0, self.n_bins_x2 - 1)
        return b1 * self.n_bins_x2 + b2 + 1

    def _evaluate(self, X, out, *args, **kwargs):
        self.base._evaluate(X, out, *args, **kwargs)
        F_clean = out['F'].copy()
        regions = self._assign_regions(X)

        for reg in np.unique(regions):
            cfg = self.noise_config.get(int(reg))
            if cfg is None:
                continue
            forca = cfg.get('forca_ruido', 0.0)
            if forca == 0:
                continue

            mask = regions == reg
            n = int(mask.sum())
            raw = gerar_ruido_raw(cfg['dist'], cfg['params'], n)
            centered = raw - raw.mean()
            std_val = centered.std()
            if std_val == 0:
                std_val = 1e-6
            std_noise = centered / std_val
            target_mean = cfg.get('target_mean', 0.0)

            for j in range(F_clean.shape[1]):
                if j > 0:
                    np.random.shuffle(std_noise)
                scale_fj = forca * self.mean_f[j]
                out['F'][mask, j] = F_clean[mask, j] + std_noise * scale_fj + target_mean


######################################################################################################################
######################################################################################################################

###########################################################
def create_landscape_from_predictions(df_previsao, df_mcmc, decision_variables=None):
    """Create a landscape DataFrame from predictions + MCMC errors.

    Supports N decision variables and M objectives.  Auto-detects objective
    columns (``f1, f2, …``) and error columns (``erro_f1, erro_f2, …``).
    """
    import re as _re

    if decision_variables is None:
        decision_variables = sorted(
            [c for c in df_previsao.columns if _re.match(r'^x_\d+$', c)],
            key=lambda c: int(c.split('_')[1]))

    obj_indices = sorted(set(int(c[1:]) for c in df_previsao.columns if _re.match(r'^f\d+$', c)))

    keep = set(decision_variables + ['regiao'])
    for c in df_previsao.columns:
        if _re.match(r'^f\d+', c):
            keep.add(c)
    cols_df = [c for c in df_previsao.columns if c in keep]

    df_landscape = df_previsao[cols_df].merge(df_mcmc, on='regiao', how='left')

    for j in obj_indices:
        pred_col = f'f{j}_predicted'
        erro_col = f'erro_f{j}'
        if pred_col in df_landscape.columns and erro_col in df_landscape.columns:
            df_landscape[f'fitness{j}'] = (df_landscape[pred_col] + df_landscape[erro_col]).round(3)

    agg_dict = {}
    skip = set(decision_variables + ['regiao', 'id_simulacao'])
    skip.update(c for c in df_landscape.columns if _re.match(r'^erro_f\d+$', c))
    for c in df_landscape.columns:
        if c in skip or c in decision_variables:
            continue
        if c.startswith('fitness'):
            agg_dict[c] = list
        else:
            agg_dict[c] = 'first'

    df_landscape = df_landscape.groupby(decision_variables, as_index=False).agg(agg_dict)

    return df_landscape