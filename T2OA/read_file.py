import json
import os
cur_path= os.getcwd()
data_path=cur_path+"/data"
def file_initialize():
    with open(data_path+"/ner结果.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    entity_type_unprocessed_set = set()
    for i in data:
        for j in i['result']:
            entity_type_unprocessed_set.add(j[1])
    entity_type_unprocessed = list(entity_type_unprocessed_set)
    with open(data_path+"/entity_type_unprocessed.json", "w", encoding="utf-8") as f1:
        json.dump(entity_type_unprocessed, f1,indent=4, ensure_ascii=False)
def read_file(read_type:str) -> list:
    if read_type=="entity_type_unprocessed.json":
        with open(data_path+"/"+read_type, "r", encoding="utf-8") as f:
            entity_type_list = json.load(f)
        return entity_type_list
    else:
        return "read_type输入错误"
