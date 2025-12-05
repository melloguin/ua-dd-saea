import numpy as np


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


def uncertainty_aware_ranking(combined_population, config):
    '''
    Uncertainty-Aware Ranking using Multiple Simulations

        - Salva os fitness originais (listas completas)
        - Realiza fast non-dominated sort para cada simulação
        - Coleta o rank de cada indivíduo nesta simulação
        - Restaura os fitness originais e calcula a média e desvio padrão dos ranks
    '''
    
    # Salva os fitness originais (listas completas)
    original_fitness = {}
    for individual in combined_population:
        original_fitness[id(individual)] = individual.fitness

    # Realiza fast non-dominated sort para cada simulação
    for s in range(config['n_simulations']):
        
        # Atribui o s-ésimo valor de fitness para cada indivíduo
        for individual in combined_population:
            # fitness[0] é uma lista com n_simulations valores para o objetivo 1
            # fitness[1] é uma lista com n_simulations valores para o objetivo 2
            individual.fitness = [
                original_fitness[id(individual)][0][s],  # s-ésimo valor do objetivo 1
                original_fitness[id(individual)][1][s]   # s-ésimo valor do objetivo 2
            ]
        
        # Realiza fast non-dominated sort com o fitness da s-ésima simulação
        fronts = fast_non_dominated_sort(combined_population, config)
        
        # Coleta o rank de cada indivíduo nesta simulação
        for individual in combined_population:
            individual.ua_rank.append(individual.rank)

    # Restaura os fitness originais e calcula estatísticas dos ranks
    for individual in combined_population:
        # Restaura os fitness originais
        individual.fitness = original_fitness[id(individual)]
        # Calcula a média dos ranks obtidos nas n_simulations
        individual.rank = np.mean(individual.ua_rank)
        # Calcula a métrica de dispersão: média dos desvios positivos acima da média
        mean_rank = individual.rank
        positive_deviations = np.maximum(0, np.array(individual.ua_rank) - mean_rank)
        individual.rank_std = round(np.mean(positive_deviations), 5)
        # Restaura os ua_ranks
        individual.ua_rank = []



####################################################################################################################################
####################################################################################################################################
### Seleção Geracional

def generational_selection(combined_population, config):
    """
    Seleção geracional: seleciona os melhores N indivíduos de Rt = Pt + Qt

	• Formamos P(t+1) com N soluções, selecionando os x elementos com maior crowding distance do x-ésimo conjunto (primeiro a não caber em N)
        • Iremos unificar ambas as populações para uma grande população Rt = Pt + Qt, de tamanho 2N
	    • Iremos usar a operação de "fast non-dominated sort", para separar as soluções de Rt em rank de não dominância
	    • Iremos selecionar todos os fronts (por rank de não dominância), enquanto couberem inteiramente em N
		○ Ou seja, adicionamos f1 inteiro se tiver menos termos que N, depois adicionamos f2 inteiro se |f1+f2| < N, 
              e assim por diante, até não caber o f-esimo conjunto inteiro junto com todos os seus antecessores em N
	    • Quando chegarmos ao conjunto que devemos dividir (fx), iremos ordenar seus termos pela crowding distance 
	        - E escolheremos as x soluções de mais crowding distance de fx para a próxima população de N = (|f1 + f2 + ... + fx-1| + x) soluções.

	- Essa metodologia garante o elitismo, uma vez que as melhores soluções entre Pt e Qt sempre serão mantidas (prioridade é sempre o ranking de dominancia)

    """

    # Calcula uncertainty-aware ranking
    uncertainty_aware_ranking(combined_population, config)

    # Ordenar população combinada por rank (menor rank/rank_std = melhor)
    combined_population_sorted = sorted(combined_population, key=lambda ind: (ind.rank, ind.rank_std))

    # Selecionar indivíduos para a próxima geração
    next_population = combined_population_sorted[:config['population_size']]    


    return next_population