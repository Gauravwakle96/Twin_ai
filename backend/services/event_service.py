"""
Event Engine - Handle disruptions and dynamic events
"""
import logging
from typing import Dict, List
from datetime import datetime, timedelta
from backend.digital_twin.state import DigitalTwinState, EventState, BinState, TruckState, RoadState
from backend.config.settings import get_settings

logger = logging.getLogger(__name__)


class EventEngine:
    """Applies event effects to Digital Twin state"""

    def __init__(self):
        self.settings = get_settings()

    def apply_festival(self, state: DigitalTwinState, event: EventState):
        """
        Festival increases waste generation in affected zone
        """
        zone = event.params.get("zone", "Market_Area")
        waste_multiplier = event.params.get("waste_multiplier", event.intensity)

        affected_bins = [
            b for b in state.bins.values()
            if zone.lower() in b.id.lower() or zone.replace("_", " ").lower() in str(b.area_type).lower()
        ]

        for bin_state in affected_bins:
            # Increase growth rate
            bin_state.growth_rate_pct_per_hour *= waste_multiplier

        logger.info(f"Festival effect applied to {len(affected_bins)} bins in {zone} (multiplier: {waste_multiplier}x)")

    def apply_heavy_rain(self, state: DigitalTwinState, event: EventState):
        """
        Heavy rain increases travel times on all roads
        """
        intensity = event.intensity  # 1.0 - 2.0
        travel_multiplier = self.settings.rain_road_multiplier * intensity

        # Update all roads
        for road in state.roads.values():
            if road.status == "open":
                road.travel_time_multiplier = travel_multiplier
                road.status = "rain"

        logger.info(f"Heavy rain effect applied to {len(state.roads)} roads (multiplier: {travel_multiplier}x)")

    def apply_road_closure(self, state: DigitalTwinState, event: EventState):
        """
        Road closure makes specific roads unavailable
        """
        affected_roads = event.params.get("roads", [])

        if not affected_roads:
            # Close roads in the affected zone (simplified)
            zone = event.zone
            affected_roads = [r.id for r in state.roads.values() if zone.lower() in r.id.lower()]

        for road_id in affected_roads:
            if road_id in state.roads:
                state.roads[road_id].status = "closed"
                state.roads[road_id].travel_time_multiplier = self.settings.closed_road_multiplier

        logger.info(f"Road closure applied to {len(affected_roads)} roads in {event.zone}")

    def apply_truck_breakdown(self, state: DigitalTwinState, event: EventState):
        """
        Truck breakdown makes a vehicle unavailable
        """
        truck_id = event.params.get("truck_id")

        if not truck_id:
            # Pick a random active truck
            active_trucks = [t for t in state.trucks.values() if t.status == "enroute"]
            if active_trucks:
                truck_id = active_trucks[0].id

        if truck_id and truck_id in state.trucks:
            truck = state.trucks[truck_id]
            truck.status = "breakdown"

            # Release assigned bins back to unassigned pool
            if truck.assigned_bins:
                for bin_id in truck.assigned_bins:
                    if bin_id in state.bins:
                        state.bins[bin_id].decision = "REASSIGN"

                logger.info(f"Truck breakdown: {truck_id} broke down. {len(truck.assigned_bins)} bins need reassignment.")
                truck.assigned_bins = []
                truck.route = []

    def apply_all_active_events(self, state: DigitalTwinState):
        """
        Apply all currently active events to the state
        """
        active_events = state.get_active_events()

        if not active_events:
            # Reset any event-affected state to normal
            self.reset_event_effects(state)
            return

        logger.info(f"Applying {len(active_events)} active events...")

        for event in active_events:
            if event.type == "festival":
                self.apply_festival(state, event)
            elif event.type == "heavy_rain":
                self.apply_heavy_rain(state, event)
            elif event.type == "road_closure":
                self.apply_road_closure(state, event)
            elif event.type == "truck_breakdown":
                self.apply_truck_breakdown(state, event)
            else:
                logger.warning(f"Unknown event type: {event.type}")

    def reset_event_effects(self, state: DigitalTwinState):
        """
        Reset state to normal when no events are active
        """
        # Reset roads
        for road in state.roads.values():
            if road.status != "open":
                road.status = "open"
                road.travel_time_multiplier = self.settings.normal_road_multiplier

        # Reset bins growth rates (would need baseline stored)
        # For now, bins naturally return to normal via simulation

        # Reset broken trucks after repair time
        for truck in state.trucks.values():
            if truck.status == "breakdown":
                # Check if event has expired
                breakdown_events = [
                    e for e in state.events.values()
                    if e.type == "truck_breakdown" and e.params.get("truck_id") == truck.id
                ]
                if not any(e.is_active for e in breakdown_events):
                    truck.status = "idle"
                    logger.info(f"Truck {truck.id} repaired and back in service")

    def cleanup_expired_events(self, state: DigitalTwinState):
        """
        Remove expired events from state
        """
        expired = [
            event_id for event_id, event in state.events.items()
            if event.is_expired(state.simulation_time)
        ]

        for event_id in expired:
            event = state.events[event_id]
            event.is_active = False
            logger.info(f"Event expired: {event.type} in {event.zone}")

        return len(expired)


class EventInjector:
    """Helper to inject pre-defined events"""

    def __init__(self):
        self.settings = get_settings()

    def inject_festival(
        self,
        state: DigitalTwinState,
        zone: str = "Market_Area",
        duration_hours: int = 12,
        intensity: float = 1.5
    ) -> EventState:
        """Inject a festival event"""
        event_id = f"EVT-{len(state.events) + 1:03d}"

        event = EventState(
            id=event_id,
            type="festival",
            zone=zone,
            start_time=state.simulation_time,
            end_time=state.simulation_time + timedelta(hours=duration_hours),
            intensity=intensity,
            params={"waste_multiplier": intensity},
            is_active=True
        )

        state.events[event_id] = event
        logger.info(f"Festival injected: {zone} for {duration_hours}h (intensity: {intensity}x)")
        return event

    def inject_heavy_rain(
        self,
        state: DigitalTwinState,
        duration_hours: int = 6,
        intensity: float = 1.3
    ) -> EventState:
        """Inject a heavy rain event"""
        event_id = f"EVT-{len(state.events) + 1:03d}"

        event = EventState(
            id=event_id,
            type="heavy_rain",
            zone="city_wide",
            start_time=state.simulation_time,
            end_time=state.simulation_time + timedelta(hours=duration_hours),
            intensity=intensity,
            params={},
            is_active=True
        )

        state.events[event_id] = event
        logger.info(f"Heavy rain injected for {duration_hours}h (intensity: {intensity}x)")
        return event

    def inject_road_closure(
        self,
        state: DigitalTwinState,
        zone: str = "Paithan_Road",
        duration_hours: int = 4,
        roads: List[str] = None
    ) -> EventState:
        """Inject a road closure event"""
        event_id = f"EVT-{len(state.events) + 1:03d}"

        event = EventState(
            id=event_id,
            type="road_closure",
            zone=zone,
            start_time=state.simulation_time,
            end_time=state.simulation_time + timedelta(hours=duration_hours),
            intensity=1.0,
            params={"roads": roads or []},
            is_active=True
        )

        state.events[event_id] = event
        logger.info(f"Road closure injected in {zone} for {duration_hours}h")
        return event

    def inject_truck_breakdown(
        self,
        state: DigitalTwinState,
        truck_id: str = None,
        duration_hours: int = 3
    ) -> EventState:
        """Inject a truck breakdown event"""
        event_id = f"EVT-{len(state.events) + 1:03d}"

        event = EventState(
            id=event_id,
            type="truck_breakdown",
            zone="any",
            start_time=state.simulation_time,
            end_time=state.simulation_time + timedelta(hours=duration_hours),
            intensity=1.0,
            params={"truck_id": truck_id},
            is_active=True
        )

        state.events[event_id] = event
        logger.info(f"Truck breakdown injected: {truck_id} for {duration_hours}h")
        return event


# Global instances
_event_engine = None
_event_injector = None


def get_event_engine() -> EventEngine:
    """Get or create global event engine"""
    global _event_engine
    if _event_engine is None:
        _event_engine = EventEngine()
    return _event_engine


def get_event_injector() -> EventInjector:
    """Get or create global event injector"""
    global _event_injector
    if _event_injector is None:
        _event_injector = EventInjector()
    return _event_injector


if __name__ == "__main__":
    import logging
    from backend.digital_twin.simulator import get_simulation_engine

    logging.basicConfig(level=logging.INFO)

    print("Testing Event Engine...")

    # Initialize simulation
    engine = get_simulation_engine()
    state = engine.initialize()

    # Get event components
    event_engine = get_event_engine()
    event_injector = get_event_injector()

    print(f"\nInitial state: {len(state.bins)} bins, {len(state.trucks)} trucks")

    # Test festival
    print("\n1. Injecting festival event...")
    festival = event_injector.inject_festival(state, zone="Market_Area", duration_hours=12, intensity=1.5)
    event_engine.apply_all_active_events(state)
    print(f"   Festival active: {festival.is_active}")

    # Test heavy rain
    print("\n2. Injecting heavy rain event...")
    rain = event_injector.inject_heavy_rain(state, duration_hours=6, intensity=1.3)
    event_engine.apply_all_active_events(state)
    print(f"   Rain active: {rain.is_active}")

    # Test truck breakdown
    print("\n3. Injecting truck breakdown...")
    breakdown = event_injector.inject_truck_breakdown(state, truck_id="TRK-ANG-01", duration_hours=3)
    event_engine.apply_all_active_events(state)
    truck_status = state.trucks["TRK-ANG-01"].status
    print(f"   Truck TRK-ANG-01 status: {truck_status}")

    print("\n✅ Event engine test complete!")
