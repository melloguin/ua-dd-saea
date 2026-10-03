# mtm6. Hypervolume-based Expected Improvement- Monotonicity Properties and Exact Computation

> Fonte (PDF original): mtm6. Hypervolume-based Expected Improvement- Monotonicity Properties and Exact Computation.pdf
> Extraído com pymupdf4llm (texto + tabelas + números; imagens omitidas). Páginas: 8.

---

# Hypervolume-based Expected Improvement: Monotonicity Properties and Exact Computation 

Michael T.M. Emmerich Andr´e H. Deutz Jan Willem Klinkenberg Leiden Institute of Leiden Institute of Leiden Institute of Advanced Computer Science Advanced Computer Science Advanced Computer Science Leiden University Leiden University Leiden University Leiden, The Netherlands Leiden, The Netherlands Leiden, The Netherlands Email: emmerich@liacs.nl Email: deutz@liacs.nl Email: jklinken@liacs.nl 

**_Abstract_ —The expected improvement (EI) is a well established criterion in Bayesian global optimization (BGO) and metamodelassisted evolutionary computation, both applied in optimization with costly function evaluations. Recently, it has been adopted in different ways to multiobjective optimization. A promising approach to formulate the expected improvement in this context, is to base it on the hypervolume indicator. Given the Bayesian model of the optimization landscape, the EI in hypervolume computes the expected gain in attained hypervolume for a given input point. Although a formulation of this expected improvement is relatively straightforward, its computation and mathematical properties are still to be investigated. This paper will outline and derive an algorithm for the exact computation of the proposed hypervolume-based EI. Moreover, this paper establishes monotonicity properties of the expected improvement. In particular the effect of the predictive distribution’s variance on the hypervolume-based EI and elementary properties of the EI landscape are studied. The monotonicity properties will reveal regions where Pareto front approximations can be improved as well as underexplored regions that are favored by the hypervolumebased expected improvement. A first numerical example is included that illustrates the behavior of the hypervolume-based EI in the multiobjective BGO framework.** 

## I. INTRODUCTION 

In global optimization with expensive black-box models it is common practice to consider a metamodel that is based on previous function evaluations [10]. This metamodel can be used to guide the search towards promising or less explored regions of the search space [5]. Gaussian process (and also Kriging) models allow to compute, for each input point, the mean and the variance of a _predictive distribution_ quantifying the probability of different results of the precise evaluation. They assume a correlation of space-indexed distributions that is based on distance in the index space [7]. 

Different criteria for selecting promising points based on Gaussian process models have been suggested in the literature [4], [7]. Among them, expected improvement [18] became very popular as a measure and part of standard algorithms, such as efficient global optimization (EGO) [13]. The expected improvement, as defined in [18] and [13], measures, for a given predictive distribution of an input point, the expected gain in closeness to the global optimum. 

The generalization of the expected improvement to multiobjective optimization is a subject of ongoing research. Different 

proposals have been made by [6], [11], [15],[17], [19], and [20]. In [17] the EGO approach has been generalized to multiobjective optimization, using Tchebyscheff scalarization with dynamically changing weights for the objective functions for computing the expected improvement. In [15] the expected improvement is interpreted as the centroid of the improvement distribution. In multiobjective optimization this centroid is a vector, which is then transformed to a scalar (i.e., the distance to the Pareto front approximation). Moreover, in [11] vectors of single-criterion expected improvement are ranked using multiobjective ranking schemes. For an comparative overview of multiobjective expected improvement measures, see [22]. 

Recently, the hypervolume indicator has been considered in different ways for generalization of the expected improvement criterion ([6], [7], [19],[20]. The hypervolume indicator [23] measures the closeness of an approximation to the Pareto front. It is used for performance assessment and selection criterion in multiobjective optimization (e.g. [3], [7], [9], [14], [24]). The hypervolume indicator does not require a-priori knowledge on the Pareto front. A set that maximizes the hypervolume indicator is a subset of the efficient set and the corresponding objective vectors cover the Pareto front. 

This paper considers the expected gain in hypervolume as a generalization of the expected improvement to the multiobjective domain. This hypervolume-based improvement has already served successfully as a preselection criterion in evolutionary algorithms [7]. For an application in quantum control, see [21]. While in [7] and [21] Monte Carlo integration was used to compute it, the exact computation of the hypervolumebased expected improvement has been announced by the authors in MCDM 2007 [16]. However, the precise details and derivation of the algorithm remained unpublished so far. 

This paper will discuss in more depth the computation procedure for the expected improvement in hypervolume. More importantly, it will contribute new theorems on fundamental properties of the expected improvement in hypervolume, in particular monotonicity properties related to the variance of the predictive distribution and a lemma on its bounds. 

In [22] the following monotonicity properties were studied: (N1) Given two predictive distributions with different means and equal variance. Then the dominance of 

the first mean value vector to the second mean value vector implies that the EI of the first point is bigger than the EI of the second point. 

- (N2) Given two predictive distributions with the same mean and different variances. Then if the first variance vector is greater in its components than the second variance vector, then the EI of the first point is bigger than the EI of the second point [22]. 

While N1 was proven to be correct, N2 could only be supported by empirical evidence. This paper will replace empirical results by analytical proofs. Property N2 is important, as it shows that the expected improvement rewards exploration in less known regions. 

Finally, this papers provides a first result on the behavior of the hypervolume-based expected improvement in the multiobjective generalization of Bayesian (or ’efficient’) global optimization [12],[18]. A first numerical experiment is reported, illustrating its behavior on a simple bi-criterion problem for approximating a Pareto front with a limited budget of 25 evaluations of the objective functions. 

The paper is structured as follows: Preliminaries for the analysis of the hypervolume-based EI are discussed in Section II. Then we discuss its properties in Section III. A detailed derivation of the computation of the hypervolume-based EI follows in Section IV. A straightforward example algorithm using the hypervolume-based EI is studied in Section V. A final discussion and questions for future research are found in Section VI. 

Let us consider predictions, e.g. from a regression model, for some **x** _∈X_ in the form of an independent _m_ -D normal distribution PDF **x** with mean **y** ˆ and a standard deviation ˆ **s** . 

**DEF 3** (Expected improvement) **.** _The expected improvement at a point_ **x** _with respect to the approximation set A, denoted by EIH_ ( **x** _, A_ ) _, is defined as follows._ 



_where the integration region R is_ R<sup>_m_</sup> _._ 

In the following we will also denote the probability density functions of predictive distributions by specifying its mean and deviation (i.e., PDF **m** _,_ **s** instead of PDF **x** ). 

## III. MONOTONICITY PROPERTIES 

**DEF 4** (Property N2) **.** _Let A ∈Am. If for two points_ **x**<sup>+</sup> _and_ **x** _in the search space the predicted value_ **y** ˆ _is the same, and for the standard deviations_ **s**<sup>+</sup> _and_ **s** _it holds that_ **s**<sup>+</sup> _>_ **s** _, then EIH_ ( **x**<sup>+</sup> _, A_ ) _> EIH_ ( **x** _, A_ ) _._ 

In order to proof property N2 for the multiobjective case we need to state a simple lemma: 

**LEMMA 1.** _Given standard deviations s and s_<sup>_′_</sup> _and an arbitrary constant a, it holds: If_ 



_, then_ 

## II. PRELIMINARIES 

This paper considers (multi-criterion) optimization problems _f_ 1( **x** ) _→_ min _, . . . , fm_ ( **x** ) _→_ min _,_ **x** _∈X_ , where _X ⊆_ R<sup>_n_</sup> , and the _fi_ are real-valued. Foremost we consider the cases _m_ = 1 and _m_ = 2. 

**DEF 1** (Approximation set) **.** _By ≺ we denote Paretodominance. Let Am be defined as the set of all finite sets A ⊂_ R<sup>_m_</sup> _with ∀_ **a** _∈ A_ : ∄ **a**<sup>_′_</sup> _∈ A_ : **a**<sup>_′_</sup> _≺_ **a** _. The elements of Am are called_ approximation sets _._ 

The hypervolume indicator _H_ (or: hypervolume) of an approximation set A is defined as the volume of the dominated subspace, bounded by a reference point **r** (a point which is dominated by each element of A): 





**DEF 2** (Hypervolume-based Improvement function) **.** _The hypervolume-based improvement function I_ : R<sup>_m_</sup> _× Am →_ R _is defined as_ 





This definition generalizes the single-objective definition of improvement[12]. 



_where I_ ( _y, {a}_ ) = max _{_ 0 _, a − y}._ 

_Proof:_ The statement easily follows from the nature of the piecewise linear improvement function and normal distribution functions (see Figure 3). 

**DEF 5** (Reference point) **.** _Let A ∈Am. A point_ **r** _∈_ R<sup>_m_</sup> _is called a_ reference point _for the set A, if each element of A dominates_ **r** _._ 

**DEF 6** (staircase and augmented staircase) **.** _Let A ∈A_ 2 _._ 

- 1) _We write the set A as a sequence by sorting it on the first coordinates and call this sequence the_ staircase _associated to A: Astaircase_ = (( _a_ 1 _, b_ 1) _, ...,_ ( _ak, bk_ )) 

- 2) _We call a pair of two adjacent points in Astaircase a_ step _._ 

- 3) _Let_ **r** = ( _r_ 1 _, r_ 2) _be a point in_ R<sup>2</sup> _which is dominated by each point of A. The_ augmented staircase _with respect to_ **r** _, denoted by A_<sup>**r**</sup> _staircase_<sup>_,isthesequence,_</sup> (( _a_<sup>_′_</sup> 1<sup>_, b′_</sup> 1<sup>)=(</sup><sup>_−∞, r_2)</sup><sup>_,_(</sup><sup>_a′_</sup> 2<sup>_, b′_</sup> 2<sup>)=(</sup><sup>_a_1</sup><sup>_, b_1)</sup><sup>_,_(</sup><sup>_a′_</sup> 3<sup>_, b′_</sup> 3<sup>)=</sup> ( _a_ 2 _, b_ 2) _, . . . ,_ ( _a_<sup>_′_</sup> _k_ +1<sup>_, b_</sup> _k_<sup>_′_</sup> +1<sup>)=(</sup><sup>_ak, bk_)</sup><sup>_,_(</sup><sup>_a′_</sup> _k_ +2<sup>_, b_</sup> _k_<sup>_′_</sup> +2<sup>)=</sup> ( _r_ 1 _, −∞_ )) _where_ ( _ai, bi_ ) _are defined as above._ 

- 4) _The_ i-th horizontal strip _with respect to a step is the region bounded by horizontal halflines Li going through the point_ ( _ai, bi_ ) _and ending in this point, similarly for_ 



Fig. 1. Improvement contribution for the step _Si_ , middle case. 

_Li_ +1 _and by the vertical line segment determined by the endpoints_ ( _ai_ +1 _, bi_ ) _and_ ( _ai_ +1 _, bi_ +1) _._ 

**DEF 7** (Improvement Contribution) **.** _Let Si denote the i- th step,_ (( _ai, bi_ ) _,_ ( _ai_ +1 _, bi_ +1)) _, of an augmented staircase A_<sup>**r**</sup> _staircase_<sup>_andlet_</sup><sup>**y**=(</sup><sup>_y_1</sup><sup>_, y_2)</sup><sup>_∈_R2</sup><sup>_.TheImprovement_</sup> _Contribution (IC) is defined as follows._ 



The notion of improvement contribution is illustrated in Figure 1 for the middle case (i.e., _y_ 1 _≤ ai_ +1 and + _bi_ +1 _≤ y_ 2 _≤ bi_ ). The shaded area is the improvement contribution for the example point ( _y_ 1 _, y_ 2). Likewise, Figure 2 illustrates the improvement contribution for the last case in the definition. 

**LEMMA 2.** _Let A ∈A_ 2 _and_ **r** = ( _r_ 1 _, r_ 2) _∈_ R<sup>2</sup> _be a reference point for A and A_<sup>**r**</sup> _staircase_<sup>_the associated, augmented staircase_</sup> _of A with respect to_ **r** _and A and let_ **y** = ( _y_ 1 _, y_ 2) _∈_ R<sup>2</sup> _. Then I_ ( **y** _, A_ ) =<sup>�</sup><sup>_k_</sup> _i_ =1<sup>+1</sup><sup>_IC_(</sup><sup>**y**</sup><sup>_, Si_)</sup><sup>_,wherekisthenumberofpoints in_</sup> _A._ 

_Proof:_ : The Lemma follows directly from the definition of IC. See also Figures 1 and 2. 

**THM 1.** _The hypervolume based EIH satisfies N2 for m_ = 1 _or m_ = 2 _._ 

_Proof:_ The 1-D case is the statement of Lemma 1). 

For the 2D case we proceed as follows. Let A _∈A_ 2 with _k_ points and **r** = ( _r_ 1 _, r_ 2) _∈_ R<sup>2</sup> be a reference point for A and A<sup>**r**</sup> staircase<sup>theaugmentedstaircaseofA.Let</sup><sup>_Si_denote</sup> the steps of A<sup>**r**</sup> staircase<sup>asinDefinition7.</sup> 

ˆ ˆ Let **y** = ( ˆ _y_ 1 _, y_ 2) be the prediction (at some **x** _∈X_ ) and **s** = ( _s_ 1 _, s_ 2) its standard deviation. Without loss of generality ˆ we assume **y** = **0** . The expected improvement is equal to: 





Fig. 2. Improvement contribution of _Si_ , last case. 

, where _R_ = R<sup>2</sup> . Due Lemma 2 this integral can be rewritten as: 



We will decompose the integration region _R_ in the integral in Expression 5 into horizontal strips _Hi_ (see Definition 6). We will show that in case the vertical variance stays the same and the variance of the horizontal coordinate is incremented, then the integration contribution by each strip is bigger for bigger horizontal variance. The integral for strip _Hi_ reads as follows: 



By inspecting Expression 6 for each summand with different variances in the horizontal direction (i.e., _s_<sup>+</sup> 1<sup>and</sup><sup>_s_1with</sup><sup>_s_+</sup> 1<sup>_>_</sup> _s_ 1) and keeping the variances the same in the vertical direction, we see by Lemma 1 that each of the summands for _s_<sup>+</sup> 1<sup>is</sup> greater or equal than the corresponding summand for _s_ 1 (the left side of the products are the same while the right side obeys the Lemma 1). Clearly one of the summands in case of _s_<sup>+</sup> 1<sup>willbestrictlybiggerthanthecorrespondingsummandin</sup> case of _s_ 1. Since the statement holds for each horizontal strip, we see also that the total integral (which is the sum over all integrals on horizontal strips) is strictly bigger in case of _s_<sup>+</sup> 1<sup>.</sup> 

We have shown that by increasing the variance in the horizontal ( _y_ 1) direction, the EI _H_ is strictly bigger in case the variance is kept the same in the vertical ( _y_ 2) direction. By symmetry it also holds that by increasing the variance in the vertical ( _y_ 2) direction, the EI _H_ is strictly bigger in case the variance is kept the same in the horizontal ( _y_ 1) direction. Hence, increasing the variance in both directions will lead to a strictly bigger EI _H_ – because we can do this in two steps, first increasing the variance in the horizontal direction and holding the vertical variance the same and subsequently increasing the vertical variance while holding the horizontal variance the same on the increased level (i.e., ( _s_ 1 _, s_ 2) _→_ ( _s_<sup>+</sup> 1<sup>_, s_2)</sup><sup>_→_(</sup><sup>_s_+</sup> 1<sup>_, s_+</sup> 2<sup>)).Bothstepswillincreasethe</sup> EI _H_ . 

The following lemma summarizes properties of the minima and maxima of the expected improvement: 

**LEMMA 3.** Minima and maxima of the expected improvement: _Given a mean value_ **y** ˆ _∈_ R<sup>_m_</sup> _, a standard deviation_ ˆ _A_ **s** _∈A∈_ R _m_<sup>_m_</sup> _≥,_ 0 **y** ˆ<sup>_,_</sup> _≤_<sup>_a_</sup> **r**<sup>_reference_</sup> _and A ⪯_<sup>_point_</sup> **r** _, then_<sup>**r**</sup> _for_<sup>_and_</sup> _the_<sup>_an_</sup> _value_<sup>_approximation_</sup> _EIH_ (ˆ **y** _,_ ˆ **s** _,_ **r** _, A_<sup>_set_</sup> ) _of the expected improvement it holds that_ 

- (a) _EIH_ (ˆ **y** _,_ ˆ **s** _,_ **r** _, A_ ) _≥_ 0 

- (a’) _if_ ˆ **s** _>_ **0** _then the stricter condition EIH_ (ˆ **y** _,_ ˆ **s** _,_ **r** _, A_ ) _>_ 0 _holds._ 

- (b) _EIH_ (ˆ **y** _,_ ˆ **s** _,_ **r** _, A_ ) _≤ EIH_ (ˆ **y** _,_ ˆ **s** _,_ **r** _, {_ **r** _}_ ) _< ∞_ 

_Proof:_ The first implication follows from I(ˆ **y** _,_ ˆ **s** _,_ **r** _,_ A) _≥_ 0 in Definition 2. Likewise, because of the infinite support of the Gaussian PDF, the stricter condition ( _a_<sup>_′_</sup> ) holds in case of strictly positive standard deviations. Part ( _b_ ) follows from the fact that for all points **y** that dominate the reference point the improvement I(ˆ **y** _,_ ˆ **s** _,_ **r** _,_ A) is upper bounded by I(ˆ **y** _,_ ˆ **s** _,_ **r** _, {_ **r** _}_ ). For all other points it is zero in both cases. 

The practical implication of this lemma is that as long as the variances are positive the expected improvement can serve as a criterion guiding the search, also for mean value vectors that are dominated. This distinguishes it for instance from the most likely improvement (MLI) in hypervolume, as defined in [7], which obtains zero values when the mean values are dominated. Moreover (b) implies that the expected improvement can always be computed as a finite value (no singularities occur). 



Fig. 3. Construction used in the proof of the stated inequality. 

## IV. COMPUTATION 

Let _A_ = _{_ **y**<sup>(1)</sup> _, · · · ,_ **y**<sup>(</sup><sup>_k_)</sup> _} ∈Am_ . The integration region R<sup>_m_</sup> can be partitioned into a set of interval boxes, and then piecewise integration can solve the problem of computing the integral directly. To provide an intuition on the grid-variables and areas introduced in the following, Figure 4may serve the reader. 

Let _b_<sup>(1)</sup> _i_<sup>,</sup><sup>_b_(2)</sup> _i_<sup>,</sup><sup>_. . ._,</sup><sup>_b_(</sup> _i_<sup>_k_)</sup> denote the sorted list of all the _i_ -th coordinates of the vectors **y**<sup>(1)</sup> _∈_ R<sup>_m_</sup> _, . . . ,_ **y**<sup>(</sup><sup>_k_)</sup> _∈_ R<sup>_m_</sup> . For technical reasons we define _b_<sup>(0)</sup> _i_ = _−∞_ and _b_<sup>(</sup> _i_<sup>_k_+1)</sup> = _ri_ , _b_<sup>(</sup> _i_<sup>_k_+2)</sup> = _∞_ . 

The grid-coordinates _b_<sup>(</sup> _j_<sup>_i_)</sup> give rise to a partitioning into grid cells. We can enumerate these grid cells as follows. For each ( _i_ 1 _, . . . , im_ ), where _is ∈{_ 0 _, . . . , k_ + 1 _}_ , the grid cell named _C_ ( _i_ 1 _, . . . , im_ ) is determined by ( _b_<sup>(</sup> 1<sup>_i_1)</sup> _, . . . , b_<sup>(</sup> _m_<sup>_im_)</sup> )<sup>_T_</sup> and ( _b_<sup>(</sup> 1<sup>_i_1+1)</sup> _, . . . , bm_<sup>(</sup><sup>_im_+1)</sup> )<sup>_T_</sup> as the half open (from below) interval box (i.e., ( _b_<sup>(</sup> 1<sup>_i_1)</sup> _, b_<sup>(</sup> 1<sup>_i_1+1)</sup> ] _×_ ( _b_<sup>(</sup> 2<sup>_i_2)</sup> _, b_<sup>(</sup> 2<sup>_i_2+1)</sup> ] _× · · · ×_ ( _b_<sup>(</sup> _m_<sup>_im_)</sup> _, bm_<sup>(</sup><sup>_im_+1)</sup> ]). We call ( _b_<sup>(</sup> 1<sup>_i_1)</sup> _, . . . , bm_<sup>(</sup><sup>_im_)</sup> )<sup>_T_</sup> the lower corner of _C_ ( _i_ 1 _, . . . , im_ ) denoted by **l** ( _i_ 1 _, . . . , im_ ), likewise we call ( _b_<sup>(</sup> 1<sup>_i_1+1)</sup> _, . . . , bm_<sup>(</sup><sup>_im_+1)</sup> )<sup>_T_</sup> the upper corner of of _C_ ( _i_ 1 _, . . . , im_ ) denoted by **u** ( _i_ 1 _, . . . , im_ ). With this notation we will also denote _C_ ( _i_ 1 _, . . . , im_ ) by ( **l** ( _i_ 1 _, . . . , im_ ) _,_ **u** ( _i_ 1 _, . . . , im_ )]. See Figure 4 for an example. 

It can be directly observed that there are many cells the integration over which adds a contribution of zero to the integral. These are cells that 

- 1) have lower corners **l** ( _i_ 1 _, . . . , im_ ) that are dominated or equal to points in A, i.e. A _⪯_ **l** ( _i_ 1 _, . . . , im_ ), or 

- 2) have upper corners **u** ( _i_ 1 _, . . . , im_ ) that do not dominate the reference point, i.e. **u** ( _i_ 1 _, . . . , im_ ) ⊀ **r** . 

The second criterion is fulfilled by grid cells _C_ ( _i_ 1 _, . . . , im_ ) with _i_ 1 = _k_ + 1 or _i_ 2 = _k_ + 1 _. . ._ or _im_ = _k_ + 1, i.e. at least one of their coordinates has index _k_ + 1. 

All cells that fulfill criterion (1) or (2) will be called inactive cells, while the other cells will be termed active cells. _Active_ 



Fig. 4. Schematic drawing of a population, its hypervolume, and grid in the bi-objective case. The black points are the points of the population, except the point in the upper right corner that marks the position of the reference point for the hypervolume. The yellow region defines the measured hypervolume _S_ . The grid coordinates are indicated by _b_<sup>(</sup> 1<sup>_i_)</sup> and _b_<sup>(</sup> 2<sup>_i_)</sup> for the first and second coordinate, respectively. Grid-cell _C_ (1 _,_ 1) is highlighted by a thick black boundary. 



Fig. 5. Schematic drawing of the integration area and grid in the bi-objective case.( _S_<sup>_−_</sup> = _{_ **z** _∈_ R<sup>_m_</sup> _|_ A( **u** ) _⪯_ **z** _⪯_ **v** _}_ , where A( **u** ) = _{_ **p** _∈_ A _|_ **u** _≺_ **p** _}_ ) 

_cells are cells the inner points of which are dominating the reference point and are not dominated by any point in A_ . 

Obviously, the expected improvement integral is the sum of all contributions of integration of the improvement integral over the set of active cells _C_<sup>+</sup> , i.e. 



. Note, that it is important to choose the half-open interval boxes here, as the lower corners can reach out to _−∞_ and we have to avoid overlapping of boundaries, which might cause 

double integration of non-zero contributions in case of zero standard deviations. Moreover, because of the possibility of zero standard deviations, Lebesgue integration is assumed. 

Let us now discuss, how the contribution _δ_ ( _i_ 1 _, . . . , im_ ) can be computed. We first describe the relevant expressions which are followed by detailed derivation later on. Readers only interested in the implementation of the integral can omit the latter part. 

The approach is discussed in a top-down way, we will provide a general expression for computing _δ_ ( _i_ 1 _, . . . , im_ ) and then its components are defined. 

The contribution _δ_ ( _i_ 1 _, . . . , im_ ) of an active grid cell can be computed via 



with 





and _j_ = 1 _, . . . , m_ . (Ψ is defined in Equation 11. For _S_<sup>_−_</sup> see Figure 5. ) 

To each **l** and A (and reference point) we can associate a vector **v** as follows. Let A( **l** ) be equal to the set _{_ **z** _∈_ A _|_ **l** _≺_ **z** _}_ and let for each _i,_ 1 _≤ i ≤ m_ , _pi_ denote the usual projection from R<sup>_m_</sup> onto the i-th factor R (i.e., _pi_ (( _r_ 1 _, · · · , ri, · · · rm_ )) = _ri_ ). Then, if A( **l** ) = _∅_ , _vi_ = max( _pi_ (A( **l** ))). Alternatively we can define the vector **v** ( _i_ 1 _, . . . , im_ ) _∈_ R<sup>_m_</sup> as follows. The _j_ - th coordinate of **v** ( _i_ 1 _, . . . , im_ ) is the _j_ -th coordinate of the intersection point, called **h**<sup>(</sup><sup>_j_)</sup> , of the attainment surface of A and the ray _{_ **y** _∈_ R<sup>_m_</sup> _|∃t ≥_ 0 : **y** = **l** ( _i_ 1 _, . . . , im_ ) + _t_ **e**<sup>(</sup><sup>_j_)</sup> _}_ (where _j ∈{_ 1 _, . . . , m}_ ). 

We can construct the _j_ -th coordinate of **v** as follows by finding the first vector in the sequence **l** ( _i_ 1 _, . . . , ij, . . . im_ ) _,_ **l** ( _i_ 1 _, . . . , ij_ + 1 _, . . . im_ ) _,_ **l** ( _i_ 1 _, . . . , ij_ + 2 _, . . . im_ ) etc. which does not strictly dominate some point of A. The _j_ -th coordinate of this point is announced as the _j_ -th coordinate of **v** (cf. Fig 5). 

The computation of this boundary coordinate can be done by looping only at the discrete steps given by the grid nodes in direction of the unit vector **e**<sup>(</sup><sup>_j_)</sup> . In case _m_ = 2 the monotonicity of the staircase structure of the polyline describing the attainment curve can be exploited to determine this value efficiently . 

The integration of the marginal normal distributions is captured in the expression: 



. In this expression _φ_ denotes the probability density function of the standard normal distribution, and Φ denotes the cumulative probability density function of the normal distribution, 

i.e.: 



Finally, Vol( _S_<sup>_−_</sup> ) is a correction term. It denotes the hypervolume measure for the subset of points in A dominated or equal to **u** ( _i_ 1 _, . . . , im_ ) and as reference point **v** ( _i_ 1 _, . . . , im_ ) (see also Figure 5). This can be computed by means of a standard procedure for hypervolume computation. For the 2-D case differences of the cumulated contributions to the hypervolume, when integrating it along _f_ 1 along the staircase, can be exploited for its efficient computation. 

The direct computation of the expected improvement contribution _δ_ ( _i_ 1 _, . . . , im_ ) can best be motivated by means of decomposing the general integral expression. For the sake of clarity, we assume that the grid indices are _i_ 1 _, . . . , im_ and omit them as parameters, i.e. we set **l** = **l** ( _i_ 1 _, . . . , im_ ) _,_ **u** = **u** ( _i_ 1 _, . . . , im_ ) _, C_ = _C_ ( _i_ 1 _, . . . , im_ ), and so forth. 

The improvement I( **y** ) in the grid cell _C_ always can be decomposed into the contribution of _L_<sup>+</sup> that is the hypervolume measure of the non-dominated part in [ **u** _,_ **v** ] and a ’boundary’ contribution _V_ that depends on the integration variable **y** and forms a boundary layer around [ **u** _,_ **v** ]. The set _V_ is determined by the set difference 







. An important observation is that only the first term, namely [ **y** _,_ **v** ] depends on **y** . 

After these preliminaries, let us recall the expected improvement integral (expression 2). The contribution _δ_ of cell _C_ is given by: 



, where **l** ( _i_ 1 _, . . . im_ ) = ( _l_ 1 _, . . . , lm_ ) and **l** ( _i_ 1 _, . . . im_ ) = ( _u_ 1 _, . . . , um_ ). In order to compute _δ_ explicitly by reducing, among others, to an S-metric computation of _S_<sup>_−_</sup> (i.e., _−_ Vol( _S_<sup>_−_</sup> ), we define three quantities _Q_ 1 _, Q_ 2 _,_ and _Q_ 3 as follows. 







The expression _−Q_ 2 + _Q_ 3 is equal to: 



Moreover the expression Vol( _L_<sup>+</sup> ) _−_<sup>�</sup><sup>_m_</sup> _i_ =1<sup>(</sup><sup>_vi−ui_) is the nega-</sup> tive hypervolume measure for the set of points in A dominated or equal to **u** with reference point **v** (i.e., Vol( _L_<sup>+</sup> ) _−_<sup>�</sup><sup>_m_</sup> _i_ =1<sup>(</sup><sup>_vi−_</sup> _ui_ ) = _−_ Vol( _S_<sup>_−_</sup> ), where _S_<sup>_−_</sup> = _{_ **z** _∈_ R<sup>_m_</sup> _|_ A( **u** ) _⪯_ **z** _⪯_ **u** _}_ with A( **u** ) = _{_ **p** _∈_ A _|_ **u** _≺_ **p** _}_ , see also Figure 5). In addition, the integral 



is, in case of independent normal distributions, equal to the term 



. 

An expression for _Q_ 1 is more difficult to derive, due to the nonlinearity. First of all we decompose the integral into the product of one-dimensional integrals: 



. The last step is motivated by the following equality and the definition in Equation 11 : 



. The computation of Ψ reduces to the integration of a one-dimensional integration the details of which _b_ are as follows: Compute � _−∞_<sup>(</sup><sup>_a_</sup> _− y_ ) pdf( _y_ ) _dy_ , where pdf( _y_ ) = _σ_<sup>_~~√~~_</sup> <u>2</u> _<u>π</u>_<sup>exp(</sup><sup>_−_</sup> 2<sup><u>1</u>(</sup><sup>_<u>y−</u>_</sup> _σ_<sup>_<u>µ</u>_)2).</sup> Answer: � _−∞b_<sup>(</sup><sup>_a−y_)</sup> _σ_<sup>_~~√~~_</sup> <u>2</u> _<u>π</u>_<sup>e</sup><sup>_−_</sup> 2<sup><u>1</u>(</sup><sup>_<u>y−</u>_</sup> _σ_<sup>_<u>µ</u>_</sup> )<sup>2</sup> _dy_ = _σ_<sup>_~~√~~_</sup> <u>2</u> _<u>π</u>_<sup>e</sup><sup>_−_</sup> 2<sup><u>1</u>(</sup><sup>_<u>y−</u>_</sup> _σ_<sup>_<u>µ</u>_</sup> )<sup>2</sup> + _√_ 2( _a − µ_ ) erf( _~~<u>√</u>~~_ 2 _σ_ <u>2</u><sup>(</sup><sup>_b−µ_))+</sup> _√_ 2( _a − µ_ ). Simplified: _σφ_ (<sup>_b−_</sup> _σ_<sup>_<u>µ</u>_)+(</sup><sup>_a−µ_)Φ(</sup><sup>_b−_</sup> _σ_<sup>_<u>µ</u>_)with</sup><sup>_φ_(</sup><sup>_y_)=</sup> _~~√~~_ <u>12</u> _π_<sup>e</sup><sup>_−_</sup> 2<sup><u>1</u></sup><sup>_y_2</sup> being the probability density function of the standard normal distribution and Φ( _y_ ) =<sup><u>1</u></sup> 2<sup>(1 + erf(</sup> _~~√~~_<sup>_<u>y</u>_</sup> 2<sup>))beingthecumulative</sup> density function of the standard normal distribution. 

All components used in the computation of _δ_ have been derived and we have summarized the computation procedure. The computation is relatively simple to implement. It needs no numerical integration (except, of course, for the computation 

of the function _erf_ ). Implementations of the _erf_ function can be found, however, in most programming languages and statistical packages. 

A useful remark is to note that in case of two objectives (i.e., _m_ = 2), the Improvement function _I_ ( **y** _,_ A) can be computed in _O_ ( _k_ ), where _k_ is the size of set A (A _∈A_ 2) without the need to compute hypervolume(s). Of course, provided A is sorted on its first or second coordinate. The function _I_ can be computed by applying the elementary increment function IC to the _k_ + 1 neighbor pairs of A<sup>**r**</sup> _staircase_<sup>and</sup> take the sum of these _k_ + 1 results. Moreover the piecewise definition of _I_ caused by the piecewise nature of IC can also be computed in symbolic mathematics software such as Maple or Mathematica giving way to a very short specification of the computation of EI _H_ – the source code for this is available on natcomp.liacs.nl. 

## V. GLOBAL OPTIMIZATION ALGORITHM 

Consider a function EI (such as EI _H_ ) that for each input vector _x_ computes a quantity that determines how promising this point is for improving a Pareto front approximation. It can use the information of all previously evaluated points. The expected improvement algorithm is similar to Bayesian Optimization [18] and Efficient (or Statistical) Global Optimization [4], [12], with the difference, that the hypervolumebased expected improvement EI _H_ replaces the single-objective expected improvement. 

**Algorithm 1** Generic algorithm for EI _H_ -based global (multiobjective) optimization 

Generate initial set of _k_ points X _k_ = ( **x**<sup>(1)</sup> _, ...,_ **x**<sup>(</sup><sup>_k_)</sup> ) (e.g. uniform randomly in the search space _X_ ) Evaluate initial points Y _k_ = ( **y**<sup>(1)</sup> = **f** ( **x**<sup>(1)</sup> ) _, . . . ,_ **y**<sup>(</sup><sup>_k_)</sup> = **f** ( **x**<sup>(</sup><sup>_k_)</sup> )) Set X<sup>_nd_</sup> _k_<sup>_,_Y</sup><sup>_nd_</sup> _k_ to the subsequence of non-dominated solutions among X _k,_ Y _k_ . _t ← k_ **while** _t < tmax_ **do** Update the Gaussian model based on X _t,_ Y _t, t ← t_ + 1 choose **x**<sup>(</sup><sup>_t_)</sup> _∈_ arg min **x** _∈X_ EI _H_ ( **x** _,_ Y<sup>_nd_</sup> _t_<sup>)</sup> **y**<sup>(</sup><sup>_t_)</sup> = **f** ( **x**<sup>(</sup><sup>_t_)</sup> ) X _t_ = X _t−_ 1 _◦_ **x**<sup>(</sup><sup>_t_)</sup> ; Y _t_ = Y _t−_ 1 _◦_ **y**<sup>(</sup><sup>_t_)</sup> Set X<sup>_nd_</sup> _t_<sup>_,_Y</sup><sup>_nd_</sup> _t_ to the sequence of non-dominated solutions among X _t,_ Y _t_ . **end while return** X<sup>_nd_</sup> _t_<sup>_,_Y</sup><sup>_nd_</sup> _t_ 

A single numerical experiment will serve here as a proof of concept and shall encourage future studies in using the hypervolume-based expected improvement. Note, that the expected improvement in hypervolume has already been used in pre-selection schemes of metamodel-assisted evolutionary algorithms in previous work [6], [21]. In contrast, the following study will be on the Bayesian global optimization scheme (Algorithm 1). 



Fig. 6. Expected improvement algorithm on 2-D generalized sphere problem. 

## _A. Numerical Experiment_ 

_a) Research Question:_ It will be studied on a simple multiobjective optimization landscape, if and how fast the hypervolume-based expected improvent algorithm converges to a known Pareto front. The problem is the 2-D generalized sphere problem: minimize _f_ 1( **x** ) = _||_ **x** _−_ **1** _||,_ minimize _f_ 2( **x** ) = _||_ **x** + **1** _||,_ **x** _∈_ [ _−_ 2 _,_ 2] _×_ [ _−_ 2 _,_ 2] _⊂_ R<sup>2</sup> . For an analysis of the generalized sphere problem, see [7], p.182. The Pareto front is the line segment from (0 _,_ 2 _· √_ 2) to (2 _· √_ 2 _,_ 0), the efficient set is the line segment that connects ( _−_ 1 _, −_ 1) and (1 _,_ 1). 

_b) Experimental setup:_ The metamodel used is a Gaussian random field model with Gaussian kernel exp _−θ||_ **x** _−_ **x**<sup>_′_</sup> _||_<sup>2</sup> . The correlation parameter was estimated from the intial sample to _θ_ = 0 _._ 0001 and was set to this constant during the run. The size of the initial population was set to 10 and 15 new points were generated using the Algorithm 1. In total the test function to be optimized was evaluated 25 times. 

_c) Result:_ The results of the experiment is depicted in Figure 6. In all pictures, points that have been evaluated are indicated by stars. The points from the initial set are additionally marked by blue squares. Efficient points are surrounded by circles. Darker gray-levels represent lower values. The top row depicts the mean value of the Gaussian random field model at **x** _∈_ [ _−_ **2** _,_ **2** ] _×_ [ _−_ **2** _,_ **2** ] for _f_ 1 and _f_ 2, resp. Likewise, the middle row depicts the variance of the Gaussian random field model at **x** _∈_ [ _−_ **2** _,_ **2** ] _×_ [ _−_ **2** _,_ **2** ] for _f_ 1 and _f_ 2, resp. In the bottom row on the left hand side all evaluated points are displayed in the objective space. On the right hand side of the same row the hypervolume-based expected improvement values after the 25th iteration are displayed. For each coordinate pair ( _x_ 1 _, x_ 2) the gray value indicates the expected improvement of **x** . 

Initially 10 points (blue squares in the plot) are evaluated. Within the first 4 loops the algorithm places an evaluation in each of the four corners of the search space. Then it proceeds with choosing points close to the Pareto front with points. 

Each of the points chosen is non-dominated to the previous points and fills a gap in the approximation. After 15 iterations of the main loop the algorithm was terminated (by the user). The total time of the experiment was in the order of a couple of minutes on a modest Pentium 6 processor. 

In summary, using only _25 evaluations of the original objective functions_ , including already the initial 10 evaluations, the algorithm discovers a fairly close approximation to the Pareto front. 

## VI. CONCLUSION 

This paper discusses an expected improvement criterion based on the hypervolume indicator (EI _H_ ) that can be used in multiobjective optimization with costly function evaluations. 

It is shown that, given a Gaussian random field and an approximation of the efficient set, the EI _H_ can be computed by means of an exact algorithm. This paper derives the steps of this algorithm. 

We have proven the monotonicity property _N_ 2, introduced in [22], analytically for two dimensions. This property states, that points with the same mean are ’rewarded’ by a higher variance, no matter where the location of the mean value vector is. This property conforms with the one dimensional case and it shows that explorative behavior of the algorithms is rewarded, when selecting by means of the EI _H_ . 

A first numerical study on a generalized sphere model provides a proof of concept that Bayesian Optimization Algorithms (or: Efficient Global Optimization) can be generalized by means of the EI _H_ to multi-objective problems. In the example this Hypervolume-Based Bayesian Optimization algorithm obtained a fairly close approximation to the Pareto front in only 25 iterations. 

Future work is needed to study the scalability and robustness of the Bayesian optimization algorithm. Moreover, it needs to be verified whether the theorem on property _N_ 2 holds also for more than two dimensions. 

The MATLAB implementation of the expected improvement is made available under natcomp.liacs.nl. 

## ACKNOWLEDGMENT 

The authors would like to thank Johannes Kruisselbrink for the Kriging implementation in MATLAB. M. Emmerich acknowledges financial support by the DELIVER Project cofinanced by STW/NWO. The authors acknowledge Tobias Wagner for his comments on the manuscript. 

## REFERENCES 

- [1] Bartz-Beielstein, T.; Lasarczyk, C. and Preuss, M. (2005), Sequential Parameter Optimization, in B. McKay et al., ed., ’Proc. of CEC’, IEEE, , pp. 773–780. 

   - [5] M.A El-Beltagy and P.B. Nair and A.J. Keane, Metamodelling Techniques for Evolutionary Optimisation of Computationally Expensive Problems: Promises and Limitations, Proc. of GECCO, Int’l Conf. on Genetic and Evolutionary Computation, Orlando 1999, pages 196-203,Morgan Kaufman, 1999 

   - [6] Emmerich, M.; Giannakoglou, K. and Naujoks, B. (2006), ’Single- and multi-objective evolutionary optimization assisted by Gaussian random field metamodels’, IEEE Trans. Evol. Comput. 10(4), 421–439. 

   - [7] Emmerich,M., Single- and Multiobjective Evolutionary Design Optimization Using Gaussian Random Field Metamodels, PhD Thesis, FB Informatik, TU Dortmund, 2005 

   - [8] Emmerich, M. and Naujoks, B. (2004), Metamodel-assisted multiobjective optimisation strategies and their application in airfoil design., in I. Parmee, ed., ’Proc of. Fifth Int’l. Conf. on Adaptive Design and Manufacture (ACDM), Bristol, UK, April 2004, Springer, pp. 249–260. 

   - [9] Igel, C.; Hansen, N. and Roth, S. (2007), ’Covariance Matrix Adaptation for Multi-objective Optimization’, Evol. Comput. 15(1), 1–28. 

   - [10] Jin, Y. (2005), ’A comprehensive survey of fitness approximation in evolutionary computation’, Soft Computing Journal 9(1), 3-12. 

   - [11] Jeong, S. and Obayashi, S. (2005), Efficient global optimization (EGO) for multi-objective problem and data mining, in D. Corne and others, ed., ’Proc. CEC’, IEEE, , pp. 2138–2145. 

   - [12] Jones, D., Schonlau, M., Welch, W., (1998) Efficient Global Optimization of Expensive Black-Box Functions, Journal of Global Optimization, Vol. 13, 455-492. 

   - [13] Jones, D. R.; Schonlau, M. and Welch, W. J. (1998), ’Efficient Global Optimization of Expensive Black-Box Functions’, J. Glob. Optim. 13(4), 455–492. 

   - [14] Knowles, J. D.; Corne, D. W. and Fleischer, M. (2003), Bounded Archiving using the Lebesgue Measure, in ’Proceedings of the IEEE Congress on Evolutionary Computation’, IEEE Press, , pp. 2490–2497. 

   - [15] Keane, A. J. (2006), ’Statistical Improvement Criteria for Use in Multiobjective Design Optimization’, AIAA J. 44(4), 879–891. 

   - [16] J.W. Klinkenberg, M. Emmerich, A. Deutz: Expected Improvement of the S-Metric for finite Pareto front Approximations, Extended Abstract, Proc. of MCDM 2008, Auckland, NZ. 

   - [17] Knowles, J. (2006), ’ParEGO: A hybrid algorithm with on-line landscape approximation for expensive multiobjective optimization problems’, IEEE Trans. Evol. Comput. 10(1), 50–66. 

   - [18] Mockus, J.; Tiesis, V. and Zilinskas, A. (1978), The application of Bayesian methods for seeking the extremum, in L. C. W. Dixon and G. P. Szego, ed., ’Towards Global Optimization’, North-Holland, , pp. 117–129. 

   - [19] Ponweiser, W.; Wagner, T.; Biermann, D. and Vincze, M. (2008), Multiobjective Optimization on a Limited Budget of Evaluations Using Model-Assisted _S_ -Metric Selection, in ’Proc. PPSN X’, Springer-Verlag, Berlin, Heidelberg, pp. 784–794. 

   - [20] Ponweiser, W.; Wagner, T. and Vincze, M. (2008), Clustered Multiple Generalized Expected Improvement: A Novel Infill Sampling Criterion for Surrogate Models, in Z. Michalewicz and others, ed., ’Proc. CEC’, IEEE, , pp. 3514–3521. 

   - [21] Ofer M. Shir, Michael Emmerich, Thomas B¨ack and Marc J.J. Vrakking. The Application of Evolutionary Multi-Criteria Optimization to Dynamic Molecular Alignment. Proceedings of IEEE-CEC 2007, Singapore; IEEE Press. 

   - [22] Wagner, T.; Emmerich, M.; Deutz, A. and Ponweiser, W. (2010), On expected-improvement criteria for model-based multi-objective optimization, in ’Proc. of PPSN XI Vol. 1’, Springer-Verlag, Berlin, Heidelberg, pp. 718–727. 

   - [23] E. Zitzler: Evolutionary Algorithms for Multiobjective Optimization: Methods and Applications, PhD Thesis, University of Zurich, Switzerland 

   - [24] Zitzler, Eckart and K¨unzli, Simon: Indicator-Based Selection in Multiobjective Search, Parallel Problem Solving from Nature - PPSN VIII, Springer Berlin Heidelberg, 2004 

- [2] B¨uche, D.; Schraudolph, N. N. and Koumoutsakos, P. (2005), ’Accelerating Evolutionary Algorithms with Gaussian Process Fitness Function Models’, IEEE Transact. SMC, Special Issue on Knowledge Extraction and Incorporation in Evolutionary Computation (Part C) 35(2), 183-194. 

- [3] Bader, J. and Zitzler, E. (2010), ’HypE: An Algorithm for Fast Hypervolume-Based Many-Objective Optimization’, Evolutionary Computation (in print), 1-32. 

- [4] Cox, D.D. and John S., SGO: a statistical method for global optimization. In V. Hampton, editor, Multidisciplinary design optimization, volume 2, pages 315329. SIAM, Philadelphia, PA, 1997. 




---

## ANEXO — Camada de texto completa do PDF (get_text)

> Reprodução integral da camada de texto do PDF (todas as páginas, ordem de leitura bruta). Inclui tabelas de resultados e equações que a conversão estruturada acima pode ter omitido. Garante completude textual (imagens continuam omitidas).


<!-- página 1 -->

Hypervolume-based Expected Improvement:
Monotonicity Properties and Exact Computation
Michael T.M. Emmerich
Leiden Institute of
Advanced Computer Science
Leiden University
Leiden, The Netherlands
Email: emmerich@liacs.nl
Andr´e H. Deutz
Leiden Institute of
Advanced Computer Science
Leiden University
Leiden, The Netherlands
Email: deutz@liacs.nl
Jan Willem Klinkenberg
Leiden Institute of
Advanced Computer Science
Leiden University
Leiden, The Netherlands
Email: jklinken@liacs.nl
Abstract—The expected improvement (EI) is a well established
criterion in Bayesian global optimization (BGO) and metamodel-
assisted evolutionary computation, both applied in optimization
with costly function evaluations. Recently, it has been adopted
in different ways to multiobjective optimization. A promising
approach to formulate the expected improvement in this context,
is to base it on the hypervolume indicator. Given the Bayesian
model of the optimization landscape, the EI in hypervolume
computes the expected gain in attained hypervolume for a
given input point. Although a formulation of this expected
improvement is relatively straightforward, its computation and
mathematical properties are still to be investigated. This paper
will outline and derive an algorithm for the exact computation
of the proposed hypervolume-based EI. Moreover, this paper
establishes monotonicity properties of the expected improvement.
In particular the effect of the predictive distribution’s variance
on the hypervolume-based EI and elementary properties of the EI
landscape are studied. The monotonicity properties will reveal re-
gions where Pareto front approximations can be improved as well
as underexplored regions that are favored by the hypervolume-
based expected improvement. A ﬁrst numerical example is
included that illustrates the behavior of the hypervolume-based
EI in the multiobjective BGO framework.
I. INTRODUCTION
In global optimization with expensive black-box models it
is common practice to consider a metamodel that is based
on previous function evaluations [10]. This metamodel can be
used to guide the search towards promising or less explored
regions of the search space [5]. Gaussian process (and also
Kriging) models allow to compute, for each input point, the
mean and the variance of a predictive distribution quantifying
the probability of different results of the precise evaluation.
They assume a correlation of space-indexed distributions that
is based on distance in the index space [7].
Different criteria for selecting promising points based on
Gaussian process models have been suggested in the literature
[4], [7]. Among them, expected improvement [18] became
very popular as a measure and part of standard algorithms,
such as efﬁcient global optimization (EGO) [13]. The expected
improvement, as deﬁned in [18] and [13], measures, for a given
predictive distribution of an input point, the expected gain in
closeness to the global optimum.
The generalization of the expected improvement to multiob-
jective optimization is a subject of ongoing research. Different
proposals have been made by [6], [11], [15],[17], [19], and
[20]. In [17] the EGO approach has been generalized to
multiobjective optimization, using Tchebyscheff scalarization
with dynamically changing weights for the objective functions
for computing the expected improvement. In [15] the expected
improvement is interpreted as the centroid of the improvement
distribution. In multiobjective optimization this centroid is a
vector, which is then transformed to a scalar (i.e., the distance
to the Pareto front approximation). Moreover, in [11] vectors
of single-criterion expected improvement are ranked using
multiobjective ranking schemes. For an comparative overview
of multiobjective expected improvement measures, see [22].
Recently, the hypervolume indicator has been considered in
different ways for generalization of the expected improvement
criterion ([6], [7], [19],[20]. The hypervolume indicator [23]
measures the closeness of an approximation to the Pareto front.
It is used for performance assessment and selection criterion in
multiobjective optimization (e.g. [3], [7], [9], [14], [24]). The
hypervolume indicator does not require a-priori knowledge
on the Pareto front. A set that maximizes the hypervolume
indicator is a subset of the efﬁcient set and the corresponding
objective vectors cover the Pareto front.
This paper considers the expected gain in hypervolume as
a generalization of the expected improvement to the multi-
objective domain. This hypervolume-based improvement has
already served successfully as a preselection criterion in evolu-
tionary algorithms [7]. For an application in quantum control,
see [21]. While in [7] and [21] Monte Carlo integration was
used to compute it, the exact computation of the hypervolume-
based expected improvement has been announced by the
authors in MCDM 2007 [16]. However, the precise details
and derivation of the algorithm remained unpublished so far.
This paper will discuss in more depth the computation pro-
cedure for the expected improvement in hypervolume. More
importantly, it will contribute new theorems on fundamental
properties of the expected improvement in hypervolume, in
particular monotonicity properties related to the variance of
the predictive distribution and a lemma on its bounds.
In [22] the following monotonicity properties were studied:
(N1)
Given two predictive distributions with different
means and equal variance. Then the dominance of


<!-- página 2 -->

the ﬁrst mean value vector to the second mean value
vector implies that the EI of the ﬁrst point is bigger
than the EI of the second point.
(N2)
Given two predictive distributions with the same
mean and different variances. Then if the ﬁrst vari-
ance vector is greater in its components than the
second variance vector, then the EI of the ﬁrst point
is bigger than the EI of the second point [22].
While N1 was proven to be correct, N2 could only be sup-
ported by empirical evidence. This paper will replace empirical
results by analytical proofs. Property N2 is important, as it
shows that the expected improvement rewards exploration in
less known regions.
Finally, this papers provides a ﬁrst result on the behavior of
the hypervolume-based expected improvement in the multiob-
jective generalization of Bayesian (or ’efﬁcient’) global opti-
mization [12],[18]. A ﬁrst numerical experiment is reported,
illustrating its behavior on a simple bi-criterion problem for
approximating a Pareto front with a limited budget of 25
evaluations of the objective functions.
The paper is structured as follows: Preliminaries for the
analysis of the hypervolume-based EI are discussed in Section
II. Then we discuss its properties in Section III. A detailed
derivation of the computation of the hypervolume-based EI
follows in Section IV. A straightforward example algorithm
using the hypervolume-based EI is studied in Section V. A
ﬁnal discussion and questions for future research are found in
Section VI.
II. PRELIMINARIES
This paper considers (multi-criterion) optimization prob-
lems f1(x) →min, . . . , fm(x) →min, x ∈X, where
X ⊆Rn, and the fi are real-valued. Foremost we consider
the cases m = 1 and m = 2.
DEF
1
(Approximation set). By ≺we denote Pareto-
dominance. Let Am be deﬁned as the set of all ﬁnite sets
A ⊂Rm with ∀a ∈A : ∄a′ ∈A : a′ ≺a. The elements of Am
are called approximation sets.
The hypervolume indicator H (or: hypervolume) of an
approximation set A is deﬁned as the volume of the dominated
subspace, bounded by a reference point r (a point which is
dominated by each element of A):
H(A) =
Vol({y ∈Rm|y is dominated by some y ∈A and y ≺r})
DEF 2 (Hypervolume-based Improvement function). The
hypervolume-based improvement function I : Rm × Am →R
is deﬁned as
I(y, A) = H(A ∪{y}) −H(A)
(1)
. , where y ∈Rm and A ∈Am.
This deﬁnition generalizes the single-objective deﬁnition of
improvement[12].
Let us consider predictions, e.g. from a regression model,
for some x ∈X in the form of an independent m-D normal
distribution PDFx with mean ˆy and a standard deviation ˆs.
DEF 3 (Expected improvement). The expected improvement
at a point x with respect to the approximation set A, denoted
by EIH(x, A), is deﬁned as follows.
EIH(x, A) =
Z
R
I(x, A) · PDFx(y)dy,
(2)
where the integration region R is Rm.
In the following we will also denote the probability density
functions of predictive distributions by specifying its mean and
deviation (i.e., PDFm,s instead of PDFx).
III. MONOTONICITY PROPERTIES
DEF 4 (Property N2). Let A ∈Am. If for two points x+ and
x in the search space the predicted value ˆy is the same, and
for the standard deviations s+ and s it holds that s+ > s,
then EIH(x+, A) > EIH(x, A).
In order to proof property N2 for the multiobjective case
we need to state a simple lemma:
LEMMA 1. Given standard deviations s and s′ and an
arbitrary constant a, it holds:
If
s > s′
(3)
, then
Z ∞
−∞
I(y, {a})PDF0,s(y)dy >
Z ∞
−∞
I(y, {a})PDF0,s′(y)dy
(4)
where I(y, {a}) = max{0, a −y}.
Proof: The statement easily follows from the nature of the
piecewise linear improvement function and normal distribution
functions (see Figure 3).
DEF 5 (Reference point). Let A ∈Am. A point r ∈Rm is
called a reference point for the set A, if each element of A
dominates r.
DEF 6 (staircase and augmented staircase). Let A ∈A2.
1) We write the set A as a sequence by sorting it on the
ﬁrst coordinates and call this sequence the staircase
associated to A: Astaircase = ((a1, b1), ..., (ak, bk))
2) We call a pair of two adjacent points in Astaircase a
step.
3) Let r = (r1, r2) be a point in R2 which is dominated
by each point of A. The augmented staircase
with
respect to r, denoted by Ar
staircase, is the sequence,
((a′
1, b′
1) = (−∞, r2), (a′
2, b′
2) = (a1, b1), (a′
3, b′
3) =
(a2, b2), . . . , (a′
k+1, b′
k+1) = (ak, bk), (a′
k+2, b′
k+2) =
(r1, −∞)) where (ai, bi) are deﬁned as above.
4) The i-th horizontal strip with respect to a step is the
region bounded by horizontal halﬂines Li going through
the point (ai, bi) and ending in this point, similarly for


<!-- página 3 -->

Fig. 1.
Improvement contribution for the step Si, middle case.
Li+1 and by the vertical line segment determined by the
endpoints (ai+1, bi) and (ai+1, bi+1).
DEF 7 (Improvement Contribution). Let Si denote the i-
th step, ((ai, bi), (ai+1, bi+1)), of an augmented staircase
Ar
staircase and let y = (y1, y2) ∈R2. The Improvement
Contribution (IC) is deﬁned as follows.
IC((y1, y2), Si) =



0
,y1 ≥ai+1 or y2 ≥bi
(ai+1 −y1)(bi −y2)
,y1 ≤ai+1 and bi+1 ≤y2 ≤bi
(ai+1 −y1)(bi −bi+1)
,y1 ≤ai+1 and y2 ≤bi+1
The notion of improvement contribution is illustrated in
Figure 1 for the middle case (i.e., y1 ≤ai+1 and + bi+1 ≤
y2 ≤bi). The shaded area is the improvement contribution for
the example point (y1, y2). Likewise, Figure 2 illustrates the
improvement contribution for the last case in the deﬁnition.
LEMMA 2. Let A ∈A2 and r = (r1, r2) ∈R2 be a reference
point for A and Ar
staircase the associated, augmented staircase
of A with respect to r and A and let y = (y1, y2) ∈R2. Then
I(y, A) = Pk+1
i=1 IC(y, Si), where k is the number of points in
A.
Proof: : The Lemma follows directly from the deﬁnition
of IC. See also Figures 1 and 2.
THM
1. The hypervolume based EIH satisﬁes N2 for
m = 1 or m = 2.
Proof: The 1-D case is the statement of Lemma 1).
For the 2D case we proceed as follows. Let A ∈A2 with
k points and r = (r1, r2) ∈R2 be a reference point for A
and Ar
staircase the augmented staircase of A. Let Si denote
the steps of Ar
staircase as in Deﬁnition 7.
Let ˆy = ( ˆy1, ˆy2) be the prediction (at some x ∈X) and
s = (s1, s2) its standard deviation. Without loss of generality
we assume ˆy = 0. The expected improvement is equal to:
Z
R
I(y, A) · PDF0,s(y)dy
Fig. 2.
Improvement contribution of Si, last case.
, where R = R2. Due Lemma 2 this integral can be rewritten
as:
Z
R
k+1
X
i=1
IC(y, Si) · PDF0,s(y)dy
(5)
We will decompose the integration region R in the integral
in Expression 5 into horizontal strips Hi (see Deﬁnition 6).
We will show that in case the vertical variance stays the same
and the variance of the horizontal coordinate is incremented,
then the integration contribution by each strip is bigger for
bigger horizontal variance. The integral for strip Hi reads as
follows:
Z
Hi
I(y)PDF0,s(y)dy
=
Z
Hi
k+1
X
j=1
IC(y, Sj) · PDF0,s(y)dy
=
Z bi
bi+1
Z ai+1
−∞
k+1
X
j=1
IC((y1, y2), Sj) ·
·PDF0,s1(y1) · PDF0,s2(y2)dy1dy2
=
k+1
X
j=1
Z bi
bi+1
Z ai+1
−∞
IC((y1, y2), Sj) ·
·PDF0,s1(y1) · PDF0,s2(y2)dy1dy2
=
i
X
j=1
Z bi
bi+1
Z ai+1
−∞
IC((y1, y2), Sj) ·
·PDF0,s1(y1) · PDF0,s2(y2)dy1dy2
=
i−1
X
j=1
Z bi
bi+1
(bj −bj+1)PDF0,s2(y2)dy2 ·
·
Z aj+1
−∞
(aj+1 −y1)PDF0,s1(y1)dy1
+
Z bi
bi+1
(bi −y2) · PDF0,s2(y2)dy2 ·
·
Z ai+1
−∞
(ai+1 −y1)PDF0,s1(y1)dy1
(6)


<!-- página 4 -->

By inspecting Expression 6 for each summand with different
variances in the horizontal direction (i.e.,s+
1 and s1 with s+
1 >
s1) and keeping the variances the same in the vertical direction,
we see by Lemma 1 that each of the summands for s+
1 is
greater or equal than the corresponding summand for s1 (the
left side of the products are the same while the right side
obeys the Lemma 1). Clearly one of the summands in case of
s+
1 will be strictly bigger than the corresponding summand in
case of s1. Since the statement holds for each horizontal strip,
we see also that the total integral (which is the sum over all
integrals on horizontal strips) is strictly bigger in case of s+
1 .
We have shown that by increasing the variance in the
horizontal (y1) direction, the EIH is strictly bigger in case
the variance is kept the same in the vertical (y2) direction.
By symmetry it also holds that by increasing the variance
in the vertical (y2) direction, the EIH is strictly bigger in
case the variance is kept the same in the horizontal (y1)
direction. Hence, increasing the variance in both directions
will lead to a strictly bigger EIH – because we can do this
in two steps, ﬁrst increasing the variance in the horizontal
direction and holding the vertical variance the same and
subsequently increasing the vertical variance while holding
the horizontal variance the same on the increased level (i.e.,
(s1, s2) →(s+
1 , s2) →(s+
1 , s+
2 )). Both steps will increase the
EIH.
The following lemma summarizes properties of the minima
and maxima of the expected improvement:
LEMMA 3. Minima and maxima of the expected improve-
ment: Given a mean value ˆy ∈Rm, a standard deviation
ˆs ∈Rm
≥0, a reference point r and an approximation set
A ∈Am, ˆy ≤r and A ⪯r, then for the value EIH(ˆy,ˆs, r, A)
of the expected improvement it holds that
(a)
EIH(ˆy,ˆs, r, A) ≥0
(a’)
if ˆs > 0 then the stricter condition EIH(ˆy,ˆs, r, A) >
0 holds.
(b)
EIH(ˆy,ˆs, r, A) ≤EIH(ˆy,ˆs, r, {r}) < ∞
Proof: The ﬁrst implication follows from I(ˆy,ˆs, r, A) ≥0
in Deﬁnition 2. Likewise, because of the inﬁnite support of
the Gaussian PDF, the stricter condition (a′) holds in case of
strictly positive standard deviations. Part (b) follows from the
fact that for all points y that dominate the reference point the
improvement I(ˆy,ˆs, r, A) is upper bounded by I(ˆy,ˆs, r, {r}).
For all other points it is zero in both cases.
The practical implication of this lemma is that as long
as the variances are positive the expected improvement can
serve as a criterion guiding the search, also for mean value
vectors that are dominated. This distinguishes it for instance
from the most likely improvement (MLI) in hypervolume,
as deﬁned in [7], which obtains zero values when the mean
values are dominated. Moreover (b) implies that the expected
improvement can always be computed as a ﬁnite value (no
singularities occur).
Fig. 3.
Construction used in the proof of the stated inequality.
IV. COMPUTATION
Let A = {y(1), · · · , y(k)} ∈Am. The integration region
Rm can be partitioned into a set of interval boxes, and then
piecewise integration can solve the problem of computing the
integral directly. To provide an intuition on the grid-variables
and areas introduced in the following, Figure 4may serve the
reader.
Let b(1)
i , b(2)
i , . . . , b(k)
i
denote the sorted list of all the i-th
coordinates of the vectors y(1) ∈Rm, . . . , y(k) ∈Rm. For
technical reasons we deﬁne b(0)
i
= −∞and b(k+1)
i
= ri,
b(k+2)
i
= ∞.
The grid-coordinates b(i)
j
give rise to a partitioning into
grid cells. We can enumerate these grid cells as follows.
For each (i1, . . . , im), where is ∈{0, . . . , k + 1}, the grid
cell named C(i1, . . . , im) is determined by (b(i1)
1
, . . . , b(im)
m
)T
and (b(i1+1)
1
, . . . , b(im+1)
m
)T as the half open (from below)
interval box (i.e., (b(i1)
1
, b(i1+1)
1
] × (b(i2)
2
, b(i2+1)
2
] × · · · ×
(b(im)
m
, b(im+1)
m
]). We call (b(i1)
1
, . . . , b(im)
m
)T the lower corner
of C(i1, . . . , im) denoted by l(i1, . . . , im), likewise we call
(b(i1+1)
1
, . . . , b(im+1)
m
)T the upper corner of of C(i1, . . . , im)
denoted by u(i1, . . . , im). With this notation we will also
denote C(i1, . . . , im) by (l(i1, . . . , im), u(i1, . . . , im)]. See
Figure 4 for an example.
It can be directly observed that there are many cells the
integration over which adds a contribution of zero to the
integral. These are cells that
1) have lower corners l(i1, . . . , im) that are dominated or
equal to points in A, i.e. A ⪯l(i1, . . . , im), or
2) have upper corners u(i1, . . . , im) that do not dominate
the reference point, i.e. u(i1, . . . , im) ⊀r.
The second criterion is fulﬁlled by grid cells C(i1, . . . , im)
with i1 = k + 1 or i2 = k + 1 . . . or im = k + 1, i.e. at least
one of their coordinates has index k + 1.
All cells that fulﬁll criterion (1) or (2) will be called inactive
cells, while the other cells will be termed active cells. Active


<!-- página 5 -->

Fig. 4.
Schematic drawing of a population, its hypervolume, and grid in the
bi-objective case. The black points are the points of the population, except the
point in the upper right corner that marks the position of the reference point
for the hypervolume. The yellow region deﬁnes the measured hypervolume
S. The grid coordinates are indicated by b(i)
1
and b(i)
2
for the ﬁrst and second
coordinate, respectively. Grid-cell C(1, 1) is highlighted by a thick black
boundary.
Fig. 5.
Schematic drawing of the integration area and grid in the bi-objective
case.(S−= {z ∈Rm|A(u) ⪯z ⪯v}, where A(u) = {p ∈A|u ≺p} )
cells are cells the inner points of which are dominating the
reference point and are not dominated by any point in A.
Obviously, the expected improvement integral is the sum
of all contributions of integration of the improvement integral
over the set of active cells C+, i.e.
EIH(x, A) =
X
C(i1,...,im)∈C+
δ(i1, . . . , im)
(7)
, where
δ(i1, . . . , im) =
Z
y∈(l(i1,...,im),u(i1,...,im)]
I(y, A)·PDFx(y)dy
(8)
. Note, that it is important to choose the half-open interval
boxes here, as the lower corners can reach out to −∞and we
have to avoid overlapping of boundaries, which might cause
double integration of non-zero contributions in case of zero
standard deviations. Moreover, because of the possibility of
zero standard deviations, Lebesgue integration is assumed.
Let us now discuss, how the contribution δ(i1, . . . , im) can
be computed. We ﬁrst describe the relevant expressions which
are followed by detailed derivation later on. Readers only
interested in the implementation of the integral can omit the
latter part.
The approach is discussed in a top-down way, we will
provide a general expression for computing δ(i1, . . . , im) and
then its components are deﬁned.
The contribution δ(i1, . . . , im) of an active grid cell can be
computed via
δ(i1, . . . , im) = (
m
Y
j=1
δj(i1, . . . , im))
−
Vol(S−)
m
Y
i=1
(Φ(ui −µi
σi
) −Φ(li −µi
σi
))·
(9)
with
δj(i1, . . . , im) =
Ψ(vj(i1, . . . , im), uj(i1, . . . , im), µj, σj)
−
Ψ(vj(i1, . . . , im), lj(i1, . . . , im), µj, σj)
(10)
and j = 1, . . . , m. (Ψ is deﬁned in Equation 11. For S−see
Figure 5. )
To each l and A (and reference point) we can associate a
vector v as follows. Let A(l) be equal to the set {z ∈A|l ≺z}
and let for each i, 1 ≤i ≤m, pi denote the usual projection
from Rm onto the i-th factor R (i.e., pi((r1, · · · , ri, · · · rm)) =
ri). Then, if A(l)̸ = ∅, vi = max(pi(A(l))). Alternatively we
can deﬁne the vector v(i1, . . . , im) ∈Rm as follows. The j-
th coordinate of v(i1, . . . , im) is the j-th coordinate of the
intersection point, called h(j), of the attainment surface of A
and the ray {y ∈Rm|∃t ≥0 : y = l(i1, . . . , im) + te(j)}
(where j ∈{1, . . . , m}).
We
can
construct
the
j-th
coordinate
of
v
as
follows
by
ﬁnding
the
ﬁrst
vector
in
the
sequence
l(i1, . . . , ij, . . . im), l(i1, . . . , ij
+ 1, . . . im), l(i1, . . . , ij
+
2, . . . im) etc. which does not strictly dominate some point of
A. The j-th coordinate of this point is announced as the j-th
coordinate of v (cf. Fig 5).
The computation of this boundary coordinate can be done
by looping only at the discrete steps given by the grid
nodes in direction of the unit vector e(j). In case m = 2
the monotonicity of the staircase structure of the polyline
describing the attainment curve can be exploited to determine
this value efﬁciently .
The integration of the marginal normal distributions is
captured in the expression:
Ψ(a, b, µ, σ) = σ · φ(b −µ
σ
) + (a −µ)Φ(b −µ
σ
)
(11)
. In this expression φ denotes the probability density function
of the standard normal distribution, and Φ denotes the cumu-
lative probability density function of the normal distribution,


<!-- página 6 -->

i.e.:
φ(x) =
1
√
2π exp(−x2/2),
Φ(x) = 1
2(1 + erf(x/
√
2))
(12)
Finally, Vol(S−) is a correction term. It denotes the hyper-
volume measure for the subset of points in A dominated or
equal to u(i1, . . . , im) and as reference point v(i1, . . . , im)
(see also Figure 5). This can be computed by means of
a standard procedure for hypervolume computation. For the
2-D case differences of the cumulated contributions to the
hypervolume, when integrating it along f1 along the staircase,
can be exploited for its efﬁcient computation.
The direct computation of the expected improvement con-
tribution δ(i1, . . . , im) can best be motivated by means of
decomposing the general integral expression. For the sake of
clarity, we assume that the grid indices are i1, . . . , im and
omit them as parameters, i.e. we set l = l(i1, . . . , im), u =
u(i1, . . . , im), C = C(i1, . . . , im), and so forth.
The improvement I(y) in the grid cell C always can be de-
composed into the contribution of L+ that is the hypervolume
measure of the non-dominated part in [u, v] and a ’boundary’
contribution V that depends on the integration variable y and
forms a boundary layer around [u, v]. The set V is determined
by the set difference
V = [y, v] −[u, v]
(13)
. In summary for points y within the cell C it holds:
I(y) = Vol([y, v] −[u, v] + L+)
(14)
. An important observation is that only the ﬁrst term, namely
[y, v] depends on y.
After these preliminaries, let us recall the expected improve-
ment integral (expression 2). The contribution δ of cell C is
given by:
δ =
Z u1
l1
· · ·
Z um
lm
I(y1, .., ym, A) · PDFx(y1, .., ym)dy1..dym
(15)
, where l(i1, . . . im)
=
(l1, . . . , lm) and l(i1, . . . im)
=
(u1, . . . , um). In order to compute δ explicitly by reduc-
ing, among others, to an S-metric computation of S−(i.e.,
−Vol(S−), we deﬁne three quantities Q1, Q2, and Q3 as
follows.
Q1 =
Z u1
l1
· · ·
Z um
lm
m
Y
i=1
(vi −yi)..PDFx(y1, .., ym)dy1..dym
(16)
,
Q2 =
Z u1
y1=l1
· · ·
Z um
lm
m
Y
i=1
(vi −ui) · PDFx(y1, .., ym)dy1..dym
(17)
, and
Q3 =
Z u1
l1
· · ·
Z um
lm
Vol(L+) · PDFx(y1, . . . , ym)dy1 . . . dym
(18)
. Clearly δ = Q1 −Q2 + Q3.
The expression −Q2 + Q3 is equal to:
(Vol(L+) −
m
Y
i=1
(vi −ui))
·
Z u1
l1
· · ·
Z um
lm
PDFx(y1, . . . , ym)dy1 . . . dym
(19)
Moreover the expression Vol(L+)−Qm
i=1(vi−ui) is the nega-
tive hypervolume measure for the set of points in A dominated
or equal to u with reference point v (i.e., Vol(L+)−Qm
i=1(vi−
ui) = −Vol(S−), where S−= {z ∈Rm|A(u) ⪯z ⪯u} with
A(u) = {p ∈A|u ≺p}, see also Figure 5).
In addition, the integral
Z u1
l1
· · ·
Z um
lm
PDFx(y1, . . . , ym)dy1 . . . dym
is, in case of independent normal distributions, equal to the
term
m
Y
i=1
(Φ(ui −µi
σi
) −Φ(li −µi
σi
))
.
An expression for Q1 is more difﬁcult to derive, due to the
nonlinearity. First of all we decompose the integral into the
product of one-dimensional integrals:
Q1
=
m
Y
i=1
Z ui
li
(vi −z)φ(yi −µi
σi
)dz
(20)
=
m
Y
i=1
(
Z ui
−∞
(vi −z)φ(z −µi
σi
)dz
−
Z li
−∞
(vi −z)φ(z −µi
σi
)dz)
=
m
Y
i=1
(Ψ(vi, ui, µi, σi) −Ψ(vi, li, µi, σi))
. The last step is motivated by the following equality and the
deﬁnition in Equation 11 :
Z b
−∞
(a −z) 1
σ φ(z −µ
σ
)dz = σφ(b −µ
σ
) + (a −µ)Φ(b −µ
σ
).
(21)
.
The
computation
of
Ψ
reduces
to
the
integration
of
a
one-dimensional
integration
the
details
of
which
are
as
follows:
Compute
R b
−∞(a
−
y)
pdf(y)dy,
where
pdf(y)
=
2
σ√π exp(−1
2( y−µ
σ )2).
Answer:
R b
−∞(a −y)
2
σ√πe−1
2 ( y−µ
σ
)2dy
=
2
σ√πe−1
2 ( y−µ
σ
)2
+
√
2(a −µ) erf(
√
2
2σ (b −µ)) +
√
2(a −µ). Simpliﬁed:
σφ( b−µ
σ ) + (a −µ)Φ( b−µ
σ ) with φ(y) =
1
√
2πe−1
2 y2 being
the probability density function of the standard normal
distribution and Φ(y) = 1
2(1 + erf( y
√
2)) being the cumulative
density function of the standard normal distribution.
All components used in the computation of δ have been
derived and we have summarized the computation procedure.
The computation is relatively simple to implement. It needs no
numerical integration (except, of course, for the computation


<!-- página 7 -->

of the function erf). Implementations of the erf function can be
found, however, in most programming languages and statistical
packages.
A useful remark is to note that in case of two objectives (i.e.,
m = 2), the Improvement function I(y, A) can be computed
in O(k), where k is the size of set A (A ∈A2) without
the need to compute hypervolume(s). Of course, provided
A is sorted on its ﬁrst or second coordinate. The function
I can be computed by applying the elementary increment
function IC to the k + 1 neighbor pairs of Ar
staircase and
take the sum of these k + 1 results. Moreover the piecewise
deﬁnition of I caused by the piecewise nature of IC can also
be computed in symbolic mathematics software such as Maple
or Mathematica giving way to a very short speciﬁcation of the
computation of EIH – the source code for this is available on
natcomp.liacs.nl.
V. GLOBAL OPTIMIZATION ALGORITHM
Consider a function EI (such as EIH) that for each input
vector x computes a quantity that determines how promising
this point is for improving a Pareto front approximation. It
can use the information of all previously evaluated points.
The expected improvement algorithm is similar to Bayesian
Optimization [18] and Efﬁcient (or Statistical) Global Opti-
mization [4], [12], with the difference, that the hypervolume-
based expected improvement EIH replaces the single-objective
expected improvement.
Algorithm 1 Generic algorithm for EIH-based global (multi-
objective) optimization
Generate initial set of k points Xk = (x(1), ..., x(k)) (e.g.
uniform randomly in the search space X)
Evaluate initial points Yk = (y(1) = f(x(1)), . . . , y(k) =
f(x(k)))
Set Xnd
k , Ynd
k
to the subsequence of non-dominated solu-
tions among Xk, Yk.
t ←k
while t < tmax do
Update the Gaussian model based on Xt, Yt,
t ←t + 1
choose x(t) ∈arg minx∈X EIH(x, Ynd
t )
y(t) = f(x(t))
Xt = Xt−1 ◦x(t); Yt = Yt−1 ◦y(t)
Set Xnd
t , Ynd
t
to the sequence of non-dominated solutions
among Xt, Yt.
end while
return Xnd
t , Ynd
t
A single numerical experiment will serve here as a proof
of concept and shall encourage future studies in using the
hypervolume-based expected improvement. Note, that the ex-
pected improvement in hypervolume has already been used
in pre-selection schemes of metamodel-assisted evolutionary
algorithms in previous work [6], [21]. In contrast, the follow-
ing study will be on the Bayesian global optimization scheme
(Algorithm 1).
Fig. 6. Expected improvement algorithm on 2-D generalized sphere problem.
A. Numerical Experiment
a) Research Question: It will be studied on a sim-
ple multiobjective optimization landscape, if and how fast
the hypervolume-based expected improvent algorithm con-
verges to a known Pareto front. The problem is the 2-D
generalized sphere problem: minimize f1(x) = ||x −1||,
minimize f2(x) = ||x + 1||, x ∈[−2, 2] × [−2, 2] ⊂R2.
For an analysis of the generalized sphere problem, see [7],
p.182. The Pareto front is the line segment from (0, 2·
√
2) to
(2 ·
√
2, 0), the efﬁcient set is the line segment that connects
(−1, −1) and (1, 1).
b) Experimental
setup:
The
metamodel
used
is
a
Gaussian
random
ﬁeld
model
with
Gaussian
kernel
exp −θ||x −x′||2. The correlation parameter was estimated
from the intial sample to θ = 0.0001 and was set to this
constant during the run. The size of the initial population
was set to 10 and 15 new points were generated using the
Algorithm 1. In total the test function to be optimized was
evaluated 25 times.
c) Result: The results of the experiment is depicted in
Figure 6. In all pictures, points that have been evaluated are
indicated by stars. The points from the initial set are addition-
ally marked by blue squares. Efﬁcient points are surrounded by
circles. Darker gray-levels represent lower values. The top row
depicts the mean value of the Gaussian random ﬁeld model at
x ∈[−2, 2]×[−2, 2] for f1 and f2, resp. Likewise, the middle
row depicts the variance of the Gaussian random ﬁeld model
at x ∈[−2, 2] × [−2, 2] for f1 and f2, resp. In the bottom
row on the left hand side all evaluated points are displayed in
the objective space. On the right hand side of the same row
the hypervolume-based expected improvement values after the
25th iteration are displayed. For each coordinate pair (x1, x2)
the gray value indicates the expected improvement of x.
Initially 10 points (blue squares in the plot) are evaluated.
Within the ﬁrst 4 loops the algorithm places an evaluation in
each of the four corners of the search space. Then it proceeds
with choosing points close to the Pareto front with points.


<!-- página 8 -->

Each of the points chosen is non-dominated to the previous
points and ﬁlls a gap in the approximation. After 15 iterations
of the main loop the algorithm was terminated (by the user).
The total time of the experiment was in the order of a couple
of minutes on a modest Pentium 6 processor.
In summary, using only 25 evaluations of the original
objective functions, including already the initial 10 evaluations,
the algorithm discovers a fairly close approximation to the
Pareto front.
VI. CONCLUSION
This paper discusses an expected improvement criterion
based on the hypervolume indicator (EIH) that can be used in
multiobjective optimization with costly function evaluations.
It is shown that, given a Gaussian random ﬁeld and an
approximation of the efﬁcient set, the EIH can be computed
by means of an exact algorithm. This paper derives the steps
of this algorithm.
We have proven the monotonicity property N2, introduced
in [22], analytically for two dimensions. This property states,
that points with the same mean are ’rewarded’ by a higher
variance, no matter where the location of the mean value
vector is. This property conforms with the one dimensional
case and it shows that explorative behavior of the algorithms
is rewarded, when selecting by means of the EIH.
A ﬁrst numerical study on a generalized sphere model
provides a proof of concept that Bayesian Optimization Algo-
rithms (or: Efﬁcient Global Optimization) can be generalized
by means of the EIH to multi-objective problems. In the exam-
ple this Hypervolume-Based Bayesian Optimization algorithm
obtained a fairly close approximation to the Pareto front in
only 25 iterations.
Future work is needed to study the scalability and robustness
of the Bayesian optimization algorithm. Moreover, it needs to
be veriﬁed whether the theorem on property N2 holds also
for more than two dimensions.
The MATLAB implementation of the expected improve-
ment is made available under natcomp.liacs.nl.
ACKNOWLEDGMENT
The authors would like to thank Johannes Kruisselbrink
for the Kriging implementation in MATLAB. M. Emmerich
acknowledges ﬁnancial support by the DELIVER Project co-
ﬁnanced by STW/NWO. The authors acknowledge Tobias
Wagner for his comments on the manuscript.
REFERENCES
[1] Bartz-Beielstein, T.; Lasarczyk, C. and Preuss, M. (2005), Sequential
Parameter Optimization, in B. McKay et al., ed., ’Proc. of CEC’, IEEE,
, pp. 773–780.
[2] B¨uche, D.; Schraudolph, N. N. and Koumoutsakos, P. (2005), ’Acceler-
ating Evolutionary Algorithms with Gaussian Process Fitness Function
Models’, IEEE Transact. SMC, Special Issue on Knowledge Extraction
and Incorporation in Evolutionary Computation (Part C) 35(2), 183-194.
[3] Bader, J. and Zitzler, E. (2010), ’HypE: An Algorithm for Fast
Hypervolume-Based Many-Objective Optimization’, Evolutionary Com-
putation (in print), 1-32.
[4] Cox, D.D. and John S., SGO: a statistical method for global optimization.
In V. Hampton, editor, Multidisciplinary design optimization, volume 2,
pages 315329. SIAM, Philadelphia, PA, 1997.
[5] M.A El-Beltagy and P.B. Nair and A.J. Keane, Metamodelling Techniques
for Evolutionary Optimisation of Computationally Expensive Problems:
Promises and Limitations, Proc. of GECCO, Int’l Conf. on Genetic
and Evolutionary Computation, Orlando 1999, pages 196-203,Morgan
Kaufman, 1999
[6] Emmerich, M.; Giannakoglou, K. and Naujoks, B. (2006), ’Single- and
multi-objective evolutionary optimization assisted by Gaussian random
ﬁeld metamodels’, IEEE Trans. Evol. Comput. 10(4), 421–439.
[7] Emmerich,M., Single- and Multiobjective Evolutionary Design Opti-
mization Using Gaussian Random Field Metamodels, PhD Thesis, FB
Informatik, TU Dortmund, 2005
[8] Emmerich, M. and Naujoks, B. (2004), Metamodel-assisted multiob-
jective optimisation strategies and their application in airfoil design.,
in I. Parmee, ed., ’Proc of. Fifth Int’l. Conf. on Adaptive Design and
Manufacture (ACDM), Bristol, UK, April 2004, Springer, pp. 249–260.
[9] Igel, C.; Hansen, N. and Roth, S. (2007), ’Covariance Matrix Adaptation
for Multi-objective Optimization’, Evol. Comput. 15(1), 1–28.
[10] Jin, Y. (2005), ’A comprehensive survey of ﬁtness approximation in
evolutionary computation’, Soft Computing Journal 9(1), 3-12.
[11] Jeong, S. and Obayashi, S. (2005), Efﬁcient global optimization (EGO)
for multi-objective problem and data mining, in D. Corne and others, ed.,
’Proc. CEC’, IEEE, , pp. 2138–2145.
[12] Jones, D., Schonlau, M., Welch, W., (1998) Efﬁcient Global Optimiza-
tion of Expensive Black-Box Functions, Journal of Global Optimization,
Vol. 13, 455-492.
[13] Jones, D. R.; Schonlau, M. and Welch, W. J. (1998), ’Efﬁcient Global
Optimization of Expensive Black-Box Functions’, J. Glob. Optim. 13(4),
455–492.
[14] Knowles, J. D.; Corne, D. W. and Fleischer, M. (2003), Bounded
Archiving using the Lebesgue Measure, in ’Proceedings of the IEEE
Congress on Evolutionary Computation’, IEEE Press, , pp. 2490–2497.
[15] Keane, A. J. (2006), ’Statistical Improvement Criteria for Use in
Multiobjective Design Optimization’, AIAA J. 44(4), 879–891.
[16] J.W. Klinkenberg, M. Emmerich, A. Deutz: Expected Improvement of
the S-Metric for ﬁnite Pareto front Approximations, Extended Abstract,
Proc. of MCDM 2008, Auckland, NZ.
[17] Knowles, J. (2006), ’ParEGO: A hybrid algorithm with on-line landscape
approximation for expensive multiobjective optimization problems’, IEEE
Trans. Evol. Comput. 10(1), 50–66.
[18] Mockus, J.; Tiesis, V. and Zilinskas, A. (1978), The application of
Bayesian methods for seeking the extremum, in L. C. W. Dixon and
G. P. Szego, ed., ’Towards Global Optimization’, North-Holland, , pp.
117–129.
[19] Ponweiser, W.; Wagner, T.; Biermann, D. and Vincze, M. (2008),
Multiobjective Optimization on a Limited Budget of Evaluations Using
Model-Assisted S-Metric Selection, in ’Proc. PPSN X’, Springer-Verlag,
Berlin, Heidelberg, pp. 784–794.
[20] Ponweiser, W.; Wagner, T. and Vincze, M. (2008), Clustered Multiple
Generalized Expected Improvement: A Novel Inﬁll Sampling Criterion
for Surrogate Models, in Z. Michalewicz and others, ed., ’Proc. CEC’,
IEEE, , pp. 3514–3521.
[21] Ofer M. Shir, Michael Emmerich, Thomas B¨ack and Marc J.J. Vrakking.
The Application of Evolutionary Multi-Criteria Optimization to Dynamic
Molecular Alignment. Proceedings of IEEE-CEC 2007, Singapore; IEEE
Press.
[22] Wagner, T.; Emmerich, M.; Deutz, A. and Ponweiser, W. (2010), On
expected-improvement criteria for model-based multi-objective optimiza-
tion, in ’Proc. of PPSN XI Vol. 1’, Springer-Verlag, Berlin, Heidelberg,
pp. 718–727.
[23] E. Zitzler: Evolutionary Algorithms for Multiobjective Optimization:
Methods and Applications, PhD Thesis, University of Zurich, Switzerland
[24] Zitzler, Eckart and K¨unzli, Simon: Indicator-Based Selection in Mul-
tiobjective Search, Parallel Problem Solving from Nature - PPSN VIII,
Springer Berlin Heidelberg, 2004



---

## ANEXO — Conteúdo textual das imagens (OCR)

> Texto extraído por OCR (Apple Vision) das figuras/imagens do PDF — apenas conteúdo NOVO, ausente da camada de texto (labels de eixos, legendas internas, tabelas/equações rasterizadas, slides). OCR de fórmulas é aproximado.

### Página 3
*(figura em y≈53–199)*
- (aj-1,b-1)
- (a;+1,b;+1)
- (VI,V2)
*(figura em y≈53–199)*
- (aj-1, b-1)
- (V1.V2)
- (a;+ 1, b;+1)

### Página 4
*(figura em y≈54–242)*
- Assume: fmin>0, s>s'
- (0, fmin)
- fmin/S
- (fmin/S',0)
- (3 , I ca.) 800, )da < f 1(zs.,.u )4(0,1) dz

### Página 5
*(figura em y≈316–486)*
- Tref
*(figura em y≈54–224)*
- Tref
- AL erAD
- JC(1,1)
- 70 bf)

### Página 7
*(figura em y≈54–239)*
- Gaussian Process f
- Gaussian Process f2
- Gaussian Process Variance f1
- Gaussian Process Variance f2
- Evaluated points in objective space
- 0.00 a
