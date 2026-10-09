"""
Train GNN Model for Academic Research Assistant
This script trains a Graph Neural Network on the nodes.csv and relationships.csv data
"""

import pandas as pd
import torch
import torch.nn.functional as F
from torch_geometric.data import HeteroData
from torch_geometric.nn import SAGEConv, to_hetero
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.model_selection import train_test_split

print("=" * 80)
print("GNN Model Training for Academic Research Assistant")
print("=" * 80)

# --- Step 1: Define Model Architecture ---
class GNN(torch.nn.Module):
    def __init__(self, hidden_channels, out_channels):
        super().__init__()
        self.conv1 = SAGEConv((-1, -1), hidden_channels)
        self.conv2 = SAGEConv(hidden_channels, out_channels)
    
    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        x = F.dropout(x, p=0.5, training=self.training)
        return self.conv2(x, edge_index)

class Classifier(torch.nn.Module):
    def forward(self, x_paper, x_concept, edge_label_index):
        edge_feat_paper = x_paper[edge_label_index[0]]
        edge_feat_concept = x_concept[edge_label_index[1]]
        return (edge_feat_paper * edge_feat_concept).sum(dim=-1)

# --- Step 2: Load Data ---
print("\n[1/6] Loading data from CSV files...")
nodes_df = pd.read_csv("nodes.csv")
rels_df = pd.read_csv("relationships.csv")
nodes_df['text'] = nodes_df['text'].fillna('')

print(f"   Loaded {len(nodes_df)} nodes")
print(f"   Loaded {len(rels_df)} relationships")
print(f"   Node types: {nodes_df['label'].value_counts().to_dict()}")

# --- Step 3: Create Embeddings ---
print("\n[2/6] Creating text embeddings for papers...")
text_model = SentenceTransformer('all-MiniLM-L6-v2')

# --- Step 4: Build HeteroData Object ---
print("\n[3/6] Building heterogeneous graph...")
data = HeteroData()
node_mappings = {}

# Create node features for each type
for label in nodes_df['label'].unique():
    mask = nodes_df['label'] == label
    df_type = nodes_df[mask]
    node_mappings[label] = {node_id: i for i, node_id in enumerate(df_type['nodeId'])}
    
    if label == 'Paper':
        paper_texts = df_type['text'].tolist()
        print(f"   Encoding {len(paper_texts)} papers...")
        data[label].x = torch.tensor(text_model.encode(paper_texts, show_progress_bar=True))
        print(f"   Paper embeddings shape: {data[label].x.shape}")
    else:
        # One-hot encoding for Author and Concept nodes
        data[label].x = torch.eye(len(df_type))
        print(f"   {label} nodes: {len(df_type)} (one-hot encoded)")

# Create edges with BIDIRECTIONAL relationships (fixes GNN message passing)
schema = {
    'WROTE': ('Author', 'wrote', 'Paper'),
    'WRITTEN_BY': ('Paper', 'written_by', 'Author'),  # Reverse edge
    'HAS_CONCEPT': ('Paper', 'has_concept', 'Concept'),
    'CONCEPT_OF': ('Concept', 'concept_of', 'Paper')  # Reverse edge
}

for edge_type_str, (source_label, rel_name, target_label) in schema.items():
    # Check if this is a reverse edge
    if edge_type_str == 'WRITTEN_BY':
        mask = rels_df['type'] == 'WROTE'
        if mask.any():
            source_indices = rels_df[mask]['target'].map(node_mappings[source_label]).values  # Reversed
            target_indices = rels_df[mask]['source'].map(node_mappings[target_label]).values  # Reversed
        else:
            continue
    elif edge_type_str == 'CONCEPT_OF':
        mask = rels_df['type'] == 'HAS_CONCEPT'
        if mask.any():
            source_indices = rels_df[mask]['target'].map(node_mappings[source_label]).values  # Reversed
            target_indices = rels_df[mask]['source'].map(node_mappings[target_label]).values  # Reversed
        else:
            continue
    else:
        mask = rels_df['type'] == edge_type_str
        if not mask.any():
            print(f"   Warning: No edges found for {edge_type_str}")
            continue
        source_indices = rels_df[mask]['source'].map(node_mappings[source_label]).values
        target_indices = rels_df[mask]['target'].map(node_mappings[target_label]).values
    
    # Remove NaN values (unmapped nodes)
    valid_mask = ~(pd.isna(source_indices) | pd.isna(target_indices))
    source_indices = source_indices[valid_mask].astype(int)
    target_indices = target_indices[valid_mask].astype(int)
    
    edge_index = torch.tensor([source_indices, target_indices], dtype=torch.long)
    data[source_label, rel_name, target_label].edge_index = edge_index
    print(f"   {edge_type_str}: {edge_index.shape[1]} edges ({source_label} -> {target_label})")

print(f"\n   Graph metadata: {data.metadata()}")

# --- Step 5: Prepare Training Data ---
print("\n[4/6] Preparing training/validation splits...")

# Get paper-concept edges for training
paper_concept_edges = data['Paper', 'has_concept', 'Concept'].edge_index.t().numpy()

# Split edges into train/val
train_edges, val_edges = train_test_split(
    paper_concept_edges, 
    test_size=0.2, 
    random_state=42
)

# Create negative samples (random pairs that don't exist)
num_papers = data['Paper'].x.shape[0]
num_concepts = data['Concept'].x.shape[0]

def create_negative_samples(num_samples, existing_edges):
    """Create negative samples that don't exist in the graph"""
    existing_set = set(map(tuple, existing_edges))
    negatives = []
    
    while len(negatives) < num_samples:
        paper_idx = np.random.randint(0, num_papers)
        concept_idx = np.random.randint(0, num_concepts)
        if (paper_idx, concept_idx) not in existing_set:
            negatives.append([paper_idx, concept_idx])
    
    return np.array(negatives)

train_neg = create_negative_samples(len(train_edges), paper_concept_edges)
val_neg = create_negative_samples(len(val_edges), paper_concept_edges)

# Convert to tensors
train_pos_edge_index = torch.tensor(train_edges.T, dtype=torch.long)
train_neg_edge_index = torch.tensor(train_neg.T, dtype=torch.long)
val_pos_edge_index = torch.tensor(val_edges.T, dtype=torch.long)
val_neg_edge_index = torch.tensor(val_neg.T, dtype=torch.long)

print(f"   Training: {len(train_edges)} positive, {len(train_neg)} negative edges")
print(f"   Validation: {len(val_edges)} positive, {len(val_neg)} negative edges")

# --- Step 6: Initialize and Train Model ---
print("\n[5/6] Initializing model...")
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"   Using device: {device}")

# Initialize models
gnn_model = GNN(hidden_channels=256, out_channels=128)
gnn_model = to_hetero(gnn_model, data.metadata(), aggr='sum')
classifier = Classifier()

# Move to device
gnn_model = gnn_model.to(device)
classifier = classifier.to(device)
data = data.to(device)

# Initialize lazy parameters by doing a forward pass
print("\nInitializing model parameters...")
with torch.no_grad():
    _ = gnn_model(data.x_dict, data.edge_index_dict)
print("   Parameters initialized!")

# Optimizer
optimizer = torch.optim.Adam(
    list(gnn_model.parameters()) + list(classifier.parameters()), 
    lr=0.001
)

def train_epoch():
    gnn_model.train()
    classifier.train()
    optimizer.zero_grad()
    
    # Forward pass through GNN
    x_dict = gnn_model(data.x_dict, data.edge_index_dict)
    
    # Positive samples
    pos_pred = classifier(
        x_dict['Paper'], 
        x_dict['Concept'], 
        train_pos_edge_index
    )
    
    # Negative samples
    neg_pred = classifier(
        x_dict['Paper'], 
        x_dict['Concept'], 
        train_neg_edge_index
    )
    
    # Binary cross-entropy loss
    pos_loss = F.binary_cross_entropy_with_logits(pos_pred, torch.ones_like(pos_pred))
    neg_loss = F.binary_cross_entropy_with_logits(neg_pred, torch.zeros_like(neg_pred))
    loss = pos_loss + neg_loss
    
    loss.backward()
    optimizer.step()
    
    return loss.item()

@torch.no_grad()
def validate():
    gnn_model.eval()
    classifier.eval()
    
    # Forward pass
    x_dict = gnn_model(data.x_dict, data.edge_index_dict)
    
    # Positive samples
    pos_pred = classifier(
        x_dict['Paper'], 
        x_dict['Concept'], 
        val_pos_edge_index
    )
    
    # Negative samples
    neg_pred = classifier(
        x_dict['Paper'], 
        x_dict['Concept'], 
        val_neg_edge_index
    )
    
    # Calculate accuracy
    pos_correct = (pos_pred > 0).sum().item()
    neg_correct = (neg_pred < 0).sum().item()
    total = len(val_pos_edge_index[0]) + len(val_neg_edge_index[0])
    accuracy = (pos_correct + neg_correct) / total
    
    # Calculate loss
    pos_loss = F.binary_cross_entropy_with_logits(pos_pred, torch.ones_like(pos_pred))
    neg_loss = F.binary_cross_entropy_with_logits(neg_pred, torch.zeros_like(neg_pred))
    val_loss = (pos_loss + neg_loss).item()
    
    return val_loss, accuracy

# Training loop
print("\n[6/6] Training model...")
print("-" * 80)

num_epochs = 50
best_val_acc = 0
patience = 10
patience_counter = 0

for epoch in range(1, num_epochs + 1):
    train_loss = train_epoch()
    val_loss, val_acc = validate()
    
    if epoch % 5 == 0:
        print(f"Epoch {epoch:3d} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f}")
    
    # Save best model
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save(gnn_model.state_dict(), 'classifier.pth')
        patience_counter = 0
        if epoch % 5 == 0:
            print(f"   ✓ New best model saved! (Accuracy: {val_acc:.4f})")
    else:
        patience_counter += 1
    
    # Early stopping
    if patience_counter >= patience:
        print(f"\nEarly stopping at epoch {epoch}")
        break

print("\n" + "=" * 80)
print(f"Training complete! Best validation accuracy: {best_val_acc:.4f}")
print(f"Model saved to: classifier.pth")
print("=" * 80)
print("\nYou can now run the Streamlit app with: streamlit run app.py")
