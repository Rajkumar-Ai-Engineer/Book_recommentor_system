import os 

"""
defining common constant variable for training pipeline
"""
ARTIFACT_DIR: str = "Artifacts"
TRAIN_BOOKS_FILE_NAME: str = "train_books.csv"
TRAIN_RATINGS_FILE_NAME: str = "train_ratings.csv"
MODEL_FILE_NAME: str = "model.pkl"
PIPELINE_NAME: str = "book_recommendation_system"

SCHEMA_FILE_PATH = os.path.join("data_schema", "schema.yaml")


# 1. Data Ingestion
DATA_INGESTION_RATINGS_DATA_PATH: str = f"{os.getcwd()}/BookRecommentorSystemData/Ratings.csv"
DATA_INGESTION_BOOKS_DATA_PATH: str = f"{os.getcwd()}/BookRecommentorSystemData/Books.csv"
DATA_INGESTION_DIR_NAME: str = "data_ingestion"
DATA_INGESTION_FEATURE_STORE_DIR: str = "feature_store"
DATA_INGESTION_INGESTED_DIR: str = "ingested"

"""
Data Validation related constant start with DATA_VALIDATION VAR NAME
"""
DATA_VALIDATION_DIR_NAME: str = "data_validation"
DATA_VALIDATION_VALID_DIR: str = "validated"
DATA_VALIDATION_INVALID_DIR: str = "invalid"
DATA_VALIDATION_DRIFT_REPORT_DIR: str = "drift_report"
DATA_VALIDATION_DRIFT_REPORT_FILE_NAME: str = "report.yaml"

"""
Data Transfromation related constant start with DATA_TRANSFORMATION VAR NAME 
"""
DATA_TRANSFORMATION_DIR_NAME: str = "data_transformation"
DATA_TRANSFORMATION_TRANSFORMED_DIR: str = "transformed"
DATA_TRANSFORMATION_TRANSFORMED_OBJECT_DIR: str = "transformed_object"
DATA_TRANSFORMATION_CONTENT_FILTERING_MATRIX: str = "content.npz"
DATA_TRANSFORMATION_COLLABORATIVE_FILTERING_MATRIX: str = "collaborative.npz"
DATA_TRANSFORMATION_OBJECT_FILE_NAME: str = "preprocessing.pkl"
DATA_TRANSFORMATION_MERGED_DATA_FILE_NAME: str = "merged_data.csv"

""" 
Model Trainer related constant start with MODEL_TRAINER VAR NAME
"""
MODEL_TRAINER_DIR_NAME:str = "model_trainer"
MODEL_TRAINER_TRAINED_MODEL_DIR: str = "trained_model"
MODEL_TRAINER_TRAINED_MODEL_NAME: str = "model.pkl"
