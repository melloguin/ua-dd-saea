# emo1. Alternative infill strategies for expensive multi-objective optimisation

> Fonte (original): emo1. Alternative infill strategies for expensive multi-objective optimisation.pdf
> Extraído com pymupdf4llm (texto + tabelas + números; imagens omitidas). Páginas: 9.

---











Latest updates: hps://dl.acm.org/doi/10.1145/3071178.3071276 

###### RESEARCH-ARTICLE 



**PDF Download 3071178.3071276.pdf 13 February 2026 Total Citations:** 34 **Total Downloads:** 498 

**Published:** 01 July 2017 

###### **Citation in BibTeX format** 

## **Alternative infill strategies for expensive multi-objective optimisation** 

**ALMA A M RAHAT** , University of Exeter, Exeter, Devon, U.K. 



Dr Rahat is an Associate Professor of Data Science. His expertise is in evolutionary and Bayesian search and optimisation. Particularly, he has worked on developing effective acquisition functions for optimising single and multi-objective problems and locating the feasible space of solutions. He has a strong track record of working with industry on a broad range of optimisation problems, which resulted in numerous articles in top journals and conferences, including a best paper in the Real-World Applications track at GECCO, and a patent with Hydro International Ltd. Recently, he has been actively contributing to the Welsh Government's response to the pandemic using his expertise in machine learning and parameter optimisation with funding from both the Welsh Government (Co-PI and Co-I; £750k) … (View more) 

GECCO '17: Genetic and Evolutionary Computation Conference _July 15 - 19, 2017 Berlin, Germany_ 

**Conference Sponsors:** SIGEVO 

#### **RICHARD M EVERSON** , University of Exeter, Exeter, Devon, U.K. 

#### **JONATHAN EDWARD FIELDSEND** , University of Exeter, Exeter, Devon, U.K. 

#### **Open Access Support** provided by: 

#### **University of Exeter** 

. 

GECCO '17: Proceedings of the Genetic and Evolutionary Computation Conference (July 2017) hps://doi.org/10.1145/3071178.3071276 ISBN: 9781450349208 

# **Alternative Infill Strategies for Expensive Multi-Objective Optimisation** 

Richard M. Everson University of Exeter United Kingdom R.M.Everson@exeter.ac.uk 

Jonathan E. Fieldsend University of Exeter United Kingdom J.E.Fieldsend@exeter.ac.uk 

Alma A. M. Rahat<sup>∗</sup> University of Exeter United Kingdom A.A.M.Rahat@exeter.ac.uk 

### **ABSTRACT** 

### **1 INTRODUCTION** 

Many multi-objective optimisation problems incorporate computationally or financially expensive objective functions. State-of-theart algorithms therefore construct surrogate model(s) of the parameter space to objective functions mapping to guide the choice of the next solution to expensively evaluate. Starting from an initial set of solutions, an infill criterion — a surrogate-based indicator of quality — is extremised to determine which solution to evaluate next, until the budget of expensive evaluations is exhausted. Many successful infill criteria are dependent on multi-dimensional integration, which may result in infill criteria that are themselves impractically expensive. We propose a computationally cheap infill criterion based on the minimum probability of improvement over the estimated Pareto set. We also present a range of set-based scalarisation methods modelling hypervolume contribution, dominance ratio and distance measures. Tese permit the use of straightforward expected improvement as a cheap infill criterion. We investigated the performance of these novel strategies on standard multi-objective test problems, and compared them with the popular SMS-EGO and ParEGO methods. Unsurprisingly, our experiments show that the best strategy is problem dependent, but in many cases a cheaper strategy is at least as good as more expensive alternatives. 

Real world multi-objective optimisation problems ofen consist of computationally or financially expensive objective functions. For instance, design optimisation of mechanical parts may require inspecting the performance of a design within a fluid environment using computational fluid dynamics (CFD) simulations. A high quality CFD simulation may take hours to converge, and thus only a limited number of designs may be considered in optimisation. 

Many effective algorithms have been proposed in the last decade for expensive multi-objective optimisation, see for example [4, 6, 8, 20, 24]. Generally, these are model-based approaches inspired by single objective Bayesian global optimisation methods. Based on an initial set of expensively evaluated solutions, a Bayesian surrogate model, either for each objective (multi-surrogate) or for a scalarised representation of the multi-objective problem (monosurrogate), is constructed. Regardless of what was modelled, a surrogate based multi-objective quality indicator, ofen referred to as an _infill criterion_ , is derived. It is usually much cheaper to evaluate in comparison to the original objective functions, but frequently induces a highly multi-modal single objective fitness landscape. As such evolutionary optimisers perform well in locating promising solutions using the infill landscape. A candidate solution is then expensively evaluated, and the surrogate model(s) are retrained. Te process is repeated until the budget on the expensive function evaluations is exhausted. Tus, these methods require only a few hundreds of expensive function evaluations to generate a good approximation of the optimal trade-off between multiple objectives. 

### **CCS CONCEPTS** 

• **Computing methodologies** → **Gaussian processes; Modeling methodologies;** • **Applied computing** → **Multi-criterion optimization and decision-making;** • **Mathematics of computing** → **Probabilistic algorithms;** 

One of the major issues with the most effective multi-surrogate infill criterion is that it ofen requires multi-dimensional integration, and therefore optimising it may become impractically expensive. A promising cheaper alternative are mono-surrogate approaches, but the only example of such an approach in a Bayesian optimisation framework is ParEGO [20]. Addressing these issues, the major contributions of this paper are as follows. 

### **KEYWORDS** 

Computationally Expensive Optimisation; Efficient Multi-Objective Optimisation; Infill Criteria; Scalarisation methods. 

###### **ACM Reference format:** 

Alma A. M. Rahat, Richard M. Everson, and Jonathan E. Fieldsend. 2017. Alternative Infill Strategies for Expensive Multi-Objective Optimisation. In _Proceedings of GECCO ’17, Berlin, Germany, July 15-19, 2017,_ 8 pages. DOI: htp://dx.doi.org/10.1145/3071178.3071276 

- We devise a novel infill criterion based on the minimum probability of improvement over an estimated Pareto set as an alternative multi-surrogate approach. 

- We propose a range of set-based scalarisation functions modelling hypervolume improvement, dominance ranking or minimum signed distance from an estimated Pareto set, that may be used in a mono-surrogate Bayesian framework, and therefore promote research on this front. 

∗Corresponding author 

Permission to make digital or hard copies of all or part of this work for personal or classroom use is granted without fee provided that copies are not made or distributed for profit or commercial advantage and that copies bear this notice and the full citation on the first page. Copyrights for components of this work owned by others than ACM must be honored. Abstracting with credit is permited. To copy otherwise, or republish, to post on servers or to redistribute to lists, requires prior specific permission and/or a fee. Request permissions from permissions@acm.org. _GECCO ’17, Berlin, Germany_ © 2017 ACM. 978-1-4503-4920-8/17/07...$15.00 DOI: htp://dx.doi.org/10.1145/3071178.3071276 

Te rest of the paper is structured as follows. In Section 2, we present the required background and the relevant work in the literature. Te novel infill strategies are described in Sections 3 and 4. We present our results in Section 5. General conclusions are drawn in Section 6. 

873 

GECCO ’17, July 15-19, 2017, Berlin, Germany 

Rahat _et al._ 

### **2 BACKGROUND** 

We now present a synthesis of the relevant background material. 

### **2.1 Single Objective Efficient Global Optimisation (EGO)** 

_Efficient Global Optimisation (EGO)_ or _Bayesian Optimisation (BO)_ is a particular area of surrogate-assisted (evolutionary) optimisation. In practice, it has proved to be a very effective approach for single objective expensive optimisation problems with limited budget on the number of true function evaluations. A recent review on the topic can be found in [26]. 

EGO is essentially a global search strategy that sequentially samples the design space at likely locations of the global optimum [17]. It starts with a space filling design (e.g. Latin hypercube sampling [22]) of the parameter space, constructed independent of the function space. Te solutions from this initial design are then evaluated with the true function. Using the set of the initial design parameters and the associated function values as data a regression model is trained. Promising parameters at which to evaluate the function can then be located using the surrogate. Frequently the surrogate model is a stochastic process, usually a Gaussian process (GP)<sup>1</sup> . Te benefit of using GPs for regression is that they provide a posterior predictive distribution given the training data, and thus querying the surrogate model at any solution in the design space results in both a mean prediction and the uncertainty associated with the prediction. Tis ofen enables the closed form calculation of an _infill criterion_ , that is the expected improvement in function value (with respect to the best function value observed so far) to be obtained by querying a solution. Tis infill criterion has monotonicity properties: it is inversely proportional to the predicted mean (with fixed uncertainty), and directly proportional to the uncertainty in prediction (with fixed predicted mean). As a consequence, it strikes a balance between global exploration and myopic exploitation of the model. Terefore, a strategy for selecting the next solution is to (expensively) evaluate the parameters that maximise the infill criterion. Te newly sampled data is then added to the training database, and a retraining of the GP model ensues. Te process is repeated until the budget is exhausted. 

A single objective optimisation problem may be expressed as: 



where the parameters x ∈ R<sup>_n_</sup> and _f_ : R<sup>_n_</sup> → R. With the initial design D = {(x<sup>_m_</sup> , _f_<sup>_m_</sup> = _f_ (x<sup>_m_</sup> )} _m_<sup>_M_</sup> =1<sup>of</sup><sup>_M_samples, a GPmodel may</sup> be constructed. In essence, a GP is a collection of random variables, and any finite number of these have a joint Gaussian distribution [25]. Te predictive density of the function for parameters x given by a GP model based on the observations D may be expressed as: 



where the mean and variance are 





Here _X_ ∈ R<sup>_M_×</sup><sup>_n_</sup> is the matrix of observed parameter values and f ∈ R<sup>_M_</sup> is the corresponding vector of the true function evaluations; 

1Gaussian Processes subsume Kriging. 

thus D = {( _X_ , f )}. Te covariance matrix _K_ ∈ R<sup>_M_×</sup><sup>_M_</sup> represents the covariance function _κ_ (x, x<sup>′</sup> ) evaluated for each pair of observations and _κ_ (x, _X_ ) ∈ R<sup>_M_</sup> is the vector of covariances between x and each of the observations. In this paper, we use a flexible class of covariance functions embodied in the Matern 5/2 kernel, as recommended for modelling realistic functions [27]. We used the limited memory BFGS algorithm with 10 restarts to optimise the kernel hyperparameters; see [12] for details. 

Te predicted improvement over the best evaluated solution so far, _f_<sup>∗</sup> = min _m_ { _f_<sup>_m_</sup> (x _m_ )}, is: _I_ (x, _f_<sup>∗</sup> ) = max ( _f_<sup>∗</sup> − _f_<sup>ˆ</sup> (x), 0). Terefore, the infill criterion (i.e. expected improvement at x) based on the surrogate model may be expressed as [17]: 



where _s_ = ( _f_<sup>∗</sup> − _µ_ (x))/ _σ_ (x), and _ϕ_ (·) and Φ(·) are the Gaussian probability density function and cumulative density functions. Te infill criterion is essentially the improvement weighted by the part of the posterior predictive distribution that lies below the evaluated minimum _f_<sup>∗</sup> and thus balances the exploitation of solutions which are very likely to be a litle beter than _f_<sup>∗</sup> with the exploration of others which may, with lower probability, turn out to be much beter. Tus maximising this infill criterion estimates where the global optimum may be given the data and a strategy for determining the next solution to evaluate is the following maximisation problem: 



Te evaluation of the infill criterion in (5) is generally cheap. Tus an evolutionary algorithms may be used to locate an approximation of the optimal solution. Tis new solution may then be evaluated with the expensive function _f_<sup>_M_+1</sup> = _f_ (x<sup>_M_+1</sup> ), and the dataset is augmented with the new solution D ←D ∪{(x<sup>_M_+1</sup> , _f_<sup>_M_+1</sup> )}. Te GP is retrained with the augmented dataset D. Te process is repeated until the limit on the number of expensive function evaluations is reached. 

Note that the infill criterion may induce a highly multi-modal fitness landscape. Terefore locating the solution that maximises the expected improvement may require a large number of evaluations on the surrogate GP model. Hence, selecting the next solution to evaluate may be relatively expensive despite the fact that computing the expected improvement for a single x is cheap. 

### **2.2 Multi-Objective Optimisation Problem** 

Many real world problems have multiple, ofen conflicting, objectives, and it is important to extremise these objectives simultaneously [5]. Consider a decision vector x ∈ R<sup>_n_</sup> within the feasible parameter space X. Without loss of generality, a multi-objective optimisation problem with _D_ objectives may then be expressed as: 



where _fi_ (x) is the _i_ th objective and F : X ∈ R<sup>_n_</sup> → R<sup>_D_</sup> generates the objective space. 

Due to the potentially conflicting objectives, generally there is not a unique solution to the optimisation problem, but a range of solutions trading-off between the objectives. Te trade-off between solutions is characterised by the notion of dominance: a solution x 

874 

GECCO ’17, July 15-19, 2017, Berlin, Germany 

Alternative Infill Strategies for Expensive Multi-Objective Optimisation 

is said to dominate another solution x<sup>′</sup> , denoted as x ≺ x<sup>′</sup> , iff 

_fi_ (x) ≤ _fi_ (x<sup>′</sup> ) ∀ _i_ = 1, . . . , _D_ and _fi_ (x) < _fi_ (x<sup>′</sup> ) for some _i_ . (8) Te set of solutions representing the optimal trade-off between the objectives is referred to as the Pareto set: 



and the image of the Pareto set in the objective space is known as the Pareto front F = {F(x) | x ∈P}. 

Exactly locating the complete Pareto set may not be possible within a practical time limit, even for cheap objective functions, and an approximation is ofen sufficient. Terefore, the overall goal of an effective optimisation approach is to generate a good approximation of the Pareto set P<sup>∗</sup> ⊆X. 

Existing infill strategies for multi-objective optimisation based on GPs may be categorised in two groups: multi-surrogate and mono-surrogate approaches. In multi-surrogate approaches, each objective function _fi_ (x) is modelled. Tese models are ofen considered to be independent ignoring any potential cross-correlations between models, which is known to reduce overall uncertainty in predictions [19]. Te combined models induce a multivariate Gaussian predictive distribution, with a diagonal covariance matrix: _p_ (F<sup>ˆ</sup> (x) | D) =<sup>�</sup> _i_<sup>_Dp_( ˆ</sup><sup>_fi_(x) | x, D)=N (Fˆ |</sup><sup>_µ_(x), Σ(x)),with</sup> _µ_ (x) = ( _µ_ 1 (x), . . . , _µD_ (x)) and Σ(x) = diag( _σ_ 1<sup>2(x), . . . ,</sup><sup>_σ_</sup> _D_<sup>2(x)),</sup> from which an infill criterion is _α_ (x, F<sup>ˆ</sup> ) may be derived. On the other hand, mono-surrogate approaches aggregate the _D_ objective functions to generate a scalarised model _д_ (x) ≡ _д_ (F(x)). A surrogate model _д_ ˆ of the scalarisation is used to compute the infill criterion _α_ (x, _д_ ˆ). In both cases, the next solution to evaluate is the one which extremises the relevant infill criterion _α_ (·). Algorithm 1 briefly describes these efficient multi-objective optimisation approaches. 

**Algorithm 1** Efficient multi-objective optimisation. 

##### **Inputs** 

_M_ : Number of initial samples _T_ : Budget on expensive function evaluations 

##### **Steps** 

|1:|_X_ ←LatinHypercubeSampling(X)<br>▷Generate initial samples|
|---|---|
|2:|f ←F(x ∈_X_)<br>▷Expensively evaluate all initial samples|
|3:|**for**_i_ =_M_ →_T_ **do**|
|4:|**if** MultiSurrogate**then**<br>▷Multi-surrogate approach<br>ˆ|
|5:|F←TrainGP (_X_,f)<br>▷Train a model for each objective<br>|
|6:|x<sup>∗</sup>←argmaxx_α_(x, F <sup>∗</sup>)<br>▷Optimise infll criterion|
|7:|**else**<br>▷Mono-surrogate approach|
|8:|ˆ_д_ ←TrainGP (_X_,_д_(x ∈_X_))<br>▷Train a model for scalarised<br>▷objective<br>|
|9:|x<sup>∗</sup>←argmaxx_α_(x, ˆ_д_)<br>▷Optimise infll criterion<br>|
|10:|**end if**|
|11:|_X_ ←_X_ ∪{x<sup>∗</sup>}<br>▷Augment data set withx<sup>∗</sup>|
|12:|f ←f ∪{F(x<sup>∗</sup>)}<br>▷Expensively evaluatex<sup>∗</sup>|
|13:|P<sup>∗</sup>←nondom(_X_)<br>▷Update Pareto set|
|14:|F <sup>∗</sup>←nondom(f)<br>▷Update Pareto front|
|15:|**end for**|
|16:|**return** P<sup>∗</sup>|



Clearly, the infill criterion is a form of scalarisation of the original multi-objective problem. Te central distinction between multiand mono-surrogate approaches is therefore how this scalarisation is performed. In multi-surrogates, this scalarisation is based on predictive models, but in mono-surrogates the scalarisation is based on the deterministic evaluations of F and uncertainty in the prediction enters through a predictive model for the scalarisation. 

### **2.3 Related Work** 

Most effective multi-surrogate strategies use expected hypervolume improvement as a multi-objective infill criterion. First proposed by Emmerich [8], the expected hypervolume improvement calculates the potential gain that may be achieved over the current Pareto set P<sup>∗</sup> by augmenting P<sup>∗</sup> with a solution based on its predictive distribution. Tis, however, involves multidimensional integration over the non-dominated objective space, which is achieved by decomposing the integration volume into disjoint cells and accounting for the volume weighted by the predictive distribution in each cell. As such the run time complexity is high and dependent on the number of solutions |P<sup>∗</sup> |. Practical improvements on implementations of the expected hypervolume computation have been proposed by Hupkens _et al._ [16] and Couckuyt _et al._ [6], but the worst case time complexity is O(|P<sup>∗</sup> |<sup>_D_</sup> ) for _D_ = 2, 3 objectives; for more objectives, the time complexity is conjectured to be even higher [16]. 

An alternative approach with a proxy for expected hypervolume improvement, referred to as S-metric selection EGO ( _SMS-EGO_ ), was proposed by Ponweiser _et al._ [24] and later improved by Wagner _et al._ [28]. In this approach, the posterior predictive distribution is accounted for implicitly with and overestimated mean prediction by simply subtracting the scaled uncertainty. Tis permits a deterministic calculation of hypervolume improvement over P<sup>∗</sup> for a tentative solution. Although this is comparatively cheaper to calculate, it still is expensive as the hypervolume calculation must be performed to evaluate the infill criterion for each tentative solution. Nonetheless, it has been shown to perform beter or at least as well as the other methods [28]. We therefore choose to compare against SMS-EGO in this paper. 

Other multi-surrogate infill strategies consider probability of improvement of a solution over P<sup>∗</sup> [6, 18], minimum Euclidean distance of mean predictions over P<sup>∗</sup> [18], aggregating the posterior prediction with Chebyshev scalarisation and computing the expected improvement in each scalarisation function within the MOEA/D framework [29], minimum angle penalised distance or maximum uncertainty within the reference vector guided evolutionary (RVEA) framework [4], etc. 

Te only mono-surrogate approach used within the Bayesian EGO framework is ParEGO [20]. It uses the normalised objective function values with an augmented Chebyshev function and a predefined set of weight vectors to achieve a scalarisation of the original multi-objective problem. Te scalarised function is learned using a GP model and the standard expected improvement is calculated using equation (5). Tis mono-surrogate approach is known to be the considerably faster than other methods [4]. Tis is because only one model is maintained and trained (step 8 in Algorithm 1), and locating a solution that maximises the expected improvement is cheap because evaluation of the GP is inexpensive. 

875 

GECCO ’17, July 15-19, 2017, Berlin, Germany 

Rahat _et al._ 

Terefore more research should be carried out in mono-surrogate approaches; especially given the success of set-based quality indicators in standard multi-objective evolutionary approaches, see for example IBEA [31] and HypE [2]. One of the main contributions of this paper is to propose a range of mono-surrogate strategies and thus propel research on this front. We therefore compare our infill criteria with ParEGO as well. Note that other mono-surrogate approaches, such as model based strategies proposed by Loschilov _et al._ [21] and Azzouz _et al._ [1], do not use GPs, and thus may not be used within the Bayesian EGO framework. 

### **3 MULTI-SURROGATE APPROACH: MINIMUM PROBABILITY OF IMPROVEMENT (MPOI)** 

In a multi-surrogate approach, we consider independent GP models for each objective: _p_ ( _f_<sup>ˆ</sup> _i_ (x) | x, D) = N ( _f_<sup>ˆ</sup> (x) | _µi_ (x), _σi_<sup>2(x)). As-</sup> suming that the objectives are independent, the probability that a solution x dominates another solution x<sup>′</sup> is given by [9, 15]: 



where 





Note that since we consider the true evaluations to be noise-free, for any x ∈ _X_ , _µi_ (x) = _fi_ (x) and _σi_<sup>2(x)= 0.</sup> 

Comparing an arbitrary solution x<sup>′</sup> ∈X with a solution x ∈P<sup>∗</sup> , the current estimated Pareto set, there are three mutually exclusive possibilities: x<sup>′</sup> dominates x (x<sup>′</sup> ≺ x), x<sup>′</sup> is dominated by x (x ≺ x<sup>′</sup> ), or they are mutually non-dominated (x ∥ x<sup>′</sup> ). Terefore, the probability that x<sup>′</sup> improves upon a solution x ∈P<sup>∗</sup> is: 



Intuitively, this measures the probability mass in the objective space beyond a solution x ∈P<sup>∗</sup> , i.e. the space not dominated by x, due to the multivariate predictive distribution for F<sup>ˆ</sup> . With this notion of the probability of improvement, we can define a multi-objective infill criterion based on least improvement upon any solution from the current Pareto front F<sup>∗</sup> of evaluated solutions: 



Tus, in a multi-objective EGO, the next solution to evaluate is: 



Keane [18] and Couckuyt _et al._ [6] suggested computing the probability of improvement over all solutions x ∈P<sup>∗</sup> , i.e. 1 − _P_ (<sup>�</sup> x∈P<sup>∗x≺x′),asaninfillcriterion.Again,similartoex-</sup> pected hypervolume improvement calculations, this requires multidimensional integration by decomposing the non-dominated objective space into disjoint regions. As such, it is computationally expensive, especially for many-objective problems. In our formulation of the infill criterion _αp_ (x<sup>′</sup> , F<sup>∗</sup> ) in equation (14), we implicitly cover all the solutions from the current estimated Pareto set P<sup>∗</sup> by 

considering the minimum probability of improvement over P<sup>∗</sup> . It is therefore fast to calculate, with the most expensive step being the calculation of erf(·) function. 

### **3.1 Monotonicity Properties** 

Te role of an infill criterion is to help us choose a good candidate solution. Te efficacy of an infill criterion thus depends on how well it distinguishes between two tentative solutions x<sup>′</sup> , x<sup>′′</sup> ∈X \ _X_ . A sound multi-objective infill criterion must therefore satisfy the following necessary conditions for two solutions x<sup>′</sup> and x<sup>′′</sup> [28]. 

- N1 Te dominance relationship should be preserved given that the uncertainty is equal. Tat is, if _µi_ (x<sup>′</sup> ) < _µi_ (x<sup>′′</sup> ) ∧ _σi_ (x<sup>′</sup> ) = _σi_ (x<sup>′′</sup> ), ∀ _i_ ∈{1, . . . , _D_ }, then: _αp_ (x<sup>′</sup> , F<sup>∗</sup> ) > _αp_ (x<sup>′′</sup> , F<sup>∗</sup> ). 

- N2 When mean predictions are equal, the infill criterion should monotonically increase with the uncertainty. Tat is if _µi_ (x<sup>′</sup> ) = _µi_ (x<sup>′′</sup> ) ∧ _σi_ (x<sup>′</sup> ) > _σi_ (x<sup>′′</sup> ), ∀ _i_ ∈{1, . . . , _D_ }, then: _αp_ (x<sup>′</sup> , F<sup>∗</sup> ) > _αp_ (x<sup>′′</sup> , F<sup>∗</sup> ). 

_Proof._ Clearly, from equation (14), it is sufficient to prove that for any solution x ∈P<sup>∗</sup> , _P_ (x ≺ x<sup>′</sup> ) < _P_ (x ≺ x<sup>′′</sup> ), for both N1 and N2 to be true. Tis further implies: it is equivalent to prove that _mi_ (x, x<sup>′</sup> ) < _mi_ (x, x<sup>′′</sup> ), ∀ _i_ ∈{1, . . . , _D_ } under the given conditions (c.f. equations (10) and (11)). As discussed earlier, with no noise in measurements _µi_ (x) = _fi_ (x) and _σi_ (x) = 0. Now, considering equation (12), given the same uncertainty in prediction _σi_ (x<sup>′</sup> ) = _σi_ (x<sup>′′</sup> ), _mi_ (x, x<sup>′</sup> ) < _mi_ (x, x<sup>′′</sup> ) for _i_ th objective iff _µi_ (x<sup>′</sup> ) < _µi_ (x<sup>′′</sup> ). Tus N1 is satisfied. Similarly, when the mean predictions are the same _µi_ (x<sup>′</sup> ) = _µi_ (x<sup>′′</sup> ), then _mi_ (x, x<sup>′</sup> ) < _mi_ (x, x<sup>′′</sup> ) for _i_ th objective iff _σi_ (x<sup>′</sup> ) > _σi_ (x<sup>′′</sup> ). Terefore N2 is satisfied. ■ 

### **3.2 Infill Fitness Landscape** 

An infill criterion essentially is a scalar representation of the objective space. It is therefore interesting to investigate the induced infill landscape within the objective space. 

To achieve a visual impression of the landscape, we consider evenly distributed samples from the objective space. Considering each sample as the mean prediction of a multivariate GP, and seting a fixed uncertainty _σ_ = 0.1, we calculate the minimum probability of improvement. In Figure 1, we show the resulting characterisation of the objective space. We can observe a clear indication that optimising this infill criteria promotes sampling in the non-dominated region, and hence it is likely to improve the current estimation of the Pareto set. It is also evident that the single objective infill criteria is highly multi-modal. It should be noted that in reality the characterisation using trained models may appear different due to variations in uncertainty. Nonetheless, the infill criteria adheres to the monotonicity properties as described in Section 3.1. 

### **4 MONO-SURROGATE APPROACH: INDICATOR BASED SCALARISATION** 

To the best of our knowledge the only scalarising function used in a mono-surrogate framework is an augmented Chebyshev function [20]. However, it is possible to model other set-based quality indicators that measure the rank of a solution within the expensively sampled solutions instead. Such scalarised ranking can then 

876 

GECCO ’17, July 15-19, 2017, Berlin, Germany 

Alternative Infill Strategies for Expensive Multi-Objective Optimisation 

Minimum Probability of Improvement (MPoI) 



<!-- Start of picture text -->
1 . 0<br>0 . 8<br>0 . 6<br>0 . 4<br>0 . 2<br>0 . 0<br>0 . 00 0 . 25 0 . 50 0 . 75 1 . 00<br>f 1( x )<br>)( fx 2<br><!-- End of picture text -->

0.00 0.13 0.27 0.40 0.53 0.67 0.80 0.93 **Figure 1: Infill fitness landscape in a hypothetical twoobjective space with fixed uncertainty** _σ_ = 0.1 **in prediction for minimum probability of improvement over current estimated Pareto front** F<sup>∗</sup> **(red squares). Lighter shades depict higher probability of improvement, and thus these areas are preferred over darker areas. Maximising the criterion promotes sampling in the non-dominated objective space. Te black squares show the dominated solutions in the data set. Te contours are unaffected by the dominated solutions.** 

be modelled with a GP and used within the EGO framework. So long as a scalarisation function preserves dominance relationship, maximising such scalarisation should improve the current set [31]. Although many different scalarisation methods may be used, in this section we present three scalarisation methods. 

### **4.1 Hypervolume Improvement (HypI)** 

Te hypervolume is a set-based quality indicator that measures the objective space covered between a non-dominated set and a predefined reference vector [30]. It is an exceptional set-based indicator as Fleischer proved that maximising hypervolume is equivalent to locating the optimal Pareto set [10]. We therefore propose a scalarisation based on hypervolume improvement. 

A set of expensively sampled solutions D = {( _X_ , f = _F_ ( _X_ ))} can be ranked according to the “Pareto shell” in which they lie. Let the first Pareto shell be the estimated Pareto set for _X_ : P1<sup>′=P∗=</sup> nondom( _X_ ), where the nondom(·) function returns the maximal non-dominated subset of its argument. Ten successive Pareto shells P _l_<sup>′(</sup><sup>_l_> 1) are defined as:</sup> 



Te hypervolume indicator for a set _X_ is the volume of objective space which is dominated by solutions in _X_ and which dominates a reference vector r [30]: 



In order to define the hypervolume improvement due to a solution x, we consider the first Pareto shell that contains no solutions that dominate x; denote this shell by P _k_<sup>′.Ten the hypervolume</sup> improvement for x is the hypervolume corresponding to P _k_<sup>′aug-</sup> mented with x: 



Here the function _дh_ (x, _X_ ) generates a set-based scalarisation of the original multi-objective problem for the set of sampled solutions. Clearly, if a solution x<sup>′′</sup> is dominated by another x<sup>′</sup> , then _дh_ (x<sup>′</sup> , _X_ ) > _дh_ (x<sup>′′</sup> , _X_ ). Terefore we may learn a function _д_ ˆ _h_ (x) and use the expected improvement in equation (5) within EGO framework in order to maximise the hypervolume improvement (a _unary_ indicator), and thus improve upon the current approximation of the Pareto set P<sup>∗</sup> . 

Note that this set-based scalarisation is different from the formulation HypE [2]. In HypE, the scalarisation does not differentiate between the dominated solutions during selection, and hence all dominated solutions have the same scalar value associated with the,, creating a plateau of equal fitness behind P<sup>∗</sup> . Using a GP to model the scalarisation thus has limited spatial information, which may hinder EGO’s global exploration. In contrast, we base our scalarisation purely on dominance rank based hypervolume improvement, and in order to generate a positive fitness gradient towards the Pareto set, aiding the EGO process. 

### **4.2 Dominance Ranking (DomRank)** 

In MOGA [11], a fitness assignment scheme based on dominance was proposed. In essence, a solution is assigned a rank in proportion to the number of already-evaluated solutions that dominate it. We use a straightforward adaptation of this. 

Given a set of solutions _X_ , a solution can be dominated by at most | _X_ | − 1 others. Te ranking strategy is defined as: 



Terefore, the current estimated Pareto set members x<sup>_a_</sup> ∈P<sup>∗</sup> have the maximum rank _дc_ (x<sup>_a_</sup> , _X_ ) = 1. Similarly, a solution x<sup>_b_</sup> that is dominated by all other members is assigned rank _дc_ (x<sup>_b_</sup> , _X_ ) = 0. 

By definition it is dominance preserving: if x<sup>′</sup> ≺ x<sup>′′</sup> , then _дc_ (x<sup>′</sup> , _X_ ) > _дc_ (x<sup>′′</sup> , _X_ ). It is therefore suitable for use in the EGO framework. 

### **4.3 Minimum Signed Distance (MSD)** 

Distance of a solution from the current estimate of the Pareto front is clearly important. Here, we consider the minimum signed distance of a solution from P<sup>∗</sup> as a ranking strategy: 



where _d_ (x<sup>′</sup> , x) =<sup>�</sup> _i_<sup>_D_</sup> =1<sup>_fi_(x′) −</sup><sup>_fi_(x) is a signed distance. Similar to</sup> the other measures, it is also dominance preserving and therefore if x<sup>′</sup> ≺ x<sup>′′</sup> , then _дd_ (x<sup>′</sup> , _X_ ) > _дd_ (x<sup>′′</sup> , _X_ ). 

### **4.4 Scalarisation Fitness Landscape** 

Te mono-surrogate strategies also induce a fitness landscape in the objective space, which can be informatively visualised. Rather than considering solutions from the decision space, we use evenly distributed points in the multi-dimensional objective space, and compute the fitness. In Figure 2, the resulting characterisations of the objective space is presented. 

Te hypervolume improvement (Figure 2 _lef_ ) and the minimum signed distance (Figure 2 _right_ ) both show strong selection preference towards the minimum of both objectives. In comparison, 

877 

GECCO ’17, July 15-19, 2017, Berlin, Germany 

Rahat _et al._ 



<!-- Start of picture text -->
Hypervolume Improvement (HypI) Dominance Ranking (DomRank) Min. Signed Distance (MSD)<br>1 . 0 1 . 0 1 . 0<br>0 . 8 0 . 8 0 . 8<br>0 . 6 0 . 6 0 . 6<br>0 . 4 0 . 4 0 . 4<br>0 . 2 0 . 2 0 . 2<br>0 . 0 0 . 0 0 . 0<br>0 . 00 0 . 25 0 . 50 0 . 75 1 . 00 0 . 00 0 . 25 0 . 50 0 . 75 1 . 00 0 . 00 0 . 25 0 . 50 0 . 75 1 . 00<br>f 1( x ) f 1( x ) f 1( x )<br>0.74 1.26 1.78 2.29 2.81 3.33 3.85 4.36 0.00 0.13 0.27 0.40 0.53 0.67 0.80 0.93 -1.69 -1.35 -1.00 -0.66 -0.31 0.04 0.38 0.73<br>)( fx 2 )( fx 2 )( fx 2<br><!-- End of picture text -->

**Figure 2: Scalarisation fitness landscape for hypervolume improvement (** **_lef_ ; with reference vector** r = (2, 2) **), dominance ranking (** **_middle_ ) and minimum signed distance (** **_right_ ) in a hypothetical two-objective space with respect to a data set shown in red (non-dominated) and black (dominated) squares. Lightly shaded areas represent higher fitness, so that maximising a scalarisation should lead to improving the current estimated Pareto set** P<sup>∗</sup> **.** 

dominance ranking (Figure:2 _middle_ ) is proportional to the number of points that dominate a given point, and clearly does not discriminate between solutions in the non-dominated space. Te figure demonstrates the dominance preserving property: maximising any of these measures should select solutions that improve P<sup>∗</sup> . 

### **5 ILLUSTRATION** 

To demonstrate the performance of the proposed strategies, we selected test problems of varying difficulty from the popular DTLZ [7] and WFG [14] problem suites. Te selected test problems and relevant setings are summarised in Table 1. 

**Table 1: Selected test problems and relevant set up.** 

|Problem|Parameters<sup>2</sup>|Objectives|Reference vector|
|---|---|---|---|
||_n_|_D_|r|
|DTLZ1|6|3|(400,400,400)|
|DTLZ2|6|3|(2.5,2.5,2.5)|
|DTLZ5|6|6|(2.5,2.5,2.5,2.5,2.5,2.5)|
|DTLZ7|6|4|(1,1,1,50)|
|WFG1|6|2|(10,10)|
|WFG2|6|2|(10,10)|



Te primary benefit of using these problems is that the Pareto set, and consequently the Pareto front, is known. Tus it allows us to either compute or approximate the optimal hypervolume [30] and can be used as a yardstick for competing methods. Te Pareto set for DTLZ1 is a simplex with vertices at 0.5 in three dimensional objective space with many local fronts. For DTLZ2, the optimal front is a unit sphere in the positive octant. Te shape of the Pareto front for DTLZ5 is unclear for four or more objectives [14]. In four dimensional objective space, DTLZ7 has a Pareto set that produces 2<sup>4−1</sup> = 8 disconnected Pareto-optimal regions. WFG1 has flat regions in the Pareto front and is strongly biased towards smaller values of the decision variables. Te Pareto front for WFG2 consists of disconnected regions. Using the geometry of the DTLZ1 and DTLZ2 fronts, we calculated the optimal hypervolume. For the other problems, we approximated the optimal hypervolume with 

10<sup>4</sup> , 10<sup>5</sup> and 10<sup>6</sup> random members from the Pareto set for two, four and six objectives respectively. 

We compare the proposed strategies with SMS-EGO (known for performance) [24, 28], ParEGO (known for speed) [20] and maximin Latin Hypercube Samples (LHS) with equal budget. Following the suggestions in [24], we implemented the dominance comparison in C for SMS-EGO. In ParEGO, we used 20 and 21 scalarising vectors for four and six objective problems respectively. Te rest of the setings are standard for these algorithms, unless explicitly specified. It should be noted that SMS-EGO and ParEGO have not been tested in more than three objectives before in the literature. 

In our experiments, we consider 11 runs of each method on any problem, starting from 11 _n_ − 1 = 65 initial maximin LHS samples of the _n_ = 6 dimensional decision space, and a budget of 250 function evaluations. Tese simulation runs are matched: different methods use the same initial design for a specific run and a specific problem; except for the competing independent LHS designs with 250 solutions. Te performance of the strategies are investigated in terms of hypervolume of the estimated Pareto set. 

Te infill criterion landscape is usually highly multi-modal. Terefore, we used Bipop-CMA-ES [13]—which is known to perform well in solving multi-modal problems—to locate the solution that maximises an infill criterion. For a fair comparison, we used the same optimiser for SMS-EGO and ParEGO. To locate a good candidate solution, we set the the maximum number of infill criterion evaluation to 20000 _n_ based on the results from a short experiment in optimising any infill criteria. Otherwise, recommended setings for Bipop-CMA-ES were used. 

We used statistical testing methods to determine which strategy performed best [23]. As we used matched initial samples, the Friedman test was performed to determine if there was a difference between all mono- and multi-surrogate approaches. Since we found a significant difference, a further multiple comparison test using the Wilcoxon Signed Rank test with Bonferroni correction was performed to identify the overall winner in a specific problem [3]. Te comparisons between LHS and other methods were performed using the Mann-Whitney-U test [23], as the samples were 

2Te WFG problems are configured with two position and four distance parameters. 

878 

GECCO ’17, July 15-19, 2017, Berlin, Germany 

Alternative Infill Strategies for Expensive Multi-Objective Optimisation 



<!-- Start of picture text -->
DTLZ1 DTLZ2 DTLZ5<br>MSD(0) MSD(2) MSD(3)<br>DomRank(1) DomRank(3) DomRank(1)<br>HypI(1) HypI(3) HypI(1)<br>MPoI(0) MPoI(1) MPoI(3)<br>ParEGO(1) ParEGO(3) ParEGO(3)<br>SMS-EGO(0) SMS-EGO(0) SMS-EGO(0)<br>LHS(6) LHS(6) LHS(6)<br>6 . 325 6 . 350 6 . 375 6 . 400 14 . 50 14 . 75 15 . 00 196 198 200<br>Hypervolume × 10 7 Hypervolume Hypervolume<br>DTLZ7 WFG1 WFG2<br>MSD(2) MSD(3) MSD(1)<br>DomRank(2) DomRank(0) DomRank(0)<br>HypI(1) HypI(0) HypI(1)<br>MPoI(1) MPoI(4) MPoI(0)<br>ParEGO(3) ParEGO(1) ParEGO(0)<br>SMS-EGO(0) SMS-EGO(0) SMS-EGO(0)<br>LHS(6) LHS(6) LHS(6)<br>30 35 40 70 80 90 85 90 95<br>Hypervolume Hypervolume Hypervolume<br><!-- End of picture text -->

**Figure 3: Hypervolume comparison for different strategies in selected test problems over** 11 **runs. Labels on the vertical axes show the method and the number of competing methods (in parentheses) that tested significantly better than the named strategy, so that lower number represent a better methods. Te statistically best method(s) in a problem are highlighted with bold text. Te optimal hypervolume is shown with blue dashed vertical lines.** 



<!-- Start of picture text -->
S-metric (SMS-EGO)<br>1 . 0<br>0 . 8<br>0 . 6<br>0 . 4<br>0 . 2<br>0 . 0<br>0 . 00 0 . 25 0 . 50 0 . 75 1 . 00<br>f 1( x )<br>-2.50 -2.01 -1.52 -1.03 -0.55 -0.06 0.43 0.92<br>Figure 4: Infill fitness landscape in a hypothetical two-<br>objective space with fixed uncertainty  σ = 0.1  in prediction<br>for  S -metric in SMS-EGO. Te red squares depict the current<br>estimated Pareto front F ∗ and the black squares show the<br>dominated solutions in this data set.<br>)( fx 2<br><!-- End of picture text -->

not matched in this case. Te maximum significance level was set to _ρ_ = 0.05 in all cases. Te results are presented in Figure 3. 

Te performance of the competing strategies are generally problem dependent. Based on the results from the statistical testing for performance comparison in all problems, the strategies considered here may be ranked in the following order: SMS-EGO, hypervolume improvement (HypI), dominance ranking (DomRank), minimum probability of improvement (MPoI), minimum signed distance (MSD), ParEGO, and Latin hypercube sampling (LHS). Te simulation runs in Figure 3, indicate that all Bayesian methods are significantly beter than naive LHS designs. Clearly, using a more informed data driven approach is beter with limited budget on function evaluations. 

SMS-EGO performs well across all problems, and it is never significantly worse than any other competing method. In particular, it outperforms other methods in DTLZ2, DTLZ5 and DTLZ7. However, in comparatively more difficult problems: DTLZ1, WFG1 and 

WFG2, which are difficult to model with a GP and a stationary kernel function, at least two of our proposed methods are competitive. 

In contrast, ParEGO is significantly worse than at least one of the proposed methods, except on WFG2 where it is comparable to the best performing methods. In addition, ParEGO is also comparable to SMS-EGO in DTLZ1 and WFG1. However, in these two problems, MSD and HypI are beter than ParEGO. 

For simpler problems, we atribute the performance of a method to its characteristic fitness landscape. Te S-metric in SMS-EGO (Figure 4) is calculated considering optimistic model predictions, i.e. mean predictions scaled down with the associated uncertainties, and thus it extends the atainment surface towards the ideal objective vector. In practice this works well by focusing the search in the vicinity of the current front and in the non-dominated regions. In contrast, MPoI (Figure 1) and DomRank (Figure 2: _middle_ ) infill fitness contours closely follow the atainment surface. Consequently, these promote exploration of solutions at the edges due to the favourable mean predictions combined with large uncertainties far from observed solutions leading to high expected improvement. Although HypI (Figure 2: _lef_ ) and MSD (Figure 2: _right_ ) do not show such bias towards the edges, these prefer the solution closest to the ideal vector and therefore the search may be somewhat misled. 

For harder problems, the subtle differences in infill fitness landscape have litle impact because of an imperfect model. As such, the methods presented here are mostly equivalent. 

We also investigated the computation time for the infill criteria on Intel (i7-2.6GHz) machines.<sup>3</sup> It is clear from Figure 5 that SMSEGO can be computationally expensive. Te high computation cost in evaluating infill criterion is primarily due to hypervolume calculation, and consequently scales poorly with the number of objectives and the number of elements in the current estimated Pareto set. All other strategies are orders of magnitude faster than SMS-EGO, while the performance is comparable in many cases. 

> 3Supplementary Figures and Python code for all the strategies used in this paper are available at: htp://bitbucket.org/arahat/gecco-2017 

879 

GECCO ’17, July 15-19, 2017, Berlin, Germany 

Rahat _et al._ 



<!-- Start of picture text -->
10 0 |P ∗ | = 10 10 0 |P ∗ | = 50 10 0 |P ∗ | = 100<br>10 − 1 10 − 1 10 − 1 Mono-Surrogate<br>MPoI<br>10 − 2 10 − 2 10 − 2 SMS-EGO<br>10 − 3 10 − 3 10 − 3<br>10 − 4 10 − 4 10 − 4<br>2 3 4 5 6 2 3 4 5 6 2 3 4 5 6<br>Number of Objectives Number of Objectives Number of Objectives<br>(seconds) (seconds) (seconds)<br>Time Time Time<br><!-- End of picture text -->

**Figure 5: Comparison of average computation time per infill criterion evaluation over** 1000 **runs between strategies. SMSEGO is highly dependent on the number of objectives and number of elements in the estimated Pareto set. Multi-surrogate MPoI is more expensive than mono-surrogate (including ParEGO) approaches. Both MPoI and mono-surrogate approaches are relatively insensitive to the increase in number of objectives or number of Pareto set elements, and orders of magnitude faster than SMS-EGO.** 

### **6 CONCLUSIONS** 

In this paper, we presented a novel cheaper multi-surrogate infill criterion based on minimum probability of improvement. We have also investigated a range of scalarisation functions modelling hypervolume improvement, dominance ranking or minimum signed distance from the estimated front. Tese effectively enable us to perform multi-objective Bayesian optimisation in a parameter free manner. Te proposed fast infill strategies perform as well as SMSEGO in half of the test problems presented here, while outperforming ParEGO. Current work focuses on the efficacy of various indicator functions and their ensembles within a mono-surrogate EGO framework. 

### **ACKNOWLEDGMENTS** 

Tis research was supported by the Engineering and Physical Sciences Research Council [grant number EP/M017915/1]. 

### **REFERENCES** 

- [1] N. Azzouz, S. Bechikh, and L. Ben Said. 2014. Steady state IBEA assisted by MLP neural networks for expensive multi-objective optimization problems. In _Proceedings of the 2014 Annual Conference on Genetic and Evolutionary Computation_ . ACM, 581–588. 

- [2] J. Bader and E. Zitzler. 2011. HypE: An algorithm for fast hypervolume-based many-objective optimization. _Evolutionary computation_ 19, 1 (2011), 45–76. 

- [3] R. Bender and S. Lange. 2001. Adjusting for multiple testing: when and how? _Journal of Clinical Epidemiology_ 54, 4 (2001), 343 – 349. 

- [4] T. Chugh, Y. Jin, K. Mietinen, J. Hakanen, and K. Sindhya. 2016. A Surrogateassisted Reference Vector Guided Evolutionary Algorithm for Computationally Expensive Many-objective Optimization. _IEEE Transactions on Evolutionary Computation_ PP, 99 (2016), 1–14. 

- [5] C. A. C. Coello, G. B. Lamont, and D. A. Van Veldhuizen. 2007. _Evolutionary algorithms for solving multi-objective problems_ (2nd ed.). Springer. 

- [6] I. Couckuyt, D. Deschrijver, and T. Dhaene. 2014. Fast calculation of multiobjective probability of improvement and expected improvement criteria for Pareto optimization. _Journal of Global Optimization_ 60, 3 (2014), 575–594. 

- [7] K. Deb, L. Tiele, M. Laumanns, and E. Zitzler. 2005. _Scalable test problems for evolutionary multiobjective optimization_ . Springer. 

- [8] M. Emmerich. 2005. _Single-and multi-objective evolutionary design optimization assisted by Gaussian random field metamodels_ . Ph.D. Dissertation. 

- [9] J. E. Fieldsend and R. M. Everson. 2005. Multi-objective optimisation in the presence of uncertainty. In _Te 2005 IEEE Congress on Evolutionary Computation._ , Vol. 1. IEEE, 243–250. 

- [10] M. Fleischer. 2003. Te measure of Pareto optima applications to multi-objective metaheuristics. In _International Conference on Evolutionary Multi-Criterion Optimization_ . Springer, 519–533. 

- [11] C. M. Fonseca and P. J. Fleming. 1993. Genetic Algorithms for Multiobjective Optimization: Formulation, Discussion and Generalization.. In _ICGA_ , Vol. 93. 416–423. 

   - [13] N. Hansen. 2009. Benchmarking a BI-population CMA-ES on the BBOB-2009 function testbed. In _Proceedings of the 11th Annual Conference Companion on Genetic and Evolutionary Computation Conference: Late Breaking Papers_ . ACM, 2389–2396. 

   - [14] S. Huband, P. Hingston, L. Barone, and L. While. 2006. A review of multiobjective test problems and a scalable test problem toolkit. _IEEE Transactions on Evolutionary Computation_ 10, 5 (2006), 477–506. 

   - [15] E. J. Hughes. 2001. Evolutionary multi-objective ranking with uncertainty and noise. In _International Conference on Evolutionary Multi-Criterion Optimization_ . Springer, 329–343. 

   - [16] I. Hupkens, M. Emmerich, and A. Deutz. 2014. Faster computation of expected hypervolume improvement. _arXiv preprint arXiv:1408.7114_ (2014). 

   - [17] D. R. Jones, M. Schonlau, and W. J. Welch. 1998. Efficient Global Optimization of Expensive Black-Box Functions. _Journal of Global Optimization_ 13, 4 (1998), 455–492. 

   - [18] A. J. Keane. 2006. Statistical improvement criteria for use in multiobjective design optimization. _AIAA journal_ 44, 4 (2006), 879–891. 

   - [19] J. P. C. Kleijnen and E. Mehdad. 2014. Multivariate versus univariate Kriging metamodels for multi-response simulation models. _European Journal of Operational Research_ 236, 2 (2014), 573–582. 

   - [20] J. Knowles. 2006. ParEGO: a hybrid algorithm with on-line landscape approximation for expensive multiobjective optimization problems. _IEEE Transactions on Evolutionary Computation_ 10, 1 (Feb 2006), 50–66. 

   - [21] I. Loshchilov, M. Schoenauer, and M. Sebag. 2010. A mono surrogate for multiobjective optimization. In _Proceedings of the 12th annual conference on Genetic and evolutionary computation_ . ACM, 471–478. 

   - [22] M. D. McKay, R. J. Beckman, and W. J. Conover. 2000. A comparison of three methods for selecting values of input variables in the analysis of output from a computer code. _Technometrics_ 42, 1 (2000), 55–61. 

   - [23] J. D. Knowles nad L. Teile and E. Zitzler. 2006. _A Tutorial on the Performance Assesment of Stochastic Multiobjective Optimizers_ . Technical Report TIK214. Computer Engineering and Networks Laboratory, ETH Zurich, Zurich, Switzerland. 

   - [24] W. Ponweiser, T. Wagner, D. Biermann, and M. Vincze. 2008. Multiobjective optimization on a limited budget of evaluations using model-assisted S-metric selection. In _International Conference on Parallel Problem Solving from Nature_ . Springer, 784–794. 

   - [25] C. E. Rasmussen and C. K. I. Williams. 2006. _Gaussian processes for machine learning_ . Te MIT Press. 

   - [26] B. Shahriari, K. Swersky, Z. Wang, R. P. Adams, and N. de Freitas. 2016. Taking the human out of the loop: A review of Bayesian optimization. _Proc. IEEE_ 104, 1 (2016), 148–175. 

   - [27] J. Snoek, H. Larochelle, and R. P. Adams. 2012. Practical Bayesian optimization of machine learning algorithms. In _Advances in neural information processing systems_ . 2951–2959. 

   - [28] T. Wagner, M. Emmerich, A. Deutz, and W. Ponweiser. 2010. On expectedimprovement criteria for model-based multi-objective optimization. In _International Conference on Parallel Problem Solving from Nature_ . Springer, 718–727. 

   - [29] Q. Zhang, W. Liu, E. Tsang, and B. Virginas. 2010. Expensive Multiobjective Optimization by MOEA/D with Gaussian Process Model. _IEEE Transactions on Evolutionary Computation_ 14, 3 (June 2010), 456–474. 

   - [30] E. Zitzler. 1999. _Evolutionary algorithms for multiobjective optimization: Methods and applications_ . Ph.D. Dissertation. 

   - [31] E. Zitzler and S. Kunzli. 2004.¨ Indicator-based selection in multiobjective search. In _International Conference on Parallel Problem Solving from Nature_ . Springer, 832–842. 

- [12] GPy. since 2012. GPy: A Gaussian process framework in Python. htp://github. com/SheffieldML/GPy. (since 2012). 

880 




---

## ANEXO — Camada de texto completa do PDF (get_text)

> Reprodução integral da camada de texto do PDF (todas as páginas, ordem de leitura bruta). Inclui tabelas de resultados e equações que a conversão estruturada acima pode ter omitido. Garante completude textual (imagens continuam omitidas).


<!-- página 1 -->

.
.
Latest updates: hps://dl.acm.org/doi/10.1145/3071178.3071276
.
.
RESEARCH-ARTICLE
Alternative infill strategies for expensive multi-objective optimisation
ALMA A M RAHAT, University of Exeter, Exeter, Devon, U.K.
.
Dr Rahat is an Associate Professor of Data Science. His expertise is in evolutionary and Bayesian
search and optimisation. Particularly, he has worked on developing eﬀective acquisition functions
for optimising single and multi-objective problems and locating the feasible space of solutions.
He has a strong track record of working with industry on a broad range of optimisation problems,
which resulted in numerous articles in top journals and conferences, including a best paper in the
Real-World Applications track at GECCO, and a patent with Hydro International Ltd. Recently,
he has been actively contributing to the Welsh Government's response to the pandemic using
his expertise in machine learning and parameter optimisation with funding from both the Welsh
Government (Co-PI and Co-I; £750k) … (View more)
.
RICHARD M EVERSON, University of Exeter, Exeter, Devon, U.K.
.
JONATHAN EDWARD FIELDSEND, University of Exeter, Exeter, Devon, U.K.
.
.
.
Open Access Support provided by:
.
University of Exeter
.
PDF Download
3071178.3071276.pdf
13 February 2026
Total Citations: 34
Total Downloads: 498
.
.
Published: 01 July 2017
.
.
Citation in BibTeX format
.
.
GECCO '17: Genetic and Evolutionary
Computation Conference
July 15 - 19, 2017
Berlin, Germany
.
.
Conference Sponsors:
SIGEVO
GECCO '17: Proceedings of the Genetic and Evolutionary Computation Conference (July 2017)
hps://doi.org/10.1145/3071178.3071276
ISBN: 9781450349208
.


<!-- página 2 -->

Alternative Infill Strategies
for Expensive Multi-Objective Optimisation
Alma A. M. Rahat∗
University of Exeter
United Kingdom
A.A.M.Rahat@exeter.ac.uk
Richard M. Everson
University of Exeter
United Kingdom
R.M.Everson@exeter.ac.uk
Jonathan E. Fieldsend
University of Exeter
United Kingdom
J.E.Fieldsend@exeter.ac.uk
ABSTRACT
Many multi-objective optimisation problems incorporate computa-
tionally or ﬁnancially expensive objective functions. State-of-the-
art algorithms therefore construct surrogate model(s) of the param-
eter space to objective functions mapping to guide the choice of the
next solution to expensively evaluate. Starting from an initial set of
solutions, an inﬁll criterion — a surrogate-based indicator of quality
— is extremised to determine which solution to evaluate next, until
the budget of expensive evaluations is exhausted. Many success-
ful inﬁll criteria are dependent on multi-dimensional integration,
which may result in inﬁll criteria that are themselves impractically
expensive. We propose a computationally cheap inﬁll criterion
based on the minimum probability of improvement over the esti-
mated Pareto set. We also present a range of set-based scalarisation
methods modelling hypervolume contribution, dominance ratio
and distance measures. Tese permit the use of straightforward ex-
pected improvement as a cheap inﬁll criterion. We investigated the
performance of these novel strategies on standard multi-objective
test problems, and compared them with the popular SMS-EGO and
ParEGO methods. Unsurprisingly, our experiments show that the
best strategy is problem dependent, but in many cases a cheaper
strategy is at least as good as more expensive alternatives.
CCS CONCEPTS
•Computing methodologies →Gaussian processes; Model-
ing methodologies; •Applied computing →Multi-criterion
optimization and decision-making; •Mathematics of comput-
ing →Probabilistic algorithms;
KEYWORDS
Computationally Expensive Optimisation; Eﬃcient Multi-Objective
Optimisation; Inﬁll Criteria; Scalarisation methods.
ACM Reference format:
Alma A. M. Rahat, Richard M. Everson, and Jonathan E. Fieldsend. 2017.
Alternative Inﬁll Strategies for Expensive Multi-Objective Optimisation. In
Proceedings of GECCO ’17, Berlin, Germany, July 15-19, 2017, 8 pages.
DOI: htp://dx.doi.org/10.1145/3071178.3071276
∗Corresponding author
Permission to make digital or hard copies of all or part of this work for personal or
classroom use is granted without fee provided that copies are not made or distributed
for proﬁt or commercial advantage and that copies bear this notice and the full citation
on the ﬁrst page. Copyrights for components of this work owned by others than ACM
must be honored. Abstracting with credit is permited. To copy otherwise, or republish,
to post on servers or to redistribute to lists, requires prior speciﬁc permission and/or a
fee. Request permissions from permissions@acm.org.
GECCO ’17, Berlin, Germany
© 2017 ACM. 978-1-4503-4920-8/17/07...$15.00
DOI: htp://dx.doi.org/10.1145/3071178.3071276
1
INTRODUCTION
Real world multi-objective optimisation problems ofen consist
of computationally or ﬁnancially expensive objective functions.
For instance, design optimisation of mechanical parts may require
inspecting the performance of a design within a ﬂuid environment
using computational ﬂuid dynamics (CFD) simulations. A high
quality CFD simulation may take hours to converge, and thus only
a limited number of designs may be considered in optimisation.
Many eﬀective algorithms have been proposed in the last decade
for expensive multi-objective optimisation, see for example [4, 6,
8, 20, 24]. Generally, these are model-based approaches inspired
by single objective Bayesian global optimisation methods. Based
on an initial set of expensively evaluated solutions, a Bayesian
surrogate model, either for each objective (multi-surrogate) or for
a scalarised representation of the multi-objective problem (mono-
surrogate), is constructed. Regardless of what was modelled, a
surrogate based multi-objective quality indicator, ofen referred to
as an inﬁll criterion, is derived. It is usually much cheaper to evaluate
in comparison to the original objective functions, but frequently
induces a highly multi-modal single objective ﬁtness landscape. As
such evolutionary optimisers perform well in locating promising
solutions using the inﬁll landscape. A candidate solution is then
expensively evaluated, and the surrogate model(s) are retrained.
Te process is repeated until the budget on the expensive function
evaluations is exhausted. Tus, these methods require only a few
hundreds of expensive function evaluations to generate a good
approximation of the optimal trade-oﬀbetween multiple objectives.
One of the major issues with the most eﬀective multi-surrogate
inﬁll criterion is that it ofen requires multi-dimensional integration,
and therefore optimising it may become impractically expensive. A
promising cheaper alternative are mono-surrogate approaches, but
the only example of such an approach in a Bayesian optimisation
framework is ParEGO [20]. Addressing these issues, the major
contributions of this paper are as follows.
• We devise a novel inﬁll criterion based on the minimum
probability of improvement over an estimated Pareto set
as an alternative multi-surrogate approach.
• We propose a range of set-based scalarisation functions
modelling hypervolume improvement, dominance ranking
or minimum signed distance from an estimated Pareto set,
that may be used in a mono-surrogate Bayesian framework,
and therefore promote research on this front.
Te rest of the paper is structured as follows. In Section 2, we
present the required background and the relevant work in the
literature. Te novel inﬁll strategies are described in Sections 3 and
4. We present our results in Section 5. General conclusions are
drawn in Section 6.
873


<!-- página 3 -->

GECCO ’17, July 15-19, 2017, Berlin, Germany
Rahat et al.
2
BACKGROUND
We now present a synthesis of the relevant background material.
2.1
Single Objective Eﬃcient Global
Optimisation (EGO)
Eﬃcient Global Optimisation (EGO) or Bayesian Optimisation (BO) is
a particular area of surrogate-assisted (evolutionary) optimisation.
In practice, it has proved to be a very eﬀective approach for single
objective expensive optimisation problems with limited budget on
the number of true function evaluations. A recent review on the
topic can be found in [26].
EGO is essentially a global search strategy that sequentially sam-
ples the design space at likely locations of the global optimum
[17]. It starts with a space ﬁlling design (e.g. Latin hypercube
sampling [22]) of the parameter space, constructed independent of
the function space. Te solutions from this initial design are then
evaluated with the true function. Using the set of the initial design
parameters and the associated function values as data a regression
model is trained. Promising parameters at which to evaluate the
function can then be located using the surrogate. Frequently the
surrogate model is a stochastic process, usually a Gaussian process
(GP)1. Te beneﬁt of using GPs for regression is that they provide
a posterior predictive distribution given the training data, and thus
querying the surrogate model at any solution in the design space re-
sults in both a mean prediction and the uncertainty associated with
the prediction. Tis ofen enables the closed form calculation of an
inﬁll criterion, that is the expected improvement in function value
(with respect to the best function value observed so far) to be ob-
tained by querying a solution. Tis inﬁll criterion has monotonicity
properties: it is inversely proportional to the predicted mean (with
ﬁxed uncertainty), and directly proportional to the uncertainty in
prediction (with ﬁxed predicted mean). As a consequence, it strikes
a balance between global exploration and myopic exploitation of
the model. Terefore, a strategy for selecting the next solution is
to (expensively) evaluate the parameters that maximise the inﬁll
criterion. Te newly sampled data is then added to the training
database, and a retraining of the GP model ensues. Te process is
repeated until the budget is exhausted.
A single objective optimisation problem may be expressed as:
min
x
f (x),
(1)
where the parameters x ∈Rn and f : Rn →R. With the initial de-
sign D = {(xm, f m = f (xm)}M
m=1 of M samples, a GP model may
be constructed. In essence, a GP is a collection of random variables,
and any ﬁnite number of these have a joint Gaussian distribution
[25]. Te predictive density of the function for parameters x given
by a GP model based on the observations D may be expressed as:
P( ˆf (x) | x, D,θ) = N ( ˆf (x) | µ(x),σ2(x)),
(2)
where the mean and variance are
µ(x) = κ(x,X ) −K−1f
(3)
σ2(x) = κ(x, x) −κ(x,X )⊤K−1κ(X, x).
(4)
Here X ∈RM×n is the matrix of observed parameter values and
f ∈RM is the corresponding vector of the true function evaluations;
1Gaussian Processes subsume Kriging.
thus D = {(X, f)}. Te covariance matrix K ∈RM×M represents
the covariance function κ(x, x′) evaluated for each pair of obser-
vations and κ(x,X ) ∈RM is the vector of covariances between
x and each of the observations. In this paper, we use a ﬂexible
class of covariance functions embodied in the Matern 5/2 kernel,
as recommended for modelling realistic functions [27]. We used
the limited memory BFGS algorithm with 10 restarts to optimise
the kernel hyperparameters; see [12] for details.
Te predicted improvement over the best evaluated solution
so far, f ∗= minm{f m(xm)}, is: I (x, f ∗) = max (f ∗−ˆf (x), 0).
Terefore, the inﬁll criterion (i.e. expected improvement at x) based
on the surrogate model may be expressed as [17]:
α(x, f ∗) =
Z ∞
−∞
I (x, f ∗)P( ˆf | x, D) d ˆf = σ (x) (sΦ(s) −ϕ(s)) , (5)
where s = (f ∗−µ(x))/σ (x), and ϕ(·) and Φ(·) are the Gaussian
probability density function and cumulative density functions. Te
inﬁll criterion is essentially the improvement weighted by the part
of the posterior predictive distribution that lies below the evaluated
minimum f ∗and thus balances the exploitation of solutions which
are very likely to be a litle beter than f ∗with the exploration of
others which may, with lower probability, turn out to be much beter.
Tus maximising this inﬁll criterion estimates where the global
optimum may be given the data and a strategy for determining the
next solution to evaluate is the following maximisation problem:
xM+1 = argmax
x
α(x, ˆf ).
(6)
Te evaluation of the inﬁll criterion in (5) is generally cheap.
Tus an evolutionary algorithms may be used to locate an approxi-
mation of the optimal solution. Tis new solution may then be evalu-
ated with the expensive function f M+1 = f (xM+1), and the dataset
is augmented with the new solution D ←D ∪{(xM+1, f M+1)}.
Te GP is retrained with the augmented dataset D. Te process
is repeated until the limit on the number of expensive function
evaluations is reached.
Note that the inﬁll criterion may induce a highly multi-modal
ﬁtness landscape. Terefore locating the solution that maximises
the expected improvement may require a large number of eval-
uations on the surrogate GP model. Hence, selecting the next
solution to evaluate may be relatively expensive despite the fact
that computing the expected improvement for a single x is cheap.
2.2
Multi-Objective Optimisation Problem
Many real world problems have multiple, ofen conﬂicting, objec-
tives, and it is important to extremise these objectives simultane-
ously [5]. Consider a decision vector x ∈Rn within the feasible
parameter space X. Without loss of generality, a multi-objective
optimisation problem with D objectives may then be expressed as:
min
x F(x) = (f1(x), . . . , fD (x)),
(7)
where fi (x) is the ith objective and F : X ∈Rn →RD generates
the objective space.
Due to the potentially conﬂicting objectives, generally there is
not a unique solution to the optimisation problem, but a range of
solutions trading-oﬀbetween the objectives. Te trade-oﬀbetween
solutions is characterised by the notion of dominance: a solution x
874


<!-- página 4 -->

Alternative Infill Strategies for Expensive Multi-Objective Optimisation
GECCO ’17, July 15-19, 2017, Berlin, Germany
is said to dominate another solution x′, denoted as x ≺x′, iﬀ
fi (x) ≤fi (x′) ∀i = 1, . . . , D and fi (x) < fi (x′) for some i.
(8)
Te set of solutions representing the optimal trade-oﬀbetween the
objectives is referred to as the Pareto set:
P = {x | x′ ⊀x ∀x, x′ ∈X ∧x , x′},
(9)
and the image of the Pareto set in the objective space is known as
the Pareto front F = {F(x) | x ∈P}.
Exactly locating the complete Pareto set may not be possible
within a practical time limit, even for cheap objective functions,
and an approximation is ofen suﬃcient. Terefore, the overall
goal of an eﬀective optimisation approach is to generate a good
approximation of the Pareto set P∗⊆X.
Existing inﬁll strategies for multi-objective optimisation based
on GPs may be categorised in two groups: multi-surrogate and
mono-surrogate approaches. In multi-surrogate approaches, each
objective function fi (x) is modelled. Tese models are ofen con-
sidered to be independent ignoring any potential cross-correlations
between models, which is known to reduce overall uncertainty
in predictions [19]. Te combined models induce a multivariate
Gaussian predictive distribution, with a diagonal covariance ma-
trix: p(ˆF(x) | D) = QD
i p( ˆfi (x) | x, D) = N (ˆF | µ(x), Σ(x)), with
µ(x) = (µ1(x), . . . , µD (x)) and Σ(x) = diag(σ2
1 (x), . . . ,σ2
D (x)),
from which an inﬁll criterion is α(x, ˆF) may be derived. On the
other hand, mono-surrogate approaches aggregate the D objective
functions to generate a scalarised model д(x) ≡д(F(x)). A sur-
rogate model ˆд of the scalarisation is used to compute the inﬁll
criterion α(x, ˆд). In both cases, the next solution to evaluate is
the one which extremises the relevant inﬁll criterion α(·). Algo-
rithm 1 brieﬂy describes these eﬃcient multi-objective optimisation
approaches.
Algorithm 1 Eﬃcient multi-objective optimisation.
Inputs
M : Number of initial samples
T : Budget on expensive function evaluations
Steps
1: X ←LatinHypercubeSampling(X)
▷Generate initial samples
2: f ←F(x ∈X )
▷Expensively evaluate all initial samples
3: for i = M →T do
4:
if MultiSurrogate then
▷Multi-surrogate approach
5:
ˆF ←TrainGP (X, f)
▷Train a model for each objective
6:
x∗←argmaxx α (x, F ∗)
▷Optimise inﬁll criterion
7:
else
▷Mono-surrogate approach
8:
ˆд ←TrainGP (X, д(x ∈X ))
▷Train a model for scalarised
▷objective
9:
x∗←argmaxx α (x, ˆд)
▷Optimise inﬁll criterion
10:
end if
11:
X ←X ∪{x∗}
▷Augment data set with x∗
12:
f ←f ∪{F(x∗)}
▷Expensively evaluate x∗
13:
P∗←nondom(X )
▷Update Pareto set
14:
F ∗←nondom(f)
▷Update Pareto front
15: end for
16: return P∗
Clearly, the inﬁll criterion is a form of scalarisation of the origi-
nal multi-objective problem. Te central distinction between multi-
and mono-surrogate approaches is therefore how this scalarisation
is performed. In multi-surrogates, this scalarisation is based on pre-
dictive models, but in mono-surrogates the scalarisation is based on
the deterministic evaluations of F and uncertainty in the prediction
enters through a predictive model for the scalarisation.
2.3
Related Work
Most eﬀective multi-surrogate strategies use expected hypervolume
improvement as a multi-objective inﬁll criterion. First proposed by
Emmerich [8], the expected hypervolume improvement calculates
the potential gain that may be achieved over the current Pareto set
P∗by augmenting P∗with a solution based on its predictive distri-
bution. Tis, however, involves multidimensional integration over
the non-dominated objective space, which is achieved by decom-
posing the integration volume into disjoint cells and accounting for
the volume weighted by the predictive distribution in each cell. As
such the run time complexity is high and dependent on the number
of solutions |P∗|. Practical improvements on implementations of
the expected hypervolume computation have been proposed by
Hupkens et al. [16] and Couckuyt et al. [6], but the worst case time
complexity is O(|P∗|D) for D = 2, 3 objectives; for more objectives,
the time complexity is conjectured to be even higher [16].
An alternative approach with a proxy for expected hypervolume
improvement, referred to as S-metric selection EGO (SMS-EGO),
was proposed by Ponweiser et al. [24] and later improved by Wag-
ner et al. [28]. In this approach, the posterior predictive distribution
is accounted for implicitly with and overestimated mean predic-
tion by simply subtracting the scaled uncertainty. Tis permits a
deterministic calculation of hypervolume improvement over P∗
for a tentative solution. Although this is comparatively cheaper
to calculate, it still is expensive as the hypervolume calculation
must be performed to evaluate the inﬁll criterion for each tentative
solution. Nonetheless, it has been shown to perform beter or at
least as well as the other methods [28]. We therefore choose to
compare against SMS-EGO in this paper.
Other multi-surrogate inﬁll strategies consider probability of
improvement of a solution over P∗[6, 18], minimum Euclidean
distance of mean predictions over P∗[18], aggregating the poste-
rior prediction with Chebyshev scalarisation and computing the
expected improvement in each scalarisation function within the
MOEA/D framework [29], minimum angle penalised distance or
maximum uncertainty within the reference vector guided evolu-
tionary (RVEA) framework [4], etc.
Te only mono-surrogate approach used within the Bayesian
EGO framework is ParEGO [20]. It uses the normalised objec-
tive function values with an augmented Chebyshev function and
a predeﬁned set of weight vectors to achieve a scalarisation of
the original multi-objective problem. Te scalarised function is
learned using a GP model and the standard expected improvement
is calculated using equation (5). Tis mono-surrogate approach is
known to be the considerably faster than other methods [4]. Tis
is because only one model is maintained and trained (step 8 in
Algorithm 1), and locating a solution that maximises the expected
improvement is cheap because evaluation of the GP is inexpensive.
875


<!-- página 5 -->

GECCO ’17, July 15-19, 2017, Berlin, Germany
Rahat et al.
Terefore more research should be carried out in mono-surrogate
approaches; especially given the success of set-based quality indi-
cators in standard multi-objective evolutionary approaches, see for
example IBEA [31] and HypE [2]. One of the main contributions
of this paper is to propose a range of mono-surrogate strategies
and thus propel research on this front. We therefore compare our
inﬁll criteria with ParEGO as well. Note that other mono-surrogate
approaches, such as model based strategies proposed by Loschilov
et al. [21] and Azzouz et al. [1], do not use GPs, and thus may not
be used within the Bayesian EGO framework.
3
MULTI-SURROGATE APPROACH:
MINIMUM PROBABILITY OF
IMPROVEMENT (MPOI)
In a multi-surrogate approach, we consider independent GP mod-
els for each objective: p( ˆfi (x) | x, D) = N ( ˆf (x) | µi (x),σ2
i (x)). As-
suming that the objectives are independent, the probability that a
solution x dominates another solution x′ is given by [9, 15]:
P(x ≺x′) =
D
Y
i=1
P( ˆfi (x) < ˆfi (x′)),
(10)
where
P( ˆfi (x) < ˆfi (x′)) = 1
2
f
1 + erf

mi (x, x′)/
√
2
g
,
(11)
and mi (x, x′) =
µi (x′) −µi (x)
q
σ2
i (x) + σ2
i (x′)
.
(12)
Note that since we consider the true evaluations to be noise-free,
for any x ∈X, µi (x) = fi (x) and σ2
i (x) = 0.
Comparing an arbitrary solution x′ ∈X with a solution x ∈P∗,
the current estimated Pareto set, there are three mutually exclusive
possibilities: x′ dominates x (x′ ≺x), x′ is dominated by x (x ≺
x′), or they are mutually non-dominated (x ∥x′). Terefore, the
probability that x′ improves upon a solution x ∈P∗is:
P(x′ ≺x or x ∥x′) = 1 −P(x ≺x′).
(13)
Intuitively, this measures the probability mass in the objective space
beyond a solution x ∈P∗, i.e. the space not dominated by x, due
to the multivariate predictive distribution for ˆF. With this notion
of the probability of improvement, we can deﬁne a multi-objective
inﬁll criterion based on least improvement upon any solution from
the current Pareto front F ∗of evaluated solutions:
αp (x′, F ∗) = min
x∈P∗(1 −P(x ≺x′)).
(14)
Tus, in a multi-objective EGO, the next solution to evaluate is:
xM+1 = argmax
x′∈X
αp (x′, F ∗).
(15)
Keane [18] and Couckuyt et al. [6] suggested computing the
probability of improvement over all solutions x ∈P∗, i.e. 1 −
P(S
x∈P∗x ≺x′), as an inﬁll criterion. Again, similar to ex-
pected hypervolume improvement calculations, this requires multi-
dimensional integration by decomposing the non-dominated ob-
jective space into disjoint regions. As such, it is computationally
expensive, especially for many-objective problems. In our formula-
tion of the inﬁll criterion αp (x′, F ∗) in equation (14), we implicitly
cover all the solutions from the current estimated Pareto set P∗by
considering the minimum probability of improvement over P∗. It
is therefore fast to calculate, with the most expensive step being
the calculation of erf(·) function.
3.1
Monotonicity Properties
Te role of an inﬁll criterion is to help us choose a good candidate
solution. Te eﬃcacy of an inﬁll criterion thus depends on how
well it distinguishes between two tentative solutions x′, x′′ ∈X \X.
A sound multi-objective inﬁll criterion must therefore satisfy the
following necessary conditions for two solutions x′ and x′′ [28].
N1 Te dominance relationship should be preserved given that
the uncertainty is equal. Tat is, if µi (x′) < µi (x′′) ∧
σi (x′) = σi (x′′),∀i ∈{1, . . . , D}, then: αp (x′, F ∗) >
αp (x′′, F ∗).
N2 When mean predictions are equal, the inﬁll criterion should
monotonically increase with the uncertainty. Tat is if
µi (x′) = µi (x′′) ∧σi (x′) > σi (x′′),∀i ∈{1, . . . , D}, then:
αp (x′, F ∗) > αp (x′′, F ∗).
Proof. Clearly, from equation (14), it is suﬃcient to prove that
for any solution x ∈P∗, P(x ≺x′) < P(x ≺x′′), for both N1 and
N2 to be true. Tis further implies: it is equivalent to prove that
mi (x, x′) < mi (x, x′′),∀i ∈{1, . . . , D} under the given conditions
(c.f. equations (10) and (11)). As discussed earlier, with no noise
in measurements µi (x) = fi (x) and σi (x) = 0. Now, considering
equation (12), given the same uncertainty in prediction σi (x′) =
σi (x′′), mi (x, x′) < mi (x, x′′) for ith objective iﬀµi (x′) < µi (x′′).
Tus N1 is satisﬁed. Similarly, when the mean predictions are the
same µi (x′) = µi (x′′), then mi (x, x′) < mi (x, x′′) for ith objective
iﬀσi (x′) > σi (x′′). Terefore N2 is satisﬁed. ■
3.2
Inﬁll Fitness Landscape
An inﬁll criterion essentially is a scalar representation of the ob-
jective space. It is therefore interesting to investigate the induced
inﬁll landscape within the objective space.
To achieve a visual impression of the landscape, we consider
evenly distributed samples from the objective space. Considering
each sample as the mean prediction of a multivariate GP, and
seting a ﬁxed uncertainty σ = 0.1, we calculate the minimum
probability of improvement. In Figure 1, we show the resulting
characterisation of the objective space. We can observe a clear
indication that optimising this inﬁll criteria promotes sampling in
the non-dominated region, and hence it is likely to improve the
current estimation of the Pareto set. It is also evident that the
single objective inﬁll criteria is highly multi-modal. It should be
noted that in reality the characterisation using trained models may
appear diﬀerent due to variations in uncertainty. Nonetheless, the
inﬁll criteria adheres to the monotonicity properties as described
in Section 3.1.
4
MONO-SURROGATE APPROACH:
INDICATOR BASED SCALARISATION
To the best of our knowledge the only scalarising function used
in a mono-surrogate framework is an augmented Chebyshev func-
tion [20]. However, it is possible to model other set-based quality
indicators that measure the rank of a solution within the expen-
sively sampled solutions instead. Such scalarised ranking can then
876


<!-- página 6 -->

Alternative Infill Strategies for Expensive Multi-Objective Optimisation
GECCO ’17, July 15-19, 2017, Berlin, Germany
0.00
0.25
0.50
0.75
1.00
f1(x)
0.0
0.2
0.4
0.6
0.8
1.0
f2(x)
0.00 0.13 0.27 0.40 0.53 0.67 0.80 0.93
Minimum Probability of Improvement (MPoI)
Figure 1:
Inﬁll ﬁtness landscape in a hypothetical two-
objective space with ﬁxed uncertainty σ = 0.1 in prediction
for minimum probability of improvement over current esti-
mated Pareto front F ∗(red squares). Lighter shades depict
higher probability of improvement, and thus these areas are
preferred over darker areas. Maximising the criterion pro-
motes sampling in the non-dominated objective space. Te
black squares show the dominated solutions in the data set.
Te contours are unaﬀected by the dominated solutions.
be modelled with a GP and used within the EGO framework. So
long as a scalarisation function preserves dominance relationship,
maximising such scalarisation should improve the current set [31].
Although many diﬀerent scalarisation methods may be used, in
this section we present three scalarisation methods.
4.1
Hypervolume Improvement (HypI)
Te hypervolume is a set-based quality indicator that measures the
objective space covered between a non-dominated set and a prede-
ﬁned reference vector [30]. It is an exceptional set-based indicator
as Fleischer proved that maximising hypervolume is equivalent
to locating the optimal Pareto set [10]. We therefore propose a
scalarisation based on hypervolume improvement.
A set of expensively sampled solutions D = {(X, f = F (X ))} can
be ranked according to the “Pareto shell” in which they lie. Let
the ﬁrst Pareto shell be the estimated Pareto set for X: P′
1 = P∗=
nondom(X ), where the nondom(·) function returns the maximal
non-dominated subset of its argument. Ten successive Pareto
shells P′
l (l > 1) are deﬁned as:
P′
l = nondom(X \ ∪i<l Pi ).
(16)
Te hypervolume indicator for a set X is the volume of objective
space which is dominated by solutions in X and which dominates
a reference vector r [30]:
H (X, r) = volz{F(x) ≺z ≺r ∧x ∈X }.
(17)
In order to deﬁne the hypervolume improvement due to a solu-
tion x, we consider the ﬁrst Pareto shell that contains no solutions
that dominate x; denote this shell by P′
k. Ten the hypervolume
improvement for x is the hypervolume corresponding to P′
k aug-
mented with x:
дh(x,X ) = H (x ∪P′
k,r).
(18)
Here the function дh(x,X ) generates a set-based scalarisation of
the original multi-objective problem for the set of sampled solu-
tions. Clearly, if a solution x′′ is dominated by another x′, then
дh(x′,X ) > дh(x′′,X ). Terefore we may learn a function ˆдh(x)
and use the expected improvement in equation (5) within EGO
framework in order to maximise the hypervolume improvement (a
unary indicator), and thus improve upon the current approximation
of the Pareto set P∗.
Note that this set-based scalarisation is diﬀerent from the formu-
lation HypE [2]. In HypE, the scalarisation does not diﬀerentiate
between the dominated solutions during selection, and hence all
dominated solutions have the same scalar value associated with the,,
creating a plateau of equal ﬁtness behind P∗. Using a GP to model
the scalarisation thus has limited spatial information, which may
hinder EGO’s global exploration. In contrast, we base our scalarisa-
tion purely on dominance rank based hypervolume improvement,
and in order to generate a positive ﬁtness gradient towards the
Pareto set, aiding the EGO process.
4.2
Dominance Ranking (DomRank)
In MOGA [11], a ﬁtness assignment scheme based on dominance
was proposed. In essence, a solution is assigned a rank in proportion
to the number of already-evaluated solutions that dominate it. We
use a straightforward adaptation of this.
Given a set of solutions X, a solution can be dominated by at
most |X | −1 others. Te ranking strategy is deﬁned as:
дc (x,X ) = 1 −|{x′|x′ ≺x ∧x , x′,∀x, x′ ∈X}|
|X | −1
.
(19)
Terefore, the current estimated Pareto set members xa ∈P∗have
the maximum rank дc (xa,X ) = 1. Similarly, a solution xb that is
dominated by all other members is assigned rank дc (xb,X ) = 0.
By deﬁnition it is dominance preserving: if x′ ≺x′′, then
дc (x′,X ) > дc (x′′,X ). It is therefore suitable for use in the EGO
framework.
4.3
Minimum Signed Distance (MSD)
Distance of a solution from the current estimate of the Pareto front is
clearly important. Here, we consider the minimum signed distance
of a solution from P∗as a ranking strategy:
дd (x,X ) = min
x′∈P∗d(x′, x),
(20)
where d(x′, x) = PD
i=1 fi (x′) −fi (x) is a signed distance. Similar to
the other measures, it is also dominance preserving and therefore
if x′ ≺x′′, then дd (x′,X ) > дd (x′′,X ).
4.4
Scalarisation Fitness Landscape
Te mono-surrogate strategies also induce a ﬁtness landscape in
the objective space, which can be informatively visualised. Rather
than considering solutions from the decision space, we use evenly
distributed points in the multi-dimensional objective space, and
compute the ﬁtness. In Figure 2, the resulting characterisations of
the objective space is presented.
Te hypervolume improvement (Figure 2 lef) and the minimum
signed distance (Figure 2 right) both show strong selection pref-
erence towards the minimum of both objectives. In comparison,
877


<!-- página 7 -->

GECCO ’17, July 15-19, 2017, Berlin, Germany
Rahat et al.
0.00
0.25
0.50
0.75
1.00
f1(x)
0.0
0.2
0.4
0.6
0.8
1.0
f2(x)
0.74 1.26 1.78 2.29 2.81 3.33 3.85 4.36
0.00
0.25
0.50
0.75
1.00
f1(x)
0.0
0.2
0.4
0.6
0.8
1.0
f2(x)
0.00 0.13 0.27 0.40 0.53 0.67 0.80 0.93
0.00
0.25
0.50
0.75
1.00
f1(x)
0.0
0.2
0.4
0.6
0.8
1.0
f2(x)
-1.69 -1.35 -1.00 -0.66 -0.31 0.04 0.38 0.73
Hypervolume Improvement (HypI)
Dominance Ranking (DomRank)
Min. Signed Distance (MSD)
Figure 2: Scalarisation ﬁtness landscape for hypervolume improvement (lef; with reference vector r = (2, 2)), dominance
ranking (middle) and minimum signed distance (right) in a hypothetical two-objective space with respect to a data set shown
in red (non-dominated) and black (dominated) squares. Lightly shaded areas represent higher ﬁtness, so that maximising a
scalarisation should lead to improving the current estimated Pareto set P∗.
dominance ranking (Figure:2 middle) is proportional to the number
of points that dominate a given point, and clearly does not discrim-
inate between solutions in the non-dominated space. Te ﬁgure
demonstrates the dominance preserving property: maximising any
of these measures should select solutions that improve P∗.
5
ILLUSTRATION
To demonstrate the performance of the proposed strategies, we
selected test problems of varying diﬃculty from the popular DTLZ
[7] and WFG [14] problem suites. Te selected test problems and
relevant setings are summarised in Table 1.
Table 1: Selected test problems and relevant set up.
Problem Parameters2
Objectives
Reference vector
n
D
r
DTLZ1
6
3
(400, 400, 400)
DTLZ2
6
3
(2.5, 2.5, 2.5)
DTLZ5
6
6
(2.5, 2.5, 2.5, 2.5, 2.5, 2.5)
DTLZ7
6
4
(1, 1, 1, 50)
WFG1
6
2
(10, 10)
WFG2
6
2
(10, 10)
Te primary beneﬁt of using these problems is that the Pareto
set, and consequently the Pareto front, is known. Tus it allows us
to either compute or approximate the optimal hypervolume [30]
and can be used as a yardstick for competing methods. Te Pareto
set for DTLZ1 is a simplex with vertices at 0.5 in three dimensional
objective space with many local fronts. For DTLZ2, the optimal
front is a unit sphere in the positive octant. Te shape of the Pareto
front for DTLZ5 is unclear for four or more objectives [14]. In four
dimensional objective space, DTLZ7 has a Pareto set that produces
24−1 = 8 disconnected Pareto-optimal regions. WFG1 has ﬂat
regions in the Pareto front and is strongly biased towards smaller
values of the decision variables. Te Pareto front for WFG2 consists
of disconnected regions. Using the geometry of the DTLZ1 and
DTLZ2 fronts, we calculated the optimal hypervolume. For the
other problems, we approximated the optimal hypervolume with
2Te WFG problems are conﬁgured with two position and four distance parameters.
104, 105 and 106 random members from the Pareto set for two, four
and six objectives respectively.
We compare the proposed strategies with SMS-EGO (known for
performance) [24, 28], ParEGO (known for speed) [20] and maximin
Latin Hypercube Samples (LHS) with equal budget. Following the
suggestions in [24], we implemented the dominance comparison in
C for SMS-EGO. In ParEGO, we used 20 and 21 scalarising vectors
for four and six objective problems respectively. Te rest of the
setings are standard for these algorithms, unless explicitly speciﬁed.
It should be noted that SMS-EGO and ParEGO have not been tested
in more than three objectives before in the literature.
In our experiments, we consider 11 runs of each method on
any problem, starting from 11n −1 = 65 initial maximin LHS
samples of the n = 6 dimensional decision space, and a budget
of 250 function evaluations. Tese simulation runs are matched:
diﬀerent methods use the same initial design for a speciﬁc run
and a speciﬁc problem; except for the competing independent LHS
designs with 250 solutions. Te performance of the strategies are
investigated in terms of hypervolume of the estimated Pareto set.
Te inﬁll criterion landscape is usually highly multi-modal. Tere-
fore, we used Bipop-CMA-ES [13]—which is known to perform well
in solving multi-modal problems—to locate the solution that max-
imises an inﬁll criterion. For a fair comparison, we used the same
optimiser for SMS-EGO and ParEGO. To locate a good candidate
solution, we set the the maximum number of inﬁll criterion eval-
uation to 20000n based on the results from a short experiment in
optimising any inﬁll criteria. Otherwise, recommended setings for
Bipop-CMA-ES were used.
We used statistical testing methods to determine which strat-
egy performed best [23]. As we used matched initial samples, the
Friedman test was performed to determine if there was a diﬀer-
ence between all mono- and multi-surrogate approaches. Since we
found a signiﬁcant diﬀerence, a further multiple comparison test
using the Wilcoxon Signed Rank test with Bonferroni correction
was performed to identify the overall winner in a speciﬁc problem
[3]. Te comparisons between LHS and other methods were per-
formed using the Mann-Whitney-U test [23], as the samples were
878


<!-- página 8 -->

Alternative Infill Strategies for Expensive Multi-Objective Optimisation
GECCO ’17, July 15-19, 2017, Berlin, Germany
6.325
6.350
6.375
6.400
Hypervolume
×107
LHS(6)
SMS-EGO(0)
ParEGO(1)
MPoI(0)
HypI(1)
DomRank(1)
MSD(0)
DTLZ1
14.50
14.75
15.00
Hypervolume
LHS(6)
SMS-EGO(0)
ParEGO(3)
MPoI(1)
HypI(3)
DomRank(3)
MSD(2)
DTLZ2
196
198
200
Hypervolume
LHS(6)
SMS-EGO(0)
ParEGO(3)
MPoI(3)
HypI(1)
DomRank(1)
MSD(3)
DTLZ5
30
35
40
Hypervolume
LHS(6)
SMS-EGO(0)
ParEGO(3)
MPoI(1)
HypI(1)
DomRank(2)
MSD(2)
DTLZ7
70
80
90
Hypervolume
LHS(6)
SMS-EGO(0)
ParEGO(1)
MPoI(4)
HypI(0)
DomRank(0)
MSD(3)
WFG1
85
90
95
Hypervolume
LHS(6)
SMS-EGO(0)
ParEGO(0)
MPoI(0)
HypI(1)
DomRank(0)
MSD(1)
WFG2
Figure 3: Hypervolume comparison for diﬀerent strategies in selected test problems over 11 runs. Labels on the vertical axes
show the method and the number of competing methods (in parentheses) that tested signiﬁcantly better than the named
strategy, so that lower number represent a better methods. Te statistically best method(s) in a problem are highlighted with
bold text. Te optimal hypervolume is shown with blue dashed vertical lines.
0.00
0.25
0.50
0.75
1.00
f1(x)
0.0
0.2
0.4
0.6
0.8
1.0
f2(x)
-2.50 -2.01 -1.52 -1.03 -0.55 -0.06 0.43 0.92
S-metric (SMS-EGO)
Figure 4:
Inﬁll ﬁtness landscape in a hypothetical two-
objective space with ﬁxed uncertainty σ = 0.1 in prediction
for S-metric in SMS-EGO. Te red squares depict the current
estimated Pareto front F ∗and the black squares show the
dominated solutions in this data set.
not matched in this case. Te maximum signiﬁcance level was set
to ρ = 0.05 in all cases. Te results are presented in Figure 3.
Te performance of the competing strategies are generally prob-
lem dependent. Based on the results from the statistical testing
for performance comparison in all problems, the strategies con-
sidered here may be ranked in the following order: SMS-EGO,
hypervolume improvement (HypI), dominance ranking (DomRank),
minimum probability of improvement (MPoI), minimum signed
distance (MSD), ParEGO, and Latin hypercube sampling (LHS). Te
simulation runs in Figure 3, indicate that all Bayesian methods are
signiﬁcantly beter than naive LHS designs. Clearly, using a more
informed data driven approach is beter with limited budget on
function evaluations.
SMS-EGO performs well across all problems, and it is never sig-
niﬁcantly worse than any other competing method. In particular, it
outperforms other methods in DTLZ2, DTLZ5 and DTLZ7. How-
ever, in comparatively more diﬃcult problems: DTLZ1, WFG1 and
WFG2, which are diﬃcult to model with a GP and a stationary ker-
nel function, at least two of our proposed methods are competitive.
In contrast, ParEGO is signiﬁcantly worse than at least one of the
proposed methods, except on WFG2 where it is comparable to the
best performing methods. In addition, ParEGO is also comparable
to SMS-EGO in DTLZ1 and WFG1. However, in these two problems,
MSD and HypI are beter than ParEGO.
For simpler problems, we atribute the performance of a method
to its characteristic ﬁtness landscape. Te S-metric in SMS-EGO
(Figure 4) is calculated considering optimistic model predictions,
i.e. mean predictions scaled down with the associated uncertain-
ties, and thus it extends the atainment surface towards the ideal
objective vector. In practice this works well by focusing the search
in the vicinity of the current front and in the non-dominated re-
gions. In contrast, MPoI (Figure 1) and DomRank (Figure 2: middle)
inﬁll ﬁtness contours closely follow the atainment surface. Conse-
quently, these promote exploration of solutions at the edges due to
the favourable mean predictions combined with large uncertainties
far from observed solutions leading to high expected improvement.
Although HypI (Figure 2: lef) and MSD (Figure 2: right) do not
show such bias towards the edges, these prefer the solution clos-
est to the ideal vector and therefore the search may be somewhat
misled.
For harder problems, the subtle diﬀerences in inﬁll ﬁtness land-
scape have litle impact because of an imperfect model. As such,
the methods presented here are mostly equivalent.
We also investigated the computation time for the inﬁll criteria
on Intel (i7-2.6GHz) machines.3 It is clear from Figure 5 that SMS-
EGO can be computationally expensive. Te high computation
cost in evaluating inﬁll criterion is primarily due to hypervolume
calculation, and consequently scales poorly with the number of
objectives and the number of elements in the current estimated
Pareto set. All other strategies are orders of magnitude faster than
SMS-EGO, while the performance is comparable in many cases.
3Supplementary Figures and Python code for all the strategies used in this paper are
available at: htp://bitbucket.org/arahat/gecco-2017
879


<!-- página 9 -->

GECCO ’17, July 15-19, 2017, Berlin, Germany
Rahat et al.
2
3
4
5
6
Number of Objectives
10−4
10−3
10−2
10−1
100
Time (seconds)
|P∗| = 10
2
3
4
5
6
Number of Objectives
10−4
10−3
10−2
10−1
100
Time (seconds)
|P∗| = 50
2
3
4
5
6
Number of Objectives
10−4
10−3
10−2
10−1
100
Time (seconds)
|P∗| = 100
Mono-Surrogate
MPoI
SMS-EGO
Figure 5: Comparison of average computation time per inﬁll criterion evaluation over 1000 runs between strategies. SMS-
EGO is highly dependent on the number of objectives and number of elements in the estimated Pareto set. Multi-surrogate
MPoI is more expensive than mono-surrogate (including ParEGO) approaches. Both MPoI and mono-surrogate approaches
are relatively insensitive to the increase in number of objectives or number of Pareto set elements, and orders of magnitude
faster than SMS-EGO.
6
CONCLUSIONS
In this paper, we presented a novel cheaper multi-surrogate inﬁll
criterion based on minimum probability of improvement. We have
also investigated a range of scalarisation functions modelling hy-
pervolume improvement, dominance ranking or minimum signed
distance from the estimated front. Tese eﬀectively enable us to
perform multi-objective Bayesian optimisation in a parameter free
manner. Te proposed fast inﬁll strategies perform as well as SMS-
EGO in half of the test problems presented here, while outper-
forming ParEGO. Current work focuses on the eﬃcacy of various
indicator functions and their ensembles within a mono-surrogate
EGO framework.
ACKNOWLEDGMENTS
Tis research was supported by the Engineering and Physical Sci-
ences Research Council [grant number EP/M017915/1].
REFERENCES
[1] N. Azzouz, S. Bechikh, and L. Ben Said. 2014. Steady state IBEA assisted by MLP
neural networks for expensive multi-objective optimization problems. In Pro-
ceedings of the 2014 Annual Conference on Genetic and Evolutionary Computation.
ACM, 581–588.
[2] J. Bader and E. Zitzler. 2011. HypE: An algorithm for fast hypervolume-based
many-objective optimization. Evolutionary computation 19, 1 (2011), 45–76.
[3] R. Bender and S. Lange. 2001. Adjusting for multiple testing: when and how?
Journal of Clinical Epidemiology 54, 4 (2001), 343 – 349.
[4] T. Chugh, Y. Jin, K. Mietinen, J. Hakanen, and K. Sindhya. 2016. A Surrogate-
assisted Reference Vector Guided Evolutionary Algorithm for Computationally
Expensive Many-objective Optimization. IEEE Transactions on Evolutionary
Computation PP, 99 (2016), 1–14.
[5] C. A. C. Coello, G. B. Lamont, and D. A. Van Veldhuizen. 2007. Evolutionary
algorithms for solving multi-objective problems (2nd ed.). Springer.
[6] I. Couckuyt, D. Deschrijver, and T. Dhaene. 2014. Fast calculation of multiobjec-
tive probability of improvement and expected improvement criteria for Pareto
optimization. Journal of Global Optimization 60, 3 (2014), 575–594.
[7] K. Deb, L. Tiele, M. Laumanns, and E. Zitzler. 2005. Scalable test problems for
evolutionary multiobjective optimization. Springer.
[8] M. Emmerich. 2005. Single-and multi-objective evolutionary design optimization
assisted by Gaussian random ﬁeld metamodels. Ph.D. Dissertation.
[9] J. E. Fieldsend and R. M. Everson. 2005. Multi-objective optimisation in the
presence of uncertainty. In Te 2005 IEEE Congress on Evolutionary Computation.,
Vol. 1. IEEE, 243–250.
[10] M. Fleischer. 2003. Te measure of Pareto optima applications to multi-objective
metaheuristics. In International Conference on Evolutionary Multi-Criterion Opti-
mization. Springer, 519–533.
[11] C. M. Fonseca and P. J. Fleming. 1993. Genetic Algorithms for Multiobjective
Optimization: Formulation, Discussion and Generalization.. In ICGA, Vol. 93.
416–423.
[12] GPy. since 2012. GPy: A Gaussian process framework in Python. htp://github.
com/SheﬃeldML/GPy. (since 2012).
[13] N. Hansen. 2009. Benchmarking a BI-population CMA-ES on the BBOB-2009
function testbed. In Proceedings of the 11th Annual Conference Companion on
Genetic and Evolutionary Computation Conference: Late Breaking Papers. ACM,
2389–2396.
[14] S. Huband, P. Hingston, L. Barone, and L. While. 2006. A review of multiob-
jective test problems and a scalable test problem toolkit. IEEE Transactions on
Evolutionary Computation 10, 5 (2006), 477–506.
[15] E. J. Hughes. 2001. Evolutionary multi-objective ranking with uncertainty and
noise. In International Conference on Evolutionary Multi-Criterion Optimization.
Springer, 329–343.
[16] I. Hupkens, M. Emmerich, and A. Deutz. 2014. Faster computation of expected
hypervolume improvement. arXiv preprint arXiv:1408.7114 (2014).
[17] D. R. Jones, M. Schonlau, and W. J. Welch. 1998. Eﬃcient Global Optimization
of Expensive Black-Box Functions. Journal of Global Optimization 13, 4 (1998),
455–492.
[18] A. J. Keane. 2006. Statistical improvement criteria for use in multiobjective design
optimization. AIAA journal 44, 4 (2006), 879–891.
[19] J. P. C. Kleijnen and E. Mehdad. 2014. Multivariate versus univariate Kriging
metamodels for multi-response simulation models. European Journal of Opera-
tional Research 236, 2 (2014), 573–582.
[20] J. Knowles. 2006. ParEGO: a hybrid algorithm with on-line landscape approxi-
mation for expensive multiobjective optimization problems. IEEE Transactions
on Evolutionary Computation 10, 1 (Feb 2006), 50–66.
[21] I. Loshchilov, M. Schoenauer, and M. Sebag. 2010. A mono surrogate for multi-
objective optimization. In Proceedings of the 12th annual conference on Genetic
and evolutionary computation. ACM, 471–478.
[22] M. D. McKay, R. J. Beckman, and W. J. Conover. 2000. A comparison of three
methods for selecting values of input variables in the analysis of output from a
computer code. Technometrics 42, 1 (2000), 55–61.
[23] J. D. Knowles nad L. Teile and E. Zitzler. 2006. A Tutorial on the Performance
Assesment of Stochastic Multiobjective Optimizers. Technical Report TIK214. Com-
puter Engineering and Networks Laboratory, ETH Zurich, Zurich, Switzerland.
[24] W. Ponweiser, T. Wagner, D. Biermann, and M. Vincze. 2008. Multiobjective
optimization on a limited budget of evaluations using model-assisted S-metric
selection. In International Conference on Parallel Problem Solving from Nature.
Springer, 784–794.
[25] C. E. Rasmussen and C. K. I. Williams. 2006. Gaussian processes for machine
learning. Te MIT Press.
[26] B. Shahriari, K. Swersky, Z. Wang, R. P. Adams, and N. de Freitas. 2016. Taking
the human out of the loop: A review of Bayesian optimization. Proc. IEEE 104, 1
(2016), 148–175.
[27] J. Snoek, H. Larochelle, and R. P. Adams. 2012. Practical Bayesian optimization
of machine learning algorithms. In Advances in neural information processing
systems. 2951–2959.
[28] T. Wagner, M. Emmerich, A. Deutz, and W. Ponweiser. 2010. On expected-
improvement criteria for model-based multi-objective optimization. In Interna-
tional Conference on Parallel Problem Solving from Nature. Springer, 718–727.
[29] Q. Zhang, W. Liu, E. Tsang, and B. Virginas. 2010. Expensive Multiobjective
Optimization by MOEA/D with Gaussian Process Model. IEEE Transactions on
Evolutionary Computation 14, 3 (June 2010), 456–474.
[30] E. Zitzler. 1999. Evolutionary algorithms for multiobjective optimization: Methods
and applications. Ph.D. Dissertation.
[31] E. Zitzler and S. K¨unzli. 2004. Indicator-based selection in multiobjective search.
In International Conference on Parallel Problem Solving from Nature. Springer,
832–842.
880



---

## ANEXO — Conteúdo textual das imagens (OCR)

> Texto extraído por OCR (Apple Vision) das figuras/imagens do PDF — apenas conteúdo NOVO, ausente da camada de texto (labels de eixos, legendas internas, tabelas/equações rasterizadas, slides). OCR de fórmulas é aproximado.

### Página 6
*(figura em y≈74–271)*
- Infill fitness landscape in a hypotl
- space with fixed uncertainty o = 0.1 in

### Página 7
*(figura em y≈74–271)*
- Hypervolume Improvement (Hypl)
- 2: Scalarisation fitness landscape for hypervolume improvement (left; with reference vector r =
- (non-dominated) and black (dominated) squares. Lightly shaded areas represent higher fitness, so that maximisin

### Página 8
*(figura em y≈298–496)*
- he optimal hypervolume iS shown with
- fill fitness landscape in a hypothet
- O = 0.1 in
- ace with fixed uncertainty
- c in SMS-EGO. The red squares depict th
*(figura em y≈78–264)*
- Hypl(1)
- MPol(0)
- ParEGO(1)1
- LHS(6) | o -H
- MSD(2)1
- Hypl(1)
- MPol(1)1
*(figura em y≈80–264)*
- Hypl(3)
- MPol(1)
- ParEGO(3)1
- LHS(6) | + CO-
- Hypl(0)
- MPol(4)
- LHS(6) - 40
*(figura em y≈80–264)*
- Hypl(1)
- MPol(3)
- LHS(6) ° +0-4
- MSD(1) o
- Hypl(1)
- MPol(0)
- LHS(6)1

### Página 9
*(figura em y≈43–228)*
- IP* = 10
- IP* = 50
- IP* = 100
- MPol
- (spuodes) awl
- 10-1. 10-2. Sons by mule
- (spuodas) awl
- 10-4L
- infill criterion evaluation over 1000 runs between strategies. SMS-
- 1Pol is more expensive than mono-surrogate (including ParEGO) approaches. Both MPoI and mono-surrogate approaches
