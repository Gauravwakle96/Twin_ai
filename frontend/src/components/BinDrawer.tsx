/**
 * BinDrawer — Premium right-side panel for bin details
 */
import { Box, Typography, Button, Divider } from '@mui/material';
import { X as CloseIcon, Truck as TruckIcon } from 'lucide-react';
import { statusColors, fmtNum } from '../design/tokens';
import StatusBadge from './StatusBadge';
import type { Bin } from '../api/client';

interface Props {
  bin: Bin;
  onClose: () => void;
  onDispatch?: () => void;
}

const PREDICTION_LABELS = ['1h', '2h', '4h'] as const;

export default function BinDrawer({ bin, onClose, onDispatch }: Props) {
  const fillPct = bin.current_fill_pct;
  const status = fillPct >= 90 ? 'critical' : fillPct >= 70 ? 'high' : fillPct >= 50 ? 'warning' : 'normal';
  const priority = bin.priority_score || 0;
  const overflowProb = (bin.overflow_probability || 0) * 100;
  const timeToOverflow = bin.time_to_overflow_hours ?? 999;

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 64,
        right: 0,
        bottom: 0,
        width: { xs: '85vw', sm: 380, md: 420 },
        background: 'var(--surface)',
        borderLeft: '1px solid var(--border2)',
        boxShadow: '-12px 0 40px rgba(0,0,0,0.6)',
        zIndex: 1100,
        display: 'flex',
        flexDirection: 'column',
        animation: 'slideInRight 220ms cubic-bezier(0.22,1,0.36,1)',
      }}
    >
      {/* Header */}
      <Box sx={{ p: 2, pb: 1.5, borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 700, color: 'var(--text)' }}>{bin.id}</Typography>
          <Typography variant="caption" sx={{ color: 'var(--text3)' }}>{bin.area_type} · {bin.waste_type}</Typography>
        </Box>
        <Button size="small" onClick={onClose} sx={{ color: 'var(--text3)', '&:hover': { color: 'var(--text)' } }}>
          <CloseIcon size={18} />
        </Button>
      </Box>

      {/* Scrollable content */}
      <Box sx={{ flex: 1, overflowY: 'auto', p: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
        {/* Main status */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="caption" sx={{ color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: 0.05 }}>Current Fill</Typography>
            <Typography variant="h4" sx={{ fontWeight: 700, color: statusColors[status].main, fontVariantNumeric: 'tabular-nums' }}>
              {fmtNum(fillPct, 1)}%
            </Typography>
          </Box>
          <StatusBadge status={status as any} pulse={status === 'critical'} />
        </Box>

        {/* Progress bar */}
        <Box sx={{ height: 6, borderRadius: 3, background: 'var(--surface3)', overflow: 'hidden' }}>
          <Box sx={{ height: '100%', width: `${Math.min(100, fillPct)}%`, background: `linear-gradient(90deg, ${statusColors.normal.main}, ${statusColors[status].main})`, borderRadius: 3, transition: 'width 600ms ease' }} />
        </Box>

        {/* AI Forecast */}
        <Box>
          <Typography variant="caption" sx={{ color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: 0.05, fontWeight: 700 }}>AI Forecast</Typography>
          <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
            {PREDICTION_LABELS.map((label) => {
              const val = bin.prediction?.[label] ?? fillPct;
              return (
                <Box key={label} sx={{ flex: 1, bgcolor: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: '8px', p: 1, textAlign: 'center' }}>
                  <Typography variant="caption" sx={{ color: 'var(--text3)', fontSize: 10 }}>{label}</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: 'var(--text)', fontVariantNumeric: 'tabular-nums' }}>{fmtNum(val, 0)}%</Typography>
                </Box>
              );
            })}
          </Box>
        </Box>

        <Divider />

        {/* Time to overflow + Overflow risk */}
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
          <Box sx={{ bgcolor: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: '8px', p: 1.5 }}>
            <Typography variant="caption" sx={{ color: 'var(--text3)', fontSize: 10 }}>TIME TO OVERFLOW</Typography>
            <Typography variant="h6" sx={{ fontWeight: 700, color: timeToOverflow < 4 ? statusColors.critical.main : 'var(--text)' }}>
              {timeToOverflow >= 999 ? '∞' : `${fmtNum(timeToOverflow, 1)}h`}
            </Typography>
          </Box>
          <Box sx={{ bgcolor: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: '8px', p: 1.5 }}>
            <Typography variant="caption" sx={{ color: 'var(--text3)', fontSize: 10 }}>OVERFLOW RISK</Typography>
            <Typography variant="h6" sx={{ fontWeight: 700, color: overflowProb > 70 ? statusColors.critical.main : 'var(--text)' }}>
              {fmtNum(overflowProb, 1)}%
            </Typography>
          </Box>
        </Box>

        <Divider />

        {/* Priority Score */}
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="caption" sx={{ color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: 0.05, fontWeight: 700 }}>Priority Score</Typography>
            <Typography variant="caption" sx={{ color: 'var(--text2)', fontWeight: 600 }}>{fmtNum(priority, 0)} / 100</Typography>
          </Box>
          <Box sx={{ height: 8, borderRadius: 4, background: 'var(--surface3)', overflow: 'hidden' }}>
            <Box sx={{ height: '100%', width: `${priority}%`, background: `linear-gradient(90deg, ${statusColors.ai.main}, #ec4899)`, borderRadius: 4, transition: 'width 600ms ease' }} />
          </Box>
        </Box>

        {/* Why flagged */}
        {priority >= 40 && (
          <Box>
            <Typography variant="caption" sx={{ color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: 0.05, fontWeight: 700, mb: 1, display: 'block' }}>Why AI Flagged</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
              <Row label="Fill level" value={fillPct.toFixed(0)} suffix="%" />
              <Row label="Growth rate" value={fmtNum(bin.growth_rate_pct_per_hour || 0, 2)} suffix="/h" />
              <Row label="Overflow risk" value={fmtNum(overflowProb, 1)} suffix="%" />
              <Row label="Zone criticality" value={bin.area_type === 'Market' ? '25' : bin.area_type === 'Commercial' ? '18' : '12'} />
            </Box>
          </Box>
        )}

        <Divider />

        {/* Sensor health */}
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
          <StatBox label="Sensor" value="Healthy" />
          <StatBox label="Battery" value="81%" />
        </Box>
      </Box>

      {/* Actions footer */}
      <Box sx={{ p: 2, borderTop: '1px solid var(--border)', display: 'flex', gap: 1 }}>
        {onDispatch && (
          <Button variant="contained" color="primary" onClick={onDispatch} fullWidth sx={{ fontWeight: 600 }}>
            <TruckIcon size={16} style={{ marginRight: 6 }} />
            Dispatch Truck
          </Button>
        )}
        <Button variant="outlined" onClick={onClose} sx={{ color: 'var(--text2)', borderColor: 'var(--border2)', fontWeight: 600 }}>
          Close
        </Button>
      </Box>
    </Box>
  );
}

const Row = ({ label, value, suffix }: { label: string; value: string; suffix?: string }) => (
  <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
    <Typography variant="caption" sx={{ color: 'var(--text3)' }}>{label}</Typography>
    <Typography variant="caption" sx={{ color: 'var(--text)', fontWeight: 600 }}>{value}{suffix && <Typography component="span" sx={{ color: 'var(--text3)', fontSize: 10 }}>{suffix}</Typography>}</Typography>
  </Box>
);

const StatBox = ({ label, value }: { label: string; value: string }) => (
  <Box sx={{ bgcolor: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: '8px', p: 1, textAlign: 'center' }}>
    <Typography variant="caption" sx={{ color: 'var(--text3)', fontSize: 10 }}>{label}</Typography>
    <Typography variant="body2" sx={{ fontWeight: 600, color: 'var(--text)' }}>{value}</Typography>
  </Box>
);