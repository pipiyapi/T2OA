import json

with open("ner第五轮.json", "r", encoding="utf-8") as json_file:
    data = json.load(json_file)
def count_entity(entity_dict):
    entity_num=set()
    entity_type_num=set()
    for key,value in entity_dict.items():
        for item in value:
            entity_num.add(item[0])
            entity_type_num.add(item[1])
    return len(entity_num),len(entity_type_num)
print(count_entity(data))