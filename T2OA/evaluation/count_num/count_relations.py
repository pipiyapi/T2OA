import os
import pandas as pd
cur_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(cur_dir)
pparent_dir = os.path.dirname(parent_dir)

with open(pparent_dir+'/logs/log_2025-04-10_13-12-45.txt', 'r', encoding='gbk') as file:
    lines = file.readlines()
    all_relation=[]
    is_a_result=[]
    for line in lines:
        if "【llm_relation_disnose】当前剩余is_a_result:" in line:
            all_relation.append(line)
    is_a_result.append(eval(all_relation[0].split("当前剩余is_a_result:")[1].strip()))
    for i in range(len(all_relation)):
        if i==len(all_relation)-1:
            break
        if "当前剩余is_a_result:[]" in all_relation[i] and all_relation[i+1].split("当前剩余is_a_result:")[1].strip()!="[]":
            v=all_relation[i + 1].split("当前剩余is_a_result:")[1].strip()
            is_a_result.append(eval(v))
print("------------------")
with open(pparent_dir+'/logs/log_2025-04-10_13-12-45.txt', 'r', encoding='gbk') as file:
    lines = file.readlines()
    all_relation=[]
    h_result=[]
    for line in lines:
        if "【llm_relation_disnose】当前剩余hypernym_generation_result:" in line:
            all_relation.append(line)
    h_result.append(eval(all_relation[0].split("当前剩余hypernym_generation_result:")[1].strip()))
    for i in range(len(all_relation)):
        if i==len(all_relation)-1:
            break
        if "当前剩余hypernym_generation_result:[]" in all_relation[i] and all_relation[i+1].split("当前剩余hypernym_generation_result:")[1].strip()!="[]":
            v=all_relation[i + 1].split("当前剩余hypernym_generation_result:")[1].strip()
            h_result.append(eval(v))
with open(pparent_dir+'/logs/log_2025-04-10_13-12-45.txt', 'r', encoding='gbk') as file:
    lines = file.readlines()
    not_handle=[]
    for line in lines:
        if "这些实体类型完全没有任何关系，完全是无关概念" in line and "【tool_not_handle】" in line:
            v=line.split("【tool_not_handle】")[1].split("这些实体类型完全没有任何关系，完全是无关概念，不进行任何操作")[0].strip()
            not_handle.append(eval(v))
print(is_a_result)
print(h_result)
turn_is,turn_h={},{}
turn_is_all,turn_h_all={},{}
for i in range(len(is_a_result)):
    turn_is[i] = 0
for i in range(len(h_result)):
    turn_h[i] = 0
for i in range(len(h_result)):
    turn_is_all[i] = 0
for i in range(len(h_result)):
    turn_h_all[i] = 0
for i in range(len(is_a_result)):
    for j in not_handle:
        if j in is_a_result[i]:
            turn_is[i]+=1
        if j in h_result[i]:
            turn_h[i]+=1
for i in range(len(is_a_result)):
    turn_is_all[i]=len(is_a_result[i])
for i in range(len(h_result)):
    turn_h_all[i]=len(h_result[i])
print(turn_is)
print(turn_h)
print(turn_is_all)
print(turn_h_all)
df = pd.DataFrame([turn_is, turn_h,turn_is_all,turn_h_all],
                 index=['is_a关系生成失败次数', 'hypernym_generation关系生成失败次数','is_a总次数','hypernym_generation总次数'],
                 columns=turn_is.keys())
df.to_excel('关系结果统计.xlsx', sheet_name='关系统计')
