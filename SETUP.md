# AI-WasteTwin: Setup Instructions

## Installation

### Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Required packages:
- fastapi
- uvicorn
- sqlalchemy
- pydantic-settings
- pandas
- numpy
- scikit-learn
- xgboost
- ortools
- joblib

### Frontend Dependencies

```bash
cd frontend
npm install
```

## Running the System

### Backend
```bash
cd backend
python main.py
# Server runs on http://localhost:8000
```

### Frontend
```bash
cd frontend
npm run dev
# UI runs on http://localhost:5173
```

## Testing

```bash
# Test Digital Twin + ML integration
python test_integration.py
```

## Current Status

✅ **Completed (Tasks 1-3):**
- Project structure
- Database models (14 tables)
- Digital Twin state model
- Aurangabad city generator (100 bins, 13 zones)
- Waste generation simulator
- Weather simulator
- Simulation engine
- ML prediction pipeline (XGBoost)
- Feature engineering
- Prediction service

📋 **Next (Tasks 4-8):**
- Priority scoring engine
- Vehicle allocation
- OR-Tools routing
- Event engine
- React UI pages
- What-If scenarios

## Quick Start (After Installing Dependencies)

1. Install backend deps: `cd backend && pip install -r requirements.txt`
2. Run backend: `python main.py`
3. Install frontend deps: `cd frontend && npm install`
4. Run frontend: `npm run dev`
5. Open browser: `http://localhost:5173`

The simulation will auto-initialize with 100 Aurangabad bins.
