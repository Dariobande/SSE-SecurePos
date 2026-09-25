"""
Controller module for the Preparation System.

This module defines the PreparationSystemController class, which orchestrates
the data preparation pipeline. It receives raw sessions, uses the DataCorrector
to clean the data, uses the FeatureExtractor to derive features, and then
forwards the prepared data to the appropriate downstream system (Classification
or Segregation) based on the session type.
"""
from requests import exceptions as requests_exceptions
from ingestion_system.raw_session import RawSession
from shared.systemsio import SystemsIO, Endpoint
from shared.address import Address
from shared.loader import load_and_validate_json_file

from preparation_system.data_corrector import DataCorrector
from preparation_system.feature_extractor import FeatureExtractor


# pylint: disable=too-few-public-methods
class PreparationSystemController:
    """
    Controls the operations of the Preparation System.

    This controller manages the lifecycle of data preparation. It initializes
    the necessary components (DataCorrector, FeatureExtractor), sets up
    communication endpoints, and orchestrates the flow of processing raw
    sessions into prepared data ready for classification or segregation.
    """
    CONFIG_PATH = "preparation_system/json/config.json"
    CONFIG_SCHEMA_PATH = "preparation_system/json/config_schema.json"
    SHARED_CONFIG_PATH = "shared/json/shared_config.json"
    SHARED_CONFIG_SCHEMA_PATH = "shared/json/shared_config.schema.json"
    RAW_SESSION_SCHEMA_PATH = "preparation_system/json/raw_session.schema.json"
    PROCESS_ENDPOINT = "/process"

    def __init__(self):
        """
        Initializes the Preparation System Controller.

        Loads the system and shared configurations, sets up the input/output
        endpoints for receiving raw sessions, and initializes the DataCorrector
        and FeatureExtractor components with the loaded settings.
        """
        self.config = load_and_validate_json_file(self.CONFIG_PATH, self.CONFIG_SCHEMA_PATH)
        self.shared_config = load_and_validate_json_file(
            self.SHARED_CONFIG_PATH,
            self.SHARED_CONFIG_SCHEMA_PATH
        )

        prep_cfg = self.shared_config["addresses"]["preparationSystem"]
        self.io = SystemsIO(
            [Endpoint(self.PROCESS_ENDPOINT, self.RAW_SESSION_SCHEMA_PATH)],
            port=int(prep_cfg["port"])
        )

        self.classification_address = Address(
            self.shared_config["addresses"]["classificationSystem"]["ip"],
            int(self.shared_config["addresses"]["classificationSystem"]["port"])
        )
        self.segregation_address = Address(
            self.shared_config["addresses"]["segregationSystem"]["ip"],
            int(self.shared_config["addresses"]["segregationSystem"]["port"])
        )

        self.corrector = DataCorrector(float(self.config["maxTransactionsAmount"]))
        self.extractor = FeatureExtractor(self.config["extractedFeatures"])

    def run(self):
        """
        Runs the main processing loop of the Preparation System.

        Continuously listens for incoming RawSession data. Upon receipt, the data
        is corrected (missing values filled, outliers clipped), features are
        extracted, and the resulting prepared session is sent to either the
        Segregation System (in development phase) or the Classification System
        (in production phase).
        """
        prep_cfg = self.shared_config["addresses"]["preparationSystem"]
        print(
            f"[PreparationSystem] Listening on {prep_cfg['ip']}:{prep_cfg['port']}. "
            f"Development phase: {self.shared_config['systemPhase']['developmentPhase']}"
        )

        while True:
            data = self.io.receive(self.PROCESS_ENDPOINT)
            if data is None:
                continue

            try:
                session = RawSession(**data)
            except TypeError as e:
                print(f"[PreparationSystem] Invalid RawSession received: {e}")
                continue

            # First handle missing samples, then clip absolute outliers
            session = self.corrector.correct_missing_samples(session)
            session = self.corrector.correct_absolute_outiers(session)

            features = self.extractor.extract_features(session)

            if self.shared_config["systemPhase"]["developmentPhase"]:
                target = self.segregation_address
                endpoint = "/prepared-session"
            else:
                target = self.classification_address
                endpoint = "/prepared-session"

            try:
                SystemsIO.send_json(target, endpoint, features)
            except requests_exceptions.RequestException as exc:
                print(f"[PreparationSystem] Failed to send prepared data: {exc}")

            if not self.shared_config["serviceFlag"]:
                break


if __name__ == "__main__":
    controller = PreparationSystemController()
    controller.run()
