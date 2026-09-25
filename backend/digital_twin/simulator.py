"""
Simulation Engine for Digital Twin
Orchestrates the main simulation loop
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
import logging
from .city_generator import AurangabadCityState
from .state import (
    DigitalTwinState,
    BinState,
    TruckState,
    FacilityState,
    RoadState,
    EventState
)
from backend.config.settings import get_settings

logger = logging.getLogger(__name__)


class SimulationEngine:
    """Main simulation engine for Digital Twin"""

    def __init__(self):
        self.settings = get_settings()
        self.state = None
        self.city = None
        self.is_running = False
        self.current_tick = 0

    def initialize(self) -> DigitalTwinState:
        """Initialize the Digital Twin"""
        logger.info("Initializing Digital Twin...")

        # Initialize city generator
        self.city = AurangabadCityState(num_bins=100, seed=42)

        # Create Digital Twin state
        self.state = DigitalTwinState(
            simulation_time=self.city.current_date,
            simulation_tick=0
        )

        # Create bins from city data
        for bin_data in self.city.bins:
            bin_state = BinState(
                id=bin_data["id"],
                latitude=bin_data["latitude"],
                longitude=bin_data["longitude"],
                area_type=bin_data["area_type"],
                waste_type=bin_data["waste_type"],
                capacity_liters=bin_data["capacity_liters"],
                current_fill_pct=self.city.bin_states[bin_data["id"]]["fill_pct"],
                criticality=bin_data["criticality"],
                temperature=self.city.current_temperature,
                rainfall=self.city.current_rainfall
            )
            self.state.bins[bin_data["id"]] = bin_state

        # Create trucks
        for i in range(self.settings.default_num_trucks):
            truck_id = f"TRK-ANG-{i+1:02d}"
            truck = TruckState(
                id=truck_id,
                latitude=self.settings.aurangabad_lat,
                longitude=self.settings.aurangabad_lon,
                capacity_liters=self.settings.default_truck_capacity_liters,
                status="idle",
                driver_name=f"Driver {i+1}"
            )
            self.state.trucks[truck_id] = truck

        # Create facilities
        facilities_data = [
            {
                "id": "FAC-001",
                "name": "General Processing Plant",
                "type": "general_processing",
                "lat": 19.85,
                "lon": 75.36,
                "capacity": 10000,
                "waste_types": ["general"]
            },
            {
                "id": "FAC-002",
                "name": "Recycling Centre - West",
                "type": "recycling_center",
                "lat": 19.88,
                "lon": 75.32,
                "capacity": 5000,
                "waste_types": ["recyclable"]
            },
            {
                "id": "FAC-003",
                "name": "Composting Plant",
                "type": "composting",
                "lat": 19.84,
                "lon": 75.34,
                "capacity": 6000,
                "waste_types": ["organic"]
            },
            {
                "id": "FAC-004",
                "name": "E-Waste Facility",
                "type": "ewaste_facility",
                "lat": 19.87,
                "lon": 75.35,
                "capacity": 2000,
                "waste_types": ["ewaste"]
            },
            {
                "id": "DEPOT",
                "name": "Main Depot",
                "type": "depot",
                "lat": self.settings.aurangabad_lat,
                "lon": self.settings.aurangabad_lon,
                "capacity": 999999,
                "waste_types": []
            }
        ]

        for fac_data in facilities_data:
            facility = FacilityState(
                id=fac_data["id"],
                name=fac_data["name"],
                facility_type=fac_data["type"],
                latitude=fac_data["lat"],
                longitude=fac_data["lon"],
                daily_capacity_liters=fac_data["capacity"],
                accepted_waste_types=fac_data["waste_types"]
            )
            self.state.facilities[fac_data["id"]] = facility

        logger.info(f"✅ Digital Twin initialized with {len(self.state.bins)} bins and {len(self.state.trucks)} trucks")
        return self.state

    async def step(self) -> DigitalTwinState:
        """Execute one simulation step (1 hour)"""
        if not self.state:
            self.initialize()

        # Step city simulation
        city_changes = self.city.step_one_hour()

        # Update state time
        self.state.simulation_time = self.city.current_date
        self.state.simulation_tick += 1
        self.current_tick = self.state.simulation_tick

        # Update bins from city simulation
        for bin_id, changes in city_changes["bins"].items():
            if bin_id in self.state.bins:
                bin_state = self.state.bins[bin_id]
                bin_state.current_fill_pct = changes["fill_pct"]
                bin_state.hours_since_collection = changes["hours_since_collection"]
                bin_state.temperature = changes["temperature"]
                bin_state.rainfall = changes["rainfall"]

                # Calculate growth rate
                if bin_state.current_fill_pct > 0:
                    bin_state.growth_rate_pct_per_hour = changes["fill_pct"] - bin_state.current_fill_pct

        # Apply active events
        from backend.services.event_service import get_event_engine
        event_engine = get_event_engine()
        event_engine.cleanup_expired_events(self.state)
        event_engine.apply_all_active_events(self.state)

        logger.debug(f"Simulation tick {self.state.simulation_tick}: {self.state.simulation_time}")

        return self.state

    def inject_event(self, event_type: str, params: Dict) -> EventState:
        """Inject an event into the simulation"""
        event_id = f"EVT-{len(self.state.events)+1:03d}"

        if event_type == "festival":
            zone = params.get("zone", "Market_Area")
            intensity = params.get("intensity", 1.5)
            duration_hours = params.get("duration_hours", 24)
            end_time = self.state.simulation_time + timedelta(hours=duration_hours)

        elif event_type == "heavy_rain":
            zone = params.get("zone", "all")
            intensity = params.get("intensity", 1.3)
            duration_hours = params.get("duration_hours", 6)
            end_time = self.state.simulation_time + timedelta(hours=duration_hours)

        elif event_type == "road_closure":
            zone = params.get("zone", "Paithan_Road")
            intensity = 1.0
            duration_hours = params.get("duration_hours", 4)
            end_time = self.state.simulation_time + timedelta(hours=duration_hours)

        elif event_type == "truck_breakdown":
            zone = params.get("zone", "any")
            intensity = 1.0
            duration_hours = params.get("duration_hours", 3)
            end_time = self.state.simulation_time + timedelta(hours=duration_hours)

        else:
            raise ValueError(f"Unknown event type: {event_type}")

        event = EventState(
            id=event_id,
            type=event_type,
            zone=zone,
            start_time=self.state.simulation_time,
            end_time=end_time,
            intensity=intensity,
            params=params,
            is_active=True
        )

        self.state.events[event_id] = event
        logger.info(f"Event injected: {event_type} in {zone} (intensity: {intensity}x)")

        return event

    def get_state(self) -> Dict:
        """Get current simulation state as dict"""
        if not self.state:
            self.initialize()
        return self.state.to_dict()

    def reset(self):
        """Reset simulation to initial state"""
        logger.info("Resetting simulation...")
        self.state = None
        self.city = None
        self.current_tick = 0
        self.initialize()


# Global simulation engine instance
_engine = None


def get_simulation_engine() -> SimulationEngine:
    """Get or create the global simulation engine"""
    global _engine
    if _engine is None:
        _engine = SimulationEngine()
    return _engine


async def run_simulation_loop(engine: SimulationEngine, speed: int = 1):
    """Run continuous simulation loop"""
    logger.info(f"Starting simulation loop at {speed}x speed")

    if not engine.state:
        engine.initialize()

    engine.is_running = True

    try:
        while engine.is_running:
            # Execute one simulation step
            await engine.step()

            # Calculate sleep time based on speed
            # 1x = 1 real second per simulation hour
            sleep_seconds = max(0.1, 1.0 / speed)
            await asyncio.sleep(sleep_seconds)

    except Exception as e:
        logger.error(f"Simulation error: {e}", exc_info=True)
        engine.is_running = False


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def test():
        engine = get_simulation_engine()
        engine.initialize()

        print("🚀 Running 10 simulation steps...")
        for i in range(10):
            await engine.step()
            state = engine.get_state()
            print(f"Tick {i+1}: {state['simulation_time']} - Critical bins: {len([b for b in state['bins'].values() if b['current_fill_pct'] > 90])}")

        print("\n💥 Injecting festival event...")
        engine.inject_event("festival", {"zone": "Market_Area", "intensity": 1.5, "duration_hours": 12})

        print("Continuing simulation for 5 more steps...")
        for i in range(5):
            await engine.step()

        print(f"\n✅ Test complete. Total ticks: {engine.current_tick}")

    asyncio.run(test())
