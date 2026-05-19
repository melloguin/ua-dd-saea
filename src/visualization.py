import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import math
import numpy as np
from matplotlib.gridspec import GridSpec
from scipy import stats as scipy_stats
from src.processing import gerar_ruido_raw

# Configure matplotlib for better performance with large datasets
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 6)
plt.rcParams['lines.linewidth'] = 0.5










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
            if 'erro_f3' in colunas_disponiveis:
                fitness_cols.append('erro_f3')
            if fitness_labels is None:
                fitness_labels = [f'F{i+1}' for i in range(len(fitness_cols))]
        else:
            fitness_cols = list(colunas_disponiveis[:2])
            fitness_labels = [f'Fitness{i+1}' for i in range(len(fitness_cols))] if fitness_labels is None else fitness_labels
    
    if fitness_labels is None:
        fitness_labels = [f'Fitness{i+1}' for i in range(len(fitness_cols))]
    
    # Calcular dimensões do grid
    n_cols = min(max_cols, n_regioes)
    n_rows_per_fitness = math.ceil(n_regioes / n_cols)
    n_fitness = len(fitness_cols)
    
    # Configuração da figura - altura sem espaço extra
    fig_width = max(16, 4 * n_cols)
    fig_height = max(12.0, 5.0 * n_rows_per_fitness * n_fitness + 3.0 * max(0, n_fitness - 1))
    fig = plt.figure(figsize=(fig_width, fig_height))
    
    # Criar GridSpec com espaçamento extra entre objetivos (qualquer número de objetivos)
    height_ratios = []
    for fi in range(n_fitness):
        height_ratios.extend([1.0] * n_rows_per_fitness)
        if fi < n_fitness - 1:
            height_ratios.append(0.3)
    
    total_rows = len(height_ratios)
    
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
        
        row_offset = fitness_idx * (n_rows_per_fitness + 1)
        
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
# WAPE / Error analysis helpers  (extracted from former plot_surrogate_comparison_dashboard)
###################################################################################################################

def _wape_grid_on_ax(ax, df, fit_col, erro_col,
                     n_bins_x1, n_bins_x2,
                     x1_edges, x2_edges,
                     x1_min, x1_max, x2_min, x2_max,
                     x1_col, x2_col):
    """Draw a WAPE heat-map with text metrics on *ax*."""
    wape_matrix = np.full((n_bins_x2, n_bins_x1), np.nan)
    for i in range(n_bins_x1):
        for j in range(n_bins_x2):
            mask = (df['bin_x1'] == i) & (df['bin_x2'] == j)
            dr = df[mask]
            if len(dr) > 0:
                denom = df[fit_col].mean()
                wape_matrix[j, i] = 100 * np.abs(dr[erro_col]).mean() / denom if denom else 0

    im = ax.imshow(wape_matrix, cmap=plt.cm.Reds, aspect='auto',
                   extent=[x1_min, x1_max, x2_min, x2_max],
                   origin='lower', alpha=0.6, interpolation='nearest')
    for e in x1_edges:
        ax.axvline(x=e, color='black', linewidth=2, alpha=0.8)
    for e in x2_edges:
        ax.axhline(y=e, color='black', linewidth=2, alpha=0.8)

    for i in range(n_bins_x1):
        for j in range(n_bins_x2):
            mask = (df['bin_x1'] == i) & (df['bin_x2'] == j)
            dr = df[mask]
            if len(dr) == 0:
                continue
            xc = (x1_edges[i] + x1_edges[i + 1]) / 2
            yc = (x2_edges[j] + x2_edges[j + 1]) / 2
            erros = dr[erro_col]
            denom_g = df[fit_col].mean()
            denom_r = dr[fit_col].sum()
            wape = 100 * np.abs(erros).mean() / denom_g if denom_g else 0
            e_sub = erros[erros < 0]
            w_sub = 100 * np.abs(e_sub).sum() / denom_r if len(e_sub) > 0 and denom_r > 0 else 0
            e_over = erros[erros > 0]
            w_over = 100 * e_over.sum() / denom_r if len(e_over) > 0 and denom_r > 0 else 0
            txt = f'WAPE: {wape:.0f}%\nSub: {w_sub:.0f}%\nSobre: {w_over:.0f}%\nN: {len(dr):,}'
            ax.text(xc, yc, txt, ha='center', va='center', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                              edgecolor='black', alpha=0.85))

    fj = erro_col.split('_')[1].upper()
    ax.set_xlabel(x1_col, fontsize=12)
    ax.set_ylabel(x2_col, fontsize=12)
    ax.set_xlim(x1_min, x1_max)
    ax.set_ylim(x2_min, x2_max)
    return im


def _error_dist_grid(df, erro_col, n_bins_x1, n_bins_x2, suptitle=None):
    """4×4 grid of error histograms per region (standalone figure)."""
    from matplotlib.gridspec import GridSpec as _GS
    fig = plt.figure(figsize=(4 * n_bins_x1, 4 * n_bins_x2))
    gs = _GS(n_bins_x2, n_bins_x1, figure=fig, hspace=0.25, wspace=0.25)
    if suptitle:
        fig.suptitle(suptitle, fontsize=15, fontweight='bold', y=1.02)
    for i in range(n_bins_x1):
        for j in range(n_bins_x2):
            ax = fig.add_subplot(gs[n_bins_x2 - 1 - j, i])
            mask = (df['bin_x1'] == i) & (df['bin_x2'] == j)
            dr = df[mask]
            if len(dr) > 0:
                errs = dr[erro_col].values
                ax.hist(errs, bins=20, color='steelblue', alpha=0.7,
                        edgecolor='darkblue', linewidth=0.5)
                ax.axvline(x=0, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
                mu, sig = errs.mean(), errs.std()
                mu_s = f'{mu:.2e}' if 0 < abs(mu) < 0.01 else f'{mu:.2f}'
                sig_s = f'{sig:.2e}' if 0 < sig < 0.01 else f'{sig:.2f}'
                ax.text(0.95, 0.95, f'μ={mu_s}\nσ={sig_s}',
                        transform=ax.transAxes, ha='right', va='top', fontsize=7,
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                  edgecolor='gray', alpha=0.8))
            else:
                ax.text(0.5, 0.5, 'Sem\ndados', ha='center', va='center',
                        transform=ax.transAxes, fontsize=8, color='gray')
            ax.tick_params(labelsize=6)
            if j > 0:
                ax.set_xticklabels([])
            else:
                ax.set_xlabel('Erro', fontsize=7)
            if i > 0:
                ax.set_yticklabels([])
            else:
                ax.set_ylabel('Freq', fontsize=7)
            ax.locator_params(axis='both', nbins=3)
            ax.grid(True, alpha=0.3, linewidth=0.5)
    plt.tight_layout()
    plt.show()
    return fig


def _decision_wape_analysis(df_wape, title=None, n_bins_x1=4, n_bins_x2=4):
    """WAPE grids + error-distribution grids for surrogate analysis.

    ``df_wape`` must contain ``x_1, x_2, f{j}, f{j}_predicted, f{j}_original``
    columns.  Objectives are auto-detected.
    """
    import pandas as _pd
    obj_ids = []
    j = 1
    while f'f{j}' in df_wape.columns and f'f{j}_predicted' in df_wape.columns:
        obj_ids.append(j)
        j += 1
    if not obj_ids:
        return

    x1c, x2c = 'x_1', 'x_2'
    df = df_wape.copy()
    df['bin_x1'] = _pd.cut(df[x1c], bins=n_bins_x1, labels=False)
    df['bin_x2'] = _pd.cut(df[x2c], bins=n_bins_x2, labels=False)
    for jj in obj_ids:
        df[f'erro_f{jj}_ruido'] = df[f'f{jj}_predicted'] - df[f'f{jj}']
        df[f'erro_f{jj}_original'] = df[f'f{jj}_predicted'] - df[f'f{jj}_original']

    x1_min, x1_max = df[x1c].min(), df[x1c].max()
    x2_min, x2_max = df[x2c].min(), df[x2c].max()
    x1_edges = np.linspace(x1_min, x1_max, n_bins_x1 + 1)
    x2_edges = np.linspace(x2_min, x2_max, n_bins_x2 + 1)

    for comp_key, comp_lbl in [('ruido', 'ruidoso'), ('original', 'original')]:
        n_obj = len(obj_ids)
        fig_w, axes_w = plt.subplots(1, n_obj, figsize=(10 * n_obj, 8))
        if n_obj == 1:
            axes_w = [axes_w]
        for idx, jj in enumerate(obj_ids):
            fit_col = f'f{jj}_original' if comp_key == 'original' else f'f{jj}'
            erro_col = f'erro_f{jj}_{comp_key}'
            im = _wape_grid_on_ax(axes_w[idx], df, fit_col, erro_col,
                                  n_bins_x1, n_bins_x2, x1_edges, x2_edges,
                                  x1_min, x1_max, x2_min, x2_max, x1c, x2c)
            axes_w[idx].set_title(f'WAPE: F{jj} (pred vs {comp_lbl})',
                                  fontsize=15, fontweight='bold')
            fig_w.colorbar(im, ax=axes_w[idx], label=f'WAPE (%) F{jj}')
        if title:
            fig_w.suptitle(f'{title} — WAPE (pred vs {comp_lbl})',
                           fontsize=18, fontweight='bold', y=1.03)
        plt.tight_layout()
        plt.show()

        for jj in obj_ids:
            erro_col = f'erro_f{jj}_{comp_key}'
            _error_dist_grid(df, erro_col, n_bins_x1, n_bins_x2,
                             suptitle=f'{title} — Erro F{jj} (pred vs {comp_lbl})')


# kept for backward compat; prefer _decision_wape_analysis


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
                                  zlim=None,
                                  true_color='white',
                                  emp_color='red'):
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

    if front_colors is not None:
        colors = front_colors
    else:
        colors = [emp_color, 'green', 'orange', 'purple', 'brown',
                  'pink', 'cyan', 'magenta', 'yellow']

    actual = min(sample_size, len(F_landscape))
    idx_bg = np.random.choice(len(F_landscape), actual, replace=False)
    F_bg = F_landscape[idx_bg]

    X_true, F_true = problem.true_pareto_front()

    if n_obj == 2:
        return _plot_pf_2d(F_bg, F_true, pareto_fronts_list, front_names,
                           colors, actual, title, xlim, ylim, true_color)
    else:
        return _plot_pf_3d(F_bg, F_true, pareto_fronts_list, front_names,
                           colors, actual, title,
                           elev_offset, azim_offset, roll_offset,
                           xlim, ylim, zlim, true_color)


def _nice_limits(arrays, axis):
    """Exact min/max across all plotted arrays on the given axis."""
    vals = np.concatenate([a[:, axis] for a in arrays if len(a) > 0])
    return float(vals.min()), float(vals.max())


def _plot_pf_2d(F_bg, F_true, fronts, names, colors, n_sample,
                title, xlim=None, ylim=None, true_color='white'):
    fig, ax = plt.subplots(figsize=(10, 10))

    ax.scatter(F_bg[:, 0], F_bg[:, 1], c='lightgray', s=21, alpha=0.3,
               label=f'Landscape ({n_sample:,} pts)', zorder=1)

    for i, pf in enumerate(fronts):
        c = colors[i % len(colors)]
        _scatter_colored(ax, pf[:, 0], pf[:, 1], c,
                         s=96, label=f'{names[i]} ({len(pf)} pts)', zorder=2 + i,
                         alpha=0.9)

    order = F_true[:, 0].argsort()
    if true_color == 'white':
        ax.plot(F_true[order, 0], F_true[order, 1], 'k-', lw=5.25, zorder=10)
        ax.plot(F_true[order, 0], F_true[order, 1], 'w-', lw=2.25,
                label=f'PF teórico ({len(F_true):,} pts)', zorder=11)
    else:
        ax.plot(F_true[order, 0], F_true[order, 1], '-', color=true_color, lw=3.0,
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


def _plot_pf_3d(F_bg, F_true, fronts, names, colors, n_sample,
                title, elev_offset=-15, azim_offset=225, roll_offset=0,
                xlim=None, ylim=None, zlim=None, true_color='white'):
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(F_bg[:, 0], F_bg[:, 1], F_bg[:, 2],
               c='lightgray', s=4, alpha=0.15, depthshade=False,
               label=f'Landscape ({n_sample:,} pts)')

    for i, pf in enumerate(fronts):
        c = colors[i % len(colors)]
        _scatter_colored(ax, pf[:, 0], pf[:, 1], c,
                         s=30, label=f'{names[i]} ({len(pf)} pts)',
                         zorder=5 + i, z=pf[:, 2], alpha=0.9)

    tc = 'black' if true_color == 'white' else true_color
    ax.scatter(F_true[:, 0], F_true[:, 1], F_true[:, 2],
               c=tc, s=2, alpha=0.4, depthshade=False,
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


# ═══════════════════════════════════════════════════════════════════════════
#  Decision-space (landscape) visualisation  (used by notebook 1)
# ═══════════════════════════════════════════════════════════════════════════

def display_decision_space(problem, X_landscape, F_landscape,
                           X_true, X_emp_list, title=None, pair_vars=None,
                           true_color='white',
                           emp_colors=None, emp_names=None,
                           emp_color=None,
                           show_2d_pca=True,
                           show_3d_pca=True,
                           cmap='Greys',
                           elev_offset=-15, azim_offset=225, roll_offset=0,
                           F_variants=None,
                           df_wape=None,
                           n_bins_wape=(4, 4)):
    """Dispatch decision-space plots based on n_var.

    Parameters
    ----------
    problem : Problem
    X_landscape : ndarray (N, n_var)
    F_landscape : ndarray (N, n_obj)
    X_true : ndarray  – true Pareto-set points.
    X_emp_list : ndarray or list of ndarray
        One or more empirical PS sets. A single ndarray is auto-wrapped.
    title : str, optional
    pair_vars : list of int (1-indexed) for pairwise grid, optional.
    true_color : str   Colour for true PS ('white' = white + black edge).
    emp_colors : list of str, optional
        Colour per empirical set.  Default ``['red', 'green', 'orange', …]``.
    emp_names : list of str, optional
        Label per empirical set.
    emp_color : str, optional
        Backward-compat alias: if a single string is passed and ``emp_colors``
        is None, it is used as the sole colour for all empirical sets.
    cmap : str
        Colormap for landscape heatmaps/scatter.
        ``'Greys'`` (default) → light-grey palette identical to the original.
        Any matplotlib name (e.g. ``'plasma'``) is used directly.
    elev_offset, azim_offset, roll_offset : float
        3-D rotation offsets (same convention as display_pareto_fronts_catalog).
    F_variants : list of (name, F_ndarray), optional
        Multiple landscape colorings for 2-var heatmaps.  Each entry is
        ``('Label', F_array)`` where F_array is (N, n_obj).  When provided
        for n_var==2, one heatmap row per variant is drawn instead of the
        single default row.
    df_wape : DataFrame, optional
        Validation/prediction DataFrame for WAPE analysis (n_var==2 only).
        Must contain ``x_1, x_2, f{j}, f{j}_predicted, f{j}_original``
        columns.  When provided, WAPE grids and error-distribution grids
        are appended after the heatmaps.
    n_bins_wape : tuple (n_bins_x1, n_bins_x2)
        Bin counts for the WAPE grid (default ``(4, 4)``).
    """
    if isinstance(X_emp_list, np.ndarray) and X_emp_list.ndim == 2:
        X_emp_list = [X_emp_list]

    _default_emp_colors = ['red', 'green', 'orange', 'purple', 'brown',
                           'pink', 'cyan', 'magenta', 'yellow']
    if emp_colors is None:
        if emp_color is not None:
            emp_colors = [emp_color] * len(X_emp_list)
        else:
            emp_colors = _default_emp_colors[:len(X_emp_list)]
    if emp_names is None:
        if len(X_emp_list) == 1:
            emp_names = ['PS empírico']
        else:
            emp_names = [f'PS emp. {i+1}' for i in range(len(X_emp_list))]

    kw = dict(true_color=true_color, emp_colors=emp_colors,
              emp_names=emp_names, cmap=cmap,
              elev_offset=elev_offset, azim_offset=azim_offset,
              roll_offset=roll_offset)
    n = problem.n_var
    
    # 2 variáveis de decisão (plot 2d landscape)
    if n == 2:
        if F_variants is not None:
            _decision_heatmap_2d_multi(problem, X_landscape, F_variants,
                                       X_true, X_emp_list, title, **kw)
        else:
            _decision_heatmap_2d(problem, X_landscape, F_landscape,
                                 X_true, X_emp_list, title, **kw)
        if df_wape is not None:
            _decision_wape_analysis(df_wape, title, *n_bins_wape)

    # 3 variáveis de decisão (plot 3d landscape)
    elif n == 3:
        _decision_scatter_3d(problem, X_landscape, F_landscape,
                             X_true, X_emp_list, title, **kw)
    
    # > 3 variáveis de decisão (necessita redução ou visualizacao pairwise)
    else:
        if show_2d_pca:
            _decision_pca_by_obj_2d(X_landscape, F_landscape, X_true, X_emp_list,
                                    title, **kw)
        if show_3d_pca:
            _decision_pca_by_obj_3d(X_landscape, F_landscape, X_true, X_emp_list,
                                    title, **kw)
        _decision_pairwise(problem, X_landscape, X_true, X_emp_list, title,
                           pair_vars=pair_vars, **kw)


def _resolve_landscape_cmap(cmap):
    """Return a matplotlib Colormap from a name string.

    ``'Greys'`` → a lighter variant good for background landscapes.
    Any other name → ``plt.get_cmap(name)`` verbatim.
    """
    import matplotlib.colors as mcolors
    if cmap == 'Greys':
        base = plt.get_cmap('Greys')
        s = base(np.linspace(0, 1, 256))
        s[:, :3] = 0.7 * s[:, :3] + 0.3
        return mcolors.LinearSegmentedColormap.from_list('Greys_light', s)
    return plt.get_cmap(cmap)


# ── 2-var heatmap: multi-variant (F_variants) ────────────────────────────

def _decision_heatmap_2d_multi(problem, X, F_variants, X_true, X_emp_list,
                                title, true_color='white', emp_colors=None,
                                emp_names=None, cmap='Greys', **_kw):
    """Multiple rows of 2D heatmaps, one per F variant.

    Parameters
    ----------
    F_variants : list of (name, F_ndarray)
        Each entry is (label, ndarray of shape (N, n_obj)).
    """
    resolved_cmap = _resolve_landscape_cmap(cmap)
    n_obj = F_variants[0][1].shape[1]
    n_rows = len(F_variants)

    fig, axes = plt.subplots(n_rows, n_obj, figsize=(9 * n_obj, 8 * n_rows),
                             squeeze=False)
    fig.subplots_adjust(top=1 - 0.06 / n_rows, hspace=0.32)
    if title:
        fig.suptitle(f'{title} — Espaço de Decisão', fontsize=20,
                     fontweight='bold', y=1 - 0.01 / n_rows)

    for vi, (vname, F_v) in enumerate(F_variants):
        for j in range(n_obj):
            ax = axes[vi, j]
            sc = ax.scatter(X[:, 0], X[:, 1], c=F_v[:, j], cmap=resolved_cmap,
                            alpha=0.9, s=8, edgecolor='none')
            _scatter_colored(ax, X_true[:, 0], X_true[:, 1], true_color,
                             s=20, label='PS teórico', zorder=10)
            for k, X_emp in enumerate(X_emp_list):
                c = emp_colors[k % len(emp_colors)]
                lbl = emp_names[k] if emp_names else f'PS emp. {k+1}'
                _scatter_colored(ax, X_emp[:, 0], X_emp[:, 1], c,
                                 s=60, label=lbl, zorder=11 + k)
            num = vi * n_obj + j + 1
            ax.set_title(f'{num}. {vname}: $f_{{{j+1}}}$',
                         fontsize=14, fontweight='bold')
            ax.set_xlabel('$x_1$', fontsize=12)
            ax.set_ylabel('$x_2$', fontsize=12)
            ax.set_xlim(problem.xl[0], problem.xu[0])
            ax.set_ylim(problem.xl[1], problem.xu[1])
            fig.colorbar(sc, ax=ax, label=f'$f_{{{j+1}}}$')

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center',
               bbox_to_anchor=(0.5, 1 - 0.03 / n_rows),
               ncol=min(len(X_emp_list) + 1, 5), fontsize=13,
               frameon=True, facecolor='white', framealpha=0.9)
    plt.tight_layout(rect=[0, 0, 1, 1 - 0.05 / n_rows])
    plt.show()
    return fig


# ── 2-var heatmap (same style as plot_landscapes_heatmap_dashboard_v2) ───

def _decision_heatmap_2d(problem, X, F, X_true, X_emp_list, title,
                         true_color='white', emp_colors=None, emp_names=None,
                         cmap='Greys', **_kw):
    resolved_cmap = _resolve_landscape_cmap(cmap)

    n_obj = F.shape[1]
    fig, axes = plt.subplots(1, n_obj, figsize=(9 * n_obj, 8))
    if n_obj == 1:
        axes = [axes]
    fig.subplots_adjust(top=0.82)

    if title:
        fig.suptitle(f'{title} \u2014 Espa\u00e7o de Decis\u00e3o', fontsize=18,
                     fontweight='bold', y=0.97)

    for j, ax in enumerate(axes):
        sc = ax.scatter(X[:, 0], X[:, 1], c=F[:, j], cmap=resolved_cmap,
                        alpha=0.9, s=8, edgecolor='none')

        _scatter_colored(ax, X_true[:, 0], X_true[:, 1], true_color,
                         s=20, label='PS teórico', zorder=10)
        for k, X_emp in enumerate(X_emp_list):
            c = emp_colors[k % len(emp_colors)]
            lbl = emp_names[k] if emp_names else f'PS emp. {k+1}'
            _scatter_colored(ax, X_emp[:, 0], X_emp[:, 1], c,
                             s=60, label=lbl, zorder=11 + k)

        ax.set_title(f'Objetivo $f_{j+1}$', fontsize=14, fontweight='bold')
        ax.set_xlabel('$x_1$', fontsize=12)
        ax.set_ylabel('$x_2$', fontsize=12)
        ax.set_xlim(problem.xl[0], problem.xu[0])
        ax.set_ylim(problem.xl[1], problem.xu[1])
        fig.colorbar(sc, ax=ax, label=f'$f_{j+1}$')

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.935),
               ncol=min(len(X_emp_list) + 1, 4), fontsize=14,
               frameon=True, facecolor='white', framealpha=0.9)
    plt.show()
    return fig


# \u2500\u2500 3-var scatter \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _decision_scatter_3d(problem, X, F, X_true, X_emp_list, title,
                         true_color='white', emp_colors=None, emp_names=None,
                         cmap='Greys',
                         elev_offset=-15, azim_offset=225, roll_offset=0):
    resolved_cmap = _resolve_landscape_cmap(cmap)
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')

    sc = ax.scatter(X[:, 0], X[:, 1], X[:, 2], c=F[:, 0],
                    cmap=resolved_cmap, s=2, alpha=0.15, depthshade=False)

    _scatter_colored(ax, X_true[:, 0], X_true[:, 1], true_color,
                     s=8, label='PS teórico', zorder=9, z=X_true[:, 2], alpha=0.5)
    for k, X_emp in enumerate(X_emp_list):
        c = emp_colors[k % len(emp_colors)]
        lbl = emp_names[k] if emp_names else f'PS emp. {k+1}'
        _scatter_colored(ax, X_emp[:, 0], X_emp[:, 1], c,
                         s=30, label=lbl, zorder=10 + k, z=X_emp[:, 2])

    ax.set_xlabel('$x_1$', fontsize=11, labelpad=6)
    ax.set_ylabel('$x_2$', fontsize=11, labelpad=6)
    ax.set_zlabel('$x_3$', fontsize=11, labelpad=6)
    ax.legend(fontsize=11, loc='upper right')
    ax.view_init(elev=25 + elev_offset, azim=45 + azim_offset, roll=roll_offset)
    fig.colorbar(sc, ax=ax, shrink=0.5, label='$f_1$')

    if title:
        ax.set_title(f'{title} \u2014 Espaço de Decisão (3D)',
                     fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.show()
    return fig


# \u2500\u2500 high-dim: PCA projection \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _scatter_colored(ax, x, y, color, s, label, zorder, z=None, **kw):
    """Scatter with smart edge: 'white' → white fill + black edge, else solid."""
    if color == 'white':
        fc, ec = 'white', 'black'
    else:
        fc, ec = color, {'red': 'darkred', 'royalblue': 'navy'}.get(color, 'black')
    if z is not None:
        ax.scatter(x, y, z, c=fc, edgecolors=ec, s=s, linewidths=0.8,
                   zorder=zorder, label=label, depthshade=False, **kw)
    else:
        ax.scatter(x, y, c=fc, edgecolors=ec, s=s, linewidths=0.8,
                   zorder=zorder, label=label, **kw)


def _pca_fit(X, X_true, X_emp_list, n_components):
    """Fit PCA on all data; return (Z_bg, Z_true, [Z_emp_1, …], var_ratio)."""
    from sklearn.decomposition import PCA
    pca = PCA(n_components=n_components)
    parts = [X, X_true] + list(X_emp_list)
    X_all = np.vstack(parts)
    Z_all = pca.fit_transform(X_all)
    offset = 0
    Z_bg = Z_all[offset:offset + len(X)]; offset += len(X)
    Z_true = Z_all[offset:offset + len(X_true)]; offset += len(X_true)
    Z_emps = []
    for xe in X_emp_list:
        Z_emps.append(Z_all[offset:offset + len(xe)]); offset += len(xe)
    return Z_bg, Z_true, Z_emps, pca.explained_variance_ratio_


def _light_grey_cmap():
    import matplotlib.colors as mcolors
    base = plt.get_cmap('Greys')
    s = base(np.linspace(0, 1, 256))
    s[:, :3] = 0.7 * s[:, :3] + 0.3
    return mcolors.LinearSegmentedColormap.from_list('Greys_light_pca', s)


# Row 1: PCA 2D + 3D unified (single colour, no objective split)

def _decision_pca_unified(X, F, X_true, X_emp_list, title,
                          true_color='white', emp_colors=None, emp_names=None,
                          cmap='Greys',
                          elev_offset=-15, azim_offset=225, roll_offset=0):
    Z2_bg, Z2_true, Z2_emps, var2 = _pca_fit(X, X_true, X_emp_list, 2)
    Z3_bg, Z3_true, Z3_emps, var3 = _pca_fit(X, X_true, X_emp_list, 3)

    fig = plt.figure(figsize=(18, 8))
    fig.subplots_adjust(top=0.82)
    if title:
        fig.suptitle(f'{title} — PCA (visão única)',
                     fontsize=18, fontweight='bold', y=0.97)

    ax2d = fig.add_subplot(1, 2, 1)
    ax2d.scatter(Z2_bg[:, 0], Z2_bg[:, 1], c='lightgray', s=8, alpha=0.3)
    _scatter_colored(ax2d, Z2_true[:, 0], Z2_true[:, 1], true_color,
                     s=20, label=f'PS teórico ({len(X_true)} pts)', zorder=10, alpha=0.8)
    for k, Z2_emp in enumerate(Z2_emps):
        c = emp_colors[k % len(emp_colors)]
        lbl = emp_names[k] if emp_names else f'PS emp. {k+1}'
        _scatter_colored(ax2d, Z2_emp[:, 0], Z2_emp[:, 1], c,
                         s=50, label=f'{lbl} ({len(Z2_emp)} pts)', zorder=11 + k, alpha=0.9)
    ax2d.set_xlabel(f'PC1 ({var2[0]:.1%})', fontsize=12)
    ax2d.set_ylabel(f'PC2 ({var2[1]:.1%})', fontsize=12)
    ax2d.set_title('PCA 2D', fontsize=14, fontweight='bold')
    ax2d.grid(True, alpha=0.3, linestyle='--')

    ax3d = fig.add_subplot(1, 2, 2, projection='3d')
    ax3d.scatter(Z3_bg[:, 0], Z3_bg[:, 1], Z3_bg[:, 2],
                 c='lightgray', s=2, alpha=0.1, depthshade=False)
    _scatter_colored(ax3d, Z3_true[:, 0], Z3_true[:, 1], true_color,
                     s=8, label='PS teórico', zorder=9, z=Z3_true[:, 2], alpha=0.5)
    for k, Z3_emp in enumerate(Z3_emps):
        c = emp_colors[k % len(emp_colors)]
        lbl = emp_names[k] if emp_names else f'PS emp. {k+1}'
        _scatter_colored(ax3d, Z3_emp[:, 0], Z3_emp[:, 1], c,
                         s=30, label=lbl, zorder=10 + k, z=Z3_emp[:, 2])
    ax3d.set_xlabel(f'PC1 ({var3[0]:.1%})', fontsize=9, labelpad=4)
    ax3d.set_ylabel(f'PC2 ({var3[1]:.1%})', fontsize=9, labelpad=4)
    ax3d.set_zlabel(f'PC3 ({var3[2]:.1%})', fontsize=9, labelpad=4)
    ax3d.set_title('PCA 3D', fontsize=14, fontweight='bold')
    ax3d.view_init(elev=25 + elev_offset, azim=45 + azim_offset, roll=roll_offset)

    handles, labels = ax2d.get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.935),
               ncol=min(len(X_emp_list) + 1, 4), fontsize=14,
               frameon=True, facecolor='white', framealpha=0.9)
    plt.tight_layout()
    plt.show()
    return fig


# Row 2: PCA 2D per objective (coloured by f_j)

def _decision_pca_by_obj_2d(X, F, X_true, X_emp_list, title,
                            true_color='white', emp_colors=None, emp_names=None,
                            cmap='Greys', **_kw):
    Z_bg, Z_true, Z_emps, var = _pca_fit(X, X_true, X_emp_list, 2)
    resolved_cmap = _resolve_landscape_cmap(cmap)
    n_obj = F.shape[1]

    fig, axes = plt.subplots(1, n_obj, figsize=(9 * n_obj, 8))
    if n_obj == 1:
        axes = [axes]
    fig.subplots_adjust(top=0.82)
    if title:
        fig.suptitle(f'{title} — PCA 2D por objetivo',
                     fontsize=18, fontweight='bold', y=0.97)

    for j, ax in enumerate(axes):
        sc = ax.scatter(Z_bg[:, 0], Z_bg[:, 1], c=F[:, j], cmap=resolved_cmap,
                        alpha=0.9, s=8, edgecolor='none')
        _scatter_colored(ax, Z_true[:, 0], Z_true[:, 1], true_color,
                         s=20, label='PS teórico', zorder=10)
        for k, Z_emp in enumerate(Z_emps):
            c = emp_colors[k % len(emp_colors)]
            lbl = emp_names[k] if emp_names else f'PS emp. {k+1}'
            _scatter_colored(ax, Z_emp[:, 0], Z_emp[:, 1], c,
                             s=60, label=lbl, zorder=11 + k)
        ax.set_title(f'Objetivo $f_{j+1}$', fontsize=14, fontweight='bold')
        ax.set_xlabel(f'PC1 ({var[0]:.1%})', fontsize=12)
        ax.set_ylabel(f'PC2 ({var[1]:.1%})', fontsize=12)
        fig.colorbar(sc, ax=ax, label=f'$f_{j+1}$')

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.935),
               ncol=min(len(X_emp_list) + 1, 4), fontsize=14,
               frameon=True, facecolor='white', framealpha=0.9)
    plt.show()
    return fig


# Row 3: PCA 3D per objective (coloured by f_j)

def _decision_pca_by_obj_3d(X, F, X_true, X_emp_list, title,
                            true_color='white', emp_colors=None, emp_names=None,
                            cmap='Greys',
                            elev_offset=-15, azim_offset=225, roll_offset=0):
    Z_bg, Z_true, Z_emps, var = _pca_fit(X, X_true, X_emp_list, 3)
    resolved_cmap = _resolve_landscape_cmap(cmap)
    n_obj = F.shape[1]

    fig = plt.figure(figsize=(9 * n_obj, 8))
    fig.subplots_adjust(top=0.82)
    if title:
        fig.suptitle(f'{title} — PCA 3D por objetivo',
                     fontsize=18, fontweight='bold', y=0.97)

    for j in range(n_obj):
        ax = fig.add_subplot(1, n_obj, j + 1, projection='3d')
        sc = ax.scatter(Z_bg[:, 0], Z_bg[:, 1], Z_bg[:, 2],
                        c=F[:, j], cmap=resolved_cmap, s=2, alpha=0.15, depthshade=False)
        _scatter_colored(ax, Z_true[:, 0], Z_true[:, 1], true_color,
                         s=10, label='PS teórico', zorder=10, z=Z_true[:, 2])
        for k, Z_emp in enumerate(Z_emps):
            c = emp_colors[k % len(emp_colors)]
            lbl = emp_names[k] if emp_names else f'PS emp. {k+1}'
            _scatter_colored(ax, Z_emp[:, 0], Z_emp[:, 1], c,
                             s=30, label=lbl, zorder=11 + k, z=Z_emp[:, 2])
        ax.set_title(f'Objetivo $f_{j+1}$', fontsize=14, fontweight='bold')
        ax.set_xlabel(f'PC1 ({var[0]:.1%})', fontsize=9, labelpad=4)
        ax.set_ylabel(f'PC2 ({var[1]:.1%})', fontsize=9, labelpad=4)
        ax.set_zlabel(f'PC3 ({var[2]:.1%})', fontsize=9, labelpad=4)
        ax.view_init(elev=25 + elev_offset, azim=45 + azim_offset, roll=roll_offset)
        fig.colorbar(sc, ax=ax, shrink=0.6, label=f'$f_{j+1}$')

    ax0 = fig.axes[0]
    handles, labels = ax0.get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.935),
               ncol=min(len(X_emp_list) + 1, 4), fontsize=14,
               frameon=True, facecolor='white', framealpha=0.9)
    plt.tight_layout()
    plt.show()
    return fig


# \u2500\u2500 high-dim: pairwise 2-D grid \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _decision_pairwise(problem, X, X_true, X_emp_list, title, pair_vars=None,
                       true_color='white', emp_colors=None, emp_names=None,
                       cmap='Greys', **_kw):
    tc_fill = 'white' if true_color == 'white' else true_color
    tc_edge = 'black' if true_color == 'white' else \
              {'red': 'darkred', 'royalblue': 'navy'}.get(true_color, 'black')

    if pair_vars is not None:
        cols = [v - 1 for v in pair_vars]
    else:
        cols = list(range(problem.n_var))

    k = len(cols)
    fig, axes = plt.subplots(k, k, figsize=(3 * k, 3 * k))
    if k == 1:
        axes = np.array([[axes]])

    for ri, ci in enumerate(cols):
        for rj, cj in enumerate(cols):
            ax = axes[ri, rj]
            if ci == cj:
                ax.hist(X[:, ci], bins=50, color='lightgray', edgecolor='gray')
                ax.hist(X_true[:, ci], bins=30, color=tc_fill, edgecolor=tc_edge,
                        alpha=0.5)
            else:
                ax.scatter(X[:, cj], X[:, ci], c='lightgray', s=1, alpha=0.1,
                           rasterized=True)
                ax.scatter(X_true[:, cj], X_true[:, ci], c=tc_fill,
                           edgecolors=tc_edge, s=3, linewidths=0.3,
                           alpha=0.4, zorder=10)
                for m, X_emp in enumerate(X_emp_list):
                    ec_fill = emp_colors[m % len(emp_colors)]
                    ec_edge = {'red': 'darkred', 'royalblue': 'navy',
                               'green': 'darkgreen', 'orange': 'darkorange',
                               'purple': 'darkviolet'}.get(ec_fill, 'black')
                    ax.scatter(X_emp[:, cj], X_emp[:, ci], c=ec_fill,
                               edgecolors=ec_edge, s=8, linewidths=0.2,
                               alpha=0.8, zorder=11 + m)

            if ri == k - 1:
                ax.set_xlabel(f'$x_{{{cj+1}}}$', fontsize=8)
            else:
                ax.set_xticklabels([])
            if rj == 0:
                ax.set_ylabel(f'$x_{{{ci+1}}}$', fontsize=8)
            else:
                ax.set_yticklabels([])

    if title:
        fig.suptitle(f'{title} — Pairwise Decision Space',
                     fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.show()
    return fig