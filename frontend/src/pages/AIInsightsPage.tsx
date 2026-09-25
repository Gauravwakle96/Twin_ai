/**
 * AI Insights Page - ML Predictions & Analytics
 */
import React from 'react';
import { Box, Grid, Card, CardContent, Typography, Chip } from '@mui/material';
import {
  Psychology as AIcon,
  TrendingUp as TrendIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import { useAppSelector } from '../store';

const InsightCard: React.FC<{ title: string; value: string | number; subtitle?: string; icon: React.ReactNode; color?: string }> = ({ title, value, subtitle, icon, color = 'primary.main' }) => (
  <Card>
    <CardContent>
      <Box display="flex" justifyContent="space-between" alignItems="flex-start">
        <Box>
          <Typography color="textSecondary" variant="body2" gutterBottom>{title}</Typography>
          <Typography variant="h4" sx={{ color, fontWeight: 'bold' }}>{value}</Typography>
          {subtitle && <Typography variant="caption" color="textSecondary">{subtitle}</Typography>}
        </Box>
        <Box sx={{ color }}>{icon}</Box>
      </Box>
    </CardContent>
  </Card>
);

const AIInsightsPage: React.FC = () => {
  const bins = useAppSelector((state) => state.bins);
  const binValues = Object.values(bins);

  const binsWithPredictions = binValues.filter((b) => b.prediction).length;
  const avg1hForecast = binValues.length > 0
    ? binValues.reduce((s, b) => s + (b.prediction?.['1h'] || 0), 0) / binValues.length
    : 0;
  const avg2hForecast = binValues.length > 0
    ? binValues.reduce((s, b) => s + (b.prediction?.['2h'] || 0), 0) / binValues.length
    : 0;
  const avg4hForecast = binValues.length > 0
    ? binValues.reduce((s, b) => s + (b.prediction?.['4h'] || 0), 0) / binValues.length
    : 0;
  const avgOverflowProb = binValues.length > 0
    ? binValues.reduce((s, b) => s + (b.overflow_probability || 0), 0) / binValues.length
    : 0;
  const anomalous = binValues.filter((b) => b.is_anomalous).length;

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>AI Insights</Typography>
      <Typography variant="body2" color="textSecondary" mb={3}>ML predictions, overflow forecasts, and anomaly detection</Typography>

      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <InsightCard title="Bins with Predictions" value={binsWithPredictions} subtitle={`of ${binValues.length} total`} icon={<AIcon fontSize="large" />} color="#9c27b0" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <InsightCard title="Avg Forecast +1h" value={`${avg1hForecast.toFixed(1)}%`} icon={<TrendIcon fontSize="large" />} color="#1976d2" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <InsightCard title="Avg Forecast +2h" value={`${avg2hForecast.toFixed(1)}%`} icon={<TrendIcon fontSize="large" />} color="#1565c0" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <InsightCard title="Avg Forecast +4h" value={`${avg4hForecast.toFixed(1)}%`} icon={<TrendIcon fontSize="large" />} color="#0d47a1" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <InsightCard title="Avg Overflow Prob" value={`${avgOverflowProb.toFixed(1)}%`} subtitle="across all bins" icon={<WarningIcon fontSize="large" />} color="#ff9800" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <InsightCard title="Anomalies Detected" value={anomalous} subtitle="ML outlier detection" icon={<CheckIcon fontSize="large" />} color="#f44336" />
        </Grid>
      </Grid>

      {/* Prediction Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>Bin Predictions (Top 10 by Fill Level)</Typography>
          {binValues.sort((a, b) => b.current_fill_pct - a.current_fill_pct).slice(0, 10).map((bin) => (
            <Box key={bin.id} display="flex" alignItems="center" gap={2} py={1} borderBottom="1px solid #eee">
              <Chip label={bin.id} size="small" variant="outlined" />
              <Typography variant="body2" sx={{ minWidth: 60 }}>Fill: {bin.current_fill_pct.toFixed(1)}%</Typography>
              <Typography variant="body2" sx={{ minWidth: 60 }}>+1h: {(bin.prediction?.['1h'] || 0).toFixed(1)}%</Typography>
              <Typography variant="body2" sx={{ minWidth: 60 }}>+2h: {(bin.prediction?.['2h'] || 0).toFixed(1)}%</Typography>
              <Typography variant="body2" sx={{ minWidth: 60 }}>+4h: {(bin.prediction?.['4h'] || 0).toFixed(1)}%</Typography>
              <Typography variant="body2" sx={{ minWidth: 80 }}>Overflow: {(bin.overflow_probability || 0).toFixed(1)}%</Typography>
              <Typography variant="body2" sx={{ minWidth: 80 }}>⏱ {(bin.time_to_overflow_hours || 0).toFixed(1)}h</Typography>
              {bin.is_anomalous && <Chip label="ANOMALY" size="small" color="error" />}
            </Box>
          ))}
        </CardContent>
      </Card>
    </Box>
  );
};

export default AIInsightsPage;
