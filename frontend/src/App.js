import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, CssBaseline, Box, Paper } from '@mui/material';
import { createTheme } from '@mui/material/styles';
import FileUpload from './components/FileUpload';
import AdminRoute from './components/AdminRoute';
import LandingPage from './components/LandingPage';

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
                <FileUpload />
              </Paper>
            </Box>
          } />
          <Route path="/admin" element={<AdminRoute />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
