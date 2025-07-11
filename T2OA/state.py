from typing import Annotated,Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
class State(TypedDict):
    messages: Annotated[list, add_messages] #消息列表
    entity_type_unprocessed_all: list #未消歧的全部实体类型列表
    entity_type_unprocessed: list #未消歧的实体类型列表（一轮个数为group_num）
    disambiguation_result: list #消歧结果列表
    in_graph_entity_type_all: list #已在图中的实体类型列表
    in_graph_entity_type:list #已在图中的实体类型列表（一轮个数为group_num）
    is_a_result: list
    hypernym_generation_result: list
    level1_list:list #一级节点列表
    level1_dict:dict #一级节点字典,包含对该节点的示例子节点
    related_nodes: list #检索到已在图中的相似实体类型列表
    group_num: int  #一轮处理的消歧的实体类型个数
    top_k:int #检索到的相似实体类型个数