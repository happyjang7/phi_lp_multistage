import main

data = "first_second_third_37.mat"
data1 = "fourth1_37.mat"
data2 = "fourth2_37.mat"
data3 = "fourth3_37.mat"
phi = 'burg'
# main.run(phi,  0.1, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result1.txt', './result/'  +data + "_" + phi + "_" + 'result1.png')
main.run(phi,  0.05, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result2.txt', './result/'  +data + "_" + phi + "_" + 'result2.png')
# main.run(phi,  0.01, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result3.txt', './result/'  +data + "_" + phi + "_" + 'result3.png')

