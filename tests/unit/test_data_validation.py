import pytest
import pandas as pd
import os
from unittest.mock import patch, Mock, MagicMock
from src.components.data_validation import DataValidation
from src.exception.custom_exception import BookRecommentorException


class TestDataValidation:
    
    def test_init(self, data_ingestion_artifact, data_validation_config, mock_schema_config, mock_logger):
        """Test DataValidation initialization"""
        with patch('src.components.data_validation.read_yaml', return_value=mock_schema_config):
            with patch('src.components.data_validation.log', mock_logger):
                data_validation = DataValidation(data_ingestion_artifact, data_validation_config)
                assert data_validation.data_ingestion_artifact == data_ingestion_artifact
                assert data_validation.data_validation_config == data_validation_config

    @patch('src.components.data_validation.read_csv')
    def test_read_data(self, mock_read_csv, sample_ratings_data):
        """Test static read_data method"""
        mock_read_csv.return_value = sample_ratings_data
        result = DataValidation.read_data("test_path.csv")
        assert result.equals(sample_ratings_data)
        mock_read_csv.assert_called_once_with("test_path.csv")

    def test_validate_number_of_columns_success(self, data_ingestion_artifact, data_validation_config, 
                                              sample_ratings_data, sample_books_data, mock_logger):
        """Test successful column validation"""
        schema_config = {
            "ratings_columns": ["User-ID", "ISBN", "Book-Rating"],
            "books_columns": ["ISBN", "Book-Title", "Book-Author", "Year-Of-Publication", "Publisher", 
                            "Image-URL-S", "Image-URL-M", "Image-URL-L"]
        }
        
        with patch('src.components.data_validation.read_yaml', return_value=schema_config):
            with patch('src.components.data_validation.log', mock_logger):
                data_validation = DataValidation(data_ingestion_artifact, data_validation_config)
                result = data_validation.validate_number_of_columns(sample_ratings_data, sample_books_data)
                assert result is True

    def test_validate_number_of_columns_failure(self, data_ingestion_artifact, data_validation_config, 
                                              sample_ratings_data, sample_books_data, mock_logger):
        """Test failed column validation"""
        schema_config = {
            "ratings_columns": ["User-ID", "ISBN"],  # Missing Book-Rating
            "books_columns": ["ISBN", "Book-Title"]  # Missing other columns
        }
        
        with patch('src.components.data_validation.read_yaml', return_value=schema_config):
            with patch('src.components.data_validation.log', mock_logger):
                data_validation = DataValidation(data_ingestion_artifact, data_validation_config)
                result = data_validation.validate_number_of_columns(sample_ratings_data, sample_books_data)
                assert result is False

    def test_numerical_column_validation_success(self, data_ingestion_artifact, data_validation_config, 
                                               sample_ratings_data, sample_books_data, mock_logger):
        """Test successful numerical column validation"""
        schema_config = {
            "numerical_ratings_columns": ["User-ID", "Book-Rating"],
            "numerical_books_columns": ["Year-Of-Publication"]
        }
        
        with patch('src.components.data_validation.read_yaml', return_value=schema_config):
            with patch('src.components.data_validation.log', mock_logger):
                data_validation = DataValidation(data_ingestion_artifact, data_validation_config)
                result = data_validation.numerical_column_validation(sample_ratings_data, sample_books_data)
                assert result is True

    def test_numerical_column_validation_failure(self, data_ingestion_artifact, data_validation_config, 
                                               mock_logger):
        """Test failed numerical column validation"""
        # Create data with non-numeric values
        ratings_data = pd.DataFrame({
            'User-ID': ['a', 'b', 'c'],  # Non-numeric
            'ISBN': ['123', '456', '789'],
            'Book-Rating': [5, 4, 3]
        })
        
        books_data = pd.DataFrame({
            'ISBN': ['123', '456', '789'],
            'Year-Of-Publication': ['invalid', 'data', 'here']  # Non-numeric
        })
        
        schema_config = {
            "numerical_ratings_columns": ["User-ID", "Book-Rating"],
            "numerical_books_columns": ["Year-Of-Publication"]
        }
        
        with patch('src.components.data_validation.read_yaml', return_value=schema_config):
            with patch('src.components.data_validation.log', mock_logger):
                data_validation = DataValidation(data_ingestion_artifact, data_validation_config)
                result = data_validation.numerical_column_validation(ratings_data, books_data)
                assert result is False

    @patch('src.components.data_validation.write_yaml_file')
    @patch('src.components.data_validation.os.makedirs')
    def test_data_drift_detection(self, mock_makedirs, mock_write_yaml, data_ingestion_artifact, 
                                data_validation_config, sample_ratings_data, sample_books_data, mock_logger):
        """Test data drift detection"""
        schema_config = {
            "numerical_ratings_columns": ["User-ID", "Book-Rating"],
            "numerical_books_columns": ["Year-Of-Publication"]
        }
        
        with patch('src.components.data_validation.read_yaml', return_value=schema_config):
            with patch('src.components.data_validation.log', mock_logger):
                data_validation = DataValidation(data_ingestion_artifact, data_validation_config)
                data_validation.data_drift_detection(sample_ratings_data, sample_books_data)
                
                mock_makedirs.assert_called_once()
                mock_write_yaml.assert_called_once()

    @patch('src.components.data_validation.DataValidation.read_data')
    @patch('src.components.data_validation.os.makedirs')
    def test_initiate_data_validation_success(self, mock_makedirs, mock_read_data, 
                                            data_ingestion_artifact, data_validation_config, 
                                            sample_ratings_data, sample_books_data, mock_logger):
        """Test successful data validation initiation"""
        mock_read_data.side_effect = [sample_ratings_data, sample_books_data]
        
        schema_config = {
            "ratings_columns": ["User-ID", "ISBN", "Book-Rating"],
            "books_columns": ["ISBN", "Book-Title", "Book-Author", "Year-Of-Publication", "Publisher", 
                            "Image-URL-S", "Image-URL-M", "Image-URL-L"],
            "numerical_ratings_columns": ["User-ID", "Book-Rating"],
            "numerical_books_columns": ["Year-Of-Publication"]
        }
        
        with patch('src.components.data_validation.read_yaml', return_value=schema_config):
            with patch('src.components.data_validation.log', mock_logger):
                with patch.object(pd.DataFrame, 'to_csv') as mock_to_csv:
                    with patch('src.components.data_validation.write_yaml_file'):
                        data_validation = DataValidation(data_ingestion_artifact, data_validation_config)
                        artifact = data_validation.initiate_data_validation()
                        
                        assert artifact.validation_status is True
                        assert artifact.valid_train_books_file_path is not None
                        assert artifact.valid_train_ratings_file_path is not None
                        assert mock_to_csv.call_count == 2

    def test_exception_handling(self, data_ingestion_artifact, data_validation_config):
        """Test exception handling in DataValidation"""
        with patch('src.components.data_validation.read_yaml', side_effect=Exception("Test error")):
            with pytest.raises(BookRecommentorException):
                DataValidation(data_ingestion_artifact, data_validation_config)