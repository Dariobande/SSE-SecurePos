"""
This file contains the implementation of the LabelsBuffer class
"""

import sqlite3
from typing import List
from evaluation_system.classifier_evaluation_model import LabelsRecord


class LabelsBufferDB:
    """
        Manages persistent storage of prediction and actual labels using SQLite.
        Implements data pairing (upsert) via UUID and checks for evaluation batch sufficiency.
    """

    def __init__(self, db_path="evaluation_system/buffer.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Create the table for the label records
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS labels_buffer (
                uuid TEXT PRIMARY KEY,
                predict_label TEXT,
                actual_label TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def store_label(self, uuid: str, predict_label: str = None, actual_label: str = None):
        """
        Upsert logic: If record exists, update it. If not, create it.
        This handles the async nature of possibly receiving the predict_label
         and the actual_label at different times.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM labels_buffer WHERE uuid = ?", (uuid,))
        row = cursor.fetchone()

        if row:
            if predict_label:
                cursor.execute(
                    "UPDATE labels_buffer SET predict_label = ? WHERE uuid = ?",
                    (predict_label, uuid)
                )
            if actual_label:
                cursor.execute(
                    "UPDATE labels_buffer SET actual_label = ? WHERE uuid = ?",
                    (actual_label, uuid)
                )
        else:
            cursor.execute(
                "INSERT INTO labels_buffer (uuid, predict_label, actual_label) VALUES (?, ?, ?)",
                (uuid, predict_label, actual_label)
            )

        conn.commit()
        conn.close()

    def sufficient_labels_query(self, min_labels: int) -> bool:
        """Checks if we have enough COMPLETE records (both predicted and actual labels)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) "
            "FROM labels_buffer "
            "WHERE predict_label IS NOT NULL AND actual_label IS NOT NULL"
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count >= min_labels

    def get_labels(self) -> List[LabelsRecord]:
        """Retrieve all the COMPLETE records (both predicted and actual labels)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT uuid, predict_label, actual_label "
            "FROM labels_buffer "
            "WHERE predict_label IS NOT NULL AND actual_label IS NOT NULL")
        rows = cursor.fetchall()
        conn.close()

        return [LabelsRecord(uuid=r[0], predict_label=r[1], actual_label=r[2]) for r in rows]

    def delete_labels(self):
        """Clears the buffer after evaluation."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Only delete the records that were complete
        cursor.execute(
            "DELETE FROM labels_buffer "
            "WHERE predict_label IS NOT NULL AND actual_label IS NOT NULL"
        )
        conn.commit()
        conn.close()
