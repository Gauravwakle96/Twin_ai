"""
Aurangabad City Data Generator
Real locations and waste generation patterns for 100 virtual bins
"""
from dataclasses import dataclass
from typing import List, Dict, Tuple
import random
from datetime import datetime, timedelta
import math


# =============================================================================
# Aurangabad City Geography
# =============================================================================

AURANGABAD_CENTER = (19.8762, 75.3433)  # Chhatrapati Sambhajinagar

# Real Aurangabad landmarks and zones
AURANGABAD_ZONES = {
    "Paithan_Road": {"lat": 19.88, "lon": 75.35, "bins": 12},
    "Station_Road": {"lat": 19.87, "lon": 75.33, "bins": 10},
    "CIDCO": {"lat": 19.90, "lon": 75.36, "bins": 15},
    "Ashok_Nagar": {"lat": 19.87, "lon": 75.32, "bins": 8},
    "Jalna_Road": {"lat": 19.86, "lon": 75.34, "bins": 10},
    "Beed_Road": {"lat": 19.85, "lon": 75.35, "bins": 8},
    "Daulatabad": {"lat": 19.84, "lon": 75.32, "bins": 6},
    "Bibi_Ka_Maqbara": {"lat": 19.84, "lon": 75.34, "bins": 5},
    "Railway_Station": {"lat": 19.87, "lon": 75.32, "bins": 7},
    "Bus_Stand": {"lat": 19.88, "lon": 75.34, "bins": 5},
    "Civil_Hospital": {"lat": 19.86, "lon": 75.36, "bins": 3},
    "Market_Area": {"lat": 19.87, "lon": 75.33, "bins": 8},
    "Parks": {"lat": 19.89, "lon": 75.35, "bins": 3},
}

# Area-specific waste generation parameters
AREA_PARAMETERS = {
    "Market": {
        "base_fill_rate": 3.8,
        "peak_hours": [8, 9, 10, 11, 12, 16, 17, 18, 19],
        "population_density": 12000,
        "holiday_boost": 1.6,
        "capacity": 240
    },
    "Residential": {
        "base_fill_rate": 1.8,
        "peak_hours": [7, 8, 12, 19, 20],
        "population_density": 5000,
        "holiday_boost": 1.2,
        "capacity": 180
    },
    "Commercial": {
        "base_fill_rate": 2.5,
        "peak_hours": [9, 10, 12, 14, 16, 18],
        "population_density": 8000,
        "holiday_boost": 1.1,
        "capacity": 240
    },
    "Hospital": {
        "base_fill_rate": 2.2,
        "peak_hours": [8, 9, 10, 12, 14, 16, 18],
        "population_density": 3000,
        "holiday_boost": 1.0,
        "capacity": 200
    },
    "School": {
        "base_fill_rate": 2.0,
        "peak_hours": [10, 11, 12, 14, 15],
        "population_density": 2000,
        "holiday_boost": 0.5,
        "capacity": 150
    },
    "Restaurant": {
        "base_fill_rate": 3.2,
        "peak_hours": [12, 13, 18, 19, 20],
        "population_density": 5000,
        "holiday_boost": 1.5,
        "capacity": 200
    },
    "Mall": {
        "base_fill_rate": 3.5,
        "peak_hours": [10, 11, 12, 14, 15, 17, 18, 19, 20],
        "population_density": 10000,
        "holiday_boost": 1.8,
        "capacity": 300
    },
    "Bus_Stand": {
        "base_fill_rate": 3.0,
        "peak_hours": [6, 7, 9, 11, 14, 16, 18, 20],
        "population_density": 8000,
        "holiday_boost": 1.4,
        "capacity": 250
    },
    "Railway_Station": {
        "base_fill_rate": 3.0,
        "peak_hours": [6, 7, 8, 10, 12, 14, 18, 20],
        "population_density": 9000,
        "holiday_boost": 1.5,
        "capacity": 300
    },
    "Park": {
        "base_fill_rate": 0.9,
        "peak_hours": [6, 7, 17, 18, 19],
        "population_density": 2000,
        "holiday_boost": 1.7,
        "capacity": 150
    },
    "Industrial": {
        "base_fill_rate": 2.0,
        "peak_hours": [8, 9, 10, 12, 14, 16, 17],
        "population_density": 1000,
        "holiday_boost": 0.8,
        "capacity": 240
    },
}

# Aurangabad holidays and festivals
AURANGABAD_HOLIDAYS = {
    "2024-01-26": "Republic Day",
    "2024-03-08": "Maha Shivaratri",
    "2024-03-29": "Good Friday",
    "2024-04-11": "Eid ul-Fitr",
    "2024-04-21": "Ram Navami",
    "2024-05-23": "Buddha Purnima",
    "2024-06-17": "Eid ul-Adha",
    "2024-07-17": "Muharram",
    "2024-08-15": "Independence Day",
    "2024-08-26": "Janmashtami",
    "2024-09-16": "Milad un-Nabi",
    "2024-10-02": "Gandhi Jayanti",
    "2024-10-12": "Dussehra",
    "2024-10-31": "Diwali",
    "2024-11-01": "Diwali (Day 2)",
    "2024-11-15": "Guru Nanak Jayanti",
    "2024-12-25": "Christmas",
    "2024-03-16": "Holi",
    "2024-11-01": "Marathwada Divas",
}


class AurangabadCityGenerator:
    """Generate realistic Aurangabad city with 100 waste bins"""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.bins = []
        self.zone_index = 0

    def generate_bins(self, num_bins: int = 100) -> List[Dict]:
        """Generate list of bins with real Aurangabad locations"""
        bins = []
        bin_id = 1

        for zone_name, zone_data in AURANGABAD_ZONES.items():
            zone_bins = zone_data["bins"]
            base_lat = zone_data["lat"]
            base_lon = zone_data["lon"]

            for _ in range(zone_bins):
                # Add slight random variation to location within zone
                lat = base_lat + random.uniform(-0.005, 0.005)  # ~500m variation
                lon = base_lon + random.uniform(-0.005, 0.005)

                # Determine area type based on zone name
                area_type = self._determine_area_type(zone_name)

                # Get parameters for this area
                params = AREA_PARAMETERS.get(area_type, AREA_PARAMETERS["Residential"])

                bin_info = {
                    "id": f"BIN{bin_id:03d}",
                    "latitude": lat,
                    "longitude": lon,
                    "zone": zone_name,
                    "area_type": area_type,
                    "waste_type": random.choice(["general", "organic", "recyclable", "ewaste"]),
                    "capacity_liters": params["capacity"],
                    "criticality": random.choices(
                        ["Low", "Medium", "High"],
                        weights=[30, 50, 20]
                    )[0],
                    "base_fill_rate": params["base_fill_rate"],
                    "peak_hours": params["peak_hours"],
                    "population_density": params["population_density"],
                    "holiday_boost": params["holiday_boost"],
                }
                bins.append(bin_info)
                bin_id += 1

        self.bins = bins
        return bins[:num_bins]  # Return requested number

    def _determine_area_type(self, zone_name: str) -> str:
        """Map zone name to area type"""
        zone_lower = zone_name.lower()

        if "market" in zone_lower or "station" in zone_lower:
            return "Market"
        elif "cidco" in zone_lower or "ashok" in zone_lower or "nagar" in zone_lower:
            return "Residential"
        elif "hospital" in zone_lower:
            return "Hospital"
        elif "school" in zone_lower or "college" in zone_lower:
            return "School"
        elif "mall" in zone_lower or "plaza" in zone_lower:
            return "Mall"
        elif "bus" in zone_lower:
            return "Bus_Stand"
        elif "railway" in zone_lower or "station" in zone_lower:
            return "Railway_Station"
        elif "park" in zone_lower:
            return "Park"
        elif "maqbara" in zone_lower or "daulatabad" in zone_lower:
            return "Commercial"
        else:
            return "Residential"

    def get_bin(self, bin_id: str) -> Dict:
        """Get bin data by ID"""
        for bin_data in self.bins:
            if bin_data["id"] == bin_id:
                return bin_data
        return None


# =============================================================================
# Waste Generation Simulator
# =============================================================================

class WasteGenerationSimulator:
    """Simulate realistic hourly waste generation for bins"""

    def __init__(self, generator: AurangabadCityGenerator, seed: int = 42):
        self.generator = generator
        random.seed(seed)
        self.collection_history = {}  # Track when each bin was last collected

    def generate_waste_at_hour(
        self,
        bin_id: str,
        simulation_hour: int,
        current_fill_pct: float,
        temperature: float = 28.0,
        rainfall: float = 0.0,
        is_holiday: bool = False,
        event_multiplier: float = 1.0
    ) -> float:
        """
        Calculate waste generated in one hour for a bin
        Returns: new fill percentage
        """
        bin_data = self.generator.get_bin(bin_id)
        if not bin_data:
            return current_fill_pct

        # Base fill rate
        base_rate = bin_data["base_fill_rate"]

        # Hour multiplier (peak vs off-peak)
        hour = simulation_hour % 24
        if hour in bin_data["peak_hours"]:
            hour_multiplier = 1.8
        else:
            hour_multiplier = 0.6

        # Day multiplier (weekday vs weekend vs holiday)
        day_multiplier = bin_data["holiday_boost"] if is_holiday else 1.1

        # Temperature effect (warmer = more waste)
        temp_effect = 1.0 + max(0, (temperature - 28) * 0.02)

        # Rainfall effect (reduces waste generation outdoors)
        rain_effect = 1.0 - min(0.4, rainfall * 0.05)

        # Noise/variability
        noise = random.gauss(1.0, 0.15)

        # Combined fill rate
        fill_rate = (
            base_rate
            * hour_multiplier
            * day_multiplier
            * temp_effect
            * rain_effect
            * event_multiplier
            * noise
        )

        # Convert to percentage increase
        capacity = bin_data["capacity_liters"]
        fill_increase = (fill_rate * capacity / 100.0) / capacity * 100

        # New fill
        new_fill = min(100.0, current_fill_pct + fill_increase)

        return new_fill

    def simulate_collection(self, bin_id: str) -> float:
        """Simulate collection event - reset fill to 2-10%"""
        self.collection_history[bin_id] = datetime.utcnow()
        return random.uniform(2, 10)


# =============================================================================
# Weather Simulator
# =============================================================================

class WeatherSimulator:
    """Simulate Aurangabad weather patterns"""

    def __init__(self, seed: int = 42):
        random.seed(seed)

    def get_temperature(self, day_of_year: int) -> float:
        """
        Simulate temperature based on day of year
        Aurangabad: Hot summers (Apr-May: 40°C), cool winters (Dec-Jan: 15°C)
        """
        # Sinusoidal pattern
        base_temp = 28 + 12 * math.sin(math.pi * (day_of_year - 80) / 365)
        # Add daily variation
        daily_var = random.gauss(0, 2)
        return max(15, min(45, base_temp + daily_var))

    def get_rainfall(self, day_of_year: int, is_monsoon: bool = False) -> float:
        """
        Simulate rainfall
        Monsoon: Jun-Oct (heavy), rest: light
        """
        # Monsoon months (153-304 days in year)
        day_in_year = day_of_year % 365
        in_monsoon = 153 <= day_in_year <= 304

        if in_monsoon:
            # Monsoon: occasional heavy rain (80% probability of some rain)
            if random.random() < 0.3:
                return random.expovariate(1.0 / 8.0)  # Heavy: ~8mm avg
            else:
                return random.expovariate(1.0 / 0.5)  # Light: ~0.5mm
        else:
            # Non-monsoon: rare rain
            if random.random() < 0.05:
                return random.expovariate(1.0 / 2.0)
            else:
                return 0.0

    def is_holiday(self, date: datetime) -> bool:
        """Check if date is an Aurangabad holiday"""
        date_str = date.strftime("%Y-%m-%d")
        return date_str in AURANGABAD_HOLIDAYS


# =============================================================================
# City State Manager
# =============================================================================

class AurangabadCityState:
    """Manages complete state of Aurangabad city simulation"""

    def __init__(self, num_bins: int = 100, seed: int = 42):
        self.city_generator = AurangabadCityGenerator(seed=seed)
        self.bins = self.city_generator.generate_bins(num_bins)
        self.waste_simulator = WasteGenerationSimulator(self.city_generator, seed=seed)
        self.weather_simulator = WeatherSimulator(seed=seed)

        # Current state
        self.current_date = datetime(2024, 6, 1, 6, 0, 0)  # Start June 1, 2024 at 6 AM
        self.bin_states = {
            bin_data["id"]: {
                "fill_pct": random.uniform(20, 50),  # Initial fill
                "last_collection": self.current_date - timedelta(hours=random.randint(12, 72)),
                "hours_since_collection": random.uniform(12, 72),
            }
            for bin_data in self.bins
        }

        # Weather
        self.current_temperature = 28.0
        self.current_rainfall = 0.0

    def step_one_hour(self) -> Dict:
        """Advance simulation by one hour"""
        self.current_date += timedelta(hours=1)
        day_of_year = self.current_date.timetuple().tm_yday

        # Update weather
        self.current_temperature = self.weather_simulator.get_temperature(day_of_year)
        self.current_rainfall = self.weather_simulator.get_rainfall(day_of_year)
        is_holiday = self.weather_simulator.is_holiday(self.current_date)

        # Update each bin
        changes = {}
        for bin_data in self.bins:
            bin_id = bin_data["id"]
            current_state = self.bin_states[bin_id]

            # Generate waste
            new_fill = self.waste_simulator.generate_waste_at_hour(
                bin_id=bin_id,
                simulation_hour=self.current_date.hour,
                current_fill_pct=current_state["fill_pct"],
                temperature=self.current_temperature,
                rainfall=self.current_rainfall,
                is_holiday=is_holiday,
                event_multiplier=1.0  # Will be set by event engine
            )

            # Update hours since collection
            current_state["fill_pct"] = new_fill
            current_state["hours_since_collection"] += 1

            changes[bin_id] = {
                "fill_pct": round(new_fill, 2),
                "hours_since_collection": current_state["hours_since_collection"],
                "temperature": round(self.current_temperature, 1),
                "rainfall": round(self.current_rainfall, 2)
            }

        return {
            "timestamp": self.current_date.isoformat(),
            "temperature": round(self.current_temperature, 1),
            "rainfall": round(self.current_rainfall, 2),
            "is_holiday": is_holiday,
            "bins": changes
        }

    def get_state(self) -> Dict:
        """Get current city state"""
        return {
            "timestamp": self.current_date.isoformat(),
            "temperature": self.current_temperature,
            "rainfall": self.current_rainfall,
            "bins": self.bin_states,
            "num_bins": len(self.bins)
        }


if __name__ == "__main__":
    # Test the generator
    print("🏙️  Generating Aurangabad City...")
    city = AurangabadCityState(num_bins=100, seed=42)

    print(f"✅ Generated {len(city.bins)} bins")
    print(f"📍 Bin sample: {city.bins[0]}")

    # Simulate 24 hours
    print("\n⏰ Simulating 24 hours...")
    for hour in range(24):
        changes = city.step_one_hour()
        if hour % 6 == 0:
            print(f"Hour {hour}: Temp={changes['temperature']}°C, Rain={changes['rainfall']}mm")

    print(f"\n✅ Simulation complete at {city.current_date}")
