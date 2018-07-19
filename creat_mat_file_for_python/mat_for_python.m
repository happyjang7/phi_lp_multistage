function mat_for_python(lp_file, obs, savefile)
load(lp_file)
numStages = lp.numStages;
numScenarios = lp.numScenarios;
obs = obs;

first_obj = lp.c;
first_lb = lp.l';
first_ub = lp.u';
first_rhs = lp.b';
first_A = lp.A;

second_col = length(lp.q{1});
second_row = length(lp.d{1});

second_obj = cellfun(@(x) reshape(x,1,second_col),lp.q,'un',0);
second_lb = cellfun(@(x) reshape(x,1,second_col),lp.l2,'un',0);
second_ub = cellfun(@(x) reshape(x,1,second_col),lp.u2,'un',0);
second_rhs = cellfun(@(x) reshape(x,1,second_row),lp.d,'un',0);
second_D = lp.D;
second_B = lp.B;

save(savefile,'numStages', 'numScenarios', 'obs','first_obj','first_lb','first_ub','first_rhs','first_A','second_obj','second_lb','second_ub','second_rhs','second_D','second_B')