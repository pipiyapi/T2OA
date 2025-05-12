from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json
from tqdm import tqdm
def read_chunk():
    with open('data/绿色建筑评价标准.txt', 'r', encoding='utf-8') as file:
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
    llm = ChatOpenAI(
        model='deepseek-chat',
        openai_api_key='*******************************',
        openai_api_base='*******************************',
        max_tokens=4000
    )
    ner_prompt = ChatPromptTemplate.from_template("""
    <Role>
    你是绿色建筑评估领域专门进行知识图谱中的实体抽取的专家。
    </Role>
    
    <task>
    请从下面给出的绿色建筑规范文本中抽取出实体并生成其实体类型，结果以json格式的列表返回[[实体1，实体类型1],[实体2，实体类型2].....[实体n，实体类型n]],除此之外不要返回其他任何内容。
    <task>
    
    <requirement>
    -你需要理解文本内容，不要遗漏任何一个实体
    -规范条文的编号不要作为实体抽取。
    -实体类型应该是从文本中抽取的实体的抽象上位词
    </requirement>
    
    <text>
    以下是你需要进行实体抽取的文本：
    {text}
    </text>
    """)
    ner_llm=ner_prompt| llm
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
    llm = ChatOpenAI(
        model='deepseek-chat',
        openai_api_key='**********************',
        openai_api_base='************************',
        max_tokens=4000
    )
    ner_prompt = ChatPromptTemplate.from_template("""
    <Role>
    你是绿色建筑评估领域专门进行知识图谱中的实体抽取的专家。
    </Role>

    <task>
    entity_list中内容为已经抽取出的实体。请根据text中的内容对entity_list中的错误的[实体,实体类型]进行替换，正确的[实体,实体类型]进行保留，遗漏的[实体,实体类型]进行追加。结果以json格式的列表返回最终完整的[[实体1，实体类型1],[实体2，实体类型2].....[实体n，实体类型n]],除此之外不要返回其他任何内容。
    <task>

    <requirement>
    -你需要理解文本内容，不要遗漏任何一个实体
    -规范条文的编号不要作为实体抽取。
    -实体类型应该是从文本中抽取的实体的抽象上位词
    </requirement>

    <text>
    以下是你需要进行实体抽取的文本：
    {text}
    </text>
    
    <entity_list>
    {entity_list}
    </entity_list>
    """)
    ner_llm = ner_prompt | llm
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
def count_len(entity_dict):
    num=0
    for key,value in entity_dict.items():
        num+=len(value)
    return num
def json_save(data,json_name):
    with open(json_name, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)
def json_load(json_name):
    with open(json_name, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)
    return data
if __name__ == "__main__":
    chunk_list=read_chunk()
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
    print(count_len(entity_dict1))
    print(count_len(entity_dict2))
    print(count_len(entity_dict3))
    print(count_len(entity_dict4))
    print(count_len(entity_dict5))

