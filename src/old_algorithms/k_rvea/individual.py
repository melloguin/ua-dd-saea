class Individual:
    """Representa um indivíduo na população do K-RVEA (RVEA offline)"""
    def __init__(self, genotype):
        self.genotype = genotype
        self.fitness = None
        self.rank = None
        self.crowding_distance = 0.0
        self.dominated_solutions = []
        self.domination_count = 0
        self.mapped_point = None
        self.mapping_success = False

    def __repr__(self):
        return f"Individual({self.genotype}, fitness={self.fitness}, rank={self.rank})"
