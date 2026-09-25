"""
Module for extracting statistical features from raw session data.

This module defines the FeatureExtractor class, which is responsible for
calculating various statistical metrics (such as mean, median, variance, etc.)
from the data fields of a RawSession object. These features are intended
for use in downstream classification or analysis tasks.
"""
from statistics import median
from typing import Dict, Any

from ingestion_system.raw_session import RawSession


# pylint: disable=too-few-public-methods
class FeatureExtractor:
    """
    Extracts statistical features from a corrected RawSession.

    This class is responsible for computing various statistical metrics from the
    data fields of a RawSession object. It assumes that the input session has
    already been processed by the DataCorrector, meaning that numeric sequences
    contain no None values and absolute outliers have been handled.
    """

    def __init__(self, extracted_features: list[str]):
        self.extracted_features = extracted_features

    @staticmethod
    def _mad(values: list[float]) -> float:
        if not values:
            return 0.0
        m = median(values)
        deviations = [abs(v - m) for v in values]
        return float(median(deviations))

    @staticmethod
    def _ip_to_int(ip: str) -> int:
        parts = ip.split(".")
        if len(parts) != 4:
            return 0
        try:
            return (
                (int(parts[0]) << 24)
                + (int(parts[1]) << 16)
                + (int(parts[2]) << 8)
                + int(parts[3])
            )
        except ValueError:
            return 0

    def extract_features(self, session: RawSession) -> Dict[str, Any]:
        """
        Extracts the configured statistical features from a corrected RawSession.

        This method computes features such as Median Absolute Deviation (MAD) for
        timestamps and amounts, and median values for coordinates and IP addresses,
        based on the configuration provided during initialization.
        """
        result: Dict[str, Any] = {"uuid": session.uuid}

        if session.label is not None:
            result["label"] = session.label

        timestamps = list(session.timestamp)
        amounts = list(session.amount)
        longitudes = list(session.longitude)
        latitudes = list(session.latitude)
        source_ips = list(session.source_ip)
        dest_ips = list(session.dest_ip)

        if "mad_timestamps" in self.extracted_features:
            result["mad_timestamps"] = self._mad(timestamps)

        if "mad_amounts" in self.extracted_features:
            result["mad_amounts"] = self._mad(amounts)

        if "median_longitude" in self.extracted_features:
            result["median_longitude"] = float(median(longitudes)) if longitudes else 0.0

        if "median_latitude" in self.extracted_features:
            result["median_latitude"] = float(median(latitudes)) if latitudes else 0.0

        if "median_source_ip" in self.extracted_features:
            ip_ints = [self._ip_to_int(ip) for ip in source_ips]
            result["median_source_ip"] = int(median(ip_ints)) if ip_ints else 0

        if "median_destination_ip" in self.extracted_features:
            ip_ints = [self._ip_to_int(ip) for ip in dest_ips]
            result["median_destination_ip"] = int(median(ip_ints)) if ip_ints else 0

        return result
