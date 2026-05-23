"""Visualisation helpers shared by notebooks ``1. fitness_landscape`` and
``2. optimization``.

Public API
----------
``display_pareto_fronts_catalog``
    Render one PF teórico + N empirical fronts in objective space.
``display_decision_space``
    Render the decision-space landscape with the PS teórico + N empirical
    point sets. Dispatches between 2D heatmap, 3D scatter and PCA grids
    depending on ``problem.n_var``.

Both functions accept **one or many** empirical sets:

* Pass a single ``ndarray`` (or a list with one ndarray) → one set is drawn.
* Pass a list of ndarrays → every set is drawn with its own colour/label.

The same code path handles either case; nothing extra is needed for the
multi-set view beyond passing the lists.
"""

import os

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 6)
plt.rcParams['lines.linewidth'] = 0.5


# ═══════════════════════════════════════════════════════════════════════════
#  Cache de imagens (compartilhado pelas funcoes publicas de visualizacao)
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_IMAGE_CACHE_DIR = 'data/images'
DEFAULT_IMAGE_DPI = 300


def _image_cache_path(cache_dir, cache_name, cache_tag, kind):
    """Resolve o caminho do arquivo de cache para uma figura.

    Retorna ``None`` quando ``cache_name`` nao for fornecido (cache desativado).
    Estrutura: ``{cache_dir}/{cache_name}/{cache_tag}_{kind}.png``
    (``cache_tag`` opcional — sem prefixo se None).
    """
    if not cache_name:
        return None
    base = cache_dir or DEFAULT_IMAGE_CACHE_DIR
    fname = f'{cache_tag}_{kind}.png' if cache_tag else f'{kind}.png'
    return os.path.join(base, cache_name, fname)


def _try_display_cached_image(path):
    """Se ``path`` aponta para uma imagem existente, exibe e retorna True."""
    if not path or not os.path.exists(path):
        return False
    try:
        from IPython.display import Image, display
        display(Image(filename=path))
    except ImportError:
        img = plt.imread(path)
        fig, ax = plt.subplots(figsize=(12, 10))
        ax.imshow(img)
        ax.axis('off')
        plt.show()
    print(f'  Imagem carregada do cache: {path}')
    return True


def _save_figure(fig, path, dpi=DEFAULT_IMAGE_DPI):
    """Salva a figura em alta qualidade (cria diretorios se necessario)."""
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    print(f'  Imagem salva em: {path}')


# ═══════════════════════════════════════════════════════════════════════════
#  Catalog-aware PF visualisation
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
                                  emp_color='red',
                                  cache_dir=None,
                                  cache_name=None,
                                  cache_tag=None,
                                  load_cache_image=False):
    """Mostra o Pareto front teórico + N fronts empíricos sobre a landscape.

    Suporta problemas com 2 ou 3 objetivos (2D ou 3D). O número de fronts
    empíricos é livre — passe **uma lista** com ``[front_1, front_2, ...]``
    e cada elemento é plotado com a cor/rótulo correspondente.

    Parameters
    ----------
    problem : Problem
        Instância do catálogo (precisa ter ``true_pareto_front``).
    F_landscape : np.ndarray (N, n_obj)
        Valores dos objetivos amostrados (background cinza).
    pareto_fronts_list : list of np.ndarray, optional
        Lista de arrays ``(M_i, n_obj)`` com fronts empíricos.
        Use 1, 2, 3 … N elementos — cada um é desenhado com sua cor/nome.
    front_names : list of str, optional
        Rótulo por front empírico (mesma ordem de ``pareto_fronts_list``).
    sample_size : int
        Máximo de pontos do landscape a plotar (subsampling).
    front_colors : list of str, optional
        Cor por front empírico (mesma ordem).
    title : str, optional
    elev_offset, azim_offset, roll_offset : float
        Rotações adicionais (graus) só para gráficos 3D.
    xlim, ylim, zlim : tuple, optional
        Limites manuais dos eixos. None = automático.
    true_color : str
        Cor do PF teórico. ``'white'`` → branco com contorno preto.
    emp_color : str
        Cor default do primeiro empírico quando ``front_colors`` é None.
    cache_dir, cache_name, cache_tag : str, optional
        Configuracao do cache de imagens. Quando ``cache_name`` eh fornecido,
        a figura gerada eh salva em
        ``{cache_dir or 'data/images'}/{cache_name}/{cache_tag}_{kind}.png``
        (``cache_tag`` opcional). ``kind`` eh ``pareto_2d`` ou ``pareto_3d``.
    load_cache_image : bool
        Quando True e a imagem cacheada existir, exibe o arquivo salvo em
        vez de regenerar o plot.
    """
    n_obj = problem.n_obj
    kind = 'pareto_2d' if n_obj == 2 else 'pareto_3d'
    save_path = _image_cache_path(cache_dir, cache_name, cache_tag, kind)

    if load_cache_image and _try_display_cached_image(save_path):
        return None

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
                           colors, actual, title, xlim, ylim, true_color,
                           save_path=save_path)
    else:
        return _plot_pf_3d(F_bg, F_true, pareto_fronts_list, front_names,
                           colors, actual, title,
                           elev_offset, azim_offset, roll_offset,
                           xlim, ylim, zlim, true_color,
                           save_path=save_path)


def _nice_limits(arrays, axis):
    """Exact min/max across all plotted arrays on the given axis."""
    vals = np.concatenate([a[:, axis] for a in arrays if len(a) > 0])
    return float(vals.min()), float(vals.max())


def _plot_pf_2d(F_bg, F_true, fronts, names, colors, n_sample,
                title, xlim=None, ylim=None, true_color='white',
                save_path=None):
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

    ax.set_xlabel('f₁', fontsize=13, fontweight='bold')
    ax.set_ylabel('f₂', fontsize=13, fontweight='bold')
    ax.legend(fontsize=14, loc='upper right')
    ax.grid(True, alpha=0.3, linestyle='--')

    all_F = [F_bg, F_true] + list(fronts)
    ax.set_xlim(*(xlim if xlim is not None else _nice_limits(all_F, axis=0)))
    ax.set_ylim(*(ylim if ylim is not None else _nice_limits(all_F, axis=1)))

    if title:
        ax.set_title(title, fontsize=15, fontweight='bold')
    plt.tight_layout()
    _save_figure(fig, save_path)
    plt.show()
    return fig


def _plot_pf_3d(F_bg, F_true, fronts, names, colors, n_sample,
                title, elev_offset=-15, azim_offset=225, roll_offset=0,
                xlim=None, ylim=None, zlim=None, true_color='white',
                save_path=None):
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

    ax.set_xlabel('f₁', fontsize=11, fontweight='bold', labelpad=6)
    ax.set_ylabel('f₂', fontsize=11, fontweight='bold', labelpad=6)
    ax.set_zlabel('f₃', fontsize=11, fontweight='bold', labelpad=6)
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
    _save_figure(fig, save_path)
    plt.show()
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  Decision-space (landscape) visualisation
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
                           cache_dir=None, cache_name=None, cache_tag=None,
                           load_cache_image=False):
    """Dispatch decision-space plots based on ``n_var``.

    Aceita **um ou vários** conjuntos empíricos de pontos no espaço de
    decisão. Os mesmos quatro layouts (2D heatmap, 3D scatter, PCA-2D por
    objetivo, PCA-3D por objetivo) sobrepõem todos os conjuntos passados.

    Parameters
    ----------
    problem : Problem
    X_landscape : ndarray (N, n_var)
    F_landscape : ndarray (N, n_obj)
    X_true : ndarray  – pontos do PS teórico.
    X_emp_list : ndarray OR list of ndarray
        Um conjunto empírico (ndarray) ou vários (lista). Um único ndarray é
        automaticamente envelopado em ``[X_emp_list]``. Passe ``[X1, X2, X3]``
        para mostrar 3 origens distintas (e.g. 3 algoritmos ou 3 amostragens).
    title : str, optional
    pair_vars : list of int (1-indexed)
        Variáveis para o grid pairwise (n_var > 3). None = todas.
    true_color : str
        Cor do PS teórico (``'white'`` → branco c/ contorno preto).
    emp_colors : list of str, optional
        Uma cor por conjunto em ``X_emp_list``.
    emp_names : list of str, optional
        Um rótulo por conjunto em ``X_emp_list``.
    emp_color : str, optional
        Atalho retro-compatível: se um único string for passado e
        ``emp_colors`` for None, vira a cor de todos os conjuntos.
    cmap : str
        Colormap do landscape (``'Greys'`` default).
    show_2d_pca, show_3d_pca : bool
        Habilita/desabilita as grades de PCA para n_var > 3.
    elev_offset, azim_offset, roll_offset : float
        Rotações 3D (mesma convenção de ``display_pareto_fronts_catalog``).
    cache_dir, cache_name, cache_tag : str, optional
        Configuracao do cache de imagens. Quando ``cache_name`` eh fornecido,
        cada sub-figura gerada eh salva em
        ``{cache_dir or 'data/images'}/{cache_name}/{cache_tag}_{kind}.png``.
        Kinds: ``decision_heatmap_2d``, ``decision_scatter_3d``,
        ``decision_pca_2d``, ``decision_pca_3d``, ``decision_pairwise``.
    load_cache_image : bool
        Quando True e a imagem cacheada existir, exibe o arquivo salvo em
        vez de regenerar o plot (avaliado por sub-figura individualmente).
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

    def _path(kind):
        return _image_cache_path(cache_dir, cache_name, cache_tag, kind)

    def _cached_or_call(kind, generator):
        path = _path(kind)
        if load_cache_image and _try_display_cached_image(path):
            return
        generator(path)

    # 2 variáveis de decisão (plot 2d landscape)
    if n == 2:
        _cached_or_call(
            'decision_heatmap_2d',
            lambda p: _decision_heatmap_2d(problem, X_landscape, F_landscape,
                                           X_true, X_emp_list, title,
                                           save_path=p, **kw))

    # 3 variáveis de decisão (plot 3d landscape)
    elif n == 3:
        _cached_or_call(
            'decision_scatter_3d',
            lambda p: _decision_scatter_3d(problem, X_landscape, F_landscape,
                                           X_true, X_emp_list, title,
                                           save_path=p, **kw))

    # > 3 variáveis de decisão (necessita redução ou visualizacao pairwise)
    else:
        if show_2d_pca:
            _cached_or_call(
                'decision_pca_2d',
                lambda p: _decision_pca_by_obj_2d(X_landscape, F_landscape,
                                                  X_true, X_emp_list, title,
                                                  save_path=p, **kw))
        if show_3d_pca:
            _cached_or_call(
                'decision_pca_3d',
                lambda p: _decision_pca_by_obj_3d(X_landscape, F_landscape,
                                                  X_true, X_emp_list, title,
                                                  save_path=p, **kw))
        _cached_or_call(
            'decision_pairwise',
            lambda p: _decision_pairwise(problem, X_landscape, X_true,
                                         X_emp_list, title,
                                         pair_vars=pair_vars,
                                         save_path=p, **kw))


def _resolve_landscape_cmap(cmap):
    """Return a matplotlib Colormap from a name string."""
    if cmap == 'Greys':
        base = plt.get_cmap('Greys')
        s = base(np.linspace(0, 1, 256))
        s[:, :3] = 0.7 * s[:, :3] + 0.3
        return mcolors.LinearSegmentedColormap.from_list('Greys_light', s)
    return plt.get_cmap(cmap)


# ── 2-var heatmap ────────────────────────────────────────────────────────

def _decision_heatmap_2d(problem, X, F, X_true, X_emp_list, title,
                         true_color='white', emp_colors=None, emp_names=None,
                         cmap='Greys', save_path=None, **_kw):
    """2D heatmap landscape with one or more overlaid empirical PS sets.

    ``X_emp_list`` é sempre uma lista — passe ``[X1]`` para um conjunto ou
    ``[X1, X2, X3]`` para múltiplos.
    """
    resolved_cmap = _resolve_landscape_cmap(cmap)

    n_obj = F.shape[1]
    fig, axes = plt.subplots(1, n_obj, figsize=(9 * n_obj, 8))
    if n_obj == 1:
        axes = [axes]
    fig.subplots_adjust(top=0.82)

    if title:
        fig.suptitle(f'{title} — Espaço de Decisão', fontsize=18,
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
    _save_figure(fig, save_path)
    plt.show()
    return fig


# ── 3-var scatter ────────────────────────────────────────────────────────

def _decision_scatter_3d(problem, X, F, X_true, X_emp_list, title,
                         true_color='white', emp_colors=None, emp_names=None,
                         cmap='Greys',
                         elev_offset=-15, azim_offset=225, roll_offset=0,
                         save_path=None):
    """3D landscape scatter with one or more overlaid empirical PS sets.

    ``X_emp_list`` é sempre uma lista — passe ``[X1]`` para um conjunto ou
    ``[X1, X2, X3]`` para múltiplos.
    """
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
        ax.set_title(f'{title} — Espaço de Decisão (3D)',
                     fontsize=15, fontweight='bold')
    plt.tight_layout()
    _save_figure(fig, save_path)
    plt.show()
    return fig


# ── helpers compartilhados ───────────────────────────────────────────────

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


# PCA 2D per objective (coloured by f_j)
def _decision_pca_by_obj_2d(X, F, X_true, X_emp_list, title,
                            true_color='white', emp_colors=None, emp_names=None,
                            cmap='Greys', save_path=None, **_kw):
    """PCA-2D per objective with one or more overlaid empirical PS sets.

    ``X_emp_list`` é sempre uma lista — passe ``[X1]`` para um conjunto ou
    ``[X1, X2, X3]`` para múltiplos.
    """
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
    _save_figure(fig, save_path)
    plt.show()
    return fig


# PCA 3D per objective (coloured by f_j)
def _decision_pca_by_obj_3d(X, F, X_true, X_emp_list, title,
                            true_color='white', emp_colors=None, emp_names=None,
                            cmap='Greys',
                            elev_offset=-15, azim_offset=225, roll_offset=0,
                            save_path=None):
    """PCA-3D per objective with one or more overlaid empirical PS sets.

    ``X_emp_list`` é sempre uma lista — passe ``[X1]`` para um conjunto ou
    ``[X1, X2, X3]`` para múltiplos.
    """
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
    _save_figure(fig, save_path)
    plt.show()
    return fig


# Pairwise 2-D grid (for n_var > 3)
def _decision_pairwise(problem, X, X_true, X_emp_list, title, pair_vars=None,
                       true_color='white', emp_colors=None, emp_names=None,
                       cmap='Greys', save_path=None, **_kw):
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
    _save_figure(fig, save_path)
    plt.show()
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  GIF de evolução do Pareto front (usado pelo dashboard Streamlit)
# ═══════════════════════════════════════════════════════════════════════════

def gerar_gif_pareto_evolucao(problem, F_landscape, df_evolution, output_path,
                              fps=4, xlim=None, ylim=None,
                              sample_size=20_000,
                              true_color='white', emp_color='red',
                              dpi=90):
    """Gera GIF da evolução do Pareto front empírico, geração a geração,
    sobre a fitness landscape — usando o mesmo estilo de
    :func:`display_pareto_fronts_catalog` (suporta apenas problemas bi-objetivo).

    O PF teórico do problema é renderizado em TODOS os frames; o front
    empírico é o conjunto de pontos da geração ``g`` extraído de
    ``df_evolution``.

    Parameters
    ----------
    problem : Problem
        Instância do catálogo (com ``true_pareto_front`` e ``n_obj == 2``).
    F_landscape : np.ndarray (N, 2)
        Pontos da fitness landscape (background cinza).
    df_evolution : pd.DataFrame
        Subset de ``data/experiments/all.parquet`` para um único
        (algoritmo, problema, seed). Deve conter ao menos as colunas
        ``generation``, ``f1`` e ``f2``.
    output_path : str
        Caminho do arquivo .gif a salvar.
    fps : int
        Frames por segundo (default 4).
    xlim, ylim : tuple (lo, hi), optional
        Limites dos eixos. None = automático (delegado a ``_plot_pf_2d``).
    sample_size : int
        Máximo de pontos do landscape por frame (subsampling).
    true_color, emp_color : str
        Cores do PF teórico e do front empírico.
    dpi : int
        DPI dos frames gerados (90 = compacto; 100 = padrão).

    Returns
    -------
    str
        ``output_path`` (caminho absoluto do GIF gerado).
    """
    import imageio.v3 as imageio
    import io
    import os

    if problem.n_obj != 2:
        raise ValueError("gerar_gif_pareto_evolucao só suporta problemas bi-objetivo.")
    if df_evolution.empty:
        raise ValueError("df_evolution está vazio — nada a renderizar.")

    _, F_true = problem.true_pareto_front()
    gens = sorted(df_evolution['generation'].unique())

    # Subsample fixo da landscape (mesmo background em todos os frames)
    actual_bg = min(sample_size, len(F_landscape))
    rng = np.random.default_rng(42)
    idx_bg = rng.choice(len(F_landscape), actual_bg, replace=False)
    F_bg = F_landscape[idx_bg]

    frames = []
    g_last = gens[-1]
    for g in gens:
        F_pop = df_evolution.loc[df_evolution['generation'] == g, ['f1', 'f2']].values
        fig = _plot_pf_2d(
            F_bg, F_true, [F_pop], [f'Geração {g}'],
            [emp_color], actual_bg,
            title=f'{type(problem).__name__} — Geração {g}/{g_last}',
            xlim=xlim, ylim=ylim, true_color=true_color,
        )
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
        buf.seek(0)
        frames.append(imageio.imread(buf))
        buf.close()
        plt.close(fig)

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    imageio.imwrite(output_path, frames, duration=1000 / fps, loop=0)
    return os.path.abspath(output_path)
