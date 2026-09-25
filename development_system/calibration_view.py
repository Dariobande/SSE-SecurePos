"""
This file contains the implementation of the CalibrationView class
"""

from random import random
import os
import matplotlib.pyplot as plt


class CalibrationView:
    """
    Handles the calibration report.
    """
    @staticmethod
    def build_report(loss_curve):
        """
        Build the calibration report.
        """
        print("\n--- CALIBRATION REPORT ---")
        plt.figure()
        plt.plot(range(1, len(loss_curve) + 1), loss_curve, label='Calibration plot')
        plt.xlabel('Training Iteration')
        plt.ylabel('Training Loss')
        plt.title('Training Loss Curve')
        plt.legend()
        os.makedirs("development_system/plot", exist_ok=True)
        plt.savefig("development_system/plot/calibration_plot.png")
        plt.close()
        print("Calibration report saved")
        print("--------------------------")

    @staticmethod
    def read_user_input(flag):
        """
        Read user input on the calibration report.
        """
        # Check calibration plot and get number iterations decision
        if not flag:
            res = input(">> Data Scientist: Number iterations fine? (y/n): ")
        else:
            res = "y" if random() <= 0.3 else "n"
        return res.lower() == 'y'
