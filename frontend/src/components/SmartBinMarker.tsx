/**
 * SmartBinMarker — Premium Leaflet bin marker with status states
 */
import L from 'leaflet';
import { useMemo } from 'react';
import { statusColors } from '../design/tokens';

interface Props {
  fillPct: number;
  priority: number;
  isCritical?: boolean;
  isSelected?: boolean;
  id: string;
}

const getFillColor = (fill: number): string => {
  if (fill >= 90) return statusColors.critical.main;
  if (fill >= 70) return statusColors.warning.main;
  if (fill >= 50) return statusColors.high.main;
  return statusColors.normal.main;
};

const getRadius = (priority: number, selected: boolean): number => {
  const base = Math.max(14, Math.min(28, 12 + priority * 0.1));
  return selected ? base + 4 : base;
};

export default function SmartBinMarker({ fillPct, priority, isCritical = false, isSelected = false, id }: Props) {
  const color = getFillColor(fillPct);
  const radius = getRadius(priority, isSelected);

  const html = useMemo(() => {
    const outerRing = isSelected
      ? `0 0 0 3px ${color}44`
      : isCritical
        ? '0 0 0 2px rgba(239,68,68,0.3)'
        : '0 2px 8px rgba(0,0,0,0.4)';

    return `
      <div style="position:relative; display:flex; align-items:center; justify-content:center; width:${radius * 2}px; height:${radius * 2}px;">
        <div style="
          width: ${radius}px;
          height: ${radius}px;
          background: radial-gradient(circle at 35% 35%, ${color}cc, ${color});
          border: 2px solid white;
          border-radius: 50%;
          box-shadow: ${outerRing}, inset 0 1px 3px rgba(0,0,0,0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 9px;
          font-weight: 700;
          color: white;
          font-family: 'Inter', system-ui, sans-serif;
          ${isCritical ? 'animation: pulse-ring 1.8s ease-in-out infinite;' : ''}
        ">
          ${Math.round(fillPct)}
        </div>
        <div style="
          position: absolute;
          bottom: -2px;
          left: 50%;
          transform: translateX(-50%);
          background: rgba(10,14,23,0.85);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 4px;
          padding: 1px 4px;
          font-size: 9px;
          color: rgba(255,255,255,0.7);
          white-space: nowrap;
          font-family: 'JetBrains Mono', monospace;
        ">
          ${id}
        </div>
      </div>
    `;
  }, [fillPct, priority, color, radius, isCritical, isSelected, id]);

  return L.divIcon({
    className: 'smart-bin-marker',
    html,
    iconSize: [radius * 2, radius * 2 + 16],
    iconAnchor: [radius, radius + 2],
    popupAnchor: [0, -radius - 14],
  });
}