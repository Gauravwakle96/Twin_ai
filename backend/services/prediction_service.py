"""
Prediction Service - Integrates ML model with Digital Twin
"""
import logging
from typing import Dict, List
import pandas as pd
from backend.ml.predictor import WastePredictionModel
from backend.digital_twin.state import DigitalTwinState, BinState

logger = logging.getLogger(__name__)


class PredictionService:
    """Service layer for running predictions on Digital Twin"""

    def __init__(self, model_path: str = "./ml/models/xgb_model.pkl"):
        self.model = WastePredictionModel(model_path=model_path)
        self.is_loaded = False

    def load_model(self):
        """Load the trained model"""
        try:
            self.model.load()
            self.is_loaded = True
            logger.info("✅ ML model loaded")
        except FileNotFoundError:
            logger.warning("⚠️ ML model not found. Will use dummy predictions.")
            self.is_loaded = False

    def predict_bin_fill(
        self,
        bin_state: BinState,
        horizons: List[int] = [1, 2, 4]
    ) -> Dict:
        """
        Predict future fill levels for a single bin
        Returns predictions dict with overflow probability and time-to-overflow
        """
        if not self.is_loaded:
            # Return dummy prediction for demo
            logger.debug(f"Using dummy prediction for {bin_state.id}")
            return self._dummy_prediction(bin_state, horizons)

        try:
            # Create feature vector for this bin
            # In production, this would use actual historical features
            features_data = self._create_features_for_bin(bin_state)

            # Get prediction
            prediction = self.model.predict(
                bin_id=bin_state.id,
                current_fill=bin_state.current_fill_pct,
                X_features=features_data,
                horizons=horizons
            )

            return prediction

        except Exception as e:
            logger.error(f"Prediction error for {bin_state.id}: {e}")
            return self._dummy_prediction(bin_state, horizons)

    def predict_all_bins(
        self,
        state: DigitalTwinState,
        horizons: List[int] = [1, 2, 4]
    ) -> Dict[str, Dict]:
        """
        Predict fill levels for all bins in Digital Twin
        Updates bin states with predictions
        """
        logger.info(f"Predicting {len(state.bins)} bins for horizons {horizons}...")

        predictions = {}

        for bin_id, bin_state in state.bins.items():
            pred = self.predict_bin_fill(bin_state, horizons)
            predictions[bin_id] = pred

            # Update bin state with predictions
            if "1h" in pred.get("predictions", {}):
                bin_state.predicted_fill_1h = pred["predictions"]["1h"]["predicted_fill"]
                bin_state.overflow_probability = pred["predictions"]["1h"]["overflow_probability"]

            if "2h" in pred.get("predictions", {}):
                bin_state.predicted_fill_2h = pred["predictions"]["2h"]["predicted_fill"]

            if "4h" in pred.get("predictions", {}):
                bin_state.predicted_fill_4h = pred["predictions"]["4h"]["predicted_fill"]
                # Time to overflow from 4h prediction
                bin_state.time_to_overflow_hours = pred["predictions"]["4h"]["time_to_overflow_hours"]

        logger.info(f"✅ Predictions complete for {len(predictions)} bins")
        return predictions

    def _create_features_for_bin(self, bin_state: BinState) -> pd.DataFrame:
        """Create feature vector for a bin (placeholder)"""
        # In production, this would query historical data
        # For now, create a dummy feature vector
        return pd.DataFrame({
            "hour": [bin_state.temperature % 24],  # Hacky but works for demo
            "day_of_week": [0],
            "month": [6],
            "is_weekend": [0],
            "day_of_year": [150],
            "fill_lag_1h": [bin_state.current_fill_pct * 0.95],
            "fill_lag_2h": [bin_state.current_fill_pct * 0.90],
            "fill_lag_3h": [bin_state.current_fill_pct * 0.85],
            "fill_rolling_mean_6h": [bin_state.current_fill_pct],
            "fill_rolling_mean_12h": [bin_state.current_fill_pct],
            "fill_rolling_mean_24h": [bin_state.current_fill_pct],
            "fill_growth_1h": [bin_state.growth_rate_pct_per_hour],
            "hours_since_collection": [bin_state.hours_since_collection],
            "temperature": [bin_state.temperature],
            "rainfall": [bin_state.rainfall],
        })

    def _dummy_prediction(
        self,
        bin_state: BinState,
        horizons: List[int]
    ) -> Dict:
        """Generate dummy predictions for demo (when model not loaded)"""
        current = bin_state.current_fill_pct
        growth = bin_state.growth_rate_pct_per_hour

        predictions = {
            "bin_id": bin_state.id,
            "current_fill": round(current, 2),
            "predictions": {}
        }

        for horizon in horizons:
            pred_fill = min(100, current + (growth * horizon * 1.2))  # Slightly boosted growth for demo

            # Overflow probability (simple sigmoid)
            overflow_prob = 1.0 / (1.0 + 2.718 ** (-(pred_fill - 80) / 5))

            # Time to overflow
            if growth > 0:
                time_to_overflow = max(0, (80 - current) / growth)
            else:
                time_to_overflow = 999

            predictions["predictions"][f"{horizon}h"] = {
                "predicted_fill": round(pred_fill, 2),
                "overflow_probability": round(max(0, min(1, overflow_prob)), 3),
                "time_to_overflow_hours": round(time_to_overflow, 2),
                "confidence_interval": {
                    "lower": round(max(0, pred_fill - 5), 2),
                    "upper": round(min(100, pred_fill + 5), 2)
                }
            }

        return predictions


# Global prediction service instance
_service = None


def get_prediction_service() -> PredictionService:
    """Get or create global prediction service"""
    global _service
    if _service is None:
        _service = PredictionService()
        _service.load_model()
    return _service
