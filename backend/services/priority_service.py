"""
Priority Scoring Engine
Continuous sigmoid-based scoring adapted from REPO 2
"""
import math
import logging
from typing import Dict, Tuple
from backend.digital_twin.state import BinState
from backend.config.settings import get_settings

logger = logging.getLogger(__name__)


class PriorityEngine:
    """Calculate priority scores for bins using continuous sigmoid scoring"""

    def __init__(self):
        self.settings = get_settings()

    def calculate_priority(
        self,
        bin_state: BinState,
        predicted_fill_4h: float = None
    ) -> Tuple[float, Dict]:
        """
        Calculate priority score (0-100) using multi-factor sigmoid scoring

        Returns: (score, explanation_dict)
        """
        # Use 4h prediction if available, otherwise current fill
        fill_for_scoring = predicted_fill_4h if predicted_fill_4h is not None else bin_state.current_fill_pct

        # 1. Fill Level Weight (Sigmoid curve centered at 65%)
        fill_weight = 1.0 / (1.0 + math.exp(-0.12 * (fill_for_scoring - 65.0)))
        fill_score = fill_weight * 100

        # 2. Time-to-Overflow Weight (inverse - higher priority if overflow soon)
        tto = bin_state.time_to_overflow_hours
        if tto <= 0:
            time_weight = 1.0  # Already overflowing
        elif tto < 48:
            time_weight = 1.0 - (tto / 48.0)
        else:
            time_weight = 0.0
        time_score = time_weight * 100

        # 3. Overflow Probability Weight
        overflow_weight = bin_state.overflow_probability
        overflow_score = overflow_weight * 100

        # 4. Criticality Multiplier
        criticality_map = {
            "Low": self.settings.criticality_low,
            "Medium": self.settings.criticality_medium,
            "High": self.settings.criticality_high
        }
        crit_multiplier = criticality_map.get(bin_state.criticality, 1.0)

        # 5. Anomaly Boost
        anomaly_boost = self.settings.priority_anomaly_boost if bin_state.is_anomalous else 0.0

        # Weighted aggregation
        base_score = (
            fill_weight * self.settings.priority_fill_weight +
            time_weight * self.settings.priority_time_weight +
            overflow_weight * self.settings.priority_overflow_weight +
            anomaly_boost
        )

        # Apply criticality multiplier
        final_score = base_score * crit_multiplier * 100

        # Clip to [0, 100]
        final_score = max(0, min(100, final_score))

        # Build explanation
        explanation = {
            "fill_level": round(fill_for_scoring, 2),
            "fill_score": round(fill_score, 1),
            "fill_weight": round(fill_weight, 3),
            "time_to_overflow_hours": round(tto, 2) if tto < 999 else None,
            "time_score": round(time_score, 1),
            "time_weight": round(time_weight, 3),
            "overflow_probability": round(bin_state.overflow_probability, 3),
            "overflow_score": round(overflow_score, 1),
            "overflow_weight": round(overflow_weight, 3),
            "criticality": bin_state.criticality,
            "criticality_multiplier": crit_multiplier,
            "is_anomalous": bin_state.is_anomalous,
            "anomaly_boost": anomaly_boost,
            "base_score": round(base_score * 100, 1),
            "final_score": round(final_score, 1)
        }

        return final_score, explanation

    def calculate_all_priorities(self, bins: Dict[str, BinState]) -> Dict[str, Tuple[float, Dict]]:
        """Calculate priorities for all bins"""
        logger.info(f"Calculating priorities for {len(bins)} bins...")

        results = {}
        for bin_id, bin_state in bins.items():
            score, explanation = self.calculate_priority(bin_state, bin_state.predicted_fill_4h)
            bin_state.priority_score = score
            results[bin_id] = (score, explanation)

        logger.info(f"✅ Priorities calculated. High priority bins (>70): {len([s for s, _ in results.values() if s > 70])}")
        return results


class AnomalyDetector:
    """Detect abnormal waste generation patterns"""

    def __init__(self, z_threshold: float = 2.0):
        self.z_threshold = z_threshold
        self.baselines = {}  # bin_id -> (mean_growth, std_growth)

    def update_baseline(self, bin_id: str, growth_rate: float):
        """Update rolling baseline for a bin"""
        if bin_id not in self.baselines:
            self.baselines[bin_id] = {"values": [], "mean": 0, "std": 1}

        baseline = self.baselines[bin_id]
        baseline["values"].append(growth_rate)

        # Keep last 24 values (24 hours)
        if len(baseline["values"]) > 24:
            baseline["values"].pop(0)

        # Calculate mean and std
        if len(baseline["values"]) >= 3:
            values = baseline["values"]
            baseline["mean"] = sum(values) / len(values)
            variance = sum((x - baseline["mean"]) ** 2 for x in values) / len(values)
            baseline["std"] = math.sqrt(variance) if variance > 0 else 1

    def detect_anomaly(self, bin_id: str, current_growth: float) -> Tuple[bool, str, float]:
        """
        Detect if current growth is anomalous
        Returns: (is_anomalous, reason, z_score)
        """
        if bin_id not in self.baselines:
            return False, "", 0.0

        baseline = self.baselines[bin_id]

        if len(baseline["values"]) < 3:
            return False, "Insufficient history", 0.0

        mean = baseline["mean"]
        std = baseline["std"]

        if std == 0:
            return False, "No variance", 0.0

        # Calculate z-score
        z_score = (current_growth - mean) / std

        # Check threshold
        if abs(z_score) > self.z_threshold:
            if z_score > 0:
                reason = f"High growth: {current_growth:.2f}%/h vs expected {mean:.2f}%/h (z={z_score:.2f})"
            else:
                reason = f"Low/negative growth: {current_growth:.2f}%/h vs expected {mean:.2f}%/h (z={z_score:.2f})"
            return True, reason, z_score

        return False, "", z_score

    def detect_all_anomalies(self, bins: Dict[str, BinState]) -> Dict[str, Tuple[bool, str]]:
        """Detect anomalies across all bins"""
        logger.info(f"Detecting anomalies for {len(bins)} bins...")

        results = {}
        for bin_id, bin_state in bins.items():
            # Update baseline
            self.update_baseline(bin_id, bin_state.growth_rate_pct_per_hour)

            # Detect
            is_anomalous, reason, z_score = self.detect_anomaly(bin_id, bin_state.growth_rate_pct_per_hour)

            # Update state
            bin_state.is_anomalous = is_anomalous
            bin_state.anomaly_reason = reason

            results[bin_id] = (is_anomalous, reason)

        anomaly_count = len([r for r in results.values() if r[0]])
        logger.info(f"✅ Anomaly detection complete. Detected: {anomaly_count}")
        return results


class DecisionEngine:
    """Decide collect/wait/reassign for bins"""

    def __init__(self):
        self.settings = get_settings()

    def decide_action(
        self,
        bin_state: BinState,
        available_trucks: int
    ) -> str:
        """
        Decide action for a bin
        Returns: "COLLECT", "WAIT", or "REASSIGN"
        """
        priority = bin_state.priority_score

        # Critical bins (>90): Collect immediately
        if priority >= 90:
            return "COLLECT"

        # High priority bins (70-90): Collect if trucks available
        if priority >= 70:
            if available_trucks > 0:
                return "COLLECT"
            else:
                return "REASSIGN"  # Need truck but none available

        # Medium priority bins (50-70): Collect if overflow predicted soon
        if priority >= 50:
            if bin_state.time_to_overflow_hours < 4:
                return "COLLECT"
            else:
                return "WAIT"

        # Low priority bins (<50): Wait
        return "WAIT"

    def decide_all_actions(
        self,
        bins: Dict[str, BinState],
        available_trucks: int
    ) -> Dict[str, str]:
        """
        Decide actions for all bins
        Returns: {bin_id: action}
        """
        logger.info(f"Deciding actions for {len(bins)} bins (available trucks: {available_trucks})...")

        decisions = {}
        for bin_id, bin_state in bins.items():
            action = self.decide_action(bin_state, available_trucks)
            bin_state.decision = action
            decisions[bin_id] = action

        # Count decisions
        collect_count = len([d for d in decisions.values() if d == "COLLECT"])
        wait_count = len([d for d in decisions.values() if d == "WAIT"])
        reassign_count = len([d for d in decisions.values() if d == "REASSIGN"])

        logger.info(f"✅ Decisions: COLLECT={collect_count}, WAIT={wait_count}, REASSIGN={reassign_count}")

        return decisions


# Global instances
_priority_engine = None
_anomaly_detector = None
_decision_engine = None


def get_priority_engine() -> PriorityEngine:
    """Get or create global priority engine"""
    global _priority_engine
    if _priority_engine is None:
        _priority_engine = PriorityEngine()
    return _priority_engine


def get_anomaly_detector() -> AnomalyDetector:
    """Get or create global anomaly detector"""
    global _anomaly_detector
    if _anomaly_detector is None:
        _anomaly_detector = AnomalyDetector(z_threshold=2.0)
    return _anomaly_detector


def get_decision_engine() -> DecisionEngine:
    """Get or create global decision engine"""
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = DecisionEngine()
    return _decision_engine


if __name__ == "__main__":
    import logging
    from backend.digital_twin.state import BinState

    logging.basicConfig(level=logging.INFO)

    # Test priority engine
    print("Testing Priority Engine...")

    bin = BinState(
        id="BIN001",
        latitude=19.87,
        longitude=75.33,
        area_type="Market",
        waste_type="general",
        capacity_liters=240,
        current_fill_pct=88.5,
        criticality="High",
        predicted_fill_4h=96.0,
        overflow_probability=0.85,
        time_to_overflow_hours=2.5,
        is_anomalous=True
    )

    engine = PriorityEngine()
    score, explanation = engine.calculate_priority(bin, bin.predicted_fill_4h)

    print(f"\nBin: {bin.id}")
    print(f"Current fill: {bin.current_fill_pct}%")
    print(f"Predicted (4h): {bin.predicted_fill_4h}%")
    print(f"Priority score: {score:.1f}/100")
    print(f"\nExplanation:")
    for key, value in explanation.items():
        print(f"  {key}: {value}")

    # Test decision
    decision_engine = DecisionEngine()
    action = decision_engine.decide_action(bin, available_trucks=3)
    print(f"\nDecision: {action}")
