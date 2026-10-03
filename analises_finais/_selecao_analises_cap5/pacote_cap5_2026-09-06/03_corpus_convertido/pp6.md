# pp6. An adaptive Bayesian approach to surrogate-assisted evolutionary multi-objective optimization

> Fonte (original): pp6. An adaptive Bayesian approach to surrogate-assisted evolutionary multi-objective optimization.pdf
> Extraído com pymupdf4llm (texto + tabelas + números; imagens omitidas). Páginas: 39.

---

**Honda Research Institute Europe GmbH** https://www.honda-ri.de/ 



# **An Adaptive Bayesian Approach to SurrogateAssisted Evolutionary Multi-objective Optimization** 

**Xilu Wang, Yaochu Jin, Sebastian Schmitt, Markus Olhofer** 

**2020** 

##### **Preprint:** 

This is an accepted article published in Information Sciences. The final authenticated version is available online at: https://doi.org/10.1016/j.ins.2020.01.048 

An Adaptive Bayesian Approach to Surrogate-Assisted Evolutionary Multi-objective Optimization 

### Journal Pre-proof 

An Adaptive Bayesian Approach to Surrogate-Assisted Evolutionary Multi-objective Optimization 

Xilu Wang, Yaochu Jin, Sebastian Schmitt, Markus Olhofer 

PII: S0020-0255(20)30059-1 DOI: https://doi.org/10.1016/j.ins.2020.01.048 Reference: INS 15179 To appear in: _Information Sciences_ Received date: 3 September 2019 Revised date: 21 January 2020 Accepted date: 28 January 2020 



Please cite this article as: Xilu Wang, Yaochu Jin, Sebastian Schmitt, Markus Olhofer, An Adaptive Bayesian Approach to Surrogate-Assisted Evolutionary Multi-objective Optimization, _Information Sciences_ (2020), doi: https://doi.org/10.1016/j.ins.2020.01.048 

This is a PDF file of an article that has undergone enhancements after acceptance, such as the addition of a cover page and metadata, and formatting for readability, but it is not yet the definitive version of record. This version will undergo additional copyediting, typesetting and review before it is published in its final form, but we are providing this version to give early visibility of the article. Please note that, during the production process, errors may be discovered which could affect the content, and all legal disclaimers that apply to the journal pertain. 

- © 2020 Published by Elsevier Inc. 

#### An Adaptive Bayesian Approach to Surrogate-Assisted Evolutionary Multi-objective Optimization 

Xilu Wang<sup>a</sup> , Yaochu Jin<sup>a,</sup><sup>_∗_</sup> , Sebastian Schmitt<sup>b</sup> , Markus Olhofer<sup>b</sup> 

> _aDepartment of Computer Science, University of Surrey, Guildford, GU2 7XH, U.K._ 

> _bHonda Research Institute Europe GmbH, Carl-Legien-Strasse 30, D-63073 Offenbach/Main, Germany_ 

###### **Abstract** 

Surrogate models have been widely used for solving computationally expensive multi-objective optimization problems (MOPs). The efficient global optimization (EGO) algorithm, a Bayesian approach to surrogate-assisted optimization, has become very popular in surrogate-assisted evolutionary optimization. In this paper, we propose an adaptive Bayesian approach to surrogate-assisted evolutionary algorithm to solve expensive MOPs. The main idea is to tune the hyperparameter in the acquisition function according to the search dynamics to determine which candidate solutions are to be evaluated using the expensive real objective functions. In addition, the sampling selection criterion switches between an angle based distance and an angle-penalized distance over the course of optimization to achieve a better balance between exploration and exploitation. The performance of the proposed algorithm is examined on a set of benchmark problems and an airfoil design optimization problem using a maximum of 300 real fitness evaluations. Our experimental results show that the proposed algorithm is competitive compared to four popular multi-objective evolutionary algorithms. 

_Keywords:_ Expensive multi-objective optimization, surrogate-assisted 

evolutionary algorithm, Bayesian optimization, acquisition function, reference 

> _∗_ Corresponding author. _Email addresses:_ `xw00616@surrey.ac.uk` (Xilu Wang), `yaochu.jin@surrey.ac.uk` (Yaochu Jin), `sebastian.schmitt@honda-ri.de` (Sebastian Schmitt), `Markus.Olhofer@honda-ri.de` (Markus Olhofer) 

_Preprint submitted to Information Sciences_ 

_January 29, 2020_ 

vectors 

###### **1. Introduction** 

Multi-objective optimization problems (MOPs) are commonly seen in many economic, scientific, and engineering applications. Various types of algorithms have been proposed for solving MOPs. For example, the scalarization tech5 nique is one popular method that converts an MOP into a single-objective optimization problem, which can be achieved by the global criterion method, the weighted min-max method, the _ϵ_ -constraint method, normal boundary intersection or reference point methods [1]. In addition, game theory has been applied to many real-world MOPs, such as wireless and communication net10 works [2, 3] and electric systems [4], due to the similarity between MOPs and the game [5]. For example, power optimization for a microgrid is defined as a bi-objective optimization [4]. Two players are assumed to correspond to two objectives, and consequently a modified game theory is adopted to find an optimal solution. Tsiropoulou _et al._ adopted the non-cooperative game theory to 15 efficiently allocate transmission power and data rate to users in the uplink of a cellular wireless network [6]. Another popular approach is based on evolutionary algorithms (EAs), which have been applied successfully to many real-world complex optimization problems [7]. Since they are population-based methods that are able to obtain multiple Pareto optimal solutions in a single run, EAs 20 are particularly well suited for MOPs. Over the past decades, a large number of multi-objective evolutionary algorithms (MOEAs) have been proposed, such as nondominated sorting genetic algorithm II (NSGA-II) [8], multi-objective evolutionary algorithm based on decomposition (MOEA/D) [9], reference vector guided evolutionary algorithm (RVEA) [10], strength Pareto evolutionary algo25 rithm 2 (SPEA2) [11], and an estimation of distribution algorithm (IM-MOEA) [12], just to name a few. 

However, a major criticism against MOEAs is that most of them require a large number of function evaluations to find Pareto optimal solutions. This 

2 

weakness becomes more obvious when EAs are employed for solving time30 consuming multi-objective problems where the evaluation of the objectives involves expensive physical experiments or computationally intensive numerical simulations. This class of problems is common in real-world applications [13], where, e.g., computationally intensive computational fluid dynamics (CFD) simulations must be conducted to evaluate the performance in structural design 35 optimization [14] and in engineering design optimization [15]. 

To address the challenges in using MOEAs for computationally expensive optimization problems, surrogate-assisted evolutionary algorithms (SAEAs) are widely adopted [16]. SAEAs can be roughly classified into two categories. In the first category, the expensive objective function is approximated by a single or 40 an ensemble of surrogates. More specifically, computationally efficient surrogate models are constructed using historical data and then used to approximate the fitness values of the candidate solutions instead of computing the real fitness. For example, Marjavaara [17] replaced the three-dimensional models of the diffuser geometries with a surrogate model and achieved better performance in 45 the diffuser shape design problem. In the second category, the surrogate works as a classifier to filter the newly generated candidate solutions based on the predicted labels. Consequently, several classification-based SAEAs have been developed, e.g., the classification and Pareto domination based MOEA [18] and the classification-based SAEA (CSEA)[19]. 

50 The commonly used surrogate models include the radial basis function (RBF), support vector machines (SVM), radial basis function networks (RBFN), polynomial regression, and Gaussian processes (GPs), also called Kriging model. Among them, GP is one of the most popular surrogate models and has attracted increasing attention. The main reason is that GP can not only predict 55 the objective value of a candidate solution, but also provide a confidence level (a degree of uncertainty) of its predictions [20]. Based on the predicted objective value and its uncertainty, an acquisition function (AF) can be utilized as the model management strategy to determine which candidate solutions should be evaluated by the real objective function. Surrogate-assisted optimization using 

3 

60 a GP in combination with an acquisition function (also known as infill criterion) is called Bayesian optimization [21] or efficient global optimization (EGO) [22]. 

The Bayesian optimization approach, which combines GPs with an acquisition function, have been widely adopted in SAEAs for handling various expensive single-objective optimization problems. For example, in [23] the GP model 65 was used as an inexpensive fitness function to accelerate convergence, and different aggregations of the predicted function value and the predicted standard deviation of the GP were employed as acquisition functions to balance exploration with exploitation. Hoyle _et al._ adopted a GP model to predict objective function values when optimizing the design of engine air intakes, new data points 70 are then chosen based on the expected improvement function, after finding a promising location, a local exploration is performed to speed up the convergence [24]. In [25], a particle swarm optimization algorithm switches between a local ensemble surrogate model and a global one, interleavingly searching for the best and most uncertain solutions. The algorithm has been shown to per75 form well on both a set of single-objective test problems and an airfoil design problem. Tian _et al._ [26] considered the uncertainty and the approximated fitness provided by the GP as two separate objectives instead of combining them into a scalar acquisition function, which was demonstrated to be competitive for solving high-dimensional single-objective optimization problems. 

80 Nevertheless, it is non-trivial to build effective surrogate models and select new data samples based on the working mechanisms of the acquisition function for accelerating convergence and promoting diversity in multi-objective optimization. In [27], an algorithm termed ParEGO was proposed, where the augmented Tchebycheff function is adopted to aggregate multiple objectives into a 

- 85 scalar fitness function so that an existing acquisition function for single-objective optimization can be directly applied for surrogate management. Ponweiser _et al._ [28] proposed a new Bayesian approach to multi-objective optimization (termed SMS-EGO), in which a hypervolume based acquisition function rather than a weighted aggregation of the objective functions is utilized to convert an MOP 

- 90 into a single-objective optimization problem. However, due to the computa- 

4 

tional complexity in calculating the hypervolume, SMS-EGO may become very time-consuming as the number of objectives increases. A GP-assisted MOEA/D was reported in [29], where a GP model is built for each subproblem so that an acquisition function can be applied to each subproblem. In [30], Chugh _et al._ 95 introduced a Kriging-based RVEA (called K-RVEA), which combines the angle penalized distance and the uncertainty for selecting new samples to update the GP. Whenever diversity is needed in K-RVEA, the uncertainty is chosen as the selection criterion by ranking the mean value of uncertainty on different objectives and selecting the one having the maximum averaging uncertainty. 

100 Most surrogate-assisted MOEAs using the Bayesian approach have focused on converting a multi-objective problem into a single-objective one by means of aggregation or decomposition so that acquisition functions can be used for surrogate management. One exception is presented in Guo _et al._ [31], which suggests to use an ensemble to replace the GP models to reduce the computational com105 plexity especially for high-dimensional problems. To the best of our knowledge, no work has been reported to tune the hyperparameters in the acquisition function to achieve the best trade-off between exploitation and exploration during the search process, which is of pivotal importance in optimization. 

The rest of this paper is organized as follows. Section 2 presents a brief 110 introduction to the background knowledge related to Bayesian optimization. In Section 3, a pilot study to investigate the efficiency of each proposed strategy is undergone and the proposed algorithm is described in detail. Numerical simulations are conducted in Section 4, where the results are presented and discussed. Finally, conclusions of this paper are drawn and future work is suggested in 115 Section 5. 

###### **2. Background** 

In this section, Gaussian processes and the widely used acquisition functions are introduced at first, followed by a review of the angle-penalized distance, the selection criterion used in RVEA. 

5 

120 _2.1. Gaussian Processes_ 

GP is a powerful surrogate model, which can provide a prediction for a new data point, together with a degree of uncertainty. For example, a 1 _D_ GP model illustrated in Fig. 1 is trained with three training data, the GP model can then predict the mean fitness and the uncertainty on any new data point. That is, for a given _x_ 1, we can know the model’s prediction _µ_ ( _x_ 1), uncertainty _σ_ ( _x_ 1), and the confidence intervals _µ_ ( _x_ 1) _± σ_ ( _x_ 1), respectively. The uncertainty information denotes the confidence level of the prediction, which is very useful in model management in surrogate-assisted optimization. The idea behind GPs [32] is that there is a multivariate Gaussian distribution on _R_<sup>_n_</sup> for any finite set of _N n_ -dimensional inputs **X** = _{_ **x**<sup>1</sup> _,_ **x**<sup>2</sup> _, ..._ **x**<sup>_N_</sup> _}_<sup>_T_</sup> . Given a set of inputs **x** and their associated function values **y** = _{y_<sup>1</sup> _, y_<sup>2</sup> _, ...y_<sup>_N_</sup> _}_<sup>_T_</sup> as the training data, a GP model can be expressed by: 



where _µ_ is the mean of the stochastic process, and _ε_ ( **x** ) is drawn from a stochastic process with zero mean but non-zero standard deviation _σ_ 



The correlation between the error terms of any two data points, **x**<sup>_i_</sup> and **x**<sup>_j_</sup> , heavily depends on the distance between them. In general, the squared exponential function with additional hyperparameters, rather than an Euclidean distance function, is employed to calculate the correlation: 





where _pk ∈_ (0 _,_ 1) controls the smoothness of the function in terms of the _k_ -th dimension, and _θk >_ 0 denotes the importance of this dimension. When there 

6 

are _N_ training data, an _N × N_ correlation matrix **C** will be obtained: 



As a result, 2 _N_ + 2 hyperparameters will determine a GP model, which can be estimated by maximizing the following likelihood function: 



Therefore, the estimates _µ_ ˆ and ˆ _σ_<sup>2</sup> for the true values _µ_ and _σ_ will be obtained 



where **1** denotes a _N ×_ 1 column vector of ones. Based on the given parameters, the GP model can predict the mean value together with a variance for a new data point **x**<sup>_new_</sup> , 





where **r** = (Corr( **x**<sup>_new_</sup> _,_ **x**<sup>1</sup> ) _, ...,_ Corr( **x**<sup>_new_</sup> _,_ **x**<sup>_N_</sup> ))<sup>_T_</sup> presents a correlation vector between **x**<sup>_new_</sup> and each element **x**<sup>_i_</sup> in **X** . 

###### _2.2. Acquisition Function_ 

Given a GP model trained by a set of observed data, selecting the appropriate 125 decision vector (a data point in the decision space) is essential for the SAEA to work effectively. Acquisition functions (AFs), inspired from Bayesian decision theory, are designed as metrics for selecting the unobserved data to be evaluated by the real expensive objective functions. AFs are computationally very cheap, 

7 



<!-- Start of picture text -->
�� x 3 � � �� x 3 �<br>�� x 3 �<br>�� x 1 � �� x 2 �<br>�� x 2 � ��� x 2 �<br>��� x 1 ���� x 1<br>x 1 x 2 x 3<br><!-- End of picture text -->

Figure 1: Illustration of a 1 _D_ Gaussian process with three training data points and the predictions of the GP mean values and standard deviation values ( _µ_ ( _·_ ) and _σ_ ( _·_ )) at three new data points ( _x_ 1, _x_ 2 and _x_ 3). The solid line and the shaded area indicate the mean and intervals estimated with the GP model. 

and by sequentially finding its optimum we are able to guide the search towards 130 the optimum of the original objective function. 

Several AFs have been proposed to select new data points utilizing the information obtained by surrogate models. Expected improvement (EI) [33] calculates the expected value of the improvements beyond the best observed point, and was extended to multi-objective optimization in [34]. Predictive entropy 135 search (PES) proposed in [35] is an alternative for Entropy Search (ES), making use of the information theory. 

The AF proposed in this work is inspired from the lower confidence bound (LCB) [36]. LCB is designed to balance the exploration and exploitation by combining the uncertainty with the predicted objective values [37]. Intuitively, for a minimization problem, selecting a point with the maximum amount of uncertainty can encourage more exploratory search; however, selecting most uncertain points only may lead to nearly random search. By contrast, we can perform exploitative search if we pick points where the predicted mean values 

8 

are minimum, which, however, at a higher risk of getting trapped in a local optimum. Hence, LCB aims to strike a balance between exploration and exploitation: 



where _κ_ presents a trade-off constant. LCB implicitly prefers points whose predicted mean value _µ_ is small and the corresponding standard deviation _σ_ is large. 

140 

###### _2.3. Angle-penalized Distance Metric_ 

The reference vector guided evolutionary algorithm (RVEA) [10] is a recently proposed MOEA for solving many-objective optimization problems. In RVEA, a set of reference vectors are predefined in the objective space as the preferred search directions that guide the search towards the Pareto front (PF). An angle-penalized distance (APD) is designed based on the reference vectors to determine which candidate solutions should be associated with their closest reference vectors. More precisely, APD combines the convergence and diversity criteria and dynamically adjusts the importance of the two criteria according to the number of objectives and the number of generations. APD is defined as follows: 



Here, _dt,i,j_ presents the APD value of the _i_ -th solution in terms of the _j_ -th reference vector in the _t_ -th generation, and **Z**<sup>_min_</sup> _t_ denotes the vector of the minimal objective values at the current generation; _∥_ **f** _t,i −_ **Z**<sup>_min_</sup> _t ∥_ denotes the translated objective value, adopted as a convergence criterion; _θ_ **f** _t,i,_ **v** _t,j_ represents the angle between the objective vector **f** _t,i_ and the reference vector **v** _t,j_ ; _P_ ( _θ_ **f** _t,i,_ **v** _t,j_ ) represents a penalty function and serves as a diversity criterion, which is defined as follows: 



with 



9 

where _M_ and _N_ represent the number of objectives and the number of reference vectors, respectively; _β_ is a predefined parameter to control the rate of the penalty function; _γvt,j_ denotes the smallest angle between the reference vector **v** _t,j_ and its closest neighboring reference vector **v** _t,i_ . 

Typically, the original reference vectors are generated uniformly in the objective space using the simplex-lattice design method. Unfortunately, these vectors are not suited for problems where different objectives have very different ranges. Hence, a reference vector adaptation method was proposed in [10] in the following manner: 



145 where ’ _◦_ ’ denotes the Hadamard product that multiplies two vectors of the same size element-wise, **v** _t_ +1 _,i_ denotes the _i_ -th adapted reference vector for the _t_ -th generation, while **v** 0 _,i_ represents the _i_ -th uniformly distributed reference vector, and **Z**<sup>_max_</sup> _t_ and **Z**<sup>_min_</sup> _t_ denote the vectors consisting the maximum and minimum objective values obtained so far. 

###### 150 **3. Proposed Algorithm** 

As mentioned above, Bayesian optimization has been extended to expensive MOPs over the past years. In this section, an adaptive Bayesian approach to surrogate-assisted multi-objective evolutionary optimization algorithm (ABMOEA) is presented, and Fig. 2 gives the flowchart of the proposed AB-MOEA. 

155 

###### _3.1. Algorithm Framework_ 

The framework of the proposed AB-MOEA are outlined in Algorithm 1. The algorithm begins with sampling the objective functions for usually around 11 _n −_ 1 points, where _n_ is the dimensionality of the decision space, and then 160 uses these samples to train the GP model. The RVEA algorithm is executed using only the surrogate models for 20 generations to obtain an optimized population. This optimized population is utilized to determine _u_ new samples with 

10 



<!-- Start of picture text -->
���������������������<br>������������������������<br>����<br>��������������<br>���������������� �������������������<br>����������������������<br>�����������������������<br>������������������������ �����������������<br>��������<br>�����������������������������<br>����������������������� �������������������������<br>����������������������������������������������������������� �������������������<br>����������������������������<br>�����������������������������������<br>�����������������������������<br>���������<br>� �<br>� FE � FE max ? w � w max ?<br>�<br>������<br><!-- End of picture text -->

Figure 2: Flowchart of AB-MOEA 

the proposed adaptive acquisition function and the proposed sampling selection criterion. The new samples are evaluated with the real objective functions and 165 the surrogate models are then retrained using the extended training set including the new data samples. The proposed framework is intended to efficiently optimize computationally expensive multi-objective optimization problems by introducing an adaptive acquisition function and a new sampling selection criterion. The adaptive acquisition function and the corresponding sampling se170 lection criterion within this framework aim to achieve a better balance between diversity and convergence, which will be elaborated in the following. 

###### _3.2. Adaptive Acquisition Function_ 

Many ideas have been suggested to adapt the Bayesian approach to MOPs, but no work on adaptation of the AFs has been reported. In this work, an adaptive acquisition function is proposed to dynamically adjust the weights of the uncertainty and the predicted mean fitness value, thereby achieving a better balance between exploration and exploitation at different search stages. 

11 

|**Algorithm 1** Framework of AB-MOEA|
|---|
|**Input:** _FEmax_: the maximum number of real objective function evaluations; _u_: the number|
|of points selected to be re-evaluated in each iteration; _wmax_: the maximum number of|
|generations before updating GPs;|
|**Output:** The fnal solution population|
|1: Initialization: Sample 11_n −_1 points **x**<sup>1</sup>, **x**<sup>2</sup>,..., **x**<sup>11</sup><sup>_n−_1 </sup>in the decision space using the|
|Latin Hybercube Sampling method; evaluate the values **y**<sup>1</sup>,...,**y**<sup>11</sup><sup>_n−_1 </sup>of the objective|
|functions on these 11_n −_1 points; use [**X**_,_**Y**] as training data ;|
|2: train GP models with the training data;|
|3: **while** _FE_ ⩽_FEmax_ **do**|
|4:<br>//Using the surrogate in RVEA//|
|5:<br>**while** _w_ ⩽_wmax_ **do**|
|6:<br>Generate ofspring by the simulated binary crossover (SBX) and the polynomial mu-|
|tation;|
|7:<br>Combine parent and ofspring populations and predict their ftness with the GP models;|
|8:<br>Select a new population for the next generation;|
|9:<br>Update the reference vectors;|
|10:<br>_w_ =_w_+ 1|
|11:<br>**endwhile**|
|12:<br>//Updating the surrogate//|
|13:<br>Call the proposed AF to evaluate the individuals in the optimized population;|
|14:<br>Call the proposed sampling selection strategy to determine _u_ points to be evaluated|
|by the original objective functions and update _FE_ =_FE_+_u_; (see Algorithm 2)|
|15:<br>Add individuals from step 8 to training data and limit the number of training data<br>and go to step 2;|



16: **end while** 

17: **return** The final solution population _P_ 

12 

The adaptive acquisition function is defined as follows: 



where 



where ’ _./_ ’ denotes element-by-element division for two vectors of the same size; **_µ_ x** and **_σ_ x** denote the mean and variance of the predicted function values of 175 each individual **x** in the optimized population obtained by RVEA, respectively; **_µ_** _max_ and **_σ_** _max_ represent the maximum values of the mean and variance values provided by the GP models, respectively. In this way, both the predicted objective value and the uncertainty are normalized to [0 _,_ 1]. _α_ is an adaptation parameter defined by a cosine function. _FE_ denotes the current number of real 180 objective function evaluations, and _FEmax_ represents the predefined maximum number of real objective function evaluations. 

The main motivation behind the above adaptive acquisition function is to achieve relatively fast convergence in the early stage by assigning a large weight to **x** , while more exploitative search is achieved in the later search stage, where we select new pints with APD, so that new data points in the neighborhood of the previously observed data are preferred to be sampled when searching the promising area. Herein we explain briefly why we select new data points with lower uncertainty as the iteration increases. It is assumed that a decision space around the training data sampled so far is the most promising area near the end of the run; therefore, the proposed AF allows to sample new points inside that domain for local search. We also test a variant of the proposed AF, 



The difference between the two AFs is whether we minimise the uncertainty or not near the end of the run and the experimental results confirm the effectiveness of the suggested AF. As shown in Fig. 3, the proposed AF and its variant sample 

185 five new data points for twice (when _FE_ = 195 and _FE_ = 200) on DTLZ2 based on the same GP model. It is worth noting that the samples selected by 

13 

the proposed AF are much closer to the PF, while points sampled by the variant are far away from the PF. These indicate that the proposed criterion in (15) results in more diverse and exploitative search in the later stage, which is of 190 particular importance when the number of fitness evaluated is highly limited. 



<!-- Start of picture text -->
Sample points (FE=195)<br>The obtained PF<br>New sample points (FE=200)<br>The true PF<br><!-- End of picture text -->



<!-- Start of picture text -->
Sample points (FE=195)<br>The obtained PF<br>New sample points (FE=200)<br>The true PF<br>(b) Data points sampled by the variant<br><!-- End of picture text -->

Figure 3: An example of new data points sampled by the proposed AF and its variant for DTLZ2 (when _FE_ = 195 and _FE_ = 200), respectively. 

###### _3.3. Adaptive Sampling Selection Criterion_ 

As analyzed in [38], the reference vectors predefined in RVEA divide the search space into several subspaces, with each reference vector specifying a direction along which the Pareto optimal solutions are preferred. A set of solutions associated to each reference vector is expected to be achieved to guarantee the diversity as well as the convergence. To this end, we introduce two different sampling selection strategies that work together with the proposed adaptive AF. Specifically, when _α <_ 0 _._ 5, the angle-based selection approach is employed to prioritize the population diversity: 



The above sampling selection criterion does not consider the distance from the candidate solution to the reference vector, which usually serves as the convergence criterion in APD. As a result, this sampling selection strategy focuses 

14 

195 on promoting the diversity of the population. When _α >_ = 0 _._ 5, APD is adopted to determine which points are to be sampled. The overall sampling selection criterion utilized in our algorithm is shown in Algorithm 2. 

###### **Algorithm 2** Adaptive Sampling Selection Criterion 

|**Input:** _α_: the adaptive parameter based on a cosine function;_u_: the number of points selected|
|---|
|to be re-evaluated in each iteration; **_v_**: the reference vectors; _P_: the fnal population<br>obtained from RVEA|
|**Output:** The selected re-evaluated individuals|
|1: **if** _α <_0_._5 **then**|
|2:<br>// Using the angle-based sampling selection criterion//|
|3:<br>Calculate the _Angle_(_θ_**f**_t,i,_**v**_t,j_) for each individual in the population and select _u_ new|
|points to be re-evaluated;|
|4: **else**If _α >_= 0_._5|
|5:<br>//Using APD method//|
|6:<br>Calculate the _dt,i,j_ for each individual in the population and select _u_ new points to be<br>re-evaluated;|
|7: **end if**|



###### **4. Comparative Studies** 

In this section, numerical experiments are conducted on nine three-objective 200 benchmark problems taken from the DTLZ test suite and seven bi-objective benchmark problems from the UF test suite. To examine the efficiency of the proposed strategies, AB-MOEA is compared with its two variants, AS-MOEA and SM-MOEA. Here, AS-MOEA employs the proposed adaptive AF and the APD sampling selection criterion, while SM-MOEA employs the LCB and the 205 proposed sampling selection criterion. Then we compare AB-MOEA with the original RVEA as well as three representative Bayesian approaches to SAEAs, namely MOEA/D-EGO [29], SMS-EGO [39], and K-RVEA [30]. Although all these compared algorithms except for RVEA employ different kinds of EAs and acquisition functions, respectively, they all adopt the Gaussian processes as the 210 surrogates and use the prediction provided by GPs during the search process. As indicated in [40, 41], the computational complexity of training GP is _O_ ( _n_<sup>3</sup> ), 

15 

where _n_ is the number of training samples. Therefore, it is worthy of noting that the major computational costs of these algorithms are mainly spent on training the GPs, which depends on the number of training data. Finally, it 215 should be emphasized that the computational complexity of an expensive real fitness evaluation, e.g., a 3D computational fluid dynamics simulation or car crash test often take hours or even days [14, 19], which is much higher than that of training a surrogate. That is the reason why the number of real fitness evaluations has been used as the baseline for comparing SAEAs. 

220 In the following section, we begin with briefly introducing the test problems and performance metrics adopted in this work. Afterwards, the details of the experimental settings concerning the four compared algorithms are described. Lastly, the experimental results including the pilot studies and the comparative results, together with the Wilcoxon rank sum test, are presented and discussed. 



225 _4.1. Test Problems_ 

In our experiments, the proposed algorithm is compared with four selected algorithms on seven benchmark functions (DTLZ1 to DTLZ7) with three objectives suggested in [42], two modified counterparts of DTLZ1 and DTLZ3, and the UF test suite from the CEC2009 MOEA competition with two objectives [43], respectively. Before starting our experiments, we want to have a discussion about the multi-model _g_ function used in DTLZ1 and DTLZ3. The _g_ function, given in the following, is suggested to control the ruggedness of DTLZ1 and DTLZ3 [42], 



where _n_ denotes the number of decision variables. As indicated in [44], 20 _π_ within the cosine term triggers excessively ruggedness. Consequently, 2 _π_ is adopted to reduce the complexity to a reasonable level. The modified counterparts are denoted as DTLZ1a and DTLZ3a, respectively. As recommended 

230 in [42], the number of decision variables for the test instances is set to _n_ = _M_ + _K −_ 1, where _K_ = 5 is adopted for DTLZ1 and DTLZ1a, _K_ = 10 is used 

16 

for DTLZ2 to DTLZ6 as well as DTLA3a, and _K_ = 20 is employed in DTLZ7. _M_ represents the number of objectives. Here, we set _M_ = 3. 

###### _4.2. Performance Metrics_ 

235 The inverted generational distance (IGD) [45], hypervolume (HV) [46], generational distance (GD) [47] and spread (∆) [48] metrics are adopted to assess the performance of the algorithms. IGD and HV provide a combined information of the convergence and diversity of the obtained set of solutions, while GD and spread metrics work as the convergence measure and diversity measure, 240 respectively. The PlatEMO toolbox [49] is used to calculate values of these performance metrics in our experiments. Let _P_<sup>_∗_</sup> be a set of uniformly distributed solutions sampled from the objective space along the true PF. Let _P_ be an obtained approximation to the PF. 

1) _GD_ : GD measures the average distance between the obtained PF and the true PF of the problem, formulated as follows: 



where _|P |_ is the cardinality of the set _P_ and _d_ ( _υ, P_<sup>_∗_</sup> ) is the minimal Euclidean 245 distance between _υ_ and all points in _P_<sup>_∗_</sup> . The smaller the GD value is, the better the convergence performance. 

2) _Spread_ (∆): Spread is used to evaluate the extent of the Pareto front covered by the obtained set of solutions, defined as 



250 

where _d_ ( _υ, P_ ) is the minimum Euclidean distance between _υ_ and all points in _P_ , ( _Ei, ..., Em_ ) are _m_ extreme solutions in the true PF _P_<sup>_∗_</sup> and _d_<sup>¯</sup> = <u>�</u> _<u>υ∈P|P</u>_<sup>_d_</sup> _|_<sup><u>(</u></sup><sup>_υ,P_</sup><sup><u>))</u></sup> is the mean distance between the solutions of _P_ . A smaller value of ∆indicates a better diversity of the obtained PF. 

3) _IGD_ : The definition of IGD is similar to GD. IGD measures the inverted generational distance from _P_<sup>_∗_</sup> to _P_ , defined as 



17 

where _d_ ( _υ, P_ ) is the minimum Euclidean distance between _υ_ and all points in _P_ . The smaller IGD value, the better the achieved solution set is. 

4) _HV_ : HV calculates the volume of the objective space dominated by an approximation set _P_ and dominates _P_<sup>_∗_</sup> sampled from the PF. 



where _ϑi_ represents the hypervolume contribution of the _i_ -th solutions with respect to the reference points. All HV values presented in this work are nor255 malized to [0 _,_ 1]. Algorithms achieving a larger HV value are better. 

###### _4.3. Experimental Settings_ 

We run each algorithm on each benchmark problem for 20 independent times, and the Wilcoxon rank sum test is calculated to compare the mean of 20 running results obtained by AB-MOEA and by the compared algorithms at a significance 260 level of 0.05. Symbol ”(+)” indicates that the proposed algorithm outperforms the compared algorithm statistically significantly, while ”(–)” means that the compared algorithm performs better than AB-MOEA, and ”( _≈_ )” means there is no significant difference between them. 

AB-MOEA and its variants are implemented in MATLAB R2009a on an Intel 265 Core i7 with 2.21 GHz CPU, and the compared algorithms are implemented in PlatEMO toolbox [49]. In all Bayesian SAEAs, the GP model is constructed using the DACE toolbox [50]. The general parameter settings in the experiments are given as follows: 1) The number of initial training points _Ntrain_ = 11 _n −_ 1, where _n_ is the number of decision variables. 2) The maximum number of real 270 function evaluations _FEmax_ = 300. 3) The maximum number of generations before updating GPs _wmax_ = 20. The specific parameter settings for each compared algorithm are the same as recommended in their original papers. 

###### _4.4. Experimental Results_ 

###### _4.4.1. Pilot Studies_ 

275 To validate the proposed strategies, pilot studies are performed on the above test instances for 20 runs independently, and the mean of the results achieved 

18 

by the original RVEA is adopted for comparison using the Wilcoxon rank sum test. We calculate the values of the performance metrics for the non-dominated solution set in each run, respectively. The minimum, maximum and mean val280 ues of the performance metrics over 20 times are collected and presented in Tables 1 and 2, respectively, where the best result of each benchmark function is highlighted. 

First, we assess the efficiency of the proposed sampling selection criterion in the proposed AB-MOEA in addressing expensive MOPs via comparing SM285 MOEA with the original RVEA. According to the statistical results presented in Table 1, it can be seen that SM-MOEA significantly outperforms the original RVEA in terms of IGD values on DTLZ1a, DTLZ2, DTLZ3a, DTLZ6 as well as DTLZ7, while there is little difference between SM-MOEA and RVEA on DTLZ1, DTLZ3, DTLZ4 and DTLZ5. Similarly, SM-MOEA outperforms 290 RVEA on all tested instances except for DTLZ4 and DTLZ7 in terms of the HV metric. These results indicate SAEAs with the help of the suggested sampling selection criterion are able to improve the balance between the diversity and convergence. 

Table 1: Statistical results of the IGD values obtained by SM-MOEA, AS-MOEA, AB-MOEA, and RVEA with the same number of real function evaluations 

|Testproblem|SM-M|OEA|AS-MOE|A|AB-M|OEA|RVEA||
|---|---|---|---|---|---|---|---|---|
||min<br>me|an<br>max|min<br>mean|max|min<br>mea|n<br>max|min mean|max|
|DTLZ1|16.67 33.14|(_≈_) 56.21|14.26 28.39 (+)|**43.13**|16.58**27.29**|(+) 52.88|**10.08** 33.68|51.56|
|DTLZ1a|2.04 5.36|(+) 9.58|0.96 1.89 (+)|3.48|**0.35 1.47**|(+) **2.70**|5.21 23.79|48.80|
|DTLZ2|0.09 0.12|(+) 0.18|0.09 0.12 (+)|0.21|**0.08 0.09**|(+) **0.17**|0.23<br>0.42|0.49|
|DTLZ3|185.7 347.6|(_≈_) 456.4|199.4 319.1 (+)|446.9|199.1**310.8**|(+)**420.7**|**154.2** 374.4|479.7|
|DTLZ3a|26.63 99.90|(+) 246.8|**9.08** 30.82 (+)|110.7|17.05**30.65**|(+)**58.97**|173.2 330.4|482.0|
|DTLZ4|0.36 0.53|(_≈_) 0.85|**0.15** 0.50 (_≈_)|0.78|0.23<br>**0.43**|(+) **0.68**|0 .30 0.56|0.71|
|DTLZ5|0.34 0.35|(_≈_) 0.37|0.34 0.34 (_≈_)|0.35|**0.06 0.09**|(+) **0.19**|0 .13 0.35|0.49|
|DTLZ6|3.91 4.70|(+) 5.54|3.89 4.66 (+)|**5.33**|**3.83 4.60**|(+) 5.56|6 .22 7.89|8.50|
|DTLZ7|2.74 3.46|(+) 4.59|3.13 4.40 (+)|6.07|**0.58 0.81**|(+) **1.40**|3 .45 6.41|7.82|



Next, we compare AS-MOEA with RVEA to investigate the effectiveness of 

19 

Table 2: Statistical results of the HV values obtained by SM-MOEA, AS-MOEA, AB-MOEA, and RVEA with the same number of real function evaluations 

|Test problem|SM-MOEA<br>min<br>mean<br>max|AS-MOEA<br>min<br>mean<br>max|AB-MOEA<br>min<br>mean<br>max|RVEA<br>min mean max|
|---|---|---|---|---|
|DTLZ1|0.968 0.985 (+) 0.995|**0.979** 0.989 (+) 0.995|0.971 **0.993**(+)**0.996**|0.901 0.939 0.995|
|DTLZ1a|0.569 0.802 (+) 0.975|0.971 0.990 (+) 0.997|**0.973 0.992**(+)**0.998**|0.000 0.166 0.736|
|DTLZ2|0.305 0.443 (+) 0.489|0.270 0.432 (+) 0.485|**0.350 0.444**(+)**0.488**|0.021 0.111 1.000|
|DTLZ3|0.863 0.910 (+) 0.956|**0.876 0.922**(+) 0.957|0.862 0.921 (+) 0.957|0.737 0.832 **0.985**|
|DTLZ3a|0.000 0.238 (+) 0.728|0.000 **0.857**(+)**0.982**|**0.403** 0.855 (+) 0.979|0.000 0.000 0.000|
|DTLZ4|0.000 0.015 (_≈_) 0.062|0.000 0.060 (_≈_)**0.443**|**0.009 0.063**(_≈_) 0.201|0.000 0.022 0.144|
|DTLZ5|0.212 0.255 (+) 0.282|**0.242 0.266**(+)**0.284**|0.108 0.118 (+) 0.147|0.000 0.006 0.068|
|DTLZ6<br>DTLZ7|0.737 0.797 (+) 0.831<br>0.000 0.000 (_≈_) 0.000|0.731 0.790 (+) 0.847<br>0.000 0.000 (_≈_) 0.000|**0.751 0.801**(+)**0.834**<br>**0.069 0.070**(+)**0.104**|0.366 0.415 0.587<br>0.000 0.000 0.000|



295 the adaptive acquisition function. On DTLZ1-3, DTLZ1a, DTLZ3a as well as DTLZ6, both the IGD and HV metrics suggest that AS-MOEA has achieved significant improvements over RVEA as the adaptive AF utilizing a nonlinear aggregation function to take both the uncertainty and the predicted mean fitness value into account. Since the maintenance of a good distribution of solutions 300 is highly desirable on DTLZ4, the approximate PF obtained by AS-MOEA is no worse than that obtained by RVEA with the limited function evaluations. These results together confirm the effectiveness of the suggested adaptive AF. 

From the above comparative results, we can conclude that the combination of the adaptive AF and the adaptive sampling selection criterion are helpful to 305 achieve diverse and converged solutions using a limited number of real fitness evaluations. In addition, AB-MOEA significantly outperforms RVEA on all the benchmark functions in terms of the IGD metric. A similar conclusion can be drawn on the results in terms of the HV values, as presented in Table 2. All results presented in Tables 1 and 2 provide strong evidence confirming that both 

310 the adaptive AF and the new sampling selection criterion are able to improve the quality of solutions, and a combination of these two can further contribute to performance improvement. 

20 

###### _4.4.2. Comparison with Surrogate-assisted MOEAs_ 

Table 3: Statistical results of the IGD values obtained by K-RVEA, MOEA/D-EGO, SMSEGO, and AB-MOEA with the same number of real function evaluations 

|Test problem||K-RV|EA||M|OEA/|D-EGO||SMS-|EGO||A|B-MOE|A|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
||min|me|an|max|min|me|an<br>max|min|mea|n|max|min|mean|max|
|DTLZ1|**13.56**|28.46|(_≈_)|45.85|18.52|38.82|(+) 57.98|25.31|35.14|(+)|**40.04**|16.58|**27.29**|52.88|
|DTLZ1a|0.58|1.68|(_≈_)|2.72|1.21|7.60|(+) 22.16|**0.07 **|**1.15**|(_≈_)|7.58|0.35|1.47|**2.70**|
|DTLZ2|0.13|0.18|(+)|0.24|0.36|0.42|(+) 0.48|0.23|0.29|(+)|0.34|**0.09**|**0.09 **|**0.17**|
|DTLZ3|214.3|355.0|(+)|430.9|225.8|253.8|(+) 401.6|204.7|**219.7**|(–)|**239.0**|**199.0**|310.8|420.7|
|DTLZ3a|31.41|77.06|(+)|212.4|121.6|250.7|(+) 398.6|**2.41**|36.08|(_≈_)|132.5|**17.05**|**30.65**|58.97|
|DTLZ4|0.30|0.47|(_≈_)|0.69|0.50|0.70|(+) 0.82|0.65|0.91|(+)|1.04|**0.23**|**0.43 **|**0.68**|
|DTLZ5|0.10|0.15|(+)|0.25|0.28|0.34|(+) 0.42|0.07|0.12|(+)|0.20|**0.06**|**0.09 **|**0.19**|
|DTLZ6|3.96|4.60|(_≈_)|5.58|**0.74 **|**3.04**|(–) **4.56**|3.69|4.66|(_≈_)|5.61|3.83|4.60|5.56|
|DTLZ7|1.00|4.28|(+)|9.66|2.61|6.57|(+) 8.87|0.59|1.33|(+)|1.78|**0.58**|**0.81 **|**1.40**|
|UF1|0.09|0.12|(+)|0.17|0.14|0.23|(+) 0.37|0.07|0.14|(+)|0.53|**0.09**|**0.09 **|**0.10**|
|UF2|0.06|0.08|(+)|0.14|0.13|0.18|(+) 0.24|**0.05**|0.07|(_≈_)|**0.10**|0.06|**0.06**|0.07|
|UF3|0.56|0.84|(+)|1.07|0.61|0.94|(+) 1.35|0.86|1.01|(+)|1.16|**0.34**|**0.48 **|**0.65**|
|UF4|0.09|0.10|(–)|0.12|0.09|0.11|(–) **0.12**|**0.07 **|**0.10**|(–)|0.12|0.14|0.16|0.18|
|UF5|0.72|1.32|(+)|2.62|2.04|2.85|(+) 4.08|0.61|1.53|(+)|2.06|**0.47**|**0.70 **|**1.08**|
|UF6|0.82|1.24|(+)|2.02|1.14|1.84|(+) 2.76|1.01|1.23|(+)|1.59|**0.82**|**1.06 **|**1.24**|
|UF7|0.88|1.24|(+)|1.47|0.14|0.29|(+) 0.57|0.07|0.11|(+)|0.38|**0.07**|**0.09 **|**0.11**|



In this subsection, the performance of the proposed AB-MOEA is compared 

315 with the state-of-the-art Bayesian SAEAs, including K-RVEA, MOEA/D-EGO, and SMS-EGO, in terms of IGD, HV, GD and spread metrics. Table 3 and Table 4 present comparative results of IGD and HV, respectively. To evaluate the diversity and convergence separately, GD and spread metrics are calculated on part of the test problems and the results are presented in Table 5 and Table 320 6, respectively. The best one of each instance is highlighted. To further illustrate the advantage of the proposed algorithm, the non-dominated solution set obtained by each of the four compared algorithms (in the run that achieved the medium performance out of 20 independent runs) on DTLZ2 and DTLZ7 are visualized in Figs. 4-5. From the results, we can clearly see the better 325 performance of the proposed algorithm. 

21 

Table 4: Statistical results of the HV values obtained by K-RVEA, MOEA/D-EGO, SMSEGO, and AB-MOEA with the same number of real function evaluations 

|Test problem|K-RVEA<br>|M<br>|OEA/D-EGO||SMS-E|GO|A<br>|B-MO|EA|
|---|---|---|---|---|---|---|---|---|---|
||min<br>mean<br>max|min|mean<br>max|min|mea|n<br>max|min|mean|max|
|DTLZ1|0.930 0.962 (+) 0.989|0.982|0.983 (+) 0.983|**0.991**|0.992|(+) 0.994|0.971|**0.993**|**0.995**|
|DTLZ1a|0.936 0.975 (+) 0.993|0.246|0.513 (+) 0.781|**0.999**|**1.000**|(–) **1.000**|0.973|0.992|0.998|
|DTLZ2|0.262 0.340 (+) 0.438|0.104|0.124 (+) 0.144|0.215|0.304|(+) 0.393|**0.350**|**0.444**|**0.488**|
|DTLZ3|0.858 0.900 (+) 0.933|0.870|0.925 (+) 0.979|**0.981**|**0.984**|(–) **0.986**|0.862|0.921|0.957|
|DTLZ3a|0.000 0.373 (+) 0.743|0.000|0.000 (+) 0.000|**0.822**|0.844|(_≈_) 0.865|0.403|**0.855**|**0.979**|
|DTLZ4|0.000 0.050 (_≈_) 0.174|0.007|0.015 (+) 0.022|0.000|0.000|(+) 0.000|**0.009**|**0.063**|**0.201**|
|DTLZ5|0.009 0.068 (+) 0.108|0.000|0.001 (+) 0.002|0.108|0.112|(_≈_) 0.116|**0.108**|**0.118**|**0.147**|
|DTLZ6|0.678 0.792 (_≈_) 0.849|**0.875**|**0.878** (–) **0.882**|0.732|0.803|(_≈_) 0.874|0.751|0.801|0.834|
|DTLZ7|0.000 0.014 (+) 0.089|0.000|0.000 (+) 0.000|0.066|0.066|(+) 0.087|**0.069**|**0.070**|**0.104**|
|UF1|0.49 0.56 (+) 0.59|0.26|0.40 (+) 0.51|0.02|0.53|(+) 0.61|**0.55**|**0.57**|**0.58**|
|UF2|0.60 0.62 (+) 0.64|0.38|0.47 (+) 0.53|0.60|0.63|(_≈_) 0.66|**0.63**|**0.64**|**0.65**|
|UF3|0.00 0.03 (+) 0.13|0.00|0.01 (+) 0.05|0.00|0.00|(+) 0.01|**0.07**|**0.18**|**0.29**|
|UF4|0.27 0.30 (–) 0.31|0.27|0.29<br>(–)<br>0.31|**0.27**|**0.30**|(–) **0.33**|0.21|0.22|0.25|
|UF5|0.00 0.00 (+) 0.02|0.00|0.00 (+) 0.00|0.00|0.00|(+) 0.01|0.00|**0.03**|**0.14**|
|UF6|0.18 0.39 (+) 0.48|0.03|0.21 (+) 0.34|0.30|0.42|(+) 0.49|**0.64**|**0.79**|**0.89**|
|UF7|0.00 0.00 (+) 0.00|0.08|0.24 (+) 0.38|0.28|0.43|(+) 0.48|**0.42**|**0.46**|**0.48**|





Table 5: Statistical results of the GD values obtained by K-RVEA, MOEA/D-EGO, SMSEGO, and AB-MOEA with the same number of real function evaluations 

|Test problem||K-RV|EA|M<br>|OEA/|D-EG|O||SMS-|EGO||A<br>|B-MO|EA|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
||min|mea|n<br>max|min|mea|n|max|min|me|an|max|min|mean|max|
|DTLZ1a|3.52|9.32|(+) 16.05|14.91|31.38|(+)|55.33|**0.01**|13.27|(_≈_)|49.39|2.64|**3.65**|**4.86**|
|DTLZ2|0.01|0.03|(+) 0.04|0.07|0.11|(+)|0.14|**0.01**|0.06|(+)|0.12|0.02|**0.04**|**0.10**|
|DTLZ3a|38.09|64.72|(+) 102.15|127.19|166.70|(+)|215.85|24.91|**69.75**|(_≈_)|**111.23**|**12.37**|78.13|114.98|
|DTLZ7|0.18|1.55|(+) 2.63|1.55|1.77|(+)|2.44|**0.01**|0.66|(+)|4.91|0.15|**0.31**|**0.83**|
|UF2|0.004|0.010|(_≈_) 0.02|0.04|0.07|(+)|0.11|0.01|0.01|(+)|0.05|**0.006**|**0.009 **|**0.014**|
|UF4|0.016|**0.020**|(–) **0.023**|0.019|0.024|(–)|0.027|**0.015**|0.025|(–)|0.035|0.027|0.032|0.036|
|UF6|0.429|0.75|(+) 1.59|0.78|1.24|(+)|2.09|0.43|0.61|(+)|1.57|**0.36**|**0.55**|**1.10**|
|UF7|**0.008**|0.03|(+) 0.11|0.03|0.16|(+)|0.40|0.02|0.07|(+)|0.26|0.009|**0.014 **|**0.029**|



22 

Table 6: Statistical results of the spread values obtained by K-RVEA, MOEA/D-EGO, SMSEGO, and AB-MOEA with the same number of real function evaluations 

|Test problem|min|K-RV<br>mea|EA<br>n<br>max|MOEA/D-EGO<br>min<br>mean<br>max|min|SMS-E<br>mea|GO<br>n<br>max|AB-MOE<br>min<br>mean|A<br>max|
|---|---|---|---|---|---|---|---|---|---|
|DTLZ1a|0.663|1.213|(_≈_) 1.787|0.528 1.058 (_≈_) 1.465|**0.439**|1.096|(_≈_) 1.853|0.883 **0.995**|**1.110**|
|DTLZ2|**0.470**|**0.594**|(+)**0.699**|0.587 0.759 (_≈_) 0.961|0.700|0.909|(+) 1.080|0.545 0.777|1.129|
|DTLZ3a|0.580|0.848|(+) 1.214|0.560 0.755 (+)**0.960**|0.711|1.064|(_≈_) 1.655|**0.225 0.611**|1.563|
|DTLZ7|0.789|1.006|(_≈_) 1.178|0.773**0.883**(+)**0.986**|**0.335**|1.213|(_≈_) 5.429|0.821 1.032|1.346|
|UF2|0.595|0.780|(+) 0.931|0.547 0.859 (+) 1.235|**0.319**|0.833|(+) 1.128|0.533 **0.700**|**0.970**|
|UF4|0.575|0.708|(_≈_) 0.859|0.453 0.649 (_≈_) 0.852|**0.453**|**0.626**|(_≈_) 0.848|0.538 0.680|**0.810**|
|UF6<br>UF7|0.780 <br>0.673|1.059 <br> 0.996|(+) 1.881<br> (+) 1.340|0.648 1.007 (+) 1.429<br>0.666 0.968 (+) 1.516|0.707 <br>**0.441**|0.884 <br> 0.908|(_≈_)**1.106**<br> (_≈_) 1.681|**0.707 0.873** <br>0.596 **0.795**|1.174<br>**1.046**|











<!-- Start of picture text -->
(a) The non-dominated solutions obtained (b) The non-dominated solutions obtained<br><!-- End of picture text -->





Figure 4: Visualization of the non-dominated solutions obtained by the four compared algorithms on DTLZ2. 

23 





<!-- Start of picture text -->
(c) The non-dominated solutions obtained<br>by K-RVEA<br><!-- End of picture text -->



<!-- Start of picture text -->
(b) The non-dominated solutions obtained<br><!-- End of picture text -->



Figure 5: Visualization of the non-dominated solutions obtained by the four compared algorithms on DTLZ7. 

The statistical results in terms of IGD values obtained by the four algorithms are summarized in Table 3. For the three-objective benchmarks, it is apparent that AB-MOEA has achieved the best approximate PF on all test problems except for DTLZ3 (SMS-EGO obtained the best IGD values) and 330 DTLZ6 (MOEA/D-EGO obtained the best IDG values). The reason behind this may be that DTLZ3 has a multimodal fitness landscape, and DTLZ6 has a plenty of disconnected Pareto optimal regions in the decision space. Actually, in our experiments, all algorithms failed to converge to the PF on DTLZ3 and 

24 

DTLZ6 due to the limited budget of function evaluations. For the bi-objective 335 test suite, we can clearly see that the IGD results obtained by AB-MOEA are much better than the compared algorithms on all UF test problems except on UF4. According to the Wilcoxon rank sum test, the proposed algorithm significantly outperforms the compared algorithms on most of the test problems. 

Similar conclusions can be drawn from the results given in Table 4. From 340 these results, we can see that AB-MOEA performs much better than K-RVEA on all three-objective benchmark problems considered in this work but DTLZ4 and DTLZ6, on which AB-MOEA and K-RVEA perform comparably. MOEA/DEGO is able to achieve well converged and evenly distributed final solutions on DTLZ6; however, its performance on the rest of problems is much worse than 

345 AB-MOEA. Regarding the bi-objective benchmarks, the best results of HV on UF1-UF3 and UF5-UF7 are obtained by AB-MOEA. It is worthy of noting that SMS-EGO outperforms AB-MOEA on DTLZ1a, DTLZ3 and UF4 in terms of the HV metric. Note, however, that SMS-EGO is very time-consuming [29]. In conclusion, the proposed algorithm shows the best overall performance. 

350 To further verify the performance of AB-MOEA, two performance indicators, GD and spread metrics are adopted to investigate the convergence and diversity of the four algorithms. Since the algorithms failed to converge to the PF on some of the benchmarks due to the limited evaluation budget, we select some of them to examine the convergence and diversity performance sep355 arately. As listed in 5, AB-MOEA obtains the best GD values compared to other three algorithms on a vast majority of the test problems, confirming the better performance indicated by IGD and HV values. On the other hand, the values of the spread metrics given in 6 indicate that AB-MOEA shows certain advantages over MOEA/D-EGO and K-RVEA concerning the diversity of the 360 obtained solutions. Note that SMS-EGO also shows competitive diversity performance; however, it is significantly outperformed by AB-MOEA with respect to the convergence performance. 

25 

###### **5. A Case Study on Airfoil Design** 

To verify the performance of the proposed algorithm on real-world opti365 mization problems, we compare AB-MOEA, K-RVEA and Bayesian optimization (BO) on a transonic airfoil design optimization problem. It is noted that time-consuming computational fluid dynamics (CFD) simulations are required to evaluate the performance of an airfoil design, which is therefore a computationally expensive optimization problem and a limited budget of evaluations 370 (here, 300 evaluations) is affordable. In the following, a brief introduction to the problem is given and then the simulation results are presented. 

We consider an airfoil design problem based on the RAE2822 airfoil test case from the GARTEUR AG52 project [25]. Here, 14 points of a nonrational B-spline (NURBS) are used to control the curvature of the upper and lower 375 surfaces of the airfoil, then CFD simulations are carried out to calculate the drag and lift coefficients ( _Cd_ and _Cl_ ) for any given geometry of the airfoil. We aim to optimize the geometry of the airfoil to minimize the drag coefficient and maximize the lift 

We compare AB-MOEA with K-RVEA and BO [37] in terms of IGD and HV. 380 Each algorithm is run for ten times on the airfoil design problem and the mean values of HV and IGD are presented in Table 7. Note that in calculating IGD, the reference set is the non-dominated solution set of all solutions obtained by three compared algorithms. The non-dominated solution set obtained by each algorithm is also visualized in Fig. 6. From Table 7 and Fig. 6, we can see 385 that the proposed algorithm has also achieved the best results on the real-world design problem. 

Table 7: The mean values of HV and IGD obtained by AB-MOEA, BO, K-RVEA on the airfoil design problem. 

|Algorithm|HV|IGD|
|---|---|---|
|AB-MOEA|**0.0423**|**0.0328**|
|BO|0.0407|0.0389|
|K-RVEA|0.0348|0.0402|



26 



<!-- Start of picture text -->
0.8 PF obtained by AB-MOEA 0.8 PF obtained by BO<br>0.7 0.7<br>0.6 0.6<br>0.5 0.5<br>0.4 0.4<br>0.3 0.3<br>0.2 0.2<br>0.1 0.1<br>0 0<br>0 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 0 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9<br>f1 f1<br>(a) The non-dominated solutions obtained (b) The non-dominated solutions obtained<br>by AB-MOEA by BO<br>0.7 PF obtained by K-RVEA<br>0.6<br>0.5<br>0.4<br>0.3<br>0.2<br>0.1<br>0<br>0 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9<br>f1<br>(c) The non-dominated solutions obtained<br>by K-RVEA<br>f2 f2<br>f2<br><!-- End of picture text -->

Figure 6: The obtained non-dominated solutions on the airfoil design problem. 

###### **6. Conclusion** 

Surrogate-assisted evolutionary algorithms have shown great promises to solve expensive multi-objective optimization problems. However, the limited budget of function evaluations requires that the algorithm is able to quickly 390 converge while ensuring a diverse distribution of the obtained solutions. Therefore, it is highly demanded to design SAEAs that can achieve an optimal balance between exploration and exploitation. For this purpose, we proposed an adaptive Bayesian approach to surrogate-assisted evolutionary algorithm to improve 

27 

the efficiency in solving expensive MOPs. Taken both the diversity and conver395 gence into account, an adaptive acquisition function is designed by adjusting the weights of the uncertainty and the mean objective value in the acquisition function on top of an adaptive sampling selection criterion that can better balance diversity and convergence. The effectiveness of the introduced strategies and the performance of the proposed algorithm are investigated on a set of 400 widely used benchmark problems and an airfoil design optimization problem. Our results demonstrate that the proposed algorithm significantly outperforms the compared algorithms on most test problems and is also able to achieve better performance on the airfoil design problem. 

Although the proposed algorithm is competitive for solving most test prob405 lems used in our experiments, we find that the proposed algorithm suffers from slow convergence when solving DTLZ1, DTLZ3 and UF6. This might be attributed to the poor prediction quality of GP models due to the strong ruggedness of the fitness landscape. Consequently, future research could investigate the use of multiple surrogate models and more sophisticated methods for es- 

- 410 timating the uncertainty. In addition, new acquisition functions are desirable when dealing with MOPs whose objective functions and / or constraints have very different computational complexities. 

###### **Acknowledgments** 

- The authors are grateful to Dr Handing Wang for her assistance in testing the 

- 415 algorithms on the airfoil design problem. The work was supported in part by a Royal Society International Exchanges Program under No. IEC _\_ NSFC _\_ 170279. 

###### **References** 

420 

- [1] R. T. Marler, J. S. Arora, Survey of multi-objective optimization methods for engineering, Structural and multidisciplinary optimization 26 (6) (2004) 369–395. 

28 

   - [2] W. Saad, Z. Han, M. Debbah, A. Hjorungnes, T. Basar, Coalitional game theory for communication networks, IEEE Signal Processing Magazine 26 (5) (2009) 77–97. 

- [3] E. E. Tsiropoulou, P. Vamvakas, G. K. Katsinis, S. Papavassiliou, Com- 

- 425 bined power and rate allocation in self-optimized multi-service two-tier femtocell networks, Computer Communications 72 (2015) 38–48. 

   - [4] F. A. Mohamed, H. N. Koivo, Multiobjective optimization using modified game theory for online management of microgrid, European Transactions on Electrical Power 21 (1) (2011) 839–854. 

- 430 [5] R. Meng, Y. Ye, N.-g. Xie, Multi-objective optimization design methods based on game theory, in: 2010 8th World Congress on Intelligent Control and Automation, IEEE, 2010, pp. 2220–2227. 

435 

   - [6] E. E. Tsiropoulou, P. Vamvakas, S. Papavassiliou, Joint utility-based uplink power and rate allocation in wireless networks: A non-cooperative game theoretic framework, Physical Communication 9 (2013) 299–307. 

   - [7] Y. Jin, Surrogate-assisted evolutionary computation: Recent advances and future challenges, Swarm and Evolutionary Computation 1 (2) (2011) 61– 70. 

- [8] K. Deb, A. Pratap, S. Agarwal, T. Meyarivan, A fast and elitist multiob- 

- 440 jective genetic algorithm: NSGA-II, IEEE Transactions on Evolutionary Computation 6 (2) (2002) 182–197. 

   - [9] Q. Zhang, H. Li, MOEA/D: A multiobjective evolutionary algorithm based on decomposition, IEEE Transactions on Evolutionary Computation 11 (6) (2007) 712–731. 

- 445 [10] R. Cheng, Y. Jin, M. Olhofer, B. Sendhoff, A reference vector guided evolutionary algorithm for many-objective optimization, IEEE Transactions on Evolutionary Computation 20 (5) (2016) 773–791. 

29 

   - [11] E. Zitzler, M. Laumanns, L. Thiele, SPEA2: Improving the strength pareto evolutionary algorithm, TIK-report 103. 

- 450 [12] R. Cheng, Y. Jin, K. Narukawa, B. Sendhoff, A multiobjective evolutionary algorithm using Gaussian process-based inverse modeling, IEEE Transactions on Evolutionary Computation 19 (6) (2015) 838–856. 

455 

   - [13] D. Rodriguez-Roman, A surrogate-assisted genetic algorithm for the selection and design of highway safety and travel time improvement projects, Safety Science 103 (2018) 305–315. 

   - [14] Y. Jin, B. Sendhoff, A systems approach to evolutionary multiobjective structural optimization and beyond, IEEE Computational Intelligence Magazine 4 (3) (2009) 62–76. 

- [15] A. Habib, H. K. Singh, T. Ray, A multiple surrogate assisted multi/many- 

- 460 objective multi-fidelity evolutionary algorithm, Information Sciences 502 (2019) 537–557. 

   - [16] Y. Jin, H. Wang, T. Chugh, D. Guo, K. Miettinen, Data-driven evolutionary optimization: an overview and case studies, IEEE Transactions on Evolutionary Computation 23 (3) (2018) 442–458. 

- 465 [17] B. D. Marjavaara, T. S. Lundstr¨om, T. Goel, Y. Mack, W. Shyy, Hydraulic turbine diffuser shape optimization by multiple surrogate model approximations of pareto fronts, Journal of Fluids Engineering 129 (9) (2007) 1228–1240. 

- [18] J. Zhang, A. Zhou, G. Zhang, A classification and pareto domination based 

- 470 multiobjective evolutionary algorithm, in: 2015 IEEE Congress on Evolutionary Computation (CEC), IEEE, 2015, pp. 2883–2890. 

475 

- [19] L. Pan, C. He, Y. Tian, H. Wang, X. Zhang, Y. Jin, A classification-based surrogate-assisted evolutionary algorithm for expensive many-objective optimization, IEEE Transactions on Evolutionary Computation 23 (1) (2018) 74–88. 

30 

   - [20] B. Shahriari, K. Swersky, Z. Wang, R. P. Adams, N. De Freitas, Taking the human out of the loop: A review of Bayesian optimization, Proceedings of the IEEE 104 (1) (2015) 148–175. 

- [21] J. Snoek, H. Larochelle, R. P. Adams, Practical Bayesian optimization of 

- 480 machine learning algorithms, in: Advances in Neural Information Processing Systems, 2012, pp. 2951–2959. 

   - [22] F. A. Viana, R. T. Haftka, L. T. Watson, Efficient global optimization algorithm assisted by multiple surrogate techniques, Journal of Global Optimization 56 (2) (2013) 669–689. 

- 485 [23] D. Buche, N. N. Schraudolph, P. Koumoutsakos, Accelerating evolutionary algorithms with Gaussian process fitness function models, IEEE Transactions on Systems, Man, and Cybernetics, Part C (Applications and Reviews) 35 (2) (2005) 183–194. 

- [24] N. Hoyle, N. W. Bressloff, A. J. Keane, Design optimization of a two- 

- 490 dimensional subsonic engine air intake, AIAA Journal 44 (11) (2006) 2672– 2681. 

   - [25] H. Wang, Y. Jin, J. Doherty, Committee-based active learning for surrogate-assisted particle swarm optimization of expensive problems, IEEE Transactions on Cybernetics 47 (9) (2017) 2664–2677. 

- 495 [26] J. Tian, Y. Tan, J. Zeng, C. Sun, Y. Jin, Multi-objective infill criterion driven Gaussian process assisted particle swarm optimization of highdimensional expensive problems, IEEE Transactions on Evolutionary Computation 23 (3) (2019) 459–472. 

- [27] J. Knowles, ParEGO: a hybrid algorithm with on-line landscape approx- 

- 500 imation for expensive multiobjective optimization problems, IEEE Transactions on Evolutionary Computation 10 (1) (2006) 50–66. 

31 

   - [28] B. Naujoks, N. Beume, M. Emmerich, Metamodel-assisted SMS-EMOA applied to airfoil optimization tasks, in: Proceedings EUROGEN, Vol. 5, 2005. 

- 505 [29] Q. Zhang, W. Liu, E. Tsang, B. Virginas, Expensive multiobjective optimization by MOEA/D with Gaussian process model, IEEE Transactions on Evolutionary Computation 14 (3) (2009) 456–474. 

- [30] T. Chugh, Y. Jin, K. Miettinen, J. Hakanen, K. Sindhya, A surrogateassisted reference vector guided evolutionary algorithm for computationally 

- 510 expensive many-objective optimization, IEEE Transactions on Evolutionary Computation 22 (1) (2018) 129–142. 

   - [31] D. Guo, Y. Jin, J. Ding, T. Chai, Heterogeneous ensemble-based infill criterion for evolutionary multiobjective optimization of expensive problems, IEEE Transactions on Cybernetics 49 (3) (2018) 1012–1025. 

- 515 [32] C. E. Rasmussen, Gaussian processes in machine learning, in: Summer School on Machine Learning, Springer, 2003, pp. 63–71. 

   - [33] D. R. Jones, M. Schonlau, W. J. Welch, Efficient global optimization of expensive black-box functions, Journal of Global Optimization 13 (4) (1998) 455–492. 

- 520 [34] D. Zhan, Y. Cheng, J. Liu, Expected improvement matrix-based infill criteria for expensive multiobjective optimization, IEEE Transactions on Evolutionary Computation 21 (6) (2017) 956–975. 

525 

- [35] J. M. Hern´andez-Lobato, M. W. Hoffman, Z. Ghahramani, Predictive entropy search for efficient global optimization of black-box functions, in: Advances in Neural Information Processing Systems, 2014, pp. 918–926. 

- [36] N. Srinivas, A. Krause, S. M. Kakade, M. Seeger, Gaussian process optimization in the bandit setting: No regret and experimental design (2010) 1015–1022. 

32 

- [37] J. Liu, Z. Han, W. Song, Comparison of infill sampling criteria in kriging- 

- 530 based aerodynamic optimization, in: 28th Congress of the International Council of the Aeronautical Sciences, 2012, pp. 23–28. 

535 

   - [38] R. Cheng, T. Rodemann, M. Fischer, M. Olhofer, Y. Jin, Evolutionary many-objective optimization of hybrid electric vehicle control: From general optimization to preference articulation, IEEE Transactions on Emerging Topics in Computational Intelligence 1 (2) (2017) 97–111. 

   - [39] M. Emmerich, N. Beume, B. Naujoks, An EMO algorithm using the hypervolume measure as selection criterion, in: International Conference on Evolutionary Multi-Criterion Optimization, Springer, 2005, pp. 62–76. 

- [40] M. T. Emmerich, K. C. Giannakoglou, B. Naujoks, Single-and multiob- 

- 540 jective evolutionary optimization assisted by gaussian random field metamodels, IEEE Transactions on Evolutionary Computation 10 (4) (2006) 421–439. 

   - [41] J. Hensman, N. Fusi, N. D. Lawrence, Gaussian processes for big data, in: Conference on Uncertainty in Artificial Intelligence, 2013, pp. 282–290. 

- 545 [42] K. Deb, L. Thiele, M. Laumanns, E. Zitzler, Scalable multi-objective optimization test problems, in: Proceedings of the 2002 Congress on Evolutionary Computation. CEC’02, Vol. 1, IEEE, 2002, pp. 825–830. 

550 

   - [43] Q. Zhang, A. Zhou, S. Zhao, P. N. Suganthan, W. Liu, S. Tiwari, Multiobjective optimization test instances for the CEC 2009 special session and competition, Tech. rep. (2008). 

   - [44] C. Yang, J. Ding, Y. Jin, T. Chai, Off-line data-driven multi-objective optimization: Knowledge transfer between surrogates and generation of final solutions, IEEE Transactions on Evolutionary Computation. 

- [45] Q. Zhang, A. Zhou, Y. Jin, RM-MEDA: A regularity model-based multi- 

- 555 objective estimation of distribution algorithm, IEEE Transactions on Evolutionary Computation 12 (1) (2008) 41–63. 

33 

   - [46] L. While, P. Hingston, L. Barone, S. Huband, A faster algorithm for calculating hypervolume, IEEE Transactions on Evolutionary Computation 10 (1) (2006) 29–38. 

- 560 [47] D. A. Van Veldhuizen, G. B. Lamont, Multiobjective evolutionary algorithm research: A history and analysis, Tech. rep., Citeseer (1998). 

   - [48] Y.-N. Wang, L.-H. Wu, X.-F. Yuan, Multi-objective self-adaptive differential evolution with elitist archive and crowding entropy-based diversity measure, Soft Computing 14 (3) (2010) 193. 

- 565 [49] Y. Tian, R. Cheng, X. Zhang, Y. Jin, PlatEMO: A MATLAB platform for evolutionary multi-objective optimization, IEEE Computational Intelligence Magazine 12 (4) (2017) 73–87. 

   - [50] S. N. Lophaven, H. B. Nielsen, J. Sondergaard, DACE - A Matlab Kriging Toolbox, 2002. 



34 

## **_Confl icts of Interest Statement_** 

**Manuscript title:** **~~An Adaptive Bayesian Approach to Surrogate-Assisted Evolutionary Multi-objective Optimization~~** 570 

The authors whose names are listed immediately below certify that they have NO affi liations with or involvement in any organization or entity with any fi nancial interest (such as honoraria; educational grants; participation in speakers’ bureaus; membership, employment, consultancies, stock ownership, or other equity interest; and expert testimony or patent-licensing arrangements), or non-fi nancial interest (such as personal or professional relationships, affi liations, knowledge or beliefs) in the subject matter or materials discussed in this manuscript. 



###### **Author names:** 

The authors whose names are listed immediately below report the following details of affi liation or involvement in an organization or entity with a fi nancial or non-fi nancial interest in the subject matter or materials discussed in this manuscript. Please specify the nature of the confl ict on a separate sheet of paper if the space below is inadequate. 

**Author names:** 



**This statement is signed by all the authors to indicate agreement that the above information is true and correct** ( _a photocopy of this form may be used if there are more than 10 authors_ ): 

Author's name (typed) Author's signature Date Yaochu Jin 29/08/2019 





###### **Credit Author Statement** 

**Xilu Wang** has developed and implemented of the algorithm, performed the experiments and written the draft of the paper. 

575 **Yaochu Jin** has contributed to the conceptualization of the research, development of the algorithm, design of the experiments, and write-up of the paper. **Sebastian Schmitt and Markus Olhofer** have contributed to the concelptualization of the reseach, discussed the ideas of the algorithms and commented 

on the earlier versions of the paper. 

37 




---

## ANEXO — Camada de texto completa do PDF (get_text)

> Reprodução integral da camada de texto do PDF (todas as páginas, ordem de leitura bruta). Inclui tabelas de resultados e equações que a conversão estruturada acima pode ter omitido. Garante completude textual (imagens continuam omitidas).


<!-- página 1 -->

Honda Research Institute Europe GmbH
https://www.honda-ri.de/
An Adaptive Bayesian Approach to Surrogate-
Assisted Evolutionary Multi-objective
Optimization
Xilu Wang, Yaochu Jin, Sebastian Schmitt, Markus
Olhofer
2020
Preprint:
This is an accepted article published in Information Sciences. The final
authenticated version is available online at:
https://doi.org/10.1016/j.ins.2020.01.048
Powered by TCPDF (www.tcpdf.org)


<!-- página 2 -->

 
An Adaptive Bayesian Approach to Surrogate-Assisted Evolutionary Multi-objective Optimization
Journal Pre-proof
An Adaptive Bayesian Approach to Surrogate-Assisted Evolutionary
Multi-objective Optimization
Xilu Wang, Yaochu Jin, Sebastian Schmitt, Markus Olhofer
PII:
S0020-0255(20)30059-1
DOI:
https://doi.org/10.1016/j.ins.2020.01.048
Reference:
INS 15179
To appear in:
Information Sciences
Received date:
3 September 2019
Revised date:
21 January 2020
Accepted date:
28 January 2020
Please cite this article as: Xilu Wang, Yaochu Jin, Sebastian Schmitt, Markus Olhofer, An Adaptive
Bayesian Approach to Surrogate-Assisted Evolutionary Multi-objective Optimization, Information Sci-
ences (2020), doi: https://doi.org/10.1016/j.ins.2020.01.048
This is a PDF ﬁle of an article that has undergone enhancements after acceptance, such as the addition
of a cover page and metadata, and formatting for readability, but it is not yet the deﬁnitive version of
record. This version will undergo additional copyediting, typesetting and review before it is published
in its ﬁnal form, but we are providing this version to give early visibility of the article. Please note that,
during the production process, errors may be discovered which could affect the content, and all legal
disclaimers that apply to the journal pertain.
© 2020 Published by Elsevier Inc.


<!-- página 3 -->

An Adaptive Bayesian Approach to Surrogate-Assisted
Evolutionary Multi-objective Optimization
Xilu Wanga, Yaochu Jina,∗, Sebastian Schmittb, Markus Olhoferb
aDepartment of Computer Science, University of Surrey, Guildford, GU2 7XH, U.K.
bHonda Research Institute Europe GmbH, Carl-Legien-Strasse 30, D-63073
Oﬀenbach/Main, Germany
Abstract
Surrogate models have been widely used for solving computationally expensive
multi-objective optimization problems (MOPs). The eﬃcient global optimiza-
tion (EGO) algorithm, a Bayesian approach to surrogate-assisted optimization,
has become very popular in surrogate-assisted evolutionary optimization. In
this paper, we propose an adaptive Bayesian approach to surrogate-assisted
evolutionary algorithm to solve expensive MOPs. The main idea is to tune the
hyperparameter in the acquisition function according to the search dynamics to
determine which candidate solutions are to be evaluated using the expensive real
objective functions. In addition, the sampling selection criterion switches be-
tween an angle based distance and an angle-penalized distance over the course of
optimization to achieve a better balance between exploration and exploitation.
The performance of the proposed algorithm is examined on a set of benchmark
problems and an airfoil design optimization problem using a maximum of 300
real ﬁtness evaluations. Our experimental results show that the proposed al-
gorithm is competitive compared to four popular multi-objective evolutionary
algorithms.
Keywords:
Expensive multi-objective optimization, surrogate-assisted
evolutionary algorithm, Bayesian optimization, acquisition function, reference
∗Corresponding author.
Email addresses: xw00616@surrey.ac.uk (Xilu Wang), yaochu.jin@surrey.ac.uk
(Yaochu Jin), sebastian.schmitt@honda-ri.de (Sebastian Schmitt),
Markus.Olhofer@honda-ri.de (Markus Olhofer)
Preprint submitted to Information Sciences
January 29, 2020
         
         


<!-- página 4 -->

vectors
1. Introduction
Multi-objective optimization problems (MOPs) are commonly seen in many
economic, scientiﬁc, and engineering applications. Various types of algorithms
have been proposed for solving MOPs.
For example, the scalarization tech-
nique is one popular method that converts an MOP into a single-objective
5
optimization problem, which can be achieved by the global criterion method,
the weighted min-max method, the ϵ-constraint method, normal boundary in-
tersection or reference point methods [1]. In addition, game theory has been
applied to many real-world MOPs, such as wireless and communication net-
works [2, 3] and electric systems [4], due to the similarity between MOPs and
10
the game [5]. For example, power optimization for a microgrid is deﬁned as a
bi-objective optimization [4]. Two players are assumed to correspond to two
objectives, and consequently a modiﬁed game theory is adopted to ﬁnd an opti-
mal solution. Tsiropoulou et al.
adopted the non-cooperative game theory to
eﬃciently allocate transmission power and data rate to users in the uplink of a
15
cellular wireless network [6]. Another popular approach is based on evolution-
ary algorithms (EAs), which have been applied successfully to many real-world
complex optimization problems [7]. Since they are population-based methods
that are able to obtain multiple Pareto optimal solutions in a single run, EAs
are particularly well suited for MOPs. Over the past decades, a large number of
20
multi-objective evolutionary algorithms (MOEAs) have been proposed, such as
nondominated sorting genetic algorithm II (NSGA-II) [8], multi-objective evo-
lutionary algorithm based on decomposition (MOEA/D) [9], reference vector
guided evolutionary algorithm (RVEA) [10], strength Pareto evolutionary algo-
rithm 2 (SPEA2) [11], and an estimation of distribution algorithm (IM-MOEA)
25
[12], just to name a few.
However, a major criticism against MOEAs is that most of them require a
large number of function evaluations to ﬁnd Pareto optimal solutions.
This
2
         
         


<!-- página 5 -->

weakness becomes more obvious when EAs are employed for solving time-
consuming multi-objective problems where the evaluation of the objectives in-
30
volves expensive physical experiments or computationally intensive numerical
simulations. This class of problems is common in real-world applications [13],
where, e.g., computationally intensive computational ﬂuid dynamics (CFD) sim-
ulations must be conducted to evaluate the performance in structural design
optimization [14] and in engineering design optimization [15].
35
To address the challenges in using MOEAs for computationally expensive
optimization problems, surrogate-assisted evolutionary algorithms (SAEAs) are
widely adopted [16]. SAEAs can be roughly classiﬁed into two categories. In the
ﬁrst category, the expensive objective function is approximated by a single or
an ensemble of surrogates. More speciﬁcally, computationally eﬃcient surrogate
40
models are constructed using historical data and then used to approximate the
ﬁtness values of the candidate solutions instead of computing the real ﬁtness.
For example, Marjavaara [17] replaced the three-dimensional models of the dif-
fuser geometries with a surrogate model and achieved better performance in
the diﬀuser shape design problem. In the second category, the surrogate works
45
as a classiﬁer to ﬁlter the newly generated candidate solutions based on the
predicted labels. Consequently, several classiﬁcation-based SAEAs have been
developed, e.g., the classiﬁcation and Pareto domination based MOEA [18] and
the classiﬁcation-based SAEA (CSEA)[19].
The commonly used surrogate models include the radial basis function (RBF),
50
support vector machines (SVM), radial basis function networks (RBFN), poly-
nomial regression, and Gaussian processes (GPs), also called Kriging model.
Among them, GP is one of the most popular surrogate models and has at-
tracted increasing attention. The main reason is that GP can not only predict
the objective value of a candidate solution, but also provide a conﬁdence level (a
55
degree of uncertainty) of its predictions [20]. Based on the predicted objective
value and its uncertainty, an acquisition function (AF) can be utilized as the
model management strategy to determine which candidate solutions should be
evaluated by the real objective function. Surrogate-assisted optimization using
3
         
         


<!-- página 6 -->

a GP in combination with an acquisition function (also known as inﬁll criterion)
60
is called Bayesian optimization [21] or eﬃcient global optimization (EGO) [22].
The Bayesian optimization approach, which combines GPs with an acquisi-
tion function, have been widely adopted in SAEAs for handling various expen-
sive single-objective optimization problems. For example, in [23] the GP model
was used as an inexpensive ﬁtness function to accelerate convergence, and dif-
65
ferent aggregations of the predicted function value and the predicted standard
deviation of the GP were employed as acquisition functions to balance explo-
ration with exploitation. Hoyle et al. adopted a GP model to predict objective
function values when optimizing the design of engine air intakes, new data points
are then chosen based on the expected improvement function, after ﬁnding a
70
promising location, a local exploration is performed to speed up the conver-
gence [24]. In [25], a particle swarm optimization algorithm switches between
a local ensemble surrogate model and a global one, interleavingly searching for
the best and most uncertain solutions. The algorithm has been shown to per-
form well on both a set of single-objective test problems and an airfoil design
75
problem. Tian et al. [26] considered the uncertainty and the approximated ﬁt-
ness provided by the GP as two separate objectives instead of combining them
into a scalar acquisition function, which was demonstrated to be competitive
for solving high-dimensional single-objective optimization problems.
Nevertheless, it is non-trivial to build eﬀective surrogate models and select
80
new data samples based on the working mechanisms of the acquisition function
for accelerating convergence and promoting diversity in multi-objective opti-
mization. In [27], an algorithm termed ParEGO was proposed, where the aug-
mented Tchebycheﬀfunction is adopted to aggregate multiple objectives into a
scalar ﬁtness function so that an existing acquisition function for single-objective
85
optimization can be directly applied for surrogate management. Ponweiser et al.
[28] proposed a new Bayesian approach to multi-objective optimization (termed
SMS-EGO), in which a hypervolume based acquisition function rather than a
weighted aggregation of the objective functions is utilized to convert an MOP
into a single-objective optimization problem. However, due to the computa-
90
4
         
         


<!-- página 7 -->

tional complexity in calculating the hypervolume, SMS-EGO may become very
time-consuming as the number of objectives increases. A GP-assisted MOEA/D
was reported in [29], where a GP model is built for each subproblem so that an
acquisition function can be applied to each subproblem. In [30], Chugh et al.
introduced a Kriging-based RVEA (called K-RVEA), which combines the an-
95
gle penalized distance and the uncertainty for selecting new samples to update
the GP. Whenever diversity is needed in K-RVEA, the uncertainty is chosen
as the selection criterion by ranking the mean value of uncertainty on diﬀerent
objectives and selecting the one having the maximum averaging uncertainty.
Most surrogate-assisted MOEAs using the Bayesian approach have focused
100
on converting a multi-objective problem into a single-objective one by means of
aggregation or decomposition so that acquisition functions can be used for surro-
gate management. One exception is presented in Guo et al. [31], which suggests
to use an ensemble to replace the GP models to reduce the computational com-
plexity especially for high-dimensional problems. To the best of our knowledge,
105
no work has been reported to tune the hyperparameters in the acquisition func-
tion to achieve the best trade-oﬀbetween exploitation and exploration during
the search process, which is of pivotal importance in optimization.
The rest of this paper is organized as follows. Section 2 presents a brief
introduction to the background knowledge related to Bayesian optimization. In
110
Section 3, a pilot study to investigate the eﬃciency of each proposed strategy is
undergone and the proposed algorithm is described in detail. Numerical simula-
tions are conducted in Section 4, where the results are presented and discussed.
Finally, conclusions of this paper are drawn and future work is suggested in
Section 5.
115
2. Background
In this section, Gaussian processes and the widely used acquisition functions
are introduced at ﬁrst, followed by a review of the angle-penalized distance, the
selection criterion used in RVEA.
5
         
         


<!-- página 8 -->

2.1. Gaussian Processes
120
GP is a powerful surrogate model, which can provide a prediction for a
new data point, together with a degree of uncertainty. For example, a 1D GP
model illustrated in Fig. 1 is trained with three training data, the GP model
can then predict the mean ﬁtness and the uncertainty on any new data point.
That is, for a given x1, we can know the model’s prediction µ(x1), uncertainty
σ(x1), and the conﬁdence intervals µ(x1)±σ(x1), respectively. The uncertainty
information denotes the conﬁdence level of the prediction, which is very useful
in model management in surrogate-assisted optimization. The idea behind GPs
[32] is that there is a multivariate Gaussian distribution on Rn for any ﬁnite set
of N n-dimensional inputs X = {x1, x2, ...xN}T . Given a set of inputs x and
their associated function values y = {y1, y2, ...yN}T as the training data, a GP
model can be expressed by:
y(x) = µ + ε(x)
(1)
where µ is the mean of the stochastic process, and ε(x) is drawn from a stochastic
process with zero mean but non-zero standard deviation σ
ε(x) ∼N(0, σ2)
(2)
The correlation between the error terms of any two data points, xi and xj, heav-
ily depends on the distance between them. In general, the squared exponential
function with additional hyperparameters, rather than an Euclidean distance
function, is employed to calculate the correlation:
d(xi, xj) =
m
X
k=1
θk|xi
k −xj
k|pk
(3)
Corr(xi, xj) = exp[−d(xi, xj)]
(4)
where pk ∈(0, 1) controls the smoothness of the function in terms of the k-th
dimension, and θk > 0 denotes the importance of this dimension. When there
6
         
         


<!-- página 9 -->

are N training data, an N × N correlation matrix C will be obtained:
C =





Corr(x1, x2)
· · ·
Corr(x1, xN)
...
...
...
Corr(xN, x1)
· · ·
Corr(xN, xN)





(5)
As a result, 2N + 2 hyperparameters will determine a GP model, which can be
estimated by maximizing the following likelihood function:
ψ (θ1, ..., θN, p1, ..., pN) = −1
2
 N ln σ2 + ln det (C)

(6)
Therefore, the estimates ˆµ and ˆσ2 for the true values µ and σ will be obtained
ˆµ = 1T C−1y
1T C−11
(7)
ˆσ2 = (y −1ˆµ)T C−1(y −1ˆµ)
N
(8)
where 1 denotes a N ×1 column vector of ones. Based on the given parameters,
the GP model can predict the mean value together with a variance for a new
data point xnew,
f(xnew) = ˆµ + rT C−1(y −1ˆµ)
(9)
ˆσ(xnew)2 = ˆσ2[1 −rT C−1r + (1 −rT C−1r)2
1T C−11
]
(10)
where r = (Corr(xnew, x1), ..., Corr(xnew, xN))T presents a correlation vector
between xnew and each element xi in X.
2.2. Acquisition Function
Given a GP model trained by a set of observed data, selecting the appropriate
decision vector (a data point in the decision space) is essential for the SAEA to
125
work eﬀectively. Acquisition functions (AFs), inspired from Bayesian decision
theory, are designed as metrics for selecting the unobserved data to be evaluated
by the real expensive objective functions. AFs are computationally very cheap,
7
         
         


<!-- página 10 -->

(
)
1
m x
(
)
2
m x
(
)
3
m x
( )
( )
1
1
m
s
-
x
x
(
)
(
)
2
2
m
s
-
x
x
(
)
(
)
3
3
m
s
+
x
x
1x
2x
3x
Figure 1:
Illustration of a 1D Gaussian process with three training data points and the
predictions of the GP mean values and standard deviation values (µ(·) and σ(·)) at three
new data points (x1, x2 and x3). The solid line and the shaded area indicate the mean and
conﬁdence intervals estimated with the GP model.
and by sequentially ﬁnding its optimum we are able to guide the search towards
the optimum of the original objective function.
130
Several AFs have been proposed to select new data points utilizing the in-
formation obtained by surrogate models. Expected improvement (EI) [33] cal-
culates the expected value of the improvements beyond the best observed point,
and was extended to multi-objective optimization in [34]. Predictive entropy
search (PES) proposed in [35] is an alternative for Entropy Search (ES), mak-
135
ing use of the information theory.
The AF proposed in this work is inspired from the lower conﬁdence bound
(LCB) [36]. LCB is designed to balance the exploration and exploitation by
combining the uncertainty with the predicted objective values [37]. Intuitively,
for a minimization problem, selecting a point with the maximum amount of
uncertainty can encourage more exploratory search; however, selecting most
uncertain points only may lead to nearly random search. By contrast, we can
perform exploitative search if we pick points where the predicted mean values
8
         
         


<!-- página 11 -->

are minimum, which, however, at a higher risk of getting trapped in a local
optimum. Hence, LCB aims to strike a balance between exploration and ex-
ploitation:
LCB (x) = µ (x) −κσ (x)
(11)
where κ presents a trade-oﬀconstant.
LCB implicitly prefers points whose
predicted mean value µ is small and the corresponding standard deviation σ is
large.
2.3. Angle-penalized Distance Metric
140
The reference vector guided evolutionary algorithm (RVEA) [10] is a re-
cently proposed MOEA for solving many-objective optimization problems. In
RVEA, a set of reference vectors are predeﬁned in the objective space as the
preferred search directions that guide the search towards the Pareto front (PF).
An angle-penalized distance (APD) is designed based on the reference vectors
to determine which candidate solutions should be associated with their closest
reference vectors. More precisely, APD combines the convergence and diversity
criteria and dynamically adjusts the importance of the two criteria according
to the number of objectives and the number of generations. APD is deﬁned as
follows:
dt,i,j = (1 + P(θft,i,vt,j)) · ∥ft,i −Zmin
t
∥
(12)
Here, dt,i,j presents the APD value of the i-th solution in terms of the j-th refer-
ence vector in the t-th generation, and Zmin
t
denotes the vector of the minimal
objective values at the current generation; ∥ft,i −Zmin
t
∥denotes the translated
objective value, adopted as a convergence criterion; θft,i,vt,j represents the angle
between the objective vector ft,i and the reference vector vt,j; P(θft,i,vt,j) rep-
resents a penalty function and serves as a diversity criterion, which is deﬁned
as follows:
P(θft,i,vt,j) = M · (
t
tmax
)β · θft,i,vt,j
γvt,j
(13)
with
γvt,j = mini∈1,...,N,i̸=jθvt,i,vt,j
(14)
9
         
         


<!-- página 12 -->

where M and N represent the number of objectives and the number of reference
vectors, respectively; β is a predeﬁned parameter to control the rate of the
penalty function; γvt,j denotes the smallest angle between the reference vector
vt,j and its closest neighboring reference vector vt,i.
Typically, the original reference vectors are generated uniformly in the objec-
tive space using the simplex-lattice design method. Unfortunately, these vectors
are not suited for problems where diﬀerent objectives have very diﬀerent ranges.
Hence, a reference vector adaptation method was proposed in [10] in the follow-
ing manner:
vt+1,i =
v0,i ◦(Zmax
t
−Zmin
t
)
∥v0,i ◦(Zmax
t
−Zmin
t
)∥
(15)
where ’◦’ denotes the Hadamard product that multiplies two vectors of the same
145
size element-wise, vt+1,i denotes the i-th adapted reference vector for the t-th
generation, while v0,i represents the i-th uniformly distributed reference vector,
and Zmax
t
and Zmin
t
denote the vectors consisting the maximum and minimum
objective values obtained so far.
3. Proposed Algorithm
150
As mentioned above, Bayesian optimization has been extended to expensive
MOPs over the past years.
In this section, an adaptive Bayesian approach
to surrogate-assisted multi-objective evolutionary optimization algorithm (AB-
MOEA) is presented, and Fig. 2 gives the ﬂowchart of the proposed AB-MOEA.
155
3.1. Algorithm Framework
The framework of the proposed AB-MOEA are outlined in Algorithm 1.
The algorithm begins with sampling the objective functions for usually around
11n −1 points, where n is the dimensionality of the decision space, and then
uses these samples to train the GP model. The RVEA algorithm is executed
160
using only the surrogate models for 20 generations to obtain an optimized pop-
ulation. This optimized population is utilized to determine u new samples with
10
         
         


<!-- página 13 -->

ሺͲሻ
		ሺሻ


	¢ ሺǡሻ
ሺͲሻ



		ሺǡሻ
ሺሻ
ሺሻ
ሺ൅ͳሻൌሺሻ൅ሺȗሺሻሻ




	¢ ሺǡሻ

max ?
w
w
£


max ?
FE
FE
£



ȗሺሻ
	



Figure 2: Flowchart of AB-MOEA
the proposed adaptive acquisition function and the proposed sampling selection
criterion. The new samples are evaluated with the real objective functions and
the surrogate models are then retrained using the extended training set includ-
165
ing the new data samples. The proposed framework is intended to eﬃciently
optimize computationally expensive multi-objective optimization problems by
introducing an adaptive acquisition function and a new sampling selection cri-
terion. The adaptive acquisition function and the corresponding sampling se-
lection criterion within this framework aim to achieve a better balance between
170
diversity and convergence, which will be elaborated in the following.
3.2. Adaptive Acquisition Function
Many ideas have been suggested to adapt the Bayesian approach to MOPs,
but no work on adaptation of the AFs has been reported. In this work, an
adaptive acquisition function is proposed to dynamically adjust the weights
of the uncertainty and the predicted mean ﬁtness value, thereby achieving a
better balance between exploration and exploitation at diﬀerent search stages.
11
         
         


<!-- página 14 -->

Algorithm 1 Framework of AB-MOEA
Input: FEmax: the maximum number of real objective function evaluations; u: the number
of points selected to be re-evaluated in each iteration; wmax: the maximum number of
generations before updating GPs;
Output: The ﬁnal solution population
1: Initialization: Sample 11n −1 points x1, x2,..., x11n−1 in the decision space using the
Latin Hybercube Sampling method; evaluate the values y1,...,y11n−1 of the objective
functions on these 11n −1 points; use [X, Y] as training data ;
2: train GP models with the training data;
3: while FE ⩽FEmax do
4:
//Using the surrogate in RVEA//
5:
while w ⩽wmax do
6:
Generate oﬀspring by the simulated binary crossover (SBX) and the polynomial mu-
tation;
7:
Combine parent and oﬀspring populations and predict their ﬁtness with the GP models;
8:
Select a new population for the next generation;
9:
Update the reference vectors;
10:
w = w + 1
11:
endwhile
12:
//Updating the surrogate//
13:
Call the proposed AF to evaluate the individuals in the optimized population;
14:
Call the proposed sampling selection strategy to determine u points to be evaluated
by the original objective functions and update FE = FE + u; (see Algorithm 2)
15:
Add individuals from step 8 to training data and limit the number of training data
and go to step 2;
16: end while
17: return The ﬁnal solution population P
12
         
         


<!-- página 15 -->

The adaptive acquisition function is deﬁned as follows:
AF = (1 −α) · (µx./µmax) + α · (σx./σmax)
(16)
where
α = −0.5 · cos(
FE
FEmax
· π) + 0.5
(17)
where ’./’ denotes element-by-element division for two vectors of the same size;
µx and σx denote the mean and variance of the predicted function values of
each individual x in the optimized population obtained by RVEA, respectively;
175
µmax and σmax represent the maximum values of the mean and variance val-
ues provided by the GP models, respectively. In this way, both the predicted
objective value and the uncertainty are normalized to [0, 1]. α is an adaptation
parameter deﬁned by a cosine function. FE denotes the current number of real
objective function evaluations, and FEmax represents the predeﬁned maximum
180
number of real objective function evaluations.
The main motivation behind the above adaptive acquisition function is to
achieve relatively fast convergence in the early stage by assigning a large weight
to x, while more exploitative search is achieved in the later search stage, where
we select new pints with APD, so that new data points in the neighborhood of
the previously observed data are preferred to be sampled when searching the
promising area. Herein we explain brieﬂy why we select new data points with
lower uncertainty as the iteration increases. It is assumed that a decision space
around the training data sampled so far is the most promising area near the end
of the run; therefore, the proposed AF allows to sample new points inside that
domain for local search. We also test a variant of the proposed AF,
AFvariant = AF = (1 −α) · (µx./µmax) −α · (σx./σmax).
(18)
The diﬀerence between the two AFs is whether we minimise the uncertainty or
not near the end of the run and the experimental results conﬁrm the eﬀectiveness
of the suggested AF. As shown in Fig. 3, the proposed AF and its variant sample
ﬁve new data points for twice (when FE = 195 and FE = 200) on DTLZ2
185
based on the same GP model. It is worth noting that the samples selected by
13
         
         


<!-- página 16 -->

the proposed AF are much closer to the PF, while points sampled by the variant
are far away from the PF. These indicate that the proposed criterion in (15)
results in more diverse and exploitative search in the later stage, which is of
particular importance when the number of ﬁtness evaluated is highly limited.
190
Sample points (FE=195)
The obtained PF
New sample points (FE=200)
The true PF
(a) Data points sampled by the proposed
AF
Sample points (FE=195)
The obtained PF
New sample points (FE=200)
The true PF
 
(b) Data points sampled by the variant
Figure 3: An example of new data points sampled by the proposed AF and its variant for
DTLZ2 (when FE = 195 and FE = 200), respectively.
3.3. Adaptive Sampling Selection Criterion
As analyzed in [38], the reference vectors predeﬁned in RVEA divide the
search space into several subspaces, with each reference vector specifying a di-
rection along which the Pareto optimal solutions are preferred. A set of solutions
associated to each reference vector is expected to be achieved to guarantee the
diversity as well as the convergence. To this end, we introduce two diﬀerent
sampling selection strategies that work together with the proposed adaptive
AF. Speciﬁcally, when α < 0.5, the angle-based selection approach is employed
to prioritize the population diversity:
Angle(θft,i,vt,j) = M · θft,i,vt,j
γvt,j
(19)
The above sampling selection criterion does not consider the distance from
the candidate solution to the reference vector, which usually serves as the con-
vergence criterion in APD. As a result, this sampling selection strategy focuses
14
         
         


<!-- página 17 -->

on promoting the diversity of the population. When α >= 0.5, APD is adopted
195
to determine which points are to be sampled. The overall sampling selection
criterion utilized in our algorithm is shown in Algorithm 2.
Algorithm 2 Adaptive Sampling Selection Criterion
Input: α: the adaptive parameter based on a cosine function; u: the number of points selected
to be re-evaluated in each iteration; v: the reference vectors; P: the ﬁnal population
obtained from RVEA
Output: The selected re-evaluated individuals
1: if α < 0.5 then
2:
// Using the angle-based sampling selection criterion//
3:
Calculate the Angle(θft,i,vt,j ) for each individual in the population and select u new
points to be re-evaluated;
4: elseIf α >= 0.5
5:
//Using APD method//
6:
Calculate the dt,i,j for each individual in the population and select u new points to be
re-evaluated;
7: end if
4. Comparative Studies
In this section, numerical experiments are conducted on nine three-objective
benchmark problems taken from the DTLZ test suite and seven bi-objective
200
benchmark problems from the UF test suite. To examine the eﬃciency of the
proposed strategies, AB-MOEA is compared with its two variants, AS-MOEA
and SM-MOEA. Here, AS-MOEA employs the proposed adaptive AF and the
APD sampling selection criterion, while SM-MOEA employs the LCB and the
proposed sampling selection criterion. Then we compare AB-MOEA with the
205
original RVEA as well as three representative Bayesian approaches to SAEAs,
namely MOEA/D-EGO [29], SMS-EGO [39], and K-RVEA [30]. Although all
these compared algorithms except for RVEA employ diﬀerent kinds of EAs and
acquisition functions, respectively, they all adopt the Gaussian processes as the
surrogates and use the prediction provided by GPs during the search process.
210
As indicated in [40, 41], the computational complexity of training GP is O(n3),
15
         
         


<!-- página 18 -->

where n is the number of training samples. Therefore, it is worthy of noting
that the major computational costs of these algorithms are mainly spent on
training the GPs, which depends on the number of training data. Finally, it
should be emphasized that the computational complexity of an expensive real
215
ﬁtness evaluation, e.g., a 3D computational ﬂuid dynamics simulation or car
crash test often take hours or even days [14, 19], which is much higher than
that of training a surrogate. That is the reason why the number of real ﬁtness
evaluations has been used as the baseline for comparing SAEAs.
In the following section, we begin with brieﬂy introducing the test problems
220
and performance metrics adopted in this work. Afterwards, the details of the
experimental settings concerning the four compared algorithms are described.
Lastly, the experimental results including the pilot studies and the comparative
results, together with the Wilcoxon rank sum test, are presented and discussed.
4.1. Test Problems
225
In our experiments, the proposed algorithm is compared with four selected
algorithms on seven benchmark functions (DTLZ1 to DTLZ7) with three objec-
tives suggested in [42], two modiﬁed counterparts of DTLZ1 and DTLZ3, and
the UF test suite from the CEC2009 MOEA competition with two objectives
[43], respectively. Before starting our experiments, we want to have a discussion
about the multi-model g function used in DTLZ1 and DTLZ3. The g function,
given in the following, is suggested to control the ruggedness of DTLZ1 and
DTLZ3 [42],
g = 100[5 +
X
i∈1,...,n
(xi −0.5)2 −cos(20π(xi −0.5))], i = 1, ..., n.
(20)
where n denotes the number of decision variables. As indicated in [44], 20π
within the cosine term triggers excessively ruggedness.
Consequently, 2π is
adopted to reduce the complexity to a reasonable level. The modiﬁed coun-
terparts are denoted as DTLZ1a and DTLZ3a, respectively. As recommended
in [42], the number of decision variables for the test instances is set to n =
230
M + K −1, where K = 5 is adopted for DTLZ1 and DTLZ1a, K = 10 is used
16
         
         


<!-- página 19 -->

for DTLZ2 to DTLZ6 as well as DTLA3a, and K = 20 is employed in DTLZ7.
M represents the number of objectives. Here, we set M = 3.
4.2. Performance Metrics
The inverted generational distance (IGD) [45], hypervolume (HV) [46], gen-
235
erational distance (GD) [47] and spread (∆) [48] metrics are adopted to assess
the performance of the algorithms. IGD and HV provide a combined informa-
tion of the convergence and diversity of the obtained set of solutions, while GD
and spread metrics work as the convergence measure and diversity measure,
respectively. The PlatEMO toolbox [49] is used to calculate values of these per-
240
formance metrics in our experiments. Let P ∗be a set of uniformly distributed
solutions sampled from the objective space along the true PF. Let P be an
obtained approximation to the PF.
1) GD: GD measures the average distance between the obtained PF and the
true PF of the problem, formulated as follows:
GD(P ∗, P) =
P
υ∈P d(υ, P ∗)
|P|
(21)
where |P| is the cardinality of the set P and d(υ, P ∗) is the minimal Euclidean
distance between υ and all points in P ∗. The smaller the GD value is, the better
245
the convergence performance.
2) Spread (∆): Spread is used to evaluate the extent of the Pareto front
covered by the obtained set of solutions, deﬁned as
∆=
Pm
i=1 d(Ei, P) + P
υ∈P |d(υ, P) −¯d)|
Pm
i=1 d(Ei, P) + (|P| −m) ¯d
(22)
where d(υ, P) is the minimum Euclidean distance between υ and all points in
P, (Ei, ..., Em) are m extreme solutions in the true PF P ∗and ¯d =
P
υ∈P d(υ,P ))
|P |
is the mean distance between the solutions of P. A smaller value of ∆indicates
a better diversity of the obtained PF.
250
3) IGD: The deﬁnition of IGD is similar to GD. IGD measures the inverted
generational distance from P ∗to P, deﬁned as
IGD(P ∗, P) =
P
υ∈P ∗d(υ, P)
|P ∗|
(23)
17
         
         


<!-- página 20 -->

where d(υ, P) is the minimum Euclidean distance between υ and all points in
P. The smaller IGD value, the better the achieved solution set is.
4) HV : HV calculates the volume of the objective space dominated by an
approximation set P and dominates P ∗sampled from the PF.
HV = volume(∪j
i=1ϑi)
(24)
where ϑi represents the hypervolume contribution of the i-th solutions with
respect to the reference points. All HV values presented in this work are nor-
malized to [0, 1]. Algorithms achieving a larger HV value are better.
255
4.3. Experimental Settings
We run each algorithm on each benchmark problem for 20 independent times,
and the Wilcoxon rank sum test is calculated to compare the mean of 20 running
results obtained by AB-MOEA and by the compared algorithms at a signiﬁcance
level of 0.05. Symbol ”(+)” indicates that the proposed algorithm outperforms
260
the compared algorithm statistically signiﬁcantly, while ”(–)” means that the
compared algorithm performs better than AB-MOEA, and ”(≈)” means there
is no signiﬁcant diﬀerence between them.
AB-MOEA and its variants are implemented in MATLAB R2009a on an Intel
Core i7 with 2.21 GHz CPU, and the compared algorithms are implemented in
265
PlatEMO toolbox [49]. In all Bayesian SAEAs, the GP model is constructed
using the DACE toolbox [50]. The general parameter settings in the experiments
are given as follows: 1) The number of initial training points Ntrain = 11n −1,
where n is the number of decision variables. 2) The maximum number of real
function evaluations FEmax = 300. 3) The maximum number of generations
270
before updating GPs wmax = 20.
The speciﬁc parameter settings for each
compared algorithm are the same as recommended in their original papers.
4.4. Experimental Results
4.4.1. Pilot Studies
To validate the proposed strategies, pilot studies are performed on the above
275
test instances for 20 runs independently, and the mean of the results achieved
18
         
         


<!-- página 21 -->

by the original RVEA is adopted for comparison using the Wilcoxon rank sum
test. We calculate the values of the performance metrics for the non-dominated
solution set in each run, respectively. The minimum, maximum and mean val-
ues of the performance metrics over 20 times are collected and presented in
280
Tables 1 and 2, respectively, where the best result of each benchmark function
is highlighted.
First, we assess the eﬃciency of the proposed sampling selection criterion
in the proposed AB-MOEA in addressing expensive MOPs via comparing SM-
MOEA with the original RVEA. According to the statistical results presented
285
in Table 1, it can be seen that SM-MOEA signiﬁcantly outperforms the orig-
inal RVEA in terms of IGD values on DTLZ1a, DTLZ2, DTLZ3a, DTLZ6 as
well as DTLZ7, while there is little diﬀerence between SM-MOEA and RVEA
on DTLZ1, DTLZ3, DTLZ4 and DTLZ5. Similarly, SM-MOEA outperforms
RVEA on all tested instances except for DTLZ4 and DTLZ7 in terms of the HV
290
metric. These results indicate SAEAs with the help of the suggested sampling
selection criterion are able to improve the balance between the diversity and
convergence.
Table 1: Statistical results of the IGD values obtained by SM-MOEA, AS-MOEA, AB-MOEA,
and RVEA with the same number of real function evaluations
Test problem
SM-MOEA
AS-MOEA
AB-MOEA
RVEA
min
mean
max
min
mean
max
min
mean
max
min mean max
DTLZ1
16.67 33.14 (≈) 56.21 14.26 28.39 (+) 43.13 16.58 27.29 (+) 52.88 10.08 33.68 51.56
DTLZ1a
2.04 5.36 (+) 9.58
0.96 1.89 (+) 3.48
0.35 1.47 (+) 2.70
5.21 23.79 48.80
DTLZ2
0.09 0.12 (+) 0.18
0.09 0.12 (+) 0.21
0.08 0.09 (+) 0.17
0.23
0.42
0.49
DTLZ3
185.7 347.6 (≈) 456.4 199.4 319.1 (+) 446.9 199.1 310.8 (+) 420.7 154.2 374.4 479.7
DTLZ3a
26.63 99.90 (+) 246.8 9.08 30.82 (+) 110.7 17.05 30.65 (+) 58.97 173.2 330.4 482.0
DTLZ4
0.36 0.53 (≈) 0.85 0.15 0.50 (≈) 0.78
0.23
0.43 (+) 0.68
0 .30 0.56
0.71
DTLZ5
0.34 0.35 (≈) 0.37
0.34 0.34 (≈) 0.35
0.06 0.09 (+) 0.19
0 .13 0.35
0.49
DTLZ6
3.91 4.70 (+) 5.54
3.89 4.66 (+) 5.33 3.83 4.60 (+) 5.56
6 .22 7.89
8.50
DTLZ7
2.74 3.46 (+) 4.59
3.13 4.40 (+) 6.07
0.58 0.81 (+) 1.40
3 .45 6.41
7.82
Next, we compare AS-MOEA with RVEA to investigate the eﬀectiveness of
19
         
         


<!-- página 22 -->

Table 2: Statistical results of the HV values obtained by SM-MOEA, AS-MOEA, AB-MOEA,
and RVEA with the same number of real function evaluations
Test problem
SM-MOEA
AS-MOEA
AB-MOEA
RVEA
min
mean
max
min
mean
max
min
mean
max
min mean max
DTLZ1
0.968 0.985 (+) 0.995 0.979 0.989 (+) 0.995 0.971 0.993 (+) 0.996 0.901 0.939 0.995
DTLZ1a
0.569 0.802 (+) 0.975 0.971 0.990 (+) 0.997 0.973 0.992 (+) 0.998 0.000 0.166 0.736
DTLZ2
0.305 0.443 (+) 0.489 0.270 0.432 (+) 0.485 0.350 0.444 (+) 0.488 0.021 0.111 1.000
DTLZ3
0.863 0.910 (+) 0.956 0.876 0.922 (+) 0.957 0.862 0.921 (+) 0.957 0.737 0.832 0.985
DTLZ3a
0.000 0.238 (+) 0.728 0.000 0.857 (+) 0.982 0.403 0.855 (+) 0.979 0.000 0.000 0.000
DTLZ4
0.000 0.015 (≈) 0.062 0.000 0.060 (≈) 0.443 0.009 0.063 (≈) 0.201 0.000 0.022 0.144
DTLZ5
0.212 0.255 (+) 0.282 0.242 0.266 (+) 0.284 0.108 0.118 (+) 0.147 0.000 0.006 0.068
DTLZ6
0.737 0.797 (+) 0.831 0.731 0.790 (+) 0.847 0.751 0.801 (+) 0.834 0.366 0.415 0.587
DTLZ7
0.000 0.000 (≈) 0.000 0.000 0.000 (≈) 0.000 0.069 0.070 (+) 0.104 0.000 0.000 0.000
the adaptive acquisition function. On DTLZ1-3, DTLZ1a, DTLZ3a as well as
295
DTLZ6, both the IGD and HV metrics suggest that AS-MOEA has achieved
signiﬁcant improvements over RVEA as the adaptive AF utilizing a nonlinear
aggregation function to take both the uncertainty and the predicted mean ﬁtness
value into account. Since the maintenance of a good distribution of solutions
is highly desirable on DTLZ4, the approximate PF obtained by AS-MOEA is
300
no worse than that obtained by RVEA with the limited function evaluations.
These results together conﬁrm the eﬀectiveness of the suggested adaptive AF.
From the above comparative results, we can conclude that the combination
of the adaptive AF and the adaptive sampling selection criterion are helpful to
achieve diverse and converged solutions using a limited number of real ﬁtness
305
evaluations. In addition, AB-MOEA signiﬁcantly outperforms RVEA on all the
benchmark functions in terms of the IGD metric. A similar conclusion can be
drawn on the results in terms of the HV values, as presented in Table 2. All
results presented in Tables 1 and 2 provide strong evidence conﬁrming that both
the adaptive AF and the new sampling selection criterion are able to improve
310
the quality of solutions, and a combination of these two can further contribute
to performance improvement.
20
         
         


<!-- página 23 -->

4.4.2. Comparison with Surrogate-assisted MOEAs
Table 3: Statistical results of the IGD values obtained by K-RVEA, MOEA/D-EGO, SMS-
EGO, and AB-MOEA with the same number of real function evaluations
Test problem
K-RVEA
MOEA/D-EGO
SMS-EGO
AB-MOEA
min
mean
max
min
mean
max
min
mean
max
min
mean max
DTLZ1
13.56 28.46 (≈) 45.85 18.52 38.82 (+) 57.98 25.31 35.14 (+) 40.04 16.58 27.29 52.88
DTLZ1a
0.58
1.68 (≈) 2.72
1.21 7.60 (+) 22.16 0.07 1.15 (≈) 7.58
0.35
1.47
2.70
DTLZ2
0.13
0.18 (+) 0.24
0.36 0.42 (+) 0.48
0.23
0.29 (+) 0.34
0.09
0.09 0.17
DTLZ3
214.3 355.0 (+) 430.9 225.8 253.8 (+) 401.6 204.7 219.7 (–) 239.0 199.0 310.8 420.7
DTLZ3a
31.41 77.06 (+) 212.4 121.6 250.7 (+) 398.6 2.41 36.08 (≈) 132.5 17.05 30.65 58.97
DTLZ4
0.30
0.47 (≈) 0.69
0.50 0.70 (+) 0.82
0.65
0.91 (+) 1.04
0.23
0.43 0.68
DTLZ5
0.10
0.15 (+) 0.25
0.28 0.34 (+) 0.42
0.07
0.12 (+) 0.20
0.06
0.09 0.19
DTLZ6
3.96
4.60 (≈) 5.58 0.74 3.04 (–) 4.56 3.69
4.66 (≈) 5.61
3.83
4.60
5.56
DTLZ7
1.00
4.28 (+) 9.66
2.61 6.57 (+) 8.87
0.59
1.33 (+) 1.78
0.58
0.81 1.40
UF1
0.09
0.12 (+) 0.17
0.14 0.23 (+) 0.37
0.07
0.14 (+) 0.53
0.09
0.09 0.10
UF2
0.06
0.08 (+) 0.14
0.13 0.18 (+) 0.24 0.05
0.07 (≈) 0.10
0.06
0.06
0.07
UF3
0.56
0.84 (+) 1.07
0.61 0.94 (+) 1.35
0.86
1.01 (+) 1.16
0.34
0.48 0.65
UF4
0.09
0.10 (–) 0.12
0.09 0.11 (–) 0.12 0.07 0.10 (–)
0.12
0.14
0.16
0.18
UF5
0.72
1.32 (+) 2.62
2.04 2.85 (+) 4.08
0.61
1.53 (+) 2.06
0.47
0.70 1.08
UF6
0.82
1.24 (+) 2.02
1.14 1.84 (+) 2.76
1.01
1.23 (+) 1.59
0.82
1.06 1.24
UF7
0.88
1.24 (+) 1.47
0.14 0.29 (+) 0.57
0.07
0.11 (+) 0.38
0.07
0.09 0.11
In this subsection, the performance of the proposed AB-MOEA is compared
with the state-of-the-art Bayesian SAEAs, including K-RVEA, MOEA/D-EGO,
315
and SMS-EGO, in terms of IGD, HV, GD and spread metrics. Table 3 and Ta-
ble 4 present comparative results of IGD and HV, respectively. To evaluate the
diversity and convergence separately, GD and spread metrics are calculated on
part of the test problems and the results are presented in Table 5 and Table
6, respectively. The best one of each instance is highlighted. To further illus-
320
trate the advantage of the proposed algorithm, the non-dominated solution set
obtained by each of the four compared algorithms (in the run that achieved
the medium performance out of 20 independent runs) on DTLZ2 and DTLZ7
are visualized in Figs.
4-5.
From the results, we can clearly see the better
performance of the proposed algorithm.
325
21
         
         


<!-- página 24 -->

Table 4: Statistical results of the HV values obtained by K-RVEA, MOEA/D-EGO, SMS-
EGO, and AB-MOEA with the same number of real function evaluations
Test problem
K-RVEA
MOEA/D-EGO
SMS-EGO
AB-MOEA
min
mean
max
min
mean
max
min
mean
max
min
mean
max
DTLZ1
0.930 0.962 (+) 0.989 0.982 0.983 (+) 0.983 0.991 0.992 (+) 0.994 0.971 0.993 0.995
DTLZ1a
0.936 0.975 (+) 0.993 0.246 0.513 (+) 0.781 0.999 1.000 (–) 1.000 0.973 0.992 0.998
DTLZ2
0.262 0.340 (+) 0.438 0.104 0.124 (+) 0.144 0.215 0.304 (+) 0.393 0.350 0.444 0.488
DTLZ3
0.858 0.900 (+) 0.933 0.870 0.925 (+) 0.979 0.981 0.984 (–) 0.986 0.862 0.921 0.957
DTLZ3a
0.000 0.373 (+) 0.743 0.000 0.000 (+) 0.000 0.822 0.844 (≈) 0.865 0.403 0.855 0.979
DTLZ4
0.000 0.050 (≈) 0.174 0.007 0.015 (+) 0.022 0.000 0.000 (+) 0.000 0.009 0.063 0.201
DTLZ5
0.009 0.068 (+) 0.108 0.000 0.001 (+) 0.002 0.108 0.112 (≈) 0.116 0.108 0.118 0.147
DTLZ6
0.678 0.792 (≈) 0.849 0.875 0.878 (–) 0.882 0.732 0.803 (≈) 0.874 0.751 0.801 0.834
DTLZ7
0.000 0.014 (+) 0.089 0.000 0.000 (+) 0.000 0.066 0.066 (+) 0.087 0.069 0.070 0.104
UF1
0.49 0.56 (+) 0.59
0.26
0.40 (+) 0.51
0.02
0.53 (+) 0.61
0.55
0.57
0.58
UF2
0.60 0.62 (+) 0.64
0.38
0.47 (+) 0.53
0.60
0.63 (≈) 0.66
0.63
0.64
0.65
UF3
0.00 0.03 (+) 0.13
0.00
0.01 (+) 0.05
0.00
0.00 (+) 0.01
0.07
0.18
0.29
UF4
0.27 0.30 (–) 0.31
0.27
0.29
(–)
0.31
0.27
0.30 (–) 0.33
0.21
0.22
0.25
UF5
0.00 0.00 (+) 0.02
0.00
0.00 (+) 0.00
0.00
0.00 (+) 0.01
0.00
0.03
0.14
UF6
0.18 0.39 (+) 0.48
0.03
0.21 (+) 0.34
0.30
0.42 (+) 0.49
0.64
0.79
0.89
UF7
0.00 0.00 (+) 0.00
0.08
0.24 (+) 0.38
0.28
0.43 (+) 0.48
0.42
0.46
0.48
Table 5: Statistical results of the GD values obtained by K-RVEA, MOEA/D-EGO, SMS-
EGO, and AB-MOEA with the same number of real function evaluations
Test problem
K-RVEA
MOEA/D-EGO
SMS-EGO
AB-MOEA
min
mean
max
min
mean
max
min
mean
max
min
mean
max
DTLZ1a
3.52
9.32 (+) 16.05
14.91 31.38 (+) 55.33
0.01 13.27 (≈) 49.39
2.64
3.65
4.86
DTLZ2
0.01
0.03 (+) 0.04
0.07
0.11 (+) 0.14
0.01
0.06 (+)
0.12
0.02
0.04
0.10
DTLZ3a
38.09 64.72 (+) 102.15 127.19 166.70 (+) 215.85 24.91 69.75 (≈) 111.23 12.37 78.13 114.98
DTLZ7
0.18
1.55 (+) 2.63
1.55
1.77 (+) 2.44
0.01
0.66 (+)
4.91
0.15
0.31
0.83
UF2
0.004 0.010 (≈) 0.02
0.04
0.07 (+) 0.11
0.01
0.01 (+)
0.05
0.006 0.009 0.014
UF4
0.016 0.020 (–) 0.023 0.019 0.024 (–) 0.027 0.015 0.025 (–)
0.035
0.027 0.032 0.036
UF6
0.429
0.75 (+) 1.59
0.78
1.24 (+) 2.09
0.43
0.61 (+)
1.57
0.36
0.55
1.10
UF7
0.008 0.03 (+) 0.11
0.03
0.16 (+) 0.40
0.02
0.07 (+)
0.26
0.009 0.014 0.029
22
         
         


<!-- página 25 -->

Table 6: Statistical results of the spread values obtained by K-RVEA, MOEA/D-EGO, SMS-
EGO, and AB-MOEA with the same number of real function evaluations
Test problem
K-RVEA
MOEA/D-EGO
SMS-EGO
AB-MOEA
min
mean
max
min
mean
max
min
mean
max
min
mean
max
DTLZ1a
0.663 1.213 (≈) 1.787 0.528 1.058 (≈) 1.465 0.439 1.096 (≈) 1.853 0.883 0.995 1.110
DTLZ2
0.470 0.594 (+) 0.699 0.587 0.759 (≈) 0.961 0.700 0.909 (+) 1.080 0.545 0.777 1.129
DTLZ3a
0.580 0.848 (+) 1.214 0.560 0.755 (+) 0.960 0.711 1.064 (≈) 1.655 0.225 0.611 1.563
DTLZ7
0.789 1.006 (≈) 1.178 0.773 0.883 (+) 0.986 0.335 1.213 (≈) 5.429 0.821 1.032 1.346
UF2
0.595 0.780 (+) 0.931 0.547 0.859 (+) 1.235 0.319 0.833 (+) 1.128 0.533 0.700 0.970
UF4
0.575 0.708 (≈) 0.859 0.453 0.649 (≈) 0.852 0.453 0.626 (≈) 0.848 0.538 0.680 0.810
UF6
0.780 1.059 (+) 1.881 0.648 1.007 (+) 1.429 0.707 0.884 (≈) 1.106 0.707 0.873 1.174
UF7
0.673 0.996 (+) 1.340 0.666 0.968 (+) 1.516 0.441 0.908 (≈) 1.681 0.596 0.795 1.046
(a) The non-dominated solutions obtained
by AB-MOEA
(b) The non-dominated solutions obtained
by SMS-EGO
(c) The non-dominated solutions obtained
by K-RVEA
(d) The non-dominated solutions obtained
by MOEA/D-EGO
Figure 4: Visualization of the non-dominated solutions obtained by the four compared algo-
rithms on DTLZ2.
23
         
         


<!-- página 26 -->

(a) The non-dominated solutions obtained
by AB-MOEA
(b) The non-dominated solutions obtained
by SMS-EGO
(c) The non-dominated solutions obtained
by K-RVEA
(d) The non-dominated solutions obtained
by MOEA/D-EGO
Figure 5: Visualization of the non-dominated solutions obtained by the four compared algo-
rithms on DTLZ7.
The statistical results in terms of IGD values obtained by the four algo-
rithms are summarized in Table 3. For the three-objective benchmarks, it is
apparent that AB-MOEA has achieved the best approximate PF on all test
problems except for DTLZ3 (SMS-EGO obtained the best IGD values) and
DTLZ6 (MOEA/D-EGO obtained the best IDG values). The reason behind
330
this may be that DTLZ3 has a multimodal ﬁtness landscape, and DTLZ6 has
a plenty of disconnected Pareto optimal regions in the decision space. Actually,
in our experiments, all algorithms failed to converge to the PF on DTLZ3 and
24
         
         


<!-- página 27 -->

DTLZ6 due to the limited budget of function evaluations. For the bi-objective
test suite, we can clearly see that the IGD results obtained by AB-MOEA are
335
much better than the compared algorithms on all UF test problems except on
UF4. According to the Wilcoxon rank sum test, the proposed algorithm signif-
icantly outperforms the compared algorithms on most of the test problems.
Similar conclusions can be drawn from the results given in Table 4. From
these results, we can see that AB-MOEA performs much better than K-RVEA
340
on all three-objective benchmark problems considered in this work but DTLZ4
and DTLZ6, on which AB-MOEA and K-RVEA perform comparably. MOEA/D-
EGO is able to achieve well converged and evenly distributed ﬁnal solutions on
DTLZ6; however, its performance on the rest of problems is much worse than
AB-MOEA. Regarding the bi-objective benchmarks, the best results of HV on
345
UF1-UF3 and UF5-UF7 are obtained by AB-MOEA. It is worthy of noting that
SMS-EGO outperforms AB-MOEA on DTLZ1a, DTLZ3 and UF4 in terms of
the HV metric. Note, however, that SMS-EGO is very time-consuming [29]. In
conclusion, the proposed algorithm shows the best overall performance.
To further verify the performance of AB-MOEA, two performance indica-
350
tors, GD and spread metrics are adopted to investigate the convergence and
diversity of the four algorithms.
Since the algorithms failed to converge to
the PF on some of the benchmarks due to the limited evaluation budget, we
select some of them to examine the convergence and diversity performance sep-
arately. As listed in 5, AB-MOEA obtains the best GD values compared to
355
other three algorithms on a vast majority of the test problems, conﬁrming the
better performance indicated by IGD and HV values. On the other hand, the
values of the spread metrics given in 6 indicate that AB-MOEA shows certain
advantages over MOEA/D-EGO and K-RVEA concerning the diversity of the
obtained solutions. Note that SMS-EGO also shows competitive diversity per-
360
formance; however, it is signiﬁcantly outperformed by AB-MOEA with respect
to the convergence performance.
25
         
         


<!-- página 28 -->

5. A Case Study on Airfoil Design
To verify the performance of the proposed algorithm on real-world opti-
mization problems, we compare AB-MOEA, K-RVEA and Bayesian optimiza-
365
tion (BO) on a transonic airfoil design optimization problem. It is noted that
time-consuming computational ﬂuid dynamics (CFD) simulations are required
to evaluate the performance of an airfoil design, which is therefore a compu-
tationally expensive optimization problem and a limited budget of evaluations
(here, 300 evaluations) is aﬀordable. In the following, a brief introduction to
370
the problem is given and then the simulation results are presented.
We consider an airfoil design problem based on the RAE2822 airfoil test
case from the GARTEUR AG52 project [25]. Here, 14 points of a nonrational
B-spline (NURBS) are used to control the curvature of the upper and lower
surfaces of the airfoil, then CFD simulations are carried out to calculate the
375
drag and lift coeﬃcients (Cd and Cl) for any given geometry of the airfoil. We
aim to optimize the geometry of the airfoil to minimize the drag coeﬃcient and
maximize the lift coeﬃcient.
We compare AB-MOEA with K-RVEA and BO [37] in terms of IGD and HV.
Each algorithm is run for ten times on the airfoil design problem and the mean
380
values of HV and IGD are presented in Table 7. Note that in calculating IGD,
the reference set is the non-dominated solution set of all solutions obtained by
three compared algorithms. The non-dominated solution set obtained by each
algorithm is also visualized in Fig. 6. From Table 7 and Fig. 6, we can see
that the proposed algorithm has also achieved the best results on the real-world
385
design problem.
Table 7: The mean values of HV and IGD obtained by AB-MOEA, BO, K-RVEA on the
airfoil design problem.
Algorithm
HV
IGD
AB-MOEA
0.0423
0.0328
BO
0.0407
0.0389
K-RVEA
0.0348
0.0402
26
         
         


<!-- página 29 -->

0
0.1
0.2
0.3
0.4
0.5
0.6
0.7
0.8
0.9
1
f1
0
0.1
0.2
0.3
0.4
0.5
0.6
0.7
0.8
f2
PF obtained by AB-MOEA
(a) The non-dominated solutions obtained
by AB-MOEA
0
0.1
0.2
0.3
0.4
0.5
0.6
0.7
0.8
0.9
f1
0
0.1
0.2
0.3
0.4
0.5
0.6
0.7
0.8
f2
PF obtained by BO
(b) The non-dominated solutions obtained
by BO
0
0.1
0.2
0.3
0.4
0.5
0.6
0.7
0.8
0.9
f1
0
0.1
0.2
0.3
0.4
0.5
0.6
0.7
f2
PF obtained by K-RVEA
(c) The non-dominated solutions obtained
by K-RVEA
Figure 6: The obtained non-dominated solutions on the airfoil design problem.
6. Conclusion
Surrogate-assisted evolutionary algorithms have shown great promises to
solve expensive multi-objective optimization problems. However, the limited
budget of function evaluations requires that the algorithm is able to quickly
converge while ensuring a diverse distribution of the obtained solutions. There-
390
fore, it is highly demanded to design SAEAs that can achieve an optimal balance
between exploration and exploitation. For this purpose, we proposed an adap-
tive Bayesian approach to surrogate-assisted evolutionary algorithm to improve
27
         
         


<!-- página 30 -->

the eﬃciency in solving expensive MOPs. Taken both the diversity and conver-
gence into account, an adaptive acquisition function is designed by adjusting
395
the weights of the uncertainty and the mean objective value in the acquisition
function on top of an adaptive sampling selection criterion that can better bal-
ance diversity and convergence. The eﬀectiveness of the introduced strategies
and the performance of the proposed algorithm are investigated on a set of
widely used benchmark problems and an airfoil design optimization problem.
400
Our results demonstrate that the proposed algorithm signiﬁcantly outperforms
the compared algorithms on most test problems and is also able to achieve better
performance on the airfoil design problem.
Although the proposed algorithm is competitive for solving most test prob-
lems used in our experiments, we ﬁnd that the proposed algorithm suﬀers from
405
slow convergence when solving DTLZ1, DTLZ3 and UF6. This might be at-
tributed to the poor prediction quality of GP models due to the strong rugged-
ness of the ﬁtness landscape. Consequently, future research could investigate
the use of multiple surrogate models and more sophisticated methods for es-
timating the uncertainty. In addition, new acquisition functions are desirable
410
when dealing with MOPs whose objective functions and / or constraints have
very diﬀerent computational complexities.
Acknowledgments
The authors are grateful to Dr Handing Wang for her assistance in testing the
algorithms on the airfoil design problem. The work was supported in part by a
415
Royal Society International Exchanges Program under No. IEC\NSFC\170279.
References
[1] R. T. Marler, J. S. Arora, Survey of multi-objective optimization methods
for engineering, Structural and multidisciplinary optimization 26 (6) (2004)
369–395.
420
28
         
         


<!-- página 31 -->

[2] W. Saad, Z. Han, M. Debbah, A. Hjorungnes, T. Basar, Coalitional game
theory for communication networks, IEEE Signal Processing Magazine
26 (5) (2009) 77–97.
[3] E. E. Tsiropoulou, P. Vamvakas, G. K. Katsinis, S. Papavassiliou, Com-
bined power and rate allocation in self-optimized multi-service two-tier fem-
425
tocell networks, Computer Communications 72 (2015) 38–48.
[4] F. A. Mohamed, H. N. Koivo, Multiobjective optimization using modiﬁed
game theory for online management of microgrid, European Transactions
on Electrical Power 21 (1) (2011) 839–854.
[5] R. Meng, Y. Ye, N.-g. Xie, Multi-objective optimization design methods
430
based on game theory, in: 2010 8th World Congress on Intelligent Control
and Automation, IEEE, 2010, pp. 2220–2227.
[6] E. E. Tsiropoulou, P. Vamvakas, S. Papavassiliou, Joint utility-based uplink
power and rate allocation in wireless networks: A non-cooperative game
theoretic framework, Physical Communication 9 (2013) 299–307.
435
[7] Y. Jin, Surrogate-assisted evolutionary computation: Recent advances and
future challenges, Swarm and Evolutionary Computation 1 (2) (2011) 61–
70.
[8] K. Deb, A. Pratap, S. Agarwal, T. Meyarivan, A fast and elitist multiob-
jective genetic algorithm: NSGA-II, IEEE Transactions on Evolutionary
440
Computation 6 (2) (2002) 182–197.
[9] Q. Zhang, H. Li, MOEA/D: A multiobjective evolutionary algorithm based
on decomposition, IEEE Transactions on Evolutionary Computation 11 (6)
(2007) 712–731.
[10] R. Cheng, Y. Jin, M. Olhofer, B. Sendhoﬀ, A reference vector guided evolu-
445
tionary algorithm for many-objective optimization, IEEE Transactions on
Evolutionary Computation 20 (5) (2016) 773–791.
29
         
         


<!-- página 32 -->

[11] E. Zitzler, M. Laumanns, L. Thiele, SPEA2: Improving the strength pareto
evolutionary algorithm, TIK-report 103.
[12] R. Cheng, Y. Jin, K. Narukawa, B. Sendhoﬀ, A multiobjective evolutionary
450
algorithm using Gaussian process-based inverse modeling, IEEE Transac-
tions on Evolutionary Computation 19 (6) (2015) 838–856.
[13] D. Rodriguez-Roman, A surrogate-assisted genetic algorithm for the selec-
tion and design of highway safety and travel time improvement projects,
Safety Science 103 (2018) 305–315.
455
[14] Y. Jin, B. Sendhoﬀ, A systems approach to evolutionary multiobjec-
tive structural optimization and beyond, IEEE Computational Intelligence
Magazine 4 (3) (2009) 62–76.
[15] A. Habib, H. K. Singh, T. Ray, A multiple surrogate assisted multi/many-
objective multi-ﬁdelity evolutionary algorithm, Information Sciences 502
460
(2019) 537–557.
[16] Y. Jin, H. Wang, T. Chugh, D. Guo, K. Miettinen, Data-driven evolu-
tionary optimization: an overview and case studies, IEEE Transactions on
Evolutionary Computation 23 (3) (2018) 442–458.
[17] B. D. Marjavaara, T. S. Lundstr¨om, T. Goel, Y. Mack, W. Shyy, Hydraulic
465
turbine diﬀuser shape optimization by multiple surrogate model approx-
imations of pareto fronts, Journal of Fluids Engineering 129 (9) (2007)
1228–1240.
[18] J. Zhang, A. Zhou, G. Zhang, A classiﬁcation and pareto domination based
multiobjective evolutionary algorithm, in: 2015 IEEE Congress on Evolu-
470
tionary Computation (CEC), IEEE, 2015, pp. 2883–2890.
[19] L. Pan, C. He, Y. Tian, H. Wang, X. Zhang, Y. Jin, A classiﬁcation-based
surrogate-assisted evolutionary algorithm for expensive many-objective op-
timization, IEEE Transactions on Evolutionary Computation 23 (1) (2018)
74–88.
475
30
         
         


<!-- página 33 -->

[20] B. Shahriari, K. Swersky, Z. Wang, R. P. Adams, N. De Freitas, Taking the
human out of the loop: A review of Bayesian optimization, Proceedings of
the IEEE 104 (1) (2015) 148–175.
[21] J. Snoek, H. Larochelle, R. P. Adams, Practical Bayesian optimization of
machine learning algorithms, in: Advances in Neural Information Process-
480
ing Systems, 2012, pp. 2951–2959.
[22] F. A. Viana, R. T. Haftka, L. T. Watson, Eﬃcient global optimization
algorithm assisted by multiple surrogate techniques, Journal of Global Op-
timization 56 (2) (2013) 669–689.
[23] D. Buche, N. N. Schraudolph, P. Koumoutsakos, Accelerating evolutionary
485
algorithms with Gaussian process ﬁtness function models, IEEE Transac-
tions on Systems, Man, and Cybernetics, Part C (Applications and Re-
views) 35 (2) (2005) 183–194.
[24] N. Hoyle, N. W. Bressloﬀ, A. J. Keane, Design optimization of a two-
dimensional subsonic engine air intake, AIAA Journal 44 (11) (2006) 2672–
490
2681.
[25] H. Wang, Y. Jin, J. Doherty, Committee-based active learning for
surrogate-assisted particle swarm optimization of expensive problems,
IEEE Transactions on Cybernetics 47 (9) (2017) 2664–2677.
[26] J. Tian, Y. Tan, J. Zeng, C. Sun, Y. Jin, Multi-objective inﬁll crite-
495
rion driven Gaussian process assisted particle swarm optimization of high-
dimensional expensive problems, IEEE Transactions on Evolutionary Com-
putation 23 (3) (2019) 459–472.
[27] J. Knowles, ParEGO: a hybrid algorithm with on-line landscape approx-
imation for expensive multiobjective optimization problems, IEEE Trans-
500
actions on Evolutionary Computation 10 (1) (2006) 50–66.
31
         
         


<!-- página 34 -->

[28] B. Naujoks, N. Beume, M. Emmerich, Metamodel-assisted SMS-EMOA
applied to airfoil optimization tasks, in: Proceedings EUROGEN, Vol. 5,
2005.
[29] Q. Zhang, W. Liu, E. Tsang, B. Virginas, Expensive multiobjective opti-
505
mization by MOEA/D with Gaussian process model, IEEE Transactions
on Evolutionary Computation 14 (3) (2009) 456–474.
[30] T. Chugh, Y. Jin, K. Miettinen, J. Hakanen, K. Sindhya, A surrogate-
assisted reference vector guided evolutionary algorithm for computationally
expensive many-objective optimization, IEEE Transactions on Evolution-
510
ary Computation 22 (1) (2018) 129–142.
[31] D. Guo, Y. Jin, J. Ding, T. Chai, Heterogeneous ensemble-based inﬁll cri-
terion for evolutionary multiobjective optimization of expensive problems,
IEEE Transactions on Cybernetics 49 (3) (2018) 1012–1025.
[32] C. E. Rasmussen, Gaussian processes in machine learning, in: Summer
515
School on Machine Learning, Springer, 2003, pp. 63–71.
[33] D. R. Jones, M. Schonlau, W. J. Welch, Eﬃcient global optimization of ex-
pensive black-box functions, Journal of Global Optimization 13 (4) (1998)
455–492.
[34] D. Zhan, Y. Cheng, J. Liu, Expected improvement matrix-based inﬁll crite-
520
ria for expensive multiobjective optimization, IEEE Transactions on Evo-
lutionary Computation 21 (6) (2017) 956–975.
[35] J. M. Hern´andez-Lobato, M. W. Hoﬀman, Z. Ghahramani, Predictive en-
tropy search for eﬃcient global optimization of black-box functions, in:
Advances in Neural Information Processing Systems, 2014, pp. 918–926.
525
[36] N. Srinivas, A. Krause, S. M. Kakade, M. Seeger, Gaussian process opti-
mization in the bandit setting: No regret and experimental design (2010)
1015–1022.
32
         
         


<!-- página 35 -->

[37] J. Liu, Z. Han, W. Song, Comparison of inﬁll sampling criteria in kriging-
based aerodynamic optimization, in: 28th Congress of the International
530
Council of the Aeronautical Sciences, 2012, pp. 23–28.
[38] R. Cheng, T. Rodemann, M. Fischer, M. Olhofer, Y. Jin, Evolutionary
many-objective optimization of hybrid electric vehicle control: From gen-
eral optimization to preference articulation, IEEE Transactions on Emerg-
ing Topics in Computational Intelligence 1 (2) (2017) 97–111.
535
[39] M. Emmerich, N. Beume, B. Naujoks, An EMO algorithm using the hy-
pervolume measure as selection criterion, in: International Conference on
Evolutionary Multi-Criterion Optimization, Springer, 2005, pp. 62–76.
[40] M. T. Emmerich, K. C. Giannakoglou, B. Naujoks, Single-and multiob-
jective evolutionary optimization assisted by gaussian random ﬁeld meta-
540
models, IEEE Transactions on Evolutionary Computation 10 (4) (2006)
421–439.
[41] J. Hensman, N. Fusi, N. D. Lawrence, Gaussian processes for big data, in:
Conference on Uncertainty in Artiﬁcial Intelligence, 2013, pp. 282–290.
[42] K. Deb, L. Thiele, M. Laumanns, E. Zitzler, Scalable multi-objective op-
545
timization test problems, in: Proceedings of the 2002 Congress on Evolu-
tionary Computation. CEC’02, Vol. 1, IEEE, 2002, pp. 825–830.
[43] Q. Zhang, A. Zhou, S. Zhao, P. N. Suganthan, W. Liu, S. Tiwari, Multi-
objective optimization test instances for the CEC 2009 special session and
competition, Tech. rep. (2008).
550
[44] C. Yang, J. Ding, Y. Jin, T. Chai, Oﬀ-line data-driven multi-objective
optimization: Knowledge transfer between surrogates and generation of
ﬁnal solutions, IEEE Transactions on Evolutionary Computation.
[45] Q. Zhang, A. Zhou, Y. Jin, RM-MEDA: A regularity model-based multi-
objective estimation of distribution algorithm, IEEE Transactions on Evo-
555
lutionary Computation 12 (1) (2008) 41–63.
33
         
         


<!-- página 36 -->

[46] L. While, P. Hingston, L. Barone, S. Huband, A faster algorithm for cal-
culating hypervolume, IEEE Transactions on Evolutionary Computation
10 (1) (2006) 29–38.
[47] D. A. Van Veldhuizen, G. B. Lamont, Multiobjective evolutionary algo-
560
rithm research: A history and analysis, Tech. rep., Citeseer (1998).
[48] Y.-N. Wang, L.-H. Wu, X.-F. Yuan, Multi-objective self-adaptive diﬀer-
ential evolution with elitist archive and crowding entropy-based diversity
measure, Soft Computing 14 (3) (2010) 193.
[49] Y. Tian, R. Cheng, X. Zhang, Y. Jin, PlatEMO: A MATLAB platform
565
for evolutionary multi-objective optimization, IEEE Computational Intel-
ligence Magazine 12 (4) (2017) 73–87.
[50] S. N. Lophaven, H. B. Nielsen, J. Sondergaard, DACE - A Matlab Kriging
Toolbox, 2002.
34
         
         


<!-- página 37 -->

Manuscript title: An Adaptive Bayesian Approach to Surrogate-Assisted Evolutionary Multi-objective Optimization  
The authors whose names are listed immediately below certify that they have NO afﬁ liations with or involvement in any 
organization or entity with any ﬁ nancial interest (such as honoraria; educational grants; participation in speakers’ bureaus; 
membership, employment, consultancies, stock ownership, or other equity interest; and expert testimony or patent-licensing 
arrangements), or non-ﬁ nancial interest (such as personal or professional relationships, afﬁ liations, knowledge or beliefs) in 
the subject matter or materials discussed in this manuscript.
Author names:
The authors whose names are listed immediately below report the following details of afﬁ liation or involvement in an 
organization or entity with a ﬁ nancial or non-ﬁ nancial interest in the subject matter or materials discussed in this manuscript. 
Please specify the nature of the conﬂ ict on a separate sheet of paper if the space below is inadequate.
Author names:
Conﬂ icts of Interest Statement
570
         
         


<!-- página 38 -->

This statement is signed by all the authors to indicate agreement that the above information is true and cor-
rect (a photocopy of this form may be used if there are more than 10 authors): 
Author's name (typed) 
Author's signature 
Date
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
29/08/2019
Yaochu Jin
         
         


<!-- página 39 -->

Credit Author Statement
Xilu Wang has developed and implemented of the algorithm, performed
the experiments and written the draft of the paper.
Yaochu Jin has contributed to the conceptualization of the research, develop-
575
ment of the algorithm, design of the experiments, and write-up of the paper.
Sebastian Schmitt and Markus Olhofer have contributed to the concelp-
tualization of the reseach, discussed the ideas of the algorithms and commented
on the earlier versions of the paper.
37
         
         



---

## ANEXO — Conteúdo textual das imagens (OCR)

> Texto extraído por OCR (Apple Vision) das figuras/imagens do PDF — apenas conteúdo NOVO, ausente da camada de texto (labels de eixos, legendas internas, tabelas/equações rasterizadas, slides). OCR de fórmulas é aproximado.

### Página 2
*(figura em y≈92–264)*
- ISSN 0028-6255
- Informatics and Computer Science
- Intelligent Systems
- Applications
- AN INTERNATIONAL JOURNAL
- Including Special Section
- Nature-Inspired Algorithms for Large Scale Global Optimization
- EAte
- Xiaodong Li. Ke Tang, P.N Suganthan and Zhenyu Yang
- ScienceDirect

### Página 3
*(figura em y≈273–577)*
- multi-objective optimization problems (MOPs) The efficient global optimiza-
- real fitness evaluations. Our experimental results show that the proposed al-

### Página 4
*(figura em y≈273–577)*
- objectives, and consequently a modified game theory is adopted
- efficiently allocate transmission power and data rate to users in
- nondominated sorting genetic algorithm I (NSGA-II) [8], multi

### Página 5
*(figura em y≈273–577)*
- optimization problems, surrogate-assisted evolutionary algorithn
- widely adopted [16]. SAEAs can be roughly classified into two cal
- first category, the expensive objective function is approximated
- an ensemble of surrogates. More specifically, computationally effi
- models are constructed using historical data and then used to al
- fitness values of the candidate solutions instead of computing
- For example, Marjavaara [17] replaced the three-dimensional mc
- the diffuser shape design problem. In the second category, the
- as a classifier to filter the newly generated candidate solutions
- predicted labels. Consequently, several classification-based SAI
- developed, e.g., the classification and Pareto domination based
- the classification-based SEA (CSEA)[19].

### Página 6
*(figura em y≈273–577)*
- ration with exploitation. Hoyle et al. adopted a GP model to pi
- Nevertheless, it is non-trivial to build effective surrogate mo

### Página 7
*(figura em y≈273–577)*
- as the selection criterion by ranking the mean value of uncertair
- tion to achieve the best trade-off between exploitation and expl
- the search process, which is of pivotal importance in optimizatic
- introduction to the background knowledge related to Bayesian 01
- Section 3, a pilot study to investigate the efficiency of each propc

### Página 8
*(figura em y≈273–577)*
- information denotes the confidence level of the prediction, whicl
- [32] is that there is a multivariate Gaussian distribution on Rn fc
- {x', x?,...xN}T. Given a set
- where u 1S the mean of the stochastic process, and e(x) IS drawn tri
- process with zero mean but non-zero standard deviation o
- E(x) ~ N (0, o?)
- function with additional hyperparameters, rather than an Euck

### Página 9
*(figura em y≈273–577)*
- 2 (01, ..., ON, PI, ..., PN) = ¿ (Nino?
- + In det (C)
- Therefore, the estimates _ and ÷2 for the true values u and
- 1"C-ly
- (y - 1P)" C-'(y - 1)
- where 1 denotes a N X 1 column vector of ones. Based on the giv
- data point x"ew,
- x"ew) = û+r'C-1 (y - 1û)
- H (xnew )2 =8°11-1"C-114 (L-1"C-DE
- (Corr(x"ew, x1), ..., Corr(xnew,x))T presents a cor
- between new and each element x' in X.
- 1 caicition Fictior

### Página 10
*(figura em y≈154–577)*
- u(x))+o(x,-
- Ku(x,)-o(x))
- predictions of the GP mean values and standard deviation values (p(:) and
- new data points (21, T2 and 13). The solid line and the shaded area indicate
- confidence intervals estimated with the GP model.
- and by sequentially finding its optimum we are able to guide the se
- The AF proposed in this work is inspired from the lower confi

### Página 11
*(figura em y≈273–577)*
- RVEA, a set of reference vectors are predefined in the objectiv
- (1 + P(0 F.a, vr., )) • ||ft,i
- Here, dt.i.j presents the APD value of the i-th solution in terms Oi
- ence vector in the t-th generation, and Zmin denotes the vector
- objective values at the current generation; ||ft.; - Zmin| denotes
- objective value, adopted as a convergence criterion; Ofe.i, Vu.; repre

### Página 12
*(figura em y≈273–577)*
- Vo,i o (Zmax
- where 'o' denotes the Hadamard product that multiplies two vect
- generation, while vo, represents the i-th uniformly distributed re
- and Zmax and Zmin denote the vectors consisting the maximum
- MOEA, is presented, and Fig. 2 gives the flowchart of the propos

### Página 13
*(figura em y≈151–577)*
- Objective Function F(X)
- Sample Data D(0) from
- RVEA
- Train Gaussian
- Process F'(X, t)
- Initialization P(0)
- Parent Population P(t)
- Population Based on The
- Evaluate The Optimized
- Genetic Operators
- Acquisition Function AF(X,t)
- D(t+1) = D(t) + D(X*(t))
- Offspring Population 0(t)
- Selection Criterion to Determine
- Use The Proposed Sampling
- to evaluate objective values
- Use the GP F'(X, t)
- Data X* (t) to Be Evaluated by The
- Expensive Objective Functions
- Output
- ing the new data samples. The proposed framework is intended to efficie
- lection criterion within this framework aim to achieve a better balance bett

### Página 14
*(figura em y≈273–577)*
- Output: The final solution population
- 1: Initialization: Sample 11n - 1 points x1, x?,.., x11n-1 in the decision
- Generate offspring by the simulated binary crossover (SBX) and th
- Combine parent and offspring populations and predict their fitness wil
- by the original objective functions and update FE = FE + u; (see Alge

### Página 15
*(figura em y≈273–577)*
- Himax and O max represent the maximum values of the mean an
- us provided by the GP models, respectively. In this way, botl
- objective value and the uncertainty are normalized to [0, 1]. c is
- parameter defined by a cosine function. FE denotes the current
- objective function evaluations, and F Emax represents the predef
- the previously observed data are preferred to be sampled wher
- promising area. Herein we explain briefly why we select new de

### Página 16
*(figura em y≈232–577)*
- As analyzed in [38, the reference vectors predefined in RVEA divide
- diversity as well as the convergence. To this end, we introduce two diffe

### Página 17
*(figura em y≈273–577)*
- 1: if a < 0.5 then
- 1/ Using the angle-based sampling selection criterion//
- Calculate the Angle(0f I,vi.;) for each individual in the population and select u new
- 4: elself a >= 0.5
- 4. Comparative Stúdies
- benchmark problems from the UF test suite. To examine the efficiency of the

### Página 18
*(figura em y≈273–577)*
- In the following section, we begin with briefly introducing the
- tives suggested in [42], two modified counterparts of DTLZ1 an
- 0.5)2 cos(20T (x; - 0.5))], i = 1,

### Página 19
*(figura em y≈273–577)*
- formance metrics in our experiments. Let P* be a set of uniforr
- 1) GD: GD measures the average distance between the obtair
- vep d(v, P*)
- where |P| is the cardinality of the set P and d(v, P*) is the min
- distance between u and all points in P*. The smaller the GD valu
- 2) Spread (4): Spread is used to evaluate the extent of th
- covered by the obtained set of solutions, defined as
- ELL d(E;, P) + Lvep Id(v, P) - d)l
- ZiE1 d(Ei, P) + (IP| - m)d
- where d(v, P) is the minimum Euclidean distance between v ar

### Página 20
*(figura em y≈273–577)*
- the compared algorithm statistically significantly, while "(-)"
- is no significant difference between them.

### Página 21
*(figura em y≈273–650)*
- in Table 1, it can be seen that SM-MOEA significantly outperforms the orig-
- inal RVEA in terms of IGD values on DTLZla, DTLZ2, DTLZ3a, DTLZ6 as
- well as DTLZ7, while there is little difference between SM-MOEA and RVEA

### Página 22
*(figura em y≈198–577)*
- DTLZla
- 0.000 0.238 (+) 0.728 0.000 0.857 (+) 0.982 0.403 0.855 (+) 0.979 10.000 0.000 0.000
- significant improvements over RVEA as the adaptive AF utilizing a nonlinear
- aggregation function to take both the uncertainty and the predicted mean fitness
- These results together confirm the effectiveness of the suggested adaptive AF.
- a limited number of real fitness
- evaluations. In addition, AB-MOEA significantly outperforms RVEA on all the

### Página 23
*(figura em y≈223–577)*
- DTLZI
- DTLZla

### Página 24
*(figura em y≈216–666)*
- DTLZla
- DILZla

### Página 25
*(figura em y≈199–628)*
- The obtained solutions
- The obtained solutions
- (a) The non-dominated solutions obtained (b) The non-dominated solutions obtained
- The obtained solutions
- The obtained solutions

### Página 26
*(figura em y≈153–577)*
- The obtained solutions
- The obtained solutions
- (a) The non-dominated solutions obtained (b) The non-dominated solutions obtained
- The obtained solutions
- The obtained solutions
- (c) The non-dominated solutions obtained (d) The non-dominated solutions obtained

### Página 27
*(figura em y≈273–577)*
- on all three-objective benchmark problems considered in this WC
- EGO is able to achieve well converged and evenly distributed fir
- DTLZ6; however, its performance on the rest of problems is mi
- tors, GD and spread metrics are adopted to investigate the CC

### Página 28
*(figura em y≈273–577)*
- (here, 300 evaluations) is affordable. In the following, a brief
- B-spline (NURBS) are used to control the curvature of the ur
- drag and lift coefficients (Ca and Cr) for any given geometry of
- maximize the lift coefficient.
- We compare AB-MOEA with K-RVEA and B0 [37] in terms

### Página 29
*(figura em y≈180–577)*
- (a) The non-dominated solutions obtained (b) The non-dominated solutions obtained

### Página 30
*(figura em y≈273–577)*
- Our results demonstrate that the proposed algorithm significant
- the compared algorithms on most test problems and is also able tc
- lems used in our experiments, we find that the proposed algoritl
- ness of the fitness landscape. Consequently, future research co
- very different computational complexities.

### Página 31
*(figura em y≈273–577)*
- power and rate allocation in wireless networks: A non-coc
- jective genetic algorithm: NSGA-II, IEEE Transactions 01

### Página 32
*(figura em y≈273–577)*
- [14] Y. Jin, B. Sendhoff, A
- objective multi-fidelity evolutionary algorithm, Informatio
- [17] B. D. Marjavaara, T. S. Lundström, T. Goel, Y. Mack, W. S
- turbine diffuser shape optimization by multiple surrogate
- [18] J. Zhang, A. Zhou, G. Zhang, A classification and pareto doi

### Página 33
*(figura em y≈273–577)*
- [22] F. A. Viana, R. T. Haftka, L. T. Watson, Efficient globe
- [23] D. Buche, N. N. Schraudolph, P. Koumoutsakos, Acceleratir
- algorithms with Gaussian process fitness function models,
- tions on Systems, Man, and Cybernetics, Part C (Applici
- [24] N. Hoyle, N. W. Bressloff. A. J. Keane, Design optimiza

### Página 34
*(figura em y≈273–577)*
- terion for evolutionary multiobjective optimization of exper
- [33] D. R. Jones, M. Schonlau, W. J. Welch, Efficient global opti

### Página 35
*(figura em y≈273–577)*
- Conference on Uncertainty in Artificial Intelligence, 2013,

### Página 36
*(figura em y≈273–577)*
- [49] Y. Tian, R. Cheng, X. Zhang, Y. Jin, PlatEMO: A MAI
- for evolutionary multi-objective optimization, IEEE Compi

### Página 37
*(figura em y≈273–577)*
- non-financial interest (such as personal or Pre-proc
- ity with a financial or non-financial interest in the subject matter or ma
- nature of the conflict on a separate sheet of paper if the
*(figura em y≈25–98)*
- Journal Pre-proof
- Conflicts of Interest Statement

### Página 38
*(página inteira)*
- Journal Pre-proof

### Página 39
*(figura em y≈273–577)*
- " PrE-PrOc
- 'ournal Pro
