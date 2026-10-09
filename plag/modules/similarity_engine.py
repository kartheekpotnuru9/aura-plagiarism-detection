"""
Semantic similarity engine for Aura plagiarism detection system
Uses sentence transformers and various similarity measures
"""

import numpy as np
from typing import List, Dict, Tuple, Any, Optional
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("Warning: sentence-transformers not available. Using TF-IDF fallback mode.")
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from rapidfuzz import fuzz
import re
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

class SemanticSimilarityEngine:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the semantic similarity engine
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.sentence_model = None
        self.tfidf_vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 3),
            min_df=1,
            max_df=0.8
        )
        self.stop_words = set(stopwords.words('english'))
        
        # Load the sentence transformer model
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            print("Sentence transformers not available. Using TF-IDF only mode.")
            self.sentence_model = None
            return
            
        try:
            self.sentence_model = SentenceTransformer(self.model_name)
            print(f"Loaded sentence transformer model: {self.model_name}")
        except Exception as e:
            print(f"Error loading model {self.model_name}: {e}")
            print("Falling back to TF-IDF only mode")
            self.sentence_model = None
    
    def compute_semantic_similarity(self, text1: str, text2: str) -> Dict[str, float]:
        """
        Compute various similarity measures between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Dictionary with different similarity scores
        """
        similarities = {}
        
        # Semantic similarity using sentence transformers
        if self.sentence_model:
            similarities['semantic'] = self._compute_sentence_transformer_similarity(text1, text2)
        
        # TF-IDF cosine similarity
        similarities['tfidf'] = self._compute_tfidf_similarity(text1, text2)
        
        # Fuzzy string matching
        similarities['fuzzy'] = self._compute_fuzzy_similarity(text1, text2)
        
        # Jaccard similarity
        similarities['jaccard'] = self._compute_jaccard_similarity(text1, text2)
        
        # Sentence-level similarity
        similarities['sentence_avg'] = self._compute_sentence_level_similarity(text1, text2)
        
        # Composite score
        similarities['composite'] = self._compute_composite_score(similarities)
        
        return similarities
    
    def _compute_sentence_transformer_similarity(self, text1: str, text2: str) -> float:
        """Compute similarity using sentence transformers"""
        if not self.sentence_model:
            return 0.0
        
        try:
            # Encode texts
            embeddings = self.sentence_model.encode([text1, text2])
            
            # Calculate cosine similarity
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            
            return float(similarity)
        except Exception as e:
            print(f"Error in sentence transformer similarity: {e}")
            return 0.0
    
    def _compute_tfidf_similarity(self, text1: str, text2: str) -> float:
        """Compute TF-IDF cosine similarity"""
        try:
            # Fit and transform texts
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([text1, text2])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
        except Exception as e:
            print(f"Error in TF-IDF similarity: {e}")
            return 0.0
    
    def _compute_fuzzy_similarity(self, text1: str, text2: str) -> float:
        """Compute fuzzy string similarity"""
        try:
            # Use different fuzzy matching algorithms
            ratio = fuzz.ratio(text1, text2) / 100.0
            partial_ratio = fuzz.partial_ratio(text1, text2) / 100.0
            token_sort_ratio = fuzz.token_sort_ratio(text1, text2) / 100.0
            token_set_ratio = fuzz.token_set_ratio(text1, text2) / 100.0
            
            # Return average of all fuzzy scores
            return (ratio + partial_ratio + token_sort_ratio + token_set_ratio) / 4.0
        except Exception as e:
            print(f"Error in fuzzy similarity: {e}")
            return 0.0
    
    def _compute_jaccard_similarity(self, text1: str, text2: str) -> float:
        """Compute Jaccard similarity between word sets"""
        try:
            # Tokenize and create word sets
            words1 = set(word.lower() for word in word_tokenize(text1) 
                        if word.isalpha() and word.lower() not in self.stop_words)
            words2 = set(word.lower() for word in word_tokenize(text2) 
                        if word.isalpha() and word.lower() not in self.stop_words)
            
            # Calculate Jaccard similarity
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            return intersection / union if union > 0 else 0.0
        except Exception as e:
            print(f"Error in Jaccard similarity: {e}")
            return 0.0
    
    def _compute_sentence_level_similarity(self, text1: str, text2: str) -> float:
        """Compute average similarity at sentence level"""
        try:
            sentences1 = sent_tokenize(text1)
            sentences2 = sent_tokenize(text2)
            
            if not sentences1 or not sentences2:
                return 0.0
            
            similarities = []
            
            # Compare each sentence in text1 with all sentences in text2
            for sent1 in sentences1:
                max_sim = 0.0
                for sent2 in sentences2:
                    if self.sentence_model:
                        embeddings = self.sentence_model.encode([sent1, sent2])
                        sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
                    else:
                        # Fallback to TF-IDF for sentence comparison
                        try:
                            tfidf_matrix = self.tfidf_vectorizer.fit_transform([sent1, sent2])
                            sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                        except:
                            sim = fuzz.ratio(sent1, sent2) / 100.0
                    
                    max_sim = max(max_sim, sim)
                
                similarities.append(max_sim)
            
            return np.mean(similarities) if similarities else 0.0
        except Exception as e:
            print(f"Error in sentence level similarity: {e}")
            return 0.0
    
    def _compute_composite_score(self, similarities: Dict[str, float]) -> float:
        """Compute weighted composite similarity score"""
        weights = {
            'semantic': 0.4,
            'tfidf': 0.2,
            'fuzzy': 0.15,
            'jaccard': 0.1,
            'sentence_avg': 0.15
        }
        
        composite = 0.0
        total_weight = 0.0
        
        for measure, score in similarities.items():
            if measure in weights and score > 0:
                composite += weights[measure] * score
                total_weight += weights[measure]
        
        return composite / total_weight if total_weight > 0 else 0.0
    
    def find_similar_segments(self, text1: str, text2: str, 
                             threshold: float = 0.7, 
                             segment_length: int = 100) -> List[Dict[str, Any]]:
        """
        Find similar segments between two texts
        
        Args:
            text1: First text
            text2: Second text
            threshold: Similarity threshold
            segment_length: Length of segments in words
            
        Returns:
            List of similar segment pairs
        """
        similar_segments = []
        
        # Split texts into segments
        segments1 = self._create_segments(text1, segment_length)
        segments2 = self._create_segments(text2, segment_length)
        
        # Compare all segment pairs
        for i, seg1 in enumerate(segments1):
            for j, seg2 in enumerate(segments2):
                similarity = self.compute_semantic_similarity(seg1['text'], seg2['text'])
                
                if similarity['composite'] >= threshold:
                    similar_segments.append({
                        'text1_segment': seg1,
                        'text2_segment': seg2,
                        'similarity_scores': similarity,
                        'overall_similarity': similarity['composite']
                    })
        
        # Sort by similarity score
        similar_segments.sort(key=lambda x: x['overall_similarity'], reverse=True)
        
        return similar_segments
    
    def _create_segments(self, text: str, segment_length: int) -> List[Dict[str, Any]]:
        """Create overlapping segments from text"""
        words = text.split()
        segments = []
        
        overlap = segment_length // 4  # 25% overlap
        
        for i in range(0, len(words), segment_length - overlap):
            segment_words = words[i:i + segment_length]
            if len(segment_words) >= segment_length // 2:  # Minimum segment size
                segments.append({
                    'text': ' '.join(segment_words),
                    'start_word': i,
                    'end_word': min(i + segment_length, len(words)),
                    'word_count': len(segment_words)
                })
        
        return segments
    
    def detect_paraphrasing(self, text1: str, text2: str) -> Dict[str, Any]:
        """
        Detect paraphrasing between texts using multiple techniques
        
        Args:
            text1: Original text
            text2: Potentially paraphrased text
            
        Returns:
            Paraphrasing detection results
        """
        # Compute similarities
        similarities = self.compute_semantic_similarity(text1, text2)
        
        # Find similar segments
        similar_segments = self.find_similar_segments(text1, text2, threshold=0.6)
        
        # Analyze structural similarity
        structural_sim = self._analyze_structural_similarity(text1, text2)
        
        # Determine paraphrasing level
        paraphrase_level = self._determine_paraphrase_level(similarities, similar_segments)
        
        return {
            'is_paraphrased': similarities['composite'] > 0.6,
            'paraphrase_confidence': similarities['composite'],
            'paraphrase_level': paraphrase_level,
            'similarity_scores': similarities,
            'similar_segments': similar_segments,
            'structural_similarity': structural_sim,
            'segment_count': len(similar_segments),
            'coverage_percentage': self._calculate_coverage_percentage(text1, similar_segments)
        }
    
    def _analyze_structural_similarity(self, text1: str, text2: str) -> Dict[str, float]:
        """Analyze structural similarity between texts"""
        # Sentence count similarity
        sentences1 = sent_tokenize(text1)
        sentences2 = sent_tokenize(text2)
        
        sentence_ratio = min(len(sentences1), len(sentences2)) / max(len(sentences1), len(sentences2)) \
                        if max(len(sentences1), len(sentences2)) > 0 else 0
        
        # Word count similarity
        words1 = len(word_tokenize(text1))
        words2 = len(word_tokenize(text2))
        
        word_ratio = min(words1, words2) / max(words1, words2) if max(words1, words2) > 0 else 0
        
        # Paragraph structure similarity
        paragraphs1 = len([p for p in text1.split('\n\n') if p.strip()])
        paragraphs2 = len([p for p in text2.split('\n\n') if p.strip()])
        
        paragraph_ratio = min(paragraphs1, paragraphs2) / max(paragraphs1, paragraphs2) \
                         if max(paragraphs1, paragraphs2) > 0 else 0
        
        return {
            'sentence_structure': sentence_ratio,
            'word_count': word_ratio,
            'paragraph_structure': paragraph_ratio,
            'overall_structure': (sentence_ratio + word_ratio + paragraph_ratio) / 3
        }
    
    def _determine_paraphrase_level(self, similarities: Dict[str, float], 
                                   similar_segments: List[Dict]) -> str:
        """Determine the level of paraphrasing"""
        composite_score = similarities['composite']
        segment_count = len(similar_segments)
        
        if composite_score > 0.8 and segment_count > 3:
            return 'HIGH'
        elif composite_score > 0.6 and segment_count > 2:
            return 'MEDIUM'
        elif composite_score > 0.4 and segment_count > 1:
            return 'LOW'
        else:
            return 'NONE'
    
    def _calculate_coverage_percentage(self, original_text: str, 
                                     similar_segments: List[Dict]) -> float:
        """Calculate what percentage of original text is covered by similar segments"""
        if not similar_segments:
            return 0.0
        
        original_words = len(original_text.split())
        covered_words = 0
        
        for segment in similar_segments:
            covered_words += segment['text1_segment']['word_count']
        
        return min(100.0, (covered_words / original_words) * 100) if original_words > 0 else 0.0
    
    def batch_similarity_computation(self, texts: List[str]) -> np.ndarray:
        """
        Compute similarity matrix for a batch of texts
        
        Args:
            texts: List of texts to compare
            
        Returns:
            Similarity matrix
        """
        n = len(texts)
        similarity_matrix = np.zeros((n, n))
        
        if self.sentence_model:
            # Use sentence transformers for efficient batch processing
            embeddings = self.sentence_model.encode(texts)
            similarity_matrix = cosine_similarity(embeddings)
        else:
            # Fallback to pairwise TF-IDF comparison
            for i in range(n):
                for j in range(i, n):
                    if i == j:
                        similarity_matrix[i][j] = 1.0
                    else:
                        sim = self._compute_tfidf_similarity(texts[i], texts[j])
                        similarity_matrix[i][j] = sim
                        similarity_matrix[j][i] = sim
        
        return similarity_matrix