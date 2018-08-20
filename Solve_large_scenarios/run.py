import main

# for i in range(1,49):
#     data = "first_second_third_"+str(i)+".mat"
#     data1 = "fourth1_"+str(i)+".mat"
#     data2 = "fourth2_"+str(i)+".mat"
#     data3 = "fourth3_"+str(i)+".mat"
#     phi = 'burg'
#     main.run(phi,  0.1, data,data1,data2,data3, './result/result'+str(i)+'.txt', './result/result.png')


data = "first_second_third.mat"
data1 = "fourth1.mat"
data2 = "fourth2.mat"
data3 = "fourth3.mat"
phi = 'burg'
main.run(phi,  0.1, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result1.txt', './result/'  +data + "_" + phi + "_" + 'result1.png')
main.run(phi,  0.05, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result2.txt', './result/'  +data + "_" + phi + "_" + 'result2.png')
main.run(phi,  0.01, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result3.txt', './result/'  +data + "_" + phi + "_" + 'result3.png')

phi = 'kl'
main.run(phi,  0.1, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result1.txt', './result/'  +data + "_" + phi + "_" + 'result1.png')
main.run(phi,  0.05, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result2.txt', './result/'  +data + "_" + phi + "_" + 'result2.png')
main.run(phi,  0.01, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result3.txt', './result/'  +data + "_" + phi + "_" + 'result3.png')

phi = 'mchi2'
main.run(phi,  0.1, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result1.txt', './result/'  +data + "_" + phi + "_" + 'result1.png')
main.run(phi,  0.05, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result2.txt', './result/'  +data + "_" + phi + "_" + 'result2.png')
main.run(phi,  0.01, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result3.txt', './result/'  +data + "_" + phi + "_" + 'result3.png')
