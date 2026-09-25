"""
Orchestrator Service - Runs the complete AI loop
"""
import logging
from typing import Dict, List
from backend.digital_twin.state import DigitalTwinState
from backend.services.prediction_service import get_prediction_service
from backend.services.priority_service import (
    get_priority_engine, get_anomaly_detector, get_decision_engine
)
from backend.optimization.routing import (
    get_vehicle_allocator, get_destination_selector, get_route_solver
)

logger = logging.getLogger(__name__)


class SimulationOrchestrator:
    """Orchestrates the complete AI loop for Digital Twin"""

    def __init__(self):
        self.prediction_service = get_prediction_service()
        self.priority_engine = get_priority_engine()
        self.anomaly_detector = get_anomaly_detector()
        self.decision_engine = get_decision_engine()
        self.vehicle_allocator = get_vehicle_allocator()
        self.destination_selector = get_destination_selector()
        self.route_solver = get_route_solver()

    def run_full_loop(self, state: DigitalTwinState) -> Dict:
        """
        Run the complete AI loop:
        1. Predict fill levels
        2. Score priorities
        3. Detect anomalies
        4. Decide collect/wait/reassign
        5. Allocate vehicles
        6. Optimize routes

        Returns: summary dict
        """
        logger.info("🔄 Running complete AI loop...")

        results = {
            "timestamp": state.simulation_time.isoformat(),
            "tick": state.simulation_tick
        }

        # Step 1: ML Predictions
        predictions = self.prediction_service.predict_all_bins(state, horizons=[1, 2, 4])
        results["predictions"] = len(predictions)

        # Step 2: Anomaly Detection
        anomalies = self.anomaly_detector.detect_all_anomalies(state.bins)
        anomaly_count = len([a for a, _ in anomalies.values() if a])
        results["anomalies"] = anomaly_count

        # Step 3: Priority Scoring
        priorities = self.priority_engine.calculate_all_priorities(state.bins)
        high_priority_bins = [bin_id for bin_id, (score, _) in priorities.items() if score > 70]
        results["high_priority_bins"] = len(high_priority_bins)
        results["avg_priority"] = round(sum(score for score, _ in priorities.values()) / len(priorities), 1)

        # Step 4: Decision Making
        available_trucks = [t for t in state.trucks.values() if t.status in ["idle", "enroute"]]
        decisions = self.decision_engine.decide_all_actions(state.bins, len(available_trucks))
        collect_bins = [bin_id for bin_id, action in decisions.items() if action == "COLLECT"]
        wait_bins = [bin_id for bin_id, action in decisions.items() if action == "WAIT"]
        reassign_bins = [bin_id for bin_id, action in decisions.items() if action == "REASSIGN"]
        results["decisions"] = {"collect": len(collect_bins), "wait": len(wait_bins), "reassign": len(reassign_bins)}

        # Step 5: Vehicle Allocation (only for bins to collect)
        collect_bin_states = [state.bins[bin_id] for bin_id in collect_bins]
        allocations = self.vehicle_allocator.allocate(
            collect_bin_states,
            available_trucks,
            state.facilities["DEPOT"].latitude,
            state.facilities["DEPOT"].longitude
        )
        results["allocations"] = sum(len(bins) for bins in allocations.values())

        # Step 6: Route Optimization
        routes = {}
        for truck_id, bin_ids in allocations.items():
            if bin_ids:
                truck = state.trucks[truck_id]
                route = self.route_solver.solve(truck, bin_ids, state)
                routes[truck_id] = route

                # Update truck state
                truck.assigned_bins = bin_ids
                truck.route = route["stops"]
                truck.status = "enroute"

        results["routes"] = len(routes)

        # Calculate metrics
        if routes:
            total_distance = sum(r["distance_km"] for r in routes.values())
            total_fuel = sum(r["fuel_liters"] for r in routes.values())
            total_co2 = sum(r["co2_kg"] for r in routes.values())
            avg_utilization = sum(r["utilization_pct"] for r in routes.values()) / len(routes)

            results["metrics"] = {
                "total_distance_km": round(total_distance, 1),
                "total_fuel_liters": round(total_fuel, 1),
                "total_co2_kg": round(total_co2, 1),
                "avg_utilization_pct": round(avg_utilization, 1)
            }

        # Update state metrics
        state.metrics["total_distance_km"] += results.get("metrics", {}).get("total_distance_km", 0)
        state.metrics["total_fuel_liters"] += results.get("metrics", {}).get("total_fuel_liters", 0)
        state.metrics["total_co2_kg"] += results.get("metrics", {}).get("total_co2_kg", 0)

        # Count overflow events
        overflow_events = len([b for b in state.bins.values() if b.current_fill_pct > 95])
        results["overflow_events"] = overflow_events
        state.metrics["overflow_events"] += overflow_events

        logger.info(f"✅ AI loop complete. Results: {results}")
        return results

    def run_what_if_scenario(
        self,
        base_state: DigitalTwinState,
        event_type: str,
        event_params: Dict
    ) -> Dict:
        """
        Run a What-If scenario on a cloned state
        """
        logger.info(f"Running What-If: {event_type} with {event_params}")

        # Clone state
        scenario_state = base_state.clone()

        # Inject event
        # (Event engine will handle this later)

        # Run full loop
        results = self.run_full_loop(scenario_state)

        return {
            "scenario": event_type,
            "params": event_params,
            "results": results
        }


# Global orchestrator
_orchestrator = None


def get_orchestrator() -> SimulationOrchestrator:
    """Get or create global orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SimulationOrchestrator()
    return _orchestrator


if __name__ == "__main__":
    import logging
    from backend.digital_twin.simulator import get_simulation_engine

    logging.basicConfig(level=logging.INFO)

    print("Testing Orchestrator...")

    # Initialize simulation
    engine = get_simulation_engine()
    state = engine.initialize()

    # Create orchestrator
    orchestrator = SimulationOrchestrator()

    # Run one loop
    results = orchestrator.run_full_loop(state)

    print("\nResults Summary:")
    print(f"Tick: {results['tick']}")
    print(f"Predictions: {results['predictions']}")
    print(f"Anomalies: {results['anomalies']}")
    print(f"High priority bins: {results['high_priority_bins']}")
    print(f"Decisions: Collect={results['decisions']['collect']}, Wait={results['decisions']['wait']}, Reassign={results['decisions']['reassign']}")
    print(f"Allocations: {results['allocations']} bins")
    print(f"Routes: {results['routes']} trucks")

    if "metrics" in results:
        print(f"Distance: {results['metrics']['total_distance_km']}km")
        print(f"Fuel: {results['metrics']['total_fuel_liters']}L")
        print(f"CO₂: {results['metrics']['total_co2_kg']}kg")
        print(f"Utilization: {results['metrics']['avg_utilization_pct']}%")
