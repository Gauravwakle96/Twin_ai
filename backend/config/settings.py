"""
Configuration for AI-WasteTwin
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "AI-WasteTwin"
    debug: bool = True
    version: str = "1.0.0"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite:///./waste_management.db"
    database_echo: bool = False

    # ML Model
    ml_model_path: str = "./ml/models/xgb_model.pkl"
    ml_metadata_path: str = "./ml/models/model_metadata.json"

    # Simulation
    simulation_tick_hours: int = 1
    default_simulation_speed: int = 1
    max_simulation_speed: int = 60

    # Aurangabad City Config
    aurangabad_lat: float = 19.8762
    aurangabad_lon: float = 75.3433

    # Fleet
    default_num_trucks: int = 8
    default_truck_capacity_liters: int = 4000

    # Bins
    default_bin_capacity_liters: int = 240
    overflow_threshold_pct: float = 80.0
    critical_threshold_pct: float = 90.0

    # Priority Weights
    priority_fill_weight: float = 0.55
    priority_time_weight: float = 0.25
    priority_overflow_weight: float = 0.15
    priority_anomaly_boost: float = 0.10

    # Criticality Multipliers
    criticality_low: float = 0.8
    criticality_medium: float = 1.0
    criticality_high: float = 1.3

    # Road Multipliers
    normal_road_multiplier: float = 1.0
    rain_road_multiplier: float = 1.3
    closed_road_multiplier: float = 999.0  # Effectively infinite

    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()