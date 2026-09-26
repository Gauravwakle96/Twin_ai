
import { Chip } from '@mui/material';
import { statusColors } from '../design/tokens';

export type Status = 'normal' | 'warning' | 'high' | 'critical' | 'offline' | 'success' | 'info' | 'ai';

interface Props {
  status: Status;
  label?: string;
  size?: 'small' | 'medium';
  pulse?: boolean;
}

export default function StatusBadge({ status, label, size = 'small', pulse = false }: Props) {
  const c = statusColors[status] || statusColors.normal;
  return (
    <Chip
      size={size}
      label={label || status.toUpperCase()}
      sx={{
        backgroundColor: c.soft,
        color: c.main,
        border: `1px solid ${c.main}33`,
        fontWeight: 700,
        height: size === 'small' ? 20 : 28,
        '& .MuiChip-label': { px: 0.8 },
        ...(pulse && {
          animation: 'pulse-soft 2s ease-in-out infinite',
          boxShadow: `0 0 0 0 ${c.glow}`,
        }),
      }}
    />
  );
}