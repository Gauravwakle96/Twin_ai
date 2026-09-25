/**
 * Fleet Page - Vehicle Management & Routes
 */
import React from 'react';
import { Box, Grid, Card, CardContent, Typography, Chip } from '@mui/material';
import { LocalShipping as TruckIcon, Navigation as RouteIcon } from '@mui/icons-material';
import { useTrucks } from '../hooks/useApp';

const FleetPage: React.FC = () => {
  const { trucks } = useTrucks();
  const truckValues = Object.values(trucks);

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>Fleet & Routes</Typography>
      <Typography variant="body2" color="textSecondary" mb={3}>Vehicle status, utilization, and optimized routes</Typography>

      <Grid container spacing={3}>
        {/* Fleet Summary */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Fleet Overview</Typography>
              <Typography variant="h3" color="primary" fontWeight="bold">{truckValues.length}</Typography>
              <Typography variant="body2" color="textSecondary">total trucks</Typography>
              <Box mt={2} display="flex" flexDirection="column" gap={1}>
                <Chip label={`Active: ${truckValues.filter((t) => t.status === 'enroute').length}`} color="success" size="small" />
                <Chip label={`Idle: ${truckValues.filter((t) => t.status === 'idle').length}`} color="default" size="small" />
                <Chip label={`Breakdown: ${truckValues.filter((t) => t.status === 'breakdown').length}`} color="error" size="small" />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Avg Utilization */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Avg Utilization</Typography>
              <Typography variant="h3" color="secondary" fontWeight="bold">
                {truckValues.length > 0
                  ? (truckValues.reduce((s, t) => s + t.utilization_pct, 0) / truckValues.length).toFixed(1)
                  : 0}%
              </Typography>
              <Typography variant="body2" color="textSecondary">overall fleet load</Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Total Load */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Total Load</Typography>
              <Typography variant="h3" color="info" fontWeight="bold">
                {truckValues.reduce((s, t) => s + t.current_load_liters, 0).toLocaleString()} L
              </Typography>
              <Typography variant="body2" color="textSecondary">across all trucks</Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Truck Cards */}
        {truckValues.map((truck) => (
          <Grid item xs={12} sm={6} md={4} key={truck.id}>
            <Card variant="outlined">
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <TruckIcon color="primary" />
                    <Typography variant="h6" fontWeight="bold">{truck.id}</Typography>
                  </Box>
                  <Chip
                    label={truck.status.toUpperCase()}
                    color={
                      truck.status === 'enroute' ? 'success' :
                      truck.status === 'idle' ? 'default' : 'error'
                    }
                    size="small"
                  />
                </Box>
                <Grid container spacing={1}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="textSecondary">Load</Typography>
                    <Typography variant="body1" fontWeight="medium">{truck.current_load_liters}/{truck.capacity_liters} L</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="textSecondary">Utilization</Typography>
                    <Typography variant="body1" fontWeight="medium">{truck.utilization_pct.toFixed(1)}%</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="textSecondary">Driver</Typography>
                    <Typography variant="body1">{truck.driver_name}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="textSecondary">Assigned Bins</Typography>
                    <Typography variant="body1">{truck.assigned_bins.length}</Typography>
                  </Grid>
                </Grid>
                {truck.route && truck.route.length > 0 && (
                  <Box mt={2}>
                    <Typography variant="body2" color="textSecondary" mb={1}>
                      <RouteIcon fontSize="small" /> Route ({truck.route.length} stops)
                    </Typography>
                    <Box display="flex" gap={0.5} flexWrap="wrap">
                      {truck.route.map((stop, i) => (
                        <Chip key={i} label={stop.bin_id || `Stop ${i + 1}`} size="small" variant="outlined" />
                      ))}
                    </Box>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default FleetPage;
