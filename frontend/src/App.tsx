/**
 * AI-WasteTwin App — Routing
 */
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, AppBar, Toolbar, Typography, Button } from '@mui/material';
import { Provider } from 'react-redux';
import { store } from './store';
import { useBins, useTrucks, useLiveUpdates } from './hooks/useApp';

// Pages
import Dashboard from './pages/Dashboard';
import MapPage from './pages/MapPage';
import AIInsightsPage from './pages/AIInsightsPage';
import FleetPage from './pages/FleetPage';
import SimulationPage from './pages/SimulationPage';
import WhatIfPage from './pages/WhatIfPage';

const theme = createTheme({
  palette: {
    primary: { main: '#1976d2' },
    secondary: { main: '#dc004e' },
  },
});

// Root-level data provider: fetches bins/trucks and opens the live
// WebSocket feed. Without this the store stays empty and every page
// shows zeros.
function DataProvider({ children }: { children: React.ReactNode }) {
  useBins();
  useTrucks();
  useLiveUpdates();
  return <>{children}</>;
}

export default function App() {
  return (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <DataProvider>
            <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
              <AppBar position="static">
                <Toolbar>
                  <Typography variant="h6" sx={{ flexGrow: 1 }}>🗑️ AI-WasteTwin</Typography>
                  <Button color="inherit" href="/">Dashboard</Button>
                  <Button color="inherit" href="/map">Map</Button>
                  <Button color="inherit" href="/insights">AI Insights</Button>
                  <Button color="inherit" href="/fleet">Fleet &amp; Routes</Button>
                  <Button color="inherit" href="/simulation">Simulation</Button>
                  <Button color="inherit" href="/whatif">What-If</Button>
                </Toolbar>
              </AppBar>

              <Box sx={{ flex: 1, overflow: 'auto' }}>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/map" element={<MapPage />} />
                  <Route path="/insights" element={<AIInsightsPage />} />
                  <Route path="/fleet" element={<FleetPage />} />
                  <Route path="/simulation" element={<SimulationPage />} />
                  <Route path="/whatif" element={<WhatIfPage />} />
                </Routes>
              </Box>
            </Box>
          </DataProvider>
        </Router>
      </ThemeProvider>
    </Provider>
  );
}