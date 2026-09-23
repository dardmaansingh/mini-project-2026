"""
Alert Severity Definitions and Classification Standards.
"""

from enum import Enum


class AlertSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @classmethod
    def from_string(cls, val: str) -> "AlertSeverity":
        val_upper = str(val).upper()
        for member in cls:
            if member.value == val_upper:
                return member
        return cls.LOW
