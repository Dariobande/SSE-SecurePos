"""
This file contains the implementation of the TestController class
"""
import json
import os
from joblib import dump
from development_system.test_view import TestView
from shared.systemsio import SystemsIO


class TestController:
    """
    Handles all test operations.
    """

    CLASSIFIER_PATH = "development_system/classifier/classifier.joblib"

    def __init__(self, parent):
        self.parent = parent
        self.view = TestView()

    def run(self, test_set):
        """
        Runs the test phase.
        """
        # Run Test
        classifier_id = self.parent.valid_classifier_id
        print(f"[Test] Final test execution on classifier {classifier_id}...")
        test_error, model_info = self.parent.neural_network.test(classifier_id, test_set)
        # Build Report
        generalization_tolerance = self.parent.config["generalizationTolerance"]
        difference = self.view.build_report(test_error, model_info, generalization_tolerance)
        # Read User Input (Test passed)
        test_passed, hidden_layer_size, hidden_neuron_per_layer = self.view.read_user_input(
            self.parent.service_flag, difference, generalization_tolerance)

        if test_passed:
            # Create and Send Classifier
            model = self.parent.neural_network.models[self.parent.valid_classifier_id]
            os.makedirs("development_system/classifier", exist_ok=True)
            customer = test_set.split(".")[1]
            dump(model, f"development_system/classifier/classifier.{customer}.joblib")
            address = self.parent.classification_address
            SystemsIO.send_files(address, "/classifier", [self.CLASSIFIER_PATH])
            print("[Test] Classifier sent")
        else:
            # Reconfigure hyper params ranges
            print(f"[Test] New range hidden layers size: {hidden_layer_size}")
            print(f"[Test] New range neurons per hidden layer: {hidden_neuron_per_layer}")
            path = self.parent.CONFIG_PATH
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["hiddenNeuronPerLayerRange"] = hidden_layer_size
            data["hiddenNeuronPerLayerRange"] = hidden_neuron_per_layer
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        return test_passed
