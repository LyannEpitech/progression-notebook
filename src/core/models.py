"""Modèles de données."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class SuspicionType(str, Enum):
    """Types de comportements suspects détectables."""
    COPIEUR = "copieur"
    PIC_ISOLE = "pic_isole"
    MONTAGNES_RUSSES = "montagnes_russes"
    COPIE_COLLECTIVE = "copie_collective"


@dataclass
class SkillBreakdown:
    """Détail d'une compétence évaluée."""
    count: int = 0
    passed: int = 0
    crashed: int = 0
    mandatory_failed: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calcule le taux de réussite."""
        if self.count == 0:
            return 0.0
        return (self.passed / self.count) * 100


@dataclass
class ActivityResult:
    """Résultat d'une activité (rendu/jour)."""
    id: int = 0
    student_id: str = ""
    unit: str = ""
    project_slug: str = ""
    day_label: str = ""
    test_type: str = "delivery"
    
    # Notations
    mark: Optional[float] = None
    prerequisites_mark: Optional[float] = None
    virtual_mark: Optional[float] = None
    
    # Détails
    skill_breakdowns: Dict[str, SkillBreakdown] = field(default_factory=dict)
    style_penalty: Optional[int] = None
    coverage_branch: Optional[float] = None
    coverage_line: Optional[float] = None
    
    # Métadonnées
    date: Optional[datetime] = None
    commit: Optional[str] = None
    failure_flags: List[str] = field(default_factory=list)
    
    @property
    def test_percentage(self) -> float:
        """Calcule le pourcentage global de tests réussis."""
        total_count = 0
        total_passed = 0
        for skill in self.skill_breakdowns.values():
            total_count += skill.count
            total_passed += skill.passed
        
        if total_count == 0:
            return 0.0
        return (total_passed / total_count) * 100


@dataclass
class Student:
    """Représentation d'un étudiant."""
    id: str = ""
    display_name: str = ""
    results: Dict[str, ActivityResult] = field(default_factory=dict)
    
    @property
    def average_score(self) -> float:
        """Calcule la moyenne des scores."""
        if not self.results:
            return 0.0
        scores = [r.test_percentage for r in self.results.values()]
        return sum(scores) / len(scores)
    
    @property
    def days_completed(self) -> int:
        """Nombre de jours complétés."""
        return len(self.results)


@dataclass
class SuspicionResult:
    """Résultat d'une détection de comportement suspect."""
    student_id: str = ""
    suspicion_type: SuspicionType = SuspicionType.COPIEUR
    score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class DetectionConfig:
    """Configuration pour les algorithmes de détection."""
    # Copieurs
    copieur_tolerance: float = 1.0
    copieur_min_days: int = 4
    copieur_min_ratio: float = 0.4
    
    # Pics isolés
    pic_seuil_haut: float = 70.0
    pic_seuil_bas: float = 30.0
    pic_fenetre: int = 2
    
    # Montagnes russes
    montagne_seuil_variation: float = 30.0
    montagne_min_alternances: int = 3
    
    # Copies collectives
    collectif_tolerance: float = 0.0
    collectif_min_eleves: int = 3
    collectif_min_jours: int = 2
