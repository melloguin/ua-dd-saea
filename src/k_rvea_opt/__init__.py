"""
K-RVEA-OPT: vectorized and parallelized variant of K-RVEA.

This package contains a from-scratch optimized implementation of K-RVEA
that preserves the algorithm's logic and statistical behavior while
removing Python-level loops, hand-rolling a fast Gaussian Process,
parallelizing the per-objective GP fits/predicts, and JIT-compiling
the non-dominated sort. Results are statistically equivalent to the
reference K-RVEA but not bit-identical (RNG consumption order changes
when vectorizing offspring creation).
"""
