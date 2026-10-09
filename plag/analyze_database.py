"""
Database Analysis and Export Tool for Aura System
Analyzes the populated database and exports data in various formats
"""

import os
import sys
import json
import csv
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict

# Add the current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from utils import setup_logging

class DatabaseAnalyzer:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = setup_logging("INFO")
        
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        stats = {}
        
        try:
            # Basic counts
            basic_stats = self.db_manager.get_database_stats()
            stats['basic'] = basic_stats
            
            # Paper statistics
            papers = self.db_manager.get_all_papers()
            if papers:
                paper_stats = {
                    'total_papers': len(papers),
                    'avg_content_length': sum(len(p.get('content', '')) for p in papers) / len(papers),
                    'papers_with_abstracts': sum(1 for p in papers if p.get('abstract')),
                    'avg_abstract_length': sum(len(p.get('abstract', '')) for p in papers if p.get('abstract')) / max(1, sum(1 for p in papers if p.get('abstract'))),
                }
                stats['papers'] = paper_stats
            
            # Author statistics
            authors = self.db_manager.get_all_authors()
            if authors:
                author_names = [a.get('name', '') for a in authors]
                author_stats = {
                    'total_authors': len(authors),
                    'unique_authors': len(set(author_names)),
                    'avg_name_length': sum(len(name) for name in author_names) / len(author_names),
                }
                stats['authors'] = author_stats
            
            # Topic statistics
            topics = self.db_manager.get_all_topics()
            if topics:
                topic_categories = [t.get('category', 'unknown') for t in topics]
                topic_stats = {
                    'total_topics': len(topics),
                    'unique_categories': len(set(topic_categories)),
                    'category_distribution': dict(Counter(topic_categories)),
                }
                stats['topics'] = topic_stats
            
            # Similarity statistics
            similarities = self.db_manager.get_all_similarities()
            if similarities:
                similarity_scores = [s.get('similarity_score', 0) for s in similarities]
                similarity_stats = {
                    'total_similarities': len(similarities),
                    'avg_similarity': sum(similarity_scores) / len(similarity_scores),
                    'max_similarity': max(similarity_scores),
                    'min_similarity': min(similarity_scores),
                    'high_similarity_count': sum(1 for s in similarity_scores if s > 0.8),
                }
                stats['similarities'] = similarity_stats
            
        except Exception as e:
            self.logger.error(f"Error getting comprehensive stats: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def analyze_content_distribution(self) -> Dict[str, Any]:
        """Analyze content length and keyword distribution"""
        analysis = {}
        
        try:
            papers = self.db_manager.get_all_papers()
            if not papers:
                return {'error': 'No papers found in database'}
            
            # Content length analysis
            content_lengths = [len(p.get('content', '')) for p in papers]
            analysis['content_lengths'] = {
                'mean': sum(content_lengths) / len(content_lengths),
                'median': sorted(content_lengths)[len(content_lengths)//2],
                'min': min(content_lengths),
                'max': max(content_lengths),
                'papers_with_content': sum(1 for length in content_lengths if length > 0)
            }
            
            # Keyword analysis
            all_keywords = []
            for paper in papers:
                keywords = paper.get('keywords', [])
                if isinstance(keywords, str):
                    keywords = [k.strip() for k in keywords.split(',')]
                all_keywords.extend([k.lower() for k in keywords if k.strip()])
            
            keyword_counter = Counter(all_keywords)
            analysis['keywords'] = {
                'total_keywords': len(all_keywords),
                'unique_keywords': len(keyword_counter),
                'top_10_keywords': keyword_counter.most_common(10),
                'avg_keywords_per_paper': len(all_keywords) / len(papers) if papers else 0
            }
            
            # Author analysis
            all_authors = []
            for paper in papers:
                authors = paper.get('authors', [])
                if isinstance(authors, str):
                    authors = [a.strip() for a in authors.split(',')]
                all_authors.extend(authors)
            
            author_counter = Counter(all_authors)
            analysis['authors'] = {
                'total_author_mentions': len(all_authors),
                'unique_authors': len(author_counter),
                'prolific_authors': author_counter.most_common(5),
                'avg_authors_per_paper': len(all_authors) / len(papers) if papers else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing content distribution: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    def export_to_csv(self, output_dir: str = "exports") -> Dict[str, str]:
        """Export database contents to CSV files"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        exported_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Export papers
            papers = self.db_manager.get_all_papers()
            if papers:
                papers_file = os.path.join(output_dir, f"papers_{timestamp}.csv")
                
                # Prepare papers data for CSV
                papers_data = []
                for paper in papers:
                    # Convert lists to strings for CSV
                    authors_str = ', '.join(paper.get('authors', [])) if isinstance(paper.get('authors'), list) else str(paper.get('authors', ''))
                    keywords_str = ', '.join(paper.get('keywords', [])) if isinstance(paper.get('keywords'), list) else str(paper.get('keywords', ''))
                    
                    papers_data.append({
                        'id': paper.get('id'),
                        'title': paper.get('title', ''),
                        'content_length': len(paper.get('content', '')),
                        'abstract_length': len(paper.get('abstract', '')),
                        'authors': authors_str,
                        'keywords': keywords_str,
                        'venue': paper.get('venue', ''),
                        'file_hash': paper.get('file_hash', ''),
                        'created_at': paper.get('created_at', '')
                    })
                
                df_papers = pd.DataFrame(papers_data)
                df_papers.to_csv(papers_file, index=False, encoding='utf-8')
                exported_files['papers'] = papers_file
                self.logger.info(f"Exported {len(papers)} papers to {papers_file}")
            
            # Export authors
            authors = self.db_manager.get_all_authors()
            if authors:
                authors_file = os.path.join(output_dir, f"authors_{timestamp}.csv")
                
                authors_data = []
                for author in authors:
                    research_areas_str = ', '.join(author.get('research_areas', [])) if isinstance(author.get('research_areas'), list) else str(author.get('research_areas', ''))
                    
                    authors_data.append({
                        'id': author.get('id'),
                        'name': author.get('name', ''),
                        'research_areas': research_areas_str,
                        'created_at': author.get('created_at', '')
                    })
                
                df_authors = pd.DataFrame(authors_data)
                df_authors.to_csv(authors_file, index=False, encoding='utf-8')
                exported_files['authors'] = authors_file
                self.logger.info(f"Exported {len(authors)} authors to {authors_file}")
            
            # Export topics
            topics = self.db_manager.get_all_topics()
            if topics:
                topics_file = os.path.join(output_dir, f"topics_{timestamp}.csv")
                df_topics = pd.DataFrame(topics)
                df_topics.to_csv(topics_file, index=False, encoding='utf-8')
                exported_files['topics'] = topics_file
                self.logger.info(f"Exported {len(topics)} topics to {topics_file}")
            
            # Export similarities
            similarities = self.db_manager.get_all_similarities()
            if similarities:
                similarities_file = os.path.join(output_dir, f"similarities_{timestamp}.csv")
                df_similarities = pd.DataFrame(similarities)
                df_similarities.to_csv(similarities_file, index=False, encoding='utf-8')
                exported_files['similarities'] = similarities_file
                self.logger.info(f"Exported {len(similarities)} similarities to {similarities_file}")
            
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {e}")
            exported_files['error'] = str(e)
        
        return exported_files
    
    def generate_analysis_report(self, output_dir: str = "exports") -> str:
        """Generate comprehensive analysis report"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(output_dir, f"database_analysis_report_{timestamp}.txt")
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("AURA SYSTEM DATABASE ANALYSIS REPORT\n")
                f.write("=" * 80 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Comprehensive statistics
                f.write("1. DATABASE OVERVIEW\n")
                f.write("-" * 40 + "\n")
                stats = self.get_comprehensive_stats()
                
                if 'basic' in stats:
                    f.write(f"Total Papers: {stats['basic'].get('papers', 0)}\n")
                    f.write(f"Total Authors: {stats['basic'].get('authors', 0)}\n")
                    f.write(f"Total Topics: {stats['basic'].get('topics', 0)}\n")
                    f.write(f"Total Similarities: {stats['basic'].get('similarities', 0)}\n\n")
                
                # Paper statistics
                if 'papers' in stats:
                    f.write("2. PAPER STATISTICS\n")
                    f.write("-" * 40 + "\n")
                    paper_stats = stats['papers']
                    f.write(f"Average Content Length: {paper_stats.get('avg_content_length', 0):.0f} characters\n")
                    f.write(f"Papers with Abstracts: {paper_stats.get('papers_with_abstracts', 0)}\n")
                    f.write(f"Average Abstract Length: {paper_stats.get('avg_abstract_length', 0):.0f} characters\n\n")
                
                # Content distribution analysis
                f.write("3. CONTENT ANALYSIS\n")
                f.write("-" * 40 + "\n")
                content_analysis = self.analyze_content_distribution()
                
                if 'keywords' in content_analysis:
                    kw_stats = content_analysis['keywords']
                    f.write(f"Total Keywords: {kw_stats.get('total_keywords', 0)}\n")
                    f.write(f"Unique Keywords: {kw_stats.get('unique_keywords', 0)}\n")
                    f.write(f"Average Keywords per Paper: {kw_stats.get('avg_keywords_per_paper', 0):.1f}\n")
                    
                    f.write("\nTop 10 Keywords:\n")
                    for keyword, count in kw_stats.get('top_10_keywords', []):
                        f.write(f"  {keyword}: {count}\n")
                    f.write("\n")
                
                # Author analysis
                if 'authors' in content_analysis:
                    auth_stats = content_analysis['authors']
                    f.write("4. AUTHOR ANALYSIS\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"Total Author Mentions: {auth_stats.get('total_author_mentions', 0)}\n")
                    f.write(f"Unique Authors: {auth_stats.get('unique_authors', 0)}\n")
                    f.write(f"Average Authors per Paper: {auth_stats.get('avg_authors_per_paper', 0):.1f}\n")
                    
                    f.write("\nMost Prolific Authors:\n")
                    for author, count in auth_stats.get('prolific_authors', []):
                        f.write(f"  {author}: {count} papers\n")
                    f.write("\n")
                
                # Topic distribution
                if 'topics' in stats:
                    f.write("5. TOPIC DISTRIBUTION\n")
                    f.write("-" * 40 + "\n")
                    topic_stats = stats['topics']
                    f.write(f"Total Topics: {topic_stats.get('total_topics', 0)}\n")
                    f.write(f"Topic Categories: {topic_stats.get('unique_categories', 0)}\n")
                    
                    f.write("\nCategory Distribution:\n")
                    for category, count in topic_stats.get('category_distribution', {}).items():
                        f.write(f"  {category}: {count}\n")
                    f.write("\n")
                
                # Similarity analysis
                if 'similarities' in stats:
                    f.write("6. SIMILARITY ANALYSIS\n")
                    f.write("-" * 40 + "\n")
                    sim_stats = stats['similarities']
                    f.write(f"Total Similarity Records: {sim_stats.get('total_similarities', 0)}\n")
                    f.write(f"Average Similarity Score: {sim_stats.get('avg_similarity', 0):.3f}\n")
                    f.write(f"Maximum Similarity: {sim_stats.get('max_similarity', 0):.3f}\n")
                    f.write(f"Minimum Similarity: {sim_stats.get('min_similarity', 0):.3f}\n")
                    f.write(f"High Similarity Pairs (>0.8): {sim_stats.get('high_similarity_count', 0)}\n\n")
                
                # System recommendations
                f.write("7. SYSTEM RECOMMENDATIONS\n")
                f.write("-" * 40 + "\n")
                
                total_papers = stats.get('basic', {}).get('papers', 0)
                if total_papers < 50:
                    f.write("⚠️  Consider adding more papers to improve plagiarism detection accuracy.\n")
                elif total_papers >= 100:
                    f.write("✅ Good paper coverage for plagiarism detection.\n")
                
                total_similarities = stats.get('basic', {}).get('similarities', 0)
                if total_similarities == 0:
                    f.write("⚠️  No similarity relationships found. Run knowledge graph builder.\n")
                else:
                    f.write("✅ Similarity relationships established for improved detection.\n")
                
                if 'keywords' in content_analysis:
                    unique_keywords = content_analysis['keywords'].get('unique_keywords', 0)
                    if unique_keywords > 500:
                        f.write("✅ Rich keyword diversity for semantic analysis.\n")
                    else:
                        f.write("⚠️  Consider adding more diverse papers to improve keyword coverage.\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write("End of Report\n")
            
            self.logger.info(f"Analysis report generated: {report_file}")
            return report_file
            
        except Exception as e:
            self.logger.error(f"Error generating analysis report: {e}")
            return f"Error: {e}"
    
    def create_visualization_plots(self, output_dir: str = "exports") -> Dict[str, str]:
        """Create visualization plots of database contents"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        plot_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Set style
            plt.style.use('default')
            sns.set_palette("husl")
            
            # Get data for plotting
            content_analysis = self.analyze_content_distribution()
            stats = self.get_comprehensive_stats()
            
            # Plot 1: Keyword frequency
            if 'keywords' in content_analysis and content_analysis['keywords'].get('top_10_keywords'):
                fig, ax = plt.subplots(figsize=(12, 6))
                
                keywords, counts = zip(*content_analysis['keywords']['top_10_keywords'])
                bars = ax.bar(range(len(keywords)), counts, color='skyblue', edgecolor='navy', alpha=0.7)
                
                ax.set_xlabel('Keywords')
                ax.set_ylabel('Frequency')
                ax.set_title('Top 10 Most Frequent Keywords in Database')
                ax.set_xticks(range(len(keywords)))
                ax.set_xticklabels(keywords, rotation=45, ha='right')
                
                # Add value labels on bars
                for bar, count in zip(bars, counts):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                           str(count), ha='center', va='bottom')
                
                plt.tight_layout()
                keyword_plot = os.path.join(output_dir, f"keywords_frequency_{timestamp}.png")
                plt.savefig(keyword_plot, dpi=300, bbox_inches='tight')
                plt.close()
                plot_files['keywords'] = keyword_plot
            
            # Plot 2: Database composition
            if 'basic' in stats:
                fig, ax = plt.subplots(figsize=(8, 8))
                
                labels = ['Papers', 'Authors', 'Topics', 'Similarities']
                sizes = [
                    stats['basic'].get('papers', 0),
                    stats['basic'].get('authors', 0),
                    stats['basic'].get('topics', 0),
                    stats['basic'].get('similarities', 0)
                ]
                
                colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
                
                # Remove zero values
                non_zero_data = [(label, size, color) for label, size, color in zip(labels, sizes, colors) if size > 0]
                if non_zero_data:
                    labels, sizes, colors = zip(*non_zero_data)
                    
                    wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                    ax.set_title('Database Composition')
                    
                    composition_plot = os.path.join(output_dir, f"database_composition_{timestamp}.png")
                    plt.savefig(composition_plot, dpi=300, bbox_inches='tight')
                    plt.close()
                    plot_files['composition'] = composition_plot
            
            # Plot 3: Content length distribution
            papers = self.db_manager.get_all_papers()
            if papers:
                content_lengths = [len(p.get('content', '')) for p in papers if len(p.get('content', '')) > 0]
                
                if content_lengths:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    ax.hist(content_lengths, bins=20, color='lightcoral', alpha=0.7, edgecolor='black')
                    ax.set_xlabel('Content Length (characters)')
                    ax.set_ylabel('Number of Papers')
                    ax.set_title('Distribution of Paper Content Lengths')
                    ax.grid(True, alpha=0.3)
                    
                    # Add statistics text
                    mean_length = sum(content_lengths) / len(content_lengths)
                    ax.axvline(mean_length, color='red', linestyle='--', label=f'Mean: {mean_length:.0f}')
                    ax.legend()
                    
                    plt.tight_layout()
                    length_plot = os.path.join(output_dir, f"content_length_distribution_{timestamp}.png")
                    plt.savefig(length_plot, dpi=300, bbox_inches='tight')
                    plt.close()
                    plot_files['content_lengths'] = length_plot
            
            self.logger.info(f"Generated {len(plot_files)} visualization plots")
            
        except Exception as e:
            self.logger.error(f"Error creating visualization plots: {e}")
            plot_files['error'] = str(e)
        
        return plot_files

def main():
    """Main execution function"""
    print("📊 Starting Aura Database Analysis")
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Create analyzer
    analyzer = DatabaseAnalyzer(db_manager)
    
    # Get basic stats
    print("\n📈 Gathering database statistics...")
    stats = analyzer.get_comprehensive_stats()
    
    if 'basic' in stats:
        print(f"📄 Papers: {stats['basic'].get('papers', 0)}")
        print(f"👥 Authors: {stats['basic'].get('authors', 0)}")
        print(f"🏷️  Topics: {stats['basic'].get('topics', 0)}")
        print(f"🔗 Similarities: {stats['basic'].get('similarities', 0)}")
    
    # Analyze content
    print("\n🔍 Analyzing content distribution...")
    content_analysis = analyzer.analyze_content_distribution()
    
    if 'keywords' in content_analysis:
        print(f"🔑 Total keywords: {content_analysis['keywords'].get('total_keywords', 0)}")
        print(f"🌟 Unique keywords: {content_analysis['keywords'].get('unique_keywords', 0)}")
    
    # Export options
    print("\n📤 Export Options:")
    print("1. Export to CSV")
    print("2. Generate analysis report")
    print("3. Create visualization plots")
    print("4. Do all")
    
    choice = input("Choose option (1-4): ").strip()
    
    if choice in ['1', '4']:
        print("\n📊 Exporting to CSV...")
        csv_files = analyzer.export_to_csv()
        for file_type, file_path in csv_files.items():
            if file_type != 'error':
                print(f"✅ Exported {file_type}: {file_path}")
    
    if choice in ['2', '4']:
        print("\n📋 Generating analysis report...")
        report_file = analyzer.generate_analysis_report()
        print(f"✅ Report generated: {report_file}")
    
    if choice in ['3', '4']:
        print("\n📈 Creating visualization plots...")
        try:
            plot_files = analyzer.create_visualization_plots()
            for plot_type, plot_path in plot_files.items():
                if plot_type != 'error':
                    print(f"✅ Plot created {plot_type}: {plot_path}")
        except ImportError:
            print("⚠️  Matplotlib/Seaborn not available. Install with: pip install matplotlib seaborn")
        except Exception as e:
            print(f"❌ Error creating plots: {e}")
    
    print("\n🎉 Analysis completed!")

if __name__ == "__main__":
    main()