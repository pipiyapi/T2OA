# Text2Onto-Agent: An Agent-Based End-to-End Automated Construction Method for Domain-Specific Ontology Models
##Environment
   - python 3.11
```bash
pip install requirement
```
## 1. T2OA Implementation
1. **Setup Configuration**  
   - Fill in LLM API key in `LLM.py`  
   - Fill in embedding model API key in `cypher.py`(function `retrieve_similar_node`)  and `utils.py`(function `get_embedding`)
   - Configure Neo4j parameters in `neo4j_conf.py`

2. **Upload Your Raw Text**  
   - Upload your raw text in `ner/data/绿色建筑评价标准.txt`

3. **Run the T2OA**
    -setting your own parameters in `run_T2OA.py` T2OA_config
    -run `python run_T2OA.py`

## 2. Evaluation
1. Baseline reproduction: `evaluation/benchmark_onto/cluster.py`  
2. NER task based on ontology: `evaluation/compare_ner.py`  
3. Compute Uniqueness Score (US): `evaluation/compute_uniqueness.py`  
4. Compute Topic Stability Score (TS): `evaluation/LDA_git.py`

## 3. Results
**Final complete green building ontology model**: [`ontology_result_green_building.csv`](ontology_result_green_building.csv)
