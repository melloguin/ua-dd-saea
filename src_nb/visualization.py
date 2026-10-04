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


# ═══════════════════════════════════════════════════════════════════════════
#  Memória de cálculo das três métricas do cap. 5 (03/10/2026): as figuras passo a passo e o relatório HTML.
#  Entrada: o dicionário `mem` de `metricas(..., memoria=True)` (notebook 2) ou de `src_nb.metrics.reconstruir_memoria`
#  (chaves `hv`, `igd_plus`, `cpf`), e a frente de referência Z do problema. Estilo das fichas
#  "HV, IGD e IGD+ na prática".
# ═══════════════════════════════════════════════════════════════════════════

import io, base64, html as _html
from pathlib import Path
from matplotlib.patches import Rectangle
from src_nb import metrics as _MET

_PAL = dict(Z='#b8b8b8', A='#1f77b4', r='#c2570a', seta='#2e8b57', caixa='#9ed4a9')

def _axes3d(fig, pos):
    ax = fig.add_subplot(pos, projection='3d'); ax.view_init(elev=22, azim=40); return ax

def _rotulos(ax, M, prefixo='f'):
    ax.set_xlabel(f'${prefixo}_1$ (normalizado)'); ax.set_ylabel(f'${prefixo}_2$ (normalizado)')
    if M == 3: ax.set_zlabel(f'${prefixo}_3$ (normalizado)')

def fig_hv(mem, Z, titulo):
    """HV: os retângulos (2 obj) ou as contribuições exclusivas (3 obj) de cada ponto até r = (1,1; …)."""
    h = mem['hv']; M = h['M']; A = h['A_dentro']; r = h['r']
    fig = plt.figure(figsize=(12.5, 4.6))
    if M == 2:
        ax = fig.add_subplot(121)
        ax.scatter(Z[:, 0], Z[:, 1], s=2, c=_PAL['Z'], label='frente de referência $Z$')
        if 'A_ord' not in h:                                   # nenhum ponto domina r: HV = 0 por definição
            h = {**h, 'A_ord': np.empty((0, 2)), 'largura': np.empty(0), 'altura': np.empty(0), 'area': np.empty(0), 'hv_varredura': 0.0}
        for f1, f2, w, hh in zip(h['A_ord'][:, 0], h['A_ord'][:, 1], h['largura'], h['altura']):
            ax.add_patch(Rectangle((f1, f2), w, hh, facecolor=_PAL['caixa'], edgecolor='#2e8b57', lw=0.5, alpha=0.55))
        fora = h['A'][~h['dentro']]
        if len(fora): ax.scatter(fora[:, 0], fora[:, 1], s=22, marker='x', c='k', label=f'fora de r ({len(fora)}): contribuem 0')
        if len(A): ax.scatter(A[:, 0], A[:, 1], s=16, c=_PAL['A'], zorder=3, label=f'$A$ (|A| = {len(A)})')
        ax.plot(r[0], r[1], 's', c=_PAL['r'], ms=7, label='r = (1,1; 1,1)')
        ax.set_xlim(min(-0.02, h['A'][:, 0].min() - 0.02), 1.15); ax.set_ylim(min(-0.02, h['A'][:, 1].min() - 0.02), 1.15); _rotulos(ax, 2)
        ax.set_title(f'HV puro = Σ área dos retângulos = {h["hv"]:.4f}   ·   HV da frente = {h["hv_frente"]:.4f}   ·   HV normalizado = {h["hv_norm"]:.4f}', fontsize=9.5)
        ax.legend(fontsize=7, frameon=False, loc='upper right')
        ax2 = fig.add_subplot(122)
        ax2.bar(range(len(A)), h['area'], color=_PAL['caixa'], edgecolor='#2e8b57', label='área do retângulo (varredura por $f_1$)')
        if h.get('contrib') is not None and len(A): ax2.plot(range(len(A)), h['contrib'][np.argsort(A[:, 0], kind='stable')], 'o-', ms=3, c=_PAL['r'], lw=1, label='contribuição exclusiva')
        ax2.set_xlabel('pontos de $A$ ordenados por $f_1$'); ax2.set_ylabel('área'); ax2.legend(fontsize=7, frameon=False)
        ax2.set_title(f'varredura: Σ = {h["hv_varredura"]:.4f} (pymoo: {h["hv"]:.4f})', fontsize=10)
    else:
        ax = _axes3d(fig, 121); Zd = Z[::max(1, len(Z) // 4000)]
        ax.scatter(Zd[:, 0], Zd[:, 1], Zd[:, 2], s=1, c=_PAL['Z'], alpha=0.5)
        tam = 12 + 300 * (h['contrib'] / max(h['contrib'].max(), 1e-12)) if h.get('contrib') is not None and len(A) else 12
        ax.scatter(A[:, 0], A[:, 1], A[:, 2], s=tam, c=_PAL['A'], alpha=0.9)
        ax.scatter([r[0]], [r[1]], [r[2]], s=50, marker='s', c=_PAL['r']); _rotulos(ax, 3)
        ax.set_title(f'HV puro = volume dominado até r = (1,1)³ = {h["hv"]:.4f}  ·  HV da frente = {h["hv_frente"]:.4f}  ·  HV normalizado = {h["hv_norm"]:.4f}\n|A| = {len(A)} (tamanho do ponto proporcional à contribuição exclusiva)', fontsize=9)
        ax2 = fig.add_subplot(122)
        if h.get('contrib') is not None and len(A):
            c = np.sort(h['contrib'])[::-1]; ax2.bar(range(len(c)), c, color=_PAL['caixa'], edgecolor='#2e8b57')
            ax2.set_title(f'contribuição exclusiva de cada ponto, decrescente (Σ = {c.sum():.4f} de {h["hv"]:.4f})', fontsize=9)
        ax2.set_xlabel('pontos de $A$'); ax2.set_ylabel('hv(A) − hv(A sem o ponto)')
    for a in fig.axes: a.spines[['top', 'right']].set_visible(False) if hasattr(a, 'spines') and a.name != '3d' else None
    fig.suptitle(titulo, fontsize=11); fig.tight_layout(); return fig

def fig_igdplus(mem, titulo, n_setas=80):
    """IGD+: cada z da referência, o seu ponto de A mais próximo em d⁺ e a projeção p = max(a, z); a média dos d⁺ é o IGD+."""
    g = mem['igd_plus']; A, Z, dp, p = g['A'], g['Z'], g['dplus'], g['p']; M = Z.shape[1]
    fig = plt.figure(figsize=(12.5, 4.6))
    passo = max(1, int(np.ceil(len(Z) / n_setas))); sel = np.arange(0, len(Z), passo)
    if M == 2:
        ax = fig.add_subplot(121)
        sc = ax.scatter(Z[:, 0], Z[:, 1], s=6, c=dp, cmap='YlOrRd', vmin=0, label='$Z$ (cor = $d^+$)')
        for i in sel:
            if dp[i] > 0: ax.annotate('', xy=(p[i, 0], p[i, 1]), xytext=(Z[i, 0], Z[i, 1]), arrowprops=dict(arrowstyle='->', color=_PAL['seta'], lw=0.6, alpha=0.8))
        ax.scatter(A[:, 0], A[:, 1], s=16, c='k', zorder=3, label=f'$A$ (|A| = {len(A)})')
        ax.set_xlim(-0.02, max(1.05, A[:, 0].max() + 0.05)); ax.set_ylim(-0.02, max(1.05, A[:, 1].max() + 0.05)); _rotulos(ax, 2)
        plt.colorbar(sc, ax=ax, shrink=0.8, label='$d^+(z, A)$'); ax.legend(fontsize=7, frameon=False, loc='upper right')
        ax.set_title(f'IGD+ = média de $d^+$ sobre os {len(Z)} z = {g["igd_plus"]:.4f}   (IGD comum: {g["igd"]:.4f})\nsetas: z → projeção p em {len(sel)} dos z', fontsize=9)
    else:
        ax = _axes3d(fig, 121)
        sc = ax.scatter(Z[:, 0], Z[:, 1], Z[:, 2], s=3, c=dp, cmap='YlOrRd', vmin=0, alpha=0.8)
        ax.scatter(A[:, 0], A[:, 1], A[:, 2], s=14, c='k'); _rotulos(ax, 3)
        plt.colorbar(sc, ax=ax, shrink=0.6, label='$d^+(z, A)$')
        ax.set_title(f'IGD+ = média de $d^+$ sobre os {len(Z)} z = {g["igd_plus"]:.4f}   (IGD comum: {g["igd"]:.4f})', fontsize=9)
    ax2 = fig.add_subplot(122)
    ax2.hist(dp, bins=40, color=_PAL['caixa'], edgecolor='#2e8b57'); ax2.axvline(g['igd_plus'], c=_PAL['r'], lw=1.5, label=f'média = IGD+ = {g["igd_plus"]:.4f}')
    ax2.set_xlabel('$d^+(z, A)$ por ponto de referência'); ax2.set_ylabel('nº de z'); ax2.legend(fontsize=8, frameon=False)
    zer = int((dp == 0).sum()); cob = g['cobertura_por_a']
    ax2.set_title(f'{zer} de {len(Z)} z com $d^+$ = 0 (dominados por A) · {int((cob > 0).sum())} de {len(A)} pontos de A servem algum z', fontsize=9)
    ax2.spines[['top', 'right']].set_visible(False)
    fig.suptitle(titulo, fontsize=11); fig.tight_layout(); return fig

def fig_cpf(mem, titulo):
    """CPF_K20: (esq.) o passo 2 — cada s levado ao ponto mais próximo da frente z*; (dir.) os passos 3–5 — a régua com os cubos."""
    c = mem['cpf']; M = c['Z'].shape[1]; S1, Z1, Ss = c['S1'], c['Z1'], c['S_star']; cs, cz = c['cob_S'], c['cob_Z']
    fig = plt.figure(figsize=(12.5, 4.6))
    if M == 2:
        ax = fig.add_subplot(121)
        ax.scatter(Z1[:, 0], Z1[:, 1], s=2, c=_PAL['Z'], label='$Z$ (reescalada pelo mín/máx de $Z$)')
        for s, j in zip(S1, c['j_star']):
            ax.annotate('', xy=(Z1[j, 0], Z1[j, 1]), xytext=(s[0], s[1]), arrowprops=dict(arrowstyle='->', color=_PAL['seta'], lw=0.6, alpha=0.7))
        ax.scatter(S1[:, 0], S1[:, 1], s=14, c=_PAL['A'], label=f'$S$ (|S| = {len(S1)})')
        ax.scatter(Ss[:, 0], Ss[:, 1], s=26, facecolors='none', edgecolors=_PAL['r'], lw=1.0, label=f'$z^*$ únicos ({len(Ss)}; {c["n_duplicados"]} duplicatas)')
        ax.set_xlim(-0.05, max(1.05, S1[:, 0].max() + 0.05)); ax.set_ylim(-0.05, max(1.05, S1[:, 1].max() + 0.05)); _rotulos(ax, 2)
        ax.set_title('passos 1–2: reescalar por $Z$ e levar cada $s$ ao $z^*$ mais próximo', fontsize=9); ax.legend(fontsize=7, frameon=False, loc='upper right')
        ax2 = fig.add_subplot(122)
        yZ = c['yZ'][:, 0]
        ax2.vlines(yZ, 0.78, 0.98, colors=_PAL['Z'], lw=0.3)
        for lo, up in zip(cz['lower'][:, 0], cz['upper'][:, 0]): ax2.add_patch(Rectangle((lo, 0.55), up - lo, 0.18, facecolor=_PAL['Z'], edgecolor='none', alpha=0.9))
        for lo, up, y in zip(cs['lower'][:, 0], cs['upper'][:, 0], c['yS'][:, 0]):
            ax2.add_patch(Rectangle((lo, 0.1), up - lo, 0.3, facecolor=_PAL['caixa'], edgecolor='#2e8b57', lw=0.8)); ax2.plot([y], [0.25], '|', c=_PAL['A'], ms=10, mew=1.3)
        ax2.plot([0.02, 0.02 + cs['cota_lado']], [-0.08, -0.08], c=_PAL['r'], lw=3); ax2.text(0.02, -0.2, f'cota = VPF/max(20, {len(Ss)}) = VPF/{c["K"]} = {c["cota_vol"]:.4f}', fontsize=8, color=_PAL['r'])
        ax2.set_xlim(-0.02, 1.02); ax2.set_ylim(-0.3, 1.05); ax2.set_yticks([0.25, 0.64, 0.88]); ax2.set_yticklabels(['segmentos de $S^*$\n(lado ≤ cota)', 'segmentos de $Z$\n(VPF)', 'posições $y$ de $Z$'], fontsize=8)
        ax2.set_xlabel('régua: $y = (f_1 - f_2 + 1)/2$ — a posição ao longo da frente')
        ax2.set_title(f'passos 3–5: V = Σ segmentos de $S^*$ = {c["V"]:.4f} · VPF = {c["VPF"]:.4f} · CPF_K20 = V/VPF = {c["cpf"]:.4f}', fontsize=9)
    else:
        ax = _axes3d(fig, 121); Zd = Z1[::max(1, len(Z1) // 4000)]
        ax.scatter(Zd[:, 0], Zd[:, 1], Zd[:, 2], s=1, c=_PAL['Z'], alpha=0.5)
        ax.scatter(S1[:, 0], S1[:, 1], S1[:, 2], s=12, c=_PAL['A']); ax.scatter(Ss[:, 0], Ss[:, 1], Ss[:, 2], s=18, c=_PAL['r'], marker='x'); _rotulos(ax, 3)
        ax.set_title(f'passos 1–2: $S$ (azul) → $z^*$ (×): |S| = {len(S1)}, {len(Ss)} únicos', fontsize=9)
        ax2 = fig.add_subplot(122)
        for lo, up in zip(cz['lower'], cz['upper']): ax2.add_patch(Rectangle(lo, up[0] - lo[0], up[1] - lo[1], facecolor=_PAL['Z'], edgecolor='none', alpha=0.6))
        for lo, up in zip(cs['lower'], cs['upper']): ax2.add_patch(Rectangle(lo, up[0] - lo[0], up[1] - lo[1], facecolor=_PAL['caixa'], edgecolor='#2e8b57', lw=0.7, alpha=0.85))
        ax2.scatter(c['yS'][:, 0], c['yS'][:, 1], s=6, c=_PAL['A']); ax2.set_xlim(0, 1); ax2.set_ylim(0, 1); ax2.set_aspect('equal')
        ax2.set_xlabel('régua $y_1$'); ax2.set_ylabel('régua $y_2$')
        ax2.set_title(f'passos 3–5 (cinza: cubos de $Z$, VPF = {c["VPF"]:.4f}; verde: cubos de $S^*$, lado ≤ {cs["cota_lado"]:.3f})\nV = Σ cubos de $S^*$ = {c["V"]:.4f} · CPF_K20 = V/VPF = {c["cpf"]:.4f}', fontsize=9)
    fig.suptitle(titulo, fontsize=11); fig.tight_layout(); return fig

def _img_b64(fig, dpi=85, qualidade=85):
    """Figura → JPEG (qualidade 85) em base64: ~55 KB por figura; em PNG seriam ~110 KB e o relatório de 315 passaria de 100 MB."""
    buf = io.BytesIO(); fig.savefig(buf, format='jpeg', dpi=dpi, bbox_inches='tight', pil_kwargs={'quality': qualidade}); plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('ascii')


_CSS = """body{font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;max-width:1180px;margin:24px auto;padding:0 18px;color:#222;line-height:1.45}
h1{font-size:1.5em;border-bottom:2px solid #2e8b57;padding-bottom:6px} h2{font-size:1.15em;margin-top:38px;border-left:5px solid #2e8b57;padding-left:10px}
h3{font-size:1em;margin:14px 0 4px} table{border-collapse:collapse;font-size:.9em;margin:8px 0} td,th{border:1px solid #ddd;padding:3px 9px;text-align:right} th{background:#f2f2f2}
td:first-child,th:first-child{text-align:left} img{max-width:100%;border:1px solid #eee;margin:4px 0} .cap{font-size:.86em;color:#555;margin:0 0 14px} .idx a{margin-right:12px;font-size:.9em}
.nota{background:#f6f9f6;border:1px solid #cfe3d3;padding:8px 12px;font-size:.9em}"""

_CAP_HV  = ("<b>HV, passo a passo.</b> Os objetivos já estão normalizados pela régua S.5 do problema. Só os pontos que dominam r = (1,1; …) contribuem; "
            "o HV normalizado é o HV puro dividido pelo HV da frente de referência (o máximo atingível no problema), de modo que 1 é a frente inteira; "
            "em 2 objetivos a varredura por f₁ decompõe a região dominada em retângulos disjuntos (ponto i: largura até o f₁ do próximo ponto, altura até r₂) e o HV é a soma das áreas; "
            "em 3 objetivos o pymoo calcula o volume exato e cada ponto é desenhado com tamanho proporcional à sua contribuição exclusiva hv(A) − hv(A sem o ponto).")
_CAP_IGD = ("<b>IGD+, passo a passo.</b> Para cada ponto z da frente de referência Z (uniforme), procura-se o ponto a de A que minimiza d⁺(z, a) = √Σ max(aᵢ − zᵢ, 0)² "
            "— só as coordenadas em que a é pior que z contam; a seta vai de z à projeção p = max(a, z), e some quando a domina z (d⁺ = 0). O IGD+ é a média dos d⁺ sobre todos os z; "
            "o histograma mostra a distribuição e quantos z ficaram cobertos. O IGD comum (euclidiano) aparece só para contraste.")
_CAP_CPF = ("<b>CPF_K20, passo a passo.</b> (1) S e Z são reescalados pelo mínimo e máximo de Z; (2) cada s é levado ao ponto z* mais próximo da frente (setas) e z* repetidos contam uma vez — "
            "a partir daqui só importa onde na frente a solução caiu; (3) z* e Z são projetados na régua (em 2 objetivos, y = (f₁ − f₂ + 1)/2); (4) cada ponto ganha um segmento (cubo) "
            "de lado igual à distância ao vizinho mais próximo, limitado à cota VPF/max(20, N), com N = nº de z* únicos — VPF é o que a própria Z ocupa sem cota; (5) CPF_K20 = Σ volumes ÷ VPF, em [0, 1]. "
            "Em 3 objetivos a régua é o quadrado unitário e os segmentos viram quadrados.")


def relatorio_html(itens, arquivo, buscar, nomes=None, titulo='Memória de cálculo das métricas', dpi=85):
    """HTML autocontido com, para cada (algoritmo, problema, seed) de `itens`, a tabela das métricas e as três figuras
    passo a passo (HV · IGD+ · CPF_K20). `buscar(algoritmo, problema, seed)` devolve `(m, mem, Z)`: a linha de métricas,
    a memória de cálculo (gravada ou recalculada) e a frente de referência (None no DDMOP7). `nomes` mapeia o id da
    configuração ao nome de exibição. Devolve o DataFrame das métricas dos itens."""
    import pandas as pd
    try:
        from tqdm.auto import tqdm
    except ImportError:                       # pragma: no cover
        tqdm = lambda x, **k: x
    nomes = nomes or {}
    secoes, linhas, indice = [], [], []
    for k, (alg, prob, seed) in enumerate(tqdm(list(itens), desc='relatório')):
        m, mem, Z = buscar(alg, prob, seed)
        nome = nomes.get(alg, alg); rot = f'{nome} · {prob} · seed {seed}'; aid = f'e{k}'
        indice.append(f'<a href="#{aid}">{_html.escape(rot)}</a>')
        if m is None or m.get('erro'):
            secoes.append(f'<h2 id="{aid}">{_html.escape(rot)}</h2><p class="nota">sem endpoint: '
                          f'{_html.escape(str(m.get("erro") if m else "célula sem avaliação real registrada"))}</p>'); continue
        linhas.append({'algoritmo': alg, 'nome': nome, 'problema': prob, 'seed': seed,
                       **{c: m[c] for c in ('hv', 'hv_frente', 'hv_norm', 'igd_plus', 'cpf_k20', 'n_nd', 'n_star', 'n_aval') if c in m}})
        f4 = lambda v: '—' if v is None or (isinstance(v, float) and np.isnan(v)) else f'{v:.4f}'
        tab = ('<table><tr><th>hv puro</th><th>hv da frente</th><th>hv normalizado</th><th>igd_plus</th><th>cpf_k20</th>'
               '<th>|S| = n_nd</th><th>z* únicos</th><th>avaliações reais</th></tr>'
               f'<tr><td>{f4(m["hv"])}</td><td>{f4(m["hv_frente"])}</td><td>{f4(m["hv_norm"])}</td><td>{f4(m["igd_plus"])}</td>'
               f'<td>{f4(m["cpf_k20"])}</td><td>{int(m["n_nd"])}</td><td>{int(m["n_star"]) if m["n_star"] == m["n_star"] else "—"}</td>'
               f'<td>{int(m["n_aval"])}</td></tr></table>')
        Zf = Z if Z is not None else mem['hv']['A'][:0]
        figs_ = [f'<h3>HV</h3><img src="data:image/jpeg;base64,{_img_b64(fig_hv(mem, Zf, rot), dpi)}"><p class="cap">{_CAP_HV}</p>']
        if 'igd_plus' in mem:
            figs_.append(f'<h3>IGD+</h3><img src="data:image/jpeg;base64,{_img_b64(fig_igdplus(mem, rot), dpi)}"><p class="cap">{_CAP_IGD}</p>')
            figs_.append(f'<h3>CPF_K20</h3><img src="data:image/jpeg;base64,{_img_b64(fig_cpf(mem, rot), dpi)}"><p class="cap">{_CAP_CPF}</p>')
        else:
            figs_.append('<p class="nota">DDMOP7 não tem frente de referência (D102.4): só o HV puro é reportado.</p>')
        secoes.append(f'<h2 id="{aid}">{_html.escape(rot)}</h2>{tab}' + ''.join(figs_))
    cab = (f'<h1>{_html.escape(titulo)}</h1><p class="nota">Espaço normalizado pela régua S.5 de cada problema; r = 1,1 por coordenada '
           f'(D69); frente de referência Z uniforme (2 objetivos: {_MET.N_REF_UNIFORME[2]} pontos por comprimento de arco; 3 objetivos: '
           f'{_MET.N_REF_UNIFORME[3]} por ponto mais distante; frentes empíricas como estão); HV normalizado = HV / HV da frente; '
           f'CPF com cota VPF/max({_MET.CPF_K}, N). {len(secoes)} experimentos.</p><p class="idx">' + ' '.join(indice) + '</p>')
    Path(arquivo).write_text(f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>{_html.escape(titulo)}</title>'
                             f'<style>{_CSS}</style></head><body>{cab}{"".join(secoes)}</body></html>', encoding='utf-8')
    print(f'→ {arquivo}  ({Path(arquivo).stat().st_size/1e6:.1f} MB, {len(secoes)} experimentos)')
    return pd.DataFrame(linhas)
