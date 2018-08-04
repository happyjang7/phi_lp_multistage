*** Order is important because of observations ***

1. make_matrix_for_water_large_FULL.m
  => Generate input files for python
    input: lpfile = 'lp_6144.mat'
    output: savefile1 = fisrt_second_third_stage data
            savefile2,savefile3,savefile4 = fourth_stage data
    dependency : make_full_rhs.m
                => generate rhs for all GPCD
                dependency :  generate_rhs.m
                              => generate rhs for a given GPCD
                              dependency: load('empty_rhs.mat')
                                          load('projected_Population.mat')
                                          load('projected_GPCD.mat')
                                          load('water_allocation.mat')
