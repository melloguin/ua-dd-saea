# jin3. Generalizing Surrogate-assisted evolutionary computation

> Fonte (original): jin3. Generalizing Surrogate-assisted evolutionary computation.pdf
> Extraído com pymupdf4llm (texto + tabelas + números; imagens omitidas). Páginas: 53.

---

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

1 

# Generalizing Surrogate-assisted Evolutionary Computation 

Dudy Lim, Yaochu Jin, Yew-Soon Ong, and Bernhard Sendhoff 

**_Abstract_ — Using surrogate models in evolutionary search provides an efficient means of handling today’s complex applications plagued with increasing high computational needs. Recent surrogate-assisted evolutionary frameworks have relied on the use of a variety of different modeling approaches to approximate the complex problem landscape. From these recent studies, one main research issue is with the choice of modeling scheme used, which has been found to affect the performance of evolutionary search significantly. Given that theoretical knowledge available for making a decision on an approximation model** **_a priori_ is very much limited, this paper describes a generalization of surrogateassisted evolutionary frameworks for optimization of problems with objective(s) and constraint(s) that are computationally expensive to evaluate. The generalized evolutionary framework unifies diverse surrogate models synergistically in the evolutionary search. In particular, it focuses on attaining reliable search performance in the surrogate-assisted evolutionary framework by working on two major issues:** **_1)_ to mitigate the** **_‘curse of uncertainty’_ robustly and,** **_2)_ to benefit from the** **_‘bless of uncertainty’_ . The backbone of the generalized framework is a surrogate-assisted memetic algorithm that conducts simultaneous local searches using** **_ensemble_ and** **_smoothing_ surrogate models, with the aims of generating reliable fitness prediction and search improvements simultaneously. Empirical study on commonly used optimization benchmark problems indicates that the generalized framework is capable of attaining reliable, high quality, and efficient performance under a limited computational budget.** 

**_Index Terms_ — Surrogate-assisted evolutionary algorithms, approximation models, metamodels, surrogate models, memetic algorithms, computationally expensive problems.** 

## I. INTRODUCTION 

VER the years, evolutionary algorithms (EAs) have **O** become one of the well-established optimization techniques, especially in the fields of art & design, business & finance, science and engineering. Many successful applications of EAs have been reported, ranging from music composition [1] to financial forecasting [2], aircraft design [3], rainfall prediction [4], and drug design [5]. Although well established as credible and powerful optimization tools, researchers in this area are now facing new challenges of increasing computational needs by today’s applications. For instance, a continuing trend in science and engineering is the use of increasingly 

D. Lim is with the Emerging Research Lab, School of Computer Engineering, Nanyang Technological University, Blk N4, B3b-06, Nanyang Avenue, Singapore 639798 (e-mail: dudy0001@ntu.edu.sg). 

Y. S. Ong is with the Division of Information System, School of Computer Engineering, Nanyang Technological University, Blk N4, 02b-39, Nanyang Avenue, Singapore 639798.(e-mail: asysong@ntu.edu.sg). 

Y. Jin and B. Sendhoff are with the Honda Research Institute Europe GmbH, Carl-Legien-Strasse 30, 63073 Offenbach/Main, Germany (email: {yaochu.jin,bernhard.sendhoff}@honda-ri.de). 

accurate analysis codes in the design and simulation process. Modern Computational Structural Mechanics (CSM), Computational Electro-Magnetics (CEM), Computational Fluid Dynamics (CFD) and first principle simulations have been shown to be reasonably accurate. Such analysis codes play a central role in the design process since they aid designers and scientists in validating new designs and studying the effect of altering key parameters on product and/or system performance. However, such moves may prove to be cost prohibitive or impractical in the evolutionary design optimization process, leading to intractable design cycle times. 

An intuitive way to reduce the search time of evolutionary optimization algorithms when dealing with computationally expensive solver, is the use of high performance computing technologies and/or computationally efficient surrogate models. In recent years, there have been increasing research activities in the design of surrogate-assisted evolutionary frameworks for handling complex optimization problems with computationally expensive objective functions and constraints. In particular, since the modeling and design optimization cycle time is roughly proportional to the number of calls to the computationally expensive solver, many evolutionary frameworks have turned to the deployment of computationally cheap approximation models in the search to replace in part the original solvers [6][7][8]. Using approximation models also known as surrogates or meta-models, the computational burden can be greatly reduced since the efforts required to build the surrogates and to use them are much lower than those in the standard approach that directly couples the EA with the expensive solvers. Among the approximation models, polynomial regression (PR), also known as response surface methodology (RSM), support vector machine (SVM), artificial neural networks (ANNs), radial basis function (RBF), and Gaussian process (GP), also referred to as Kriging or design and analysis of computer experiment (DACE) models, are the most prominent and commonly used [9][10][11]. 

In the context of EA, various approaches for working with computationally expensive problems using surrogate models have been reported. Early techniques include the use of fitness inheritance or imitation [12][13], where the fitness of an individual is defined by either the parents or other individuals previously encountered along the search. Another common approach is to pre-select a subset of individuals that would undergo exact function evaluations while all others are predicted based on surrogate models. Some of the simple schemes introduced are based on random individual selection [14] or selecting the best/most promising individuals based on the predictions made by the surrogate models [7][11][15][16]. Other 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

2 

schemes include identifying some cluster centers [17][18], or uncertain individuals that are predicted to have poor estimates [19] as representatives that will undergo exact function evaluations subsequently. Such forms of model management schemes are termed as ‘ _evolution control_ ’ in [7][20]. An alternative approach adopted in [21] involves the refinement of the surrogate used, from coarse to fine grained models as the search evolves. Online localized surrogate models are also deployed within the local search phase of memetic algorithms (MAs) [8][22]. The synergy of online global and local surrogate in the memetic search was also investigated in [11]. To enhance the prediction accuracy of fitness predictions based on surrogates, the inclusion of gradient information in surrogate building was also studied in [23] and [24], independently. More recently, [25] proposed the use of co-evolution technique to address issues such as level of approximation and accuracy of fitness predictors. 

More recently, the idea of using surrogate to speed-up evolutionary search process has found its way into the field of evolutionary multi-objective optimization (MOO). Many of the schemes introduced in the context of single-objective optimization (SOO) have been extended to their corresponding MOO variants. The Kriging-based surrogate-assisted evolutionary multi-objective algorithm in [26] represents an extension of the efficient global optimization framework [27] introduced for handling SOO problems, while [28] and [29] extended the coarse-to-fine grained approximation and preselection schemes to its MOO variants, respectively. The coevolution of genetic algorithms (GAs) for multiple objectives based on online surrogates was introduced in [30]. After some fixed search intervals, the surrogates produced that represent the different objectives are then exchanged and shared among multiple GAs. In [31], a multi-objective EA is run for a number of iterations on a surrogate model before the model is updated using exact evaluation from some selected points. For greater details on surrogate-assisted EAs for handling optimization problems with computationally expensive objective/constraint functions, the readers are referred to [9] and [32]. 

In spite of the extensive research efforts on this topic, existing surrogate-assisted evolutionary frameworks remains open for further improvement. Jin _et al._ in [14] have shown that existing surrogate-assisted evolutionary frameworks proposed are often flawed by introduction of false optima since the parametric approximation technique used may not be capable of modeling the problem landscapes accurately, thus producing unreliable search. Generally, the _‘curse of dimensionality’_ creates significant difficulties in the construction of accurate surrogate models for fitness prediction. Further, recent studies have shown that the choice of approximation technique used affects the performance of evolutionary searches [33]. On the other hand, it is worth keeping in mind that approximation error in the surrogate model does not always harm. A surrogate model capable of smoothing the multi-modal or noisy landscape of the complex problem may contribute more beneficially to the evolutionary search than one that models the original fitness function accurately. For instance, the study in [44] has emphasized the importance of predicting search improvement 

as opposed to the usual practice of improving only the quality of the surrogate in the context of evolutionary optimization. Based on these recent works, it is worth highlighting the influence of the approximation method used on the performance of any surrogate-assisted evolutionary search. The greatest barrier to further progress is that, with so many approximation techniques available in the literature, it is almost impossible to know which is most relevant for modeling the problem landscape or generating reliable fitness predictions when one has only limited knowledge of its fitness space before the search starts. Moreover, approximation techniques by themselves may model differently on different problem landscapes. Depending on the complexity of a design problem, a single approximation model that may have proven to be successful in an instance might not work so well, or at all, on others. In the field of multidisciplinary optimization, such observations have also been reported [34][35][36][37][38][39][40][41]. In those works, this issue is commonly handled by performing multiple optimization runs, each on different surrogate model or ensemble model. In [34][35][39], a set of surrogate models consisting Kriging, PR, RBF, and weighted average ensemble is used to demonstrate that multiple surrogates can improve robustness of optimization at minimal cost. Similarly, [36] uses PR and RBF surrogate models in the context of multiobjective optimization and shows that each of the models performs better at different region of the Pareto front. Others in [37][38][40][41] resolve this issue by introducing various ensemble model building techniques. It is shown from these works that ensemble models generally outperform most of the individual surrogates. 

The present paper introduces a generalized framework for unifying diverse surrogate models synergistically in the evolutionary search. In contrast to existing efforts, we focus on predicting search improvement in the context of optimization as opposed to solely on improving the prediction quality of the approximation. In particular, we generalize the problem to attain reliable search improvement in surrogate-assisted evolutionary framework as two major goals: _1)_ to mitigate the _‘curse of uncertainty’_ and, _2)_ to benefit from the _‘bless of uncertainty’_ . The _‘curse of uncertainty’_<sup>1</sup> refers to the negative consequences introduced by the approximation error of the surrogate models used. On the other hand, _‘bless of uncertainty’_ refers to the benefits attained by the use of surrogate models. Particularly, we seek for surrogate models that are capable of generating reliable fitness predictions on diverse problems of different landscapes to mitigate the _‘curse of uncertainty’_ on one hand, and on the other hand surrogate models that are capable of smoothing rugged fitness landscapes to prevent the search from getting stuck in local optima [44]. Previous works by Yao _et al._ [42][43] have also confirmed that smoothed landscape of rugged fitness landscape can lead the search to optimum solutions easier than using the exact fitness landscape. 

The rest of this paper is organized as follows. Section II discusses the impacts of uncertainty due to approximation 

1In the present context, the definition of ’uncertainty’ refers to the approximation errors in the fitness function due to the use of surrogate models based on the definitions given in [45]. 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

3 

errors in evolutionary frameworks that employ surrogates. Based on the discussion, Section III provides a generalization of surrogate-assisted evolutionary search for both SOO and MOO subsequently. We summarize the empirical studies on some popular SOO and MOO benchmark problems in Section IV. Finally, Section V concludes this paper. 

## II. IMPACTS OF APPROXIMATION ERRORS IN SURROGATE-ASSISTED EVOLUTIONARY ALGORITHMS 

In this section, we discuss the effects of uncertainty introduced by inaccurate approximation models on Surrogate-Assisted Evolutionary Algorithms (SAEA) search performance. Without loss of generality, here we consider computationally expensive minimization problems under limited computational budget with bound constraints of the following form: 



where i = 1, 2, . . . , d, d is the dimensionality of the search problem, r is the number of objective functions, and x<sup>l</sup> i<sup>,xu</sup> i are the lower and upper bounds of the i<sup>th</sup> dimension of vector x, respectively. 

Note that when more than one objective is involved for approximation, there are two commonly adopted strategies, i.e. _1)_ one approximation model per objective function, and _2)_ one approximation model for an aggregated (linear or nonlinear combination) objective function, faggr(x). In this paper, we consider the second strategy. Since in single-objective context, faggr(x) = f (x) = f1(x), the term f (x) might be used interchangeably to faggr(x) for brevity purpose when only single-objective context is considered. 

If faggr(x) denotes the original function and the approximated function is f<sup>ˆ</sup> aggr(x), the approximation errors at any solution vector x is e(x) , i.e., the uncertainty introduced by the surrogate at x, may then be defined as: 



Here, we highlight the negative and positive impacts introduced by the approximation inaccuracies of the surrogates on SAEA search [44]. The negative impact or otherwise known as the ‘ _curse of uncertainty_ ’ on SAEA search can be briefly defined as the phenomenon where the inaccuracies of the surrogates used results in the SAEA search to stall or converge to false optimum. To illustrate the ‘ _curse_ ’ effect, we refer to Fig. 1(a) where the SAEA is likely to converge to the false optimum of the spline interpolation model due to inaccuracy. On the other hand, the positive impact, i.e., the ‘ _bless of uncertainty_ ’ in SAEA materializes when the use of surrogate(s) brings about greater search improvements over the use of original exact objective/fitness function. For instance, the surrogate can help to traverse the search across valleys and hills of local optima by smoothing the ruggedness/multimodality of the problem landscape. To illustrate the blessing effect, we refer to the example in Fig. 1(b), where a low order polynomial regression scheme is used to approximate the exact objective function. Due to the smoothing effect of 

the polynomial surrogate, the search leads to an improved solution that is unlikely to be attained even if the exact objective function is used. Hence, the ‘ _bless of uncertainty_ ’ brings about possible acceleration in the search. Besides a faster convergence, recent study in [32] revealed that the ‘ _bless of uncertainty_ ’ in SAEA also exists in the form of improving evolutionary search diversity through the use of surrogate model. 

Next, to illustrate ‘ _curse and bless of uncertainty_ ’ in the context of multi-objective optimization, we refer to the examples in Figs. 2(a) and 2(b). Fig. 2(a) depicts the effect of ‘ _curse of uncertainty_ ’ in MOEA search due to the presence of inaccurate surrogate models. In Fig. 2(a), the surrogateassisted MOEA search is observed to be evolving towards poor non-dominated solutions in comparison to that based on exact fitness functions. Moreover, those labeled as x1 and x2 in Fig. 2(a) suggest that some solutions might stall, while others fail to converge optimally. On the other hand, Fig. 2(b) illustrates the presence of ‘ _bless of uncertainty_ ’ where the errors in the surrogate used is observed to improve the MO evolutionary search in both convergence and diversity measures. Particularly, some improved solutions of the surrogateassisted search is shown to dominate at least one of its initial solutions, while others such as x3 and x4 are newly found non-dominated solutions. 

## III. GENERALIZING SURROGATE-ASSISTED EVOLUTIONARY SEARCH 

In this section, we present a generalization of surrogateassisted evolutionary frameworks for optimization of problems with objective(s) and constraint(s) that are computationally expensive to evaluate. The generalized framework illustrated here for unifying diverse approximation concept synergistically is a surrogate-assisted memetic algorithm that conducts simultaneous local searches on separate _ensemble_ and _smoothing_ surrogate models. MAs are population-based meta-heuristic search methods that are inspired by Darwinian principles of natural evolution and Dawkins notion of a meme defined as a unit of cultural evolution capable of local refinements [46]<sup>2</sup> . For example, the brief outline of a traditional MA is provided in Algorithm 1. 

In the generalized framework, we introduce the idea of employing online local ensemble surrogate models constructed from diverse approximation concepts using data points that lie in the vicinity of an initial guess. The surrogate or approximation models are then used to replace the expensive function evaluations performed in the local search phase. The improved solution generated by the local search procedure then replaces the genotype and/or fitness of the original individual<sup>3</sup> . 

> 2Note that the rationale behind using a memetic framework over a traditional evolutionary framework is multi-fold [46][50]. First, we aim to exploit MAs’ capability of locating the local and global optima efficiently. Second, a memetic model of adaptation exhibits the plasticity of individuals that a pure genetic model fails to capture. Further, by limiting the use of surrogate models within the local search procedures, the global convergence property of EAs can be ensured. For a greater exposition of local meta-heuristics in optimization, the reader is referred to [47][48][49]. 

> 3There are two basic replacement strategies in MAs [50]: 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

4 

## **Algorithm 1** Memetic Algorithm (for SOO) 

|1:|**Initialization**: Generate and evaluate a population of design<br>vectors.|
|---|---|
|2: <br>3:|**while** computational budget is not exhausted **do**<br>Apply evolutionary operators (selection, crossover, mutation)<br>to create a new population.|
|4:||
|5:<br>6:|/∗∗∗∗**Local Search Phase** ∗∗∗∗/|
|7:|**for** each individual x in current population **do**<br>|
|8:|• Apply local search to fnd an improved solution, xopt.|
|9:|• Perform replacement using Lamarckian learning, i.e.|
|10:|**if** f(xopt)< f(x) **then**|
|11:|x=xopt|
|12:|**end if**|
|13:|**end for**|
|14:||
|15:<br>16:<br>17:|/∗∗**End of Local Search Phase** ∗∗/<br> **end while**|



## _A. Ensemble Model_ 

To mitigate the _‘curse of uncertainty’_ due to the effect of using imperfect surrogate models, we seek for surrogate models that are capable of generating reliable fitness predictions on diverse problems. In particular, since it is almost impossible to know in advance which approximation technique best suits the optimization problem at hand, we consider a synergy of diverse approximation methods through the use of ensemble models to generate reliable accurate predictions across problems of differing problem landscapes [18][51][37], as opposed to single surrogate models created by specific approximation scheme that may not be appropriate for the problem at hand. In what follows, we consider online local weighted average ensembles. For instance, in the single-objective context, the predicted ensemble output of f (x) is formulated as: 



ˆ ˆ where fens(x) and fi(x) are the fitness prediction made by the ensemble and i<sup>th</sup> surrogate model, respectively. The same formulation applies in the multi-objective context where faggr(x) is considered. ci is the weight coefficient associated with the i<sup>th</sup> surrogate model. A model can be assigned a larger weight if it is found or deemed to be more accurate. Hence, the weighting function becomes: 



- _Lamarckian learning_ forces the genotype to the result of improvement in local search by placing the locally improved individual back into the population to compete for reproductive opportunities. 

- _Baldwinian learning_ only alters the of the individuals and the improved genotype is not encoded back into the population. 

For the sake of brevity, we consider Lamarckian learning in this paper. 

where εj is the error measurement for the j<sup>th</sup> surrogate model. Here, the root mean square error (rmse) is used as the error measurement. The rmse of each surrogate model is then of the form: 



where m is the number of data samples compared, e(xi) is the error of prediction for data point xi, as shown in Equation (2). For greater details on other ensemble model building techniques, interested readers are referred to [37][38][40][41][51]. 

## _B. Landscape Smoothing Model_ 

Meanwhile, to from the _‘bless of uncertainty’_ , smoothing techniques including global convex underestimation, tunneling and filling methods are some appropriate alternatives [52] that may be used. Given a problem landscape, smoothing methods transform the function into one with noticeably fewer minima, thus speeding up the evolutionary search. In the generalized framework, global convex underestimation is used for successive smoothing of the problem landscape within the local search phase which is realized through low-order polynomial regression (PR). Besides the generalization property of PR models on rugged landscape, the low computational costs incurred makes them very efficient as online surrogate models. Note that the PR model may be used in both ensemble and the smoothing models, hence only a one-time model building cost is involved. 

## _C. GSM Framework for Single-Objective Optimization_ 

In this subsection, we describe the generalized surrogate memetic framework for single-objective optimization. A brief outline of the generalized surrogate single-objective memetic algorithm (GS-SOMA) is presented in Algorithm 2. Note that the difference between the GS-SOMA and a traditional MA lies in the local search phase of the algorithms. 

GS-SOMA begins with the initialization of a population of design points. During the database building phase, the search operates like a traditional evolutionary algorithm based on the original exact fitness function for some initial Gdb generations. Up to this stage, no form of surrogates are used, and all exact fitness function evaluations made are archived in a central database. Subsequently, the algorithm proceeds into the local search phase. For each individual x, n online surrogates that model the fitness function are created dynamically using m training data points, which lie in the vicinity of x, extracted from the archived database of previously evaluated design points. From the n surrogates, an ensemble model is built. From here, two separate local searches are conducted on _1)_ M1, the ensemble of n surrogate models, and _2)_ M2, a low-order PR model. If improved solutions are achieved, GS-SOMA proceeds with the individual replacement scheme. Since we adopt the Lamarckian scheme here, the genotype/phenotype of the initial individual is then replaced by the higher quality solutions among the two that are locally improved based on M1 and M2, i.e., x<sup>1</sup> opt<sup>orx2</sup> opt<sup>.The</sup> search cycle is then repeated until the allowed maximum computational budget is exhausted. 

5 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

## **Algorithm 2** Generalized Surrogate Single-Objective Memetic Algorithm (GS-SOMA) 

|1:|**initialization**: Generate and evaluate a database containing a<br>population of designs, archive all exact evaluations into the<br>database.|
|---|---|
|2:|**while** computational budget is not exhausted **do**|
|3:|**if** generation count < database building phase (Gdb) **then**<br>|
|4:|Evolve the population using exact ftness function evalua-<br>tions, archive all exact evaluations into the database.|
|5:|**else**|
|6:|Apply evolutionary operators (selection, crossover, muta-<br>tion) to create a new population.|
|7:||
|8:|/∗∗∗∗**Local Search Phase** ∗∗∗∗/|
|9:||
|10:|**for** each individual x in the population **do**|
|11:|• Find m nearest points to x in database as training<br>points for surrogate models.<br>|
|12:|• Build model-1: M1, as an ensemble of all M <sup>′</sup><br>j <sup>for</sup><br>j = 1, . . . , nwherenis the number of surrogate models<br>used.|
|13:|• Build model-2: M2, which is a low-order PR model.<br>|
|14:|• Apply local search in M1 to arrive at x<sup>1</sup><br>opt<sup>, and M</sup>2 <sup>to</sup><br>arrive at x<sup>2</sup><br>opt<sup>.</sup>|
|15:|• Replace x with the locally improved solution, i.e.<br><br>|
|16:|**if** f(x<sup>1</sup><br>opt<sup>) < f(x2</sup><br>opt<sup>)</sup> <sup>**then**</sup><br>|
|17:|x=x<sup>1</sup><br>opt|
|18:|**else**<br>|
|19:|x=x<sup>2</sup><br>opt|
|20:|**end if**|
|21:|• Archive all new exact function evaluations into the<br>database.|
|22:|**end for**|
|23:||
|24:<br>25:|/∗∗**End of Local Search Phase** ∗∗/|
|26:|**end if**|
|27:|**end while**|



## _D. GSM Framework for Multi-Objective Optimization_ 

Next, we describe the Generalized Surrogate Memetic framework in the context of multi-objective optimization (MOO). In MOO, a solution x<sup>(1)</sup> is said to dominate solution x<sup>(2)</sup> in the objective space, i.e., x<sup>(1)</sup> ⪯ x<sup>(2)</sup> if the following two conditions hold: 

- x<sup>(1)</sup> is no worse than x<sup>(2)</sup> on all objectives or fj(x<sup>(1)</sup> ) ≤ fj(x<sup>(2)</sup> ) for all j = 1, 2, . . . , r. 

- x<sup>(1)</sup> is strictly better than x<sup>(2)</sup> on at least one objective, or fj(x<sup>(1)</sup> ) < fj(x<sup>(2)</sup> ) for at least one j ∈ 1, 2, . . . , r 

If set P is the entire feasible search space, the non-dominated set P<sup>∗</sup> is labeled as the _Pareto-optimal set_ . Any two solutions in P<sup>∗</sup> must non-dominate each other, i.e. x<sup>(1)</sup> ∼ x<sup>(2)</sup> . On the other hand, Pareto front (PF<sup>∗</sup> ) is the image of the Pareto-optimal set in objective space. The brief outline of a typical Multi-Objective Memetic Algorithm (MOMA) using weighting (scalarization) technique [58][59][60] is illustrated in Algorithm 3. In contrast, the studied GSM framework for multi-objective optimization (GS-MOMA) is outlined in Algorithm 4. Note that the key differences of the two algorithms lie in the local search phase and selection pool forming phase. 

GS-MOMA begins with the population initialization phase and evolutionary search based on exact fitness function for a 

## **Algorithm 3** Multi-Objective Memetic Algorithm 

|1: <br>|**initialization**: Generate and evaluate a population of design<br>vectors.<br>|
|---|---|
|2:|**while** computational budget is not exhausted **do**<br>|
|3:|Apply MO evolutionary operators (selection, crossover, muta-<br>tion) to create a new population.|
|4:||
|5:<br>6:|/∗∗∗∗**Local Search Phase** ∗∗∗∗/|
|7:|**for** each individual x in the population **do**<br>|
|8:|•Generate a random weight vectorw = (w1, w2, . . . , wr),<br>Pr<br>i=1 <sup>wi = 1 where r is the number of objectives.</sup><br> <br>|
|9:|• Apply local search in faggr = <sup>Pr</sup><br>i=1 <sup>wifi(x) to fnd an</sup><br>improved solution, x<sup>opt</sup>.|
|10:|• Perform Lamarckian learning, i.e.<br>|
|11:|**if** faggr(xopt)< faggr(x) **then**|
|12:|x=xopt<br>|
|13:|**end if**<br>|
|14:|**end for**|
|15:||
|16:<br>17:|/∗∗**End of Local Search Phase** ∗∗/|



### 18: **end while** 

**Algorithm 4** Generalized Surrogate Multi-objective Memetic Algorithm (GS-MOMA) 

- 1: **initialization** : Generate and evaluate an initial population with Npop individuals, archive all exact evaluations into a database. 

- 2: **while** computational budget is not exhausted **do** 3: **if** generation count < database building phase (Gdb) **then** 4: Evolve the population using exact fitness function evaluations, archive all exact evaluations into the database. 

- 5: **else** 6: Generate the offspring population , Po using MO evolutionary operators (selection, crossover, mutation) on the selection pool. 

- 7: 8: / ∗∗∗∗ **Local Search Phase** ∗∗∗∗ / 9: 

- 10: Initialize the learning archive, Al to empty state. 11: **for** each individual x in the offspring population **do** 12: • Generate a random weight vector w = (w1, w2, . . . , wr),<sup>Pr</sup> i=1<sup>wi</sup> = 1 where r is the number of objectives. 

- 13: • Find m nearest points to x in database as training points for surrogate models. 

- 14: • Build model-1: M1, as an ensemble of all Mj<sup>′for</sup> j = 1, . . . , n where n is the number of surrogate models used, of faggr =<sup>Pr</sup> i=1<sup>wifi(x)</sup> 

- 15: • Build model-2: M2, which is a low-order PR model, of faggr =<sup>Pr</sup> i=1<sup>wifi(x)</sup> 

- 16: • Apply local search in M1 to arrive at x<sup>1</sup> opt<sup>,andM</sup> 2<sup>to</sup> arrive at x<sup>2</sup> opt 

- 17: • Replace&Archive( x, x<sup>1</sup> opt<sup>,x2</sup> opt<sup>,A</sup> l<sup>)</sup> 18: **end for** 

- 19: 20: / ∗∗ **End of Local Search Phase** ∗∗ / 21: 

- 22: 23: / ∗∗∗∗ **Selection pool forming** ∗∗∗∗ / 24: 25: Form selection pool, Ps = Pc S Po S Al. 26: 27: / ∗∗ **End of selection pool forming** ∗∗ / 28: 29: **end if** 30: **end while** 

6 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

**Algorithm 5** Procedure Replace&Archive(x, x<sup>1</sup> opt<sup>, x2</sup> opt<sup>, Al)</sup> 



number of early generations, Gdb, before entering the local search phase. In the local search phase, independent local searches are conducted on _1)_ M1, the ensemble of n surrogate models, and _2)_ M2, the smoothing low-order PR model on each individual of the generated offspring population. For the sake of brevity, the core distinguishing feature of GS-MOMA can be noted in line 17 of Algorithm 4, i.e. the existence of the Replace&Archive procedure. 

The Replace&Archive procedure performs replacements based on domination between the original offspring and the two local optima found. The original offspring will only be replaced by one dominating optimum found. Any other local optima are then saved into the learning archive, Al. Note that the result of GS-MOMA’s local searches is either xopt ⪯ x or xopt ∼ x. Otherwise, there is no improvement to the original offspring, and hence we get xopt == x. 

Based on the procedure in Algorithm 5, the possible local search outcomes and corresponding actions taken by the scheme are summarized in Table I. Note that there exist 6 possible actions to be taken by GS-MOMA which are summarized as follows: 

- Replacement is performed once (e.g. Fig. 3a). 

- Two subsequent replacements are performed (e.g. Fig. 3b). 

- Both replacement and archiving are performed (e.g. Fig. 3c). 

- Archiving is performed once (e.g. Fig. 3d). 

- Archiving is performed twice (e.g. Fig. 3e). 

- Neither replacement nor archiving is performed (e.g. Fig. 3f). 

At the end of each GS-MOMA generation, Al is combined with the current parent population, Pc, and the offspring population, Po to form the entire pool of individuals, Ps 

that will then undergo the MOEA selection mechanism, i.e., Ps = Pc � Po � Al. From here, the process described repeats until the maximum computational budget of the GS-MOMA is exhausted. 

## _E. Local Search Scheme_ 

In the GSM framework for SO/MOO, a trust-regionregulated search strategy is utilized to ensure convergence to some local optimum or the global optimum of the exact computationally expensive fitness function [61][8][53], even though surrogate models are deployed in the local search. For each individual in the GS-SO/MOMA population, the local search (refer to line 14 of Algorithm 2 and line 16 of Algorithm 4) proceeds with a sequence of trust-region subproblems of the form 



where k = 0, 1, 2, . . . , kmax, f<sup>ˆ</sup> (x) is the approximation function corresponding to the objective function f (x). Meanwhile, x<sup>k</sup> c<sup>, s, and Ωkrepresent the initial guess (current best solution)</sup> at iteration k, an arbitrary step, and the trust-region radius at iteration k, respectively. In our experiments, the Sequential Quadratic Programming (SQP) [54] is used to minimize the sequence of subproblems on the approximated landscape. 

During the local search, the initial trust-region radius Ω is initialized based on the minimum and maximum values of the m design points used to construct the surrogate model (refer to line 11 of Algorithm 2 and line 13 of Algorithm 4). The trust-region radius for iteration k, i.e. Ω<sup>k</sup> is updated based on a measure which indicates the accuracy of the surrogate model at the k<sup>th</sup> local optimum, x<sup>k</sup> opt<sup>.Thismeasure,ρk,</sup> provides a measure of the actual versus predicted change in the exact fitness function values at the k<sup>th</sup> local optimum and is calculated as: 



The value of ρ<sup>k</sup> is then used to update the trust-region radius as follows [61]: 



where C1, C2, C3, and C4 are constants. Typically, C1 ∈ (0, 1) and C4 ≥ 1 for the scheme to work efficiently. From experience, we set C1 = 0.25, C2 = 0.25, C3 = 0.75, and C4 = 2, if ||x<sup>k</sup> opt<sup>−x</sup> c<sup>k||∞= Ωkor C4= 1, if ||xk</sup> opt<sup>−x</sup> c<sup>k||∞<</sup> Ω<sup>k</sup> . 

The trust-region radius for the next iteration, Ω<sup>k+1</sup> , is reduced if the accuracy of the surrogate, measured by ρ<sup>k</sup> is low. On the other hand, Ω<sup>k</sup> is doubled if the surrogate is found to be accurate and the k<sup>th</sup> local optimum, x<sup>k</sup> opt<sup>,liesonthe</sup> trust-region bounds. Otherwise the trust-region radius remains unchanged. 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

7 

The initial guess of the optimum at iteration k +1 becomes 



The trust-region process for an individual terminates when the termination condition is satisfied. For instance, this termination condition could be when the trust-region radius Ω approaches ε, where ε represents some small trust-region radius, or when a maximum number of iteration kterm is reached. 

## IV. EMPIRICAL STUDY 

In this section, we present an empirical study on the GSM framework for solving single and multi-objective optimization problems. In the present study, we considered a diverse set of exact interpolating and generalizing approximation techniques for constructing the local surrogate models, i.e., M1 and M2. These include the interpolating Kriging/Gaussian process (GP), interpolating linear spline radial basis function (RBF) and 2<sup>nd</sup> order polynomial regression (PR). For greater details on GP, PR, and RBF, the reader is referred to [55][56][57] and Appendix I. 

## _A. Parameters of GSM Framework_ 

ters of the GSM framework. Apart from the parameters of the underlying SO/MOEA, the generalized framework has three additional user-specified parameters: m, Gdb and kterm. 

of the m data points used for model building, the size of nearest neighboring points used (based on Euclidean distance) is defined by d+(d+1)(d+2)/2, where d is the dimensionality of the optimization problem. It is worth noting that the complexity for identifying these m points is negligible compared to the cost of surrogate model building. Moreover, since our emphasis here is with regard to a framework that is tailored for solving computationally expensive problems, i.e., problems that may cost from minutes to hours of computational time per evaluation, such overheads are considered to be insignificant. From these m data points, as many as (d +1)(d +2)/2 among them<sup>4</sup> are chosen uniformly as the training data for building the surrogates, the remaining data points then form the set for validating the prediction quality of the surrogate. 

Parameter Gdb, on the other hand, the period of the database building phase (refer to lines 3-5 in Algorithms 2 and 4) before the core operation of the GSM framework begins to take effect. Hence Gdb can be adapted for different optimization problems according to the fulfillment on the requirement of parameter m. The lower bound of Gdb is defined by the period to acquire a minimum of m data points for construction of reliable surrogate models. 

Theoretically, the trust-region local search scheme terminates when the trust-region radius, Ω approaches ε, where ε represents some very small value for termination condition (refer to Section III-E). Nevertheless, for practical reason, 

> 4This amount corresponds to the minimum number of data points required for building quadratic regression models. 

under limited computational budget, it is more appropriate to derive a suitable value for kterm as the termination condition in the trust-region local search. In what follows, we present a theoretical bound for kterm: 



Since C1 ∈ (0, 1) → log C1 < 0, we arrive at: 



Similarly, the maximum number of trust-region iterations in the local search, i.e., kmax, is estimated by: 



Note that Nsucc<sup>maxisthemaximumnumberofsuccessfulitera-</sup> tions, while Ω<sup>1</sup> min<sup>andΩ1</sup> max<sup>arethelowerandupperbounds</sup> of the initial trust-region radius. In effect, the bounds for kterm as the termination condition can be derived as: 



In the trust-region-regulated local search, Ω<sup>1</sup> depends on the local region of interest where the initial m nearest neighbors are located. Hence it is not possible to define this term precisely for any new optimization problem. For instance, if Ω<sup>1</sup> min<sup>≈10εandC1= 0.25,wearriveat:</sup> 



As opposed to using kterm = 1 which translates to a single iteration local search, a minimum value of kterm ≥ 2 is more practical to allow the mechanisms of the trust-region-regulated local search to take effect. 

## _B. Single-Objective Optimization_ 

Empirical study on the GS-SOMA is performed using 10 benchmark problems (F1-F10) reported in [62][63] and summarized here in Table II. More detailed description of the problems are also provided in Appendix II. They consist of problems with diverse properties in terms of separability, multi-modality, and continuity. 

In this paper, all the benchmark problems are with a dimensionality of d = 30 for SOO. Performance comparisons are then made between the GA, SS-SOMA-GP, SS-SOMA-PR, SS-SOMA-RBF, SS-SOMA-Perfect, and GSSOMA (refer to Table III for the definition of the algorithms investigated here). Note that to facilitate a fair comparison, the surrogate memetic variants are built on top of the same GA used in the study, which ensures that any improvements observed is a direct contribution of the surrogate framework 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

8 

considered. SS-SOMA- _XXX_ refers to the different surrogateassisted single-objective MA variants, each with a unique approximation method used to generate the surrogate model. For instance, _XXX_ in SS-SOMA- _XXX_ refers to GP, PR, or RBF. On the other hand, SS-SOMA-Perfect refers to an SSSOMA that employs an imaginary approximation technique that generates error-free surrogates<sup>5</sup> , i.e., RMSE = 0. Hence the notion of curse or bless of uncertainty does not exist in the SS-SOMA-Perfect search. As such, any SS-SOMA- _XXX_ that under/out-perform SS-SOMA-Perfect is clearly attributed to the effects of curse and bless of uncertainty, respectively. Last but not least, GS-SOMA refers to the Generalized Surrogate framework for single-objective optimization. The common parameter settings of the algorithms used in the present experimental study are summarized in Table IV. 

_1)_ **_Experimental Results_** _:_ In Tables V-XIV, the detailed statistical results of 20 independent runs for SS-SOMAs, GSSOMA, and GA are presented. The GS-SOMA and best performing SS-SOMA are highlighted in the tables. Note that none of the SS-SOMAs always dominates in performance on all 10 benchmark problems. This makes good sense since the performance of any surrogate-assisted evolutionary search would depend on the match between the characteristics of the problem landscape and approximation scheme used. For instance, in the tables, it is shown that SS-SOMA-PR serves to be best suited for F1, F5, and F9 since it outperforms all other algorithms on these problems. Similarly, this also applies to SS-SOMA-GP which excels on F3. On the other hand, SS-SOMA-RBF, though not superior, performs relatively well on F3, F4, F7, and F8. Moreover, it is worth noting that the SS-SOMAs are observed to have performed much poorly on several occasions. For instance, SS-SOMA-PR fares badly on F3, F4, F7, and F8. The same is true for SS-SOMA-GP on F1, F4-F8, and F10, and SS-SOMA-RBF on F1, F2, F5, F6, F9, and F10. 

On the other hand, the results in Tables V-XIV, indicate that GS-SOMA consistently performs well on all the benchmark problems. The _t-test_ results, i.e., at 95% confidence level, for the different algorithms as reported in Table XV confirms that GS-SOMA outperforms or is competitive to the SS-SOMAs on 43/50 cases. On the remaining 7 cases, GS-SOMA also displays solution qualities close to that of the superior SSSOMA, see the highlighted results in Tables V-XIV. Note that this is a significant achievement considering that no _a priori_ knowledge is available to select an appropriate surrogate modeling scheme for the problems considered. This highlights the reliability of the generalized framework. 

The search convergence trends of GS-SOMA, SS-SOMAAV, and SS-SOMA-Perfect are also plotted in Fig. 4. Note that SS-SOMA-AV represents the estimated performance one might expect to get when an approximation technique is randomly chosen for use. Hence, SS-SOMA-AV is generated from the average of the results obtained by all 3 SS-SOMAs, 

> 5An error-free surrogate model can be realized by using exact fitness function in the portion of SS-SOMA where a surrogate model should be used, but the incurred fitness evaluation is counted only as many as in SS-SOMA. 

i.e. SS-SOMA-GP, SS-SOMA-PR, and SS-SOMA-RBF. It is evident from the search convergence trends that GS-SOMA is superior over SS-SOMA-AV on the 10 benchmark problems. This indicates that the generalized framework is more reliable when one has no knowledge about the suitability of the approximation scheme for the problem at hand. 

_2)_ **_Analyzing the Generalized Evolutionary Framework in Single-Objective Optimization_** _:_ To gain a better understanding of the generalized framework, we further analyze the reliability and effectiveness of the ensemble (M1) and smoothing (M2) surrogate models in contributing to the evolutionary search. 

To facilitate the analysis, the normalized root mean square errors (N-RMSE) of fitness predictions based on the ensemble surrogate model, i.e., M1 in GS-SOMA search, for the benchmark problems are presented in Fig. 5. The normalized RMSE of model i is determined as follows: 



where n is the total approximation methods used in shaping the ensemble. From this figure, the consistently low N-RMSE of the ensemble model generated in the GS-SOMA search across all benchmark problems, demonstrates the high reliability of the fitness prediction generated by M1 across the different optimization problems over any single surrogates. 

Further, it is worth noting that the use of M2 contributes to the fitness improvement in GS-SOMA, which confirms the possible benefits of bless of uncertainty in surrogate model. The normalized average fitness improvement of the local searches contributed via the use of M1 (ImpM 1) and M2 (ImpM 2) during the GS-SOMA searches are summarized in Fig. 6 and is defined by: 



ImpM 1 is the total improvements attained by local refinements, i.e., through Lamarckian learning, when f (x<sup>1</sup> opt<sup>) <</sup> f (x<sup>2</sup> opt<sup>), while ImpM2is the total fitness improvements when</sup> f (x<sup>2</sup> opt<sup>) < f(x1</sup> opt<sup>).</sup> 

From the statistical results given in Fig. 6, it is notable that M1 and M2 surrogates have contributed to the surrogateassisted memetic search in their unique ways. This provides a means for explaining the results that were obtained in Fig. 4 and Tables V-XIV. In particular, the reason for that all surrogate-assisted SOMAs outperform SS-SOMA-Perfect on F1 (Ackley) suggests the presence of _‘bless of uncertainty’_ through the use of surrogate(s), since the notion of curse or bless of uncertainty cannot exist in the latter. Further, the fact that SS-SOMA-PR is the most superior on F1 (Ackley) highlights the strength of the PR model in contributing to the search via smoothing the rugged landscape of the Ackley function. This hypothesis is clearly supported by the large portion of fitness improvements that are contributed by M 2 (i.e., the PR model) on F1, see Fig. 6. On the other hand, neither SS-SOMAs nor GS-SOMA manage to outperform the SS-SOMA-Perfect on F3(Rosenbrock), suggesting the 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

9 

presence of _‘curse of uncertainty’_ due to the surrogate(s). Further, the results in F3 of Fig. 6 also indicate that M2 (i.e., the smoothing PR model) did not contribute significantly to the search since the problem landscape of this function is originally smooth. Rather, the use of ensemble model in GS-SOMA had contributed to reliable fitness improvement on F3(Rosenbrock) by generating reliable prediction accuracy. On the other test problems, both M1 and M2 surrogates were shown to contribute significantly to GS-SOMA in their own unique ways. 

## _C. Multi-Objective Optimization_ 

In this subsection, we present the empirical study of the GSMOMA on 6 moderate to high dimensional MO benchmark problems, labeled here as MF1-MF6 [64]. The MO benchmark problems used in the study are summarized in Table XVI. 

Performance comparisons are then made between the standard non-dominated sorting genetic algorithm-II (NSGAII) [65] and variants of MOMA. For fair comparison, we compare GS-MOMA with several SS-MOMAs and the NSGAII since the formers are demonstrated with NSGA-II as the baseline by building on top of it. Hence, all algorithms compared inherit the same evolutionary operators as the NSGAII used in our experiment. In SS-MOMAs, an offspring will be replaced in the spirit of Lamarckian learning during local search if its aggregated fitness function is found to be better than the original offspring. Similarly, SS-MOMA-Perfect is introduced here to assess the effects of approximation error on surrogate-assisted evolutionary search performance. For the sake of brevity, the notations and definitions of the MO algorithms studied are tabulated in Table XVII while the common parameter settings of the MO algorithms used in the experimental study are defined in Table XVIII<sup>6</sup> . 

Many performance indicators exists for assessing the performance of MOEAs, such as those summarized in [66][67]. Here, the following three performance indicators are used, i.e., 

- **Generational Distance (GD)** [68][69]: This measurement indicates the gap between the true Pareto front (PF<sup>∗</sup> ) and the evolved Pareto front (PF ). Mathematically, it can be formulated as: 



where nP F is the number of members in PF , di is the Euclidean distance (in objective space) between member i of PF and its nearest member in PF<sup>∗</sup> . A low value of GD is more desirable since it reflects a good convergence to the true Pareto fronts. 

- **Maximum Spread (MS)** [70]: It is used to measure how well the true Pareto front (PF<sup>∗</sup> ) is covered by the evolved Pareto front (PF ). The MS measurement used in this 

> 6Since MF3 and MF4 have higher dimensionality, i.e. d = 50, greater initial database size is required. For these cases, Gdb is set to 20. 

paper is formulated as: 



where fi<sup>max</sup> and fi<sup>min</sup> are the maximum and minimum of the i<sup>th</sup> objective in the evolved PF, respectively. Fi<sup>max</sup> and Fi<sup>min</sup> are the maximum and minimum of the i<sup>th</sup> objective in PF<sup>∗</sup> , respectively. Higher value of MS reflects a larger area of PF<sup>∗</sup> covered by PF , which is desirable. 

- **Hypervolume Ratio (HR)** [69]: This indicates the ratio between the hyperarea or hypervolume (H) [71] dominated by the evolved PF and PF<sup>∗</sup> , where HR is defined as: 



Here, vi denotes the hypercube constructed from member i of a particular Pareto front and the reference point. A HR value close to 1 indicates that the evolved Pareto front is quite close to the true Pareto front, in both convergence and spread of solutions. 

_1)_ **_Experimental Results_** _:_ The obtained Pareto fronts of the benchmark problems for 20 independent runs are combined and depicted in Figs. 9-14. The respective performance metrics are then summarized in Figs. 15-20. From these results, all surrogate-assisted multi-objective evolutionary algorithms, i.e., SS-MOMAs and GS-MOMA, are shown to outperform the standard NSGA-II on MF1, MF2, MF5, and MF6. MF6 (ZDT4) is generally regarded as a challenging problem and hence commonly used by many in the literature. Here, we validate our results on ZDT4 against those obtained by Deb _et al._ in [28]. While [28] reported to solve ZDT4 with from 21781 to 22730 exact function evaluations with an achieved spread measure<sup>7</sup> of 0.332 to 0.422, GS-MOMA requires only 20000 exact evaluations at a competitive spread measure of 0.410 ± 0.046. On MF3 and MF4, some SS-MOMAs perform competitively or slightly poorer than NSGA-II (see Figs. 11(d) and 12(d)). On the other hand, GS-MOMA searches more efficiently than all the SS-MOMA variants and NSGA-II on the 6 benchmark problems considered. Note that GS-MOMA also outperforms the SS-MOMA-Perfect on a majority of the MOO benchmarks with respect to all three performance metrics, thus suggesting the positive synergy of the ensemble and smoothing surrogate models in the GSM framework. 

_2)_ **_Analyzing the Generalized Evolutionary Framework in Multi-Objective Optimization_** _:_ To arrive at better understanding of the generalized framework in the context of multi-objective optimization, we analyze next the reliability and effectiveness of the ensemble (M1) and smoothing (M2) 

> 7The spread metric [72] considers the distance between two extreme ends of Pareto front as well as the uniformity of distribution for solutions between the two extremes. This metric may be used for measuring the diversity of converged Pareto fronts. Note that a lower spread metric is desirable. 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

10 

surrogate models in contributing to evolutionary search. 

The N-RMSE, i..e, see Equation (19), of predictions based on GP, PR, RBF, or ensemble in GS-MOMA is summarized in Fig. 7. From the results, the ensemble model, M1, is shown to arrive at low N-RMSE on all the multi-objective test problems considered, which is consistent with observations obtained in the single-objective context. M1 generates high reliability predictions in comparison to the other single surrogate model counterparts, i.e., GP, PR or RBF. 

Besides N-RMSE, the _solution archiving to replacement ratio_ , labeled here as Γ, of the GS-MOMA search is also reported in Figure 8. Γ indicates the degree of solution diversity (through archival of new non-dominating solutions) against search convergence (through the process of Lamarckian learning replacement) in the GS-MOMA search. While Lamarckian learning helps to speedup convergence towards the desired Pareto front, the large Γ ratio observed on all benchmark problems implies frequent discovery of potential non-dominating solutions when using both M1 and M2 with local refinements. This suggests _‘bless of uncertainty’_ may take the form of faster search convergence and better solution diversity in the context of multi-objective evolutionary search. 

## _D. Computational Complexity of GSM Framework_ 

In this subsection, we present an analytical study on the computational complexity of the GSM framework. The computational effort, referred here by Tcomp, of GS-SOMA or GS-MOMA is formulated as follows: 



where: 

- Gdb : number of standard SO/MOEA search generations configured for building the database of training data points at the initial search phase of the GSM framework, 

- Gmax : maximum number of search generations, 

- Npop : population size, 

- r : number of objectives to optimize, 

- kterm : number of iterations made in the trust-regionregulated local searches, 

- F : original/exact function evaluation cost, 

- Tens : time to build M1 i,e. the ensemble model, 

- TP R : time to build M2, i.e. the polynomial regression model, which is not applicable if PR is already built when constructing M1, 

- Toverhead : other additional costs such as for predictions and finding nearest points, which are often negligible. 

On the other hand, the computational cost for SS-SOMA or SS-MOMA variants is: 



where Tm is the time taken to build the particular surrogate model used. 

Although there are several elements in Equations (24) and (25), it is worth noting that when working with computationally expensive problems, the most significant part contributing to the total computational effort incurred is F . Hence, when F is significantly large, which is assumed to be fulfilled in any surrogate-assisted optimization framework, Tens, TP R, Toverhead and Tm are generally considered to be negligible, otherwise such frameworks should never be used. 

## V. CONCLUSION 

With a plethora of approximation/surrogate modeling approaches available in the literature, the choice of technique to use greatly affects the performance of surrogate-assisted evolutionary searches. It is argued that every approximation technique introduces some unique characteristics suitable for modeling some classes of problems accurately but not for others. Given that _a priori_ knowledge about the problem landscape is often scarce, the ability to tackle new problems in a reliable way is of significant value. This paper investigates on a generalized framework that unifies diverse surrogate models synergistically in the memetic evolutionary search. In contrast to existing works, the studied memetic framework emphasizes not only on _1)_ mitigating the impact of _‘curse of uncertainty’_ robustly, but also _2)_ benefitting from the _‘bless of uncertainty’_ , through the use of ensemble and landscape smoothing surrogate models, respectively. 

The core purpose of proposing any new search strategies, including the GSM framework, is to solve real-world optimization problems more robustly, effectively and/or efficiently. Hence, to facilitate possible systematic study and gain deeper understanding of the proposed methods for solving complex real-world problems plagued with computationally expensive functions, benchmark problems of diverse known properties have been employed. In this paper, we have presented extensive numerical studies on commonly used single/multi-objective optimization benchmark problems which have demonstrated the competitiveness of the generalized framework. Overall, the ensemble model is shown to be capable of attaining reliable, accurate surrogate models, while smoothing model speeds up evolutionary search performance by traversing through the multi- modal landscape of complex problems. Statistically, the generalized framework achieved significantly better performance on SOO/MOO when compared to SS-SOMA/MOMA and their underlying SO/MOEA. 

Presently, the GSM framework is used for solving realworld problems plagued with computationally expensive functions, particularly in the field of aerodynamic and molecular structural designs. Based on our experiences with both benchmark and real-world problems that range from turbine blade [7][20] to airfoil designs [8][11][22][32], the observations obtained from the use of benchmark problems do not deviate significantly from those in the real-world problems we have experimented. Some of the observations and problems we have noted when dealing with real-world problems are listed as follows: 

- In contrast to benchmark problems, the time taken to collect adequate amount of database points when dealing 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

11 

   - with real-world problems can be relatively if unsupported by sufficient machines capability. A possible solution is to directly utilize an external database of previously evaluated design points, if available, instead of building the database from scratch in the initial Gdb generations of evolutionary optimization. When existing database are unavailable, or the design points available are insufficient for building reliable surrogates, a smaller Gdb can be used to obtain the initial design points necessary for the reliable surrogate building to facilitate time saving. 

- When parallel machines capability is available, multilevel parallelization can be leveraged through the GSM framework, namely, _1)_ generation level, i.e., individuals at the same generation are sent to multiple computing nodes for evaluation, and _2)_ individual level, independent local searches utilizing M1 and M2 respectively, are executed in parallel. Hence, further acceleration can be expected. 

## ACKNOWLEDGMENT 

D. Lim and Y. S. Ong would like to thank Honda Research Institute Europe GmbH for sponsoring this work and members of Nanyang Technological University, Singapore for providing the computing resources. 

## REFERENCES 

- [1] C. G. Johnson and J. J. R. Caldalda, “Introduction: Genetic Algorithms in Visual Art and Music,” _Leonardo_ 35(2):175-184, 2002. 

- [2] S. Mahfoud, G. Mani, “Financial forecasting using genetic algorithms,” _Applied Artificial Intelligence_ , 10:543-565, 1996. 

- [3] D. Simon, “Biogeography-Based Optimization,” page(s): 1-13, Digital Object Identifier: 10.1109/TEVC.2008.919004. 

- [4] H. Karahan, H. Ceylan, M. T. Ayvaz, “Predicting rainfall intensity using a genetic algorithm approach,” _Hydrological Processes_ , 21(4):470-475, 2006. 

- [5] E. W. Lameijer, T. Baeck, J. N. Kok and A. P. Ijzerman, “Evolutionary algorithms in drug design,” _Natural Computing_ , 4(3):177-243, 2005. 

- [6] M. Olhofer, T. Arima, T. Sonoda, and B. Sendhoff, “Optimization of a stator blade used in a transonic compressor cascade with evolution strategies,” _Adaptive Computing in Design and Manufacture_ (ACDM), Springer Verlag, pp. 45-54, 2000. 

- [7] Y. Jin, M. Olhofer, B. Sendhoff, “A framework for evolutionary optimization with approximate fitness function,” _IEEE Transactions on Evolutionary Computation_ , 6(5):481-494, 2002. 

- [8] Y. S. Ong, P. B. Nair, and A. J. Keane, “Evolutionary optimization of computationally expensive problems via surrogate modeling,” _American Institute of Aeronautics and Astronautics Journal_ , 41(4):687-696, 2003. 

- [9] Y. Jin, “A comprehensive survey of approximation in evolutionary computation,” _Soft Computing_ , 9(1):3-12, 2005. 

- [10] A. Ratle, “Kriging as a surrogate landscape in evolutionary optimization,” _Artificial Intelligence for Engineering Design Analysis and Manufacturing_ , 15(1):37-49, 2001. 

- [11] Z. Zhou, Y. S. Ong, P. B. Nair, A. J. Keane, and K. Y. Lum, “Combining Global and Local Surrogate Models to Accelerate Evolutionary Optimization,” _IEEE Transactions on Systems, Man and Cybernetics, Part C: Reviews and Applications_ , 37(1):66-76, Jan 2007. 

- [12] R. Smith, B. Dike, and S. Stegmann, “Fitness inheritance in genetic algorithms,” _ACM Symposiums on Applied Computing_ , pp. 345-350, 1995. 

- [13] J. H. Chen, D. E. Goldberg, S. Y. Ho, and K. Sastry, “Fitness inheritance in multi-objective optimization,” _Genetic and Evolutionary Computation Conference_ , pp. 319-326, 2002. 

- [14] Y. Jin, M. Olhofer, and B. Sendhoff, “On evolutionary optimization with approximate fitness functions,” _Genetic and Evolutionary Computation Conference_ , pp. 786-792, 2000. 

- [15] M. Emmerich, A. Giotis, M. Oezdenir, T. Baeck, and K. Giannakoglou, “Metamodel-assisted evolution strategies,” _Parallel Problem Solving from Nature_ , LNCS 2439, pp. 371-380, 2002. 

- [16] H. Ulmer, F. Streichert, and A. Zell, “Evolution strategies assisted by gaussian processes with improved pre-selection criterion,” _Proc. of IEEE Congress on Evolutionary Computation_ , pp. 692-699, 2003. 

- [17] H. S. Kim and S. B. Cho, “An genetic algorithms with less fitness evaluation by clustering,” _Congress on Evolutionary Computation_ , pp. 887-894, 2001. 

- [18] Y. Jin and B. Sendhoff, “Reducing evaluations using clustering techniques and neural networks ensembles,” _Genetic and Evolutionary Computation Conference_ , LNCS 3102, pp. 688-699, 2004. 

- [19] J. Branke and C. Schmidt, “Faster convergence by means of estimation,” _Soft Computing_ , 9(1):13-20, 2005. 

- [20] L. Gr¨aning, Y. Jin, and B. Sendhoff. “Individual-based management of meta-models for evolutionary optimization with applications to threedimensional blade optimization,” In: S. Yang, Y.-S. Ong, Y. Jin(eds.), _Evolutionary Computation in Dynamic and Uncertain Environments_ , pp.225-250, Springer, 2007. 

- [21] P. K. S. Nain and K. Deb, “Computationally effective search and optimization procedure using coarse to fine approximation,” _Congress on Evolutionary Computation_ , pp.2081-2088, 2003. 

- [22] Y. S. Ong, P. B. Nair and K. Y. Lum, “Max-Min Surrogate-Assisted Evolutionary Algorithm for Robust Aerodynamic Design,” _IEEE Transactions on Evolutionary Computation_ , 10(4):392-404, August 2006. 

- [23] Y. S. Ong, P. B. Nair, K. Y. Lum, “Evolutionary algorithm with hermite radial basis function interpolations for computationally expensive adjoint solvers,” _Computational Optimization and Applications_ , 39(1):91-119, January 2008. 

- [24] K. C. Giannakoglou, D. I. Papadimitriou, I. C. Kampolis, “Aerodynamic shape design using evolutionary algorithms and new gradient-assisted metamodels,” _Computer Methods in Applied Mechanics and Engineering_ , 195:6312-6329, 2006. 

- [25] M. D. Schmidt and H. Lipson, “Coevolution of predictors,” page(s): 1-14 Digital Object Identifier: 10.1109/TEVC.2008.919006. 

- [26] J. Knowles, “ParEGO: a hybrid algorithm with on-line landscape approximation for expensive multiobjective optimization problems,” _IEEE Transcations on Evolutionary Computation_ , 10(1):50-66, 2006. 

- [27] D. Jones, M. Schonlau, and W. Welch, global optimization of expensive black-box functions,” _Journal of Global Optimization_ , 13:455492, 1998. 

- [28] K. Deb and P. K. S. Nain, “An evolutionary multi-objective metamodeling procedure using artificial neural networks,” In S. Yang, Y. S. Ong, and Y. Jin (eds.) _Evolutionary Computation in Dynamic and Uncertain Environments_ , pp. 297-322, Springer, 2007. 

- [29] M. Emmerich, K. Giannakoglou, and B. Naujoks, “Single and multiobjective evolutionary optimization assisted by gaussian random field metamodels,” _IEEE Transactions on Evolutionary Computation_ , 10(4): 421- 439, 2006. 

- [30] D. Chafekar, L. Shi, K. Rasheed, and J. Xuan, “Multi-objective GA optimization using reduced models,” _IEEE Trans. on Systems, Man, and Cybernetics, Part C: Reviews and Applications_ , 9(2):261-265, 2005. 

- [31] I. Voutchkov and A. J. Keane. “Multiobjective optimization using surrogates,” _Proceedings of the 7th International Conference on Adaptive Computing in Design and Manufacture_ , pp. 167-175, Holland, The M.C.Escher Company, 2006. 

- [32] Y. S. Ong, P. B. Nair, A. J. Keane, and K. W. Wong, “SurrogateAssisted Evolutionary Optimization Frameworks for High-Fidelity Engineering Design Problems,” In: Y. Jin(ed.), _Knowledge Incorporation in Evolutionary Computation_ , Springer Verlag, pp. 307 - 331, 2004. 

- [33] D. Lim, Y. S. Ong, Y. Jin, and B. Sendhoff, “A study on metamodeling techniques, ensembles, and multi-surrogates in evolutionary computation,” _Genetic and Evolutionary Computation Conference_ . London, UK, pp. 1288-1295, ACM Press, 2007. 

- [34] A. Samad and K.-Y. Kim, “Multiple surrogate modeling for axial compressor blade shape optimization,” _Journal of Propulsion & Power_ , 24(2):302-310, 2008. 

- [35] L. E. Zerpa, N. V. Queipo, S. Pintos, J.-L. Salager, “An optimization methodology of alkaline-surfactant-polymer flooding processes using field scale numerical simulation and multiple surrogates,” 47:197-208, 2005. 

- [36] D. Marjavaara, S. Lundstr¨om, W. Shyy, “Hydraulic turbine diffuser shape optimization by multiple surrogate model approximations of pareto fronts,” _ASME Journal of Fluids Engineering_ , 129(9):1228-1240, 2007. 

- [37] N. V. Queipo, R. T. Haftka, W. Shyy, T. Goel, R. Vaidyanathan, P. K. Tucker, “Surrogate-based analysis and optimization,” _Progress in Aerospace Sciences_ , 37:59-118, 2001. 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

12 

- [38] E. Sanchez, S. Pintos, N. V. Queipo, “Toward an optimal ensemble of kernel-based approximations with engineering applications,” _Structural Multidisciplinary Optimization_ , DOI 10.1007/s00158-007-0159-6, Accepted May 2007. 

- [39] A. Samad, K.-D. Lee, K.-Y. Kim, and R. T. Haftka, “Application of multiple-surrogate model to optimization of a dimpled channel,” _7th World Congress on Structural and Multidisciplinary Optimization_ , pp. 2276-2282, 2007. 

- [40] T. Goel, R. T. Haftka, W. Shyy, N. V. Queipo, “Ensemble of surrogates,” _Structural Multidisciplinary Optimization_ , 33:199-216, 2007. 

- [41] E. Acar and M. Rais-Rohani, “Ensemble of metamodels with optimized weight factors,” _Structural Multidisciplinary Optimization_ , DOI 10.1007/s00158-008-0230-y, Accepted December 2007. 

- [42] K.-H. Liang, X. Yao, and C. Newton, “Combining landscape approximation and local search in global optimization,” _Proceedings of the 1999 Congress on Evolutionary Computation_ , 2:1514-1520, Piscataway, NJ, 1999. 

- [43] K.-H. Liang, X. Yao, and C. Newton, “Evolutionary search of approximated n-dimensional landscape,” _International Journal of Knowledgebased Intelligent Engineering Systems_ , 4(3):172-183, 2000. 

- [44] Y. S. Ong, Z. Zhou, and D. Lim, “Curse and blessing of uncertainty in evolutionary algorithm using approximation,” _Congress on Evolutionary Computation_ , pp. 2928-2935, Vancouver, 2006. 

- [45] Y. Jin and J. Branke, “Evolutionary optimization in uncertain environments - a survey,” _IEEE Transactions on Evolutionary Computation_ , 9(3):303-317, June 2005. 

- [46] Y. S. Ong and A. J. Keane, “Meta-Lamarckian Learning in Memetic Algorithm,” _IEEE Transactions On Evolutionary Computation_ , 8(2):99110, April 2004. 

- [47] J. D. Knowles, R. A. Watson, D. W. Corne, “Reducing local optima in single-objective problems by multi-objectivization,” _Proceedings of the First International Conference on Evolutionary Multi-criterion Optimization (EMO’01)_ , pp. 269-283, 2001. 

- [48] N. Noman and H. Iba, “Accelerating differential evolution using an adaptive local search,” _IEEE Transactions on Evolutionary Computation_ , 12(1):107-125, 2008. 

- [49] A. J. Nebro, A. J. Luna, E. Alba, B. Dorronsoro, J. J. Durillo, A. Beham, “AbYSS: Adapting Scatter Search to Multiobjective Optimization,” page(s): 1-19 Digital Object Identifier: 10.1109/TEVC.2007.913109. 

- [50] Y. S. Ong, M.H. Lim, N. Zhu and K. W. Wong, of Adaptive Memetic Algorithms: A Comparative Study,” _IEEE Transactions on Systems, Man and Cybernetics - Part B_ , 36(1):141-152, 2006. 

- [51] Y. Liu, X. Yao and T. Higuchi, “Evolutionary Ensembles with Negative Correlation Learning,” _IEEE Transactions on Evolutionary Computation_ , 4(4):380-387, 2000. 

- [52] J. D. Pinter, _Global Optimization in Action_ , Kluwer, 1996. 

- [53] J. F. Rodriguez, J. E. Renaud, and L. T. Watson, “Convergence of trust region augmented lagrangian methods using variable fidelity approximation data,” _Structural Optimization_ , 15(3-4):141-156, 1998. 

- [54] C. T. Lawrence and A. L. Tits, “A computationally feasible sequential quadratic programming algorithm,” _Society for Industrial and Applied Mathematics_ , 11(4):1092-1118, 2001. 

- [55] D. J. C. Mackay, “Introduction to gaussian processes,” _Neural Networks and Machine Learning_ , 168:133-165, 1998. 

- [56] F. H. Lesh, “Multi-dimensional least-square polynomial curve _Communications of ACM_ , 2(9):29-30, 1959. 

- [57] C. Bishop, _Neural networks for pattern recognition_ , Oxford University Press, 1995. 

- [58] H. Ishibuchi and T. Murata, “Multi-objective genetic local search algorithm,” _IEEE International Conference on Evolutionary Computation_ , pp. 119-124, 1996. 

- [59] A. Jaszkiewicz, “Genetic local search for multiple objective combinatorial optimization,” Technical report RA-014/98, Institute of Computing Science, Poznan University of Technology, 1998. 

- [60] J. Knowles and D. Corne, “Memetic algorithms for multiobjective optimization: issues, methods and prospects,” in W. E. Hart, N. Krasnogor, J. E. Smith , editors, _Recent Advances in Memetic Algorithms_ , pp. 313352, 2005. 

- [61] N. Alexandrov, J. E. Dennis, R. M. Lewis, and V. Torczon, “A trust region framework for managing the use of approximation models in optimization,” _Journal on Structural Optimization_ , 15(1):16-23, 1998. 

- [62] J. G. Digalakis and K. G. Margaritis, “On benchmarking functions for genetic algorithms,” _Intern. J. Computer Math._ , 77(4):481-506, 2001. 

- [63] P. N. Suganthan, N. Hansen, J. J. Liang, K. Deb, Y. P. Chen, A. Auger and S. Tiwari, “Problem Definitions and Evaluation Criteria for the CEC 2005 Special Session on Real-Parameter Optimization,” Technical Report, 

Nanyang Technological University, Singapore, May 2005 AND KanGAL Report No. 2005005, IIT Kanpur, India. 

- [64] E. Zitzler, K. Deb, and L. Thiele, “Comparison of multi-objective evolutionary algorithms: empirical results,” _Evolutionary Computation_ , 8(2):173-195, 2000. 

- [65] K. Deb, S. Agrawal, A. Pratab, and T. Meyarivan, “A fast elitist nondominated sorting genetic algorithm for multi-objective optimization: NSGA-II,” _Parallel Problem Solving from Nature VI Conference_ , LNCS 1917, pp. 849-858, 2000. 

- [66] E. Zitzler, L. Thiele, M. Laumanns, C. M. Foneseca, and V. Grunert da Fonseca, “Performance Assessment of Multiobjective Optimizers: An Analysis and Review,” _IEEE Transactions on Evolutionary Computation_ , 7(2):117-132, 2003. 

- [67] C. A. Coello Coello, D. A. Van Veldhuizen, and G. B. Lamont, _Evolutionary algorithms for solving multi-objective problems_ , New York: Kluwer Academic, 2002. 

- [68] D. A. Van Veldhuizen and G. B. Lamont, “Evolutionary computation and convergence to a Pareto front,” in J. R. Koza, editor, _Late Breaking Papers at the Genetic Programming_ , pp. 221-228, 1998. 

- [69] D. A. Van Veldhuizen, “Multiobjective evolutionary algorithms: classsifications, analysis, and new innovations,” Ph. D. Thesis, Air Force Institute of Technology Dayton, OH, 1999. 

- [70] E. Zitzler, “Evolutionary algorithms for multiobjective optimization: methods and applications,” PhD thesis, Swiss Federal Institute of Technology (ETH) Zurich, Switzerland, TIK-Schriftenreihe Nr. 30, Diss ETH No. 13398, Shaker Verlag, Aachen, Germany, 1999. 

- [71] E. Zitzler and L. Thiele, “Multiobjective optimization using evolutionary algorithms a comparative case study”, _Fifth International Conference on Parallel Problem Solving from Nature (PPSN-V)_ , pp. 292-301, Springer, 1998. 

- [72] K. Deb, _Multi-objective optimization using evolutionary algorithms_ , First Edition, Chichester, UK: Wiley, 2001. 

- [73] R. G. Regis and C. A. Shoemaker, “Local function approximation in evolutionary algorithms for the optimization of costly functions,” _IEEE Transactions on Evolutionary Computation_ , 8:490-505, 2004. 

- [74] H.-M. Gutmann, On the semi-norm of radial basis function interpolants, Dept. Applied Math. Theor. Phy., Univ. Cambridge, Cambridge, U.K., Tech. Rep. DAMTP 2000/NA04, 2000. 

## APPENDIX I 

## APPROXIMATION/SURROGATE MODELING TECHNIQUES 

Here, we provide a brief review on three different surrogate modeling techniques used in this paper, namely: Kriging/Gaussian Process (GP), Polynomial Regression (PR), and Radial Basis Function (RBF). Throughout this section, let D = {xi, ti}, i = 1 . . . m denote the training dataset, where xi ∈ R<sup>d</sup> is an input design vector and ti ∈ R is the corresponding target value. 

## _A. Kriging/Gaussian Process (GP)_ 

The GP surrogate model [55] assumes the presence of an unknown true modeling function f (x) and an additive noise term v to account for anomalies in the observed data. Thus: 



The standard analysis requires the of prior probabilities on the modeling function and the noise model. From a stochastic process viewpoint, the collection t = {t1, t2, ..., tm} is called a Gaussian process if every subset of t has a joint Gaussian distribution. More specifically, 



where **C** is a covariance matrix parameterized in terms of hyperparameters θ, i.e., Cij = k(xi, xj; θ) and µ is the process mean. The Gaussian process is characterized by this 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

13 

covariance structure since it incorporates prior beliefs both about the true underlying function as well as the noise model. In the present study, we use the following exponential covariance model 



where Θ = diag{θ1, θ2, ..., θd} ∈ R<sup>d×d</sup> is a diagonal matrix of undetermined hyperparameters, and θd+1 ∈ R is an additional hyperparameter arising from the assumption that noise in the dataset is Gaussian (and output dependent). We shall henceforth use the symbol θ to denote the vector of undetermined hyperparameters, i.e., θ = {θ1, θ2, ..., θd+1}. In practice, the undetermined hyperparameters are tuned to the data using the evidence maximization framework. Once the hyperparameters have been estimated from the data, predictions can be readily made for a new testing point. 

## _B. Polynomial Regression (PR)_ 

In PR metamodeling technique [56], we an exponent vector ε containing positive integers (π1, π2, . . . , πd) and define x<sup>ε</sup> i<sup>asanexponentinputvector(xi</sup> 1 π1, xi2 π2 , . . . , xid πd). 

Given a set of exponent vectors ε1, ε2, . . . , εo and the set of data (xi, ti), where i = 1, 2, . . . , m, the polynomial model of (o − 1)<sup>th</sup> order has the form: 



where C1, C2, . . . , Co are the vectors to be estimated, and Cj = (cj1 , cj2 , . . . , cjd ), j = 1, 2, . . . , o. 

The least square method is then used to estimate the coefficients of the polynomial model. By definition, the least square error E to be minimized is: 



It may be easily shown that ti = f (xi), and by multiplying both sides of Equation (29) with x<sup>ε</sup> i<sup>j</sup> and taking the sum of m pairs of input-output data, we arrive at 



For j = 1, 2, . . . , o, the polynomial model for the training dataset can be represented in the matrix notation as follows 



where 



Then the matrix of the polynomial is: 







The predicted output for a new input pattern is then given by t<sup>ˆ</sup> i = γ.Bi<sup>T.</sup> 

## _C. Radial Basis Function_ 

The surrogate models of RBF used in this paper are interpolating radial basis function networks of the form 



where K(||x − xi||) : R<sup>d</sup> → R is a RBF and α = {α1, α2, . . . , αm} ∈ R<sup>m</sup> denotes the vector of weights. Hence, the number of hidden nodes in the RBF here is as many as the number of training points. 

Typical choices for the kernel include linear splines, cubic splines, multiquadrics, thin-plate splines, and Gaussian functions [57]. Recent studies in [73][74], indicate that the linear, cubic, and thin plate spline RBFs have better theoretical properties than the multiquadric and Gaussian RBFs. Hence, in this paper, we opt to use linear spline kernel function. The structure of some commonly used radial basis kernels and their parameterization are shown in Table XIX Given a suitable kernel, the weight vector can be computed by solving the linear algebraic system of equations Kα = t, where t = {t1, t2, . . . , tm} ∈ R<sup>m</sup> denotes the vector of outputs and K ∈ R<sup>m×m</sup> denotes the Gram matrix formed using the training inputs (i.e., the ijth element of K is computed as K(||xi − xj||)). 

## APPENDIX II 

## SINGLE-OBJECTIVE BENCHMARK FUNCTIONS 

Single-objective benchmark functions used in this paper are presented in this section. The shifted and/or rotated functions are taken from [62] and [63]. Note that due to the long description for F7-F10, reader is referred directly to [63] for those functions. From F4-F6, the following nomenclature applies: 

o = [o1, o2, . . . , od]: the shifted global optimum 

M: linear transformation matrix, obtained from [63]. 

## **_F1: Ackley_** 





IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

14 

## **_F2: Griewank_** 



Global optimum x<sup>∗</sup> i<sup>= 0.0fori = 1, . . . , d,F(x∗) = 0.0</sup> **_F3: Rosenbrock_** 



Global optimum x<sup>∗</sup> i<sup>= 1.0fori = 1, . . . , d,F(x∗) = 0.0</sup> **_F4: Shifted Rotated Rastrigin_** 



Global optimum x<sup>∗</sup> = o, F (x<sup>∗</sup> ) = fbias = −330. **_F5: Shifted Rotated Weierstrass_** 



Global optimum x<sup>∗</sup> = o, F (x<sup>∗</sup> ) = fbias = 90. a = 0.5, b = 3, kmax=20. 

**_F6: Shifted Expanded Griewank plus Rosenbrock_** 



Global optimum x<sup>∗</sup> = o, F (x<sup>∗</sup> ) = fbias = −130 

**_F7: Hybrid Composition Function(refer to F15 in [63]) F8: Rotated Hybrid Composition Function of F7(refer to F16 in [63])_** 

**_F9: Rotated Hybrid Composition Function with Narrow Basin Global Optimum(refer to F19 in [63]) F10: Non-continuous Rotated Hybrid Composition Function(refer to F23 in [63])_** 

15 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 



<!-- Start of picture text -->
45 45<br>exact function exact function<br>40 data points 40 data points<br>   approximated function   approximated function<br>35 starting point 35 starting point<br>local optimum found local optimum found<br>30 exact local optimum 30 exact local optimum<br>25<br>25<br>20<br>20<br>15<br>15<br>10<br>10<br>5<br>0 5<br>−5 0<br>−5 −4 −3 −2 −1 0 1 2 3 4 5 −5 −4 −3 −2 −1 0 1 2 3 4 5<br>x x<br>f(x) f(x)<br><!-- End of picture text -->

(a) ‘Curse of uncertainty’ in single-objective EA using surrogates. Approximated function in the figure is obtained using spline interpolation technique. 

(b) ‘Bless of uncertainty’ in single-objective EA using surrogates. Approximated function in the figure is obtained using a low order Polynomial Regression. 

Fig. 1. Curse and bless of uncertainty in single-objective EA using surrogates. 

16 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 



<!-- Start of picture text -->
f2 f2<br>x<br>x<br>o x X1 x o<br>o o xx x X X2 x xoo<br>o X x o X3<br>o o x oo X4 Initial solutions<br>x<br>Pareto solutions for MOEA<br>x o<br>Pareto Pareto without using surrogates<br>Front Front<br>x Pareto solutions for MOEA<br>f1 f1 using surrogates<br>(a) ‘Curse of uncertainty’ in multi ob- (b) ‘Bless of uncertainty’ in multi objec-<br>jective EA using surrogates. tive EA using surrogates.<br><!-- End of picture text -->

Fig. 2. Curse and bless of uncertainty in multi-objective EA using surrogates. 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

17 

f2 f2 f2 x 1 x x x opt 2 2 x x opt opt 2 x opt 1 1 x x opt opt Pareto Pareto Pareto Front Front Front f1 f1 f1 (a) An example of the case where (b) An example of the case (c) An example of the case where replacement is performed only where two subsequent replaceboth replacement and archiving once by GS-MOMA. (x<sup>1</sup> opt<sup>⪯</sup> ments are performed by GSare performed by GS-MOMA. x) ∧ (x<sup>1</sup> opt<sup>⪯x2</sup> opt<sup>)∧(x∼</sup> MOMA. (x<sup>1</sup> opt<sup>⪯x) ∧(x2</sup> opt<sup>⪯</sup> (x<sup>1</sup> opt<sup>⪯x)∧(x2</sup> opt<sup>⪯x)∧</sup> x<sup>2</sup> opt<sup>).x1</sup> opt<sup>replacesx.</sup> x<sup>1</sup> opt<sup>). x1</sup> opt<sup>replaces x, followed</sup> (x<sup>1</sup> opt<sup>∼x2</sup> opt<sup>).x1</sup> opt<sup>replaces</sup> by x<sup>2</sup> opt<sup>replacesx.</sup> x, x<sup>2</sup> opt<sup>isarchivedinAl.</sup> 



<!-- Start of picture text -->
f2 f2 f2<br>1 2<br>x == x == x<br>opt opt<br>x<br>x<br>1<br>x 2 x opt<br>opt<br>2<br>x<br>1 opt<br>x<br>opt<br>Pareto Pareto Pareto<br>Front Front Front<br>f1 f1 f1<br>(d) An example of the case where (e) An example of the case where (f) An example of the case where<br>archiving is performed only once archiving is performed twice by GS- neither replacement nor archiving<br>by GS-MOMA. (x ∼ x 1 opt ) ∧ MOMA. (x ∼ x 1 opt ) ∧ (x ∼ is performed. No new optimum is<br>(x ∼ x 2 opt ) ∧ (x1 opt ⪯ x2 opt ). x 2 opt ) ∧ (x1 opt ∼ x2 opt ). Both x1 opt found.<br>x 1 opt is archived in Al. and x 2 opt are archived in Al.<br><!-- End of picture text -->

Fig. 3. Examples of the 6 different actions taken by the Replace&Archive scheme in GS-MOMA for corresponding results of local searches. 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

18 



<!-- Start of picture text -->
3.2 6 8<br>3 4 7.5<br>2.8 7<br>2<br>2.6 SS−SOMA−AV 6.5<br>2.4 SS−SOMA−Perfect 0 6<br>2.2 −2 5.5<br>SS−SOMA−AV<br>2 −4 5<br>1.8 SS−SOMA−AV GS−SOMA 4.5 GS−SOMA<br>GS−SOMA −6<br>1.6 4 SS−SOMA−Perfect<br>1.4 −8 SS−SOMA−Perfect 3.5<br>−10 3<br>0 1 2 3 4 5 6 7 8 0 1 2 3 4 5 6 7 8 0 1 2 3 4 5 6 7 8<br>Exact Function Evaluations ( x1e3 ) Exact Function Evaluations ( x1e3 ) Exact Function Evaluations ( x1e3 )<br>(a) F1 (b) F2 (c) F3<br>50 4.9 −50<br>−60<br>SS−SOMA−Perfect<br>0<br>SS−SOMA−Perfect −70<br>4.85<br>SS−SOMA−Perfect<br>−80<br>−50 SS−SOMA−AV<br>−90 SS−SOMA−AV<br>GS−SOMA<br>4.8<br>−100 GS−SOMA −100 GS−SOMA<br>SS−SOMA−AV −110<br>−150 4.75 −120<br>0 1 2 3 4 5 6 7 8 0 1 2 3 4 5 6 7 8 0 1 2 3 4 5 6 7 8<br>Exact Function Evaluations ( x1e3 ) Exact Function Evaluations ( x1e3 ) Exact Function Evaluations ( x1e3 )<br>(d) F4 (e) F5 (f) F6<br>7.02<br>6.85 7<br>6.4<br>6.8<br>6.98 SS−SOMA−Perfect<br>6.75 SS−SOMA−Perfect 6.3 SS−SOMA−Perfect<br>6.96<br>6.7<br>6.2 6.94<br>6.65<br>6.6 6.1 SS−SOMA−AV 6.92<br>6.55 SS−SOMA−AV 6 6.9<br>6.456.5 GS−SOMA 5.9 GS−SOMA 6.886.86 GS−SOMASS−SOMA−AV<br>6.4 5.8 6.84<br>6.35<br>0 1 2 3 4 5 6 7 8 0 1 2 3 4 5 6 7 8 0 1 2 3 4 5 6 7 8<br>Exact Function Evaluations ( x1e3 ) Exact Function Evaluations ( x1e3 ) Exact Function Evaluations ( x1e3 )<br>(g) F7 (h) F8 (i) F9<br>7.4<br>7.35 SS−SOMA−Perfect<br>7.3<br>7.25<br>SS−SOMA−AV<br>7.2<br>7.15<br>7.1 GS−SOMA<br>7.05<br>7<br>6.95<br>6.9<br>0 1 2 3 4 5 6 7 8<br>Exact Function Evaluations ( x1e3 )<br>(j) F10<br>Fitness Value ( Natural Log ) Fitness Value ( Natural Log ) Fitness Value ( Natural Log )<br>Fitness Value  Fitness Value<br>Fitness Value (Natural Log)<br>Fitness Value (Natural Log) Fitness Value (Natural Log) Fitness Value (Natural Log)<br>Fitness Value (Natural Log)<br><!-- End of picture text -->

Fig. 4. Convergence trends for F1-F10 obtained from GS-SOMA, SS-SOMA-Perfect, and SS-SOMA-AV. 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

19 



<!-- Start of picture text -->
1<br>Gaussian Process (GP)<br>0.9 Polynomial Regression (PR)<br>Radial Basis Function (RBF)<br>0.8 Ensemble Model (M1)<br>0.7<br>0.6<br>0.5<br>0.4<br>0.3<br>0.2<br>0.1<br>0<br>F1 F2 F3 F4 F5 F6  F7 F8 F9 F10<br>Benchmark Problem<br>Normalized RMSE<br><!-- End of picture text -->

Fig. 5. The normalized RMSE by GP, PR, RBF, and weighted average ensemble. 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

20 



<!-- Start of picture text -->
1<br>0.9<br>0.8<br>0.7<br>0.6<br>0.5<br>0.4<br>0.3<br>0.2<br>0.1<br>0<br>F1 F2 F3 F4 F5 F6 F7 F8  F9  F10<br>Benchmark Problem<br>Fitness improvement contributed by M1<br>Fitness improvement contributed by M2<br>Normalized Fitness Improvement<br><!-- End of picture text -->

Fig. 6. The normalized improvement during the runs of GS-SOMA contributed by M1 (ImpM 1) and M2 (ImpM 2). 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

21 



<!-- Start of picture text -->
0.7<br>Gaussian Process (GP)<br>Polynomial Regression (PR)<br>0.6<br>Radial Basis Function (RBF)<br>Ensemble Model (M1)<br>0.5<br>0.4<br>0.3<br>0.2<br>0.1<br>0<br>MF1 MF2 MF3 MF4 MF5 MF6<br>Benchmark Problem<br>Normalized RMSE<br><!-- End of picture text -->

Fig. 7. The normalized RMSE by GP, PR, RBF, and weighted average ensemble on MF1-MF6. 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

22 



<!-- Start of picture text -->
1<br>0.9<br>0.8<br>0.7<br>0.6<br>0.5<br>0.4<br>0.3<br>0.2<br>0.1<br>0<br>MF1 MF2 MF3 MF4 MF5 MF6<br>Benchmark Problem<br>Replacement<br>Archiving<br>Ratio of Archiving to Replacement<br><!-- End of picture text -->

Fig. 8. Archiving to Replacement Ratio of GS-MOMA on MF1-MF6. 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

23 



<!-- Start of picture text -->
1.4 1 1<br>0.9 0.9<br>1.2<br>0.8 0.8<br>1 0.7 0.7<br>0.8 0.6 0.6<br>0.5 0.5<br>0.6 0.4 0.4<br>0.4 0.3 0.3<br>0.2 0.2<br>0.2<br>0.1 0.1<br>00 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 00 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 00 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1<br>f1 f1 f1<br>(a) NSGA-II (b) GS-MOMA (c) SS-MOMA-I<br>1 1.4<br>0.9<br>1.2<br>0.8<br>0.7 1<br>0.6 0.8<br>0.5<br>0.6<br>0.4<br>0.3 0.4<br>0.2<br>0.2<br>0.1<br>00 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 00 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1<br>f1 f1<br>(d) SS-MOMA-II (e) SS-MOMA-Perfect<br>f2 f2 f2<br>f2 f2<br><!-- End of picture text -->

Fig. 9. Pareto Front evolved for benchmark problem MF1 in NSGA-II, GS-MOMA, SS-MOMA-I, SS-MOMA-II, and SS-MOMA-Perfect. 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

24 



<!-- Start of picture text -->
1.4 1 1<br>0.9 0.9<br>1.2<br>0.8 0.8<br>1 0.7 0.7<br>0.8 0.6 0.6<br>0.5 0.5<br>0.6<br>0.4 0.4<br>0.4 0.3 0.3<br>0.2 0.2<br>0.2<br>0.1 0.1<br>00 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 00 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 00 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1<br>f1 f1 f1<br>(a) NSGA-II (b) GS-MOMA (c) SS-MOMA-I<br>1<br>0.9 1<br>0.8<br>0.7 0.8<br>0.6<br>0.6<br>0.5<br>0.4<br>0.4<br>0.3<br>0.2 0.2<br>0.1<br>00 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 00 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1<br>f1 f1<br>(d) SS-MOMA-II (e) SS-MOMA-Perfect<br>f2 f2 f2<br>f2 f2<br><!-- End of picture text -->

Fig. 10. Pareto Front evolved for benchmark problem MF2 in NSGA-II, GS-MOMA, SS-MOMA-I, SS-MOMA-II, and SS-MOMA-Perfect. 

25 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 



<!-- Start of picture text -->
1.5 1 1.2<br>0.8 1<br>1 0.6 0.8<br>0.6<br>0.4<br>0.5 0.4<br>0.2<br>0.2<br>0<br>0 0<br>−0.2<br>−0.2<br>−0.5 −0.4 −0.4<br>−0.6 −0.6<br>−10 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 −0.80 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 −0.80 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1<br>f1 f1 f1<br>(a) NSGA-II (b) GS-MOMA (c) SS-MOMA-I<br>1.5 1.2<br>1<br>1 0.8<br>0.6<br>0.5 0.4<br>0.2<br>0 0<br>−0.2<br>−0.5 −0.4<br>−0.6<br>−10 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 −0.80 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1<br>f1 f1<br>(d) SS-MOMA-II (e) SS-MOMA-Perfect<br>f2 f2 f2<br>f2 f2<br><!-- End of picture text -->

Fig. 11. Pareto Front evolved for benchmark problem MF3 in NSGA-II, GS-MOMA, SS-MOMA-I, SS-MOMA-II, and SS-MOMA-Perfect. 

26 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 



<!-- Start of picture text -->
6 4 4.5<br>3.5 4<br>5<br>3 3.5<br>4 3<br>2.5<br>2.5<br>3 2<br>2<br>1.5<br>2 1.5<br>1 1<br>1<br>0.5 0.5<br>0 0.4 0.5 0.6 0.7 0.8 0.9 1 0 0.4 0.5 0.6 0.7 0.8 0.9 1 0 0.4 0.5 0.6 0.7 0.8 0.9 1<br>f1 f1 f1<br>(a) NSGA-II (b) GS-MOMA (c) SS-MOMA-I<br>7 6<br>6 5<br>5<br>4<br>4<br>3<br>3<br>2<br>2<br>1 1<br>0 0.4 0.5 0.6 0.7 0.8 0.9 1 0 0.4 0.5 0.6 0.7 0.8 0.9 1<br>f1 f1<br>(d) SS-MOMA-II (e) SS-MOMA-Perfect<br>f2 f2 f2<br>f2 f2<br><!-- End of picture text -->

Fig. 12. Pareto Front evolved for benchmark problem MF4 in NSGA-II, GS-MOMA, SS-MOMA-I, SS-MOMA-II, and SS-MOMA-Perfect. 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

27 



<!-- Start of picture text -->
3 3 3.5<br>2.5 2.5 3<br>2 2 2.5<br>2<br>1.5 1.5<br>1.5<br>1 1 1<br>0.5 0.5 0.5<br>0 0 0<br>3 2 2<br>2 2 2.5 3 1.5 1 1.5 2 1.5 1 1.5 2<br>f2 1 0 0 0.5 1 f1 1.5 f2 0.5 0 0 0.5 f1 1 f2 0.5 0 0 0.5 f1 1<br>(a) NSGA-II (b) GS-MOMA (c) SS-MOMA-I<br>3.5<br>3 3.5<br>3<br>2.5<br>2.5<br>2 2<br>1.5 1.5<br>1 1<br>0.5 0.5<br>0 0<br>2 2.5 2.5<br>1.5 2 2 2<br>1 0.5 0.5 1 1.5 1.5 1 0.5 0.5 1 1.5<br>f2 0 0 f1 f2 0 0 f1<br>(d) SS-MOMA-II (e) SS-MOMA-Perfect<br>f3 f3 f3<br>f3 f3<br><!-- End of picture text -->

Fig. 13. Pareto Front evolved for benchmark problem MF5 in NSGA-II, GS-MOMA, SS-MOMA-I, SS-MOMA-II, and SS-MOMA-Perfect. 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

28 



<!-- Start of picture text -->
4.5 1.4 2<br>4 1.8<br>1.2<br>3.5 1.6<br>1 1.4<br>3<br>2.5 0.8 1.2<br>1<br>2 0.6 0.8<br>1.5<br>0.4 0.6<br>1 0.4<br>0.2<br>0.5 0.2<br>00 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 00 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 00 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1<br>f1 f1 f1<br>(a) NSGA-II (b) GS-MOMA (c) SS-MOMA-I<br>2.5 1.6<br>1.4<br>2<br>1.2<br>1.5 1<br>0.8<br>1 0.6<br>0.4<br>0.5<br>0.2<br>00 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1 00 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1<br>f1 f1<br>(d) SS-MOMA-II (e) SS-MOMA-Perfect<br>f2 f2 f2<br>f2 f2<br><!-- End of picture text -->

Fig. 14. Pareto Front evolved for benchmark problem MF6 in NSGA-II, GS-MOMA, SS-MOMA-I, SS-MOMA-II, and SS-MOMA-Perfect. 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

29 



<!-- Start of picture text -->
0.15 1<br>1.4<br>0.14 0.95<br>1.3<br>0.13 0.9<br>0.12 0.85 1.2<br>0.11 0.8<br>1.1<br>0.1<br>0.75<br>0.09 1<br>0.7<br>0.08<br>0.65 0.9<br>0.07<br>0.6<br>A B C D E A B C D E A B C D E<br>Algorithm Algorithm Algorithm<br>(a) Generational Distance (GD) (b) Maximum Spread (MS) (c) Hypervolume Ratio (HR)<br>Generational Distance (GD) Maximum Spread (MS) Hypervolume Ratio (HR)<br><!-- End of picture text -->

Fig. 15. Generational Distance(GD), Maximum Spread(MS), and Hypervolume Ratio(HR) performance metrics for benchmark problem MF1. (A:NSGA-II, B:GS-MOMA, C:SS-MOMA-I, D:SS-MOMA-II, E:SS-MOMA-Perfect) 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

30 



<!-- Start of picture text -->
0.26 1<br>0.24 0.95 1.2<br>0.22 0.9 1<br>0.85<br>0.2 0.8<br>0.8<br>0.18<br>0.75 0.6<br>0.16<br>0.7<br>0.14 0.4<br>0.65<br>0.12 0.6 0.2<br>0.1 0.55 0<br>A B C D E A B C D E A B C D E<br>Algorithm Algorithm Algorithm<br>(a) Generational Distance (GD) (b) Maximum Spread (MS) (c) Hypervolume Ratio (HR)<br>Generational Distance (GD) Maximum Spread (MS) Hypervolume Ratio (HR)<br><!-- End of picture text -->

Fig. 16. Generational Distance(GD), Maximum Spread(MS), and Hypervolume Ratio(HR) performance metrics for benchmark problem MF2. (A:NSGA-II, B:GS-MOMA, C:SS-MOMA-I, D:SS-MOMA-II, E:SS-MOMA-Perfect) 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

31 



<!-- Start of picture text -->
0.17 1 5.5<br>0.16 0.95 5<br>0.15 0.9 4.5<br>0.14 0.85 4<br>0.13 0.8 3.5<br>0.12 3<br>0.75<br>0.11 2.5<br>0.7<br>0.1 2<br>0.65<br>0.09 1.5<br>0.08 0.6 1<br>0.07 0.55<br>0.5<br>A B C D E A B C D E A B C D E<br>Algorithm Algorithm Algorithm<br>(a) Generational Distance (GD) (b) Maximum Spread (MS) (c) Hypervolume Ratio (HR)<br>Generational Distance (GD) Maximum Spread (MS) Hypervolume Ratio (HR)<br><!-- End of picture text -->

Fig. 17. Generational Distance(GD), Maximum Spread(MS), and Hypervolume Ratio(HR) performance metrics for benchmark problem MF3. (A:NSGA-II, B:GS-MOMA, C:SS-MOMA-I, D:SS-MOMA-II, E:SS-MOMA-Perfect) 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

32 



<!-- Start of picture text -->
1 2<br>2<br>0.9 1.8<br>1.6<br>1.5 0.8 1.4<br>0.7 1.2<br>1 1<br>0.6<br>0.8<br>0.5<br>0.5 0.6<br>0.4 0.4<br>0.2<br>0<br>A B C D E A B C D E A B C D E<br>Algorithm Algorithm Algorithm<br>(a) Generational Distance (GD) (b) Maximum Spread (MS) (c) Hypervolume Ratio (HR)<br>Generational Distance (GD) Maximum Spread (MS) Hypervolume Ratio (HR)<br><!-- End of picture text -->

Fig. 18. Generational Distance(GD), Maximum Spread(MS), and Hypervolume Ratio(HR) performance metrics for benchmark problem MF4. (A:NSGA-II, B:GS-MOMA, C:SS-MOMA-I, D:SS-MOMA-II, E:SS-MOMA-Perfect) 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

33 



<!-- Start of picture text -->
0.14 1 1.15<br>0.135 0.9999 1.1<br>0.9998<br>0.13 0.9997 1.05<br>0.125 0.9996 1<br>0.9995<br>0.12 0.9994 0.95<br>0.115 0.9993 0.9<br>0.9992<br>0.11<br>0.9991 0.85<br>0.105 0.999 0.8<br>A B C D E A B C D E A B C D E<br>Algorithm Algorithm Algorithm<br>(a) Generational Distance (GD) (b) Maximum Spread (MS) (c) Hypervolume Ratio (HR)<br>Values<br>Generational Distance (GD) Hypervolume Ratio (HR)<br><!-- End of picture text -->

Fig. 19. Generational Distance(GD), Maximum Spread(MS), and Hypervolume Ratio(HR) performance metrics for benchmark problem MF5. (A:NSGA-II, B:GS-MOMA, C:SS-MOMA-I, D:SS-MOMA-II, E:SS-MOMA-Perfect) 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

34 



<!-- Start of picture text -->
1 4<br>0.25 0.9 3.5<br>0.8<br>3<br>0.7<br>0.2<br>2.5<br>0.6<br>0.15 0.5 2<br>0.4<br>1.5<br>0.1 0.3<br>1<br>0.2<br>0.5<br>A B C D E A B C D E A B C D E<br>Algorithm Algorithm Algorithm<br>(a) Generational Distance (GD) (b) Maximum Spread (MS) (c) Hypervolume Ratio (HR)<br>Generational Distance (GD) Maximum Spread (MS) Hypervolume Ratio (HR)<br><!-- End of picture text -->

Fig. 20. Generational Distance(GD), Maximum Spread(MS), and Hypervolume Ratio(HR) performance metrics for benchmark problem MF6. (A:NSGA-II, B:GS-MOMA, C:SS-MOMA-I, D:SS-MOMA-II, E:SS-MOMA-Perfect) 

35 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

TABLE I 

ACTIONS TAKEN BY THE Replace&Archive SCHEME IN GS-MOMA FOR CORRESPONDING RESULTS OF LOCAL SEARCHES. NOTE THAT IRRELEVANT CASES HAVE BEEN EXCLUDED FOR BREVITY. 

|x<sup>1</sup><br>opt <sup>vs x</sup>|x<sup>2</sup><br>opt <sup>vs x</sup>|x<sup>1</sup><br>opt <sup>vs x2</sup><br>opt|Actions taken by GS-MOMA<br>|
|---|---|---|---|
|⪯|⪯|⪯|x=x<sup>1</sup><br>opt<br>|
|⪯|⪯|≻|x=x<sup>2</sup><br>opt<br><br>|
|⪯|⪯|∼|x=x<sup>1</sup><br>opt<sup>, archive x2</sup><br>opt<br>|
|⪯|⪯|==|x=x<sup>1</sup><br>opt<br>|
|⪯|==|⪯|x=x<sup>1</sup><br>opt<br>|
|⪯|∼|⪯|x=x<sup>1</sup><br>opt<br><br>|
|⪯|∼|∼|x=x<sup>1</sup><br>opt<sup>, archive x2</sup><br>opt<br>|
|==|⪯|≻|x=x<sup>2</sup><br>opt|
|==|==|==|No changes|
|==|∼|∼|Archive x<sup>2</sup><br>opt<br>|
|∼|⪯|≻|x=x<sup>2</sup><br>opt<br><br>|
|∼|⪯|∼|x=x<sup>2</sup><br>opt<sup>, archive x1</sup><br>opt<br>|
|∼|==|∼|Archive x<sup>1</sup><br>opt<br>|
|∼|∼|⪯|Archive x<sup>1</sup><br>opt|
|∼|∼|≻|Archive x<sup>2</sup><br>opt|
|∼|∼|∼|Archive x<sup>1</sup><br>opt <sup>and x2</sup><br>opt<br>|
|∼|∼|==|Archive x<sup>1</sup><br>opt|



36 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

#### TABLE II 

THE BENCHMARK PROBLEMS USED (F1-F10) FOR THE EMPIRICAL STUDY OF SINGLE-OBJECTIVE OPTIMIZATION. 

|**Benchmark**<br>**Problem**|**Description**|**Global**<br>**Optimum**<br>f(x<sup>∗</sup>)|
|---|---|---|
|F1|Ackley|0.0|
|F2|Griewank|0.0|
|F3|Rosenbrock|0.0|
|F4|Shifted Rotated Rastrigin (F10 in [63])|-330.0|
|F5|Shifted Rotated Weierstrass (F11 in [63])|90.0|
|F6|Shifted Expanded Griewank<br>plus Rosenbrock (F13 in [63])|-130.0|
|F7|Hybrid Composition Function (F15 in [63])|120.0|
|F8|Rotated Hybrid Composition Function (F16 in [63])|120.0|
|F9|Rotated Hybrid Composition Function<br>with Narrow Basin Global Optimum (F19 in [63])|10.0|
|F10|Non-continuous Rotated Hybrid<br>Composition Function (F23 in [63])|360.0|



IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

37 

#### TABLE III 

DEFINITION OF THE SINGLE-OBJECTIVE MAS (SOMAS) COMPARED. 

|**Algorithms**|**Defnition**|
|---|---|
|GA|No surrogate is used|
|SS-SOMA-GP|Single surrogate SOMA with M1: GP|
|SS-SOMA-PR|Single surrogate SOMA with M1: PR|
|SS-SOMA-RBF|Single surrogate SOMA with M1: RBF|
|SS-SOMA-Perfect|Single surrogate SOMA with M1: Perfect model|
|GS-SOMA|Generalized surrogate SOMA with<br>M1: _weighted-average_ ensemble of GP, PR, and RBF<br>M2: PR|



IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

38 

TABLE IV 

SETTING OF EXPERIMENTS FOR GA, SS-SOMA, SS-SOMA-PERFECT, AND GS-SOMA. 

|**Parameters Setting**|
|---|
|Population size (Npop)<br>100|
|Crossover probability (Pcross)<br>0.9|
|Mutation probability (Pmut)<br>0.1|
|Maximum number of exact evaluations<br>8000|
|Evolutionary operators<br>uniform crossover & mutation,<br>elitism and ranking selection|
|Number of trust region iteration(kterm)<br>for SS-SOMA and GS-SOMA<br>3|
|Database building phase (Gdb)|
|for SS-SOMA and GS-SOMA<br>20|
|(in number of generations)|
|Number of independent runs<br>20|



IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

39 

TABLE V 

STATISTICS OF THE FINAL SOLUTION QUALITY AT THE END OF 8000 EXACT FUNCTION EVALUATIONS FOR F1 USING GA, SS-SOMA-GP, SS-SOMA-PR, SS-SOMA-RBF, AND GS-SOMA. 

|Optimization||St|atistical Valu|es||
|---|---|---|---|---|---|
|Algorithm|Mean|Std. Dev.|Median|Best|Worst|
|GA|1.24e+01|9.50e-01|1.23e+01|1.12e+01|1.42e+01|
|SS-SOMA-GP|6.43e+00|9.73e-01|3.98e+00|2.87e+00|1.56e+01|
|~~SS-SOMA-PR~~|~~1.39e+00~~|~~1.93e-01~~|~~1.36e+00~~|~~1.14e+00~~|~~1.75e+00~~|
|SS-SOMA-RBF|4.91e+00|7.57e-01|4.86e+00|3.78e+00|6.09e+00|
|~~GS-SOMA~~|~~3.58e+00~~|~~5.09e-01~~|~~3.67e+00~~|~~2.87e+00~~|~~4.28e+00~~|



IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

40 

TABLE VI 

STATISTICS OF THE FINAL SOLUTION QUALITY AT THE END OF 8000 EXACT FUNCTION EVALUATIONS FOR F2 USING GA, SS-SOMA-GP, SS-SOMA-PR, SS-SOMA-RBF, AND GS-SOMA. 

|Optimization||St|atistical Valu|es||
|---|---|---|---|---|---|
|Algorithm|Mean|Std. Dev.|Median|Best|Worst|
|GA|4.58e+01|8.61e+00|4.67e+01|2.15e+01|6.19e+01|
|SS-SOMA-GP|1.79e+01|8.58e+00|1.07e+01|5.15e-09|3.00e+01|
|~~SS-SOMA-PR~~|~~1.18e-02~~|~~2.78e-02~~|~~4.29e-08~~|~~7.48e-10~~|~~1.19e-01~~|
|SS-SOMA-RBF|7.49e-01|8.98e-02|7.51e-01|6.02e-01|8.72e-01|
|~~GS-SOMA~~|~~2.2e-03~~|~~4.60e-03~~|~~8.95e-09~~|~~1.40e-10~~|~~1.54e-02~~|



IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

41 

#### TABLE VII 

STATISTICS OF THE FINAL SOLUTION QUALITY AT THE END OF 8000 EXACT FUNCTION EVALUATIONS FOR F3 USING GA, SS-SOMA-GP, SS-SOMA-PR, SS-SOMA-RBF, AND GS-SOMA. 

|Optimization||St|atistical Valu|es||
|---|---|---|---|---|---|
|Algorithm|Mean|Std. Dev.|Median|Best|Worst|
|GA|4.10e+02|1.01e+02|3.85e+02|2.33e+02|5.73e+02|
|~~SS-SOMA-GP~~|~~2.99e+01~~|~~7.73e-01~~|~~3.00e+01~~|~~2.87e+01~~|~~3.11e+01~~|
|SS-SOMA-PR|6.73e+01|2.55e+01|5.62e+01|3.72e+01|1.04e+02|
|SS-SOMA-RBF|4.90e+01|2.92e+01|3.97e+01|2.92e+01|1.57e+02|
|~~GS-SOMA~~|~~4.63e+01~~|~~2.92e+01~~|~~3.02e+01~~|~~2.83e+01~~|~~1.26e+02~~|



IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

42 

#### TABLE VIII 

STATISTICS OF THE FINAL SOLUTION QUALITY AT THE END OF 8000 EXACT FUNCTION EVALUATIONS FOR F4 USING GA, SS-SOMA-GP, SS-SOMA-PR, SS-SOMA-RBF, AND GS-SOMA. 

|Optimization||S|tatistical Valu|es||
|---|---|---|---|---|---|
|Algorithm|Mean|Std. Dev.|Median|Best|Worst|
|GA|-5.46e+01|3.01e+01|-5.48e+01|-1.11e+02|5.19e-01|
|SS-SOMA-GP|-1.19e+02|1.87e+01|-1.17e+02|-1.50e+02|-8.71e+01|
|SS-SOMA-PR|-1.19e+02|1.23e+01|-1.21e+02|-1.43e+02|-9.01e+01|
|~~SS-SOMA-RBF~~|~~-1.65e+02~~|~~1.86e+01~~|~~-1.66e+02~~|~~-1.91e+02~~|~~-1.36e+02~~|
|~~GS-SOMA~~|~~-1.26e+02~~|~~1.60e+01~~|~~-1.23e+02~~|~~-1.64e+02~~|~~-9.97e+01~~|



IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

43 

TABLE IX 

STATISTICS OF THE FINAL SOLUTION QUALITY AT THE END OF 8000 EXACT FUNCTION EVALUATIONS FOR F5 USING GA, SS-SOMA-GP, SS-SOMA-PR, SS-SOMA-RBF, AND GS-SOMA. 

|Optimization||St|atistical Valu|es||
|---|---|---|---|---|---|
|Algorithm|Mean|Std. Dev.|Median|Best|Worst|
|GA|1.26e+02|2.85e+00|1.26e+02|1.20e+02|1.32e+02|
|SS-SOMA-GP|1.19e+02|4.29e+00|1.20e+02|1.12e+02|1.25e+02|
|~~SS-SOMA-PR~~|~~5.67e+01~~|~~3.79e+00~~|~~1.16e+02~~|~~1.13e+02~~|~~1.25e+02~~|
|SS-SOMA-RBF|1.21e+02|2.61e+00|1.21e+02|1.18e+02|1.24e+02|
|~~GS-SOMA~~|~~1.19e+02~~|~~3.05e+00~~|~~1.19e+02~~|~~1.14e+02~~|~~1.24e+02~~|



IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

44 

TABLE X 

STATISTICS OF THE FINAL SOLUTION QUALITY AT THE END OF 8000 EXACT FUNCTION EVALUATIONS FOR F6 USING GA, SS-SOMA-GP, SS-SOMA-PR, SS-SOMA-RBF, AND GS-SOMA. 

|Optimization||St|atistical Valu|es||
|---|---|---|---|---|---|
|Algorithm|Mean|Std. Dev.|Median|Best|Worst|
|GA|-9.57e+01|9.43e+00|-9.79e+01|-1.06e+02|-7.28e+01|
|SS-SOMA-GP|-1.02e+02|2.99e+00|-1.03e+02|-1.05e+02|-9.74e+02|
|~~SS-SOMA-PR~~|~~-1.06e+02~~|~~2.45e+00~~|~~-1.07e+02~~|~~-1.09e+02~~|~~-1.02e+02~~|
|SS-SOMA-RBF|-1.03e+02|2.43e+00|-1.03e+02|-1.07e+02|-9.96e+01|
|~~GS-SOMA~~|~~-1.12e+02~~|~~1.05e+00~~|~~-1.23e+02~~|~~-1.13e+02~~|~~-1.11e+02~~|



45 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

TABLE XI 

STATISTICS OF THE FINAL SOLUTION QUALITY AT THE END OF 8000 EXACT FUNCTION EVALUATIONS FOR F7 USING GA, SS-SOMA-GP, SS-SOMA-PR, SS-SOMA-RBF, AND GS-SOMA. 

|Optimization||St|atistical Valu|es||
|---|---|---|---|---|---|
|Algorithm|Mean|Std. Dev.|Median|Best|Worst|
|GA|7.29e+02|5.92e+01|7.27e+02|6.43e+02|8.21e+02|
|SS-SOMA-GP|6.81e+02|7.23e+01|6.95e+02|6.02e+02|8.23e+02|
|SS-SOMA-PR|6.42e+02|5.80e+01|6.34e+02|5.73e+02|7.09e+02|
|~~SS-SOMA-RBF~~|~~6.27e+02~~|~~7.93e+01~~|~~5.99e+02~~|~~5.95e+02~~|~~8.49e+02~~|
|~~GS-SOMA~~|~~6.07e+02~~|~~3.06e+01~~|~~6.00e+02~~|~~5.79e+02~~|~~6.59e+02~~|



46 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

#### TABLE XII 

STATISTICS OF THE FINAL SOLUTION QUALITY AT THE END OF 8000 EXACT FUNCTION EVALUATIONS FOR F8 USING GA, SS-SOMA-GP, SS-SOMA-PR, SS-SOMA-RBF, AND GS-SOMA. 

|Optimization||St|atistical Valu|es||
|---|---|---|---|---|---|
|Algorithm|Mean|Std. Dev.|Median|Best|Worst|
|GA|4.83e+02|6.3e+01|4.62e+02|4.19e+02|6.06e+02|
|SS-SOMA-GP|4.52e+02|9.66e+01|4.35e+02|3.40e+02|5.63e+02|
|SS-SOMA-PR|3.94e+02|4.41e+01|3.75e+02|3.43e+02|4.52e+02|
|~~SS-SOMA-RBF~~|~~3.79e+02~~|~~3.3e+01~~|~~3.69e+02~~|~~3.51e+02~~|~~4.41e+02~~|
|~~GS-SOMA~~|~~3.25e+02~~|~~1.17e+02~~|~~2.86e+02~~|~~2.32e+02~~|~~5.54e+02~~|



IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

47 

#### TABLE XIII 

STATISTICS OF THE FINAL SOLUTION QUALITY AT THE END OF 8000 EXACT FUNCTION EVALUATIONS FOR F9 USING GA, SS-SOMA-GP, SS-SOMA-PR, SS-SOMA-RBF, AND GS-SOMA. 

|Optimization||St|atistical Valu|es||
|---|---|---|---|---|---|
|Algorithm|Mean|Std. Dev.|Median|Best|Worst|
|GA|1.02e+03|2.35e+01|1.02e+03|9.86e+02|1.08e+03|
|SS-SOMA-GP|9.42e+02|1.71e+01|9.37e+02|9.25e+02|9.81e+02|
|~~SS-SOMA-PR~~|~~9.32e+02~~|~~8.26e+00~~|~~9.31e+02~~|~~9.22e+02~~|~~9.48e+02~~|
|SS-SOMA-RBF|9.81e+02|1.43e+01|9.80e+02|9.67e+02|1.00e+03|
|~~GS-SOMA~~|~~9.42e+02~~|~~1.75e+01~~|~~9.37e+02~~|~~9.30e+02~~|~~9.86e+02~~|



IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

48 

#### TABLE XIV 

STATISTICS OF THE FINAL SOLUTION QUALITY AT THE END OF 8000 EXACT FUNCTION EVALUATIONS FOR F10 USING GA, SS-SOMA-GP, SS-SOMA-PR, SS-SOMA-RBF, AND GS-SOMA. 

|Optimization||St|atistical Valu|es||
|---|---|---|---|---|---|
|Algorithm|Mean|Std. Dev.|Median|Best|Worst|
|GA|1.51e+03|5.52e+01|1.52e+03|1.40e+03|1.58e+03|
|SS-SOMA-GP|1.26e+03|1.88e+02|1.22e+03|1.03e+03|1.54e+03|
|~~SS-SOMA-PR~~|~~1.07e+03~~|~~1.07e+02~~|~~1.04e+03~~|~~9.42e+02~~|~~1.29e+03~~|
|SS-SOMA-RBF|1.12e+03|1.16e+02|1.15e+03|9.59e+02|1.28e+03|
|~~GS-SOMA~~|~~1.01e+03~~|~~7.85e+01~~|~~9.53e+02~~|~~9.09e+02~~|~~1.51e+03~~|



IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

49 

TABLE XV 

RESULT OF T-TEST WITH 95% CONFIDENCE LEVEL COMPARING STATISTICAL VALUES FOR GS-SOMA AND THOSE OF SS-SOMA-GP, SS-SOMA-PR, SS-SOMA-RBF, SS-SOMA-PERFECT ON F1-F10 (s+, s−, AND ≈ INDICATES THAT GS-SOMA IS SIGNIFICANTLY BETTER, SIGNIFICANTLY WORSE, AND INDIFFERENT, RESPECTIVELY). 

||GA|SS-SOMA-GP|SS-SOMA-PR|SS-SOMA-RBF|SS-SOMA-Perfect|
|---|---|---|---|---|---|
|F1|s+|s+|s−|s+|s+|
|F2|s+|s+|≈|s+|s−|
|F3|s+|s−|s+|≈|s−|
|F4|s+|≈|≈|s−|s+|
|F5|s+|≈|s−|s+|s+|
|F6|s+|s+|s+|s+|s+|
|F7|s+|s+|s+|≈|s+|
|F8|s+|s+|s+|≈|s+|
|F9|s+|≈|s−|s+|s+|
|F10|s+|s+|≈|s+|s+|



50 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

#### TABLE XVI 

MULTI-OBJECTIVE BENCHMARK PROBLEMS (MF1-MF6). PARAMETRIC DOMAIN USED IS [0, 1]<sup>d</sup> , WHERE d IS THE PROBLEM DIMENSIONALITY CONSIDERED IN THE PRESENT STUDY. 

|**Benchmark**<br>**Function**|**Formulation**|**Characteristics**|
|---|---|---|
|MF1 (d= 30)|f1(x) =x1<br>f2(x) =g(x)[1−<br>�<br>f1(x)/g(x)]<br>g(x)= 1 + 9(<sup>�d</sup><br>i=2 <sup>xi)/(d −1)</sup>|Convex, 2-objective Pareto front|
|MF2 (d= 30)|f1(x) =x1<br>f2(x) =g(x)[1−f1(x)/g(x)<sup>2</sup>]<br>g(x)= 1 + 9(<sup>�d</sup><br>i=2 <sup>xi)/(d −1)</sup>|Non-convex, 2-objective Pareto front|
|MF3 (d= 50)|f1(x)=x1<br>f2(x) =g(x)[1−<br>�<br>f1/g−(f1/g)sin(10πf1)]<br>g(x)= 1 + 9(<sup>�d</sup><br>i=2 <sup>xi)/(d −1)</sup>|Convex, disconnected, 2-objective Pareto front|
|MF4 (d= 50)|f1(x) = 1−exp(−4x1)sin<sup>6</sup>(6πx1)<br>f2(x) =g(x)[1−(f1(x)/g(x))<sup>2</sup>]<br>g(x)= 1 + 9[<sup>�d</sup><br>i=2 <sup>xi/(d −1)]0.25</sup>|Non-convex, 2-objective Pareto front|
|MF5 (d= 20)|f1(x) =cos( <sup>π</sup><br>2 <sup>x1)cos(</sup> <sup>π</sup><br>2 <sup>x2)(1 + g(x))</sup><br>f2(x) =cos( <sup>π</sup><br>2 <sup>x1)sin( π</sup><br>2 <sup>x2)(1 + g(x))</sup><br>f3(x) =cos( <sup>π</sup><br>2 <sup>x1)(1 + g(x))</sup><br>g(x)= <sup>�d</sup><br>i=3<sup>(xi −x1)2</sup>|Non-convex, 3-objective, Pareto front|
|MF6 (d= 10)|f1(x) =x1<br>f2(x) =g(x)[1−<br>�<br>f1(x)/g(x)]<br>g(x)= 1 + 10(d−1)+ <sup>�d</sup><br>i=2<sup>(x2</sup><br>i <sup>−10 cos(4πxi))</sup>|Convex, 2-objective, multiple local Pareto front|



51 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

#### TABLE XVII 

DEFINITION OF THE MULTI-OBJECTIVE MAS (MOMAS) COMPARED. 

|**Algorithms**|**Defnition**|
|---|---|
|NSGA-II|No surrogate is used|
|GS-MOMA|Generalized surrogate MOMA with<br>M1: _weighted-average_ ensemble of GP, PR, and RBF<br>M2: PR|
|SS-MOMA-I|Single surrogate MOMA with<br>M1: Ensemble of GP, PR, and RBF|
|SS-MOMA-II|Single surrogate MOMA with<br>M1: PR|
|SS-MOMA-Perfect|Single surrogate MOMA with<br>M1: Perfect model|



52 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

#### TABLE XVIII 

SETTING OF EXPERIMENTS FOR NSGA-II, GS-MOMA, AND SS-MOMA. 

|**Parameters Se**|**tting**|
|---|---|
|Population size (Npop)|100|
|Crossover probability (Pcross)|0.9|
|Mutation probability (Pmut)|0.1|
|Maximum number of exact evaluations|MF1-MF2: 8000<br>MF3-MF4: 16000<br>MF5: 30000<br>MF6: 20000|
|Evolutionary operators|simulated binary crossover,<br>polynomial mutation,<br>binary tournament selection,<br>elitism, non-domination rank,<br>and crowded distance|
|Number of trust region iteration(kterm)<br>for SS-MOMA and GS-MOMA|2|
|Database building phase (Gdb)|MF1-MF2, MF5-MF6: 10|
|for SS-MOMA and GS-MOMA<br>(in number of generations)|MF3-MF4: 20|
|Number of independent runs|20|



53 

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION 

#### TABLE XIX 

RADIAL BASIS KERNELS. 

|Linear Splines|||x−ci||<br>|
|---|---|
|Thin Plate Splines|||x−ci||<sup>k</sup>ln||x−ci||<br>|
|Cubic Splines|||x−ci||<sup>3</sup><br>|
|Gaussian|e<sup>−||x−ci||2</sup><br>βi|
|Multiquadrics|�<br>1 + <sup>||x−ci||2</sup><br>βi<br>|
|Inverse Multiquadrics|(1 + <sup>||x−ci||2</sup><br>βi<br>)<sup>−1</sup><br>2|






---

## ANEXO — Camada de texto completa do PDF (get_text)

> Reprodução integral da camada de texto do PDF (todas as páginas, ordem de leitura bruta). Inclui tabelas de resultados e equações que a conversão estruturada acima pode ter omitido. Garante completude textual (imagens continuam omitidas).


<!-- página 1 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
1
Generalizing Surrogate-assisted Evolutionary
Computation
Dudy Lim, Yaochu Jin, Yew-Soon Ong, and Bernhard Sendhoff
Abstract— Using surrogate models in evolutionary search pro-
vides an efﬁcient means of handling today’s complex applica-
tions plagued with increasing high computational needs. Recent
surrogate-assisted evolutionary frameworks have relied on the
use of a variety of different modeling approaches to approximate
the complex problem landscape. From these recent studies, one
main research issue is with the choice of modeling scheme used,
which has been found to affect the performance of evolutionary
search signiﬁcantly. Given that theoretical knowledge available
for making a decision on an approximation model a priori is very
much limited, this paper describes a generalization of surrogate-
assisted evolutionary frameworks for optimization of problems
with objective(s) and constraint(s) that are computationally
expensive to evaluate. The generalized evolutionary framework
uniﬁes diverse surrogate models synergistically in the evolution-
ary search. In particular, it focuses on attaining reliable search
performance in the surrogate-assisted evolutionary framework
by working on two major issues: 1) to mitigate the ‘curse
of uncertainty’ robustly and, 2) to beneﬁt from the ‘bless of
uncertainty’. The backbone of the generalized framework is
a surrogate-assisted memetic algorithm that conducts simulta-
neous local searches using ensemble and smoothing surrogate
models, with the aims of generating reliable ﬁtness prediction
and search improvements simultaneously. Empirical study on
commonly used optimization benchmark problems indicates that
the generalized framework is capable of attaining reliable, high
quality, and efﬁcient performance under a limited computational
budget.
Index Terms— Surrogate-assisted evolutionary algorithms, ap-
proximation models, metamodels, surrogate models, memetic
algorithms, computationally expensive problems.
I. INTRODUCTION
O
VER the years, evolutionary algorithms (EAs) have
become one of the well-established optimization tech-
niques, especially in the ﬁelds of art & design, business &
ﬁnance, science and engineering. Many successful applications
of EAs have been reported, ranging from music composi-
tion [1] to ﬁnancial forecasting [2], aircraft design [3], rainfall
prediction [4], and drug design [5]. Although well established
as credible and powerful optimization tools, researchers in this
area are now facing new challenges of increasing computa-
tional needs by today’s applications. For instance, a continuing
trend in science and engineering is the use of increasingly
D. Lim is with the Emerging Research Lab, School of Computer Engineer-
ing, Nanyang Technological University, Blk N4, B3b-06, Nanyang Avenue,
Singapore 639798 (e-mail: dudy0001@ntu.edu.sg).
Y. S. Ong is with the Division of Information System, School of Computer
Engineering, Nanyang Technological University, Blk N4, 02b-39, Nanyang
Avenue, Singapore 639798.(e-mail: asysong@ntu.edu.sg).
Y. Jin and B. Sendhoff are with the Honda Research Institute Europe
GmbH, Carl-Legien-Strasse 30, 63073 Offenbach/Main, Germany (email:
{yaochu.jin,bernhard.sendhoff}@honda-ri.de).
high-ﬁdelity accurate analysis codes in the design and sim-
ulation process. Modern Computational Structural Mechanics
(CSM), Computational Electro-Magnetics (CEM), Computa-
tional Fluid Dynamics (CFD) and ﬁrst principle simulations
have been shown to be reasonably accurate. Such analysis
codes play a central role in the design process since they
aid designers and scientists in validating new designs and
studying the effect of altering key parameters on product
and/or system performance. However, such moves may prove
to be cost prohibitive or impractical in the evolutionary design
optimization process, leading to intractable design cycle times.
An intuitive way to reduce the search time of evolutionary
optimization algorithms when dealing with computationally
expensive solver, is the use of high performance comput-
ing technologies and/or computationally efﬁcient surrogate
models. In recent years, there have been increasing research
activities in the design of surrogate-assisted evolutionary
frameworks for handling complex optimization problems with
computationally expensive objective functions and constraints.
In particular, since the modeling and design optimization
cycle time is roughly proportional to the number of calls
to the computationally expensive solver, many evolutionary
frameworks have turned to the deployment of computationally
cheap approximation models in the search to replace in part
the original solvers
[6][7][8]. Using approximation models
also known as surrogates or meta-models, the computational
burden can be greatly reduced since the efforts required to
build the surrogates and to use them are much lower than
those in the standard approach that directly couples the EA
with the expensive solvers. Among the approximation models,
polynomial regression (PR), also known as response surface
methodology (RSM), support vector machine (SVM), artiﬁcial
neural networks (ANNs), radial basis function (RBF), and
Gaussian process (GP), also referred to as Kriging or design
and analysis of computer experiment (DACE) models, are the
most prominent and commonly used [9][10][11].
In the context of EA, various approaches for working with
computationally expensive problems using surrogate models
have been reported. Early techniques include the use of ﬁtness
inheritance or imitation [12][13], where the ﬁtness of an
individual is deﬁned by either the parents or other individuals
previously encountered along the search. Another common
approach is to pre-select a subset of individuals that would
undergo exact function evaluations while all others are pre-
dicted based on surrogate models. Some of the simple schemes
introduced are based on random individual selection [14] or
selecting the best/most promising individuals based on the pre-
dictions made by the surrogate models [7][11][15][16]. Other


<!-- página 2 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
2
schemes include identifying some cluster centers [17][18],
or uncertain individuals that are predicted to have poor esti-
mates [19] as representatives that will undergo exact function
evaluations subsequently. Such forms of model management
schemes are termed as ‘evolution control’ in [7][20]. An
alternative approach adopted in [21] involves the reﬁnement
of the surrogate used, from coarse to ﬁne grained models as
the search evolves. Online localized surrogate models are also
deployed within the local search phase of memetic algorithms
(MAs) [8][22]. The synergy of online global and local surro-
gate in the memetic search was also investigated in [11]. To
enhance the prediction accuracy of ﬁtness predictions based on
surrogates, the inclusion of gradient information in surrogate
building was also studied in
[23] and [24], independently.
More recently, [25] proposed the use of co-evolution technique
to address issues such as level of approximation and accuracy
of ﬁtness predictors.
More recently, the idea of using surrogate to speed-up
evolutionary search process has found its way into the ﬁeld
of evolutionary multi-objective optimization (MOO). Many
of the schemes introduced in the context of single-objective
optimization (SOO) have been extended to their corresponding
MOO variants. The Kriging-based surrogate-assisted evolu-
tionary multi-objective algorithm in [26] represents an ex-
tension of the efﬁcient global optimization framework
[27]
introduced for handling SOO problems, while [28] and [29]
extended the coarse-to-ﬁne grained approximation and pre-
selection schemes to its MOO variants, respectively. The co-
evolution of genetic algorithms (GAs) for multiple objectives
based on online surrogates was introduced in [30]. After some
ﬁxed search intervals, the surrogates produced that represent
the different objectives are then exchanged and shared among
multiple GAs. In [31], a multi-objective EA is run for a
number of iterations on a surrogate model before the model
is updated using exact evaluation from some selected points.
For greater details on surrogate-assisted EAs for handling
optimization problems with computationally expensive ob-
jective/constraint functions, the readers are referred to [9]
and [32].
In spite of the extensive research efforts on this topic, exist-
ing surrogate-assisted evolutionary frameworks remains open
for further improvement. Jin et al. in [14] have shown that ex-
isting surrogate-assisted evolutionary frameworks proposed are
often ﬂawed by introduction of false optima since the paramet-
ric approximation technique used may not be capable of mod-
eling the problem landscapes accurately, thus producing unre-
liable search. Generally, the ‘curse of dimensionality’ creates
signiﬁcant difﬁculties in the construction of accurate surrogate
models for ﬁtness prediction. Further, recent studies have
shown that the choice of approximation technique used affects
the performance of evolutionary searches [33]. On the other
hand, it is worth keeping in mind that approximation error in
the surrogate model does not always harm. A surrogate model
capable of smoothing the multi-modal or noisy landscape
of the complex problem may contribute more beneﬁcially
to the evolutionary search than one that models the original
ﬁtness function accurately. For instance, the study in [44] has
emphasized the importance of predicting search improvement
as opposed to the usual practice of improving only the quality
of the surrogate in the context of evolutionary optimization.
Based on these recent works, it is worth highlighting the in-
ﬂuence of the approximation method used on the performance
of any surrogate-assisted evolutionary search. The greatest
barrier to further progress is that, with so many approximation
techniques available in the literature, it is almost impossible
to know which is most relevant for modeling the problem
landscape or generating reliable ﬁtness predictions when one
has only limited knowledge of its ﬁtness space before the
search starts. Moreover, approximation techniques by them-
selves may model differently on different problem landscapes.
Depending on the complexity of a design problem, a single
approximation model that may have proven to be successful
in an instance might not work so well, or at all, on others. In
the ﬁeld of multidisciplinary optimization, such observations
have also been reported [34][35][36][37][38][39][40][41]. In
those works, this issue is commonly handled by performing
multiple optimization runs, each on different surrogate model
or ensemble model. In [34][35][39], a set of surrogate models
consisting Kriging, PR, RBF, and weighted average ensemble
is used to demonstrate that multiple surrogates can improve
robustness of optimization at minimal cost. Similarly, [36]
uses PR and RBF surrogate models in the context of multi-
objective optimization and shows that each of the models
performs better at different region of the Pareto front. Others
in [37][38][40][41] resolve this issue by introducing various
ensemble model building techniques. It is shown from these
works that ensemble models generally outperform most of the
individual surrogates.
The present paper introduces a generalized framework for
unifying diverse surrogate models synergistically in the evo-
lutionary search. In contrast to existing efforts, we focus on
predicting search improvement in the context of optimization
as opposed to solely on improving the prediction quality of
the approximation. In particular, we generalize the problem
to attain reliable search improvement in surrogate-assisted
evolutionary framework as two major goals: 1) to mitigate
the ‘curse of uncertainty’ and, 2) to beneﬁt from the ‘bless
of uncertainty’. The ‘curse of uncertainty’1 refers to the
negative consequences introduced by the approximation error
of the surrogate models used. On the other hand, ‘bless of
uncertainty’ refers to the beneﬁts attained by the use of
surrogate models. Particularly, we seek for surrogate models
that are capable of generating reliable ﬁtness predictions
on diverse problems of different landscapes to mitigate the
‘curse of uncertainty’ on one hand, and on the other hand
surrogate models that are capable of smoothing rugged ﬁtness
landscapes to prevent the search from getting stuck in local
optima [44]. Previous works by Yao et al. [42][43] have also
conﬁrmed that smoothed landscape of rugged ﬁtness landscape
can lead the search to optimum solutions easier than using the
exact ﬁtness landscape.
The rest of this paper is organized as follows. Section II
discusses the impacts of uncertainty due to approximation
1In the present context, the deﬁnition of ’uncertainty’ refers to the approxi-
mation errors in the ﬁtness function due to the use of surrogate models based
on the deﬁnitions given in [45].


<!-- página 3 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
3
errors in evolutionary frameworks that employ surrogates.
Based on the discussion, Section III provides a generalization
of surrogate-assisted evolutionary search for both SOO and
MOO subsequently. We summarize the empirical studies on
some popular SOO and MOO benchmark problems in Section
IV. Finally, Section V concludes this paper.
II. IMPACTS OF APPROXIMATION ERRORS IN
SURROGATE-ASSISTED EVOLUTIONARY ALGORITHMS
In this section, we brieﬂy discuss the effects of uncer-
tainty introduced by inaccurate approximation models on
Surrogate-Assisted Evolutionary Algorithms (SAEA) search
performance. Without loss of generality, here we consider
computationally expensive minimization problems under lim-
ited computational budget with bound constraints of the fol-
lowing form:
minimize:
f1(x), f2(x), . . . , fr(x)
subject to:
xl
i ≤xi ≤xu
i ,
(1)
where i = 1, 2, . . . , d, d is the dimensionality of the search
problem, r is the number of objective functions, and xl
i, xu
i
are the lower and upper bounds of the ith dimension of vector
x, respectively.
Note that when more than one objective is involved for
approximation, there are two commonly adopted strategies, i.e.
1) one approximation model per objective function, and 2) one
approximation model for an aggregated (linear or nonlinear
combination) objective function, faggr(x). In this paper, we
consider the second strategy. Since in single-objective context,
faggr(x) = f(x) = f1(x), the term f(x) might be used
interchangeably to faggr(x) for brevity purpose when only
single-objective context is considered.
If faggr(x) denotes the original ﬁtness function and the
approximated function is ˆfaggr(x), the approximation errors at
any solution vector x is e(x) , i.e., the uncertainty introduced
by the surrogate at x, may then be deﬁned as:
e(x) = |faggr(x) −ˆfaggr(x)|
(2)
Here, we highlight the negative and positive impacts in-
troduced by the approximation inaccuracies of the surrogates
on SAEA search [44]. The negative impact or otherwise
known as the ‘curse of uncertainty’ on SAEA search can be
brieﬂy deﬁned as the phenomenon where the inaccuracies of
the surrogates used results in the SAEA search to stall or
converge to false optimum. To illustrate the ‘curse’ effect, we
refer to Fig. 1(a) where the SAEA is likely to converge to
the false optimum of the spline interpolation model due to
inaccuracy. On the other hand, the positive impact, i.e., the
‘bless of uncertainty’ in SAEA materializes when the use of
surrogate(s) brings about greater search improvements over the
use of original exact objective/ﬁtness function. For instance,
the surrogate can help to traverse the search across valleys
and hills of local optima by smoothing the ruggedness/multi-
modality of the problem landscape. To illustrate the blessing
effect, we refer to the example in Fig. 1(b), where a low
order polynomial regression scheme is used to approximate
the exact objective function. Due to the smoothing effect of
the polynomial surrogate, the search leads to an improved
solution that is unlikely to be attained even if the exact
objective function is used. Hence, the ‘bless of uncertainty’
brings about possible acceleration in the search. Besides a
faster convergence, recent study in [32] revealed that the ‘bless
of uncertainty’ in SAEA also exists in the form of improving
evolutionary search diversity through the use of surrogate
model.
Next, to illustrate ‘curse and bless of uncertainty’ in the
context of multi-objective optimization, we refer to the ex-
amples in Figs. 2(a) and 2(b). Fig. 2(a) depicts the effect of
‘curse of uncertainty’ in MOEA search due to the presence
of inaccurate surrogate models. In Fig. 2(a), the surrogate-
assisted MOEA search is observed to be evolving towards
poor non-dominated solutions in comparison to that based
on exact ﬁtness functions. Moreover, those labeled as x1 and
x2 in Fig. 2(a) suggest that some solutions might stall, while
others fail to converge optimally. On the other hand, Fig. 2(b)
illustrates the presence of ‘bless of uncertainty’ where the
errors in the surrogate used is observed to improve the MO
evolutionary search in both convergence and diversity mea-
sures. Particularly, some improved solutions of the surrogate-
assisted search is shown to dominate at least one of its initial
solutions, while others such as x3 and x4 are newly found
non-dominated solutions.
III. GENERALIZING SURROGATE-ASSISTED
EVOLUTIONARY SEARCH
In this section, we present a generalization of surrogate-
assisted evolutionary frameworks for optimization of problems
with objective(s) and constraint(s) that are computationally ex-
pensive to evaluate. The generalized framework illustrated here
for unifying diverse approximation concept synergistically is
a surrogate-assisted memetic algorithm that conducts simul-
taneous local searches on separate ensemble and smoothing
surrogate models. MAs are population-based meta-heuristic
search methods that are inspired by Darwinian principles of
natural evolution and Dawkins notion of a meme deﬁned as a
unit of cultural evolution capable of local reﬁnements [46]2.
For example, the brief outline of a traditional MA is provided
in Algorithm 1.
In the generalized framework, we introduce ﬁrst the idea of
employing online local ensemble surrogate models constructed
from diverse approximation concepts using data points that lie
in the vicinity of an initial guess. The surrogate or approxi-
mation models are then used to replace the expensive function
evaluations performed in the local search phase. The improved
solution generated by the local search procedure then replaces
the genotype and/or ﬁtness of the original individual 3.
2Note that the rationale behind using a memetic framework over a tradi-
tional evolutionary framework is multi-fold [46][50]. First, we aim to exploit
MAs’ capability of locating the local and global optima efﬁciently. Second,
a memetic model of adaptation exhibits the plasticity of individuals that a
pure genetic model fails to capture. Further, by limiting the use of surrogate
models within the local search procedures, the global convergence property
of EAs can be ensured. For a greater exposition of local meta-heuristics in
optimization, the reader is referred to [47][48][49].
3There are two basic replacement strategies in MAs [50]:


<!-- página 4 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
4
Algorithm 1 Memetic Algorithm (for SOO)
1: Initialization: Generate and evaluate a population of design
vectors.
2: while computational budget is not exhausted do
3:
Apply evolutionary operators (selection, crossover, mutation)
to create a new population.
4:
5:
/ ∗∗∗∗Local Search Phase ∗∗∗∗/
6:
7:
for each individual x in current population do
8:
• Apply local search to ﬁnd an improved solution, xopt.
9:
• Perform replacement using Lamarckian learning, i.e.
10:
if f(xopt) < f(x) then
11:
x = xopt
12:
end if
13:
end for
14:
15:
/ ∗∗End of Local Search Phase ∗∗/
16:
17: end while
A. Ensemble Model
To mitigate the ‘curse of uncertainty’ due to the effect of
using imperfect surrogate models, we seek for surrogate mod-
els that are capable of generating reliable ﬁtness predictions on
diverse problems. In particular, since it is almost impossible
to know in advance which approximation technique best suits
the optimization problem at hand, we consider a synergy of
diverse approximation methods through the use of ensemble
models to generate reliable accurate predictions across prob-
lems of differing problem landscapes [18][51][37], as opposed
to single surrogate models created by speciﬁc approximation
scheme that may not be appropriate for the problem at hand.
In what follows, we consider online local weighted average
ensembles. For instance, in the single-objective context, the
predicted ensemble output of f(x) is formulated as:
ˆfens(x)
=
n
X
i=1
ci ˆfi(x),
n
X
i=1
ci
=
1,
(3)
where
ˆfens(x) and
ˆfi(x) are the ﬁtness prediction made
by the ensemble and ith surrogate model, respectively. The
same formulation applies in the multi-objective context where
faggr(x) is considered. ci is the weight coefﬁcient associated
with the ith surrogate model. A model can be assigned a larger
weight if it is found or deemed to be more accurate. Hence,
the weighting function becomes:
ci =
Pn
j=1,j̸=i εj
(n −1) Pn
j=1 εj
,
(4)
• Lamarckian learning forces the genotype to reﬂect the result of im-
provement in local search by placing the locally improved individual
back into the population to compete for reproductive opportunities.
• Baldwinian learning only alters the ﬁtness of the individuals and the
improved genotype is not encoded back into the population.
For the sake of brevity, we consider Lamarckian learning in this paper.
where εj is the error measurement for the jth surrogate model.
Here, the root mean square error (rmse) is used as the error
measurement. The rmse of each surrogate model is then of
the form:
rmse =
rPm
i=1 e2(xi)
m
,
(5)
where m is the number of data samples compared, e(xi) is
the error of prediction for data point xi, as shown in Equation
(2). For greater details on other ensemble model building tech-
niques, interested readers are referred to [37][38][40][41][51].
B. Landscape Smoothing Model
Meanwhile, to beneﬁt from the ‘bless of uncertainty’,
smoothing techniques including global convex underestima-
tion, tunneling and ﬁlling methods are some appropriate alter-
natives [52] that may be used. Given a problem landscape,
smoothing methods transform the function into one with
noticeably fewer minima, thus speeding up the evolutionary
search. In the generalized framework, global convex under-
estimation is used for successive smoothing of the problem
landscape within the local search phase which is realized
through low-order polynomial regression (PR). Besides the
generalization property of PR models on rugged landscape, the
low computational costs incurred makes them very efﬁcient as
online surrogate models. Note that the PR model may be used
in both ensemble and the smoothing models, hence only a
one-time model building cost is involved.
C. GSM Framework for Single-Objective Optimization
In this subsection, we describe the generalized surrogate
memetic framework for single-objective optimization. A brief
outline of the generalized surrogate single-objective memetic
algorithm (GS-SOMA) is presented in Algorithm 2. Note that
the difference between the GS-SOMA and a traditional MA
lies in the local search phase of the algorithms.
GS-SOMA begins with the initialization of a population
of design points. During the database building phase, the
search operates like a traditional evolutionary algorithm based
on the original exact ﬁtness function for some initial Gdb
generations. Up to this stage, no form of surrogates are used,
and all exact ﬁtness function evaluations made are archived
in a central database. Subsequently, the algorithm proceeds
into the local search phase. For each individual x, n online
surrogates that model the ﬁtness function are created dynam-
ically using m training data points, which lie in the vicinity
of x, extracted from the archived database of previously
evaluated design points. From the n surrogates, an ensemble
model is built. From here, two separate local searches are
conducted on 1) M1, the ensemble of n surrogate models,
and 2) M2, a low-order PR model. If improved solutions are
achieved, GS-SOMA proceeds with the individual replacement
scheme. Since we adopt the Lamarckian scheme here, the
genotype/phenotype of the initial individual is then replaced
by the higher quality solutions among the two that are locally
improved based on M1 and M2, i.e., x1
opt or x2
opt. The
search cycle is then repeated until the allowed maximum
computational budget is exhausted.


<!-- página 5 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
5
Algorithm 2 Generalized Surrogate Single-Objective Memetic
Algorithm (GS-SOMA)
1: initialization: Generate and evaluate a database containing a
population of designs, archive all exact evaluations into the
database.
2: while computational budget is not exhausted do
3:
if generation count < database building phase (Gdb) then
4:
Evolve the population using exact ﬁtness function evalua-
tions, archive all exact evaluations into the database.
5:
else
6:
Apply evolutionary operators (selection, crossover, muta-
tion) to create a new population.
7:
8:
/ ∗∗∗∗Local Search Phase ∗∗∗∗/
9:
10:
for each individual x in the population do
11:
• Find m nearest points to x in database as training
points for surrogate models.
12:
• Build model-1: M1, as an ensemble of all M ′
j for
j = 1, . . . , n where n is the number of surrogate models
used.
13:
• Build model-2: M2, which is a low-order PR model.
14:
• Apply local search in M1 to arrive at x1
opt, and M2 to
arrive at x2
opt.
15:
• Replace x with the locally improved solution, i.e.
16:
if f(x1
opt) < f(x2
opt) then
17:
x = x1
opt
18:
else
19:
x = x2
opt
20:
end if
21:
• Archive all new exact function evaluations into the
database.
22:
end for
23:
24:
/ ∗∗End of Local Search Phase ∗∗/
25:
26:
end if
27: end while
D. GSM Framework for Multi-Objective Optimization
Next, we describe the Generalized Surrogate Memetic
framework in the context of multi-objective optimization
(MOO). In MOO, a solution x(1) is said to dominate solution
x(2) in the objective space, i.e., x(1) ⪯x(2) if the following
two conditions hold:
• x(1) is no worse than x(2) on all objectives or fj(x(1)) ≤
fj(x(2)) for all j = 1, 2, . . . , r.
• x(1) is strictly better than x(2) on at least one objective,
or fj(x(1)) < fj(x(2)) for at least one j ∈1, 2, . . . , r
If set P is the entire feasible search space, the non-dominated
set P ∗is labeled as the Pareto-optimal set. Any two solutions
in P ∗must non-dominate each other, i.e. x(1) ∼x(2). On
the other hand, Pareto front (PF ∗) is the image of the
Pareto-optimal set in objective space. The brief outline of a
typical Multi-Objective Memetic Algorithm (MOMA) using
weighting (scalarization) technique [58][59][60] is illustrated
in Algorithm 3. In contrast, the studied GSM framework for
multi-objective optimization (GS-MOMA) is outlined in Al-
gorithm 4. Note that the key differences of the two algorithms
lie in the local search phase and selection pool forming phase.
GS-MOMA begins with the population initialization phase
and evolutionary search based on exact ﬁtness function for a
Algorithm 3 Multi-Objective Memetic Algorithm
1: initialization: Generate and evaluate a population of design
vectors.
2: while computational budget is not exhausted do
3:
Apply MO evolutionary operators (selection, crossover, muta-
tion) to create a new population.
4:
5:
/ ∗∗∗∗Local Search Phase ∗∗∗∗/
6:
7:
for each individual x in the population do
8:
• Generate a random weight vector w = (w1, w2, . . . , wr),
Pr
i=1 wi = 1 where r is the number of objectives.
9:
• Apply local search in faggr = Pr
i=1 wifi(x) to ﬁnd an
improved solution, xopt.
10:
• Perform Lamarckian learning, i.e.
11:
if faggr(xopt) < faggr(x) then
12:
x = xopt
13:
end if
14:
end for
15:
16:
/ ∗∗End of Local Search Phase ∗∗/
17:
18: end while
Algorithm 4 Generalized Surrogate Multi-objective Memetic
Algorithm (GS-MOMA)
1: initialization: Generate and evaluate an initial population with
Npop individuals, archive all exact evaluations into a database.
2: while computational budget is not exhausted do
3:
if generation count < database building phase (Gdb) then
4:
Evolve the population using exact ﬁtness function evalua-
tions, archive all exact evaluations into the database.
5:
else
6:
Generate the offspring population , Po using MO evolu-
tionary operators (selection, crossover, mutation) on the
selection pool.
7:
8:
/ ∗∗∗∗Local Search Phase ∗∗∗∗/
9:
10:
Initialize the learning archive, Al to empty state.
11:
for each individual x in the offspring population do
12:
•
Generate
a
random
weight
vector
w
=
(w1, w2, . . . , wr), Pr
i=1 wi
=
1 where r is the
number of objectives.
13:
• Find m nearest points to x in database as training
points for surrogate models.
14:
• Build model-1: M1, as an ensemble of all M ′
j for
j = 1, . . . , n where n is the number of surrogate models
used, of faggr = Pr
i=1 wifi(x)
15:
• Build model-2: M2, which is a low-order PR model,
of faggr = Pr
i=1 wifi(x)
16:
• Apply local search in M1 to arrive at x1
opt, and M2 to
arrive at x2
opt
17:
• Replace&Archive( x, x1
opt, x2
opt, Al )
18:
end for
19:
20:
/ ∗∗End of Local Search Phase ∗∗/
21:
22:
23:
/ ∗∗∗∗Selection pool forming ∗∗∗∗/
24:
25:
Form selection pool, Ps = Pc
S Po
S Al.
26:
27:
/ ∗∗End of selection pool forming ∗∗/
28:
29:
end if
30: end while


<!-- página 6 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
6
Algorithm 5 Procedure Replace&Archive(x, x1
opt, x2
opt, Al)
1: if x1
opt ⪯x then
2:
x = x1
opt
3:
if x2
opt ⪯x1
opt then
4:
x = x2
opt
5:
else if x2
opt ∼x1
opt then
6:
Archive x2
opt in Al
7:
end if
8: else if x2
opt ⪯x then
9:
x = x2
opt
10:
if x2
opt ∼x1
opt then
11:
Archive x1
opt in Al
12:
end if
13: else if (x1
opt ∼x) ∧(x2
opt == x) then
14:
Archive x1
opt in Al
15: else if (x2
opt ∼x) ∧(x1
opt == x) then
16:
Archive x2
opt in Al
17: else if (x1
opt ∼x) ∧(x2
opt ∼x) then
18:
if (x1
opt ⪯x2
opt) ∥(x1
opt == x2
opt) then
19:
Archive x1
opt in Al
20:
else if x2
opt ⪯x1
opt then
21:
Archive x2
opt in Al
22:
else
23:
Archive x1
opt and x2
opt in Al
24:
end if
25: end if
number of early generations, Gdb, before entering the local
search phase. In the local search phase, independent local
searches are conducted on 1) M1, the ensemble of n surrogate
models, and 2) M2, the smoothing low-order PR model on
each individual of the generated offspring population. For the
sake of brevity, the core distinguishing feature of GS-MOMA
can be noted in line 17 of Algorithm 4, i.e. the existence of
the Replace&Archive procedure.
The Replace&Archive procedure performs replacements
based on domination between the original offspring and the
two local optima found. The original offspring will only be
replaced by one dominating optimum found. Any other local
optima are then saved into the learning archive, Al. Note that
the result of GS-MOMA’s local searches is either xopt ⪯x or
xopt ∼x. Otherwise, there is no improvement to the original
offspring, and hence we get xopt == x.
Based on the procedure in Algorithm 5, the possible local
search outcomes and corresponding actions taken by the
scheme are summarized in Table I. Note that there exist
6 possible actions to be taken by GS-MOMA which are
summarized as follows:
• Replacement is performed once (e.g. Fig. 3a).
• Two subsequent replacements are performed (e.g. Fig.
3b).
• Both replacement and archiving are performed (e.g. Fig.
3c).
• Archiving is performed once (e.g. Fig. 3d).
• Archiving is performed twice (e.g. Fig. 3e).
• Neither replacement nor archiving is performed (e.g. Fig.
3f).
At the end of each GS-MOMA generation, Al is combined
with the current parent population, Pc, and the offspring
population, Po to form the entire pool of individuals, Ps
that will then undergo the MOEA selection mechanism, i.e.,
Ps = Pc
S Po
S Al. From here, the process described repeats
until the maximum computational budget of the GS-MOMA
is exhausted.
E. Local Search Scheme
In the GSM framework for SO/MOO, a trust-region-
regulated search strategy is utilized to ensure convergence
to some local optimum or the global optimum of the exact
computationally expensive ﬁtness function [61][8][53], even
though surrogate models are deployed in the local search.
For each individual in the GS-SO/MOMA population, the
local search (refer to line 14 of Algorithm 2 and line 16
of Algorithm 4) proceeds with a sequence of trust-region
subproblems of the form
minimize :
ˆf k(xk
c + s),
subject to :
∥s∥≤Ωk,
(6)
where k = 0, 1, 2, . . . , kmax, ˆf(x) is the approximation func-
tion corresponding to the objective function f(x). Meanwhile,
xk
c, s, and Ωk represent the initial guess (current best solution)
at iteration k, an arbitrary step, and the trust-region radius at
iteration k, respectively. In our experiments, the Sequential
Quadratic Programming (SQP) [54] is used to minimize the
sequence of subproblems on the approximated landscape.
During the local search, the initial trust-region radius Ωis
initialized based on the minimum and maximum values of the
m design points used to construct the surrogate model (refer
to line 11 of Algorithm 2 and line 13 of Algorithm 4). The
trust-region radius for iteration k, i.e. Ωk is updated based
on a measure which indicates the accuracy of the surrogate
model at the kth local optimum, xk
opt. This measure, ρk,
provides a measure of the actual versus predicted change in
the exact ﬁtness function values at the kth local optimum and
is calculated as:
ρk = f(xk
c) −f(xk
opt)
ˆf(xkc) −ˆf(xk
opt)
.
(7)
The value of ρk is then used to update the trust-region radius
as follows [61]:
Ωk+1
= C1Ωk,
if ρk ≤C2,
= Ωk,
if C2 < ρk ≤C3,
(8)
= C4Ωk,
if ρk > C3,
where C1, C2, C3, and C4 are constants. Typically, C1 ∈
(0, 1) and C4 ≥1 for the scheme to work efﬁciently. From
experience, we set C1 = 0.25, C2 = 0.25, C3 = 0.75, and
C4 = 2, if ||xk
opt−xk
c||∞= Ωk or C4 = 1, if ||xk
opt−xk
c||∞<
Ωk.
The trust-region radius for the next iteration, Ωk+1, is
reduced if the accuracy of the surrogate, measured by ρk is
low. On the other hand, Ωk is doubled if the surrogate is found
to be accurate and the kth local optimum, xk
opt, lies on the
trust-region bounds. Otherwise the trust-region radius remains
unchanged.


<!-- página 7 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
7
The initial guess of the optimum at iteration k +1 becomes
xk+1
c
= xk
opt,
if ρk > 0,
= xk
c,
if ρk ≤0.
(9)
The trust-region process for an individual terminates when the
termination condition is satisﬁed. For instance, this termination
condition could be when the trust-region radius Ωapproaches
ε, where ε represents some small trust-region radius, or when
a maximum number of iteration kterm is reached.
IV. EMPIRICAL STUDY
In this section, we present an empirical study on the GSM
framework for solving single and multi-objective optimization
problems. In the present study, we considered a diverse set of
exact interpolating and generalizing approximation techniques
for constructing the local surrogate models, i.e., M1 and
M2. These include the interpolating Kriging/Gaussian process
(GP), interpolating linear spline radial basis function (RBF)
and 2nd order polynomial regression (PR). For greater details
on GP, PR, and RBF, the reader is referred to [55][56][57] and
Appendix I.
A. Parameters of GSM Framework
In this subsection, we discuss on the user-speciﬁed parame-
ters of the GSM framework. Apart from the parameters of the
underlying SO/MOEA, the generalized framework has three
additional user-speciﬁed parameters: m, Gdb and kterm.
Since model accuracy is highly dependent on the sufﬁciency
of the m data points used for model building, the size of
nearest neighboring points used (based on Euclidean distance)
is deﬁned by d+(d+1)(d+2)/2, where d is the dimensionality
of the optimization problem. It is worth noting that the com-
plexity for identifying these m points is negligible compared
to the cost of surrogate model building. Moreover, since our
emphasis here is with regard to a framework that is tailored
for solving computationally expensive problems, i.e., problems
that may cost from minutes to hours of computational time per
evaluation, such overheads are considered to be insigniﬁcant.
From these m data points, as many as (d+1)(d+2)/2 among
them 4 are chosen uniformly as the training data for building
the surrogates, the remaining data points then form the set for
validating the prediction quality of the surrogate.
Parameter Gdb, on the other hand, deﬁnes the period of the
database building phase (refer to lines 3-5 in Algorithms 2
and 4) before the core operation of the GSM framework
begins to take effect. Hence Gdb can be adapted for different
optimization problems according to the fulﬁllment on the
requirement of parameter m. The lower bound of Gdb is
deﬁned by the period to acquire a minimum of m data points
for construction of reliable surrogate models.
Theoretically, the trust-region local search scheme termi-
nates when the trust-region radius, Ωapproaches ε, where ε
represents some very small value for termination condition
(refer to Section III-E). Nevertheless, for practical reason,
4This amount corresponds to the minimum number of data points required
for building quadratic regression models.
under limited computational budget, it is more appropriate to
derive a suitable value for kterm as the termination condition
in the trust-region local search. In what follows, we present a
theoretical bound for kterm:
Ω1
min (C1)kmin ≤ε
(10)
⇒(C1)kmin ≤
ε
Ω1
min
(11)
⇒kmin log C1 ≤log
ε
Ω1
min
(12)
Since C1 ∈(0, 1) →log C1 < 0, we arrive at:
⇒kmin ≥

log

ε
Ω1
min

/ (log C1)
(13)
⇒kmin ≥logC1

ε
Ω1
min

.
(14)
Similarly, the maximum number of trust-region iterations in
the local search, i.e., kmax, is estimated by:
kmax < N max
succ + N max
succ logC1

ε
Ω1
max

(15)
⇒kmax < N max
succ

1 + logC1

ε
Ω1max

.
(16)
Note that N max
succ is the maximum number of successful itera-
tions, while Ω1
min and Ω1
max are the lower and upper bounds
of the initial trust-region radius. In effect, the bounds for kterm
as the termination condition can be derived as:
logC1

ε
Ω1
min

≤kterm < N max
succ

1 + logC1

ε
Ω1max

.
(17)
In the trust-region-regulated local search, Ω1 depends on the
local region of interest where the initial m nearest neighbors
are located. Hence it is not possible to deﬁne this term
precisely for any new optimization problem. For instance, if
Ω1
min ≈10ε and C1 = 0.25, we arrive at:
kterm ≥
log 0.1
log 0.25,
kterm ≥1.66.
(18)
As opposed to using kterm = 1 which translates to a single
iteration local search, a minimum value of kterm ≥2 is more
practical to allow the mechanisms of the trust-region-regulated
local search to take effect.
B. Single-Objective Optimization
Empirical study on the GS-SOMA is performed using
10 benchmark problems (F1-F10) reported in [62][63] and
summarized here in Table II. More detailed description of
the problems are also provided in Appendix II. They consist
of problems with diverse properties in terms of separability,
multi-modality, and continuity.
In this paper, all the benchmark problems are conﬁgured
with a dimensionality of d = 30 for SOO. Performance
comparisons are then made between the GA, SS-SOMA-GP,
SS-SOMA-PR, SS-SOMA-RBF, SS-SOMA-Perfect, and GS-
SOMA (refer to Table III for the deﬁnition of the algorithms
investigated here). Note that to facilitate a fair comparison,
the surrogate memetic variants are built on top of the same
GA used in the study, which ensures that any improvements
observed is a direct contribution of the surrogate framework


<!-- página 8 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
8
considered. SS-SOMA-XXX refers to the different surrogate-
assisted single-objective MA variants, each with a unique
approximation method used to generate the surrogate model.
For instance, XXX in SS-SOMA-XXX refers to GP, PR, or
RBF. On the other hand, SS-SOMA-Perfect refers to an SS-
SOMA that employs an imaginary approximation technique
that generates error-free surrogates 5, i.e., RMSE = 0. Hence
the notion of curse or bless of uncertainty does not exist in the
SS-SOMA-Perfect search. As such, any SS-SOMA-XXX that
under/out-perform SS-SOMA-Perfect is clearly attributed to
the effects of curse and bless of uncertainty, respectively. Last
but not least, GS-SOMA refers to the Generalized Surrogate
framework for single-objective optimization. The common
parameter settings of the algorithms used in the present
experimental study are summarized in Table IV.
1) Experimental Results: In Tables V-XIV, the detailed
statistical results of 20 independent runs for SS-SOMAs, GS-
SOMA, and GA are presented. The GS-SOMA and best
performing SS-SOMA are highlighted in the tables. Note that
none of the SS-SOMAs always dominates in performance on
all 10 benchmark problems. This makes good sense since
the performance of any surrogate-assisted evolutionary search
would depend on the match between the characteristics of
the problem landscape and approximation scheme used. For
instance, in the tables, it is shown that SS-SOMA-PR serves
to be best suited for F1, F5, and F9 since it outperforms all
other algorithms on these problems. Similarly, this also applies
to SS-SOMA-GP which excels on F3. On the other hand,
SS-SOMA-RBF, though not superior, performs relatively well
on F3, F4, F7, and F8. Moreover, it is worth noting that the
SS-SOMAs are observed to have performed much poorly on
several occasions. For instance, SS-SOMA-PR fares badly on
F3, F4, F7, and F8. The same is true for SS-SOMA-GP on
F1, F4-F8, and F10, and SS-SOMA-RBF on F1, F2, F5, F6,
F9, and F10.
On the other hand, the results in Tables V-XIV, indicate that
GS-SOMA consistently performs well on all the benchmark
problems. The t-test results, i.e., at 95% conﬁdence level, for
the different algorithms as reported in Table XV conﬁrms that
GS-SOMA outperforms or is competitive to the SS-SOMAs
on 43/50 cases. On the remaining 7 cases, GS-SOMA also
displays solution qualities close to that of the superior SS-
SOMA, see the highlighted results in Tables V-XIV. Note
that this is a signiﬁcant achievement considering that no a
priori knowledge is available to select an appropriate surrogate
modeling scheme for the problems considered. This highlights
the reliability of the generalized framework.
The search convergence trends of GS-SOMA, SS-SOMA-
AV, and SS-SOMA-Perfect are also plotted in Fig. 4. Note
that SS-SOMA-AV represents the estimated performance one
might expect to get when an approximation technique is
randomly chosen for use. Hence, SS-SOMA-AV is generated
from the average of the results obtained by all 3 SS-SOMAs,
5An error-free surrogate model can be realized by using exact ﬁtness
function in the portion of SS-SOMA where a surrogate model should be used,
but the incurred ﬁtness evaluation is counted only as many as in SS-SOMA.
i.e. SS-SOMA-GP, SS-SOMA-PR, and SS-SOMA-RBF. It is
evident from the search convergence trends that GS-SOMA is
superior over SS-SOMA-AV on the 10 benchmark problems.
This indicates that the generalized framework is more reliable
when one has no knowledge about the suitability of the
approximation scheme for the problem at hand.
2) Analyzing the Generalized Evolutionary Framework in
Single-Objective Optimization: To gain a better understanding
of the generalized framework, we further analyze the reliability
and effectiveness of the ensemble (M1) and smoothing (M2)
surrogate models in contributing to the evolutionary search.
To facilitate the analysis, the normalized root mean square
errors (N-RMSE) of ﬁtness predictions based on the ensemble
surrogate model, i.e., M1 in GS-SOMA search, for the bench-
mark problems are presented in Fig. 5. The normalized RMSE
of model i is determined as follows:
Normalized RMSEi =
RMSEi
Pn
j=1 RMSEj
,
(19)
where n is the total approximation methods used in shaping the
ensemble. From this ﬁgure, the consistently low N-RMSE of
the ensemble model generated in the GS-SOMA search across
all benchmark problems, demonstrates the high reliability of
the ﬁtness prediction generated by M1 across the different
optimization problems over any single surrogates.
Further, it is worth noting that the use of M2 contributes
to the ﬁtness improvement in GS-SOMA, which conﬁrms the
possible beneﬁts of bless of uncertainty in surrogate model.
The normalized average ﬁtness improvement of the local
searches contributed via the use of M1 (ImpM1) and M2
(ImpM2) during the GS-SOMA searches are summarized in
Fig. 6 and is deﬁned by:
Normalized ImpM1 =
ImpM1
ImpM1+ImpM2 ,
Normalized ImpM2 =
ImpM2
ImpM1+ImpM2 .
(20)
ImpM1 is the total ﬁtness improvements attained by local re-
ﬁnements, i.e., through Lamarckian learning, when f(x1
opt) <
f(x2
opt), while ImpM2 is the total ﬁtness improvements when
f(x2
opt) < f(x1
opt).
From the statistical results given in Fig. 6, it is notable
that M1 and M2 surrogates have contributed to the surrogate-
assisted memetic search in their unique ways. This provides
a means for explaining the results that were obtained in
Fig. 4 and Tables V-XIV. In particular, the reason for that
all surrogate-assisted SOMAs outperform SS-SOMA-Perfect
on F1 (Ackley) suggests the presence of ‘bless of uncertainty’
through the use of surrogate(s), since the notion of curse or
bless of uncertainty cannot exist in the latter. Further, the
fact that SS-SOMA-PR is the most superior on F1 (Ackley)
highlights the strength of the PR model in contributing to
the search via smoothing the rugged landscape of the Ackley
function. This hypothesis is clearly supported by the large
portion of ﬁtness improvements that are contributed by M2
(i.e., the PR model) on F1, see Fig. 6. On the other hand,
neither SS-SOMAs nor GS-SOMA manage to outperform
the SS-SOMA-Perfect on F3(Rosenbrock), suggesting the


<!-- página 9 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
9
presence of ‘curse of uncertainty’ due to the surrogate(s).
Further, the results in F3 of Fig. 6 also indicate that M2
(i.e., the smoothing PR model) did not contribute signiﬁcantly
to the search since the problem landscape of this function
is originally smooth. Rather, the use of ensemble model in
GS-SOMA had contributed to reliable ﬁtness improvement on
F3(Rosenbrock) by generating reliable prediction accuracy. On
the other test problems, both M1 and M2 surrogates were
shown to contribute signiﬁcantly to GS-SOMA in their own
unique ways.
C. Multi-Objective Optimization
In this subsection, we present the empirical study of the GS-
MOMA on 6 moderate to high dimensional MO benchmark
problems, labeled here as MF1-MF6
[64]. The MO bench-
mark problems used in the study are summarized in Table XVI.
Performance comparisons are then made between the stan-
dard non-dominated sorting genetic algorithm-II (NSGA-
II) [65] and variants of MOMA. For fair comparison, we com-
pare GS-MOMA with several SS-MOMAs and the NSGA-
II since the formers are demonstrated with NSGA-II as the
baseline by building on top of it. Hence, all algorithms com-
pared inherit the same evolutionary operators as the NSGA-
II used in our experiment. In SS-MOMAs, an offspring will
be replaced in the spirit of Lamarckian learning during local
search if its aggregated ﬁtness function is found to be better
than the original offspring. Similarly, SS-MOMA-Perfect is
introduced here to assess the effects of approximation error
on surrogate-assisted evolutionary search performance. For
the sake of brevity, the notations and deﬁnitions of the MO
algorithms studied are tabulated in Table XVII while the
common parameter settings of the MO algorithms used in the
experimental study are deﬁned in Table XVIII 6.
Many performance indicators exists for assessing the per-
formance of MOEAs, such as those summarized in [66][67].
Here, the following three performance indicators are used, i.e.,
• Generational Distance (GD) [68][69]: This measure-
ment indicates the gap between the true Pareto front
(PF ∗) and the evolved Pareto front (PF). Mathemati-
cally, it can be formulated as:
GD =
1
nP F
v
u
u
t
nP F
X
i=1
di
2,
(21)
where nP F is the number of members in PF, di is the
Euclidean distance (in objective space) between member
i of PF and its nearest member in PF ∗. A low value of
GD is more desirable since it reﬂects a good convergence
to the true Pareto fronts.
• Maximum Spread (MS) [70]: It is used to measure how
well the true Pareto front (PF ∗) is covered by the evolved
Pareto front (PF). The MS measurement used in this
6Since MF3 and MF4 have higher dimensionality, i.e. d = 50, greater
initial database size is required. For these cases, Gdb is set to 20.
paper is formulated as:
MS =
v
u
u
t1
r
r
X
i=1
»min(f max
i
, F max
i
) −max(f min
i
, F min
i
)
F max
i
−F min
i
–2
,
(22)
where f max
i
and f min
i
are the maximum and minimum of
the ith objective in the evolved PF, respectively. F max
i
and F min
i
are the maximum and minimum of the ith
objective in PF ∗, respectively. Higher value of MS
reﬂects a larger area of PF ∗covered by PF, which is
desirable.
• Hypervolume Ratio (HR) [69]: This indicates the ratio
between the hyperarea or hypervolume (H) [71] domi-
nated by the evolved PF and PF ∗, where HR is deﬁned
as:
HR =
H(P F )
H(P F ∗),
H = volume (SnP F
i=1 vi) .
(23)
Here, vi denotes the hypercube constructed from member
i of a particular Pareto front and the reference point. A
HR value close to 1 indicates that the evolved Pareto front
is quite close to the true Pareto front, in both convergence
and spread of solutions.
1) Experimental Results: The obtained Pareto fronts of the
benchmark problems for 20 independent runs are combined
and depicted in Figs. 9-14. The respective performance metrics
are then summarized in Figs. 15-20. From these results, all
surrogate-assisted multi-objective evolutionary algorithms, i.e.,
SS-MOMAs and GS-MOMA, are shown to outperform the
standard NSGA-II on MF1, MF2, MF5, and MF6. MF6
(ZDT4) is generally regarded as a challenging problem and
hence commonly used by many in the literature. Here, we
validate our results on ZDT4 against those obtained by Deb
et al. in [28]. While [28] reported to solve ZDT4 with from
21781 to 22730 exact function evaluations with an achieved
spread measure 7 of 0.332 to 0.422, GS-MOMA requires only
20000 exact evaluations at a competitive spread measure of
0.410±0.046. On MF3 and MF4, some SS-MOMAs perform
competitively or slightly poorer than NSGA-II (see Figs. 11(d)
and 12(d)). On the other hand, GS-MOMA searches more
efﬁciently than all the SS-MOMA variants and NSGA-II on
the 6 benchmark problems considered. Note that GS-MOMA
also outperforms the SS-MOMA-Perfect on a majority of
the MOO benchmarks with respect to all three performance
metrics, thus suggesting the positive synergy of the ensemble
and smoothing surrogate models in the GSM framework.
2) Analyzing the Generalized Evolutionary Framework
in Multi-Objective Optimization: To arrive at better un-
derstanding of the generalized framework in the context of
multi-objective optimization, we analyze next the reliability
and effectiveness of the ensemble (M1) and smoothing (M2)
7The spread metric [72] considers the distance between two extreme ends
of Pareto front as well as the uniformity of distribution for solutions between
the two extremes. This metric may be used for measuring the diversity of
converged Pareto fronts. Note that a lower spread metric is desirable.


<!-- página 10 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
10
surrogate models in contributing to evolutionary search.
The N-RMSE, i..e, see Equation (19), of ﬁtness predic-
tions based on GP, PR, RBF, or ensemble in GS-MOMA
is summarized in Fig. 7. From the results, the ensemble
model, M1, is shown to arrive at low N-RMSE on all the
multi-objective test problems considered, which is consistent
with observations obtained in the single-objective context. M1
generates high reliability predictions in comparison to the
other single surrogate model counterparts, i.e., GP, PR or RBF.
Besides N-RMSE, the solution archiving to replacement
ratio, labeled here as Γ, of the GS-MOMA search is also
reported in Figure 8. Γ indicates the degree of solution
diversity (through archival of new non-dominating solutions)
against search convergence (through the process of Lamarck-
ian learning replacement) in the GS-MOMA search. While
Lamarckian learning helps to speedup convergence towards
the desired Pareto front, the large Γ ratio observed on all
benchmark problems implies frequent discovery of potential
non-dominating solutions when using both M1 and M2 with
local reﬁnements. This suggests ‘bless of uncertainty’ may
take the form of faster search convergence and better solution
diversity in the context of multi-objective evolutionary search.
D. Computational Complexity of GSM Framework
In this subsection, we present an analytical study on the
computational complexity of the GSM framework. The com-
putational effort, referred here by Tcomp, of GS-SOMA or
GS-MOMA is formulated as follows:
Tcomp = GdbNpop
Pr
i=1 Fi + (Gmax −Gdb)[Npop
(Tens + TP R + 2kterm
Pr
i=1 Fi + Toverhead)],
(24)
where:
• Gdb : number of standard SO/MOEA search generations
conﬁgured for building the database of training data
points at the initial search phase of the GSM framework,
• Gmax : maximum number of search generations,
• Npop : population size,
• r : number of objectives to optimize,
• kterm : number of iterations made in the trust-region-
regulated local searches,
• F : original/exact function evaluation cost,
• Tens : time to build M1 i,e. the ensemble model,
• TP R : time to build M2, i.e. the polynomial regression
model, which is not applicable if PR is already built when
constructing M1,
• Toverhead : other additional costs such as for ﬁtness
predictions and ﬁnding nearest points, which are often
negligible.
On the other hand, the computational cost for SS-SOMA or
SS-MOMA variants is:
Tcomp = GdbNpop
Pr
i=1 Fi + (Gmax −Gdb)[Npop
(Tm + kterm
Pr
i=1 Fi + Toverhead)],
(25)
where Tm is the time taken to build the particular surrogate
model used.
Although there are several elements in Equations (24) and
(25), it is worth noting that when working with computation-
ally expensive problems, the most signiﬁcant part contributing
to the total computational effort incurred is F. Hence, when
F is signiﬁcantly large, which is assumed to be fulﬁlled in
any surrogate-assisted optimization framework, Tens, TP R,
Toverhead and Tm are generally considered to be negligible,
otherwise such frameworks should never be used.
V. CONCLUSION
With a plethora of approximation/surrogate modeling ap-
proaches available in the literature, the choice of technique
to use greatly affects the performance of surrogate-assisted
evolutionary searches. It is argued that every approximation
technique introduces some unique characteristics suitable for
modeling some classes of problems accurately but not for
others. Given that a priori knowledge about the problem
landscape is often scarce, the ability to tackle new problems in
a reliable way is of signiﬁcant value. This paper investigates
on a generalized framework that uniﬁes diverse surrogate
models synergistically in the memetic evolutionary search. In
contrast to existing works, the studied memetic framework
emphasizes not only on 1) mitigating the impact of ‘curse
of uncertainty’ robustly, but also 2) beneﬁtting from the ‘bless
of uncertainty’, through the use of ensemble and landscape
smoothing surrogate models, respectively.
The core purpose of proposing any new search strate-
gies, including the GSM framework, is to solve real-world
optimization problems more robustly, effectively and/or ef-
ﬁciently. Hence, to facilitate possible systematic study and
gain deeper understanding of the proposed methods for solv-
ing complex real-world problems plagued with computa-
tionally expensive functions, benchmark problems of diverse
known properties have been employed. In this paper, we
have presented extensive numerical studies on commonly
used single/multi-objective optimization benchmark problems
which have demonstrated the competitiveness of the general-
ized framework. Overall, the ensemble model is shown to be
capable of attaining reliable, accurate surrogate models, while
smoothing model speeds up evolutionary search performance
by traversing through the multi- modal landscape of complex
problems. Statistically, the generalized framework achieved
signiﬁcantly better performance on SOO/MOO when com-
pared to SS-SOMA/MOMA and their underlying SO/MOEA.
Presently, the GSM framework is used for solving real-
world problems plagued with computationally expensive func-
tions, particularly in the ﬁeld of aerodynamic and molecular
structural designs. Based on our experiences with both bench-
mark and real-world problems that range from turbine blade
[7][20] to airfoil designs [8][11][22][32], the observations
obtained from the use of benchmark problems do not deviate
signiﬁcantly from those in the real-world problems we have
experimented. Some of the observations and problems we have
noted when dealing with real-world problems are listed as
follows:
• In contrast to benchmark problems, the time taken to
collect adequate amount of database points when dealing


<!-- página 11 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
11
with real-world problems can be relatively signiﬁcant if
unsupported by sufﬁcient machines capability. A possible
solution is to directly utilize an external database of
previously evaluated design points, if available, instead
of building the database from scratch in the initial Gdb
generations of evolutionary optimization. When existing
database are unavailable, or the design points available
are insufﬁcient for building reliable surrogates, a smaller
Gdb can be used to obtain the initial design points
necessary for the reliable surrogate building to facilitate
time saving.
• When parallel machines capability is available, multi-
level parallelization can be leveraged through the GSM
framework, namely, 1) generation level, i.e., individuals
at the same generation are sent to multiple computing
nodes for evaluation, and 2) individual level, independent
local searches utilizing M1 and M2 respectively, are
executed in parallel. Hence, further acceleration can be
expected.
ACKNOWLEDGMENT
D. Lim and Y. S. Ong would like to thank Honda Research
Institute Europe GmbH for sponsoring this work and members
of Nanyang Technological University, Singapore for providing
the computing resources.
REFERENCES
[1] C. G. Johnson and J. J. R. Caldalda, “Introduction: Genetic Algorithms
in Visual Art and Music,” Leonardo 35(2):175-184, 2002.
[2] S. Mahfoud, G. Mani, “Financial forecasting using genetic algorithms,”
Applied Artiﬁcial Intelligence, 10:543-565, 1996.
[3] D. Simon, “Biogeography-Based Optimization,” page(s): 1-13, Digital
Object Identiﬁer: 10.1109/TEVC.2008.919004.
[4] H. Karahan, H. Ceylan, M. T. Ayvaz, “Predicting rainfall intensity using
a genetic algorithm approach,” Hydrological Processes, 21(4):470-475,
2006.
[5] E. W. Lameijer, T. Baeck, J. N. Kok and A. P. Ijzerman, “Evolutionary
algorithms in drug design,” Natural Computing, 4(3):177-243, 2005.
[6] M. Olhofer, T. Arima, T. Sonoda, and B. Sendhoff, “Optimization of
a stator blade used in a transonic compressor cascade with evolution
strategies,” Adaptive Computing in Design and Manufacture (ACDM),
Springer Verlag, pp. 45-54, 2000.
[7] Y. Jin, M. Olhofer, B. Sendhoff, “A framework for evolutionary op-
timization with approximate ﬁtness function,” IEEE Transactions on
Evolutionary Computation, 6(5):481-494, 2002.
[8] Y. S. Ong, P. B. Nair, and A. J. Keane, “Evolutionary optimization of
computationally expensive problems via surrogate modeling,” American
Institute of Aeronautics and Astronautics Journal, 41(4):687-696, 2003.
[9] Y. Jin, “A comprehensive survey of ﬁtness approximation in evolutionary
computation,” Soft Computing, 9(1):3-12, 2005.
[10] A. Ratle, “Kriging as a surrogate ﬁtness landscape in evolutionary
optimization,” Artiﬁcial Intelligence for Engineering Design Analysis and
Manufacturing, 15(1):37-49, 2001.
[11] Z. Zhou, Y. S. Ong, P. B. Nair, A. J. Keane, and K. Y. Lum, “Com-
bining Global and Local Surrogate Models to Accelerate Evolutionary
Optimization,” IEEE Transactions on Systems, Man and Cybernetics, Part
C: Reviews and Applications, 37(1):66-76, Jan 2007.
[12] R. Smith, B. Dike, and S. Stegmann, “Fitness inheritance in genetic
algorithms,” ACM Symposiums on Applied Computing, pp. 345-350, 1995.
[13] J. H. Chen, D. E. Goldberg, S. Y. Ho, and K. Sastry, “Fitness inheritance
in multi-objective optimization,” Genetic and Evolutionary Computation
Conference, pp. 319-326, 2002.
[14] Y. Jin, M. Olhofer, and B. Sendhoff, “On evolutionary optimization with
approximate ﬁtness functions,” Genetic and Evolutionary Computation
Conference, pp. 786-792, 2000.
[15] M. Emmerich, A. Giotis, M. Oezdenir, T. Baeck, and K. Giannakoglou,
“Metamodel-assisted evolution strategies,” Parallel Problem Solving from
Nature, LNCS 2439, pp. 371-380, 2002.
[16] H. Ulmer, F. Streichert, and A. Zell, “Evolution strategies assisted by
gaussian processes with improved pre-selection criterion,” Proc. of IEEE
Congress on Evolutionary Computation, pp. 692-699, 2003.
[17] H. S. Kim and S. B. Cho, “An efﬁcient genetic algorithms with less
ﬁtness evaluation by clustering,” Congress on Evolutionary Computation,
pp. 887-894, 2001.
[18] Y. Jin and B. Sendhoff, “Reducing ﬁtness evaluations using clustering
techniques and neural networks ensembles,” Genetic and Evolutionary
Computation Conference, LNCS 3102, pp. 688-699, 2004.
[19] J. Branke and C. Schmidt, “Faster convergence by means of ﬁtness
estimation,” Soft Computing, 9(1):13-20, 2005.
[20] L. Gr¨aning, Y. Jin, and B. Sendhoff. “Individual-based management of
meta-models for evolutionary optimization with applications to three-
dimensional blade optimization,” In: S. Yang, Y.-S. Ong, Y. Jin(eds.),
Evolutionary Computation in Dynamic and Uncertain Environments,
pp.225-250, Springer, 2007.
[21] P. K. S. Nain and K. Deb, “Computationally effective search and
optimization procedure using coarse to ﬁne approximation,” Congress
on Evolutionary Computation, pp.2081-2088, 2003.
[22] Y. S. Ong, P. B. Nair and K. Y. Lum, “Max-Min Surrogate-Assisted
Evolutionary Algorithm for Robust Aerodynamic Design,” IEEE Trans-
actions on Evolutionary Computation, 10(4):392-404, August 2006.
[23] Y. S. Ong, P. B. Nair, K. Y. Lum, “Evolutionary algorithm with hermite
radial basis function interpolations for computationally expensive adjoint
solvers,” Computational Optimization and Applications, 39(1):91-119,
January 2008.
[24] K. C. Giannakoglou, D. I. Papadimitriou, I. C. Kampolis, “Aerodynamic
shape design using evolutionary algorithms and new gradient-assisted
metamodels,” Computer Methods in Applied Mechanics and Engineering,
195:6312-6329, 2006.
[25] M. D. Schmidt and H. Lipson, “Coevolution of ﬁtness predictors,”
page(s): 1-14 Digital Object Identiﬁer: 10.1109/TEVC.2008.919006.
[26] J. Knowles, “ParEGO: a hybrid algorithm with on-line landscape ap-
proximation for expensive multiobjective optimization problems,” IEEE
Transcations on Evolutionary Computation, 10(1):50-66, 2006.
[27] D. Jones, M. Schonlau, and W. Welch, “Efﬁcient global optimization of
expensive black-box functions,” Journal of Global Optimization, 13:455-
492, 1998.
[28] K. Deb and P. K. S. Nain, “An evolutionary multi-objective meta-
modeling procedure using artiﬁcial neural networks,” In S. Yang, Y.
S. Ong, and Y. Jin (eds.) Evolutionary Computation in Dynamic and
Uncertain Environments, pp. 297-322, Springer, 2007.
[29] M. Emmerich, K. Giannakoglou, and B. Naujoks, “Single and multi-
objective evolutionary optimization assisted by gaussian random ﬁeld
metamodels,” IEEE Transactions on Evolutionary Computation, 10(4):
421- 439, 2006.
[30] D. Chafekar, L. Shi, K. Rasheed, and J. Xuan, “Multi-objective GA
optimization using reduced models,” IEEE Trans. on Systems, Man, and
Cybernetics, Part C: Reviews and Applications, 9(2):261-265, 2005.
[31] I. Voutchkov and A. J. Keane. “Multiobjective optimization using
surrogates,” Proceedings of the 7th International Conference on Adaptive
Computing in Design and Manufacture, pp. 167-175, Holland, The
M.C.Escher Company, 2006.
[32] Y. S. Ong, P. B. Nair, A. J. Keane, and K. W. Wong, “Surrogate-
Assisted Evolutionary Optimization Frameworks for High-Fidelity En-
gineering Design Problems,” In: Y. Jin(ed.), Knowledge Incorporation in
Evolutionary Computation, Springer Verlag, pp. 307 - 331, 2004.
[33] D. Lim, Y. S. Ong, Y. Jin, and B. Sendhoff, “A study on metamodeling
techniques, ensembles, and multi-surrogates in evolutionary computa-
tion,” Genetic and Evolutionary Computation Conference. London, UK,
pp. 1288-1295, ACM Press, 2007.
[34] A. Samad and K.-Y. Kim, “Multiple surrogate modeling for axial
compressor blade shape optimization,” Journal of Propulsion & Power,
24(2):302-310, 2008.
[35] L. E. Zerpa, N. V. Queipo, S. Pintos, J.-L. Salager, “An optimization
methodology of alkaline-surfactant-polymer ﬂooding processes using ﬁeld
scale numerical simulation and multiple surrogates,” 47:197-208, 2005.
[36] D. Marjavaara, S. Lundstr¨om, W. Shyy, “Hydraulic turbine diffuser
shape optimization by multiple surrogate model approximations of pareto
fronts,” ASME Journal of Fluids Engineering, 129(9):1228-1240, 2007.
[37] N. V. Queipo, R. T. Haftka, W. Shyy, T. Goel, R. Vaidyanathan, P.
K. Tucker, “Surrogate-based analysis and optimization,” Progress in
Aerospace Sciences, 37:59-118, 2001.


<!-- página 12 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
12
[38] E. Sanchez, S. Pintos, N. V. Queipo, “Toward an optimal ensemble
of kernel-based approximations with engineering applications,” Struc-
tural Multidisciplinary Optimization, DOI 10.1007/s00158-007-0159-6,
Accepted May 2007.
[39] A. Samad, K.-D. Lee, K.-Y. Kim, and R. T. Haftka, “Application of
multiple-surrogate model to optimization of a dimpled channel,” 7th
World Congress on Structural and Multidisciplinary Optimization, pp.
2276-2282, 2007.
[40] T. Goel, R. T. Haftka, W. Shyy, N. V. Queipo, “Ensemble of surrogates,”
Structural Multidisciplinary Optimization, 33:199-216, 2007.
[41] E. Acar and M. Rais-Rohani, “Ensemble of metamodels with opti-
mized weight factors,” Structural Multidisciplinary Optimization, DOI
10.1007/s00158-008-0230-y, Accepted December 2007.
[42] K.-H. Liang, X. Yao, and C. Newton, “Combining landscape approxi-
mation and local search in global optimization,” Proceedings of the 1999
Congress on Evolutionary Computation, 2:1514-1520, Piscataway, NJ,
1999.
[43] K.-H. Liang, X. Yao, and C. Newton, “Evolutionary search of approx-
imated n-dimensional landscape,” International Journal of Knowledge-
based Intelligent Engineering Systems, 4(3):172-183, 2000.
[44] Y. S. Ong, Z. Zhou, and D. Lim, “Curse and blessing of uncertainty in
evolutionary algorithm using approximation,” Congress on Evolutionary
Computation, pp. 2928-2935, Vancouver, 2006.
[45] Y. Jin and J. Branke, “Evolutionary optimization in uncertain envi-
ronments - a survey,” IEEE Transactions on Evolutionary Computation,
9(3):303-317, June 2005.
[46] Y. S. Ong and A. J. Keane, “Meta-Lamarckian Learning in Memetic
Algorithm,” IEEE Transactions On Evolutionary Computation, 8(2):99-
110, April 2004.
[47] J. D. Knowles, R. A. Watson, D. W. Corne, “Reducing local optima in
single-objective problems by multi-objectivization,” Proceedings of the
First International Conference on Evolutionary Multi-criterion Optimiza-
tion (EMO’01), pp. 269-283, 2001.
[48] N. Noman and H. Iba, “Accelerating differential evolution using an
adaptive local search,” IEEE Transactions on Evolutionary Computation,
12(1):107-125, 2008.
[49] A. J. Nebro, A. J. Luna, E. Alba, B. Dorronsoro, J. J. Durillo, A. Be-
ham, “AbYSS: Adapting Scatter Search to Multiobjective Optimization,”
page(s): 1-19 Digital Object Identiﬁer: 10.1109/TEVC.2007.913109.
[50] Y. S. Ong, M.H. Lim, N. Zhu and K. W. Wong, Classiﬁcation of
Adaptive Memetic Algorithms: A Comparative Study,” IEEE Transactions
on Systems, Man and Cybernetics - Part B, 36(1):141-152, 2006.
[51] Y. Liu, X. Yao and T. Higuchi, “Evolutionary Ensembles with Negative
Correlation Learning,” IEEE Transactions on Evolutionary Computation,
4(4):380-387, 2000.
[52] J. D. Pinter, Global Optimization in Action, Kluwer, 1996.
[53] J. F. Rodriguez, J. E. Renaud, and L. T. Watson, “Convergence of trust
region augmented lagrangian methods using variable ﬁdelity approxima-
tion data,” Structural Optimization, 15(3-4):141-156, 1998.
[54] C. T. Lawrence and A. L. Tits, “A computationally efﬁcient feasible
sequential quadratic programming algorithm,” Society for Industrial and
Applied Mathematics, 11(4):1092-1118, 2001.
[55] D. J. C. Mackay, “Introduction to gaussian processes,” Neural Networks
and Machine Learning, 168:133-165, 1998.
[56] F. H. Lesh, “Multi-dimensional least-square polynomial curve ﬁtting,”
Communications of ACM, 2(9):29-30, 1959.
[57] C. Bishop, Neural networks for pattern recognition, Oxford University
Press, 1995.
[58] H. Ishibuchi and T. Murata, “Multi-objective genetic local search algo-
rithm,” IEEE International Conference on Evolutionary Computation, pp.
119-124, 1996.
[59] A. Jaszkiewicz, “Genetic local search for multiple objective combina-
torial optimization,” Technical report RA-014/98, Institute of Computing
Science, Poznan University of Technology, 1998.
[60] J. Knowles and D. Corne, “Memetic algorithms for multiobjective
optimization: issues, methods and prospects,” in W. E. Hart, N. Krasnogor,
J. E. Smith , editors, Recent Advances in Memetic Algorithms, pp. 313-
352, 2005.
[61] N. Alexandrov, J. E. Dennis, R. M. Lewis, and V. Torczon, “A trust
region framework for managing the use of approximation models in
optimization,” Journal on Structural Optimization, 15(1):16-23, 1998.
[62] J. G. Digalakis and K. G. Margaritis, “On benchmarking functions for
genetic algorithms,” Intern. J. Computer Math., 77(4):481-506, 2001.
[63] P. N. Suganthan, N. Hansen, J. J. Liang, K. Deb, Y. P. Chen, A. Auger
and S. Tiwari, “Problem Deﬁnitions and Evaluation Criteria for the CEC
2005 Special Session on Real-Parameter Optimization,” Technical Report,
Nanyang Technological University, Singapore, May 2005 AND KanGAL
Report No. 2005005, IIT Kanpur, India.
[64] E. Zitzler, K. Deb, and L. Thiele, “Comparison of multi-objective
evolutionary algorithms: empirical results,” Evolutionary Computation,
8(2):173-195, 2000.
[65] K. Deb, S. Agrawal, A. Pratab, and T. Meyarivan, “A fast elitist non-
dominated sorting genetic algorithm for multi-objective optimization:
NSGA-II,” Parallel Problem Solving from Nature VI Conference, LNCS
1917, pp. 849-858, 2000.
[66] E. Zitzler, L. Thiele, M. Laumanns, C. M. Foneseca, and V. Grunert
da Fonseca, “Performance Assessment of Multiobjective Optimizers: An
Analysis and Review,” IEEE Transactions on Evolutionary Computation,
7(2):117-132, 2003.
[67] C. A. Coello Coello, D. A. Van Veldhuizen, and G. B. Lamont,
Evolutionary algorithms for solving multi-objective problems, New York:
Kluwer Academic, 2002.
[68] D. A. Van Veldhuizen and G. B. Lamont, “Evolutionary computation
and convergence to a Pareto front,” in J. R. Koza, editor, Late Breaking
Papers at the Genetic Programming, pp. 221-228, 1998.
[69] D. A. Van Veldhuizen, “Multiobjective evolutionary algorithms: class-
siﬁcations, analysis, and new innovations,” Ph. D. Thesis, Air Force
Institute of Technology Dayton, OH, 1999.
[70] E. Zitzler, “Evolutionary algorithms for multiobjective optimization:
methods and applications,” PhD thesis, Swiss Federal Institute of Tech-
nology (ETH) Zurich, Switzerland, TIK-Schriftenreihe Nr. 30, Diss ETH
No. 13398, Shaker Verlag, Aachen, Germany, 1999.
[71] E. Zitzler and L. Thiele, “Multiobjective optimization using evolutionary
algorithms a comparative case study”, Fifth International Conference on
Parallel Problem Solving from Nature (PPSN-V), pp. 292-301, Springer,
1998.
[72] K. Deb, Multi-objective optimization using evolutionary algorithms,
First Edition, Chichester, UK: Wiley, 2001.
[73] R. G. Regis and C. A. Shoemaker, “Local function approximation in
evolutionary algorithms for the optimization of costly functions,” IEEE
Transactions on Evolutionary Computation, 8:490-505, 2004.
[74] H.-M. Gutmann, On the semi-norm of radial basis function interpolants,
Dept. Applied Math. Theor. Phy., Univ. Cambridge, Cambridge, U.K.,
Tech. Rep. DAMTP 2000/NA04, 2000.
APPENDIX I
APPROXIMATION/SURROGATE MODELING TECHNIQUES
Here, we provide a brief review on three different surro-
gate modeling techniques used in this paper, namely: Krig-
ing/Gaussian Process (GP), Polynomial Regression (PR), and
Radial Basis Function (RBF). Throughout this section, let
D = {xi, ti}, i = 1 . . . m denote the training dataset, where
xi ∈Rd is an input design vector and ti ∈R is the
corresponding target value.
A. Kriging/Gaussian Process (GP)
The GP surrogate model [55] assumes the presence of an
unknown true modeling function f(x) and an additive noise
term v to account for anomalies in the observed data. Thus:
t = f(x) + v
(26)
The standard analysis requires the speciﬁcation of prior
probabilities on the modeling function and the noise model.
From a stochastic process viewpoint, the collection t =
{t1, t2, ..., tm} is called a Gaussian process if every subset
of t has a joint Gaussian distribution. More speciﬁcally,
P(t|C, {xm}) = 1
Z exp

−1
2(t −µ)T C−1(t −µ)

(27)
where C is a covariance matrix parameterized in terms of
hyperparameters θ, i.e., Cij = k(xi, xj; θ) and µ is the
process mean. The Gaussian process is characterized by this


<!-- página 13 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
13
covariance structure since it incorporates prior beliefs both
about the true underlying function as well as the noise model.
In the present study, we use the following exponential covari-
ance model
k(xi, xj) = e−(xi−xj)T Θ(xi−xj) + θd+1
(28)
where Θ = diag{θ1, θ2, ..., θd} ∈Rd×d is a diagonal matrix of
undetermined hyperparameters, and θd+1 ∈R is an additional
hyperparameter arising from the assumption that noise in the
dataset is Gaussian (and output dependent). We shall hence-
forth use the symbol θ to denote the vector of undetermined
hyperparameters, i.e., θ = {θ1, θ2, ..., θd+1}. In practice, the
undetermined hyperparameters are tuned to the data using the
evidence maximization framework. Once the hyperparameters
have been estimated from the data, predictions can be readily
made for a new testing point.
B. Polynomial Regression (PR)
In PR metamodeling technique [56], we deﬁne an exponent
vector ε containing positive integers (π1, π2, . . . , πd) and de-
ﬁne xε
i as an exponent input vector (xi1
π1, xi2
π2, . . . , xid
πd).
Given a set of exponent vectors ε1, ε2, . . . , εo and the set
of data (xi, ti), where i = 1, 2, . . . , m, the polynomial model
of (o −1)th order has the form:
ˆti = C1xε1
i + C2xε2
i + . . . + Cmxεo
i
(29)
where C1, C2, . . . , Co are the coefﬁcient vectors to be esti-
mated, and Cj = (cj1, cj2, . . . , cjd), j = 1, 2, . . . , o.
The least square method is then used to estimate the
coefﬁcients of the polynomial model. By deﬁnition, the least
square error E to be minimized is:
E =
m
X
i=1
[ti −ˆti]2
(30)
It may be easily shown that ti = f(xi), and by multiplying
both sides of Equation (29) with xεj
i
and taking the sum of
m pairs of input-output data, we arrive at
C1
X
i
xε1+εj
i
+ . . . + Co
X
i
xεo+εj
i
=
X
i
tixεj
i
(31)
For j = 1, 2, . . . , o, the polynomial model for the training
dataset can be represented in the matrix notation as follows
AγT = bT
(32)
where
A =


P
i xε1+ε1
i
. . .
P
i xε1+εo
i
...
...
P
i xεo+ε1
i
. . .
P
i xεo+εo
i


(33)
b = (
X
tixε1
i , . . . ,
X
tixεo
i )
(34)
γ = (C1, C2, . . . , Co)
(35)
Then the coefﬁcient matrix of the polynomial is:
γ = (A−1bT )T
(36)
Let Bi = (xε1
i , . . . , xεo
i ), the following equations may be
derived:
• A = P
i BT
i Bi
• b = P
i tiBi
• ˆti = γ.BT
i
The predicted output for a new input pattern is then given
by ˆti = γ.BT
i .
C. Radial Basis Function
The surrogate models of RBF used in this paper are inter-
polating radial basis function networks of the form
ˆt = ˆf(x) =
m
X
i=1
αiK(||x −xi||)
(37)
where K(||x −xi||) : Rd
→R is a RBF and α =
{α1, α2, . . . , αm} ∈Rm denotes the vector of weights. Hence,
the number of hidden nodes in the RBF here is as many as
the number of training points.
Typical choices for the kernel include linear splines, cu-
bic splines, multiquadrics, thin-plate splines, and Gaussian
functions [57]. Recent studies in [73][74], indicate that the
linear, cubic, and thin plate spline RBFs have better theoretical
properties than the multiquadric and Gaussian RBFs. Hence,
in this paper, we opt to use linear spline kernel function.
The structure of some commonly used radial basis kernels
and their parameterization are shown in Table XIX Given a
suitable kernel, the weight vector can be computed by solving
the linear algebraic system of equations Kα = t, where
t = {t1, t2, . . . , tm} ∈Rm denotes the vector of outputs
and K ∈Rm×m denotes the Gram matrix formed using the
training inputs (i.e., the ijth element of K is computed as
K(||xi −xj||)).
APPENDIX II
SINGLE-OBJECTIVE BENCHMARK FUNCTIONS
Single-objective benchmark functions used in this paper are
presented in this section. The shifted and/or rotated functions
are taken from [62] and [63]. Note that due to the long
description for F7-F10, reader is referred directly to [63]
for those functions. From F4-F6, the following nomenclature
applies:
o = [o1, o2, . . . , od]: the shifted global optimum
M: linear transformation matrix, obtained from [63].
F1: Ackley
F(x) = 20 + e −20e
−0.2
s
1
d
d
P
i=1
x2
i −e
1
d
d
P
i=1
cos(2πxi)
(38)
−32.768 ≤xi ≤32.768, i = 1, 2, . . . , d.
Global optimum x∗
i = 0.0 for i = 1, . . . , d, F(x∗) = 0.0


<!-- página 14 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
14
F2: Griewank
F(x) = 1 + Pd
i=1 x2
i /4000 −Qd
i=1 cos(xi/
√
i)
(39)
−600 ≤xi ≤600, i = 1, 2, . . . , d.
Global optimum x∗
i = 0.0 for i = 1, . . . , d, F(x∗) = 0.0
F3: Rosenbrock
F(x) = Pd−1
i=1 (100 × (xi+1 −x2
i )2 + (1 −xi)2)
(40)
−2.048 ≤xi ≤2.048, i = 1, 2, . . . , d.
Global optimum x∗
i = 1.0 for i = 1, . . . , d, F(x∗) = 0.0
F4: Shifted Rotated Rastrigin
F(x) = Pd
i=1(z2
i −10cos(2πzi) + 10) −330
(41)
z = (x −o) ∗M,
−5 ≤xi ≤5, i = 1, 2, . . . , d.
Global optimum x∗= o, F(x∗) = fbias = −330.
F5: Shifted Rotated Weierstrass
F(x) = Pd
i=1(Pkmax
k=0 [akcos(2πbk(zi + 0.5))])
(42)
−d Pkmax
k=0 [akcos(2πbk.0.5)] + 90
z = (x −o) ∗M,
−0.5 ≤xi ≤0.5, i = 1, 2, . . . , d.
Global optimum x∗= o, F(x∗) = fbias = 90. a = 0.5,
b = 3, kmax=20.
F6: Shifted Expanded Griewank plus Rosenbrock
F(x) = F2(F3(z1, z2)) + F2(F3(z2, z3)) + . . .
(43)
+F2(F3(zd−1, zd)) + F2(F3(zd, z1)) −130
z = x −o + 1,
−3 ≤xi ≤1, i = 1, 2, . . . , d.
Global optimum x∗= o, F(x∗) = fbias = −130
F7: Hybrid Composition Function(refer to F15 in [63])
F8: Rotated Hybrid Composition Function of F7(refer to
F16 in [63])
F9: Rotated Hybrid Composition Function with Narrow
Basin Global Optimum(refer to F19 in [63])
F10: Non-continuous Rotated Hybrid Composition Func-
tion(refer to F23 in [63])


<!-- página 15 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
15
−5
−4
−3
−2
−1
0
1
2
3
4
5
−5
0
5
10
15
20
25
30
35
40
45
x
f(x)
 
 
exact function
data points
   approximated function
starting point
local optimum found
exact local optimum
(a) ‘Curse of uncertainty’ in single-objective EA using surrogates. Ap-
proximated function in the ﬁgure is obtained using spline interpolation
technique.
−5
−4
−3
−2
−1
0
1
2
3
4
5
0
5
10
15
20
25
30
35
40
45
x
f(x)
 
 
exact function
data points
  approximated function
starting point
local optimum found
exact local optimum
(b) ‘Bless of uncertainty’ in single-objective EA using surrogates.
Approximated function in the ﬁgure is obtained using a low order
Polynomial Regression.
Fig. 1.
Curse and bless of uncertainty in single-objective EA using surrogates.


<!-- página 16 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
16
f1
f2
Pareto
Front
X
x
xx
x
x
o
o o
o
o
X1
X
X2
o
(a) ‘Curse of uncertainty’ in multi ob-
jective EA using surrogates.
f1
f2
Pareto
Front
x
x
x
x
x
x
x
o
o o
o
o
x
X3
X4
o
(b) ‘Bless of uncertainty’ in multi objec-
tive EA using surrogates.
Initial solutions
Pareto solutions for MOEA 
without using surrogates
Pareto solutions for MOEA 
using surrogates
o
x
Fig. 2.
Curse and bless of uncertainty in multi-objective EA using surrogates.


<!-- página 17 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
17
f1
f2
Pareto
Front
2
xopt
1
xopt
x
(a) An example of the case where
replacement is performed only
once by GS-MOMA. (x1
opt ⪯
x) ∧(x1
opt ⪯x2
opt) ∧(x ∼
x2
opt). x1
opt replaces x.
f1
f2
Pareto
Front
1xopt
2
xopt
x
(b) An example of the case
where two subsequent replace-
ments are performed by GS-
MOMA. (x1
opt ⪯x) ∧(x2
opt ⪯
x1
opt). x1
opt replaces x, followed
by x2
opt replaces x.
f1
f2
Pareto
Front
2
xopt
1
xopt
x
(c) An example of the case where
both replacement and archiving
are performed by GS-MOMA.
(x1
opt ⪯x) ∧(x2
opt ⪯x) ∧
(x1
opt ∼x2
opt). x1
opt replaces
x, x2
opt is archived in Al.
f1
f2
Pareto
Front
2
xopt
1
xopt
x
(d) An example of the case where
archiving is performed only once
by GS-MOMA. (x ∼x1
opt) ∧
(x ∼x2
opt) ∧(x1
opt ⪯x2
opt).
x1
opt is archived in Al.
f1
f2
Pareto
Front
2
xopt
1xopt
x
(e) An example of the case where
archiving is performed twice by GS-
MOMA. (x
∼
x1
opt) ∧(x
∼
x2
opt) ∧(x1
opt ∼x2
opt). Both x1
opt
and x2
opt are archived in Al.
f1
f2
Pareto
Front
1
2
opt
opt
x
x
x
==
==
(f) An example of the case where
neither replacement nor archiving
is performed. No new optimum is
found.
Fig. 3.
Examples of the 6 different actions taken by the Replace&Archive scheme in GS-MOMA for corresponding results of local searches.


<!-- página 18 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
18
0
1
2
3
4
5
6
7
8
1.4
1.6
1.8
2
2.2
2.4
2.6
2.8
3
3.2
Exact Function Evaluations ( x1e3 )
Fitness Value ( Natural Log )
GS−SOMA
SS−SOMA−AV
SS−SOMA−Perfect
(a) F1
0
1
2
3
4
5
6
7
8
−10
−8
−6
−4
−2
0
2
4
6
Exact Function Evaluations ( x1e3 )
Fitness Value ( Natural Log )
GS−SOMA
SS−SOMA−AV
SS−SOMA−Perfect
(b) F2
0
1
2
3
4
5
6
7
8
3
3.5
4
4.5
5
5.5
6
6.5
7
7.5
8
Exact Function Evaluations ( x1e3 )
Fitness Value ( Natural Log )
GS−SOMA
SS−SOMA−AV
SS−SOMA−Perfect
(c) F3
0
1
2
3
4
5
6
7
8
−150
−100
−50
0
50
Exact Function Evaluations ( x1e3 )
Fitness Value 
GS−SOMA
SS−SOMA−AV
SS−SOMA−Perfect
(d) F4
0
1
2
3
4
5
6
7
8
4.75
4.8
4.85
4.9
Exact Function Evaluations ( x1e3 )
Fitness Value (Natural Log)
GS−SOMA
SS−SOMA−AV
SS−SOMA−Perfect
(e) F5
0
1
2
3
4
5
6
7
8
−120
−110
−100
−90
−80
−70
−60
−50
Exact Function Evaluations ( x1e3 )
Fitness Value
GS−SOMA
SS−SOMA−AV
SS−SOMA−Perfect
(f) F6
0
1
2
3
4
5
6
7
8
6.35
6.4
6.45
6.5
6.55
6.6
6.65
6.7
6.75
6.8
6.85
Exact Function Evaluations ( x1e3 )
Fitness Value (Natural Log)
GS−SOMA
SS−SOMA−AV
SS−SOMA−Perfect
(g) F7
0
1
2
3
4
5
6
7
8
5.8
5.9
6
6.1
6.2
6.3
6.4
Exact Function Evaluations ( x1e3 )
Fitness Value (Natural Log)
GS−SOMA
SS−SOMA−AV
SS−SOMA−Perfect
(h) F8
0
1
2
3
4
5
6
7
8
6.84
6.86
6.88
6.9
6.92
6.94
6.96
6.98
7
7.02
Exact Function Evaluations ( x1e3 )
Fitness Value (Natural Log)
GS−SOMA
SS−SOMA−AV
SS−SOMA−Perfect
(i) F9
0
1
2
3
4
5
6
7
8
6.9
6.95
7
7.05
7.1
7.15
7.2
7.25
7.3
7.35
7.4
Exact Function Evaluations ( x1e3 )
Fitness Value (Natural Log)
GS−SOMA
SS−SOMA−AV
SS−SOMA−Perfect
(j) F10
Fig. 4.
Convergence trends for F1-F10 obtained from GS-SOMA, SS-SOMA-Perfect, and SS-SOMA-AV.


<!-- página 19 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
19
F1
F2
F3
F4
F5
F6 
F7
F8
F9
F10
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
Benchmark Problem
Normalized RMSE
Gaussian Process (GP)
Polynomial Regression (PR)
Radial Basis Function (RBF)
Ensemble Model (M1)
Fig. 5.
The normalized RMSE by GP, PR, RBF, and weighted average
ensemble.


<!-- página 20 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
20
F1
F2
F3
F4
F5
F6
F7
F8 
F9 
F10
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
Benchmark Problem
Normalized Fitness Improvement
Fitness improvement contributed by M1
Fitness improvement contributed by M2
Fig. 6.
The normalized ﬁtness improvement during the runs of GS-SOMA
contributed by M1 (ImpM1) and M2 (ImpM2).


<!-- página 21 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
21
MF1
MF2
MF3
MF4
MF5
MF6
0
0.1
0.2
0.3
0.4
0.5
0.6
0.7
Benchmark Problem
Normalized RMSE
Gaussian Process (GP)
Polynomial Regression (PR)
Radial Basis Function (RBF)
Ensemble Model (M1)
Fig. 7.
The normalized RMSE by GP, PR, RBF, and weighted average
ensemble on MF1-MF6.


<!-- página 22 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
22
MF1
MF2
MF3
MF4
MF5
MF6
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
Benchmark Problem
Ratio of Archiving to Replacement
Replacement
Archiving
Fig. 8.
Archiving to Replacement Ratio of GS-MOMA on MF1-MF6.


<!-- página 23 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
23
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
0
0.2
0.4
0.6
0.8
1
1.2
1.4
f1
f2
 
 
(a) NSGA-II
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
f2
 
 
(b) GS-MOMA
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
f2
(c) SS-MOMA-I
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
f2
(d) SS-MOMA-II
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
0
0.2
0.4
0.6
0.8
1
1.2
1.4
f1
f2
 
 
(e) SS-MOMA-Perfect
Fig. 9.
Pareto Front evolved for benchmark problem MF1 in NSGA-II, GS-MOMA, SS-MOMA-I, SS-MOMA-II, and SS-MOMA-Perfect.


<!-- página 24 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
24
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
0
0.2
0.4
0.6
0.8
1
1.2
1.4
f1
f2
 
 
(a) NSGA-II
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
f2
(b) GS-MOMA
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
f2
(c) SS-MOMA-I
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
f2
(d) SS-MOMA-II
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
0
0.2
0.4
0.6
0.8
1
f1
f2
(e) SS-MOMA-Perfect
Fig. 10.
Pareto Front evolved for benchmark problem MF2 in NSGA-II, GS-MOMA, SS-MOMA-I, SS-MOMA-II, and SS-MOMA-Perfect.


<!-- página 25 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
25
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
−1
−0.5
0
0.5
1
1.5
f1
f2
 
 
(a) NSGA-II
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
−0.8
−0.6
−0.4
−0.2
0
0.2
0.4
0.6
0.8
1
f1
f2
 
 
(b) GS-MOMA
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
−0.8
−0.6
−0.4
−0.2
0
0.2
0.4
0.6
0.8
1
1.2
f1
f2
 
 
(c) SS-MOMA-I
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
−1
−0.5
0
0.5
1
1.5
f1
f2
 
 
(d) SS-MOMA-II
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
−0.8
−0.6
−0.4
−0.2
0
0.2
0.4
0.6
0.8
1
1.2
f1
f2
 
 
(e) SS-MOMA-Perfect
Fig. 11.
Pareto Front evolved for benchmark problem MF3 in NSGA-II, GS-MOMA, SS-MOMA-I, SS-MOMA-II, and SS-MOMA-Perfect.


<!-- página 26 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
26
0.4
0.5
0.6
0.7
0.8
0.9
1
0
1
2
3
4
5
6
f1
f2
(a) NSGA-II
0.4
0.5
0.6
0.7
0.8
0.9
1
0
0.5
1
1.5
2
2.5
3
3.5
4
f1
f2
(b) GS-MOMA
0.4
0.5
0.6
0.7
0.8
0.9
1
0
0.5
1
1.5
2
2.5
3
3.5
4
4.5
f1
f2
(c) SS-MOMA-I
0.4
0.5
0.6
0.7
0.8
0.9
1
0
1
2
3
4
5
6
7
f1
f2
(d) SS-MOMA-II
0.4
0.5
0.6
0.7
0.8
0.9
1
0
1
2
3
4
5
6
f1
f2
(e) SS-MOMA-Perfect
Fig. 12.
Pareto Front evolved for benchmark problem MF4 in NSGA-II, GS-MOMA, SS-MOMA-I, SS-MOMA-II, and SS-MOMA-Perfect.


<!-- página 27 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
27
0
0.5
1
1.5
2
2.5
3
0
1
2
3
0
0.5
1
1.5
2
2.5
3
f1
f2
f3
(a) NSGA-II
0
0.5
1
1.5
2
0
0.5
1
1.5
2
0
0.5
1
1.5
2
2.5
3
f1
f2
f3
(b) GS-MOMA
0
0.5
1
1.5
2
0
0.5
1
1.5
2
0
0.5
1
1.5
2
2.5
3
3.5
f1
f2
f3
(c) SS-MOMA-I
0
0.5
1
1.5
2
0
0.5
1
1.5
2
0
0.5
1
1.5
2
2.5
3
3.5
f1
f2
f3
(d) SS-MOMA-II
0
0.5
1
1.5
2
2.5
0
0.5
1
1.5
2
2.5
0
0.5
1
1.5
2
2.5
3
3.5
f1
f2
f3
(e) SS-MOMA-Perfect
Fig. 13.
Pareto Front evolved for benchmark problem MF5 in NSGA-II, GS-MOMA, SS-MOMA-I, SS-MOMA-II, and SS-MOMA-Perfect.


<!-- página 28 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
28
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
0
0.5
1
1.5
2
2.5
3
3.5
4
4.5
f1
f2
 
 
(a) NSGA-II
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
0
0.2
0.4
0.6
0.8
1
1.2
1.4
f1
f2
 
 
(b) GS-MOMA
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
0
0.2
0.4
0.6
0.8
1
1.2
1.4
1.6
1.8
2
f1
f2
 
 
(c) SS-MOMA-I
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
0
0.5
1
1.5
2
2.5
f1
f2
 
 
(d) SS-MOMA-II
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
0
0.2
0.4
0.6
0.8
1
1.2
1.4
1.6
f1
f2
 
 
(e) SS-MOMA-Perfect
Fig. 14.
Pareto Front evolved for benchmark problem MF6 in NSGA-II, GS-MOMA, SS-MOMA-I, SS-MOMA-II, and SS-MOMA-Perfect.


<!-- página 29 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
29
A
B
C
D
E
0.07
0.08
0.09
0.1
0.11
0.12
0.13
0.14
0.15
Generational Distance (GD)
Algorithm
(a) Generational Distance (GD)
A
B
C
D
E
0.6
0.65
0.7
0.75
0.8
0.85
0.9
0.95
1
Maximum Spread (MS)
Algorithm
(b) Maximum Spread (MS)
A
B
C
D
E
0.9
1
1.1
1.2
1.3
1.4
Hypervolume Ratio (HR)
Algorithm
(c) Hypervolume Ratio (HR)
Fig. 15.
Generational Distance(GD), Maximum Spread(MS), and Hypervolume Ratio(HR) performance metrics for benchmark problem MF1. (A:NSGA-II,
B:GS-MOMA, C:SS-MOMA-I, D:SS-MOMA-II, E:SS-MOMA-Perfect)


<!-- página 30 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
30
A
B
C
D
E
0.1
0.12
0.14
0.16
0.18
0.2
0.22
0.24
0.26
Generational Distance (GD)
Algorithm
(a) Generational Distance (GD)
A
B
C
D
E
0.55
0.6
0.65
0.7
0.75
0.8
0.85
0.9
0.95
1
Maximum Spread (MS)
Algorithm
(b) Maximum Spread (MS)
A
B
C
D
E
0
0.2
0.4
0.6
0.8
1
1.2
Hypervolume Ratio (HR)
Algorithm
(c) Hypervolume Ratio (HR)
Fig. 16.
Generational Distance(GD), Maximum Spread(MS), and Hypervolume Ratio(HR) performance metrics for benchmark problem MF2. (A:NSGA-II,
B:GS-MOMA, C:SS-MOMA-I, D:SS-MOMA-II, E:SS-MOMA-Perfect)


<!-- página 31 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
31
A
B
C
D
E
0.07
0.08
0.09
0.1
0.11
0.12
0.13
0.14
0.15
0.16
0.17
Generational Distance (GD)
Algorithm
(a) Generational Distance (GD)
A
B
C
D
E
0.55
0.6
0.65
0.7
0.75
0.8
0.85
0.9
0.95
1
Maximum Spread (MS)
Algorithm
(b) Maximum Spread (MS)
A
B
C
D
E
0.5
1
1.5
2
2.5
3
3.5
4
4.5
5
5.5
Hypervolume Ratio (HR)
Algorithm
(c) Hypervolume Ratio (HR)
Fig. 17.
Generational Distance(GD), Maximum Spread(MS), and Hypervolume Ratio(HR) performance metrics for benchmark problem MF3. (A:NSGA-II,
B:GS-MOMA, C:SS-MOMA-I, D:SS-MOMA-II, E:SS-MOMA-Perfect)


<!-- página 32 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
32
A
B
C
D
E
0
0.5
1
1.5
2
Generational Distance (GD)
Algorithm
(a) Generational Distance (GD)
A
B
C
D
E
0.4
0.5
0.6
0.7
0.8
0.9
1
Maximum Spread (MS)
Algorithm
(b) Maximum Spread (MS)
A
B
C
D
E
0.2
0.4
0.6
0.8
1
1.2
1.4
1.6
1.8
2
Hypervolume Ratio (HR)
Algorithm
(c) Hypervolume Ratio (HR)
Fig. 18.
Generational Distance(GD), Maximum Spread(MS), and Hypervolume Ratio(HR) performance metrics for benchmark problem MF4. (A:NSGA-II,
B:GS-MOMA, C:SS-MOMA-I, D:SS-MOMA-II, E:SS-MOMA-Perfect)


<!-- página 33 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
33
A
B
C
D
E
0.105
0.11
0.115
0.12
0.125
0.13
0.135
0.14
Generational Distance (GD)
Algorithm
(a) Generational Distance (GD)
A
B
C
D
E
0.999
0.9991
0.9992
0.9993
0.9994
0.9995
0.9996
0.9997
0.9998
0.9999
1
Values
Algorithm
(b) Maximum Spread (MS)
A
B
C
D
E
0.8
0.85
0.9
0.95
1
1.05
1.1
1.15
Hypervolume Ratio (HR)
Algorithm
(c) Hypervolume Ratio (HR)
Fig. 19.
Generational Distance(GD), Maximum Spread(MS), and Hypervolume Ratio(HR) performance metrics for benchmark problem MF5. (A:NSGA-II,
B:GS-MOMA, C:SS-MOMA-I, D:SS-MOMA-II, E:SS-MOMA-Perfect)


<!-- página 34 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
34
A
B
C
D
E
0.1
0.15
0.2
0.25
Generational Distance (GD)
Algorithm
(a) Generational Distance (GD)
A
B
C
D
E
0.2
0.3
0.4
0.5
0.6
0.7
0.8
0.9
1
Maximum Spread (MS)
Algorithm
(b) Maximum Spread (MS)
A
B
C
D
E
0.5
1
1.5
2
2.5
3
3.5
4
Hypervolume Ratio (HR)
Algorithm
(c) Hypervolume Ratio (HR)
Fig. 20.
Generational Distance(GD), Maximum Spread(MS), and Hypervolume Ratio(HR) performance metrics for benchmark problem MF6. (A:NSGA-II,
B:GS-MOMA, C:SS-MOMA-I, D:SS-MOMA-II, E:SS-MOMA-Perfect)


<!-- página 35 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
35
TABLE I
ACTIONS TAKEN BY THE Replace&Archive SCHEME IN GS-MOMA FOR CORRESPONDING RESULTS OF LOCAL SEARCHES. NOTE THAT IRRELEVANT
CASES HAVE BEEN EXCLUDED FOR BREVITY.
x1
opt vs x
x2
opt vs x
x1
opt vs x2
opt
Actions taken by GS-MOMA
⪯
⪯
⪯
x = x1
opt
⪯
⪯
≻
x = x2
opt
⪯
⪯
∼
x = x1
opt, archive x2
opt
⪯
⪯
==
x = x1
opt
⪯
==
⪯
x = x1
opt
⪯
∼
⪯
x = x1
opt
⪯
∼
∼
x = x1
opt, archive x2
opt
==
⪯
≻
x = x2
opt
==
==
==
No changes
==
∼
∼
Archive x2
opt
∼
⪯
≻
x = x2
opt
∼
⪯
∼
x = x2
opt, archive x1
opt
∼
==
∼
Archive x1
opt
∼
∼
⪯
Archive x1
opt
∼
∼
≻
Archive x2
opt
∼
∼
∼
Archive x1
opt and x2
opt
∼
∼
==
Archive x1
opt


<!-- página 36 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
36
TABLE II
THE BENCHMARK PROBLEMS USED (F1-F10) FOR THE EMPIRICAL STUDY
OF SINGLE-OBJECTIVE OPTIMIZATION.
Benchmark
Description
Global
Problem
Optimum
f(x∗)
F1
Ackley
0.0
F2
Griewank
0.0
F3
Rosenbrock
0.0
F4
Shifted Rotated Rastrigin (F10 in [63])
-330.0
F5
Shifted Rotated Weierstrass (F11 in [63])
90.0
F6
Shifted Expanded Griewank
-130.0
plus Rosenbrock (F13 in [63])
F7
Hybrid Composition Function (F15 in [63])
120.0
F8
Rotated Hybrid Composition Function (F16 in [63])
120.0
F9
Rotated Hybrid Composition Function
10.0
with Narrow Basin Global Optimum (F19 in [63])
F10
Non-continuous Rotated Hybrid
360.0
Composition Function (F23 in [63])


<!-- página 37 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
37
TABLE III
DEFINITION OF THE SINGLE-OBJECTIVE MAS (SOMAS) COMPARED.
Algorithms
Deﬁnition
GA
No surrogate is used
SS-SOMA-GP
Single surrogate SOMA with M1: GP
SS-SOMA-PR
Single surrogate SOMA with M1: PR
SS-SOMA-RBF
Single surrogate SOMA with M1: RBF
SS-SOMA-Perfect
Single surrogate SOMA with M1: Perfect model
GS-SOMA
Generalized surrogate SOMA with
M1: weighted-average ensemble of GP, PR, and RBF
M2: PR


<!-- página 38 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
38
TABLE IV
SETTING OF EXPERIMENTS FOR GA, SS-SOMA, SS-SOMA-PERFECT,
AND GS-SOMA.
Parameters Setting
Population size (Npop)
100
Crossover probability (Pcross)
0.9
Mutation probability (Pmut)
0.1
Maximum number of exact evaluations
8000
Evolutionary operators
uniform crossover & mutation,
elitism and ranking selection
Number of trust region iteration(kterm)
for SS-SOMA and GS-SOMA
3
Database building phase (Gdb)
for SS-SOMA and GS-SOMA
20
(in number of generations)
Number of independent runs
20


<!-- página 39 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
39
TABLE V
STATISTICS OF THE FINAL SOLUTION QUALITY AT THE END OF 8000 EXACT FUNCTION EVALUATIONS FOR F1 USING GA, SS-SOMA-GP,
SS-SOMA-PR, SS-SOMA-RBF, AND GS-SOMA.
Optimization
Algorithm
Statistical Values
Mean
Std. Dev.
Median
Best
Worst
GA
1.24e+01
9.50e-01
1.23e+01
1.12e+01
1.42e+01
SS-SOMA-GP
6.43e+00
9.73e-01
3.98e+00
2.87e+00
1.56e+01
SS-SOMA-PR
1.39e+00
1.93e-01
1.36e+00
1.14e+00
1.75e+00
SS-SOMA-RBF
4.91e+00
7.57e-01
4.86e+00
3.78e+00
6.09e+00
GS-SOMA
3.58e+00
5.09e-01
3.67e+00
2.87e+00
4.28e+00


<!-- página 40 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
40
TABLE VI
STATISTICS OF THE FINAL SOLUTION QUALITY AT THE END OF 8000 EXACT FUNCTION EVALUATIONS FOR F2 USING GA, SS-SOMA-GP,
SS-SOMA-PR, SS-SOMA-RBF, AND GS-SOMA.
Optimization
Algorithm
Statistical Values
Mean
Std. Dev.
Median
Best
Worst
GA
4.58e+01
8.61e+00
4.67e+01
2.15e+01
6.19e+01
SS-SOMA-GP
1.79e+01
8.58e+00
1.07e+01
5.15e-09
3.00e+01
SS-SOMA-PR
1.18e-02
2.78e-02
4.29e-08
7.48e-10
1.19e-01
SS-SOMA-RBF
7.49e-01
8.98e-02
7.51e-01
6.02e-01
8.72e-01
GS-SOMA
2.2e-03
4.60e-03
8.95e-09
1.40e-10
1.54e-02


<!-- página 41 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
41
TABLE VII
STATISTICS OF THE FINAL SOLUTION QUALITY AT THE END OF 8000 EXACT FUNCTION EVALUATIONS FOR F3 USING GA, SS-SOMA-GP,
SS-SOMA-PR, SS-SOMA-RBF, AND GS-SOMA.
Optimization
Algorithm
Statistical Values
Mean
Std. Dev.
Median
Best
Worst
GA
4.10e+02
1.01e+02
3.85e+02
2.33e+02
5.73e+02
SS-SOMA-GP
2.99e+01
7.73e-01
3.00e+01
2.87e+01
3.11e+01
SS-SOMA-PR
6.73e+01
2.55e+01
5.62e+01
3.72e+01
1.04e+02
SS-SOMA-RBF
4.90e+01
2.92e+01
3.97e+01
2.92e+01
1.57e+02
GS-SOMA
4.63e+01
2.92e+01
3.02e+01
2.83e+01
1.26e+02


<!-- página 42 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
42
TABLE VIII
STATISTICS OF THE FINAL SOLUTION QUALITY AT THE END OF 8000 EXACT FUNCTION EVALUATIONS FOR F4 USING GA, SS-SOMA-GP,
SS-SOMA-PR, SS-SOMA-RBF, AND GS-SOMA.
Optimization
Algorithm
Statistical Values
Mean
Std. Dev.
Median
Best
Worst
GA
-5.46e+01
3.01e+01
-5.48e+01
-1.11e+02
5.19e-01
SS-SOMA-GP
-1.19e+02
1.87e+01
-1.17e+02
-1.50e+02
-8.71e+01
SS-SOMA-PR
-1.19e+02
1.23e+01
-1.21e+02
-1.43e+02
-9.01e+01
SS-SOMA-RBF
-1.65e+02
1.86e+01
-1.66e+02
-1.91e+02
-1.36e+02
GS-SOMA
-1.26e+02
1.60e+01
-1.23e+02
-1.64e+02
-9.97e+01


<!-- página 43 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
43
TABLE IX
STATISTICS OF THE FINAL SOLUTION QUALITY AT THE END OF 8000 EXACT FUNCTION EVALUATIONS FOR F5 USING GA, SS-SOMA-GP,
SS-SOMA-PR, SS-SOMA-RBF, AND GS-SOMA.
Optimization
Algorithm
Statistical Values
Mean
Std. Dev.
Median
Best
Worst
GA
1.26e+02
2.85e+00
1.26e+02
1.20e+02
1.32e+02
SS-SOMA-GP
1.19e+02
4.29e+00
1.20e+02
1.12e+02
1.25e+02
SS-SOMA-PR
5.67e+01
3.79e+00
1.16e+02
1.13e+02
1.25e+02
SS-SOMA-RBF
1.21e+02
2.61e+00
1.21e+02
1.18e+02
1.24e+02
GS-SOMA
1.19e+02
3.05e+00
1.19e+02
1.14e+02
1.24e+02


<!-- página 44 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
44
TABLE X
STATISTICS OF THE FINAL SOLUTION QUALITY AT THE END OF 8000 EXACT FUNCTION EVALUATIONS FOR F6 USING GA, SS-SOMA-GP,
SS-SOMA-PR, SS-SOMA-RBF, AND GS-SOMA.
Optimization
Algorithm
Statistical Values
Mean
Std. Dev.
Median
Best
Worst
GA
-9.57e+01
9.43e+00
-9.79e+01
-1.06e+02
-7.28e+01
SS-SOMA-GP
-1.02e+02
2.99e+00
-1.03e+02
-1.05e+02
-9.74e+02
SS-SOMA-PR
-1.06e+02
2.45e+00
-1.07e+02
-1.09e+02
-1.02e+02
SS-SOMA-RBF
-1.03e+02
2.43e+00
-1.03e+02
-1.07e+02
-9.96e+01
GS-SOMA
-1.12e+02
1.05e+00
-1.23e+02
-1.13e+02
-1.11e+02


<!-- página 45 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
45
TABLE XI
STATISTICS OF THE FINAL SOLUTION QUALITY AT THE END OF 8000 EXACT FUNCTION EVALUATIONS FOR F7 USING GA, SS-SOMA-GP,
SS-SOMA-PR, SS-SOMA-RBF, AND GS-SOMA.
Optimization
Algorithm
Statistical Values
Mean
Std. Dev.
Median
Best
Worst
GA
7.29e+02
5.92e+01
7.27e+02
6.43e+02
8.21e+02
SS-SOMA-GP
6.81e+02
7.23e+01
6.95e+02
6.02e+02
8.23e+02
SS-SOMA-PR
6.42e+02
5.80e+01
6.34e+02
5.73e+02
7.09e+02
SS-SOMA-RBF
6.27e+02
7.93e+01
5.99e+02
5.95e+02
8.49e+02
GS-SOMA
6.07e+02
3.06e+01
6.00e+02
5.79e+02
6.59e+02


<!-- página 46 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
46
TABLE XII
STATISTICS OF THE FINAL SOLUTION QUALITY AT THE END OF 8000 EXACT FUNCTION EVALUATIONS FOR F8 USING GA, SS-SOMA-GP,
SS-SOMA-PR, SS-SOMA-RBF, AND GS-SOMA.
Optimization
Algorithm
Statistical Values
Mean
Std. Dev.
Median
Best
Worst
GA
4.83e+02
6.3e+01
4.62e+02
4.19e+02
6.06e+02
SS-SOMA-GP
4.52e+02
9.66e+01
4.35e+02
3.40e+02
5.63e+02
SS-SOMA-PR
3.94e+02
4.41e+01
3.75e+02
3.43e+02
4.52e+02
SS-SOMA-RBF
3.79e+02
3.3e+01
3.69e+02
3.51e+02
4.41e+02
GS-SOMA
3.25e+02
1.17e+02
2.86e+02
2.32e+02
5.54e+02


<!-- página 47 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
47
TABLE XIII
STATISTICS OF THE FINAL SOLUTION QUALITY AT THE END OF 8000 EXACT FUNCTION EVALUATIONS FOR F9 USING GA, SS-SOMA-GP,
SS-SOMA-PR, SS-SOMA-RBF, AND GS-SOMA.
Optimization
Algorithm
Statistical Values
Mean
Std. Dev.
Median
Best
Worst
GA
1.02e+03
2.35e+01
1.02e+03
9.86e+02
1.08e+03
SS-SOMA-GP
9.42e+02
1.71e+01
9.37e+02
9.25e+02
9.81e+02
SS-SOMA-PR
9.32e+02
8.26e+00
9.31e+02
9.22e+02
9.48e+02
SS-SOMA-RBF
9.81e+02
1.43e+01
9.80e+02
9.67e+02
1.00e+03
GS-SOMA
9.42e+02
1.75e+01
9.37e+02
9.30e+02
9.86e+02


<!-- página 48 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
48
TABLE XIV
STATISTICS OF THE FINAL SOLUTION QUALITY AT THE END OF 8000 EXACT FUNCTION EVALUATIONS FOR F10 USING GA, SS-SOMA-GP,
SS-SOMA-PR, SS-SOMA-RBF, AND GS-SOMA.
Optimization
Algorithm
Statistical Values
Mean
Std. Dev.
Median
Best
Worst
GA
1.51e+03
5.52e+01
1.52e+03
1.40e+03
1.58e+03
SS-SOMA-GP
1.26e+03
1.88e+02
1.22e+03
1.03e+03
1.54e+03
SS-SOMA-PR
1.07e+03
1.07e+02
1.04e+03
9.42e+02
1.29e+03
SS-SOMA-RBF
1.12e+03
1.16e+02
1.15e+03
9.59e+02
1.28e+03
GS-SOMA
1.01e+03
7.85e+01
9.53e+02
9.09e+02
1.51e+03


<!-- página 49 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
49
TABLE XV
RESULT OF T-TEST WITH 95% CONFIDENCE LEVEL COMPARING STATISTICAL VALUES FOR GS-SOMA AND THOSE OF SS-SOMA-GP, SS-SOMA-PR,
SS-SOMA-RBF, SS-SOMA-PERFECT ON F1-F10 (s+, s−, AND ≈INDICATES THAT GS-SOMA IS SIGNIFICANTLY BETTER, SIGNIFICANTLY WORSE,
AND INDIFFERENT, RESPECTIVELY).
GA
SS-SOMA-GP
SS-SOMA-PR
SS-SOMA-RBF
SS-SOMA-Perfect
F1
s+
s+
s−
s+
s+
F2
s+
s+
≈
s+
s−
F3
s+
s−
s+
≈
s−
F4
s+
≈
≈
s−
s+
F5
s+
≈
s−
s+
s+
F6
s+
s+
s+
s+
s+
F7
s+
s+
s+
≈
s+
F8
s+
s+
s+
≈
s+
F9
s+
≈
s−
s+
s+
F10
s+
s+
≈
s+
s+


<!-- página 50 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
50
TABLE XVI
MULTI-OBJECTIVE BENCHMARK PROBLEMS (MF1-MF6). PARAMETRIC DOMAIN USED IS [0, 1]d, WHERE d IS THE PROBLEM DIMENSIONALITY
CONSIDERED IN THE PRESENT STUDY.
Benchmark
Formulation
Characteristics
Function
MF1 (d = 30)
f1(x) = x1
Convex, 2-objective Pareto front
f2(x) = g(x)[1 −
p
f1(x)/g(x)]
g(x) = 1 + 9(Pd
i=2 xi)/(d −1)
MF2 (d = 30)
f1(x) = x1
Non-convex, 2-objective Pareto front
f2(x) = g(x)[1 −f1(x)/g(x)2]
g(x) = 1 + 9(Pd
i=2 xi)/(d −1)
MF3 (d = 50)
f1(x) = x1
Convex, disconnected, 2-objective Pareto front
f2(x) = g(x)[1 −
p
f1/g −(f1/g)sin(10πf1)]
g(x) = 1 + 9(Pd
i=2 xi)/(d −1)
MF4 (d = 50)
f1(x) = 1 −exp(−4x1)sin6(6πx1)
Non-convex, 2-objective Pareto front
f2(x) = g(x)[1 −(f1(x)/g(x))2]
g(x) = 1 + 9[Pd
i=2 xi/(d −1)]0.25
MF5 (d = 20)
f1(x) = cos( π
2 x1)cos( π
2 x2)(1 + g(x))
Non-convex, 3-objective, Pareto front
f2(x) = cos( π
2 x1)sin( π
2 x2)(1 + g(x))
f3(x) = cos( π
2 x1)(1 + g(x))
g(x) = Pd
i=3(xi −x1)2
MF6 (d = 10)
f1(x) = x1
Convex, 2-objective, multiple local Pareto front
f2(x) = g(x)[1 −
p
f1(x)/g(x)]
g(x) = 1 + 10(d −1) + Pd
i=2(x2
i −10 cos(4πxi))


<!-- página 51 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
51
TABLE XVII
DEFINITION OF THE MULTI-OBJECTIVE MAS (MOMAS) COMPARED.
Algorithms
Deﬁnition
NSGA-II
No surrogate is used
GS-MOMA
Generalized surrogate MOMA with
M1: weighted-average ensemble of GP, PR, and RBF
M2: PR
SS-MOMA-I
Single surrogate MOMA with
M1: Ensemble of GP, PR, and RBF
SS-MOMA-II
Single surrogate MOMA with
M1: PR
SS-MOMA-Perfect
Single surrogate MOMA with
M1: Perfect model


<!-- página 52 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
52
TABLE XVIII
SETTING OF EXPERIMENTS FOR NSGA-II, GS-MOMA, AND SS-MOMA.
Parameters Setting
Population size (Npop)
100
Crossover probability (Pcross)
0.9
Mutation probability (Pmut)
0.1
Maximum number of exact evaluations
MF1-MF2: 8000
MF3-MF4: 16000
MF5: 30000
MF6: 20000
Evolutionary operators
simulated binary crossover,
polynomial mutation,
binary tournament selection,
elitism, non-domination rank,
and crowded distance
Number of trust region iteration(kterm)
2
for SS-MOMA and GS-MOMA
Database building phase (Gdb)
MF1-MF2, MF5-MF6: 10
for SS-MOMA and GS-MOMA
MF3-MF4: 20
(in number of generations)
Number of independent runs
20


<!-- página 53 -->

IEEE TRANSACTIONS ON EVOLUTIONARY COMPUTATION
53
TABLE XIX
RADIAL BASIS KERNELS.
Linear Splines
||x −ci||
Thin Plate Splines
||x −ci||kln||x −ci||
Cubic Splines
||x −ci||3
Gaussian
e−||x−ci||2
βi
Multiquadrics
q
1 + ||x−ci||2
βi
Inverse Multiquadrics
(1 + ||x−ci||2
βi
)−1
2



---

## ANEXO — Conteúdo textual das imagens (OCR)

> Texto extraído por OCR (Apple Vision) das figuras/imagens do PDF — apenas conteúdo NOVO, ausente da camada de texto (labels de eixos, legendas internas, tabelas/equações rasterizadas, slides). OCR de fórmulas é aproximado.

### Página 16
*(figura em y≈296–444)*
- VAne

### Página 18
*(figura em y≈402–528)*
- enje^ ssauy! (Natural Log)
- 607 ¡eunjen) enjeA ssound
- 607 ¡eunjen) enjeA ssou!
- 6.35 L
*(figura em y≈64–190)*
- A A DA. GS-SOMA
- 507 reunieN) enjeA ssou
- I SS-SOMA-Perfect
*(figura em y≈233–359)*
- enje ssound
- anje ssauny
- CS-SOMA
- (607 ¡BUnjEN) enjeA SsOuly
- -150 l

### Página 19
*(figura em y≈291–480)*
- }SNU paz! euloN

### Página 21
*(figura em y≈291–480)*
- }SW paZ! eULON

### Página 22
*(página inteira)*
- 3 5 9 28 3
- quawedejdey o, BujAjupy j0 ogey
- Archiving of to Replacement Ratio of GS-MOMA on MF1-MF6.

### Página 24
*(figura em y≈403–513)*
- 8 8 8 38888 5°

### Página 26
*(figura em y≈249–359)*
- -innUG
*(figura em y≈403–513)*
- MA NOCE
- CHON x0002.

### Página 28
*(figura em y≈403–513)*
- Ax fet

### Página 29
*(figura em y≈314–440)*
- 0.14 F
- I Distance
- unwixew Spread
- ogey ewnjo/adÁt

### Página 30
*(figura em y≈314–440)*
- 8 022
- 3 0.85
- ) ogey awnjo/adAp
- SQUeISIa jeuogeJauag

### Página 31
*(figura em y≈314–440)*
- 8 0.14
- Distance Generational
- Spread unwixew
- ogey awnjo/adAn

### Página 32
*(figura em y≈314–440)*
- (SW) praids wnwixew
- ogey ewnjo/Jad/H

### Página 33
*(figura em y≈314–440)*
- 0.14 F
- 0.9998 F
- ogey ewnjo/adÁ,
- (05) sue}sia (euojejouag
- 0.9992 F

### Página 34
*(figura em y≈314–440)*
- peads wnwprey
- (HH) ogey ownjo/adÁH

### Página 53
*(página inteira)*
- |x - c; ll
- |x - cill
- x - call*In| x -
- |x-cill-
- Inverse Multiquadrics (1 + lx-call)-}
- V1+ Ix-call2
