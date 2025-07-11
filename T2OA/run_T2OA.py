from graph_struct import graph,memory
from file_initialize import file_initialize
from text_chunking import chunk_text
from ner import iteration_ner
from generate_description import generate_description
import logging
import time
import os
import json
def stream_graph_updates(config,group_num,top_k):
    with open("data/entity_type_unprocessed.json", "r", encoding="utf-8") as f:
        entity_type_unprocessed_all = json.load(f)
    state_dict={
    "entity_type_unprocessed_all": entity_type_unprocessed_all[group_num:],
    "entity_type_unprocessed": entity_type_unprocessed_all[:group_num],
    "related_nodes": [],
    "in_graph_entity_type_all": [],
    "in_graph_entity_type": [],
    "group_num": group_num,
    "top_k":top_k}
    events = graph.stream(state_dict,config=config,stream_mode="values")
    # events = graph.stream({"group_num":group_num},config=config,stream_mode="values")
    for event in events:
        if "messages" in event and event["messages"]:
            # event["messages"][-1].pretty_logging.info()
            logging.info("------------------------------------------------")
        # logging.info(event["disambiguation_unprocessed"])
        # logging.info(event["disambiguation_processed"])
def get_last_state(config):

    checkpoint = memory.get(config)
    logging.info(f"最新的checkpoint为:{checkpoint}")
    checkpoint_state=checkpoint["channel_values"]
    logging.info(f"最新的checkpoint_state为:{checkpoint_state}")
    # #更新图中state.
    # config = {"recursion_limit": 10000,
    #           "configurable": {"thread_id": "agent4_10"}}
    graph.update_state(config,checkpoint_state)
    #从checkpoint恢复
    for event in graph.stream(None, config=config,stream_mode="values"):
        if "messages" in event and event["messages"]:
            # event["messages"][-1].pretty_logging.info()
            logging.info("------------------------------------------------")
if __name__ == "__main__":
    T2OA_config={
        "recursion_limit": 200000, #Langgraph recursion restriction
        "thread_id":"111", #Thread ID
        "group_num":50,#Size of the current processing concept list
        "top_k":65,#Size of the retrieved node list
        "raw_data_path":"ner/data/绿色建筑评价标准.txt",#raw data path
        "split_data_path":"ner/data/绿色建筑评价标准_chunk.txt",#split data path
    }
    #设置config
    config = {"recursion_limit": 20000,"configurable": {"thread_id": "agent4_13"}}
    group_num=T2OA_config.get("group_num")
    top_k=T2OA_config.get("top_k")
    #log set
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_filename = os.path.join(log_dir, f"log_{timestamp}.txt")
    logging.basicConfig(
        level=logging.INFO,  # 日志记录级别
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_filename, mode='w'),
            logging.StreamHandler()
        ]
    )
    #Run the agent from scratch
    # concept extraction
    chunk_text(T2OA_config.get("raw_data_path"), 500, T2OA_config.get("split_data_path"))
    iteration_ner(T2OA_config.get("split_data_path"))
    #concept description generation
    file_initialize("ner/ner结果.json","data/entity_type_unprocessed.json")
    generate_description("data/entity_type_unprocessed.json","data/description_result.json")
    #concept disambiguation,relation generation,ontology restructuring
    stream_graph_updates(config,group_num,top_k)

    #Start running the agent from the breakpoint
    # retry_count = 0
    # max_retries = 2
    # while retry_count < max_retries:
    #     try:
    #         get_last_state(config)
    #         break
    #     except Exception as e:
    #         logging.error(f"Error occurred: {e}",exc_info=True)
    #         retry_count += 1
    #         logging.info(f"Retrying... (Attempt {retry_count}/{max_retries})")


