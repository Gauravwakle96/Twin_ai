/**
 * Map Page - Interactive Leaflet Map
 */
import React, { useEffect, useState } from 'react';
import { Box, Card, CardContent, Typography, Chip } from '@mui/material';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useMapMarkers } from '../hooks/useApp';

// Custom icons
const createBinIcon = (fill: number, priority: number) => {
  const color = fill >= 90 ? '#f44336' : fill >= 70 ? '#ff9800' : '#4caf50';
  const size = 24 + (priority / 10);

  return L.divIcon({
    className: 'custom-bin-marker',
    html: `
      <div style="
        width: ${size}px;
        height: ${size}px;
        background: ${color};
        border: 3px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="white">
          <path d="M19 6h-2c0-2.76-2.24-5-5-5S7 3.24 7 6H5c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-7-3c1.66 0 3 1.34 3 3H9c0-1.66 1.34-3 3-3zm7 17H5V8h14v12z"/>
        </svg>
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
};

const truckIcon = L.divIcon({
  className: 'custom-truck-marker',
  html: `
    <div style="
      width: 32px;
      height: 32px;
      background: #2196f3;
      border: 2px solid white;
      border-radius: 4px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      justify-content: center;
    ">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
        <path d="M20 8h-3V4H3c-1.1 0-2 .9-2 2v11h2c0 1.66 1.34 3 3 3s3-1.34 3-3h6c0 1.66 1.34 3 3 3s3-1.34 3-3h2v-5l-3-4zM6 18.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm13.5-9l1.96 2.5H17V9.5h2.5zm-1.5 9c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
      </svg>
    </div>
  `,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

const depotIcon = L.divIcon({
  className: 'custom-depot-marker',
  html: `
    <div style="
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, #673ab7, #9c27b0);
      border: 3px solid white;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.4);
      display: flex;
      align-items: center;
      justify-content: center;
    ">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="white">
        <path d="M12 7V3H2v18h20V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm10 12h-8v-2h2v-2h-2v-2h2v-2h-2V9h8v10zm-2-8h-2v2h2v-2zm0 4h-2v2h2v-2z"/>
      </svg>
    </div>
  `,
  iconSize: [40, 40],
  iconAnchor: [20, 20],
});

// Depot position (Aurangabad)
const DEPOT_POSITION: [number, number] = [19.8762, 75.3433];

// Map controller component
const MapController: React.FC<{ center: [number, number] }> = ({ center }) => {
  const map = useMap();

  useEffect(() => {
    if (center) {
      map.flyTo(center, 14, { duration: 1 });
    }
  }, [center, map]);

  return null;
};

const MapPage: React.FC = () => {
  const { binMarkers, truckMarkers } = useMapMarkers();
  const [mapCenter, setMapCenter] = useState<[number, number]>(DEPOT_POSITION);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  const handleBinClick = (bin: typeof binMarkers[0]) => {
    setMapCenter(bin.position);
  };

  return (
    <Box sx={{ height: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column' }}>
      {/* Map */}
      <Box sx={{ flex: 1, position: 'relative' }}>
        <MapContainer
          center={DEPOT_POSITION}
          zoom={13}
          style={{ height: '100%', width: '100%' }}
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Map Controller */}
          <MapController center={mapCenter} />

          {/* Depot Marker */}
          <Marker position={DEPOT_POSITION} icon={depotIcon}>
            <Popup>
              <Typography variant="subtitle2">Main Depot</Typography>
              <Typography variant="body2">Aurangabad Central</Typography>
            </Popup>
          </Marker>

          {/* Bin Markers */}
          {binMarkers.map((bin) => (
            <Marker
              key={bin.id}
              position={bin.position}
              icon={createBinIcon(bin.fill, bin.priority)}
              eventHandlers={{
                click: () => handleBinClick(bin),
              }}
            >
              <Popup>
                <Box minWidth={200}>
                  <Typography variant="h6">{bin.id}</Typography>
                  <Typography variant="body2">Fill: {bin.fill.toFixed(1)}%</Typography>
                  <Typography variant="body2">Priority: {bin.priority.toFixed(1)}/100</Typography>
                  {bin.decision && (
                    <Chip
                      label={bin.decision}
                      size="small"
                      color={bin.decision === 'COLLECT' ? 'error' : 'default'}
                      sx={{ mt: 1 }}
                    />
                  )}
                </Box>
              </Popup>
            </Marker>
          ))}

          {/* Truck Markers */}
          {truckMarkers.map((truck) => (
            <Marker
              key={truck.id}
              position={truck.position}
              icon={truckIcon}
            >
              <Popup>
                <Box minWidth={150}>
                  <Typography variant="h6">{truck.id}</Typography>
                  <Typography variant="body2">Status: {truck.status}</Typography>
                </Box>
              </Popup>
            </Marker>
          ))}

          {/* Route Polylines */}
          {truckMarkers.map((truck) =>
            truck.route && truck.route.length > 1 ? (
              <Polyline
                key={`route-${truck.id}`}
                positions={truck.route.map((stop) => [stop.lat || 0, stop.lon || 0] as [number, number])}
                pathOptions={{
                  color: '#2196f3',
                  weight: 4,
                  opacity: 0.7,
                  dashArray: '10, 5',
                }}
              />
            ) : null
          )}
        </MapContainer>

        {/* Legend */}
        <Card sx={{ position: 'absolute', bottom: 20, left: 20, zIndex: 1000, minWidth: 200 }}>
          <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
            <Typography variant="subtitle2" gutterBottom>Legend</Typography>
            <Box display="flex" flexDirection="column" gap={1}>
              <Box display="flex" alignItems="center" gap={1}>
                <Box sx={{ width: 16, height: 16, borderRadius: '50%', background: '#f44336' }} />
                <Typography variant="caption">Critical (≥90%)</Typography>
              </Box>
              <Box display="flex" alignItems="center" gap={1}>
                <Box sx={{ width: 16, height: 16, borderRadius: '50%', background: '#ff9800' }} />
                <Typography variant="caption">Warning (70-89%)</Typography>
              </Box>
              <Box display="flex" alignItems="center" gap={1}>
                <Box sx={{ width: 16, height: 16, borderRadius: '50%', background: '#4caf50' }} />
                <Typography variant="caption">Normal (&lt;70%)</Typography>
              </Box>
              <Box display="flex" alignItems="center" gap={1}>
                <Box sx={{ width: 16, height: 16, borderRadius: '4px', background: '#2196f3' }} />
                <Typography variant="caption">Active Truck</Typography>
              </Box>
              <Box display="flex" alignItems="center" gap={1}>
                <Box sx={{ width: 16, height: 16, borderRadius: '8px', background: 'linear-gradient(135deg, #673ab7, #9c27b0)' }} />
                <Typography variant="caption">Depot</Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
};

export default MapPage;