"""
Production-grade Prediction Pipeline for Book Recommendation System
Handles real-time inference using trained hybrid models
"""
import sys
import os
import pandas as pd
from typing import List, Dict, Optional, Tuple
from src.exception.custom_exception import BookRecommentorException
from src.logger import GLOBAL_LOGGER as log
from src.utils.main_utils.utils import load_object
from src.constants import training_pipeline


class PredictionPipeline:
    """Production prediction pipeline for book recommendations"""
    
    def __init__(self, model_path: Optional[str] = None, preprocessing_path: Optional[str] = None):
        try:
            # Load latest model if no path specified
            if model_path is None:
                model_path = self._get_latest_model_path()
            if preprocessing_path is None:
                preprocessing_path = self._get_latest_preprocessing_path()
                
            self.model = load_object(model_path)
            self.preprocessor = load_object(preprocessing_path) if preprocessing_path else None
            log.info(f"Prediction pipeline initialized with model: {model_path}")
            
        except Exception as e:
            raise BookRecommentorException(e, sys) from e
            
    def _get_latest_model_path(self) -> str:
        """Get path to the latest trained model"""
        try:
            artifacts_dir = training_pipeline.ARTIFACT_DIR
            if not os.path.exists(artifacts_dir):
                raise FileNotFoundError("No artifacts directory found")
                
            # Get latest timestamp folder
            folders = [f for f in os.listdir(artifacts_dir) if os.path.isdir(os.path.join(artifacts_dir, f))]
            if not folders:
                raise FileNotFoundError("No training artifacts found")
                
            latest_folder = max(folders)
            model_path = os.path.join(
                artifacts_dir, latest_folder, 
                training_pipeline.MODEL_TRAINER_DIR_NAME,
                training_pipeline.MODEL_TRAINER_TRAINED_MODEL_DIR,
                training_pipeline.MODEL_TRAINER_TRAINED_MODEL_NAME
            )
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model not found at: {model_path}")
                
            return model_path
            
        except Exception as e:
            raise BookRecommentorException(e, sys) from e
            
    def _get_latest_preprocessing_path(self) -> Optional[str]:
        """Get path to the latest preprocessing object"""
        try:
            artifacts_dir = training_pipeline.ARTIFACT_DIR
            folders = [f for f in os.listdir(artifacts_dir) if os.path.isdir(os.path.join(artifacts_dir, f))]
            if not folders:
                return None
                
            latest_folder = max(folders)
            preprocessing_path = os.path.join(
                artifacts_dir, latest_folder,
                training_pipeline.DATA_TRANSFORMATION_DIR_NAME,
                training_pipeline.DATA_TRANSFORMATION_TRANSFORMED_OBJECT_DIR,
                training_pipeline.DATA_TRANSFORMATION_OBJECT_FILE_NAME
            )
            
            return preprocessing_path if os.path.exists(preprocessing_path) else None
            
        except Exception as e:
            log.warning(f"Could not load preprocessing object: {e}")
            return None
            
    def predict(self, user_id: int, k: int = 10) -> List[Dict]:
        """Generate top-k book recommendations for a user"""
        try:
            log.info(f"Generating recommendations for user {user_id}")
            
            # Use model to predict recommendations
            recommendations = self.model.recommend_books(user_id, k=k)
            
            log.info(f"Generated {len(recommendations)} recommendations for user {user_id}")
            return recommendations
            
        except Exception as e:
            raise BookRecommentorException(e, sys) from e
            
    def predict_batch(self, user_ids: List[int], k: int = 10) -> Dict[int, List[Dict]]:
        """Generate recommendations for multiple users"""
        try:
            log.info(f"Generating batch recommendations for {len(user_ids)} users")
            
            results = {}
            for user_id in user_ids:
                results[user_id] = self.predict(user_id, k)
                
            log.info("Batch prediction completed")
            return results
            
        except Exception as e:
            raise BookRecommentorException(e, sys) from e
            
    def get_similar_books(self, book_id: str, k: int = 10) -> List[Dict]:
        """Get similar books using content-based filtering"""
        try:
            log.info(f"Finding similar books for book {book_id}")
            
            similar_books = self.model.get_similar_books(book_id, k=k)
            
            log.info(f"Found {len(similar_books)} similar books")
            return similar_books
            
        except Exception as e:
            raise BookRecommentorException(e, sys) from e


def predict_recommendations(user_id: int, k: int = 10) -> List[Dict]:
    """Convenience function for single user prediction"""
    try:
        pipeline = PredictionPipeline()
        return pipeline.predict(user_id, k)
    except Exception as e:
        raise BookRecommentorException(e, sys) from e