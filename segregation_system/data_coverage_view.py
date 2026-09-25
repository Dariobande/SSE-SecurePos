"""
Provides functionalities for visualizing the data coverage report as a radar chart
"""

import os
import random

import plotly.graph_objects as go
import plotly.express as px

from segregation_system.data_coverage_model import DataCoverageModel
from shared.attack_risk_level import AttackRiskLevel


class DataCoverageView:
    """
    Represents the view for the data coverage chart

    :ivar output_dir: The directory where the chart will be saved
    :type output_dir: str
    """
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def build_report(self, model: DataCoverageModel) -> None:
        """
        Builds a radar chart based on the provided data coverage model
        """
        flat_features = []
        flat_samples = []
        flat_colors = []

        colors = px.colors.qualitative.Plotly
        for feature, samples in model.normalized_features_samples.items():
            for sample in samples:
                flat_features.append(feature.name)
                flat_samples.append(sample)
                flat_colors.append(colors[0 % len(colors)])

        fig = go.Figure()

        fig.add_trace(
            go.Scatterpolar(
                r=flat_samples,
                theta=flat_features,
                mode="markers",
                marker={"color": flat_colors},
                fill=None,
            )
        )

        fig.update_layout(
            polar={"radialaxis": {"visible": True}},
            showlegend=False,
            title="Data coverage report"
        )

        os.makedirs(self.output_dir, exist_ok=True)
        output_file = f"{self.output_dir}/data_coverage_report.png"
        fig.write_image(output_file)
        print(f"[DataCoverageView] Data coverage report saved to '{output_file}'")

    @staticmethod
    def read_user_input(service_flag: bool) -> None | dict[AttackRiskLevel, int]:
        """
        Reads (or randomly chooses) user input to determine feature distribution and,
        if necessary, the additional sessions required.
        If features are well distributed returns None, else returns the number of
        additional sessions requested
        """
        # Are features well distributed?
        if service_flag:
            features_well_distributed = random.random() < 0.9
            print(
                f"[DataCoverageView] Simulated user decision: "
                f"features {'not ' if not features_well_distributed else ' '}distributed")
        else:
            result = input("[DataCoverageView] Are features well distributed? (Y/n): \n > ")
            features_well_distributed = result.lower() == "y"
        if features_well_distributed:
            return None

        # If features are not well distributed, how many additional sessions do we need?
        requested_sessions = {level: 0 for level in AttackRiskLevel}
        if service_flag:
            result = random.randint(0, 50)
            print(f"[DataCoverageView] Simulated user decision: "
                  f"requested {result} additional sessions")
        else:
            result = int(input("[DataCoverageView] How many additional sessions? \n > "))
        # Evenly distribute the requested sessions
        for level in AttackRiskLevel:
            requested_sessions[level] = result // 3
        return requested_sessions
