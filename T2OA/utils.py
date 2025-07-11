import json
import logging
from generate_description import process_item
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
def remove_list(list1,list2):
    return [item for item in list1 if item not in list2]

def get_embedding(text) -> list:
    url = "https://api.siliconflow.cn/v1/embeddings"
    payload = {
        "model": "BAAI/bge-large-zh-v1.5",
        "input": text,
        "encoding_format": "float"
    }
    headers = {
        "Authorization": "Bearer sk-bsgplggngjjboctlpenlllmbgegyxsfrxbltbvusqtgveghx",
        "Content-Type": "application/json"
    }

    # 创建 Session 对象
    session = requests.Session()

    # 设置重试策略
    retries = Retry(
        total=3,  # 总重试次数
        backoff_factor=1,  # 重试之间的等待时间因子
        status_forcelist=[500, 502, 503, 504]  # 需要重试的 HTTP 状态码
    )

    # 将重试策略应用到 Session 的 HTTPAdapter
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    max_retries=5
    retries=0
    while retries < max_retries:
        try:
            response = session.post(url, json=payload, headers=headers)
            response.raise_for_status()  # 如果响应状态码不是 200-299，抛出异常
            embedding = json.loads(response.text).get("data")[0].get("embedding")
            return embedding
        except requests.exceptions.RequestException as e:
            retries += 1
            if retries < max_retries:
                logging.info(f"【get_embedding】Request failed, retrying...")
                logging.info(f"【get_embedding】Request failed: {e}")
            else:
                logging.info(f"【get_embedding】Request failed after {max_retries} retries.")
                return None
def get_entity_str(entity_types:list):
    entity_list=[]
    entity_str=""
    with open("data/dict_type_entity.json", 'r', encoding='utf-8') as f:
        DICT_TYPE_ENTITY = json.load(f)
    for entity_type in entity_types:
        entity_list.append(entity_type+":"+str(DICT_TYPE_ENTITY.get(entity_type,[])))
    entity_str="\n".join(entity_list)
    return entity_str
def get_description(entity_type):
    with open("temp_data/description_result.json", 'r', encoding='utf-8') as f:
        description_result = json.load(f)
    entity_type_description=description_result.get(entity_type,None)
    if entity_type_description is None:
        logging.info(f"【get_description】实体类型:{entity_type}没有找到描述，正在生成描述...")
        process_item(entity_type)
        description_result[entity_type] = process_item(entity_type)
        with open("temp_data/description_result.json", 'w', encoding='utf-8') as f:
            json.dump(description_result, f, indent=4, ensure_ascii=False)
        entity_type_description=description_result[entity_type]
    entity_type_description_str=(
    f"{entity_type}:\n"
    f"{entity_type}的可能父类：{entity_type_description['父类']}\n"
    f"{entity_type}的可能同层次类型：{entity_type_description['同层次类型']}\n"
    f"{entity_type}的可能子类型：{entity_type_description['子类型']}\n"
    f"{entity_type}的定义描述：{entity_type_description['定义描述']}"
)
    logging.info(f"【get_description】entity_type:{entity_type}description_result:{entity_type_description}")
    return entity_type_description_str


def closest_sum(arr, target):
    def backtrack(index, current_sum, path, result):
        if current_sum > target:
            return
        if current_sum > result['max_sum']:
            result['max_sum'] = current_sum
            result['best_path'] = path.copy()

        for i in range(index, len(arr)):
            backtrack(i + 1, current_sum + arr[i], path + [arr[i]], result)

    result = {'max_sum': -1, 'best_path': []}
    backtrack(0, 0, [], result)
    return result['best_path']
if __name__ == "__main__":
    from llm import *
    llm_is_a_diagnose_assistant = is_a_diagnose_prompt | llm
    list_1=["建筑物","建筑部件"]
    entity_type_description = "\n".join(get_description(i) for i in list_1)
    llm_is_a_diagnose_result = llm_is_a_diagnose_assistant.invoke({"entity_type_description": entity_type_description, "entity_type_list": str(list_1)})
    print(llm_is_a_diagnose_result)