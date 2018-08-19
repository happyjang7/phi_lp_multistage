# PhiDivergence defines a phi-divergence for use in robust optimization
# Detailed explanation goes here
import numpy as np
from scipy.optimize import fsolve
from scipy.stats import chi2
import cplex
class set(object):
    def __init__(self, inDivergence):
        lsts=["burg", "kl", "chi2", "mchi2", "hellinger"]
        if not inDivergence in lsts:
            raise ValueError('inDivergence should be in "%s"' % (lsts))
        else:
            self.divergence = inDivergence
            self.computationLimit = np.inf

    def func(self,t):
        if self.divergence == "burg":
            return -np.log(t) + t - 1
        elif self.divergence == "kl":
            return t*np.log(np.maximum(t, np.ﬁnfo(np.ﬂoat64).tiny)) - t + 1
        elif self.divergence == "chi2":
            return (t-1)**2/np.abs(t)
        elif self.divergence == "mchi2":
            return (t-1)**2
        elif self.divergence == "hellinger":
            return (np.sqrt(t)-1)**2

    def conjugate(self, s):
        if self.divergence == "burg":
            return -np.log(1-s)
        elif self.divergence == "kl":
            return np.exp(s) - 1
        elif self.divergence == "chi2":
            return 2 - 2*np.sqrt(1-s)
        elif self.divergence == "mchi2":
            return (-1)*(s < -2) + (np.maximum(s, -2)+np.maximum(s,-2)**2/4)*(s >= -2)
        elif self.divergence == "hellinger":
            return np.maximum(s,-np.ﬁnfo(np.ﬂoat64).max)/(1-np.maximum(s,-np.ﬁnfo(np.ﬂoat64).max))

    def conjugateDerivative(self,s):
        if self.divergence == "burg":
            return 1/(1-s)
        elif self.divergence == "kl":
            return np.exp(s)
        elif self.divergence == "chi2":
            return 1/np.sqrt(1-s)
        elif self.divergence == "mchi2":
            return (1+np.maximum(s, -2)/2)*(s >= -2)
        elif self.divergence == "hellinger":
            return 1/((s-1)**2)

    def phi2Derivative(self,t):
        if self.divergence == "burg":
            return 1/(t**2)
        elif self.divergence == "kl":
            return 1/t
        elif self.divergence == "chi2":
            return 2/np.power(t,3)
        elif self.divergence == "mchi2":
            return 2
        elif self.divergence == "hellinger":
            return 1/(2*np.power(t,3/2))

    def limit(self):
        if self.divergence == "burg":
            return np.array([1])
        elif self.divergence == "kl":
            return np.inf
        elif self.divergence == "chi2":
            return np.array([1])
        elif self.divergence == "mchi2":
            return np.inf
        elif self.divergence == "hellinger":
            return np.array([1])

    def Contribution(self, inNumer, inDenom ):
        zD = inDenom == 0
        zN = zD & (inNumer == 0)
        outVal = inDenom * self.func(inNumer/inDenom)
        outVal[zD] = inNumer[zD] * self.limit()
        outVal[zN] = 0
        return outVal

    def Conjugate(self, inS):
        outVal = self.conjugate(inS)
        if not sum(np.where(inS > self.limit())[0])==0:
            outVal[np.where(inS > self.limit())[0]] = np.inf
        return outVal

    def ConjugateDerivative(self, inS):
        outDeriv = self.conjugateDerivative(inS)
        if not sum(np.where(inS > self.limit())[0])==0:
            outDeriv[np.where(inS > self.limit())[0]] = np.nan
        outDeriv[inS > self.limit()] = np.nan
        return outDeriv

    def SecondDerivativeAt1(self):
        outDeriv = self.phi2Derivative(1)
        return outDeriv

    def SetComputationLimit(self, inDistr, inRho):
            assert(all(inDistr >= 0))
            if not np.isinf(self.limit()):
                return
            distr = inDistr/np.sum(inDistr)

            def function_t(t, data):
                return self.func(t)-data
            data = inRho/np.min(distr[distr>0])
            t = fsolve(function_t , 2, args=data)

            def function_s(s,data):
                return self.conjugateDerivative(s)-data
            data1 = t
            s = fsolve(function_s, 1, args=data1)
            self.computationLimit = s

    def Rho(self, alpha, obs):
        rho = self.SecondDerivativeAt1() / (2*np.sum(obs)) * chi2.ppf(1-alpha, obs.size - 1)
        return rho

    def Alpha(self, rho, obs):
        alpha = 1-chi2.cdf(2*np.sum(obs)/self.SecondDerivativeAt1() * rho, obs.size -1)
        return alpha


if __name__ == "__main__":
    phi = set("mchi2")
    alpha= 0.05
    obs =np.array([1,1,1,1,1,1])
    rho = phi.Rho(alpha,obs)



