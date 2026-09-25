"""
This file contains the implementation of the ClassifierEvaluationView class
"""

import json
import os


class ClassifierEvaluationView:
    """
    View component responsible for generating the evaluation report
    and handling user interaction via terminal.
    """

    @staticmethod
    def read_user_input():
        """
        Reads decision directly from the terminal.
        """
        print("\n" + "=" * 50)
        print(">>> USER DECISION REQUIRED <<<")
        print("Please check 'evaluation_report.json' to review the results.")

        # Read the input from the terminal until it is a valid option
        while True:
            decision = input("Type 'accept' or 'reject': ").strip().lower()
            if decision in ['accept', 'reject']:
                return decision
            print("Invalid input. Please type 'accept' or 'reject'.")

    @staticmethod
    def generate_report(model, filename="evaluation_system/json/evaluation_report.json"):
        """
        Generates a JSON report containing:
        1. The list of collected label records.
        2. The obtained metrics (total errors and max consecutive errors).
        """

        # 1. Prepare the data structure
        report_data = {
            "results": {
                "total_errors": model.total_errors,
                "max_consecutive_errors": model.max_consecutive_errors
            },
            "configuration_thresholds": {
                "max_allowed_errors": model.total_errors_threshold,
                "max_allowed_consecutive_errors": model.max_consecutive_errors_threshold
            },
            "collected_records": []
        }

        # 2. Populate the records list
        for record in model.labels_records:
            is_match = record.predict_label == record.actual_label

            record_entry = {
                "uuid": record.uuid,
                "expert_label": record.actual_label,
                "classifier_label": record.predict_label,
                "match_result": "MATCH" if is_match else "ERROR"
            }
            report_data["collected_records"].append(record_entry)

        # 3. Write to JSON file
        try:
            with open(filename, 'w') as f:
                json.dump(report_data, f, indent=4)
            print(f"\n[Evaluation System] JSON Report generated successfully: "
                  f"{os.path.abspath(filename)}")
        except Exception as e:
            print(f"\n[Evaluation System Error] Could not save JSON report: {e}")
