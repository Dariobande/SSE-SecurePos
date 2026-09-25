"""
This file contains the implementation of the TestView class
"""

from random import random, randint


class TestView:
    """
    Handles the test report.
    """
    @staticmethod
    def build_report(test_error, model_info, generalization_tolerance) -> float:
        """
        Builds the report of the test.
        """
        val_error = model_info["validation_error"]
        difference = (val_error - test_error) / val_error if val_error > test_error \
            else (test_error - val_error) / test_error
        print("\n--- TEST REPORT ---")
        print(f"Winner Network ID: {model_info['id']}")
        print(f"Validation Error: {val_error}")
        print(f"Test Error: {test_error}")
        print(f"Difference: {difference}")
        print("--------------------")
        print(f"Generalization Tolerance: {generalization_tolerance}")
        print("--------------------")
        return difference

    @staticmethod
    def read_user_input(flag, difference, generalization_tolerance):
        """
        Reads the user input for the test result.
        """
        # Data Scientist: Test passed
        hidden_layer_size = None
        hidden_neuron_per_layer = None
        if not flag:
            res = input(">> Data Scientist: Test passed and send classifier? (y/n): ")
        else:
            res = "n" if difference > generalization_tolerance else "y" if random() >= 0.01 else "n"
        if res.lower() == "n":
            hidden_layer_size = {
                "min": 1,
                "max": 5 + randint(0, 10),
                "step": 1 + randint(0, 2)
            }
            hidden_neuron_per_layer = {
                "min": 1,
                "max": 50 + randint(50, 250),
                "step": 15 + randint(0, 25)
            }
        return res.lower() == 'y', hidden_layer_size, hidden_neuron_per_layer
