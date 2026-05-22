import numpy as np
from pymoo.core.problem import Problem as _PymooProblem


def gerar_ruido_raw(dist, params, n_samples):
    """Gera a amostragem bruta baseada no nome da distribuição e seus parâmetros."""
    if dist == 'bimodal':
        regime = np.random.choice([0, 1], size=n_samples, p=params['p'])
        return np.where(regime == 0,
                        np.random.normal(params['mu1'], params['sd1'], n_samples),
                        np.random.normal(params['mu2'], params['sd2'], n_samples))
    elif dist == 'student_t':   return np.random.standard_t(df=params['df'], size=n_samples)
    elif dist == 'lognormal':   return np.random.lognormal(mean=params['mean'], sigma=params['sigma'], size=n_samples)
    elif dist == 'poisson':     return np.random.poisson(lam=params['lam'], size=n_samples)
    elif dist == 'binomial':    return np.random.binomial(n=params['n'], p=params['p'], size=n_samples)
    elif dist == 'geometric':   return np.random.geometric(p=params['p'], size=n_samples)
    elif dist == 'exponential': return np.random.exponential(scale=params['scale'], size=n_samples)
    elif dist == 'uniform':     return np.random.uniform(low=params['low'], high=params['high'], size=n_samples)
    elif dist == 'laplace':     return np.random.laplace(loc=params['loc'], scale=params['scale'], size=n_samples)
    elif dist == 'gamma':       return np.random.gamma(shape=params['shape'], scale=params['scale'], size=n_samples)
    elif dist == 'beta':        return np.random.beta(a=params['a'], b=params['b'], size=n_samples)
    elif dist == 'rayleigh':    return np.random.rayleigh(scale=params['scale'], size=n_samples)
    elif dist == 'weibull':     return np.random.weibull(a=params['a'], size=n_samples)
    elif dist == 'logistic':    return np.random.logistic(loc=params['loc'], scale=params['scale'], size=n_samples)
    elif dist == 'pareto':      return np.random.pareto(a=params['a'], size=n_samples)
    elif dist == 'rademacher':  return np.random.choice([-1.0, 1.0], size=n_samples)
    else:                       return np.random.normal(0, 1, n_samples)


class NoisyProblem(_PymooProblem):
    """Wrap a clean pymoo Problem so that ``_evaluate`` returns noisy fitness.

    Region-based distribution, centred/standardised, scaled by
    ``forca_ruido * mean_fj_global``.
    """

    def __init__(self, base, noise_config, mean_f,
                 n_bins_x1=4, n_bins_x2=4):
        super().__init__(n_var=base.n_var, n_obj=base.n_obj,
                         n_ieq_constr=0, xl=base.xl, xu=base.xu)
        self.base = base
        self.noise_config = noise_config
        self.mean_f = np.asarray(mean_f, dtype=float)
        self.n_bins_x1 = n_bins_x1
        self.n_bins_x2 = n_bins_x2
        self._x1_edges = np.linspace(base.xl[0], base.xu[0], n_bins_x1 + 1)
        self._x2_edges = np.linspace(base.xl[1], base.xu[1], n_bins_x2 + 1)

    def true_pareto_front(self, *args, **kwargs):
        return self.base.true_pareto_front(*args, **kwargs)

    def _assign_regions(self, X):
        """Return 1-indexed region (1..n_bins_x1*n_bins_x2) for each row."""
        b1 = np.clip(np.searchsorted(self._x1_edges, X[:, 0], side='right') - 1,
                      0, self.n_bins_x1 - 1)
        b2 = np.clip(np.searchsorted(self._x2_edges, X[:, 1], side='right') - 1,
                      0, self.n_bins_x2 - 1)
        return b1 * self.n_bins_x2 + b2 + 1

    def _evaluate(self, X, out, *args, **kwargs):
        self.base._evaluate(X, out, *args, **kwargs)
        F_clean = out['F'].copy()
        regions = self._assign_regions(X)

        for reg in np.unique(regions):
            cfg = self.noise_config.get(int(reg))
            if cfg is None:
                continue
            forca = cfg.get('forca_ruido', 0.0)
            if forca == 0:
                continue

            mask = regions == reg
            n = int(mask.sum())
            raw = gerar_ruido_raw(cfg['dist'], cfg['params'], n)
            centered = raw - raw.mean()
            std_val = centered.std()
            if std_val == 0:
                std_val = 1e-6
            std_noise = centered / std_val
            target_mean = cfg.get('target_mean', 0.0)

            for j in range(F_clean.shape[1]):
                if j > 0:
                    np.random.shuffle(std_noise)
                scale_fj = forca * self.mean_f[j]
                out['F'][mask, j] = F_clean[mask, j] + std_noise * scale_fj + target_mean
