/**
 * Dashboard Page — Premium Command Center
 */
import React, { useEffect, useState } from 'react';
import { Box, Grid, Card, CardContent, Typography, Button, Chip } from '@mui/material';
import {
  Trash2 as BinIcon,
  AlertTriangle as WarningIcon,
  TrendingUp as TrendIcon,
  Truck as TruckIcon,
  Activity as LiveIcon,
  AlertCircle as AlertIcon,
} from 'lucide-react';
import { useSimulation, useBinStats, useTruckStats, useEvents } from '../hooks/useApp';
import { useAppSelector } from '../store';
import KpiCard from '../components/KpiCard';
import { fmtNum } from '../design/tokens';

const Dashboard: React.FC = () => {
  const { running, speed, tick, simulation_time, startSimulation, stopSimulation, setSimulationSpeed } = useSimulation();
  const binStats = useBinStats();
  const truckStats = useTruckStats();
  const { events } = useEvents();
  const bins = useAppSelector((state) => state.bins);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const formatTime = (iso: string) => {
    if (!iso) return '--:--:--';
    try {
      const date = new Date(iso);
      return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return iso;
    }
  };

  if (!mounted) return null;

  // Calculate dynamic metrics
  const criticalBins = Object.values(bins).filter((b: any) => b.current_fill_pct >= 80).length;
  const highPriorityBins = Object.values(bins).filter((b: any) => (b.priority_score || 0) >= 70).length;
  const activeTrucks = Object.values(bins).filter((t: any) => t.status === 'enroute' || t.status === 'collecting').length;
  const avgFill = Object.values(bins).reduce((s: number, b: any) => s + b.current_fill_pct, 0) / (Object.values(bins).length || 1);
  const totalDistance = useAppSelector((state) => state.metrics.total_distance_km);
  const totalFuel = useAppSelector((state) => state.metrics.total_fuel_liters);
  const totalCO2 = useAppSelector((state) => state.metrics.total_co2_kg);

  return (
    <Box sx={{ p: 3, bgcolor: 'var(--bg)', minHeight: 'calc(100vh - 64px)' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, color: 'var(--text)', letterSpacing: '-0.02em' }}>
            Dashboard
          </Typography>
          <Typography variant="body2" sx={{ color: 'var(--text2)', mt: 0.5 }}>
            AI-WasteTwin Digital Twin Control Center · Aurangabad Smart City
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Chip
            icon={running ? <LiveIcon size={14} /> : undefined}
            label={running ? 'LIVE' : 'PAUSED'}
            color={running ? 'success' : 'default'}
            sx={{ fontWeight: 700 }}
          />
          <Typography variant="caption" sx={{ color: 'var(--text3)', fontVariantNumeric: 'tabular-nums' }}>
            Tick: {tick}
          </Typography>
        </Box>
      </Box>

      {/* Simulation Controls */}
      <Card sx={{ mb: 3, background: 'var(--surface)', border: '1px solid var(--border)' }}>
        <CardContent sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                color={running ? 'error' : 'success'}
                onClick={running ? stopSimulation : startSimulation}
                sx={{ fontWeight: 600 }}
              >
                {running ? 'Pause' : 'Start'}
              </Button>
              <Button
                variant="outlined"
                onClick={() => window.location.reload()}
                sx={{ color: 'var(--text2)', borderColor: 'var(--border2)' }}
              >
                Reset
              </Button>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" sx={{ color: 'var(--text3)' }}>Speed:</Typography>
              {[1, 10, 60].map((s) => (
                <Button
                  key={s}
                  size="small"
                  variant={speed === s ? 'contained' : 'outlined'}
                  onClick={() => setSimulationSpeed(s)}
                  sx={{ minWidth: 48, fontWeight: 600 }}
                >
                  {s}x
                </Button>
              ))}
            </Box>

            <Typography variant="body2" sx={{ color: 'var(--text2)', fontVariantNumeric: 'tabular-nums' }}>
              Time: {formatTime(simulation_time)}
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* KPI Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={4} md={2}>
          <KpiCard
            title="Total Bins"
            value={binStats.total}
            subtitle={`${criticalBins} critical`}
            icon={<BinIcon size={20} />}
            status={criticalBins > 0 ? 'warning' : 'normal'}
          />
        </Grid>
        <Grid item xs={6} sm={4} md={2}>
          <KpiCard
            title="Critical"
            value={criticalBins}
            subtitle="≥80% fill"
            icon={<WarningIcon size={20} />}
            status="critical"
          />
        </Grid>
        <Grid item xs={6} sm={4} md={2}>
          <KpiCard
            title="High Priority"
            value={highPriorityBins}
            subtitle="Score ≥70"
            icon={<AlertIcon size={20} />}
            status={highPriorityBins > 0 ? 'high' : 'normal'}
          />
        </Grid>
        <Grid item xs={6} sm={4} md={2}>
          <KpiCard
            title="Active Trucks"
            value={`${activeTrucks}/${truckStats.total}`}
            subtitle={`${truckStats.avgUtilization.toFixed(1)}% util`}
            icon={<TruckIcon size={20} />}
            status="info"
          />
        </Grid>
        <Grid item xs={6} sm={4} md={2}>
          <KpiCard
            title="Avg Fill"
            value={fmtNum(avgFill, 1)}
            unit="%"
            subtitle={`${binStats.anomalies} anomalies`}
            icon={<TrendIcon size={20} />}
            accent="#9c27b0"
          />
        </Grid>
        <Grid item xs={6} sm={4} md={2}>
          <KpiCard
            title="Events"
            value={events.length}
            subtitle="Active"
            icon={<LiveIcon size={20} />}
            status={events.length > 0 ? 'warning' : 'normal'}
          />
        </Grid>
      </Grid>

      {/* Main Content Grid */}
      <Grid container spacing={2}>
        {/* Collection Decisions */}
        <Grid item xs={12} md={6}>
          <Card sx={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>Collection Decisions</Typography>
              <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <Chip
                  label={`COLLECT: ${binStats.toCollect}`}
                  color="error"
                  sx={{ fontWeight: 700, fontSize: '1rem', px: 2, py: 1 }}
                />
                <Chip
                  label={`WAIT: ${binStats.waiting}`}
                  sx={{ fontWeight: 700, fontSize: '1rem', px: 2, py: 1, bgcolor: 'var(--surface2)', color: 'var(--text)' }}
                />
              </Box>
              <Typography variant="body2" sx={{ color: 'var(--text3)' }}>
                Based on AI priority scoring and truck availability
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Environmental Impact */}
        <Grid item xs={12} md={6}>
          <Card sx={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>Environmental Impact</Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 2 }}>
                <StatItem label="Distance" value={`${totalDistance.toFixed(1)} km`} />
                <StatItem label="Fuel" value={`${totalFuel.toFixed(1)} L`} />
                <StatItem label="CO₂" value={`${totalCO2.toFixed(1)} kg`} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Active Events */}
        <Grid item xs={12}>
          <Card sx={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>Active Events</Typography>
              {events.length === 0 ? (
                <Typography variant="body2" sx={{ color: 'var(--text3)' }}>
                  No active events. City operating normally.
                </Typography>
              ) : (
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {events.map((event: any) => (
                    <Chip
                      key={event.id}
                      label={`${event.type.replace(/_/g, ' ').toUpperCase()} — ${event.zone}`}
                      color={
                        event.type === 'festival' ? 'secondary' :
                        event.type === 'heavy_rain' ? 'primary' :
                        event.type === 'road_closure' ? 'warning' : 'error'
                      }
                      sx={{ fontWeight: 600 }}
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

const StatItem = ({ label, value }: { label: string; value: string }) => (
  <Box sx={{ textAlign: 'center', p: 1 }}>
    <Typography variant="caption" sx={{ color: 'var(--text3)', textTransform: 'uppercase', fontSize: '0.7rem' }}>
      {label}
    </Typography>
    <Typography variant="h6" sx={{ fontWeight: 700, color: 'var(--text)', fontVariantNumeric: 'tabular-nums' }}>
      {value}
    </Typography>
  </Box>
);

export default Dashboard;