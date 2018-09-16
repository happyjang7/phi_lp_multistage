import main

for n in [8, 24, 40, 56, 72, 88, 104, 120, 136, 152, 168, 184, 200, 216, 232, 248, 264, 280, 296, 312, 328, 344, 360, 376]:
    main.run('mchi2', 0.05, 'water' + str(n) + '_0.mat', 'water' + str(n) + '_1.mat', 'water' + str(n) + '_2.mat',
        'water' + str(n) + '_3.mat', './result/mchi2_water' + str(n) + '_decomp.txt',
        './result/water.pkl', './result/water.png')
main.run('mchi2', 0.05, 'NI_first_second_third.mat', 'NI_fourth1.mat', 'NI_fourth2.mat', 'NI_fourth3.mat',
    './result/mchi2_water' + str(384) + '_decomp.txt',
    './result/water.pkl', './result/water.png')