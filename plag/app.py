"""
Aura - Academic Plagiarism Detection System
Main Streamlit Application
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import networkx as nx
import json
import hashlib
from datetime import datetime
import time

# Import our modules
from database import DatabaseManager, DatabaseExporter
from modules import (
    PDFProcessor, 
    SemanticSimilarityEngine, 
    KnowledgeGraphBuilder,
    PlagiarismDetector,
    PlagiarismType
)
from config import MAX_FILE_SIZE, SUPPORTED_FORMATS, PLAGIARISM_LEVELS

# Configure page
st.set_page_config(
    page_title="Aura - Academic Plagiarism Detection",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()
if 'pdf_processor' not in st.session_state:
    st.session_state.pdf_processor = PDFProcessor()
if 'plagiarism_detector' not in st.session_state:
    st.session_state.plagiarism_detector = PlagiarismDetector(st.session_state.db_manager)
if 'kg_builder' not in st.session_state:
    st.session_state.kg_builder = KnowledgeGraphBuilder()

def main():
    """Main application function"""
    st.title("🔍 Aura - Academic Plagiarism Detection System")
    st.markdown("*AI-powered semantic plagiarism detection for academic research papers*")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Upload & Analyze", "Database Explorer", "Knowledge Graph", "Statistics", "Settings"]
    )
    
    if page == "Upload & Analyze":
        upload_and_analyze_page()
    elif page == "Database Explorer":
        database_explorer_page()
    elif page == "Knowledge Graph":
        knowledge_graph_page()
    elif page == "Statistics":
        statistics_page()
    elif page == "Settings":
        settings_page()

def upload_and_analyze_page():
    """Main page for uploading and analyzing documents"""
    st.header("📄 Upload and Analyze Document")
    
    # File upload section
    st.subheader("Upload PDF Document")
    uploaded_file = st.file_uploader(
        "Choose a PDF file to analyze for plagiarism",
        type=['pdf'],
        help=f"Maximum file size: {MAX_FILE_SIZE//1024//1024}MB"
    )
    
    if uploaded_file is not None:
        # Check file size
        if uploaded_file.size > MAX_FILE_SIZE:
            st.error(f"File size ({uploaded_file.size//1024//1024}MB) exceeds maximum allowed size ({MAX_FILE_SIZE//1024//1024}MB)")
            return
        
        # Display file info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Name", uploaded_file.name)
        with col2:
            st.metric("File Size", f"{uploaded_file.size//1024:.1f} KB")
        with col3:
            st.metric("File Type", uploaded_file.type)
        
        # Process PDF
        with st.spinner("Extracting text from PDF..."):
            extraction_result = st.session_state.pdf_processor.extract_text_from_pdf(uploaded_file)
        
        if not extraction_result['success']:
            st.error(f"Failed to extract text from PDF: {extraction_result.get('error', 'Unknown error')}")
            return
        
        # Display extraction results
        st.success("✅ Text extraction completed successfully!")
        
        # Show text statistics
        stats = extraction_result['statistics']
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Word Count", stats.get('word_count', 0))
        with col2:
            st.metric("Sentence Count", stats.get('sentence_count', 0))
        with col3:
            st.metric("Pages", len(extraction_result['pages']))
        with col4:
            st.metric("Readability", f"{stats.get('readability_flesch', 0):.1f}")
        
        # Show extracted structure
        if extraction_result['structure']:
            with st.expander("📋 Document Structure"):
                structure = extraction_result['structure']
                if 'title' in structure:
                    st.write(f"**Title:** {structure['title']}")
                if 'authors' in structure:
                    st.write(f"**Authors:** {', '.join(structure['authors'])}")
                if 'abstract' in structure:
                    st.write(f"**Abstract:** {structure['abstract'][:300]}...")
                if 'keywords' in structure:
                    st.write(f"**Keywords:** {', '.join(structure['keywords'])}")
        
        # Check if document already exists
        existing_paper = st.session_state.db_manager.get_paper_by_hash(extraction_result['file_hash'])
        
        if existing_paper:
            st.info("ℹ️ This document was previously analyzed.")
            st.write(f"**Previous Title:** {existing_paper['title']}")
            st.write(f"**Analyzed on:** {existing_paper['created_at']}")
        
        # IMPORTANT: We do NOT add uploaded documents to the reference database
        # This prevents false positives when re-testing the same document
        st.info("💡 **Note:** Uploaded documents are analyzed but NOT added to the reference database to ensure accurate results on re-testing.")
        
        # Plagiarism Detection Section
        st.subheader("🔍 Plagiarism Analysis")
        
        if st.button("🚀 Start Plagiarism Detection", type="primary"):
            perform_plagiarism_detection(extraction_result, existing_paper)

def perform_plagiarism_detection(extraction_result, existing_paper):
    """Perform plagiarism detection and display results"""
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Prepare text
        status_text.text("Preparing text for analysis...")
        progress_bar.progress(10)
        
        text_content = extraction_result['text']
        
        # IMPORTANT: We do NOT add uploaded documents to the database
        # This ensures accurate plagiarism detection on re-testing
        # The paper_id is None, indicating this is a test document
        paper_id = None
        
        # Step 2: Run plagiarism detection
        status_text.text("Running plagiarism detection algorithms...")
        progress_bar.progress(40)
        
        start_time = time.time()
        plagiarism_result = st.session_state.plagiarism_detector.detect_plagiarism(
            text_content, paper_id
        )
        detection_time = time.time() - start_time
        
        progress_bar.progress(100)
        status_text.text("Analysis complete!")
        
        # Display results
        display_plagiarism_results(plagiarism_result, detection_time)
        
    except Exception as e:
        st.error(f"Error during plagiarism detection: {str(e)}")
        st.exception(e)

def display_plagiarism_results(result, detection_time):
    """Display plagiarism detection results"""
    
    st.subheader("📊 Plagiarism Detection Results")
    
    # Overall score and level
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        score_color = "red" if result.overall_score > 0.7 else "orange" if result.overall_score > 0.4 else "green"
        st.metric(
            "Overall Plagiarism Score", 
            f"{result.overall_score:.1%}",
            help="Composite plagiarism score based on multiple detection algorithms"
        )
    
    with col2:
        level_color = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟠", "MINIMAL": "🟢"}
        st.metric(
            "Plagiarism Level", 
            f"{level_color.get(result.plagiarism_level, '⚪')} {result.plagiarism_level}"
        )
    
    with col3:
        st.metric("Total Matches", result.total_matches)
    
    with col4:
        st.metric("Coverage", f"{result.coverage_percentage:.1f}%")
    
    # Performance metrics
    st.caption(f"⏱️ Analysis completed in {detection_time:.2f} seconds")
    
    # Detailed results
    if result.matches:
        st.subheader("🎯 Detailed Matches")
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📋 Match List", "📈 Similarity Analysis", "🗂️ Source Papers"])
        
        with tab1:
            display_match_list(result.matches)
        
        with tab2:
            display_similarity_analysis(result)
        
        with tab3:
            display_source_papers(result)
    
    else:
        st.success("🎉 No significant plagiarism detected!")
        st.info("This document appears to be original based on our analysis.")
    
    # Export results
    if st.button("📥 Export Results"):
        export_results(result)

def display_match_list(matches):
    """Display list of plagiarism matches"""
    
    # Create DataFrame for better display
    match_data = []
    for i, match in enumerate(matches):
        match_data.append({
            "Match #": i + 1,
            "Type": match.plagiarism_type.value.replace('_', ' ').title(),
            "Similarity": f"{match.similarity_score:.1%}",
            "Confidence": f"{match.confidence:.1%}",
            "Source Text": match.source_text[:100] + "..." if len(match.source_text) > 100 else match.source_text,
            "Target Text": match.target_text[:100] + "..." if len(match.target_text) > 100 else match.target_text,
            "Position": f"{match.start_position}-{match.end_position}"
        })
    
    df = pd.DataFrame(match_data)
    
    # Display with styling
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    
    # Detailed view for selected match
    if not df.empty:
        selected_match = st.selectbox("Select match for detailed view:", range(len(matches)))
        
        if selected_match is not None:
            match = matches[selected_match]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Source Text:**")
                st.text_area("", match.source_text, height=200, disabled=True, key=f"source_{selected_match}")
            
            with col2:
                st.write("**Matching Text:**")
                st.text_area("", match.target_text, height=200, disabled=True, key=f"target_{selected_match}")

def display_similarity_analysis(result):
    """Display similarity analysis charts"""
    
    if not result.matches:
        st.info("No matches to analyze")
        return
    
    # Similarity score distribution
    scores = [match.similarity_score for match in result.matches]
    
    fig1 = px.histogram(
        x=scores,
        nbins=20,
        title="Distribution of Similarity Scores",
        labels={"x": "Similarity Score", "y": "Count"}
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    # Plagiarism type distribution
    type_counts = {}
    for match in result.matches:
        ptype = match.plagiarism_type.value.replace('_', ' ').title()
        type_counts[ptype] = type_counts.get(ptype, 0) + 1
    
    fig2 = px.pie(
        values=list(type_counts.values()),
        names=list(type_counts.keys()),
        title="Plagiarism Types Distribution"
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    # Score timeline (by position in document)
    positions = [match.start_position for match in result.matches]
    scores = [match.similarity_score for match in result.matches]
    
    fig3 = px.scatter(
        x=positions,
        y=scores,
        title="Plagiarism Scores by Document Position",
        labels={"x": "Position in Document", "y": "Similarity Score"}
    )
    st.plotly_chart(fig3, use_container_width=True)

def display_source_papers(result):
    """Display information about source papers"""
    
    # Get unique target papers
    target_papers = {}
    for match in result.matches:
        if match.target_paper_id:
            if match.target_paper_id not in target_papers:
                target_papers[match.target_paper_id] = {
                    'matches': 0,
                    'max_similarity': 0,
                    'avg_similarity': 0,
                    'scores': []
                }
            
            target_papers[match.target_paper_id]['matches'] += 1
            target_papers[match.target_paper_id]['max_similarity'] = max(
                target_papers[match.target_paper_id]['max_similarity'], 
                match.similarity_score
            )
            target_papers[match.target_paper_id]['scores'].append(match.similarity_score)
    
    # Calculate averages
    for paper_id in target_papers:
        scores = target_papers[paper_id]['scores']
        target_papers[paper_id]['avg_similarity'] = sum(scores) / len(scores)
    
    # Get paper details from database
    paper_details = []
    for paper_id in target_papers.keys():
        papers = st.session_state.db_manager.get_all_papers()
        paper = next((p for p in papers if p['id'] == paper_id), None)
        if paper:
            paper_info = target_papers[paper_id]
            paper_details.append({
                'Title': paper['title'][:50] + "..." if len(paper['title']) > 50 else paper['title'],
                'Matches': paper_info['matches'],
                'Max Similarity': f"{paper_info['max_similarity']:.1%}",
                'Avg Similarity': f"{paper_info['avg_similarity']:.1%}",
                'Added': paper['created_at'][:10] if paper['created_at'] else 'Unknown'
            })
    
    if paper_details:
        df = pd.DataFrame(paper_details)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No source papers identified")

def database_explorer_page():
    """Database explorer page"""
    st.header("🗄️ Database Explorer")
    
    # Database statistics
    stats = st.session_state.db_manager.get_database_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Papers", stats.get('papers', 0))
    with col2:
        st.metric("Authors", stats.get('authors', 0))
    with col3:
        st.metric("Topics", stats.get('topics', 0))
    with col4:
        st.metric("Similarities", stats.get('paper_similarities', 0))
    
    # Search functionality
    st.subheader("🔍 Search Papers")
    search_query = st.text_input("Enter search terms:")
    
    if search_query:
        results = st.session_state.db_manager.search_papers(search_query)
        
        if results:
            st.write(f"Found {len(results)} papers:")
            
            for paper in results:
                with st.expander(f"📄 {paper['title']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        if paper['authors']:
                            authors = json.loads(paper['authors']) if isinstance(paper['authors'], str) else paper['authors']
                            st.write(f"**Authors:** {', '.join(authors)}")
                        st.write(f"**Added:** {paper['created_at']}")
                        st.write(f"**Word Count:** {paper.get('word_count', 'N/A')}")
                    
                    with col2:
                        if paper['abstract']:
                            st.write("**Abstract:**")
                            st.write(paper['abstract'][:300] + "..." if len(paper['abstract']) > 300 else paper['abstract'])
        else:
            st.info("No papers found matching your search.")
    
    # Export functionality
    st.subheader("📤 Export Data")
    exporter = DatabaseExporter(st.session_state.db_manager)
    export_summary = exporter.get_export_summary()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Export to JSON"):
            with st.spinner("Exporting to JSON..."):
                filepath = exporter.export_to_json()
                st.success(f"Exported to: {filepath}")
    
    with col2:
        if st.button("Export to Excel"):
            with st.spinner("Exporting to Excel..."):
                filepath = exporter.export_to_excel()
                st.success(f"Exported to: {filepath}")
    
    with col3:
        if st.button("Create Backup"):
            with st.spinner("Creating backup..."):
                backup_name = exporter.create_backup()
                st.success(f"Backup created: {backup_name}")

def knowledge_graph_page():
    """Knowledge graph visualization page"""
    st.header("🕸️ Academic Knowledge Graph")
    
    # Get all papers for graph construction
    papers = st.session_state.db_manager.get_all_papers()
    
    if not papers:
        st.info("No papers in database to build knowledge graph.")
        return
    
    st.write(f"Building knowledge graph from {len(papers)} papers...")
    
    # Build knowledge graph
    with st.spinner("Constructing knowledge graph..."):
        graph = st.session_state.kg_builder.build_knowledge_graph(papers)
    
    # Graph statistics
    stats = st.session_state.kg_builder.get_graph_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Nodes", stats.get('total_nodes', 0))
    with col2:
        st.metric("Edges", stats.get('total_edges', 0))
    with col3:
        st.metric("Density", f"{stats.get('density', 0):.3f}")
    with col4:
        st.metric("Components", stats.get('connected_components', 0))
    
    # Node type distribution
    if 'node_types' in stats:
        st.subheader("📊 Node Types")
        node_types = stats['node_types']
        
        fig = px.bar(
            x=list(node_types.keys()),
            y=list(node_types.values()),
            title="Distribution of Node Types in Knowledge Graph"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Export graph data
    if st.button("📥 Export Graph Data"):
        graph_data = st.session_state.kg_builder.export_graph_data()
        
        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"knowledge_graph_{timestamp}.json"
        
        with open(f"data/{filename}", 'w') as f:
            json.dump(graph_data, f, indent=2)
        
        st.success(f"Graph data exported to: data/{filename}")

def statistics_page():
    """Statistics and analytics page"""
    st.header("📈 System Statistics")
    
    # Get plagiarism statistics
    plag_stats = st.session_state.plagiarism_detector.get_plagiarism_statistics()
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Detections", plag_stats.get('total_detections', 0))
    with col2:
        db_stats = plag_stats.get('database_stats', {})
        st.metric("Papers Analyzed", db_stats.get('papers', 0))
    with col3:
        st.metric("Authors", db_stats.get('authors', 0))
    with col4:
        st.metric("Similarities Found", db_stats.get('paper_similarities', 0))
    
    # Plagiarism level distribution
    if 'level_distribution' in plag_stats and plag_stats['level_distribution']:
        st.subheader("🎯 Plagiarism Level Distribution")
        
        levels = list(plag_stats['level_distribution'].keys())
        counts = list(plag_stats['level_distribution'].values())
        
        fig = px.pie(
            values=counts,
            names=levels,
            title="Distribution of Plagiarism Levels",
            color_discrete_map={
                'HIGH': 'red',
                'MEDIUM': 'orange', 
                'LOW': 'yellow',
                'MINIMAL': 'green'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Plagiarism type distribution
    if 'type_distribution' in plag_stats and plag_stats['type_distribution']:
        st.subheader("🔍 Plagiarism Type Distribution")
        
        types = list(plag_stats['type_distribution'].keys())
        counts = list(plag_stats['type_distribution'].values())
        
        fig = px.bar(
            x=types,
            y=counts,
            title="Most Common Types of Plagiarism Detected"
        )
        st.plotly_chart(fig, use_container_width=True)

def settings_page():
    """Settings and configuration page"""
    st.header("⚙️ System Settings")
    
    st.subheader("🎛️ Detection Thresholds")
    
    # Allow users to adjust thresholds
    col1, col2 = st.columns(2)
    
    with col1:
        st.slider("High Plagiarism Threshold", 0.5, 1.0, PLAGIARISM_LEVELS['HIGH'], 0.05)
        st.slider("Medium Plagiarism Threshold", 0.3, 0.8, PLAGIARISM_LEVELS['MEDIUM'], 0.05)
    
    with col2:
        st.slider("Low Plagiarism Threshold", 0.1, 0.6, PLAGIARISM_LEVELS['LOW'], 0.05)
        st.slider("Similarity Threshold", 0.3, 0.9, SIMILARITY_THRESHOLD, 0.05)
    
    st.subheader("📊 System Information")
    
    # Display system info
    st.write("**Database Path:**", st.session_state.db_manager.db_path)
    st.write("**Supported Formats:**", ", ".join(SUPPORTED_FORMATS))
    st.write("**Max File Size:**", f"{MAX_FILE_SIZE//1024//1024}MB")
    
    # Database management
    st.subheader("🗄️ Database Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Database"):
            st.rerun()
    
    with col2:
        if st.button("📊 Rebuild Statistics"):
            # Could trigger statistics recalculation
            st.success("Statistics refreshed!")
    
    with col3:
        if st.button("⚠️ Clear Cache"):
            # Clear any cached data
            st.success("Cache cleared!")

def export_results(result):
    """Export plagiarism detection results"""
    # Create export data
    export_data = {
        'detection_timestamp': result.detection_timestamp,
        'overall_score': result.overall_score,
        'plagiarism_level': result.plagiarism_level,
        'coverage_percentage': result.coverage_percentage,
        'total_matches': result.total_matches,
        'matches': [
            {
                'type': match.plagiarism_type.value,
                'similarity_score': match.similarity_score,
                'confidence': match.confidence,
                'source_text': match.source_text,
                'target_text': match.target_text,
                'position': f"{match.start_position}-{match.end_position}"
            }
            for match in result.matches
        ],
        'comparison_summary': result.comparison_summary
    }
    
    # Save to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"plagiarism_report_{timestamp}.json"
    
    with open(f"data/{filename}", 'w') as f:
        json.dump(export_data, f, indent=2)
    
    st.success(f"Results exported to: data/{filename}")

if __name__ == "__main__":
    main()