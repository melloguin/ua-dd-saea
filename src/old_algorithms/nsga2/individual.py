class Individual:
    """Representa um indivíduo na população"""
    def __init__(self, genotype):
        self.genotype = genotype  # Lista de 6 dígitos
        self.fitness = None  # [f1, f2]
        self.rank = None  # Rank de dominância
        self.crowding_distance = 0.0
        self.dominated_solutions = []  # Sp: lista de soluções que este indivíduo domina
        self.domination_count = 0  # np: número de soluções que dominam este indivíduo
    
    def __repr__(self):
        return f"Individual({self.genotype}, fitness={self.fitness}, rank={self.rank})" 