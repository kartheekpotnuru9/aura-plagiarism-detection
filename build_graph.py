import os
import arxiv
import spacy
from neo4j import GraphDatabase
import tarfile
import re

# --- 1. Configuration ---
NEO4J_URI = "neo4j://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "academic-graph"
SEARCH_QUERY = "cat:cs.LG OR cat:cs.AI"
MAX_RESULTS = 100
DOWNLOAD_DIR = "./arxiv_sources"

# --- 2. Helper Functions ---

def clean_tex_content(tex_content):
    text = re.sub(r'%.*?\n', '', tex_content)
    text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', text)
    text = re.sub(r'\\[a-zA-Z]+\[[^]]*\]', '', text)
    text = re.sub(r'\\[a-zA-Z]+\s?', '', text)
    text = re.sub(r'\$\$.*?\$\$', '', text, flags=re.DOTALL)
    text = re.sub(r'\$.*?\$', '', text)
    text = re.sub(r'\\begin\{[a-zA-Z\*]+\}.*?\\end\{[a-zA-Z\*]+\}', '', text, flags=re.DOTALL)
    text = re.sub(r'[\{\}]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_text_from_source(source_path):
    main_tex_content = ""
    try:
        with tarfile.open(source_path, 'r:gz') as tar:
            tex_files = [f for f in tar.getnames() if f.endswith('.tex')]
            if not tex_files: return ""
            main_tex_file = max(tex_files, key=lambda f: tar.getmember(f).size)
            extracted_file = tar.extractfile(main_tex_file)
            if extracted_file:
                main_tex_content = extracted_file.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error processing source file {source_path}: {e}")
        return ""
    return clean_tex_content(main_tex_content)

def extract_key_phrases(text, nlp_model):
    nlp_model.max_length = len(text) + 100
    doc = nlp_model(text)
    phrases = [chunk.text for chunk in doc.noun_chunks if 1 < len(chunk.text.split()) < 5]
    return list(set(phrases[:15]))

def write_to_neo4j(tx, paper_info):
    tx.run("""
        MERGE (p:Paper {paper_id: $paper_id})
        SET p.title = $title, p.full_text = $text
        """,
        paper_id=paper_info['paper_id'],
        title=paper_info['title'],
        text=paper_info['full_text']
    )
    for author_name in paper_info['authors']:
        tx.run("MERGE (a:Author {name: $author_name}) MERGE (a)-[:WROTE]->(p:Paper {paper_id: $paper_id})",
               author_name=author_name, paper_id=paper_info['paper_id'])
    for concept_name in paper_info['concepts']:
        tx.run("MERGE (c:Concept {name: $concept_name}) MERGE (p:Paper {paper_id: $paper_id})-[:HAS_CONCEPT]->(c)",
               concept_name=concept_name, paper_id=paper_info['paper_id'])

# --- 3. Main Execution Logic ---
if __name__ == "__main__":
    if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)
    print("Starting data ingestion process using LaTeX source...")
    nlp = spacy.load("en_core_web_sm")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    print(f"Searching arXiv for '{SEARCH_QUERY}'...")
    search = arxiv.Search(query=SEARCH_QUERY, max_results=MAX_RESULTS, sort_by=arxiv.SortCriterion.SubmittedDate)
    results = list(arxiv.Client().results(search))
    print(f"Found {len(results)} papers to process.")

    for paper in results:
        source_path = ""
        try:
            print(f"\nProcessing: '{paper.title}' (ID: {paper.get_short_id()})")
            filename = f"{paper.get_short_id()}.tar.gz"
            source_path = paper.download_source(dirpath=DOWNLOAD_DIR, filename=filename)
            full_text = extract_text_from_source(source_path)
            if not full_text: continue

            concepts = extract_key_phrases(full_text, nlp)
            paper_data = {
                'paper_id': paper.get_short_id(), # Use the unique ID
                'title': paper.title,
                'authors': [author.name for author in paper.authors],
                'concepts': concepts,
                'full_text': full_text
            }
            with driver.session() as session:
                session.execute_write(write_to_neo4j, paper_data)
            print(f"  Successfully wrote '{paper.title}' to Neo4j.")
        except Exception as e:
            print(f"  An error occurred while processing '{paper.title}': {e}")
        finally:
            if source_path and os.path.exists(source_path): os.remove(source_path)

    driver.close()
    print("\nData ingestion process complete.")
