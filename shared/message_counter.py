"""
A module to track the current system phase (evaluation or production)
"""

from typing import Final

import json
from pathlib import Path

from shared.loader import load_and_validate_json_file

class PhaseMessageCounter:
    """Tracks how many messages were seen in each phase and flips phases at window boundaries"""

    STATE_SCHEMA_PATH: Final[str] = "shared/json/message_counter_state.schema.json"

    def __init__(
        self,
        state_file: str,
        evaluation_window: int,
        production_window: int,
    ):
        self.state_path = Path(state_file)
        self.evaluation_window = evaluation_window
        self.production_window = production_window

    def is_evaluation(self) -> bool:
        state = load_and_validate_json_file(
            str(self.state_path),
            self.STATE_SCHEMA_PATH
        )
        return bool(state["is_evaluation"])

    def register_message(self) -> bool:
        """Decrement the counter and return whether the system is currently in the evaluation phase"""
        state = load_and_validate_json_file(
            str(self.state_path),
            self.STATE_SCHEMA_PATH
        )
        is_evaluation = bool(state["is_evaluation"])
        counter = int(state["counter"])

        if counter <= 0:
            is_evaluation = not is_evaluation
            counter = self.evaluation_window if is_evaluation else self.production_window
        else:
            counter -= 1

        state = {"is_evaluation": is_evaluation, "counter": counter}
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with self.state_path.open("w", encoding="utf-8") as handle:
            json.dump(state, handle)

        return is_evaluation
