"""
Core plagiarism detection module for Aura system
Combines multiple detection techniques to identify plagiarism and calculate scores
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

from modules.similarity_engine import SemanticSimilarityEngine
from modules.pdf_processor import PDFProcessor
from database.models import DatabaseManager
from config import SIMILARITY_THRESHOLD, PLAGIARISM_LEVELS, CHUNK_SIZE

class PlagiarismType(Enum):
    DIRECT_COPY = "direct_copy"
    PARAPHRASED = "paraphrased"
    STRUCTURAL = "structural"
    MOSAIC = "mosaic"
    IDEA_PLAGIARISM = "idea_plagiarism"

@dataclass
class PlagiarismMatch:
    source_text: str
    target_text: str
    similarity_score: float
    plagiarism_type: PlagiarismType
    confidence: float
    start_position: int
    end_position: int
    source_paper_id: Optional[int] = None
    target_paper_id: Optional[int] = None

@dataclass
class PlagiarismResult:
    overall_score: float
    plagiarism_level: str
    matches: List[PlagiarismMatch]
    total_matches: int
    coverage_percentage: float
    source_paper_info: Dict[str, Any]
    comparison_summary: Dict[str, Any]
    detection_timestamp: str

class PlagiarismDetector:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.similarity_engine = SemanticSimilarityEngine()
        self.pdf_processor = PDFProcessor()
        
        # Detection thresholds
        self.thresholds = {
            PlagiarismType.DIRECT_COPY: 0.9,
            PlagiarismType.PARAPHRASED: 0.7,
            PlagiarismType.STRUCTURAL: 0.6,
            PlagiarismType.MOSAIC: 0.5,
            PlagiarismType.IDEA_PLAGIARISM: 0.4
        }
    
    def detect_plagiarism(self, source_text: str, source_paper_id: Optional[int] = None) -> PlagiarismResult:
        """
        Main plagiarism detection function
        
        Args:
            source_text: Text to check for plagiarism
            source_paper_id: ID of the source paper if available
            
        Returns:
            PlagiarismResult object with detection results
        """
        # Get all papers from database for comparison
        all_papers = self.db_manager.get_all_papers()
        
        if not all_papers:
            return self._create_empty_result(source_text, source_paper_id)
        
        all_matches = []
        comparison_results = []
        
        # OPTIMIZATION: Limit number of papers to compare against for speed
        # Prioritize more recent papers or papers with similar keywords
        max_papers_to_compare = min(50, len(all_papers))  # Compare with max 50 papers
        papers_to_check = all_papers[:max_papers_to_compare]
        
        print(f"🔍 Comparing against {len(papers_to_check)} papers from database...")
        
        # Compare with each paper in the database
        for idx, paper in enumerate(papers_to_check):
            if source_paper_id and paper['id'] == source_paper_id:
                continue  # Skip self-comparison
            
            # Progress indication
            if (idx + 1) % 10 == 0:
                print(f"   Analyzed {idx + 1}/{len(papers_to_check)} papers...")
            
            paper_matches = self._compare_with_paper(source_text, paper)
            all_matches.extend(paper_matches)
            
            if paper_matches:
                comparison_results.append({
                    'paper_id': paper['id'],
                    'paper_title': paper['title'],
                    'match_count': len(paper_matches),
                    'max_similarity': max(match.similarity_score for match in paper_matches),
                    'avg_similarity': np.mean([match.similarity_score for match in paper_matches])
                })
        
        # Filter and rank matches
        filtered_matches = self._filter_and_rank_matches(all_matches)
        
        # Calculate overall plagiarism score
        overall_score = self._calculate_overall_score(filtered_matches, source_text)
        
        # Determine plagiarism level
        plagiarism_level = self._determine_plagiarism_level(overall_score)
        
        # Calculate coverage percentage
        coverage_percentage = self._calculate_coverage_percentage(filtered_matches, source_text)
        
        # Create summary
        comparison_summary = {
            'total_papers_compared': len(all_papers),
            'papers_with_matches': len(comparison_results),
            'total_potential_matches': len(all_matches),
            'filtered_matches': len(filtered_matches),
            'top_matching_papers': sorted(comparison_results, 
                                        key=lambda x: x['max_similarity'], 
                                        reverse=True)[:5]
        }
        
        # Store results in database if source_paper_id is provided
        if source_paper_id:
            self._store_plagiarism_results(source_paper_id, filtered_matches)
        
        return PlagiarismResult(
            overall_score=overall_score,
            plagiarism_level=plagiarism_level,
            matches=filtered_matches,
            total_matches=len(filtered_matches),
            coverage_percentage=coverage_percentage,
            source_paper_info={'id': source_paper_id, 'text_length': len(source_text)},
            comparison_summary=comparison_summary,
            detection_timestamp=datetime.now().isoformat()
        )
    
    def _compare_with_paper(self, source_text: str, target_paper: Dict) -> List[PlagiarismMatch]:
        """Compare source text with a specific paper - OPTIMIZED VERSION"""
        target_text = target_paper.get('content', '')
        
        if not target_text:
            return []
        
        # OPTIMIZATION 1: Quick pre-filter using Jaccard similarity on whole text
        # If overall similarity is very low, skip detailed chunk comparison
        quick_check = self.similarity_engine.compute_semantic_similarity(
            source_text[:5000],  # Use first 5000 chars for quick check
            target_text[:5000]
        )
        
        if quick_check.get('jaccard', 0) < 0.1:  # Very low similarity, skip this paper
            return []
        
        matches = []
        
        # Create chunks for comparison
        source_chunks = self.pdf_processor.chunk_text(source_text, CHUNK_SIZE)
        target_chunks = self.pdf_processor.chunk_text(target_text, CHUNK_SIZE)
        
        # OPTIMIZATION 2: Limit chunk comparisons - only compare most relevant chunks
        # Use TF-IDF to find top N most similar target chunks for each source chunk
        max_target_chunks_per_source = min(5, len(target_chunks))  # Compare with max 5 target chunks
        
        # OPTIMIZATION 3: Limit number of source chunks analyzed (focus on first part of document)
        max_source_chunks = min(20, len(source_chunks))  # Only analyze first 20 chunks
        
        # Compare chunks with smart filtering
        for i, source_chunk in enumerate(source_chunks[:max_source_chunks]):
            # OPTIMIZATION 4: For each source chunk, only compare with top N most similar target chunks
            # Use fast Jaccard similarity to pre-rank target chunks
            chunk_similarities = []
            
            for j, target_chunk in enumerate(target_chunks):
                quick_sim_results = self.similarity_engine.compute_semantic_similarity(
                    source_chunk['text'][:500],  # Use first 500 chars for speed
                    target_chunk['text'][:500]
                )
                chunk_similarities.append((j, quick_sim_results.get('jaccard', 0)))
            
            # Sort and get top N most similar chunks
            top_chunks = sorted(chunk_similarities, key=lambda x: x[1], reverse=True)[:max_target_chunks_per_source]
            
            # Only do expensive semantic comparison on top candidate chunks
            for chunk_idx, quick_score in top_chunks:
                target_chunk = target_chunks[chunk_idx]
                
                # Only compute full similarity if quick similarity was promising
                if quick_score >= 0.15:  # Minimum threshold for detailed comparison
                    similarity_results = self.similarity_engine.compute_semantic_similarity(
                        source_chunk['text'], target_chunk['text']
                    )
                    
                    # Check for different types of plagiarism
                    plagiarism_matches = self._analyze_chunk_similarity(
                        source_chunk, target_chunk, similarity_results, target_paper['id']
                    )
                    
                    matches.extend(plagiarism_matches)
        
        return matches
    
    def _analyze_chunk_similarity(self, source_chunk: Dict, target_chunk: Dict, 
                                 similarity_results: Dict, target_paper_id: int) -> List[PlagiarismMatch]:
        """Analyze similarity results to identify plagiarism types"""
        matches = []
        
        # Direct copy detection
        if similarity_results['fuzzy'] > self.thresholds[PlagiarismType.DIRECT_COPY]:
            matches.append(PlagiarismMatch(
                source_text=source_chunk['text'][:200] + "..." if len(source_chunk['text']) > 200 else source_chunk['text'],
                target_text=target_chunk['text'][:200] + "..." if len(target_chunk['text']) > 200 else target_chunk['text'],
                similarity_score=similarity_results['fuzzy'],
                plagiarism_type=PlagiarismType.DIRECT_COPY,
                confidence=similarity_results['fuzzy'],
                start_position=source_chunk['start_index'],
                end_position=source_chunk['end_index'],
                target_paper_id=target_paper_id
            ))
        
        # Paraphrased content detection
        elif similarity_results['semantic'] > self.thresholds[PlagiarismType.PARAPHRASED]:
            matches.append(PlagiarismMatch(
                source_text=source_chunk['text'][:200] + "..." if len(source_chunk['text']) > 200 else source_chunk['text'],
                target_text=target_chunk['text'][:200] + "..." if len(target_chunk['text']) > 200 else target_chunk['text'],
                similarity_score=similarity_results['semantic'],
                plagiarism_type=PlagiarismType.PARAPHRASED,
                confidence=similarity_results['semantic'],
                start_position=source_chunk['start_index'],
                end_position=source_chunk['end_index'],
                target_paper_id=target_paper_id
            ))
        
        # Structural plagiarism detection
        elif similarity_results['tfidf'] > self.thresholds[PlagiarismType.STRUCTURAL]:
            matches.append(PlagiarismMatch(
                source_text=source_chunk['text'][:200] + "..." if len(source_chunk['text']) > 200 else source_chunk['text'],
                target_text=target_chunk['text'][:200] + "..." if len(target_chunk['text']) > 200 else target_chunk['text'],
                similarity_score=similarity_results['tfidf'],
                plagiarism_type=PlagiarismType.STRUCTURAL,
                confidence=similarity_results['tfidf'],
                start_position=source_chunk['start_index'],
                end_position=source_chunk['end_index'],
                target_paper_id=target_paper_id
            ))
        
        # Mosaic plagiarism (combination of techniques)
        elif similarity_results['composite'] > self.thresholds[PlagiarismType.MOSAIC]:
            matches.append(PlagiarismMatch(
                source_text=source_chunk['text'][:200] + "..." if len(source_chunk['text']) > 200 else source_chunk['text'],
                target_text=target_chunk['text'][:200] + "..." if len(target_chunk['text']) > 200 else target_chunk['text'],
                similarity_score=similarity_results['composite'],
                plagiarism_type=PlagiarismType.MOSAIC,
                confidence=similarity_results['composite'],
                start_position=source_chunk['start_index'],
                end_position=source_chunk['end_index'],
                target_paper_id=target_paper_id
            ))
        
        # Idea plagiarism (weaker similarity but still concerning)
        elif similarity_results['jaccard'] > self.thresholds[PlagiarismType.IDEA_PLAGIARISM]:
            matches.append(PlagiarismMatch(
                source_text=source_chunk['text'][:200] + "..." if len(source_chunk['text']) > 200 else source_chunk['text'],
                target_text=target_chunk['text'][:200] + "..." if len(target_chunk['text']) > 200 else target_chunk['text'],
                similarity_score=similarity_results['jaccard'],
                plagiarism_type=PlagiarismType.IDEA_PLAGIARISM,
                confidence=similarity_results['jaccard'],
                start_position=source_chunk['start_index'],
                end_position=source_chunk['end_index'],
                target_paper_id=target_paper_id
            ))
        
        return matches
    
    def _filter_and_rank_matches(self, matches: List[PlagiarismMatch]) -> List[PlagiarismMatch]:
        """Filter out low-quality matches and rank by importance"""
        if not matches:
            return []
        
        # Remove duplicates and overlapping matches
        filtered_matches = []
        seen_positions = set()
        
        # Sort by confidence score first
        sorted_matches = sorted(matches, key=lambda x: x.confidence, reverse=True)
        
        for match in sorted_matches:
            # Check for overlap with existing matches
            overlap = False
            for start, end in seen_positions:
                if (match.start_position < end and match.end_position > start):
                    # If there's overlap, keep the higher confidence match
                    if match.confidence > 0.8:  # High confidence threshold
                        # Remove the overlapping match and add this one
                        filtered_matches = [m for m in filtered_matches 
                                          if not (m.start_position < end and m.end_position > start)]
                        seen_positions = {(m.start_position, m.end_position) for m in filtered_matches}
                        break
                    else:
                        overlap = True
                        break
            
            if not overlap:
                filtered_matches.append(match)
                seen_positions.add((match.start_position, match.end_position))
        
        # Limit to top matches to avoid overwhelming results
        return filtered_matches[:50]  # Top 50 matches
    
    def _calculate_overall_score(self, matches: List[PlagiarismMatch], source_text: str) -> float:
        """Calculate overall plagiarism score"""
        if not matches:
            return 0.0
        
        # Weight different types of plagiarism
        type_weights = {
            PlagiarismType.DIRECT_COPY: 1.0,
            PlagiarismType.PARAPHRASED: 0.8,
            PlagiarismType.STRUCTURAL: 0.6,
            PlagiarismType.MOSAIC: 0.5,
            PlagiarismType.IDEA_PLAGIARISM: 0.3
        }
        
        # Calculate weighted score
        weighted_scores = []
        for match in matches:
            weight = type_weights.get(match.plagiarism_type, 0.5)
            weighted_score = match.similarity_score * weight * match.confidence
            weighted_scores.append(weighted_score)
        
        # Consider coverage - how much of the text is potentially plagiarized
        coverage_factor = self._calculate_coverage_percentage(matches, source_text) / 100.0
        
        # Calculate final score
        if weighted_scores:
            avg_weighted_score = np.mean(weighted_scores)
            # Boost score based on coverage
            final_score = avg_weighted_score * (0.7 + 0.3 * coverage_factor)
            return min(1.0, final_score)  # Cap at 1.0
        
        return 0.0
    
    def _determine_plagiarism_level(self, overall_score: float) -> str:
        """Determine plagiarism level based on score"""
        if overall_score >= PLAGIARISM_LEVELS['HIGH']:
            return 'HIGH'
        elif overall_score >= PLAGIARISM_LEVELS['MEDIUM']:
            return 'MEDIUM'
        elif overall_score >= PLAGIARISM_LEVELS['LOW']:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def _calculate_coverage_percentage(self, matches: List[PlagiarismMatch], source_text: str) -> float:
        """Calculate what percentage of source text is covered by matches"""
        if not matches:
            return 0.0
        
        source_words = len(source_text.split())
        covered_positions = set()
        
        for match in matches:
            for pos in range(match.start_position, match.end_position):
                covered_positions.add(pos)
        
        coverage = len(covered_positions) / source_words if source_words > 0 else 0.0
        return min(100.0, coverage * 100)
    
    def _store_plagiarism_results(self, source_paper_id: int, matches: List[PlagiarismMatch]):
        """Store plagiarism detection results in database"""
        for match in matches:
            if match.target_paper_id:
                matching_segments = {
                    'source_text': match.source_text,
                    'target_text': match.target_text,
                    'start_position': match.start_position,
                    'end_position': match.end_position,
                    'confidence': match.confidence
                }
                
                self.db_manager.add_plagiarism_result(
                    source_id=source_paper_id,
                    target_id=match.target_paper_id,
                    score=match.similarity_score,
                    plagiarism_type=match.plagiarism_type.value,
                    matching_segments=matching_segments,
                    detection_method='aura_semantic_detection'
                )
    
    def _create_empty_result(self, source_text: str, source_paper_id: Optional[int]) -> PlagiarismResult:
        """Create empty result when no papers to compare against"""
        return PlagiarismResult(
            overall_score=0.0,
            plagiarism_level='MINIMAL',
            matches=[],
            total_matches=0,
            coverage_percentage=0.0,
            source_paper_info={'id': source_paper_id, 'text_length': len(source_text)},
            comparison_summary={
                'total_papers_compared': 0,
                'papers_with_matches': 0,
                'total_potential_matches': 0,
                'filtered_matches': 0,
                'top_matching_papers': []
            },
            detection_timestamp=datetime.now().isoformat()
        )
    
    def get_plagiarism_statistics(self) -> Dict[str, Any]:
        """Get statistics about plagiarism detection results"""
        stats = self.db_manager.get_database_stats()
        
        # Get plagiarism level distribution
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get score distribution
            cursor.execute('''
                SELECT 
                    CASE 
                        WHEN plagiarism_score >= 0.8 THEN 'HIGH'
                        WHEN plagiarism_score >= 0.6 THEN 'MEDIUM'
                        WHEN plagiarism_score >= 0.4 THEN 'LOW'
                        ELSE 'MINIMAL'
                    END as level,
                    COUNT(*) as count
                FROM plagiarism_results
                GROUP BY level
            ''')
            
            level_distribution = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Get most common plagiarism types
            cursor.execute('''
                SELECT plagiarism_type, COUNT(*) as count
                FROM plagiarism_results
                GROUP BY plagiarism_type
                ORDER BY count DESC
                LIMIT 5
            ''')
            
            type_distribution = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            'total_detections': stats.get('plagiarism_results', 0),
            'level_distribution': level_distribution,
            'type_distribution': type_distribution,
            'average_detection_time': 'N/A',  # Could be calculated if we store timestamps
            'database_stats': stats
        }