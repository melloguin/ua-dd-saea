import numpy as np
import matplotlib.pyplot as plt


def collect_generation_stats(population, generation, config):
    fitness_values = [ind.fitness for ind in population if ind.fitness is not None]

    if len(fitness_values) == 0:
        return {'generation': generation}

    fitness_array = np.array(fitness_values)

    stats = {
        'generation': generation,
        'pop_size': len(population),
    }

    for obj_idx in range(config['n_objetivos']):
        obj_values = fitness_array[:, obj_idx]
        stats[f'obj{obj_idx+1}_mean'] = np.mean(obj_values)
        stats[f'obj{obj_idx+1}_min'] = np.min(obj_values)
        stats[f'obj{obj_idx+1}_max'] = np.max(obj_values)
        stats[f'obj{obj_idx+1}_std'] = np.std(obj_values)

    return stats


def plot_optimization_progress(df_progress):
    n_objectives = sum(1 for col in df_progress.columns if col.endswith('_mean') and col.startswith('obj'))

    fig, axes = plt.subplots(1, n_objectives, figsize=(8 * n_objectives, 5))
    if n_objectives == 1:
        axes = [axes]

    for obj_idx in range(n_objectives):
        ax = axes[obj_idx]
        ax.plot(df_progress['generation'], df_progress[f'obj{obj_idx+1}_mean'], label='Mean', linewidth=2)
        ax.fill_between(
            df_progress['generation'],
            df_progress[f'obj{obj_idx+1}_min'],
            df_progress[f'obj{obj_idx+1}_max'],
            alpha=0.3, label='Min-Max Range'
        )
        ax.set_xlabel('Geração')
        ax.set_ylabel(f'Objetivo {obj_idx+1}')
        ax.set_title(f'Progresso do Objetivo {obj_idx+1}')
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()
