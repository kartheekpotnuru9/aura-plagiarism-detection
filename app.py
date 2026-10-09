import streamlit as st
import pandas as pd
import torch
import torch.nn.functional as F
from torch_geometric.data import HeteroData
from torch_geometric.nn import SAGEConv, to_hetero
from sentence_transformers import SentenceTransformer, util
import pdfplumber
import os
import re
import nltk
from typing import List, Dict, Tuple

# --- Model & Data Loading (Cached for Performance) ---

# Define the GNN and Classifier classes so Streamlit can load the models
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

@st.cache_resource
def load_models_and_data():
    """
    Loads all necessary models and data files.
    This function is cached so it only runs once.
    """
    # Load data from CSVs
    nodes_df = pd.read_csv("nodes.csv")
    rels_df = pd.read_csv("relationships.csv")
    nodes_df['text'] = nodes_df['text'].fillna('')

    # Load the SentenceTransformer model for text embeddings
    text_model = SentenceTransformer('all-MiniLM-L6-v2')

    # --- Recreate the HeteroData object ---
    data = HeteroData()
    node_mappings = {}
    for label in nodes_df['label'].unique():
        mask = nodes_df['label'] == label
        df_type = nodes_df[mask]
        node_mappings[label] = {node_id: i for i, node_id in enumerate(df_type['nodeId'])}
        if label == 'Paper':
            paper_texts = df_type['text'].tolist()
            data[label].x = torch.tensor(text_model.encode(paper_texts))
        else:
            data[label].x = torch.eye(len(df_type))
    
    # Create edges with BIDIRECTIONAL relationships (must match training!)
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
                source_indices = rels_df[mask]['target'].map(node_mappings[source_label]).values
                target_indices = rels_df[mask]['source'].map(node_mappings[target_label]).values
            else:
                continue
        elif edge_type_str == 'CONCEPT_OF':
            mask = rels_df['type'] == 'HAS_CONCEPT'
            if mask.any():
                source_indices = rels_df[mask]['target'].map(node_mappings[source_label]).values
                target_indices = rels_df[mask]['source'].map(node_mappings[target_label]).values
            else:
                continue
        else:
            mask = rels_df['type'] == edge_type_str
            if not mask.any(): 
                continue
            source_indices = rels_df[mask]['source'].map(node_mappings[source_label]).values
            target_indices = rels_df[mask]['target'].map(node_mappings[target_label]).values
        
        edge_index = torch.tensor([source_indices, target_indices], dtype=torch.long)
        data[source_label, rel_name, target_label].edge_index = edge_index

    # --- Load the trained GNN model ---
    # Define model architecture
    gnn_model = GNN(hidden_channels=256, out_channels=128)
    gnn_model = to_hetero(gnn_model, data.metadata(), aggr='sum')
    
    # Load the saved state dictionary with error handling
    try:
        gnn_model.load_state_dict(torch.load('classifier.pth', map_location=torch.device('cpu')))
        gnn_model.eval()
        st.success("✓ GNN model loaded successfully!")
    except FileNotFoundError:
        st.warning("⚠️ classifier.pth not found. Please run train_gnn_model.py first to train the model.")
    except Exception as e:
        st.warning(f"⚠️ Error loading model: {e}. Using untrained model.")
    
    gnn_model.eval()

    return gnn_model, text_model, nodes_df, rels_df, node_mappings, data

# --- Helper Functions for Backend Logic ---

def extract_text_from_pdf(uploaded_file):
    """Extracts text from an uploaded PDF file."""
    text = ""
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text(x_tolerance=2)
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None
    return text

def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using simple regex."""
    # Simple sentence splitter - splits on . ! ? followed by space and capital letter
    # This is a simplified version; for production, consider using spaCy or NLTK
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    # Clean up sentences
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]
    return sentences

def is_common_phrase(sentence: str) -> bool:
    """Check if sentence is a common academic phrase that should be ignored."""
    common_phrases = [
        "in this paper",
        "in this study",
        "we propose",
        "we present",
        "the results show",
        "as shown in",
        "it can be seen",
        "future work",
        "in conclusion",
        "to summarize"
    ]
    sentence_lower = sentence.lower()
    # If sentence is very short and contains common phrase, ignore it
    if len(sentence.split()) < 15:
        for phrase in common_phrases:
            if phrase in sentence_lower:
                return True
    return False

def analyze_sentence_similarity(
    user_sentences: List[str],
    text_model,
    nodes_df,
    top_papers: List[Dict],
    threshold: float = 0.75
) -> List[Dict]:
    """
    Analyze similarity for each sentence against matched papers.
    
    Returns list of sentence matches with details.
    """
    # Get only top matched papers' texts for efficiency
    paper_df = nodes_df[nodes_df['label'] == 'Paper'].reset_index(drop=True)
    
    sentence_matches = []
    
    # Pre-compute embeddings for user sentences (batch processing)
    user_embeddings = text_model.encode(user_sentences, convert_to_tensor=True, show_progress_bar=False)
    
    # For each top matched paper, split into sentences and compare
    for paper_info in top_papers[:10]:  # Only check top 10 papers for performance
        paper_title = paper_info['title']
        
        # Find paper text in database
        paper_row = paper_df[paper_df['title'] == paper_title]
        if paper_row.empty:
            continue
            
        paper_text = paper_row['text'].iloc[0]
        if not paper_text or len(paper_text) < 100:
            continue
        
        # Split paper into sentences
        paper_sentences = split_into_sentences(paper_text)
        if not paper_sentences:
            continue
        
        # Compute embeddings for paper sentences (batch)
        paper_embeddings = text_model.encode(paper_sentences, convert_to_tensor=True, show_progress_bar=False)
        
        # Compute similarity matrix (all user sentences vs all paper sentences)
        similarity_matrix = util.pytorch_cos_sim(user_embeddings, paper_embeddings)
        
        # For each user sentence, find best match in this paper
        for sent_idx, user_sent in enumerate(user_sentences):
            # Skip common phrases
            if is_common_phrase(user_sent):
                continue
            
            # Get similarities for this sentence
            sent_similarities = similarity_matrix[sent_idx]
            max_sim, max_idx = torch.max(sent_similarities, dim=0)
            max_sim = max_sim.item()
            
            # Only record if above threshold
            if max_sim >= threshold:
                matched_sentence = paper_sentences[max_idx.item()]
                
                sentence_matches.append({
                    'sentence_id': sent_idx,
                    'user_sentence': user_sent,
                    'source_paper': paper_title,
                    'source_sentence': matched_sentence,
                    'similarity': max_sim,
                    'is_exact': max_sim >= 0.95,
                    'is_high': max_sim >= 0.85,
                    'is_moderate': 0.75 <= max_sim < 0.85
                })
    
    return sentence_matches

def generate_detailed_report(sentence_matches: List[Dict], user_sentences: List[str]) -> Dict:
    """Generate summary statistics for the detailed report."""
    total_sentences = len(user_sentences)
    
    if not sentence_matches:
        return {
            'total_sentences': total_sentences,
            'flagged_sentences': 0,
            'flagged_percentage': 0.0,
            'unique_sources': 0,
            'exact_matches': 0,
            'high_matches': 0,
            'moderate_matches': 0
        }
    
    # Get unique flagged sentence IDs
    flagged_ids = set(m['sentence_id'] for m in sentence_matches)
    flagged_count = len(flagged_ids)
    
    # Get unique sources
    unique_sources = set(m['source_paper'] for m in sentence_matches)
    
    # Count by severity
    exact_count = sum(1 for m in sentence_matches if m['is_exact'])
    high_count = sum(1 for m in sentence_matches if m['is_high'] and not m['is_exact'])
    moderate_count = sum(1 for m in sentence_matches if m['is_moderate'])
    
    return {
        'total_sentences': total_sentences,
        'flagged_sentences': flagged_count,
        'flagged_percentage': (flagged_count / total_sentences * 100) if total_sentences > 0 else 0,
        'unique_sources': len(unique_sources),
        'exact_matches': exact_count,
        'high_matches': high_count,
        'moderate_matches': moderate_count,
        'sources_list': list(unique_sources)
    }

def display_sentence_matches(sentence_matches: List[Dict], user_sentences: List[str]):
    """Display color-coded sentence matches in Streamlit."""
    st.markdown("### 📝 Sentence-Level Analysis")
    
    if not sentence_matches:
        st.success("✅ No suspicious sentence matches found! Your paper appears highly original.")
        return
    
    # Group matches by sentence ID
    matches_by_sentence = {}
    for match in sentence_matches:
        sent_id = match['sentence_id']
        if sent_id not in matches_by_sentence:
            matches_by_sentence[sent_id] = []
        matches_by_sentence[sent_id].append(match)
    
    # Display flagged sentences
    st.write(f"**Found {len(matches_by_sentence)} flagged sentences**")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        severity_filter = st.selectbox(
            "Filter by severity:",
            ["All", "Exact Matches (≥95%)", "High Similarity (≥85%)", "Moderate (≥75%)"]
        )
    with col2:
        sort_by = st.selectbox(
            "Sort by:",
            ["Similarity (High to Low)", "Sentence Order"]
        )
    
    # Apply filters and sorting
    filtered_matches = matches_by_sentence.copy()
    
    if severity_filter != "All":
        filtered_matches = {
            sent_id: matches for sent_id, matches in filtered_matches.items()
            if any(
                (severity_filter.startswith("Exact") and m['is_exact']) or
                (severity_filter.startswith("High") and m['is_high']) or
                (severity_filter.startswith("Moderate") and m['is_moderate'])
                for m in matches
            )
        }
    
    # Sort
    if sort_by == "Similarity (High to Low)":
        sorted_items = sorted(
            filtered_matches.items(),
            key=lambda x: max(m['similarity'] for m in x[1]),
            reverse=True
        )
    else:
        sorted_items = sorted(filtered_matches.items(), key=lambda x: x[0])
    
    # Display each flagged sentence
    for sent_id, matches in sorted_items:
        # Get highest similarity match for this sentence
        top_match = max(matches, key=lambda m: m['similarity'])
        similarity = top_match['similarity']
        
        # Color code
        if similarity >= 0.95:
            color_icon = "🔴"
            severity = "CRITICAL - Nearly Identical"
            bg_color = "#ffe6e6"
        elif similarity >= 0.85:
            color_icon = "🟠"
            severity = "HIGH - Strong Similarity"
            bg_color = "#fff4e6"
        else:
            color_icon = "🟡"
            severity = "MODERATE - Similar Phrasing"
            bg_color = "#fffff0"
        
        with st.expander(
            f"{color_icon} Sentence #{sent_id + 1} | {similarity:.1%} match | {severity}",
            expanded=False
        ):
            # Show user sentence with background color
            st.markdown(
                f'<div style="background-color: {bg_color}; padding: 10px; border-radius: 5px; margin: 10px 0;">'
                f'<strong>Your Text:</strong><br>"{top_match["user_sentence"]}"</div>',
                unsafe_allow_html=True
            )
            
            # Show matched sentence
            st.markdown(
                f'<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin: 10px 0;">'
                f'<strong>Matched Text from "{top_match["source_paper"]}":</strong><br>"{top_match["source_sentence"]}"</div>',
                unsafe_allow_html=True
            )
            
            # Similarity meter (clamp to avoid edge case with 1.0)
            st.progress(min(similarity, 0.9999))
            st.caption(f"Similarity Score: {similarity:.2%}")
            
            # Recommendations
            st.markdown("**💡 Recommendation:**")
            if similarity >= 0.95:
                st.error("⚠️ Nearly identical text detected. **Action Required:**\n- Add proper citation immediately, OR\n- Completely rephrase in your own words")
            elif similarity >= 0.85:
                st.warning("⚠️ Strong similarity detected. **Suggested Actions:**\n- Verify citation exists and is properly formatted\n- Improve paraphrasing - use different sentence structure\n- Consider using direct quote with quotation marks")
            else:
                st.info("ℹ️ Moderate similarity. **Suggested Actions:**\n- Ensure proper attribution if summarizing their work\n- Review paraphrasing quality\n- Generally acceptable if properly cited")
            
            # If multiple sources match this sentence
            if len(matches) > 1:
                st.markdown(f"**Also matches {len(matches) - 1} other source(s):**")
                for other_match in matches[1:]:
                    st.caption(f"- {other_match['source_paper']} ({other_match['similarity']:.1%})")


def find_similar_papers(new_text, text_model, nodes_df, gnn_model, data, top_k=3):
    """Finds similar papers using a hybrid approach: text + GNN embeddings."""
    # Get embeddings for all papers in the database
    paper_df = nodes_df[nodes_df['label'] == 'Paper']
    
    # Step 1: Get text embedding for new paper (384-dim)
    new_text_embedding = text_model.encode(new_text, convert_to_tensor=True)
    
    # Step 2: Get text embeddings for database papers (384-dim)
    db_text_embeddings = data['Paper'].x.cpu()  # Original 384-dim text embeddings
    
    # Step 3: Calculate text-based similarity
    db_text_embeddings_normalized = F.normalize(db_text_embeddings, p=2, dim=1)
    new_text_embedding_normalized = F.normalize(new_text_embedding.unsqueeze(0), p=2, dim=1)
    text_similarities = torch.mm(new_text_embedding_normalized, db_text_embeddings_normalized.t()).squeeze()
    
    # Step 4: Get GNN-enhanced embeddings for database papers (128-dim)
    with torch.no_grad():
        gnn_model.eval()
        x_dict = gnn_model(data.x_dict, data.edge_index_dict)
        gnn_paper_embeddings = x_dict['Paper'].cpu()  # Shape: [num_papers, 128]
    
    # Step 5: Project new paper to GNN space via weighted average of top similar papers
    top_k_candidates = min(50, len(paper_df))
    top_k_values, top_k_indices = torch.topk(text_similarities, k=top_k_candidates)
    
    # Create weighted combination of GNN embeddings
    weights = F.softmax(top_k_values * 10, dim=0)  # Temperature=10
    new_gnn_embedding = torch.zeros(128)
    for i, idx in enumerate(top_k_indices):
        new_gnn_embedding += weights[i] * gnn_paper_embeddings[idx]
    
    # Step 6: Calculate GNN-based similarity
    gnn_paper_embeddings_normalized = F.normalize(gnn_paper_embeddings, p=2, dim=1)
    new_gnn_embedding_normalized = F.normalize(new_gnn_embedding.unsqueeze(0), p=2, dim=1)
    gnn_similarities = torch.mm(new_gnn_embedding_normalized, gnn_paper_embeddings_normalized.t()).squeeze()
    
    # Step 7: HYBRID SCORING - Combine both similarities
    # Text similarity is more reliable, so weight it higher
    hybrid_scores = 0.7 * text_similarities + 0.3 * gnn_similarities
    
    # Find top_k results based on hybrid scores
    top_results_values, top_results_indices = torch.topk(hybrid_scores, k=min(top_k, len(paper_df)))
    
    results = []
    # Reset paper_df index to ensure integer-based indexing
    paper_df_reset = paper_df.reset_index(drop=True)
    
    for score, idx in zip(top_results_values, top_results_indices):
        idx_int = int(idx.item())
        results.append({
            "title": paper_df_reset.iloc[idx_int]['title'],
            "score": score.item()
        })
    return results, hybrid_scores  # Return all scores for overall calculation

def calculate_plagiarism_score(hybrid_scores):
    """
    Calculate overall plagiarism percentage like Turnitin.
    
    Algorithm (STRICT VERSION):
    1. Only count papers with similarity > 70% (high threshold)
    2. Apply conservative scoring formula
    3. Discount for common academic overlap
    """
    # Convert to numpy for easier processing
    scores = hybrid_scores.numpy() if isinstance(hybrid_scores, torch.Tensor) else hybrid_scores
    
    # STRICT THRESHOLD - Only very similar papers count
    SUSPICIOUS_THRESHOLD = 0.70  # Raised from 0.50 to 0.70!
    
    # Get all suspicious matches
    suspicious_matches = scores[scores >= SUSPICIOUS_THRESHOLD]
    
    if len(suspicious_matches) == 0:
        # If no matches above 70%, check if there are any above 60%
        moderate_matches = scores[(scores >= 0.60) & (scores < 0.70)]
        if len(moderate_matches) > 0:
            # Low plagiarism score for moderate matches
            highest = float(moderate_matches.max())
            # Adjust the highest match score too (×0.3 discount)
            adjusted_highest_moderate = highest * 0.3
            return {
                'overall_percentage': adjusted_highest_moderate * 100,  # Already discounted
                'risk_level': '🟢 Low Risk',
                'num_matches': len(moderate_matches),
                'highest_match': adjusted_highest_moderate * 100,  # Show adjusted, not raw
                'interpretation': 'Low similarity. Paper appears mostly original with minor overlaps.'
            }
        else:
            return {
                'overall_percentage': 0.0,
                'risk_level': '✅ Original',
                'num_matches': 0,
                'highest_match': 0.0,
                'interpretation': 'Original work - no significant matches found'
            }
    
    # Sort matches in descending order
    sorted_matches = sorted(suspicious_matches, reverse=True)
    
    # Take top 5 matches (or fewer if less available)
    top_matches = sorted_matches[:5]
    
    # CONSERVATIVE SCORING FORMULA
    # Apply academic discount - subtract baseline academic overlap
    ACADEMIC_BASELINE = 0.35  # Common academic language baseline
    
    # Adjust scores by removing baseline
    adjusted_matches = [(s - ACADEMIC_BASELINE) / (1.0 - ACADEMIC_BASELINE) for s in top_matches]
    adjusted_matches = [max(0, s) for s in adjusted_matches]  # Ensure non-negative
    
    highest_match = top_matches[0]
    adjusted_highest = adjusted_matches[0]
    
    if len(adjusted_matches) > 1:
        avg_other_matches = sum(adjusted_matches[1:]) / len(adjusted_matches[1:])
        # Even more conservative: 60% highest, 40% average (was 70/30)
        overall_plag = (0.6 * adjusted_highest + 0.4 * avg_other_matches)
    else:
        overall_plag = adjusted_highest
    
    # Convert to percentage (0-100)
    overall_percentage = float(overall_plag * 100)
    
    # More strict thresholds
    if overall_percentage >= 70:
        risk_level = '🔴 Critical'
        interpretation = 'Severe plagiarism detected! This paper has extensive overlap with existing work.'
    elif overall_percentage >= 50:
        risk_level = '🟠 High Risk'
        interpretation = 'High plagiarism risk. Significant portions match existing papers.'
    elif overall_percentage >= 30:
        risk_level = '🟡 Moderate Risk'
        interpretation = 'Moderate similarity detected. Some content overlaps with existing work.'
    elif overall_percentage >= 15:
        risk_level = '🟢 Low Risk'
        interpretation = 'Low similarity. Paper appears mostly original with minor overlaps.'
    else:
        risk_level = '✅ Original'
        interpretation = 'Minimal similarity. Paper appears to be original work.'
    
    return {
        'overall_percentage': overall_percentage,
        'risk_level': risk_level,
        'num_matches': len(suspicious_matches),
        'highest_match': float(adjusted_highest * 100),  # Show ADJUSTED highest match, not raw!
        'interpretation': interpretation,
        'top_5_scores': [float(s * 100) for s in top_matches]
    }

def find_researchers(query, text_model, gnn_model, nodes_df, rels_df, node_mappings, data, top_k=3):
    """Finds researchers based on a topic query."""
    # This function demonstrates the full pipeline:
    # 1. Embed the query.
    # 2. Find similar papers using the text model.
    # 3. Use the GNN to refine embeddings (conceptual step, simplified here).
    # 4. Find authors of the most relevant papers.
    
    # For this prototype, we'll find authors of the most textually similar papers.
    similar_papers, _ = find_similar_papers(query, text_model, nodes_df, gnn_model, data, top_k=5)
    
    author_list = []
    paper_df = nodes_df[nodes_df['label'] == 'Paper']
    author_df = nodes_df[nodes_df['label'] == 'Author']

    for paper in similar_papers:
        # Find the nodeId for the paper title with error handling
        paper_match = paper_df[paper_df['title'] == paper['title']]
        if paper_match.empty:
            continue
        paper_node_id = paper_match['nodeId'].iloc[0]
        
        # Find author relationships for this paper
        author_ids = rels_df[rels_df['target'] == paper_node_id]['source'].tolist()
        
        for author_id in author_ids:
            author_match = author_df[author_df['nodeId'] == author_id]
            if author_match.empty:
                continue
            author_name = author_match['title'].iloc[0]
            if author_name not in [a['name'] for a in author_list]:
                 author_list.append({"name": author_name})
    
    return author_list[:top_k]


# --- Streamlit UI ---

st.set_page_config(page_title="Aura", layout="centered")
st.title("Aura: Academic Research Assistant")

# Load all models and data
try:
    gnn_model, text_model, nodes_df, rels_df, node_mappings, data = load_models_and_data()
except FileNotFoundError as e:
    st.error(f"Could not find necessary files: {e}")
    st.error("Make sure 'nodes.csv' and 'relationships.csv' are in the same directory as this script.")
    st.stop()
except Exception as e:
    st.error(f"Error loading models and data: {e}")
    st.stop()

# Create tabs for the two modules
tab1, tab2 = st.tabs(["Semantic Plagiarism Detector", "Research Discovery Engine"])

with tab1:
    st.header("Check a New Paper for Similarity")
    
    # Add threshold slider for ADJUSTED scores
    threshold = st.slider(
        "Display Threshold (adjusted similarity score)",
        min_value=0.0,
        max_value=1.0,
        value=0.30,
        step=0.05,
        help="Shows papers above this ADJUSTED score (after strict scoring). Recommended: 0.30 for plagiarism detection. Note: Raw 60% scores become ~18% after adjustment."
    )
    
    uploaded_file = st.file_uploader("Upload a research paper (PDF)", type="pdf")

    if uploaded_file is not None:
        with st.spinner("Analyzing paper for plagiarism..."):
            new_paper_text = extract_text_from_pdf(uploaded_file)
            if new_paper_text:
                # Use GNN-enhanced similarity for better accuracy
                similar_papers, all_scores = find_similar_papers(
                    new_paper_text, 
                    text_model, 
                    nodes_df,
                    gnn_model,
                    data,
                    top_k=20
                )
                
                # Calculate overall plagiarism score (Turnitin-style)
                plag_report = calculate_plagiarism_score(all_scores)
                
                st.success("✅ Analysis Complete!")
                
                # === OVERALL PLAGIARISM SCORE (like Turnitin) ===
                st.markdown("---")
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.metric(
                        label="📊 Overall Plagiarism Score",
                        value=f"{plag_report['overall_percentage']:.1f}%",
                        delta=None
                    )
                    st.write(f"**Risk Level:** {plag_report['risk_level']}")
                    st.write(f"*{plag_report['interpretation']}*")
                
                with col2:
                    st.metric(
                        label="🔍 Matches Found",
                        value=plag_report['num_matches']
                    )
                
                with col3:
                    st.metric(
                        label="📈 Highest Match",
                        value=f"{plag_report['highest_match']:.1f}%"
                    )
                
                # Visual progress bar for overall score (clamped to avoid edge cases)
                st.markdown("### Plagiarism Level")
                st.progress(min(plag_report['overall_percentage'] / 100, 0.9999))
                
                st.markdown("---")
                
                # Show interpretation guide
                with st.expander("📖 How to Interpret Your Score"):
                    st.markdown(f"""
                    **Plagiarism Score Ranges (STRICT MODE):**
                    - **0-15%**: ✅ **Original Work** - Minimal similarity, acceptable for publication
                    - **15-30%**: 🟢 **Low Risk** - Some common phrases/citations, generally acceptable
                    - **30-50%**: 🟡 **Moderate Risk** - Significant overlap, needs review and revision
                    - **50-70%**: 🟠 **High Risk** - Extensive similarities, major revision required
                    - **70-100%**: 🔴 **Critical** - Severe plagiarism, likely unpublishable
                    
                    **Note:** This score represents semantic similarity across your entire paper compared to our database of **{len(nodes_df[nodes_df['label'] == 'Paper'])} papers**.
                    
                    **Strict Scoring Algorithm:**
                    - Only papers with >70% similarity are counted as matches
                    - Papers with 60-70% similarity contribute minimally (heavily discounted)
                    - Papers below 60% are ignored completely
                    - Academic baseline of 35% is subtracted (common academic language)
                    - Highest match: 60% weight, Average of next 4: 40% weight
                    
                    **Why strict scoring?**
                    Embedding-based similarity can be sensitive. This strict mode reduces false positives from:
                    - Common academic terminology
                    - Standard methodologies
                    - Normal literature review overlap
                    - Field-specific jargon
                    """)
                
                # Apply strict scoring to individual papers for display
                # Same logic as overall score: subtract baseline, filter by threshold
                DISPLAY_THRESHOLD = 0.70  # Only show truly similar papers
                ACADEMIC_BASELINE = 0.35
                
                # Adjust all scores
                adjusted_papers = []
                for paper in similar_papers:
                    raw_score = paper['score']
                    
                    # Apply same strict adjustment as overall score
                    if raw_score >= DISPLAY_THRESHOLD:
                        # High similarity - adjust by removing baseline
                        adjusted_score = (raw_score - ACADEMIC_BASELINE) / (1.0 - ACADEMIC_BASELINE)
                        adjusted_score = max(0.0, min(1.0, adjusted_score))  # Clamp to [0, 1]
                        
                        adjusted_papers.append({
                            'title': paper['title'],
                            'raw_score': raw_score,
                            'adjusted_score': adjusted_score,
                            'is_significant': True
                        })
                    elif raw_score >= 0.60:
                        # Moderate similarity - heavily discount
                        adjusted_score = raw_score * 0.3
                        adjusted_papers.append({
                            'title': paper['title'],
                            'raw_score': raw_score,
                            'adjusted_score': adjusted_score,
                            'is_significant': False
                        })
                
                # Filter by user's threshold slider (applied to adjusted scores)
                filtered_papers = [p for p in adjusted_papers if p['adjusted_score'] >= threshold]
                
                if filtered_papers:
                    st.markdown("---")
                    st.subheader(f"🔎 Significant Matches Found:")
                    st.caption(f"Showing {len(filtered_papers)} papers with adjusted similarity ≥ {threshold:.0%}")
                    
                    for i, paper in enumerate(filtered_papers, 1):
                        adj_score = paper['adjusted_score']
                        raw_score = paper['raw_score']
                        
                        # Color code based on ADJUSTED similarity (strict scoring)
                        if adj_score >= 0.70:
                            color = "🔴"
                            risk = "Critical - Very High Similarity"
                        elif adj_score >= 0.50:
                            color = "🟠"
                            risk = "High Similarity"
                        elif adj_score >= 0.30:
                            color = "🟡"
                            risk = "Moderate Similarity"
                        else:
                            color = "🟢"
                            risk = "Low Similarity"
                        
                        with st.expander(f"#{i} {color} {paper['title']} - {adj_score:.1%}"):
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.write(f"**Adjusted Score:** {adj_score:.1%}")
                                st.write(f"**Raw Similarity:** {raw_score:.1%}")
                                st.write(f"**Assessment:** {risk}")
                            with col_b:
                                st.write(f"**Contribution to Overall Score:**")
                                if i == 1:
                                    st.write(f"⭐ Primary match (60% weight)")
                                elif i <= 5:
                                    st.write(f"📊 Top 5 match (40% weight)")
                                else:
                                    st.write(f"📋 Additional match")
                            
                            # Show what adjustment was applied
                            if paper['is_significant']:
                                st.info(f"ℹ️ High match (≥70%) - adjusted by removing 35% academic baseline")
                            else:
                                st.info(f"ℹ️ Moderate match (60-70%) - heavily discounted (×0.3)")
                            
                            # Progress bar visualization (use adjusted score, clamped to valid range)
                            st.progress(min(adj_score, 0.9999))
                else:
                    st.success(f"✅ No significant matches found above {threshold:.0%} threshold after strict scoring.")
                    st.info("💡 This means your paper is highly original! Some moderate similarities (60-70%) may exist but were filtered out by strict scoring.")
                
                # === DETAILED SENTENCE-LEVEL REPORT (NEW!) ===
                st.markdown("---")
                st.markdown("## 📋 Detailed Plagiarism Report")
                
                # Add button to generate detailed report
                if st.button("🔍 Generate Sentence-Level Analysis", help="Analyzes each sentence for plagiarism - may take 20-30 seconds"):
                    with st.spinner("Analyzing sentences... This may take a moment."):
                        # Split user paper into sentences
                        user_sentences = split_into_sentences(new_paper_text)
                        
                        if len(user_sentences) == 0:
                            st.warning("Could not extract sentences from your paper. Please ensure the PDF has selectable text.")
                        else:
                            # Analyze sentence similarity
                            sentence_matches = analyze_sentence_similarity(
                                user_sentences,
                                text_model,
                                nodes_df,
                                similar_papers,
                                threshold=0.75  # Sentence-level threshold
                            )
                            
                            # Generate report statistics
                            report_stats = generate_detailed_report(sentence_matches, user_sentences)
                            
                            # Display summary statistics
                            st.markdown("### 📊 Report Summary")
                            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
                            
                            with col_r1:
                                st.metric("Total Sentences", report_stats['total_sentences'])
                            with col_r2:
                                flagged_pct = report_stats['flagged_percentage']
                                st.metric(
                                    "Flagged Sentences",
                                    report_stats['flagged_sentences'],
                                    f"{flagged_pct:.1f}%"
                                )
                            with col_r3:
                                st.metric("Unique Sources", report_stats['unique_sources'])
                            with col_r4:
                                total_issues = (
                                    report_stats['exact_matches'] +
                                    report_stats['high_matches'] +
                                    report_stats['moderate_matches']
                                )
                                st.metric("Total Matches", total_issues)
                            
                            # Severity breakdown
                            st.markdown("### 🎯 Severity Breakdown")
                            col_s1, col_s2, col_s3 = st.columns(3)
                            with col_s1:
                                st.metric("🔴 Exact Matches (≥95%)", report_stats['exact_matches'])
                            with col_s2:
                                st.metric("🟠 High Similarity (≥85%)", report_stats['high_matches'])
                            with col_s3:
                                st.metric("🟡 Moderate (≥75%)", report_stats['moderate_matches'])
                            
                            # Source distribution
                            if report_stats['unique_sources'] > 0:
                                with st.expander("📚 Source Distribution"):
                                    st.write("**Papers contributing to flagged sentences:**")
                                    for i, source in enumerate(report_stats['sources_list'], 1):
                                        source_count = sum(
                                            1 for m in sentence_matches if m['source_paper'] == source
                                        )
                                        st.write(f"{i}. {source} ({source_count} matches)")
                            
                            st.markdown("---")
                            
                            # Display sentence-level matches
                            display_sentence_matches(sentence_matches, user_sentences)
                            
                            # Export option
                            st.markdown("---")
                            if sentence_matches:
                                if st.button("📥 Download Text Report"):
                                    # Generate text report
                                    report_text = f"""
DETAILED PLAGIARISM REPORT
Generated by AURA - Academic Research Assistant
==============================================

SUMMARY STATISTICS:
- Total Sentences: {report_stats['total_sentences']}
- Flagged Sentences: {report_stats['flagged_sentences']} ({report_stats['flagged_percentage']:.1f}%)
- Unique Sources: {report_stats['unique_sources']}
- Exact Matches: {report_stats['exact_matches']}
- High Similarity: {report_stats['high_matches']}
- Moderate Similarity: {report_stats['moderate_matches']}

OVERALL PLAGIARISM SCORE: {plag_report['overall_percentage']:.1f}%
Risk Level: {plag_report['risk_level']}

==============================================
FLAGGED SENTENCES:
==============================================

"""
                                    for i, (sent_id, matches) in enumerate(
                                        sorted(
                                            {m['sentence_id']: m for m in sentence_matches}.items(),
                                            key=lambda x: x[0]
                                        ),
                                        1
                                    ):
                                        match = matches
                                        report_text += f"\n{i}. SENTENCE #{match['sentence_id'] + 1} ({match['similarity']:.1%} match)\n"
                                        report_text += f"   Your text: \"{match['user_sentence']}\"\n"
                                        report_text += f"   Source: {match['source_paper']}\n"
                                        report_text += f"   Matched text: \"{match['source_sentence']}\"\n"
                                        report_text += f"   {'='*80}\n"
                                    
                                    st.download_button(
                                        label="Download Report as TXT",
                                        data=report_text,
                                        file_name="plagiarism_report.txt",
                                        mime="text/plain"
                                    )

with tab2:
    st.header("Find Researchers by Topic")
    query = st.text_input("Enter a research topic", placeholder="e.g., machine learning in agriculture")

    if st.button("Search Researchers"):
        if query:
            with st.spinner(f"Finding researchers for '{query}'..."):
                researchers = find_researchers(query, text_model, gnn_model, nodes_df, rels_df, node_mappings, data)
                st.success("Search Complete!")
                st.subheader("Top Researchers Found:")
                if researchers:
                    for researcher in researchers:
                        st.info(f"**{researcher['name']}**")
                else:
                    st.warning("No researchers found for this specific topic.")
        else:
            st.warning("Please enter a research topic.")
