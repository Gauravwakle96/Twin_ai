import React, { useEffect, useState } from 'react';
import { Box, Typography, Tooltip } from '@mui/material';
import { statusColors, fmtNum } from '../design/tokens';

interface Props {
  title: string;
  value: number | string;
  unit?: string;
  subtitle?: string;
  trend?: { value: number; label: string };
  status?: 'normal' | 'warning' | 'high' | 'critical' | 'offline' | 'success' | 'info';
  icon?: React.ReactNode;
  accent?: string;
  onClick?: () => void;
}

export default function KpiCard({ title, value, unit, subtitle, trend, status, icon, accent = '#3b82f6', onClick }: Props) {
  const [display, setDisplay] = useState(0);
  const numeric = typeof value === 'number' ? value : null;

  useEffect(() => {
    if (numeric === null) return;
    const start = display;
    const end = numeric;
    const dur = 600;
    const t0 = performance.now();
    let raf: number;
    const tick = (now: number) => {
      const p = Math.min(1, (now - t0) / dur);
      const e = 1 - Math.pow(1 - p, 3);
      setDisplay(start + (end - start) * e);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line
  }, [numeric]);

  const sc = status ? statusColors[status] : null;

  return (
    <Tooltip title={subtitle || ''} placement="top" disableHoverListener={!subtitle}>
      <Box
        onClick={onClick}
        sx={{
          position: 'relative',
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md,10px)',
          padding: '14px 16px',
          cursor: onClick ? 'pointer' : 'default',
          overflow: 'hidden',
          transition: 'all 220ms cubic-bezier(0.22,1,0.36,1)',
          '&:hover': onClick ? { borderColor: 'var(--border3)', transform: 'translateY(-2px)', boxShadow: 'var(--shadow-md)' } : {},
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0, left: 0, right: 0,
            height: 2,
            background: `linear-gradient(90deg, ${accent}, transparent)`,
            opacity: 0.8,
          },
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="caption" sx={{ color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.06em', fontSize: '10.5px', fontWeight: 700 }}>
              {title}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.5, mt: 0.5 }}>
              <Typography variant="h5" sx={{ fontWeight: 700, color: 'var(--text)', lineHeight: 1.1, fontVariantNumeric: 'tabular-nums' }}>
                {numeric !== null ? fmtNum(display, 0) : value}
              </Typography>
              {unit && <Typography variant="caption" sx={{ color: 'var(--text3)', fontWeight: 600 }}>{unit}</Typography>}
            </Box>
            {subtitle && (
              <Typography variant="caption" sx={{ color: 'var(--text3)', mt: 0.4, display: 'block' }}>
                {subtitle}
              </Typography>
            )}
          </Box>
          {icon && (
            <Box sx={{ color: sc ? sc.main : accent, opacity: 0.85, mt: -2, ml: 1, flexShrink: 0 }}>
              {icon}
            </Box>
          )}
        </Box>
        {trend && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 1 }}>
            <Typography variant="caption" sx={{ color: trend.value >= 0 ? '#22c55e' : '#ef4444', fontWeight: 700 }}>
              {trend.value >= 0 ? '▲' : '▼'} {Math.abs(trend.value)}%
            </Typography>
            <Typography variant="caption" sx={{ color: 'var(--text3)' }}>{trend.label}</Typography>
          </Box>
        )}
        {sc && (
          <Box sx={{ position: 'absolute', top: 12, right: 12, width: 8, height: 8, borderRadius: '50%', background: sc.main, boxShadow: `0 0 8px ${sc.glow}`, animation: status === 'critical' || status === 'high' ? 'pulse-soft 1.6s ease-in-out infinite' : 'none' }} />
        )}
      </Box>
    </Tooltip>
  );
}