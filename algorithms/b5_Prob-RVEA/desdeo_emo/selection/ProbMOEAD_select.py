import numpy as np
from typing import List
from desdeo_emo.selection.SelectionBase import SelectionBase
from desdeo_emo.population.Population import Population
from desdeo_emo.othertools.ReferenceVectors import ReferenceVectors
from desdeo_emo.othertools.ProbabilityWrong import Probability_wrong

n_samples = 1000

# ── [T11-A3 / I-05 · anchor b5-pwrong-stats] TELEMETRIA READ-ONLY ────────────
# `p_wrong_stats` era o UNICO campo DI-10 com 0/N em todo o estudo: ausente em
# 30.165/30.165 eventos do b5 (controle: b1 3/3, b4 3/3, c217 3/3, c238 1/1,
# c122 2/2, c149 2/2, e81 2/2, c311 2/2, e103 2/2, e74 2/2, nsga3 3/3, moead
# 3/3, nsga2 2/2, smsemoa 2/2 — zeros absolutos SO em b5m, b5r e moead_media).
# Sem ele, a cadeia A8 — o congelamento (`adapt` zera `values` -> PBI NaN ->
# P_wrong identicamente 0,0 -> ZERO substituicoes) — fica INFERIDA em 4.050
# celulas, e o congelamento PARCIAL (8 celulas do piso, previsto por face do
# lattice 8/8) fica invisivel.
#
# Este acumulador so LE `probabilities` e `selection`, que a decisao ja
# computou (`compute_probability_wrong_MC`, abaixo). NAO consome RNG, NAO
# altera retorno, NAO entra em ramo de decisao: o criterio DI-12.1 e
# comportamento, nao pureza textual. Custo medido pelo plano F5: 0,022 s por run
# acumulando (0,0008% de `tempo_busca_s` mediano = 2.868,2 s).
#
# O runner LE e ZERA por run (`b5_prob.py` / `piso_offline.py`); a chave e o
# `gen_count` da populacao, para o replay pos-laco casar geracao a geracao.
P_WRONG_STATS = {}


def _pw_registra(gen, probabilities, n_substituicoes):
    """[I-05] Acumula (min, mediana, max, n) de P_wrong da geracao. Nunca levanta."""
    try:
        import numpy as _np
        pr = _np.asarray(probabilities, dtype=float).ravel()
        if pr.size == 0:
            return
        P_WRONG_STATS.setdefault(int(gen), []).append({
            "min": float(_np.min(pr)), "med": float(_np.median(pr)),
            "max": float(_np.max(pr)), "n_vizinhos": int(pr.size),
            "n_substituicoes": int(n_substituicoes),
            "n_nan": int(_np.count_nonzero(~_np.isfinite(pr))),
        })
    except Exception:
        pass


class ProbMOEAD_select(SelectionBase):
    """The MOEAD selection operator. 

    Parameters
    ----------
    pop : Population
        The population of individuals
    SF_type : str
        The scalarizing function employed to evaluate the solutions

    """
    def __init__(
        self, pop: Population, SF_type: str
    ):
	 # initialize
        self.SF_type = SF_type

    def do(self, pop: Population, vectors: ReferenceVectors, ideal_point, current_neighborhood, offspring_fx, offspring_unc, theta_adaptive) -> List[int]:
        """Select the individuals that are kept in the neighborhood.

        Parameters
        ----------
        pop : Population
            The current population.
        vectors : ReferenceVectors
            Class instance containing reference vectors.
        ideal_point
            Ideal vector found so far
        current_neighborhood
            Neighborhood to be updated
        offspring_fx
            Offspring solution to be compared with the rest of the neighborhood

        Returns
        -------
        List[int]
            List of indices of the selected individuals
        """
        # Compute the value of the SF for each neighbor
        num_neighbors               = len(current_neighborhood)
        current_population          = pop.objectives[current_neighborhood,:]
        current_uncertainty          = pop.uncertainity[current_neighborhood,:]
        current_reference_vectors   = vectors.values[current_neighborhood,:]
        offspring_population        = np.array([offspring_fx]*num_neighbors)
        offspring_uncertainty       = np.array([offspring_unc]*num_neighbors)
        ideal_point_matrix          = np.array([ideal_point]*num_neighbors)
        theta_adaptive_matrix       = np.array([theta_adaptive]*num_neighbors)
        pwrong_current = Probability_wrong(mean_values=current_population, stddev_values=current_uncertainty, n_samples=n_samples)
        pwrong_current.vect_sample_f()

        pwrong_offspring = Probability_wrong(mean_values=offspring_population.reshape(-1,pop.problem.n_of_objectives), stddev_values=offspring_uncertainty.reshape(-1,pop.problem.n_of_objectives), n_samples=n_samples)
        pwrong_offspring.vect_sample_f()

        values_SF_current = self._evaluate_SF(current_population, current_reference_vectors, ideal_point_matrix, pwrong_current, theta_adaptive_matrix)
        values_SF_offspring = self._evaluate_SF(offspring_population, current_reference_vectors, ideal_point_matrix, pwrong_offspring, theta_adaptive_matrix)

        ##### KDE here and then compute probability
        # [R3-b5 / anchor b5-mode72-kde] Bloco KDE MORTO + plt_density CRASHY
        # comentado. As linhas 66-73 computavam pdf/ecdf que a decisao (linha
        # abaixo, compute_probability_wrong_MC) NUNCA usa; a linha 75
        # (plt_density) salva um PDF por vizinho sob usetex e da reshape(20,...)
        # -> ValueError se n_neighbors != 20 (aqui, e sempre, e 20, mas o custo
        # de I/O em 40k FE inviabiliza a busca). A decisao usa MC (mode 72).
        # pwrong_current.pdf_list = {}
        # pwrong_current.ecdf_list = {}
        # pwrong_offspring.pdf_list = {}
        # pwrong_offspring.ecdf_list = {}
        # values_SF_offspring_temp = np.asarray([values_SF_offspring])
        # values_SF_current_temp = np.asarray([values_SF_current])
        # pwrong_offspring.compute_pdf(values_SF_offspring_temp.reshape(num_neighbors,1,n_samples))
        # pwrong_current.compute_pdf(values_SF_current_temp.reshape(num_neighbors,1,n_samples))
        # #pwrong_offspring.plt_density(values_SF_offspring.reshape(20,1,n_samples))
        # pwrong_current.plt_density(values_SF_current_temp.reshape(20,1,n_samples))
        probabilities = np.zeros(num_neighbors)
        for i in range(num_neighbors):
            # cheaper MC samples comparison
            probabilities[i]=pwrong_current.compute_probability_wrong_MC(values_SF_current[i], values_SF_offspring[i])
            #probabilities[i]=pwrong_current.compute_probability_wrong_PBI(pwrong_offspring, index=i)
        # Compare the offspring with the individuals in the neighborhood 
        # and replace the ones which are outperformed by it if P_{wrong}>0.5
        selection = np.where(probabilities>0.5)[0]
        # [T11-A3/I-05 · anchor b5-pwrong-stats] telemetria READ-ONLY (a decisao
        # acima ja esta tomada; nada abaixo a le)
        _pw_registra(getattr(pop, "gen_count", -1), probabilities, len(selection))

        # Considering mean
        # selection2 = np.where(np.mean(values_SF_offspring, axis=1) < np.mean(values_SF_current, axis=1))[0]
        print("*****Selection:",selection)

        return current_neighborhood[selection]


    def tchebycheff(self, objective_values:np.ndarray, weights:np.ndarray, ideal_point:np.ndarray):
        feval   = np.abs(objective_values - ideal_point) * weights
        max_fun = np.max(feval)
        return max_fun

    def weighted_sum(self, objective_values, weights):
        feval   = np.sum(objective_values * weights)
        return feval

    def pbi(self, objective_values, weights, ideal_point, pwrong_f_samples, theta):

        norm_weights    = np.linalg.norm(weights)
        weights         = weights/norm_weights
        
        #fx_a            = objective_values - ideal_point
        fx_a            = pwrong_f_samples - ideal_point.reshape(-1,1)
        
        #d1              = np.inner(fx_a, weights)
        
        d1               = np.sum(np.transpose(fx_a)* np.tile(weights,(n_samples,1)), axis=1)
        
        #fx_b            = objective_values - (ideal_point + d1 * weights)

        fx_b             = np.transpose(pwrong_f_samples) - (np.tile(ideal_point,(n_samples,1)) + np.reshape(d1,(-1,1)) * np.tile(weights,(n_samples,1)))

        #d2              = np.linalg.norm(fx_b)
        
        d2               = np.linalg.norm(fx_b, axis=1)

        fvalue          = d1 + theta * d2

        return fvalue


    def _evaluate_SF(self, neighborhood, weights, ideal_point, pwrong, theta_adaptive):
        if self.SF_type == "TCH":
            SF_values = np.array(list(map(self.tchebycheff, neighborhood, weights, ideal_point)))
            return SF_values
        elif self.SF_type == "PBI":
            SF_values = np.array(list(map(self.pbi, neighborhood, weights, ideal_point, pwrong.f_samples, theta_adaptive)))
            return SF_values
        elif self.SF_type == "WS":
            SF_values = np.array(list(map(self.weighted_sum, neighborhood, weights)))
            return SF_values
        else:
            return []



    

    

    
    

