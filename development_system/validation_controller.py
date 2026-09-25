"""
This file contains the implementation of the ValidationController class
"""

from development_system.validation_view import ValidationView


class ValidationController:
    """
    Handles all validation operations.
    """
    def __init__(self, parent):
        self.parent = parent
        self.view = ValidationView()
        self.ongoing_validation = False

    def run(self, test_set, validation_set):
        """
        runs the validation phase.
        """
        # Set HyperParams
        self.ongoing_validation = self.parent.neural_network.set_hyper_params()
        print("[Validation] Initial HyperParams set (Grid Search).")

        while self.ongoing_validation:
            # Calibrate
            self.parent.neural_network.calibrate(test_set)
            # Set HyperParams
            self.ongoing_validation = self.parent.neural_network.set_hyper_params()

        # Validation score
        res = self.parent.neural_network.validate(validation_set)
        if not res:
            print("[Validation] Validation failed.")
            return
        # Build Report
        top_five = self.view.build_report(self.parent.neural_network.models_info)

        # Read User Input (Classifier decision)
        overfitting_tolerance = self.parent.config["overfittingTolerance"]
        res = self.view.read_user_input(self.parent.service_flag, top_five, overfitting_tolerance)
        print(f"[Validation] Valid classifier selected: {res}")
        if res != "n" and 0 <= int(res) <= len(self.parent.neural_network.models):
            self.parent.valid_classifier_id = int(res)
            self.parent.valid_classifier_exists = True
