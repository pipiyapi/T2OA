import pandas as pd
import json
from neo4j_database.cypher import search_all_nodes
def get_disambiguation_results():
    with open("disambiguation_record.txt", 'r', encoding='utf-8') as f:
        data = f.readlines()
    dis_list=[]
    for line in data:
        line = line.strip()  # 去除首尾空白字符（包括换行符）
        if not line.endswith("无"):
            dis_list.append(line)
    with open("dict_type_entity.json", 'r', encoding='utf-8') as f:
        data_entity = json.load(f)
    entity_list=[]
    for line in dis_list:
        split_line=line.split("'")
        len(split_line)
        one_entity = []
        for i in range(1,len(split_line),2):
            one_entity.append(data_entity[split_line[i]])
        entity_list.append(one_entity)


    df = pd.DataFrame({"消歧对象":dis_list,"对应实体":entity_list})

    # 将DataFrame写入Excel文件
    df.to_excel("disambiguation_results1.xlsx", index=False)
    print("消歧结果已保存到 disambiguation_results1.xlsx")
def get_disambiguation_wu():
    with open("disambiguation_record.txt", 'r', encoding='utf-8') as f:
        data = f.readlines()
    dis_list=[]
    for line in data:
        line = line.strip()  # 去除首尾空白字符（包括换行符）
        if line.endswith("无"):
            if line not in dis_list:
                dis_list.append(line)
    with open("dict_type_entity.json", 'r', encoding='utf-8') as f:
        data_entity = json.load(f)
    entity_list=[]
    for line in dis_list:
        split_line=line.split("'")
        len(split_line)
        one_entity = []
        for i in range(1,len(split_line),2):
            one_entity.append(data_entity[split_line[i]])
        if one_entity not in entity_list:
            entity_list.append(one_entity)


    df = pd.DataFrame({"消歧对象":dis_list,"对应实体":entity_list})

    # 将DataFrame写入Excel文件
    df.to_excel("disambiguation_wu.xlsx", index=False)
    print("消歧结果已保存到 disambiguation_wu.xlsx")
if __name__ == "__main__":
    get_disambiguation_wu()
