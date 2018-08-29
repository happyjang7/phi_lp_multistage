import numpy as np

class set(object):
    def __init__(self, inLPModel):
        self.lpModel = inLPModel
        self.numVariables =self.lpModel['obj'].size
        self.Reset()

    def Reset(self):
        self.solution = np.zeros_like(self.lpModel['obj'],dtype=float)
        self.fval = np.float64(0)
        self.pi = np.zeros_like(self.lpModel['rhs'],dtype=float)


    def SetFval(self, inFval):
        self.fval = np.float64(inFval)
    def Fval(self):
        return self.fval


    def SetPi(self, inPi):
        self.pi = np.array(inPi,dtype=float)
    def Pi(self):
        return self.pi


    def SetX(self, inX):
        if np.array(inX).size != self.numVariables:
            raise Exception('X has size '+str(np.array(inX).size)+', should be '+str(self.numVariables))
        self.solution = np.array(inX,dtype=float)
    def X(self):
        return self.solution