from neo4j_database.cypher import get_all_triples
import pandas as pd
import json
def get_relation_result():
    relation_list=get_all_triples()
    df = pd.DataFrame({"relation_list":relation_list})
    # 将DataFrame写入Excel文件
    df.to_excel("relation_results1.xlsx", index=False)
    print("消歧结果已保存到 relation_results1.xlsx")
def get_samelevel_relation_result():
    relation_list=get_all_triples()
    father_list=[]
    for i in relation_list:
        if i[2] not in father_list:
            father_list.append(i[2])
    rel_dict={}
    for j in father_list:
        son_list=[]
        for k in relation_list:
            if k[2]==j:
                son_list.append(k[0])
        rel_dict[j]=son_list
    pair_list=[]
    f_list=[]
    count=[]
    df1 = pd.read_excel('relation_results.xlsx')  # 替换为你的文件路径
    # 获取第二列等于1的行，然后提取这些行的第一列值
    result_list = df1[df1.iloc[:, 1] == 1].iloc[:, 0].tolist()
    result_1=[]
    entity_list=[]
    with open("dict_type_entity.json", 'r', encoding='utf-8') as f:
        data_entity = json.load(f)
    for i in result_list:
        result_1.append(i.split("'")[1])
    for key,value in rel_dict.items():
        if len(value)!=1:
            for j in value:
                if j not in result_1:
                    value.remove(j)
            for o in range(len(value)):
                for p in range(o+1,len(value)):
                    pair_list.append([value[o],value[p]])
                    f_list.append(key)
                    entity_list.append([data_entity.get(value[o],"无"),data_entity.get(value[p],"无")])
    df = pd.DataFrame({"pair_list": pair_list,"f_list":f_list,"entity_list":entity_list})
    # 将DataFrame写入Excel文件
    df.to_excel("relation_samelevel_results.xlsx", index=False)
    print("消歧结果已保存到 relation_samelevel_results.xlsx")

if __name__ == "__main__":
    # get_relation_result()
    get_samelevel_relation_result()