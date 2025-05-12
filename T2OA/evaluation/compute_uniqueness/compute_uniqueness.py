from utils import get_embedding
import numpy as np
from neo4j_database.cypher import search_all_nodes,get_subtreenodes,check_indegree_zero
def cosine_similarity(v1, v2):
    """计算两个向量的余弦相似度"""
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


def calculate_us(strings, phi):
    """计算u(TD)分数"""
    n = len(strings)
    if n < 2:
        return 0  # 如果列表元素少于2个，直接返回0

    # 获取所有字符串的嵌入向量
    embeddings = []
    for s in strings:
        emb = get_embedding(s)
        if emb is None:
            raise Exception(f"Failed to get embedding for string: {s}")
        embeddings.append(emb)

    # 计算所有两两组合的余弦相似度
    count = 0
    total_pairs = 0

    for i in range(n):
        for j in range(i + 1, n):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            if sim < phi:
                count += 1
            total_pairs += 1

    # 计算u(TD)分数
    if total_pairs == 0:
        return 0
    us = count / total_pairs
    return us

def calculate_subtree_us(tree_dict, phi):
    """计算u(TD)分数"""
    n = len(tree_dict)
    if n < 2:
        return 0  # 如果列表元素少于2个，直接返回0

    # 获取所有字符串的嵌入向量
    embeddings = []
    for k,v in tree_dict.items():
        c_embedding = []
        for c in v:
            c_embedding.append(get_embedding(c))
        # c=" ".join(v)
        # emb = get_embedding(c)
        # embeddings.append(emb)
        #平均
        avg_embedding = np.mean(c_embedding, axis=0)
        embeddings.append(avg_embedding)
        #相加归一化
        # summed_vector = np.sum(c_embedding, axis=0)
        # normalized_vector = summed_vector / np.linalg.norm(summed_vector)
        # embeddings.append(normalized_vector)
        #拼接

    # 计算所有两两组合的余弦相似度
    count = 0
    total_pairs = 0

    for i in range(n):
        for j in range(i + 1, n):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            if sim < phi:
                count += 1
            total_pairs += 1

    # 计算u(TD)分数
    if total_pairs == 0:
        return 0
    us = count / total_pairs
    return us
# 示例用法
if __name__ == "__main__":
    import json
    with open("labeling_dict.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    beachmark_list=[]
    for key,value in data.items():
        beachmark_list.append(key)
        beachmark_list.extend(value)

    # my_result=search_all_nodes()[0]['node_names']
    phi_list = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    # for phi in phi_list:
    #     print(f"phi: {phi}")
    #     my_result_us= calculate_us(my_result, phi)
    #     beachmark_us= calculate_us(beachmark_list, phi)
    #     print(f"us for my_result: {my_result_us}")
    #     print(f"us for beachmark: {beachmark_us}")
    my_result_subtree=get_subtreenodes()
    indegree_zero=check_indegree_zero()
    new_my_result_subtree={}
    for k,v in my_result_subtree.items():
        new_list=[]
        for i in v:
            if i in indegree_zero:
                new_list.append(i)
        new_my_result_subtree[k]=new_list
    for phi in phi_list:
        print(f"phi: {phi}")
        my_result_us= calculate_subtree_us(new_my_result_subtree, phi)
        beachmark_us= calculate_subtree_us(data, phi)
        print(f"us for my_result subtree: {my_result_us}")
        print(f"us for beachmark subtree: {beachmark_us}")


