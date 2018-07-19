import main

data = "water20.mat"


phi = 'kl'
# main.run(phi, 0.01, data, './result/' +data + "_" + phi + "_" +'result1.txt', './result/'  +data + "_" + phi + "_" + 'result1.png')
# main.run(phi, 0.05, data, './result/' +data + "_" + phi + "_" + 'result2.txt', './result/'  +data + "_" + phi + "_" + 'result2.png')
# main.run(phi,  0.1, data, './result/' +data + "_" + phi + "_" + 'result3.txt', './result/'  +data + "_" + phi + "_" + 'result3.png')

phi = 'mchi2'
main.run(phi, 0.01, data, './result/' +data + "_" + phi + "_" +'result1.txt', './result/'  +data + "_" + phi + "_" + 'result1.png')
main.run(phi, 0.05, data, './result/' +data + "_" + phi + "_" + 'result2.txt', './result/'  +data + "_" + phi + "_" + 'result2.png')
main.run(phi,  0.1, data, './result/' +data + "_" + phi + "_" + 'result3.txt', './result/'  +data + "_" + phi + "_" + 'result3.png')

phi = 'burg'
# main.run(phi, 0.01, data, './result/' +data + "_" + phi + "_" +'result1.txt', './result/'  +data + "_" + phi + "_" + 'result1.png')
# main.run(phi, 0.05, data, './result/' +data + "_" + phi + "_" + 'result2.txt', './result/'  +data + "_" + phi + "_" + 'result2.png')
main.run(phi,  0.1, data, './result/' +data + "_" + phi + "_" + 'result3.txt', './result/'  +data + "_" + phi + "_" + 'result3.png')
