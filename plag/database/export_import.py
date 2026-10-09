"""
Database export and import functionality for Aura system
Handles data backup, restoration, and format conversion
"""

import json
import csv
import pandas as pd
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Any
from database.models import DatabaseManager
from config import BACKUP_PATH, EXPORT_FORMATS

class DatabaseExporter:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.ensure_backup_dir()
    
    def ensure_backup_dir(self):
        """Ensure backup directory exists"""
        os.makedirs(BACKUP_PATH, exist_ok=True)
    
    def export_to_json(self, filename: str = None) -> str:
        """Export entire database to JSON format"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'aura_export_{timestamp}.json'
        
        filepath = os.path.join(BACKUP_PATH, filename)
        
        # Get all data from database
        data = {
            'export_timestamp': datetime.now().isoformat(),
            'papers': self.db_manager.get_all_papers(),
            'authors': self._get_all_authors(),
            'topics': self._get_all_topics(),
            'similarities': self._get_all_similarities(),
            'plagiarism_results': self._get_all_plagiarism_results(),
            'statistics': self.db_manager.get_database_stats()
        }
        
        # Convert JSON strings back to objects for better readability
        for paper in data['papers']:
            if paper['authors']:
                paper['authors'] = json.loads(paper['authors'])
            if paper['keywords']:
                paper['keywords'] = json.loads(paper['keywords'])
        
        for author in data['authors']:
            if author['research_areas']:
                author['research_areas'] = json.loads(author['research_areas'])
        
        for similarity in data['similarities']:
            if similarity['matching_segments']:
                similarity['matching_segments'] = json.loads(similarity['matching_segments'])
        
        for result in data['plagiarism_results']:
            if result['matching_segments']:
                result['matching_segments'] = json.loads(result['matching_segments'])
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        return filepath
    
    def export_to_csv(self, table_name: str, filename: str = None) -> str:
        """Export specific table to CSV format"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{table_name}_{timestamp}.csv'
        
        filepath = os.path.join(BACKUP_PATH, filename)
        
        with self.db_manager.get_connection() as conn:
            df = pd.read_sql_query(f'SELECT * FROM {table_name}', conn)
            df.to_csv(filepath, index=False, encoding='utf-8')
        
        return filepath
    
    def export_to_excel(self, filename: str = None) -> str:
        """Export all tables to Excel with multiple sheets"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'aura_export_{timestamp}.xlsx'
        
        filepath = os.path.join(BACKUP_PATH, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            with self.db_manager.get_connection() as conn:
                # Export each table as a separate sheet
                tables = ['papers', 'authors', 'topics', 'paper_similarities', 'plagiarism_results']
                
                for table in tables:
                    df = pd.read_sql_query(f'SELECT * FROM {table}', conn)
                    df.to_excel(writer, sheet_name=table, index=False)
                
                # Add statistics sheet
                stats = self.db_manager.get_database_stats()
                stats_df = pd.DataFrame(list(stats.items()), columns=['Table', 'Count'])
                stats_df.to_excel(writer, sheet_name='statistics', index=False)
        
        return filepath
    
    def import_from_json(self, filepath: str) -> bool:
        """Import data from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Import papers
            for paper_data in data.get('papers', []):
                self.db_manager.add_paper(
                    title=paper_data['title'],
                    content=paper_data['content'],
                    abstract=paper_data.get('abstract'),
                    authors=paper_data.get('authors', []),
                    keywords=paper_data.get('keywords', []),
                    file_hash=paper_data.get('file_hash'),
                    venue=paper_data.get('venue')
                )
            
            # Import authors
            for author_data in data.get('authors', []):
                self.db_manager.add_author(
                    name=author_data['name'],
                    affiliation=author_data.get('affiliation'),
                    email=author_data.get('email'),
                    research_areas=author_data.get('research_areas', [])
                )
            
            # Import topics
            for topic_data in data.get('topics', []):
                self.db_manager.add_topic(
                    name=topic_data['name'],
                    category=topic_data.get('category'),
                    description=topic_data.get('description')
                )
            
            return True
            
        except Exception as e:
            print(f"Error importing from JSON: {e}")
            return False
    
    def create_backup(self) -> str:
        """Create a complete backup of the database"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'aura_backup_{timestamp}'
        
        # Create JSON backup
        json_file = self.export_to_json(f'{backup_name}.json')
        
        # Create Excel backup
        excel_file = self.export_to_excel(f'{backup_name}.xlsx')
        
        # Copy SQLite database file
        import shutil
        db_backup = os.path.join(BACKUP_PATH, f'{backup_name}.sqlite')
        shutil.copy2(self.db_manager.db_path, db_backup)
        
        return backup_name
    
    def _get_all_authors(self) -> List[Dict]:
        """Get all authors from database"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM authors ORDER BY name')
            return [dict(row) for row in cursor.fetchall()]
    
    def _get_all_topics(self) -> List[Dict]:
        """Get all topics from database"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM topics ORDER BY name')
            return [dict(row) for row in cursor.fetchall()]
    
    def _get_all_similarities(self) -> List[Dict]:
        """Get all similarities from database"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM paper_similarities ORDER BY similarity_score DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def _get_all_plagiarism_results(self) -> List[Dict]:
        """Get all plagiarism results from database"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM plagiarism_results ORDER BY plagiarism_score DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_export_summary(self) -> Dict[str, Any]:
        """Get summary of exportable data"""
        stats = self.db_manager.get_database_stats()
        
        return {
            'total_papers': stats.get('papers', 0),
            'total_authors': stats.get('authors', 0),
            'total_topics': stats.get('topics', 0),
            'total_similarities': stats.get('paper_similarities', 0),
            'total_plagiarism_results': stats.get('plagiarism_results', 0),
            'supported_formats': EXPORT_FORMATS,
            'backup_location': BACKUP_PATH
        }