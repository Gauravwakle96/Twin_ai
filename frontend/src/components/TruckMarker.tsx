/**
 * TruckMarker — Animated Leaflet truck marker
 */
import L from 'leaflet';
import { useMemo } from 'react';
import { statusColors } from '../design/tokens';

interface Props {
  id: string;
  status: string;
  loadPct: number;
  isBroken?: boolean;
}

const STATUS_COLORS: Record<string, string> = {
  idle: '#22c55e',
  enroute: '#3b82f6',
  collecting: '#a855f7',
  returning: '#f59e0b',
  breakdown: '#ef4444',
  maintenance: '#6b7280',
};

export default function TruckMarker({ id, status, loadPct, isBroken = false }: Props) {
  const color = isBroken ? statusColors.critical.main : (STATUS_COLORS[status] || '#3b82f6');

  const html = useMemo(() => `
    <div style="position:relative; display:flex; align-items:center; justify-content:center;">
      <div style="
        width: 32px;
        height: 20px;
        background: linear-gradient(135deg, ${color}, ${color}cc);
        border: 2px solid white;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
      ">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="white">
          <path d="M20 8h-3V4H3c-1.1 0-2 .9-2 2v11h2c0 1.66 1.34 3 3 3s3-1.34 3-3h6c0 1.66 1.34 3 3 3s3-1.34 3-3h2v-5l-3-4zM6 18.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm13.5-9l1.96 2.5H17V9.5h2.5zm-1.5 9c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
        </svg>
      </div>
      <div style="
        position: absolute;
        top: -18px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(10,14,23,0.9);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 10px;
        color: ${color};
        font-weight: 700;
        white-space: nowrap;
        font-family: 'JetBrains Mono', monospace;
      ">
        ${id} · ${loadPct}%
      </div>
    </div>
  `, [id, color, loadPct]);

  return L.divIcon({
    className: 'truck-marker',
    html,
    iconSize: [32, 28],
    iconAnchor: [16, 14],
    popupAnchor: [0, -16],
  });
}