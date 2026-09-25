import time
import uuid
import threading
from typing import Final
import random
import csv
import os

import numpy as np

from shared.address import Address
from shared.attack_risk_level import AttackRiskLevel
from shared.loader import load_and_validate_json_file
from shared.systemsio import SystemsIO, Endpoint

class Simulator:
    """
    Simulates the client side systems sending data to the ingestion system

    :ivar N_SAMPLES: Number of samples generated per record type
    :type N_SAMPLES: int
    """
    N_SAMPLES: Final[int] = 10

    def __init__(self):
        self.io = SystemsIO(
            [Endpoint("/timestamp", "simulator/schemas/timestamp.schema.json")],
            8000
        )
        configuration = load_and_validate_json_file(
            "shared/json/shared_config.json",
            "shared/json/shared_config.schema.json"
        )
        self.ingestion_system_address = Address(
            configuration["addresses"]["ingestionSystem"]["ip"],
            configuration["addresses"]["ingestionSystem"]["port"]
        )

    def _generate_label_record(self, id: str, label: AttackRiskLevel) -> dict:
        return {
            "type": "label",
            "uuid": id,
            "label": label.value
        }

    def _generate_transaction_record(self, id: str, label: AttackRiskLevel) -> dict:
        # Transaction window, Min amount, Max amount
        transaction_config = {
            AttackRiskLevel.NORMAL: (300, 10, 190),
            AttackRiskLevel.MODERATE: (60, 150, 500),
            AttackRiskLevel.HIGH: (15, 400, 1000)
        }
        window, min_amt, max_amt = transaction_config[label]
        offsets = np.random.choice(
            range(window),
            size=self.N_SAMPLES,
            replace=(window < self.N_SAMPLES)
        )
        amounts = np.random.uniform(min_amt, max_amt, self.N_SAMPLES)
        return {
            "type": "transaction_data",
            "uuid": id,
            "timestamp": offsets.tolist(),
            "amount": amounts.tolist()
        }

    def _generate_location_record(self, id: str, label: AttackRiskLevel) -> dict:
        base_lat = np.random.uniform(-90, 90)
        base_lon = np.random.uniform(-180, 180)
        # Noise calculation
        if label == AttackRiskLevel.NORMAL:
            # Low risk: Very tight cluster (walking distance, ~1km max variation)
            # 0.01 degrees is roughly 1.1km
            lat_noise = np.random.normal(0, 0.005, self.N_SAMPLES)
            lon_noise = np.random.normal(0, 0.005, self.N_SAMPLES)
        elif label == AttackRiskLevel.MODERATE:
            # Moderate: City-wide travel (10-20km variation)
            lat_noise = np.random.normal(0, 0.1, self.N_SAMPLES)
            lon_noise = np.random.normal(0, 0.1, self.N_SAMPLES)
        else:  # High Risk
            # "Impossible Travel": Start locally, but insert huge jumps
            # Base noise (local)
            lat_noise = np.random.normal(0, 0.01, self.N_SAMPLES)
            lon_noise = np.random.normal(0, 0.01, self.N_SAMPLES)
            # Pick 3 random indices out of the 10 transactions to "teleport"
            jump_indices = np.random.choice(range(10), 3, replace=False)
            # Add huge coordinates to these indices (simulating VPN switching or stolen session)
            lat_noise[jump_indices] += np.random.uniform(20, 50, 3) * np.random.choice([-1, 1], 3)
            lon_noise[jump_indices] += np.random.uniform(50, 120, 3) * np.random.choice([-1, 1], 3)
        # Apply noise to base
        latitudes = base_lat + lat_noise
        longitudes = base_lon + lon_noise
        # Clip to valid geo ranges
        latitudes = np.clip(latitudes, -90, 90)
        longitudes = np.clip(longitudes, -180, 180)
        return {
            "type": "location_data",
            "uuid": id,
            "longitude": longitudes.tolist(),
            "latitude": latitudes.tolist()
        }

    def _generate_ip_record(self, id: str, label: AttackRiskLevel):
        def _generate_ip_sequence(label: AttackRiskLevel) -> list[str]:
            ip_history = []
            # Establish a "Home" or Base IP for this entity
            # This simulates a user mostly staying on one subnet unless hopping
            base_o1 = np.random.randint(1, 223)
            base_o2 = np.random.randint(0, 255)
            base_o3 = np.random.randint(0, 255)
            for _ in range(self.N_SAMPLES):
                # The 4th octet usually changes every request even for normal users
                o4 = np.random.randint(0, 255)
                # Current octets start as the base octets
                curr_o1 = base_o1
                curr_o2 = base_o2
                # Apply Risk Logic (Simulate IP Hopping / Proxy Rotation)
                if label == AttackRiskLevel.HIGH:
                    # 30% chance per log entry to look like a completely different network
                    if np.random.random() > 0.7:
                        curr_o1 = np.random.randint(1, 223)
                        curr_o2 = np.random.randint(0, 255)
                # Format and append
                ip_history.append(f"{curr_o1}.{curr_o2}.{base_o3}.{o4}")
            return ip_history
        source_ips = _generate_ip_sequence(label)
        dest_ips = _generate_ip_sequence(label)
        return {
            "type": "network_data",
            "uuid": id,
            "source_ip": source_ips,
            "dest_ip": dest_ips
        }

    def _generate_records(self) -> tuple[dict, dict, dict, dict]:
        id = uuid.uuid4().hex
        label = random.choices(
            list(AttackRiskLevel),
            weights=[0.45, 0.30, 0.25],
            k=1
        )[0]
        label_record = self._generate_label_record(id, label)
        transaction_record = self._generate_transaction_record(id, label)
        location_record = self._generate_location_record(id, label)
        ip_record = self._generate_ip_record(id, label)
        return label_record, transaction_record, location_record, ip_record

    def run(self, sessions: int = 1) -> None:
        """
        Sends simulated records to the ingestion system
        """
        while sessions > 0:
            records = self._generate_records()
            for record in list(records):
                self.io.send_json(self.ingestion_system_address, "/record", record)
            sessions -= 1

    def elasticity_test_production_phase(self):
        """
        Performs an elasticity test on the production phase.
        Results are saved in a CSV file
        """
        csv_filename = "elasticity_test_production_phase.csv"
        if not os.path.exists(csv_filename):
            with open(csv_filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["n_sessions", "response_time_ms"])
        for n in range(100, 800, 50):
            start_ts = int(time.time() * 1000)
            self.run(n)
            for _ in range(n):
                self.io.receive("/timestamp")
            end_ts = int(time.time() * 1000)
            diff_ms = end_ts - start_ts
            with open(csv_filename, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([n, diff_ms])
            print(f"[Iteration N={n}] Processed {n} sessions in {diff_ms}ms")
            time.sleep(10)

    def elasticity_test_development_phase(self):
        """
        Performs an elasticity test on the development phase.
        Results are saved in a CSV file
        """
        def _generator_job():
            print("[Simulator] Generator thread started")
            while True:
                self.run(100000000)
        def _observer_job():
            print("[Simulator] Timestamp observer started")
            csv_filename = "elasticity_test_development_phase.csv"
            start_ts = int(time.time() * 1000)
            with open(csv_filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["n_classifiers", "response_time_ms"])
                received_classifiers = 0
                while True:
                    final_json = self.io.receive("/timestamp")
                    rec_ts = int(final_json["timestamp"])
                    latency = rec_ts - start_ts
                    received_classifiers += 1
                    writer.writerow([received_classifiers, latency])
                    f.flush()
                    print(f"[Receiver] Logged ({received_classifiers}, {latency})")

        threading.Thread(target=_observer_job(), daemon=True).start()
        threading.Thread(target=_generator_job(), daemon=True).start()

        # --- Keep Main Alive ---
        while True:
            time.sleep(1)

if __name__ == "__main__":
    simulator = Simulator()
    simulator.elasticity_test_production_phase()
    #simulator.elasticity_test_development_phase()
