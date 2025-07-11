import json
from langchain.prompts import ChatPromptTemplate
from concurrent.futures import ThreadPoolExecutor, as_completed
from llm import llm,llm_description_generate_prompt
from tqdm import tqdm
def process_item(item):
    description_generate_assistant = llm_description_generate_prompt | llm
    result = description_generate_assistant.invoke({"entity_type": item}).content
    json_data = json.loads(result.replace('```json', '').replace('```', ''))
    json_data["实体类型"] = item
    return json_data
def generate_description(data_path,description_path):
    description_result={}
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(process_item, item) for item in data]
        for future in tqdm(as_completed(futures), total=len(data)):
            json_data = future.result()
            print(json_data)
            description_result[json_data["实体类型"]]=json_data
    with open(description_path, 'w', encoding='utf-8') as f:
        json.dump(description_result, f,indent=4, ensure_ascii=False)

