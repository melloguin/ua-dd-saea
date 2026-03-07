import numpy as np
import copy
from src.nsga2.individual import Individual


####################################################################################################################################
####################################################################################################################################
### Seleção por Torneio

def crowded_comparison_operator(ind1, ind2):
    """
    Operador de comparação por crowding
    Retorna True se ind1 deve ser selecionado sobre ind2
    
    Critérios (em ordem de prioridade):
    1. Menor rank de dominancia (um indivíduo domina o outro, melhor front)
    2. Maior crowding distance (mais diverso)
    """
    if ind1.rank != ind2.rank:
        return ind1.rank < ind2.rank
    return ind1.crowding_distance > ind2.crowding_distance


def tournament_selection(population: list, 
			            		 k_tournament: int
			            		) -> Individual:
    """
    Seleção por torneio com K indivíduos:
    
	- Seleciona aleatoriamente K soluções (sem reposição) na população, 
      e encontra a melhor dentre elas a partir do crowded-comparison operator.

	- Grandes valores de K favorecem exploitation (pressão seletiva alta), 
	    pois selecionam mais candidatos para o torneio, a probabilidade de selecionar
	    melhores as soluções da população (que sempre irão vencer o torneio) é alta. 
	  Pequenos valores favorecem exploration, gerando populações mais diversas,
	    com menos convergência para as melhores soluções da população antecessora.

	- Uma excelente estratégia é aumentar o valor de K ao longo da execução,
		  favorecendo exploration da landscape no inicio e exploitation para as 
		  melhores soluções no final. K tem um poder de manipulação direto sobre
		  a pressão seletiva, de forma prática e efetiva.
    
    args:
	- population(list): População de indivíduos
	- k_tournament(int): Número de indivíduos participantes do torneio
        
    returns:
	- Individual: Melhor indivíduo do torneio (cópia profunda)

    """

    # Selecionar k indivíduos aleatoriamente
    tournament_indices = np.random.choice(len(population), size=k_tournament, replace=False)
    tournament_individuals = [population[i] for i in tournament_indices]
    
    # Encontrar o melhor usando comparações sucessivas - o(n)
    best = tournament_individuals[0]
    for individual in tournament_individuals[1:]:
        if crowded_comparison_operator(individual, best):
            best = individual
    
    return copy.deepcopy(best)



####################################################################################################################################
####################################################################################################################################
### Operadores Genéticas (Cruzamento e Mutação)

def simulated_binary_crossover(parent1, parent2, eta=15, prob=0.9, xl=None, xu=None):
    """
    SBX Vetorizado - Implementação fiel à lógica matricial do Pymoo.
    	• Operadores Genéticos
	(Transformações Genéticas) - geração de filhos
	Aplicados sobre o genótipo
		○ Cruzamento/Crossover (troca de material genético entre dois indivíduos)
		○ Mutação (modificação de um único indivíduo com si mesmo)

    """
    # Converter para float para cálculos precisos
    p1 = np.array(parent1.genotype, dtype=float)
    p2 = np.array(parent2.genotype, dtype=float)
    n_var = len(p1)
    
    # Definir limites padrão se não fornecidos
    if xl is None:
        xl = np.zeros(n_var)
    else:
        xl = np.array(xl, dtype=float)
    if xu is None:
        xu = np.ones(n_var)
    else:
        xu = np.array(xu, dtype=float)
    
    # Inicializar filhos como cópia dos pais
    c1 = p1.copy()
    c2 = p2.copy()

    # 1. Verificação de Crossover (Geral)
    # O Pymoo verifica se o cruzamento ocorre para o PAR.
    if np.random.random() > prob:
        return c1.tolist(), c2.tolist()

    # 2. Definição de quais genes serão alterados (Probabilidade por gene = 0.5 é padrão no SBX)
    # O Pymoo geralmente altera todas as variáveis se o crossover ocorrer, 
    # a menos que 'prob_var' seja definido. Vamos assumir alteração em todas para simplificar.
    # Mas para garantir robustez, checamos se os pais são diferentes.
    
    mask = np.abs(p1 - p2) > 1e-14
    
    if not np.any(mask):
        return c1.tolist(), c2.tolist()
    
    # 3. Vetorização: Extrair valores onde o crossover ocorrerá
    y1 = np.minimum(p1[mask], p2[mask])
    y2 = np.maximum(p1[mask], p2[mask])
    
    delta = y2 - y1
    
    # Gerar números aleatórios para TODOS os genes de uma vez (como o Pymoo faz)
    rand = np.random.random(len(delta))
    
    beta = np.zeros(len(delta))
    alpha = np.zeros(len(delta))
    betaq = np.zeros(len(delta))
    
    # --- Cálculo do Beta (Vetorizado) ---
    # Limite Inferior
    xl_masked = xl[mask]
    xu_masked = xu[mask]
    
    beta = 1.0 + (2.0 * (y1 - xl_masked) / delta)
    alpha = 2.0 - np.power(beta, -(eta + 1.0))
    
    # Lógica condicional vetorizada para betaq
    mask_lower = rand <= (1.0 / alpha)
    mask_upper = ~mask_lower
    
    if np.any(mask_lower):
        val = rand[mask_lower] * alpha[mask_lower]
        betaq[mask_lower] = np.power(val, 1.0 / (eta + 1.0))
        
    if np.any(mask_upper):
        val = 1.0 / (2.0 - rand[mask_upper] * alpha[mask_upper])
        betaq[mask_upper] = np.power(val, 1.0 / (eta + 1.0))

    # --- Cálculo dos Filhos ---
    c1_vals = 0.5 * ((y1 + y2) - betaq * delta)
    c2_vals = 0.5 * ((y1 + y2) + betaq * delta)
    
    # --- Passo CRUCIAL: Swap Aleatório ---
    # O Pymoo troca c1 e c2 com 50% de chance por gene para evitar viés
    swap = np.random.random(len(delta)) < 0.5
    
    # Aplicar swap e limites
    final_c1 = np.where(swap, c2_vals, c1_vals)
    final_c2 = np.where(swap, c1_vals, c2_vals)
    
    final_c1 = np.clip(final_c1, xl_masked, xu_masked)
    final_c2 = np.clip(final_c2, xl_masked, xu_masked)
    
    # Inserir valores calculados de volta nos vetores originais
    c1[mask] = final_c1
    c2[mask] = final_c2
    
    return c1.tolist(), c2.tolist()



#################################################################
def polynomial_mutation(individual, eta=20, prob=1/6, xl=None, xu=None):
    """
    Polynomial Mutation (PM) - Implementação idêntica ao pymoo
    Baseado no código fonte: pymoo/operators/mutation/pm.py

    • Operadores Genéticos
	(Transformações Genéticas) - geração de filhos
	Aplicados sobre o genótipo
		○ Cruzamento/Crossover (troca de material genético entre dois indivíduos)
		○ Mutação (modificação de um único indivíduo com si mesmo)

    """
    mutated = list(individual.genotype) if not isinstance(individual.genotype, list) else individual.genotype.copy()
    
    n_var = len(mutated)
    if xl is None:
        xl = np.zeros(n_var)
    else:
        xl = np.array(xl, dtype=float)
    if xu is None:
        xu = np.ones(n_var)
    else:
        xu = np.array(xu, dtype=float)
    
    for i in range(len(mutated)):
        if np.random.random() <= prob:
            x = float(mutated[i])
            xl_i = float(xl[i])
            xu_i = float(xu[i])
            
            delta = xu_i - xl_i
            rand = np.random.random()
            mut_pow = 1.0 / (eta + 1.0)
            
            if rand < 0.5:
                xy = 1.0 - (x - xl_i) / delta
                val = 2.0 * rand + (1.0 - 2.0 * rand) * np.power(xy, eta + 1.0)
                deltaq = np.power(val, mut_pow) - 1.0
            else:
                xy = 1.0 - (xu_i - x) / delta
                val = 2.0 * (1.0 - rand) + 2.0 * (rand - 0.5) * np.power(xy, eta + 1.0)
                deltaq = 1.0 - np.power(val, mut_pow)
            
            x_new = x + deltaq * delta
            x_new = np.clip(x_new, xl_i, xu_i)
            mutated[i] = x_new
    
    return mutated



####################################################################################################################################
####################################################################################################################################
### População Descendente (Offspring Population)

def create_offspring_population(population, config):
    """
    Cria população descendente através de seleção, crossover e mutação
    """
    offspring = []
    n_offspring_needed = len(population)
    
    for _ in range(0, n_offspring_needed, 2):
        # Seleção de pais por torneio
        parent1 = tournament_selection(population, config['k_tournament'])
        parent2 = tournament_selection(population, config['k_tournament'])
        
        # Crossover
        child1_genotype, child2_genotype = simulated_binary_crossover(
            parent1, parent2,
            eta=config['crossover_eta'],
            prob=config['crossover_prob'],
            xl=config['limite_inferior'],
            xu=config['limite_superior']
        )
        
        # Mutação
        child1_genotype = polynomial_mutation(
            Individual(child1_genotype),
            eta=config['mutation_eta'],
            prob=config['mutation_prob'],
            xl=config['limite_inferior'],
            xu=config['limite_superior']
        )
        child2_genotype = polynomial_mutation(
            Individual(child2_genotype),
            eta=config['mutation_eta'],
            prob=config['mutation_prob'],
            xl=config['limite_inferior'],
            xu=config['limite_superior']
        )
        
        # Adiciona filhos à população de descendentes
        offspring.append(Individual(list(child1_genotype) if not isinstance(child1_genotype, list) else child1_genotype))
        if len(offspring) < n_offspring_needed:
            offspring.append(Individual(list(child2_genotype) if not isinstance(child2_genotype, list) else child2_genotype))
    
    
    return offspring
