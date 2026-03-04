import numpy as np
import pandas as pd
from scipy import stats


def comparar_distribuicoes(df_surrogate, df_validacao, col, problema, calcula_wape = True,
                          alpha=0.05, metodo='auto'):
    """
    Compara distribuições estatísticas de uma coluna entre dois dataframes,
    por região, usando teste de Kolmogorov-Smirnov.
    
    Parameters:
    -----------
    df_surrogate : pd.DataFrame
        DataFrame com dados gerais (surrogate/população completa)
    df_validacao : pd.DataFrame
        DataFrame com dados de validação (amostra)
    col : str
        Nome da coluna a ser analisada (ex: 'erro1_c1', 'erro2_c1')
    problema : str
        Identificador do problema (ex: 'problema1', 'problema2')
    alpha : float, default=0.05
        Nível de significância para o teste KS (threshold para determinar igualdade)
    metodo : str, default='auto'
        Método para calcular p-value no teste KS ('auto', 'exact', 'asymp')
    
    Returns:
    --------
    pd.DataFrame
        DataFrame com resultados da comparação por região, contendo:
        - problema: identificador do problema
        - objetivo: 'fitness1' ou 'fitness2' baseado na coluna
        - regiao: região analisada
        - coluna: nome da coluna analisada
        - ks_statistic: estatística do teste KS
        - ks_pvalue: p-valor do teste KS
        - distribuicoes_iguais: 'Sim' se p-value >= alpha, 'Não' caso contrário
        - media_geral: média da distribuição em df_surrogate
        - media_validacao: média da distribuição em df_validacao
        - desvpad_geral: desvio padrão em df_surrogate
        - desvpad_validacao: desvio padrão em df_validacao
        - size_geral: número de observações em df_surrogate
        - size_validacao: número de observações em df_validacao
        - wape_geral: WAPE da base geral (média do erro absoluto / média do fitness)
        - wape_validacao: WAPE da base de validação (média do erro absoluto / média do fitness)
    """
    
    # Determinar objetivo baseado na coluna de forma flexível
    if col == 'erro1_c1':
        objetivo = 'fitness1'
    elif col == 'erro2_c1':
        objetivo = 'fitness2'
    elif col == 'erro_f1':
        objetivo = 'f1'
    elif col == 'erro_f2':
        objetivo = 'f2'
    else:
        # Padrão genérico: substitui 'erro' por 'fitness' ou remove '_erro'
        objetivo = col.replace('erro', 'fitness').replace('_c1', '')
    
    # Lista para armazenar resultados
    resultados = []
    
    # Obter regiões únicas (do df_surrogate que tem todas as regiões)
    regioes = df_surrogate['regiao'].unique()
    
    for regiao in sorted(regioes):
        # Filtrar dados por região
        df_surr_regiao = df_surrogate[df_surrogate['regiao'] == regiao]
        df_val_regiao = df_validacao[df_validacao['regiao'] == regiao]
        
        # Obter distribuições da coluna (removendo NaN)
        dist_surrogate = df_surr_regiao[col].dropna()
        dist_validacao = df_val_regiao[col].dropna()
        
        # Verificar se há dados suficientes
        if len(dist_surrogate) == 0 or len(dist_validacao) == 0:
            print(f"Aviso: Região {regiao} não tem dados suficientes")
            continue
        
        # Teste de Kolmogorov-Smirnov (two-sample test)
        ks_statistic, ks_pvalue = stats.ks_2samp(
            dist_surrogate, 
            dist_validacao, 
            alternative='two-sided', 
            method=metodo
        )
        
        # Determinar se distribuições são iguais (baseado no p-value e alpha)
        # H0: as distribuições são iguais
        # Se p-value >= alpha, não rejeitamos H0 (distribuições são iguais)
        distribuicoes_iguais = 'Sim' if ks_pvalue >= alpha else 'Não'
        
        # Calcular estatísticas descritivas
        media_geral = dist_surrogate.mean()
        media_validacao = dist_validacao.mean()
        desvpad_geral = dist_surrogate.std()
        desvpad_validacao = dist_validacao.std()
        
        # Número de observações
        size_geral = len(dist_surrogate)
        size_validacao = len(dist_validacao)
        
        # Calcular WAPE (média do erro absoluto / média do fitness correspondente)
        # WAPE = erro médio absoluto / valor médio real
        if calcula_wape:
            media_absoluto_geral = df_surr_regiao[col].abs().mean()
            media_fitness_geral = df_surr_regiao[objetivo].mean()
            wape_geral = (media_absoluto_geral / media_fitness_geral) if media_fitness_geral != 0 else np.nan
            
            media_absoluto_validacao = df_val_regiao[col].abs().mean()
            media_fitness_validacao = df_val_regiao[objetivo].mean()
            wape_validacao = (media_absoluto_validacao / media_fitness_validacao) if media_fitness_validacao != 0 else np.nan
        
        # Armazenar resultados
        resultado = {
            'problema': problema,
            'objetivo': objetivo,
            'regiao': regiao,
            'coluna': col,
            'ks_statistic': ks_statistic,
            'ks_pvalue': ks_pvalue,
            'distribuicoes_iguais': distribuicoes_iguais,
            'media_geral': media_geral,
            'media_validacao': media_validacao,
            'desvpad_geral': desvpad_geral,
            'desvpad_validacao': desvpad_validacao,
            'size_geral': size_geral,
            'size_validacao': size_validacao,
        }

        if calcula_wape:
            resultado['wape_geral'] = wape_geral
            resultado['wape_validacao'] = wape_validacao

        
        resultados.append(resultado)
    
    # Criar DataFrame com resultados
    df_resultados = pd.DataFrame(resultados)
    
    return df_resultados


def gerar_amostra_mcmc(df, col, n_samples, 
                       burn_in=1000, 
                       thinning=10,
                       proposal_std=None,
                       proposal_scale=0.7,
                       adaptive=True,
                       random_state=None):
    """
    Gera amostras usando MCMC (Metropolis-Hastings) que seguem a distribuição 
    empírica de uma coluna do DataFrame.
    
    O algoritmo usa Metropolis-Hastings com:
    - Distribuição alvo: densidade estimada via Kernel Density Estimation (KDE)
    - Distribuição proposta: Normal centrada no estado atual
    - Ajuste adaptativo opcional para otimizar taxa de aceitação
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame contendo os dados
    col : str
        Nome da coluna cuja distribuição será replicada
    n_samples : int
        Número de amostras a serem geradas (após burn-in e thinning)
    burn_in : int, default=1000
        Número de iterações iniciais a serem descartadas
    thinning : int, default=10
        Intervalo entre amostras consecutivas (reduz autocorrelação)
    proposal_std : float, optional
        Desvio padrão da distribuição proposta (Normal).
        Se None, usa proposal_scale * std da coluna
    proposal_scale : float, default=0.7
        Fator de escala para calcular proposal_std automaticamente.
        Valores maiores = passos maiores = menor taxa de aceitação
        Valores menores = passos menores = maior taxa de aceitação
    adaptive : bool, default=True
        Se True, ajusta proposal_std durante burn-in para taxa de aceitação ideal
    random_state : int, optional
        Seed para reprodutibilidade
    
    Returns:
    --------
    np.ndarray
        Array com n_samples valores que seguem a distribuição de df[col]
    
    Example:
    --------
    >>> df = pd.DataFrame({'erro': np.random.normal(0, 1, 1000)})
    >>> amostras = gerar_amostra_mcmc(df, 'erro', n_samples=500)
    >>> print(f"Amostras geradas: {len(amostras)}")
    
    Notes:
    ------
    - O algoritmo Metropolis-Hastings garante convergência assintótica 
      para a distribuição alvo
    - Valores maiores de burn_in e thinning aumentam a qualidade das 
      amostras mas aumentam o tempo de computação
    - A taxa de aceitação ideal é entre 20-50% (modo adaptativo busca 35%)
    """
    
    if random_state is not None:
        np.random.seed(random_state)
    
    # Extrair dados da coluna (remover NaN)
    data = df[col].dropna().values
    
    if len(data) == 0:
        raise ValueError(f"Coluna '{col}' não contém dados válidos")
    
    # Estimar densidade usando Kernel Density Estimation (KDE)
    kde = stats.gaussian_kde(data)
    
    # Função de densidade log (mais estável numericamente)
    def log_target_density(x):
        """Log da densidade alvo (evita underflow)"""
        try:
            density = kde.evaluate(x)
            # Adicionar pequeno epsilon para evitar log(0)
            return np.log(density + 1e-300)
        except:
            return -np.inf
    
    # Definir desvio padrão inicial da proposta
    if proposal_std is None:
        proposal_std = proposal_scale * np.std(data)
    
    # Inicializar cadeia com valor próximo à mediana
    current_state = np.median(data)
    current_log_density = log_target_density(current_state)
    
    # Armazenar amostras
    samples = []
    
    # Métricas
    total_iterations = burn_in + (n_samples * thinning)
    accepted = 0
    
    # Ajuste adaptativo durante burn-in
    if adaptive and burn_in > 0:
        adaptation_window = 100  # Janela para calcular taxa de aceitação
        acceptance_target = 0.35  # Taxa de aceitação alvo (ideal ~30-40%)
        accepted_in_window = 0
        
        for iteration in range(burn_in):
            # Propor novo estado (random walk)
            proposed_state = current_state + np.random.normal(0, proposal_std)
            proposed_log_density = log_target_density(proposed_state)
            
            # Calcular razão de aceitação (em log-space)
            log_acceptance_ratio = proposed_log_density - current_log_density
            
            # Aceitar ou rejeitar
            if np.log(np.random.uniform(0, 1)) < log_acceptance_ratio:
                current_state = proposed_state
                current_log_density = proposed_log_density
                accepted += 1
                accepted_in_window += 1
            
            # Ajustar proposal_std periodicamente durante burn-in
            if (iteration + 1) % adaptation_window == 0:
                acceptance_rate_window = accepted_in_window / adaptation_window
                
                # Ajustar proposal_std baseado na taxa de aceitação
                if acceptance_rate_window > 0.50:
                    proposal_std *= 1.2  # Aumentar passos se aceitação muito alta
                elif acceptance_rate_window < 0.20:
                    proposal_std *= 0.8  # Diminuir passos se aceitação muito baixa
                
                accepted_in_window = 0  # Reset contador
        
        # Após burn-in, continuar amostragem com proposal_std ajustado
        for iteration in range(n_samples * thinning):
            proposed_state = current_state + np.random.normal(0, proposal_std)
            proposed_log_density = log_target_density(proposed_state)
            log_acceptance_ratio = proposed_log_density - current_log_density
            
            if np.log(np.random.uniform(0, 1)) < log_acceptance_ratio:
                current_state = proposed_state
                current_log_density = proposed_log_density
                accepted += 1
            
            # Coletar amostras com thinning
            if iteration % thinning == 0:
                samples.append(current_state)
    else:
        # MCMC loop sem adaptação
        for iteration in range(total_iterations):
            # Propor novo estado (random walk)
            proposed_state = current_state + np.random.normal(0, proposal_std)
            proposed_log_density = log_target_density(proposed_state)
            
            # Calcular razão de aceitação (em log-space)
            log_acceptance_ratio = proposed_log_density - current_log_density
            
            # Aceitar ou rejeitar
            if np.log(np.random.uniform(0, 1)) < log_acceptance_ratio:
                current_state = proposed_state
                current_log_density = proposed_log_density
                accepted += 1
            
            # Após burn-in, coletar amostras com thinning
            if iteration >= burn_in and (iteration - burn_in) % thinning == 0:
                samples.append(current_state)
    
    # Calcular taxa de aceitação
    acceptance_rate = accepted / total_iterations
    
    print(f"MCMC completado:")
    print(f"  - Total de iterações: {total_iterations:,}")
    print(f"  - Burn-in: {burn_in:,}")
    print(f"  - Thinning: {thinning}")
    print(f"  - Amostras geradas: {len(samples):,}")
    print(f"  - Taxa de aceitação: {acceptance_rate:.2%}")
    print(f"  - Proposal std final: {proposal_std:.4f}")
    
    if acceptance_rate < 0.15:
        print("  ⚠️  Taxa de aceitação baixa. Considere reduzir proposal_scale.")
    elif acceptance_rate > 0.70:
        print("  ⚠️  Taxa de aceitação alta. Considere aumentar proposal_scale.")
    else:
        print("  ✅ Taxa de aceitação adequada (15-70%).")
    
    return np.array(samples)


def gerar_amostras_mcmc_por_regiao(df, col, n_samples, 
                                   burn_in=1000, 
                                   thinning=10,
                                   proposal_std=None,
                                   proposal_scale=0.7,
                                   adaptive=True,
                                   random_state=None):
    """
    Gera amostras MCMC para cada região do DataFrame.
    
    Wrapper conveniente que aplica gerar_amostra_mcmc() separadamente
    para cada região, gerando um dicionário de amostras indexado por região.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame contendo os dados com coluna 'regiao'
    col : str
        Nome da coluna cuja distribuição será replicada
    n_samples : int
        Número de amostras a serem geradas por região
    burn_in : int, default=1000
        Número de iterações iniciais a serem descartadas
    thinning : int, default=10
        Intervalo entre amostras consecutivas
    proposal_std : float, optional
        Desvio padrão da distribuição proposta. Se None, calculado automaticamente
    proposal_scale : float, default=0.7
        Fator de escala para calcular proposal_std automaticamente
    adaptive : bool, default=True
        Se True, ajusta proposal_std durante burn-in
    random_state : int, optional
        Seed para reprodutibilidade
    
    Returns:
    --------
    dict
        Dicionário {regiao: np.ndarray} com amostras MCMC para cada região
    
    Example:
    --------
    >>> amostras_por_regiao = gerar_amostras_mcmc_por_regiao(
    ...     df_surrogate1, 'erro1_c1', n_samples=500, random_state=42
    ... )
    >>> print(f"Regiões processadas: {list(amostras_por_regiao.keys())}")
    """
    
    if 'regiao' not in df.columns:
        raise ValueError("DataFrame deve conter coluna 'regiao'")
    
    # Dicionário para armazenar amostras por região
    amostras_por_regiao = {}
    
    # Obter regiões únicas
    regioes = sorted(df['regiao'].unique())
    
    print(f"\n{'='*70}")
    print(f"Gerando amostras MCMC por região para coluna '{col}'")
    print(f"Modo adaptativo: {'Ativado' if adaptive else 'Desativado'}")
    print(f"Proposal scale: {proposal_scale}")
    print(f"{'='*70}\n")
    
    for regiao in regioes:
        print(f"📍 Região {regiao}:")
        
        # Filtrar dados da região
        df_regiao = df[df['regiao'] == regiao]
        
        # Verificar se há dados suficientes
        n_dados = df_regiao[col].notna().sum()
        if n_dados < 10:
            print(f"  ⚠️  Região {regiao} tem apenas {n_dados} observações. Pulando...")
            continue
        
        # Gerar amostras MCMC para esta região
        try:
            if random_state is not None:
                seed = random_state + int(regiao) if regiao.isdigit() else random_state
            else:
                seed = None
                
            amostras = gerar_amostra_mcmc(
                df_regiao, 
                col, 
                n_samples=n_samples,
                burn_in=burn_in,
                thinning=thinning,
                proposal_std=proposal_std,
                proposal_scale=proposal_scale,
                adaptive=adaptive,
                random_state=seed
            )
            
            amostras_por_regiao[regiao] = amostras
            
            # Estatísticas de comparação
            media_original = df_regiao[col].mean()
            std_original = df_regiao[col].std()
            media_mcmc = amostras.mean()
            std_mcmc = amostras.std()
            
            print(f"  📊 Comparação de estatísticas:")
            print(f"     Original  - Média: {media_original:8.4f}, Std: {std_original:8.4f}")
            print(f"     MCMC      - Média: {media_mcmc:8.4f}, Std: {std_mcmc:8.4f}")
            print()
            
        except Exception as e:
            print(f"  ❌ Erro ao gerar amostras para região {regiao}: {str(e)}")
            print()
            continue
    
    print(f"{'='*70}")
    print(f"✅ Amostras MCMC geradas para {len(amostras_por_regiao)} região(ões)")
    print(f"{'='*70}\n")
    
    return amostras_por_regiao


def gerar_amostras_mcmc_por_problema(df_validacao, n_samples, 
                                     col1='erro1_c1', 
                                     col2='erro2_c1',
                                     burn_in=1000, 
                                     thinning=10,
                                     proposal_scale=0.7,
                                     adaptive=True,
                                     random_state=42):
    """
    Gera amostras MCMC para duas colunas (fitness 1 e fitness 2) de um problema
    e unifica os resultados em um único DataFrame.
    
    Esta função gera amostras separadamente para cada coluna usando MCMC,
    cria DataFrames com índices de linha, e faz join por índice e região
    para garantir correspondência correta entre as amostras.
    
    Parameters:
    -----------
    df_validacao : pd.DataFrame
        DataFrame de validação contendo os dados e coluna 'regiao'
    n_samples : int
        Número de amostras a serem geradas por região
    col1 : str, default='erro1_c1'
        Nome da primeira coluna (tipicamente erro do fitness 1)
    col2 : str, default='erro2_c1'
        Nome da segunda coluna (tipicamente erro do fitness 2)
    burn_in : int, default=1000
        Número de iterações iniciais a serem descartadas
    thinning : int, default=10
        Intervalo entre amostras consecutivas
    proposal_scale : float, default=0.7
        Fator de escala para calcular proposal_std automaticamente
    adaptive : bool, default=True
        Se True, ajusta proposal_std durante burn-in
    random_state : int, optional
        Seed para reprodutibilidade
    
    Returns:
    --------
    pd.DataFrame
        DataFrame unificado contendo:
        - index_linha: índice da amostra dentro de cada região
        - regiao: identificador da região
        - col1: amostras MCMC para a primeira coluna
        - col2: amostras MCMC para a segunda coluna
    
    Example:
    --------
    >>> df_mcmc1 = gerar_amostras_mcmc_por_problema(
    ...     df_validacao=df_validacao1,
    ...     n_samples=200,
    ...     random_state=42
    ... )
    >>> print(f"Amostras geradas: {len(df_mcmc1)}")
    >>> print(df_mcmc1.head())
    
    Notes:
    ------
    - A função garante que as amostras de col1 e col2 são alinhadas por
      índice e região (double check de segurança)
    - Cada região terá exatamente n_samples amostras
    - O índice de linha (index_linha) vai de 0 a n_samples-1 para cada região
    """
    
    print(f"\n{'='*70}")
    print(f"🔄 GERANDO AMOSTRAS MCMC PARA PROBLEMA")
    print(f"{'='*70}")
    print(f"Colunas: {col1} e {col2}")
    print(f"Amostras por região: {n_samples}")
    print(f"{'='*70}\n")
    
    # ========================================================================
    # Gerar amostras para col1 (ex: erro1_c1 / fitness1)
    # ========================================================================
    print(f"📊 Gerando amostras para {col1}...\n")
    amostras_col1 = gerar_amostras_mcmc_por_regiao(
        df=df_validacao,
        col=col1,
        n_samples=n_samples,
        burn_in=burn_in,
        thinning=thinning,
        proposal_scale=proposal_scale,
        adaptive=adaptive,
        random_state=random_state
    )
    
    # Criar DataFrame para col1 com índice de linha
    df_col1 = pd.DataFrame({
        'regiao': np.repeat(list(amostras_col1.keys()), 
                           [len(v) for v in amostras_col1.values()]),
        col1: np.concatenate(list(amostras_col1.values()))
    })
    # Adicionar índice de linha dentro de cada região
    df_col1['index_linha'] = df_col1.groupby('regiao').cumcount()
    
    # ========================================================================
    # Gerar amostras para col2 (ex: erro2_c1 / fitness2)
    # ========================================================================
    print(f"\n📊 Gerando amostras para {col2}...\n")
    amostras_col2 = gerar_amostras_mcmc_por_regiao(
        df=df_validacao,
        col=col2,
        n_samples=n_samples,
        burn_in=burn_in,
        thinning=thinning,
        proposal_scale=proposal_scale,
        adaptive=adaptive,
        random_state=random_state
    )
    
    # Criar DataFrame para col2 com índice de linha
    df_col2 = pd.DataFrame({
        'regiao': np.repeat(list(amostras_col2.keys()), 
                           [len(v) for v in amostras_col2.values()]),
        col2: np.concatenate(list(amostras_col2.values()))
    })
    # Adicionar índice de linha dentro de cada região
    df_col2['index_linha'] = df_col2.groupby('regiao').cumcount()
    
    # ========================================================================
    # Unificar DataFrames com double check (join por index_linha e regiao)
    # ========================================================================
    print(f"\n🔗 Unificando DataFrames...")
    print(f"   - DataFrame {col1}: {len(df_col1)} linhas")
    print(f"   - DataFrame {col2}: {len(df_col2)} linhas")
    
    # Join por região e índice de linha (garantia dupla de correspondência)
    df_mcmc = pd.merge(
        df_col1,
        df_col2,
        on=['regiao', 'index_linha'],
        how='inner',
        validate='one_to_one'  # Garante correspondência 1:1
    )
    
    # Verificação de integridade
    assert len(df_mcmc) == len(df_col1) == len(df_col2), \
        "Erro: Tamanhos dos DataFrames não correspondem após merge"
    
    print(f"   ✅ Unificação concluída: {len(df_mcmc)} linhas")
    print(f"   ✅ Validação 1:1 bem-sucedida")
    
    # Reordenar colunas para melhor legibilidade
    df_mcmc = df_mcmc[['index_linha', 'regiao', col1, col2]]
    
    # Resumo final
    print(f"\n{'='*70}")
    print(f"✅ AMOSTRAS MCMC GERADAS COM SUCESSO")
    print(f"{'='*70}")
    print(f"📊 DataFrame resultante:")
    print(f"   - Total de linhas: {len(df_mcmc)}")
    print(f"   - Regiões: {sorted(df_mcmc['regiao'].unique())}")
    print(f"   - Amostras por região: {df_mcmc.groupby('regiao').size().iloc[0]}")
    print(f"   - Colunas: {list(df_mcmc.columns)}")
    print(f"{'='*70}\n")
    
    return df_mcmc

