/**
 * Custom hooks for AI-WasteTwin
 */
import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux';
import { useEffect, useState, useCallback } from 'react';
import type { RootState, AppDispatch } from '../store';
import { wasteTwinApi, useWebSocket } from '../api/client';
import {
  setBins,
  setTrucks,
  setEvents,
  setRunning,
  setSpeed,
  setTick,
  setSimulationTime,
  updateMetrics,
} from '../store';

// Typed hooks
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

// Simulation controls
export function useSimulation() {
  const dispatch = useAppDispatch();
  const simulation = useAppSelector((state) => state.simulation);

  const startSimulation = useCallback(async () => {
    try {
      await wasteTwinApi.simulateStart();
      dispatch(setRunning(true));
    } catch (e) {
      console.error('Failed to start simulation:', e);
    }
  }, [dispatch]);

  const stopSimulation = useCallback(async () => {
    try {
      await wasteTwinApi.simulateStop();
      dispatch(setRunning(false));
    } catch (e) {
      console.error('Failed to stop simulation:', e);
    }
  }, [dispatch]);

  const setSimulationSpeed = useCallback(async (speed: number) => {
    try {
      await wasteTwinApi.simulateSpeed(speed);
      dispatch(setSpeed(speed));
    } catch (e) {
      console.error('Failed to set speed:', e);
    }
  }, [dispatch]);

  return {
    ...simulation,
    startSimulation,
    stopSimulation,
    setSimulationSpeed,
  };
}

// Bins data
export function useBins() {
  const bins = useAppSelector((state) => state.bins);
  const dispatch = useAppDispatch();
  const [loading, setLoading] = useState(true);

  const fetchBins = useCallback(async () => {
    try {
      const response = await wasteTwinApi.getBins();
      dispatch(setBins(response.data.bins || {}));
    } catch (e) {
      console.error('Failed to fetch bins:', e);
    } finally {
      setLoading(false);
    }
  }, [dispatch]);

  useEffect(() => {
    fetchBins();
  }, [fetchBins]);

  return { bins, loading, refetch: fetchBins };
}

// Trucks data
export function useTrucks() {
  const trucks = useAppSelector((state) => state.trucks);
  const dispatch = useAppDispatch();
  const [loading, setLoading] = useState(true);

  const fetchTrucks = useCallback(async () => {
    try {
      const response = await wasteTwinApi.getTrucks();
      dispatch(setTrucks(response.data.trucks || {}));
    } catch (e) {
      console.error('Failed to fetch trucks:', e);
    } finally {
      setLoading(false);
    }
  }, [dispatch]);

  useEffect(() => {
    fetchTrucks();
  }, [fetchTrucks]);

  return { trucks, loading, refetch: fetchTrucks };
}

// Events
export function useEvents() {
  const events = useAppSelector((state) => state.events);
  const dispatch = useAppDispatch();

  const injectEvent = useCallback(async (type: string, params?: Record<string, unknown>) => {
    try {
      const response = await wasteTwinApi.injectEvent(type, params);
      dispatch(setEvents(response.data.active_events || []));
    } catch (e) {
      console.error('Failed to inject event:', e);
    }
  }, [dispatch]);

  return { events, injectEvent };
}

// Live updates via WebSocket
export function useLiveUpdates() {
  const dispatch = useAppDispatch();

  const handleMessage = useCallback((data: any) => {
    if (data.type === 'bin_update') {
      dispatch(setBins(data.bins));
    } else if (data.type === 'simulation_state') {
      dispatch(setRunning(data.running));
      dispatch(setSpeed(data.speed));
      dispatch(setTick(data.tick));
      dispatch(setSimulationTime(data.timestamp));
    } else if (data.type === 'metrics_update') {
      dispatch(updateMetrics(data.metrics));
    }
  }, [dispatch]);

  const { connect, disconnect } = useWebSocket();

  useEffect(() => {
    connect(handleMessage);
    return () => disconnect();
  }, [connect, disconnect, handleMessage]);
}

// Computed stats
export function useBinStats() {
  const bins = useAppSelector((state) => state.bins);
  const binValues = Object.values(bins);

  const stats = {
    total: binValues.length,
    critical: binValues.filter((b) => b.current_fill_pct >= 80).length,
    highPriority: binValues.filter((b) => (b.priority_score || 0) >= 70).length,
    anomalies: binValues.filter((b) => b.is_anomalous).length,
    avgFill: binValues.length > 0
      ? binValues.reduce((sum, b) => sum + b.current_fill_pct, 0) / binValues.length
      : 0,
    toCollect: binValues.filter((b) => b.decision === 'COLLECT').length,
    waiting: binValues.filter((b) => b.decision === 'WAIT').length,
  };

  return stats;
}

export function useTruckStats() {
  const trucks = useAppSelector((state) => state.trucks);
  const truckValues = Object.values(trucks);

  const stats = {
    total: truckValues.length,
    active: truckValues.filter((t) => t.status === 'enroute').length,
    idle: truckValues.filter((t) => t.status === 'idle').length,
    broken: truckValues.filter((t) => t.status === 'breakdown').length,
    avgUtilization: truckValues.length > 0
      ? truckValues.reduce((sum, t) => sum + t.utilization_pct, 0) / truckValues.length
      : 0,
    totalLoad: truckValues.reduce((sum, t) => sum + t.current_load_liters, 0),
  };

  return stats;
}

// Map helpers
export function useMapMarkers() {
  const bins = useAppSelector((state) => state.bins);
  const trucks = useAppSelector((state) => state.trucks);

  const binMarkers = Object.values(bins).map((bin) => ({
    id: bin.id,
    position: [bin.latitude, bin.longitude] as [number, number],
    fill: bin.current_fill_pct,
    priority: bin.priority_score || 0,
    decision: bin.decision,
    isAnomaly: bin.is_anomalous || false,
  }));

  const truckMarkers = Object.values(trucks).map((truck) => ({
    id: truck.id,
    position: [truck.latitude, truck.longitude] as [number, number],
    status: truck.status,
    route: truck.route,
  }));

  return { binMarkers, truckMarkers };
}