"""
This file contains the Raw Session DTO class.
"""

from typing import List, Optional

from dataclasses import dataclass
from shared.attack_risk_level import AttackRiskLevel


# pylint: disable=too-many-instance-attributes
@dataclass
class RawSession:
    """
    Raw Session DTO.
    """
    uuid: str
    timestamp: List[Optional[float]]
    amount: List[Optional[float]]
    source_ip: List[Optional[str]]
    dest_ip: List[Optional[str]]
    longitude: List[Optional[float]]
    latitude: List[Optional[float]]
    label: Optional[AttackRiskLevel] = None
