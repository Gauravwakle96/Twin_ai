/**
 * AI-WasteTwin API Client
 */
import axios from 'axios';

// Vite injects import.meta.env at build time
const API_BASE = import.meta.env.VITE_API_URL ?? '/api';
const WS_BASE = import.meta.env.VITE_WS_URL ?? `${window.location.protocol.replace("http", "ws")}${window.location.host}/ws`;

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// API calls
export const wasteTwinApi = {
  // Health
  health: () => api.get('/health'),

  // Simulation
  simulateStart: () => api.post('/simulate/start'),
  simulateStop: () => api.post('/simulate/stop'),
  simulateSpeed: (speed: number) => api.post('/simulate/speed', null, { params: { speed } }),
  simulateStatus: () => api.get('/simulate/status'),

  // Bins
  getBins: () => api.get('/bins'),
  getBin: (id: string) => api.get(`/bins/${id}`),

  // Trucks
  getTrucks: () => api.get('/trucks'),

  // Predictions
  predict: () => api.post('/predict'),

  // Optimization
  optimize: () => api.post('/optimize'),

  // Events
  getEvents: () => api.get('/events/active'),
  injectEvent: (type: string, params?: Record<string, unknown>) =>
    api.post('/events/inject', null, { params: { type, ...params } }),
};

// Types
export interface Bin {
  id: string;
  latitude: number;
  longitude: number;
  area_type: string;
  waste_type: string;
  capacity_liters: number;
  current_fill_pct: number;
  criticality: string;
  status: string;
  last_collection: string | null;
  prediction?: {
    '1h': number;
    '2h': number;
    '4h': number;
  };
  overflow_probability?: number;
  time_to_overflow_hours?: number;
  priority_score?: number;
  decision?: string;
  is_anomalous?: boolean;
  anomaly_reason?: string;
}

export interface Truck {
  id: string;
  latitude: number;
  longitude: number;
  capacity_liters: number;
  current_load_liters: number;
  status: string;
  assigned_bins: string[];
  route: RouteStop[];
  driver_name: string;
  utilization_pct: number;
}

export interface RouteStop {
  type: string;
  lat?: number;
  lon?: number;
  bin_id?: string;
  load_liters?: number;
}

export interface SimulationState {
  running: boolean;
  speed: number;
  tick: number;
  simulation_time: string;
}

export interface Event {
  id: string;
  type: string;
  zone: string;
  start_time: string;
  end_time: string | null;
  intensity: number;
  params: Record<string, unknown>;
  is_active: boolean;
}

export interface Metrics {
  total_distance_km: number;
  total_fuel_liters: number;
  total_co2_kg: number;
  overflow_events: number;
}

export interface PriorityExplanation {
  fill_level: number;
  fill_score: number;
  time_to_overflow_hours: number | null;
  overflow_probability: number;
  criticality: string;
  is_anomalous: boolean;
  anomaly_boost: number;
  final_score: number;
}

// WebSocket hook
export function useWebSocket() {
  const wsRef = { current: null as WebSocket | null };

  const connect = (onMessage: (data: unknown) => void) => {
    wsRef.current = new WebSocket(WS_BASE);

    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
    };

    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        console.error('WS parse error:', e);
      }
    };

    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected');
    };
  };

  const disconnect = () => {
    wsRef.current?.close();
  };

  return { connect, disconnect };
}

export default api;