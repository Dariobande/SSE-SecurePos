"""
Defines the model for the data coverage report
"""

from typing import Final

import numpy as np

from segregation_system.prepared_sessions_db import PreparedSession
from shared.feature import Feature

class DataCoverageModel:
    """
    Represents the model for the data coverage report

    :ivar normalized_features_samples: A dictionary that stores [0, 1] normalized feature samples
    :type normalized_features_samples: dict[Feature, np.ndarray]
    """

    # Feature -> (Min, Max)
    FEATURE_BOUNDS: Final[dict[Feature, tuple[int, int]]] = {
        Feature.MAD_TIMESTAMPS: (0, 600),
        Feature.MAD_AMOUNTS: (0, 1000),
        Feature.MEDIAN_LONGITUDE: (-180, 180),
        Feature.MEDIAN_LATITUDE: (-90, 90),
        Feature.MEDIAN_SOURCE_IP: (0, 4294967295),
        Feature.MEDIAN_DESTINATION_IP: (0, 4294967295)
    }

    def __init__(self, sessions: list[PreparedSession]):
        self.normalized_features_samples = {}

        if not sessions:
            for feature in self.FEATURE_BOUNDS:
                self.normalized_features_samples[feature] = np.array([])
            return

        for feature, (t_min, t_max) in self.FEATURE_BOUNDS.items():
            raw_values = [getattr(s, feature.value) for s in sessions]
            arr = np.array(raw_values, dtype=np.float32)
            np.clip(arr, t_min, t_max, out=arr)
            arr -= t_min
            arr /= t_max - t_min
            self.normalized_features_samples[feature] = arr
