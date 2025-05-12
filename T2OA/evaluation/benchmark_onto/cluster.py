import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
from collections import defaultdict
from utils import get_embedding
from tqdm import tqdm
import json
from llm import llm,llm_cluster_labeling_prompt

def topic_clustering(dict_type_entity):
    # 参数设置（与论文完全一致）
    w_t = 0.5  # 主题标签权重
    w_k = 0.5  # 关键词权重
    theta = 1  # 主题出现次数阈值
    n = 3  # 每个聚类最小关键词数
    m = 9  # 聚类总关键词数阈值
    s = 0.05  # 阈值搜索步长

    print("=" * 50)
    print("Starting Topic Clustering Process")
    print(f"Initial Parameters: w_t={w_t}, w_k={w_k}, theta={theta}, n={n}, m={m}, s={s}")
    print(f"Total topics to process: {len(dict_type_entity)}")
    print("=" * 50)

    # 步骤1：生成主题嵌入
    print("\nStep 1: Generating topic embeddings...")
    topic_embeddings = []
    topic_info = []
    skipped_topics = 0

    for topic, keywords in tqdm(dict_type_entity.items(), desc="Processing topics"):
        if len(keywords) < theta:
            skipped_topics += 1
            continue  # 过滤低频主题

        try:
            # 获取主题标签嵌入
            topic_emb = np.array(get_embedding(topic))

            # 计算关键词嵌入质心
            keyword_embs = [np.array(get_embedding(kw)) for kw in keywords]
            centroid = np.mean(keyword_embs, axis=0)

            # 加权平均
            combined_emb = w_t * topic_emb + w_k * centroid
            topic_embeddings.append(combined_emb)
            topic_info.append({
                'topic': topic,
                'keywords': keywords,
                'kw_count': len(keywords)
            })
        except Exception as e:
            skipped_topics += 1
            continue

    print(f"\nCompleted Step 1: Generated embeddings for {len(topic_embeddings)} topics")
    print(f"Skipped {skipped_topics} topics (low frequency or embedding errors)")

    # 步骤2：层次聚类
    print("\nStep 2: Performing hierarchical clustering...")
    best_score = -1
    best_labels = None
    threshold_range = np.arange(0, 1.0 + s, s)

    print(f"Testing {len(threshold_range)} distance thresholds from 0 to 1.0 (step={s})")

    for threshold in tqdm(threshold_range, desc="Testing thresholds"):
        if threshold == 0: continue

        model = AgglomerativeClustering(
            n_clusters=None,
            metric='cosine',
            linkage='complete',
            distance_threshold=threshold
        )
        labels = model.fit_predict(topic_embeddings)

        if len(np.unique(labels)) < 2: continue

        score = silhouette_score(topic_embeddings, labels)
        if score > best_score:
            best_score = score
            best_labels = labels

    print(f"\nCompleted Step 2: Best silhouette score = {best_score:.4f}")
    print(f"Number of clusters found: {len(np.unique(best_labels))}")

    # 步骤3：后处理过滤
    print("\nStep 3: Post-processing and filtering clusters...")
    clusters = defaultdict(list)
    for label, info in zip(best_labels, topic_info):
        clusters[label].append(info)

    final_clusters = []
    for cluster_id, cluster in clusters.items():
        valid_topics = [t for t in cluster if t['kw_count'] >= n]
        total_kw = sum(t['kw_count'] for t in valid_topics)

        if total_kw >= m and len(valid_topics) > 0:
            final_clusters.append({
                'topics': valid_topics,
                'total_kw': total_kw
            })

    print(f"\nCompleted Step 3: Final number of valid clusters = {len(final_clusters)}")
    print("=" * 50)
    print("Clustering process completed successfully!")
    print("=" * 50)

    return final_clusters
def cluster_labeling(topic_list):
    cluster_labeling_assistant = llm_cluster_labeling_prompt | llm
    labeling_dict={}
    for topic_cluster in topic_list:
        print(topic_cluster)
        result = cluster_labeling_assistant.invoke({"topic_cluster": topic_cluster}).content
        print(result)
        labeling_dict[result]=topic_cluster
    with open("labeling_dict.json", 'w', encoding='utf-8') as f:
        json.dump(labeling_dict, f, ensure_ascii=False, indent=4)
    return labeling_dict


if __name__ == '__main__':
    print("Loading input data...")
    with open("dict_type_entity.json", 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("\nStarting clustering process...")
    result = topic_clustering(data)
    topic_list=[]
    with open("cluster_result.json", 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    for i in result:
        item_List=[]
        for j in i["topics"]:
            item_List.append(j["topic"])
        topic_list.append(item_List)
    with open("topic_list.json", 'w', encoding='utf-8') as f:
        json.dump(topic_list, f, ensure_ascii=False, indent=4)
    print(cluster_labeling(topic_list))