from graph_struct import graph,memory
from read_file import read_file,file_initialize
from neo4j_database.cypher import search_all_nodes
import logging
import time
import os
def stream_graph_updates(config,group_num):
    entity_type_unprocessed_all = read_file("entity_type_unprocessed.json")
    state_dict={
    "entity_type_unprocessed_all": entity_type_unprocessed_all[group_num:],
    "entity_type_unprocessed": entity_type_unprocessed_all[:group_num],
    "related_nodes": [],
    "in_graph_entity_type_all": [],
    "in_graph_entity_type": [],
    "group_num": group_num}
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
    #设置config
    config = {"recursion_limit": 20000,"configurable": {"thread_id": "agent4_13"}}
    group_num=15

    #log 设置
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
    #从头开始agent
    #文件初始化
    file_initialize()
    stream_graph_updates(config,group_num)

    #从断点开始agent
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


