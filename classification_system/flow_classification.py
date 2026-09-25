"""
This file contains the implementation of the FlowClassification class
"""

import os

import pandas as pd
from sklearn.neural_network import MLPClassifier
import joblib

from shared.attack_risk_level import AttackRiskLevel


class FlowClassification:
    """
    Flow Classification class.
    This class implements the deploy and classify methods,
    which are called from the Classification System Controller,
    depending on the operating phase.
    """

    @staticmethod
    def deploy(filename: str) -> MLPClassifier:
        """
        Deserialize the received binary file into a MLPClassifier python class
        :param filename:
        :return:
        """
        model = joblib.load(filename)
        if not isinstance(model, MLPClassifier):
            raise TypeError("Loaded object is not an MLPClassifier")
        os.makedirs("classification_system/state", exist_ok=True)
        joblib.dump(model, "classification_system/state/saved_model.joblib")
        return model

    @staticmethod
    def classify(model: MLPClassifier, prepared_session: dict) -> AttackRiskLevel:
        """
        Classifies the given features using the provided MLP model.

        :param model: The trained MLPClassifier.
        :param prepared_session: A PreparedSession dict.
        :return: The corresponding AttackRiskLevel.
        """

        expected_features = model.feature_names_in_

        df = pd.DataFrame([prepared_session])

        try:
            x_pred = df[expected_features]
        except KeyError:
            print(f"No features were provided for {expected_features}")
            return AttackRiskLevel.NORMAL

        prediction = model.predict(x_pred)[0]

        raw_result = list(AttackRiskLevel)[int(prediction)]

        try:
            return AttackRiskLevel(raw_result)
        except ValueError:
            print(f"Warning: Unknown classification label '{raw_result}'")
            return AttackRiskLevel.NORMAL
