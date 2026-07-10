class Individual:
    """Representa um indivíduo na população do DR-NSGA-II"""
    def __init__(self, genotype):
        self.genotype = genotype
        self.fitness = None           # [f1_predicted, f2_predicted]
        self.adjusted_fitness = None  # [f1_adj, f2_adj] = predicted + z * std
        self.rank = None
        self.rank_ori = None          # rank from original fitness NDS
        self.rank_adj = None          # rank from adjusted fitness NDS
        self.avg_rank = None          # (rank_ori + rank_adj) / 2
        self.crowding_distance = 0.0
        self.dominated_solutions = []
        self.domination_count = 0
        self.mapped_point = None
        self.mapping_success = False

    def __repr__(self):
        return f"Individual({self.genotype}, fitness={self.fitness}, avg_rank={self.avg_rank})"
