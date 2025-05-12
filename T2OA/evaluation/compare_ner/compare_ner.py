import json
import os
from neo4j_database.cypher import check_indegree_zero
from llm import llm
from langchain_core.prompts import ChatPromptTemplate
def get_benchmark_entitytype():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    file_path=parent_dir+"/benchmark_onto/topic_list.json"
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    benchmark_entitytype=[]
    for item in data:
        benchmark_entitytype.extend(item)
    return benchmark_entitytype
def get_my_entitytype():
    my_entitytype=check_indegree_zero()
    return my_entitytype
def read_chunk():
    with open('绿色建筑评价标准.txt', 'r', encoding='utf-8') as file:
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
def ner_test(entitytype_list):
    llm_ner_prompt = ChatPromptTemplate.from_template("""
    <Role>
    你是绿色建筑评估领域专门进行知识图谱中的实体抽取的专家。
    </Role>
    
    <task>
    请根据下面给出的绿色建筑规范文本以及实体类型，从文本中抽取出实体类型列表中对应的实体，结果以json格式的列表返回[[实体1，实体类型1],[实体2，实体类型2].....[实体n，实体类型n]],除此之外不要返回其他任何内容。
    <task>
    
    <requirement>
    -你需要理解文本内容，不要遗漏任何一个实体
    -规范条文的编号不要作为实体抽取。
    -结果返回的实体类型只能是实体类型列表中的实体类型
    -请确保抽取文本中所有的实体，并通过给出的实体类型检查是否遗漏，不要遗漏任何一个实体
    </requirement>
    
    <text>
    以下是你需要进行实体抽取的文本：
    {text}
    </text>
    
    <entity_type>
    以下是给出的实体类型列表：
    {entitytype_list}
    </entity_type>
    """)
    chunk_list=read_chunk()
    id = 0
    entity_dict={}
    for chunk in chunk_list:
        llm_ner_assistant = llm_ner_prompt | llm
        retries = 0
        while retries < 3:
            try:
                ner_result = llm_ner_assistant.invoke({"text": chunk,"entitytype_list":entitytype_list}).content
                ner_result_json = json.loads(ner_result.replace('```json', '').replace('```', ''))
                print(ner_result_json)
                print(id)
                break
            except Exception as e:
                retries += 1
                print(f"Error processing chunk {chunk} (attempt {retries}/3): {e}")
        id+=1
        entity_dict[id] = ner_result_json
    return entity_dict
if __name__ == "__main__":
    # print(len(get_benchmark_entitytype()))
    print(len(get_my_entitytype()))
    # benchmark_result=ner_test(get_benchmark_entitytype())
    # with open('benchmark_result.json', 'w', encoding='utf-8') as file:
    #     json.dump(benchmark_result, file, ensure_ascii=False, indent=4)
    my_result=ner_test(get_my_entitytype())
    with open('my_result.json', 'w', encoding='utf-8') as file:
        json.dump(my_result, file, ensure_ascii=False, indent=4)