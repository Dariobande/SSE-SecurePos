"""
Module for correcting and cleaning raw session data.

This module defines the DataCorrector class, which provides methods to handle
missing values (e.g., by filling with the mode) and to clip absolute outliers
(e.g., capping transaction amounts) in RawSession objects, ensuring data quality
before feature extraction.
"""
from ingestion_system.raw_session import RawSession


class DataCorrector:
    """
    Corrects and cleans RawSession data.

    This class provides functionality to handle missing samples in session data
    (e.g., by imputing them with the mode) and to clip absolute outliers, such
    as ensuring transaction amounts do not exceed a specified maximum.
    """
    def __init__(self, max_transactions_amount: float):
        self.max_transactions_amount = max_transactions_amount

    def correct_missing_samples(self, session: RawSession) -> RawSession:
        """
        Handles missing samples in the session data by imputing them with the mode.

        Iterates through the data fields (timestamp, amount, coordinates, IPs) and
        replaces `None` values with the most frequent non-None value in the sequence.
        If a sequence contains only `None` values, they are replaced with a default
        value (0.0 or "0.0.0.0").
        """

        def _fill_with_mode(values, ips=False):
            non_null = [v for v in values if v is not None]
            if not non_null:
                # All values are None: assign a default value (0.0) or "0.0.0.0" for IPs
                return ["0.0.0.0" if ips else 0.0 for _ in values]

            # compute most frequent value (mode)
            freq = {}
            for v in non_null:
                freq[v] = freq.get(v, 0) + 1
            mode_value = max(freq.items(), key=lambda item: item[1])[0]

            return [mode_value if v is None else v for v in values]

        if session.timestamp:
            session.timestamp = _fill_with_mode(session.timestamp)
        if session.amount:
            session.amount = _fill_with_mode(session.amount)
        if session.longitude:
            session.longitude = _fill_with_mode(session.longitude)
        if session.latitude:
            session.latitude = _fill_with_mode(session.latitude)
        if session.source_ip:
            session.source_ip = _fill_with_mode(session.source_ip, ips=True)
        if session.dest_ip:
            session.dest_ip = _fill_with_mode(session.dest_ip, ips=True)

        return session

    def correct_absolute_outiers(self, session: RawSession) -> RawSession:
        """
        Clips absolute outliers in the session data.

        Specifically, this method caps transaction amounts to a maximum configured
        value (`max_transactions_amount`) to prevent extreme values from skewing
        analysis.
        """
        if session.amount:
            session.amount = [
                min(a, self.max_transactions_amount) if a is not None else None
                for a in session.amount
            ]

        return session
