class Individual:
    """Representa um indivíduo na população"""
    def __init__(self, genotype, pop_size = None):
        self.genotype = genotype  # Lista de 6 dígitos
        self.fitness = None  # [f1, f2]
        self.rank = pop_size  # Rank de dominância
        self.rank_std = pop_size  # Desvio padrão do rank
        self.ua_rank = []  # Ranks de dominância nas s simulações
        self.dominated_solutions = []  # Sp: lista de soluções que este indivíduo domina
        self.domination_count = 0  # np: número de soluções que dominam este indivíduo
    
    def __repr__(self):
        return f"Individual({self.genotype}, fitness={self.fitness}, rank={self.rank}, ua_rank={self.ua_rank}, rank_std={self.rank_std})"