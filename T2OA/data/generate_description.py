import json
from langchain.prompts import ChatPromptTemplate
from concurrent.futures import ThreadPoolExecutor, as_completed
from llm import llm
from tqdm import tqdm
description_result={}
llm_description_generate_prompt = ChatPromptTemplate.from_template(
    """
    你是绿色建筑领域进行本体模型构建的专家，根据以下给出的实体类型，生成要求的实体类型的定义描述，结果返回json格式字典，除此之外不要返回其他任何内容。
    要求包含以下4点：
    1.该实体类型是父类中的一种
    2.有哪些类型与该实体类型同层次，也同属于父类。
    3.该实体类型可能包含哪些子类型
    4.对该实体类型的一段文字定义描述
    
    以下是你需要定义的实体类型名称：{entity_type}
    
    结果返回json格式字典如下：{{"父类":"......","同层次类型":["类型1","类型2",....],"子类型":["子类型1","子类型2",....],"定义描述":"......"}}
    """
)
description_generate_assistant = llm_description_generate_prompt | llm
def process_item(item):
    result = description_generate_assistant.invoke({"entity_type": item}).content
    json_data = json.loads(result.replace('```json', '').replace('```', ''))
    json_data["实体类型"] = item
    return json_data
if __name__ == "__main__":
    with open("data/disambiguation_unprocessed.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(process_item, item) for item in data]
        for future in tqdm(as_completed(futures), total=len(data)):
            json_data = future.result()
            print(json_data)
            description_result[json_data["实体类型"]]=json_data
    with open("graph_description_result.json", 'w', encoding='utf-8') as f:
        json.dump(description_result, f,indent=4, ensure_ascii=False)