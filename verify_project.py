"""
Project Verification Script
Checks if all required files and dependencies are ready
"""

import sys
import os
from pathlib import Path

def check_mark(condition):
    return "✓" if condition else "✗"

def main():
    print("=" * 80)
    print("AURA PROJECT VERIFICATION")
    print("=" * 80)
    
    all_checks_passed = True
    
    # Check 1: Required Files
    print("\n[1] Checking Required Files...")
    required_files = {
        'nodes.csv': 'Graph node data',
        'relationships.csv': 'Graph relationship data',
        'app.py': 'Main Streamlit application',
        'train_gnn_model.py': 'GNN training script',
        'build_graph.py': 'Neo4j graph builder',
        'export_graph.py': 'Neo4j export script'
    }
    
    for filename, description in required_files.items():
        exists = os.path.exists(filename)
        status = check_mark(exists)
        print(f"   {status} {filename:25s} - {description}")
        if not exists:
            all_checks_passed = False
    
    # Check 2: Optional Files
    print("\n[2] Checking Optional Files...")
    optional_files = {
        'classifier.pth': 'Trained GNN model (run train_gnn_model.py to create)',
        'requirements.txt': 'Python dependencies'
    }
    
    for filename, description in optional_files.items():
        exists = os.path.exists(filename)
        status = check_mark(exists)
        print(f"   {status} {filename:25s} - {description}")
    
    # Check 3: Python Version
    print("\n[3] Checking Python Version...")
    python_version = sys.version_info
    version_ok = python_version >= (3, 8)
    status = check_mark(version_ok)
    print(f"   {status} Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    if not version_ok:
        print("   ⚠️  Python 3.8+ is recommended")
        all_checks_passed = False
    
    # Check 4: Required Packages
    print("\n[4] Checking Required Packages...")
    required_packages = [
        'torch',
        'torch_geometric',
        'sentence_transformers',
        'streamlit',
        'pandas',
        'pdfplumber',
        'numpy',
        'sklearn'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'torch_geometric':
                __import__('torch_geometric')
            elif package == 'sklearn':
                __import__('sklearn')
            else:
                __import__(package)
            print(f"   ✓ {package}")
        except ImportError:
            print(f"   ✗ {package} (MISSING)")
            missing_packages.append(package)
            all_checks_passed = False
    
    # Check 5: Data Files Content
    print("\n[5] Checking Data Files Content...")
    try:
        import pandas as pd
        
        # Check nodes.csv
        if os.path.exists('nodes.csv'):
            nodes_df = pd.read_csv('nodes.csv')
            print(f"   ✓ nodes.csv: {len(nodes_df)} rows")
            print(f"      - Papers: {len(nodes_df[nodes_df['label'] == 'Paper'])}")
            print(f"      - Authors: {len(nodes_df[nodes_df['label'] == 'Author'])}")
            print(f"      - Concepts: {len(nodes_df[nodes_df['label'] == 'Concept'])}")
        
        # Check relationships.csv
        if os.path.exists('relationships.csv'):
            rels_df = pd.read_csv('relationships.csv')
            print(f"   ✓ relationships.csv: {len(rels_df)} rows")
            print(f"      - WROTE: {len(rels_df[rels_df['type'] == 'WROTE'])}")
            print(f"      - HAS_CONCEPT: {len(rels_df[rels_df['type'] == 'HAS_CONCEPT'])}")
    except Exception as e:
        print(f"   ✗ Error reading data files: {e}")
        all_checks_passed = False
    
    # Check 6: Model File
    print("\n[6] Checking Model File...")
    if os.path.exists('classifier.pth'):
        size_mb = os.path.getsize('classifier.pth') / (1024 * 1024)
        print(f"   ✓ classifier.pth exists ({size_mb:.2f} MB)")
        print("   → Ready to run the application!")
    else:
        print("   ✗ classifier.pth not found")
        print("   → You need to train the model first!")
        print("   → Run: python train_gnn_model.py")
    
    # Summary
    print("\n" + "=" * 80)
    if all_checks_passed and os.path.exists('classifier.pth'):
        print("✅ ALL CHECKS PASSED - PROJECT IS READY!")
        print("\nNext step: Run the application")
        print("   streamlit run app.py")
    elif all_checks_passed and not os.path.exists('classifier.pth'):
        print("⚠️  ALMOST READY - NEED TO TRAIN MODEL")
        print("\nNext step: Train the GNN model")
        print("   python train_gnn_model.py")
        print("\nThen run the application:")
        print("   streamlit run app.py")
    else:
        print("❌ SOME CHECKS FAILED - SEE ABOVE FOR DETAILS")
        if missing_packages:
            print("\nInstall missing packages:")
            print(f"   pip install {' '.join(missing_packages)}")
    print("=" * 80)

if __name__ == "__main__":
    main()
