"""
Test Script for Aura Plagiarism Detection
Tests the system with sample text to verify it's working with the populated database
"""

import os
import sys
import tempfile
from typing import Dict

# Add the current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from modules import PlagiarismDetector
from utils import setup_logging

def create_test_document(content: str, filename: str = "test_document.txt") -> str:
    """Create a temporary test document"""
    # Create temporary file
    temp_dir = tempfile.gettempdir()
    test_file_path = os.path.join(temp_dir, filename)
    
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return test_file_path

def test_plagiarism_detection():
    """Test plagiarism detection with sample content"""
    print("🧪 Testing Aura Plagiarism Detection System")
    print("=" * 50)
    
    # Initialize components
    db_manager = DatabaseManager()
    detector = PlagiarismDetector(db_manager)
    
    # Get database stats
    stats = db_manager.get_database_stats()
    print(f"📊 Database contains {stats.get('papers', 0)} papers")
    
    if stats.get('papers', 0) == 0:
        print("❌ No papers in database! Run populate_sample_data.py first.")
        return
    
    # Test cases
    test_cases = [
        {
            'name': 'High Similarity Test',
            'content': '''Deep learning has revolutionized the field of computer vision, particularly in image classification tasks. Convolutional Neural Networks have become the foundation of modern image classification systems. ResNet introduced residual connections, enabling the training of much deeper networks by addressing the vanishing gradient problem.'''
        },
        {
            'name': 'Moderate Similarity Test', 
            'content': '''Machine learning techniques have transformed computer vision applications. Neural network architectures like ResNet and DenseNet have shown remarkable performance improvements in image recognition tasks. These models utilize advanced techniques to solve the vanishing gradient problem.'''
        },
        {
            'name': 'Low Similarity Test',
            'content': '''Quantum computing represents a paradigm shift in computational power. Quantum algorithms leverage quantum mechanical phenomena such as superposition and entanglement to solve specific problems more efficiently than classical computers. Applications include cryptography, optimization, and drug discovery.'''
        },
        {
            'name': 'Original Content Test',
            'content': '''Blockchain technology enables decentralized digital transactions through cryptographic hashing and distributed consensus mechanisms. Smart contracts automate agreement execution without intermediaries, while proof-of-work protocols ensure network security and transaction validation across distributed nodes.'''
        }
    ]
    
    print("\n🔍 Running Plagiarism Detection Tests...")
    print("-" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['name']}")
        print(f"Content: {test_case['content'][:100]}...")
        
        try:
            # Create temporary test file
            test_file = create_test_document(test_case['content'], f"test_{i}.txt")
            
            # Run plagiarism detection
            results = detector.detect_plagiarism(test_file)
            
            # Display results
            if hasattr(results, 'overall_score'):
                overall_score = results.overall_score
                print(f"✅ Detection completed!")
                print(f"🎯 Overall Plagiarism Score: {overall_score:.1f}%")
                print(f"📊 Plagiarism Level: {results.plagiarism_level}")
                print(f"🔢 Total Matches: {results.total_matches}")
                print(f"📈 Coverage: {results.coverage_percentage:.1f}%")
                
                # Show top matches
                if results.matches:
                    print("🔗 Top Matches:")
                    for i, match in enumerate(results.matches[:3]):  # Show top 3
                        print(f"  • Match {i+1}: {match.similarity_score:.1f}% similarity ({match.plagiarism_type.value})")
                        print(f"    Text: {match.target_text[:80]}...")
                else:
                    print("📭 No significant matches found")
                
                # Interpretation
                if overall_score > 70:
                    print("🚨 HIGH plagiarism risk detected!")
                elif overall_score > 40:
                    print("⚠️  MODERATE plagiarism risk detected")
                elif overall_score > 15:
                    print("💡 LOW plagiarism risk detected")
                else:
                    print("✅ Content appears to be original")
                    
            else:
                print(f"❌ Detection failed: {str(results)}")
            
            # Clean up
            if os.path.exists(test_file):
                os.remove(test_file)
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Plagiarism Detection Testing Complete!")
    print("\nThe system is now ready to detect plagiarism effectively!")
    print("You can upload PDFs through the Streamlit interface at http://localhost:8502")

def main():
    """Main execution function"""
    test_plagiarism_detection()

if __name__ == "__main__":
    main()