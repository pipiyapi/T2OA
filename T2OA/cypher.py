from neo4j_conf import graph
from utils import get_embedding
from langchain_community.vectorstores import Neo4jVector
from T2OA.my_embedding import SiliconFlowEmbeddings
from llm import llm,tree_format_prompt


def claer_graph():
    graph.query("""
    MATCH (n)
    DETACH DELETE n
    """)
    return
def add_nodes(node_name_list):
    if node_name_list==[]:
        return
    for node_name in node_name_list:
        node_embedding=get_embedding(node_name)
        query_return=graph.query(f"""
        MERGE (e:Entity_type {{entity_type_name: $node_name}})
        SET e.embedding = $embedding
        RETURN e
        """, params={"node_name": node_name,"embedding":node_embedding})
    return
def add_nodes_entity(node_name_list):
    if node_name_list==[]:
        return
    for node_name in node_name_list:
        node_embedding=get_embedding(node_name)
        query_return=graph.query(f"""
        MERGE (e:Entity {{entity_name: $node_name}})
        SET e.embedding = $embedding
        RETURN e
        """, params={"node_name": node_name,"embedding":node_embedding})
    return
def add_nodes_entity_type(node_name_list):
    if node_name_list==[]:
        return
    for node_name in node_name_list:
        node_embedding=get_embedding(node_name)
        query_return=graph.query(f"""
        MERGE (e:Entity_type {{entity_type_name: $node_name}})
        SET e.embedding = $embedding
        RETURN e
        """, params={"node_name": node_name,"embedding":node_embedding})
    return
def replace_node(replace_node_name, new_node_name):
    node_embedding = get_embedding(new_node_name)
    query_return = graph.query(
        """
        // 匹配原节点 A
        MATCH (A:Entity_type {entity_type_name: $replace_node_name})

        // 创建新节点 D
        CREATE (D:Entity_type {entity_type_name: $new_node_name})
        SET D.embedding = $embedding

        // 传递变量到后续操作
        WITH A, D

        // 继承 A 的 outgoing 关系
        MATCH (A)-[r]->(other)
        WITH D, r, other, type(r) AS rel_type, A
        CREATE (D)-[r2:rel_type]->(other)
        SET r2 = r

        // 传递变量到后续操作
        WITH A, D

        // 继承 A 的 incoming 关系
        MATCH (other)-[r]->(A)
        WITH D, r, other, type(r) AS rel_type, A
        CREATE (other)-[r2:rel_type]->(D)
        SET r2 = r

        // 删除原节点 A
        WITH A
        DETACH DELETE A
        """,
        params={
            "replace_node_name": replace_node_name,
            "new_node_name": new_node_name,
            "embedding": node_embedding
        }
    )
    return query_return
def delete_nodes(node_name_list):
    if node_name_list==[]:
        return
    for node_name in node_name_list:
        query_return=graph.query(f"""
        MATCH (e:Entity_type {{entity_type_name: $node_name}})
        DETACH DELETE e
        RETURN e
        """, params={"node_name": node_name})
    return
def one_to_many_triple(head_node_name_list,tail_node_name):
    for head_node_name in head_node_name_list:
        query_return=graph.query(f"""
        MATCH (head:Entity_type {{entity_type_name: $head_node_name}})
        MATCH (tail:Entity_type {{entity_type_name: $tail_node_name}})
        MERGE (head)-[:is_a]->(tail)
        """, params={"head_node_name": head_node_name,"tail_node_name": tail_node_name})
    return
def enitity_type_to_entity_triple(head_node_name_list,tail_node_name):
    for head_node_name in head_node_name_list:
        query_return=graph.query(f"""
        MATCH (head:Entity {{entity_name: $head_node_name}})
        MATCH (tail:Entity_type {{entity_type_name: $tail_node_name}})
        MERGE (head)-[:is_a]->(tail)
        """, params={"head_node_name": head_node_name,"tail_node_name": tail_node_name})
    return
def one_to_one_triple(head_node_name,tail_node_name):
    query_return=graph.query(f"""
    MATCH (head:Entity_type {{entity_type_name: $head_node_name}})
    MATCH (tail:Entity_type {{entity_type_name: $tail_node_name}})
    MERGE (head)-[:is_a]->(tail)
    """, params={"head_node_name": head_node_name,"tail_node_name": tail_node_name})
    return
def create_embedding_index():
    vector_dimensions=1024
    graph.query(
        """CREATE VECTOR INDEX Entity_type_embedding IF NOT EXISTS
            FOR (m:Entity_type)
            ON m.embedding
            OPTIONS {indexConfig: {
             `vector.dimensions`: $vector_dimensions,
             `vector.similarity_function`: 'cosine'
            }}
        """,
        params={"vector_dimensions": vector_dimensions}
    )
def retrieve_similar_node(node_name, query, idx_name):
    embeddings = SiliconFlowEmbeddings(api_key="****************")
    lc_vector = Neo4jVector.from_existing_index(
        embeddings,
        url="bolt://localhost:7687",
        database="neo4j",
        username="neo4j",
        password="12345678",
        index_name=idx_name,
        text_node_property="entity_type_name",
        embedding_node_property="embedding",
        search_type="vector"
    )

    docs = lc_vector.similarity_search_with_score(
        node_name,
        k=5
    )
    if not docs:
        return []
    return docs
def get_connected_subgraph(node_names:list):
    if node_names==[]:
        return [],[]
    triple_list = graph.query("""
            MATCH (start:Entity_type) WHERE start.entity_type_name IN $node_names
            MATCH (start)-[*]-(connected)
            WITH collect(DISTINCT start) AS starts, collect(DISTINCT connected) AS connecteds
            UNWIND (starts + connecteds) AS node
            WITH collect(DISTINCT node) AS subgraphNodes
            MATCH (h)-[r]->(t)
            WHERE h IN subgraphNodes AND t IN subgraphNodes
            RETURN h.entity_type_name AS from, 
                   type(r) AS relation, 
                   t.entity_type_name AS to
            """, params={"node_names": node_names})
    node_list = graph.query("""
            MATCH (start:Entity_type) WHERE start.entity_type_name IN $node_names
            // 匹配输入节点及其连通子图的所有节点
            MATCH (start)-[*]-(connected)
            // 收集所有唯一节点（包含输入节点）
            WITH collect(DISTINCT start) + collect(DISTINCT connected) AS subgraphNodes
            // 提取所有节点名字并返回列表
            UNWIND subgraphNodes AS node
            RETURN collect(DISTINCT node.entity_type_name) AS node_list
            """, params={"node_names": node_names})[0]["node_list"]
    return triple_list,node_list

def get_indegree_outdegree(node_name):
    query_result=graph.query("""
    MATCH (n:Entity_type {entity_type_name: $node_name})
    RETURN 
    n.entity_type_name AS entity_type_name,
    COUNT { (n)-->() } AS outDegree,
    COUNT { (n)<--() } AS inDegree;
    """, params={"node_name": node_name})
    outDegree=query_result[0]["outDegree"]
    inDegree=query_result[0]["inDegree"]
    return {"outDegree":outDegree,"inDegree":inDegree}
def get_connected_subgraph_tree_format(query_data):
    tree_format_llm =tree_format_prompt | llm
    result = tree_format_llm.invoke({"triple_list": str(query_data)}).content
    return result
def search_all_nodes():
    query_result=graph.query("""
    MATCH (n)
    RETURN collect(n.entity_type_name) AS node_names
    """)
    return query_result
def get_nodes_triples(entity_type_list: list) -> list:
    query_result = graph.query("""
    UNWIND $nodelist AS node
    MATCH (a:Entity_type {entity_type_name: node})-[r]->(b:Entity_type)
    WITH node, collect([a.entity_type_name, type(r), b.entity_type_name]) AS outgoing_triples
    MATCH (a:Entity_type {entity_type_name: node})<-[r]-(b:Entity_type)
    WITH outgoing_triples, collect([b.entity_type_name, type(r), a.entity_type_name]) AS incoming_triples
    WITH outgoing_triples + incoming_triples AS triples_per_node
    RETURN reduce(acc = [], triples IN collect(triples_per_node) | acc + triples) AS all_triples
    """, params={"nodelist": entity_type_list})
    return query_result[0].get("all_triples", [])
def del_nodes_triples(triple_dict: dict) -> None:
    if not triple_dict:
        return
    triple_list = []
    for triple in triple_dict:
        triple_list.append([triple['from'], triple['relation'], triple['to']])
    query_result = graph.query("""
    UNWIND $triple_list AS triple
    MATCH (a:Entity_type {entity_type_name: triple[0]})-[r]->(b:Entity_type {entity_type_name: triple[2]})
    WHERE type(r) = triple[1]
    DELETE r
    """, params={"triple_list": triple_list})
    return
def add_nodes_triples(triple_dict: dict) -> None:
    if not triple_dict:
        return
    triple_list = []
    for triple in triple_dict:
        triple_list.append([triple['from'], triple['relation'], triple['to']])
    query_result = graph.query("""
    UNWIND $triple_list AS triple
    MATCH (a:Entity_type {entity_type_name: triple[0]})
    MATCH (b:Entity_type {entity_type_name: triple[2]})
    CREATE (a)-[:is_a]->(b)
    """, params={"triple_list": triple_list})
    return
def check_cycle():
    query_result = graph.query("""
    MATCH p=(a)-[*]->(a)
    WHERE length(p) > 1
    WITH a, p
    RETURN COLLECT(DISTINCT a.entity_type_name) AS nodeNames
    """)
    return query_result[0]['nodeNames']
def check_outdegree():
    query_result = graph.query("""
    MATCH (n)-[r]->(m)
    WITH n, COUNT(r) AS out_degree
    WHERE out_degree > 1
    RETURN COLLECT(DISTINCT n.entity_type_name) AS nodeNames
    """)
    return query_result[0]['nodeNames']
def check_outdegree_zero():
    query_result = graph.query("""
    MATCH (n)
    WHERE NOT (n)-->()
    RETURN COLLECT(DISTINCT n.entity_type_name) AS nodeNames
    """)
    return query_result[0]['nodeNames']
def check_indegree_zero():
    query_result = graph.query("""
    MATCH (n)
    WHERE NOT ()-->(n)
    RETURN COLLECT(DISTINCT n.entity_type_name) AS nodeNames
    """)
    return query_result[0]['nodeNames']
def get_subtreenodes():
    query_result = graph.query("""
    MATCH (center {entity_type_name: '绿色建筑评价规范'})<-[*1..1]-(subtreeRoot)
    WITH subtreeRoot
    MATCH (subtreeRoot)<-[*]-(child)
    WITH subtreeRoot.entity_type_name AS rootType, collect(DISTINCT child.entity_type_name) AS childTypes
    RETURN apoc.map.fromLists(collect(rootType), collect(childTypes)) AS result
    """)
    return query_result[0]['result']
def get_all_triples():
    query_result = graph.query("""
    MATCH (a:Entity_type)-[r:is_a]->(b:Entity_type)
    RETURN [a.entity_type_name, type(r), b.entity_type_name] AS triple
    """)
    return [row['triple'] for row in query_result]
if __name__ == "__main__":
    # print(get_all_triples())
    # one_to_one_triple("照明相关参数","照明产品")
    # print(get_subtreenodes())
    # ll=[{'from': '建筑能耗指标', 'relation': 'is_a', 'to': '能耗指标'}, {'from': '能耗指标', 'relation': 'is_a', 'to': '能源利用指标'}, {'from': '能源利用指标', 'relation': 'is_a', 'to': '建筑能耗指标'}]
    # add_nodes_triples(ll)
    # triples=get_nodes_triples(["数值体系","功能分类"])
    # del_nodes_triples(triples)
    # add_nodes_triples(triples)
    # print(triples)
    # create_embedding_index()
    # retrieve_similar_node_list = retrieve_similar_node(node_name="建筑参数", idx_name="Entity_type_embedding")
    # print(retrieve_similar_node_list)
    # for item in retrieve_similar_node_list:
    #     print(item[0].page_content)
    #     print(item[1])
    #     print(type(item[1]))
    # retrieve_similar_node_name=retrieve_similar_node(node_name="建筑",query="",idx_name="Entity_type_embedding")
    # print(retrieve_similar_node_name)
    # print(get_indegree_outdegree("建筑"))
    # replace_node("建筑措施","建筑措")
    # triple_list,node_list=get_connected_subgraph("建筑工程")
    # print(triple_list)
    # print(node_list)
    # query_return=get_connected_subgraph("建筑要素")
    # print(get_connected_subgraph_tree_format(query_return))
    # retrieve_result=retrieve_similar_node(node_name="管子",query="",idx_name="Entity_type_embedding")
    # print(retrieve_result[0][0].page_content)
    # add_nodes(["建筑","水管","柱子","混凝土","钢筋","钢筋混凝土","混凝土结构","钢筋混凝土结构"])
    # logging.info(query_return)
    # logging.info(query_return)
    # one_to_many_triple("apple",["banana","orange"])
    # claer_graph()
    # query_return=del_nodes(["apple"])
    # logging.info(query_return)
    # triple_list, node_list=get_connected_subgraph(node_names=["标准规范","标准编号","建筑要素"])
    # print(triple_list)
    # print(node_list)
    pass
