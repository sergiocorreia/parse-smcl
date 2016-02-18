{smcl}
{hline}
help for {hi:psmatch2}
{hline}

{title:Mahalanobis and Propensity score Matching}

{p 8 21 2}{cmdab:psmatch2}
{it:depvar}
[{it:indepvars}]
[{cmd:if} {it:exp}]
[{cmd:in} {it:range}]
[{cmd:,}
    {cmdab:out:come}{cmd:(}{it:varlist}{cmd:)}
    {cmdab:p:score}{cmd:(}{it:varname}{cmd:)}
    {cmdab:n:eighbor}{cmd:(}{it:integer}{cmd:)}
    {cmd:radius}
    {cmdab:cal:iper}{cmd:(}{it:real}{cmd:)}
    {cmdab:mahal:anobis}{cmd:(}{it:varlist}{cmd:)}
    {cmdab:ai}{cmd:(}{it:integer}{cmd:)}
    {cmdab:pop:ulation}
    {cmdab:altv:ariance}
    {cmd:kernel}
    {cmd:llr}
    {cmdab:k:erneltype}{cmd:(}{it:type}{cmd:)}
    {cmdab:bw:idth}{cmd:(}{it:real}{cmd:)}
    {cmd:spline}
    {cmdab:n:knots}{cmd:(}{it:integer}{cmd:)}
    {cmdab:com:mon}
    {cmd:trim}{cmd:(}{it:real}{cmd:)}
    {cmdab:norepl:acement}
    {cmdab:desc:ending}
    {cmd:odds}
    {cmd:index}
    {cmd:logit}
    {cmd:ties}
    {cmdab:qui:etly}
    {cmd:w}{cmd:(}{it:matrix}{cmd:)}
    {cmd:ate}]
    
{p 8 21 2}where {it:indepvars} and {cmdab:mahal:anobis}{cmd:(}{it:varlist}{cmd:)} may contain factor variables; see {cmd:fvvarlist}.

{title:Description}

{pstd}
{cmd:psmatch2} implements full Mahalanobis matching and a variety of propensity score matching methods
to adjust for pre-treatment observable differences between a group of treated and a group of untreated.
Treatment status is identified by {it:depvar}==1 for the treated and {it:depvar}==0 for the untreated observations.
{p_end}

{pstd}
{cmd:psmatch2} is being continuously improved and developed. Make sure to keep your version up-to-date as follows

    {inp: . ssc install psmatch2, replace}

{pstd}
By default {cmd:psmatch2} calculates approximate standard errors on the treatment effects assuming independent
observations, fixed weights, homoskedasticity of the outcome variable within the treated and within the control
groups and that the variance of the outcome does not depend on the propensity score:

{pstd}
1/N1*Var(Y | DM=1) + Sum(w_i^2; i in DM=0)/(N1)^2*Var(Y | DM=0)

{pstd}
where N1 is the number of matched treated, DM=1 denotes the matched treated, DM=0 the matched controls and  
w_i is the weight given to control i. {cmd:psmatch2} stores the estimate of the standard error of the ATT 
in {it:r(seatt)} or with more than one outcome variable, in {it:r(seatt_varname)}.

{pstd}
With nearest neighbor matching on the X's ({cmd:mahal()}), then analytical standard errors as in Abadie and Imbens (2006) are calculated
when {it:M>0} is passed using option {cmd:ai(}{it:M}{cmd:)}, where {it:M} is the number of neighbors that are used
to calculate the conditional variance (formula (14) in Abadie and Imbens, 2006).

{pstd}
{cmd:psmatch2} stores the estimate of the treatment effect on the treated in {it:r(att)}, this allows
bootstrapping of the standard error of the estimate (although it is unclear whether the bootstrap is valid in this context). 
This can be done as follows:

    {inp: . bootstrap r(att) : psmatch2 training age gender, out(wage)}

{pstd}
If the average treatment is requested using option {it:ate} the estimate is returned
in {it:r(ate)}. The average treatment effect on the untreated is then also returned in {it:r(atu)}.
With more than one outcome variable the effects are returned as r(att_{it:varname}) etc. for each
outcome variable and effect.

{pstd}
See the documentation of {help bootstrap} for more details about bootstrapping in Stata.

{pstd}
If you want to be able to replicate your results you should set {help seed}
before calling {cmd:psmatch2}.

{pstd}
The propensity score - the conditional treatment probability - is either directly provided by the
user or estimated by the program on the {it:indepvars}. Note that the sort order of your data could affect the
results when using nearest-neighbor matching on a propensity score estimated with categorical (non-continuous)
variables. Or more in general when there are untreated with identical propensity scores.

{pstd}
Matching methods to choose from are one-to-one (nearest neighbour or within caliper;
with or without replacement), {it:k}-nearest neighbors, radius, kernel, local linear regression,
'spline-smoothing' and Mahalanobis matching. The following list presents the syntax for each method.

{pstd}
You can also click {dialog psmatch2:here} to pop up a {dialog psmatch2:dialog} or type
{inp: db psmatch2}.

{title:About sample weights}

{pstd}
As far as we know it's not really clear in the literature how to accommodate sample weights in the context of matching. If you are aware how to properly account for sampling weights, please let us know.
In the meantime, here are some thoughts you might want to take into consideration when asking yourself the following questions:

{pstd}
1) Should I use weights when estimating the score?

{pstd}
The recommendation to date seems to be to ignore sampling weights, estimate the propensity
score using a logit model (option {cmd:logit}) and match on the (logarithm of the) odds ratio (option {cmd:odds}).

{pstd}
2) Should I use weights after having performed matching?

{pstd}
When interested in the effect of treatment on the treated, the sampling weights should
refer to the treated alone. So the pweigths should be applied to the observed and to
the matched outcome (if need be further restricted to the treated on the common support)
for all the treated:

{pstd}{inp: . sum outcome if treated==1 [aw=pweight]}

{pstd}{inp: . sum _outcome if treated==1 [aw=pweight]}

{title:Matching within strata}

{pstd} The following code illustrates how to match within exact cells and then calculate the average effect for the whole population.

	{cmd:g att = .}
	{cmd:egen g = group(groupvars)}
	{cmd:levels g, local(gr)}
	{cmd:qui foreach j of local gr {c -(}}
		{cmd:psmatch2 treatvar varlist if g==`j', out(outvar)}
		{cmd:replace att = r(att) if  g==`j'}
	{cmd:{c )-}}
	{cmd:sum att}

{title:Detailed Syntax}

{phang}
{bf:One-to-one matching:}

{p 8 21 2}{cmdab:psmatch2}
{it:depvar}
[{it:indepvars}]
[{cmd:if} {it:exp}]
[{cmd:in} {it:range}]
{cmd:,}
    [{cmdab:out:come}{cmd:(}{it:varlist}{cmd:)}
    {cmdab:p:score}{cmd:(}{it:varname}{cmd:)}
    {cmdab:ai}{cmd:(}{it:integer k}>1{cmd:)}
    {cmdab:mahal:anobis}{cmd:(}{it:varlist}{cmd:)}
    {cmdab:cal:iper}{cmd:(}{it:real}{cmd:)}
    {cmdab:norep:lacement}
    {cmdab:desc:ending}
    {cmdab:com:mon}
    {cmd:trim}{cmd:(}{it:real}{cmd:)}
    {cmd:odds}
    {cmd:index}
    {cmd:logit}
    {cmd:ties}
    {cmdab:nowarn:ings}
    {cmdab:qui:etly}
    {cmd:ate}]


{phang}
{bf:{it:k}-Nearest neighbors matching:}

{p 8 21 2}{cmdab:psmatch2}
{it:depvar}
[{it:indepvars}]
[{cmd:if} {it:exp}]
[{cmd:in} {it:range}]
{cmd:,}
    [{cmdab:out:come}{cmd:(}{it:varlist}{cmd:)}
    {cmdab:p:score}{cmd:(}{it:varname}{cmd:)}
    {cmdab:n:eighbor}{cmd:(}{it:integer k}>1{cmd:)}
    {cmdab:cal:iper}{cmd:(}{it:real}{cmd:)}
    {cmdab:com:mon}
    {cmd:trim}{cmd:(}{it:real}{cmd:)}
    {cmd:odds}
    {cmd:index}
    {cmd:logit}
    {cmd:ties}
    {cmdab:nowarn:ings}
    {cmdab:qui:etly}
    {cmd:ate}]


{pstd}
{bf:Radius matching:}

{p 8 21 2}{cmdab:psmatch2}
{it:depvar}
[{it:indepvars}]
[{cmd:if} {it:exp}]
[{cmd:in} {it:range}]
{cmd:,}
    {cmdab:radius}
    {cmdab:cal:iper}{cmd:(}{it:real}{cmd:)}
    [{cmdab:out:come}{cmd:(}{it:varlist}{cmd:)}
    {cmdab:p:score}{cmd:(}{it:varname}{cmd:)}
    {cmdab:com:mon}
    {cmd:trim}{cmd:(}{it:real}{cmd:)}
    {cmd:odds}
    {cmd:index}
    {cmd:logit}
    {cmdab:qui:etly}
    {cmd:ate}]


{pstd}
{bf:Kernel matching:}

{p 8 21 2}{cmdab:psmatch2}
{it:depvar}
[{it:indepvars}]
[{cmd:if} {it:exp}]
[{cmd:in} {it:range}]
{cmd:,}
    {cmdab:kernel}
    [{cmdab:out:come}{cmd:(}{it:varlist}{cmd:)}
    {cmdab:k:erneltype}{cmd:(}{it:kernel_type}{cmd:)}
    {cmdab:p:score}{cmd:(}{it:varname}{cmd:)}
    {cmdab:bw:idth}{cmd:(}{it:real}{cmd:)}
    {cmdab:mahal:anobis}{cmd:(}{it:varlist}{cmd:)}
    {cmdab:com:mon}
    {cmd:trim}{cmd:(}{it:real}{cmd:)}
    {cmd:odds}
    {cmd:index}
    {cmd:logit}
    {cmdab:qui:etly}
    {cmd:ate}]


{pstd}
{bf:Local linear regression matching:}

{p 8 21 2}{cmdab:psmatch2}
{it:depvar}
[{it:indepvars}]
[{cmd:if} {it:exp}]
[{cmd:in} {it:range}]
{cmd:,}
    {cmdab:llr}
    {cmdab:out:come}{cmd:(}{it:varlist}{cmd:)}
    [{cmdab:k:erneltype}{cmd:(}{it:kernel_type}{cmd:)}
    {cmdab:p:score}{cmd:(}{it:varname}{cmd:)}
    {cmdab:bw:idth}{cmd:(}{it:real}{cmd:)}
    {cmdab:mahal:anobis}{cmd:(}{it:varlist}{cmd:)}
    {cmdab:com:mon}
    {cmd:trim}{cmd:(}{it:real}{cmd:)}
    {cmd:odds}
    {cmd:index}
    {cmd:logit}
    {cmdab:qui:etly}
    {cmd:ate}]

{phang}
{bf:Spline matching:}

{p 8 21 2}{cmdab:psmatch2}
{it:depvar}
[{it:indepvars}]
[{cmd:if} {it:exp}]
[{cmd:in} {it:range}]
{cmd:,}
    {cmd:spline}
    {cmdab:out:come}{cmd:(}{it:varlist}{cmd:)}
    [{cmdab:nk:nots(}{it:integer}{cmd:)}
    {cmdab:p:score}{cmd:(}{it:varname}{cmd:)}
    {cmdab:n:eighbor}{cmd:(}{it:integer}{cmd:)}
    {cmdab:cal:iper}{cmd:(}{it:real}{cmd:)}
    {cmdab:com:mon}
    {cmd:trim}{cmd:(}{it:real}{cmd:)}
    {cmd:odds}
    {cmd:index}
    {cmd:logit}
    {cmd:ties}
    {cmdab:nowarn:ings}
    {cmdab:qui:etly}
    {cmd:ate}]

{pstd}
{bf:Mahalanobis matching:}

{p 8 21 2}{cmdab:psmatch2}
{it:depvar}
[{cmd:if} {it:exp}]
[{cmd:in} {it:range}]
{cmd:,}
    {cmdab:mahal:anobis}{cmd:(}{it:varlist}{cmd:)}
    {cmdab:out:come}{cmd:(}{it:varlist}{cmd:)}
    {cmdab:ai}{cmd:(}{it:integer}{cmd:)}
    [{cmdab:pop:ulation}
    {cmdab:altv:ariance}
    {cmdab:k:ernel}{cmd:(}{it:kernel_type}{cmd:)}
    {cmd:llr}
    {cmdab:bw:idth}{cmd:(}{it:real}{cmd:)}
    {cmdab:cal:iper}{cmd:(}{it:real}{cmd:)}
    {cmd:w}{cmd:(}{it:matrix}{cmd:)}
    {cmd:ate}]


{pstd}
{cmd:psmatch2} creates a number of variables for the convenience of the user:

{pmore}
{inp:_treated} is a variable that equals 0 for control observations and 1 for treatment observations.

{pmore}
{inp:_support} is an indicator variable with equals 1 if the observation is on the common support
and 0 if the observatio is off the support.

{pmore}
{inp:_pscore} is the estimated propensity score or a copy of the one provided by {cmdab:p:score()}.

{pmore}
{inp:_{it:outcome_variable}} for every treatment observation stores the value of the matched outcome.

{pmore}
{inp:_weight}. For nearest neighbor matching, it holds the frequency with which the
observation is used as a match; with option {cmd:ties} and k-nearest neighbors matching it holds
the normalized weight; for kernel matching, and llr matching with a weight other than
stata's tricube, it stores the overall weight given to the matched observation. When estimating att only
_weight = 1 for the treated.

{pmore}
{inp:_id} In the case of one-to-one and nearest-neighbors matching, a new identifier created for all observations.

{pmore}
{inp:_n{it:k}} In the case of one-to-one and nearest-neighbors matching, for every treatment observation,
it stores the observation number of the k-th matched control observation. Do not forget to sort by
{it:_id} if you want to use the observation number (id) of for example the 1st nearest neighbor as in

	{cmd:sort _id}
	{cmd:g x_of_match = x[_n1]}

{pmore}
{inp:_nn} In the case of nearest-neighbors matching, for every treatment observation,
it stores the number of matched control observations.

{title:Options}

{phang}
{cmdab:out:come}{cmd:(}{it:varlist}{cmd:)} the outcome variable(s). 
When evaluating multiple outcomes psmatch2 reduces to the min common number of observations 
with non-missing values on ALL outcomes, because otherwise the matching weigths will not sum 
to the right number. If you have multiple outcomes with widely differing missing values 
you may wish to run psmatch2 separately for each of the outcomes.

{phang}
{cmdab:ate} with this option the average treatment effect (ate) and average treatment
effect on the untreated (atu) are reported in addition to the average treatment effect on the treated (att).
The estimates are returned in {it:r(ate)}, {it:r(atu)} and {it:r(att)} respectively, see above.

{phang}
{cmdab:ai}{cmd:(}{it:integer}{cmd:)}
calculate the heteroskedasticity-consistent analytical standard errors
proposed by Abadie and Imbens (2006) by specifying the number of neighbors to be used
to calculate the conditional variance (their formula (14)). With option {cmdab:altv:ariance} one can
specify to use the estimator of Abadie et al. (2004) instead.

{pmore}
Note that this is appropriate for nearest-neighbor matching on the X's, i.e. Mahalanobis-metric matching ({cmd:mahal()}) not augmented with the propensity score.

{pmore}
By default the sample variance is calculated (population variance can be calculated using option {cmdab:pop:ulation}).

{phang}
{cmdab:pop:ulation}
When using {cmdab:ai}{cmd:(}{it:integer}{cmd:)}, calculate the population variance rather than the sample variance (default).

{phang}
{cmdab:altv:ariance}
When using {cmdab:ai}{cmd:(}{it:integer}{cmd:)}, calculate the conditional variance using the expression in Abadie et al. (2004, p.303).

{title:Options: Estimation of the propensity score}

{phang}
{cmdab:p:score}{cmd:(}{it:varname}{cmd:)} specifies the variable to be used as propensity score.

{pstd}
Alternatively, {it:indepvars} need to be specified to allow the program to estimate the propensity score on them.
In this case:

{phang}
{cmd:logit} use logit instead of the default probit to estimate the propensity score.

{phang}
{cmdab:qui:etly} do not print output of propensity score estimation.

{phang}
{cmd:odds} match on the logarithm of the odds ratio of the propensity score (stored in _pscore).

{phang}
{cmd:index} use the latent variable index instead of the probability.

{phang}
{cmdab:nowarn:ings} do not test for control observations with duplicate propensity score values.


{title:Options: Imposition of common support}

{phang}
{cmdab:com:mon} imposes a common support by dropping treatment observations
whose pscore is higher than the maximum or less than the minimum pscore of the controls.

{phang}
{cmd:trim(}{it:integer}{cmdab:)} imposes common support by dropping # percent of the treatment
observations at which the pscore density of the control observations is the lowest.

{title:Options: Choice of matching estimator}

{phang}
{cmdab:n:eighbor}{cmd:(}{it:integer}{cmd:)} number of neighbors used to calculate the matched outcome.
Defaults to 1. Default matching method is single nearest-neighbour (without caliper).

{phang}
{cmdab:norep:lacement} perform 1-to-1 matching without replacement. Nearest neigbor propensity score matching only.

{phang}
{cmdab:desc:ending} perform 1-to-1 matching without replacement in descending order. Nearest neighbor propensity score matching only.

{phang}
{cmd:ties} not only match nearest neighbor but also other controls with identical (tied) pscores.

{phang}
{cmd:radius} perform radius matching within the specified radius given by {cmd:caliper}.

{phang}
{cmdab:cal:iper}{cmd:(}{it:real}{cmd:)} value for maximum distance of controls.
Use to perform nearest neighbor(s) within caliper, radius matching and Mahalanobis 1-to-1 matching.

{phang}
{cmdab:k:ernel} perform kernel matching.

{phang}
{cmdab:k:erneltype}{cmd:(}{it:kernel_type}{cmd:)} specifies the type of kernel:

{p 8 8 2}{inp:normal} the gaussian kernel.

{p 8 8 2}{inp:biweight} the biweight kernel.

{p 8 8 2}{inp:epan} the epanechnikov kernel (Default).

{p 8 8 2}{inp:uniform} the uniform kernel.

{p 8 8 2}{inp:tricube} the tricube kernel.

{phang}
{cmd:llr} llr use local linear regression matching instead of kernel matching.

{phang}
{cmdab:bw:idth}{cmd:(}{it:real}{cmd:)} the bandwidth for kernel and local linear regression matching.
Default bandwidth is 0.06, except when doing local linear regression with the Epanechnikov kernel when the default bandwidth is the rule-of-thumb bandwidth of {cmd:lpoly}.

{phang}
{cmdab:mahal:anobis}{cmd:(}{it:varlist}{cmd:)} perform Mahalanobis-metric matching on {it: varlist}.

{phang}
{cmd:w}{cmd:(}{it:matrix}{cmd:)} specify alternative weighting matrix. Mahalanobis-metric matching
becomes matching on a quadratic metric with the specified weighting matrix.

{phang}
{cmd:spline} performs 'spline-smoothing matching' by first fitting a natural cubic
    spline on pscore (or on the result from estimate) to outcome.
    The matched values are stored in the new variable, _s_outcomevar.  (It requires the
    {cmd:spline} programme, which for stata7 needs to be downloaded by typing: net install snp7_1.)

{phang}
{cmdab:nk:nots(}{it:integer}{cmd:)} specifies the number of interior knots for spline smoothing. Default is
    the fourth root of the number of comparison units.

{title:Examples}

    {inp: . psmatch2 training age gender, kernel k(biweight) out(wage)}
    {inp: . psmatch2 training age gender, n(5) logit}
    {inp: . psmatch2 training age gender, out(wage)}
    {inp: . bs "psmatch2 training age gender, out(wage)" "r(att)"}

{title:Also see}

{pstd}
The commands {help pstest}, {help psgraph}.


{title:Thanks for citing {cmd:psmatch2} as follows}

{pstd}
E. Leuven and B. Sianesi. (2003). "PSMATCH2: Stata module to perform full Mahalanobis and propensity score matching, common support graphing, and covariate imbalance testing".
http://ideas.repec.org/c/boc/bocode/s432001.html. This version INSERT_VERSION_HERE.

where you can check your version as follows:

    {inp: . which psmatch2}


{title:Disclaimer}

{pstd}
THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM IS WITH YOU. SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING, REPAIR OR CORRECTION.

{pstd}
IN NO EVENT WILL THE COPYRIGHT HOLDERS OR THEIR EMPLOYERS, OR ANY OTHER PARTY WHO MAY MODIFY AND/OR REDISTRIBUTE THIS SOFTWARE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS), EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.

{title:Background Reading}

{p 0 2}Abadie, A., Drukker, D., Herr, J. L., & Imbens, G. W. (2004). "Implementing matching estimators for average treatment effects in Stata", {it:Stata journal 4}, 290-311.

{p 0 2}Abadie A. and Imbens, G. (2006), "Large sample properties of matching estimators for average treatment effects", {it:Econometrica 74}(1), 235-267.

{p 0 2}Cochran, W. and Rubin, D.B. (1973), "Controlling Bias in Observational Studies", {it:Sankyha 35}, 417-446.

{p 0 2}Dehejia, R.H and Wahba, S. (1999), "Causal Effects in Non-Experimental Studies: Re-Evaluating the Evaluation of Training Programmes", {it:Journal of the American Statistical Association 94}, 1053-1062.

{p 0 2}Heckman, J.J., Ichimura, H. and Todd, P.E. (1997), "Matching As An Econometric Evaluation Estimator: Evidence from Evaluating a Job Training Programme", {it:Review of Economic Studies 64}, 605-654.

{p 0 2}Heckman, J.J., Ichimura, H. and Todd, P.E. (1998), "Matching as an Econometric Evaluation Estimator", {it:Review of Economic Studies 65}, 261-294.

{p 0 2}Heckman, J.J., Ichimura, H., Smith, J.A. and Todd, P. (1998), "Characterising Selection Bias Using Experimental Data", {it:Econometrica 66}, 5.

{p 0 2}Heckman, J.J., LaLonde, R.J., Smith, J.A. (1998), "The Economics and Econometrics of Active Labour Market Programmes", in Ashenfelter, O. and Card, D. (eds.), {it:The Handbook of Labour Economics Vol. 3A}.

{p 0 2}Imbens, G. (2000), "The Role of Propensity Score in Estimating Dose-Response Functions", {it:Biometrika 87(3)}, 706-710.

{p 0 2}Lechner, M. (2001), Identification and Estimation of Causal Effects of Multiple Treatments under the Conditional Independence Assumption, in: Lechner, M., Pfeiffer, F. (eds), {it:Econometric Evaluation of Labour Market Policies}, Heidelberg: Physica/Springer, p. 43-58.

{p 0 2}Rosenbaum, P.R. and Rubin, D.B. (1983), "The Central Role of the Propensity Score in Observational Studies for Causal Effects", {it:Biometrika 70}, 1, 41-55.

{p 0 2}Rosenbaum, P.R. and Rubin, D.B. (1985), "Constructing a Control Group Using Multivariate Matched Sampling Methods that Incorporate the Propensity Score", {it:The American Statistician 39(1)}, 33-38.

{p 0 2}Rubin, D.B. (1974), "Estimating Causal Effects of Treatments in Randomised and Non-Randomised Studies", {it:Journal of Educational Psychology 66}, 688-701.

{p 0 2}Rubin, D.B. (1980), "Bias Reduction Using Mahalanobis-Metric Matching", {it:Biometrics 36}, 293-298.

{title:Author}

{pstd}
Edwin Leuven, University of Oslo. If you observe any problems {browse "mailto:e.leuven@gmail.com"}.

{pstd}
Barbara Sianesi, Institute for Fiscal Studies, London, UK.

