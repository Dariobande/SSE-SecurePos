"""
This file contains the implementation of the EvaluationSystemController class
"""

import random
import sys

from shared.systemsio import SystemsIO, Endpoint
from shared.loader import load_and_validate_json_file

from evaluation_system.labels_buffer_db import LabelsBufferDB
from evaluation_system.classifier_evaluation_model import ClassifierEvaluationModel
from evaluation_system.classifier_evaluation_view import ClassifierEvaluationView


class EvaluationSystemController:
    """
    Controller for the Evaluation System.
    Manages data ingestion, storage, and the evaluation workflow based on thresholds.
    """

    def __init__(self):
        # Local configuration paths
        self.LOCAL_CONFIG_PATH = "evaluation_system/json/config.json"
        self.LOCAL_SCHEMA_PATH = "evaluation_system/json/config.schema.json"

        # Shared configuration paths
        self.SHARED_CONFIG_PATH = "shared/json/shared_config.json"
        self.SHARED_SCHEMA_PATH = "shared/json/shared_config.schema.json"

        # Endpoints
        self.PREDICT_ENDPOINT = "/predicted-label"
        self.ACTUAL_ENDPOINT = "/actual-label"

        # 1. Load and validate local configuration
        try:
            self.local_config = load_and_validate_json_file(
                self.LOCAL_CONFIG_PATH,
                self.LOCAL_SCHEMA_PATH
            )
            print("[Evaluation System] Local configuration loaded.")
        except Exception as e:
            print(f"[Evaluation System Error] Failed to load local config: {e}")
            sys.exit(1)

        # 2. Load and validate shared configuration
        try:
            shared_config = load_and_validate_json_file(
                self.SHARED_CONFIG_PATH,
                self.SHARED_SCHEMA_PATH
            )

            # Extract Service Flag
            self.service_flag = shared_config.get('serviceFlag', False)

            # Extract System Port (from addresses -> evaluationSystem -> port)
            self.PORT = shared_config['addresses']['evaluationSystem']['port']

            print(f"[Evaluation System] Shared configuration loaded. "
                  f"Port: {self.PORT}, Service Flag: {self.service_flag}")

        except FileNotFoundError as e:
            print(f"[Evaluation System Error] Configuration file not found: {e}")
            sys.exit(1)
        except KeyError as e:
            print(f"[Evaluation System Error] Missing required key in shared config: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"[Evaluation System Error] Failed to load shared config: {e}")
            sys.exit(1)

        # 3. Initialize Components
        self.db = LabelsBufferDB()
        self.view = ClassifierEvaluationView()

        # 4. Initialize Endpoints to receive data from the other systems
        endpoints = [
            Endpoint(self.PREDICT_ENDPOINT, "evaluation_system/json/message.schema.json"),
            Endpoint(self.ACTUAL_ENDPOINT, "evaluation_system/json/message.schema.json")
        ]
        self.io = SystemsIO(endpoints, port=self.PORT)

    def run(self):
        """
        Main application loop.
        Continuously ingests data and triggers evaluation when thresholds are met.
        """
        print(f"[Evaluation System] System started on port {self.PORT}."
              f" Waiting for data streams...")

        while True:
            # Phase 1: Data Accumulation
            # Keep collecting data until the minimum batch size (from local config) is reached
            while not self.db.sufficient_labels_query(self.local_config['minNumberLabels']):
                # Receive 1: Prediction (blocking call)
                predict_data = self.io.receive(self.PREDICT_ENDPOINT)

                # Store Prediction immediately.
                # DB handles finding the actual label or creating a new record.
                self.db.store_label(
                    uuid=predict_data.get('uuid'),
                    predict_label=predict_data.get('label'),
                    actual_label=None
                )
                print(f"[Evaluation System] Stored PREDICT for UUID {predict_data.get('uuid')}.")

                # Receive 2: Actual label (blocking call)
                actual_data = self.io.receive(self.ACTUAL_ENDPOINT)

                # Store Actual immediately.
                # DB handles finding the prediction or creating a new record.
                self.db.store_label(
                    uuid=actual_data.get('uuid'),
                    predict_label=None,
                    actual_label=actual_data.get('label')
                )
                print(f"[Evaluation System] Stored ACTUAL for UUID {actual_data.get('uuid')}.")

            # Phase 2: Evaluation Phase
            # Threshold met, proceed to analyze metrics
            self._perform_evaluation()

    def _perform_evaluation(self):
        """
        Orchestrates the creation of the evaluation report and handles the decision outcome.
        """
        print("\n[Evaluation System] Batch threshold reached. Generating evaluation report...")

        # Retrieve accumulated data and initialize the domain model
        labels_records = self.db.get_labels()
        model = ClassifierEvaluationModel(labels_records, self.local_config)

        # Generate the JSON report
        self.view.generate_report(model)

        # Proceed to handle the acceptance or rejection decision
        self._handle_decision()

    def _handle_decision(self):
        """
        Manages the decision-making process based on the Service Flag.
        """
        if self.service_flag:
            # Automatic Mode: Decision is simulated without user intervention
            print("[Evaluation System] Service Flag active. Proceeding with automated decision...")
            # Weighted choice: 6/7 chance for 'accept', 1/7 for 'reject'
            # (assuming 6 times out of 7 the evaluation is fine)
            weighted_choices = ['accept'] * 6 + ['reject'] * 1
            decision = random.choice(weighted_choices)

            print(f"[Evaluation System] Automated decision: {decision.upper()}")
        else:
            # Manual Mode: Wait for user input via terminal
            decision = self.view.read_user_input()

        # Execute logic based on decision
        if decision == 'accept':
            print("[Evaluation System] Evaluation approved.")
        elif decision == 'reject':
            print("[Evaluation System] Evaluation rejected.")

            # Print the current configuration to the terminal for debugging/reconfiguration
            print("\n" + "*" * 50)
            print(">>> CONFIGURATION DUMP <<<")
            print(f"Current Config: {self.local_config}")
            print("*" * 50 + "\n")

        # Reset system state for the next batch
        print("[Evaluation System] Clearing internal buffer...")
        self.db.delete_labels()
        print("[Evaluation System] Buffer cleared. Resuming data ingestion.\n")


if __name__ == '__main__':
    app = EvaluationSystemController()
    app.run()
