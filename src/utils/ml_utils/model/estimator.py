"""
Hybrid Recommendation Model - Main estimator class
"""

import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import linear_kernel
from sklearn.neighbors import NearestNeighbors
from src.logger import GLOBAL_LOGGER as log


class HybridRecommendationModel:
    """
    Hybrid Recommendation Model using pre-computed matrices from data transformation
    """
    
    def __init__(self):
        self.content_matrix = None
        self.collaborative_matrix = None
        self.cf_model = None
        self.books_data = None
        self.merged_data = None
        self.preprocessor = None
        self.is_trained = False
    
    def load_transformed_data(self, content_matrix, collaborative_matrix, preprocessor, merged_data, books_data):
        """
        Load pre-computed matrices and data from transformation step
        """
        self.content_matrix = content_matrix
        self.collaborative_matrix = collaborative_matrix
        self.preprocessor = preprocessor
        self.merged_data = merged_data
        self.books_data = books_data  # Can be None
        
        # Create index mappings for collaborative filtering
        # The collaborative matrix is based on unique ISBNs, not merged data indices
        unique_isbns = merged_data['ISBN'].unique()
        self.isbn_to_collab_idx = {isbn: idx for idx, isbn in enumerate(unique_isbns)}
        self.collab_idx_to_isbn = {idx: isbn for isbn, idx in self.isbn_to_collab_idx.items()}
        
        # Train collaborative filtering model
        self.cf_model = NearestNeighbors(
            algorithm='brute',
            metric='cosine',
            n_jobs=-1
        )
        self.cf_model.fit(self.collaborative_matrix)
        
        self.is_trained = True
        log.info("Model loaded with pre-computed matrices successfully")
        log.info(f"Created mappings for {len(self.isbn_to_collab_idx)} unique ISBNs")
    
    def get_content_recommendations(self, book_index, top_k=10):
        """
        Get content-based recommendations using pre-computed TF-IDF matrix
        """
        try:
            # Validate index bounds
            if book_index >= self.content_matrix.shape[0]:
                log.warning(f"Error in content recommendations: index ({book_index}) out of range")
                return []
            
            # Calculate similarity scores using pre-computed content matrix
            cosine_scores = linear_kernel(
                self.content_matrix[book_index],
                self.content_matrix
            ).flatten()
            
            # Get top similar books (excluding the input book)
            similar_indices = cosine_scores.argsort()[::-1][1:top_k+1]
            
            # Filter out invalid indices
            valid_indices = [idx for idx in similar_indices if idx < len(self.merged_data)]
            return valid_indices
        except Exception as e:
            log.warning(f"Error in content recommendations: {str(e)}")
            return []
    
    def get_collaborative_recommendations(self, book_index, top_k=10):
        """
        Get collaborative filtering recommendations using pre-computed matrix
        """
        try:
            # Get ISBN from merged data at book_index
            if book_index >= len(self.merged_data):
                log.warning(f"Error in collaborative recommendations: book_index ({book_index}) out of range for merged data")
                return []
            
            book_isbn = self.merged_data.iloc[book_index]['ISBN']
            
            # Get collaborative matrix index for this ISBN
            if book_isbn not in self.isbn_to_collab_idx:
                log.warning(f"ISBN {book_isbn} not found in collaborative matrix")
                return []
            
            collab_idx = self.isbn_to_collab_idx[book_isbn]
            
            # Validate collaborative matrix index bounds
            if collab_idx >= self.collaborative_matrix.shape[0]:
                log.warning(f"Error in collaborative recommendations: collab_index ({collab_idx}) out of range")
                return []
            
            # Get similar books using pre-trained KNN model
            distances, indices = self.cf_model.kneighbors(
                self.collaborative_matrix[collab_idx].reshape(1, -1),
                n_neighbors=min(top_k+1, self.collaborative_matrix.shape[0])
            )
            
            # Convert collaborative indices back to merged data indices
            recommended_indices = []
            for collab_idx in indices.flatten()[1:]:  # Skip first (input book)
                if collab_idx < len(self.collab_idx_to_isbn):
                    recommended_isbn = self.collab_idx_to_isbn[collab_idx]
                    # Find first occurrence of this ISBN in merged data
                    matching_rows = self.merged_data[self.merged_data['ISBN'] == recommended_isbn]
                    if not matching_rows.empty:
                        recommended_indices.append(matching_rows.index[0])
            
            return recommended_indices[:top_k]
            
        except Exception as e:
            log.warning(f"Error in collaborative recommendations: {str(e)}")
            return []
    
    def recommend(self, book_title, top_k=10):
        """
        Generate hybrid recommendations for a book title
        """
        if not self.is_trained:
            return {"error": "Model not trained"}
        
        try:
            # Find matching books in merged data
            import re
            escaped_title = re.escape(book_title)
            matching_books = self.merged_data[
                self.merged_data['Book-Title'].str.contains(
                    escaped_title, case=False, na=False, regex=True
                )
            ]
            
            if matching_books.empty:
                return {"error": "Book not found"}
            
            # Get the first match
            selected_book = matching_books.iloc[0]
            book_index = matching_books.index[0]
            
            # Get recommendations from both approaches
            content_indices = self.get_content_recommendations(book_index, top_k)
            collab_indices = self.get_collaborative_recommendations(book_index, top_k)
            
            # Combine recommendations
            recommended_books = {}
            
            # Add content-based results
            for idx in content_indices:
                if idx < len(self.merged_data):
                    book_info = self.merged_data.iloc[idx]
                    title = book_info['Book-Title']
                    cleaned_title = self._clean_title(title)
                    if cleaned_title not in recommended_books:
                        recommended_books[cleaned_title] = {
                            'title': title,
                            'author': book_info['Book-Author'],
                            'isbn': book_info['ISBN'],
                            'source': 'content'
                        }
            
            # Add collaborative results
            for idx in collab_indices:
                if idx < len(self.merged_data):
                    book_info = self.merged_data.iloc[idx]
                    title = book_info['Book-Title']
                    cleaned_title = self._clean_title(title)
                    if cleaned_title not in recommended_books:
                        recommended_books[cleaned_title] = {
                            'title': title,
                            'author': book_info['Book-Author'],
                            'isbn': book_info['ISBN'],
                            'source': 'collaborative'
                        }
            
            # Return top recommendations
            final_recommendations = list(recommended_books.values())[:top_k]
            
            return {
                "selected_book": {
                    "title": selected_book['Book-Title'],
                    "author": selected_book['Book-Author'],
                    "isbn": selected_book['ISBN']
                },
                "recommendations": final_recommendations
            }
            
        except Exception as e:
            log.error(f"Error in recommendation: {str(e)}")
            return {"error": f"Recommendation failed: {str(e)}"}
    
    def _clean_title(self, title):
        """Clean book title for deduplication"""
        title = str(title).lower()
        remove_words = ['paperback', 'hardcover', 'audio', 'large print', 'mass market']
        for word in remove_words:
            title = title.replace(word, '')
        return title.strip()
    
    def get_model_info(self):
        """Get model information"""
        if not self.is_trained:
            return {"status": "not_trained"}
        
        return {
            "status": "trained",
            "content_matrix_shape": self.content_matrix.shape if self.content_matrix is not None else None,
            "collaborative_matrix_shape": self.collaborative_matrix.shape if self.collaborative_matrix is not None else None,
            "total_books": len(self.merged_data) if self.merged_data is not None else 0,
            "unique_books": self.merged_data['ISBN'].nunique() if self.merged_data is not None else 0,
            "unique_users": self.merged_data['User-ID'].nunique() if self.merged_data is not None else 0
        }