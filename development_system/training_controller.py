"""
This file contains the implementation of the TrainingController class
"""

from random import randint
from development_system.calibration_view import CalibrationView


class TrainingController:
    """
    Handles all training operations.
    """
    ITERATION_PATH = "development_system/input/number_iterations.json"
    ITERATION_DECISION_PATH = "development_system/input/iterations_decision.json"

    def __init__(self, parent):
        self.parent = parent
        self.view = CalibrationView()

    def set_average_params(self):
        """
        Sets the average parameters of the training process.
        """
        self.parent.neural_network.set_avg_hyper_params()

    def run(self, test_set):
        """
        Runs the training phase.
        """
        iterations = self.parent.neural_network.number_iterations
        # Set average hyper params
        if iterations is None or iterations == 0:
            self.set_average_params()
        # Read number of iterations
        if not self.parent.service_flag:
            iterations = input(">> Insert number of iterations (eg. 100): ")
        else:
            iterations = 100 + randint(-50, 50)
        self.parent.neural_network.set_number_iterations(iterations)
        # Calibrate
        loss_curve = self.parent.neural_network.calibrate(test_set)
        # Build Report
        self.view.build_report(loss_curve)
        # Read User Input (iterations decision)
        self.parent.iterations_fine = self.view.read_user_input(self.parent.service_flag)
