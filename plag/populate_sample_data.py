"""
Simple Database Populator with Sample ML Papers
Creates realistic sample papers for testing the Aura system
"""

import os
import sys
import hashlib
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict

# Add the current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from utils import setup_logging, extract_keywords

class SamplePaperGenerator:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = setup_logging("INFO")
    
    def generate_sample_papers(self) -> List[Dict]:
        """Generate realistic sample ML papers"""
        
        # Sample paper data with realistic ML topics
        sample_papers = [
            {
                'title': 'Deep Learning for Image Classification: A Comprehensive Survey',
                'abstract': 'This paper presents a comprehensive survey of deep learning techniques for image classification. We analyze various convolutional neural network architectures including ResNet, DenseNet, and EfficientNet. Our analysis covers performance metrics, computational efficiency, and practical applications across different domains.',
                'content': '''Deep learning has revolutionized the field of computer vision, particularly in image classification tasks. This comprehensive survey examines the evolution of deep learning architectures from basic multilayer perceptrons to sophisticated convolutional neural networks (CNNs).

Convolutional Neural Networks have become the foundation of modern image classification systems. The introduction of architectures like LeNet, AlexNet, and VGGNet laid the groundwork for more advanced models. ResNet introduced residual connections, enabling the training of much deeper networks by addressing the vanishing gradient problem.

DenseNet further improved upon these concepts by connecting each layer to every other layer in a feed-forward fashion. This approach reduces the number of parameters while improving gradient flow. EfficientNet optimized the balance between model accuracy and computational efficiency through compound scaling.

Our experimental evaluation demonstrates that these architectures achieve state-of-the-art performance on standard benchmarks including ImageNet, CIFAR-10, and CIFAR-100. The results show significant improvements in both accuracy and inference speed compared to earlier approaches.''',
                'authors': ['Sarah Johnson', 'Michael Chen', 'David Rodriguez'],
                'venue': 'IEEE Transactions on Pattern Analysis and Machine Intelligence',
                'keywords': ['deep learning', 'image classification', 'convolutional neural networks', 'computer vision', 'ResNet', 'DenseNet', 'EfficientNet']
            },
            {
                'title': 'Attention Mechanisms in Natural Language Processing: From Theory to Practice',
                'abstract': 'We explore the development and application of attention mechanisms in natural language processing. From the original attention mechanism to transformers and BERT, this work analyzes the theoretical foundations and practical implementations that have shaped modern NLP.',
                'content': '''Attention mechanisms have fundamentally transformed natural language processing, enabling models to focus on relevant parts of input sequences. The attention mechanism was first introduced to address limitations in sequence-to-sequence models for machine translation.

The transformer architecture revolutionized the field by relying entirely on attention mechanisms, eliminating the need for recurrent connections. Self-attention allows the model to attend to different positions within the same sequence, capturing long-range dependencies more effectively than traditional RNNs.

BERT (Bidirectional Encoder Representations from Transformers) demonstrated the power of pre-trained transformer models. By training on large corpora using masked language modeling, BERT achieved state-of-the-art results across numerous NLP tasks including question answering, sentiment analysis, and named entity recognition.

GPT models further advanced the field by showing that large-scale language models can exhibit emergent capabilities. The scaling of transformer architectures has led to remarkable improvements in text generation, summarization, and even reasoning tasks.''',
                'authors': ['Emily Zhang', 'Robert Wilson', 'Lisa Park'],
                'venue': 'Association for Computational Linguistics (ACL)',
                'keywords': ['attention mechanisms', 'natural language processing', 'transformers', 'BERT', 'GPT', 'self-attention', 'machine translation']
            },
            {
                'title': 'Reinforcement Learning for Autonomous Systems: Challenges and Solutions',
                'abstract': 'This paper examines the application of reinforcement learning in autonomous systems. We discuss the challenges of sparse rewards, exploration-exploitation trade-offs, and safety considerations in real-world deployments of RL agents.',
                'content': '''Reinforcement learning has emerged as a powerful paradigm for training autonomous systems. Unlike supervised learning, RL agents learn through interaction with their environment, making it particularly suitable for sequential decision-making tasks.

The exploration-exploitation trade-off remains one of the fundamental challenges in reinforcement learning. Agents must balance between exploiting known good actions and exploring potentially better alternatives. Various strategies including epsilon-greedy, Upper Confidence Bounds (UCB), and Thompson sampling have been developed to address this challenge.

Deep reinforcement learning combines neural networks with RL algorithms, enabling agents to handle high-dimensional state spaces. Deep Q-Networks (DQN) demonstrated that neural networks could successfully approximate Q-values, while policy gradient methods like REINFORCE and Actor-Critic architectures provided alternative approaches.

Safety considerations are crucial when deploying RL systems in real-world applications. Techniques such as safe exploration, constrained optimization, and formal verification methods are essential for ensuring reliable autonomous behavior.''',
                'authors': ['James Thompson', 'Maria Garcia', 'Kevin Liu'],
                'venue': 'International Conference on Robotics and Automation (ICRA)',
                'keywords': ['reinforcement learning', 'autonomous systems', 'exploration exploitation', 'deep reinforcement learning', 'safety', 'robotics']
            },
            {
                'title': 'Generative Adversarial Networks: Advances in Synthetic Data Generation',
                'abstract': 'We present recent advances in Generative Adversarial Networks (GANs) for synthetic data generation. Our work covers architectural improvements, training stability techniques, and applications across multiple domains including computer vision and healthcare.',
                'content': '''Generative Adversarial Networks have become a cornerstone of generative modeling, enabling the creation of realistic synthetic data across various domains. The adversarial training process between generator and discriminator networks creates a competitive environment that drives both networks to improve.

Training stability has been a major challenge in GAN development. Techniques such as Wasserstein GANs, Spectral Normalization, and Progressive Growing have significantly improved training stability and output quality. These advances have made GANs more practical for real-world applications.

StyleGAN introduced style-based generators that provide unprecedented control over generated images. The disentangled representation of style and content enables fine-grained manipulation of generated samples, opening new possibilities for creative applications and data augmentation.

Conditional GANs extend the basic GAN framework by incorporating additional information during training. This enables controlled generation where users can specify desired attributes of the generated samples, making GANs more practical for specific applications.''',
                'authors': ['Alex Morgan', 'Jennifer Kim', 'Daniel Brown'],
                'venue': 'Neural Information Processing Systems (NeurIPS)',
                'keywords': ['generative adversarial networks', 'synthetic data generation', 'StyleGAN', 'training stability', 'conditional generation']
            },
            {
                'title': 'Graph Neural Networks for Social Network Analysis',
                'abstract': 'This paper introduces novel graph neural network architectures for analyzing social networks. We propose methods for node classification, link prediction, and community detection, demonstrating superior performance on real-world social media datasets.',
                'content': '''Graph Neural Networks have emerged as powerful tools for analyzing structured data, particularly in social network analysis. Unlike traditional neural networks that operate on Euclidean data, GNNs can directly process graph-structured information.

Message passing is the core mechanism in most GNN architectures. Nodes aggregate information from their neighbors through learnable functions, enabling the network to capture both local and global graph structure. Graph Convolutional Networks (GCNs) and GraphSAGE are prominent examples of this approach.

Social networks exhibit unique characteristics such as homophily, where connected nodes tend to have similar attributes. GNNs can effectively model these properties for tasks like node classification, where the goal is to predict user attributes based on network structure and available features.

Community detection in social networks benefits from GNN architectures that can identify densely connected subgroups. By learning embeddings that capture community structure, GNNs outperform traditional clustering methods on large-scale social networks.''',
                'authors': ['Rachel Adams', 'Thomas Lee', 'Amanda Foster'],
                'venue': 'International Conference on Web and Social Media (ICWSM)',
                'keywords': ['graph neural networks', 'social network analysis', 'node classification', 'community detection', 'message passing', 'homophily']
            },
            {
                'title': 'Federated Learning: Privacy-Preserving Machine Learning at Scale',
                'abstract': 'We investigate federated learning approaches for training machine learning models while preserving data privacy. Our work addresses challenges in non-IID data distribution, communication efficiency, and differential privacy in distributed settings.',
                'content': '''Federated learning enables collaborative machine learning without centralizing data, addressing growing privacy concerns in the digital age. Instead of collecting data in a central location, the model is trained across distributed devices or servers.

Non-IID (non-independent and identically distributed) data poses significant challenges in federated settings. Different clients may have vastly different data distributions, leading to model drift and convergence issues. Techniques such as FedAvg, FedProx, and SCAFFOLD have been developed to handle data heterogeneity.

Communication efficiency is crucial in federated learning due to bandwidth limitations and communication costs. Model compression techniques, gradient compression, and selective participation strategies help reduce communication overhead while maintaining model performance.

Differential privacy provides formal guarantees for privacy protection in federated learning. By adding calibrated noise to model updates, differential privacy ensures that individual data points cannot be inferred from the trained model, enabling privacy-preserving machine learning at scale.''',
                'authors': ['Sophie Turner', 'Nathan Cooper', 'Grace Martinez'],
                'venue': 'International Conference on Machine Learning (ICML)',
                'keywords': ['federated learning', 'privacy preserving', 'non-IID data', 'differential privacy', 'distributed learning', 'communication efficiency']
            }
        ]
        
        return sample_papers
    
    def populate_database(self, num_papers: int = 20) -> Dict:
        """Populate database with sample papers"""
        self.logger.info(f"Populating database with {num_papers} sample ML papers")
        
        sample_papers = self.generate_sample_papers()
        results = {
            'requested': num_papers,
            'added': 0,
            'failed': 0,
            'already_existed': 0
        }
        
        # Generate additional papers by modifying existing ones
        extended_papers = []
        while len(extended_papers) < num_papers:
            for base_paper in sample_papers:
                if len(extended_papers) >= num_papers:
                    break
                
                # Create variations
                variation = self.create_paper_variation(base_paper, len(extended_papers))
                extended_papers.append(variation)
        
        # Add papers to database
        for i, paper_data in enumerate(extended_papers[:num_papers]):
            try:
                # Generate unique hash
                content_for_hash = f"{paper_data['title']}_{paper_data['abstract']}_{i}"
                file_hash = hashlib.sha256(content_for_hash.encode()).hexdigest()
                
                # Check if already exists
                existing = self.db_manager.get_paper_by_hash(file_hash)
                if existing:
                    results['already_existed'] += 1
                    continue
                
                # Extract keywords
                combined_text = f"{paper_data['title']} {paper_data['abstract']} {paper_data['content']}"
                keywords = paper_data.get('keywords', [])
                if not keywords:
                    keywords = extract_keywords(combined_text, top_n=10)
                
                # Add paper
                paper_id = self.db_manager.add_paper(
                    title=paper_data['title'],
                    content=paper_data['content'],
                    abstract=paper_data['abstract'],
                    authors=paper_data['authors'],
                    keywords=keywords,
                    file_hash=file_hash,
                    venue=paper_data.get('venue', 'Sample Conference')
                )
                
                if paper_id:
                    results['added'] += 1
                    self.logger.info(f"Added paper {results['added']}/{num_papers}: {paper_data['title'][:50]}...")
                else:
                    results['failed'] += 1
                
            except Exception as e:
                self.logger.error(f"Error adding paper: {e}")
                results['failed'] += 1
        
        # Get final database stats
        db_stats = self.db_manager.get_database_stats()
        
        self.logger.info(f"\n🎉 Database population complete!")
        self.logger.info(f"Added: {results['added']} papers")
        self.logger.info(f"Failed: {results['failed']} papers") 
        self.logger.info(f"Already existed: {results['already_existed']} papers")
        self.logger.info(f"Total papers in database: {db_stats.get('papers', 0)}")
        
        return results
    
    def create_paper_variation(self, base_paper: Dict, variation_num: int) -> Dict:
        """Create a variation of a base paper"""
        
        # Variation techniques
        title_prefixes = [
            "A Novel Approach to", "Improved Methods for", "Advanced Techniques in",
            "Efficient Algorithms for", "Scalable Solutions for", "Robust Framework for",
            "Comparative Study of", "Empirical Analysis of", "Theoretical Foundations of"
        ]
        
        abstract_modifications = [
            "This work extends previous research by",
            "We propose novel improvements to",
            "Our methodology enhances existing approaches through",
            "This study investigates advanced techniques for",
            "We present a comprehensive framework for"
        ]
        
        # Create variation
        variation = base_paper.copy()
        
        # Vary title
        if variation_num % 3 == 0 and variation_num > 0:
            prefix = random.choice(title_prefixes)
            variation['title'] = f"{prefix} {base_paper['title']}"
        elif variation_num % 3 == 1:
            variation['title'] = base_paper['title'].replace("Deep Learning", "Machine Learning")
            variation['title'] = variation['title'].replace("Neural Networks", "Deep Networks")
        
        # Vary abstract
        if variation_num % 2 == 1:
            mod = random.choice(abstract_modifications)
            variation['abstract'] = f"{mod} {base_paper['abstract']}"
        
        # Vary authors (simulate different research groups)
        author_variations = [
            ['Dr. ' + name for name in base_paper['authors']],
            [name + ', PhD' for name in base_paper['authors']],
            base_paper['authors'][:2] + ['Prof. John Smith'],  # Add/remove authors
            ['Team Lead ' + base_paper['authors'][0]] + base_paper['authors'][1:]
        ]
        variation['authors'] = author_variations[variation_num % len(author_variations)]
        
        # Vary venue slightly
        venues = [
            'IEEE Conference on Computer Vision and Pattern Recognition',
            'International Joint Conference on Artificial Intelligence',
            'European Conference on Machine Learning',
            'AAAI Conference on Artificial Intelligence',
            base_paper.get('venue', 'Sample Conference')
        ]
        variation['venue'] = venues[variation_num % len(venues)]
        
        return variation

def main():
    """Main execution function"""
    print("🚀 Starting Aura Sample Database Population")
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Create sample generator
    generator = SamplePaperGenerator(db_manager)
    
    # Get current stats
    current_stats = db_manager.get_database_stats()
    print(f"Current papers in database: {current_stats.get('papers', 0)}")
    
    # Ask how many papers to add
    num_papers = input("How many sample papers to generate? (default: 20): ").strip()
    num_papers = int(num_papers) if num_papers.isdigit() else 20
    
    # Populate database
    results = generator.populate_database(num_papers)
    
    print(f"\n✅ Sample database population completed!")
    print(f"Your Aura system now has realistic ML papers for testing.")
    
    return results

if __name__ == "__main__":
    main()