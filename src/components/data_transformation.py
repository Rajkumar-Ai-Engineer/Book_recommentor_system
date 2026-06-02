import os 
import sys 
from src.exception.custom_exception import BookRecommentorException
from src.logger import GLOBAL_LOGGER as log
import pandas as pd

from src.utils.main_utils.utils import read_csv,save_numpy_array_data, save_object
from src.entity.config_entity import DataTransformationConfig
from src.entity.artifacts_entity import DataValidationArtifact,DataTransformationArtifact 

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer 
from scipy.sparse import csr_matrix


class DataTransformation:
    def __init__(self,data_validation_artifact:DataValidationArtifact,data_transformation_config:DataTransformationConfig):
        try:
            log.info(f"{'>>'*20} Data Transformation {'<<'*20}")
            self.data_validation_artifact=data_validation_artifact
            self.data_transformation_config=data_transformation_config
        except Exception as e:
            log.error("Error occured in Data Transformation class")
            raise BookRecommentorException(e,sys)
        
    @staticmethod
    def read_data(file_path:str):
        return read_csv(file_path)
    
    def get_preprocessor_object(self):
        try:
            tfidf_vectorizer = TfidfVectorizer(stop_words='english')
            preprocessor = Pipeline([
                ("tfidf_vectorizer", tfidf_vectorizer)
            ])
            return preprocessor
        except Exception as e:
            log.error("Error in getting preprocessor object")
            raise BookRecommentorException(e,sys)
        
    def merging_data(self,books_df,ratings_df):
        try:
            merged_df = pd.merge(ratings_df, books_df, on='ISBN')
            return merged_df
        except Exception as e:
            log.error("Error in merging data")
            raise BookRecommentorException(e,sys)
        
    def converting_to_sparse_matrix(self,preprocessor,merged_df):
        try:
            content_filtering_matrix = preprocessor.fit_transform(merged_df['Book-Title'] + " " + merged_df['Book-Author'] + " " + merged_df['Publisher'])
            collaborative_filtering_matrix = csr_matrix(merged_df.pivot_table(index='ISBN', columns='User-ID', values='Book-Rating').fillna(0).values)
            return content_filtering_matrix, collaborative_filtering_matrix
        except Exception as e:
            log.error("Error in converting to sparse matrix")
            raise BookRecommentorException(e,sys)
        
    def initiate_data_transformation(self):
        try:
            validated_ratings_file_path = self.data_validation_artifact.valid_train_ratings_file_path
            validated_books_file_path = self.data_validation_artifact.valid_train_books_file_path
            ratings_df = DataTransformation.read_data(validated_ratings_file_path)
            books_df = DataTransformation.read_data(validated_books_file_path)
            preprocessor = self.get_preprocessor_object()
            merged_df = self.merging_data(books_df, ratings_df)
            content_filtering_matrix, collaborative_filtering_matrix = self.converting_to_sparse_matrix(preprocessor, merged_df)
            
            save_numpy_array_data(self.data_transformation_config.content_filtering_matrix_file_path, content_filtering_matrix)
            save_numpy_array_data(self.data_transformation_config.collaborative_filtering_matrix_file_path, collaborative_filtering_matrix)
            save_object(self.data_transformation_config.preprocessing_object_file_path, preprocessor)
            
            # Save merged data for model training
            merged_df.to_csv(self.data_transformation_config.merged_data_file_path, index=False)
            log.info(f"Merged data saved at {self.data_transformation_config.merged_data_file_path}")
            log.info("Initiated data transformation successfully")
            data_transformation_artifact = DataTransformationArtifact(
                transformed_object_file_path=self.data_transformation_config.preprocessing_object_file_path,
                transformed_content_filtering_matrix_file_path=self.data_transformation_config.content_filtering_matrix_file_path,
                transformed_collaborative_filtering_matrix_file_path=self.data_transformation_config.collaborative_filtering_matrix_file_path,
                transformed_merged_data_file_path=self.data_transformation_config.merged_data_file_path
            )
            return data_transformation_artifact
        except Exception as e:
            log.error("Error in initiating data transformation")
            raise BookRecommentorException(e,sys)
        
        
    