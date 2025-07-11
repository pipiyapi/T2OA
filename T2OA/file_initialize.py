import json
import os
def file_initialize(ner_path,data_path):
    with open(ner_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    entity_type_unprocessed_set = set()
    for i in data:
        for j in i['result']:
            entity_type_unprocessed_set.add(j[1])
    entity_type_unprocessed = list(entity_type_unprocessed_set)
    with open(data_path, "w", encoding="utf-8") as f1:
        json.dump(entity_type_unprocessed, f1,indent=4, ensure_ascii=False)

