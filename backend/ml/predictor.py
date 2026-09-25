"""
XGBoost ML Model for Bin Fill-Level Prediction
Adapted from REPO 1 (EcoBin)
"""
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error
from scipy.stats import norm
import joblib
import logging
from typing import Dict, Tuple, Optional, List
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class WastePredictionModel:
    """XGBoost model for bin fill-level prediction"""

    def __init__(self, model_path: str = "./ml/models/xgb_model.pkl"):
        self.model = None
        self.model_path = Path(model_path)
        self.feature_names = None
        self.metadata = {
            "model_type": "XGBoost",
            "horizons": [1, 2, 4],
            "training_date": None,
            "metrics": {}
        }

    def train(
        self,
        X: pd.DataFrame,
        y: pd.DataFrame,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict:
        """
        Train XGBoost model on multi-horizon targets
        """
        logger.info("Training XGBoost model...")

        self.feature_names = X.columns.tolist()

        # Train separate model for each horizon
        models = {}
        results = {}

        for target_col in y.columns:
            horizon = target_col.replace("target_fill_", "").replace("h", "")
            logger.info(f"\n📊 Training model for {horizon}h horizon...")

            y_target = y[target_col].dropna()
            X_filtered = X.loc[y_target.index]

            # Train-test split
            X_train, X_test, y_train, y_test = train_test_split(
                X_filtered, y_target,
                test_size=test_size,
                random_state=random_state
            )

            # XGBoost parameters (tuned from REPO 1)
            xgb_params = {
                "objective": "reg:squarederror",
                "n_estimators": 150,
                "learning_rate": 0.08,
                "max_depth": 6,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "random_state": random_state,
                "n_jobs": -1,
                "verbosity": 0
            }

            model = xgb.XGBRegressor(**xgb_params)
            model.fit(X_train, y_train)

            # Predictions
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)

            # Clip predictions to [0, 100]
            y_pred_train = np.clip(y_pred_train, 0, 100)
            y_pred_test = np.clip(y_pred_test, 0, 100)

            # Metrics
            mae = mean_absolute_error(y_test, y_pred_test)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
            mape = mean_absolute_percentage_error(y_test, y_pred_test)
            r2 = r2_score(y_test, y_pred_test)

            logger.info(f"  MAE:  {mae:.2f}%")
            logger.info(f"  RMSE: {rmse:.2f}%")
            logger.info(f"  MAPE: {mape:.2f}%")
            logger.info(f"  R²:   {r2:.3f}")

            models[horizon] = model
            results[horizon] = {
                "mae": float(mae),
                "rmse": float(rmse),
                "mape": float(mape),
                "r2": float(r2),
                "train_samples": len(X_train),
                "test_samples": len(X_test)
            }

        self.model = models
        self.metadata["metrics"] = results
        self.metadata["training_date"] = pd.Timestamp.now().isoformat()

        logger.info("\n✅ Training complete!")
        return results

    def predict(
        self,
        bin_id: str,
        current_fill: float,
        X_features: pd.DataFrame,
        horizons: List[int] = [1, 2, 4]
    ) -> Dict:
        """
        Predict future fill levels for a bin
        Returns: {
            "bin_id": "BIN001",
            "current_fill": 72.5,
            "predictions": {
                "1h": {"fill": 81.2, "overflow_prob": 0.15, "time_to_overflow": 8.5},
                "2h": {"fill": 91.5, "overflow_prob": 0.45, "time_to_overflow": 2.1},
                "4h": {"fill": 100.0, "overflow_prob": 0.98, "time_to_overflow": 0.0}
            }
        }
        """
        if not self.model:
            raise ValueError("Model not trained. Call train() first.")

        predictions = {
            "bin_id": bin_id,
            "current_fill": round(current_fill, 2),
            "predictions": {}
        }

        for horizon in horizons:
            if str(horizon) not in self.model:
                logger.warning(f"No model for {horizon}h horizon")
                continue

            # Get prediction
            model = self.model[str(horizon)]
            pred = model.predict(X_features.values.reshape(1, -1))[0]
            pred = np.clip(pred, 0, 100)

            # Get RMSE for uncertainty
            rmse = self.metadata["metrics"].get(str(horizon), {}).get("rmse", 5.0)

            # Overflow probability (using normal distribution)
            overflow_prob = 1.0 - norm.cdf(80.0, loc=pred, scale=rmse)
            overflow_prob = np.clip(overflow_prob, 0.0, 1.0)

            # Time to overflow (linear interpolation)
            if pred < 80.0:
                growth_rate = (pred - current_fill) / horizon
                if growth_rate > 0:
                    time_to_overflow = (80.0 - current_fill) / growth_rate
                else:
                    time_to_overflow = 999.0
            else:
                # Already at overflow threshold
                time_to_overflow = 0.0

            predictions["predictions"][f"{horizon}h"] = {
                "predicted_fill": round(pred, 2),
                "overflow_probability": round(overflow_prob, 3),
                "time_to_overflow_hours": round(max(0, time_to_overflow), 2),
                "confidence_interval": {
                    "lower": round(max(0, pred - 1.96 * rmse), 2),
                    "upper": round(min(100, pred + 1.96 * rmse), 2)
                }
            }

        return predictions

    def save(self, path: Optional[str] = None):
        """Save model and metadata"""
        path = Path(path or self.model_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Save model
        joblib.dump(self.model, path)
        logger.info(f"✅ Model saved to {path}")

        # Save metadata
        metadata_path = path.with_suffix(".json")
        with open(metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=2)
        logger.info(f"✅ Metadata saved to {metadata_path}")

    def load(self, path: Optional[str] = None):
        """Load model and metadata"""
        path = Path(path or self.model_path)

        if not path.exists():
            raise FileNotFoundError(f"Model not found: {path}")

        self.model = joblib.load(path)
        logger.info(f"✅ Model loaded from {path}")

        # Load metadata
        metadata_path = path.with_suffix(".json")
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                self.metadata = json.load(f)
            logger.info(f"✅ Metadata loaded from {metadata_path}")

        return self


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example usage
    print("🔬 Testing ML model...")

    # Create dummy training data
    n_samples = 1000
    X = pd.DataFrame({
        "hour": np.random.randint(0, 24, n_samples),
        "day_of_week": np.random.randint(0, 7, n_samples),
        "month": np.random.randint(1, 13, n_samples),
        "is_weekend": np.random.randint(0, 2, n_samples),
        "day_of_year": np.random.randint(1, 366, n_samples),
        "fill_lag_1h": np.random.uniform(0, 100, n_samples),
        "fill_lag_2h": np.random.uniform(0, 100, n_samples),
        "fill_lag_3h": np.random.uniform(0, 100, n_samples),
        "fill_rolling_mean_6h": np.random.uniform(0, 100, n_samples),
        "fill_rolling_mean_12h": np.random.uniform(0, 100, n_samples),
        "fill_rolling_mean_24h": np.random.uniform(0, 100, n_samples),
        "fill_growth_1h": np.random.uniform(-5, 5, n_samples),
        "hours_since_collection": np.random.uniform(0, 72, n_samples),
        "temperature": np.random.uniform(15, 45, n_samples),
        "rainfall": np.random.exponential(0.5, n_samples),
    })

    y = pd.DataFrame({
        "target_fill_1h": np.random.uniform(0, 100, n_samples),
        "target_fill_2h": np.random.uniform(0, 100, n_samples),
        "target_fill_4h": np.random.uniform(0, 100, n_samples),
    })

    # Train model
    model = WastePredictionModel()
    results = model.train(X, y)

    print("\n📈 Training Results:")
    for horizon, metrics in results.items():
        print(f"  {horizon}h: MAE={metrics['mae']:.2f}, RMSE={metrics['rmse']:.2f}, R²={metrics['r2']:.3f}")

    # Test prediction
    print("\n🔮 Sample prediction:")
    sample = X.iloc[0:1]
    pred = model.predict("BIN001", current_fill=72.5, X_features=sample)
    print(json.dumps(pred, indent=2))
