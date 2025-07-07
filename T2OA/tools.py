from langchain_core.tools import tool
from state import State
import os
import logging
from utils import get_entity_str
from typing import List,Annotated
from llm import llm,Hypernym_disambiguation_prompt,Hypernym_disambiguation_diagnose_prompt
from neo4j_database.cypher import *
from utils import get_description
class ToolResult:
    def __init__(self, tool_name: str, tool_input: str, tool_output: str):
        self.tool_name = tool_name
        self.tool_input = tool_input
        self.tool_output = tool_output
def raplace_trples(trples:list,old_node:list,new_node:str):
    for triple in trples:
        if triple[0] in old_node:
            triple[0]=new_node
        elif triple[2] in old_node:
            triple[2]=new_node
    return trples
def write_disambiguation_to_file(disambiguation_unprocessed:list,disambiguation_processed:str):
    file_path = "disambiguation_record.txt"
    content = str(disambiguation_unprocessed) + "->" + str(disambiguation_processed) + "\n"
    # 如果文件不存在，先创建并写入；否则追加
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
    else:
        with open(file_path, "a", encoding="utf-8") as file:
            file.write(content)
# 添加tool装饰器
@tool
def tool_disambiguation(same_entity_type: Annotated[List[str],"包含相同含义实体类型的一维字符串列表，元素个数至少为两个或以上"],disambiguated_entity_type:Annotated[str,"对same_entity_type消歧后的一个实体类型"]) -> str:
    """
    <tool description>
    当判断给出的实体类型只是名称不同，但是指代的对象和描述的范围一致，本质上属于同一个实体类型，调用此工具。
    </tool description>
    """
    in_graph=[]
    not_in_graph=[]
    disambiguated_entity_type_is_in_graph=False
    graph_state=search_all_nodes()[0]['node_names']
    #区分在图中和不在图中的实体类型
    for entity_type in same_entity_type:
        if entity_type in graph_state:
            in_graph.append(entity_type)
        else:
            not_in_graph.append(entity_type)
    #操作neo4j
    delete_nodes(in_graph)
    logging.info(f"【neo4j操作】删除节点：{in_graph}")
    add_nodes([disambiguated_entity_type])
    logging.info(f"【neo4j操作】添加节点：{disambiguated_entity_type}")
    write_disambiguation_to_file(same_entity_type,disambiguated_entity_type)
    logging.info(f"记录消歧")
    return ToolResult(
            tool_name="tool_disambiguation",
            tool_input=str(same_entity_type),
            tool_output=str(disambiguated_entity_type)
        )
@tool
def tool_not_disambiguation(not_related_entity_type: Annotated[List[str],"包含多个相互之间没有任何关系的实体类型的一维字符串列表，元素个数至少为两个或以上"]) -> str:
    """
        <tool description>
        如果你认为这些实体类型完全没有任何关系，完全是无关概念，则调用此工具，
        </tool description>
    """
    logging.info(f"【tool_not_disambiguation】{not_related_entity_type}这些实体类型完全没有任何关系，完全是无关概念，直接加入图中")
    add_nodes(not_related_entity_type)
    logging.info(f"【neo4j操作】添加节点：{not_related_entity_type}")
    write_disambiguation_to_file(not_related_entity_type, "无")
    logging.info(f"记录消歧")
    return ToolResult(
        tool_name="tool_not_disambiguation",
        tool_input=str(not_related_entity_type),
        tool_output=str(not_related_entity_type)
    )
@tool
def tool_hypernym_generation(similar_entity_type:  Annotated[List[str],"包含多个属于同一层级实体类型的一维字符串列表，元素个数至少为两个或以上"],generated_hypernym:Annotated[str,"对similar_entity_type生成的父类"]) -> str:
    """
    <tool description>
    当判断给出实体类型属于同一个层级，即同属于同一个父类之下时，调用此工具。
    </tool description>
    """
    in_graph = []
    not_in_graph = []
    graph_state = search_all_nodes()[0]['node_names']
    if generated_hypernym not in graph_state:
        #如果generated_hypernym与图中的某个节点可能需要消歧，则不添加该节点，并将上位词替换为消歧后节点
        retrieve_node_list=[]
        related_nodes=[]
        retrieve_similar_node_list = retrieve_similar_node(node_name=generated_hypernym, query="",idx_name="Entity_type_embedding")
        logging.info(f"【tool_hypernym_generation】节点{generated_hypernym}检索的retrieve_similar_node_list：{retrieve_similar_node_list}")
        for item in retrieve_similar_node_list:
            retrieve_node_list.append([item[0].page_content,item[1]])
        sorted_list = sorted(retrieve_node_list, key=lambda x: x[1], reverse=True)
        for item in sorted_list:
            related_nodes.append(item[0])
        logging.info(f"【tool_hypernym_generation】节点{generated_hypernym}检索的related_nodes：{related_nodes}")
        #大模型选择可能消歧节点
        llm_Hypernym_disambiguation_prompt=Hypernym_disambiguation_prompt | llm
        result = llm_Hypernym_disambiguation_prompt.invoke({"entity_type": generated_hypernym,"related_nodes":related_nodes}).content
        logging.info(f"【tool_hypernym_generation】节点{generated_hypernym}大模型认为相似的词语为{result}")
        #大模型消歧诊断
        entity_type_list=[generated_hypernym,result]
        entity_type_description = "\n".join(get_description(i) for i in entity_type_list)
        llm_Hypernym_disambiguation_diagnose_prompt=Hypernym_disambiguation_diagnose_prompt | llm
        result = llm_Hypernym_disambiguation_diagnose_prompt.invoke({"entity_type_description": entity_type_description, "entity_type_list": str(entity_type_list)}).content
        logging.info(f"【tool_hypernym_generation】节点{generated_hypernym}大模型诊断结果为{result}")
        if result=="消歧失败":
            add_nodes([generated_hypernym])
            logging.info(f"消歧失败，添加上位词{generated_hypernym}")
        else:
            generated_hypernym=result
            logging.info(f"【tool_hypernym_generation】消歧成功，上位词改为{generated_hypernym}")
            add_nodes([generated_hypernym])
        logging.info(f"【neo4j操作】上位词不在图中，添加节点：{generated_hypernym}")
    one_to_many_triple(similar_entity_type,generated_hypernym)
    logging.info(f"【neo4j操作】添加关系：{similar_entity_type}->{generated_hypernym}")
    return ToolResult(
        tool_name="tool_hypernym_generation",
        tool_input=str(similar_entity_type),
        tool_output=str(generated_hypernym)
    )
@tool
def tool_is_a(head_node: Annotated[str,"is_a三元组关系中的头实体，子类实体类型"],tail_node:Annotated[str,"is_a三元组关系中的尾实体，父类实体类型"]) -> str:
    """
    <tool description>
    你认为两个实体类型存在is_a关系，即存在其中一个实体类型是另一个的子类或父类时，调用此工具。
    </tool description>
    """
    graph_state = search_all_nodes()[0]['node_names']
    logging.info(f"【tool_is_a】准备将节点添加图中，头节点为{head_node}，尾节点尾{tail_node}")
    if head_node not in graph_state:
        logging.info(f"【tool_is_a】头节点:{head_node}不在图中,添加头节点")
        add_nodes([head_node])
        logging.info(f"【neo4j操作】添加节点：{[head_node]}")
    if tail_node not in graph_state:
        logging.info(f"【tool_is_a】尾节点:{head_node}不在图中,添加尾节点")
        add_nodes([tail_node])
        logging.info(f"【neo4j操作】添加节点：{[tail_node]}")
    one_to_one_triple(head_node,tail_node)
    logging.info(f"【neo4j操作】添加关系：{head_node}->{tail_node}")
    return ToolResult(
        tool_name="tool_is_a",
        tool_input=str([head_node,tail_node]),
        tool_output=str([head_node,tail_node])
    )
@tool
def tool_not_handle(not_related_entity_type: Annotated[List[str],"包含多个相互之间没有任何关系的实体类型的一维字符串列表，元素个数至少为两个或以上"]) -> str:
    """
        <tool description>
        如果你认为这些实体类型完全没有任何关系，完全是无关概念，则调用此工具，
        </tool description>
    """
    logging.info(f"【tool_not_handle】{not_related_entity_type}这些实体类型完全没有任何关系，完全是无关概念，不进行任何操作")
    return ToolResult(
        tool_name="tool_not_handle",
        tool_input=str(not_related_entity_type),
        tool_output=str(not_related_entity_type)
    )