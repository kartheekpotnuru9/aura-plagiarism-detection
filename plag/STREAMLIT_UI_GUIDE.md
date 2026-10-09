# 🔍 Aura Streamlit UI Guide - Complete Navigation

## 📱 Interface Overview

The Aura system has **5 main pages** accessible from the sidebar navigation:

```
Sidebar Navigation:
├── 📄 Upload & Analyze    (Main plagiarism detection)
├── 🗄️ Database Explorer   (Browse and search papers)
├── 🕸️ Knowledge Graph     (Visualize paper relationships)
├── 📈 Statistics          (System analytics)
└── ⚙️ Settings            (Configuration)
```

---

## 1. 📄 Upload & Analyze (Main Page)

**Purpose:** Upload PDFs and detect plagiarism

### Features:

#### A. File Upload Section
- **Upload PDF**: Drag & drop or browse for PDF files
- **File Validation**: 
  - Max file size check (configurable, default ~10MB)
  - PDF format verification
  - File integrity check

#### B. Document Information Display
Shows after successful upload:
- 📄 **File Name**: Original filename
- 📦 **File Size**: In KB/MB
- 📑 **File Type**: MIME type (application/pdf)

#### C. Text Extraction
- Automatic PDF text extraction
- Progress indicator
- Error handling for corrupted/image-only PDFs
- Shows:
  - **Word Count**: Total words extracted
  - **Character Count**: Total characters
  - **Readability Score**: Flesch reading ease

#### D. Document Structure (Expandable)
If detected, shows:
- **Title**: Extracted paper title
- **Authors**: Author names
- **Abstract**: Paper abstract preview
- **Keywords**: Extracted keywords

#### E. Important Notice
```
💡 Note: Uploaded documents are analyzed but NOT added 
to the reference database to ensure accurate results 
on re-testing.
```

#### F. Plagiarism Detection
- **Start Button**: Triggers analysis
- **Progress Bar**: Shows analysis progress (0-100%)
- **Status Messages**:
  - "Preparing text for analysis..."
  - "Running plagiarism detection algorithms..."
  - "🔍 Comparing against X papers from database..."
  - "Analyzed X/Y papers..."
  - "Analysis complete!"

#### G. Results Display
After analysis completes, shows:

**Overall Metrics:**
- 🎯 **Overall Plagiarism Score**: 0-100% (color-coded)
- 📊 **Plagiarism Level**: MINIMAL/LOW/MEDIUM/HIGH
- 📈 **Coverage Percentage**: How much of document matched
- ⏱️ **Detection Time**: Seconds taken for analysis

**Detailed Results:**
- **Match Count by Type**: 
  - Direct Copy matches
  - Paraphrased matches
  - Structural matches
  - Mosaic plagiarism
  - Idea plagiarism

**Top Matches Section:**
For each significant match:
- 📄 Source paper title
- 📊 Similarity percentage
- 🏷️ Plagiarism type
- 📝 Matched text snippet (first 100 chars)

**Visual Charts:**
- Plagiarism type distribution (pie chart)
- Similarity scores over threshold (bar chart)
- Match locations in document (heatmap)

#### H. Export Options
- 📥 **Download JSON**: Complete results in JSON format
- 📄 **Download PDF Report**: Formatted PDF report
- 📊 **Download CSV**: Matches in spreadsheet format

---

## 2. 🗄️ Database Explorer

**Purpose:** Browse, search, and manage reference papers

### Features:

#### A. Database Statistics Dashboard
Quick overview with 4 metrics:
- 📄 **Papers**: Total papers in database
- 👥 **Authors**: Total unique authors
- 🏷️ **Topics**: Total topics/keywords
- 🔗 **Similarities**: Total similarity relationships

#### B. Search Functionality
- **Search Box**: Enter keywords to search
- **Search Scope**: Searches in:
  - Paper titles
  - Abstracts
  - Full content
  - Author names
  - Keywords

#### C. Search Results
For each matching paper:
- **Expandable Card** showing:
  - 📄 **Title**: Full paper title
  - 👥 **Authors**: Comma-separated list
  - 📅 **Added Date**: When added to database
  - 📊 **Word Count**: Document length
  - 📝 **Abstract**: Preview (first 300 chars)

#### D. Export Data Section
Three export options:

**Export to JSON:**
```json
{
  "papers": [...],
  "authors": [...],
  "topics": [...],
  "timestamp": "2025-10-15T10:30:00"
}
```

**Export to CSV:**
- papers.csv (titles, authors, abstracts)
- authors.csv (names, research areas)
- topics.csv (keywords, categories)

**Export to Excel:**
- Multi-sheet workbook
- Formatted tables
- Statistics summary sheet

#### E. Database Info
Shows:
- Total size on disk
- Last updated timestamp
- Backup status

---

## 3. 🕸️ Knowledge Graph

**Purpose:** Visualize relationships between papers

### Features:

#### A. Graph Construction
- Automatically builds graph from database papers
- Progress indicator during construction
- Shows paper count being processed

#### B. Graph Statistics
Four key metrics:
- 🔵 **Nodes**: Total entities (papers, authors, topics)
- 🔗 **Edges**: Total connections/relationships
- 📊 **Density**: Graph connectivity (0-1)
- 🧩 **Components**: Number of disconnected clusters

#### C. Node Type Distribution
**Bar Chart** showing:
- Paper nodes
- Author nodes  
- Topic nodes
- Keyword nodes

Color-coded by type

#### D. Graph Visualization
Interactive network graph showing:
- **Nodes**:
  - Papers (blue circles)
  - Authors (green circles)
  - Topics (orange circles)
- **Edges**:
  - Citation links
  - Co-authorship
  - Topic similarity
  - Semantic similarity

**Interactive Features:**
- Zoom in/out
- Pan around
- Click nodes for details
- Hover for tooltips

#### E. Export Graph Data
Downloads knowledge graph as:
- **JSON format**: For analysis tools
- **GraphML format**: For Gephi/Cytoscape
- **Adjacency Matrix**: For mathematical analysis

**Example JSON:**
```json
{
  "nodes": [
    {"id": "paper_1", "type": "paper", "title": "..."},
    {"id": "author_1", "type": "author", "name": "..."}
  ],
  "edges": [
    {"source": "paper_1", "target": "author_1", "type": "authorship"}
  ]
}
```

---

## 4. 📈 Statistics

**Purpose:** System analytics and insights

### Features:

#### A. Overview Metrics
Four dashboard cards:
- 🔍 **Total Detections**: Plagiarism checks run
- 📄 **Papers Analyzed**: Unique documents checked
- 👥 **Authors**: Database author count
- 🔗 **Similarities Found**: Total matches detected

#### B. Plagiarism Level Distribution
**Pie Chart** showing:
- 🔴 HIGH: Severe plagiarism (>70%)
- 🟠 MEDIUM: Moderate plagiarism (40-70%)
- 🟡 LOW: Minor plagiarism (15-40%)
- 🟢 MINIMAL: Very low plagiarism (<15%)

**Color-coded segments** with percentages

#### C. Plagiarism Type Distribution
**Bar Chart** showing frequency of:
- Direct Copy detection
- Paraphrased content
- Structural plagiarism
- Mosaic plagiarism
- Idea plagiarism

Sorted from most to least common

#### D. Trend Analysis (If Available)
**Line Chart** showing:
- Detections over time
- Average plagiarism scores by month
- Type frequency trends

#### E. System Performance
Shows:
- Average detection time
- Papers processed per day
- Database growth rate

---

## 5. ⚙️ Settings

**Purpose:** Configure system parameters

### Features:

#### A. Detection Thresholds
**Interactive Sliders** to adjust:

**High Plagiarism Threshold** (0.5 - 1.0)
- Default: 0.7 (70%)
- Scores above this = HIGH risk

**Medium Plagiarism Threshold** (0.3 - 0.8)
- Default: 0.4 (40%)
- Scores in range = MEDIUM risk

**Low Plagiarism Threshold** (0.1 - 0.6)
- Default: 0.15 (15%)
- Scores in range = LOW risk

**Similarity Threshold** (0.3 - 0.9)
- Default: 0.5 (50%)
- Minimum to consider as match

#### B. System Information
Read-only display:
- 📁 **Database Path**: Location of SQLite database
- 📄 **Supported Formats**: PDF, TXT (configurable)
- 📦 **Max File Size**: Upload limit in MB
- 🐍 **Python Version**: Runtime version
- 🔧 **Dependencies**: Installed packages

#### C. Database Management
Three action buttons:

**🔄 Refresh Database:**
- Reloads database connection
- Clears any stale data
- Re-indexes papers

**📊 Rebuild Statistics:**
- Recalculates all stats
- Updates cached metrics
- Useful after bulk changes

**⚠️ Clear Cache:**
- Clears embeddings cache
- Frees up memory
- Forces fresh calculations

#### D. Advanced Options (If Available)
- Model selection (different embedding models)
- Chunk size configuration
- Parallel processing settings
- Logging level

---

## 🎨 UI Design Features

### Color Coding
- 🟢 **Green**: Success, low plagiarism, safe
- 🟡 **Yellow**: Warning, medium plagiarism, caution
- 🟠 **Orange**: High concern, review needed
- 🔴 **Red**: Critical, high plagiarism, action required
- 🔵 **Blue**: Information, neutral

### Icons
- 📄 Papers/Documents
- 👥 Authors/People
- 🏷️ Topics/Keywords
- 🔍 Search/Detection
- 📊 Statistics/Charts
- ⚙️ Settings/Config
- 🕸️ Network/Graph
- 💾 Save/Export
- ⬆️ Upload
- ⬇️ Download

### Interactive Elements
- **Expandable Sections**: Click to show/hide details
- **Tooltips**: Hover for explanations
- **Progress Bars**: Visual feedback during processing
- **Buttons**: Clear call-to-action
- **Sliders**: Adjust thresholds in real-time

---

## 🚀 Typical User Workflow

### 1. First Time Setup
```
Settings → Check thresholds → Database Explorer → Verify papers
```

### 2. Analyze Document
```
Upload & Analyze → Choose PDF → Upload → Start Detection → Review Results → Export
```

### 3. Browse Database
```
Database Explorer → Search keywords → View papers → Export data
```

### 4. Visualize Relationships
```
Knowledge Graph → Build graph → Explore connections → Export
```

### 5. Review Statistics
```
Statistics → View trends → Analyze patterns → Make decisions
```

---

## 💡 Pro Tips

### For Best Results:
1. **Upload & Analyze**: Clear, high-quality PDFs work best
2. **Database Explorer**: Use specific keywords for better search results
3. **Knowledge Graph**: More papers = richer graph visualization
4. **Statistics**: Run multiple detections to see meaningful trends
5. **Settings**: Start with defaults, adjust based on your needs

### Performance Tips:
- Smaller PDFs analyze faster (<5MB ideal)
- Database with 50-200 papers is optimal
- Clear cache if system feels slow
- Export data regularly for backup

### Accuracy Tips:
- Keep database focused on relevant domain
- Don't add test documents to database
- Adjust thresholds based on your standards
- Review matches manually for context

---

## 🎯 Quick Reference

| Need to... | Go to... |
|------------|----------|
| Check a paper for plagiarism | Upload & Analyze |
| Find a specific paper | Database Explorer |
| See how papers relate | Knowledge Graph |
| View detection history | Statistics |
| Adjust sensitivity | Settings |
| Export results | Upload & Analyze (after detection) |
| Search database | Database Explorer |
| Backup data | Database Explorer → Export |
| Change thresholds | Settings |

---

## 🆘 Troubleshooting

### Upload & Analyze Issues:
- **PDF won't upload**: Check file size and format
- **No text extracted**: PDF might be image-based (needs OCR)
- **Analysis taking long**: Normal for large files, check progress

### Database Explorer Issues:
- **No results**: Check search terms, try broader keywords
- **Export fails**: Check disk space and permissions

### Knowledge Graph Issues:
- **Graph won't load**: Need at least 3 papers in database
- **Slow performance**: Large databases (>200 papers) take time

### Statistics Issues:
- **No data shown**: Need to run at least one detection
- **Charts not updating**: Click "Rebuild Statistics"

### Settings Issues:
- **Changes not saving**: Some settings require page refresh
- **Cache won't clear**: Restart Streamlit application

---

This is your complete guide to navigating and using the Aura Streamlit UI! 🎉