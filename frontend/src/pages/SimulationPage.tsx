/**
 * Simulation Page - Event Controls
 */
import React from 'react';
import { Box, Grid, Card, CardContent, Typography, Button, Chip, Slider } from '@mui/material';
import {
  Festival as FestivalIcon,
  Thunderstorm as RainIcon,
  Block as RoadClosureIcon,
  Construction as BreakdownIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  FastForward as FastIcon,
  Replay as ResetIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { useSimulation, useEvents } from '../hooks/useApp';

const EVENT_CONFIGS = [
  {
    type: 'festival',
    label: 'Festival',
    icon: <FestivalIcon />,
    color: '#9c27b0',
    description: 'Increases waste generation in affected area',
    params: { zone: 'Market_Area', duration_hours: 12, intensity: 1.5 },
  },
  {
    type: 'heavy_rain',
    label: 'Heavy Rain',
    icon: <RainIcon />,
    color: '#1976d2',
    description: 'Increases travel times on all roads',
    params: { duration_hours: 6, intensity: 1.3 },
  },
  {
    type: 'road_closure',
    label: 'Road Closure',
    icon: <RoadClosureIcon />,
    color: '#ff9800',
    description: 'Makes specific roads unavailable',
    params: { zone: 'Paithan_Road', duration_hours: 4 },
  },
  {
    type: 'truck_breakdown',
    label: 'Truck Breakdown',
    icon: <BreakdownIcon />,
    color: '#f44336',
    description: 'Truck becomes unavailable, bins need reassignment',
    params: { duration_hours: 3 },
  },
];

const SimulationPage: React.FC = () => {
  const { running, speed, tick, startSimulation, stopSimulation, setSimulationSpeed } = useSimulation();
  const { events, injectEvent } = useEvents();
  const handleInjectEvent = async (type: string, params: Record<string, unknown>) => {
    await injectEvent(type, params);
  };

  const activeEventTypes = events.map((e) => e.type);

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Simulation Control
      </Typography>
      <Typography variant="body2" color="textSecondary" mb={3}>
        Manage simulation speed, inject events, and observe system responses
      </Typography>

      <Grid container spacing={3}>
        {/* Simulation Controls */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Simulation Clock
              </Typography>

              <Box display="flex" gap={2} mb={3}>
                <Button
                  variant="contained"
                  color={running ? 'error' : 'success'}
                  startIcon={running ? <PauseIcon /> : <PlayIcon />}
                  onClick={running ? stopSimulation : startSimulation}
                  size="large"
                >
                  {running ? 'Pause' : 'Start'}
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<ResetIcon />}
                  onClick={() => window.location.reload()}
                >
                  Reset
                </Button>
              </Box>

              <Typography variant="body2" gutterBottom>
                Current Tick: {tick}
              </Typography>

              <Typography variant="body2" gutterBottom sx={{ mt: 2 }}>
                Simulation Speed: {speed}x
              </Typography>
              <Slider
                value={speed}
                onChange={(_, value) => setSimulationSpeed(value as number)}
                min={1}
                max={60}
                step={1}
                marks={[
                  { value: 1, label: '1x' },
                  { value: 10, label: '10x' },
                  { value: 30, label: '30x' },
                  { value: 60, label: '60x' },
                ]}
              />
              <Typography variant="caption" color="textSecondary">
                Higher speed = faster simulation (1 hour = 1 second at 1x)
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Time Jump Controls */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Time Jump
              </Typography>
              <Typography variant="body2" color="textSecondary" mb={2}>
                Skip forward in simulation time
              </Typography>

              <Box display="flex" gap={2} flexWrap="wrap">
                <Button variant="outlined" startIcon={<AddIcon />}>
                  +1 Hour
                </Button>
                <Button variant="outlined" startIcon={<FastIcon />}>
                  +6 Hours
                </Button>
                <Button variant="outlined" startIcon={<FastIcon />}>
                  +24 Hours
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Event Injection */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Event Injection
              </Typography>
              <Typography variant="body2" color="textSecondary" mb={2}>
                Inject events to test system response and automatic replanning
              </Typography>

              <Grid container spacing={2}>
                {EVENT_CONFIGS.map((event) => (
                  <Grid item xs={12} sm={6} md={3} key={event.type}>
                    <Card
                      variant="outlined"
                      sx={{
                        cursor: 'pointer',
                        borderColor: activeEventTypes.includes(event.type) ? event.color : 'divider',
                        backgroundColor: activeEventTypes.includes(event.type) ? `${event.color}10` : 'transparent',
                        '&:hover': { backgroundColor: `${event.color}05` },
                      }}
                      onClick={() => handleInjectEvent(event.type, event.params)}
                    >
                      <CardContent sx={{ textAlign: 'center', py: 2 }}>
                        <Box sx={{ color: event.color, mb: 1 }}>
                          {React.cloneElement(event.icon as React.ReactElement, { fontSize: 'large' })}
                        </Box>
                        <Typography variant="subtitle1" fontWeight="bold">
                          {event.label}
                        </Typography>
                        <Typography variant="caption" display="block" color="textSecondary">
                          {event.description}
                        </Typography>
                        {activeEventTypes.includes(event.type) && (
                          <Chip
                            label="ACTIVE"
                            size="small"
                            color="success"
                            sx={{ mt: 1 }}
                          />
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
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
                  No active events. System operating normally.
                </Typography>
              ) : (
                <Box display="flex" gap={1} flexWrap="wrap">
                  {events.map((event) => (
                    <Chip
                      key={event.id}
                      label={`${event.type.replace('_', ' ').toUpperCase()} - ${event.zone}`}
                      color={
                        event.type === 'festival' ? 'secondary' :
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

        {/* Event Effects Explanation */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                How Events Affect the System
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="primary">Festival</Typography>
                  <Typography variant="body2" color="textSecondary">
                    Increases waste generation by 50-100% in affected zone.
                    Bins fill faster → higher priority → more collections needed.
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="primary">Heavy Rain</Typography>
                  <Typography variant="body2" color="textSecondary">
                    Increases travel time by 30%. Routes take longer,
                    less bins can be collected per trip.
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="primary">Road Closure</Typography>
                  <Typography variant="body2" color="textSecondary">
                    Makes specific roads unavailable. Routes must be
                    recalculated to avoid closed roads.
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="primary">Truck Breakdown</Typography>
                  <Typography variant="body2" color="textSecondary">
                    Truck becomes unavailable. Assigned bins are released
                    and must be reassigned to other trucks.
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SimulationPage;