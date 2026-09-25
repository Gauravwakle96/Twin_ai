"""
Create a dummy ML model for demonstration
Actual training would use synthetic/historical data
"""
import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from backend.ml.predictor import WastePredictionModel

# Create a minimal trained model for demonstration
def create_dummy_model():
    print("Creating dummy ML model for demo...")

    # Create dummy features matching what the system expects
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

    # Create realistic targets
    y = pd.DataFrame({
        "target_fill_1h": X["fill_lag_1h"] + np.random.normal(0, 2, n_samples),
        "target_fill_2h": X["fill_lag_2h"] + np.random.normal(0, 4, n_samples),
        "target_fill_4h": X["fill_lag_3h"] + np.random.normal(0, 6, n_samples),
    })

    # Clip to valid range
    y = y.clip(0, 100)

    # Train model
    model = WastePredictionModel("./ml/models/xgb_model.pkl")
    results = model.train(X, y)

    # Save
    model.save()

    print("✅ Dummy model created with metrics:")
    for horizon, metrics in results.items():
        print(f"  {horizon}h: MAE={metrics['mae']:.2f}%, RMSE={metrics['rmse']:.2f}%")

    return model

if __name__ == "__main__":
    create_dummy_model()
    print("\nTo use the model in prediction service:")
    print("1. Update config to use this model path")
    print("2. Call get_prediction_service().load_model()")