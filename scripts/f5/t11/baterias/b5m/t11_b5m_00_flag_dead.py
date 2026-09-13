"""Prova ISOLADA (sem rodar celula): o caminho de atributo do
`flag_vetores_degenerados` (src/b5_prob.py:118) nao existe.
Roda no env_b5 com o desdeo VENDORIZADO root-first."""
import sys, os
import typing as _t, typing_extensions as _te
_t.Literal = getattr(_t,"Literal",_te.Literal)
import types as _ty
_st=_ty.ModuleType("pygmo"); _st.fast_non_dominated_sorting=lambda *a,**k:None
sys.modules.setdefault("pygmo",_st)
V = "/Users/gmello/Documents/python_repos/mestrado/ua-dd-saea/algorithms/b5_Prob-RVEA"
sys.path.insert(0, V)
import desdeo_problem, desdeo_emo
from desdeo_problem.Problem import DataProblem
from desdeo_emo.population.Population import Population
from desdeo_emo.EAs.ProbMOEAD import ProbMOEAD
print("desdeo_problem de:", desdeo_problem.__file__)
print("DataProblem tem 'reference_vectors' ?      ", hasattr(DataProblem, "reference_vectors"))
print("Population  tem 'reference_vectors' ?      ", hasattr(Population, "reference_vectors"))
print("'reference_vectors' no __init__ de Population:",
      "reference_vectors" in open(os.path.join(V,"desdeo_emo/population/Population.py")).read())
import inspect
src = inspect.getsource(DataProblem)
print("ocorrencias de 'reference_vectors' no fonte de DataProblem:", src.count("reference_vectors"))
# o caminho CORRETO
from desdeo_emo.EAs.BaseEA import BaseDecompositionEA
b = inspect.getsource(BaseDecompositionEA)
print("BaseDecompositionEA seta self.reference_vectors:", "self.reference_vectors = ReferenceVectors" in b)
