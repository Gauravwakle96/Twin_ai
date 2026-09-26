/**
 * AI-WasteTwin Design Tokens
 * Aurangabad Smart City AI Command Center
 *
 * Single source of truth for colors, typography, spacing, motion.
 * Dark-first, premium, technical — operations-center aesthetic.
 */

// Semantic status colors (consistent everywhere)
export const statusColors = {
  normal:    { main: '#22c55e', soft: 'rgba(34,197,94,0.12)',  glow: 'rgba(34,197,94,0.35)' },
  warning:   { main: '#f59e0b', soft: 'rgba(245,158,11,0.12)', glow: 'rgba(245,158,11,0.35)' },
  high:      { main: '#f97316', soft: 'rgba(249,115,22,0.14)',  glow: 'rgba(249,115,22,0.40)' },
  critical:  { main: '#ef4444', soft: 'rgba(239,68,68,0.14)',  glow: 'rgba(239,68,68,0.45)' },
  offline:   { main: '#6b7280', soft: 'rgba(107,114,128,0.12)', glow: 'rgba(107,114,128,0.30)' },
  success:   { main: '#10b981', soft: 'rgba(16,185,129,0.12)', glow: 'rgba(16,185,129,0.35)' },
  info:      { main: '#3b82f6', soft: 'rgba(59,130,246,0.12)', glow: 'rgba(59,130,246,0.35)' },
  ai:        { main: '#a855f7', soft: 'rgba(168,85,247,0.14)', glow: 'rgba(168,85,247,0.40)' },
};

export const brand = {
  // Core brand
  bg:        '#0a0e17',
  bg2:       '#0f1420',
  bg3:       '#141a26',
  surface:   '#161c29',
  surface2:  '#1b2232',
  surface3:  '#202838',
  border:    'rgba(255,255,255,0.07)',
  border2:   'rgba(255,255,255,0.11)',
  border3:   'rgba(255,255,255,0.16)',
  // Text
  text:      '#e6e9f0',
  text2:     '#9aa3b2',
  text3:     '#6b7280',
  // Accent
  accent:    '#3b82f6',
  accent2:   '#6366f1',
  accentSoft:'rgba(59,130,246,0.10)',
  // Aurangabad heritage accent
  saffron:   '#f59e0b',
  // Glass
  glass:     'rgba(22,28,41,0.72)',
  glassBlur: 16,
};

export const typography = {
  display: { fontFamily: '"Inter", system-ui, sans-serif', fontWeight: 700, letterSpacing: '-0.02em' },
  title:   { fontFamily: '"Inter", system-ui, sans-serif', fontWeight: 600, letterSpacing: '-0.015em' },
  body:    { fontFamily: '"Inter", system-ui, sans-serif', fontWeight: 400 },
  mono:    { fontFamily: '"JetBrains Mono", "SF Mono", ui-monospace, monospace', fontSize: '12px' },
};

export const radius = { sm: 6, md: 10, lg: 14, xl: 18, pill: 999 };

export const shadow = {
  sm: '0 1px 2px rgba(0,0,0,0.4)',
  md: '0 4px 16px rgba(0,0,0,0.45)',
  lg: '0 12px 40px rgba(0,0,0,0.55)',
  glow: (c: string) => `0 0 24px ${c}`,
};

export const motion = {
  fast: '120ms cubic-bezier(0.22,1,0.36,1)',
  mid:  '220ms cubic-bezier(0.22,1,0.36,1)',
  slow: '360ms cubic-bezier(0.22,1,0.36,1)',
};

// Z-index layers
export const z = {
  dropdown: 1000,
  sticky:   1020,
  fixed:    1030,
  modal:    1040,
  popover:  1050,
  tooltip:  1060,
  mapCtrl:  1000,
  mapFloat: 1050,
  drawer:   1100,
  toast:    1200,
};

// Breakpoints
export const bp = { sm: 600, md: 900, lg: 1200, xl: 1536 };

// Format helpers
export const fmtPct = (v: number) => `${Math.round(v)}%`;
export const fmtNum = (v: number, d = 1) => v.toFixed(d);
export const fmtTime = (iso: string) => {
  if (!iso) return '--';
  try {
    const d = new Date(iso);
    return d.toLocaleString('en-IN', { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' });
  } catch { return iso; }
};