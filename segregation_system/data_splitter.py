"""
Module for splitting a dataset of prepared sessions into training, validation, and test subsets
"""

import os
import uuid
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from segregation_system.prepared_sessions_db import PreparedSession

class DataSplitter:
    """
    Splits a dataset of prepared sessions into training, validation,
    and test subsets based on user-defined percentage splits

    :ivar train_split_percentage: Percentage of the dataset to be used for training [0, 1]
    :type train_split_percentage: float
    :ivar validation_split_percentage: Percentage of the dataset to be used for validation [0, 1]
    :type validation_split_percentage: float
    :ivar test_split_percentage: Percentage of the dataset to be used for testing [0, 1]
    :type test_split_percentage: float
    """

    def __init__(
        self,
        train_split_percentage: float,
        validation_split_percentage: float,
        test_split_percentage: float,
        output_dir: str
    ):
        self.train_split_percentage = train_split_percentage
        self.validation_split_percentage = validation_split_percentage
        self.test_split_percentage = test_split_percentage
        self.output_dir = output_dir

    def split(self, sessions: list[PreparedSession]) -> list[str]:
        """
        Splits a list of prepared sessions into training, validation, and test sets.
        The splits are then saved into separate CSV files
        """
        df = pd.DataFrame([vars(s) for s in sessions])

        initial_cols = len(df.columns)
        df.dropna(axis=1, how='any', inplace=True)
        non_na_cols = len(df.columns)
        print(f"[DataSplitter] Dropped {initial_cols - non_na_cols} columns with missing values")

        # First Split: Separate Train from the rest (Validation + Test)
        train_df, temp_df = train_test_split(
            df,
            train_size=self.train_split_percentage,
            shuffle=True
        )

        # Second Split: Separate Validation and Test from the 'temp_set'
        # We must recalculate the split ratio relative to the remaining data
        relative_test_size = (self.test_split_percentage /
            (self.validation_split_percentage + self.test_split_percentage))
        validation_df, test_df = train_test_split(
            temp_df,
            test_size=relative_test_size,
            shuffle=True
        )

        output_files = []
        splits_id = uuid.uuid4() # Avoids overwriting previous splits
        os.makedirs(self.output_dir, exist_ok=True)

        datasets = {
            "train": train_df,
            "validation": validation_df,
            "test": test_df
        }
        for split_name, split_df in datasets.items():
            path = f"{self.output_dir}/{split_name}_set.{splits_id}.csv"
            split_df.to_csv(path, index=False, encoding="utf-8")
            print(f"[DataSplitter] Saved {len(split_df)} sessions to '{path}'")
            output_files.append(path)
        return output_files

    @staticmethod
    def delete(paths: list[str]) -> None:
        """
        Deletes the specified files from the filesystem
        """
        for path in paths:
            Path(path).unlink(missing_ok=True)
            print(f"[DataSplitter] Deleted '{path}'")
