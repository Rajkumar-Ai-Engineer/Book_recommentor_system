"""
Production-grade Batch Processing Pipeline for Book Recommendation System
Handles large-scale batch recommendation generation with optimizations
"""
import sys
import os
import pandas as pd
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.exception.custom_exception import BookRecommentorException
from src.logger import GLOBAL_LOGGER as log
from src.pipeline.prediction_pipeline import PredictionPipeline


class BatchProcessingPipeline:
    """Production batch processing pipeline for recommendations"""
    
    def __init__(self, model_path: Optional[str] = None, max_workers: int = 4):
        try:
            self.prediction_pipeline = PredictionPipeline(model_path)
            self.max_workers = max_workers
            log.info(f"Batch pipeline initialized with {max_workers} workers")
            
        except Exception as e:
            raise BookRecommentorException(e, sys) from e
            
    def process_user_batch(self, user_ids: List[int], k: int = 10, 
                          batch_size: int = 100) -> Dict[int, List[Dict]]:
        """Process recommendations for a batch of users"""
        try:
            log.info(f"Processing batch of {len(user_ids)} users with batch_size={batch_size}")
            
            results = {}
            
            # Process in smaller batches to manage memory
            for i in range(0, len(user_ids), batch_size):
                batch = user_ids[i:i+batch_size]
                log.info(f"Processing batch {i//batch_size + 1}/{(len(user_ids)-1)//batch_size + 1}")
                
                batch_results = self._process_batch_parallel(batch, k)
                results.update(batch_results)
                
            log.info(f"Batch processing completed for {len(results)} users")
            return results
            
        except Exception as e:
            raise BookRecommentorException(e, sys) from e
            
    def _process_batch_parallel(self, user_batch: List[int], k: int) -> Dict[int, List[Dict]]:
        """Process a batch of users in parallel"""
        try:
            results = {}
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit tasks
                future_to_user = {
                    executor.submit(self.prediction_pipeline.predict, user_id, k): user_id 
                    for user_id in user_batch
                }
                
                # Collect results
                for future in as_completed(future_to_user):
                    user_id = future_to_user[future]
                    try:
                        recommendations = future.result()
                        results[user_id] = recommendations
                    except Exception as e:
                        log.error(f"Error processing user {user_id}: {e}")
                        results[user_id] = []  # Empty recommendations on error
                        
            return results
            
        except Exception as e:
            raise BookRecommentorException(e, sys) from e
            
    def export_recommendations(self, recommendations: Dict[int, List[Dict]], 
                             output_path: str, format: str = 'csv') -> None:
        """Export recommendations to file"""
        try:
            log.info(f"Exporting recommendations to {output_path}")
            
            # Flatten recommendations for export
            export_data = []
            for user_id, recs in recommendations.items():
                for i, rec in enumerate(recs):
                    export_data.append({
                        'user_id': user_id,
                        'rank': i + 1,
                        'book_id': rec.get('book_id'),
                        'score': rec.get('score', 0.0),
                        'title': rec.get('title', ''),
                        'author': rec.get('author', '')
                    })
                    
            df = pd.DataFrame(export_data)
            
            if format.lower() == 'csv':
                df.to_csv(output_path, index=False)
            elif format.lower() == 'parquet':
                df.to_parquet(output_path, index=False)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
            log.info(f"Recommendations exported successfully to {output_path}")
            
        except Exception as e:
            raise BookRecommentorException(e, sys) from e
            
    def generate_daily_recommendations(self, user_ids: List[int], 
                                     output_dir: str, k: int = 10) -> str:
        """Generate daily recommendations and save to timestamped file"""
        try:
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"recommendations_{timestamp}.csv")
            
            log.info(f"Generating daily recommendations for {len(user_ids)} users")
            
            recommendations = self.process_user_batch(user_ids, k=k)
            self.export_recommendations(recommendations, output_file)
            
            log.info(f"Daily recommendations generated: {output_file}")
            return output_file
            
        except Exception as e:
            raise BookRecommentorException(e, sys) from e


def run_batch_processing(user_ids: List[int], output_path: str, 
                        k: int = 10, max_workers: int = 4) -> None:
    """Convenience function to run batch processing"""
    try:
        pipeline = BatchProcessingPipeline(max_workers=max_workers)
        recommendations = pipeline.process_user_batch(user_ids, k=k)
        pipeline.export_recommendations(recommendations, output_path)
    except Exception as e:
        raise BookRecommentorException(e, sys) from e