import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
from Levenshtein import distance as levenshtein_distance
from collections import defaultdict
import json
def compute_distance_matrix(str_list: list) -> np.ndarray:
    """计算绝对Levenshtein距离矩阵"""
    n = len(str_list)
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            dist_matrix[i][j] = dist_matrix[j][i] = levenshtein_distance(str_list[i], str_list[j])
    return dist_matrix


def balanced_hierarchical_clustering(str_list: list, n_clusters: int) -> list:
    """带均衡优化的层次聚类"""
    # 计算距离矩阵
    dist_matrix = compute_distance_matrix(str_list)

    # 层次聚类
    condensed_dist = squareform(dist_matrix)
    Z = linkage(condensed_dist, method='complete')  # 全链接生成紧凑簇
    initial_labels = fcluster(Z, t=n_clusters, criterion='maxclust')

    # 初始分组
    clusters = defaultdict(list)
    for idx, label in enumerate(initial_labels):
        clusters[label].append(str_list[idx])
    clustered = list(clusters.values())

    # 动态均衡处理
    target_avg = len(str_list) / n_clusters
    final_clusters = []
    pending = []

    # 处理过大簇
    for cluster in clustered:
        if len(cluster) > target_avg * 1.5:  # 超过平均大小1.5倍的进行拆分
            sub_dist = compute_distance_matrix(cluster)
            sub_Z = linkage(squareform(sub_dist), 'complete')
            sub_labels = fcluster(sub_Z, t=2, criterion='maxclust')
            sub_clusters = defaultdict(list)
            for i, lbl in enumerate(sub_labels):
                sub_clusters[lbl].append(cluster[i])
            pending.extend(sub_clusters.values())
        else:
            pending.append(cluster)

    # 合并过小簇
    pending.sort(key=len, reverse=True)
    small_clusters = [c for c in pending if len(c) < target_avg * 0.5]
    other_clusters = [c for c in pending if len(c) >= target_avg * 0.5]

    # 构建相似度矩阵用于合并
    if small_clusters:
        centroid_distances = []
        for i, sc in enumerate(small_clusters):
            min_dist = float('inf')
            for j, oc in enumerate(other_clusters):
                dist = min(levenshtein_distance(s, t) for s in sc for t in oc)
                if dist < min_dist:
                    min_dist = dist
                    min_idx = j
            centroid_distances.append((min_dist, i, min_idx))

        # 按距离排序并合并
        centroid_distances.sort()
        for _, s_idx, o_idx in centroid_distances:
            other_clusters[o_idx].extend(small_clusters[s_idx])

    final_clusters = other_clusters[:n_clusters]  # 确保最终数量

    return sorted(final_clusters, key=lambda x: (len(x), x[0]), reverse=True)


# 使用示例
if __name__ == "__main__":
    with open("entity_type_unprocessed.json", 'r', encoding='utf-8') as f:
        strings = json.load(f)

    clustered = balanced_hierarchical_clustering(strings, 100)

    # 统计分布
    sizes = [len(c) for c in clustered]
    print(f"最大簇: {max(sizes)}, 最小簇: {min(sizes)}, 平均: {sum(sizes) / len(sizes):.1f}")

    with open("balanced_clusters.json", 'w', encoding='utf-8') as f:
        json.dump(clustered, f, ensure_ascii=False, indent=4)
    entity_list=[]
    for i in clustered:
        entity_list.extend(i)
    with open("balanced_clusters.json", 'w', encoding='utf-8') as f:
        json.dump(clustered, f, ensure_ascii=False, indent=4)
    with open("entity_type_unprocessed.json", 'w', encoding='utf-8') as f:
        json.dump(entity_list, f, ensure_ascii=False, indent=4)