import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, Mock, MagicMock
from scipy.sparse import csr_matrix
from src.components.data_transformation import DataTransformation
from src.exception.custom_exception import BookRecommentorException


class TestDataTransformation:
    
    def test_init(self, data_validation_artifact, data_transformation_config, mock_logger):
        """Test DataTransformation initialization"""
        with patch('src.components.data_transformation.log', mock_logger):
            data_transformation = DataTransformation(data_validation_artifact, data_transformation_config)
            assert data_transformation.data_validation_artifact == data_validation_artifact
            assert data_transformation.data_transformation_config == data_transformation_config

    @patch('src.components.data_transformation.read_csv')
    def test_read_data(self, mock_read_csv, sample_ratings_data):
        """Test static read_data method"""
        mock_read_csv.return_value = sample_ratings_data
        result = DataTransformation.read_data("test_path.csv")
        assert result.equals(sample_ratings_data)
        mock_read_csv.assert_called_once_with("test_path.csv")

    def test_get_preprocessor_object(self, data_validation_artifact, data_transformation_config, mock_logger):
        """Test preprocessor object creation"""
        with patch('src.components.data_transformation.log', mock_logger):
            data_transformation = DataTransformation(data_validation_artifact, data_transformation_config)
            preprocessor = data_transformation.get_preprocessor_object()
            
            assert preprocessor is not None
            assert len(preprocessor.steps) == 1
            assert preprocessor.steps[0][0] == "tfidf_vectorizer"

    def test_merging_data(self, data_validation_artifact, data_transformation_config, mock_logger):
        """Test data merging functionality"""
        books_df = pd.DataFrame({
            'ISBN': ['123', '456'],
            'Book-Title': ['Book A', 'Book B'],
            'Book-Author': ['Author A', 'Author B'],
            'Publisher': ['Pub A', 'Pub B']
        })
        
        ratings_df = pd.DataFrame({
            'User-ID': [1, 2],
            'ISBN': ['123', '456'],
            'Book-Rating': [5, 4]
        })
        
        with patch('src.components.data_transformation.log', mock_logger):
            data_transformation = DataTransformation(data_validation_artifact, data_transformation_config)
            merged_df = data_transformation.merging_data(books_df, ratings_df)
            
            assert len(merged_df) == 2
            assert 'User-ID' in merged_df.columns
            assert 'Book-Title' in merged_df.columns
            assert 'Book-Rating' in merged_df.columns

    def test_converting_to_sparse_matrix(self, data_validation_artifact, data_transformation_config, mock_logger):
        """Test sparse matrix conversion"""
        merged_df = pd.DataFrame({
            'ISBN': ['123', '456', '123'],
            'User-ID': [1, 2, 3],
            'Book-Rating': [5, 4, 3],
            'Book-Title': ['Book A', 'Book B', 'Book A'],
            'Book-Author': ['Author A', 'Author B', 'Author A'],
            'Publisher': ['Pub A', 'Pub B', 'Pub A']
        })
        
        with patch('src.components.data_transformation.log', mock_logger):
            data_transformation = DataTransformation(data_validation_artifact, data_transformation_config)
            preprocessor = data_transformation.get_preprocessor_object()
            
            content_matrix, collaborative_matrix = data_transformation.converting_to_sparse_matrix(
                preprocessor, merged_df
            )
            
            assert content_matrix is not None
            assert collaborative_matrix is not None
            assert hasattr(content_matrix, 'shape')
            assert hasattr(collaborative_matrix, 'shape')

    @patch('src.components.data_transformation.save_object')
    @patch('src.components.data_transformation.save_numpy_array_data')
    @patch('src.components.data_transformation.DataTransformation.read_data')
    def test_initiate_data_transformation(self, mock_read_data, mock_save_numpy, mock_save_object,
                                        data_validation_artifact, data_transformation_config, mock_logger):
        """Test complete data transformation process"""
        # Mock data
        ratings_df = pd.DataFrame({
            'User-ID': [1, 2, 3],
            'ISBN': ['123', '456', '789'],
            'Book-Rating': [5, 4, 3]
        })
        
        books_df = pd.DataFrame({
            'ISBN': ['123', '456', '789'],
            'Book-Title': ['Book A', 'Book B', 'Book C'],
            'Book-Author': ['Author A', 'Author B', 'Author C'],
            'Publisher': ['Pub A', 'Pub B', 'Pub C']
        })
        
        mock_read_data.side_effect = [ratings_df, books_df]
        
        with patch('src.components.data_transformation.log', mock_logger):
            with patch.object(pd.DataFrame, 'to_csv') as mock_to_csv:
                data_transformation = DataTransformation(data_validation_artifact, data_transformation_config)
                artifact = data_transformation.initiate_data_transformation()
                
                # Verify saves were called
                assert mock_save_numpy.call_count == 2
                mock_save_object.assert_called_once()
                mock_to_csv.assert_called_once()
                
                # Verify artifact
                assert artifact.transformed_object_file_path == data_transformation_config.preprocessing_object_file_path
                assert artifact.transformed_content_filtering_matrix_file_path == data_transformation_config.content_filtering_matrix_file_path
                assert artifact.transformed_collaborative_filtering_matrix_file_path == data_transformation_config.collaborative_filtering_matrix_file_path

    def test_exception_handling(self, data_validation_artifact, data_transformation_config):
        """Test exception handling in DataTransformation"""
        with patch('src.components.data_transformation.DataTransformation.read_data', 
                  side_effect=Exception("Test error")):
            with patch('src.components.data_transformation.log'):
                data_transformation = DataTransformation(data_validation_artifact, data_transformation_config)
                with pytest.raises(BookRecommentorException):
                    data_transformation.initiate_data_transformation()

    @patch('src.components.data_transformation.TfidfVectorizer')
    def test_preprocessor_with_mock_tfidf(self, mock_tfidf, data_validation_artifact, 
                                        data_transformation_config, mock_logger):
        """Test preprocessor creation with mocked TfidfVectorizer"""
        mock_vectorizer_instance = Mock()
        mock_tfidf.return_value = mock_vectorizer_instance
        
        with patch('src.components.data_transformation.log', mock_logger):
            data_transformation = DataTransformation(data_validation_artifact, data_transformation_config)
            preprocessor = data_transformation.get_preprocessor_object()
            
            mock_tfidf.assert_called_once_with(stop_words='english')
            assert preprocessor is not None