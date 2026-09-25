/**
 * Redux Toolkit Store for AI-WasteTwin
 */
import { configureStore, createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { Bin, Truck, SimulationState, Event, Metrics } from '../api/client';

// Initial state
interface AppState {
  bins: Record<string, Bin>;
  trucks: Record<string, Truck>;
  simulation: SimulationState;
  events: Event[];
  metrics: Metrics;
  selectedBin: string | null;
  selectedTruck: string | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: AppState = {
  bins: {},
  trucks: {},
  simulation: {
    running: false,
    speed: 1,
    tick: 0,
    simulation_time: new Date().toISOString(),
  },
  events: [],
  metrics: {
    total_distance_km: 0,
    total_fuel_liters: 0,
    total_co2_kg: 0,
    overflow_events: 0,
  },
  selectedBin: null,
  selectedTruck: null,
  isLoading: false,
  error: null,
};

// Slices
const simulationSlice = createSlice({
  name: 'simulation',
  initialState: initialState.simulation,
  reducers: {
    setRunning: (state, action: PayloadAction<boolean>) => {
      state.running = action.payload;
    },
    setSpeed: (state, action: PayloadAction<number>) => {
      state.speed = action.payload;
    },
    setTick: (state, action: PayloadAction<number>) => {
      state.tick = action.payload;
    },
    setSimulationTime: (state, action: PayloadAction<string>) => {
      state.simulation_time = action.payload;
    },
    updateSimulation: (state, action: PayloadAction<Partial<SimulationState>>) => {
      return { ...state, ...action.payload };
    },
  },
});

const binsSlice = createSlice({
  name: 'bins',
  initialState: initialState.bins,
  reducers: {
    setBins: (_state, action: PayloadAction<Record<string, Bin>>) => {
      return action.payload;
    },
    updateBin: (state, action: PayloadAction<{ id: string; updates: Partial<Bin> }>) => {
      const { id, updates } = action.payload;
      if (state[id]) {
        state[id] = { ...state[id], ...updates };
      }
    },
  },
});

const trucksSlice = createSlice({
  name: 'trucks',
  initialState: initialState.trucks,
  reducers: {
    setTrucks: (_state, action: PayloadAction<Record<string, Truck>>) => {
      return action.payload;
    },
    updateTruck: (state, action: PayloadAction<{ id: string; updates: Partial<Truck> }>) => {
      const { id, updates } = action.payload;
      if (state[id]) {
        state[id] = { ...state[id], ...updates };
      }
    },
  },
});

const eventsSlice = createSlice({
  name: 'events',
  initialState: initialState.events,
  reducers: {
    setEvents: (_state, action: PayloadAction<Event[]>) => {
      return action.payload;
    },
    addEvent: (state, action: PayloadAction<Event>) => {
      state.push(action.payload);
    },
    removeEvent: (state, action: PayloadAction<string>) => {
      return state.filter(e => e.id !== action.payload);
    },
  },
});

const metricsSlice = createSlice({
  name: 'metrics',
  initialState: initialState.metrics,
  reducers: {
    updateMetrics: (state, action: PayloadAction<Partial<Metrics>>) => {
      return { ...state, ...action.payload };
    },
    resetMetrics: () => initialState.metrics,
  },
});

const uiSlice = createSlice({
  name: 'ui',
  initialState: { selectedBin: null as string | null, selectedTruck: null as string | null, isLoading: false, error: null as string | null },
  reducers: {
    setSelectedBin: (state, action: PayloadAction<string | null>) => {
      state.selectedBin = action.payload;
    },
    setSelectedTruck: (state, action: PayloadAction<string | null>) => {
      state.selectedTruck = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
});

// Export actions
export const {
  setRunning,
  setSpeed,
  setTick,
  setSimulationTime,
  updateSimulation,
} = simulationSlice.actions;

export const {
  setBins,
  updateBin,
} = binsSlice.actions;

export const {
  setTrucks,
  updateTruck,
} = trucksSlice.actions;

export const {
  setEvents,
  addEvent,
  removeEvent,
} = eventsSlice.actions;

export const {
  updateMetrics,
  resetMetrics,
} = metricsSlice.actions;

export const {
  setSelectedBin,
  setSelectedTruck,
  setLoading,
  setError,
} = uiSlice.actions;

// Store
export const store = configureStore({
  reducer: {
    simulation: simulationSlice.reducer,
    bins: binsSlice.reducer,
    trucks: trucksSlice.reducer,
    events: eventsSlice.reducer,
    metrics: metricsSlice.reducer,
    ui: uiSlice.reducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Typed hooks
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

// Selectors
export const selectSimulation = (state: RootState) => state.simulation;
export const selectBins = (state: RootState) => state.bins;
export const selectTrucks = (state: RootState) => state.trucks;
export const selectEvents = (state: RootState) => state.events;
export const selectMetrics = (state: RootState) => state.metrics;
export const selectUI = (state: RootState) => state.ui;

// Computed selectors
export const selectCriticalBins = (state: RootState) =>
  Object.values(state.bins).filter(b => b.current_fill_pct >= 80);

export const selectHighPriorityBins = (state: RootState) =>
  Object.values(state.bins).filter(b => (b.priority_score || 0) >= 70);

export const selectActiveTrucks = (state: RootState) =>
  Object.values(state.trucks).filter(t => t.status !== 'breakdown');

export const selectBinsToCollect = (state: RootState) =>
  Object.values(state.bins).filter(b => b.decision === 'COLLECT');

export const selectUtilization = (state: RootState) => {
  const trucks = Object.values(state.trucks);
  if (trucks.length === 0) return 0;
  const total = trucks.reduce((sum, t) => sum + t.capacity_liters, 0);
  const used = trucks.reduce((sum, t) => sum + t.current_load_liters, 0);
  return (used / total) * 100;
};