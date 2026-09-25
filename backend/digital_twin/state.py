"""
Digital Twin State Model for AI-WasteTwin
Represents the complete state of the simulated Aurangabad city
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal
from enum import Enum
import json


@dataclass
class BinState:
    """State of a single waste bin"""
    id: str
    latitude: float
    longitude: float
    area_type: str          # Residential, Commercial, Market, etc.
    waste_type: str         # general, organic, recyclable, ewaste
    capacity_liters: float
    current_fill_pct: float
    criticality: str        # Low, Medium, High
    status: str = "Active"
    last_collection: Optional[datetime] = None
    hours_since_collection: float = 24.0
    temperature: float = 28.0
    rainfall: float = 0.0

    # AI Prediction results
    predicted_fill_1h: float = 0.0
    predicted_fill_2h: float = 0.0
    predicted_fill_4h: float = 0.0
    overflow_probability: float = 0.0
    time_to_overflow_hours: float = 999.0

    # Priority & Decision
    priority_score: float = 0.0
    decision: str = "WAIT"  # COLLECT, WAIT, REASSIGN
    is_anomalous: bool = False
    anomaly_reason: str = ""

    # Historical context
    growth_rate_pct_per_hour: float = 0.0
    avg_growth_rate: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "area_type": self.area_type,
            "waste_type": self.waste_type,
            "capacity_liters": self.capacity_liters,
            "current_fill_pct": round(self.current_fill_pct, 2),
            "criticality": self.criticality,
            "status": self.status,
            "last_collection": self.last_collection.isoformat() if self.last_collection else None,
            "hours_since_collection": round(self.hours_since_collection, 1),
            "temperature": round(self.temperature, 1),
            "rainfall": round(self.rainfall, 1),
            "prediction": {
                "1h": round(self.predicted_fill_1h, 2),
                "2h": round(self.predicted_fill_2h, 2),
                "4h": round(self.predicted_fill_4h, 2)
            },
            "overflow_probability": round(self.overflow_probability, 3),
            "time_to_overflow_hours": round(self.time_to_overflow_hours, 1) if self.time_to_overflow_hours < 999 else None,
            "priority_score": round(self.priority_score, 1),
            "decision": self.decision,
            "is_anomalous": self.is_anomalous,
            "anomaly_reason": self.anomaly_reason,
            "growth_rate_pct_per_hour": round(self.growth_rate_pct_per_hour, 2)
        }


@dataclass
class TruckState:
    """State of a collection truck"""
    id: str
    latitude: float
    longitude: float
    capacity_liters: float
    current_load_liters: float = 0.0
    status: Literal["idle", "enroute", "breakdown", "maintenance"] = "idle"
    assigned_bins: List[str] = field(default_factory=list)
    route: List[Dict] = field(default_factory=list)
    destination: Optional[str] = None
    driver_name: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "capacity_liters": self.capacity_liters,
            "current_load_liters": round(self.current_load_liters, 1),
            "status": self.status,
            "assigned_bins": self.assigned_bins,
            "route": self.route,
            "destination": self.destination,
            "driver_name": self.driver_name,
            "utilization_pct": round((self.current_load_liters / self.capacity_liters * 100), 1) if self.capacity_liters > 0 else 0
        }

    @property
    def utilization_pct(self) -> float:
        return round((self.current_load_liters / self.capacity_liters * 100), 1) if self.capacity_liters > 0 else 0

    @property
    def remaining_capacity(self) -> float:
        return max(0, self.capacity_liters - self.current_load_liters)


@dataclass
class FacilityState:
    """State of a waste processing facility"""
    id: str
    name: str
    facility_type: str  # general_processing, recycling_center, composting, ewaste_facility, depot
    latitude: float
    longitude: float
    daily_capacity_liters: float
    current_load_liters: float = 0.0
    accepted_waste_types: List[str] = field(default_factory=list)
    is_active: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "facility_type": self.facility_type,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "daily_capacity_liters": self.daily_capacity_liters,
            "current_load_liters": round(self.current_load_liters, 1),
            "remaining_capacity": round(self.daily_capacity_liters - self.current_load_liters, 1),
            "utilization_pct": round((self.current_load_liters / self.daily_capacity_liters * 100), 1),
            "accepted_waste_types": self.accepted_waste_types,
            "is_active": self.is_active
        }

    @property
    def remaining_capacity(self) -> float:
        return max(0, self.daily_capacity_liters - self.current_load_liters)


@dataclass
class RoadState:
    """State of a road segment"""
    id: str
    start_node: str
    end_node: str
    distance_km: float
    travel_time_multiplier: float = 1.0
    status: Literal["open", "rain", "closed"] = "open"
    road_type: str = "local"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "start_node": self.start_node,
            "end_node": self.end_node,
            "distance_km": self.distance_km,
            "travel_time_multiplier": self.travel_time_multiplier,
            "status": self.status,
            "road_type": self.road_type
        }


@dataclass
class EventState:
    """State of an active event"""
    id: str
    type: Literal["festival", "heavy_rain", "road_closure", "truck_breakdown"]
    zone: str  # Affected area/ward name
    start_time: datetime
    end_time: Optional[datetime] = None
    intensity: float = 1.0
    params: Dict = field(default_factory=dict)
    is_active: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "zone": self.zone,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "intensity": self.intensity,
            "params": self.params,
            "is_active": self.is_active
        }

    def is_expired(self, current_time: datetime) -> bool:
        if self.end_time is None:
            return False
        return current_time >= self.end_time


@dataclass
class DigitalTwinState:
    """
    Central Digital Twin state model for Aurangabad waste management
    This is the single source of truth for the entire simulation
    """
    # Time
    simulation_time: datetime = field(default_factory=lambda: datetime.utcnow().replace(hour=6, minute=0, second=0, microsecond=0))
    simulation_tick: int = 0

    # Entities
    bins: Dict[str, BinState] = field(default_factory=dict)
    trucks: Dict[str, TruckState] = field(default_factory=dict)
    facilities: Dict[str, FacilityState] = field(default_factory=dict)
    roads: Dict[str, RoadState] = field(default_factory=dict)
    events: Dict[str, EventState] = field(default_factory=dict)

    # Simulation state
    is_running: bool = False
    speed: int = 1  # 1x to 60x real-time

    # Metrics
    metrics: Dict = field(default_factory=lambda: {
        "total_distance_km": 0,
        "total_fuel_liters": 0,
        "total_co2_kg": 0,
        "overflow_events": 0,
        "bins_collected": 0,
        "trucks_deployed": 0
    })

    def to_dict(self) -> dict:
        """Export state to JSON-compatible dict"""
        return {
            "simulation_time": self.simulation_time.isoformat(),
            "simulation_tick": self.simulation_tick,
            "is_running": self.is_running,
            "speed": self.speed,
            "bins": {k: v.to_dict() for k, v in self.bins.items()},
            "trucks": {k: v.to_dict() for k, v in self.trucks.items()},
            "facilities": {k: v.to_dict() for k, v in self.facilities.items()},
            "roads": {k: v.to_dict() for k, v in self.roads.items()},
            "events": {k: v.to_dict() for k, v in self.events.items()},
            "metrics": self.metrics
        }

    def get_critical_bins(self, threshold: float = 80.0) -> List[BinState]:
        """Get bins above overflow threshold"""
        return [b for b in self.bins.values() if b.current_fill_pct >= threshold]

    def get_high_priority_bins(self, threshold: float = 70.0) -> List[BinState]:
        """Get bins with priority score above threshold"""
        return [b for b in self.bins.values() if b.priority_score >= threshold]

    def get_available_trucks(self) -> List[TruckState]:
        """Get trucks that are not broken down"""
        return [t for t in self.trucks.values() if t.status != "breakdown"]

    def get_active_events(self) -> List[EventState]:
        """Get currently active events"""
        now = self.simulation_time
        return [e for e in self.events.values() if e.is_active and not e.is_expired(now)]

    def clone(self) -> "DigitalTwinState":
        """Create a deep copy for What-If scenarios"""
        import copy
        new_state = DigitalTwinState(
            simulation_time=self.simulation_time,
            simulation_tick=self.simulation_tick,
            is_running=False,
            speed=self.speed,
            metrics=copy.deepcopy(self.metrics)
        )
        # Deep copy all entities
        new_state.bins = {k: copy.deepcopy(v) for k, v in self.bins.items()}
        new_state.trucks = {k: copy.deepcopy(v) for k, v in self.trucks.items()}
        new_state.facilities = {k: copy.deepcopy(v) for k, v in self.facilities.items()}
        new_state.roads = {k: copy.deepcopy(v) for k, v in self.roads.items()}
        new_state.events = {k: copy.deepcopy(v) for k, v in self.events.items()}
        return new_state