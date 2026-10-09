"""
Utility functions for the Aura plagiarism detection system
"""

import os
import hashlib
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('aura.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('aura')

def calculate_file_hash(file_content: bytes) -> str:
    """Calculate SHA-256 hash of file content"""
    return hashlib.sha256(file_content).hexdigest()

def clean_text(text: str) -> str:
    """Clean and normalize text for processing"""
    if not text:
        return ""
    
    try:
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation 
        text = re.sub(r'[^\w\s.,!?;:\'\-]', '', text)
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
        
        return text.strip()
    except Exception as e:
        # If any processing fails, just return basic cleaned text
        return ' '.join(text.split())

def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """Extract keywords from text using simple frequency analysis"""
    # Simple keyword extraction (could be enhanced with NLP)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Common stop words to filter out
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
        'those', 'his', 'her', 'its', 'their', 'our', 'your', 'may', 'can',
        'will', 'would', 'could', 'should', 'shall', 'might', 'must', 'have',
        'has', 'had', 'been', 'being', 'are', 'was', 'were', 'they', 'them',
        'what', 'when', 'where', 'who', 'which', 'why', 'how', 'all', 'any',
        'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'only',
        'own', 'same', 'than', 'too', 'very', 'can', 'just', 'now', 'also'
    }
    
    # Filter out stop words and count frequency
    word_freq = {}
    for word in words:
        if word not in stop_words and len(word) > 2:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Return top N keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:top_n]]

def format_similarity_score(score: float) -> str:
    """Format similarity score for display"""
    return f"{score:.1%}"

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def validate_pdf_file(file_content: bytes) -> bool:
    """Validate if file is a proper PDF"""
    return file_content.startswith(b'%PDF-')

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:251 - len(ext)] + ext
    
    return filename

def create_export_filename(base_name: str, export_format: str) -> str:
    """Create export filename with timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{base_name}_{timestamp}.{export_format}"

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def merge_overlapping_ranges(ranges: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Merge overlapping ranges"""
    if not ranges:
        return []
    
    # Sort ranges by start position
    sorted_ranges = sorted(ranges, key=lambda x: x[0])
    merged = [sorted_ranges[0]]
    
    for current in sorted_ranges[1:]:
        last = merged[-1]
        
        # If ranges overlap, merge them
        if current[0] <= last[1]:
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
    
    return merged

def calculate_text_overlap(text1: str, text2: str, min_length: int = 5) -> float:
    """Calculate text overlap percentage using longest common subsequence"""
    words1 = text1.lower().split()
    words2 = text2.lower().split()
    
    if not words1 or not words2:
        return 0.0
    
    # Simple longest common subsequence calculation
    m, n = len(words1), len(words2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if words1[i-1] == words2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    lcs_length = dp[m][n]
    
    if lcs_length < min_length:
        return 0.0
    
    # Return overlap as percentage of shorter text
    return (lcs_length / min(m, n)) * 100

def generate_similarity_report(matches: List[Dict]) -> Dict[str, Any]:
    """Generate summary report from similarity matches"""
    if not matches:
        return {
            'total_matches': 0,
            'average_similarity': 0.0,
            'max_similarity': 0.0,
            'types_distribution': {},
            'confidence_levels': {'high': 0, 'medium': 0, 'low': 0}
        }
    
    similarities = [match.get('similarity_score', 0) for match in matches]
    types = [match.get('type', 'unknown') for match in matches]
    confidences = [match.get('confidence', 0) for match in matches]
    
    # Calculate confidence levels
    confidence_levels = {
        'high': sum(1 for c in confidences if c >= 0.8),
        'medium': sum(1 for c in confidences if 0.5 <= c < 0.8),
        'low': sum(1 for c in confidences if c < 0.5)
    }
    
    # Types distribution
    types_dist = {}
    for t in types:
        types_dist[t] = types_dist.get(t, 0) + 1
    
    return {
        'total_matches': len(matches),
        'average_similarity': sum(similarities) / len(similarities),
        'max_similarity': max(similarities),
        'min_similarity': min(similarities),
        'types_distribution': types_dist,
        'confidence_levels': confidence_levels
    }

def ensure_directory_exists(directory_path: str) -> None:
    """Ensure directory exists, create if it doesn't"""
    os.makedirs(directory_path, exist_ok=True)

def load_json_file(filepath: str) -> Optional[Dict]:
    """Safely load JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading JSON file {filepath}: {e}")
        return None

def save_json_file(data: Dict, filepath: str) -> bool:
    """Safely save data to JSON file"""
    try:
        ensure_directory_exists(os.path.dirname(filepath))
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return True
    except Exception as e:
        logging.error(f"Error saving JSON file {filepath}: {e}")
        return False