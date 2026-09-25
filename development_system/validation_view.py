"""
This file contains the implementation of the ValidationView class
"""

from random import random


class ValidationView:
    """
    Handles the validation report.
    """
    @staticmethod
    def build_report(models_info):
        """
        Builds a report of the validation results.
        """
        top_five = sorted(models_info, key=lambda x: x["validation_error"])[:5]
        print("\n--- VALIDATION REPORT ---")
        for model in top_five:
            print(model)
        print("-------------------------")
        return top_five

    @staticmethod
    def read_user_input(flag, top_five, overfitting_tolerance):
        """
        Reads the user input for the validation results.
        """
        # Data Scientist: Valid classifier decision
        if not flag:
            return input(">> Data Scientist: Is there a valid classifier? (id/n): ")
        best = top_five[0]
        second_best = top_five[1]
        if random() < 0.05 or best["difference"] > overfitting_tolerance:
            return "n"
        val_err_diff = best["validation_error"] - second_best["validation_error"]
        if val_err_diff >= 0.05 or second_best["difference"] > overfitting_tolerance:
            return best["id"]
        return (
            second_best["id"]
            if second_best["network_complexity"] < best["network_complexity"]
            else best["id"]
        )
