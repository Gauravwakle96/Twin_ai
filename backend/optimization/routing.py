"""
Vehicle Allocation and OR-Tools Route Optimization
"""
import logging
import math
from typing import Dict, List, Tuple, Optional
from ortools.constraint_solver import routing_enums_pb2, pywrapcp
from backend.digital_twin.state import DigitalTwinState, BinState, TruckState, FacilityState
from backend.config.settings import get_settings

logger = logging.getLogger(__name__)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great circle distance between two points
    Returns distance in kilometers
    """
    R = 6371.0  # Earth radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance * 1.3  # 1.3x routing multiplier for road network


class VehicleAllocator:
    """Allocate bins to trucks based on proximity and capacity"""

    def __init__(self):
        self.settings = get_settings()

    def allocate(
        self,
        bins_to_collect: List[BinState],
        available_trucks: List[TruckState],
        depot_lat: float,
        depot_lon: float
    ) -> Dict[str, List[str]]:
        """
        Allocate bins to trucks using greedy proximity matching
        Returns: {truck_id: [bin_id1, bin_id2, ...]}
        """
        logger.info(f"Allocating {len(bins_to_collect)} bins to {len(available_trucks)} trucks...")

        # Sort bins by priority descending
        sorted_bins = sorted(bins_to_collect, key=lambda b: b.priority_score, reverse=True)

        # Initialize allocations
        allocations = {truck.id: [] for truck in available_trucks}
        truck_loads = {truck.id: 0.0 for truck in available_trucks}

        # Greedy allocation
        for bin_state in sorted_bins:
            bin_demand = bin_state.capacity_liters * (bin_state.current_fill_pct / 100.0)

            # Find best available truck
            best_truck = None
            best_score = float('inf')

            for truck in available_trucks:
                # Check capacity
                if truck_loads[truck.id] + bin_demand > truck.capacity_liters:
                    continue  # Skip if no capacity

                # Calculate distance from truck's last position to bin
                if allocations[truck.id]:
                    # Truck has assignments, use last bin location
                    last_bin_id = allocations[truck.id][-1]
                    last_bin = next((b for b in bins_to_collect if b.id == last_bin_id), None)
                    if last_bin:
                        truck_lat = last_bin.latitude
                        truck_lon = last_bin.longitude
                    else:
                        truck_lat = truck.latitude
                        truck_lon = truck.longitude
                else:
                    # Truck has no assignments, use depot
                    truck_lat = depot_lat
                    truck_lon = depot_lon

                distance = haversine_distance(truck_lat, truck_lon, bin_state.latitude, bin_state.longitude)

                # Calculate score (lower is better)
                utilization = truck_loads[truck.id] / truck.capacity_liters
                score = distance - (0.3 * (1.0 - utilization) * 10)  # Prefer trucks with more capacity

                if score < best_score:
                    best_score = score
                    best_truck = truck

            # Assign bin to best truck
            if best_truck:
                allocations[best_truck.id].append(bin_state.id)
                truck_loads[best_truck.id] += bin_demand
                logger.debug(f"  Allocated {bin_state.id} to {best_truck.id} (load: {truck_loads[best_truck.id]:.1f}L)")
            else:
                logger.warning(f"  Could not allocate {bin_state.id} (no capacity)")

        # Log summary
        for truck_id, bin_ids in allocations.items():
            if bin_ids:
                load = truck_loads[truck_id]
                truck = next(t for t in available_trucks if t.id == truck_id)
                utilization = (load / truck.capacity_liters) * 100
                logger.info(f"  {truck_id}: {len(bin_ids)} bins, {load:.1f}L ({utilization:.1f}%)")

        return allocations


class DestinationSelector:
    """Select appropriate facility for each bin based on waste type"""

    def select_destination(
        self,
        bin_state: BinState,
        facilities: Dict[str, FacilityState]
    ) -> Optional[str]:
        """
        Select best facility for bin's waste type
        Returns: facility_id or None if no capacity
        """
        # Filter facilities by waste type
        compatible = [
            fac for fac in facilities.values()
            if bin_state.waste_type in fac.accepted_waste_types and fac.is_active
        ]

        if not compatible:
            logger.warning(f"No compatible facility for {bin_state.id} (waste type: {bin_state.waste_type})")
            return None

        # Sort by remaining capacity and distance
        bin_demand = bin_state.capacity_liters * (bin_state.current_fill_pct / 100.0)

        best_facility = None
        best_score = float('inf')

        for fac in compatible:
            # Check capacity
            if fac.remaining_capacity < bin_demand:
                continue

            # Calculate distance
            distance = haversine_distance(bin_state.latitude, bin_state.longitude, fac.latitude, fac.longitude)

            # Score (prefer closer + more remaining capacity)
            utilization = fac.current_load_liters / fac.daily_capacity_liters
            score = distance + (utilization * 10)

            if score < best_score:
                best_score = score
                best_facility = fac

        if best_facility:
            return best_facility.id
        else:
            logger.warning(f"No facility with capacity for {bin_state.id}")
            return None


class RouteSolver:
    """Solve CVRP using Google OR-Tools"""

    def __init__(self):
        self.settings = get_settings()

    def solve(
        self,
        truck: TruckState,
        bin_ids: List[str],
        state: DigitalTwinState
    ) -> Dict:
        """
        Solve vehicle routing for one truck
        Returns: route dict with stops, distance, etc.
        """
        if not bin_ids:
            return {"truck_id": truck.id, "stops": [], "distance_km": 0, "load_liters": 0}

        logger.info(f"Solving route for {truck.id} with {len(bin_ids)} bins...")

        # Get depot location
        depot_lat = self.settings.aurangabad_lat
        depot_lon = self.settings.aurangabad_lon

        # Build locations list: [depot, bin1, bin2, ..., facilities]
        locations = [(depot_lat, depot_lon)]  # Index 0 = depot
        bin_indices = {}
        demands = [0]  # Depot has 0 demand

        for i, bin_id in enumerate(bin_ids):
            bin_state = state.bins[bin_id]
            locations.append((bin_state.latitude, bin_state.longitude))
            bin_indices[bin_id] = i + 1
            demand = bin_state.capacity_liters * (bin_state.current_fill_pct / 100.0)
            demands.append(int(demand))

        # Build distance matrix
        num_locations = len(locations)
        distance_matrix = [[0] * num_locations for _ in range(num_locations)]

        for i in range(num_locations):
            for j in range(num_locations):
                if i != j:
                    dist = haversine_distance(
                        locations[i][0], locations[i][1],
                        locations[j][0], locations[j][1]
                    )
                    distance_matrix[i][j] = int(dist * 1000)  # Convert to meters

        # Create routing model
        manager = pywrapcp.RoutingIndexManager(num_locations, 1, 0)  # 1 vehicle, depot at 0
        routing = pywrapcp.RoutingModel(manager)

        # Distance callback
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return distance_matrix[from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Demand/Capacity constraint
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return demands[from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # No slack
            [int(truck.capacity_liters)],  # Vehicle capacity
            True,  # Start cumul at zero
            'Capacity'
        )

        # Search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = 5

        # Solve
        solution = routing.SolveWithParameters(search_parameters)

        if not solution:
            logger.error(f"No solution found for {truck.id}")
            return {"truck_id": truck.id, "stops": [], "distance_km": 0, "load_liters": 0}

        # Extract route
        route = []
        index = routing.Start(0)
        total_distance = 0
        total_load = 0

        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node == 0:
                route.append({"type": "depot", "lat": depot_lat, "lon": depot_lon})
            else:
                # Find bin
                bin_id = bin_ids[node - 1]
                bin_state = state.bins[bin_id]
                load = bin_state.capacity_liters * (bin_state.current_fill_pct / 100.0)
                total_load += load
                route.append({
                    "type": "bin",
                    "bin_id": bin_id,
                    "lat": bin_state.latitude,
                    "lon": bin_state.longitude,
                    "load_liters": round(load, 1)
                })

            previous_index = index
            index = solution.Value(routing.NextVar(index))
            total_distance += routing.GetArcCostForVehicle(previous_index, index, 0)

        # Add depot return
        route.append({"type": "depot", "lat": depot_lat, "lon": depot_lon})

        total_distance_km = total_distance / 1000.0  # Convert to km
        fuel_liters = total_distance_km * 0.3
        co2_kg = fuel_liters * 2.68

        logger.info(f"✅ Route for {truck.id}: {len(route)} stops, {total_distance_km:.1f}km, {total_load:.1f}L")

        return {
            "truck_id": truck.id,
            "stops": route,
            "distance_km": round(total_distance_km, 2),
            "load_liters": round(total_load, 1),
            "fuel_liters": round(fuel_liters, 2),
            "co2_kg": round(co2_kg, 2),
            "utilization_pct": round((total_load / truck.capacity_liters) * 100, 1)
        }


# Global instances
_allocator = None
_destination_selector = None
_route_solver = None


def get_vehicle_allocator() -> VehicleAllocator:
    global _allocator
    if _allocator is None:
        _allocator = VehicleAllocator()
    return _allocator


def get_destination_selector() -> DestinationSelector:
    global _destination_selector
    if _destination_selector is None:
        _destination_selector = DestinationSelector()
    return _destination_selector


def get_route_solver() -> RouteSolver:
    global _route_solver
    if _route_solver is None:
        _route_solver = RouteSolver()
    return _route_solver
