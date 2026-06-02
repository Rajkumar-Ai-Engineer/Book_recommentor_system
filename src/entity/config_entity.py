import os 
from datetime import datetime
from src.constants import training_pipeline

class TrainingPipelineConfig:
    def __init__(self,timestamp:datetime = datetime.now()):
        timestamp=timestamp.strftime("%m_%d_%Y_%H_%M_%S")
        self.pipeline_name=training_pipeline.PIPELINE_NAME
        self.artifact_name=training_pipeline.ARTIFACT_DIR
        self.artifact_dir=os.path.join(self.artifact_name,timestamp)
        self.timestamp: str=timestamp
        
class DataIngestionConfig:
    def __init__(self,training_pipeline_config:TrainingPipelineConfig):
        
        self.actual_ratings_file_path:str = training_pipeline.DATA_INGESTION_RATINGS_DATA_PATH
        self.actual_books_file_path:str = training_pipeline.DATA_INGESTION_BOOKS_DATA_PATH
        
        self.data_ingestion_dir:str = os.path.join(
            training_pipeline_config.artifact_dir,training_pipeline.DATA_INGESTION_DIR_NAME
        )
        self.feature_store_books_file_path:str = os.path.join(self.data_ingestion_dir,training_pipeline.DATA_INGESTION_FEATURE_STORE_DIR,training_pipeline.TRAIN_BOOKS_FILE_NAME)
        self.feature_store_ratings_file_path:str = os.path.join(self.data_ingestion_dir,training_pipeline.DATA_INGESTION_FEATURE_STORE_DIR,training_pipeline.TRAIN_RATINGS_FILE_NAME)
        
        self.training_books_file_path:str = os.path.join(self.data_ingestion_dir,training_pipeline.DATA_INGESTION_INGESTED_DIR,training_pipeline.TRAIN_BOOKS_FILE_NAME)
        self.training_ratings_file_path:str = os.path.join(self.data_ingestion_dir,training_pipeline.DATA_INGESTION_INGESTED_DIR,training_pipeline.TRAIN_RATINGS_FILE_NAME)
        
class DataValidationConfig:
    def __init__(self,training_pipeline_config:TrainingPipelineConfig):
        self.data_validation_dir:str = os.path.join(
            training_pipeline_config.artifact_dir,training_pipeline.DATA_VALIDATION_DIR_NAME
        )
        self.valid_dir:str = os.path.join(self.data_validation_dir,training_pipeline.DATA_VALIDATION_VALID_DIR)
        self.invalid_dir:str = os.path.join(self.data_validation_dir,training_pipeline.DATA_VALIDATION_INVALID_DIR)
        self.drift_report_dir:str = os.path.join(self.data_validation_dir,training_pipeline.DATA_VALIDATION_DRIFT_REPORT_DIR)
        self.drift_report_file_path:str = os.path.join(self.drift_report_dir,training_pipeline.DATA_VALIDATION_DRIFT_REPORT_FILE_NAME)
        self.valid_train_books_file_path:str = os.path.join(self.valid_dir,training_pipeline.TRAIN_BOOKS_FILE_NAME)
        self.valid_train_ratings_file_path:str = os.path.join(self.valid_dir,training_pipeline.TRAIN_RATINGS_FILE_NAME)
        self.invalid_train_books_file_path:str = os.path.join(self.invalid_dir,training_pipeline.TRAIN_BOOKS_FILE_NAME)
        self.invalid_train_ratings_file_path:str = os.path.join(self.invalid_dir,training_pipeline.TRAIN_RATINGS_FILE_NAME)
        
class DataTransformationConfig:
    def __init__(self,training_pipeline_config: TrainingPipelineConfig):
        self.data_transformation_dir:str = os.path.join(
            training_pipeline_config.artifact_dir,training_pipeline.DATA_TRANSFORMATION_DIR_NAME
        )
        self.transformed_dir:str = os.path.join(self.data_transformation_dir,training_pipeline.DATA_TRANSFORMATION_TRANSFORMED_DIR)
        self.transformed_object_dir:str = os.path.join(self.data_transformation_dir,training_pipeline.DATA_TRANSFORMATION_TRANSFORMED_OBJECT_DIR)
        self.content_filtering_matrix_file_path:str = os.path.join(self.transformed_dir,training_pipeline.DATA_TRANSFORMATION_CONTENT_FILTERING_MATRIX)
        self.collaborative_filtering_matrix_file_path:str = os.path.join(self.transformed_dir,training_pipeline.DATA_TRANSFORMATION_COLLABORATIVE_FILTERING_MATRIX)
        self.preprocessing_object_file_path:str = os.path.join(self.transformed_object_dir,training_pipeline.DATA_TRANSFORMATION_OBJECT_FILE_NAME)
        self.merged_data_file_path:str = os.path.join(self.transformed_dir,training_pipeline.DATA_TRANSFORMATION_MERGED_DATA_FILE_NAME)
        
class ModelTrainerConfig:
    def __init__(self,training_pipeline_config: TrainingPipelineConfig):
        self.model_trainer_dir:str = os.path.join(
            training_pipeline_config.artifact_dir,training_pipeline.MODEL_TRAINER_DIR_NAME
        )
        self.trained_model_dir:str = os.path.join(self.model_trainer_dir,training_pipeline.MODEL_TRAINER_TRAINED_MODEL_DIR)
        self.trained_model_file_path:str = os.path.join(self.trained_model_dir,training_pipeline.MODEL_TRAINER_TRAINED_MODEL_NAME)