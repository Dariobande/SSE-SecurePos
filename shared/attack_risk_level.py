from enum import Enum

class AttackRiskLevel(str, Enum):
    """
    Enum for the classifier label
    """
    NORMAL = "normal"
    MODERATE = "moderate"
    HIGH = "high"
