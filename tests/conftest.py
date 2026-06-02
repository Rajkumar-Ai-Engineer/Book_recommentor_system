import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from unittest.mock import Mock, patch
from src.entity.config_entity import DataIngestionConfig, DataValidationConfig, DataTransformationConfig
from src.entity.artifacts_entity import DataIngestionArtifact, DataValidationArtifact


@pytest.fixture
def sample_ratings_data():
    """Sample ratings data for testing"""
    return pd.DataFrame({
        'User-ID': [1, 2, 3, 1, 2],
        'ISBN': ['123', '456', '789', '456', '123'],
        'Book-Rating': [5, 4, 3, 2, 1]
    })


@pytest.fixture
def sample_books_data():
    """Sample books data for testing"""
    return pd.DataFrame({
        'ISBN': ['123', '456', '789'],
        'Book-Title': ['Book A', 'Book B', 'Book C'],
        'Book-Author': ['Author A', 'Author B', 'Author C'],
        'Year-Of-Publication': [2020, 2021, 2022],
        'Publisher': ['Pub A', 'Pub B', 'Pub C'],
        'Image-URL-S': ['url1', 'url2', 'url3'],
        'Image-URL-M': ['url1', 'url2', 'url3'],
        'Image-URL-L': ['url1', 'url2', 'url3']
    })


@pytest.fixture
def temp_dir():
    """Temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def data_ingestion_config(temp_dir):
    """Mock DataIngestionConfig"""
    from src.entity.config_entity import TrainingPipelineConfig
    training_config = TrainingPipelineConfig()
    training_config.artifact_dir = temp_dir
    return DataIngestionConfig(training_config)


@pytest.fixture
def data_validation_config(temp_dir):
    """Mock DataValidationConfig"""
    from src.entity.config_entity import TrainingPipelineConfig
    training_config = TrainingPipelineConfig()
    training_config.artifact_dir = temp_dir
    return DataValidationConfig(training_config)


@pytest.fixture
def data_transformation_config(temp_dir):
    """Mock DataTransformationConfig"""
    from src.entity.config_entity import TrainingPipelineConfig
    training_config = TrainingPipelineConfig()
    training_config.artifact_dir = temp_dir
    return DataTransformationConfig(training_config)


@pytest.fixture
def data_ingestion_artifact(temp_dir):
    """Mock DataIngestionArtifact"""
    return DataIngestionArtifact(
        trained_books_file_path=os.path.join(temp_dir, "books.csv"),
        trained_ratings_file_path=os.path.join(temp_dir, "ratings.csv")
    )


@pytest.fixture
def data_validation_artifact(temp_dir):
    """Mock DataValidationArtifact"""
    return DataValidationArtifact(
        validation_status=True,
        valid_train_books_file_path=os.path.join(temp_dir, "books.csv"),
        valid_train_ratings_file_path=os.path.join(temp_dir, "ratings.csv"),
        invalid_train_books_file_path=None,
        invalid_train_ratings_file_path=None,
        drift_report_file_path=os.path.join(temp_dir, "drift_report.yaml")
    )


@pytest.fixture
def mock_logger():
    """Mock logger for testing"""
    return Mock()


@pytest.fixture
def mock_schema_config():
    """Mock schema configuration"""
    return {
        "ratings_columns": ["User-ID", "ISBN", "Book-Rating"],
        "books_columns": ["ISBN", "Book-Title", "Book-Author", "Year-Of-Publication", "Publisher"],
        "numerical_ratings_columns": ["User-ID", "Book-Rating"],
        "numerical_books_columns": ["Year-Of-Publication"]
    }