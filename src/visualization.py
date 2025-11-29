import matplotlib.pyplot as plt
import math
from matplotlib.gridspec import GridSpec

# Configure matplotlib for better performance with large datasets
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 6)
plt.rcParams['lines.linewidth'] = 0.5


def plota_fitness_landscape_com_equacoes(df, n_regioes=5):
    """
    Plota o fitness landscape com 3 subplots:
    1. Fitness1 e Fitness2 (2.5x altura)
    2. Equações geradoras da Fitness1 (1.5x altura)
    3. Equações geradoras da Fitness2 (1.5x altura)
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataframe contendo as colunas 'registro', 'fitness1', 'fitness2',
        e as equações 'fitness1_eq*' e 'fitness2_eq*'
    n_regioes : int, optional
        Número de regiões para divisão do gráfico (default: 5)
    """
    max_registro = df['registro'].max()
    
    # Cores das regiões
    cores_regioes = ['lightblue', 'lightgreen', 'lightyellow', 'lightcoral', 'lavender']
    
    # Função auxiliar para adicionar regiões coloridas
    def adicionar_regioes_coloridas(ax):
        for i, cor in enumerate(cores_regioes):
            inicio = i * (1 / n_regioes) * max_registro
            fim = (i + 1) * (1 / n_regioes) * max_registro
            ax.axvspan(inicio, fim, color=cor, alpha=0.2, zorder=0)
        for percent in [0.2, 0.4, 0.6, 0.8]:
            ax.axvline(x=max_registro * percent, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    
    # Criar figura com GridSpec - primeiro subplot tem 2.5x a altura dos outros
    fig = plt.figure(figsize=(16, 14))
    gs = GridSpec(3, 1, figure=fig, height_ratios=[2.5, 1.5, 1.5], hspace=0.3)
    
    # ========== SUBPLOT 1: Fitness1 e Fitness2 ==========
    ax1 = fig.add_subplot(gs[0])
    adicionar_regioes_coloridas(ax1)
    
    ax1.plot(df['registro'], df['fitness1'], label='fitness1', linewidth=1.5, color='steelblue')
    ax1.plot(df['registro'], df['fitness2'], label='fitness2', linewidth=1.5, color='coral')
    
    ax1.legend(loc='upper left', fontsize=11)
    ax1.set_ylabel('Fitness', fontweight='bold', fontsize=12)
    ax1.set_title('Fitness Landscape - Fitness1 e Fitness2', fontweight='bold', fontsize=13)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, max_registro)
    
    # ========== SUBPLOT 2: Equações geradoras da Fitness1 ==========
    ax2 = fig.add_subplot(gs[1])
    adicionar_regioes_coloridas(ax2)
    
    fitness1_eq_cols = [col for col in df.columns if 'fitness1_eq' in col]
    for col in fitness1_eq_cols:
        ax2.plot(df['registro'], df[col], label=col, alpha=0.7, linewidth=0.8)
    
    ax2.legend(loc='upper right', fontsize=8, ncol=3)
    ax2.set_ylabel('Equações Fitness1', fontweight='bold', fontsize=11)
    ax2.set_title('Equações Geradoras da Fitness1', fontweight='bold', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, max_registro)
    
    # ========== SUBPLOT 3: Equações geradoras da Fitness2 ==========
    ax3 = fig.add_subplot(gs[2])
    adicionar_regioes_coloridas(ax3)
    
    fitness2_eq_cols = [col for col in df.columns if 'fitness2_eq' in col]
    for col in fitness2_eq_cols:
        ax3.plot(df['registro'], df[col], label=col, alpha=0.7, linewidth=0.8)
    
    ax3.legend(loc='upper right', fontsize=8, ncol=3)
    ax3.set_xlabel('Registro', fontweight='bold', fontsize=12)
    ax3.set_ylabel('Equações Fitness2', fontweight='bold', fontsize=11)
    ax3.set_title('Equações Geradoras da Fitness2', fontweight='bold', fontsize=12)
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, max_registro)
    
    plt.tight_layout()
    plt.show()


def display_pareto_front(df, pareto_df):

        # ============================================================================
        # Calcular limites comuns para ambos os gráficos
        # ============================================================================
        
        # Encontrar o máximo entre fitness1 e fitness2 de todos os pontos
        max_fitness = max(df['fitness1'].max(), df['fitness2'].max())
        # Arredondar para cima para um valor "bonito"
        max_limit = math.ceil(max_fitness / 2) * 2
        
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







def dividir_plot_regioes(plt, df3, n_regioes):

    # Adicionar áreas coloridas a cada 20% do eixo x
    max_registro = df3['registro'].max()
    cores = ['lightblue', 'lightgreen', 'lightyellow', 'lightcoral', 'lavender']

    for i, cor in enumerate(cores):
        inicio = i * (1 / n_regioes) * max_registro
        fim = (i + 1) * (1 / n_regioes) * max_registro
        plt.axvspan(inicio, fim, color=cor, alpha=0.2, zorder=0)

    # Adicionar linhas verticais a cada 20% do eixo x
    for percent in [0.2, 0.4, 0.6, 0.8, 1]:
        plt.axvline(x=max_registro * percent, color='gray', linestyle='--', linewidth=1, alpha=0.5)

    return plt



def adicionar_wape_por_regiao(plt, df, col_real, col_previsto, n_regioes):
    """
    Calcula e adiciona os valores de WAPE por região no gráfico.
    
    Parameters:
    -----------
    plt : matplotlib.pyplot
        Objeto pyplot do matplotlib
    df : pd.DataFrame
        Dataframe contendo os dados
    col_real : str
        Nome da coluna com valores reais
    col_previsto : str
        Nome da coluna com valores previstos
        
    Returns:
    --------
    plt : matplotlib.pyplot
        Objeto pyplot atualizado com as anotações de WAPE
    """
    import numpy as np
    
    # Obter o registro máximo
    max_registro = df['registro'].max()
    
    # Calcular denominador global (média de toda a base)
    denominador_global = df[col_real].mean()
    
    # Calcular WAPE para cada região (5 regiões de 20% cada)
    wapes = []
    
    for i in range(n_regioes):
        # Definir limites da região
        inicio = i * (1 / n_regioes) * max_registro
        fim = (i + 1) * (1 / n_regioes) * max_registro
        
        # Filtrar dados da região
        df_regiao = df[(df['registro'] >= inicio) & (df['registro'] < fim)]
        
        # Calcular WAPE: mean(abs(real-previsto))/mean(real de toda a base)
        erro_abs = np.abs(df_regiao[col_real] - df_regiao[col_previsto])
        wape = round(100 * erro_abs.mean() / denominador_global, 1)
        wapes.append(wape)
        
        # Posição no meio da região para adicionar o texto
        posicao_x = (inicio + fim) / 2
        
        # Pegar o valor máximo do y para posicionar o texto no topo
        y_max = plt.gca().get_ylim()[1]
        posicao_y = y_max * 0.95  # 95% da altura do gráfico
        
        # Adicionar texto com o valor do WAPE
        plt.text(posicao_x, posicao_y, 
                f'WAPE: {wape:.1f} %',
                horizontalalignment='center',
                verticalalignment='top',
                fontsize=10,
                fontweight='bold',
                #bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='black', alpha=0.7)
                )
    
    return plt


def adicionar_wape_amostragem_por_regiao(plt, df, col_real, col_previsto, df_amostragem, col_cenario, n_regioes):
    """
    Calcula e adiciona os valores de WAPE e percentuais de amostragem por região no gráfico.
    
    Parameters:
    -----------
    plt : matplotlib.pyplot
        Objeto pyplot do matplotlib
    df : pd.DataFrame
        Dataframe contendo os dados de fitness
    col_real : str
        Nome da coluna com valores reais
    col_previsto : str
        Nome da coluna com valores previstos
    df_amostragem : pd.DataFrame
        Dataframe contendo as taxas de amostragem por região
    col_cenario : str
        Nome da coluna do cenário de amostragem (ex: 'cenario1', 'cenario2', etc)
    n_regioes : int
        Número de regiões para divisão
        
    Returns:
    --------
    plt : matplotlib.pyplot
        Objeto pyplot atualizado com as anotações de WAPE e amostragem
    """
    import numpy as np
    
    # Obter o registro máximo
    max_registro = df['registro'].max()
    
    # Calcular denominador global (média de toda a base)
    denominador_global = df[col_real].mean()
    
    # Calcular WAPE para cada região
    wapes = []
    
    for i in range(n_regioes):
        # Definir limites da região
        inicio = i * (1 / n_regioes) * max_registro
        fim = (i + 1) * (1 / n_regioes) * max_registro
        
        # Filtrar dados da região
        df_regiao = df[(df['registro'] >= inicio) & (df['registro'] < fim)]
        
        # Calcular erros
        erros = df_regiao[col_previsto] - df_regiao[col_real]
        
        # Calcular WAPE: mean(abs(erro))/mean(real de toda a base)
        erro_abs = np.abs(erros)
        wape = round(100 * erro_abs.mean() / denominador_global, 1)
        wapes.append(wape)
        
        # Calcular WAPE de sub-previsão: mean(erros negativos)/mean(real de toda a base)
        erros_sub = erros[erros < 0]
        wape_sub = round(100 * erros_sub.mean() / denominador_global, 1) if len(erros_sub) > 0 else 0
        
        # Calcular WAPE de sobre-previsão: mean(erros positivos)/mean(real de toda a base)
        erros_sobre = erros[erros > 0]
        wape_sobre = round(100 * erros_sobre.mean() / denominador_global, 1) if len(erros_sobre) > 0 else 0
        
        # Obter percentual de amostragem da região
        if i < len(df_amostragem):
            taxa_amostragem = df_amostragem.loc[i, col_cenario] * 100  # Converter para percentual
        else:
            taxa_amostragem = 0
        
        # Posição no meio da região para adicionar o texto
        posicao_x = (inicio + fim) / 2
        
        # Pegar o valor máximo do y para posicionar o texto no topo
        y_max = plt.gca().get_ylim()[1]
        y_min = plt.gca().get_ylim()[0]
        altura_grafico = y_max - y_min
        
        # Posição dos textos (ajustadas para incluir mais informações)
        posicao_y_wape = y_max * 0.95
        posicao_y_wape_sub = y_max * 0.90
        posicao_y_wape_sobre = y_max * 0.85
        posicao_y_amostragem = y_max * 0.80
        
        # Adicionar texto com o valor do WAPE
        plt.text(posicao_x, posicao_y_wape, 
                f'WAPE: {wape:.1f}%',
                horizontalalignment='center',
                verticalalignment='top',
                fontsize=9,
                fontweight='bold',
                color='darkblue')
        
        # Adicionar texto com WAPE de sub-previsão
        plt.text(posicao_x, posicao_y_wape_sub, 
                f'Sub: {wape_sub:.1f}%',
                horizontalalignment='center',
                verticalalignment='top',
                fontsize=8,
                fontweight='normal',
                color='red')
        
        # Adicionar texto com WAPE de sobre-previsão
        plt.text(posicao_x, posicao_y_wape_sobre, 
                f'Sobre: {wape_sobre:.1f}%',
                horizontalalignment='center',
                verticalalignment='top',
                fontsize=8,
                fontweight='normal',
                color='orange')
        
        # Adicionar texto com o percentual de amostragem
        plt.text(posicao_x, posicao_y_amostragem, 
                f'Amost: {taxa_amostragem:.2f}%',
                horizontalalignment='center',
                verticalalignment='top',
                fontsize=8,
                fontweight='normal',
                color='darkgreen',
                style='italic')
    
    return plt







def criar_plot_base(df3, features):
    plt.figure()
    plt.plot(df3['registro'], df3['fitness1'], label='fitness1_real')
    dividir_plot_regioes(plt, df3, n_regioes=5)
    # Features (skip categorical/string columns)
    for col in features:
        if df3[col].dtype in ['object', 'string', 'category']:
            continue
        plt.plot(df3['registro'], df3[col], label=col)


def plota_landscape_cenario(df3, features, df_amostragem, cenario='c1', fitness_num=1):
    """
    Plota o landscape de um cenário específico para um fitness específico.
    
    Parameters:
    -----------
    df3 : pd.DataFrame
        Dataframe contendo os dados de fitness real e previsão
    features : list
        Lista de features utilizadas no modelo
    df_amostragem : pd.DataFrame
        Dataframe com as taxas de amostragem por região
    cenario : str, optional
        Cenário a ser plotado: 'c1', 'c2' ou 'c3' (default: 'c1')
    fitness_num : int, optional
        Número do fitness/objetivo: 1 ou 2 (default: 1)
    """
    import numpy as np
    from matplotlib.gridspec import GridSpec
    
    n_regioes = 5
    max_registro = df3['registro'].max()
    
    # Cores para os cenários
    cores_cenarios = {
        'c1': 'blue',
        'c2': 'green', 
        'c3': 'red'
    }
    
    # Cores das regiões
    cores_regioes = ['lightblue', 'lightgreen', 'lightyellow', 'lightcoral', 'lavender']
    
    # Definir nomes de colunas baseado no fitness
    col_fitness_real = f'fitness{fitness_num}'
    col_fitness_previsto = f'fitness{fitness_num}_{cenario}'
    col_erro = f'erro_{cenario}_f{fitness_num}'
    col_cenario_amostragem = f'cenario{cenario[1]}'  # Extrai o número do cenário (c1 -> cenario1)
    
    # Verificar se as colunas existem
    if col_fitness_real not in df3.columns:
        raise ValueError(f"Coluna '{col_fitness_real}' não encontrada no dataframe")
    if col_fitness_previsto not in df3.columns:
        raise ValueError(f"Coluna '{col_fitness_previsto}' não encontrada no dataframe")
    
    # Calcular coluna de erro se não existir
    if col_erro not in df3.columns:
        df3[col_erro] = df3[col_fitness_previsto] - df3[col_fitness_real]
    
    # Função auxiliar para adicionar regiões coloridas
    def adicionar_regioes_coloridas(ax):
        for i, cor in enumerate(cores_regioes):
            inicio = i * (1 / n_regioes) * max_registro
            fim = (i + 1) * (1 / n_regioes) * max_registro
            ax.axvspan(inicio, fim, color=cor, alpha=0.2, zorder=0)
        for percent in [0.2, 0.4, 0.6, 0.8]:
            ax.axvline(x=max_registro * percent, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    
    # Função auxiliar para calcular métricas por região
    def calcular_metricas_por_regiao(df, col_real, col_previsto):
        metricas = []
        # Calcular denominador global (média de toda a base)
        denominador_global = df[col_real].mean()
        
        for i in range(n_regioes):
            inicio = i * (1 / n_regioes) * max_registro
            fim = (i + 1) * (1 / n_regioes) * max_registro
            df_regiao = df[(df['registro'] >= inicio) & (df['registro'] < fim)]
            
            erros = df_regiao[col_previsto] - df_regiao[col_real]
            erro_abs = np.abs(erros)
            wape = 100 * erro_abs.mean() / denominador_global
            
            erros_sub = erros[erros < 0]
            wape_sub = 100 * erros_sub.mean() / denominador_global if len(erros_sub) > 0 else 0
            
            erros_sobre = erros[erros > 0]
            wape_sobre = 100 * erros_sobre.mean() / denominador_global if len(erros_sobre) > 0 else 0
            
            # Buscar taxa de amostragem no dataframe
            if col_cenario_amostragem in df_amostragem.columns and i < len(df_amostragem):
                taxa_amostragem = df_amostragem.loc[i, col_cenario_amostragem] * 100
            else:
                taxa_amostragem = 0
            
            metricas.append({
                'wape': wape,
                'wape_sub': wape_sub,
                'wape_sobre': wape_sobre,
                'taxa_amostragem': taxa_amostragem
            })
        return metricas
    
    # Calcular métricas
    metricas = calcular_metricas_por_regiao(df3, col_fitness_real, col_fitness_previsto)
    
    # Criar figura com 5 subplots
    fig = plt.figure(figsize=(16, 16))
    gs = GridSpec(5, 1, figure=fig, height_ratios=[2.3, 1, 0.3, 0.8, 1], hspace=0.3)
    
    # ========== SUBFIGURA 1: Landscape (fitness real + previsto) ==========
    ax1 = fig.add_subplot(gs[0])
    adicionar_regioes_coloridas(ax1)
    ax1.plot(df3['registro'], df3[col_fitness_real], label=f'{col_fitness_real}_real', linewidth=1.5, color='black')
    ax1.plot(df3['registro'], df3[col_fitness_previsto], label=f'previsao_{cenario}', linewidth=1.5, color=cores_cenarios[cenario], alpha=0.25)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.set_ylabel('Fitness', fontweight='bold')
    ax1.set_title(f'Cenário {cenario.upper()} - Fitness{fitness_num} Real vs Previsto', fontweight='bold', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, max_registro)
    
    # ========== SUBFIGURA 2: Features ==========
    ax2 = fig.add_subplot(gs[1])
    adicionar_regioes_coloridas(ax2)
    for col in features:
        if df3[col].dtype in ['object', 'string', 'category']:
            continue
        ax2.plot(df3['registro'], df3[col], label=col, alpha=0.7)
    ax2.legend(loc='upper right', fontsize=8, ncol=2)
    ax2.set_ylabel('Features', fontweight='bold')
    ax2.set_title('Features Utilizadas no Modelo', fontweight='bold', fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, max_registro)
    
    # ========== SUBFIGURA 3: Textos WAPE e Amostragem ==========
    ax3 = fig.add_subplot(gs[2])
    adicionar_regioes_coloridas(ax3)
    ax3.set_xlim(0, max_registro)
    ax3.set_ylim(0, 1)
    ax3.axis('off')  # Remover eixos
    
    # Adicionar textos de WAPE e Amostragem
    posicoes_barras = [(i + 0.5) * (1 / n_regioes) * max_registro for i in range(n_regioes)]
    wapes_geral = [m['wape'] for m in metricas]
    taxas_amost = [m['taxa_amostragem'] for m in metricas]
    
    for pos, wape_g, taxa_amost in zip(posicoes_barras, wapes_geral, taxas_amost):
        ax3.text(pos, 0.5, f'WAPE: {wape_g:.0f}%\nAmost: {taxa_amost:.0f}%', 
                ha='center', va='center', fontsize=13, fontweight='bold', color='darkblue',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='lightgray', alpha=0.9))
    
    # ========== SUBFIGURA 4: Gráfico de barras WAPE ==========
    ax4 = fig.add_subplot(gs[3])
    adicionar_regioes_coloridas(ax4)
    
    largura_barra = 0.15 * (1 / n_regioes) * max_registro
    
    wapes_sub = [m['wape_sub'] for m in metricas]
    wapes_sobre = [m['wape_sobre'] for m in metricas]
    
    ax4.bar(posicoes_barras, wapes_sub, width=largura_barra, 
            color='darkblue', alpha=0.8, label='WAPE Sub', edgecolor='navy', linewidth=1.5)
    ax4.bar(posicoes_barras, wapes_sobre, width=largura_barra, 
            color='lightblue', alpha=0.8, label='WAPE Sobre', edgecolor='steelblue', linewidth=1.5)
    
    for i, (pos, wape_sub_val, wape_sobre_val) in enumerate(zip(posicoes_barras, wapes_sub, wapes_sobre)):
        if abs(wape_sub_val) > 2:
            ax4.text(pos, wape_sub_val/2, f'{abs(wape_sub_val):.0f}%', 
                    ha='center', va='center', fontsize=9, fontweight='bold', color='white')
        if abs(wape_sobre_val) > 2:
            ax4.text(pos, wape_sobre_val/2, f'{abs(wape_sobre_val):.0f}%', 
                    ha='center', va='center', fontsize=9, fontweight='bold', color='darkblue')
    
    ax4.set_ylabel('WAPE (%)', fontweight='bold')
    ax4.set_title('WAPE por Região (Sub-previsão e Sobre-previsão)', fontweight='bold', fontsize=11)
    ax4.axhline(y=0, color='black', linewidth=0.8, linestyle='-')
    ax4.legend(loc='upper left', fontsize=8)
    ax4.grid(True, alpha=0.3, axis='y')
    ax4.set_xlim(0, max_registro)
    
    # ========== SUBFIGURA 5: Distribuições de erro ==========
    ax5 = fig.add_subplot(gs[4])
    
    # Determinar cor baseada no cenário
    cor_distribuicao = cores_cenarios[cenario]
    cor_linha = {'c1': 'darkblue', 'c2': 'darkgreen', 'c3': 'darkred'}.get(cenario, 'darkblue')
    
    for i in range(n_regioes):
        inicio = i * (1 / n_regioes) * max_registro
        fim = (i + 1) * (1 / n_regioes) * max_registro
        df_regiao = df3[(df3['registro'] >= inicio) & (df3['registro'] < fim)]
        
        ax5.axvspan(inicio, fim, color=cores_regioes[i], alpha=0.2, zorder=0)
        
        erros = df_regiao[col_erro].values
        
        if len(erros) > 0:
            counts, bin_edges = np.histogram(erros, bins=30)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            counts_norm = counts / counts.max() if counts.max() > 0 else counts
            largura_regiao = fim - inicio
            x_positions = inicio + (bin_centers - bin_centers.min()) / (bin_centers.max() - bin_centers.min() + 1e-10) * largura_regiao * 0.9
            x_positions += largura_regiao * 0.05
            
            ax5.fill_between(x_positions, 0, counts_norm, alpha=0.6, color=cor_distribuicao)
            ax5.plot(x_positions, counts_norm, color=cor_linha, linewidth=1.5, alpha=0.8)
    
    ax5.set_xlabel('Registro', fontweight='bold')
    ax5.set_ylabel('Densidade Normalizada', fontweight='bold')
    ax5.set_title('Distribuição dos Erros por Região', fontweight='bold', fontsize=11)
    ax5.set_xlim(0, max_registro)
    ax5.grid(True, alpha=0.3)
    
    for percent in [0.2, 0.4, 0.6, 0.8]:
        ax5.axvline(x=max_registro * percent, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    
    plt.tight_layout()
    plt.show()


def plota_landscape_5cenarios(df3, features, df_amostragem):
    """
    DEPRECATED: Use plota_landscape_cenario() em vez desta função.
    
    Esta função plota os 3 cenários chamando plota_landscape_cenario() 3 vezes.
    """
    print("⚠️  AVISO: Esta função está deprecated. Use plota_landscape_cenario() para plotar cenários individuais.")
    
    # Plotar cada cenário individualmente
    for cenario in ['c1', 'c2', 'c3']:
        plota_landscape_cenario(df3, features, df_amostragem, cenario=cenario, fitness_num=1)


def display_two_pareto_fronts(df_real, pareto_real, pareto_surrogate):
    """
    Mostra dois fronts de Pareto (real e surrogate) sobre a fitness landscape verdadeira.
    
    Parameters:
    -----------
    df_real : pd.DataFrame
        Dataframe com a fitness landscape verdadeira (todos os pontos)
    pareto_real : pd.DataFrame
        Dataframe com o front de Pareto verdadeiro
    pareto_surrogate : pd.DataFrame
        Dataframe com o front de Pareto encontrado pelo surrogate
    """
    
    # ============================================================================
    # Calcular limites comuns para ambos os gráficos
    # ============================================================================
    
    # Encontrar o máximo entre fitness1 e fitness2 de todos os pontos
    max_fitness = max(df_real['fitness1'].max(), df_real['fitness2'].max())
    # Arredondar para cima para um valor "bonito"
    max_limit = math.ceil(max_fitness / 2) * 2
    
    # ============================================================================
    # GRÁFICO 1: Dois Fronts de Pareto
    # ============================================================================
    
    # Gráfico de dispersão dos dois fronts (figura quadrada)
    fig, ax = plt.subplots(figsize=(10, 10))

    # Plotar o front verdadeiro
    ax.scatter(pareto_real['fitness1'], pareto_real['fitness2'], 
            c='red', s=50, alpha=0.7, edgecolors='darkred', 
            linewidth=1.5, label=f'Front Verdadeiro ({len(pareto_real)} pts)', zorder=3)

    # Conectar os pontos do front verdadeiro
    ax.plot(pareto_real['fitness1'], pareto_real['fitness2'], 
            'r--', alpha=0.4, linewidth=1, zorder=2)

    # Plotar o front encontrado pelo surrogate
    ax.scatter(pareto_surrogate['fitness1'], pareto_surrogate['fitness2'], 
            c='blue', s=50, alpha=0.7, edgecolors='darkblue', 
            linewidth=1.5, label=f'Front Surrogate ({len(pareto_surrogate)} pts)', zorder=3)

    # Conectar os pontos do front surrogate
    ax.plot(pareto_surrogate['fitness1'], pareto_surrogate['fitness2'], 
            'b--', alpha=0.4, linewidth=1, zorder=2)

    # Configurações do gráfico
    ax.set_xlabel('Fitness1 (f1)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Fitness2 (f2)', fontsize=13, fontweight='bold')
    ax.set_title(f'Comparação dos Fronts de Pareto na Landscape Verdadeira\n(Vermelho = Real, Azul = Encontrado pelo Surrogate)', 
            fontsize=15, fontweight='bold', pad=20)
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Definir limites iguais para x e y começando em 0
    ax.set_xlim(0, max_limit)
    ax.set_ylim(0, max_limit)
    
    # Definir aspect ratio igual (1 cm no x = 1 cm no y)
    ax.set_aspect('equal', adjustable='box')

    # Adicionar anotações para os pontos extremos do front verdadeiro
    # Ponto com maior fitness1
    max_f1_point = pareto_real.iloc[0]
    ax.annotate(f'Max f1 (Real)\n({max_f1_point["fitness1"]:.2f}, {max_f1_point["fitness2"]:.2f})',
            xy=(max_f1_point['fitness1'], max_f1_point['fitness2']),
            xytext=(10, -20), textcoords='offset points',
            fontsize=9, color='darkred',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
            arrowprops=dict(arrowstyle='->', color='darkred', lw=1.5))

    # Ponto com maior fitness2
    max_f2_point = pareto_real.iloc[-1]
    ax.annotate(f'Max f2 (Real)\n({max_f2_point["fitness1"]:.2f}, {max_f2_point["fitness2"]:.2f})',
            xy=(max_f2_point['fitness1'], max_f2_point['fitness2']),
            xytext=(10, 20), textcoords='offset points',
            fontsize=9, color='darkred',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
            arrowprops=dict(arrowstyle='->', color='darkred', lw=1.5))

    plt.tight_layout()
    plt.show()

    print("\n✅ Visualização concluída!")

    # ============================================================================
    # GRÁFICO 2: Dois Fronts no contexto de todos os pontos com boxplots
    # ============================================================================

    # Subsampling para todos os pontos (para não sobrecarregar o gráfico)
    sample_size = min(500000, len(df_real))  # Máximo de 500k pontos
    df_sample = df_real.sample(n=sample_size, random_state=42)

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

    # Plotar o front verdadeiro em destaque
    ax_main.scatter(pareto_real['fitness1'], pareto_real['fitness2'], 
            c='red', s=80, alpha=0.9, edgecolors='darkred', 
            linewidth=1.5, label=f'Front Verdadeiro ({len(pareto_real)} pts)', zorder=3)

    # Conectar os pontos do front verdadeiro
    ax_main.plot(pareto_real['fitness1'], pareto_real['fitness2'], 
            'r-', alpha=0.6, linewidth=2, zorder=2)

    # Plotar o front surrogate em destaque
    ax_main.scatter(pareto_surrogate['fitness1'], pareto_surrogate['fitness2'], 
            c='blue', s=80, alpha=0.9, edgecolors='darkblue', 
            linewidth=1.5, label=f'Front Surrogate ({len(pareto_surrogate)} pts)', zorder=3)

    # Conectar os pontos do front surrogate
    ax_main.plot(pareto_surrogate['fitness1'], pareto_surrogate['fitness2'], 
            'b-', alpha=0.6, linewidth=2, zorder=2)

    # Configurações do gráfico principal
    ax_main.set_xlabel('Fitness1 (f1)', fontsize=13, fontweight='bold')
    ax_main.set_ylabel('Fitness2 (f2)', fontsize=13, fontweight='bold')
    ax_main.set_title(f'Comparação dos Fronts de Pareto no Espaço de Objetivos\n(Problema de Maximização Bi-Objetivo)', 
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

def display_fitness_landscape_with_2pareto(df, pareto_real, pareto_surrogate):
    '''
    Plots fitness landscape with two Pareto fronts (real and surrogate)
    and predicted landscapes with transparency.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with real and predicted fitness landscapes
        Required columns: registro, fitness1, fitness2, fitness_full
        Optional columns: fitness1_c1, fitness2_c1 (predicted landscapes)
    pareto_real : pd.DataFrame
        DataFrame with real Pareto front (must have 'registro' column to match with df)
    pareto_surrogate : pd.DataFrame
        DataFrame with surrogate Pareto front (must have 'registro' column to match with df)
    '''
    
    def add_pareto_markers(ax, pareto_df, df_main, y_col, marker_color, marker_style='D', label_suffix='', edge_color=None):
        """Helper function to add Pareto markers using ORIGINAL landscape values"""
        # Merge pareto with main df to get original fitness values at those registro positions
        pareto_with_values = pareto_df.merge(df_main[['registro', y_col]], on='registro', how='left', suffixes=('', '_original'))
        
        # Use the original values from the main df
        if y_col + '_original' in pareto_with_values.columns:
            y_values = pareto_with_values[y_col + '_original']
        else:
            y_values = pareto_with_values[y_col]
        
        # Add vertical lines at key Pareto positions
        pareto_sorted = pareto_with_values.sort_values('registro')
        positions = [0, len(pareto_sorted)//4, len(pareto_sorted)//2, 
                     3*len(pareto_sorted)//4, -1]
        for i in positions:
            ax.axvline(x=pareto_sorted.iloc[i]['registro'], color='red', 
                      alpha=0.3, linewidth=1.5, linestyle='--', zorder=1)
        
        # Determine edge color
        if edge_color is None:
            if marker_color == 'red':
                edge_color = 'darkred'
            elif marker_color == 'royalblue':
                edge_color = 'darkblue'
            elif marker_color == 'green':
                edge_color = 'darkgreen'
            elif marker_color == 'darkgreen':
                edge_color = 'black'
            elif marker_color == 'gold':
                edge_color = 'red'  # Gold markers with red edge
            else:
                edge_color = 'darkorange'
        
        # Add scatter points at ORIGINAL fitness values
        ax.scatter(pareto_with_values['registro'], y_values, 
                  c=marker_color, s=40 if marker_style=='D' else 50, 
                  alpha=0.9 if marker_style=='D' else 0.95,
                  edgecolors=edge_color,
                  linewidth=1.5 if marker_style=='D' else 2,
                  label=f'Pareto {label_suffix} ({len(pareto_df):,})', 
                  zorder=5, marker=marker_style)
    
    # Configuration for the first two subplots (fitness1 and fitness2)
    plot_configs = [
        {
            'y_col': 'fitness1',
            'y_col_pred': 'fitness1_c1',
            'fill_color': 'steelblue',
            'edge_color': 'darkblue',
            'pred_color': 'darkorange',  # Different color for predicted
            'pareto_real_color': 'red',
            'pareto_surrogate_color': 'royalblue',
            'marker_style': 'D',
            'ylabel': 'Fitness1',
            'title': 'Fitness1 Landscape: Ótimos Verdadeiros e Encontrados'
        },
        {
            'y_col': 'fitness2',
            'y_col_pred': 'fitness2_c1',
            'fill_color': 'coral',
            'edge_color': 'darkred',
            'pred_color': 'darkturquoise',  # Different color for predicted
            'pareto_real_color': 'red',
            'pareto_surrogate_color': 'royalblue',
            'marker_style': 'D',
            'ylabel': 'Fitness2',
            'title': 'Fitness2 Landscape: Ótimos Verdadeiros e Encontrados'
        }
    ]
    
    fig, axes = plt.subplots(3, 1, figsize=(16, 14))
    
    # ========== SUBFIGURAS 1 e 2: Fitness1 e Fitness2 ==========
    for ax, config in zip(axes[:2], plot_configs):
        # Plot real landscape (filled area)
        ax.fill_between(df['registro'], df[config['y_col']], alpha=0.5,
                       color=config['fill_color'], edgecolor=config['edge_color'],
                       linewidth=0.5, label='Landscape verdadeira')
        
        # Plot predicted landscape LINE with 50% transparency (ADDED)
        if config['y_col_pred'] in df.columns:
            ax.plot(df['registro'], df[config['y_col_pred']], 
                   alpha=0.5, color=config['pred_color'], linewidth=1.5, 
                   linestyle='--', label='Landscape prevista', zorder=2)
        
        # Add Pareto front markers - real (ótimos verdadeiros) - using ORIGINAL values
        add_pareto_markers(ax, pareto_real, df, config['y_col'], 
                         config['pareto_real_color'], config['marker_style'], 
                         label_suffix='Verdadeiro')
        
        # Add Pareto front markers - surrogate (ótimos encontrados) - using ORIGINAL values
        add_pareto_markers(ax, pareto_surrogate, df, config['y_col'], 
                         config['pareto_surrogate_color'], 'D', 
                         label_suffix='Encontrado')
        
        ax.set_xlabel('Registro (x)', fontsize=12, fontweight='bold')
        ax.set_ylabel(config['ylabel'], fontsize=12, fontweight='bold')
        ax.set_title(config['title'], fontsize=14, fontweight='bold')
        ax.legend(fontsize=10, loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)
    
    # ========== SUBFIGURA 3: Comparação completa ==========
    ax = axes[2]
    
    # Plot real landscapes (all three)
    for col, color, alpha, lw, label in [
        ('fitness_full', 'purple', 0.6, 1.5, 'Fitness Full (verdadeira)'),
        ('fitness1', 'steelblue', 0.5, 1, 'Fitness1 (verdadeira)'),
        ('fitness2', 'coral', 0.5, 1, 'Fitness2 (verdadeira)')
    ]:
        ax.plot(df['registro'], df[col], alpha=alpha, color=color, 
               linewidth=lw, label=label, zorder=2)
    
    # Plot predicted fitness_full LINE (fitness1_c1 + fitness2_c1) with transparency (ADDED)
    if 'fitness1_c1' in df.columns and 'fitness2_c1' in df.columns:
        # Calculate predicted full fitness (sum of predicted f1 and f2)
        fitness_full_pred = df['fitness1_c1'] + df['fitness2_c1']
        ax.plot(df['registro'], fitness_full_pred, 
               alpha=0.5, color='darkorange', linewidth=1.5, 
               linestyle='--', label='Fitness Full (prevista)', zorder=1)
    
    # Add Pareto markers for real front (ótimos verdadeiros) - using ORIGINAL values
    # Red diamond markers (STANDARDIZED across all figures)
    add_pareto_markers(ax, pareto_real, df, 'fitness_full', 'red', 'D', 
                     label_suffix='Verdadeiro', edge_color='darkred')
    
    # Add Pareto markers for surrogate front (ótimos encontrados) - using ORIGINAL values
    # Royal blue diamond markers (STANDARDIZED across all figures)
    add_pareto_markers(ax, pareto_surrogate, df, 'fitness_full', 'royalblue', 'D', 
                     label_suffix='Encontrado', edge_color='darkblue')
    
    ax.set_xlabel('Registro (x)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Fitness', fontsize=12, fontweight='bold')
    ax.set_title('Comparação Completa: Landscapes Verdadeiras e Previstas com Ótimos',
                fontsize=14, fontweight='bold')
    ax.legend(fontsize=9, loc='best', framealpha=0.9, ncol=2)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
