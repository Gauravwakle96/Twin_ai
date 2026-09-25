"""
AI-WasteTwin Backend - FastAPI Server
Digital Twin for Aurangabad Smart Waste Management
"""

import asyncio
from datetime import datetime
import json
import logging
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.digital_twin.simulator import get_simulation_engine
from backend.services.event_service import get_event_engine, get_event_injector
from backend.services.orchestrator import SimulationOrchestrator
from backend.services.prediction_service import get_prediction_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI-WasteTwin Backend",
    description="Digital Twin for Aurangabad Smart Waste Management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AppState:
    def __init__(self):
        self.simulation_running = False
        self.simulation_speed = 1.0
        self.current_tick = 0
        self.ws_connections: List[WebSocket] = []
        self.engine = get_simulation_engine()
        self.state = self.engine.initialize()
        self.orchestrator = SimulationOrchestrator()
        self.event_engine = get_event_engine()
        self.event_injector = get_event_injector()
        self.loop_task: Optional[asyncio.Task] = None

    async def broadcast(self, message: dict):
        """Broadcast WebSocket message to all connected clients"""
        disconnected = []
        for ws in self.ws_connections:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket send error: {e}")
                disconnected.append(ws)
        for ws in disconnected:
            if ws in self.ws_connections:
                self.ws_connections.remove(ws)

    def serialize_state(self) -> dict:
        """Helper to serialize state for responses and broadcasts"""
        bins_data = {}
        for b_id, b in self.state.bins.items():
            bins_data[b_id] = {
                "id": b.id,
                "latitude": b.latitude,
                "longitude": b.longitude,
                "area_type": b.area_type,
                "waste_type": b.waste_type,
                "capacity_liters": b.capacity_liters,
                "current_fill_pct": b.current_fill_pct,
                "criticality": b.criticality,
                "status": b.status,
                "last_collection": b.last_collection.isoformat() if b.last_collection else None,
                "prediction": {"1h": b.predicted_fill_1h, "2h": b.predicted_fill_2h, "4h": b.predicted_fill_4h},
                "overflow_probability": b.overflow_probability,
                "time_to_overflow_hours": b.time_to_overflow_hours,
                "priority_score": b.priority_score,
                "decision": b.decision,
                "is_anomalous": b.is_anomalous,
                "anomaly_reason": b.anomaly_reason,
            }

        trucks_data = {}
        for t_id, t in self.state.trucks.items():
            trucks_data[t_id] = {
                "id": t.id,
                "latitude": t.latitude,
                "longitude": t.longitude,
                "capacity_liters": t.capacity_liters,
                "current_load_liters": t.current_load_liters,
                "status": t.status,
                "assigned_bins": t.assigned_bins,
                "route": t.route,
                "driver_name": t.driver_name,
                "utilization_pct": t.utilization_pct,
            }

        events_data = {}
        for e_id, e in self.state.events.items():
            if e.is_active:
                events_data[e_id] = {
                    "id": e.id,
                    "type": e.type,
                    "zone": e.zone,
                    "start_time": e.start_time.isoformat(),
                    "end_time": e.end_time.isoformat() if e.end_time else None,
                    "intensity": e.intensity,
                    "params": e.params,
                    "is_active": e.is_active,
                }

        return {
            "simulation": {
                "running": self.simulation_running,
                "speed": self.simulation_speed,
                "tick": self.state.simulation_tick,
                "simulation_time": self.state.simulation_time.isoformat(),
            },
            "bins": bins_data,
            "trucks": trucks_data,
            "events": events_data,
        }


app_state = AppState()


async def simulation_worker():
    """Background task to advance the simulation clock and orchestrate AI steps"""
    while True:
        try:
            if app_state.simulation_running:
                # 1. Simulator step
                await app_state.engine.step()

                # 2. Event processing
                app_state.event_engine.cleanup_expired_events(app_state.state)
                app_state.event_engine.apply_all_active_events(app_state.state)

                # 3. AI Loop
                app_state.orchestrator.run_full_loop(app_state.state)

                # 4. Broadcast updated state
                state_data = app_state.serialize_state()
                await app_state.broadcast({
                    "type": "state_update",
                    "data": state_data
                })

            # Calculate sleep interval based on simulation speed (base: 1 second per tick)
            sleep_time = max(0.05, 1.0 / app_state.simulation_speed)
            await asyncio.sleep(sleep_time)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in simulation loop: {e}")
            await asyncio.sleep(1)


@app.on_event("startup")
async def startup_event():
    # Initial AI loop so state is fully scored and populated
    app_state.orchestrator.run_full_loop(app_state.state)
    app_state.loop_task = asyncio.create_task(simulation_worker())


@app.on_event("shutdown")
async def shutdown_event():
    if app_state.loop_task:
        app_state.loop_task.cancel()


# ============================================================================
# Health Check
# ============================================================================

@app.get("/api/health")
async def health_check():
    """System health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "simulation": {
            "running": app_state.simulation_running,
            "speed": app_state.simulation_speed,
            "tick": app_state.state.simulation_tick
        }
    }


# ============================================================================
# Simulation Control
# ============================================================================

@app.post("/api/simulate/start")
async def start_simulation():
    """Start the simulation clock"""
    app_state.simulation_running = True
    logger.info("Simulation started")

    await app_state.broadcast({
        "type": "simulation_started",
        "timestamp": datetime.utcnow().isoformat()
    })

    return {"status": "started"}


@app.post("/api/simulate/stop")
async def stop_simulation():
    """Stop the simulation clock"""
    app_state.simulation_running = False
    logger.info("Simulation stopped")

    await app_state.broadcast({
        "type": "simulation_stopped",
        "timestamp": datetime.utcnow().isoformat()
    })

    return {"status": "stopped"}


@app.post("/api/simulate/speed")
async def set_simulation_speed(speed: float):
    """Set simulation speed multiplier (1x to 60x)"""
    if speed < 0.1 or speed > 60:
        raise HTTPException(status_code=400, detail="Speed must be between 0.1 and 60")

    app_state.simulation_speed = speed
    logger.info(f"Simulation speed set to {speed}x")

    await app_state.broadcast({
        "type": "speed_changed",
        "speed": speed,
        "timestamp": datetime.utcnow().isoformat()
    })

    return {"speed": speed}


@app.get("/api/simulate/status")
async def get_simulation_status():
    """Get current simulation status"""
    return {
        "running": app_state.simulation_running,
        "speed": app_state.simulation_speed,
        "tick": app_state.state.simulation_tick,
        "simulation_time": app_state.state.simulation_time.isoformat(),
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# State & Data Endpoints
# ============================================================================

@app.get("/api/bins")
async def get_bins():
    """Get all bins"""
    bins_data = []
    for b in app_state.state.bins.values():
        bins_data.append({
            "id": b.id,
            "latitude": b.latitude,
            "longitude": b.longitude,
            "area_type": b.area_type,
            "waste_type": b.waste_type,
            "capacity_liters": b.capacity_liters,
            "current_fill_pct": b.current_fill_pct,
            "criticality": b.criticality,
            "status": b.status,
            "last_collection": b.last_collection.isoformat() if b.last_collection else None,
            "prediction": {"1h": b.predicted_fill_1h, "2h": b.predicted_fill_2h, "4h": b.predicted_fill_4h},
            "overflow_probability": b.overflow_probability,
            "time_to_overflow_hours": b.time_to_overflow_hours,
            "priority_score": b.priority_score,
            "decision": b.decision,
            "is_anomalous": b.is_anomalous,
            "anomaly_reason": b.anomaly_reason,
        })
    return {
        "total": len(bins_data),
        "bins": bins_data,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/bins/{bin_id}")
async def get_bin(bin_id: str):
    """Get single bin details"""
    if bin_id not in app_state.state.bins:
        raise HTTPException(status_code=404, detail="Bin not found")
    b = app_state.state.bins[bin_id]
    return {
        "id": b.id,
        "latitude": b.latitude,
        "longitude": b.longitude,
        "area_type": b.area_type,
        "waste_type": b.waste_type,
        "capacity_liters": b.capacity_liters,
        "current_fill_pct": b.current_fill_pct,
        "criticality": b.criticality,
        "status": b.status,
        "last_collection": b.last_collection.isoformat() if b.last_collection else None,
        "prediction": {"1h": b.predicted_fill_1h, "2h": b.predicted_fill_2h, "4h": b.predicted_fill_4h},
        "overflow_probability": b.overflow_probability,
        "time_to_overflow_hours": b.time_to_overflow_hours,
        "priority_score": b.priority_score,
        "decision": b.decision,
        "is_anomalous": b.is_anomalous,
        "anomaly_reason": b.anomaly_reason,
    }


@app.get("/api/trucks")
async def get_trucks():
    """Get all trucks"""
    trucks_data = []
    for t in app_state.state.trucks.values():
        trucks_data.append({
            "id": t.id,
            "latitude": t.latitude,
            "longitude": t.longitude,
            "capacity_liters": t.capacity_liters,
            "current_load_liters": t.current_load_liters,
            "status": t.status,
            "assigned_bins": t.assigned_bins,
            "route": t.route,
            "driver_name": t.driver_name,
            "utilization_pct": t.utilization_pct,
        })
    return {
        "total": len(trucks_data),
        "trucks": trucks_data,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/predict")
async def predict():
    """Run ML predictions manually"""
    pred_service = get_prediction_service()
    predictions = pred_service.predict_all_bins(app_state.state, horizons=[1, 2, 4])
    critical_bins = len([b for b in app_state.state.bins.values() if b.current_fill_pct > 80])
    return {
        "predictions_generated": len(predictions),
        "critical_bins": critical_bins,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/optimize")
async def optimize_routes():
    """Run priority and routing optimization"""
    results = app_state.orchestrator.run_full_loop(app_state.state)
    return {
        "status": "success",
        "results": results,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/events/active")
async def get_active_events():
    """Get all active events"""
    events = [
        {
            "id": e.id,
            "type": e.type,
            "zone": e.zone,
            "start_time": e.start_time.isoformat(),
            "end_time": e.end_time.isoformat() if e.end_time else None,
            "intensity": e.intensity,
            "params": e.params,
            "is_active": e.is_active,
        }
        for e in app_state.state.get_active_events()
    ]
    return {
        "total": len(events),
        "events": events,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/events/inject")
async def inject_event(type: str, zone: Optional[str] = None, duration_hours: Optional[int] = 12, intensity: Optional[float] = 1.5, truck_id: Optional[str] = None):
    """Inject an event into the simulation"""
    valid_types = ["festival", "heavy_rain", "road_closure", "truck_breakdown"]

    if type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid event type. Must be one of {valid_types}")

    event = None
    if type == "festival":
        event = app_state.event_injector.inject_festival(
            app_state.state,
            zone=zone or "Market_Area",
            duration_hours=duration_hours or 12,
            intensity=intensity or 1.5
        )
    elif type == "heavy_rain":
        event = app_state.event_injector.inject_heavy_rain(
            app_state.state,
            duration_hours=duration_hours or 6,
            intensity=intensity or 1.3
        )
    elif type == "road_closure":
        event = app_state.event_injector.inject_road_closure(
            app_state.state,
            zone=zone or "Paithan_Road",
            duration_hours=duration_hours or 4
        )
    elif type == "truck_breakdown":
        event = app_state.event_injector.inject_truck_breakdown(
            app_state.state,
            truck_id=truck_id,
            duration_hours=duration_hours or 3
        )

    # Re-run loop to apply effects immediately
    app_state.event_engine.apply_all_active_events(app_state.state)
    app_state.orchestrator.run_full_loop(app_state.state)

    logger.info(f"Event injected: {type}")

    await app_state.broadcast({
        "type": "event_injected",
        "event_type": type,
        "event_id": event.id if event else None,
        "timestamp": datetime.utcnow().isoformat()
    })

    return {
        "status": "injected",
        "event_type": type,
        "event_id": event.id if event else None
    }


# ============================================================================
# WebSocket Live Feed
# ============================================================================

@app.websocket("/ws")
@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time digital twin updates"""
    await websocket.accept()
    app_state.ws_connections.append(websocket)
    logger.info("WebSocket client connected")

    try:
        # Send initial state snapshot on connect
        await websocket.send_json({
            "type": "initial_state",
            "data": app_state.serialize_state()
        })

        while True:
            data = await websocket.receive_text()
            logger.debug(f"WebSocket message received: {data}")
    except Exception as e:
        logger.info(f"WebSocket client disconnected: {e}")
    finally:
        if websocket in app_state.ws_connections:
            app_state.ws_connections.remove(websocket)


# ============================================================================
# Root
# ============================================================================

@app.get("/")
async def root():
    """API root"""
    return {
        "name": "AI-WasteTwin Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
