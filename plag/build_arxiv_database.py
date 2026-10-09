"""
Improved arXiv Paper Database Builder for Aura System
Downloads ML papers from arXiv and populates the SQLite database
"""

import os
import sys
import time
import requests
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import re
from io import BytesIO
import gzip
from urllib.parse import quote

# Add the current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from modules import PDFProcessor, KnowledgeGraphBuilder
from utils import setup_logging, clean_text, extract_keywords

class ArxivPaperFetcher:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.pdf_processor = PDFProcessor()
        self.kg_builder = KnowledgeGraphBuilder()
        self.logger = setup_logging("INFO")
        
        # ArXiv API configuration
        self.base_url = "http://export.arxiv.org/api/query"
        self.delay_between_requests = 3  # seconds (arXiv rate limit)
        
        # ML-focused search queries
        self.ml_categories = [
            "cs.LG",  # Machine Learning
            "cs.AI",  # Artificial Intelligence
            "cs.CV",  # Computer Vision
            "cs.CL",  # Computation and Language (NLP)
            "cs.IR",  # Information Retrieval
            "stat.ML"  # Machine Learning (Statistics)
        ]
        
        # Popular ML keywords for filtering
        self.ml_keywords = {
            'deep learning', 'neural networks', 'machine learning', 'artificial intelligence',
            'convolutional neural', 'recurrent neural', 'transformer', 'attention mechanism',
            'reinforcement learning', 'supervised learning', 'unsupervised learning',
            'natural language processing', 'computer vision', 'image classification',
            'object detection', 'generative adversarial', 'autoencoder', 'bert', 'gpt',
            'random forest', 'support vector', 'clustering', 'regression', 'classification',
            'gradient descent', 'backpropagation', 'feature extraction', 'dimensionality reduction',
            'cross validation', 'overfitting', 'regularization', 'optimization'
        }
    
    def build_search_query(self, category: str, max_results: int = 50) -> str:
        """Build arXiv API search query"""
        # Use simpler query without date range to avoid parsing issues
        query = f"cat:{category}"
        encoded_query = quote(query)
        
        return f"{self.base_url}?search_query={encoded_query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
    
    def fetch_papers_metadata(self, category: str, max_results: int = 50) -> List[Dict]:
        """Fetch paper metadata from arXiv API"""
        url = self.build_search_query(category, max_results)
        
        try:
            self.logger.info(f"Fetching papers from category {category}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            
            papers = []
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                paper_data = self.parse_paper_entry(entry)
                if paper_data and self.is_relevant_ml_paper(paper_data):
                    papers.append(paper_data)
            
            self.logger.info(f"Found {len(papers)} relevant ML papers from {category}")
            return papers
            
        except Exception as e:
            self.logger.error(f"Error fetching papers from {category}: {e}")
            return []
    
    def parse_paper_entry(self, entry) -> Optional[Dict]:
        """Parse individual paper entry from arXiv XML"""
        try:
            # Namespaces
            atom_ns = '{http://www.w3.org/2005/Atom}'
            arxiv_ns = '{http://arxiv.org/schemas/atom}'
            
            # Extract basic information
            paper_id = entry.find(f'{atom_ns}id').text.split('/')[-1]
            title = entry.find(f'{atom_ns}title').text.strip()
            summary = entry.find(f'{atom_ns}summary').text.strip()
            
            # Extract authors
            authors = []
            for author in entry.findall(f'{atom_ns}author'):
                name = author.find(f'{atom_ns}name').text.strip()
                authors.append(name)
            
            # Extract categories
            categories = []
            for category in entry.findall(f'{atom_ns}category'):
                categories.append(category.get('term'))
            
            # Extract published date
            published = entry.find(f'{atom_ns}published').text
            
            # Try to get PDF link
            pdf_url = None
            for link in entry.findall(f'{atom_ns}link'):
                if link.get('type') == 'application/pdf':
                    pdf_url = link.get('href')
                    break
            
            return {
                'arxiv_id': paper_id,
                'title': clean_text(title),
                'abstract': clean_text(summary),
                'authors': authors,
                'categories': categories,
                'published_date': published,
                'pdf_url': pdf_url
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing paper entry: {e}")
            return None
    
    def is_relevant_ml_paper(self, paper_data: Dict) -> bool:
        """Check if paper is relevant to ML domain"""
        # Check categories
        if any(cat in self.ml_categories for cat in paper_data['categories']):
            return True
        
        # Check title and abstract for ML keywords
        text_to_check = (paper_data['title'] + ' ' + paper_data['abstract']).lower()
        
        # Count ML keyword matches
        keyword_matches = sum(1 for keyword in self.ml_keywords if keyword in text_to_check)
        
        # Consider relevant if has at least 2 ML keywords
        return keyword_matches >= 2
    
    def download_paper_content(self, paper_data: Dict) -> Optional[str]:
        """Download and extract text content from paper"""
        if not paper_data.get('pdf_url'):
            return None
        
        try:
            # Download PDF
            response = requests.get(paper_data['pdf_url'], timeout=60)
            response.raise_for_status()
            
            # Create a file-like object
            pdf_file = BytesIO(response.content)
            
            # Extract text using our PDF processor
            extraction_result = self.pdf_processor.extract_text_from_pdf(pdf_file)
            
            if extraction_result['success']:
                return extraction_result['text']
            else:
                self.logger.warning(f"Failed to extract text from {paper_data['arxiv_id']}: {extraction_result.get('error')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error downloading/processing {paper_data['arxiv_id']}: {e}")
            return None
    
    def generate_paper_hash(self, paper_data: Dict) -> str:
        """Generate unique hash for paper"""
        content = f"{paper_data['arxiv_id']}_{paper_data['title']}_{paper_data['abstract']}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def add_paper_to_database(self, paper_data: Dict, content: str = None) -> Optional[int]:
        """Add paper to database"""
        try:
            # Use abstract as content if full text not available
            text_content = content or paper_data['abstract']
            
            # Generate file hash
            file_hash = self.generate_paper_hash(paper_data)
            
            # Check if paper already exists
            existing_paper = self.db_manager.get_paper_by_hash(file_hash)
            if existing_paper:
                self.logger.info(f"Paper {paper_data['arxiv_id']} already exists in database")
                return existing_paper['id']
            
            # Extract keywords from content
            keywords = extract_keywords(text_content, top_n=15)
            
            # Add paper to database
            paper_id = self.db_manager.add_paper(
                title=paper_data['title'],
                content=text_content,
                abstract=paper_data['abstract'],
                authors=paper_data['authors'],
                keywords=keywords,
                file_hash=file_hash,
                venue=f"arXiv:{paper_data['arxiv_id']}"
            )
            
            # Add authors to database
            for author_name in paper_data['authors']:
                author_id = self.db_manager.add_author(
                    name=author_name,
                    research_areas=paper_data['categories']
                )
            
            # Add topics/categories
            for category in paper_data['categories']:
                topic_id = self.db_manager.add_topic(
                    name=category,
                    category='arxiv_category',
                    description=f"arXiv category: {category}"
                )
            
            # Add extracted keywords as topics
            for keyword in keywords:
                topic_id = self.db_manager.add_topic(
                    name=keyword,
                    category='keyword',
                    description=f"Extracted keyword from paper content"
                )
            
            self.logger.info(f"Successfully added paper {paper_data['arxiv_id']} to database")
            return paper_id
            
        except Exception as e:
            self.logger.error(f"Error adding paper {paper_data['arxiv_id']} to database: {e}")
            return None
    
    def build_paper_database(self, total_papers: int = 100) -> Dict:
        """Main function to build paper database"""
        self.logger.info(f"Starting to build database with {total_papers} ML papers from arXiv")
        
        papers_per_category = max(1, total_papers // len(self.ml_categories))
        added_papers = 0
        failed_papers = 0
        skipped_papers = 0
        
        results = {
            'total_requested': total_papers,
            'successfully_added': 0,
            'failed_downloads': 0,
            'already_existed': 0,
            'categories_processed': []
        }
        
        for category in self.ml_categories:
            if added_papers >= total_papers:
                break
                
            self.logger.info(f"\nProcessing category: {category}")
            
            # Fetch papers metadata
            papers_metadata = self.fetch_papers_metadata(category, papers_per_category + 10)  # Get extra for filtering
            
            category_results = {
                'category': category,
                'fetched': len(papers_metadata),
                'added': 0,
                'failed': 0,
                'skipped': 0
            }
            
            for paper_data in papers_metadata:
                if added_papers >= total_papers:
                    break
                
                try:
                    self.logger.info(f"Processing: {paper_data['title'][:60]}... ({paper_data['arxiv_id']})")
                    
                    # Try to download full content
                    content = self.download_paper_content(paper_data)
                    
                    # Add to database
                    paper_id = self.add_paper_to_database(paper_data, content)
                    
                    if paper_id:
                        added_papers += 1
                        category_results['added'] += 1
                        self.logger.info(f"✅ Added paper {added_papers}/{total_papers}")
                    else:
                        failed_papers += 1
                        category_results['failed'] += 1
                        self.logger.warning(f"❌ Failed to add paper")
                    
                    # Rate limiting
                    time.sleep(self.delay_between_requests)
                    
                except Exception as e:
                    self.logger.error(f"Error processing paper {paper_data.get('arxiv_id', 'unknown')}: {e}")
                    failed_papers += 1
                    category_results['failed'] += 1
            
            results['categories_processed'].append(category_results)
            self.logger.info(f"Category {category} completed: {category_results['added']} papers added")
        
        # Update final results
        results['successfully_added'] = added_papers
        results['failed_downloads'] = failed_papers
        
        # Get database statistics
        db_stats = self.db_manager.get_database_stats()
        
        self.logger.info(f"\n📊 Database Building Complete!")
        self.logger.info(f"Successfully added: {added_papers} papers")
        self.logger.info(f"Failed downloads: {failed_papers} papers")
        self.logger.info(f"Total papers in database: {db_stats.get('papers', 0)}")
        self.logger.info(f"Total authors in database: {db_stats.get('authors', 0)}")
        self.logger.info(f"Total topics in database: {db_stats.get('topics', 0)}")
        
        return results

def main():
    """Main execution function"""
    print("🚀 Starting Aura Paper Database Builder")
    print("Fetching ML papers from arXiv...")
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Create fetcher
    fetcher = ArxivPaperFetcher(db_manager)
    
    # Build database with 100 papers
    results = fetcher.build_paper_database(total_papers=100)
    
    print("\n🎉 Database building completed!")
    print(f"Check the results above for details.")
    
    # Optionally build knowledge graph relationships
    build_kg = input("\n🕸️ Build knowledge graph relationships? (y/n): ").lower().strip()
    if build_kg in ['y', 'yes']:
        print("Building knowledge graph relationships...")
        try:
            papers = db_manager.get_all_papers()
            if papers:
                kg_builder = KnowledgeGraphBuilder()
                graph = kg_builder.build_knowledge_graph(papers)
                stats = kg_builder.get_graph_statistics()
                print(f"✅ Knowledge graph built with {stats.get('total_nodes', 0)} nodes and {stats.get('total_edges', 0)} edges")
            else:
                print("⚠️ No papers found in database to build knowledge graph")
        except Exception as e:
            print(f"❌ Error building knowledge graph: {e}")
    
    return results

if __name__ == "__main__":
    main()