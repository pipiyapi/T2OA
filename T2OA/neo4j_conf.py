from langchain_neo4j import Neo4jGraph
graph = Neo4jGraph(
    url="bolt://localhost:7687",
    database="neo4j",
    username="neo4j",
    password="12345678"
)
