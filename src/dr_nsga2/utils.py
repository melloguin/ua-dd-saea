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
    # Encontrar soluções no primeiro front
    front1 = [ind for ind in population if ind.rank == 1]
    
    n_obj = len(front1[0].fitness) if front1 else 2
    maximize = config.get('maximize', False)

    stats = {'geracao': generation + 1, 'solucoes_front1': len(front1)}
    fitness_sum = 0.0
    for j in range(n_obj):
        vals = [ind.fitness[j] for ind in front1]
        best = -min(vals) if maximize else max(vals)
        stats[f'fitness{j+1}_max'] = best
        fitness_sum += best
    stats['fitness_sum_max'] = fitness_sum
    return stats

def plot_optimization_progress(df_progress):
    """Plot optimization progress (works for any number of objectives)."""
    fit_cols = [c for c in df_progress.columns if c.startswith('fitness') and c.endswith('_max')
                and c != 'fitness_sum_max']

    fig, axes = plt.subplots(1, 2, figsize=(16, 5))

    ax1 = axes[0]
    for fc in fit_cols:
        ax1.plot(df_progress['geracao'], df_progress[fc],
                 label=fc, marker='o', linewidth=2, markersize=3)
    if 'fitness_sum_max' in df_progress.columns:
        ax1.plot(df_progress['geracao'], df_progress['fitness_sum_max'],
                 label='sum (máx)', marker='^', linewidth=2, markersize=3, linestyle='--')
    ax1.set_xlabel('Geração', fontsize=12)
    ax1.set_ylabel('Fitness (máximo)', fontsize=12)
    ax1.set_title('Evolução das Fitness por Geração', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)

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