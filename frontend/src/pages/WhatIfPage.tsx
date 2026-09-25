/**
 * What-If Page - Scenario Comparison
 */
import React, { useState } from 'react';
import { Box, Grid, Card, CardContent, Typography, Chip, Slider, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import {
  Science as ExperimentIcon,
  Compare as CompareIcon,
  TrendingUp as TrendIcon,
} from '@mui/icons-material';

interface ScenarioResult {
  label: string;
  total_distance_km: number;
  total_fuel_liters: number;
  total_co2_kg: number;
  overflow_events: number;
  bins_collected: number;
  efficiency: number;
}

const BASELINE: ScenarioResult = {
  label: 'Fixed Schedule',
  total_distance_km: 1250,
  total_fuel_liters: 185,
  total_co2_kg: 480,
  overflow_events: 45,
  bins_collected: 850,
  efficiency: 72,
};

const generateAIResult = (trucks: number, events: number): ScenarioResult => ({
  label: 'AI Dynamic',
  total_distance_km: Math.round(1250 * (1 - 0.22 - trucks * 0.01) + events * 2),
  total_fuel_liters: Math.round(185 * (1 - 0.25) + events * 1.5),
  total_co2_kg: Math.round(480 * (1 - 0.23) + events),
  overflow_events: Math.max(2, Math.round(45 * (1 - 0.7) - trucks * 1.5 + events * 2)),
  bins_collected: Math.round(850 * (1 + 0.15) - events * 3),
  efficiency: Math.min(98, Math.round(72 + 18 - trucks * 0.5 + events * 0.3)),
});

const WhatIfPage: React.FC = () => {
  const [truckCount, setTruckCount] = useState(8);
  const [eventCount, setEventCount] = useState(3);
  const [scenarioType, setScenarioType] = useState('standard');

  const aiResult = generateAIResult(truckCount, eventCount);

  const compare = (a: ScenarioResult, b: ScenarioResult, lowerIsBetter: boolean) => {
    const diff = a[b.label === 'Fixed Schedule' ? 'total_distance_km' : 'efficiency'] - b[b.label === 'Fixed Schedule' ? 'total_distance_km' : 'efficiency'];
    if (lowerIsBetter) return diff > 0 ? `${Math.abs(diff).toFixed(1)} worse` : `${Math.abs(diff).toFixed(1)} better`;
    return diff > 0 ? `${Math.abs(diff).toFixed(1)} worse` : `${Math.abs(diff).toFixed(1)} better`;
  };

  const scenarios = [
    { value: 'standard', label: 'Standard AI (8 trucks, 3 events)' },
    { value: 'reduced', label: 'Reduced Fleet (4 trucks)' },
    { value: 'peak', label: 'Peak Season (10 events)' },
    { value: 'breakdown', label: '2 Truck Breakdowns' },
  ];

  const getScenarioResult = () => {
    if (scenarioType === 'reduced') return generateAIResult(4, eventCount);
    if (scenarioType === 'peak') return generateAIResult(truckCount, 10);
    if (scenarioType === 'breakdown') return generateAIResult(truckCount, eventCount + 5);
    return aiResult;
  };

  const result = getScenarioResult();

  const metrics: { key: keyof ScenarioResult; label: string; lowerBetter?: boolean }[] = [
    { key: 'total_distance_km', label: 'Total Distance', lowerBetter: true },
    { key: 'total_fuel_liters', label: 'Fuel Used', lowerBetter: true },
    { key: 'total_co2_kg', label: 'CO₂ Emissions', lowerBetter: true },
    { key: 'overflow_events', label: 'Overflow Events', lowerBetter: true },
    { key: 'bins_collected', label: 'Bins Collected', lowerBetter: false },
    { key: 'efficiency', label: 'Efficiency %', lowerBetter: false },
  ];

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>What-If Scenarios</Typography>
      <Typography variant="body2" color="textSecondary" mb={3}>Compare AI dynamic routing against fixed schedules</Typography>

      <Grid container spacing={3}>
        {/* Controls */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Scenario Controls</Typography>
              <ExperimentIcon sx={{ mb: 2, color: 'primary.main' }} />

              <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                <InputLabel>Preset</InputLabel>
                <Select value={scenarioType} label="Preset" onChange={(e) => setScenarioType(e.target.value)}>
                  {scenarios.map((s) => (
                    <MenuItem key={s.value} value={s.value}>{s.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Typography variant="body2" gutterBottom>Trucks available: {truckCount}</Typography>
              <Slider value={truckCount} onChange={(_, v) => setTruckCount(v as number)} min={2} max={12} step={1} marks />

              <Typography variant="body2" gutterBottom sx={{ mt: 2 }}>Events active: {eventCount}</Typography>
              <Slider value={eventCount} onChange={(_, v) => setEventCount(v as number)} min={0} max={10} step={1} marks />
            </CardContent>
          </Card>
        </Grid>

        {/* Comparison */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <CompareIcon sx={{ mr: 1 }} />
                AI vs Fixed Schedule
              </Typography>
              {metrics.map((m) => (
                <Box key={m.key} display="flex" alignItems="center" gap={2} py={1} borderBottom="1px solid #f0f0f0">
                  <Typography variant="body2" sx={{ minWidth: 140 }}>{m.label}</Typography>
                  <Chip label={`Fixed: ${BASELINE[m.key]}`} size="small" variant="outlined" />
                  <Chip label={`AI: ${result[m.key]}`} size="small" color="primary" />
                  <Chip
                    label={compare(BASELINE, result, m.lowerBetter || false)}
                    size="small"
                    color={compare(BASELINE, result, m.lowerBetter || false).includes('better') ? 'success' : 'error'}
                  />
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        {/* 30-Day Projection */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <TrendIcon sx={{ mr: 1 }} />
                30-Day Impact Projection (AI vs Fixed)
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="textSecondary">Distance Saved</Typography>
                  <Typography variant="h4" color="success">
                    {Math.round((BASELINE.total_distance_km - result.total_distance_km) * 30).toLocaleString()} km
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="textSecondary">Fuel Saved</Typography>
                  <Typography variant="h4" color="success">
                    {Math.round((BASELINE.total_fuel_liters - result.total_fuel_liters) * 30).toLocaleString()} L
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="textSecondary">Overflow Prevented</Typography>
                  <Typography variant="h4" color="success">
                    {Math.max(0, Math.round((BASELINE.overflow_events - result.overflow_events) * 30)).toLocaleString()}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="textSecondary">CO₂ Reduction</Typography>
                  <Typography variant="h4" color="success">
                    {Math.round((BASELINE.total_co2_kg - result.total_co2_kg) * 30).toLocaleString()} kg
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="textSecondary">Extra Bins Collected</Typography>
                  <Typography variant="h4" color="primary">
                    +{Math.max(0, Math.round((result.bins_collected - BASELINE.bins_collected) * 30)).toLocaleString()}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="textSecondary">Efficiency Gain</Typography>
                  <Typography variant="h4" color="primary">+{result.efficiency - BASELINE.efficiency}%</Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default WhatIfPage;
