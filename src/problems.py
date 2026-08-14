"""
Benchmark problem catalog for multi-objective optimization.

Suites implemented:
  - MMF  (CEC 2020 Multimodal Multi-objective)
  - ZDT  (Zitzler-Deb-Thiele, 2000)
  - DTLZ (Deb-Thiele-Laumanns-Zitzler, 2001)
  - WFG  (Walking Fish Group, Huband et al. 2006)
  - BBOB Gallagher Mock

Each class inherits from pymoo.core.problem.Problem.
"""

import os

import numpy as np
from pymoo.core.problem import Problem
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting


_NDS = NonDominatedSorting(method="efficient_non_dominated_sort")


def _nds_filter(F):
    """Return indices of the non-dominated front.

    Uses Efficient Non-dominated Sort (ENS, Roy et al. 2016) with early stop
    at the first front: O(N * log^(M-1) N) time and no NxN matrix allocation,
    which makes it viable for N >> 10^5.
    """
    return _NDS.do(F, only_non_dominated_front=True)


def _make_bounds(bounds):
    """Convert a per-variable bounds list into (xl, xu) arrays.

    Args:
        bounds: array-like of shape (n_var, 2), where each row is [lower, upper].
    Returns:
        xl, xu: 1-D numpy arrays of length n_var.
    """
    b = np.asarray(bounds, dtype=float)
    return b[:, 0].copy(), b[:, 1].copy()


# ═══════════════════════════════════════════════════════════════════════════
#  MMF – Multimodal Multi-objective Functions  (CEC 2020)
# ═══════════════════════════════════════════════════════════════════════════

class MMF1(Problem):
    """
    MMF1 - CEC 2020.

    Two global Pareto sets mirrored about x1 = 2.
    f1 = |x1 - 2|
    f2 = 1 - sqrt(f1) + 2*(x2 - sin(6π|x1-2| + π))²
    Search space: x1 ∈ [1,3], x2 ∈ [-1,1].
    """
    def __init__(self):
        bounds = [
            [1.0, 3.0],    # x1
            [-1.0, 1.0],   # x2
        ]
        xl, xu = _make_bounds(bounds)
        super().__init__(n_var=2, n_obj=2, xl=xl, xu=xu)

    def _evaluate(self, X, out, *args, **kwargs):
        x1, x2 = X[:, 0], X[:, 1]
        f1 = np.abs(x1 - 2.0)
        f2 = 1.0 - np.sqrt(f1) + 2.0 * (x2 - np.sin(6.0 * np.pi * np.abs(x1 - 2.0) + np.pi)) ** 2
        out["F"] = np.column_stack([f1, f2])

    def true_pareto_front(self, n=500):
        """Liang et al. (CEC 2020): PS: x2 = sin(6π|x1−2|+π), x1∈[1,3]; PF: f2 = 1−√f1."""
        x1 = np.linspace(1.0, 3.0, 2 * n)
        x2 = np.sin(6.0 * np.pi * np.abs(x1 - 2.0) + np.pi)
        X = np.column_stack([x1, x2])
        return X, evaluate_problem(self, X)


class MMF4(Problem):
    """
    MMF4 - CEC 2020.

    Four global Pareto sets (piecewise formulation).
    f1 = |x1|
    f2 (x2 < 1) = 1 - x1² + 2*(x2 - sin(π|x1|))²
    f2 (x2 ≥ 1) = 1 - x1² + 2*(x2 - 1 - sin(π|x1|))²
    Search space: x1 ∈ [-1,1], x2 ∈ [0,2].
    """
    def __init__(self):
        bounds = [
            [-1.0, 1.0],   # x1
            [0.0, 2.0],    # x2
        ]
        xl, xu = _make_bounds(bounds)
        super().__init__(n_var=2, n_obj=2, xl=xl, xu=xu)

    def _evaluate(self, X, out, *args, **kwargs):
        x1, x2 = X[:, 0], X[:, 1]
        f1 = np.abs(x1)
        f2 = np.where(
            x2 < 1.0,
            1.0 - x1 ** 2 + 2.0 * (x2 - np.sin(np.pi * np.abs(x1))) ** 2,
            1.0 - x1 ** 2 + 2.0 * (x2 - 1.0 - np.sin(np.pi * np.abs(x1))) ** 2,
        )
        out["F"] = np.column_stack([f1, f2])

    def true_pareto_front(self, n=500):
        """Liang et al. (CEC 2020): PS1: x2=sin(π|x1|); PS2: x2=1+sin(π|x1|); PF: f2=1−f1²."""
        x1 = np.linspace(-1.0, 1.0, n)
        x2_lo = np.sin(np.pi * np.abs(x1))
        x2_hi = 1.0 + np.sin(np.pi * np.abs(x1))
        X = np.column_stack([np.tile(x1, 2), np.concatenate([x2_lo, x2_hi])])
        return X, evaluate_problem(self, X)


class MMF11_L(Problem):
    """
    MMF11_l – CEC 2020.

    1 global PS + 1 local PS  (n_p = 2).
    f1 = x1
    f2 = g(x2) / x1
    g(x) = 2 - exp(-2·ln2·((x-0.1)/0.8)²) · sin⁶(n_p·π·x)
    Search space: x1, x2 ∈ [0.1, 1.1].
    """
    def __init__(self, n_p=2):
        bounds = [
            [0.1, 1.1],    # x1
            [0.1, 1.1],    # x2
        ]
        xl, xu = _make_bounds(bounds)
        super().__init__(n_var=2, n_obj=2, xl=xl, xu=xu)
        self.n_p = n_p

    def _evaluate(self, X, out, *args, **kwargs):
        x1, x2 = X[:, 0], X[:, 1]
        f1 = x1
        g = (2.0
             - np.exp(-2.0 * np.log(2.0) * ((x2 - 0.1) / 0.8) ** 2)
             * np.sin(self.n_p * np.pi * x2) ** 6)
        f2 = g / x1
        out["F"] = np.column_stack([f1, f2])

    def true_pareto_front(self, n=500):
        """Liang et al. (CEC 2020): Global PS: x2 = 1/(2·n_p), x1∈[0.1,1.1]."""
        x1 = np.linspace(0.1, 1.1, n)
        x2 = np.full(n, 1.0 / (2.0 * self.n_p))
        X = np.column_stack([x1, x2])
        return X, evaluate_problem(self, X)


class MMF16_L3(Problem):
    """
    MMF16_l3 – CEC 2020 (3-objective variant).

    Extension of MMF16 (Liang et al., CEC 2020) to m = 3 objectives, n = 3
    variables, n_pg = 2 global PS, n_pl = 2 local PS.  k = n − (m−1) = 1
    distance variable (x3).

    Objectives (general MMF16 structure, §1.3 of the report):
        f1 = cos(π·x1/2) · cos(π·x2/2) · (1 + g)
        f2 = cos(π·x1/2) · sin(π·x2/2) · (1 + g)
        f3 = sin(π·x1/2)               · (1 + g)

    Piecewise g on the last variable xn (here x3):
        Global region  (x3 ∈ [0, 0.5)):
            g = 2 − sin⁶(2·n_pg·π·x3)
        Local region   (x3 ∈ [0.5, 1]):
            g = 2 − exp(−2·ln2·((x3−0.1)/0.8)²) · sin⁶(2·n_pl·π·x3)
    """
    def __init__(self, n_pg=2, n_pl=2):
        bounds = [
            [0.0, 1.0],    # x1 – position
            [0.0, 1.0],    # x2 – position
            [0.0, 1.0],    # x3 – distance (piecewise g)
        ]
        xl, xu = _make_bounds(bounds)
        super().__init__(n_var=3, n_obj=3, xl=xl, xu=xu)
        self.n_pg = n_pg
        self.n_pl = n_pl

    def _evaluate(self, X, out, *args, **kwargs):
        x1 = X[:, 0]
        x2 = X[:, 1]
        x3 = X[:, 2]

        g = np.where(
            x3 < 0.5,
            2.0 - np.sin(2.0 * self.n_pg * np.pi * x3) ** 2,
            2.0 - np.exp(-2.0 * np.log(2.0) * ((x3 - 0.1) / 0.8) ** 2)
                * np.sin(2.0 * self.n_pl * np.pi * x3) ** 2,
        )

        f1 = np.cos(np.pi * x1 / 2.0) * np.cos(np.pi * x2 / 2.0) * (1.0 + g)
        f2 = np.cos(np.pi * x1 / 2.0) * np.sin(np.pi * x2 / 2.0) * (1.0 + g)
        f3 = np.sin(np.pi * x1 / 2.0) * (1.0 + g)
        out["F"] = np.column_stack([f1, f2, f3])

    def true_pareto_front(self, n=100):
        """Analytical sphere PF with radius (1+g_min).
        g_min found numerically in [0, 0.5); X uses x3 at the optimum."""
        xn_grid = np.linspace(0, 0.4999, 10_000)
        g_glob = 2.0 - np.sin(2.0 * self.n_pg * np.pi * xn_grid) ** 2
        i_min = np.argmin(g_glob)
        g_min, xn_opt = g_glob[i_min], xn_grid[i_min]
        R = 1.0 + g_min

        t = np.linspace(0, 1, n)
        U, V = np.meshgrid(t, t)
        u, v = U.ravel(), V.ravel()
        f1 = R * np.cos(u * np.pi / 2) * np.cos(v * np.pi / 2)
        f2 = R * np.cos(u * np.pi / 2) * np.sin(v * np.pi / 2)
        f3 = R * np.sin(u * np.pi / 2)

        X = np.column_stack([u, v, np.full(len(u), xn_opt)])
        F = np.column_stack([f1, f2, f3])
        return X, F


class MMF16_20(Problem):
    """
    MMF16 – CEC 2020 (3-objective, 20-variable variant).

    Extension of MMF16 (Liang et al., CEC 2020) to m = 3 objectives, n = 20
    variables, n_pg = 2 global PS, n_pl = 2 local PS.  k = n − (m−1) = 18
    distance variables (x3..x20); only xn participates in g.

    Objectives (general MMF16 structure, §1.3 of the report):
        f1 = cos(π·x1/2) · cos(π·x2/2) · (1 + g)
        f2 = cos(π·x1/2) · sin(π·x2/2) · (1 + g)
        f3 = sin(π·x1/2)               · (1 + g)

    Piecewise g on the last variable xn (here x20):
        Global region  (x20 ∈ [0, 0.5)):
            g = 2 − sin²(2·n_pg·π·x20)
        Local region   (x20 ∈ [0.5, 1]):
            g = 2 − exp(−2·ln2·((x20−0.1)/0.8)²) · sin²(2·n_pl·π·x20)
    """
    def __init__(self, n_pg=2, n_pl=2):
        n_var = 20
        bounds = [[0.0, 1.0]] * n_var
        xl, xu = _make_bounds(bounds)
        super().__init__(n_var=n_var, n_obj=3, xl=xl, xu=xu)
        self.n_pg = n_pg
        self.n_pl = n_pl

    def _evaluate(self, X, out, *args, **kwargs):
        x1 = X[:, 0]
        x2 = X[:, 1]
        xn = X[:, -1]

        g = np.where(
            xn < 0.5,
            2.0 - np.sin(2.0 * self.n_pg * np.pi * xn) ** 2,
            2.0 - np.exp(-2.0 * np.log(2.0) * ((xn - 0.1) / 0.8) ** 2)
                * np.sin(2.0 * self.n_pl * np.pi * xn) ** 2,
        )

        f1 = np.cos(np.pi * x1 / 2.0) * np.cos(np.pi * x2 / 2.0) * (1.0 + g)
        f2 = np.cos(np.pi * x1 / 2.0) * np.sin(np.pi * x2 / 2.0) * (1.0 + g)
        f3 = np.sin(np.pi * x1 / 2.0) * (1.0 + g)
        out["F"] = np.column_stack([f1, f2, f3])

    def true_pareto_front(self, n=100):
        """Analytical sphere PF. g uses sin²; g_min found numerically."""
        xn_grid = np.linspace(0, 0.4999, 10_000)
        g_glob = 2.0 - np.sin(2.0 * self.n_pg * np.pi * xn_grid) ** 2
        i_min = np.argmin(g_glob)
        g_min, xn_opt = g_glob[i_min], xn_grid[i_min]
        R = 1.0 + g_min

        t = np.linspace(0, 1, n)
        U, V = np.meshgrid(t, t)
        u, v = U.ravel(), V.ravel()
        m = len(u)
        f1 = R * np.cos(u * np.pi / 2) * np.cos(v * np.pi / 2)
        f2 = R * np.cos(u * np.pi / 2) * np.sin(v * np.pi / 2)
        f3 = R * np.sin(u * np.pi / 2)

        X = np.column_stack([u, v, np.full((m, self.n_var - 3), 0.5),
                             np.full(m, xn_opt).reshape(-1, 1)])
        F = np.column_stack([f1, f2, f3])
        return X, F


# ═══════════════════════════════════════════════════════════════════════════
#  ZDT – Zitzler, Deb, Thiele (2000)
# ═══════════════════════════════════════════════════════════════════════════

class ZDT1(Problem):
    """
    ZDT1 – convex Pareto front.

    f1 = x1
    g  = 1 + 9/(n-1) · Σ x_i  (i=2..n)
    f2 = g · (1 - √(f1/g))
    x_i ∈ [0, 1], default n = 30.
    """
    def __init__(self, n_var=30):
        bounds = [[0.0, 1.0]] * n_var          # x1..xn ∈ [0, 1]
        xl, xu = _make_bounds(bounds)
        super().__init__(n_var=n_var, n_obj=2, xl=xl, xu=xu)

    def _evaluate(self, X, out, *args, **kwargs):
        f1 = X[:, 0]
        g = 1.0 + 9.0 * np.sum(X[:, 1:], axis=1) / (self.n_var - 1)
        f2 = g * (1.0 - np.sqrt(f1 / g))
        out["F"] = np.column_stack([f1, f2])

    def true_pareto_front(self, n=500):
        """ZDT (2000): PS: x1∈[0,1], x2=…=xn=0; PF: f2 = 1−√f1."""
        x1 = np.linspace(0.0, 1.0, n)
        X = np.column_stack([x1, np.zeros((n, self.n_var - 1))])
        return X, evaluate_problem(self, X)


class ZDT3(Problem):
    """
    ZDT3 – disconnected Pareto front.

    f1 = x1
    g  = 1 + 9/(n-1) · Σ x_i
    f2 = g · (1 - √(f1/g) - (f1/g)·sin(10π·f1))
    x_i ∈ [0, 1], default n = 30.
    """
    def __init__(self, n_var=30):
        bounds = [[0.0, 1.0]] * n_var          # x1..xn ∈ [0, 1]
        xl, xu = _make_bounds(bounds)
        super().__init__(n_var=n_var, n_obj=2, xl=xl, xu=xu)

    def _evaluate(self, X, out, *args, **kwargs):
        f1 = X[:, 0]
        g = 1.0 + 9.0 * np.sum(X[:, 1:], axis=1) / (self.n_var - 1)
        f2 = g * (1.0 - np.sqrt(f1 / g) - (f1 / g) * np.sin(10.0 * np.pi * f1))
        out["F"] = np.column_stack([f1, f2])

    def true_pareto_front(self, n=5000):
        """ZDT (2000): PS same as ZDT1; PF has 5 disconnected segments (NDS-filtered)."""
        x1 = np.linspace(0.0, 1.0, n)
        X = np.column_stack([x1, np.zeros((n, self.n_var - 1))])
        F = evaluate_problem(self, X)
        idx = _nds_filter(F)
        return X[idx], F[idx]


class ZDT4(Problem):
    """
    ZDT4 – multimodal g (many local fronts).

    f1 = x1
    g  = 1 + 10(n-1) + Σ (x_i² - 10·cos(4π·x_i))  (i=2..n)
    f2 = g · (1 - √(f1/g))
    x1 ∈ [0, 1], x_i ∈ [-5, 5] for i ≥ 2, default n = 10.
    """
    def __init__(self, n_var=10):
        bounds = [
            [0.0, 1.0],                        # x1 ∈ [0, 1]
            *[[-5.0, 5.0]] * (n_var - 1),      # x2..xn ∈ [-5, 5]
        ]
        xl, xu = _make_bounds(bounds)
        super().__init__(n_var=n_var, n_obj=2, xl=xl, xu=xu)

    def _evaluate(self, X, out, *args, **kwargs):
        f1 = X[:, 0]
        xi = X[:, 1:]
        g = 1.0 + 10.0 * (self.n_var - 1) + np.sum(xi ** 2 - 10.0 * np.cos(4.0 * np.pi * xi), axis=1)
        f2 = g * (1.0 - np.sqrt(f1 / g))
        out["F"] = np.column_stack([f1, f2])

    def true_pareto_front(self, n=500):
        """ZDT (2000): PS: x1∈[0,1], x2=…=xn=0; PF: f2 = 1−√f1 (same as ZDT1)."""
        x1 = np.linspace(0.0, 1.0, n)
        X = np.column_stack([x1, np.zeros((n, self.n_var - 1))])
        return X, evaluate_problem(self, X)


class ZDT6(Problem):
    """
    ZDT6 – nonconvex, non-uniform density.

    f1 = 1 - exp(-4x1)·sin⁶(6πx1)
    g  = 1 + 9·(Σ x_i / (n-1))^0.25  (i=2..n)
    f2 = g · (1 - (f1/g)²)
    x_i ∈ [0, 1], default n = 10.
    """
    def __init__(self, n_var=10):
        bounds = [[0.0, 1.0]] * n_var          # x1..xn ∈ [0, 1]
        xl, xu = _make_bounds(bounds)
        super().__init__(n_var=n_var, n_obj=2, xl=xl, xu=xu)

    def _evaluate(self, X, out, *args, **kwargs):
        x1 = X[:, 0]
        f1 = 1.0 - np.exp(-4.0 * x1) * np.sin(6.0 * np.pi * x1) ** 6
        g = 1.0 + 9.0 * (np.sum(X[:, 1:], axis=1) / (self.n_var - 1)) ** 0.25
        f2 = g * (1.0 - (f1 / g) ** 2)
        out["F"] = np.column_stack([f1, f2])

    def true_pareto_front(self, n=500):
        """ZDT (2000): PS: x1∈[0,1], x2=…=xn=0; PF: f2 = 1−f1² (non-uniform f1)."""
        x1 = np.linspace(0.0, 1.0, n)
        X = np.column_stack([x1, np.zeros((n, self.n_var - 1))])
        return X, evaluate_problem(self, X)


# ═══════════════════════════════════════════════════════════════════════════
#  DTLZ – Deb, Thiele, Laumanns, Zitzler (2001)
# ═══════════════════════════════════════════════════════════════════════════

class DTLZ1(Problem):
    """
    DTLZ1 – linear PF, highly multimodal g  (Deb et al. 2001, eq. 20–21).

    f1 = 0.5 · x1 · x2 · (1 + g)
    f2 = 0.5 · x1 · (1 − x2) · (1 + g)
    f3 = 0.5 · (1 − x1) · (1 + g)
    g  = 100 · [k + Σ((x_i − 0.5)² − cos(20π(x_i − 0.5)))]  over x3..xn
    x_i ∈ [0, 1], default k = 5, n = 7.
    """
    def __init__(self, k=5):
        n_var = 2 + k                          # M-1 + k = 2 + k
        bounds = [[0.0, 1.0]] * n_var
        xl, xu = _make_bounds(bounds)
        super().__init__(n_var=n_var, n_obj=3, xl=xl, xu=xu)
        self.k = k

    def _evaluate(self, X, out, *args, **kwargs):
        x1 = X[:, 0]
        x2 = X[:, 1]
        xm = X[:, 2:]
        g = 100.0 * (self.k + np.sum((xm - 0.5) ** 2 - np.cos(20.0 * np.pi * (xm - 0.5)), axis=1))

        f1 = 0.5 * x1 * x2 * (1.0 + g)
        f2 = 0.5 * x1 * (1.0 - x2) * (1.0 + g)
        f3 = 0.5 * (1.0 - x1) * (1.0 + g)
        out["F"] = np.column_stack([f1, f2, f3])

    def true_pareto_front(self, n=100):
        """Analytical: f1=0.5·u·v, f2=0.5·u·(1−v), f3=0.5·(1−u). PS: xm=0.5."""
        t = np.linspace(0, 1, n)
        U, V = np.meshgrid(t, t)
        u, v = U.ravel(), V.ravel()
        F = np.column_stack([0.5 * u * v,
                             0.5 * u * (1.0 - v),
                             0.5 * (1.0 - u)])
        X = np.column_stack([u, v, np.full((len(u), self.k), 0.5)])
        return X, F


class DTLZ2(Problem):
    """
    DTLZ2 – spherical PF  (Deb et al. 2001, eq. 22).

    f1 = (1 + g) · cos(x1·π/2) · cos(x2·π/2)
    f2 = (1 + g) · cos(x1·π/2) · sin(x2·π/2)
    f3 = (1 + g) · sin(x1·π/2)
    g  = Σ (x_i − 0.5)²  over x3..xn
    x_i ∈ [0, 1], default k = 10, n = 12.
    """
    def __init__(self, k=10):
        n_var = 2 + k
        bounds = [[0.0, 1.0]] * n_var
        xl, xu = _make_bounds(bounds)
        super().__init__(n_var=n_var, n_obj=3, xl=xl, xu=xu)
        self.k = k

    def _evaluate(self, X, out, *args, **kwargs):
        x1 = X[:, 0]
        x2 = X[:, 1]
        xm = X[:, 2:]
        g = np.sum((xm - 0.5) ** 2, axis=1)

        f1 = (1.0 + g) * np.cos(x1 * np.pi / 2.0) * np.cos(x2 * np.pi / 2.0)
        f2 = (1.0 + g) * np.cos(x1 * np.pi / 2.0) * np.sin(x2 * np.pi / 2.0)
        f3 = (1.0 + g) * np.sin(x1 * np.pi / 2.0)
        out["F"] = np.column_stack([f1, f2, f3])

    def true_pareto_front(self, n=100):
        """Deb et al. (2001, §8.2): PS: x1,x2∈[0,1], xm=0.5; PF: f1²+f2²+f3²=1."""
        t1 = np.linspace(0, 1, n)
        T1, T2 = np.meshgrid(t1, t1)
        T1, T2 = T1.ravel(), T2.ravel()
        m = len(T1)
        X = np.column_stack([T1, T2, np.full((m, self.k), 0.5)])
        return X, evaluate_problem(self, X)


class DTLZ3(Problem):
    """
    DTLZ3 – spherical PF with DTLZ1's multimodal g  (Deb et al. 2001, eq. 23).

    f1 = (1 + g) · cos(x1·π/2) · cos(x2·π/2)
    f2 = (1 + g) · cos(x1·π/2) · sin(x2·π/2)
    f3 = (1 + g) · sin(x1·π/2)
    g  = 100 · [k + Σ((x_i − 0.5)² − cos(20π(x_i − 0.5)))]  over x3..xn
    x_i ∈ [0, 1], default k = 10, n = 12.
    """
    def __init__(self, k=10):
        n_var = 2 + k
        bounds = [[0.0, 1.0]] * n_var
        xl, xu = _make_bounds(bounds)
        super().__init__(n_var=n_var, n_obj=3, xl=xl, xu=xu)
        self.k = k

    def _evaluate(self, X, out, *args, **kwargs):
        x1 = X[:, 0]
        x2 = X[:, 1]
        xm = X[:, 2:]
        g = 100.0 * (self.k + np.sum((xm - 0.5) ** 2 - np.cos(20.0 * np.pi * (xm - 0.5)), axis=1))

        f1 = (1.0 + g) * np.cos(x1 * np.pi / 2.0) * np.cos(x2 * np.pi / 2.0)
        f2 = (1.0 + g) * np.cos(x1 * np.pi / 2.0) * np.sin(x2 * np.pi / 2.0)
        f3 = (1.0 + g) * np.sin(x1 * np.pi / 2.0)
        out["F"] = np.column_stack([f1, f2, f3])

    def true_pareto_front(self, n=100):
        """Analytical unit sphere (same shape as DTLZ2). PS: xm=0.5."""
        t = np.linspace(0, 1, n)
        U, V = np.meshgrid(t, t)
        u, v = U.ravel(), V.ravel()
        F = np.column_stack([np.cos(u * np.pi / 2) * np.cos(v * np.pi / 2),
                             np.cos(u * np.pi / 2) * np.sin(v * np.pi / 2),
                             np.sin(u * np.pi / 2)])
        X = np.column_stack([u, v, np.full((len(u), self.k), 0.5)])
        return X, F


class DTLZ4(Problem):
    """
    DTLZ4 – biased density on spherical PF  (Deb et al. 2001, eq. 24).

    f1 = (1 + g) · cos(x1^α·π/2) · cos(x2^α·π/2)
    f2 = (1 + g) · cos(x1^α·π/2) · sin(x2^α·π/2)
    f3 = (1 + g) · sin(x1^α·π/2)
    g  = Σ (x_i − 0.5)²  over x3..xn
    x_i ∈ [0, 1], default k = 10, α = 100, n = 12.
    """
    def __init__(self, k=10, alpha=100):
        n_var = 2 + k
        bounds = [[0.0, 1.0]] * n_var
        xl, xu = _make_bounds(bounds)
        super().__init__(n_var=n_var, n_obj=3, xl=xl, xu=xu)
        self.k = k
        self.alpha = alpha

    def _evaluate(self, X, out, *args, **kwargs):
        x1 = X[:, 0]
        x2 = X[:, 1]
        xm = X[:, 2:]
        a = self.alpha
        g = np.sum((xm - 0.5) ** 2, axis=1)

        f1 = (1.0 + g) * np.cos(x1 ** a * np.pi / 2.0) * np.cos(x2 ** a * np.pi / 2.0)
        f2 = (1.0 + g) * np.cos(x1 ** a * np.pi / 2.0) * np.sin(x2 ** a * np.pi / 2.0)
        f3 = (1.0 + g) * np.sin(x1 ** a * np.pi / 2.0)
        out["F"] = np.column_stack([f1, f2, f3])

    def true_pareto_front(self, n=100):
        """Analytical unit sphere (α only affects density, not shape). PS: xm=0.5."""
        t = np.linspace(0, 1, n)
        U, V = np.meshgrid(t, t)
        u, v = U.ravel(), V.ravel()
        F = np.column_stack([np.cos(u * np.pi / 2) * np.cos(v * np.pi / 2),
                             np.cos(u * np.pi / 2) * np.sin(v * np.pi / 2),
                             np.sin(u * np.pi / 2)])
        X = np.column_stack([u, v, np.full((len(u), self.k), 0.5)])
        return X, F


class DTLZ7(Problem):
    """
    DTLZ7 – disconnected PF regions, 2^{M-1} = 4 patches  (Deb et al. 2001, eq. 27).

    f1 = x1
    f2 = x2
    g  = 1 + (9/k) · Σ x_i  over x3..xn
    h  = 3 − [f1/(1+g) · (1 + sin(3π·f1))] − [f2/(1+g) · (1 + sin(3π·f2))]
    f3 = (1 + g) · h
    x_i ∈ [0, 1], default k = 20, n = 22.
    """
    def __init__(self, k=20):
        n_var = 2 + k
        bounds = [[0.0, 1.0]] * n_var
        xl, xu = _make_bounds(bounds)
        super().__init__(n_var=n_var, n_obj=3, xl=xl, xu=xu)
        self.k = k

    def _evaluate(self, X, out, *args, **kwargs):
        f1 = X[:, 0]
        f2 = X[:, 1]
        xm = X[:, 2:]
        g = 1.0 + (9.0 / self.k) * np.sum(xm, axis=1)

        h = (3.0
             - (f1 / (1.0 + g)) * (1.0 + np.sin(3.0 * np.pi * f1))
             - (f2 / (1.0 + g)) * (1.0 + np.sin(3.0 * np.pi * f2)))
        f3 = (1.0 + g) * h
        out["F"] = np.column_stack([f1, f2, f3])

    def true_pareto_front(self, n=200):
        """Deb et al. (2001, §8.7): PS: x1,x2∈[0,1], xm=0 (g=1). NDS for 4 patches."""
        t1 = np.linspace(0, 1, n)
        T1, T2 = np.meshgrid(t1, t1)
        T1, T2 = T1.ravel(), T2.ravel()
        m = len(T1)
        X = np.column_stack([T1, T2, np.zeros((m, self.k))])
        F = evaluate_problem(self, X)
        idx = _nds_filter(F)
        return X[idx], F[idx]


# ═══════════════════════════════════════════════════════════════════════════
#  WFG – Walking Fish Group  (Huband et al. 2006)
#
#  Variable bounds: x_i ∈ [0, 2i]  for i = 1 .. n
#  Normalisation:   z_i = x_i / (2i)
#
#  Default: M = 2, k = 2 (position params), l = 20 (distance params), n = 22
# ═══════════════════════════════════════════════════════════════════════════

# ── helper transformations ────────────────────────────────────────────────

def _correct_to_01(x):
    """Clamp values to [0, 1] and fix floating-point drift."""
    return np.clip(x, 0.0, 1.0)


def _s_linear(y, A=0.35):
    return _correct_to_01(np.abs(y - A) / np.maximum(np.abs(np.floor(A - y) + A), 1e-30))


def _s_multi(y, A, B, C):
    tmp1 = np.abs(y - C) / (2.0 * (np.floor(C - y) + C))
    tmp2 = (4.0 * A + 2.0) * np.pi * (0.5 - tmp1)
    return _correct_to_01((1.0 + np.cos(tmp2) + 4.0 * B * tmp1 ** 2) / (B + 2.0))


def _s_decept(y, A=0.35, B=0.001, C=0.05):
    tmp1 = np.floor(y - A + B) * (1.0 - C + (A - B) / B) / (A - B)
    tmp2 = np.floor(A + B - y) * (1.0 - C + (1.0 - A - B) / B) / (1.0 - A - B)
    return _correct_to_01(1.0 + (np.abs(y - A) - B) * (tmp1 + tmp2 + 1.0 / B))


def _b_poly(y, alpha):
    return _correct_to_01(y ** alpha)


def _b_flat(y, A, B, C):
    tmp1 = np.minimum(0.0, np.floor(y - B)) * A * (B - y) / B
    tmp2 = np.minimum(0.0, np.floor(C - y)) * (1.0 - A) * (y - C) / (1.0 - C)
    return _correct_to_01(A + tmp1 - tmp2)


def _b_param(y, u, A, B, C):
    v = A - (1.0 - 2.0 * u) * np.abs(np.floor(0.5 - u) + A)
    return _correct_to_01(y ** (B + (C - B) * v))


def _r_sum(y, w):
    """Weighted sum reduction.  y: (N, p),  w: (p,) → (N,)"""
    return np.dot(y, w) / np.sum(w)


def _r_nonsep(y, A):
    """Non-separable reduction.  y: (N, p), A: degree → (N,)"""
    p = y.shape[1]
    denom = p * np.ceil(A / 2.0) * (1.0 + 2.0 * A - 2.0 * np.ceil(A / 2.0)) / A
    accum = np.zeros(y.shape[0])
    for j in range(p):
        accum += y[:, j]
        for k_ in range(0, int(A - 1)):
            accum += np.abs(y[:, j] - y[:, (j + 1 + k_) % p])
    return accum / denom


# ── shape functions ───────────────────────────────────────────────────────

def _shape_convex(x, M):
    """Convex shape.  x: list of (N,) with M-1 entries → list of M (N,)."""
    h = []
    for m in range(M):
        val = np.ones(x[0].shape[0])
        for i in range(M - 1 - m):
            val *= 1.0 - np.cos(x[i] * np.pi / 2.0)
        if m > 0:
            val *= 1.0 - np.sin(x[M - 1 - m] * np.pi / 2.0)
        h.append(val)
    return h


def _shape_concave(x, M):
    """Concave shape (sphere-like)."""
    h = []
    for m in range(M):
        val = np.ones(x[0].shape[0])
        for i in range(M - 1 - m):
            val *= np.sin(x[i] * np.pi / 2.0)
        if m > 0:
            val *= np.cos(x[M - 1 - m] * np.pi / 2.0)
        h.append(val)
    return h


def _shape_mixed(x_last, A=5, alpha=1.0):
    """Mixed convex/concave – applied to one variable."""
    return _correct_to_01(
        (1.0 - x_last - np.cos(2.0 * A * np.pi * x_last + np.pi / 2.0) / (2.0 * A * np.pi))
    ) ** alpha


def _shape_disc(x_last, A=5, alpha=1.0, beta=1.0):
    """Disconnected shape."""
    return 1.0 - x_last ** alpha * np.cos(A * x_last ** beta * np.pi) ** 2


# ── WFG base ──────────────────────────────────────────────────────────────

class _WFGBase(Problem):
    """Common WFG infrastructure."""

    def __init__(self, n_obj=2, k=2, l=20):
        n_var = k + l
        bounds = [[0.0, 2.0 * i] for i in range(1, n_var + 1)]   # x_i ∈ [0, 2i]
        xl, xu = _make_bounds(bounds)
        super().__init__(n_var=n_var, n_obj=n_obj, xl=xl, xu=xu)
        self.k = k
        self.l = l
        self.S = 2.0 * np.arange(1, n_obj + 1, dtype=float)
        self.A = np.ones(n_obj - 1)

    def _normalise(self, X):
        """z_i = x_i / (2i)"""
        return X / (2.0 * np.arange(1, self.n_var + 1, dtype=float))

    def true_pareto_front(self, n=500):
        """Huband et al. (2006): PS: z_i=0.35 for distance params (i>k), position free.
        For M=2: one free position-parameter sweep covers the full PF."""
        z_pos = np.linspace(0.0, 1.0, n)
        X = np.empty((n, self.n_var))
        for i in range(self.n_var):
            if i < self.k:
                X[:, i] = z_pos * 2.0 * (i + 1)
            else:
                X[:, i] = 0.35 * 2.0 * (i + 1)
        return X, evaluate_problem(self, X)

    def _post(self, t_p, shape_h):
        """Compute objectives from last-transition vector t_p and shape h."""
        M = self.n_obj
        N = t_p.shape[0]
        x = []
        for i in range(M - 1):
            bound = np.maximum(t_p[:, M - 1], 1.0)
            x.append(_correct_to_01(bound * (t_p[:, i] - 0.5) + 0.5))
        x_m = t_p[:, M - 1]

        h = shape_h(x, M)

        F = np.empty((N, M))
        for m in range(M):
            F[:, m] = x_m + self.S[m] * h[m]
        return F


# ── WFG1 ──────────────────────────────────────────────────────────────────

class WFG1(_WFGBase):
    """
    WFG1 – separable, unimodal, biased (polynomial + flat).
    PF shape: convex + mixed.
    """

    def _evaluate(self, X, out, *args, **kwargs):
        M, k = self.n_obj, self.k
        y = self._normalise(X)
        N = X.shape[0]

        # t1: identity for position, s_linear for distance
        t1 = np.copy(y)
        t1[:, k:] = _s_linear(y[:, k:], 0.35)

        # t2: identity for position, b_flat for distance
        t2 = np.copy(t1)
        t2[:, k:] = _b_flat(t1[:, k:], 0.8, 0.75, 0.85)

        # t3: b_poly for all
        t3 = _b_poly(t2, 0.02)

        # t4: weighted-sum reduction to M params
        t4 = np.empty((N, M))
        for i in range(M - 1):
            start = i * k // (M - 1)
            end = (i + 1) * k // (M - 1)
            seg = t3[:, start:end]
            w = 2.0 * np.arange(start + 1, end + 1, dtype=float)
            t4[:, i] = _r_sum(seg, w)
        seg = t3[:, k:]
        w = 2.0 * np.arange(k + 1, self.n_var + 1, dtype=float)
        t4[:, M - 1] = _r_sum(seg, w)

        def shape(x_list, M_):
            h_convex = _shape_convex(x_list, M_)
            h_convex[-1] = _shape_mixed(x_list[-1] if x_list else np.zeros(N), A=5, alpha=1.0)
            return h_convex

        out["F"] = self._post(t4, shape)

    def true_pareto_front(self, n=500):
        """Analytical convex + mixed PF. f1=S1·h_convex, f2=S2·h_mixed, NDS-filtered."""
        t = np.linspace(0, 1, n)
        f1 = 2.0 * (1.0 - np.cos(t * np.pi / 2.0))
        h_mixed = np.clip(
            1.0 - t - np.cos(10.0 * np.pi * t + np.pi / 2.0) / (10.0 * np.pi),
            0.0, 1.0)
        f2 = 4.0 * h_mixed
        F = np.column_stack([f1, f2])
        idx = _nds_filter(F)
        X_ps = np.empty((n, self.n_var))
        for i in range(self.n_var):
            if i < self.k:
                X_ps[:, i] = t * 2.0 * (i + 1)
            else:
                X_ps[:, i] = 0.35 * 2.0 * (i + 1)
        return X_ps[idx], F[idx]


# ── WFG2 ──────────────────────────────────────────────────────────────────

class WFG2(_WFGBase):
    """
    WFG2 – non-separable distance parameters.
    PF shape: convex + disconnected.
    Requires l to be even.
    """

    def _evaluate(self, X, out, *args, **kwargs):
        M, k, l = self.n_obj, self.k, self.l
        y = self._normalise(X)
        N = X.shape[0]

        # t1: identity for position, s_linear for distance
        t1 = np.copy(y)
        t1[:, k:] = _s_linear(y[:, k:], 0.35)

        # t2: identity for position; r_nonsep(2) on pairs of distance params
        t2_pos = t1[:, :k]
        half = l // 2
        t2_dist = np.empty((N, half))
        for i in range(half):
            seg = t1[:, k + 2 * i: k + 2 * i + 2]
            t2_dist[:, i] = _r_nonsep(seg, 2)
        t2 = np.column_stack([t2_pos, t2_dist])

        # t3: weighted-sum reduction to M params
        t3 = np.empty((N, M))
        kk = k
        for i in range(M - 1):
            start = i * kk // (M - 1)
            end = (i + 1) * kk // (M - 1)
            seg = t2[:, start:end]
            w = np.ones(end - start)
            t3[:, i] = _r_sum(seg, w)
        seg = t2[:, kk:]
        w = np.ones(seg.shape[1])
        t3[:, M - 1] = _r_sum(seg, w)

        def shape(x_list, M_):
            h_convex = _shape_convex(x_list, M_)
            h_convex[-1] = _shape_disc(x_list[-1] if x_list else np.zeros(N), A=5, alpha=1.0, beta=1.0)
            return h_convex

        out["F"] = self._post(t3, shape)

    def true_pareto_front(self, n=500):
        """WFG2 has a disconnected PF; NDS filter removes dominated parts."""
        X, F = _WFGBase.true_pareto_front(self, n)
        idx = _nds_filter(F)
        return X[idx], F[idx]


# ── WFG4 ──────────────────────────────────────────────────────────────────

class WFG4(_WFGBase):
    """
    WFG4 – multimodal (s_multi on every param).
    PF shape: concave.
    """

    def _evaluate(self, X, out, *args, **kwargs):
        M, k = self.n_obj, self.k
        y = self._normalise(X)
        N = X.shape[0]

        # t1: s_multi for all
        t1 = _s_multi(y, A=30, B=10, C=0.35)

        # t2: weighted-sum reduction
        t2 = np.empty((N, M))
        for i in range(M - 1):
            start = i * k // (M - 1)
            end = (i + 1) * k // (M - 1)
            seg = t1[:, start:end]
            w = np.ones(end - start)
            t2[:, i] = _r_sum(seg, w)
        seg = t1[:, k:]
        w = np.ones(seg.shape[1])
        t2[:, M - 1] = _r_sum(seg, w)

        out["F"] = self._post(t2, _shape_concave)


# ── WFG5 ──────────────────────────────────────────────────────────────────

class WFG5(_WFGBase):
    """
    WFG5 – deceptive (s_decept on every param).
    PF shape: concave.
    """

    def _evaluate(self, X, out, *args, **kwargs):
        M, k = self.n_obj, self.k
        y = self._normalise(X)
        N = X.shape[0]

        # t1: s_decept for all
        t1 = _s_decept(y, 0.35, 0.001, 0.05)

        # t2: weighted-sum reduction
        t2 = np.empty((N, M))
        for i in range(M - 1):
            start = i * k // (M - 1)
            end = (i + 1) * k // (M - 1)
            seg = t1[:, start:end]
            w = np.ones(end - start)
            t2[:, i] = _r_sum(seg, w)
        seg = t1[:, k:]
        w = np.ones(seg.shape[1])
        t2[:, M - 1] = _r_sum(seg, w)

        out["F"] = self._post(t2, _shape_concave)


# ── WFG9 ──────────────────────────────────────────────────────────────────

class WFG9(_WFGBase):
    """
    WFG9 – parameter-dependent bias, deceptive positions, multimodal
    distances, nonseparable reduction.
    PF shape: concave.
    """

    def _evaluate(self, X, out, *args, **kwargs):
        M, k = self.n_obj, self.k
        n = self.n_var
        y = self._normalise(X)
        N = X.shape[0]

        # t1: b_param (dependent bias) for i < n, identity for last
        t1 = np.empty_like(y)
        for i in range(n - 1):
            u_i = _r_sum(y[:, i + 1:], np.ones(n - i - 1))
            t1[:, i] = _b_param(y[:, i], u_i, 0.98 / 49.98, 0.02, 50.0)
        t1[:, n - 1] = y[:, n - 1]

        # t2: s_decept for position, s_multi for distance
        t2 = np.empty_like(t1)
        t2[:, :k] = _s_decept(t1[:, :k], 0.35, 0.001, 0.05)
        t2[:, k:] = _s_multi(t1[:, k:], A=30, B=95, C=0.35)

        # t3: r_nonsep reduction
        t3 = np.empty((N, M))
        for i in range(M - 1):
            start = i * k // (M - 1)
            end = (i + 1) * k // (M - 1)
            seg = t2[:, start:end]
            t3[:, i] = _r_nonsep(seg, k // (M - 1))
        seg = t2[:, k:]
        t3[:, M - 1] = _r_nonsep(seg, self.l)

        out["F"] = self._post(t3, _shape_concave)

    def true_pareto_front(self, n=500):
        """Analytical concave PF: f1=2·sin(t·π/2), f2=4·cos(t·π/2). Same ellipse as WFG4/5."""
        t = np.linspace(0, 1, n)
        f1 = 2.0 * np.sin(t * np.pi / 2.0)
        f2 = 4.0 * np.cos(t * np.pi / 2.0)
        F = np.column_stack([f1, f2])
        X = np.empty((n, self.n_var))
        for i in range(self.n_var):
            if i < self.k:
                X[:, i] = t * 2.0 * (i + 1)
            else:
                X[:, i] = 0.35 * 2.0 * (i + 1)
        return X, F


# ═══════════════════════════════════════════════════════════════════════════
#  BBOB bi-objective suite  (bbob-biobj; Tušar et al. 2016)
#
#  Each function f = (f_α, f_β) combines two single-objective bbob functions
#  (Hansen et al. 2009, RR-6829).  Properties:
#
#  • Objectives are RAW / un-normalised.  COCO normalises only for its
#    hypervolume metric (bbob-biobj report §2.3), never inside the function.
#  • f_opt is dropped (≡ 0) so each objective's global minimum is exactly 0.
#  • Per COCO the two objectives use DIFFERENT instances
#    (Kα = 2K+1, Kβ = 2K+2) so the two single-objective optima differ and the
#    Pareto set is a non-degenerate curve between them.
#  • Search domain [-5, 5]^D (report §3.2: the extremal solutions and their
#    radius-1 neighbourhood are guaranteed to lie there).
#  • Instance parameters (x_opt, rotations R/Q, Gallagher peaks) come from a
#    numpy RNG seeded by (bbob_fid, instance_id, n_var).  This reproduces the
#    bbob-biobj landscape characteristics but is NOT bit-identical to COCO's
#    own RNG (cocoex is not a project dependency).
#
#  Only F1 (Sphere/Sphere) has an analytical Pareto front (segment between
#  the two sphere optima).  The other six have no closed form; their
#  true_pareto_front is COCO's own approach: accumulated NSGA-II runs.
# ═══════════════════════════════════════════════════════════════════════════

_BBOB_PF_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "bbob_pf_cache",
)


def _bbob_rng(fid, inst, n_var):
    """Deterministic Generator keyed by (function id, instance id, dim)."""
    return np.random.default_rng(
        np.random.SeedSequence([int(fid), int(inst), int(n_var)]))


def _bbob_lambda_diag(alpha, D):
    """Diagonal of Λ^α: λ_ii = α^(0.5·(i−1)/(D−1)), i=1..D.  Returns (D,)."""
    if D == 1:
        return np.ones(1)
    i = np.arange(D, dtype=float)
    return alpha ** (0.5 * i / (D - 1.0))


def _bbob_T_osz(x):
    """Oscillation transformation T_osz, element-wise (T_osz(0)=0)."""
    x = np.asarray(x, dtype=float)
    s = np.sign(x)
    absx = np.abs(x)
    nz = absx > 0.0
    xhat = np.where(nz, np.log(np.where(nz, absx, 1.0)), 0.0)
    c1 = np.where(x > 0.0, 10.0, 5.5)
    c2 = np.where(x > 0.0, 7.9, 3.1)
    return s * np.exp(xhat + 0.049 * (np.sin(c1 * xhat) + np.sin(c2 * xhat)))


def _bbob_T_asy(x, beta):
    """Asymmetry transformation T_asy^β on (N, D); positive entries only."""
    x = np.asarray(x, dtype=float)
    D = x.shape[1]
    if D == 1:
        return x.copy()
    i = np.arange(D, dtype=float)
    expo = 1.0 + beta * (i / (D - 1.0)) * np.sqrt(np.maximum(x, 0.0))
    return np.where(x > 0.0, np.power(np.maximum(x, 0.0), expo), x)


def _bbob_f_pen(X):
    """Boundary penalty Σ max(0,|x_i|−5)².  X: (N, D) → (N,)."""
    return np.sum(np.maximum(0.0, np.abs(X) - 5.0) ** 2, axis=1)


def _bbob_rotation(rng, D):
    """Random orthonormal D×D matrix (Gram–Schmidt via QR), sign-fixed."""
    Qm, Rm = np.linalg.qr(rng.standard_normal((D, D)))
    return Qm * np.sign(np.diag(Rm))


class _BBOBSingle:
    """A single-objective bbob function instance with f_opt ≡ 0.

    Supported bbob ids: 1 Sphere, 2 Ellipsoid separable, 6 Attractive sector,
    13 Sharp ridge, 15 Rastrigin, 17 Schaffer F7 (cond 10),
    21 Gallagher's Gaussian 101-me peaks.  Callable: X (N,D) → f (N,).
    """

    def __init__(self, fid, inst, D):
        self.fid = int(fid)
        self.D = int(D)
        rng = _bbob_rng(fid, inst, D)
        self.x_opt = rng.uniform(-4.0, 4.0, self.D)
        self.R = _bbob_rotation(rng, self.D)
        self.Q = _bbob_rotation(rng, self.D)
        self.lam10 = _bbob_lambda_diag(10.0, self.D)
        if self.fid == 21:
            self._init_gallagher(rng)

    def _init_gallagher(self, rng):
        D, n_peaks = self.D, 101
        w = np.empty(n_peaks)
        w[0] = 10.0
        w[1:] = 1.1 + 8.0 * (np.arange(2, n_peaks + 1) - 2.0) / 99.0
        self.g_w = w

        alphas = np.empty(n_peaks)
        alphas[0] = 1000.0
        alphas[1:] = rng.permutation(1000.0 ** (2.0 * np.arange(100) / 99.0))
        C = np.empty((n_peaks, D))
        for k in range(n_peaks):
            diag = rng.permutation(_bbob_lambda_diag(alphas[k], D))
            C[k] = diag / (alphas[k] ** 0.25)
        self.g_C = C

        Y = np.empty((n_peaks, D))
        Y[0] = self.x_opt
        Y[1:] = rng.uniform(-4.9, 4.9, (n_peaks - 1, D))
        self.g_Y = Y

    def __call__(self, X):
        X = np.atleast_2d(np.asarray(X, dtype=float))
        fid, D = self.fid, self.D

        if fid == 1:                                            # Sphere
            z = X - self.x_opt
            return np.sum(z * z, axis=1)

        if fid == 2:                                            # Ellipsoid sep.
            z = _bbob_T_osz(X - self.x_opt)
            expo = (np.arange(D, dtype=float) / (D - 1.0)) if D > 1 \
                else np.zeros(D)
            return np.sum(10.0 ** (6.0 * expo) * z * z, axis=1)

        if fid == 6:                                            # Attr. sector
            z = ((X - self.x_opt) @ self.R.T) * self.lam10
            z = z @ self.Q.T
            s = np.where(z * self.x_opt > 0.0, 100.0, 1.0)
            return _bbob_T_osz(np.sum((s * z) ** 2, axis=1)) ** 0.9

        if fid == 13:                                           # Sharp ridge
            z = ((X - self.x_opt) @ self.R.T) * self.lam10
            z = z @ self.Q.T
            return z[:, 0] ** 2 + 100.0 * np.sqrt(
                np.sum(z[:, 1:] ** 2, axis=1))

        if fid == 15:                                           # Rastrigin
            z = (X - self.x_opt) @ self.R.T
            z = _bbob_T_asy(_bbob_T_osz(z), 0.2) * self.lam10
            z = (z @ self.Q.T) @ self.R.T
            return (10.0 * (D - np.sum(np.cos(2.0 * np.pi * z), axis=1))
                    + np.sum(z * z, axis=1))

        if fid == 17:                                           # Schaffer F7
            z = _bbob_T_asy((X - self.x_opt) @ self.R.T, 0.5)
            z = (z @ self.Q.T) * self.lam10
            s = np.sqrt(z[:, :-1] ** 2 + z[:, 1:] ** 2)
            inner = np.mean(
                np.sqrt(s) + np.sqrt(s) * np.sin(50.0 * s ** 0.2) ** 2, axis=1)
            return inner ** 2 + 10.0 * _bbob_f_pen(X)

        if fid == 21:                                           # Gallagher 101
            best = np.full(X.shape[0], -np.inf)
            for k in range(self.g_Y.shape[0]):
                d = (X - self.g_Y[k]) @ self.R.T
                quad = np.sum(self.g_C[k] * d * d, axis=1)
                best = np.maximum(
                    best, self.g_w[k] * np.exp(-quad / (2.0 * D)))
            return _bbob_T_osz(10.0 - best) ** 2 + _bbob_f_pen(X)

        raise ValueError(f"Unsupported bbob function id: {fid}")


class _BBOBBiobjBase(Problem):
    """Base for bbob-biobj functions f = (f_{_FID_A}, f_{_FID_B})."""

    _FID_A = None
    _FID_B = None

    def __init__(self, n_var=10, instance=1):
        xl, xu = _make_bounds([[-5.0, 5.0]] * n_var)
        super().__init__(n_var=n_var, n_obj=2, xl=xl, xu=xu)
        self.instance = int(instance)
        K = self.instance
        self._fa = _BBOBSingle(self._FID_A, 2 * K + 1, n_var)
        self._fb = _BBOBSingle(self._FID_B, 2 * K + 2, n_var)

    def _evaluate(self, X, out, *args, **kwargs):
        X = np.atleast_2d(np.asarray(X, dtype=float))
        out["F"] = np.column_stack([self._fa(X), self._fb(X)])

    # ── reference Pareto front (empirical, NSGA-II accumulation) ──────────
    def true_pareto_front(self, n=1000, pop_size=200, n_gen=300,
                          n_seeds=5, seed=0):
        """COCO has no closed-form PF for these (report Fig. 1 uses NSGA-II).
        Accumulate the non-dominated points of `n_seeds` independent NSGA-II
        runs, cache to data/bbob_pf_cache/, subsample to `n` points."""
        cache = os.path.join(
            _BBOB_PF_CACHE_DIR,
            f"{type(self).__name__}_d{self.n_var}_i{self.instance}.npz")
        if os.path.exists(cache):
            d = np.load(cache)
            X, F = d["X"], d["F"]
        else:
            X, F = self._nsga2_front(pop_size, n_gen, n_seeds, seed)
            os.makedirs(_BBOB_PF_CACHE_DIR, exist_ok=True)
            np.savez_compressed(cache, X=X, F=F)
        if len(F) > n:
            idx = self._subsample_front(F, n)
            X, F = X[idx], F[idx]
        return X, F

    def _nsga2_front(self, pop_size, n_gen, n_seeds, seed):
        from pymoo.algorithms.moo.nsga2 import NSGA2
        from pymoo.optimize import minimize
        Xs, Fs = [], []
        for s in range(seed, seed + n_seeds):
            res = minimize(self, NSGA2(pop_size=pop_size),
                           ("n_gen", n_gen), seed=s, verbose=False)
            if res.X is not None:
                Xs.append(np.atleast_2d(res.X))
                Fs.append(np.atleast_2d(res.F))
        X = np.vstack(Xs)
        F = np.vstack(Fs)
        idx = _nds_filter(F)
        return X[idx], F[idx]

    @staticmethod
    def _subsample_front(F, n):
        order = np.argsort(F[:, 0])
        pick = np.unique(np.linspace(0, len(order) - 1, n).round().astype(int))
        return order[pick]


class BBOB_F1_Sphere_Sphere(_BBOBBiobjBase):
    """
    bbob-biobj F1 – Sphere / Sphere  (bbob f1 / f1).

    f_α = ‖x − x_optα‖²,   f_β = ‖x − x_optβ‖².
    Search space: x_i ∈ [−5, 5], default n_var = 10.

    Analytical Pareto set: the straight segment between the two sphere
    optima.  Pareto front convex; closed-form normalised hypervolume
    (nadir reference) = 1 − ∫₀¹(1−√x)²dx = 0.8333…
    """
    _FID_A = 1
    _FID_B = 1

    def true_pareto_front(self, n=1000):
        a, b = self._fa.x_opt, self._fb.x_opt
        t = np.linspace(0.0, 1.0, n).reshape(-1, 1)
        X = a + t * (b - a)
        return X, evaluate_problem(self, X)


class BBOB_F5_Sphere_SharpRidge(_BBOBBiobjBase):
    """
    bbob-biobj F5 – Sphere / Sharp ridge  (bbob f1 / f13).

    f_α = ‖x − x_optα‖²  (separable, convex).
    f_β = z₁² + 100·√(Σ_{i≥2} z_i²),  z = Q·Λ¹⁰·R·(x − x_optβ)
          (non-separable, non-differentiable ridge).
    Search space: x_i ∈ [−5, 5], default n_var = 10.
    No closed-form PF; true_pareto_front uses accumulated NSGA-II.
    """
    _FID_A = 1
    _FID_B = 13


class BBOB_F17_EllipsoidSeparable_SchafferF7(_BBOBBiobjBase):
    """
    bbob-biobj F17 – Ellipsoid separable / Schaffer F7 cond 10
    (bbob f2 / f17).

    f_α = Σ 10^(6(i−1)/(D−1)) z_i²,  z = T_osz(x − x_optα)  (ill-conditioned).
    f_β = (mean_i(√s_i + √s_i·sin²(50 s_i^{1/5})))² + 10·f_pen,
          s_i = √(z_i²+z_{i+1}²),  z = Λ¹⁰·Q·T_asy^{0.5}(R·(x − x_optβ))
          (asymmetric, non-separable, highly multimodal).
    Search space: x_i ∈ [−5, 5], default n_var = 10.
    No closed-form PF; true_pareto_front uses accumulated NSGA-II.
    """
    _FID_A = 2
    _FID_B = 17


class BBOB_F22_AttractiveSector_SharpRidge(_BBOBBiobjBase):
    """
    bbob-biobj F22 – Attractive sector / Sharp ridge  (bbob f6 / f13).

    f_α = T_osz(Σ(s_i z_i)²)^0.9,  z = Q·Λ¹⁰·R·(x − x_optα),
          s_i = 100 if z_i·x_optα_i>0 else 1  (highly asymmetric).
    f_β = z₁² + 100·√(Σ_{i≥2} z_i²),  z = Q·Λ¹⁰·R·(x − x_optβ)
          (non-differentiable ridge).
    Search space: x_i ∈ [−5, 5], default n_var = 10.
    No closed-form PF; true_pareto_front uses accumulated NSGA-II.
    """
    _FID_A = 6
    _FID_B = 13


class BBOB_F37_SharpRidge_Rastrigin(_BBOBBiobjBase):
    """
    bbob-biobj F37 – Sharp ridge / Rastrigin  (bbob f13 / f15).

    f_α = z₁² + 100·√(Σ_{i≥2} z_i²),  z = Q·Λ¹⁰·R·(x − x_optα).
    f_β = 10·(D − Σ cos(2π z_i)) + ‖z‖²,
          z = R·Λ¹⁰·Q·T_asy^{0.2}(T_osz(R·(x − x_optβ)))
          (non-separable, ≈10^D local optima).
    Search space: x_i ∈ [−5, 5], default n_var = 10.
    No closed-form PF; true_pareto_front uses accumulated NSGA-II.
    """
    _FID_A = 13
    _FID_B = 15


class BBOB_F49_Rastrigin_Gallagher101(_BBOBBiobjBase):
    """
    bbob-biobj F49 – Rastrigin / Gallagher 101 peaks  (bbob f15 / f21).

    f_α = 10·(D − Σ cos(2π z_i)) + ‖z‖²  (≈10^D local optima).
    f_β = T_osz(10 − max_i w_i·exp(−1/(2D)·(x−y_i)ᵀRᵀC_iR(x−y_i)))² + f_pen
          (101 randomly placed peaks, weak global structure).
    Search space: x_i ∈ [−5, 5], default n_var = 10.
    No closed-form PF; true_pareto_front uses accumulated NSGA-II.
    """
    _FID_A = 15
    _FID_B = 21


class BBOB_F55_Gallagher101_Gallagher101(_BBOBBiobjBase):
    """
    bbob-biobj F55 – Gallagher 101 peaks / Gallagher 101 peaks
    (bbob f21 / f21).

    Both objectives: T_osz(10 − max_i w_i·exp(−1/(2D)·(x−y_i)ᵀRᵀC_iR(x−y_i)))²
    + f_pen, with independent random peak fields (different instances).
    No global structure in either objective.
    Search space: x_i ∈ [−5, 5], default n_var = 10.
    No closed-form PF; true_pareto_front uses accumulated NSGA-II.
    """
    _FID_A = 21
    _FID_B = 21



# ═══════════════════════════════════════════════════════════════════════════
#  PROBLEMAS DE DADOS REAIS (D101/REAL-1) — RE21 · DDMOP7 · ESTOQUE40
#
#  Escada de dimensionalidade D = 4 → 17 → 40 (maxFE 31D−1 = 123 → 526 → 1239)
#  e escada de "modo de realidade": fórmula física → dado como ambiente de
#  avaliação → dado como distribuição empírica. Transplantados BIT-A-BIT de
#  `real_problems.py` do pacote de fusão do Agente 8 (2026-08-04), com três
#  adaptações declaradas: (i) caminhos de dados re-ancorados na raiz do repo;
#  (ii) docstring dos slots do DDMOP7 corrigido pelo mapa MEDIDO (TD-18);
#  (iii) o port aritmético morto do DDMOP7 NÃO veio — é registro histórico e
#  vive no arquivo de fusão (`mestrado2/_real_experiments/real_problems.py`).
#  Posições no catálogo (Q1, IRREVERSÍVEL): RE21=25 · DDMOP7=26 · ESTOQUE40=27.
# ═══════════════════════════════════════════════════════════════════════════

#: Espelha `_BBOB_PF_CACHE_DIR`: <repo-root>/data/real_pf_cache (D72).
_REAL_PF_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "real_pf_cache")

#: Fontes congeladas dos problemas reais: <repo-root>/data/real_sources.
_REAL_SOURCES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "real_sources")


class _EmpiricalFrontMixin:
    """Front de referência D72 para problemas sem forma fechada.

    Mesma abordagem dos BBOB: acumula os não-dominados de `n_seeds` runs
    independentes de NSGA-II (pop 200 × 300 ger × 5 sementes), cacheia em
    `data/real_pf_cache/` e subamostra para `n`. NUNCA recompute em laço —
    o ESTOQUE40 custa 164 s por recomputação; o cache é a via."""

    def true_pareto_front(self, n=1000, pop_size=200, n_gen=300,
                          n_seeds=5, seed=0):
        cache = os.path.join(_REAL_PF_CACHE_DIR,
                             f"{type(self).__name__}_d{self.n_var}.npz")
        if os.path.exists(cache):
            d = np.load(cache)
            X, F = d["X"], d["F"]
        else:
            X, F = self._nsga2_front(pop_size, n_gen, n_seeds, seed)
            os.makedirs(_REAL_PF_CACHE_DIR, exist_ok=True)
            np.savez_compressed(cache, X=X, F=F)
        if len(F) > n:
            idx = self._subsample_front(F, n)
            X, F = X[idx], F[idx]
        return X, F

    def _nsga2_front(self, pop_size, n_gen, n_seeds, seed):
        from pymoo.algorithms.moo.nsga2 import NSGA2
        from pymoo.optimize import minimize
        Xs, Fs = [], []
        for s in range(seed, seed + n_seeds):
            res = minimize(self, NSGA2(pop_size=pop_size), ("n_gen", n_gen),
                           seed=s, verbose=False)
            if res.X is not None:
                Xs.append(np.atleast_2d(res.X))
                Fs.append(np.atleast_2d(res.F))
        X, F = np.vstack(Xs), np.vstack(Fs)
        idx = _nds_filter(F)
        return X[idx], F[idx]

    @staticmethod
    def _subsample_front(F, n):
        order = np.argsort(F[:, 0])
        pick = np.unique(np.linspace(0, len(order) - 1, n).round().astype(int))
        return order[pick]


class RE21(_EmpiricalFrontMixin, Problem):
    """RE21 — four-bar truss design (Tanabe & Ishibuchi 2020). M=2, D=4.

    x1..x4 = áreas de seção das quatro barras. Constantes: F=10, sigma=10,
    E=2e5, L=200; a = F/sigma = 1. Bounds: x1,x4 ∈ [a,3a]; x2,x3 ∈ [√2·a,3a].
    Objetivos (ambos minimizados, genuinamente conflitantes):
      f1 = L·(2·x1 + √2·x2 + √x3 + x4)                    (volume estrutural)
      f2 = (F·L/E)·(2/x1 + 2√2/x2 − 2√2/x3 + 2/x4)        (deslocamento nodal)
    Fidelidade: EXATA — bit-verificada contra o `reproblem.py` oficial
    (dif = 0,0; IGD⁺ cruzado 4,82e-4/1,28e-4). Formulação: Cheng & Li (1999).
    Front de referência = D72 empírico (D102.13); o oficial da suíte RE fica
    como cross-check em `front_oficial_suite_RE()` e não alimenta métrica."""
    _F, _SIGMA, _E, _L = 10.0, 10.0, 2.0e5, 200.0

    def __init__(self):
        a = self._F / self._SIGMA          # = 1.0
        s2a = np.sqrt(2.0) * a
        bounds = [[a, 3 * a], [s2a, 3 * a], [s2a, 3 * a], [a, 3 * a]]
        xl, xu = _make_bounds(bounds)
        super().__init__(n_var=4, n_obj=2, xl=xl, xu=xu)

    def _evaluate(self, X, out, *args, **kwargs):
        x1, x2, x3, x4 = X[:, 0], X[:, 1], X[:, 2], X[:, 3]
        s2 = np.sqrt(2.0)
        f1 = self._L * (2.0 * x1 + s2 * x2 + np.sqrt(x3) + x4)
        f2 = (self._F * self._L / self._E) * (
            2.0 / x1 + 2.0 * s2 / x2 - 2.0 * s2 / x3 + 2.0 / x4)
        out["F"] = np.column_stack([f1, f2])

    @staticmethod
    def front_oficial_suite_RE():
        """Front aproximado OFICIAL da suíte RE — só `F`, cross-check citável.

        NÃO é a referência das métricas (não tem X; o contrato D72 pede o
        par). `None` se o arquivo congelado não estiver presente."""
        f = os.path.join(_REAL_SOURCES_DIR, "RE21_reference_front.npy")
        return np.load(f) if os.path.exists(f) else None


def _importa_ponte_ddmop7():
    """Importa `DDMOP7Matlab` (a ponte oficial). Import TARDIO de propósito:
    importar o catálogo não pode puxar a MATLAB Engine — o F0 importa
    `problems.py` em máquina sem MATLAB nenhum. [TD-07 resolvido: a ponte
    mora em `src/ddmop7_bridge.py`; o fallback plano cobre execução avulsa.]"""
    erros = []
    for mod in ("src.ddmop7_bridge", "ddmop7_bridge"):
        try:
            return __import__(mod, fromlist=["DDMOP7Matlab"]).DDMOP7Matlab
        except Exception as e:                                    # noqa: BLE001
            erros.append(f"{mod}: {type(e).__name__}: {e}")
    raise ImportError(
        "nao encontrei DDMOP7Matlab (a ponte oficial do DDMOP7). Tentativas:\n  "
        + "\n  ".join(erros))


class DDMOP7(Problem):
    """DDMOP7 — treino de rede neural (Statlog Australian Credit). M=2, D=17.

    AQUI NÃO SE CALCULA f. Esta classe é a CASCA que dá ao DDMOP7 a mesma
    porta dos outros 27 (subclasse de `Problem`, instanciação sem argumento);
    a avaliação DELEGA ao `DDMOP7.p` oficial via `ddmop7_bridge.DDMOP7Matlab`
    (D102.5/D88.5) — que conta FE, aplica o hard-stop exato em 526 (D21/D61),
    deduplica por X bit-a-bit (D57/D89) e monta a camada ①. O port aritmético
    exigia 3 definições que o paper não dá (EPS, ativação, normalização) —
    escolhê-las é o que o D81 proíbe; foram DISSOLVIDAS pela caixa-preta.

    VARIÁVEIS DE DECISÃO (17), em [−1,1]^17 — mapa dos slots MEDIDO no oráculo
    (TD-18; 5 batimentos exatos, `ddmop7_VEREDICTO.md` §7 + evidência em
    `docs/exemplos/DDMOP7_evidencia_slots.csv` do pacote de fusão):
        x[0]    viés do neurônio oculto
        x[1:15] os 14 pesos de entrada (atributo j ↔ x[j])
        x[15]   viés de saída
        x[16]   peso oculta→saída
    OBJETIVOS (ambos minimizados), verbatim do paper:
        f1 = "the ratio of nonzero weights" ⇒ k/17, um DEGRAU (o treino
             interno nunca poda: 55/62 pontos do oráculo deram f1 = 1,0)
        f2 = "the classification error rate" (quantizado em múltiplos de 1/690)
    Referência: He, Tian, Wang & Jin, Complex & Intelligent Systems 6(1) (2020).

    LIGAÇÃO TARDIA À SEMENTE: `DDMOP7()` instancia BARATO (sem MATLAB, sem
    DoE, sem FE — serve ao catálogo/F0/gates); `prob.bind(semente=s)` liga à
    ponte e ao DoE congelado daquela semente; `DDMOP7_SEMENTE=<s>` no ambiente
    liga sozinho no __init__; avaliar sem ligar = RuntimeError pára-e-loga
    (D81). Um objeto ligado = UM run (D88.5) — para outra semente, outro
    objeto. Regime especial: SEM sonda (D102.10, ver
    `experiment.PROBLEMAS_SEM_SONDA`), SEM front D72 (D102.4 — só HV), régua
    S.5 em duas fases com selo (D102.3)."""

    D = 17
    BOUND = 1.0
    DOE_N = 11 * 17 - 1                 # 186   (D63)
    MAX_FE = 31 * 17 - 1                # 526   (D21/D61, hard-stop exato)
    P_CODE_CAP = 600                    # teto interno do próprio DDMOP7.p

    def __init__(self, semente=None, **kw_ponte):
        super().__init__(n_var=self.D, n_obj=2,
                         xl=np.full(self.D, -self.BOUND),
                         xu=np.full(self.D, +self.BOUND))
        self._ponte = None
        self._kw_ponte = dict(kw_ponte)
        self.semente = None
        if semente is None:
            env = os.environ.get("DDMOP7_SEMENTE", "").strip()
            semente = int(env) if env else None
        if semente is not None:
            self.bind(semente)

    def bind(self, semente, **kw_ponte):
        """Liga esta casca à ponte oficial, para UMA semente. Devolve `self`."""
        if self._ponte is not None:
            raise RuntimeError(
                f"DDMOP7 ja esta ligado a semente {self.semente} (D88.5: um "
                f"objeto = um run). Para a semente {semente}, construa outro "
                f"objeto. Se o run anterior acabou, chame encerra() antes.")
        DDMOP7Matlab = _importa_ponte_ddmop7()
        kw = dict(self._kw_ponte)
        kw.update(kw_ponte)
        self._ponte = DDMOP7Matlab(semente=int(semente), **kw)
        self.semente = int(semente)
        return self

    @property
    def ligado(self):
        return self._ponte is not None

    @property
    def ponte(self):
        self._exige_ligado("acessar a ponte")
        return self._ponte

    def _exige_ligado(self, acao):
        if self._ponte is None:
            raise RuntimeError(
                f"DDMOP7 nao esta ligado a nenhuma semente -- nao da para "
                f"{acao}. Pare-e-logue (D81): esta classe e so a casca; a "
                f"avaliacao mora no DDMOP7.p oficial. Ligue com "
                f"prob.bind(semente=<s>), construa com DDMOP7(semente=<s>), "
                f"ou exporte DDMOP7_SEMENTE=<s> no ambiente. "
                f"NUNCA presuma uma semente: o DoE do DDMOP7 vem de sorteios "
                f"CONGELADOS de DDMOP7('init'), que e ESTOCASTICO (D102.1).")

    def _evaluate(self, X, out, *args, **kwargs):
        """Delega ao `.p` oficial — ponto único de FE, hard-stop, solution_id.
        Sem aritmética aqui DE PROPÓSITO (qualquer conta seria o port morto
        de volta pela janela)."""
        self._exige_ligado("avaliar")
        return self._ponte._evaluate(X, out, *args, **kwargs)

    @property
    def doe(self):
        self._exige_ligado("ler o DoE")
        return self._ponte.doe

    @property
    def fe(self):
        self._exige_ligado("ler o contador de FE")
        return self._ponte.fe

    def camada1(self):
        self._exige_ligado("montar a camada ①")
        return self._ponte.camada1()

    def manifesto(self, status="ok", extra=None):
        self._exige_ligado("emitir o manifesto")
        return self._ponte.manifesto(status, extra)

    def encerra(self):
        """Fecha a MATLAB Engine (D86). Idempotente e seguro se desligado."""
        if self._ponte is not None:
            self._ponte.encerra()

    def true_pareto_front(self, n=1000, *args, **kwargs):
        """SEMPRE levanta — PARA-RAIOS do D72 (D102.4), não preguiça.

        Se esta classe herdasse a maquinaria empírica, uma chamada distraída
        dispararia 300.000 avaliações REAIS no `.p` = 21,76 DIAS-core em
        silêncio. O DDMOP7 é reportado só por HV (f1 = k/17 quantizado ⇒
        |ND| ≤ 18; um IGD⁺ contra um "front" desses mediria ruído). Quem itera
        problemas chamando fronts DEVE pular `PROBLEMAS_SEM_FRONT_D72`
        (`src/metrics.py`) — falhar alto aqui é o comportamento certo."""
        raise NotImplementedError("D102.4: DDMOP7 não tem front D72")


class ESTOQUE40(_EmpiricalFrontMixin, Problem):
    """ESTOQUE40 — reposição semanal dos top-40 produtos. M=3, D=40.

    Construído do dado REAL UCI Online Retail II (CC BY 4.0, DOI
    10.24432/C5CG6D) por `data_estoque.py` (pacote de fusão), que congela as
    distribuições empíricas de demanda semanal em `data/estoque_problem.npz`
    (106 semanas completas, 2009-11-30 a 2011-12-11).

    x (40) = quantidade de reposição semanal por produto, bounds [0, q95_i].
    Objetivos (todos minimizados; receita NEGADA para virar minimização):
      f1 = − Σ_i price_i · E_w[min(x_i, D_{i,w})]      (receita esperada, neg.)
      f2 =   Σ_i hold_i  · E_w[max(x_i − D_{i,w}, 0)]  (custo de sobra)
      f3 =   Σ_c (cov_c − mean)²  (desequilíbrio de cobertura por categoria;
             8 × a variância — acopla variáveis, não-separável)
    E_w[·] é a média empírica EXATA sobre as semanas; contínuo por partes.
    Categoria = família `StockCode[:3]` → índice de ordem lexicográfica entre
    as 26 famílias → mod 8 (regra A1 — NÃO é "dígitos mod 8")."""

    def __init__(self, npz_path=None):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        npz_path = npz_path or os.path.join(root, "data",
                                            "estoque_problem.npz")
        d = np.load(npz_path)
        self._D = d["demand"].astype(float)            # (P, W)
        self._price = d["price"].astype(float)         # (P,)
        self._hold = d["hold"].astype(float)           # (P,)
        self._cat = d["category"].astype(int)          # (P,)
        self._stock = d["current_stock"].astype(float)  # (P,)
        self._meandem = self._D.mean(axis=1)           # (P,)
        self._cats = np.unique(self._cat)
        self._stock_c = np.array([self._stock[self._cat == c].sum()
                                  for c in self._cats])
        self._meandem_c = np.array([self._meandem[self._cat == c].sum()
                                    for c in self._cats])
        P = self._D.shape[0]
        xl = np.zeros(P)
        xu = d["xu"].astype(float)
        super().__init__(n_var=P, n_obj=3, xl=xl, xu=xu)

    def _evaluate(self, X, out, *args, **kwargs):
        X = np.atleast_2d(np.asarray(X, dtype=float))       # (N,P)
        Dm = self._D                                        # (P,W)
        xexp = X[:, :, None]                                # (N,P,1)
        sold = np.minimum(xexp, Dm[None, :, :]).mean(axis=2)        # (N,P)
        over = np.maximum(xexp - Dm[None, :, :], 0.0).mean(axis=2)  # (N,P)
        f1 = -np.sum(self._price[None, :] * sold, axis=1)
        f2 = np.sum(self._hold[None, :] * over, axis=1)
        added_c = np.stack([X[:, self._cat == c].sum(axis=1)
                            for c in self._cats], axis=1)           # (N,C)
        cov = (self._stock_c[None, :] + added_c) / np.maximum(
            self._meandem_c[None, :], 1e-9)
        f3 = np.sum((cov - cov.mean(axis=1, keepdims=True)) ** 2, axis=1)
        out["F"] = np.column_stack([f1, f2, f3])


# ═══════════════════════════════════════════════════════════════════════════
#  Utility
# ═══════════════════════════════════════════════════════════════════════════

def evaluate_problem(problem, X):
    """
    Evaluate a pymoo Problem on decision vectors X.

    Args:
        problem: pymoo Problem instance
        X: numpy array of shape (n_solutions, n_var)

    Returns:
        F: numpy array of shape (n_solutions, n_obj) with objective values
    """
    if X.ndim == 1:
        X = X.reshape(1, -1)
    out = {}
    problem._evaluate(X, out)
    return out["F"]
