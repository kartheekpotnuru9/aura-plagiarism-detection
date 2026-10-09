"""
Test script for Aura plagiarism detection system
Run this to verify the system is working correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager, DatabaseExporter
from modules import PDFProcessor, SemanticSimilarityEngine, KnowledgeGraphBuilder, PlagiarismDetector
from utils import setup_logging
import io

def test_database():
    """Test database functionality"""
    print("🔧 Testing database functionality...")
    
    try:
        db = DatabaseManager()
        
        # Add a test paper
        paper_id = db.add_paper(
            title="Test Paper on Machine Learning",
            content="This is a test paper about machine learning algorithms and neural networks.",
            abstract="A comprehensive study of machine learning techniques.",
            authors=["John Doe", "Jane Smith"],
            keywords=["machine learning", "neural networks", "algorithms"],
            file_hash="test_hash_123"
        )
        
        print(f"✅ Added test paper with ID: {paper_id}")
        
        # Test retrieval
        paper = db.get_paper_by_hash("test_hash_123")
        if paper:
            print(f"✅ Retrieved paper: {paper['title']}")
        
        # Test statistics
        stats = db.get_database_stats()
        print(f"✅ Database stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_pdf_processor():
    """Test PDF processing (without actual PDF)"""
    print("\n🔧 Testing PDF processor...")
    
    try:
        processor = PDFProcessor()
        
        # Test text cleaning
        dirty_text = "This  is   a   test\n\n  with    extra   spaces."
        cleaned_text = processor._clean_text(dirty_text)
        print(f"✅ Text cleaning: '{dirty_text}' -> '{cleaned_text}'")
        
        # Test sentence extraction
        test_text = "This is the first sentence. This is the second sentence. And this is the third."
        sentences = processor.extract_sentences(test_text)
        print(f"✅ Extracted {len(sentences)} sentences")
        
        # Test text chunking
        chunks = processor.chunk_text(test_text, chunk_size=5)
        print(f"✅ Created {len(chunks)} text chunks")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF processor test failed: {e}")
        return False

def test_similarity_engine():
    """Test semantic similarity engine"""
    print("\n🔧 Testing similarity engine...")
    
    try:
        engine = SemanticSimilarityEngine()
        
        # Test similarity computation
        text1 = "Machine learning is a subset of artificial intelligence."
        text2 = "AI includes machine learning as one of its components."
        
        similarities = engine.compute_semantic_similarity(text1, text2)
        print(f"✅ Similarity scores: {similarities}")
        
        # Test paraphrase detection
        result = engine.detect_paraphrasing(text1, text2)
        print(f"✅ Paraphrase detection: {result['is_paraphrased']} (confidence: {result['paraphrase_confidence']:.2f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Similarity engine test failed: {e}")
        return False

def test_knowledge_graph():
    """Test knowledge graph builder"""
    print("\n🔧 Testing knowledge graph builder...")
    
    try:
        kg_builder = KnowledgeGraphBuilder()
        
        # Test with sample papers
        sample_papers = [
            {
                'id': 1,
                'title': 'Deep Learning for Image Classification',
                'content': 'This paper presents deep learning methods for image classification using convolutional neural networks.',
                'abstract': 'We propose a CNN-based approach for image classification.',
                'authors': ['Alice Johnson', 'Bob Wilson']
            },
            {
                'id': 2,
                'title': 'Natural Language Processing with Transformers',
                'content': 'This work explores transformer architectures for natural language processing tasks.',
                'abstract': 'Transformers have revolutionized NLP applications.',
                'authors': ['Carol Davis', 'David Brown']
            }
        ]
        
        graph = kg_builder.build_knowledge_graph(sample_papers)
        stats = kg_builder.get_graph_statistics()
        
        print(f"✅ Built knowledge graph with {stats.get('total_nodes', 0)} nodes and {stats.get('total_edges', 0)} edges")
        
        return True
        
    except Exception as e:
        print(f"❌ Knowledge graph test failed: {e}")
        return False

def test_plagiarism_detector():
    """Test plagiarism detection"""
    print("\n🔧 Testing plagiarism detector...")
    
    try:
        db = DatabaseManager()
        detector = PlagiarismDetector(db)
        
        # Add a reference paper
        ref_paper_id = db.add_paper(
            title="Reference Paper on Neural Networks",
            content="Neural networks are computational models inspired by biological neural networks. They consist of interconnected nodes called neurons that process information.",
            abstract="An introduction to neural networks and their applications.",
            authors=["Expert Author"],
            file_hash="ref_hash_456"
        )
        
        # Test with potentially plagiarized content
        test_content = "Neural networks are computational models based on biological neural networks. These systems use interconnected nodes known as neurons for information processing."
        
        result = detector.detect_plagiarism(test_content)
        
        print(f"✅ Plagiarism detection completed:")
        print(f"   - Overall score: {result.overall_score:.2%}")
        print(f"   - Level: {result.plagiarism_level}")
        print(f"   - Matches found: {result.total_matches}")
        print(f"   - Coverage: {result.coverage_percentage:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Plagiarism detector test failed: {e}")
        return False

def test_export_functionality():
    """Test database export functionality"""
    print("\n🔧 Testing export functionality...")
    
    try:
        db = DatabaseManager()
        exporter = DatabaseExporter(db)
        
        # Test export summary
        summary = exporter.get_export_summary()
        print(f"✅ Export summary: {summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ Export test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Aura System Tests\n")
    
    # Setup logging
    logger = setup_logging("INFO")
    
    tests = [
        ("Database", test_database),
        ("PDF Processor", test_pdf_processor),
        ("Similarity Engine", test_similarity_engine),
        ("Knowledge Graph", test_knowledge_graph),
        ("Plagiarism Detector", test_plagiarism_detector),
        ("Export Functionality", test_export_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The Aura system is ready to use.")
        print("\n🚀 To start the application, run:")
        print("   streamlit run app.py")
    else:
        print("⚠️ Some tests failed. Please check the error messages above.")
        print("💡 You may need to install additional dependencies:")
        print("   pip install -r requirements.txt")

if __name__ == "__main__":
    main()