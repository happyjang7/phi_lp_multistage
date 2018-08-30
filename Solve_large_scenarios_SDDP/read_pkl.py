import pickle

with open('results.pkl', 'rb') as f:
    data = pickle.load(f)
print(data[1][0].pWorst)

