import pandas as pd 
import yaml
import os
import sys
from src.exception.custom_exception import BookRecommentorException
from src.logger import GLOBAL_LOGGER as log 
import numpy as np
import pickle
from scipy.sparse import issparse

def read_csv(file_path:str):
    """
    Reads a CSV file and returns a DataFrame.
    """
    df = pd.read_csv(file_path, low_memory=False)
    return df


def read_yaml(file_path:str):
    """
    Reads a YAML file and returns a dictionary.
    """
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    return data

def write_yaml_file(file_path:str,content:dict=None):
    try:
        os.makedirs(os.path.dirname(file_path),exist_ok=True)
        with open(file_path,"w") as yaml_file:
            yaml.dump(content, yaml_file, default_flow_style=False, allow_unicode=True)
        log.info(f"yaml file: {file_path} written successfully")
    except Exception as e:
        log.error(f"Error writing yaml file: {file_path}")
        raise BookRecommentorException(e,sys)

def drop_columns(dataframe:pd.DataFrame,columns:list):
    """
    Drops specified columns from a DataFrame.
    """
    if not all(column in dataframe.columns for column in columns):
        raise ValueError("One or more columns to drop are not present in the DataFrame.")
    df = dataframe.drop(columns=columns)
    return df

def save_numpy_array_data(file_path:str,array:np.array):
    """
    Saves a numpy array or sparse matrix to a file.
    """
    try:
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Handle sparse matrices
        from scipy.sparse import issparse
        if issparse(array):
            # Use scipy's save_npz for sparse matrices
            from scipy.sparse import save_npz
            save_npz(file_path, array)
        else:
            # Use numpy's save for regular arrays
            with open(file_path, "wb") as file_obj:
                np.save(file_obj, array, allow_pickle=True)
        
        log.info(f"Array saved successfully at {file_path}")
    except Exception as e:
        log.error(f"Error saving array: {str(e)}")
        raise BookRecommentorException(e, sys)
    
def save_object(file_path:str, obj:object):
    """
    Saves an object to a file.
    """
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as file_obj:
        pickle.dump(obj, file_obj)
    log.info(f"Object saved successfully at {file_path}")
    
def load_numpy_array_data(file_path:str):
    """
    Loads a numpy array or sparse matrix from a file.
    """
    try:
        # Check if it's a sparse matrix file (.npz extension)
        if file_path.endswith('.npz'):
            from scipy.sparse import load_npz
            array = load_npz(file_path)
        else:
            # Load regular numpy array
            with open(file_path, "rb") as file_obj:
                array = np.load(file_obj, allow_pickle=True)
        
        log.info(f"Array loaded successfully from {file_path}")
        return array
    except Exception as e:
        log.error(f"Error loading array: {str(e)}")
        raise BookRecommentorException(e, sys)
    
def load_object(file_path:str):
    """
    Loads an object from a file.
    """
    with open(file_path, "rb") as file_obj:
        return pickle.load(file_obj)
    log.info(f"Object loaded successfully from {file_path}")
    