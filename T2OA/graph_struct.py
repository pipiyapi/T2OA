import json

from langgraph.graph import StateGraph, START, END

from langchain_core.messages import ToolMessage

from tools import tool_disambiguation,tool_hypernym_generation,tool_is_a,tool_not_disambiguation,tool_not_handle
from state import State
from llm import llm,llm_R1,llm_disambiguation_prompt,llm_disambiguation_diagnose_prompt,llm_add_relation_prompt,llm_is_a_diagnose_prompt,llm_hypernym_generation_diagnose_prompt,llm_fix_graph_prompt,llm_schema_prompt,llm_json_format_prompt,llm_is_a_schema_prompt
from state_db.db_conf import conn
from data.compute_Levenshtein import balanced_hierarchical_clustering
from langgraph.checkpoint.sqlite import SqliteSaver
from neo4j_database.cypher import *
from utils import *
#状态
graph_builder = StateGraph(State)

#补全group_num
def group_num_complete(state: State):
    # 如果unprocess列表中个数少于group_num个数，则补全为group_num个数
    entity_type_unprocessed_all = state.get("entity_type_unprocessed_all")
    entity_type_unprocessed = state.get("entity_type_unprocessed")
    graph_state=search_all_nodes()[0]['node_names']
    d_value = state.get("group_num") - len(entity_type_unprocessed)
    logging.info(f"【group_num_complete】entity_type_unprocessed_all长度:{len(entity_type_unprocessed_all)}")
    logging.info(f"【group_num_complete】entity_type_unprocessed长度:{len(entity_type_unprocessed)}")
    logging.info(f"【group_num_complete】d_value:{d_value}")
    if d_value==0:
        logging.info(f"【group_num_complete】d_value为0，将前2个实体类型加入图中，然后将d_value改为2")
        add_nodes(entity_type_unprocessed[:2])
        logging.info(f"【neo4j操作】添加节点：{entity_type_unprocessed[:2]}")
        entity_type_unprocessed=entity_type_unprocessed[2:]
        d_value=2
    if d_value > 0:
        # 创建一个临时列表，用于存储将要加入entity_type_unprocessed的元素
        temp_list = []
        all_temp_list=[]
        for item in entity_type_unprocessed_all:
            all_temp_list.append(item)
            if item not in graph_state:
                temp_list.append(item)
                if len(temp_list) >= d_value:
                    break
            else:
                logging.info(f"【group_num_complete】{item}已经在图中")

        # 将符合条件的元素加入entity_type_unprocessed
        entity_type_unprocessed.extend(temp_list)
        # 从entity_type_unprocessed_all中移除已经加入的元素
        entity_type_unprocessed_all = remove_list(entity_type_unprocessed_all,all_temp_list)
    logging.info(f"【group_num_complete】补全后entity_type_unprocessed_all长度:{len(entity_type_unprocessed_all)},entity_type_unprocessed_all:{entity_type_unprocessed_all}")
    logging.info(f"【group_num_complete】补全后entity_type_unprocessed长度:{len(entity_type_unprocessed)},entity_type_unprocessed:{entity_type_unprocessed}")

    return {
        "entity_type_unprocessed_all": entity_type_unprocessed_all,
        "entity_type_unprocessed": entity_type_unprocessed,
    }

def retrieval_related_node(state: State):
    top_k=20
    entity_type_unprocessed = state.get("entity_type_unprocessed")
    logging.info(f"【retrieval_related_node】entity_type_unprocessed:{state.get('entity_type_unprocessed')}")
    retrieve_node_list=[]
    related_nodes = []
    seen={}
    for entity_type in entity_type_unprocessed:
        #[(Document(metadata={}, page_content='绿色建筑措施'), 0.76141357421875), (Document(metadata={}, page_content='技术措施'), 0.6863839626312256), (Document(metadata={}, page_content='评估方案'), 0.6482696533203125), (Document(metadata={}, page_content='阈值数值'), 0.6458165645599365)]
        retrieve_similar_node_list=retrieve_similar_node(node_name=entity_type,query="", idx_name="Entity_type_embedding")
        logging.info(f"【retrieval_related_node】节点{entity_type}检索的retrieve_similar_node_list：{retrieve_similar_node_list}")
        if retrieve_similar_node_list==[]:
            logging.info(f"【retrieval_related_node】图中没有节点")
            return {"related_nodes":""}
        for item in retrieve_similar_node_list:
            retrieve_node_list.append([item[0].page_content,item[1]])
    sorted_list = sorted(retrieve_node_list, key=lambda x: x[1], reverse=True)
    logging.info(f"【retrieval_related_node】相关节点排序sorted_list：{sorted_list}")
    for item in sorted_list:
        key = item[0]  # 第一个元素，如 "性能指标"
        if key not in seen:
            seen[key] = True  # 标记为已出现
            related_nodes.append(item[0])
    logging.info(f"【retrieval_related_node】返回的相似节点列表：{related_nodes[:top_k]}")
    return {"related_nodes":related_nodes[:top_k]}
def retrieval_related_node_2(state: State):
    top_k=10
    in_graph_entity_type = state.get("in_graph_entity_type")
    logging.info(f"【retrieval_related_node_2】in_graph_entity_type:{state.get('in_graph_entity_type')}")
    retrieve_node_list=[]
    related_nodes = []
    seen={}
    for entity_type in in_graph_entity_type:
        #[(Document(metadata={}, page_content='绿色建筑措施'), 0.76141357421875), (Document(metadata={}, page_content='技术措施'), 0.6863839626312256), (Document(metadata={}, page_content='评估方案'), 0.6482696533203125), (Document(metadata={}, page_content='阈值数值'), 0.6458165645599365)]
        retrieve_similar_node_list=retrieve_similar_node(node_name=entity_type,query="", idx_name="Entity_type_embedding")
        logging.info(f"【retrieval_related_node】节点{entity_type}检索的retrieve_similar_node_list：{retrieve_similar_node_list}")
        if retrieve_similar_node_list==[]:
            logging.info(f"【retrieval_related_node】图中没有节点")
            return {"related_nodes":""}
        for item in retrieve_similar_node_list:
            retrieve_node_list.append([item[0].page_content,item[1]])
    sorted_list = sorted(retrieve_node_list, key=lambda x: x[1], reverse=True)
    logging.info(f"【retrieval_related_node】相关节点排序sorted_list：{sorted_list}")
    for item in sorted_list:
        key = item[0]  # 第一个元素，如 "性能指标"
        if key not in seen:
            seen[key] = True  # 标记为已出现
            related_nodes.append(item[0])
    related_nodes=remove_list(related_nodes,in_graph_entity_type)
    logging.info(f"【retrieval_related_node】返回的相似节点列表：{related_nodes[:top_k]}")
    return {"related_nodes":related_nodes[:top_k]}
#定义assistance结点
def llm_disambiguation(state:State):
    entity_type_unprocessed=state.get('entity_type_unprocessed', [])
    related_nodes=state.get('related_nodes',[])
    logging.info(f"【llm_disambiguation】entity_type_unprocessed:{state.get('entity_type_unprocessed')}")
    logging.info(f"【llm_disambiguation】related_nodes:{state.get('related_nodes')}")
    llm_disambiguation_assistant = llm_disambiguation_prompt | llm
    entity_type_list=entity_type_unprocessed+related_nodes
    logging.info(f"【llm_disambiguation】entity_type_list:{entity_type_list}")
    retry_count = 0
    while retry_count < 3:
        try:
            result = llm_disambiguation_assistant.invoke({"entity_type_list":entity_type_list}).content
            disambiguation_result = json.loads(result.replace('```json', '').replace('```', ''))
            break
        except (json.JSONDecodeError, ValueError) as e:
            retry_count += 1
            logging.info(f"【llm_disambiguation】第{retry_count}次重试，错误信息：{e}")
    logging.info(f"【llm_disambiguation】disambiguation_result:{disambiguation_result}")
    return {"messages": result,"disambiguation_result":disambiguation_result}
def llm_tool_disambiguation_diagnose(state:State):
    disambiguation_result=state.get('disambiguation_result')
    logging.info(f"【llm_tool_disambiguation_diagnose】当前剩余disambiguation_result:{disambiguation_result}")
    tools=[tool_disambiguation,tool_not_disambiguation]
    llm_with_tools = llm.bind_tools(tools)
    if disambiguation_result!=[]:
        llm_disambiguation_diagnose_assistant = llm_disambiguation_diagnose_prompt | llm_with_tools
        entity_type_description = "\n".join(get_description(i) for i in disambiguation_result[0])
        logging.info(f"【llm_tool_disambiguation_diagnose】本次disambiguation diagnose为:{str(disambiguation_result[0])}")
        logging.info(f"【llm_tool_disambiguation_diagnose】entity_type_description:{entity_type_description}")
        llm_disambiguation_diagnose_result = llm_disambiguation_diagnose_assistant.invoke({"entity_type_description":entity_type_description,"entity_type_list":str(disambiguation_result[0])})
        logging.info(f"【llm_tool_disambiguation_diagnose】llm_disambiguation_diagnose_result:{llm_disambiguation_diagnose_result}")
        return {"messages":llm_disambiguation_diagnose_result,"disambiguation_result":disambiguation_result}
    else:
        logging.info(f"【llm_tool_disambiguation_diagnose】disambiguation_result为空，没有需要判断的实体类型列表")
class disambiguation_ToolNode():
    """A node that runs the tools requested in the last AIMessage."""

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        entity_type_unprocessed=inputs["entity_type_unprocessed"]
        disambiguation_result=inputs["disambiguation_result"]
        logging.info(f"【ToolNode】进行本次工具前entity_type_unprocessed:{entity_type_unprocessed}")
        logging.info(f"【ToolNode】进行本次工具前disambiguation_result:{disambiguation_result}")
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            if tool_result.tool_name=="tool_disambiguation":
                logging.info(f"进行了【ToolNode】tool_disambiguation，{tool_result.tool_input}移出entity_type_unprocessed")
                entity_type_unprocessed=remove_list(entity_type_unprocessed,eval(tool_result.tool_input))
                logging.info(f"进行了【ToolNode】tool_disambiguation，{tool_result.tool_input}移出disambiguation_result")
                disambiguation_result = disambiguation_result[1:]
            elif tool_result.tool_name=="tool_not_disambiguation":
                logging.info(f"进行了【ToolNode】tool_not_disambiguation，{tool_result.tool_input}移出entity_type_unprocessed")
                entity_type_unprocessed=remove_list(entity_type_unprocessed,eval(tool_result.tool_input))
                logging.info(f"进行了【ToolNode】tool_not_disambiguation，{tool_result.tool_input}移出disambiguation_result")
                disambiguation_result = disambiguation_result[1:]
            outputs.append(
            ToolMessage(
                content=json.dumps(tool_result.tool_output, ensure_ascii=False),
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )
        logging.info(f"【ToolNode】进行本次工具后entity_type_unprocessed:{entity_type_unprocessed}")
        logging.info(f"【ToolNode】进行本次工具后disambiguation_result:{disambiguation_result}")
        return {"messages": outputs,"entity_type_unprocessed":entity_type_unprocessed,"disambiguation_result":disambiguation_result}
def disambiguation_route_tools(
    state: State,
):
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """
    entity_type_unprocessed_all = state.get("entity_type_unprocessed_all")
    disambiguation_result = state.get("disambiguation_result")
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools_disambiguation_process"
    if entity_type_unprocessed_all == []:
        logging.info(f"【disambiguation_route_tools】entity_type_unprocessed_all为空，已完成所有实体类型消歧处理，路由的end")
        add_nodes(state.get("entity_type_unprocessed",[]))
        logging.info(f"【disambiguation_route_tools】将剩余的entity_type_unprocessed添加到图中:{state.get('entity_type_unprocessed')}")
        logging.info(f"【disambiguation_route_tools】消歧义阶段已完成，路由到in_graph_complete进行关系生成阶段")
        return "in_graph_complete"
    logging.info(f"【disambiguation_route_tools】没有调用任何工具，说明disambiguation_result为空，已完成所有工具调用，进入下一轮，路由到group_num_complete补充实体类型")
    return "group_num_complete"
##################################################################################################################################
#add_relation
def llm_relation(state:State):
    in_graph_entity_type=state.get('in_graph_entity_type')
    related_nodes=state.get('related_nodes')
    logging.info(f"【llm_relation】in_graph_entity_type:{state.get('in_graph_entity_type')}")
    logging.info(f"【llm_relation】related_nodes:{state.get('related_nodes')}")
    llm_relation_assistant = llm_add_relation_prompt | llm
    entity_type_list=in_graph_entity_type+related_nodes
    retry_count = 0
    while retry_count < 3:
        try:
            result = llm_relation_assistant.invoke({"entity_type_list":str(entity_type_list)}).content
            add_relation_result = json.loads(result.replace('```json', '').replace('```', ''))
            break
        except (json.JSONDecodeError, ValueError) as e:
            retry_count += 1
            logging.info(f"【llm_relation】第{retry_count}次重试，错误信息：{e}")
    is_a_result=add_relation_result.get('is_a',[])
    logging.info(f"【llm_relation】is_a_result:{is_a_result}")
    hypernym_generation_result=add_relation_result.get('same_level_entity_type',[])
    logging.info(f"【llm_relation】hypernym_generation_result:{hypernym_generation_result}")
    return {"messages": str(add_relation_result),"is_a_result":is_a_result,"hypernym_generation_result":hypernym_generation_result}
def llm_relation_diagnose(state:State):
    is_a_result=state.get('is_a_result',[])
    hypernym_generation_result=state.get('hypernym_generation_result',[])
    logging.info(f"【llm_relation_disnose】当前剩余is_a_result:{is_a_result}")
    logging.info(f"【llm_relation_disnose】当前剩余hypernym_generation_result:{hypernym_generation_result}")
    if is_a_result!=[]:
        tools=[tool_is_a,tool_not_handle]
        llm_with_tools = llm.bind_tools(tools)
        llm_is_a_diagnose_assistant = llm_is_a_diagnose_prompt | llm_with_tools
        entity_type_description = "\n".join(get_description(i) for i in is_a_result[0])
        logging.info(f"【llm_relation_disnose】本次is_a diagnose为:{str(is_a_result[0])}")
        llm_is_a_diagnose_result = llm_is_a_diagnose_assistant.invoke({"entity_type_description": entity_type_description, "entity_type_list": str(is_a_result[0])})
        logging.info(f"【llm_relation_disnose】llm_is_a_diagnose_result:{llm_is_a_diagnose_result}")
        return {"messages": llm_is_a_diagnose_result}
    elif hypernym_generation_result!=[]:
        tools=[tool_hypernym_generation,tool_not_handle]
        llm_with_tools = llm.bind_tools(tools)
        llm_hypernym_generation_diagnose_assistant = llm_hypernym_generation_diagnose_prompt | llm_with_tools
        entity_type_description = "\n".join(get_description(i) for i in hypernym_generation_result[0])
        logging.info(f"【llm_relation_disnose】本次hypernym diagnose为:{str(hypernym_generation_result[0])}")
        llm_hypernym_generation_diagnose_result = llm_hypernym_generation_diagnose_assistant.invoke({"entity_type_description": entity_type_description, "entity_type_list": str(hypernym_generation_result[0])})
        logging.info(f"【llm_relation_disnose】llm_hypernym_generation_diagnose_result:{llm_hypernym_generation_diagnose_result}")
        return {"messages": llm_hypernym_generation_diagnose_result}
    else:
        logging.info(f"【llm_relation_disnose】is_a_result和hypernym_generation_result都为空，没有需要判断的实体类型列表")
def relation_route_tools(
    state: State,
):
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """
    in_graph_entity_type_all = state.get("in_graph_entity_type_all")
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools_relation_process"
    logging.info(f"【relation_route_tools】没有调用任何工具，说明is_a_result和hypernym_generation_result为空，已完成所有工具调用，进入下一轮，路由到llm_check_tree_format检查图中节点是否符合要求")
    return "llm_check_tree_format"
class relation_ToolNode():
    """A node that runs the tools requested in the last AIMessage."""

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        in_graph_entity_type=inputs["in_graph_entity_type"]
        is_a_result=inputs["is_a_result"]
        hypernym_generation_result=inputs["hypernym_generation_result"]
        logging.info(f"【relation_ToolNode】进行本次工具前in_graph_entity_type:{in_graph_entity_type}")
        logging.info(f"【relation_ToolNode】进行本次工具前is_a_result:{is_a_result}")
        logging.info(f"【relation_ToolNode】进行本次工具前hypernym_generation_result:{hypernym_generation_result}")
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            if tool_result.tool_name=="tool_hypernym_generation":
                logging.info(f"进行了【relation_ToolNode】tool_hypernym_generation，{tool_result.tool_input}移出in_graph_entity_type")
                in_graph_entity_type=remove_list(in_graph_entity_type,eval(tool_result.tool_input))
                logging.info(f"进行了【relation_ToolNode】tool_hypernym_generation，{tool_result.tool_input}移出is_a_result")
                hypernym_generation_result = hypernym_generation_result[1:]
            elif tool_result.tool_name=="tool_is_a":
                logging.info(f"进行了【relation_ToolNode】tool_is_a，{tool_result.tool_input}移出in_graph_entity_type")
                in_graph_entity_type=remove_list(in_graph_entity_type,eval(tool_result.tool_input))
                logging.info(f"进行了【relation_ToolNode】tool_is_a，{tool_result.tool_input}移出hypernym_generation_result")
                is_a_result = is_a_result[1:]
            elif tool_result.tool_name=="tool_not_handle":
                logging.info(f"进行了【relation_ToolNode】tool_not_handle，{tool_result.tool_input}移出in_graph_entity_type")
                in_graph_entity_type=remove_list(in_graph_entity_type,eval(tool_result.tool_input))
                if is_a_result!=[]:
                    is_a_result = is_a_result[1:]
                    logging.info(f"进行了【relation_ToolNode】tool_not_handle，{tool_result.tool_input}移出is_a_result")
                else:
                    hypernym_generation_result=hypernym_generation_result[1:]
                    logging.info(f"进行了【relation_ToolNode】tool_not_handle，{tool_result.tool_input}移出hypernym_generation_result")
            outputs.append(
            ToolMessage(
                content=json.dumps(tool_result.tool_output, ensure_ascii=False),
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )
        return {"messages": outputs,"in_graph_entity_type":in_graph_entity_type,"is_a_result":is_a_result,"hypernym_generation_result":hypernym_generation_result}
def in_graph_complete(state:State):
    # 如果unprocess列表中个数少于group_num个数，则补全为group_num个数
    in_graph_entity_type_all = state.get("in_graph_entity_type_all", [])
    in_graph_entity_type = state.get("in_graph_entity_type",[])
    group_num=state.get("group_num")
    if in_graph_entity_type_all==[] and in_graph_entity_type==[]:
        logging.info(f"【in_graph_complete】in_graph_entity_type_all和in_graph_entity_type都为空，将图中所有节点加入in_graph_entity_type_all，前group_num个节点加入in_graph_entity_type")
        in_graph_entity_type_all = search_all_nodes()[0]['node_names']
        in_graph_entity_type_all_sort = balanced_hierarchical_clustering(in_graph_entity_type_all, 100)
        entity_list = []
        for i in in_graph_entity_type_all_sort:
            entity_list.extend(i)
        logging.info(f"【in_graph_complete】in_graph_entity_type_all长度:{len(entity_list)}")
        logging.info(f"【in_graph_complete】in_graph_entity_type_all:{entity_list}")
        return {"in_graph_entity_type_all": entity_list[group_num:], "in_graph_entity_type": entity_list[:group_num]}
    d_value = group_num - len(in_graph_entity_type)
    logging.info(f"【in_graph_complete】in_graph_entity_type_all长度:{len(in_graph_entity_type_all)}")
    logging.info(f"【in_graph_complete】in_graph_entity_type长度:{len(in_graph_entity_type)}")
    logging.info(f"【in_graph_complete】d_value:{d_value}")

    if d_value > 0:
        logging.info(f"【in_graph_complete】进行补全")
        in_graph_entity_type.extend(in_graph_entity_type_all[:d_value])
        in_graph_entity_type_all = in_graph_entity_type_all[d_value:]
    logging.info(
        f"【in_graph_complete】补全后entity_type_unprocessed_all长度:{len(in_graph_entity_type_all)},entity_type_unprocessed_all:{in_graph_entity_type_all}")
    logging.info(
        f"【in_graph_complete】补全后entity_type_unprocessed长度:{len(in_graph_entity_type)},entity_type_unprocessed:{in_graph_entity_type}")
    return {
        "in_graph_entity_type_all": in_graph_entity_type_all,
        "in_graph_entity_type": in_graph_entity_type,
    }
def llm_check_tree_format(state:State):
    def fix_graph(node):
        triple_list, node_list = get_connected_subgraph([node])
        graph_json_info = {"nodes": node_list, "edges": triple_list}
        logging.info(f"【fix_graph】当前待修复图:{graph_json_info}")
        llm_fix_graph_assistant = llm_fix_graph_prompt | llm
        llm_fix_graph_result = llm_fix_graph_assistant.invoke({"json_graph_info": str(graph_json_info)}).content
        logging.info(f"【fix_graph】llm_fix_graph_result结果:{llm_fix_graph_result}")
        fix_graph_result = json.loads(llm_fix_graph_result.replace('```json', '').replace('```', ''))
        logging.info(f"【fix_graph】修复后结果:{fix_graph_result}")
        del_nodes_triples(graph_json_info["edges"])
        logging.info(f"【fix_graph】删除旧边{graph_json_info['edges']}")
        add_nodes_triples(fix_graph_result["edges"])
        logging.info(f"【fix_graph】添加新边:{fix_graph_result['edges']}")
    while True:
        logging.info("【llm_check_tree_format】检测是否有环")
        cycle_list=check_cycle()
        outdegree_list=check_outdegree()
        if cycle_list!=[]:
            logging.info(f"【llm_check_tree_format】检测到有环，对{cycle_list[0]}所在子图进行修复")
            fix_graph(cycle_list[0])
            logging.info(f"【llm_check_tree_format】检测到有环，对{cycle_list[0]}所在子图进行修复完成")
        elif outdegree_list!=[]:
            logging.info(f"【llm_check_tree_format】检测到有出度大于1节点，对{outdegree_list[0]}所在子图进行修复")
            fix_graph(outdegree_list[0])
            logging.info(f"【llm_check_tree_format】检测到有出度大于1节点，对{outdegree_list[0]}所在子图进行修复完成")
        else:
            logging.info("【llm_check_tree_format】检测到没有环和出度大于1节点，返回")
            break
    return {"messages": "检测到没有环和出度大于1节点，返回"}
def relation_route_to_end(state: State):
    in_graph_entity_type_all = state.get("in_graph_entity_type_all")
    if in_graph_entity_type_all == []:
        logging.info(f"【relation_route_to_end】in_graph_entity_type_all为空，已完成所有实体类型增加关系处理，路由的llm_schema进行schema阶段")
        return "llm_schema"
    else:
        logging.info(f"【relation_route_to_end】in_graph_entity_type_all不为空，路由到in_graph_complete补全")
        return "in_graph_complete"

def llm_schema(state:State):
    in_graph_all_node = search_all_nodes()[0]['node_names']
    logging.info(f"【llm_schema】图中的节点为:{in_graph_all_node}，一共{len(in_graph_all_node)}个")
    schema_assistant = llm_schema_prompt | llm_R1
    schema_result = schema_assistant.invoke({"in_graph_all_node":in_graph_all_node}).content
    logging.info(f"【llm_schema】schema_result:{schema_result}")
    json_format_assistant=llm_json_format_prompt | llm
    json_format_result=json_format_assistant.invoke({"schema_result":schema_result}).content
    logging.info(f"【llm_schema】json_format_result:{json_format_result}")
    json_object=json.loads(json_format_result.replace('```json', '').replace('```', ''))
    level1_list=json_object["一级实体列表"]
    level1_dict=json_object["一级实体列表字典表"]
    logging.info(f"【llm_schema】level1_list：{level1_list}")
    logging.info(f"【llm_schema】level1_dict：{level1_dict}")
    return {"level1_list":level1_list,"level1_dict":level1_dict}
def llm_is_a_schema(state:State):
    #只对出度为0的进行level1生成
    in_graph_all_node = check_outdegree_zero()
    logging.info(f"【llm_is_a_schema】图中的节点为:{in_graph_all_node}，一共{len(in_graph_all_node)}个")
    level1_list=state.get('level1_list')
    level1_dict=state.get('level1_dict')
    schema_example = '\n'.join(key + ":"+str(value) for key, value in level1_dict.items())
    logging.info(f"【llm_is_a_schema】schema_example:{schema_example}")
    llm_is_a_schema_assistant = llm_is_a_schema_prompt | llm
    add_nodes(level1_list)
    logging.info(f"【llm_is_a_schema】将level1节点{level1_list}加入图中")
    for entity_type in in_graph_all_node:
        result=llm_is_a_schema_assistant.invoke({"schema_example":schema_example,"Hypernym_list":level1_list,"entity_type":entity_type}).content
        logging.info(f"【llm_is_a_schema】llm_is_a_schema_assistant结果为{result}")
        one_to_one_triple(entity_type,result)
        logging.info(f"【neo4j操作】（{entity_type}->{result}）到图中")
    logging.info("【llm_is_a_schema】llm_is_a_schema完成")
    return {"messages":"llm_is_a_schema完成"}
def llm_check_tree_format_schema(state:State):
    def fix_graph(node):
        triple_list, node_list = get_connected_subgraph([node])
        graph_json_info = {"nodes": node_list, "edges": triple_list}
        logging.info(f"【fix_graph】当前待修复图:{graph_json_info}")
        llm_fix_graph_assistant = llm_fix_graph_prompt | llm
        llm_fix_graph_result = llm_fix_graph_assistant.invoke({"json_graph_info": str(graph_json_info)}).content
        logging.info(f"【fix_graph】llm_fix_graph_result结果:{llm_fix_graph_result}")
        fix_graph_result = json.loads(llm_fix_graph_result.replace('```json', '').replace('```', ''))
        logging.info(f"【fix_graph】修复后结果:{fix_graph_result}")
        del_nodes_triples(graph_json_info["edges"])
        logging.info(f"【fix_graph】删除旧边{graph_json_info['edges']}")
        add_nodes_triples(fix_graph_result["edges"])
        logging.info(f"【fix_graph】添加新边:{fix_graph_result['edges']}")
    while True:
        logging.info("【llm_check_tree_format_schema】检测是否有环")
        cycle_list=check_cycle()
        outdegree_list=check_outdegree()
        if cycle_list!=[]:
            logging.info(f"【llm_check_tree_format_schema】检测到有环，对{cycle_list[0]}所在子图进行修复")
            fix_graph(cycle_list[0])
            logging.info(f"【llm_check_tree_format_schema】检测到有环，对{cycle_list[0]}所在子图进行修复完成")
        elif outdegree_list!=[]:
            logging.info(f"【llm_check_tree_format_schema】检测到有出度大于1节点，对{outdegree_list[0]}所在子图进行修复")
            fix_graph(outdegree_list[0])
            logging.info(f"【llm_check_tree_format_schema】检测到有出度大于1节点，对{outdegree_list[0]}所在子图进行修复完成")
        else:
            logging.info("【llm_check_tree_format_schema】检测到没有环和出度大于1节点")
            break
    outdegree_zero_list=check_outdegree_zero()
    logging.info(f"【llm_check_tree_format_schema】检测到出度为0的节点为:{outdegree_zero_list},个数为{len(outdegree_zero_list)}")
    add_nodes(["绿色建筑评价规范"])
    one_to_many_triple(outdegree_zero_list,"绿色建筑评价规范")
    logging.info(f"【neo4j操作】添加关系{outdegree_zero_list}->绿色建筑评价规范")
    return {"messages": "本体模型构建完成"}


#disambiguation阶段
tools_disambiguation_process = disambiguation_ToolNode(tools=[tool_disambiguation,tool_not_disambiguation])
graph_builder.add_node("llm_disambiguation",llm_disambiguation)
graph_builder.add_node("llm_tool_disambiguation_diagnose",llm_tool_disambiguation_diagnose)
graph_builder.add_node("group_num_complete",group_num_complete)
graph_builder.add_node("retrieval_related_node",retrieval_related_node)
graph_builder.add_node("tools_disambiguation_process",tools_disambiguation_process)

#schema阶段
graph_builder.add_node("llm_schema",llm_schema)
graph_builder.add_node("llm_is_a_schema",llm_is_a_schema)
graph_builder.add_node("llm_check_tree_format_schema",llm_check_tree_format_schema)

# add_relation阶段
graph_builder.add_node("llm_relation",llm_relation)
graph_builder.add_node("llm_relation_diagnose",llm_relation_diagnose)
tools_relation_process=relation_ToolNode(tools=[tool_is_a,tool_hypernym_generation,tool_not_handle])
graph_builder.add_node("tools_relation_process",tools_relation_process)
graph_builder.add_node("in_graph_complete",in_graph_complete)
graph_builder.add_node("retrieval_related_node_2",retrieval_related_node_2)
graph_builder.add_node("llm_check_tree_format",llm_check_tree_format)
#disambiguation阶段
graph_builder.add_edge(START,"llm_disambiguation")
graph_builder.add_edge("llm_disambiguation","llm_tool_disambiguation_diagnose")
graph_builder.add_conditional_edges(
    "llm_tool_disambiguation_diagnose",
    disambiguation_route_tools,
    {"tools_disambiguation_process": "tools_disambiguation_process", "in_graph_complete": "in_graph_complete", "group_num_complete": "group_num_complete"},
)
graph_builder.add_edge("tools_disambiguation_process","llm_tool_disambiguation_diagnose")
graph_builder.add_edge("group_num_complete","retrieval_related_node")
graph_builder.add_edge("retrieval_related_node","llm_disambiguation")
#add_relation阶段
graph_builder.add_edge("llm_relation","llm_relation_diagnose")
graph_builder.add_conditional_edges(
    "llm_relation_diagnose",
    relation_route_tools,
    {"tools_relation_process":"tools_relation_process","llm_check_tree_format": "llm_check_tree_format"},
)
graph_builder.add_edge("tools_relation_process","llm_relation_diagnose")
graph_builder.add_conditional_edges("llm_check_tree_format",relation_route_to_end,{"in_graph_complete":"in_graph_complete", "llm_schema" : "llm_schema"})
graph_builder.add_edge("in_graph_complete","retrieval_related_node_2")
graph_builder.add_edge("retrieval_related_node_2","llm_relation")

#schema阶段
graph_builder.add_edge("llm_schema","llm_is_a_schema")
graph_builder.add_edge("llm_is_a_schema","llm_check_tree_format_schema")
graph_builder.add_edge("llm_check_tree_format_schema",END)




#记忆
memory = SqliteSaver(conn)
#编译图
graph = graph_builder.compile(checkpointer=memory)
if __name__ == "__main__":
    pass
