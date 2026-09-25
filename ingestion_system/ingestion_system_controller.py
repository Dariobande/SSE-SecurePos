"""
This file implements the Ingestion System Controller.
Its purpose is to collect records, gather them into raw sessions and
send them to the next system
"""

from dataclasses import asdict
from shared.address import Address

from shared.message_counter import PhaseMessageCounter
from shared.systemsio import SystemsIO, Endpoint
from shared.loader import load_and_validate_json_file
from ingestion_system.raw_session_db import RawSessionDB
from ingestion_system.flow_analysis import FlowAnalysis


# pylint: disable=too-many-instance-attributes,too-few-public-methods
class IngestionSystemController:
    """
    This class implements the Ingestion System Controller.
    It can be run from the user by calling the method run.
    """

    LOCAL_CONFIG_PATH = "ingestion_system/json/ingestion_system_configuration.json"
    SHARED_CONFIG_PATH = "shared/json/shared_config.json"
    RECORD_SCHEMA = "ingestion_system/json/record.schema.json"
    LOCAL_CONFIG_SCHEMA = "ingestion_system/json/config.schema.json"
    SHARED_CONFIG_SCHEMA = "shared/json/shared_config.schema.json"

    INPUT_RECORD_ENDPOINT = "/record"
    EVALUATION_SYSTEM_ENDPOINT = "/actual-label"
    PREPARATION_SYSTEM_ENDPOINT = "/process"

    def _get_min_records(self) -> int:
        return 3 if not self.is_development and not self.counter.is_evaluation() else 4

    def __init__(self):
        self.local_config = load_and_validate_json_file(
            self.LOCAL_CONFIG_PATH,
            self.LOCAL_CONFIG_SCHEMA
        )
        self.shared_config = load_and_validate_json_file(
            self.SHARED_CONFIG_PATH,
            self.SHARED_CONFIG_SCHEMA
        )
        self.ingestion_system_address = Address(
            **self.shared_config['addresses']['ingestionSystem']
        )
        self.preparation_system_address = Address(
            **self.shared_config['addresses']['preparationSystem']
        )
        self.evaluation_system_address = Address(
            **self.shared_config['addresses']['evaluationSystem']
        )
        self.db = RawSessionDB()
        endpoints = [Endpoint(self.INPUT_RECORD_ENDPOINT, self.RECORD_SCHEMA)]
        self.io = SystemsIO(endpoints, port=self.ingestion_system_address.port)
        self.analysis = FlowAnalysis()
        evaluation_window = self.shared_config['systemPhase']['evaluationPhaseWindow']
        production_window = self.shared_config['systemPhase']['productionPhaseWindow']
        self.counter = PhaseMessageCounter(
            "state/ingestion_counter.json",
            evaluation_window,
            production_window
        )
        self.is_development = self.shared_config['systemPhase']['developmentPhase']
        self.minimum_records = self._get_min_records()

    def run(self):
        """
        The Ingestion System Controller can be run from the user
        by calling this method. If the service flag is on, this system
        will not close after one iteration: it will listen forever for new
        incoming records.
        """
        while True:
            raw_session = None
            while raw_session is None:
                json_record = self.io.receive(self.INPUT_RECORD_ENDPOINT)

                if json_record['type'] == 'label' and self.minimum_records == 3:
                    continue

                self.db.store(json_record)
                raw_session = self.db.get_session(json_record['uuid'], self.minimum_records)

            self.db.remove(raw_session.uuid)

            if not self.analysis.mark_missing_samples(
                    raw_session,
                    self.local_config["missingSamplesThreshold"]
            ):
                return

            if not self.is_development and self.counter.register_message():
                self.io.send_json(
                    self.evaluation_system_address,
                    self.EVALUATION_SYSTEM_ENDPOINT,
                    {"uuid": raw_session.uuid, "label": raw_session.label}
                )

            self.minimum_records = self._get_min_records()

            self.io.send_json(
                self.preparation_system_address,
                self.PREPARATION_SYSTEM_ENDPOINT,
                asdict(raw_session)
            )

            if not self.shared_config["serviceFlag"]:
                break


if __name__ == "__main__":
    controller = IngestionSystemController()
    controller.run()
