# Text2Onto-Agent: An Agent-Based End-to-End Automated Construction Method for Domain-Specific Ontology Models
##Environment
   - python 3.11
   - 
```bash
pip install requirement
```
## 1. T2OA Implementation
1. **Setup Configuration**  
   - Fill in LLM API key in `LLM.py`  
   - Fill in embedding model API key in `neo4j_database/cypher.py`(function `retrieve_similar_node`)  
   - Configure Neo4j parameters in `neo4j_conf.py`  
   - Execute `create_embedding_index` function in `neo4j_database/cypher.py` to create vector index in Neo4j

2. **Concept Extraction**  
   - Initial extraction: `ner/ner.py` (function `ner_1`)  
   - Iterative refinement: `ner/ner.py` (function `ner_2`)

3. **Graph Construction**  
   - Run `run_graph.py` for:  
     - Concept Disambiguation  
     - Relation Generation  
     - Schema Refinement  
   - Agent framework: `graph_struct.py`  
   - Prompt templates: `LLM.py`

## 2. Evaluation
1. Baseline reproduction: `evaluation/benchmark_onto/cluster.py`  
2. NER task based on ontology: `evaluation/compare_ner.py`  
3. Compute Uniqueness Score (US): `evaluation/compute_uniqueness.py`  
4. Compute Topic Stability Score (TS): `evaluation/LDA_git.py`

## 3. Results
**Final complete green building ontology model**: [`ontology_result_green_building.csv`](ontology_result_green_building.csv)
