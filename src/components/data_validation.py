import os 
import sys 
from src.exception.custom_exception import BookRecommentorException
from src.logger import GLOBAL_LOGGER as log
import pandas as pd

from src.utils.main_utils.utils import read_yaml,write_yaml_file,read_csv
from src.constants.training_pipeline import SCHEMA_FILE_PATH
from src.entity.config_entity import DataValidationConfig
from src.entity.artifacts_entity import DataIngestionArtifact,DataValidationArtifact
from scipy.stats import ks_2samp



class DataValidation:
    def __init__(self,data_ingestion_artifact:DataIngestionArtifact,
                 data_validation_config:DataValidationConfig):
        try:
            self.data_ingestion_artifact=data_ingestion_artifact
            self.data_validation_config=data_validation_config
            self._schema_config = read_yaml(SCHEMA_FILE_PATH)
            log.info(f"{'>>'*20} Data Validation {'<<'*20}")
        except Exception as e:
            log.error("Error occured in Data Validation class")
            raise BookRecommentorException(e,sys)
    
    @staticmethod
    def read_data(file_path:str):
        return read_csv(file_path)
        
    def validate_number_of_columns(self,ratings_dataframe,books_dataframe):
        try:
            rating_column_names = self._schema_config["ratings_columns"]
            book_column_names = self._schema_config["books_columns"]
            if len(rating_column_names) != len(ratings_dataframe.columns):
                log.warning("Number of columns in ratings dataframe is not equal to schema")
                return False
            if len(book_column_names) != len(books_dataframe.columns):
                log.warning("Number of columns in books dataframe is not equal to schema")
                return False
            return True
        except Exception as e:
            log.error("Error in number of columns validation")
            raise BookRecommentorException(e,sys)
        
    def numerical_column_validation(self,ratings_dataframe,books_dataframe):
        try:
            numerical_ratings_columns = self._schema_config["numerical_ratings_columns"]
            numerical_books_columns = self._schema_config["numerical_books_columns"]
            given_numerical_columns_ratings = ratings_dataframe.select_dtypes(include=[float,int]).columns.tolist()
            given_numerical_columns_books = books_dataframe.select_dtypes(include=[float,int]).columns.tolist()
            
            # Check if columns exist and can be converted to numeric
            missing_numerical_columns_ratings = []
            for column in numerical_ratings_columns:
                if column not in ratings_dataframe.columns:
                    missing_numerical_columns_ratings.append(column)
                elif column not in given_numerical_columns_ratings:
                    # Try to convert to numeric
                    numeric_col = pd.to_numeric(ratings_dataframe[column], errors='coerce')
                    if numeric_col.notna().sum() == 0:
                        missing_numerical_columns_ratings.append(column)
            
            missing_numerical_columns_books = []
            for column in numerical_books_columns:
                if column not in books_dataframe.columns:
                    missing_numerical_columns_books.append(column)
                elif column not in given_numerical_columns_books:
                    # Try to convert to numeric
                    numeric_col = pd.to_numeric(books_dataframe[column], errors='coerce')
                    if numeric_col.notna().sum() == 0:
                        missing_numerical_columns_books.append(column)
            
            if len(missing_numerical_columns_ratings) > 0:
                log.warning(f"Missing numerical columns in ratings dataframe: {missing_numerical_columns_ratings}")
                return False
            if len(missing_numerical_columns_books) > 0:
                log.warning(f"Missing numerical columns in books dataframe: {missing_numerical_columns_books}")
                return False
            return True
        except Exception as e:
            log.error("Error in numerical columns validation")
            raise BookRecommentorException(e,sys)
    
    def data_drift_detection(self,ratings_dataframe,books_dataframe):
        try:
            drift_report = {}
            for column in self._schema_config["numerical_ratings_columns"]:
                numeric_col = pd.to_numeric(ratings_dataframe[column], errors='coerce').dropna()
                is_ratings_same_distribution = ks_2samp(numeric_col, numeric_col)
                is_drift_found = bool(is_ratings_same_distribution.pvalue <= 0.05)
                drift_report.update({column:{"p_value":float(is_ratings_same_distribution.pvalue),"drift_status":is_drift_found}})
            for column in self._schema_config["numerical_books_columns"]:
                numeric_col = pd.to_numeric(books_dataframe[column], errors='coerce').dropna()
                if len(numeric_col) == 0:
                    log.warning(f"Column {column} has no numeric values, skipping drift detection")
                    drift_report.update({column:{"p_value":None,"drift_status":False}})
                    continue
                is_books_same_distribution = ks_2samp(numeric_col, numeric_col)
                is_drift_found = bool(is_books_same_distribution.pvalue <= 0.05)
                drift_report.update({column:{"p_value":float(is_books_same_distribution.pvalue),"drift_status":is_drift_found}})
            drift_report_file_path = self.data_validation_config.drift_report_file_path
            os.makedirs(os.path.dirname(drift_report_file_path),exist_ok=True)
            write_yaml_file(file_path=drift_report_file_path,content=drift_report)
            log.info("Data drift detection completed successfully")
        except Exception as e:
            log.error("Error in data drift validation")
            raise BookRecommentorException(e,sys)
        
    def initiate_data_validation(self)->DataValidationArtifact:
        try:
            log.info("Initiating data validation")
            trained_books_file_path = self.data_ingestion_artifact.trained_books_file_path
            trained_ratings_file_path = self.data_ingestion_artifact.trained_ratings_file_path
            ratings_dataframe = DataValidation.read_data(trained_ratings_file_path)
            books_dataframe = DataValidation.read_data(trained_books_file_path)
            status_of_number_of_columns = self.validate_number_of_columns(ratings_dataframe,books_dataframe)
            status_of_numerical_columns = self.numerical_column_validation(ratings_dataframe,books_dataframe)
            if status_of_number_of_columns and status_of_numerical_columns:
                data_drift_report_file_path = self.data_validation_config.drift_report_file_path
                self.data_drift_detection(ratings_dataframe,books_dataframe)
                data_validation_train_ratings_file_path = self.data_validation_config.valid_train_ratings_file_path
                data_validation_train_books_file_path = self.data_validation_config.valid_train_books_file_path
                os.makedirs(os.path.dirname(data_validation_train_ratings_file_path),exist_ok=True)
                os.makedirs(os.path.dirname(data_validation_train_books_file_path),exist_ok=True)
                ratings_dataframe.to_csv(data_validation_train_ratings_file_path, index=False, header=True)
                books_dataframe.to_csv(data_validation_train_books_file_path, index=False, header=True)
                data_validation_artifact = DataValidationArtifact(
                    validation_status=True,
                    valid_train_books_file_path=data_validation_train_books_file_path,
                    valid_train_ratings_file_path=data_validation_train_ratings_file_path,
                    invalid_train_books_file_path=None,
                    invalid_train_ratings_file_path=None,
                    drift_report_file_path=data_drift_report_file_path
                )
            else:
                log.warning("Data validation status False and invalid data found")
                self.data_drift_detection(ratings_dataframe,books_dataframe)
                invalid_ratings_train_file_path = self.data_validation_config.invalid_train_ratings_file_path
                invalid_books_train_file_path = self.data_validation_config.invalid_train_books_file_path
                os.makedirs(os.path.dirname(invalid_ratings_train_file_path), exist_ok=True)
                os.makedirs(os.path.dirname(invalid_books_train_file_path), exist_ok=True)
                ratings_dataframe.to_csv(invalid_ratings_train_file_path, index=False, header=True)
                books_dataframe.to_csv(invalid_books_train_file_path, index=False, header=True)
                data_validation_artifact = DataValidationArtifact(
                    validation_status=False,
                    valid_train_books_file_path=None,
                    valid_train_ratings_file_path=None,
                    invalid_train_books_file_path=invalid_books_train_file_path,
                    invalid_train_ratings_file_path=invalid_ratings_train_file_path,
                    drift_report_file_path=self.data_validation_config.drift_report_file_path,
                )
                
            log.info("Data validation completed successfully")
            return data_validation_artifact
                
        except Exception as e:
            log.error("Error in initiating data validation")
            raise BookRecommentorException(e,sys)