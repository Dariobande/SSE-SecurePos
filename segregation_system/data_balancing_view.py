"""
Provides functionalities for visualizing the data balancing report as a bar chart
"""

import os
import random

import matplotlib.pyplot as plt
import numpy as np

from segregation_system.data_balancing_model import DataBalancingModel
from shared.attack_risk_level import AttackRiskLevel

class DataBalancingView:
    """
    Represents the view for the data balancing chart

    :ivar output_dir: The directory where the chart will be saved
    :type output_dir: str
    """
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def build_report(self, model: DataBalancingModel) -> None:
        """
        Generate a bar chart that provides a data balancing report based on session counts,
        target sessions per class, and a specified tolerance for balancing
        """
        labels = [AttackRiskLevel.NORMAL, AttackRiskLevel.MODERATE, AttackRiskLevel.HIGH]
        sessions = [
            model.session_counts[AttackRiskLevel.NORMAL],
            model.session_counts[AttackRiskLevel.MODERATE],
            model.session_counts[AttackRiskLevel.HIGH]
        ]
        colors = ["green", "orange", "red"]

        tolerance = model.balancing_tolerance
        mean = float(np.mean(sessions))

        _, ax = plt.subplots(figsize=(10, 6))

        ax.bar(labels, sessions, color=colors)

        ax.axhline(y=mean, color="black", linewidth=2, label="Mean")
        ax.axhline(y=mean + mean * tolerance, color="black", linestyle="--",
            label=f"Mean +/- tolerance ({tolerance})")
        ax.axhline(y=mean - mean * tolerance, color="black", linestyle="--")

        ax.set_ylabel("Number of sessions")
        ax.set_xlabel("Attack risk level")
        ax.set_title("Data balancing report")
        ax.legend()

        os.makedirs(self.output_dir, exist_ok=True)
        output_file = f"{self.output_dir}/data_balancing_report.png"
        plt.savefig(output_file)
        print(f"[DataBalancingView] Data balancing report saved to '{output_file}'")

    @staticmethod
    def read_user_input(service_flag: bool) -> None | dict[AttackRiskLevel, int]:
        """
        Reads (or randomly chooses) user input to determine data balance and,
        if necessary, the additional sessions required for each attack risk level.
        If data is balanced returns None, else returns the number of additional
        sessions requested
        """
        # Is data balanced?
        if service_flag:
            data_balanced = random.random() < 0.9
            print(f"[DataBalancingView] Simulated user decision: data "
                  f"{'not ' if not data_balanced else ' '}balanced")
        else:
            result = input("[DataBalancingView] Is data balanced? (Y/n): \n > ")
            data_balanced = result.lower() == "y"
        if data_balanced:
            return None

        # If data is not balanced, how many additional sessions do we need?
        requested_sessions = {level: 0 for level in AttackRiskLevel}
        if service_flag:
            for level in AttackRiskLevel:
                requested_sessions[level] = random.randint(0, 50)
            print(f"[DataBalancingView] Simulated user decision: "
                  f"requested sessions {requested_sessions}")
        else:
            for level in AttackRiskLevel:
                result = input(f"[Controller] How many additional sessions for {level}? \n > ")
                requested_sessions[level] = int(result)
        return requested_sessions
