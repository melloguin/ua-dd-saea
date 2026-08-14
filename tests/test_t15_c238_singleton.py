# -*- coding: utf-8 -*-
"""[T15.9/DEC-8] O fix do front singleton no Infill_EIM do c238 — controles.

O bug (laudo `handoff/D0-LAUDO-C238-BADSUBSCRIPT.md`): com `num_pareto==1` o
`min(reshape(...))` SEM dimensão colapsava a fitness a um ESCALAR (min de
vetor-linha reduz ao longo da linha) e o `Optimizer_GA:17` morria em
`MATLAB:badsubscript` — 28/28 células falhadas tinham `n_front1==1`; 0/617
células ok. O fix (autor, DEC-8): `,[],1` explicita a dimensão.

Controles deste arquivo (MATLAB real, kriging treinado de verdade):
  1. COMPORTAMENTO NOVO: front singleton ⇒ y é vetor num_x×1 (o velho dava 1×1).
  2. O DELTA, DEMONSTRADO: a expressão ANTIGA (sem `,[],1`), computada inline
     sobre a MESMA matriz EIM, devolve ESCALAR no singleton — o bug preservado
     como evidência executável, sem depender de checkout antigo.
  3. IDENTIDADE: com front ≥2, expressão antiga ≡ nova (bit-exato) — é a prova
     de que as 617 células ok não mudam e nenhum re-run delas é necessário.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests import TIMEOUT_MATLAB

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _RAIZ)


def _matlab_bin():
    cand = os.environ.get("UA_DD_SAEA_MATLAB")
    if cand and os.path.exists(cand):
        return cand
    cand = "/Applications/MATLAB_R2025a.app/bin/matlab"
    return cand if os.path.exists(cand) else shutil.which("matlab")


MATLAB = _matlab_bin()

_SNIPPET = r"""
addpath('__C238__');
rng(0,'twister');
n = 8; d = 2; nx = 5;
X  = lhsdesign(n, d);
Y1 = sum(X.^2, 2);  Y2 = sum((X-1).^2, 2);
lb = zeros(1,d); ub = ones(1,d);
th0 = ones(1,d); thl = 0.001*ones(1,d); thu = 1000*ones(1,d);
kr = {GP_Train(X, Y1, lb, ub, th0, thl, thu), GP_Train(X, Y2, lb, ub, th0, thl, thu)};
xs = rand(nx, d);

% ---- (1) front SINGLETON: o fix devolve vetor nx-por-1 ----
[y1, ~, ~, ~] = Infill_EIM(xs, kr, [0.1 0.9], 'Euclidean');
fprintf('SINGLETON_numel=%d esperado=%d\n', numel(y1), nx);

% ---- (2) o DELTA: a expressao ANTIGA no mesmo cenario da escalar ----
np = 1; u = zeros(nx,2); s = zeros(nx,2);
for ii = 1:2, [u(:,ii), s(:,ii)] = GP_Predict(xs, kr{ii}); end
um = repelem(u, np, 1); sm = repelem(s, np, 1);
fm = repmat([0.1 0.9], nx, 1);
EIM = (fm-um).*normcdf((fm-um)./sm) + sm.*normpdf((fm-um)./sm);
EIM(isnan(EIM)) = 0;
y_velho = min(reshape(sqrt(sum(EIM.^2,2)),[np,nx]))';
fprintf('VELHO_SINGLETON_numel=%d\n', numel(y_velho));

% ---- (3) IDENTIDADE com front >= 2 (todas as 3 variantes) ----
front3 = [0.1 0.9; 0.5 0.5; 0.9 0.1];
iguais = zeros(1,3); crits = {'Euclidean','Maximin','Hypervolume'};
for c = 1:3
    [yn, ~, ~, ~] = Infill_EIM(xs, kr, front3, crits{c});
    np3 = size(front3,1); num_obj = 2;
    um3 = repelem(u, np3, 1); sm3 = repelem(s, np3, 1);
    fm3 = repmat(front3, nx, 1);
    E3 = (fm3-um3).*normcdf((fm3-um3)./sm3) + sm3.*normpdf((fm3-um3)./sm3);
    E3(isnan(E3)) = 0;
    switch crits{c}
        case 'Euclidean'
            yv = min(reshape(sqrt(sum(E3.^2,2)),[np3,nx]))';
        case 'Maximin'
            yv = min(reshape(max(E3,[],2),[np3,nx]))';
        case 'Hypervolume'
            rp = 1.1*ones(1,num_obj);
            yv = min(reshape(prod(rp-fm3+E3,2)-prod(rp-fm3,2),[np3,nx]))';
    end
    iguais(c) = isequal(yn, yv);
end
fprintf('IDENTIDADE_p3=%d%d%d\n', iguais(1), iguais(2), iguais(3));
"""


@unittest.skipUnless(MATLAB, "MATLAB indisponível nesta máquina")
class TestC238FrontSingleton(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        c238 = os.path.join(_RAIZ, "algorithms", "c238_EIM")
        with tempfile.TemporaryDirectory() as td:
            script = os.path.join(td, "probe_c238.m")
            with open(script, "w") as fh:
                fh.write(_SNIPPET.replace("__C238__", c238))
            p = subprocess.run(
                [MATLAB, "-batch", f"run('{script}')"],
                capture_output=True, text=True, timeout=TIMEOUT_MATLAB)
            cls.out = p.stdout + p.stderr
            cls.rc = p.returncode

    def test_singleton_devolve_vetor(self):
        self.assertIn("SINGLETON_numel=5 esperado=5", self.out, self.out[-800:])

    def test_delta_expressao_antiga_escalar(self):
        # a evidência executável do bug: mesma matriz, semântica velha ⇒ 1×1
        self.assertIn("VELHO_SINGLETON_numel=1", self.out, self.out[-800:])

    def test_identidade_para_front_maior(self):
        # 617 células ok bit-exatas: antiga ≡ nova nas 3 variantes com p≥2
        self.assertIn("IDENTIDADE_p3=111", self.out, self.out[-800:])

    def test_processo_fechou_limpo(self):
        self.assertEqual(self.rc, 0, self.out[-800:])


if __name__ == "__main__":
    unittest.main()
