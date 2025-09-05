import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, CssBaseline, Box, Paper } from '@mui/material';
import { createTheme } from '@mui/material/styles';
import RecordVideo from './components/RecordVideo';
import AdminRoute from './components/AdminRoute';
import LandingPage from './components/LandingPage';
import ChatPage from './components/ChatPage';

const theme = createTheme({
  palette: {
    background: {
      default: '#f5f5f5',
    },
  },
  shape: {
    borderRadius: 10
  }
});

function App() {
  // Set the correct basename based on environment and host
  const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  const basename = isLocalhost ? '/' : '';  // Use root path in production, / in localhost

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router basename={basename}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/upload" element={
            <Box sx={{ p: 3, maxWidth: 800, mx: 'auto' }}>
              <Paper sx={{ p: 3 }}>
                <RecordVideo />
              </Paper>
            </Box>
          } />
          <Route path="/admin" element={<AdminRoute />} />
          <Route path="/chat/:videoId" element={
            <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
              <Paper sx={{ p: 3 }}>
                <ChatPage />
              </Paper>
            </Box>
          } />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
