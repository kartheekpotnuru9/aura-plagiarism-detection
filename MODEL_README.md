# AURA Model Files

This directory should contain the trained GNN model file:

## Required Files

- `classifier.pth` - Trained GraphSAGE model (~5-10 MB)

## How to Get the Model

### Option 1: Download Pre-trained Model
Due to GitHub's file size limitations, the model is hosted separately:

**[Download classifier.pth](https://github.com/mohan120105/aura-plagiarism-detection/releases/latest)**

Place the downloaded file in the project root directory.

### Option 2: Train Your Own Model

#### Local Training (CPU)
```bash
python train_gnn_model.py
```
This will take 10-30 minutes on CPU.

#### Kaggle Training (GPU - Recommended)
1. Upload `train_gnn_kaggle.ipynb` to Kaggle
2. Enable GPU accelerator (faster, free)
3. Run all cells
4. Download the generated `classifier.pth`
5. Place it in this directory

See [KAGGLE_TRAINING_GUIDE.md](../KAGGLE_TRAINING_GUIDE.md) for detailed instructions.

## Graph Data Files

You'll also need:
- `nodes.csv` - Graph nodes (papers, authors, concepts)
- `relationships.csv` - Graph edges

These can be generated using:
```bash
python build_graph.py
```

Or download from the releases page.

## File Sizes (Approximate)

- `classifier.pth`: 5-10 MB
- `nodes.csv`: 1-2 MB
- `relationships.csv`: 200-500 KB

**Note**: These files are excluded from Git repository to keep it lightweight. They must be downloaded or generated separately.
