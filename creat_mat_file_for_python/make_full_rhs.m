
function [second_rhs, third_rhs, fourth_rhs] = make_full_rhs()
for GPCD=1:48
[second_tmp{GPCD}, third_tmp{GPCD}, fourth_tmp{GPCD}] = generate_rhs(GPCD);
end

second_rhs = cell(0);
third_rhs  = cell(0);
fourth_rhs  = cell(0);
% for i=1:48
%     second_rhs = vertcat(second_rhs,second_tmp{i});
%     third_rhs  = vertcat(third_rhs,third_tmp{i});
%     fourth_rhs  = vertcat(fourth_rhs,fourth_tmp{i});
% end

for GPCD = 1:48
    for i=1:8
        second_rhs{i+8*(GPCD-1),1} = second_tmp{1,GPCD}{i,1};
        for j=1:8
            third_rhs{i+8*(GPCD-1),j} = third_tmp{1,GPCD}{i,j};
            for k=1:8
                fourth_rhs{i+8*(GPCD-1),j,k} = fourth_tmp{1,GPCD}{i,j,k};
            end
        end
    end
end


