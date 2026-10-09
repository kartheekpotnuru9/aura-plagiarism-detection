# import pandas as pd
# from neo4j import GraphDatabase

# # --- 1. Configuration ---
# # Neo4j Credentials - Use the same credentials as your build script
# NEO4J_URI = "neo4j://localhost:7687"
# NEO4J_USER = "neo4j"
# NEO4J_PASSWORD = "academic-graph" 

# # --- 2. Main Execution Logic ---

# if __name__ == "__main__":
#     print("Starting graph export process...")
    
#     # Initialize Neo4j Driver
#     driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

#     with driver.session() as session:
#         # Query 1: Get all nodes and their properties.
#         # We assign a unique ID to each node for easier lookup in the ML model.
#         # The 'full_text' property is included for Paper nodes and is empty for others.
#         print("Exporting nodes...")
#         nodes_query = """
#         MATCH (p:Paper)
#         RETURN id(p) AS nodeId, p.title AS title, p.full_text AS text, labels(p)[0] AS label
#         UNION
#         MATCH (a:Author)
#         RETURN id(a) AS nodeId, a.name AS title, '' AS text, labels(a)[0] AS label
#         UNION
#         MATCH (c:Concept)
#         RETURN id(c) AS nodeId, c.name AS title, '' AS text, labels(c)[0] AS label
#         """
#         nodes_result = session.run(nodes_query)
#         nodes_df = pd.DataFrame([record.data() for record in nodes_result])
        
#         # Save nodes to CSV
#         nodes_df.to_csv("nodes.csv", index=False)
#         print(f"  Successfully exported {len(nodes_df)} nodes to nodes.csv")

#         # Query 2: Get all relationships (edges)
#         print("Exporting relationships...")
#         rels_query = """
#         MATCH (source)-[r]->(target)
#         RETURN id(source) AS source, id(target) AS target, type(r) AS type
#         """
#         rels_result = session.run(rels_query)
#         rels_df = pd.DataFrame([record.data() for record in rels_result])
        
#         # Save relationships to CSV
#         rels_df.to_csv("relationships.csv", index=False)
#         print(f"  Successfully exported {len(rels_df)} relationships to relationships.csv")

#     # Close the Neo4j connection
#     driver.close()
#     print("\nGraph export process complete.")
    

import pandas as pd
from neo4j import GraphDatabase

# --- 1. Configuration ---
NEO4J_URI = "neo4j://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "academic-graph" 

# --- 2. Main Execution Logic ---

if __name__ == "__main__":
    print("Starting graph export process...")
    
    # Initialize Neo4j Driver
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session() as session:
        # --- DEBUGGING: Check node counts first ---
        paper_count = session.run("MATCH (p:Paper) RETURN count(p) AS count").single()["count"]
        author_count = session.run("MATCH (a:Author) RETURN count(a) AS count").single()["count"]
        concept_count = session.run("MATCH (c:Concept) RETURN count(c) AS count").single()["count"]
        
        print(f"Nodes in Neo4j: Papers={paper_count}, Authors={author_count}, Concepts={concept_count}")
        # --- END DEBUGGING ---

        # Query 1: Get all nodes and their properties.
        print("Exporting nodes...")
        nodes_query = """
        MATCH (p:Paper)
        RETURN id(p) AS nodeId, p.title AS title, p.full_text AS text, labels(p)[0] AS label
        UNION ALL  // Use UNION ALL to ensure all records are included, even if they have identical properties (unlikely for IDs)
        MATCH (a:Author)
        RETURN id(a) AS nodeId, a.name AS title, '' AS text, labels(a)[0] AS label
        UNION ALL
        MATCH (c:Concept)
        RETURN id(c) AS nodeId, c.name AS title, '' AS text, labels(c)[0] AS label
        """
        nodes_result = session.run(nodes_query)
        nodes_df = pd.DataFrame([record.data() for record in nodes_result])
        
        # Save nodes to CSV
        nodes_df.to_csv("nodes.csv", index=False)
        print(f"   Successfully exported {len(nodes_df)} nodes to nodes.csv")

        # Query 2: Get all relationships (edges)
        print("Exporting relationships...")
        rels_query = """
        MATCH (source)-[r]->(target)
        RETURN id(source) AS source, id(target) AS target, type(r) AS type
        """
        rels_result = session.run(rels_query)
        rels_df = pd.DataFrame([record.data() for record in rels_result])
        
        # Save relationships to CSV
        rels_df.to_csv("relationships.csv", index=False)
        print(f"   Successfully exported {len(rels_df)} relationships to relationships.csv")

    # Close the Neo4j connection
    driver.close()
    print("\nGraph export process complete.")