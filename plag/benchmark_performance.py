"""
Performance Benchmark for Aura Plagiarism Detection
Tests detection speed with different database sizes
"""

import os
import sys
import time
import tempfile
from typing import Dict, List

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from modules import PlagiarismDetector

def create_test_document(content: str, filename: str = "test.txt") -> str:
    """Create a temporary test document"""
    temp_dir = tempfile.gettempdir()
    test_file_path = os.path.join(temp_dir, filename)
    
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return test_file_path

def benchmark_detection_speed():
    """Benchmark plagiarism detection performance"""
    
    print("⚡ Aura Performance Benchmark")
    print("=" * 60)
    
    # Initialize
    db_manager = DatabaseManager()
    detector = PlagiarismDetector(db_manager)
    
    # Get database size
    stats = db_manager.get_database_stats()
    papers_count = stats.get('papers', 0)
    
    print(f"\n📊 Database Size: {papers_count} papers")
    print(f"📊 Authors: {stats.get('authors', 0)}")
    print(f"📊 Topics: {stats.get('topics', 0)}")
    
    # Test documents of different sizes
    test_cases = [
        {
            'name': 'Short Text (50 words)',
            'content': ' '.join(['This is a test sentence about machine learning and neural networks.'] * 10)
        },
        {
            'name': 'Medium Text (200 words)',
            'content': ' '.join(['Deep learning has revolutionized computer vision. Neural networks can now classify images with human-level accuracy. Convolutional networks are particularly effective for visual tasks.'] * 15)
        },
        {
            'name': 'Long Text (500 words)',
            'content': '''Deep learning has revolutionized the field of computer vision, particularly in image classification tasks. 
            Convolutional Neural Networks have become the foundation of modern image classification systems. 
            The introduction of architectures like LeNet, AlexNet, and VGGNet laid the groundwork for more advanced models. 
            ResNet introduced residual connections, enabling the training of much deeper networks by addressing the vanishing gradient problem.
            DenseNet further improved upon these concepts by connecting each layer to every other layer in a feed-forward fashion.
            This approach reduces the number of parameters while improving gradient flow through the network.
            EfficientNet optimized the balance between model accuracy and computational efficiency through compound scaling.
            Modern architectures achieve state-of-the-art performance on standard benchmarks including ImageNet, CIFAR-10, and CIFAR-100.
            The field continues to evolve with new innovations in attention mechanisms, transformer architectures, and self-supervised learning.
            Transfer learning has made it possible to apply pre-trained models to new tasks with limited data.
            Data augmentation techniques help improve model generalization and reduce overfitting.
            ''' * 5
        }
    ]
    
    print("\n" + "=" * 60)
    print("🔬 Running Performance Tests...")
    print("=" * 60)
    
    results = []
    
    for test_case in test_cases:
        print(f"\n📝 Test: {test_case['name']}")
        print(f"📏 Text length: {len(test_case['content'])} characters")
        print(f"📏 Word count: {len(test_case['content'].split())} words")
        
        # Create test file
        test_file = create_test_document(test_case['content'], "benchmark.txt")
        
        # Measure detection time
        start_time = time.time()
        
        try:
            result = detector.detect_plagiarism(test_file)
            
            detection_time = time.time() - start_time
            
            print(f"⏱️  Detection Time: {detection_time:.2f} seconds")
            print(f"📊 Plagiarism Score: {result.overall_score:.1f}%")
            print(f"🔢 Matches Found: {result.total_matches}")
            
            # Calculate performance metrics
            chars_per_second = len(test_case['content']) / detection_time
            papers_per_second = papers_count / detection_time if papers_count > 0 else 0
            
            print(f"⚡ Speed: {chars_per_second:.0f} chars/sec")
            print(f"⚡ Papers compared: {papers_per_second:.1f} papers/sec")
            
            results.append({
                'name': test_case['name'],
                'text_length': len(test_case['content']),
                'word_count': len(test_case['content'].split()),
                'detection_time': detection_time,
                'papers_compared': papers_count,
                'matches_found': result.total_matches,
                'chars_per_second': chars_per_second,
                'papers_per_second': papers_per_second
            })
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        finally:
            # Clean up
            if os.path.exists(test_file):
                os.remove(test_file)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Performance Summary")
    print("=" * 60)
    
    if results:
        avg_time = sum(r['detection_time'] for r in results) / len(results)
        avg_speed = sum(r['chars_per_second'] for r in results) / len(results)
        
        print(f"\n📈 Average Detection Time: {avg_time:.2f} seconds")
        print(f"⚡ Average Speed: {avg_speed:.0f} characters/second")
        print(f"📊 Database Size: {papers_count} papers")
        
        print("\n📋 Detailed Results:")
        print(f"{'Test':<25} {'Time (s)':<12} {'Speed (c/s)':<15} {'Matches':<10}")
        print("-" * 62)
        
        for r in results:
            print(f"{r['name']:<25} {r['detection_time']:<12.2f} {r['chars_per_second']:<15.0f} {r['matches_found']:<10}")
        
        # Performance rating
        print("\n🎯 Performance Rating:")
        if avg_time < 10:
            print("✅ EXCELLENT - Very fast detection")
        elif avg_time < 30:
            print("✅ GOOD - Acceptable performance")
        elif avg_time < 60:
            print("⚠️  FAIR - Usable but could be faster")
        else:
            print("⚠️  SLOW - Consider optimizing or reducing database size")
        
        # Recommendations
        print("\n💡 Performance Tips:")
        if papers_count == 0:
            print("⚠️  Database is empty - add papers for meaningful plagiarism detection")
        elif papers_count < 20:
            print("💡 Small database - consider adding more papers for better coverage")
        elif papers_count > 100:
            print("💡 Large database - performance is optimized but may slow with 200+ papers")
        else:
            print("✅ Good database size for optimal performance and coverage")
        
        if avg_time > 30:
            print("💡 Consider reducing max papers to compare (currently 50)")
            print("💡 Try shorter documents for faster testing")
    
    return results

if __name__ == "__main__":
    benchmark_detection_speed()