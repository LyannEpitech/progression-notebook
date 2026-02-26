"""Moteur de détection des comportements suspects."""

from typing import List, Dict, Any, Tuple, Set
import pandas as pd
import numpy as np

from src.core.models import SuspicionResult, SuspicionType, DetectionConfig


class DetectionEngine:
    """Moteur de détection des comportements suspects chez les étudiants."""
    
    def __init__(self, df: pd.DataFrame, config: DetectionConfig = None):
        """
        Initialise le moteur de détection.
        
        Args:
            df: DataFrame avec index=student_id, columns=jours, values=scores
            config: Configuration des seuils de détection
        """
        self.df = df
        self.config = config or DetectionConfig()
        self.results: List[SuspicionResult] = []
    
    def detect_all(self) -> List[SuspicionResult]:
        """Lance toutes les détections et retourne les résultats agrégés."""
        self.results = []
        
        self.results.extend(self.detect_copieurs())
        self.results.extend(self.detect_pics_isoles())
        self.results.extend(self.detect_montagnes_russes())
        self.results.extend(self.detect_copies_collectives())
        
        # Trier par score décroissant
        self.results.sort(key=lambda x: x.score, reverse=True)
        return self.results
    
    def detect_copieurs(self) -> List[SuspicionResult]:
        """
        Détecte les paires d'étudiants avec des scores très similaires.
        
        Suspect si ≥N jours avec |score_A - score_B| ≤ tolerance,
        surtout si jours consécutifs.
        """
        if len(self.df) < 2:
            return []
        
        results = []
        students = self.df.index.tolist()
        
        for i in range(len(students)):
            for j in range(i + 1, len(students)):
                s1, s2 = students[i], students[j]
                scores1, scores2 = self.df.loc[s1], self.df.loc[s2]
                
                # Jours avec scores similaires
                similar_days = []
                consecutive_streak = 0
                max_consecutive = 0
                last_similar = -1
                
                for idx, day in enumerate(self.df.columns):
                    if abs(scores1[day] - scores2[day]) <= self.config.copieur_tolerance:
                        similar_days.append(day)
                        if last_similar == idx - 1:
                            consecutive_streak += 1
                        else:
                            consecutive_streak = 1
                        max_consecutive = max(max_consecutive, consecutive_streak)
                        last_similar = idx
                
                ratio = len(similar_days) / len(self.df.columns)
                
                if (len(similar_days) >= self.config.copieur_min_days and 
                    ratio >= self.config.copieur_min_ratio):
                    
                    # Calculer le score de suspicion
                    base_score = 40
                    bonus_sim = min((len(similar_days) - 3) * 5, 20)
                    bonus_consec = 15 if max_consecutive >= 2 else 0
                    total_score = min(base_score + bonus_sim + bonus_consec, 100)
                    
                    # Créer le résultat pour s1
                    results.append(SuspicionResult(
                        student_id=s1,
                        suspicion_type=SuspicionType.COPIEUR,
                        score=total_score,
                        details={
                            "partner": s2,
                            "similar_days": len(similar_days),
                            "max_consecutive": max_consecutive,
                            "ratio": ratio,
                            "days": similar_days
                        },
                        description=(
                            f"{len(similar_days)} jours similaires avec {s2.split('@')[0]} "
                            f"(dont {max_consecutive} consécutifs)"
                        )
                    ))
                    
                    # Créer le résultat pour s2
                    results.append(SuspicionResult(
                        student_id=s2,
                        suspicion_type=SuspicionType.COPIEUR,
                        score=total_score,
                        details={
                            "partner": s1,
                            "similar_days": len(similar_days),
                            "max_consecutive": max_consecutive,
                            "ratio": ratio,
                            "days": similar_days
                        },
                        description=(
                            f"{len(similar_days)} jours similaires avec {s1.split('@')[0]} "
                            f"(dont {max_consecutive} consécutifs)"
                        )
                    ))
        
        return results
    
    def detect_pics_isoles(self) -> List[SuspicionResult]:
        """
        Détecte les pics isolés - un jour >70% entouré de jours <30%.
        Signe d'une aide ponctuelle extérieure.
        """
        results = []
        
        for student in self.df.index:
            scores = self.df.loc[student]
            
            for i, day in enumerate(self.df.columns):
                score = scores[day]
                
                # Vérifier si c'est un pic haut
                if score < self.config.pic_seuil_haut:
                    continue
                
                # Calculer moyenne avant et après
                avant = scores[max(0, i - self.config.pic_fenetre):i]
                apres = scores[i + 1:min(len(scores), i + 1 + self.config.pic_fenetre)]
                
                moyenne_avant = avant.mean() if len(avant) > 0 else 100
                moyenne_apres = apres.mean() if len(apres) > 0 else 100
                
                # Suspect si entouré de mauvais scores
                if (moyenne_avant < self.config.pic_seuil_bas and 
                    moyenne_apres < self.config.pic_seuil_bas):
                    
                    results.append(SuspicionResult(
                        student_id=student,
                        suspicion_type=SuspicionType.PIC_ISOLE,
                        score=60.0,
                        details={
                            "day": day,
                            "score": score,
                            "moyenne_avant": moyenne_avant,
                            "moyenne_apres": moyenne_apres,
                            "contexte": f"{moyenne_avant:.0f}% → {score:.0f}% → {moyenne_apres:.0f}%"
                        },
                        description=(
                            f"Pic isolé sur {day}: {score:.0f}% "
                            f"(contexte: {moyenne_avant:.0f}% → {moyenne_apres:.0f}%)"
                        )
                    ))
        
        return results
    
    def detect_montagnes_russes(self) -> List[SuspicionResult]:
        """
        Détecte les alternances rapides hausse/baisse >30%.
        Signe d'irrégularité artificielle (triche sélective).
        """
        results = []
        
        for student in self.df.index:
            scores = self.df.loc[student].values
            alternances = 0
            details_jours = []
            
            for i in range(1, len(scores)):
                diff = scores[i] - scores[i - 1]
                
                if abs(diff) >= self.config.montagne_seuil_variation:
                    # Compter comme alternance si direction change
                    if i > 1:
                        prev_diff = scores[i - 1] - scores[i - 2]
                        if (diff > 0 and prev_diff < 0) or (diff < 0 and prev_diff > 0):
                            alternances += 1
                            details_jours.append({
                                "from": self.df.columns[i - 2],
                                "middle": self.df.columns[i - 1],
                                "to": self.df.columns[i],
                                "variation": f"{prev_diff:+.0f}% → {diff:+.0f}%"
                            })
            
            if alternances >= self.config.montagne_min_alternances:
                score = min(alternances * 15, 100)
                results.append(SuspicionResult(
                    student_id=student,
                    suspicion_type=SuspicionType.MONTAGNES_RUSSES,
                    score=score,
                    details={
                        "alternances": alternances,
                        "patterns": details_jours[:5]  # Limiter les détails
                    },
                    description=f"{alternances} alternances rapides détectées (pattern montagnes russes)"
                ))
        
        return results
    
    def detect_copies_collectives(self) -> List[SuspicionResult]:
        """
        Détecte les clusters d'élèves avec exactement le même score sur plusieurs jours.
        Signe d'une copie organisée à plusieurs.
        """
        results = []
        clusters_detected = []
        
        for day in self.df.columns:
            day_scores = self.df[day]
            
            # Grouper par score (arrondi à 0.5 près)
            rounded = day_scores.round(0)
            value_counts = rounded.value_counts()
            
            for score, count in value_counts.items():
                if count >= self.config.collectif_min_eleves:
                    eleves = day_scores[rounded == score].index.tolist()
                    clusters_detected.append({
                        "day": day,
                        "score": score,
                        "count": count,
                        "students": eleves
                    })
                    
                    # Ajouter un résultat pour chaque étudiant du cluster
                    for student in eleves:
                        existing = [r for r in results if r.student_id == student 
                                   and r.suspicion_type == SuspicionType.COPIE_COLLECTIVE]
                        if not existing:
                            results.append(SuspicionResult(
                                student_id=student,
                                suspicion_type=SuspicionType.COPIE_COLLECTIVE,
                                score=50.0,
                                details={
                                    "day": day,
                                    "score": score,
                                    "cluster_size": count,
                                    "partners": [e for e in eleves if e != student][:5]
                                },
                                description=(
                                    f"Copie collective sur {day}: "
                                    f"{count} élèves avec {score:.0f}%"
                                )
                            ))
        
        return results
    
    def calculate_suspicion_scores(self) -> pd.DataFrame:
        """
        Calcule un score global de suspicion avec les heuristiques.
        
        Returns:
            DataFrame avec les scores par étudiant
        """
        self.detect_all()
        
        scores: Dict[str, Dict[str, Any]] = {}
        
        def _init():
            return {'score': 0, 'raisons': [], 'copieurs': 0, 'pics': 0, 
                    'montagnes': 0, 'collectif': 0}
        
        for result in self.results:
            student = result.student_id
            if student not in scores:
                scores[student] = _init()
            
            # Ajouter les points selon le type
            if result.suspicion_type == SuspicionType.COPIEUR:
                points = 4 + min(result.details.get('similar_days', 0) - 3, 3)
                if result.details.get('max_consecutive', 0) >= 2:
                    points += 2
                scores[student]['score'] += points
                scores[student]['copieurs'] += points
            
            elif result.suspicion_type == SuspicionType.PIC_ISOLE:
                scores[student]['score'] += 6
                scores[student]['pics'] += 6
            
            elif result.suspicion_type == SuspicionType.MONTAGNES_RUSSES:
                points = min(result.details.get('alternances', 0) * 1.5, 7)
                scores[student]['score'] += points
                scores[student]['montagnes'] += points
            
            elif result.suspicion_type == SuspicionType.COPIE_COLLECTIVE:
                scores[student]['score'] += 2
                scores[student]['collectif'] += 2
            
            scores[student]['raisons'].append(result.description)
        
        if not scores:
            return pd.DataFrame()
        
        result_df = pd.DataFrame.from_dict(scores, orient='index')
        result_df = result_df.sort_values('score', ascending=False)
        
        # S'assurer que toutes les colonnes existent
        for col in ['copieurs', 'pics', 'montagnes', 'collectif']:
            if col not in result_df.columns:
                result_df[col] = 0
        
        return result_df
    
    def get_student_score(self, student_id: str) -> float:
        """Calcule le score global de suspicion pour un étudiant."""
        student_results = [r for r in self.results if r.student_id == student_id]
        if not student_results:
            return 0.0
        return sum(r.score for r in student_results) / len(student_results)
    
    def get_top_suspects(self, n: int = 10) -> List[Tuple[str, float]]:
        """Retourne les N étudiants les plus suspects."""
        students = self.df.index.tolist()
        scores = [(s, self.get_student_score(s)) for s in students]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:n]


# Fonctions de compatibilité pour l'ancien code
def detect_copieurs(df: pd.DataFrame, tolerance: float = 1, 
                    min_days: int = 4, min_ratio: float = 0.4) -> pd.DataFrame:
    """Fonction wrapper pour compatibilité."""
    config = DetectionConfig(
        copieur_tolerance=tolerance,
        copieur_min_days=min_days,
        copieur_min_ratio=min_ratio
    )
    engine = DetectionEngine(df, config)
    results = engine.detect_copieurs()
    
    pairs = []
    seen = set()
    for r in results:
        key = tuple(sorted([r.student_id, r.details.get('partner', '')]))
        if key not in seen:
            seen.add(key)
            pairs.append({
                'etudiant_1': r.student_id,
                'etudiant_2': r.details.get('partner', ''),
                'jours_similaires': r.details.get('similar_days', 0),
                'jours_consecutifs': r.details.get('max_consecutive', 0),
                'ratio': r.details.get('ratio', 0),
                'liste_jours': ', '.join(r.details.get('days', [])[:5])
            })
    
    return pd.DataFrame(pairs)


def detect_pics_isoles(df: pd.DataFrame, seuil_haut: float = 70, 
                       seuil_bas: float = 30, fenetre: int = 2) -> pd.DataFrame:
    """Fonction wrapper pour compatibilité."""
    config = DetectionConfig(
        pic_seuil_haut=seuil_haut,
        pic_seuil_bas=seuil_bas,
        pic_fenetre=fenetre
    )
    engine = DetectionEngine(df, config)
    results = engine.detect_pics_isoles()
    
    return pd.DataFrame([{
        'etudiant': r.student_id,
        'jour': r.details.get('day', ''),
        'score': r.details.get('score', 0),
        'moyenne_avant': r.details.get('moyenne_avant', 0),
        'moyenne_apres': r.details.get('moyenne_apres', 0),
        'contexte': r.details.get('contexte', '')
    } for r in results])


def detect_montagnes_russes(df: pd.DataFrame, seuil_variation: float = 30) -> pd.DataFrame:
    """Fonction wrapper pour compatibilité."""
    config = DetectionConfig(montagne_seuil_variation=seuil_variation)
    engine = DetectionEngine(df, config)
    results = engine.detect_montagnes_russes()
    
    return pd.DataFrame([{
        'etudiant': r.student_id,
        'alternances': r.details.get('alternances', 0),
        'pattern': 'Montagnes russes',
        'details': r.details.get('patterns', [])
    } for r in results])


def detect_copies_collectives(df: pd.DataFrame, tolerance: float = 0,
                              min_eleves: int = 3, min_jours: int = 2) -> pd.DataFrame:
    """Fonction wrapper pour compatibilité."""
    config = DetectionConfig(
        collectif_tolerance=tolerance,
        collectif_min_eleves=min_eleves,
        collectif_min_jours=min_jours
    )
    engine = DetectionEngine(df, config)
    results = engine.detect_copies_collectives()
    
    # Agréger par jour
    clusters = {}
    for r in results:
        day = r.details.get('day', '')
        if day not in clusters:
            clusters[day] = {
                'jour': day,
                'score': r.details.get('score', 0),
                'nb_eleves': r.details.get('cluster_size', 0),
                'eleves': [r.student_id.split('@')[0]]
            }
        else:
            clusters[day]['eleves'].append(r.student_id.split('@')[0])
    
    for c in clusters.values():
        c['eleves'] = ', '.join(c['eleves'][:5]) + ('...' if len(c['eleves']) > 5 else '')
    
    return pd.DataFrame(list(clusters.values()))


def calculate_suspicion_score_v2(df: pd.DataFrame) -> pd.DataFrame:
    """Fonction wrapper pour compatibilité."""
    engine = DetectionEngine(df)
    return engine.calculate_suspicion_scores()
