import matplotlib.pyplot as plt


def collect_generation_stats(population, generation, config):
    """
    Coleta estatísticas da população em uma geração
    
    Args:
        population: lista de indivíduos da população
        generation: número da geração atual (0-indexed)
        config: dicionário de configuração
    
    Returns:
        dict com estatísticas da geração
    """
    # Encontrar soluções com ua_rank próximo de 1 (melhor front uncertainty-aware)
    # Usamos threshold de 1.5 para capturar soluções do primeiro front considerando incerteza
    front1 = [ind for ind in population if hasattr(ind, 'ua_rank') and ind.ua_rank <= 1.5]
    
    # Fallback: se não houver ua_rank, tenta usar rank tradicional
    if len(front1) == 0:
        front1 = [ind for ind in population if hasattr(ind, 'rank') and ind.rank == 1]
    
    # Calcular estatísticas de fitness
    fitness1_values = [ind.fitness[0] for ind in front1]
    fitness2_values = [ind.fitness[1] for ind in front1]
    
    # Converter de volta para valores originais se estiver maximizando
    if config.get('maximize', False):
        fitness1_max = -min(fitness1_values)
        fitness2_max = -min(fitness2_values)
    else:
        fitness1_max = max(fitness1_values)
        fitness2_max = max(fitness2_values)
    
    fitness_sum_max = fitness1_max + fitness2_max
    
    return {
        'geracao': generation + 1,
        'solucoes_front1': len(front1),
        'fitness1_max': fitness1_max,
        'fitness2_max': fitness2_max,
        'fitness_sum_max': fitness_sum_max
    }

def plot_optimization_progress(df_progress):
    """
    Plota gráficos de evolução da otimização
    
    Args:
        df_progress: DataFrame com colunas [geracao, solucoes_front1, fitness1_max, fitness2_max, fitness_sum_max]
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    
    # Gráfico 1: Evolução das Fitness por Geração
    ax1 = axes[0]
    ax1.plot(df_progress['geracao'], df_progress['fitness1_max'], 
             label='Fitness 1 (máx)', marker='o', linewidth=2, markersize=3)
    ax1.plot(df_progress['geracao'], df_progress['fitness2_max'], 
             label='Fitness 2 (máx)', marker='s', linewidth=2, markersize=3)
    ax1.plot(df_progress['geracao'], df_progress['fitness_sum_max'], 
             label='Fitness 1 + 2 (máx)', marker='^', linewidth=2, markersize=3, linestyle='--')
    
    ax1.set_xlabel('Geração', fontsize=12)
    ax1.set_ylabel('Valor de Fitness (máximo)', fontsize=12)
    ax1.set_title('Evolução das Fitness por Geração', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Gráfico 2: Número de Soluções no Front por Geração
    ax2 = axes[1]
    ax2.plot(df_progress['geracao'], df_progress['solucoes_front1'], 
             color='#2E86AB', marker='o', linewidth=2, markersize=4)
    ax2.fill_between(df_progress['geracao'], df_progress['solucoes_front1'], 
                      alpha=0.3, color='#2E86AB')
    
    ax2.set_xlabel('Geração', fontsize=12)
    ax2.set_ylabel('Número de Soluções', fontsize=12)
    ax2.set_title('Evolução do Tamanho do Front de Pareto', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    print("\n✅ Gráficos de progresso gerados com sucesso!")