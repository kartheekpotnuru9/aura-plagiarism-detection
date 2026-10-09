"""
Modules package initialization
"""

from .pdf_processor import PDFProcessor
from .similarity_engine import SemanticSimilarityEngine
from .knowledge_graph import KnowledgeGraphBuilder
from .plagiarism_detector import PlagiarismDetector, PlagiarismResult, PlagiarismMatch, PlagiarismType

__all__ = [
    'PDFProcessor',
    'SemanticSimilarityEngine', 
    'KnowledgeGraphBuilder',
    'PlagiarismDetector',
    'PlagiarismResult',
    'PlagiarismMatch',
    'PlagiarismType'
]