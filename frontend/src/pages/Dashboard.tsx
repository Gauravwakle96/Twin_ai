/**
 * Dashboard Page - Main KPI overview
 */
import React, { useEffect, useState } from 'react';
import { Box, Grid, Card, CardContent, Typography, Chip, Button } from '@mui/material';
import {
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Speed as SpeedIcon,
  Warning as WarningIcon,
  LocalShipping as TruckIcon,
} from '@mui/icons-material';
import { useSimulation, useBinStats, useTruckStats, useEvents } from '../hooks/useApp';
import { useAppSelector } from '../store';

const StatCard: React.FC<{
  title: string;
  value: string | number;
  subtitle?: string;
  color?: string;
  icon?: React.ReactNode;
}> = ({ title, value, subtitle, color = 'primary.main', icon }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Box display="flex" justifyContent="space-between" alignItems="flex-start">
        <Box>
          <Typography color="textSecondary" variant="body2" gutterBottom>
            {title}
          </Typography>
          <Typography variant="h4" sx={{ color, fontWeight: 'bold' }}>
            {value}
          </Typography>
          {subtitle && (
            <Typography variant="caption" color="textSecondary">
              {subtitle}
            </Typography>
          )}
        </Box>
        {icon && <Box sx={{ color }}>{icon}</Box>}
      </Box>
    </CardContent>
  </Card>
);

const Dashboard: React.FC = () => {
  const { running, speed, tick, simulation_time, startSimulation, stopSimulation, setSimulationSpeed } = useSimulation();
  const binStats = useBinStats();
  const truckStats = useTruckStats();
  const { events } = useEvents();
  const metrics = useAppSelector((state) => state.metrics);

  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const formatTime = (iso: string) => {
    if (!iso) return '--:--:--';
    try {
      const date = new Date(iso);
      return date.toLocaleString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        day: 'numeric',
        month: 'short',
      });
    } catch {
      return iso;
    }
  };

  if (!mounted) return null;

  return (
    <Box p={3}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" fontWeight="bold">
            Dashboard
          </Typography>
          <Typography variant="body2" color="textSecondary">
            AI-WasteTwin Digital Twin Control Center
          </Typography>
        </Box>
        <Box display="flex" gap={1}>
          <Chip
            icon={running ? <PauseIcon /> : <PlayIcon />}
            label={running ? 'Running' : 'Paused'}
            color={running ? 'success' : 'default'}
          />
          <Chip label={`Tick: ${tick}`} variant="outlined" />
        </Box>
      </Box>

      {/* Simulation Controls */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2}>
            <Box display="flex" gap={1} alignItems="center">
              <Button
                variant="contained"
                color={running ? 'error' : 'success'}
                startIcon={running ? <PauseIcon /> : <PlayIcon />}
                onClick={running ? stopSimulation : startSimulation}
              >
                {running ? 'Pause' : 'Start'}
              </Button>
              <Button variant="outlined" startIcon={<RefreshIcon />}>
                Reset
              </Button>
            </Box>

            <Box display="flex" alignItems="center" gap={1}>
              <SpeedIcon color="action" />
              <Typography variant="body2">Speed:</Typography>
              <Button
                size="small"
                variant={speed === 1 ? 'contained' : 'outlined'}
                onClick={() => setSimulationSpeed(1)}
              >
                1x
              </Button>
              <Button
                size="small"
                variant={speed === 10 ? 'contained' : 'outlined'}
                onClick={() => setSimulationSpeed(10)}
              >
                10x
              </Button>
              <Button
                size="small"
                variant={speed === 60 ? 'contained' : 'outlined'}
                onClick={() => setSimulationSpeed(60)}
              >
                60x
              </Button>
            </Box>

            <Typography variant="body2" color="textSecondary">
              Simulation Time: {formatTime(simulation_time)}
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* KPI Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Bins"
            value={binStats.total}
            subtitle={`${binStats.critical} critical (≥80%)`}
            color="#1976d2"
            icon={<TruckIcon fontSize="large" />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="High Priority"
            value={binStats.highPriority}
            subtitle="Score ≥70"
            color="#ff9800"
            icon={<WarningIcon fontSize="large" />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Trucks"
            value={`${truckStats.active}/${truckStats.total}`}
            subtitle={`${truckStats.avgUtilization.toFixed(1)}% avg utilization`}
            color="#4caf50"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Avg Fill Level"
            value={`${binStats.avgFill.toFixed(1)}%`}
            subtitle={`${binStats.anomalies} anomalies detected`}
            color="#9c27b0"
          />
        </Grid>
      </Grid>

      {/* Decision Summary */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Collection Decisions
              </Typography>
              <Box display="flex" gap={2} mb={2}>
                <Chip label={`COLLECT: ${binStats.toCollect}`} color="error" />
                <Chip label={`WAIT: ${binStats.waiting}`} color="warning" />
              </Box>
              <Typography variant="body2" color="textSecondary">
                Based on priority scoring and truck availability
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Environmental Impact
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={4}>
                  <Typography variant="body2" color="textSecondary">Distance</Typography>
                  <Typography variant="h6">{metrics.total_distance_km.toFixed(1)} km</Typography>
                </Grid>
                <Grid item xs={4}>
                  <Typography variant="body2" color="textSecondary">Fuel</Typography>
                  <Typography variant="h6">{metrics.total_fuel_liters.toFixed(1)} L</Typography>
                </Grid>
                <Grid item xs={4}>
                  <Typography variant="body2" color="textSecondary">CO2</Typography>
                  <Typography variant="h6">{metrics.total_co2_kg.toFixed(1)} kg</Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Active Events */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Active Events
              </Typography>
              {events.length === 0 ? (
                <Typography variant="body2" color="textSecondary">
                  No active events. City operating normally.
                </Typography>
              ) : (
                <Box display="flex" gap={1} flexWrap="wrap">
                  {events.map((event) => (
                    <Chip
                      key={event.id}
                      label={`${event.type.replace('_', ' ').toUpperCase()} in ${event.zone}`}
                      color={
                        event.type === 'festival' ? 'info' :
                        event.type === 'heavy_rain' ? 'primary' :
                        event.type === 'road_closure' ? 'warning' : 'error'
                      }
                      onDelete={() => {}}
                    />
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
