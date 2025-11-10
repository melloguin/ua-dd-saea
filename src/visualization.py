import matplotlib.pyplot as plt
import math

# Configure matplotlib for better performance with large datasets
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 6)
plt.rcParams['lines.linewidth'] = 0.5

def display_pareto_front(df, pareto_df):

        # ============================================================================
        # Calcular limites comuns para ambos os gráficos
        # ============================================================================
        
        # Encontrar o máximo entre fitness1 e fitness2 de todos os pontos
        max_fitness = max(df['fitness1'].max(), df['fitness2'].max())
        # Arredondar para cima para um valor "bonito"
        max_limit = math.ceil(max_fitness / 5) * 5
        
        # ============================================================================
        # GRÁFICO 1: Fronteira de Pareto
        # ============================================================================
        
        # Gráfico de dispersão da fronteira de Pareto (figura quadrada)
        fig, ax = plt.subplots(figsize=(10, 10))

        # Plotar a fronteira de Pareto
        ax.scatter(pareto_df['fitness1'], pareto_df['fitness2'], 
                c='red', s=50, alpha=0.7, edgecolors='darkred', 
                linewidth=1.5, label='Fronteira de Pareto', zorder=3)

        # Conectar os pontos para melhor visualização
        ax.plot(pareto_df['fitness1'], pareto_df['fitness2'], 
                'r--', alpha=0.4, linewidth=1, zorder=2)

        # Configurações do gráfico
        ax.set_xlabel('Fitness1 (f1)', fontsize=13, fontweight='bold')
        ax.set_ylabel('Fitness2 (f2)', fontsize=13, fontweight='bold')
        ax.set_title(f'Fronteira de Pareto Global Verdadeira\n({len(pareto_df):,} pontos não-dominados)', 
                fontsize=15, fontweight='bold', pad=20)
        ax.legend(fontsize=11, loc='best')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Definir limites iguais para x e y começando em 0
        ax.set_xlim(0, max_limit)
        ax.set_ylim(0, max_limit)
        
        # Definir aspect ratio igual (1 cm no x = 1 cm no y)
        ax.set_aspect('equal', adjustable='box')

        # Adicionar anotações para os pontos extremos
        # Ponto com maior fitness1
        max_f1_point = pareto_df.iloc[0]
        ax.annotate(f'Max f1\n({max_f1_point["fitness1"]:.2f}, {max_f1_point["fitness2"]:.2f})',
                xy=(max_f1_point['fitness1'], max_f1_point['fitness2']),
                xytext=(10, -20), textcoords='offset points',
                fontsize=9, color='darkred',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                arrowprops=dict(arrowstyle='->', color='darkred', lw=1.5))

        # Ponto com maior fitness2
        max_f2_point = pareto_df.iloc[-1]
        ax.annotate(f'Max f2\n({max_f2_point["fitness1"]:.2f}, {max_f2_point["fitness2"]:.2f})',
                xy=(max_f2_point['fitness1'], max_f2_point['fitness2']),
                xytext=(10, 20), textcoords='offset points',
                fontsize=9, color='darkred',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                arrowprops=dict(arrowstyle='->', color='darkred', lw=1.5))

        plt.tight_layout()
        plt.show()

        print("\n✅ Visualização concluída!")


        # ============================================================================
        # GRÁFICO 2: Fronteira de Pareto no contexto de todos os pontos com boxplots
        # ============================================================================

        # Subsampling para todos os pontos (para não sobrecarregar o gráfico)
        sample_size = min(500000, len(df))  # Máximo de 50k pontos
        df_sample = df.sample(n=sample_size, random_state=42)

        # Criar figura com subplots usando GridSpec (boxplots mais discretos)
        # Ajustar para figura mais quadrada
        fig = plt.figure(figsize=(12, 12))
        gs = fig.add_gridspec(3, 3, width_ratios=[1, 6, 0.4], height_ratios=[0.4, 6, 1], 
                             hspace=0.02, wspace=0.02)
        
        # Eixo principal (scatter plot)
        ax_main = fig.add_subplot(gs[1, 1])
        
        # Eixos para os boxplots (mais discretos)
        ax_top = fig.add_subplot(gs[0, 1], sharex=ax_main)  # Boxplot fitness1 (topo)
        ax_right = fig.add_subplot(gs[1, 2], sharey=ax_main)  # Boxplot fitness2 (direita)

        # Plotar todos os pontos (amostra) em cinza
        ax_main.scatter(df_sample['fitness1'], df_sample['fitness2'], 
                c='lightgray', s=10, alpha=0.3, 
                label=f'Todos os pontos (amostra de {sample_size:,})', zorder=1)

        # Plotar a fronteira de Pareto em destaque
        ax_main.scatter(pareto_df['fitness1'], pareto_df['fitness2'], 
                c='red', s=80, alpha=0.9, edgecolors='darkred', 
                linewidth=1.5, label='Fronteira de Pareto', zorder=3)

        # Conectar os pontos da fronteira
        ax_main.plot(pareto_df['fitness1'], pareto_df['fitness2'], 
                'r-', alpha=0.6, linewidth=2, zorder=2)

        # Configurações do gráfico principal
        ax_main.set_xlabel('Fitness1 (f1)', fontsize=13, fontweight='bold')
        ax_main.set_ylabel('Fitness2 (f2)', fontsize=13, fontweight='bold')
        ax_main.set_title(f'Fronteira de Pareto no Espaço de Objetivos\n(Problema de Maximização Bi-Objetivo)', 
                fontsize=15, fontweight='bold', pad=20)
        ax_main.legend(fontsize=11, loc='best')
        ax_main.grid(True, alpha=0.3, linestyle='--')
        
        # Definir limites iguais para x e y começando em 0
        ax_main.set_xlim(0, max_limit)
        ax_main.set_ylim(0, max_limit)
        
        # Definir aspect ratio igual (1 cm no x = 1 cm no y)
        ax_main.set_aspect('equal', adjustable='box')

        # Boxplot para Fitness1 da amostra (topo - horizontal, mais discreto)
        bp1 = ax_top.boxplot([df_sample['fitness1']], vert=False, widths=0.5,
                             patch_artist=True, 
                             boxprops=dict(facecolor='lightgray', alpha=0.4, linewidth=0.8),
                             medianprops=dict(color='dimgray', linewidth=1.2),
                             whiskerprops=dict(color='gray', linewidth=0.8),
                             capprops=dict(color='gray', linewidth=0.8),
                             flierprops=dict(marker='o', markersize=2, alpha=0.3))
        ax_top.tick_params(labelbottom=False, labelleft=False, length=0)
        ax_top.set_yticks([])
        ax_top.spines['top'].set_visible(False)
        ax_top.spines['right'].set_visible(False)
        ax_top.spines['left'].set_visible(False)
        
        # Boxplot para Fitness2 da amostra (direita - vertical, mais discreto)
        bp2 = ax_right.boxplot([df_sample['fitness2']], vert=True, widths=0.5,
                               patch_artist=True,
                               boxprops=dict(facecolor='lightgray', alpha=0.4, linewidth=0.8),
                               medianprops=dict(color='dimgray', linewidth=1.2),
                               whiskerprops=dict(color='gray', linewidth=0.8),
                               capprops=dict(color='gray', linewidth=0.8),
                               flierprops=dict(marker='o', markersize=2, alpha=0.3))
        ax_right.tick_params(labelleft=False, labelbottom=False, length=0)
        ax_right.set_xticks([])
        ax_right.spines['top'].set_visible(False)
        ax_right.spines['right'].set_visible(False)
        ax_right.spines['bottom'].set_visible(False)

        plt.show()



def display_fitness_landscape_with_pareto(df, pareto_df=None):
    '''
    Plots comprehensive fitness landscape with Pareto front overlay
    '''
    
    def add_pareto_markers(ax, pareto_df, y_col, marker_color, marker_style='D'):
        """Helper function to add Pareto markers and vertical lines"""
        # Add vertical lines at key Pareto positions
        pareto_sorted = pareto_df.sort_values('registro')
        positions = [0, len(pareto_sorted)//4, len(pareto_sorted)//2, 
                     3*len(pareto_sorted)//4, -1]
        for i in positions:
            ax.axvline(x=pareto_sorted.iloc[i]['registro'], color='red', 
                      alpha=0.3, linewidth=1.5, linestyle='--', zorder=1)
        
        # Add scatter points
        ax.scatter(pareto_df['registro'], pareto_df[y_col], 
                  c=marker_color, s=40 if marker_style=='D' else 50, 
                  alpha=0.9 if marker_style=='D' else 0.95,
                  edgecolors='darkred' if marker_color=='red' else ('black' if marker_color=='darkgreen' else 'darkorange'),
                  linewidth=1.5 if marker_style=='D' else 2,
                  label=f'Pareto Front ({len(pareto_df):,})', 
                  zorder=5, marker=marker_style)
    
    # Configuration for each subplot
    plot_configs = [
        {
            'y_col': 'fitness1',
            'fill_color': 'steelblue',
            'edge_color': 'darkblue',
            'marker_color': 'red',
            'marker_style': 'D',
            'ylabel': 'Fitness1',
            'title': 'Fitness1 Landscape com Pareto Front'
        },
        {
            'y_col': 'fitness2',
            'fill_color': 'coral',
            'edge_color': 'darkred',
            'marker_color': 'darkgreen',
            'marker_style': 'D',
            'ylabel': 'Fitness2',
            'title': 'Fitness2 Landscape com Pareto Front'
        }
    ]
    
    fig, axes = plt.subplots(3, 1, figsize=(16, 14))
    
    # Plot first two subplots (fitness1 and fitness2)
    for ax, config in zip(axes[:2], plot_configs):
        ax.fill_between(df['registro'], df[config['y_col']], alpha=0.5,
                       color=config['fill_color'], edgecolor=config['edge_color'],
                       linewidth=0.5, label='Todos os pontos')
        
        if pareto_df is not None:
            add_pareto_markers(ax, pareto_df, config['y_col'], 
                             config['marker_color'], config['marker_style'])
        
        ax.set_xlabel('Registro (x)', fontsize=12, fontweight='bold')
        ax.set_ylabel(config['ylabel'], fontsize=12, fontweight='bold')
        ax.set_title(config['title'], fontsize=14, fontweight='bold')
        ax.legend(fontsize=10, loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)
    
    # Third subplot (comparison)
    ax = axes[2]
    for col, color, alpha, lw, label in [
        ('fitness_full', 'purple', 0.6, 1, 'Fitness Full (todos)'),
        ('fitness1', 'steelblue', 0.5, 0.8, 'Fitness1 (todos)'),
        ('fitness2', 'coral', 0.5, 0.8, 'Fitness2 (todos)')
    ]:
        ax.plot(df['registro'], df[col], alpha=alpha, color=color, 
               linewidth=lw, label=label)
    
    if pareto_df is not None:
        add_pareto_markers(ax, pareto_df, 'fitness_full', 'gold', '*')
    
    ax.set_xlabel('Registro (x)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Fitness', fontsize=12, fontweight='bold')
    ax.set_title('Comparação Completa: Fitness Full vs Fitness1 vs Fitness2',
                fontsize=14, fontweight='bold')
    ax.legend(fontsize=9, loc='best', framealpha=0.9, ncol=2)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()