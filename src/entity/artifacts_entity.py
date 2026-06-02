from dataclasses import dataclass


@dataclass
class DataIngestionArtifact:
    trained_books_file_path:str
    trained_ratings_file_path:str

@dataclass
class DataValidationArtifact:
    validation_status: bool
    valid_train_books_file_path: str
    valid_train_ratings_file_path: str
    invalid_train_books_file_path: str
    invalid_train_ratings_file_path: str
    drift_report_file_path: str
    
@dataclass
class DataTransformationArtifact:
    transformed_object_file_path:str
    transformed_content_filtering_matrix_file_path:str
    transformed_collaborative_filtering_matrix_file_path:str
    transformed_merged_data_file_path:str
    
@dataclass
class ClassificationMetricArtifact:
    f1_score: float
    precision_score: float
    recall_score: float
    
@dataclass
class ModelTrainerArtifact:
    trained_model_file_path:str
    train_metric_artifact: ClassificationMetricArtifact
    test_metric_artifact: ClassificationMetricArtifact
    

    