# Aura - Academic Plagiarism Detection System

Aura is an AI-powered plagiarism detection system designed for academic research papers. It uses semantic similarity measures and knowledge graphs to identify paraphrased or copied content across documents.

## Features

- **PDF Upload & Analysis**: Upload research papers in PDF format for plagiarism detection
- **Semantic Plagiarism Detection**: Identify paraphrased content using advanced NLP techniques
- **Academic Knowledge Graph**: Build relationships between papers, authors, topics, and methods
- **Research Discovery**: Find relevant work and collaborators using natural language queries
- **Interactive Dashboard**: User-friendly Streamlit interface with visualizations

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Download required NLTK data:
   ```python
   import nltk
   nltk.download('punkt')
   nltk.download('stopwords')
   ```

## Usage

Run the Streamlit application:
```bash
streamlit run app.py
```

## Project Structure

- `app.py` - Main Streamlit application
- `database/` - Database models and management
- `modules/` - Core functionality modules
- `utils/` - Utility functions
- `data/` - Sample data and exports

## Architecture

The system consists of:
1. PDF text extraction module
2. Academic Knowledge Graph construction
3. Semantic similarity engine
4. Plagiarism detection algorithm
5. Database management system
6. Interactive web interface

## Contributing

This project is part of academic research in AI-powered academic integrity systems.