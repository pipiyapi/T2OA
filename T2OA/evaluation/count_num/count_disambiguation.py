import os
import pandas as pd
cur_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(cur_dir)
pparent_dir = os.path.dirname(parent_dir)

with open(pparent_dir+'/logs/log_2025-04-10_13-12-45.txt', 'r', encoding='gbk') as file:
    lines = file.readlines()
    tag=1
    turn_list=[]
    turn_num=[]
    for line in lines:
        if "当前剩余disambiguation_result:[]" in line:
            tag=1
        elif "当前剩余disambiguation_result:" in line and tag==1:
            l=line.split(":")[3]
            turn_list.append(l)
            turn_num.append(len(eval(l)))
            # print(l)
            # print(len(eval(l)))
            tag=0
    print(sum(turn_num))
    # print(len(turn_list))
with open(parent_dir+'/disambiguation_evaluation/disambiguation_record.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    turn_dict={}
    turn_fail={}
    for i in range(len(turn_list)):
        turn_dict[i]=0
    for i in range(len(turn_list)):
        turn_fail[i]=0
    nu=0
    for j in turn_num:
        temp=lines[:j]
        lines=lines[j:]
        for k in temp:
            if k.split("->")[1].strip()!="无":
                turn_dict[nu]+=1
            else:
                turn_fail[nu]+=1
        # print(j)
        # print(temp)
        # print(lines)
        nu+=1
    print(f"消歧成功轮次{turn_dict}")
    print(f"消歧失败轮次{turn_fail}")
    print(f"消歧成功总次数{sum(turn_dict.values())}")
    print(f"消歧失败总次数{sum(turn_fail.values())}")
df = pd.DataFrame([turn_dict, turn_fail],
                 index=['消歧成功次数', '消歧失败次数'],
                 columns=turn_dict.keys())

# 转置表格（如果需要轮次作为行而不是列）
# df = df.T

print(df)
df.to_excel('消歧结果统计.xlsx', sheet_name='消歧统计')
