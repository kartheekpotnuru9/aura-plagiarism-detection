# Aura: Academic Research Assistant - Project Completion Guide

## 📋 Project Overview

**Aura** is an AI-powered academic research assistant with two main features:
1. **Semantic Plagiarism Detector**: Analyzes research papers to find similar content
2. **Research Discovery Engine**: Finds relevant researchers based on topic queries

## 🔍 Current Status

### ✅ What's Working:
- ✓ Graph database created with Neo4j (`build_graph.py`)
- ✓ Data exported to CSV files (`export_graph.py`)
  - `nodes.csv`: 7,623 nodes (Papers, Authors, Concepts)
  - `relationships.csv`: 3,838 relationships (WROTE, HAS_CONCEPT)
- ✓ Streamlit UI application (`app.py`)

### ❌ What's Missing:
- ✗ **Trained GNN Model** (`classifier.pth`)

## 🚀 Step-by-Step Completion Instructions

### Step 1: Verify Your Environment

Make sure you have all required packages installed:

```powershell
pip install torch torch-geometric sentence-transformers streamlit pdfplumber pandas numpy scikit-learn
```

### Step 2: Train the GNN Model

**This is the CRITICAL missing piece!** Run the training script:

```powershell
python train_gnn_model.py
```

**What this does:**
- Loads your `nodes.csv` and `relationships.csv` data
- Creates text embeddings for all papers using SentenceTransformer
- Builds a heterogeneous graph with Papers, Authors, and Concepts
- Trains a Graph Neural Network to predict Paper-Concept relationships
- Saves the trained model as `classifier.pth`

**Expected output:**
- Training will take 5-15 minutes depending on your hardware
- You'll see progress bars for encoding papers
- Training epochs with loss and accuracy metrics
- Final message: "Training complete! Best validation accuracy: X.XXXX"

**Training parameters:**
- Hidden channels: 256
- Output channels: 128
- Learning rate: 0.001
- Max epochs: 50 (with early stopping)
- Train/Val split: 80/20

### Step 3: Verify the Model File

After training, check that `classifier.pth` exists:

```powershell
ls classifier.pth
```

You should see a file around 5-20 MB in size.

### Step 4: Run the Application

Launch the Streamlit app:

```powershell
streamlit run app.py
```

The app will open in your browser (usually `http://localhost:8501`)

### Step 5: Test the Features

#### Test 1: Semantic Plagiarism Detector
1. Click on the "Semantic Plagiarism Detector" tab
2. Upload a research paper PDF
3. The app will show the top 3 most similar papers with similarity scores

#### Test 2: Research Discovery Engine
1. Click on the "Research Discovery Engine" tab
2. Enter a research topic (e.g., "machine learning", "natural language processing")
3. The app will show the top 3 researchers working on that topic

## 📊 Architecture Details

### Graph Structure:
```
Nodes:
  - Paper: Research papers with full text embeddings (384-dim vectors)
  - Author: Authors with one-hot encodings
  - Concept: Key phrases/concepts with one-hot encodings

Relationships:
  - WROTE: Author → Paper (authorship)
  - HAS_CONCEPT: Paper → Concept (paper topics)
```

### Model Architecture:
```
GNN (GraphSAGE):
  - Conv Layer 1: variable input → 256 hidden channels
  - ReLU activation + Dropout (0.5)
  - Conv Layer 2: 256 → 128 output channels

Classifier:
  - Edge classification via dot product
  - Predicts Paper-Concept relationships
```

### Data Flow:
```
1. PDF Upload → Extract Text (pdfplumber)
2. Text → Embedding (SentenceTransformer: all-MiniLM-L6-v2)
3. Embedding → Similarity Search (Cosine Similarity)
4. Top-K Papers → Find Authors (Graph Traversal)
```

## 🔧 Troubleshooting

### Issue: "classifier.pth not found"
**Solution:** Run `python train_gnn_model.py` first

### Issue: "CUDA out of memory"
**Solution:** The training script automatically uses CPU if CUDA is unavailable. If you have GPU but get OOM errors:
- Reduce batch size in training script
- Use a smaller model (reduce hidden_channels to 128)

### Issue: Low similarity scores
**Solution:** This is normal! Semantic similarity ranges 0-1:
- 0.7-1.0: Very similar
- 0.5-0.7: Moderately similar
- 0.3-0.5: Somewhat related
- 0.0-0.3: Different topics

### Issue: "No researchers found"
**Solution:** 
- Try broader search terms
- Check if your graph has WROTE relationships
- Verify authors are connected to papers in your data

### Issue: App is slow
**Solution:**
- First load is slow (building embeddings) - this is cached
- Subsequent loads are much faster
- Consider reducing MAX_RESULTS in `build_graph.py` if rebuilding

## 📁 File Structure

```
project/
├── app.py                      # Main Streamlit application
├── train_gnn_model.py          # GNN model training script (NEW!)
├── build_graph.py              # Neo4j graph builder (data ingestion)
├── export_graph.py             # Export Neo4j to CSV
├── nodes.csv                   # Node data (Papers, Authors, Concepts)
├── relationships.csv           # Edge data (WROTE, HAS_CONCEPT)
├── classifier.pth              # Trained GNN model (created by training)
├── requirements.txt            # Python dependencies
└── PROJECT_COMPLETION_GUIDE.md # This file
```

## 🎯 Next Steps (Optional Enhancements)

1. **Improve Model Performance:**
   - Collect more training data
   - Experiment with different GNN architectures (GAT, GCN)
   - Use larger embedding models (e.g., all-mpnet-base-v2)

2. **Add More Features:**
   - Citation network visualization
   - Temporal analysis (paper trends over time)
   - Author collaboration network
   - Concept clustering and topic modeling

3. **Optimize Performance:**
   - Use FAISS for faster similarity search
   - Implement batch processing for large PDFs
   - Add caching for frequently searched terms

4. **Deploy to Production:**
   - Use Docker for containerization
   - Deploy to cloud (Streamlit Cloud, AWS, GCP)
   - Add authentication and user management

## 📝 Important Notes

1. **First Run:** The first time you run the app, it will:
   - Download the SentenceTransformer model (~80MB)
   - Encode all papers (may take 1-2 minutes)
   - Cache everything for future runs

2. **Data Privacy:** Currently, all papers are encoded locally. No data is sent to external services except for downloading the initial embedding model.

3. **Model Accuracy:** The GNN model predicts Paper-Concept relationships. Higher validation accuracy means better understanding of research topics, which improves researcher discovery.

4. **Scalability:** The current implementation handles thousands of papers. For larger datasets (100k+ papers):
   - Consider using approximate nearest neighbor search (FAISS, Annoy)
   - Implement database indexing
   - Use distributed computing frameworks

## 🆘 Support

If you encounter issues:
1. Check the error messages carefully
2. Verify all CSV files exist and have data
3. Ensure all dependencies are installed
4. Check Python version (3.8+ recommended)
5. Review the troubleshooting section above

## ✅ Success Criteria

You'll know the project is complete when:
- ✓ `classifier.pth` exists and is loaded successfully
- ✓ Streamlit app launches without errors
- ✓ You can upload a PDF and get similarity results
- ✓ You can search for researchers and get results
- ✓ No warning messages about missing models

---

**Good luck! 🚀**
