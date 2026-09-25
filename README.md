# AI-WasteTwin: Aurangabad Smart Waste Management Digital Twin

An AI-driven, software-based digital twin for urban waste management in Aurangabad (Chhatrapati Sambhajinagar). Predicts waste accumulation, detects overflow risk, scores bin priority, allocates vehicles dynamically, optimizes routes, and adapts to disruptions (festivals, rain, road closures, truck breakdowns).

## Features

- **Digital Twin Simulation** – Real-time city model with 100+ virtual bins across Aurangabad
- **AI Prediction** – XGBoost forecasts bin fill-levels 1h/2h/4h ahead with overflow probability
- **Continuous Priority Scoring** – Sigmoid-based 0-100 priority with multi-factor weighting
- **Event Engine** – Festival, heavy rain, road closure, truck breakdown injection + auto-replanning
- **Multi-Destination Routing** – General waste → landfill, Organic → compost → farms, Recyclable → centers, E-waste → facility
- **OR-Tools CVRP** – Capacitated vehicle routing optimization with road multipliers
- **What-If Sandbox** – Test scenarios, see impact on metrics
- **Interactive Map** – Leaflet-based visualization with real Aurangabad locations
- **Real-Time WebSocket** – Live bin/truck/route updates

## Project Structure

```
AI-WasteTwin/
├── backend/
│   ├── api/                 # FastAPI routers
│   ├── digital_twin/        # State model & simulator
│   ├── ml/                  # Prediction pipeline
│   ├── optimization/        # OR-Tools routing
│   ├── services/            # Business logic
│   ├── config/              # Configuration
│   ├── main.py              # FastAPI app
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── pages/           # Dashboard, Map, AI Insights, Fleet, Simulation
│   │   ├── components/      # Reusable UI
│   │   ├── api/             # API client
│   │   ├── hooks/           # Custom hooks
│   │   ├── store/           # Redux slices
│   │   └── App.tsx          # Main app
│   ├── package.json
│   └── tsconfig.json
├── database/
│   └── models.py            # SQLAlchemy ORM
├── .env.example
├── docker-compose.yml
└── README.md
```

## Tech Stack

**Backend:** FastAPI, SQLAlchemy, XGBoost, Google OR-Tools, Uvicorn  
**Frontend:** React 18, TypeScript, Leaflet, Recharts, MUI, Redux Toolkit  
**Database:** SQLite (dev) / PostgreSQL (prod)  
**ML:** scikit-learn, pandas, numpy  

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py
```

Runs on `http://localhost:8000` with API docs at `/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:5173`

## How It Works

1. **Simulation Clock** – Advances hourly (or faster with speed multiplier)
2. **Waste Generation** – Based on area type (market, residential, hospital, etc.)
3. **ML Prediction** – XGBoost predicts fill 1h/2h/4h ahead
4. **Priority Scoring** – Sigmoid curve: fill + time-to-overflow + criticality + anomaly
5. **Decision Engine** – Collect/Wait/Reassign logic
6. **Vehicle Allocation** – Greedy assignment by proximity & capacity
7. **Route Optimization** – OR-Tools CVRP solver
8. **Event Injection** – Festival/rain/closure/breakdown mutates state
9. **Auto-Replanning** – Loop repeats; routes update in real-time

## Real Data: Aurangabad

100 bins placed across:
- Markets (Paithan Road, Station Road)
- Residential zones (CIDCO, Ashok Nagar)
- Landmarks (Railway Station, Bus Stand, Bibi Ka Maqbara)
- Hospitals (Civil Hospital, Apex Hospital)
- Schools and colleges
- Parks and public spaces

Waste generation tuned by Aurangabad weather:
- Monsoon (Jun-Oct): +rainfall effect, travel time multiplier
- Peak hours: 8-10am, 12-2pm, 5-7pm
- Festivals: Eid, Diwali, Holi, Marathwada Diwas boost waste +50%

## Evaluation

Compare **Fixed Schedule** (static routes) vs **AI Digital Twin** (dynamic, event-aware):
- Distance (km)
- Fuel & CO₂
- Overflow events
- Truck utilization
- Service-level (% collected before overflow)

## Demo Flow for Judges

1. Show live simulation running on map
2. Click a bin → see priority breakdown (why it's critical?)
3. Inject a Festival event → watch waste spike, routes recompute
4. Inject Road Closure → routes reroute around it
5. Show What-If: "How much worse if 2 trucks break down?"
6. Display evaluation: AI vs Fixed Schedule metrics over 30 days

## Authors

Developed as a college innovation project for smart urban waste management.

## License

MIT
