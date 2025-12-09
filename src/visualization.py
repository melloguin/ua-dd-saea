import matplotlib.pyplot as plt
import math
import numpy as np
from matplotlib.gridspec import GridSpec
from scipy import stats as scipy_stats
from src.nsga2.evaluation import genotype_to_registro
from src.nsga2.evaluation import evaluate_population
import matplotlib.pyplot as plt

# Configure matplotlib for better performance with large datasets
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 6)
plt.rcParams['lines.linewidth'] = 0.5


def plota_fitness_landscape_com_equacoes(df, n_regioes=5, show_regions=True, 
                                         pareto_fronts_list=None, front_names=None):
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
    show_regions : bool, optional
        Se True, mostra as regiões coloridas no fundo (default: True)
    pareto_fronts_list : list of pd.DataFrame, optional
        Lista de dataframes com fronts de Pareto para plotar bolinhas (default: None)
    front_names : list of str, optional
        Lista de nomes personalizados para cada front na legenda (default: None)
    """
    max_registro = df['registro'].max()
    
    # Gerar cores dinamicamente baseado no número de regiões
    # Usar colormap 'tab20' que tem 20 cores distintas
    import matplotlib.cm as cm
    cmap = cm.get_cmap('tab20', n_regioes)
    cores_regioes = [cmap(i) for i in range(n_regioes)]
    
    # Função auxiliar para adicionar regiões coloridas
    def adicionar_regioes_coloridas(ax):
        if not show_regions:
            return
        for i in range(n_regioes):
            inicio = i * (1 / n_regioes) * max_registro
            fim = (i + 1) * (1 / n_regioes) * max_registro
            ax.axvspan(inicio, fim, color=cores_regioes[i], alpha=0.2, zorder=0)
        # Gerar linhas verticais dinamicamente baseado no número de regiões
        for i in range(1, n_regioes):
            percent = i / n_regioes
            ax.axvline(x=max_registro * percent, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    
    # Criar figura com GridSpec - primeiro subplot tem 2.5x a altura dos outros
    fig = plt.figure(figsize=(16, 14))
    gs = GridSpec(3, 1, figure=fig, height_ratios=[2.5, 1.5, 1.5], hspace=0.3)
    
    # ========== SUBPLOT 1: Fitness1 e Fitness2 ==========
    ax1 = fig.add_subplot(gs[0])
    adicionar_regioes_coloridas(ax1)
    
    ax1.plot(df['registro'], df['fitness1'], label='fitness1', linewidth=1.5, color='steelblue')
    ax1.plot(df['registro'], df['fitness2'], label='fitness2', linewidth=1.5, color='coral')
    
    # Plotar fronts de Pareto se fornecidos
    if pareto_fronts_list is not None and len(pareto_fronts_list) > 0:
        # Cores para os fronts (mesmas de display_pareto_fronts3)
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan', 'magenta', 'yellow']
        dark_colors = ['darkred', 'darkblue', 'darkgreen', 'darkorange', 'darkviolet', 'saddlebrown', 'deeppink', 'darkcyan', 'darkmagenta', 'gold']
        
        # Se não foram fornecidos nomes, usar nomes padrão
        if front_names is None:
            front_names = [f'Front {i+1}' for i in range(len(pareto_fronts_list))]
        
        # Plotar cada front
        for i, pareto_front in enumerate(pareto_fronts_list):
            color = colors[i % len(colors)]
            dark_color = dark_colors[i % len(dark_colors)]
            
            # Para cada ponto, usar o maior valor entre fitness1 e fitness2
            # Isso faz a bolinha aparecer sempre na linha mais alta
            fitness_max = pareto_front[['fitness1', 'fitness2']].max(axis=1)
            
            # Plotar bolinhas sempre na linha mais alta
            ax1.scatter(pareto_front['registro'], fitness_max, 
                       c=color, s=30, alpha=0.9, edgecolors=dark_color, 
                       linewidth=1.2, label=f'{front_names[i]} ({len(pareto_front)} pts)', 
                       zorder=5+i, marker='D')
    
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
    
    return fig


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

    # Adicionar áreas coloridas dinamicamente baseado no número de regiões
    max_registro = df3['registro'].max()
    
    # Gerar cores dinamicamente usando colormap
    import matplotlib.cm as cm
    cmap = cm.get_cmap('tab20', n_regioes)
    cores = [cmap(i) for i in range(n_regioes)]

    for i in range(n_regioes):
        inicio = i * (1 / n_regioes) * max_registro
        fim = (i + 1) * (1 / n_regioes) * max_registro
        plt.axvspan(inicio, fim, color=cores[i], alpha=0.2, zorder=0)

    # Adicionar linhas verticais dinamicamente baseado no número de regiões
    for i in range(1, n_regioes + 1):
        percent = i / n_regioes
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







def criar_plot_base(df3, features, n_regioes=10):
    plt.figure()
    plt.plot(df3['registro'], df3['fitness1'], label='fitness1_real')
    dividir_plot_regioes(plt, df3, n_regioes=n_regioes)
    # Features (skip categorical/string columns)
    for col in features:
        if df3[col].dtype in ['object', 'string', 'category']:
            continue
        plt.plot(df3['registro'], df3[col], label=col)


def plota_landscape_cenario(df3, features, df_amostragem, cenario='c1', fitness_num=1, n_regioes=10, show_subplots=None):
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
    n_regioes : int, optional
        Número de regiões para divisão do gráfico (default: 10)
    show_subplots : list of bool, optional
        Lista com 5 booleanos indicando quais subfiguras exibir:
        [Landscape, Features, WAPE_text, WAPE_bars, Distribuição_erro]
        Se None, exibe todas (default: None)
        
    Returns:
    --------
    fig : matplotlib.figure.Figure
        Figura gerada
    """
    import numpy as np
    from matplotlib.gridspec import GridSpec
    import matplotlib.cm as cm
    
    # Se não especificado, exibir todas as subfiguras
    if show_subplots is None:
        show_subplots = [True, True, True, True, True]
    
    # Validar show_subplots
    if len(show_subplots) != 5:
        raise ValueError("show_subplots deve ter exatamente 5 elementos booleanos")
    
    max_registro = df3['registro'].max()
    
    # Cores para os cenários
    cores_cenarios = {
        'c1': 'blue',
        'c2': 'green', 
        'c3': 'red'
    }
    
    # Gerar cores dinamicamente baseado no número de regiões
    # Usar colormap 'tab20' que tem 20 cores distintas
    cmap = cm.get_cmap('tab20', n_regioes)
    cores_regioes = [cmap(i) for i in range(n_regioes)]
    
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
        for i in range(n_regioes):
            inicio = i * (1 / n_regioes) * max_registro
            fim = (i + 1) * (1 / n_regioes) * max_registro
            ax.axvspan(inicio, fim, color=cores_regioes[i], alpha=0.2, zorder=0)
        # Gerar linhas verticais dinamicamente baseado no número de regiões
        for i in range(1, n_regioes):
            percent = i / n_regioes
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
    
    # Definir height_ratios e índices baseado nas subfiguras ativas
    base_height_ratios = [2.3, 1, 0.3, 0.8, 1]
    active_ratios = [ratio for ratio, show in zip(base_height_ratios, show_subplots) if show]
    n_subplots = sum(show_subplots)
    
    # Calcular altura da figura dinamicamente
    fig_height = sum(active_ratios) * 2.5 + 2  # Escala baseada nos ratios
    
    # Criar figura com subplots dinâmicos
    fig = plt.figure(figsize=(16, fig_height))
    gs = GridSpec(n_subplots, 1, figure=fig, height_ratios=active_ratios, hspace=0.3)
    
    # Mapear índices de subfiguras originais para índices dinâmicos
    subplot_map = {}
    current_idx = 0
    for i, show in enumerate(show_subplots):
        if show:
            subplot_map[i] = current_idx
            current_idx += 1
    
    # ========== SUBFIGURA 1: Landscape (fitness real + previsto) ==========
    if show_subplots[0]:
        ax1 = fig.add_subplot(gs[subplot_map[0]])
        adicionar_regioes_coloridas(ax1)
        ax1.plot(df3['registro'], df3[col_fitness_real], label=f'{col_fitness_real}_real', linewidth=1.5, color='black')
        ax1.plot(df3['registro'], df3[col_fitness_previsto], label=f'previsao_{cenario}', linewidth=1.5, color=cores_cenarios[cenario], alpha=0.25)
        ax1.legend(loc='upper left', fontsize=10)
        ax1.set_ylabel('Fitness', fontweight='bold')
        ax1.set_title(f'Cenário {cenario.upper()} - Fitness{fitness_num} Real vs Previsto', fontweight='bold', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(0, max_registro)
    
    # ========== SUBFIGURA 2: Features ==========
    if show_subplots[1]:
        ax2 = fig.add_subplot(gs[subplot_map[1]])
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
    if show_subplots[2]:
        ax3 = fig.add_subplot(gs[subplot_map[2]])
        adicionar_regioes_coloridas(ax3)
        ax3.set_xlim(0, max_registro)
        ax3.set_ylim(0, 1)
        ax3.axis('off')  # Remover eixos
        
        # Adicionar textos de WAPE e Amostragem
        posicoes_barras = [(i + 0.5) * (1 / n_regioes) * max_registro for i in range(n_regioes)]
        wapes_geral = [m['wape'] for m in metricas]
        taxas_amost = [m['taxa_amostragem'] for m in metricas]
        
        # Ajustar tamanho da fonte baseado no número de regiões (reduzido em 20%)
        fontsize_texto = max(11, 21 - n_regioes // 2)  # Reduzido em 20%, mínimo 11
        
        for pos, wape_g, taxa_amost in zip(posicoes_barras, wapes_geral, taxas_amost):
            ax3.text(pos, 0.5, f'WAPE: {wape_g:.0f}%\nAmost: {taxa_amost:.0f}%', 
                    ha='center', va='center', fontsize=fontsize_texto, fontweight='bold', color='darkblue')
    
    # ========== SUBFIGURA 4: Gráfico de barras WAPE ==========
    if show_subplots[3]:
        ax4 = fig.add_subplot(gs[subplot_map[3]])
        adicionar_regioes_coloridas(ax4)
        
        # Recalcular posicoes_barras se não foi calculado antes (caso subplot 3 esteja oculto)
        if not show_subplots[2]:
            posicoes_barras = [(i + 0.5) * (1 / n_regioes) * max_registro for i in range(n_regioes)]
        
        largura_barra = 0.15 * (1 / n_regioes) * max_registro
        
        wapes_sub = [m['wape_sub'] for m in metricas]
        wapes_sobre = [m['wape_sobre'] for m in metricas]
        
        ax4.bar(posicoes_barras, wapes_sub, width=largura_barra, 
                color='darkblue', alpha=0.8, label='WAPE Sub', edgecolor='navy', linewidth=1.5)
        ax4.bar(posicoes_barras, wapes_sobre, width=largura_barra, 
                color='lightblue', alpha=0.8, label='WAPE Sobre', edgecolor='steelblue', linewidth=1.5)
        
        # Ajustar tamanho da fonte dos valores nas barras baseado no número de regiões (reduzido em 25%)
        fontsize_barras = max(9, 14 - n_regioes // 3)  # Reduzido em 25%, mínimo 9
        
        for i, (pos, wape_sub_val, wape_sobre_val) in enumerate(zip(posicoes_barras, wapes_sub, wapes_sobre)):
            if abs(wape_sub_val) > 2:
                ax4.text(pos, wape_sub_val/2, f'{abs(wape_sub_val):.0f}%', 
                        ha='center', va='center', fontsize=fontsize_barras, fontweight='bold', color='white')
            if abs(wape_sobre_val) > 2:
                ax4.text(pos, wape_sobre_val/2, f'{abs(wape_sobre_val):.0f}%', 
                        ha='center', va='center', fontsize=fontsize_barras, fontweight='bold', color='darkblue')
        
        ax4.set_ylabel('WAPE (%)', fontweight='bold')
        ax4.set_title('WAPE por Região (Sub-previsão e Sobre-previsão)', fontweight='bold', fontsize=11)
        ax4.axhline(y=0, color='black', linewidth=0.8, linestyle='-')
        ax4.legend(loc='upper left', fontsize=8)
        ax4.grid(True, alpha=0.3, axis='y')
        ax4.set_xlim(0, max_registro)
    
    # ========== SUBFIGURA 5: Distribuições de erro ==========
    if show_subplots[4]:
        ax5 = fig.add_subplot(gs[subplot_map[4]])
        
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
        
        # Gerar linhas verticais dinamicamente baseado no número de regiões
        for i in range(1, n_regioes):
            percent = i / n_regioes
            ax5.axvline(x=max_registro * percent, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    
    plt.tight_layout()
    plt.show()
    
    return fig


def plota_landscape_5cenarios(df3, features, df_amostragem):
    """
    DEPRECATED: Use plota_landscape_cenario() em vez desta função.
    
    Esta função plota os 3 cenários chamando plota_landscape_cenario() 3 vezes.
    """
    print("⚠️  AVISO: Esta função está deprecated. Use plota_landscape_cenario() para plotar cenários individuais.")
    
    # Plotar cada cenário individualmente
    for cenario in ['c1', 'c2', 'c3']:
        plota_landscape_cenario(df3, features, df_amostragem, cenario=cenario, fitness_num=1)


def display_pareto_fronts3(df_real, pareto_fronts_list, front_names=None, sample_size=1000000):
    """
    Mostra múltiplos fronts de Pareto sobre a fitness landscape verdadeira.
    
    Parameters:
    -----------
    df_real : pd.DataFrame
        Dataframe com a fitness landscape verdadeira (todos os pontos)
    pareto_fronts_list : list of pd.DataFrame
        Lista de dataframes com os fronts de Pareto a serem plotados
    front_names : list of str, optional
        Lista de nomes personalizados para cada front na legenda.
        Se None, usa nomes padrão 'Front 1', 'Front 2', etc.
    sample_size : int, optional
        Número de pontos a amostrar da landscape para plotar (default: 1000000)
    """
    
    # ============================================================================
    # Calcular limites comuns para ambos os gráficos
    # ============================================================================
    
    # Encontrar o máximo entre fitness1 e fitness2 de todos os pontos
    max_fitness = max(df_real['fitness1'].max(), df_real['fitness2'].max())
    # Arredondar para cima para um valor "bonito"
    max_limit = math.ceil(max_fitness / 2) * 2
    
    # ============================================================================
    # GRÁFICO: Múltiplos Fronts no contexto de todos os pontos com boxplots
    # ============================================================================

    # Subsampling para todos os pontos (para não sobrecarregar o gráfico)
    actual_sample_size = min(sample_size, len(df_real))
    df_sample = df_real.sample(n=actual_sample_size, random_state=42)

    # Criar figura simples (sem boxplots)
    fig, ax_main = plt.subplots(figsize=(10, 10))

    # Plotar todos os pontos (amostra) em cinza (s=10 -> s=14 -> s=21)
    ax_main.scatter(df_sample['fitness1'], df_sample['fitness2'], 
            c='lightgray', s=21, alpha=0.3, 
            label=f'Todos os pontos (amostra de {actual_sample_size:,})', zorder=1)

    # Definir cores para os diferentes fronts
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan', 'magenta', 'yellow']
    dark_colors = ['darkred', 'darkblue', 'darkgreen', 'darkorange', 'darkviolet', 'saddlebrown', 'deeppink', 'darkcyan', 'darkmagenta', 'gold']
    
    # Se não foram fornecidos nomes, usar nomes padrão
    if front_names is None:
        front_names = [f'Front {i+1}' for i in range(len(pareto_fronts_list))]
    
    # Plotar cada front de Pareto
    for i, pareto_front in enumerate(pareto_fronts_list):
        color = colors[i % len(colors)]
        dark_color = dark_colors[i % len(dark_colors)]
        
        # Plotar o front em destaque (s=40 -> s=64 -> s=96)
        ax_main.scatter(pareto_front['fitness1'], pareto_front['fitness2'], 
                c=color, s=96, alpha=0.9, edgecolors=dark_color, 
                linewidth=1.5, label=f'{front_names[i]} ({len(pareto_front)} pts)', zorder=3+i)

    # Configurações do gráfico principal
    ax_main.set_xlabel('Fitness1 (f1)', fontsize=13, fontweight='bold')
    ax_main.set_ylabel('Fitness2 (f2)', fontsize=13, fontweight='bold')
    ax_main.legend(fontsize=11, loc='best')
    ax_main.grid(True, alpha=0.3, linestyle='--')
    
    # Definir limites iguais para x e y começando em 0
    ax_main.set_xlim(0, max_limit)
    ax_main.set_ylim(0, max_limit)
    
    # Definir aspect ratio igual (1 cm no x = 1 cm no y)
    ax_main.set_aspect('equal', adjustable='box')

    plt.tight_layout()
    plt.show()
    
    return fig

def plota_comparacao_distribuicoes(df_surrogate, df_validacao, df_resultados, problema_num=1, n_regioes=10):
    """
    Plota comparação de distribuições em um grid 2xN (2 fitness x N regiões).
    Para visualizar ambos os problemas, chame a função duas vezes.
    
    Parameters:
    -----------
    df_surrogate : pd.DataFrame
        DataFrame com dados gerais (surrogate/população completa)
    df_validacao : pd.DataFrame
        DataFrame com dados de validação (amostra)
    df_resultados : pd.DataFrame
        DataFrame retornado pela função comparar_distribuicoes contendo as métricas
    problema_num : int
        Número do problema (1 ou 2) para filtrar os resultados
    n_regioes : int, optional
        Número de regiões para divisão do gráfico (default: 10)
    
    Returns:
    --------
    matplotlib.figure.Figure
        A figura gerada
    """
    
    # Filtrar resultados para o problema específico
    df_prob = df_resultados[df_resultados['problema'] == f'problema{problema_num}'].copy()
    
    # Configuração do grid: 2 linhas (fitness1, fitness2) x N colunas (regiões)
    # Ajustar largura da figura dinamicamente
    fig_width = max(16, 4 * n_regioes)  # Mínimo 16, 4 polegadas por região
    fig = plt.figure(figsize=(fig_width, 10))
    gs = GridSpec(2, n_regioes, figure=fig, hspace=0.15, wspace=0.15)
    
    # Cores para as distribuições
    cor_surrogate = 'blue'
    cor_validacao = 'red'
    
    # Fitness a plotar
    fitness_cols = ['erro1_c1', 'erro2_c1']
    fitness_labels = ['Fitness1', 'Fitness2']
    
    for row_idx, (col_erro, fitness_label) in enumerate(zip(fitness_cols, fitness_labels)):
        # Filtrar resultados para este fitness
        df_fitness = df_prob[df_prob['coluna'] == col_erro].copy()
        
        # Ordenar por região
        df_fitness = df_fitness.sort_values('regiao')
        
        for col_idx, (_, resultado) in enumerate(df_fitness.iterrows()):
            regiao = resultado['regiao']
            
            # Criar subplot
            ax = fig.add_subplot(gs[row_idx, col_idx])
            
            # Filtrar dados por região
            df_surr_regiao = df_surrogate[df_surrogate['regiao'] == regiao]
            df_val_regiao = df_validacao[df_validacao['regiao'] == regiao]
            
            # Obter distribuições
            dist_surrogate = df_surr_regiao[col_erro].dropna()
            dist_validacao = df_val_regiao[col_erro].dropna()
            
            if len(dist_surrogate) == 0 or len(dist_validacao) == 0:
                ax.text(0.5, 0.5, 'Sem dados', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=10)
                continue
            
            # Calcular bins comuns para ambas as distribuições
            all_data = np.concatenate([dist_surrogate, dist_validacao])
            bins = np.histogram_bin_edges(all_data, bins=30)
            
            # Plotar histogramas sobrepostos com transparência
            ax.hist(dist_surrogate, bins=bins, alpha=0.3, color=cor_surrogate, 
                   label='Geral', density=True, edgecolor=cor_surrogate, linewidth=0.8)
            ax.hist(dist_validacao, bins=bins, alpha=0.3, color=cor_validacao, 
                   label='Validação', density=True, edgecolor=cor_validacao, linewidth=0.8)
            
            # Adicionar curvas KDE (densidade) mais visíveis
            # KDE para surrogate
            kde_surr = scipy_stats.gaussian_kde(dist_surrogate)
            x_range = np.linspace(all_data.min(), all_data.max(), 100)
            ax.plot(x_range, kde_surr(x_range), color=cor_surrogate, 
                   linewidth=2.0, alpha=0.9)
            
            # KDE para validação
            kde_val = scipy_stats.gaussian_kde(dist_validacao)
            ax.plot(x_range, kde_val(x_range), color=cor_validacao, 
                   linewidth=2.0, alpha=0.9)
            
            # Obter WAPE validação dos resultados
            wape_validacao = resultado.get('wape_validacao', np.nan) * 100  # converter para porcentagem
            
            # Determinar cor e símbolo para o status "Iguais"
            iguais_valor = resultado['distribuicoes_iguais']
            if iguais_valor == 'Sim':
                cor_iguais = 'darkgreen'
                simbolo_iguais = '✓'
            else:
                cor_iguais = 'darkred'
                simbolo_iguais = '✗'
            
            # Adicionar texto com métricas (sem a linha Iguais que será adicionada separadamente)
            texto_metricas = (
                f"KS p-value: {resultado['ks_pvalue']:.4f}\n"
                f"\n"  # espaço reservado para a linha Iguais
                f"μ_val: {resultado['media_validacao']:.2f}\n"
                f"σ_val: {resultado['desvpad_validacao']:.2f}\n"
                f"WAPE_val: {wape_validacao:.1f}%"
            )
            
            # Ajustar tamanho da fonte baseado no número de regiões
            fontsize_metricas = max(7, 10.5 - n_regioes // 3)  # Reduz conforme aumenta regiões
            fontsize_titulo = max(9, 13 - n_regioes // 3)
            fontsize_label = max(8, 11 - n_regioes // 3)
            
            # Box principal com fundo branco
            ax.text(0.02, 0.98, texto_metricas, transform=ax.transAxes,
                   fontsize=fontsize_metricas, verticalalignment='top', horizontalalignment='left',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                            edgecolor='gray', alpha=0.9, linewidth=0.8),
                   zorder=10)
            
            # Adicionar linha "Iguais:" COLORIDA sobreposta
            ax.text(0.025, 0.928, f"Iguais: {simbolo_iguais} {iguais_valor}", 
                   transform=ax.transAxes,
                   fontsize=fontsize_metricas, verticalalignment='top', horizontalalignment='left',
                   color=cor_iguais, fontweight='bold',
                   zorder=11)
            
            # Configurações do subplot
            if row_idx == 0:
                ax.set_title(f'Região {regiao}', fontweight='bold', fontsize=fontsize_titulo)
            
            if col_idx == 0:
                ax.set_ylabel(f'{fitness_label}\nDensidade', fontweight='bold', fontsize=fontsize_label)
            
            if row_idx == 1:
                ax.set_xlabel('Erro', fontsize=10)
            
            # Grid e formatação
            ax.grid(True, alpha=0.3, linewidth=0.6)
            ax.tick_params(labelsize=9)
            
            # Ajustar espessura das bordas do subplot
            for spine in ax.spines.values():
                spine.set_linewidth(1.2)
            
            # Legenda apenas no primeiro subplot de cada linha
            if col_idx == 0:
                ax.legend(fontsize=9, loc='upper right', framealpha=0.8)
    
    # Título geral
    fig.suptitle(f'Comparação de Distribuições - Problema {problema_num}', 
                fontsize=16, fontweight='bold', y=0.995)
    
    plt.tight_layout(rect=[0, 0, 1, 0.99], pad=0.5)
    plt.show()
    
    return fig


def display_fitness_landscape_with_paretos(df, pareto_fronts_list, n_regioes=None):
    '''
    Plots fitness landscape with multiple Pareto fronts and predicted landscapes.
    Uses same colors as display_pareto_fronts3 for consistency.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with real and predicted fitness landscapes
        Required columns: registro, fitness1, fitness2, fitness_full
        Optional columns: fitness1_c1, fitness2_c1 (predicted landscapes)
    pareto_fronts_list : list of pd.DataFrame
        List of dataframes with Pareto fronts (must have 'registro' column to match with df)
    n_regioes : int or None, optional
        Number of regions to divide the plot. If None, no regions are shown (default: None)
    '''
    
    # Same colors as display_pareto_fronts3 for consistency
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan', 'magenta', 'yellow']
    dark_colors = ['darkred', 'darkblue', 'darkgreen', 'darkorange', 'darkviolet', 'saddlebrown', 'deeppink', 'darkcyan', 'darkmagenta', 'gold']
    
    max_registro = df['registro'].max()
    
    # Generate region colors only if n_regioes is specified
    cores_regioes = None
    if n_regioes is not None:
        import matplotlib.cm as cm
        cmap = cm.get_cmap('tab20', n_regioes)
        cores_regioes = [cmap(i) for i in range(n_regioes)]
    
    def adicionar_regioes_coloridas(ax):
        """Add colored regions to plot (only if n_regioes is specified)"""
        if n_regioes is None:
            return
        for i in range(n_regioes):
            inicio = i * (1 / n_regioes) * max_registro
            fim = (i + 1) * (1 / n_regioes) * max_registro
            ax.axvspan(inicio, fim, color=cores_regioes[i], alpha=0.2, zorder=0)
        # Add vertical lines
        for i in range(1, n_regioes):
            percent = i / n_regioes
            ax.axvline(x=max_registro * percent, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    
    def add_pareto_markers(ax, pareto_df, df_main, y_col, marker_color, edge_color, label_suffix):
        """Helper function to add Pareto markers using ORIGINAL landscape values"""
        # Merge pareto with main df to get original fitness values at those registro positions
        pareto_with_values = pareto_df.merge(df_main[['registro', y_col]], on='registro', how='left', suffixes=('', '_original'))
        
        # Use the original values from the main df
        if y_col + '_original' in pareto_with_values.columns:
            y_values = pareto_with_values[y_col + '_original']
        else:
            y_values = pareto_with_values[y_col]
        
        # Add vertical lines at key Pareto positions (thin and discreet)
        pareto_sorted = pareto_with_values.sort_values('registro')
        positions = [0, len(pareto_sorted)//4, len(pareto_sorted)//2, 
                     3*len(pareto_sorted)//4, -1]
        for i in positions:
            ax.axvline(x=pareto_sorted.iloc[i]['registro'], color=marker_color, 
                      alpha=0.2, linewidth=0.8, linestyle='--', zorder=1)
        
        # Add scatter points at ORIGINAL fitness values (75% of original: s=40 -> s=30)
        ax.scatter(pareto_with_values['registro'], y_values, 
                  c=marker_color, s=30, 
                  alpha=0.9,
                  edgecolors=edge_color,
                  linewidth=1.2,
                  label=f'{label_suffix} ({len(pareto_df):,})', 
                  zorder=5, marker='D')
    
    # Configuration for the first two subplots (fitness1 and fitness2)
    plot_configs = [
        {
            'y_col': 'fitness1',
            'y_col_pred': 'fitness1_c1',
            'ylabel': 'Fitness1',
            'title': 'Fitness1 Landscape: Ótimos de Múltiplos Fronts'
        },
        {
            'y_col': 'fitness2',
            'y_col_pred': 'fitness2_c1',
            'ylabel': 'Fitness2',
            'title': 'Fitness2 Landscape: Ótimos de Múltiplos Fronts'
        }
    ]
    
    fig, axes = plt.subplots(3, 1, figsize=(16, 14))
    
    # ========== SUBFIGURAS 1 e 2: Fitness1 e Fitness2 ==========
    for ax, config in zip(axes[:2], plot_configs):
        # Add colored regions first
        adicionar_regioes_coloridas(ax)
        
        # Plot real landscape as BLACK LINE (not filled area)
        ax.plot(df['registro'], df[config['y_col']], 
               color='black', linewidth=1.5, 
               label='Landscape verdadeira', zorder=2)
        
        # Plot predicted landscape as GRAY LINE (25% thinner)
        if config['y_col_pred'] in df.columns:
            ax.plot(df['registro'], df[config['y_col_pred']], 
                   color='gray', linewidth=1.125, 
                   linestyle='--', label='Landscape prevista', zorder=1)
        
        # Add Pareto front markers for all fronts
        for i, pareto_front in enumerate(pareto_fronts_list):
            color = colors[i % len(colors)]
            dark_color = dark_colors[i % len(dark_colors)]
            add_pareto_markers(ax, pareto_front, df, config['y_col'], 
                             color, dark_color, f'Front {i+1}')
        
        ax.set_xlabel('Registro (x)', fontsize=12, fontweight='bold')
        ax.set_ylabel(config['ylabel'], fontsize=12, fontweight='bold')
        ax.set_title(config['title'], fontsize=14, fontweight='bold')
        ax.legend(fontsize=10, loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, max_registro)
    
    # ========== SUBFIGURA 3: Comparação completa ==========
    ax = axes[2]
    adicionar_regioes_coloridas(ax)
    
    # Plot real landscapes as BLACK LINES (only real landscapes, no predicted)
    ax.plot(df['registro'], df['fitness_full'], 
           color='black', linewidth=2, 
           label='Fitness Full (verdadeira)', zorder=3)
    ax.plot(df['registro'], df['fitness1'], 
           color='black', linewidth=1, alpha=0.4,
           label='Fitness1 (verdadeira)', zorder=2)
    ax.plot(df['registro'], df['fitness2'], 
           color='black', linewidth=1, alpha=0.4,
           label='Fitness2 (verdadeira)', zorder=2)
    
    # Add Pareto markers for all fronts
    for i, pareto_front in enumerate(pareto_fronts_list):
        color = colors[i % len(colors)]
        dark_color = dark_colors[i % len(dark_colors)]
        add_pareto_markers(ax, pareto_front, df, 'fitness_full', 
                         color, dark_color, f'Front {i+1}')
    
    ax.set_xlabel('Registro (x)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Fitness', fontsize=12, fontweight='bold')
    ax.set_title('Comparação Completa: Landscapes Verdadeiras com Múltiplos Fronts',
                fontsize=14, fontweight='bold')
    ax.legend(fontsize=9, loc='best', framealpha=0.9, ncol=2)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, max_registro)
    
    plt.tight_layout()
    plt.show()
    
    return fig


def display_fitness_landscape_with_2pareto(df, pareto_real, pareto_surrogate):
    '''
    DEPRECATED: Use display_fitness_landscape_with_paretos() instead.
    
    Plots fitness landscape with two Pareto fronts (real and surrogate).
    This function is kept for backward compatibility.
    '''
    print("⚠️  AVISO: Esta função está deprecated. Use display_fitness_landscape_with_paretos() para múltiplos fronts.")
    display_fitness_landscape_with_paretos(df, [pareto_real, pareto_surrogate])


def gerar_gif_evolucao_nsga2(df_landscape, history, nome_arquivo='evolucao_nsga2.gif', 
                              fps=10, output_dir='data'):
    """
    Gera um GIF animado mostrando a evolução das populações do NSGA-II ao longo das gerações.
    
    Parameters:
    -----------
    df_landscape : pd.DataFrame
        Dataframe com a fitness landscape verdadeira (todos os pontos)
    history : list
        Lista com histórico de populações retornado por run_my_uasa_nsga2 com save_history=True.
        Cada elemento da lista é uma lista de dicionários com 'genotype' e 'fitness'.
    nome_arquivo : str, optional
        Nome do arquivo GIF a ser gerado (default: 'evolucao_nsga2.gif')
    fps : int, optional
        Frames por segundo (velocidade do gif) (default: 10)
    output_dir : str, optional
        Diretório onde o GIF será salvo (default: 'data')
    """
    import imageio.v3 as imageio
    import io
    import os
    
    if history is None:
        raise ValueError("Histórico de populações não foi fornecido. Execute run_my_uasa_nsga2 com save_history=True")
    
    # Criar diretório de saída se não existir
    os.makedirs(output_dir, exist_ok=True)
    
    # Calcular limites comuns para todos os gráficos
    max_fitness = max(df_landscape['fitness1'].max(), df_landscape['fitness2'].max())
    max_limit = math.ceil(max_fitness / 2) * 2
    
    # Subsampling da landscape para não sobrecarregar o gráfico
    sample_size = min(500000, len(df_landscape))
    df_sample = df_landscape.sample(n=sample_size, random_state=42)
    
    n_frames = len(history)
    print(f"Iniciando a geração de {n_frames} frames...")
    
    frames_buffer = []  # Lista para segurar as imagens na memória RAM
    
    # Loop de geração de frames
    for i, population_snapshot in enumerate(history):
        # Converter população snapshot para dataframe
        registros_pop = []
        for ind in population_snapshot:
            # Converter genótipo para registro
            registro = int(''.join(map(str, ind['genotype'])))
            registros_pop.append(registro)
        
        # Filtrar população atual do dataframe
        df_pop_atual = df_landscape[df_landscape['registro'].isin(registros_pop)].copy()
        
        # Criar figura com subplots usando GridSpec
        fig = plt.figure(figsize=(12, 12))
        gs = fig.add_gridspec(3, 3, width_ratios=[1, 6, 0.4], height_ratios=[0.4, 6, 1], 
                             hspace=0.02, wspace=0.02)
        
        # Eixo principal (scatter plot)
        ax_main = fig.add_subplot(gs[1, 1])
        
        # Eixos para os boxplots
        ax_top = fig.add_subplot(gs[0, 1], sharex=ax_main)
        ax_right = fig.add_subplot(gs[1, 2], sharey=ax_main)
        
        # Plotar todos os pontos (amostra) em cinza
        ax_main.scatter(df_sample['fitness1'], df_sample['fitness2'], 
                c='lightgray', s=10, alpha=0.3, 
                label=f'Landscape completa (amostra de {sample_size:,})', zorder=1)
        
        # Plotar a população atual em vermelho
        ax_main.scatter(df_pop_atual['fitness1'], df_pop_atual['fitness2'], 
                c='red', s=80, alpha=0.9, edgecolors='darkred', 
                linewidth=1.5, label=f'População Gen {i} ({len(df_pop_atual)} pts)', zorder=3)
        
        # Configurações do gráfico principal
        ax_main.set_xlabel('Fitness1 (f1)', fontsize=13, fontweight='bold')
        ax_main.set_ylabel('Fitness2 (f2)', fontsize=13, fontweight='bold')
        ax_main.set_title(f'Evolução NSGA-II - Geração {i}/{n_frames-1}\n(Problema de Maximização Bi-Objetivo)', 
                fontsize=15, fontweight='bold', pad=20)
        ax_main.legend(fontsize=11, loc='best')
        ax_main.grid(True, alpha=0.3, linestyle='--')
        
        # Definir limites iguais para x e y começando em 0
        ax_main.set_xlim(0, max_limit)
        ax_main.set_ylim(0, max_limit)
        
        # Definir aspect ratio igual
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
        
        # Salvar o plot na Memória (Buffer)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)  # Retorna o "cursor" para o início do arquivo na memória
        
        # Ler a imagem da memória usando imageio
        frame_imagem = imageio.imread(buf)
        frames_buffer.append(frame_imagem)
        
        # Limpeza
        buf.close()
        plt.close(fig)
        
        # Barra de progresso simples
        if (i + 1) % 10 == 0:
            print(f"Processado {i + 1}/{n_frames} frames...")
    
    # Salvar o GIF Final
    caminho_arquivo = os.path.join(output_dir, nome_arquivo)
    print(f"Salvando arquivo '{nome_arquivo}' no diretório '{output_dir}'...")
    
    # loop=0 significa que o GIF vai repetir infinitamente
    # duration é o tempo de cada frame em milissegundos (ou 1000/fps)
    imageio.imwrite(caminho_arquivo, frames_buffer, duration=(1000/fps), loop=0)
    
    caminho_completo = os.path.abspath(caminho_arquivo)
    print(f"\n✅ Sucesso! GIF gerado em:\n{caminho_completo}")
    
    return caminho_completo





def display_evolution_of_genotypes(df_history):

    # Visualizar evolução dos genótipos ao longo das gerações
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))

    # Plot 1: COM diferenciação de cor por id_solucao
    ax1 = axes[0]
    for id_sol in df_history['id_solucao'].unique():
        df_sol = df_history[df_history['id_solucao'] == id_sol]
        ax1.plot(df_sol['geracao'], df_sol['genotipo'], 
                alpha=0.6, linewidth=0.8, marker='')

    ax1.set_xlabel('Geração', fontsize=12)
    ax1.set_ylabel('Genótipo (Registro)', fontsize=12)
    ax1.set_title('Evolução dos Genótipos - COM diferenciação por solução', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # Plot 2: SEM diferenciação de cor (todas as linhas iguais)
    ax2 = axes[1]
    for id_sol in df_history['id_solucao'].unique():
        df_sol = df_history[df_history['id_solucao'] == id_sol]
        ax2.plot(df_sol['geracao'], df_sol['genotipo'], 
                color='steelblue', alpha=0.4, linewidth=0.8, marker='')

    ax2.set_xlabel('Geração', fontsize=12)
    ax2.set_ylabel('Genótipo (Registro)', fontsize=12)
    ax2.set_title('Evolução dos Genótipos - SEM diferenciação por solução', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

    # Estatísticas adicionais
    print(f"\n📊 Estatísticas do histórico:")
    print(f"   • Total de registros: {len(df_history):,}")
    print(f"   • Gerações: {df_history['geracao'].nunique()}")
    print(f"   • Soluções por geração: {df_history['id_solucao'].nunique()}")
    print(f"   • Genótipos únicos visitados: {df_history['genotipo'].nunique():,}")
