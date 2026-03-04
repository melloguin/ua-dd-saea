class Individual:
    """Representa um indivíduo na população"""
    def __init__(self, genotype, pop_size = None):
        # atributos GA
        self.genotype = genotype  # Lista de 6 dígitos
        self.fitness = None  # [f1, f2]
        # atributos NSGA-II
        self.rank = pop_size  # Rank de dominância (usado pelo fast_non_dominated_sort)
        self.dominated_solutions = []  # Sp: lista de soluções que este indivíduo domina
        self.domination_count = 0  # np: número de soluções que dominam este indivíduo
        # atributos UA-SA-NSGA-II
        self.ua_rank = pop_size  # UA-rank: média dos ranks das n_simulations
        self.ua_rank_std = pop_size  # Desvio padrão do UA-rank
        self.ua_simulation_ranks = []  # Lista com ranks de todas as simulações UA
        self.ds_niching_distance = 0
    
    def __repr__(self):
        return (f"Individual = {self.genotype}, "
                f"fitness = {self.fitness}, "
                f"rank = {self.rank}, "
                f"ds_niching_distance = {self.ds_niching_distance}, "
                f"ua_rank = {self.ua_rank}, "
                f"ua_rank_std = {self.ua_rank_std}, "
                f"ua_simulation_ranks = {self.ua_simulation_ranks}")