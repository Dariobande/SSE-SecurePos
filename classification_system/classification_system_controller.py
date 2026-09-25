"""
Main File of the Classification System package
"""
import time
import joblib

from classification_system.flow_classification import FlowClassification
from shared.message_counter import PhaseMessageCounter
from shared.systemsio import SystemsIO, Endpoint
from shared.loader import load_and_validate_json_file
from shared.address import Address


# pylint: disable=too-many-instance-attributes,too-few-public-methods
class ClassificationSystemController:
    """
    The Classification System Controller will manage two operations:
        1. deployment of the new classifier received during the development phase
        2. classification of  the prepared session received by the preparation system
    """

    SHARED_CONFIG_PATH = "shared/json/shared_config.json"
    SHARED_CONFIG_SCHEMA = "shared/json/shared_config.schema.json"
    PREPARED_SESSION_SCHEMA = "classification_system/json/prepared_session.schema.json"

    INPUT_CLASSIFIER_ENDPOINT = "/classifier"
    INPUT_PREPARED_SESSION_ENDPOINT = "/prepared-session"
    EVALUATION_ENDPOINT = "/predicted-label"
    TIMESTAMP_ENDPOINT = "/timestamp"

    def __init__(self):
        shared_config = load_and_validate_json_file(
            self.SHARED_CONFIG_PATH,
            self.SHARED_CONFIG_SCHEMA
        )
        self.classification_system_address = Address(
            **shared_config['addresses']['classificationSystem']
        )
        self.evaluation_system_address = Address(
            **shared_config['addresses']['evaluationSystem']
        )
        self.simulator_system_address = Address(
            **shared_config['addresses']['simulatorSystem']
        )
        endpoints = [
            Endpoint(self.INPUT_CLASSIFIER_ENDPOINT),
            Endpoint(self.INPUT_PREPARED_SESSION_ENDPOINT, self.PREPARED_SESSION_SCHEMA)
        ]
        self.io = SystemsIO(endpoints, port=self.classification_system_address.port)
        self.is_development = shared_config['systemPhase']['developmentPhase']
        self.flow = FlowClassification()
        self.service_flag = shared_config['serviceFlag']
        evaluation_window = shared_config['systemPhase']['evaluationPhaseWindow']
        production_window = shared_config['systemPhase']['productionPhaseWindow']
        self.counter = PhaseMessageCounter(
            "state/classification_counter.json",
            evaluation_window,
            production_window
        )

    def run(self):
        """
        Method to run the classification system controller;
        if the system is in development phase, a new classifier will be developed,
        else it will list for a prepared session to be classified.
        """
        while True:
            if self.is_development:
                filename = self.io.receive(self.INPUT_CLASSIFIER_ENDPOINT)[0]
                model = self.flow.deploy(filename)
                print("[TO MESSAGING SYSTEM]")
                print(f"Model loaded from: {filename}")
                print(f"Model type: {type(model).__name__}")
                print(f"Hidden layer sizes: {model.hidden_layer_sizes}")
                print(f"Number of iterations trained: {model.n_iter_}")
                self.io.send_json(
                    self.simulator_system_address,
                    self.TIMESTAMP_ENDPOINT,
                    {'timestamp': int(time.time() * 1000)}
                )
                if not self.service_flag:
                    return
                continue

            model = joblib.load("classification_system/state/saved_model.joblib")

            prepared_session = self.io.receive(self.INPUT_PREPARED_SESSION_ENDPOINT)
            out_label = self.flow.classify(model, prepared_session)

            if self.counter.register_message():
                data = {
                    'uuid': prepared_session['uuid'],
                    'label': out_label.value
                }
                self.io.send_json(self.evaluation_system_address, self.EVALUATION_ENDPOINT, data)
            else:
                self.io.send_json(
                    self.simulator_system_address,
                    self.TIMESTAMP_ENDPOINT,
                    {'timestamp': int(time.time() * 1000)}
                )

            print(f"[TO CLIENT_SIDE SYSTEM] label: {out_label.value}")

            if not self.service_flag:
                break


if __name__ == "__main__":
    controller = ClassificationSystemController()
    controller.run()
