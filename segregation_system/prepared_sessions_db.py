"""
A module for managing a database of prepared sessions
"""

from dataclasses import dataclass
import sqlite3

from shared.attack_risk_level import AttackRiskLevel

@dataclass
class PreparedSession:
    """
    Represents a collection of features ready to be used as inputs to a classifier
    """
    uuid: str
    label: AttackRiskLevel
    mad_timestamps: float | None = None
    mad_amounts: float | None = None
    median_longitude: float | None = None
    median_latitude: float | None = None
    median_source_ip: int | None = None
    median_destination_ip: int | None = None

class PreparedSessionsDB:
    """
    Manages a database for storing and retrieving prepared sessions

    :ivar conn: The active SQLite connection used to communicate with the database
    :type conn: sqlite3.Connection
    """

    def __init__(self, database_name: str = "segregation_system/prepared_sessions.db"):
        self.conn = sqlite3.connect(database_name)
        self._create_schema()

    def _create_schema(self) -> None:
        """
        Creates the `prepared_sessions` table in the database if it does not already exist
        """
        query = """
        CREATE TABLE IF NOT EXISTS prepared_sessions (
            uuid VARCHAR(32) PRIMARY KEY,
            mad_timestamps REAL,
            mad_amounts REAL,
            median_longitude REAL,
            median_latitude REAL,
            median_source_ip INTEGER,
            median_destination_ip INTEGER,
            label VARCHAR(32)
        );
        """
        with self.conn:
            self.conn.execute(query)

    def store(self, prepared_session: PreparedSession) -> None:
        """
        Stores a prepared session into the database
        """
        query = """
        INSERT INTO prepared_sessions (
            uuid,
            mad_timestamps, 
            mad_amounts, 
            median_longitude, 
            median_latitude,
            median_source_ip, 
            median_destination_ip,
            label
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        values = (
            prepared_session.uuid,
            prepared_session.mad_timestamps,
            prepared_session.mad_amounts,
            prepared_session.median_longitude,
            prepared_session.median_latitude,
            prepared_session.median_source_ip,
            prepared_session.median_destination_ip,
            prepared_session.label
        )

        with self.conn:
            self.conn.execute(query, values)
        #print(f"[SessionsDB] Stored {prepared_session} session in the database")

    def get_all(self) -> list[PreparedSession]:
        """
        Retrieves all prepared sessions from the database
        """
        query = """
        SELECT *
        FROM prepared_sessions
        """

        cursor = self.conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            session = PreparedSession(
                uuid=row[0],
                mad_timestamps=row[1],
                mad_amounts=row[2],
                median_longitude=row[3],
                median_latitude=row[4],
                median_source_ip=row[5],
                median_destination_ip = row[6],
                label = row[7]
            )
            results.append(session)
        print(f"[SessionsDB] Loaded {len(results)} sessions from the database")
        return results

    def delete_all(self) -> None:
        """
        Deletes all prepared sessions from the database
        """
        query = "DELETE FROM prepared_sessions"

        with self.conn:
            self.conn.execute(query)
        print("[SessionsDB] Deleted all sessions from the database")

    def count(self) -> int:
        """
        Returns the total number of prepared sessions stored in the database
        """
        query = "SELECT COUNT(*) FROM prepared_sessions"

        cursor = self.conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()

        # fetchone() returns a tuple like (N,), so we return the first element
        return result[0]
