import json
with open("ner结果.json", 'r', encoding='utf-8') as f:
    data = json.load(f)
dict_type_entity={}
exist_list=[]
for i in data:
    for j in i["result"]:
        if j[1] in exist_list:
            if j[0] not in dict_type_entity[j[1]]:
                dict_type_entity[j[1]].append(j[0])
        else:
            exist_list.append(j[1])
            dict_type_entity[j[1]]=[j[0]]
with open("dict_type_entity.json", 'w', encoding='utf-8') as f:
    json.dump(dict_type_entity, f, ensure_ascii=False, indent=4)
print(dict_type_entity)
