"""
SQLAlchemy Database Models for AI-WasteTwin
"""
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, Text, JSON, Enum as SQLEnum, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum
import json

Base = declarative_base()


# =============================================================================
# Enums
# =============================================================================

class WasteType(str, Enum):
    GENERAL = "general"
    ORGANIC = "organic"
    RECYCLABLE = "recyclable"
    EWASTE = "ewaste"


class AreaType(str, Enum):
    RESIDENTIAL = "Residential"
    COMMERCIAL = "Commercial"
    MARKET = "Market"
    HOSPITAL = "Hospital"
    SCHOOL = "School"
    RESTAURANT = "Restaurant"
    MALL = "Mall"
    BUS_STAND = "Bus Stand"
    RAILWAY_STATION = "Railway Station"
    PARK = "Park"
    INDUSTRIAL = "Industrial"


class Criticality(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class TruckStatus(str, Enum):
    IDLE = "idle"
    ENROUTE = "enroute"
    BREAKDOWN = "breakdown"
    MAINTENANCE = "maintenance"
    LOADING = "loading"
    UNLOADING = "unloading"


class BinStatus(str, Enum):
    ACTIVE = "Active"
    FULL = "Full"
    MAINTENANCE = "Maintenance"
    OFFLINE = "Offline"


class FacilityType(str, Enum):
    GENERAL = "general_processing"
    RECYCLING = "recycling_center"
    COMPOST = "composting"
    EWASTE = "ewaste_facility"
    DEPOT = "depot"


class EventType(str, Enum):
    FESTIVAL = "festival"
    HEAVY_RAIN = "heavy_rain"
    ROAD_CLOSURE = "road_closure"
    TRUCK_BREAKDOWN = "truck_breakdown"


class UserRole(str, Enum):
    ADMIN = "admin"
    DRIVER = "driver"
    MAINTENANCE = "maintenance"
    VIEWER = "viewer"


# =============================================================================
# Core Tables
# =============================================================================

class Bin(Base):
    """Smart bin inventory"""
    __tablename__ = "bins"

    id = Column(String(20), primary_key=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    area_type = Column(String(50), nullable=False)  # AreaType enum stored as string
    waste_type = Column(String(20), nullable=False)  # WasteType
    capacity_liters = Column(Float, nullable=False)
    current_fill_pct = Column(Float, default=0.0)
    criticality = Column(String(20), default="Medium")  # Criticality
    status = Column(String(20), default="Active")
    street_name = Column(String(100))
    ward_name = Column(String(100))
    ward_number = Column(Integer)
    installation_date = Column(DateTime, default=datetime.utcnow)
    last_collection = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    fill_history = relationship("FillHistory", back_populates="bin")
    predictions = relationship("Prediction", back_populates="bin")
    notifications = relationship("Notification", back_populates="bin")

    def to_dict(self):
        return {
            "id": self.id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "area_type": self.area_type,
            "waste_type": self.waste_type,
            "capacity_liters": self.capacity_liters,
            "current_fill_pct": self.current_fill_pct,
            "criticality": self.criticality,
            "status": self.status,
            "street_name": self.street_name,
            "ward_name": self.ward_name,
            "ward_number": self.ward_number,
            "last_collection": self.last_collection.isoformat() if self.last_collection else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }


class FillHistory(Base):
    """Time-series sensor data"""
    __tablename__ = "fill_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bin_id = Column(String(20), ForeignKey("bins.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    fill_pct = Column(Float, nullable=False)
    temperature = Column(Float)
    rainfall = Column(Float)
    waste_generated = Column(Float)

    # Relationships
    bin = relationship("Bin", back_populates="fill_history")


class Prediction(Base):
    """ML forecast output"""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bin_id = Column(String(20), ForeignKey("bins.id"), nullable=False)
    prediction_time = Column(DateTime, default=datetime.utcnow)
    horizon_hours = Column(Integer, nullable=False)  # 1, 2, 4
    predicted_fill = Column(Float, nullable=False)
    overflow_probability = Column(Float)
    time_to_overflow = Column(Float)  # in hours
    model_version = Column(String(50))

    # Relationships
    bin = relationship("Bin", back_populates="predictions")


class Truck(Base):
    """Collection vehicle fleet"""
    __tablename__ = "trucks"

    id = Column(String(20), primary_key=True)
    plate_number = Column(String(20), unique=True)
    capacity_liters = Column(Float, nullable=False)
    current_load_liters = Column(Float, default=0.0)
    status = Column(String(20), default="idle")
    latitude = Column(Float)
    longitude = Column(Float)
    driver_name = Column(String(100))
    driver_phone = Column(String(20))

    def to_dict(self):
        return {
            "id": self.id,
            "plate_number": self.plate_number,
            "capacity_liters": self.capacity_liters,
            "current_load_liters": self.current_load_liters,
            "status": self.status,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "driver_name": self.driver_name
        }


class Facility(Base):
    """Waste processing facilities"""
    __tablename__ = "facilities"

    id = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # FacilityType
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    daily_capacity_liters = Column(Float, nullable=False)
    current_load_liters = Column(Float, default=0.0)
    accepted_waste_types = Column(JSON)  # List of WasteType
    is_active = Column(Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "daily_capacity_liters": self.daily_capacity_liters,
            "current_load_liters": self.current_load_liters,
            "accepted_waste_types": self.accepted_waste_types,
            "is_active": self.is_active
        }


class Road(Base):
    """Road network for routing"""
    __tablename__ = "roads"

    id = Column(String(50), primary_key=True)
    start_node = Column(String(50))  # Intersection/landmark name
    end_node = Column(String(50))
    distance_km = Column(Float, nullable=False)
    travel_time_multiplier = Column(Float, default=1.0)
    status = Column(String(20), default="open")  # open, rain, closed
    road_type = Column(String(50))  # highway, main, local

    def to_dict(self):
        return {
            "id": self.id,
            "start_node": self.start_node,
            "end_node": self.end_node,
            "distance_km": self.distance_km,
            "travel_time_multiplier": self.travel_time_multiplier,
            "status": self.status,
            "road_type": self.road_type
        }


class Event(Base):
    """Active events and disruptions"""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False)  # EventType
    zone = Column(String(100))  # Affected area/ward
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    intensity = Column(Float, default=1.0)  # Multiplier for effects
    params_json = Column(JSON)  # Additional parameters
    is_active = Column(Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "zone": self.zone,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "intensity": self.intensity,
            "params_json": self.params_json,
            "is_active": self.is_active
        }


class Route(Base):
    """Optimized collection routes"""
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    truck_id = Column(String(20), ForeignKey("trucks.id"))
    date = Column(DateTime, default=datetime.utcnow)
    route_json = Column(JSON)  # Ordered list of stops
    distance_km = Column(Float, default=0.0)
    estimated_duration_hours = Column(Float, default=0.0)
    fuel_liters = Column(Float, default=0.0)
    co2_kg = Column(Float, default=0.0)
    utilization_pct = Column(Float, default=0.0)
    status = Column(String(20), default="planned")  # planned, active, completed

    def to_dict(self):
        return {
            "id": self.id,
            "truck_id": self.truck_id,
            "date": self.date.isoformat() if self.date else None,
            "route_json": self.route_json,
            "distance_km": self.distance_km,
            "estimated_duration_hours": self.estimated_duration_hours,
            "fuel_liters": self.fuel_liters,
            "co2_kg": self.co2_kg,
            "utilization_pct": self.utilization_pct,
            "status": self.status
        }


class Notification(Base):
    """System alerts and notifications"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bin_id = Column(String(20), ForeignKey("bins.id"))
    severity = Column(String(20), default="info")  # info, warning, critical
    title = Column(String(200), nullable=False)
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    bin = relationship("Bin", back_populates="notifications")


class User(Base):
    """User authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="viewer")
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# =============================================================================
# Database Connection
# =============================================================================

def get_database_url() -> str:
    """Get database URL from settings or default"""
    try:
        from backend.config.settings import get_settings
        settings = get_settings()
        return settings.database_url
    except:
        return "sqlite:///./waste_management.db"


def create_engine_and_session():
    """Create database engine and session"""
    engine = create_engine(
        get_database_url(),
        echo=False,
        connect_args={"check_same_thread": False} if "sqlite" in get_database_url() else {}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal


def init_database():
    """Initialize database tables"""
    engine, _ = create_engine_and_session()
    Base.metadata.create_all(bind=engine)
    return engine