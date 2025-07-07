from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json
from llm import llm,ner1_prompt,ner2_prompt
from tqdm import tqdm
def read_chunk(chunk_path="ner/data/绿色建筑评价标准.txt"):
    with open(chunk_path, 'r', encoding='utf-8') as file:
        chunk_list=[]
        chunk=[]
        for line in file:
            line=line.strip()
            if line=="---":
                chunk_str = "\n ".join(chunk)
                chunk_list.append(chunk_str)
                chunk = []
            else:
                chunk.append(line)
    return chunk_list
def ner(chunk_list):

    ner_llm=ner1_prompt| llm
    entity_dict={}
    id=0
    entity_len=0
    for chunk in tqdm(chunk_list, desc="Processing chunks 1", unit="chunk"):
        retries = 0
        while retries < 3:
            try:
                print(f"text:{chunk}")
                ner_result = ner_llm.invoke({"text": chunk}).content
                ner_result_json = json.loads(ner_result.replace('```json', '').replace('```', ''))
                print(ner_result_json)
                break
            except Exception as e:
                retries += 1
                print(f"Error processing chunk {chunk} (attempt {retries}/3): {e}")
                if retries == 3:
                    print(f"Failed to process chunk {chunk} after 3 attempts. Skipping...")
        entity_len+=len(ner_result_json)
        print(entity_len)
        id+=1
        entity_dict[id]=ner_result_json
    return entity_dict
def ner_2(entity_dict,chunk_list):
    ner_llm = ner2_prompt | llm
    id = 1
    entity_len=0
    for chunk in tqdm(chunk_list, desc="Processing chunks 2", unit="chunk"):
        retries = 0
        while retries < 3:
            try:
                print(f"text:{chunk},entity_list:{str(entity_dict[str(id)])}")
                ner_result = ner_llm.invoke({"text": chunk,"entity_list":str(entity_dict[str(id)])}).content
                print(ner_result)
                ner_result_json = json.loads(ner_result.replace('```json', '').replace('```', ''))
                print(ner_result_json)
                break
            except Exception as e:
                retries += 1
                print(e)
                if retries == 3:
                    print(f"Failed to process chunk {chunk} after 3 attempts. Skipping...")
        entity_len += len(ner_result_json)
        print(entity_len)
        entity_dict[id] = ner_result_json
        id += 1
    return entity_dict
def count_entity(entity_dict):
    entity_num=set()
    entity_type_num=set()
    for key,value in entity_dict.items():
        for item in value:
            entity_num.add(item[0])
            entity_type_num.add(item[1])
    return len(entity_num),len(entity_type_num)
def json_save(data,json_name):
    with open(json_name, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)
def json_load(json_name):
    with open(json_name, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)
    return data
def iteration_ner(chunk_path):
    chunk_list=read_chunk(chunk_path)
    entity_dict=ner(chunk_list)
    json_save(entity_dict,"ner/ner第1轮.json")
    num=1
    while True:
        entity_dict=json_load(f"ner/ner第{num}轮.json")
        entity_dict2=ner_2(entity_dict,chunk_list)
        num += 1
        json_save(entity_dict2, f"ner/ner第{num}轮.json")
        if count_entity(entity_dict2[1])<=count_entity(entity_dict[1]):
            break
    json_result = json_load(f"ner/ner第{num}轮.json")
    list_result = []
    for key, value in json_result.items():
        dict_item = {}
        dict_item["id"] = key
        dict_item["result"] = value
        list_result.append(dict_item)
    json_save(list_result, "ner/ner结果.json")


if __name__ == "__main__":
    # chunk_list=read_chunk()
    # entity_dict=ner(chunk_list)
    # json_save(entity_dict,"ner第一轮.json")
    # entity_dict=json_load("ner第一轮.json")
    # entity_dict2=ner_2(entity_dict,chunk_list)
    # json_save(entity_dict2, "ner第二轮.json")
    # entity_dict=json_load("ner第四轮.json")
    # entity_dict2=ner_2(entity_dict,chunk_list)
    # json_save(entity_dict2, "ner第五轮.json")
    entity_dict1 = json_load("ner第一轮.json")
    entity_dict2 = json_load("ner第二轮.json")
    entity_dict3 = json_load("ner第三轮.json")
    entity_dict4 = json_load("ner第四轮.json")
    entity_dict5 = json_load("ner第五轮.json")
    print(count_entity(entity_dict1))
    print(count_entity(entity_dict2))
    print(count_entity(entity_dict3))
    print(count_entity(entity_dict4))
    print(count_entity(entity_dict5))

