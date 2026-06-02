import os 
import sys 
from src.exception.custom_exception import BookRecommentorException
from src.logger import GLOBAL_LOGGER as log
import pandas as pd
import numpy as np

from src.utils.main_utils.utils import read_csv, save_object, load_object, load_numpy_array_data
from src.utils.ml_utils.model.estimator import HybridRecommendationModel
from src.utils.ml_utils.metrics.recommentor_metrics import RecommendationMetrics, get_classification_metrics
from src.entity.config_entity import ModelTrainerConfig
from src.entity.artifacts_entity import ModelTrainerArtifact, DataTransformationArtifact, ClassificationMetricArtifact


class ModelTrainer:
    def __init__(self, data_transformation_artifact: DataTransformationArtifact, model_trainer_config: ModelTrainerConfig):
        try:
            self.data_transformation_artifact = data_transformation_artifact
            self.model_trainer_config = model_trainer_config
            log.info(f"{'>>'*20} Model Trainer {'<<'*20}")
        except Exception as e:
            log.error("Error in Model Trainer Init")
            raise BookRecommentorException(e, sys)
        
    @staticmethod
    def read_data(file_path:str):
        return read_csv(file_path)
    
    def load_transformed_data(self):
        """
        Load pre-computed matrices and data from transformation artifacts
        """
        try:
            log.info("Loading transformed data and matrices")
            
            # Load preprocessor object
            preprocessor = load_object(
                file_path=self.data_transformation_artifact.transformed_object_file_path
            )
            
            # Load pre-computed matrices
            content_matrix = load_numpy_array_data(
                self.data_transformation_artifact.transformed_content_filtering_matrix_file_path
            )
            
            collaborative_matrix = load_numpy_array_data(
                self.data_transformation_artifact.transformed_collaborative_filtering_matrix_file_path
            )
            
            log.info(f"Content matrix shape: {content_matrix.shape}")
            log.info(f"Collaborative matrix shape: {collaborative_matrix.shape}")
            
            return preprocessor, content_matrix, collaborative_matrix
            
        except Exception as e:
            log.error("Error in loading transformed data")
            raise BookRecommentorException(e, sys)
    
    def load_transformed_merged_data(self):
        """
        Load the transformed merged data from data transformation artifact
        This ensures we use the same validated and processed data that was used for matrix creation
        """
        try:
            log.info("Loading transformed merged data for training")
            merged_df = ModelTrainer.read_data(
                self.data_transformation_artifact.transformed_merged_data_file_path
            )
            log.info(f"Transformed merged data shape: {merged_df.shape}")
            log.info("Using validated and transformed data for model training")
            return merged_df
            
        except Exception as e:
            log.error("Error in loading transformed merged data")
            raise BookRecommentorException(e, sys)
    
    def train_model(self, preprocessor, content_matrix, collaborative_matrix, merged_df):
        """
        Train the hybrid model using pre-computed matrices
        """
        try:
            log.info("Training hybrid recommendation model with pre-computed matrices")
            
            # Initialize model
            model = HybridRecommendationModel()
            
            # Load pre-computed data into model
            model.load_transformed_data(
                content_matrix=content_matrix,
                collaborative_matrix=collaborative_matrix,
                preprocessor=preprocessor,
                merged_data=merged_df,
                books_data=None  # Not needed since we have merged data
            )
            
            # Log model information
            model_info = model.get_model_info()
            log.info(f"Model training completed: {model_info}")
            
            return model
            
        except Exception as e:
            log.error("Error in training model")
            raise BookRecommentorException(e, sys)
    
    def evaluate_model(self, model, merged_df):
        """
        Evaluate the trained model
        """
        try:
            log.info("Evaluating model performance")
            
            # Simple evaluation using sample data
            sample_size = min(1000, len(merged_df))
            test_sample = merged_df.sample(sample_size, random_state=42)
            
            successful_recommendations = 0
            total_tests = 0
            
            # Test recommendations for sample books
            unique_books = test_sample['Book-Title'].unique()[:50]  # Test 50 books
            
            for book_title in unique_books:
                try:
                    result = model.recommend(book_title, top_k=5)
                    if 'error' not in result and len(result['recommendations']) > 0:
                        successful_recommendations += 1
                    total_tests += 1
                except:
                    total_tests += 1
                    continue
            
            # Calculate success rate as proxy metrics
            success_rate = successful_recommendations / total_tests if total_tests > 0 else 0.0
            
            log.info(f"Model evaluation: {successful_recommendations}/{total_tests} successful recommendations")
            log.info(f"Success rate: {success_rate:.4f}")
            
            # Create metrics artifacts
            train_metrics = ClassificationMetricArtifact(
                f1_score=success_rate,
                precision_score=success_rate,
                recall_score=success_rate
            )
            
            test_metrics = ClassificationMetricArtifact(
                f1_score=success_rate,
                precision_score=success_rate,
                recall_score=success_rate
            )
            
            return train_metrics, test_metrics
            
        except Exception as e:
            log.error("Error in evaluating model")
            raise BookRecommentorException(e, sys)
    
    def save_trained_model(self, model):
        """
        Save the trained model
        """
        try:
            log.info("Saving trained model")
            
            # Create model directory
            os.makedirs(
                os.path.dirname(self.model_trainer_config.trained_model_file_path),
                exist_ok=True
            )
            
            # Save model
            save_object(
                file_path=self.model_trainer_config.trained_model_file_path,
                obj=model
            )
            
            log.info(f"Model saved at: {self.model_trainer_config.trained_model_file_path}")
            
        except Exception as e:
            log.error("Error in saving trained model")
            raise BookRecommentorException(e, sys)
    
    def test_model_predictions(self, model):
        """
        Test model with sample predictions
        """
        try:
            log.info("Testing model with sample predictions")
            
            # Test with sample books
            test_books = ["Harry Potter", "The Great Gatsby", "Pride and Prejudice"]
            
            for book_title in test_books:
                try:
                    result = model.recommend(book_title, top_k=3)
                    if 'error' not in result:
                        log.info(f"✓ '{book_title}': {len(result['recommendations'])} recommendations")
                    else:
                        log.warning(f"✗ '{book_title}': {result['error']}")
                except Exception as e:
                    log.warning(f"✗ '{book_title}': Error - {str(e)}")
            
        except Exception as e:
            log.error("Error in testing model predictions")
            raise BookRecommentorException(e, sys)
    
    def initiate_model_trainer(self) -> ModelTrainerArtifact:
        """
        Initiate model training process using pre-computed matrices
        """
        try:
            log.info("Initiating model training with pre-computed matrices")
            
            # Load pre-computed matrices from transformation
            preprocessor, content_matrix, collaborative_matrix = self.load_transformed_data()
            
            # Load transformed merged data (validated and processed)
            merged_df = self.load_transformed_merged_data()
            
            # Train model using pre-computed matrices
            model = self.train_model(
                preprocessor, content_matrix, collaborative_matrix, merged_df
            )
            
            # Evaluate model
            train_metrics, test_metrics = self.evaluate_model(model, merged_df)
            
            # Test sample predictions
            self.test_model_predictions(model)
            
            # Save trained model
            self.save_trained_model(model)
            
            # Create model trainer artifact
            model_trainer_artifact = ModelTrainerArtifact(
                trained_model_file_path=self.model_trainer_config.trained_model_file_path,
                train_metric_artifact=train_metrics,
                test_metric_artifact=test_metrics
            )
            
            log.info("Model training completed successfully")
            log.info(f"Model metrics - Precision: {test_metrics.precision_score:.4f}, "
                    f"Recall: {test_metrics.recall_score:.4f}, F1: {test_metrics.f1_score:.4f}")
            
            return model_trainer_artifact
            
        except Exception as e:
            log.error("Error in initiating model training")
            raise BookRecommentorException(e, sys)