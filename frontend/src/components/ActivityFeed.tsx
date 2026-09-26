/**
 * ActivityFeed — Live event stream for AI decisions and system events
 */
import { useEffect, useState, useCallback } from 'react';
import { Box, Typography } from '@mui/material';
import { useEvents, useAppDispatch } from '../hooks/useApp';
import { setEvents } from '../store';
import { useWebSocket } from '../api/client';
import { format } from 'date-fns';
import zhCN from 'date-fns/locale/zh-CN';
import { fmtNum } from '../design/tokens';

interface EventItem {
  id: string;
  type: string;
  zone: string;
  message: string;
  timestamp: Date;
  severity: 'info' | 'warning' | 'critical';
}

const EVENT_MESSAGES: Record<string, (e: any) => string> = {
  bin_overflow_risk: (e) => `${e.bin_id} overflow risk ${fmtPct(e.probability)}`,
  bin_critical: (e) => `${e.bin_id} reached critical level`,
  truck_dispatched: (e) => `TRK-${e.truck_id?.slice(-2)} dispatched`,
  route_optimized: (e) => `Route optimized for zone ${e.zone}`,
  festival_started: () => 'Festival event started',
  rain_started: () => 'Heavy rain detected',
  road_closure: (e) => `Road closed in ${e.zone}`,
  truck_breakdown: (e) => `TRK-${e.truck_id?.slice(-2)} breakdown`,
};

function fmtPct(v: number) {
  return `${Math.round(v * 100)}%`;
}

export default function ActivityFeed() {
  const { injectEvent } = useEvents();
  const dispatch = useAppDispatch();
  const [liveEvents, setLiveEvents] = useState<EventItem[]>([]);
  const [connected, setConnected] = useState(false);

  const handleMessage = useCallback((data: any) => {
    if (data.type === 'state_update') {
      const state = data.data;
      if (state.bins) {
        // Find newly critical bins
        Object.entries(state.bins).forEach(([id, bin]: any) => {
          if (bin.current_fill_pct >= 80 && bin.priority_score >= 70) {
            const existing = liveEvents.find(e => e.id === `crit_${id}`);
            if (!existing) {
              setLiveEvents(prev => [{
                id: `crit_${id}`,
                type: 'bin_critical',
                zone: bin.area_type || 'Unknown',
                message: `${id} priority ${fmtNum(bin.priority_score || 0)}/100`,
                timestamp: new Date(),
                severity: 'critical' as const,
              }, ...prev].slice(0, 50));
              dispatch(setEvents([]));
            }
          }
        });
      }
    } else if (data.type === 'event_injected') {
      setLiveEvents(prev => [{
        id: `event_${Date.now()}`,
        type: data.event_type,
        zone: 'City-wide',
        message: EVENT_MESSAGES[data.event_type]?.({ event_type: data.event_type }) || `${data.event_type} injected`,
        timestamp: new Date(),
        severity: 'warning' as const,
      }, ...prev].slice(0, 50));
    }
  }, [liveEvents, dispatch]);

  const { connect, disconnect } = useWebSocket();

  useEffect(() => {
    connect(handleMessage);
    setConnected(true);
    return () => disconnect();
  }, []);

  const severityColor = {
    info: '#3b82f6',
    warning: '#f59e0b',
    critical: '#ef4444',
  };

  return (
    <Box sx={{ bgcolor: 'var(--bg2)', borderLeft: '1px solid var(--border)', height: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column', minWidth: 280, maxWidth: 360 }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 700, color: 'var(--text)' }}>LIVE ACTIVITY</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 8, height: 8, borderRadius: '50%', background: connected ? '#22c55e' : '#ef4444', boxShadow: connected ? '0 0 8px #22c55e' : 'none' }} />
          <Typography variant="caption" sx={{ color: 'var(--text3)' }}>{connected ? 'CONNECTED' : 'DISCONNECTED'}</Typography>
        </Box>
      </Box>

      {/* Events list */}
      <Box sx={{ flex: 1, overflowY: 'auto', p: 1 }}>
        {liveEvents.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="caption" sx={{ color: 'var(--text3)' }}>Waiting for events...</Typography>
          </Box>
        ) : (
          liveEvents.map((evt) => (
            <Box
              key={evt.id}
              sx={{
                p: 1.5,
                mb: 1,
                bgcolor: 'var(--surface)',
                border: '1px solid var(--border)',
                borderLeft: `3px solid ${severityColor[evt.severity]}`,
                borderRadius: '0 8px 8px 0',
                animation: 'fadeUp 200ms ease-out',
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                <Typography variant="caption" sx={{ color: severityColor[evt.severity], fontWeight: 700, fontSize: 10, textTransform: 'uppercase' }}>
                  {evt.type.replace(/_/g, ' ')}
                </Typography>
                <Typography variant="caption" sx={{ color: 'var(--text3)', fontVariantNumeric: 'tabular-nums' }}>
                  {format(evt.timestamp, 'HH:mm:ss', { locale: zhCN })}
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ color: 'var(--text)', fontSize: 13, lineHeight: 1.4 }}>
                {evt.message}
              </Typography>
              {evt.zone !== 'City-wide' && (
                <Typography variant="caption" sx={{ color: 'var(--text3)', fontSize: 11, mt: 0.5, display: 'block' }}>
                  Zone: {evt.zone}
                </Typography>
              )}
            </Box>
          ))
        )}
      </Box>

      {/* Quick actions */}
      <Box sx={{ p: 2, borderTop: '1px solid var(--border)' }}>
        <Typography variant="caption" sx={{ color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: 0.05, fontWeight: 700, mb: 1, display: 'block' }}>Quick Actions</Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
          <ActionButton label="Inject Rain" onClick={() => injectEvent('heavy_rain')} color="#3b82f6" />
          <ActionButton label="Festival" onClick={() => injectEvent('festival')} color="#a855f7" />
          <ActionButton label="Road Closure" onClick={() => injectEvent('road_closure')} color="#f59e0b" />
          <ActionButton label="Breakdown" onClick={() => injectEvent('truck_breakdown')} color="#ef4444" />
        </Box>
      </Box>
    </Box>
  );
}

function ActionButton({ label, onClick, color }: { label: string; onClick: () => void; color: string }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '4px 10px',
        fontSize: 11,
        fontWeight: 600,
        color: color,
        background: `${color}15`,
        border: `1px solid ${color}40`,
        borderRadius: 4,
        cursor: 'pointer',
        transition: 'all 150ms',
      }}
      onMouseEnter={e => (e.currentTarget.style.background = `${color}25`)}
      onMouseLeave={e => (e.currentTarget.style.background = `${color}15`)}
    >
      {label}
    </button>
  );
}