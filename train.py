#!/usr/bin/env python3
"""
Training Script for Book Recommendation System
Uses the production-grade training pipeline
"""
import sys
from src.pipeline import run_training_pipeline
from src.exception.custom_exception import BookRecommentorException
from src.logger import GLOBAL_LOGGER as log


def main():
    """Execute the training pipeline"""
    try:
        log.info("Starting training pipeline execution")
        model_trainer_artifact = run_training_pipeline()
        log.info(f"Training completed successfully! Model saved at: {model_trainer_artifact.trained_model_file_path}")
        
    except Exception as e:
        log.error(f"Training pipeline failed: {e}")
        raise BookRecommentorException(e, sys) from e


if __name__ == "__main__":
    main()