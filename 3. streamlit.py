"""
3. streamlit.py — Dashboard SAEA

Consolida métricas (HV/IGD/Gamma/Delta + Multicritério) e visualizações
(Pareto fronts, decision space, pairplot, GIF de evolução) por
algoritmo × problema, a partir de:
  - data/experiments/all.parquet            (resultados por geração)
  - data/dataframes/{prob}/df_{prob}_landscape_latin_hypercube.parquet

Uso:
    streamlit run "3. streamlit.py"
"""

# IMPORTANTE: usar backend não-interativo ANTES de importar pyplot.
# Muitas funções de src.visualization chamam plt.show() internamente —
# com backend Agg, isso é no-op e podemos capturar a Figure normalmente.
import matplotlib
matplotlib.use('Agg')

import io
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st

# Tornar src/ importável
REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from pymoo.indicators.hv import HV
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting
from scipy.spatial.distance import cdist

from src.experiment import _instantiate_problem
from src.visualization import (
    display_pareto_fronts_catalog,
    _decision_heatmap_2d,
    _decision_scatter_3d,
    _decision_pca_by_obj_2d,
    _decision_pca_by_obj_3d,
    _decision_pairwise,
    gerar_gif_pareto_evolucao,
)


# ═══════════════════════════════════════════════════════════════════════════
#  Constantes globais
# ═══════════════════════════════════════════════════════════════════════════

ALGORITHMS = ['NSGA2_surrogate', 'DR-NSGA-II', 'Prob-MOEA/D',
              'K-RVEA', 'ParEGO', 'KTA2']
PROBLEMS = [
    'MMF1', 'MMF4', 'MMF11_L', 'MMF16_L3', 'MMF16_20',
    'ZDT1', 'ZDT3', 'ZDT4', 'ZDT6',
    'DTLZ1', 'DTLZ2', 'DTLZ3', 'DTLZ4', 'DTLZ7',
    'WFG1', 'WFG2', 'WFG4', 'WFG5', 'WFG9',
    'BBOB1', 'BBOB5', 'BBOB17', 'BBOB22', 'BBOB37', 'BBOB49', 'BBOB55',
]
METRIC_DIRECTION = {'HV': 'max', 'IGD': 'min', 'Gamma': 'min', 'Delta': 'min'}
METRIC_LABELS = {'Hypervolume': 'HV', 'IGD': 'IGD', 'Gamma': 'Gamma',
                 'Delta': 'Delta', 'Multicritério': 'Multicritério'}
SAMPLING_METHOD = 'latin_hypercube'
PLOT_3D_PCA = {'MMF16_20', 'DTLZ1', 'DTLZ2', 'DTLZ3', 'DTLZ4', 'DTLZ7'}
OUT_2D_PCA = {'MMF16_20'}
GIF_CACHE_DIR = REPO_ROOT / 'data' / 'gifs' / 'streamlit_cache'
LANDSCAPE_DIR = REPO_ROOT / 'data' / 'dataframes'
ALL_PARQUET = REPO_ROOT / 'data' / 'experiments' / 'all.parquet'

_NDS = NonDominatedSorting(method='efficient_non_dominated_sort')


# ═══════════════════════════════════════════════════════════════════════════
#  PLOT_CONFIG por problema (extraído do notebook 1)
# ═══════════════════════════════════════════════════════════════════════════

def _cfg(xlim=None, ylim=None, zlim=None, elev=-15, azim=225, roll=0,
         pair_vars=None, true_color='white', emp_color='red'):
    return dict(xlim=xlim, ylim=ylim, zlim=zlim,
                elev=elev, azim=azim, roll=roll,
                pair_vars=pair_vars,
                true_color=true_color, emp_color=emp_color)


PLOT_CONFIG = {
    # MMF (CEC 2020)
    'MMF1':     _cfg(),
    'MMF4':     _cfg(),
    'MMF11_L':  _cfg(),
    'MMF16_L3': _cfg(elev=-27, true_color='red', emp_color='white'),
    'MMF16_20': _cfg(pair_vars=[1, 2, 20]),
    # ZDT
    'ZDT1': _cfg(elev=-27, pair_vars=[1, 2]),
    'ZDT3': _cfg(pair_vars=[1, 2]),
    'ZDT4': _cfg(pair_vars=[1, 2]),
    'ZDT6': _cfg(pair_vars=[1, 2]),
    # DTLZ
    'DTLZ1': _cfg(xlim=(0, 100),  ylim=(0, 100),  zlim=(0, 100),  pair_vars=[1, 2, 3]),
    'DTLZ2': _cfg(xlim=(0, 2),    ylim=(0, 2),    zlim=(0, 2),    pair_vars=[1, 2, 3]),
    'DTLZ3': _cfg(xlim=(0, 1000), ylim=(0, 1000), zlim=(0, 1000), pair_vars=[1, 2, 3]),
    'DTLZ4': _cfg(xlim=(0, 2),    ylim=(0, 2),    zlim=(0, 2),    pair_vars=[1, 2, 3]),
    'DTLZ7': _cfg(zlim=(0, 20), pair_vars=[1, 2, 3]),
    # WFG
    'WFG1': _cfg(pair_vars=[1, 2, 3]),
    'WFG2': _cfg(pair_vars=[1, 2, 3]),
    'WFG4': _cfg(pair_vars=[1, 2, 3]),
    'WFG5': _cfg(pair_vars=[1, 2, 3]),
    'WFG9': _cfg(pair_vars=[1, 2, 3]),
    # BBOB
    'BBOB1':  _cfg(xlim=(0, 210),       ylim=(0, 210),  elev=-27, pair_vars=[1, 2, 3, 4]),
    'BBOB5':  _cfg(xlim=(0, 220),       ylim=(0, 3200), elev=-27, pair_vars=[1, 2, 3, 4]),
    'BBOB17': _cfg(xlim=(0, 5_000_000), ylim=(0, 200),  elev=-27, pair_vars=[1, 2, 3, 4]),
    'BBOB22': _cfg(xlim=(0, 500_000),   ylim=(0, 2000), elev=-27, pair_vars=[1, 2, 3, 4]),
    'BBOB37': _cfg(xlim=(0, 3500),      ylim=(0, 7000), elev=-27, pair_vars=[1, 2, 4, 5]),
    'BBOB49': _cfg(xlim=(0, 5000),                       elev=-27, pair_vars=[1, 3, 7, 9]),
    'BBOB55': _cfg(elev=-27, pair_vars=[1, 3, 5, 6]),
}


# ═══════════════════════════════════════════════════════════════════════════
#  Loaders cacheados
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def load_all_parquet() -> pd.DataFrame:
    return pd.read_parquet(ALL_PARQUET)


@st.cache_data(show_spinner=False)
def load_landscape(problem: str):
    """Retorna (X_landscape, F_landscape) como arrays numpy."""
    fp = LANDSCAPE_DIR / problem / f'df_{problem}_landscape_{SAMPLING_METHOD}.parquet'
    if not fp.exists():
        return None, None
    df = pd.read_parquet(fp)
    x_cols = sorted([c for c in df.columns if c.startswith('x_')],
                    key=lambda c: int(c.split('_')[1]))
    f_cols = sorted([c for c in df.columns if c.startswith('f') and c[1:].isdigit()],
                    key=lambda c: int(c[1:]))
    return df[x_cols].values.astype(float), df[f_cols].values.astype(float)


@st.cache_resource(show_spinner=False)
def get_problem(name: str):
    return _instantiate_problem(name)


# ═══════════════════════════════════════════════════════════════════════════
#  Métricas (HV, IGD, Gamma, Delta)  — cópia verbatim do notebook 2
# ═══════════════════════════════════════════════════════════════════════════

def compute_hypervolume(F, ref_point):
    return float(HV(ref_point=ref_point)(F))


def compute_igd(F_approx, F_true):
    D = cdist(F_true, F_approx)
    return float(np.mean(np.min(D, axis=1)))


def compute_gamma(F_approx, F_true):
    D = cdist(F_approx, F_true)
    return float(np.mean(np.min(D, axis=1)))


def compute_delta(F_approx, F_true):
    if len(F_approx) < 2:
        return float('inf')
    n_obj = F_approx.shape[1]
    idx_sort = np.lexsort(F_approx[:, ::-1].T)
    F_sorted = F_approx[idx_sort]
    d = np.array([np.linalg.norm(F_sorted[i + 1] - F_sorted[i])
                  for i in range(len(F_sorted) - 1)])
    if len(d) == 0:
        return float('inf')
    d_bar = d.mean()
    D_to_true = cdist(F_true, F_approx)
    extremes_true_idx = [np.argmin(F_true[:, j]) for j in range(n_obj)]
    d_f = np.min(D_to_true[extremes_true_idx[0]])
    d_l = np.min(D_to_true[extremes_true_idx[-1]])
    denom = d_f + d_l + len(d) * d_bar
    if denom == 0:
        return 0.0
    return float((d_f + d_l + np.sum(np.abs(d - d_bar))) / denom)


def evaluate_metrics(F_approx, problem, n_pf_points=500):
    _, F_true = problem.true_pareto_front(n_pf_points) \
        if 'n' in problem.true_pareto_front.__code__.co_varnames \
        else problem.true_pareto_front()
    ref_point = np.max(F_true, axis=0) * 1.1 + 0.01
    out = {}
    try:
        out['HV'] = compute_hypervolume(F_approx, ref_point)
    except Exception:
        out['HV'] = np.nan
    try:
        out['IGD'] = compute_igd(F_approx, F_true)
    except Exception:
        out['IGD'] = np.nan
    try:
        out['Gamma'] = compute_gamma(F_approx, F_true)
    except Exception:
        out['Gamma'] = np.nan
    try:
        out['Delta'] = compute_delta(F_approx, F_true)
    except Exception:
        out['Delta'] = np.nan
    return out


# ═══════════════════════════════════════════════════════════════════════════
#  Agregação: build_metric_table
# ═══════════════════════════════════════════════════════════════════════════

def _f_cols(df):
    return sorted([c for c in df.columns if c.startswith('f') and c[1:].isdigit()],
                  key=lambda c: int(c[1:]))


@st.cache_data(show_spinner='Calculando métricas …')
def build_metric_table(parquet_mtime: float) -> pd.DataFrame:
    """Para cada (problem, algo, seed): pega última geração → F_pop → 4 métricas.
    Agrega pela média entre seeds. Retorna long-format DataFrame com colunas
    ['problem','algorithm','HV','IGD','Gamma','Delta'].

    O argumento ``parquet_mtime`` é apenas a chave de cache (mtime do parquet).
    """
    df = load_all_parquet()
    rows = []
    for problem_name in df['problem'].unique():
        try:
            problem_obj = get_problem(problem_name)
        except Exception:
            continue
        sub = df[df['problem'] == problem_name]
        f_cols = _f_cols(sub)
        for algo in sub['algorithm'].unique():
            sub_a = sub[sub['algorithm'] == algo]
            per_seed = []
            for seed in sub_a['seed'].unique():
                sub_s = sub_a[sub_a['seed'] == seed]
                last_gen = sub_s['generation'].max()
                F_pop = sub_s.loc[sub_s['generation'] == last_gen, f_cols].values.astype(float)
                if len(F_pop) == 0:
                    continue
                m = evaluate_metrics(F_pop, problem_obj)
                per_seed.append(m)
            if not per_seed:
                continue
            avg = {k: np.nanmean([d[k] for d in per_seed]) for k in ('HV', 'IGD', 'Gamma', 'Delta')}
            rows.append({'problem': problem_name, 'algorithm': algo, **avg})
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════
#  Multicritério
# ═══════════════════════════════════════════════════════════════════════════

def apply_multicriterion(table: pd.DataFrame, weights: dict) -> pd.DataFrame:
    """Normaliza min-max cada métrica POR PROBLEMA (1 = melhor) e calcula a
    média ponderada das 4 colunas normalizadas. Adiciona 'Multicritério'
    (round 3)."""
    out = table.copy()
    for m in ('HV', 'IGD', 'Gamma', 'Delta'):
        out[m + '_norm'] = np.nan
    for problem, sub in table.groupby('problem'):
        for m in ('HV', 'IGD', 'Gamma', 'Delta'):
            x = sub[m].values.astype(float)
            valid = ~np.isnan(x)
            if valid.sum() == 0:
                continue
            lo = np.nanmin(x)
            hi = np.nanmax(x)
            if hi == lo:
                norm = np.where(valid, 1.0, np.nan)
            else:
                norm = (x - lo) / (hi - lo)
                if METRIC_DIRECTION[m] == 'min':
                    norm = 1.0 - norm
            out.loc[sub.index, m + '_norm'] = norm
    w = np.array([weights[k] for k in ('HV', 'IGD', 'Gamma', 'Delta')], dtype=float)
    if w.sum() == 0:
        w = np.ones(4)
    w = w / w.sum()
    mat = out[['HV_norm', 'IGD_norm', 'Gamma_norm', 'Delta_norm']].values
    out['Multicritério'] = np.round(np.nansum(mat * w, axis=1), 3)
    # Se TODAS as 4 métricas são NaN, o resultado também é NaN
    all_nan = np.all(np.isnan(mat), axis=1)
    out.loc[all_nan, 'Multicritério'] = np.nan
    return out


# ═══════════════════════════════════════════════════════════════════════════
#  Tabela de métricas: pivot, linha TOTAL, highlight de vencedor
# ═══════════════════════════════════════════════════════════════════════════

def render_metric_table(table_long: pd.DataFrame, metric_name: str):
    """Retorna um Styler para st.dataframe — 26+1 linhas × 6 colunas (algos)."""
    pivot = table_long.pivot_table(index='problem', columns='algorithm',
                                   values=metric_name, aggfunc='mean')
    pivot = pivot.reindex(index=PROBLEMS, columns=ALGORITHMS).astype(float).round(3)
    total = pivot.mean(axis=0, skipna=True).to_frame().T.round(3)
    total.index = ['TOTAL']
    full = pd.concat([total, pivot])

    direction = METRIC_DIRECTION.get(metric_name, 'max')  # Multicritério → max

    def _highlight(row):
        vals = row.values.astype(float)
        if np.all(np.isnan(vals)):
            return [''] * len(row)
        if direction == 'max':
            best = np.nanargmax(vals)
        else:
            best = np.nanargmin(vals)
        styles = [''] * len(row)
        styles[best] = 'background-color: #90EE90; font-weight: bold;'
        return styles

    return full.style.apply(_highlight, axis=1).format('{:.3f}', na_rep='—')


# ═══════════════════════════════════════════════════════════════════════════
#  Ordem dos algoritmos por Multicritério médio (melhor → pior)
# ═══════════════════════════════════════════════════════════════════════════

def compute_algo_order(table_long: pd.DataFrame) -> list:
    s = (table_long
         .groupby('algorithm')['Multicritério']
         .mean()
         .sort_values(ascending=False))
    order = list(s.index)
    # Acrescenta algoritmos faltantes (sem dados) ao final
    for a in ALGORITHMS:
        if a not in order:
            order.append(a)
    return order


# ═══════════════════════════════════════════════════════════════════════════
#  Gráfico: # de 1º lugares por algoritmo, 1 linha por métrica
# ═══════════════════════════════════════════════════════════════════════════

def build_wins_chart(table_long: pd.DataFrame, algo_order: list):
    metrics = ['HV', 'IGD', 'Gamma', 'Delta', 'Multicritério']
    rows = []
    for m in metrics:
        direction = METRIC_DIRECTION.get(m, 'max')
        wins = {a: 0 for a in algo_order}
        for problem, sub in table_long.groupby('problem'):
            x = sub[['algorithm', m]].dropna()
            if x.empty:
                continue
            if direction == 'max':
                winner = x.loc[x[m].idxmax(), 'algorithm']
            else:
                winner = x.loc[x[m].idxmin(), 'algorithm']
            wins[winner] = wins.get(winner, 0) + 1
        for a in algo_order:
            rows.append({'algorithm': a, 'metric': m, 'wins': wins[a]})
    df_w = pd.DataFrame(rows)
    fig = px.line(df_w, x='algorithm', y='wins', color='metric',
                  markers=True,
                  category_orders={'algorithm': algo_order},
                  title='# de 1º lugares por algoritmo (algoritmos ordenados pelo Multicritério)')
    fig.update_layout(yaxis_title='# vitórias (de 26 problemas)',
                      xaxis_title='Algoritmo (melhor → pior em Multicritério)',
                      height=420)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  Construção de fronts/X por algoritmo para um problema
# ═══════════════════════════════════════════════════════════════════════════

def _nds_filter(F):
    return _NDS.do(F, only_non_dominated_front=True)


def build_algo_arrays(df_all: pd.DataFrame, problem: str, algos: list):
    """Retorna dois dicts {algo: F_array} e {algo: X_array}, agregando todas as
    seeds (última geração de cada), com NDS-filter aplicado no espaço de
    objetivos."""
    sub = df_all[df_all['problem'] == problem]
    if sub.empty:
        return {}, {}
    x_cols = sorted([c for c in sub.columns if c.startswith('x_')],
                    key=lambda c: int(c.split('_')[1]))
    f_cols = _f_cols(sub)
    out_F, out_X = {}, {}
    for algo in algos:
        sub_a = sub[sub['algorithm'] == algo]
        if sub_a.empty:
            continue
        parts_F, parts_X = [], []
        for seed in sub_a['seed'].unique():
            sub_s = sub_a[sub_a['seed'] == seed]
            last_gen = sub_s['generation'].max()
            last = sub_s[sub_s['generation'] == last_gen]
            parts_F.append(last[f_cols].values.astype(float))
            parts_X.append(last[x_cols].values.astype(float))
        F = np.vstack(parts_F)
        X = np.vstack(parts_X)
        idx = _nds_filter(F)
        out_F[algo] = F[idx]
        out_X[algo] = X[idx]
    return out_F, out_X


# ═══════════════════════════════════════════════════════════════════════════
#  Helpers de visualização: matplotlib Figure → bytes PNG para Streamlit
# ═══════════════════════════════════════════════════════════════════════════

def fig_to_png_bytes(fig, width_px=600, height_px=600, dpi=100):
    fig.set_size_inches(width_px / dpi, height_px / dpi)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════
#  Renderizadores dos 4 quadrantes
# ═══════════════════════════════════════════════════════════════════════════

def render_pareto_fronts(problem_obj, F_landscape, algo_fronts, cfg):
    """Esquerda superior: display_pareto_fronts_catalog."""
    if F_landscape is None:
        return None
    names = list(algo_fronts.keys())
    fronts = list(algo_fronts.values())
    kw = dict(pareto_fronts_list=fronts, front_names=names,
              true_color=cfg['true_color'], emp_color=cfg['emp_color'])
    if problem_obj.n_obj == 2:
        kw['xlim'] = cfg['xlim']
        kw['ylim'] = cfg['ylim']
    else:
        kw['xlim'] = cfg['xlim']
        kw['ylim'] = cfg['ylim']
        kw['zlim'] = cfg['zlim']
        kw['elev_offset'] = cfg['elev']
        kw['azim_offset'] = cfg['azim']
        kw['roll_offset'] = cfg['roll']
    return display_pareto_fronts_catalog(problem_obj, F_landscape, **kw)


_DEFAULT_EMP_COLORS = ['red', 'green', 'orange', 'purple', 'brown',
                       'pink', 'cyan', 'magenta', 'yellow']


def render_decision_space(problem_obj, X_landscape, F_landscape, algo_X, cfg,
                          show_2d_pca: bool, show_3d_pca: bool):
    """Direita superior: decision space (heatmap/scatter/PCA, sem pairwise)."""
    if X_landscape is None:
        return None
    X_true, _ = problem_obj.true_pareto_front()
    X_emp_list = list(algo_X.values()) or [np.zeros((0, problem_obj.n_var))]
    emp_names = list(algo_X.keys()) or ['—']
    emp_colors = _DEFAULT_EMP_COLORS[:len(X_emp_list)] or ['red']
    n = problem_obj.n_var
    common = dict(true_color=cfg['true_color'],
                  emp_colors=emp_colors,
                  emp_names=emp_names)
    if n == 2:
        return _decision_heatmap_2d(problem_obj, X_landscape, F_landscape,
                                    X_true, X_emp_list, None, **common)
    if n == 3:
        return _decision_scatter_3d(problem_obj, X_landscape, F_landscape,
                                    X_true, X_emp_list, None,
                                    elev_offset=cfg['elev'],
                                    azim_offset=cfg['azim'],
                                    roll_offset=cfg['roll'], **common)
    # n_var > 3 — escolhe PCA preferencial
    if show_3d_pca:
        return _decision_pca_by_obj_3d(X_landscape, F_landscape, X_true, X_emp_list,
                                       None, elev_offset=cfg['elev'],
                                       azim_offset=cfg['azim'],
                                       roll_offset=cfg['roll'], **common)
    if show_2d_pca:
        return _decision_pca_by_obj_2d(X_landscape, F_landscape, X_true, X_emp_list,
                                       None, **common)
    return None


def render_pairplot(problem_obj, X_landscape, algo_X, cfg):
    """Esquerda inferior: pairwise grid (apenas n_var > 3)."""
    if X_landscape is None:
        return None
    if problem_obj.n_var <= 3 or cfg.get('pair_vars') is None:
        return None
    X_true, _ = problem_obj.true_pareto_front()
    X_emp_list = list(algo_X.values())
    emp_names = list(algo_X.keys())
    emp_colors = _DEFAULT_EMP_COLORS[:len(X_emp_list)] or ['red']
    return _decision_pairwise(problem_obj, X_landscape, X_true, X_emp_list,
                              title=None, pair_vars=cfg['pair_vars'],
                              true_color=cfg['true_color'],
                              emp_colors=emp_colors, emp_names=emp_names)


def render_gif(problem_name: str, algo: str, seed: int, problem_obj,
               force_regen: bool, cfg):
    """Direita inferior: GIF (apenas n_obj == 2)."""
    if problem_obj.n_obj != 2:
        return None, 'GIF disponível apenas para problemas bi-objetivo.'
    safe_algo = algo.replace('/', '_').replace(' ', '_').replace('-', '_').lower()
    cache_path = GIF_CACHE_DIR / f'{safe_algo}_{problem_name}_seed{seed}.gif'
    if not force_regen and cache_path.exists():
        return str(cache_path), None
    if not force_regen:
        return None, "Sem GIF em cache. Clique '🔄 Atualizar GIF' na sidebar."
    df_all = load_all_parquet()
    sub = df_all[(df_all['problem'] == problem_name) &
                 (df_all['algorithm'] == algo) &
                 (df_all['seed'] == seed)]
    if sub.empty:
        return None, f"Sem dados em all.parquet para ({algo}, {problem_name}, seed={seed})."
    _, F_landscape = load_landscape(problem_name)
    if F_landscape is None:
        return None, f"Landscape não encontrada em data/dataframes/{problem_name}/"
    gerar_gif_pareto_evolucao(problem_obj, F_landscape, sub, str(cache_path),
                              fps=4, xlim=cfg['xlim'], ylim=cfg['ylim'],
                              true_color=cfg['true_color'],
                              emp_color=cfg['emp_color'])
    return str(cache_path), None


# ═══════════════════════════════════════════════════════════════════════════
#  Explicações das métricas (markdown verbatim do notebook 2)
# ═══════════════════════════════════════════════════════════════════════════

METRIC_EXPLANATIONS_MD = r"""
## Métricas de Avaliação

As 4 métricas abaixo foram selecionadas com base na frequência de uso nos
artigos dos algoritmos implementados e na cobertura de diferentes aspectos
da qualidade das soluções (convergência e diversidade).

### 1. Hypervolume (HV) — Convergência + Diversidade | ↑ Maior = melhor
**Aparece em:** K-RVEA, DR-NSGA-II, ParEGO, Prob-MOEA/D (4 artigos)

Volume do espaço de objetivos **dominado** pelo conjunto de soluções A,
limitado por um ponto de referência r (pior que todos os pontos). Um conjunto
com melhor convergência E melhor espalhamento terá maior HV.

**Cálculo:** Para cada par de pontos consecutivos (ordenados por f₁),
calcula-se a área/volume do retângulo/hipercubo dominado.
HV = soma dessas áreas.

**Exemplo 2D:** A = {(0.2, 0.8), (0.5, 0.3), (0.9, 0.1)}, r = (1.1, 1.1)
- Retângulo 1: (1.1−0.2) × (1.1−0.8) = 0.27
- Retângulo 2: (1.1−0.5) × (0.8−0.3) = 0.30
- Retângulo 3: (1.1−0.9) × (0.3−0.1) = 0.04
- **HV = 0.61**

### 2. IGD (Inverted Generational Distance) — Convergência + Diversidade | ↓ Menor = melhor
**Aparece em:** K-RVEA, KTA2 (2 artigos)

Para cada ponto `p` do PF verdadeiro P*, encontra a distância ao ponto mais
próximo no conjunto A.

**Cálculo:** IGD = (1/|P*|) × Σ_{p ∈ P*} min_{a ∈ A} ‖p − a‖

**Exemplo:** P* = {(0,1), (0.5,0.5), (1,0)}, A = {(0.1,0.9), (0.6,0.4)}
- d(p₁) = min(0.141, 0.781) = 0.141
- d(p₂) = min(0.566, 0.141) = 0.141
- d(p₃) = min(1.273, 0.566) = 0.566
- **IGD = 0.283**

Se A não cobre uma região do PF verdadeiro, os pontos nessa região terão
distâncias altas → IGD sobe.

### 3. Gamma (Γ) — Convergência pura | ↓ Menor = melhor
**Aparece em:** NSGA-II (Deb et al., 2002, Sec. IV-B)

Inverso do IGD: para cada ponto `a` do conjunto encontrado A, distância ao
PF verdadeiro mais próximo.

**Cálculo:** Γ = (1/|A|) × Σ_{a ∈ A} min_{p ∈ P*} ‖a − p‖

Se todas as soluções estão exatamente no PF, Γ = 0.

### 4. Delta (Δ) — Diversidade / Uniformidade | ↓ Menor = melhor
**Aparece em:** NSGA-II (Deb et al., 2002, Sec. IV-B)

Mede a uniformidade da distribuição de soluções ao longo do front.

**Cálculo:** Δ = (d_f + d_l + Σ|d_i − d̄|) / (d_f + d_l + (N−1)×d̄)

Onde:
- d_i = distância entre soluções consecutivas (ordenadas por f₁)
- d̄ = média das d_i
- d_f = distância do extremo do PF verdadeiro ao primeiro ponto de A
- d_l = distância do extremo do PF verdadeiro ao último ponto de A

Se todas as d_i = d̄ (perfeitamente uniforme) e d_f = d_l = 0 (cobre os
extremos): **Δ = 0**.

### Multicritério
Média ponderada das 4 métricas, após normalização min-max **por problema**
(sobre os algoritmos), invertendo as métricas que são "quanto menor melhor"
de modo que 1 = melhor. Pesos editáveis no menu lateral.
"""


# ═══════════════════════════════════════════════════════════════════════════
#  Layout
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(page_title='SAEA Dashboard', layout='wide')

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header('Pesos do Multicritério')
    w_hv    = st.number_input('peso Hypervolume', 0.0, 10.0, 1.0, 0.5)
    w_igd   = st.number_input('peso IGD',         0.0, 10.0, 1.0, 0.5)
    w_gamma = st.number_input('peso Gamma',       0.0, 10.0, 1.0, 0.5)
    w_delta = st.number_input('peso Delta',       0.0, 10.0, 1.0, 0.5)

    st.divider()
    st.header('Visualizações por problema')
    problem_name = st.selectbox('Problema', PROBLEMS, index=0,
                                key='problem_selector')

    cfg_default = PLOT_CONFIG[problem_name]
    problem_obj = get_problem(problem_name)
    n_obj = problem_obj.n_obj
    n_var = problem_obj.n_var

    selected_algos = st.multiselect('Algoritmos (fronts exibidos)',
                                    ALGORITHMS, default=ALGORITHMS,
                                    key=f'algos_{problem_name}')

    st.divider()
    st.subheader('Configurações do GIF')
    gif_algo = st.selectbox('Algoritmo do GIF', ALGORITHMS,
                            key=f'gif_algo_{problem_name}')
    df_all = load_all_parquet()
    available_seeds = sorted(df_all['seed'].unique())
    gif_seed = st.selectbox('Seed do GIF', available_seeds,
                            key=f'gif_seed_{problem_name}')
    btn_refresh_gif = st.button('🔄 Atualizar GIF')

    st.divider()
    st.subheader('Limites dos eixos')
    xdef = cfg_default['xlim'] or (0.0, 1.0)
    ydef = cfg_default['ylim'] or (0.0, 1.0)
    zdef = cfg_default['zlim'] or (0.0, 1.0)
    xlim_lo = st.number_input('x_lim min', value=float(xdef[0]),
                              key=f'xlo_{problem_name}', format='%g')
    xlim_hi = st.number_input('x_lim max', value=float(xdef[1]),
                              key=f'xhi_{problem_name}', format='%g')
    ylim_lo = st.number_input('y_lim min', value=float(ydef[0]),
                              key=f'ylo_{problem_name}', format='%g')
    ylim_hi = st.number_input('y_lim max', value=float(ydef[1]),
                              key=f'yhi_{problem_name}', format='%g')
    use_xlim = st.checkbox('Aplicar x_lim',
                           value=cfg_default['xlim'] is not None,
                           key=f'usex_{problem_name}')
    use_ylim = st.checkbox('Aplicar y_lim',
                           value=cfg_default['ylim'] is not None,
                           key=f'usey_{problem_name}')
    if n_obj == 3:
        zlim_lo = st.number_input('z_lim min', value=float(zdef[0]),
                                  key=f'zlo_{problem_name}', format='%g')
        zlim_hi = st.number_input('z_lim max', value=float(zdef[1]),
                                  key=f'zhi_{problem_name}', format='%g')
        use_zlim = st.checkbox('Aplicar z_lim',
                               value=cfg_default['zlim'] is not None,
                               key=f'usez_{problem_name}')
    else:
        zlim_lo, zlim_hi, use_zlim = 0.0, 1.0, False

    st.divider()
    st.subheader('Rotação 3D (gráficos 3D apenas)')
    elev = st.slider('elev_offset', -180, 180, int(cfg_default['elev']),
                     key=f'el_{problem_name}')
    azim = st.slider('azim_offset', -180, 360, int(cfg_default['azim']),
                     key=f'az_{problem_name}')
    roll = st.slider('roll_offset', -180, 180, int(cfg_default['roll']),
                     key=f'rl_{problem_name}')

    st.divider()
    st.subheader('Tamanho das figuras (px)')
    img_width  = st.number_input('largura', 200, 2000, 600, 50,
                                 key=f'imgw_{problem_name}')
    img_height = st.number_input('altura',  200, 2000, 600, 50,
                                 key=f'imgh_{problem_name}')

    st.divider()
    st.subheader('PCA (problemas com n_var > 3)')
    show_2d_pca_default = problem_name not in OUT_2D_PCA
    show_3d_pca_default = problem_name in PLOT_3D_PCA
    show_2d_pca = st.checkbox('Mostrar PCA 2D',
                              value=show_2d_pca_default,
                              key=f'pca2_{problem_name}')
    show_3d_pca = st.checkbox('Mostrar PCA 3D',
                              value=show_3d_pca_default,
                              key=f'pca3_{problem_name}')

    st.caption(f'Problema: **n_var = {n_var}**, **n_obj = {n_obj}**')

# ── Header ─────────────────────────────────────────────────────────────────
st.title('SAEA Dashboard — análise comparativa de algoritmos')

weights = {'HV': w_hv, 'IGD': w_igd, 'Gamma': w_gamma, 'Delta': w_delta}

# ── Tabela e gráfico ───────────────────────────────────────────────────────
try:
    parquet_mtime = ALL_PARQUET.stat().st_mtime
    metric_table = build_metric_table(parquet_mtime)
except Exception as e:
    st.error(f'Falha ao carregar/processar {ALL_PARQUET}: {e}')
    st.stop()

metric_table = apply_multicriterion(metric_table, weights)

# 1) Tabela
st.subheader('1) Tabela de métricas (média entre seeds)')
metric_choice = st.selectbox('Métrica',
                             list(METRIC_LABELS.keys()),
                             index=4,  # Multicritério como default
                             key='metric_selector')
metric_key = METRIC_LABELS[metric_choice]
st.dataframe(render_metric_table(metric_table, metric_key),
             use_container_width=True, height=900)

# 2) Gráfico de vitórias
st.subheader('2) Quantidade de 1º lugares por algoritmo')
algo_order = compute_algo_order(metric_table)
st.plotly_chart(build_wins_chart(metric_table, algo_order),
                use_container_width=True)

# 3) Quadrante 2x2 de visualizações
st.subheader(f'3) Análise visual — {problem_name}')

cfg = dict(PLOT_CONFIG[problem_name])  # cópia
cfg['xlim'] = (xlim_lo, xlim_hi) if use_xlim else None
cfg['ylim'] = (ylim_lo, ylim_hi) if use_ylim else None
cfg['zlim'] = (zlim_lo, zlim_hi) if (n_obj == 3 and use_zlim) else None
cfg['elev'] = elev
cfg['azim'] = azim
cfg['roll'] = roll

X_landscape, F_landscape = load_landscape(problem_name)
algo_fronts, algo_X_dict = build_algo_arrays(df_all, problem_name, selected_algos)

col1, col2 = st.columns(2)
with col1:
    st.markdown('**Pareto fronts encontrados** (espaço de objetivos)')
    try:
        fig1 = render_pareto_fronts(problem_obj, F_landscape, algo_fronts, cfg)
        if fig1 is not None:
            st.image(fig_to_png_bytes(fig1, img_width, img_height), width=img_width)
        else:
            st.info('Sem dados de landscape para este problema.')
    except Exception as e:
        st.error(f'Erro ao renderizar Pareto fronts: {e}')

with col2:
    st.markdown('**Decision space** (heatmap / 3D / PCA conforme n_var)')
    try:
        fig2 = render_decision_space(problem_obj, X_landscape, F_landscape,
                                     algo_X_dict, cfg,
                                     show_2d_pca, show_3d_pca)
        if fig2 is not None:
            st.image(fig_to_png_bytes(fig2, img_width, img_height), width=img_width)
        else:
            st.info('Decision space indisponível para este problema/configuração.')
    except Exception as e:
        st.error(f'Erro ao renderizar Decision space: {e}')

col3, col4 = st.columns(2)
with col3:
    st.markdown('**Pairplot** (variáveis selecionadas — apenas n_var > 3)')
    try:
        fig3 = render_pairplot(problem_obj, X_landscape, algo_X_dict, cfg)
        if fig3 is not None:
            st.image(fig_to_png_bytes(fig3, img_width, img_height), width=img_width)
        else:
            st.info('Pairplot não aplicável (n_var ≤ 3 ou pair_vars vazio).')
    except Exception as e:
        st.error(f'Erro ao renderizar Pairplot: {e}')

with col4:
    st.markdown(f'**Evolução do front — {gif_algo}, seed {gif_seed}**')
    gif_path, gif_msg = render_gif(problem_name, gif_algo, gif_seed,
                                   problem_obj, btn_refresh_gif, cfg)
    if gif_path:
        st.image(gif_path, width=img_width)
    elif gif_msg:
        st.info(gif_msg)

# 4) Explicações das métricas
st.markdown('---')
st.markdown(METRIC_EXPLANATIONS_MD)
