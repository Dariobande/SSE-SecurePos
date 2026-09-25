"""
This file contains the implementation of the Raw Session DB class.
"""

import sqlite3
import json
from typing import Optional

from ingestion_system.raw_session import RawSession


class RawSessionDB:
    """
    This is a helper class used by the Ingestion System to communicate with a temporary buffer.
    The temporary buffer is implemented as a SQLite database.
    It is used to temporarily store records until it is possible to create a new raw session.
    """

    TYPE_TO_COLUMN = {
        'transaction_data': 'transaction_data',
        'network_data': 'network_data',
        'location_data': 'location_data',
        'label': 'label'
    }

    def __init__(self, db_path: str = "ingestion_system/raw_sessions.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        query = """
                CREATE TABLE IF NOT EXISTS partial_sessions \
                ( \
                    uuid \
                    VARCHAR \
                ( \
                    32 \
                ) PRIMARY KEY,
                    transaction_data TEXT,
                    network_data TEXT,
                    location_data TEXT,
                    label TEXT -- Now stores JSON blob like the others
                    );
                """
        with self.conn:
            self.conn.execute(query)

    def store(self, r: dict):
        """
        Stores a partial record.
        Now uniformly dumps JSON for ALL types, including labels.
        """
        uuid = r.get('uuid')
        record_type = r.get('type')

        target_col = self.TYPE_TO_COLUMN.get(record_type)

        if not uuid or not target_col:
            print(f"[RawSessionDB] Error: Invalid UUID or Type in record: {r}")
            return

        val_to_store = json.dumps(r)

        with self.conn:
            self.conn.execute(
                "INSERT OR IGNORE INTO partial_sessions (uuid) VALUES (?)",
                (uuid,)
            )

            query = f"UPDATE partial_sessions SET {target_col} = ? WHERE uuid = ?"
            self.conn.execute(query, (val_to_store, uuid))

    def get_session(self, uuid: str, minimum_records: int) -> Optional[RawSession]:
        """
        Returns the session ONLY if all data parts are present.
        """
        query = """
                SELECT transaction_data,network_data, location_data, label FROM partial_sessions WHERE uuid = ?
                """
        cursor = self.conn.cursor()
        cursor.execute(query, (uuid,))
        row = cursor.fetchone()

        if not row:
            return None

        trans_blob, net_blob, loc_blob, label_blob = row

        records = [trans_blob, net_blob, loc_blob, label_blob]
        if sum(x is not None for x in records) < minimum_records:
            return None

        t_data = json.loads(trans_blob)
        n_data = json.loads(net_blob)
        l_data = json.loads(loc_blob)

        final_label_value = json.loads(label_blob).get('label') if label_blob else None

        return RawSession(
            uuid=uuid,
            timestamp=t_data.get('timestamp', []),
            amount=t_data.get('amount', []),
            source_ip=n_data.get('source_ip', []),
            dest_ip=n_data.get('dest_ip', []),
            longitude=l_data.get('longitude', []),
            latitude=l_data.get('latitude', []),
            label=final_label_value
        )

    def remove(self, uuid: str):
        """
        Removes a session from the database.
        """
        with self.conn:
            self.conn.execute("DELETE FROM partial_sessions WHERE uuid = ?", (uuid,))
