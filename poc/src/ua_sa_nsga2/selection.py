import numpy as np
from joblib import Parallel, delayed


####################################################################################################################################
####################################################################################################################################
### Fast non-dominated sort

def dominates(fitness_solucao1, 
              fitness_solucao2,
              maximize = False):
    """
    Verifica se fitness1 domina fitness2 (minimização)
    Domina se é melhor ou igual em todos os objetivos e estritamente melhor em pelo menos um

    args:
        fitness1 (list[float, float]): 
    """
    better_in_any = False
    # percorre fitness a fitness das 2 solucoes (s1 e s2) 
    for f1, f2 in zip(fitness_solucao1, fitness_solucao2):
        # se maximização, inverte o sinal dos fitness
        if maximize:
            f1, f2 = -f1, -f2
        # e sinaliza se a 2a solucao é pior em algum objetivo (indica que s1 não domina s2)
        if f1 > f2:  # Pior em algum objetivo
            return False
        if f1 < f2:  # Melhor em algum objetivo
            better_in_any = True

    return better_in_any



def fast_non_dominated_sort(population, config):
    """
    Implementação rápida da ordenação não-dominada (Fast Non-Dominated Sort)
    Complexidade: O(MN²) onde M é número de objetivos e N é tamanho da população
    
    Retorna: lista de fronts, onde cada front é uma lista de indivíduos

	• Abordagem NSGA-II
		- I. Comparar cada solução n-ésima, com as outras N-1 soluções, e capturar 2 variáveis:
			* Sp: lista de soluções que n domina
			* np: quantidade de soluções que dominam n
            * flag primeiro front se np = 0
		    Esse processo tem complexidade O(MN²) - pois realiza n * n-1 comparações

        - II. Encontra fronts de dominancia
            - Percorre os elementos do front 1, avaliando seus Sp, e subtraindo 1 do np de cada elemento encontrado em cada Sp
                * O mesmo elemento pode ser encontrado mais de uma vez, pois é dominado por mais de um elemento do conjunto 1, nesse caso, ele tem seu np subtraído também mais de uma vez.
                * Os elementos que tiverem np = 0 no final desse processo, serão alocados para o grupo 2 (dominados apenas por 1)
            - Repete o processo para os elementos dominados pelo conjunto 1 para achar o conjunto 2, e assim por diante até finalizar a ordenação não-dominada
	
    """
    # Inicializar estruturas
    fronts = [[]]  # Lista de fronts, começando com o primeiro front
    
    # I. Para cada indivíduo p, calcular np e Sp (e identifica primeiro front)
    for individual_p in population:

        # inicializa np e Sp vazios
        individual_p.dominated_solutions = []
        individual_p.domination_count = 0
        
        # compara p com cada outra n-1 solução
        for individual_q in population:
            if individual_p is individual_q:
                continue
            # se p domina q, adicionar q à lista Sp
            if dominates(individual_p.fitness, individual_q.fitness, config['maximize']):
                individual_p.dominated_solutions.append(individual_q)
            # se q domina p, incrementar np
            elif dominates(individual_q.fitness, individual_p.fitness, config['maximize']):
                individual_p.domination_count += 1
        
        # identifica primeiro front
        if individual_p.domination_count == 0:
            individual_p.rank = 1
            fronts[0].append(individual_p)
    

    # II. Encontrar os fronts de dominancia subsequentes
    i = 0

    while len(fronts[i]) > 0:
        next_front = []
        
        for individual_p in fronts[i]:
            # Para cada solução q dominada por p
            for individual_q in individual_p.dominated_solutions:
                individual_q.domination_count -= 1
                
                # Se np de q se tornou 0, q pertence ao próximo front
                if individual_q.domination_count == 0:
                    individual_q.rank = i + 2
                    next_front.append(individual_q)
        
        fronts.append(next_front)
        i += 1
    
    # Remover o último front vazio
    if len(fronts[-1]) == 0:
        fronts.pop()
    

    return fronts


def _process_single_simulation(s, original_fitness_list, config):
    """
    Processa uma única simulação para uncertainty-aware ranking
    
    Args:
        s: índice da simulação
        original_fitness_list: lista com os fitness originais [fitness_ind0, fitness_ind1, ...]
        config: configurações do algoritmo
        
    Returns:
        list: lista de ranks [rank_ind0, rank_ind1, ...] nesta simulação
    """
    # Cria uma cópia temporária da população para esta simulação
    # usando uma classe simples para evitar modificar os objetos originais
    from types import SimpleNamespace
    
    temp_population = []
    for idx, original_fitness in enumerate(original_fitness_list):
        # Cria um objeto temporário com o fitness da s-ésima simulação
        temp_ind = SimpleNamespace()
        temp_ind.fitness = [
            original_fitness[0][s],  # s-ésimo valor do objetivo 1
            original_fitness[1][s]   # s-ésimo valor do objetivo 2
        ]
        temp_ind.dominated_solutions = []
        temp_ind.domination_count = 0
        temp_ind.rank = 0
        temp_ind.idx = idx  # guarda o índice original
        temp_population.append(temp_ind)
    
    # Realiza fast non-dominated sort com o fitness da s-ésima simulação
    fronts = fast_non_dominated_sort(temp_population, config)
    
    # Coleta o rank de cada indivíduo nesta simulação, ordenado por índice
    simulation_ranks = [0] * len(original_fitness_list)
    for individual in temp_population:
        simulation_ranks[individual.idx] = individual.rank
    
    return simulation_ranks


def uncertainty_aware_ranking(combined_population, config, ua_rank_stat=None):
    '''
    Uncertainty-Aware Ranking using Multiple Simulations (Paralelizado com joblib)

        - Salva os fitness originais (listas completas)
        - Realiza fast non-dominated sort para cada simulação (em paralelo)
        - Coleta o rank de cada indivíduo nesta simulação em ua_simulation_ranks
        - Restaura os fitness originais e calcula:
            * ua_rank: estatística dos ranks das n_simulations (default: média)
            * ua_rank_std: média dos desvios positivos acima da estatística
    
    Args:
        combined_population: população combinada Pt + Qt
        config: configurações do algoritmo
        ua_rank_stat: função ou string para calcular ua_rank a partir dos ranks
                      - None ou 'mean': usa np.mean (default)
                      - 'median' ou 'percentile_50': usa percentil 50
                      - 'percentile_X': usa percentil X (ex: 'percentile_40')
                      - função callable: aplica a função diretamente
    '''
    
    # Define a função de estatística a ser usada
    if ua_rank_stat is None or ua_rank_stat == 'mean':
        stat_func = np.mean
    elif ua_rank_stat == 'median' or ua_rank_stat == 'percentile_50':
        stat_func = np.median
    elif isinstance(ua_rank_stat, str) and ua_rank_stat.startswith('percentile_'):
        # Extrai o valor do percentil (ex: 'percentile_40' -> 40)
        percentile_value = float(ua_rank_stat.split('_')[1])
        stat_func = lambda x: np.percentile(x, percentile_value)
    elif callable(ua_rank_stat):
        stat_func = ua_rank_stat
    else:
        raise ValueError(f"ua_rank_stat inválido: {ua_rank_stat}. Use 'mean', 'median', 'percentile_X' ou uma função.")
    
    # Salva os fitness originais (listas completas) em uma lista indexada
    original_fitness_list = [individual.fitness for individual in combined_population]

    # Realiza fast non-dominated sort para cada simulação (em paralelo)
    # n_jobs=-1 usa todos os cores disponíveis
    # Agora funciona com multiprocessing pois não depende de id()
    all_simulation_ranks = Parallel(n_jobs=-1)(
        delayed(_process_single_simulation)(s, original_fitness_list, config)
        for s in range(config['n_simulations'])
    )
    
    # Coleta os ranks de todas as simulações para cada indivíduo
    # all_simulation_ranks é uma lista de listas: [[ranks_sim0], [ranks_sim1], ...]
    # Precisamos transpor para: [[ranks_ind0], [ranks_ind1], ...]
    for idx, individual in enumerate(combined_population):
        individual.ua_simulation_ranks = [simulation_ranks[idx] for simulation_ranks in all_simulation_ranks]

    # Restaura os fitness originais e calcula estatísticas dos ranks
    for idx, individual in enumerate(combined_population):
        # Restaura os fitness originais
        individual.fitness = original_fitness_list[idx]
        # Calcula a estatística dos ranks obtidos nas n_simulations
        individual.ua_rank = round(stat_func(individual.ua_simulation_ranks), 5)
        # Calcula a métrica de dispersão: média dos desvios positivos acima da estatística
        ua_rank_value = individual.ua_rank
        positive_deviations = np.maximum(0, np.array(individual.ua_simulation_ranks) - ua_rank_value)
        individual.ua_rank_std = round(np.mean(positive_deviations), 5)
        # Limpa os ua_simulation_ranks
        individual.ua_simulation_ranks = []


####################################################################################################################################
####################################################################################################################################
### Decision Space Niching

def calculate_distance_matrix(population, weights):
    """
    Calcula a matriz de distâncias euclidianas ponderadas entre os genótipos de todos os indivíduos.
    
    Args:
        population: lista de indivíduos
        weights: lista de pesos para cada gene (pesos_ds_niching)
        
    Returns:
        numpy array NxN com as distâncias entre todos os pares de indivíduos
    """
    n = len(population)
    distance_matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i + 1, n):
            # Calcula distância euclidiana ponderada
            genotype_i = np.array(population[i].genotype)
            genotype_j = np.array(population[j].genotype)
            weights_array = np.array(weights)
            
            # Distância: sqrt(sum(peso(d) * (xi,d - xj,d)^2))
            dist = np.sqrt(np.sum(weights_array * (genotype_i - genotype_j) ** 2))
            
            distance_matrix[i][j] = dist
            distance_matrix[j][i] = dist  # Matriz simétrica
    
    return distance_matrix


def calculate_ds_niching_distance(population, distance_matrix, selected_indices=None):
    """
    Calcula a ds-niching-distance para cada indivíduo.
    
    Args:
        population: lista de indivíduos
        distance_matrix: matriz NxN de distâncias euclidianas
        selected_indices: se None, calcula média de distâncias vs todos;
                         se fornecido, calcula média de distâncias vs apenas os selecionados
    
    Returns:
        None (atualiza o atributo ds_niching_distance de cada indivíduo)
    """
    n = len(population)
    
    for i in range(n):
        if selected_indices is None:
            # Média das distâncias para todos os outros indivíduos
            distances = [distance_matrix[i][j] for j in range(n) if i != j]
        else:
            # Média das distâncias apenas para os indivíduos já selecionados
            distances = [distance_matrix[i][j] for j in selected_indices]
        
        if len(distances) > 0:
            population[i].ds_niching_distance = np.mean(distances)
        else:
            population[i].ds_niching_distance = 0.0


def select_rank1_iteratively(combined_population, config, distance_matrix, generation):
    """
    Seleciona indivíduos iterativamente usando fast_non_dominated_sort com critérios:
    - ua_rank (menor = melhor)
    - alpha_rank_distance (menor = melhor) - combinação ponderada de ua_rank e ds_niching_distance
    
    A métrica alpha_rank_distance equilibra exploração (diversidade) e convergência:
    - alpha = 1.0 (início): prioriza ds_niching_distance (exploração/diversidade)
    - alpha = 0.0 (fim): prioriza ua_rank (convergência)
    - Transição linear entre gerações
    
    Processo iterativo:
    1. Calcula ds-niching-distance vs todos
    2. Normaliza ua_rank e ds_niching_distance (min-max)
    3. Calcula alpha_rank_distance = alpha * norm_ds + (1-alpha) * norm_ua
    4. Seleciona rank 1 baseado em [ua_rank, alpha_rank_distance]
    5. Recalcula ds-niching-distance dos candidatos vs selecionados
    6. Repete até preencher população ou rank 1 não caber todo
    
    Args:
        combined_population: população combinada Pt + Qt
        config: configurações do algoritmo
        distance_matrix: matriz de distâncias euclidianas
        generation: geração atual (0-indexed)
        
    Returns:
        next_population: população selecionada
    """
    n = len(combined_population)
    population_size = config['population_size']
    
    # Índices dos indivíduos na combined_population (para rastrear)
    all_indices = set(range(n))
    selected_indices = []
    next_population = []
    
    # Passo 2: Calcula ds-niching-distance inicial (média vs todos)
    calculate_ds_niching_distance(combined_population, distance_matrix, selected_indices=None)
    
    # Loop iterativo: máximo de population_size iterações
    for iteration in range(population_size):
        
        # Verifica se já preencheu a população
        if len(next_population) >= population_size:
            break
        
        # Identifica candidatos (ainda não selecionados)
        candidate_indices = list(all_indices - set(selected_indices))
        if len(candidate_indices) == 0:
            break
            
        candidates = [combined_population[i] for i in candidate_indices]
        
        # Passo 3 (primeira vez) / Passo 5 (iterações seguintes):
        # Normaliza ua_rank e ds_niching_distance dos candidatos (min-max)
        ua_ranks = [c.ua_rank for c in candidates]
        ds_distances = [c.ds_niching_distance for c in candidates]
        
        ua_min, ua_max = min(ua_ranks), max(ua_ranks)
        ds_min, ds_max = min(ds_distances), max(ds_distances)
        
        # Pega alpha da geração atual
        alpha = config['alpha_exploration_rank_distance'][generation]
        
        # Calcula alpha_rank_distance para cada candidato
        for candidate in candidates:
            # Normaliza ua_rank (min-max)
            if ua_max - ua_min > 0:
                norm_ua = (candidate.ua_rank - ua_min) / (ua_max - ua_min)
            else:
                norm_ua = 0.0
            
            # Normaliza ds_niching_distance (min-max) e inverte (1 - norm)
            # Invertemos porque queremos MAXIMIZAR ds_niching_distance
            if ds_max - ds_min > 0:
                norm_ds = 1.0 - (candidate.ds_niching_distance - ds_min) / (ds_max - ds_min)
            else:
                norm_ds = 0.0
            
            # Calcula alpha_rank_distance: combinação ponderada
            # alpha=1.0: prioriza diversidade (norm_ds), alpha=0.0: prioriza convergência (norm_ua)
            candidate.alpha_rank_distance = alpha * norm_ds + (1 - alpha) * norm_ua
        
        # Cria configuração temporária para fast_non_dominated_sort
        # Usa ua_rank como objetivo 1 (minimizar) e alpha_rank_distance como objetivo 2 (minimizar)
        temp_config = config.copy()
        temp_config['maximize'] = False
        
        # Prepara fitness temporário: [ua_rank, alpha_rank_distance]
        for candidate in candidates:
            candidate.temp_fitness = candidate.fitness  # Salva fitness original
            candidate.fitness = [candidate.ua_rank, candidate.alpha_rank_distance]
        
        # Fast non-dominated sort nos candidatos
        fronts = fast_non_dominated_sort(candidates, temp_config)
        
        # Restaura fitness original
        for candidate in candidates:
            candidate.fitness = candidate.temp_fitness
            delattr(candidate, 'temp_fitness')
        
        # Pega rank 1
        rank1_candidates = fronts[0] if len(fronts) > 0 else []
        
        # Verifica se rank 1 cabe todo na população
        if len(next_population) + len(rank1_candidates) <= population_size:
            # Passo 3/5: Seleciona todos do rank 1
            for candidate in rank1_candidates:
                # Encontra índice original
                idx = candidate_indices[candidates.index(candidate)]
                selected_indices.append(idx)
                next_population.append(candidate)
            
            # Se já preencheu a população exata, termina
            if len(next_population) == population_size:
                break
            
            # Passo 4: Recalcula ds-niching-distance dos candidatos restantes vs selecionados
            if len(selected_indices) > 0:
                calculate_ds_niching_distance(combined_population, distance_matrix, selected_indices)
        else:
            # Rank 1 não cabe todo - precisa usar crowding distance para desempate
            # Calcula crowding distance baseado em ua_rank e alpha_rank_distance
            for candidate in rank1_candidates:
                candidate.temp_fitness = candidate.fitness  # Salva fitness original
                candidate.fitness = [candidate.ua_rank, candidate.alpha_rank_distance]
            
            calculate_crowding_distance(rank1_candidates)
            
            # Restaura fitness original
            for candidate in rank1_candidates:
                candidate.fitness = candidate.temp_fitness
                delattr(candidate, 'temp_fitness')
            
            # Ordena por crowding distance (maior = melhor)
            rank1_candidates.sort(key=lambda ind: ind.crowding_distance, reverse=True)
            
            # Seleciona os que faltam para completar a população
            remaining_slots = population_size - len(next_population)
            for i in range(remaining_slots):
                next_population.append(rank1_candidates[i])
            
            break
    
    # Atualiza ds-niching-distance dos selecionados como média das distâncias entre si
    # Cria mapeamento: indivíduo -> índice na combined_population
    individual_to_idx = {id(ind): i for i, ind in enumerate(combined_population)}
    selected_final_indices = [individual_to_idx[id(ind)] for ind in next_population]
    
    for ind in next_population:
        idx = individual_to_idx[id(ind)]
        # Calcula média das distâncias vs todos os outros selecionados
        distances = [distance_matrix[idx][j] for j in selected_final_indices if j != idx]
        if len(distances) > 0:
            ind.ds_niching_distance = np.mean(distances)
        else:
            ind.ds_niching_distance = 0.0
    
    return next_population


####################################################################################################################################
####################################################################################################################################
### Crowding Distance

def calculate_crowding_distance(front):
    """
    Calcula a crowding distance para cada indivíduo no front
    Complexidade: O(M*N*log(N)) onde M é número de objetivos e N é tamanho do front

	• Muito importante manter a diversidade de soluções ao longo da evolucão de um algoritmo MOEA, 
      para garantir que não iremos convergir para um ótimo local, e iremos explorar e encontrar
      os modais em todo o fitness landscape

	• Abordagem NSGA-II (Crowding Distance)
		○ Realizamos o cálculo da crowding distance das soluções em um objetivo por vez:
			§ Ordenamos as soluções, em O(NlogN), com base nos seus valores para o objetivo m1 (primeiro dos M objetivos)
			§ Para a menor e maior solução (em relação aos valores de m1) -> atribuímos distancia(m1) = infinito
			§ Para todas as outras:
			    § distância(m1) = (fitness da próxima solução - fitness da solução anterior) / (fitness da maior solução - fitness da menor solução)
                § Ou seja, a distância entre os vizinhos normalizada pela distância dos extremos

		○ Realizamos esse cálculo para todos os M objetivos. A crowding distance total de uma solução 
          é o somatório de sua crowding distance individual em cada um dos M objetivos.
			§ Como atribuímos infinito para as soluções extremas em cada objetivo, elas serão sempre priorizadas em um 
              desempate por distância (vamos ver que o algoritmo ainda prioriza nível de dominância antes de diversidade) 
              o que faz sentido, pois por serem extremas, são mais diversas.
		
		○ Complexidade final = O(M*NlogN)
			§ Observamos que a operação que domina a complexidade do cálculo em cada objetivo é a ordenação. 
              As outras operações são muito simples.
			§ Como ordenamos em O(NlogN) em cada um dos M objetivos, temos a complexidade acima.

    """
    # Front vazio termina a funcao
    if len(front) == 0:
        return
    
    # Identifica quantidade de fitness
    n_objectives = len(front[0].fitness)
    
    # Inicializar crowding distance para todos os individuos do front
    for individual in front:
        individual.crowding_distance = 0.0
    
    # Para cada objetivo, calcula Crowding Distance
    for obj_idx in range(n_objectives):

        # Ordenar o front pelo objetivo atual
        front.sort(key=lambda ind: ind.fitness[obj_idx])
        
        # Atribuir infinito para as soluções extremas
        front[0].crowding_distance = float('inf')
        front[-1].crowding_distance = float('inf')
        
        # Obter o range do objetivo
        f_min = front[0].fitness[obj_idx]
        f_max = front[-1].fitness[obj_idx]
        
        # Evitar divisão por zero
        if f_max - f_min == 0:
            continue
        
        # Calcular crowding distance para as soluções intermediárias
        for i in range(1, len(front) - 1):
            distance = (front[i + 1].fitness[obj_idx] - front[i - 1].fitness[obj_idx]) / (f_max - f_min)
            front[i].crowding_distance += distance



####################################################################################################################################
####################################################################################################################################
### Seleção Ambiental

def environmental_selection(combined_population, config, generation, ua_rank_stat=None):
    """
    Seleção ambiental: seleciona os melhores N indivíduos de Rt = Pt + Qt
    
    Utiliza três mecanismos principais:
    1. Uncertainty-Aware Ranking: calcula ua_rank (estatística) e ua_rank_std (dispersão) 
       através de múltiplas simulações de fast non-dominated sort
    
    2. Decision-Space Niching (opcional): mantém diversidade no espaço de decisão através de:
       - Matriz de distâncias euclidianas ponderadas entre genótipos
       - Alpha-Rank-Distance: combinação adaptativa de ua_rank e ds_niching_distance
       - Seleção iterativa baseada em dominância de (ua_rank, alpha_rank_distance)
       - Crowding distance para desempate final
    
    3. Elitismo: as melhores soluções entre Pt e Qt são sempre mantidas
    
    Processo:
    - Calcula uncertainty-aware ranking (ua_rank e ua_rank_std)
    - Se config['utiliza_ds_niching'] == True:
        - Calcula matriz de distâncias no espaço de decisão
        - Calcula alpha_rank_distance adaptativo por geração
        - Seleciona iterativamente usando dominância em (ua_rank, alpha_rank_distance)
        - Usa crowding distance quando rank 1 não cabe todo
    - Se False:
        - Seleciona os population_size indivíduos de menor ua_rank
    
    Args:
        combined_population: população combinada Pt + Qt
        config: configurações do algoritmo
        generation: geração atual (0-indexed)
        ua_rank_stat: função ou string para calcular ua_rank (default: 'mean')
    """

    # Passo 1: Calcula uncertainty-aware ranking
    uncertainty_aware_ranking(combined_population, config, ua_rank_stat)

    # Passo 2: Verifica se usa decision-space niching
    if config['utiliza_ds_niching'] == True:
        # Calcula decision-space niching (matriz de distâncias euclidianas ponderadas)
        weights = config['pesos_ds_niching']
        distance_matrix = calculate_distance_matrix(combined_population, weights)
        
        # Seleção iterativa com decision-space niching + uncertainty-aware ranking + alpha adaptativo
        next_population = select_rank1_iteratively(combined_population, config, distance_matrix, generation)
    else:
        # Método antigo: ordena por ua_rank e seleciona os primeiros population_size
        combined_population_sorted = sorted(combined_population, key=lambda ind: (ind.ua_rank, ind.ua_rank_std))
        next_population = combined_population_sorted[:config['population_size']]

    return next_population