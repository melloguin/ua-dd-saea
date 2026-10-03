# mtm4. Single- and Multi-objective Evolutionary Optimization Assisted by Gaussian Random Field Metamodels

> Fonte (original): mtm4. Single- and Multi-objective Evolutionary Optimization Assisted by Gaussian Random Field Metamodels.pdf
> Extraído com pymupdf4llm (texto + tabelas + números; imagens omitidas). Páginas: 18.

---

1 

# Single- and Multi-objective Evolutionary Optimization Assisted by Gaussian Random Field Metamodels 

Michael Emmerich, Kyriakos Giannakoglou, Boris Naujoks 

**_Abstract_ — This paper presents and analyzes in detail an efficient search method based on Evolutionary Algorithms (EA) assisted by local Gaussian Random Field Metamodels (GRFM). It is created for the use in optimization problems with computationally expensive evaluation function(s). The role of GRFM is to predict objective function values for new candidate solutions by exploiting information recorded during previous evaluations. Moreover, GRFM are able to provide estimates of the confidence of their predictions.** 

**are used by the Metamodel Assisted EA (MAEA). It selects the promising members in each generation and carries out exact, costly evaluations only for them. The extensive use of the uncertainty information of predictions for screening the candidate solutions makes it possible to significantly reduce the computational cost of single- and multi-objective EA. This is adequately demonstrated below by means of mathematical test cases and a multi–point airfoil design in aerodynamics.** 

**_Index Terms_ — Evolutionary Optimization, Metamodeling, Uncertainty Prediction, Kriging, Gaussian Random Field Models, Multi-objective Design Optimization** 

## I. INTRODUCTION 

Optimization problems, with ng (ng ≥ 0) inequality constraints gi can be cast in the form of minimization problems with nf (nf ≥ 1) objective functions fi: 



The search space S is defined as S := [xmin, xmax], where xmin and xmax are user-defined lower and upper bounds for the design variables. Single-objective optimization (nf = 1, ng = 0) is an important special case of the problem formulation. Multi-objective optimization problems are either constrained (ng > 0) and/or multi-objective (nf > 1) ones, though multi-objective, constrained problems (nf > 1, ng > 0) often occur. In the multi-objective case, it is a common 

M. Emmerich is Assistant Professor at the Leiden Center of Advanced Computer Science (LIACS), University of Leiden, Niels-Bohr-Weg 1, CA3335 Leiden, The Netherlands, emmerich@liacs.nl 

K. Giannakoglou is Associate Professor in the School of Mechanical Engineering of the National Technical University of Athens, Lab. Of Thermal Turbomachines, Athens, Greece, kgianna@central.ntua.gr B. Naujoks is with the Chair for Systems Analysis, Computer Science Dept., University of Dortmund, 44221 Dortmund, Germany, boris.naujoks@uni-dortmund.de 

strategy to search for an approximation to the Pareto optimal set instead of a single optimal solution. 

Often, it is not possible to evaluate the objective function precisely. Noise due to physical experimentation is a typical example of a _source of uncertainty_ . On the other hand, if deterministic computer models are used, uncertainties related to the evaluation might occur. In this paper, we focus on uncertainties that arise, whenever – for the purpose of cost reduction – imprecise fast evaluations replace the precise ones. For a general survey on the treatment of uncertainties in EA the reader should refer to [1]. 

This paper is concerned with optimization problems in which the evaluation of candidate solutions require timeconsuming simulation software (such as Computational Fluid Dynamics, CFD, tools for applications in fluid mechanics and aerodynamics, Finite Element, FEM, tools for structural analysis, etc). The high CPU cost of a single evaluation makes search methods, which are capable of locating global optima through the minimum number of evaluations, attractive. Note that, in most real–world problems, the functional relation between input variables and responses is very complex. 

EA are well-established techniques for multivariate optimization with highly-nonlinear solution spaces. They can be adapted to different computing environments and problem specific knowledge can be integrated into their search operators. The concept of population-based search allows their use for global optimization. 

However, standard EA need a large number of function evaluations in order to reach a global or local optimum with adequate precision. EA using computationally expensive evaluations may reduce their CPU cost through metamodeling [2], [3], [4], [5], [6], [7], [8], [9], [10]. Metamodels should be understood as surrogate evaluation models that are built using existing information. The cost of training a metamodel depends on its type and the training set size. Compared to the cost of an exact evaluation, that of training and using the metamodel is relatively low. 

Nowadays, in EA neural networks (ANN) are frequently employed to screen candidate solutions. Multilayer perceptrons [11] or exactly interpolating radial basis function (RBF) networks [6] can be used, either in their standard forms or by incorporating add-on features such as measures for the relative importance of input variables (cf. Giannakoglou [6], [12]). Kriging models (or Gaussian Random Field models (GRFM), [3], [13], [14], [9]) are in use, too. An overview on metamodeling approaches in Evolutionary Computation can be 

2 



<!-- Start of picture text -->
found in [7]. Recent publications show, that metamodels are y<br>beneficialand multi-objective optimization [15],to speed up the evolutionary[16],search[17],in[18],constrainedthough y(1) y(3) Predicted Function<br>FieldThisthethereRecently, screening methods also consider the confidence ofpredictedinformationaremodelsstill whichoutputopencanquestions.predicthavebe obtainedbeenthe suggestedunknownthroughevaluation[3],Gaussian[9], [13],resultRandom[19].by Confidence Range y ������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������ (2) 
�
�
�
�
�
�
�

�
�
�
�
�
�
�

�
�
�
�
�
�
�

�
�
�
�
�
�
�

�
�
�
�
�
�
�

�
�
�
�
�
�
�

�
�
�
�
�
�
�

�
�
�
�
�
�
�

�
�
�
�
�
�
�

�
�
�
�
�
�
�

�
�
�
�
�
�
�

�
�
�
�
�
�
�

�
�
�
�
�
�
�

�
�
�
�
�
�
�

�
�
�
�
�
�
�

�
�
�
�
�
�
�

�
�
�
�
�
�
�

�
�
�
�
�
�
�

�
�
�
�
�
�
�
 y(x’)+s(x’) ^ y(x’)−s(x’) ^ y(x’) ^ ’ ^^<br>formation increasesmeans of a Gaussianthedistribution.prediction accuracyThe use ofof theconfidencemetamodelin- x(1) x(2) x’ x(3) x<br>and helps guiding the search towards less explored regions in<br>the search space. This also prevents premature convergence. Fig. 1. Outputs of Gaussian Random Field Metamodels using a<br><!-- End of picture text -->

Fig. 1. Outputs of Gaussian Random Field Metamodels using a R → R mapping example. 

In this paper, the term _pre-screening_ will denote the use of metamodels for the selection of promising members which are not evaluated so far. Criteria that can be used to support prescreening procedures by incorporating confidence information are introduced; their concept is discussed and statistical studies of their performance are presented. These criteria figure out improvements in a set of new (offspring) solutions, assuming that the unknown response is described by a Gaussian distribution. 

sense. On the other hand, the term _Gaussian random functions_ [21] might be misleading, because a random function is often associated with a single random variable instead of a set of them. However, in the present paper, the term Gaussian Random Field seems to be more appropriate than _Gaussian Process_ [22] since this paper is dealing with a multidimensional – spatial – rather than a one-dimensional – temporal – input space [23]. 

In order to extend the application domain of the proposed methods, pre-screening criteria used in single-objective problems will be generalized to constrained and multi-objective problems. After scrutinizing a number of mathematical optimization problems, a challenging aerodynamic design problem with 3 objectives and 6 constraints will be solved. The results presented below indicate that it is very beneficial to consider the confidence information within a MAEA, in order to improve its robustness. 

Apart from the predicted objective function value, another information provided by a GRFM is a measure of confidence for its prediction. It is reasonable that the confidence is expected to be higher if the training point density in the neighborhood of a newly proposed point is higher. Another important output of the metamodel is the variance of the output values and the average correlation between responses at neighboring points. A GRFM interpolates data values and estimates their prediction accuracy. It provides the mean value and the standard deviation for a one-dimensional Gaussian distribution which represents the likelihood for different realizations of outcomes to represent a precise function evaluation. Figure 1 illustrates the use of GRFM in an example mapping R → R. 

The structure of this paper is as follows: In section II, GRFM are presented and discussed. In section III, the singleand multi-objective EA used are presented. In section IV, the integration of GRFM in single- and multi-objective EA is outlined. Finally, using a number of academic test cases (section V) and a real-world test problem (section VI), the efficiency of the proposed MAEA is investigated. 

The user of modern optimization methods desires to operate the metamodel in the most efficient manner, i.e. to maximize its prediction capabilities and minimize the CPU cost for its training. For this purpose, a better understanding of the statistical assumptions, limitations and practicalities related to the model itself and its use are needed. 

## II. GAUSSIAN RANDOM FIELD METAMODELS 

The Gaussian Random Field (GRF) theory constitutes a powerful framework for building metamodels based on data obtained through computer experiments. _Gaussian Random Field Models_ (GRFM) will be defined below, by first putting emphasis to the information required by the model as well as its responses after training. Later, statistical assumptions, limitations and practicalities related to the model itself and its use will be discussed. 

Let y : R<sup>d</sup> → R be the output of a computationally expensive computer experiment and X = {x<sup>(1)</sup> , . . . , x<sup>(m)</sup> } be a set of m input configurations which are available along with the corresponding responses y<sup>(1)</sup> = y(x<sup>(1)</sup> ), y<sup>(2)</sup> = y(x<sup>(2)</sup> ), . . . , y<sup>(m)</sup> = y(x<sup>(m)</sup> ). No assumption on the regularity of the distribution of x<sup>(1)</sup> , . . . , x<sup>(m)</sup> in S is made. 

In the literature, GRFM are also known under different names, such as Kriging, Gaussian processes and Gaussian random functions methods. The term _Kriging_ points directly to the origin of these prediction methods dating back to the sixties, when the mining engineer Krige used GRFM-like models to predict the concentration of ore in gold- and uranium mines [20]. Today, Kriging includes a wide class of spatial prediction methods which do not necessarily assume Gaussian 

In GRF theory, the aim is to build a non-time-consuming tool capable of predicting the output corresponding to a new point x<sup>′</sup> ∈ S, according to an approximated R<sup>d</sup> → R mapping. With x<sup>′</sup> ∈ X, the precise objective function value is returned. This corresponds to the well known exact interpolation problem for which a large variety of methods, ranging from splines [24] to radial basis networks [25] and Shepard polynomials [26], are available. 

The basic assumption in modeling with GRFM is that the output function is a realization (sample-path) of a Gaussian 

Note that the latter assumption is essential in our algorithms and the term GRFM is used herein in the standard (strict) 

3 



<!-- Start of picture text -->
Weakly correlated landscape<br>Realization F(x)<br> 500<br> 400<br> 300<br> 200<br> 100<br> 0<br>-100<br>-200<br>-300<br>-400<br>-500<br> 10<br> 8<br> 0  6<br> 2  4 x2<br>x1 4  6  8  10  0  2<br><!-- End of picture text -->

Fig. 2. Sample path of a 2-dim. GRF with low correlation approximated through Krigifier [27]. 



where θi, i = 1, . . . , d denote correlation parameters. For the related isotropic Gaussian kernel, the assumption θi = θ = const., i = 1, . . . d is made. 

The θ-parameter(s) as well as β and s<sup>2</sup> are invariant with respect to F. Their values can be estimated through a sample by generalized least square methods; θ can be estimated by maximum likelihood hypothesis, by minimizing 





with 



<!-- Start of picture text -->
Strongly correlated landscape<br>Realization F(x)<br> 400<br> 300<br> 200<br> 100<br> 0<br>-100<br>-200<br>-300<br> 1<br> 0.8<br> 0  0.6<br> 0.2  0.4 x2<br> 0.4x1  0.6  0.8  1  0  0.2<br><!-- End of picture text -->

Fig. 3. Sample path of a 2-dim. GRF with high correlation approximated through Krigifier [27]. 

random F. The latter is a mapping that assigns a 1- dim. Gaussian distributed random variable F(x) with constant mean β := E(F) and variance s<sup>2</sup> = Var(F) to each point x of an input space S (which is typically R<sup>d</sup> ). Two examples of GRF sample paths are given in Figure 2 and 3. In contrast to other modeling techniques such as linear regression, a spatial correlation between the output values is assumed. For two arbitrary inputs x and x<sup>′</sup> , this is expressed by a correlation function with 



Typically the correlation function is assumed to be stationary, i. e. 



or isotropic 



where d(x, x<sup>′</sup> ) is the relative distance between inputs. 

In the design and analysis of computer experiments literature [28], the isotropic Gaussian kernel and the Gaussian product kernel are often used. The latter reads: 



using the following generalized least square estimates [29] of β and s<sup>2</sup> 





The algorithm estimates the parameters iteratively in a multivariate maximization of PDF(F(X) = y) with variable θ. The cost of the maximization depends on the number of variables in θ. Generally, it is not always possible to solve this optimization problem in closed form due to nonlinearities. Quasi–Newton methods can be employed for its solution. Partial derivatives of the likelihood formula are given in [29]. However, since the problem is multimodal (cf. Mac Kay [22]), it cannot be guaranteed that its precise solution can be obtained with gradient based methods. Thus, direct search methods like multidimensional pattern search algorithm [4] or evolution strategies [9] have been employed to improve numerical robustness. 

In order to solve the maximum likelihood problem, typically, a simplified mathematical problem is cast and solved, which has the same optimum with PDF(F(X) = y), namely 



The expression is derived as follows: By substituting sˆ<sup>2</sup> (equation 11) in the exponential term of equation 8 we get: 





Expressed as the minimization of the denominator, it yields 



Finally, through logarithmic calculus and elimination of constant values, equation 12 is obtained. 

An alternative is to calculate these parameters by means of cross validation [21], [30]. For practical optimization, it 

4 

is suggested to use leave-one-out cross validation (LC) [21] for adapting θ. Furthermore, it is suggested to use the median deviation instead of the average deviation to the known outputs in order to increase robustness at outliers. 

Having estimated these values for the set of inputs, we can derive the conditional distribution of F at x<sup>′</sup> , denoted by F(x<sup>′</sup> |X, y), given the information X, y. The prediction ˆ of a new output vector is now y(x) = E(F(x<sup>′</sup> |X, y)) with the corresponding variance s<sup>2</sup> (x) := Var(F(x<sup>′</sup> |X, y)). This yields 



with 



which can be rewritten as a linear predictor 



with 



Assuming that the value of β is known, the local variance s<sup>2</sup> (x) = Var(F(x<sup>′</sup> )|X, y) for this random variable is given by 



However, if the maximum likelihood estimate β<sup>ˆ</sup> is used instead of β, Schonlau [31] suggests to use the more pessimistic expression sˆ<sup>2</sup> (x) defined as 



rather than s<sup>2</sup> (x). 

The derivation of these equations can be found in Sacks et al. [28]. Schonlau et al. [29] interprets the term c<sup>T</sup> C<sup>−1</sup> c(x) as the reduction in prediction error due to being correlated with the sampled points. The term (1 − 1C<sup>−1</sup> c(x))<sup>2</sup> /(1<sup>T</sup> C<sup>−1</sup> 1) is added, if the exact value of β is unknown and is estimated only from the sample. For a known β value, a simplified expression results. 

Note that the time complexity for the training of the metamodel is O(Nm<sup>3</sup> d + m<sup>2</sup> d), where N ≥ 1 denotes the number of iterations spent for adjusting the metamodel parameters θ, µ and s<sup>2</sup> and d is the dimension of the search space. Once the metamodel has been trained, each prediction requires O(nm<sup>2</sup> ) elementary operations (if sˆ(x) is to be computed) or O(nm) (if yˆ(x) is to be computed). 

The number of training points is the main factor that determines the training cost. Thus, it is recommended to use only the minimum necessary subset of the total number of samples available in the database, for the metamodel training. A well performing heuristic is to use a small number of Nr points which are closest<sup>1</sup> to each new point x<sup>′</sup> and train a 

new, locally valid metamodel. Such a strategy would be called _local metamodeling_ in contrast to _global metamodeling_ , for which all evaluated points in the search space are used to build the model. Local metamodels have been proposed in [5] and, later, adapted by other authors, [3], [32]. For a systematic study of the number of neighbors we refer to [3]. The authors suggest to use ≥ 2d neighboring points for the purpose of local metamodeling. In this paper, Nr = 2d is chosen in order to keep the computational effort low. 

## III. EVOLUTIONARY ALGORITHMS 

EA originated as models of biological adaptation processes in the early 60ties for the purpose of parameter optimization [33]. Among the existing variants of EA, only a few have undergone a thorough theoretical investigation. Among them are Evolution Strategies (ES) [34], [35], often used in realvalued function optimization. Their convergence behavior has been studied on a large number of theoretical [36] and realworld test cases. The (µ + λ)-EA that will be described below bears many of the well known features of ES. However, for the purpose of the present paper, the (µ + λ) scheme is not restrictive by any means and any other EA could be used instead. 

With µ parents and λ offspring, the (µ + λ)-EA works as follows: 

|**Algorithm 1** (µ+λ)**-EA**|
|---|









The(µ+λ)-EA starts with initializing the _generation_ counter t (algorithm 1). After generating the initial population with µ individuals by uniform random sampling in S, the EA generates λ new solutions in S through _recombination_ and _mutation_ [33]. The new candidate solutions are evaluated and ranked in terms of their quality. The µ best solutions in Gt∪Pt are selected to form the new _parent_ population Pt+1. 

In this paper, individuals consist of a real-valued vector x ∈ R<sup>d</sup> and a single step-size σ ∈ R<sup>+</sup> . The variation procedure ( _generate_ ) used in the present study is described in algorithm 2. For details on variation procedures used in ES the reader should refer to Beyer [36]. ES works with a robust and fast mutative self-adaptation of a single step size and γ = 1.3 (algorithm 2). This kind of mutation has been recommended by Beyer for the starting phase of an EA [36]. Here, N(0, 1) denotes a Gaussian distributed random number and ’or’ symbolizes a uniform random choice. 

The (µ+λ)-EA for single-objective, constrained, and multiobjective optimization differ in the ranking of solutions during the _select_ procedure. 

> 1with regard to the euclidian metric 

5 



**Algorithm 2** Generation of a new individual (x<sup>′′</sup> , σ<sup>′′</sup> ) from Pt in the simple (µ + λ)-ES 







Dealing with a single objective only (nf = 1, ng = 0), it is reasonable to establish an order among individuals by comparing the values of f1. In constrained optimization, Hoffmeister and Sprave [37] proposed the following preference relation to guide the search towards the (feasible) global optimal point: 



with 



There are many other ways to deal with constraints; however, the one suggested here is well suited for use within rank based algorithms with metamodel assistance. It allows for an independent modeling of constraint functions. Hence, neither discontinuities or non-differential points are introduced, nor are non-linear combinations of prediction terms to be handled. This will further be discussed in section IV. 

Since EA are population-based search methods, they are also suitable for Pareto optimization for multi-objective problems (nf > 1). In Pareto optimization, a set that is dominant with respect to the relation ≺p, defined as 



is sought. In constrained multi-objective problems, equations 21 and 22 can be combined. 

A straightforward method for adapting the (µ + λ)-EA to Pareto-optimization is through NSGA-II [38]. The population is first partitioned by means of non-dominated sorting (figure 4) and, then, sharing is employed (figure 5) by considering distances between individuals of the same rank. 

A comprehensive overview on this and other Pareto front methods can be found in Deb [39] and Zitzler [40]. 

## IV. METAMODEL-ASSISTED OPTIMIZATION 

Aiming at the minimum possible number of costly evaluations during the search for the optimal solution(s), black-box 



<!-- Start of picture text -->
f2<br>3<br>2 3 3<br>1<br>Co−domain of (f1, f2)<br>2 3<br>Pareto optimal 1 3<br>        front 2<br>1<br>1<br>1<br>f1<br><!-- End of picture text -->

Fig. 4. Non-dominated sorting: The population is partitioned in subpopulations of equal dominance rank. The non-dominated subset of the population is identified and its members are given rank 1. Then, the nondominated set from the remaining individuals is computed and given rank 2. This goes on until a rank is assigned to each individual. 



<!-- Start of picture text -->
f2<br>1<br>Co−domain of (f1, f2)<br>3<br>Pareto optimal 4<br>        set<br>5<br>2<br>f1<br><!-- End of picture text -->

Fig. 5. Distance-based sorting of the Pareto front members: The circumference of the boxes touching neighboring solutions determines their final rank. Thus, individuals lying away from their closest neighbors are promoted. 

optimization methods can incorporate metamodels in different ways. 

- The metamodel is trained at a pre-processing phase and the optimization algorithm searches for the optimal solution based exclusively on the metamodel; the socomputed optimum is then evaluated by means of the exact-costly tool, the metamodel is updated after enriching the training database and the above steps are repeated until a convergence criterion is met. Bayesian global optimization algorithms work in this way [41], [31]. In MAEA, the term “generation-based control” denotes algorithms in which some generations are evaluated by the exact tool and some other generations are evaluated solely by the metamodel. 

- In each generation (apart from the very ones), metamodels and exact evaluation tools are used in cooperative manner. The evaluation of population members does not rely entirely on the metamodel but the latter is used to improve the efficiency of the local search steps. 

6 

This is where the present paper puts emphasis. In highdimensional search spaces, a single metamodel might fail to give predictions of acceptable accuracy over the entire search space. The remedy is to switch to local search strategies supported by local metamodels, [5], [19], [32], [42]. In the literature, the term “individual-based control” has been used to denote such a use of metamodels in MAEA. 

The idea to assist direct search algorithms by metamodels has first been explored by Torczon et al. [4], [42] for pattern search algorithms. The metamodel was used to decide on the sequence in which the search point located on the pattern of local variations in pattern search should be evaluated. A similar approach can be employed in EA by incorporating a pre-screening procedure before the offspring population is evaluated with the time consuming evaluation tool. Algorithm 3 gives an outline of MAES which is, in fact, a modified version of the basic (µ + λ)-ES described in algorithm 1. Two features distinguish MAES from standard ES. 

- 1) All exactly evaluated individuals are recorded. 

- 2) During the pre-screening phase, the objective function values for new solutions are predicted by the metamodel, before deciding whether they need to be re-evaluated by the exact and costly tool. 

Thereby, at generation t, the set of offspring solutions Gt is reduced to the subset of offspring solutions Qt, which will be evaluated exactly and will also be considered in the final selection procedure. 

**Algorithm 3** (µ + ν < λ) **-MAES** 



t ← 0 

Pt ← init() _/*_ Pt ∈ S<sup>µ</sup> _: Set of solutions */_ evaluate Pt and insert results to database D **while** t < tmax **do** 

Gt ← generate(Pt) _/* Generate_ λ _variations */_ **evaluate** Gt with metamodel derived from D **choose** set of maximal ν promising solutions Qt ⊆ Gt evaluate Qt and update database D with results Pt+1 ← select(Qt ∪ Pt) _/* Rank and select_ µ _best */_ t ← t + 1 

## **end while** 



Next, the pre-screening procedures for the MAES will be introduced, starting from single objective optimization and generalizing to the multi-objective case later. For higher dimensional solution spaces (nf + ng > 1), it is proposed to predict all objective and constraint values independently, instead of learning aggregate expressions. For notational convenience we introduce y1 = f1, . . . , ynf = fnf , ynf +1 = ygˆ1i , . . . , yand correspondingnf +ng = gng .standardAccordingly, wedeviationsdefinesˆi, i = 1the predictions, . . . , nf + ng. In single objective optimization, we will omit the index, whenever it seems suitable. 

## _A. Pre-screening procedures for single-objective optimization_ 

A ranking algorithm, applied over the offspring population Gt, identifies the most promising individuals in the new 

generation. In the general case, this algorithm is based on the values yˆ1(x) (predictions for f1(x)) and sˆ1(x) (corresponding standard deviations) obtained for each x ∈ Gt through the metamodel. Comparisons with objective function values for the parent population Pt are necessary. Various criteria for identifying promising solutions are discussed below. Once the promising subset Qt of Gt has been found, its members undergo exact evaluations. 

The proposed criteria are all related to the notion of _improvement_ . In minimization problems, the _improvement_ I(y) of a solution with the (predicted) objective function value y with respect to the current optimal solution with objective function value fmin is defined by 



As it will become clear below, in this expression, y could be replaced by any other function value predicted by the metamodel. In any case, a reasonable choice is that fmin takes on the function value of the best individual in the parent population, whenever a (µ + λ)-selection is used. 

The simplest way to pre-screen new solutions is by ranking them through the _most likely improvement_ criterion, denoted by MI(x) = I(ˆy(x)) (where y in expression 23 is defined in terms of yˆ(x)). This criterion makes use of the predicted mean function value without considering the confidence information sˆ(x). Stated differently, this criterion reflects the improvement achieved when the response value with maximum probability density function is considered. Conceptually, this criterion is similar to any pre-screening which is based on any kind of neural networks. 

In this paper, the main issue is how to from the uncertainty information provided by the metamodel. For minimization problems, Torczon et al. [4], [43] suggested the use of the _lower confidence bound_ (LB) of a prediction 



instead of the predicted value itself. The idea is to increase the number of evaluations in promising but less explored regions of the search space by directing the search towards them. Emmerich et al. [19] demonstrated that flb is also a good criterion in the context of MAEA. In particular, in multimodal optimization problems the optimization results improved significantly. 

By choosing ω, the user can scale the MAES from fast local search to more explorative global search [43]. However, the choice of an extra parameter might also be seen as a burden to the user. A reasonable choice is ω = 2, which leads to a high confidence probability (ca. 97 %) for flb(x) to be the lower bound of f (x), once the GRFM assumptions are valid. Still, a fast local convergence on smooth problems is possible [19]. 

In order to get rid of the ω parameter, Ulmer et al. [9] suggested the use of the _probability of improvement_ (PoI). Let φ denote the probability density function 



7 

and Φ denote the cumulative distribution function of the standard normal distribution 



respectively. Let, also, fmin be the objective value of the current best solution. Then, the probability of improvement is as 



Though, dimensionally, this criterion is not directly based on responses, it can be used to rank the population members. An important feature of the PoI criterion is that it equally promotes solutions that are likely to give very small improvements with high (i.e. around 0.5) probability and those expected to lead to considerable improvement with small probability. According to the applications shown in [9], a significant improvement compared to the mean value criterion is expected. 

Another parameter–free approach that also takes the quantitative amount of improvement into account is the _expected improvement_ (ExI) criterion proposed by Schonlau et al. [31] within the context of Bayesian global optimization. It reads 



Using the aforementioned four improvement criteria, various pre-screening processes can be derived. As rule of the thumb, it is desirable to increase the number of qualified solutions whenever the pre-screening identifies too many promising solutions or to decrease it, if the predicted quality is low. Within the proposed algorithm, this is decided upon the comparison of the expected quality of each candidate solution with the quality of parent solutions. However, the user needs to define a maximum and minimum number of qualified solutions in order to avoid convergence stagnation or excess number of evaluations within the generation. With regard to the latter, it should be noted that quite a few iterations are needed in order to adapt the step-sizes and allow for refined search in high-performance regions. In this paper, the maximum number νt := |Qt| of exact evaluations in each generation may vary between 1 and µ. 

According to the previous discussion, we recapitulate the pre-screening procedures used in this paper, with some comments on their use: 

_a) Mean value (MI) Pre-screening:_ It is based on MI(x). Note that solutions with MI(x) = 0 are not selected, unless there is at least one individual with a higher function value. 

_b) Probability of Improvement (PoI) Pre-screening:_ The (µ) best individuals according to the probability of improvement (PoI) criterion are selected. Alternatively, the user may provide a threshold value by specifying a minimal probability of improvement, e. g. 0.2 which will remain constant during the search. 

_c) Expected Improvement (ExI) Pre-screening:_ Based on the ExI criterion, the µ best solutions are pre-selected. A threshold value for ExI can be provided by the user so that solutions with ExI lower than this threshold are rejected. However, unlike the user–defined threshold value of the PoI criterion, the ExI threshold should dynamically decrease in the vicinity of a local optimum, thus requiring extra parameters to control it. 

_d) Lower bound (LB) pre-screening:_ Based practically on eq. 24, the potential improvement criterion rewards promising solutions located in unexplored regions of the search space. ω is user-defined; ω = 2 seems to be a good choice. 

Compared to the mean value pre-screening, only potential improvements higher than zero are accepted, unless at least one such improvement is found. Note, that getting rid of all the user-defined parameters is impossible. He should specify either ω, ν or threshold values for the PoI and ExI criteria. 

Finally, let us discuss some issues concerning the relationship between the aforementioned pre-screening procedures. At least two points deserve to be highlighted. First of all, the role of the standard deviation is a different one for the LB pre-screening compared to the PoI pre-screening. While for the LB pre-screening, a high value of σˆ always increases the competitiveness of an individual, this does not hold for the PoI pre-screening. For the latter, a high value of σˆ(x) is only rewarding, if yˆ(x) > fmin, otherwise, the probability of improvement decreases with increasing σˆ. Thus, the difference between both pre-screening procedures is larger than it might be expected at first glance, and it is thus well justified to include both into the empirical comparison. Unlike the PoI, the ExI first sinks and then grows again as sˆ(x) increases. This behavior can be easily observed by plotting expression 29. 

Moreover, one might consider a threshold version of the PoI criterion, such that only individuals are accepted, whose value exceeds the threshold – say τ with τ ∈ [0, 1]. It turns out, that this strategy is equivalent to a LB pre-screening using a value of ω such that τ = Φ(−ω). In particular, a threshold version of the PoI pre-screening with τ = 0.5 is formally equivalent to a MI pre-screening. Note, that these equivalences only hold, if no maximal value bounds the number of accepted individuals. 

## _B. Constrained and Multi-objective Optimization_ 

In this section, the aforementioned pre-screening techniques will be extended to optimization problems with multiple objectives. Problems with nf + ng > 1, i. e. problems with implicit constraints and/or multiple objectives, in which the evaluation describes a mapping from R<sup>d</sup> to R<sup>ny</sup> , with ny := ng +nf > 1, will be handled. 

The basic idea is to compute a multivariate probability distribution for a single response vector (the first nf positions in the response and variance vectors correspond to the objective function values and the last ng ones to the constraints) and use this information during pre-screening. By assuming an independent output (which might not always be justified), separate metamodels for the different outputs can be constructed. Thus, an independent Gaussian distribution 

8 

with mean value yˆ ∈ R<sup>ny</sup> and standard deviations ˆs ∈ R<sup>n</sup> +<sup>y</sup> is considered. In the case of correlated outputs, specialized multivariate GRFM (Co-Kriging models) can be employed to calculate the probability distribution of response vectors [25]. 

_1) Treatment of constraints:_ Dealing with a single objective function and one or more constraints (nf = 1, ng > 0), the pre-screening procedures should be based on the preference relation, equation 21. Assuming that the reference solution xmin is feasible, the improvement criteria can be generalized in a straightforward manner. 

The most likely improvement criterion is as 



Note, that this criterion is also valid for general multivariate Gaussian distributions. 

The PoI criterion can be calculated as 



where PDFx denotes the estimated probability density function of response vectors for input x and Hf denotes the dominated hypervolume for xmin 



For independent response vector distributions the PoI criterion can be simply calculated as 



provided that the best solution is feasible. 

Accordingly, the expected improvement criterion reads 



and in the case of a independent PDF (cf. Schonlau et al. [30]) 



Last but not least, the generalization for the LB criterion should be discussed. The concept is to work with the lower bound of a confidence interval, symmetrically placed around the mean prediction value. This can be generalized by working with _confidence interval boxes_ (cf. Figure 6). In the case of independent distributions these boxes can be calculated by B(x) := yˆ ± ωˆs(x). The value for ω can be derived from a user specified confidence probability pα - the probability for the true result to lie inside an interval box (=Pr(y ∈ B(x))) - with the help of the following equation 



<!-- Start of picture text -->
Constraint boundary<br>Mean  values of approximations<br>Lower bound edges of approximations<br>Confidence intervals<br>Probability Density Rank 3<br> 0.2<br> 20<br> 0<br> 20 Rank 2 Rank 1  15<br> 15  0<br> 10 g1<br>f1  5 −5<br> 0 −10<br><!-- End of picture text -->

Fig. 6. Interval boxes for approximations in a solution space with one objective and one constraint function. 



<!-- Start of picture text -->
1 m = 1<br>m = 2<br>m = 3<br>m = 4<br>n =1<br>y<br>n =2<br>P y<br>α<br>n =3<br>y<br>n =4<br>y<br>0<br>0 1 2 3 4<br>Confidence factor ω<br><!-- End of picture text -->

Fig. 7. Computation of the factor ω for a desired pα value and a given number of (assumed) independent response functions ny (equation 36). 

Practically, the ω value can be obtained from a graph of this function (c.f. figure 7). Given the value for ω, we thus get 



Having established these criteria for the pre-screening procedure, all the rest can be worked out as in the single criterion case. 

_2) Treatment of multiple objectives:_ Here, the generalization for nf > 1 and ng = 0 is discussed, but the concepts can easily be extended to ng > 0 (cf. equation 1). According to section III, optimal solutions according to the Pareto dominance relation (cf. equation 22) are sought. Similarly to the constrained case, a multivariate (nf - dimensional) distribution for each point x ∈ S is provided by the GRFM. 

The in the generalization of the pre-screening procedures is that the notions of best found solution and of improvement are not clearly defined in the multi-objective case. The best found solution is equivalent to the _set of nondominated solutions_ Et in the current population Pt. 

In order to have a scalar measure for improvement, which is needed at least for the generalization of the ExI criterion, the dominated hypervolume measure H(P ) of a set P (cf. [40]), i. e. the Lebesgue measure of the dominated hypervolume VD for a restricted solution space (cf. figure 9) can be employed. Fleischer [44] proved that, for countable spaces<sup>2</sup> , 

> 2i. e. all spaces that are relevant if these algorithms are implemented on digital computers. 

pα(ω) = (1 − 2Φ(ω))<sup>ny</sup> . (36) 

9 

the hypervolume measure of a set takes its maximum, if the set found covers the true Pareto set. Furthermore, adding a new point to P , the hypervolume H(P ∪{x}) increases, if and only if x is not dominated by any point in Et and thus Et ∪{x} could be regarded as an improvement of Et. For a normalized solution space, higher values of H reflect better solution sets. _Normalized solution spaces_ are restricted solution spaces for which a gain according to the first criterion is as important as the same gain according to the second criterion. Provided that the user can define such a normalization, the improvement measure is as follows: 



For most practical problems in multi-objective optimization it is easy to find a rough restriction for the solution space. However, it is often difficult to normalize a restricted solution space a-priori. Thus, the improvement measure might be biased towards improvements to one of the objectives. Thus, a quantitative interpretation of I(y(x)) - as it is needed for the ExI criterion - should be handled with care. Given these preliminaries, the pre-screening procedures can be generalized: 

For the _mean value_ and the _lower bound prescreening_ , ranking by means of non-dominated sorting is used, by replacing the true function value by the mean value y(x) of ˆ the approximation or the lower confidence bound y−ωs(x) of the confidence interval box (cf. figure 8), respectively. These strategies are described by Emmerich et al. [45]. 

If the user can provide an adequate normalization of the solution space, the improvement criteria MI(x) = I(y(x)) and LB(x) = I(y(x) − s(x)) may also be chosen for prescreening. 

The PoI criterion can be adopted in a straightforward manner by calculating the integral of the PDF of the response, i.e. 





For independent distributions it is reasonable to partition the non-dominated volume into disjoint rectangles [ymin<sup>i, y</sup> max<sup>i[</sup> with ∪<sup>m</sup> i=1<sup>[y</sup> min<sup>i, y</sup> max<sup>i[=Vnd(Et),[44],andthendetermine</sup> the integral that appears in equation 38 by 



large improvements. Should this be desired, ExI can be used, calculated by the integral 



Integration is much more difficult even if statistical independence is assumed. However, even in this case, piecewise numerical integration over nf dimensional hyper-rectangles seems to be the most appropriate way to deal with this integration. As a simple alternative, one may use MonteCarlo integration by producing N random samples qi of the Gaussian distribution with mean yˆ and standard deviation sˆ and by measuring the increase in hypervolume I(qi). Then, the approximate integral reads: 



. 

An error estimate for the monte carlo estimate is given by: 



Here the variance S<sup>2</sup> is as 



This result can directly be obtained from the theory of monte carlo integration ([46], pp. 11). Regardless of the dimension of the search space, the error scales like 1/√N . 

The progress obtained with the latter criterion heavily depends on the adequacy of the improvement criterion in equation 37 and thus on the adequacy of the solution space normalization. Thus, it is recommended to handle the ExI criterion with care and prefer the LB criterion, whenever the normalization is not clear. 

Also in the constrained multi-objective case, the criteria can be generalized. Assuming independent constraint functions, it suffices to multiply the expressions for PoI and ExI (38 and 41) with the probability of a feasible solutions. Thus, we receive 



and 



## V. METHOD APPLICATION – RESULTS AND DISCUSSION 

Again, Φ denotes the cumulative Gaussian distribution function. The PoI measure is the probability of x to be nondominated by individuals in Et. It is remarkable, that this measure can be calculated without restricting the solution space and making explicitly use of the quantity of the improvement I(x). However, as already mentioned for singlecriterion problems, a possible weakness is that it hardly favors 

## _A. Mathematical Test Problems and Performance Measures_ 

ematical test problems in order to compare the performance of different MAES variants. These variants were tested on different objective function landscapes, featuring minimization of a simple convex function (sphere function, appendix A), a 

10 



<!-- Start of picture text -->
Precise Evaluationson the old Pareto front<br>Mean  values of approximations<br>Lower bound edges of approximations<br>x2<br>Probability Density<br> 0.2<br> 0  20<br> 20 x1 x3  15<br> 15  10<br> 10 f1<br>f2  5  5<br> 0 0<br><!-- End of picture text -->

Fig. 8. Interval boxes for approximations in a solution space with two objectives. 

It is reasonable that none of the metamodels could always retrieve the ensemble of relevant individuals out of Gt. A non-satisfactory metamodel is one which: (a) fails capturing a considerable part of Gt ∩ Mµ(Gt ∪ Pt) or (b) in order to capture as many as possible of them, it additionally selects too many irrelevant individuals. 

The retrieval accuracy, practically in relation to the of the two unpleasant situations just mentioned, i. e. the ratio the relevant solutions retrieved from Gt to the number of all relevant solutions in Gt, is quantified as follows: 





<!-- Start of picture text -->
f2<br>f max<br>f (x1)<br>f (x2) Vd(P )<br>f (x3)<br>Vnd(P )<br>Pareto−front f (x4)<br>f min<br>f1<br><!-- End of picture text -->

Fig. 9. Illustration of the hypervolume measure. 

non-isotropic function (ellipsoid function, appendix B), a discontinuous function (step function, appendix C) and - finally - a highly multimodal function (Ackley function, appendix D). 

MAES testing was carried out using population sizes of µ = 5 and λ = 100 individuals, among which ν = 20 individuals at most were pre-selected for exact evaluation. Each run was repeated 20 times, each of which with a different random number seed. 

The median of the best results found after t evaluations (t ≤ 1000) was plotted. In order to get a reliability measure, the 16th worst function value, i. e. the 80%-quantile of the distribution of the obtained function values, was recorded and presented. For similar studies on 20–dimensional test-cases and with different population sizes the reader should refer to [9], [19], [45] and recently [3]. 



where the optimal values is recall(t) = 1. 

On the other hand, precision(t) is a measure for controlling the second unpleasant metamodel behavior. This is expressed by the ratio of the number of correctly retrieved solutions to the total number of retrieved solutions, namely: 



The optimal value for this criterion is precision(t) = 1. 

Unfortunately, in contrast to quantitative measures such as ˆ y − y plots, specificity measures cannot be evaluated without performing extra evaluations with the costly evaluation tool. Hence, these are useful for statistics on simple academic cases but not for real–world problems. 

## _C. Implementation details_ 

The basic evolution strategy corresponds to the one described previously in section IV. The initial step-size was set to 0.05% of the search space width. The database is formed only by exact evaluations. The metamodel is used from the first generation on. As soon as there are more than 2d solutions in the database, the algorithm switches to the local metamodeling strategy as described in section II. For all strategies, the maximal number of pre-selected individuals was set to µ. 

## _D. Results – Discussion on the performance_ 

## _B. Prediction Accuracy Measures_ 

It is well known that EA are rank-based strategies that are invariant to monotonic transformations of the objective function. Hence, for a metamodel used in conjunction with an EA to be successful, it suffices this to predict the subset of Gt that would be selected by the recombination if all evaluations were precise improvements with respect to the parent population Pt. The so–called _retrieval quality_ of any pre-screening tool (metamodel) can be measured through the _recall_ and _precision_ measures defined below. 

Let Mµ(A) denote the subset of the µ best solutions in A. Pre-screening aims at identifying the members of Gt ∩ Mµ(Gt ∪ Pt) which will enter the next generation. Thus, it is desirable that 



The comparison was conducted on the 20-dimensional sphere model (cf. appendix A). The median of the best found solution is shown in Figure 10. All metamodel-based strategies outperformed conventional strategies (i.e. (5+20)-ES, (5+35)ES<sup>3</sup> , (5+100)-ES) since they ask considerably less function evaluations. An exception is the (1+10)-ES that performs comparable to the MAES that utilized the confidence measure for pre-screening. This is due to the small population incorporated in the (1+10)-ES that allows twice as many generations to be carried out. The best average performance was obtained using the mean value pre-screening. 

Similar results were obtained on the non-isotropic elliptic function (figure 11). This is interesting since, during the choice of the correlation function, we didn’t consider non-isotropic 

> 3This strategy has been added in order to be comparable with Ulmer et al. [9]. 

11 

ones and the metamodel was expected to be less precise than in the isotropic case. However, the results show that the approach is quite insensitive to small “errors” in the model assumptions. It should also be noted that, on this test function, MAES versions outperform all standard ES variants. In particular, the (1+10)-ES was outperformed by the MAES using confidence measures as well. 

Unlike previous test functions, the MAES based on dence measures yielded better results than that using the mean value criterion (figure 12); in fact, the mean value criterion performance was expected not to be good, since the step function is discontinuous. The LB criterion performs slightly worse than the ExI one. The use of confidence measures is advantageous since it drives the search towards the most unexplored regions of the search space, where the sˆ(x) values increase. In contrast, the mean value pre-screening or the conventional ES use to keep searching over already adequately explored regions or areas with negligibly varying cost values (plateaus). 

A typical example of multimodal functions is the 20-dim. Ackley function (Appendix D); the corresponding results are shown in figures 13 (history) and 14 (final results and standard deviations). Here, the advantage of using the confidence measure expressed by sˆ(x) is obvious. As long as the search takes place far from the global optimum, the algorithm behaves as on the sphere function. Later on, the multimodal structure of the search space seems to be reflected on the performance. In this phase, it is important to use the information included in the confidence measure, since this will guide the search towards more unexplored regions, i.e. away from local optima. The advantage of strategies using sˆ(x) becomes significant when looking at the 80% quantile, where all strategies using the uncertainty information outperform those based on the mean value pre-screening; the latter stagnates after about 200 evaluations. 

An additional study was carried out on the 20-dim. Ackley function (appendix D), in order to compare the effect of different parametric settings of MAES. Figure 15 displays the results and reveals that an optimal value for ω exists. For high ω values (ω = 3), the intensive exploration led to low convergence speed. For low ω values (ω ≤ 1), the MAES used to converge to a local optimum, due to the weak exploration. The effect of the number of pre-selected individuals ν on the convergence speed of MAES is also illustrated in figure 15. According to this figure, the high number of generations which were carried out at the same computing cost, due to the low value of ν, led to significantly better results during the first generations but increased the risk of premature stagnation. Note that stagnation occured later than it could even happen if an erroneous ω was used. The choices ω = 2 and ν = 20 led to a similar behavior to those of the ExI and PoI strategies with ν = 20. 

Finally, the long term behavior of the MAES was studied. Figure 16 displays results for a long run with 2000 precise evaluations on the 20-dim. ellipsoid problem. The results indicate that the MAES is capable to approximate a local optimum with a high precision. Another conclusion is that the absolute error of the prediction shrinks proportionally to 



<!-- Start of picture text -->
 1000<br> 100<br> 10<br> 1<br> 0.1<br> 0.01<br> 0.001<br> 0.0001<br> 1e-05<br> 0  200  400  600  800  1000<br>No. of evaluations<br>1p10 5p35 MLI PoI<br>5p20 5p100 LBI ExI<br>Median of the best found function value of different<br>sphere problem.<br> 10000<br> 1000<br> 100<br> 10<br> 1<br> 0.1<br> 0.01<br> 0  200  400  600  800  1000<br>No. of evaluations<br>1p10 5p35 MLI PoI<br>5p20 5p100 LBI ExI<br>Median of best found function value<br>Median of best found function value<br><!-- End of picture text -->

Fig. 10. Median of the best found function value of different EA on the 20-dim. sphere problem. 

Fig. 11. Average convergence behavior of different EA on the 20-dim. scaled sphere problem (ellipsoid problem). 



<!-- Start of picture text -->
 1000<br> 100<br> 10<br> 1<br> 0  200  400  600  800  1000<br>No. of evaluations<br>1p10 5p35 MLI PoI<br>5p20 5p100 LBI ExI<br>Average convergence behavior of different EA on the<br> 100<br> 10<br> 1<br> 0  200  400  600  800  1000<br>No. of evaluations<br>1p10 5p35 MLI PoI<br>5p20 5p100 LBI ExI<br>Median of best found function value<br>Median of best found function value<br><!-- End of picture text -->

Fig. 12. Average convergence behavior of different EA on the 20-dim. step function. 

Fig. 13. Average convergence behavior of different EA on the 20-dim. Ackley function. 

12 



<!-- Start of picture text -->
 30<br>Mean/stdv.<br> 25<br> 20<br> 15<br> 10<br> 5<br> 0<br>1p10 5p20 5p35 5p100 MLI LBI PoI ExI<br>Strategy<br>Best function value after 1000 eval.<br><!-- End of picture text -->



Fig. 14. Summary of the results on Ackley’s function after 1000 evaluations each. The mean value and the standard deviation of the best found result is displayed. 



<!-- Start of picture text -->
 25<br> 20<br> 15<br> 10<br> 5<br> 0  200  400  600  800  1000<br>No. of evaluations<br>nu=5, omega=2 nu=5, omega=3<br>nu=5, omega=0 nu=1, omega=2<br>nu=5, omega=1 nu=15, omega=2<br>80%-quantile of best found function value<br><!-- End of picture text -->

Fig. 15. Development of the 80%-quantiles for best found function values for differently parameterized versions of the MAES. The runs have been conducted on the 20-dim. Ackley function. Different settings for the number of pre-selected individuals ν and the confidence factor ω in the (µ+λ)-MAES using the criterion described in equation 24 are displayed. 



<!-- Start of picture text -->
 10000<br>sampled value<br>absolute prediction error<br> 1000<br> 100<br> 10<br> 1<br> 0.1<br> 0.01<br> 0.001<br> 1e-04<br> 0  500  1000  1500  2000<br><!-- End of picture text -->

Fig. 16. A run of the (20 + 5 < 100)-MAES with PoI pre-screening on the ellipsoid problem with 2000 evaluations. It demonstrates that the MAES is capable to converge to a high precision. Also, it can be obtained that the error of the predictions shrinks proportionally with the distance to the optimum. 

improvements are likely to get lost through the mean value prescreening strategy; however, the high number of relevant solutions identified is, indeed, an improvement. 

Finally, the capability of the GRFM to obtain valid predictions during a run of the MAES on a multimodal problem, was studied. For that purpose, all 1000 evaluations obtained during one run have been compared to their predicted values. The results for the PoI-MAES are displayed in figure 25. There is a strong correlation between predicted and observed values. However, there is also a deviation between these two values. One of the advantages of GRFM is that it provides the degree of uncertainty of each prediction. In order to check the validity ˆ of the lower confidence bound given by ylb = y − 2ˆs, results have also been plotted in a y −ylb diagram (figure 26). It turns out that ylb is a good approximation to the sharp lower bound for the true function values. 

## _F. Discussion of results on constrained optimizations_ 

the distance from the optimum. 

## _E. Discussion on precision and recall_ 

For all pre-screening strategies, the accuracy measures ( _precision_ and _recall_ ) have been evaluated and averaged results (for the 20 runs) are illustrated. 

The best _recall_ values have been obtained through the LB, ExI, and PoI criteria (figures 19, 21, and 23). Their ability to capture a large part of the really top-most individuals (more than 40%) can be discussed after examining the _precision_ plots shown in figures 20, 24, and 22. In all aforementioned cases, the _precision_ is very low. This indicates that high _recall_ values can be achieved by evaluating a large surplus of designs in each generation with the exact evaluation software. The low number of generations needed is probably the reason for the bad performance of these strategies on the simpler test-cases. 

A better balance between accuracy and precision has been achieved through the mean value pre-screening. However, _recall_ (figure 17) stays below 40%, except for the step function. In contrast to the other pre-screening strategies, _precision_ is above 40% (figure 18) most of the time, while the precision for the other strategies stays below 20%. Summarizing, 

In order to evaluate the performance of MAES coupled with different pre-screening criteria in constraint optimization problems, test runs on the 10-dim. Keane problem (appendix E) have been conducted. In this problem, a highly multimodal function has to be minimized, subject to non-linear constraints. 

Results are summarized in 27 (history of median) and 28 (final results and standard deviations). In order to be comparable with previous studies [19] we slightly changed the parameters of the population size and a (15 + 15 < 100)MAES was tested. Two important observations can be made. First of all, any metamodel assisted strategy performs significantly better than the corresponding EA without metamodel assistance. Second, strategies using the confidence information perform much better than the ones utilizing only the predicted function value. The differences between the three pre-screening criteria that use confidence information (lower bound, PoI and ExI) are less significant for this problem. 

## _G. Results on Multi-objective functions_ 

In order to prove the feasibility of the new approach, the multi-objective strategies have been tested on the 10dimensional generalized Schaffer problems F. The curvature 

13 



<!-- Start of picture text -->
 1<br> 0.8<br> 0.6<br> 0.4<br> 0.2<br> 0<br> 0  100  200  300  400  500  600  700  800  900<br>No. of evaluations<br>Sphere 20-D Step 20-D<br>Scaled sphere 20-D Ackley 20-D<br>Average Recall<br><!-- End of picture text -->

Fig. 17. Recall for mean value pre-screening. 



<!-- Start of picture text -->
 1<br> 0.8<br> 0.6<br> 0.4<br> 0.2<br> 0<br> 0  100  200  300  400  500  600  700  800  900<br>No. of evaluations<br>Sphere 20-D Step 20-D<br>Scaled sphere 20-D Ackley 20-D<br>Precision for mean value pre-screening.<br> 1<br> 0.8<br> 0.6<br> 0.4<br> 0.2<br> 0<br> 0  100  200  300  400  500  600  700  800  900<br>No. of evaluations<br>Sphere 20-D Step 20-D<br>Scaled sphere 20-D Ackley 20-D<br>Recall for lower bound pre-screening.<br> 1<br> 0.8<br> 0.6<br> 0.4<br> 0.2<br> 0<br> 0  100  200  300  400  500  600  700  800  900<br>No. of evaluations<br>Sphere 20-D Step 20-D<br>Scaled sphere 20-D Ackley 20-D<br>Average Precision<br>Average Recall<br>Average Precision<br><!-- End of picture text -->

Fig. 18. Precision for mean value pre-screening. 

Fig. 19. Recall for lower bound pre-screening. 

Fig. 20. Precision for lower bound pre-screening. 



<!-- Start of picture text -->
 1<br> 0.8<br> 0.6<br> 0.4<br> 0.2<br> 0<br> 0  100  200  300  400  500  600  700  800  900<br>No. of evaluations<br>Sphere 20-D Step 20-D<br>Scaled sphere 20-D Ackley 20-D<br>Average Recall<br><!-- End of picture text -->

Fig. 21. Recall for PoI pre-screening. 



<!-- Start of picture text -->
 1<br> 0.8<br> 0.6<br> 0.4<br> 0.2<br> 0<br> 0  100  200  300  400  500  600  700  800  900<br>No. of evaluations<br>Sphere 20-D Step 20-D<br>Scaled sphere 20-D Ackley 20-D<br>Precision for PoI pre-screening.<br> 1<br> 0.8<br> 0.6<br> 0.4<br> 0.2<br> 0<br> 0  100  200  300  400  500  600  700  800  900<br>No. of evaluations<br>Sphere 20-D Step 20-D<br>Scaled sphere 20-D Ackley 20-D<br>Recall for ExI pre-screening.<br> 1<br> 0.8<br> 0.6<br> 0.4<br> 0.2<br> 0<br> 0  100  200  300  400  500  600  700  800  900<br>No. of evaluations<br>Sphere 20-D Step 20-D<br>Scaled sphere 20-D Ackley 20-D<br>Average Precision<br>Average Recall<br>Average Precision<br><!-- End of picture text -->

Fig. 22. Precision for PoI pre-screening. 

Fig. 23. Recall for ExI pre-screening. 

Fig. 24. Precision for ExI pre-screening. 

14 



<!-- Start of picture text -->
 25<br> 20<br> 15<br> 10<br> 5<br> 5  10  15  20  25<br>y<br>y predicted<br><!-- End of picture text -->

Fig. 25. y − y plot for a run of the MAES on the 20-dim. Ackley function. 



<!-- Start of picture text -->
 25<br> 20<br> 15<br> 10<br> 5<br> 5  10  15  20  25<br>y<br>y lower bound<br><!-- End of picture text -->

Fig. 26. y − ylb plot for a run of the MAES on the 20-dim. Ackley function. 



<!-- Start of picture text -->
 0<br>-0.1<br>-0.2<br>-0.3<br>-0.4<br>-0.5<br>-0.6<br> 0  200  400  600  800  1000<br>No. of evaluations<br>1p10 5p20 POI LB<br>15p100 Mean EXI<br>Median of best found feasible function values for different<br>multimodal and constrained 10-dim. Keane bump problem<br>-0.1<br>Mean/stdv.<br>-0.2<br>-0.3<br>-0.4<br>-0.5<br>-0.6<br>-0.7<br>1p10 5p20 5p100 MLI LBI PoI ExI<br>Strategy<br>Best found function value (Median)<br>Best function value after 1000 eval.<br><!-- End of picture text -->

Fig. 27. Median of best found feasible function values for different strategies on the multimodal and constrained 10-dim. Keane bump problem (20 runs)). 

Fig. 28. Mean values and standard deviations for best found feasible function values for different strategies on the multimodal and constrained 10-dim. Keane bump problem (20 runs, 1000 objective function evaluations). 

of the Pareto front for these problems depends on the choice of the parameter γ [47]. By setting γ > 1, a convex Pareto front is the solution of the problem. The opposite occurs if γ < 1 where the Pareto front is concave. By setting γ = 1, the Pareto front is linear. 

Results on problems with differently shaped Pareto fronts are displayed in figure 29 (convex Pareto front), figure 30 (linear Pareto front) and figure 31 (concave Pareto front). All experiments have been conducted with an initial step-size of 1. The (20 + 20 < 100)-NSGA-II has been opposed to the (20 + 100)-NSGA-II and the (20 + 20)-NSGA-II. The same variation procedure to that used in the single-objective ES was employed. In the multi-objective case, a larger population size was used, in order capture a greater variety of solutions. 

On the average, pre-screening through the mean value is less successful than taht through the confidence information. The ExI criterion yields the best performance, followed by the lower bound and PoI criteria. In particular, on the concave and linear problems, the ExI criterion leads to significantly better results. However, we note that - unlike the PoI and the lower bound criteria - the performance of the ExI criterion depends on the choice of the reference point, which was set to f<sup>max</sup> = (20, 20)<sup>T</sup> for the given problems. Furthermore, the cost for computing the ExI criterion is significantly higher than that associated with the lower bound and PoI criteria. Hence, the two latter criteria should be considered as efficient pre-screening alternatives. The marginerformance deviation between all metamodel-assisted NSGA-II and the two versions of the standard NSGA-II is significant on all three problems. 

## VI. RAE 2822 AIRFOIL OPTIMIZATION 

The RAE 2822 airfoil was redesigned aiming at optimal performance at three operating points; the corresponding flow conditions are listed in table I. First, the flow around the baseline RAE 2822 airfoil was computed at the aforementioned conditions. The computation resulted to different values for the drag, lift, and pitching moment coefficients. The objective was to minimize the airfoil drag fi = Cd<sup>iateachoperating</sup> point (i = 1, 2, 3), maintain at least the baseline airfoil lift while allowing the pitching moment to vary within a 2 % range. 

### TABLE I 

FLOW CONDITIONS FOR THE RAE 2822 AIRFOIL DESIGN PROBLEM 

||cruise|off-design 1|off-design 2|
|---|---|---|---|
|M|0.734|0.754|0.680|
|Re|6.5·10<sup>6</sup>|6.2·10<sup>6</sup>|5.7·10<sup>6</sup>|
|α|2.8|2.8|1.8|
|transition|3%|3%|11%|









Thus, the aerodynamic constraints for lift Cl<sup>iandpitching</sup> moment Cm<sup>iwereasfollows:</sup> 

- ∀i ∈{1, 2, 3} : Cl<sup>i≥Cl,basewithCl,basebeingthe</sup> lift of the baseline airfoil. 

- ∀i ∈{1, 2, 3} : Cm<sup>iwithin+/-2%ofthepitching</sup> moment Cm,base of the baseline airfoil. 

Furthermore, some geometrical constraints have been de- 

15 



<!-- Start of picture text -->
 1<br> 0.8<br> 0.6<br> 0.4<br> 0.2<br> 0<br> 0  0.2  0.4  0.6  0.8  1<br>f1<br>20p100 MLI PoI<br>20p20 LBI ExI<br>f2<br><!-- End of picture text -->

Fig. 29. Approximation to a convex Pareto front. The 50% attainment surface on the 10-dim. generalized Schaffer problem with γ = 2 is displayed (10 runs, 1000 evaluations). 



<!-- Start of picture text -->
 1<br> 0.8<br> 0.6<br> 0.4<br> 0.2<br> 0<br> 0  0.2  0.4  0.6  0.8  1<br>f1<br>20p100 MLI PoI<br>20p20 LBI ExI<br>f2<br><!-- End of picture text -->

Fig. 30. Approximation to a linear Pareto front. The 50% attainment surface on the 10-dim. generalized Schaffer problem with γ = 1 is displayed (10 runs, 1000 evaluations). 



<!-- Start of picture text -->
 1<br> 0.8<br> 0.6<br> 0.4<br> 0.2<br> 0<br> 0  0.2  0.4  0.6  0.8  1<br>f1<br>20p100 MLI PoI<br>20p20 LBI ExI<br>f2<br><!-- End of picture text -->

Fig. 31. Approximation to a concave Pareto front. The 50% attainment surface on the 10-dim. generalized Schaffer problem with γ = 0.5 is displayed (10 runs, 1000 evaluations). 

- The thickness of the new airfoil at 5% chord length should be greater than or equal to the corresponding thickness of the baseline airfoil. 

- The maximum thickness should be greater than or equal to the maximum thickness of the baseline airfoil. 

- The leading edge radius should be greater than or equal to 90% of the leading edge radius of the baseline airfoil. 

- The trailing edge angle should be greater than or equal to 80% of the trailing edge angle of the baseline airfoil. 

Geometrical processing of any candidate airfoil is possible once the airfoil shape has been generated and prior to solving 

the computationally expensive flow equations. This is why the geometrical constraints are treated differently from the aerodynamic ones, which should be taken into account only after solving the flow problem. All candidate aifoil shapes undergo a preliminary geometrical check. During mutation, many mutated offspring are created and tested unless the necessary number of feasible offspring (according to the geometrical constraints) is obtained or the number of samplings exceeds 1000. The latter was incorporated in both strategies - the M-NSGA-II and standard NSGA-II - in order to get higher percentages of feasible individuals for exact evaluation. 

The airfoil parameterization was based on Bezier polynomials, with the ordinates of control points acting as the design variables. Each airfoil side was parameterized using five Bezier control points; this resulted to six degrees of freedom, in total, since the first and last control point on either side was fixed. All other aspects and parameters concerning mesh generation, flow solution, models in use etc. are kept constant during this study. 

A comparison between the NSGA-II and the metamodelassisted NSGA-II on the RAE problem is displayed in figure 33 (f1 vs. f2), figure 34 (f1 vs. f3), and figure 35 (f2 vs. f3). In all three cases, attainment surfaces have been plotted for the (20 + 20)-NSGA-II (NSGA) and the (20 + 4 < 20-NSGA-II (M-NSGA) (for a detailed plot of all runs we refer to [45]). In particular, the best Pareto front (BEST) consists of the nondominated set from the union of all points over all five runs. The median attainment surface (AVG:average) consists of all non-dominated points that are weakly dominated by at least two of the other Pareto fronts obtained with the same strategy. A number of 1000 evaluations of the objective function were carried out for each of the runs. 

The plots demonstrate the gain in solution quality achieved using the new techniques, with almost the same CPU cost. Through the use of metamodels, the diversity and precision of the computed optimal set was improved. The results show additional improvement if the confidence interval was used. The latter was used by the optimization method to detect and re-sample insufficiently explored regions of the search space. 

Considering constrained optimization, the metamodel assistance made it possible to achieve a significantly higher ratio of feasible solutions in all five cases of the RAE 2822 problem (figure 32). Furthermore, it was possible to find an improvement for the baseline design of the RAE 2822 test case. 

## VII. CONCLUSIONS 

The use of metamodels within evolutionary algorithm based optimization methods is beneficial whenever dealing with computationally expensive function evaluations. Data collected for all previously evaluated points can be used during the evolution to build metamodels and, through them, screen out the less promising generation members. By doing so, expensive evaluations of the most promising population members are necessary and the economy in computational cost is considerable. For multimodal problems and in multi-objective optimization it is strongly recommended to use the confidence 

16 



<!-- Start of picture text -->
1000<br>NSGA−II<br>MNSGA−II (Mean)<br>900 MNSGA−II (LB)<br>800<br>700<br>600<br>500<br>400<br>300<br>200<br>100<br>0<br>1 2 3 4 5<br>RUN<br>NO. OF FEASIBLE SOLUTIONS<br><!-- End of picture text -->

Fig. 32. Number of feasible solutions for 5 runs on the RAE test case. 



<!-- Start of picture text -->
Attainment surfaces f1 vs. f2<br> 0.0295<br>NSGA-BEST<br> 0.0294 NSGA-AVG<br>M-NSGA-BEST<br> 0.0293 Baseline DesignM-NSGA-AVG<br> 0.0292<br> 0.0291<br> 0.029<br> 0.0289<br> 0.0288<br> 0.0287<br> 0.0286<br> 0.0285<br> 0.0216  0.0218  0.022  0.0222  0.0224  0.0226  0.0228<br>f1<br>f2<br><!-- End of picture text -->

Fig. 33. Feasible RAE 2822-results with NSGA: f1 vs. f2 

information provided by a Gaussian Random Field Metamodel (GRFM) in order to boost evaluations towards less explored regions. The use of GRFM may prevent premature convergence without being misled by poor predictions. In particular, in multi-objective optimization, the integration of the confidence information into the metamodel helps to increasing the coverage of the Pareto optimal set. In this paper, this was demonstrated on mathematical test problems as well as on a design problem in aerodynamics. 

This paper focused on the understanding of the behavior of various pre-screening criteria. Despite the high number of test problems analyzed in this paper, there are still open questions. However, one of the most important conclusions is that, according to the results presented in the paper, there is an interesting trade-off between _recall_ and _precision_ measured during the pre-screening. It seems that the “adaptation” of the number of pre-selected individuals plays an important role for the performance of the algorithms. The same results indicate that measuring _recall_ and _precision_ may not suffice to explain the good performance of the lower bound pre-screening in case of multimodal and flat functions. It seems, that the lower bound pre-screening guides the search towards unexplored regions of the search space, which are not likely to be visited by standard EA. Another lesson learned from these studies is that MAES utilizing mean value pre-screening perform badly in the presence of discontinuities and plateaus. The use of the confidence measure improves the results significantly. 

## APPENDIX 

_A. Sphere problem_ 



<!-- Start of picture text -->
Attainment surfaces f1 vs. f3<br> 0.01168<br>NSGA-BEST<br>NSGA-AVG<br> 0.01167 M-NSGA-BEST<br>M-NSGA-AVG<br>Baseline Design<br> 0.01166<br> 0.01165<br> 0.01164<br> 0.01163<br> 0.01162<br> 0.01161<br> 0.0216  0.0218  0.022  0.0222  0.0224  0.0226  0.0228<br>f1<br>f3<br><!-- End of picture text -->

Fig. 34. Feasible RAE 2822-results with NSGA: f1 vs. f3 



<!-- Start of picture text -->
Attainment surfaces f2 vs. f3<br> 0.01168<br>NSGA-BEST<br>NSGA-AVG<br> 0.01167 M-NSGA-BEST<br>M-NSGA-AVG<br>Baseline Design<br> 0.01166<br> 0.01165<br> 0.01164<br> 0.01163<br> 0.01162<br> 0.01161<br> 0.0285 0.0286 0.0287 0.0288 0.0289 0.029 0.0291 0.0292 0.0293 0.0294 0.0295<br>f2<br>f3<br><!-- End of picture text -->

Fig. 35. Feasible RAE 2822-results with NSGA: f2 vs. f3. 





Known minimum: x<sup>∗</sup> = 0, f (x<sup>∗</sup> ) = 0 

_B. Ellipsoid problem_ 





Known minimum: x<sup>∗</sup> = 0, f (x<sup>∗</sup> ) = 0 

_C. Step problem_ 



Known minimum: x<sup>∗</sup> = 0, f (x<sup>∗</sup> ) = 0 

17 

_D. Ackley’s problem_ 





Known minimum: x<sup>∗</sup> = 0, f (x<sup>∗</sup> ) = 0 

_E. Keane’s bump problem_ 



Minimum is unknown 

_F. Generalized Schaffer problem_ 







The curvature of the Pareto front is scalable by means of the parameter γ. The equation describing the Pareto front reads 



Thus, γ = 1 results in a linear Pareto front, γ < 1 in concave Pareto fronts, and γ > 1 in convex Pareto fronts. The Pareto fronts are axis-symmetric to the bi-sector. The extremal points of this function are given by (y1, y2)<sup>T</sup> = (0, 1)<sup>T</sup> and (y1, y2)<sup>T</sup> = (1, 0)<sup>T</sup> . A detailed analysis of this function was provided by Emmerich [47]. 

## REFERENCES 

- [1] Y. Jin and J. Branke, “Evolutionary optimization in uncertain environments - a survey.” _IEEE Transactions on Evolutionary Computation_ , vol. 9, no. 3, 2005, in print. 

- [2] J. M. Barthelemy and R. T. Haftka, “Recent advances in approximation concepts for optimum structural design,” NASA Langley Research Center, Hampton, VA, Tech. Rep. Tech. Report 104032, 1991. 

- [3] D. B¨uche, N. N. Schraudolph, and P. Koumoutsakos, “Accelerating evolutionary algorithms with gaussian process fitness function models,” _IEEE Transactions on Systems, Man and Cybernetics, Special Issue on Knowledge Extraction and Incorporation in Evolutionary Computation (Part C)_ , 2005, in print. 

- [4] J. E. Dennis and V. Torczon, “Managing approximation models in optimisation,” in _Multidisciplinary Design Optimisation: State-of-theart_ , N. M. Alexandrov and N. Hussaini, Eds. Philadelphia: SIAM, 1997, pp. 330–347. 

- [5] A. P. Giotis and K. Giannakoglou, “Single- and multi-objective airfoil design using genetic algorithms and artificial intelligence,” in _EUROGEN 99, Evolutionary Algorithms in Engineering and Computer Science_ , 1999. 

- [6] K. C. Giannakoglou, “Design of optimal aerodynamic shapes using stochastic optimization methods and computational intelligence,” _International Review Journal Progress in Aerospace Sciences_ , vol. 38, pp. 43–76, 2001. 

- [7] Y. Jin, “A comprehensive computation,” _Soft Computing Journal_ , vol. 9, no. 1, pp. 3–12, 2005. 

- [8] K. Giannakoglou, “Designing turbomachinery blades using evolutionary methods,” in _ASME Paper 99-GT-181, 44th ASME Gas Turbine and Aeroengine Congress_ , Indianapolis, IN, USA, 1999. 

- [9] H. Ulmer, F. Streichert, and A. Zell, “Evolution strategies assisted by gaussian processes with improved pre-selection criterion,” in _IEEE Congress on Evolutionary Computation,CEC 2003, Canberra, Australia, Dec. 8.-12, 2003_ . IEEE-Press, 2003, pp. 692–699. 

- [10] S. Yesilyurt and A. T. Patera, “Surrogates for numerical simulations; optimization of eddy–promoter heat exchangers,” NASA Langley Research Center, Institute for Computer Applications in Science and Engineering, Hampton, VA, Tech. Rep. Tech. Report 93-50, 1993. 

- [11] Y. Jin, M. Olhofer, and B. Sendhoff, “Managing Approximation Models in Evolutionary Aerodynamic Design Optimisation,” in _CEC 2001 Int’l Conference on Evolutionary Computation, Las Vegas_ , vol. 1. Piscataway NJ: IEEE Press, 2001, pp. 592–599. 

- [12] K. Giannakoglou, A. Giotis, and M. Karakasis, “Low-cost genetic optimization based on inexact pre-evaluations and the sensitivity analysis of design parameters,” _Inverse Problems in Engineering_ , no. 9, pp. 389– 412, 2001. 

- [13] M. El-Beltagy, P. Nair, and A. Keane, “Metamodelling Techniques for Evolutionary Optimisation of Computationally Expensive Problems: Promises and Limitations,” in _Proc. of GECCO, Int’l Conf. on Genetic and Evolutionary Computation, Orlando 1999_ , W. Banzhaf, J. Daida, A. Eiben, M. Garzon, V. Honavar, M. Jakiela, and R. Smith, Eds. Morgan Kaufman, 1999, pp. 196–203. 

- [14] A. Ratle, “Accelerating the convergence of evolutionary algorithms by fitness landscape approximations,” in _Parallel Problem Solving by Nature_ , ser. LNCS, A. Eiben, T. B¨ack, M. Sch¨onauer, and H.-P. Schwefel, Eds., vol. V. Berlin: Springer-Verlag, 1998, pp. 87–96. 

- [15] M. Emmerich and J. Jakumeit, “Metamodel-assisted optimisation with constraints: A case study in material process design,” in _Int’l Conference EUROGEN 2003_ . Barcelona: CIMNE, 2003. 

- [16] A. P. Giotis, K. C. Giannakoglou, and J. P´eriaux, “A Reduced-Cost Multi-Objective Optimization Method based on the Pareto Front Technique, Neural Networks, and PVM,” in _Proc. European Congress on Computational Methods in Applied Sciences and Engineering (ECCOMAS’00),_ (CD-ROM). Barcelona: Center for Numerical Methods in Engineering (CIMNE), 2000. 

- [17] K. Giannakoglou and M. K. Karakakis, “On the use of surrogate evaluation models in multi-objective evolutionary algorithms,” in _ECCOMAS_ , 2004. 

- [18] P. K. Nain and K. Deb, “Computationally effective search and optimization procedure using coarse to fine approximations,” in _Proc. of the Congress on Evolutionary Computation CEC 2003, Canberra, Australia_ , 2003, pp. 2081–2088. 

- [19] M. Emmerich, A. Giotis, M. Ozdemir,<sup>¨</sup> T. B¨ack, and K. Giannakoglou, “Metamodel-assisted evolution strategies,” in _Parallel Problem Solving from Nature VII, Proc. Int’l Conf., Granada 2002, LNCS2439_ , J. J. M. Guerv´os, P. Adamidis, H.-G. Beyer, J. L. F.-V. Mart´ın, and H.-P. Schwefel, Eds. Berlin: Springer, 2002, pp. 361–370. 

- [20] D. G. Krige, “A study of gold and uranium distribution patterns in the Klerksdorp gold field,” _Geoexploration_ , vol. 4, no. 1, pp. 43–53, 1966. 

- [21] T. J. Santers, N. J. Williams, and W. I. Notz, _The Design and Analysis of Computer Experiments_ . Berlin: Springer, 2003. 

- [22] D. J. C. MacKay, “Introduction to gaussian processes,” in _Neural Networks and Machine Learning_ , ser. NATO Advanced Study Institute, C. M. Bishop, Ed. Berlin: Springer, 1998, vol. 168, pp. 133–165. 

- [23] R. Adler, _The Geometry of Random Fields_ . NY: Wiley, 1981. 

- [24] W. H. Flannery, S. A. S. A. Teukolsky, and W. T. Vetterling, _Numerical Recipes in FORTRAN: The Art of Scientific Computing_ . Cambridge University Press, 1992, ch. ”Interpolation and Extrapolation.” Ch. 3. 

- [25] D. E. Myers, “Kriging, cokriging, radial basis functions and the role of positive definiteness,” _Computers Mathematics Applications_ , vol. 24, no. 12, pp. 139–148, 1992. 

- [26] C. Zuppa, “Error estimates for modified local shepard’s interpolation formula,” _Applied Numerical Mathematics archive_ , vol. 49, no. 2, pp. 245–259, 2004. 

- [27] A. Padula, “Interpolation and pseudorandom function generators,” University, Dept. of Computational and Applied Mathematics, Rice University, Houston, TX, Senior Honors Thesis, 2000. 

18 

- [28] J. Sacks, W. J. Welch, T. J. Mitchell, and H. P. Wynn, “Design and analysis of computer experiments,” _Statistical Science_ , vol. 4, no. 4, pp. 409–435, 1989. 

- [29] J. R. Koehler and A. B. Owen, _Handbook on Statistics_ . ElsevierScience, 1996, vol. 13, ch. Computer Experiments, pp. 239–245. 

- [30] M. Schonlau, W. Welch, and D. Jones, “Global versus local search in constrained optimization of computer models,” in _New Developments and Applications in Experimental Design_ , N. Flournoy, W. Rosenberger, and W. Wong, Eds. Hayward, California: Institute of Mathematical Statistics, 1998, vol. 34, pp. 11–25. 

- [31] M. Schonlau, “Efficient global optimization of expensive black-box functions,” _Journal of Global Optimization_ , vol. 13, no. 4, pp. 433–492, 1998. 

- [32] Y. Ong, P. Nair, and A. Keane, “Evolutionary optimization of computationally expensive problems via surrogate modeling,” _AIAA Journal_ , vol. 41, no. 4, pp. 687–696, 2003. 

- [33] T. B¨ack, D. B. Fogel, and Z. Michalewicz, Eds., _Handbook of Evolutionary Computation_ . Bristol, UK: IoP Press, 1997. 

- [34] H.-G. Beyer and H.-P. Schwefel, “Evolution strategies - A comprehensive introduction,” _Natural Computing_ , vol. 1, no. 1, pp. 3–52, 2002. 

- [35] H.-P.Schwefel, _Evolution and Optimum Seeking_ . Wiley, N.Y., 1995. 

- [36] H.-G. Beyer, _The Theory of Evolution Strategies_ , 1st ed., ser. Natural Computing Series. Berlin, Heidelberg: Springer-Verlag, 2001. 

- [37] F. Hoffmeister and J. Sprave, “Problem independent handling of constraints by use of metric penalty functions,” in _Evolutionary Programming V - Proc. Fifth Annual Conf. Evolutionary Programming (EP’96)_ , L. J. Fogel, P. J. Angeline, and T. Bck, Eds. The MIT Press, 1996, pp. 289–294. 

- [38] K. Deb, A. Pratap, S. Agarwal, and T. Meyarivan, “A fast and elitist multi-objective genetic algorithm NSGA-II,” KanGAL, Kanpur, India, Tech. Rep. 2000001, 2000. 

- [39] K. Deb, _Multi-Objective Optimization using Evolutionary Algorithms_ . NY: Wiley, 2001. 

- [40] E. Zitzler, “Evolutionary algorithms for multiobjective optimization,” Ph.D. dissertation, ETH Zurich, Switzerland, 1998. 

- [41] D. D. Cox and S. John, “SDO: a statistical method for global optimization,” in _Multidisciplinary design optimization (Hampton, VA, 1995)_ . Philadelphia, PA: SIAM, 1997, pp. 315–329. [Online]. Available: citeseer.ist.psu.edu/cox97sdo.html 

- [42] M. Trosset and V. Torczon, “Numerical optimization using computer experiments,” Institute for Computer Applications in Science and Engineering ICASE TR 9738, NASA Langley Research Center, Hampton Virginia, Tech. Rep., 1997. 

- [43] V. Torczon and M. W. Trosset, “Direct search methods: Then and now,” ICASE, Hampton, VA, Tech. Rep. NASA/CR-2000-210125, ICASE Report No. 2000-26, 2000. 

- [44] M. Fleischer, “The measure of Pareto optima: Applications in multiobjective metaheuristics,” in _Evolutionary Multiobjective Optimisation, Second Int’l Conference, EMO 2003_ , C. M. F. et al., Ed., 2003, pp. 519–533. 

- [45] M. Emmerich and B. Naujoks, “Metamodel-assisted multiobjective optimisation strategies and their application in airfoil design.” in _Fifth International Conf. on Adaptive Design and Manufacture (ACDM 04)_ , I. Parmee, Ed. Berlin: Springer, 2004, pp. 249–260. 

- [46] S. Weinzierl, “Introduction to monte carlo methods,” NIKHEF, Theory Group, Amsterdam, Technical Report NIKHEF-00-012, 2000. 

- [47] M. Emmerich, “A rigorous analysis of two bi-criteria problem families with scalable curvature of the pareto fronts,” Leiden Institute on Advanced Computer Science, Leiden, NL, Technical Report LIACS TR 2005-05, May 2005. 

**Acknowledgements:** This work was supported by the Deutsche Forschungsgemeinschaft (DFG) as part of the _Collaborative Research Center_ ’Computational Intelligence’ (SFB 531). Also, the support from bilateral Personnel Exchange Programme between Greece and Germany (IKYDA 2000) is acknowledged. 




---

## ANEXO — Camada de texto completa do PDF (get_text)

> Reprodução integral da camada de texto do PDF (todas as páginas, ordem de leitura bruta). Inclui tabelas de resultados e equações que a conversão estruturada acima pode ter omitido. Garante completude textual (imagens continuam omitidas).


<!-- página 1 -->

1
Single- and Multi-objective Evolutionary
Optimization Assisted by Gaussian Random Field
Metamodels
Michael Emmerich, Kyriakos Giannakoglou, Boris Naujoks
Abstract— This paper presents and analyzes in detail an
efﬁcient search method based on Evolutionary Algorithms (EA)
assisted by local Gaussian Random Field Metamodels (GRFM).
It is created for the use in optimization problems with compu-
tationally expensive evaluation function(s). The role of GRFM is
to predict objective function values for new candidate solutions
by exploiting information recorded during previous evaluations.
Moreover, GRFM are able to provide estimates of the conﬁdence
of their predictions.
Predictions and their conﬁdence intervals predicted by GRFM
are used by the Metamodel Assisted EA (MAEA). It selects
the promising members in each generation and carries out
exact, costly evaluations only for them. The extensive use of
the uncertainty information of predictions for screening the
candidate solutions makes it possible to signiﬁcantly reduce the
computational cost of single- and multi-objective EA. This is
adequately demonstrated below by means of mathematical test
cases and a multi–point airfoil design in aerodynamics.
Index Terms— Evolutionary Optimization, Metamodeling, Un-
certainty Prediction, Kriging, Gaussian Random Field Models,
Multi-objective Design Optimization
I. INTRODUCTION
Optimization problems, with ng (ng ≥0) inequality con-
straints gi can be cast in the form of minimization problems
with nf (nf ≥1) objective functions fi:
min f1(x), . . . , min fnf (x)
(1)
g1(x) ≤0, . . . , gng(x) ≤0
(2)
x ∈S ⊂Rd
(3)
The search space S is deﬁned as S := [xmin, xmax], where
xmin and xmax are user-deﬁned lower and upper bounds
for the design variables. Single-objective optimization (nf =
1, ng = 0) is an important special case of the problem
formulation. Multi-objective optimization problems are either
constrained (ng > 0) and/or multi-objective (nf > 1) ones,
though multi-objective, constrained problems (nf > 1, ng >
0) often occur. In the multi-objective case, it is a common
M. Emmerich is Assistant Professor at the Leiden Center of Advanced
Computer Science (LIACS), University of Leiden, Niels-Bohr-Weg 1, CA-
3335 Leiden, The Netherlands, emmerich@liacs.nl
K. Giannakoglou is Associate Professor in the School of Mechanical
Engineering of the National Technical University of Athens, Lab. Of Thermal
Turbomachines, Athens, Greece, kgianna@central.ntua.gr
B.
Naujoks
is
with
the
Chair
for
Systems
Analysis,
Computer
Science
Dept.,
University
of
Dortmund,
44221
Dortmund,
Germany,
boris.naujoks@uni-dortmund.de
strategy to search for an approximation to the Pareto optimal
set instead of a single optimal solution.
Often, it is not possible to evaluate the objective function
precisely. Noise due to physical experimentation is a typical
example of a source of uncertainty. On the other hand, if
deterministic computer models are used, uncertainties related
to the evaluation might occur. In this paper, we focus on
uncertainties that arise, whenever – for the purpose of cost
reduction – imprecise fast evaluations replace the precise ones.
For a general survey on the treatment of uncertainties in EA
the reader should refer to [1].
This paper is concerned with optimization problems in
which the evaluation of candidate solutions require time-
consuming simulation software (such as Computational Fluid
Dynamics, CFD, tools for applications in ﬂuid mechanics
and aerodynamics, Finite Element, FEM, tools for structural
analysis, etc). The high CPU cost of a single evaluation makes
search methods, which are capable of locating global optima
through the minimum number of evaluations, attractive. Note
that, in most real–world problems, the functional relation
between input variables and responses is very complex.
EA are well-established techniques for multivariate opti-
mization with highly-nonlinear solution spaces. They can be
adapted to different computing environments and problem spe-
ciﬁc knowledge can be integrated into their search operators.
The concept of population-based search allows their use for
global optimization.
However, standard EA need a large number of ﬁtness func-
tion evaluations in order to reach a global or local optimum
with adequate precision. EA using computationally expensive
evaluations may reduce their CPU cost through metamodeling
[2], [3], [4], [5], [6], [7], [8], [9], [10]. Metamodels should
be understood as surrogate evaluation models that are built
using existing information. The cost of training a metamodel
depends on its type and the training set size. Compared to
the cost of an exact evaluation, that of training and using the
metamodel is relatively low.
Nowadays, in EA artiﬁcial neural networks (ANN) are
frequently employed to screen candidate solutions. Multilayer
perceptrons [11] or exactly interpolating radial basis function
(RBF) networks [6] can be used, either in their standard forms
or by incorporating add-on features such as measures for the
relative importance of input variables (cf. Giannakoglou [6],
[12]). Kriging models (or Gaussian Random Field models
(GRFM), [3], [13], [14], [9]) are in use, too. An overview on
metamodeling approaches in Evolutionary Computation can be


<!-- página 2 -->

2
found in [7]. Recent publications show, that metamodels are
beneﬁcial to speed up the evolutionary search in constrained
and multi-objective optimization [15], [16], [17], [18], though
there are still open questions.
Recently, screening methods also consider the conﬁdence of
the predicted output have been suggested [3], [9], [13], [19].
This information can be obtained through Gaussian Random
Field models which predict the unknown evaluation result by
means of a Gaussian distribution. The use of conﬁdence in-
formation increases the prediction accuracy of the metamodel
and helps guiding the search towards less explored regions in
the search space. This also prevents premature convergence.
In this paper, the term pre-screening will denote the use of
metamodels for the selection of promising members which are
not evaluated so far. Criteria that can be used to support pre-
screening procedures by incorporating conﬁdence information
are introduced; their concept is discussed and statistical studies
of their performance are presented. These criteria ﬁgure out
improvements in a set of new (offspring) solutions, assuming
that the unknown response is described by a Gaussian distri-
bution.
In order to extend the application domain of the proposed
methods, pre-screening criteria used in single-objective prob-
lems will be generalized to constrained and multi-objective
problems. After scrutinizing a number of mathematical opti-
mization problems, a challenging aerodynamic design problem
with 3 objectives and 6 constraints will be solved. The results
presented below indicate that it is very beneﬁcial to consider
the conﬁdence information within a MAEA, in order to
improve its robustness.
The structure of this paper is as follows: In section II,
GRFM are presented and discussed. In section III, the single-
and multi-objective EA used are presented. In section IV,
the integration of GRFM in single- and multi-objective EA
is outlined. Finally, using a number of academic test cases
(section V) and a real-world test problem (section VI), the
efﬁciency of the proposed MAEA is investigated.
II. GAUSSIAN RANDOM FIELD METAMODELS
The Gaussian Random Field (GRF) theory constitutes a
powerful framework for building metamodels based on data
obtained through computer experiments. Gaussian Random
Field Models (GRFM) will be deﬁned below, by ﬁrst putting
emphasis to the information required by the model as well
as its responses after training. Later, statistical assumptions,
limitations and practicalities related to the model itself and its
use will be discussed.
In the literature, GRFM are also known under different
names, such as Kriging, Gaussian processes and Gaussian
random functions methods. The term Kriging points directly
to the origin of these prediction methods dating back to the
sixties, when the mining engineer Krige used GRFM-like
models to predict the concentration of ore in gold- and uranium
mines [20]. Today, Kriging includes a wide class of spatial
prediction methods which do not necessarily assume Gaussian
ﬁelds.
Note that the latter assumption is essential in our algorithms
and the term GRFM is used herein in the standard (strict)
                                          



































































































































































































































































































	
								
	
								
	
								
	
								
	
								
	
								
	
								
	
								
	
								
	
								
	
								
	
								
	
								
	
								
	
								
	
								
	
								
	
								
	
								
	
	
	
	
	
	
	
	
	




























































































































































































































































































x
x
x
(1)
(2)
(3)
y
y
(1)
(3)
(2)
^
y
Confidence Range
^
y
y(x’)
’
y(x’)+s(x’)
x’
^
^
y(x’)−s(x’)
^
x
Predicted 
Function
Fig. 1.
Outputs of Gaussian Random Field Metamodels using a R →R
mapping example.
sense. On the other hand, the term Gaussian random functions
[21] might be misleading, because a random function is often
associated with a single random variable instead of a set
of them. However, in the present paper, the term Gaussian
Random Field seems to be more appropriate than Gaussian
Process [22] since this paper is dealing with a multidimen-
sional – spatial – rather than a one-dimensional – temporal –
input space [23].
Apart from the predicted objective function value, another
information provided by a GRFM is a measure of conﬁdence
for its prediction. It is reasonable that the conﬁdence is
expected to be higher if the training point density in the
neighborhood of a newly proposed point is higher. Another
important output of the metamodel is the variance of the output
values and the average correlation between responses at neigh-
boring points. A GRFM interpolates data values and estimates
their prediction accuracy. It provides the mean value and the
standard deviation for a one-dimensional Gaussian distribution
which represents the likelihood for different realizations of
outcomes to represent a precise function evaluation. Figure 1
illustrates the use of GRFM in an example mapping R →R.
The user of modern optimization methods desires to operate
the metamodel in the most efﬁcient manner, i.e. to maximize
its prediction capabilities and minimize the CPU cost for
its training. For this purpose, a better understanding of the
statistical assumptions, limitations and practicalities related to
the model itself and its use are needed.
Let y : Rd →R be the output of a computationally
expensive computer experiment and X = {x(1), . . . , x(m)}
be a set of m input conﬁgurations which are available along
with the corresponding responses y(1) = y(x(1)), y(2) =
y(x(2)), . . . , y(m) = y(x(m)). No assumption on the regularity
of the distribution of x(1), . . . , x(m) in S is made.
In GRF theory, the aim is to build a non-time-consuming
tool capable of predicting the output corresponding to a new
point x′ ∈S, according to an approximated Rd →R mapping.
With x′ ∈X, the precise objective function value is returned.
This corresponds to the well known exact interpolation prob-
lem for which a large variety of methods, ranging from splines
[24] to radial basis networks [25] and Shepard polynomials
[26], are available.
The basic assumption in modeling with GRFM is that the
output function is a realization (sample-path) of a Gaussian


<!-- página 3 -->

3
Weakly correlated landscape
 0
 2
 4
 6
 8
 10
x1
 0
 2
 4
 6
 8
 10
x2
-500
-400
-300
-200
-100
 0
 100
 200
 300
 400
 500
Realization F(x)
Fig. 2.
Sample path of a 2-dim. GRF with low correlation approximated
through Krigiﬁer [27].
Strongly correlated landscape
 0
 0.2
 0.4
 0.6
 0.8
 1
x1
 0
 0.2
 0.4
 0.6
 0.8
 1
x2
-300
-200
-100
 0
 100
 200
 300
 400
Realization F(x)
Fig. 3.
Sample path of a 2-dim. GRF with high correlation approximated
through Krigiﬁer [27].
random ﬁeld F. The latter is a mapping that assigns a 1-
dim. Gaussian distributed random variable F(x) with constant
mean β := E(F) and variance s2 = Var(F) to each point x
of an input space S (which is typically Rd). Two examples of
GRF sample paths are given in Figure 2 and 3. In contrast to
other modeling techniques such as linear regression, a spatial
correlation between the output values is assumed. For two
arbitrary inputs x and x′, this is expressed by a correlation
function with
c(F(x), F(x′)) ≡c(x, x′).
(4)
Typically the correlation function is assumed to be station-
ary, i. e.
c(F(x), F(x′)) ≡c(x −x′)
(5)
or isotropic
c(F(x), F(x′)) ≡c(d(x, x′)).
(6)
where d(x, x′) is the relative distance between inputs.
In the design and analysis of computer experiments liter-
ature [28], the isotropic Gaussian kernel and the Gaussian
product kernel are often used. The latter reads:
c(θ1, . . . , θd) =
d
Y
i=1
exp(θi|xi −x′
i|2)
(7)
where θi, i = 1, . . . , d denote correlation parameters. For the
related isotropic Gaussian kernel, the assumption θi = θ =
const., i = 1, . . . d is made.
The θ-parameter(s) as well as β and s2 are invariant with
respect to F. Their values can be estimated through a sample
by generalized least square methods; θ can be estimated by
maximum likelihood hypothesis, by minimizing
PDF(F(X) = y)
=
(8)
1
(2π)n/2(ˆs2)n/2p
det(C)
exp
"
−(y −1ˆβ)T C−1(y −1ˆβ)
2ˆs2
#
with
C =


cθ(x1, x1)
· · ·
cθ(x1, xm)
...
...
...
cθ(xm, x1)
· · ·
cθ(xm, xm)

, 1 =


1
...
1

(9)
using the following generalized least square estimates [29] of
β and s2
ˆβ = 1T C−1y
1T C−11
(10)
ˆs2 = (y −1ˆβ)T C−1(y −1ˆβ)
m
.
(11)
The algorithm estimates the parameters iteratively in a
multivariate maximization of PDF(F(X) = y) with variable
θ. The cost of the maximization depends on the number of
variables in θ. Generally, it is not always possible to solve
this optimization problem in closed form due to nonlinearities.
Quasi–Newton methods can be employed for its solution.
Partial derivatives of the likelihood formula are given in [29].
However, since the problem is multimodal (cf. Mac Kay
[22]), it cannot be guaranteed that its precise solution can
be obtained with gradient based methods. Thus, direct search
methods like multidimensional pattern search algorithm [4]
or evolution strategies [9] have been employed to improve
numerical robustness.
In order to solve the maximum likelihood problem, typi-
cally, a simpliﬁed mathematical problem is cast and solved,
which has the same optimum with PDF(F(X) = y), namely
m log ˆs2(θ) + log det C(θ) →min .
(12)
The expression is derived as follows: By substituting ˆs2
(equation 11) in the exponential term of equation 8 we get:
1
2πm/2 + (ˆs2)m/2 det C(θ)1/2 exp(m/2) →max .
(13)
Expressed as the minimization of the denominator, it yields
2πm/2 · (ˆs2)m/2 · det C(θ)1/2 · exp(−m/2) →min .
(14)
Finally, through logarithmic calculus and elimination of con-
stant values, equation 12 is obtained.
An alternative is to calculate these parameters by means
of cross validation [21], [30]. For practical optimization, it


<!-- página 4 -->

4
is suggested to use leave-one-out cross validation (LC) [21]
for adapting θ. Furthermore, it is suggested to use the median
deviation instead of the average deviation to the known outputs
in order to increase robustness at outliers.
Having estimated these values for the set of inputs, we
can derive the conditional distribution of F at x′, denoted
by F(x′|X, y), given the information X, y. The prediction
of a new output vector is now ˆy(x) = E(F(x′|X, y)) with
the corresponding variance s2(x) := Var(F(x′|X, y)). This
yields
ˆy(x) = β + (y −1β)T C−1c(x),
(15)
with
c = [cθ(x, x1), . . . , cθ(x, xm)]T ,
(16)
which can be rewritten as a linear predictor
β +
m
X
i=1
λ(i)c(x, xi)
(17)
with
[λ(1), . . . , λ(m)] = (y −1β)C−1.
(18)
Assuming that the value of β is known, the local variance
s2(x) = Var(F(x′)|X, y) for this random variable is given by
s2(x) = s2 · (1 −c(x)T C−1c(x))
(19)
However, if the maximum likelihood estimate ˆβ is used in-
stead of β, Schonlau [31] suggests to use the more pessimistic
expression ˆs2(x) deﬁned as
ˆs2(x) =
(20)
s2

1 −c(x)T C−1c(x) + (1 −1T C−1c(x))2
1T C−11

.
rather than s2(x).
The derivation of these equations can be found in Sacks et
al. [28]. Schonlau et al. [29] interprets the term cT C−1c(x) as
the reduction in prediction error due to being correlated with
the sampled points. The term (1 −1C−1c(x))2/(1TC−11) is
added, if the exact value of β is unknown and is estimated only
from the sample. For a known β value, a simpliﬁed expression
results.
Note that the time complexity for the training of the meta-
model is O(Nm3d+m2d), where N ≥1 denotes the number
of iterations spent for adjusting the metamodel parameters θ, µ
and s2 and d is the dimension of the search space. Once the
metamodel has been trained, each prediction requires O(nm2)
elementary operations (if ˆs(x) is to be computed) or O(nm)
(if ˆy(x) is to be computed).
The number of training points is the main factor that
determines the training cost. Thus, it is recommended to use
only the minimum necessary subset of the total number of
samples available in the database, for the metamodel training.
A well performing heuristic is to use a small number of Nr
points which are closest1 to each new point x′ and train a
1with regard to the euclidian metric
new, locally valid metamodel. Such a strategy would be called
local metamodeling in contrast to global metamodeling, for
which all evaluated points in the search space are used to
build the model. Local metamodels have been proposed in [5]
and, later, adapted by other authors, [3], [32]. For a systematic
study of the number of neighbors we refer to [3]. The authors
suggest to use ≥2d neighboring points for the purpose of
local metamodeling. In this paper, Nr = 2d is chosen in order
to keep the computational effort low.
III. EVOLUTIONARY ALGORITHMS
EA originated as models of biological adaptation processes
in the early 60ties for the purpose of parameter optimization
[33]. Among the existing variants of EA, only a few have
undergone a thorough theoretical investigation. Among them
are Evolution Strategies (ES) [34], [35], often used in real-
valued function optimization. Their convergence behavior has
been studied on a large number of theoretical [36] and real-
world test cases. The (µ+λ)-EA that will be described below
bears many of the well known features of ES. However, for
the purpose of the present paper, the (µ + λ) scheme is not
restrictive by any means and any other EA could be used
instead.
With µ parents and λ offspring, the (µ + λ)-EA works as
follows:
Algorithm 1 (µ + λ)-EA
t ←0
Pt ←init()
/* Pt ∈Sµ: Set of solutions */
evaluate(Pt)
while t < tmax do
Gt ←generate(Pt)
/* Generate λ variations */
evaluate(Gt)
Pt+1 ←select(Gt ∪Pt)
/* Rank and select µ best */
t ←t + 1
end while
The(µ+λ)-EA starts with initializing the generation counter
t (algorithm 1). After generating the initial population with
µ individuals by uniform random sampling in S, the EA
generates λ new solutions in S through recombination and
mutation [33]. The new candidate solutions are evaluated and
ranked in terms of their quality. The µ best solutions in Gt∪Pt
are selected to form the new parent population Pt+1.
In this paper, individuals consist of a real-valued vector
x ∈Rd and a single step-size σ ∈R+. The variation
procedure (generate) used in the present study is described
in algorithm 2. For details on variation procedures used in
ES the reader should refer to Beyer [36]. ES works with a
robust and fast mutative self-adaptation of a single step size
and γ = 1.3 (algorithm 2). This kind of mutation has been
recommended by Beyer for the starting phase of an EA [36].
Here, N(0, 1) denotes a Gaussian distributed random number
and ’or’ symbolizes a uniform random choice.
The (µ+λ)-EA for single-objective, constrained, and multi-
objective optimization differ in the ranking of solutions during
the select procedure.


<!-- página 5 -->

5
Algorithm 2 Generation of a new individual (x′′, σ′′) from
Pt in the simple (µ + λ)-ES
draw x(1), σ(1) and x(2), σ(2) randomly out of Pt
for all i ∈{1, . . . , d} do
x′
i ←x(1)
i
or x(2)
i
end for
σ′ ←(σ(1) + σ(2))/2
σ′′ ←σ′ · γ or σ′/γ
for all i ∈{1, . . . , d} do
x′′
i ←x′
i + σ′′ · N(0, 1)
end for
Dealing with a single objective only (nf = 1, ng = 0), it is
reasonable to establish an order among individuals by compar-
ing the values of f1. In constrained optimization, Hoffmeister
and Sprave [37] proposed the following preference relation to
guide the search towards the (feasible) global optimal point:
x1 ≺c x2(x1 dominates x2) :⇔
(21)
g(x1) ≤0 ∧g(x2) ≤0 ∧f(x1) ≤f(x2) or
g(x1) ≤0 ∧g(x2) > 0
or
g(x1) > 0 ∧g(x2) > 0 ∧p(x1) < p(x2)
with
p(g(x)) =
ng
X
i=0
max{0, gi(x)}2.
There are many other ways to deal with constraints; how-
ever, the one suggested here is well suited for use within rank
based algorithms with metamodel assistance. It allows for an
independent modeling of constraint functions. Hence, neither
discontinuities or non-differential points are introduced, nor
are non-linear combinations of prediction terms to be handled.
This will further be discussed in section IV.
Since EA are population-based search methods, they are
also suitable for Pareto optimization for multi-objective prob-
lems (nf > 1). In Pareto optimization, a set that is dominant
with respect to the relation ≺p, deﬁned as
x1 ≺p x2(x1 (Pareto) dominates x2) :⇔
(22)
∀i ∈{1, . . . nf} : fi(x1) ≤fi(x2)
∧
∃i ∈{1, . . .nf} : fi(x1) < fi(x2)
is sought. In constrained multi-objective problems, equations
21 and 22 can be combined.
A straightforward method for adapting the (µ + λ)-EA to
Pareto-optimization is through NSGA-II [38]. The population
is ﬁrst partitioned by means of non-dominated sorting (ﬁgure
4) and, then, sharing is employed (ﬁgure 5) by considering
distances between individuals of the same rank.
A comprehensive overview on this and other Pareto front
methods can be found in Deb [39] and Zitzler [40].
IV. METAMODEL-ASSISTED OPTIMIZATION
Aiming at the minimum possible number of costly evalua-
tions during the search for the optimal solution(s), black-box
f2
f1
Pareto optimal
        front
Co−domain of (f1, f2)
1
1
1
1
1
2
2
2
3
3
3
3
3
Fig. 4.
Non-dominated sorting: The population is partitioned in sub-
populations of equal dominance rank. The non-dominated subset of the
population is identiﬁed and its members are given rank 1. Then, the non-
dominated set from the remaining individuals is computed and given rank 2.
This goes on until a rank is assigned to each individual.
f2
Pareto optimal
        set
Co−domain of (f1, f2)
1
2
3
4
5
f1
Fig. 5.
Distance-based sorting of the Pareto front members: The circumfer-
ence of the boxes touching neighboring solutions determines their ﬁnal rank.
Thus, individuals lying away from their closest neighbors are promoted.
optimization methods can incorporate metamodels in different
ways.
• The metamodel is trained at a pre-processing phase
and the optimization algorithm searches for the optimal
solution based exclusively on the metamodel; the so-
computed optimum is then evaluated by means of the
exact-costly tool, the metamodel is updated after enrich-
ing the training database and the above steps are repeated
until a convergence criterion is met. Bayesian global
optimization algorithms work in this way [41], [31].
In MAEA, the term “generation-based control” denotes
algorithms in which some generations are evaluated by
the exact tool and some other generations are evaluated
solely by the metamodel.
• In each generation (apart from the very ﬁrst ones),
metamodels and exact evaluation tools are used in co-
operative manner. The evaluation of population members
does not rely entirely on the metamodel but the latter is
used to improve the efﬁciency of the local search steps.


<!-- página 6 -->

6
This is where the present paper puts emphasis. In high-
dimensional search spaces, a single metamodel might fail
to give predictions of acceptable accuracy over the entire
search space. The remedy is to switch to local search
strategies supported by local metamodels, [5], [19], [32],
[42]. In the literature, the term “individual-based control”
has been used to denote such a use of metamodels in
MAEA.
The idea to assist direct search algorithms by metamodels
has ﬁrst been explored by Torczon et al. [4], [42] for pattern
search algorithms. The metamodel was used to decide on the
sequence in which the search point located on the pattern
of local variations in pattern search should be evaluated. A
similar approach can be employed in EA by incorporating
a pre-screening procedure before the offspring population is
evaluated with the time consuming evaluation tool. Algorithm
3 gives an outline of MAES which is, in fact, a modiﬁed
version of the basic (µ+λ)-ES described in algorithm 1. Two
features distinguish MAES from standard ES.
1) All exactly evaluated individuals are recorded.
2) During the pre-screening phase, the objective function
values for new solutions are predicted by the metamodel,
before deciding whether they need to be re-evaluated by
the exact and costly tool.
Thereby, at generation t, the set of offspring solutions Gt is
reduced to the subset of offspring solutions Qt, which will
be evaluated exactly and will also be considered in the ﬁnal
selection procedure.
Algorithm 3 (µ + ν < λ)-MAES
t ←0
Pt ←init()
/* Pt ∈Sµ: Set of solutions */
evaluate Pt and insert results to database D
while t < tmax do
Gt ←generate(Pt)
/* Generate λ variations */
evaluate Gt with metamodel derived from D
choose set of maximal ν promising solutions Qt ⊆Gt
evaluate Qt and update database D with results
Pt+1 ←select(Qt ∪Pt)
/* Rank and select µ best */
t ←t + 1
end while
Next, the pre-screening procedures for the MAES will
be introduced, starting from single objective optimization
and generalizing to the multi-objective case later. For higher
dimensional solution spaces (nf + ng > 1), it is proposed
to predict all objective and constraint values independently,
instead of learning aggregate expressions. For notational con-
venience we introduce y1 = f1, . . . , ynf = fnf , ynf +1 =
g1, . . . , ynf +ng = gng. Accordingly, we deﬁne the predictions
ˆyi and corresponding standard deviations ˆsi, i = 1, . . . , nf +
ng. In single objective optimization, we will omit the index,
whenever it seems suitable.
A. Pre-screening procedures for single-objective optimization
A ranking algorithm, applied over the offspring population
Gt, identiﬁes the most promising individuals in the new
generation. In the general case, this algorithm is based on the
values ˆy1(x) (predictions for f1(x)) and ˆs1(x) (corresponding
standard deviations) obtained for each x ∈Gt through the
metamodel. Comparisons with objective function values for
the parent population Pt are necessary. Various criteria for
identifying promising solutions are discussed below. Once
the promising subset Qt of Gt has been found, its members
undergo exact evaluations.
The proposed criteria are all related to the notion of im-
provement. In minimization problems, the improvement I(y) of
a solution with the (predicted) objective function value y with
respect to the current optimal solution with objective function
value fmin is deﬁned by
I(y) =

0
if y > fmin
fmin −y
otherwise
.
(23)
As it will become clear below, in this expression, y could
be replaced by any other function value predicted by the
metamodel. In any case, a reasonable choice is that fmin
takes on the function value of the best individual in the parent
population, whenever a (µ + λ)-selection is used.
The simplest way to pre-screen new solutions is by ranking
them through the most likely improvement criterion, denoted
by MI(x) = I(ˆy(x)) (where y in expression 23 is deﬁned in
terms of ˆy(x)). This criterion makes use of the predicted mean
function value without considering the conﬁdence information
ˆs(x). Stated differently, this criterion reﬂects the improvement
achieved when the response value with maximum probability
density function is considered. Conceptually, this criterion is
similar to any pre-screening which is based on any kind of
neural networks.
In this paper, the main issue is how to beneﬁt from the
uncertainty information provided by the metamodel. For min-
imization problems, Torczon et al. [4], [43] suggested the use
of the lower conﬁdence bound (LB) of a prediction
flb(x) = ˆy(x) −ωˆs(x),
ω ∈[0, 3]
(24)
instead of the predicted value itself. The idea is to increase
the number of evaluations in promising but less explored
regions of the search space by directing the search towards
them. Emmerich et al. [19] demonstrated that flb is also
a good criterion in the context of MAEA. In particular, in
multimodal optimization problems the optimization results
improved signiﬁcantly.
By choosing ω, the user can scale the MAES from fast local
search to more explorative global search [43]. However, the
choice of an extra parameter might also be seen as a burden to
the user. A reasonable choice is ω = 2, which leads to a high
conﬁdence probability (ca. 97 %) for flb(x) to be the lower
bound of f(x), once the GRFM assumptions are valid. Still,
a fast local convergence on smooth problems is possible [19].
In order to get rid of the ω parameter, Ulmer et al. [9]
suggested the use of the probability of improvement (PoI). Let
φ denote the probability density function
φ(y) :=
1
√
2π exp(−y2/2)
(25)


<!-- página 7 -->

7
and Φ denote the cumulative distribution function of the
standard normal distribution
Φ(y) := 1
2(1 + erf( y
√
2)),
(26)
respectively. Let, also, fmin be the objective value of the
current best solution. Then, the probability of improvement
is deﬁned as
PoI(x) =
Z fmin
y=−∞
φ(y)dy = Φ
 ı(x)
ˆs(x)

(27)
ı(x) := fmin −ˆy(x).
(28)
Though, dimensionally, this criterion is not directly based on
responses, it can be used to rank the population members. An
important feature of the PoI criterion is that it equally promotes
solutions that are likely to give very small improvements with
high (i.e. around 0.5) probability and those expected to lead to
considerable improvement with small probability. According
to the applications shown in [9], a signiﬁcant improvement
compared to the mean value criterion is expected.
Another parameter–free approach that also takes the quan-
titative amount of improvement into account is the expected
improvement (ExI) criterion proposed by Schonlau et al. [31]
within the context of Bayesian global optimization. It reads
ExI(x)
=
Z fmin
−∞
(fmin −y)φ
y −ˆy(x)
ˆs(x)

dy
=
(fmin −ˆy(x))Φ
 ı(x)
ˆs(x)

+ ˆs(x)φ
 ı(x)
ˆs(x)

(29)
Using the aforementioned four improvement criteria, var-
ious pre-screening processes can be derived. As rule of the
thumb, it is desirable to increase the number of qualiﬁed
solutions whenever the pre-screening identiﬁes too many
promising solutions or to decrease it, if the predicted quality is
low. Within the proposed algorithm, this is decided upon the
comparison of the expected quality of each candidate solution
with the quality of parent solutions. However, the user needs to
deﬁne a maximum and minimum number of qualiﬁed solutions
in order to avoid convergence stagnation or excess number of
evaluations within the generation. With regard to the latter,
it should be noted that quite a few iterations are needed in
order to adapt the step-sizes and allow for reﬁned search in
high-performance regions. In this paper, the maximum number
νt := |Qt| of exact evaluations in each generation may vary
between 1 and µ.
According to the previous discussion, we recapitulate the
pre-screening procedures used in this paper, with some com-
ments on their use:
a) Mean value (MI) Pre-screening: It is based on MI(x).
Note that solutions with MI(x) = 0 are not selected, unless
there is at least one individual with a higher function value.
b) Probability of Improvement (PoI) Pre-screening: The
(µ) best individuals according to the probability of improve-
ment (PoI) criterion are selected. Alternatively, the user may
provide a threshold value by specifying a minimal probability
of improvement, e. g. 0.2 which will remain constant during
the reﬁned search.
c) Expected Improvement (ExI) Pre-screening: Based on
the ExI criterion, the µ best solutions are pre-selected. A
threshold value for ExI can be provided by the user so that
solutions with ExI lower than this threshold are rejected.
However, unlike the user–deﬁned threshold value of the PoI
criterion, the ExI threshold should dynamically decrease in the
vicinity of a local optimum, thus requiring extra parameters
to control it.
d) Lower bound (LB) pre-screening: Based practically
on eq. 24, the potential improvement criterion rewards promis-
ing solutions located in unexplored regions of the search space.
ω is user-deﬁned; ω = 2 seems to be a good choice.
Compared to the mean value pre-screening, only potential
improvements higher than zero are accepted, unless at least
one such improvement is found. Note, that getting rid of all
the user-deﬁned parameters is impossible. He should specify
either ω, ν or threshold values for the PoI and ExI criteria.
Finally, let us discuss some issues concerning the relation-
ship between the aforementioned pre-screening procedures.
At least two points deserve to be highlighted. First of all,
the role of the standard deviation is a different one for the
LB pre-screening compared to the PoI pre-screening. While
for the LB pre-screening, a high value of ˆσ always increases
the competitiveness of an individual, this does not hold for
the PoI pre-screening. For the latter, a high value of ˆσ(x) is
only rewarding, if ˆy(x) > fmin, otherwise, the probability of
improvement decreases with increasing ˆσ. Thus, the difference
between both pre-screening procedures is larger than it might
be expected at ﬁrst glance, and it is thus well justiﬁed to
include both into the empirical comparison. Unlike the PoI,
the ExI ﬁrst sinks and then grows again as ˆs(x) increases.
This behavior can be easily observed by plotting expression
29.
Moreover, one might consider a threshold version of the PoI
criterion, such that only individuals are accepted, whose value
exceeds the threshold – say τ with τ ∈[0, 1]. It turns out, that
this strategy is equivalent to a LB pre-screening using a value
of ω such that τ = Φ(−ω). In particular, a threshold version
of the PoI pre-screening with τ = 0.5 is formally equivalent to
a MI pre-screening. Note, that these equivalences only hold, if
no maximal value bounds the number of accepted individuals.
B. Constrained and Multi-objective Optimization
In this section, the aforementioned pre-screening techniques
will be extended to optimization problems with multiple objec-
tives. Problems with nf + ng > 1, i. e. problems with implicit
constraints and/or multiple objectives, in which the evaluation
describes a mapping from Rd to Rny, with ny := ng+nf > 1,
will be handled.
The basic idea is to compute a multivariate probability
distribution for a single response vector (the ﬁrst nf po-
sitions in the response and variance vectors correspond to
the objective function values and the last ng ones to the
constraints) and use this information during pre-screening. By
assuming an independent output (which might not always be
justiﬁed), separate metamodels for the different outputs can
be constructed. Thus, an independent Gaussian distribution


<!-- página 8 -->

8
with mean value ˆy ∈Rny and standard deviations ˆs ∈Rny
+
is considered. In the case of correlated outputs, specialized
multivariate GRFM (Co-Kriging models) can be employed to
calculate the probability distribution of response vectors [25].
1) Treatment of constraints: Dealing with a single objective
function and one or more constraints (nf = 1, ng > 0), the
pre-screening procedures should be based on the preference
relation, equation 21. Assuming that the reference solution
xmin is feasible, the improvement criteria can be generalized
in a straightforward manner.
The most likely improvement criterion is deﬁned as
MI(x) =
 I(ˆy1(x))
if ˆyi(x) ≤0, i = 2, . . . , 1 + ng
0
otherwise
.
(30)
Note, that this criterion is also valid for general multivariate
Gaussian distributions.
The PoI criterion can be calculated as
Z
y∈Hf
PDFx(y)dy
(31)
where PDFx denotes the estimated probability density function
of response vectors for input x and Hf denotes the dominated
hypervolume for xmin
Hf := [(−∞, . . . , −∞
|
{z
}
ny times
), (fmin, 0, . . . , 0
| {z }
ng times
)].
(32)
For independent response vector distributions the PoI criterion
can be simply calculated as
PoI(x) = Φ( ˆy1(x) −fmin
ˆs(x)
) ·
ng+1
Y
i=2
Φ(−ˆyi(x)
ˆs(x) )
(33)
provided that the best solution is feasible.
Accordingly, the expected improvement criterion reads
Z
y∈Hf
(fmin −y1)PDFx(y)dy
(34)
and in the case of a independent PDF (cf. Schonlau et al. [30])
ExI(x)
=

(fmin −ˆy(x))Φ
 ı(x)
ˆs(x)

+ ˆs(x)φ
 ı(x)
ˆs(x)

×
ng+1
Y
i=2
Φ(−ˆyi(x)
ˆs(x) ).
(35)
Last but not least, the generalization for the LB criterion
should be discussed. The concept is to work with the lower
bound of a conﬁdence interval, symmetrically placed around
the mean prediction value. This can be generalized by working
with conﬁdence interval boxes (cf. Figure 6). In the case of
independent distributions these boxes can be calculated by
B(x) := ˆy ± ωˆs(x). The value for ω can be derived from
a user speciﬁed conﬁdence probability pα - the probability for
the true result to lie inside an interval box (=Pr(y ∈B(x))) -
with the help of the following equation
pα(ω) = (1 −2Φ(ω))ny.
(36)
 15
 20
 0
 5
 10
 15
 20
 0
 0.2
Mean  values of approximations
g1
f1
 0
−5
−10
Constraint boundary
Lower bound edges of approximations
Probability Density
Rank 3
Confidence intervals
Rank 1
Rank 2
Fig. 6.
Interval boxes for approximations in a solution space with one
objective and one constraint function.
Pα
ω
Confidence factor
1
0
1
2
3
4
0
n =1
n =2
n =3
n =4
y
y
y
y
m = 1
m = 2
m = 3
m = 4
Fig. 7.
Computation of the conﬁdence factor ω for a desired pα value and
a given number of (assumed) independent response functions ny (equation
36).
Practically, the ω value can be obtained from a graph of this
function (c.f. ﬁgure 7). Given the value for ω, we thus get
LB(x) =



I(ˆy1(x) −ωˆs1(x))
if ˆyi(x) −ωˆsi(x) ≤0,
i = 2, . . . , 1 + ng
0
otherwise.
Having established these criteria for the pre-screening proce-
dure, all the rest can be worked out as in the single criterion
case.
2) Treatment of multiple objectives: Here, the general-
ization for nf
> 1 and ng
= 0 is discussed, but the
concepts can easily be extended to ng > 0 (cf. equation 1).
According to section III, optimal solutions according to the
Pareto dominance relation (cf. equation 22) are sought.
Similarly to the constrained case, a multivariate (nf-
dimensional) distribution for each point x ∈S is provided
by the GRFM.
The difﬁculty in the generalization of the pre-screening
procedures is that the notions of best found solution and of
improvement are not clearly deﬁned in the multi-objective
case. The best found solution is equivalent to the set of non-
dominated solutions Et in the current population Pt.
In order to have a scalar measure for improvement, which is
needed at least for the generalization of the ExI criterion, the
dominated hypervolume measure H(P) of a set P (cf. [40]),
i. e. the Lebesgue measure of the dominated hypervolume
VD for a restricted solution space (cf. ﬁgure 9) can be
employed. Fleischer [44] proved that, for countable spaces2,
2i. e. all spaces that are relevant if these algorithms are implemented on
digital computers.


<!-- página 9 -->

9
the hypervolume measure of a set takes its maximum, if the set
found covers the true Pareto set. Furthermore, adding a new
point to P, the hypervolume H(P ∪{x}) increases, if and only
if x is not dominated by any point in Et and thus Et ∪{x}
could be regarded as an improvement of Et. For a normalized
solution space, higher values of H reﬂect better solution sets.
Normalized solution spaces are restricted solution spaces for
which a gain according to the ﬁrst criterion is as important
as the same gain according to the second criterion. Provided
that the user can deﬁne such a normalization, the improvement
measure is deﬁned as follows:
I(y(x)) =
(37)
=
 H(Et ∪{y(x)}) −H(Et)
if Et non-dominates y(x)
0
otherwise.
For most practical problems in multi-objective optimization
it is easy to ﬁnd a rough restriction for the solution space.
However, it is often difﬁcult to normalize a restricted solution
space a-priori. Thus, the improvement measure might be
biased towards improvements to one of the objectives. Thus,
a quantitative interpretation of I(y(x)) - as it is needed for
the ExI criterion - should be handled with care. Given these
preliminaries, the pre-screening procedures can be generalized:
For the mean value and the lower conﬁdence bound pre-
screening, ranking by means of non-dominated sorting is used,
by replacing the true function value by the mean value y(x) of
the approximation or the lower conﬁdence bound y−ωˆs(x) of
the conﬁdence interval box (cf. ﬁgure 8), respectively. These
strategies are described by Emmerich et al. [45].
If the user can provide an adequate normalization of the
solution space, the improvement criteria MI(x) = I(y(x))
and LB(x) = I(y(x) −s(x)) may also be chosen for pre-
screening.
The PoI criterion can be adopted in a straightforward
manner by calculating the integral of the PDF of the response,
i.e.
PoI(x) =
Z
y∈Vnd
PDFx(y)dy,
(38)
Vnd := {y|y is non-dominated by Et}.
(39)
For independent distributions it is reasonable to partition the
non-dominated volume into disjoint rectangles [yi
min, yi
max[
with ∪m
i=1[yi
min, yi
max[= Vnd(Et), [44], and then determine
the integral that appears in equation 38 by
n
X
i=0
nf
Y
j=1
(Φ(ri
max,j −ˆyj(x)
ˆsj(x)
) −Φ(ri
min,j −ˆyj(x)
ˆsj(x)
)).
(40)
Again, Φ denotes the cumulative Gaussian distribution
function. The PoI measure is the probability of x to be non-
dominated by individuals in Et. It is remarkable, that this
measure can be calculated without restricting the solution
space and making explicitly use of the quantity of the im-
provement I(x). However, as already mentioned for single-
criterion problems, a possible weakness is that it hardly favors
large improvements. Should this be desired, ExI can be used,
calculated by the integral
ExI(x) =
Z
y∈Vnd(P )
I(y) · PDFx(y)dy.
(41)
Integration is much more difﬁcult even if statistical inde-
pendence is assumed. However, even in this case, piecewise
numerical integration over nf dimensional hyper-rectangles
seems to be the most appropriate way to deal with this
integration. As a simple alternative, one may use Monte-
Carlo integration by producing N random samples qi of the
Gaussian distribution with mean ˆy and standard deviation ˆs
and by measuring the increase in hypervolume I(qi). Then,
the approximate integral reads:
ExI(x) ≈1
N
N
X
i=1
I(qi)
(42)
.
An error estimate for the monte carlo estimate is given by:
( 1
N
N
X
i=1
I(yi)) −ExI(x) ≈S2/N.
(43)
Here the variance S2 is deﬁned as
S2 =
1
N −1
N
X
i=1
(I(yi) −1
N
N
X
i=1
I(yi))2.
(44)
This result can directly be obtained from the theory of monte
carlo integration ([46], pp. 11). Regardless of the dimension
of the search space, the error scales like 1/
√
N.
The progress obtained with the latter criterion heavily
depends on the adequacy of the improvement criterion in
equation 37 and thus on the adequacy of the solution space
normalization. Thus, it is recommended to handle the ExI
criterion with care and prefer the LB criterion, whenever the
normalization is not clear.
Also in the constrained multi-objective case, the criteria can
be generalized. Assuming independent constraint functions, it
sufﬁces to multiply the expressions for PoI and ExI (38 and 41)
with the probability of a feasible solutions. Thus, we receive
PoI(x) =
Z
y∈Vnd
PDFx(y)dy ·
ng+1
Y
i=2
Φ(−ˆyi(x)
ˆs(x) )
(45)
and
ExI(x) =
Z
y∈Vnd(P )
I(y)PDFx(y)dy ·
ng+1
Y
i=2
Φ(−ˆyi(x)
ˆs(x) ).
(46)
V. METHOD APPLICATION – RESULTS AND DISCUSSION
A. Mathematical Test Problems and Performance Measures
At ﬁrst, experiments have been conducted on selected math-
ematical test problems in order to compare the performance
of different MAES variants. These variants were tested on
different objective function landscapes, featuring minimization
of a simple convex function (sphere function, appendix A), a


<!-- página 10 -->

10
on the old Pareto front
0
 5
 10
 15
 20
 0
 5
 10
 15
 20
 0
 0.2
f1
f2
Probability Density
Precise Evaluations
Mean  values of approximations
Lower bound edges of approximations
x1
x2
x3
Fig. 8.
Interval boxes for approximations in a solution space with two
objectives.
Pareto−front
Vd(P)
Vnd(P)
f1
f2
f(x1)
f(x2)
f(x3)
f(x4)
f max
f min
Fig. 9.
Illustration of the hypervolume measure.
non-isotropic function (ellipsoid function, appendix B), a dis-
continuous function (step function, appendix C) and - ﬁnally -
a highly multimodal function (Ackley function, appendix D).
MAES testing was carried out using population sizes of
µ = 5 and λ = 100 individuals, among which ν = 20
individuals at most were pre-selected for exact evaluation.
Each run was repeated 20 times, each of which with a different
random number seed.
The median of the best results found after t evaluations
(t ≤1000) was plotted. In order to get a reliability measure,
the 16th worst function value, i. e. the 80%-quantile of the
distribution of the obtained function values, was recorded and
presented. For similar studies on 20–dimensional test-cases
and with different population sizes the reader should refer to
[9], [19], [45] and recently [3].
B. Prediction Accuracy Measures
It is well known that EA are rank-based strategies that
are invariant to monotonic transformations of the objective
function. Hence, for a metamodel used in conjunction with
an EA to be successful, it sufﬁces this to predict the subset
of Gt that would be selected by the recombination if all
evaluations were precise improvements with respect to the
parent population Pt. The so–called retrieval quality of any
pre-screening tool (metamodel) can be measured through the
recall and precision measures deﬁned below.
Let Mµ(A) denote the subset of the µ best solutions in
A. Pre-screening aims at identifying the members of Gt ∩
Mµ(Gt ∪Pt) which will enter the next generation. Thus, it is
desirable that
Qt ≈Gt ∩Mµ(Gt ∪Pt).
(47)
It is reasonable that none of the metamodels could always
retrieve the ensemble of relevant individuals out of Gt. A
non-satisfactory metamodel is one which: (a) fails capturing
a considerable part of Gt ∩Mµ(Gt ∪Pt) or (b) in order to
capture as many as possible of them, it additionally selects too
many irrelevant individuals.
The retrieval accuracy, practically in relation to the ﬁrst of
the two unpleasant situations just mentioned, i. e. the ratio
the relevant solutions retrieved from Gt to the number of all
relevant solutions in Gt, is quantiﬁed as follows:
recall(t) = |Mµ(Gt ∪Pt) ∩Qt|
|Mµ(Gt ∪Pt) ∩Gt|,
(48)
where the optimal values is recall(t) = 1.
On the other hand, precision(t) is a measure for controlling
the second unpleasant metamodel behavior. This is expressed
by the ratio of the number of correctly retrieved solutions to
the total number of retrieved solutions, namely:
precision(t) = |Mµ(Gt ∪Pt) ∩Qt|
|Qt|
(49)
The optimal value for this criterion is precision(t) = 1.
Unfortunately, in contrast to quantitative measures such as
y −ˆy plots, speciﬁcity measures cannot be evaluated without
performing extra evaluations with the costly evaluation tool.
Hence, these are useful for statistics on simple academic cases
but not for real–world problems.
C. Implementation details
The basic evolution strategy corresponds to the one de-
scribed previously in section IV. The initial step-size was
set to 0.05% of the search space width. The database is
formed only by exact evaluations. The metamodel is used
from the ﬁrst generation on. As soon as there are more than
2d solutions in the database, the algorithm switches to the
local metamodeling strategy as described in section II. For all
strategies, the maximal number of pre-selected individuals was
set to µ.
D. Results – Discussion on the performance
The ﬁrst comparison was conducted on the 20-dimensional
sphere model (cf. appendix A). The median of the best found
solution is shown in Figure 10. All metamodel-based strategies
outperformed conventional strategies (i.e. (5+20)-ES, (5+35)-
ES3, (5+100)-ES) since they ask considerably less function
evaluations. An exception is the (1+10)-ES that performs com-
parable to the MAES that utilized the conﬁdence measure for
pre-screening. This is due to the small population incorporated
in the (1+10)-ES that allows twice as many generations to be
carried out. The best average performance was obtained using
the mean value pre-screening.
Similar results were obtained on the non-isotropic elliptic
function (ﬁgure 11). This is interesting since, during the choice
of the correlation function, we didn’t consider non-isotropic
3This strategy has been added in order to be comparable with Ulmer et al.
[9].


<!-- página 11 -->

11
ones and the metamodel was expected to be less precise than in
the isotropic case. However, the results show that the approach
is quite insensitive to small “errors” in the model assumptions.
It should also be noted that, on this test function, MAES
versions outperform all standard ES variants. In particular, the
(1+10)-ES was outperformed by the MAES using conﬁdence
measures as well.
Unlike previous test functions, the MAES based on conﬁ-
dence measures yielded better results than that using the mean
value criterion (ﬁgure 12); in fact, the mean value criterion
performance was expected not to be good, since the step
function is discontinuous. The LB criterion performs slightly
worse than the ExI one. The use of conﬁdence measures
is advantageous since it drives the search towards the most
unexplored regions of the search space, where the ˆs(x) values
increase. In contrast, the mean value pre-screening or the
conventional ES use to keep searching over already adequately
explored regions or areas with negligibly varying cost values
(plateaus).
A typical example of multimodal functions is the 20-dim.
Ackley function (Appendix D); the corresponding results are
shown in ﬁgures 13 (history) and 14 (ﬁnal results and standard
deviations). Here, the advantage of using the conﬁdence mea-
sure expressed by ˆs(x) is obvious. As long as the search takes
place far from the global optimum, the algorithm behaves as
on the sphere function. Later on, the multimodal structure of
the search space seems to be reﬂected on the performance.
In this phase, it is important to use the information included
in the conﬁdence measure, since this will guide the search
towards more unexplored regions, i.e. away from local optima.
The advantage of strategies using ˆs(x) becomes signiﬁcant
when looking at the 80% quantile, where all strategies using
the uncertainty information outperform those based on the
mean value pre-screening; the latter stagnates after about 200
evaluations.
An additional study was carried out on the 20-dim. Ackley
function (appendix D), in order to compare the effect of
different parametric settings of MAES. Figure 15 displays
the results and reveals that an optimal value for ω exists. For
high ω values (ω = 3), the intensive exploration led to low
convergence speed. For low ω values (ω ≤1), the MAES used
to converge to a local optimum, due to the weak exploration.
The effect of the number of pre-selected individuals ν on the
convergence speed of MAES is also illustrated in ﬁgure 15.
According to this ﬁgure, the high number of generations which
were carried out at the same computing cost, due to the low
value of ν, led to signiﬁcantly better results during the ﬁrst
generations but increased the risk of premature stagnation.
Note that stagnation occured later than it could even happen
if an erroneous ω was used. The choices ω = 2 and ν = 20
led to a similar behavior to those of the ExI and PoI strategies
with ν = 20.
Finally, the long term behavior of the MAES was studied.
Figure 16 displays results for a long run with 2000 precise
evaluations on the 20-dim. ellipsoid problem. The results
indicate that the MAES is capable to approximate a local
optimum with a high precision. Another conclusion is that
the absolute error of the prediction shrinks proportionally to
 1e-05
 0.0001
 0.001
 0.01
 0.1
 1
 10
 100
 1000
 0
 200
 400
 600
 800
 1000
Median of best found function value
No. of evaluations
1p10
5p20
5p35
5p100
MLI
LBI
PoI
ExI
Fig. 10.
Median of the best found function value of different EA on the
20-dim. sphere problem.
 0.01
 0.1
 1
 10
 100
 1000
 10000
 0
 200
 400
 600
 800
 1000
Median of best found function value
No. of evaluations
1p10
5p20
5p35
5p100
MLI
LBI
PoI
ExI
Fig. 11. Average convergence behavior of different EA on the 20-dim. scaled
sphere problem (ellipsoid problem).
 1
 10
 100
 1000
 0
 200
 400
 600
 800
 1000
Median of best found function value
No. of evaluations
1p10
5p20
5p35
5p100
MLI
LBI
PoI
ExI
Fig. 12.
Average convergence behavior of different EA on the 20-dim. step
function.
 1
 10
 100
 0
 200
 400
 600
 800
 1000
Median of best found function value
No. of evaluations
1p10
5p20
5p35
5p100
MLI
LBI
PoI
ExI
Fig. 13. Average convergence behavior of different EA on the 20-dim. Ackley
function.


<!-- página 12 -->

12
 0
 5
 10
 15
 20
 25
 30
1p10
5p20
5p35
5p100
MLI
LBI
PoI
ExI
Best function value after 1000 eval.
Strategy
Mean/stdv.
Fig. 14.
Summary of the results on Ackley’s function after 1000 evaluations
each. The mean value and the standard deviation of the best found result is
displayed.
 5
 10
 15
 20
 25
 0
 200
 400
 600
 800
 1000
80%-quantile of best found function value
No. of evaluations
nu=5, omega=2
nu=5, omega=0
nu=5, omega=1
nu=5, omega=3
nu=1, omega=2
nu=15, omega=2
Fig. 15.
Development of the 80%-quantiles for best found function values
for differently parameterized versions of the MAES. The runs have been
conducted on the 20-dim. Ackley function. Different settings for the number
of pre-selected individuals ν and the conﬁdence factor ω in the (µ+λ)-MAES
using the criterion described in equation 24 are displayed.
the distance from the optimum.
E. Discussion on precision and recall
For all pre-screening strategies, the accuracy measures (pre-
cision and recall) have been evaluated and averaged results (for
the 20 runs) are illustrated.
The best recall values have been obtained through the LB,
ExI, and PoI criteria (ﬁgures 19, 21, and 23). Their ability to
capture a large part of the really top-most individuals (more
than 40%) can be discussed after examining the precision plots
shown in ﬁgures 20, 24, and 22. In all aforementioned cases,
the precision is very low. This indicates that high recall values
can be achieved by evaluating a large surplus of designs in
each generation with the exact evaluation software. The low
number of generations needed is probably the reason for the
bad performance of these strategies on the simpler test-cases.
A better balance between accuracy and precision has been
achieved through the mean value pre-screening. However, re-
call (ﬁgure 17) stays below 40%, except for the step function.
In contrast to the other pre-screening strategies, precision is
above 40% (ﬁgure 18) most of the time, while the preci-
sion for the other strategies stays below 20%. Summarizing,
 1e-04
 0.001
 0.01
 0.1
 1
 10
 100
 1000
 10000
 0
 500
 1000
 1500
 2000
sampled value
absolute prediction error
Fig. 16.
A run of the (20 + 5 < 100)-MAES with PoI pre-screening on the
ellipsoid problem with 2000 evaluations. It demonstrates that the MAES is
capable to converge to a high precision. Also, it can be obtained that the error
of the predictions shrinks proportionally with the distance to the optimum.
improvements are likely to get lost through the mean value
prescreening strategy; however, the high number of relevant
solutions identiﬁed is, indeed, an improvement.
Finally, the capability of the GRFM to obtain valid predic-
tions during a run of the MAES on a multimodal problem,
was studied. For that purpose, all 1000 evaluations obtained
during one run have been compared to their predicted values.
The results for the PoI-MAES are displayed in ﬁgure 25. There
is a strong correlation between predicted and observed values.
However, there is also a deviation between these two values.
One of the advantages of GRFM is that it provides the degree
of uncertainty of each prediction. In order to check the validity
of the lower conﬁdence bound given by ylb = ˆy −2ˆs, results
have also been plotted in a y−ylb diagram (ﬁgure 26). It turns
out that ylb is a good approximation to the sharp lower bound
for the true function values.
F. Discussion of results on constrained optimizations
In order to evaluate the performance of MAES coupled
with different pre-screening criteria in constraint optimization
problems, test runs on the 10-dim. Keane problem (appendix
E) have been conducted. In this problem, a highly multimodal
function has to be minimized, subject to non-linear constraints.
Results are summarized in ﬁgure 27 (history of median)
and 28 (ﬁnal results and standard deviations). In order to be
comparable with previous studies [19] we slightly changed
the parameters of the population size and a (15 + 15 < 100)-
MAES was tested. Two important observations can be made.
First of all, any metamodel assisted strategy performs signif-
icantly better than the corresponding EA without metamodel
assistance. Second, strategies using the conﬁdence informa-
tion perform much better than the ones utilizing only the
predicted function value. The differences between the three
pre-screening criteria that use conﬁdence information (lower
bound, PoI and ExI) are less signiﬁcant for this problem.
G. Results on Multi-objective functions
In order to prove the feasibility of the new approach,
the multi-objective strategies have been tested on the 10-
dimensional generalized Schaffer problems F. The curvature


<!-- página 13 -->

13
 0
 0.2
 0.4
 0.6
 0.8
 1
 0
 100 200 300 400 500 600 700 800 900
Average Recall
No. of evaluations
Sphere 20-D
Scaled sphere 20-D
Step 20-D
Ackley 20-D
Fig. 17.
Recall for mean value pre-screening.
 0
 0.2
 0.4
 0.6
 0.8
 1
 0
 100 200 300 400 500 600 700 800 900
Average Precision
No. of evaluations
Sphere 20-D
Scaled sphere 20-D
Step 20-D
Ackley 20-D
Fig. 18.
Precision for mean value pre-screening.
 0
 0.2
 0.4
 0.6
 0.8
 1
 0
 100 200 300 400 500 600 700 800 900
Average Recall
No. of evaluations
Sphere 20-D
Scaled sphere 20-D
Step 20-D
Ackley 20-D
Fig. 19.
Recall for lower bound pre-screening.
 0
 0.2
 0.4
 0.6
 0.8
 1
 0
 100 200 300 400 500 600 700 800 900
Average Precision
No. of evaluations
Sphere 20-D
Scaled sphere 20-D
Step 20-D
Ackley 20-D
Fig. 20.
Precision for lower bound pre-screening.
 0
 0.2
 0.4
 0.6
 0.8
 1
 0
 100 200 300 400 500 600 700 800 900
Average Recall
No. of evaluations
Sphere 20-D
Scaled sphere 20-D
Step 20-D
Ackley 20-D
Fig. 21.
Recall for PoI pre-screening.
 0
 0.2
 0.4
 0.6
 0.8
 1
 0
 100 200 300 400 500 600 700 800 900
Average Precision
No. of evaluations
Sphere 20-D
Scaled sphere 20-D
Step 20-D
Ackley 20-D
Fig. 22.
Precision for PoI pre-screening.
 0
 0.2
 0.4
 0.6
 0.8
 1
 0
 100 200 300 400 500 600 700 800 900
Average Recall
No. of evaluations
Sphere 20-D
Scaled sphere 20-D
Step 20-D
Ackley 20-D
Fig. 23.
Recall for ExI pre-screening.
 0
 0.2
 0.4
 0.6
 0.8
 1
 0
 100 200 300 400 500 600 700 800 900
Average Precision
No. of evaluations
Sphere 20-D
Scaled sphere 20-D
Step 20-D
Ackley 20-D
Fig. 24.
Precision for ExI pre-screening.


<!-- página 14 -->

14
 5
 10
 15
 20
 25
 5
 10
 15
 20
 25
y predicted
y
Fig. 25.
y −y plot for a run of the MAES on the 20-dim. Ackley function.
 5
 10
 15
 20
 25
 5
 10
 15
 20
 25
y lower bound
y
Fig. 26.
y −ylb plot for a run of the MAES on the 20-dim. Ackley function.
-0.6
-0.5
-0.4
-0.3
-0.2
-0.1
 0
 0
 200
 400
 600
 800
 1000
Best found function value (Median)
No. of evaluations
1p10
15p100
5p20
Mean
POI
EXI
LB
Fig. 27.
Median of best found feasible function values for different strategies
on the multimodal and constrained 10-dim. Keane bump problem (20 runs)).
-0.7
-0.6
-0.5
-0.4
-0.3
-0.2
-0.1
1p10
5p20
5p100
MLI
LBI
PoI
ExI
Best function value after 1000 eval.
Strategy
Mean/stdv.
Fig. 28. Mean values and standard deviations for best found feasible function
values for different strategies on the multimodal and constrained 10-dim.
Keane bump problem (20 runs, 1000 objective function evaluations).
of the Pareto front for these problems depends on the choice
of the parameter γ [47]. By setting γ > 1, a convex Pareto
front is the solution of the problem. The opposite occurs if
γ < 1 where the Pareto front is concave. By setting γ = 1,
the Pareto front is linear.
Results on problems with differently shaped Pareto fronts
are displayed in ﬁgure 29 (convex Pareto front), ﬁgure 30
(linear Pareto front) and ﬁgure 31 (concave Pareto front). All
experiments have been conducted with an initial step-size of
1. The (20 + 20 < 100)-NSGA-II has been opposed to the
(20 + 100)-NSGA-II and the (20 + 20)-NSGA-II. The same
variation procedure to that used in the single-objective ES was
employed. In the multi-objective case, a larger population size
was used, in order capture a greater variety of solutions.
On the average, pre-screening through the mean value is
less successful than taht through the conﬁdence information.
The ExI criterion yields the best performance, followed by
the lower bound and PoI criteria. In particular, on the concave
and linear problems, the ExI criterion leads to signiﬁcantly
better results. However, we note that - unlike the PoI and the
lower bound criteria - the performance of the ExI criterion
depends on the choice of the reference point, which was set
to f max = (20, 20)T for the given problems. Furthermore,
the cost for computing the ExI criterion is signiﬁcantly higher
than that associated with the lower bound and PoI criteria.
Hence, the two latter criteria should be considered as efﬁcient
pre-screening alternatives. The marginerformance deviation
between all metamodel-assisted NSGA-II and the two versions
of the standard NSGA-II is signiﬁcant on all three problems.
VI. RAE 2822 AIRFOIL OPTIMIZATION
The RAE 2822 airfoil was redesigned aiming at optimal
performance at three operating points; the corresponding ﬂow
conditions are listed in table I. First, the ﬂow around the base-
line RAE 2822 airfoil was computed at the aforementioned
conditions. The computation resulted to different values for
the drag, lift, and pitching moment coefﬁcients. The objective
was to minimize the airfoil drag fi = Ci
d at each operating
point (i = 1, 2, 3), maintain at least the baseline airfoil lift
while allowing the pitching moment to vary within a 2 %
range.
TABLE I
FLOW CONDITIONS FOR THE RAE 2822 AIRFOIL DESIGN PROBLEM
cruise
off-design 1
off-design 2
M
0.734
0.754
0.680
Re
6.5 · 106
6.2 · 106
5.7 · 106
α
2.8
2.8
1.8
transition
3%
3%
11%
Thus, the aerodynamic constraints for lift Ci
l and pitching
moment Ci
m were as follows:
• ∀i ∈{1, 2, 3} :
Ci
l ≥Cl,base with Cl,base being the
lift coefﬁcient of the baseline airfoil.
• ∀i ∈{1, 2, 3} :
Ci
m within +/- 2% of the pitching
moment Cm,base of the baseline airfoil.
Furthermore, some geometrical constraints have been de-
ﬁned:


<!-- página 15 -->

15
 0
 0.2
 0.4
 0.6
 0.8
 1
 0
 0.2
 0.4
 0.6
 0.8
 1
f2
f1
20p100
20p20
MLI
LBI
PoI
ExI
Fig. 29. Approximation to a convex Pareto front. The 50% attainment surface
on the 10-dim. generalized Schaffer problem with γ = 2 is displayed (10 runs,
1000 evaluations).
 0
 0.2
 0.4
 0.6
 0.8
 1
 0
 0.2
 0.4
 0.6
 0.8
 1
f2
f1
20p100
20p20
MLI
LBI
PoI
ExI
Fig. 30.
Approximation to a linear Pareto front. The 50% attainment surface
on the 10-dim. generalized Schaffer problem with γ = 1 is displayed (10
runs, 1000 evaluations).
 0
 0.2
 0.4
 0.6
 0.8
 1
 0
 0.2
 0.4
 0.6
 0.8
 1
f2
f1
20p100
20p20
MLI
LBI
PoI
ExI
Fig. 31.
Approximation to a concave Pareto front. The 50% attainment
surface on the 10-dim. generalized Schaffer problem with γ
= 0.5 is
displayed (10 runs, 1000 evaluations).
• The thickness of the new airfoil at 5% chord length
should be greater than or equal to the corresponding
thickness of the baseline airfoil.
• The maximum thickness should be greater than or equal
to the maximum thickness of the baseline airfoil.
• The leading edge radius should be greater than or equal
to 90% of the leading edge radius of the baseline airfoil.
• The trailing edge angle should be greater than or equal
to 80% of the trailing edge angle of the baseline airfoil.
Geometrical processing of any candidate airfoil is possible
once the airfoil shape has been generated and prior to solving
the computationally expensive ﬂow equations. This is why
the geometrical constraints are treated differently from the
aerodynamic ones, which should be taken into account only
after solving the ﬂow problem. All candidate aifoil shapes un-
dergo a preliminary geometrical check. During mutation, many
mutated offspring are created and tested unless the necessary
number of feasible offspring (according to the geometrical
constraints) is obtained or the number of samplings exceeds
1000. The latter was incorporated in both strategies - the
M-NSGA-II and standard NSGA-II - in order to get higher
percentages of feasible individuals for exact evaluation.
The airfoil parameterization was based on Bezier polyno-
mials, with the ordinates of control points acting as the design
variables. Each airfoil side was parameterized using ﬁve Bezier
control points; this resulted to six degrees of freedom, in total,
since the ﬁrst and last control point on either side was ﬁxed.
All other aspects and parameters concerning mesh generation,
ﬂow solution, models in use etc. are kept constant during this
study.
A comparison between the NSGA-II and the metamodel-
assisted NSGA-II on the RAE problem is displayed in ﬁgure
33 (f1 vs. f2), ﬁgure 34 (f1 vs. f3), and ﬁgure 35 (f2 vs. f3). In
all three cases, attainment surfaces have been plotted for the
(20 + 20)-NSGA-II (NSGA) and the (20 + 4 < 20-NSGA-II
(M-NSGA) (for a detailed plot of all runs we refer to [45]).
In particular, the best Pareto front (BEST) consists of the non-
dominated set from the union of all points over all ﬁve runs.
The median attainment surface (AVG:average) consists of all
non-dominated points that are weakly dominated by at least
two of the other Pareto fronts obtained with the same strategy.
A number of 1000 evaluations of the objective function were
carried out for each of the runs.
The plots demonstrate the gain in solution quality achieved
using the new techniques, with almost the same CPU cost.
Through the use of metamodels, the diversity and precision
of the computed optimal set was improved. The results show
additional improvement if the conﬁdence interval was used.
The latter was used by the optimization method to detect and
re-sample insufﬁciently explored regions of the search space.
Considering constrained optimization, the metamodel as-
sistance made it possible to achieve a signiﬁcantly higher
ratio of feasible solutions in all ﬁve cases of the RAE 2822
problem (ﬁgure 32). Furthermore, it was possible to ﬁnd an
improvement for the baseline design of the RAE 2822 test
case.
VII. CONCLUSIONS
The use of metamodels within evolutionary algorithm based
optimization methods is beneﬁcial whenever dealing with
computationally expensive function evaluations. Data collected
for all previously evaluated points can be used during the
evolution to build metamodels and, through them, screen
out the less promising generation members. By doing so,
expensive evaluations of the most promising population mem-
bers are necessary and the economy in computational cost is
considerable. For multimodal problems and in multi-objective
optimization it is strongly recommended to use the conﬁdence


<!-- página 16 -->

16
1
2
3
4
5
0
100
200
300
400
500
600
700
800
900
1000
RUN
NO. OF FEASIBLE SOLUTIONS
NSGA−II
MNSGA−II (Mean)
MNSGA−II (LB)
Fig. 32.
Number of feasible solutions for 5 runs on the RAE test case.
 0.0285
 0.0286
 0.0287
 0.0288
 0.0289
 0.029
 0.0291
 0.0292
 0.0293
 0.0294
 0.0295
 0.0216
 0.0218
 0.022
 0.0222
 0.0224
 0.0226
 0.0228
f2
f1
Attainment surfaces f1 vs. f2
NSGA-BEST
NSGA-AVG
M-NSGA-BEST
M-NSGA-AVG
Baseline Design
Fig. 33.
Feasible RAE 2822-results with NSGA: f1 vs. f2
 0.01161
 0.01162
 0.01163
 0.01164
 0.01165
 0.01166
 0.01167
 0.01168
 0.0216
 0.0218
 0.022
 0.0222
 0.0224
 0.0226
 0.0228
f3
f1
Attainment surfaces f1 vs. f3
NSGA-BEST
NSGA-AVG
M-NSGA-BEST
M-NSGA-AVG
Baseline Design
Fig. 34.
Feasible RAE 2822-results with NSGA: f1 vs. f3
 0.01161
 0.01162
 0.01163
 0.01164
 0.01165
 0.01166
 0.01167
 0.01168
 0.0285 0.0286 0.0287 0.0288 0.0289 0.029 0.0291 0.0292 0.0293 0.0294 0.0295
f3
f2
Attainment surfaces f2 vs. f3
NSGA-BEST
NSGA-AVG
M-NSGA-BEST
M-NSGA-AVG
Baseline Design
Fig. 35.
Feasible RAE 2822-results with NSGA: f2 vs. f3.
information provided by a Gaussian Random Field Metamodel
(GRFM) in order to boost evaluations towards less explored
regions. The use of GRFM may prevent premature conver-
gence without being misled by poor predictions. In particular,
in multi-objective optimization, the integration of the conﬁ-
dence information into the metamodel helps to increasing the
coverage of the Pareto optimal set. In this paper, this was
demonstrated on mathematical test problems as well as on a
design problem in aerodynamics.
This paper focused on the understanding of the behavior
of various pre-screening criteria. Despite the high number
of test problems analyzed in this paper, there are still open
questions. However, one of the most important conclusions is
that, according to the results presented in the paper, there is
an interesting trade-off between recall and precision measured
during the pre-screening. It seems that the “adaptation” of the
number of pre-selected individuals plays an important role for
the performance of the algorithms. The same results indicate
that measuring recall and precision may not sufﬁce to explain
the good performance of the lower bound pre-screening in
case of multimodal and ﬂat functions. It seems, that the lower
bound pre-screening guides the search towards unexplored
regions of the search space, which are not likely to be visited
by standard EA. Another lesson learned from these studies is
that MAES utilizing mean value pre-screening perform badly
in the presence of discontinuities and plateaus. The use of the
conﬁdence measure improves the results signiﬁcantly.
APPENDIX
A. Sphere problem
f(x) =
d
X
i=1
x2
i →min
(50)
xi ∈[−5.12, 5.12], i = 1, . . . , d
(51)
Known minimum: x∗= 0, f(x∗) = 0
B. Ellipsoid problem
f(x) =
d
X
i=1
ix2
i →min
(52)
xi ∈[−5.12, 5.12], i = 1, . . . , d
(53)
Known minimum: x∗= 0, f(x∗) = 0
C. Step problem
f(x) =
d
X
i=1
⌊xi⌋2 →min
(54)
xi ∈[−5.12, 5.12], i = 1, . . . , d
(55)
Known minimum: x∗= 0, f(x∗) = 0


<!-- página 17 -->

17
D. Ackley’s problem
−20 · exp(−0.2
p
(1
d ·
n
X
i=1
x2
i )) −exp(1
d
d
X
i=1
cos(2πxi)) (56)
xi ∈[−32.768, 32.768], i = 1, . . . , d
(57)
Known minimum: x∗= 0, f(x∗) = 0
E. Keane’s bump problem
min −| Pn
i=1(cos4 xi) −2 ∗Qn
i=1(cos2(xi))|
pPn
i=1 i ∗x2
i
,
(58)
n
Y
i=1
xi > 0.75,
n
X
i=1
xi < 15n
2
(59)
xi ∈]0, 10.0]
(60)
Minimum is unknown
F. Generalized Schaffer problem
f1(x) := 2
γ (
d
X
i=1
x2
i )γ/2 →min,
(61)
f2(x) := 2
γ (
d
X
i=1
(1 −xi)2)γ/2 →min
(62)
x ∈[0, 10]d
(63)
The curvature of the Pareto front is scalable by means of the
parameter γ. The equation describing the Pareto front reads
y2 = (1 −y1/γ
1
)γ, y1 ∈[0, 1].
(64)
Thus, γ = 1 results in a linear Pareto front, γ < 1 in
concave Pareto fronts, and γ > 1 in convex Pareto fronts. The
Pareto fronts are axis-symmetric to the bi-sector. The extremal
points of this function are given by (y1, y2)T = (0, 1)T and
(y1, y2)T = (1, 0)T. A detailed analysis of this function was
provided by Emmerich [47].
REFERENCES
[1] Y. Jin and J. Branke, “Evolutionary optimization in uncertain environ-
ments - a survey.” IEEE Transactions on Evolutionary Computation,
vol. 9, no. 3, 2005, in print.
[2] J. M. Barthelemy and R. T. Haftka, “Recent advances in approximation
concepts for optimum structural design,” NASA Langley Research
Center, Hampton, VA, Tech. Rep. Tech. Report 104032, 1991.
[3] D. B¨uche, N. N. Schraudolph, and P. Koumoutsakos, “Accelerating
evolutionary algorithms with gaussian process ﬁtness function models,”
IEEE Transactions on Systems, Man and Cybernetics, Special Issue on
Knowledge Extraction and Incorporation in Evolutionary Computation
(Part C), 2005, in print.
[4] J. E. Dennis and V. Torczon, “Managing approximation models in
optimisation,” in Multidisciplinary Design Optimisation: State-of-the-
art, N. M. Alexandrov and N. Hussaini, Eds.
Philadelphia: SIAM,
1997, pp. 330–347.
[5] A. P. Giotis and K. Giannakoglou, “Single- and multi-objective airfoil
design using genetic algorithms and artiﬁcial intelligence,” in EU-
ROGEN 99, Evolutionary Algorithms in Engineering and Computer
Science, 1999.
[6] K. C. Giannakoglou, “Design of optimal aerodynamic shapes using
stochastic optimization methods and computational intelligence,” Inter-
national Review Journal Progress in Aerospace Sciences, vol. 38, pp.
43–76, 2001.
[7] Y. Jin, “A comprehensive survey of ﬁtness approximation in evolutionary
computation,” Soft Computing Journal, vol. 9, no. 1, pp. 3–12, 2005.
[8] K. Giannakoglou, “Designing turbomachinery blades using evolutionary
methods,” in ASME Paper 99-GT-181, 44th ASME Gas Turbine and
Aeroengine Congress, Indianapolis, IN, USA, 1999.
[9] H. Ulmer, F. Streichert, and A. Zell, “Evolution strategies assisted
by gaussian processes with improved pre-selection criterion,” in IEEE
Congress on Evolutionary Computation,CEC 2003, Canberra, Australia,
Dec. 8.-12, 2003.
IEEE-Press, 2003, pp. 692–699.
[10] S. Yesilyurt and A. T. Patera, “Surrogates for numerical simulations; op-
timization of eddy–promoter heat exchangers,” NASA Langley Research
Center, Institute for Computer Applications in Science and Engineering,
Hampton, VA, Tech. Rep. Tech. Report 93-50, 1993.
[11] Y. Jin, M. Olhofer, and B. Sendhoff, “Managing Approximation Models
in Evolutionary Aerodynamic Design Optimisation,” in CEC 2001 Int’l
Conference on Evolutionary Computation, Las Vegas, vol. 1. Piscataway
NJ: IEEE Press, 2001, pp. 592–599.
[12] K. Giannakoglou, A. Giotis, and M. Karakasis, “Low-cost genetic
optimization based on inexact pre-evaluations and the sensitivity analysis
of design parameters,” Inverse Problems in Engineering, no. 9, pp. 389–
412, 2001.
[13] M. El-Beltagy, P. Nair, and A. Keane, “Metamodelling Techniques
for Evolutionary Optimisation of Computationally Expensive Problems:
Promises and Limitations,” in Proc. of GECCO, Int’l Conf. on Genetic
and Evolutionary Computation, Orlando 1999, W. Banzhaf, J. Daida,
A. Eiben, M. Garzon, V. Honavar, M. Jakiela, and R. Smith, Eds.
Morgan Kaufman, 1999, pp. 196–203.
[14] A. Ratle, “Accelerating the convergence of evolutionary algorithms by
ﬁtness landscape approximations,” in Parallel Problem Solving by Na-
ture, ser. LNCS, A. Eiben, T. B¨ack, M. Sch¨onauer, and H.-P. Schwefel,
Eds., vol. V.
Berlin: Springer-Verlag, 1998, pp. 87–96.
[15] M. Emmerich and J. Jakumeit, “Metamodel-assisted optimisation with
constraints: A case study in material process design,” in Int’l Conference
EUROGEN 2003.
Barcelona: CIMNE, 2003.
[16] A. P. Giotis, K. C. Giannakoglou, and J. P´eriaux, “A Reduced-Cost
Multi-Objective Optimization Method based on the Pareto Front Tech-
nique, Neural Networks, and PVM,” in Proc. European Congress on
Computational Methods in Applied Sciences and Engineering (ECCO-
MAS’00), (CD-ROM).
Barcelona: Center for Numerical Methods in
Engineering (CIMNE), 2000.
[17] K. Giannakoglou and M. K. Karakakis, “On the use of surrogate evalua-
tion models in multi-objective evolutionary algorithms,” in ECCOMAS,
2004.
[18] P. K. Nain and K. Deb, “Computationally effective search and opti-
mization procedure using coarse to ﬁne approximations,” in Proc. of the
Congress on Evolutionary Computation CEC 2003, Canberra, Australia,
2003, pp. 2081–2088.
[19] M. Emmerich, A. Giotis, M. ¨Ozdemir, T. B¨ack, and K. Giannakoglou,
“Metamodel-assisted evolution strategies,” in Parallel Problem Solving
from Nature VII, Proc. Int’l Conf., Granada 2002, LNCS2439, J. J. M.
Guerv´os, P. Adamidis, H.-G. Beyer, J. L. F.-V. Mart´ın, and H.-P.
Schwefel, Eds.
Berlin: Springer, 2002, pp. 361–370.
[20] D. G. Krige, “A study of gold and uranium distribution patterns in the
Klerksdorp gold ﬁeld,” Geoexploration, vol. 4, no. 1, pp. 43–53, 1966.
[21] T. J. Santers, N. J. Williams, and W. I. Notz, The Design and Analysis
of Computer Experiments.
Berlin: Springer, 2003.
[22] D. J. C. MacKay, “Introduction to gaussian processes,” in Neural
Networks and Machine Learning, ser. NATO Advanced Study Institute,
C. M. Bishop, Ed.
Berlin: Springer, 1998, vol. 168, pp. 133–165.
[23] R. Adler, The Geometry of Random Fields.
NY: Wiley, 1981.
[24] W. H. Flannery, S. A. S. A. Teukolsky, and W. T. Vetterling, Numerical
Recipes in FORTRAN: The Art of Scientiﬁc Computing.
Cambridge
University Press, 1992, ch. ”Interpolation and Extrapolation.” Ch. 3.
[25] D. E. Myers, “Kriging, cokriging, radial basis functions and the role
of positive deﬁniteness,” Computers Mathematics Applications, vol. 24,
no. 12, pp. 139–148, 1992.
[26] C. Zuppa, “Error estimates for modiﬁed local shepard’s interpolation
formula,” Applied Numerical Mathematics archive, vol. 49, no. 2, pp.
245–259, 2004.
[27] A. Padula, “Interpolation and pseudorandom function generators,” Uni-
versity, Dept. of Computational and Applied Mathematics, Rice Univer-
sity, Houston, TX, Senior Honors Thesis, 2000.


<!-- página 18 -->

18
[28] J. Sacks, W. J. Welch, T. J. Mitchell, and H. P. Wynn, “Design and
analysis of computer experiments,” Statistical Science, vol. 4, no. 4, pp.
409–435, 1989.
[29] J. R. Koehler and A. B. Owen, Handbook on Statistics.
Elsevier-
Science, 1996, vol. 13, ch. Computer Experiments, pp. 239–245.
[30] M. Schonlau, W. Welch, and D. Jones, “Global versus local search in
constrained optimization of computer models,” in New Developments
and Applications in Experimental Design, N. Flournoy, W. Rosenberger,
and W. Wong, Eds.
Hayward, California: Institute of Mathematical
Statistics, 1998, vol. 34, pp. 11–25.
[31] M. Schonlau, “Efﬁcient global optimization of expensive black-box
functions,” Journal of Global Optimization, vol. 13, no. 4, pp. 433–492,
1998.
[32] Y. Ong, P. Nair, and A. Keane, “Evolutionary optimization of compu-
tationally expensive problems via surrogate modeling,” AIAA Journal,
vol. 41, no. 4, pp. 687–696, 2003.
[33] T. B¨ack, D. B. Fogel, and Z. Michalewicz, Eds., Handbook of Evolu-
tionary Computation.
Bristol, UK: IoP Press, 1997.
[34] H.-G. Beyer and H.-P. Schwefel, “Evolution strategies - A comprehen-
sive introduction,” Natural Computing, vol. 1, no. 1, pp. 3–52, 2002.
[35] H.-P.Schwefel, Evolution and Optimum Seeking.
Wiley, N.Y., 1995.
[36] H.-G. Beyer, The Theory of Evolution Strategies, 1st ed., ser. Natural
Computing Series.
Berlin, Heidelberg: Springer-Verlag, 2001.
[37] F. Hoffmeister and J. Sprave, “Problem independent handling of con-
straints by use of metric penalty functions,” in Evolutionary Program-
ming V - Proc. Fifth Annual Conf. Evolutionary Programming (EP’96),
L. J. Fogel, P. J. Angeline, and T. Bck, Eds.
The MIT Press, 1996, pp.
289–294.
[38] K. Deb, A. Pratap, S. Agarwal, and T. Meyarivan, “A fast and elitist
multi-objective genetic algorithm NSGA-II,” KanGAL, Kanpur, India,
Tech. Rep. 2000001, 2000.
[39] K. Deb, Multi-Objective Optimization using Evolutionary Algorithms.
NY: Wiley, 2001.
[40] E. Zitzler, “Evolutionary algorithms for multiobjective optimization,”
Ph.D. dissertation, ETH Zurich, Switzerland, 1998.
[41] D. D. Cox and S. John, “SDO: a statistical method for global
optimization,”
in Multidisciplinary
design optimization
(Hampton,
VA, 1995).
Philadelphia, PA: SIAM, 1997, pp. 315–329. [Online].
Available: citeseer.ist.psu.edu/cox97sdo.html
[42] M. Trosset and V. Torczon, “Numerical optimization using computer
experiments,” Institute for Computer Applications in Science and En-
gineering ICASE TR 9738, NASA Langley Research Center, Hampton
Virginia, Tech. Rep., 1997.
[43] V. Torczon and M. W. Trosset, “Direct search methods: Then and now,”
ICASE, Hampton, VA, Tech. Rep. NASA/CR-2000-210125, ICASE
Report No. 2000-26, 2000.
[44] M. Fleischer, “The measure of Pareto optima: Applications in multi-
objective metaheuristics,” in Evolutionary Multiobjective Optimisation,
Second Int’l Conference, EMO 2003, C. M. F. et al., Ed., 2003, pp.
519–533.
[45] M. Emmerich and B. Naujoks, “Metamodel-assisted multiobjective
optimisation strategies and their application in airfoil design.” in Fifth
International Conf. on Adaptive Design and Manufacture (ACDM 04),
I. Parmee, Ed.
Berlin: Springer, 2004, pp. 249–260.
[46] S. Weinzierl, “Introduction to monte carlo methods,” NIKHEF, Theory
Group, Amsterdam, Technical Report NIKHEF-00-012, 2000.
[47] M. Emmerich, “A rigorous analysis of two bi-criteria problem families
with scalable curvature of the pareto fronts,” Leiden Institute on Ad-
vanced Computer Science, Leiden, NL, Technical Report LIACS TR
2005-05, May 2005.
Acknowledgements: This work was supported by the Deutsche
Forschungsgemeinschaft (DFG) as part of the Collaborative Research
Center ’Computational Intelligence’ (SFB 531). Also, the support
from bilateral Personnel Exchange Programme between Greece and
Germany (IKYDA 2000) is acknowledged.



---

## ANEXO — Conteúdo textual das imagens (OCR)

> Texto extraído por OCR (Apple Vision) das figuras/imagens do PDF — apenas conteúdo NOVO, ausente da camada de texto (labels de eixos, legendas internas, tabelas/equações rasterizadas, slides). OCR de fórmulas é aproximado.

### Página 5
*(figura em y≈282–442)*
- Co-domaih of (f1, f2)

### Página 10
*(figura em y≈183–303)*
- fmar
- emin

### Página 11
*(figura em y≈411–541)*
- $90000000
*(figura em y≈63–193)*
- *779099000000000001
*(figura em y≈237–367)*
- **V9000000000000-

### Página 12
*(figura em y≈59–240)*
- nary of the results on Ackley's function after 1000
- value and the standard deviation of the best four

### Página 13
*(figura em y≈589–719)*
- 1+086**8$86806010*
- Acklev 20-D
*(figura em y≈66–197)*
- Acklev 20-D
*(figura em y≈241–371)*
- Acklev 20-D
*(figura em y≈66–197)*
- 1509
- 0-0 10
- Acklev 20-D
*(figura em y≈415–545)*
- p-004
- Acklev 20-D
*(figura em y≈415–545)*
- 88T: 09
- Acklev 20-D
*(figura em y≈589–719)*
- Acklev 20-D
*(figura em y≈241–371)*
- 9009 00000004
- Acklev 20-D

### Página 14
*(figura em y≈402–533)*
- -0000-01
- 20 909000

### Página 15
*(figura em y≈240–371)*
- 20n20
*(figura em y≈422–553)*
- 20n20
*(figura em y≈59–190)*
- 20n20

### Página 16
*(figura em y≈57–214)*
- MNSGA-1I (Mean)
- 800 F
*(figura em y≈436–545)*
- LOSS
- U ROAD OS
- T Contre
