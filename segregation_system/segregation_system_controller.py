"""
The controller module for the segregation system
"""

from typing import Final

from shared.loader import load_and_validate_json_file
from shared.systemsio import SystemsIO, Endpoint
from shared.address import Address
from shared.attack_risk_level import AttackRiskLevel

from segregation_system.data_balancing_model import DataBalancingModel
from segregation_system.data_balancing_view import DataBalancingView
from segregation_system.data_coverage_model import DataCoverageModel
from segregation_system.data_coverage_view import DataCoverageView
from segregation_system.data_splitter import DataSplitter
from segregation_system.prepared_sessions_db import PreparedSessionsDB, PreparedSession

class SegregationSystemController:
    """
    Manages the segregation system, handling the configuration, preparation,
    and processing of sessions, including data balancing and coverage analysis

    :ivar OUTPUT_DIR: Directory where the output files such as splits, reports,
        or logs will be stored
    :type OUTPUT_DIR: str
    :ivar configuration: Parsed and validated JSON configuration dict merged
        from the main system configuration with shared settings
    :type configuration: dict
    :ivar service_flag: Determines if the service should operate in a specific
        mode based on configuration settings
    :type service_flag: bool
    :ivar development_system_address: Address object representing the development
        system's IP and port
    :type development_system_address: Address
    :ivar io: SystemsIO instance managing communication with endpoints such as
        receiving prepared sessions and sending calibration sets
    :type io: SystemsIO
    :ivar sessions_db: Database object managing storage and retrieval of prepared
        sessions
    :type sessions_db: PreparedSessionsDB
    :ivar splitter: DataSplitter object responsible for splitting sessions into
        training, testing, and validation datasets
    :type splitter: DataSplitter
    :ivar data_balancing_view: View object generating and handling reports
        regarding data balancing operations
    :type data_balancing_view: DataBalancingView
    :ivar data_coverage_view: View object generating and handling reports
        relating to data coverage analysis
    :type data_coverage_view: DataCoverageView
    """

    OUTPUT_DIR: Final[str] = "segregation_system/output"

    def __init__(self):
        self.configuration = load_and_validate_json_file(
            "segregation_system/configuration.json",
            "segregation_system/schemas/configuration.schema.json"
        )
        self.configuration |= load_and_validate_json_file(
            "shared/json/shared_config.json",
            "shared/json/shared_config.schema.json"
        )

        self.service_flag = bool(self.configuration["serviceFlag"])
        self.development_system_address = Address(
            self.configuration["addresses"]["developmentSystem"]["ip"],
            self.configuration["addresses"]["developmentSystem"]["port"]
        )

        self.io = SystemsIO(
            [Endpoint("/prepared-session",
                      "segregation_system/schemas/prepared_session.schema.json")],
            self.configuration["addresses"]["segregationSystem"]["port"],
        )
        self.sessions_db = PreparedSessionsDB()
        self.splitter = DataSplitter(
            self.configuration["trainSplitPercentage"],
            self.configuration["testSplitPercentage"],
            self.configuration["validationSplitPercentage"],
            self.OUTPUT_DIR
        )
        self.data_balancing_view = DataBalancingView(self.OUTPUT_DIR)
        self.data_coverage_view = DataCoverageView(self.OUTPUT_DIR)

    def run(self, requested_sessions: dict[AttackRiskLevel, int] = None) -> None:
        """
        Executes the main workflow for managing session preparation and processing
        """
        received_sessions = self.sessions_db.count()
        print(f"[Controller] Initially loaded {received_sessions} sessions from the database")
        minimum_number_of_sessions = int(self.configuration["minimumNumberOfSessions"])
        while True:
            # Exit conditions check
            if requested_sessions:
                if sum(requested_sessions.values()) <= 0:
                    break
            else:
                if received_sessions >= minimum_number_of_sessions:
                    break

            prepared_session_data = self.io.receive("/prepared-session")
            prepared_session = PreparedSession(**prepared_session_data)

            if requested_sessions:
                if requested_sessions.get(prepared_session.label, 0) <= 0:
                    # Ignore the session, the user does not need it
                    continue
                requested_sessions[prepared_session.label] -= 1
            else:
                received_sessions += 1
            self.sessions_db.store(prepared_session)

        sessions = self.sessions_db.get_all()

        model = DataBalancingModel(
            balancing_tolerance=self.configuration["balancingTolerance"],
            sessions=sessions
        )
        self.data_balancing_view.build_report(model)
        requested_sessions = self.data_balancing_view.read_user_input(self.service_flag)
        if requested_sessions:
            self.run(requested_sessions)
            return

        model = DataCoverageModel(sessions)
        self.data_coverage_view.build_report(model)
        requested_sessions = self.data_coverage_view.read_user_input(self.service_flag)
        if requested_sessions:
            self.run(requested_sessions)
            return

        splits = self.splitter.split(sessions)
        self.io.send_files(self.development_system_address, "/calibration-sets", splits)
        self.sessions_db.delete_all()
        self.splitter.delete(splits)

if __name__ == "__main__":
    controller = SegregationSystemController()
    while True:
        controller.run()
