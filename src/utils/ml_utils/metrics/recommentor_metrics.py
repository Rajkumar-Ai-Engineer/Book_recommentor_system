import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score
from typing import List, Dict, Tuple

class RecommendationMetrics:
    """
    Metrics for evaluating recommendation systems
    """
    
    @staticmethod
    def precision_at_k(actual: List, predicted: List, k: int = 10) -> float:
        """
        Calculate Precision@K
        """
        if not predicted or k <= 0:
            return 0.0
            
        predicted_k = predicted[:k]
        relevant_items = len(set(actual) & set(predicted_k))
        return relevant_items / min(k, len(predicted_k))
    
    @staticmethod
    def recall_at_k(actual: List, predicted: List, k: int = 10) -> float:
        """
        Calculate Recall@K
        """
        if not actual or not predicted or k <= 0:
            return 0.0
            
        predicted_k = predicted[:k]
        relevant_items = len(set(actual) & set(predicted_k))
        return relevant_items / len(actual)
    
    @staticmethod
    def f1_at_k(actual: List, predicted: List, k: int = 10) -> float:
        """
        Calculate F1@K
        """
        precision = RecommendationMetrics.precision_at_k(actual, predicted, k)
        recall = RecommendationMetrics.recall_at_k(actual, predicted, k)
        
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)
    
    @staticmethod
    def ndcg_at_k(actual: List, predicted: List, k: int = 10) -> float:
        """
        Calculate Normalized Discounted Cumulative Gain@K
        """
        if not actual or not predicted or k <= 0:
            return 0.0
            
        predicted_k = predicted[:k]
        
        # Calculate DCG
        dcg = 0.0
        for i, item in enumerate(predicted_k):
            if item in actual:
                dcg += 1.0 / np.log2(i + 2)  # +2 because log2(1) = 0
        
        # Calculate IDCG (Ideal DCG)
        idcg = 0.0
        for i in range(min(len(actual), k)):
            idcg += 1.0 / np.log2(i + 2)
        
        return dcg / idcg if idcg > 0 else 0.0
    
    @staticmethod
    def coverage(predicted_items: List[List], total_items: int) -> float:
        """
        Calculate catalog coverage
        """
        if not predicted_items or total_items <= 0:
            return 0.0
            
        unique_recommended = set()
        for items in predicted_items:
            unique_recommended.update(items)
        
        return len(unique_recommended) / total_items
    
    @staticmethod
    def diversity(predicted_items: List[List]) -> float:
        """
        Calculate intra-list diversity (average pairwise distance)
        """
        if not predicted_items:
            return 0.0
            
        diversities = []
        for items in predicted_items:
            if len(items) <= 1:
                diversities.append(0.0)
                continue
                
            # Calculate pairwise diversity (simple Jaccard distance)
            total_pairs = 0
            diverse_pairs = 0
            
            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    total_pairs += 1
                    if items[i] != items[j]:  # Different items
                        diverse_pairs += 1
            
            diversity = diverse_pairs / total_pairs if total_pairs > 0 else 0.0
            diversities.append(diversity)
        
        return np.mean(diversities)
    
    @staticmethod
    def evaluate_recommendations(
        test_data: pd.DataFrame,
        model,
        k: int = 10
    ) -> Dict[str, float]:
        """
        Comprehensive evaluation of recommendation model
        """
        precisions = []
        recalls = []
        f1_scores = []
        ndcgs = []
        all_predictions = []
        
        # Sample test cases (limit for performance)
        test_sample = test_data.sample(min(1000, len(test_data)), random_state=42)
        
        for _, row in test_sample.iterrows():
            user_id = row['User-ID']
            actual_isbn = row['ISBN']
            
            # Get user's other rated books as ground truth
            user_books = test_data[test_data['User-ID'] == user_id]['ISBN'].tolist()
            
            if len(user_books) < 2:  # Need at least 2 books for evaluation
                continue
            
            # Use one book to get recommendations, others as ground truth
            query_book = user_books[0]
            actual_books = user_books[1:]
            
            try:
                # Get book title for the query
                book_title = test_data[test_data['ISBN'] == query_book]['Book-Title'].iloc[0] if 'Book-Title' in test_data.columns else "Unknown"
                
                # Get recommendations
                result = model.recommend(book_title, top_k=k)
                
                if 'error' in result:
                    continue
                    
                predicted_isbns = [rec['isbn'] for rec in result['recommendations']]
                all_predictions.append(predicted_isbns)
                
                # Calculate metrics
                precision = RecommendationMetrics.precision_at_k(actual_books, predicted_isbns, k)
                recall = RecommendationMetrics.recall_at_k(actual_books, predicted_isbns, k)
                f1 = RecommendationMetrics.f1_at_k(actual_books, predicted_isbns, k)
                ndcg = RecommendationMetrics.ndcg_at_k(actual_books, predicted_isbns, k)
                
                precisions.append(precision)
                recalls.append(recall)
                f1_scores.append(f1)
                ndcgs.append(ndcg)
                
            except Exception as e:
                continue
        
        # Calculate coverage and diversity
        total_books = test_data['ISBN'].nunique() if 'ISBN' in test_data.columns else 1
        coverage = RecommendationMetrics.coverage(all_predictions, total_books)
        diversity = RecommendationMetrics.diversity(all_predictions)
        
        return {
            'precision_at_k': np.mean(precisions) if precisions else 0.0,
            'recall_at_k': np.mean(recalls) if recalls else 0.0,
            'f1_at_k': np.mean(f1_scores) if f1_scores else 0.0,
            'ndcg_at_k': np.mean(ndcgs) if ndcgs else 0.0,
            'coverage': coverage,
            'diversity': diversity,
            'num_evaluations': len(precisions)
        }

def get_classification_metrics(y_true, y_pred) -> Dict[str, float]:
    """
    Calculate classification metrics for binary relevance
    """
    try:
        precision = precision_score(y_true, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_true, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }
    except Exception as e:
        return {
            'precision': 0.0,
            'recall': 0.0,
            'f1_score': 0.0
        }