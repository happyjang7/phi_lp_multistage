import main

for i in range(10,11):
    data = "first_second_third_news"+str(i)+".mat"
    data1 = "fourth1_news"+str(i)+".mat"
    data2 = "fourth2_news"+str(i)+".mat"
    data3 = "fourth3_news"+str(i)+".mat"
    phi = 'burg'
    main.run(phi,  0.1, data,data1,data2,data3, './result/result'+str(i)+'.txt', './result/result.png')


# data = "first_second_third_1.mat"
# data1 = "fourth1_1.mat"
# data2 = "fourth2_1.mat"
# data3 = "fourth3_1.mat"
# phi = 'burg'
#
# main.run(phi,  0.1, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result1.txt', './result/'  +data + "_" + phi + "_" + 'result1.png')
# main.run(phi,  0.05, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result2.txt', './result/'  +data + "_" + phi + "_" + 'result2.png')
# main.run(phi,  0.01, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result3.txt', './result/'  +data + "_" + phi + "_" + 'result3.png')
#
#
#
# data = "WWTP_first_second_third.mat"
# data1 = "WWTP_fourth1.mat"
# data2 = "WWTP_fourth2.mat"
# data3 = "WWTP_fourth3.mat"
# phi = 'burg'
#
# main.run(phi,  0.1, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result1.txt', './result/'  +data + "_" + phi + "_" + 'result1.png')
# main.run(phi,  0.05, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result2.txt', './result/'  +data + "_" + phi + "_" + 'result2.png')
# main.run(phi,  0.01, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result3.txt', './result/'  +data + "_" + phi + "_" + 'result3.png')
#
#
# data = "IPR_first_second_third.mat"
# data1 = "IPR_fourth1.mat"
# data2 = "IPR_fourth2.mat"
# data3 = "IPR_fourth3.mat"
# phi = 'burg'
#
# main.run(phi,  0.1, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result1.txt', './result/'  +data + "_" + phi + "_" + 'result1.png')
# main.run(phi,  0.05, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result2.txt', './result/'  +data + "_" + phi + "_" + 'result2.png')
# main.run(phi,  0.01, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result3.txt', './result/'  +data + "_" + phi + "_" + 'result3.png')



# #
# phi = 'kl'
# main.run(phi,  0.1, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result1.txt', './result/'  +data + "_" + phi + "_" + 'result1.png')
# main.run(phi,  0.05, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result2.txt', './result/'  +data + "_" + phi + "_" + 'result2.png')
# main.run(phi,  0.01, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result3.txt', './result/'  +data + "_" + phi + "_" + 'result3.png')
#
# phi = 'mchi2'
# main.run(phi,  0.1, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result1.txt', './result/'  +data + "_" + phi + "_" + 'result1.png')
# main.run(phi,  0.05, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result2.txt', './result/'  +data + "_" + phi + "_" + 'result2.png')
# main.run(phi,  0.01, data,data1,data2,data3, './result/' +data + "_" + phi + "_" + 'result3.txt', './result/'  +data + "_" + phi + "_" + 'result3.png')
