"""Core module - Logique métier pure."""

from src.core.detection import DetectionEngine
from src.core.scoring import ScoringEngine
from src.core.models import (
    Student, 
    ActivityResult, 
    SuspicionResult, 
    SuspicionType,
    DetectionConfig
)

__all__ = [
    "DetectionEngine",
    "ScoringEngine",
    "Student",
    "ActivityResult",
    "SuspicionResult",
    "SuspicionType",
    "DetectionConfig",
]
