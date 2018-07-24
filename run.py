import main

data = "water20.mat"
phi = 'burg'
main.run(phi,  0.1, data, './result/' +data + "_" + phi + "_" + 'result3.txt', './result/'  +data + "_" + phi + "_" + 'result3.png')


data = "water10.mat"
phi = 'burg'
main.run(phi,  0.1, data, './result/' +data + "_" + phi + "_" + 'result3.txt', './result/'  +data + "_" + phi + "_" + 'result3.png')

