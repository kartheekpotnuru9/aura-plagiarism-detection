"""
Academic Knowledge Graph construction module for Aura system
Extracts entities and relationships from academic papers
"""

import re
import networkx as nx
from typing import Dict, List, Tuple, Set
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from nltk.corpus import stopwords
from collections import Counter, defaultdict
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    print("Warning: spaCy not available. Using NLTK-only mode for knowledge graph.")
    spacy = None
    SPACY_AVAILABLE = False
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Download required NLTK data
try:
    nltk.data.find('averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

try:
    nltk.data.find('maxent_ne_chunker')
except LookupError:
    nltk.download('maxent_ne_chunker')

try:
    nltk.data.find('words')
except LookupError:
    nltk.download('words')

class KnowledgeGraphBuilder:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.academic_stopwords = {
            'paper', 'study', 'research', 'work', 'approach', 'method',
            'technique', 'algorithm', 'model', 'system', 'framework',
            'analysis', 'results', 'conclusion', 'discussion', 'introduction'
        }
        
        # Try to load spaCy model
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except (OSError, Exception) as e:
                print(f"Warning: spaCy model 'en_core_web_sm' could not be loaded: {e}")
                print("Some NLP features may be limited. Falling back to NLTK-only mode.")
                self.nlp = None
        else:
            self.nlp = None
        
        self.graph = nx.Graph()
        
        # Academic terms and methods patterns
        self.ml_methods = {
            'neural networks', 'deep learning', 'machine learning', 'artificial intelligence',
            'convolutional neural network', 'cnn', 'recurrent neural network', 'rnn',
            'transformer', 'bert', 'gpt', 'lstm', 'gru', 'svm', 'support vector machine',
            'random forest', 'decision tree', 'k-means', 'clustering', 'classification',
            'regression', 'supervised learning', 'unsupervised learning', 'reinforcement learning',
            'natural language processing', 'nlp', 'computer vision', 'cv'
        }
        
        self.research_areas = {
            'computer science', 'artificial intelligence', 'machine learning', 'data science',
            'natural language processing', 'computer vision', 'robotics', 'cybersecurity',
            'software engineering', 'human-computer interaction', 'database systems',
            'distributed systems', 'algorithms', 'theory', 'graphics', 'networking'
        }
    
    def build_knowledge_graph(self, papers_data: List[Dict]) -> nx.Graph:
        """Build knowledge graph from multiple papers"""
        self.graph.clear()
        
        for paper in papers_data:
            self._process_paper(paper)
        
        # Add inter-paper relationships
        self._add_citation_relationships(papers_data)
        self._add_similarity_relationships(papers_data)
        
        return self.graph
    
    def _process_paper(self, paper_data: Dict) -> None:
        """Process a single paper and add to knowledge graph"""
        paper_id = paper_data.get('id', f"paper_{hash(paper_data.get('title', ''))}")
        title = paper_data.get('title', '')
        content = paper_data.get('content', '')
        abstract = paper_data.get('abstract', '')
        authors = paper_data.get('authors', [])
        
        # Add paper node
        self.graph.add_node(paper_id, 
                           type='paper', 
                           title=title,
                           content_length=len(content),
                           abstract=abstract[:200] + '...' if len(abstract) > 200 else abstract)
        
        # Extract and add entities
        entities = self._extract_entities(content + ' ' + abstract)
        
        # Add author nodes and relationships
        for author in authors if isinstance(authors, list) else []:
            author_id = f"author_{author.replace(' ', '_').lower()}"
            self.graph.add_node(author_id, type='author', name=author)
            self.graph.add_edge(paper_id, author_id, relationship='authored_by', weight=1.0)
        
        # Add method/technique nodes and relationships
        methods = self._extract_methods(content + ' ' + abstract)
        for method in methods:
            method_id = f"method_{method.replace(' ', '_').lower()}"
            self.graph.add_node(method_id, type='method', name=method)
            self.graph.add_edge(paper_id, method_id, relationship='uses_method', weight=0.8)
        
        # Add topic nodes and relationships
        topics = self._extract_topics(content + ' ' + abstract)
        for topic, weight in topics:
            topic_id = f"topic_{topic.replace(' ', '_').lower()}"
            self.graph.add_node(topic_id, type='topic', name=topic)
            self.graph.add_edge(paper_id, topic_id, relationship='discusses_topic', weight=weight)
        
        # Add concept nodes from named entities
        for entity, entity_type in entities:
            entity_id = f"entity_{entity.replace(' ', '_').lower()}"
            self.graph.add_node(entity_id, type='concept', name=entity, entity_type=entity_type)
            self.graph.add_edge(paper_id, entity_id, relationship='mentions', weight=0.6)
    
    def _extract_entities(self, text: str) -> List[Tuple[str, str]]:
        """Extract named entities from text"""
        entities = []
        
        if self.nlp:
            # Use spaCy for better entity recognition
            doc = self.nlp(text[:10000])  # Limit text length for performance
            for ent in doc.ents:
                if ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT']:
                    entities.append((ent.text, ent.label_))
        else:
            # Fallback to NLTK
            sentences = sent_tokenize(text[:5000])  # Limit for performance
            for sentence in sentences[:20]:  # Limit number of sentences
                tokens = word_tokenize(sentence)
                pos_tags = pos_tag(tokens)
                chunks = ne_chunk(pos_tags, binary=False)
                
                for chunk in chunks:
                    if hasattr(chunk, 'label'):
                        entity_name = ' '.join([token for token, pos in chunk.leaves()])
                        entities.append((entity_name, chunk.label()))
        
        # Filter and clean entities
        filtered_entities = []
        for entity, entity_type in entities:
            entity = entity.strip()
            if (len(entity) > 2 and 
                entity.lower() not in self.stop_words and
                not entity.isdigit() and
                len(entity) < 50):
                filtered_entities.append((entity, entity_type))
        
        return list(set(filtered_entities))  # Remove duplicates
    
    def _extract_methods(self, text: str) -> Set[str]:
        """Extract machine learning methods and techniques"""
        text_lower = text.lower()
        found_methods = set()
        
        # Direct matching of known methods
        for method in self.ml_methods:
            if method in text_lower:
                found_methods.add(method)
        
        # Pattern-based extraction
        method_patterns = [
            r'\b([A-Z][a-z]+ [A-Z][a-z]+ [Nn]etwork)\b',  # e.g., "Convolutional Neural Network"
            r'\b([A-Z][a-z]+ [Ll]earning)\b',  # e.g., "Deep Learning"
            r'\b([A-Z][a-z]+ [Aa]lgorithm)\b',  # e.g., "Genetic Algorithm"
            r'\b([A-Z][a-z]+ [Mm]ethod)\b',  # e.g., "Monte Carlo Method"
            r'\b([A-Z][a-z]+ [Mm]odel)\b',  # e.g., "Hidden Markov Model"
        ]
        
        for pattern in method_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) > 5 and match.lower() not in self.academic_stopwords:
                    found_methods.add(match.lower())
        
        return found_methods
    
    def _extract_topics(self, text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Extract research topics using TF-IDF"""
        # Preprocess text
        sentences = sent_tokenize(text)
        
        if not sentences:
            return []
        
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 3),  # Include unigrams, bigrams, and trigrams
            min_df=1,
            max_df=0.8
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(sentences)
            feature_names = vectorizer.get_feature_names_out()
            
            # Get average TF-IDF scores
            mean_scores = np.mean(tfidf_matrix.toarray(), axis=0)
            
            # Get top topics
            top_indices = np.argsort(mean_scores)[-top_k:][::-1]
            topics = [(feature_names[i], mean_scores[i]) for i in top_indices if mean_scores[i] > 0.1]
            
            # Filter academic terms
            filtered_topics = []
            for topic, score in topics:
                if (len(topic) > 3 and 
                    not topic.isdigit() and
                    topic not in self.academic_stopwords and
                    any(char.isalpha() for char in topic)):
                    filtered_topics.append((topic, score))
            
            return filtered_topics
            
        except Exception as e:
            print(f"Error in topic extraction: {e}")
            return []
    
    def _add_citation_relationships(self, papers_data: List[Dict]) -> None:
        """Add citation relationships between papers"""
        # Simple citation detection based on title matching in references
        for i, paper1 in enumerate(papers_data):
            paper1_id = paper1.get('id', f"paper_{hash(paper1.get('title', ''))}")
            paper1_content = paper1.get('content', '').lower()
            
            for j, paper2 in enumerate(papers_data):
                if i != j:
                    paper2_id = paper2.get('id', f"paper_{hash(paper2.get('title', ''))}")
                    paper2_title = paper2.get('title', '').lower()
                    
                    # Check if paper2's title appears in paper1's content
                    if paper2_title and len(paper2_title) > 10 and paper2_title in paper1_content:
                        self.graph.add_edge(paper1_id, paper2_id, 
                                          relationship='cites', weight=0.9)
    
    def _add_similarity_relationships(self, papers_data: List[Dict]) -> None:
        """Add similarity relationships between papers based on content"""
        if len(papers_data) < 2:
            return
        
        # Extract abstracts for similarity comparison
        abstracts = []
        paper_ids = []
        
        for paper in papers_data:
            abstract = paper.get('abstract', '') or paper.get('content', '')[:500]
            if abstract:
                abstracts.append(abstract)
                paper_ids.append(paper.get('id', f"paper_{hash(paper.get('title', ''))}"))
        
        if len(abstracts) < 2:
            return
        
        try:
            # Create TF-IDF vectors
            vectorizer = TfidfVectorizer(stop_words='english', max_features=500)
            tfidf_matrix = vectorizer.fit_transform(abstracts)
            
            # Calculate cosine similarity
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Add similarity edges
            for i in range(len(paper_ids)):
                for j in range(i + 1, len(paper_ids)):
                    similarity = similarity_matrix[i][j]
                    if similarity > 0.3:  # Threshold for similarity
                        self.graph.add_edge(paper_ids[i], paper_ids[j],
                                          relationship='similar_to', weight=similarity)
        
        except Exception as e:
            print(f"Error in similarity calculation: {e}")
    
    def get_graph_statistics(self) -> Dict[str, any]:
        """Get statistics about the knowledge graph"""
        if not self.graph.nodes():
            return {}
        
        # Count nodes by type
        node_types = defaultdict(int)
        for node, data in self.graph.nodes(data=True):
            node_types[data.get('type', 'unknown')] += 1
        
        # Count edges by relationship
        edge_types = defaultdict(int)
        for u, v, data in self.graph.edges(data=True):
            edge_types[data.get('relationship', 'unknown')] += 1
        
        # Graph metrics
        stats = {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'node_types': dict(node_types),
            'edge_types': dict(edge_types),
            'average_degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes(),
            'density': nx.density(self.graph),
            'connected_components': nx.number_connected_components(self.graph)
        }
        
        return stats
    
    def find_related_papers(self, paper_id: str, max_results: int = 10) -> List[Dict]:
        """Find papers related to a given paper through the knowledge graph"""
        if paper_id not in self.graph:
            return []
        
        related = []
        
        # Get neighbors (directly connected nodes)
        neighbors = list(self.graph.neighbors(paper_id))
        
        # Find papers connected through shared entities
        for neighbor in neighbors:
            neighbor_neighbors = list(self.graph.neighbors(neighbor))
            for nn in neighbor_neighbors:
                if (nn != paper_id and 
                    self.graph.nodes[nn].get('type') == 'paper'):
                    
                    # Calculate relationship strength
                    path_length = nx.shortest_path_length(self.graph, paper_id, nn)
                    edge_data = self.graph.get_edge_data(neighbor, nn, {})
                    weight = edge_data.get('weight', 0.5)
                    
                    related.append({
                        'paper_id': nn,
                        'title': self.graph.nodes[nn].get('title', ''),
                        'relationship_strength': weight / path_length,
                        'connection_path': nx.shortest_path(self.graph, paper_id, nn),
                        'shared_entities': [neighbor]
                    })
        
        # Sort by relationship strength and return top results
        related.sort(key=lambda x: x['relationship_strength'], reverse=True)
        return related[:max_results]
    
    def export_graph_data(self) -> Dict[str, any]:
        """Export graph data for visualization"""
        nodes = []
        edges = []
        
        for node, data in self.graph.nodes(data=True):
            nodes.append({
                'id': node,
                'label': data.get('name', data.get('title', node)),
                'type': data.get('type', 'unknown'),
                'size': self.graph.degree(node),
                **data
            })
        
        for u, v, data in self.graph.edges(data=True):
            edges.append({
                'source': u,
                'target': v,
                'relationship': data.get('relationship', 'connected'),
                'weight': data.get('weight', 1.0)
            })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'statistics': self.get_graph_statistics()
        }