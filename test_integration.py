#!/usr/bin/env python3
"""
Integration test: Run full Digital Twin simulation with ML prediction
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    """Test the complete pipeline"""
    print("=" * 60)
    print("AI-WasteTwin Integration Test")
    print("=" * 60)

    try:
        # Import modules (within try to catch import errors)
        from backend.digital_twin.simulator import get_simulation_engine
        from backend.services.prediction_service import get_prediction_service

        print("\n[OK] Modules loaded successfully")

        # Step 1: Initialize simulation
        print("\n[Step 1] Initializing Digital Twin...")
        engine = get_simulation_engine()
        state = engine.initialize()

        print(f"   - Created {len(state.bins)} bins in Aurangabad")
        print(f"   - Created {len(state.trucks)} trucks")
        print(f"   - Created {len(state.facilities)} facilities")
        print(f"   - Simulation time: {state.simulation_time}")

        # Step 2: Load ML model
        print("\n[Step 2] Loading ML prediction model...")
        prediction_service = get_prediction_service()
        print(f"   - Model loaded: {prediction_service.is_loaded}")

        # Step 3: Run prediction for all bins
        print("\n[Step 3] Running ML predictions...")
        predictions = prediction_service.predict_all_bins(state, horizons=[1, 2, 4])

        # Show sample predictions
        sample_bins = list(predictions.keys())[:3]
        for bin_id in sample_bins:
            pred = predictions[bin_id]
            current = pred["current_fill"]
            pred_1h = pred["predictions"]["1h"]["predicted_fill"]
            pred_4h = pred["predictions"]["4h"]["predicted_fill"]
            overflow_prob = pred["predictions"]["4h"]["overflow_probability"]
            print(f"   - {bin_id}: {current}% -> +1h: {pred_1h}% -> +4h: {pred_4h}% (overflow risk: {overflow_prob:.0%})")

        # Step 4: Step simulation forward 3 hours
        print("\n[Step 4] Stepping simulation 3 hours...")
        for hour in range(3):
            state = await engine.step()
            print(f"   Hour {hour+1}: {state.simulation_time} - Temp: {state.bins['BIN001'].temperature} C")

        # Step 5: Run predictions again to see changes
        print("\n[Step 5] Running updated predictions...")
        updated_predictions = prediction_service.predict_all_bins(state, horizons=[1, 2, 4])

        for bin_id in sample_bins:
            pred = updated_predictions[bin_id]
            current = pred["current_fill"]
            overflow_prob = pred["predictions"]["4h"]["overflow_probability"]
            time_to_overflow = pred["predictions"]["4h"]["time_to_overflow_hours"]
            print(f"   - {bin_id}: {current}% | Risk: {overflow_prob:.0%} | Time to overflow: {time_to_overflow}h")

        # Step 6: Test event injection
        print("\n[Step 6] Testing event injection...")
        event = engine.inject_event("festival", {
            "zone": "Market_Area",
            "intensity": 1.5,
            "duration_hours": 12
        })
        print(f"   - Festival event injected: {event.zone}")

        print(f"\n[OK] Integration test complete!")
        print(f"   - Total bins: {len(state.bins)}")
        print(f"   - Critical bins (>80%): {len([b for b in state.bins.values() if b.current_fill_pct > 80])}")
        print(f"   - Simulation tick: {state.simulation_tick}")
        print(f"   - Active events: {len([e for e in state.events.values() if e.is_active])}")

    except Exception as e:
        print(f"\n[ERROR] Integration test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())