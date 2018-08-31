import pickle
import numpy as np

with open('result2.pkl', 'rb') as f:
    data = pickle.load(f)
print(data[1][0].candidateSolution.X())
