"""
Production-grade Training Pipeline for Book Recommendation System
Implements hybrid approach (content-based + collaborative filtering)
"""
import sys
from typing import Optional, Tuple
from src.exception.custom_exception import BookRecommentorException
from src.logger import GLOBAL_LOGGER as log
from src.components.data_ingestion import DataIngestion
from src.components.data_validation import DataValidation
from src.components.data_transformation import DataTransformation
from src.components.model_trainer import ModelTrainer
from src.entity.config_entity import (
    TrainingPipelineConfig, DataIngestionConfig, DataValidationConfig,
    DataTransformationConfig, ModelTrainerConfig
)
from src.entity.artifacts_entity import (
    DataIngestionArtifact, DataValidationArtifact, 
    DataTransformationArtifact, ModelTrainerArtifact
)


class TrainingPipeline:
    """Production training pipeline for hybrid book recommendation system"""
    
    def __init__(self, training_pipeline_config: Optional[TrainingPipelineConfig] = None):
        self.training_pipeline_config = training_pipeline_config or TrainingPipelineConfig()
        
    def start_data_ingestion(self) -> DataIngestionArtifact:
        """Execute data ingestion stage"""
        try:
            log.info("Starting data ingestion stage")
            data_ingestion_config = DataIngestionConfig(self.training_pipeline_config)
            data_ingestion = DataIngestion(data_ingestion_config)
            data_ingestion_artifact = data_ingestion.initiate_data_ingestion()
            log.info("Data ingestion completed successfully")
            return data_ingestion_artifact
        except Exception as e:
            raise BookRecommentorException(e, sys) from e
            
    def start_data_validation(self, data_ingestion_artifact: DataIngestionArtifact) -> DataValidationArtifact:
        """Execute data validation stage"""
        try:
            log.info("Starting data validation stage")
            data_validation_config = DataValidationConfig(self.training_pipeline_config)
            data_validation = DataValidation(data_ingestion_artifact, data_validation_config)
            data_validation_artifact = data_validation.initiate_data_validation()
            log.info("Data validation completed successfully")
            return data_validation_artifact
        except Exception as e:
            raise BookRecommentorException(e, sys) from e
            
    def start_data_transformation(self, data_validation_artifact: DataValidationArtifact) -> DataTransformationArtifact:
        """Execute data transformation stage"""
        try:
            log.info("Starting data transformation stage")
            data_transformation_config = DataTransformationConfig(self.training_pipeline_config)
            data_transformation = DataTransformation(data_validation_artifact, data_transformation_config)
            data_transformation_artifact = data_transformation.initiate_data_transformation()
            log.info("Data transformation completed successfully")
            return data_transformation_artifact
        except Exception as e:
            raise BookRecommentorException(e, sys) from e
            
    def start_model_trainer(self, data_transformation_artifact: DataTransformationArtifact) -> ModelTrainerArtifact:
        """Execute model training stage"""
        try:
            log.info("Starting model training stage")
            model_trainer_config = ModelTrainerConfig(self.training_pipeline_config)
            model_trainer = ModelTrainer(data_transformation_artifact, model_trainer_config)
            model_trainer_artifact = model_trainer.initiate_model_trainer()
            log.info("Model training completed successfully")
            return model_trainer_artifact
        except Exception as e:
            raise BookRecommentorException(e, sys) from e
            
    def run_pipeline(self) -> ModelTrainerArtifact:
        """Execute complete training pipeline"""
        try:
            log.info(f"Starting training pipeline: {self.training_pipeline_config.pipeline_name}")
            
            # Execute pipeline stages
            data_ingestion_artifact = self.start_data_ingestion()
            data_validation_artifact = self.start_data_validation(data_ingestion_artifact)
            data_transformation_artifact = self.start_data_transformation(data_validation_artifact)
            model_trainer_artifact = self.start_model_trainer(data_transformation_artifact)
            
            log.info("Training pipeline completed successfully!")
            return model_trainer_artifact
            
        except Exception as e:
            raise BookRecommentorException(e, sys) from e


def run_training_pipeline() -> ModelTrainerArtifact:
    """Convenience function to run the training pipeline"""
    try:
        training_pipeline = TrainingPipeline()
        return training_pipeline.run_pipeline()
    except Exception as e:
        raise BookRecommentorException(e, sys) from e