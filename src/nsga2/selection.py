####################################################################################################################################
####################################################################################################################################
### Fast non-dominated sort

def dominates(fitness_solucao1, 
              fitness_solucao2):
    """
    Verifica se fitness1 domina fitness2 (minimização)
    Domina se é melhor ou igual em todos os objetivos e estritamente melhor em pelo menos um

    args:
        fitness1 (list[float, float]): 
    """
    better_in_any = False
    # percorre fitness a fitness das 2 solucoes (s1 e s2) 
    for f1, f2 in zip(fitness_solucao1, fitness_solucao2):
        # e sinaliza se a 2a solucao é pior em algum objetivo (indica que s1 não domina s2)
        if f1 > f2:  # Pior em algum objetivo
            return False
        if f1 < f2:  # Melhor em algum objetivo
            better_in_any = True

    return better_in_any



def fast_non_dominated_sort(population):
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
            if dominates(individual_p.fitness, individual_q.fitness):
                individual_p.dominated_solutions.append(individual_q)
            # se q domina p, incrementar np
            elif dominates(individual_q.fitness, individual_p.fitness):
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

def environmental_selection(combined_population, config):
    """
    Seleção ambiental: seleciona os melhores N indivíduos de Rt = Pt + Qt

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
    # Realiza fast non-dominated sort
    fronts = fast_non_dominated_sort(combined_population)
    
    # Calcular crowding distance para todos os fronts
    for front in fronts:
        calculate_crowding_distance(front)
    
    # Selecionar indivíduos para a próxima geração
    next_population = []
    front_idx = 0
    
    # Adicionar fronts completos enquanto couberem
    while front_idx < len(fronts) and len(next_population) + len(fronts[front_idx]) <= pop_size:
        next_population.extend(fronts[front_idx])
        front_idx += 1
    
    # Se ainda há espaço, preencher com os melhores (crowding distance) do próximo front
    if front_idx < len(fronts) and len(next_population) < pop_size:
        remaining = pop_size - len(next_population)
        # Ordenar por crowding distance (decrescente)
        fronts[front_idx].sort(key=lambda ind: ind.crowding_distance, reverse=True)
        next_population.extend(fronts[front_idx][:remaining])
    

    return next_population