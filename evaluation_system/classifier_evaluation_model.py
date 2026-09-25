"""
This file contains the implementation of the ClassifierEvaluationModel class
"""

from dataclasses import dataclass
from typing import List, Dict
from shared.attack_risk_level import AttackRiskLevel


@dataclass
class LabelsRecord:
    """Class to hold a single transaction's evaluation record."""
    uuid: str
    predict_label: AttackRiskLevel  # Classifier's predicted risk level
    actual_label: AttackRiskLevel  # True risk level (Ground Truth)


class ClassifierEvaluationModel:
    """
    Model responsible for calculating and storing performance metrics
    based on a batch of label records.
    """

    def __init__(self, records: List[LabelsRecord], config: Dict):
        self.labels_records = records  # The batch of records to evaluate

        # Extract thresholds directly from the config dictionary
        self.total_errors_threshold = config['maxErrors']
        self.max_consecutive_errors_threshold = config['maxConsecutiveErrors']

        # Initialize the metrics
        self.total_errors = 0
        self.max_consecutive_errors = 0

        # Calculate the metrics
        self._calculate_metrics()

    def _calculate_metrics(self):
        """
        Calculates and updates the total errors and the maximum consecutive errors.
        """
        current_consecutive = 0
        for record in self.labels_records:
            # Check for a classification error
            if record.predict_label != record.actual_label:
                self.total_errors += 1
                current_consecutive += 1
            else:
                # Reset consecutive count if match occurs, update max if needed
                self.max_consecutive_errors = max(self.max_consecutive_errors, current_consecutive)
                current_consecutive = 0

        # Final check in case the sequence ended with an error streak
        self.max_consecutive_errors = max(self.max_consecutive_errors, current_consecutive)
