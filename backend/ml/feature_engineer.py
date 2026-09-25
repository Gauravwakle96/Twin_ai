"""
ML Feature Engineering for Waste Bin Prediction
Adapted from REPO 1 (EcoBin) with enhancements
"""
import pandas as pd
import numpy as np
from typing import Tuple, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Build features for ML prediction"""

    @staticmethod
    def create_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Create lag and rolling features for time-series prediction
        Input: DataFrame with columns [bin_id, timestamp, fill_pct, temperature, rainfall]
        Output: DataFrame with engineered features
        """
        logger.info("Engineering features...")

        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Ensure sorted by bin and time
        df = df.sort_values(["bin_id", "timestamp"]).reset_index(drop=True)

        # Temporal features
        df["hour"] = df["timestamp"].dt.hour
        df["day_of_week"] = df["timestamp"].dt.dayofweek
        df["month"] = df["timestamp"].dt.month
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
        df["day_of_year"] = df["timestamp"].dt.dayofyear

        # Lag features (per bin)
        for lag in [1, 2, 3, 6, 12, 24]:
            df[f"fill_lag_{lag}h"] = df.groupby("bin_id")["fill_pct"].shift(lag)

        # Rolling features (per bin, per area_type)
        for window in [6, 12, 24]:
            df[f"fill_rolling_mean_{window}h"] = (
                df.groupby("bin_id")["fill_pct"]
                .rolling(window=window, min_periods=1)
                .mean()
                .reset_index(drop=True)
            )
            df[f"fill_rolling_std_{window}h"] = (
                df.groupby("bin_id")["fill_pct"]
                .rolling(window=window, min_periods=1)
                .std()
                .reset_index(drop=True)
            )

        # Growth rate (current - 1h lag)
        df["fill_growth_1h"] = df.groupby("bin_id")["fill_pct"].diff(1)

        # Hours since collection (cumulative)
        # Assume collection when fill drops > 50%
        df["is_collected"] = (df["fill_pct"].shift(1) - df["fill_pct"]) > 50
        df["collection_event"] = df.groupby("bin_id")["is_collected"].cumsum()
        df["hours_since_collection"] = df.groupby(["bin_id", "collection_event"]).cumcount()

        # Interaction features
        df["temp_rain_interaction"] = df["temperature"] * df["rainfall"]

        # Fill fill NaNs forward then backward
        df = df.fillna(method="bfill").fillna(method="ffill")

        logger.info(f"✅ Created {df.shape[1]} features")
        return df

    @staticmethod
    def prepare_training_data(
        df: pd.DataFrame,
        prediction_horizons: List[int] = [1, 2, 4]
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Create target variables for multi-horizon prediction
        Returns: (features_df, targets_df)
        """
        logger.info(f"Preparing training data for horizons: {prediction_horizons}h...")

        df = df.copy()

        # Create target columns for each horizon
        for horizon in prediction_horizons:
            df[f"target_fill_{horizon}h"] = (
                df.groupby("bin_id")["fill_pct"]
                .shift(-horizon)
            )

        # Filter out rows where collection occurred in prediction window
        # (to avoid training on collection events)
        for horizon in prediction_horizons:
            # Check if any collection event in the next `horizon` hours
            df[f"has_collection_{horizon}h"] = False
            for i in range(1, horizon + 1):
                df[f"has_collection_{horizon}h"] |= (
                    df.groupby("bin_id")["is_collected"].shift(-i).fillna(False)
                )

        # Remove rows with collections in prediction window
        valid_mask = ~df[[f"has_collection_{h}h" for h in prediction_horizons]].any(axis=1)
        df = df[valid_mask].reset_index(drop=True)

        # Select feature columns
        feature_cols = [col for col in df.columns if col.startswith(
            ("hour", "day", "month", "is_", "fill_lag", "fill_rolling", "fill_growth", "hours_since", "temp_rain", "capacity", "area_")
        ) and not col.startswith("is_collected") and not col.startswith("has_collection")]

        target_cols = [f"target_fill_{h}h" for h in prediction_horizons]

        logger.info(f"Features: {len(feature_cols)}, Targets: {len(target_cols)}")
        logger.info(f"Training samples: {len(df)}")

        return df[feature_cols], df[target_cols]

    @staticmethod
    def get_feature_names() -> List[str]:
        """Get list of feature column names"""
        return [
            "hour", "day_of_week", "month", "is_weekend", "day_of_year",
            "fill_lag_1h", "fill_lag_2h", "fill_lag_3h", "fill_lag_6h", "fill_lag_12h", "fill_lag_24h",
            "fill_rolling_mean_6h", "fill_rolling_std_6h",
            "fill_rolling_mean_12h", "fill_rolling_std_12h",
            "fill_rolling_mean_24h", "fill_rolling_std_24h",
            "fill_growth_1h",
            "hours_since_collection",
            "temp_rain_interaction",
            "temperature", "rainfall"
        ]
