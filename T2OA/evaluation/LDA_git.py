from gensim import corpora
from gensim.models.ldamodel import LdaModel
from gensim.models import CoherenceModel
import math
from gensim.matutils import kullback_leibler
import jieba  # 替换nltk的分词器
import pickle
import pandas as pd
import json
from tqdm import tqdm

# 中文停用词列表（需要准备一个中文停用词文件）
with open('cn_stopword.txt', 'r', encoding='utf-8') as f:
    stop_words = set([line.strip() for line in f])

def preprocess(text):
    jieba.load_userdict("arc_dict.txt")
    # 使用jieba进行中文分词
    words = jieba.lcut(text)
    # 过滤停用词和非字母数字字符（中文可能需要调整过滤条件）
    return [word for word in words if word not in stop_words and len(word.strip()) > 1]
def train_lda(num_topics,texts):

    processed_texts = [preprocess(text) for text in texts]

    # 创建词典和语料库
    dictionary = corpora.Dictionary(processed_texts)
    corpus = [dictionary.doc2bow(text) for text in processed_texts]
    with open(f'./doc4_dictionary.pkl', 'wb') as f:
        pickle.dump(dictionary, f)

    # 训练LDA模型
    lda = LdaModel(corpus, num_topics=num_topics, id2word=dictionary,passes=15,random_state=23)
    # # # 计算主题一致性（使用 c_v 方法）
    # coherence_model = CoherenceModel(
    #     model=lda,  # LDA 模型
    #     texts=processed_texts,  # 预处理后的分词文本（列表形式）
    #     dictionary=dictionary,  # Gensim 词典
    #     coherence='c_v'  # 可选 'u_mass', 'c_v', 'c_uci', 'c_npmi'
    # )
    #
    # # 获取一致性分数
    # coherence_score = coherence_model.get_coherence()
    # print(f"Topic Coherence (c_v): {coherence_score}")

    with open(f'./doc4_lda.pkl', 'wb') as f:
        pickle.dump(lda, f)


def calculate_ts_score(doc,doc4, dictionary, lda):
    processed_source = preprocess(doc4)
    processed_triples = preprocess(doc)
    source_corpus = dictionary.doc2bow(processed_source)
    triples_corpus = dictionary.doc2bow(processed_triples)

    source_dist = lda.get_document_topics(source_corpus, minimum_probability=0)
    triples_dist = lda.get_document_topics(triples_corpus, minimum_probability=0)

    ts_score = math.exp(-kullback_leibler(source_dist, triples_dist))
    return ts_score
if __name__ == "__main__":
    import json
    def connect_text(data):
        text = ""
        l=0
        for key, value in data.items():
            l+=len(value)
            for i in value:
                text += i[0]+"、"
        print(f"len{l}")
        return text
    with open("compare_ner/my_result2.json", 'r', encoding='utf-8') as f:
        data1 = json.load(f)
    with open("compare_ner/benchmark_result.json", 'r', encoding='utf-8') as f:
        data2 = json.load(f)
    with open("ner第一轮.json", 'r', encoding='utf-8') as f:
        data3 = json.load(f)
    with open("ner第三轮.json", 'r', encoding='utf-8') as f:
        data4 = json.load(f)
    with open("ner第五轮.json", 'r', encoding='utf-8') as f:
        data5 = json.load(f)
    def read_chunk():
        with open('绿色建筑评价标准.txt', 'r', encoding='utf-8') as file:
            chunk_list = []
            chunk = []
            for line in file:
                line = line.strip()
                if line == "---":
                    chunk_str = "\n ".join(chunk)
                    chunk_list.append(chunk_str)
                    chunk = []
                else:
                    chunk.append(line)
        return chunk_list
    doc1 = connect_text(data1)
    doc2 = connect_text(data2)
    doc3 = connect_text(data3)
    doc4 = connect_text(data4)
    doc5 = connect_text(data5)
    doc_train = read_chunk()
    doc_text="".join(doc_train)
    scores = {
        'doc1': [],
        'doc2': [],
        'doc3': [],
        'doc4': [],
        'doc5': []
    }
    topic_num_list=[10,20,30,40,50,80,100,150,200]
    for topic_num in topic_num_list:
        print(f"当前主题数: {topic_num}")

        # 训练模型并加载
        train_lda(num_topics=topic_num, texts=doc_train)
        dictionary = pickle.load(open(f'./doc4_dictionary.pkl', 'rb'))
        lda_model = pickle.load(open(f'./doc4_lda.pkl', 'rb'))

        # 计算各文档分数
        doc1_score = calculate_ts_score(doc1, doc_text, dictionary, lda_model)
        doc2_score = calculate_ts_score(doc2, doc_text, dictionary, lda_model)
        doc3_score = calculate_ts_score(doc3, doc_text, dictionary, lda_model)
        doc4_score = calculate_ts_score(doc4, doc_text, dictionary, lda_model)
        doc5_score = calculate_ts_score(doc5, doc_text, dictionary, lda_model)

        # 存储分数
        scores['doc1'].append(doc1_score)
        scores['doc2'].append(doc2_score)
        scores['doc3'].append(doc3_score)
        scores['doc4'].append(doc4_score)
        scores['doc5'].append(doc5_score)

        # 转换为DataFrame并写入Excel
    df = pd.DataFrame.from_dict(
        scores,
        orient='index',
        columns=[str(num) for num in topic_num_list]
    )
    df.to_excel('ts_scores_noentity.xlsx', sheet_name='TS Scores')
    print("分数已保存至 ts_scores_noentity.xlsx")
