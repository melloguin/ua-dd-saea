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


def _shape_linear(x, M):
    """Linear shape."""
    h = []
    for m in range(M):
        val = np.ones(x[0].shape[0])
        for i in range(M - 1 - m):
            val *= x[i]
        if m > 0:
            val *= 1.0 - x[M - 1 - m]
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
#  BBOB Gallagher Mock  (from original problems.py)
# ═══════════════════════════════════════════════════════════════════════════

class BBOB_Gallagher_Mock(Problem):
    """
    BBOB f16 mock (Gallagher's 101 Peaks) – bi-objective version.
    Chaotic surface with n_peaks Gaussian craters per objective.
    Bounds: x1, x2 ∈ [-5, 5].
    """
    def __init__(self, n_peaks=101):
        bounds = [
            [-5.0, 5.0],   # x1
            [-5.0, 5.0],   # x2
        ]
        xl, xu = _make_bounds(bounds)
        super().__init__(n_var=2, n_obj=2, xl=xl, xu=xu)
        self.n_peaks = n_peaks

        np.random.seed(42)
        self.c1 = np.random.uniform(-4.5, 4.5, (n_peaks, 2))
        self.w1 = np.random.uniform(0.1, 2.0, n_peaks)
        self.s1 = np.random.uniform(0.2, 1.0, n_peaks)
        self.c2 = np.random.uniform(-4.5, 4.5, (n_peaks, 2))
        self.w2 = np.random.uniform(0.1, 2.0, n_peaks)
        self.s2 = np.random.uniform(0.2, 1.0, n_peaks)

        g = np.linspace(-5.0, 5.0, 500)
        X1, X2 = np.meshgrid(g, g)
        X_grid = np.column_stack([X1.ravel(), X2.ravel()])

        f1_raw = np.zeros(len(X_grid))
        f2_raw = np.zeros(len(X_grid))
        for i in range(n_peaks):
            d1 = np.sum((X_grid - self.c1[i]) ** 2, axis=1)
            f1_raw -= self.w1[i] * np.exp(-d1 / (2 * self.s1[i] ** 2))
            d2 = np.sum((X_grid - self.c2[i]) ** 2, axis=1)
            f2_raw -= self.w2[i] * np.exp(-d2 / (2 * self.s2[i] ** 2))
        self._f1_global_min = np.min(f1_raw)
        self._f2_global_min = np.min(f2_raw)

    def _evaluate(self, X, out, *args, **kwargs):
        f1 = np.zeros(X.shape[0])
        f2 = np.zeros(X.shape[0])
        for i in range(self.n_peaks):
            dist1 = np.sum((X - self.c1[i]) ** 2, axis=1)
            f1 -= self.w1[i] * np.exp(-dist1 / (2 * self.s1[i] ** 2))
            dist2 = np.sum((X - self.c2[i]) ** 2, axis=1)
            f2 -= self.w2[i] * np.exp(-dist2 / (2 * self.s2[i] ** 2))
        f1 = f1 - self._f1_global_min + 0.1
        f2 = f2 - self._f2_global_min + 0.1
        out["F"] = np.column_stack([f1, f2])

    def true_pareto_front(self, n=1000):
        """No analytical PF; computed numerically from dense grid + NDS."""
        g = np.linspace(-5.0, 5.0, n)
        X1, X2 = np.meshgrid(g, g)
        X = np.column_stack([X1.ravel(), X2.ravel()])
        F = evaluate_problem(self, X)
        idx = _nds_filter(F)
        return X[idx], F[idx]


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
