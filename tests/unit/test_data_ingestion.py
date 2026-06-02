import pytest
import pandas as pd
import os
from unittest.mock import patch, Mock, MagicMock
from src.components.data_ingestion import DataIngestion
from src.exception.custom_exception import BookRecommentorException


class TestDataIngestion:
    
    def test_init(self, data_ingestion_config, mock_logger):
        """Test DataIngestion initialization"""
        with patch('src.components.data_ingestion.log', mock_logger):
            data_ingestion = DataIngestion(data_ingestion_config)
            assert data_ingestion.data_ingestion_config == data_ingestion_config
            mock_logger.info.assert_called_once()

    @patch('src.components.data_ingestion.read_csv')
    def test_export_data_into_dataframe(self, mock_read_csv, data_ingestion_config, 
                                      sample_ratings_data, sample_books_data, mock_logger):
        """Test data export into dataframe"""
        mock_read_csv.side_effect = [sample_ratings_data, sample_books_data]
        
        with patch('src.components.data_ingestion.log', mock_logger):
            data_ingestion = DataIngestion(data_ingestion_config)
            ratings_df, books_df = data_ingestion.export_data_into_dataframe()
            
            assert ratings_df.equals(sample_ratings_data)
            assert books_df.equals(sample_books_data)
            assert mock_read_csv.call_count == 2

    @patch('src.components.data_ingestion.os.makedirs')
    @patch('src.components.data_ingestion.read_csv')
    def test_export_data_into_feature_store(self, mock_read_csv, mock_makedirs, 
                                          data_ingestion_config, sample_ratings_data, 
                                          sample_books_data, mock_logger):
        """Test data export into feature store"""
        mock_read_csv.side_effect = [sample_ratings_data, sample_books_data]
        
        with patch('src.components.data_ingestion.log', mock_logger):
            with patch.object(pd.DataFrame, 'to_csv') as mock_to_csv:
                data_ingestion = DataIngestion(data_ingestion_config)
                data_ingestion.export_data_into_feature_store()
                
                assert mock_to_csv.call_count == 2
                mock_makedirs.assert_called()

    def test_dropped_dataframe(self, data_ingestion_config, sample_books_data, mock_logger):
        """Test dropping unnecessary columns"""
        with patch('src.components.data_ingestion.log', mock_logger):
            with patch('src.components.data_ingestion.drop_columns') as mock_drop:
                expected_df = sample_books_data.drop(['Image-URL-S', 'Image-URL-M', 'Image-URL-L'], axis=1)
                mock_drop.return_value = expected_df
                
                data_ingestion = DataIngestion(data_ingestion_config)
                result = data_ingestion.dropped_dataframe(sample_books_data)
                
                mock_drop.assert_called_once()
                assert result.equals(expected_df)

    def test_filter_data(self, data_ingestion_config, mock_logger):
        """Test data filtering logic"""
        # Create test data with users having >50 ratings and books with >20 ratings
        ratings_data = pd.DataFrame({
            'User-ID': [1] * 60 + [2] * 30,  # User 1 has 60 ratings, User 2 has 30
            'ISBN': ['book1'] * 25 + ['book2'] * 25 + ['book3'] * 10 + ['book1'] * 30,
            'Book-Rating': [5] * 90
        })
        
        books_data = pd.DataFrame({
            'ISBN': ['book1', 'book2', 'book3'],
            'Book-Title': ['Title1', 'Title2', 'Title3']
        })
        
        with patch('src.components.data_ingestion.log', mock_logger):
            data_ingestion = DataIngestion(data_ingestion_config)
            filtered_ratings, filtered_books = data_ingestion.filter_data(ratings_data, books_data)
            
            # Should only include User 1 (>50 ratings) and books with >20 ratings
            assert 2 not in filtered_ratings['User-ID'].values  # User 2 filtered out
            assert 'book3' not in filtered_ratings['ISBN'].values  # Book3 filtered out

    @patch('src.components.data_ingestion.DataIngestion.export_data_into_feature_store')
    @patch('src.components.data_ingestion.DataIngestion.export_data_to_ingested_artifact')
    def test_initiate_data_ingestion(self, mock_export_ingested, mock_export_feature, 
                                   data_ingestion_config, mock_logger):
        """Test complete data ingestion process"""
        with patch('src.components.data_ingestion.log', mock_logger):
            data_ingestion = DataIngestion(data_ingestion_config)
            artifact = data_ingestion.initiate_data_ingestion()
            
            mock_export_feature.assert_called_once()
            mock_export_ingested.assert_called_once()
            assert artifact.trained_books_file_path == data_ingestion_config.training_books_file_path
            assert artifact.trained_ratings_file_path == data_ingestion_config.training_ratings_file_path

    def test_exception_handling(self, data_ingestion_config):
        """Test exception handling in DataIngestion"""
        with patch('src.components.data_ingestion.read_csv', side_effect=Exception("Test error")):
            with patch('src.components.data_ingestion.log'):
                data_ingestion = DataIngestion(data_ingestion_config)
                with pytest.raises(BookRecommentorException):
                    data_ingestion.export_data_into_dataframe()