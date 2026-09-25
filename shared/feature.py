from enum import Enum

class Feature(str, Enum):
    """
    Enum representing all the possible classifier inputs
    """
    MAD_TIMESTAMPS = "mad_timestamps"
    MAD_AMOUNTS = "mad_amounts"
    MEDIAN_LONGITUDE = "median_longitude"
    MEDIAN_LATITUDE = "median_latitude"
    MEDIAN_SOURCE_IP = "median_source_ip"
    MEDIAN_DESTINATION_IP = "median_destination_ip"
