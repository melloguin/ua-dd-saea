"""
Problem definitions for the benchmark suite.

Classes extracted from notebook 1 (fitness_landscape.ipynb).
Each class inherits from pymoo.core.problem.Problem and defines
two objectives (n_obj=2) with two decision variables (n_var=2).
"""

import numpy as np
from pymoo.core.problem import Problem


class MMF1(Problem):
    """
    MMF1 (CEC 2019 MMOP) - Multimodal Multi-objective Function 1.

    Two global optimal regions in decision space, mirrored at x1=2.
    Bounds: x1 ∈ [1, 3], x2 ∈ [-1, 1]
    """
    def __init__(self):
        super().__init__(n_var=2, n_obj=2, xl=np.array([1.0, -1.0]), xu=np.array([3.0, 1.0]))

    def _evaluate(self, X, out, *args, **kwargs):
        x1, x2 = X[:, 0], X[:, 1]
        f1 = np.abs(x1 - 2.0)
        senoide = np.sin(6.0 * np.pi * np.abs(x1 - 2.0) + np.pi)
        f2 = 1.0 - np.sqrt(f1) + 2.0 * (x2 - senoide)**2
        out["F"] = np.column_stack([f1, f2])


class MMF4(Problem):
    """
    MMF4 (Symmetric Niching) - Multimodal Multi-objective Function 4.

    Four global Pareto sets in decision space forming two stacked 'M' shapes.
    Bounds: x1 ∈ [-1, 1], x2 ∈ [0, 2]
    """
    def __init__(self):
        super().__init__(n_var=2, n_obj=2, xl=np.array([-1.0, 0.0]), xu=np.array([1.0, 2.0]))

    def _evaluate(self, X, out, *args, **kwargs):
        x1, x2 = X[:, 0], X[:, 1]
        f1 = np.abs(x1)
        f2 = 1.0 - x1**2 + 2.0 * np.sin(np.pi * (x2 - np.sin(np.pi * np.abs(x1))))**2
        out["F"] = np.column_stack([f1, f2])


class BBOB_Gallagher_Mock(Problem):
    """
    BBOB f16 mock (Gallagher's 101 Peaks) - bi-objective version.

    Chaotic surface with 101 Gaussian craters per objective.
    Bounds: x1, x2 ∈ [-5, 5]
    """
    def __init__(self, n_peaks=101):
        super().__init__(n_var=2, n_obj=2, xl=np.array([-5.0, -5.0]), xu=np.array([5.0, 5.0]))
        self.n_peaks = n_peaks

        np.random.seed(42)

        self.c1 = np.random.uniform(-4.5, 4.5, (n_peaks, 2))
        self.w1 = np.random.uniform(0.1, 2.0, n_peaks)
        self.s1 = np.random.uniform(0.2, 1.0, n_peaks)

        self.c2 = np.random.uniform(-4.5, 4.5, (n_peaks, 2))
        self.w2 = np.random.uniform(0.1, 2.0, n_peaks)
        self.s2 = np.random.uniform(0.2, 1.0, n_peaks)

    def _evaluate(self, X, out, *args, **kwargs):
        f1 = np.zeros(X.shape[0])
        f2 = np.zeros(X.shape[0])

        for i in range(self.n_peaks):
            dist1 = np.sum((X - self.c1[i])**2, axis=1)
            f1 -= self.w1[i] * np.exp(-dist1 / (2 * self.s1[i]**2))

            dist2 = np.sum((X - self.c2[i])**2, axis=1)
            f2 -= self.w2[i] * np.exp(-dist2 / (2 * self.s2[i]**2))

        f1 = f1 - np.min(f1) + 0.1
        f2 = f2 - np.min(f2) + 0.1

        out["F"] = np.column_stack([f1, f2])


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
