# Configuration settings for Aura Plagiarism Detection System

import os

# Database Configuration
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'aura_db.sqlite')
BACKUP_PATH = os.path.join(os.path.dirname(__file__), 'data', 'backups')

# Model Configuration
SIMILARITY_THRESHOLD = 0.7  # Threshold for plagiarism detection
SENTENCE_TRANSFORMER_MODEL = 'all-MiniLM-L6-v2'  # Lightweight and fast
MIN_SENTENCE_LENGTH = 10  # Minimum sentence length to consider
CHUNK_SIZE = 500  # Size of text chunks for processing

# UI Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB max file size
SUPPORTED_FORMATS = ['.pdf']

# Knowledge Graph Configuration
MIN_EDGE_WEIGHT = 0.5  # Minimum weight for edges in knowledge graph
MAX_GRAPH_NODES = 1000  # Maximum nodes to display in graph visualization

# Plagiarism Detection Configuration
PLAGIARISM_LEVELS = {
    'HIGH': 0.8,
    'MEDIUM': 0.6,
    'LOW': 0.4
}

# Export Configuration
EXPORT_FORMATS = ['json', 'csv', 'xlsx']