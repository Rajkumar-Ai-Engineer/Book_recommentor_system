"""Test utilities for common testing functions"""
import pandas as pd
import numpy as np
import os
import tempfile
from unittest.mock import Mock, patch
from contextlib import contextmanager


class TestDataGenerator:
    """Generate test data for various scenarios"""
    
    @staticmethod
    def create_sample_ratings(num_users=100, num_books=50, num_ratings=1000):
        """Create sample ratings data"""
        np.random.seed(42)
        user_ids = np.random.choice(range(1, num_users + 1), num_ratings)
        book_isbns = np.random.choice([f"book_{i}" for i in range(1, num_books + 1)], num_ratings)
        ratings = np.random.choice([1, 2, 3, 4, 5], num_ratings)
        
        return pd.DataFrame({
            'User-ID': user_ids,
            'ISBN': book_isbns,
            'Book-Rating': ratings
        }).drop_duplicates(['User-ID', 'ISBN'])
    
    @staticmethod
    def create_sample_books(num_books=50):
        """Create sample books data"""
        return pd.DataFrame({
            'ISBN': [f"book_{i}" for i in range(1, num_books + 1)],
            'Book-Title': [f"Title {i}" for i in range(1, num_books + 1)],
            'Book-Author': [f"Author {i % 10}" for i in range(1, num_books + 1)],
            'Year-Of-Publication': np.random.choice(range(1990, 2024), num_books),
            'Publisher': [f"Publisher {i % 5}" for i in range(1, num_books + 1)],
            'Image-URL-S': [f"url_s_{i}" for i in range(1, num_books + 1)],
            'Image-URL-M': [f"url_m_{i}" for i in range(1, num_books + 1)],
            'Image-URL-L': [f"url_l_{i}" for i in range(1, num_books + 1)]
        })
    
    @staticmethod
    def create_filtered_data():
        """Create data that passes filtering criteria"""
        # Users with >50 ratings, books with >20 ratings
        ratings_data = []
        
        # Create 3 active users with >50 ratings each
        for user_id in [1, 2, 3]:
            for book_id in range(1, 26):  # 25 books each
                ratings_data.append({
                    'User-ID': user_id,
                    'ISBN': f"book_{book_id}",
                    'Book-Rating': np.random.choice([3, 4, 5])
                })
        
        # Add more ratings to make books popular (>20 ratings each)
        for book_id in range(1, 26):
            for user_id in range(4, 10):  # Additional users
                ratings_data.append({
                    'User-ID': user_id,
                    'ISBN': f"book_{book_id}",
                    'Book-Rating': np.random.choice([3, 4, 5])
                })
        
        return pd.DataFrame(ratings_data)


class MockFileSystem:
    """Mock file system operations for testing"""
    
    @staticmethod
    @contextmanager
    def mock_file_operations():
        """Context manager for mocking file operations"""
        with patch('pandas.DataFrame.to_csv') as mock_to_csv, \
             patch('os.makedirs') as mock_makedirs, \
             patch('os.path.exists', return_value=True) as mock_exists:
            yield {
                'to_csv': mock_to_csv,
                'makedirs': mock_makedirs,
                'exists': mock_exists
            }


class MockLogger:
    """Mock logger for testing"""
    
    def __init__(self):
        self.info = Mock()
        self.error = Mock()
        self.warning = Mock()
        self.debug = Mock()


class AssertionHelpers:
    """Helper methods for common assertions"""
    
    @staticmethod
    def assert_dataframe_structure(df, expected_columns, min_rows=0):
        """Assert dataframe has expected structure"""
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == expected_columns
        assert len(df) >= min_rows
    
    @staticmethod
    def assert_file_created(file_path):
        """Assert file was created"""
        assert os.path.exists(file_path)
        assert os.path.getsize(file_path) > 0
    
    @staticmethod
    def assert_artifact_structure(artifact, expected_attributes):
        """Assert artifact has expected attributes"""
        for attr in expected_attributes:
            assert hasattr(artifact, attr)
            assert getattr(artifact, attr) is not None


def create_temp_csv_file(data, temp_dir, filename):
    """Create temporary CSV file with data"""
    file_path = os.path.join(temp_dir, filename)
    data.to_csv(file_path, index=False)
    return file_path


def mock_component_dependencies():
    """Mock common component dependencies"""
    return {
        'logger': MockLogger(),
        'read_csv': Mock(),
        'save_object': Mock(),
        'save_numpy_array_data': Mock(),
        'write_yaml_file': Mock()
    }