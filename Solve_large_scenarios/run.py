import main

data = "first_second_third.mat"
data1 = "fourth1.mat"
data2 = "fourth2.mat"
data3 = "fourth3.mat"
phi = 'burg'
main.run(phi,  0.05, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result.txt', './result/'  +data + "_" + phi + "_" + 'result.png')
# phi = 'kl'
# main.run(phi,  0.05, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result.txt', './result/'  +data + "_" + phi + "_" + 'result.png')
# phi = 'mchi2'
# main.run(phi,  0.01, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result.txt', './result/'  +data + "_" + phi + "_" + 'result.png')
