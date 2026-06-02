import os 
import sys 
from src.exception.custom_exception import BookRecommentorException
from src.logger import GLOBAL_LOGGER as log 

from src.entity.config_entity import DataIngestionConfig
from src.entity.artifacts_entity import DataIngestionArtifact

from src.utils.main_utils.utils import read_csv,drop_columns,read_yaml


class DataIngestion:
    def __init__(self,data_ingestion_config:DataIngestionConfig):
        try:
            self.data_ingestion_config=data_ingestion_config
            log.info(f"{'>>'*20} Data Ingestion {'<<'*20}")
        except Exception as e:
            log.error("Error occured in Data Ingestion class")
            raise BookRecommentorException(e,sys)
        
    def export_data_into_dataframe(self):
        try:
            log.info("Exporting data into dataframe")
            ratings_data_frame = read_csv(file_path=self.data_ingestion_config.actual_ratings_file_path)
            books_data_frame = read_csv(file_path=self.data_ingestion_config.actual_books_file_path)
            log.info("Data exportation into dataframe completed successfully")
            return ratings_data_frame,books_data_frame
        except Exception as e:
            log.error("Error occured in export_data_into_dataframe method")
            raise BookRecommentorException(e,sys)
    
    def export_data_into_feature_store(self):
        try:
            log.info("Exporting data into feature store")
            ratings_data_frame,books_data_frame = self.export_data_into_dataframe()
            log.info("Exporting books and ratings")
            os.makedirs(os.path.dirname(self.data_ingestion_config.feature_store_ratings_file_path), exist_ok=True)
            os.makedirs(os.path.dirname(self.data_ingestion_config.feature_store_books_file_path), exist_ok=True)
            ratings_data_frame.to_csv(self.data_ingestion_config.feature_store_ratings_file_path,index=False,header=True)
            books_data_frame.to_csv(self.data_ingestion_config.feature_store_books_file_path,index=False,header=True)
            log.info("Data exportation into feature store completed successfully")
        except Exception as e:
            log.error("Error occured in export_data_into_feature_store method")
            raise BookRecommentorException(e,sys)
        
    def dropped_dataframe(self,books_dataframe):
        try:
            log.info("Dropping unnecessary columns from books dataframe")
            columns_to_drop = ["Image-URL-S", "Image-URL-M", "Image-URL-L"]
            dropped_books_dataframe = drop_columns(dataframe=books_dataframe,columns=columns_to_drop)
            log.info("Dropping unnecessary columns from books dataframe completed successfully")
            return dropped_books_dataframe
        except Exception as e:
            log.error("Error occured in dropped_dataframe method")
            raise BookRecommentorException(e,sys)
        
    def export_data_to_ingested_artifact(self):
        try:
            log.info("Exporting data into ingested artifact")
            ratings_data_frame,books_data_frame = self.export_data_into_dataframe()
            log.info("Exporting books and ratings")
            books_data_frame_dropped = self.dropped_dataframe(books_dataframe=books_data_frame)
            base_dir = os.path.dirname(self.data_ingestion_config.training_books_file_path)
            os.makedirs(base_dir, exist_ok=True)
            finalized_ratings_dataframe,finalize_book_dataframe = self.filter_data(ratings_dataframe=ratings_data_frame,books_dataframe=books_data_frame_dropped)
            finalized_ratings_dataframe.to_csv(self.data_ingestion_config.training_ratings_file_path,index=False,header=True)
            finalize_book_dataframe.to_csv(self.data_ingestion_config.training_books_file_path,index=False,header=True)
            log.info("Data exportation into ingested artifact completed successfully")
        except Exception as e:
            log.error("Error occured in export_data_to_ingested_artifact method")
            raise BookRecommentorException(e,sys)
        
    def filter_data(self,ratings_dataframe,books_dataframe):
        try:
            log.info("Filtering data for training and testing")
            ratings_dataframe = ratings_dataframe.drop_duplicates(["User-ID","ISBN"])
            books_dataframe = books_dataframe.drop_duplicates(["ISBN"])
            # Users who rated more than 50 books
            active_users = ratings_dataframe["User-ID"].value_counts()
            active_50_users = active_users[active_users > 50].index
            final_ratings_dataframe = ratings_dataframe[ratings_dataframe["User-ID"].isin(active_50_users)]
            
            # Books with more than 20 ratings
            popular_books = final_ratings_dataframe["ISBN"].value_counts()
            popular_20_books = popular_books[popular_books > 20].index
            finalized_ratings_dataframe = final_ratings_dataframe[final_ratings_dataframe["ISBN"].isin(popular_20_books)]
            log.info("Data filtering completed successfully")
            return finalized_ratings_dataframe, books_dataframe
        except Exception as e:
            log.error("Error occured in filter_data method")
            raise BookRecommentorException(e,sys)
        
    def initiate_data_ingestion(self)->DataIngestionArtifact:
        try:
            log.info("Initiating data ingestion")
            self.export_data_into_feature_store()
            self.export_data_to_ingested_artifact()
            data_ingestion_artifact = DataIngestionArtifact(
                trained_books_file_path=self.data_ingestion_config.training_books_file_path,
                trained_ratings_file_path=self.data_ingestion_config.training_ratings_file_path
            )
            log.info("Data ingestion completed successfully")
            return data_ingestion_artifact
        except Exception as e:
            log.error("Error occured in initiate_data_ingestion method")
            raise BookRecommentorException(e,sys)
    