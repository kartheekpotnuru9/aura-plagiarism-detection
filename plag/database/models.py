"""
Database models for Aura Academic Plagiarism Detection System
Implements Academic Knowledge Graph with papers, authors, topics, and relationships
"""

import sqlite3
import json
import datetime
from typing import List, Dict, Any, Optional
import os
from config import DATABASE_PATH, BACKUP_PATH

class DatabaseManager:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.ensure_database_exists()
        self.create_tables()
    
    def ensure_database_exists(self):
        """Ensure the database directory and file exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            open(self.db_path, 'a').close()
    
    def get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_tables(self):
        """Create all necessary tables for the Academic Knowledge Graph"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Papers table - stores academic papers
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    abstract TEXT,
                    content TEXT,
                    authors TEXT,  -- JSON list of authors
                    publication_date DATE,
                    venue TEXT,
                    keywords TEXT,  -- JSON list of keywords
                    file_hash TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Authors table - stores author information
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS authors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    affiliation TEXT,
                    email TEXT,
                    research_areas TEXT,  -- JSON list of research areas
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Topics table - stores research topics and methods
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    category TEXT,  -- e.g., 'method', 'topic', 'technique'
                    description TEXT,
                    frequency INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Paper-Author relationships
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS paper_authors (
                    paper_id INTEGER,
                    author_id INTEGER,
                    author_order INTEGER,
                    PRIMARY KEY (paper_id, author_id),
                    FOREIGN KEY (paper_id) REFERENCES papers (id),
                    FOREIGN KEY (author_id) REFERENCES authors (id)
                )
            ''')
            
            # Paper-Topic relationships (Knowledge Graph edges)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS paper_topics (
                    paper_id INTEGER,
                    topic_id INTEGER,
                    weight REAL DEFAULT 1.0,
                    context TEXT,  -- Where this topic appears in the paper
                    PRIMARY KEY (paper_id, topic_id),
                    FOREIGN KEY (paper_id) REFERENCES papers (id),
                    FOREIGN KEY (topic_id) REFERENCES topics (id)
                )
            ''')
            
            # Similarity relationships between papers
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS paper_similarities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paper1_id INTEGER,
                    paper2_id INTEGER,
                    similarity_score REAL,
                    similarity_type TEXT,  -- 'semantic', 'structural', 'citation'
                    matching_segments TEXT,  -- JSON of matching text segments
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (paper1_id) REFERENCES papers (id),
                    FOREIGN KEY (paper2_id) REFERENCES papers (id),
                    UNIQUE(paper1_id, paper2_id, similarity_type)
                )
            ''')
            
            # Plagiarism detection results
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS plagiarism_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_paper_id INTEGER,
                    target_paper_id INTEGER,
                    plagiarism_score REAL,
                    plagiarism_type TEXT,  -- 'direct', 'paraphrased', 'structural'
                    matching_segments TEXT,  -- JSON of matching segments with scores
                    detection_method TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_paper_id) REFERENCES papers (id),
                    FOREIGN KEY (target_paper_id) REFERENCES papers (id)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_papers_hash ON papers(file_hash)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_papers_title ON papers(title)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_similarities_score ON paper_similarities(similarity_score)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_plagiarism_score ON plagiarism_results(plagiarism_score)')
            
            conn.commit()
    
    def add_paper(self, title: str, content: str, abstract: str = None, 
                  authors: List[str] = None, keywords: List[str] = None,
                  file_hash: str = None, venue: str = None) -> int:
        """Add a new paper to the database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO papers (title, abstract, content, authors, keywords, file_hash, venue)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                title, abstract, content,
                json.dumps(authors or []),
                json.dumps(keywords or []),
                file_hash, venue
            ))
            
            paper_id = cursor.lastrowid
            conn.commit()
            return paper_id
    
    def add_author(self, name: str, affiliation: str = None, 
                   email: str = None, research_areas: List[str] = None) -> int:
        """Add a new author to the database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO authors (name, affiliation, email, research_areas)
                    VALUES (?, ?, ?, ?)
                ''', (name, affiliation, email, json.dumps(research_areas or [])))
                
                author_id = cursor.lastrowid
                conn.commit()
                return author_id
            except sqlite3.IntegrityError:
                # Author already exists, return existing ID
                cursor.execute('SELECT id FROM authors WHERE name = ?', (name,))
                return cursor.fetchone()[0]
    
    def add_topic(self, name: str, category: str = None, description: str = None) -> int:
        """Add a new topic to the database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO topics (name, category, description)
                    VALUES (?, ?, ?)
                ''', (name, category, description))
                
                topic_id = cursor.lastrowid
                conn.commit()
                return topic_id
            except sqlite3.IntegrityError:
                # Topic already exists, return existing ID
                cursor.execute('SELECT id FROM topics WHERE name = ?', (name,))
                return cursor.fetchone()[0]
    
    def add_similarity(self, paper1_id: int, paper2_id: int, score: float,
                      similarity_type: str, matching_segments: Dict = None):
        """Add similarity relationship between papers"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO paper_similarities 
                (paper1_id, paper2_id, similarity_score, similarity_type, matching_segments)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                paper1_id, paper2_id, score, similarity_type,
                json.dumps(matching_segments or {})
            ))
            conn.commit()
    
    def add_plagiarism_result(self, source_id: int, target_id: int, score: float,
                            plagiarism_type: str, matching_segments: Dict,
                            detection_method: str):
        """Add plagiarism detection result"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO plagiarism_results 
                (source_paper_id, target_paper_id, plagiarism_score, plagiarism_type,
                 matching_segments, detection_method)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                source_id, target_id, score, plagiarism_type,
                json.dumps(matching_segments), detection_method
            ))
            conn.commit()
    
    def get_paper_by_hash(self, file_hash: str) -> Optional[Dict]:
        """Get paper by file hash"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM papers WHERE file_hash = ?', (file_hash,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_papers(self) -> List[Dict]:
        """Get all papers from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM papers ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_similar_papers(self, paper_id: int, threshold: float = 0.5) -> List[Dict]:
        """Get papers similar to given paper"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.*, ps.similarity_score, ps.similarity_type, ps.matching_segments
                FROM papers p
                JOIN paper_similarities ps ON (p.id = ps.paper2_id)
                WHERE ps.paper1_id = ? AND ps.similarity_score >= ?
                ORDER BY ps.similarity_score DESC
            ''', (paper_id, threshold))
            return [dict(row) for row in cursor.fetchall()]
    
    def search_papers(self, query: str) -> List[Dict]:
        """Search papers by title, abstract, or content"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            search_pattern = f'%{query}%'
            cursor.execute('''
                SELECT * FROM papers 
                WHERE title LIKE ? OR abstract LIKE ? OR content LIKE ?
                ORDER BY title
            ''', (search_pattern, search_pattern, search_pattern))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            tables = ['papers', 'authors', 'topics', 'paper_similarities', 'plagiarism_results']
            
            for table in tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                stats[table] = cursor.fetchone()[0]
            
            return stats
    
    def get_all_papers(self) -> List[Dict]:
        """Get all papers from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM papers ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_authors(self) -> List[Dict]:
        """Get all authors from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM authors ORDER BY name')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_topics(self) -> List[Dict]:
        """Get all topics from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM topics ORDER BY name')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_similarities(self) -> List[Dict]:
        """Get all similarity records from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM paper_similarities ORDER BY similarity_score DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_paper_by_hash(self, file_hash: str) -> Optional[Dict]:
        """Get paper by file hash"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM papers WHERE file_hash = ?', (file_hash,))
            row = cursor.fetchone()
            return dict(row) if row else None