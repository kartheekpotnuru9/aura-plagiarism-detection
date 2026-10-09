"""
PDF text extraction module for Aura plagiarism detection system
Handles PDF parsing, text extraction, and preprocessing
"""

import PyPDF2
import re
import hashlib
from typing import Dict, List, Tuple, Optional
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import textstat
import io

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class PDFProcessor:
    def __init__(self):
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
    
    def extract_text_from_pdf(self, pdf_file) -> Dict[str, any]:
        """
        Extract text and metadata from PDF file
        
        Args:
            pdf_file: File-like object (from Streamlit file uploader)
            
        Returns:
            Dictionary containing extracted text, metadata, and statistics
        """
        try:
            # Reset file pointer to beginning
            pdf_file.seek(0)
            
            # Create PDF reader
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Extract metadata
            metadata = self._extract_metadata(pdf_reader)
            
            # Extract text from all pages
            full_text = ""
            page_texts = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    page_texts.append({
                        'page_number': page_num + 1,
                        'text': page_text,
                        'word_count': len(page_text.split())
                    })
                    full_text += page_text + "\n"
                except Exception as e:
                    print(f"Error extracting text from page {page_num + 1}: {e}")
                    continue
            
            # Clean and preprocess text
            cleaned_text = self._clean_text(full_text)
            
            # Generate file hash for duplicate detection
            file_hash = self._generate_file_hash(pdf_file)
            
            # Extract paper structure
            structure = self._extract_paper_structure(cleaned_text)
            
            # Calculate text statistics
            stats = self._calculate_text_statistics(cleaned_text)
            
            return {
                'success': True,
                'text': cleaned_text,
                'raw_text': full_text,
                'pages': page_texts,
                'metadata': metadata,
                'structure': structure,
                'statistics': stats,
                'file_hash': file_hash
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'metadata': {},
                'structure': {},
                'statistics': {},
                'file_hash': None
            }
    
    def _extract_metadata(self, pdf_reader) -> Dict[str, str]:
        """Extract metadata from PDF"""
        metadata = {}
        
        if pdf_reader.metadata:
            metadata.update({
                'title': pdf_reader.metadata.get('/Title', ''),
                'author': pdf_reader.metadata.get('/Author', ''),
                'subject': pdf_reader.metadata.get('/Subject', ''),
                'creator': pdf_reader.metadata.get('/Creator', ''),
                'producer': pdf_reader.metadata.get('/Producer', ''),
                'creation_date': str(pdf_reader.metadata.get('/CreationDate', '')),
                'modification_date': str(pdf_reader.metadata.get('/ModDate', ''))
            })
        
        metadata['num_pages'] = len(pdf_reader.pages)
        
        return metadata
    
    def _clean_text(self, text: str) -> str:
        """Clean and preprocess extracted text"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers (common patterns)
        text = re.sub(r'\n\d+\n', '\n', text)
        text = re.sub(r'\n[A-Z\s]{2,30}\n', '\n', text)
        
        # Fix common PDF extraction issues
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between words
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)  # Add space after sentences
        
        # Remove URLs and email addresses
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[-]{3,}', '---', text)
        
        return text.strip()
    
    def _generate_file_hash(self, pdf_file) -> str:
        """Generate SHA-256 hash of the PDF file for duplicate detection"""
        pdf_file.seek(0)
        content = pdf_file.read()
        pdf_file.seek(0)  # Reset for future use
        
        return hashlib.sha256(content).hexdigest()
    
    def _extract_paper_structure(self, text: str) -> Dict[str, str]:
        """Extract paper structure (title, abstract, sections, etc.)"""
        structure = {}
        
        # Split text into lines for analysis
        lines = text.split('\n')
        text_lower = text.lower()
        
        # Extract title (usually the first significant line)
        title_candidates = [line.strip() for line in lines[:10] if len(line.strip()) > 10]
        if title_candidates:
            structure['title'] = title_candidates[0]
        
        # Extract abstract
        abstract_match = re.search(r'abstract\s*:?\s*(.*?)(?:\n\s*\n|\n\s*(?:keywords|introduction|1\.|i\.))', 
                                 text_lower, re.DOTALL | re.IGNORECASE)
        if abstract_match:
            structure['abstract'] = abstract_match.group(1).strip()
        
        # Extract keywords
        keywords_match = re.search(r'keywords?\s*:?\s*(.*?)(?:\n\s*\n|\n\s*(?:introduction|1\.|i\.))', 
                                  text_lower, re.DOTALL | re.IGNORECASE)
        if keywords_match:
            keywords_text = keywords_match.group(1).strip()
            keywords = [kw.strip() for kw in re.split(r'[,;]', keywords_text) if kw.strip()]
            structure['keywords'] = keywords
        
        # Extract authors (look for patterns before abstract)
        author_patterns = [
            r'(?:by\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)*[A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+(?:\s+[A-Z]\.?\s*)*[A-Z][a-z]+)*)'
        ]
        
        for pattern in author_patterns:
            authors_match = re.search(pattern, text[:1000])  # Look in first 1000 chars
            if authors_match:
                authors_text = authors_match.group(1)
                authors = [auth.strip() for auth in authors_text.split(',') if auth.strip()]
                structure['authors'] = authors
                break
        
        # Extract sections (look for numbered or titled sections)
        sections = []
        section_patterns = [
            r'\n\s*(\d+\.?\s+[A-Z][^.\n]{5,50})\s*\n',
            r'\n\s*([A-Z][A-Z\s]{3,30})\s*\n',
            r'\n\s*(I{1,3}\.?\s+[A-Z][^.\n]{5,50})\s*\n'
        ]
        
        for pattern in section_patterns:
            matches = re.findall(pattern, text)
            if matches:
                sections.extend([match.strip() for match in matches])
        
        if sections:
            structure['sections'] = list(set(sections))  # Remove duplicates
        
        return structure
    
    def _calculate_text_statistics(self, text: str) -> Dict[str, any]:
        """Calculate various text statistics"""
        if not text:
            return {}
        
        sentences = sent_tokenize(text)
        words = word_tokenize(text.lower())
        words_no_stop = [word for word in words if word.isalpha() and word not in self.stop_words]
        
        stats = {
            'char_count': len(text),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'paragraph_count': len([p for p in text.split('\n\n') if p.strip()]),
            'avg_words_per_sentence': len(words) / len(sentences) if sentences else 0,
            'avg_chars_per_word': len(text) / len(words) if words else 0,
            'unique_words': len(set(words_no_stop)),
            'vocabulary_richness': len(set(words_no_stop)) / len(words_no_stop) if words_no_stop else 0,
            'readability_flesch': textstat.flesch_reading_ease(text),
            'readability_grade': textstat.flesch_kincaid_grade(text)
        }
        
        return stats
    
    def extract_sentences(self, text: str, min_length: int = 10) -> List[str]:
        """Extract and clean sentences from text"""
        sentences = sent_tokenize(text)
        
        # Filter and clean sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) >= min_length and not self._is_noise_sentence(sentence):
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def _is_noise_sentence(self, sentence: str) -> bool:
        """Check if sentence is likely noise (headers, page numbers, etc.)"""
        # Too short or too long
        if len(sentence) < 10 or len(sentence) > 1000:
            return True
        
        # Mostly numbers or special characters
        if len(re.findall(r'[a-zA-Z]', sentence)) < len(sentence) * 0.5:
            return True
        
        # Common noise patterns
        noise_patterns = [
            r'^\d+$',  # Just numbers
            r'^page \d+',  # Page numbers
            r'^figure \d+',  # Figure captions
            r'^table \d+',  # Table captions
            r'^\d+\.\d+',  # Section numbers
            r'^[A-Z\s]{10,}$'  # All caps headers
        ]
        
        for pattern in noise_patterns:
            if re.match(pattern, sentence.lower()):
                return True
        
        return False
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict[str, any]]:
        """Split text into overlapping chunks for analysis"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            chunks.append({
                'text': chunk_text,
                'start_index': i,
                'end_index': min(i + chunk_size, len(words)),
                'word_count': len(chunk_words)
            })
            
            if i + chunk_size >= len(words):
                break
        
        return chunks