import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import math
import numpy as np
from matplotlib.gridspec import GridSpec
from scipy import stats as scipy_stats
from src.nsga2.evaluation import genotype_to_registro
from src.nsga2.evaluation import evaluate_population
from src.processing import gerar_ruido_raw

# Configure matplotlib for better performance with large datasets
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 6)
plt.rcParams['lines.linewidth'] = 0.5


def plota_fitness_landscape_com_equacoes(df, n_regioes=5, show_regions=True, 
                                         pareto_fronts_list=None, front_names=None,
                                         fitness1 = 'fitness1', fitness2 = 'fitness2',
                                         plot_equations = True):
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
    
    ax1.plot(df['registro'], df[fitness1], label=fitness1, linewidth=1.5, color='steelblue')
    ax1.plot(df['registro'], df[fitness2], label=fitness2, linewidth=1.5, color='coral')
    
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
            fitness_max = pareto_front[[fitness1, fitness2]].max(axis=1)
            
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
    
    if plot_equations:

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
        Lista com 4 booleanos indicando quais subfiguras exibir:
        [Landscape, Features, WAPE_text, Distribuição_erro]
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
        show_subplots = [True, True, True, True]
    
    # Validar show_subplots
    if len(show_subplots) != 4:
        raise ValueError("show_subplots deve ter exatamente 4 elementos booleanos")
    
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
            
            # Denominador por região: soma de todos os valores verdadeiros da região
            denominador_regiao = df_regiao[col_real].sum()
            
            # WAPE sub: soma dos erros absolutos negativos / soma dos valores verdadeiros da região
            erros_sub = erros[erros < 0]
            wape_sub = 100 * np.abs(erros_sub).sum() / denominador_regiao if len(erros_sub) > 0 and denominador_regiao > 0 else 0
            
            # WAPE sobre: soma dos erros positivos / soma dos valores verdadeiros da região
            erros_sobre = erros[erros > 0]
            wape_sobre = 100 * erros_sobre.sum() / denominador_regiao if len(erros_sobre) > 0 and denominador_regiao > 0 else 0
            
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
    base_height_ratios = [2.3, 1, 0.5, 1]  # Subfigura 3 com altura 0.5
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
    
    # ========== SUBFIGURA 3: Textos WAPE, WAPE sub, WAPE sobre e Amostragem ==========
    if show_subplots[2]:
        ax3 = fig.add_subplot(gs[subplot_map[2]])
        adicionar_regioes_coloridas(ax3)
        ax3.set_xlim(0, max_registro)
        ax3.set_ylim(0, 2.6)  # Aumentado em 30% (2 * 1.30 = 2.6)
        ax3.axis('off')  # Remover eixos
        
        # Adicionar textos de WAPE, WAPE sub, WAPE sobre e Amostragem
        posicoes_barras = [(i + 0.5) * (1 / n_regioes) * max_registro for i in range(n_regioes)]
        wapes_geral = [m['wape'] for m in metricas]
        wapes_sub = [m['wape_sub'] for m in metricas]
        wapes_sobre = [m['wape_sobre'] for m in metricas]
        taxas_amost = [m['taxa_amostragem'] for m in metricas]
        
        # Ajustar tamanho da fonte baseado no número de regiões (aumentado em 10%)
        fontsize_texto = max(7, int((19 - n_regioes // 2) * 0.75 * 1.10))  # Aumentado em 10%, mínimo 7
        
        for pos, wape_g, wape_sub, wape_sobre, taxa_amost in zip(posicoes_barras, wapes_geral, wapes_sub, wapes_sobre, taxas_amost):
            texto = f'WAPE: {wape_g:.0f}%\nsubprevisao: {wape_sub:.0f}%\nsobreprevisao: {wape_sobre:.0f}%\nAmost: {taxa_amost:.0f}%'
            ax3.text(pos, 1.3, texto, 
                    ha='center', va='center', fontsize=fontsize_texto, fontweight='bold', color='black')
    
    # ========== SUBFIGURA 4: Distribuições de erro ==========
    if show_subplots[3]:
        ax4 = fig.add_subplot(gs[subplot_map[3]])
        
        # Determinar cor baseada no cenário
        cor_distribuicao = cores_cenarios[cenario]
        cor_linha = {'c1': 'darkblue', 'c2': 'darkgreen', 'c3': 'darkred'}.get(cenario, 'darkblue')
        
        for i in range(n_regioes):
            inicio = i * (1 / n_regioes) * max_registro
            fim = (i + 1) * (1 / n_regioes) * max_registro
            df_regiao = df3[(df3['registro'] >= inicio) & (df3['registro'] < fim)]
            
            ax4.axvspan(inicio, fim, color=cores_regioes[i], alpha=0.2, zorder=0)
            
            erros = df_regiao[col_erro].values
            
            if len(erros) > 0:
                counts, bin_edges = np.histogram(erros, bins=30)
                bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
                counts_norm = counts / counts.max() if counts.max() > 0 else counts
                largura_regiao = fim - inicio
                x_positions = inicio + (bin_centers - bin_centers.min()) / (bin_centers.max() - bin_centers.min() + 1e-10) * largura_regiao * 0.9
                x_positions += largura_regiao * 0.05
                
                ax4.fill_between(x_positions, 0, counts_norm, alpha=0.6, color=cor_distribuicao)
                ax4.plot(x_positions, counts_norm, color=cor_linha, linewidth=1.5, alpha=0.8)
        
        ax4.set_xlabel('Registro', fontweight='bold')
        ax4.set_ylabel('Densidade Normalizada', fontweight='bold')
        ax4.set_title('Distribuição dos Erros por Região', fontweight='bold', fontsize=11)
        ax4.set_xlim(0, max_registro)
        ax4.grid(True, alpha=0.3)
        
        # Gerar linhas verticais dinamicamente baseado no número de regiões
        for i in range(1, n_regioes):
            percent = i / n_regioes
            ax4.axvline(x=max_registro * percent, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    
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


def display_pareto_fronts3(df_real,
                           pareto_fronts_list, 
                           fitness1 = 'fitness1',
                           fitness2 = 'fitness2',
                           front_names=None, 
                           sample_size=1000000, 
                           front_colors=None):
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
    front_colors : list of str, optional
        Lista de cores para cada front de Pareto.
        Se None, usa cores padrão ['red', 'blue', 'green', ...].
    """
    
    # ============================================================================
    # Calcular limites comuns para ambos os gráficos
    # ============================================================================
    
    # Calcular limites independentes para cada eixo
    max_fitness1 = df_real[fitness1].max()
    max_fitness2 = df_real[fitness2].max()
   
    # Arredondar para cima para valores "bonitos"
    if max_fitness1 <= 1:
        max_limit_x = 1
    else:
        max_limit_x = math.ceil(max_fitness1 / 2) * 2

    if max_fitness2 <= 1:
        max_limit_y = 1
    else:
        max_limit_y = math.ceil(max_fitness2 / 2) * 2

    # ============================================================================
    # GRÁFICO: Múltiplos Fronts no contexto de todos os pontos com boxplots
    # ============================================================================

    # Subsampling para todos os pontos (para não sobrecarregar o gráfico)
    actual_sample_size = min(sample_size, len(df_real))
    df_sample = df_real.sample(n=actual_sample_size, random_state=42)

    # Criar figura simples (sem boxplots)
    fig, ax_main = plt.subplots(figsize=(10, 10))

    # Plotar todos os pontos (amostra) em cinza (s=10 -> s=14 -> s=21)
    ax_main.scatter(df_sample[fitness1], df_sample[fitness2], 
            c='lightgray', s=21, alpha=0.3, 
            label=f'Todos os pontos (amostra de {actual_sample_size:,})', zorder=1)

    # Definir cores para os diferentes fronts
    default_colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan', 'magenta', 'yellow']
    default_dark_colors = ['darkred', 'darkblue', 'darkgreen', 'darkorange', 'darkviolet', 'saddlebrown', 'deeppink', 'darkcyan', 'darkmagenta', 'gold']
    
    # Usar cores personalizadas se fornecidas, caso contrário usar cores padrão
    if front_colors is not None:
        colors = front_colors
        # Gerar cores escuras correspondentes para as bordas
        dark_colors = []
        for color in colors:
            if color == 'red':
                dark_colors.append('darkred')
            elif color == 'blue':
                dark_colors.append('darkblue')
            elif color == 'yellow':
                dark_colors.append('gold')
            elif color == 'goldenrod':
                dark_colors.append('darkgoldenrod')
            elif color == 'green':
                dark_colors.append('darkgreen')
            elif color == 'orange':
                dark_colors.append('darkorange')
            elif color == 'purple':
                dark_colors.append('darkviolet')
            elif color == 'brown':
                dark_colors.append('saddlebrown')
            elif color == 'pink':
                dark_colors.append('deeppink')
            elif color == 'cyan':
                dark_colors.append('darkcyan')
            elif color == 'magenta':
                dark_colors.append('darkmagenta')
            else:
                dark_colors.append('black')  # fallback para cores desconhecidas
    else:
        colors = default_colors
        dark_colors = default_dark_colors
    
    # Se não foram fornecidos nomes, usar nomes padrão
    if front_names is None:
        front_names = [f'Front {i+1}' for i in range(len(pareto_fronts_list))]
    
    # Plotar cada front de Pareto
    for i, pareto_front in enumerate(pareto_fronts_list):
        color = colors[i % len(colors)]
        dark_color = dark_colors[i % len(dark_colors)]
        
        # Plotar o front em destaque (s=40 -> s=64 -> s=96)
        ax_main.scatter(pareto_front[fitness1], pareto_front[fitness2], 
                c=color, s=96, alpha=0.9, edgecolors=dark_color, 
                linewidth=1.5, label=f'{front_names[i]} ({len(pareto_front)} pts)', zorder=3+i)

    # Configurações do gráfico principal
    ax_main.set_xlabel('Fitness1 (f1)', fontsize=13, fontweight='bold')
    ax_main.set_ylabel('Fitness2 (f2)', fontsize=13, fontweight='bold')
    ax_main.legend(fontsize=17, loc='best')
    ax_main.grid(True, alpha=0.3, linestyle='--')
    
    # Definir limites iguais para x e y começando em 0
    ax_main.set_xlim(0, max_limit_x)
    ax_main.set_ylim(0, max_limit_y)
    
    # Definir aspect ratio igual (1 cm no x = 1 cm no y)
#    ax_main.set_aspect('equal', adjustable='box')

    plt.tight_layout()
    plt.show()
    
    return fig



def display_pareto_fronts7(df_real,
                           dict_solutions,
                           fitness1='fitness1',
                           fitness2='fitness2',
                           sample_size=1000000,
                           title=None):
    """
    Mostra múltiplos fronts de Pareto sobre a fitness landscape verdadeira.
    Versão simplificada que recebe um dicionário de soluções.

    Parameters
    ----------
    df_real : pd.DataFrame
        Dataframe com a fitness landscape verdadeira (todos os pontos).
    dict_solutions : dict
        Dicionário onde cada chave é o rótulo (str) e o valor é uma lista
        [df_pareto, cor, tamanho].  Exemplo::

            {
                'Pareto ótimo':        [df_pareto_mmf1, 'white', 20],
                'NSGA-II + surrogate': [df_pareto_my2,  'red',  80],
            }
    fitness1 : str, optional
        Nome da coluna de fitness 1 (default: 'fitness1').
    fitness2 : str, optional
        Nome da coluna de fitness 2 (default: 'fitness2').
    sample_size : int, optional
        Número de pontos a amostrar da landscape para plotar (default: 1000000).
    title : str or None, optional
        Título do gráfico. Se None, omite título.

    Returns
    -------
    matplotlib.figure.Figure
    """
    labels = list(dict_solutions.keys())
    df_paretos = [v[0] for v in dict_solutions.values()]
    colors = [v[1] for v in dict_solutions.values()]
    sizes = [v[2] for v in dict_solutions.values()]

    max_fitness1 = df_real[fitness1].max()
    max_fitness2 = df_real[fitness2].max()

    max_limit_x = 1 if max_fitness1 <= 1 else math.ceil(max_fitness1 / 2) * 2
    max_limit_y = 1 if max_fitness2 <= 1 else math.ceil(max_fitness2 / 2) * 2

    actual_sample_size = min(sample_size, len(df_real))
    df_sample = df_real.sample(n=actual_sample_size, random_state=42)

    fig, ax_main = plt.subplots(figsize=(10, 10))

    ax_main.scatter(df_sample[fitness1], df_sample[fitness2],
                    c='lightgray', s=21, alpha=0.3,
                    label=f'Landscape ({actual_sample_size:,} pts)', zorder=1)

    for label, df_par, color, size in zip(labels, df_paretos, colors, sizes):
        ax_main.scatter(
            df_par[fitness1], df_par[fitness2],
            c=color, s=size, alpha=0.9, edgecolors='black',
            linewidth=1.2, label=f'{label} ({len(df_par)} pts)',
            zorder=3
        )

    ax_main.set_xlabel(f'{fitness1}', fontsize=13, fontweight='bold')
    ax_main.set_ylabel(f'{fitness2}', fontsize=13, fontweight='bold')
    ax_main.legend(fontsize=17, loc='best')
    ax_main.grid(True, alpha=0.3, linestyle='--')

    ax_main.set_xlim(0, max_limit_x)
    ax_main.set_ylim(0, max_limit_y)

    if title is not None:
        ax_main.set_title(title, fontsize=18, fontweight='bold')

    plt.tight_layout()
    plt.show()

    return fig


def plota_comparacao_distribuicoes(df_surrogate, df_validacao, df_resultados, problema_num=1, n_regioes=None, 
                                   fitness_cols=None, fitness_labels=None, problem_name=None, max_cols=5):
    """
    Plota comparação de distribuições em um grid com quebra de linha.
    Para visualizar ambos os problemas, chame a função duas vezes.
    
    Parameters:
    -----------
    df_surrogate : pd.DataFrame
        DataFrame com dados gerais (surrogate/população completa)
    df_validacao : pd.DataFrame
        DataFrame com dados de validação (amostra)
    df_resultados : pd.DataFrame
        DataFrame retornado pela função comparar_distribuicoes contendo as métricas
    problema_num : int, optional
        Número do problema (1 ou 2) para filtrar os resultados usando padrão 'problema{num}'
        Ignorado se problem_name for fornecido (default: 1)
    n_regioes : int, optional
        Número de regiões para divisão do gráfico (default: None = auto-detecta dos dados)
    fitness_cols : list of str, optional
        Lista com os nomes das colunas de erro a plotar (default: auto-detecta)
    fitness_labels : list of str, optional
        Lista com os labels para os fitness (default: auto-gera baseado nas colunas)
    problem_name : str, optional
        Nome específico do problema no DataFrame (ex: 'MMF1', 'MMF4', 'BBob16'). 
        Se fornecido, sobrescreve problema_num (default: None)
    max_cols : int, optional
        Número máximo de colunas por linha antes de quebrar (default: 5)
    
    Returns:
    --------
    matplotlib.figure.Figure
        A figura gerada
    """
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec
    import numpy as np
    from scipy import stats as scipy_stats
    import math
    import pandas as pd
    
    # Determinar o nome do problema a filtrar
    if problem_name is not None:
        problema_filtro = problem_name
    else:
        problema_filtro = f'problema{problema_num}'
    
    # Filtrar resultados para o problema específico
    df_prob = df_resultados[df_resultados['problema'] == problema_filtro].copy()
    
    if len(df_prob) == 0:
        print(f"⚠️  AVISO: Nenhum dado encontrado para problema='{problema_filtro}'")
        print(f"    Problemas disponíveis: {list(df_resultados['problema'].unique())}")
        return plt.figure(figsize=(16, 10))
    
    # Auto-detectar número de regiões se não fornecido
    if n_regioes is None:
        n_regioes = len(df_prob['regiao'].unique())
        print(f"📊 Auto-detectado: {n_regioes} regiões")
    
    # Auto-detectar colunas de fitness se não fornecidas
    if fitness_cols is None:
        colunas_disponiveis = df_resultados['coluna'].unique()
        
        if 'erro1_c1' in colunas_disponiveis or 'erro2_c1' in colunas_disponiveis:
            fitness_cols = ['erro1_c1', 'erro2_c1']
            fitness_labels = ['Fitness1', 'Fitness2'] if fitness_labels is None else fitness_labels
        elif 'erro_f1' in colunas_disponiveis or 'erro_f2' in colunas_disponiveis:
            fitness_cols = ['erro_f1', 'erro_f2']
            fitness_labels = ['F1', 'F2'] if fitness_labels is None else fitness_labels
        else:
            fitness_cols = list(colunas_disponiveis[:2])
            fitness_labels = [f'Fitness{i+1}' for i in range(len(fitness_cols))] if fitness_labels is None else fitness_labels
    
    if fitness_labels is None:
        fitness_labels = [f'Fitness{i+1}' for i in range(len(fitness_cols))]
    
    # Calcular dimensões do grid
    n_cols = min(max_cols, n_regioes)
    n_rows_per_fitness = math.ceil(n_regioes / n_cols)
    
    # Configuração da figura - altura sem espaço extra
    fig_width = max(16, 4 * n_cols)
    fig_height = 5 * n_rows_per_fitness * 2
    fig = plt.figure(figsize=(fig_width, fig_height))
    
    # Criar GridSpec com espaçamento extra entre objetivos
    height_ratios = []
    for i in range(n_rows_per_fitness):
        height_ratios.append(1.0)
    height_ratios.append(0.3)  # Espaço entre objetivos
    for i in range(n_rows_per_fitness):
        height_ratios.append(1.0)
    
    total_rows = n_rows_per_fitness * 2 + 1  # +1 para o espaçamento
    
    gs = GridSpec(total_rows, n_cols, figure=fig, 
                  height_ratios=height_ratios,
                  hspace=0.2, wspace=0.15)
    
    # Cores para as distribuições
    cor_surrogate = 'blue'
    cor_validacao = 'red'
    
    # Plotar cada fitness
    for fitness_idx, (col_erro, fitness_label) in enumerate(zip(fitness_cols, fitness_labels)):
        # Filtrar resultados para este fitness
        df_fitness = df_prob[df_prob['coluna'] == col_erro].copy()
        
        if len(df_fitness) == 0:
            print(f"⚠️  AVISO: Nenhum dado encontrado para coluna='{col_erro}'")
            continue
        
        # Ordenar numericamente pela região
        df_fitness['regiao_num'] = pd.to_numeric(df_fitness['regiao'], errors='coerce')
        df_fitness = df_fitness.sort_values('regiao_num')
        
        # Calcular offset de linha para o segundo fitness
        if fitness_idx == 0:
            row_offset = 0
        else:
            row_offset = n_rows_per_fitness + 1  # +1 para pular a linha de espaçamento
        
        for idx, (_, resultado) in enumerate(df_fitness.iterrows()):
            regiao = resultado['regiao']
            
            # Calcular posição no grid
            grid_row = idx // n_cols
            grid_col = idx % n_cols
            actual_row = row_offset + grid_row
            
            # Criar subplot
            ax = fig.add_subplot(gs[actual_row, grid_col])
            
            # Adicionar título do objetivo no primeiro subplot de cada bloco
            if idx == 0:
                # Título acima do primeiro subplot
                ax.text(0.5, 1.15, f'Objetivo: {fitness_label}', 
                       transform=ax.transAxes,
                       fontsize=14, fontweight='bold', color='darkblue',
                       ha='center', va='bottom')
            
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
            kde_surr = scipy_stats.gaussian_kde(dist_surrogate)
            x_range = np.linspace(all_data.min(), all_data.max(), 100)
            ax.plot(x_range, kde_surr(x_range), color=cor_surrogate, 
                   linewidth=2.0, alpha=0.9)
            
            kde_val = scipy_stats.gaussian_kde(dist_validacao)
            ax.plot(x_range, kde_val(x_range), color=cor_validacao, 
                   linewidth=2.0, alpha=0.9)
            
            # Obter WAPE validação dos resultados
            wape_validacao = resultado.get('wape_validacao', np.nan) * 100
            
            # Determinar cor e símbolo para o status "Iguais"
            iguais_valor = resultado['distribuicoes_iguais']
            if iguais_valor == 'Sim':
                cor_iguais = 'darkgreen'
                simbolo_iguais = '✓'
            else:
                cor_iguais = 'darkred'
                simbolo_iguais = '✗'
            
            # Adicionar texto com métricas
            texto_metricas = (
                f"KS p-value: {resultado['ks_pvalue']:.4f}\n"
                f"\n"
                f"μ_val: {resultado['media_validacao']:.2f}\n"
                f"σ_val: {resultado['desvpad_validacao']:.2f}\n"
                f"WAPE_val: {wape_validacao:.1f}%"
            )
            
            # Ajustar tamanho da fonte
            fontsize_metricas = max(7, 10.5 - n_cols // 2)
            fontsize_titulo = max(9, 13 - n_cols // 2)
            fontsize_label = max(8, 11 - n_cols // 2)
            
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
            
            # Título do subplot
            ax.set_title(f'Região {regiao}', fontweight='bold', fontsize=fontsize_titulo)
            
            # Label do eixo Y apenas na primeira coluna
            if grid_col == 0:
                ax.set_ylabel('Densidade', fontweight='bold', fontsize=fontsize_label)
            
            # Label do eixo X apenas na última linha de cada fitness
            if grid_row == n_rows_per_fitness - 1 or idx == len(df_fitness) - 1:
                ax.set_xlabel('Erro', fontsize=10)
            
            # Grid e formatação
            ax.grid(True, alpha=0.3, linewidth=0.6)
            ax.tick_params(labelsize=9)
            
            # Ajustar espessura das bordas do subplot
            for spine in ax.spines.values():
                spine.set_linewidth(1.2)
            
            # Legenda apenas no primeiro subplot de cada fitness
            if idx == 0:
                ax.legend(fontsize=9, loc='upper right', framealpha=0.8)
    
    # Ajustar layout sem espaço extra
    plt.tight_layout(pad=0.5)
    plt.show()
    
    return fig



def display_fitness_landscape_with_paretos(df, pareto_fronts_list, n_regioes=None, front_colors=None, show_error_subplot=False):
    '''
    Plots fitness landscape with multiple Pareto fronts and predicted landscapes.
    Uses same colors as display_pareto_fronts3 for consistency.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with real and predicted fitness landscapes
        Required columns: registro, fitness1, fitness2, fitness_full
        Optional columns: fitness1_c1, fitness2_c1 (predicted landscapes)
        Optional columns for error subplot: regiao (required if show_error_subplot=True)
    pareto_fronts_list : list of pd.DataFrame
        List of dataframes with Pareto fronts (must have 'registro' column to match with df)
    n_regioes : int or None, optional
        Number of regions to divide the plot. If None, no regions are shown (default: None)
    front_colors : list of str, optional
        Lista de cores para cada front de Pareto.
        Se None, usa cores padrão ['red', 'blue', 'green', ...].
    show_error_subplot : bool, optional
        If True, replaces the 3rd subplot with error information by region (default: False)
    '''
    
    # Same colors as display_pareto_fronts3 for consistency
    default_colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan', 'magenta', 'yellow']
    default_dark_colors = ['darkred', 'darkblue', 'darkgreen', 'darkorange', 'darkviolet', 'saddlebrown', 'deeppink', 'darkcyan', 'darkmagenta', 'gold']
    
    # Usar cores personalizadas se fornecidas, caso contrário usar cores padrão
    if front_colors is not None:
        colors = front_colors
        # Gerar cores escuras correspondentes para as bordas
        dark_colors = []
        for color in colors:
            if color == 'red':
                dark_colors.append('darkred')
            elif color == 'blue':
                dark_colors.append('darkblue')
            elif color == 'yellow':
                dark_colors.append('gold')
            elif color == 'goldenrod':
                dark_colors.append('darkgoldenrod')
            elif color == 'green':
                dark_colors.append('darkgreen')
            elif color == 'orange':
                dark_colors.append('darkorange')
            elif color == 'purple':
                dark_colors.append('darkviolet')
            elif color == 'brown':
                dark_colors.append('saddlebrown')
            elif color == 'pink':
                dark_colors.append('deeppink')
            elif color == 'cyan':
                dark_colors.append('darkcyan')
            elif color == 'magenta':
                dark_colors.append('darkmagenta')
            else:
                dark_colors.append('black')  # fallback para cores desconhecidas
    else:
        colors = default_colors
        dark_colors = default_dark_colors
    
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
    
    # Determine height ratios based on whether we're showing error subplot
    if show_error_subplot:
        height_ratios = [2.3, 2.3, 1]  # Third subplot is smaller for text
    else:
        height_ratios = [1, 1, 1]  # Equal heights for standard layout
    
    fig = plt.figure(figsize=(16, 14))
    gs = GridSpec(3, 1, figure=fig, height_ratios=height_ratios, hspace=0.3)
    
    # ========== SUBFIGURAS 1 e 2: Fitness1 e Fitness2 ==========
    for idx, config in enumerate(plot_configs):
        ax = fig.add_subplot(gs[idx])
        
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
    
    # ========== SUBFIGURA 3: Error info by region OR Comparison ==========
    ax = fig.add_subplot(gs[2])
    
    if show_error_subplot and n_regioes is not None:
        # Show error information by region (like plota_landscape_cenario subfigure 3)
        adicionar_regioes_coloridas(ax)
        ax.set_xlim(0, max_registro)
        ax.set_ylim(0, 2.6)
        ax.axis('off')  # Remove axes
        
        # Check if we have the necessary columns for error calculation
        if 'fitness1_c1' in df.columns and 'fitness2_c1' in df.columns and 'regiao' in df.columns:
            # Calculate metrics per region
            metricas_f1 = []
            metricas_f2 = []
            
            # Denominador global para cada fitness
            denominador_global_f1 = df['fitness1'].mean()
            denominador_global_f2 = df['fitness2'].mean()
            
            for i in range(n_regioes):
                inicio = i * (1 / n_regioes) * max_registro
                fim = (i + 1) * (1 / n_regioes) * max_registro
                df_regiao = df[(df['registro'] >= inicio) & (df['registro'] < fim)]
                
                # Fitness 1 errors
                erros_f1 = df_regiao['fitness1_c1'] - df_regiao['fitness1']
                erro_abs_f1 = np.abs(erros_f1)
                wape_f1 = 100 * erro_abs_f1.mean() / denominador_global_f1
                
                denominador_regiao_f1 = df_regiao['fitness1'].sum()
                erros_sub_f1 = erros_f1[erros_f1 < 0]
                wape_sub_f1 = 100 * np.abs(erros_sub_f1).sum() / denominador_regiao_f1 if len(erros_sub_f1) > 0 and denominador_regiao_f1 > 0 else 0
                erros_sobre_f1 = erros_f1[erros_f1 > 0]
                wape_sobre_f1 = 100 * erros_sobre_f1.sum() / denominador_regiao_f1 if len(erros_sobre_f1) > 0 and denominador_regiao_f1 > 0 else 0
                
                metricas_f1.append({'wape': wape_f1, 'wape_sub': wape_sub_f1, 'wape_sobre': wape_sobre_f1})
                
                # Fitness 2 errors
                erros_f2 = df_regiao['fitness2_c1'] - df_regiao['fitness2']
                erro_abs_f2 = np.abs(erros_f2)
                wape_f2 = 100 * erro_abs_f2.mean() / denominador_global_f2
                
                denominador_regiao_f2 = df_regiao['fitness2'].sum()
                erros_sub_f2 = erros_f2[erros_f2 < 0]
                wape_sub_f2 = 100 * np.abs(erros_sub_f2).sum() / denominador_regiao_f2 if len(erros_sub_f2) > 0 and denominador_regiao_f2 > 0 else 0
                erros_sobre_f2 = erros_f2[erros_f2 > 0]
                wape_sobre_f2 = 100 * erros_sobre_f2.sum() / denominador_regiao_f2 if len(erros_sobre_f2) > 0 and denominador_regiao_f2 > 0 else 0
                
                metricas_f2.append({'wape': wape_f2, 'wape_sub': wape_sub_f2, 'wape_sobre': wape_sobre_f2})
            
            # Add text for each region
            posicoes_barras = [(i + 0.5) * (1 / n_regioes) * max_registro for i in range(n_regioes)]
            fontsize_texto = max(7, int((19 - n_regioes // 2) * 0.75 * 1.10))
            
            for pos, m_f1, m_f2 in zip(posicoes_barras, metricas_f1, metricas_f2):
                texto = (f'fitness1 - WAPE: {m_f1["wape"]:.0f}%\n'
                        f'subprevisao: {m_f1["wape_sub"]:.0f}%\n'
                        f'sobreprevisao: {m_f1["wape_sobre"]:.0f}%\n'
                        f'\n'
                        f'fitness2 - WAPE: {m_f2["wape"]:.0f}%\n'
                        f'subprevisao: {m_f2["wape_sub"]:.0f}%\n'
                        f'sobreprevisao: {m_f2["wape_sobre"]:.0f}%')
                ax.text(pos, 1.3, texto, 
                       ha='center', va='center', fontsize=fontsize_texto, 
                       fontweight='bold', color='black')
        else:
            # Show warning if columns are missing
            ax.text(0.5, 0.5, 
                   'Erro: Colunas necessárias não encontradas\n(fitness1_c1, fitness2_c1, regiao)', 
                   ha='center', va='center', fontsize=12, color='red',
                   transform=ax.transAxes)
    else:
        # Show standard comparison plot
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





###################################################################################################################
###################################################################################################################

import pandas as pd
import numpy as np

import plotly.express as px
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

from sklearn.decomposition import PCA
from scipy.stats import qmc
from pymoo.problems import get_problem
from pymoo.core.problem import Problem




def plot_landscapes_heatmap_dashboard(df_m1, df_par_m1, mmf1,
                                      df_m4, df_par_m4, mmf4, 
                                      df_b, df_par_b, bbob):
    plt.style.use('seaborn-v0_8-darkgrid')
    fig = plt.figure(figsize=(18, 16))
    fig.suptitle('Análise Topológica (Espaço de Decisão 2D): MMF1, MMF4 vs BBOB-BiObj f16', 
                 fontsize=22, fontweight='bold', y=0.95)
    
    gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.15)
    
    def plot_heatmap(ax, df, df_par, obj_col, title, cbar_label, cmap='plasma', xl=None, xu=None):
        scatter = ax.scatter(df['x_1'], df['x_2'], c=df[obj_col], cmap=cmap, 
                             alpha=0.9, s=8, edgecolor='none')
        
        # Plota o Pareto (bolinhas brancas)
        ax.scatter(df_par['x_1'], df_par['x_2'], 
                   color='white', edgecolor='black', s=40, linewidth=1.0, 
                   zorder=10, label='Pareto Optimal Set')
        
        ax.set_title(title, fontsize=15, fontweight='bold')
        ax.set_xlabel('$x_1$ (Decisão 1)', fontsize=12)
        ax.set_ylabel('$x_2$ (Decisão 2)', fontsize=12)
        
        if xl is not None and xu is not None:
            ax.set_xlim(xl[0], xu[0])
            ax.set_ylim(xl[1], xu[1])
            
        ax.legend(loc='upper right', facecolor='white', framealpha=0.8)
        fig.colorbar(scatter, ax=ax, label=cbar_label)

    # --- Plot 1 & 2: MMF1 ---
    ax1 = fig.add_subplot(gs[0, 0])
    plot_heatmap(ax1, df_m1, df_par_m1, 'f1', '1. MMF1 - Objetivo 1 ($f_1$)', 'Valor de $f_1$', 'plasma', mmf1.xl, mmf1.xu)

    ax2 = fig.add_subplot(gs[0, 1])
    plot_heatmap(ax2, df_m1, df_par_m1, 'f2', '2. MMF1 - Objetivo 2 ($f_2$)', 'Valor de $f_2$', 'plasma', mmf1.xl, mmf1.xu)

    # --- Plot 3 & 4: MMF4 ---
    ax3 = fig.add_subplot(gs[1, 0])
    plot_heatmap(ax3, df_m4, df_par_m4, 'f1', '3. MMF4 - Objetivo 1 ($f_1$)', 'Valor de $f_1$', 'plasma', mmf4.xl, mmf4.xu)

    ax4 = fig.add_subplot(gs[1, 1])
    plot_heatmap(ax4, df_m4, df_par_m4, 'f2', '4. MMF4 - Objetivo 2 ($f_2$)', 'Valor de $f_2$', 'plasma', mmf4.xl, mmf4.xu)

    # --- Plot 5 & 6: BBOB ---
    ax5 = fig.add_subplot(gs[2, 0])
    plot_heatmap(ax5, df_b, df_par_b, 'f1', '5. BBOB Gallagher Caótico - Objetivo 1', 'Valor de $f_1$', 'plasma', bbob.xl, bbob.xu)

    ax6 = fig.add_subplot(gs[2, 1])
    plot_heatmap(ax6, df_b, df_par_b, 'f2', '6. BBOB Gallagher Caótico - Objetivo 2', 'Valor de $f_2$', 'plasma', bbob.xl, bbob.xu)

    plt.tight_layout()
    plt.show()


def plot_landscapes_heatmap_dashboard_v2(
    problem,
    df_landscape,
    dict_solutions,
    cmap='Greys_r',
    cmap_lighten=0.3,
    title=None
):
    """
    Plota heatmaps do espaço de decisão para um único problema bi-objetivo,
    com suporte a múltiplos conjuntos de Pareto sobrepostos.

    Parameters
    ----------
    problem : pymoo Problem
        Instância do problema (deve ter .xl e .xu para limites dos eixos).
    df_landscape : pd.DataFrame
        DataFrame com colunas x_1, x_2, f1, f2 (landscape completa).
    dict_solutions : dict
        Dicionário onde cada chave é o rótulo (str) e o valor é uma lista
        [df_pareto, cor, tamanho].  Exemplo::

            {
                'Pareto ótimo':       [df_pareto_mmf1, 'white', 20],
                'NSGA-II + surrogate': [df_pareto_my2,  'red',  80],
            }
    cmap : str, optional
        Colormap do heatmap (default: 'Greys_r').
        Sugestões: 'Greys_r', 'gray_r', 'bone_r', 'plasma', 'viridis',
        'inferno', 'cividis', 'magma', 'coolwarm'.
        Referência: https://matplotlib.org/stable/gallery/color/colormap_reference.html
    cmap_lighten : float, optional
        Fator de clareamento do extremo escuro do colormap (0.0 a 1.0).
        0.0 = sem alteração, 0.3 = 30 % mais claro, etc. (default: 0.3).
    title : str or None, optional
        Título geral da figura. Se None, omite suptitle.

    Returns
    -------
    matplotlib.figure.Figure
    """
    import matplotlib.colors as mcolors

    plt.style.use('seaborn-v0_8-darkgrid')

    # --- clarear o colormap misturando cada cor com branco ----------------
    base_cmap = plt.get_cmap(cmap)
    cmap_lighten = max(0.0, min(cmap_lighten, 1.0))
    if cmap_lighten > 0:
        sampled = base_cmap(np.linspace(0, 1, 256))
        sampled[:, :3] = (1 - cmap_lighten) * sampled[:, :3] + cmap_lighten
        light_cmap = mcolors.LinearSegmentedColormap.from_list(
            f'{cmap}_light', sampled
        )
    else:
        light_cmap = base_cmap

    # --- extrair listas do dicionário -------------------------------------
    labels = list(dict_solutions.keys())
    df_paretos = [v[0] for v in dict_solutions.values()]
    colors = [v[1] for v in dict_solutions.values()]
    sizes = [v[2] for v in dict_solutions.values()]

    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    fig.subplots_adjust(top=0.82)

    if title is not None:
        fig.suptitle(title, fontsize=20, fontweight='bold', y=0.97)

    xl = problem.xl if hasattr(problem, 'xl') else None
    xu = problem.xu if hasattr(problem, 'xu') else None

    obj_configs = [
        {'col': 'f1', 'label': 'Objetivo 1 ($f_1$)', 'cbar': 'Valor de $f_1$'},
        {'col': 'f2', 'label': 'Objetivo 2 ($f_2$)', 'cbar': 'Valor de $f_2$'},
    ]

    for ax, cfg in zip(axes, obj_configs):
        scatter = ax.scatter(
            df_landscape['x_1'], df_landscape['x_2'],
            c=df_landscape[cfg['col']], cmap=light_cmap,
            alpha=0.9, s=8, edgecolor='none'
        )

        for df_par, color, size, label in zip(df_paretos, colors, sizes, labels):
            ax.scatter(
                df_par['x_1'], df_par['x_2'],
                color=color, edgecolor='black', s=size,
                linewidth=1.0, zorder=10, label=label
            )

        ax.set_title(cfg['label'], fontsize=15, fontweight='bold')
        ax.set_xlabel('$x_1$ (Decisão 1)', fontsize=12)
        ax.set_ylabel('$x_2$ (Decisão 2)', fontsize=12)

        if xl is not None and xu is not None:
            ax.set_xlim(xl[0], xu[0])
            ax.set_ylim(xl[1], xu[1])

        fig.colorbar(scatter, ax=ax, label=cfg['cbar'])

    # --- legenda unificada horizontal acima dos subplots ------------------
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles, legend_labels,
        loc='upper center',
        bbox_to_anchor=(0.5, 0.935),
        ncol=len(labels),
        fontsize=16,
        frameon=True,
        facecolor='white',
        framealpha=0.9
    )

    plt.show()

    return fig


def plot_mmf1_dashboard(df, pareto_df, features_cols=['x_1', 'x_2'], fit1_col='f1', fit2_col='f2'):
    """
    Gera um dashboard enxuto com 4 visualizações em um grid 2x2:
    1. Heatmap do Espaço de Decisão para a Fitness 1.
    2. Heatmap do Espaço de Decisão para a Fitness 2.
    3. Coordenadas Paralelas das soluções do Front de Pareto.
    4. Boxplots da distribuição das variáveis do Front de Pareto.
    """
    # Configuração geral da figura (Layout 2 linhas x 2 colunas)
    fig, axes = plt.subplots(2, 2, figsize=(20, 14))
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # Título principal (suptitle) removido conforme solicitado
    
    x1_col = features_cols[0]
    x2_col = features_cols[1]
    
    # Paleta de cor Laranja/Roxo para o Heatmap
    cmap_heatmap = 'plasma' 
    
    # Tamanho dos pontos do Pareto
    tamanho_pareto = 7

    # ==========================================================
    # 1. Heatmap do Espaço de Decisão (Apenas Fitness 1)
    # ==========================================================
    ax1 = axes[0, 0]
    
    scatter1 = ax1.scatter(df[x1_col], df[x2_col], 
                           c=df[fit1_col], cmap=cmap_heatmap, 
                           alpha=0.3, s=5, edgecolor='none')
    
    ax1.scatter(pareto_df[x1_col], pareto_df[x2_col], 
                color='white', s=tamanho_pareto, edgecolor='black', linewidth=0.2, 
                label='Soluções Ótimas (Pareto)', zorder=3)
    
    ax1.set_title(f'1. Heatmap Espacial: Objetivo 1 (${fit1_col}$)', fontsize=15, fontweight='bold')
    ax1.set_xlabel(f'{x1_col} (Domínio [1, 3])', fontsize=12)
    ax1.set_ylabel(f'{x2_col} (Domínio [-1, 1])', fontsize=12)
    ax1.legend(loc='upper right')
    fig.colorbar(scatter1, ax=ax1, label=f'Valor de {fit1_col}')

    # ==========================================================
    # 2. Heatmap do Espaço de Decisão (Apenas Fitness 2)
    # ==========================================================
    ax2 = axes[0, 1]
    
    scatter2 = ax2.scatter(df[x1_col], df[x2_col], 
                           c=df[fit2_col], cmap=cmap_heatmap, 
                           alpha=0.3, s=5, edgecolor='none')
    
    ax2.scatter(pareto_df[x1_col], pareto_df[x2_col], 
                color='white', s=tamanho_pareto, edgecolor='black', linewidth=0.2, 
                label='Soluções Ótimas (Pareto)', zorder=3)
    
    ax2.set_title(f'2. Heatmap Espacial: Objetivo 2 (${fit2_col}$)', fontsize=15, fontweight='bold')
    ax2.set_xlabel(f'{x1_col} (Domínio [1, 3])', fontsize=12)
    ax2.set_ylabel(f'{x2_col} (Domínio [-1, 1])', fontsize=12)
    ax2.legend(loc='upper right')
    fig.colorbar(scatter2, ax=ax2, label=f'Valor de {fit2_col}')

    # ==========================================================
    # PREPARANDO DADOS DO PARETO
    # ==========================================================
    if len(pareto_df) > 100:
        pareto_plot = pareto_df.sample(100, random_state=42).copy()
    else:
        pareto_plot = pareto_df.copy()
        
    pareto_plot = pareto_plot.sort_values(by=fit1_col)

    # ==========================================================
    # 3. Coordenadas Paralelas (PARETO FRONT)
    # ==========================================================
    ax3 = axes[1, 0]
    
    norm = Normalize(vmin=pareto_plot[fit1_col].min(), vmax=pareto_plot[fit1_col].max())
    cmap_linhas = plt.get_cmap('cool')
    
    for _, row in pareto_plot.iterrows():
        color = cmap_linhas(norm(row[fit1_col]))
        ax3.plot(range(len(features_cols)), row[features_cols], color=color, alpha=0.7, linewidth=2.0)
    
    ax3.set_title('3. Coordenadas Paralelas (Front de Pareto)', fontsize=15, fontweight='bold')
    ax3.set_xticks(range(len(features_cols)))
    ax3.set_xticklabels(features_cols, fontsize=12)
    ax3.set_ylabel('Valores das Variáveis', fontsize=12)
    
    ax3.set_ylim(-1.2, 3.2)
    
    sm = ScalarMappable(cmap=cmap_linhas, norm=norm)
    sm.set_array([])
    fig.colorbar(sm, ax=ax3, label=f'Posição no Pareto (Cor via ${fit1_col}$)')

    # ==========================================================
    # 4. Boxplots (Distribuição do PARETO FRONT)
    # ==========================================================
    ax4 = axes[1, 1]
    
    box_data = [pareto_plot[col] for col in features_cols]
    
    bplot = ax4.boxplot(box_data, patch_artist=True, labels=features_cols)
    
    for patch in bplot['boxes']:
        patch.set_facecolor('skyblue')
        patch.set_alpha(0.7)
        patch.set_edgecolor('black')
        
    for median in bplot['medians']:
        median.set_color('red')
        median.set_linewidth(2)

    ax4.set_title('4. Boxplots das Variáveis (Front de Pareto)', fontsize=15, fontweight='bold')
    ax4.set_ylabel('Valores das Variáveis', fontsize=12)
    
    ax4.set_ylim(-1.2, 3.2)

    # TRUQUE PARA IGUALAR LARGURAS: Adiciona colorbar invisível no ax4
    cbar4 = fig.colorbar(scatter2, ax=ax4)
    cbar4.ax.set_visible(False)

    plt.tight_layout()
    plt.show()



###################################################################################################################
# Adicao de ruido no treinamento do modelo surrogate (MMF1)
###################################################################################################################

def plot_grid_16_ruidos(config_dict, n_samples=10000):
    """
    Gera um painel 4x4 simulando a cara de cada uma das 16 distribuições de ruído,
    padronizadas da mesma forma que ocorre na injeção.
    """
    fig, axes = plt.subplots(4, 4, figsize=(20, 16))
    fig.suptitle('Perfis de Incerteza por Região (Padronizados)', fontsize=22, fontweight='bold', y=0.98)
    axes = axes.flatten()
    
    # Paleta de cores para ficar bonito
    colors = sns.color_palette("husl", 16)
    np.random.seed(42)
    
    for i, (reg, conf) in enumerate(config_dict.items()):
        ax = axes[i]
        
        raw = gerar_ruido_raw(conf['dist'], conf['params'], n_samples)
        
        # Padroniza igual fazemos no dataset principal para plotar a forma
        std_noise = (raw - np.mean(raw)) / (np.std(raw) + 1e-6)
        
        # Usamos KDE (linha suavizada) na maioria, mas histograma nas muito bizarras (rademacher)
        if conf['dist'] == 'rademacher':
            sns.histplot(std_noise, bins=20, ax=ax, color=colors[i], stat='density')
        else:
            sns.histplot(std_noise, bins=50, kde=True, ax=ax, color=colors[i], 
                         edgecolor="none", alpha=0.4)
            
        ax.set_title(f"Reg {reg}: {conf['dist'].capitalize()}", fontsize=13, fontweight='bold')
        ax.set_xlabel('Desvios do Ruído', fontsize=10)
        ax.set_ylabel('Densidade', fontsize=10)
        
        # Foca nos limites importantes para visualizar bem as caudas (remove super outliers do plot)
        ax.set_xlim(-5, 5)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    plt.show()



###################################################################################################################
# Noisy MMF1 Dashboard
###################################################################################################################

def plot_surrogate_comparison_dashboard(
    df_real, df_real_pareto,
    df_pred, df_pred_pareto,
    df_pareto_original=None,  # NOVO: Pareto sobre valores originais
    df_pareto_ruidoso=None,   # NOVO: Pareto sobre valores ruidosos
    features_cols=['x_1', 'x_2'],
    fit1_col='f1',
    fit2_col='f2',
    fit1_pred_col='f1_predicted',
    fit2_pred_col='f2_predicted',
    fit1_original_col='f1_original',  # NOVO
    fit2_original_col='f2_original',  # NOVO
    n_bins_x1=4,
    n_bins_x2=4
):
    """
    Gera um dashboard completo de comparação entre valores originais, ruidosos e previstos.
    
    Figuras 1-2:   Heatmaps ORIGINAIS (f1_original, f2_original) + Pareto Original
    Figuras 3-4:   Heatmaps RUIDOSOS (f1, f2) + Pareto Ruidoso
    Figuras 5-6:   Heatmaps PREVISTOS (f1_predicted, f2_predicted) + Pareto Previsto
    Figuras 7-8:   Grid 4x4 com heatmap WAPE + métricas (previsões vs ruidosos)
    Figuras 9-10:  Grid 4x4 com distribuições dos erros (previsões vs ruidosos)
    Figuras 11-12: Grid 4x4 com heatmap WAPE + métricas (previsões vs originais)
    Figuras 13-14: Grid 4x4 com distribuições dos erros (previsões vs originais)
    """
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
    import numpy as np
    import matplotlib.patches as mpatches
    
    x1_col = features_cols[0]
    x2_col = features_cols[1]
    cmap_heatmap = 'plasma'
    tamanho_pareto = 7
    
    # Usar paretos fornecidos ou os defaults
    if df_pareto_original is None:
        df_pareto_original = df_real_pareto
    if df_pareto_ruidoso is None:
        df_pareto_ruidoso = df_real_pareto
    
    # Criar dataframe combinado com TODAS as colunas necessárias
    df_combined = df_real.copy()
    df_combined[f'{fit1_pred_col}'] = df_pred[fit1_pred_col].values
    df_combined[f'{fit2_pred_col}'] = df_pred[fit2_pred_col].values
    
    # Criar bins equidistantes
    df_combined['bin_x1'] = pd.cut(df_combined[x1_col], bins=n_bins_x1, labels=False)
    df_combined['bin_x2'] = pd.cut(df_combined[x2_col], bins=n_bins_x2, labels=False)
    
    # Calcular erros: PREVISÕES vs RUIDOSOS
    df_combined[f'erro_{fit1_col}_ruido'] = df_combined[fit1_pred_col] - df_combined[fit1_col]
    df_combined[f'erro_{fit2_col}_ruido'] = df_combined[fit2_pred_col] - df_combined[fit2_col]
    
    # Calcular erros: PREVISÕES vs ORIGINAIS
    df_combined[f'erro_{fit1_col}_original'] = df_combined[fit1_pred_col] - df_combined[fit1_original_col]
    df_combined[f'erro_{fit2_col}_original'] = df_combined[fit2_pred_col] - df_combined[fit2_original_col]
    
    # Obter limites
    x1_min, x1_max = df_combined[x1_col].min(), df_combined[x1_col].max()
    x2_min, x2_max = df_combined[x2_col].min(), df_combined[x2_col].max()
    x1_edges = np.linspace(x1_min, x1_max, n_bins_x1 + 1)
    x2_edges = np.linspace(x2_min, x2_max, n_bins_x2 + 1)
    
    # Configuração da figura: 7 linhas x 2 colunas = 14 subplots
    fig = plt.figure(figsize=(20, 49))  # Altura aumentada para 7 linhas
    gs = GridSpec(7, 2, figure=fig, hspace=0.35, wspace=0.25)
    
    # ==========================================================
    # FIGURAS 1-2: Heatmaps ORIGINAIS + Front de Pareto Original
    # ==========================================================
    for idx, (fit_col, subplot_idx) in enumerate([
        (fit1_original_col, (0, 0)), 
        (fit2_original_col, (0, 1))
    ]):
        ax = fig.add_subplot(gs[subplot_idx])
        
        scatter = ax.scatter(df_real[x1_col], df_real[x2_col],
                           c=df_real[fit_col], cmap=cmap_heatmap,
                           alpha=0.3, s=5, edgecolor='none')
        
        ax.scatter(df_pareto_original[x1_col], df_pareto_original[x2_col],
                  color='white', s=tamanho_pareto, edgecolor='black', linewidth=0.5,
                  label='Pareto Original', zorder=3)
        
        fit_name = 'F1' if 'f1' in fit_col.lower() else 'F2'
        ax.set_title(f'{idx+1}. Heatmap ORIGINAL: {fit_name} (sem ruído)', 
                    fontsize=15, fontweight='bold')
        ax.set_xlabel(f'{x1_col}', fontsize=12)
        ax.set_ylabel(f'{x2_col}', fontsize=12)
        ax.legend(loc='upper right')
        fig.colorbar(scatter, ax=ax, label=f'Valor de {fit_name} Original')
    
    # ==========================================================
    # FIGURAS 3-4: Heatmaps RUIDOSOS + Front de Pareto Ruidoso
    # ==========================================================
    for idx, (fit_col, subplot_idx) in enumerate([
        (fit1_col, (1, 0)), 
        (fit2_col, (1, 1))
    ]):
        ax = fig.add_subplot(gs[subplot_idx])
        
        scatter = ax.scatter(df_real[x1_col], df_real[x2_col],
                           c=df_real[fit_col], cmap=cmap_heatmap,
                           alpha=0.3, s=5, edgecolor='none')
        
        ax.scatter(df_pareto_ruidoso[x1_col], df_pareto_ruidoso[x2_col],
                  color='white', s=tamanho_pareto, edgecolor='black', linewidth=0.5,
                  label='Pareto Ruidoso', zorder=3)
        
        fit_name = 'F1' if 'f1' in fit_col.lower() else 'F2'
        ax.set_title(f'{idx+3}. Heatmap RUIDOSO: {fit_name} (com ruído/gabarito)', 
                    fontsize=15, fontweight='bold')
        ax.set_xlabel(f'{x1_col}', fontsize=12)
        ax.set_ylabel(f'{x2_col}', fontsize=12)
        ax.legend(loc='upper right')
        fig.colorbar(scatter, ax=ax, label=f'Valor de {fit_name} Ruidoso')
    
    # ==========================================================
    # FIGURAS 5-6: Heatmaps PREVISTOS + Front de Pareto Previsto
    # ==========================================================
    for idx, (fit_pred_col, subplot_idx) in enumerate([
        (fit1_pred_col, (2, 0)), 
        (fit2_pred_col, (2, 1))
    ]):
        ax = fig.add_subplot(gs[subplot_idx])
        
        scatter = ax.scatter(df_pred[x1_col], df_pred[x2_col],
                           c=df_pred[fit_pred_col], cmap=cmap_heatmap,
                           alpha=0.3, s=5, edgecolor='none')
        
        ax.scatter(df_pred_pareto[x1_col], df_pred_pareto[x2_col],
                  color='white', s=tamanho_pareto, edgecolor='black', linewidth=0.5,
                  label='Pareto Previsto', zorder=3)
        
        fit_name = 'F1' if 'f1' in fit_pred_col.lower() else 'F2'
        ax.set_title(f'{idx+5}. Heatmap PREVISTO: {fit_name} (previsões do surrogate)', 
                    fontsize=15, fontweight='bold')
        ax.set_xlabel(f'{x1_col}', fontsize=12)
        ax.set_ylabel(f'{x2_col}', fontsize=12)
        ax.legend(loc='upper right')
        fig.colorbar(scatter, ax=ax, label=f'Valor de {fit_name} Previsto')
    
    # ==========================================================
    # FUNÇÃO AUXILIAR: Plotar Grid de Métricas WAPE
    # ==========================================================
    def plot_wape_grid(ax, fit_col_real, erro_col, fig_num, comparison_type):
        """Plota grid 4x4 com heatmap WAPE e métricas textuais."""
        # Calcular WAPE de cada região para criar matriz do heatmap
        wape_matrix = np.zeros((n_bins_x2, n_bins_x1))
        wape_matrix[:] = np.nan
        
        for i in range(n_bins_x1):
            for j in range(n_bins_x2):
                df_regiao = df_combined[
                    (df_combined['bin_x1'] == i) &
                    (df_combined['bin_x2'] == j)
                ]
                
                if len(df_regiao) > 0:
                    erros = df_regiao[erro_col]
                    denominador_global = df_combined[fit_col_real].mean()
                    wape = 100 * np.abs(erros).mean() / denominador_global
                    wape_matrix[j, i] = wape
        
        # Plotar heatmap de fundo
        cmap_wape = plt.cm.Reds
        
        im = ax.imshow(wape_matrix, cmap=cmap_wape, aspect='auto',
                      extent=[x1_min, x1_max, x2_min, x2_max],
                      origin='lower', alpha=0.6, interpolation='nearest')
        
        # Desenhar grid
        for x1_edge in x1_edges:
            ax.axvline(x=x1_edge, color='black', linestyle='-', linewidth=2, alpha=0.8)
        for x2_edge in x2_edges:
            ax.axhline(y=x2_edge, color='black', linestyle='-', linewidth=2, alpha=0.8)
        
        # Adicionar texto com métricas em cada célula
        for i in range(n_bins_x1):
            for j in range(n_bins_x2):
                df_regiao = df_combined[
                    (df_combined['bin_x1'] == i) &
                    (df_combined['bin_x2'] == j)
                ]
                
                if len(df_regiao) == 0:
                    continue
                
                x1_center = (x1_edges[i] + x1_edges[i+1]) / 2
                x2_center = (x2_edges[j] + x2_edges[j+1]) / 2
                
                erros = df_regiao[erro_col]
                denominador_global = df_combined[fit_col_real].mean()
                denominador_regiao = df_regiao[fit_col_real].sum()
                
                wape = 100 * np.abs(erros).mean() / denominador_global
                
                erros_sub = erros[erros < 0]
                wape_sub = 100 * np.abs(erros_sub).sum() / denominador_regiao if len(erros_sub) > 0 and denominador_regiao > 0 else 0
                
                erros_sobre = erros[erros > 0]
                wape_sobre = 100 * erros_sobre.sum() / denominador_regiao if len(erros_sobre) > 0 and denominador_regiao > 0 else 0
                
                n_obs = len(df_regiao)
                
                texto = f'WAPE: {wape:.0f}%\nSub: {wape_sub:.0f}%\nSobre: {wape_sobre:.0f}%\nN: {n_obs:,}'
                
                ax.text(x1_center, x2_center, texto,
                       ha='center', va='center',
                       fontsize=9, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3',
                                facecolor='white',
                                edgecolor='black',
                                alpha=0.85))
        
        fit_name = 'F1' if 'f1' in fit_col_real.lower() else 'F2'
        ax.set_title(f'{fig_num}. Grid de Métricas WAPE: {fit_name} (pred vs {comparison_type})', 
                    fontsize=15, fontweight='bold')
        ax.set_xlabel(f'{x1_col}', fontsize=12)
        ax.set_ylabel(f'{x2_col}', fontsize=12)
        ax.set_xlim(x1_min, x1_max)
        ax.set_ylim(x2_min, x2_max)
        
        fig.colorbar(im, ax=ax, label=f'WAPE (%) de {fit_name}')
    
    # ==========================================================
    # FIGURAS 7-8: Grid WAPE (previsões vs ruidosos)
    # ==========================================================
    for idx, (fit_col, erro_col, subplot_idx) in enumerate([
        (fit1_col, f'erro_{fit1_col}_ruido', (3, 0)), 
        (fit2_col, f'erro_{fit2_col}_ruido', (3, 1))
    ]):
        ax = fig.add_subplot(gs[subplot_idx])
        plot_wape_grid(ax, fit_col, erro_col, idx+7, 'ruidoso')
    
    # ==========================================================
    # FUNÇÃO AUXILIAR: Plotar Grid de Distribuições
    # ==========================================================
    def plot_error_distributions(gs_pos, erro_col, fig_num, comparison_type):
        """Plota grid 4x4 com distribuições dos erros por região."""
        ax_main = fig.add_subplot(gs[gs_pos])
        fit_name = 'F1' if 'f1' in erro_col else 'F2'
        ax_main.set_title(f'{fig_num}. Distribuições dos Erros: {fit_name} (pred vs {comparison_type})', 
                         fontsize=15, fontweight='bold', pad=10)
        ax_main.axis('off')
        
        # Criar sub-grid 4x4
        gs_sub = GridSpecFromSubplotSpec(n_bins_x2, n_bins_x1, 
                                        subplot_spec=gs[gs_pos],
                                        hspace=0.15, wspace=0.15)
        
        # Plotar distribuição em cada célula do grid
        for i in range(n_bins_x1):
            for j in range(n_bins_x2):
                ax_cell = fig.add_subplot(gs_sub[n_bins_x2-1-j, i])
                
                df_regiao = df_combined[
                    (df_combined['bin_x1'] == i) &
                    (df_combined['bin_x2'] == j)
                ]
                
                if len(df_regiao) > 0:
                    erros = df_regiao[erro_col].values
                    
                    ax_cell.hist(erros, bins=20, color='steelblue',
                               alpha=0.7, edgecolor='darkblue', linewidth=0.5)
                    
                    ax_cell.axvline(x=0, color='red', linestyle='--',
                                  linewidth=1.5, alpha=0.7)
                    
                    media_erro = erros.mean()
                    std_erro = erros.std()
                    
                    # Formatação adaptativa
                    if abs(media_erro) < 0.01 and abs(media_erro) > 0:
                        media_str = f'{media_erro:.2e}'
                    else:
                        media_str = f'{media_erro:.2f}'
                    
                    if std_erro < 0.01 and std_erro > 0:
                        std_str = f'{std_erro:.2e}'
                    else:
                        std_str = f'{std_erro:.2f}'
                    
                    ax_cell.text(0.95, 0.95, f'μ={media_str}\nσ={std_str}',
                               transform=ax_cell.transAxes,
                               ha='right', va='top',
                               fontsize=7, 
                               bbox=dict(boxstyle='round,pad=0.3',
                                       facecolor='white',
                                       edgecolor='gray',
                                       alpha=0.8))
                else:
                    ax_cell.text(0.5, 0.5, 'Sem\ndados',
                               ha='center', va='center',
                               transform=ax_cell.transAxes,
                               fontsize=8, color='gray')
                
                ax_cell.tick_params(labelsize=6)
                
                if j > 0:
                    ax_cell.set_xticklabels([])
                else:
                    ax_cell.set_xlabel('Erro', fontsize=7)
                    
                if i > 0:
                    ax_cell.set_yticklabels([])
                else:
                    ax_cell.set_ylabel('Freq', fontsize=7)
                
                ax_cell.locator_params(axis='both', nbins=3)
                ax_cell.grid(True, alpha=0.3, linewidth=0.5)
    
    # ==========================================================
    # FIGURAS 9-10: Distribuições (previsões vs ruidosos)
    # ==========================================================
    for idx, (erro_col, gs_pos) in enumerate([
        (f'erro_{fit1_col}_ruido', (4, 0)), 
        (f'erro_{fit2_col}_ruido', (4, 1))
    ]):
        plot_error_distributions(gs_pos, erro_col, idx+9, 'ruidoso')
    
    # ==========================================================
    # FIGURAS 11-12: Grid WAPE (previsões vs originais)
    # ==========================================================
    for idx, (fit_col, erro_col, subplot_idx) in enumerate([
        (fit1_original_col, f'erro_{fit1_col}_original', (5, 0)), 
        (fit2_original_col, f'erro_{fit2_col}_original', (5, 1))
    ]):
        ax = fig.add_subplot(gs[subplot_idx])
        plot_wape_grid(ax, fit_col, erro_col, idx+11, 'original')
    
    # ==========================================================
    # FIGURAS 13-14: Distribuições (previsões vs originais)
    # ==========================================================
    for idx, (erro_col, gs_pos) in enumerate([
        (f'erro_{fit1_col}_original', (6, 0)), 
        (f'erro_{fit2_col}_original', (6, 1))
    ]):
        plot_error_distributions(gs_pos, erro_col, idx+13, 'original')
    
    plt.tight_layout()
    
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  Catalog-aware PF visualisation  (used by notebook 1)
# ═══════════════════════════════════════════════════════════════════════════

def display_pareto_fronts_catalog(problem,
                                  F_landscape,
                                  pareto_fronts_list=None,
                                  front_names=None,
                                  sample_size=100_000,
                                  front_colors=None,
                                  title=None,
                                  elev_offset=-15,
                                  azim_offset=225,
                                  roll_offset=0,
                                  xlim=None,
                                  ylim=None,
                                  zlim=None):
    """
    Mostra o Pareto front teórico verdadeiro + fronts empíricos sobre a
    fitness landscape, no estilo de ``display_pareto_fronts3``.

    Suporta problemas com 2 ou 3 objetivos (2D ou 3D).

    Parameters
    ----------
    problem : Problem
        Instância de problema do catálogo (deve ter ``true_pareto_front``).
    F_landscape : np.ndarray (N, n_obj)
        Valores dos objetivos amostrados (background cinza).
    pareto_fronts_list : list of np.ndarray, optional
        Lista de arrays (M_i, n_obj) com fronts empíricos a plotar.
    front_names : list of str, optional
        Rótulos para cada front empírico.
    sample_size : int
        Máximo de pontos do landscape a plotar (subsampling).
    front_colors : list of str, optional
        Cores para os fronts empíricos.
    title : str, optional
        Título do gráfico.
    elev_offset : float
        Rotação adicional em graus em torno do eixo X (elevação) para
        gráficos 3D. Default 15.
    azim_offset : float
        Rotação adicional em graus em torno do eixo Z (azimute) para
        gráficos 3D. Default 225.
    roll_offset : float
        Rotação adicional em graus em torno do eixo Y (roll) para
        gráficos 3D. Default 0.
    xlim : tuple (lo, hi), optional
        Limites do eixo X. None = automático.
    ylim : tuple (lo, hi), optional
        Limites do eixo Y. None = automático.
    zlim : tuple (lo, hi), optional
        Limites do eixo Z (só 3D). None = automático.

    Returns
    -------
    fig : matplotlib Figure
    """
    n_obj = problem.n_obj

    if pareto_fronts_list is None:
        pareto_fronts_list = []
    if front_names is None:
        front_names = [f'Front {i+1}' for i in range(len(pareto_fronts_list))]

    default_colors = ['royalblue', 'green', 'orange', 'purple', 'brown',
                      'pink', 'cyan', 'magenta', 'yellow']
    default_edge   = ['navy', 'darkgreen', 'darkorange', 'darkviolet',
                      'saddlebrown', 'deeppink', 'darkcyan', 'darkmagenta', 'gold']
    colors = front_colors if front_colors is not None else default_colors
    edge_colors = default_edge

    actual = min(sample_size, len(F_landscape))
    idx_bg = np.random.choice(len(F_landscape), actual, replace=False)
    F_bg = F_landscape[idx_bg]

    X_true, F_true = problem.true_pareto_front()

    if n_obj == 2:
        return _plot_pf_2d(F_bg, F_true, pareto_fronts_list, front_names,
                           colors, edge_colors, actual, title, xlim, ylim)
    else:
        return _plot_pf_3d(F_bg, F_true, pareto_fronts_list, front_names,
                           colors, edge_colors, actual, title,
                           elev_offset, azim_offset, roll_offset,
                           xlim, ylim, zlim)


def _nice_limits(arrays, axis):
    """Exact min/max across all plotted arrays on the given axis."""
    vals = np.concatenate([a[:, axis] for a in arrays if len(a) > 0])
    return float(vals.min()), float(vals.max())


def _plot_pf_2d(F_bg, F_true, fronts, names, colors, edge_colors, n_sample,
                title, xlim=None, ylim=None):
    fig, ax = plt.subplots(figsize=(10, 10))

    ax.scatter(F_bg[:, 0], F_bg[:, 1], c='lightgray', s=21, alpha=0.3,
               label=f'Landscape ({n_sample:,} pts)', zorder=1)

    for i, pf in enumerate(fronts):
        c = colors[i % len(colors)]
        ec = edge_colors[i % len(edge_colors)]
        ax.scatter(pf[:, 0], pf[:, 1], c=c, s=96, alpha=0.9,
                   edgecolors=ec, linewidth=1.5,
                   label=f'{names[i]} ({len(pf)} pts)', zorder=2 + i)

    order = F_true[:, 0].argsort()
    ax.plot(F_true[order, 0], F_true[order, 1], 'r-', lw=2.5,
            label=f'PF teórico ({len(F_true):,} pts)', zorder=10)

    ax.set_xlabel('f\u2081', fontsize=13, fontweight='bold')
    ax.set_ylabel('f\u2082', fontsize=13, fontweight='bold')
    ax.legend(fontsize=14, loc='upper right')
    ax.grid(True, alpha=0.3, linestyle='--')

    all_F = [F_bg, F_true] + list(fronts)
    ax.set_xlim(*(xlim if xlim is not None else _nice_limits(all_F, axis=0)))
    ax.set_ylim(*(ylim if ylim is not None else _nice_limits(all_F, axis=1)))

    if title:
        ax.set_title(title, fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.show()
    return fig


def _plot_pf_3d(F_bg, F_true, fronts, names, colors, edge_colors, n_sample,
                title, elev_offset=-15, azim_offset=225, roll_offset=0,
                xlim=None, ylim=None, zlim=None):
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(F_bg[:, 0], F_bg[:, 1], F_bg[:, 2],
               c='lightgray', s=4, alpha=0.15, depthshade=False,
               label=f'Landscape ({n_sample:,} pts)')

    for i, pf in enumerate(fronts):
        c = colors[i % len(colors)]
        ec = edge_colors[i % len(edge_colors)]
        ax.scatter(pf[:, 0], pf[:, 1], pf[:, 2],
                   c=c, s=30, alpha=0.9, edgecolors=ec, linewidths=0.4,
                   depthshade=False,
                   label=f'{names[i]} ({len(pf)} pts)', zorder=5 + i)

    ax.scatter(F_true[:, 0], F_true[:, 1], F_true[:, 2],
               c='red', s=2, alpha=0.4, depthshade=False,
               label=f'PF teórico ({len(F_true):,} pts)', zorder=10)

    ax.set_xlabel('f\u2081', fontsize=11, fontweight='bold', labelpad=6)
    ax.set_ylabel('f\u2082', fontsize=11, fontweight='bold', labelpad=6)
    ax.set_zlabel('f\u2083', fontsize=11, fontweight='bold', labelpad=6)
    if xlim is not None:
        ax.set_xlim(*xlim)
    if ylim is not None:
        ax.set_ylim(*ylim)
    if zlim is not None:
        ax.set_zlim(*zlim)

    ax.legend(fontsize=11, loc='upper right')
    ax.view_init(elev=25 + elev_offset, azim=45 + azim_offset, roll=roll_offset)

    if title:
        ax.set_title(title, fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.show()
    return fig